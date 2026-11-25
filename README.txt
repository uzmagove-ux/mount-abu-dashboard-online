# Mount Abu Screening Analytics Dashboard

## Start the dashboard (Windows)
1. Install Python 3.10 or newer from https://www.python.org/downloads/ (select "Add Python to PATH").
2. Extract this folder.
3. Double-click `Run_Dashboard_Windows.bat`.
4. Wait for the browser tab to open. If it does not, open the local URL printed in the terminal (usually http://localhost:8501).
5. Upload the Mount Abu Excel workbook when prompted.

## Input workbook
The app reads the `Patient Data` worksheet. It uses the latest available Scan Date per Patient ID when dates are available, then retains one row per Patient ID. It calculates all dashboard statistics from the uploaded workbook.

## Privacy
The app runs locally on your computer. It does not connect to Google Sheets or send workbook data to a dashboard server. It does not display patient names or direct identifiers. Keep the workbook and this project in a secure location.

## Notes
- The app warns if the unique patient count differs from 5,074; it does not force the expected count.
- Red is a screening classification, not a confirmed cancer diagnosis.
- Missing menopause ages are counted separately.
