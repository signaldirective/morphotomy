#!/usr/bin/env bash
# Build the animated wallpaper and the boot intro from the composed still.
#
# The motion is a single slow breath: the zoom is a sine over the whole clip,
# so the first and last frame match exactly and the loop has no seam.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
root=$(dirname "$here")
still=${1:-$root/backgrounds/1-specimen-84.webp}
stem=$(basename "$still"); stem=${stem%.*}
frames=576          # 24 s at 24 fps
fps=24

[[ -f $still ]] || { echo "missing $still" >&2; exit 1; }

mkvid() {
  local out=$1 size=$2 zoom=$3 dur=$4 extra=${5:-}
  local w=${size%x*} h=${size#*x}
  local fade=""
  if [[ $extra == "intro" ]]; then
    fade=",fade=t=in:st=0:d=0.7,fade=t=out:st=$((dur-1)):d=1.0"
  fi

  ffmpeg -hide_banner -loglevel error -y -loop 1 -i "$still" \
    -vf "scale=${w}:${h}:flags=lanczos,\
zoompan=z='${zoom}+${zoom}*0.018*sin(2*PI*on/${frames})':\
x='(iw-iw/zoom)*0.62':y='(ih-ih/zoom)*0.5':d=${frames}:s=${w}x${h}:fps=${fps},\
noise=alls=4:allf=t+u,vignette=PI/6,unsharp=5:5:0.4${fade},format=yuv420p" \
    -t "$dur" -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p \
    -movflags +faststart "$out"

  echo "wrote $out ($(du -h "$out" | cut -f1))"
}

mkvid "$root/backgrounds/$stem.mp4" 2560x1440 1.02 24
mkvid "$root/backgrounds/$stem-1080.mp4" 1920x1080 1.02 24
mkvid "$root/backgrounds/intros/$stem.mp4" 1920x1080 1.06 6 intro
