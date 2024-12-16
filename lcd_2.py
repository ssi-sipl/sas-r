from RPLCD.i2c import CharLCD

# Replace 0x27 with your I2C address
I2C_ADDRESS = 0x27
lcd = CharLCD('PCF8574', I2C_ADDRESS)

def main():
    # Display message
    lcd.write_string("Hello, World!")
    
    # Wait and then clear
    import time
    time.sleep(5)
    lcd.clear()

if __name__ == "__main__":
    main()
