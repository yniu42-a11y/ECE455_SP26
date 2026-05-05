# ECE455 Vending Machine Build and Reproduction Guide

Document owner scope: software and software-defined hardware integration (GPIO mapping, runtime behavior, verification procedure).

Last updated: 2026-04-26

## 0) Rubric Coverage Matrix

| Rubric item | Where this document addresses it | What evidence to submit |
|---|---|---|
| Professionalism (10) | Section 2 and Section 2.1 | Final polished schematics, labeled photos, figure captions |
| Reproducibility (10) | Sections 3, 4, 5, 6, 7, 11, 12 | BOM, exact wiring map, setup commands, run instructions, code-comment map |
| Design Verification (10) | Section 9 | Completed test matrix with measured outcomes and logs |
| Design Strategy (10) | Sections 8 and 10 | Design rationale, failure analysis, troubleshooting path and fixes |

## 1) Project Summary
This project is a Raspberry Pi based vending controller with two container types:
- Lockboxes (IDs 1-9)
- Carousel bins (IDs 10-15)

Current physical deployment (this build):
- Installed lockbox: ID 1 only
- Installed carousel: ID 10 only
- Software still shows/selects IDs 1-15 to keep schema and UI consistent.

Main functions:
- User and admin authentication using keypad passwords
- Carousel indexing using a limit switch (container 10 configured)
- Lockbox open, wait for close, and inventory updates
- LCD status display
- Inventory and history persisted to CSV

Primary entry point: main.py

## 2) Professional System Figures and Schematics
Figure 1. System architecture (functional block diagram)

    +---------------------+          +----------------------+
    |   Matrix Keypad     |          |   16x2 I2C LCD       |
    |   (3x4 membrane)    |          |   (PCF8574 backpack) |
    +----------+----------+          +----------+-----------+
               |                                |
               | GPIO scan                      | I2C
               v                                v
    +--------------------------------------------------------+
    |                  Raspberry Pi (BCM GPIO)               |
    |  - main.py creates all controllers                     |
    |  - vending_app.py runs user/admin state machine        |
    +-----+----------------------+----------------------+-----+
          |                      |                      |
          | IN1/IN2/ENA PWM      | lock pulse + detect  | limit switch input
          v                      v                      v
    +------------+         +-------------+        +-------------+
    |   L298N    |         | Lock driver |        | SS-5GL NO   |
    | Motor drv  |         | (relay/FET) |        | limit switch |
    +-----+------+         +------+------+        +------+------+ 
          |                       |                      |
          | Motor output          | 12V lock coil        | COM->GND
          v                       v                      | NO->GPIO17
      Carousel DC motor      Cabinet lock(s)            +-------------+

Figure 2. Power-domain schematic (critical for stability)

    12V PSU (+) -----------------> L298N VMOT
                    \-----------> Lock driver supply
    12V PSU (-) ----+------------> L298N GND
                    +------------> Lock driver GND
                    +------------> Raspberry Pi GND (common ground)

    Raspberry Pi GPIO pins are signal only.
    Do NOT power motors or lock coils directly from Raspberry Pi GPIO.

## 2.1 Required High-Quality Figure Package (for Grading)
To satisfy the professionalism rubric, include these final figures in your slide deck/report:

1. `Figure A`: full system architecture block diagram (clean vector graphic, not screenshot of terminal text)
2. `Figure B`: electrical schematic (power domain + GPIO signal domain)
3. `Figure C`: annotated wiring photo of actual hardware
4. `Figure D`: close-up of motor driver and limit-switch wiring labels
5. `Figure E`: close-up of lockbox wiring labels

Figure quality requirements:
- Use a schematic tool (draw.io, Fritzing, KiCad, or equivalent)
- Label all pins with BCM numbers and net names
- Add caption with one-sentence purpose and assumptions
- Export at high resolution (recommended 1920 px width or larger)
- Ensure wire colors in drawing match real wiring photo labels

## 3) Bill of Materials (BOM)
Minimum reproducible set:

