"""Organize carved bk2 files into per-category folders and emit a convert job list.

Usage:
    python -m gta6media.extract --catalog catalog.csv --source _all_movies \
        --out other_videos --jobs jobs.json --skip-category "TV show (station logo)"
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import defaultdict
from pathlib import Path

from .common import safe_folder, save_json


def organize(catalog: str, source: str, out: str, jobs_out: str,
             skip_categories: set[str] | None = None,
             copy: bool = True) -> list[dict]:
    skip_categories = skip_categories or set()
    with open(catalog, "r", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    groups = defaultdict(list)
    for r in rows:
        if r["category"] in skip_categories:
            continue
        groups[r["category"]].append(r)

    jobs = []
    for cat, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        folder = safe_folder(cat)
        bk2_dir = Path(out) / folder / "bk2"
        mp4_dir = Path(out) / folder / "mp4"
        bk2_dir.mkdir(parents=True, exist_ok=True)
        mp4_dir.mkdir(parents=True, exist_ok=True)
        for r in items:
            src = Path(source) / r["file"]
            dst = bk2_dir / r["file"]
            if copy and not dst.exists():
                shutil.copy2(src, dst)
            jobs.append({
                "bk2": str(dst),
                "mp4": str(mp4_dir / (Path(r["file"]).stem + ".mp4")),
                "category": cat,
                "folder": folder,
                "duration": float(r["duration_sec"]),
                "width": int(r["width"]),
                "height": int(r["height"]),
            })
    save_json(jobs, jobs_out)
    return jobs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--source", required=True, help="directory holding carved .bk2 files")
    ap.add_argument("--out", required=True, help="output root for organized folders")
    ap.add_argument("--jobs", required=True, help="output convert-jobs JSON")
    ap.add_argument("--skip-category", action="append", default=[],
                    help="category label to skip (repeatable)")
    ap.add_argument("--link", action="store_true", help="hardlink instead of copy")
    args = ap.parse_args()
    jobs = organize(args.catalog, args.source, args.out, args.jobs,
                    set(args.skip_category), copy=not args.link)
    print(f"organized {len(jobs)} files -> {args.out}")
    print(f"jobs written -> {args.jobs}")


if __name__ == "__main__":
    main()
