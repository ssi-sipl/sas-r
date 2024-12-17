import time
import serial
import adafruit_fingerprint
import pandas as pd
import hashlib
import sys

# Add DFRobot_RGBLCD1602 library path and import the class
sys.path.append('../')  # Update this path if needed
from DFRobot_RGBLCD1602 import DFRobot_RGBLCD1602

# LCD Setup (I2C address 0x2D)
lcd = DFRobot_RGBLCD1602(rgb_addr=0x2D, col=16, row=2)  # Initialize LCD with 16 columns and 2 rows
lcd.set_RGB(0, 0, 255)  # Set display color to blue

# Serial setup for fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Load fingerprint database from CSV or create a new one
csv_file = 'fingerprint_data.csv'

try:
    df = pd.read_csv(csv_file)
except FileNotFoundError:
    df = pd.DataFrame(columns=['id', 'name', 'sha_key'])

# Function to display messages on the LCD
def display_message(line1, line2=""):
    """Display two lines of text on the LCD."""
    lcd.clear()
    lcd.set_cursor(0, 0)  # First line
    lcd.print_out(line1[:16])
    lcd.set_cursor(0, 1)  # Second line
    lcd.print_out(line2[:16])

# Utility Functions
def wait_and_prompt():
    """Wait for user action and show prompt on LCD."""
    display_message("Please Wait...", "")
    time.sleep(2)
    display_message("Ready to Scan", "")

def generate_sha_key(data):
    """Generate a SHA-256 hash for the provided data."""
    return hashlib.sha256(data.encode()).hexdigest()

# Core Functionalities
def enroll_fingerprint():
    """Enroll a new fingerprint and associate it with a name."""
    display_message("Enroll Finger", "Follow Steps")
    print("Enrolling a new fingerprint...")
    
    for _ in range(3):  # Attempt 3 times to get the image
        wait_and_prompt()
        while finger.get_image() != adafruit_fingerprint.OK:
            pass
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            display_message("Failed!", "Try Again")
            continue
        if finger.store_model(1) != adafruit_fingerprint.OK:
            display_message("Store Failed", "Retry")
            continue
        break
    else:
        display_message("Enroll Failed", "Max Attempts")
        return

    finger_id = input("Enter an ID for this fingerprint (0-127): ")
    if not finger_id.isdigit() or int(finger_id) < 0 or int(finger_id) > 127:
        display_message("Invalid ID", "Try Again")
        return

    finger_name = input("Enter a name for this fingerprint: ")
    sha_key = generate_sha_key(f"{finger_id}{finger_name}")

    if finger.store_model(int(finger_id)) == adafruit_fingerprint.OK:
        display_message("Enroll Success", f"ID: {finger_id}")
        global df
        # Add new fingerprint data to DataFrame
        new_entry = pd.DataFrame({'id': [int(finger_id)], 'name': [finger_name], 'sha_key': [sha_key]})
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(csv_file, index=False)
    else:
        display_message("Store Failed", "Retry Later")

def search_fingerprint():
    """Search for an existing fingerprint."""
    display_message("Search Finger", "Place Finger")
    wait_and_prompt()
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        display_message("Scan Failed", "")
        return
    if finger.finger_search() == adafruit_fingerprint.OK:
        finger_id = finger.finger_id
        record = df[df['id'] == finger_id]
        if not record.empty:
            display_message("Found!", f"Name: {record.iloc[0]['name']}")
        else:
            display_message("Found!", "No Name Set")
    else:
        display_message("Not Found", "Try Again")

def view_all_fingerprints():
    """View all enrolled fingerprints."""
    if df.empty:
        display_message("No Records", "Enroll First")
    else:
        display_message("Records on PC", "")
        print("All Enrolled Fingerprints:")
        print(df)

def delete_fingerprint():
    """Delete a fingerprint by ID."""
    display_message("Delete Finger", "Enter ID")
    try:
        finger_id = int(input("Enter the ID of the fingerprint to delete: "))
        if finger.delete_model(finger_id) == adafruit_fingerprint.OK:
            display_message("Deleted", f"ID: {finger_id}")
            global df
            df = df[df['id'] != finger_id]
            df.to_csv(csv_file, index=False)
        else:
            display_message("Delete Failed", "Invalid ID")
    except ValueError:
        display_message("Invalid Input", "Try Again")

# Main Menu
def main_menu():
    """Display the main menu on the LCD."""
    display_message("Fingerprint Menu", "1-5 to Choose")

def main():
    """Main program loop."""
    while True:
        main_menu()
        print("\nFingerprint System Menu:")
        print("1. Enroll Fingerprint")
        print("2. Search Fingerprint")
        print("3. View All Fingerprints")
        print("4. Delete Fingerprint")
        print("5. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            enroll_fingerprint()
        elif choice == '2':
            search_fingerprint()
        elif choice == '3':
            view_all_fingerprints()
        elif choice == '4':
            delete_fingerprint()
        elif choice == '5':
            display_message("Exiting...", "Goodbye!")
            print("Exiting system.")
            break
        else:
            display_message("Invalid Choice", "Try Again")

if __name__ == "__main__":
    main()
