# 🎥 Video Transcriber App

A professional-grade desktop application that converts video files to accurate text transcripts using OpenAI's Whisper AI model. Features both PyQt6 desktop and modern Electron web interfaces with real-time processing, comprehensive settings management, and enterprise-level security.

## ✨ Key Features

### 🚀 **Professional Interface**
- **Headless Startup**: Clean application launch without visible command prompts
- **Modern Material UI**: Professional Electron-based interface with Material Design 3
- **Settings Dialog**: Comprehensive configuration management with validation
- **Enhanced File Operations**: Intelligent error handling and user feedback
- **Keyboard Shortcuts**: F12 for DevTools, Ctrl+, for settings

### 🤖 **AI-Powered Transcription**
- **Multiple Whisper Models**: Choose from base, small, medium, or large models
- **Language Options**: English-only or auto-detect capabilities
- **Format Support**: Export as TXT, SRT, or VTT subtitle formats
- **GPU Acceleration**: Automatic CUDA detection for faster processing

### ⚡ **Advanced Processing**
- **Batch Processing**: Handle multiple video files simultaneously
- **Smart File Handling**: Automatic splitting of large files (>25MB)
- **Real-Time Progress**: WebSocket-based live updates with detailed statistics
- **Pause/Resume**: Full control over processing workflow
- **Queue Management**: Add, remove, and organize files with drag-drop support

### 🔒 **Security & Reliability**
- **Path Validation**: Comprehensive security against directory traversal attacks
- **Input Sanitization**: Protected against malicious file inputs  
- **Comprehensive Testing**: Full test suite with security focus
- **Error Recovery**: Robust error handling with detailed reporting

### ⚙️ **Configuration Management**
- **Output Directory**: Configurable with validation and disk space checking
- **Processing Options**: Persistent settings across sessions
- **Validation**: Real-time validation of all configuration options
- **Default Suggestions**: Smart defaults for common use cases

## 🏗️ Architecture

### **Dual Interface Design**
- **PyQt6 Desktop App**: Native desktop interface with traditional widgets
- **Electron Web App**: Modern web-based interface with React and Material-UI
- **FastAPI Backend**: RESTful API with WebSocket support for real-time updates
- **Shared Processing Core**: Common transcription pipeline for both interfaces

### **System Components**
```
┌─────────────────┐    ┌─────────────────┐
│   PyQt6 GUI     │    │  Electron GUI   │
│   (Desktop)     │    │  (Web-based)    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────┐
         │   FastAPI       │
         │   Backend       │
         │   (Port 8000)   │
         └─────────────────┘
                     │
         ┌─────────────────┐
         │  Transcription  │
         │    Pipeline     │
         │  (Whisper AI)   │
         └─────────────────┘
```

## 🚀 Quick Start

### **Electron App (Recommended)**
```bash
# 1. Start the backend
cd video-transcriber-electron/backend
python main.py

# 2. In a new terminal, start the frontend
cd video-transcriber-electron
npm run dev
```

### **PyQt6 Desktop App**  
```bash
python run.py
```

### **Automatic Startup (Windows)**
```bash
# Use provided scripts for automatic startup
video-transcriber-electron/start.bat
# or
video-transcriber-electron/start.ps1
```

## ⚙️ Settings & Configuration

### **Output Settings**
- **Output Directory**: Custom path with validation and permission checking
- **Create Directories**: Automatic directory creation with parent validation
- **Disk Space Check**: Minimum 100MB free space validation
- **File Naming**: Automatic conflict resolution with incremental naming

### **Processing Options**
| Setting | Options | Description |
|---------|---------|-------------|
| **Whisper Model** | base, small, medium, large | Balance between speed and accuracy |
| **Language** | English, Auto-detect | Forced English or automatic detection |
| **Output Format** | TXT, SRT, VTT | Plain text or subtitle formats |
| **GPU Acceleration** | Auto-detect | Automatic CUDA utilization when available |

### **File Support**
- **Video Formats**: MP4, AVI, MKV, MOV
- **Max File Size**: Automatic splitting for files >25MB
- **Batch Processing**: Unlimited queue size with memory management
- **File Validation**: Real-time format and accessibility checking

## 🛠️ Installation

### **Prerequisites**
- **Python**: 3.8+ (3.10+ recommended)
- **Node.js**: 16+ (for Electron interface)
- **System Dependencies**: FFmpeg for audio processing
- **Optional**: CUDA toolkit for GPU acceleration

### **Setup Steps**
```bash
# 1. Clone repository
git clone https://github.com/yourusername/video-transcriber-app.git
cd video-transcriber-app

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Node.js dependencies (for Electron interface)
cd video-transcriber-electron
npm install
cd ..

# 4. Install in development mode
pip install -e .
```

### **Verify Installation**
```bash
# Test Python backend
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "from faster_whisper import WhisperModel; print('Whisper OK')"

# Test Node.js setup  
node --version
npm --version

# Test FFmpeg
ffmpeg -version
```

## 📖 User Guide

### **Getting Started**
1. **Launch Application**: Use startup scripts or manual launch
2. **Configure Settings**: Press Ctrl+, or use Settings menu
3. **Add Files**: Drag-drop or use file browser
4. **Start Processing**: Click play button to begin transcription
5. **Monitor Progress**: Watch real-time updates and statistics

### **Settings Configuration**
1. **Access Settings**: Keyboard shortcut Ctrl+, or menu
2. **Output Directory**: Browse and validate output location
3. **Model Selection**: Choose based on accuracy vs speed needs
4. **Language Settings**: English-only recommended for best results
5. **Format Selection**: Choose output format (TXT/SRT/VTT)

