import pandas as pd
import os
from datetime import datetime, timedelta

class AttendanceSystemManager:
    def __init__(self, user_csv="users.csv", attendance_dir="attendance_logs"):
        # File and directory paths
        self.user_csv = user_csv
        self.attendance_dir = attendance_dir
        
        # Columns for the user DataFrame
        self.user_headers = ["employee_id", "first_name", "last_name", "fingerprint_id", "is_disabled", "created_at"]
        self.users_df = pd.DataFrame(columns=self.user_headers)

        self.attendance_headers = [
            "employee_id", "first_name", "last_name", "entry_time", "exit_time", "status", 
            "total_time", "is_late", "created_at"
        ]

        # Initialize files and directories
        self._initialize_user_csv()
        self._initialize_attendance_directory()

    def _initialize_user_csv(self):
        """Initialize the user CSV file and load data."""
        if not os.path.exists(self.user_csv):
            print(f"Creating {self.user_csv}")
            self.users_df.to_csv(self.user_csv, index=False)
        else:
            print(f"Loading existing file: {self.user_csv}")
            self.users_df = pd.read_csv(self.user_csv, dtype={
                'employee_id': str,
                'first_name': str,
                'last_name': str,
                'fingerprint_id': str,
                'is_disabled': str,
                'created_at': str
            })

    def _initialize_attendance_directory(self):
        """Ensure the attendance log directory exists."""
        if not os.path.exists(self.attendance_dir):
            print(f"Creating directory: {self.attendance_dir}")
            os.makedirs(self.attendance_dir)

    def _save_users_to_csv(self):
        """Save the users DataFrame to the CSV file."""
        self.users_df.to_csv(self.user_csv, index=False)

    @staticmethod
    def _capitalize(string):
        """Capitalize the first letter of a string."""
        return string.capitalize()

    @staticmethod
    def _clean_name(name):
        """Remove non-alphabetic characters from a name."""
        return "".join(filter(str.isalpha, name))
    
    @staticmethod
    def _calculate_time_spent(entry_time, exit_time):
        """Calculate total time spent."""
        try:
            entry = datetime.strptime(entry_time, "%I:%M:%S %p")
            exit = datetime.strptime(exit_time, "%I:%M:%S %p")
            time_diff = exit - entry
            return str(time_diff)
        except Exception:
            return ""

    def enroll_new_user(self, first_name, last_name, fingerprint_id, employee_id):
        """Enroll a new user."""
        cleaned_first_name = self._capitalize(self._clean_name(first_name.strip()))
        cleaned_last_name = self._capitalize(self._clean_name(last_name.strip()))
        cleaned_fingerprint_id = str(fingerprint_id).strip()
        cleaned_employee_id = str(employee_id).strip()

        # Check for duplicate fingerprint ID or employee ID
        if not self.users_df[
            (self.users_df["fingerprint_id"] == cleaned_fingerprint_id) | 
            (self.users_df["employee_id"] == cleaned_employee_id)
        ].empty:
            return {"status": False, "message": "User already exists."}

        # Add new user
        new_user = {
            "employee_id": cleaned_employee_id,
            "first_name": str(cleaned_first_name),
            "last_name": str(cleaned_last_name),
            "fingerprint_id": cleaned_fingerprint_id,
            "is_disabled": "False",
            "created_at": str(datetime.now().strftime("%a, %b %d, %Y %I:%M:%S %p")),
        }
        self.users_df = self.users_df._append(new_user, ignore_index=True)
        self._save_users_to_csv()
        return {"status": True, "message": "User enrolled successfully.", "data": new_user}

    def fetch_all_users(self):
        """Fetch all users."""
        if self.users_df.empty:
            return {"status": False, "message": "No users found."}
        return {
            "status": True,
            "message": "Users fetched successfully.",
            "count": len(self.users_df),
            "data": self.users_df.to_dict(orient="records"),
        }

    def delete_user(self, fingerprint_id):
        """Delete a user by fingerprint ID."""
        fingerprint_id = str(fingerprint_id).strip()

        if str(fingerprint_id) not in self.users_df["fingerprint_id"].astype(str).values:
            return {"status": False, "message": "User not found."}

        self.users_df = self.users_df[self.users_df["fingerprint_id"].astype(str) != str(fingerprint_id)]
        self._save_users_to_csv()
        return {"status": True, "message": "User deleted successfully."}
    
    def handle_attendance(self, fingerprint_id):
        """Handle attendance logging with entry and exit logic."""
        # Clean and validate fingerprint_id
        cleaned_fingerprint_id = str(fingerprint_id).strip()

        # Find user
        user = self.users_df[self.users_df["fingerprint_id"] == cleaned_fingerprint_id]
        if user.empty:
            return {"status": False, "message": "User doesn't exist."}

        # Check if user is disabled
        if user.iloc[0]["is_disabled"] == "True":
            return {"status": False, "message": "Access Denied. ( Disabled User )"}

        # Extract user details
        employee_id = str(user.iloc[0]["employee_id"])
        first_name = str(user.iloc[0]["first_name"])
        last_name = str(user.iloc[0]["last_name"])

        # Prepare date and file paths
        current_date = datetime.now().strftime("%Y-%m-%d")
        attendance_file = os.path.join(self.attendance_dir, f"{current_date}.csv")

        # Read or create attendance DataFrame
        if os.path.exists(attendance_file):
            attendance_df = pd.read_csv(attendance_file, dtype={
                'employee_id': str,
                'first_name': str,
                'last_name': str,
                'entry_time': str,
                'exit_time': str,
                'status': str,
                'total_time': str,
                'is_late': str,
                'created_at': str
            })
        else:
            attendance_df = pd.DataFrame(columns=self.attendance_headers)

        # Check existing log for today
        existing_log = attendance_df[
            (attendance_df["employee_id"] == employee_id) & 
            (attendance_df["created_at"] == str(current_date))
        ]

        # Current time
        current_time = datetime.now().strftime("%I:%M:%S %p")
        late_threshold = datetime.strptime("10:30:00 AM", "%I:%M:%S %p")
        is_late = datetime.strptime(current_time, "%I:%M:%S %p") > late_threshold

        if not existing_log.empty:
            # Handle exit logic
            if existing_log.iloc[0]["status"] == "OUT":
                return {
                    "status": False, 
                    "message": "Once exited, you cannot enter back on the same day."
                }

            # Calculate total time
            total_time = self._calculate_time_spent(
                existing_log.iloc[0]["entry_time"], 
                current_time
            )

            # Update existing log
            mask = (attendance_df["employee_id"] == employee_id) & (attendance_df["created_at"] == str(current_date))
            attendance_df.loc[mask, "exit_time"] = str(current_time)
            attendance_df.loc[mask, "status"] = "OUT"
            attendance_df.loc[mask, "total_time"] = str(total_time)
            attendance_df.loc[mask, "is_late"] = str(is_late)

            attendance_df.to_csv(attendance_file, index=False)

            return {
                "status": True,
                "message": f"Exit successful. Goodbye {first_name} {last_name}!",
                "data": {"first_name": first_name, "last_name": last_name, "employee_id": employee_id}
            }

        # Handle entry logic
        new_log = {
            "employee_id": employee_id,
            "first_name": first_name,
            "last_name": last_name,
            "entry_time": str(current_time),
            "exit_time": "",
            "status": "IN",
            "total_time": "",
            "created_at": str(current_date),
            "is_late": str(is_late)
        }

        attendance_df = attendance_df._append(new_log, ignore_index=True)
        attendance_df.to_csv(attendance_file, index=False)

        return {
            "status": True,
            "message": f"Entry successful. Welcome {first_name} {last_name}!",
            "data": {"first_name": first_name, "last_name": last_name, "employee_id": employee_id}
        }

    def fetch_attendance(self, date=None):
        """Fetch attendance for a specific date or today."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        attendance_file = os.path.join(self.attendance_dir, f"{date}.csv")

        if not os.path.exists(attendance_file):
            return {"status": False, "message": f"No attendance records found for {date}."}

        attendance_df = pd.read_csv(attendance_file, dtype={
            'employee_id': str,
            'first_name': str,
            'last_name': str,
            'entry_time': str,
            'exit_time': str,
            'status': str,
            'total_time': str,
            'is_late': str,
            'created_at': str
        })
        return {
            "status": True,
            "message": "Attendance records fetched successfully.",
            "count": len(attendance_df),
            "data": attendance_df.to_dict(orient="records"),
        }
    
    def disable_user(self, fingerprint_id):
        fingerprint_id = str(fingerprint_id).strip()

        if str(fingerprint_id) not in self.users_df["fingerprint_id"].astype(str).values:
            return {"status": False, "message": "User not found."}
        
         # Check if the user is already enabled
        is_disabled = self.users_df.loc[self.users_df["fingerprint_id"] == str(fingerprint_id), "is_disabled"].iloc[0]
        if is_disabled == "True":
            return {"status": False, "message": "User is already disabled."}

        self.users_df.loc[self.users_df["fingerprint_id"] == str(fingerprint_id), "is_disabled"] = "True"

        self._save_users_to_csv()

        return {"status": True, "message": "User disabled successfully."}
    
    def enable_user(self, fingerprint_id):
        fingerprint_id = str(fingerprint_id).strip()

        if str(fingerprint_id) not in self.users_df["fingerprint_id"].astype(str).values:
            return {"status": False, "message": "User not found."}

        # Check if the user is already enabled
        is_disabled = self.users_df.loc[self.users_df["fingerprint_id"] == str(fingerprint_id), "is_disabled"].iloc[0]
        if is_disabled == "False":
            return {"status": False, "message": "User is already enabled."}

        # Enable the user
        self.users_df.loc[self.users_df["fingerprint_id"] == str(fingerprint_id), "is_disabled"] = "False"
        self._save_users_to_csv()

        return {"status": True, "message": "User enabled successfully."}

    
    def fetch_user(self, fingerprint_id):
        fingerprint_id = str(fingerprint_id).strip()

        if str(fingerprint_id) not in self.users_df["fingerprint_id"].astype(str).values:
            return {"status": False, "message": "User not found."}

        user = self.users_df[self.users_df["fingerprint_id"] == str(fingerprint_id)]

        return {
            "status": True,
            "message": "User fetched successfully.",
            "data": user.to_dict(orient="records")
        }

# Example Usage
if __name__ == "__main__":
    pass
    # manager = AttendanceSystemManager()

    # Enroll a new user
    # print(manager.enroll_new_user("John", "Doe", "12345", "001"))

    # # Fetch all users
    # print(manager.fetch_all_users())

    # # Fetch a specific user
    # print(manager.fetch_user("12345"))

    # # Handle attendance (entry)
    # print(manager.handle_attendance("12345"))

    # # Handle attendance (exit)
    # print(manager.handle_attendance("12345"))

    # # Fetch attendance for today
    # print(manager.fetch_attendance())

    # # Disable a user
    # print(manager.disable_user("12345"))

    # # Enable a user
    # print(manager.enable_user("12345"))

    # # Delete a user
    # print(manager.delete_user("12345"))

    # # Fetch all users after deletion
    # print(manager.fetch_all_users())
    