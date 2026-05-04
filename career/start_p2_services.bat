@echo off
set PYTHONPATH=E:\workspace\idino_career

cd /d E:\workspace\idino_career\services\badge-service
start "Badge Service 8012" python -m uvicorn app.main:app --host 0.0.0.0 --port 8012

cd /d E:\workspace\idino_career\services\advisor-service
start "Advisor Service 8014" python -m uvicorn app.main:app --host 0.0.0.0 --port 8014

cd /d E:\workspace\idino_career\services\roadmap-service
start "Roadmap Service 8015" python -m uvicorn app.main:app --host 0.0.0.0 --port 8015

cd /d E:\workspace\idino_career\services\portfolio-service
start "Portfolio Service 8016" python -m uvicorn app.main:app --host 0.0.0.0 --port 8016

echo P2 Services started!
