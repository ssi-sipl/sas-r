import time
import serial
import adafruit_fingerprint
import requests
import RPi.GPIO as GPIO
import hashlib
import uuid


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


#def hash_fingerprint_template(template, unique_id):
#    if not template or not unique_id:
#        raise ValueError("Template and unique ID cannot be empty or None.")
#    template_bytes = bytes(template)
#    sha256_hash = hashlib.sha256(template_bytes + unique_id.encode()).hexdigest()
#    return sha256_hash


def hash_fingerprint_template(template):
    if not template:
        raise ValueError("Template cannot be empty or None.")
    template_bytes = bytes(template)
    sha256_hash = hashlib.sha256(template_bytes).hexdigest()
    return sha256_hash  # Return only the hash

def clear_fingerprint_buffer():
    """
    Clears the fingerprint sensor buffer slots.
    """
    if finger.empty_library() == adafruit_fingerprint.OK:
        print("Fingerprint buffer cleared successfully.")
    else:
        print("Failed to clear fingerprint buffer.")



def send_post_request(endpoint, data):
    """Send a POST request to the backend."""
    try:
        response = requests.post(endpoint, json=data)
        if response.status_code == 200:
            print(f"POST request successful: {response.json()}")
            return True
        else:
            print(
                f"POST request failed: {response.status_code} - {response.json()}")
            return False
    except Exception as e:
        print(f"Error sending POST request: {e}")
        return False


def process_fingerprint():
    
    print("Clearing fingerprint buffer...")
    clear_fingerprint_buffer()  # Clear buffer before starting a new search

    
    """Capture fingerprint, retrieve template, and send to backend."""
    print("Waiting for fingerprint...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass

    # Process the captured fingerprint image
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Failed to process fingerprint.")
        return

    # Retrieve the fingerprint template from buffer 1
    template = finger.get_fpdata("char", 1)  # fingerprint template

    if template is None:
        print("Failed to retrieve fingerprint template.")
        return

    try:
        hashed_template = hash_fingerprint_template(template)
    except ValueError as e:
        print(e)
        return

    print("Fingerprint scanned successfully. Sending to server...")

    data = {"fingerprint_id": hashed_template}

    # Send POST request to backend
    success = send_post_request(ATTENDANCE_ENDPOINT, data)

    # Indicate success or failure using LEDs
    if success:
        GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.LOW)
    else:
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)


def monitor_fingerprint():
    """Continuously monitor the fingerprint sensor."""
    try:
        while True:
            process_fingerprint()
            time.sleep(2)  # Optional delay between scans
    except KeyboardInterrupt:
        print("Exiting program. Cleaning up GPIO...")
        GPIO.cleanup()


if __name__ == "__main__":
    print("System ready. Monitoring fingerprint sensor...")
    monitor_fingerprint()

