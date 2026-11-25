"""Shared helpers for the gta6-media toolkit."""

from __future__ import annotations

import json
import os
import re
import struct
from pathlib import Path

# Bink2 header: magic "KB2" + version char, then 8 little-endian u32 fields.
HDR_FMT = "<8I"
BK2_NAME_RE = re.compile(r"movies_bink2_([0-9a-fA-F]+)\.bk2$")


def load_manifest(path: str | os.PathLike) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(obj, path: str | os.PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)


def bk2_offset(filename: str) -> str | None:
    m = BK2_NAME_RE.search(filename)
    return m.group(1).lower() if m else None


def read_bk2_header(path: str | os.PathLike) -> dict:
    with open(path, "rb") as fh:
        magic = fh.read(4)
        rest = fh.read(32)
    if len(magic) < 4 or magic[:3] != b"KB2":
        raise ValueError(f"not a Bink2 file: {path}")
    v = struct.unpack(HDR_FMT, rest[:32])
    codec = magic[3:4].decode("latin-1")
    return {
        "codec": codec,
        "declared_size": v[0],
        "frames": v[1],
        "largest_frame": v[2],
        "frames2": v[3],
        "width": v[4],
        "height": v[5],
        "fps": v[6],
        "flags": v[7],
    }


def safe_folder(name: str) -> str:
    """Turn a category label into a filesystem-safe folder name."""
    s = name.replace("/", "_").replace("\\", "_")
    s = s.replace("(", "").replace(")", "").replace(" ", "")
    return re.sub(r'[<>:"|?*]', "", s)


def find_ffmpeg() -> tuple[str, str]:
    """Return (ffmpeg, ffprobe) absolute paths from PATH."""
    from shutil import which

    ff, fp = which("ffmpeg"), which("ffprobe")
    if not ff or not fp:
        raise RuntimeError("ffmpeg and ffprobe must be on PATH")
    return ff, fp
