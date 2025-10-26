# Building Video Transcriber Executable

## Prerequisites

1. **Python Environment**: Ensure you're in the virtual environment
   ```bash
   venv\Scripts\activate
   ```

2. **Install PyInstaller**: 
   ```bash
   pip install pyinstaller==6.5.0
   ```

3. **Install All Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Build Methods

### Method 1: Quick Build (Smaller, Requires Dependencies)

```bash
pyinstaller --onefile --windowed run.py
```

This creates a single executable but may require users to have certain dependencies installed.

### Method 2: Full Build with All Dependencies (Recommended)

The project includes a pre-configured spec file for complete builds:

```bash
pyinstaller VideoTranscriber-Full.spec
```

This includes:
- All Python dependencies
- Whisper models
- FFmpeg binaries
- Translation models support
- All required DLLs

### Method 3: Custom Build with Hidden Imports

If you need to create a new spec file with all translation dependencies:

```bash
pyinstaller --name="VideoTranscriber" ^
    --windowed ^
    --onefile ^
    --icon="assets/icon.ico" ^
    --add-data="src;src" ^
    --add-data="assets;assets" ^
    --hidden-import="whisper" ^
    --hidden-import="torch" ^
    --hidden-import="transformers" ^
    --hidden-import="sentencepiece" ^
    --hidden-import="sacremoses" ^
    --hidden-import="langdetect" ^
    --hidden-import="pysubs2" ^
    --hidden-import="faster_whisper" ^
    --hidden-import="moviepy" ^
    --hidden-import="pydub" ^
    --collect-all="transformers" ^
    --collect-all="torch" ^
    --collect-all="whisper" ^
    --collect-all="faster_whisper" ^
    run.py
```

## Important Notes for Translation Support

### Including Translation Models

The Helsinki-NLP models are downloaded on first use. To include them in the executable:

1. **Pre-download Models** (Optional):
   ```python
   from transformers import pipeline
   # Pre-download commonly used models
   models = [
       'Helsinki-NLP/opus-mt-es-en',
       'Helsinki-NLP/opus-mt-en-es',
       'Helsinki-NLP/opus-mt-fr-en',
       'Helsinki-NLP/opus-mt-de-en'
   ]
   for model in models:
       pipeline("translation", model=model)
   ```

2. **Model Cache Location**:
   - Models are cached in `~/.cache/huggingface/`
   - First-time users will need internet to download models
   - Each model is 200-500MB

### FFmpeg Requirements

The application needs FFmpeg for video processing:

1. **Option 1**: Bundle FFmpeg (Increases size by ~100MB)
   - Download FFmpeg binaries
   - Place in `ffmpeg/` folder
   - Add to spec file: `--add-binary="ffmpeg/*;ffmpeg"`

2. **Option 2**: System FFmpeg
   - Users must have FFmpeg installed
   - Smaller executable size

## Build Output

After building, you'll find:
- **Single File Build**: `dist/VideoTranscriber.exe` (or `run.exe`)
- **Full Build**: `dist/VideoTranscriber-Full/VideoTranscriber-Full.exe`

## Testing the Executable

1. **Test Basic Functionality**:
   - Run the exe: `dist\VideoTranscriber.exe`
   - Try transcribing a video
   - Test subtitle generation
   - Test translation features

2. **Check for Missing Dependencies**:
   - Run from a clean environment
   - Check console for import errors
   - Add any missing modules to hidden imports

## Troubleshooting

### Common Issues:

1. **"No module named 'transformers'"**
   - Add `--collect-all="transformers"` to build command
   
2. **"Failed to execute script"**
   - Run without `--windowed` flag to see console errors
   - Check for missing data files

3. **Translation Models Not Found**
   - Ensure internet connection on first run
   - Or pre-bundle models in the build

4. **FFmpeg Not Found**
   - Bundle FFmpeg binaries
   - Or ensure users install FFmpeg separately

## Optimizing Executable Size

The full build can be large (500MB-1GB). To reduce size:

1. **Exclude Unused Torch Components**:
   ```
   --exclude-module="torch.distributions"
   ```

2. **Use UPX Compression**:
   ```bash
   pip install pyinstaller[upx]
   pyinstaller --upx-dir=path/to/upx ...
   ```

3. **Selective Model Inclusion**:
   - Only include specific Whisper model sizes
   - Limit translation language pairs

## Distribution

### Creating an Installer (Optional)

Use NSIS or Inno Setup to create a professional installer:

1. **Inno Setup Script** (`installer.iss`):
   ```iss
   [Setup]
   AppName=Video Transcriber
   AppVersion=2.0
   DefaultDirName={pf}\VideoTranscriber
   DefaultGroupName=Video Transcriber
   OutputBaseFilename=VideoTranscriber-Setup
   
   [Files]
   Source: "dist\VideoTranscriber.exe"; DestDir: "{app}"
   Source: "README.md"; DestDir: "{app}"; Flags: isreadme
   
   [Icons]
   Name: "{group}\Video Transcriber"; Filename: "{app}\VideoTranscriber.exe"
   Name: "{commondesktop}\Video Transcriber"; Filename: "{app}\VideoTranscriber.exe"
   ```

2. Compile with Inno Setup Compiler

## Final Checklist

- [ ] All dependencies in requirements.txt
- [ ] Icon file exists (if specified)
- [ ] Test on clean Windows system
- [ ] Translation features working
- [ ] Subtitle generation working
- [ ] FFmpeg accessible
- [ ] No console window in final build
- [ ] Reasonable file size (<1GB)
- [ ] Signed executable (optional, prevents Windows warnings)

## Quick Start Command

For most users, this command will work:

```bash
pyinstaller VideoTranscriber-Full.spec
```

The executable will be in `dist/VideoTranscriber-Full/`