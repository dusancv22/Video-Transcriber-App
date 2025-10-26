@echo off
echo ============================================
echo Video Transcriber App
echo ============================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first:
    echo   1. python -m venv venv
    echo   2. venv\Scripts\activate
    echo   3. pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Video Transcriber App...
echo.
python run.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ============================================
    echo Application exited with errors
    echo ============================================
    pause
)
