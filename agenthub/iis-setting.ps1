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

# =============================================================
# ⚠ 보안 경고 — 운영 시크릿은 절대 이 스크립트에 평문으로 두지 않는다.
# =============================================================
# 본 스크립트는 IIS Machine 환경변수에 등록할 "키 이름" 만 정의한다.
# 실제 값은 다음 중 하나의 방식으로 운영자가 직접 주입한다:
#   1) Windows Credential Manager (cmdkey / Get-Credential)
#   2) 별도 .secrets.ps1 (gitignore 대상)을 dot-source: `. .\.secrets.ps1`
#   3) 운영자가 PowerShell 세션에서 `$env:OPENAI_KEY = '...'` 로 주입 후 본 스크립트 실행
# placeholder 그대로 실행하면 앱이 부팅은 되지만 외부 LLM 호출이 실패한다 — 의도된 동작.
# 회전 시: 외부 콘솔에서 키 재발급 → 위 방식 중 하나로 값 주입 → 본 스크립트 재실행 → iisreset.

# --------------------------------------------------
# 1. DB 연결 문자열 — 비밀번호는 외부 주입
# --------------------------------------------------
$dbPassword = if ($env:AGENTHUB_DB_PASSWORD) { $env:AGENTHUB_DB_PASSWORD } else { "<DB_PASSWORD>" }
[System.Environment]::SetEnvironmentVariable(
    "ConnectionStrings__DefaultConnection",
    "Server=192.168.10.159;Database=AIAgentManagement;User ID=aiuser;Password=$dbPassword;TrustServerCertificate=true;MultipleActiveResultSets=true",
    "Machine"
)
Write-Host "✅ ConnectionStrings__DefaultConnection" -ForegroundColor Green

# --------------------------------------------------
# 2. JWT 시크릿 키 — 운영 환경에서는 32바이트 이상 랜덤값을 외부 주입
# --------------------------------------------------
$jwtSecret = if ($env:AGENTHUB_JWT_SECRET) { $env:AGENTHUB_JWT_SECRET } else { "<JWT_SECRET_KEY_AT_LEAST_32_CHARS>" }
[System.Environment]::SetEnvironmentVariable(
    "JwtSettings__SecretKey",
    $jwtSecret,
    "Machine"
)
Write-Host "✅ JwtSettings__SecretKey" -ForegroundColor Green

# --------------------------------------------------
# 3. AI API 키 — 외부 LLM 콘솔에서 발급, 환경변수로 주입
# --------------------------------------------------
$openaiKey = if ($env:OPENAI_API_KEY) { $env:OPENAI_API_KEY } else { "<OPENAI_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__OpenAI__ApiKey",
    $openaiKey,
    "Machine"
)
Write-Host "✅ AiApiSettings__OpenAI__ApiKey" -ForegroundColor Green

$geminiKey = if ($env:GEMINI_API_KEY) { $env:GEMINI_API_KEY } else { "<GEMINI_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Gemini__ApiKey",
    $geminiKey,
    "Machine"
)
Write-Host "✅ AiApiSettings__Gemini__ApiKey" -ForegroundColor Green

$perplexityKey = if ($env:PERPLEXITY_API_KEY) { $env:PERPLEXITY_API_KEY } else { "<PERPLEXITY_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Perplexity__ApiKey",
    $perplexityKey,
    "Machine"
)
Write-Host "✅ AiApiSettings__Perplexity__ApiKey" -ForegroundColor Green

$tavilyKey = if ($env:TAVILY_API_KEY) { $env:TAVILY_API_KEY } else { "<TAVILY_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Tavily__ApiKey",
    $tavilyKey,
    "Machine"
)
Write-Host "✅ AiApiSettings__Tavily__ApiKey" -ForegroundColor Green

# --------------------------------------------------
# 4. 이메일 설정 — SMTP 앱 비밀번호는 외부 주입
# --------------------------------------------------
$smtpUser = if ($env:SMTP_USERNAME) { $env:SMTP_USERNAME } else { "<SMTP_USERNAME>" }
[System.Environment]::SetEnvironmentVariable(
    "EmailSettings__SmtpUsername",
    $smtpUser,
    "Machine"
)
Write-Host "✅ EmailSettings__SmtpUsername" -ForegroundColor Green

$smtpPassword = if ($env:SMTP_PASSWORD) { $env:SMTP_PASSWORD } else { "<SMTP_APP_PASSWORD>" }
[System.Environment]::SetEnvironmentVariable(
    "EmailSettings__SmtpPassword",
    $smtpPassword,
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
