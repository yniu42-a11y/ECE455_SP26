#!/usr/bin/env python3

"""Main vending workflow: auth, admin tools, lockbox access, and carousel dispense."""

import csv
import importlib.util
import os
import time

from config_vm import (
    ADMIN_PASSWORD,
    ADMIN_CAROUSEL_HOLD_DUTY,
    ADMIN_CAROUSEL_HOLD_KICK_DUTY,
    ADMIN_CAROUSEL_HOLD_KICK_INTERVAL_S,
    ADMIN_CAROUSEL_HOLD_KICK_SECONDS,
    ADMIN_CAROUSEL_HOLD_KEY_GRACE_S,
    ADMIN_CAROUSEL_HOLD_START_S,
    ADMIN_CAROUSEL_JOG_DUTY,
    ADMIN_CAROUSEL_JOG_SECONDS,
    ADMIN_CAROUSEL_START_DUTY,
    ADMIN_CAROUSEL_START_SECONDS,
    ACTIVE_CAROUSEL_IDS,
    ACTIVE_LOCKBOX_IDS,
    CAROUSEL_CAPACITY,
    CAROUSEL_LIMIT_APPROACH_DUTY,
    CAROUSEL_LIMIT_BRAKE_DUTY,
    CAROUSEL_LIMIT_BRAKE_PULSE_S,
    CAROUSEL_LIMIT_CORRECTION_DUTY,
    CAROUSEL_LIMIT_CORRECTION_TIMEOUT_S,
    CAROUSEL_LIMIT_MAX_RETRIES,
    CAROUSEL_LIMIT_PRESS_SETTLE_S,
    CAROUSEL_LIMIT_RECOVERY_DUTY,
    CAROUSEL_LIMIT_RECOVERY_TIMEOUT_S,
    CAROUSEL_LIMIT_SEARCH_DUTY,
    CAROUSEL_LIMIT_RELEASE_NUDGE_DUTY,
    CAROUSEL_LIMIT_RELEASE_NUDGE_TIMEOUT_S,
    CAROUSEL_LIMIT_RELEASE_NUDGE_SETTLE_S,
    CAROUSEL_LIMIT_SETTLE_CHECK_S,
    CAROUSEL_LIMIT_SWITCH_PINS,
    CAROUSEL_LIMIT_WAIT_PRESS_S,
    CAROUSEL_LIMIT_WAIT_RELEASE_S,
    LOCKBOX_DEFAULT_STARTING_WEIGHT,
    MIN_PASSWORD_LEN,
    MAX_PASSWORD_LEN,
    MOTOR_DUTY_CYCLE,
    CAROUSEL_STEP_SECONDS,
)
from password_store import (
    load_passwords,
    save_passwords,
    masked,
    validate_password_format,
)
from inventory_store import load_inventory, save_inventory
from history_store import append_history_entry


class MockKeypad:
    """Mock keypad for testing when physical keypad is unavailable."""

    def get_key(self):
        while True:
            key = input("Mock key (0-9,*,#): ").strip()
            if key in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "#"}:
                return key
            print("Invalid mock key")

    def get_current_key(self):
        # In mock mode, no hold behavior is available.
        return None

    def cleanup(self):
        return


