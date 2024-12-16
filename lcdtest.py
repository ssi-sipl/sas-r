from RPLCD.i2c import CharLCD

lcd = CharLCD(i2c_expander='PCF8574', address=0x2D, port=1, cols=16, rows=2, dotsize=8)
lcd.clear()

lcd.write_string('Hello, World!')
