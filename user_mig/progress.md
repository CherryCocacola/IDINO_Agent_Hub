# IDINO Agent Hub — 통합 작업 진행 상황

> **마지막 갱신**: 2026-05-05
> **갱신 규칙**: 모든 작업 완료 시 본 파일을 갱신한다 (CLAUDE.md 의무 사항).
> **참조**: `user_mig/TECHSPEC.md` (통합 기술 명세), `docs/AI_INVENTORY.md` (Phase 1 산출물)

---

## 0. 현재 상태 한눈에

| 항목 | 값 |
|---|---|
| **현재 Phase** | Phase 3 (AgentHub MSSQL → PostgreSQL 마이그레이션) — **3.1 코드 전환 + 3.5 진짜 SSE 코드 작성 완료** |
| **다음 Phase** | Phase 3.2 (Npgsql baseline migration `Init` 생성, dotnet CLI 환경 마련 후) — 3.5는 빌드 검증 대기 |
| **마지막 commit** | `259012f [infra/db] Phase 2 — AGENT_HUB DB init.sql + DB_MIGRATION 가이드` (Phase 3.1 / 3.5 commit 후 갱신 예정) |
| **GitHub remote** | https://github.com/CherryCocacola/IDINO_Agent_Hub.git (push 대기 — secret leak 미해결) |
| **TECHSPEC** | `user_mig/TECHSPEC.md` v1.0 (작성 완료) |
| **AI 인벤토리** | `docs/AI_INVENTORY.md` v1.0 (Phase 1 산출, 35 호출 + 5 위임 + 15 신규 Agent 카탈로그) |
| **DB 마이그레이션** | `infra/db/init.sql` v1.0 + `docs/DB_MIGRATION.md` v1.0 (Phase 2 산출, 단일 PG + 4 schema + pgvector + idempotent) |
| **분석 보고서** | `source_AGENTHUB.md`, `source_DOCUTIL.md`, `source_CAREER.md`, `source_NEXUS.md` (4개 완료) |

---

## 1. Phase 진척도

| Phase | 내용 | 상태 | 완료일 / 예정 |
|---|---|---|---|
| **0** | 작업공간 셋업 + monorepo 초기화 + 분석/TECHSPEC | ✅ 완료 | 2026-05-04 |
| **1** | AI 호출 인벤토리 작성 (`docs/AI_INVENTORY.md`) | ✅ 완료 | 2026-05-05 |
| **2** | AGENT_HUB DB 설계 + 생성 (`infra/db/init.sql`) | ✅ 완료 | 2026-05-05 |
| **3** | AgentHub MSSQL → PostgreSQL 마이그레이션 | 🔄 진행 중 (3.1 완료) | Phase 2 후 |
| **4** | DocUtil/career → AGENT_HUB 통합 | ⏳ 대기 | Phase 3 후 |
| **5** | AgentHub Nexus provider + LlmRouting + 진짜 SSE | ⏳ 대기 | Phase 3 후 (4와 병렬) |
| **6** | DocUtil 운영자 → AgentHub 흡수 + KB 마이그레이션 | ⏳ 대기 | Phase 5 후 |
| **7** | DocUtil/career AI 호출 → AgentHub 위임 | ⏳ 대기 | Phase 5+6 후 |
| **8** | (보류) Vue → Next.js | ⏸ 보류 | — |

범례: ✅ 완료 / 🔄 진행 중 / ⏸ 사용자 승인 대기 / ⏳ 의존성 대기

---

## 2. Phase 0 — 완료된 작업 (2026-05-04)

