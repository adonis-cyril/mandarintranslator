#!/usr/bin/env python3
"""Generate a custom macOS app icon for Zhumu."""

from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "icon"
SOURCE_PNG = ASSETS_DIR / "zhumu-icon.png"
ICONSET_DIR = ASSETS_DIR / "Zhumu.iconset"
ICNS_PATH = ASSETS_DIR / "Zhumu.icns"
CANVAS = 1024


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def gradient_background() -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS))
    pixels = image.load()

    top_left = (25, 30, 40)
    top_right = (50, 26, 34)
    bottom_left = (15, 91, 106)
    bottom_right = (118, 41, 57)

    for y in range(CANVAS):
        ty = y / (CANVAS - 1)
        left = tuple(lerp(top_left[i], bottom_left[i], ty) for i in range(3))
        right = tuple(lerp(top_right[i], bottom_right[i], ty) for i in range(3))
        for x in range(CANVAS):
            tx = x / (CANVAS - 1)
            rgb = tuple(lerp(left[i], right[i], tx) for i in range(3))
            pixels[x, y] = (*rgb, 255)

    return image


def add_transcript_cards(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    cards = [
        ((170, 190, 425, 835), (247, 240, 233, 74)),
        ((599, 190, 854, 835), (235, 244, 245, 74)),
    ]

    for bounds, fill in cards:
        draw.rounded_rectangle(bounds, radius=76, fill=fill, outline=(255, 255, 255, 36), width=4)
        left, top, right, _ = bounds
        for idx in range(5):
            y = top + 92 + idx * 98
            width = 145 if idx % 2 == 0 else 165
            x1 = left + 40
            x2 = min(right - 40, x1 + width)
            draw.rounded_rectangle((x1, y, x2, y + 22), radius=11, fill=(255, 255, 255, 112))


def add_eye_mark(base: Image.Image) -> None:
    shadow = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow, "RGBA")
    eye_bounds = (230, 352, 794, 686)
    shadow_draw.ellipse(eye_bounds, fill=(0, 0, 0, 135))
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    base.alpha_composite(shadow)

    draw = ImageDraw.Draw(base, "RGBA")
    eye_fill = (251, 245, 236, 255)
    eye_outline = (255, 255, 255, 110)
    draw.polygon(
        [
            (240, 519),
            (355, 410),
            (512, 360),
            (670, 410),
            (784, 519),
            (670, 628),
            (512, 678),
            (355, 628),
        ],
        fill=eye_fill,
    )
    draw.line(
        [(274, 519), (358, 438), (512, 392), (666, 438), (750, 519)],
        fill=eye_outline,
        width=10,
        joint="curve",
    )
    draw.line(
        [(274, 519), (358, 600), (512, 646), (666, 600), (750, 519)],
        fill=(227, 216, 205, 210),
        width=10,
        joint="curve",
    )

    iris_bounds = (376, 382, 648, 654)
    draw.ellipse(iris_bounds, fill=(14, 122, 137, 255))
    draw.ellipse((414, 420, 610, 616), fill=(28, 177, 176, 175))
    draw.ellipse((452, 458, 572, 578), fill=(32, 44, 56, 250))
    draw.ellipse((510, 478, 548, 516), fill=(255, 247, 226, 210))
    draw.ellipse((438, 432, 500, 494), fill=(255, 255, 255, 115))


def add_spark(base: Image.Image) -> None:
    draw = ImageDraw.Draw(base, "RGBA")
    center_x, center_y = 736, 314
    outer = 52
    inner = 18
    points: list[tuple[float, float]] = []
    for i in range(8):
        angle = math.radians(-90 + i * 45)
        radius = outer if i % 2 == 0 else inner
        points.append((center_x + math.cos(angle) * radius, center_y + math.sin(angle) * radius))
    draw.polygon(points, fill=(255, 209, 102, 235))


def build_base_icon() -> Image.Image:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    background = gradient_background()
    rounded = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    mask = Image.new("L", (CANVAS, CANVAS), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, CANVAS, CANVAS), radius=228, fill=255)
    rounded.paste(background, (0, 0), mask)

    glow = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse((110, 54, 884, 700), fill=(255, 255, 255, 22))
    rounded.alpha_composite(glow.filter(ImageFilter.GaussianBlur(48)))

    add_transcript_cards(rounded)
    add_eye_mark(rounded)
    add_spark(rounded)

    border = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(border, "RGBA").rounded_rectangle(
        (12, 12, CANVAS - 12, CANVAS - 12),
        radius=220,
        outline=(255, 255, 255, 36),
        width=10,
    )
    rounded.alpha_composite(border)
    return rounded


def export_iconset(source: Path) -> None:
    if ICONSET_DIR.exists():
        shutil.rmtree(ICONSET_DIR)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }

    for filename, size in sizes.items():
        subprocess.run(
            ["sips", "-z", str(size), str(size), str(source), "--out", str(ICONSET_DIR / filename)],
            check=True,
            capture_output=True,
        )

    subprocess.run(["iconutil", "-c", "icns", str(ICONSET_DIR), "-o", str(ICNS_PATH)], check=True)
    shutil.rmtree(ICONSET_DIR)


def main() -> None:
    icon = build_base_icon()
    icon.save(SOURCE_PNG, format="PNG")
    export_iconset(SOURCE_PNG)
    print(f"Generated {SOURCE_PNG}")
    print(f"Generated {ICNS_PATH}")


if __name__ == "__main__":
    main()
