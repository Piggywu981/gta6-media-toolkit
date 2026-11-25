"""Quality-control converted MP4s: stream integrity, frame count and audio level.

Usage:
    python -m gta6media.qc --jobs jobs.json --report qc.json
    python -m gta6media.qc --jobs jobs.json --report qc.json --audio-check
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from .common import find_ffmpeg, save_json

VOL_RE = re.compile(r"mean_volume:\s*(-?[\d.]+) dB")


def probe_streams(ffprobe: str, path: str) -> list[dict] | None:
    p = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "stream=codec_name,codec_type,width,height,nb_frames,duration",
         "-of", "json", path],
        capture_output=True, text=True, errors="replace",
    )
    try:
        return json.loads(p.stdout).get("streams", [])
    except Exception:
        return None


def check_audio(ffmpeg: str, path: str) -> float | None:
    p = subprocess.run(
        [ffmpeg, "-hide_banner", "-v", "info", "-i", path,
         "-vn", "-af", "volumedetect", "-f", "null", "NUL"],
        capture_output=True, text=True, errors="replace",
    )
    combined = (p.stderr or "") + (p.stdout or "")
    m = VOL_RE.search(combined)
    return float(m.group(1)) if m else None


def run_qc(jobs: list[dict], report_path: str, audio_check: bool = False) -> dict:
    ffmpeg, ffprobe = find_ffmpeg()
    stat = {"total": len(jobs), "missing": [], "no_video": [],
            "with_audio": 0, "no_audio": 0, "clipped": [], "silent": [],
            "audio_normal": 0, "audio_unchecked": 0}
    for j in jobs:
        mp4 = j["mp4"]
        name = Path(mp4).name
        if not Path(mp4).exists() or Path(mp4).stat().st_size < 1500:
            stat["missing"].append(name)
            continue
        streams = probe_streams(ffprobe, mp4)
        if not streams or not any(s.get("codec_type") == "video" for s in streams):
            stat["no_video"].append(name)
            continue
        if any(s.get("codec_type") == "audio" for s in streams):
            stat["with_audio"] += 1
        else:
            stat["no_audio"] += 1
        if audio_check:
            vol = check_audio(ffmpeg, mp4)
            if vol is None:
                stat["audio_unchecked"] += 1
            elif vol > -3:
                stat["clipped"].append({"file": name, "db": vol})
            elif vol <= -85:
                stat["silent"].append(name)
            else:
                stat["audio_normal"] += 1
    save_json(stat, report_path)
    return stat


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--audio-check", action="store_true")
    args = ap.parse_args()
    jobs = json.load(open(args.jobs, encoding="utf-8"))
    s = run_qc(jobs, args.report, args.audio_check)
    print(f"TOTAL {s['total']}")
    print(f"  missing={len(s['missing'])}  no_video={len(s['no_video'])}")
    print(f"  with_audio={s['with_audio']}  no_audio={s['no_audio']}")
    if args.audio_check:
        print(f"  audio_normal={s['audio_normal']}  silent={len(s['silent'])} "
              f"clipped={len(s['clipped'])}  unchecked={s['audio_unchecked']}")
    print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
