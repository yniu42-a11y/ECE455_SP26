#!/usr/bin/env python3
"""
L298N + DC Motor quick spin test for Raspberry Pi.

Default wiring (BCM):
- IN1 <- GPIO23 (pin 16)
- IN2 <- GPIO24 (pin 18)
- ENA <- GPIO18 (pin 12, PWM)
- RP GND <-> L298N GND (common ground)
"""

import time
import RPi.GPIO as GPIO

# Change these pins only if your wiring is different.
IN1_PIN = 23
IN2_PIN = 24
ENA_PIN = 18

PWM_FREQ_HZ = 1000


def motor_stop(pwm):
    """Disable both direction pins and set PWM duty to zero."""
    GPIO.output(IN1_PIN, GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.LOW)
    pwm.ChangeDutyCycle(0)


def motor_forward(pwm, duty):
    """Spin motor in forward direction at given duty cycle."""
    GPIO.output(IN1_PIN, GPIO.HIGH)
    GPIO.output(IN2_PIN, GPIO.LOW)
    pwm.ChangeDutyCycle(duty)


def motor_backward(pwm, duty):
    """Spin motor in reverse direction at given duty cycle."""
    GPIO.output(IN1_PIN, GPIO.LOW)
    GPIO.output(IN2_PIN, GPIO.HIGH)
    pwm.ChangeDutyCycle(duty)


def main():
    """Run a short forward/backward motor smoke test."""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(IN1_PIN, GPIO.OUT)
    GPIO.setup(IN2_PIN, GPIO.OUT)
    GPIO.setup(ENA_PIN, GPIO.OUT)

    pwm = GPIO.PWM(ENA_PIN, PWM_FREQ_HZ)
    pwm.start(0)

    print("Motor test starting...")
    print("Forward 2s -> Stop 1s -> Backward 2s -> Stop")

    try:
        # Start with a moderate duty cycle to reduce current spikes.
        duty_cycle = 55

        print("Forward")
        motor_forward(pwm, duty_cycle)
        time.sleep(2.0)

        print("Stop")
        motor_stop(pwm)
        time.sleep(1.0)

        print("Backward")
        motor_backward(pwm, duty_cycle)
        time.sleep(2.0)

        print("Stop")
        motor_stop(pwm)
        time.sleep(0.5)

        print("Test completed")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        motor_stop(pwm)
        pwm.stop()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
  