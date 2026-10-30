# MORPHOTOMY

A theme for [Omarchy](https://omarchy.org/) about grafts that were not always
consented to.

Alternate timeline: cybernetics are cut into living bodies by morphotomists —
surgeons who are more machine than person. The desktop is the operating bay.
Bone and dried blood carry the interface; arterial red is the only thing that
ever lights up, and it means *incision*.

![MORPHOTOMY](preview.png)

## Install

```bash
./install.sh                 # copy into ~/.config/omarchy/themes/morphotomy
./install.sh --link --apply  # symlink (edits apply live) and switch to it now
./install.sh --plymouth --hook   # custom boot splash + keep it after theme changes
```

`--plymouth` needs sudo: it installs a script-module theme into
`/usr/share/plymouth/themes/morphotomy`, sets it as the default and rebuilds the
initramfs. `--hook` installs a `theme-set` hook, because Omarchy's theme switch
re-publishes its own Plymouth theme and would otherwise take the splash back.

## What's in it

| File | Purpose |
|---|---|
| `colors.toml` | the palette every generated template derives from |
| `hyprland.lua` | arterial gradient border, graft shadow, suture/incision curves |
| `btop.theme` | vitals monitor: cauterised orange titles, bone text |
| `chromium.theme`, `icons.theme`, `keyboard.rgb` | browser tint, icon theme, LED colour |
| `backgrounds/1-implantation.webp` | default wallpaper: forced implantation scene |
| `backgrounds/2-surgery-bay.webp` | alternate: surgery bay |
| `backgrounds/3-eye.webp` | alternate: isolated eye, quiet dossier |
| `backgrounds/4-eye-dossier.webp` | alternate: eye with the full overlay |
| `backgrounds/5-hand.webp` | Specimen 311, hand with full dossier |
| `backgrounds/6-heart.webp` | user-supplied Specimen 217, existing HUD preserved |
| `backgrounds/7-brain.webp` | user-supplied Specimen 443, existing HUD preserved |
| `backgrounds/8-surgery.webp` | surgery room, existing in-world HUD preserved |
| `backgrounds/9-eye-diagnostic.mp4` | alternate: fixed eye with 2 animated callouts |
| `backgrounds/9-eye-blink.mp4` | alternate: brief eye blink, repeated every 8 s |
| `backgrounds/9-heart-diagnostic.mp4` | alternate: fixed heart with 3 callouts |
| `backgrounds/9-brain-diagnostic.mp4` | alternate: fixed brain with 3 callouts |
| `source/SURGERY.png` | original branded surgery-room artwork |
| `source/contact-sheet.png` | 15 Wallhaven candidates, numbered |
| `unlock.png` | wordmark used by Plymouth, SDDM and the lock screen |
| `plymouth/morphotomy/` | boot splash: seam closes, fourteen sutures drop in |

Neovim, Alacritty, Kitty, Ghostty, foot, Helix, btop and the rest are generated
by Omarchy from `colors.toml`, so they follow automatically.

## Wallpapers

No Blender artwork ships any more. The eight WebP stills remain the default
choices. Four opt-in MP4 alternatives add only diagnostic callouts or the brief
eye blink; they do not zoom, shake, or repaint the source. Background intros
remain disabled.

The default is the forced-implantation still, in `--overlay tag` mode. `5-hand`
uses a Pexels prosthetic-hand photo with the custom Specimen 311 dossier.
`6-heart` and `7-brain` are your pre-branded dossier images; their existing type
is preserved. `8-surgery` is your branded surgery-room image. Original PNGs are
kept in `source/`.

The hand source photo is Pexels #7688766:
https://www.pexels.com/photo/close-up-photo-of-a-prosthetic-arm-7688766/.

## Diagnostic HUD animations

`tools/render-diagnostic-hud.py` draws a separate transparent layer over a still;
the base image stays fixed and unchanged. The eye uses two callouts; heart and
brain use three each. All three videos begin and end on the untouched still.

```bash
python3 tools/render-diagnostic-hud.py tools/diagnostics/eye.json --out /tmp/eye.mp4
python3 tools/render-diagnostic-hud.py tools/diagnostics/heart.json --out /tmp/heart.mp4
python3 tools/render-diagnostic-hud.py tools/diagnostics/brain.json --out /tmp/brain.mp4
bash tools/make-eye-blink-alternate.sh
```

No camera motion, zoom, shake, or audio is used. The blink alternate is based on
`source/eye-blink-seed.mp4`; intros remain disabled.

`source/contact-sheet.png` collects fifteen candidates pulled from Wallhaven,
each with the tag overlay, numbered. To promote one:

```bash
tools/fetch-candidates.py 15                     # top up source/candidates/
tools/compose-dossier.py source/candidates/<file> --out backgrounds/9-<name>.webp \
    --overlay quiet --grade 0.35
./install.sh --link && omarchy theme set morphotomy
```

Candidates are filtered to 16:9-ish, ≥2560×1440, SFW. The project owner has
confirmed redistribution rights for all image assets included in this beta;
retain any per-image attribution or license terms when reusing them.

Drop candidates into `source/` (an inbox, not shipped) and make a still:

```bash
tools/compose-dossier.py source/yours.jpg --out backgrounds/9-yours.webp \
    --title "SPECIMEN 84" --preview /home/ro/.hermes/cache/scratch/check.png
```

`compose-dossier.py` cover-crops to 2560×1440, grades the picture into the
palette, finds a quiet region for the type, and can add the title, metadata,
ruler, barcode and ECG trace. Styles: `--overlay full|quiet|minimal|tag`;
`--anchor left|right|none` overrides placement; `--grade 0..1` controls grading.
`--trace-label` and `--timestamp-label` customize the lower telemetry. Everything
is seeded for repeatable renders.

Background intros are disabled with `omarchy theme bg intro disable`. The
still WebPs remain available beside the four explicit MP4 alternates.

## Palette

```
background   #080506   dried blood black
foreground   #d3c7be   bone
muted        #4a3a3a   dried tissue
accent       #ff2e3d   arterial — links, focus, the active border
selection    #3b0d12   clot
green        #5f8f6a   vitals (kept green on purpose, it has to read instantly)
```

Bone on background measures ~12:1. Red is deliberately not used for body text.

## Regenerating theme elements

The wordmark, Plymouth splash and dossier typography are generated by tools in
`tools/`. Wallpaper imagery is source art, not a Blender render. The theme ships
eight stills plus four opt-in MP4 alternates: diagnostic overlays for eye,
heart and brain, and the approved quick blink. Background intros remain off.

```bash
python3 tools/make-wordmark.py
python3 tools/make-plymouth-assets.py
tools/compose-dossier.py source/your-image.jpg --out backgrounds/9-your-image.webp
```

## Caveats

- `omarchy theme bg next` cycles through eight stills and four explicit
  motion alternates; intros are disabled so selecting one never plays a second
  intro clip.
- No `shell.toml` ships with this theme: Omarchy's generated one already
  derives bar and lock colours from `colors.toml`, and shipping a partial file
  risks losing geometry it sets. A hand-tuned bar is the next lever.
- The Plymouth splash and its hook are the only parts outside `~/.config`, so
  they are the only parts an Omarchy update can disturb.
- Cursors are not included: `xcursorgen` (package `xorg-xcursorgen`) is not
  installed here, so the scalpel cursor is still to do.

## Licence

MIT applies to the theme scripts and original code. Third-party or user-supplied
wallpaper art retains its own source/license; `source/` is excluded from install.
