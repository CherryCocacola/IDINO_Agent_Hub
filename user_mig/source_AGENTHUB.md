# AgentHub (AIAgentManagement) — monorepo 통합 분석

> 원본 위치: `D:\workspace\AIAgentManagement`
> 기준 자료: TECHSPEC.md (1,171라인, v1.0 / 2026-04-30), CLAUDE.md, `.claude/rules/*.md`
> 작성일: 2026-05-04
> 통합 목적: IDINO_Agent_Hub monorepo 내 **Control Plane (운영자 콘솔 + LLM 게이트웨이)** 역할 정의

---

## 1. 시스템 한 줄 요약

**AgentHub**는 다중 LLM 프로바이더(8종 채팅 + 5종 이미지)를 단일 플랫폼에서 통합 운영하고, 비기술 사용자가 코딩 없이 AI 에이전트를 만들어 배포·공유할 수 있는 **No-code AI Agent 관리 플랫폼**이다. LiteLLM(API 게이트웨이)을 한 단계 확장하여 **운영자 UI + RAG/PII/Quota/Workflow/PPTX**까지 묶은 ASP.NET Core 8.0 + Vue 3 SPA.

### 기술 스택 (요약)
- **Backend**: .NET 8.0 / ASP.NET Core 8.0 (IIS InProcess) / EF Core 8 / **MS SQL Server** / SignalR / Hangfire 1.8 / StackExchange.Redis 2.7 (선택)
- **Frontend**: Vue 3.4 / TypeScript 5.3 / Vite 5 / Pinia / vue-router / vue-i18n / Bootstrap 5.3 / Vue Flow / Chart.js
- **AI/문서**: OpenAI · Claude · Gemini · Vertex · Perplexity · Mistral · Copilot · Azure OpenAI · Tavily · DALL-E · Imagen · Flux2 / DocumentFormat.OpenXml · ClosedXML · PdfPig · CsvHelper / **LibreOffice** (HWP·PPTX↔PDF) / Roslyn(C# 도구) / BCrypt
- **배포**: Windows Server + IIS, 도메인 `agenthub.idino.co.kr`, MSDeploy

---

## 2. 현재 완성도 평가

### 동작하는 핵심 기능
- **JWT 로그인 / 회원관리 / RBAC** (Admin·Developer·User 역할 시드)
- **Agent CRUD + 5단계 위저드** (`AgentBuilder`) — 단, **편집 모드 미구현**
- **단일 채팅 (`AgentChat`)**: 8종 LLM 호출, 30 메시지 history, 응답 캐시(SHA256+Redis 5분)
- **멀티 채팅 (`AgentMultiChat`, 최대 4개 동시 비교)**
- **OpenAI 호환 API** `/v1/chat/completions`, `/v1/models` (API Key 인증, 외부 시스템 연동용)
- **API Key 풀 (라운드로빈 + 60초 쿨다운)**: 7종 프로바이더에 다중 키 분산
- **RAG**: PDF/Word/Excel/CSV/HWP 업로드 → 청크(1000자/200 오버랩) → `text-embedding-3-small` → SIMD 메모리 코사인 검색
- **PII 차단/마스킹**: 한국 PII 8종 정규식 (주민번호/핸드폰/카드 등)
- **BannedWord**: 5분 캐시, 전역/Agent별
- **Quota**: 사용자×ApiService별 일/월 한도 + Hangfire 리셋
- **공개/임베드**: `/chatbot/{code}`, `/embed/{code}`, QR 생성, AllowedEmbedDomains 화이트리스트
- **PPTX/PDF 생성**: 9종 레이아웃 OpenXML 직접 작성, LibreOffice 변환
- **이미지 생성**: DALL-E·Imagen4·Flux2·Gen4
- **Activity Log**: Channel 비동기 배치 INSERT (50개/3초)
- **Hangfire 4 작업**: daily/monthly quota reset, daily/monthly report

### 미완성/약점 (TECHSPEC §16 요약)
| 분류 | 핵심 항목 |
|---|---|
| 🔴 보안 | AES-CBC 고정 IV(C1), JWT키↔AES키 재사용(C2), API Key O(N) 풀스캔(C3), CSharpToolExecutor 코드 인젝션·메모리 누수(C5), DB 평문 비번 하드코딩(C6), SignalR Hub `[Authorize]` 부재 + 임의 userId 입력(C8), `appsettings.*.json` 시크릿 평문 커밋(C10) |
| 🔴 데이터 무결성 | EF **InitialCreate 마이그레이션 부재** + `EnsureCreated` 사용(C7), `Users.Email` UNIQUE 인덱스 누락(C4), 환경별 schema drift 위험 |
| 🔴 호환성 | OpenAI `/v1/chat/completions`의 **stream 가짜 SSE** (전체 응답 후 단어 단위 분할 + 15ms 딜레이)(C9) |
| 🟠 안정성 | RagService 전체 청크 메모리 로드(H1), Workflow 비동기 실행이 scoped DbContext 캡처(H2), Workflow Condition/DataTransform/Loop **NO-OP 스텁**(H3), `ChatService._convLocks` 무한 증가(H4), Stream API가 키 풀/쿨다운 우회(H5), `per-user` Rate Limit 정책 미부착 데드코드(H8), `AiProxyService` 3,749 LOC god class(H13), Fallback 1단계만 지원(H14), QuotaService.RecordUsage 토큰수 무시(H10) |
| 🟡 코드품질 | PII 정규식 과적용, BannedWord 부분일치, SSRF 미차단(TextExtraction/ApiToolExecutor), path traversal 미차단, AgentChat.vue 5,286줄, raw axios 사용처 4건, SignalR 클라이언트 dead, SSE 스트림 클라이언트 dead |
| 미구현 | Agent **편집 모드**, 비디오 생성, Webhook 이벤트, Python/Node SDK, API Key 회전, Redis 분산 Rate Limit, CIDR IP 검증, Landing/약관 Vue 컴포넌트 |

전체적으로 **운영 가능한 단계까지 도달했지만 마이그레이션·시크릿·암호화·SSE 4영역의 부채가 누적**되어 monorepo 통합 시 우선 해결 대상이다.

---

## 3. 도메인 모델 핵심 (통합 관점)

총 **35 엔티티**. monorepo 통합에서 의미가 있는 것은 다음과 같다.

### 3.1 핵심 마스터
- **`User`**: 인증 주체. Email·BCrypt PasswordHash·Status(Active/Pending/Inactive)·2FA 인프라(미활성). UserSession(RefreshToken), UserPreference, TeamMember.
- **`Role` / `UserRole`**: RBAC. 시드 = Admin/Developer/User. (운영 설명서는 SuperAdmin/Admin/User로 다름 — 통합 시 정리 필요)
- **`Team` / `TeamMember`**: 팀 단위 자원 공유.

### 3.2 LLM 카탈로그 (게이트웨이의 골격)
- **`ApiService`**: LLM 프로바이더 추상화. `ServiceCode`(UNIQUE) = "openai|claude|gemini|perplexity|mistral|copilot|azureopenai|tavily" 등. `ServiceType`이 **AiProxyService 분기 키**.
- **`ApiServiceModel`**: 프로바이더가 제공하는 모델 카탈로그 (gpt-5/o3/o1/4o, claude-opus-4-6, gemini-3.1-pro 등 50+).
- **`Agent`**: 사용자 인격체. `AgentCode`(UNIQUE, 외부 노출 식별자) · `SystemPrompt`(MAX) · `Temperature` · `DefaultModel` · `EnableRag` · `PiiProtectionEnabled/Mode` · `IsPublic` · `AllowGuestChat` · `AllowedEmbedDomains` · `WelcomeMessage` · `ChatTheme`. **ServiceId FK Cascade 위험** (서비스 삭제 시 모든 Agent 연쇄 삭제).
- **`AgentDocument`**: Agent ↔ KnowledgeBaseDocument N:M.

### 3.3 채팅·사용량 (시계열 트랜잭션)
- **`ChatConversation`**: User × Agent 대화. **비정규화 캐시**(`MessageCount`, `TotalTokens`, `TotalCost`, `LastMessageAt`) — DB 트리거 부재로 drift 가능.
- **`ChatMessage`**: bigint identity. `Role` ∈ {user, assistant, system, tool}.
- **`ApiUsage`**: 모든 LLM 호출 원자 기록 (Tokens · Cost · Latency · Prompt). 분석/리포트 소스. bigint identity.

### 3.4 인증·인가·통제
- **`ApiKey`** (외부 시스템 → AgentHub 인증):
  - `EncryptedKey nvarchar(500)` — AES-CBC + 고정 IV(zero) + JWT SecretKey 재사용 🔴
  - `AgentId int? FK` — 키 ↔ Agent 바인딩 (라운드로빈은 다른 ApiKeyPool 개념과 별개)
  - `Scopes` (`chat,stream,info,usage`), `AllowedIps`, `RateLimitPerMinute/Day`
  - `ServiceCode`가 **FK가 아닌 단순 문자열** → 임의 값 허용
  - `KeyHash` 컬럼 부재 → 매 인증 풀스캔 + AES 복호화 비교
- **`ApiQuota`**: User × ApiService. `DailyLimit/MonthlyLimit/CurrentUsage/CurrentCost` + `LastResetAt`. Hangfire `QuotaResetJob`이 일/월 리셋.
- **`ActivityLog`**: 모든 API 호출 메타. Channel 배치 INSERT.
- **`PiiDetectionLog`**: 검출 시점/유형/원본/마스킹값. 감사 + 알림.
- **`BannedWord`**: 카테고리별, 전역(Agent NULL) + Agent별.

### 3.5 RAG (DocUtil 위임 시 deprecate 후보)
- **`KnowledgeBaseDocument`**: 업로드 원본 메타.
- **`DocumentChunk`**: bigint identity. `Embedding nvarchar(MAX)` JSON `float[1536]`. **벡터 인덱스 부재**.

### 3.6 워크플로우
- **`Workflow`** (`WorkflowCode` UNIQUE), **`WorkflowNode`** (Connections JSON `{sources, targets}`, NodeType ∈ start/agent/llm/tool/condition/loop/datatransform/output), **`WorkflowExecution`**, **`WorkflowNodeExecution`**.

### 3.7 도구
- **`Tool`** (`ToolCode` UNIQUE, type=csharp/python/javascript/api), **`ToolVersion`**, **`ToolExecution`**.

### 3.8 프레젠테이션
- **`Presentation`** (레거시 `Slides nvarchar(MAX)` + 정규화 `PresentationSlides` 이중 저장), **`PresentationSlide`** (PK는 GUID 문자열), **`PresentationTemplate`**.

### 3.9 콘텐츠/시스템
- `ExamplePrompt` / `Faq` / `Tutorial` (Anonymous GET + Admin CUD), `SystemSetting` (KV).

### 3.10 식별자 정책
- 32개 int identity, 6개 bigint identity (시계열). 외부 노출은 `*Code` 문자열 UNIQUE. PresentationSlide만 GUID. 순차 ID 노출 → IDOR 가능, 컨트롤러 인가 검증 필수.

---

## 4. API 표면적

### 4.1 게이트웨이 라우팅
| 경로 | 인증 | Rate Limit | 비고 |
|---|---|---|---|
| `/api/auth/*` | Anonymous (login/register/forgot/reset), Authorize (logout) | (없음) | JWT 발급, RefreshToken 7일 |
| `/api/*` | JWT Bearer | `per-user` (60/min, **정의만 미부착**) | 비즈니스 API, 28개 컨트롤러 |
| `/v1/*` | API Key (`X-API-Key` 또는 `Bearer ak-…`) | `ip-openai` (30/min) | OpenAI 호환, snake_case |
| `/api/agents/{id}/chat`, `/chat/stream`, `/info`, `/usage` | API Key + Scope | (per-user 미부착) | 외부 Agent API, Postman 컬렉션 |
| `/api/agents/public/{code}/*` | Anonymous + 도메인 화이트리스트 | `ip-guest` (20/min) | 게스트 채팅, QR PNG |
| `/hubs/chat`, `/hubs/notification` | **`[Authorize]` 부재** ⚠️ | — | SignalR (도청 위험) |
| `/hangfire` | HangfireAuthorizationFilter (Admin/SuperAdmin) | — | 잡 대시보드 |
| `/swagger` | — | — | Dev only |

### 4.2 OpenAI 호환 API (외부 통합 핵심)
- `GET /v1/models` → AgentHub Agent 목록을 OpenAI 모델 형식으로
- `GET /v1/models/{model}` → AgentCode 메타
- `POST /v1/chat/completions` → JSON 또는 SSE
  - **`stream:true`가 가짜 SSE** — `ChatService.SendDirectMessageAsync`로 전체 응답 받은 뒤 `Content.Split(' ')` + `Task.Delay(15)`로 chunk 위장 (위치: `Controllers/OpenAICompatController.cs:138`)
  - usage 추정: `(total, completion=0.65*total, prompt=0.35*total)`

### 4.3 표준 응답
- 성공: 200 + DTO. 실패: 400/401/403/404/429/500 + `ErrorResponseDto { message, errorCode, details }`. 메시지는 모두 한국어.
- 오류 코드: `VALIDATION_ERROR`, `BANNED_WORD_DETECTED`, `PII_DETECTED`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `INTERNAL_SERVER_ERROR`.

### 4.4 인증 우선순위
JWT Bearer(`/api/*`) → API Key(`/v1/*`) → Anonymous + Rate Limit(게스트) → Hangfire 필터.

---

## 5. 외부 연동

### 5.1 LLM 호출 패턴 (`AiProxyService`, 3,749 LOC)
```
Controller → ChatService → (Quota → BannedWord → PII) → AiProxyService
   → provider switch (openai/claude/gemini/perplexity/mistral/copilot/azureopenai/vertex)
   → ApiKeyPoolService.GetNextKey(provider)  // 라운드로빈 lock 보호
   → IHttpClientFactory.CreateClient(provider)  // Named HttpClient
   → POST → 429 시 ApiKeyPool.MarkAsCoolingDown(60s) + throw
   → ChatService catch → fallback model 1단계 재시도
```
- **추론 모델 분기** (`o1/o3/gpt-5`): `max_completion_tokens` 사용, temperature 미전송.
- **Fallback 매핑**: `gpt-4o → gpt-4o-mini`, `claude-opus → sonnet → haiku → gpt-4o-mini`(cross-provider) 등 12종.
- **Stream API (`SendChatMessageStreamAsync`)는 ApiKeyPool/Cooldown 우회**(H5).

### 5.2 Named HttpClient 풀 (`Program.cs`)
프로바이더별 `services.AddHttpClient("openai")`, `"claude"`, … 등록 + 타임아웃·BaseUrl 설정. 모든 외부 호출은 `IHttpClientFactory` 경유 (직접 `new HttpClient()` 금지).

### 5.3 Hangfire (SQL Server Storage)
- 4개 RecurringJob (cron UTC) — `daily-quota-reset`, `monthly-quota-reset`, `daily-report`, `monthly-report`. **Daily Reset이 사용량 0으로 초기화하지 않고 LastResetAt만 변경**(버그). 일/월 리포트는 **저장 미구현 TODO**.
- DB 연결 실패 시 Hangfire 등록을 빈 catch로 삼킴 (Program.cs:185) → 헬스체크 부재.

### 5.4 SignalR
- `ChatHub` (그룹 `conversation_{id}` 푸시), `NotificationHub` (`JoinUserNotifications(userId)`).
- **두 Hub 모두 `[Authorize]` 부재** + `JoinUserNotifications`가 클라이언트 입력 userId로 그룹 가입 → 다른 사용자 알림 도청 가능.
- **프론트엔드는 SignalR을 사용하지 않음** (`@microsoft/signalr` dead dependency).

### 5.5 LibreOffice (외부 프로세스)
경로 `C:\Program Files\LibreOffice\program\soffice.exe` 고정. HWP↔PDF, PPTX→PDF headless 변환. 미설치 시 PPTX 폴백 + 응답 헤더 `X-Pdf-Fallback-Pptx: true`.

### 5.6 Redis (선택)
미설치 시 `MemoryDistributedCache` 자동 폴백. 캐시 키 5종: `chat:resp:{agentId}:{model}:{hash}`(5분), `embedding:{hash}`(1h), `rag:{agentId}:{userId}:{hash}`(10분), `quota:user:{}:service:{}`(30분).

---

## 6. MSSQL → PostgreSQL 전환 시 고려사항

### 6.1 EF Core Provider 교체
- `Microsoft.EntityFrameworkCore.SqlServer` (8.0.0) → `Npgsql.EntityFrameworkCore.PostgreSQL` (8.x).
- `appsettings.json`의 `ConnectionStrings:DefaultConnection` 형식 전환:
  - From `Server=...;Database=...;User ID=...;Password=...;TrustServerCertificate=true;MultipleActiveResultSets=true`
  - To `Host=...;Port=5432;Database=AgentHub;Username=...;Password=...;Search Path=AIAgentManagement`
- `MultipleActiveResultSets`(MARS) 동등 옵션 없음 — 동일 DbContext 동시 enumeration 코드를 검사 필요.
- `OptionsBuilder.UseSqlServer(...)` → `UseNpgsql(...)` 일괄 교체. (`Program.cs`, `DesignTimeDbContextFactory` 있다면)

### 6.2 데이터 타입 차이
| 영역 | SQL Server | PostgreSQL | 영향 |
|---|---|---|---|
| 기본 문자열 | `nvarchar(N)` | `varchar(N)` 또는 `text` | EF가 자동 매핑하지만 `nvarchar(MAX)` 다수 컬럼은 PG `text`로 변환됨 — 길이 검증을 응용 코드/Validation에 보존 필요 |
| 시간 | `datetime2` (`GETDATE()`) | `timestamp` / `timestamptz` (`now()`) | `GETDATE()`/`SYSUTCDATETIME()` 직접 호출 SQL 점검 + UTC 통일(M13) |
| boolean | `bit` | `boolean` | EF 자동 매핑, 직접 작성 SQL은 `1/0` → `true/false` |
| 정수 자동증가 | `IDENTITY` | `bigserial`/`serial` 또는 `GENERATED BY DEFAULT AS IDENTITY` | EF Core 자동 처리, 단 raw SQL 시드 스크립트 점검 |
| Money | `decimal(10,4)` | `numeric(10,4)` | 호환 |
| JSON | `nvarchar(MAX)` (수동 직렬화) | `jsonb` (네이티브) | `DocumentChunk.Embedding`, `WorkflowNode.Connections`, `Presentation.Slides`, `Agent.AllowedEmbedDomains` 등 전환 시 `jsonb`로 옮기면 인덱싱·검색 가능 |
| 임베딩 벡터 | `nvarchar(MAX)` JSON | **`pgvector` 확장의 `vector(1536)`** | RAG 성능 핵심 — `<=>` 코사인 거리 + IVFFlat/HNSW 인덱스로 H1(OOM 위험) 해결 |
| Cascade Delete | 동일 | 동일 | EF 모델 그대로 유효, 단 핵심 마스터(ApiServices→Agents, Users→Tools/Workflows)는 Restrict로 강등 권장 |
| CHECK 제약 | 동일 | 동일 | 코드는 EF Fluent API로 작성되어 호환 |
| `MERGE`·`OUTPUT` 등 | T-SQL | 미지원/다른 문법 | DatabaseInitializer가 `EnsureCreated` 의존 — raw T-SQL 거의 없음. 단 루트 레거시 SQL 16+개는 PostgreSQL 호환 검토 후 폐기 |

### 6.3 인덱스 / 함수 영향
- T-SQL **filtered index** (`WHERE IsActive=1`, TeamMembers) → PG **partial index** (`WHERE is_active = true`) 동등.
- **Full-text search**: SQL Server `CONTAINS()`/`FREETEXT` (현재 미사용) → PG `tsvector` + `to_tsquery` (한국어는 `pg_bigm`/`zhparser` 또는 외부 형태소 분석 필요).
- **컬레이션**: SQL Server 기본 `Korean_Wansung_CI_AS` → PG `ko_KR.UTF-8` (CI/AS 흉내는 `citext` 확장 또는 `LOWER()` 인덱스). BannedWord 한글 비교 영향 점검.
- **저장 프로시저/함수**: 현재 코드베이스 미사용 (Service에서 LINQ만 사용). 마이그레이션 안전.
- **GUID 디폴트**: `NEWID()` → `gen_random_uuid()` (pgcrypto 확장).

### 6.4 마이그레이션 절차
1. 35테이블의 **PostgreSQL용 baseline migration**을 EF로 새로 생성 (`dotnet ef migrations add Init -- --provider Npgsql`).
2. 단일 PG 인스턴스에 `AIAgentManagement` 스키마 격리 (`Search Path=AIAgentManagement`). DocUtil/Career 다른 스키마와 동거.
3. 데이터 이관: `bcp` → CSV → `COPY` 또는 pgloader 사용. 시계열(ApiUsages, ChatMessages, DocumentChunks, ActivityLogs)는 **bigint identity 일관성** 검증.
4. JSON nvarchar(MAX) 컬럼은 일괄 `text` 또는 `jsonb`로 들이고, 임베딩만 `vector(1536)` 별도 컬럼 추가 후 백필 → 인덱스 생성 → 구 컬럼 drop.
5. 쿠키 인증/Hangfire는 PG storage(`Hangfire.PostgreSql`) 패키지로 교체.

---

## 7. monorepo 통합 시 변경 필요 항목

### 7.1 Nexus provider 추가 (`CallNexusAsync`)
- `appsettings.json:AiApiSettings:Nexus` 섹션 추가 (BaseUrl, ApiKey 또는 mTLS 인증).
- `Program.cs`: `services.AddHttpClient("nexus", c => { c.BaseAddress = ...; c.Timeout = ...; })`.
- `Services/AiProxyService.cs`: switch에 `"nexus"` 분기 + `CallNexusAsync(model, messages, ct)` 메서드 신설. 응답 매핑(usage·content·tool_calls)을 `AiResponseDto`에 통일.
- `Data/DatabaseInitializer.cs`: `ApiServices` 시드에 `nexus` 추가 + `ApiServiceModels`에 사용 모델 카탈로그 등록.
- `ApiKeyPoolService`에 nexus 풀 추가 (다중 키 지원이 필요한 경우).
- `IAiProxyService` 인터페이스 변경 없음 — 분기 추가만으로 외부 표면 고정.
- 위치: `Services/AiProxyService.cs` 내 `switch (serviceType.ToLower())` (정확한 라인은 코드 변경 시점에 확인) — provider별 약 200~400 LOC 패턴.

### 7.2 DocUtil 운영자 기능 흡수 (BFF 패턴)
- AgentHub가 **유일한 운영자 콘솔**이 되며, DocUtil의 운영자 페이지를 IFrame이 아닌 **AgentHub Vue SPA에서 직접 호출**.
- 신규 컨트롤러: `DocUtilProxyController` 또는 `BffController`. JWT 검증 후 DocUtil 백엔드(FastAPI)에 `httpx` 대신 .NET `IHttpClientFactory("docutil")`로 위임.
- DocUtil 인증은 **AgentHub JWT를 그대로 forwarding** 또는 **상호 mTLS / Service Token** 두 옵션 중 후자 권장 (DocUtil은 외부 노출 차단).
- Vue 측: `/docutil/...` 라우트 신설, 기존 DocUtil 페이지를 `views/docutil/*.vue`로 이식 (Pinia 스토어 공유).
- ActivityLog에 `Source=docutil-proxy`로 표기하여 감사 일원화.

### 7.3 자체 KB → DocUtil 위임 (KnowledgeBaseDocument deprecate)
- 신규 코드 경로: `IRagService.RetrieveAsync` 내부에서 **DocUtil Vector Search API 호출** + 결과만 system 메시지에 주입.
- `KnowledgeBaseDocument`/`DocumentChunk`/`AgentDocument` 테이블은 **읽기 전용(레거시)** 으로 동결 → 신규 업로드는 차단(컨트롤러에 410 Gone) 또는 DocUtil로 자동 전달.
- `EmbeddingService` / `DocumentIndexingService` / `FileParsingService` (PDF/Excel/Word/PPTX/HWP) → DocUtil로 이관.
- `AgentDocument`는 **Agent ↔ DocUtil document_id** 매핑 테이블로 의미 변경 (외래 키 제거 + 문자열 ID 보유).
- 마이그레이션 단계: ① RagService에 feature flag(`UseExternalKb`) → ② 신규 업로드만 DocUtil → ③ 기존 데이터 백필 → ④ 자체 KB 삭제.

### 7.4 OpenAI 호환 API의 진짜 SSE 보강
- 현재 `OpenAICompatController.cs:138`의 가짜 SSE를 제거. `ChatService.SendDirectMessageStreamAsync(IAsyncEnumerable<string>)` 신설.
- `AiProxyService.SendChatMessageStreamAsync`에 **ApiKeyPool/Cooldown 적용**(H5 해결) + `IAsyncEnumerable<ChatChunk>` 반환.
- 컨트롤러: `Response.ContentType = "text/event-stream"` + `Response.Headers["X-Accel-Buffering"]="no"` + `await foreach` chunk → `data: {json}\n\n` 작성 + flush.
- IIS InProcess의 chunked transfer 제대로 흐르는지 검증 필요(`Response.Body.FlushAsync` 호출).
- 외부 시스템 요구: SDK들이 OpenAI 표준 chunk 포맷(`{ id, object:"chat.completion.chunk", choices: [{ delta: { content: "..." } }] }`)을 기대하므로 정확히 매핑. 마지막에 `data: [DONE]\n\n`.
- usage 추정값(0.65/0.35) 제거 — 가능한 프로바이더는 실제 토큰 수, 불가능하면 별도 헤더로 표시.

### 7.5 PostgreSQL 단일 인스턴스 + 스키마 격리
- 단일 PG 클러스터 → 스키마 3개: `AIAgentManagement` / `docutil` / `idino_career` (또는 명명 통일).
- DbContext에 `modelBuilder.HasDefaultSchema("AIAgentManagement")` 추가.
- 연결 문자열에 `Search Path=AIAgentManagement,public`.
- Hangfire는 별도 스키마(`hangfire`) 권장.

### 7.6 LlmRouting 도입 (External / Internal / Hybrid)
- 신규 엔티티: `LlmRouting` (`AgentId FK`, `Mode ∈ External|Internal|Hybrid`, `RoutingPolicyJson nvarchar(MAX)`, `Priority`, `IsActive`).
- `RoutingPolicyJson` 예: `{ "primary": "openai/gpt-4o", "fallbacks": ["anthropic/sonnet", "internal/nexus"], "rules": [{ "if": "tokens>4000", "use": "internal/nexus" }] }`.
- `AiProxyService` 진입 시점에 `LlmRoutingService.Resolve(agentId, request) → ResolvedRoute` 단계를 추가하고, 기존의 `ChatService.GetDefaultFallbackModel`을 흡수.
- 변경 영향:
  - `ChatService.SendMessageAsync` 단순화 — fallback 매핑 12종을 `LlmRouting`으로 이관.
  - `AiProxyService.SendChatMessageStreamAsync`에도 동일 routing 적용 (현재 키 풀 우회 버그와 함께 해결).
  - DTO `ChatRequest`에 명시적 model이 와도 routing 정책이 우선. UI에서 사용자가 모델 강제 지정 시 정책 우회 토글(`OverridePolicy=true`).
- 연동: `ApiKey.AgentId` 바인딩과 결합하여 외부 시스템마다 다른 routing을 할당.

---

## 8. 알려진 보안/성능 위험 (요약)

| ID | 분류 | 위치/내용 | 통합 시 처리 우선순위 |
|---|---|---|---|
| C1 | 보안 | `ApiKeyService.cs:318`, `ApiKeyAuthService.cs:89` AES-CBC 고정 IV(zero) | **Phase 1 마이그레이션 동시 처리** — per-record random IV 또는 AES-GCM, KeyHash 컬럼과 함께 재암호화 |
| C2 | 보안 | `ApiKeyService.cs:24` JWT SecretKey ↔ AES 암호화 키 재사용 | KMS/User Secrets로 분리 |
| C3 | 성능·보안 | `ApiKeyAuthService.cs:34-66` 모든 활성 키 풀스캔 + AES 복호화 | `KeyHash UNIQUE`(SHA-256) 추가 → O(1) lookup |
| C4 | 데이터 | `Users.Email` UNIQUE 미설정 | baseline 마이그레이션에 포함 |
| C5 | 보안 | `CSharpToolExecutor.cs:27-50,84` 코드 인젝션 + `AssemblyLoadContext.Default` 영구 누수 | collectible AssemblyLoadContext + 최소 권한 또는 기능 차단 |
| C6 | 보안 | `Program.cs:362` DB 평문 비번 하드코딩 | 환경변수/User Secrets 이관 |
| C7 | 데이터 | EF InitialCreate 부재 + EnsureCreated → 환경 drift | **PG 전환 baseline에서 자연 해결** |
| C8 | 보안 | `ChatHub`/`NotificationHub` `[Authorize]` 부재 + 임의 userId 입력 | `[Authorize]` + `Context.UserIdentifier` 사용 |
| C9 | 호환성 | `OpenAICompatController.cs:138` 가짜 SSE | §7.4의 진짜 SSE 보강과 함께 해결 |
| C10 | 보안 | `appsettings.*.json` 시크릿 평문 커밋 | Vault/IIS 환경변수 + git 이력 정화 |
| H1 | 성능 | `RagService.cs:112` 전체 청크 메모리 로드 | DocUtil 위임으로 자연 해결, 잔여는 pgvector |
| H2 | 안정성 | `WorkflowExecutionService.cs:50` `Task.Run` scoped DbContext | `IServiceScopeFactory` 사용 + CancellationToken |
| H3 | 기능 | Workflow Condition/DataTransform/Loop NO-OP | 정식 구현 또는 노드 비활성 |
| H4 | 메모리 | `ChatService.cs:14 _convLocks` 무한 증가 | TTL evict (MemoryCache 슬라이딩 1h) |
| H5 | 안정성 | `AiProxyService.SendChatMessageStreamAsync` ApiKeyPool/Cooldown 우회 | §7.4와 동시 |
| H6 | 안정성 | `ScriptToolExecutor.cs:148` 임시 input 파일 정리 버그 | 동일 Guid 보존 |
| H7 | 운영 | `Program.cs:185` Hangfire 빈 catch | 실패 시 헬스체크 노출 |
| H8 | 운영 | `per-user` Rate Limit 정책 정의만 | 모든 `/api/*` 컨트롤러 부착 |
| H10 | 정확성 | `QuotaService.RecordUsageAsync` 토큰수 무시 | `CurrentUsage += tokens` |
| H13 | 구조 | `AiProxyService` 3,749 LOC god class | provider별 Strategy 분리 (Nexus 추가 시 자연스럽게) |

---

## 9. 미해결 TODO / 기술 부채 (통합 관련)

1. **EF Core baseline 마이그레이션 부재** — 통합 시점에 PostgreSQL용 `dotnet ef migrations add Init` 새로 작성 (구 SQL Server 마이그레이션 1개는 폐기). 루트 레거시 `*.sql` 16+개도 함께 폐기 표시.
2. **시드 데이터 (`DatabaseInitializer.cs`, 866 LOC)** — Roles/Users/ApiServices/ApiServiceModels 시드를 PG idempotent로 재작성. Nexus 추가, 일부 deprecated 모델 정리, admin 자가치유(`Admin123!` 강제 재설정) 정책 유지 여부 결정.
3. **가짜 SSE → 진짜 SSE** (C9) — 외부 OpenAI SDK·Cursor·LangChain 호환성을 위해 우선 처리. `IAsyncEnumerable<ChatChunk>` 형태로 ChatService/AiProxyService 양쪽 노출. provider별 streaming endpoint 구현 점검(OpenAI/Anthropic/Gemini/Mistral은 SSE 지원, Tavily/Vertex 일부 미지원).
4. **API Key 회전(Rotation)** — 24시간 유예기간 미구현. `ApiKey.PreviousKeyHash` + `RotatedAt` 컬럼 + 백그라운드 정리.
5. **Webhook 이벤트** (`key.expiring`, `quota.exceeded`, `agent.message.failed`) 미구현 — DocUtil/Career에서 운영 알림 받으려면 필요.
6. **CIDR IP 검증** — `AllowedIps`가 단순 문자열 일치. monorepo 내부 호출은 보통 사설 대역(10.0.0.0/8)이라 CIDR 필요.
7. **Redis 분산 Rate Limit / Pool 쿨다운** — 다중 인스턴스 배포 시 카운터/쿨다운 공유 필요. `IApiKeyRateLimiter`, `IApiKeyPoolService` Redis 백엔드.
8. **랜딩 / 약관 / 개인정보처리방침** Vue 컴포넌트 미완 — 통합 시 IDINO 공통 정책으로 교체.
9. **Agent 편집 모드** AgentBuilder는 신규 생성만 — 통합 후 운영자 UX 핵심.
10. **AiProxyService 분리** — Strategy 패턴으로 8개 provider 클래스로 쪼개기. Nexus 추가가 트리거.
11. **Frontend 정리** — AgentChat 5,286줄, AgentMultiChat 4,031줄, PresentationBuilder 1,830줄 분해. raw axios 4건(`ToolList`, `ToolBuilder`, `WorkflowList`, `WorkflowExecutionMonitor`) → `@/services/api` 통합. dead dependency(SignalR/vue-chartjs) 제거 또는 활성화.
12. **시간대 통일** — `GETDATE()` 잔존 vs `SYSUTCDATETIME()` — PG에서는 `now() AT TIME ZONE 'UTC'` 또는 `timestamptz` 일관 적용.
13. **Hangfire 일/월 리포트 본체 미구현** (`ReportGenerationJob`) — TODO 주석만 존재.
14. **Daily Quota Reset 버그** — Usage를 0으로 리셋하지 않고 LastResetAt만 갱신. PG 전환과 함께 정정.

---

## 부록: 참조 위치 (절대경로)

- `D:\workspace\AIAgentManagement\TECHSPEC.md` (1,171 라인 종합 명세)
- `D:\workspace\AIAgentManagement\CLAUDE.md`
- `D:\workspace\AIAgentManagement\.claude\rules\architecture.md`
- `D:\workspace\AIAgentManagement\.claude\rules\anti-patterns.md`
- `D:\workspace\AIAgentManagement\.claude\rules\domain-model.md`
- `D:\workspace\AIAgentManagement\.claude\rules\agent-collaboration.md`
- `D:\workspace\AIAgentManagement\.claude\rules\testing.md`
- `D:\workspace\AIAgentManagement\Program.cs` (575 라인, DI/미들웨어/Hangfire 등록)
- `D:\workspace\AIAgentManagement\Data\AIAgentManagementDbContext.cs` (252 라인)
- `D:\workspace\AIAgentManagement\Data\DatabaseInitializer.cs` (866 라인, 시드)
- `D:\workspace\AIAgentManagement\Migrations\20260320012331_AddApiUsagePromptAndIndexes.cs` (유일 EF migration)
- `D:\workspace\AIAgentManagement\Migrations\AIAgentManagementDbContextModelSnapshot.cs` (2,373 라인)
- `D:\workspace\AIAgentManagement\Services\AiProxyService.cs` (3,749 라인)
- `D:\workspace\AIAgentManagement\Services\ChatService.cs` (1,049 라인)
- `D:\workspace\AIAgentManagement\Services\ApiKeyAuthService.cs:34-66, 89` (보안 핫스팟)
- `D:\workspace\AIAgentManagement\Services\ApiKeyService.cs:24, 318` (보안 핫스팟)
- `D:\workspace\AIAgentManagement\Services\RagService.cs:112` (성능 핫스팟)
- `D:\workspace\AIAgentManagement\Controllers\OpenAICompatController.cs:138` (가짜 SSE)
- `D:\workspace\AIAgentManagement\Controllers\AgentsController.cs` (1,080 라인)
- `D:\workspace\AIAgentManagement\Hubs\ChatHub.cs`, `NotificationHub.cs` ([Authorize] 누락)
- `D:\workspace\AIAgentManagement\appsettings.json` / `appsettings.Development.json` / `appsettings.Production.json` (시크릿 평문 노출)

> 본 문서는 IDINO_Agent_Hub monorepo 통합 작업의 AgentHub 측 참조 자료다. 통합 진행 시 §7의 6개 변경 항목을 우선 처리하고, §8/§9의 부채는 단계별 로드맵에 편입한다.
