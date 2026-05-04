@echo off
REM Kill process on port 8002
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8002 " ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" (
        taskkill /F /PID %%a
    )
)
timeout /t 2 /nobreak > nul

REM Start student service
cd /d E:\workspace\idino_career\services\student-service
start "" /B cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8002"
echo Student service restarting on port 8002...
