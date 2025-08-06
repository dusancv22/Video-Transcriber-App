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

### **PyQt6 Desktop Application**
```bash
# Run the desktop application
python run.py

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Build executable
pyinstaller --onefile --windowed run.py
```

### **Electron Web Application (Recommended)**
```bash
# Quick start with automated scripts (Windows)
video-transcriber-electron/start.bat
# or
video-transcriber-electron/start.ps1

# Manual startup - Terminal 1 (Backend)
cd video-transcriber-electron/backend
python main.py

# Manual startup - Terminal 2 (Frontend)
cd video-transcriber-electron
npm run dev

# Install Node.js dependencies
cd video-transcriber-electron
npm install

# Build for production
npm run build

# Run with development features
npm run dev:debug
```

### **Testing & Quality Assurance**
```bash
# Run all Python tests
python -m pytest tests/ -v

# Run security tests
python -m pytest tests/integration/security/ -v

# Run specific test module
python -m pytest tests/test_transcription/test_pipeline.py -v

# Run frontend tests
cd video-transcriber-electron
npm test

# Run integration tests
npm run test:integration

# Security audit
npm run test:security
```

### **API Development & Testing**
```bash
# Start backend with auto-reload
cd video-transcriber-electron/backend
python main.py --reload

# Test API endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/status

# View API documentation
# Open: http://127.0.0.1:8000/docs

# Test WebSocket connection
# Use browser console: new WebSocket('ws://127.0.0.1:8000/ws')
```

### **Debugging & Development Tools**
```bash
# Enable debug logging
cd video-transcriber-electron/backend
python main.py --log-level debug

# Frontend with debug features
cd video-transcriber-electron
npm run dev

# Hot reload development
npm run dev:hot

# Performance profiling
python -m cProfile run.py
```

## Architecture Overview

The Video Transcriber App features a modern dual-interface architecture with both native PyQt6 desktop and web-based Electron interfaces. Both interfaces share a common FastAPI backend and transcription pipeline, ensuring consistency while providing flexibility in user experience.

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │   PyQt6 GUI     │    │      Electron Frontend             │  │
│  │   (Desktop)     │    │   ┌─────────────────────────────┐   │  │
│  │                 │    │   │ React + Material-UI         │   │  │
│  │ - Native UI     │    │   │ - Settings Dialog           │   │  │
│  │ - Drag & Drop   │    │   │ - Real-time Progress        │   │  │
│  │ - Queue Mgmt    │    │   │ - WebSocket Integration     │   │  │
│  │ - Progress      │    │   │ - Error Handling            │   │  │
│  └─────────────────┘    │   │ - Professional UI           │   │  │
│          │               │   └─────────────────────────────┘   │  │
│          │               └─────────────────────────────────────┘  │
└──────────┼────────────────────────────┼────────────────────────────┘
           │                            │
           │     ┌─────────────────────┐ │
           │     │    FastAPI Backend  │ │
           └─────┤                     ├─┘
                 │  - REST API         │
                 │  - WebSocket Server │
                 │  - Settings Mgmt    │
                 │  - Security Layer   │
                 │  - Path Validation  │
                 └─────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Core Processing Components                     ││
│  │                                                             ││
│  │  • TranscriptionPipeline - Orchestrates workflow          ││
│  │  • QueueManager - Thread-safe queue operations            ││
│  │  • WhisperManager - AI model management                   ││
│  │  • SettingsManager - Configuration persistence            ││
│  │  • SecurityValidator - Input validation & sanitization    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
           │
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PROCESSING LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  • AudioConverter - Video-to-audio processing                  │
│  • FileSplitter - Large file segmentation (>25MB)             │
│  • TextProcessor - Post-processing and formatting              │
│  • FormatExporter - Multiple output formats (TXT/SRT/VTT)     │
│  • ProgressTracker - Real-time status updates                 │
└─────────────────────────────────────────────────────────────────┘
           │
