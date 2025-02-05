import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os

# Load Google Sheets API credentials
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

SYNC_TRACKER_FILE = os.path.join(SCRIPT_DIR, "synced_files.txt")

# Authenticate Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

# Function to update Employee Data
def update_users_sheet():
    try:
        df = pd.read_csv(USERS_CSV)
        sheet = client.open(EMPLOYEE_SHEET_NAME).sheet1  # First sheet
        sheet.clear()  # Clear existing data
        sheet.append_rows([df.columns.tolist()] + df.values.tolist())  # Append new data
        print("✅ Employee data synced successfully!")
    except Exception as e:
        print(f"❌ Error updating employee sheet: {e}")

# Function to read already synced files
def get_synced_files():
    if os.path.exists(SYNC_TRACKER_FILE):
        with open(SYNC_TRACKER_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

# Function to update Daily Attendance Logs
def update_attendance_logs():
    try:
        sheet = client.open(ATTENDANCE_SHEET_NAME)
        synced_files = get_synced_files()  # Get previously synced files

        for filename in os.listdir(ATTENDANCE_FOLDER):
            if filename.endswith(".csv") and filename not in synced_files:
                date = filename.replace(".csv", "")  # Extract date from filename
                df = pd.read_csv(os.path.join(ATTENDANCE_FOLDER, filename))
                
                try:
                    worksheet = sheet.worksheet(date)  # Try to find existing sheet
                except gspread.exceptions.WorksheetNotFound:
                    worksheet = sheet.add_worksheet(title=date, rows="1000", cols="10")  # Create new sheet
                
                worksheet.clear()  # Clear previous data
                worksheet.append_rows([df.columns.tolist()] + df.values.tolist())  # Append new data
                
                # Mark file as synced
                with open(SYNC_TRACKER_FILE, "a") as f:
                    f.write(filename + "\n")

                print(f"✅ Synced attendance log for {date}")
            else:
                print(f"🔄 Skipping already synced file: {filename}")
    except Exception as e:
        print(f"❌ Error updating attendance logs: {e}")

# Run both sync functions
update_users_sheet()
update_attendance_logs()
