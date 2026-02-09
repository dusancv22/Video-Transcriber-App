# PLANNING.md

## Project Overview

The Video Transcriber App is a desktop application that converts video files into text transcripts using OpenAI's Whisper AI model. Built with PyQt6, the application provides a user-friendly GUI for batch processing video files with real-time progress tracking, queue management, and comprehensive error handling. The app is designed for users who need to transcribe multiple video files efficiently with professional-grade accuracy.

### Key Goals
- Convert media files (MP4, AVI, MKV, MOV, WEBM, MP3) to accurate text transcripts
- Provide an intuitive desktop interface for batch processing
- Support large file handling through intelligent audio splitting
- Offer real-time progress tracking with time estimates
- Ensure reliable processing with pause/resume capabilities
- Generate clean, formatted text output

## Technology Stack

### Core Technologies
- **Language:** Python 3.8+
- **GUI Framework:** PyQt6 (6.7.0+) - Modern desktop interface
- **AI/ML:** OpenAI Whisper (via faster-whisper 0.10.0+) - Speech-to-text transcription
- **Audio Processing:** MoviePy - Video to audio conversion and manipulation
- **Deep Learning:** PyTorch (2.2.0+) - GPU acceleration support
- **Build Tools:** PyInstaller (6.5.0+) - Executable generation

### Development Tools
- **Package Management:** pip with requirements.txt
- **Testing:** pytest for unit testing
- **Logging:** Python's built-in logging module
- **Virtual Environment:** venv for dependency isolation
- **Version Control:** Git with structured branching

### Dependencies
- **Media Processing:** ffmpeg-python (0.2.0) - Video/audio format handling
- **Numerical Computing:** numpy (1.24.0+) - Array operations
- **GUI Components:** PyQt6 widgets for modern UI elements
- **Hardware Acceleration:** CUDA support for GPU processing

## User Personas

### Primary User: Content Creator/Researcher
- **Description:** Video content creators, researchers, journalists, and students who regularly work with video content
- **Needs:** 
  - Transcribe interviews, lectures, meetings, and content videos
  - Process multiple files efficiently in batches
  - Obtain accurate, formatted transcripts for editing or analysis
  - Monitor progress for long processing sessions
- **Pain Points:** 
  - Manual transcription is time-consuming and expensive
  - Online services have file size limits and privacy concerns
  - Need offline solution for sensitive content
  - Require consistent formatting for professional use

### Secondary User: Accessibility Professional
- **Description:** Organizations and individuals creating accessible content
- **Needs:**
  - Generate transcripts for video accessibility compliance
  - Process large volumes of educational or training content
  - Ensure consistent quality across multiple files
- **Pain Points:**
  - Manual captioning is labor-intensive
  - Need reliable, repeatable processes
  - Require professional-quality output

## Features

### Completed Features
- **Media File Input Processing:** Multi-format support (MP4, AVI, MKV, MOV, WEBM, MP3) with validation and queue management. Handles individual files and entire directories with recursive scanning. *(Added 2025-01-08)*
- **Audio Conversion Pipeline:** Intelligent video-to-audio conversion using MoviePy with automatic file splitting for large files (>25MB). Supports temporary file management and cleanup. *(Added 2025-01-08)*
- **Whisper AI Integration:** Advanced speech-to-text using faster-whisper with large model support. Forced English language processing for consistency. GPU acceleration support when available. *(Added 2025-01-08)*
- **Professional GUI Interface:** Modern PyQt6 interface with drag-and-drop support, real-time progress tracking, and comprehensive status reporting. Includes pause/resume functionality. *(Added 2025-01-08)*
- **Queue Management System:** Thread-safe queue with status tracking (queued, processing, completed, failed). Supports concurrent processing with proper synchronization. *(Added 2025-01-08)*
- **Progress Tracking & Time Estimation:** Real-time progress bars with ETA calculations based on historical processing times. Visual status indicators for each file. *(Added 2025-01-08)*
- **Text Post-Processing:** Advanced text formatting with sentence detection, capitalization correction, and punctuation normalization. Handles long texts through chunking. *(Added 2025-01-08)*
- **Error Handling & Recovery:** Comprehensive error reporting with graceful failure handling. Detailed logging for debugging and user feedback. *(Added 2025-01-08)*
- **Multi-Threading Architecture:** Worker thread implementation prevents UI freezing during processing. Proper thread cleanup and resource management. *(Added 2025-01-08)*
- **Output Management:** Configurable output directories with structured file naming. UTF-8 encoded text files for international character support. *(Added 2025-01-08)*

### In-Progress Features
- **Enhanced Language Detection:** While currently forced to English, the system includes infrastructure for language detection and multi-language support
  *(Status 2025-01-08: Language detection code present but disabled in favor of English-only processing)*

