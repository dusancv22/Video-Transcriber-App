# 🚀 How to Start the Video Transcriber App

## Step-by-Step Manual Startup (Recommended)

### 1. Start the FastAPI Backend First
Open **Command Prompt** or **PowerShell** and run:
```bash
cd "C:\Users\Dusan\source\repos\Video Transcriber\Video Transcriber App\video-transcriber-electron\backend"
python main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started server process
INFO:     Application startup complete.
```

**⚠️ KEEP THIS WINDOW OPEN** - The backend needs to stay running.

### 2. Test Backend is Working
Open a web browser and go to: http://127.0.0.1:8000/health

You should see: `{"status":"healthy","timestamp":"..."}`

### 3. Start the Electron Frontend
Open a **NEW** Command Prompt/PowerShell window and run:
```bash
cd "C:\Users\Dusan\source\repos\Video Transcriber\Video Transcriber App\video-transcriber-electron"
npm run dev
```

**Expected Output:**
```
VITE v5.4.19 ready in 150ms
➜  Local:   http://localhost:5175/
Electron app should launch automatically
```

### 4. Verify Everything is Working
- Electron app window should open automatically
- Look at the title bar - you should see:
  - ✅ **Green checkmark + "Connected"** = Everything working!
  - ⚠️ **Orange warning + "Connecting"** = Backend connection issue

## 🐛 Troubleshooting Common Issues

### Issue 1: "python is not recognized"
**Solution:**
```bash
# Try these alternatives:
py main.py
# or
python3 main.py
# or check if Python is installed:
python --version
```

### Issue 2: Backend won't start - Import errors
**Solution:**
```bash
# Install missing dependencies:
pip install fastapi uvicorn websockets python-multipart

# If still issues, try from the main project directory:
cd "C:\Users\Dusan\source\repos\Video Transcriber\Video Transcriber App"
python video-transcriber-electron\backend\main.py
```

### Issue 3: "npm is not recognized"
**Solution:**
```bash
# Check if Node.js is installed:
node --version
npm --version

# If not installed, download from: https://nodejs.org/
```

### Issue 4: Electron app shows "Backend Error"
**Solution:**
1. Make sure Step 1 (backend) is running first
2. Test backend with: http://127.0.0.1:8000/health
3. Check backend terminal for error messages
4. If backend is running, restart Electron app

### Issue 5: Frontend starts but no Electron window
**Solution:**
```bash
# Try starting Electron manually:
npm run dev:electron

# Or check if there are multiple Electron processes:
tasklist | findstr electron
```

## 🎯 What Should Happen When Working

### Backend Terminal (Step 1):
```
INFO: Backend components initialized successfully
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Started server process
INFO: Application startup complete
```

### Frontend Terminal (Step 3):
```
VITE v5.4.19 ready in 150ms
➜  Local: http://localhost:5175/
[Electron process starts]
```

### Electron App Window:
- Modern Material-UI interface opens
- Title bar shows "Video Transcriber" with connection status
- Three panels: "Add Files", "Processing Queue", "Progress Overview"
- Status bar at bottom shows "Backend: Connected"

## 📝 Quick Test Checklist

- [ ] Backend running on http://127.0.0.1:8000/health ✓
- [ ] Frontend Vite server on http://localhost:5175 ✓  
- [ ] Electron app window opened ✓
- [ ] Connection status shows green checkmark ✓
- [ ] Can drag/drop video files into app ✓
- [ ] Files appear in Processing Queue ✓

## 🔄 To Stop the App

1. Close the Electron app window
2. In frontend terminal: Press `Ctrl+C`
3. In backend terminal: Press `Ctrl+C`

## 🆘 If Nothing Works

Try the **absolute simplest test**:
```bash
# 1. Test Python
python --version

# 2. Test backend directly
cd "C:\Users\Dusan\source\repos\Video Transcriber\Video Transcriber App"
python -m http.server 8080
# Should show: Serving HTTP at 0.0.0.0 port 8080
# Press Ctrl+C to stop

# 3. Test Node.js
node --version

# 4. Test npm
npm --version
```

If any of these fail, you need to install the missing software first.