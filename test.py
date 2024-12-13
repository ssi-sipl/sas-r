import time
import serial
import adafruit_fingerprint
import pandas as pd
import hashlib
import RPi.GPIO as GPIO
from datetime import datetime

# GPIO Pin Setup (Physical Board Pins)
ENTRY_BUTTON_PIN = 11  # Physical pin 11 (GPIO17)
EXIT_BUTTON_PIN = 13   # Physical pin 13 (GPIO27)
ACCESS_GRANTED_LED_PIN = 15  # Physical pin 15 (GPIO22)
NOT_AUTHORISED_LED_PIN = 16  # Physical pin 16 (GPIO23)

# Setup GPIO mode and pin configuration
GPIO.setmode(GPIO.BOARD)
GPIO.setup(ENTRY_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(EXIT_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ACCESS_GRANTED_LED_PIN, GPIO.OUT)
GPIO.setup(NOT_AUTHORISED_LED_PIN, GPIO.OUT)

# Setup serial connection for the fingerprint sensor
uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

# Load fingerprint database from CSV or create an empty one
csv_file = 'fingerprint_data.csv'
log_file = 'access_log.csv'

try:
    df = pd.read_csv(csv_file)
except FileNotFoundError:
    df = pd.DataFrame(columns=['id', 'name', 'sha_key'])

if not pd.DataFrame(columns=['id', 'name', 'date', 'time']).empty:
    pd.DataFrame(columns=['id', 'name', 'date', 'time']).to_csv(log_file, index=False)

def generate_sha_key(data):
    """Generate a SHA-256 hash for the provided data."""
    return hashlib.sha256(data.encode()).hexdigest()

def log_access(action, finger_id, name):
    """Log access attempt with date and time."""
    current_time = datetime.now()
    new_log = pd.DataFrame({
        'action': [action],
        'id': [finger_id],
        'name': [name],
        'date': [current_time.strftime("%Y-%m-%d")],
        'time': [current_time.strftime("%H:%M:%S")]
    })
    new_log.to_csv(log_file, mode='a', header=False, index=False)

def search_and_log(action):
    """Search for a fingerprint and log the result."""
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        print("Failed to process fingerprint.")
        return
    if finger.finger_search() == adafruit_fingerprint.OK:
        finger_id = finger.finger_id
        record = df[df['id'] == finger_id]
        if not record.empty:
            name = record.iloc[0]['name']
            print(f"Access Granted for {name}.")
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(ACCESS_GRANTED_LED_PIN, GPIO.LOW)
            log_access(action, finger_id, name)
        else:
            print("Fingerprint found, but no associated name.")
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)
    else:
        print("Fingerprint not found.")
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(NOT_AUTHORISED_LED_PIN, GPIO.LOW)

def entry():
    """Handle entry button press."""
    print("Entry button pressed.")
    search_and_log("Entry")

def exit():
    """Handle exit button press."""
    print("Exit button pressed.")
    search_and_log("Exit")

def monitor_buttons():
    """Monitor buttons and call corresponding functions."""
    try:
        while True:
            if GPIO.input(ENTRY_BUTTON_PIN) == GPIO.LOW:  # Button pressed
                entry()
                time.sleep(0.5)  # Debounce
            if GPIO.input(EXIT_BUTTON_PIN) == GPIO.LOW:  # Button pressed
                exit()
                time.sleep(0.5)  # Debounce
    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    print("System ready. Waiting for button presses...")
    monitor_buttons()
