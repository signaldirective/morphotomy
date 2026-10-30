# drop wallpapers here

`nexus-emblem.png` is the supplied Nexus Morphotomy Clinics emblem sheet.
`tools/make-login.py` cuts the circular figure out of it and remaps the cyan to
arterial red; nothing else from this directory ships.

Put candidate images in this directory — any size, 2560×1440 or larger is
ideal. Nothing in `source/` ships with the theme; it is just an inbox.

```bash
# full dossier still
tools/compose-dossier.py source/whatever.jpg \
    --out backgrounds/9-whatever.webp \
    --title "SPECIMEN 84" \
    --preview /home/ro/.hermes/cache/scratch/check.png

# quieter static variant: title + metadata + barcode, no grid/ECG/ruler
tools/compose-dossier.py source/whatever.jpg --overlay quiet --out backgrounds/9-alt.webp
```

`compose-dossier.py --help` lists the rest: `--grade` (how hard to push the
picture into the palette), `--anchor left|right|none` (skip the automatic
quiet-area detection), `--row "KEY=VALUE"` to change the metadata, `--serial`,
`--caption`, `--seed`.

What the overlay needs from the picture, for reference when choosing:

- a large, low-detail region (sky, fog, flat wall, dark water) for the text
- midtones or darker — near-white highlights blow out once graded
- no faces or crucial detail exactly where the title lands; `--anchor` overrides
  the automatic placement if it guesses wrong
