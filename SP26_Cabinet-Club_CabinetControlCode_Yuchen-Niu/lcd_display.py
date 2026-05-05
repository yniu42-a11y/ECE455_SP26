#!/usr/bin/env python3

import time


class LCDDisplay:
    """Small wrapper around a 16x2 I2C LCD.

    The class degrades gracefully when the LCD library/hardware is unavailable,
    so the rest of the application can keep running during development.
    """

    def __init__(self, i2c_address=0x27):
        self.enabled = False
        self.lcd = None

        try:
            from RPLCD.i2c import CharLCD

            self.lcd = CharLCD(
                i2c_expander="PCF8574",
                address=i2c_address,
                port=1,
                cols=16,
                rows=2,
                dotsize=8,
                charmap="A00",
                auto_linebreaks=False,
            )
            self.enabled = True
            self.show("LCD Ready", f"Addr: {hex(i2c_address)}")
            time.sleep(1)
        except Exception as error:
            # Keep app functional even if LCD init fails (dev/testing mode).
            print(f"LCD disabled ({error})")

    @staticmethod
    def _fit_16(text):
        """Trim/pad text to exactly one 16-character LCD row."""
        return (text or "")[:16].ljust(16)

    def show(self, line1="", line2=""):
        """Display two lines on the LCD immediately."""
        if not self.enabled:
            return
        self.lcd.clear()
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(self._fit_16(line1))
        self.lcd.cursor_pos = (1, 0)
        self.lcd.write_string(self._fit_16(line2))

    def show_temp(self, line1="", line2="", delay_s=1.2):
        """Show a short-lived message, then return after delay."""
        self.show(line1, line2)
        time.sleep(delay_s)

    def close(self):
        """Clear LCD before shutdown when hardware is active."""
        if self.enabled:
            self.lcd.clear()
