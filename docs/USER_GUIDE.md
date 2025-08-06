# 📖 Video Transcriber App - User Guide

## Welcome to Video Transcriber App

The Video Transcriber App is a professional-grade application that converts your video files into accurate text transcripts using OpenAI's Whisper AI technology. This guide will help you get started and make the most of all available features.

## 🚀 Getting Started

### System Requirements

**Minimum Requirements:**
- **Operating System**: Windows 10+, macOS 10.14+, or Ubuntu 18.04+
- **Processor**: Multi-core CPU (4+ cores recommended)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 5GB for AI models + space for output files
- **Internet**: Required for initial setup and model downloads

**Recommended Setup:**
- **Processor**: 8+ core CPU with high performance
- **Memory**: 32GB RAM for large video files
- **Graphics**: NVIDIA GPU with CUDA support for faster processing
- **Storage**: SSD drive for optimal performance

### Installation & First Launch

1. **Download and Install**: Follow installation instructions from README.md
2. **Launch the Application**: 
   - **Recommended**: Use the modern Electron interface with automated startup scripts
   - **Alternative**: Use the PyQt6 desktop application

3. **First Launch Setup**:
   - The application will download required AI models (this may take a few minutes)
   - Configure your preferred settings through the Settings dialog

## 🎯 Quick Start Guide

### Step 1: Launch the Application

**Recommended Method - Electron Interface:**
```bash
# Use the automated startup script (Windows)
video-transcriber-electron/start.bat
```

**Alternative - Manual Launch:**
```bash
# Terminal 1 - Start Backend
cd video-transcriber-electron/backend
python main.py

# Terminal 2 - Start Frontend
cd video-transcriber-electron
npm run dev
```

### Step 2: Configure Settings

1. **Open Settings**: Press `Ctrl+,` or click the Settings button
2. **Configure Output Directory**: Choose where transcripts will be saved
3. **Select AI Model**: Choose based on your needs (see Model Comparison below)
4. **Choose Language**: English-only (recommended) or Auto-detect
5. **Select Output Format**: TXT, SRT, or VTT format
6. **Save Settings**: Click "Save Changes"

### Step 3: Add Video Files

**Method 1 - Drag & Drop (Easiest):**
- Drag video files directly into the application window
- Files will automatically appear in the Processing Queue

**Method 2 - File Browser:**
- Click "Browse Files" button
- Select one or multiple video files
- Click "Open" to add to queue

**Method 3 - Directory Import:**
- Click the folder icon in the header
- Select a directory containing video files
- All supported video files will be added automatically

### Step 4: Start Processing

1. **Review Queue**: Check that all desired files are listed
2. **Start Processing**: Click the play button (▶️)
3. **Monitor Progress**: Watch real-time progress updates
4. **Find Results**: Completed transcripts appear in your configured output directory

## ⚙️ Detailed Settings Guide

### Accessing Settings
- **Keyboard Shortcut**: `Ctrl+,` (most convenient)
- **Menu Option**: Click Settings in the application menu
- **Button**: Click the Settings button in the interface

### Output Directory Configuration

**Setting Up Output Location:**
1. **Browse for Directory**: Click "Browse" to select a folder
2. **Manual Entry**: Type the full path to your desired location
3. **Validation**: The system automatically checks permissions and disk space
4. **Default Suggestions**: The system provides common location suggestions

**Path Requirements:**
- Must be a valid directory path
- Write permission required
- Minimum 100MB free disk space
- No special characters that could cause issues

**Recommended Locations:**
- `Documents/Video Transcripts` - Easy to find and organize
- `Desktop/Transcripts` - Quick access for immediate use
- Custom project folders - Organize by project or client

### AI Model Selection

Choose the right model based on your priorities:

| Model | File Size | Speed | Accuracy | Best For |
|-------|-----------|--------|----------|----------|
| **Base** | ~39 MB | Fastest | Good | Quick drafts, clear audio |
| **Small** | ~244 MB | Fast | Better | Balanced performance |
| **Medium** | ~769 MB | Moderate | Great | High-quality results |
| **Large** | ~1550 MB | Slower | Excellent | Maximum accuracy, professional use |

**Recommendations:**
- **For quick drafts**: Use Base or Small model
- **For professional work**: Use Medium or Large model
- **For unclear audio**: Use Large model for best results
- **For batch processing**: Consider Medium model for balance

