# AIAgentManagement — 남은 작업 목록

> 최초 작성: 2026-03-17 / 마지막 업데이트: 2026-03-17
> 현재 완성도: **100%** 🎉

---

## ✅ 완료된 작업 (2026-03-17)

| # | 작업 | 분류 |
|---|------|------|
| ✅ | DB 인덱스 6개 SQL 실행 | 운영 필수 |
| ✅ | AllowedEmbedDomains DB 컬럼 추가 | 운영 필수 |
| ✅ | PasswordResetToken / Expiry 컬럼 추가 (SQL 실행 필요) | 운영 필수 |
| ✅ | 성능 개선 — ActivityLog 비동기 배치 처리 | 성능 |
| ✅ | 성능 개선 — Named HttpClient (AiProxyService) | 성능 |
| ✅ | 성능 개선 — ChatService AsNoTracking | 성능 |
| ✅ | 성능 개선 — DbContext 인덱스 6개 코드 반영 | 성능 |
| ✅ | 성능 개선 — AI API 타임아웃 300→120초 | 성능 |
| ✅ | AgentBuilder 수정 모드 (route param + PUT 분기) | 핵심 UX |
| ✅ | AgentSelect 수정 모달에 "빌더에서 수정" 버튼 추가 | 핵심 UX |
| ✅ | Workflow 시각적 편집기 (@vue-flow/core 도입) | 대형 기능 |
| ✅ | Workflow 테스트 실행 버튼 연동 (모달 결과 표시) | 기능 완성 |
| ✅ | AgentDto에 allowedEmbedDomains 타입 필드 추가 | 타입 동기화 |
| ✅ | 이용약관 / 개인정보처리방침 페이지 (Vue + 라우터) | 법적 필요 |
| ✅ | Hangfire 관리자 인증 강화 (Admin role 체크) | 보안 |
| ✅ | 비밀번호 재설정 API + ForgotPassword.vue + ResetPassword.vue | 사용자 필수 |
| ✅ | AgentTemplates → AgentBuilder 연동 ("Agent로 만들기" 버튼) | 편의성 |
| ✅ | Landing 페이지 Vue 이식 (LandingPage.vue + `/landing` 라우트) | 마케팅 |
| ✅ | KnowledgeBase AI Q&A 모드 활성화 (RAG 채팅 UI) | 기능 완성 |
| ✅ | 멀티채팅 파일 첨부 구현 (이미지/파일 업로드 + 미리보기) | 편의성 |
| ✅ | VideoGeneration 코드 삭제 (Controller/DTO/Vue 제거) | 코드 정리 |
| ✅ | Help 라이브 채팅 버튼 제거 | 코드 정리 |
| ✅ | appsettings.json 민감 정보 보호 (개발: Development.json 분리) | 보안 |

---

## 🔵 남은 작업

### 1. 비디오 생성 AI 연동 (향후 예정)
- Sora(OpenAI), Veo(Google), Gen4Video 실제 모델 연동
- 폴링 방식 비동기 응답 처리
- ⚠️ Controller/DTO/Vue 파일 삭제됨 — 재구현 시 신규 작성 필요

---

## 📋 남은 작업 우선순위

| 순위 | 작업 | 공수 | 중요도 |
|------|------|------|--------|
| 1 | **프로덕션 환경변수 설정 (IIS)** | 30분 | 🔴 배포 필수 |
| 2 | 비디오 생성 AI 연동 | 향후 예정 | 🔵 신규 기능 |

---

## 🧪 배포 전 체크리스트

- [x] DB 인덱스 SQL 실행 완료
- [x] AllowedEmbedDomains 컬럼 추가 완료
- [x] 앱 재시작 시 ActivityLogWorker 백그라운드 서비스 동작 확인
- [x] 이용약관/개인정보 페이지 추가 완료
- [x] Hangfire 관리자 인증 구현 완료
- [x] **PasswordResetToken/Expiry 컬럼 DB 실행** (`ALTER TABLE Users ADD ...`)
- [x] **appsettings.json 민감 정보 분리** (Development.json에 격리 완료)
- [x] **프로덕션 IIS 환경변수 설정** (iis-setting.ps1 실행)
- [x] SmtpUsername 설정 (`"SmtpUsername": "jyj7970@gmail.com"`) — iis-setting.ps1에 포함
- [x] HTTPS 설정 확인 (RequireHttpsForDomainMiddleware)
- [x] CORS 운영 도메인 제한 확인
- [x] Rate Limiting 운영 값 조정
- [x] 로그 레벨 Production = Warning 확인

---

## 🔐 프로덕션 IIS 환경변수 설정 가이드

> `appsettings.Development.json`은 개발 전용. 프로덕션 서버(IIS)에는 아래 환경변수를 직접 등록해야 함.
> IIS Manager → 사이트 선택 → Configuration Editor → `system.webServer/aspNetCore` → `environmentVariables`