┌─────────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  • Security System - Path traversal protection                 │
│  • Error Handling - Comprehensive error recovery               │
│  • Logging System - Configurable logging levels               │
│  • File Management - Temporary file cleanup                    │
│  • Threading System - Non-blocking operations                  │
│  • WebSocket Manager - Real-time communication                 │
└─────────────────────────────────────────────────────────────────┘
```

### Enhanced Core Pipeline Flow

1. **User Interface & Input** → Dual interface options → File validation & security checks
2. **Settings Validation** → Configuration validation → Path security verification → Permission checking
3. **Queue Management** → Thread-safe operations → Real-time status updates → WebSocket broadcasts
4. **Audio Processing** → Video extraction → Intelligent segmentation → Quality optimization
5. **AI Transcription** → Model loading → Segment processing → Progress tracking → Error handling
6. **Post-Processing** → Text formatting → Multi-format export → Quality assurance
7. **Output & Cleanup** → Secure file writing → Progress completion → Resource cleanup

### Key Architectural Components

**Modern Electron Frontend** (`video-transcriber-electron/`):
- **React + Material-UI**: Professional interface with Material Design 3
- **Settings Dialog**: Comprehensive configuration with real-time validation
- **WebSocket Integration**: Real-time progress updates and status changes
- **Security Features**: Input validation and error boundary handling
- **Professional UX**: Headless startup, keyboard shortcuts (F12, Ctrl+,)

**FastAPI Backend** (`video-transcriber-electron/backend/`):
- **REST API**: Complete API for file operations and processing control
- **WebSocket Server**: Real-time bidirectional communication
- **Security Layer**: Path validation, input sanitization, permission checking
- **Settings Management**: Persistent configuration with validation
- **Error Handling**: Comprehensive error recovery and reporting

**Enhanced Processing Pipeline** (`src/transcription/`):
- **Pipeline Orchestration**: Improved workflow management
- **Model Management**: Configurable Whisper models (base/small/medium/large)
- **Language Processing**: English-only and auto-detect options
- **Progress Tracking**: Detailed real-time progress with time estimates

**Security & Validation System**:
- **Path Traversal Protection**: Comprehensive directory security validation
- **Input Sanitization**: All user inputs validated and sanitized
- **Permission Checking**: File system access validation
- **Configuration Validation**: Real-time settings validation with feedback

**Multi-Format Output System** (`src/post_processing/`):
- **Text Processing**: Enhanced formatting and structure correction
- **Format Export**: Support for TXT, SRT, and VTT output formats
- **File Management**: Intelligent naming with conflict resolution
- **Quality Assurance**: Output validation and verification

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
- **Supported Formats**: MP4, AVI, MKV, MOV video files with comprehensive validation
- **File Size Limits**: Files >25MB automatically split into segments for optimal processing
- **Language Processing**: Configurable English-only or auto-detect language options
- **Queue Management**: Duplicate detection with user notification and automatic rejection
- **Processing Order**: FIFO (First In, First Out) with pause/resume capabilities
- **Output Formats**: Multiple format support (TXT, SRT, VTT) with user configuration

### Security & Validation Rules
- **Path Security**: Comprehensive directory traversal protection with validation
- **Input Sanitization**: All user inputs validated and sanitized before processing
- **Permission Checking**: Real-time validation of file system permissions
- **Output Directory**: Automatic validation with disk space and write permission checks
- **File Validation**: Real-time format verification and accessibility checking
- **Error Boundaries**: Secure error handling without information leakage

### Configuration Management Rules
- **Settings Persistence**: All user preferences saved between sessions
- **Real-time Validation**: Immediate feedback on configuration changes
- **Default Fallbacks**: Intelligent defaults when configuration is invalid
- **Path Validation**: Comprehensive security checks for all directory paths
- **Disk Space Monitoring**: Minimum 100MB free space requirement with warnings

### Quality Assurance Rules
- **Model Selection**: User-configurable Whisper models (base/small/medium/large)
- **Audio Quality**: Optimized 44.1kHz sample rate with intelligent preprocessing
- **Text Processing**: Enhanced formatting with sentence detection and structure correction
- **Error Handling**: Comprehensive error reporting without stopping batch processing
- **Output Validation**: Post-processing verification of generated transcript files

### Resource Management Rules
- **Temporary Files**: Aggressive cleanup with automatic garbage collection
- **Memory Management**: Intelligent chunked processing to prevent memory exhaustion
- **GPU Utilization**: Automatic CUDA detection with fallback to CPU processing
- **Thread Safety**: All operations protected with threading locks and WebSocket synchronization
- **Connection Management**: Robust WebSocket handling with automatic reconnection

### Performance & Scalability Considerations
- **Lazy Loading**: Models loaded on-demand with intelligent caching
- **Intelligent Segmentation**: Dynamic file splitting based on content and system resources
- **Memory Optimization**: Streaming processing for large files with minimal memory footprint
- **Real-time Updates**: WebSocket-based progress streaming without UI blocking
- **Batch Processing**: Efficient queue processing with detailed progress tracking
- **Error Recovery**: Graceful degradation and recovery from processing failures

### User Experience Rules
- **Professional Interface**: Headless startup without visible command prompts
- **Responsive Design**: Real-time UI updates with smooth animations and transitions
- **Keyboard Shortcuts**: Efficient workflow with F12 (DevTools) and Ctrl+, (Settings)
- **Error Communication**: Clear, actionable error messages with suggested solutions
- **Progress Transparency**: Detailed progress information with accurate time estimates
- **Settings Accessibility**: Intuitive configuration with immediate validation feedback

## Current Development Status

The project has evolved from a simple PyQt6 desktop application to a comprehensive dual-interface system with modern web technologies. Currently on branch "fix-transcript-repetition-bug" with significant architectural improvements.

### Major Version 2.0 Enhancements Completed

**🚀 Modern Electron Interface:**
- Professional React + Material-UI interface with Material Design 3
- Headless application startup without visible command prompts
- Comprehensive Settings Dialog with real-time validation
- WebSocket-based real-time progress updates
- Enhanced file operations with drag-and-drop support
- Keyboard shortcuts (F12 for DevTools, Ctrl+, for Settings)

**🔐 Enterprise-Level Security:**
- Comprehensive path traversal protection with multi-layer validation
- Input sanitization and validation for all user inputs
- File system permission checking and disk space validation
- Secure error handling without information leakage
- Complete security testing suite with 100+ test cases

**⚙️ Advanced Configuration Management:**
- Persistent settings across sessions with validation
- Multiple Whisper model options (base/small/medium/large)
- Language configuration (English-only/Auto-detect)
- Output format selection (TXT/SRT/VTT)
- Intelligent default suggestions and path validation

**📡 FastAPI Backend Architecture:**
- RESTful API with comprehensive endpoint documentation
- WebSocket server for real-time bidirectional communication
- Request/response validation with Pydantic models
- Background task processing with detailed progress tracking
- Comprehensive error handling and logging system

**🧪 Comprehensive Testing Infrastructure:**
- Security-focused testing with path traversal protection
- Integration tests for API endpoints and WebSocket communication
- Frontend component testing with React Testing Library
- End-to-end testing with realistic user workflows
- Performance and load testing capabilities

### Recent Technical Improvements
- Eliminated transcription repetition with three-layer solution
- Enhanced text processing with intelligent deduplication
- Improved audio segmentation for large files
- Optimized memory usage and resource management
- Added comprehensive logging and debugging capabilities

### Current Architecture Status
- ✅ **Dual Interface**: Both PyQt6 desktop and Electron web interfaces fully functional
- ✅ **Backend API**: Complete FastAPI backend with all endpoints implemented
- ✅ **Security**: Comprehensive security measures with full test coverage
- ✅ **Settings System**: Complete configuration management with persistence
- ✅ **Real-time Updates**: WebSocket communication for live progress tracking
- ✅ **Error Handling**: Robust error recovery and user feedback systems
- ✅ **Documentation**: Complete user, developer, API, and security documentation

### Development Focus Areas
- **Performance Optimization**: Continued improvements in processing speed and memory usage
- **User Experience**: Refinements to UI/UX based on user feedback
- **Testing Coverage**: Expanding test suite coverage for edge cases
- **Integration**: Streamlined deployment and distribution processes