| Qty | Item | Typical spec/model | Notes |
|---:|---|---|---|
| 1 | Raspberry Pi | Pi 4B recommended | Runs Python control app |
| 1 | microSD card | 16 GB+ | Raspberry Pi OS |
| 1 | DC motor driver | L298N module | Carousel motor channel A used |
| 1 | DC motor | 12V compatible motor/gear motor | Drives carousel |
| 1 | Limit switch | SS-5GL style NO microswitch | Carousel index feedback |
| 1 | Matrix keypad | 3x4 membrane keypad | Password input |
| 1 | LCD | 16x2 with I2C backpack (PCF8574) | Address 0x27 in code |
| 1+ | Electric lock | 12V lock with detect switch | For lockbox flow |
| 1+ | Lock driver channel(s) | Relay or MOSFET channels | Lock coil switching |
| 1 | 12V power supply | Current sized for motor + lock | Shared power domain |
| - | Wires, terminals, breadboard | - | Integration wiring |
| - | Flyback diode(s) | 1N400x or similar | Required on lock coils if MOSFET switching |

Optional:
- HX711 + load cell (weight logic placeholder exists, hardware integration not completed)
- SendGrid/email setup for report sending

## 4) Software Setup and Repository Structure
Project root:
- main.py: startup and dependency wiring
- vending_app.py: user/admin logic and hardware workflows
- config_vm.py: pin assignments and tuning constants
- matrix_keypad.py, lcd_display.py, motor_controller.py, lockbox_controller.py
- inventory_store.py, history_store.py, password_store.py

## 4.1 How to Connect to the Raspberry Pi
There are several valid ways to work with this project on the Raspberry Pi.

### Method A: Direct Local Access on the Pi
Use this when the Pi is connected to a monitor, keyboard, and mouse.
1. Power on the Raspberry Pi.
2. Log in at the desktop or console.
3. Open a terminal.
4. Change into the project folder.
    - `cd /home/pi/ECE455`
5. Run the app or syntax checks from that terminal.

This is the simplest option for first bring-up and hardware debugging.

### Method B: SSH Over Wi-Fi or Ethernet
Use this when the Pi is on the network and you want to control it from another computer.
1. Enable SSH on the Raspberry Pi.
2. Make sure the Pi and your laptop are on the same network.
3. Find the Pi IP address from the router, desktop network panel, or `hostname -I` on the Pi.
4. From your laptop, connect with SSH.
    - Example: `ssh pi@<pi-ip-address>`
5. Enter the Pi password when prompted.
6. Navigate to the repository and run commands as needed.

This is the best option if you want to edit files remotely without touching the Pi directly.

### Method C: VNC or Remote Desktop
Use this when you want the Pi desktop GUI from another machine.
1. Enable VNC on the Raspberry Pi.
2. Install a VNC viewer on your computer.
3. Connect to the Pi using its IP address.
4. Open the project folder and use the desktop normally.

This is useful if you need the full GUI, not just a terminal.

### Method D: VS Code Remote SSH
Use this if you want to edit and run the project from VS Code on your computer.
1. Install the VS Code Remote - SSH extension.
2. Enable SSH on the Pi.
3. Connect VS Code to `pi@<pi-ip-address>`.
4. Open `/home/pi/ECE455` in the remote workspace.
5. Use the built-in terminal and editor on the remote Pi.

This is usually the most convenient development workflow for code changes.

### What I Used / What You Can Reproduce
For this project, the most important part is not the exact UI tool, but that you can reliably reach the Pi shell and the `/home/pi/ECE455` folder. Any of the methods above is acceptable as long as it lets you:
- edit the Python files,
- run `python main.py`, and
- run syntax checks such as `python3 -m py_compile ...`.

Recommended setup steps on Raspberry Pi:
1. Install Python and system updates.
2. Enable I2C (for LCD) in Raspberry Pi configuration.
3. Create and activate virtual environment.
4. Install Python packages used by the project.
5. Run syntax check.
6. Launch main app.

Commands:
- python3 -m venv .venv
- source .venv/bin/activate
- pip install RPLCD RPi.GPIO
- python3 -m py_compile vending_app.py config_vm.py main.py
- python main.py

Environment reproducibility capture commands:
- python3 --version
- pip --version
- uname -a
- git rev-parse --short HEAD

## 5) Exact GPIO and Wiring Map from Current Code
Source of truth: config_vm.py and matrix_keypad.py

