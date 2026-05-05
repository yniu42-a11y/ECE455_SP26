#!/usr/bin/env python3
"""Generate a PDF schematic for the current ECE455 hardware wiring."""

from pathlib import Path

import config_vm as config
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
OUTPUT_PDF = ROOT / "ECE455_current_wiring_schematic.pdf"


def draw_box(c, x, y, w, h, title, body_lines, fill=colors.whitesmoke, stroke=colors.black):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, 10, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 10, y + h - 18, title)
    c.setFont("Helvetica", 9.5)
    text = c.beginText(x + 10, y + h - 34)
    text.setLeading(12)
    for line in body_lines:
        text.textLine(line)
    c.drawText(text)


def draw_label(c, x, y, text, size=8.5, angle=0, color=colors.black):
    c.saveState()
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    c.translate(x, y)
    if angle:
        c.rotate(angle)
    c.drawString(0, 0, text)
    c.restoreState()


def line(c, x1, y1, x2, y2, width=1.2, color=colors.black):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    c.restoreState()


def dot(c, x, y, r=2.5, color=colors.black):
    c.saveState()
    c.setFillColor(color)
    c.circle(x, y, r, fill=1, stroke=0)
    c.restoreState()


def make_page_one(c):
    width, height = landscape(letter)
    margin = 0.45 * inch

    c.setTitle("ECE455 Current Wiring Schematic")
    c.setAuthor("GitHub Copilot")
    c.setSubject("Current Raspberry Pi vending machine wiring")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height - 0.45 * inch, "ECE455 Current Wiring Schematic")
    c.setFont("Helvetica", 9.5)
    c.drawString(margin, height - 0.62 * inch, "Based on the current connected devices in /home/pi/ECE455")
    c.drawString(margin, height - 0.76 * inch, "Active physical devices: lockbox ID 1 and carousel ID 10")

    pi_x, pi_y, pi_w, pi_h = 4.05 * inch, 3.05 * inch, 2.65 * inch, 1.9 * inch
    keypad_x, keypad_y = 0.55 * inch, 3.0 * inch
    lcd_x, lcd_y = 8.05 * inch, 4.0 * inch
    motor_x, motor_y = 0.55 * inch, 0.65 * inch
    switch_x, switch_y = 4.1 * inch, 0.8 * inch
    lock_x, lock_y = 8.0 * inch, 0.75 * inch
    power_x, power_y = 4.1 * inch, 0.45 * inch

    draw_box(
        c,
        pi_x,
        pi_y,
        pi_w,
        pi_h,
        "Raspberry Pi",
        [
            "BCM GPIO mode",
            "Runs main.py / vending_app.py",
            "Common ground with 12V system",
            "I2C bus 1 for LCD",
        ],
        fill=colors.lightblue,
    )

    draw_box(
        c,
        keypad_x,
        keypad_y,
        2.6 * inch,
        1.7 * inch,
        "3x4 Matrix Keypad",
        [
            "Rows: R1=GPIO26, R2=GPIO19, R3=GPIO13, R4=GPIO6",
            "Cols: C1=GPIO27, C2=GPIO20, C3=GPIO22",
            "Used for password and admin input",
        ],
        fill=colors.lavender,
    )

    draw_box(
        c,
        lcd_x,
        lcd_y,
        2.7 * inch,
        1.55 * inch,
        "16x2 I2C LCD",
        [
            "SDA = GPIO2 / physical pin 3",
            "SCL = GPIO3 / physical pin 5",
            "Address = 0x27",
            "VCC to Pi 5V, GND to Pi GND",
        ],
        fill=colors.beige,
    )

    draw_box(
        c,
        motor_x,
        motor_y,
        3.0 * inch,
        1.7 * inch,
        "L298N Motor Driver + Carousel Motor",
        [
            f"IN1 = GPIO{config.MOTOR_IN1_PIN}",
            f"IN2 = GPIO{config.MOTOR_IN2_PIN}",
            f"ENA = GPIO{config.MOTOR_ENA_PIN} (PWM)",
            "VMOT = 12V supply, GND common",
            "OUT1/OUT2 to carousel DC motor",
        ],
        fill=colors.honeydew,
    )

    draw_box(
        c,
        switch_x,
        switch_y,
        2.55 * inch,
        1.15 * inch,
        "Carousel Limit Switch",
        [
            "Container 10 feedback",
            "COM -> GND",
            f"NO -> GPIO{config.CAROUSEL_LIMIT_SWITCH_PINS['10']}",
            "Pressed = LOW, released = HIGH",
        ],
        fill=colors.mistyrose,
    )

    draw_box(
        c,
        lock_x,
        lock_y,
        2.85 * inch,
        1.75 * inch,
        "Lock Driver + Lockbox ID 1",
        [
            f"Lock control = GPIO{config.LOCKBOX_CONFIG['1']['lock_pin']}",
            f"Detect input = GPIO{config.LOCKBOX_CONFIG['1']['detect_pin']}",
            "Lock coil powered from 12V through driver",
            "Detect switch closed = LOW, open = HIGH",
        ],
        fill=colors.aliceblue,
    )

    draw_box(
        c,
        power_x,
        power_y,
        2.6 * inch,
        0.7 * inch,
        "12V Supply / Common Ground",
        ["12V -> motor driver and lock driver", "0V -> Raspberry Pi GND, L298N GND, lock driver GND"],
        fill=colors.lightgrey,
    )

    # Main wiring lines
    line(c, keypad_x + 2.6 * inch, keypad_y + 0.9 * inch, pi_x, pi_y + 1.2 * inch, color=colors.darkviolet)
    line(c, lcd_x, lcd_y + 0.75 * inch, pi_x + pi_w, pi_y + 1.3 * inch, color=colors.darkgoldenrod)
    line(c, motor_x + 3.0 * inch, motor_y + 1.1 * inch, pi_x, pi_y + 0.65 * inch, color=colors.darkgreen)
    line(c, switch_x + 1.3 * inch, switch_y + 1.15 * inch, pi_x + pi_w / 2, pi_y, color=colors.firebrick)
    line(c, lock_x, lock_y + 1.0 * inch, pi_x + pi_w, pi_y + 0.95 * inch, color=colors.navy)
    line(c, power_x + 1.3 * inch, power_y + 0.7 * inch, motor_x + 1.5 * inch, motor_y + 1.7 * inch, color=colors.black)
    line(c, power_x + 1.5 * inch, power_y + 0.7 * inch, lock_x + 1.2 * inch, lock_y + 1.75 * inch, color=colors.black)
    line(c, power_x + 2.15 * inch, power_y + 0.7 * inch, pi_x + 1.0 * inch, pi_y, color=colors.black)

    # Connection labels
    draw_label(c, 2.8 * inch, 4.45 * inch, "GPIO26/19/13/6 rows", 8.2, color=colors.darkviolet)
    draw_label(c, 6.7 * inch, 4.6 * inch, "GPIO27/20/22 columns", 8.2, color=colors.darkviolet)
    draw_label(c, 7.15 * inch, 5.0 * inch, "GPIO2/3 + 5V + GND", 8.2, color=colors.darkgoldenrod)
    draw_label(c, 2.1 * inch, 1.55 * inch, "GPIO23 / 24 / 18", 8.2, color=colors.darkgreen)
    draw_label(c, 4.55 * inch, 1.9 * inch, "GPIO17", 8.2, color=colors.firebrick)
    draw_label(c, 8.8 * inch, 1.95 * inch, "GPIO4 / GPIO14", 8.2, color=colors.navy)
    draw_label(c, 4.75 * inch, 0.95 * inch, "12V + common ground", 8.2, color=colors.black)

    # Junction dots at Pi side
    for px, py in [
        (pi_x, pi_y + 1.2 * inch),
        (pi_x + pi_w, pi_y + 1.3 * inch),
        (pi_x, pi_y + 0.65 * inch),
        (pi_x + pi_w / 2, pi_y),
        (pi_x + pi_w, pi_y + 0.95 * inch),
    ]:
        dot(c, px, py)

    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(margin, 0.28 * inch, "Note: only lockbox ID 1 and carousel ID 10 are currently installed/controlled in this build.")


