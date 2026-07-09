# Codebase Review & Improvement Roadmap

**Created:** 2026-07-05
**Status:** Planning complete — execution not yet started
**Context:** Full in-depth codebase review performed after re-cloning the repo. This document is the single source of truth for what was found, what we decided, and where execution stands. Future sessions/agents: read this first, update the checkboxes as you go.

---

## 1. Background & User Goals

The user's two driving requests:

1. **Reliable SRT/subtitle export** — the feature *already exists* (UI checkbox → SRT/VTT/ASS via `process_video_with_subtitles`), but has correctness bugs that degrade output.
2. **Better recognition for Spanish/Portuguese** — past results were poor. User hypothesized low audio volume might be the cause and suggested an "audio quality pass" (boost dB when audio is too quiet) before transcription.

### Root-cause analysis for poor es/pt recognition (ranked by likelihood)

| # | Suspect | Detail | Evidence |
|---|---------|--------|----------|
| 1 | **Fragile language auto-detection** | Default language is "Auto-detect". In the VAD path, language is detected from the **first speech region only** (often seconds long, possibly music/noise/English intro) and then **locked in for the entire file**. Misdetection → every subsequent word transcribed with wrong language token → garbage. | `src/transcription/enhanced_whisper_manager.py:217-229` |
| 2 | **Quiet audio breaks VAD + detection** | VAD threshold 0.3 decides which regions are transcribed at all. Quiet speech → regions missed entirely. Low volume also degrades Whisper's 30-second language detection more than it degrades transcription itself. **This is where the user's volume theory is correct.** | `src/transcription/enhanced_whisper_manager.py:30` (threshold), `src/audio_processing/vad_manager.py` |
| 3 | **Lossy MP3 intermediate** | Converter extracts audio to MP3 44.1kHz (lossy re-encode) before Whisper, which internally wants 16kHz mono. WAV/FLAC 16kHz mono would be lossless AND faster. | `src/audio_processing/converter.py:244` |
| 4 | **Spanish-tuned heuristics, limited scope** | `SmartTimingEstimator` speech-rate constants and phrase-boundary word lists are Spanish+English only — affects subtitle timing quality for other languages. | `src/subtitles/smart_timing_estimator.py:15,139` |

### Decision on the "audio quality pass"

**Approved approach:** implement inside the existing ffmpeg conversion step (`AudioConverter`):
- Two-pass: first measure loudness (ffmpeg `loudnorm` analysis, EBU R128).
- **Only if below threshold** (integrated loudness < ~−24 LUFS) apply normalization + gentle highpass (~80Hz, removes rumble that confuses VAD).
- Nearly zero added processing time; one ffmpeg filter chain.
- Note: `src/audio_processing/optimizer.py` is an **empty 1-line stub** — someone planned this and never built it. That's the natural home for this logic.

---

## 2. Full Findings Inventory

### 2.1 Correctness bugs (affect output quality today)

