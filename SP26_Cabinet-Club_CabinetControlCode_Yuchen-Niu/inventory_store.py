#!/usr/bin/env python3

"""Inventory CSV read/write helpers and default schema for items 1-15."""

import csv
import os

from config_vm import CAROUSEL_CAPACITY, LOCKBOX_DEFAULT_STARTING_WEIGHT


FIELDS = [
    "item_id",
    "container_type",
    "stock",
    "times_opened",
    "starting_weight",
    "current_weight",
    "fullness",
]


def default_inventory():
    """Build the default inventory dictionary for all configured container IDs."""
    inventory = {}

    # Containers 1-9 are lockboxes.
    for container_id in range(1, 10):
        item_id = str(container_id)
        inventory[item_id] = {
            "item_id": item_id,
            "container_type": "lockbox",
            "stock": 1,
            "times_opened": 0,
            "starting_weight": LOCKBOX_DEFAULT_STARTING_WEIGHT,
            "current_weight": LOCKBOX_DEFAULT_STARTING_WEIGHT,
            "fullness": 0.0,
        }

    # Containers 10-15 are carousels.
    for container_id in range(10, 16):
        item_id = str(container_id)
        inventory[item_id] = {
            "item_id": item_id,
            "container_type": "carousel",
            "stock": CAROUSEL_CAPACITY,
            "times_opened": 0,
            "starting_weight": 0.0,
            "current_weight": 0.0,
            "fullness": float(CAROUSEL_CAPACITY),
        }

    return inventory


def ensure_inventory_file(file_path):
    """Create inventory CSV from defaults when file is missing."""
    if os.path.exists(file_path):
        return

    defaults = default_inventory()

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for item_id in sorted(defaults.keys(), key=lambda value: int(value)):
            writer.writerow(defaults[item_id])


def load_inventory(file_path):
    """Load inventory from CSV and normalize invalid/missing fields."""
    ensure_inventory_file(file_path)
    inventory = {}

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            item_id = (row.get("item_id") or "").strip()
            if not item_id:
                continue
            if item_id.lower() == "item_id":
                continue

            try:
                stock = int((row.get("stock") or "0").strip())
            except ValueError:
                stock = 0

            container_type = (row.get("container_type") or "carousel").strip().lower()
            if container_type not in {"carousel", "lockbox"}:
                container_type = "carousel"

            try:
                times_opened = int((row.get("times_opened") or "0").strip())
            except ValueError:
                times_opened = 0

            try:
                starting_weight = float(
                    (row.get("starting_weight") or str(LOCKBOX_DEFAULT_STARTING_WEIGHT)).strip()
                )
            except ValueError:
                starting_weight = LOCKBOX_DEFAULT_STARTING_WEIGHT

            try:
                current_weight = float((row.get("current_weight") or str(starting_weight)).strip())
            except ValueError:
                current_weight = starting_weight

            # If old CSV had only stock, synthesize fullness.
            fullness_raw = row.get("fullness")
            if fullness_raw is None or str(fullness_raw).strip() == "":
                if container_type == "lockbox":
                    fullness = max(0.0, starting_weight - current_weight)
                else:
                    fullness = float(max(0, stock))
            else:
                try:
                    fullness = float(str(fullness_raw).strip())
                except ValueError:
                    fullness = 0.0

            inventory[item_id] = {
                "container_type": container_type,
                "stock": max(0, stock),
                "times_opened": max(0, times_opened),
                "starting_weight": max(0.0, starting_weight),
                "current_weight": max(0.0, current_weight),
                "fullness": max(0.0, fullness),
            }

    # Ensure required container IDs (1-15) are always present.
    defaults = default_inventory()
    for item_id, default_item in defaults.items():
        if item_id not in inventory:
            inventory[item_id] = {
                "container_type": default_item["container_type"],
                "stock": int(default_item["stock"]),
                "times_opened": int(default_item["times_opened"]),
                "starting_weight": float(default_item["starting_weight"]),
                "current_weight": float(default_item["current_weight"]),
                "fullness": float(default_item["fullness"]),
            }

    return inventory


def save_inventory(file_path, inventory):
    """Persist normalized inventory rows back to CSV in numeric ID order."""
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for item_id in sorted(inventory.keys(), key=lambda value: int(value)):
            item = inventory[item_id]
            writer.writerow(
                {
                    "item_id": item_id,
                    "container_type": item.get("container_type", "carousel"),
                    "stock": int(item.get("stock", 0)),
                    "times_opened": int(item.get("times_opened", 0)),
                    "starting_weight": float(item.get("starting_weight", 0.0)),
                    "current_weight": float(item.get("current_weight", 0.0)),
                    "fullness": float(item.get("fullness", 0.0)),
                }
            )
