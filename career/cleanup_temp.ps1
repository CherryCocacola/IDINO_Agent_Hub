# Stop all Python processes related to idino_career
Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -like "*idino_career*" -or (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine -like "*idino_career*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop all Node processes
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop specific ports
$ports = @(3000, 8002, 8003, 8005, 8006, 8007, 8008, 8009, 8010, 8011, 8012, 8013, 8014, 8015, 8016, 8017, 8018, 8020)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        if ($conn.OwningProcess -ne 0) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped process on port $port (PID: $($conn.OwningProcess))"
        }
    }
}

Write-Host "Cleanup completed"
