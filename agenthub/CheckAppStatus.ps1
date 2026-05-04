# 애플리케이션 상태 확인 및 진단 스크립트

Write-Host "=== AI Agent Management 애플리케이션 상태 확인 ===" -ForegroundColor Cyan
Write-Host ""

$deployPath = "C:\publish\AIAgentManagement"
$logPath = "$deployPath\logs"

# 1. 배포 폴더 확인
Write-Host "1. 배포 폴더 확인..." -ForegroundColor Yellow
if (Test-Path $deployPath) {
    Write-Host "   ✓ 배포 폴더 존재: $deployPath" -ForegroundColor Green
    
    # DLL 파일 확인
    $dllPath = "$deployPath\AIAgentManagement.dll"
    if (Test-Path $dllPath) {
        Write-Host "   ✓ DLL 파일 존재" -ForegroundColor Green
    } else {
        Write-Host "   ✗ DLL 파일 없음: $dllPath" -ForegroundColor Red
    }
    
    # web.config 확인
    $webConfigPath = "$deployPath\web.config"
    if (Test-Path $webConfigPath) {
        Write-Host "   ✓ web.config 존재" -ForegroundColor Green
    } else {
        Write-Host "   ✗ web.config 없음" -ForegroundColor Red
    }
} else {
    Write-Host "   ✗ 배포 폴더 없음: $deployPath" -ForegroundColor Red
}
Write-Host ""

# 2. 로그 파일 확인
Write-Host "2. 로그 파일 확인..." -ForegroundColor Yellow
if (Test-Path $logPath) {
    $logFiles = Get-ChildItem -Path $logPath -Filter "stdout_*.log" | Sort-Object LastWriteTime -Descending
    if ($logFiles) {
        $latestLog = $logFiles[0]
        Write-Host "   ✓ 최근 로그 파일: $($latestLog.Name)" -ForegroundColor Green
        Write-Host "   마지막 수정: $($latestLog.LastWriteTime)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   === 최근 로그 (마지막 30줄) ===" -ForegroundColor Yellow
        try {
            Get-Content $latestLog.FullName -Tail 30 -ErrorAction Stop
        } catch {
            Write-Host "   로그 파일 읽기 실패: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ✗ 로그 파일 없음" -ForegroundColor Red
        Write-Host "   로그 디렉토리: $logPath" -ForegroundColor Gray
    }
} else {
    Write-Host "   ✗ 로그 디렉토리 없음: $logPath" -ForegroundColor Red
    Write-Host "   로그 디렉토리를 생성하시겠습니까? (Y/N): " -NoNewline
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        try {
            New-Item -ItemType Directory -Path $logPath -Force | Out-Null
            Write-Host "   ✓ 로그 디렉토리 생성됨" -ForegroundColor Green
        } catch {
            Write-Host "   ✗ 로그 디렉토리 생성 실패: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
Write-Host ""

# 3. IIS 애플리케이션 풀 확인
Write-Host "3. IIS 애플리케이션 풀 확인..." -ForegroundColor Yellow
try {
    Import-Module WebAdministration -ErrorAction Stop
    $appPools = Get-WebAppPoolState -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*AIAgent*" -or $_.Name -like "*DefaultAppPool*" }
    if ($appPools) {
        foreach ($pool in $appPools) {
            $status = if ($pool.Value -eq 'Started') { "✓ 실행 중" } else { "✗ 중지됨" }
            $color = if ($pool.Value -eq 'Started') { "Green" } else { "Red" }
            Write-Host "   [$status] $($pool.Name)" -ForegroundColor $color
            
            # 중지된 경우 재시작 제안
            if ($pool.Value -ne 'Started') {
                Write-Host "     재시작하시겠습니까? (Y/N): " -NoNewline
                $response = Read-Host
                if ($response -eq 'Y' -or $response -eq 'y') {
                    try {
                        Start-WebAppPool -Name $pool.Name
                        Write-Host "     ✓ 애플리케이션 풀 재시작됨" -ForegroundColor Green
                    } catch {
                        Write-Host "     ✗ 재시작 실패: $($_.Exception.Message)" -ForegroundColor Red
                    }
                }
            }
        }
    } else {
        Write-Host "   ⚠ 관련 애플리케이션 풀을 찾을 수 없습니다." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ IIS 모듈 로드 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   관리자 권한으로 실행해주세요." -ForegroundColor Yellow
}
Write-Host ""

# 4. 웹 사이트 확인
Write-Host "4. IIS 웹 사이트 확인..." -ForegroundColor Yellow
try {
    $sites = Get-Website -ErrorAction SilentlyContinue | Where-Object { $_.physicalPath -like "*AIAgent*" -or $_.Name -like "*AIAgent*" }
    if ($sites) {
        foreach ($site in $sites) {
            $status = if ($site.State -eq 'Started') { "✓ 실행 중" } else { "✗ 중지됨" }
            $color = if ($site.State -eq 'Started') { "Green" } else { "Red" }
            Write-Host "   [$status] $($site.Name)" -ForegroundColor $color
            Write-Host "     바인딩: $($site.Bindings.bindingInformation)" -ForegroundColor Gray
            Write-Host "     경로: $($site.physicalPath)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠ 관련 웹 사이트를 찾을 수 없습니다." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ 웹 사이트 확인 실패: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 5. 프로세스 확인
Write-Host "5. 프로세스 확인..." -ForegroundColor Yellow
$w3wpProcesses = Get-Process -Name "w3wp" -ErrorAction SilentlyContinue
$dotnetProcesses = Get-Process -Name "dotnet" -ErrorAction SilentlyContinue

if ($w3wpProcesses) {
    Write-Host "   ✓ w3wp 프로세스 실행 중 ($($w3wpProcesses.Count)개)" -ForegroundColor Green
} else {
    Write-Host "   ✗ w3wp 프로세스 없음" -ForegroundColor Red
}

if ($dotnetProcesses) {
    Write-Host "   ✓ dotnet 프로세스 실행 중 ($($dotnetProcesses.Count)개)" -ForegroundColor Green
} else {
    Write-Host "   ⚠ dotnet 프로세스 없음 (정상일 수 있음 - InProcess 모드)" -ForegroundColor Yellow
}
Write-Host ""

# 6. 포트 확인
Write-Host "6. 포트 80 사용 확인..." -ForegroundColor Yellow
try {
    $port80 = netstat -ano | findstr ":80" | findstr "LISTENING"
    if ($port80) {
        Write-Host "   ✓ 포트 80 사용 중:" -ForegroundColor Green
        Write-Host $port80
    } else {
        Write-Host "   ✗ 포트 80이 LISTENING 상태가 아닙니다." -ForegroundColor Red
    }
} catch {
    Write-Host "   포트 확인 실패" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== 진단 완료 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "추가 확인 사항:" -ForegroundColor Yellow
Write-Host "1. IIS Manager에서 애플리케이션 풀 상태 확인"
Write-Host "2. 로그 파일에서 오류 메시지 확인: $logPath"
Write-Host "3. 배포된 appsettings.Production.json 파일 확인"
Write-Host "4. .NET 8.0 런타임이 설치되어 있는지 확인"
Write-Host ""