### 5.1 Carousel motor (L298N channel A)
- MOTOR_IN1_PIN = BCM23 (RP physical pin 16)
- MOTOR_IN2_PIN = BCM24 (RP physical pin 18)
- MOTOR_ENA_PIN = BCM18 (RP physical pin 12, PWM)
- MOTOR_PWM_FREQ = 1000

L298N wiring:
- IN1 <- BCM23 (pin 16)
- IN2 <- BCM24 (pin 18)
- ENA <- BCM18 (pin 12)
- VMOT <- +12V external
- GND <- 12V GND and Raspberry Pi GND (common)
- OUT1/OUT2 -> carousel motor terminals

### 5.2 Carousel limit switch
Configured map:
- container 10 -> BCM17 (RP physical pin 11)

Current deployment:
- Only container 10 is physically wired for carousel control.

Wiring expectation in code:
- COM -> GND
- NO -> BCM17 (pin 11)
- Pull-up enabled in software
- Pressed state = LOW
- Released state = HIGH

### 5.3 Keypad (3x4)
Rows (BCM):
- R1=BCM26 (pin 37)
- R2=BCM19 (pin 35)
- R3=BCM13 (pin 33)
- R4=BCM6 (pin 31)

Columns (BCM):
- C1=BCM27 (pin 13)
- C2=BCM20 (pin 38)
- C3=BCM22 (pin 15)

This mapping is already implemented in matrix_keypad.py.

### 5.4 LCD (I2C)
- Address: 0x27
- Raspberry Pi I2C bus 1
- SDA: BCM2 (RP physical pin 3)
- SCL: BCM3 (RP physical pin 5)
- Also connect LCD VCC and GND to Pi 5V and GND

### 5.5 Lockbox control and detect GPIO map (current code)
- ID1: lock BCM4 (pin 7), detect BCM14 (pin 8)

Current deployment:
- Only lockbox ID 1 is physically wired and controlled.
- IDs 2-9 remain inventory/UI entries but are not controlled in runtime.

Important integration note:
- There are pin overlaps between lockbox map and carousel motor pins (BCM18/23/24).
- If you need simultaneous full lockbox + carousel production behavior, remap LOCKBOX_CONFIG to non-conflicting pins.
- The software supports remapping by editing config_vm.py.

### 5.6 Lock wiring practice
- Lock red/black coil wires must be switched by relay/MOSFET from 12V supply.
- Do not drive lock coil directly from GPIO.
- Detect wires (blue/yellow style) are status switch lines to GPIO input path.
- Code assumes detect closed=LOW, open=HIGH using pull-up.

### 5.7 Quick BCM to RP Pin Reference (Used in This Build)
- BCM2 -> pin 3 (I2C SDA)
- BCM3 -> pin 5 (I2C SCL)
- BCM4 -> pin 7
- BCM6 -> pin 31
- BCM13 -> pin 33
- BCM14 -> pin 8
- BCM17 -> pin 11
- BCM18 -> pin 12
- BCM19 -> pin 35
- BCM20 -> pin 38
- BCM22 -> pin 15
- BCM23 -> pin 16
- BCM24 -> pin 18
- BCM26 -> pin 37
- BCM27 -> pin 13

## 6) Build Procedure (Step-by-Step)
1. Assemble Raspberry Pi and verify boot.
2. Wire keypad and LCD first; run app with motor disconnected to verify UI and passwords.
3. Wire L298N and motor using external 12V and shared ground.
4. Wire limit switch COM->GND and NO->BCM17.
5. Run app and test admin manual carousel control.
6. Tune carousel constants in config_vm.py only if needed.
7. Add lock driver wiring and one lockbox channel; verify open/close detection.
8. Scale lockbox channels if required and resolve any pin conflicts.

## 6.1 Field Wiring Checklist (Pin-by-Pin, On-Site Use)
Use this checklist during physical assembly. Mark each item only after continuity/polarity is verified.

Power and safety first:
- [ ] 12V power supply is OFF before wiring.
- [ ] Raspberry Pi is OFF before wiring.
- [ ] Shared ground plan is understood (Pi GND, L298N GND, lock driver GND, 12V negative).

Raspberry Pi physical pin order checklist:

