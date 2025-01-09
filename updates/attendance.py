import time
import serial
import adafruit_fingerprint
import requests
import RPi.GPIO as GPIO

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
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def process_fingerprint():
    print("Waiting for fingerprint...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Failed to convert image to template.")
        return

    if finger.finger_search() != adafruit_fingerprint.OK:
        print("Fingerprint not found.")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
        return

    fingerprint_id = finger.finger_id
    print(f"Fingerprint ID {fingerprint_id} recognized.")

    data = {"fingerprint_id": str(fingerprint_id)}
    try:
        response = requests.post(ATTENDANCE_ENDPOINT, json=data)
        if response.status_code == 200:
            print("Access Granted.")
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.LOW)
        else:
            print("Access Denied.")
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
    except requests.RequestException as e:
        print(f"Error logging attendance: {e}")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)

def monitor_fingerprint():
    try:
        while True:
            process_fingerprint()
            time.sleep(2)
    except KeyboardInterrupt:
        print("Exiting program. Cleaning up GPIO...")
        GPIO.cleanup()

if __name__ == "__main__":
    print("System ready. Monitoring fingerprint sensor...")
    monitor_fingerprint()
