@echo off
chcp 65001 > nul
title IDINO Career - Service Launcher

echo ============================================
echo   IDINO Career - Full Service Launcher
echo   Total: 17 Backend Services + Frontend
echo ============================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed.
    pause
    exit /b 1
)

REM Check if Node.js is available
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed.
    pause
    exit /b 1
)

REM Set base directory
set BASE_DIR=%~dp0

REM Set PYTHONPATH for shared module access
set PYTHONPATH=%BASE_DIR%

REM Create logs directory
if not exist "%BASE_DIR%logs" mkdir "%BASE_DIR%logs"

echo [*] Cleaning up existing processes...
REM Inline cleanup - kill all processes on known ports
for %%p in (8002 8003 8005 8006 8007 8008 8009 8010 8011 8012 8013 8014 8015 8016 8017 8018 8020 3000) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        if not "%%a"=="" if not "%%a"=="0" (
            taskkill /F /PID %%a >nul 2>&1
        )
    )
)
timeout /t 2 /nobreak > nul

echo.
echo [*] Starting all 18 services in parallel...
echo.

REM Start all backend services in parallel (no waiting between)
echo     Starting auth-service (8011)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\auth-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8011 >> "%BASE_DIR%logs\auth-service-stdout.log" 2>&1"

echo     Starting student-service (8002)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\student-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 >> "%BASE_DIR%logs\student-service-stdout.log" 2>&1"

echo     Starting competency-service (8003)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\competency-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 >> "%BASE_DIR%logs\competency-service-stdout.log" 2>&1"

echo     Starting alumni-service (8005)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\alumni-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 >> "%BASE_DIR%logs\alumni-service-stdout.log" 2>&1"

echo     Starting ai-service (8006)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\ai-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8006 >> "%BASE_DIR%logs\ai-service-stdout.log" 2>&1"

echo     Starting skill-service (8007)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\skill-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8007 >> "%BASE_DIR%logs\skill-service-stdout.log" 2>&1"

echo     Starting opportunity-service (8008)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\opportunity-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 >> "%BASE_DIR%logs\opportunity-service-stdout.log" 2>&1"

echo     Starting coaching-service (8009)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\coaching-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8009 >> "%BASE_DIR%logs\coaching-service-stdout.log" 2>&1"

echo     Starting risk-service (8010)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\risk-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8010 >> "%BASE_DIR%logs\risk-service-stdout.log" 2>&1"

echo     Starting badge-service (8012)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\badge-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8012 >> "%BASE_DIR%logs\badge-service-stdout.log" 2>&1"

echo     Starting simulation-service (8013)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\simulation-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8013 >> "%BASE_DIR%logs\simulation-service-stdout.log" 2>&1"

echo     Starting advisor-service (8014)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\advisor-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8014 >> "%BASE_DIR%logs\advisor-service-stdout.log" 2>&1"

echo     Starting roadmap-service (8015)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\roadmap-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8015 >> "%BASE_DIR%logs\roadmap-service-stdout.log" 2>&1"

echo     Starting portfolio-service (8016)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\portfolio-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8016 >> "%BASE_DIR%logs\portfolio-service-stdout.log" 2>&1"

echo     Starting privacy-service (8017)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\privacy-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8017 >> "%BASE_DIR%logs\privacy-service-stdout.log" 2>&1"

echo     Starting worknet-service (8018)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\worknet-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8018 >> "%BASE_DIR%logs\worknet-service-stdout.log" 2>&1"

echo     Starting notification-service (8020)...
start "" /B cmd /c "cd /d "%BASE_DIR%services\notification-service" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8020 >> "%BASE_DIR%logs\notification-service-stdout.log" 2>&1"

echo     Starting frontend (3000)...
if not exist "%BASE_DIR%frontend\node_modules" (
    echo     Installing npm dependencies...
    cd /d "%BASE_DIR%frontend" && npm install
)
start "" /B cmd /c "cd /d "%BASE_DIR%frontend" && npm run dev >> "%BASE_DIR%logs\frontend-stdout.log" 2>&1"

echo.
echo [*] All services started. Waiting 30 seconds for initialization...
echo.
timeout /t 30 /nobreak

echo.
echo ============================================
echo   Service Status:
echo ============================================
echo.
echo   --- Core Services ---
netstat -aon 2>nul | findstr ":8011 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] auth-service) || (echo   [X]  auth-service - FAILED)
netstat -aon 2>nul | findstr ":8002 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] student-service) || (echo   [X]  student-service - FAILED)
netstat -aon 2>nul | findstr ":8003 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] competency-service) || (echo   [X]  competency-service - FAILED)
netstat -aon 2>nul | findstr ":8005 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] alumni-service) || (echo   [X]  alumni-service - FAILED)
netstat -aon 2>nul | findstr ":8006 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] ai-service) || (echo   [X]  ai-service - FAILED)
echo.
echo   --- P1 Services ---
netstat -aon 2>nul | findstr ":8007 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] skill-service) || (echo   [X]  skill-service - FAILED)
netstat -aon 2>nul | findstr ":8008 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] opportunity-service) || (echo   [X]  opportunity-service - FAILED)
netstat -aon 2>nul | findstr ":8009 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] coaching-service) || (echo   [X]  coaching-service - FAILED)
netstat -aon 2>nul | findstr ":8010 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] risk-service) || (echo   [X]  risk-service - FAILED)
echo.
echo   --- P2 Services ---
netstat -aon 2>nul | findstr ":8012 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] badge-service) || (echo   [X]  badge-service - FAILED)
netstat -aon 2>nul | findstr ":8013 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] simulation-service) || (echo   [X]  simulation-service - FAILED)
netstat -aon 2>nul | findstr ":8014 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] advisor-service) || (echo   [X]  advisor-service - FAILED)
netstat -aon 2>nul | findstr ":8015 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] roadmap-service) || (echo   [X]  roadmap-service - FAILED)
netstat -aon 2>nul | findstr ":8016 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] portfolio-service) || (echo   [X]  portfolio-service - FAILED)
echo.
echo   --- Additional Services ---
netstat -aon 2>nul | findstr ":8017 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] privacy-service) || (echo   [X]  privacy-service - FAILED)
netstat -aon 2>nul | findstr ":8018 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] worknet-service) || (echo   [X]  worknet-service - FAILED)
netstat -aon 2>nul | findstr ":8020 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] notification-service) || (echo   [X]  notification-service - FAILED)
echo.
echo   --- Frontend ---
netstat -aon 2>nul | findstr ":3000 " | findstr "LISTENING" >nul 2>&1 && (echo   [OK] frontend) || (echo   [X]  frontend - FAILED)

echo.
echo ============================================
echo   Log files: %BASE_DIR%logs\
echo   To stop all services: run stop.bat
echo ============================================
echo.

pause
