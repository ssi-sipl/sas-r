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

def capture_fingerprint(retry_limit):
    logging.info("Place your finger on the sensor.")
    for attempt in range(retry_limit):
        if finger.gen_image() == adafruit_fingerprint.OK:
            if finger.image_2_tz(1) == adafruit_fingerprint.OK:
                logging.info("Fingerprint captured and converted.")
                return True
            logging.warning("Failed to convert image to template.")
            return False
        time.sleep(1)
    logging.error("Timeout: Fingerprint capture failed.")
    return False

def enroll_fingerprint():
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

if __name__ == "__main__":
    initialize_manager()
    monitor_fingerprint()
