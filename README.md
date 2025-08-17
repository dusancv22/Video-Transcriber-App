# Video Transcriber App

A powerful desktop application that converts video files into accurate text transcripts using OpenAI's Whisper AI model. Features a modern GUI built with PyQt6, batch processing capabilities, and advanced text post-processing with filler word removal.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0+-green.svg)
![Whisper](https://img.shields.io/badge/Whisper-Latest-orange.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

## ✨ Features

- **🎥 Multi-Format Support**: Process MP4, AVI, MKV, and MOV video files
- **🚀 GPU Acceleration**: Automatic CUDA detection for 10-20x faster processing
- **📦 Batch Processing**: Queue multiple videos for automated transcription
- **🧹 Advanced Text Processing**: 
  - Automatic filler word removal ("um", "uh", "like", "you know")
  - Smart punctuation and capitalization
  - Paragraph formatting for readability
- **🎯 Flexible Model Selection**: Choose from tiny, base, small, medium, or large Whisper models
- **💾 Custom Model Loading**: Load pre-downloaded models to work offline
- **📊 Real-time Progress**: Track processing with time estimates and progress bars
- **⏸️ Pause/Resume**: Control processing without losing progress
- **🎨 Modern UI**: Clean, intuitive interface with drag-and-drop support

## 📥 Installation

### Option 1: Download Pre-built Executable (Windows)

1. Download the latest `VideoTranscriber.exe` from the [Releases](https://github.com/yourusername/video-transcriber/releases) page
2. Download Whisper model files (see [Model Setup](#model-setup) below)
3. Run `VideoTranscriber.exe`

### Option 2: Run from Source

#### Prerequisites
- Python 3.11 or higher
- NVIDIA GPU (optional, for faster processing)
- CUDA 11.8 or 12.1 (if using GPU)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/video-transcriber.git
cd video-transcriber
```

#### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Install PyTorch with CUDA (for GPU support)
```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CPU only
pip install torch torchvision torchaudio
```

#### Step 5: Run the Application
```bash
python run.py
```

## 🎯 Model Setup

### Understanding Whisper Models

The app uses OpenAI's Whisper models for transcription. Each model size offers different trade-offs:

| Model | Parameters | Speed | Quality | Download Size |
|-------|------------|-------|---------|---------------|
| tiny  | 39M | Very Fast | Basic | ~39 MB |
| base  | 74M | Fast | Good | ~74 MB |
| small | 244M | Moderate | Better | ~244 MB |
| medium | 769M | Slow | Very Good | ~769 MB |
| large | 1550M | Very Slow | Best | ~1.5 GB |

### Automatic Model Download

On first use, the app will automatically download the selected model from OpenAI (requires internet connection).

### Manual Model Setup (Recommended for Offline Use)

1. **Download Model Files**
   - Download `.pt` files from [OpenAI Whisper](https://github.com/openai/whisper/releases)
   - Or from [Hugging Face](https://huggingface.co/openai)

2. **Place Models in a Folder**
   ```
   C:\WhisperModels\
   ├── tiny.pt
   ├── base.pt
   ├── small.pt
   ├── medium.pt
   └── large-v3.pt
   ```

3. **Load in Application**
   - Click "Load Model Folder" button
   - Navigate to your models folder
   - Select the folder containing `.pt` files
   - The app will remember this location

## 🚀 Usage Guide

### Basic Workflow

1. **Start the Application**
   - Run `VideoTranscriber.exe` or `python run.py`

2. **Configure Settings**
   - Select output directory for transcripts
   - Choose Whisper model size (larger = better quality, slower)
   - (Optional) Load custom model folder

3. **Add Videos**
   - Click "Add Files" to select videos
   - Or "Add Directory" to process entire folders
   - Or drag and drop files directly

4. **Process Videos**
   - Click "Start Processing"
   - Monitor progress in real-time
   - Pause/resume as needed

5. **Get Results**
   - Transcripts saved as `.txt` files
   - Same filename as video with `.txt` extension
   - Located in your selected output directory

### Advanced Features

#### GPU Acceleration
The app automatically detects and uses NVIDIA GPUs. Check status in console output:
- `Model loaded successfully on cuda` = GPU active ✅
- `Model loaded successfully on cpu` = CPU only ⚠️

#### Batch Processing Tips
- Queue processes videos in order (FIFO)
- Each video's transcript is saved immediately upon completion
- Failed videos don't stop the queue
- Time estimates improve as more videos are processed

#### Text Processing Options
The app automatically:
- Removes filler words while preserving meaning
- Adds proper punctuation and capitalization
- Creates readable paragraphs
- Fixes common transcription errors

## 🔧 Building from Source

### Creating Executable

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Run Build Script**
   ```bash
   # Windows
   build_exe.bat
   
   # Or manually
   pyinstaller VideoTranscriber.spec --clean
   ```

3. **Find Executable**
   - Located in `dist/VideoTranscriber.exe`
   - Single file, ready for distribution

### Customizing Build
Edit `VideoTranscriber.spec` to:
- Add custom icon
- Include additional files
- Modify build options

## 🐛 Troubleshooting

### Common Issues

**"No model found" error**
- Ensure `.pt` files are in the selected folder
- File names should contain model size (e.g., `large.pt`, `large-v3.pt`)

**Slow processing on CPU**
- Install CUDA-enabled PyTorch (see installation)
- Use smaller model (base or small)
- Check GPU is detected in console output

**"CUDA out of memory" error**
- Use smaller model
- Close other GPU applications
- Process shorter videos

**Transcription has repeated text**
- App includes automatic repetition removal
- Update to latest version
- Report persistent issues

### Performance Tips

1. **For Speed**: Use GPU + smaller models (base/small)
2. **For Quality**: Use large model with GPU
3. **For Long Videos**: Videos auto-split into segments
4. **For Batch Processing**: Queue overnight with large model

## 📁 Project Structure

```
video-transcriber/
├── src/
│   ├── ui/                    # GUI components
│   ├── transcription/          # Whisper integration
│   ├── audio_processing/       # Video/audio conversion
│   ├── post_processing/        # Text enhancement
│   ├── input_handling/         # File management
│   └── config/                 # Settings management
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── VideoTranscriber.spec       # PyInstaller configuration
└── build_exe.bat              # Build script
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for the amazing transcription model
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- [MoviePy](https://github.com/Zulko/moviepy) for video processing
- [PyTorch](https://pytorch.org/) for ML framework

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/video-transcriber/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/video-transcriber/discussions)

## 🚀 Roadmap

- [ ] Support for more video formats
- [ ] Real-time transcription preview
- [ ] Speaker diarization
- [ ] Multiple language support
- [ ] Cloud processing option
- [ ] Export to SRT/VTT subtitles
- [ ] Integration with video editing software

---

Made with ❤️ by [Your Name]