### **File Management**
- **Drag & Drop**: Intuitive file addition to processing queue
- **Directory Import**: Add entire folders with video files
- **Queue Operations**: Remove, reorder, or clear queue items
- **Status Tracking**: Real-time status updates for each file

### **Processing Control**
- **Start/Stop**: Full control over processing workflow
- **Pause/Resume**: Interrupt and continue processing
- **Progress Monitoring**: Detailed progress with time estimates
- **Error Handling**: Comprehensive error reporting and recovery

## 🧪 Testing & Quality Assurance

### **Automated Testing**
```bash
# Run all tests
python -m pytest tests/ -v

# Security tests
python -m pytest tests/integration/security/ -v

# Frontend tests
cd video-transcriber-electron
npm test
```

### **Security Testing**
- **Path Traversal Protection**: Comprehensive validation against directory attacks
- **Input Validation**: Sanitization of all user inputs
- **Permission Checks**: File system access validation
- **Error Boundary Testing**: Graceful failure handling

### **Performance Testing**
- **Large File Handling**: Files up to several GB
- **Memory Management**: Efficient processing without memory leaks
- **Concurrent Processing**: Multiple file handling capabilities
- **GPU Acceleration**: Performance comparison with/without CUDA

## 🏢 System Requirements

### **Minimum Requirements**
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 8GB minimum (16GB recommended for large files)
- **Storage**: 5GB for models + space for output files
- **Network**: Internet connection for initial model download

### **Recommended Setup**
- **CPU**: 8+ core processor with high single-thread performance
- **RAM**: 32GB for processing large video files
- **GPU**: NVIDIA GPU with CUDA support (RTX series recommended)
- **Storage**: SSD for faster I/O operations

## 🔧 Development

### **Development Commands**
```bash
# Backend development
cd backend && python main.py --reload

# Frontend development with hot reload
cd video-transcriber-electron && npm run dev

# Run specific tests
python -m pytest tests/test_transcription/ -v

# Security audit
python -m pytest tests/integration/security/path-traversal.test.ts

# Build production version
npm run build
```

### **Contributing Guidelines**
1. **Security First**: All contributions must pass security tests
2. **Test Coverage**: Maintain 80%+ test coverage for new features
3. **Documentation**: Update relevant documentation for changes
4. **Code Review**: All PRs require review and automated testing

### **Architecture Documentation**
- See `CLAUDE.md` for detailed technical architecture
- See `docs/API_REFERENCE.md` for API documentation
- See `DEVELOPER_GUIDE.md` for contributing guidelines

## 📄 Documentation

- **[User Guide](docs/USER_GUIDE.md)**: Complete end-user documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)**: Technical documentation for developers
- **[API Reference](docs/API_REFERENCE.md)**: Complete API documentation
- **[Security Guide](docs/SECURITY.md)**: Security best practices and testing
- **[Troubleshooting](video-transcriber-electron/TESTING_GUIDE.md)**: Common issues and solutions

## 🔐 Security & Privacy

### **Security Features**
- **Path Validation**: Protection against directory traversal attacks
- **Input Sanitization**: All user inputs are validated and sanitized
- **Permission Checking**: Comprehensive file system permission validation
- **Error Handling**: Secure error messages without information leakage

### **Privacy Considerations**
- **Local Processing**: All transcription occurs locally on your machine
- **No Data Collection**: Application doesn't send data to external services
- **Model Downloads**: Whisper models downloaded directly from OpenAI
- **File Privacy**: Your video files never leave your computer

## 📊 Performance & Benchmarks

### **Processing Speed** (approximate times)
| Model | File Size | GPU (RTX 4090) | CPU (Intel i9) |
|-------|-----------|----------------|----------------|
| Base | 10 minutes | ~2 minutes | ~8 minutes |
| Small | 10 minutes | ~3 minutes | ~12 minutes |
| Medium | 10 minutes | ~5 minutes | ~20 minutes |
| Large | 10 minutes | ~8 minutes | ~35 minutes |

### **Accuracy Comparison**
- **Large Model**: Highest accuracy, slower processing
- **Medium Model**: Good balance of speed and accuracy
- **Small Model**: Faster processing, good for clear audio
- **Base Model**: Fastest processing, basic accuracy

## 🆘 Support & Troubleshooting

### **Common Issues**
1. **Backend Connection Failed**: Check if port 8000 is available
2. **Model Download Failed**: Verify internet connection and disk space
3. **Processing Errors**: Check file format and permissions
4. **GPU Not Detected**: Verify CUDA installation and drivers

### **Getting Help**
- **Documentation**: Check comprehensive guides in `/docs`
- **Testing Guide**: See `video-transcriber-electron/TESTING_GUIDE.md`
- **Issues**: Report bugs with detailed system information
- **Logs**: Check application logs for detailed error information

## 📋 Changelog

### **Version 2.0 (Current)**
- ✨ Modern Electron interface with Material Design 3
- 🔧 Comprehensive Settings Dialog with validation
- 🔒 Enhanced security with path validation and input sanitization
- 📡 WebSocket-based real-time updates
- 🧪 Comprehensive testing suite with security focus
- ⚙️ Configurable output formats (TXT/SRT/VTT)
- 🚀 Headless application startup
- 🎯 Enhanced error handling and user feedback

### **Version 1.x (Legacy)**
- PyQt6 desktop interface
- Basic Whisper integration
- Simple queue management
- File drag-and-drop support

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Developer Guide](docs/DEVELOPER_GUIDE.md) and ensure all security tests pass before submitting pull requests.

---

**Built with ❤️ using OpenAI Whisper, PyQt6, React, Material-UI, and FastAPI**