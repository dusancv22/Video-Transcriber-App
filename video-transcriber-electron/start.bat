@echo off

REM Start only the FastAPI Backend 
REM The frontend will be started separately via npm run dev
echo Starting Video Transcriber Backend...
start /b /min "" cmd /c "cd /d "%~dp0backend" && "..\..\venv\Scripts\python.exe" main.py"

echo Backend started. Now run 'npm run dev' from the video-transcriber-electron folder to start the frontend.
echo.
echo To start the frontend, open another terminal and run:
echo cd video-transcriber-electron
echo npm run dev
echo.
echo Both services are starting...
echo - Backend API: http://127.0.0.1:7050
echo - Frontend: http://localhost:5175
echo - Electron app should launch automatically
echo.
echo Close this window and the service windows to stop the app.
pause
