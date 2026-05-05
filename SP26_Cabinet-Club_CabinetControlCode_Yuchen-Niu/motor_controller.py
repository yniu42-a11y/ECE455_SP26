#!/usr/bin/env python3

"""L298N motor control wrapper with PWM speed and direction helpers."""

import time
import RPi.GPIO as GPIO


class MotorController:
    """Safe motor driver facade that no-ops when GPIO is unavailable."""

    def __init__(self, in1_pin, in2_pin, ena_pin, pwm_freq):
        self.enabled = False
        self.pwm = None
        self.running = False
        self.direction = None
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.ena_pin = ena_pin

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.in1_pin, GPIO.OUT)
            GPIO.setup(self.in2_pin, GPIO.OUT)
            GPIO.setup(self.ena_pin, GPIO.OUT)

            self.pwm = GPIO.PWM(self.ena_pin, pwm_freq)
            self.pwm.start(0)

            GPIO.output(self.in1_pin, GPIO.LOW)
            GPIO.output(self.in2_pin, GPIO.LOW)
            self.enabled = True
        except Exception as error:
            print(f"Motor controller disabled ({error})")

    def start_forward(self, duty):
        """Start motor in forward direction using the given PWM duty cycle."""
        if not self.enabled:
            return
        GPIO.output(self.in1_pin, GPIO.HIGH)
        GPIO.output(self.in2_pin, GPIO.LOW)
        self.pwm.ChangeDutyCycle(duty)
        self.running = True
        self.direction = "forward"

    def start_backward(self, duty):
        """Start motor in backward direction using the given PWM duty cycle."""
        if not self.enabled:
            return
        GPIO.output(self.in1_pin, GPIO.LOW)
        GPIO.output(self.in2_pin, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(duty)
        self.running = True
        self.direction = "backward"

    def stop(self):
        """Stop motor drive and set PWM duty to zero."""
        if not self.enabled:
            return
        GPIO.output(self.in1_pin, GPIO.LOW)
        GPIO.output(self.in2_pin, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)
        self.running = False
        self.direction = None

    def close(self):
        """Stop motor and release PWM resource before process exit."""
        if not self.enabled:
            return
        self.stop()
        self.pwm.stop()

    def dispense_for(self, seconds, duty):
        """Run motor forward for a fixed duration; returns success state."""
        if not self.enabled:
            return False

        self.start_forward(duty)
        time.sleep(max(0.1, seconds))
        self.stop()
        return True
