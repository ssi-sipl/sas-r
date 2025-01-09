# Updated Enrollment Script
import time
import serial
import adafruit_fingerprint
import requests

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Backend API endpoint
ENROLL_ENDPOINT = "https://attendance-system-backend-ptbf.onrender.com/api/users/enroll"

def get_new_finger_id():
    """Get a new unique fingerprint ID for storage on the sensor."""
    for fid in range(1, 128):  # Sensor supports up to 127 fingerprints
        if finger.load_model(fid) != adafruit_fingerprint.OK:
            return fid
    return None

def enroll_fingerprint():
    print("Place your finger on the sensor to enroll.")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Failed to convert image to template.")
        return

    print("Remove finger and place it again.")
    time.sleep(2)

    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    if finger.image_2_tz(2) != adafruit_fingerprint.OK:
        print("Failed to convert image to template on second attempt.")
        return

    if finger.create_model() != adafruit_fingerprint.OK:
        print("Failed to create fingerprint model.")
        return

    finger_id = get_new_finger_id()
    if finger_id is None:
        print("No available storage slots on sensor.")
        return

    if finger.store_model(finger_id) != adafruit_fingerprint.OK:
        print("Failed to store fingerprint on sensor.")
        return

    first_name = input("Enter your first name: ")
    last_name = input("Enter your last name: ")
    if not first_name or not last_name:
        print("First name and last name cannot be empty.")
        return

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "finger_id": finger_id
    }
    try:
        response = requests.post(ENROLL_ENDPOINT, json=payload)
        if response.status_code == 200:
            print("Enrollment successful.")
        else:
            print("Enrollment failed:", response.text)
    except requests.RequestException as e:
        print(f"Error enrolling fingerprint: {e}")

def main():
    while True:
        print("Press 'E' to enroll a new fingerprint.")
        print("Press 'Q' to quit.")
        choice = input("Enter your choice: ").upper()
        if choice == "E":
            enroll_fingerprint()
        elif choice == "Q":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
