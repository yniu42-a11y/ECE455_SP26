#!/usr/bin/env python3

"""History CSV helpers for usage logging."""

import csv
import os
from datetime import datetime


HISTORY_FIELDS = ["timestamp", "user_pin", "container_type", "container_id"]


def ensure_history_file(file_path):
    """Create the history CSV with header if it does not exist."""
    if os.path.exists(file_path):
        return

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HISTORY_FIELDS)
        writer.writeheader()


def append_history_entry(file_path, user_pin, container_type, container_id):
    """Append one usage record with an ISO timestamp."""
    ensure_history_file(file_path)

    with open(file_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HISTORY_FIELDS)
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "user_pin": str(user_pin),
                "container_type": str(container_type),
                "container_id": str(container_id),
            }
        )
