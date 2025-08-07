@echo off
echo.
echo ========================================
echo   WORKFLOW VERIFICATION TEST RUNNER
echo ========================================
echo.
echo Testing both critical fixes:
echo   1. Browse Button Fix (Electron dialog API)
echo   2. Python PATH Fix (start.bat virtual environment)
echo.

REM Change to project directory
cd /d "%~dp0"

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Run comprehensive tests
echo.
echo Running comprehensive verification tests...
echo.
python tests\run_comprehensive_tests.py

REM Also run manual test guide
echo.
echo ========================================
echo   MANUAL TEST GUIDE
echo ========================================
echo.
echo For manual testing, see:
echo   tests\manual_workflow_test.md
echo.

pause