def make_page_two(c):
    width, height = landscape(letter)
    margin = 0.45 * inch

    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - 0.45 * inch, "Connection Table and Build Notes")

    c.setFont("Helvetica", 9.5)
    lines = [
        ["Device", "Signal / Wire", "BCM", "Physical Pin", "Destination / Notes"],
        ["Keypad", "R1", "26", "37", "Matrix keypad row 1"],
        ["Keypad", "R2", "19", "35", "Matrix keypad row 2"],
        ["Keypad", "R3", "13", "33", "Matrix keypad row 3"],
        ["Keypad", "R4", "6", "31", "Matrix keypad row 4"],
        ["Keypad", "C1", "27", "13", "Matrix keypad column 1"],
        ["Keypad", "C2", "20", "38", "Matrix keypad column 2"],
        ["Keypad", "C3", "22", "15", "Matrix keypad column 3"],
        ["LCD", "SDA", "2", "3", "I2C bus 1"],
        ["LCD", "SCL", "3", "5", "I2C bus 1"],
        ["LCD", "VCC", "5V", "2/4", "Pi 5V rail"],
        ["LCD", "GND", "GND", "6/9/14/etc.", "Pi ground"],
        ["Motor driver", "IN1", str(config.MOTOR_IN1_PIN), "16", "L298N input"],
        ["Motor driver", "IN2", str(config.MOTOR_IN2_PIN), "18", "L298N input"],
        ["Motor driver", "ENA", str(config.MOTOR_ENA_PIN), "12", "L298N PWM enable"],
        ["Motor driver", "VMOT", "12V", "--", "External 12V supply"],
        ["Limit switch", "NO", "17", "11", "Carousel container 10 input, pull-up enabled"],
        ["Limit switch", "COM", "GND", "--", "Switch common to ground"],
        ["Lockbox 1", "Lock control", str(config.LOCKBOX_CONFIG['1']['lock_pin']), "7", "Driver input to 12V lock path"],
        ["Lockbox 1", "Detect", str(config.LOCKBOX_CONFIG['1']['detect_pin']), "8", "Closed=LOW, open=HIGH"],
        ["System", "Common ground", "--", "--", "Pi, L298N, and lock driver ground tied together"],
    ]

    x0, y0 = margin, height - 0.95 * inch
    col_widths = [1.45 * inch, 1.2 * inch, 0.8 * inch, 1.0 * inch, 3.3 * inch]
    row_h = 0.28 * inch

    # Header
    y = y0
    c.setFillColor(colors.lightgrey)
    c.rect(x0, y - row_h, sum(col_widths), row_h, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9.2)
    x = x0
    for idx, head in enumerate(lines[0]):
        c.drawString(x + 4, y - 0.18 * inch, head)
        x += col_widths[idx]

    # Body
    c.setFont("Helvetica", 8.5)
    y -= row_h
    for row in lines[1:]:
        y -= row_h
        c.rect(x0, y, sum(col_widths), row_h, fill=0, stroke=1)
        x = x0
        for idx, cell in enumerate(row):
            c.drawString(x + 4, y + 0.08 * inch, cell)
            x += col_widths[idx]

    notes_y = y - 0.45 * inch
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(margin, notes_y, "Build notes")
    c.setFont("Helvetica", 9)
    notes = [
        "1. Keep all GPIO wiring as signal-level only; do not power motors or locks from Pi GPIO.",
        "2. Use a shared ground between the Pi, L298N, and lock driver.",
        "3. The project currently controls only lockbox ID 1 and carousel ID 10.",
        "4. If the wiring changes, update config_vm.py and regenerate this PDF.",
    ]
    ty = notes_y - 0.18 * inch
    for note in notes:
        c.drawString(margin, ty, note)
        ty -= 0.22 * inch


def main():
    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=landscape(letter))
    make_page_one(c)
    make_page_two(c)
    c.save()
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()