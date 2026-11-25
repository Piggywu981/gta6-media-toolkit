# gta6-media-toolkit

A small, dependency-free Python toolkit for **inventorying, classifying,
organizing, transcoding and quality-checking carved Bink2 media** from a GTA VI
(Xbox Series, RAGE 9 / RPF9) package.

> This repository contains **only original toolkit code and documentation**.
> It ships **no game media, no proprietary DLLs and no decryption keys**. All
> tools operate on files the operator already owns, read-only with respect to
> the source package.

---

## Why this exists

RPF9 archives store movies in `movies.rpf` as Bink2 (`.bk2`) streams. The
archive table of contents is AES-encrypted and its key is not public, so
original filenames are unavailable. Tools such as
[`gta6-explorer`](https://github.com/HolyRoses/gta6-explorer) carve the raw
streams by header scanning. That yields files like
`movies_bink2_143205000.bk2` — correct bytes, but no semantic names.

This toolkit adds the missing downstream steps:

1. **Inventory** — count and describe what was carved.
2. **Classify** — heuristically bucket clips by resolution/duration.
3. **Extract** — copy clips into per-category folders and build a job list.
4. **Convert** — batch-transcode `.bk2` to MP4 in parallel, with resume.
5. **QC** — verify stream integrity, frame counts and audio levels.
6. **Inspect** — visual frame/contact-sheet diagnostics for suspicious clips.

---

## Install

Requires Python 3.10+ and `ffmpeg`/`ffprobe` on `PATH`. No third-party Python
packages are needed.

```bash
git clone <this-repo> gta6-media-toolkit
cd gta6-media-toolkit
python -m gta6media --version
```

### External decoder

Transcoding needs an external `bink2mp4.py` that can decode Bink2. See
[`docs/DECODER.md`](docs/DECODER.md). The toolkit drives it as a subprocess; it
does not vendor it.

---

## Tools

All tools are reachable through one entry point:

```bash
python -m gta6media <command> --help
```

| Command | Purpose |
|---|---|
| `inventory` | Resolution / duration / orientation statistics for a manifest |
| `classify` | Assign a content-bucket label to each clip, write CSV |
| `extract` | Organize `.bk2` files into category folders + jobs JSON |
| `convert` | Parallel `.bk2` → MP4 with resume and result log |
| `qc` | ffprobe integrity check + optional loudness check |
| `inspect` | Extract frames, build contact sheets, pick best raw frame |

---

## Typical workflow

Assume `movies.json` came from `gta6x movies --full --out _all_movies`.

```bash
# 1. see what is in the archive
python -m gta6media inventory --manifest _all_movies/movies.json

# 2. classify (optionally mark known TV-show offsets)
python -m gta6media classify \
  --manifest _all_movies/movies.json \
  --out catalog.csv \
  --tv-offsets 16f0d2000,1811ef000

# 3. organize clips by category (skip TV shows if handled separately)
python -m gta6media extract \
  --catalog catalog.csv \
  --source _all_movies \
  --out organized \
  --jobs jobs.json \
  --skip-category "TV show (station logo)"

# 4. transcode in parallel
python -m gta6media convert \
  --jobs jobs.json \
  --bink2mp4 /path/to/bink2mp4.py \
  --result convert-results.json \
  --workers 7 --preset veryfast

# 5. quality-check
python -m gta6media qc \
  --jobs jobs.json --report qc.json --audio-check

# 6. inspect a suspicious clip visually
python -m gta6media inspect frames --input clip.mp4 --out frames/ --count 9
python -m gta6media inspect sheet --frames frames/ --out contact.png --cols 5
```

See [`examples/`](examples/) for sample CSV/JSON shapes and
[`docs/WORKFLOW.md`](docs/WORKFLOW.md) for a fuller walkthrough.

---

## Important notes

- **Classification is heuristic.** RPF9 has no recoverable original names, so
  labels describe visual shape (resolution/duration), not an official catalog.
- **Short/UI clips may look like noise.** Loading transitions, HUD graphics and
  in-game ads legitimately contain static, gradients and color blocks. Use
  `inspect` and compare source frames before concluding a clip is corrupt.
- **Audio must come from the official decoder.** The open-source Bink audio
  decoder in some ffmpeg builds produces clipped, DC-offset garbage. Verify a
  converted file with `qc --audio-check`: a healthy track reads roughly
  `-15 .. -25 dB`; a broken one reads `0.0 dB` with large DC offset. See
  [`docs/DECODER.md`](docs/DECODER.md).
- **`--preset` requires a patched `bink2mp4.py`.** Stock versions hard-code
  `medium`. Apply the tiny patch in [`patches/`](patches/) to honor
  `GTA6X_PRESET`, or just omit `--preset` in the toolkit.

---

## License

MIT — see [`LICENSE`](LICENSE). Applies to this toolkit's code and docs only.
