# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Add src directory to path for imports
src_path = Path('.').absolute() / 'src'
sys.path.insert(0, str(src_path))

a = Analysis(
    ['run.py'],
    pathex=['.', 'src'],
    binaries=[],
    datas=[
        ('src', 'src'),  # Include all source files
    ],
    hiddenimports=[
        # Core transcription engine
        'faster_whisper',
        'faster_whisper.transcribe',
        'faster_whisper.vad',

        # PyTorch and audio processing
        'torch',
        'torch._C',
        'torch._C._dynamo',
        'torch._C._functorch',
        'torch._dynamo',
        'torch._functorch',
        'torchaudio',
        'torchaudio.backend',
        'torchaudio.backend.soundfile_backend',

        # Numpy
        'numpy',
        'numpy.core._multiarray_umath',

        # Audio processing libraries
        'pydub',
        'pydub.utils',
        'audioop_lts',
        'soundfile',

        # Subtitle generation
        'pysubs2',

        # Video processing
        'ffmpeg',
        'ffmpeg_python',

        # Translation support
        'transformers',
        'transformers.models',
        'transformers.models.auto',
        'sentencepiece',
        'sacremoses',
        'langdetect',
        'langdetect.lang_detect_exception',

        # PyQt6 GUI
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',

        # Standard library modules that might need explicit inclusion
        'regex',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'notebook',
        'jupyter',
        'ipython',
        'pandas',
        'tkinter',
        'PIL',  # Pillow not needed
        'cv2',  # OpenCV not needed
        'scipy',  # Not used in current version
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect all required data
a.datas += Tree('./src', prefix='src', excludes=['*.pyc', '__pycache__'])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoTranscriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,  # Add icon if available
    version_file=None,
)

# For creating a folder distribution instead of single file
# Uncomment below if you want folder distribution
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoTranscriber',
)
"""