import time
import serial
import adafruit_fingerprint
import pandas as pd
import requests  # For making POST requests

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.AdafruitFingerprint(uart)

# Load fingerprint database from CSV or create an empty one
csv_file = 'fingerprint_data.csv'

try:
    df = pd.read_csv(csv_file)
except FileNotFoundError:
    df = pd.DataFrame(columns=['id', 'name'])

# Backend API endpoint
ENROLL_ENDPOINT = "https://attendance-system-backend-ptbf.onrender.com/api/users/enroll"  # Replace with your actual backend URL

def wait_and_prompt():
    """Display wait and ready prompts with a 2-second delay."""
    print("Wait...")
    time.sleep(2)  # Wait for 2 seconds
    print("Ready for scanning.")

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
    if finger.store_model(int(finger_id)) == adafruit_fingerprint.OK:
        print(f"Fingerprint enrolled successfully with ID {finger_id}.")
        global df
        # Use pd.concat() to add a new row to the dataframe
        new_entry = pd.DataFrame({'id': [int(finger_id)], 'name': [finger_name]})
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(csv_file, index=False)

        # Send a POST request to the backend
        try:
            payload = {
                "first_name": finger_name.split()[0],  # Assuming first name is the first word
                "last_name": " ".join(finger_name.split()[1:]),  # Remaining words as last name
                "fingerprint_id": int(finger_id)
            }
            response = requests.post(ENROLL_ENDPOINT, json=payload)
            if response.status_code == 200:
                print("Enrollment data successfully sent to the backend.")
                print("Backend Response:", response.json())
            else:
                print("Failed to send data to the backend.")
                print("Backend Response:", response.text)
        except requests.RequestException as e:
            print(f"Error sending data to backend: {e}")
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
    if finger.finger_search() == adafruit_fingerprint.OK:
        finger_id = finger.finger_id
        print(f"Fingerprint found! ID: {finger_id}")
        record = df[df['id'] == finger_id]
        if not record.empty:
            print(f"Name: {record.iloc[0]['name']}")
            print(f"Raw Data: {record.iloc[0]['raw_data']}")
        else:
            print("No name associated with this fingerprint.")
    else:
        print("Fingerprint not found.")

def view_all_fingerprints():
    """View all enrolled fingerprints."""
    if df.empty:
        print("No fingerprints enrolled.")
    else:
        print("All Enrolled Fingerprints:")
        print(df[['id', 'name', 'raw_data']])

def delete_fingerprint():
    """Delete a fingerprint by ID."""
    try:
        finger_id = int(input("Enter the ID of the fingerprint to delete: "))
        if finger.delete_model(finger_id) == adafruit_fingerprint.OK:
            print(f"Fingerprint with ID {finger_id} deleted successfully.")
            global df
            df = df[df['id'] != finger_id]
            df.to_csv(csv_file, index=False)
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
