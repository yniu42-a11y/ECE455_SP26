# ECE455 Project Snapshot

Last updated: 2026-04-26

## 1. Project Goal
Raspberry Pi vending machine app with:
- Password-based user/admin access
- Carousel dispensing with limit-switch indexing
- Lockbox access flow (IDs 1-9)
- CSV-based inventory and history records

## 2. Main Runtime Flow
- Entry point: main.py
- Boot checks create files if missing:
  - passwords.csv
  - inventory.csv
  - history.csv
- Hardware objects are created:
  - LCD
  - Motor controller
  - Lockbox controller
  - Keypad (real or mock)
- App loop runs in vending_app.py

## 3. Key Files
- main.py: dependency wiring and app startup
- vending_app.py: user/admin logic, carousel and lockbox actions
- config_vm.py: all GPIO pins and tuning constants
- inventory_store.py: inventory schema load/save
- lockbox_controller.py: lock pulse and open/close wait logic

## 4. Container Model
- Lockbox IDs: 1-9
- Carousel IDs: 10-15 (carousel limit switch currently configured for 10)

Physical install status:
- Only lockbox ID 1 is currently wired and controlled.
- Only carousel ID 10 is currently wired and controlled.
- UI still allows selecting IDs 1-15 for consistency with inventory schema.

## 5. Current Carousel (12V) Parameters
From config_vm.py:
- CAROUSEL_LIMIT_SEARCH_DUTY = 44
- CAROUSEL_LIMIT_APPROACH_DUTY = 33
- CAROUSEL_LIMIT_CORRECTION_DUTY = 35
- CAROUSEL_LIMIT_RECOVERY_DUTY = 58
- CAROUSEL_LIMIT_WAIT_PRESS_S = 5.0
- CAROUSEL_LIMIT_WAIT_RELEASE_S = 5.0
- CAROUSEL_LIMIT_MAX_RETRIES = 2
- CAROUSEL_LIMIT_BRAKE_DUTY = 38
- CAROUSEL_LIMIT_BRAKE_PULSE_S = 0.012
- CAROUSEL_LIMIT_RELEASE_NUDGE_DUTY = 20
- CAROUSEL_LIMIT_RELEASE_NUDGE_TIMEOUT_S = 0.25

## 6. Lockbox Wiring/Logic Assumptions
- Lock coil uses external power/control path (not direct GPIO power)
- Detect switch logic in software expects:
  - closed = LOW
  - open = HIGH
- Current deployment lockbox wiring is only for ID 1.

## 7. Known Operational Focus
Main active tuning area is carousel indexing stability under 12V:
- Avoid multi-slot overshoot
- Avoid stall in detent/cam resistance regions
- End in released switch state for correct user pickup alignment

## 8. Useful Commands
Run app:
- python main.py

Quick syntax check:
- python3 -m py_compile vending_app.py config_vm.py main.py

## 9. Notes for Future Q&A (When RP Is Not Connected)
If you ask about this project without RP connected, provide these files from your local copy:
- PROJECT_SNAPSHOT.md
- TUNING_LOG.md
- HOW_TO_BUILD.md
- config_vm.py
- vending_app.py
This is enough context for most troubleshooting and change planning.
