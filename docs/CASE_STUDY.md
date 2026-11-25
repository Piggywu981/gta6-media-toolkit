# Case study: 20 clips flagged as "extraction anomalies"

A set of 20 short 1920x1080 clips was reported as suspicious because their
first frames showed grey static, color blocks and torn bands.

## Investigation

1. **Metadata check** — every file existed (3 KB–16 MB); source vs output
   resolution (1920x1080), frame count and duration matched exactly. 19 clips
   had no audio track, one had audio — matching the sources.

2. **Decoder cross-check** — an open-source Bink2 decoder produced almost
   entirely black frames from the source `.bk2` files, i.e. it could not decode
   these particular KB2n clips. The official-DLL decoder produced the same
   frames seen in the MP4s.

3. **Temporal sampling** — extracting frames at 25% / 60% / 95% of each clip
   revealed that several videos transition from abstract intro effects into
   real gameplay: a female character in a grey shirt, a group on a couch, a
   man on a phone. One clip contained an in-game parody ad ("buckme") on a
   purple background.

## Conclusion

The clips are legitimate game assets — loading transitions, screen effects,
HUD elements and in-game advertisements — not corrupt extractions. The static
and gradients are their designed content. No re-extraction was needed.

## Takeaway

Before treating an odd-looking clip as corrupt:

- compare against the source decoded with the *official* decoder,
- sample multiple timestamps, not just frame 0,
- verify metadata (resolution/frames/duration) matches the source.

The `inspect` command automates the visual part; `qc` covers integrity.
