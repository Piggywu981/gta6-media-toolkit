"""Visual inspection helpers: extract frames and build contact sheets.

Useful for verifying that a suspicious clip actually contains source content
rather than a decode failure.

Usage:
    python -m gta6media.inspect frames --input clip.mp4 --out frames/ --count 9
    python -m gta6media.inspect sheet --frames frames/ --out contact.png --cols 5
    python -m gta6media.inspect best --raw clip.i420 --w 1920 --h 1080 \
        --samples 10 --out best.png
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from .common import find_ffmpeg


def extract_frames(video: str, out_dir: str, count: int = 9, width: int = 320) -> list[str]:
    ffmpeg, _ = find_ffmpeg()
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    outputs = []
    for i in range(count):
        dst = str(d / f"frame_{i+1:02d}.png")
        # seek to even spacing using -ss before -i (fast)
        cmd = [ffmpeg, "-y", "-v", "error", "-i", video,
               "-vf", f"select='not(mod(n\\,{max(1,count)}))',scale={width}:-1",
               "-vsync", "vfr", "-frames:v", "1", dst]
        # simpler: use fps filter sampling
        cmd = [ffmpeg, "-y", "-v", "error", "-i", video,
               "-vf", f"fps={count}/1,scale={width}:-1",
               "-frames:v", "1", dst]
        subprocess.run(cmd, capture_output=True)
        if Path(dst).exists():
            outputs.append(dst)
    return outputs


def build_sheet(frames_dir: str, out: str, cols: int = 5, cell: str = "320x180") -> None:
    ffmpeg, _ = find_ffmpeg()
    frames = sorted(Path(frames_dir).glob("*.png"))
    if not frames:
        raise RuntimeError(f"no PNG frames in {frames_dir}")
    list_file = Path(frames_dir) / "_concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in frames),
        encoding="utf-8",
    )
    w, h = cell.split("x")
    rows = (len(frames) + cols - 1) // cols
    cmd = [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0",
           "-i", str(list_file), "-vf", f"scale={w}:{h},tile={cols}x{rows}",
           "-frames:v", "1", out]
    subprocess.run(cmd, capture_output=True)
    print(f"sheet -> {out} ({len(frames)} frames)")


def best_raw_frame(raw: str, w: int, h: int, samples: int, out: str) -> None:
    """Pick the frame with the widest chroma variety from a raw I420 dump."""
    ffmpeg, _ = find_ffmpeg()
    fb = w * h * 3 // 2
    data = Path(raw).read_bytes()
    total = len(data) // fb
    if total == 0:
        raise RuntimeError("empty raw I420 file")
    indices = sorted({min(total - 1, int(total * f)) for f in
                      [i / (samples + 1) for i in range(1, samples + 1)]})
    best_fn, best_score = 0, -1
    for fn in indices:
        uv = data[fn * fb + w * h: (fn + 1) * fb]
        score = len(set(uv[::32]))
        if score > best_score:
            best_fn, best_score = fn, score
    tmp = Path(out).with_suffix(".i420.tmp")
    tmp.write_bytes(data[best_fn * fb: (best_fn + 1) * fb])
    subprocess.run([ffmpeg, "-y", "-v", "error", "-f", "rawvideo",
                    "-pix_fmt", "yuv420p", "-s", f"{w}x{h}", "-i", str(tmp),
                    "-vf", "scale=320:180", "-frames:v", "1", out],
                   capture_output=True)
    tmp.unlink(missing_ok=True)
    print(f"best frame {best_fn}/{total} (chroma variety={best_score}) -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("frames")
    f.add_argument("--input", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--count", type=int, default=9)
    f.add_argument("--width", type=int, default=320)

    s = sub.add_parser("sheet")
    s.add_argument("--frames", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--cols", type=int, default=5)
    s.add_argument("--cell", default="320x180")

    b = sub.add_parser("best")
    b.add_argument("--raw", required=True)
    b.add_argument("--w", type=int, required=True)
    b.add_argument("--h", type=int, required=True)
    b.add_argument("--samples", type=int, default=10)
    b.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "frames":
        outs = extract_frames(args.input, args.out, args.count, args.width)
        print(f"extracted {len(outs)} frames -> {args.out}")
    elif args.cmd == "sheet":
        build_sheet(args.frames, args.out, args.cols, args.cell)
    elif args.cmd == "best":
        best_raw_frame(args.raw, args.w, args.h, args.samples, args.out)


if __name__ == "__main__":
    main()