### Planned Features
- **Batch Export Options:** Support for multiple output formats (TXT, SRT, VTT, DOCX)
- **Advanced Audio Preprocessing:** Noise reduction and audio enhancement before transcription
- **Custom Model Support:** Ability to use different Whisper model sizes based on accuracy vs speed preferences
- **Transcription Accuracy Metrics:** Confidence scores and quality indicators
- **Configuration Management:** User preferences for model settings, output formats, and processing options
- **Plugin Architecture:** Extensible system for custom post-processing and export plugins

## Architecture

### System Architecture
The application follows a modular, layered architecture with clear separation of concerns:

**Presentation Layer (UI):**
- PyQt6-based main window with modern styling
- Real-time progress widgets and status reporting
- Queue management interface with visual file status
- Worker thread integration for non-blocking operations

**Business Logic Layer:**
- TranscriptionPipeline: Orchestrates the complete processing workflow
- QueueManager: Thread-safe queue operations and status tracking
- WhisperManager: AI model management and transcription coordination
- TextProcessor: Post-processing and formatting operations

**Data Processing Layer:**
- AudioConverter: Video-to-audio conversion and file management
- File handlers: Input validation and format verification
- Progress tracking: Real-time status updates and time estimation

**Infrastructure Layer:**
- Logging system with configurable levels
- Error handling and recovery mechanisms
- Temporary file management and cleanup
- Threading and synchronization primitives

### Database Schema
**File-based system** - No traditional database. State managed through:
- Queue data structures (in-memory)
- File system for input/output management
- Temporary audio files in structured directories
- Configuration stored in object properties

### Processing Pipeline
1. **File Input & Validation:** User selects files/directories → File format validation → Queue population
2. **Audio Conversion:** Video loading → Audio extraction → File size checking → Splitting if needed (>25MB)
3. **AI Transcription:** Whisper model loading → Segment processing → Text generation → Language detection
4. **Post-Processing:** Text chunking → Formatting enhancement → Sentence structure correction
5. **Output Generation:** File writing → Cleanup → Status reporting

### State Management
- **Queue State:** Thread-safe QueueManager with atomic operations
- **Progress State:** Real-time updates via PyQt signals and slots
- **UI State:** Reactive interface updates based on processing status
- **File State:** Temporary file tracking with automatic cleanup

## Authentication System
**Not applicable** - Desktop application with local file access only. No user authentication or network services required.

## UI/UX Patterns

### Visual Design Principles
- **Modern Flat Design:** Clean buttons with hover effects and professional color scheme
- **Status-Driven UI:** Visual indicators for queue item states (⏳ queued, 🔄 processing, ✓ completed, ❌ failed)
- **Progressive Disclosure:** Hide advanced options until needed (progress section appears during processing)
- **Responsive Feedback:** Immediate visual feedback for all user actions

### Interaction Patterns
- **Drag & Drop Support:** Primary file input method for intuitive operation
- **Batch Operations:** Support for directory selection with recursive file discovery
- **Pause/Resume Control:** User control over long-running operations
- **Real-time Updates:** Live progress bars and time estimates
- **Error Recovery:** Clear error messages with actionable guidance

