#!/usr/bin/env python3
"""Render a deterministic animated diagnostic HUD over an unchanged still.

Only the transparent overlay is drawn per frame. The source image is copied
unchanged into every frame; there is no camera motion, zoom, grain, vignette,
or generated/altered specimen artwork.

Usage:
  python3 tools/render-diagnostic-hud.py tools/diagnostics/eye.json \
      --out /home/ro/.hermes/cache/scratch/eye-hud-prototype.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return min(hi, max(lo, value))


def smoothstep(value: float) -> float:
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def point_px(point: list[float], size: tuple[int, int]) -> tuple[float, float]:
    return point[0] * size[0], point[1] * size[1]


def polyline_prefix(points: list[tuple[float, float]], progress: float) -> list[tuple[float, float]]:
    """Return the first `progress` fraction of a polyline by arc length."""
    progress = clamp(progress)
    if progress <= 0.0 or len(points) < 2:
        return []
    lengths = [math.dist(a, b) for a, b in zip(points, points[1:])]
    total = sum(lengths)
    if total <= 0:
        return [points[0], points[-1]]
    target = total * progress
    result = [points[0]]
    walked = 0.0
    for a, b, length in zip(points, points[1:], lengths):
        if walked + length <= target:
            result.append(b)
            walked += length
            continue
        local = (target - walked) / length if length else 0.0
        result.append((a[0] + (b[0] - a[0]) * local, a[1] + (b[1] - a[1]) * local))
        break
    return result


def tracked(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str,
            font: ImageFont.FreeTypeFont, fill: tuple[int, int, int, int],
            spacing: float) -> None:
    x, y = xy
    for char in text:
        draw.text((round(x), round(y)), char, font=font, fill=fill)
        x += font.getlength(char) + spacing


def type_state(callout: dict, t: float) -> tuple[int, float]:
    text_length = sum(len(line) for line in callout["lines"]) + len(callout["lines"]) - 1
    type_start = callout["start"] + callout["line_duration"] + callout.get("type_delay", 0.08)
    erase_start = callout["hold_until"]
    if t < type_start:
        return 0, text_length
    if t < erase_start:
        shown = min(text_length, int((t - type_start) * callout.get("type_rate", 24)))
        return shown, text_length
    erased = int((t - erase_start) * callout.get("erase_rate", 34))
    return max(0, text_length - erased), text_length


def line_state(callout: dict, t: float) -> float:
    start = callout["start"]
    line_end = start + callout["line_duration"]
    retract_start = callout["hold_until"] + callout.get("erase_duration", 0.8)
    retract_end = retract_start + callout.get("retract_duration", 0.6)
    if t < start:
        return 0.0
    if t < line_end:
        return smoothstep((t - start) / callout["line_duration"])
    if t < retract_start:
        return 1.0
    if t < retract_end:
        return 1.0 - smoothstep((t - retract_start) / callout.get("retract_duration", 0.6))
    return 0.0


def draw_callout(layer: Image.Image, callout: dict, cfg: dict, t: float,
                 font: ImageFont.FreeTypeFont) -> None:
    w, h = layer.size
    size = (w, h)
    draw = ImageDraw.Draw(layer, "RGBA")
    line_progress = line_state(callout, t)
    if line_progress > 0.0:
        anchor = point_px(callout["anchor"], size)
        elbow_points = [point_px(p, size) for p in callout.get("elbows", [])]
        label_x, label_y = point_px(callout["label"], size)
        endpoint = (label_x - cfg.get("leader_to_label_gap", 14),
                    label_y + cfg.get("font_size", 26) * 0.62)
        path = [anchor, *elbow_points, endpoint]
        visible_path = polyline_prefix(path, line_progress)
        if len(visible_path) >= 2:
            draw.line(visible_path, fill=tuple(cfg["line_rgba"]),
                      width=cfg.get("line_width", 2), joint="curve")
            # Tiny red anchor and endpoint pips; the destination only lights
            # once the line has fully arrived.
            ax, ay = anchor
            r = cfg.get("anchor_radius", 3)
            draw.ellipse((ax-r, ay-r, ax+r, ay+r), fill=tuple(cfg["accent_rgba"]))
            if line_progress >= 0.985:
                ex, ey = endpoint
                rr = cfg.get("endpoint_radius", 4)
                draw.ellipse((ex-rr, ey-rr, ex+rr, ey+rr), fill=tuple(cfg["accent_rgba"]))

    shown, total = type_state(callout, t)
    if shown <= 0:
        return
    remaining = shown
    x, y = point_px(callout["label"], size)
    line_gap = cfg.get("line_gap", int(cfg.get("font_size", 26) * 1.45))
    spacing = cfg.get("tracking", 1.0)
    for index, text in enumerate(callout["lines"]):
        visible_count = min(len(text), remaining)
        if visible_count > 0:
            color = cfg["text_rgba"] if index == 0 else cfg.get("value_rgba", cfg["text_rgba"])
            tracked(draw, (x, y + index * line_gap), text[:visible_count], font,
                    tuple(color), spacing)
        remaining -= len(text) + (1 if index < len(callout["lines"]) - 1 else 0)
        if remaining <= 0:
            break


def make_frame(base: Image.Image, cfg: dict, callouts: list[dict], font: ImageFont.FreeTypeFont,
               t: float) -> Image.Image:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    for callout in callouts:
        draw_callout(overlay, callout, cfg, t, font)
    frame = base.copy().convert("RGBA")
    frame.alpha_composite(overlay)
    return frame.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="specimen JSON config")
    parser.add_argument("--out", required=True, help="MP4 output path")
    parser.add_argument("--force", action="store_true", help="overwrite output if it exists")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    cfg = json.loads(config_path.read_text())
    source = Path(cfg["source"])
    if not source.is_absolute():
        source = ROOT / source
    source = source.resolve()
    if not source.is_file():
        parser.error(f"source wallpaper does not exist: {source}")

    out = Path(args.out).expanduser().resolve()
    if out.exists() and not args.force:
        parser.error(f"output exists; use --force to replace it: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)

    base = Image.open(source).convert("RGB")
    width, height = base.size
    fps = int(cfg.get("fps", 24))
    duration = float(cfg.get("duration", 14.0))
    frames = round(fps * duration)
    font_path = Path(cfg.get("font", "/home/ro/.local/share/fonts/IosevkaNerdFontMono-Regular.ttf"))
    font_size = int(cfg.get("font_size", 26))
    font = ImageFont.truetype(str(font_path), font_size)
    callouts = cfg["callouts"]

    # The loop starts and ends on a frame with an entirely transparent overlay.
    first = make_frame(base, cfg, callouts, font, 0.0)
    last = make_frame(base, cfg, callouts, font, duration - 1 / fps)
    if ImageChops.difference(first, base).getbbox() is not None:
        raise RuntimeError("first frame must be the untouched source still")
    if ImageChops.difference(last, base).getbbox() is not None:
        raise RuntimeError("last frame must be the untouched source still")

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pixel_format", "rgb24",
        "-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", "pipe:0",
        "-an", "-c:v", "libx264", "-preset", cfg.get("preset", "medium"),
        "-crf", str(cfg.get("crf", 18)), "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(out),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame_no in range(frames):
            t = frame_no / fps
            frame = first if frame_no == 0 else last if frame_no == frames - 1 else make_frame(base, cfg, callouts, font, t)
            process.stdin.write(frame.tobytes())
        process.stdin.close()
    except BrokenPipeError:
        process.stdin.close()
        return process.wait() or 1
    code = process.wait()
    if code != 0:
        print(f"ffmpeg failed with exit code {code}", file=sys.stderr)
        return code
    print(f"wrote {out} ({width}x{height}, {fps} fps, {duration:g} s, {frames} frames)")
    print(f"background source unchanged: {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
