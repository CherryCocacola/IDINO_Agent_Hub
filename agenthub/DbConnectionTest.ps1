# 데이터베이스 연결 테스트 PowerShell 스크립트
$connectionString = "Server=192.168.10.159;Database=AIAgentManagement;User ID=aiuser;Password=rnehrwhgdk20@^;TrustServerCertificate=true;MultipleActiveResultSets=true"

Write-Host "=== 데이터베이스 연결 테스트 ===" -ForegroundColor Cyan
Write-Host ""

# 연결 문자열 출력 (비밀번호 마스킹)
$maskedConnectionString = $connectionString -replace "Password=[^;]+", "Password=***"
Write-Host "연결 문자열: $maskedConnectionString"
Write-Host ""

try {
    # .NET 어셈블리 로드
    Add-Type -AssemblyName System.Data
    
    Write-Host "1. SqlConnection 객체 생성 중..." -ForegroundColor Yellow
    $connection = New-Object System.Data.SqlClient.SqlConnection($connectionString)
    
    Write-Host "2. 데이터베이스 연결 시도 중..." -ForegroundColor Yellow
    $connection.Open()
    Write-Host "   ✓ 연결 성공!" -ForegroundColor Green
    Write-Host ""
    
    # 서버 정보 조회
    Write-Host "3. 서버 정보 조회 중..." -ForegroundColor Yellow
    $command = $connection.CreateCommand()
    $command.CommandText = "SELECT @@VERSION AS Version, DB_NAME() AS CurrentDB, USER_NAME() AS CurrentUser"
    $reader = $command.ExecuteReader()
    
    if ($reader.Read()) {
        Write-Host "   ✓ SQL Server 버전:" -ForegroundColor Green
        Write-Host "     $($reader['Version'])"
        Write-Host "   ✓ 현재 데이터베이스: $($reader['CurrentDB'])" -ForegroundColor Green
        Write-Host "   ✓ 현재 사용자: $($reader['CurrentUser'])" -ForegroundColor Green
    }
    $reader.Close()
    Write-Host ""
    
    # 테이블 개수 조회
    Write-Host "4. 테이블 정보 조회 중..." -ForegroundColor Yellow
    $command.CommandText = "SELECT COUNT(*) AS TableCount FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
    $tableCount = $command.ExecuteScalar()
    Write-Host "   ✓ 테이블 개수: $tableCount" -ForegroundColor Green
    Write-Host ""
    
    # Hangfire 테이블 확인
    Write-Host "5. Hangfire 테이블 확인 중..." -ForegroundColor Yellow
    $command.CommandText = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME LIKE 'HangFire%'"
    $hangfireTableCount = $command.ExecuteScalar()
    Write-Host "   ✓ Hangfire 테이블 개수: $hangfireTableCount" -ForegroundColor Green
    Write-Host ""
    
    $connection.Close()
    
    Write-Host "=== 모든 테스트 통과 ===" -ForegroundColor Green
    Write-Host ""
    exit 0
}
catch [System.Data.SqlClient.SqlException] {
    Write-Host ""
    Write-Host "=== SQL Server 오류 발생 ===" -ForegroundColor Red
    Write-Host "오류 번호: $($_.Exception.Number)" -ForegroundColor Red
    Write-Host "오류 메시지: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "서버: $($_.Exception.Server)" -ForegroundColor Red
    Write-Host "데이터베이스: $($_.Exception.Database)" -ForegroundColor Red
    Write-Host "상태: $($_.Exception.State)" -ForegroundColor Red
    Write-Host "심각도: $($_.Exception.Class)" -ForegroundColor Red
    Write-Host ""
    exit 1
}
catch {
    Write-Host ""
    Write-Host "=== 오류 발생 ===" -ForegroundColor Red
    Write-Host "오류 타입: $($_.Exception.GetType().Name)" -ForegroundColor Red
    Write-Host "오류 메시지: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "스택 트레이스:" -ForegroundColor Yellow
    Write-Host $_.Exception.StackTrace
    Write-Host ""
    exit 1
}
finally {
    if ($connection -and $connection.State -eq 'Open') {
        $connection.Close()
    }
}
