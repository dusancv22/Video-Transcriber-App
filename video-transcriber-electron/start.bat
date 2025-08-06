@echo off

REM Start FastAPI Backend in background (hidden)
start /b /min "" cmd /c "cd /d "%~dp0backend" && python main.py"

REM Wait for backend to start
timeout /t 5 > nul

REM Start Electron Frontend in background (hidden)
start /b /min "" cmd /c "cd /d "%~dp0" && npm run dev"

REM Exit immediately (headless mode)
exit