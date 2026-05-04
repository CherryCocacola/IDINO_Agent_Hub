$env:PYTHONPATH = "E:\workspace\idino_career"
Set-Location -Path "E:\workspace\idino_career\services\alumni-service"
Start-Process python "-m uvicorn app.main:app --host 0.0.0.0 --port 8005" -WindowStyle Hidden
Set-Location -Path "E:\workspace\idino_career\services\ai-service"
Start-Process python "-m uvicorn app.main:app --host 0.0.0.0 --port 8006" -WindowStyle Hidden
