# Full workflow walkthrough

This document walks through organizing a full `movies.rpf` carve (~500 clips)
into a browsable MP4 library.

## 0. Prerequisites

- Python 3.10+, `ffmpeg` + `ffprobe` on `PATH`
- A carved manifest `movies.json` and its `.bk2` files (from `gta6x movies`)
- An external official-DLL decoder (see [DECODER.md](DECODER.md))

## 1. Inventory

```bash
python -m gta6media inventory --manifest _all_movies/movies.json
```

Reports totals, resolution histogram, duration buckets and orientation. In the
reference run this showed 515 clips / 8.2 GiB / 236 minutes, dominated by short
720p loops and 1080p cutscenes.

## 2. Classify

```bash
python -m gta6media classify \
  --manifest _all_movies/movies.json \
  --out catalog.csv \
  --tv-offsets <comma-separated offsets>
```

Assigns one of: `TV show (station logo)`, `Square HUD graphics`,
`Portrait phone video`, `High-res cutscene 1440p`, `Loading / UI loop 720p`,
`Cutscene other 720p`, `UI / short clip 1080p`, `Cutscene 1080p`, or
`Other WxH`. `--tv-offsets` is optional; supply offsets you have positively
identified (e.g. by an on-screen station logo).

## 3. Extract / organize

```bash
python -m gta6media extract \
  --catalog catalog.csv --source _all_movies \
  --out organized --jobs jobs.json \
  --skip-category "TV show (station logo)"
```

For each category a folder `<out>/<safe_label>/{bk2,mp4}/` is created. Clips are
copied (use `--link` for hardlinks) and a `jobs.json` is emitted for conversion.

## 4. Convert

```bash
python -m gta6media convert \
  --jobs jobs.json --bink2mp4 /path/to/bink2mp4.py \
  --result results.json --workers 7 --preset veryfast
```

- Workers run in parallel; each child calls `bink2mp4.py convert`.
- Progress is printed every 20 jobs.
- Results are checkpointed every 10 jobs; re-running skips completed items.
- `--preset veryfast` roughly halves encode time versus `medium`. It requires
  the preset patch; omit it otherwise.

In the reference run, 493 clips completed in about 10 minutes on 24 cores with
7 workers. Eight very short `KB2j` clips hit transient failures under load and
were recovered by re-running them individually.

## 5. QC

```bash
python -m gta6media qc --jobs jobs.json --report qc.json --audio-check
```

Checks every output for: file presence, a valid video stream, audio-stream
presence, and (with `--audio-check`) mean volume. Reference result: 493/493
valid video streams, 174 with audio, 319 without (UI/silent sources), zero
clipped tracks.

## 6. Inspect suspicious clips

```bash
python -m gta6media inspect frames --input clip.mp4 --out frames/ --count 9
python -m gta6media inspect sheet --frames frames/ --out contact.png --cols 5
```

If a clip looks like static or color blocks, compare against the decoded source
frame before calling it corrupt. In the reference investigation, 20 flagged
clips turned out to be legitimate loading/HUD/ad content: the official-DLL
source frames matched the MP4 frames exactly, and several clips contained real
gameplay characters in their middle sections. See
[`CASE_STUDY.md`](CASE_STUDY.md).

## Notes on scale

- Disk: budget roughly the carve size again for MP4 output.
- Concurrent workers load one decoder per child process; 7 is a safe default on
  a 24-core machine with ~16 GB RAM.
- The toolkit never modifies source `.bk2` files.