### Language Configuration

**English Only (Recommended):**
- Processes all audio as English
- Provides most consistent results
- Best for content primarily in English
- Reduces processing time

**Auto-detect:**
- Automatically detects the spoken language
- Supports multiple languages
- May be less accurate for mixed-language content
- Slightly longer processing time

### Output Format Options

**Plain Text (.txt):**
- Simple text file with the transcription
- Easy to edit and format
- Compatible with all text editors
- Best for basic transcription needs

**SubRip (.srt):**
- Standard subtitle format with timestamps
- Compatible with most video players
- Includes timing information
- Ideal for creating subtitles

**WebVTT (.vtt):**
- Modern web subtitle format
- Enhanced formatting options
- Web-optimized
- Best for web video content

## 📁 File Management

### Supported Video Formats
- **MP4** - Most common, universally supported
- **AVI** - Legacy format, widely compatible
- **MKV** - High-quality container format
- **MOV** - Apple QuickTime format

### File Size Handling
- **Small Files** (< 25MB): Processed as single unit
- **Large Files** (> 25MB): Automatically split into segments
- **Maximum Size**: No strict limit (limited by available disk space)
- **Memory Management**: Intelligent processing prevents memory issues

### Queue Management

**Adding Files:**
- Drag and drop multiple files simultaneously
- Use file browser for precise selection
- Import entire directories with video files
- Duplicate files are automatically detected and skipped

**Queue Operations:**
- **Remove Files**: Click the X button next to any file
- **Clear Queue**: Use "Clear All" button to empty the queue
- **Reorder Files**: Processing follows the order files were added
- **View Details**: Hover over files to see size, format, and status

**File Status Indicators:**
- **⏳ Queued**: Waiting to be processed
- **⚡ Processing**: Currently being transcribed
- **✅ Completed**: Successfully transcribed
- **❌ Failed**: Error occurred (hover for details)

## 🎮 Processing Control

### Starting Processing
1. **Verify Settings**: Ensure output directory and model are configured
2. **Check Queue**: Review files to be processed
3. **Disk Space**: Ensure sufficient space for output files
4. **Start**: Click the play button to begin

### Monitoring Progress

**Real-time Updates:**
- **File Progress**: Individual file completion percentage
- **Overall Progress**: Total batch completion
- **Current Step**: Detailed processing stage information
- **Time Estimates**: Remaining time calculations
- **Statistics**: Files completed, failed, and remaining

**Progress Information:**
- **Current File**: Shows which file is being processed
- **Processing Stage**: Indicates current operation (audio extraction, transcription, etc.)
- **Speed**: Processing rate and estimated completion time
- **Queue Status**: Overview of entire batch progress

### Pausing and Resuming
- **Pause**: Click pause button (⏸️) to temporarily stop processing
- **Resume**: Click resume button to continue from where paused
- **Stop**: Click stop button (⏹️) to completely halt processing
- **File Recovery**: Partially processed files can be resumed

## 📊 Understanding Results

### Output File Locations
- Files are saved in your configured output directory
- File names match original video names with appropriate extensions
- Conflicting names automatically get numbered suffixes (e.g., `video_1.txt`)

### Quality Assessment

**High Quality Transcripts:**
- Clear speech with minimal background noise
- Use of Large model for maximum accuracy
- Proper sentence structure and punctuation
- Minimal transcription errors

**Common Issues and Solutions:**
- **Poor Audio Quality**: Use larger model or enhance audio first
- **Background Music**: May interfere with speech recognition
- **Multiple Speakers**: May require manual editing for speaker identification
- **Technical Terms**: May need manual review for specialized vocabulary

### Post-Processing Tips

**Text Formatting:**
- Review for proper punctuation and capitalization
- Check for technical terms or names that may need correction
- Consider paragraph breaks for better readability

**Subtitle Timing (SRT/VTT):**
- Verify timing accuracy with original video
- Adjust timing if needed using subtitle editing software
- Check for proper line breaks and reading speed

## 🔧 Troubleshooting Common Issues

### Connection Issues

**Backend Connection Failed:**
- Verify backend is running on port 8000
- Check if antivirus/firewall is blocking connection
- Restart both backend and frontend applications

