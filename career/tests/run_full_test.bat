@echo off
echo ========================================
echo IDINO Career - FULL Student E2E Test
echo Testing ALL 7,436 students
echo ========================================
echo.

cd /d E:\workspace\idino_career

REM Check Python
python --version 2>nul
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
pip show playwright >nul 2>&1
if errorlevel 1 (
    echo Installing playwright...
    pip install playwright psycopg2-binary
    playwright install chromium
)

echo.
echo WARNING: This will test 7,436 students.
echo Estimated time: 30-60 minutes
echo.
set /p confirm="Continue? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Running full test...
echo.
python tests\test_all_students.py

echo.
echo Test complete. Check tests\ folder for results JSON.
pause
