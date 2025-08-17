@echo off
echo ======================================
echo Video Transcriber Build Script
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please create a virtual environment first with: python -m venv venv
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade PyInstaller
echo Installing PyInstaller...
pip install --upgrade pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Build the executable
echo Building executable...
pyinstaller VideoTranscriber.spec --clean

REM Check if build was successful
if exist "dist\VideoTranscriber.exe" (
    echo.
    echo ======================================
    echo Build successful!
    echo ======================================
    echo Executable created at: dist\VideoTranscriber.exe
    echo.
    echo File size:
    for %%I in ("dist\VideoTranscriber.exe") do echo %%~zI bytes
    echo.
    echo You can now distribute the VideoTranscriber.exe file.
    echo Users will also need to download Whisper model files separately.
) else (
    echo.
    echo ======================================
    echo Build failed!
    echo ======================================
    echo Please check the error messages above.
)

pause