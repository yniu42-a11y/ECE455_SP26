#!/usr/bin/env python3

"""Application entrypoint: initialize hardware adapters and run VendingApp."""

import argparse

from config_vm import (
    DB_FILE,
    INVENTORY_FILE,
    HISTORY_FILE,
    LCD_I2C_ADDRESS,
    LOCKBOX_CONFIG,
    LOCKBOX_UNLOCK_PULSE_S,
    LOCKBOX_WAIT_TIMEOUT_S,
    MOTOR_IN1_PIN,
    MOTOR_IN2_PIN,
    MOTOR_ENA_PIN,
    MOTOR_PWM_FREQ,
)
from lcd_display import LCDDisplay
from lockbox_controller import LockboxController
from matrix_keypad import MatrixKeypad, ROW_PINS, COL_PINS, KEY_MAP
from motor_controller import MotorController
from password_store import ensure_db_file
from inventory_store import ensure_inventory_file
from history_store import ensure_history_file
from vending_app import VendingApp, MockKeypad


def main():
    """Parse CLI options, prepare dependencies, and start the main loop."""
    parser = argparse.ArgumentParser(description="Vending machine app")
    parser.add_argument(
        "--mock-keypad",
        action="store_true",
        help="Use terminal input to simulate keypad keys",
    )
    args = parser.parse_args()

    ensure_db_file(DB_FILE)
    ensure_inventory_file(INVENTORY_FILE)
    ensure_history_file(HISTORY_FILE)

    lcd = LCDDisplay(LCD_I2C_ADDRESS)
    motor = MotorController(MOTOR_IN1_PIN, MOTOR_IN2_PIN, MOTOR_ENA_PIN, MOTOR_PWM_FREQ)
    lockbox = LockboxController(
        LOCKBOX_CONFIG,
        unlock_pulse_s=LOCKBOX_UNLOCK_PULSE_S,
        wait_timeout_s=LOCKBOX_WAIT_TIMEOUT_S,
    )

    if args.mock_keypad:
        keypad = MockKeypad()
        print("Running in MOCK keypad mode")
        print("Use terminal input to simulate keys: 0-9, *, #")
    else:
        keypad = MatrixKeypad(
            row_pins=ROW_PINS,
            col_pins=COL_PINS,
            key_map=KEY_MAP,
            debounce_ms=50,
            scan_interval=0.01,
        )

    app = VendingApp(keypad, lcd, motor, lockbox, DB_FILE, INVENTORY_FILE, HISTORY_FILE)
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExit program")
    finally:
        motor.close()
        keypad.cleanup()
        lcd.close()


if __name__ == "__main__":
    main()