**WebSocket Disconnected:**
- Refresh the application
- Check network stability
- Restart the application if issue persists

### Processing Errors

**File Format Not Supported:**
- Verify file is MP4, AVI, MKV, or MOV format
- Check file isn't corrupted
- Try converting to MP4 format first

**Out of Memory Errors:**
- Close other applications to free memory
- Use smaller AI model (Base or Small)
- Process fewer files simultaneously

**Disk Space Issues:**
- Free up disk space in output directory
- Choose different output location
- Clean up temporary files

### Performance Issues

**Slow Processing:**
- Use smaller AI model for faster results
- Close unnecessary applications
- Consider GPU acceleration if available

**Application Not Responding:**
- Check if processing is still active in background
- Wait for current file to complete
- Restart application if necessary

## 🔐 Privacy and Security

### Data Privacy
- **Local Processing**: All transcription happens on your computer
- **No Cloud Upload**: Your videos never leave your machine
- **No Data Collection**: Application doesn't collect or transmit personal data
- **Model Downloads**: AI models downloaded securely from OpenAI

### File Security
- **Path Protection**: Built-in security prevents unauthorized file access
- **Permission Checking**: System validates file permissions before processing
- **Secure Output**: Transcripts saved with proper file permissions
- **Cleanup**: Temporary files automatically removed after processing

## 💡 Tips and Best Practices

### For Best Results

**Audio Quality:**
- Use videos with clear, high-quality audio
- Minimize background noise when possible
- Consider audio enhancement before transcription

**Model Selection:**
- Use Large model for important/professional content
- Use smaller models for quick drafts or testing
- Consider processing time vs accuracy trade-offs

**Batch Processing:**
- Process similar content together for consistency
- Use appropriate model for the batch content
- Monitor disk space for large batches

### Workflow Optimization

**Organize Your Files:**
- Create dedicated folders for different projects
- Use consistent naming conventions
- Keep original videos and transcripts together

**Regular Maintenance:**
- Periodically clear temporary files
- Update to latest version for improvements
- Review and adjust settings based on usage

**Quality Control:**
- Always review important transcriptions
- Keep notes on model performance for different content types
- Develop templates for common corrections

## 🆘 Getting Additional Help

### Documentation Resources
- **Technical Documentation**: Check `/docs` folder for detailed technical information
- **API Reference**: Available for developers and advanced users
- **Troubleshooting Guide**: Comprehensive solutions for common issues

### Support Channels
- **GitHub Issues**: Report bugs and request features
- **Community Forums**: Connect with other users
- **Documentation**: Most questions answered in comprehensive guides

### Reporting Issues
When reporting problems, include:
- Operating system and version
- Application version
- Detailed steps to reproduce issue
- Error messages (if any)
- System specifications (CPU, RAM, GPU)

## 📈 Advanced Features

### Keyboard Shortcuts
- **Ctrl+,**: Open Settings dialog
- **F12**: Open Developer Tools (for troubleshooting)
- **Ctrl+O**: Open file browser
- **Space**: Pause/Resume processing
- **Esc**: Close current dialog

### Command Line Options
```bash
# Backend with debug logging
python main.py --log-level debug

# Custom port configuration
python main.py --port 8080

# Specific model loading
python main.py --model medium
```

### Integration Options
- **API Access**: RESTful API available for custom integrations
- **Batch Scripts**: Automate processing with custom scripts
- **Configuration Files**: Advanced settings via configuration files

## 📝 Conclusion

The Video Transcriber App provides a powerful, user-friendly solution for converting video content to text. With its dual interface options, comprehensive settings, and professional-grade accuracy, it serves both casual users and professional content creators.

**Key Takeaways:**
- Start with the Electron interface for the best experience
- Configure settings before your first transcription
- Choose AI model based on your accuracy vs speed needs
- Use drag-and-drop for fastest file addition
- Monitor progress and check results for quality

**Next Steps:**
- Explore advanced settings as you become more comfortable
- Experiment with different AI models for your content types
- Set up efficient workflows for regular transcription tasks
- Consider integrating with your existing content creation pipeline

For technical details, developer information, and advanced configuration options, refer to the additional documentation in the `/docs` directory.

---

*Happy Transcribing! 🎬→📝*