# File Drop & Dual Instance Issues - FIXED

## Issues Fixed

### 1. ✅ **File Path Extraction Error**
- **Problem**: `Cannot read properties of undefined (reading 'getPathForFile')`
- **Root Cause**: `webUtils.getPathForFile()` was not available in Electron 28.2.0
- **Solution**: Replaced with IPC-based file handling approach

### 2. ✅ **Dual Application Instances**
- **Problem**: `start.bat` launched both backend and frontend, and `npm run dev` also launched both
- **Root Cause**: Double-execution of processes
- **Solution**: Modified `start.bat` to only start backend, created `start-dev.bat` for proper development workflow

### 3. ✅ **Native File Drop Handling**
- **Problem**: Drag-and-drop files didn't have accessible file paths
- **Solution**: Implemented native file drop handling in main Electron process with IPC communication

## Technical Changes Made

### A. Electron Main Process (`electron/main.ts`)
- ✅ Added `file:selectVideoFiles` IPC handler for browse dialog
- ✅ Added `file:getFilePathsFromDrop` IPC handler (future enhancement)
- ✅ Implemented `setupFileDropHandling()` with native drag/drop support
- ✅ Added JavaScript injection to handle file drops at OS level

### B. Preload Script (`electron/preload.ts`)
- ✅ Removed `webUtils` dependency
- ✅ Added IPC-based file utilities API
- ✅ Updated TypeScript interfaces

### C. Frontend Component (`src/components/FileDropZone.tsx`)
- ✅ Updated file selection to use new IPC API
- ✅ Added native file drop event listener
- ✅ Improved error handling and user feedback
- ✅ Added comprehensive logging for debugging

### D. Startup Scripts
- ✅ Modified `start.bat` to prevent dual instances
- ✅ Created `start-dev.bat` for proper development workflow

### E. TypeScript Definitions (`src/types/electron.d.ts`)
- ✅ Updated to reflect new file API structure

## How It Works Now

### File Selection Methods:
1. **Browse Button**: Uses native Electron dialog via IPC
2. **Drag & Drop**: Uses native OS file drop handling via main process

### Startup Process:
1. Use `start.bat` to start backend only
2. Use `npm run dev` to start frontend with Electron
3. Or use `start-dev.bat` for automated development startup

## Testing Steps

1. **Start the application**:
   ```bash
   cd video-transcriber-electron
   start-dev.bat
   ```

2. **Test Browse Functionality**:
   - Click the drop zone or "Browse Files" button
   - Select video files (.mp4, .avi, .mkv, .mov)
   - Verify files are added to the queue with full paths

3. **Test Drag & Drop**:
   - Drag video files from File Explorer
   - Drop them on the drop zone
   - Verify files are detected and added with full paths

4. **Check Console Logs**:
   - Press F12 to open DevTools
   - Look for file path information in console
   - Verify no "undefined" or path extraction errors

5. **Test Transcription**:
   - Add files to queue
   - Click Settings/Start button
   - Configure output directory
   - Start transcription process
   - Monitor progress and completion

## Debug Information

### Console Logs to Look For:
- `"Using IPC-based file selection..."` - Browse working
- `"Received native file drop: [paths]"` - Drag/drop working
- `"Selected file paths via IPC: [paths]"` - IPC communication working
- File paths should be absolute (e.g., `C:\Users\...`) not just filenames

### API Endpoints for Testing:
- `GET http://127.0.0.1:8000/api/health` - Backend status
- `GET http://127.0.0.1:8000/api/debug/queue` - Queue inspection
- `GET http://127.0.0.1:8000/api/status` - Component status

## Expected Results

After these fixes:
- ✅ No more "getPathForFile" errors
- ✅ Only one application instance opens
- ✅ Drag & drop works with full file paths
- ✅ Browse button works reliably
- ✅ Files are added to queue with absolute paths
- ✅ Backend can find and process the files
- ✅ Transcription workflow functions correctly

## Troubleshooting

If issues persist:

1. **Check backend logs** - Look for file path validation errors
2. **Use debug endpoint** - `http://127.0.0.1:8000/api/debug/queue`
3. **Verify file paths** - Ensure they're absolute, not relative
4. **Check permissions** - Ensure files are accessible
5. **Restart application** - Close all instances and restart

The core file handling issues have been resolved with this comprehensive IPC-based approach.