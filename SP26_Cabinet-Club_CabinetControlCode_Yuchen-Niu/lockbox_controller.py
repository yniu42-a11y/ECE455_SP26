#!/usr/bin/env python3

import time


class LockboxController:
    """GPIO controller for lockbox unlock pulse and open/close detection."""

    def __init__(self, lockbox_config, unlock_pulse_s=0.3, wait_timeout_s=30.0):
        self.enabled = False
        self.gpio = None
        self.lockbox_config = lockbox_config or {}
        self.unlock_pulse_s = unlock_pulse_s
        self.wait_timeout_s = wait_timeout_s

        try:
            import RPi.GPIO as GPIO

            self.gpio = GPIO
            self.gpio.setwarnings(False)
            self.gpio.setmode(self.gpio.BCM)
            self.enabled = True
        except Exception as error:
            print(f"Lockbox controller disabled ({error})")

    def _setup_lockbox_pins(self, lock_pin, detect_pin):
        """Initialize lock output pin and detect input pin for one lockbox."""
        self.gpio.setup(lock_pin, self.gpio.OUT)
        self.gpio.output(lock_pin, self.gpio.LOW)
        self.gpio.setup(detect_pin, self.gpio.IN, pull_up_down=self.gpio.PUD_UP)

    def _pulse_unlock(self, lock_pin):
        """Drive the lock line high for a short unlock pulse."""
        self.gpio.output(lock_pin, self.gpio.HIGH)
        time.sleep(self.unlock_pulse_s)
        self.gpio.output(lock_pin, self.gpio.LOW)

    def _wait_for_state(self, detect_pin, target_state, timeout_s):
        """Wait until detect pin reaches the target state or timeout occurs."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.gpio.input(detect_pin) == target_state:
                return True
            time.sleep(0.05)
        return False

    def read_weight(self, lockbox_id, fallback_weight):
        # Placeholder for HX711 integration. Keep current value until load-cell code is added.
        return fallback_weight

    def access_box(self, lockbox_id, fallback_weight=None):
        """Unlock, wait for open and close events, then return measured/fallback weight."""
        if not self.enabled:
            # Allow application flow in development mode without lockbox hardware.
            return True, fallback_weight

        config = self.lockbox_config.get(lockbox_id)
        if not config:
            print(f"No lockbox GPIO config for ID {lockbox_id}")
            return False, fallback_weight

        lock_pin = config["lock_pin"]
        detect_pin = config["detect_pin"]

        try:
            self._setup_lockbox_pins(lock_pin, detect_pin)
            self._pulse_unlock(lock_pin)

            # Door open event: switch transitions to HIGH.
            opened = self._wait_for_state(detect_pin, self.gpio.HIGH, self.wait_timeout_s)
            if not opened:
                print(f"Lockbox {lockbox_id} open timeout")
                return False, fallback_weight

            # Door close event: switch returns to LOW.
            closed = self._wait_for_state(detect_pin, self.gpio.LOW, self.wait_timeout_s)
            if not closed:
                print(f"Lockbox {lockbox_id} close timeout")
                return False, fallback_weight

            measured_weight = self.read_weight(lockbox_id, fallback_weight)
            return True, measured_weight
        except Exception as error:
            print(f"Lockbox access failed ({error})")
            return False, fallback_weight
