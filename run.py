import sys
import subprocess
from pathlib import Path

# Prevent FFmpeg (and other console subprocesses) from opening visible
# console windows on Windows.  Must be applied before any library imports
# that spawn processes (ffmpeg-python, pydub, etc.).
if sys.platform == "win32":
    _original_popen = subprocess.Popen

    class _SilentPopen(_original_popen):
        def __init__(self, *args, **kwargs):
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    subprocess.Popen = _SilentPopen

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()