import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Mount Abu Screening Analytics", page_icon="🩺", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f7f9fc; border: 1px solid #e6eaf0; padding: 14px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.title("Mount Abu Screening Analytics Dashboard")
st.caption("Upload your Excel workbook to analyse screening data locally. No Google Sheets connection required.")

uploaded = st.file_uploader("Upload Mount Abu Excel workbook", type=["xlsx", "xls"])

def load_data(file):
    book = pd.ExcelFile(file)
    preferred = "Patient Data"
    if preferred not in book.sheet_names:
        raise ValueError(f"Could not find a '{preferred}' worksheet. Available sheets: {', '.join(book.sheet_names)}")
    data = pd.read_excel(file, sheet_name=preferred)
    required = ["Patient ID", "Status", "Age"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    data = data.copy()
    data["Patient ID"] = data["Patient ID"].astype("string").str.strip()
    data = data[data["Patient ID"].notna() & data["Patient ID"].ne("")]
    if "Scan Date" in data.columns:
        data["_scan_dt"] = pd.to_datetime(data["Scan Date"], errors="coerce", utc=True)
        data = data.sort_values(["Patient ID", "_scan_dt", "Visit ID"] if "Visit ID" in data.columns else ["Patient ID", "_scan_dt"])
        data = data.drop_duplicates("Patient ID", keep="last")
    else:
        data = data.drop_duplicates("Patient ID", keep="last")
    data["Age"] = pd.to_numeric(data["Age"], errors="coerce")
    data["Status"] = data["Status"].astype("string").str.strip().str.title()
    return data

def count_table(data, group):
    tab = pd.crosstab(data[group].fillna("Missing"), data["Status"])
    for c in ["Green", "Yellow", "Red"]:
        if c not in tab.columns: tab[c] = 0
    return tab[["Green", "Yellow", "Red"]].reset_index()

if uploaded is None:
    st.info("Start by uploading the Excel workbook. The dashboard will read the **Patient Data** worksheet and calculate the results from the uploaded records.")
    st.markdown("**Expected workbook:** Mount Abu screening analysis Excel file containing a `Patient Data` worksheet.")
    st.stop()

try:
    df = load_data(uploaded)
except Exception as e:
    st.error(f"Could not read the workbook: {e}")
    st.stop()

total = len(df)
valid_status = df["Status"].isin(["Green", "Yellow", "Red"]).sum()
green = int((df["Status"] == "Green").sum())
yellow = int((df["Status"] == "Yellow").sum())
red = int((df["Status"] == "Red").sum())

st.success(f"Workbook loaded successfully · {total:,} unique Patient IDs")
if total != 5074:
    st.warning(f"The uploaded workbook contains {total:,} unique Patient IDs, not the previously expected 5,074. Dashboard figures below use the uploaded file.")
if valid_status != total:
    st.warning(f"{total-valid_status:,} records have a missing or unrecognised screening status and are excluded from status charts.")

# Sidebar filters
st.sidebar.header("Dashboard filters")
status_options = [x for x in ["Green", "Yellow", "Red"] if x in df["Status"].dropna().unique()]
selected_status = st.sidebar.multiselect("Screening status", status_options, default=status_options)
age_min = int(df["Age"].min()) if df["Age"].notna().any() else 0
age_max = int(df["Age"].max()) if df["Age"].notna().any() else 100
age_range = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))
filtered = df[df["Status"].isin(selected_status) & df["Age"].between(age_range[0], age_range[1], inclusive="both")]

st.subheader("Overview")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Unique patients", f"{total:,}")
c2.metric("Green", f"{green:,}", f"{green/total:.1%}" if total else "—")
c3.metric("Yellow", f"{yellow:,}", f"{yellow/total:.1%}" if total else "—")
c4.metric("Red", f"{red:,}", f"{red/total:.1%}" if total else "—")

left,right = st.columns(2)
with left:
    status_df = pd.DataFrame({"Status":["Green","Yellow","Red"],"Patients":[green,yellow,red]})
    fig=px.pie(status_df,names="Status",values="Patients",hole=.55,title="Screening status distribution")
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.markdown("**Age summary (all unique patients)**")
    st.metric("Mean age", f"{df['Age'].mean():.1f} years" if df["Age"].notna().any() else "Not available")
    st.metric("Median age", f"{df['Age'].median():.0f} years" if df["Age"].notna().any() else "Not available")
    st.caption(f"Age available for {df['Age'].notna().sum():,} of {total:,} patients.")

