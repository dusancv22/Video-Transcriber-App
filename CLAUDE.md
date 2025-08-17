# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
python run.py
```

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
   - `converter.py`: Video-to-audio conversion using MoviePy/FFmpeg
   - `splitter.py`: Splits large audio files (>25MB) into segments
   - `text_processor.py`: Post-processing for formatting and cleanup
   - `combiner.py`: Intelligent text combination with overlap removal

4. **Infrastructure Layer** - `src/input_handling/` & `src/utils/`
   - `queue_manager.py`: Thread-safe queue with status tracking
   - `file_validator.py`: Validates video formats and accessibility
   - `logger.py`: Configurable logging system
   - `error_handler.py`: Comprehensive error recovery

### Core Pipeline Flow
1. **File Input & Validation** → Validates formats → Populates queue
2. **Audio Conversion** → Extracts audio → Splits if >25MB
3. **AI Transcription** → Loads Whisper model → Processes segments → Forces English
4. **Post-Processing** → Removes duplicates → Formats text
5. **Output Generation** → Saves transcript → Cleans temporary files

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
- **faster-whisper** (0.10.0+): Optimized Whisper implementation  
- **MoviePy**: Video editing library for audio extraction
- **torch** (2.2.0+): PyTorch backend for Whisper inference
- **numpy** (1.24.0+): Array operations
- **ffmpeg-python** (0.2.0): FFmpeg wrapper
- **PyInstaller** (6.5.0+): Executable generation

## Testing Structure

Tests organized under `tests/` mirroring `src/` structure. Uses pytest with fixtures for media files in `test_files/` subdirectories.

## Business Rules & Constraints

### File Processing Rules
- **Supported Formats**: MP4, AVI, MKV, MOV only
- **File Size Limits**: Files >25MB automatically split into segments
- **Language Processing**: Currently forced to English for consistency
- **Queue Management**: Duplicate files automatically rejected (FIFO processing)

### Quality Assurance Rules
- **Model Selection**: Large Whisper model for highest accuracy
- **Audio Quality**: 44.1kHz sample rate, 4-byte depth
- **Text Processing**: Automatic formatting with sentence detection
- **Error Handling**: Failed files marked but don't stop batch

### Resource Management Rules
- **Temporary Files**: Automatic cleanup after processing
- **Memory Management**: Chunked processing for large files
- **GPU Utilization**: Automatic CUDA detection and use
- **Thread Safety**: All queue operations protected with locks

## Current Development Status

The project is on branch "clean-pyqt6-app" with a complete, functional UI. Recent work focused on modernizing from card-based to flat design, fixing transcription repetition issues, and forcing English-only transcription for consistency.