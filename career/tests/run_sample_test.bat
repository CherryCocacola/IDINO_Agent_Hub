@echo off
echo ========================================
echo IDINO Career - Sample Student E2E Test
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
echo Running sample test (30 students)...
echo.
python tests\test_sample_students.py

echo.
pause
