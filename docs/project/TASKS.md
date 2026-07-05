# TASKS.md

> **⚠️ This file is superseded.** Active planning, findings, and progress now live in
> [`CODEBASE_REVIEW_AND_ROADMAP.md`](CODEBASE_REVIEW_AND_ROADMAP.md) (created 2026-07-05).
> Check that file for the current roadmap and where work left off.

## Historical summary (pre-2026)

The transcription repetition bug was resolved with a three-layer solution
(audio splitting with overlap, Whisper parameter tuning, text deduplication).
22 completed tasks from that effort are archived in
[`ARCHIVED_TASKS.md`](ARCHIVED_TASKS.md).

## Status as of 2026-07-05

- **Phase 1 done** — audio quality pass (loudness normalization for quiet audio),
  WAV 16kHz mono intermediate, robust language auto-detection (es/pt fix)
- **Phase 2 done** — subtitle export correctness fixes (word-timestamp sampling,
  line breaks, overlap clamps, phantom formats, return types)
- **Phase 3 done** — cleanup sweep (dead code removed, faster-whisper-only,
  requirements fixed, docs updated, test suite repaired)
- **Phase 4 done** — UI robustness (thread safety, real mid-file cancel/pause,
  graceful shutdown, aggregated error reporting)
- **Phase 5 done** — translation quality (per-segment batched translation,
  pt→en ROMANCE model, ASS style preservation, transformers 5.x compatibility fix)

**All roadmap phases complete as of 2026-07-05.** Remaining: validate es/pt
transcription with a real user sample. See the roadmap doc for details,
bug IDs, and verification notes.
