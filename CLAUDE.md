# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Video Transcriber App is a desktop application that converts video files into text transcripts using OpenAI's Whisper AI model. Built with PyQt6, the application provides a user-friendly GUI for batch processing video files with real-time progress tracking, queue management, and comprehensive error handling.

### Key Goals
- Convert video files (MP4, AVI, MKV, MOV) to accurate text transcripts
- Provide an intuitive desktop interface for batch processing
- Support large file handling through intelligent audio splitting
- Offer real-time progress tracking with time estimates
- Ensure reliable processing with pause/resume capabilities
- Generate clean, formatted text output

### Target Users
- **Content Creator/Researcher**: Video content creators, researchers, journalists, and students who need to transcribe interviews, lectures, meetings, and content videos
- **Accessibility Professional**: Organizations creating accessible content who need to generate transcripts for video accessibility compliance

## Development Commands

**Run the application:**
```bash
python run.py
```

**Run tests:**
```bash
python -m pytest tests/
```

**Run specific test module:**
```bash
python -m pytest tests/test_audio_processing/test_converter.py
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
pyinstaller --onefile --windowed run.py
```

## Architecture Overview

This is a PyQt6-based video transcription application that uses Whisper AI for speech-to-text conversion. The architecture follows a modular, 4-layer design with clear separation of concerns:

### System Architecture Layers

**Presentation Layer (UI):**
- PyQt6-based main window with modern styling and CSS-like stylesheets
- Real-time progress widgets and status reporting with visual indicators
- Queue management interface with drag-drop support and file status display
- Worker thread integration for non-blocking operations

**Business Logic Layer:**
- `TranscriptionPipeline`: Orchestrates the complete processing workflow
- `QueueManager`: Thread-safe queue operations and status tracking
- `WhisperManager`: AI model management and transcription coordination
- `TextProcessor`: Post-processing and formatting operations

**Data Processing Layer:**
- `AudioConverter`: Video-to-audio conversion using MoviePy and file management
- File handlers: Input validation and format verification
- Progress tracking: Real-time status updates and time estimation

**Infrastructure Layer:**
- Logging system with configurable levels
- Error handling and recovery mechanisms
- Temporary file management and cleanup
- Threading and synchronization primitives

### Core Pipeline Flow
1. **File Input & Validation** → User selects files/directories → File format validation → Queue population
2. **Audio Conversion** → Video loading → Audio extraction → File size checking → Splitting if needed (>25MB)
3. **AI Transcription** → Whisper model loading → Segment processing → Text generation → Language detection
4. **Post-Processing** → Text chunking → Formatting enhancement → Sentence structure correction
5. **Output Generation** → File writing → Cleanup → Status reporting

### Key Architectural Components

**UI Layer** (`src/ui/`):
- `main_window.py`: Main PyQt6 interface with drag-drop, queue display, and real-time progress
- `worker.py`: Background thread for transcription processing
- Custom styling with CSS-like PyQt stylesheets

**Processing Pipeline** (`src/transcription/`):
- `transcription_pipeline.py`: Orchestrates the entire video→text workflow
- `whisper_manager.py`: Handles Whisper model loading and audio transcription
- Large files (>25MB) are automatically split into segments for processing

**Audio Processing** (`src/audio_processing/`):
- `converter.py`: FFmpeg wrapper for video-to-audio conversion
- `splitter.py`: Splits large audio files into manageable segments
- Automatic cleanup of temporary files

**Queue System** (`src/input_handling/`):
- `queue_manager.py`: Thread-safe queue with status tracking and persistence
- `file_validator.py`: Validates video file formats and accessibility
- Supports both individual files and directory scanning

**Post-processing** (`src/post_processing/`):
- `text_processor.py`: Cleans and formats transcription output
- `exporter.py`: Handles multiple output formats

### Critical Implementation Details

**Thread Safety**: The queue manager uses thread-safe operations and the UI updates are marshalled back to the main thread via Qt signals.

**Error Recovery**: Each stage has comprehensive error handling with graceful degradation. Failed files are marked but don't stop the entire queue.

**Memory Management**: Large audio files are processed in segments to avoid memory exhaustion. Temporary files are aggressively cleaned up.

**Progress Tracking**: Real-time progress reporting with ETA calculations based on processing history.

## Key Dependencies

- **PyQt6 (6.7.0+)**: Modern GUI framework for desktop interface
- **faster-whisper (0.10.0+)**: Optimized Whisper implementation for better performance
- **MoviePy**: Python video editing library for audio extraction and conversion
- **torch (2.2.0+)**: PyTorch backend for Whisper model inference with GPU acceleration support
- **numpy (1.24.0+)**: Array operations for audio processing
- **PyInstaller (6.5.0+)**: Executable generation for distribution

## Testing Structure

Tests are organized by module under `tests/` with corresponding structure to `src/`. Test files use pytest and include both unit tests and integration tests with actual media files in `test_files/` subdirectories.

## Business Rules & Constraints

### File Processing Rules
- **Supported Formats**: Only MP4, AVI, MKV, MOV video files accepted
- **File Size Limits**: Files >25MB automatically split into segments for processing
- **Language Processing**: Currently forced to English for consistent results
- **Queue Management**: Duplicate files automatically rejected from queue
- **Processing Order**: Files processed in order added (FIFO)

### Quality Assurance Rules
- **Model Selection**: Large Whisper model used by default for highest accuracy
- **Audio Quality**: 44.1kHz sample rate, 4-byte depth for optimal transcription
- **Text Processing**: Automatic formatting with sentence detection and capitalization
- **Error Handling**: Failed files marked but don't stop batch processing

### Resource Management Rules
- **Temporary Files**: Automatic cleanup after processing completion
- **Memory Management**: Chunked processing for large texts to prevent memory issues
- **GPU Utilization**: Automatic CUDA detection and utilization when available
- **Thread Safety**: All queue operations protected with threading locks

### Performance Considerations
- **Lazy Loading**: Whisper model loaded only when first needed
- **File Splitting**: Large audio files automatically segmented to optimize processing
- **Memory Management**: Text processing in chunks to handle large transcripts
- **GPU Acceleration**: Automatic CUDA utilization when available
- **Progress Streaming**: Real-time updates without blocking main thread

## Current Development Status

The project is on branch "Stage-5---Fixing-Bugs" focusing on stability improvements. Recent changes include forced English-only transcription and enhanced progress reporting. The UI is complete and functional - current work centers on bug fixes and performance optimization.

### Recent Commits
- Fixed transcription language (forced English only)
- Added new print messages for better process visibility
- Updated icons and achieved perfect working version
- UI finished with all buttons working and transcription functional