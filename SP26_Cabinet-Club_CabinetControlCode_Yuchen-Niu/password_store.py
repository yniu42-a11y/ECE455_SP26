#!/usr/bin/env python3

"""Password CSV persistence and validation helpers."""

import csv
import os


def ensure_db_file(db_file):
    """Create password database file with header when missing."""
    if not os.path.exists(db_file):
        with open(db_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["password"])


def load_passwords(db_file):
    """Load all stored user passwords from CSV."""
    ensure_db_file(db_file)
    passwords = []

    with open(db_file, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            value = (row.get("password") or "").strip()
            if value:
                passwords.append(value)

    return passwords


def save_passwords(db_file, passwords):
    """Overwrite password CSV with provided password list."""
    with open(db_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["password"])
        for password in passwords:
            writer.writerow([password])


def masked(password):
    """Return a masked string with same length as password."""
    return "*" * len(password)


def validate_password_format(password, min_len, max_len):
    """Validate numeric PIN format and length bounds."""
    if not password:
        return False, "Password cannot be empty"
    if not password.isdigit():
        return False, "Password must contain digits only"
    if len(password) < min_len:
        return False, f"Password must be at least {min_len} digits"
    if len(password) > max_len:
        return False, f"Password must be <= {max_len} digits"
    return True, "OK"
