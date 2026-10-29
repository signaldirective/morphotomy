#!/usr/bin/env python3
"""Pull wallpaper candidates from Wallhaven for the theme.

Filters for 16:9-ish, >=2560 wide, SFW general-category art. Writes into
source/candidates/ and prints what it found. Nothing is installed: this is an
inbox you then run through compose-dossier.py.
"""
import json
import random
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source" / "candidates"

TERMS = [
    "cyberpunk",
    "horror",
    "skull",
    "robot",
    "alien",
    "organic",
    "medical",
    "dystopia",
    "machine",
    "dark",
    "giger",
    "biomech",
]

API = "https://wallhaven.cc/api/v1/search"


def fetch(term):
    query = {
        "q": term,
        "categories": "110",   # general + anime: dark sci-fi art lives in both
        "purity": "100",       # sfw
        "sorting": "toplist",
        "atleast": "2560x1440",
    }
    url = API + "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={"User-Agent": "morphotomy-theme/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    OUT.mkdir(parents=True, exist_ok=True)
    seen = set()
    picked = []

    for term in TERMS:
        try:
            data = fetch(term)
        except Exception as err:
            print(f"  {term}: failed ({err})")
            continue
        items = data.get("data", [])
        good = []
        for item in items:
            wid, _, hei = item["resolution"].partition("x")
            wid, hei = int(wid), int(hei)
            ratio = wid / hei
            if wid < 2560 or not (1.65 < ratio < 1.85):
                continue
            if item["id"] in seen:
                continue
            good.append(item)
        print(f"  {term}: {len(items)} results, {len(good)} usable")
        for item in good[:3]:
            if len(picked) >= limit:
                break
            seen.add(item["id"])
            picked.append(item)
        if len(picked) >= limit:
            break

    for item in picked:
        name = f"{item['id']}-{item['resolution']}{Path(item['path']).suffix}"
        target = OUT / name
        if target.exists():
            continue
        try:
            req = urllib.request.Request(item["path"], headers={"User-Agent": "morphotomy-theme/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp, target.open("wb") as fh:
                fh.write(resp.read())
            print(f"  saved {name}")
        except Exception as err:
            print(f"  failed {name}: {err}")

    print(f"\n{len(list(OUT.glob('*')))} files in {OUT}")


if __name__ == "__main__":
    main()