| 환경변수 이름 | 값 예시 | 설명 |
|---|---|---|
| `ConnectionStrings__DefaultConnection` | `Server=...;Database=AIAgentManagement;...` | DB 연결 문자열 |
| `JwtSettings__SecretKey` | 32자 이상 랜덤 문자열 | JWT 서명 키 |
| `AiApiSettings__OpenAI__ApiKey` | `sk-proj-...` | OpenAI API 키 |
| `AiApiSettings__Claude__ApiKey` | `sk-ant-...` | Claude API 키 |
| `AiApiSettings__Gemini__ApiKey` | `AIza...` | Gemini API 키 |
| `AiApiSettings__Perplexity__ApiKey` | `pplx-...` | Perplexity API 키 |
| `AiApiSettings__Mistral__ApiKey` | `...` | Mistral API 키 (사용 시) |
| `AiApiSettings__Tavily__ApiKey` | `tvly-...` | Tavily 검색 API 키 |
| `EmailSettings__SmtpUsername` | `jyj7970@gmail.com` | Gmail 계정 |
| `EmailSettings__SmtpPassword` | `앱 비밀번호 16자리` | Gmail 앱 비밀번호 |

> **참고**: ASP.NET Core는 `__` (언더바 2개)를 JSON 계층 구분자로 인식함.
> **관리자 권한 PowerShell**에서 아래 명령어를 실행하세요.

```powershell
# ⚠️ 관리자 권한 PowerShell에서 실행 필요
# 실행 후 iisreset 으로 IIS 재시작 필요
#
# 🔐 보안: 아래 placeholder 값들은 절대 git 에 평문으로 커밋하지 않는다.
# 운영자는 본 스크립트 실행 전에 PowerShell 세션에서 다음 환경변수를 먼저 주입한다:
#   $env:AGENTHUB_DB_PASSWORD = '...'
#   $env:AGENTHUB_JWT_SECRET  = '...'
#   $env:OPENAI_API_KEY       = '...'
#   $env:GEMINI_API_KEY       = '...'
#   $env:PERPLEXITY_API_KEY   = '...'
#   $env:TAVILY_API_KEY       = '...'
#   $env:SMTP_USERNAME        = '...'
#   $env:SMTP_PASSWORD        = '...'
# 또는 .gitignore 처리된 .secrets.ps1 을 dot-source: `. .\.secrets.ps1`
# placeholder 그대로 실행하면 앱은 부팅되지만 외부 LLM/SMTP 호출이 실패한다 (의도된 동작).

# DB 연결
$dbPassword = if ($env:AGENTHUB_DB_PASSWORD) { $env:AGENTHUB_DB_PASSWORD } else { "<DB_PASSWORD>" }
[System.Environment]::SetEnvironmentVariable(
    "ConnectionStrings__DefaultConnection",
    "Server=192.168.10.159;Database=AIAgentManagement;User ID=aiuser;Password=$dbPassword;TrustServerCertificate=true;MultipleActiveResultSets=true",
    "Machine"
)

# JWT
$jwtSecret = if ($env:AGENTHUB_JWT_SECRET) { $env:AGENTHUB_JWT_SECRET } else { "<JWT_SECRET_KEY_AT_LEAST_32_CHARS>" }
[System.Environment]::SetEnvironmentVariable(
    "JwtSettings__SecretKey",
    $jwtSecret,
    "Machine"
)

# OpenAI
$openaiKey = if ($env:OPENAI_API_KEY) { $env:OPENAI_API_KEY } else { "<OPENAI_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__OpenAI__ApiKey",
    $openaiKey,
    "Machine"
)

# Gemini
$geminiKey = if ($env:GEMINI_API_KEY) { $env:GEMINI_API_KEY } else { "<GEMINI_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Gemini__ApiKey",
    $geminiKey,
    "Machine"
)

# Perplexity
$perplexityKey = if ($env:PERPLEXITY_API_KEY) { $env:PERPLEXITY_API_KEY } else { "<PERPLEXITY_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Perplexity__ApiKey",
    $perplexityKey,
    "Machine"
)

# Tavily
$tavilyKey = if ($env:TAVILY_API_KEY) { $env:TAVILY_API_KEY } else { "<TAVILY_API_KEY>" }
[System.Environment]::SetEnvironmentVariable(
    "AiApiSettings__Tavily__ApiKey",
    $tavilyKey,
    "Machine"
)

# Email
$smtpUser = if ($env:SMTP_USERNAME) { $env:SMTP_USERNAME } else { "<SMTP_USERNAME>" }
[System.Environment]::SetEnvironmentVariable(
    "EmailSettings__SmtpUsername",
    $smtpUser,
    "Machine"
)
$smtpPassword = if ($env:SMTP_PASSWORD) { $env:SMTP_PASSWORD } else { "<SMTP_APP_PASSWORD>" }
[System.Environment]::SetEnvironmentVariable(
    "EmailSettings__SmtpPassword",
    $smtpPassword,
    "Machine"
)

Write-Host "환경변수 설정 완료. IIS를 재시작하세요." -ForegroundColor Green

# IIS 재시작
iisreset
```

---

*이 파일은 개발 진행에 따라 업데이트하세요.*
