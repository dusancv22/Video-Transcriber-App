@echo off
echo Starting Video Transcriber in Development Mode...
echo.

REM Check if backend is already running
netstat -an | findstr "127.0.0.1:7050" >nul
if %errorlevel% == 0 (
    echo Backend already running on port 7050
) else (
    echo Starting FastAPI Backend...
    start /b "" cmd /c "cd /d "%~dp0backend" && "..\..\venv\Scripts\python.exe" main.py"
    
    echo Waiting for backend to initialize...
    timeout /t 5 > nul
)

echo Starting Electron Frontend...
npm run dev

echo.
echo Both backend and frontend are now running.
pause