Pin 3 (BCM2, I2C SDA)
- [ ] Connect LCD SDA to pin 3.

Pin 5 (BCM3, I2C SCL)
- [ ] Connect LCD SCL to pin 5.

Pin 7 (BCM4)
- [ ] Connect lockbox ID1 lock control signal (to lock driver input channel) to pin 7.

Pin 8 (BCM14)
- [ ] Connect lockbox ID1 detect signal wire to pin 8.

Pin 11 (BCM17)
- [ ] Connect carousel limit switch NO to pin 11.

Pin 12 (BCM18)
- [ ] Connect L298N ENA (PWM) to pin 12.

Pin 13 (BCM27)
- [ ] Connect keypad column C1 to pin 13.

Pin 15 (BCM22)
- [ ] Connect keypad column C3 to pin 15.

Pin 16 (BCM23)
- [ ] Connect L298N IN1 to pin 16.

Pin 18 (BCM24)
- [ ] Connect L298N IN2 to pin 18.

Pin 31 (BCM6)
- [ ] Connect keypad row R4 to pin 31.

Pin 33 (BCM13)
- [ ] Connect keypad row R3 to pin 33.

Pin 35 (BCM19)
- [ ] Connect keypad row R2 to pin 35.

Pin 37 (BCM26)
- [ ] Connect keypad row R1 to pin 37.

Pin 38 (BCM20)
- [ ] Connect keypad column C2 to pin 38.

Ground and power domain checklist:
- [ ] Connect limit switch COM to GND.
- [ ] Connect Raspberry Pi GND to common system GND.
- [ ] Connect L298N GND to common system GND.
- [ ] Connect lock driver GND to common system GND.
- [ ] Connect 12V PSU negative to common system GND.
- [ ] Connect L298N VMOT to 12V PSU positive.
- [ ] Connect lock driver supply to 12V PSU as required by driver module.
- [ ] Connect lock coil through relay/MOSFET path (not directly to Raspberry Pi GPIO).

Motor output checklist:
- [ ] Connect L298N OUT1/OUT2 to carousel motor terminals.
- [ ] Verify motor can rotate both directions under admin control.

LCD power checklist:
- [ ] Connect LCD VCC to Pi 5V.
- [ ] Connect LCD GND to Pi GND.

Pre-power validation checklist:
- [ ] No loose wire strands or short circuits.
- [ ] No GPIO pin connected directly to 12V.
- [ ] Lock coil path includes correct driver channel.
- [ ] If MOSFET lock driver is used, flyback diode orientation is verified.

Power-on and smoke test:
- [ ] Power ON 12V supply.
- [ ] Power ON Raspberry Pi.
- [ ] Run `python main.py`.
- [ ] Confirm LCD prompt appears.
- [ ] Confirm keypad input is detected.
- [ ] Confirm admin carousel jog works.
- [ ] Confirm lockbox ID1 open/close sequence is detected.

## 7) Operating Instructions
### 7.1 Startup
- Run python main.py
- On boot, CSV files are auto-created if missing.

### 7.2 User mode
1. Enter user password and press #.
2. Enter container ID (1-15) and submit #.
3. If selected ID is not physically installed, UI shows NOT INSTALLED and no actuation occurs.
4. Lockbox control is active for ID 1 only.
5. Carousel control is active for ID 10 only.

### 7.3 Admin mode
1. Enter admin password.
2. Menu options:
- 1 Select container (refill + carousel manual control)
- 2 Send inventory email
- 3 Send history email
- 4 Add password
- 5 Delete password
- 6 Modify password
- 9 Exit

Carousel admin control:
- Tap 1 for jog
- Hold 1 for continuous run
- 9 to exit

## 7.4 Expected Runtime Messages
These messages help verify behavior quickly:
- Non-installed ID selected: `NOT INSTALLED`
- Lockbox success path: `LOCKBOX DONE`
- Carousel failure path: `CAROUSEL ERROR`
- Admin control active: `RUN` / `JOG`

### 7.5 End-to-End Operating Script (TA/Grader Friendly)
Use this exact script during demo so operation is unambiguous:

