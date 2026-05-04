@echo off
echo Starting IDINO Career Services...

set PYTHONPATH=E:\workspace\idino_career

echo Starting Student Service (8002)...
start "Student Service" cmd /k "cd /d E:\workspace\idino_career\services\student-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002"

echo Starting Competency Service (8003)...
start "Competency Service" cmd /k "cd /d E:\workspace\idino_career\services\competency-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003"

echo Starting Alumni Service (8005)...
start "Alumni Service" cmd /k "cd /d E:\workspace\idino_career\services\alumni-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005"

echo Starting AI Service (8006)...
start "AI Service" cmd /k "cd /d E:\workspace\idino_career\services\ai-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8006"

echo Starting Integration Service (8007)...
start "Integration Service" cmd /k "cd /d E:\workspace\idino_career\services\integration-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8007"

echo Starting Frontend (3000)...
start "Frontend" cmd /k "cd /d E:\workspace\idino_career\frontend && npm run dev"

echo All services started!
echo.
echo Service Ports:
echo   Student:     http://localhost:8002
echo   Competency:  http://localhost:8003
echo   Alumni:      http://localhost:8005
echo   AI:          http://localhost:8006
echo   Integration: http://localhost:8007
echo   Frontend:    http://localhost:3000
echo.
echo Logs: E:\workspace\idino_career\logs\