### 2.1 디렉토리 셋업
- [x] `D:\workspace\IDINO_Agent_Hub\` 생성
- [x] 4개 서브프로젝트 복사 (PowerShell robocopy):
  - [x] `agenthub/` (98 items, AIAgentManagement 복사)
  - [x] `docutil/` (23 items, document_utilization 복사)
  - [x] `career/` (77 items, idino_career 복사)
  - [x] `nexus/` (21 items, nexus 복사)

### 2.2 루트 파일
- [x] `.gitignore` (다국어 스택 + 시크릿 제외)
- [x] `README.md` (프로젝트 개요)
- [x] `CLAUDE.md` (AI 코딩 도구 협업 컨텍스트)

### 2.3 `.claude/rules/` (6개)
- [x] `architecture.md` (10개 원칙 P1~P10)
- [x] `anti-patterns.md` (13개 금지 패턴)
- [x] `agent-collaboration.md` (작업 절차 + 커밋 규약)
- [x] `domain-model.md` (엔티티/용어 카탈로그)
- [x] `testing.md` (4계층 테스트 전략)
- [x] `development-workflow.md` (Phase별 작업 순서)

### 2.4 `docs/`
- [x] `ARCHITECTURE.md` (Control Plane / Data Plane Federation)
- [x] `AI_INVENTORY.md` (Phase 1 산출물 템플릿)

### 2.5 `user_mig/` (신규)
- [x] `source_AGENTHUB.md` (AgentHub 종합 분석, 334 라인)
- [x] `source_DOCUTIL.md` (DocUtil 종합 분석, 341 라인)
- [x] `source_CAREER.md` (idino_career 종합 분석, 295 라인)
- [x] `source_NEXUS.md` (Nexus 종합 분석, 354 라인)
- [x] `TECHSPEC.md` (통합 기술 명세, v1.0)
- [x] `progress.md` (본 파일)

### 2.6 Git
- [x] `git init -b main`
- [x] `git remote add origin https://github.com/CherryCocacola/IDINO_Agent_Hub.git`
- [x] 초기 commit `1da04ab` (1,921 files / 558,811 insertions)
- [x] 시크릿 파일 .gitignore 강제 (검증 완료):
  - `appsettings.Development/Production.json`
  - `.env` (career 6 MS, infrastructure)
  - `nexus/config/{nexus_config,permission_rules,tenants}.yaml`
  - `nexus/config/ssl/`

### 2.7 GitHub Push 상태
- ⏸ **대기 중** — 사용자 승인 후 `git push -u origin main` 실행

---

## 3. 핵심 의사결정 (Phase 0 동안 확정)

| ADR | 결정 | 이유 |
|---|---|---|
| ADR-1 | Nexus 통합 **옵션 B** (AgentHub-side `CallNexusAsync`) | Nexus 세션/멀티테넌시 보존 |
| ADR-2 | RAG 단일 권위 = **DocUtil** | AgentHub 자체 KB는 deprecate |
| ADR-3 | Vue 3 유지 (Phase 8 보류) | 통합의 핵심 가치는 Data Plane 통합 |
| ADR-4 | 단일 PostgreSQL `AGENT_HUB` DB + 4 schema | 운영 단순화 |
| ADR-5 | MSSQL → PostgreSQL | DocUtil/career가 PG 사용, pgvector 우수 |
| ADR-7 | DocUtil Phase 4 별도 트랙 | S6/S7 미완 상태 통합 시 회귀 위험 |
| ADR-8 | `Tenants` 신규 엔티티 | 멀티테넌시 단일 권위 |
| ADR-9 | JWT HS256 단일 표준 | DocUtil RS256/HS256 fallback 통합 |
| ADR-10 | 임베딩 1536D 단일화 | Qdrant collection 단일성 |
| ADR-11 | Nexus DB 별도 유지 | 라이프사이클 다름 |
| ADR-12 | 순환 호출 방지 (DocUtil은 `/search/hybrid`만) | 무한 루프 방지 |
| ADR-13 | 공유 시크릿 인증 (AgentHub-Nexus) | LAN 격리 + 1차 방어 |
| ADR-15 | progress.md 자동 갱신 규칙 | git commit 단위로 진행 명확화 |

(전체 ADR-1 ~ ADR-15는 TECHSPEC §20 참조)

---

## 4. 미해결 결정 (Open Questions, Phase 진입 전 결정)

