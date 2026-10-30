#!/usr/bin/env bash
# Repackage the user-approved 8-second blink test as a seamless 24-second
# 1080p alternate. No camera motion, interpolation, grain, or added effects.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
root=$(dirname "$here")
source=${1:-$root/source/eye-blink-seed.mp4}
out=${2:-$root/backgrounds/9-eye-blink.mp4}

[[ -f "$source" ]] || { echo "missing blink seed: $source" >&2; exit 1; }
mkdir -p "$(dirname "$out")"
ffmpeg -hide_banner -loglevel error -y \
  -stream_loop 2 -i "$source" -t 24 \
  -vf 'scale=1920:1080:flags=lanczos,format=yuv420p' \
  -an -c:v libx264 -preset slow -crf 18 -movflags +faststart "$out"
echo "wrote $out"