class VendingApp:
    """Application state machine coordinating keypad, LCD, motor, and storage."""

    def __init__(self, keypad, lcd, motor, lockbox, db_file, inventory_file, history_file):
        self.keypad = keypad
        self.lcd = lcd
        self.motor = motor
        self.lockbox = lockbox
        self.db_file = db_file
        self.inventory_file = inventory_file
        self.history_file = history_file
        self._email_sender = None
        self._email_load_error = None
        self._limit_gpio = None

        # Limit switch input setup is optional so the app still runs without hardware.
        try:
            import RPi.GPIO as GPIO

            self._limit_gpio = GPIO
            for pin in CAROUSEL_LIMIT_SWITCH_PINS.values():
                self._limit_gpio.setup(pin, self._limit_gpio.IN, pull_up_down=self._limit_gpio.PUD_UP)
        except Exception as error:
            print(f"Carousel limit switches disabled ({error})")

    @staticmethod
    def _is_lockbox(item):
        return item.get("container_type") == "lockbox"

    @staticmethod
    def _is_carousel(item):
        return item.get("container_type") == "carousel"

    @staticmethod
    def _is_active_container(container_id, item):
        if item.get("container_type") == "lockbox":
            return container_id in ACTIVE_LOCKBOX_IDS
        if item.get("container_type") == "carousel":
            return container_id in ACTIVE_CAROUSEL_IDS
        return False

    def _load_email_sender(self):
        """Load send_email function with import fallback for local script execution."""
        if self._email_sender is not None:
            return self._email_sender

        if self._email_load_error is not None:
            return None

        # Try normal import first.
        try:
            from test_email import send_email as imported_send_email

            self._email_sender = imported_send_email
            return self._email_sender
        except Exception as error:
            first_error = error

        # Fallback: load test_email.py by absolute file path.
        module_path = os.path.join(os.path.dirname(__file__), "test_email.py")
        try:
            spec = importlib.util.spec_from_file_location("test_email_local", module_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._email_sender = getattr(module, "send_email", None)
                if self._email_sender is not None:
                    return self._email_sender
                self._email_load_error = "send_email not found in test_email.py"
                return None
            self._email_load_error = f"Unable to build import spec for {module_path}"
            return None
        except Exception as error:
            self._email_load_error = (
                f"normal import failed: {first_error}; file import failed: {error}"
            )
            return None

    def write_history(self, user_pin, container_type, container_id):
        """Append a successful access event to history storage."""
        append_history_entry(self.history_file, user_pin, container_type, container_id)
        print(f"History saved: user {user_pin} -> {container_type} {container_id}")

    def build_inventory_report(self):
        """Generate plain-text inventory summary for email delivery."""
        inventory = load_inventory(self.inventory_file)
        lines = ["Vending inventory report", ""]
        for item_id in sorted(inventory.keys(), key=lambda value: int(value)):
            item = inventory[item_id]
            if self._is_lockbox(item):
                lines.append(
                    f"Lockbox {item_id}: stock={item['stock']}, times_opened={item['times_opened']}, "
                    f"starting_weight={item['starting_weight']}, current_weight={item['current_weight']}, "
                    f"fullness={item['fullness']}"
                )
            else:
                lines.append(f"Carousel {item_id}: stock={item['stock']}")
        return "\n".join(lines)

    def build_history_report(self, max_rows=100):
        """Generate plain-text history summary for email delivery."""
        rows = []
        try:
            with open(self.history_file, "r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    rows.append(row)
        except Exception as error:
            return f"Failed to read history file: {error}"

        if not rows:
            return "Usage history report\n\nNo history records found."

        lines = ["Usage history report", ""]
        for row in rows[-max_rows:]:
            lines.append(
                f"{row.get('timestamp', '')} | user={row.get('user_pin', '')} | "
                f"type={row.get('container_type', '')} | id={row.get('container_id', '')}"
            )
        return "\n".join(lines)

    def select_container(self, prompt="Select container number"):
        """Read container ID from keypad and validate against inventory list."""
        inventory = load_inventory(self.inventory_file)
        container_ids = sorted(inventory.keys(), key=lambda value: int(value))
        if not container_ids:
            print("No container configured in inventory")
            if self.lcd:
                self.lcd.show_temp("NO CONTAINER", "Config required")
            return None, inventory

        if self.lcd:
            self.lcd.show("SELECT CONTAINER", "1-15 + #")

        print("Available container IDs:", ", ".join(container_ids))
        container_id = self.read_password_from_keypad(prompt, input_line1="Input box number")
        if not container_id or container_id not in inventory:
            print("Invalid container selection")
            if self.lcd:
                self.lcd.show_temp("INVALID CONTAINER", container_id[:16] if container_id else "Empty ID")
            return None, inventory
        return container_id, inventory

    def admin_send_inventory_email(self):
        """Send inventory report email and mirror status on LCD."""
        email_sender = self._load_email_sender()
        if email_sender is None:
            print("Email module unavailable")
            if self._email_load_error:
                print(f"Email load error: {self._email_load_error}")
            if self.lcd:
                self.lcd.show_temp("EMAIL FAILED", "Module missing")
            return

        message = self.build_inventory_report()
        print("Sending inventory report email...")
        ok = email_sender(message)
        if ok:
            print("Inventory report email sent")
            if self.lcd:
                self.lcd.show_temp("EMAIL SENT", "Inventory")
        else:
            print("Inventory report email failed")
            if self.lcd:
                self.lcd.show_temp("EMAIL FAILED", "Inventory")

    def admin_send_history_email(self):
        """Send history report email and mirror status on LCD."""
        email_sender = self._load_email_sender()
        if email_sender is None:
            print("Email module unavailable")
            if self._email_load_error:
                print(f"Email load error: {self._email_load_error}")
            if self.lcd:
                self.lcd.show_temp("EMAIL FAILED", "Module missing")
            return

        message = self.build_history_report()
        print("Sending history report email...")
        ok = email_sender(message)
        if ok:
            print("History report email sent")
            if self.lcd:
                self.lcd.show_temp("EMAIL SENT", "History")
        else:
            print("History report email failed")
            if self.lcd:
                self.lcd.show_temp("EMAIL FAILED", "History")

    def read_password_from_keypad(self, prompt, input_line1="Input password"):
        """Collect numeric input from keypad with backspace and submit keys."""
        print("\n" + prompt)
        print("Type digits, '*' = backspace, '#' = submit")

        if self.lcd:
            self.lcd.show(prompt[:16], "*=del #=ok")

        buffer = ""

        while True:
            key = self.keypad.get_key()
            if key is None:
                time.sleep(0.005)
                continue

            if key.isdigit():
                if len(buffer) < MAX_PASSWORD_LEN:
                    buffer += key
                    print(f"Input: {masked(buffer)}")
                    if self.lcd:
                        self.lcd.show(input_line1[:16], masked(buffer))
                else:
                    print(f"Input max length reached ({MAX_PASSWORD_LEN})")
                    if self.lcd:
                        self.lcd.show_temp("Input too long", f"Max {MAX_PASSWORD_LEN}")

            elif key == "*":
                if buffer:
                    buffer = buffer[:-1]
                    print(f"Input: {masked(buffer)}")
                    if self.lcd:
                        self.lcd.show(input_line1[:16], masked(buffer))
                else:
                    print("Input is empty")
                    if self.lcd:
                        self.lcd.show_temp("Input empty", "")

            elif key == "#":
                print("Submitted")
                if self.lcd:
                    self.lcd.show_temp("Submitted", "Processing...")
                return buffer

    def admin_add_password(self):
        """Admin action: add one new user PIN after validation."""
        passwords = load_passwords(self.db_file)
        new_password = self.read_password_from_keypad("Admin Add")
        valid, message = validate_password_format(new_password, MIN_PASSWORD_LEN, MAX_PASSWORD_LEN)
        if not valid:
            print(f"Add failed: {message}")
            if self.lcd:
                self.lcd.show_temp("Add failed", message[:16])
            return
        if new_password == ADMIN_PASSWORD:
            print("Add failed: cannot add admin password to user database")
            if self.lcd:
                self.lcd.show_temp("Add failed", "Admin pwd blocked")
            return
        if new_password in passwords:
            print("Add failed: password already exists")
            if self.lcd:
                self.lcd.show_temp("Add failed", "Already exists")
            return

        passwords.append(new_password)
        save_passwords(self.db_file, passwords)
        print("Add success")
        if self.lcd:
            self.lcd.show_temp("Add success", "")

    def admin_delete_password(self):
        """Admin action: delete an existing user PIN."""
        passwords = load_passwords(self.db_file)
        target_password = self.read_password_from_keypad("Admin Delete")
        if target_password not in passwords:
            print("Delete failed: password not found")
            if self.lcd:
                self.lcd.show_temp("Delete failed", "Not found")
            return

        passwords.remove(target_password)
        save_passwords(self.db_file, passwords)
        print("Delete success")
        if self.lcd:
            self.lcd.show_temp("Delete success", "")

    def admin_modify_password(self):
        """Admin action: replace an old PIN with a new validated PIN."""
        passwords = load_passwords(self.db_file)

        old_password = self.read_password_from_keypad("Mod old password")
        if old_password not in passwords:
            print("Modify failed: old password not found")
            if self.lcd:
                self.lcd.show_temp("Modify failed", "Old not found")
            return

        new_password = self.read_password_from_keypad("Mod new password")
        valid, message = validate_password_format(new_password, MIN_PASSWORD_LEN, MAX_PASSWORD_LEN)
        if not valid:
            print(f"Modify failed: {message}")
            if self.lcd:
                self.lcd.show_temp("Modify failed", message[:16])
            return
        if new_password == ADMIN_PASSWORD:
            print("Modify failed: cannot use admin password as user password")
            if self.lcd:
                self.lcd.show_temp("Modify failed", "Admin pwd blocked")
            return
        if new_password in passwords and new_password != old_password:
            print("Modify failed: new password already exists")
            if self.lcd:
                self.lcd.show_temp("Modify failed", "New exists")
            return

        idx = passwords.index(old_password)
        passwords[idx] = new_password
        save_passwords(self.db_file, passwords)
        print("Modify success")
        if self.lcd:
            self.lcd.show_temp("Modify success", "")

    def admin_select_container_for_operation(self):
        """Admin action: select installed container and apply refill/reset policy."""
        container_id, inventory = self.select_container("Admin Select Box")
        if container_id is None:
            return None

        item = inventory[container_id]
        if not self._is_active_container(container_id, item):
            print(f"Container {container_id} is not physically installed")
            if self.lcd:
                self.lcd.show_temp("NOT INSTALLED", f"ID {container_id}")
            return None

        if self._is_carousel(item):
            item["stock"] = CAROUSEL_CAPACITY
            item["fullness"] = float(CAROUSEL_CAPACITY)
            save_inventory(self.inventory_file, inventory)
            print(f"Carousel {container_id} stock reset to {CAROUSEL_CAPACITY}")
            if self.lcd:
                self.lcd.show_temp("REFILL OK", f"CAR {container_id}")
            return (container_id, "carousel")

        # Lockbox refill path.
        item["stock"] = 1
        item["times_opened"] = 0
        starting_weight = float(item.get("starting_weight", LOCKBOX_DEFAULT_STARTING_WEIGHT))
        item["starting_weight"] = starting_weight
        item["current_weight"] = starting_weight
        item["fullness"] = 0.0
        save_inventory(self.inventory_file, inventory)
        print(f"Lockbox {container_id} reset")
        if self.lcd:
            self.lcd.show_temp("REFILL OK", f"LB {container_id}")
        return (container_id, "lockbox")

    def admin_control_carousel(self, item_id):
        """Manual carousel control: tap for jog, hold for continuous rotation."""
        print(f"Control carousel {item_id}")
        print("Tap 1 for small jog, hold 1 for continuous rotate, 9 to exit")

        if self.lcd:
            self.lcd.show("1:ROTATE", "9:EXIT")

        realtime_mode = hasattr(self.keypad, "get_current_key") and not isinstance(self.keypad, MockKeypad)

        def start_backward_with_boost(target_duty):
            if not self.motor or not self.motor.enabled:
                return
            # Short boost breaks static friction, then drop to low duty for controllability.
            self.motor.start_backward(ADMIN_CAROUSEL_START_DUTY)
            time.sleep(ADMIN_CAROUSEL_START_SECONDS)
            self.motor.start_backward(target_duty)

        if realtime_mode:
            was_pressed_1 = False
            press_started_at = 0.0
            last_seen_1_at = 0.0
            last_hold_kick_at = 0.0
            while True:
                key = self.keypad.get_current_key()
                now = time.monotonic()

                if key == "1":
                    last_seen_1_at = now

                # Treat short scan drops as still held to avoid motor stop/start chatter.
                key1_effective = (now - last_seen_1_at) <= ADMIN_CAROUSEL_HOLD_KEY_GRACE_S

                if key1_effective:
                    if not was_pressed_1:
                        was_pressed_1 = True
                        press_started_at = now
                        if self.motor and self.motor.enabled:
                            # Tap behavior: one short low-speed jog for fine control.
                            start_backward_with_boost(ADMIN_CAROUSEL_JOG_DUTY)
                            time.sleep(ADMIN_CAROUSEL_JOG_SECONDS)
                            self.motor.stop()
                            print(f"Carousel {item_id} jog")
                            if self.lcd:
                                self.lcd.show("JOG", "Hold 1 to run")
                        time.sleep(0.01)
                        continue

                    if (
                        self.motor
                        and self.motor.enabled
                        and (not self.motor.running or self.motor.direction != "backward")
                        and (now - press_started_at) >= ADMIN_CAROUSEL_HOLD_START_S
                    ):
                        start_backward_with_boost(ADMIN_CAROUSEL_HOLD_DUTY)
                        last_hold_kick_at = now
                        print(f"Carousel {item_id} motor running")
                        if self.lcd:
                            self.lcd.show("RUN", "9:EXIT")

                    # Periodic short torque kick helps pass detent points during long hold.
                    if (
                        self.motor
                        and self.motor.enabled
                        and self.motor.running
                        and self.motor.direction == "backward"
                        and (now - last_hold_kick_at) >= ADMIN_CAROUSEL_HOLD_KICK_INTERVAL_S
                    ):
                        self.motor.start_backward(ADMIN_CAROUSEL_HOLD_KICK_DUTY)
                        time.sleep(ADMIN_CAROUSEL_HOLD_KICK_SECONDS)
                        self.motor.start_backward(ADMIN_CAROUSEL_HOLD_DUTY)
                        last_hold_kick_at = now

                    time.sleep(0.01)
                    continue

                if was_pressed_1:
                    was_pressed_1 = False

                if self.motor and self.motor.enabled and self.motor.running:
                    self.motor.stop()
                    print(f"Carousel {item_id} motor stopped")
                    if self.lcd:
                        self.lcd.show("1:ROTATE", "9:EXIT")

                if key == "9":
                    if self.lcd:
                        self.lcd.show_temp("EXIT CONTROL", f"CAR {item_id}")
                    return

                time.sleep(0.01)

        # Mock keypad fallback: key hold is unavailable, so key 1 triggers one step.
        while True:
            key = self.keypad.get_key()
            if key == "1":
                print(f"Carousel {item_id} jog")
                if self.motor and self.motor.enabled:
                    start_backward_with_boost(ADMIN_CAROUSEL_JOG_DUTY)
                    time.sleep(ADMIN_CAROUSEL_JOG_SECONDS)
                    self.motor.stop()
                else:
                    time.sleep(ADMIN_CAROUSEL_JOG_SECONDS)
                if self.lcd:
                    self.lcd.show_temp(f"CAR {item_id}", "JOG")
                    self.lcd.show("1:ROTATE", "9:EXIT")
            elif key == "9":
                if self.lcd:
                    self.lcd.show_temp("EXIT CONTROL", f"CAR {item_id}")
                return
            else:
                print("Invalid key, use 1 or 9")
                if self.lcd:
                    self.lcd.show_temp("Invalid key", "Use 1/9")

    def admin_mode(self):
        """Admin menu loop for container operations, email, and password management."""
        print("\n=== ADMIN MODE ===")
        print("1: Select container (refill + control)")
        print("2: Send inventory email")
        print("3: Send history email")
        print("4: Add password")
        print("5: Delete password")
        print("6: Modify password")
        print("9: Exit admin mode")

        if self.lcd:
            self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")

        allowed_menu_keys = {"1", "2", "3", "4", "5", "6", "9"}
        realtime_mode = hasattr(self.keypad, "get_current_key") and not isinstance(self.keypad, MockKeypad)

        if realtime_mode:
            last_menu_key = None
            while True:
                key = self.keypad.get_current_key()

                # No key: keep scanning
                if key is None:
                    last_menu_key = None
                    time.sleep(0.01)
                    continue

                # Ignore scan noise and non-menu keys in admin screen
                if key not in allowed_menu_keys:
                    time.sleep(0.01)
                    continue

                # Edge trigger: act only once per physical press
                if key == last_menu_key:
                    time.sleep(0.01)
                    continue
                last_menu_key = key

                if key == "1":
                    result = self.admin_select_container_for_operation()
                    if result and result[1] == "carousel":
                        self.admin_control_carousel(result[0])
                    if self.lcd:
                        self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
                elif key == "2":
                    self.admin_send_inventory_email()
                    if self.lcd:
                        self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
                elif key == "3":
                    self.admin_send_history_email()
                    if self.lcd:
                        self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
                elif key == "4":
                    self.admin_add_password()
                    if self.lcd:
                        self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
                elif key == "5":
                    self.admin_delete_password()
                    if self.lcd:
                        self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
                elif key == "6":
                    self.admin_modify_password()
                    if self.lcd:
                        self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
                elif key == "9":
                    print("Exit admin mode")
                    if self.lcd:
                        self.lcd.show_temp("Exit admin", "")
                    return

                time.sleep(0.15)

        # Mock keypad mode fallback
        while True:
            key = self.keypad.get_key()
            if key == "1":
                result = self.admin_select_container_for_operation()
                if result and result[1] == "carousel":
                    self.admin_control_carousel(result[0])
                if self.lcd:
                    self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
            elif key == "2":
                self.admin_send_inventory_email()
                if self.lcd:
                    self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
            elif key == "3":
                self.admin_send_history_email()
                if self.lcd:
                    self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
            elif key == "4":
                self.admin_add_password()
                if self.lcd:
                    self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
            elif key == "5":
                self.admin_delete_password()
                if self.lcd:
                    self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
            elif key == "6":
                self.admin_modify_password()
                if self.lcd:
                    self.lcd.show("1:CONTAINER", "2I3H4A5D6M9X")
            elif key == "9":
                print("Exit admin mode")
                if self.lcd:
                    self.lcd.show_temp("Exit admin", "")
                return
            else:
                print("Invalid admin menu key")
                if self.lcd:
                    self.lcd.show_temp("Invalid menu", "Use 1/2/3/4/5/6/9")

    def handle_lock_box(self, lockbox_id):
        """Display helper before starting lockbox access routine."""
        print(f"Lock box {lockbox_id} selected")
        if self.lcd:
            self.lcd.show_temp("LOCK BOX", f"ID {lockbox_id}")

    def access_lockbox(self, lockbox_id, inventory):
        """Execute lockbox open/close cycle and update inventory counters."""
        item = inventory[lockbox_id]
        stock = item.get("stock", 0)
        if stock <= 0:
            print(f"Lockbox {lockbox_id} out of stock")
            if self.lcd:
                self.lcd.show_temp("OUT OF STOCK", f"LB {lockbox_id}")
            return False

        if self.lcd:
            self.lcd.show("LOCKBOX OPEN", f"ID {lockbox_id}")

        fallback_weight = float(
            item.get("current_weight", item.get("starting_weight", LOCKBOX_DEFAULT_STARTING_WEIGHT))
        )
        if self.lockbox:
            success, measured_weight = self.lockbox.access_box(lockbox_id, fallback_weight)
        else:
            success, measured_weight = True, fallback_weight

        if not success:
            print(f"Lockbox {lockbox_id} access failed")
            if self.lcd:
                self.lcd.show_temp("LOCKBOX ERROR", f"ID {lockbox_id}")
            return False

        if measured_weight is None:
            measured_weight = fallback_weight

        starting_weight = float(item.get("starting_weight", LOCKBOX_DEFAULT_STARTING_WEIGHT))
        item["times_opened"] = int(item.get("times_opened", 0)) + 1
        item["current_weight"] = max(0.0, float(measured_weight))
        item["fullness"] = max(0.0, starting_weight - item["current_weight"])
        item["stock"] = max(0, stock - 1)
        save_inventory(self.inventory_file, inventory)

        print(
            f"Lockbox access success: ID {lockbox_id}, stock {item['stock']}, "
            f"times_opened {item['times_opened']}, fullness {item['fullness']}"
        )
        if self.lcd:
            self.lcd.show_temp("LOCKBOX DONE", f"LEFT {item['stock']}")
        return True

    def rotate_carousel_step(self):
        """Timed fallback carousel step when no limit-switch indexing is available."""
        if self.motor and self.motor.enabled:
            self.motor.start_backward(MOTOR_DUTY_CYCLE)
            time.sleep(CAROUSEL_STEP_SECONDS)
            self.motor.stop()
        else:
            # In development/mock mode, simulate a single fixed-angle step.
            time.sleep(CAROUSEL_STEP_SECONDS)

    def _clockwise_release_nudge(self, gpio, pin, item_id):
        """Apply a short clockwise nudge so the switch ends fully released (HIGH)."""
        if not self.motor or not self.motor.enabled:
            return gpio.input(pin) == gpio.HIGH

        deadline = time.monotonic() + CAROUSEL_LIMIT_RELEASE_NUDGE_TIMEOUT_S
        self.motor.start_forward(CAROUSEL_LIMIT_RELEASE_NUDGE_DUTY)
        while time.monotonic() < deadline:
            if gpio.input(pin) == gpio.HIGH:
                settle_deadline = time.monotonic() + CAROUSEL_LIMIT_RELEASE_NUDGE_SETTLE_S
                stable_high = True
                while time.monotonic() < settle_deadline:
                    if gpio.input(pin) == gpio.LOW:
                        stable_high = False
                        break
                    time.sleep(0.002)
                if stable_high and gpio.input(pin) == gpio.HIGH:
                    self.motor.stop()
                    print(f"Carousel {item_id} release nudge done (switch HIGH)")
                    return True
            time.sleep(0.002)
        self.motor.stop()

        print(f"Carousel {item_id} release nudge failed (switch still LOW)")
        return False

    def rotate_carousel_until_switch_release(self, item_id):
        """Index carousel by limit-switch edge tracking and stable-release verification."""
        pin = CAROUSEL_LIMIT_SWITCH_PINS.get(item_id)

        # If this carousel has no configured switch, fallback to timed movement.
        if pin is None or self._limit_gpio is None:
            self.rotate_carousel_step()
            return True

        if not self.motor or not self.motor.enabled:
            # Development mode: simulate time delay.
            time.sleep(CAROUSEL_STEP_SECONDS)
            return True

        gpio = self._limit_gpio

        for attempt in range(CAROUSEL_LIMIT_MAX_RETRIES + 1):
            try:
                # If a prior failure left the switch pressed, first force it back to released (HIGH).
                if gpio.input(pin) == gpio.LOW:
                    print(f"Carousel {item_id} switch stuck LOW, recovery attempt {attempt + 1}")
                    self.motor.start_backward(CAROUSEL_LIMIT_RECOVERY_DUTY)
                    deadline_recover = time.monotonic() + CAROUSEL_LIMIT_RECOVERY_TIMEOUT_S
                    while time.monotonic() < deadline_recover:
                        if gpio.input(pin) == gpio.HIGH:
                            # Starting LOW then reaching first HIGH already means one index edge was completed.
                            self.motor.stop()

                            # Quick settle check to avoid counting switch bounce as a finished move.
                            settle_deadline = time.monotonic() + CAROUSEL_LIMIT_SETTLE_CHECK_S
                            bounced_back_low = False
                            while time.monotonic() < settle_deadline:
                                if gpio.input(pin) == gpio.LOW:
                                    bounced_back_low = True
                                    break
                                time.sleep(0.002)

                            if not bounced_back_low and gpio.input(pin) == gpio.HIGH:
                                if self._clockwise_release_nudge(gpio, pin, item_id):
                                    return True
                                print(f"Carousel {item_id} nudge failed after recovery, retrying")
                                break
                            # If it bounced back low, continue recovery motion inside this attempt.
                            self.motor.start_backward(CAROUSEL_LIMIT_RECOVERY_DUTY)
                        time.sleep(0.002)
                    else:
                        continue

                # Move normally until next press edge (LOW).
                self.motor.start_backward(CAROUSEL_LIMIT_SEARCH_DUTY)
                deadline_press = time.monotonic() + CAROUSEL_LIMIT_WAIT_PRESS_S
                press_found = False
                while time.monotonic() < deadline_press:
                    if gpio.input(pin) == gpio.LOW:
                        press_found = True
                        break
                    time.sleep(0.002)
                if not press_found:
                    print(f"Carousel {item_id} limit switch not pressed before timeout")
                    continue

                # Remove inertia before entering low-speed release tracking.
                self.motor.stop()
                self.motor.start_forward(CAROUSEL_LIMIT_BRAKE_DUTY)
                time.sleep(CAROUSEL_LIMIT_BRAKE_PULSE_S)
                self.motor.stop()
                time.sleep(CAROUSEL_LIMIT_PRESS_SETTLE_S)

                # Ignore false press edges caused by bounce.
                if gpio.input(pin) != gpio.LOW:
                    print(f"Carousel {item_id} press edge bounced, retrying")
                    continue

                # Slow approach for cleaner release edge.
                self.motor.start_backward(CAROUSEL_LIMIT_APPROACH_DUTY)
                release_found = False
                deadline_release = time.monotonic() + CAROUSEL_LIMIT_WAIT_RELEASE_S
                while time.monotonic() < deadline_release:
                    if gpio.input(pin) == gpio.HIGH:
                        self.motor.stop()

                        # Apply brief active braking at release edge to reduce overshoot.
                        self.motor.start_forward(CAROUSEL_LIMIT_BRAKE_DUTY)
                        time.sleep(CAROUSEL_LIMIT_BRAKE_PULSE_S)
                        self.motor.stop()

                        # Short settle check; if re-pressed, keep moving slowly to release again.
                        settle_deadline = time.monotonic() + CAROUSEL_LIMIT_SETTLE_CHECK_S
                        repressed = False
                        while time.monotonic() < settle_deadline:
                            if gpio.input(pin) == gpio.LOW:
                                repressed = True
                                break
                            time.sleep(0.002)

                        if repressed:
                            print(f"Carousel {item_id} overshoot detected, applying correction")
                            self.motor.start_backward(CAROUSEL_LIMIT_CORRECTION_DUTY)
                            correction_deadline = time.monotonic() + CAROUSEL_LIMIT_CORRECTION_TIMEOUT_S
                            while time.monotonic() < correction_deadline:
                                if gpio.input(pin) == gpio.HIGH:
                                    break
                                time.sleep(0.002)
                            self.motor.stop()

                        # Only accept success if the final state is stably released (HIGH).
                        settle_deadline = time.monotonic() + CAROUSEL_LIMIT_SETTLE_CHECK_S
                        stable_high = True
                        while time.monotonic() < settle_deadline:
                            if gpio.input(pin) == gpio.LOW:
                                stable_high = False
                                break
                            time.sleep(0.002)

                        if stable_high and gpio.input(pin) == gpio.HIGH:
                            if self._clockwise_release_nudge(gpio, pin, item_id):
                                release_found = True
                                break
                            print(f"Carousel {item_id} nudge failed after release edge, retrying")
                            break

                        print(f"Carousel {item_id} ended in LOW after release edge, retrying")
                        break
                    time.sleep(0.002)

                if release_found:
                    return True

                print(f"Carousel {item_id} limit switch did not reach stable release before timeout")
            finally:
                self.motor.stop()

        return False

    def dispense_from_carousel(self, item_id, inventory):
        """Dispense one unit from carousel and persist updated stock."""
        item = inventory[item_id]
        stock = item["stock"]

        if stock <= 0:
            print(f"Carousel {item_id} out of stock")
            if self.lcd:
                self.lcd.show_temp("OUT OF STOCK", f"ID {item_id}")
            return False

        print(f"Carousel {item_id} selected -> rotate one fixed step")
        if self.lcd:
            self.lcd.show("CAROUSEL MOVE", f"ID {item_id}")

        moved = self.rotate_carousel_until_switch_release(item_id)
        if not moved:
            if self.lcd:
                self.lcd.show_temp("CAROUSEL ERROR", f"ID {item_id}")
            return False

        item["stock"] = max(0, stock - 1)
        item["fullness"] = float(item["stock"])
        save_inventory(self.inventory_file, inventory)

        print(f"Dispense success: carousel {item_id}, remaining stock {item['stock']}")
        if self.lcd:
            self.lcd.show_temp("DISPENSED", f"LEFT {item['stock']}")
        return True

    def run(self):
        """Top-level runtime loop handling user login and operation dispatch."""
        print("=== Vending Machine Password System ===")
        print("Enter user password and press #")
        print("Enter admin password to open admin mode")

        if self.lcd:
            self.lcd.show("Enter password", "#=submit *=del")

        while True:
            entered = self.read_password_from_keypad("Enter password")
            if not entered:
                print("Password error: empty input")
                if self.lcd:
                    self.lcd.show_temp("Password error", "Empty input")
                continue

            if entered == ADMIN_PASSWORD:
                print("Admin password correct")
                if self.lcd:
                    self.lcd.show_temp("ENTER ADMIN", "", delay_s=2.0)
                self.admin_mode()
                if self.lcd:
                    self.lcd.show("Enter password", "#=submit *=del")
                continue

            passwords = load_passwords(self.db_file)
            if entered in passwords:
                print("Password correct")
                if self.lcd:
                    self.lcd.show_temp("Password", "Correct")

                container_id, inventory = self.select_container("Select container number")
                if container_id is not None:
                    item = inventory[container_id]
                    if not self._is_active_container(container_id, item):
                        print(f"Container {container_id} is not physically installed")
                        if self.lcd:
                            self.lcd.show_temp("NOT INSTALLED", f"ID {container_id}")
                        if self.lcd:
                            self.lcd.show("Enter password", "#=submit *=del")
                        continue

                    if self._is_lockbox(item):
                        self.handle_lock_box(container_id)
                        if self.access_lockbox(container_id, inventory):
                            self.write_history(entered, "lockbox", container_id)
                    else:
                        if self.dispense_from_carousel(container_id, inventory):
                            self.write_history(entered, "carousel", container_id)
            else:
                print("Password incorrect")
                if self.lcd:
                    self.lcd.show_temp("Password", "Incorrect")

            if self.lcd:
                self.lcd.show("Enter password", "#=submit *=del")
