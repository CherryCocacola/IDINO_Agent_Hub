@echo off
set PYTHONPATH=E:\workspace\idino_career

cd /d E:\workspace\idino_career\services\risk-service
start "Risk Service" python -m uvicorn app.main:app --host 0.0.0.0 --port 8004

cd /d E:\workspace\idino_career\services\auth-service
start "Auth Service" python -m uvicorn app.main:app --host 0.0.0.0 --port 8011

cd /d E:\workspace\idino_career\services\simulation-service
start "Simulation Service" python -m uvicorn app.main:app --host 0.0.0.0 --port 8013

echo Services started!
