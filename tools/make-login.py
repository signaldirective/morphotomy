#!/usr/bin/env python3
"""Nexus Morphotomy Clinics — login identity.

Renders the two brand assets the theme ships:

  unlock.png          transparent lockup. Omarchy publishes it as the SDDM
                      greeter logo and the Plymouth splash centre, so it has to
                      stand on its own against a flat #080506 field.
  preview-unlock.png  2560x1440 mock of the login screen: the lockup plus the
                      clinic chrome the real greeter cannot carry.

Everything is drawn from geometry, seeded, and deterministic.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent

BRAND = "/home/ro/.local/share/fonts/GeistMonoNerdFont-Black.otf"
BRAND_REG = "/home/ro/.local/share/fonts/GeistMonoNerdFont-Regular.otf"
BRAND_LIGHT = "/home/ro/.local/share/fonts/GeistMonoNerdFont-Light.otf"
SYS = "/home/ro/.local/share/fonts/SpaceMonoNerdFont-Regular.ttf"

BONE = (211, 199, 190, 255)
DIM  = (168, 158, 150, 255)   # console values: readable, never competing
BRIGHT = (244, 234, 225, 255)
MUTED = (106, 89, 85, 255)
TISSUE = (74, 58, 58, 255)
ARTERIAL = (255, 46, 61, 255)
VITAL = (95, 143, 106, 255)
BG = (8, 5, 6, 255)

WIDTH = 2560
HEIGHT = 1440

WORD_1 = "NEXUS"
WORD_2 = "MORPHOTOMY"
SUB = "CLINICS"
TAGLINE = "AUTHORIZED AUGMENTATION  ·  EST. 2084"

EMBLEM_SRC = ROOT / "source" / "nexus-emblem.png"
EMBLEM_CACHE = {}

# ------------------------------------------------------------------ emblem


def emblem(size, warm=0.10):
    """The circular figure, cropped out of the supplied artwork.

    SIVA cyan is remapped to arterial red by luminance, so the glow keeps its
    shape and the mark stays inside the theme's palette. Whites are nudged
    toward bone: pure #ffffff reads cold next to #d3c7be.
    """
    key = (size, warm)
    if key in EMBLEM_CACHE:
        return EMBLEM_CACHE[key]

    src = Image.open(EMBLEM_SRC).convert("RGBA")
    lum = src.convert("L")
    # only the emblem: everything above the wordmark
    bbox = lum.point(lambda v: 255 if v > 24 else 0).crop(
        (0, 0, src.width, int(src.height * 0.632))
    ).getbbox()
    x0, y0, x1, y1 = bbox

    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sq = (
        int(cx - side / 2), int(cy - side / 2),
        int(cx + side / 2), int(cy + side / 2),
    )
    art = src.crop(sq)

    px = art.load()
    bone = (211, 199, 190)
    for y in range(art.height):
        for x in range(art.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if b > r + 12 and g > r + 8:
                v = max(r, g, b) / 255.0
                px[x, y] = (round(255 * v), round(46 * v), round(61 * v), a)
            elif warm:
                px[x, y] = (
                    round(r * (1 - warm) + bone[0] * warm),
                    round(g * (1 - warm) + bone[1] * warm),
                    round(b * (1 - warm) + bone[2] * warm),
                    a,
                )

    out = art.resize((size, size), Image.LANCZOS)
    EMBLEM_CACHE[key] = out
    return out


# ----------------------------------------------------------------- geometry


def hexagon(cx, cy, r, rot=-90.0):
    import math

    return [
        (cx + r * math.cos(math.radians(rot + 60 * i)),
         cy + r * math.sin(math.radians(rot + 60 * i)))
        for i in range(6)
    ]


def _poly(draw, pts, fill=None, outline=None, width=1):
    draw.polygon(pts, fill=fill)
    if outline is not None:
        draw.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


# -------------------------------------------------------------------- type


def font(path, size):
    return ImageFont.truetype(path, size)


def tracked_size(text, f, tracking=0.0):
    return sum(f.getlength(c) + tracking for c in text) - tracking


def tracked(d, xy, text, f, fill, tracking=0.0, anchor="la"):
    """Letter-spaced text. anchor is a PIL anchor, e.g. 'la', 'lm', 'ma'."""
    x, y = xy
    w = tracked_size(text, f, tracking)
    if anchor[0] == "m":
        x -= w / 2
    elif anchor[0] == "r":
        x -= w
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="l" + anchor[1])
        x += f.getlength(ch) + tracking
    return x


def rule(d, x0, x1, y, fill=(211, 199, 190, 22), width=1):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)


def barcode(d, x, y, w, h, seed=9, colour=(211, 199, 190, 150)):
    import random

    rnd = random.Random(seed)
    cursor = x
    while cursor < x + w - 2:
        bw = rnd.choice([2, 2, 3, 5])
        gap = rnd.choice([3, 4, 6])
        if cursor + bw > x + w:
            break
        d.rectangle([cursor, y, cursor + bw, y + h], fill=colour)
        cursor += bw + gap


# ------------------------------------------------------------------ lockup


def lockup(scale=1.0):
    """Horizontal mark + wordmark, tightly cropped on its own canvas.

    The canvas is measured from the type, never guessed: clipping the wordmark
    is the one failure that survives every later resize.
    """
    f_big = font(BRAND, int(84 * scale))
    f_sub = font(BRAND_LIGHT, int(31 * scale))
    f_tag = font(SYS, int(15 * scale))

    tr_big, tr_sub, tr_tag = 5 * scale, 20 * scale, 2.4 * scale
    gap_word = int(26 * scale)

    w_nexus = tracked_size(WORD_1, f_big, tr_big)
    w_value = tracked_size(WORD_2, f_big, tr_big)
    w_clinics = tracked_size(SUB, f_sub, tr_sub)
    w_tag = tracked_size(TAGLINE, f_tag, tr_tag)
    text_w = max(w_nexus + gap_word + w_value, w_clinics, w_tag)

    mark_s = int(186 * scale)
    gap, pad = int(44 * scale), int(6 * scale)
    div_w = max(1, int(2 * scale))

    W = int(pad + mark_s + gap + div_w + gap + text_w + pad)
    H = mark_s

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    img.alpha_composite(emblem(mark_s), (pad, 0))

    div_x = pad + mark_s + gap
    d.line([(div_x, 0), (div_x, H)], fill=(211, 199, 190, 46), width=div_w)

    tx = div_x + div_w + gap
    tracked(d, (tx, H * 0.33), WORD_1, f_big, BRIGHT, tr_big, "lm")
    tracked(d, (tx + w_nexus + gap_word, H * 0.33), WORD_2, f_big, BRIGHT,
            tr_big, "lm")

    rule_y = H * 0.545
    d.line([(tx, rule_y), (tx + w_nexus * 0.62, rule_y)], fill=ARTERIAL,
           width=max(1, int(3 * scale)))

    tracked(d, (tx, H * 0.685), SUB, f_sub, BONE, tr_sub, "lm")
    tracked(d, (tx, H * 0.905), TAGLINE, f_tag, MUTED, tr_tag, "lm")

    return img


def build_unlock():
    """Transparent lockup for SDDM + Plymouth, on an 1800x430 field."""
    lu = lockup(1.0)
    W, H = 1800, 430
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # wide margin inside the canvas keeps the greeter's own scaling sane
    ink_w = min(lu.width, 1180)
    lu = lu.resize((ink_w, round(lu.height * ink_w / lu.width)), Image.LANCZOS)
    # ink is centred in the canvas: SDDM centres the canvas, not the ink
    x, y = (W - ink_w) // 2, 75
    img.alpha_composite(lu, (x, y))

    d = ImageDraw.Draw(img)
    base = y + lu.height + 46
    rule(d, W / 2 - 470, W / 2 + 470, base, (211, 199, 190, 40))
    tracked(
        d, (W / 2, base + 30),
        "CLINIC NETWORK 04  ·  WORKSTATION 09-B  ·  SECTOR 9",
        font(SYS, 19), MUTED, 2, "mm",
    )
    return img


def build_preview():
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG)

    # ---- field: soft arterial light, hex weave, vignette
    wash = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    wd.ellipse([WIDTH * 0.18, -HEIGHT * 0.30, WIDTH * 0.82, HEIGHT * 0.86],
               fill=(255, 46, 61, 20))
    img.alpha_composite(wash.filter(ImageFilter.GaussianBlur(240)))

    weave = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    wd = ImageDraw.Draw(weave)
    step, rad = 92, 52
    for row in range(-1, HEIGHT // step + 2):
        oy = row * step * 0.87
        for col in range(-1, WIDTH // step + 2):
            ox = col * step + (step // 2 if row % 2 else 0)
            _poly(wd, hexagon(ox, oy, rad), outline=(211, 199, 190, 7))
    img.alpha_composite(weave)

    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-WIDTH * 0.22, -HEIGHT * 0.30, WIDTH * 1.22, HEIGHT * 1.30], fill=90)
    vignette = vignette.filter(ImageFilter.GaussianBlur(220))
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    shadow.putalpha(Image.eval(vignette, lambda v: 255 - v))
    img.alpha_composite(shadow)

    d = ImageDraw.Draw(img)
    M = 88
    f_sys = font(SYS, 15)

    # ---- top bar
    img.alpha_composite(emblem(46), (M, 70))
    tracked(d, (M + 62, 84), "NEXUS MORPHOTOMY CLINICS",
            font(BRAND_REG, 21), BONE, 3)
    tracked(d, (M + 62, 114), "BIO-INTEGRATION DIVISION", f_sys, TISSUE, 2.2)

    right_x = WIDTH - M
    station = "WORKSTATION 09-B  ·  CLINIC 04  ·  SECTOR 9"
    tracked(d, (right_x, 84), station, f_sys, MUTED, 2, "ra")
    state = "SYSTEM NOMINAL  ·  NETWORK 04"
    state_w = tracked_size(state, f_sys, 2)
    d.ellipse([right_x - state_w - 20, 112, right_x - state_w - 12, 120], fill=VITAL)
    tracked(d, (right_x, 110), state, f_sys, VITAL, 2, "ra")

    rule(d, M, WIDTH - M, 168, (211, 199, 190, 34))
    rule(d, M, WIDTH - M, 1292, (211, 199, 190, 34))

    # ---- centre lockup
    lu = lockup(1.0)
    ink_w = 1060
    lu = lu.resize((ink_w, round(lu.height * ink_w / lu.width)), Image.LANCZOS)
    img.alpha_composite(lu, ((WIDTH - ink_w) // 2, 292))
    d = ImageDraw.Draw(img)

    # who is unlocking: the corporate-workstation half of the brief
    tracked(d, (WIDTH / 2, 534),
            "OPERATOR  K. VOSS  ·  BADGE 4-1190  ·  SHIFT 02  ·  SPECIMEN CONTROL",
            font(SYS, 16), MUTED, 2.6, "mm")

    # ---- credential field, 520x82, arterial border
    fw, fh = 520, 82
    fx, fy = (WIDTH - fw) // 2, 596
    d.rounded_rectangle([fx - 3, fy - 3, fx + fw + 3, fy + fh + 3], radius=8,
                        fill=(255, 46, 61, 22))
    d.rounded_rectangle([fx, fy, fx + fw, fy + fh], radius=5, fill=(13, 8, 9, 235),
                        outline=(255, 46, 61, 150), width=2)

    # masked credential: drawn, not typed — a mono font may lack U+25CF
    dot_r, dot_step = 5, 19
    dots = 8
    group_w = dots * dot_step - (dot_step - 2 * dot_r)
    dx = fx + (fw - 74 - group_w) / 2 + dot_r
    for _ in range(dots):
        d.ellipse([dx - dot_r, fy + fh / 2 - dot_r, dx + dot_r, fy + fh / 2 + dot_r],
                  fill=BONE)
        dx += dot_step
    d.rectangle([dx - dot_r + dot_step - 2, fy + 28,
                 dx - dot_r + dot_step, fy + fh - 28], fill=ARTERIAL)

    grip = (211, 199, 190, 110)
    fcx, fcy = fx + fw - 42, fy + fh / 2
    for r in (8, 13, 18, 23):
        d.arc([fcx - r, fcy - r, fcx + r, fcy + r], 198, 342, fill=grip, width=2)
    d.arc([fcx - 5, fcy - 5, fcx + 5, fcy + 5], 205, 335, fill=grip, width=2)

    tracked(d, (WIDTH / 2, fy + fh + 28), "ENTER EMPLOYEE CREDENTIALS  ·  PRESS RETURN",
            f_sys, MUTED, 3, "ma")
    tracked(d, (WIDTH / 2, fy + fh + 58),
            "UNAUTHORIZED ACCESS IS A CLASS-IV CONSENT VIOLATION",
            font(SYS, 13), (150, 46, 52, 220), 2.2, "ma")

    # ---- clinic console: full-width strip, the hospital half of the brief
    px, py, pw, ph = M, 856, WIDTH - 2 * M, 328
    d.rectangle([px, py, px + pw, py + ph], fill=(10, 6, 7, 140),
                outline=(211, 199, 190, 22))
    d.line([(px, py), (px + 5, py)], fill=ARTERIAL, width=3)

    tracked(d, (px + 24, py + 27), "CLINIC CONSOLE  ·  BAY 09  ·  LIVE",
            f_sys, MUTED, 2.6, "lm")
    tracked(d, (px + pw - 24, py + 27), "SYNC 14:07:22", f_sys, TISSUE, 2.2, "rm")
    rule(d, px + 24, px + pw - 24, py + 52, (211, 199, 190, 22))

    split = px + 924
    d.line([(split, py + 52), (split, py + ph - 24)], fill=(211, 199, 190, 20))

    # left column: shift state
    f_row = font(SYS, 15)
    f_lab = font(SYS, 14)
    tracked(d, (px + 24, py + 82), "SHIFT STATUS", font(SYS, 13), TISSUE, 2.4, "lm")
    rows = [
        ("BAY 09", "ACTIVE", DIM),
        ("STERILE FIELD", "READY", VITAL),
        ("GRAFT QUEUE", "12 WAITING", DIM),
        ("CONSENT REVIEWS", "3 PENDING", ARTERIAL),
        ("NIGHT SURGEON", "V. SAAR", DIM),
    ]
    ry = py + 122
    for label, value, colour in rows:
        tracked(d, (px + 24, ry), label, f_lab, TISSUE, 2.2, "lm")
        tracked(d, (split - 32, ry), value, f_lab, colour, 2.2, "rm")
        ry += 38

    # right column: graft manifest
    mx = split + 34
    tracked(d, (mx, py + 82), "TODAY'S GRAFT MANIFEST", font(SYS, 13), TISSUE, 2.4,
            "lm")
    cols = [(mx, "TIME"), (mx + 150, "SPECIMEN"), (mx + 470, "PROCEDURE"),
            (px + pw - 24, "STATUS")]
    for cx, label in cols:
        anc = "rm" if label == "STATUS" else "lm"
        tracked(d, (cx, py + 116), label, font(SYS, 13), TISSUE, 2.2, anc)

    manifest = [
        ("06:40", "0084-AC-61", "CORTICAL BRIDGE, LAYER III", "IN PROGRESS", DIM),
        ("09:15", "0091-KD-04", "OCULAR REPLACEMENT, LEFT", "SCHEDULED", MUTED),
        ("11:00", "0107-TT-88", "SPINAL LATTICE EXTENSION", "CONSENT HOLD", ARTERIAL),
    ]
    ry = py + 150
    for time, spec, proc, status, colour in manifest:
        tracked(d, (mx, ry), time, f_row, MUTED, 2, "lm")
        tracked(d, (mx + 150, ry), spec, f_row, DIM, 2, "lm")
        tracked(d, (mx + 470, ry), proc, f_row, MUTED, 2, "lm")
        tracked(d, (px + pw - 24, ry), status, f_row, colour, 2, "rm")
        rule(d, mx, px + pw - 24, ry + 20, (211, 199, 190, 12))
        ry += 38

    tracked(d, (mx + 470, py + ph - 42), "RECOVERY RATE 98.4%  ·  REVISION RATE 6.1%",
            font(SYS, 13), TISSUE, 2.2, "lm")

    # ---- footer
    tracked(d, (M, 1326),
            "NEXUS MORPHOTOMY CLINICS  ·  4471 ASHGRAVE AVENUE  ·  SECTOR 9",
            f_sys, MUTED, 2, "lm")
    tracked(d, (WIDTH / 2, 1326), "© 2087 NEXUS HEALTHNET  ·  ALL GRAFTS RESERVED",
            f_sys, TISSUE, 2, "mm")
    barcode(d, WIDTH - M - 316, 1314, 180, 24, seed=84)
    tracked(d, (WIDTH - M, 1326), "09-B / 4.7.2", f_sys, MUTED, 2, "rm")

    return img.convert("RGB")


def main():
    unlock = build_unlock()
    unlock.save(ROOT / "unlock.png")
    print("wrote", ROOT / "unlock.png", unlock.size)

    preview = build_preview()
    preview.save(ROOT / "preview-unlock.png")
    print("wrote", ROOT / "preview-unlock.png", preview.size)


if __name__ == "__main__":
    main()
