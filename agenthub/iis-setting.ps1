# =============================================================
# AIAgentManagement — IIS 프로덕션 환경변수 설정 스크립트
# =============================================================
# 사용법: 관리자 권한 PowerShell에서 실행
#   .\iis-setting.ps1
# =============================================================

# 관리자 권한 확인
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ 관리자 권한으로 실행해주세요." -ForegroundColor Red
    Write-Host "   PowerShell을 '관리자 권한으로 실행' 후 다시 시도하세요." -ForegroundColor Yellow
    exit 1
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AIAgentManagement IIS 환경변수 설정" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------
# 1. DB 연결 문자열
# --------------------------------------------------
[System.Environment]::SetEnvironmentVariable(
    "ConnectionStrings__DefaultConnection",
    "Server=192.168.10.159;Database=AIAgentManagement;User ID=aiuser;Password=rnehrwhgdk20@^;TrustServerCertificate=true;MultipleActiveResultSets=true",
    "Machine"
)
Write-Host "✅ ConnectionStrings__DefaultConnection" -ForegroundColor Green

# --------------------------------------------------
# 2. JWT 시크릿 키
# --------------------------------------------------
[System.Environment]::SetEnvironmentVariable(
    "JwtSettings__SecretKey",
    "YourSuperSecretKeyForJWTTokenGenerationThatShouldBeAtLeast32CharactersLong!",
    "Machine"
)
Write-Host "✅ JwtSettings__SecretKey" -ForegroundColor Green

# --------------------------------------------------
# 3. AI API 키
# --------------------------------------------------
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__OpenAI__ApiKey",
    "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",
    "Machine"
)
Write-Host "✅ AiApiSettings__OpenAI__ApiKey" -ForegroundColor Green

[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Gemini__ApiKey",
    "AIzaSyC_P29YSPl5mLvlPeSHTWhTk36y-6Qf4wo",
    "Machine"
)
Write-Host "✅ AiApiSettings__Gemini__ApiKey" -ForegroundColor Green

[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Perplexity__ApiKey",
    "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",
    "Machine"
)
Write-Host "✅ AiApiSettings__Perplexity__ApiKey" -ForegroundColor Green

[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Tavily__ApiKey",
    "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",
    "Machine"
)
Write-Host "✅ AiApiSettings__Tavily__ApiKey" -ForegroundColor Green

# --------------------------------------------------
# 4. 이메일 설정
# --------------------------------------------------
[System.Environment]::SetEnvironmentVariable(
    "EmailSettings__SmtpUsername",
    "jyj7970@gmail.com",
    "Machine"
)
Write-Host "✅ EmailSettings__SmtpUsername" -ForegroundColor Green

[System.Environment]::SetEnvironmentVariable(
    "EmailSettings__SmtpPassword",
    "asjlnarogfiprmna",
    "Machine"
)
Write-Host "✅ EmailSettings__SmtpPassword" -ForegroundColor Green

# --------------------------------------------------
# 설정 확인 출력
# --------------------------------------------------
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  설정된 환경변수 확인" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$vars = @(
    "ConnectionStrings__DefaultConnection",
    "JwtSettings__SecretKey",
    "AiApiSettings__OpenAI__ApiKey",
    "AiApiSettings__Gemini__ApiKey",
    "AiApiSettings__Perplexity__ApiKey",
    "AiApiSettings__Tavily__ApiKey",
    "EmailSettings__SmtpUsername",
    "EmailSettings__SmtpPassword"
)

foreach ($var in $vars) {
    $val = [System.Environment]::GetEnvironmentVariable($var, "Machine")
    if ($val) {
        # 값의 앞 6자리만 표시 (보안)
        $masked = $val.Substring(0, [Math]::Min(6, $val.Length)) + "****"
        Write-Host "  $var = $masked" -ForegroundColor White
    } else {
        Write-Host "  ❌ $var = (없음)" -ForegroundColor Red
    }
}

# --------------------------------------------------
# IIS 재시작
# --------------------------------------------------
Write-Host ""
Write-Host "IIS를 재시작합니다..." -ForegroundColor Yellow
iisreset

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  완료! 앱이 환경변수를 읽어올 준비가 되었습니다." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
