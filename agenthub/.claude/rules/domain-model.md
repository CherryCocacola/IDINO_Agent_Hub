# AgentHub 도메인 모델

코드, 변수, 주석, DTO 명에서 아래 정의된 용어를 정확히 사용한다. 동의어 혼용 금지.

## 핵심 엔티티 (Models/)

### User (사용자)
- 인증 주체. `Email` 유일, 비밀번호는 `BCrypt` 해시
- `UserRole`로 N:M `Role`과 연결 — 역할 기반 접근 제어 (RBAC)
- `UserSession` — 로그인 세션 추적 (Refresh Token 보관)
- `UserPreference` — 다국어/테마 등 개인 설정

### Agent (AI 에이전트)
- 사용자가 만드는 AI 인격체. `SystemPrompt`, `Model`, `ServiceType` 보유
- `EnableRag` / `EnableWebSearch` / `PiiProtection` 플래그
- `AgentDocument` 통해 RAG 문서와 N:M
- 채팅(`ChatConversation`)의 호스트

### ApiService (LLM 프로바이더)
- OpenAI, Claude, Gemini, Perplexity, Mistral 등 외부 LLM 서비스의 추상화
- `ServiceType` (string) — 코드 분기 키 (`"openai"`, `"claude"`, ...)
- `ApiServiceModel` — 프로바이더가 제공하는 모델 카탈로그 (gpt-4o, claude-3-5-sonnet, ...)

### ApiKey (API 키)
- 사용자가 외부 시스템에서 본 시스템을 호출할 때 사용하는 키
- `AgentId` 바인딩 — 키 하나당 한 에이전트
- 라운드로빈 풀(`IApiKeyPoolService`) — 같은 Agent에 여러 키 등록 시 분산
- Rate Limit (`IApiKeyRateLimiter`) — 키별 분당/시간당/일당 호출 제한

### ApiQuota (할당량)
- 사용자별 × ApiService별 사용량 한도
- `DailyLimit`, `MonthlyLimit`, `DailyUsage`, `MonthlyUsage`
- Hangfire `QuotaResetJob`이 일/월 단위로 리셋

### ApiUsage (사용 기록)
- 각 LLM 호출의 원자 기록 — 토큰 수, 비용, 응답 시간, 프롬프트 본문
- 분석/리포트의 소스 데이터

### ChatConversation / ChatMessage (대화 / 메시지)
- 사용자 ↔ Agent 간 대화 컨테이너
- `ChatMessage.Role`: `"user" | "assistant" | "system" | "tool"`
- 게스트 채팅(공개)도 동일 모델, `UserId = null`

### KnowledgeBaseDocument / DocumentChunk (지식베이스)
- 업로드된 원본 문서와 청크 단위 임베딩
- `Embedding` (vector, 1536d) — `text-embedding-3-small` 기본
- `AgentDocument`로 Agent에 N:M 연결

### Workflow / WorkflowNode / WorkflowExecution (워크플로우)
- 노드 기반 비주얼 파이프라인 (Vue Flow 에디터)
- 노드 타입: `llm`, `tool`, `condition`, `transform`, `input`, `output` 등
- `WorkflowExecutionService` + `WorkflowEngine`이 실행
- `WorkflowNodeExecution` — 각 노드의 실행 기록

### Tool / ToolExecution / ToolVersion (도구)
- 사용자 정의 함수형 도구 (LLM이 함수 호출 시 사용)
- 실행 백엔드 3종: **C# (Roslyn)**, **Script (외부 프로세스)**, **API (HTTP 호출)**
- `IToolExecutionService`가 분기 → `ICSharpToolExecutor` / `IScriptToolExecutor` / `IApiToolExecutor`

### Presentation / PresentationSlide / PresentationTemplate (프레젠테이션)
- LLM이 생성하는 PPTX 산출물
- 템플릿(`PresentationTemplate`)을 PPTX 파일로 업로드 → `IPptxTemplateParser`가 파싱
- `PptxGenerationService`가 OpenXml로 슬라이드 생성

### BannedWord (금칙어)
- 입력/출력 필터링용 단어 사전. 카테고리별 분류, 캐싱(`IMemoryCache` / `CachingService`)

### PiiDetectionLog (PII 검출 로그)
- 개인정보 검출 시점/유형/원본/마스킹된 값 기록
- 감사(audit) 추적 + 사용자 알림용

### ActivityLog (활동 로그)
- 모든 API 호출의 메타 기록 (사용자, 엔드포인트, 상태, 응답시간)
- `ActivityLoggingMiddleware` → `ActivityLogChannel` → `ActivityLogWorker` (배치 INSERT)

### Team / TeamMember (팀)
- 사용자 그룹화. 팀 단위 자원 공유

### ExamplePrompt / Faq / Tutorial (콘텐츠)
- 운영자가 관리하는 정적 콘텐츠

## 횡단 인프라 (Infrastructure/)

### ActivityLogChannel
- `System.Threading.Channels.Channel<ActivityLog>` 래퍼 (Singleton)
- 미들웨어가 producer, `ActivityLogWorker`(IHostedService)가 consumer

### JsonElementRawConverter / DictionaryStringObjectJsonConverter
- `Dictionary<string, object>` 안의 `JsonElement` 직렬화 보장
- 차트 데이터, 워크플로우 노드 입출력 등에 사용

### CachingService
- `IMemoryCache` 래퍼. 키 네임스페이스 통일, TTL 표준화

## API 인증 흐름

| 인증 방식 | 사용처 | 검증자 |
|---|---|---|
| JWT Bearer | `/api/*` | `Microsoft.AspNetCore.Authentication.JwtBearer` |
| API Key | `/v1/*` (OpenAI 호환) | `[ApiKeyAuth]` Attribute → `IApiKeyAuthService` |
| Anonymous | `/api/auth/login`, 게스트 채팅 | (없음, Rate Limiter만) |
| Hangfire Filter | `/hangfire` | `HangfireAuthorizationFilter` (관리자) |

## 용어 규칙

| 정확한 용어 | 금지 용어 |
|---|---|
| Agent (에이전트) | bot, assistant, character |
| ApiService (프로바이더) | provider, vendor, llm |
| ServiceType ("openai", "claude") | provider name, vendorId |
| Conversation (대화) | session, chat, thread |
| Message (메시지) | turn, post |
| Knowledge Base (지식베이스) | document store, vector db |
| Document Chunk | passage, segment, fragment |
| Workflow Node | step, stage, block |
| Tool / ToolExecution | function, plugin, action |
| Quota (할당량) | limit, usage cap |
| Activity Log (활동 로그) | access log, audit trail (audit는 PII 전용) |
| API Key Pool | key rotation, key set |
| RAG (검색 증강 생성) | search, retrieval (단독 사용 시) |

## ServiceType 표준 값

문자열 비교 시 항상 소문자로 비교. `appsettings.json`의 키는 PascalCase지만 코드 내 `ServiceType`은 소문자.

```
"openai", "claude", "gemini", "google", "perplexity",
"mistral", "copilot", "azureopenai", "tavily"
```

## ChatMessage.Role 값

```
"user" | "assistant" | "system" | "tool"
```
프로바이더별 변환은 `AiProxyService` 내부에서 처리 (예: Anthropic의 `system`은 별도 파라미터).