| ID | 질문 | 결정 시점 |
|---|---|---|
| Q1 | career `department_id` 매핑 정책 (Tenants sub-org / 별도 Departments / 자체 유지) | Phase 4 시작 전 |
| Q2 | 사용자 SSO 시점 (Phase 5+ 즉시 / Phase 7+ / 별도 트랙) | Phase 4 완료 후 |
| Q3 | **DocUtil Phase 4 S6/S7 진행 위치 (DocUtil 원본 / monorepo 내부)** | **즉시 (Phase 1 진입 전)** |
| Q4 | Nexus DB 위치 (별도 DB / AGENT_HUB.nexus schema) | ADR-11에 따라 별도 DB, schema 분리만 추가 검토 |
| Q5 | 외부 LLM Tenant별 다른 키 풀 가능 여부 | Phase 5 |
| Q6 | DocUtil 임베딩 vLLM Qwen3 2048D 처리 (제거 / 별도 collection) | Phase 7 |
| Q7 | Workflow Condition/DataTransform/Loop 정식 구현 | Phase 5+ 별도 |
| Q8 | CSharpToolExecutor 보안 (collectible AssemblyLoadContext / 기능 차단) | Phase 5+ |
| Q9 | 운영자 SSO (AD/LDAP) | Phase 6+ |
| Q10 | 시계열 데이터 보존 정책 | Phase 5+ |

---

## 5. 위험 추적 (R1~R30)

### Critical (Phase 3 진입 전 결정 필수)
- [ ] R1: Tenant/Organization/Department 모델 설계 → §4.5
- [ ] R5: Nexus DB 별도 유지 → ADR-11 확정
- [ ] R11: EF baseline 부재 → Phase 3에서 신규 작성
- [ ] R15: JWT 알고리즘 통일 → ADR-9 확정

### High (Phase 5 전)
- [ ] R3: OpenAI Structured Outputs 다중 프로바이더 fallback
- [ ] R7: API Key 회전
- [ ] R8: CIDR IP 검증
- [ ] R10: Nexus 인증 미들웨어
- [ ] R12: Cascade Delete 강등
- [ ] R13: 임베딩 차원 통일
- [ ] R17: Qdrant collection 단일성 vs Nexus 1024D
- [ ] R18: 평문 시크릿 잔존
- [ ] R20: AgentHub KB → DocUtil visibility 매핑
- [ ] R27: SSO 결정

### Medium / Low — TECHSPEC §16 참조

---

## 6. 작업 로그 (Append-only, 시간 역순)

### 2026-05-05 (Phase 3.5 — 가짜 SSE → 진짜 SSE 코드 작성 완료, 빌드 검증 대기)
- **Phase 3.5 우선 진입 (UX 가시성 즉시 개선)**: TECHSPEC §15.4 / §16 C9(가짜 SSE) + H5(Stream API 키 풀 우회) 동시 해소
- **신설 파일 1개**:
  - `agenthub/DTOs/ChatChunk.cs` — `record ChatChunk(Content, FinishReason, PromptTokens, CompletionTokens, TotalTokens)` + 정적 helper `Delta/Stop/Usage`
