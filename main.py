import time
import serial
import logging
import adafruit_fingerprint
import RPi.GPIO as GPIO
from library import AttendanceSystemManager
from config import GPIO_PINS, SERIAL_CONFIG, FINGERPRINT_RETRY_LIMIT

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_PINS["ACCESS_GRANTED_LED"], GPIO.OUT)
GPIO.setup(GPIO_PINS["NOT_AUTHORISED_LED"], GPIO.OUT)

# Initialize serial connection for fingerprint sensor
uart = serial.Serial(SERIAL_CONFIG["port"], baudrate=SERIAL_CONFIG["baudrate"], timeout=SERIAL_CONFIG["timeout"])
finger = adafruit_fingerprint.AdafruitFingerprint(uart)


MANAGER = None

def initialize_manager():
    global MANAGER
    try:
        MANAGER = AttendanceSystemManager()
        logging.info("AttendanceSystemManager initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize AttendanceSystemManager: {e}")
        logging.info("Exiting system.")
        GPIO.cleanup()
        MANAGER = None
        exit()

def enable_user():  
    fingerprint_id = input("Enter fingerprint ID to enable: ").strip()
    if not fingerprint_id:
        logging.error("Fingerprint ID cannot be empty.")
        return
    try:
        response = MANAGER.enable_user(fingerprint_id)
        if response["status"]:
            logging.info(response["message"])
        else:
            logging.error(response["message"])
    except Exception as e:
        logging.error(f"Error occurred during user enablement: {e}")

def disable_user():
    fingerprint_id = input("Enter fingerprint ID to disable: ").strip()
    if not fingerprint_id:
        logging.error("Fingerprint ID cannot be empty.")
        return
    try:
        response = MANAGER.disable_user(fingerprint_id)
        if response["status"]:
            logging.info(response["message"])
        else:
            logging.error(response["message"])
    except Exception as e:
        logging.error(f"Error occurred during user disablement: {e}")

def print_all_users():
    try:
        response = MANAGER.fetch_all_users()
        if response["status"]:
            users = response["data"]
            logging.info(f"Total users: {response['count']}")
            logging.info("=== All Users ===")
            logging.info(f"{'Employee ID':<15} {'First Name':<15} {'Last Name':<15} {'Fingerprint ID':<15} {'Disabled':<10} {'Created At':<30}")
            for user in users:
                logging.info(f"{user['employee_id']:<15} {user['first_name']:<15} {user['last_name']:<15} {user['fingerprint_id']:<15} {user['is_disabled']:<10} {user['created_at']:<30}")
        else:
            logging.error(response["message"])
    except Exception as e:
        logging.error(f"Error occurred in print_all_users: {e}")

def print_attendance_logs():
    try:
        date = input("Enter the date (yy-mm-dd): ").strip()
        if not date:
            logging.error("Date cannot be empty.")
            return
        response = MANAGER.fetch_attendance(date)
        if response["status"]:
            logs = response["data"]
            logging.info(f"Total logs: {response['count']}")
            logging.info("=== All Attendance Logs ===")
            logging.info(f"{'Employee ID':<15} {'First Name':<15} {'Last Name':<15} {'Entry Time':<15} {'Exit Time':<15} {'Total Hours':<15} {'is_late'} {'Created At':<30}")
            for log in logs:
                logging.info(f"{log['employee_id']:<15} {log['first_name']:<15} {log['last_name']:<15} {log['entry_time']:<15} {log['exit_time']:<15} {log['total_hours']:<15} {log['is_late']:<10} {log['created_at']:<30}")
        else:
            logging.error(response["message"])
    except Exception as e:
        logging.error(f"Error occurred in print_attendance_logs: {e}")

def print_a_user():
    fingerprint_id = input("Enter fingerprint ID to fetch: ").strip()
    if not fingerprint_id:
        logging.error("Fingerprint ID cannot be empty.")
        return
    try:
        response = MANAGER.fetch_user(fingerprint_id)
        if response["status"]:
            user = response["data"]
            logging.info("=== User Details ===")
            logging.info(f"{'Employee ID':<15} {'First Name':<15} {'Last Name':<15} {'Fingerprint ID':<15} {'Disabled':<10} {'Created At':<30}")
            logging.info(f"{user['employee_id']:<15} {user['first_name']:<15} {user['last_name']:<15} {user['fingerprint_id']:<15} {user['is_disabled']:<10} {user['created_at']:<30}")
        else:
            logging.error(response["message"])
    except Exception as e:
        logging.error(f"Error occurred in print_a_user: {e}")

def delete_user():
    fingerprint_id = input("Enter fingerprint ID to delete: ").strip()
    if not fingerprint_id:
        logging.error("Fingerprint ID cannot be empty.")
        return

    try:
        response = MANAGER.delete_user(fingerprint_id)
        if response["status"]:
            logging.info(response["message"])
        else:
            logging.error(response["message"])
    except Exception as e:
        logging.error(f"Error occurred during user deletion: {e}")

def capture_fingerprint(retry_limit):
    logging.info("Place your finger on the sensor.")
    for attempt in range(retry_limit):
        if finger.gen_img() == adafruit_fingerprint.OK:
            if finger.img_2Tz(1) == adafruit_fingerprint.OK:
                logging.info("Fingerprint captured and converted.")
                return True
            logging.warning("Failed to convert image to template.")
            return False
        time.sleep(1)
    logging.error("Timeout: Fingerprint capture failed.")
    return False

