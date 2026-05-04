# AgentHub — AI Agent 통합관리 시스템

다중 LLM 프로바이더(OpenAI, Claude, Gemini, Perplexity, Mistral 등)를 통합한
AI Agent 관리 플랫폼. RAG, 워크플로우, 툴 실행, PII 보호, 할당량 관리, 프레젠테이션 생성을 지원한다.

## 기술 스택

### Backend
- **ASP.NET Core 8.0** (Web API, In-Process IIS hosting)
- **Entity Framework Core 8.0** + **Microsoft SQL Server**
- **JWT** 인증 + **API Key** 인증 (라운드로빈 풀 + Rate Limiter)
- **SignalR** — 실시간 채팅(`/hubs/chat`), 알림(`/hubs/notification`)
- **Hangfire** — 할당량 리셋, 일/월 리포트 생성
- **Redis** (선택적, 없으면 MemoryCache 자동 폴백)
- **DocumentFormat.OpenXml** + ClosedXML + PdfPig + CsvHelper — 문서 처리
- **LibreOffice** (PPTX → PDF 변환, Windows 경로 고정)

### Frontend (`ClientApp/`)
- **Vue 3** + **TypeScript** + **Vite 5**
- **Pinia** (상태), **Vue Router** (라우팅), **vue-i18n** (다국어)
- **Bootstrap 5.3** + Bootstrap Icons
- **Vue Flow** — 워크플로우 비주얼 에디터
- **Chart.js** / **vue-chartjs** — 분석 대시보드
- **@microsoft/signalr** — 백엔드 허브 클라이언트
- **marked** + **DOMPurify** + **prismjs** — 채팅 마크다운/코드 렌더링

### 프록시 LLM 프로바이더
OpenAI / Claude / Gemini / Google Vertex / Perplexity / Mistral / Copilot / Azure OpenAI / Tavily —
모두 `IAiProxyService`를 통해서만 호출. Named HttpClient 풀로 타임아웃/연결 관리.

## 프로젝트 구조 (반드시 준수)

```
AIAgentManagement/
├── Controllers/        # API 엔드포인트 (한 리소스 = 한 컨트롤러)
├── Services/           # 비즈니스 로직 — I{Name}Service 인터페이스 + {Name}Service 구현
├── Models/             # EF Core 엔티티 (DbContext에 매핑됨)
├── DTOs/               # Request/Response 전송 객체 — 외부 노출용
├── Data/               # DbContext, DatabaseInitializer, Seed 스크립트
├── Migrations/         # EF Core 자동 생성 마이그레이션 (SQL 직접 작성 금지)
├── Middleware/         # 전역 예외, 보안 헤더, ActivityLog, HTTPS 리다이렉트
├── Hubs/               # SignalR Hub (ChatHub, NotificationHub)
├── BackgroundJobs/     # Hangfire 작업 (QuotaResetJob, ReportGenerationJob, ActivityLogWorker)
├── Tools/              # 운영용 일회성 스크립트 (비즈니스 로직 아님)
├── Infrastructure/     # JsonConverters, ActivityLogChannel 등 횡단 관심사
├── Attributes/         # 인증/권한 커스텀 속성
├── Exceptions/         # 도메인 예외
├── Settings/           # 강타입 설정 옵션 클래스
├── Utils/              # 헬퍼 (정적 메서드)
├── ClientApp/src/
│   ├── views/          # 페이지 단위 Vue 컴포넌트
│   ├── components/     # 재사용 컴포넌트
│   ├── stores/         # Pinia 스토어
│   ├── services/       # axios 기반 API 클라이언트
│   ├── composables/    # Composition API 훅
│   ├── router/         # vue-router
│   ├── i18n/           # 다국어 리소스 (ko/en)
│   ├── layouts/        # 레이아웃 컴포넌트
│   └── types/          # TypeScript 타입 선언
└── wwwroot/            # 프로덕션 빌드 산출물 + 정적 파일
```

## 핵심 명령어

```bash
# 백엔드 빌드/실행
dotnet build
dotnet run                                  # https://localhost:5001
dotnet ef migrations add <Name>             # 마이그레이션 생성
dotnet ef database update                   # DB 적용

# 프론트엔드 (ClientApp/)
cd ClientApp && npm install
npm run dev                                 # http://localhost:5173
npm run build:check                         # vue-tsc + vite build (타입 검사 포함)
npm run build                               # 프로덕션 빌드

# 통합 빌드 (프로덕션)
dotnet publish -c Release                   # ClientApp 자동 빌드 → wwwroot 복사

# IIS 배포 점검
powershell -File CheckAppStatus.ps1
powershell -File DbConnectionTest.ps1
```

## 핵심 규칙

- **모든 LLM 호출은 `IAiProxyService`를 경유**한다 — `OpenAI`, `Anthropic.SDK` 등을 직접 import 금지
- **모든 설정은 `IConfiguration` / Options 패턴**으로 주입 — 하드코딩 금지 (URL, API 키, 포트 등)
- **DB 스키마 변경은 EF Core 마이그레이션**으로만 — 루트의 `*.sql` 파일은 레거시 일회성 스크립트(역사적 기록)
- **C# 백엔드: PascalCase**, **JSON API 경계: camelCase** (`Program.cs`의 `JsonNamingPolicy.CamelCase` 적용됨)
- **모든 사용자향 메시지는 한국어** (오류 메시지, 로그, ErrorResponseDto, RateLimit 응답)
- **ErrorResponseDto 형식 통일** — 컨트롤러는 `BadRequest(new ErrorResponseDto(...))` 패턴, 모델 검증도 `Program.cs`에서 자동 변환
- **인증 우선순위**: JWT Bearer (`/api/*`) → API Key (`/v1/*` OpenAI 호환) → 게스트 (Rate Limiter 정책 분리)
- **민감 데이터**: PiiDetectionService를 통과시키고, BannedWordService로 금칙어 검사
- **커밋 메시지**: `[모듈] 한글 설명` (예: `[chat] WebSocket 재연결 안정화`)

## API 게이트웨이 구조

- `/api/auth/*` — 로그인/회원가입/토큰 갱신 (JWT 발급)
- `/api/*` — 비즈니스 API (JWT 필수, `per-user` Rate Limit 60/min)
- `/v1/*` — OpenAI 호환 API (API Key 인증, `ip-openai` Rate Limit 30/min)
- `/api/chat/public/*` — 게스트 공개 채팅 (`ip-guest` Rate Limit 20/min)
- `/hubs/chat`, `/hubs/notification` — SignalR
- `/hangfire` — 작업 대시보드 (관리자 전용)
- `/swagger` — 개발 환경에서만 활성화

## 배포 환경

- **개발**: Windows + LocalDB/SQL Express + npm dev server (vite proxy)
- **프로덕션**: IIS (`agenthub.idino.co.kr`) + SQL Server + Hangfire
- 프로덕션 도메인 진입 시 `RequireHttpsForDomainMiddleware`가 HTTPS 리다이렉트 적용
- IIS InProcess 호스팅이므로 Kestrel 직접 노출하지 않음

## 도메인 규칙 / 안티 패턴 / 협업 가이드

- `.claude/rules/architecture.md` — 계층 구조, 의존성 방향, 데이터 흐름
- `.claude/rules/anti-patterns.md` — 금지 패턴
- `.claude/rules/agent-collaboration.md` — AI 코딩 도구가 따라야 하는 절차
- `.claude/rules/domain-model.md` — 핵심 엔티티/용어 정의
- `.claude/rules/testing.md` — 테스트 전략
