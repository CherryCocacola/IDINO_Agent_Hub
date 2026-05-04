# AgentHub — 기술 명세서 (TECHSPEC)

> 작성일: 2026-04-30  
> 버전: v1.0 (현재 코드베이스 기준 종합)  
> 대상 환경: Windows Server + IIS + SQL Server (프로덕션: `agenthub.idino.co.kr`)

---

## 목차
1. [제품 개요](#1-제품-개요)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [기술 스택](#3-기술-스택)
4. [도메인 모델 (35개 엔티티)](#4-도메인-모델)
5. [백엔드 서비스 레이어](#5-백엔드-서비스-레이어)
6. [API 설계](#6-api-설계)
7. [인증·인가 체계](#7-인증인가-체계)
8. [핵심 데이터 흐름 (시퀀스)](#8-핵심-데이터-흐름-시퀀스)
9. [프론트엔드 아키텍처](#9-프론트엔드-아키텍처)
10. [RAG 파이프라인](#10-rag-파이프라인)
11. [워크플로우 엔진](#11-워크플로우-엔진)
12. [도구 시스템](#12-도구-시스템)
13. [프레젠테이션 빌더](#13-프레젠테이션-빌더)
14. [인프라·배포·운영](#14-인프라배포운영)
15. [데이터베이스 운영](#15-데이터베이스-운영)
16. [알려진 이슈 및 기술 부채](#16-알려진-이슈-및-기술-부채)
17. [개선 우선순위 로드맵](#17-개선-우선순위-로드맵)

---

## 1. 제품 개요

### 1.1 정체성
**AgentHub** (코드명: AIAgentManagement) — 기관·기업 내 다양한 LLM 프로바이더(OpenAI, Claude, Gemini, Mistral, Perplexity 등)를 단일 플랫폼에서 통합 운영하고, 비기술 사용자가 코딩 없이 AI 에이전트를 만들어 배포·공유할 수 있는 **No-code AI Agent 관리 플랫폼**.

### 1.2 LiteLLM 대비 포지셔닝
| 축 | LiteLLM | AgentHub |
|---|---|---|
| 정체성 | LLM API 게이트웨이/프록시 | 에이전트 생성·관리·공유 엔드-투-엔드 플랫폼 |
| 핵심 사용자 | 개발자/DevOps | 비기술 업무 담당자 + 개발자 |
| UI | 없음 (API만) | Vue 3 SPA (33개 라우트) |
| Agent 빌더 | 없음 | 5단계 위저드 |
| 공개 URL/임베드 | 없음 | `/chatbot/{code}` + `/embed/{code}` + QR |
| RAG/PII 내장 | 없음 | 내장 |
| 지원 LLM 수 | 140+ (2,600+ 모델) | 8종 채팅 + 5종 이미지 + 3종 비디오 |
| 비용 추적 | 정밀 | 기본 (ApiUsage 단순 집계) |

**상호 보완 가능**: AgentHub의 `IAiProxyService` BaseUrl을 LiteLLM 프록시로 변경하면 두 제품을 결합할 수 있다.

### 1.3 6대 기능 영역
1. **AI Agent 관리** — 5단계 위저드, 시스템 프롬프트, QR/iframe 배포, 템플릿
2. **AI 채팅** — 단일/멀티(최대 4) 비교, 파일 첨부, OpenAI 호환 API(`/v1/*`)
3. **Knowledge Base (RAG)** — PDF/Word/Excel/HWP 업로드, 청크 임베딩, 코사인 유사도 검색
4. **워크플로우** — Vue Flow 기반 노드 그래프, Kahn 위상 정렬 + 레벨별 병렬 실행
5. **콘텐츠 생성** — DALL-E/Imagen/Flux2 이미지, AI 슬라이드 자동 생성 + PPTX/PDF 내보내기
6. **관리·통제** — 사용량/비용 분석, 사용자/팀, BannedWord, PII, DB 백업, SystemHealth

### 1.4 타겟 시나리오
- 부서별 전용 AI 봇 (코딩 없이 5분 내 배포)
- 사내 문서 RAG Q&A (PDF/HWP 업로드 → 챗)
- 외부 웹사이트 챗봇 임베드 (`<iframe>` + 도메인 화이트리스트)
- OpenAI SDK 호환 API로 기존 시스템 통합

---

## 2. 시스템 아키텍처

### 2.1 전체 구성도 (논리)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         External Clients                             │
│  Browser (Vue SPA) │ OpenAI SDK │ Postman │ Embed iframe │ Mobile   │
└──────────────┬──────────────────────────────────────────────────────┘
               │ HTTPS (agenthub.idino.co.kr)
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│   IIS InProcess Hosting (W3SVC)  ──  Windows Server                  │
│   ┌─────────────────────────────────────────────────────────────┐    │
│   │  ASP.NET Core 8.0 (Kestrel In-Process)                      │    │
│   │                                                             │    │
│   │  Middleware Pipeline (순서 고정):                            │    │
│   │   GlobalExceptionHandler → SecurityHeaders → Swagger(dev)   │    │
│   │   → RequireHttpsForDomain → StaticFiles → CORS              │    │
│   │   → Authentication(JWT) → Authorization → RateLimiter       │    │
│   │   → ActivityLogging → Endpoints                             │    │
│   │                                                             │    │
│   │  Endpoints:                                                 │    │
│   │   /api/*    JWT + per-user Rate Limit (정의만, 미부착)       │    │
│   │   /v1/*     ApiKeyAuthorize + ip-openai (30/min)            │    │
│   │   /api/agents/public/{code}/*  Anonymous + ip-guest (20/min)│    │
│   │   /hubs/chat, /hubs/notification  SignalR (인증 없음 ⚠️)     │    │
│   │   /hangfire  HangfireAuthorizationFilter (Admin)            │    │
│   │   /swagger   Dev only                                       │    │
│   │                                                             │    │
│   │  Background:                                                │    │
│   │   Hangfire 4 jobs (daily/monthly quota, daily/monthly rpt)  │    │
│   │   ActivityLogWorker IHostedService (Channel batch INSERT)   │    │
│   └─────────────────────────────────────────────────────────────┘    │
└──────┬──────────────────┬──────────────────┬──────────────────┬─────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────┐  ┌────────────────┐
│ SQL Server   │  │ Redis (선택)    │  │ Hangfire │  │ External APIs  │
│ 192.168.10.  │  │ localhost:6379  │  │ SqlServer│  │ OpenAI/Claude/ │
│ 159          │  │ Memurai 권장    │  │ Storage  │  │ Gemini/Tavily/ │
│ (35 tables,  │  │ 폴백:           │  │          │  │ Perplexity/    │
│ EnsureCreated│  │ MemoryDistCache │  │          │  │ Mistral/Imagen │
│ + 1 EF mig)  │  │                 │  │          │  │ /DALL-E/Flux2  │
└──────────────┘  └─────────────────┘  └──────────┘  └────────────────┘
                                                      ▲
                                                      │
                                          ┌───────────┴────────────┐
                                          │ LibreOffice (HWP/PPTX  │
                                          │  ↔ PDF headless 변환)  │
                                          └────────────────────────┘
```

### 2.2 핵심 토폴로지 결정
- **단일 IIS 서버 배포 가정** — Rate Limiter, ApiKeyPool 쿨다운, ApiKeyRateLimiter 모두 **인-메모리 단일 인스턴스 상태**. 다중 서버 배포 시 Redis 기반 분산 카운터 필요(현재 미구현).
- **선택적 Redis** — 미설치 시 자동 폴백(`Program.cs:128-158`). 영향: RAG/임베딩/할당량 캐싱이 인-메모리로 전환되어 프로세스 재시작 시 손실, 다중 인스턴스 간 캐시 공유 불가.
- **InProcess 호스팅** — IIS와 .NET 프로세스가 분리되지 않음. 배포 시 `app_offline.htm` 자동 생성(MSDeploy `EnableMsDeployAppOffline=true`).

### 2.3 환경 분기
| 측면 | Development | Production |
|---|---|---|
| Swagger UI | ON (`/swagger`) | OFF |
| 정적 파일 | `UseSpaStaticFiles` (ClientApp/dist) | `UseDefaultFiles + UseStaticFiles` (wwwroot) |
| SPA Fallback | Vite proxy `http://localhost:5173` | `MapFallbackToFile("/index.html")` |
| HTTPS 강제 | OFF | `agenthub.idino.co.kr`일 때만 |

---

## 3. 기술 스택

### 3.1 Backend (`AIAgentManagement.csproj`)
| 분류 | 기술 | 버전 |
|---|---|---|
| 런타임 | .NET | 8.0 |
| Web | ASP.NET Core | 8.0 (InProcess IIS) |
| ORM | EF Core SqlServer | 8.0.0 |
| DB | Microsoft SQL Server | (엔터프라이즈 가정) |
| 인증 | JWT Bearer + API Key (Custom Attribute) | System.IdentityModel.Tokens.Jwt 8.3.0 |
| 비밀번호 | BCrypt.Net-Next | 4.0.3 |
| 캐시 | StackExchange.Redis (선택) | 2.7.20 |
| 백그라운드 | Hangfire (Core/SqlServer/AspNetCore) | 1.8.6 |
| 실시간 | SignalR | (내장 8.0) |
| OpenAPI | Swashbuckle.AspNetCore | 6.5.0 |
| 문서 처리 | DocumentFormat.OpenXml | 2.20.0 |
| 문서 처리 | ClosedXML (Excel) | 0.102.2 |
| 문서 처리 | PdfPig (PDF 텍스트 추출) | 0.1.8 |
| 문서 처리 | CsvHelper | 33.0.1 |
| 문서 처리 | LibreOffice (HWP/PPTX↔PDF) | 외부 설치 |
| QR | QRCoder | 1.6.0 |
| Roslyn | Microsoft.CodeAnalysis.CSharp | 4.5.0 |

### 3.2 Frontend (`ClientApp/package.json`)
| 분류 | 기술 | 버전 |
|---|---|---|
| Framework | Vue | ^3.4.21 |
| Lang | TypeScript | ^5.3.3 |
| Build | Vite | ^5.1.0 |
| 상태 | Pinia | ^2.1.7 (스토어 1개: auth) |
| Router | vue-router | ^4.2.5 |
| i18n | vue-i18n | ^9.14.5 (ko/en) |
| UI | Bootstrap 5.3 + Bootstrap Icons | ^5.3.2 / ^1.11.3 |
| Charts | Chart.js + vue-chartjs | ^4.4.2 / ^5.3.1 (실사용 1곳) |
| Workflow | @vue-flow/core + background + controls | ^1.48.2 |
| Markdown | marked + DOMPurify + prismjs | ^11.0.0 / ^3.0.6 / ^1.29.0 |
| HTTP | axios | ^1.6.5 |
| SignalR | @microsoft/signalr | ^8.0.0 (**dead dependency, 미사용**) |

### 3.3 외부 LLM 프로바이더 (`appsettings.json:13-55`)
| 프로바이더 | 용도 | API Key 풀 지원 |
|---|---|---|
| OpenAI | Chat (gpt-5/o3/o1/4o) + Embedding (text-embedding-3-small) + DALL-E | ✅ |
| Claude (Anthropic) | Chat (claude-opus-4-6/sonnet-4-6/haiku-4-5) | ✅ |
| Gemini (Google AI) | Chat (gemini-3.1/2.5-pro) + 이미지 | ✅ |
| Perplexity | Chat + 웹검색 | ✅ |
| Mistral | Chat (large/small-latest) | ✅ |
| Azure OpenAI | Chat (자체 deploy) | ✅ |
| GitHub Copilot | Chat | ✅ |
| Tavily | 웹 검색 + Deep Research | ❌ (단일 키) |
| Vertex AI (Imagen4/Gen4) | 이미지 | ❌ |
| Stability/Flux2 | 이미지 | ❌ |

---

## 4. 도메인 모델

### 4.1 엔티티 그룹 (총 35개)

#### 인증/사용자 (7)
`User`, `Role`, `UserRole`, `UserSession`, `UserPreference`, `Team`, `TeamMember`

#### 에이전트/LLM 카탈로그 (4)
`ApiService`, `ApiServiceModel`, `Agent`, `AgentDocument`

#### 채팅/사용량 (3)
`ChatConversation`, `ChatMessage`, `ApiUsage`

#### RAG (2)
`KnowledgeBaseDocument`, `DocumentChunk`

#### 워크플로우 (4)
`Workflow`, `WorkflowNode`, `WorkflowExecution`, `WorkflowNodeExecution`

#### 도구 (3)
`Tool`, `ToolVersion`, `ToolExecution`

#### 프레젠테이션 (3)
`Presentation`, `PresentationSlide`, `PresentationTemplate`

#### 보안/모니터링 (5)
`ApiKey`, `ApiQuota`, `ActivityLog`, `BannedWord`, `PiiDetectionLog`

#### 콘텐츠/시스템 (4)
`ExamplePrompt`, `Faq`, `Tutorial`, `SystemSetting`

### 4.2 주요 엔티티 상세

#### User
| 컬럼 | 타입 | 비고 |
|---|---|---|
| UserId | int PK identity | |
| Email | nvarchar(100) NN | **UNIQUE 인덱스 누락** ⚠️ |
| PasswordHash | nvarchar(255) NN | BCrypt(`$2a$/$2b$/$2y$`) |
| FullName, PhoneNumber, Department, Bio, ProfileImageUrl | | |
| Status | nvarchar(20) NN | CHECK IN('Active','Pending','Inactive') |
| IsEmailVerified, IsDeleted | bit | Soft delete (글로벌 필터 미적용) |
| TwoFactorSecret/Enabled/BackupCodes | | 2FA 인프라 (실제 활성화 여부 미확인) |
| PasswordResetToken/Expiry | | 2시간 유효, BCrypt 해시 저장 |

#### Agent (핵심)
- `AgentCode` UNIQUE — 외부 노출 식별자
- `ServiceId FK Cascade` — ApiService 삭제 시 모든 Agent 연쇄 삭제 ⚠️
- `SystemPrompt nvarchar(MAX)`, `Temperature decimal(3,2)`, `MaxTokens`, `DefaultModel`
- 공개/임베드: `IsPublic`, `AllowGuestChat`, `AllowedEmbedDomains nvarchar(2000)`, `WelcomeMessage`, `PlaceholderText`, `ChatTheme(light/dark)`
- 보안: `EnableRag`, `PiiProtectionEnabled`, `PiiProtectionMode(Block|Mask|NULL=글로벌)`
- 인덱스 5종: `IsActive`, `(IsActive,IsPublic)`, `(IsActive,CreatedBy)`, `(IsActive,SortOrder,CreatedAt)`, `AgentCode`(UQ)

#### ApiKey (외부 인증)
- `EncryptedKey nvarchar(500)` — AES-CBC 암호화, **고정 IV(zero) + JWT SecretKey 재사용** 🔴
- `AgentId int? FK` — 키를 특정 Agent에만 묶을 수 있음
- `ServiceCode nvarchar(50)` — **FK가 아닌 단순 문자열** (ApiServices에 없는 임의 값 허용)
- `Scopes nvarchar(200)` — `chat,stream,info,usage` 콤마 분리
- `AllowedIps nvarchar(2000)` — 콤마 분리, CIDR 미지원
- `RateLimitPerMinute/Day int?`, `UsageCount int`
- **인덱스 누락**: lookup용 `KeyHash` 컬럼 없음 → 매 인증 시 풀스캔 + AES 복호화 비교 (O(N)) 🔴

#### DocumentChunk (RAG)
- `Embedding nvarchar(MAX)` — `float[1536]` JSON 직렬화
- 검색은 C# 메모리 코사인 유사도 (SIMD `System.Numerics.Vector<float>`)
- **벡터 인덱스 미사용** — 수만 청크 이상에서 OOM 위험 ⚠️

#### ChatConversation (비정규화 캐시 다수)
- `MessageCount int`, `TotalTokens int`, `TotalCost decimal(10,4)`, `LastMessageAt`
- 동기화 메커니즘: 응용 코드만 (DB 트리거 없음 → drift 위험)

### 4.3 ER 그룹 다이어그램

```
인증/사용자                    에이전트/LLM
Users ──< UserRoles >── Roles  ApiServices ──< ApiServiceModels
  │                              │
  │< UserSessions               │
  │< UserPreferences            ▼
  │< TeamMembers >── Teams      Agents ──< AgentDocuments >── KnowledgeBaseDocuments
  │                              │                              │
  ▼                              ▼                              ▼
ChatConversations ──< ChatMessages           DocumentChunks (Embedding nvarchar(MAX))
  │              ──< ApiUsages
  │
  └── ApiQuotas (User × Service)

워크플로우                              도구
Workflows ──< WorkflowNodes              Tools ──< ToolVersions
   │       ──< WorkflowExecutions               ──< ToolExecutions
                ──< WorkflowNodeExecutions

프레젠테이션                            보안/모니터링
Presentations ──< PresentationSlides    ApiKeys (User, Agent?)
PresentationTemplates                   BannedWords (Agent? NULL=전역)
                                        PiiDetectionLogs
                                        ActivityLogs (channel batch)
```

### 4.4 식별자 정책
- **PK**: 32개 int identity, 5개 bigint identity (시계열: `ApiUsage`, `ChatMessage`, `DocumentChunk`, `WorkflowExecution`, `WorkflowNodeExecution`, `ToolExecution`, `ActivityLog`)
- **외부 노출 코드**: `Agent.AgentCode`, `ApiService.ServiceCode`, `Tool.ToolCode`, `Workflow.WorkflowCode`, `Role.RoleName` 모두 nvarchar(50) UNIQUE
- **GUID 사용 1곳**: `PresentationSlide.SlideId nvarchar(50) = Guid.NewGuid().ToString()`
- 순차 ID 노출 → IDOR 가능성, 컨트롤러 인가 검증 필수

---

## 5. 백엔드 서비스 레이어

### 5.1 서비스 카탈로그 (30+개)

| 서비스 | LOC | 책임 |
|---|---|---|
| **AiProxyService** | 3,749 | 8종 채팅 + 5종 이미지 프로바이더 통합, 429 키 쿨다운, RAG 컨텍스트 주입, Tavily 웹/Deep Research |
| **ChatService** | 1,049 | 대화 CRUD, AI 호출 오케스트레이션, 응답 캐싱(SHA256+Redis 5분), Fallback 모델 자동 전환 |
| **PresentationService** | 1,394 | AI 슬라이드 콘텐츠 생성, 이미지 생성 통합, DB 저장 |
| **PptxGenerationService** | 1,175 | OpenXML 기반 PPTX 직접 생성, 9종 레이아웃 |
| **PiiDetectionService** | 418 | 8종 한국 PII 감지 (정규식) |
| **WorkflowEngine** | 362 | Kahn 위상 정렬, 레벨별 병렬 실행 |
| **ApiKeyService** | 347 | API 키 CRUD, AES 암호화 |
| **FileService** | 336 | 파일 업로드, 확장자/크기 검증, GUID 파일명 |
| **BannedWordService** | 285 | 전역/에이전트별 금칙어 (5분 캐시) |
| **WorkflowExecutionService** | 259 | 실행 기록, 동기/비동기 분기, 노드별 결과 저장 |
| **AuthService** | 256 | BCrypt 검증, UserSession, RefreshToken, 비밀번호 재설정 |
| **QuotaService** | 219 | 월/일/비용 한도 체크, RecordUsage |
| **DocumentIndexingService** | 211 | 문서 청크 분할(1000자/200 오버랩), 임베딩 생성 |
| **EmbeddingService** | 193 | OpenAI Embeddings 호출, 배치 100개, SIMD 코사인 |
| **RagService** | 179 | 쿼리 임베딩 → 코사인 검색 → Top-K (캐시 2단계) |
| **PptxTemplateParser** | 178 | PPTX 템플릿 레이아웃/색상 추출 |
| **ApiKeyPoolService** | 168 | 7종 프로바이더 다중 키 풀, 라운드로빈, 60초 쿨다운 |
| **ScriptToolExecutor** | 161 | Python/JS 외부 프로세스 실행 |
| **CachingService** | 149 | IDistributedCache 추상화 (Redis) |
| **CSharpToolExecutor** | 113 | Roslyn 동적 컴파일 (30s 타임아웃) |
| **ApiKeyAuthService** | 108 | 외부 API Key 검증 (O(N) 복호화) |
| **JwtService** | 88 | HS256 서명, ClockSkew=Zero |
| **EmailService** | 84 | SmtpClient SSL 분기 |
| **TextExtractionService** | 54 | URL HTML → 텍스트 (정규식) |
| **NotificationService** | 53 | SignalR 푸시 (다수 stub) |
| **ApiKeyRateLimiter** | 67 | MemoryCache 슬라이딩 윈도우 |
| 기타 | | KnowledgeBaseService, AgentService, AnalyticsService, ActivityLogService, ToolService, ToolExecutionService, ApiToolExecutor, FileParsingService, SystemSettingsService, TeamService, UserService, IPiiDetectionService 외 |

### 5.2 주요 서비스 핵심 알고리즘

#### AiProxyService — API Key 획득 우선순위
```
GetApiKey(provider, configPath):
  1순위: ApiKeyPoolService.GetNextKey(provider)   ← 라운드로빈
  2순위: Configuration[configPath]                 ← 단일 키 폴백
```

**429 처리**: 응답 StatusCode가 429이면 `ApiKeyPool.MarkAsCoolingDown(provider, key, 60s)` 후 `HttpRequestException(429)` re-throw → ChatService가 catch하여 fallback 모델로 재시도.

**추론 모델 분기** (`o1/o3/gpt-5`): `max_completion_tokens` 사용, temperature 미전송.

#### ChatService — Fallback Chain
```csharp
fallback = request.FallbackModel ?? GetDefaultFallbackModel(model);
```
매핑 (12종):
- `gpt-4o → gpt-4o-mini`, `gpt-4-turbo → gpt-4o-mini`, `gpt-4 → gpt-3.5-turbo`
- `o1/o1-mini/o3-mini → gpt-4o-mini`
- `claude-opus-4-6 → claude-sonnet-4-6 → claude-haiku-4-5 → gpt-4o-mini` (cross-provider)
- `mistral-large-latest → mistral-small-latest`
- `gemini-2.0-pro → gemini-2.0-flash`

**1단계 fallback만 지원** — fallback 모델도 실패 시 예외 전파.

#### ChatService — 응답 캐싱 조건
```
!EnableRag && !EnableWebSearch && !EnableDeepResearch
&& 모든 메시지가 텍스트(Contents 없음)
&& AgentId 존재
```
캐시 키: `chat:resp:{agentId}:{model}:{sha256(messages)[..16]}`, TTL 5분.

#### ApiKeyPoolService
- Singleton, `lock(_lock)`으로 보호된 라운드로빈
- 키별 `CooldownUntil DateTime` 비교로 사용 가능 여부 판정
- 전체 쿨다운 시 가장 빨리 복귀할 키 반환

#### RagService — 캐시 2단계
1. `embedding:{hash16}` (1시간) — 쿼리 임베딩 벡터
2. `rag:{agentId}:{userId}:{hash16}` (10분) — 검색 결과 전체

필터 우선순위: `documentIds → agentId → userId`

### 5.3 외부 LLM 호출 흐름 (요약)
```
ChatController/AgentsController/OpenAICompatController
    ↓
ChatService.SendMessageAsync (또는 SendDirectMessageAsync)
    ↓ Quota → BannedWord → PII 검사
    ↓ DB 메시지 저장 + 30개 history 빌드
    ↓
AiProxyService.SendChatMessageAsync (RAG 활성화 시 RagService 선행)
    ↓ provider switch (openai/claude/gemini/...)
    ↓ ApiKeyPool.GetNextKey (라운드로빈)
    ↓ HttpClient POST + 429 → MarkAsCoolingDown
    ↓
External LLM API
```

---

## 6. API 설계

### 6.1 컨트롤러 카탈로그 (28개)

| Controller | Route | 인증 | 비고 |
|---|---|---|---|
| AuthController | `/api/auth` | Anonymous(login/register/forgot/reset) + Authorize(logout) | JWT 발급 |
| AgentsController | `/api/agents` | JWT + ApiKey + 게스트 혼합 | 1080 LOC, 7개 서비스 주입, QR 코드 생성 |
| ChatController | `/api/chat` | JWT | SignalR 트리거 (`ReceiveMessage`) |
| OpenAICompatController | `/v1` | ApiKeyAuthorize + ip-openai | OpenAI 호환, snake_case |
| AnalyticsController | `/api/analytics` | JWT + Admin 일부 | dashboard/usage/cost/top-users/agents/{id}/stats |
| KnowledgeBaseController | `/api/knowledgebase` | JWT | RAG 인덱싱/재인덱싱 트리거 |
| ToolBuilderController | `/api/toolbuilder` | JWT | Roslyn compile/validate/test |
| ToolsController | `/api/tools` | JWT | CRUD + versions + execute |
| WorkflowsController | `/api/workflows` | JWT | CRUD + execute + cancel |
| ApiKeysController | `/api/apikeys` | JWT | CRUD + reveal |
| QuotaController | `/api/quota` | JWT + Admin 일부 | my-quotas / 설정 |
| UsersController | `/api/users` | JWT + Admin 일부 | me / CRUD |
| TeamsController | `/api/teams` | Admin | 팀 멤버 관리 |
| BannedWordsController | `/api/bannedwords` | JWT + Admin | CRUD |
| PiiDetectionLogsController | `/api/piidetectionlogs` | Admin | 조회 + statistics |
| PresentationController | `/api/presentations` | JWT | 13개 엔드포인트, PPTX/PDF 내보내기 |
| PresentationTemplateController | `/api/presentation-templates` | JWT | upload(멀티파트) |
| ImageGenerationController | `/api/image-generation` | JWT | DALL-E/Imagen/Flux2 |
| FilesController | `/api/files` | JWT | upload/download/delete (와일드카드 라우트 ⚠️) |
| ActivityLogController | `/api/activitylog` | Admin | 조회 |
| FaqsController | `/api/faqs` | Anonymous(GET) + Admin(변경) | |
| TutorialsController | `/api/tutorials` | Anonymous(GET) + Admin(변경) | |
| ExamplePromptsController | `/api/exampleprompts` | Anonymous(GET) + Admin(변경) | |
| UserPreferencesController | `/api/userpreferences` | JWT | KV CRUD |
| ApiServicesController | `/api/apiservices` | JWT | 서비스/모델 조회 + connection-status |
| SystemHealthController | `/api/systemhealth` | Admin | diagnostics |
| SystemSettingsController | `/api/systemsettings` | Admin | pii-protection 설정 |
| DatabaseBackupController | `/api/databasebackup` | Admin | backup/restore/settings |

### 6.2 OpenAI 호환 API (`/v1/*`)

```
GET  /v1/models                  → Agent 목록을 OpenAI 모델 형식으로 반환
GET  /v1/models/{model}          → AgentCode로 Agent 메타 조회
POST /v1/chat/completions        → 채팅 (stream:true → SSE, false → JSON)
                                   ⚠️ stream이 가짜 SSE — 전체 응답 받고 단어 단위 분할
```

### 6.3 외부 Agent API (Postman 컬렉션 정의)
```
X-API-Key: ak-{base64-32bytes}  또는  Authorization: Bearer ak-{...}

POST /api/agents/{agentId}/chat              → 단일 메시지 (스코프: chat)
POST /api/agents/code/{code}/chat            → AgentCode 기반
POST /api/agents/{agentId}/chat/stream       → SSE 스트림 (스코프: stream)
GET  /api/agents/{agentId}/info              → 메타 (스코프: info)
GET  /api/agents/{agentId}/usage             → 사용량 (스코프: usage)
```

**스코프 동작**: 빈 스코프(`""`) = 모든 권한, 콤마 분리 시 해당만 허용.

### 6.4 게스트 공개 API (`ip-guest`, 20/min)
```
GET  /api/agents/public/{code}/info          → 메타 (시스템 프롬프트 미포함)
POST /api/agents/public/{code}/chat          → 게스트 채팅 (DB 미저장)
POST /api/agents/public/{code}/stream        → 게스트 스트림
GET  /api/agents/public/{code}/qr?size=400   → QR PNG
```
조건: `IsPublic && IsActive && AllowGuestChat`. iframe 임베드 시 `AllowedEmbedDomains` 화이트리스트 검증.

### 6.5 표준 응답 형식
- 성공: `200 OK` + DTO
- 검증 실패: `400 + ErrorResponseDto { message, errorCode, details }` (자동 변환)
- 인증 실패: `401`
- 권한 부족: `403`
- 미존재: `404`
- Rate Limit 초과: `429 + Retry-After: 60` + 한국어 메시지
- 서버 오류: `500 + ErrorResponseDto`

오류 코드: `VALIDATION_ERROR`, `BANNED_WORD_DETECTED`, `PII_DETECTED`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `INTERNAL_SERVER_ERROR`

---

## 7. 인증·인가 체계

### 7.1 JWT (`/api/*`)
- 발급: `POST /api/auth/login` → BCrypt 검증 → `IJwtService.GenerateToken(userId, email, roles)`
- 알고리즘: HS256, `ClockSkew = TimeSpan.Zero` (1초 시계 차이로 401 가능)
- 만료: 60분 (configurable `JwtSettings:ExpirationInMinutes`)
- RefreshToken: 32바이트 `RandomNumberGenerator` Base64, 7일 유효, `UserSession` 저장
- 클레임: `NameIdentifier(userId)`, `Email`, `Jti(GUID)`, 다중 `Role`
- 자동 갱신: 프론트 axios 인터셉터에서 401 → `POST /auth/refresh` → 원 요청 재시도 (무한루프 방어 없음 ⚠️)

### 7.2 API Key (`/v1/*`, Agent 외부 API)
```
[ApiKeyAuthorize("scope1", "scope2")]
    ↓ X-API-Key 또는 Authorization: Bearer 추출
    ↓ ApiKeyAuthService.ValidateApiKeyAsync (sync over async ⚠️)
       ↓ 모든 활성 ApiKey 조회 → 각각 AES 복호화 후 평문 비교 (O(N)) 🔴
       ↓ AES IV = new byte[16] (고정 zero IV) 🔴
       ↓ 키 = SHA-256(JwtSecretKey) (PBKDF2 미적용) 🔴
    ↓ AllowedIps 정확 일치 검사 (CIDR 미지원)
    ↓ ApiKeyRateLimiter.CheckAndIncrement (분/일 슬라이딩, MemoryCache, race 가능 ⚠️)
    ↓ Scope 검사 (빈 값 = 모든 권한)
    ↓ ClaimsPrincipal 교체 (AuthenticationType="ApiKey")
```

### 7.3 게스트 (Anonymous + Rate Limit)
- `[AllowAnonymous] + [EnableRateLimiting("ip-guest")]`
- IP당 20/min만으로 보호
- `Agent.IsPublic && AllowGuestChat` + 임베드 도메인 화이트리스트 추가 검증

### 7.4 Hangfire Dashboard (`/hangfire`)
- `HangfireAuthorizationFilter`: 인증 + Role IN ('Admin', 'SuperAdmin')
- ⚠️ 브라우저 정적 페이지 로드 시 JWT를 어떻게 전달하는지 불명확 (쿠키 인증 미설정)

### 7.5 RBAC 구조
- 역할: `Admin`, `Developer`, `User` (DatabaseInitializer 시드)
- 사용자취급설명서 명세: `SuperAdmin / Admin / User` (실제 운영) — 코드와 차이 검토 필요
- 부여: `[Authorize(Roles = "Admin")]` 컨트롤러/액션 부착
- **프론트엔드 라우터 가드는 역할 미체크** — Admin 전용 페이지도 URL 직타입 시 로드되어 백엔드 401/403에 의존

---

## 8. 핵심 데이터 흐름 (시퀀스)

### 8.1 일반 채팅
```
User → POST /api/chat/conversations/{id}/messages (JWT)
  ChatController.SendMessage [Authorize]
    ChatService.SendMessageAsync(convId, request, userId)
      QuotaService.CheckQuotaAsync (월/일/비용)
      BannedWordService.CheckBannedWordsAsync (5분 캐시)
      PiiDetectionService.DetectPiiAsync (Block: 예외 / Mask: 메시지 교체)
      DbContext.ChatMessages.Add(user) + SaveChanges
      Load last 30 msgs → Build ChatMessageRequestDto
      AiProxyService.SendChatMessageAsync(serviceId, model, request)
        → provider switch (openai/claude/gemini/...)
        → ApiKeyPool.GetNextKey
        → HttpClient POST
        → 429: MarkAsCoolingDown + throw HttpRequestException
      [catch 429/500/503]
        → fallback = GetDefaultFallbackModel(model)
        → AiProxyService.SendChatMessageAsync(fallback model)
      AiProxyService.CalculateCostAsync
      Save assistant msg + ApiUsage + Conversation 갱신
      QuotaService.RecordUsageAsync (CurrentUsage++ ⚠️ 토큰 미반영)
      SaveChanges (트랜잭션)
    ChatHub.Clients.Group($"conversation_{id}").SendAsync("ReceiveMessage")
  → 200 ChatMessageDto
```

### 8.2 RAG 활성화 (위 흐름의 AiProxy 내부 분기)
```
AiProxyService (request.EnableRag=true)
  RagService.RetrieveAsync(query, topK, userId, agentId, documentIds)
    queryHash = SHA256(query)[..16]
    cache.Get("rag:{agentId}:{userId}:{hash}") → hit 시 즉시 반환
    cache.Get("embedding:{hash}") OR EmbeddingService.GetEmbeddingAsync (1h 캐시)
    DbContext.DocumentChunks.AsNoTracking().ToListAsync()  ⚠️ 전체 청크 메모리 로드
    for each chunk:
      embedding = JsonDeserialize(chunk.Embedding)
      similarity = SIMD CosineSimilarity(query, chunk)
    Top-K = OrderByDescending.Take(topK)
    cache.Set("rag:...", 10min)
  Append "[지식 기반 문서 검색 결과]\n출처 1: ... (유사도: 0.92)" to system message (800자 절단)
  → CallOpenAi/CallClaude/...
```

### 8.3 OpenAI 호환 API
```
External Client (OpenAI SDK / Cursor / LangChain)
  POST /v1/chat/completions  Authorization: Bearer ak-...
  [ApiKeyAuthorize] → ApiKeyAuthService.ValidateApiKeyAsync (O(N) AES 복호화)
  [EnableRateLimiting("ip-openai")]
  OpenAICompatController.ChatCompletions
    Validate model (= AgentCode), Agent 권한 검증
    BannedWord + PII 검사
    Build DirectSendMessageRequestDto (system 메시지 제외, 마지막 user는 마스킹)
    if request.Stream:
      Response.ContentType = "text/event-stream"
      ChatService.SendDirectMessageAsync (전체 응답 한 번에 받음 ⚠️)
      for each word in Content.Split(' '): WriteChunk + Task.Delay(15)
      Write "data: [DONE]"
    else:
      ChatService.SendDirectMessageAsync
      Map → OpenAIChatCompletionResponse (snake_case)
      usage = (totalTokens, completion=0.65*total, prompt=0.35*total)  ⚠️ 추정값
```

### 8.4 429 Fallback
```
ChatService (request.Model="gpt-4o")
  try AiProxyService.SendChatMessageAsync("gpt-4o")
    apiKey₁ = ApiKeyPool.GetNextKey("openai")
    POST → 429
    ApiKeyPool.MarkAsCoolingDown("openai", apiKey₁, 60s)
    throw HttpRequestException(429)
  catch (StatusCode in 429/500/503):
    fallbackModel = request.FallbackModel ?? "gpt-4o-mini"
    AiProxyService.SendChatMessageAsync("gpt-4o-mini")
      apiKey₂ = ApiKeyPool.GetNextKey("openai")  // key₁ 쿨다운 → 제외
      POST → 200 OK
  return aiResponse (model="gpt-4o-mini" 추적)
```

### 8.5 워크플로우 실행
```
User → POST /api/workflows/{id}/execute (JWT)
  WorkflowsController.Execute
    WorkflowExecutionService.ExecuteWorkflowAsync(id, request, userId)
      Insert WorkflowExecution(Status=Running) + SaveChanges
      if !waitForCompletion:
        _ = Task.Run(...)  ⚠️ scoped DbContext 캡처 → 응답 후 disposed
        return Running
      WorkflowEngine.ExecuteAsync
        Workflows.Include(WorkflowNodes).First(IsActive)
        DetermineExecutionOrder (Kahn 위상 정렬)
          parse node.Connections JSON {sources, targets}
          inDegree dict + adjacency
          BFS by levels → List<List<Node>>
        nodeData = { 0: inputData }
        for each level: Task.WhenAll over nodes
          ExecuteNodeAsync switch:
            "agent": ⚠️ stub: $"Agent {name} processed: {message}"
            "llm":   AiProxyService.SendChatMessageAsync
            "tool":  ToolExecutionService.ExecuteToolAsync (Roslyn/Python/JS/API 분기)
            "condition":     ⚠️ stub: return inputData
            "datatransform": ⚠️ stub: return inputData
        result.OutputData = nodeData[lastNode by SortOrder DESC]
      Update WorkflowExecution + Insert WorkflowNodeExecution × N
      SaveChanges
  → 200 WorkflowExecutionDto
```

---

## 9. 프론트엔드 아키텍처

### 9.1 부팅 흐름 (`src/main.ts`)
```
createApp(App) → Pinia → Router → i18n → mount('#app')
```
글로벌 CSS: `bootstrap.min.css`, `bootstrap-icons.css`, `bootstrap.bundle.min.js`(JS 번들), `utilities.css`, `App.vue:styles.css + aiuiux-theme.css`.

**글로벌 컴포넌트/디렉티브: 등록 없음.**

### 9.2 라우터 구조 (`src/router/index.ts`)
- **공개 라우트 (8)**: `/login`, `/landing`, `/forgot-password`, `/reset-password`, `/terms`, `/privacy`, `/chatbot/:code`, `/embed/:code`
- **인증 단독**: `/agent-test/:code`
- **MainLayout 자식 (30+)**: Dashboard, Users, Agents, AgentChat, AgentMultiChat, AgentBuilder, Quota, Analytics, Settings, Playground, AgentMarketplace, AgentTemplates, AuditLog, CostAnalysis, Help, KnowledgeBase, Reports, UsageHistory, ApiKeys, BannedWords, PiiProtection, Team, SystemHealth, DatabaseBackup, PresentationTemplateManagement, ImageGeneration, QuickImageGeneration, PresentationBuilder, Tools, ToolBuilder, Workflows, WorkflowBuilder, WorkflowExecutionMonitor

#### 인증 가드 (`router.beforeEach`)
1. `/` + 미로그인 → `/landing`
2. `requiresAuth && !token` → `/login?redirect=...`
3. 로그인된 상태에서 `/login`/`/landing` → `/`

⚠️ **역할 가드 미구현** — Admin 전용도 페이지 로드 후 백엔드 401/403 의존.

### 9.3 Pinia 스토어 — `useAuthStore` 1개
```
state:    token, refreshToken, user, isAuthenticated
actions:  login, logout, loadUser
영속화:    token, refreshToken만 localStorage (user는 매번 GET /users/me)
```
**모든 view 상태는 컴포넌트 로컬 ref**.

### 9.4 API 서비스 (`src/services/api.ts`)
- `baseURL: '/api'` (환경변수 미사용)
- Vite proxy: `/api → http://localhost:5000`, `/hubs → ws://localhost:5000`
- Request 인터셉터: `Authorization: Bearer {token}` 부착
- Response 인터셉터:
  - Blob 401 응답 → text → JSON 파싱
  - `/auth/login` 401은 throw (로그인 실패 메시지 표시)
  - 그 외 401 → `/auth/refresh` → 원 요청 재시도 (무한루프 방어 없음)
  - 실패 시 `window.location.href = '/login'`

⚠️ **도메인별 서비스 파일 없음** — 각 view가 직접 호출.

### 9.5 거대 view 파일 (재사용 컴포넌트 추출 미적용)
- `AgentChat.vue` — **5,286줄** (단일 파일)
- `AgentMultiChat.vue` — 4,031줄
- `AgentSelect.vue` — 1,202줄
- `AgentBuilder.vue` — 1,182줄
- `PresentationBuilder.vue` — 1,830줄

**`src/components/` 디렉토리 부재** — 재사용 패턴 미정착.

### 9.6 SignalR — **미사용**
- `@microsoft/signalr` 패키지 설치되어 있으나 `src/`에 import 0건
- `WorkflowExecutionMonitor.vue`도 폴링/SignalR 없이 mount 시 1회 호출만
- 백엔드 Hub는 노출되어 있지만 프론트는 활용하지 않음 → **dead dependency**

### 9.7 SSE 스트리밍 — **미사용**
- 백엔드 `/v1/chat/completions` (stream:true), `/api/agents/{id}/chat/stream` 존재
- 프론트 `AgentChat`은 `stream: false` 명시, `EventSource`/`fetchEventSource` 0건
- 응답은 단일 axios POST → `response.data.content`

### 9.8 raw axios 사용 (인증 토큰 미부착 버그 가능성)
- 의도적: `AgentEmbed`, `AgentPublicChat` (게스트)
- **잠재적 버그**: `ToolList`, `ToolBuilder`, `WorkflowList`, `WorkflowExecutionMonitor`

### 9.9 Vue Flow (워크플로우 에디터)
- 단일 사용처: `WorkflowBuilder.vue`
- 노드 8종: Start, Agent, LLM, Tool, Condition, Loop, DataTransform, Output
- 드래그 → drop → `useVueFlow().project()` (deprecated, `screenToFlowCoordinate` 권장)
- visual ↔ code 토글 시 JSON 직렬화/역직렬화

### 9.10 Chart.js — **사용 1곳뿐** (`SystemHealth.vue`)
- Analytics, CostAnalysis, Dashboard는 progress bar만 사용
- `vue-chartjs`는 설치되었으나 사용 0건 (dead dependency)

### 9.11 i18n
- vue-i18n v9 Composition Mode (`legacy: false`)
- `ko` + `en` 543줄/언어
- 초기 locale: localStorage → navigator.language → fallback `en`
- ⚠️ `quota` 키가 ko/en JSON에 중복 정의됨 (후순위가 덮음)

### 9.12 빌드 파이프라인
```
npm run dev          → vite (포트 5173)
npm run build        → vite build (⚠️ TypeScript 미검사)
npm run build:check  → vue-tsc && vite build (CI 권장)
```
- manualChunks: `vue-vendor`, `chart-vendor`, `axios-vendor`
- `tsconfig.json`: `noUnusedLocals/Parameters: false` (느슨함)

### 9.13 코드 품질 관찰
- `any` 타입 38개 파일 / 총 171건 (AgentChat 26건, PresentationBuilder 17건)
- `alert(...)` 다수 (디자인 시스템 분리)
- `Login.vue`에 평문 dev 자격증명 하드코딩 (`admin@example.com / Admin123!`, isLocalhost 분기)
- `Playground.vue` 비교 모드 두 번째 모델 호출 mock (실제 미구현)
- `Playground.vue` `localStorage('experiment_${Date.now()}')` 무제한 누적

---

## 10. RAG 파이프라인

### 10.1 흐름
```
1. 문서 등록  → KB.upload (PDF/Word/Excel/CSV/HWP)
2. 인덱싱     → DocumentIndexingService
                 ├─ FileParsingService → 텍스트 추출 (LibreOffice 의존)
                 ├─ SplitIntoChunks(1000자, 200자 오버랩)
                 ├─ EmbeddingService.GetEmbeddingsAsync (배치 100)
                 └─ DocumentChunks INSERT (Embedding nvarchar(MAX) JSON)
3. 채팅 시 RAG 활성화 → AiProxyService → RagService.RetrieveAsync
4. 결과 → system 메시지에 컨텍스트 주입 (각 청크 800자 절단)
```

### 10.2 설정
| 항목 | 값 |
|---|---|
| 임베딩 모델 | `text-embedding-3-small` |
| 차원 | 1,536 |
| 청크 크기 | 1,000자 |
| 청크 오버랩 | 200자 (⚠️ 한국어 환경에서 실제 ~0자 적용 — 버그) |
| 기본 Top-K | 5 (최대 20) |
| 유사도 임계값 | 0.7 |
| 배치 크기 | 100 |

### 10.3 캐싱
| 키 | TTL | 내용 |
|---|---|---|
| `embedding:{쿼리해시16}` | 1시간 | 쿼리 임베딩 벡터 |
| `rag:{agentId}:{userId}:{쿼리해시16}` | 10분 | 검색 결과 전체 |
| `quota:user:{}:service:{}` | 30분 | 할당량 정보 |

응답 캐시 제외 조건: RAG / 웹검색 / 멀티모달.

### 10.4 한계
- **벡터 인덱스 미사용** — 모든 청크를 메모리에 로드 후 SIMD 코사인 → 100K 청크 × 1536 float ≈ 1.8GB OOM 위험
- **권장 개선**: SQL Server 2025 `vector(1536)` 타입, 또는 외부 벡터 DB(Qdrant/pgvector/Pinecone)

---

## 11. 워크플로우 엔진

### 11.1 노드 타입 (8종, Frontend Vue Flow)
Start, Agent, LLM, Tool, Condition, Loop, DataTransform, Output

### 11.2 실행 알고리즘 (`WorkflowEngine.cs`)
1. `Workflows.Include(WorkflowNodes).First(IsActive)`
2. `DetermineExecutionOrder` — Kahn 위상 정렬
   - Parse `node.Connections JSON` `{sources:[], targets:[]}`
   - inDegree dict + adjacency
   - BFS levels → `List<List<WorkflowNode>>`
3. for each level: `Task.WhenAll` 병렬
4. 각 노드: `ExecuteNodeAsync` switch (NodeType)

### 11.3 동기/비동기 분기 (`WorkflowExecutionService.cs`)
- `waitForCompletion: true` → 동기, 결과 대기
- `waitForCompletion: false` → `_ = Task.Run(...)` ⚠️ **scoped DbContext 캡처** → 응답 후 disposed → `ObjectDisposedException`

### 11.4 미구현/스텁
- ❌ `agent` 노드: `return $"Agent {name} processed: {message}"` (가짜)
- ❌ `condition` 노드: `return inputData` (NO-OP)
- ❌ `datatransform` 노드: `return inputData` (NO-OP)
- ❌ `loop` 노드: 정의되어 있으나 실행 분기 없음
- ❌ `CancelExecutionAsync`: DB 행만 "Cancelled" 변경 — 실제 Task 취소 미작동

---

## 12. 도구 시스템

### 12.1 3종 Executor (`ToolExecutionService.cs` switch)
| Tool Type | Executor | 백엔드 |
|---|---|---|
| `csharp` | `CSharpToolExecutor` | Roslyn 동적 컴파일 (in-process) |
| `python` / `javascript` | `ScriptToolExecutor` | 외부 프로세스 (`Process.Start`) |
| `api` | `ApiToolExecutor` | HttpClient 임의 URL 호출 |

### 12.2 보안 위험 🔴
- **CSharpToolExecutor**: 코드 인젝션 가능 (`var fullCode = $@"... {code} ..."` wrapper escape), 어셈블리는 `AssemblyLoadContext.Default`에 영구 로드 → 메모리 누수
- **ScriptToolExecutor**: 임시 input 파일 finally에서 새 Guid 생성 버그 → 파일 영구 누수, 코드 검증 없음
- **ApiToolExecutor**: SSRF 미차단 (`localhost`, `169.254.169.254` 호출 가능)

### 12.3 ToolBuilder UI
- 평범한 `<textarea class="form-control font-monospace">` (Monaco/CodeMirror 미사용)
- raw axios 사용 → 인증 토큰 미부착 가능성 ⚠️

---

## 13. 프레젠테이션 빌더

### 13.1 생성 흐름
```
사용자 입력 (topic | paste | import) → PresentationService.GenerateAsync
  ├─ topic: 주제 + 슬라이드 수
  ├─ paste: 텍스트 → AI 요약 → 슬라이드
  └─ import: URL → TextExtractionService → AI 요약 → 슬라이드

→ AiProxyService (영/한 시스템 프롬프트, 정확한 슬라이드 수 + JSON 강제)
→ 슬라이드별 이미지 생성 (순차 ⚠️ 10장 = 10번 직렬 호출)
→ DB 저장 (Presentation + PresentationSlides)
→ PptxGenerationService.GeneratePptxAsync (OpenXML)
   - 9종 레이아웃: title-only, title-content, two-column, comparison, quote, thank-you, ...
   - Markdown(`**bold**`, `*italic*`)
   - Table OOXML A.Table
   - 빈 텍스트는 `​` zero-width space (PowerPoint 복구 메시지 회피)
→ PPTX 또는 PDF (LibreOffice headless 변환)
   미설치 시: PPTX 폴백 + `X-Pdf-Fallback-Pptx: true` 헤더
```

### 13.2 8종 레이아웃, 4가지 스타일
스타일: 비즈니스/교육/마케팅/창의적  
폰트: 맑은 고딕(기본), Noto Sans KR(Education=나눔고딕), Pretendard(Minimal)  
사이즈: 4:3, 16:9, 16:10

### 13.3 알려진 이슈
- `Presentation.Slides nvarchar(MAX)` 레거시 컬럼 + `PresentationSlides` 정규화 테이블 **이중 저장**
- `PresentationBuilder.vue` 1,830줄 단일 파일 (분리 필요)
- JSON 잘림 대응: `maxContentPerSlide=20,000자`, JSON 500K 초과 시 400K로 절단

### 13.4 미구현 로드맵
- Phase 1: AI 이미지 자동 삽입 (DALL-E 슬라이드별 호출)
- Phase 2: 테마 원클릭 전환, Chart OOXML 렌더링
- Phase 3: 슬라이드 재생성, 드래그 순서 변경, Find & Replace
- Phase 4: 공개 링크 공유, 버전 이력, 실시간 협업

---

## 14. 인프라·배포·운영

### 14.1 배포 환경
| 항목 | 값 |
|---|---|
| OS | Windows Server (IIS) |
| 도메인 | `agenthub.idino.co.kr` (HTTPS 강제) |
| 호스팅 모델 | InProcess (`AspNetCoreModuleV2`) |
| 게시 경로 | `/c/publish/AIAgentManagement/` |
| stdout 로그 | `/logs/stdout_*.log` |
| MSDeploy | `EnableMsDeployAppOffline=true`, retry 10회/1초 |

### 14.2 Hangfire 작업
| Job ID | Cron | 본체 | 주의 |
|---|---|---|---|
| `daily-quota-reset` | UTC 자정 | `QuotaResetJob.ResetDailyQuotas` | ⚠️ Daily는 Usage 0 리셋 안 함 (LastResetAt만) |
| `monthly-quota-reset` | 매월 1일 | `QuotaResetJob.ResetMonthlyQuotas` | CurrentUsage=0, CurrentCost=0 |
| `daily-report` | UTC 1AM | `ReportGenerationJob.GenerateDailyReport` | ⚠️ 저장 미구현 (TODO 주석) |
| `monthly-report` | 매월 1일 2AM | `GenerateMonthlyReport` | ⚠️ 저장 미구현 |

모두 `[AutomaticRetry(Attempts = 3)]`.

### 14.3 ActivityLog 비동기 처리
```
Middleware (Producer) → Channel<ActivityLog>(capacity 1000, DropOldest)
    → ActivityLogWorker (IHostedService Consumer)
       BatchSize=50, FlushInterval=3s
       IServiceScopeFactory.CreateAsyncScope → DbContext → AddRange + SaveChanges
```

### 14.4 Rate Limiter 정책
| 정책 | 한도 | 키 | 적용처 |
|---|---|---|---|
| `ip-guest` | 20/min | RemoteIpAddress | `/api/agents/public/{code}/*` 4곳 |
| `ip-openai` | 30/min | RemoteIpAddress | `/v1/*` (OpenAICompatController 클래스 레벨) |
| `per-user` | 60/min | userId or IP | ⚠️ **정의만, 어디에도 부착 안 됨** (데드 코드) |

거절: `429 + Retry-After: 60` + 한국어 메시지

### 14.5 Redis 폴백
- 연결 실패 시 `Program.cs:128-158` `try/catch`로 `MemoryDistributedCache` 자동 전환
- 영향: RAG/임베딩/할당량 캐싱이 인-메모리로 전환, 다중 인스턴스 캐시 공유 불가

### 14.6 보안 헤더 (`SecurityHeadersMiddleware.cs`)
CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy 7종.

### 14.7 LibreOffice 의존
- 경로: `C:\Program Files\LibreOffice\program\soffice.exe`
- 용도: HWP/HWPX → PDF 변환 (RAG 한국어 공공 문서), PPTX → PDF (프레젠테이션 내보내기)
- 미설치 시: PPTX 폴백 (HWP RAG는 실패)

---

## 15. 데이터베이스 운영

### 15.1 Connection (개발/프로덕션 동일)
```
Server=192.168.10.159
Database=AIAgentManagement
User ID=aiuser
Password=rnehrwhgdk20@^   ⚠️ 평문 노출 (Program.cs:362, appsettings.*.json)
TrustServerCertificate=true
MultipleActiveResultSets=true
CommandTimeout=30s
```

### 15.2 마이그레이션 상태 (🔴 Critical)
- **EF Core 마이그레이션 단 1개**: `20260320012331_AddApiUsagePromptAndIndexes`
- **InitialCreate 마이그레이션 부재** — 35개 테이블의 초기 생성은 `DatabaseInitializer.SeedAsync`의 `EnsureCreatedAsync()`로 처리 (`__EFMigrationsHistory` 테이블 미생성)
- **루트 레거시 SQL 16+개** — `CreateApiKeysTable.sql`, `AddBannedWordsPerformanceIndexes.sql` 등이 EF 도입 이전의 수동 진화 이력
- **Drift 위험 4가지 환경**:
  - (a) 구 EnsureCreated → 모든 SQL 수동 실행
  - (b) 구 EnsureCreated → 일부 SQL 누락
  - (c) 최신 모델 EnsureCreated (EF 인덱스 + ApiUsage.Prompt 포함, 레거시 SQL 추가 인덱스 누락)
  - (d) (a)/(b) 위에 2026-03-20 EF 마이그레이션 적용

**권장**: baseline 마이그레이션 작성 → `Database.MigrateAsync()` 전환

### 15.3 시드 데이터 (`DatabaseInitializer.cs`)
- **Roles**: Admin, Developer, User
- **Users**: `admin@example.com / Admin123!`
- **ApiServices**:
  - Chat 6: chatgpt, claude, cursor, copilot, gemini, mistral
  - Image 5: dalle, gemini-image, imagen4, gen4-image, flux2
  - Video 3: gen4-video, veo, openai-video
- **ApiServiceModels**: 50+ 모델 (gpt-5/o3/o1, claude-opus-4-6, gemini-3.1-pro 등)
- **자가 치유**: admin Status=Active 강제, BCrypt 포맷 위반 시 `Admin123!` 재설정

### 15.4 인덱스 정책 (총 36개)
- 유니크: UserRoles, ApiQuotas, UserPreferences, ApiServices.Code, Agents.Code, UserSessions.Token, SystemSettings.Key, Roles.Name, AgentDocuments, Tools.Code, Workflows.Code, ApiServiceModels(ServiceId,ModelName), TeamMembers(필터드 IsActive=1)
- 성능: ApiUsages 4종(시계열), ChatMessages.ConversationId, ChatConversations(UserId,LastMessageAt), Agents 5종, BannedWords, PiiDetectionLogs 4종

### 15.5 누락된 핵심 인덱스 🔴
- `Users.Email UNIQUE` — 매 로그인 풀스캔
- `ApiKeys.KeyHash UNIQUE` — 매 인증 O(N) 스캔 + AES 복호화
- `ApiKeys(UserId, ServiceCode, IsActive)`
- `ChatConversations(AgentId, LastMessageAt)`
- `PiiDetectionLogs.ConversationId` (FK도 미설정)

### 15.6 Cascade 위험 ⚠️
- `ApiServices → Agents` Cascade — 서비스 삭제 시 모든 Agent 연쇄 삭제
- `Users → Tools/Workflows` Cascade — 관리자 삭제 시 시스템 핵심 자산 소실
- 권장: 핵심 마스터 테이블 `Restrict`로 강등

### 15.7 임베딩 저장
- `DocumentChunks.Embedding nvarchar(MAX)` — JSON `float[1536]`
- 검색: C# 메모리 SIMD 코사인 유사도
- **벡터 인덱스 부재** — 수만 청크 이상 OOM

---

## 16. 알려진 이슈 및 기술 부채

### 16.1 🔴 Critical (보안/데이터 무결성)

| # | 위치 | 문제 | 영향 |
|---|---|---|---|
| C1 | `ApiKeyService.cs:318`, `ApiKeyAuthService.cs:89` | AES-CBC **고정 IV (zero)** | 동일 평문 → 동일 암호문 (deterministic), 패턴 분석 위험 |
| C2 | `ApiKeyService.cs:24` | **JWT SecretKey를 AES 암호화 키로 재사용** | JWT 키 유출 시 모든 API 키 복호화 가능 |
| C3 | `ApiKeyAuthService.cs:34-66` | **O(N) 활성 키 풀스캔 + AES 복호화 비교** | 1,000키면 요청당 1,000회 AES 연산 |
| C4 | `Users.Email` | UNIQUE 인덱스 누락 | 동일 이메일 중복 가입 가능 + 로그인 풀스캔 |
| C5 | `CSharpToolExecutor.cs:27-50, 84` | 코드 인젝션 + `AssemblyLoadContext.Default` 영구 누수 | wrapper escape, 메모리 누수 |
| C6 | `Program.cs:362` | DB 평문 비밀번호 하드코딩 | git 이력 영구 보존, 키 회전 어려움 |
| C7 | EF 마이그레이션 | InitialCreate 부재 + EnsureCreated 사용 | 환경별 스키마 drift |
| C8 | `Hubs/ChatHub.cs`, `NotificationHub.cs` | `[Authorize]` 부재 + `JoinUserNotifications(userId)` 임의 ID 입력 | 다른 사용자 알림 도청 가능 |
| C9 | `OpenAICompatController.cs:138` | 가짜 SSE 스트리밍 (전체 응답 후 단어 분할 + Task.Delay 15ms) | OpenAI SDK 호환성 약함, 사용자 체감 응답 지연 |
| C10 | `appsettings.Development/Production.json` | API Key/SMTP 비밀번호 평문 커밋 | OpenAI/Gemini/Perplexity/Tavily/Gmail 키 노출 |

### 16.2 🟠 High (안정성/확장성)

| # | 위치 | 문제 |
|---|---|---|
| H1 | `RagService.cs:112` | 모든 청크 메모리 로드 → OOM 위험 (벡터 인덱스 부재) |
| H2 | `WorkflowExecutionService.cs:50` | `Task.Run`이 scoped DbContext 캡처 → `ObjectDisposedException` |
| H3 | `WorkflowEngine.cs:281-361` | Agent/Condition/DataTransform 노드 stub |
| H4 | `ChatService.cs:14` | `static ConcurrentDictionary<string, SemaphoreSlim> _convLocks` 무한 증가 |
| H5 | `AiProxyService.cs:232-252` | Stream API가 키 풀/Cooldown 우회 |
| H6 | `ScriptToolExecutor.cs:148` | 임시 input 파일 finally에서 새 Guid → 영구 누수 |
| H7 | `Program.cs:185` | Hangfire 등록 실패를 빈 catch로 삼킴 → 잡 조용히 멈춤 |
| H8 | `Program.cs:303-319` | `per-user` Rate Limit 정책 정의만, 부착 0건 |
| H9 | `Attributes/ApiKeyAuthorizeAttribute.cs:70` | sync over async (`.GetAwaiter().GetResult()`) → ThreadPool 고갈 |
| H10 | `QuotaService.cs:197` | `RecordUsageAsync`가 token count 무시 (`CurrentUsage++`만) |
| H11 | `EmbeddingService.cs:48` | ApiKeyPool 우회, 단일 키만 사용 |
| H12 | `DocumentIndexingService.cs:180` | 청크 오버랩 `chunkOverlap/20` 한국어 가정 오류 |
| H13 | `AiProxyService.cs` | 3,749 LOC god class — Strategy 패턴 분리 필요 |
| H14 | `ChatService.cs:1023` | Fallback 1단계만 + 매핑되지 않은 모델 처리 없음 |

### 16.3 🟡 Medium (코드 품질/UX)

| # | 위치 | 문제 |
|---|---|---|
| M1 | `PiiDetectionService.cs:24-33` | 정규식 과적용 (13~19자리 임의 숫자도 신용카드로 매칭) |
| M2 | `BannedWordService.cs:56` | `Contains` 부분 일치 ("ass" → "passport" 차단) |
| M3 | `TextExtractionService.cs` | SSRF 취약 (`169.254.169.254` 호출 가능) |
| M4 | `FileService.cs` + `FilesController` 와일드카드 | path traversal `..` 미차단 |
| M5 | `NotificationService.cs:36-52` | `GetNotificationsAsync` 빈 list, `MarkAsReadAsync` no-op 등 다수 stub |
| M6 | Frontend `ToolList`, `ToolBuilder`, `WorkflowList`, `WorkflowExecutionMonitor` | raw axios 사용 → JWT 미부착 가능성 |
| M7 | `Login.vue:172-175` | 평문 dev 자격증명 하드코딩 (isLocalhost 분기, dist에 포함됨) |
| M8 | `Playground.vue:211-218` | 비교 모드 두 번째 모델 호출 mock |
| M9 | `Playground.vue:240` | `localStorage('experiment_${Date.now()}')` 무제한 누적 |
| M10 | `package.json` | `npm run build`가 vue-tsc 미수행 |
| M11 | `i18n/locales/ko.json,en.json` | `quota` 키 중복 |
| M12 | `ChatConversation` 비정규화 캐시 (MessageCount, TotalTokens, TotalCost) | DB 트리거 부재 → drift 가능 |
| M13 | `ConversationId/UserId/Email` 등 | 시간대 일관성 (UTC vs `GETDATE()`) |
| M14 | Frontend | Admin 전용 페이지 라우터 가드 없음 |
| M15 | Frontend | SignalR 패키지 설치되었으나 사용 0건 (dead) |
| M16 | Frontend | chart.js 사용 1곳 (Analytics 등은 progress bar) |

### 16.4 🟢 Low (개선 제안)
- `ToolVersion(ToolId, Version)` UNIQUE 미설정
- `ApiKey.ServiceCode`가 FK 아닌 단순 문자열
- `Presentations.Slides` 레거시 nvarchar(MAX) 컬럼 + PresentationSlides 정규화 이중 저장
- `User.IsDeleted` 글로벌 쿼리 필터 미적용
- BannedWord `collation` 명시 미흡 (한글 대소문자/액센트)
- `KnowledgeBaseDocument.Content` 풀텍스트 인덱스 미적용 (BM25 하이브리드 검색 시 필요)

### 16.5 미구현 / 진행 중 항목
- **랜딩 페이지** Vue 컴포넌트 미구현 (HTML 시안만)
- **이용약관 / 개인정보처리방침** 법무 검토 미완
- **비디오 생성 AI 연동** (Sora/Veo/Gen4Video) 미구현 (Controller/Vue 삭제됨)
- **에이전트 편집 모드** AgentBuilder가 신규 생성만 지원 (수정 모드 미구현)
- **Webhook 이벤트** (`key.expiring`, `quota.exceeded` 등) 미구현
- **Python/Node.js SDK** 미구현
- **API 키 회전(Rotation)** 24시간 유예기간 등 미구현
- **Redis 분산 Rate Limit** (현재 MemoryCache → 다중 서버 환경 미지원)
- **CIDR IP 검증** 미지원 (단순 일치만)

### 16.6 GS인증 관련 미완 항목 (`GS_TODO.md`)
- 전수 테스트, k6 성능 테스트, 브라우저 호환성 (Edge/Firefox/Safari), 모바일 반응형 (768/375px)
- HTTPS 인증서 시험 환경 적용 확인
- OWASP ZAP 취약점 스캔 리포트
- 사업자등록증 / 법인인감증명서
- 서버 재시작·DB 끊김·Redis 실패 신뢰성 테스트
- JWT 토큰 만료·갱신 동작 확인

---

## 17. 개선 우선순위 로드맵

### Phase 1: 보안 핫픽스 (1주)
1. 🔴 `appsettings.*.json` 평문 시크릿을 IIS 환경변수/User Secrets로 이관 + 모든 키 회전 (OpenAI/Gemini/Perplexity/Tavily/Gmail/DB)
2. 🔴 `Users.Email` UNIQUE 인덱스 추가
3. 🔴 `ApiKeys.KeyHash` 컬럼 추가 + UNIQUE 인덱스 (SHA-256(plaintext)) → ApiKeyAuthService O(N) 제거
4. 🔴 AES 고정 IV → per-record random IV (또는 AES-GCM) 마이그레이션
5. 🔴 JWT SecretKey와 AES 암호화 키 분리
6. 🔴 SignalR Hub에 `[Authorize]` 추가 + `JoinUserNotifications`에서 `Context.UserIdentifier` 사용 (클라 입력 무시)
7. 🟠 `Program.cs:362` DB 평문 패스워드 하드코딩 제거
8. 🟠 `Hubs.NotificationHub.JoinUserNotifications` 임의 ID 차단

### Phase 2: 데이터 무결성 (2주)
9. 🔴 EF Core baseline 마이그레이션 작성 + `Database.MigrateAsync()` 전환
10. 🟠 핵심 Cascade FK를 Restrict로 강등 (`ApiServices→Agents`, `Users→Tools/Workflows`)
11. 🟠 `User.IsDeleted` 글로벌 쿼리 필터 적용
12. 🟠 시간대 통일 (UTC) — `GETDATE()` → `SYSUTCDATETIME()` 일괄 교체

### Phase 3: 안정성 (3주)
13. 🟠 `WorkflowExecutionService` 비동기 실행에 `IServiceScopeFactory` 사용 + CancellationToken 전파
14. 🟠 `WorkflowEngine` Condition/DataTransform/Loop 노드 실제 구현, AgentNode → ChatService 연동
15. 🟠 `ChatService._convLocks` TTL 기반 evict (MemoryCache 1h 슬라이딩)
16. 🟠 `AiProxyService.SendChatMessageStreamAsync`에 키 풀/Cooldown 적용
17. 🟠 `CSharpToolExecutor` 샌드박싱 (collectible AssemblyLoadContext) 또는 기능 제거
18. 🟠 `ScriptToolExecutor` 임시 파일 정리 버그 수정
19. 🟠 `Program.cs` Hangfire 등록 실패 빈 catch 제거 → 헬스체크 노출
20. 🟠 `QuotaService.RecordUsageAsync` 토큰 카운트 반영
21. 🟠 `EmbeddingService` ApiKeyPool 사용으로 변경

### Phase 4: 확장성 (4주)
22. 🟠 RAG 벡터 인덱스 도입 (SQL Server 2025 vector / pgvector / Qdrant)
23. 🟠 `AiProxyService` Strategy 패턴 분리 (provider별 ~400 LOC × 8)
24. 🟠 `ApiKeyRateLimiter` Redis 기반 분산 구현
25. 🟠 `ApiKeyPoolService` Redis 기반 분산 쿨다운
26. 🟡 `OpenAICompatController` 진짜 SSE 스트리밍 (`SendChatMessageStreamAsync` 활용)
27. 🟡 `ChatService` Fallback chain 다단계 + 매핑되지 않은 모델 자동 처리

### Phase 5: 코드 품질 (지속)
28. 🟡 PiiDetectionService 정규식 정밀화 (오탐 다수)
29. 🟡 BannedWordService 단어 경계 매칭 (`\b{word}\b`)
30. 🟡 TextExtractionService URL allowlist (SSRF 방지)
31. 🟡 FileService `..` traversal 차단
32. 🟡 Frontend raw axios → `@/services/api` 통합 (ToolList/ToolBuilder/WorkflowList/WorkflowExecutionMonitor)
33. 🟡 거대 view 컴포넌트 분리 (AgentChat 5,286줄, AgentMultiChat 4,031줄)
34. 🟡 `Login.vue` 개발용 자격증명 환경변수로 이관
35. 🟡 `npm run build`에 `vue-tsc` 통합
36. 🟡 i18n `quota` 키 중복 제거

### Phase 6: 미구현 기능
37. 🟢 에이전트 편집 모드 (AgentBuilder)
38. 🟢 비디오 생성 AI 연동 재구현
39. 🟢 Webhook 이벤트 + HMAC-SHA256 서명
40. 🟢 Python/Node.js SDK
41. 🟢 API 키 회전(Rotation)
42. 🟢 랜딩/이용약관/개인정보처리방침 Vue 컴포넌트
43. 🟢 SignalR 클라이언트 활용 (실시간 워크플로우 모니터, 실시간 채팅 푸시)
44. 🟢 SSE 스트리밍 클라이언트 적용 (체감 응답 속도 개선)

---

## 부록 A: 핵심 파일 인덱스

### Backend
- `Program.cs` (575라인) — 부팅, DI, 미들웨어 파이프라인, Hangfire 스케줄
- `Data/AIAgentManagementDbContext.cs` (252라인) — DbSet 등록, 36개 인덱스, 2개 CHECK
- `Data/DatabaseInitializer.cs` (866라인) — 시드 데이터, admin 자가 치유
- `Migrations/20260320012331_AddApiUsagePromptAndIndexes.cs` — 유일한 EF 마이그레이션
- `Migrations/AIAgentManagementDbContextModelSnapshot.cs` (2,373라인) — 현재 모델 스냅샷
- `Services/AiProxyService.cs` (3,749라인) — 다중 LLM 프록시
- `Services/ChatService.cs` (1,049라인) — 채팅 오케스트레이션
- `Services/PresentationService.cs` (1,394라인)
- `Services/PptxGenerationService.cs` (1,175라인)
- `Services/ApiKeyAuthService.cs` (108라인) — 외부 API 인증
- `Services/RagService.cs` (179라인)
- `Services/WorkflowEngine.cs` (362라인)
- `Controllers/AgentsController.cs` (1080라인)
- `Controllers/OpenAICompatController.cs` (399라인)
- `Attributes/ApiKeyAuthorizeAttribute.cs` — API Key 인증 필터
- `Infrastructure/ActivityLogChannel.cs` — 비동기 채널
- `BackgroundJobs/ActivityLogWorker.cs` — IHostedService
- `Middleware/{ActivityLogging,GlobalExceptionHandler,RequireHttpsForDomain,SecurityHeaders}Middleware.cs`

### Frontend
- `ClientApp/src/main.ts`, `App.vue` — 부팅
- `ClientApp/src/router/index.ts` (263라인)
- `ClientApp/src/stores/auth.ts` — 유일한 Pinia 스토어
- `ClientApp/src/services/api.ts` — axios 인스턴스 + 인터셉터
- `ClientApp/src/views/agent/AgentChat.vue` (5,286라인)
- `ClientApp/src/views/agent/AgentBuilder.vue` (1,182라인)
- `ClientApp/src/views/workflow/WorkflowBuilder.vue` (751라인) — Vue Flow 사용처
- `ClientApp/src/views/PresentationBuilder.vue` (1,830라인)
- `ClientApp/src/i18n/locales/{ko,en}.json` (각 543라인)
- `ClientApp/vite.config.ts`, `tsconfig.json`, `package.json`

### 운영 설정
- `appsettings.json`, `appsettings.Development.json`, `appsettings.Production.json` (⚠️ 시크릿 노출)
- `web.config` — IIS InProcess 호스팅
- `iis-setting.ps1` — IIS 환경변수 주입
- `CheckAppStatus.ps1`, `DbConnectionTest.ps1`

---

## 부록 B: 참고 문서 (기존 자산)

| 문서 | 위치 | 용도 |
|---|---|---|
| 제품소개서 v1.0 | `DOCS/제품소개서_AIAgentManagement_v1.0.md` | 비즈니스 목적, 6대 기능 |
| 사용자취급설명서 v1.0 | `DOCS/사용자취급설명서_AIAgentManagement_v1.0.md` | 운영 시나리오, 관리자 절차, 오류 코드 |
| LiteLLM vs AgentHub | `LiteLLM-vs-AgentHub.md` | 제품 포지셔닝 |
| AGENT_API_ROADMAP | `DOCS/AGENT_API_ROADMAP.md` | 외부 API 계획 |
| RAG_USAGE_GUIDE | `RAG_USAGE_GUIDE.md` | RAG 사용법, 임베딩 설정 |
| PPT_TEMPLATE_IMPLEMENTATION_PLAN | `PPT_TEMPLATE_IMPLEMENTATION_PLAN.md` | PPTX 빌더 설계 |
| PRESENTATION_BUILDER_ENHANCEMENT_PLAN | `PRESENTATION_BUILDER_ENHANCEMENT_PLAN.md` | 빌더 로드맵 |
| LAYOUT_ARCHITECTURE | `LAYOUT_ARCHITECTURE.md` | 프론트 레이아웃 |
| LIBREOFFICE_INSTALLATION_GUIDE | `LIBREOFFICE_INSTALLATION_GUIDE.md` | LibreOffice 설정 |
| REDIS_SETUP_GUIDE | `DOCS/REDIS_SETUP_GUIDE.md` | Redis 폴백 정책 |
| DATABASE_DESIGN | `DATABASE_DESIGN.md` | 초기 14테이블 설계 |
| PROJECT-STATUS | `PROJECT-STATUS.md` | 2026-03-16 현황 |
| GS_TODO | `GS_TODO.md` | GS인증 미완 |
| Postman Collection | `DOCS/AIAgentManagement_AgentAPI.postman_collection.json` | 외부 API 사용 예시 |

---

> 본 문서는 코드베이스 직접 분석 결과(파일경로:라인번호 인용 기반)와 기존 운영 문서를 통합한 종합 명세서이다.
> 작업 진행 시 §16의 이슈 목록과 §17의 우선순위 로드맵을 기준으로 사용자 승인 후 단계별로 처리한다.
