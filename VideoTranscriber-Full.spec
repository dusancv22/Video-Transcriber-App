# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Video Transcriber App (PyInstaller 6.x).

Builds a one-FOLDER distribution (dist/VideoTranscriber/VideoTranscriber.exe):
much faster startup than onefile, which would extract ~2GB of torch/
transformers to temp on every launch.

Build:  ./venv/Scripts/python.exe -m PyInstaller VideoTranscriber-Full.spec
Runtime requirement: ffmpeg must be available on PATH.
Whisper/translation models download to the user cache on first use.
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

datas = []
binaries = []
hiddenimports = []

# Packages whose data files / dynamic imports PyInstaller can't fully discover
for package in ('faster_whisper', 'pysubs2', 'sacremoses'):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# langdetect needs its language profile data files
datas += collect_data_files('langdetect')

# Application assets (icons)
datas += [('assets', 'assets')]

hiddenimports += [
    'pydub',
    'pydub.utils',
    'soundfile',
    'ffmpeg',
    'langdetect',
    'transformers',
    'sentencepiece',
]

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Not used by the app - keep the bundle smaller
        'matplotlib',
        'notebook',
        'jupyter',
        'IPython',
        'pandas',
        'tkinter',
        'PIL',
        'cv2',
        'scipy',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VideoTranscriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Windowed app - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='VideoTranscriber',
)
