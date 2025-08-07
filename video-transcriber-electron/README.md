# Video Transcriber App

A powerful desktop application that converts video files into accurate text transcripts using OpenAI's Whisper AI model. Features both modern Electron web interface and native PyQt6 desktop interface.

## Features

- **Dual Interface Options**: Choose between modern web-based Electron interface or native PyQt6 desktop application
- **AI-Powered Transcription**: Utilizes OpenAI's Whisper model for high-accuracy speech-to-text conversion
- **Batch Processing**: Process multiple video files with intelligent queue management
- **Multiple Format Support**: Handles MP4, AVI, MKV, MOV video files
- **Real-time Progress Tracking**: Live progress updates with accurate time estimates
- **Professional Output**: Generates clean, formatted transcripts in TXT, SRT, and VTT formats
- **Large File Handling**: Intelligent segmentation for files over 25MB
- **Enterprise Security**: Comprehensive input validation and path security protection

## Quick Start

### Electron Interface (Recommended)
```bash
# Windows quick start
cd video-transcriber-electron
start.bat

# Or using PowerShell
start.ps1
```

### PyQt6 Desktop Interface
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python run.py
```

## System Requirements

- **OS**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for models and temporary files
- **GPU**: CUDA-compatible GPU optional (for faster processing)

## Documentation

- **[User Guide](docs/user_guide/)** - Complete usage instructions
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Development setup and contribution guidelines
- **[API Reference](docs/API_REFERENCE.md)** - Backend API documentation
- **[Security Guide](docs/SECURITY.md)** - Security features and best practices

## Architecture

The application features a hybrid architecture supporting both desktop and web interfaces:

- **Frontend**: React + Material-UI (Electron) or PyQt6 (Desktop)
- **Backend**: FastAPI with WebSocket support for real-time updates
- **AI Engine**: Whisper model with configurable sizes (base/small/medium/large)
- **Processing**: Intelligent audio extraction and segmentation
- **Output**: Multi-format export with professional formatting

## Getting Help

- **Issues**: Report bugs and feature requests on GitHub Issues
- **Documentation**: Check the `docs/` folder for comprehensive guides
- **Support**: See `docs/USER_GUIDE.md` for troubleshooting

## License

This project is licensed under the MIT License - see the LICENSE file for details.