#!/usr/bin/env python3

"""Central configuration for GPIO mapping, timing, and runtime tuning."""

ADMIN_PASSWORD = "47694769"
DB_FILE = "/home/pi/ECE455/passwords.csv"
INVENTORY_FILE = "/home/pi/ECE455/inventory.csv"
HISTORY_FILE = "/home/pi/ECE455/history.csv"

MIN_PASSWORD_LEN = 4
MAX_PASSWORD_LEN = 16

LCD_I2C_ADDRESS = 0x27

# L298N channel A (OUT1/OUT2)
MOTOR_IN1_PIN = 23
MOTOR_IN2_PIN = 24
MOTOR_ENA_PIN = 18
MOTOR_PWM_FREQ = 1000
MOTOR_DUTY_CYCLE = 85

# Fixed motor runtime for one carousel step (maps to a fixed angle after calibration)
CAROUSEL_STEP_SECONDS = 1.2
CAROUSEL_CAPACITY = 35

# User-mode carousel indexing with one limit switch for now.
# Wiring assumption: COM->GND, NO->GPIO, input uses pull-up.
# Pressed = LOW, released = HIGH.
CAROUSEL_LIMIT_SWITCH_PINS = {
    "10": 17,
}

# Physical install status (software still keeps inventory options 1-15 visible).
# Only these IDs are actually wired and should be controlled.
ACTIVE_LOCKBOX_IDS = {"1"}
ACTIVE_CAROUSEL_IDS = {"10"}
CAROUSEL_LIMIT_WAIT_PRESS_S = 5.0
CAROUSEL_LIMIT_WAIT_RELEASE_S = 5.0
# 12V supply tuning: use much lower PWM duties to avoid multi-slot overshoot.
CAROUSEL_LIMIT_SEARCH_DUTY = 44
CAROUSEL_LIMIT_APPROACH_DUTY = 33
CAROUSEL_LIMIT_SETTLE_CHECK_S = 0.10
CAROUSEL_LIMIT_CORRECTION_DUTY = 35
CAROUSEL_LIMIT_CORRECTION_TIMEOUT_S = 0.5
CAROUSEL_LIMIT_PRESS_SETTLE_S = 0.012
CAROUSEL_LIMIT_BRAKE_DUTY = 38
CAROUSEL_LIMIT_BRAKE_PULSE_S = 0.012
CAROUSEL_LIMIT_MAX_RETRIES = 2
CAROUSEL_LIMIT_RECOVERY_DUTY = 58
CAROUSEL_LIMIT_RECOVERY_TIMEOUT_S = 1.2
CAROUSEL_LIMIT_RELEASE_NUDGE_DUTY = 20
CAROUSEL_LIMIT_RELEASE_NUDGE_TIMEOUT_S = 0.25
CAROUSEL_LIMIT_RELEASE_NUDGE_SETTLE_S = 0.06

# Admin manual carousel control (12V): tap = short jog, hold = slow continuous run.
ADMIN_CAROUSEL_START_DUTY = 65
ADMIN_CAROUSEL_START_SECONDS = 0.05
ADMIN_CAROUSEL_JOG_DUTY = 36
ADMIN_CAROUSEL_JOG_SECONDS = 0.10
ADMIN_CAROUSEL_HOLD_START_S = 0.25
ADMIN_CAROUSEL_HOLD_DUTY = 40
ADMIN_CAROUSEL_HOLD_KEY_GRACE_S = 0.08
ADMIN_CAROUSEL_HOLD_KICK_INTERVAL_S = 0.35
ADMIN_CAROUSEL_HOLD_KICK_DUTY = 68
ADMIN_CAROUSEL_HOLD_KICK_SECONDS = 0.03

# Lockbox defaults and GPIO mapping.
LOCKBOX_DEFAULT_STARTING_WEIGHT = 500.0
LOCKBOX_UNLOCK_PULSE_S = 0.3
LOCKBOX_WAIT_TIMEOUT_S = 30.0

# Switch wiring expectation:
# closed = LOW, open = HIGH (input pull-up)
LOCKBOX_CONFIG = {
    "1": {"lock_pin": 4, "detect_pin": 14, "starting_weight": 500.0},
}