- **수정 파일 4개**:
  - `agenthub/Services/IAiProxyService.cs` — 기존 `SendChatMessageStreamAsync`(`Task<Stream>` 반환)은 `[Obsolete]` 마킹(호출처 0건). 신규 `IAsyncEnumerable<ChatChunk> SendChatMessageStreamChunksAsync(...)` 추가
  - `agenthub/Services/AiProxyService.cs` — 기존 메서드 `[Obsolete]`. 신규 `SendChatMessageStreamChunksAsync` 추가:
    - OpenAI provider: `StreamOpenAiChunksAsync` 신규 — `HttpCompletionOption.ResponseHeadersRead` 로 본문 chunk 단위 수신 + `data: {...}\n\n` 라인 파서 + `[DONE]` 마커 처리. **`stream_options.include_usage:true` 옵션으로 마지막 chunk에 OpenAI 실제 토큰수 동봉(0.65 추정 제거)**. **ApiKeyPool 라운드로빈 + 429 Cooldown 적용 (H5 해소)**
    - 그 외 provider(claude/gemini/perplexity/mistral/copilot/azure-openai): 비스트리밍 호출 결과를 단일 chunk로 폴백 yield + TODO Phase 5+ 주석. 가짜 SSE 위장보다 정직
    - 신규 private 클래스 3개: `OpenAiStreamChunk` / `OpenAiStreamChoice` / `OpenAiStreamDelta` (snake_case 매핑)
    - `using System.Runtime.CompilerServices;` 추가 (`[EnumeratorCancellation]`)
  - `agenthub/Services/IChatService.cs` — `IAsyncEnumerable<ChatChunk> SendDirectMessageStreamChunksAsync(...)` 추가
  - `agenthub/Services/ChatService.cs` — 동명 streaming wrapper 구현. Quota 사전 체크 + BannedWord/PII 검사(SendDirectMessageAsync 와 동일 정책) → ConversationFind/Create(락 보존) → AiProxy.SendChatMessageStreamChunksAsync await foreach yield → 종료 후 ChatMessage / ApiUsage / Conversation 통계 1회 SaveChanges + RecordUsageAsync. 영속화 실패는 silently 로그(이미 chunk는 사용자에게 전달됨)
  - `agenthub/Controllers/OpenAICompatController.cs` — `SendStreaming` 메서드 전면 재작성:
    - **삭제**: `Content.Split(' ')` + `Task.Delay(15)` 단어 위장 chunk 패턴(라인 ~343-358)
    - **신규**: `await foreach (chunk in _chatService.SendDirectMessageStreamChunksAsync(...))` → 즉시 `data: {...}\n\n` flush
    - SSE 헤더: `Cache-Control: no-cache` + `X-Accel-Buffering: no` + `Connection: keep-alive`
    - usage chunk: OpenAI 표준 동작(finish_reason 청크 다음에 choices=[] + usage 채운 별도 청크) 모사하여 OpenAI SDK 호환
    - 에러 fallback: 스트림 시작 후 예외 발생 시 SSE error chunk 한 건 + `[DONE]` 흘리고 종료(상태 코드 변경 불가 상황 대응)
    - 비스트리밍 분기의 0.65 휴리스틱 추정값에는 TODO 주석 추가(Phase 5+에서 DTO 확장 시 정확화)
- **추가 점검 결과 / 사용자 보고용 사실**:
  - **Vue 채팅 UI(`AgentChat.vue`)는 OpenAI 호환 API를 호출하지 않음**: `AgentChat.vue:1708` `api.post('/chat/send', { ..., stream: false })` → ChatController `[POST] /api/chat/send`(라인 347) → `ChatService.SendDirectMessageAsync` 비스트리밍 분기. 즉 본 작업은 **외부 OpenAI 호환 클라이언트(Cursor/LangChain/OpenAI SDK/Postman) 한정** UX 개선. **사용자가 보고한 "Vue UI에서 5~10초 대기 후 일괄 출력"은 본 작업으로 직접 해결되지 않음** — Phase 5+ 별도 트랙에서 `/api/chat/send` 엔드포인트도 SSE 변환 + 프론트엔드 `EventSource`/`fetch ReadableStream` 도입 필요(별도 TODO)
  - 기존 `SendChatMessageStreamAsync` 호출처 grep 결과 **0건** — `[Obsolete]` 마킹만으로 안전
  - `IAiProxyService` / `IChatService` 구현체 grep 결과 각각 단일(`AiProxyService` / `ChatService`) — 모의구현 영향 없음
