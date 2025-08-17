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
        'whisper',
        'whisper.model',
        'whisper.audio',
        'whisper.decoding',
        'whisper.tokenizer',
        'whisper.utils',
        'torch',
        'torch._C',
        'torch._C._dynamo',
        'torch._C._functorch',
        'torch._dynamo',
        'torch._functorch',
        'torchaudio',
        'torchvision',
        'numpy',
        'numpy.core._multiarray_umath',
        'scipy',
        'scipy.signal',
        'moviepy',
        'moviepy.editor',
        'moviepy.video.io.VideoFileClip',
        'moviepy.audio.io.AudioFileClip',
        'imageio',
        'imageio_ffmpeg',
        'ffmpeg',
        'ffmpeg_python',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'numba',
        'numba.core',
        'numba.cuda',
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        'regex',
        'openai_whisper',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'notebook',
        'jupyter',
        'ipython',
        'pandas',
        'tkinter',
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