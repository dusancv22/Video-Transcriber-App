# PLANNING.md

## Project Overview

The Video Transcriber App is a modern hybrid desktop application that converts video files into text transcripts using OpenAI's Whisper AI model. Built with Electron, React, and FastAPI, the application provides a modern web-based interface wrapped in a desktop shell for batch processing video files with real-time progress tracking, queue management, and comprehensive error handling. The app is designed for users who need to transcribe multiple video files efficiently with professional-grade accuracy.

### Key Goals
- Convert video files (MP4, AVI, MKV, MOV) to accurate text transcripts
- Provide an intuitive desktop interface for batch processing
- Support large file handling through intelligent audio splitting
- Offer real-time progress tracking with time estimates
- Ensure reliable processing with pause/resume capabilities
- Generate clean, formatted text output

## Technology Stack

### Frontend Technologies
- **Desktop Shell:** Electron - Cross-platform desktop wrapper
- **Framework:** React 18 - Modern component-based UI framework
- **Language:** TypeScript - Type-safe JavaScript development
- **UI Library:** Material-UI v5 - Comprehensive React components
- **State Management:** Zustand - Lightweight state management
- **Build Tool:** Vite - Fast development server and bundler

### Backend Technologies
- **Language:** Python 3.8+
- **API Framework:** FastAPI - Modern async web framework
- **AI/ML:** OpenAI Whisper (via faster-whisper 0.10.0+) - Speech-to-text transcription
- **Audio Processing:** MoviePy - Video to audio conversion and manipulation
- **Deep Learning:** PyTorch (2.2.0+) - GPU acceleration support
- **WebSocket:** FastAPI WebSocket support for real-time communication

### Development Tools
- **Frontend Package Manager:** npm - Node.js package management
- **Backend Package Manager:** pip with requirements.txt
- **Testing:** pytest (Python), Jest (JavaScript)
- **Logging:** Python's built-in logging module
- **Virtual Environment:** venv for Python dependency isolation
- **Version Control:** Git with structured branching

### Dependencies
- **Media Processing:** ffmpeg-python (0.2.0) - Video/audio format handling
- **Numerical Computing:** numpy (1.24.0+) - Array operations
- **HTTP Client:** Axios - Frontend API communication
- **Hardware Acceleration:** CUDA support for GPU processing
- **Cross-Platform:** Electron Builder - Multi-platform packaging

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
- **Video File Input Processing:** Multi-format support (MP4, AVI, MKV, MOV) with validation and queue management. Handles individual files and entire directories with recursive scanning. *(Added 2025-01-08)*
- **Audio Conversion Pipeline:** Intelligent video-to-audio conversion using MoviePy with automatic file splitting for large files (>25MB). Supports temporary file management and cleanup. *(Added 2025-01-08)*
- **Whisper AI Integration:** Advanced speech-to-text using faster-whisper with large model support. Forced English language processing for consistency. GPU acceleration support when available. *(Added 2025-01-08)*
- **Modern Web Interface:** React-based Material-UI interface with drag-and-drop support, real-time progress tracking via WebSocket, and comprehensive status reporting. Includes pause/resume functionality. *(Converted 2025-01-08)*
- **Queue Management System:** Thread-safe queue with status tracking (queued, processing, completed, failed). Supports concurrent processing with proper synchronization. *(Added 2025-01-08)*
- **Progress Tracking & Time Estimation:** Real-time progress bars with ETA calculations based on historical processing times. Visual status indicators for each file. *(Added 2025-01-08)*
- **Text Post-Processing:** Advanced text formatting with sentence detection, capitalization correction, and punctuation normalization. Handles long texts through chunking. *(Added 2025-01-08)*
- **Error Handling & Recovery:** Comprehensive error reporting with graceful failure handling. Detailed logging for debugging and user feedback. *(Added 2025-01-08)*
- **Multi-Threading Architecture:** Worker thread implementation prevents UI freezing during processing. Proper thread cleanup and resource management. *(Added 2025-01-08)*
- **Output Management:** Configurable output directories with structured file naming. UTF-8 encoded text files for international character support. *(Added 2025-01-08)*

### Recently Completed Features
- **Hybrid Architecture Migration:** Successfully converted from PyQt6 to Electron + React + FastAPI architecture
  *(Status 2025-01-08: UI modernization complete, API integration complete, WebSocket communication functional)*
