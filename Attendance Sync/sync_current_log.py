# Sync the current log to the Google Sheet every hour
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))  # Move one level up
# Load Google Sheets API credentials
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")

# Define your sheet names
EMPLOYEE_SHEET_NAME = "EmployeeDetails"
ATTENDANCE_SHEET_NAME = "AttendanceRecords"

# CSV file paths
USERS_CSV = os.path.join(PARENT_DIR, "data", "users.csv")
ATTENDANCE_FOLDER = os.path.join(PARENT_DIR, "data", "attendance_logs")

current_date = datetime.now().strftime("%Y-%m-%d")
attendance_file = os.path.join(ATTENDANCE_FOLDER, f"{current_date}.csv")


# Authenticate Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

def sync_current_log():
    try:
        sheet = client.open(ATTENDANCE_SHEET_NAME)
        
        
        date = current_date
        df = pd.read_csv(attendance_file)
                
        try:
            worksheet = sheet.worksheet(date)  # Try to find existing sheet
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=date, rows="1000", cols="10")  # Create new sheet
                
        worksheet.clear()  # Clear previous data
        worksheet.append_rows([df.columns.tolist()] + df.values.tolist())  # Append new data
                
        print(f"✅ Synced attendance log for {date}")
    except Exception as e:
        print(f"❌ Error updating attendance logs: {e}")


sync_current_log()
