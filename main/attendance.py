import time
import serial
import adafruit_fingerprint
import requests
import RPi.GPIO as GPIO
from library import AttendanceSystemManager

# GPIO Pin Setup (Physical Board Pins)
ACCESS_GRANTED_LED_PIN = 15  # Physical pin 15 (GPIO22)
NOT_AUTHORISED_LED_PIN = 16  # Physical pin 16 (GPIO23)

# Backend API Configuration
ATTENDANCE_ENDPOINT = "https://attendance-system-backend-ptbf.onrender.com/api/logs/attendance"

# Setup GPIO mode and pin configuration
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ACCESS_GRANTED_LED_PIN, GPIO.OUT)
GPIO.setup(NOT_AUTHORISED_LED_PIN, GPIO.OUT)

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

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

def clear_fingerprint_buffer():
    """
    Clears the fingerprint sensor buffer slots.
    """
    if finger.empty_library() == adafruit_fingerprint.OK:
        print("Fingerprint buffer cleared successfully.")
    else:
        print("Failed to clear fingerprint buffer.")

def process_fingerprint():
    print("\n=== Starting fingerprint processing ===")
    print("Waiting for finger placement...")
    
    # Get the image
    get_image_result = finger.get_image()
    if get_image_result != adafruit_fingerprint.OK:
        print(f"Failed to get image. Error code: {get_image_result}")
        return
    print("Image taken successfully")

    # First template conversion
    print("Converting image to template (slot 1)...")
    convert_result = finger.image_2_tz(1)
    if convert_result != adafruit_fingerprint.OK:
        print(f"Failed to convert image to template. Error code: {convert_result}")
        print("Possible issues:")
        print("1. Finger might be too dry or wet")
        print("2. Finger placement might be incorrect")
        print("3. Sensor might be dirty")
        print("Please try again with a clean, well-placed finger")
        return

    print("Template conversion successful")
    print("Searching for matching fingerprint...")
    
    # Search for the fingerprint
    search_result = finger.finger_search()
    if search_result != adafruit_fingerprint.OK:
        print(f"Fingerprint not found in database. Error code: {search_result}")
        print("Turning on NOT_AUTHORIZED LED...")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
        print("LED turned off")
        return

    fingerprint_id = finger.finger_id
    confidence = finger.confidence
    print(f"Fingerprint ID {fingerprint_id} recognized successfully!")
    print(f"Match confidence: {confidence}")

    data = {"fingerprint_id": str(fingerprint_id)}
    try:
        print(f"Sending attendance request for fingerprint ID {fingerprint_id}...")
        response = MANAGER.handle_attendance(fingerprint_id)
        
        if response["status"]:
            print("Access Granted - Attendance logged successfully!")
            print("Turning on ACCESS_GRANTED LED...")
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.LOW)
            print("LED turned off")
        else:
            print(f"Access Denied: {response.get('message', 'Unknown error')}")
            print("Turning on NOT_AUTHORIZED LED...")
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
            print("LED turned off")
    except requests.RequestException as e:
        print(f"Error logging attendance: {e}")
        print("Turning on NOT_AUTHORIZED LED due to error...")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
        print("LED turned off")
    print("=== Fingerprint processing complete ===\n")

def monitor_fingerprint():
    try:
        initialize_manager()
        while True:
            process_fingerprint()
            time.sleep(2)
    except KeyboardInterrupt:
        print("Exiting program. Cleaning up GPIO...")
        GPIO.cleanup()

if __name__ == "__main__":
    print("System ready. Monitoring fingerprint sensor...")
    monitor_fingerprint()