- **Real-time Communication:** WebSocket integration for live progress updates and status reporting
  *(Status 2025-01-08: Full implementation complete with bidirectional communication)*
- **RESTful API Layer:** Comprehensive FastAPI backend exposing all transcription functionality
  *(Status 2025-01-08: Complete API coverage with proper error handling)*

### In-Progress Features
- **Enhanced Language Detection:** While currently forced to English, the system includes infrastructure for language detection and multi-language support
  *(Status 2025-01-08: Language detection code present but disabled in favor of English-only processing)*
- **Production Build Optimization:** Finalizing Electron packaging and distribution setup
  *(Status 2025-01-08: Development environment complete, production builds in testing)*

### Enhanced by New Architecture
- **Real-time Progress:** WebSocket-based live updates eliminate UI polling and provide instant feedback
- **Modern Interface:** Material-UI components provide consistent, accessible, and responsive design
- **Cross-platform Support:** Electron enables native desktop features across Windows, macOS, and Linux
- **Scalable Communication:** RESTful API design allows future mobile or web client development
- **Improved Error Handling:** Structured API responses with detailed error information and user guidance
- **Development Experience:** Hot reload, TypeScript safety, and modern tooling for faster iteration

### Planned Features
- **Batch Export Options:** Support for multiple output formats (TXT, SRT, VTT, DOCX)
- **Advanced Audio Preprocessing:** Noise reduction and audio enhancement before transcription
- **Custom Model Support:** Ability to use different Whisper model sizes based on accuracy vs speed preferences
- **Transcription Accuracy Metrics:** Confidence scores and quality indicators
- **Configuration Management:** User preferences for model settings, output formats, and processing options
- **Plugin Architecture:** Extensible system for custom post-processing and export plugins
- **API Extensions:** External integrations and third-party tool connectivity

## Architecture

### Hybrid System Architecture
The application follows a modern hybrid architecture with clear separation between frontend and backend concerns:

**Frontend Layer (Electron + React):**
- Electron desktop shell for cross-platform native capabilities
- React 18 components with TypeScript for type safety
- Material-UI v5 for consistent, modern design system
- Zustand state management for predictable state updates
- Real-time WebSocket client for live progress updates
- RESTful API client using Axios for backend communication

**API Communication Layer:**
- RESTful endpoints for all transcription operations
- WebSocket connection for real-time progress streaming
- JSON data format for structured request/response handling
- Error handling and retry logic for network resilience
- Authentication tokens for secure API access

**Backend Layer (FastAPI + Python):**
- FastAPI async web framework for high-performance API
- WebSocket support for real-time bidirectional communication
- Preserved existing Python transcription pipeline
- TranscriptionPipeline: Orchestrates the complete processing workflow
- QueueManager: Thread-safe queue operations and status tracking
- WhisperManager: AI model management and transcription coordination
- TextProcessor: Post-processing and formatting operations

**Data Processing Layer (Preserved):**
- AudioConverter: Video-to-audio conversion and file management
- File handlers: Input validation and format verification
- Progress tracking: Real-time status updates via WebSocket
- Temporary file management and cleanup

**Infrastructure Layer:**
- Logging system with configurable levels
- Error handling and recovery mechanisms
- Cross-origin resource sharing (CORS) configuration
- Threading and synchronization primitives
- Process management for backend services

### Database Schema
**File-based system** - No traditional database. State managed through:
- Queue data structures (in-memory)
- File system for input/output management
- Temporary audio files in structured directories
- Configuration stored in object properties

### Hybrid Architecture Flow
**Frontend to Backend Communication:**
1. **User Interaction:** React components handle user input (file selection, queue management)
2. **API Requests:** Axios client sends HTTP requests to FastAPI backend
3. **Real-time Updates:** WebSocket connection streams live progress data
4. **State Management:** Zustand store updates trigger component re-renders

**Backend Processing Pipeline:**
1. **API Endpoints:** FastAPI receives requests and validates input data
2. **Queue Management:** Thread-safe queue operations via existing Python pipeline
3. **File Processing:** Preserved transcription pipeline (conversion → transcription → post-processing)
4. **Progress Streaming:** WebSocket broadcasts real-time status updates
5. **Response Handling:** JSON responses with error handling and status codes