- **잠재 위험 / 사용자 검증 필요**:
  - IIS InProcess 호스팅에서 `Response.Body.FlushAsync()` 호출 시 chunked transfer 실제 적용 확인 필요(Content-Length 미설정 + `X-Accel-Buffering: no` 설정으로 1차 방어). 운영 IIS 앞 reverse proxy(nginx/Apache/IIS ARR) 사용 시 buffering 비활성화 추가 점검
  - OpenAI `stream_options.include_usage:true` 옵션은 OpenAI 표준 모델만 지원 — Azure OpenAI / 호환 엔드포인트에서 미지원 시 usage 0 반환 가능(현재 폴백 분기는 비스트리밍 호출이므로 영향 없음)
  - **OpenAI streaming 경로는 RAG / 웹검색 / DeepResearch 미적용**(SendChatMessageAsync 의 RAG 흐름과 미동기화). Phase 5+ 에서 RAG 컨텍스트 주입을 streaming 진입 직전 별도 단계로 분리하여 양 경로에서 공유 예정 — 본 단계 코드에 명시 TODO 주석 (`StreamOpenAiChunksAsync` summary)
  - dotnet CLI 미설치 — `dotnet build` / `dotnet test` 미실행. 사용자 측에서 SDK 설치 후 워닝 0건 검증 필요
- **검증 방법 (사용자 측)**:
  ```bash
  # 외부 OpenAI 호환 SDK 호환성
  curl -N -X POST https://localhost:5001/v1/chat/completions \
    -H "X-API-Key: ak-xxx" -H "Content-Type: application/json" \
    -d '{"model":"<agentCode>","messages":[{"role":"user","content":"안녕"}],"stream":true}'
  # 기대: 토큰 단위 실시간 흐름. 가짜 SSE 시 5~10초 대기 후 일괄 → 진짜 SSE 시 즉시 첫 chunk
  ```
- **남은 작업 (별도 commit / 별도 task)**:
  - Phase 3.5 검증: dotnet 8 SDK 환경에서 `dotnet build` 워닝 0건 + 외부 SDK e2e 테스트
  - Phase 3.5+: Vue 채팅 UI(`/api/chat/send`)도 streaming SSE 도입 — 사용자 보고한 "5~10초 대기" 진짜 해소 (별도 작업, frontend 수정 포함)
  - C9 / H5는 본 코드로 해소 완료(빌드 검증 후 TECHSPEC §16 표 업데이트 예정)

### 2026-05-05 (Phase 3.1 — EF Provider 코드 전환 완료)
- **AgentHub EF Core SQL Server → PostgreSQL provider 교체** (코드만, 운영 데이터 이전 보류)
  - `agenthub/AIAgentManagement.csproj`: `Microsoft.EntityFrameworkCore.SqlServer` / `Hangfire.SqlServer` 제거 → `Npgsql.EntityFrameworkCore.PostgreSQL` 8.0.11 / `Hangfire.PostgreSql` 1.20.10 추가. `Microsoft.Data.SqlClient`는 보류 (3개 파일 직접 사용처 — Program.cs:403, TestDbConnection.cs, Controllers/DatabaseBackupController.cs)
  - `agenthub/Program.cs`:
    - `using Hangfire.SqlServer` → `using Hangfire.PostgreSql`
    - `options.UseSqlServer(...)` → `options.UseNpgsql(connectionString, npg => npg.CommandTimeout(30))`
    - `UseSqlServerStorage(...)` → `UsePostgreSqlStorage(opt => opt.UseNpgsqlConnection(...), new PostgreSqlStorageOptions { SchemaName = "hangfire", PrepareSchemaIfNecessary = true, QueuePollInterval = TimeSpan.Zero })`
  - `agenthub/Data/AIAgentManagementDbContext.cs`: `OnModelCreating` 시작부에 `modelBuilder.HasDefaultSchema("AIAgentManagement")` 추가 (P4 schema 격리)
  - `agenthub/Migrations/` → `Migrations.mssql.archive/` 로 `git mv` (3 파일 보존, ADR-7 historical 참조용). csproj `<Compile Remove="Migrations.mssql.archive\**" />` 추가하여 빌드 제외
  - `agenthub/appsettings.Development.json`: `DefaultConnection`만 `Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Search Path=AIAgentManagement,public` 형식으로 전환. 다른 키(JWT/AI/Email)는 미변경
  - `agenthub/appsettings.Production.json`: **변경 안 함** (위험 작업, Phase 7+에서 사용자 결정)
