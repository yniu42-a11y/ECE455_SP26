#!/usr/bin/env python3
"""
3x4 Matrix Keypad for Raspberry Pi 4B

Wiring used (BCM mode):
Keypad pin1=C2 -> GPIO20 (physical pin 38)
Keypad pin2=R1 -> GPIO26 (physical pin 37)
Keypad pin3=C1 -> GPIO27 (physical pin 13)
Keypad pin4=R4 -> GPIO6  (physical pin 31)
Keypad pin5=C3 -> GPIO22 (physical pin 15)
Keypad pin6=R3 -> GPIO13 (physical pin 33)
Keypad pin7=R2 -> GPIO19 (physical pin 35)
"""

import time
import argparse
import RPi.GPIO as GPIO


# Row order: R1, R2, R3, R4
ROW_PINS = [26, 19, 13, 6]

# Column order: C1, C2, C3
COL_PINS = [27, 20, 22]

# Standard 3x4 keypad map
KEY_MAP = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["*", "0", "#"],
]


class MatrixKeypad:
    """Scanner for 3x4 matrix keypad using row-drive and column-read."""

    def __init__(self, row_pins, col_pins, key_map, debounce_ms=50, scan_interval=0.01):
        self.row_pins = row_pins
        self.col_pins = col_pins
        self.key_map = key_map
        self.debounce_s = debounce_ms / 1000.0
        self.scan_interval = scan_interval

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        for row_pin in self.row_pins:
            GPIO.setup(row_pin, GPIO.OUT)
            GPIO.output(row_pin, GPIO.HIGH)

        for col_pin in self.col_pins:
            GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def _scan_once(self):
        """Perform one matrix scan and return the detected key or None."""
        for row_idx, row_pin in enumerate(self.row_pins):
            GPIO.output(row_pin, GPIO.LOW)
            time.sleep(0.001)

            for col_idx, col_pin in enumerate(self.col_pins):
                if GPIO.input(col_pin) == GPIO.LOW:
                    GPIO.output(row_pin, GPIO.HIGH)
                    return self.key_map[row_idx][col_idx]

            GPIO.output(row_pin, GPIO.HIGH)

        return None

    def _scan_once_with_position(self):
        """Perform one scan and return key with its row/column indices."""
        for row_idx, row_pin in enumerate(self.row_pins):
            GPIO.output(row_pin, GPIO.LOW)
            time.sleep(0.001)

            for col_idx, col_pin in enumerate(self.col_pins):
                if GPIO.input(col_pin) == GPIO.LOW:
                    GPIO.output(row_pin, GPIO.HIGH)
                    return self.key_map[row_idx][col_idx], row_idx, col_idx

            GPIO.output(row_pin, GPIO.HIGH)

        return None, None, None

    def _any_pressed(self):
        """Check whether any key is currently pressed."""
        return self._scan_once() is not None

    def get_current_key(self):
        """
        Return the key that is currently being held down, or None.
        This method does not debounce and does not wait for key release.
        Useful for hold-to-run controls.
        """
        return self._scan_once()

    def get_key(self):
        """Return one debounced key press and wait for release."""
        first_key = self._scan_once()
        if first_key is None:
            return None

        time.sleep(self.debounce_s)
        confirm_key = self._scan_once()
        if confirm_key != first_key:
            return None

        while self._any_pressed():
            time.sleep(self.scan_interval)

        return first_key

    def get_key_with_position(self):
        """Return one debounced key press with matrix position."""
        first_key, first_row, first_col = self._scan_once_with_position()
        if first_key is None:
            return None, None, None

        time.sleep(self.debounce_s)
        confirm_key, confirm_row, confirm_col = self._scan_once_with_position()
        if confirm_key != first_key or confirm_row != first_row or confirm_col != first_col:
            return None, None, None

        while self._any_pressed():
            time.sleep(self.scan_interval)

        return first_key, first_row, first_col

    def cleanup(self):
        """Release GPIO resources used by the keypad scanner."""
        GPIO.cleanup()


