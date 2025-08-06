@echo off
echo Starting Video Transcriber App...

echo.
echo [1/2] Starting FastAPI Backend...
start "FastAPI Backend" cmd /k "cd /d "%~dp0backend" && python main.py"

echo Waiting for backend to start...
timeout /t 5 > nul

echo.
echo [2/2] Starting Electron Frontend...
start "Electron Frontend" cmd /k "cd /d "%~dp0" && npm run dev"

echo.
echo Both services are starting...
echo - Backend API: http://127.0.0.1:8000
echo - Frontend: http://localhost:5175
echo - Electron app should launch automatically
echo.
echo Close this window and the service windows to stop the app.
pause