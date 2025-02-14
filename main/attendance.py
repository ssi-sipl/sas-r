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

def get_image_with_retry(max_retries=3):
    print("Waiting for finger placement...")
    
    # Try to get the image
    consecutive_detections = 0  # Counter for consistent finger detections
    
    while True:
        get_image_result = finger.get_image()
        
        if get_image_result == adafruit_fingerprint.NOFINGER:
            consecutive_detections = 0  # Reset counter when no finger detected
            time.sleep(0.1)
            continue
            
        elif get_image_result == adafruit_fingerprint.OK:
            consecutive_detections += 1
            if consecutive_detections >= 3:  # Require 3 consecutive successful readings
                print("Finger detected! Processing...")
                return True
            time.sleep(0.1)  # Small delay between readings
            continue
            
        elif get_image_result == 2:  # PACKETRECIEVEERR
            print(f"Communication error")
            time.sleep(0.5)  # Wait before retry
            consecutive_detections = 0
            
        else:
            print(f"Failed to get image. Error code: {get_image_result}")
            return False
            
        # Check if we've exceeded max retries for errors
        if consecutive_detections == 0:  # Only count failed attempts when no finger detected
            max_retries -= 1
            if max_retries <= 0:
                print("Max retries exceeded. Please try again.")
                return False
    
    return False

def process_fingerprint():
    print("\n=== Starting fingerprint processing ===")
    print("Please place your finger on the sensor...")
    
    # Try to get the image with retries
    if not get_image_with_retry():
        return
    
    # Add a small delay after successful detection
    time.sleep(0.2)
    
    # print("Image taken successfully")
    
    # First template conversion
    # print("Converting image to template (slot 1)...")
    convert_result = finger.image_2_tz(1)
    if convert_result != adafruit_fingerprint.OK:
        print(f"Failed to convert image to template. Error code: {convert_result}")
        # print("Possible issues:")
        # print("1. Finger might be too dry or wet")
        # print("2. Finger placement might be incorrect")
        # print("3. Sensor might be dirty")
        # print("Please try again with a clean, well-placed finger")
        return

    # print("Template conversion successful")
    # print("Searching for matching fingerprint...")
    
    # Search for the fingerprint
    search_result = finger.finger_search()
    if search_result != adafruit_fingerprint.OK:
        print(f"Fingerprint not found in database. Error code: {search_result}")
        # print("Turning on NOT_AUTHORIZED LED...")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
        # print("LED turned off")
        return

    fingerprint_id = finger.finger_id
    confidence = finger.confidence
    print(f"Fingerprint ID {fingerprint_id} recognized successfully!")
    # print(f"Match confidence: {confidence}")

    data = {"fingerprint_id": str(fingerprint_id)}
    try:
        # print(f"Sending attendance request for fingerprint ID {fingerprint_id}...")
        response = MANAGER.handle_attendance(fingerprint_id)
        
        if response["status"]:
            # print("Access Granted - Attendance logged successfully!")
            print(response.get('message', 'Unknown error'))
            # print("Turning on ACCESS_GRANTED LED...")
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.LOW)
            # print("LED turned off")
        else:
            print(response.get('message', 'Unknown error'))
            # print("Turning on NOT_AUTHORIZED LED...")
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
            # print("LED turned off")
    except requests.RequestException as e:
        print(f"Error logging attendance: {e}")
        # print("Turning on NOT_AUTHORIZED LED due to error...")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
        # print("LED turned off")
    print("=== Fingerprint processing complete ===\n")

def monitor_fingerprint():
    try:
        initialize_manager()
        print("System initialized successfully")
        print("Place finger on sensor to scan...")
        
        while True:
            process_fingerprint()
            print("\nNext scan in 2 seconds...")
            time.sleep(2)  # Longer delay between scans
            
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected")
        print("Exiting program. Cleaning up GPIO...")
        GPIO.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    print("System ready. Monitoring fingerprint sensor...")
    monitor_fingerprint()
