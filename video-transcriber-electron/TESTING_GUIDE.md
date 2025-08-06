# Video Transcriber Testing & Troubleshooting Guide

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
# Windows Command Prompt
start.bat

# Or PowerShell (with error checking)
powershell -ExecutionPolicy Bypass -File start.ps1
```

### Option 2: Manual Startup
```bash
# Terminal 1 - Start FastAPI Backend
cd backend
python main.py

# Terminal 2 - Start Electron Frontend  
npm run dev
```

## 🔍 Testing Checklist

### 1. Backend Health Check
```bash
# Test if backend is running
curl http://127.0.0.1:8000/health
# Expected: {"status":"healthy","timestamp":"..."}

# Test API status
curl http://127.0.0.1:8000/api/status
# Expected: {"status":"running","python_version":"...","backend_connected":true}

# View API documentation
# Open: http://127.0.0.1:8000/docs
```

### 2. Frontend Connection Test
- Open Electron app (should launch automatically)
- Check connection status in title bar:
  - ✅ Green checkmark = Connected
  - ⚠️ Orange warning = Connecting/Disconnected
- Open DevTools (F12) and check console for errors

### 3. File Operations Test
1. **Drag & Drop Test:**
   - Drag a video file (.mp4, .avi, .mkv, .mov) into the drop zone
   - File should appear in Processing Queue panel
   
2. **File Dialog Test:**
   - Click "Browse Files" button
   - Select video files using file dialog
   - Files should be added to queue

3. **Directory Test:**
   - Click folder icon in header
   - Select a directory containing video files
   - All valid video files should be added

### 4. Processing Test
1. Add files to queue
2. Click "Start" button
3. Monitor progress in real-time
4. Check WebSocket updates in DevTools

## 🐛 Common Issues & Solutions

### Issue 1: "Connection Refused" Errors
**Symptoms:** Red API errors in DevTools console
```
Failed to load resource: net::ERR_CONNECTION_REFUSED
```

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
2. Check if port 8000 is blocked by firewall
3. Restart backend with verbose logging:
   ```bash
   cd backend
   python main.py --log-level debug
   ```

### Issue 2: WebSocket Connection Failures
**Symptoms:** WebSocket errors in DevTools
```
WebSocket connection to 'ws://127.0.0.1:8000/ws' failed
```

**Solutions:**
1. Ensure backend WebSocket endpoint is running
2. Check browser WebSocket support
3. Test WebSocket manually:
   ```javascript
   // In browser console
   const ws = new WebSocket('ws://127.0.0.1:8000/ws');
   ws.onopen = () => console.log('WebSocket connected');
   ws.onerror = (error) => console.error('WebSocket error:', error);
   ```

### Issue 3: Python Backend Import Errors
**Symptoms:** Backend fails to start with import errors
```
Error importing existing modules: cannot import name '...'
```

**Solutions:**
1. Install missing dependencies:
   ```bash
   pip install fastapi uvicorn websockets python-multipart
   ```
2. Check Python path and virtual environment
3. Backend will run with limited functionality if some imports fail

### Issue 4: Electron App Won't Launch
**Symptoms:** Vite starts but Electron doesn't open
```
wait-on http://localhost:5175 && ... electron .
```

**Solutions:**
1. Check if port 5175 is correct:
   ```bash
   # Should show Vite running on 5175
   curl http://localhost:5175
   ```
2. Manually launch Electron:
   ```bash
   npm run dev:electron
   ```
3. Check Electron installation:
   ```bash
   npx electron --version
   ```

### Issue 5: File Operations Not Working
**Symptoms:** Files don't appear in queue after drag/drop

**Solutions:**
1. Check file permissions
2. Verify file formats are supported (.mp4, .avi, .mkv, .mov)
3. Check DevTools console for specific error messages
4. Test with a small sample video file

## 📊 Debugging Tools

### 1. API Testing with curl
```bash
# Test file upload
curl -X POST "http://127.0.0.1:8000/api/files/add" \
  -H "Content-Type: application/json" \
  -d '{"files": ["C:/path/to/video.mp4"]}'

# Test queue status
curl http://127.0.0.1:8000/api/queue

# Test processing start
curl -X POST "http://127.0.0.1:8000/api/processing/start" \
  -H "Content-Type: application/json" \
  -d '{"output_directory": "C:/Output"}'
```

### 2. Browser DevTools Monitoring
- **Network tab:** Monitor API calls and responses
- **Console tab:** Check for JavaScript errors
- **WebSocket tab:** Monitor real-time connections
- **Application tab:** Check local storage and session data

### 3. Backend Logs
- FastAPI logs show in terminal where backend was started
- Look for uvicorn INFO messages and error tracebacks
- WebSocket connections show as "connection open" messages

### 4. Performance Monitoring
- Check CPU and memory usage during processing
- Monitor file I/O operations
- Watch network traffic between frontend and backend

## 🎯 Expected Behavior

### Normal Startup Sequence
1. Backend starts on port 8000 ✅
2. Frontend Vite server starts on port 5175 ✅
3. Electron app launches automatically ✅
4. WebSocket connection establishes ✅
5. Connection indicator shows green checkmark ✅

### Normal File Processing Flow
1. User adds files → Files appear in queue as "Queued" ✅
2. User clicks Start → Processing begins, status changes to "Processing" ✅
3. Real-time progress updates via WebSocket ✅
4. Completion → Status changes to "Completed", output file created ✅

### UI State Indicators
- **Connection Status:** Green (connected) / Orange (connecting) / Red (error)
- **Processing Status:** "Ready" / "Processing" / "Paused" / "Completed"
- **Queue Statistics:** Live count of queued/processing/completed files
- **Progress Overview:** Real-time processing metrics

## 📞 Getting Help

If issues persist:
1. Check this guide for common solutions
2. Review backend logs for specific error messages
3. Test each component individually (backend, frontend, WebSocket)
4. Use browser DevTools to diagnose client-side issues
5. Verify all dependencies are installed and up to date

## 🔧 Development Mode Features
- **Hot reload:** Frontend updates automatically on code changes
- **API documentation:** Available at http://127.0.0.1:8000/docs
- **Debug logging:** Detailed console output in development
- **Error boundaries:** Graceful error handling in React components