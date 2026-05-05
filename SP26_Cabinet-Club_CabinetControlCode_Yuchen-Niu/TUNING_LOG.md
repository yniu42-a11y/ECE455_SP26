# ECE455 Tuning Log

Purpose:
Keep a compact history of control-parameter changes and measured behavior.
Use this file as the source of truth when switching machines/environments.

---

## Entry Template
Date:
Environment:
- Supply voltage:
- Mechanical setup notes:

Changed files:
- config_vm.py
- vending_app.py

Parameters changed:
- NAME: old -> new

Observed behavior:
- Improvement:
- Regression:

Decision:
- Keep / Revert / Iterate

Next adjustment:
- One small planned change only

---

## 2026-04-26 Baseline Snapshot
Environment:
- Supply voltage: 12V
- Carousel uses limit-switch indexing

Current user carousel constants (config_vm.py):
- CAROUSEL_LIMIT_SEARCH_DUTY = 44
- CAROUSEL_LIMIT_APPROACH_DUTY = 33
- CAROUSEL_LIMIT_CORRECTION_DUTY = 35
- CAROUSEL_LIMIT_RECOVERY_DUTY = 58
- CAROUSEL_LIMIT_BRAKE_DUTY = 38
- CAROUSEL_LIMIT_BRAKE_PULSE_S = 0.012
- CAROUSEL_LIMIT_RELEASE_NUDGE_DUTY = 20
- CAROUSEL_LIMIT_RELEASE_NUDGE_TIMEOUT_S = 0.25

Status notes:
- Ongoing tradeoff between anti-stall torque and overshoot control.
- Strategy preference: small single-step tuning changes.
