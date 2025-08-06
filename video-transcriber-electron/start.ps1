# Video Transcriber App Startup Script
Write-Host "🎬 Starting Video Transcriber App..." -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    python --version | Out-Null
    Write-Host "✅ Python is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python first." -ForegroundColor Red
    pause
    exit 1
}

# Check if Node.js is available
try {
    node --version | Out-Null
    Write-Host "✅ Node.js is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "🐍 Starting FastAPI Backend..." -ForegroundColor Yellow

# Start backend in new window
$backendJob = Start-Job -ScriptBlock {
    Set-Location "$using:PSScriptRoot\backend"
    python main.py
}

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/status" -TimeoutSec 5
    Write-Host "✅ Backend is running on http://127.0.0.1:8000" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend may still be starting..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⚛️  Starting Electron Frontend..." -ForegroundColor Yellow

# Start frontend
try {
    Set-Location $PSScriptRoot
    npm run dev
} catch {
    Write-Host "❌ Failed to start frontend. Make sure npm dependencies are installed." -ForegroundColor Red
    Write-Host "Run: npm install" -ForegroundColor Yellow
    pause
}

# Cleanup
Write-Host ""
Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
Remove-Job -Job $backendJob -ErrorAction SilentlyContinue