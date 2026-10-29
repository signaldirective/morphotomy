#!/usr/bin/env python3
"""Composite SPECIMEN 84 into the finished wallpaper.

Takes the transparent Blender render and builds the clinical document around
it: dark graded field, faint grid, registration marks, measurement ruler,
specimen labels, ECG trace, bloom, scanlines and grain.

Usage: compose-specimen.py <render.png> <out.webp> [--size WxH]
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

DISPLAY = "/home/ro/.local/share/fonts/DepartureMonoNerdFont-Regular.otf"
BODY = "/home/ro/.local/share/fonts/IosevkaNerdFontMono-Regular.ttf"

BONE = (211, 199, 190)
MUTED = (106, 89, 85)
DIM = (74, 58, 58)
ARTERIAL = (255, 46, 61)
BG = (8, 5, 6)

random.seed(84)


def tracked(draw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x


def text_width(text, font, tracking=0.0):
    return sum(font.getlength(c) + tracking for c in text) - tracking


def grade(size):
    """Deep, uneven black field with a cold rust bloom bottom-right."""
    w, h = size
    base = Image.new("RGB", size, BG)
    glow = Image.new("RGB", size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(26):
        t = i / 25
        radius = int(max(w, h) * (0.55 - 0.4 * t))
        alpha = int(10 + 22 * (1 - t))
        cx, cy = int(w * 0.72), int(h * 0.78)
        gd.ellipse(
            [cx - radius, cy - int(radius * 0.62), cx + radius, cy + int(radius * 0.62)],
            fill=(alpha * 5, alpha, alpha // 2),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(180))
    return ImageChops.add(base, glow)


def main():
    render_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    size = (2560, 1440)
    if "--size" in sys.argv:
        w, h = sys.argv[sys.argv.index("--size") + 1].lower().split("x")
        size = (int(w), int(h))
    w, h = size

    scene = grade(size)

    # ---- specimen, right of centre, sitting in a haze
    specimen = Image.open(render_path).convert("RGBA").resize((w, h), Image.LANCZOS)
    sx, sy = 0, 0

    # feathered haze: blur, then cut the alpha into a soft ellipse so the
    # paste leaves no rectangular edge
    haze = specimen.filter(ImageFilter.GaussianBlur(80))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse(
        [w * 0.42, -h * 0.15, w * 1.35, h * 1.15], fill=255
    )
    mask = mask.filter(ImageFilter.GaussianBlur(180))
    haze.putalpha(ImageChops.multiply(haze.getchannel("A"), mask).point(lambda v: v * 0.35))
    scene.paste(haze, (sx, sy), haze)
    scene.paste(specimen, (sx, sy), specimen)

    # bloom around the hottest rim
    bloom_src = specimen.copy()
    px = bloom_src.load()
    for y in range(0, bloom_src.height, 2):
        for x in range(0, bloom_src.width, 2):
            r, g, b, a = px[x, y]
            lum = (r * 0.5 + g * 0.3 + b * 0.2) * (a / 255)
            px[x, y] = (r, g, b, int(min(255, lum * 1.5)))
    bloom = bloom_src.filter(ImageFilter.GaussianBlur(38))
    bloom_layer = Image.new("RGB", scene.size, (0, 0, 0))
    bloom_layer.paste(bloom, (sx, sy), bloom)
    scene = ImageChops.screen(scene, bloom_layer)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # ---- grid
    step = 64
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(120, 40, 44, 12))
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(120, 40, 44, 12))

    # ---- registration marks
    m = 46
    for cx, cy, dx, dy in [
        (m, m, 1, 1),
        (w - m, m, -1, 1),
        (m, h - m, 1, -1),
        (w - m, h - m, -1, -1),
    ]:
        draw.line([(cx, cy), (cx + 34 * dx, cy)], fill=(150, 60, 64, 120), width=2)
        draw.line([(cx, cy), (cx, cy + 34 * dy)], fill=(150, 60, 64, 120), width=2)

    # ---- left measurement ruler
    ruler_x = 84
    draw.line([(ruler_x, 200), (ruler_x, h - 240)], fill=(90, 40, 44, 140), width=1)
    for i in range(0, 41):
        y = 200 + i * (h - 440) / 40
        long = i % 5 == 0
        draw.line(
            [(ruler_x - (18 if long else 8), y), (ruler_x, y)],
            fill=(120, 50, 54, 160 if long else 90),
            width=2 if long else 1,
        )

    # ---- typography
    label_font = ImageFont.truetype(DISPLAY, 58)
    mid_font = ImageFont.truetype(BODY, 26)
    small_font = ImageFont.truetype(BODY, 21)
    tiny_font = ImageFont.truetype(BODY, 18)

    tracked(draw, (128, 128), "SPECIMEN 84", label_font, BONE, 6)
    draw.line([(128, 206), (128 + 300, 206)], fill=(*ARTERIAL, 200), width=2)

    rows = [
        ("GRAFT CLASS", "IV / SUSPENDED"),
        ("ORIGIN", "MORPHOTOMY UNIT 09"),
        ("CONSENT", "DISPUTED"),
        ("INTEGRITY", "61%"),
        ("PERFUSION", "NOMINAL"),
    ]
    y = 240
    for key, value in rows:
        tracked(draw, (128, y), key, tiny_font, (150, 130, 124), 2)
        tracked(draw, (330, y), value, small_font, BONE if key != "CONSENT" else ARTERIAL, 1)
        y += 36

    # ---- ECG trace along the bottom
    base_y = h - 150
    points = []
    x = 120
    phase = 0.0
    while x < w - 120:
        t = phase
        v = math.sin(t * 1.5) * 4
        beat = t % 3.4
        if beat < 0.12:
            v -= 26 * math.sin(beat / 0.12 * math.pi)
        elif 0.2 < beat < 0.26:
            v += 8
        elif 0.26 < beat < 0.32:
            v -= 6
        points.append((x, base_y + v))
        x += 3
        phase += 0.02
    draw.line(points, fill=(*ARTERIAL, 235), width=2, joint="curve")
    glow_trace = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(glow_trace).line(points, fill=(*ARTERIAL, 90), width=6, joint="curve")
    overlay.alpha_composite(glow_trace.filter(ImageFilter.GaussianBlur(5)))
    draw = ImageDraw.Draw(overlay)
    draw.line(points, fill=(*ARTERIAL, 235), width=2, joint="curve")
    tracked(draw, (120, base_y + 34), "CARDIAC SYNC · 62 BPM · LEAD II", tiny_font, (150, 130, 124), 2)

    # ---- caption bottom right
    cap = "GRAFTED UNDER PROTEST"
    cw = text_width(cap, small_font, 4)
    tracked(draw, (w - 120 - cw, h - 96), cap, small_font, (170, 62, 68), 4)

    # ---- callouts: point at the graft, label on the quiet side
    callout_font = ImageFont.truetype(BODY, 24)

    def callout(text, anchor, label_pos):
        ax, ay = anchor
        lx, ly = label_pos
        mid = (lx + text_width(text, callout_font, 2) + 26, ly + 12)
        draw.line([(ax, ay), mid], fill=(214, 96, 102, 200), width=2)
        draw.line([(ax - 7, ay - 7), (ax + 7, ay + 7)], fill=(235, 210, 200, 210), width=2)
        draw.line([(ax - 7, ay + 7), (ax + 7, ay - 7)], fill=(235, 210, 200, 210), width=2)
        tracked(draw, (lx, ly), text, callout_font, (208, 184, 176), 2)

    callout("SUTURE BANK C · 14 LOADED", (1618, 612), (1310, 596))
    callout("GRAFT INTERFACE 04 · ACTIVE", (1810, 900), (1360, 906))
    callout("PERFUSION LINE · NOMINAL", (1520, 1042), (1290, 1072))

    # ---- timestamp, scale and barcode
    tracked(draw, (120, h - 246), "2026-03-14  04:12:07  ·  SLOT 84  ·  UNIT 09", tiny_font, (150, 130, 124), 2)

    scale_x, scale_y = 620, h - 168
    draw.line([(scale_x, scale_y), (scale_x + 220, scale_y)], fill=(190, 150, 145, 190), width=2)
    for dx in (0, 55, 110, 165, 220):
        draw.line([(scale_x + dx, scale_y - 7), (scale_x + dx, scale_y + 7)], fill=(190, 150, 145, 190), width=2)
    tracked(draw, (scale_x, scale_y + 16), "10 CM", tiny_font, (150, 130, 124), 2)

    bar_x, bar_y, bars = w - 470, h - 250, 46
    random.seed(84)
    x = bar_x
    for i in range(bars):
        width = random.choice([2, 2, 3, 5, 7])
        if i % 2 == 0:
            draw.rectangle([x, bar_y, x + width, bar_y + 46], fill=(200, 186, 178, 210))
        x += width + random.choice([2, 3, 4])
    tracked(draw, (bar_x, bar_y + 56), "0084-AC-61", tiny_font, (150, 130, 124), 3)

    scene = Image.alpha_composite(scene.convert("RGBA"), overlay).convert("RGB")

    # ---- vignette
    vig = Image.new("L", size, 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-w * 0.25, -h * 0.35, w * 1.25, h * 1.35], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    black = Image.new("RGB", size, (0, 0, 0))
    scene = Image.composite(scene, black, vig)

    # ---- scanlines + grain
    scan = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for y in range(0, h, 3):
        sd.line([(0, y), (w, y)], fill=(0, 0, 0, 16))
    scene = Image.alpha_composite(scene.convert("RGBA"), scan)

    noise = Image.effect_noise(size, 16).convert("L")
    grain = Image.merge("RGBA", (noise, noise, noise, Image.new("L", size, 10)))
    scene = Image.alpha_composite(scene, grain).convert("RGB")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix == ".webp":
        scene.save(out_path, quality=92, method=6)
    else:
        scene.save(out_path)
    print("wrote", out_path, scene.size)


if __name__ == "__main__":
    main()