- **검증 결과 / 발견 사항**:
  - `dotnet` CLI가 Windows 환경에 설치되어 있지 않아 `dotnet build` / `dotnet ef migrations add Init` 실행 불가. Phase 3.2에서 dotnet 8 SDK 설치 후 검증 + baseline 생성 필요
  - **(해결)** root `.gitignore`의 `data/` / `models/` / `checkpoints/` 패턴이 Windows case-insensitive 매칭으로 .NET 표준 `Data/` `Models/` 디렉토리와 Python ORM `models/` 모듈까지 차단하는 결함 발견. 본 commit에서 3개 디렉토리 패턴 제거 (파일 확장자 패턴 `*.bin/.safetensors/.pt/.pth/.onnx/.gguf`만 유지, 대용량 데이터 디렉토리는 시스템별 명시 정책으로 전환)
  - **(해결)** `.gitignore` 정정 결과 1da04ab 초기 commit에서 누락된 핵심 코드 55개 파일 신규 추적: `agenthub/Data/` (DbContext + DatabaseInitializer + 3 SQL) 5개, `agenthub/Models/` (EF 엔티티) 35개, `career/services/{advisor|alumni|auth|badge|coaching|competency|opportunity|risk|simulation|skill|student}-service/app/models/` 15개. docutil/nexus는 추가 0건 (이미 적절히 추적 중)
  - `agenthub/appsettings.Development.json`은 의도된 시크릿 보호로 그대로 차단 유지 (디스크에만 적용, 향후 `appsettings.Development.example.json` 템플릿 도입 검토)
  - `Microsoft.Data.SqlClient` 직접 사용처 3건 (`Program.cs:403` `catch SqlException` / `TestDbConnection.cs` 전체 / `Controllers/DatabaseBackupController.cs:148,179` `new SqlConnection`) — Phase 3 후속에서 PG로 정리 또는 controller 자체 deprecate 검토 필요

### 2026-05-05 (Phase 2 완료)
- **Phase 2 — AGENT_HUB DB 설계 + 생성 완료**
  - `infra/db/init.sql` v1.0 작성 (idempotent, 9 섹션) — psql `-v idino_pw` 환경변수 주입 + DO 블록 멱등 보호 + 검증 쿼리 포함
    - DB user `AGENT_HUB` (LOGIN, password 환경변수)
    - DATABASE `AGENT_HUB` (UTF8, ko_KR.UTF-8, TEMPLATE template0)
    - Extensions: `vector` / `uuid-ossp` / `pgcrypto` / `pg_trgm`
    - Schemas: `AIAgentManagement` / `document_utilization` / `idino_career` / `hangfire`
    - `ALTER DEFAULT PRIVILEGES`로 향후 객체 자동 권한 부여
    - search_path 기본값 4 schema + public
  - `docs/DB_MIGRATION.md` v1.0 작성 (9 섹션 + 부록 2개) — Phase 2 적용 절차 + Phase 3/4 계획 가이드 + 롤백/재시작/모니터링/시크릿 정책
- ADR-4(단일 PG) / ADR-10(임베딩 1536D) / P4(스키마 격리) / P10(시크릿 비커밋) / R26(시크릿 환경변수) 모두 반영
- 본 단계는 schema/extension/role까지만 생성 — 테이블은 Phase 3+에서 EF/Alembic이 담당

### 2026-05-05 (Phase 1 완료)
- **Phase 1 — AI 호출 인벤토리 완료** (`docs/AI_INVENTORY.md` 12 섹션 + 부록 2개 v1.0)
  - 4개 시스템 grep 검증 + source 보고서 종합
  - **35개 직접 호출 지점** 식별 (agenthub 8 분기 / docutil 9 / career 12 / nexus 0)
  - **5개 위임 호출** (career coaching/competency/roadmap/opportunity/skill)
  - **15개 신규 Agent 카탈로그** 정의 (docutil 4 + career 8 + 공통 3)
  - **Phase 7 견적 9 영업일** 확정 (TECHSPEC §12 "10 영업일"과 일치, 1일 여유)
