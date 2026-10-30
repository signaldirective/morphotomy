#!/usr/bin/env python3
"""Assets for the MORPHOTOMY Plymouth theme.

Plymouth's script module has no drawing primitives beyond images and simple
scaling, so everything is pre-rendered here: the wordmark, the seam that grows
with boot progress, the stitches that appear along it, and the unit label.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "plymouth" / "morphotomy"

DISPLAY = "/home/ro/.local/share/fonts/DepartureMonoNerdFont-Regular.otf"
BODY = "/home/ro/.local/share/fonts/IosevkaNerdFontMono-Regular.ttf"

BONE = (211, 199, 190, 255)
MUTED = (106, 89, 85, 255)
ARTERIAL = (255, 46, 61, 255)

SEAM_W = 900
STITCHES = 14


def tracked(draw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x


def text_width(text, font, tracking=0.0):
    return sum(font.getlength(c) + tracking for c in text) - tracking


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- lockup, cropped then pre-scaled for a fast initramfs load
    logo = Image.open(ROOT / "unlock.png").convert("RGBA")
    # unlock.png carries a terminal-ID line under the lockup for SDDM; the
    # splash supplies its own seam and label, so cut at the first clear row.
    alpha = logo.getchannel("A")
    rows = [alpha.crop((0, y, logo.width, y + 1)).getbbox() is not None
            for y in range(logo.height)]
    start = rows.index(True)
    cut = logo.height
    for y in range(start, logo.height):
        if not rows[y]:
            cut = y
            break
    logo = logo.crop((0, 0, logo.width, max(cut, 1)))
    logo = logo.crop(logo.getbbox())
    logo.thumbnail((820, 400), Image.LANCZOS)
    logo.save(OUT / "logo.png")

    # ---- the seam: a thin arterial line with a hot core and soft glow
    seam = Image.new("RGBA", (SEAM_W, 15), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seam)
    sd.line([(0, 7), (SEAM_W, 7)], fill=(120, 24, 30, 255), width=3)
    sd.line([(0, 7), (SEAM_W, 7)], fill=ARTERIAL, width=1)
    glow = seam.filter(ImageFilter.GaussianBlur(4))
    seam = Image.alpha_composite(Image.new("RGBA", seam.size, (0, 0, 0, 0)), glow)
    seam.alpha_composite(glow)
    sd = ImageDraw.Draw(seam)
    sd.line([(0, 7), (SEAM_W, 7)], fill=(255, 120, 130, 255), width=1)
    seam.save(OUT / "seam.png")

    # ---- stitch ticks
    for i, hot in enumerate([False] * STITCHES):
        tick = Image.new("RGBA", (18, 40), (0, 0, 0, 0))
        td = ImageDraw.Draw(tick)
        td.line([(3, 2), (15, 38)], fill=ARTERIAL if hot else BONE, width=4)
        if hot:
            tick = tick.filter(ImageFilter.GaussianBlur(1))
        tick.save(OUT / "stitch.png")
        break  # one bone tick, reused; the hot one is separate

    hot = Image.new("RGBA", (20, 42), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hot)
    hd.line([(3, 2), (17, 40)], fill=ARTERIAL, width=4)
    hot = hot.filter(ImageFilter.GaussianBlur(1))
    hot.save(OUT / "stitch_hot.png")

    # ---- unit label under the seam
    small = ImageFont.truetype(BODY, 20)
    label_text = "BAY 09  ·  GRAFT 0084  ·  INTEGRITY 61%"
    w = int(text_width(label_text, small, 3)) + 8
    label = Image.new("RGBA", (w, 30), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(label), (0, 4), label_text, small, MUTED, 3)
    label.save(OUT / "label.png")

    print("plymouth assets:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
