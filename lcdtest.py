import time
import board
import digitalio
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import busio

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)

# LCD 1602 setup (adjust the address if necessary)
lcd = CharLCD(i2c_expander='PCF8574', address=0x2d, port=1, cols=16, rows=2, dotsize=8)
lcd.clear()


# Clear the LCD screen
lcd.clear()

# Set the LCD display to "Hello, World!"
lcd.message = "Hello, World!"

# Wait 5 seconds before clearing the screen
time.sleep(5)

# Clear the display after some time
lcd.clear()

# Display another message
lcd.message = "Raspberry Pi I2C"

# Keep the message on for 10 seconds
time.sleep(10)

# Final clear
lcd.clear()
