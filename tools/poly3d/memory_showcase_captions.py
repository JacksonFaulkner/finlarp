#!/usr/bin/env python3
"""Burn the timed narration guide into the rendered frame sequence."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "artifacts/memory-model-showcase/frames"
OUT = ROOT / "artifacts/memory-model-showcase/captioned"
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT = ImageFont.truetype(FONT_PATH, 32)
STEP_FONT = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 28)
BEATS = (
    (0.0, 2.0, "DRAM CELL · ONE BIT", "A DRAM cell stores one bit."),
    (2.0, 4.0, "STEP 01 · STORE CHARGE", "First, the capacitor stores charge."),
    (4.0, 6.0, "STEP 02 · OPEN THE CELL", "The word line turns on the access transistor."),
    (6.0, 8.0, "STEP 03 · READ THE CHARGE", "Charge flows to the bit line; the chip senses a one."),
    (8.0, 10.0, "STEP 04 · RESTORE", "The sense amp restores it, ready for the next read."),
)

OUT.mkdir(parents=True, exist_ok=True)
for index, path in enumerate(sorted(FRAMES.glob("*.png"))):
    t = index / 30
    label, caption = next((label, caption) for start, end, label, caption in BEATS if start <= t < end)
    with Image.open(path) as source:
        image = source.convert("RGBA")
    w, h = image.size
    draw = ImageDraw.Draw(image, "RGBA")

    # Keep the current lesson step in a fixed, quiet header while the model holds.
    header_box = draw.textbbox((0, 0), label, font=STEP_FONT)
    header_w = header_box[2] - header_box[0]
    header_h = header_box[3] - header_box[1]
    hx, hy = w - header_w - 58, 46
    draw.rounded_rectangle(
        (hx - 16, hy - 10, hx + header_w + 42, hy + header_h + 15),
        radius=8,
        fill=(25, 27, 38, 215),
        outline=(83, 188, 208, 190),
        width=2,
    )
    draw.text((hx, hy), label, font=STEP_FONT, fill=(106, 216, 231, 255))

    box = draw.textbbox((0, 0), caption, font=FONT, stroke_width=0)
    text_w = box[2] - box[0]
    text_h = box[3] - box[1]
    pad_x, pad_y = 34, 18
    x = (w - text_w) // 2
    y = h - 105
    draw.rounded_rectangle(
        (x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y),
        radius=10,
        fill=(25, 27, 38, 220),
        outline=(100, 160, 175, 150),
        width=2,
    )
    draw.text((x, y), caption, font=FONT, fill=(232, 232, 229, 255))
    image.convert("RGB").save(OUT / path.name, quality=95)
