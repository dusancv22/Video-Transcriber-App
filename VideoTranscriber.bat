@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo ============================================
echo Video Transcriber
echo ============================================
echo.
echo Starting app from:
echo %CD%
echo.

"%PYTHON_EXE%" run.py
if errorlevel 1 (
    echo.
    echo ============================================
    echo Video Transcriber exited with an error.
    echo Make sure dependencies are installed:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo ============================================
    pause
    exit /b 1
)

endlocal
