# IIS 애플리케이션 상태 확인 스크립트

Write-Host "=== IIS 애플리케이션 상태 확인 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 애플리케이션 풀 확인
Write-Host "1. 애플리케이션 풀 확인..." -ForegroundColor Yellow
try {
    $appPools = Get-WebAppPoolState -Name "*" -ErrorAction SilentlyContinue
    if ($appPools) {
        foreach ($pool in $appPools) {
            $status = if ($pool.Value -eq 'Started') { "✓ 실행 중" } else { "✗ 중지됨" }
            $color = if ($pool.Value -eq 'Started') { "Green" } else { "Red" }
            Write-Host "   [$status] $($pool.Name)" -ForegroundColor $color
        }
    } else {
        Write-Host "   애플리케이션 풀을 찾을 수 없습니다." -ForegroundColor Red
    }
} catch {
    Write-Host "   애플리케이션 풀 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 2. 웹 사이트 확인
Write-Host "2. 웹 사이트 확인..." -ForegroundColor Yellow
try {
    $sites = Get-Website -ErrorAction SilentlyContinue
    if ($sites) {
        foreach ($site in $sites) {
            $status = if ($site.State -eq 'Started') { "✓ 실행 중" } else { "✗ 중지됨" }
            $color = if ($site.State -eq 'Started') { "Green" } else { "Red" }
            Write-Host "   [$status] $($site.Name) - $($site.Bindings.bindingInformation)" -ForegroundColor $color
        }
    } else {
        Write-Host "   웹 사이트를 찾을 수 없습니다." -ForegroundColor Red
    }
} catch {
    Write-Host "   웹 사이트 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 3. 포트 80 사용 확인
Write-Host "3. 포트 80 사용 확인..." -ForegroundColor Yellow
try {
    $port80 = netstat -ano | findstr ":80"
    if ($port80) {
        Write-Host "   포트 80을 사용하는 프로세스:" -ForegroundColor Green
        Write-Host $port80
    } else {
        Write-Host "   ✗ 포트 80을 사용하는 프로세스가 없습니다." -ForegroundColor Red
    }
} catch {
    Write-Host "   포트 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 4. dotnet 프로세스 확인
Write-Host "4. dotnet 프로세스 확인..." -ForegroundColor Yellow
try {
    $dotnetProcesses = Get-Process -Name "dotnet" -ErrorAction SilentlyContinue
    if ($dotnetProcesses) {
        Write-Host "   ✓ dotnet 프로세스 실행 중:" -ForegroundColor Green
        foreach ($proc in $dotnetProcesses) {
            Write-Host "     PID: $($proc.Id) - $($proc.Path)"
        }
    } else {
        Write-Host "   ✗ dotnet 프로세스가 실행되지 않았습니다." -ForegroundColor Red
    }
} catch {
    Write-Host "   dotnet 프로세스 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 5. w3wp 프로세스 확인 (IIS 워커 프로세스)
Write-Host "5. w3wp 프로세스 확인 (IIS 워커 프로세스)..." -ForegroundColor Yellow
try {
    $w3wpProcesses = Get-Process -Name "w3wp" -ErrorAction SilentlyContinue
    if ($w3wpProcesses) {
        Write-Host "   ✓ w3wp 프로세스 실행 중:" -ForegroundColor Green
        foreach ($proc in $w3wpProcesses) {
            Write-Host "     PID: $($proc.Id)"
        }
    } else {
        Write-Host "   ✗ w3wp 프로세스가 실행되지 않았습니다." -ForegroundColor Red
    }
} catch {
    Write-Host "   w3wp 프로세스 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 6. 로그 파일 확인
Write-Host "6. 로그 파일 확인..." -ForegroundColor Yellow
$logPath = "C:\publish\AIAgentManagement\logs"
if (Test-Path $logPath) {
    $logFiles = Get-ChildItem -Path $logPath -Filter "stdout_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($logFiles) {
        Write-Host "   최근 로그 파일: $($logFiles.FullName)" -ForegroundColor Green
        Write-Host "   마지막 수정 시간: $($logFiles.LastWriteTime)" -ForegroundColor Green
        Write-Host ""
        Write-Host "   최근 20줄:" -ForegroundColor Yellow
        Get-Content $logFiles.FullName -Tail 20
    } else {
        Write-Host "   ✗ 로그 파일을 찾을 수 없습니다." -ForegroundColor Red
    }
} else {
    Write-Host "   ✗ 로그 디렉토리가 없습니다: $logPath" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== 확인 완료 ===" -ForegroundColor Cyan
