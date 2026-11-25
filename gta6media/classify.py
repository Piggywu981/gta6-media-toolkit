"""Classify carved Bink2 videos by resolution and duration into content buckets.

The labels are heuristic (RPF9 archives have an encrypted table of contents, so
original filenames are unavailable). They describe *visual shape*, not an
official Rockstar classification.

Usage:
    python -m gta6media.classify --manifest movies.json --out catalog.csv
    python -m gta6media.classify --manifest movies.json --out catalog.csv \
        --tv-offsets 16f0d2000,1811ef000 --no-tv-label
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .common import bk2_offset, load_manifest

# (label, predicate). First match wins; order matters.
DEFAULT_RULES = [
    ("Square HUD graphics", lambda m: m["width"] == m["height"]),
    ("Portrait phone video", lambda m: m["height"] > m["width"]),
    ("High-res cutscene 1440p", lambda m: m["width"] == 2560),
    ("Loading / UI loop 720p", lambda m: m["width"] == 1280 and m["duration"] < 10),
    ("Cutscene other 720p", lambda m: m["width"] == 1280),
    ("UI / short clip 1080p", lambda m: m["width"] == 1920 and m["duration"] < 30),
    ("Cutscene 1080p", lambda m: m["width"] == 1920),
]


def classify_one(m: dict, rules=DEFAULT_RULES) -> str:
    for label, pred in rules:
        try:
            if pred(m):
                return label
        except Exception:
            continue
    return f"Other {m['width']}x{m['height']}"


def build_catalog(manifest: str, tv_offsets: set[str] | None = None,
                  tv_label: str = "TV show (station logo)") -> list[dict]:
    data = load_manifest(manifest)
    tv_offsets = tv_offsets or set()
    rows = []
    for m in data:
        off = bk2_offset(Path(m["file"]).name)
        label = tv_label if off in tv_offsets else classify_one(m)
        rows.append({
            "file": Path(m["file"]).name,
            "category": label,
            "offset": m["offset"],
            "duration_sec": round(m["duration"], 2),
            "width": m["width"],
            "height": m["height"],
            "bytes": m["bytes"],
            "is_tv": off in tv_offsets,
        })
    return rows


def write_csv(rows: list[dict], out: str) -> None:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True, help="output CSV path")
    ap.add_argument("--tv-offsets", default="", help="comma-separated bk2 offsets to label as TV shows")
    ap.add_argument("--tv-label", default="TV show (station logo)")
    args = ap.parse_args()
    tv = {x.strip().lower() for x in args.tv_offsets.split(",") if x.strip()}
    rows = build_catalog(args.manifest, tv, args.tv_label)
    write_csv(rows, args.out)
    from collections import Counter
    c = Counter(r["category"] for r in rows)
    print(f"wrote {args.out}: {len(rows)} rows")
    for label, n in c.most_common():
        print(f"  {label}: {n}")


if __name__ == "__main__":
    main()
