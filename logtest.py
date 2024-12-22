import time
import serial
import adafruit_fingerprint
import requests
import RPi.GPIO as GPIO

# GPIO Pin Setup (Physical Board Pins)
ACCESS_GRANTED_LED_PIN = 15  # Physical pin 15 (GPIO22)
NOT_AUTHORISED_LED_PIN = 16  # Physical pin 16 (GPIO23)

# Backend API Configuration
BACKEND_BASE_URL = "https://attendance-system-backend-ptbf.onrender.com/api"  # Replace with your backend base URL
ENTRY_ENDPOINT = f"{https://attendance-system-backend-ptbf.onrender.com/api}/entry"
EXIT_ENDPOINT = f"{https://attendance-system-backend-ptbf.onrender.com/api}/exit"

# Setup GPIO mode and pin configuration
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ACCESS_GRANTED_LED_PIN, GPIO.OUT)
GPIO.setup(NOT_AUTHORISED_LED_PIN, GPIO.OUT)

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)  # Replace /dev/ttyS0 if necessary
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

def send_post_request(endpoint, data):
    """Send a POST request to the backend."""
    try:
        response = requests.post(endpoint, json=data, headers=HEADERS)
        if response.status_code == 200:
            print(f"POST request to {endpoint} successful: {response.json()}")
        else:
            print(f"POST request to {endpoint} failed with status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending POST request to {endpoint}: {e}")

def process_fingerprint(action):
    """Process the fingerprint and send POST request for entry or exit."""
    print(f"Waiting for {action} fingerprint...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Failed to process fingerprint.")
        return
    if finger.finger_search() == adafruit_fingerprint.OK:
        fingerprint_id = finger.finger_id
        print(f"Fingerprint ID {fingerprint_id} matched. Sending {action} request.")
        GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.LOW)

        # Send POST request
        data = {"fingerprint_id": fingerprint_id}
        if action == "entry":
            send_post_request(ENTRY_ENDPOINT, data)
        elif action == "exit":
            send_post_request(EXIT_ENDPOINT, data)
    else:
        print("Fingerprint not found.")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)

def monitor_fingerprint():
    """Continuously monitor the fingerprint sensor for entry and exit."""
    try:
        while True:
            # Process entry
            print("Processing Entry...")
            process_fingerprint("entry")
            time.sleep(2)  # Delay to simulate separate actions

            # Process exit
            print("Processing Exit...")
            process_fingerprint("exit")
            time.sleep(2)  # Delay to simulate separate actions
    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    print("System ready. Monitoring fingerprint sensor...")
    monitor_fingerprint()
