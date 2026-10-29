#!/usr/bin/env python3
"""Render the MORPHOTOMY wordmark: bone lettering, suture seam, clinical subtitle.

Output: unlock.png (transparent) used by Plymouth, SDDM and the lock screen.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "unlock.png"

DISPLAY = "/home/ro/.local/share/fonts/DepartureMonoNerdFont-Regular.otf"
BODY = "/home/ro/.local/share/fonts/IosevkaNerdFontMono-Regular.ttf"

BONE = (211, 199, 190, 255)
MUTED = (106, 89, 85, 255)
ARTERIAL = (255, 46, 61, 255)

W, H = 1400, 620
random.seed(84)


def tracked(draw, xy, text, font, fill, tracking=0.0):
    """Draw text with letter spacing; returns the end x position."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x


def main():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    big = ImageFont.truetype(DISPLAY, 128)
    small = ImageFont.truetype(BODY, 30)
    tiny = ImageFont.truetype(BODY, 22)

    word = "MORPHOTOMY"
    tracking = 10
    width = sum(big.getlength(c) + tracking for c in word) - tracking
    x0 = (W - width) / 2
    y0 = 210

    # Faint arterial bloom behind the mark.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse(
        [x0 + width * 0.30, y0 - 30, x0 + width * 0.78, y0 + 190],
        fill=(255, 46, 61, 60),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img.alpha_composite(glow)

    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    end = tracked(draw, (x0, y0), word, big, BONE, tracking)

    # Subtle bone wear: a few darker flecks along the letters.
    for _ in range(240):
        px = random.uniform(x0, end)
        py = random.uniform(y0 + 10, y0 + 130)
        draw.point((px, py), fill=(120, 104, 100, random.randint(20, 70)))

    img.alpha_composite(text_layer)

    draw = ImageDraw.Draw(img)

    # The seam: a taut suture line under the word, seven stitches, one skewed.
    seam_y = y0 + 168
    seam_x0 = x0 - 40
    seam_x1 = end + 40
    draw.line([(seam_x0, seam_y), (seam_x1, seam_y)], fill=(120, 30, 36, 220), width=3)
    stitches = 7
    for i in range(stitches):
        t = i / (stitches - 1)
        sx = seam_x0 + t * (seam_x1 - seam_x0)
        skew = 7 if i == 4 else 0
        draw.line(
            [(sx - 9, seam_y - 15 - skew), (sx + 9, seam_y + 15 - skew)],
            fill=ARTERIAL if i == 4 else BONE,
            width=4,
        )

    # A single stitch crossing the first O, as if the mark were sewn on.
    o_x = x0 + big.getlength("M") + tracking + big.getlength("O") * 0.5
    for k in range(3):
        yy = y0 + 34 + k * 26
        draw.line([(o_x - 26, yy), (o_x + 26, yy + 10)], fill=(140, 36, 42, 200), width=2)

    sub = "GRAFT 0084  ·  MORPHOTOMY UNIT  ·  INTEGRITY 61%"
    sub_w = sum(small.getlength(c) + 3 for c in sub)
    tracked(draw, ((W - sub_w) / 2, seam_y + 44), sub, small, MUTED, 3)

    note = "consent status: disputed"
    note_w = sum(tiny.getlength(c) + 2 for c in note)
    tracked(draw, ((W - note_w) / 2, seam_y + 92), note, tiny, (150, 46, 52, 210), 2)

    # Grain and a faint scanline weave so it sits on the splash naturally.
    noise = Image.effect_noise((W, H), 18).convert("L")
    grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (W, H), 14)))
    img.alpha_composite(grain)

    scan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(scan)
    for y in range(0, H, 3):
        sdraw.line([(0, y), (W, y)], fill=(0, 0, 0, 18))
    img.alpha_composite(scan)

    img.save(OUT)
    print("wrote", OUT, img.size)


if __name__ == "__main__":
    main()
