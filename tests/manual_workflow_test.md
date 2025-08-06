# Manual Workflow Verification Test Guide

**CRITICAL FIXES VERIFICATION**  
After fixing both Browse button and Python PATH issues, this manual test guide verifies the complete application workflow functions end-to-end.

## Test Overview

**Critical Fixes Applied:**
1. ✅ **Browse Button Fix**: Electron dialog API properly exposed for directory selection
2. ✅ **Python PATH Fix**: start.bat uses correct virtual environment Python path

**What We're Testing:**
- Complete application startup without errors
- Settings dialog functionality with working Browse button
- End-to-end video processing workflow
- Error handling and recovery mechanisms
- User experience quality

---

## Test 1: Backend Startup Verification

**Objective:** Verify Python backend starts without Python PATH errors

### Test Steps:

1. **Navigate to Electron app directory:**
   ```
   cd "C:\Users\Dusan\source\repos\Video Transcriber\Video Transcriber App\video-transcriber-electron\"
   ```

2. **Run start.bat:**
   ```
   start.bat
   ```

3. **Expected Results:**
   - ✅ Backend starts without Python PATH errors
   - ✅ No "Python was not found" messages
   - ✅ FastAPI server runs on port 8000
   - ✅ Console shows: "Server starting on http://127.0.0.1:8000"

4. **Verify API accessibility:**
   - Open browser to: `http://127.0.0.1:8000`
   - Should see API documentation or status page
   - Test endpoints: `/api/status`, `/api/queue`

### Success Criteria:
- [ ] start.bat runs without Python errors
- [ ] Backend API accessible at http://127.0.0.1:8000
- [ ] No B:/ drive errors or hardcoded paths
- [ ] Virtual environment Python is used

### If Test Fails:
- Check start.bat uses correct Python path: `%~dp0..\..\venv\Scripts\python.exe`
- Verify virtual environment exists and contains Python
- Check for typos in Python path

---

## Test 2: Directory Browsing Functionality

**Objective:** Verify Browse button opens native directory picker

### Test Steps:

1. **Start the Electron application:**
   ```
   npm start
   ```

2. **Open Settings Dialog:**
   - Click "Start" button (should open Settings Dialog first)
   - Or click Settings button if available

3. **Test Browse Button:**
   - Click "Browse" button next to "Output Directory"
   - **CRITICAL:** Native Windows directory picker should open
   - Select a directory (e.g., Desktop or Documents)
   - Click "Select Folder"

4. **Verify Directory Selection:**
   - Selected directory path should appear in input field
   - Path should be valid Windows path format
   - No B:/ drive references

5. **Save Settings:**
   - Click "Save & Start Processing"
   - Settings should persist to localStorage

### Success Criteria:
- [ ] Browse button opens native directory picker
- [ ] Selected directory populates input field correctly
- [ ] Settings are saved and persist
- [ ] No hardcoded paths or B:/ drive errors

### If Test Fails:
- Check main.js has dialog API exposed: `ipcMain.handle('show-directory-dialog')`
- Verify contextIsolation is disabled or preload script exists
- Check for JavaScript console errors

---

## Test 3: Complete End-to-End Workflow

**Objective:** Full video transcription from start to finish

### Test Steps:

1. **Prepare Test Video:**
   - Use a small video file (under 100MB recommended)
   - Formats: MP4, AVI, MKV, or MOV

2. **Add Video to Queue:**
   - Drag and drop video file onto application
   - OR use "Add Files" button
   - Verify file appears in queue with correct status

3. **Configure Settings:**
   - Set Output Directory to a valid location
   - Choose Model: "base" (faster) or "large" (better quality)
   - Select Format: TXT, SRT, or VTT
   - Save settings

4. **Start Processing:**
   - Click "Start Processing"
   - Verify backend receives ProcessingOptions correctly

5. **Monitor Progress:**
   - Progress bar should update in real-time
   - Status messages should be clear and informative
   - Time estimates should be reasonable (NOT 1 minute mock processing)

6. **Verify Output:**
   - Output file created in specified directory
   - File contains actual transcript text
   - Processing time is realistic (15-30+ minutes for larger files)

### Success Criteria:
- [ ] Video files added to queue successfully
- [ ] Settings configuration works correctly
- [ ] Processing uses real Whisper (not mock processing)
- [ ] Output file created in user-specified directory
- [ ] Processing time is realistic for file size
- [ ] Complete workflow from file addition to transcript completion

### Expected Processing Times:
- Small video (1-5 min): 5-15 minutes
- Medium video (5-20 min): 15-45 minutes  
- Large video (20+ min): 45+ minutes

### If Test Fails:
- Check WebSocket connection between frontend/backend
- Verify Whisper models are downloaded and accessible
- Check file permissions for output directory