def run_normal_mode(keypad):
    """CLI helper: print each detected key in normal scan mode."""
    print("3x4 Matrix Keypad ready")
    print("Press keys (1-9, *, 0, #). Press Ctrl+C to exit.")

    while True:
        key = keypad.get_key()
        if key is not None:
            print(f"Key pressed: {key}")
        time.sleep(0.005)


def run_diag_mode(keypad):
    """CLI helper: diagnostic scan that tracks row/column hit counts."""
    print("3x4 Matrix Keypad DIAGNOSTIC mode")
    print("Press all keys once (left->right, top->bottom), then Ctrl+C to see summary.")
    print("Showing detected key with row/col index (R1..R4, C1..C3).")

    key_hits = {k: 0 for row in KEY_MAP for k in row}
    row_hits = [0, 0, 0, 0]
    col_hits = [0, 0, 0]

    while True:
        key, row_idx, col_idx = keypad.get_key_with_position()
        if key is not None:
            key_hits[key] += 1
            row_hits[row_idx] += 1
            col_hits[col_idx] += 1
            print(f"Key pressed: {key}  (R{row_idx+1}, C{col_idx+1})")
        time.sleep(0.005)


def print_diag_summary():
    """Reserved for future refactor; summary is printed in main() currently."""
    pass


def main():
    """Run keypad scanner in normal mode or diagnostic mode."""
    parser = argparse.ArgumentParser(description="3x4 Matrix Keypad scanner for Raspberry Pi")
    parser.add_argument("--diag", action="store_true", help="Run diagnostic mode with row/column detection")
    args = parser.parse_args()

    keypad = MatrixKeypad(
        row_pins=ROW_PINS,
        col_pins=COL_PINS,
        key_map=KEY_MAP,
        debounce_ms=50,
        scan_interval=0.01,
    )

    key_hits = {k: 0 for row in KEY_MAP for k in row}
    row_hits = [0, 0, 0, 0]
    col_hits = [0, 0, 0]

    try:
        if args.diag:
            print("3x4 Matrix Keypad DIAGNOSTIC mode")
            print("Press all keys once (left->right, top->bottom), then Ctrl+C to see summary.")
            print("Showing detected key with row/col index (R1..R4, C1..C3).")

            while True:
                key, row_idx, col_idx = keypad.get_key_with_position()
                if key is not None:
                    key_hits[key] += 1
                    row_hits[row_idx] += 1
                    col_hits[col_idx] += 1
                    print(f"Key pressed: {key}  (R{row_idx+1}, C{col_idx+1})")
                time.sleep(0.005)
        else:
            run_normal_mode(keypad)
    except KeyboardInterrupt:
        print("\nExit keypad scanner")
        if args.diag:
            print("\n=== DIAGNOSTIC SUMMARY ===")
            print("Key hits:")
            for row in KEY_MAP:
                for key in row:
                    print(f"  {key}: {key_hits[key]}")

            print("Row hits:")
            for idx, hits in enumerate(row_hits, start=1):
                print(f"  R{idx}: {hits}")

            print("Column hits:")
            for idx, hits in enumerate(col_hits, start=1):
                print(f"  C{idx}: {hits}")

            dead_rows = [idx + 1 for idx, hits in enumerate(row_hits) if hits == 0]
            dead_cols = [idx + 1 for idx, hits in enumerate(col_hits) if hits == 0]
            if dead_rows or dead_cols:
                print("\nLikely dead lines detected:")
                if dead_rows:
                    print(f"  Dead rows: {dead_rows}")
                if dead_cols:
                    print(f"  Dead columns: {dead_cols}")
                print("Check keypad membrane, connector orientation, and those specific wires/GPIO pins.")
            else:
                print("\nNo dead row/column detected.")
    finally:
        keypad.cleanup()


if __name__ == "__main__":
    main()