def get_new_finger_id():
    try:
        if finger.read_templates() == adafruit_fingerprint.OK:
            logging.info("Reading stored fingerprints...")
            logging.info(f"Stored fingerprint IDs: {finger.templates}")

            for fid in range(1, 128):
                if fid not in finger.templates:
                    logging.info(f"Available fingerprint ID: {fid}")
                    return fid

            logging.warning("Sensor storage is full.")
            return None
        else:
            logging.error("Failed to read stored fingerprints.")
    except Exception as e:
        logging.error(f"Error occurred in get_new_finger_id: {e}")
    return None

def enroll_fingerprint():
    try:
        if not capture_fingerprint(FINGERPRINT_RETRY_LIMIT):
            return

        logging.info("Remove finger and place it again.")
        time.sleep(2)

        if not capture_fingerprint(FINGERPRINT_RETRY_LIMIT):
            return

        if finger.create_model() != adafruit_fingerprint.OK:
            logging.error("Failed to create fingerprint model.")
            return

        fingerprint_id = get_new_finger_id()
        if fingerprint_id is None:
            logging.error("No available storage slots on sensor.")
            return

        logging.info(f"Auto Generated Fingerprint ID: {fingerprint_id}")

        if finger.store_model(fingerprint_id) == adafruit_fingerprint.OK:
            logging.info(f"Fingerprint stored successfully at ID {fingerprint_id}.")
        else:
            logging.error("Failed to store fingerprint in sensor.")
            return

        # Enroll user in the system
        first_name = input("Enter your first name: ").strip()
        last_name = input("Enter your last name: ").strip()
        employee_id = input("Enter your employee ID: ").strip()
        if not first_name or not last_name or not employee_id:
            logging.error("First name, last name, and employee ID cannot be empty.")
            return

        try:
            response = MANAGER.enroll_new_user(first_name, last_name, fingerprint_id, employee_id)
            if response["status"]:
                logging.info(f"Enrollment successful: {response['message']}")
            else:
                logging.error(f"Enrollment failed: {response['message']}")
        except Exception as e:
            logging.error(f"Error occurred during enrollment: {e}")
    except Exception as e:
        logging.error(f"Error occurred in enroll_fingerprint: {e}")

def listen_for_fingerprint(timeout=30):
    logging.info("Waiting for fingerprint...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        if capture_fingerprint(FINGERPRINT_RETRY_LIMIT):
            if finger.finger_search() == adafruit_fingerprint.OK:
                fingerprint_id = finger.finger_id
                logging.info(f"Fingerprint ID {fingerprint_id} recognized.")
                return fingerprint_id
    logging.warning("Timeout: No fingerprint detected.")
    return None

def monitor_fingerprint():
    print("Monitoring fingerprints for Attendance...")
    try:
        while True:
            fingerprint_id = listen_for_fingerprint()
            if fingerprint_id is not None:
                try:
                    response = MANAGER.handle_attendance(fingerprint_id)
                    if response["status"]:
                        logging.info(response["message"])
                        GPIO.output(GPIO_PINS["ACCESS_GRANTED_LED"], GPIO.HIGH)
                        time.sleep(1)
                        GPIO.output(GPIO_PINS["ACCESS_GRANTED_LED"], GPIO.LOW)
                    else:
                        logging.info(response["message"])
                        GPIO.output(GPIO_PINS["NOT_AUTHORISED_LED"], GPIO.HIGH)
                        time.sleep(1)
                        GPIO.output(GPIO_PINS["NOT_AUTHORISED_LED"], GPIO.LOW)
                except Exception as e:
                    logging.error(f"Error during attendance handling: {e}")
            time.sleep(2)
    except KeyboardInterrupt:
        logging.info("Exiting system.")
        GPIO.cleanup()
    except Exception as e:
        logging.error(f"Error in monitor_fingerprint: {e}")
        GPIO.cleanup()

def show_menu():
    print("\n=== Attendance System Manager ===")
    print("1. Enroll New Fingerprint")
    print("2. Monitor Attendance")
    print("3. Fetch all Attendance Logs")
    print("4. Fetch all Users")
    print("5. Fetch a User")
    print("6. Delete a User")
    print("7. Enable a User")
    print("8. Disable a User")
    print("9. Exit")
    print("===========================================")
    choice = input("Enter your choice (1/2/3/4/5/6/7/8/9): ").strip()
    return choice

if __name__ == "__main__":

    initialize_manager()

    while True:
        choice = show_menu()

        if choice == "1":
            enroll_fingerprint()
        elif choice == "2":
            monitor_fingerprint()
        elif choice == "3":
            print_attendance_logs()
        elif choice == "4":
            print_all_users()
        elif choice == "5":
            print_a_user()
        elif choice == "6":
            delete_user()
        elif choice == "7":
            enable_user()
        elif choice == "8":
            disable_user()
        elif choice == "9":
            logging.info("Exiting the system. Goodbye!")
            GPIO.cleanup()
            break
        else:
            print("Invalid choice. Please try again.")
