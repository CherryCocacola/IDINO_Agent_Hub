$env:PYTHONPATH = "E:\workspace\idino_career"

Write-Host "Starting IDINO Career Services..." -ForegroundColor Green

# Student Service
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002" -WorkingDirectory "E:\workspace\idino_career\services\student-service" -WindowStyle Normal
Write-Host "  Student Service started (8002)" -ForegroundColor Cyan

# Competency Service
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003" -WorkingDirectory "E:\workspace\idino_career\services\competency-service" -WindowStyle Normal
Write-Host "  Competency Service started (8003)" -ForegroundColor Cyan

# Alumni Service
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005" -WorkingDirectory "E:\workspace\idino_career\services\alumni-service" -WindowStyle Normal
Write-Host "  Alumni Service started (8005)" -ForegroundColor Cyan

# AI Service
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006" -WorkingDirectory "E:\workspace\idino_career\services\ai-service" -WindowStyle Normal
Write-Host "  AI Service started (8006)" -ForegroundColor Cyan

# Integration Service
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007" -WorkingDirectory "E:\workspace\idino_career\services\integration-service" -WindowStyle Normal
Write-Host "  Integration Service started (8007)" -ForegroundColor Cyan

# Frontend
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "E:\workspace\idino_career\frontend" -WindowStyle Normal
Write-Host "  Frontend started (3000)" -ForegroundColor Cyan

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "Logs: E:\workspace\idino_career\logs\" -ForegroundColor Yellow