st.divider()
st.subheader("Age analysis")
age_bins=[0,29,39,49,59,69,200]
age_labels=["<30","30–39","40–49","50–59","60–69","70+"]
df["Age group dashboard"]=pd.cut(df["Age"],bins=age_bins,labels=age_labels)
age_tab=count_table(df,"Age group dashboard")
age_tab=age_tab.rename(columns={"Age group dashboard":"Age group"})
st.plotly_chart(px.bar(age_tab,x="Age group",y=["Green","Yellow","Red"],barmode="group",title="Screening status by age group"),use_container_width=True)
st.dataframe(age_tab,use_container_width=True,hide_index=True)

st.divider()
st.subheader("Menopause analysis")
if "Menopause Age" in df.columns:
    df["Menopause Age numeric"]=pd.to_numeric(df["Menopause Age"],errors="coerce")
    recorded=df["Menopause Age numeric"].notna().sum()
    missing=total-recorded
    m1,m2,m3=st.columns(3)
    m1.metric("Menopause age recorded",f"{recorded:,}")
    m2.metric("Missing menopause age",f"{missing:,}")
    m3.metric("Mean menopause age",f"{df['Menopause Age numeric'].mean():.1f}" if recorded else "—")
    men=df[df["Menopause Age numeric"].notna()].copy()
    if len(men):
        men_bins=[0,39,44,49,54,59,120]
        men_labels=["<40","40–44","45–49","50–54","55–59","60+"]
        men["Menopause age group dashboard"]=pd.cut(men["Menopause Age numeric"],bins=men_bins,labels=men_labels)
        men_tab=count_table(men,"Menopause age group dashboard").rename(columns={"Menopause age group dashboard":"Menopause age group"})
        st.plotly_chart(px.bar(men_tab,x="Menopause age group",y=["Green","Yellow","Red"],barmode="group",title="Screening status by recorded menopause age"),use_container_width=True)
        st.dataframe(men_tab,use_container_width=True,hide_index=True)
else:
    st.info("The workbook does not contain a 'Menopause Age' column.")

st.divider()
st.subheader("Symptom analysis")
symptoms=["Lump in Breast","Breast Pain","Nipple Discharge","Skin Changes"]
available=[c for c in symptoms if c in df.columns]
if available:
    rows=[]
    for col in available:
        values=pd.to_numeric(df[col],errors="coerce").fillna(0)
        rows.append({"Symptom":col,"All screened":int((values>0).sum()),"Red cases":int(((values>0)&(df["Status"]=="Red")).sum())})
    symtab=pd.DataFrame(rows)
    st.plotly_chart(px.bar(symtab,x="Symptom",y=["All screened","Red cases"],barmode="group",title="Reported symptoms"),use_container_width=True)
    st.dataframe(symtab,use_container_width=True,hide_index=True)
else:
    st.info("No recognised symptom columns were found.")

st.divider()
st.subheader("Symptomatic status")
if "Symptom status" in df.columns:
    symptom_status=df["Symptom status"].fillna("Missing").value_counts().rename_axis("Symptom status").reset_index(name="Patients")
    st.plotly_chart(px.bar(symptom_status,x="Symptom status",y="Patients",title="Symptomatic and asymptomatic patients"),use_container_width=True)
    st.dataframe(symptom_status,use_container_width=True,hide_index=True)
else:
    st.info("No 'Symptom status' column was found.")

st.divider()
st.subheader("Filtered summary")
st.caption("The sidebar filters affect this section. Patient names and direct identifiers are not displayed.")
filtered_summary=filtered["Status"].value_counts().reindex(["Green","Yellow","Red"],fill_value=0).rename_axis("Status").reset_index(name="Patients")
st.dataframe(filtered_summary,use_container_width=True,hide_index=True)

# Export aggregate summaries only
output=BytesIO()
with pd.ExcelWriter(output,engine="openpyxl") as writer:
    pd.DataFrame({"Metric":["Unique patients","Green","Yellow","Red","Mean age","Median age"],
                  "Value":[total,green,yellow,red,df["Age"].mean(),df["Age"].median()]}).to_excel(writer,index=False,sheet_name="Overview")
    age_tab.to_excel(writer,index=False,sheet_name="Age Analysis")
    if available: symtab.to_excel(writer,index=False,sheet_name="Symptoms")
    if "Menopause Age" in df.columns:
        men_sum=pd.DataFrame({"Metric":["Recorded menopause age","Missing menopause age","Mean menopause age"],
                              "Value":[recorded,missing,df["Menopause Age numeric"].mean()]})
        men_sum.to_excel(writer,index=False,sheet_name="Menopause")
st.download_button("Download aggregate analysis (Excel)",data=output.getvalue(),file_name="Mount_Abu_Dashboard_Summary.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("Interpretation note: Red is a screening classification, not a confirmed cancer diagnosis. All calculations are based on the uploaded workbook; missing values are not imputed.")
