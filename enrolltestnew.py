import time
import serial
import adafruit_fingerprint
import requests  # For making POST requests
import hashlib
import uuid

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Backend API endpoint
# Replace with your actual backend URL
ENROLL_ENDPOINT = "https://attendance-system-backend-ptbf.onrender.com/api/users/enroll"


def wait_and_prompt():
    print("Wait...")
    time.sleep(2)
    print("Ready for scanning.")


#def clear_fingerprint_buffer():
#    """
#    Clears the fingerprint sensor temporary buffer slots (for current scan).
#    """
#    # Attempt to clear the current fingerprint data (temporary buffer)
#    result = finger.empty_finger()  # Clears the buffer temporarily
#    if result == adafruit_fingerprint.OK:
#        print("Fingerprint buffer cleared successfully.")
#    else:
#        print(f"Failed to clear fingerprint buffer. Error code: {result}")

def hash_fingerprint_template(template):
    if not template:
        raise ValueError("Template cannot be empty or None.")
    template_bytes = bytes(template)
    unique_id = str(uuid.uuid4()).encode()  # Generate a unique ID
    sha256_hash = hashlib.sha256(template_bytes + unique_id).hexdigest()
    return sha256_hash


def enroll_fingerprint():

    print("Clearing fingerprint buffer...")
    #clear_fingerprint_buffer()  # Clear buffer before starting a new enrollment

    
    print("Put you finger on the sensor to enroll.")
    for _ in range(3):  # Attempt 3 times to get the image
        wait_and_prompt()
        while finger.get_image() != adafruit_fingerprint.OK:
            pass
        if finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("Failed to capture the fingerprint. Try again.")
            continue
        break
    else:
        print("Failed to capture the fingerprint after 3 attempts.")
        return

    template = finger.get_fpdata("char", 1)  # fingerprint template

    if template is None:
        print("Failed to retrieve fingerprint template.")
        return

    try:
        hashed_template = hash_fingerprint_template(template)
    except ValueError as e:
        print(e)
        return

    first_name = input("Enter your first name: ")
    last_name = input("Enter your last name: ")

    if not (first_name) or not (last_name):
        print("First name and last name cannot be empty.")
        return

    try:
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "fingerprint_id": hashed_template
        }
        response = requests.post(ENROLL_ENDPOINT, json=payload)
        if response.status_code == 200:
            print("Enrollment Successfull.")
            print("Backend Response:", response.json())
        else:
            print("Enrollment Failed.")
            print("Backend Response:", response.text)
    except requests.RequestException as e:
        print(f"Error sending data to Server: {e}")


def main():
    while True:
        print("Press 'E' to enroll a new fingerprint.")
        print("Press 'Q' to quit the program.")
        choice = input("Enter your choice: ").upper()
        if choice == "E":
            enroll_fingerprint()
        elif choice == "Q":
            print("Quitting the program.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
