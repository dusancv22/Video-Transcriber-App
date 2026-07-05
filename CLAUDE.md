# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **⚠️ ACTIVE WORK — READ FIRST:** [`docs/project/CODEBASE_REVIEW_AND_ROADMAP.md`](docs/project/CODEBASE_REVIEW_AND_ROADMAP.md) contains the current findings inventory, prioritized execution roadmap, and progress log. Check it for where work left off before starting anything.

## Project Overview

The Video Transcriber App is a desktop application that converts video files into text transcripts using OpenAI's Whisper AI model. Built with PyQt6, it provides batch processing, real-time progress tracking, and comprehensive error handling.

### Key Goals
- Convert video files (MP4, AVI, MKV, MOV) to accurate text transcripts
- Provide an intuitive desktop interface for batch processing
- Support large file handling through intelligent audio splitting
- Offer real-time progress tracking with time estimates
- Ensure reliable processing with pause/resume capabilities
- Generate clean, formatted text output

### Target Users
- Content creators, researchers, journalists, and students needing transcriptions
- Organizations creating accessible content for compliance

## Development Commands

**Run the application:**
```bash
./venv/Scripts/python.exe run.py
```

**IMPORTANT**: When the user asks to "run the app", ALWAYS use the virtual environment Python (`./venv/Scripts/python.exe`) and run in background mode. Never use system Python.

**Run tests:**
```bash
python -m pytest tests/
python -m pytest tests/test_audio_processing/test_converter.py  # Run specific test module
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Install in development mode:**
```bash
pip install -e .
```

**Build executable:**
```bash
# Standard build
pyinstaller --onefile --windowed run.py

# Full build with all dependencies (uses existing spec file)
pyinstaller VideoTranscriber-Full.spec
```

## Subtitle Synchronization System

**For detailed technical documentation on the subtitle synchronization architecture, see: [`docs/subtitle-synchronization-architecture.md`](docs/subtitle-synchronization-architecture.md)**

Transcription uses **faster-whisper** exclusively (openai-whisper support was removed 2026-07). Word-level timestamps drive subtitle timing; when unavailable, a smart estimation fallback is used. Subtitle formats: SRT, VTT, ASS, SSA.

## Architecture Overview

This is a PyQt6-based video transcription application using a 4-layer modular architecture:

### System Architecture Layers

1. **Presentation Layer (UI)** - `src/ui/`
   - `main_window.py`: Main PyQt6 interface with drag-drop and real-time progress
   - `worker.py`: Background thread for non-blocking transcription
   - `styles/modern_theme.py`: CSS-like PyQt stylesheets for modern flat design

2. **Business Logic Layer** - `src/transcription/`
   - `transcription_pipeline.py`: Orchestrates video→text workflow
   - `whisper_manager.py`: Manages Whisper model loading and transcription
   - `progress_tracker.py`: Tracks processing progress across components

3. **Data Processing Layer** - `src/audio_processing/` & `src/post_processing/`
   - `converter.py`: Media-to-audio conversion (FFmpeg, 16kHz mono WAV) + duration-based splitting with overlap
   - `optimizer.py`: Audio quality pass — loudness analysis, conditional normalization of quiet audio
   - `vad_manager.py`: Silero VAD speech-region detection
   - `text_processor.py`: Post-processing for formatting and cleanup
   - `combiner.py`: Intelligent text combination with overlap removal

4. **Infrastructure Layer** - `src/input_handling/` & `src/utils/`
   - `queue_manager.py`: Thread-safe queue with status tracking
   - `file_validator.py`: Validates video formats and accessibility
   - `logger.py`: Configurable logging system
   - `error_handler.py`: Comprehensive error recovery

### Core Pipeline Flow
1. **File Input & Validation** → Validates formats → Populates queue
2. **Audio Conversion** → Extracts 16kHz mono WAV → Quality pass (boosts quiet audio) → Splits if >25 min
3. **AI Transcription** → faster-whisper → Language: user-selected (46 languages) or robust auto-detect
4. **Post-Processing** → Removes duplicates → Formats text
5. **Output Generation** → Saves transcript (+ optional SRT/VTT/ASS subtitles, optional translation) → Cleans temporary files

### Critical Implementation Details

**Thread Safety**: Queue operations use threading locks. UI updates marshalled via Qt signals.

**Memory Management**: Large files processed in segments. Aggressive temporary file cleanup.

**Error Recovery**: Each pipeline stage has comprehensive error handling with graceful degradation.

**Performance Optimizations**:
- Lazy loading of Whisper model (only loaded when first needed)
- Automatic CUDA detection for GPU acceleration
- Chunked text processing for large transcripts
- Real-time progress streaming without blocking

## Key Dependencies

- **PyQt6** (6.7.0+): GUI framework
- **faster-whisper** (0.10.0+): Whisper implementation (the only transcription backend)
- **torch** (2.2.0+): PyTorch backend (Silero VAD, translation models)
- **ffmpeg-python** (0.2.0): FFmpeg wrapper for audio extraction (system ffmpeg required)
- **pysubs2**: Subtitle file generation (SRT/VTT/ASS/SSA)
- **transformers**: Helsinki-NLP translation models
- **PyInstaller** (6.5.0+): Executable generation

Dev dependencies: `pip install -r requirements-dev.txt` (adds pytest).

## Testing Structure

Tests organized under `tests/` mirroring `src/` structure. Uses pytest with fixtures for media files in `test_files/` subdirectories.

## Business Rules & Constraints

### File Processing Rules
- **Supported Formats**: MP4, AVI, MKV, MOV, WEBM, MP3
- **Duration Limits**: Audio >25 minutes automatically split into overlapping segments
- **Language Processing**: 46 selectable languages + auto-detect (detects on the longest speech region)
- **Queue Management**: Duplicate files automatically rejected (FIFO processing)

### Quality Assurance Rules
- **Model Selection**: Large Whisper model (large-v3 via faster-whisper) for highest accuracy
- **Audio Quality**: 16kHz mono WAV intermediate (Whisper-native); quiet audio (<−24 LUFS) automatically normalized
- **Text Processing**: Automatic formatting with sentence detection
- **Error Handling**: Failed files marked but don't stop batch

### Resource Management Rules
- **Temporary Files**: Automatic cleanup after processing
- **Memory Management**: Chunked processing for large files
- **GPU Utilization**: Automatic CUDA detection and use
- **Thread Safety**: All queue operations protected with locks

## Current Development Status

See [`docs/project/CODEBASE_REVIEW_AND_ROADMAP.md`](docs/project/CODEBASE_REVIEW_AND_ROADMAP.md) for the findings inventory, execution roadmap, and progress log. As of 2026-07-05 **all 5 roadmap phases are complete**: audio quality pass + robust language detection, subtitle correctness fixes, dead-code cleanup sweep, UI robustness (real cancel/pause), and translation quality (per-segment, pt→en ROMANCE model). Outstanding: validate es/pt transcription with a real user sample.