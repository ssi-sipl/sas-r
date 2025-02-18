# Sync the users to the Google Sheet every day at 5 PM      
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
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


# Authenticate Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

def clean_dataframe(df):
    # Handle missing values (NaN, empty strings) by replacing them with None
    df = df.applymap(lambda x: None if isinstance(x, str) and x.strip() == '' else x)
    
    # Ensure the 'created_at' column is formatted as string
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.strftime('%a, %b %d, %Y %I:%M:%S %p')
    
    return df

# Function to update Employee Data
def sync_users():
    try:
        df = pd.read_csv(USERS_CSV)
        df = clean_dataframe(df)
        sheet = client.open(EMPLOYEE_SHEET_NAME).sheet1  # First sheet
        sheet.clear()  # Clear existing dataPARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))  # Move one level up
        sheet.append_rows([df.columns.tolist()] + df.values.tolist())  # Append new data
        print("✅ Employee data synced successfully!")
    except Exception as e:
        print(f"❌ Error updating employee sheet: {e}")

# Run both sync functions
sync_users()
