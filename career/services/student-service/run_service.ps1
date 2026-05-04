$env:PYTHONPATH = "E:\workspace\idino_career"
Set-Location "E:\workspace\idino_career\services\student-service"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