### Color Coding System
- **Blue (#2563eb):** Primary actions (Add Files, Add Directory)
- **Gray (#4b5563):** Secondary actions (Output Directory)
- **Red (#dc2626):** Destructive actions (Clear Queue)
- **Green (#16a34a):** Success states and primary processing action
- **Yellow (#eab308):** Warning states and pause functionality

## Business Rules

### File Processing Rules
- **Supported Formats:** MP4, AVI, MKV, MOV, WEBM video files and MP3 audio files accepted
- **File Size Limits:** Files >25MB automatically split into segments for processing
- **Language Processing:** Currently forced to English for consistent results
- **Queue Management:** Duplicate files automatically rejected from queue
- **Processing Order:** Files processed in order added (FIFO)

### Quality Assurance Rules
- **Model Selection:** Large Whisper model used by default for highest accuracy
- **Audio Quality:** 44.1kHz sample rate, 4-byte depth for optimal transcription
- **Text Processing:** Automatic formatting with sentence detection and capitalization
- **Error Handling:** Failed files marked but don't stop batch processing

### Resource Management Rules
- **Temporary Files:** Automatic cleanup after processing completion
- **Memory Management:** Chunked processing for large texts to prevent memory issues
- **GPU Utilization:** Automatic CUDA detection and utilization when available
- **Thread Safety:** All queue operations protected with threading locks

## Integration Points

### External Dependencies
- **FFmpeg:** Video processing and format conversion (via ffmpeg-python)
- **OpenAI Whisper:** AI transcription model (via faster-whisper)
- **PyTorch:** Deep learning framework for model execution
- **MoviePy:** Python video editing library for audio extraction

### System Integration
- **File System:** Direct file I/O for input/output operations
- **Operating System:** Native OS file dialogs and directory selection
- **Hardware Acceleration:** CUDA integration for GPU processing
- **Process Management:** Multi-threading with proper resource cleanup

## Performance Considerations

### Optimization Strategies
- **Lazy Loading:** Whisper model loaded only when first needed
- **File Splitting:** Large audio files automatically segmented to optimize processing
- **Memory Management:** Text processing in chunks to handle large transcripts
- **GPU Acceleration:** Automatic CUDA utilization when available
- **Progress Streaming:** Real-time updates without blocking main thread

### Scalability Factors
- **Batch Processing:** Support for processing multiple files sequentially
- **Queue Management:** Thread-safe operations for concurrent access
- **Resource Cleanup:** Automatic temporary file management
- **Error Isolation:** Individual file failures don't affect batch processing

## Environment Variables
**No environment variables required** - All configuration handled through application settings and file paths selected via GUI.

## Testing Strategy

### Test Coverage Areas
- **Unit Tests:** Individual component testing (converters, processors, managers)
- **Integration Tests:** Pipeline workflow testing with sample files
- **UI Tests:** Widget behavior and user interaction validation
- **Error Handling Tests:** Exception scenarios and recovery mechanisms

### Testing Framework
- **pytest:** Primary testing framework for unit and integration tests
- **Test Files:** Sample audio/video files for transcription testing
- **Mock Objects:** Simulated components for isolated testing
- **Automated Testing:** CI/CD integration for continuous validation

### Current Test Structure
```
tests/
├── test_transcription/
│   ├── test_whisper_manager.py
│   ├── test_pipeline.py
│   └── test_files/
├── test_audio_processing/
│   ├── test_converter.py
│   └── test_splitter.py
└── test_input_handling/
    └── test_file_handler.py
```

## Deployment

### Distribution Method
- **Standalone Executable:** PyInstaller builds for Windows distribution
- **Dependencies Bundled:** All required libraries packaged in executable
- **No Installation Required:** Portable application with minimal system requirements

### System Requirements
- **Operating System:** Windows (primary), with potential for cross-platform support
- **Python Runtime:** 3.8+ (bundled in executable)
- **Hardware:** Minimum 8GB RAM, GPU recommended for faster processing
- **Storage:** Adequate space for temporary audio files during processing

### Build Process
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --onefile --windowed run.py
```

## Constraints & Non-Goals

### Technical Constraints
- **Desktop Only:** No web interface or mobile support planned
- **English Language:** Currently optimized for English transcription only
- **Local Processing:** No cloud services or remote processing
- **Single User:** No multi-user or collaborative features

### Scope Limitations
- **Real-time Transcription:** Not designed for live audio processing
- **Video Editing:** No video editing or manipulation features
- **Audio Enhancement:** No advanced audio preprocessing capabilities
- **Network Features:** No sharing, sync, or collaboration features

### Performance Boundaries
- **File Size:** Very large files (>1GB) may require significant processing time
- **Concurrent Processing:** Single-threaded transcription pipeline
- **Memory Usage:** Large audio files may require substantial RAM

## Development Guidelines

### Code Organization
- **Modular Architecture:** Clear separation between UI, business logic, and data processing
- **Single Responsibility:** Each class and module has a focused purpose
- **Dependency Injection:** Components receive dependencies rather than creating them
- **Error Propagation:** Consistent error handling throughout the application stack

### Coding Standards
- **Python Style:** Follow PEP 8 conventions with clear naming and documentation
- **Type Hints:** Use type annotations for method signatures and return values
- **Logging:** Comprehensive logging at appropriate levels (DEBUG, INFO, ERROR)
- **Documentation:** Docstrings for all public methods and classes

### Version Control Strategy
- **Branch Structure:** Feature branches for development, main branch for stable releases
- **Commit Messages:** Descriptive commits that explain the "why" not just the "what"
- **Recent Development:** Currently on "Stage-5---Fixing-Bugs" branch focusing on stability improvements

### Quality Assurance
- **Testing:** Unit tests for core functionality, integration tests for workflows
- **Code Reviews:** Peer review for significant changes
- **Error Handling:** Graceful degradation and user-friendly error messages
- **Performance Monitoring:** Logging of processing times and resource usage

---

*Last Updated: 2025-01-08*
*Current Branch: Stage-5---Fixing-Bugs*
*Recent Focus: Bug fixes and stability improvements following UI completion*