| ID | Bug | Location | Impact |
|----|-----|----------|--------|
| B1 | Word-timestamp availability decided by sampling **only first 5 segments**; if early segments lack `words` (music, merged), whole file falls back to heuristic timing even when word data exists later | `src/subtitles/subtitle_generator.py:112` | Subtitle sync silently degrades |
| B2 | Language locked in from first VAD region for whole file (see root-cause #1) | `src/transcription/enhanced_whisper_manager.py:217-229` | es/pt garbage transcripts |
| B3 | Word-based generator emits raw `\n` instead of pysubs2's `\N` in `SSAEvent.text` | `src/subtitles/word_based_subtitle_generator.py:245` | Line breaks mangled per format |
| B4 | Min-duration extension can push cue past next cue's start (overlapping subtitles); other clamps can produce `end < start` | `src/subtitles/word_based_subtitle_generator.py:199-203`, `src/subtitles/smart_timing_estimator.py:112-114` | Overlapping/invalid cues |
| B5 | Live translation path translates 7-segment window as paragraph, splits on punctuation, takes "middle sentence" when counts mismatch → dropped/duplicated/misassigned translations. Also does 2N+1 redundant translation work per file | `src/translation/engines/helsinki_translator.py:477-580` (esp. `:554-555`) | Translation quality |
| B6 | No direct pt→en Helsinki model — Portuguese falls to lower-quality multilingual `mul-en` model | `src/translation/engines/helsinki_translator.py:21-42` | pt→en translation quality |
| B7 | TTML/SAMI advertised in `SUPPORTED_FORMATS` but pysubs2 can't write them; exception swallowed, format maps to `None` silently | `src/subtitles/subtitle_generator.py:17-24,329-341` | Silent feature failure |
| B8 | `WordBasedSubtitleGenerator.generate_from_segments` returns `None` when no words found; callers expect `Path` | `src/subtitles/word_based_subtitle_generator.py:84` | Potential crash |
| B9 | In multi-chunk text-only path (`process_video`), each chunk auto-detects language independently — language can flip mid-transcript | `src/transcription/transcription_pipeline.py:236-259` | Inconsistent transcripts |
| B10 | ASS style preserved by name only — translated subtitle files reference undefined styles | `src/translation/subtitle_translator.py:286-287` | Broken ASS styling |

### 2.2 UI / threading bugs

| ID | Bug | Location | Impact |
|----|-----|----------|--------|
| U1 | Main window reads private `queue_manager._queue` from GUI thread **without lock** while worker mutates it | `src/ui/main_window.py:741,787-791,941-952,993` | Race conditions |
| U2 | `QThread.terminate()` on close force-kills mid-FFmpeg/mid-inference; `stop()` flag only checked between files so `wait(3000)` almost always times out → terminate is the common path | `src/ui/main_window.py:684-686` | Corrupt state, leaked temp files |
| U3 | Pause is cosmetic mid-file: only halts between-files loop; processing continues, progress updates silently dropped | `src/ui/worker.py:72-75,90-92` | Misleading UX, wasted compute |
| U4 | Throwaway `SubtitleTranslator` constructed in worker `__init__` **on GUI thread** (model load can freeze UI), then never used — fresh one created per file per format | `src/ui/worker.py:44-56,175-191` | UI freeze + wasted loads |
| U5 | Same translation model reloaded per subtitle format per file (SRT+VTT+ASS = 3 full loads) | `src/ui/worker.py:181-184` | Slow batch processing |
| U6 | Modal `QMessageBox.critical` per failed file while worker continues — dialog storm on failing batches | `src/ui/main_window.py:1005` | UX |
| U7 | UI advertises TowerInstruct GPU translation for pt→en, but Tower is permanently disabled via `if False` in the translator | `src/ui/main_window.py:1327-1331` vs `src/translation/subtitle_translator.py:68` | Misleading UI |
| U8 | `handle_all_completed` drops worker reference without waiting for thread cleanup | `src/ui/main_window.py:925-927` | "QThread destroyed while running" risk |

### 2.3 Loose ends / dead code / drift

| ID | Item | Location |
|----|------|----------|
| D1 | `openai-whisper` imported but **not in requirements.txt** — `whisper_manager.py` + 2 test modules fail to import; app survives via silent try/except fallback to faster-whisper | `src/transcription/whisper_manager.py:3`, `tests/test_repetition_fix/test_whisper_configuration.py`, `tests/test_transcription/test_whisper_manager.py` |
| D2 | `src/ui/main_window_old.py` — 690 lines of dead legacy UI, imported by nothing | |
| D3 | Empty 0-byte stubs never imported: `src/ui/progress_widget.py`, `src/ui/queue_widget.py`, `src/ui/upload_widget.py`; near-empty `src/audio_processing/optimizer.py` (1 line — will become the audio quality pass) | |
| D4 | TowerInstruct translator: 487 lines permanently disabled (`if False and source_lang == 'pt'`), comment says "too slow (10+ min for 87 segments)" | `src/translation/subtitle_translator.py:68`, `src/translation/engines/tower_translator.py` |
| D5 | `LanguageDetector` class never used — `SubtitleTranslator._detect_language` reimplements inline with langdetect | `src/translation/utils/language_detector.py` |
| D6 | `SubtitleTimingFixer` + `WordLevelAnalyzer` constructed but never invoked; `use_word_level_optimization` flag is decorative | `src/subtitles/subtitle_generator.py:49,58` |
| D7 | ~8 abandoned method iterations: `translate_with_context`, `translate_with_context_fixed`, `translate_segments_with_smart_context`, `batch_translate` (helsinki), `translate_from_segments_data` (subtitle_translator), `adjust_timing`, `merge_short_segments`, `detect_sync_offset` (subtitle_generator), `estimate_phrase_boundaries` (smart_timing_estimator), `wait_with_timeout` (worker) | various |
| D8 | `print("DEBUG: ...")` noise throughout production code | `src/ui/worker.py:141-221`, `src/translation/subtitle_translator.py`, `src/translation/engines/helsinki_translator.py`, `src/transcription/*` |
| D9 | **CLAUDE.md is stale**: still says "Forces English" (false — 46-language dropdown + auto-detect exists), "MoviePy" (false — ffmpeg-python is used), branch "clean-pyqt6-app" (repo is on master) | `CLAUDE.md:97,133,150` |
| D10 | TASKS.md last updated 2025-08-06, doesn't reflect current state | `docs/project/TASKS.md` |
| D11 | `requirements.txt` pins `audioop-lts>=0.2.2` unconditionally but it requires Python 3.13+; venv is 3.12 where stdlib audioop still exists. Needs environment marker: `audioop-lts>=0.2.2; python_version >= "3.13"` | `requirements.txt:10` |
| D12 | Unused imports (`QThread`, `QFont` in main_window; `json`, `math` elsewhere); dead attribute `self.custom_model_path`; copy-paste residue comments | various |

### 2.4 Test suite state (as of 2026-07-05, venv Python 3.12.7)

- **43 passed, 3 failed, 2 modules fail collection**
- Collection errors: `test_whisper_configuration.py`, `test_whisper_manager.py` — `ModuleNotFoundError: No module named 'whisper'` (see D1)
- Failures: 3 integration tests in `tests/test_repetition_fix/test_integration.py` feed synthetic invalid MP3 data → `av.error.InvalidDataError` (tests create fake MP3s that faster-whisper/PyAV rejects)

---

## 3. Execution Roadmap

Work through phases in order. Check items off as completed. Each phase should end with tests passing + a manual verification where feasible.

### Phase 1 — Language handling + audio quality pass (the es/pt fix) 🎯 ✅ DONE 2026-07-05
- [x] **1.1** Audio quality pass implemented in `src/audio_processing/optimizer.py` (`AudioQualityOptimizer`), wired into `AudioConverter.convert_video_to_audio` (on by default, `enable_quality_pass=True`):
  - Two-pass ffmpeg `loudnorm`: analysis pass (JSON), then conditional highpass(80Hz)+loudnorm with measured values (`linear=true`)
  - Threshold −24 LUFS, target −16 LUFS; silence (`-inf`) and analysis failures leave audio untouched (never blocks transcription)
  - Report exposed via `converter.get_last_quality_report()`
- [x] **1.2** Intermediate audio switched MP3 → **WAV 16kHz mono PCM** (`AudioConverter.AUDIO_SUFFIX`); extension checks in `whisper_manager.py` accept `.wav`/`.mp3`; split part files inherit source suffix; cleanup globs both; splitting is now **duration-based** (`max_duration_seconds=1500` ≈ 25 min) instead of size-based
- [x] **1.3** Robust language detection:
  - VAD path: `EnhancedWhisperManager._detect_language_robust()` detects on the **longest** speech region (up to 30s) via `model.detect_language()` before the region loop — replaces the fragile first-region lock-in; falls back to old behavior on failure
  - Non-VAD paths: `language_detection_segments=3` added to both faster-whisper transcribe calls
  - B9 fixed: both pipeline loops pass `language or detected_language` so later chunks reuse the first chunk's detection
- [x] **1.4** Verified:
  - Unit: loud audio (−19.9 LUFS) untouched; quiet (−47.9 LUFS) boosted to −16.6 LUFS ✓
  - End-to-end: quiet (−48 LUFS) test video → quality pass fired → word-perfect transcript + valid SRT with correct timing (tiny model, simple faster-whisper path) ✓
  - Control caveat: clean synthetic TTS at −48 LUFS transcribed fine even *without* the boost (Whisper normalizes internally; no noise floor). The pass matters for real-world noisy/low-SNR audio, VAD region detection, and language ID — needs validation with a real quiet es/pt sample when the user has one.
  - Test suite: 43 passed, 3 failed — the 3 failures are **pre-existing** (synthetic invalid MP3 fixtures, see §2.4), unchanged by Phase 1.

### Phase 2 — Subtitle export correctness (SRT quality) ✅ DONE 2026-07-05
- [x] **2.1** B1 fixed: `generate_subtitles` now scans **all** segments for word timestamps (was `segments[:5]`); logs `N/M segments -> word-based|estimated timing`
- [x] **2.2** B3 fixed: word-based generator emits `\N` (pysubs2 escape) instead of raw `\n` in `SSAEvent.text`
- [x] **2.3** B4 fixed: min-duration extension in `word_based_subtitle_generator` clamps against next cue's start (0.05s gap) and never shrinks below the word-timed end; `smart_timing_estimator` overlap clamp can no longer invert cues (`max(next_start-0.1, start+0.2)`)
- [x] **2.4** B7 fixed: TTML/SAMI removed from `SUPPORTED_FORMATS` (pysubs2 can't write them); pipeline now prints `FAILED to generate` per format + logs error instead of silently omitting
- [x] **2.5** B8 fixed: `generate_from_segments` raises `ValueError` on empty input instead of returning `None` (caught & reported by `generate_multiple_formats`)
- [x] **2.6** Verified:
  - Targeted checks (scratchpad/phase2_check.py): wordless head segments still get word-based timing; adjacent short cues don't overlap; no inverted cues; proper 2-line breaks in SRT; VTT/ASS parse with matching cue counts; ttml rejected; empty input raises ✓
  - End-to-end: quiet test video → SRT+VTT+ASS all generated, 3 cues each, 0 invalid cues (pysubs2 round-trip validation) ✓
  - Test suite: 43 passed, 3 pre-existing failures (§2.4) — unchanged

### Phase 3 — Cleanup sweep ✅ DONE 2026-07-05
- [x] **3.1** `requirements.txt`: `audioop-lts` now has `; python_version >= "3.13"` marker (D11); added `requirements-dev.txt` (pytest). **openai-whisper path deleted**: `whisper_manager.py` + its 2 test modules removed; `TranscriptionPipeline` now imports `EnhancedWhisperManager` unconditionally (`use_faster_whisper` param kept as a no-op for backward compat)
- [x] **3.2** Deleted: `main_window_old.py` (690 lines), 3 empty widget stubs, `splitter.py`+test (dead `AudioSplitter`), `translation/utils/` (dead `LanguageDetector`), `subtitle_timing_fixer.py`, `word_level_analyzer.py` + their wiring in `SubtitleGenerator` (incl. dead `configure_word_optimization`/`get_optimization_status` and pipeline's dead `configure_subtitle_sync`), `tower_translator.py` (487 lines, was `if False`-disabled) + all Tower references in `subtitle_translator.py` and the UI's misleading GPU advertising (U7), abandoned methods (D7: 4 Helsinki context variants → only live `translate_with_sliding_context` kept, `translate_from_segments_data`, `adjust_timing`, `merge_short_segments`, `detect_sync_offset`, `estimate_phrase_boundaries`, `wait_with_timeout`), unused imports + dead `custom_model_path` attr (D12)
- [x] **3.3** All `print("DEBUG:")` noise stripped from worker, subtitle_translator, helsinki_translator, pipeline, vad_manager; tracebacks now go through `logger.error(..., exc_info=True)`. Bonus fixes pulled forward from Phase 4 while rewriting the worker translation block: **U4** (no more model load on GUI thread — translator created lazily in worker thread) and **U5** (one translator per file reused across formats, with `cleanup()` after). Also fixed Helsinki `device` attr never being set (GPU cache now freed correctly in `cleanup()`)
- [x] **3.4** CLAUDE.md fully refreshed (faster-whisper only, WAV 16kHz pipeline, quality pass, 46-language support, real dependency list, status section points here); TASKS.md marked superseded with pointer to this file
- [x] **3.5** Integration tests fixed: they were patching `WhisperManager` (a symbol the pipeline never used), so the *real* model ran on fake MP3s — now patch `EnhancedWhisperManager`. `test_audio_segmentation.py` rewritten to exercise the real `AudioConverter.split_audio_if_needed` with real generated WAV audio (was testing the deleted dead `AudioSplitter`). `test_context_translation` updated to test the live `translate_with_sliding_context`
- [x] **3.6** Verified: **full suite 45/45 green** (17s, was 75s with 3 failures + 2 collection errors); app smoke test passes offscreen (window constructs, translation engine label correct)

### Phase 4 — UI robustness ✅ DONE 2026-07-05
- [x] **4.1** U1 fixed: `QueueManager` gained thread-safe `get_items_snapshot()` (copied items), `count_by_status()`, `contains()`; `is_processing`/`current_item` properties now locked; all four `_queue` reach-ins in `main_window.py` replaced
- [x] **4.2** U2/U8 fixed: **real mid-file cancellation** — faster-whisper's transcribe() is a lazy generator, so `EnhancedWhisperManager` now checks a `cancel_event` between segments/regions (raises `TranscriptionCancelled`, re-raise guards added so broad fallback excepts can't swallow it); pipeline exposes `request_cancel()`/`set_paused()`/`reset_control_flags()` and returns `{'cancelled': True}`; `worker.stop()` triggers cancel; `closeEvent` waits 10s (cancel normally lands in ~2s), `terminate()` only as logged last resort. U8: worker reference released via `QThread.finished` → `_on_worker_finished` (+`deleteLater`), no more dropping a live thread
- [x] **4.3** U3 fixed: **honest pause** — `pause_event` stalls the transcription loops mid-file (sleep-loop between segments); worker pause/resume wires through `pipeline.set_paused()`; `MainWindow.is_paused` is now actually set by `toggle_pause` (was read-only before, so ETA/progress gates never fired)
- [x] **4.4** U4/U5: done early in Phase 3.3 — translator created lazily in the worker thread (no GUI freeze) and reused across formats within a file
- [x] **4.5** U6 fixed: per-file failure modals removed (failures marked in queue list + aggregated in completion dialog); startup failures still get a modal (no completion dialog follows those)
- [x] **4.6** `state == 2` → `_is_checked()` helper using `Qt.CheckState`; language-code parsing deduped into `_lang_code_from_combo_text()` (3 call sites)
- [x] **Verified**: 45/45 tests green; functional harness (scratchpad/phase4_check.py) on a 67s speech file: cancel mid-file exits in 2.1s vs 3.4s baseline with `cancelled=True`; pause stalls the run (10.2s total = 3.4s work + 6.4s held) and resumes to success; offscreen UI smoke test exercises new helpers, toggles, and queue accessors

### Phase 5 — Translation quality ✅ DONE 2026-07-05
- [x] **5.1** B5 fixed: `translate_with_sliding_context` (window-as-paragraph + "middle sentence" extraction) deleted; `translate_segments` now does **batched per-segment translation** (batch_size=16, per-item fallback on batch failure) — every subtitle gets exactly its own translation; `SubtitleTranslator` context plumbing removed
- [x] **5.2** B6 fixed: `('pt','en')` now maps to `Helsinki-NLP/opus-mt-ROMANCE-en` (romance→en, much better than the generic `mul-en` fallback pt was hitting)
- [x] **5.3** B10 fixed: `create_translated_subtitle` now **loads the original file and replaces event texts in place** — style definitions, script info, and positioning all carry over to translated ASS/SSA (and everything else) instead of rebuilding a bare file with dangling style names
- [x] **BONUS — critical latent bug found & fixed**: transformers 5.x **removed the `"translation"` pipeline task**, so `HelsinkiTranslator._initialize_model` crashed with `KeyError: "Unknown task translation"` on any real use with current deps (transformers 5.13 installed). Rewritten to use `AutoTokenizer` + `AutoModelForSeq2SeqLM.generate()` directly (`_translate_batch` is the single model-call seam, also used by tests as the stub point)
- [x] **Verified**: real end-to-end pt→en run (scratchpad/phase5_check.py) — langdetect auto-detected `pt`, ROMANCE-en model downloaded & loaded, 4/4 segments translated correctly ("Bom dia a todos e bem-vindos ao nosso canal." → "Good morning, everyone, and welcome to our channel."), timestamps preserved exactly; ASS style-preservation unit test; **full suite 47/47 green**

---

## 4. Environment Notes (for future sessions)

- **venv**: Python 3.12.7 at `./venv/`, deps installed 2026-07-05 from requirements.txt **except** `audioop-lts` (needs py3.13; stdlib audioop covers it on 3.12). `pytest` installed manually (not in requirements.txt — consider adding a dev requirements file).
- **torch is CPU build** (`2.12.1+cpu`). No CUDA. faster-whisper runs int8 on CPU. If the user gets a GPU, reinstall torch with CUDA.
- **Repo**: cloned fresh 2026-07-05 from https://github.com/dusancv22/Video-Transcriber-App, branch `master` @ `6340b87`. The local folder previously wasn't a git repo (leftover venv + assets only).
- **Run the app**: `./venv/Scripts/python.exe run.py` (always venv python, background mode).
- **Run tests**: `./venv/Scripts/python.exe -m pytest tests/`

---

## 5. Progress Log

| Date | Session summary |
|------|-----------------|
| 2026-07-05 | Repo re-cloned, venv repaired + deps installed. Full codebase review completed (core pipeline read directly; UI + subtitles/translation swept by agents; test suite run). This document created. |
| 2026-07-05 | **Phase 1 complete.** Audio quality pass (`optimizer.py` + converter wiring), WAV 16kHz mono intermediate, duration-based splitting, robust language detection (longest-region detection + multi-segment sampling + cross-chunk propagation / B9). Verified end-to-end with synthetic quiet video: quality pass fires, transcript word-perfect, SRT valid. Converter tests updated for new API. Outstanding: validate es/pt improvement with a real user sample. |
| 2026-07-05 | **Phase 2 complete.** All five subtitle correctness bugs fixed (B1 word-timestamp sampling, B3 `\N` line breaks, B4 overlap/inversion clamps, B7 phantom TTML/SAMI formats, B8 None return). Verified with targeted edge-case script + end-to-end SRT/VTT/ASS generation (0 invalid cues). |
| 2026-07-05 | **Phase 3 complete.** ~2,900 lines of dead code deleted (openai-whisper path, Tower translator, legacy UI, unused analyzers, abandoned methods); DEBUG noise stripped; requirements fixed (+dev file); CLAUDE.md/TASKS.md refreshed; test suite repaired — **45/45 green in 17s** (was 43 pass/3 fail/2 broken in 75s). Bonus: U4/U5 (GUI-thread model load, per-format translator reload) fixed during worker rewrite; Helsinki GPU-cleanup device bug fixed. |
| 2026-07-05 | **Phase 4 complete.** UI robustness: thread-safe queue accessors (U1), real mid-file cancellation + safe worker teardown (U2/U8 — `terminate()` now a logged last resort), honest mid-file pause (U3), no more modal storm on failing batches (U6), Qt.CheckState + deduped language parsing (4.6). Functionally verified: cancel lands in ~2s mid-transcription; pause genuinely stalls the model and resumes cleanly. 45/45 tests green. |
| 2026-07-05 | **Phase 5 complete — ALL ROADMAP PHASES DONE.** Translation quality: per-segment batched translation replaces lossy sliding-context (B5), pt→en uses ROMANCE-en model (B6), translated ASS files keep style definitions via edit-in-place (B10). Critical latent bug found & fixed: transformers 5.x removed the "translation" pipeline task — translation would have crashed on ANY real use; rewritten on tokenizer+generate. Verified with real pt→en model run (perfect translations, timestamps intact); 47/47 tests green. **Remaining (not code): validate es/pt transcription improvement with a real user sample when available. Possible future work: GPU torch install for faster transcription, PyInstaller build check, README refresh.** |
| 2026-07-05 | **Real-world validation round (Portuguese video)** exposed 3 issues, all fixed (commit ca18a14): (1) transcripts/subtitles now written UTF-8 **with BOM** — Windows apps misdetected plain UTF-8 as ANSI (mojibake on every accent); (2) English-centric post-processing corrupted Portuguese — abbreviation list uppercased *eu*→EU and *ai*→AI, sentence rules injected bad breaks; advanced processor now English-only, basic processor language-aware; (3) Whisper hallucination loops on non-speech audio (walls of repeated words) — enabled faster-whisper's built-in VAD filter on the non-VAD paths + repetition-run collapse (word >3x, phrase >2x) in transcripts and subtitles. Exe rebuilt. Remaining caveat: adult/noisy content will never transcribe perfectly — fragmented and non-lexical audio is out of ASR scope. |
| 2026-07-05 | **Validation round 2 (translated SRT)**: hallucination walls persisted in the *translated* subtitles (43× "whoa" in a 0.9s cue) — generated by MarianMT itself from degenerate inputs, post-collapse. Fixed (commit c68fd79): `no_repeat_ngram_size=4` in generation, `TextProcessor.is_degenerate_subtitle_text()` (repetition walls / char-loop tokens / dominant-char noise / impossible speech density) with degenerate cues **dropped entirely** in subtitle generation + translation output. SRT timestamps are absolute → no re-sync needed. Verified with real ROMANCE-en model: bait cues dropped, normal cues intact. 59/59 tests. |
