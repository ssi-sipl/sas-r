import time
import serial
import adafruit_fingerprint
import pandas as pd
import hashlib
from datetime import datetime

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Load fingerprint metadata database or create an empty one
metadata_csv = 'fingerprint_data.csv'
raw_data_csv = 'fingerprint_raw_data.csv'

try:
    metadata_df = pd.read_csv(metadata_csv)
except FileNotFoundError:
    metadata_df = pd.DataFrame(columns=['id', 'name', 'sha_key'])

try:
    raw_data_df = pd.read_csv(raw_data_csv)
except FileNotFoundError:
    raw_data_df = pd.DataFrame(columns=['timestamp', 'operation', 'finger_id', 'raw_data'])

def wait_and_prompt():
    """Display wait and ready prompts with a 2-second delay."""
    print("Wait...")
    time.sleep(2)  # Wait for 2 seconds
    print("Ready for scanning.")

def generate_sha_key(data):
    """Generate a SHA-256 hash for the provided data."""
    return hashlib.sha256(data.encode()).hexdigest()

def display_and_save_fingerprint_raw_data(data, operation, finger_id=None):
    """Display and save raw fingerprint data."""
    print("Raw Fingerprint Data:")
    print(data)
    
    # Save raw fingerprint data to CSV
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_raw_entry = pd.DataFrame({
        'timestamp': [timestamp],
        'operation': [operation],
        'finger_id': [finger_id if finger_id is not None else "N/A"],
        'raw_data': [data]
    })
    global raw_data_df
    raw_data_df = pd.concat([raw_data_df, new_raw_entry], ignore_index=True)
    raw_data_df.to_csv(raw_data_csv, index=False)

def enroll_fingerprint():
    """Enroll a new fingerprint and associate it with a name."""
    print("Enrolling a new fingerprint...")
    for _ in range(3):  # Attempt 3 times to get the image
        wait_and_prompt()
        while finger.get_image() != adafruit_fingerprint.OK:
            pass
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("Failed to process fingerprint. Try again.")
            continue
        # Display and save raw fingerprint data
        raw_data = finger.get_fpdata(sensorbuffer="image")
        display_and_save_fingerprint_raw_data(raw_data, "enroll")
        if finger.store_model(1) != adafruit_fingerprint.OK:
            print("Failed to store fingerprint. Try again.")
            continue
        break
    else:
        print("Failed to enroll fingerprint after 3 attempts.")
        return

    finger_id = input("Enter an ID for this fingerprint (0-127): ")
    if not finger_id.isdigit() or int(finger_id) < 0 or int(finger_id) > 127:
        print("Invalid ID. Enrollment failed.")
        return

    finger_name = input("Enter a name for this fingerprint: ")
    sha_key = generate_sha_key(f"{finger_id}{finger_name}")
    if finger.store_model(int(finger_id)) == adafruit_fingerprint.OK:
        print(f"Fingerprint enrolled successfully with ID {finger_id}.")
        global metadata_df
        # Use pd.concat() to add a new row to the dataframe
        new_entry = pd.DataFrame({'id': [int(finger_id)], 'name': [finger_name], 'sha_key': [sha_key]})
        metadata_df = pd.concat([metadata_df, new_entry], ignore_index=True)
        metadata_df.to_csv(metadata_csv, index=False)
    else:
        print("Failed to store fingerprint on the sensor.")

def search_fingerprint():
    """Search for an existing fingerprint."""
    wait_and_prompt()
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Failed to process fingerprint.")
        return
    # Display and save raw fingerprint data
    raw_data = finger.get_fpdata(sensorbuffer="image")
    display_and_save_fingerprint_raw_data(raw_data, "search")
    if finger.finger_search() == adafruit_fingerprint.OK:
        finger_id = finger.finger_id
        print(f"Fingerprint found! ID: {finger_id}")
        record = metadata_df[metadata_df['id'] == finger_id]
        if not record.empty:
            print(f"Name: {record.iloc[0]['name']}")
            print(f"SHA Key: {record.iloc[0]['sha_key']}")
        else:
            print("No name associated with this fingerprint.")
    else:
        print("Fingerprint not found.")

def view_all_fingerprints():
    """View all enrolled fingerprints."""
    if metadata_df.empty:
        print("No fingerprints enrolled.")
    else:
        print("All Enrolled Fingerprints:")
        print(metadata_df)

def delete_fingerprint():
    """Delete a fingerprint by ID."""
    try:
        finger_id = int(input("Enter the ID of the fingerprint to delete: "))
        if finger.delete_model(finger_id) == adafruit_fingerprint.OK:
            print(f"Fingerprint with ID {finger_id} deleted successfully.")
            global metadata_df
            metadata_df = metadata_df[metadata_df['id'] != finger_id]
            metadata_df.to_csv(metadata_csv, index=False)
        else:
            print("Failed to delete fingerprint.")
    except ValueError:
        print("Invalid ID.")

def main():
    while True:
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
            print("Exiting system.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
