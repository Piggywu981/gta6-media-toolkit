"""Inventory a carved Bink2 manifest: resolution, duration and orientation stats.

Usage:
    python -m gta6media.inventory --manifest movies.json
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from .common import load_manifest

DURATION_BUCKETS = [
    (0, 2, "<2s"), (2, 5, "2-5s"), (5, 10, "5-10s"),
    (10, 30, "10-30s"), (30, 60, "30-60s"), (60, 120, "1-2min"),
    (120, 180, "2-3min"), (180, 300, "3-5min"), (300, float("inf"), ">5min"),
]


def summarize(manifest: str) -> dict:
    data = load_manifest(manifest)
    res = Counter((m["width"], m["height"]) for m in data)
    dur = Counter()
    for m in data:
        d = m["duration"]
        for lo, hi, label in DURATION_BUCKETS:
            if lo <= d < hi:
                dur[label] += 1
                break
    portrait = sum(1 for m in data if m["height"] > m["width"])
    square = sum(1 for m in data if m["height"] == m["width"])
    return {
        "total": len(data),
        "total_bytes": sum(m["bytes"] for m in data),
        "total_duration_s": sum(m["duration"] for m in data),
        "resolutions": res,
        "durations": dur,
        "portrait": portrait,
        "square": square,
        "landscape": len(data) - portrait - square,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="movies.json from gta6x movies extraction")
    args = ap.parse_args()
    s = summarize(args.manifest)
    print(f"TOTAL {s['total']} files, {s['total_bytes']/1e6:.0f} MB, "
          f"{s['total_duration_s']:.0f}s ({s['total_duration_s']/60:.1f} min)")
    print("\nRESOLUTIONS")
    for (w, h), n in s["resolutions"].most_common(20):
        print(f"  {w}x{h}: {n}")
    print("\nDURATIONS")
    for _, _, label in DURATION_BUCKETS:
        print(f"  {label}: {s['durations'][label]}")
    print(f"\nORIENTATION  landscape={s['landscape']}  portrait={s['portrait']}  square={s['square']}")


if __name__ == "__main__":
    main()
