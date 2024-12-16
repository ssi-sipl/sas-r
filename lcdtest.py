import time
import board
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)

# LCD 1602 setup with address 0x2D (adjust the address if necessary)
lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2, address=0x2D)  # 16x2 LCD with address 0x2D

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
