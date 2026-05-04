# Stop all processes listening on port 8011
$processes = Get-NetTCPConnection -LocalPort 8011 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($pid in $processes) {
    Write-Host "Stopping process $pid"
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

# Remove Python cache
Get-ChildItem -Path "E:\workspace\idino_career\services\auth-service" -Recurse -Include "__pycache__","*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Start auth service
Set-Location "E:\workspace\idino_career\services\auth-service"
Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8011" -WindowStyle Hidden

Write-Host "Auth service started on port 8011"
