# Copilot Instructions for ECE455

## Project Context
- This repository is a Raspberry Pi vending-machine controller for ECE455.
- Main entry point: `main.py`.
- Runtime logic and user/admin flows: `vending_app.py`.
- Hardware and tuning constants: `config_vm.py`.
- Persistent CSV stores: `inventory_store.py`, `history_store.py`, `password_store.py`.
- Hardware wrappers: `matrix_keypad.py`, `lcd_display.py`, `motor_controller.py`, `lockbox_controller.py`.

## Physical Deployment Scope
- Only lockbox ID `1` is physically wired and controlled.
- Only carousel ID `10` is physically wired and controlled.
- The UI and inventory schema still show IDs `1` through `15` for consistency.
- Do not expand runtime control to uninstalled hardware unless the user explicitly requests it.

## Important Safety Rules
- Never hardcode secrets or API keys in source files.
- Keep SendGrid credentials in environment variables or a local `.env` file.
- If a secret is found in the repo, treat it as compromised and recommend rotation.
- Do not power motors or locks directly from Raspberry Pi GPIO.
- Preserve the current 12V motor/lock power-domain assumptions unless asked to redesign wiring.

## Current Hardware Assumptions
- Raspberry Pi uses BCM GPIO numbering.
- Carousel motor uses the L298N driver.
- Carousel indexing uses a limit switch on container `10`.
- LCD is a 16x2 I2C display at address `0x27`.
- Keypad is a 3x4 matrix keypad.
- Lockbox detect logic assumes closed = LOW and open = HIGH.

## Editing Guidance
- Prefer the smallest change that fixes the requested behavior.
- Keep code style and naming consistent with surrounding files.
- Avoid unrelated refactors.
- Do not remove existing comments or documentation unless they are incorrect.
- If changing hardware pins or timings, update `config_vm.py` and the build docs together.

## Verification
- First choice: run `python3 -m py_compile` on touched Python files.
- For app-level checks, run `python main.py` only when hardware is connected and safe.
- If email changes are made, verify `test_email.py` still loads credentials from the environment first.
- If hardware behavior changes, compare against `HOW_TO_BUILD.md` and `TUNING_LOG.md`.

## Useful Reference Files
- `PROJECT_SNAPSHOT.md` for a short current-state summary.
- `HOW_TO_BUILD.md` for reproducible build, wiring, and setup steps.
- `TUNING_LOG.md` for carousel tuning history and observed behavior.

## Communication Style
- When summarizing changes, focus on what changed and how it was verified.
- If SendGrid returns `403 Forbidden`, assume the issue may be account-side until proven otherwise.
- If a local file is missing or hardware is not connected, state that clearly instead of guessing.