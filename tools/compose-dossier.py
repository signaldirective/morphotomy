#!/usr/bin/env python3
"""MORPHOTOMY dossier overlay — put the theme's typography on any wallpaper.

    compose-dossier.py SOURCE --out BACKGROUNDS/1-name.webp [options]

The photograph does the work; this script does four things to it:

  1. cover-crops to the target size and grades it into the palette (darken,
     cool the deepest blacks, keep the highlights from clipping),
  2. finds the quietest region of the frame by measuring local variance, so
     the dossier block lands on empty sky instead of on a face,
  3. lays the overlay: title rule, metadata rows, ruler, barcode, ECG trace
     and optional callouts,
  4. writes webp/jpg plus a small preview for checking.

Styles: --overlay full (default), quiet (title + rows + barcode only),
minimal (title rule only). Everything is seeded, so reruns are identical.
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

DISPLAY = "/home/ro/.local/share/fonts/DepartureMonoNerdFont-Regular.otf"
BODY = "/home/ro/.local/share/fonts/IosevkaNerdFontMono-Regular.ttf"

BONE = (211, 199, 190)
BONE_HI = (244, 234, 225)
MUTED = (172, 152, 144)
DIM = (128, 110, 106)
ARTERIAL = (255, 46, 61)

DEFAULT_ROWS = [
    ("GRAFT CLASS", "IV / SUSPENDED"),
    ("ORIGIN", "MORPHOTOMY UNIT 09"),
    ("CONSENT", "DISPUTED"),
    ("INTEGRITY", "61%"),
    ("PERFUSION", "NOMINAL"),
]


def tracked(draw, xy, text, font, fill, tracking=0.0):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking
    return x


def text_width(text, font, tracking=0.0):
    return sum(font.getlength(c) + tracking for c in text) - tracking


def cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    w, h = size
    scale = max(w / img.width, h / img.height)
    resized = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
    left = (resized.width - w) // 2
    top = (resized.height - h) // 2
    return resized.crop((left, top, left + w, top + h))


def grade(img: Image.Image, amount: float) -> Image.Image:
    """Push the picture down into the theme's blacks without crushing it."""
    if amount <= 0:
        return img
    img = ImageEnhance.Color(img).enhance(1.0 - 0.25 * amount)
    img = ImageEnhance.Brightness(img).enhance(1.0 - 0.45 * amount)
    img = ImageEnhance.Contrast(img).enhance(1.0 + 0.15 * amount)
    # warm the shadows toward dried blood, keep highlights neutral
    shade = Image.new("RGB", img.size, (10, 4, 5))
    img = ImageChops.blend(img, ImageChops.multiply(img, shade), 0.20 * amount)
    return img


def quiet_zone(img: Image.Image, cols: int = 6, rows: int = 4) -> tuple[int, int, int, int]:
    """Return the (col, row, cols, rows) cell block with the least detail."""
    small = img.convert("L").resize((cols * 32, rows * 32), Image.LANCZOS)
    px = small.load()
    best, best_score = (0, 0), 1e9
    for cy in range(rows):
        for cx in range(cols):
            vals = [px[x, y] for y in range(cy * 32, (cy + 1) * 32, 4) for x in range(cx * 32, (cx + 1) * 32, 4)]
            mean = sum(vals) / len(vals)
            var = sum((v - mean) ** 2 for v in vals) / len(vals)
            # prefer dark, quiet cells, slightly favouring the left and top
            score = var + mean * 0.35 + cx * 6
            if score < best_score:
                best_score, best = score, (cx, cy)
    return best[0], best[1], cols, rows