- **본 인벤토리 작업으로 신규 발견** (TECHSPEC 보강 권고):
  - DocUtil 단일 진입점 위반 2건 추가 — `agentic_search.py:215,237`, `training/data_generator.py:68-69` (R31 후보)
  - AgentHub Chat provider 실측 7개 (보고서 8 표기 정정 — Vertex/Tavily는 별도 카테고리)
  - AgentHub 가짜 SSE 정확 위치 — `OpenAICompatController.cs:343` `Content.Split(' ')` + `:357` `Task.Delay(15)` (138은 함수 진입점)
  - career skill-service 포트 불일치 발견 — `AI_SERVICE_URL=:8000` vs 실제 ai-service `:8006` (W5)
- **GitHub push 차단 발견** — 첫 commit `1da04ab`에 평문 API 키 4개 (OpenAI/Gemini/Perplexity/Tavily). 위치: `agenthub/iis-setting.ps1` + `agenthub/TODO.md`. 사용자 결정 대기 (키 무효화 + B1/B2/B3 옵션)
- CLAUDE.md 최상단에 **신규 세션 자동 로드 규칙** 추가 (`progress.md` + `TECHSPEC.md` 필수 Read). commit `c3fc024`
- 글로벌 메모리 7개 작성:
  - `MEMORY.md` (인덱스)
  - `idino_agent_hub_migration.md` (project, 작업 dir 이전)
  - `idino_agent_hub_status.md` (project, Phase 0 완료/Push 차단)
  - `idino_agent_hub_secret_leak.md` (project, 4개 평문 키 + 처리 옵션)
  - `idino_agent_hub_docs.md` (reference, 문서 위치)
  - `idino_agent_hub_session_entry.md` (feedback, 진입 절차)
  - `idino_agent_hub_decisions.md` (project, 15개 ADR 요약)
- 메모리는 `D--workspace-AIAgentManagement` + `D--workspace-IDINO_Agent_Hub` 양쪽에 보존 (작업 dir 전환 대비)

### 2026-05-04
- 통합 TECHSPEC v1.0 작성 (`user_mig/TECHSPEC.md`, 21개 섹션 + 부록 3개)
- 4개 시스템 종합 분석 보고서 작성 (병렬 에이전트 4개)
  - `source_AGENTHUB.md` — TECHSPEC.md 1171라인 + 9개 섹션 분석
  - `source_DOCUTIL.md` — Phase 4 ~54% 완료, factory 단일 진입점 확인
  - `source_CAREER.md` — LLM 직접 호출 11곳, AgentHub Agent 매핑 8개 제안
  - `source_NEXUS.md` — 4-Tier AsyncGenerator + 옵션 B 통합 명세
- progress.md 신설 (본 파일)
- CLAUDE.md에 progress.md 자동 갱신 규칙 추가
- Phase 0 완료 — Git 초기 commit + remote 등록 (`1da04ab`)
- 4개 서브프로젝트 monorepo 통합 (1,921 files)
- 셋업 파일 작성 (.gitignore, README, CLAUDE.md, .claude/rules/ 6개, docs/ 2개)

---

## 7. 다음 작업 (Phase 3 진행 예정)

### Phase 3: AgentHub MSSQL → PostgreSQL 마이그레이션 + 부채 정리

**Phase 3은 가장 큰 위험 구간** — DB 전환 + 코드 부채(C1~C10) 동시 처리. 사용자 승인 후 진행 권장.

#### 작업 항목 (예상 10 영업일)
- [ ] EF Core provider 교체 — `Microsoft.EntityFrameworkCore.SqlServer` → `Npgsql.EntityFrameworkCore.PostgreSQL` 8.x
- [ ] 기존 SqlServer migration 1개 + ModelSnapshot 폐기, Npgsql baseline `Init` 신규 생성
- [ ] `appsettings.*.json` connection string 전환 (`Server=...` → `Host=...;Search Path=AIAgentManagement`)
- [ ] **부채 정리 (DB 전환과 동시)**:
  - C1: AES-CBC 고정 IV → per-record random IV + AES-GCM (`ApiKey.KeyIv`/`KeyTag` 컬럼 신설 + 재암호화)
  - C2: JWT SecretKey ↔ AES Key 분리 (KMS/User Secrets)
  - C3: API Key 풀스캔 → `KeyHash UNIQUE` SHA-256 인덱스
  - C4: `Users.Email` UNIQUE 인덱스 추가
  - C7: `EnsureCreatedAsync` → `MigrateAsync` (baseline 적용으로 자연 해결)
  - C8: SignalR Hub `[Authorize]` + `Context.UserIdentifier` 사용
  - H10: `QuotaService.RecordUsageAsync` 토큰수 무시 버그 수정
  - H13: `AiProxyService` 3,749 LOC god class 일부 분해 (Strategy 패턴 준비)
