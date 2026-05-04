@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
title IDINO Career - Service Stopper

echo ============================================
echo   IDINO Career - Service Stopper
echo ============================================
echo.

echo [*] Stopping all services...
echo.

REM Define all ports to stop (auth-service uses 8011, not 8001)
set PORTS=8002 8003 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 8015 8016 8017 8018 8020 3000

REM Stop each port
for %%p in (%PORTS%) do (
    call :stop_port %%p
)

echo.
echo [*] Cleaning up orphan processes...

REM Kill any remaining Python processes related to idino_career
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%idino_career%%' and name='python.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo      Killed orphan Python PID %%a
)

REM Kill any remaining Node.js processes related to idino_career
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%idino_career%%' and name='node.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo      Killed orphan Node PID %%a
)

REM Kill wrapper cmd processes
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%uvicorn%%idino_career%%' and name='cmd.exe'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo      Killed wrapper cmd PID %%a
)

REM Kill npm processes
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%npm%%dev%%' and commandline like '%%idino_career%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /F /PID %%a >nul 2>&1
    echo      Killed npm PID %%a
)

timeout /t 2 /nobreak > nul

echo.
echo ============================================
echo   Cache Cleanup:
echo ============================================
echo.

REM Python __pycache__ directories
echo [*] Clearing Python cache (__pycache__)...
set CACHE_COUNT=0
for /d /r "E:\workspace\idino_career\services" %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d" 2>nul
        set /a CACHE_COUNT+=1
    )
)
echo      Removed %CACHE_COUNT% __pycache__ directories

REM .pyc files (in case any remain outside __pycache__)
echo [*] Clearing .pyc files...
del /s /q "E:\workspace\idino_career\services\*.pyc" 2>nul
echo      Done

REM pytest cache
echo [*] Clearing pytest cache...
for /d /r "E:\workspace\idino_career" %%d in (.pytest_cache) do (
    if exist "%%d" rd /s /q "%%d" 2>nul
)
echo      Done

REM mypy cache
echo [*] Clearing mypy cache...
for /d /r "E:\workspace\idino_career" %%d in (.mypy_cache) do (
    if exist "%%d" rd /s /q "%%d" 2>nul
)
echo      Done

REM Next.js cache (.next)
echo [*] Clearing Next.js cache...
if exist "E:\workspace\idino_career\frontend\.next\cache" (
    rd /s /q "E:\workspace\idino_career\frontend\.next\cache" 2>nul
    echo      Cleared .next/cache
) else (
    echo      No .next cache found
)

REM Node modules cache
echo [*] Clearing node_modules cache...
if exist "E:\workspace\idino_career\frontend\node_modules\.cache" (
    rd /s /q "E:\workspace\idino_career\frontend\node_modules\.cache" 2>nul
    echo      Cleared node_modules/.cache
) else (
    echo      No node_modules cache found
)

REM Ruff cache
echo [*] Clearing ruff cache...
for /d /r "E:\workspace\idino_career" %%d in (.ruff_cache) do (
    if exist "%%d" rd /s /q "%%d" 2>nul
)
echo      Done

echo.
echo ============================================
echo   Verification:
echo ============================================

REM Verify all ports are stopped
set ALL_STOPPED=1
for %%p in (%PORTS%) do (
    call :verify_port %%p
)

if %ALL_STOPPED%==1 (
    echo.
    echo   All services stopped successfully!
) else (
    echo.
    echo   [WARN] Some services may still be running.
    echo   Try running this script again or kill manually.
)

echo.
echo ============================================
endlocal
pause
exit /b 0

REM ============================================
REM Functions
REM ============================================

:stop_port
set port=%1
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%port% " ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" (
        REM Try graceful termination first
        taskkill /PID %%a >nul 2>&1
        timeout /t 1 /nobreak >nul
        REM Force kill if still running
        taskkill /F /PID %%a >nul 2>&1
        echo   [STOP] Port %port% - Killed PID %%a
    )
)
exit /b 0

:verify_port
set port=%1
netstat -aon 2>nul | findstr ":%port% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo   [X] Port %port% - still in use
    set ALL_STOPPED=0
) else (
    echo   [OK] Port %port% - stopped
)
exit /b 0