def frames(size, ink):
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    m = 48
    for cx, cy, dx, dy in [(m, m, 1, 1), (w - m, m, -1, 1), (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
        draw.line([(cx, cy), (cx + 36 * dx, cy)], fill=(*ink, 110), width=2)
        draw.line([(cx, cy), (cx, cy + 36 * dy)], fill=(*ink, 110), width=2)
    return layer


def ruler(size, x, top, bottom, ink):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.line([(x, top), (x, bottom)], fill=(*ink, 120), width=1)
    steps = 40
    for i in range(steps + 1):
        y = top + i * (bottom - top) / steps
        long = i % 5 == 0
        draw.line([(x - (18 if long else 8), y), (x, y)], fill=(*ink, 150 if long else 80), width=2 if long else 1)
    return layer


def ecg(size, base_y, ink, seed):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    w, h = size
    points = []
    x = 120
    phase = 0.0
    random.seed(seed)
    jitter = random.uniform(0, 3)
    while x < w - 120:
        t = phase + jitter
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
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).line(points, fill=(*ink, 80), width=6, joint="curve")
    layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(5)))
    draw.line(points, fill=(*ink, 235), width=2, joint="curve")
    return layer


def barcode(size, x, y, ink, seed):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    random.seed(seed)
    cx = x
    for i in range(46):
        width = random.choice([2, 2, 3, 5, 7])
        if i % 2 == 0:
            draw.rectangle([cx, y, cx + width, y + 46], fill=(*ink, 205))
        cx += width + random.choice([2, 3, 4])
    return layer, cx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="2560x1440")
    ap.add_argument("--title", default="SPECIMEN 84")
    ap.add_argument("--subtitle", default="MORPHOTOMY UNIT 09")
    ap.add_argument("--caption", default="GRAFTED UNDER PROTEST")
    ap.add_argument("--serial", default="0084-AC-61")
    ap.add_argument("--row", action="append", default=[], help="KEY=VALUE, repeatable")
    ap.add_argument("--overlay", choices=["full", "quiet", "minimal", "tag"], default="full")
    ap.add_argument("--anchor", default="auto", choices=["auto", "left", "right", "none"])
    ap.add_argument("--grade", type=float, default=0.45, help="0 leaves the picture alone, 1 buries it")
    ap.add_argument("--grain", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=84)
    ap.add_argument("--preview", default=None, help="also write a 1280-wide preview here")
    args = ap.parse_args()

    w, h = (int(v) for v in args.size.lower().split("x"))
    size = (w, h)

    src = Image.open(args.source).convert("RGB")
    scene = grade(cover(src, size), args.grade).convert("RGBA")

    rows = DEFAULT_ROWS
    if args.row:
        rows = []
        for spec in args.row:
            key, _, value = spec.partition("=")
            rows.append((key.strip(), value.strip()))

    title_font = ImageFont.truetype(DISPLAY, max(38, int(h * 0.040)))
    row_font = ImageFont.truetype(BODY, max(18, int(h * 0.016)))
    micro_font = ImageFont.truetype(BODY, max(15, int(h * 0.014)))
    small_font = ImageFont.truetype(BODY, max(17, int(h * 0.015)))

    # ---- where does the text live?
    if args.anchor == "none":
        block = None
    elif args.anchor == "left":
        block = (0, 1)
    elif args.anchor == "right":
        block = (3, 1)
    else:
        cx, cy, cols, rows_n = quiet_zone(scene)
        block = (0, cy) if cx < cols / 2 else (cols // 2, cy)
    on_left = block is None or block[0] < 2

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    margin = int(w * 0.05)
    stamp_y = int(h * 0.09) if args.anchor in ("auto", "left", "none") else int(h * 0.09)
    text_x = margin if on_left else int(w * 0.54)

    if args.overlay == "tag":
        # Small plate in the top-right: enough to brand the frame, quiet enough
        # to leave pre-branded artwork alone.
        plate_w = int(w * 0.20)
        plate_h = int(h * 0.085)
        px = w - margin - plate_w
        py = margin + int(h * 0.01)
        draw.rectangle([px, py, px + plate_w, py + plate_h], outline=(*BONE, 90), width=1)
        tracked(draw, (px + 14, py + 12), args.title, micro_font, BONE_HI, 3)
        tracked(draw, (px + 14, py + 12 + int(h * 0.026)), "INTEGRITY 61%  ·  CONSENT DISPUTED",
                micro_font, MUTED, 1)
        code, _ = barcode(size, px + 14, py + plate_h + 16, BONE, args.seed)
        scale = 0.55
        code = code.resize((int(code.width * scale), int(code.height * scale)), Image.LANCZOS)
        overlay.alpha_composite(code, (px + 14, py + plate_h + 16))
        tracked(draw, (px + 14, py + plate_h + 16 + 34), args.serial, micro_font, DIM, 2)
        block = None

    if block is not None:
        tracked(draw, (text_x, stamp_y), args.title, title_font, BONE_HI, 6)
        rule_y = stamp_y + int(title_font.size * 1.35)
        draw.line(
            [(text_x, rule_y), (text_x + int(text_width(args.title, title_font, 6)), rule_y)],
            fill=(*ARTERIAL, 210),
            width=2,
        )
        tracked(draw, (text_x, rule_y + int(h * 0.014)), args.subtitle, micro_font, DIM, 2)

        if args.overlay != "minimal":
            y = rule_y + int(h * 0.055)
            value_x = text_x + int(w * 0.075)
            for key, value in rows:
                tracked(draw, (text_x, y), key, micro_font, MUTED, 2)
                colour = ARTERIAL if value.upper().startswith(("DISPUT", "REFUSED", "DENIED")) else BONE
                tracked(draw, (value_x, y), value, small_font, colour, 1)
                y += int(h * 0.026)

    if args.overlay == "full":
        overlay.alpha_composite(frames(size, BONE))
        ruler_x = margin + 40 if on_left else w - margin - 40
        overlay.alpha_composite(ruler(size, ruler_x, int(h * 0.30), int(h * 0.78), (110, 60, 62)))
        overlay.alpha_composite(ecg(size, h - int(h * 0.10), ARTERIAL, args.seed))
        draw = ImageDraw.Draw(overlay)
        tracked(draw, (120, h - int(h * 0.062)), "CARDIAC SYNC · 62 BPM · LEAD II", micro_font, MUTED, 2)
        tracked(draw, (120, h - int(h * 0.17)), "2026-03-14  04:12:07  ·  SLOT 84  ·  UNIT 09", micro_font, MUTED, 2)

    if args.overlay != "minimal":
        code, end_x = barcode(size, w - margin - int(w * 0.16), h - int(h * 0.19), BONE, args.seed)
        overlay.alpha_composite(code)
        draw = ImageDraw.Draw(overlay)
        tracked(draw, (w - margin - int(w * 0.16), h - int(h * 0.19) + 56), args.serial, micro_font, MUTED, 3)
        cap_w = text_width(args.caption, small_font, 4)
        tracked(draw, (w - margin - cap_w, h - int(h * 0.062)), args.caption, small_font, (170, 62, 68), 4)

    scene = Image.alpha_composite(scene, overlay)

    # ---- vignette
    vig = Image.new("L", size, 0)
    ImageDraw.Draw(vig).ellipse([-w * 0.22, -h * 0.32, w * 1.22, h * 1.32], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(200))
    scene = Image.composite(scene, Image.new("RGBA", size, (0, 0, 0, 255)), vig)

    # ---- scanlines + grain
    if args.grain > 0:
        scan = Image.new("RGBA", size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(scan)
        for y in range(0, h, 3):
            sd.line([(0, y), (w, y)], fill=(0, 0, 0, 14))
        scene = Image.alpha_composite(scene, scan)

        noise = Image.effect_noise(size, 14).convert("L")
        alpha = Image.new("L", size, int(9 * min(1.0, args.grain)))
        scene = Image.alpha_composite(scene, Image.merge("RGBA", (noise, noise, noise, alpha)))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    flat = scene.convert("RGB")
    if out.suffix.lower() == ".webp":
        flat.save(out, quality=92, method=6)
    elif out.suffix.lower() in (".jpg", ".jpeg"):
        flat.save(out, quality=92)
    else:
        flat.save(out)
    print(f"wrote {out} ({w}x{h})")

    if args.preview:
        prev = Path(args.preview)
        prev.parent.mkdir(parents=True, exist_ok=True)
        flat.resize((1280, int(1280 * h / w)), Image.LANCZOS).save(prev)
        print(f"preview {prev}")


if __name__ == "__main__":
    main()
