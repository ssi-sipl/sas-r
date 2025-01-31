# Updated Enrollment Script
import time
import serial
import adafruit_fingerprint
# import requests
from library import AttendanceSystemManager

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Backend API endpoint
ENROLL_ENDPOINT = "https://attendance-system-backend-ptbf.onrender.com/api/users/enroll"

MANAGER = None

def initialize_manager():
    global MANAGER
    try:
        MANAGER = AttendanceSystemManager()
        print("AttendanceSystemManager initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize AttendanceSystemManager: {e}")
        print("Exiting system.")
        MANAGER = None
        exit()

def get_new_finger_id():
    """
    Get a new unique fingerprint ID for storage on the sensor.
    """
    if finger.read_templates() == adafruit_fingerprint.OK:  # Read all stored fingerprint IDs
        print("Reading stored fingerprints...")
        print("Stored fingerprint IDs:", finger.templates)
        
        if not finger.templates:
            print("No fingerprints stored. fingerprint_id will start from 1.")
            return 1  # If no fingerprints are stored, start with ID 1

        print()
        # Find the first available ID (1-127)
        for fid in range(1, 128):
            print(f"Checking fingerprint ID: {fid}")
            if fid not in finger.templates:
                print(f"Available fingerprint ID: {fid}")
                return fid
            print("Fingerprint ID already exists. Checking next ID...")
            print()

        print("Sensor storage is full.")
        return None
    else:
        print("Failed to read stored fingerprints.")

def check_stored_fingerprints():
    """
    Prints all stored fingerprint IDs.
    """
    print("These are the stored fingerprints:")
    
    if finger.read_templates() == adafruit_fingerprint.OK:
        print("Stored fingerprint IDs:", finger.templates)
    else:
        print("Failed to read stored fingerprints.")
    print("Total stored fingerprints:", len(finger.templates))



def clear_fingerprint_buffer():
    """
    Clears the fingerprint sensor buffer slots.
    """
    if finger.empty_library() == adafruit_fingerprint.OK:
        print("Fingerprint buffer cleared successfully.")
    else:
        print("Failed to clear fingerprint buffer.")

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

    fingerprint_id = get_new_finger_id()
    if fingerprint_id is None:
        print("No available storage slots on sensor.")
        return
    
    print("Auto Generated Fingerprint Id:", fingerprint_id)

    if finger.store_model(fingerprint_id) == adafruit_fingerprint.OK:
        print(f"Fingerprint stored successfully at ID {fingerprint_id}.")
    else:
        print("Failed to store fingerprint in sensor.")
        return


    print("Fingerprint Id:", fingerprint_id)

    first_name = input("Enter your first name: ")
    last_name = input("Enter your last name: ")
    employee_id = input("Enter your employee ID: ")
    if not first_name or not last_name or not employee_id:
        print("First name, last name, and employee ID cannot be empty.")
        return
    

    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "employee_id": employee_id,
        "fingerprint_id": str(fingerprint_id)
    }
    try:
        response = MANAGER.enroll_new_user(first_name, last_name, fingerprint_id, employee_id)
        # response = requests.post(ENROLL_ENDPOINT, json=payload)
        if response["status"]:
            print(f"Enrollment successful: {response['message']}")
        else:
            print(f"Enrollment failed: {response['message']}")
            print("Enrollment successful.")
        
    except Exception as e:
        print(f"Error enrolling fingerprint: {e}")

def main():
    while True:
        print("Press 'E' to enroll a new fingerprint.")
        print("Press 'C' to check stored fingerprints.")
        print("Press 'Q' to quit.")
        choice = input("Enter your choice: ").upper()
        if choice == "E":
            enroll_fingerprint()
        elif choice == "Q":
            print("Exiting program.")
            break
        elif choice == "C":
            check_stored_fingerprints()
            
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    initialize_manager()
    main()
