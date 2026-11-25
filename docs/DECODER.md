# Bink2 decoder notes

## Two ways to decode `.bk2`

Two Bink2 decoders were evaluated while building this toolkit.

### 1. Open-source ffmpeg path (video only)

Some ffmpeg builds (for example the one bundled with `vice-lens`, `vl-2`)
include a clean-room `bink2video` decoder. It extracts frames reliably and is
fine for **thumbnails and visual inspection**.

However, its `binkaudio_dct` decoder was found to produce **broken audio** on
the tested build: `volumedetect` reported `mean_volume = 0.0 dB`,
`max_volume = 0.0 dB`, with a DC offset around -13 to -31 and peaks near
126 dB — i.e. clipped noise, not sound.

### 2. Official DLL path (video + correct audio)

The reliable path drives the game's own `Bink2Scarlett.dll` through a small
host and muxes the decoded PCM with the video. The project
[`gta6-video-reader`](https://github.com/hoshino-114514/gta6-video-reader)
provides such a host (`bink2mp4.py` plus a C source you compile yourself).

Observed with the official decoder:

```
mean_volume: -18.8 dB   max_volume: -1.7 dB   DC offset ~ 0
```

That is a normal audio track. **Use this path for final MP4 output.**

## Recommended setup

1. Obtain `bink2mp4.py` from the upstream project above.
2. Compile its decode host with MinGW-w64 (see its `references/pipeline.md`).
   Place `Bink2Scarlett.dll`, the host `.exe`, its allocator stub and the VC++
   runtime DLLs in the directory the host expects (it loads them from CWD).
3. Apply [`../patches/bink2mp4-preset.patch`](../patches/bink2mp4-preset.patch)
   so the script honors the `GTA6X_PRESET` environment variable. This lets
   `gta6media convert --preset veryfast` work. Skip this step if you only use
   the default `medium`.
4. Ensure `ffmpeg`/`ffprobe` are on `PATH`.

The `gta6media convert` command calls:

```
python bink2mp4.py convert <input.bk2> -o <output.mp4> --no-verify --crf N
```

`--no-verify` avoids a known Windows GBK-decoding crash in the upstream script's
verify step; the toolkit performs its own independent QC afterwards.

## Verifying audio health

```bash
python -m gta6media qc --jobs jobs.json --report qc.json --audio-check
```

Healthy: roughly `-15 .. -25 dB`, peak below 0 dB, near-zero DC offset.
Broken: `0.0 dB` with a large DC offset — re-decode with the official DLL.
Digital silence (`<= -85 dB`) can be legitimate for UI/HUD clips with no sound.

## Ethics / scope

This tooling is for organizing media from a package the operator lawfully
possesses. Do not redistribute game media or the proprietary DLL. This repo
contains neither.
