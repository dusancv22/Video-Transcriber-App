# Video Transcriber App

A powerful desktop application that converts video files to text transcripts using OpenAI's Whisper AI model. Built with PyQt6, it provides batch processing, real-time progress tracking, and professional-grade transcription accuracy.

## Features

- **AI-Powered Transcription**: Uses OpenAI's Whisper large model for high accuracy
- **Batch Processing**: Process multiple video files in queue
- **Smart File Handling**: Automatically splits large files (>25MB) for optimal processing
- **Real-Time Progress**: Visual progress bars with time estimates
- **Modern UI**: Drag-and-drop interface with pause/resume functionality
- **Format Support**: MP4, AVI, MKV, MOV video formats
- **GPU Acceleration**: Automatic CUDA support for faster processing

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/video-transcriber-app.git
cd video-transcriber-app

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Usage

```bash
# Run the application
python run.py
```

1. Launch the application
2. Add video files via "Add Files" button or drag-and-drop
3. Select output directory (optional)
4. Click "Start Processing" to begin transcription
5. Monitor progress in real-time
6. Find transcripts in the output folder

## Requirements

- Python 3.8+
- PyQt6 6.7.0+
- faster-whisper 0.10.0+
- torch 2.2.0+
- moviepy
- ffmpeg (system dependency)

## System Requirements

- **RAM**: 8GB minimum (16GB recommended for large files)
- **Storage**: 5GB for model files + space for temporary audio files
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster processing)

## Building Executable

```bash
pyinstaller --onefile --windowed run.py
```

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/test_audio_processing/
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.