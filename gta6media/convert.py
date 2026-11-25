"""Parallel batch converter: bk2 -> MP4 using the official-DLL decoder pipeline.

This tool drives an external ``bink2mp4.py`` (see docs/DECODER.md). It never
bundles or redistributes any proprietary DLL or game media.

Features: worker pool, resume from a result log, configurable preset/CRF,
and UTF-8 child environment (avoids Windows GBK decode failures).

Usage:
    python -m gta6media.convert --jobs jobs.json --bink2mp4 <path>/bink2mp4.py \
        --result convert-results.json --workers 7 --preset veryfast
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .common import find_ffmpeg, save_json

MIN_MP4_BYTES = 20000


def run_one(job: dict, script: str, preset: str, crf: int, timeout: int) -> tuple[dict, str]:
    mp4 = job["mp4"]
    if Path(mp4).exists() and Path(mp4).stat().st_size > MIN_MP4_BYTES:
        return job, "skip"
    env = os.environ.copy()
    ffbin = str(Path(find_ffmpeg()[0]).parent)
    env["PATH"] = ffbin + os.pathsep + env.get("PATH", "")
    env["GTA6X_PRESET"] = preset
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, script, "convert", job["bk2"], "-o", mp4,
           "--no-verify", "--crf", str(crf)]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return job, "fail"
    size = Path(mp4).stat().st_size if Path(mp4).exists() else 0
    return job, ("ok" if p.returncode == 0 and size > MIN_MP4_BYTES else "fail")


def convert_all(jobs: list[dict], script: str, result_path: str,
                workers: int = 7, preset: str = "veryfast", crf: int = 23,
                timeout: int = 1200) -> dict:
    results = []
    if Path(result_path).exists():
        try:
            results = json.load(open(result_path, encoding="utf-8"))
        except Exception:
            results = []
    done = {r["bk2"] for r in results if r.get("status") in ("ok", "skip")}
    todo = [j for j in jobs if j["bk2"] not in done]
    print(f"total={len(jobs)} done={len(done)} todo={len(todo)}", flush=True)

    lock = threading.Lock()
    counts = {"ok": 0, "skip": 0, "fail": 0}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(run_one, j, script, preset, crf, timeout) for j in todo]
        for n, fut in enumerate(as_completed(futures), 1):
            job, status = fut.result()
            counts[status] += 1
            with lock:
                results.append({
                    "bk2": job["bk2"], "mp4": job["mp4"],
                    "category": job.get("category"), "status": status,
                })
                if n % 10 == 0 or n == len(todo):
                    save_json(results, result_path)
            if n % 20 == 0 or n == len(todo):
                print(f"{n}/{len(todo)} ok={counts['ok']} skip={counts['skip']} "
                      f"fail={counts['fail']} elapsed={time.time()-t0:.0f}s", flush=True)
    save_json(results, result_path)
    counts["total_elapsed_s"] = round(time.time() - t0)
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--bink2mp4", required=True, help="path to external bink2mp4.py")
    ap.add_argument("--result", required=True)
    ap.add_argument("--workers", type=int, default=7)
    ap.add_argument("--preset", default="veryfast",
                    help="libx264 preset (veryfast/medium/...) - requires patched bink2mp4.py")
    ap.add_argument("--crf", type=int, default=23)
    ap.add_argument("--timeout", type=int, default=1200)
    args = ap.parse_args()
    jobs = json.load(open(args.jobs, encoding="utf-8"))
    stats = convert_all(jobs, args.bink2mp4, args.result,
                        args.workers, args.preset, args.crf, args.timeout)
    print(f"DONE {stats}")


if __name__ == "__main__":
    main()