- [ ] JSON `nvarchar(MAX)` → `jsonb` 전환 (인덱싱 가능 컬럼만)
- [ ] `DocumentChunk.Embedding` → `vector(1536)` + IVFFlat 인덱스 (자체 KB는 deprecate 예정이지만 Phase 6까지는 동작 유지 필요)
- [ ] Hangfire SqlServer storage → `Hangfire.PostgreSql` 전환
- [ ] `DatabaseInitializer.cs` (866 LOC) idempotent 재작성 — Roles/ApiServices/ApiServiceModels/Agents 시드
- [ ] 데이터 이전 (pgloader 또는 bcp+COPY) — MSSQL → AGENT_HUB.AIAgentManagement
- [ ] 빌드 검증 — `dotnet build` 워닝 0건, `dotnet ef database update` 성공
- [ ] 통합 검증 — Agent CRUD, OpenAI 호환 API, ApiKey 인증, Quota 리셋

#### Phase 3 진입 전 결정 필요
- **운영 데이터 이전 시점**: 개발/스테이징에서 dry-run 후 운영 적용 (사용자 확인 필수 — 운영 데이터 영향)
- **AGENT_HUB DB 비밀번호 회전**: 현 비밀번호 사용 vs 신규 발급 (R26 — 비밀번호 정책)

**예상 영업일**: 10일
**의존성**: Phase 2 (완료)

### 별도 트랙 (Phase 진행과 무관)
- **Q3**: DocUtil S6/S7 진행 위치 (Phase 4 시작 전 결정, 현 단계 차단 없음)
- **GitHub push 차단**: 첫 commit `1da04ab` secret leak — 키 무효화 + B1/B2/B3 옵션 (사용자 결정 시 처리)

---

## 8. 갱신 규칙 (CLAUDE.md 동기화)

본 progress.md는 다음 시점에 갱신한다:
1. 새 Phase 진입 시 — Phase 상태 변경 + 작업 로그
2. 핵심 작업 완료 시 — 작업 로그 추가
3. ADR / 위험 / Open Question 변경 시 — 해당 섹션 갱신
4. Git commit 후 — 마지막 commit 해시 갱신

**갱신 형식**:
- 시간 역순으로 작업 로그 추가 (오래된 항목 위에 신규 항목)
- Phase 상태표는 항상 최상단
- ADR/위험은 결정 단위로 행 추가/수정

---

## 부록. 빠른 참조

| 작업 | 위치 |
|---|---|
| 통합 기술 명세 | `user_mig/TECHSPEC.md` |
| AgentHub 분석 | `user_mig/source_AGENTHUB.md` |
| DocUtil 분석 | `user_mig/source_DOCUTIL.md` |
| career 분석 | `user_mig/source_CAREER.md` |
| Nexus 분석 | `user_mig/source_NEXUS.md` |
| 협업 규칙 | `.claude/rules/agent-collaboration.md` |
| 아키텍처 원칙 | `.claude/rules/architecture.md` |
| 금지 패턴 | `.claude/rules/anti-patterns.md` |
| 도메인 모델 | `.claude/rules/domain-model.md` |
| 테스트 전략 | `.claude/rules/testing.md` |
| Phase 작업 순서 | `.claude/rules/development-workflow.md` |
| AI 인벤토리 (Phase 1 대상) | `docs/AI_INVENTORY.md` |
| DB 마이그레이션 기록 (Phase 2+) | `docs/DB_MIGRATION.md` (예정) |