1. Power on 12V supply and Raspberry Pi.
2. Run `python main.py` and wait for LCD prompt `Enter password`.
3. User flow check:
- Enter a valid user password, press `#`.
- Enter container `10`, press `#`.
- Observe one carousel dispense and stock decrement in inventory.csv.
4. Lockbox flow check:
- Enter a valid user password, press `#`.
- Enter container `1`, press `#`.
- Open and close the door once; verify `LOCKBOX DONE` and updated history.csv.
5. Non-installed guard check:
- Enter a valid user password and choose container `2` or `11`.
- Verify `NOT INSTALLED` and confirm no hardware actuation.
6. Admin flow check:
- Enter admin password.
- Press `1` -> select `10` -> tap `1` and hold `1` to verify jog/hold behavior.
- Press `9` to exit control, then `9` to exit admin mode.
7. Stop app with Ctrl+C.

## 8) Design Strategy (Why This Design)
### 8.1 Why limit-switch edge tracking for carousel
- Carousel index is detected using transition events (press/release edges) rather than fixed time only.
- This reduces drift from battery/power/motor variation and mechanical load changes.

### 8.2 Why separate user and admin control profiles
- User mode prioritizes repeatable one-step dispense behavior.
- Admin mode prioritizes manual serviceability (tap jog and hold run).

### 8.3 Why external 12V power domain
- Motor and lock coil current/noise are too large for GPIO power.
- Shared ground with isolated power switching improves reliability.

### 8.4 If not fully working, expected troubleshooting strategy
- Keep algorithm stable, tune constants in small increments.
- Change one variable per test cycle.
- Record each change in TUNING_LOG.md.

### 8.5 Scope-Limited Deployment Strategy
- Software keeps container schema at IDs 1-15 for compatibility and future scaling.
- Runtime actuation is intentionally restricted to physically installed IDs only (lockbox 1, carousel 10).
- This avoids unsafe actuation attempts on unwired outputs while preserving database/report structure.

### 8.6 Why This Architecture Instead of Alternatives
Alternative A: Pure timed carousel rotation without a limit switch
- Rejected because supply/load changes at 12V cause index drift and cumulative alignment error.

Alternative B: Full sensor stack for every container in this phase
- Rejected for this milestone to reduce integration risk and keep validation focused.
- Current design keeps software schema for 1-15 but enables safe actuation only on installed hardware.

Alternative C: Single admin/user motor profile
- Rejected because service tasks need fine manual control while user mode needs repeatable one-step behavior.

Chosen architecture rationale summary:
- Limit-switch indexing improves repeatability.
- Separate user/admin control profiles improve usability and maintenance.
- External 12V power with isolated switching improves electrical safety and robustness.

## 9) Design Verification and Experimental Documentation
Use this exact test matrix to demonstrate design requirements.

### 9.1 Verification matrix

| Test ID | Requirement | Procedure | Pass criteria |
|---|---|---|---|
| V1 | App boots and initializes hardware | Run python main.py | No crash, LCD prompt visible |
| V2 | Password auth works | Test known user/admin and invalid passwords | Correct accept/reject behavior |
| V3 | Carousel index event path works | Trigger user dispense for container 10 repeatedly | Consistent successful cycle without runtime errors |
| V4 | Limit switch logic polarity correct | Manually press/release switch while observing behavior/log | Press seen as LOW, release as HIGH |
| V5 | Lockbox open/close sequence works | Select lockbox ID, open then close door | Access success and inventory update |
| V6 | Data persistence | Perform operations, restart app | CSV state is preserved |
| V7 | Admin manual control | Enter admin mode, tap/hold carousel control | Jog and hold behavior match spec |

### 9.2 Suggested evidence package (for grading)
- Photos of final wiring and enclosure
- Labeled pin map screenshot from this guide
- Short video of user flow (password -> dispense)
- Short video of admin carousel control
- CSV before/after snapshots showing inventory and history updates
- Tuning log entries showing iterative engineering process

### 9.3 Experimental run log template

Date:
Voltage:
Test IDs run:
Observed outcomes:
Failures:
Root cause hypothesis:
Fix attempted:
Retest result:

### 9.4 Quantitative Acceptance Criteria
Use these measurable targets in verification evidence:

| Metric | Acceptance target |
|---|---|
| Boot reliability | 5/5 successful starts without crash |
| User auth correctness | 10/10 correct accept/reject outcomes |
| Carousel indexing repeatability (ID 10) | >= 20 consecutive cycles without fatal error |
| Lockbox cycle correctness (ID 1) | >= 10 cycles with open then close detected |
| Data persistence | inventory.csv and history.csv remain consistent after restart |

If a target is not met, include the failed metric, root cause hypothesis, and next action in the run log.

### 9.5 Requirement-to-Evidence Traceability (What Proves Compliance)

| Requirement claim | Evidence artifact | Acceptance decision rule |
|---|---|---|
| User can authenticate correctly | Demo video + terminal log of valid/invalid attempts | Must match expected accept/reject outcomes exactly |
| Carousel dispenses one index step repeatedly | Continuous run video for >=20 cycles + history.csv/inventory.csv snapshots | No fatal error and stock decreases by one per successful cycle |
| Lockbox sequence is detected correctly | Video showing open then close + history.csv entry timestamps | Open/close events both observed and one completed record written |
| Non-installed IDs are safely blocked | Demo showing IDs 2-9/11-15 return `NOT INSTALLED` | No motor/lock actuation occurs for blocked IDs |
| Data persistence works across restart | Before/after CSV snapshots around app restart | Data values are preserved and remain internally consistent |

### 9.6 Minimum Experimental Package to Submit
To clearly prove the circuit satisfies design requirements, submit all items below together:

1. One wiring photo set (wide + close-up labels).
2. One end-to-end demo video following Section 7.5 in order.
3. One verification table filled for V1-V7 with pass/fail and notes.
4. One run log entry including voltage, failures, fixes, and retest result.
5. inventory.csv and history.csv snapshots captured before and after the demo.

## 10) Troubleshooting Guide
### Symptom A: Carousel does not move
- Check 12V PSU output under load.
- Confirm common ground between PSU, L298N, and Raspberry Pi.
- Verify BCM23/24/18 wiring to IN1/IN2/ENA.
- Increase CAROUSEL_LIMIT_SEARCH_DUTY in small increments.

### Symptom B: Carousel overshoots
- Reduce CAROUSEL_LIMIT_SEARCH_DUTY and CAROUSEL_LIMIT_APPROACH_DUTY.
- Increase settle checks slightly.
- Verify limit switch mechanical mounting and trigger geometry.

### Symptom C: Stops at wrong alignment
- Verify switch released state is HIGH.
- Tune release nudge duty/timeout.
- Confirm switch actuator fully disengages at desired pickup position.

### Symptom D: Lockbox does not trigger
- Verify lock channel uses relay/MOSFET path, not direct GPIO coil drive.
- Confirm detect wiring polarity against closed=LOW, open=HIGH assumption.
- Check lock pulse width and driver channel operation.

### Symptom E: Motor works, lockbox breaks (or vice versa)
- Check pin conflicts in LOCKBOX_CONFIG against motor pins.
- Remap lockbox GPIO to non-conflicting BCM pins and retest.

### Symptom F: Selecting IDs 2-9 or 11-15 does nothing
- This is expected in current deployment: only IDs 1 and 10 are installed.
- Runtime intentionally blocks actuation for non-installed IDs.

## 11) Reproducibility Checklist
Before declaring final reproduction complete:
- BOM acquired and documented
- Wiring matches Section 5 exactly
- Software environment installed and app starts cleanly
- V1 to V7 verification matrix passed and recorded
- Tuning log updated with final stable settings

## 12) Code Comment and Traceability Checklist
This project is graded from a software-integration perspective. Use this checklist to document comment quality and traceability:

1. Confirm each hardware module file includes purpose-level comments:
- `motor_controller.py`
- `lockbox_controller.py`
- `matrix_keypad.py`
- `vending_app.py`

2. Confirm all tuning constants are centralized and named in `config_vm.py`.

3. Confirm behavior comments exist around non-trivial control logic:
- Carousel press/release edge handling
- Overshoot correction behavior
- Lockbox open/close detection flow

4. For each submission, include the commit hash and the exact `config_vm.py` values used during verification.

This completes a reproducible software+hardware integration package for this codebase.
