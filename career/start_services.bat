@echo off
start "portfolio-service" cmd /c "cd /d E:\workspace\idino_career\services\portfolio-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8016"
start "opportunity-service" cmd /c "cd /d E:\workspace\idino_career\services\opportunity-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8008"
start "coaching-service" cmd /c "cd /d E:\workspace\idino_career\services\coaching-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8009"
start "risk-service" cmd /c "cd /d E:\workspace\idino_career\services\risk-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8010"
start "badge-service" cmd /c "cd /d E:\workspace\idino_career\services\badge-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8012"
start "simulation-service" cmd /c "cd /d E:\workspace\idino_career\services\simulation-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8013"
start "advisor-service" cmd /c "cd /d E:\workspace\idino_career\services\advisor-service && python -m uvicorn app.main:app --host 0.0.0.0 --port 8014"
echo Services starting... please wait 5 seconds
timeout /t 5 /nobreak > nul