---

## Test 4: Error Recovery Testing

**Objective:** Verify error handling and recovery mechanisms

### Test Scenarios:

#### 4.1 Invalid Output Directory
1. Set output directory to invalid path: `Z:\nonexistent\path`
2. Try to save settings
3. Should show clear error message
4. Should not crash application

#### 4.2 Backend Unavailable
1. Stop backend server
2. Try to add files to queue
3. Should handle disconnection gracefully
4. Should show appropriate error message

#### 4.3 Unsupported File Format
1. Try to add unsupported file (e.g., .txt, .doc)
2. Should reject file with clear message
3. Should not crash application

#### 4.4 Permission Denied
1. Set output directory to protected location (e.g., C:\Windows)
2. Try to process video
3. Should handle permission error gracefully

### Success Criteria:
- [ ] Clear error messages for all failure scenarios
- [ ] Application doesn't crash on errors
- [ ] Users can recover from errors easily
- [ ] Error messages suggest solutions

---

## Test 5: User Experience Validation

**Objective:** Verify overall user experience quality

### Test Areas:

#### 5.1 First-Run Experience
1. **Fresh Installation Test:**
   - Delete any existing settings/cache
   - Start application for "first time"
   - Should guide user through initial setup

2. **Settings-First Workflow:**
   - Click "Start" should open Settings Dialog
   - Clear guidance on what each setting does
   - Help text or tooltips available

#### 5.2 Professional Appearance
1. **Startup Behavior:**
   - No command prompt windows visible
   - Clean application launch
   - Professional branding/icons

2. **Error Presentation:**
   - Errors shown in UI, not console
   - User-friendly error messages
   - Clear recovery instructions

#### 5.3 Workflow Intuitiveness
1. **File Management:**
   - Drag-and-drop works smoothly
   - Queue management is clear
   - File status indicators are helpful

2. **Processing Feedback:**
   - Progress indication is meaningful
   - Time estimates are helpful
   - Clear completion notifications

### Success Criteria:
- [ ] Professional startup (no command prompts visible)
- [ ] Settings-first workflow guides users
- [ ] Clear error messages and recovery options
- [ ] Intuitive UI with helpful guidance
- [ ] Good first-run experience for new users

---

## Test Results Documentation

### Test Result Template:

For each test, record:

```
## Test [Number]: [Name]
**Date:** [Date]
**Tester:** [Name]
**Result:** ✅ PASSED / ❌ FAILED / ⚠️ PARTIAL

**Details:**
- [What worked]
- [What didn't work]
- [Issues encountered]

**Evidence:**
- Screenshots: [if applicable]
- Error messages: [if any]
- Log files: [if relevant]

**Follow-up Actions:**
- [Any required fixes]
- [Additional testing needed]
```

### Overall Workflow Status:

**CRITICAL SUCCESS CRITERIA:**
- [ ] start.bat runs without Python errors
- [ ] Backend API accessible at http://127.0.0.1:8000
- [ ] Browse button opens directory picker
- [ ] Settings Dialog saves configuration
- [ ] Processing uses real Whisper (not mock)
- [ ] Output files created in configured directory
- [ ] Processing time is realistic (15-30+ minutes for large files)
- [ ] No B:/ drive errors or hardcoded paths

**WORKFLOW STATUS:**
- ✅ **WORKING**: All critical criteria met, application ready for users
- ⚠️ **MOSTLY WORKING**: Core functionality works, minor issues remain  
- ❌ **BROKEN**: Critical failures prevent normal operation

### Recommendations:

**If All Tests Pass:**
- Application is ready for normal use
- Consider user acceptance testing
- Document any remaining minor issues

**If Critical Tests Fail:**
- Address critical issues before user testing
- Focus on Browse button and Python PATH fixes
- Verify all hardcoded paths are removed

**If Performance Issues:**
- Test with larger video files
- Verify Whisper model optimization
- Check resource usage during processing

---

## Automated Test Execution

You can also run automated tests:

```bash
# Run Python workflow verification tests
cd "C:\Users\Dusan\source\repos\Video Transcriber\Video Transcriber App"
python -m pytest tests/test_workflow_verification.py -v

# Run specific test
python tests/test_workflow_verification.py
```

---

**IMPORTANT NOTES:**

1. **Real Processing Required:** Tests must use actual Whisper processing, not mock/simulation
2. **Realistic Timing:** Processing should take 15-30+ minutes for substantial videos
3. **User Perspective:** Test from a new user's perspective, not developer assumptions
4. **Complete Workflow:** Test the full journey from startup to completed transcript
5. **Error Scenarios:** Don't skip error testing - it's critical for user experience

**After completing all tests, the application should provide a reliable, professional video transcription experience for end users.**