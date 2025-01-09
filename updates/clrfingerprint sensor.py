import serial
import adafruit_fingerprint

def clear_fingerprint_library(sensor):
    """
    Clears the entire fingerprint library from the sensor's internal memory.
    """
    print("Attempting to clear all fingerprints from the sensor...")
    if sensor.empty_library() == adafruit_fingerprint.OK:
        print("All fingerprints have been successfully deleted from the sensor.")
    else:
        print("Failed to delete fingerprints. Please check the connection or try again.")

def main():
    # Set up the serial connection to the fingerprint sensor
    try:
        # Replace '/dev/ttyUSB0' with the correct port (e.g., '/dev/serial0' for Raspberry Pi GPIO UART)
        uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=1)
        sensor = adafruit_fingerprint.Adafruit_Fingerprint(uart)
    except Exception as e:
        print(f"Error initializing sensor: {e}")
        return

    # Clear all fingerprints using the function
    clear_fingerprint_library(sensor)

if __name__ == "__main__":
    main()