**Data Flow Architecture:**
```
Electron Shell
├── React Frontend (Port 5173)
│   ├── Material-UI Components
│   ├── Zustand State Store
│   ├── Axios API Client
│   └── WebSocket Client
│
└── FastAPI Backend (Port 8000)
    ├── REST API Endpoints
    ├── WebSocket Server
    ├── Existing Python Pipeline
    │   ├── TranscriptionPipeline
    │   ├── QueueManager
    │   ├── WhisperManager
    │   └── TextProcessor
    └── Audio Processing Layer
```

### State Management
- **Frontend State:** Zustand store for UI state, queue status, and user preferences
- **Queue State:** Thread-safe QueueManager with atomic operations (backend)
- **Progress State:** Real-time updates via WebSocket streaming
- **UI State:** Reactive React components with automatic re-rendering
- **API State:** Axios interceptors for request/response handling
- **File State:** Temporary file tracking with automatic cleanup (backend)

## Authentication System
**Not applicable** - Desktop application with local file access only. No user authentication or network services required.

## UI/UX Patterns

### Visual Design Principles
- **Material Design:** Google's Material-UI components with consistent design language
- **Modern Interface:** Clean typography, proper spacing, and professional color palette
- **Status-Driven UI:** Visual indicators for queue item states with Material icons and colors
- **Progressive Disclosure:** Collapsible sections and conditional rendering based on state
- **Responsive Design:** Adaptive layout for different window sizes and screen densities
- **Real-time Feedback:** Live progress indicators updated via WebSocket

### Interaction Patterns
- **Drag & Drop Support:** Primary file input method for intuitive operation
- **Batch Operations:** Support for directory selection with recursive file discovery
- **Pause/Resume Control:** User control over long-running operations
- **Real-time Updates:** Live progress bars and time estimates
- **Error Recovery:** Clear error messages with actionable guidance

### Color Coding System
- **Material Primary:** Primary actions and brand elements (Material-UI theme)
- **Material Secondary:** Secondary actions and supporting elements
- **Success Green:** Completed transcriptions and success states
- **Error Red:** Failed operations and destructive actions
- **Warning Orange:** Pause states and cautionary actions
- **Info Blue:** Processing states and informational elements

## Business Rules

### File Processing Rules
- **Supported Formats:** Only MP4, AVI, MKV, MOV video files accepted
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

## Setup Instructions

### Prerequisites
- **Python:** 3.8+ with pip package manager
- **Node.js:** 16+ with npm package manager
- **System Dependencies:** FFmpeg for audio processing

### Development Setup
1. **Backend Setup:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Frontend Setup:**
   ```bash
   npm install
   ```

3. **Start Development Servers:**
   ```bash
   # Terminal 1: Start FastAPI backend
   python backend/main.py
   
   # Terminal 2: Start React development server
   npm run dev
   ```

### Detailed Documentation
- **START_INSTRUCTIONS.md:** Complete setup and development guide
- **TESTING_GUIDE.md:** Testing procedures and validation steps
- **CLAUDE.md:** Project overview and architecture context

## Deployment

### Distribution Method
- **Electron App:** Cross-platform desktop application (Windows, macOS, Linux)
- **Hybrid Architecture:** Frontend assets bundled with Electron, Python backend as subprocess
- **Dependencies Bundled:** All Node.js and Python dependencies packaged
- **Native Installation:** Standard OS-specific installers (.exe, .dmg, .deb/.rpm)

### System Requirements
- **Operating System:** Cross-platform (Windows, macOS, Linux)
- **Node.js Runtime:** Bundled with Electron
- **Python Runtime:** 3.8+ (bundled with application)
- **Hardware:** Minimum 8GB RAM, GPU recommended for faster processing
- **Storage:** Adequate space for temporary audio files during processing
- **Network:** Required for initial setup and updates (offline capable after setup)

### Build Process
```bash
# Backend setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
npm install

# Development
npm run dev          # Start frontend development server
python backend/main.py  # Start FastAPI backend

# Production build
npm run build        # Build React app
npm run electron:build  # Package Electron app
```

## Constraints & Non-Goals

### Technical Constraints
- **Desktop Application:** Electron-based desktop app with web technologies
- **English Language:** Currently optimized for English transcription only
- **Local Processing:** No cloud services or remote processing
- **Single User:** No multi-user or collaborative features
- **Hybrid Architecture:** Requires both Node.js and Python runtime environments

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
*Current Branch: fix-transcript-repetition-bug*
*Recent Focus: Hybrid architecture migration complete - Electron + React + FastAPI implementation functional with WebSocket real-time communication*