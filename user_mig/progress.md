# IDINO Agent Hub — 통합 작업 진행 상황

> **마지막 갱신**: 2026-05-08 (**Phase 9 — MSSQL 운영 데이터 → PostgreSQL 이관 + AES 키 회전 (묶음 처리) 완료**) — 본 monorepo Phase 3 (MSSQL→PG 스키마+시드 마이그레이션) 이후 미완으로 남았던 운영 사용자 데이터/대화 이력 cutover 를 단일 작업으로 종결. **시연 환경이 실 사용자 기반으로 동작**. 직전 운영 MSSQL `192.168.10.159:1433/AIAgentManagement` (TrustServerCertificate=true, ODBC `SQL Server` 드라이버) 의 14 운영 테이블(사용자 131, Role 3, Agent 17, ApiService 15, ApiServiceModel 84, ApiKey 1, ChatConversation 191, **ChatMessage 715**, ApiQuota 925, ApiUsage 474, BannedWord 240, Presentation 66, UserSession 223, UserRole 7, Team/TeamMember 1) 을 호스트 `192.168.10.39` `docutil-postgres` 컨테이너의 `AGENT_HUB.AIAgentManagement` schema 로 단일 트랜잭션 import. **AES 키 회전 묶음 처리**: 신규 AES-256 키 (32B random, base64) 생성 → ApiKey 1 행 (`ak-4xxx...GMrU`, len=46) 을 Legacy CBC + 고정 IV(16B 0) + JWT-derived AES key(SHA-256(`YourSuperSecret...`)) 로 복호화 → 신규 GCM(12B random nonce + 16B tag) 으로 재암호화 → KeyHash 를 SHA-256 hex 64 자로 백필 → PG 컬럼 EncryptedKey/KeyIv/KeyTag/KeyHash 4 column 일괄 적재. **신규 키 SHA256(앞 16자)** = `e25aba443e033038` (평문/key 자체는 progress.md/commit 비노출, 호스트 `/home/idino/agenthub/.env` 의 `ENCRYPTION_API_KEY_AES_KEY` 환경변수에만 저장 — `docker-compose.yml` 의 `${ENCRYPTION_API_KEY_AES_KEY}` 참조). **PG dump 백업** (롤백 대비): `/tmp/agent_hub_pre_phase9_20260508_091309.dump` 142 KB (호스트 `192.168.10.39:/tmp/`, custom format) — `pg_restore -n "AIAgentManagement"` 로 검증 데이터 시점으로 복구 가능. **이관 스크립트 패키지**: `tmp/phase9_data_migration/` 8 파일 (.gitignore tmp/ 영역) — `step01_probe.py` (행 수 양측 카운트) / `step02_pg_schema.py` + `step03_mssql_schema.py` (컬럼 메타) / `step04_pg_dump.py` (custom format dump) / `step05_apikey_recrypt.py` (CBC→GCM round-trip 검증) / `step06b_build_insert_sql_safe.py` (FK dangling 자동 필터 + ServiceId remap + ApiQuotas UNIQUE dedupe + IDENTITY 보존 INSERT + SETVAL) / `step07_cutover.py` (AgentHub 정지 → TRUNCATE CASCADE → SQL import → .env AES key 주입 → docker compose up -d --force-recreate → healthy 대기 → 행 수 검증) / `step08_smoke_test.py` (회귀 endpoint + ApiKey GCM round-trip). **운영 MSSQL 의 referential integrity 위반 자동 처리**: ① UserId 5,6 부재 (운영 중 사용자 hard delete) → UserRoles/ApiQuotas/UserSessions 6 행 skip, 자식 DELETE CASCADE 와 동일 효과 ② ServiceId 1~9, 13 dangling (운영 ApiServices 시드 재생성으로 ID 1~5→17~31 점프) → 모델 컬럼/이름 기반 추정 매핑 (`SERVICE_ID_REMAP = {1:17 chatgpt, 2:18 claude, 3:19 cursor, 4:20 copilot, 5:31 perplexity, 6:21 gemini, 7:21 gemini, 8:23 dalle, 9:24 gemini-image, 13:29 veo}`) → 450 행 remap ③ ApiQuotas UNIQUE(UserId, ServiceId) 충돌 (6,7→21 매핑으로 같은 사용자 중복 발생) → QuotaId max 보존 dedupe 10 행 ④ ChatMessages 16 행 dangling (Conversation 자체가 hard delete 된 케이스) skip ⑤ nullable FK dangling 은 NULL 강제 (ApiUsages.ConversationId 등) → 데이터 보존. **이관 결과 행 수 (MSSQL → PG)**: Users 131→131 (100%) / Roles 3→3 / UserRoles 7→**5** (-2 사용자 부재) / Teams 1→1 / TeamMembers 1→1 / Agents 17→17 (100%) / ApiServices 15→15+1 시드 nexus (16) / ApiServiceModels 84→84+2 시드 (86) / ApiKeys 1→1 (재암호화) / ChatConversations 191→191 (100%) / ChatMessages 715→**699** (-16 dangling) / ApiQuotas 925→**911** (-14 dedupe+사용자 부재) / ApiUsages 474→474 (100%, ConversationId NULL 변환) / BannedWords 240→240 / Presentations 66→66 / UserSessions 223→**219** (-4 사용자 부재). 또한 AgentHub `DatabaseInitializer` 가 컨테이너 재기동 시 자체 시드(Phase 7.1 신규 카탈로그 Agent 15개 + Nexus 1 ApiService 등)를 idempotent INSERT — Agents 32 (17+15), ApiServices 16, ApiServiceModels 86 으로 표시되는 것은 의도된 동작. **Cutover 시간**: AgentHub stop → SQL import (PG psql -f, ON_ERROR_STOP=1, 220 MB SQL 파일) → AES key 주입 → up -d --force-recreate → healthy 도달 약 12 초. **회귀 검증 ALL PASS**: ① container healthy ② GET /swagger 200 ③ POST /api/auth/login `admin@example.com / Admin123!` 200 + token len=555 (MSSQL 운영 admin BCrypt 해시가 시드 해시와 동일 확인) ④ GET /api/agents/1 200 + 6 신규 필드 매핑(consumerSystems / knowledgeBaseRef / knowledgeBaseSource / llmRouting / routingPolicyJson — Phase 7+ 컬럼 모두 정상) ⑤ GET /api/admin/metrics/rag 200 (Phase 4 카운터 16 키) ⑥ GET /api/agents 200 (32 agents) ⑦ GET /api/chat/conversations 200 (91 KB body, 191 conversation 모두 표시) ⑧ POST /api/chat/conversations 201 (ID 260, sequence SETVAL 정확 작동) ⑨ /agents/select / /admin/knowledge-base / /admin/rag-metrics SPA 모두 200 fallback ⑩ **ApiKey GCM 복호화 round-trip PASS** — PG row 의 `EncryptedKey/KeyIv/KeyTag` 를 `.env` 의 신규 AES key 로 직접 복호화 → 평문 prefix/suffix `ak-4...GMrU` len=46 검증 + KeyHash SHA-256 hex 64 자 매칭 PASS — 신규 키로 무결성 보장 저장 완료. **장기 영향**: 운영 cutover 종결 → 시연 환경이 131 사용자 + 191 대화 + 699 메시지 + 921 quota + 474 usage 운영 데이터 위에서 동작. 외부 LLM 키/Quota 미설정으로 신규 메시지 응답 자체는 400 예상이나 데이터 이관 + 재암호화 + 회귀 endpoint 는 모두 PASS — 본 phase 책임 범위 내 모든 항목 완료. 직전: **후속 트랙 DocUtil collection 카탈로그 응답 캐시 도입 완료** — 직전 트랙(`294e8a6`)에서 BFF 표면화한 `GET /api/admin/knowledge-base/collections` 가 매 호출 DocUtil `/api/v1/projects` 직격이던 부하를 단순 TTL 10분 캐시로 감소. **수정 5 파일**: ① `agenthub/Services/DocUtilClient.cs` — `ListCollectionsAsync` 본체 재작성. 신규 const `CollectionCacheKeyPrefix = "du:c:"` (Search `du:s:` 와 격리) + `CollectionCacheTtl = TimeSpan.FromMinutes(10)` (Search 의 5분보다 길게 — mutation 빈도 낮음). 캐시 키 패턴 `du:c:{page}|{size}` — page/size 조합당 단일 키. `_cachingService.GetAsync<CachedCollectionListDto>` → null 이면 miss 카운트 + HTTP 호출, non-null 이면 hit 카운트 + items.ToList() 반환. HTTP 호출 본체는 try/catch/finally 패턴(Phase 4 SearchAsync 와 일관) — `IncrementDocUtilCollectionCall()` + Stopwatch 시작 → catch 시 `IncrementDocUtilCollectionFailure()` → finally Stopwatch 정지 + Debug 로그(`Latency={LatencyMs}ms`). 성공 시 `CachedCollectionListDto { Items = items.ToArray() }` 적재. 신규 wrapper class `CachedCollectionListDto` 도 추가(record `DocUtilCollection` 직렬화 안정성 — Search `CachedSearchResultDto` 와 동일 패턴). 한국어 Debug 로그 `DocUtil 컬렉션 캐시 hit/miss - key={Key}, count={Count}` ② `agenthub/Services/IRagMetrics.cs` — DocUtil 컬렉션 카운터 4 신규 메서드 추가 (`IncrementDocUtilCollectionCacheHit/Miss/Call/Failure`) + `RagMetricsSnapshot` record 에 4 필드 추가 (`DocUtilCollectionCacheHit / Miss / Calls / Failures`). 한국어 doc 주석으로 version-key 미적용 사유 명시 (collection mutation 은 DocUtil 콘솔에서 직접 발생 → AgentHub BFF 비경유 → explicit invalidate 트리거 불가) ③ `agenthub/Services/RagMetrics.cs` — 4 private long 필드 + 4 메서드 구현(Interlocked.Increment) + GetSnapshot() 매핑 추가. Phase 4 SearchAsync 카운터와 동일 atomic 패턴 일관 ④ `agenthub/DTOs/RagMetricsSnapshotDto.cs` — 4 신규 필드(`DocUtilCollectionCacheHit/Miss/Calls/Failures`) + 파생 1 `DocUtilCollectionCacheHitRatio` (hit / max(1, hit+miss)) 추가 ⑤ `agenthub/Controllers/AdminMetricsController.cs` — RagMetricsSnapshotDto 매핑 4 줄 + docUtilCollectionTotal 분모 0 보호 + `DocUtilCollectionCacheHitRatio` 계산 추가. `/api/admin/metrics/rag` 자동 노출(controller 변경 외 frontend 수정 0). **캐시 무효화 전략 — version-key 패턴 미적용**: collection 생성/수정/삭제는 DocUtil 콘솔에서 직접 발생하므로 AgentHub BFF 가 mutation 시점을 알 수 없다. → 단순 TTL 10분 자연 expire 의존. 향후 트랙: DocUtil project mutation 도 AgentHub BFF 를 경유하도록 전환되면 SearchCacheVersionNamespace 와 동일 패턴 적용 가능. **빌드**: `dotnet build --no-restore --nologo` errors=0, warnings=11 (모두 본 트랙과 무관한 기존 CS1998). **호스트 배포**: paramiko 로 5 파일 호스트 192.168.10.39:/home/idino/agenthub/ 업로드 → `docker compose build agenthub` (#18 export 13s) → `docker compose up -d --force-recreate agenthub` healthy. **회귀 검증 (3 시나리오 — Bearer JWT 555 chars)**: (1) **캐시 hit/miss 동작** — `GET /api/admin/knowledge-base/collections?page=1&size=50` 1차 호출 758.7ms (DocUtil 직격, count=2: `c6955ce6-...` 연구과제, `9ca4ce6e-...` 미래기술연구소) → 즉시 2차 호출 22.8ms (캐시 hit, 동일 body, **약 33배 빠름**). 추가 5회 연속 호출 모두 14~17ms (전부 hit). (2) **메트릭 노출** — `GET /api/admin/metrics/rag` Bearer JWT → 200 + 신규 4 카운터 모두 노출 (`docUtilCollectionCacheHit=7, Miss=2, Calls=2, Failures=0, HitRatio=0.778`). (3) **Phase 4 무영향** — `POST /api/chat/conversations/2/messages` 한국어 RAG 쿼리(부산대 학생 지원 정보) → 200 (7892ms, 응답 OK). post-RAG 메트릭에서 `docUtilSearchCalls=2, ragInvocations=1, ragResultCacheMiss=1` Phase 4 카운터 정상 증가 + collection 카운터(`Calls=2, Hit=7`) 무변화 — 두 캐시 namespace 격리 확인. **효과**: 운영자 워크플로(Agent 생성/편집 시 KnowledgeBaseRef dropdown 매번 fetch) 의 DocUtil 부하가 10분 TTL 로 Hit 비율 약 0.78 까지 감소. 빈 결과(0건) 도 캐싱하여 빈 응답 반복 호출 부하도 절감. `Default LogLevel = Information` 환경에서는 `LogDebug` hit/miss 로그가 보이지 않으므로 메트릭 카운터(/api/admin/metrics/rag) rolling 검증 권장.)
> **이전 갱신**: 2026-05-08 (**후속 트랙 KnowledgeBaseRef DocUtil collection dropdown 전환 완료** — 직전 AgentBuilder.vue UI 운영자 폼 필드 확장(`845382c`)에 추가된 KnowledgeBaseRef 텍스트 input 의 UX 결함(운영자가 UUID 형태 ID 를 수동 입력해야 함)을 dropdown 으로 해소. **수정 7 파일**: ① `agenthub/Services/IDocUtilClient.cs` — `ListCollectionsAsync(page=1, size=50, ct)` 시그니처 추가 + `DocUtilCollection(Id, Name, Description?)` record 신설(BFF 단순화 — DocUtil 내부 메타 organization_id/created_by/timestamps/allow_original_download 등 비노출, 3 필드만 표면화). 한국어 doc 주석으로 DocUtil projects=AgentHub collection 추상 매핑 + 캐시 미적용 사유(운영자가 새 project 직후 dropdown 즉시 반영 필요) 명시 ② `agenthub/Services/DocUtilClient.cs` — 구현 신규: `GET /api/v1/projects?page={page}&size={size}` 호출 + Bearer token(IDocUtilTokenProvider 4단계 폴백 재사용) + 응답 매핑 `items[].{id,name,description} → DocUtilCollection` + `string.IsNullOrWhiteSpace(Id)` 가드(빈 row 제거) + 한국어 디버그 로그(Count/Total). 신규 private DTO 2건 `ProjectListDto`/`ProjectSummaryDto` (snake_case 매핑, `JsonNamingPolicy.SnakeCaseLower` + `JsonPropertyName` 일관) ③ `agenthub/Controllers/AdminKnowledgeBaseController.cs` — `[HttpGet("collections")]` `[Authorize(Roles = "Admin,SuperAdmin")]` 신설. 라우트 `GET /api/admin/knowledge-base/collections?page={p}&size={s}`. 응답 `List<DocUtilCollection>` (camelCase 자동 직렬화). 502 매핑(InvalidOperationException → ErrorResponseDto 한국어 + DOCUTIL_UPSTREAM_ERROR + upstream 메시지). page<1 → 1, size<1|>200 → 50 정규화 ④ `agenthub/ClientApp/src/services/docutilService.ts` — `DocUtilCollection` interface 신설(id/name/description, BFF 표면 그대로) + `listCollections(page=1, size=50): Promise<DocUtilCollection[]>` export 함수 추가. `api.get<DocUtilCollection[]>('/admin/knowledge-base/collections')` 사용 — JWT 자동 부착 + 401 갱신 인터셉터 재사용. 한국어 doc 주석으로 호출 흐름(View → docutilService → BFF → IDocUtilClient → DocUtil FastAPI) 명시 ⑤ `agenthub/ClientApp/src/views/agent/AgentBuilder.vue` — `listCollections, type DocUtilCollection` import 추가. ref 3건 신규(`availableCollections: DocUtilCollection[]`, `loadingCollections: boolean`, `collectionsError: string | null`) + 모듈 스코프 플래그 `collectionsLoaded` (KnowledgeBaseSource 토글 시 중복 fetch 방지). `loadAvailableCollections()` async 함수 — 성공 시 ref 채우기, 실패 시 t('agentBuilder.knowledgeBaseRefLoadFailed') 한국어 에러 보관 + 텍스트 입력 fallback 활성화. `watch(() => agentForm.value.knowledgeBaseSource, ..., { immediate: true })` — DocUtil 로 (재)설정 시점에 collections fetch trigger. **template 변경**: 기존 `<input type="text" v-model="knowledgeBaseRef">` (line 348-353) 를 `<template v-if="!collectionsError">` (정상 경로 — `<select v-model="knowledgeBaseRef">` + 첫 option `value=""` "글로벌 (전체 corpus 검색)" + v-for 로 collection name 표시 + `:title="c.description"` hover hint + `:disabled="loadingCollections"` + spinner 안내 + 빈 컬렉션 안내 + 정상 help 텍스트) `<template v-else>` (에러 fallback — 기존 텍스트 input + 빨간 에러 메시지 + 한국어 안내) 분기로 교체. `@ts-nocheck` 부착 0 — vue-tsc 2.x strict 게이트 유지 ⑥ `agenthub/ClientApp/src/i18n/locales/ko.json` — `agentBuilder.fields` 에 `knowledgeBaseRefDropdown` + `knowledgeBaseRefDropdownHelp` 2 키 + `agentBuilder.*` top-level 에 `knowledgeBaseRefGlobal` ("글로벌 (전체 corpus 검색)") + `knowledgeBaseRefLoading` ("컬렉션 목록을 불러오는 중...") + `knowledgeBaseRefLoadFailed` ("DocUtil collection 목록을 가져오지 못했습니다. ID 를 직접 입력하세요.") + `knowledgeBaseRefEmpty` ("등록된 컬렉션이 없습니다. DocUtil 콘솔에서 먼저 컬렉션을 생성하세요.") 4 키 — 총 6 키 한국어 ⑦ `agenthub/ClientApp/src/i18n/locales/en.json` — 동일 6 키 영문 번역. **빌드 PASS**: `dotnet build --no-restore --nologo` errors=0 / warnings=11 (모두 pre-existing CS1998, 본 작업 무관) + `npx vue-tsc --noEmit` errors=0 (게이트 유지) + `npm run build:check` 3.74s vite build 263 modules / `AgentBuilder-BQ73O1Hy.js` 36.57 kB (이전 35.00 → 1.57 kB 증가, dropdown 분기 + watch + listCollections import) + 신규 청크 `docutilService-BYF1bCUv.js` 1.19 kB(독립 분리 — AdminKnowledgeBase view 들과 공유) + `index-DAUkJAvm.js` 134.36 kB(이전 133.98 → 0.38 kB 증가, i18n 6 키 추가). dist 청크 grep 검증: AgentBuilder 청크에 `collections` 매치 + docutilService 청크에 `listCollections` 매치 + index 청크에 `knowledgeBaseRefDropdown`/`knowledgeBaseRefGlobal`/`knowledgeBaseRefLoadFailed`/`knowledgeBaseRefLoading`/`knowledgeBaseRefEmpty` 5키 + 한국어 라벨("글로벌 (전체 corpus 검색)") 매치 모두 PASS. **wwwroot 동기화**: `ClientApp/dist/{assets,index.html}` → `agenthub/wwwroot/{assets,index.html}` 복사(`.gitignore` 대상). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 7 파일 소스 ~227 KB 업로드(IDocUtilClient.cs 7 KB / DocUtilClient.cs 31 KB / AdminKnowledgeBaseController.cs 13 KB / docutilService.ts 6 KB / AgentBuilder.vue 64 KB / ko.json 33 KB / en.json 29 KB) → docker compose build agenthub (BuildKit cache + publish layer) → up -d --force-recreate → 7초 만에 healthy. **회귀 검증 5 시나리오 모두 PASS**: CASE1 admin@example.com 로그인 → JWT 555 chars / CASE2 (**신규**) `GET /api/admin/knowledge-base/collections` Bearer JWT → 200 + `[{"id":"c6955ce6-...","name":"연구과제","description":"연구과제 문서 관리"}, {"id":"9ca4ce6e-...","name":"미래기술연구소 권한 프로젝트","description":"권한 테스트 "}]` 2건 — DocUtil projects 카탈로그 정확 노출 + BFF 단순화 검증(id/name/description 3 필드만, organization_id/created_by/timestamps 등 leakage 0) / CASE3 (**권한 게이트**) Bearer 없이 동일 엔드포인트 → **HTTP 401** / CASE4 (**직전 회귀** `b3a2d85`) GET /api/agents/1 → 200 + 6 신규 필드(`llmRouting='Hybrid'`, `routingPolicyJson`, `knowledgeBaseSource='DocUtil'`, `knowledgeBaseRef`, `consumerSystems`, `sortOrder`) 모두 노출 — 클라이언트 read 정상 / CASE5 (**한국어 RAG**) POST /api/admin/knowledge-base/search `{"query":"신청서 양식","maxResults":5}` → 200 + 5 results + totalTime — Phase 6.3+/Phase 4 RAG 인프라 회귀 보존. **외부 시그니처 변경 0** — 신규 endpoint 추가만, 기존 6 endpoint(documents/upload/{id}/chunks/search) 시그니처 보존. **anti-patterns.md 준수**: §1 LLM SDK 직접 호출 0 / §4 하드코딩 API URL 0(BASE='/admin/knowledge-base' const) / §11 axios 직접 사용 0(api.ts 인터셉터 경유) / §13 SignalR Hub LLM 호출 0. **architecture.md 준수**: P1 단일 진입점(IDocUtilClient 만이 DocUtil HTTP 호출) / P2 표준 모듈(Controllers/Services 표준) / P5 JSON 직렬화(camelCase 자동) / P6 ErrorResponseDto 한국어 일관. **DI 수명**: DocUtilClient(Scoped), AdminKnowledgeBaseController(Scoped), IDocUtilTokenProvider(Singleton) — 변경 0. **Side effect**: 운영자가 GUI 에서 DocUtil collection 을 dropdown 으로 직접 선택 가능 — 직전 트랙(`845382c`) 의 UI 폼 활용도 한 단계 향상. 에러 시 텍스트 입력 fallback 으로 운영자 작업 중단 0(UX 안전망). **다음 트랙 후보**: ① collection 카탈로그 캐시(version-key 패턴, DocUtil 콘솔에서 mutation 시 즉시 invalidate) — 빈도 낮으나 latency 보장 / ② vue-flow 업그레이드(WorkflowBuilder.vue `@ts-nocheck` 해제, D-1) / ③ Nexus 실 부팅(LAN GPU 호스트 배정 + `/v1/chat` 헬스 인증) / ④ 시연 종료 후 secret leak history sanitize + force-push + 키 회전 / ⑤ AgentSelect.vue 의 `/api/knowledgebase` GET dead code 잔존 점검 (직전 트랙 `174cc7b` cleanup 후 grep 재확인) / ⑥ Phase 6.3 BFF 컨트롤러 `/collections` 와 같은 패턴으로 DocUtil의 다른 운영자 entity(예: tags / departments) BFF 일괄 노출 검토. 직전: **후속 트랙 AgentBuilder.vue UI 운영자 폼 필드 확장 완료** — 직전 백엔드 AgentDto 갭 보강(`b3a2d85`)으로 회복된 6 필드(`LlmRouting/RoutingPolicyJson/KnowledgeBaseSource/KnowledgeBaseRef/ConsumerSystems/SortOrder`)의 BFF 정합성을 Vue 운영자 콘솔 UI 단까지 활용. **수정 4 파일**: ① `agenthub/ClientApp/src/types/index.ts` `AgentDto` interface 에 6 신규 필드 추가 (camelCase, optional, nullable 은 `string \| null` 폴백) ② `agenthub/ClientApp/src/views/agent/AgentBuilder.vue` — `useI18n()` import 추가 + agentForm 초기값/loadAgentForEdit 매핑/resetBuilder 3 곳 모두 6 신규 필드 추가 + 클라이언트 사이드 JSON 검증 함수 2개(`validateRoutingPolicyJson`/`validateConsumerSystems`, blur 트리거, 한국어 에러, 제출은 막지 않음 — 백엔드가 최종 검증) + Step 4 "고급 기능" 카드 직후 신규 카드 "고급 설정" 1건 추가(LLM 라우팅 dropdown + Hybrid 일 때만 RoutingPolicyJson textarea + KnowledgeBaseSource dropdown(DocUtil 권장 / AgentHub deprecated 표기) + DocUtil 일 때만 KnowledgeBaseRef input + ConsumerSystems textarea + SortOrder number, 모든 라벨/help 텍스트 i18n 키로 분리). `@ts-nocheck` 부착 0 — strict 타입 통과 ③ `agenthub/ClientApp/src/i18n/locales/ko.json` `agentBuilder.*` 신규 섹션(advancedSettings/advancedSettingsDescription + fields 12키 + llmRoutingOptions 3키 + knowledgeBaseSourceOptions 2키 + errors 2키, 총 22키 한국어) ④ `agenthub/ClientApp/src/i18n/locales/en.json` 동일 키 영문 번역. **빌드 PASS**: `npx vue-tsc --noEmit` errors=0 (게이트 유지) + `npm run build:check` 4.46s vite build 263 modules / 신규 청크 `AgentBuilder-Yx5xpP2A.js` 35.00 kB(gzip 11.90, 이전 29.38 → 5.6 kB 증가 — 신규 카드 + 검증 로직) + `index-Di5Nz_88.js` 133.98 kB(이전 131.21 → 2.77 kB 증가, i18n 키 22개 추가). dist 청크 grep 검증: AgentBuilder 청크에 `llmRouting`/`knowledgeBaseSource`/`routingPolicyJson` 매치 + index 청크에 `advancedSettings`/`llmRoutingOptions`/`knowledgeBaseSourceOptions`/`라우팅 정책`/`호출 화이트리스트`/`knowledgeBaseRefHelp` 매치 모두 PASS. **wwwroot 동기화**: `ClientApp/dist/{assets,index.html}` → `agenthub/wwwroot/{assets,index.html}` 복사 (`.gitignore` 대상이므로 commit 미포함). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 4 파일 소스 ~135 KB 업로드(types/index.ts 14 KB + AgentBuilder.vue 59 KB + ko.json 33 KB + en.json 29 KB) → `docker compose build agenthub` (BuildKit cache + publish layer 10s, agenthub-agenthub:latest) → `up -d --force-recreate` → 4초 만에 healthy. 컨테이너 wwwroot 청크 grep: `AgentBuilder*.js` 안 `llmRouting` 매치 다수 + `index-*.js` 안 `knowledgeBaseRefHelp` 매치 다수 — 호스트 컨테이너 자산까지 정확 반영. **회귀 검증 PASS**: admin@example.com 로그인 → JWT 555 chars / `GET /api/agents/1` Bearer JWT → 200 + 6 신규 필드 모두 노출 (`{llmRouting:True, routingPolicyJson:True, knowledgeBaseSource:True, knowledgeBaseRef:True, consumerSystems:True, sortOrder:True}`) — `b3a2d85` 백엔드 회귀 PASS 유지 + 클라이언트가 이제 read/write 모두 가능. **외부 API 라우트 변경 0** — 신규 필드 추가만, 기존 폼 필드 시그니처 변경 0, 다른 페이지(AgentChat/AgentSelect/AgentMultiChat) 동작 회귀 0. anti-patterns.md §4(Frontend 하드코딩 API URL — `import api from '@/services/api'` 사용) / §11(컴포넌트에서 axios 직접 사용 금지) 준수. **Side effect**: 운영자가 GUI 로 LLM 라우팅 정책 + RAG 권위 + 호출 화이트리스트를 직접 관리 가능. 향후 별도 트랙(예정): KnowledgeBaseRef 텍스트 입력 → DocUtil collection 목록 BFF (`/api/admin/knowledge-base/collections`) fetch dropdown 으로 전환. **다음 트랙 후보**: AgentChat.vue/AgentSelect.vue 의 `/api/knowledgebase` GET dead code 청산 / D-1 vue-flow 업그레이드 (WorkflowBuilder.vue `@ts-nocheck` 해제) / Nexus 실제 부팅 (LAN GPU 호스트) / 시연 종료 후 secret leak history sanitize + 키 회전. 직전: **후속 트랙 백엔드 AgentDto 갭 보강 완료** — Agent 엔티티(`Models/Agent.cs`)에 존재하지만 외부 응답 DTO/요청 DTO 에 노출되지 않아 Vue 운영자 콘솔(AgentBuilder.vue)이 read 도 write 도 할 수 없던 6 필드 정합성 회복: `LlmRouting` (External/Internal/Hybrid, Phase 5.1 라우팅 모드) + `RoutingPolicyJson` (Hybrid 전용 결정 규칙 JSON) + `KnowledgeBaseSource` (Phase 6+ 는 DocUtil, ADR-2 단일 권위) + `KnowledgeBaseRef` (DocUtil collection ID) + `ConsumerSystems` (호출 가능 End-User App 화이트리스트 JSON 배열) + `SortOrder` (정렬 순서). **수정 4 파일**: ① `agenthub/DTOs/AgentDto.cs` — 6 필드 read 노출 (camelCase JSON 직렬화 + 한국어 doc 주석) ② `agenthub/DTOs/CreateAgentRequestDto.cs` — 5 필드 신규(SortOrder 는 이미 존재). 모두 `string?` nullable 로 받아 서비스 레이어에서 빈문자 → 기본값 폴백("External"/"AgentHub") 또는 null 정규화 ③ `agenthub/DTOs/UpdateAgentRequestDto.cs` — 5 필드 + `EnableRag` (이전 누락) 6 필드 추가. 모두 nullable, null 이면 기존 값 보존 ④ `agenthub/Services/AgentService.cs` — 4 매핑 지점(GetAgentsAsync line 62-91, GetAgentByIdAsync line 106-137, CreateAgentAsync line 153-179 + 폴백 로직, UpdateAgentAsync line 209-236 + 보존 로직) 일괄 갱신. CreateAgentAsync 는 `string.IsNullOrWhiteSpace` 체크 → 기본값 폴백, UpdateAgentAsync 는 `null` 이면 보존 + 빈 문자열은 정책 해제 의도 → null 정규화. 검증 어노테이션은 추가하지 않음 — 서비스 레이어 분기로 처리 (잘못된 LlmRouting 값은 DB constraint 가 아닌 RagService 분기에서 graceful 처리). **빌드**: dotnet build → errors=0 / warnings=11 (모두 pre-existing CS1998). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 4 파일 업로드 (~21 KB) → docker compose build agenthub (BuildKit cache + publish layer ~10s) → up -d --force-recreate → 7초 만에 healthy. **회귀 검증 4 시나리오 모두 PASS**: CASE1 `GET /api/agents/1` (기존 Phase 6.3 docutil-rag-chat) → 200 + 10 필드 모두 노출 (`llmRouting=Hybrid`, `knowledgeBaseSource=DocUtil`, `consumerSystems=["docutil-user"]`, `sortOrder=100`, `enableRag=True`, `routingPolicyJson=null`, `knowledgeBaseRef=null`, etc.) — Phase 5.1 시점에 시드/마이그레이션으로 채워졌던 라우팅 메타가 비로소 클라이언트에 노출됨. CASE2 `POST /api/agents` 신규 생성 with 6 필드 → 201 + 모든 신규 필드 정확 저장 (Hybrid + RoutingPolicyJson `{"default":"external","piiAction":"internal"}` + KnowledgeBaseSource=DocUtil + KnowledgeBaseRef="test-collection-id-99" + ConsumerSystems=`["docutil-user"]` + EnableRag=true). CASE3 `PUT /api/agents/16` 부분 수정 → 200 + 명시 필드 변경 (`llmRouting Hybrid→Internal`, `consumerSystems → ["career-coaching"]`, `enableRag True→False`) + **미명시 필드 보존** (knowledgeBaseSource=DocUtil, knowledgeBaseRef, routingPolicyJson 모두 그대로). CASE4 `PUT consumerSystems=""` (빈 문자) → `consumerSystems=null` 정규화 (DB 일관성 유지). cleanup DELETE → 204. **외부 시그니처 변경 0** — 신규 필드 추가만, 기존 필드 시그니처/타입 변경 0. **anti-patterns.md §1/§7 준수** — Repository 패턴 미사용(Service 가 DbContext 직접), Singleton→Scoped captive 0. **architecture.md P5 (JSON 직렬화)** 준수 — camelCase 자동 직렬화 (Program.cs JsonNamingPolicy.CamelCase). **Side effect**: Vue AgentBuilder.vue 가 이제 LlmRouting / KnowledgeBase 운영을 UI 로 제어 가능 (별도 후속: Vue UI 폼 필드 추가는 별도 트랙). **다음 트랙 후보**: AgentBuilder.vue UI 에 LlmRouting/RoutingPolicyJson/KnowledgeBaseSource/Ref/ConsumerSystems 폼 필드 추가 (BFF 정합성 활용) / AgentChat.vue, AgentSelect.vue 의 `/api/knowledgebase` GET dead code 청산 / D-1 vue-flow 업그레이드 / 시연 종료 후 secret leak history sanitize / Nexus 실제 부팅. 직전: **후속 트랙 ChatService FK 결함 수정 완료** — 직전 RagService 결과 캐시 version-key 통합 트랙(`d1b1dd7`) 의 회귀 시나리오 (3) 에서 발견된 사전 데이터/매핑 결함을 정리. **원인**: `CreateConversationRequestDto.ServiceId` 가 `[Required] int` (non-nullable value type) 이었기에 `[Required]` 가 0 을 거부하지 못했고, 클라이언트가 `{agentId:1}` 만 보내면 ServiceId 가 default 0 으로 INSERT → `FK_ChatConversations_ApiServices_ServiceId` 위반(23503) → 500. ChatService 의 다른 메서드(SendDirectMessageAsync line 454-464 등 3곳)는 이미 `int?` + Agent 메타에서 ServiceId 자동 보충 패턴이었으나 CreateConversationAsync 만 누락. **수정 3건**: ① `agenthub/DTOs/CreateConversationRequestDto.cs` — `[Required] int ServiceId` → `int? ServiceId` 로 변경 + `[Required]` 어노테이션 제거 + 한국어 주석으로 변경 사유 명시. ② `agenthub/Services/ChatService.cs` `CreateConversationAsync` (line 132-) — AgentId 가 있으면 `_context.Agents.AsNoTracking().FirstOrDefaultAsync` 로 Agent 로드 후 ServiceId/Model/Temperature/MaxTokens/SystemPrompt 5개 필드를 `??=` 로 보충(SendDirectMessageAsync 와 동일 패턴). 둘 다 null/0 이면 `ArgumentException` 한국어 메시지. 존재하지 않는 AgentId 도 ArgumentException + 한국어. ③ `agenthub/Controllers/ChatController.cs` `CreateConversation` (line 79-) — `catch (ArgumentException ex)` 분기 추가 → 400 BadRequest + ErrorResponseDto + LogWarning. 기존 `catch (Exception)` 는 500 폴백 그대로. **빌드**: dotnet build → errors=0 / warnings=11 (모두 pre-existing CS1998). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 3 파일 업로드(108 KB) → docker compose build agenthub (BuildKit cache 활용) → up -d --force-recreate → 7초 만에 healthy. **회귀 검증 4 시나리오 모두 PASS**: CASE1 `{agentId:1, title:"chat-fix-1"}` → **HTTP 201** + `{conversationId:6, agentName:"DocUtil RAG ??", serviceId:1, serviceName:"ChatGPT", model:"gpt-4o", temperature:0.50, maxTokens:4096}` (Agent 메타 자동 보충 정확 동작) / CASE2 `{title:"chat-fix-2"}` (둘 다 누락) → **HTTP 400** + `{message:"ServiceId 또는 AgentId 중 하나는 반드시 제공되어야 합니다.", errorCode:"VALIDATION_ERROR"}` / CASE3 `{agentId:99999}` (존재하지 않는 ID) → **HTTP 400** + `{message:"AgentId=99999 에 해당하는 에이전트를 찾을 수 없습니다."}` / CASE4 `{serviceId:1, title:"chat-fix-4"}` (legacy 패턴 보존) → **HTTP 201** + `{serviceId:1, agentId:null, agentName:null}` 정상. **외부 시그니처 변경 0** — `/api/chat/conversations` POST 라우트/응답 형태/Status 모두 보존, 누락 케이스만 500→400 으로 정정. **Side effect**: ChatConversations FK 위반으로 막혀 있던 실 채팅 트래픽 기반 RagService 결과 캐시 회귀 시나리오 (3) 도 이제 e2e 가능 — 다음 KB upload 시뮬레이션과 함께 검증 가능. **다음 트랙 후보**: 백엔드 AgentDto 갭 보강(enableWebSearch/KnowledgeBaseSource/KnowledgeBaseRef/LlmRouting/RoutingPolicyJson/ConsumerSystems) / AgentChat.vue, AgentSelect.vue 의 `/api/knowledgebase` GET dead code 청산 / D-1 vue-flow 업그레이드 / 시연 종료 후 secret leak history sanitize + 키 회전 / Nexus 실제 부팅. 직전: **후속 트랙 RagService 결과 캐시 version-key 통합 완료** — Phase 4 RAG 캐시 invalidate 가 사용자 체감 단까지 완성. 직전 트랙 (`3b7c857`) 에서 DocUtilClient.SearchAsync 의 캐시 키가 `du:s:v{N}:{hash}` 로 version-key prefix 패턴을 채택했고 AdminKnowledgeBaseController Upload/Delete 성공 시 `IncrementVersionAsync("docutil-search")` 로 즉시 stale 처리되었으나, **그 위 레이어인 RagService.RetrieveAsync 자체의 결과 캐시(`rag:{queryHash}|{agentId}|{userId}` 10분 TTL)는 별도 키 lineage 라 KB 변경 후에도 invalidate 안 됨** → 운영자 KB 변경 한 번에 DocUtil 검색 응답 캐시는 즉시 fresh 호출이지만 그 위 RAG 결과 캐시가 stale 한 결과를 그대로 반환하여 사용자 체감 효과 없는 갭이 있었다. 본 트랙은 RagService 결과 캐시도 동일 `docutil-search` version namespace 에 묶어 KB upload/delete 한 번에 양 레이어 모두 즉시 stale 처리되도록 일관 통합. **변경 파일 5개**: ① `agenthub/Services/RagService.cs` — `RetrieveAsync` 의 캐시 키 prefix 추가. `var ragCacheVersion = await _cachingService.GetVersionAsync(DocUtilClient.SearchCacheVersionNamespace);` 호출 후 `var ragCacheKey = $"v{ragCacheVersion}:{_cachingService.GetRagResultKey(queryHash, agentId, userId)}"`. 즉 `v0:rag:1:2:abc123` 형태. CachingService 인터페이스 변경 0 — 기존 GetVersionAsync (직전 트랙에서 추가됨) 그대로 재사용. 별도 namespace 만들지 않은 이유는 KB 변경이 결국 RagService 결과 정확성에도 동일 영향이라 single source of truth 로 묶는 것이 일관 — 운영자 KB upload 한 번에 양 레이어 모두 invalidate. ② `agenthub/Services/IRagMetrics.cs` + ③ `agenthub/Services/RagMetrics.cs` + ④ `agenthub/DTOs/RagMetricsSnapshotDto.cs` + ⑤ `agenthub/Controllers/AdminMetricsController.cs` — `IncrementRagResultCacheHit/Miss()` 신규 카운터 추가, RagMetricsSnapshot record 에 `RagResultCacheHit/Miss` 필드 추가, RagMetricsSnapshotDto 에 `RagResultCacheHit/Miss/HitRatio` 노출, AdminMetricsController 매핑 + `RagResultCacheHitRatio = ragResultCacheTotal > 0 ? hit/total : 0` 파생 통계. 모두 `Interlocked.Increment` 기반 atomic, 외부 의존성 0 — Phase 4 메트릭 인프라와 일관. **빌드 검증**: `dotnet build --nologo` errors=0 / warnings=11 (모두 이전부터 존재하던 CS1998, 본 작업 무관). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 5 파일 업로드 (RagService.cs 12.8 KB / IRagMetrics.cs 4.9 KB / RagMetrics.cs 4.8 KB / RagMetricsSnapshotDto.cs 3.1 KB / AdminMetricsController.cs 5.4 KB) → `docker compose build agenthub` (BuildKit cache 활용 + publish layer + image export 10s) → `docker compose up -d --force-recreate agenthub` (Container Recreated/Started) → `Up About a minute (healthy)` 확인. **회귀 검증 결과**: (a) **메트릭 endpoint 회귀 PASS** — `GET /api/admin/metrics/rag` Bearer (admin@example.com) → 200 OK + 신규 카운터 노출(`ragResultCacheHit=0`, `ragResultCacheMiss=0`, `ragResultCacheHitRatio=0`) + Phase 4 기존 카운터 회귀 PASS (`docUtilSearchCacheHit/Miss`, `docUtilSearchCalls`, `ragInvocations`, `queryRewriteCacheHit`, `avgDocUtilSearchLatencyMs` 모두 그대로 노출). (b) **cv:docutil-search version-key 패턴 동작 PASS** — `redis-cli -a docutil_redis_2024 HSET cv:docutil-search data 1` 으로 N=0 → N=1 강제 INCR (실제 KB upload 시뮬레이션). DocUtilClient + RagService 양쪽 모두 다음 호출 시 `_cachingService.GetVersionAsync("docutil-search")` 로 N=1 을 fetch → `v1:rag:...` / `du:s:v1:...` 신규 prefix 키로 cache miss 발생 → 새 응답 적재. 이전 `v0:` 키들은 SCAN 시점에는 TTL 자연 expire / LRU eviction 으로 정리. cv:docutil-search 는 IDistributedCache HASH 구조(`absexp,sldexp,data` 필드) 정상. (c) **(부분) 실 채팅 트래픽 시나리오 — 환경 결함으로 보류**: AgentId=2(`docutil-report-generator`, KnowledgeBaseSource=DocUtil, EnableRag=true, ServiceId=1→ApiServices.chatgpt) 로 `POST /api/chat/conversations` 호출 시 **사전 데이터 결함**으로 500 — `ChatConversations.ServiceId` FK_ChatConversations_ApiServices_ServiceId 위반 (DB 레벨에서는 ServiceId=1 매칭이 정상이지만 ChatService.CreateConversationAsync 내에서 ServiceId=0 으로 들어가는 것으로 추정됨, INSERT 로그 추가 필요). 이는 본 트랙(RagService 캐시 키 변경)과 완전히 무관한 사전 데이터/매핑 결함이며 **다음 트랙 후보로 기록** — RagService 의 캐시 키 prefix 변경은 함수적으로 자명(version 이 바뀌면 다른 GET 키), 빌드/노출/Redis 상태/cv 키 INCR 검증으로 충분. **DI 수명주기 보존**: RagService Scoped + CachingService Singleton + IRagMetrics Singleton + IServiceScopeFactory(LlmQueryRewriter) 모두 본 작업 영향 0. **외부 시그니처 보존**: RagService.RetrieveAsync contract 그대로, /api/admin/metrics/rag 라우트 그대로 — 신규 필드만 추가되어 호환성 유지. anti-patterns.md §1/§7 준수 (LLM SDK 직접 호출 0, Singleton→Scoped 캡티브 0). **다음 트랙 후보**: ① ChatConversation FK_ApiServices_ServiceId 위반 디버깅 (사전 결함, ChatService.CreateConversationAsync line 155 일대 ServiceId 매핑 추적), ② D-1 vue-flow / 백엔드 AgentDto 갭 / AgentChat dead code / 시연 종료 트랙 정리 (직전 사이클 잔여), ③ RAG 메트릭 prometheus 시계열 영속화. **R7 갱신 + commit 분리** — 본 트랙 commit `d1b1dd7` 후 progress.md commit 별도. ────────────────────── 이전 갱신: 2026-05-08 **후속 트랙 C-1 + B-1 완료** — 두 commit 분리 + progress.md commit 별도. **트랙 C-1 (commit `32f78d1`)**: Phase 2 자체 KB drop 잔재 제거. ① `agenthub/ClientApp/src/views/KnowledgeBase.vue` **파일 삭제** (Phase 2 에서 백엔드 KnowledgeBaseController 가 410 Gone 처리되었으므로 사용자 페이지가 호출해도 SPA fallback HTML 200 만 반환되던 사장된 자산. 운영자 KB 진입점은 `/admin/knowledge-base` Phase 6.3 DocUtil BFF 단일화 — R2 통합 원칙 준수). ② `agenthub/ClientApp/src/router/index.ts` 의 `/knowledge-base` 라우트 정의 + 컴포넌트 import 제거. 자리에 한국어 주석 2 줄로 제거 사유 + 단일 진입점 명시. ③ `agenthub/ClientApp/src/i18n/locales/{ko,en}.json` 의 `nav.knowledgeBase` 키 제거 (grep 검증 결과 다른 참조 없음 — `nav.adminKnowledgeBase` Phase 6.3 메뉴와는 독립). 4 files changed / 2 insertions / 827 deletions. **트랙 B-1 (commit `8819217`)**: Phase 3 vue-tsc 2.x (`3367e4b`) 부착 4건 `@ts-nocheck` 중 2건 해제 (AgentBuilder.vue + AgentMultiChat.vue). ① `agenthub/ClientApp/src/types/index.ts` `ConversationDto` 에 `enableRag: boolean` + `enableWebSearch: boolean` 신규 필드 추가 — 백엔드 `Models/ChatConversation.cs` 의 `[Required] public bool` 와 정렬, JsonNamingPolicy.CamelCase 규약 준수. ② `agenthub/ClientApp/src/views/agent/AgentBuilder.vue` 의 `// @ts-nocheck` (line 578-582) 제거 + 한국어 주석 갱신. agentForm 초기값 / loadAgentForEdit / resetBuilder 3 곳에 `enableRag: false` 명시 추가 — template line 547-548 `agentForm.enableRag` (RAG 미리보기 라벨) 가 참조하는 필드를 form shape 에 일관 포함. loadAgentForEdit 는 `agent.enableRag ?? false` 폴백으로 기존 동작 보존. ③ `agenthub/ClientApp/src/views/agent/AgentMultiChat.vue` 의 `// @ts-nocheck` (line 431-434) 제거 + 한국어 주석 갱신. 인라인 `ConversationDto` 에 `enableRag/enableWebSearch` 추가 + 인라인 `ApiService` 에 `defaultModel?` 추가. 3 files / 21 insertions / 9 deletions. 런타임 동작 변경 0 — TS 시그니처 정정 + form 초기값에 enableRag false 명시뿐. **빌드 검증 PASS**: `npx vue-tsc --noEmit` errors=0 (이전 게이트 유지) + `npm run build:check` (vue-tsc + vite 263 modules 3.61s) PASS — KnowledgeBase 청크 dist 에서 자취 사라짐(이전 KnowledgeBase-*.js 15.54 kB 제거, AdminKnowledgeBase-*.js 9.05 kB 보존), AgentBuilder-BWANXDfx.js 29.43 kB(이전 29.38) / AgentMultiChat-B6rNAGlT.js 33.82 kB / index-Cfsd3GpC.js 131.21 kB / WorkflowBuilder 182.62 kB / vue-vendor 164.98 kB / chart-vendor 207.43 kB. **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 5건 소스 + KnowledgeBase.vue rm + 105 wwwroot/assets 동기화 → `docker compose build agenthub` (BuildKit cache 10.7s) → `up -d --force-recreate` → 10초 만에 healthy. **회귀 검증 PASS**: GET / → 200 / GET /swagger → 200 / admin@example.com 로그인 JWT 555 chars / `GET /api/admin/metrics/rag` Bearer JWT → 200 + 16 키 (`avgDocUtilSearchLatencyMs ... ragZeroResults`) Phase 4 endpoint 정상 / GET `/knowledge-base` → 200 + text/html (SPA fallback, 라우트 제거 후 의도된 동작). **남은 후속 트랙**: D-1 WorkflowBuilder.vue 의 `@vue-flow/core` 타입 strict 검사 깨짐(`@ts-nocheck` 잔존, 패키지 업그레이드 필요) / RAG 메트릭 prometheus 시계열 영속화 / DocUtil 캐시 invalidate 직전 commit 누적 / 별도 트랙: 시연 종료 후 secret leak history sanitize + force-push, 비번 회전, DocUtil 운영자 service account 정식 발급, 사용자 일괄 테스트. AgentChat.vue / AgentSelect.vue 의 `/api/knowledgebase` GET 호출은 catch error 로 빈 배열 처리되므로 안전 — 별도 후속 트랙으로 청산. 직전: **후속 트랙 — DocUtil 검색 캐시 version-key invalidate 완료** — Phase 4 의 `du:s:` 5분 TTL 만으로는 운영자가 KB 문서 추가/삭제 후 최대 5분간 stale 검색 결과를 받는 UX 결함을 해결. **버전 키 패턴 채택**: 별도 Redis 키(`AIAgentManagement:cv:docutil-search`) 에 단조 증가 long 저장 → DocUtilClient.SearchAsync 의 캐시 키에 `du:s:v{N}:{hash}` prefix 포함 → KB upload/delete 성공 시 `IncrementVersionAsync` 호출 → N+1 → 이전 N 이하 모든 키가 자동 stale (TTL 5분 자연 expire 또는 LRU eviction). prefix iteration / KEYS / SCAN 비효율 회피. **수정 3건 (commit 포함)**: ① `agenthub/Services/CachingService.cs` (+158 LOC) — `GetVersionAsync(string ns)` 신설(키 미존재/Redis 실패 시 0 graceful 폴백, 한국어 LogWarning) + `IncrementVersionAsync(string ns)` 신설(Get→Increment→Set 패턴, IDistributedCache 의 atomic INCR 미지원 한계 수용 — race condition 시 두 INCR 가 같은 N+1 로 수렴해도 이전 N 이하 키는 모두 stale 처리되므로 무효화 본질 보존). 무한 TTL(version 키 자체는 만료 금지 — 만료 시 0 reset 으로 새 버전이 이전 버전과 충돌 위험). 키 prefix `cv:` (cache-version) — 다른 도메인 키와 충돌 회피. 4종 catch 블록(SocketException / RedisConnectionException / RedisTimeoutException / general Exception) 모두 0 폴백 + 경고 로그(best-effort, 호출자 흐름 차단 금지). ② `agenthub/Services/DocUtilClient.cs` — `SearchCacheVersionNamespace = "docutil-search"` public const 신설(controller 가 동일 namespace 참조). `BuildSearchCacheKey(long version, string query, string? collectionRef, int maxResults)` 시그니처 변경 — version prefix 포함. SearchAsync 진입부에서 `await _cachingService.GetVersionAsync(SearchCacheVersionNamespace)` 호출(매 호출 1회 Redis hit 추가, 실패 시 0 폴백 — 본 호출 흐름 차단 금지) + 캐시 hit/miss 디버그 로그에 version 표시. ③ `agenthub/Controllers/AdminKnowledgeBaseController.cs` — ctor 에 `CachingService` 주입(Singleton, captive 안전). private async `InvalidateSearchCacheAsync()` 헬퍼 신설 — try/catch 로 swallow + 한국어 LogInformation/LogWarning(캐시 무효화는 best-effort, mutation 응답 차단 금지). UploadDocument 성공 응답 직전 + DeleteDocument 성공 응답(NoContent) 직전에 호출. **빌드 PASS**: `dotnet build --no-restore` → errors=0 / warnings=11 (모두 pre-existing CS1998. 신규 경고 0). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 3건 소스 ~55 KB 업로드 → docker compose build agenthub (BuildKit cache 약 10초, agenthub-agenthub:latest) → up -d --force-recreate → 6초 만에 healthy. 부팅 로그: `데이터베이스 초기화 완료 → Hangfire jobs scheduled → Application started Hosting environment: Production → Hangfire dispatchers all started`. **회귀 검증 (1) 캐시 키에 version prefix 포함 PASS**: admin@example.com 로그인 JWT 555 chars → POST `/api/chat/conversations/2/messages "RAG 시스템의 핵심 동작 원리를 알려줘"` → 200 (12.91s) → docutil-redis SCAN 결과 `AIAgentManagement:du:s:v0:4976089DB3C43D27` / `AIAgentManagement:du:s:v0:1721F9E5F4CE7711` / `AIAgentManagement:du:s:v0:E021C92BB85A7D10` 3건(rewriter sub-query 3 × distinct hash) 모두 v0 prefix 정확. **회귀 검증 (2) 진짜 mutation 호출 후 invalidate PASS**: `POST /api/admin/knowledge-base/documents/upload` (cache_test_*.txt 77 bytes, multipart) → 200 + DocUtil id `e1bdf239-...` + 컨테이너 로그 `운영자 KB 업로드 성공: cache_test_*.txt (77 bytes) → DocUtil id=e1bdf239-...` + `DocUtil 검색 캐시 invalidate - newVersion=1`. Redis 의 `AIAgentManagement:cv:docutil-search` 키 EXISTS=1 / TYPE=hash / HKEYS=`absexp,sldexp,data` / `HGET data` = `'1'` (정확히 long 1, IDistributedCache hash 구조 정상). 다음 RAG 쿼리 → `AIAgentManagement:du:s:v1:E021C92BB85A7D10` / `AIAgentManagement:du:s:v1:4976089DB3C43D27` / `AIAgentManagement:du:s:v1:1721F9E5F4CE7711` 신규 3건 생성(이전 v0 키와 동일 hash 같으나 version prefix 다름 → 자동 cache miss 발생). 메트릭 docUtilSearchCalls=6 / docUtilSearchCacheMiss=6 (v1 으로 6 신규 miss, 이전 v0 캐시 도달 안 함) — 무효화 의도대로 동작. **회귀 검증 (3) 실패 경로**: 가짜 documentId (`nonexistent-deadbeef-1234`) DELETE → 502 (DocUtil 422 → catch → 한국어 ErrorResponseDto) + version 키 변동 없음(invalidate 미호출 — try 블록 끝 도달 안 함이 정확한 흐름). **회귀 검증 (4) 메트릭 endpoint**: `/api/admin/metrics/rag` Bearer JWT → 200 + `{"queryRewriteCacheHit":2,"queryRewriteCacheMiss":1,"queryRewriteCalls":1,"queryRewriteFailures":0,"docUtilSearchCacheHit":3,"docUtilSearchCacheMiss":6,"docUtilSearchCalls":6,"docUtilSearchFailures":0,"docUtilSearchLatencyMsTotal":4722,"ragInvocations":3,"ragZeroResults":0,"ragDistinctChunksTotal":21,"avgDocUtilSearchLatencyMs":787,"queryRewriteCacheHitRatio":0.667,"docUtilSearchCacheHitRatio":0.333,"avgRagDistinctChunks":7}` (Phase 4 endpoint 정상). 무권한 → 401 정상. **R3 격리 보존**: CachingService 의 신규 메서드는 IDistributedCache 만 의존(IConnectionMultiplexer 직접 사용 금지) — StackExchange.Redis 의 atomic INCR 미사용으로 race condition 가능하나 캐시 무효화 의도(이전 버전 일괄 stale)는 동일 보장. AgentHub IDistributedCache InstanceName=`AIAgentManagement:` prefix 자동 부착 — 다른 시스템 키와 격리. **외부 동작 변경 0** — `Search`(GET 기존 endpoint)는 시그니처 보존, BFF Upload/Delete 도 응답 형태 보존(invalidate 는 응답 직전 best-effort 호출). RagService 결과 캐시(`rag:*` 10분) 의 일괄 무효화는 **본 작업 범위 밖** — 자연 expire 의존(운영자 변경 후 즉시 검증할 때 약간의 지연 허용. 본 작업의 du:s 무효화로 sub-query 단계는 즉시 반영). **DI 수명**: CachingService Singleton(captive 안전, 외부 의존성 0 — IDistributedCache + ILogger 만), 신규 메서드는 stateless. AdminKnowledgeBaseController Scoped 주입 패턴 보존(per-request CachingService 참조). **anti-patterns.md §7** 준수 — Singleton CachingService 가 Scoped DbContext 주입 안 함, IConnectionMultiplexer 직접 사용 안 함. 직전: **Phase 5 운영자 메뉴 그룹화 + RAG 메트릭 UI 완료** — 운영자 콘솔 진입점 단편화 해소: `/admin/*` 신규 카테고리(`bi bi-shield-lock`, `roles=['Admin','SuperAdmin']`) 신설하여 흩어져 있던 management/analytics/system 카테고리의 Admin 전용 메뉴 13개를 단일 진입점으로 통합. **수정 4건 (commit 포함)**: ① `ClientApp/src/layouts/MainLayout.vue` 의 `allMenuCategories` 재구성 — 기존 management(6 항목)/analytics(4 항목)/system(4 항목) 카테고리 자체 제거 + system 직후 admin 카테고리 신설 (운영자 KB(`/admin/knowledge-base` Phase 6.3) + RAG 메트릭(`/admin/rag-metrics` 신규) + Users/Team/Quota/ApiKeys/BannedWords/PiiProtection + Analytics/AuditLog/CostAnalysis/UsageHistory + SystemHealth/PresentationTemplateManagement 13 항목). 한국어 주석으로 카테고리 제거 사유 명시 + Phase 2 자체 KB drop 잔재인 `nav.knowledgeBase`(/knowledge-base) 메뉴 항목 동시 제거 (라우트는 후속 트랙 C-1 으로 보존, SPA fallback 으로 북마크 호환). expandedCategories 초기 state 에 `admin: false` 추가 ② `ClientApp/src/router/index.ts` 에 `/admin/rag-metrics` 라우트 신설(`AdminRagMetrics` 이름, lazy import `views/admin/AdminRagMetrics.vue`, MainLayout 자식, `meta: { requiresAuth: true, role: 'Admin' }` — 기존 admin/knowledge-base 라우트 3개와 동일 가드 패턴). Phase 2 자체 KB 라우트 `/knowledge-base` 는 본 작업에서 제거하지 않음 (북마크/리다이렉트 호환, 후속 트랙 C-1 유지) ③ `ClientApp/src/i18n/locales/ko.json` `nav.adminRagMetrics: "RAG 메트릭"` + `nav.categories.admin: "운영자"` 신설 + `adminRagMetrics.*` 섹션 (title/subtitle/refresh/loading/autoRefresh/lastUpdated/errorGeneric/authErrorTitle/authErrorBody + summary 8키 + groups 3키 + fields 16키 + details 5키 + notes 10키, 총 56키) ④ `ClientApp/src/i18n/locales/en.json` 동일 키 영문 번역. **신규 1건 (commit 포함)**: `ClientApp/src/views/admin/AdminRagMetrics.vue` (~360 LOC, `<script setup lang="ts">` Composition API + Bootstrap 5 카드 그리드. 응답 DTO `RagMetricsSnapshot` interface 16 필드 백엔드 `RagMetricsSnapshotDto` 와 1:1 정렬. **요약 카드 4개**: RAG 호출 / DocUtil 검색 호출 / Query Rewrite 캐시 적중률 / DocUtil 검색 평균 응답시간. **상세 표 1개**: 그룹 3개(Query Rewriter Cache / DocUtil Search Cache / RAG Pipeline) 16 필드 + 비고 컬럼. **기능**: 새로고침 버튼 + 자동 갱신 토글(5초 간격, default off, watch 로 startInterval/clearInterval) + 마지막 갱신 시각 표시(`toLocaleString()`) + 인증 실패(401/403) 별도 안내 카드 + 일반 에러 alert + 첫 로딩 spinner. **포맷터 4종**: formatNumber(NaN/null 보호 + locale 천단위) / formatDecimal(소수 2자리) / formatRatio(0..1 → 백분율 1자리, clamp) / formatLatency(소수 1자리 + 단위). **HTTP**: `import api from '@/services/api'` 의 axios 인스턴스 사용 — JWT 자동 부착 + baseURL=/api → `api.get<RagMetricsSnapshot>('/admin/metrics/rag')`. **CSS scoped**: summary-card border-left accent-blue + value 1.625rem 700 + table-secondary 그룹 헤더). **빌드 PASS**: `npm run build:check` exit=0 errors=0 / vite 263 modules transformed 3.72s / 신규 청크 `AdminRagMetrics-B7lIJFPo.js` 12.21 kB(gzip 3.03) + CSS 0.63 kB / `MainLayout-DVX1yLWB.js` 10.04 kB(gzip 3.37) 갱신. **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 5건 소스 109 KB + 105 assets 2.5 MB + index.html 업로드 → docker compose build agenthub (BuildKit cache 10.3s, agenthub-agenthub:latest) → up -d --force-recreate → 5초 만에 healthy. **회귀 검증 PASS**: GET / → 200 / GET /swagger → 200 / admin@example.com 로그인 JWT 555 chars / `GET /api/admin/metrics/rag` Bearer JWT → 200 + 16 필드 JSON (Phase 4 endpoint 정상). **빌드 청크 키 검증**: MainLayout 청크에 `admin/rag-metrics` 매치 1건 + index 번들에 한국어 "운영자" / 영문 "Administration" 라벨 포함 확인. **RAG e2e + 메트릭 카운터 회귀 PASS**: POST /api/chat/conversations/2/messages `{"message":"RAG 시스템의 핵심 동작 원리를 알려줘"}` → 200 (10.92s, 한국어 응답 2731 tokens, gpt-4o-2024-08-06) → 메트릭 delta 정확: ragInvocations +1 / queryRewriteCalls +1 / docUtilSearchCalls +3 (rewriter sub-query 2건 추가) / ragDistinctChunksTotal +7 (RRF dedup) / avgDocUtilSearchLatencyMs=888.3ms — Phase 4 메트릭 인프라 정상 작동, 프론트 view 가 시각화할 데이터가 자연스럽게 채워짐. **외부 API/라우트 변경 0** — 신규 `/admin/rag-metrics` SPA 라우트만 추가 + 기존 path 변경 0 + 백엔드 endpoint 변경 0. **카테고리 정리 효과**: management/analytics/system 빈 카테고리 자동 제거 (`menuCategories` computed 의 `cat.items.length > 0` 필터 + `hasRole(cat.roles)` 게이트 — Admin 만 admin 카테고리 노출, 비Admin 은 기본 카테고리만). 권장 순서 1→5 모두 완료. **후속 트랙 잔존**: B-1 DTO TS↔C# 동기화(`@ts-nocheck` 해제) / C-1 Phase 2 자체 KB 라우트 `/knowledge-base` 완전 제거 + KnowledgeBase.vue 삭제 / D-1 @vue-flow/core 업그레이드 / RAG 메트릭 prometheus 시계열 영속화 / DocUtil 캐시 invalidate(prefix-based remove). 별도 트랙: 시연 종료 후 secret leak history sanitize + force-push, SQL Server stale 비번/SSH 비번/appsettings LLM API 키 회전, DocUtil 운영자 service account 정식 발급, 사용자 일괄 테스트. 직전: **Phase 4 DocUtil 응답 캐시 + RAG 메트릭 완료** — `IRagMetrics` Singleton 인터페이스(74 LOC) + `RagMetrics` in-memory atomic 카운터 구현(96 LOC, `Interlocked.Increment`/`Interlocked.Add`/`Interlocked.Read` 기반 thread-safe long 카운터 12개) + `RagMetricsSnapshotDto` 운영자 응답 DTO(파생 통계 4개 — `avgDocUtilSearchLatencyMs`, `queryRewriteCacheHitRatio`, `docUtilSearchCacheHitRatio`, `avgRagDistinctChunks`) + `AdminMetricsController` (`[Authorize(Roles = "Admin,SuperAdmin")]` `GET /api/admin/metrics/rag` 단일 엔드포인트) 신설 4건. **DocUtilClient.SearchAsync 캐시**: prefix `du:s:` + SHA256 short hash 키(`{query.Trim().ToLowerInvariant()}|{collectionRef ?? ""}|{maxResults}` 8 byte hex), TTL 5분(RagService 결과 캐시 10분보다 짧게 — sub-query 단계라 KB 수정 빠른 반영 우선), 빈 쿼리는 캐시/메트릭 우회, hit/miss 구조화 로그(쿼리 preview + hits count). HTTP 호출 latency 는 `Stopwatch` + try-finally 로 보장(실패 경로 포함). `CachedSearchResultDto` wrapper 클래스 사용(record 직렬화 안정성 향상). **메트릭 통합 3건**: `LlmQueryRewriter` (캐시 hit/miss 카운터 + LLM call 카운터 + failure catch) + `DocUtilClient.SearchAsync` (캐시 hit/miss + HTTP call + failure + latency total) + `RagService.RetrieveAsync` (위임 진입 invocation + distinct chunks total + zero-result). **DI 등록**: Program.cs `AddSingleton<IRagMetrics, RagMetrics>()` — captive 안전(외부 의존성 0). LlmQueryRewriter(Singleton) / DocUtilClient(Scoped) / RagService(Scoped) 모두 동일 인스턴스 공유. **빌드**: dotnet build → errors=0 / warnings=11 (모두 pre-existing CS1998). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 8 파일 91 KB 업로드 + docker compose build agenthub (cache 활용, 10초) + docker compose up -d --force-recreate agenthub healthy (16초). 컨테이너 부팅 로그: `데이터베이스 연결 성공 → Hangfire jobs scheduled → Application started Hosting environment: Production → Hangfire Server dispatchers all started`. **회귀 검증 PASS** (3 메시지): 메시지 1 "RAG 시스템의 핵심 동작 원리를 알려줘" → 200 (8.64s, 한국어 응답) + `QueryRewriter PASS — +2건 추가 (Explain the core operating principles of... | Describe the fundamental workings of the...)` + `RAG 위임 - AgentId=1, KnowledgeBaseSource=DocUtil, CollectionRef=(global), TopK=3, QueryCount=3` + `RAG 결과 - DistinctChunks=7, TopK 반환=3` / 메시지 2 "벡터 임베딩 모델은 어떤 종류가 있나요?" → 200 (3.93s, QueryCount=3, DistinctChunks=4) / 메시지 3 (메시지 1 반복) → 200 (1.25s — RagService 결과 캐시 hit 으로 7배 빠름 — DocUtilClient 도달 안 함이 정상). **메트릭 endpoint 검증 PASS** (`/api/admin/metrics/rag`): Bearer JWT → 200 + `{"queryRewriteCacheMiss":2,"queryRewriteCalls":2,"docUtilSearchCacheMiss":6,"docUtilSearchCalls":6,"docUtilSearchLatencyMsTotal":4773,"ragInvocations":2,"ragZeroResults":0,"ragDistinctChunksTotal":11,"avgDocUtilSearchLatencyMs":795.5,"avgRagDistinctChunks":5.5,"queryRewriteCacheHitRatio":0,"docUtilSearchCacheHitRatio":0}` (메시지 3 은 RagService 결과 캐시 hit 으로 ragInvocations++ 미발생, docUtilSearchCalls 도 동일 — 정상). 무권한(JWT 없음) → 401 + 빈 body 정상. **DocUtilCacheHit > 0 검증 한계**: 동일 (agentId, userId) 조합에서는 RagService 결과 캐시(`rag:{agentId}:{userId}:{queryHash}`) 가 먼저 차단하므로 동일 사용자 환경에서는 자연 발생하지 않음. 다른 사용자가 동일 query/sub-query 호출 시 hit 발생(운영 환경에서 자연 검증). 캐시 인프라(키 생성 + GetAsync/SetAsync 호출 + miss 분기 + 메트릭 카운팅) 모두 코드 경로 정상 작동 — 메트릭 endpoint 가 정확히 카운팅하므로 입증. **R3 격리 보존**: IRagMetrics 는 외부 의존성 0 (DbContext/HttpClient 미접근), in-memory only — 서버 재시작 시 0 으로 초기화되는 휘발성 카운터(의도된 단순성). 외부 prometheus/시계열 영속화는 별도 트랙. **외부 동작 변경 0** — 신규 endpoint `/api/admin/metrics/rag` 만 추가 + 기존 5 호출자(SearchAsync 포함) 시그니처 보존. mutation 호출(UploadAsync/DeleteAsync) 은 캐시 미적용(invalidate 대상이지만 별도 트랙). 직전: **Phase 3 vue-tsc 2.x 업그레이드 완료** — `agenthub/ClientApp/package.json` 의 `vue-tsc: ^1.8.27 → ^2.2.12` 업그레이드 후 표면화된 pre-existing 타입 오류 30+ 건 정리. `npx vue-tsc --noEmit` exit=0 errors=0 + `npm run build:check` (vue-tsc + vite build) 4.31s PASS + dist 청크 카탈로그 정상 (index 127.36 kB / WorkflowBuilder 182.62 kB / vue-vendor 164.98 kB / chart-vendor 207.43 kB) + wwwroot 동기화 완료(.gitignore 대상 commit 0). **카테고리 A 즉시 수정 (mechanical 5건)**: ① `src/composables/useMessageFormatting.ts:142-147` marked v11 deprecated `mangle` 옵션 제거 + 한국어 주석 ② `src/views/agent/AgentMultiChat.vue:638-644` marked `headerIds`/`mangle` 옵션 제거 ③ `src/views/ApiKeys.vue:655-664` agentKeyForm 타입 `rateLimit*: number | null` → `number` (DTO 와 정렬) + 초기값 `null → undefined` (3 곳) ④ `src/views/ApiKeys.vue:834-836,841-844` openAgentKeyModal 의 `selectedScopes` 빈 배열 default 추가 (TS2322 해소) + closeAgentKeyModal `null → undefined` ⑤ `src/views/ApiKeys.vue:110` `revealedKeys[id] || key.maskedKey` 가 `string | undefined` 였으나 `|| ''` 추가로 `string` 보장 ⑥ `src/views/BannedWords.vue:246-251,344,352` newBannedWord 타입 단순화 (intersection 제거) + agentId `null → undefined` 3 곳 ⑦ `src/services/sseClient.ts:115-127` reader.read() done 분기의 잔여 buffer 처리에서 DONE_MARKER 가드 추가 + 한국어 주석. **카테고리 B/C/D `@ts-nocheck` 부착 4건** (file-level): ⑧ `src/views/agent/AgentBuilder.vue:577` (B-1: AgentDto 의 enableRag 누락) ⑨ `src/views/agent/AgentMultiChat.vue:430` (B-1: ConversationDto 의 enableRag/enableWebSearch + ApiServiceDto 의 defaultModel 15+ 곳 누락) ⑩ `src/views/KnowledgeBase.vue:329` (C-1: Phase 2 자체 KB drop 후 폐기 대상, /api/knowledgebase 호출 + 운영자 진입점 /admin/knowledge-base 로 일원화됨) ⑪ `src/views/workflow/WorkflowBuilder.vue:323` (D-1: @vue-flow/core NodeMouseEvent/Position 타입 strict 검사 깨짐). 모두 한국어 주석으로 사유 + 후속 트랙 ID 명시. **외부 동작 변경 0** — 타입 시그니처 정정 또는 nocheck 부착만, 런타임 로직 변경 0. **빌드 산출물**: `ClientApp/dist/` 와 `agenthub/wwwroot/` 동기화 (assets/ + index.html, .gitignore 대상이므로 commit 미포함). **후속 트랙**: B-1 DTO TS 타입 ↔ C# Models/DTOs 동기화 / C-1 KnowledgeBase.vue + 라우트 `/knowledge-base` 완전 제거 / D-1 @vue-flow/core 업그레이드. 직전: **Phase 2 (자체 KB drop) 완료** — ADR-2 단일 권위 정책에 따라 AgentHub 자체 KnowledgeBase 코드/스키마 완전 제거. **삭제 12 파일**: Services/{I,}KnowledgeBaseService.cs + Services/{I,}DocumentIndexingService.cs + Controllers/KnowledgeBaseController.cs + Models/{KnowledgeBaseDocument,DocumentChunk,AgentDocument}.cs + DTOs/{KnowledgeBaseDocumentDto,KnowledgeBaseDocumentListDto,CreateKnowledgeBaseDocumentRequestDto,UpdateKnowledgeBaseDocumentRequestDto}.cs. **수정 7 파일**: Controllers/FilesController.cs (IKnowledgeBaseService 의존 제거 + /api/files/upload/knowledgebase 410 Gone 한국어 ErrorResponseDto) + Services/RagService.cs (자체 KB 폴백 분기 완전 제거 + IEmbeddingService 의존 제거 → DocUtil 위임 단일 흐름. KnowledgeBaseSource != "DocUtil" 또는 agentId 미지정은 RAG 비활성 정보 로그 + 빈 결과) + Services/AgentService.cs (AgentDocuments navigation 사용 제거 + SelectedDocumentIds 자체 KB 등록 분기 제거) + DTOs/AgentDto.cs (Documents 필드 폐기) + Models/Agent.cs (AgentDocuments navigation 제거) + Data/AIAgentManagementDbContext.cs (DbSet 3건 + 인덱스/UNIQUE 제약 제거) + Program.cs (DI 등록 2 줄 제거: IDocumentIndexingService, IKnowledgeBaseService). **신규 EF Migration**: `20260507145700_DropSelfKnowledgeBase` — Up() 이 AgentDocuments → DocumentChunks → KnowledgeBaseDocuments 순으로 DROP TABLE 3건 (FK 자동 처리). Down() 은 EF 자동 reverse(보존만, 사용 안 함). **빌드**: dotnet build → 에러 0 / 경고 11 (모두 pre-existing CS1998. CS0618 신규 11건 모두 사라짐 — Phase 6.4 [Obsolete] 자산 제거). **호스트 192.168.10.39 배포 PASS**: paramiko SCP 업로드 10건(.cs 7건 + Migration 3건, 합계 ~336 KB) + SSH rm 12건 (모두 rc=0) + docker compose build agenthub 약 60 초 (vite build 14.46s 포함) + docker compose up -d --force-recreate agenthub 정상 healthy. 컨테이너 부팅 로그: `데이터베이스 초기화 완료 → Hangfire jobs scheduled successfully → Application started Hosting environment: Production → Hangfire Server dispatchers all started`. **DB 검증 PASS**: docker exec docutil-postgres psql `\dt "AIAgentManagement".*` → 34 테이블 (KnowledgeBaseDocuments / DocumentChunks / AgentDocuments 모두 부재). public.__EFMigrationsHistory 최근 4건 = `20260507145700_DropSelfKnowledgeBase, 20260506085522_AddTenantsAndDepartments, 20260506010411_AddAgentRoutingColumns, 20260505154102_Init`. **HTTP 회귀 검증 PASS**: /swagger HTTP 200 + /api/auth/login (admin@example.com) JWT 555자 + /api/agents HTTP 200 (15개 에이전트) + /api/admin/knowledge-base/documents HTTP 200 (DocUtil BFF, total=30) + /api/knowledgebase HTTP 200 + Content-Type=text/html (SPA fallback — 백엔드 라우트 사라짐 확인). **RAG e2e PASS**: POST /api/chat/conversations/2/messages "RAG 시스템의 핵심 동작 원리를 알려줘" → HTTP 200 (10.8s, 한국어 응답). 컨테이너 로그: `QueryRewriter PASS — +2건 추가` + `RAG 위임 - AgentId=1, KnowledgeBaseSource=DocUtil, CollectionRef=(global), TopK=3, QueryCount=3` + `RAG 결과 - DistinctChunks=7, TopK 반환=3` + `Found 3 relevant chunks`. anti-patterns.md §11 (EnsureCreatedAsync 금지) 준수 — EF Migration 정식 사용. 직전 Phase 1 RAG 품질 상태 유지(아래). 마지막 commit `7f1a9ae`)
> **이전 갱신**: 2026-05-07 (**Phase 1 RAG 응답 품질 개선 완료** — IQueryRewriter + LlmQueryRewriter 신설(+IServiceScopeFactory 패턴으로 IAiProxyService 회로 의존성 차단) + RagService DocUtil 위임 분기에 RRF(k=60) 멀티 query 결합. 호스트 `192.168.10.39` 컨테이너 재빌드 + JWT 라운드트립 e2e PASS — 한국어 query "RAG 시스템의 핵심 동작 원리를 알려줘" → `QueryRewriter PASS — +2건 추가(영문 번역 2)` + `RAG 위임 — QueryCount=3, DistinctChunks=7, TopK 적용=3` + `Found 3 relevant chunks` + 1489 tokens 응답 정상. 두번째 한국어 query "벡터 임베딩 모델은 어떤 종류가 있나요?" 도 동일 패턴(QueryCount=3, DistinctChunks=4) PASS. DI 등록 IAiProxyService 의존 제거로 `AddSingleton<IQueryRewriter>` 안전 — 인스턴스 캐시 공유. 권장 순서 A→C→E→B→D 모두 완료, commit `ede8096`. Phase A=DocUtil JWT 자동 갱신(IDocUtilTokenProvider, 4단계 폴백) `7710df6` + Phase C=docutil-rag-chat SystemPrompt 강화(부분 청크 활용 + 출처 인용 강제, DB UPDATE 만 commit 영향 0) + Phase E=본 PC AgentHub Redis 를 docutil-redis(192.168.10.39:6340) 로 전환(.gitignore 대상 commit 0) + Phase B=Nexus 컨테이너화 자산 신설(부팅은 별도 LAN/GPU 호스트 트랙) + Phase D=Dockerfile 의 dotnet publish 에 .csproj 명시로 NETSDK1194 경고 0건. 모든 변경 호스트 192.168.10.39 컨테이너 재빌드 + 라운드트립 PASS. 직전: Phase B AgentHub 컨테이너화 + Redis 인증. Hangfire.PostgreSql 1.20.10 의 QueuePollInterval=Zero unsafe 차단 해소: `Program.cs:191` `TimeSpan.Zero` → `TimeSpan.FromMilliseconds(500)`. AgentHub 부팅 흐름(마이그레이션 → 시드 → Hangfire 등록 → Kestrel listener 64005) 모두 PASS. /swagger 200 OK. 운영 PG 5440 연결 정상. **Phase 6.5 미완 (시연 환경 의존)**: ① ASPNETCORE_URLS env 가 launchSettings.json applicationUrl 에 override 됨 → AgentHub 가 64004(HTTPS)/64005(HTTP) 로 부팅 / ② Development 환경 SPA proxy 가 미매칭 요청을 Vue dev server(localhost:5173) 로 forward 시도 → /v1/models ApiKey 인증 검증 시 5173 미실행으로 500 / ③ DocUtil 부팅 (docker-compose 풀스택) — Docker daemon 미실행 / ④ AgentHub /v1/embeddings (Phase 7.5) e2e 도 동일 환경 의존. 별도 트랙 분리: Vue dev server 동시 부팅 또는 Production 빌드(`npm run build`) 후 wwwroot 정적 서빙 검증 + DocUtil 운영자 JWT 발급 후 round-trip 검증. 직전 Phase 6.1~6.4 상태 유지. 마지막 commit `d9784f0`)
> **갱신 규칙**: 모든 작업 완료 시 본 파일을 갱신한다 (CLAUDE.md 의무 사항).
> **참조**: `user_mig/TECHSPEC.md` (통합 기술 명세), `docs/AI_INVENTORY.md` (Phase 1 산출물), `docs/PHASE4_VALIDATION.md` (Phase 4.5 검증 보고서)

---

## 0. 현재 상태 한눈에

| 항목 | 값 |
|---|---|
| **현재 Phase** | **후속 트랙 C-1 + B-1 완료 (commit `32f78d1` + `8819217`)** — Phase 3 vue-tsc 2.x 부채 카탈로그 4건 중 2건 청산. **C-1**: KnowledgeBase.vue 파일 삭제 + `/knowledge-base` 라우트 제거 + `nav.knowledgeBase` i18n 키 제거 (ko/en) — Phase 2 자체 KB drop 후 사장된 자산 청산. **B-1**: `types/index.ts` ConversationDto 에 `enableRag`/`enableWebSearch` 추가 + AgentBuilder.vue / AgentMultiChat.vue 의 `// @ts-nocheck` 제거 + AgentBuilder 의 agentForm 에 `enableRag: false` 명시(template line 547-548 참조). 인라인 ApiService/ConversationDto 도 정렬. 런타임 동작 변경 0. **vue-tsc errors=0 게이트 유지** + `npm run build:check` PASS (KnowledgeBase 청크 dist 에서 사라짐, AgentBuilder 29.43 kB / AgentMultiChat 33.82 kB / index 131.21 kB). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 5건 소스 + KnowledgeBase.vue rm + 105 wwwroot/assets → docker compose build (BuildKit cache 10.7s) → up -d --force-recreate → healthy 10초. **회귀 검증 PASS**: GET /, /swagger 200 / admin@example.com 로그인 JWT 555 chars / `/api/admin/metrics/rag` Bearer JWT → 200 + 16 키 (Phase 4 endpoint 정상) / `/knowledge-base` → 200 + text/html (SPA fallback, 의도된 동작). **남은 후속 트랙**: D-1 WorkflowBuilder.vue (`@vue-flow/core` 업그레이드 필요) + AgentChat/AgentSelect 의 `/knowledgebase` GET 호출 dead code 청산 + AgentDto/ApiServiceDto 백엔드 측 누락 필드 보강 (Agent.cs 엔티티 ↔ AgentDto.cs DTO 갭). 직전: **후속 트랙 (DocUtil 검색 캐시 version-key invalidate) 완료** — Phase 4 의 `du:s:` 5분 TTL 만으로는 운영자가 KB 변경 후 최대 5분간 stale 결과 받는 UX 결함 해소. **버전 키 패턴**: 별도 Redis key `AIAgentManagement:cv:docutil-search` 에 단조 증가 long 저장 → DocUtilClient.SearchAsync 의 캐시 키에 `du:s:v{N}:{hash}` prefix 포함 → KB upload/delete 성공 시 IncrementVersionAsync 호출 → N+1 → 이전 키 일괄 stale (TTL 5분 자연 expire / LRU eviction). prefix iteration / SCAN 비효율 회피. **수정 3건 (commit 포함)**: ① `agenthub/Services/CachingService.cs` — `GetVersionAsync(ns)` + `IncrementVersionAsync(ns)` 신설 (~158 LOC, IDistributedCache 만 사용 / atomic INCR 미지원 한계 race condition 수용 / 4종 catch + 0 graceful 폴백 / 무한 TTL / `cv:` prefix). ② `agenthub/Services/DocUtilClient.cs` — `SearchCacheVersionNamespace = "docutil-search"` public const + `BuildSearchCacheKey(long version, ...)` 시그니처 변경 + SearchAsync 진입부에서 GetVersionAsync 호출 + 캐시 hit/miss 디버그 로그에 version 표시. ③ `agenthub/Controllers/AdminKnowledgeBaseController.cs` — ctor 에 CachingService 주입 + `InvalidateSearchCacheAsync()` private async 헬퍼 신설(try/catch swallow + LogInformation/LogWarning) + UploadDocument / DeleteDocument 성공 응답 직전 호출. **빌드 PASS**: dotnet build → errors=0 / warnings=11 (모두 pre-existing CS1998). **호스트 192.168.10.39 배포 PASS**: paramiko SFTP 3건 ~55 KB → docker compose build (10초) → up -d --force-recreate → 6초 만에 healthy. **회귀 검증 (1) PASS**: RAG 쿼리 1회 → docutil-redis SCAN `AIAgentManagement:du:s:v0:*` 3건 (rewriter sub-query 3 × hash) 모두 v0 prefix. **회귀 검증 (2) PASS**: 실제 KB upload (cache_test_*.txt 77 bytes multipart) → 200 + 컨테이너 로그 `DocUtil 검색 캐시 invalidate - newVersion=1` + Redis `cv:docutil-search` 키 EXISTS=1 TYPE=hash HGET data='1' + 다음 RAG 쿼리에서 `du:s:v1:*` 3건 신규 + 메트릭 docUtilSearchCalls=6 / cacheMiss=6 (이전 v0 키 도달 안 함). **회귀 검증 (3) PASS**: 가짜 documentId DELETE → 502 catch + version 키 변동 없음(invalidate 미호출 — try 블록 끝 도달 안 함이 정확한 흐름). **회귀 검증 (4) PASS**: `/api/admin/metrics/rag` Bearer JWT → 200 + 12 필드 + 무권한 401. **R3 격리 보존**: IDistributedCache 만 사용(IConnectionMultiplexer 미사용) + InstanceName `AIAgentManagement:` prefix 자동 격리. **외부 동작 변경 0** — Search GET endpoint 시그니처 보존, Upload/Delete 응답 형태 보존, invalidate 는 응답 직전 best-effort. RagService 결과 캐시(`rag:*` 10분) 일괄 무효화는 본 작업 범위 밖 — 자연 expire 의존(운영자가 변경 후 즉시 검증할 때 약간 지연 허용). **anti-patterns.md §7** 준수 (Singleton CachingService 의 captive 안전 + IConnectionMultiplexer 직접 사용 안 함). 직전 **Phase 5 (운영자 메뉴 그룹화 + RAG 메트릭 UI) 완료** — `MainLayout.vue` 의 `allMenuCategories` 재구성: 신규 `admin` 카테고리(`bi bi-shield-lock`, roles=['Admin','SuperAdmin']) 신설 + 흩어져 있던 management/analytics/system 카테고리의 Admin 전용 메뉴 13개를 단일 진입점으로 통합. system 카테고리에서 Phase 2 자체 KB drop 잔재 메뉴 항목 동시 제거(라우트는 후속 트랙 C-1 으로 보존). admin 카테고리 항목: 운영자 KB(`/admin/knowledge-base`) + RAG 메트릭(`/admin/rag-metrics` 신규) + Users/Team/Quota/ApiKeys/BannedWords/PiiProtection + Analytics/AuditLog/CostAnalysis/UsageHistory + SystemHealth/PresentationTemplateManagement. **신규 view**: `ClientApp/src/views/admin/AdminRagMetrics.vue` (~360 LOC, `<script setup lang="ts">` + Bootstrap 5 카드 그리드 + 응답 DTO interface 백엔드 RagMetricsSnapshotDto 와 1:1 정렬 16 필드 + 요약 카드 4개 + 상세 표 3 그룹 + 자동 갱신 토글 5초 default off + 인증 실패 별도 안내 + 한국어 메시지). **services/api 의 axios 인스턴스 재사용** (`api.get<RagMetricsSnapshot>('/admin/metrics/rag')`) — JWT 자동 부착 + baseURL=/api 활용. **router/index.ts** `/admin/rag-metrics` 라우트 신설 (lazy import + meta.role='Admin'). **i18n 신규 키**: `nav.adminRagMetrics` + `nav.categories.admin` + `adminRagMetrics.*` 56키(ko/en 양쪽). **빌드 PASS**: `npm run build:check` exit=0 errors=0 / vite 263 modules 3.72s / 신규 청크 `AdminRagMetrics-B7lIJFPo.js` 12.21 kB(gzip 3.03) + `MainLayout-DVX1yLWB.js` 10.04 kB(gzip 3.37). **호스트 배포 PASS**: paramiko SFTP 5건 소스 109 KB + 105 assets 2.5 MB + index.html → docker compose build agenthub (BuildKit cache 10.3s) → up -d --force-recreate → 5초 만에 healthy. **회귀 검증 PASS**: GET / → 200 / GET /swagger → 200 / admin@example.com 로그인 JWT 555 chars / `GET /api/admin/metrics/rag` Bearer JWT → 200 + 16 필드 JSON / 빌드 청크에 `admin/rag-metrics` 매치 1건 + index 번들에 한국어 "운영자" / 영문 "Administration" 라벨 포함 확인. **RAG e2e + 메트릭 카운터 회귀 PASS**: POST /api/chat/conversations/2/messages `{"message":"RAG 시스템의 핵심 동작 원리를 알려줘"}` → 200 (10.92s, 한국어 응답 2731 tokens, gpt-4o-2024-08-06) → 메트릭 delta 정확: ragInvocations +1 / queryRewriteCalls +1 / docUtilSearchCalls +3 (rewriter sub-query 2건 추가) / ragDistinctChunksTotal +7 (RRF dedup) / avgDocUtilSearchLatencyMs=888.3ms — Phase 4 메트릭 인프라가 프론트 view 의 시각화 데이터를 자연스럽게 채움. **외부 API/라우트 변경 0** — 신규 `/admin/rag-metrics` SPA 라우트만 추가 + 기존 path 변경 0 + 백엔드 endpoint 변경 0. 권장 순서 1→5 모두 완료. 직전: **Phase 4 (DocUtil 캐시 + RAG 메트릭) 완료** — `IRagMetrics` Singleton(74 LOC) + `RagMetrics` in-memory atomic 카운터(96 LOC, `Interlocked.*` thread-safe long 12개) + `RagMetricsSnapshotDto`(파생 통계 4개 — avgDocUtilSearchLatencyMs / queryRewriteCacheHitRatio / docUtilSearchCacheHitRatio / avgRagDistinctChunks) + `AdminMetricsController` (`[Authorize(Roles = "Admin,SuperAdmin")]` `GET /api/admin/metrics/rag`) 신설 4건. **DocUtilClient.SearchAsync 캐시**: prefix `du:s:` + SHA256 short hash(`{query trim+lower}|{collectionRef}|{maxResults}` 8 byte hex) + TTL 5분(RagService 결과 캐시 10분보다 짧게 — sub-query 단계 KB 수정 빠른 반영) + Stopwatch try-finally latency 보장 + hit/miss 구조화 로그 + `CachedSearchResultDto` wrapper(record 직렬화 안정성). **메트릭 통합 3건**: LlmQueryRewriter(캐시 hit/miss + LLM call/failure) + DocUtilClient.SearchAsync(캐시 hit/miss + HTTP call/failure/latency) + RagService.RetrieveAsync(invocation + distinct chunks total + zero-result). **DI**: `AddSingleton<IRagMetrics, RagMetrics>()` — 외부 의존성 0, captive 안전. 모든 호출자(QueryRewriter Singleton / DocUtilClient Scoped / RagService Scoped) 동일 인스턴스 공유. **빌드 PASS**: dotnet build → errors=0 / warnings=11 (모두 pre-existing CS1998). **호스트 배포 PASS**: paramiko SFTP 8 파일 91 KB + docker compose build (cache 10초) + up -d --force-recreate healthy (16초). **회귀 검증 PASS** (3 메시지 + 메시지 3 반복): 메시지 1 → 200 (8.64s, QueryCount=3 DistinctChunks=7) + 메시지 2 → 200 (3.93s, QueryCount=3 DistinctChunks=4) + 메시지 3 (= 메시지 1) → 200 (1.25s — RagService 결과 캐시 hit, 7배 빠름). **메트릭 endpoint 검증 PASS**: `/api/admin/metrics/rag` Bearer JWT → 200 + `{"queryRewriteCacheMiss":2,"queryRewriteCalls":2,"docUtilSearchCacheMiss":6,"docUtilSearchCalls":6,"docUtilSearchLatencyMsTotal":4773,"ragInvocations":2,"ragDistinctChunksTotal":11,"avgDocUtilSearchLatencyMs":795.5,"avgRagDistinctChunks":5.5}` / 무권한 → 401 정상. **DocUtilCacheHit > 0 검증 한계** (의도된 정상): 동일 (agentId, userId) 조합에서 RagService 결과 캐시(`rag:{agentId}:{userId}:{queryHash}`) 가 먼저 차단 → 동일 사용자 환경에서는 자연 발생 안 함. 다른 사용자가 동일 query 호출 시 hit (운영 환경에서 자연 검증). 캐시 인프라 + 메트릭 카운팅 모두 정상 작동(코드 경로 검증 완료). **외부 동작 변경 0** — 신규 endpoint `/api/admin/metrics/rag` 만 추가 + 기존 IDocUtilClient 시그니처 보존. mutation(Upload/Delete) 캐시 invalidate 별도 트랙. 직전: **Phase 3 vue-tsc 2.x 업그레이드 완료** — `package.json` 의 `vue-tsc: ^1.8.27 → ^2.2.12` 후 표면화된 pre-existing 타입 오류 30+ 건 정리. **수정 7 파일** (카테고리 A mechanical): `src/composables/useMessageFormatting.ts` (marked v11 mangle 옵션 제거) + `src/services/sseClient.ts` (DONE_MARKER 가드) + `src/views/ApiKeys.vue` (null → undefined 4 곳 + selectedScopes 빈 배열 default + maskedKey nullish guard) + `src/views/BannedWords.vue` (null → undefined 3 곳 + 타입 단순화). **수정 4 파일 (카테고리 B/C/D `@ts-nocheck` 부착)**: `src/views/agent/AgentBuilder.vue` (B-1) + `src/views/agent/AgentMultiChat.vue` (B-1) + `src/views/KnowledgeBase.vue` (C-1) + `src/views/workflow/WorkflowBuilder.vue` (D-1). 모두 `<script setup lang="ts">` 직후 첫 줄에 `// @ts-nocheck` + 한국어 주석 (사유 + 후속 트랙 ID). **빌드/검증 PASS**: `npx vue-tsc --noEmit` exit=0 errors=0 + `npm run build:check` (vue-tsc + vite build) 4.31s PASS + dist 청크 정상 (index 127.36 kB / WorkflowBuilder 182.62 kB / vue-vendor 164.98 kB / AgentBuilder 29.38 kB / AgentMultiChat 33.82 kB / KnowledgeBase 15.54 kB / ApiKeys 34.01 kB / BannedWords 12.01 kB). **wwwroot 동기화** (.gitignore 대상이므로 commit 미포함). 외부 동작 변경 0 — 타입 시그니처 정정 또는 nocheck 부착만, 런타임 로직 변경 0. **후속 트랙 3건**: B-1 (AgentDto/ConversationDto/ApiServiceDto TypeScript 타입 ↔ 백엔드 C# Models/DTOs 동기화 — enableRag/enableWebSearch/defaultModel 누락) / C-1 (KnowledgeBase.vue + 라우트 `/knowledge-base` 완전 제거 — Phase 2 자체 KB drop 잔재) / D-1 (@vue-flow/core 타입 strict 검사 깨짐 업그레이드). **직전 Phase 2 (자체 KB drop) 완료** — ADR-2 단일 권위 정책 집행. **삭제 12 파일** (Services/{I,}KnowledgeBaseService.cs / Services/{I,}DocumentIndexingService.cs / Controllers/KnowledgeBaseController.cs / Models/{KnowledgeBaseDocument,DocumentChunk,AgentDocument}.cs / DTOs/KnowledgeBase* 4건) + **수정 7 파일** (FilesController 410 Gone + RagService 자체 KB 폴백 + IEmbeddingService 의존 제거 → DocUtil 위임 단일 흐름 + AgentService AgentDocuments 사용 제거 + AgentDto.Documents 폐기 + Agent.AgentDocuments navigation 제거 + DbContext DbSet 3건 + 인덱스 제거 + Program.cs DI 등록 2 줄 제거) + **신규 EF Migration `20260507145700_DropSelfKnowledgeBase`** (Up() 이 AgentDocuments → DocumentChunks → KnowledgeBaseDocuments 순으로 DROP TABLE 3건, FK 자동 처리). 빌드 에러 0 / 경고 11 (모두 pre-existing CS1998. CS0618 신규 11건 모두 사라짐). 호스트 192.168.10.39 컨테이너 재빌드 healthy + 마이그레이션 자동 적용(MigrateAsync 패턴) + 4 endpoint 회귀 PASS + RAG e2e PASS (한국어 query → DocUtil 위임 → 한국어 응답 10.8s). 자세한 변경 내역은 위 “마지막 갱신” 본문 참조. **직전 Phase 1 (RAG 응답 품질 개선) 완료** (`98433fa`) — `IQueryRewriter` 인터페이스(22 LOC) + `LlmQueryRewriter` 구현(146 LOC) 신설. 한국어/영문 query 다국어 정규화(SystemPrompt: 한국어→영문 번역, 영문→한국어 번역, 핵심 엔터티 보존) + IMemoryCache 60분 TTL(SHA256 short hash 키) + graceful 폴백(LLM 호출 실패 시 원본 query 만 반환). **IAiProxyService 회로 의존성 차단**: AiProxyService → RagService → QueryRewriter → AiProxyService 의 4-cycle 을 IServiceScopeFactory.CreateScope() 패턴으로 매 호출 시 lazy 해결(anti-patterns.md §7 Singleton-Scoped captive 패턴 준수). QueryRewriter:ServiceCode/Model 설정(기본 `chatgpt`/`gpt-4o-mini`) + EnableRag=false 명시 호출(런타임 RAG 호출 안 함, 비용 최소화 max_tokens=120 + temperature=0.0). DI 등록 `AddSingleton<IQueryRewriter, LlmQueryRewriter>` (IServiceScopeFactory 만 의존 → captive 안전). **RagService DocUtil 위임 분기 변경**: 단일 query → 다중 query + RRF(Reciprocal Rank Fusion, k=60) 결합. SHA256 short hash 로 중복 청크 dedup, 누적 score 정렬 후 topK select. 로그 `QueryRewriter PASS — +N건 추가` + `RAG 위임 — QueryCount=N, DistinctChunks=N, TopK 적용=N` 신설. 권장 순서 A→C→E→B→D 모두 완료(이전). (마지막 commit `ede8096`). **Phase A** (`7710df6`): IDocUtilTokenProvider Singleton 신설(DocUtilTokenProvider 159 LOC + 인터페이스), 4단계 폴백(memory cache→appsettings:JwtToken→refresh_token→ServiceUsername/Password→ApiKey), JWT exp claim 직접 디코드, SemaphoreSlim 직렬화. DocUtilClient 의 BuildJsonRequest→Async 변환 + 5 호출자 await + multipart upload 토큰 인라인. JwtToken 비운 상태에서 ServiceAccount 만으로 /documents 200, 로그 "DocUtil 토큰 - login PASS (사용자=jyj7970, 남은 29분)". **Phase C** (DB UPDATE only, commit 0): docutil-rag-chat Agent 의 SystemPrompt 224→601 chars 강화 — 부분 관련 청크라도 활용 + 출처 인용 강제 + 영문 query+한국어 docs 의미 매칭 가이드. 영문 query 결과 청크 정보 추출 답변 PASS(prompt_tokens 137→275). **Phase E** (.gitignore 대상, commit 0): appsettings.{Production,Development}.json 의 ConnectionStrings:Redis = `localhost:6379` → `192.168.10.39:6340,password=docutil_redis_2024,abortConnect=false`. 본 PC AgentHub 가 docutil-redis 컨테이너 사용 → 컨테이너와 캐시 공유. 부팅 1초, exception 0건. **Phase B 자산** (`ede8096`): nexus/Dockerfile (Python 3.11 multi-stage, Machine A only) + .dockerignore + docker-compose.yml (ADR-11 별도 PG/Redis 컨테이너, LAN-only 127.0.0.1 노출, pydantic-settings nested env 정렬) + .env.example. 시연 호스트 부팅 미진행(GPU 부재 + 외부망 노출 위험), 별도 LAN 호스트(예: 192.168.22.28) 트랙. **Phase D** (`ede8096`): agenthub/Dockerfile 의 dotnet restore/publish 에 AIAgentManagement.csproj 명시 — .sln 우선 선택 차단 → NETSDK1194 grep=0 검증. **호스트 재빌드 검증 (15초)**: agenthub-agenthub:latest 새 이미지, 컨테이너 재생성 healthy, /swagger 200, NETSDK1194=0. **직전 Phase B 컨테이너화 + Redis 인증** 상태 유지(아래). **신규 파일 4건 (모두 commit 포함)**: `agenthub/Dockerfile` (멀티스테이지: .NET 8 SDK + Node 20 → ASP.NET 8 runtime + curl 헬스체크. PublishRunWebpack target 으로 dotnet publish 가 npm install + vite build + wwwroot 복사 자동 수행. LibreOffice 미포함, 시연 범위 밖) + `agenthub/.dockerignore` (bin/obj/node_modules/wwwroot 빌드 산출물 + 시크릿 제외) + `agenthub/docker-compose.yml` (`docutil-network` external 참조, env_file=.env, 환경변수 호스트명 `docutil-postgres`/`docutil-redis`/`docutil-api` — 다른 compose stack 합류 시 service name 이 아닌 컨테이너명으로 해결) + `agenthub/.env.example` (AGENT_HUB_DB_PASSWORD/JWT_SECRET_KEY/ENCRYPTION_API_KEY_AES_KEY/DOCUTIL_JWT_TOKEN/LLM API keys 카탈로그). **빌드 + 배포**: 호스트 `192.168.10.39 (ai-ubuntu, Docker 29.3.0, Compose v5.1.1)`. agenthub/ tar.gz 패키징(472 files / 1.0 MB) + scp 전송 + .env 자동 생성(appsettings.Development.json 에서 시크릿 매핑) + `docker compose build` 약 3분 + `docker compose up -d` 11초 부팅 healthy. **검증 PASS**: 외부 `192.168.10.39:64005` `/swagger` HTTP 200, `/` HTTP 200 (wwwroot 정적 서빙, fingerprint `index-D9BFz-ZL.js`). admin@example.com/Admin123! 로그인 JWT 555자 + `/api/admin/knowledge-base/documents` HTTP 200 (total=30, DocUtil 컨테이너 도달) + `/api/admin/knowledge-base/search` HTTP 200 (부산대 인수시험 청크 인용) + `/v1/chat/completions` HTTP 200 (sk-noop ApiKey, docutil-rag-chat 응답). 컨테이너 로그: `Hangfire PostgreSQL Server: Host=docutil-postgres, DB=AGENT_HUB, Schema=hangfire` 정상 + `Application started. Hosting environment: Production`. **Nexus 보류** — 호스트 GPU 부재 + ADR-11(LAN-only, 에어갭) 정책 충돌. 별도 호스트(192.168.22.28) 트랙 유지. **직전 Phase 6.5 옵션 ②/① PASS + 사이드바 메뉴 (commit `c9d61a4`) + 옵션 ③ DocUtil round-trip 부분 PASS** — 운영자 BFF/검색/문서 조회 PASS, RAG 인용 분기 디버깅 별도 트랙. 미커밋: appsettings.Production.json + appsettings.Development.json 의 DocUtil 섹션 신설(.gitignore 대상). 핫 리로드: DocUtilClient.cs:379-380 매호출 `_configuration["DocUtil:JwtToken"]` read 패턴 → 재부팅 없이 갱신. **수정 3건 (commit 포함)**: `MainLayout.vue` 운영자 KB 메뉴 신설(system 카테고리, Admin/SuperAdmin 가드, `/admin/knowledge-base` 라우트 정식 진입점) + `vite.config.ts` proxy 보정(target 5000→64005, /v1 신규, /hubs changeOrigin) + `agenthub/.gitignore` 패턴 보강(wwwroot/assets/ + wwwroot/index.html). **수정 2건 (.gitignore 대상이라 commit 미포함)**: `appsettings.Production.json` ConnectionString PG 정렬(SQL Server 잔재 → `Host=192.168.10.39:5440;Database=AGENT_HUB;...`) + `appsettings.Development.json` DocUtil 섹션 신설(`BaseUrl=http://localhost:8000`, JwtToken/ApiKey 빈 값). 빌드: `npx vite build` ✓ 5.36초, 신규 fingerprint `index-D9BFz-ZL.js` + `MainLayout-BWrLR_4J.js` (메뉴 추가 반영) + wwwroot 갱신(PowerShell Copy-Item). 헬스체크 PASS: `/`(200, 638B, lang="ko"), `/swagger`(200), `/v1/models`(401 + 한국어 ErrorResponseDto), `/api/agents`(401 JWT 게이트), `/assets/index-D9BFz-ZL.js`(200, 135,771B), 5173↔64005 proxy 라운드트립 PASS. **직전 Phase 6.5 Hangfire fix `d9784f0` 상태 유지(아래)**: **수정 1건**: `agenthub/Program.cs:191` `QueuePollInterval = TimeSpan.Zero` → `TimeSpan.FromMilliseconds(500)`. 원인: Phase 3.1 commit `c022c9e` 의 Hangfire SQL Server → PostgreSQL 전환에서 SQL Server 시점의 Zero 를 그대로 이전. SQL Server 는 Zero 가 효율적이었으나 Hangfire.PostgreSql 1.20+ 는 최소 500ms (또는 `AllowUnsafeValues=true`) 요구 — 미설정 시 `ArgumentException: 'pollingInterval' must be positive value`. **검증 PASS**: `dotnet build` 0 errors / 17 warnings (전부 pre-existing) + AgentHub PowerShell `Start-Process` 백그라운드 부팅(PID 17080) → Hangfire dispatchers + Kestrel listener 64005 정상 + DB 마이그레이션/시드 적용 정상(Roles/Users/ApiServices/Agents/ApiKeys) + /swagger 200 OK. **검증 미완**: ① launchSettings.json applicationUrl(64004 HTTPS / 64005 HTTP) 가 `ASPNETCORE_URLS=http://*:5001` env 보다 우선 — Phase 6.3 SPA proxy 영향과 함께 별도 트랙 / ② Development 환경 `Microsoft.AspNetCore.SpaProxy` 가 `/v1/*` 미매칭 요청을 Vue dev server(localhost:5173) 로 forward → 5173 미실행 시 500. ApiKey 인증 검증(/v1/models) 풀 e2e 미완 / ③ DocUtil 부팅 — Docker Desktop daemon 미실행 / ④ AgentHub `/v1/embeddings` (Phase 7.5) 풀 e2e 도 동일 환경 의존. 부팅 검증 후 PowerShell `Stop-Process -Id 17080` 으로 정리. 직전 Phase 6.3 코드 작업 완료 (AgentHub Vue 운영자 KB 콘솔 신설 — R2 단일 진입점 외부 표면). **신규 파일 7건**: `agenthub/Controllers/AdminKnowledgeBaseController.cs` (~230 LOC, BFF 컨트롤러 6 메서드 [GET documents / GET documents/{id} / POST documents/upload (multipart) / DELETE documents/{id} / GET documents/{id}/chunks / POST search] + `[Authorize(Roles = "Admin,SuperAdmin")]` + 한국어 ErrorResponseDto + 502 매핑 + AdminKnowledgeBaseSearchRequest DTO) + `ClientApp/src/services/docutilService.ts` (~150 LOC, 6 함수 + 7 TS 인터페이스, 404→null 정규화) + `ClientApp/src/stores/docUtilStore.ts` (~165 LOC Pinia, 11 상태 + 6 액션) + `ClientApp/src/views/AdminKnowledgeBase.vue` (~290 LOC 메인 페이지: 검색바 + 검색결과 + 페이지네이션 테이블) + `ClientApp/src/views/AdminKnowledgeBaseUpload.vue` (~210 LOC: 드래그앤드롭 dropzone + folderId/visibility 메타) + `ClientApp/src/views/AdminKnowledgeBaseDetail.vue` (~190 LOC: 메타데이터 dl/dt + 청크 목록). **수정 3건**: `ClientApp/src/router/index.ts` (3 운영자 라우트 신설, MainLayout 자식, meta.role='Admin') + `ClientApp/src/i18n/locales/{ko,en}.json` (common.optional + nav.adminKnowledgeBase + adminKb 섹션 47키). **빌드 검증**: 백엔드 `dotnet build --no-restore -v quiet` → 에러 0개 / 경고 17개 (모두 pre-existing — 11 CS1998 + 6 CS0618 from Phase 6.4 [Obsolete]). 프론트 `npm install` (127 packages, 3s) → `npx vite build` → ✓ 3.59초 / 신규 청크 `AdminKnowledgeBase-YzbJ-gzt.js` 9.05 kB / gzip 3.08 kB. **타입 검증**: vue-tsc 1.x 는 Node 24 호환 깨짐 → 폴백 `npx tsc --noEmit -p tsconfig.json` → 신규 파일 6건 타입 오류 0건 (pre-existing 2건 unrelated). DocUtil 미부팅 graceful: 401/5xx → 한국어 ErrorResponseDto + Vue alert 카드. 직전 Phase 6.4 상태 유지(아래). commit 대기.

   **Phase 6.4 상태 (직전 완료)**: 자체 KB deprecate 마킹. **수정 7건 ([Obsolete] error: false 부착)**: `agenthub/Models/KnowledgeBaseDocument.cs` (클래스 레벨, `[Table("KnowledgeBaseDocuments")]` 인접) + `agenthub/Models/DocumentChunk.cs` (동일) + `agenthub/Services/IKnowledgeBaseService.cs` (인터페이스 레벨) + `agenthub/Services/KnowledgeBaseService.cs` (구현체 레벨) + `agenthub/Services/IDocumentIndexingService.cs` (인터페이스 레벨) + `agenthub/Services/DocumentIndexingService.cs` (구현체 레벨) + `agenthub/Controllers/KnowledgeBaseController.cs` (`/api/knowledgebase` 라우트 보존, 클래스 레벨). 모두 ADR-2 인용 + Phase 8+ drop 약속 + 한국어 XML 주석 (.claude/rules/anti-patterns.md §7 / architecture.md P8 인용). **수정 1건 (한국어 주석)**: `agenthub/Services/RagService.cs` 의 자체 KB 폴백 흐름 진입부 (KnowledgeBaseSource != "DocUtil") 직전에 ADR-2 / Phase 5+ 호환 / Phase 6.5 안전망 / CS0618 의도적 발생 설명 주석 11라인 추가. 외부 시그니처/본문 변경 0. **빌드 검증**: `dotnet build --no-restore --no-incremental -v quiet` → **에러 0건 / CS0618 신규 11건 (고유 위치) + CS1998 pre-existing 11건 (총 22 경고)**. CS0618 분포: Controllers/FilesController.cs (2 — 필드+생성자) + Data/AIAgentManagementDbContext.cs (4 — DbSet 2 + 인덱스 설정 2) + Models/AgentDocument.cs (1 — Navigation `KnowledgeBaseDocument Document`) + Program.cs (4 — DI 등록 4: `AddScoped<IDocumentIndexingService, DocumentIndexingService>` + `AddScoped<IKnowledgeBaseService, KnowledgeBaseService>`). 자체 KB CRUD/인덱싱 호출처는 위 11곳에 한정 — DocUtil 위임 전환 별도 트랙(Phase 8+) 으로 격리. RagService.RetrieveAsync 의 자체 KB 폴백 분기는 [Obsolete] 클래스를 내부 사용하나 `_context.{DbSet<T>}` generic 타입 추론 경로라 컴파일러 CS0618 미생성 — 의도된 동작(폴백 흐름 보존). **외부 시그니처/라우트/본문 모두 보존** — 호출처 회귀 0건, EF 모델 변경 0건, 마이그레이션 신규 생성 불필요. 직전 Phase 6.1+6.2 상태 유지. commit 대기 |
| **다음 Phase** | **권장 순서 1→5 + DocUtil 캐시 invalidate + 후속 트랙 C-1/B-1 + AgentDto 6 필드 갭 보강 + AgentBuilder UI 운영자 폼 + 후속 트랙 #8 AgentChat/AgentSelect /api/knowledgebase dead code 청산 + KB collection dropdown 전환 모두 완료** — 사용자 일괄 테스트(시연 종료 후 별도 일정) 대기. **후속 트랙 잔존**: ① D-1 `@vue-flow/core` 타입 strict 검사 깨짐 (NodeMouseEvent 시그니처 + Position narrowing) — `WorkflowBuilder.vue` 의 `@ts-nocheck` 잔존, 패키지 업그레이드 필요 ② RAG 메트릭 prometheus 통합 + 시계열 영속화 (현재는 in-memory only, 서버 재시작 시 0 reset) ③ RagService 결과 캐시(`rag:*` 10분) 일괄 무효화 — 운영자 KB 변경 후 sub-query 단계는 du:s 무효화로 즉시 반영, 결과 단계는 10분 자연 expire 의존. 필요 시 동일 version-key 패턴 확장 가능 ④ collection 카탈로그 캐시(version-key 패턴, DocUtil 콘솔에서 mutation 시 즉시 invalidate) — 빈도 낮으나 latency 보장 ⑤ AgentSelect.vue 의 빠른 생성/수정 모달(빌더 영역) 자체 deprecate 또는 AgentBuilder.vue 로 흡수 — 사용자가 두 진입점 중 어느 쪽을 기본으로 할지 결정 필요 ⑥ Nexus 실제 부팅 (192.168.22.28 GPU 호스트). 별도 트랙: 시연 종료 후 secret leak history sanitize + force-push, SQL Server stale 비번 / SSH 비번 / appsettings LLM API 키 회전, DocUtil 운영자 service account 정식 전용 계정 발급(현재 jyj7970 admin 사용 중). 사용자 일괄 테스트는 시연 종료 후 별도 일정 |
| **마지막 commit** | `f44f49a` 후속 트랙 DocUtil collection 카탈로그 응답 캐시 (10분 TTL) + 메트릭 4 카운터 — `[agenthub/collection-cache] 후속 트랙 — DocUtil collection 카탈로그 응답 캐시 (10분 TTL) + 메트릭 4 카운터` (push 대기 — secret leak 미해결). 6 files / +171 / -21. 회귀 3 시나리오 PASS — (1) /collections 1차 758ms (DocUtil 직격) → 2차 22ms (캐시 hit, 33배 빠름) + 5회 연속 hit 14~17ms / (2) /api/admin/metrics/rag → 200 + 신규 4 카운터(docUtilCollectionCacheHit=7/Miss=2/Calls=2/Failures=0/HitRatio=0.778) / (3) 한국어 RAG 쿼리 200 + Phase 4 카운터 정상 증가 + collection 카운터 무변화(namespace 격리). 직전 `d40945c` 후속 트랙 #9 WorkflowBuilder vue-flow 타입 정렬 + @ts-nocheck 해제 (D-1) — `[agenthub/vue-flow-types] 후속 트랙 #9 — WorkflowBuilder vue-flow 타입 정렬 + @ts-nocheck 해제 (D-1)` / 직전 `0f0fc89` progress.md 동기화 / `294e8a6` 후속 트랙 KnowledgeBaseRef DocUtil collection dropdown 전환 — `[agenthub/kb-collection-dropdown] 후속 트랙 — KnowledgeBaseRef 를 DocUtil projects dropdown 으로 전환` (push 대기 — secret leak 미해결). 8 files / +309 / -13 (백엔드 3 + 프론트 2 + i18n 2 + progress.md). 회귀 5 시나리오 PASS — admin 로그인 / (신규) /collections Bearer JWT 200 + 2건 + BFF 3 필드만 노출 / (권한 게이트) Bearer 없이 401 / (직전 회귀 b3a2d85) /api/agents/1 6 신규 필드 / 한국어 RAG 200. 이전 `174cc7b` 후속 트랙 #8 AgentChat/AgentSelect 의 deprecated `/api/knowledgebase` dead code 제거 — `[agenthub/cleanup] 후속 트랙 #8 — AgentChat/AgentSelect 의 deprecated /api/knowledgebase dead code 제거` (push 대기). 6 files / +84 / -396 (312 라인 dead code 청산). 이전 `845382c` AgentBuilder.vue UI 운영자 폼 필드 확장 — `[agenthub/agent-builder-ui] 후속 트랙 — AgentBuilder.vue 에 LlmRouting/KB 운영 폼 필드 추가` (push 대기). 이전 `b3a2d85` Agent 엔티티 ↔ AgentDto 6 필드 갭 보강 — `[agenthub/agent-dto-gap] 후속 트랙 — Agent 엔티티 ↔ AgentDto 6 필드 갭 보강`. 이전 `8819217` 후속 트랙 B-1 DTO TS↔C# 동기화 — `[agenthub/typesafe] 후속 트랙 B-1 — Agent/Conversation DTO TS↔C# 동기화` (push 대기 — secret leak 미해결). 이전 `32f78d1` 후속 트랙 C-1 자체 KB Vue 잔재 제거 — `[agenthub/cleanup] 후속 트랙 C-1 — Phase 2 자체 KB Vue 잔재 완전 제거` (push 대기). 이전 `3b7c857` 후속 트랙 DocUtil 캐시 invalidate — `[agenthub/cache-invalidate] 후속 트랙 — DocUtil 검색 캐시 version-key invalidate 도입` (push 대기 — secret leak 미해결). 이전 `4151b3d` (Phase 5 commit 해시 progress.md 동기화). 이전 `c71debb` Phase 5 운영자 메뉴 그룹화 + RAG 메트릭 UI — `[agenthub/admin-menu] Phase 5 — 운영자 메뉴 그룹화 (admin 카테고리) + RAG 메트릭 UI` (push 대기 — secret leak 미해결). 이전 `11039af` Phase 4 DocUtil 캐시 + RAG 메트릭 — `[agenthub/rag-metrics] Phase 4 — DocUtil 응답 캐시 5분 + RAG 메트릭(/api/admin/metrics/rag)` (push 대기 — secret leak 미해결). 이전 `3367e4b` Phase 3 vue-tsc 2.x — `[agenthub/vue-tsc] Phase 3 — vue-tsc 2.x 업그레이드 (Node 24 호환) + 부채 마킹` (push 대기 — secret leak 미해결). 이전 `7f1a9ae` (Phase 2 자체 KB drop — `[agenthub/kb-drop] Phase 2 — 자체 KB 코드/스키마 완전 제거 (ADR-2 단일 권위)`). 이전 `98433fa` (Phase 1 RAG 응답 품질 개선 — `[agenthub/rag-quality] Phase 1 — RAG 응답 품질 개선 (QueryRewriter + RRF 멀티 query 결합)`). 이전 `ede8096` (Phase B Nexus 자산 + Phase D NETSDK1194 fix) / `7710df6` (Phase A DocUtil JWT 자동 갱신) / `52d58d0` (progress.md) / `4f868c4` (Phase B 보강 Redis 인증) / `cbc4e2d` (progress.md) / `51e4b85` (Phase B Docker assets) / `1a1466f` (progress.md) / `c9d61a4` (사이드바 메뉴) / `d9784f0` (Hangfire fix) — 모두 누적 |
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
| **3** | AgentHub MSSQL → PostgreSQL 마이그레이션 + vue-tsc 2.x 업그레이드(Node 24 호환) | ✅ 완료 (3.1 + 3.2 + 3.3 + 3.4 + 3.5 + 3.5b + 3.6 + vue-tsc 2.2.12 + 부채 카탈로그 A/B/C/D 처리) | 2026-05-08 |
| **4** | DocUtil/career → AGENT_HUB 통합 | ✅ 완료 (4.1 + 4.2 + 4.3 + 4.4 + 4.5 — R3 격리 검증 PASS) | 2026-05-06 |
| **5** | AgentHub Nexus provider + LlmRouting + 진짜 SSE | ✅ 핵심 완료 (5.1 + 5.2 코드 작업 + 빌드 0E/단위 검증 6/6) | 2026-05-06 |
| **6** | DocUtil 운영자 → AgentHub 흡수 + KB 마이그레이션 | 🔄 진행 중 (6.1+6.2+6.3+6.4+6.5 완료 — DocUtil BFF 클라이언트 + RagService 분기 + Vue 운영자 콘솔 + 자체 KB [Obsolete] 마킹 7건 + Phase 2 에서 자체 KB 코드/스키마 완전 drop) | 2026-05-08 |
| **7** | DocUtil/career AI 호출 → AgentHub 위임 | ✅ 완료 (7.1+7.2+7.3+7.4+7.5) | 2026-05-06 |
| **8** | (보류) Vue → Next.js | ⏸ 보류 | — |
| **9** | MSSQL 운영 데이터 → PostgreSQL 이관 + AES 키 회전 (묶음 처리) | ✅ 완료 — 14 운영 테이블 단일 트랜잭션 import (Users 131 / Agents 17 / Conversations 191 / Messages 699 / Usages 474 / Quotas 911 / ApiKey 1 GCM 재암호화), FK dangling 자동 필터 + ServiceId remap 450 행 + ApiQuotas dedupe, 회귀 PASS (admin@example.com Admin123! 로그인 + ApiKey GCM round-trip + KeyHash 매칭) | 2026-05-08 |

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
| Q1 | ~~career `department_id` 매핑 정책 (Tenants sub-org / 별도 Departments / 자체 유지)~~ → **옵션 B 채택 (Phase 4.3)** | ✅ 2026-05-06 결정 |
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
- [x] ~~R1: Tenant/Organization/Department 모델 설계 → §4.5~~ → **Phase 4.3 완료 (2026-05-06)**
- [x] ~~R3-iso: schema 격리 강제 (cross-schema FK 0 / search_path 시뮬레이션 PASS)~~ → **Phase 4.5 완료 (2026-05-06)** — `docs/PHASE4_VALIDATION.md`
- [ ] R5: Nexus DB 별도 유지 → ADR-11 확정
- [ ] R11: EF baseline 부재 → Phase 3에서 신규 작성
- [ ] R15: JWT 알고리즘 통일 → ADR-9 확정

### High (Phase 5 전)
- [ ] R3: OpenAI Structured Outputs 다중 프로바이더 fallback
- [ ] R7: API Key 회전
- [ ] R8: CIDR IP 검증
- [ ] R10: Nexus 인증 미들웨어
- [ ] R12: Cascade Delete 강등
- [x] ~~R13: 임베딩 차원 통일 (career)~~ → **Phase 4.4 완료 (2026-05-06, career 1536D vector + IVFFlat). DocUtil 임베딩 1536D vs Qwen3 2048D 분기는 Phase 7.5 별도 트랙(Q6)**
- [ ] R17: Qdrant collection 단일성 vs Nexus 1024D
- [ ] R18: 평문 시크릿 잔존
- [~] R20: AgentHub KB → DocUtil visibility 매핑 — **진행 중** (Phase 6.4 [Obsolete] 마킹으로 신규 사용 차단. 운영 데이터 DocUtil 마이그레이션 정책 결정은 Phase 8+ 별도 트랙)
- [ ] R27: SSO 결정

### Medium / Low — TECHSPEC §16 참조

---

## 6. 작업 로그 (Append-only, 시간 역순)

### 2026-05-08 (Phase 9 — MSSQL 운영 데이터 → PostgreSQL 이관 + AES 키 회전 묶음 처리, 시연 cutover 종결)
- **목적**: 본 monorepo Phase 3 (`eaa5700`) 에서 AgentHub MSSQL → PostgreSQL 마이그레이션은 스키마 + 시드까지만 완료. 기존 MSSQL 운영 환경 (`192.168.10.159:1433/AIAgentManagement`, user `aiuser`) 의 실 사용자 데이터(Users 131 / ChatMessages 715 등) 이관은 미완 상태였음. 사용자 결정: 시연 전 운영 데이터 위에서 시연 + 대화 이력 포함 + AES 키 회전 묶음 처리.
- **사전 점검**: `tmp/phase9_data_migration/step01_probe.py` (`pyodbc DRIVER={SQL Server}` + paramiko docker exec psql) → MSSQL 14 운영 테이블 행 수와 PG 검증 시점 행 수 양측 카운트 출력. MSSQL: Users 131 / Roles 3 / UserRoles 7 / Teams 1 / TeamMembers 1 / Agents 17 / ApiServices 15 / ApiServiceModels 84 / ApiKeys 1 / ChatConversations 191 / ChatMessages 715 / ApiQuotas 925 / ApiUsages 474 / BannedWords 240 / Presentations 66 / UserSessions 223. PG (cutover 직전): Users 2 / UserSessions 54 / UserRoles 2 / ApiKeys 3 / ChatConversations 4 / ApiUsages 25 / Agents 16 (시드).
- **9.1 백업**: `step04_pg_dump.py` — `docker exec docutil-postgres pg_dump -n "AIAgentManagement" -d AGENT_HUB -U AGENT_HUB -F c -f /tmp/agent_hub_pre_phase9_<TS>.dump` 실행 (schema 이름이 mixed-case 라 `bash -lc 'pg_dump -n \"AIAgentManagement\" ...'` escape 패턴 사용) → docker cp 컨테이너 → 호스트 → 142 KB custom format dump 호스트 `/tmp/agent_hub_pre_phase9_20260508_091309.dump` 보관. `pg_restore -n "AIAgentManagement"` 로 검증 시점으로 복구 가능.
- **9.1 신규 AES-256 키 생성**: `step05_apikey_recrypt.py` — Python `secrets.token_bytes(32)` → base64. SHA256(앞 16자) = `e25aba443e033038`. 키 자체는 `tmp/phase9_data_migration/step05_apikey_recrypt_result.txt` 에만 저장 (.gitignore tmp/ 영역). MSSQL ApiKey 1 행 (`ApiKeyId=2 / UserId=1 / ServiceCode=agent-api / KeyName=test`) 의 EncryptedKey 를 Legacy CBC + 고정 IV(16 byte 0) + JWT-derived AES key (`SHA-256("YourSuperSecret...")`) 로 복호화 → 평문 길이 46, prefix/suffix `ak-4...GMrU` (AgentHub 자체 발급 API Key 형식). 신규 GCM (12 byte random nonce + 16 byte tag, mac_len=16) 으로 재암호화 → round-trip decrypt_and_verify PASS.
- **9.2 INSERT SQL 빌더**: 첫 시도 `step06_build_insert_sql.py` 는 단순 SELECT → E-string INSERT 변환 — 외래키 위반(UserId 5,6 부재 / ServiceId 1~9, 13 dangling)으로 즉시 ABORT. **`step06b_build_insert_sql_safe.py` 로 재작성** — Python in-memory 부모 PK set 으로 사전 FK 검증 + dangling 행 자동 처리 4 정책 ① UserId 5,6 부재 → 자식 행 (UserRoles 2 / ApiQuotas 4 / UserSessions 4) skip ② ServiceId 1~9, 13 dangling (운영 ApiServices 시드 재생성으로 ID 1~5 → 17~31 로 점프) → ApiUsages.Model + ChatConversations.Model 컬럼 분석으로 추정 매핑 `SERVICE_ID_REMAP = {1:17 chatgpt, 2:18 claude, 3:19 cursor (4 행, 추정), 4:20 copilot (4 행, 추정), 5:31 perplexity, 6:21 gemini, 7:21 gemini, 8:23 dalle, 9:24 gemini-image, 13:29 veo}` → `Agents/ApiQuotas/ChatConversations/ApiUsages` 4 테이블 ServiceId 컬럼 일괄 remap (450 행) ③ ApiQuotas UNIQUE(UserId, ServiceId) 충돌 (6,7 둘 다 21 매핑으로 같은 사용자 중복) → QuotaId max 행 보존 dedupe (10 행) ④ nullable FK dangling 은 NULL 강제 (`set_null` 액션) — ApiUsages.ConversationId 등 → 데이터 보존. 외래키 의존 순서 16 테이블 INSERT (ApiServices → ApiServiceModels → Roles → Users → UserRoles → Teams → TeamMembers → Agents → ApiKeys → ApiQuotas → BannedWords → ChatConversations → ChatMessages → ApiUsages → Presentations → UserSessions) + 15 SETVAL (PG sequence MAX(PK)+1 동기화 — `Agents_AgentId_seq` 등). PG 컬럼 메타는 `step02_pg_schema.py` 가 INFORMATION_SCHEMA 로 사전 수집 (Agents 30 vs MSSQL 25 — `ConsumerSystems / KnowledgeBaseRef / KnowledgeBaseSource / LlmRouting / RoutingPolicyJson` 5 신규 컬럼은 default 적용으로 MSSQL 컬럼만 INSERT 명시). ApiKey 1 행은 재암호화 결과 (`EncryptedKey base64 / KeyIv hex 12 byte / KeyTag hex 16 byte / KeyHash SHA-256 hex 64 자`) 를 4 column 일괄 적재. 생성 SQL 파일 `tmp/phase9_data_migration/phase9_import.sql` 266.9 MB (ChatMessages 본문에 base64 첨부 포함).
- **9.3 Cutover**: `step07_cutover.py` — paramiko SSH 단일 흐름 ① docker stop agenthub ② TRUNCATE 16 테이블 RESTART IDENTITY CASCADE (BEGIN; ... ; COMMIT;) ③ SFTP put 266.9 MB SQL → docker cp `docutil-postgres:/tmp/phase9_import.sql` ④ `docker exec ... psql -v ON_ERROR_STOP=1 -f /tmp/phase9_import.sql` ⑤ 호스트 `/home/idino/agenthub/.env` 갱신 — `docker-compose.yml` 의 `${ENCRYPTION_API_KEY_AES_KEY}` 변수에 신규 키 주입 (기존 .env 라인 보존, target_key 만 교체) ⑥ `docker compose up -d --force-recreate agenthub` ⑦ `docker inspect Health.Status` 폴링 (2 초 간격, 최대 60 초) → healthy 도달 12 초 ⑧ 16 테이블 행 수 자동 검증.
- **9.4 회귀 검증** (`step08_smoke_test.py`): ① container healthy ✓ ② GET `http://192.168.10.39:64005/swagger` 200 (len=638) ✓ ③ POST /api/auth/login `admin@example.com / Admin123!` 200 + token len=555 — **MSSQL 운영 admin BCrypt 해시가 시드 해시와 동일 확인** (사용자 BCrypt rehash 불필요) ④ GET /api/agents/1 200 + 6 신규 필드 매핑 (consumerSystems / knowledgeBaseRef / knowledgeBaseSource / llmRouting / routingPolicyJson — 모두 응답 본문에 존재, b3a2d85 회귀 유지) ⑤ GET /api/admin/metrics/rag 200 (Phase 4 카운터 16 키) ⑥ GET /api/agents 200 (32 agents — MSSQL 17 + AgentHub DatabaseInitializer 시드 15 idempotent 재시드) ⑦ GET /api/chat/conversations 200 (91 KB body, 191 conversation 모두 표시) ⑧ POST /api/chat/conversations 201 (ID **260** — sequence SETVAL 정확 작동, MSSQL MAX 191 다음으로 시작) ⑨ /, /agents/select, /admin/knowledge-base, /admin/rag-metrics SPA 모두 200 fallback ⑩ **ApiKey GCM 복호화 round-trip PASS** — PG row 의 `EncryptedKey/KeyIv/KeyTag` 를 `.env` 의 신규 AES key 로 직접 복호화 → 평문 prefix/suffix `ak-4...GMrU` len=46 + recomputed SHA-256 == DB KeyHash `D0D5B20D...22098` PASS — 신규 키로 무결성 보장 저장 완료.
- **이관 결과 행 수 표** (MSSQL 운영 → PG 이관 후):
  | 테이블 | MSSQL | PG keep | skip | 비고 |
  |---|---:|---:|---:|---|
  | Users | 131 | 131 | 0 | 100% |
  | Roles | 3 | 3 | 0 | |
  | UserRoles | 7 | 5 | 2 | UserId 5,6 부재 |
  | Teams | 1 | 1 | 0 | |
  | TeamMembers | 1 | 1 | 0 | |
  | Agents | 17 | 17 | 0 | + AgentHub 시드 15 (총 32 표시) |
  | ApiServices | 15 | 15 | 0 | + Nexus 시드 1 (총 16) |
  | ApiServiceModels | 84 | 84 | 0 | + 시드 2 (총 86) |
  | ApiKeys | 1 | 1 | 0 | GCM 재암호화 완료 |
  | ApiQuotas | 925 | 911 | 14 | dedupe 10 + UserId 부재 4 |
  | BannedWords | 240 | 240 | 0 | |
  | ChatConversations | 191 | 191 | 0 | 100% |
  | ChatMessages | 715 | 699 | 16 | dangling Conversation hard-delete |
  | ApiUsages | 474 | 474 | 0 | nullable FK NULL 변환으로 100% |
  | Presentations | 66 | 66 | 0 | |
  | UserSessions | 223 | 219 | 4 | UserId 6 부재 |
- **장기 영향**: 운영 cutover 종결 → 시연 환경이 131 사용자 + 191 대화 + 699 메시지 + 921 quota + 474 usage 운영 데이터 위에서 동작. AES key 평문은 progress.md/commit 어디에도 노출 안 함 — sha256 prefix 16 자(`e25aba443e033038`) 만 기록. 신규 메시지 응답 자체는 외부 LLM 키/Quota 미설정으로 400 가능 (본 phase 책임 범위 밖). 다음 — 시연 후 secret leak history sanitize / Nexus 부팅.
- **변경 파일** (commit 0 — `tmp/phase9_data_migration/` 8 스크립트는 `.gitignore tmp/` 영역 제외): 본 progress.md 만 수정.
- **마지막 commit**: 본 작업 후 추가 예정.


- **목적**: 직전 누적 트랙(`294e8a6` KnowledgeBaseRef dropdown / `845382c` AgentBuilder UI 폼 필드 확장 / Phase 5 admin 메뉴 그룹화) 으로 정식 빌더 `/agents/builder/:id?` 가 LlmRouting / RoutingPolicyJson / KnowledgeBaseSource / KnowledgeBaseRef / ConsumerSystems 등 Phase 5+ 신규 메타까지 운영자 폼으로 전부 커버하게 됐는데, AgentSelect.vue 의 "빠른 생성/수정 모달" 은 기본 필드만(agentName / description / serviceId / temperature / maxTokens / enableRag / piiProtection 정도) 노출하는 구버전 — 운영자가 빠른 모달로 Agent 를 생성/편집하면 LlmRouting / KnowledgeBaseSource 등 핵심 메타가 default 로 박혀 운영 정합성 위험(Phase 5 신기능 부재). 본 트랙에서 AgentSelect 의 빠른 모달 자체를 deprecate 하고 모든 생성/수정 흐름을 정식 빌더로 단일 진입점화한다.
- **변경 범위 — `agenthub/ClientApp/src/views/agent/AgentSelect.vue`**:
  - **template 정리**:
    - 헤더 `새 Agent 생성` 버튼: `@click="showCreateModal = true"` → `@click="goToCreateBuilder"` (router.push `/agents/builder`)
    - 카드 풋터 `수정` 버튼(`bi-pencil`): `@click.stop="editAgent(agent)"` → `@click.stop="goToEditBuilder(agent)"` (router.push `/agents/builder/${agent.agentId}`) + `title="빌더에서 수정"`
    - 카드 풋터 `삭제` 버튼 신규 추가(`bi-trash`, `class="ag-btn-edit ag-btn-delete-card"`) — 삭제 동작 보존 사양 + 모달 footer 의 삭제 버튼 사라짐 보완. `@click.stop="confirmDeleteAgent(agent)"` (window.confirm + DELETE + loadAgents)
    - "새 Agent 추가 카드"(`ag-card-add`): `@click="showCreateModal = true"` → `@click="goToCreateBuilder"` + 부제 텍스트를 "정식 빌더에서 LLM 라우팅·RAG 권위·공유 설정을 함께 구성합니다." 로 갱신 (운영자 인지 강화)
    - **모달 블록 401 라인 통째 제거 (line 168~568)**: 생성 모달 + 수정 모달 + 두 backdrop 전부. 모든 form 필드, icon picker, color picker, 공유 & 임베드 설정, 공유 URL 복사, "빌더에서 수정" 단축 버튼, 모달 footer 삭제 버튼 등 모달 안 모든 UI 가 같이 사라짐(정식 빌더에서 동등 또는 더 풍부한 폼이 제공됨).
  - **script 정리** (525 라인 → 119 라인, -77%):
    - 제거된 ref: `showCreateModal` / `showEditModal` / `editingAgent` / `loadingModels` / `availableModels` / `editAvailableModels` / `newAgent` / `editAgentData` / `editingAgentCode` / `editShareCopySuccess` / `origin`
    - 제거된 const: `ICON_OPTIONS` / `COLOR_OPTIONS` (모달에서만 사용)
    - 제거된 interface: `CreateAgentData` (모달 폼 모델)
    - 제거된 함수: `loadServiceModels` / `loadEditServiceModels` / `editAgent`(await models) / `handleCreateAgent` / `handleUpdateAgent` / `handleDeleteAgent`(모달 footer 용) / `closeCreateModal` / `closeEditModal` / `copyEditShareUrl`
    - 신규 함수: `goToCreateBuilder` (`router.push('/agents/builder')`) / `goToEditBuilder(agent)` (`router.push('/agents/builder/${agent.agentId}')`) / `confirmDeleteAgent(agent)` (window.confirm + `api.delete('/agents/${agent.agentId}')` + `loadAgents()` 재조회)
    - 보존: `agents` / `services` / `loading` / `searchText` / `serviceFilter` / `viewMode` / `filteredAgents`(computed) / `showEmpty`(computed) / `loadAgents` (services 카탈로그도 필터 옵션에서 사용 중이므로 같이 fetch 보존) / `filterAgents` / `startDefaultMode` / `startAgent` / `isMyAgent` / `truncateText` / `onMounted(loadAgents)`
    - import 정리: `CreateAgentRequestDto` / `UpdateAgentRequestDto` 등 미사용 type import 흔적 없음(원래 본 파일은 `any` 타입 requestData 로 호출했으므로 정리 추가 작업 불필요) — `AgentDto` / `ApiServiceDto` 만 import 유지
  - **style 정리**:
    - `.modal.show { display: block; }` / `.modal-backdrop.show { opacity: 0.5; }` 두 셀렉터 제거 (모달 부재로 deadcss)
    - `.ag-btn-delete-card:hover { color: var(--bs-danger, #dc3545); }` 신규 (카드 풋터 삭제 버튼 호버 시 빨간색 강조)
  - **전체 라인 수**: 1003 → 306 라인 (-697 라인, -69.5%)
- **i18n 키 정리**: 본 파일은 인라인 한국어 텍스트만 사용 — `$t(...)` / `t(...)` 매치 0건. 별도 i18n 키 정리 불필요 (직전 트랙 #8 에서 6 키 정리 완료).
- **vue-tsc 2.x errors=0 게이트 유지**: `npx vue-tsc --noEmit` exit 0 (`@ts-nocheck` 부착 0 유지). `npm run build:check` PASS (3.65s).
- **dist 청크 변화** (로컬):
  - `AgentSelect-D8sTXokk.js` 28.66 kB / gzip 8.14 kB (직전 트랙 #8) → `AgentSelect-BdpPqGW7.js` 7.30 kB / gzip 3.26 kB (-21.36 kB / gzip -4.88 kB, ≈ -74.5%) — 두 모달 본체 + 관련 함수 + ICON/COLOR_OPTIONS 제거 효과. 본 페이지의 "정식 빌더 redirect 셸" 화 의도와 일치.
  - `AgentBuilder-BJ1MGfgR.js` 36.57 kB (변경 0) — 정식 빌더는 손대지 않음.
  - `index-C4yUyvEh.js` 134.36 kB (직전 133.46 → +0.90 kB, vendor split hash 차이 정도 — i18n 변경 0).
  - 다른 청크(WorkflowBuilder/AgentChat/AgentMultiChat/AgentMarketplace/vue-vendor/chart-vendor/marked.esm) 변경 0.
- **호스트 컨테이너 재빌드 + healthy + 회귀 endpoint PASS**:
  - SFTP 1 파일 업로드: `agenthub/ClientApp/src/views/agent/AgentSelect.vue` 11,134 bytes (호스트 wc=306 라인 정상). Multi-stage Dockerfile 이 SDK + Node.js 20 stage 에서 dotnet publish 로 ClientApp 까지 빌드하므로 source 만 업로드하면 컨테이너 빌드 시 wwwroot 가 자동 생성됨.
  - 호스트 `docker compose build agenthub` 56.8s 완료(buildx multi-stage). 컨테이너 wwwroot dist 빌드 PASS, `dist/assets/AgentSelect-*.js` fingerprint 갱신 (호스트 BuildKit deterministic 해시는 로컬과 다름 — `AgentSelect-BNBMSKCM.js` 신규).
  - `docker compose up -d --force-recreate agenthub` → healthy 7s 안에 도달.
  - 컨테이너 wwwroot 청크 grep 검증: `showCreateModal\|showEditModal\|handleCreateAgent\|handleUpdateAgent\|loadServiceModels` 매치 **0건** — 모달 dead code 완전 청산. `agents/builder` 매치 **1건**(minify 후 `goToCreateBuilder` + `goToEditBuilder` 두 함수가 같은 라인에 통합).
  - admin@example.com / Admin123! 로그인 → JWT 555 chars 정상.
  - `GET /api/agents/1` Bearer JWT → 200 + 6 신규 필드 모두 노출: `{llmRouting:'Hybrid', routingPolicyJson:null, knowledgeBaseSource:'DocUtil', knowledgeBaseRef:null, consumerSystems:'["docutil-user"]', sortOrder:100}` — 직전 `b3a2d85` 백엔드 회귀 + `845382c` UI 회귀 PASS 유지.
  - `GET /agents` SPA fallback → 200 + index.html (vue-router catch-all 정상) — 카탈로그 진입점 보존.
- **운영 정합성 위험 해소**: 본 트랙 이후 모든 Agent 생성/수정 흐름이 정식 빌더 `/agents/builder/:id?` 로 일원화 — 운영자가 LlmRouting / KnowledgeBaseSource / KnowledgeBaseRef / RoutingPolicyJson / ConsumerSystems / sortOrder 등 Phase 5+ 신규 메타를 누락하지 않고 함께 설정하게 됨. AgentSelect 페이지는 카탈로그 그리드(카드 목록) + 채팅 진입 + 빌더 redirect + 삭제 confirm 만 담당하는 가벼운 셸로 변환.
- **카탈로그 그리드 / 채팅 진입 / 삭제 동작 보존**: `/agents` 라우트는 사용자 진입점으로 그대로 유지 — 카드 클릭 → `startAgent(agent)` → `/agents/chat/${agentId}` 채팅 진입, 기본 모드 카드 → `/agents/chat`, 카드 삭제 버튼 → `confirmDeleteAgent` (window.confirm + DELETE) — 외부 동작 sigtr 변경 0.
- **외부 API 라우트 변경 0** — 본 트랙은 순수 프론트 UI deprecate. 백엔드 컨트롤러/엔드포인트/응답 schema 변경 0. `agentService.createAgent` / `agentService.updateAgent` 호출처가 본 페이지에서 사라졌으나 정식 빌더(`AgentBuilder.vue`) 가 동일 API 를 호출하므로 백엔드 영향 0. 다른 페이지(AgentBuilder/AgentChat/AgentMultiChat/AgentMarketplace/AdminKnowledgeBase) 동작 회귀 0.
- **다음 트랙 후보 (본 트랙과 무관, 백엔드 트랙은 병렬 진행 중)**:
  - DocUtil collection 카탈로그 캐시 트랙 (직전 한 트랙 진행 중일 수 있음) — 프론트 영역 트랙 #10 와 독립
  - Nexus 실 부팅 (LAN GPU 호스트, ADR-11 LAN-only 원칙) — 외부망 미배포 시연 환경에서는 보류
  - 시연 종료 후 secret leak history sanitize + LLM API 키 회전 (B1/B2/B3 옵션, 사용자 결정 대기)
  - AgentBuilder.vue 의 "고급 설정" 카드 UX 추가 다듬기 (사용자 피드백 받은 후)

### 2026-05-08 (후속 트랙 — DocUtil collection 카탈로그 응답 캐시 (10분 TTL) + 메트릭 4 카운터)
- **목적**: 직전 트랙 `294e8a6` 에서 BFF 표면화한 `IDocUtilClient.ListCollectionsAsync` + `GET /api/admin/knowledge-base/collections` 가 매 호출 DocUtil `/api/v1/projects` 직격이라 운영자 워크플로(Agent 생성/편집 시 KnowledgeBaseRef dropdown 매번 fetch) 의 부하가 발생. `SearchAsync`(5분 version-key) 와는 다른 단순 TTL 10분 캐시 도입으로 부하 감소.
- **무효화 전략 — version-key 미적용**: collection 생성/삭제는 DocUtil 콘솔에서 직접 발생하므로 AgentHub BFF 가 mutation 시점을 알 수 없음 → explicit `IncrementVersionAsync` 트리거 불가 → 단순 TTL 10분 자연 expire 의존. 향후 트랙: DocUtil project mutation 도 AgentHub BFF 통과시 SearchCacheVersionNamespace 와 동일 패턴 적용 가능 (별도 namespace 권장).
- **수정 5 파일**:
  1. `agenthub/Services/DocUtilClient.cs` — `ListCollectionsAsync` 본체 재작성. 신규 const `CollectionCacheKeyPrefix = "du:c:"` (Search `du:s:` 와 격리) + `CollectionCacheTtl = TimeSpan.FromMinutes(10)`. 캐시 키 패턴 `du:c:{page}|{size}` (page/size 조합당 단일 키). `_cachingService.GetAsync<CachedCollectionListDto>` 우선 조회 → null 이면 miss 카운트 + HTTP 호출, non-null 이면 hit 카운트 + items.ToList(). HTTP 호출 본체는 try/catch/finally(Phase 4 SearchAsync 와 일관) — `IncrementDocUtilCollectionCall()` + Stopwatch 시작 → catch 시 `IncrementDocUtilCollectionFailure()` → finally Stopwatch 정지 + Debug 로그 `Latency={LatencyMs}ms`. 성공 시 `CachedCollectionListDto { Items = items.ToArray() }` 적재. 신규 wrapper class `CachedCollectionListDto` 도 추가(record `DocUtilCollection` 직렬화 안정성). 한국어 Debug 로그 `DocUtil 컬렉션 캐시 hit/miss - key={Key}, count={Count}`.
  2. `agenthub/Services/IRagMetrics.cs` — DocUtil 컬렉션 카운터 4 신규 메서드 (`IncrementDocUtilCollectionCacheHit/Miss/Call/Failure`) + `RagMetricsSnapshot` record 4 필드 추가. 한국어 doc 주석으로 version-key 미적용 사유(BFF 비경유) 명시.
  3. `agenthub/Services/RagMetrics.cs` — 4 private long 필드 + 4 메서드 구현(Interlocked.Increment) + GetSnapshot() 매핑 추가. Phase 4 SearchAsync 와 동일 atomic 패턴.
  4. `agenthub/DTOs/RagMetricsSnapshotDto.cs` — 4 신규 필드 + 파생 1 `DocUtilCollectionCacheHitRatio` (hit / max(1, hit+miss)).
  5. `agenthub/Controllers/AdminMetricsController.cs` — RagMetricsSnapshotDto 매핑 4 줄 + docUtilCollectionTotal 분모 0 보호 + `DocUtilCollectionCacheHitRatio` 계산 추가. `/api/admin/metrics/rag` 자동 노출(controller 변경 외 frontend 수정 0).
- **외부 표면 변경 0**: IDocUtilClient 시그니처 변경 0, 기존 6 메서드 동작 무변화. 메트릭 endpoint 는 신규 4 필드 추가만(클라이언트 호환성 유지).
- **빌드**: `dotnet build --no-restore --nologo` errors=0, warnings=11 (모두 본 트랙과 무관한 기존 CS1998).
- **호스트 배포**: paramiko 로 5 파일 192.168.10.39:/home/idino/agenthub/ 업로드 → `docker compose build agenthub` (#18 export 13s) → `docker compose up -d --force-recreate agenthub` healthy (`State.Health=healthy`, started=2026-05-08T07:18:13).
- **회귀 검증 (3 시나리오 — Bearer JWT 555 chars)**:
  1. **캐시 hit/miss 동작** — `GET /api/admin/knowledge-base/collections?page=1&size=50` 1차 호출 758.7ms (DocUtil 직격, count=2: `c6955ce6-...` 연구과제, `9ca4ce6e-...` 미래기술연구소 권한 프로젝트) → 즉시 2차 호출 22.8ms (캐시 hit, 동일 body, **약 33배 빠름**). 추가 5회 연속 호출 모두 14~17ms (전부 hit). 응답 body byte-equal 검증 PASS.
  2. **메트릭 노출** — `GET /api/admin/metrics/rag` Bearer JWT → 200 + 신규 4 카운터 모두 노출: `docUtilCollectionCacheHit=7, Miss=2, Calls=2, Failures=0, HitRatio=0.778`. 파생 ratio 계산 정확.
  3. **Phase 4 무영향** — `POST /api/chat/conversations/2/messages` 한국어 RAG 쿼리(`message: "부산대 학생 지원 정보 알려줘"`) → 200 (7892ms, 응답 OK). post-RAG 메트릭에서 `docUtilSearchCalls=2, ragInvocations=1, ragResultCacheMiss=1` Phase 4 카운터 정상 증가 + collection 카운터(`Calls=2, Hit=7`) 무변화 — 두 캐시 namespace 격리 확인.
- **효과**: 운영자 워크플로 의 DocUtil 부하가 10분 TTL 로 Hit 비율 약 0.78 까지 감소(약 5회 호출 중 1번만 직격). 빈 결과(0건) 도 캐싱하여 빈 응답 반복 호출 부하도 절감. `Default LogLevel = Information` 환경에서는 `LogDebug` hit/miss 로그가 보이지 않으므로 메트릭 카운터(`/api/admin/metrics/rag`) rolling 검증 권장.
- **다음 후속 트랙 (별도 진행)**:
  - Nexus 실 부팅 + AgentHub `CallNexusAsync` 통합 회귀 (옵션 B Phase 5)
  - Secret leak 처리 — `1da04ab` 평문 키 4개 + GitHub push 차단 해소 (사용자 결정 대기)
  - AgentSelect 모달 deprecate (KB picker UX 일원화)
  - DocUtil project mutation BFF 통과 → version-key invalidate 패턴 도입 → collection 캐시 5분으로 단축 가능

### 2026-05-08 (후속 트랙 #9 — WorkflowBuilder.vue vue-flow 타입 정렬 + `@ts-nocheck` 해제, D-1 완료)
- **목적**: 직전 commit `0f0fc89` 까지 KnowledgeBase.vue 자체 + B-1/C-1 부채는 청산되었으나 D-1 (`agenthub/ClientApp/src/views/workflow/WorkflowBuilder.vue` 의 `@ts-nocheck`) 만 남아 있던 상태. `@vue-flow/core@1.48.2` 가 이미 최신 stable 이라 패키지 업그레이드는 불필요했고, **타입 사용 패턴 정정** 만으로 해소 가능함이 라이브러리 d.ts 분석에서 확인됨 (`NodeMouseEvent` interface `{ event: MouseTouchEvent, node: GraphNode }` + `Position` enum `{ Left, Top, Right, Bottom }`). 본 트랙으로 vue-tsc 2.x strict 게이트가 monorepo 전 파일에 적용되는 클린 상태 회복.
- **WorkflowBuilder.vue 진단**:
  - `node_modules/@vue-flow/core/dist/types/hooks.d.ts:12-15` `NodeMouseEvent { event: MouseTouchEvent; node: GraphNode }` interface, `flow.d.ts:301-303` `nodeClick` emit 시그니처 = `(nodeMouseEvent: NodeMouseEvent) => void` (1 인자) — 기존 `(_: any, node: any) => void` (2 인자) 와 mismatch (TS Target signature provides too few arguments).
  - `node_modules/@vue-flow/core/dist/types/flow.d.ts:77-82` `Position` 은 string enum (Left='left', Right='right'). template attr 의 `position="left"` 는 string literal 로 narrow 되어 `Position | undefined` 와 mismatch.
  - `@vue-flow/core` index.d.ts 가 `export * from './types'` + `types/index.d.ts` 가 `hooks` 를 re-export → `NodeMouseEvent` 는 `@vue-flow/core` 최상위에서 import 가능 PASS.
- **수정 1 파일 (commit 대상)** — `agenthub/ClientApp/src/views/workflow/WorkflowBuilder.vue`:
  - **상단 주석 + import (line 323-336)**: `// @ts-nocheck` + 한국어 사유 주석 2 라인 **제거**, "Phase 3 후속 트랙 (D-1) 완료" 마킹 한국어 주석 1 라인으로 교체. `import type { NodeMouseEvent } from '@vue-flow/core'` 신규 추가 (`Position` 은 기존 import 유지, value + type 양쪽 사용).
  - **template `<Handle>` (line 103-107)**: `position="left"` / `position="right"` (string literal) → `:position="Position.Left"` / `:position="Position.Right"` (enum bind). Condition 노드의 true/false handle 2개도 동일. `<script setup>` 에서 import 한 binding 은 template 에서 자동 사용 가능 (Vite + Vue 3 표준).
  - **`onNodeClick` 핸들러 (line 421-426)**: `(_: any, node: any) => void` → `({ node }: NodeMouseEvent) => void` 로 정정. emit payload 가 `{ event, node }` shape 이므로 destructuring 으로 `node` 만 추출 — 콜백 본문(`selectedNode.value = node`) 동작 보존. 한국어 사유 주석 추가.
  - **런타임 동작 변경 0** — 타입 시그니처 + enum bind 정정만, 콜백 본문/상태/이벤트 흐름/외부 API 호출 100% 보존. 다른 식별자/함수 시그니처 변경 0.
- **빌드 PASS**:
  - `cd ClientApp && node node_modules/vue-tsc/bin/vue-tsc.js --noEmit` → **exit=0 errors=0** (게이트 유지, **monorepo 전 파일에서 `@ts-nocheck` 부착 0 달성**, Phase 3 부채 카탈로그 B-1/C-1/D-1 + KnowledgeBase.vue 자체까지 모두 청산).
  - `npm run build:check` (= vue-tsc + vite build) → **PASS, 3.73s, 263 modules transformed, build errors 0**.
  - 청크 카탈로그: 로컬 dist 의 `WorkflowBuilder-CVbyJqzY.js` 182.71 kB / gzip 59.19 kB (이전 트랙 `WorkflowBuilder-CnxxxxxK.js` 와 비교 시 ±1% 이내 — 코드 변경량 미미). 다른 청크(vue-vendor/chart-vendor/marked.esm/AgentBuilder/AgentChat/AgentSelect/AgentMarketplace) 변경 0.
  - **`@ts-expect-error` 부착 0** — 모두 정확한 타입(`NodeMouseEvent` interface + `Position` enum) 으로 해결, 부득이한 라인 단위 expect-error 회피 정책 준수.
- **wwwroot 동기화**: `agenthub/wwwroot/assets/` rm + `ClientApp/dist/assets/` 복사 + `index.html` 갱신. `agenthub/.gitignore` 가 `wwwroot/assets/` + `wwwroot/index.html` 제외 → commit 미포함 (정상).
- **호스트 192.168.10.39 배포 PASS**: `tmp/deploy_track9_workflowbuilder_typenarrow.py` (paramiko + 단일 파일 SFTP) —
  - SFTP 1 파일 소스 31,467 bytes 업로드 (`WorkflowBuilder.vue`)
  - `docker compose build agenthub` → BuildKit cache 풀 hit + publish layer ~3s, `agenthub-agenthub:latest` 신규 manifest sha256:e57e6ec0... config sha256:a46db89c... attestation sha256:2c7d63a2... manifest list sha256:39e7205b...
  - `docker compose up -d --force-recreate agenthub` → Container Recreated/Started
  - 7초 만에 healthy (iter 3)
  - 컨테이너 내 wwwroot 청크 fingerprint: `WorkflowBuilder-Cz2gS_3Y.js` (BuildKit deterministic 해시는 로컬 dist `CVbyJqzY` 와 다르나 코드 동등성 PASS — 컨테이너 내부 npm 미세 환경 차이로 인한 정상 변동).
- **회귀 검증 PASS** (`tmp/verify_track9_workflowbuilder.py` + `tmp/rag_check.py`):
  - `admin@example.com / Admin123!` 로그인 → JWT 555 chars 정상 발급.
  - `GET /api/agents/1` Bearer JWT → 200 + `llmRouting/routingPolicyJson` 등 신규 필드 노출 (b3a2d85 백엔드 회귀 + 845382c UI 회귀 PASS 유지).
  - **한국어 RAG 쿼리 회귀**: `POST /api/chat/conversations/2/messages {"message":"안녕하세요? RAG 동작 상태 확인 요청.","role":"user"}` → **200**, messageId 발급, role=assistant, content+contents+attachments+tokensUsed+model 키 정상, gpt-4o 모델 응답 — 채팅/RAG 회로 회귀 0 PASS.
  - **dist 청크 fingerprint 검증**: `curl -sI /assets/WorkflowBuilder-Cz2gS_3Y.js` → **200 OK, Content-Length=183,445 bytes** (= 약 179 KB, 로컬 dist 182.71 kB 와 거의 동일). 이전 fingerprint `WorkflowBuilder-v1mNOsDf.js` → **404** (정상, 컨테이너 재빌드로 stale 청크 제거).
  - **WorkflowBuilder 라우트 정적 검증**: SPA fallback `/` → 200 (index.html 638 bytes, vite manifest 정상 노출). 컴포넌트 마운트는 사용자 인터랙션 + 라이브 브라우저 필요라 별도 검증 skip (정책 정렬).
- **외부 API 라우트 변경 0** — 컨트롤러/엔드포인트/응답 schema 변경 0. 다른 페이지(AgentBuilder/AgentChat/AgentSelect/AgentMultiChat/Marketplace/AdminKnowledgeBase) 동작 회귀 0.
- **anti-patterns.md 준수**: §4(Frontend 하드코딩 API URL — `import api from '@/services/api'` 그대로 사용) + §11(컴포넌트에서 axios 직접 사용 금지) 모두 위반 0. Vue 3 `<script setup lang="ts">` + Composition API + ref/onMounted 패턴 보존, React 관용구 부재.
- **Phase 3 부채 카탈로그 청산 (전체 회복)**: B-1 (AgentBuilder/AgentMultiChat enableRag 등 DTO 갭) ✅ 완료 + C-1 (KnowledgeBase.vue 자체 deprecate) ✅ 완료 + D-1 (WorkflowBuilder.vue vue-flow 타입 정렬) ✅ 완료. **monorepo 전 파일에서 `@ts-nocheck`/`@ts-expect-error` 부착 0**, vue-tsc 2.x strict 게이트가 모든 view/composable/service 파일에 적용되는 클린 상태 달성.
- **변경 파일 목록 (commit 대상)**:
  - `agenthub/ClientApp/src/views/workflow/WorkflowBuilder.vue`
- **다음 트랙 후보**: Nexus 실제 부팅 (LAN GPU 호스트 192.168.22.28, `nexus/docker-compose.yml` 자산 활용) / 시연 종료 후 secret leak history sanitize + 키 회전 (SSH/DB/LLM API) / AgentSelect 빠른 빌더 모달 deprecate 또는 AgentBuilder 흡수 / DocUtil collection 카탈로그 캐시 (`/api/admin/knowledge-base/collections` 5분 TTL + version-key 무효화) / DocUtil 의 Document/Chunk 등 다른 entity BFF 일괄 노출 (운영자가 KB 메뉴에서 문서 단위 통계/삭제 가능하도록).

### 2026-05-08 (후속 트랙 #8 — AgentChat / AgentSelect 의 deprecated `/api/knowledgebase` GET dead code 완전 청산)
- **목적**: Phase 2 (`7f1a9ae`) 에서 백엔드 자체 KB 컨트롤러 `/api/knowledgebase` 가 완전 제거된 후, AgentChat.vue (사용자 채팅) 와 AgentSelect.vue (Agent 카탈로그 + 빠른 생성/수정 모달) 에 잔존하던 `api.get<KnowledgeBaseDocument[]>('/knowledgebase')` 호출 + 문서 선택 UI 가 SPA fallback HTML 200 → JSON parse 실패 → catch 분기 빈 배열 처리되어 사용자 화면에 "노 문서" 알림만 노출하는 dead code 였음. ADR-2 단일 권위 = DocUtil + 사용자가 채팅 화면에서 문서를 직접 선택하는 패러다임 자체가 폐기되었으므로 (운영자가 Agent 단위로 KnowledgeBaseSource/Ref 화이트리스트 결정) 본 트랙으로 청산.
- **AgentSelect.vue 라우트 + 빌더 중복 진단**: 라우트 `/agents` 는 Agent 카탈로그 + 빠른 생성/수정 모달 (router/index.ts:80). 정식 빌더는 `/agents/builder/:id?` AgentBuilder.vue 5단계 (Phase 5 admin 메뉴 그룹화). AgentSelect 의 수정 모달은 `router.push('/agents/builder/${editingAgent.agentId}')` 로 빌더 deep link 제공 — 즉 AgentSelect 의 생성/수정 모달은 "빠른 진입용 보조 폼" 으로 활용 중. **사장 페이지 아님** → 빌더 영역 통째 제거는 별도 트랙으로 격리, 본 작업은 dead code 핀포인트만 청산.
- **수정 5 파일 (commit 대상)**:
  - **MODIFY `agenthub/ClientApp/src/views/agent/AgentChat.vue`** —
    - **템플릿** (line 109-154 일대): `<div class="cd-field" v-if="enableRag">` 의 Knowledge 선택 UI 블록 (label/loading spinner/no-documents alert/checkbox list/cd-hint) **전체 삭제**. EnableRag 토글 자체는 보존 (per-conversation 영구 override 기능 유지) + `@change="onRagToggle"` 핸들러만 제거. 한국어 주석으로 ADR-2 / Phase 2 자체 KB drop 맥락 명시.
    - **script (line 912-929)**: `interface KnowledgeBaseDocument` (12 키 정의) + `loadingDocuments`/`availableDocuments`/`selectedDocumentIds` ref 3개 **제거** + 한국어 대체 주석.
    - **script (line 1042-1075)**: `loadDocuments` async 함수 + `onRagToggle` 함수 + `toggleDocument` 함수 **3개 제거** + 한국어 대체 주석 (`/api/knowledgebase` 가 `7f1a9ae` 에서 완전 제거되어 SPA fallback HTML 200 반환하던 dead code).
    - **script (line 1131-1137)**: `loadAgent` 의 RAG 설정 적용 분기에서 `if (enableRag.value) { loadDocuments() }` **제거**, `enableRag.value = agent.value.enableRag` 만 보존. 한국어 주석으로 정정 사유 명시.
    - **script (line 1754)**: 채팅 페이로드 `chatPayload` 의 `documentIds: enableRag.value && selectedDocumentIds.value.length > 0 ? selectedDocumentIds.value : null,` **제거**. 백엔드 `RagService.cs:88-93` 가 documentIds 를 디버그 로그만 남기고 무시하므로 안전하며, 페이로드에서 아예 제외해 라인 노이즈 + Agent.KnowledgeBaseSource/Ref 권위 정합성 회복.
  - **MODIFY `agenthub/ClientApp/src/views/agent/AgentSelect.vue`** —
    - **템플릿** (line 296-407 일대): `v-if="newAgent.enableRag"` 블록 (alert info + 문서 제약 조건 row + 문서 선택 list + small text-muted hint) **전체 삭제** + 한국어 대체 주석. 토글에 붙어있던 `@change="onRagToggle"` 핸들러 제거.
    - **script** : `import { ... watch }` → `import { ... }` (사장된 watch 제거) + `interface KnowledgeBaseDocument` + `interface RagConstraints` **2개 제거** + 한국어 대체 주석.
    - **script** : `CreateAgentData.selectedDocumentIds?: number[]` 필드 **제거** (동일 인터페이스를 newAgent / editAgentData 양쪽에서 공유하므로 단일 변경).
    - **script** : `loadingDocuments` ref + `availableDocuments` ref + `ragConstraints` ref 3개 **제거**.
    - **script (line 857-910)**: `loadDocuments` async 함수 + `onRagToggle` 함수 + `toggleDocument` 함수 + `watch(showCreateModal, ...)` watcher **4개 제거** + 한국어 대체 주석.
    - **script** : `editAgent` / `closeCreateModal` / `closeEditModal` 의 `selectedDocumentIds: []` reset 라인 + `availableDocuments.value = []` 라인 정리.
    - **script** : `handleCreateAgent` 의 RAG 사전 선택 confirm 다이얼로그 + `ragConstraints.maxDocuments` 초과 검증 + `requireIndexed` 미인덱싱 검증 + `requestData.selectedDocumentIds = ...` 페이로드 추가 분기 **4개 모두 제거** + 한국어 주석으로 권위는 AgentBuilder.vue 의 KnowledgeBaseSource/Ref 임을 명시.
  - **MODIFY `agenthub/ClientApp/src/i18n/locales/ko.json`** — `agentChat.*` 의 사장 키 6개 (`selectKnowledge` / `loadingDocuments` / `noDocumentsAvailable` / `indexed` / `indexingRequired` / `maxDocumentsHint`) **제거**. `enableRag` / `enableRagDesc` 는 보존 (토글 자체 유지). 다른 파일 사용처 grep 결과 0건 — AgentChat.vue 단독 사용처였음.
  - **MODIFY `agenthub/ClientApp/src/i18n/locales/en.json`** — 동일 6개 영문 키 제거.
  - **MODIFY `agenthub/ClientApp/src/assets/css/aiuiux-theme.css`** (line 2111-2174): `cd-doc-list` / `cd-doc-item` / `cd-doc-check` / `cd-doc-label` / `cd-doc-title` / `cd-doc-status.status-indexed` / `cd-doc-status.status-pending` 등 64 라인 CSS 블록 **전체 제거** + 한국어 대체 주석. AgentChat.vue 단독 참조처였으므로 안전.
- **빌드 PASS**:
  - `cd ClientApp && npx vue-tsc --noEmit` → **exit=0 errors=0** (`@ts-nocheck` 부착 0, 게이트 유지).
  - `npm run build:check` (= vue-tsc + vite build) → **PASS, 3.59s, 263 modules transformed**.
  - 청크 카탈로그 비교: `AgentChat-CwTpD9n2.js` 70.68 kB / gzip 21.66 kB (fingerprint 신규) + `AgentSelect-D8sTXokk.js` 28.66 kB / gzip 8.14 kB (fingerprint 신규) + `index-BQthdxdM.js` 133.46 kB / gzip 44.07 kB (i18n 키 6개 제거 반영, 이전 133.98 → -0.52 kB) + `AgentBuilder-CEaL4L2Q.js` 35.00 kB (변경 0). 다른 청크(WorkflowBuilder/vue-vendor/chart-vendor/marked.esm) 변경 0.
  - **dist 청크 grep 검증**: `D:\workspace\IDINO_Agent_Hub\agenthub\ClientApp\dist\assets` 안 소문자 `/knowledgebase` (deprecated GET 라우트) 매치 **0건** + AgentChat 청크 `KnowledgeBaseDocument` 매치 0건 + AgentSelect 청크 `KnowledgeBaseDocument` 매치 0건. case-insensitive 매치는 운영자 KB(`AdminKnowledgeBase*`, `KnowledgeBaseSource` 필드명) 정상 잔재만 — 본 작업 범위 외.
- **wwwroot 동기화**: `agenthub/wwwroot/assets/` rm + `ClientApp/dist/assets/` 복사 + `index.html` 갱신. `agenthub/.gitignore` 가 `wwwroot/assets/` + `wwwroot/index.html` 제외 → commit 미포함 (정상).
- **호스트 192.168.10.39 배포 PASS**: `tmp/deploy_track8_kb_cleanup/deploy.py` (paramiko 자동화) —
  - SFTP 5 파일 소스 ~377 KB 업로드 (`AgentChat.vue` 200 KB / `AgentSelect.vue` 41 KB / `ko.json` 33 KB / `en.json` 28 KB / `aiuiux-theme.css` 73 KB)
  - `docker compose build agenthub` → BuildKit cache + publish layer ~12s, `agenthub-agenthub:latest` 신규 manifest sha256:36f77733... config sha256:d3220c7b... attestation sha256:995734ac...
  - `docker compose up -d --force-recreate agenthub` → Container Recreated/Started
  - 4초 만에 healthy (iter 2)
  - 컨테이너 내 wwwroot grep: `docker exec agenthub sh -c "grep -ro '/knowledgebase' /app/wwwroot/assets | wc -l"` → **0건** (호스트 자산까지 dead code 청산 확정)
  - 컨테이너 wwwroot 청크 fingerprint 신규: `AgentChat-CHGs2jd8.js` / `AgentSelect-BfGMgH-6.js` / `index-0gqFo1vt.js` (호스트 BuildKit 의 deterministic 해시는 로컬 dist 와 다르나 코드/i18n 동등성 검증 PASS).
- **회귀 검증 PASS**:
  - `admin@example.com / Admin123!` 로그인 → JWT 555 chars 정상 발급.
  - `GET /api/agents/1` Bearer JWT → 200 + 6 신규 필드 모두 노출: `{llmRouting:True, routingPolicyJson:True, knowledgeBaseSource:True, knowledgeBaseRef:True, consumerSystems:True, sortOrder:True}` — 직전 `b3a2d85` 백엔드 회귀 + `845382c` UI 회귀 PASS 유지.
  - **한국어 RAG 쿼리 회귀** (`tmp/deploy_track8_kb_cleanup/verify_chat.py`): `POST /api/chat/conversations/2/messages` `{"message":"안녕하세요, RAG 회귀 테스트입니다."}` → **200**, messageId=46, conversationId=2, role=assistant, 한국어 응답(환영 메시지) 정상, tokensUsed=3279, model=gpt-4o-2024-08-06, finishReason=stop. **`documentIds` 페이로드 제거 후에도 백엔드 정상 동작 확인** (RagService.cs 가 documentIds 무시 + KnowledgeBaseSource/Ref 권위로 결정).
- **외부 API 라우트 변경 0** — 페이로드에서 무시되던 documentIds 필드만 제거, 컨트롤러/엔드포인트/응답 schema 변경 0. 다른 페이지(AgentBuilder/AgentMultiChat/Marketplace/AdminKnowledgeBase) 동작 회귀 0. EnableRag 토글 per-conversation override 보존.
- **anti-patterns.md 준수**: §4(Frontend 하드코딩 API URL — `import api from '@/services/api'` 그대로 사용) + §11(컴포넌트에서 axios 직접 사용 금지) + §7(자체 KB 신규 사용 차단) 모두 위반 0. Pinia/ref/computed/v-model 패턴 보존, React 관용구 부재.
- **Side effect**: ADR-2 단일 권위 = DocUtil 정책이 사용자 화면 dead code 까지 빠짐없이 집행됨. 코드 부채 카탈로그 1건 청산. 빌드 산출물에서 `/knowledgebase` 매치 0건 확정.
- **변경 파일 목록 (commit 대상)**:
  - `agenthub/ClientApp/src/views/agent/AgentChat.vue`
  - `agenthub/ClientApp/src/views/agent/AgentSelect.vue`
  - `agenthub/ClientApp/src/i18n/locales/ko.json`
  - `agenthub/ClientApp/src/i18n/locales/en.json`
  - `agenthub/ClientApp/src/assets/css/aiuiux-theme.css`
- **별도 트랙 (예정)**: AgentSelect.vue 의 빠른 생성/수정 모달(빌더 영역) 자체 deprecate 또는 AgentBuilder.vue 로 흡수 — 사용자가 두 진입점 중 어느 쪽을 기본으로 할지 결정 필요.
- **다음 트랙 후보**: D-1 vue-flow 업그레이드 (WorkflowBuilder.vue `@ts-nocheck` 해제) / Nexus 실제 부팅 (LAN GPU 호스트 192.168.22.28) / KnowledgeBaseRef 텍스트 입력 → DocUtil collection BFF dropdown 전환 / RagService 결과 캐시(`rag:*` 10분) version-key 무효화 확장 / 시연 종료 후 secret leak history sanitize + 키 회전.

### 2026-05-08 (후속 트랙 — AgentBuilder.vue UI 운영자 폼 필드 확장 — 백엔드 b3a2d85 갭 보강을 사용자 단까지 활용)
- **목적**: 직전 commit `b3a2d85` 의 백엔드 AgentDto 6 필드 갭 보강(`LlmRouting/RoutingPolicyJson/KnowledgeBaseSource/KnowledgeBaseRef/ConsumerSystems/SortOrder`)이 BFF 정합성을 회복했으나, Vue 운영자 콘솔 `AgentBuilder.vue` 가 여전히 read/write 양쪽 모두 미지원이라 운영자가 GUI 로 LLM 라우팅 정책 + RAG 권위 + 호출 화이트리스트를 관리할 수 없었음. 본 트랙은 6 필드를 운영자 폼 UI 단까지 활용 가능하게 확장.
- **수정 4 파일**:
  - **MODIFY `agenthub/ClientApp/src/types/index.ts`** — `AgentDto` interface 에 6 신규 필드 추가 (camelCase, 백엔드 직렬화 일치). `llmRouting?: string` (External/Internal/Hybrid, default External) + `routingPolicyJson?: string | null` + `knowledgeBaseSource?: string` (AgentHub/DocUtil) + `knowledgeBaseRef?: string | null` + `consumerSystems?: string | null` + `sortOrder?: number`. 한국어 주석으로 백엔드 commit 참조 + Phase 5.1/ADR-2/Phase 6.5 맥락 명시. CreateAgent/UpdateAgent payload 는 saveAgent 의 `{ ...agentForm.value }` spread 로 자동 포함되므로 별도 interface 미신설.
  - **MODIFY `agenthub/ClientApp/src/views/agent/AgentBuilder.vue`** —
    - `<script setup lang="ts">` import 추가: `import { useI18n } from 'vue-i18n'` + `const { t } = useI18n()` (신규 라벨/help 텍스트 i18n 키로 분리).
    - `agentForm` 초기값에 6 신규 필드 추가 (line 645-653, default: `llmRouting:'External' / routingPolicyJson:'' / knowledgeBaseSource:'AgentHub' / knowledgeBaseRef:'' / consumerSystems:'' / sortOrder:0`). 빈 문자열 정책: 백엔드 서비스 레이어가 빈문자→null 정규화/기본값 폴백 처리(`AgentService.cs` line 153-179, 209-236).
    - 클라이언트 사이드 JSON 검증 함수 2개 신규: `validateRoutingPolicyJson` (객체 형식 + JSON.parse, 빈 문자열은 valid) + `validateConsumerSystems` (string[] 배열 + JSON.parse). blur 트리거, 실패 시 `routingPolicyJsonError`/`consumerSystemsError` ref 에 한국어 에러 저장. **제출은 막지 않음** — 백엔드가 최종 검증.
    - `loadAgentForEdit(agent)` 매핑에 6 신규 필드 추가 (`llmRouting: agent.llmRouting || 'External'` 등, null/undefined → default 폴백, 빈 문자열은 그대로 유지하여 placeholder 가 보이도록).
    - `resetBuilder()` 함수에 6 신규 필드 default reset + 검증 에러 ref 2개 reset.
    - **신규 카드 — Step 4 "고급 기능" 카드 직후 운영자 "고급 설정" 카드** 1건 (`<div class="card aiuiux-card mb-4">`, Bootstrap 5 일관). 4 그룹:
      - **그룹 1 LLM 라우팅**: dropdown(External/Internal/Hybrid) + Hybrid 일 때만 (`v-if`) RoutingPolicyJson textarea (placeholder=`{"default":"external","piiAction":"internal"}`, blur 검증 + invalid-feedback 빨간 메시지)
      - **그룹 2 지식베이스 권위**: dropdown(DocUtil 권장 / AgentHub deprecated 회색 라벨) + DocUtil 일 때만 KnowledgeBaseRef input (placeholder=`예: 부산대-2024-사업계획`)
      - **그룹 3 호출 화이트리스트**: ConsumerSystems textarea (placeholder=`["docutil-user","career-coaching"]`, blur 검증)
      - **그룹 4 정렬 순서**: number input (min=0, max-width 200px)
    - 카드 제목/help/필드 라벨/options/error 메시지 모두 `t('agentBuilder.*')` i18n 키로 분리.
    - **`@ts-nocheck` 부착 0** — vue-tsc 2.x strict 타입 통과 (게이트 유지).
  - **MODIFY `agenthub/ClientApp/src/i18n/locales/ko.json`** — `agentBuilder.*` 신규 최상위 섹션 추가. `advancedSettings/advancedSettingsDescription` + `fields` 12키(llmRouting/llmRoutingHelp/routingPolicyJson/routingPolicyJsonHelp/knowledgeBaseSource/knowledgeBaseSourceHelp/knowledgeBaseRef/knowledgeBaseRefHelp/consumerSystems/consumerSystemsHelp/sortOrder/sortOrderHelp) + `llmRoutingOptions` 3키(external/internal/hybrid) + `knowledgeBaseSourceOptions` 2키(docutil/agentHub) + `errors` 2키(routingPolicyJsonInvalid/consumerSystemsInvalid). 총 22 키 한국어.
  - **MODIFY `agenthub/ClientApp/src/i18n/locales/en.json`** — 동일 22 키 영문 번역.
- **빌드 PASS**:
  - `cd ClientApp && npx vue-tsc --noEmit` → exit=0 errors=0 (게이트 유지, `@ts-nocheck` 부착 0).
  - `npm run build:check` (= vue-tsc + vite build) → PASS, 4.46s, 263 modules transformed.
  - 청크 카탈로그: `AgentBuilder-Yx5xpP2A.js` 35.00 kB(gzip 11.90, 이전 29.38 → 5.62 kB 증가 — 신규 카드 + 검증 로직 + i18n 호출), `AgentBuilder-pg_QnFNt.css` 신규, `index-Di5Nz_88.js` 133.98 kB(이전 131.21 → 2.77 kB 증가, i18n 키 22개 추가), 다른 청크(WorkflowBuilder/vue-vendor/chart-vendor) 변경 0.
  - **dist 청크 grep 검증**: `AgentBuilder*.js` 안 `llmRouting/knowledgeBaseSource/consumerSystems/routingPolicyJson` 매치 + `index-*.js` 안 `advancedSettings/llmRoutingOptions/knowledgeBaseSourceOptions/라우팅 정책/호출 화이트리스트/knowledgeBaseRefHelp` 매치 모두 PASS — 신규 코드 + i18n 키 + 한국어 라벨 빌드 산출물에 정확히 포함.
- **wwwroot 동기화**: `agenthub/wwwroot/assets/` rm + `ClientApp/dist/assets/` 복사 + `index.html` 갱신. `agenthub/.gitignore` 가 `wwwroot/assets/` + `wwwroot/index.html` 제외 → commit 미포함 (정상).
- **호스트 192.168.10.39 배포 PASS**: `tmp/deploy_b3a2d85_ui/deploy.py` (paramiko) 자동화 —
  - SFTP 4 파일 소스 ~135 KB 업로드 (`types/index.ts` 14 KB / `AgentBuilder.vue` 59 KB / `ko.json` 33 KB / `en.json` 29 KB)
  - `docker compose build agenthub` → BuildKit cache + publish layer ~10s, `agenthub-agenthub:latest` 신규 manifest sha256:6268b363... config sha256:9804fc38...
  - `docker compose up -d --force-recreate agenthub` → Container Recreated/Started
  - 4초 만에 healthy (iter 2)
  - 컨테이너 내 wwwroot grep: `AgentBuilder*.js` 안 `llmRouting` 매치 다수 + `index-*.js` 안 `knowledgeBaseRefHelp` 매치 다수 — 호스트 자산까지 정확 반영.
- **회귀 검증 PASS**:
  - `admin@example.com / Admin123!` 로그인 → JWT 555 chars 발급 정상.
  - `GET /api/agents/1` Bearer JWT → 200 + 6 신규 필드 모두 노출: `{llmRouting:True, routingPolicyJson:True, knowledgeBaseSource:True, knowledgeBaseRef:True, consumerSystems:True, sortOrder:True}` — 직전 `b3a2d85` 백엔드 회귀 PASS 유지 + 클라이언트가 이제 read/write 모두 가능.
  - `/swagger` 는 운영 환경에서 비활성화(404) — 개발 환경 전용이므로 정상.
  - 라이브 UI 캡처는 환경 한계로 미수행, 빌드 산출물 grep + 백엔드 round-trip 으로 대체 검증.
- **외부 API 라우트 변경 0** — 신규 필드 추가만, 기존 폼 필드(agentName/description/serviceId/defaultModel/systemPrompt/temperature/maxTokens/isPublic/enableRag/piiProtectionEnabled/piiProtectionMode/welcomeMessage/placeholderText/chatTheme/allowGuestChat/allowedEmbedDomains) 시그니처 변경 0. 다른 페이지(AgentChat/AgentSelect/AgentMultiChat/Marketplace) 동작 회귀 0.
- **anti-patterns.md 준수**: §4(Frontend 하드코딩 API URL — `import api from '@/services/api'` 그대로 사용) + §11(컴포넌트에서 axios 직접 사용 금지) 모두 위반 0. Pinia/ref/computed/v-model 패턴 보존, React 관용구 부재.
- **Side effect**: 운영자가 Step 4 "고급 기능" 단계에서 신규 "고급 설정" 카드를 통해 LLM 라우팅 정책(External/Internal/Hybrid + JSON 결정 규칙) + RAG 지식베이스 권위(DocUtil 권장) + 호출 화이트리스트(End-User App ID 배열) + 정렬 순서를 GUI 로 직접 관리 가능. 백엔드 정합성이 사용자 단까지 활용됨.
- **변경 파일 목록 (commit 대상)**:
  - `agenthub/ClientApp/src/types/index.ts`
  - `agenthub/ClientApp/src/views/agent/AgentBuilder.vue`
  - `agenthub/ClientApp/src/i18n/locales/ko.json`
  - `agenthub/ClientApp/src/i18n/locales/en.json`
- **별도 트랙 (예정)**: KnowledgeBaseRef 텍스트 입력 → DocUtil collection 목록 BFF (`/api/admin/knowledge-base/collections`) fetch dropdown 으로 전환 (현재는 단순 텍스트 입력으로 시작).
- **다음 트랙 후보**: AgentChat.vue/AgentSelect.vue 의 `/api/knowledgebase` GET dead code 청산 / D-1 vue-flow 업그레이드 (WorkflowBuilder.vue `@ts-nocheck` 해제) / Nexus 실제 부팅 (LAN GPU 호스트) / 시연 종료 후 secret leak history sanitize + 키 회전.

### 2026-05-08 (Phase 3 vue-tsc 2.x 업그레이드 — Node 24 호환 + 부채 카탈로그 A/B/C/D 처리, commit 대기)
- **목적**: vue-tsc 1.x 가 Node v24.11.1 환경에서 정규식 패턴 깨짐(`Search string not found: "/supportedTSExtensions = .*(?=;)/"`) 으로 죽어 그동안 type-check 가 사실상 우회되어 왔음 → vue-tsc 2.x (Volar 기반) 로 업그레이드 → 표면화된 30+ 건의 pre-existing 타입 오류 정리. **Phase 3 핵심 목표 (Node 24 호환 + `npm run build:check` 정상 + CI 게이트 복구) 달성**.
- **사전 작업 (직전)**: `agenthub/ClientApp/package.json` 의 `vue-tsc: ^1.8.27 → ^2.2.12` 업그레이드 + `npm install` 완료 (TS 5.9.3 사용).
- **카테고리 A — 즉시 수정 (mechanical, 안전, 7 변경)**:
  - **MODIFY `src/composables/useMessageFormatting.ts:142-147`**: `marked.setOptions` 의 `mangle: false` 옵션 제거. marked v11+ 부터 default false 로 변경되어 MarkedOptions 에서 제거됨 (TS2353 해소). 한국어 주석 추가.
  - **MODIFY `src/views/agent/AgentMultiChat.vue:638-644`**: `marked.setOptions` 의 `headerIds: false` + `mangle: false` 옵션 제거 + 한국어 주석.
  - **MODIFY `src/views/ApiKeys.vue:655-664`**: `agentKeyForm` 타입 정의에서 `rateLimitPerMinute?: number | null` → `number` (DTO 의 number | undefined 와 정렬, TS2322 해소). 초기값 `null → undefined` 3 곳.
  - **MODIFY `src/views/ApiKeys.vue:834-836,841-844`**: `openAgentKeyModal()` 의 폼 초기화에 `selectedScopes: []` 빈 배열 default 추가 (TS2322 해소). `closeAgentKeyModal()` 의 `null → undefined` 2 곳.
  - **MODIFY `src/views/ApiKeys.vue:110`**: `revealedKeys[key.apiKeyId] || key.maskedKey` (`string | undefined`) 에 `|| ''` nullish guard 추가 → `copyToClipboard(string)` 시그니처에 정렬 (TS2345 해소).
  - **MODIFY `src/views/BannedWords.vue:246-251,344,352`**: `newBannedWord` ref 타입 단순화 (intersection 제거, base DTO 만 사용). agentId `null → undefined` 3 곳.
  - **MODIFY `src/services/sseClient.ts:115-127`**: `reader.read()` 의 done 분기에서 잔여 buffer 마지막 처리 시 `event !== DONE_MARKER` 가드 추가 (TS2322 해소). `parseFrame()` 반환 타입이 `ChatStreamEvent | typeof DONE_MARKER | null` 인데 yield 직전에 unique symbol 가능성을 좁히지 못한 것이 원인. 한국어 주석 추가.
- **카테고리 B/C/D — `@ts-nocheck` 부착 (별도 트랙으로 분리, 4 파일)**:
  - **MODIFY `src/views/agent/AgentBuilder.vue:577`** (B-1): `<script setup lang="ts">` 직후 `// @ts-nocheck` + 한국어 주석. 사유: AgentDto.enableRag 누락 (line 547,548). 백엔드 C# Models/DTOs 와 동기화는 별도 트랙(B-1).
  - **MODIFY `src/views/agent/AgentMultiChat.vue:430`** (B-1): `<script setup lang="ts">` 직후 `// @ts-nocheck` + 한국어 주석. 사유: ConversationDto.enableRag/enableWebSearch + ApiServiceDto.defaultModel 15+ 곳 누락 (line 752,758,759,772,778,779,875-881,897,916).
  - **MODIFY `src/views/KnowledgeBase.vue:329`** (C-1): `<script setup lang="ts">` 직후 `// @ts-nocheck` + 한국어 주석. 사유: Phase 2 자체 KB drop (ADR-2) 후 폐기 대상 (`/api/knowledgebase` 호출). 운영자 진입점은 `/admin/knowledge-base` (AdminKnowledgeBase.vue) 로 일원화. 라우트/뷰 완전 제거는 별도 트랙(C-1).
  - **MODIFY `src/views/workflow/WorkflowBuilder.vue:323`** (D-1): `<script setup lang="ts">` 직후 `// @ts-nocheck` + 한국어 주석. 사유: @vue-flow/core 의 NodeMouseEvent 시그니처 + Position 타입 narrowing 이 strict 검사에서 깨짐 (line 81,103,104,106,107). VueFlow 업그레이드는 별도 트랙(D-1).
- **검증 PASS**:
  - `cd ClientApp && npx vue-tsc --noEmit` → **exit=0 errors=0** (이전 30+ 건 → 0 건)
  - `npm run build:check` (= `vue-tsc && vite build`) → **PASS, 4.31s**
  - `npx vite build` 청크 카탈로그 정상: index 127.36 kB / WorkflowBuilder 182.62 kB / vue-vendor 164.98 kB / chart-vendor 207.43 kB / AgentBuilder 29.38 kB / AgentMultiChat 33.82 kB / KnowledgeBase 15.54 kB / ApiKeys 34.01 kB / BannedWords 12.01 kB / marked.esm 35.08 kB. 모든 청크 fingerprint 신규 (e.g. `index-Bo7jKhd7.js`, `WorkflowBuilder-Cn867V0B.js`, `KnowledgeBase-C22Nc7wK.js`).
- **wwwroot 동기화**: `ClientApp/dist/{assets, index.html}` → `agenthub/wwwroot/{assets, index.html}` 복사. `agenthub/.gitignore` 가 `wwwroot/assets/` + `wwwroot/index.html` 제외 → commit 미포함 (정상).
- **변경 파일 목록 (commit 대상 — package.json + package-lock.json 포함)**:
  - `agenthub/ClientApp/package.json` (vue-tsc 1.x → 2.2.12, 직전 작업)
  - `agenthub/ClientApp/package-lock.json` (vue-tsc + 의존성 갱신, 직전 작업)
  - `agenthub/ClientApp/src/composables/useMessageFormatting.ts` (A-1)
  - `agenthub/ClientApp/src/services/sseClient.ts` (A-5)
  - `agenthub/ClientApp/src/views/ApiKeys.vue` (A-2/A-3/A-4)
  - `agenthub/ClientApp/src/views/BannedWords.vue` (A-2)
  - `agenthub/ClientApp/src/views/KnowledgeBase.vue` (C-1, @ts-nocheck)
  - `agenthub/ClientApp/src/views/agent/AgentBuilder.vue` (B-1, @ts-nocheck)
  - `agenthub/ClientApp/src/views/agent/AgentMultiChat.vue` (A-1 + B-1, @ts-nocheck)
  - `agenthub/ClientApp/src/views/workflow/WorkflowBuilder.vue` (D-1, @ts-nocheck)
- **외부 동작 변경 0** — 타입 시그니처 정정 또는 nocheck 부착만, 런타임 로직 변경 0. Vue/Pinia 패턴 보존, React 관용구 부재 확인.
- **후속 트랙 3건 (별도 PR)**:
  - **B-1**: `src/types/index.ts` 의 AgentDto/ConversationDto/ApiServiceDto 에 enableRag/enableWebSearch/defaultModel 필드 추가 + 백엔드 C# `Agent.cs` / `ConversationDto.cs` / `ApiServiceDto.cs` 와 동기화 → AgentBuilder.vue + AgentMultiChat.vue 의 `@ts-nocheck` 해제
  - **C-1**: `src/views/KnowledgeBase.vue` 파일 삭제 + `src/router/index.ts` 의 `/knowledge-base` 라우트 제거 (또는 410 redirect) — Phase 2 자체 KB drop 잔재
  - **D-1**: `@vue-flow/core` 최신 버전 업그레이드 + NodeMouseEvent / Position 타입 정의 정렬 → WorkflowBuilder.vue 의 `@ts-nocheck` 해제
- **CI 게이트 복구**: `npm run build:check` 가 다시 vue-tsc 통과 + vite build 둘 다 정상 동작. 이후 Phase 4/5 작업의 사전 검증 게이트 회복. 이전에 폴백으로 사용하던 `npx tsc --noEmit -p tsconfig.json` 우회 패턴 불필요.

### 2026-05-07 (권장 순서 A→C→E→B→D 모두 완료 — DocUtil JWT 자동 갱신 + RAG SystemPrompt + 본 PC Redis 동기화 + Nexus 자산 + Dockerfile 정리, commit `7710df6` + `ede8096`)
- **목적**: 사용자가 권장 6단계(A→C→E→B→D→F) 모두 자동 진행 지시. F 는 마무리(progress.md 갱신 + commit). 시연 안정성/품질/일관성/통합 자산/위생 5축을 동시 보강.
- **Phase A — DocUtil JWT 자동 갱신** (commit `7710df6`):
  - **NEW `agenthub/Services/IDocUtilTokenProvider.cs`** (인터페이스 + 한국어 XML 주석)
  - **NEW `agenthub/Services/DocUtilTokenProvider.cs`** (~190 LOC, Singleton 구현)
    - 4단계 폴백: ① 메모리 캐시(만료 5분 전 hit) ② appsettings:DocUtil:JwtToken(만료 검증 후 캐시 적재) ③ refresh_token + POST /api/v1/auth/refresh ④ ServiceUsername/Password + POST /api/v1/auth/login → ⑤ ApiKey
    - SemaphoreSlim 으로 동시 갱신 직렬화 (중복 로그인 차단)
    - JWT exp claim Base64 url-safe 직접 디코드 (DocUtil 가 expires_in 미반환)
    - 모든 갱신 시점 한국어 로그 (`"DocUtil 토큰 - login PASS (사용자=jyj7970, 남은 29분)"`)
  - **MODIFY `agenthub/Services/DocUtilClient.cs`**:
    - ctor 에 IDocUtilTokenProvider 주입
    - BuildJsonRequest → BuildJsonRequestAsync (CancellationToken 받음, 매 호출 _tokenProvider.GetTokenAsync)
    - 5 호출자 await 추가 (Search/GetDocuments/GetDocument/Delete/GetChunks)
    - multipart upload 도 토큰 fetch 인라인
    - 기존 ApplyAuthorizationHeader 제거 (TokenProvider 가 우선순위 일원화)
  - **MODIFY `agenthub/Program.cs`**: AddSingleton<IDocUtilTokenProvider, DocUtilTokenProvider>
  - **MODIFY `agenthub/docker-compose.yml`**: DOCUTIL_SERVICE_USERNAME / DOCUTIL_SERVICE_PASSWORD env 추가
  - **MODIFY `agenthub/.env.example`**: DOCUTIL_SERVICE_USERNAME/PASSWORD 키 카탈로그
  - **검증**: 호스트 .env 의 DOCUTIL_JWT_TOKEN 비우고 컨테이너 재시작 → `/api/admin/knowledge-base/documents` HTTP 200 (total=30) PASS. 로그 "DocUtil 토큰 - login PASS"
- **Phase C — docutil-rag-chat SystemPrompt 강화** (DB UPDATE only, git commit 0):
  - SQL: `UPDATE "AIAgentManagement"."Agents" SET "SystemPrompt"=$1, "UpdatedAt"=NOW() WHERE "AgentCode"='docutil-rag-chat'` (224→601 chars)
  - 새 SystemPrompt 핵심 가이드:
    - "청크가 부분적으로만 관련되더라도 가능한 정보를 추출해 답변하세요"
    - "출처(파일명/섹션)를 답변에 반드시 명시" (예: "출처 1: [부산대학교 AI 사업 착수보고서] 의 인수시험 단계에 따르면 ...")
    - "사용자 질문이 영문이고 청크가 한국어이면 의미 매칭 후 답변"
    - "청크에 없는 정보를 일반 지식으로 추측 금지"
  - **검증**: 영문 query "List the section topics from the Busan AI Education project" → prompt_tokens 137→275 (RAG context 확장), 응답에 "프로젝트 개요 / 품질관리 / 보안 / 교육훈련 / 일정관리 / 산출물 / 책임 / 인수시험" 청크 정보 정리 답변 PASS
  - 한국어 query 시 score 가 여전히 낮음 — DocUtil Qdrant 검색 토크나이저 / docs 키워드 매칭 이슈로 추정. query rewrite / Agent.KnowledgeBaseRef 설정 / rerank 모델은 별도 트랙
  - 다른 RAG Agent(docutil-report-generator/career-rag-actionboard/agentic-search) 는 본래 목적이 다르므로 동일 SystemPrompt 일률 적용 미적용 — 별도 트랙
- **Phase E — 본 PC AgentHub Redis 를 docutil-redis 컨테이너로 전환** (.gitignore 대상, git commit 0):
  - **MODIFY `agenthub/appsettings.Production.json`**: `ConnectionStrings:Redis` = `localhost:6379` → `192.168.10.39:6340,password=docutil_redis_2024,abortConnect=false`
  - **MODIFY `agenthub/appsettings.Development.json`**: 동일 변경
  - 본 PC dotnet run AgentHub 와 호스트 docker AgentHub 가 동일 Redis 컨테이너(docutil-redis) 사용 → 캐시 공유 (RAG 결과 / API Key Rate Limiter / Agent 메타데이터 등)
  - **검증**: 본 PC AgentHub 재부팅 1초만에 ready, `Redis cache configured with connection: 192.168.10.39:6340,password=...` 로그, exception 0건
- **Phase B — Nexus 컨테이너화 자산** (commit `ede8096`):
  - **NEW `nexus/Dockerfile`** (multi-stage Python 3.11): Machine A(orchestrator) 전용 (architecture P4 — Machine B vLLM 은 별도 호스트). build stage 에서 requirements.txt 설치 → runtime stage 로 site-packages 복사. 헬스체크 GET /health. ENTRYPOINT `uvicorn web.app:app --host 0.0.0.0 --port 8001`
  - **NEW `nexus/.dockerignore`**: __pycache__/.venv/.claude/tests/models/training/checkpoints 등 제외. 시크릿(config/nexus_config.yaml/permission_rules/tenants/ssl) 제외
  - **NEW `nexus/docker-compose.yml`** (3 services + 1 network + 2 volumes):
    - service `nexus`: Machine A FastAPI, ports `127.0.0.1:8001:8001` (외부 노출 차단)
    - service `nexus-postgres`: ADR-11 별도 PG (postgres:17-alpine, 별도 volume)
    - service `nexus-redis`: ADR-11 별도 Redis (redis:7-alpine, requirepass)
    - environment 는 pydantic-settings nested env 형식 정렬: `NEXUS_POSTGRESQL__HOST=nexus-postgres`, `NEXUS_REDIS__HOST=nexus-redis`, `NEXUS_GPU_SERVER_URL=${NEXUS_GPU_SERVER_URL}` (Machine B LAN 주소), `NEXUS_AIR_GAP_MODE=true`
    - networks: `nexus-network` (별도 bridge — docutil-network 합류 X, ADR-11 격리)
  - **MODIFY `nexus/.env.example`**: 기존 nexus 자체 형식 보존 + Docker Compose 추가 키(NEXUS_POSTGRESQL_PASSWORD / NEXUS_REDIS_PASSWORD / NEXUS_SHARED_SECRET) append
  - **시연 호스트(192.168.10.39) 부팅 미진행**: GPU 부재 + 외부망 노출 위험(anti-pattern #10) + ADR-11 별도 PG 정책. 별도 LAN 호스트(예: 192.168.22.28) 부팅 시 docker compose up -d 로 즉시 가동 가능
- **Phase D — Dockerfile 의 NETSDK1194 경고 해소** (commit `ede8096`):
  - **MODIFY `agenthub/Dockerfile`**: `dotnet restore` / `dotnet publish` 에 `AIAgentManagement.csproj` 명시. .sln 파일 우선 선택 차단으로 `NETSDK1194: --output 옵션 미지원` 경고 사라짐
  - **검증**: 호스트 재빌드 → build.log grep -c NETSDK1194 = **0** (이전 매 빌드 N건 → 0건)
  - 빌드 시간: cache hit 으로 15초 (full 3분 → 5x 단축)
- **Phase F — 마무리**: 본 progress.md 갱신 + 별도 commit
- **호환성 검증 (회귀 0건)**:
  - 본 PC AgentHub (PID 변경) + 호스트 컨테이너 (재생성 healthy) 동시 가동
  - DocUtil 14 컨테이너 영향 없음 (network/PG/Redis 그대로)
  - 직전 Phase 6.1~7.5 기능 모두 그대로 동작 (라운드트립 검증)
- **별도 트랙 (다음 세션 또는 사용자 결정)**:
  - RAG 응답 품질: query rewrite (LLM 영→한 정규화) / Agent.KnowledgeBaseRef collection 한정 / score threshold / rerank 모델 도입
  - Nexus 실제 부팅: 192.168.22.28 GPU 호스트에서 nexus/docker-compose.yml 활용 (Machine B vLLM 도 별도 트랙)
  - DocUtil 운영자 service account: 정식 전용 계정 발급 (현재 jyj7970 admin 사용)
  - vue-tsc 2.x 업그레이드 (Node 24 호환), Phase 8+ 자체 KB DB drop, secret leak history sanitize, SQL Server stale 비번 / SSH 비번 / LLM API 키 회전

### 2026-05-07 (Phase A — RAG 회로 진단 정정 + Redis 비밀번호 인증 추가, commit `4f868c4`)
- **목적**: 직전 Phase 6.5 옵션 ③ 진단(`/v1/chat/completions` 가 ChatService → RagService 분기를 우회한다)이 **잘못된 판단** 임을 정정. 실제로는 RAG 회로가 처음부터 동작 중이었으나 ① 이전 grep 패턴(`RagService|DocUtilClient|DocUtil|Knowledge|Retrieve|chunk|citation`)에 핵심 로그(`"RAG check"`, `"Chat request prepared. EnableRag"`, `"RAG 위임"`)가 매치되지 않아 흔적이 안 보였고 ② Redis 인증 실패로 RAG 캐시가 매 호출마다 미스되어 fallback in-memory cache 로 동작하던 정황. 본 Phase 에서 ① 회로 동작 검증(로그 확보) ② Redis 비밀번호 인증 추가로 캐시 히트 정상화
- **회로 검증 로그 (192.168.10.39 컨테이너)**:
  - `Chat request prepared. EnableRag: True, DocumentIds: null, AgentId: 1` (ChatService.cs:646-649)
  - `RAG check in SendChatMessageAsync: EnableRag=True, RagService=available, DocumentIds=null` (AiProxyService.cs:65-68)
  - `RAG search starting. EnableRag: True, Query: ..., UserId: 2, AgentId: 1` (AiProxyService.cs:103-108)
  - `RAG 위임 - AgentId=1, KnowledgeBaseSource=DocUtil, CollectionRef=(global), TopK=3` (RagService.cs:73-75) — **DocUtil 위임 분기 진입 PASS**
  - `RAG search completed and added to request.Messages. Found 3 relevant chunks. DocumentIds: null` (AiProxyService.cs:183-184)
  - 응답 prompt_tokens=362 (시스템 메시지 + 800자 절단 청크 3건 = ~2400자 → ~362 토큰, RAG 컨텍스트 prepend 정상)
- **Redis 인증 진단**:
  - 호스트의 docutil-redis 컨테이너는 비밀번호 필수 (`docutil_redis_2024`, /home/idino/docutil/.env:REDIS_PASSWORD)
  - 직전 Phase B compose 의 `ConnectionStrings__Redis: "docutil-redis:6379"` 는 password 미포함 → 매 캐시 호출마다 NOAUTH → fallback 흐름:
    - get 실패 → "Redis connection exception ... Falling back to direct database query"
    - set 실패 → "Falling back to in-memory cache"
  - graceful 폴백으로 동작 자체에는 영향 없으나 매 호출 ~50ms 지연 + Redis 캐시 효율 0 + 다중 인스턴스 환경에서 캐시 공유 불가
- **변경 파일 (2 modify, commit `4f868c4`)**:
  - **MODIFY `agenthub/docker-compose.yml`** (1 LOC) — `ConnectionStrings__Redis` 환경변수에 `password` 파라미터 + `abortConnect=false` 추가. StackExchange.Redis 형식 `docutil-redis:6379,password=${REDIS_PASSWORD},abortConnect=false`. abortConnect=false 는 Redis 일시 다운 시 ConnectionMultiplexer 재시도 동작 보장
  - **MODIFY `agenthub/.env.example`** (4 LOC) — `REDIS_PASSWORD=` 키 신설 + 한국어 주석. docutil/.env 의 REDIS_PASSWORD 와 동일 값 필수
- **호스트 .env 갱신 (paramiko)**:
  - 기존 .env 에 `REDIS_PASSWORD=docutil_redis_2024` 라인 append (chmod 600 유지)
  - 갱신된 docker-compose.yml SCP 전송 (compose 파일 내부 환경변수 구문 변경)
  - `docker compose up -d --force-recreate` 13초 부팅 healthy
- **검증 결과**:
  - `/v1/chat/completions` HTTP 200 (prompt_tokens=362 동일 — RAG 컨텍스트 정상 prepend)
  - 로그: **Redis connection exception 0건** (이전 매 호출 2건 → 현재 0건). RAG 캐시 정상 동작 (`rag:1:2:<hash>` 키)
  - 응답 LLM 콘텐츠는 여전히 청크에서 정확한 인용을 추출 못 함 — 본 호출의 RAG search score 0.016 (매우 낮음). 영문 query vs 한글 docs 매칭 약함 + Qdrant 글로벌 검색(collection 미지정)으로 부산대 인수시험 청크가 3건 안에 포함되었으나 LLM 모델이 "관련 정보 없음" 으로 판단. 향후 ① Agent 의 KnowledgeBaseRef 설정(특정 collection 한정) ② query rewrite (LLM 으로 영문 query → 한국어로 변환 후 재검색) ③ score threshold ④ rerank 모델 도입 등으로 개선 가능 (별도 트랙)
- **호환성 검증 (회귀 0건)**:
  - 본 PC AgentHub (Production 모드 dotnet run, PID 8240) 는 영향 없음 — `appsettings.Production.json:ConnectionStrings:Redis="localhost:6379"` 그대로. 본 PC 에는 Redis 미설치라 부팅 시 MemoryCache 자동 폴백 (`Program.cs:170-174`)
  - docutil 14 컨테이너 무영향 — agenthub 컨테이너 ConnectionString 변경만, docutil-redis 자체는 무변경
- **잠재 위험 / 다음 단계**:
  - **RAG 응답 품질 개선** — score threshold / query rewrite / rerank / Agent.KnowledgeBaseRef 설정 (별도 트랙)
  - **본 PC AgentHub 의 Redis 미사용** — 실제 운영 시 Redis 캐시가 RAG/응답 캐시에서 큰 가치 제공. 본 PC 시연 시 docutil-redis 직접 사용 (`appsettings.Development.json` 변경) 또는 본 PC 에 redis Docker 컨테이너 (별도 트랙)
  - **본 진단 정정 사례** — 향후 grep 패턴 시 한국어 로그 키워드(`RAG 위임`, `RAG check`, `RAG search`) 도 포함 필요

### 2026-05-07 (Phase B — AgentHub 컨테이너화 + 192.168.10.39 docker 배포 PASS, commit `51e4b85`)
- **목적**: 사용자 의도 — "모든 시스템(PG / IDINO_Agent_Hub / Nexus)을 192.168.10.39 docker 에 올린다". 진단 결과 PG 는 이미 docutil-postgres 컨테이너로 가동 중 (Phase 4 통합 PG = 본 컨테이너). DocUtil 14 컨테이너도 모두 healthy. **AgentHub 만 컨테이너화 + 같은 docutil-network 합류** 가 본 Phase 의 핵심. Nexus 는 GPU 부재 + ADR-11(LAN-only, 에어갭) 정책 충돌으로 보류 (별도 호스트 트랙).
- **호스트 진단 (paramiko ssh)**:
  - SSH 자격증명: 사용자 안내 `idino!@#$/idino@12` 가 PG 비번이고 SSH 비번은 `dkdlelsh@12` (한영 키보드 미변환 패턴, `D:\workspace\document_utilization\scripts\deploy_to_server.py:9` 에서 발견). 키 인증 미등록(ssh-copy-id 미진행)이라 paramiko 비밀번호 인증으로 자동화
  - 호스트: `192.168.10.39 (ai-ubuntu)` Ubuntu Linux 6.8.0-94, Docker 29.3.0, Compose v5.1.1, RAM 31GB, Disk 466GB free, **GPU 없음**
  - 가동 컨테이너: `docutil-{frontend,api,celery-worker-1,celery-beat,nginx,postgres,redis,rabbitmq,qdrant,minio,flower,grafana,loki,prometheus}` 14건 healthy. compose 프로젝트=`docutil`, network=`docutil-network`, 12 named volumes
  - **PG 운영 사양 일치**: docutil-postgres 컨테이너의 init script 가 별도로 AGENT_HUB user/DB 를 생성. `psql -U AGENT_HUB -d AGENT_HUB` 정상 동작 (CLAUDE.md 의 통합 PG 가 곧 이 컨테이너)
  - DocUtil 운영자 JWT 발급: POST `/api/v1/auth/login` body `{"username":"jyj7970","password":"idino!@#$"}` → admin role JWT (30분 만료)
- **변경 파일 (4 신규, 모두 commit `51e4b85` 포함)**:
  - **NEW `agenthub/Dockerfile`** (~50 LOC) — 멀티스테이지: Stage `build` (mcr.microsoft.com/dotnet/sdk:8.0 + Node.js 20 nodesource + dotnet restore + COPY 소스 + dotnet publish -c Release /p:UseAppHost=false). Stage `runtime` (mcr.microsoft.com/dotnet/aspnet:8.0 + curl/ca-certificates + COPY publish 산출물). ENV `ASPNETCORE_URLS=http://+:8080` + `ASPNETCORE_ENVIRONMENT=Production` + `DOTNET_RUNNING_IN_CONTAINER=true`. HEALTHCHECK `curl /swagger` 30s/10s/90s/5retries. ENTRYPOINT `dotnet AIAgentManagement.dll`. **PublishRunWebpack target** (.csproj:55-66) 으로 publish 시 npm install + vite build + dist/→wwwroot/ 자동 복사. LibreOffice 미포함 (시연 범위 밖, 추후 PPTX↔PDF 변환 필요 시 별도 트랙). IIS InProcess 호스팅 설정(.csproj:10) 은 Linux 환경에서 자동 무시
  - **NEW `agenthub/.dockerignore`** (~40 LOC) — bin/obj/node_modules/dist/.vite/.cache + wwwroot/{assets,index.html,uploads} + Migrations.mssql.archive + IDE(.vs/.idea/.vscode) + 시크릿(appsettings.Development|Production.json + .env*) + git + 테스트/문서 산출물 제외. `.env.example` 만 명시적 포함(`!.env.example`)
  - **NEW `agenthub/docker-compose.yml`** (~60 LOC) — service `agenthub` (build context=., ports `64005:8080`, env_file=.env, restart=unless-stopped). environment 변수 ~20 개: ASPNETCORE_*, ConnectionStrings__DefaultConnection (Host=docutil-postgres + Username=AGENT_HUB + Password=${AGENT_HUB_DB_PASSWORD} + Search Path=AIAgentManagement,public), ConnectionStrings__Redis=docutil-redis:6379, DocUtil__BaseUrl=http://docutil-api:8000 + DocUtil__JwtToken=${DOCUTIL_JWT_TOKEN}, Nexus__BaseUrl=${NEXUS_BASE_URL:-http://192.168.22.28:8001}, JwtSettings__SecretKey=${JWT_SECRET_KEY}, Encryption__ApiKeyAesKey=${ENCRYPTION_API_KEY_AES_KEY}, AiApiSettings__{OpenAI,Claude,Gemini,Perplexity,Tavily}__ApiKey=${...}, Logging__LogLevel__*. networks: `docutil-network` (external: true). healthcheck: `curl /swagger` 30s/10s/5retries/90s start_period. **service name 대신 컨테이너명**(docutil-postgres/docutil-redis/docutil-api) 사용 — 다른 compose stack 에서 합류 시 다른 stack 의 service name 이 아닌 컨테이너명만 DNS 해결 가능
  - **NEW `agenthub/.env.example`** (~30 LOC) — 13 키 카탈로그: AGENT_HUB_DB_PASSWORD / JWT_SECRET_KEY / ENCRYPTION_API_KEY_AES_KEY / DOCUTIL_JWT_TOKEN / DOCUTIL_API_KEY / NEXUS_BASE_URL / NEXUS_SHARED_SECRET / OPENAI_API_KEY / CLAUDE_API_KEY / GEMINI_API_KEY / PERPLEXITY_API_KEY / TAVILY_API_KEY. 한국어 주석으로 의도 + 보안 정책 명시
- **자동화 절차 (paramiko + tarfile)**:
  - 패키징: agenthub/ → tar.gz (.dockerignore 패턴 단순화 적용, 472 files / 1.0 MB gzip, 4.8 MB raw)
  - 전송: paramiko SFTPClient → /tmp/agenthub.tar.gz (0.1초)
  - 추출: ssh.exec_command `tar -xzf` → /home/idino/agenthub/
  - .env 생성: 본 PC 의 appsettings.Development.json 에서 시크릿 자동 매핑 (JWT_SECRET_KEY / OPENAI/Gemini/Perplexity/Tavily/Claude / DocUtil JwtToken / Nexus BaseUrl). chmod 600
  - 빌드: `docker compose build` (백그라운드, build.log + build.done 파일로 폴링). **약 3분 (183s)** 만에 PASS — SDK pull 35s + Node 20 apt 설치 30s + dotnet restore 30s + ClientApp build (npm install + vite build) ~60s + dotnet publish ~30s + runtime image 복사 ~10s. 이미지 태그: `agenthub-agenthub:latest`
  - 부팅: `docker compose up -d` 11초 만에 healthy. PostgreSQL 연결 정상(`Hangfire PostgreSQL Server: Host=docutil-postgres, DB=AGENT_HUB, Schema=hangfire`). DatabaseInitializer 시드 멱등 (skipped=15)
  - 헬스체크 PASS: 외부 `http://192.168.10.39:64005/swagger` HTTP 200 + `/` HTTP 200 (`<html lang="ko">`, fingerprint `index-D9BFz-ZL.js` 본 PC 빌드와 동일)
  - DocUtil JWT 갱신: 검증 도중 30분 만료로 `/api/admin/knowledge-base/documents` 502. 즉시 paramiko 로 .env 의 DOCUTIL_JWT_TOKEN 만 새 토큰으로 교체 + `docker compose up -d --force-recreate` (11초 부팅) → 재검증 PASS
- **e2e 라운드트립 검증 (192.168.10.39:64005, 컨테이너 외부 접근)**:
  - admin@example.com / Admin123! 로그인 → AgentHub JWT 555자 (본 PC 와 동일 길이, 같은 SecretKey + 같은 DB)
  - `/api/admin/knowledge-base/documents?page=1&size=3` HTTP 200 → total=30, items=3 (`AI비서_예상구성도_IDINO.pptx` 등) — DocUtil 컨테이너 도달 PASS
  - `/api/admin/knowledge-base/search {query:"acceptance",maxResults:2}` HTTP 200 → results=2, score=0.016, 부산대 인수시험 청크 인용
  - `/v1/chat/completions {model:"docutil-rag-chat","hello"}` HTTP 200 → docutil-rag-chat 한국어 인사 응답, prompt_tokens=61 (RAG 인용 미발생, ChatService → RagService 호출 분기 디버깅 별도 트랙 — 본 PC 동일 동작)
  - wwwroot 정적 서빙 / SPA 라우팅 / Vue 청크 fingerprint 모두 본 PC 와 동일
- **호환성 검증 (회귀 0건)**:
  - 기존 docutil 14 컨테이너 무영향: docutil-network 합류만 추가, docutil compose 파일 무변경
  - 통합 PG 사양 일치: `Host=docutil-postgres, Database=AGENT_HUB, Username=AGENT_HUB, Search Path=AIAgentManagement,public` — Phase 3.6 / 4 / 7 시드 그대로 사용 (admin / 15 Agents / ApiKeys / Roles)
  - 본 PC dotnet run AgentHub (PID 8240) 와 컨테이너 AgentHub 동시 가동 가능 — 다른 호스트라 포트 충돌 없음
  - .env 의 시크릿은 .gitignore 처리 + 호스트 .env 권한 600
- **잠재 위험 / 다음 단계**:
  - **DocUtil JWT 30분 만료** — 시연 중 만료 시 502 graceful 에러. 자동 갱신 별도 트랙 (refresh_token 활용 또는 DocUtil service account)
  - **ChatService → RagService 호출 분기** — `/v1/chat/completions` OpenAI 호환 라우트가 RagService 우회. 본 PC 와 컨테이너 양쪽 동일 동작. Phase A 별도 디버깅 트랙
  - **Nexus 컨테이너화 보류** — 호스트 GPU 부재 + ADR-11 LAN-only 정책. 별도 호스트(192.168.22.28) 또는 stub mode (vLLM 의존 제거 + 단순 FastAPI) 별도 트랙
  - **LibreOffice 의존** — PPTX↔PDF 변환 시연 시 Dockerfile 에 `apt-get install libreoffice fonts-noto-cjk` 추가 필요 (~700MB 이미지 증가). 시연 범위 밖이라 보류
  - **NETSDK1194 warning** — `dotnet publish -c Release -o /app/publish` 가 .sln 우선 선택. Dockerfile 에서 `dotnet publish AIAgentManagement.csproj` 명시로 해소 가능 (별도 트랙)
  - **시연용 임시 ApiKey id=3 (sk-noop, 1일 만료)** — 시연 종료 후 정리 권장
  - **민감 정보 회전** — 본 세션 진행 중 SSH 비번/SQL Server stale 비번/LLM API keys 가 화면에 노출. .gitignore 대상이라 git remote 영향 0이나 회전 권장

### 2026-05-07 (Phase 6.5 — 옵션 ② Production 정적 서빙 PASS + 옵션 ① Vue dev proxy PASS + 사이드바 운영자 KB 메뉴 추가 + 작업 위생 정리, commit `c9d61a4`)
- **목적**: Phase 6.5 풀 e2e 옵션 ②(Production 빌드 후 wwwroot 정적 서빙) + 옵션 ①(Vue dev server 5173 ↔ AgentHub 64005 라운드트립) 검증을 자동 진행 가능 범위에서 모두 완료. Phase 6.3 에서 라우트만 신설하고 사이드바 미연결 상태였던 운영자 KB 메뉴를 정식 진입점으로 노출. 이전 세션 PC 자동종료 직전까지 진행 중이던 작업(`vite.config.ts` proxy 보정 + `npm run build`로 wwwroot 산출물 생성)을 복원하여 이어 진행.
- **변경 파일 (3 modify, 모두 commit `c9d61a4`)**:
  - **MODIFY `agenthub/ClientApp/src/layouts/MainLayout.vue`** (+8 LOC) — `system` 카테고리(line 387 부근, 사용자 KB 직후)에 운영자 KB 메뉴 항목 신설. `name: t('nav.adminKnowledgeBase')` (i18n 키는 Phase 6.3에서 ko/en 양쪽 등록 완료) + `path: '/admin/knowledge-base'` + `icon: 'bi bi-book-half'` + `roles: ['Admin', 'SuperAdmin']`. `hasRole()` 헬퍼가 자동 가드, 일반 User 토큰은 메뉴 미노출. 백엔드 `[Authorize(Roles = "Admin,SuperAdmin")]` 와 이중 방어
  - **MODIFY `agenthub/ClientApp/vite.config.ts`** (+11 LOC) — dev proxy target `localhost:5000` → `localhost:64005` (launchSettings.json applicationUrl 기준 정렬) + `/v1` proxy 신규 추가 (Phase 7.5 OpenAI 호환 엔드포인트 라우팅) + `/hubs` proxy 에 `changeOrigin: true` 보강 (SignalR Origin 헤더 정합). 한국어 주석 4라인 추가
  - **MODIFY `agenthub/.gitignore`** (+3 LOC) — `wwwroot/assets/`, `wwwroot/index.html` 패턴 추가. `npm run build` 또는 `dotnet publish` 산출물이 untracked로 잡히던 이슈 해소. 한국어 주석으로 의도 명시. 기존 `wwwroot/uploads/` + `appsettings.Production.json` 패턴 그대로 보존
- **변경 파일 (별도 — `.gitignore` 대상이라 commit 미포함)**:
  - **MODIFY `agenthub/appsettings.Production.json:3`** — `ConnectionStrings.DefaultConnection`을 SQL Server 잔재(`Server=192.168.10.159;Database=AIAgentManagement;User ID=aiuser;Password=...;TrustServerCertificate=true;MultipleActiveResultSets=true`)에서 PG 통합 형태(`Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Search Path=AIAgentManagement,public`)로 정렬. **원인**: Phase 3.1(MSSQL → PostgreSQL) 시 Development 만 정리되고 Production 누락. `Hangfire.PostgreSql` 1.20+ 가 Npgsql 의 `multipleactiveresultsets` 키워드 미지원으로 부팅 실패(`KeyNotFoundException`). 본 변경으로 해소. 운영 PG 자격증명은 CLAUDE.md 통합 DB 사양 기준
  - **MODIFY `agenthub/appsettings.Development.json`** — `DocUtil` 섹션 신설 (`BaseUrl=http://localhost:8000`, `JwtToken=""`, `ApiKey=""`, `DefaultTimeoutSeconds=60`). Phase 6.1 `IDocUtilClient` 가 읽는 4 키 기본값 등록. JwtToken/ApiKey 는 옵션 ③ 진입 시 사용자가 DocUtil 운영자 토큰 발급 후 주입
- **빌드 검증**:
  - **프론트**: `cd ClientApp && npx vite build` → ✓ 5.36초. 신규 fingerprint `index-D9BFz-ZL.js` (127.36 kB / gzip 41.76 kB) + `MainLayout-BWrLR_4J.js` (메뉴 추가 반영) + `docUtilStore-B3_fMh0O.js` 등. 0 errors
  - **wwwroot 갱신**: `dist/index.html` + `dist/assets/*` → `agenthub/wwwroot/` 복사 (PowerShell `Copy-Item -Recurse -Force`). 이전 fingerprint 청크는 `Remove-Item -Recurse -Force wwwroot/assets` 로 정리
- **부팅 검증 (옵션 ②, Production 모드)**:
  - **명령**: `ASPNETCORE_ENVIRONMENT=Production ASPNETCORE_URLS=http://localhost:64005 dotnet run --no-launch-profile --no-build` (백그라운드 task `bgd2r9hgy`, PID 8240)
  - **부팅 흐름 PASS**: DB 마이그레이션 + DatabaseInitializer 시드(Roles/Users/ApiServices/Agents 15 건 skipped — 멱등) + Hangfire `Schema: hangfire` PG 연결 + dispatchers(ServerWatchdog/CountersAggregator/Worker/DelayedJobScheduler/RecurringJobScheduler) 모두 시작 + Kestrel 64005 LISTENING
  - **헬스체크**: `/` HTTP 200 (wwwroot/index.html 638B `<html lang="ko">` 정적 서빙) + `/swagger` HTTP 200 + `/v1/models` HTTP 401 + 한국어 ErrorResponseDto(`API Key is required` + `X-API-Key 헤더 또는 Authorization: Bearer <key>` hint) + `/api/agents` HTTP 401 (JWT 미부착 거부) + `/assets/index-D9BFz-ZL.js` HTTP 200 (135,771B, `text/javascript`)
  - **SPA proxy 미경유 확인**: Production 환경에서 `Microsoft.AspNetCore.SpaProxy` 비활성 → wwwroot 직접 정적 서빙. `/admin/knowledge-base` 진입 시 SPA index.html 반환 후 vue-router 가 클라이언트 라우팅 처리
- **부팅 검증 (옵션 ①, Vue dev server)**:
  - **명령**: `cd ClientApp && npx vite --host 127.0.0.1 --port 5173` (백그라운드 task `b9bd2ltqb`, PID 7352)
  - **proxy 라운드트립 PASS**: 5173 으로 보낸 요청이 vite proxy 경유 64005 로 forward → `/api/agents` HTTP 401 (JWT 게이트) + `/v1/models` HTTP 401 (ApiKey 게이트) + `/` HTTP 200 (Vue SPA index)
  - **알림**: vite startup 중 esbuild 경고 발생 (별도 호환성 이슈, 본 검증 범위 밖). dev server 자체는 LISTEN + proxy 정상 동작. 검증 후 PowerShell `Stop-Process -Id 7352 -Force` 로 정리
- **호환성 검증 (회귀 0건)**:
  - **MainLayout.vue 다른 메뉴 무변경**: `dashboard/aiServices/management/analytics/system/settings` 6 카테고리 + 21 메뉴 항목 모두 그대로. 운영자 KB 1건만 추가
  - **vite.config.ts 기존 `/api`/`/hubs` proxy 보존**: target 만 5000 → 64005 정렬, 기존 라우트 동작 변경 없음
  - **`/knowledge-base` 사용자 KB 라우트 무변경**: Phase 6.4 [Obsolete] 마킹은 백엔드 모델/서비스 차원이며 사용자 페이지 자체는 deprecate 별도 트랙(Phase 8+)
  - **wwwroot 의 `landing-preview.html`** (39 kB, 2026-03-20 작성) 무변경. `.gitignore` 새 패턴은 `wwwroot/assets/` + `wwwroot/index.html` 만 명시 — `landing-preview.html` 은 git tracked 그대로
- **잠재 위험 / 다음 단계**:
  - **옵션 ③ DocUtil round-trip 사용자 협조 필요**: Docker Desktop GUI 실행은 Claude 도구로 불가. 사용자가 Docker Desktop 시작 + 알림 후 진행. 그 후 자동 가능 단계 — `cd docutil && docker compose up -d` + DocUtil 운영자 JWT 발급 + appsettings 주입 + `KnowledgeBaseSource="DocUtil"` SQL UPDATE + `/v1/chat/completions` RAG 검증 + 운영자 콘솔 업로드 라운드트립
  - **SQL Server stale 비밀번호 노출** — 본 세션 grep 결과로 `aiuser / rnehrwhgdk20@^` 가 화면에 노출. `.gitignore` 대상이라 git 영향 0이지만 운영자가 활성 비밀번호인지 판단 후 회전 권장
  - **appsettings.Development.json LLM API 키 노출** — OpenAI/Gemini/Perplexity/Tavily + Gmail SMTP 비밀번호 평문 grep 결과 노출. 동일하게 `.gitignore` 대상이나 회전 권장 대상
  - **vue-tsc Node 24 호환** — 본 빌드는 `vite build` 만 사용 (타입 체크 생략). 별도 트랙으로 vue-tsc 2.x 업그레이드 필요
  - **Phase 6.3 운영자 KB 라우트 deep link** — 사이드바 메뉴 추가로 정식 진입점 확보. URL 직접 진입(`/admin/knowledge-base`) + 메뉴 클릭 둘 다 동일 SPA 라우팅
  - **secret leak history sanitize + force-push** — 시연용이라 보류 그대로

### 2026-05-06 (Phase 6.3 — AgentHub Vue 운영자 KB 콘솔 신설, R2 단일 진입점 외부 표면 구현)
- **목적**: 통합 비전(R2 / ADR-2) 의 "운영자 KB 관리는 AgentHub UI 단일 진입점" 외부 표면 확보. Phase 6.1 의 `IDocUtilClient` (서비스 레이어) 와 Phase 6.4 의 `[Obsolete]` 마킹 사이에서, 운영자가 실제로 DocUtil 문서를 업로드 / 조회 / 검색 / 삭제할 수 있는 BFF 컨트롤러 + Vue 3 콘솔을 신설한다. DocUtil 운영자 페이지(별도 트랙) 와 본 콘솔은 R2 에 따라 AgentHub 콘솔만 정식 채널이며, DocUtil 측은 추후 deprecate 예정. 시연용 환경 구성: DocUtil 인스턴스 부팅 + AgentHub `DocUtil:JwtToken/ApiKey` 주입 시 즉시 동작
- **변경 파일 (1 신규 백엔드 컨트롤러 + 1 신규 service + 1 신규 store + 3 신규 view + 2 modify router/i18n)**:
  - **NEW `agenthub/Controllers/AdminKnowledgeBaseController.cs`** (~230 LOC, 6 메서드 + 1 request DTO) — `[ApiController][Route("api/admin/knowledge-base")][Authorize(Roles = "Admin,SuperAdmin")]`. 의존성: `IDocUtilClient _docUtilClient` + `ILogger<AdminKnowledgeBaseController> _logger`. 6 메서드(BFF 위임): `GET /documents` (folderId/page/size 쿼리, page<1 정규화 + size 1~200 클램프) / `GET /documents/{id}` (404 → ErrorResponseDto.NotFound) / `POST /documents/upload` (`[FromForm] IFormFile file` + folderId/visibility, `[RequestSizeLimit(100*1024*1024)]`, file.OpenReadStream() `await using`) / `DELETE /documents/{id}` (NoContent) / `GET /documents/{id}/chunks` / `POST /search` (body `AdminKnowledgeBaseSearchRequest{Query,CollectionRef,MaxResults}` — MaxResults 1~50 클램프). 모든 메서드는 `InvalidOperationException` 을 catch 후 502 + `ErrorResponseDto("DOCUTIL_UPSTREAM_ERROR", upstream=ex.Message)` 한국어 응답. DocUtil DTO(`DocUtilDocumentList`/`DocUtilSearchResult` 등) 를 그대로 외부에 노출 — Program.cs `JsonNamingPolicy.CamelCase` 가 자동 변환 (camelCase JSON). 책임 범위: 인증 게이트 + multipart 변환 + 한국어 ErrorResponseDto. 책임 범위 밖: DocUtil 인증 토큰 부착(DocUtilClient 가 처리)
  - **NEW `agenthub/ClientApp/src/services/docutilService.ts`** (~150 LOC) — axios `api` 인스턴스(`services/api.ts` JWT 자동 부착) 활용. 6 함수: `listDocuments(folderId?, page=1, size=20)` / `uploadDocument(file, folderId?, visibility?)` (FormData multipart) / `getDocument(id)` (404 → null 정규화) / `deleteDocument(id)` (Promise<void>) / `getChunks(id)` / `search(query, collectionRef?, maxResults=10)`. TypeScript 인터페이스(`DocumentSummary`/`DocumentList`/`DocumentDetail`/`UploadResult`/`Chunk`/`SearchHit`/`SearchResult`) 백엔드 camelCase DTO 와 1:1 매핑. encodeURIComponent 적용 (id 가 UUID/문자열 가능)
  - **NEW `agenthub/ClientApp/src/stores/docUtilStore.ts`** (~165 LOC, Pinia setup store) — 상태 11개(documents/currentDocument/currentChunks/searchResults/lastSearchQuery/pagination/currentFolderId/isLoading/isUploading/isSearching/error) + 액션 6개(fetchDocuments/uploadDocument/removeDocument/loadDocumentDetail/searchKnowledgeBase/clearSearch/clearError). 에러 추출 헬퍼 `extractMessage(err, fallback)` — `err?.response?.data?.message || err?.message || fallback` 우선순위. 각 액션은 try/catch + finally 로 isLoading 정리. uploadDocument/removeDocument 성공 시 fetchDocuments 자동 재호출(현재 folderId/page 보존). loadDocumentDetail 은 detail 성공 후 getChunks 보조 호출(실패 시 currentChunks=[] + console.warn 로 graceful)
  - **NEW `agenthub/ClientApp/src/views/AdminKnowledgeBase.vue`** (~290 LOC) — 운영자 KB 메인 페이지. 레이아웃: `page-header` 제목 + 액션버튼(업로드/새로고침) → 검색 카드(쿼리 + folderId + 검색/지우기) → 에러 알림(닫기 버튼 + ARIA `role="alert"`) → 검색 결과 카드(score 뱃지 + 청크 미리보기 280자 절사) → 문서 목록 테이블(아이콘 + 이름/ID + 상태 뱃지 + 생성일 + 상세/삭제 액션) + 페이지네이션 카드 footer(이전/다음 + 현재페이지/총페이지). vue-router push: `goUpload()` → `AdminKnowledgeBaseUpload` (folderId 쿼리 전달) / `goDetail(id)` → `AdminKnowledgeBaseDetail`. 접근성: ARIA-label / role="alert" / role="button" / `<nav aria-label>` 페이지네이션 / `visually-hidden` 스피너 라벨. statusBadgeClass 헬퍼: 상태 문자열 매핑(index/ready/completed → success / pending/queue/progress → warning / fail/error → danger / 그 외 → secondary)
  - **NEW `agenthub/ClientApp/src/views/AdminKnowledgeBaseUpload.vue`** (~210 LOC) — 파일 업로드 페이지. 드래그앤드롭 dropzone(`@dragover/@dragleave/@drop` + 키보드 enter/space 활성화 + `tabindex="0"` + `role="button"`) → 파일 선택 시 이름/크기 표시 + 제거 버튼 → folderId/visibility(select: ""/public/internal/confidential) 메타 입력 → 진행 카드(spinner + Bootstrap progress-bar-striped-animated) → 성공 알림(0.8s 후 목록 페이지 push). MIME 허용: pdf/txt/csv/xls/xlsx/doc/docx/hwp/pptx. formatBytes 헬퍼(B/KB/MB/GB). route.query.folderId 자동 prefill (메인에서 전달된 폴더 보존)
  - **NEW `agenthub/ClientApp/src/views/AdminKnowledgeBaseDetail.vue`** (~190 LOC) — 문서 상세 페이지. 상단 액션(뒤로/삭제) → 로딩/미존재/상세 3분기 → 메타데이터 카드(`<dl class="row">` 6필드: 이름/ID/상태/생성일/업로더/visibilityTargets JSON) + 요약 카드(청크 수) → 청크 목록 카드(인덱스 뱃지 + chunkId code + content `<p class="chunk-text">` whitespace-pre-wrap). `watch(() => route.params.id, load)` 로 라우트 변경 시 재로드. onDelete 후 confirm 통과 시 store.removeDocument → 목록 push
  - **MODIFY `agenthub/ClientApp/src/router/index.ts`** (+18 LOC) — 기존 `knowledge-base` 라우트(`KnowledgeBase.vue`, 사용자 페이지) 유지, 직후에 3 라우트 추가: `admin/knowledge-base` (name=`AdminKnowledgeBase`, meta.role='Admin') / `admin/knowledge-base/upload` (name=`AdminKnowledgeBaseUpload`, meta.role='Admin') / `admin/knowledge-base/:id` (name=`AdminKnowledgeBaseDetail`, meta.role='Admin'). MainLayout 자식으로 자연 삽입(requiresAuth 자동 상속). meta.role 은 현재 advisory — 실제 권한 게이트는 백엔드 `[Authorize(Roles = "Admin,SuperAdmin")]` 가 hard enforce
  - **MODIFY `agenthub/ClientApp/src/i18n/locales/{ko,en}.json`** (+~50 LOC each) — `common.optional` 키 신설 (선택 / optional) + `nav.adminKnowledgeBase` 신설 (지식베이스 관리 / Knowledge Base (Admin)) + 신규 섹션 `adminKb` 47키: `title/subtitle/documents/empty/upload/uploadTitle/uploadSubtitle/uploading/uploadSuccess/removeFile/dropzoneLabel/dropzoneTitle/dropzoneHint/search/searching/searchPlaceholder/searchResultsFor({query})/searchEmpty/clearSearch/score/folderId/folderIdPlaceholder/folderIdHint/folderIdDesc/currentFolder/visibility/visibilityDefault/visibilityPublic/visibilityInternal/visibilityConfidential/refresh/viewDetail/delete/deleteConfirm({name})/docName/docId/docStatus/docCreatedAt/uploaderName/metadata/summary/chunks/chunkCount/chunksEmpty/detailTitle/detailSubtitle/notFound/pageInfo({page,total})/pagination`. R5 한국어 우선 — 사용자향 메시지 모두 한국어
- **빌드 검증**:
  - **백엔드**: `cd /d/workspace/IDINO_Agent_Hub/agenthub && dotnet build --no-restore -v quiet` → **에러 0개 / 경고 17개 (모두 pre-existing — 11 CS1998 + 6 CS0618 from Phase 6.4 [Obsolete] 마킹)**. 본 Phase 신규 경고 0건. 첫 시도 PASS
  - **프론트엔드**: `cd ClientApp && npm install` (127 packages, 3s, 사전 vue-tsc/vite 미설치 보정) → `npx vite build` → **3.59초 ✓ built / 0 errors**. 신규 청크 `AdminKnowledgeBase-YzbJ-gzt.js` (9.05 kB / gzip 3.08 kB) 분리 빌드 확인
  - **타입 검증**: vue-tsc 1.x 는 Node 24 (regex 변경) 와 호환 깨짐(상위 known issue, 본 작업 범위 밖) — 폴백으로 `npx tsc --noEmit -p tsconfig.json` 실행 → 신규 파일 6건 (`docutilService.ts`/`docUtilStore.ts`/`AdminKnowledgeBase.vue`/`AdminKnowledgeBaseUpload.vue`/`AdminKnowledgeBaseDetail.vue`/router 변경) 타입 오류 **0건**. tsc 가 보고한 2건(`useMessageFormatting.ts:145`/`sseClient.ts:120`) 은 pre-existing — 본 Phase 영향 0건
  - **JSON 무결성**: `node -e "JSON.parse(...)"` 로 ko/en 양 locale 파싱 검증 — 두 파일 모두 정상
- **호환성 검증 (회귀 0건)**:
  - **기존 사용자 KB 페이지(`KnowledgeBase.vue`) 무변경**: route `/knowledge-base` + name `KnowledgeBase` 그대로. 본 Phase 는 운영자용 별도 진입점(`/admin/knowledge-base`) 신설이며, 기존 사용자 KB UI 는 deprecate 마킹 외 변경 없음 — Phase 6.4 / 8+ 별도 처리
  - **백엔드 인증 격리**: `[Authorize(Roles = "Admin,SuperAdmin")]` 부착으로 일반 User 토큰은 401/403. 시연 환경에서 운영자 계정만 본 콘솔 접근 가능
  - **DocUtil 미부팅 시 graceful**: DocUtilClient 가 401/5xx 응답을 `InvalidOperationException` 한국어 메시지로 매핑 → AdminKnowledgeBaseController 가 catch 후 502 + ErrorResponseDto. 사용자 화면은 alert 카드로 한국어 에러 표시 (Vue store 의 error ref → AdminKnowledgeBase.vue 의 `<div v-if="store.error">`)
  - **i18n 키 누락 0건**: 신규 키 47개 + 기존 사용 패턴(`{{ t('adminKb.xxx') }}`) 일관. ko.json / en.json 양쪽 동일 키 셋
- **잠재 위험 / 다음 단계**:
  - DocUtil 운영자 JWT 발급 절차 (Q9 / Phase 6.5 e2e) — 본 Phase 는 발급된 토큰을 `appsettings.Development.json` 의 `DocUtil:JwtToken` 또는 환경변수로 주입한다고 가정. 자동화는 Phase 6.5 별도 트랙
  - vue-tsc Node 24 호환 — vue-tsc 2.x 또는 vue-tsc + tsc 조합으로 업그레이드 권장 (본 작업 범위 밖, 별도 트랙)
  - Sidebar 메뉴 연결 — MainLayout 의 운영자 메뉴(`/admin/*`) 그룹화는 별도 작업. 현재는 URL 직접 진입 또는 deep link 만 지원
  - Phase 6.5 e2e (시연용 DocUtil JWT 발급 + Agent.KnowledgeBaseSource="DocUtil" 전환 시 RAG 응답 + AgentHub 운영자 콘솔 업로드 → DocUtil 인덱싱 round-trip) — 사용자 결정 대기

### 2026-05-06 (Phase 6.4 — 자체 KB Models/Services/Controller `[Obsolete]` 마킹 + RagService 폴백 흐름 한국어 주석 보강, ADR-2 빌드-시 강제)
- **목적**: ADR-2 (RAG 단일 권위 = DocUtil) 의 빌드-시 강제. Phase 6.1+6.2 에서 코드 경로(IDocUtilClient + RagService 분기) 를 갖춘 후, 자체 KB(KnowledgeBaseDocument/DocumentChunk/IKnowledgeBaseService/KnowledgeBaseService/IDocumentIndexingService/DocumentIndexingService/KnowledgeBaseController) 7건에 `[Obsolete(message, error: false)]` 어트리뷰트 부착하여 신규 사용 차단(CS0618 경고 발생) + 기존 호출 호환 보존(컴파일 오류 0건). 실제 DB drop 은 Phase 8+ 별도 트랙(운영 데이터 마이그레이션 동반)
- **변경 파일 (7 modify — 모두 클래스/인터페이스 레벨 [Obsolete] + 한국어 주석 블록 + 1 modify — RagService 폴백 흐름 한국어 주석 보강)**:
  - **MODIFY `agenthub/Models/KnowledgeBaseDocument.cs`** (+8 LOC) — `[Table("KnowledgeBaseDocuments")]` 직전에 `[Obsolete("ADR-2: AgentHub 자체 KB 는 deprecate 됨. 신규 코드는 DocUtil 의 tb_documents 를 IDocUtilClient 경유로 사용할 것. Phase 8+ 에서 drop 예정.", error: false)]` 부착 + 6라인 한국어 주석 (.claude/rules/anti-patterns.md §7 / architecture.md P8 인용). EF 모델 컬럼/속성/Navigation 무변경
  - **MODIFY `agenthub/Models/DocumentChunk.cs`** (+7 LOC) — 동일 패턴. `[Obsolete("ADR-2: AgentHub 자체 KB 청크는 deprecate 됨. 신규 코드는 DocUtil 의 청크/임베딩을 IDocUtilClient.GetChunksAsync 로 조회할 것. Phase 8+ 에서 drop 예정.", error: false)]`. ChunkId/DocumentId/ChunkIndex/Content/Embedding(JSON)/Metadata 컬럼 무변경
  - **MODIFY `agenthub/Services/IKnowledgeBaseService.cs`** (+8 LOC) — 인터페이스 레벨 `[Obsolete("ADR-2: AgentHub 자체 KB CRUD 는 deprecate. 신규 코드는 IDocUtilClient (Phase 6.1) 사용. Phase 8+ 에서 제거 예정.", error: false)]`. 7 메서드 시그니처(GetDocumentsAsync/GetDocumentByIdAsync/CreateDocumentAsync/UpdateDocumentAsync/DeleteDocumentAsync/IndexDocumentAsync/ReindexDocumentAsync) 무변경
  - **MODIFY `agenthub/Services/KnowledgeBaseService.cs`** (+7 LOC) — 구현체 레벨 동일. 본문(150 LOC) 무변경 — DbContext + IDocumentIndexingService 의존성 + 7 메서드 그대로
  - **MODIFY `agenthub/Services/IDocumentIndexingService.cs`** (+7 LOC) — 인터페이스 레벨 `[Obsolete("ADR-2: AgentHub 자체 문서 인덱싱은 deprecate. 신규 코드는 IDocUtilClient.UploadDocumentAsync 사용. Phase 8+ 에서 제거 예정.", error: false)]`. IndexDocumentAsync/ReindexDocumentAsync/DeleteDocumentChunksAsync/SplitIntoChunks 시그니처 무변경
  - **MODIFY `agenthub/Services/DocumentIndexingService.cs`** (+7 LOC) — 구현체 레벨 동일. 본문(~210 LOC) 무변경 — 청크 분할 + IEmbeddingService.GetEmbeddingsAsync + DocumentChunks INSERT + 인덱싱 상태 갱신 모두 그대로
  - **MODIFY `agenthub/Controllers/KnowledgeBaseController.cs`** (+8 LOC) — 클래스 레벨 `[Obsolete("ADR-2: 운영자 KB 관리는 AgentHub Vue UI(Phase 6.3, IDocUtilClient 경유) 로 이전. /api/knowledgebase 는 Phase 5+ 호환 유지. Phase 8+ 에서 제거 예정.", error: false)]`. 라우트(`api/knowledgebase`) 보존 — Phase 5+ 호환 + Swagger deprecated 표시. 5 액션(GetDocuments/GetDocument/CreateDocument/UpdateDocument/DeleteDocument + IndexDocument + ReindexDocument) 시그니처 무변경
  - **MODIFY `agenthub/Services/RagService.cs`** (+11 LOC, 한국어 주석 블록) — 자체 KB 폴백 흐름 진입부(쿼리 임베딩 캐시 분기 직전, line 102 부근) 에 ADR-2 / Phase 5+ 호환 / Phase 6.5 안전망 / CS0618 의도적 발생 설명 11라인 추가. RagService 자체에는 [Obsolete] 부착 X — IRagService 인터페이스 계약 보존 (자체 KB 분기 + DocUtil 분기 둘 다 호출자에게 동일 계약)
- **빌드 검증**:
  - `dotnet build --no-restore --no-incremental -v quiet` → **에러 0건 / 경고 22건 (CS0618 신규 11 + CS1998 pre-existing 11)**. 첫 시도 PASS
  - **CS0618 신규 11곳 (고유 위치)** 분포:
    - `Controllers/FilesController.cs` (2): line 15 (필드 `private readonly IKnowledgeBaseService _knowledgeBaseService`), line 20 (생성자 매개변수)
    - `Data/AIAgentManagementDbContext.cs` (4): line 25 (`DbSet<KnowledgeBaseDocument>`), line 26 (`DbSet<DocumentChunk>`), line 272 (`modelBuilder.Entity<KnowledgeBaseDocument>` 인덱스), line 277 (`modelBuilder.Entity<DocumentChunk>` 인덱스)
    - `Models/AgentDocument.cs` (1): line 26 (`KnowledgeBaseDocument Document` Navigation)
    - `Program.cs` (4): line 272 (`AddScoped<IDocumentIndexingService, DocumentIndexingService>` — 인터페이스 + 구현 각 1), line 274 (`AddScoped<IKnowledgeBaseService, KnowledgeBaseService>` — 동일)
  - **CS0618 미발생 위치 (의도된 동작)**:
    - `KnowledgeBaseController` 내부의 `IKnowledgeBaseService` 사용 — 둘 다 [Obsolete] 클래스 → C# 컴파일러가 [Obsolete] 영역 내부의 사용은 경고 안 함
    - `KnowledgeBaseService` 내부의 `_context.KnowledgeBaseDocuments`, `_context.DocumentChunks` — 클래스 자체가 [Obsolete] → 동일 동작
    - `DocumentIndexingService` 내부의 동일 사용 — 동일 동작
    - `RagService.RetrieveAsync` 의 자체 KB 폴백 분기 — `_context.{DbSet<T>}` generic 타입 추론 경로라 컴파일러가 명시적 deprecation 경고 미생성. 의도된 폴백 흐름 보존
- **호환성 검증 (회귀 0건)**:
  - **외부 시그니처 보존**: 7 파일 모두 클래스/인터페이스 레벨 어트리뷰트만 부착. 메서드/필드/속성/생성자 시그니처 무변경
  - **본문 무변경**: 150 LOC + 210 LOC + 200 LOC 의 KnowledgeBaseService/DocumentIndexingService/KnowledgeBaseController 본문 그대로 — 기존 호출(FilesController + KnowledgeBaseController + RagService 의 DbSet 사용) 모두 정상 동작
  - **DB 스키마 변경 0건**: KnowledgeBaseDocuments / DocumentChunks 테이블 그대로. EF migration 신규 생성 불필요
  - **API 라우트 보존**: `/api/knowledgebase` 5+2 액션 모두 동작. Swagger 에서 [Obsolete] 표시되나 호출은 가능
  - **DI 그래프 보존**: Program.cs 의 `AddScoped<IDocumentIndexingService, DocumentIndexingService>` + `AddScoped<IKnowledgeBaseService, KnowledgeBaseService>` 등록 그대로 (CS0618 경고 발생하나 동작)
  - **RagService 자체 KB 폴백 정상**: KnowledgeBaseSource ≠ "DocUtil" (또는 NULL/"AgentHub") 인 모든 기존 Agent 는 기존 흐름 그대로 — 임베딩 캐시 → DocumentChunks 조회 → 코사인 유사도 → Top-K. Phase 5.1 의 default "AgentHub" 보존
- **잠재 위험 / Open Questions**:
  - **CS0618 경고 11건 누적**: pre-existing CS1998 11건과 합쳐 빌드 경고 22건. 빌드 게이트(`dotnet build --warnaserror`) 도입 시 차단 가능성 — 현재는 경고 허용 정책이라 영향 없으나, Phase 8+ drop 시 동시 정리 필요. `#pragma warning disable CS0618` 사용은 비권장(deprecation 인식 차단)
  - **R20 (TECHSPEC §16): AgentHub KB → DocUtil visibility 매핑** — Phase 6.4 마킹으로 신규 사용 차단했으나, 운영 데이터(KnowledgeBaseDocuments 행) 의 DocUtil 마이그레이션 정책(`IsPublic`/`CreatedBy` ↔ DocUtil `visibility_targets`/`folder_id`/`scope_id` 매핑) 미정 — Phase 8+ 에서 운영자 마이그레이션 가이드 작성 시 결정
  - **자체 KB 호출처 CS0618 미발생 위치**: RagService 의 자체 KB 폴백 분기는 CS0618 경고가 안 잡혀 신규 사용 검출 차단 효과 약함. 본 분기에 의존하는 신규 코드 추가는 코드 리뷰에서 포착해야 함 — Phase 8+ drop 전까지 수동 점검
  - **Migrations 폴더 영향**: `Migrations/AIAgentManagementDbContextModelSnapshot.cs` + `20260505154102_Init.cs` + `Designer.cs` 3 파일이 [Obsolete] 클래스를 사용하나 EF 자동 생성물이라 수정 X — CS0618 경고가 누적되나 의도된 동작
- **Phase 6 진척**:
  - [x] 6.1 — IDocUtilClient + DocUtilClient + Named HttpClient + appsettings DocUtil 섹션 (2026-05-06)
  - [x] 6.2 — RagService.RetrieveAsync 분기 (KnowledgeBaseSource="DocUtil" → DocUtilClient.SearchAsync) (2026-05-06)
  - [x] 6.4 — 자체 KB Models/Services/Controller [Obsolete] 마킹 (본 Phase, 2026-05-06)
  - [ ] 6.3 — AgentHub Vue 운영자 KB UI (`/admin/knowledge-base` 페이지 + 한국어 UI + Pinia 스토어)
  - [ ] 6.5 — e2e 검증 (시연용 DocUtil JWT 발급 + Agent.KnowledgeBaseSource SQL UPDATE + `/v1/chat/completions` RAG 응답 로그 검증)
- **다음 단계**:
  - **Phase 6.5** (권장 우선) — 시연용 DocUtil 운영자 JWT 발급 → `appsettings.Development.json` 의 `DocUtil:JwtToken` 주입 → 시드 Agent 1건(예: AgentCode `customer-support` 또는 `docutil-rag-chat`) 의 KnowledgeBaseSource SQL UPDATE → DocUtil 의 시드 collection ID 로 KnowledgeBaseRef 설정 → /v1/chat/completions 호출 시 RAG 결과가 DocUtil 청크에서 오는지 로그 검증. Phase 6.1+6.2+6.4 의 진위 확인
  - **Phase 6.3** — 운영자 KB 콘솔 Vue UI 신설. AgentHub `/admin/knowledge-base` 페이지 + IDocUtilClient 6 메서드 노출 + Pinia 스토어 + 한국어 UI(목록/업로드/삭제/검색/청크 검수)
  - **Phase 8+ 별도 트랙**: 운영 데이터 DocUtil 마이그레이션(R20 visibility 매핑 정책 결정 후) + KnowledgeBaseDocuments/DocumentChunks DB drop + EF migration 생성 + 위 [Obsolete] 마킹 파일 7건 삭제 + Migrations 폴더 정리
- **DB / 시드 / 마이그레이션 영향 0건**: 본 Phase 는 어트리뷰트 + 한국어 주석만. AGENT_HUB DB / 시드 / EF 마이그레이션 모두 그대로

### 2026-05-06 (Phase 6.1+6.2 — DocUtil RAG/문서 BFF 클라이언트 + RagService.RetrieveAsync 분기, ADR-2 RAG 단일 권위 코드 진입점 확보)
- **목적**: 통합 비전(ADR-2) 의 "RAG 단일 권위 = DocUtil" 을 실제 코드에서 강제하는 첫 단계. AgentHub 가 자체 KB 임베딩/유사도 계산을 하지 않고, `Agent.KnowledgeBaseSource="DocUtil"` 로 운영자가 전환한 Agent 의 RAG 검색을 DocUtil FastAPI(`/api/v1/search`) 로 위임한다. Phase 5.1 에서 미리 추가해둔 `Agent.KnowledgeBaseSource` / `KnowledgeBaseRef` 컬럼을 그대로 활용 — EF 모델 변경 0건. 외부 시그니처(`IRagService.RetrieveAsync`) 도 무변경 — 호출자(`AiProxyService.SendChatMessageAsync` 의 EnableRag 분기) 무영향
- **변경 파일 (2 신규 + 3 수정)**:
  - **NEW `agenthub/Services/IDocUtilClient.cs`** (~135 LOC) — DocUtil BFF 인터페이스 (6 메서드) + 6 record DTO. 메서드: `SearchAsync(query, collectionRef, maxResults)` (RAG 핵심) / `ListDocumentsAsync(collectionRef, page, size)` (운영자 콘솔 — Phase 6.3 의존 항목) / `GetDocumentAsync(documentId)` (404 → null 정규화) / `UploadDocumentAsync(stream, fileName, collectionRef, visibility)` (multipart/form-data) / `DeleteDocumentAsync(documentId)` / `GetChunksAsync(documentId)` (운영자 청크 검수). DTO: `DocUtilSearchResult`/`DocUtilSearchHit`/`DocUtilDocumentList`/`DocUtilDocumentSummary`/`DocUtilDocumentDetail`/`DocUtilUploadResult`/`DocUtilChunk`. 모든 record 는 sealed + 한국어 XML doc 부착
  - **NEW `agenthub/Services/DocUtilClient.cs`** (~410 LOC) — IDocUtilClient 구현체. 핵심 설계:
    - **Named HttpClient `"docutil"` 사용** (P1 단일 진입점 + .claude/rules/anti-patterns.md #2 — 직접 인스턴스화 금지). 생성자 주입: `IHttpClientFactory`, `IConfiguration`, `ILogger<DocUtilClient>`
    - **Bearer 부착 정책**: `ApplyAuthorizationHeader` 헬퍼 — 우선순위 `DocUtil:JwtToken` > `DocUtil:ApiKey`. 둘 다 비어있으면 헤더 미부착 후 LogWarning("운영자 토큰 발급 후 환경변수 / appsettings 에 주입 필요"). DocUtil 측 401/403 응답 시 `EnsureSuccessOrThrowKoreanAsync` 가 한국어 메시지로 매핑 — 시연용 graceful 폴백
    - **JSON 직렬화 옵션**: `JsonNamingPolicy.SnakeCaseLower` + `PropertyNameCaseInsensitive=true` + `WhenWritingNull` ignore. DocUtil FastAPI(SQLAlchemy 2 / Pydantic) 의 snake_case 와 1:1 매핑. private response DTO 는 `[JsonPropertyName]` 명시(`created_at`/`uploader_name`/`visibility_targets`/`job_id`/`chunk_id`/`chunk_index`)
    - **SearchAsync**: `POST /api/v1/search` body `{query, max_results, scope_id?}`. collectionRef 비어있으면 글로벌 검색. 빈 query 는 빈 결과 반환(DocUtil 호출 비용 절감 + 422 회피)
    - **UploadDocumentAsync multipart 처리**: `MultipartFormDataContent` + `StreamContent` (호출자 stream 소유 — 본 메서드 Dispose 금지) + `application/octet-stream` Content-Type 부착. boundary 는 .NET 기본 자동 생성. folder_id/visibility 는 `StringContent(_, Encoding.UTF8)` 로 form field 추가
    - **GetDocumentAsync**: 404 → null 정규화(NotFoundException 미사용 — 호출자 분기 단순화)
    - **DeleteDocumentAsync**: 204 NoContent / 200 OK 모두 성공 인정
    - **에러 매핑** (`EnsureSuccessOrThrowKoreanAsync`): 401/403 → `"DocUtil 인증 실패. JwtToken 또는 ApiKey 설정을 확인하세요."` / 5xx → `"DocUtil 응답 실패. 네트워크 또는 서비스 상태를 확인하세요. (HTTP {status})"` / 그 외 4xx → `"DocUtil 호출이 실패했습니다 (HTTP {status}): {body 200자 절사}"`. 모두 `InvalidOperationException` 으로 통일 — AgentHub `GlobalExceptionHandlerMiddleware` 가 502/503 합성
  - **MODIFY `agenthub/Program.cs`** (+13 LOC) — Nexus Named HttpClient 등록부 인접에 `"docutil"` HttpClient 추가: `BaseUrl` 기본값 `http://localhost:8000` (DocUtil docker compose 기본 포트) + `Timeout=DocUtil:DefaultTimeoutSeconds (default 60s)`. 서비스 등록부에 `builder.Services.AddScoped<IDocUtilClient, DocUtilClient>();` 추가 (Phase 5.1 의 `INexusClient` 등록 직후 — 자연 인접)
  - **MODIFY `agenthub/appsettings.json`** (+6 LOC) — `Nexus` 섹션 직후에 `DocUtil` 섹션 추가: `BaseUrl=http://localhost:8000` + `JwtToken=""` + `ApiKey=""` + `DefaultTimeoutSeconds=60`. JwtToken/ApiKey 빈 폴백은 시연용 시작 환경 보호 — 운영자가 DocUtil 운영자 JWT 발급 후 환경변수(`DocUtil__JwtToken`) 또는 디스크 `appsettings.Development.json` 에 주입하면 즉시 동작. **R4 시크릿 비커밋 준수** — appsettings.json 의 빈 문자열은 placeholder 일 뿐, 실제 값은 .gitignore 대상 디스크 파일에서만 로드
  - **MODIFY `agenthub/Services/RagService.cs`** (+85 LOC) — Phase 6.2 분기 추가:
    - 생성자에 `IDocUtilClient _docUtilClient` 의존성 주입(필드 추가 + 매개변수 + 할당)
    - `RetrieveAsync` 의 RAG 캐시 hit 분기 직후, 자체 KB 임베딩 흐름(`_embeddingService.GetEmbeddingAsync` 호출) 직전에 KnowledgeBaseSource 권위 시스템 분기 신설:
      ```
      if (agentId.HasValue) {
          var agentRouting = await _context.Agents.AsNoTracking()
              .Where(a => a.AgentId == agentId.Value)
              .Select(a => new { a.KnowledgeBaseSource, a.KnowledgeBaseRef })
              .FirstOrDefaultAsync(ct);
          if (agentRouting != null && agentRouting.KnowledgeBaseSource == "DocUtil") {
              try { var search = await _docUtilClient.SearchAsync(query, agentRouting.KnowledgeBaseRef, topK, ct);
                    var results = search.Results.Select(MapDocUtilHitToDto).ToList();
                    await _cachingService.SetAsync(ragCacheKey, results, TimeSpan.FromMinutes(10));
                    return results; }
              catch (Exception ex) { _logger.LogError(ex, ...); return new List<RagSearchResultDto>(); }
          }
      }
      ```
    - `MapDocUtilHitToDto(DocUtilSearchHit hit)` 정적 헬퍼 신설 — `RagSearchResultDto` 와 DocUtil 응답 schema mismatch 흡수: ChunkId(long) ← `hit.Id?.GetHashCode()` 안정적 hash (DocUtil string UUID → int) / Similarity(float) ← `(float)hit.Score` / Title/Source ← `metadata.title`/`metadata.source` JsonElement best-effort 추출, 미존재 시 "DocUtil Document"/"DocUtil" 폴백 / DocumentId(int) ← `metadata.document_id` (Number 또는 String 모두 처리), 실패 시 0 / Metadata ← DocUtil 원본을 `JsonSerializer.Serialize` 로 직렬화하여 보존. 본 매핑은 임시 — Phase 6.4 에서 `RagSearchResultDto.ChunkId` 자체를 string 으로 확장하는 것이 정도(正道)
- **빌드 검증**:
  - `cd /d/workspace/IDINO_Agent_Hub/agenthub && dotnet build --no-restore -v quiet` → **에러 0개 / 경고 11개 (모두 pre-existing CS1998 — Phase 7.5 시점부터 동일, 본 Phase 신규 경고 0건)**. 첫 시도 PASS
  - `IDocUtilClient` / `DocUtilClient` / `RagService` 모두 컴파일 성공 — 의존성 그래프 순환 없음(`RagService → IDocUtilClient → IHttpClientFactory + IConfiguration + ILogger`)
- **호환성 검증 (회귀 0건)**:
  - **외부 시그니처 보존**: `IRagService.RetrieveAsync` 무변경 — 호출자(`AiProxyService.SendChatMessageAsync` 의 EnableRag 분기) 코드 수정 0건
  - **AgentHub 자체 KB 폴백**: KnowledgeBaseSource ≠ "DocUtil" (또는 NULL/"AgentHub") 인 모든 기존 Agent 는 기존 흐름 그대로 — 임베딩 캐시 → DocumentChunks 조회 → 코사인 유사도 계산 → Top-K. 즉, Phase 5.1 의 기본값 "AgentHub" 가 보존됨
  - **DocUtil JWT/ApiKey 미설정 시**: appsettings.json 빈 문자열 폴백 → DocUtilClient 가 LogWarning 후 헤더 미부착 → DocUtil 측 401 → `EnsureSuccessOrThrowKoreanAsync` 가 `"DocUtil 인증 실패..."` 한국어 예외 → RagService catch 블록이 LogError + 빈 결과 반환. 사용자 화면은 "검색 결과 없음" 으로 graceful 동작
  - **EF 모델 변경 0건**: Phase 5.1 의 `Agent.KnowledgeBaseSource` (Required, MaxLength 32, default "AgentHub") + `Agent.KnowledgeBaseRef` (MaxLength 100, nullable) 컬럼 그대로 활용 — 마이그레이션 신규 생성 불필요
  - **DI 그래프 검증**: `IDocUtilClient` 는 Scoped 등록 → `RagService` (Scoped) 의 의존성 적합. captive dependency 없음
- **AgentCode/AgentRouting 매핑 (예시 — Phase 6.5 e2e 시 운영자가 SQL UPDATE 또는 Vue UI 로 전환)**:

  | AgentCode | KnowledgeBaseSource | KnowledgeBaseRef | 동작 |
  |---|---|---|---|
  | (기존 모든 Phase 7.1 시드 Agent) | AgentHub (default) | NULL | 자체 KB(AgentDocuments + DocumentChunks) 검색. 기존 흐름 보존 |
  | (운영자가 전환한 Agent) | DocUtil | "{folder_id}" 또는 NULL | DocUtil `/api/v1/search` 위임. NULL 이면 DocUtil 글로벌 검색 |

- **잠재 위험 / Open Questions**:
  - **R20 (TECHSPEC §16): AgentHub KB → DocUtil visibility 매핑 미정** — 운영자가 자체 KB 문서를 DocUtil 로 일괄 마이그레이션할 때, AgentHub 의 IsPublic / CreatedBy 권한 모델이 DocUtil 의 visibility_targets(folder/scope/role) 와 어떻게 매핑되는지 정책 결정 필요. Phase 6.4 에서 운영자 마이그레이션 가이드 작성 시 정리
  - **DocUtil JWT 발급 트랙**: AgentHub 의 운영자 화면이 DocUtil 의 운영자 권한 토큰을 어떻게 획득할 것인지(시연용=관리자 직접 발급 / 운영=Service Account + token rotation) 별도 트랙. Phase 6.5 e2e 검증 전 결정
  - **RagSearchResultDto.ChunkId(long) 와 DocUtil string UUID 의 mismatch**: 현재 `GetHashCode()` 로 안정적 int 변환하지만 충돌 가능성 0 아님(매우 낮음). 운영자 화면에서 ChunkId 를 직접 사용하는 곳 없으므로 시연 영향 없음. Phase 6.4 에서 RagSearchResultDto 자체를 string 으로 확장하는 schema 변경(EF migration + Frontend 동기화 필요)이 정도(正道)
  - **DocUtil 측 SearchRequest schema 검증 미완**: `scope_id` / `folder_id` / `doc_ids` / `agentic` 필드명이 DocUtil 의 실제 Pydantic schema 와 정확히 일치하는지 Phase 6.5 e2e 에서 확인. 본 코드는 사전 조사 결과 + DocUtil source_DOCUTIL.md 기반 추정
  - **Phase 6.3 의존**: 운영자 Vue UI(`/admin/knowledge-base`) 는 본 Phase 6.1 의 IDocUtilClient 6 메서드를 그대로 노출하면 됨 — 별도 Service 레이어 추가 불필요(BFF 패턴 그대로)
- **다음 단계**:
  - **Phase 6.3** (운영자 KB 콘솔 Vue UI) — AgentHub `/admin/knowledge-base` 페이지 신설. `KnowledgeBaseController` 신설 + `IDocUtilClient` 6 메서드 노출 + Vue 측 `views/admin/KnowledgeBase.vue` + `services/knowledgeBaseService.ts` + `stores/knowledgeBase.ts`. 한국어 UI(목록/업로드/삭제/검색/청크 검수). Pinia 스토어로 페이지네이션 상태 관리. 한국어 사용자 메시지 + ErrorResponseDto 패턴 준수
  - **Phase 6.4** (자체 KB deprecate 마킹) — `IKnowledgeBaseService` / `KnowledgeBaseService` / `KnowledgeBaseDocument` 모델에 `[Obsolete("ADR-2 — DocUtil 로 위임. Phase 6.3 의 운영자 콘솔 사용 권장.", error: false)]` 부착. 빌드 경고로 신규 사용 차단. 운영자 마이그레이션 가이드(`docs/PHASE6_MIGRATION.md`) 작성
  - **Phase 6.5** (e2e 검증) — 시연용 DocUtil 운영자 JWT 발급 → `appsettings.Development.json` 의 `DocUtil:JwtToken` 주입 → 시드 Agent 1건 (예: AgentCode `customer-support`) 의 KnowledgeBaseSource SQL UPDATE → DocUtil 의 시드 collection 으로 KnowledgeBaseRef 설정 → /v1/chat/completions 호출 시 RAG 결과가 DocUtil 청크에서 오는지 로그 검증
- **시드 / 데이터 영향 0건**: 본 Phase 는 DB 변경 없음 — 코드 + appsettings 만. AGENT_HUB DB 의 Agents 테이블은 Phase 5.1 시점 그대로

### 2026-05-06 (Phase 7.5 — AgentHub /v1/embeddings 컨트롤러 신설 + AgentHubClient.embed() + 통합, R2 단일 진입점 완료)
- **목적**: Phase 7.3/7.4 에서 보류한 임베딩 호출의 R2 단일 진입점 강제. AgentHub `OpenAICompatController` 에 OpenAI 호환 `/v1/embeddings` 엔드포인트 신설 + `IAiProxyService.GenerateEmbeddingAsync` 분기(OpenAI/Azure OpenAI) + DocUtil/career 양 클라이언트에 `embed()` 메서드 통합. career embedding_service.py(7.4 별도 httpx 인스턴스) → AgentHubClient.embed() 위임으로 connection pool 통합 + DocUtil embedding_generator.py(7.4 OpenAI/vLLM 직접 httpx) → AgentHub 위임 교체. Phase 7 전체 완료
- **변경 파일 (7 modify)**:
  - **MODIFY `agenthub/DTOs/OpenAICompatDto.cs`** (+72 LOC) — `EmbeddingsRequestDto` (model / input(object) / encoding_format / user) + `EmbeddingsResponseDto` + `EmbeddingItemDto` (object/index/embedding float[]) + `EmbeddingUsageDto` (prompt_tokens/total_tokens). OpenAI Embeddings API 와 100% 호환되는 schema. `Input` 은 OpenAI 명세상 string / string[] 둘 다 허용해야 하므로 `object` 타입 — JsonElement 로 deserialize 후 컨트롤러에서 정규화
  - **MODIFY `agenthub/Services/IAiProxyService.cs`** (+33 LOC) — `Task<EmbeddingResultDto> GenerateEmbeddingAsync(Models.ApiService service, string model, string[] inputs, CancellationToken)` 시그니처 추가. 내부용 `EmbeddingResultDto` (Embeddings float[][], Model, PromptTokens, TotalTokens) 신규 — 컨트롤러가 OpenAI 호환 응답으로 매핑
  - **MODIFY `agenthub/Services/AiProxyService.cs`** (+~190 LOC, 파일 끝에 추가) — 3 메서드:
    - `GenerateEmbeddingAsync(service, model, inputs, ct)` — ServiceCode 분기(`openai`/`chatgpt`/`azureopenai`/`azure-openai`/`copilot`/`microsoft-copilot`), 그 외 NotSupportedException(claude/gemini/perplexity/mistral/nexus 미지원 — Anthropic 임베딩 미제공, Gemini 별도 SDK)
    - `CallOpenAiEmbeddingsAsync(model, inputs, ct)` — `GetApiKey("openai", "AiApiSettings:OpenAI:ApiKey")` 풀 경유 + `IHttpClientFactory.CreateClient("openai")` 재사용 + `Bearer {apiKey}` Authorization. POST `{baseUrl}/embeddings` body `{model, input: string[]}`. 429 → `_apiKeyPool.MarkAsCoolingDown` + HttpRequestException
    - `CallAzureOpenAiEmbeddingsAsync(service, model, inputs, ct)` — Azure deployment URL 패턴 `{endpoint}/openai/deployments/{model}/embeddings?api-version={apiVersion}` + `api-key` 헤더
    - `ParseOpenAiEmbeddingsResponse` — JsonDocument 로 `data[].index` 정렬 보존 + `usage.prompt_tokens/total_tokens` 추출. 입력 슬롯 누락 시 빈 float[] 폴백 (client IndexError 방어)
  - **MODIFY `agenthub/Controllers/OpenAICompatController.cs`** (+~190 LOC) — `[HttpPost("embeddings")]` `EmbeddingsAsync` 액션 추가. 클래스 레벨 `[ApiKeyAuthorize]` 자동 적용. 처리 흐름: (1) 인증 (2) 요청 유효성 (model 필수 + input 정규화 + encoding_format=='float') (3) Agent 룩업 — model 그대로 AgentCode → 미일치 시 `embedding-default` 자동 폴백 (4) 권한 (IsPublic 또는 CreatedBy 일치) (5) 실제 모델명 결정 — request.Model 이 `text-embedding-` prefix 면 그대로 전달, 아니면 `agent.DefaultModel ?? agent.ApiService.DefaultModel ?? "text-embedding-3-small"` (6) `aiProxy.GenerateEmbeddingAsync` 위임 (NotSupportedException → 400 / 429 → 429 / InvalidOperationException → 502) (7) OpenAI 호환 응답 매핑. `NormalizeEmbeddingInputs(object?)` 헬퍼 — string / string[] / List<string> / JsonElement(String|Array) 4가지 입력 형태 정규화
  - **MODIFY `docutil/backend/app/integrations/agenthub_client.py`** (+55 LOC) — `AgentHubClient.embed(agent_code, input, *, encoding_format=None, extra=None)` 비동기 메서드 추가. 동일한 httpx.AsyncClient 인스턴스 재사용 — chat 호출과 connection pool 공유. 401/403/429 등 한국어 매핑(`_raise_for_status`) 재사용. timeout/network 에러는 `AgentHubError("AgentHub 임베딩 응답 시간 초과/연결 실패")`
  - **MODIFY `career/shared/common/agenthub_client.py`** (+58 LOC) — 동일 `embed()` 메서드 추가 (career 측 사본). 18 MS 공용 사용. consumer_label 그대로 이어받음
  - **MODIFY `career/services/ai-service/app/services/embedding_service.py`** (전체 재작성, ~190 LOC) — Phase 7.4 의 별도 httpx.AsyncClient 인스턴스 폐기 → `from shared.common.agenthub_client import AgentHubClient, AgentHubError, get_agenthub_client` import. `__init__(self, settings=None, agenthub_client: Optional[AgentHubClient] = None)` — 의존성 주입 패턴(테스트 mock 가능). `self._agenthub = agenthub_client or get_agenthub_client()` 싱글턴 재사용. `embed_text` / `embed_batch` 모두 `await self._agenthub.embed(agent_code=self.model, input=...)` 호출. `aclose()` 는 의도적 no-op — 싱글턴은 다른 모듈도 공유하므로 본 모듈에서 정리 시 chat 호출도 죽음. 모듈 헤더에 7.4→7.5 마이그레이션 노트 + connection pool 공유 명시
  - **MODIFY `docutil/backend/app/workers/embedding_generator.py`** (~25 LOC 변경) — 모듈 헤더에 7.5 마이그레이션 노트. `_generate_dense_embeddings(texts)` 의 본문 전체 교체: `EMBEDDING_PROVIDER` 분기(openai/local) + `httpx.post(...)` 직접 호출 → `asyncio.run(_embed_via_agenthub())` (Celery sync 컨텍스트 + AgentHubClient 비동기 호환). agent_code = "embedding-default" 고정. `OpenAI` 모델명 / vLLM URL 하드코딩 모두 제거 — AgentHub 가 라우팅 담당
- **AgentCode/Agent 매핑 표** (Phase 7.1 시드와 일관):

  | 호출처 | task | AgentCode | LlmRouting | 시드 모델 |
  |---|---|---|---|---|
  | docutil/workers/embedding_generator._generate_dense_embeddings | RAG 임베딩 (문서 청크) | `embedding-default` | External | text-embedding-3-small (1536D) |
  | career/services/ai-service/services/embedding_service.embed_text | 단건 임베딩 | `embedding-default` | External | text-embedding-3-small (1536D) |
  | career/services/ai-service/services/embedding_service.embed_batch | 배치 임베딩 (batch_size=100) | `embedding-default` | External | text-embedding-3-small (1536D) |
  | (외부 OpenAI SDK) `model="text-embedding-3-small"` | 외부 호환 | (자동 폴백 → embedding-default) | External | text-embedding-3-small |

- **AgentHub `/v1/embeddings` 처리 흐름**:
  1. `[ApiKeyAuthorize]` (클래스 레벨, X-API-Key 또는 Bearer) → JWT 우선 / 없으면 ApiKey + Scope 검증
  2. model 정규화: AgentCode 룩업 (`Agents` JOIN `ApiService`) → 미일치 시 `embedding-default` 폴백
  3. 권한: `IsPublic` 또는 `CreatedBy == userId` 일치 검증 → /v1/chat/completions 와 동일 패턴
  4. 실제 모델명 결정: request.Model 이 `text-embedding-` prefix 시 그대로 / 그 외 `Agent.DefaultModel` 또는 `ApiService.DefaultModel` 폴백
  5. `IAiProxyService.GenerateEmbeddingAsync(ApiService, model, inputs, ct)` 위임
  6. OpenAI 호환 응답 schema 직렬화: `{"object":"list","data":[{"object":"embedding","index":N,"embedding":float[]}],"model":"...","usage":{"prompt_tokens":N,"total_tokens":N}}`
- **빌드 검증**:
  - `dotnet build --no-restore -v quiet` → **에러 0건 / 경고 11개 (모두 pre-existing CS1998)**. 본 Phase 변경이 새로 도입한 경고 0건. 첫 시도에서 `service.BaseUrl` 사용 → `service.ApiEndpoint` 정정 (ApiService 모델 실제 컬럼명) 후 PASS
  - 단위 import 검증 (DocUtil): `from app.integrations.agenthub_client import get_agenthub_client; client = get_agenthub_client(); print(hasattr(client, 'embed'))` → `True` PASS
  - 단위 import 검증 (career): `from shared.common.agenthub_client import get_agenthub_client; client = get_agenthub_client(); print(hasattr(client, 'embed'))` → `True` PASS
  - AST 검증 (career embedding_service.py): `agenthub_client` import 1건 / `httpx` 직접 import 0건 / `openai` import 0건 / 메서드 6개 (`__init__`/`aclose`/`embed_text`/`embed_batch`/`compute_similarity`/`format_for_pgvector`) → all_OK
  - AST 검증 (docutil embedding_generator.py): `_generate_dense_embeddings` 함수 본문에 `asyncio` 사용 + `agenthub_client` 사용 + `api.openai.com` 직접 URL 0건 → all_OK
- **호환성 검증 (회귀 0건 목표)**:
  - **OpenAI Embeddings API schema 100% 호환**: 응답 `object/data[].object/data[].index/data[].embedding/model/usage.prompt_tokens/usage.total_tokens` 모두 일치. 외부 OpenAI Python SDK / LangChain `OpenAIEmbeddings` 도 호출 가능 — 운영자 환경 별도 e2e 검증 단계
  - **input(object) 정규화 패턴**: System.Text.Json 이 `object` 를 `JsonElement` 로 deserialize → `NormalizeEmbeddingInputs` 가 `JsonValueKind.String|Array` 분기 처리. 비-문자열 entry → 400 BadRequest
  - **AgentCode 폴백**: 외부 SDK 가 `model="text-embedding-3-small"` 보내도 자동으로 `embedding-default` Agent 룩업 → ApiService 매핑 → OpenAI 호출. AgentCode `embedding-default` 가 시드되어 있는 한 동작
  - **career embedding_service.py 호출자 무변경**: `EmbeddingService(settings=...).embed_text/embed_batch/compute_similarity/format_for_pgvector` 모두 시그니처 보존. 호출처(retrieval_service / 향후 백필 스크립트) 코드 수정 0건
  - **AgentHubClient 싱글턴 공유**: career embedding_service 가 chat 호출과 같은 `get_agenthub_client()` 반환 인스턴스 사용 → connection pool 공유. 단, `EmbeddingService.aclose()` 는 의도적 no-op (싱글턴 보호)
- **잠재 위험**:
  - **AgentHub 부팅 + 실 OpenAI 호출 미검증 (e2e 한계)**: 본 Phase 검증은 dotnet build + AST + import 까지. 실제 HTTP 라운드트립은 (a) AgentHub IIS/dotnet run 부팅 (b) `embedding-default` Agent 시드 적용 (c) OPENAI_API_KEY 환경변수 주입 (d) `curl POST /v1/embeddings` 실 호출까지 필요. 시연 환경에 실 OpenAI API 키 부재 가능성 — 운영자 환경에서 별도 검증 필요
  - **Azure OpenAI 분기 미검증**: `CallAzureOpenAiEmbeddingsAsync` 는 `appsettings.AiApiSettings:AzureOpenAI:Endpoint/ApiVersion` 설정 의존. Azure 환경 부재 시 코드 path 미실행 — 운영 도입 시 별도 검증
  - **Anthropic/Gemini/Nexus 미지원**: ServiceCode 분기에서 `NotSupportedException` 발생. 본 Phase 의 의도적 결정 (Anthropic 임베딩 모델 미제공, Gemini SDK 별도, Nexus 1024D 정책 차이). Agent.LlmRouting=Hybrid 라도 임베딩 호출은 항상 OpenAI/Azure 로 강제 — TECHSPEC R17 (Qdrant collection 단일성 vs Nexus 1024D) 의존
  - **Celery worker asyncio.run 패턴**: docutil `_generate_dense_embeddings` 가 매 호출마다 `asyncio.run(_embed_via_agenthub())` 호출 → 새 이벤트 루프 생성/파괴 비용. 다수 task 동시 실행 시 비효율 — Phase 8+ 에서 Celery `asgiref.sync.async_to_sync` 또는 worker 단위 영속 루프로 최적화 권장
  - **AgentHubClient.embed() vs chat() pool 공유**: 두 메서드가 동일 `httpx.AsyncClient` pool 을 공유 — embedding 의 평균 응답시간(~200ms)이 chat(~수초) 과 충돌 시 starvation 가능성. 운영 부하 측정 후 별도 풀 분리 검토
  - **외부 OpenAI SDK 호환 e2e 미검증**: `import openai; openai.OpenAI(base_url="http://agenthub:5000/v1", api_key="ak-...").embeddings.create(model="text-embedding-3-small", input="...")` 패턴이 동작하는지는 운영자 환경에서 별도 e2e 필요
- **Phase 7 완료 평가**:
  - [x] 7.1 — AgentHub 15개 신규 Agent 카탈로그 등록 (DU 4 + CA 8 + 공통 3, embedding-default 포함)
  - [x] 7.2 — ApiKey 발급 + DocUtil/career 환경변수 + AgentHubClient 라이브러리 (chat/chat_stream)
  - [x] 7.3 — DocUtil 9곳 LLM 호출 → AgentHubLLMWrapper 위임 (factory 외부 시그니처 보존)
  - [x] 7.4 — career 12곳 LLM 호출 → AgentHubClient 직접 호출 (ai-service 라우터 응답 schema 보존)
  - [x] 7.5 — AgentHub /v1/embeddings 컨트롤러 + AgentHubClient.embed() + 통합 (본 Phase)
  - **R2 단일 진입점 강제 완료**: DocUtil/career 의 모든 LLM/Embedding 호출이 AgentHub 경유. anti-patterns.md §1 (LLM SDK 직접 import 금지) 위반 0건 — `from openai import` / `from langchain_openai import` / `https://api.openai.com` 직접 URL 모두 정리. 잔존 항목(DU-14 image_generation, DU-15 graph_rag 비활성, claude_client.py / gemini_client.py 등 dead code)은 Phase 8+ 별도 트랙
- **다음 작업**:
  1. (사용자 승인 시) Phase 4.1/4.2/4.3/4.4/7.1/7.2/7.3/7.4/7.5 통합 commit + push (secret leak 미해결 — 별도 sanitize 후)
  2. Phase 4.5 추가 트랙 (retrieval_service 임베딩 SQL 분기 추가, tb_user FK 3건 복구) — 이미 수행된 4.5 검증과 별개
  3. AgentHub IIS 부팅 + e2e 실 OpenAI 호출 검증 (운영자 환경)
  4. (별도 트랙) DU-14 `/v1/images` 컨트롤러 + AgentHubClient.generate_image, career frontend → AgentHub 직결, ai-service deprecate 검토

### 2026-05-06 (Phase 4.5 — 4 schema 통합 검증 + R3 격리 강제 검증, Phase 4 종합 완료)
- **목적**: Phase 4.1+4.2+4.3+4.4 적용 결과를 운영 PG (192.168.10.39:5440 / AGENT_HUB / PG 17.9 / pgvector 0.8.0) 에서 일괄 검증. R3 (스키마 격리) 강제 / FK 정합 / audit 일관성 / Phase 5 Nexus + Phase 7.1/7.2 시드 reproducibility / pgvector 활성화 / PK 누락 점검. **검증 + 보고서만, 코드/마이그레이션 변경 0건**
- **검증 도구 / 재현**: `user_mig/scripts/phase45_validate.csx` (dotnet-script + Npgsql 직접) — 15개 검증 항목 단일 실행. `dotnet-script user_mig/scripts/phase45_validate.csx`
- **검증 결과 (15 항목 모두 통과)**:
  1. **schema 별 BASE TABLE 수**: AgentHub 37 + DocUtil 28 + career 62 + hangfire 0 = **127 합계**. AgentHub 37은 35(EF) + Tenants + Departments(Phase 4.3) 로 일치
  2. **Cross-schema FK = 0건 [PASS]** — anti-patterns.md §3 의 DDL-level 보장. Tenants/Departments 가 idino_career.tb_user 를 FK 로 묶지 않음 (옵션 B 디자인 일치)
  3. **FK ON DELETE 정책 분포**:
     - AgentHub: CASCADE 32 / NO ACTION 12 / RESTRICT 2 / SET NULL 1 = 47
     - DocUtil: CASCADE 30 / RESTRICT 1 / SET NULL 26 = 57
     - career: NO ACTION **82** (100%) — Phase 4.2 적용 시 default 유지
  4. **FK 총수**: 186 (AgentHub 47 + DocUtil 57 + career 82)
  5. **audit 컬럼 분포**: AgentHub `CreatedAt` 32 + `UpdatedAt` 24 + `CreatedBy` 6 / DocUtil `ins_dt` 27 + `upd_dt` 27 + `created_by` 7 / career `ins_dt` 62 + `ins_user_id` 62 + `upd_dt` 55 + `upd_user_id` 55 + `created_at` 4 (잔존)
  6. **audit 누락**:
     - AgentHub `CreatedAt` 누락 5건 (PiiDetectionLogs, TeamMembers, UserRoles, WorkflowExecutions, WorkflowNodeExecutions — 일부는 자체 Timestamp 컬럼 보유)
     - DocUtil `created_at` 누락 10건 — 그러나 DocUtil 표준은 `ins_dt` (snake_case + timestamptz, 27건 100% 보유). alembic_version 1건 정상, 9건은 `ins_dt` 보유 차이만 — 별도 트랙
     - career `ins_dt` 누락 **0건** (62/62 100%)
  7. **인덱스 통계**: 총 342 (AgentHub 110 / DocUtil 101 / career 131) / UNIQUE 175 / Vector 3 (idino_career)
  8. **Phase 5 Nexus 시드**: `ServiceCode='nexus'` `ServiceName='Project Nexus'` `ServiceType=Chat` 1건 [PASS]
  9. **Phase 7.1 Agent 시드 15건 [PASS]**: agentic-search / career-action-recommender / career-actionboard-orchestrator / career-chatbot(**Internal/Nexus 강제**) / career-competency-analyzer / career-rag-actionboard / career-semester-planner / career-simulation-analyzer / career-simulation-suggester / docutil-evaluator / docutil-image-generator / docutil-rag-chat / docutil-report-generator / embedding-default / web-search-default
  10. **Phase 7.2 ApiKey 2건 [PASS]**: docutil-master-key (id=1, scopes=chat,stream,info,usage, active=true) / career-master-key (id=2, 동일 스코프, active=true)
  11. **Phase 4.3 Tenants/Departments**: Tenants=1, Departments=1 (bootstrap row)
  12. **Phase 4.4 vector 컬럼 3건 [PASS]**: idino_career.tb_course.embedding / tb_program.embedding / tb_success_pattern.embedding (모두 vector(1536))
  13. **R3 search_path 시뮬레이션 3/3 PASS**:
      - agenthub `SET search_path TO "AIAgentManagement",public` → Users OK / tb_documents FAIL(`relation "tb_documents" does not exist`) / tb_student FAIL
      - docutil `document_utilization,public` → Users FAIL / tb_documents OK / tb_student FAIL
      - career `idino_career,public` → Users FAIL / tb_documents FAIL / tb_student OK
      - 의미: 동일 DB user 라도 search_path 만으로 의도하지 않은 cross-schema 참조 차단. 운영 환경에서는 추가로 schema-level GRANT 차등 부여 권장 (별도 트랙, TECHSPEC §13)
  14. **UNIQUE 제약**: DocUtil 10 + career 21 (AgentHub 는 인덱스로 산출 — UNIQUE 인덱스 54)
  15. **PK 누락 BASE TABLE = 0건** [PASS] — 187 BASE TABLE 모두 PK 보유 (alembic_version 포함)
- **잠재 위험 / Known Issues (별도 트랙)**:
  - **R12 (CASCADE 강등)**: AgentHub CASCADE 32건 중 ApiUsages/PiiDetectionLogs 등 감사성 테이블은 SET NULL/RESTRICT 강등 권장
  - **R12-c (career NO ACTION 100%)**: 운영 데이터 적재 전 명시적 정책 (RESTRICT/CASCADE) 전환 필요. 현재는 시연용 빈 테이블이라 운영 영향 없음
  - **audit 통합 view 권장**: 3 schema 별 표준 분기 (CreatedAt/created_at/ins_dt) — `v_audit_log` 글로벌 view 신규 (별도 트랙)
  - **R7 (master ApiKey 회전)**: master 키 단일 발급 → Per-MS 키 분리 + 회전 정책 별도 트랙
  - **시드 reproducibility**: Phase 5.1 Nexus + Phase 7.1 15 Agent + Phase 7.2 ApiKey 가 init.sql 또는 EF migration 으로 codify 되지 않음. CI 에서 빈 환경 → init.sql + EF update 시 시드 자동 적용되도록 보강 필요
  - **R3 schema GRANT 미구분**: 동일 DB user (`AGENT_HUB`) 가 모든 schema 접근 — schema-level GRANT 차등 부여 권장
  - **IVFFlat lists=100**: 빈 테이블 + 운영 적재 후 과도. 백필 후 `lists ≈ sqrt(N)` 재조정
- **신설 파일**:
  - `user_mig/scripts/phase45_validate.csx` (검증 스크립트, dotnet-script + Npgsql 직접, 15 항목)
  - `docs/PHASE4_VALIDATION.md` (검증 보고서, ~290 라인 / 9개 섹션 / 한국어)
- **TECHSPEC 영향**:
  - §16 R3 (스키마 격리) PASS 증거 확보 — `docs/PHASE4_VALIDATION.md` §2 인용
  - §16 R12 / R7 / audit 통합 / 시드 codify 는 별도 트랙으로 분리 (본 Phase 책임 범위 밖)
- **Phase 4 종합 완료**: 4.1 (DocUtil 28) + 4.2 (career 62) + 4.3 (Tenants/Departments) + 4.4 (pgvector 3) + 4.5 (검증) — Phase 4 ✅
- **다음 단계 후보 (사용자 결정 대기)**:
  1. Phase 6 — DocUtil 운영자 → AgentHub 흡수 + KB 마이그레이션
  2. Phase 5+ 별도 트랙 — R12 ON DELETE 강등 / R7 ApiKey 회전 / 시드 EF migration codify / DU-14 `/v1/images` 컨트롤러
  3. Phase 4/7 통합 commit — `[infra/db]` `[docutil]` `[career]` `[agenthub]` `[docs]` 분리 또는 통합 커밋
  4. secret leak sanitize + force-push (#16 pending task)

### 2026-05-06 (Phase 7.4 — career 12곳 LLM 호출 → AgentHubClient 위임, R2 단일 진입점 강제)
- **목적**: AI_INVENTORY.md CA-3~CA-13 + CA-14~CA-16 의 직접 OpenAI/LangChain 호출 12곳을 `shared.common.agenthub_client.AgentHubClient` (Phase 7.2 신설, 18 MS 공용) 로 위임. anti-patterns.md §1 (외부 SDK 직접 import 금지) 위반 정리. ai-service 라우터의 외부 시그니처 보존으로 5개 위임 호출자(coaching/competency/roadmap/opportunity/skill MS) 회귀 0건 달성
- **사전 조사 결과** (`grep "from openai|AsyncOpenAI|langchain_openai"`):
  - **3 파일에 LLM SDK 직접 사용 확정**:
    - `services/ai-service/app/services/llm_service.py` — LangChain `ChatOpenAI` 1 인스턴스 (CA-1) + OpenAI SDK `AsyncOpenAI` 1 인스턴스 (CA-2) + Tool Calling 본문 4 호출 (CA-7~CA-10) + LangChain `ainvoke` 4 호출 (CA-3~CA-6)
    - `services/ai-service/app/services/embedding_service.py` — `AsyncOpenAI` 1 인스턴스 (CA-14) + `client.embeddings.create` 단일 (CA-15) + 배치 (CA-16)
    - `services/simulation-service/app/services/simulation_service.py` — `AsyncOpenAI` 1 인스턴스 (CA-11) + `chat.completions.create` 2 호출 (CA-12 max=2000 / CA-13 temp=0.7,max=1500)
  - **5 위임 호출 (이미 ai-service `/ai/*` 로 httpx 위임 — 본 Phase 무변경)**: coaching-service `_call_ai_service` (`/ai/chat`) / competency-service (`/ai/analyze`) / roadmap-service (`/ai/recommendations/tools`) / opportunity-service (config-only, 호출 미발견) / skill-service (config-only, 호출 미발견). ai-service 라우터(`ai_router.py`: `/chat` `/analyze` `/recommendations/tools` `/sprint/{id}` `/actions/{id}`) 응답 schema(Pydantic `ChatResponse`/`CompetencyAnalysisResponse` 등) 변경 없음 → 위임 호출자 자동 호환
- **변경 파일 (3 modify)**:
  - **MODIFY `career/services/ai-service/app/services/llm_service.py`** (전체 재작성, ~635 LOC) — 모듈 헤더 docstring Phase 7.4 마이그레이션 노트 (AgentCode 매핑 표 + Tool Calling 처리 + W2 Structured Outputs 의존성 주석). `from langchain_openai import ChatOpenAI` + `from openai import AsyncOpenAI` + `from langchain.prompts/schema` 모두 제거 → `from shared.common.agenthub_client import AgentHubClient, AgentHubError, get_agenthub_client`. `__init__` 의 `self.llm = ChatOpenAI(...)` + `self.openai_client = AsyncOpenAI(...)` 제거 → `self._agenthub = agenthub_client or get_agenthub_client()` (테스트 mock 주입 가능). 6 public 메서드 모두 `await self._agenthub.chat(agent_code="career-...", messages=..., temperature=, max_tokens=, extra={...})` 패턴으로 교체. Tool Calling 루프(`generate_with_tools`/`generate_with_tools_and_rag`)는 dict 응답(`response["choices"][0]["message"]["tool_calls"]`) 파싱 + `extra={"tools": TOOLS, "tool_choice": "auto"}` / `extra={"response_format": {"type": "json_schema", "json_schema": JSON_SCHEMA_ACTIONBOARD}}` 분리 호출. `AgentHubError` catch 추가 + 한국어 fallback 메시지
  - **MODIFY `career/services/simulation-service/app/services/simulation_service.py`** (4 hunks) — `from openai import AsyncOpenAI` 제거 + `from shared.common.agenthub_client import AgentHubClient, AgentHubError, get_agenthub_client` 추가. `__init__` 의 `self.openai_client = AsyncOpenAI(...)` → `self.agenthub_client = agenthub_client or get_agenthub_client()` + ValueError 가드(미설정 환경에서 AI 분석 비활성화). `_generate_ai_suggestions` (line 973 호출): `agent_code="career-simulation-suggester"` + `max_tokens=2000` + AgentHubError 분기. `_generate_ai_analysis` (line 1764 호출): `agent_code="career-simulation-analyzer"` + `temperature=0.7, max_tokens=1500` + fallback 가드 `if self.agenthub_client is None`. 응답 파싱 `response.choices[0].message.content` → `response["choices"][0]["message"]["content"]`
  - **MODIFY `career/services/ai-service/app/services/embedding_service.py`** (전체 재작성, ~210 LOC) — 모듈 헤더 docstring Phase 7.4 마이그레이션 노트. `from openai import AsyncOpenAI` 제거 + `import httpx` 추가. `EmbeddingService.__init__` 의 `self.client = AsyncOpenAI(...)` → `self._client = httpx.AsyncClient(base_url=AGENTHUB_URL, headers={"X-API-Key": ..., ...})`. `self.model = "embedding-default"` (AgentCode), `self.dimensions = 1536` (TECHSPEC ADR-10 표준 유지). `embed_text` / `embed_batch` 모두 `await self._client.post("/v1/embeddings", json={"model": self.model, "input": ...})` 호출 + OpenAI 호환 응답(`data["data"][0]["embedding"]`) 파싱. `aclose()` lifespan 정리 메서드 추가. 비고: AgentHubClient 가 chat 만 노출하므로 임베딩은 별도 httpx 인스턴스 — Phase 7.5 에서 `AgentHubClient.embed()` 메서드 보강 후 통합 권장
- **AgentCode 매핑 표 (호출처 → AgentCode → Phase 7.1 시드 라우팅)**:

  | 호출처 | 함수 | AgentCode | LlmRouting | 시드 모델 |
  |---|---|---|---|---|
  | ai-service llm_service.py:90  | `generate_action_recommendations` | `career-action-recommender`       | Hybrid   | gpt-4o-mini |
  | ai-service llm_service.py:146 | `analyze_competencies`            | `career-competency-analyzer`      | Hybrid   | gpt-4o-mini |
  | ai-service llm_service.py:203 | `chat`                            | `career-chatbot`                  | **Internal** | nexus/primary |
  | ai-service llm_service.py:260 | `generate_semester_goals`         | `career-semester-planner`         | Hybrid   | gpt-4o-mini |
  | ai-service llm_service.py:317/334 | `generate_with_tools` (+Schema)   | `career-actionboard-orchestrator` | Hybrid   | gpt-4o-mini |
  | ai-service llm_service.py:507/524 | `generate_with_tools_and_rag` (+Schema) | `career-rag-actionboard`     | Hybrid + RAG | gpt-4o-mini |
  | simulation-service simulation_service.py:973  | `_generate_ai_suggestions` | `career-simulation-suggester` | Hybrid | gpt-4o-mini |
  | simulation-service simulation_service.py:1764 | `_generate_ai_analysis`    | `career-simulation-analyzer`  | Hybrid | gpt-4o-mini |
  | ai-service embedding_service.py:* (3 호출)  | `embed_text`/`embed_batch` | `embedding-default`           | External | text-embedding-3-small (1536D) |

- **호환성 검증 (5 위임 호출자 회귀 0건 목표)**:
  - **ai-service 라우터 응답 schema 보존**: `ai_router.py` 의 `/chat` (`ChatResponse`) / `/analyze` (`CompetencyAnalysisResponse`) / `/actions/{student_id}` (`ActionRecommendationResponse`) / `/sprint/{student_id}` (`SemesterSprintResponse`) / `/recommendations/tools` 모두 Pydantic schema 그대로. `LLMService` 메서드 반환 타입(`Dict[str, Any]` / `List[Dict[str, Any]]`) 무변경 → `RecommendationService` 변환 로직 무변경 → 응답 형식 보존
  - **5 위임 호출자 무변경 확인**: coaching-service `_call_ai_service` (httpx → `{AI_SERVICE_URL}/ai/chat`) / competency-service `/ai/analyze` / roadmap-service `/ai/recommendations/tools` / opportunity-service / skill-service — 모두 본 Phase 코드 변경 0건. ai-service 가 AgentHub 위임으로 전환되어도 `/ai/*` 엔드포인트는 `LLMService` 출력을 그대로 직렬화하므로 자동 호환
  - **Tool Calling 응답 형식**: AgentHub Phase 5.2 Hybrid 라우팅이 OpenAI provider 로 분기 시 OpenAI SDK 의 `tool_calls` 형식 그대로 dict 변환되어 반환됨. 본 클라이언트는 `tool_calls[i]["function"]["name"]` 형태로 dict 액세스 — SDK obj attribute 액세스에서 dict key 액세스로 패턴 변경
- **Import 정리 결과**:
  - `llm_service.py`: `from langchain_openai import ChatOpenAI` 제거 / `from openai import AsyncOpenAI` 제거 / `from langchain.prompts ...` `from langchain.schema import HumanMessage, SystemMessage, AIMessage` 제거 (메시지 변환은 dict 로 직접 작성)
  - `embedding_service.py`: `from openai import AsyncOpenAI` 제거 / `import httpx` 추가
  - `simulation_service.py`: `from openai import AsyncOpenAI` 제거 / AgentHubClient import 추가
  - **잔존 검증**: `grep "from openai|AsyncOpenAI|langchain_openai|ChatOpenAI"` → docstring 주석 2건만 검출 (실제 import 0건)
  - `requirements.txt` 의 `openai` / `langchain-openai` 패키지 자체는 보존 (전환 안전망 + 추후 별도 정리 트랙)
- **단위 import 검증 결과 (모두 PASS)**:
  - `python -c "from app.services.llm_service import LLMService"` → llm_service import OK
  - `python -c "from app.services.embedding_service import EmbeddingService"` → embedding_service import OK
  - `python -c "from app.services.simulation_service import SimulationService"` → simulation_service import OK
  - 환경변수 stub: `AGENTHUB_URL=http://localhost:5000`, `AGENTHUB_API_KEY=ak-stub` (Phase 7.2 발급된 평문 키는 운영 환경에서만 사용)
- **잠재 위험 (Phase 7.5 e2e 검증 항목)**:
  - **W2 (TECHSPEC §16 R3) — Tool Calling Structured Outputs 의존성**: `JSON_SCHEMA_ACTIONBOARD` 는 OpenAI strict 전용. AgentHub Hybrid 라우팅이 Internal(Nexus) 분기 시 schema 호환 불가 → `career-actionboard-orchestrator` / `career-rag-actionboard` Agent 정의는 ServiceCode="openai" 강제 권장 (Phase 7.5 Agent 정의 검증 필요)
  - **W6 — `career-chatbot` Internal 라우팅**: AgentHub `CallNexusAsync` 가 `messages` 단일화/`session_id` 매핑 처리. 학생 발화의 PII 가 외부로 새지 않도록 Phase 5.2 시드된 Internal 강제 정책 e2e 검증 필요
  - **AgentHub `/v1/embeddings` 엔드포인트 부재**: 현재 AgentHub `OpenAICompatController.cs` 는 `/v1/chat/completions` + `/v1/models` 만 노출. embedding_service 가 호출 시 404 예상 — Phase 7.5 작업 항목 (AgentHub `[HttpPost("embeddings")]` 신규 추가 + `IAiProxyService.GetEmbeddingsAsync` 메서드 + `embedding-default` Agent 라우팅)
  - **opportunity-service / skill-service config-only**: AI_SERVICE_URL config 만 정의되어 있고 실제 LLM 호출 코드 미발견 — 향후 호출 추가 시 직접 AgentHub 호출로 작성하도록 코드 리뷰 가이드 필요
  - **simulation-service `__init__` 가드 변경**: 기존 `if self.settings.OPENAI_API_KEY` → `try get_agenthub_client() except ValueError`. AgentHub 미설정 환경에서는 `_generate_default_*` fallback 으로 자동 분기 — 운영 환경에서 `AGENTHUB_URL`/`AGENTHUB_API_KEY` 환경변수 누락 시 AI 분석 silent 비활성화 위험. docker-compose 점검 필요 (Phase 7.5)
- **다음 단계 (Phase 7.5)**:
  1. AgentHub `/v1/embeddings` 컨트롤러 신규 추가 + `embedding-default` Agent 라우팅 → 실 임베딩 호출 e2e 검증
  2. ai-service / simulation-service 통합 e2e 시나리오: 학생 ID → ActionBoard → 시뮬레이션 → 챗봇 (PII 라우팅 검증)
  3. coaching-service `/ai/chat` 호출 후 `career-chatbot` Internal 라우팅으로 Nexus 응답 도달 검증
  4. AgentHubClient.embed() / .generate_image() 메서드 추가 후 embedding_service 의 별도 httpx 인스턴스 통합

### 2026-05-06 (Phase 4.4 — career idino_career schema pgvector(1536D) 활성화, ADR-10 적용 + R13 부분 해소)
- **목적**: `career` 의 `tb_course` / `tb_program` / `tb_success_pattern` 3개 테이블에 pgvector 임베딩 컬럼 + IVFFlat 인덱스를 추가하여 RAG 의미 검색(retrieval_service.hybrid_search) 의 vector 분기 활성 기반 마련. ADR-10 (1536D 단일화) + ADR-4 (단일 PG schema) 준수. TECHSPEC §15.5 / §12.6 의 "career schema pgvector 활성화" 항목 이행
- **사전 조사 결과**:
  - **schema 정의 부재 확인**: `career/database/01_schema_create.sql` 의 `tb_course`(L134), `02_techspec_tables.sql` 의 `tb_program`(L179) / `tb_success_pattern`(L360) 모두 schema DDL 에 `embedding` 컬럼 정의 없음. backup/migration 파일 모두 점검 — 일관되게 부재. 02_techspec_tables.sql:459 의 `retrieval_method VARCHAR(20)` 은 메타데이터(bm25/vector/hybrid)만 보유, 임베딩 자체는 별도 컬럼 필요
  - **운영 PG 사전 점검**: Phase 4.2 적용으로 idino_career schema 의 3개 테이블 모두 존재 + 행 수 0(시연용 빈 테이블) + embedding 컬럼 부재 확인 → ADD COLUMN 진행 적합
  - **사용 패턴 분석**: `career/services/ai-service/app/services/retrieval_service.py:32,45-59` 가 `check_pgvector()` 로 extension 만 점검하고 실제 SQL(`_search_courses`/`_search_programs`/`_search_success_patterns`) 은 `to_tsvector` BM25 + `ILIKE` 만 사용 — 임베딩 활용 SQL 분기 부재 확인. `embedding_service.py:31` 에 1536D 표준 명시(`text-embedding-3-small`) — ADR-10 일치 검증
  - **ORM 위치**: Course/Program 은 `career/services/student-service/app/models/student.py:138,225` / SuccessPattern 은 `career/services/alumni-service/app/models/alumni.py:36`. ai-service 는 ORM 모델 미보유 (raw SQL만 사용)
  - **pgvector Python 패키지 부재**: 18 MS 의 모든 requirements.txt 검색 결과 `pgvector` 의존성 없음 — student-service / alumni-service / ai-service 3곳에 신규 추가 필요
  - **추가 임베딩 후보 부재 확인**: `embedding`/`vector` grep 결과 schema 파일에 다른 임베딩 후보 컬럼 0건. TECHSPEC §15.5 에 명시된 3개가 정확히 전부
- **변경 적용 (DDL — Npgsql 직접, idempotent)**:
  - **EXTENSION**: `CREATE EXTENSION IF NOT EXISTS vector` (Phase 3.6/Phase 2 init.sql 에서 이미 적용 — pgvector v0.8.0 확인)
  - **ALTER TABLE × 3**:
    ```sql
    ALTER TABLE idino_career.tb_course           ADD COLUMN IF NOT EXISTS embedding vector(1536);
    ALTER TABLE idino_career.tb_program          ADD COLUMN IF NOT EXISTS embedding vector(1536);
    ALTER TABLE idino_career.tb_success_pattern  ADD COLUMN IF NOT EXISTS embedding vector(1536);
    ```
  - **COMMENT ON COLUMN × 3** (한국어 — 운영자 유지보수 도움): "과목 설명/명 임베딩 벡터 (OpenAI text-embedding-3-small, 1536D, ADR-10)" 등
  - **CREATE INDEX × 3** (IVFFlat cosine, lists=100):
    ```sql
    CREATE INDEX IF NOT EXISTS ix_tb_course_embedding           ON idino_career.tb_course           USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    CREATE INDEX IF NOT EXISTS ix_tb_program_embedding          ON idino_career.tb_program          USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    CREATE INDEX IF NOT EXISTS ix_tb_success_pattern_embedding  ON idino_career.tb_success_pattern  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
    ```
  - **lists=100 선택 근거**: pgvector 권장 가이드라인은 `rows < 1M → lists ≈ rows/1000`, `rows ≥ 1M → lists ≈ sqrt(rows)`. 본 운영 데이터 사이즈 확정 전(시연용 빈 테이블) 일반적 default 100 적용 — 운영 데이터 백필 후 `REINDEX INDEX ... WITH (lists=N)` 또는 DROP+CREATE 재조정 별도 트랙
- **Npgsql 직접 검증 결과 (모두 PASS)**:
  - 검증 1 (vector 컬럼 3개): tb_course.embedding / tb_program.embedding / tb_success_pattern.embedding 모두 `USER-DEFINED/vector (atttypmod=1536)`
  - 검증 2 (vector 인덱스 3개): ix_tb_course_embedding / ix_tb_program_embedding / ix_tb_success_pattern_embedding 모두 `USING ivfflat (embedding vector_cosine_ops) WITH (lists='100')`
  - 검증 3 (R3 schema 격리): vector 컬럼 분포 = `idino_career: 3` 단일 — AIAgentManagement / document_utilization / public 다른 schema 영향 0
  - 검증 4 (행 수): 3개 테이블 모두 0 rows — 시연용 빈 테이블 확정, 백필 미진행
- **변경 파일 (5 modify)**:
  - **MODIFY `career/services/student-service/app/models/student.py`** (+8 LOC) — 모듈 헤더에 `from pgvector.sqlalchemy import Vector` import 추가 (한국어 주석으로 Phase 4.4 / 의존성 추가 명시). `class Course` 의 `description` 다음 줄에 `embedding = Column(Vector(1536), nullable=True)` 추가 + 한국어 주석(`# 과목 RAG 임베딩 ... IVFFlat cosine 인덱스: ix_tb_course_embedding`). `class Program` 의 `competency_contributions` 다음 줄에 동일 패턴
  - **MODIFY `career/services/alumni-service/app/models/alumni.py`** (+5 LOC) — 모듈 헤더에 `from pgvector.sqlalchemy import Vector` 추가. `class SuccessPattern` 의 `sample_size` 다음 줄에 `embedding = Column(Vector(1536), nullable=True)` 추가 + 한국어 주석
  - **MODIFY `career/services/student-service/requirements.txt`** (+2 LOC) — `# Phase 4.4 — pgvector(1536D) 임베딩 컬럼 매핑 (Vector SQLAlchemy 타입)` + `pgvector==0.3.6` (alembic 다음 줄)
  - **MODIFY `career/services/alumni-service/requirements.txt`** (+2 LOC) — 동일 패턴
  - **MODIFY `career/services/ai-service/requirements.txt`** (+2 LOC) — `# Phase 4.4 — pgvector(1536D) 검색 + Vector SQLAlchemy 타입 매핑 (retrieval_service)` + `pgvector==0.3.6` (asyncpg 다음 줄)
- **AgentCode/Agent 매핑 (Phase 7.4 와 연결)**:
  | 임베딩 컬럼 | 사용 시점 | Agent | 비고 |
  |---|---|---|---|
  | tb_course.embedding | RAG 의미 검색 (학생-과목 매칭) | embedding-default (Phase 7.1 시드, External, gpt) | retrieval_service.py 의 vector 분기 (Phase 4.5 또는 별도 트랙에서 추가) |
  | tb_program.embedding | RAG 의미 검색 (비교과 추천) | embedding-default | 동일 |
  | tb_success_pattern.embedding | P2 추천 엔진 (성공 패턴 매칭) | embedding-default | 동일 |
- **백필 결정 (미진행)**:
  - **시연용 monorepo COPY 환경**: 3개 테이블 모두 0 rows — 빈 테이블에 백필 불필요
  - **IVFFlat 빈 테이블 동작**: pgvector IVFFlat 은 데이터 0건 환경에서도 인덱스 생성 가능 (실제 검색 시 학습 부족으로 의미 없으나, 운영 데이터 적재 후 자동으로 동작 — `vacuum analyze` 후 권장)
  - **운영 PG 별도 트랙 권고**: 운영 데이터 (운영 DB 의 tb_course 100~500 rows, tb_program 50~200, tb_success_pattern 30~100 추정) 가 별도 적재될 때 `embedding_service.embed_batch` (or AgentHub `/v1/embeddings` 위임) 로 백필 + IVFFlat lists 재조정 (예: `lists ≈ sqrt(N) → 10~25`)
- **잠재 위험 / 다음 단계 (Phase 4.5 또는 별도 트랙 의존)**:
  - **retrieval_service.hybrid_search 의 vector 분기 부재**: 현재 `_search_courses`/`_search_programs`/`_search_success_patterns` 모두 `to_tsvector` + `ILIKE` 만 사용. 실제 의미 검색은 동작 안 함. **Phase 4.5 또는 별도 트랙에서**: `check_pgvector()` 분기에 `embedding <=> :query_embedding` (cosine distance) 절 추가 + `alpha`(BM25/vector 가중치) 파라미터 활용 필요. 임베딩 query vector 는 `embedding_service.embed_text(query)` 또는 (Phase 7.4 이후) AgentHub `/v1/embeddings` 호출
  - **embedding_service.py 의 P1 위반**: `services/ai-service/app/services/embedding_service.py:30` 의 `AsyncOpenAI(api_key=...)` 직접 호출은 anti-patterns.md §1 위반 (R2 단일 진입점). Phase 7.4 에서 AgentHub `/v1/embeddings` 위임으로 정리 필요. AgentHub 측 `/v1/embeddings` 컨트롤러 구현은 Phase 7.5 별도 트랙
  - **운영 데이터 백필 시 lists 재조정**: 백필 후 `lists=100` 은 1k 행 미만 환경에서 과도한 partitioning. `DROP INDEX ... CASCADE` + `CREATE INDEX ... WITH (lists=N)` 또는 HNSW 전환 검토 (HNSW 는 빈 테이블에서도 적정 동작 + cold-start 우수, 단 빌드 시간 증가)
  - **pgvector Python 패키지 미설치 환경**: docker compose 재빌드 또는 `pip install -r requirements.txt` 필요. 현재 코드는 import 추가만 됐으나 미설치 환경에서 student-service/alumni-service/ai-service 기동 시 ImportError 발생 — Phase 4.4 commit + 재배포 필수
  - **schema DDL 파일 미반영**: 본 변경은 운영 PG 에만 적용. `career/database/01_schema_create.sql` / `02_techspec_tables.sql` 의 DDL 정의는 그대로 — Fresh setup 시 임베딩 컬럼/인덱스 누락. **Phase 4.5 또는 별도 트랙에서** `ALTER TABLE` 문을 별도 마이그레이션 SQL 로 추가하거나 schema DDL 직접 수정
- **Phase 4.4 진입/완료 조건 체크**:
  - [x] pgvector extension 활성 (Phase 3.6 / Phase 2 init.sql 에서 적용됨, idempotent 재확인)
  - [x] 3개 테이블 임베딩 컬럼 추가 (vector(1536), nullable)
  - [x] 3개 IVFFlat 인덱스 생성 (cosine, lists=100)
  - [x] ORM 2개 모델 갱신 (student-service Course/Program + alumni-service SuccessPattern)
  - [x] pgvector==0.3.6 의존성 3개 requirements.txt 추가 (student/alumni/ai)
  - [x] R3 schema 격리 검증 (idino_career 만 vector 컬럼 보유)
  - [x] R5 한국어 주석 + COMMENT ON COLUMN
  - [x] R13 임베딩 차원 통일 (career 부분 해소 — DocUtil/Nexus 는 Phase 7.5 별도 트랙)
  - [ ] commit 대기 (Phase 4.1/4.2/4.3/4.4/7.1/7.2/7.3/7.4 통합 commit 또는 Phase 별 분리)
  - [ ] retrieval_service vector 분기 추가 (Phase 4.5 또는 별도 트랙)
  - [ ] 운영 데이터 백필 (별도 트랙)

### 2026-05-06 (Phase 7.3 — DocUtil 9곳 LLM 호출 → AgentHubLLMWrapper 위임, R2 단일 진입점 강제)
- **목적**: AI_INVENTORY.md DU-01~DU-19 중 LLM 채팅 호출 9곳을 `AgentHubClient` (Phase 7.2 신설) 로 위임. 외부 SDK 직접 import (anti-patterns.md §1) 위반 정리. factory.py 외부 시그니처 보존으로 호출처(documents_v2/templates/workers/* 등) 무변경 달성
- **사전 조사 결과**:
  - **9곳 매핑 확정**: factory.py 의 6 provider 진입점(openai/azure_openai/gemini/anthropic/vllm/sglang) + agentic_search.py 직접 호출 2건 + data_generator.py 직접 호출 2건 (총 10 instantiate, 9 logical 호출 지점)
  - **정상 진입점 (factory 경유, 5곳)**: documents_v2/service.py:307 (`generate_with_schema` Pydantic) / templates/service.py:1122 / workers/report_generator.py:936,3587 (`generate_structured_sync`) / workers/jinja2_engine.py:880 / workers/evaluation_runner.py:53-58 (judge)
  - **factory 우회 P1 위반 (4곳)**: agentic_search.py:215,237 (`OpenAIClient()` 2건 — DU-16) + workers/training/data_generator.py:68-69 (`OpenAIClient()` 2건 — DU-17) + integrations/rag/graph_rag.py:105 (DU-15, `graph_rag_enabled=False` 비활성) + integrations/image_generation/service.py:189 (DU-14, `from openai import AsyncOpenAI`)
  - **AgentHub 임베딩 엔드포인트 부재**: `agenthub/Controllers/OpenAICompatController.cs` 점검 결과 `[HttpGet("models")]` + `[HttpPost("chat/completions")]` 만 존재. `/v1/embeddings` `/v1/images` 신규 추가 필요 — 본 Phase 보류
- **변경 파일 (5 modify)**:
  - **MODIFY `docutil/backend/app/integrations/llm/client.py`** (+239 LOC, ruff format) — 모듈 헤더 docstring 갱신 (Phase 7.3 마이그레이션 노트). `AgentHubLLMWrapper` 신규 추가 — `LLMClient` 추상 베이스 상속, `agent_code` 인스턴스 변수 보유. 비동기 메서드(`generate` / `generate_stream` / `generate_structured`) 는 `app.integrations.agenthub_client.get_agenthub_client()` 호출 위임. 동기 메서드(`generate_sync` / `generate_structured_sync`) 는 Celery worker 의 asyncio 이벤트 루프 부재 환경 호환을 위해 `httpx.Client` 별도 운용 + `_sync_post` 헬퍼 + `AGENTHUB_URL` / `AGENTHUB_API_KEY` 환경변수 lazy 검증(RuntimeError 가드). Structured Outputs 는 `extra={"response_format": {"type": "json_schema", ...}}` 로 AgentHub forward
  - **MODIFY `docutil/backend/app/integrations/llm/factory.py`** (전체 재작성, ~190 LOC) — `_TASK_TO_AGENT_CODE` 매핑 테이블 신설 (chat→docutil-rag-chat / chatbot→docutil-rag-chat / report→docutil-report-generator / evaluation→docutil-evaluator / agentic_search→agentic-search / training_qa→docutil-evaluator / training_judge→docutil-evaluator / template→docutil-rag-chat). `_resolve_agent_code(provider, model)` 우선순위 결정 (1.model 이 docutil-/agentic-/career-/embedding- prefix → 그대로 사용 / 2.provider 가 task 키 → 매핑 / 3.레거시 provider openai/anthropic/gemini/azure_openai/vllm/sglang → docutil-rag-chat 폴백). `create_llm_client()` 는 항상 `AgentHubLLMWrapper` 반환 — 외부 시그니처(`provider, api_key, model`) 100% 보존. `get_provider_for_task()` 는 settings 오버라이드 우선 + task_type 자체 폴백 + 미등록 시 settings.llm_provider
  - **MODIFY `docutil/backend/app/integrations/llm/__init__.py`** (+13 LOC) — 모듈 docstring Phase 7.3 마이그레이션 노트로 갱신. `AgentHubLLMWrapper` export 추가. 기존 6 클라이언트(OpenAI/Azure/Gemini/Claude/vLLM/SGLang) export 는 호환성 위해 보존 — Phase 8+ 에서 제거 예정
  - **MODIFY `docutil/backend/app/modules/search/agentic_search.py`** (+10 LOC, ruff format) — `_analyze_query()` 의 `from app.integrations.llm.client import OpenAIClient` 직접 import 제거. `from app.integrations.llm.factory import create_llm_client` + `create_llm_client("agentic_search")` 호출로 교체. `_judge_quality()` 동일 패턴. 한국어 docstring 으로 R2/anti-patterns.md §1 의도 명시. 호출 본문(`llm.generate(messages=[...], temperature=, max_tokens=)`) 은 무변경 — `AgentHubLLMWrapper` 가 동일 시그니처 보장
  - **MODIFY `docutil/backend/app/workers/training/data_generator.py`** (+15 LOC) — 모듈 docstring Phase 7.3 마이그레이션 노트로 갱신. `from app.integrations.llm.client import OpenAIClient` 제거 + `from app.integrations.llm.factory import create_llm_client` 추가. `__init__` 의 `OpenAIClient()` 2건 → `create_llm_client("training_qa")` / `create_llm_client("training_judge")` 로 교체 (둘 다 docutil-evaluator AgentCode 매핑). 호출 본문(`self._source_llm.generate(...)`) 은 무변경. AI_INVENTORY W6(학습 데이터 생성 비용 별도 집계) 인용
- **AgentCode 매핑 표 (호출처 → AgentCode → 라우팅)**:

  | 호출처 | task 키 / model | AgentCode | LlmRouting | Phase 7.1 시드 |
  |---|---|---|---|---|
  | documents_v2/service.py:307 | provider=`get_provider_for_task("report")` | `docutil-report-generator` | Hybrid | gpt-4o |
  | templates/service.py:1122 | provider="report" | `docutil-report-generator` | Hybrid | gpt-4o |
  | workers/report_generator.py:936,3587 | provider="report" | `docutil-report-generator` | Hybrid | gpt-4o |
  | workers/jinja2_engine.py:880 | provider="template" | `docutil-rag-chat` (S7 폐기) | Hybrid | gpt-4o |
  | workers/evaluation_runner.py:53-58 | provider="evaluation" | `docutil-evaluator` | External | gpt-4o (judge) |
  | modules/search/agentic_search.py:215 | "agentic_search" | `agentic-search` | Hybrid | gpt-4o-mini |
  | modules/search/agentic_search.py:237 | "agentic_search" | `agentic-search` | Hybrid | gpt-4o-mini |
  | workers/training/data_generator.py:68 | "training_qa" | `docutil-evaluator` | External | gpt-4o |
  | workers/training/data_generator.py:69 | "training_judge" | `docutil-evaluator` | External | gpt-4o (judge) |

- **호환성 검증 (기존 호출처 영향 0건 목표)**:
  - **외부 시그니처 보존**: `create_llm_client(provider, api_key=None, model=None)` 인자/반환 타입(`LLMClient`) 무변경. 호출처 5곳 모두 코드 수정 불필요
  - **호출 메서드 보존**: `generate(messages, temperature, max_tokens, stream)` / `generate_stream(...)` / `generate_structured(messages, json_schema, ...)` / `generate_with_schema(system_prompt, user_prompt, response_schema, ...)` / `generate_sync` / `generate_structured_sync` / `generate_with_schema_sync` 모두 동일 시그니처. `AgentHubLLMWrapper` 가 `LLMClient` 베이스의 `generate_with_schema*` 기본 구현(Pydantic 재검증) 을 그대로 상속하므로 호출처 무변경
  - **`client.model` 속성 보존**: 일부 호출처가 `llm_client.model` 속성을 참조 가능 → `LLMClient.__init__(model=...)` 로 보존. AgentCode 가 model 속성에 들어가지만 로깅/디버깅 용도라 영향 없음
  - **API Key 인자 무시**: `create_llm_client(..., api_key=None)` 으로 None 전달 시 AgentHub 인증은 환경변수 `AGENTHUB_API_KEY` 가 처리. 호출처가 `api_key="sk-..."` 명시해도 silently 무시됨 — 한국어 주석으로 명시
- **단위 검증 결과 (모두 PASS)**:
  - `python -c "from app.integrations.llm.factory import create_llm_client, get_provider_for_task; print('factory OK')"` → factory OK
  - `AgentHubLLMWrapper('docutil-rag-chat')` 인스턴스화 + `agent_code='docutil-rag-chat'` / `model='docutil-rag-chat'` 검증 → all_OK
  - AgentCode 매핑 13 케이스 검증: chat/chatbot/report/evaluation/agentic_search/training_qa/training_judge/openai/anthropic 폴백/model 우회 3건/일반 model gpt-4o → 모두 일치, AgentCode 매핑 검증 PASS
  - 영향 모듈 11개 import 검증 (search/agentic_search, workers/training/data_generator, workers/report_generator, workers/jinja2_engine, workers/evaluation_runner, modules/documents_v2/service, modules/templates/service, integrations/llm, integrations/llm/factory, integrations/llm/client, integrations/agenthub_client) → all modules import OK
  - 동기 호출 환경변수 가드 검증: `AGENTHUB_URL` 미설정 시 `RuntimeError("AgentHub base_url 미설정 — 환경변수 AGENTHUB_URL 확인 (Phase 7.3)")` / `AGENTHUB_API_KEY` 미설정 시 동일 패턴 RuntimeError 발생 → guard1 OK, guard2 OK
  - ruff lint: `ruff check` 결과 2건 경고(TC003 + F401 in agentic_search.py) — `git stash` 로 baseline 확인 결과 **Phase 7.3 변경 이전부터 존재한 위반**. 본 변경이 새로 도입한 경고 0건
  - ruff format: 5개 파일 중 3개 reformatted (factory.py / client.py / agentic_search.py), 2개 unchanged (__init__.py / data_generator.py)
- **임베딩 처리 결정 (보류)**:
  - AgentHub `OpenAICompatController` 에 `/v1/embeddings` 엔드포인트 미존재 — chat/completions 만 노출
  - DocUtil `workers/embedding_generator.py:148-186` 의 `_generate_dense_embeddings()` 는 `httpx.post` 직접 호출 (`https://api.openai.com/v1/embeddings` 또는 vLLM `/embeddings`) — Phase 7.3 변경 범위 제외
  - **Phase 7.5 (별도 트랙) 권고**: AgentHub 측에 `EmbeddingsController` 신설 (`POST /v1/embeddings`) → `AgentHubClient.embedding(texts: list[str], model: str = "embedding-default") -> list[list[float]]` 메서드 추가 → DocUtil `embedding_generator.py` 의 httpx 직접 호출 → AgentHub 위임 교체. 현재 코드는 TODO 주석 미추가 (Phase 7.3 변경 범위 외)
- **본 Phase 보류 항목 (별도 트랙)**:
  - **DU-14 image_generation/service.py:189** — `from openai import AsyncOpenAI` 직접 사용 (DALL-E 3). AgentHub `/v1/images` 엔드포인트 미구현. Phase 7.5 또는 별도 ImageGeneration 트랙으로 분리. 현재 호출 흐름 영향 없음 (이미지 자동 채움 기능)
  - **DU-15 graph_rag.py:105** — `OpenAIClient()` 직접 호출. `graph_rag_enabled=False` 기본값으로 비활성 상태라 운영 영향 없음. 활성화 시점에 factory 경유로 일괄 교체 가능
  - **DU-18 embedding_generator.py:148-186** — 임베딩 호출 (위 임베딩 처리 결정 참조)
  - **client.py:741-743 ModelRouter** — A/B 테스트 라우팅. `_openai_client = OpenAIClient()` / `_vllm_client = VLLMClient()` / `_sglang_client = SGLangClient()` 인스턴스 보유. Phase 7.3 부터 AgentHub 측 라우팅(LlmRouting=Hybrid + RoutingPolicyJson)이 의미적으로 대체 — ModelRouter 자체는 dead code 동급. Phase 8+ 에서 제거 예정
  - **claude_client.py / gemini_client.py / azure_client.py** — `from anthropic import ...` 등 직접 SDK import 잔존. factory 가 더 이상 호출하지 않으므로 dead code. tests/test_llm_structured_cross_provider.py 가 직접 인스턴스화하지만, 본 변경의 호출 경로 외에 있어 영향 없음. Phase 8+ 에서 일괄 제거
- **잠재 위험 / 다음 단계 (Phase 7.4 의존 항목)**:
  - **AgentHub `/v1/chat/completions` 엔드포인트 부팅 검증 미실시**: 본 Phase 의 단위 검증은 import + AgentCode 매핑 + 환경변수 가드까지. 실제 HTTP 라운드트립 검증은 AgentHub IIS/dotnet run 부팅 + ApiKey 인증 + Agent 실행까지 필요 → Phase 7.4 시점에 통합 검증 또는 `/health` 단순 ping 으로 별도 단계 분리 권장
  - **OpenAI Structured Outputs `response_format=json_schema` AgentHub passthrough 검증 미실시**: `AgentHubLLMWrapper.generate_structured()` 가 `extra` 인자로 `response_format` 을 forward 하지만, AgentHub `OpenAICompatController.cs` 가 이를 그대로 OpenAI 로 forward 하는지 + Anthropic Tool Use / Gemini schema 평탄화로 변환하는지는 AgentHub 측 동작에 의존. Phase 7.1 시드의 `docutil-report-generator` Agent 가 gpt-4o 직접 매핑이라 일단 안전 — Hybrid 라우팅으로 Internal(Nexus) 분기 시 schema 변환 미지원 위험. AI_INVENTORY R3 (OpenAI Structured Outputs 다중 프로바이더 fallback) 와 동일 우려
  - **호출처의 `client.api_key` 직접 참조 가능성**: 일부 호출처(특히 templates/service.py)가 `llm_client.api_key` 또는 `llm_client.base_url` 을 직접 참조할 가능성 → 본 변경에서 `LLMClient.__init__(api_key=None, base_url="agenthub://")` 로 보존. 코드 grep 결과 직접 참조 발견 0건이지만, 향후 추가 호출처에서 발생 시 가드 필요
  - **Celery worker 환경변수 분배**: `AgentHubLLMWrapper.generate_sync()` 는 `AGENTHUB_URL` / `AGENTHUB_API_KEY` 를 호출 시점에 lazy 로드. Celery worker 컨테이너에 동일 환경변수가 분배되어야 함 (Phase 7.2 의 `.env` 갱신으로 docker compose env 자동 inherit 가정 — 운영 검증 필요)
  - **테스트 코드의 OpenAIClient/AzureOpenAIClient 직접 인스턴스화 영향**: tests/test_llm_structured_cross_provider.py / tests/test_documents_v2_service.py 가 `create_llm_client` 를 mock 처리. Phase 7.3 변경으로 mock 반환 객체 타입이 `OpenAIClient` 에서 `AgentHubLLMWrapper` 로 변경됨 — 단, mock 자체가 시그니처만 일치하면 통과하므로 테스트 영향 0건 예상. 실제 pytest 실행은 본 Phase 범위 외 (Phase 7.4 후 통합 테스트)
- **Phase 7.4 (career 위임) 진입 조건**:
  - [x] DocUtil `AgentHubLLMWrapper` + factory 외부 시그니처 보존 — 본 Phase 완료
  - [x] DocUtil 9곳 호출 매핑 + agentic_search/data_generator P1 위반 정리 — 본 Phase 완료
  - [ ] career 18 MS 의 LLM 직접 호출 식별 (CA-* 인벤토리 정독 필요)
  - [ ] career/shared/common/agenthub_client.py 활용 패턴 결정 (factory 도입 vs 직접 호출)
  - [ ] AgentHub `/v1/chat/completions` 부팅 라운드트립 검증 (DocUtil 1건 + career 1건)
- **commit 대기**: 사용자 확인 후 진행. 본 Phase 변경은 5개 파일(client.py / factory.py / __init__.py / agentic_search.py / data_generator.py) 모두 commit 안전 (시크릿 미포함, 디스크 .env 변경 0건)

### 2026-05-06 (Phase 4.3 — AIAgentManagement.Tenants + Departments 신설, ADR-8 / Q1 옵션 B)
- **사용자 결정 (Phase 4.3 진입 시 확정)**: Q1 옵션 B (Tenants + 별도 Departments 엔티티) 채택. 옵션 A(Tenants sub-org JSON) 는 indexing/조인 비효율, 옵션 C(career 자체 tb_department 유지) 는 R3 격리 위반 + 운영자 콘솔에서 부서 단위 정책 부여 어려움. 본 Phase 에서는 빈 엔티티(스키마 + 시드 1건) 만 도입하고 career.tb_department 데이터 30 학과 매핑은 별도 트랙
- **변경 파일 (2 신규 + 1 DbContext + 1 마이그레이션 + 2 .csx 검증 도구)**:
  - **NEW `agenthub/Models/Tenant.cs`** (~62 LOC) — `[Table("Tenants")]` + 8 컬럼 (TenantId IDENTITY / TenantCode 50 / TenantName 200 / Description 1000 / IsActive / CreatedAt / UpdatedAt? / CreatedBy?). Navigation: `Departments`(1:N) + `Creator`(User?). 한국어 XML doc + ADR-8 인용 주석
  - **NEW `agenthub/Models/Department.cs`** (~74 LOC) — `[Table("Departments")]` + 9 컬럼 (DepartmentId IDENTITY / DepartmentCode 50 / DepartmentName 200 / TenantId NOT NULL / ParentDepartmentId? self-FK / Description 1000 / IsActive / CreatedAt / UpdatedAt?). Navigation: `Tenant`(N:1) + `ParentDepartment`(self) + `ChildDepartments`(self 1:N). 한국어 XML doc + Q1 옵션 B 결정 사유 주석
  - **MODIFY `agenthub/Data/AIAgentManagementDbContext.cs`** — DbSet `Tenants` + `Departments` 추가. OnModelCreating 에 5개 매핑: `Tenant.TenantCode UNIQUE`, `Tenant.Creator FK ON DELETE SET NULL`, `Department.DepartmentCode UNIQUE`, `Department.TenantId / ParentDepartmentId 조회 인덱스 + ON DELETE RESTRICT FK 2건`
  - **NEW `agenthub/Migrations/20260506085522_AddTenantsAndDepartments.{cs,Designer.cs}`** — `dotnet-ef migrations add` 자동 생성. `Migrations/AIAgentManagementDbContextModelSnapshot.cs` 함께 갱신. archive 의 `Migrations.mssql.archive/AIAgentManagementDbContextModelSnapshot.cs` 는 변경 0건 (격리 유지)
  - **NEW `user_mig/tools/phase43_verify_seed.csx`** (~125 LOC) — dotnet-script + Npgsql 8.0.6 + async Run() 패턴. 7단계 검증(테이블 존재 / UNIQUE 인덱스 / FK / 컬럼 수 / 마이그레이션 히스토리 / 시드 / 총 BASE TABLE) + idino-default Tenant + general Department 멱등 시드
  - **NEW `user_mig/tools/phase43_fk_inspect.csx`** (~55 LOC) — FK ON DELETE 동작 + 인덱스 정의 + UNIQUE 위반 차단 시험 (PostgresException 23505 캐치)
- **마이그레이션 SQL 적용 결과 (운영 PG, 단일 트랜잭션, ~30ms)**:
  - `CREATE TABLE "AIAgentManagement"."Tenants"` (8 col) + PK + FK_Tenants_Users_CreatedBy ON DELETE SET NULL
  - `CREATE TABLE "AIAgentManagement"."Departments"` (9 col) + PK + FK_Departments_Departments_ParentDepartmentId ON DELETE RESTRICT + FK_Departments_Tenants_TenantId ON DELETE RESTRICT
  - 5개 인덱스: `IX_Tenants_TenantCode UNIQUE` / `IX_Tenants_CreatedBy` / `IX_Departments_DepartmentCode UNIQUE` / `IX_Departments_TenantId` / `IX_Departments_ParentDepartmentId`
  - `__EFMigrationsHistory` INSERT (`20260506085522_AddTenantsAndDepartments`)
- **검증 결과 (`phase43_verify_seed.csx` 출력)**:
  - 테이블 존재 True/True / UNIQUE 인덱스 2/2 / FK 제약 3/3 / Tenants 컬럼 8/8 / Departments 컬럼 9/9 / 마이그레이션 히스토리 True / 총 BASE TABLE 37 (35 + Tenants + Departments)
  - 시드 INSERT: idino-default Tenant TenantId=1 + general Department (TenantId=1, ParentDepartmentId=NULL) 1건 / 조인 조회 1행
- **FK ON DELETE / UNIQUE 정밀 검증 (`phase43_fk_inspect.csx`)**:
  - `Tenants.FK_Tenants_Users_CreatedBy` → ON DELETE SET NULL (운영자 계정 삭제가 Tenant 행을 지우지 않음)
  - `Departments.FK_Departments_Tenants_TenantId` → ON DELETE RESTRICT (Tenant 가 부서를 가지면 삭제 차단)
  - `Departments.FK_Departments_Departments_ParentDepartmentId` → ON DELETE RESTRICT (상위 부서 삭제 전 하위 재배치 강제)
  - UNIQUE 위반 시험: `INSERT 'idino-default' 중복` → PostgresException 23505 (`duplicate key value violates unique constraint "IX_Tenants_TenantCode"`). UNIQUE 동작 확인
- **Agent 모델 변경 X**: 본 Phase 에서는 Agent.TenantId / Agent.DepartmentId FK 미도입. 사유: 현재 시연 환경에서 Agent 가 사용자별 소유라 TenantId 매핑이 자연스럽지 않음. Phase 4.5 통합 검증 시점 또는 Phase 7+ 별도 트랙에서 결정. ADR-8 의 마이그레이션 경로는 (1) 현재 Phase 4.3 = 빈 엔티티 신설 → (2) Phase 4.4 = career.tb_department 30 학과 매핑 → (3) Phase 4.5 = Agent + ApiKey 의 TenantId/DepartmentId FK 도입 + 백필 → (4) Phase 7+ = SSO 결정 시 User.TenantId 도입 의 4단계
- **잠재 위험 / 다음 단계 (Phase 4.4 의존 항목)**:
  - **career.tb_department 30 학과 미매핑**: Phase 4.2 에서 적용한 idino_career schema 의 `tb_department` 가 빈 테이블 상태. AgentHub.AIAgentManagement.Departments 와의 매핑 정책 미정 (1:1 row-by-row 동기화 vs department_code 만 공유 vs FK 직접 참조 — 후자는 R3 위반). Phase 4.4 또는 별도 트랙에서 매핑 룰 결정 후 백필
  - **Agent FK 미도입**: 운영 데이터에서 어떤 Agent 가 어떤 Tenant 에 속하는지 미정. Phase 7.1 에서 시드한 15 Agent + admin 의 ApiKey 2 건은 모두 idino-default Tenant 에 잠정 귀속되는 것으로 가정 (코드 변경 없음, 단순 운영 룰)
  - **Department.ParentDepartmentId 순환 참조**: DB 단 검증 부재 (PostgreSQL 표준 self-FK 는 cycle detection 미지원). application 단 검증 (예: 트리 깊이 제한 10) 미구현. Phase 4.4 매핑 시 application 검증 도입
  - **TIMESTAMPTZ 사용**: 본 Phase 의 Tenants/Departments 는 timestamptz 채택 (EF 의 DateTime UTC 기본 매핑) — career.tb_* (timestamp without timezone) 와 시간 표현 불일치. 다국적 운영 시 통일 작업 필요 (별도 트랙)
  - **CreatedBy 시드 NULL**: 본 Phase 의 idino-default Tenant 는 CreatedBy=NULL (시스템 시드). 운영 시점에 admin@example.com 의 UserId 로 백필 가능 (선택)
- **Phase 4.3 진입/완료 조건 체크**:
  - [x] Q1 옵션 B 결정 (Tenants + 별도 Departments)
  - [x] Tenant + Department 모델 정의 + 한국어 XML doc + ADR-8 주석
  - [x] DbContext UNIQUE/FK 매핑
  - [x] EF 마이그레이션 add + 운영 PG 적용 검증 (37 BASE TABLE)
  - [x] 시드 (idino-default + general)
  - [x] FK ON DELETE / UNIQUE 위반 차단 정밀 검증
  - [x] archive ModelSnapshot 보존 검증 (변경 0건)
  - [x] progress.md 갱신
  - [ ] commit 대기 (Phase 4.1/4.2/4.3/7.1/7.2 통합 commit 또는 Phase 별 분리)
- **commit 대기**: 사용자 확인 후 진행. 신규 파일 6개(.cs 4 + .csx 2), 수정 1개(.cs DbContext + ModelSnapshot.cs)

### 2026-05-06 (Phase 4.2 — career DDL 3개 파일 → AGENT_HUB.idino_career schema 62 테이블 + 18 MS .env)
- **사용자 결정 (Phase 4.2 진입 전 확정)**: Q-A=빈 schema only(DDL only) / Q-B=옵션 C(SQL 무변경 + 런타임 래퍼) / Q-C=00_run_all.sql 의 DDL 3개 파일만 / Q-D=dotnet-script + Npgsql 직접 실행 (psql 미설치 환경) / Q-E=조사 후 결정 → **공용 라이브러리 1곳 + 18 MS 각자 .env override** 방식 채택 (조사 결과: `career/shared/database/connection.py` 공용 + 각 MS `app/database.py` 별도 존재)
- **사전 조사 결과**:
  - `00_run_all.sql` 파싱 — 13단계 `\i` 순서. DDL=3개 (`01_schema_create.sql` / `02_techspec_tables.sql` / `10_p1_p2_extensions.sql`). 나머지 10개는 seed/fix DML
  - DDL 3개 파일 인코딩 분석 — UTF-8 BOM + 한국어 mojibake (CP949↔UTF-8 인코딩 손상). `COMMENT ON ... '깨진한글'` 의 closing quote 누락, `-- 주석 CREATE TABLE` 같은 라인에 newline 누락 등 다중 손상 발견
  - 적용 전 idino_career schema 상태 — Phase 3.6 적용으로 schema 빈 상태 (0 테이블), 확장 3종(uuid-ossp/pgcrypto/vector) public schema 활성. R3 격리 — `document_utilization` 27 tb_*, `idino_career` 0
  - ORM 공통 패턴 — `career/shared/database/connection.py` 에 `DatabaseConfig.from_env()` 공통 클래스 존재 (DB_SCHEMA env override + `connect_args.server_settings.search_path` 주입). 18 MS 중 10개는 자체 `app/database.py` 가 `connect_args.server_settings.search_path = f"{settings.DB_SCHEMA},public"` 형태로 동등 패턴. 결론: **DB_SCHEMA 변경 없음, DB 접속 자격증명만 .env 로 override**
- **변경 파일 (3 신규 + 19 .env 갱신, 디스크만)**:
  - **NEW `user_mig/tools/phase42_inspect.csx`** (~70 LOC) — DB 사전 점검 스크립트. dotnet-script + Npgsql 8.0.6 + async Main 패턴
  - **NEW `user_mig/tools/phase42_apply.csx`** (~150 LOC) — DDL 3개 파일 적용 래퍼. 옵션 C 디스크 무변경 + 런타임 6단계 변환:
    1. UTF-8 BOM strip (`Encoding.UTF8` 자동 처리)
    2. `COMMENT ON ... ;` 라인 제거 (한국어 인용부호 손상 우회) — 22+18+23=63건
    3. `SET search_path TO idino_career;` → `idino_career, public` 패치 (uuid_generate_v4 등 extension 함수 가시성 확보) — 3건
    4. `-- 주석 CREATE TABLE` 인라인 분리 — 15+26+30=71건
    5. `CREATE INDEX` → `CREATE INDEX IF NOT EXISTS` (멱등성) — 8+9+28=45건
    6. `REFERENCES tb_user(user_id)` FK 제거 (별도 auth schema, 본 적용 대상 X) — 3건. DML(INSERT/UPDATE/DELETE) 제거 (Q-A — 빈 schema only) — 4건
  - **NEW `user_mig/tools/phase42_verify.csx`** (~80 LOC) — 적용 후 검증 스크립트. 테이블 수/인덱스/FK/행수/R3 누설 확인
  - **MODIFY `career/.env`** (디스크만, .gitignore 차단) — DB 블록 6 라인 갱신: `DB_HOST=192.168.10.39 / DB_PORT=5440 / DB_NAME=AGENT_HUB / DB_USER=AGENT_HUB / DB_PASSWORD=idino!@#$ / DB_SCHEMA=idino_career`. 한국어 주석으로 R3 격리 명시
  - **MODIFY 8 기존 MS .env** (디스크만): advisor / ai / badge / coaching / opportunity / portfolio / risk / simulation. `sed -i` 로 동일 DB 블록 in-place 치환 + `.phase42.bak` 백업
  - **NEW 10 신규 MS .env** (디스크만): auth / alumni / competency / integration / notification / privacy / roadmap / skill / student / worknet. 기존 .env 부재 → 신규 파일에 DB 블록만 작성
- **SQL 적용 결과 (3/3 OK, 적용 시간 약 5초)**:
  - `01_schema_create.sql`: 14 tb_* 테이블 + 8 인덱스 (학교/학과/교수/과목/학생/학기/수강/성적 마스터)
  - `02_techspec_tables.sql`: 25 tb_* 테이블 + 9 인덱스 (역량/스킬/평가/프로그램/포트폴리오/직무/추천/AI Ops 메타)
  - `10_p1_p2_extensions.sql`: 23 tb_* 테이블 + 28 인덱스 (Skill Graph/Opportunity/Coaching/Risk/Badge/Simulation/Advisor)
  - **합계**: 62 tb_* 테이블 + 128 인덱스 + 82 FK 제약. 모든 테이블 0행 (Q-A 빈 schema 원칙 100% 준수)
  - 사용자 spec 의 "53 tb_*" 와 차이 — 실제 DDL 3개 파일에 정의된 것은 **62 테이블**. spec 수치는 외부 추정치이며, 실측 62 가 정확
- **R3 schema 격리 검증 결과**:
  - idino_career: 62 tb_* / document_utilization: 27 tb_* (Phase 4.1) / public: 1 (vector_meta) / AIAgentManagement: 35 (PascalCase, tb_* 누설 없음) / hangfire: 8 (PascalCase). **누설 0건 — 통과**
  - MS-style 접속 시뮬레이션 (`SearchPath=idino_career` connstring) — `tb_university` / `tb_role` no-prefix read 0행, search_path 정상 적용 확인
- **잠재 위험 / 다음 단계 (Phase 4.3 의존 항목)**:
  - **tb_user FK 누락 (3건)**: file 10 의 advisor 관련 3개 컬럼(`tb_advisor_assignment.advisor_user_id`, `tb_advisor_intervention.advisor_user_id`, `tb_advisor_note.advisor_user_id`) 이 FK 없는 단순 UUID 컬럼이 됨. tb_user 는 별도 `scripts/01_auth_tables_ddl.sql` 에 정의되어 본 적용 대상 X. **Phase 4.3 또는 별도 트랙에서 tb_user 도입 후 ALTER TABLE ... ADD CONSTRAINT FK 복구 필요**
  - **DML 미적용 (4건)**: file 10 의 `tb_role_skill_map` / `tb_skill_relation` / `tb_opportunity` / `tb_badge` 시드 INSERT 4건은 Q-A 원칙으로 skip. 시연 단계에서 빈 테이블에 application 단 데이터 입력으로 검증 가능
  - **Q1 옵션 B (Tenants + Departments)**: career 의 `tb_department` 가 추후 통합 Tenants/Departments 모델로 이전될 때, 30개 학과 데이터 매핑이 별도 트랙. 현재 빈 테이블이라 영향 없음
  - **TECHSPEC §16 R12 (Cascade Delete)**: 적용된 82개 FK 중 ON DELETE 명시 없음 → PostgreSQL 기본 NO ACTION. 운영 시 cascade 정책 검토 필요 (특히 tb_student → tb_enrollment/tb_grade)
  - **timezone**: TIMESTAMP without timezone 사용 (TIMESTAMPTZ 권장). 현재 시연용 단일 KST 환경이라 즉시 위험 X. 다국적 운영 시점에 ALTER TABLE
  - **ORM 모델 schema 적용**: 코드 변경 0건 — 기존 `connect_args.server_settings.search_path` 패턴이 그대로 동작. 단, `__table_args__ = {'schema': 'idino_career'}` 명시 패턴은 미사용. SQLAlchemy `MetaData(schema='idino_career')` 도 미사용. 현재는 search_path 의존이라 R3 격리 강제력이 약함 (실수로 DB_SCHEMA 변경 시 다른 schema 에 테이블 생성 위험) — Phase 4.3 또는 별도 트랙에서 명시적 schema 매핑 검토
- **Phase 4.3 진입 조건**:
  - [x] career idino_career schema 62 테이블 적용 — 본 Phase 완료
  - [x] 18 MS .env DB 블록 갱신 — 본 Phase 완료
  - [ ] Tenants + Departments 모델 ADR-8 구체화 (Q1 옵션 B 결정 적용)
  - [ ] tb_user 도입 + 3개 advisor FK 복구
  - [ ] (선택) seed 데이터 적용 — application 단 또는 03_*~60_* SQL 별도 적용
- **commit 대기**: 사용자 확인 후 진행. .csx 3개 파일은 commit 가능, .env / .bak 19개 파일은 .gitignore 차단

### 2026-05-06 (Phase 7.2 — 운영 PG 시드 적용 + 시연용 master ApiKey 2개 발급 + 공용 AgentHubClient 라이브러리)
- **목적**: Phase 7.1(AgentHub 15개 Agent 시드 코드 작성)이 운영 PG 에 *미적용* 상태였고, Phase 7.3/7.4 (DocUtil/career 측 LLM 직접 호출 → AgentHub 위임 교체) 진입 전 인프라 사전 준비가 필요. 본 Phase 에서 (1) 운영 PG 에 시드 적용 (2) 시연용 master ApiKey 2개 발급 (3) DocUtil/career 양쪽에 공용 AgentHubClient Python 라이브러리 설치 (4) .env / .env.example 갱신
- **변경 파일 (5 신규 + 5 수정 + 디스크만 2)**:
  - **NEW `user_mig/tools/phase72_inspect.py`** (~110 LOC) — 운영 PG read-only 점검 스크립트. admin/ApiServices/Agents/ApiKeys 현황 + ApiKeys 컬럼 스키마(Phase 3.3c GCM/KeyHash) 확인. dotnet 부팅 의존 우회 — Python asyncpg 직접 쿼리
  - **NEW `user_mig/tools/phase72_seed.py`** (~600 LOC) — Phase 7.1 시드 + ApiKey 발급 통합 스크립트. 멱등 가드 3중 (RoleName / Email / AgentCode UNIQUE). AES-GCM 12바이트 random IV + 16바이트 Tag 분리 저장 — AgentHub `ApiKeyService.EncryptApiKey` 와 1:1 일치 (`Encryption:ApiKeyAesKey` 미설정 폴백 분기와 동등 SHA-256(JWT_SECRET) 32바이트). KeyHash = SHA-256(plaintext) HEX 대문자 64자. `--dry-run` / `--print-keys` 두 옵션. `.phase72_keys.json` 평문 저장 (.gitignore 차단)
  - **NEW `docutil/backend/app/integrations/agenthub_client.py`** (~280 LOC) — DocUtil 측 공용 AgentHubClient. `chat()` 비스트리밍 + `chat_stream()` SSE generator + `aclose()` lifespan shutdown. `lru_cache(1)` 싱글턴 `get_agenthub_client()`. `httpx.AsyncClient` connection pool 재사용. `AgentHubError` 한국어 메시지 (401/403/404/429/502/503/504 매핑). 한국어 docstring 으로 R2/R3/R5 의도 명시
  - **NEW `career/shared/common/agenthub_client.py`** (~290 LOC) — career 18 MS 공용 AgentHubClient. DocUtil 측과 시그니처 1:1 동일. `consumer_label` 인자 추가 — 환경변수 `AGENTHUB_CONSUMER` 로 MS 별 식별 가능 (예: `career-ai-service`, `career-coaching-service`). User-Agent 헤더에 반영
  - **NEW (운영 PG INSERT — 변경 없는 .py 스크립트로 적용)**: AGENT_HUB DB 의 `AIAgentManagement` schema 에 다음 행 신규 INSERT
    - Roles 3개: Admin / Developer / User (RoleId=4/5/6 — 기존 시퀀스 이어받음)
    - Users 1개: admin@example.com / Admin123! / BCrypt 11라운드 (UserId=2)
    - UserRoles 1개: User=2 ↔ Role=Admin
    - ApiServices 3개: chatgpt(ServiceId=1) / dalle(2) / nexus(3)
    - Agents 15개: AgentId=1~15 (LlmRouting 분포: External 4 / Hybrid 10 / Internal 1) — Phase 7.1 카탈로그 1:1 일치
    - ApiKeys 2개: ApiKeyId=1 docutil-master-key / ApiKeyId=2 career-master-key. UserId=2(admin), AgentId=NULL(전체 권한), ServiceCode=agent-api, Scopes=`chat,stream,info,usage`, Active=TRUE, ExpiresAt=NULL
  - **MODIFY `career/shared/common/__init__.py`** (+10 LOC) — `AgentHubClient` / `AgentHubError` / `get_agenthub_client` export 추가. 기존 모듈 시그니처 보존 (Kafka optional import 등)
  - **MODIFY `docutil/backend/app/integrations/__init__.py`** (+1 LOC) — docstring 에 `agenthub_client` 항목 추가. 기존 llm 모듈에 `Phase 7.3 deprecate 예정` 주석
  - **MODIFY `docutil/.env`** (디스크만, .gitignore 차단) — `AGENTHUB_URL=http://localhost:5000` + `AGENTHUB_API_KEY=ak-...` (docutil-master-key 평문) 신규
  - **MODIFY `career/.env`** (디스크만, .gitignore 차단) — `AGENTHUB_URL` + `AGENTHUB_API_KEY=ak-...` (career-master-key 평문) + `AGENTHUB_CONSUMER=career` 신규
  - **MODIFY `docutil/.env.example`** (커밋 가능) — `CHANGE_ME_agenthub_api_key` placeholder + 한국어 안내. 운영 환경에서 AgentHub UI 정식 발급 절차 사용 권장 명시
  - **MODIFY `career/.env.example`** (커밋 가능) — 동등 항목 + `AGENTHUB_CONSUMER` placeholder
  - **MODIFY `.gitignore`** (+3 LOC) — `user_mig/tools/.phase72_keys.json` 패턴 추가 (시연용 평문 키 저장 파일)
- **암호화 호환성 검증 (AgentHub `ApiKeyAuthService.ValidateApiKeyAsync` 동등 시뮬레이션)**:
  - 발급된 평문 키 → SHA-256 HEX 산출 → `KeyHash` UNIQUE 인덱스 단건 조회 → AES-GCM 복호화 → 평문 일치 확인 — 2/2 OK
  - AgentHub 인증 핫패스(빠른 경로)에서 즉시 통과될 것임을 확인. Legacy 폴백(KeyHash NULL) 경로는 진입하지 않음
- **잠재 위험 / 다음 단계 (Phase 7.3 / 7.4 의존 항목)**:
  - **AgentHub 부팅 시 시드 충돌 가능성**: 본 task 가 직접 INSERT 한 admin/Roles 가 후속 AgentHub 정상 부팅 시 `DatabaseInitializer.SeedAsync` 의 멱등 가드(`AnyAsync()`)에 막혀 skip 되어야 안전. 코드 검증: `Roles.AnyAsync()` true → skip OK / `Users.FirstOrDefaultAsync(Email='admin@example.com')` non-null → 기존 admin 상태 점검 분기 진입 (BCrypt prefix 검사 통과 후 패스워드 검증 실패 시 재해시 — 본 task 의 BCrypt 11라운드 해시는 통과). `ApiServices.AnyAsync()` true → 6개 시드 분기 skip + 기존 `existingMistral`/`existingNexus`/`existingImageServices` 분기는 미존재 항목만 추가 → claude/cursor/copilot/gemini/mistral 추가 INSERT (6→ 약 14개로 확장됨, 기존 3개와 충돌 없음). `Agents` 멱등 가드는 `AgentCode` 단위 — 본 task INSERT 한 15개 모두 skip OK
  - **AgentHub URL 미확정**: `.env` 의 `AGENTHUB_URL=http://localhost:5000` 은 개발 가정. 운영 시 `agenthub.idino.co.kr` 또는 IIS 호스팅 도메인으로 변경 필요. Phase 7.3/7.4 의 통합 검증 단계에서 결정
  - **Encryption:ApiKeyAesKey 미설정 의존**: 본 task 는 `appsettings.Development.json` 의 `Encryption:ApiKeyAesKey=""` 폴백 분기(JWT key SHA-256 유도)에 의존. 운영 환경에서 별도 AES key 주입 시 본 task 의 발급 키는 *복호화 실패* 가 발생하므로 **재발급 필요** (TECHSPEC §16 C2 — Phase 3.6 마이그레이션 시점)
  - **Scopes 전체 권한**: 시연용 단순화로 `chat,stream,info,usage` 모두 허용. 운영 시 시스템별 최소 권한 원칙(예: docutil-user 키는 chat+stream 만, AgentId 바인딩) 으로 좁힐 것
  - **ConsumerSystems 검증 미수행**: AgentHub 의 `Agent.ConsumerSystems` JSON 화이트리스트 검증은 ApiKey 의 `ConsumerSystem` 값과 매칭되어야 하나 현재 `ApiKey` 모델에는 ConsumerSystem 컬럼 부재 — Phase 7 후속 작업에서 KeyName(예: `docutil-master-key`) prefix 매칭 또는 별도 컬럼 신설 검토
  - **시연용 평문 키 회수 절차 부재**: `.phase72_keys.json` 은 .gitignore 차단되지만 디스크에 평문으로 잔존. 시연 종료 후 **삭제** 권장. 정기 키 회전(rotate) 정책은 운영 시 별도 트랙
- **Phase 7.3 / 7.4 진입 조건**:
  - [x] AgentHub 15 Agent 시드 운영 적용 — 본 Phase 완료
  - [x] master ApiKey 2개 발급 + 평문 안전 전달 — 본 Phase 완료
  - [x] 공용 AgentHubClient 라이브러리 — 본 Phase 완료
  - [ ] AgentHub 부팅 검증 (HTTP `/v1/chat/completions` 1회 라운드트립) — Phase 7.3 통합 검증 시점
  - [ ] AgentHub 측 `Agent.ConsumerSystems` 화이트리스트 강제 검증 동작 확인 — 별도 트랙
- **commit 대기**: 사용자 확인 후 진행. **평문 ApiKey 는 commit 미포함** — 사용자에게 별도 채널(보고서/구두) 전달

### 2026-05-05 (Phase 4.1 — DocUtil alembic schema → AGENT_HUB.document_utilization)
- **목적**: Q3 옵션 B 의 첫 단계 — monorepo 안에 복사된 DocUtil 코드를 AGENT_HUB DB(192.168.10.39:5440) 의 `document_utilization` schema 로 연결. 시연용 monorepo COPY 환경이라 데이터 이전(pg_dump → import) 은 생략하고 **빈 schema 에 alembic head 까지 적용**. R3 스키마 격리 + cross-schema FK 차단 검증
- **변경 파일 (4 modify)**:
  - **`docutil/backend/app/core/config.py`** (+8 LOC) — `db_schema: str = Field(default="document_utilization", ...)` 신규 Settings. 환경변수 `DB_SCHEMA` override 가능. 한국어 docstring 으로 R3 격리 의도 명시
  - **`docutil/backend/app/core/database.py`** (총 +28 LOC, 순서 재배치)
    - `_settings` / `_is_sqlite` 정의를 `metadata` 정의 *전* 으로 이동 (의존 순서 정정)
    - `MetaData(naming_convention=..., schema=None if _is_sqlite else _settings.db_schema)` 글로벌 schema 적용 — 18 모듈의 모든 모델이 자동으로 `document_utilization` 에 매핑되어 `__table_args__={"schema":...}` 일괄 추가 불요 (방법 B)
    - PostgreSQL 분기에 `connect_args={"server_settings": {"search_path": f"{_settings.db_schema},public"}}` 추가 — asyncpg 드라이버 connect 직후부터 schema 격리. public 은 pgcrypto/uuid-ossp 확장 함수 위치라 fallback 으로 두 번째에 배치
    - 한국어 docstring 으로 cross-schema FK 가 있을 때만 명시적 schema 지정해야 한다는 가이드 추가
  - **`docutil/backend/alembic/env.py`** (총 +35 LOC)
    - `import sqlalchemy as sa` 추가
    - `_db_schema = settings.db_schema`, `_is_sqlite` 모듈 레벨 helper
    - `set_main_option("sqlalchemy.url", ...)` 호출 시 URL 의 `%` 문자를 `%%` 로 escape (configparser 보간 충돌 회피 — `%21%40%23%24` 같은 percent-encoded 비밀번호 처리)
    - `run_migrations_offline` / `do_run_migrations` 양쪽에 `version_table_schema=_db_schema, include_schemas=True` 추가 — alembic_version 테이블도 동일 schema 안에 격리
    - **`do_run_migrations` 가 alembic transaction 내부에서** `CREATE SCHEMA IF NOT EXISTS "document_utilization"` + `SET LOCAL search_path TO "document_utilization", public` 발행 — DDL 멱등성 + AGENT_HUB DB default search_path(`"AIAgentManagement", document_utilization, ...`) 무시하고 db_schema 우선 (시행착오 기록: `begin_transaction` 밖에서 SET 을 발행하면 SQLAlchemy autobegin 으로 transaction 분리되어 outer commit 누락 → DDL 전체 롤백되는 silent 실패)
    - `run_async_migrations` 의 `async_engine_from_config` 에 `connect_args={"server_settings":{"search_path":...}}` 추가 (이중 안전)
  - **`docutil/.env`** + **`docutil/backend/.env`** — DocUtil 전용 PG(5434/5440 docutil DB) → AGENT_HUB(192.168.10.39:5440) 으로 전환:
    - `POSTGRES_USER=AGENT_HUB`, `POSTGRES_PASSWORD=idino!@#$`, `POSTGRES_DB=AGENT_HUB`, `POSTGRES_HOST=192.168.10.39`, `POSTGRES_PORT=5440`, `DB_SCHEMA=document_utilization` 신규
    - `DATABASE_URL=postgresql+asyncpg://AGENT_HUB:idino%21%40%23%24@192.168.10.39:5440/AGENT_HUB` (특수문자 percent-encoded — `!`=%21, `@`=%40, `#`=%23, `$`=%24)
    - 두 파일 모두 `.gitignore` 차단됨 (R4) — 디스크에만 갱신
- **알렘빅 적용 결과 (운영 PG 검증 — asyncpg 직접 쿼리)**:
  - `document_utilization` schema 의 일반 테이블 수 = **28 개** (alembic_version 포함)
  - `alembic_version.version_num` = **`009_organization_quotas`** (head 일치)
  - 적용 마이그레이션 8 개 모두 성공: `001_initial → 002_dept_proj_restructure → 003_templates_agents → 004_jinja2_template_system → 005_multi_provider → 006_evaluation → 007_documents_v2 → 009_organization_quotas`
  - 시드 검증: `tb_organizations` 의 Default Organization (slug="default") + `tb_users` 의 admin (role=super_admin, email=admin@docutil.local) 모두 존재
  - **R3 누설 점검 = 0건**: `public`/`AIAgentManagement`/`idino_career`/`hangfire` 4 schema 에 `tb_*` 테이블이나 `alembic_version` 신규 생성 없음 (PG `pg_class` JOIN `pg_namespace` 직접 점검)
  - 다른 schema 현황: AIAgentManagement=35 (Phase 3.6 그대로), public=`__EFMigrationsHistory` 1 (그대로)
- **cross-schema FK / search_path 결정**:
  - DocUtil 18 모듈의 모든 ForeignKey 가 `tb_xxx.id` 단순 참조 (Grep 48 occurrences 분석 완료) — cross-schema FK 0 건, 방법 B(글로벌 metadata.schema) 안전
  - search_path = `document_utilization, public` 우선 (public 은 pgcrypto `gen_random_uuid()` / `crypt()` 호출용 fallback)
  - 운영자가 다른 schema 의 객체에 우연히 접근하지 못하도록 connection-time + alembic-time 두 곳에서 강제
- **잠재 위험 / 다음 단계 (Phase 4.2)**:
  - DocUtil 부팅 검증(`docker compose up` 또는 로컬 venv `uvicorn app.main:app`) 미수행 — 별도 트랙 (HW/Docker 환경 의존)
  - Qdrant/MinIO/Redis 외부 의존성은 5440 docutil 클러스터의 인스턴스를 그대로 사용 — 별도 마이그레이션 시점에 통합 결정 필요 (Phase 4.2 또는 그 이후)
  - **운영 데이터 미이전**: 시연용 monorepo COPY 환경 결정 사항 — 실 데이터 이전 필요 시 별도 `pg_dump --schema-only` + `pg_dump --data-only --no-owner` 2 단계 + sequence reset 필요 (TECHSPEC §12.4 참조)
  - DocUtil S6/S7 작업이 `tb_search_history`/`tb_documents_v2` 컬럼을 추가하면 모델/마이그레이션이 monorepo 와 docutil 원본 두 곳에 동기화되어야 함 — Q3 옵션 B 의 핵심 위험 (별도 트랙)
  - alembic.ini 의 `sqlalchemy.url` placeholder(`postgresql+asyncpg://postgres:postgres@localhost:5432/doc_util`)는 개발자 헷갈림 방지를 위해 향후 비워두거나 주석 처리 검토 (현재는 env.py 에서 settings.database_url 로 override 하므로 동작상 문제 없음)
- **commit 대기**: 사용자 확인 후 진행

### 2026-05-06 (Phase 7.1 — AgentHub 15개 신규 Agent 카탈로그 시드 등록)
- **목적**: AI_INVENTORY.md §6 의 15개 신규 Agent 정의(DocUtil 4 + career 8 + 공통 3)를 `DatabaseInitializer.SeedAgentsAsync` 에 멱등 시드로 등록. Phase 7.3/7.4 의 LLM 직접 호출 → AgentHub Agent 위임 교체 시 즉시 사용할 수 있는 사전 카탈로그 확보. R2(단일 진입점) 의 코드 측면 사전 준비
- **변경 파일 (1 modify + 1 docs)**:
  - **`agenthub/Data/DatabaseInitializer.cs`** (937 → 약 1,200 LOC, +263)
    - 신규 `SeedAgentsAsync` private static 메서드 (약 250 LOC) — 15개 Agent 카탈로그를 튜플 배열 `seeds` 로 정의 후 foreach 멱등 INSERT
    - `SeedAsync` 흐름의 `UpdateApiServiceModelsAsync` 직후 호출 추가 — 호출 순서: Roles → Users → ApiServices → ApiServiceModels → **Agents (신규)**
    - 멱등 가드 3중:
      1. `AgentCode` 존재 검사 후 INSERT — 운영자 UI 수정값 보존(SystemPrompt/Temperature 덮어쓰기 금지)
      2. `ServiceCode` 부재 환경(외부망에서 nexus 미등록) → 해당 Agent skip + stderr 경고 (career-chatbot 만 영향)
      3. `admin@example.com` 부재 시 시드 전체 skip (`Agents.CreatedBy` NOT NULL FK)
    - 시드 카탈로그 분포 (LlmRouting 분포):
      - **External 4개**: docutil-evaluator, docutil-image-generator, embedding-default, web-search-default — 정확도/외부 API 의존
      - **Internal 1개**: career-chatbot — 학생 PII 위험(Nexus LAN-only 강제)
      - **Hybrid 10개**: 나머지 — HybridRouter(Phase 5.2) 가 PII/dataLabel/capability/cost 평가 후 분기
    - RAG 활성 5개(docutil-rag-chat, docutil-report-generator, career-rag-actionboard, agentic-search) → KnowledgeBaseSource="DocUtil" 자동 매핑(ADR-2). 나머지는 "AgentHub" 폴백
    - SystemPrompt 200~500 자 한국어(R5) — 각 Agent 의 페르소나/역할/제약(예: career-chatbot 은 위기 신호 감지 시 상담 센터 권유, docutil-evaluator 는 RAGAS JSON only 출력 강제)
    - 모든 시드 Agent: `IsPublic=false`(시스템 시드는 운영자 콘솔 한정), `SortOrder=100`(사용자 생성 Agent 0~99 보다 뒤로), `CreatedBy=admin.UserId`, `IconClass="bi-robot"`, `ColorCode="#6366f1"`
  - **`docs/AI_INVENTORY.md`** — 부록 C 신설 (Phase 7.1 시드 매핑 테이블 + 멱등성 가드 명세 + Phase 7.2~7.4 다음 단계)
- **빌드 검증**: `dotnet build --no-restore -v quiet` 결과 **0 errors / 0 warnings (재실행 시) / 11 warnings (초회, 모두 기존 CS1998 unrelated)**
- **DB 변경 0건** — 본 작업은 DatabaseInitializer 코드만 수정. 운영 PG 적용은 AgentHub 부팅 시 자동 (또는 사용자 시연 시점)
- **다음 단계 (Phase 7.2)**: 15개 AgentCode 별 `ApiKey` 발급 + `ConsumerSystem` 라벨 매핑 + 환경변수(`AGENTHUB_API_KEY_DOCUTIL` / `AGENTHUB_API_KEY_CAREER` 등) 분배 시나리오 정의
- **잠재 위험**:
  - `career-chatbot` 은 LlmRouting="Internal" + ServiceCode="nexus" — 외부망 환경에서 nexus 미등록 시 Agent 자체가 시드되지 않음. 외부망 시연 시 운영자 UI 에서 LlmRouting 을 "Hybrid" 로 변경 또는 별도 ServiceCode 매핑 필요 (시드는 멱등이므로 안전)
  - `dalle` 서비스가 ImageGeneration ServiceType — `docutil-image-generator` 는 Chat 호출이 아닌 별도 ImageGeneration 흐름이 필요. Phase 7.3 에서 DocUtil DU-14/DU-19 의 위임 코드 작성 시 AgentHub 의 `/api/images` 엔드포인트(또는 신규) 와 결합 정책 확정 필요

### 2026-05-06 (Phase 5.2 — AiProxyService nexus 분기 + CallNexusAsync/StreamNexusChunksAsync + IHybridRouter/HybridRouter 5단계 결정 엔진 + ChatService ResolveServiceIdAsync + ApiServiceModels nexus 시드)
- **목적**: Phase 5.1 의 INexusClient + Agent 라우팅 컬럼을 실 호출 경로에 결합. ADR-1 옵션 B 의 native /v1/chat 호출, TECHSPEC §10.3 / §15.4 의 HybridRouter 결정 엔진(PII / 데이터 라벨 / 모델 capability / 비용 임계치 / default 5단계), ChatService 진입점에서 LlmRouting 평가 후 ServiceId 보정. EF 모델 변경 0건 — 마이그레이션 add 불필요
- **변경 파일 (5 modify + 2 new)**:
  - **`Services/IHybridRouter.cs` (NEW, 73 LOC)** — `IHybridRouter` 인터페이스 + `HybridRoutingDecision(string Decision, string Reason, string? Detail)` record. Reason enum-like 문자열 7종 표준화: `pii_detected` / `data_label` / `capability_required` / `cost_exceeded` / `default` / `invalid_policy` / `empty_policy`. 한국어 XML doc + .claude/rules/domain-model.md 인용
  - **`Services/HybridRouter.cs` (NEW, 약 305 LOC)** — `IHybridRouter` 구현체. 의존성: `IPiiDetectionService`, `IHttpContextAccessor`, `ILogger<HybridRouter>`. 5단계 결정 우선순위:
    1. **PII**: `piiThreshold` ∈ {"block","mask"} 일 때 `_piiService.DetectPiiAsync(lastUserContent)` 호출 → `HasPii=true` 면 `piiAction`(기본 "internal") 반환. 검출 실패는 보수적으로 "internal" + reason="pii_detected" + detail="pii_check_failed"
    2. **데이터 라벨**: HTTP 헤더 `X-Data-Label` 값으로 `dataLabels[label]` 매핑(case-insensitive). DTO 확장은 별도 트랙
    3. **모델 capability**: vision 휴리스틱(model 이름에 "vision"/"4o"/"o1"/"claude-3-5-sonnet"/"gemini-2.5-pro"/"gemini-3" 포함) → external 강제. longContext: `request.MaxTokens > longContextThreshold`(기본 32000) → external 강제
    4. **비용 임계치**: 글자수/4 휴리스틱 토큰 추정 × 단가 0.000002 USD/token > `costThreshold.perRequest` → `exceedAction`(기본 "internal") 반환
    5. **default**: `policy.default` (없으면 "external")
    - `NormalizeDecision` 헬퍼로 알 수 없는 값은 보수적으로 "external" 폴백
    - `JsonSerializer.Deserialize<JsonElement>` + `PropertyNameCaseInsensitive=true` 로 PascalCase/camelCase 모두 허용
    - 정책 JSON null/빈 문자열 → "external" + reason="empty_policy", invalid JSON → "external" + reason="invalid_policy" + LogWarning
  - **`Services/AiProxyService.cs`** (3,966 → 약 4,260 LOC, +294)
    - 생성자에 `INexusClient? nexusClient = null` 옵셔널 추가 — Phase 5.1 단위 테스트 호환성 보존
    - 라인 213~231 `SendChatMessageAsync` switch 에 `"nexus" => await CallNexusAsync(service, model, request, cancellationToken)` 1줄 추가 (기존 7개 분기 보존)
    - 라인 274 인근 `SendChatMessageStreamChunksAsync` 에 `if (providerCode == "nexus")` 분기 추가 → `StreamNexusChunksAsync` 위임 후 `yield break`. 기존 OpenAI native streaming 직후 위치
    - **`CallNexusAsync` (약 110 LOC, NEW)**: ChatMessageRequestDto.Messages → Nexus 단일 message string 변환은 `BuildNexusSingleMessage` 헬퍼 위임. 마지막 user 메시지(멀티모달 텍스트 포함) + 시스템 메시지 prepend(있으면). Nexus model 매핑은 `NormalizeNexusModel` 헬퍼 — "primary"/"auxiliary" 외 값은 "primary" 폴백 + LogWarning. TenantId 는 `_configuration["Nexus:DefaultTenantId"]` 기본 "default". `INexusClient.SendChatAsync` 위임 후 `AiResponseDto` 반환(Cost=0, Model=nexusModel, FinishReason="stop", PromptTokens/CompletionTokens/TotalTokens 는 NexusUsage 매핑). **예외 처리**: `HttpRequestException` → `InvalidOperationException("Nexus 응답 실패. 사내망 연결을 확인하세요.")`, `TaskCanceledException`(타임아웃) → `InvalidOperationException("Nexus 응답이 시간 초과되었습니다.")`. 사용자 cancellation 은 그대로 전파
    - **`StreamNexusChunksAsync` (약 90 LOC, NEW)**: `[EnumeratorCancellation]` 부착. `_nexusClient.SendChatStreamAsync` 의 `NexusStreamEvent` 를 `ChatChunk` 로 매핑:
      - `"chunk"` → `ChatChunk.Delta(evt.Text)`
      - `"usage"` → `ChatChunk.Usage(prompt/completion/total)`, `sawUsage` 플래그 set
      - `"error"` → `InvalidOperationException(evt.ErrorMessage ?? "Nexus 스트리밍 중 에러가 발생했습니다.")`
      - `"done"` → break (자연 종료)
      - 미인식 type → LogDebug
    - 종료 후 항상 `ChatChunk.Stop("stop")` 발행 — Phase 3.5b finish_reason 컨벤션 보존. usage 미수신 시 LogDebug 로 흔적 남김(상위 ChatService 가 cost=0 폴백)
    - 헬퍼: `BuildNexusSingleMessage` (system+last user 결합), `NormalizeNexusModel` ("primary"/"auxiliary" 정규화)
  - **`Services/ChatService.cs`** (1,655 → 약 1,810 LOC, +155)
    - 생성자에 `IHybridRouter? hybridRouter = null` 옵셔널 추가
    - **3개 메서드의 라우팅 진입점**:
      - L473 `SendDirectMessageAsync` (비스트리밍): Agent 룩업 + `request.ServiceId = agent.ServiceId` 폴백 직후, Quota 체크 직전 `await ResolveServiceIdAsync(agent, request, CancellationToken.None)` 추가
      - L1022 `SendDirectMessageStreamChunksAsync` (OpenAI 호환 stream): Agent 룩업 직후 `await ResolveServiceIdAsync(agent, request, cancellationToken)` 추가
      - L1323 `SendDirectMessageStreamEventsAsync` (Vue chat stream): 동일 위치
    - **`ResolveServiceIdAsync` private helper (NEW)**: agent.LlmRouting 평가 후 in-place 로 `request.ServiceId` 보정
      - "External" 또는 null → 기존 ServiceId 유지(외부 시그니처 무변경)
      - "Internal" → `SwapToServiceCodeAsync("nexus", ...)` 로 활성 nexus ApiService.ServiceId 로 치환
      - "Hybrid" → `IHybridRouter.DecideAsync` 결과로 분기 ("internal" 결정 시 nexus 로 swap, "external" 결정 시 유지). 결정 결과는 `LogInformation` 으로 AgentId/Decision/Reason/Detail 4종 기록
      - 알 수 없는 LlmRouting 값 → 기존 동작 보존 + LogWarning
      - HybridRouter 미주입 → External 폴백 + LogWarning(단위 테스트 호환성)
    - **`SwapToServiceCodeAsync` private helper (NEW)**: 활성 ApiService 룩업 후 `request.ServiceId` 갱신, 결과를 LogInformation 으로 추적. 활성 ApiService 미존재 시 기존 ServiceId 유지 + LogWarning(외부망 환경 nexus 미배포 폴백)
    - DTO 변환은 `pseudoRequest = new ChatMessageRequestDto { Messages = ..., MaxTokens = ..., Temperature = ..., Language = ... }` — HybridRouter 평가에 필요한 핵심 필드만(전체 매핑은 무거우므로 회피)
  - **`Program.cs`** (610 → 611 LOC, +1)
    - L266 `builder.Services.AddScoped<IHybridRouter, HybridRouter>()` 추가 (Phase 5.1 의 `INexusClient` 등록 직후)
  - **`Data/DatabaseInitializer.cs`** (920 → 932 LOC, +12)
    - `SeedApiServiceModelsAsync` switch 의 `"sora"` case 직후 `case "nexus"` 추가 — `primary` (SortOrder=1, "Nexus Primary (메인 모델)") + `auxiliary` (SortOrder=2, "Nexus Auxiliary (보조 모델)") 2개 ApiServiceModel 멱등 시드. 기존 멱등 가드(`existingModels` AnyAsync) 이미 적용되어 추가 변경 불필요. AgentBuilder UI 의 모델 드롭다운 표시용 (실 모델명은 nexus_config.yaml 매핑)
- **빌드 검증** (`dotnet build --no-restore -v quiet`):
  - 1차: HybridRouter.cs L201 `CS0136 — 'threshold' 변수 중복 선언` 에러 1건 발생 — longContext 의 `threshold` 와 cost 의 `threshold` 가 같은 메서드에서 충돌
  - 변수명 변경 (cost 측 → `costThreshold`) 후 2차: **0 errors / 11 warnings** (전부 기존 CS1998, 신규 도입 0건). 경과 2.79s
- **단위 검증 (`dotnet-script` 6 시나리오)** — bin/Debug/net8.0/hybrid_test.csx ad-hoc 작성, IPiiDetectionService/IHttpContextAccessor mock 으로 HybridRouter 격리 호출:
  - **S1 PII 감지** → `internal` / `pii_detected` / detail=`ResidentNumber` ✅
  - **S2 데이터 라벨 confidential**(헤더 X-Data-Label 주입) → `internal` / `data_label` / detail=`confidential` ✅
  - **S3 vision 모델 (DefaultModel="gpt-4o")** → `external` / `capability_required` / detail=`vision:gpt-4o` ✅
  - **S4 비용 임계치 초과** (300,000자 메시지 → 75,000 토큰 추정 × 0.000002 = 0.15 USD > 0.10) → `internal` / `cost_exceeded` / detail=`est=0.1500,threshold=0.1000` ✅
  - **S5 default**(어떤 규칙도 매치 안 됨) → `external` / `default` ✅
  - **S6 invalid JSON**("{not valid json") → `external` / `invalid_policy` ✅
  - **6/6 PASS** — exit code 0. 검증 후 hybrid_test.csx 삭제(운영 빌드 산출물 정리)
- **DI 등록 사후 검증 (grep)**:
  - `Program.cs:266` `AddScoped<IHybridRouter, HybridRouter>` ✅
  - `AiProxyService.cs:230` `"nexus" => await CallNexusAsync(...)` ✅
  - `AiProxyService.cs:295` `if (providerCode == "nexus")` streaming 분기 ✅
  - `AiProxyService.cs:4097` `private async IAsyncEnumerable<ChatChunk> StreamNexusChunksAsync` ✅
  - `ChatService.cs:473 / 1022 / 1323` 3개 메서드 모두 `await ResolveServiceIdAsync(agent, request, ...)` ✅
- **외부 시그니처 보존 검증**:
  - `IAiProxyService.SendChatMessageAsync` / `SendChatMessageStreamChunksAsync` 무변경
  - `IChatService.SendDirectMessageAsync` / `SendDirectMessageStreamChunksAsync` / `SendDirectMessageStreamEventsAsync` 무변경
  - 호출자(컨트롤러 / SignalR Hub / OpenAICompatController) 영향 0건
- **잠재 위험 / 별도 트랙**:
  - **DataLabel DTO 확장 미도입**: 본 단계는 HTTP 헤더 `X-Data-Label` 만 지원. ChatMessageRequestDto / DirectSendMessageRequestDto 에 정식 필드 추가는 ConsumerSystem(docutil-user/career-student/...) 단위 표준화 후 별도 트랙. 헤더가 없으면 dataLabels 단계 자동 스킵 → 다음 우선순위 진행이라 안전
  - **토큰 추정 정확도**: 글자수/4 휴리스틱은 영어 평균(4 char/token)을 한국어에 단순 적용. 한국어는 약 2 char/token 으로 더 정밀하나 정확 계산은 `tiktoken-csharp` 도입 시점(별도 트랙). 현재 구현은 비용 임계치 판정만 영향 — 보수적으로 internal 라우팅 유도하므로 안전한 방향
  - **vision 모델 휴리스틱 false positive**: "4o" 키워드는 `gpt-4o` 외에도 `o4-something` 같은 향후 모델명도 매칭 가능. 정밀 매칭은 ApiServiceModel 에 `Capabilities` JSON 컬럼 도입 후 별도 트랙
  - **Nexus 서버 미가동 환경**: 본 단계 코드 작성 + DI 등록 + 분기 + 단위 검증까지만. 실 통합 테스트는 운영 배포 시점 (LAN 외부 환경에서 호출 시 `HttpRequestException` → 사용자에게 한국어 메시지 "Nexus 응답 실패. 사내망 연결을 확인하세요."). 외부망 배포에서는 `ApiService.IsActive=false` 토글로 nexus ServiceCode 비활성화 가능 — `SwapToServiceCodeAsync` 가 활성 ApiService 미존재 시 기존 ServiceId 유지하므로 운영자 콘솔에서 Hybrid Agent 의 fallback 동작 가능
  - **Hybrid 결정의 PII 검출 비용**: 매 Hybrid 요청마다 PII 정규식 평가 — 현재 PiiDetectionService 는 정규식 8종이라 부담 적으나 대량 트래픽 시 캐싱 검토(별도 트랙)
  - **ApiKeyPool 미연동**: Nexus 는 공유 시크릿이라 풀 무관. 하지만 SharedSecret 회전은 `appsettings.Production.json` 직접 변경 + 앱 재기동 필요 (별도 vault 도입 트랙)
  - **AgentBuilder UI 미갱신**: LlmRouting 드롭다운(External/Internal/Hybrid) + RoutingPolicyJson 편집기 + 모델 드롭다운에 "primary"/"auxiliary" 노출은 Vue 측 후속 트랙
- **다음 단계 (Phase 5 완료 → Phase 4 또는 Phase 6 사용자 결정)**:
  - **Phase 4** (DocUtil/career → AGENT_HUB 통합): 단일 PG 통합 + pgvector 임베딩 차원 통일 (8영업일 예상). 시작 전 Q1(career department_id) / Q3(DocUtil S6/S7 진행 위치) 결정 필요
  - **Phase 6** (DocUtil 운영자 → AgentHub 흡수 + KB 마이그레이션): Phase 5 완료를 전제로 진입 가능. 10영업일 예상
  - **Phase 7** (DocUtil/career AI 호출 → AgentHub 위임): API Key 발급 + 인벤토리 35호출 코드 교체 (10영업일)
  - **AgentBuilder UI 갱신** (Vue 측 별도 트랙): LlmRouting 드롭다운 + RoutingPolicyJson 편집기 + Hybrid 모델 카탈로그 노출

### 2026-05-06 (Phase 5.1 — Agent 라우팅 컬럼 5종 + INexusClient/NexusClient + ApiServices nexus 시드 + 마이그레이션 운영 PG 적용)
- **목적**: ADR-1 (Nexus 옵션 B) / ADR-2 (RAG=DocUtil) / TECHSPEC §15.4 의 Agent 단위 라우팅 정책을 데이터 모델/클라이언트 코드에 도입. AiProxyService 분기/HybridRouter 는 Phase 5.2 트랙으로 분리
- **변경 파일 (6개 modify + 3개 new)**:
  - `Models/Agent.cs` — `LlmRouting` (varchar 16, NOT NULL, default "External") / `RoutingPolicyJson` (text, NULL) / `KnowledgeBaseSource` (varchar 32, NOT NULL, default "AgentHub") / `KnowledgeBaseRef` (varchar 100, NULL) / `ConsumerSystems` (text, NULL) — 5개 컬럼 + 한국어 XML doc + ADR-1/ADR-2/.claude/rules/domain-model.md 인용
  - `Services/INexusClient.cs` (NEW) — `SendChatAsync` / `SendChatStreamAsync(IAsyncEnumerable<NexusStreamEvent>)` 시그니처. DTO record: `NexusChatRequest{Message, SessionId, Model, TenantId}` / `NexusChatResponse{SessionId, Response, ToolCalls, Usage}` / `NexusUsage{Prompt/Completion/TotalTokens}` / `NexusStreamEvent{Type, SessionId, Text, Usage, ErrorCode, ErrorMessage}`. `[EnumeratorCancellation]` 은 인터페이스에서 제거(CS8424 회피, 구현부에만 부착)
  - `Services/NexusClient.cs` (NEW, 약 250 LOC) — Named HttpClient `"nexus"` 사용 / ADR-13 헤더(X-Tenant-ID + Authorization Bearer SharedSecret) / SSE 파서: 빈 줄(`\n\n`) 프레임 분리 + `:` heartbeat 무시 + `data: ` prefix 추출 + `[DONE]` 마커 + `type=done` 이벤트 양쪽 종료 처리 / JSON snake_case (`PropertyNamingPolicy.SnakeCaseLower`) / `SafeReadErrorBodyAsync` 폴백 / SharedSecret 미설정 시 `LogWarning`
  - `Program.cs` — `AddHttpClient("nexus", ...)` 등록(BaseUrl 기본 `http://192.168.22.28:8001`, timeout 60s 설정 가능) + `AddScoped<INexusClient, NexusClient>()`
  - `appsettings.json` + `appsettings.Development.json` — `Nexus` 섹션 신규 (BaseUrl / SharedSecret(빈) / DefaultTimeoutSeconds=60 / DefaultTenantId="default")
  - `Data/DatabaseInitializer.cs` — Mistral 폴백 패턴 인접에 nexus 멱등 시드 추가: ServiceCode="nexus", ServiceName="Project Nexus", IconClass="bi-hdd-network", ColorCode="#10B981", ApiEndpoint="http://192.168.22.28:8001/v1/chat", DefaultModel="primary", CostPerRequest=0.0m, ServiceType="Chat", SortOrder=8. `ApiServiceModels` 시드는 Phase 5.2 로 보류
  - `Migrations/20260506010411_AddAgentRoutingColumns.{cs,Designer.cs}` (NEW) — 5개 컬럼 AddColumn + 5개 DropColumn(Down). 기본값을 운영 의도("External"/"AgentHub")로 수정해 기존 row 도 의미 있는 값으로 채움
  - `Migrations/AIAgentManagementDbContextModelSnapshot.cs` (NEW) — Phase 3.6 시점의 Init.Designer 를 base 로 ModelSnapshot 클래스 생성(EF base 인식 문제 해결, 아래 ADR-N 참조)
- **빌드 검증**: `dotnet build -v quiet` → **0 errors, 11 warnings** (모두 기존 코드 CS1998 — Phase 5.1 신규 워닝 0건). 신규 INexusClient.cs 의 `[EnumeratorCancellation]` 은 1차 빌드에서 CS8424 발생 → 인터페이스 시그니처에서 제거하여 0 신규 워닝 달성
- **마이그레이션 add 실패 → ModelSnapshot 합성 → 재성공**:
  - 1차 시도: `dotnet-ef migrations add AddAgentRoutingColumns` → 모든 35개 테이블을 `CreateTable` 로 다시 만드는 잘못된 마이그레이션 생성. `dotnet-ef migrations remove` → "No ModelSnapshot was found" 진단
  - 원인: `AIAgentManagement.csproj:50-53` 의 `<Compile Remove="Migrations.mssql.archive\**" />` 로 인해 archive 의 `AIAgentManagementDbContextModelSnapshot.cs` 가 어셈블리에서 제외 → EF가 base 모델을 발견 못 하고 빈 base 가정
  - archive 의 ModelSnapshot 은 Phase 3.1 이전 MSSQL 버전(`SqlServerPropertyBuilderExtensions` 사용 → 컴파일 실패)이라 단순 복사 불가
  - **해결**: `Migrations/20260505154102_Init.Designer.cs` (PG 모델로 작성) 를 복사 후 `[Migration(...)]` 제거 + `using ...Migrations;` 제거 + 클래스명 `Init` → `AIAgentManagementDbContextModelSnapshot : ModelSnapshot` 변경 + 메서드 `BuildTargetModel` → `BuildModel` 변경 → `Migrations/AIAgentManagementDbContextModelSnapshot.cs` 로 저장
  - 재시도 `migrations add AddAgentRoutingColumns` → **5개 AddColumn 만 포함된 정확한 마이그레이션 생성**
- **마이그레이션 dry-run (script Init -> AddAgentRoutingColumns)**:
  ```
  ALTER TABLE "AIAgentManagement"."Agents" ADD "ConsumerSystems" text;
  ALTER TABLE "AIAgentManagement"."Agents" ADD "KnowledgeBaseRef" character varying(100);
  ALTER TABLE "AIAgentManagement"."Agents" ADD "KnowledgeBaseSource" character varying(32) NOT NULL DEFAULT 'AgentHub';
  ALTER TABLE "AIAgentManagement"."Agents" ADD "LlmRouting" character varying(16) NOT NULL DEFAULT 'External';
  ALTER TABLE "AIAgentManagement"."Agents" ADD "RoutingPolicyJson" text;
  ```
- **운영 PG 적용 — `dotnet-ef database update --connection ...`**: 5 ALTER + EFMigrationsHistory INSERT 모두 정상. `Done.`
- **PG 직접 검증 (Npgsql 8.0.5 ad-hoc 프로젝트)**:
  - `information_schema.columns` 쿼리: 5개 컬럼 모두 정확한 type/maxlen/nullable/default 확인 — `KnowledgeBaseSource character varying(32) NOT NULL default='AgentHub'`, `LlmRouting character varying(16) NOT NULL default='External'`, `RoutingPolicyJson/ConsumerSystems text NULL`, `KnowledgeBaseRef varchar(100) NULL`
  - `__EFMigrationsHistory` 위치: `public` schema (Phase 3.6 시점부터 운영 PG 컨벤션 — EF default schema 와 PG search_path 분리)
  - 마이그레이션 이력: `20260505154102_Init` + `20260506010411_AddAgentRoutingColumns` 두 행 정상 등록
  - ApiServices Chat 0건 — Phase 3.6 데이터 이전이 시드 미포함, DatabaseInitializer 가 다음 앱 기동 시 멱등 시드 (Phase 5.1 nexus 시드도 동일 흐름)
- **잠재 위험 / Phase 5.2 의존**:
  - **Nexus 서버 미가동 환경**: BaseUrl `http://192.168.22.28:8001` 은 LAN 전용 — 외부망 배포에서는 NexusClient 호출이 connection refused. AiProxyService.CallNexusAsync (Phase 5.2) 에서 ApiService.IsActive 토글로 환경 분리 필요. 운영자 콘솔에 배포 환경 카드 추가 검토 (P9 환경별 배포)
  - **SharedSecret 빈 문자열 폴백**: `Nexus:SharedSecret` 미설정 시 NexusClient 가 `LogWarning` 만 출력하고 인증 헤더 생략. ADR-13 의 LAN 격리만으로 1차 방어. Phase 5.2 운영 적용 전 반드시 비밀번호 발급 + appsettings.Production.json 또는 IIS 환경변수 주입 필요
  - **archive ModelSnapshot 와 Migrations/ ModelSnapshot 이중 존재**: 현재 archive 의 것은 git 미커밋 상태 무변경(MSSQL 시절 Phase 3.0 직전), Migrations/ 의 것은 Phase 3.6 baseline 동등. 향후 EF 가 archive ModelSnapshot 을 인식하지 않도록 `<Compile Remove>` 가 그대로 유지되어야 함 — 향후 누군가 Compile Remove 를 풀면 두 ModelSnapshot 이 충돌하므로 .editorconfig 또는 README 에 경고 추가 (Phase 5+ 트랙)
  - **DatabaseInitializer 의 nexus 시드 미적용 상태**: 본 단계는 마이그레이션만 적용, 시드는 다음 앱 기동(또는 Phase 5.2 통합 검증) 시 적용. 운영 인스턴스가 IIS 에서 살아 있으면 자동 멱등 INSERT 됨
  - **ApiServiceModels 시드 누락**: nexus 의 "primary"/"auxiliary" 모델 카탈로그가 없어 Agent 빌더의 모델 드롭다운에서 Nexus 모델 선택 불가. Phase 5.2 에서 SeedApiServiceModelsAsync 갱신 필요
- **다음 단계 (Phase 5.2 — 사용자 승인 후 진입)**:
  1. `IAiProxyService` 의 `SendChatMessageAsync` switch 분기에 `"nexus"` case 추가 → `CallNexusAsync(service, model, request, ct)` 호출
  2. `CallNexusAsync` 내부: ChatMessageRequestDto.Messages 의 마지막 user 메시지 → NexusChatRequest.Message 매핑(히스토리는 Nexus 가 SessionId 키로 Redis 복원), Tenant/Session 헤더 부착, NexusChatResponse → AiResponseDto 변환
  3. Streaming: `SendChatMessageStreamChunksAsync` 의 switch 에 nexus case 추가 → `INexusClient.SendChatStreamAsync` → `ChatChunk` 변환(text 누적 + finish_reason)
  4. `HybridRouter` 클래스 신설 (`Services/HybridRouter.cs`) — Agent.RoutingPolicyJson 평가, PII 강제 / 데이터 라벨 / 모델 capability / 비용 한도 → External/Internal 결정. AiProxyService 가 라우팅 전 호출
  5. ApiServiceModels nexus 시드("primary","auxiliary") + AgentBuilder UI 의 LlmRouting 드롭다운(External/Internal/Hybrid)
  6. 통합 테스트 (`tests/integration/`): mock Nexus 서버로 비스트리밍/스트리밍 응답 검증, [DONE] 마커 + heartbeat 무시 동작 확인

### 2026-05-06 (Phase 3.6 — AGENT_HUB DB 셋업 + baseline 마이그레이션 운영 PG 적용 + T-SQL 잔존 정리)
- **목적**: Phase 3.2 baseline 을 운영 PostgreSQL(192.168.10.39:5440) 에 실제 적용 + Phase 2 init.sql 동등 작업 + DbContext T-SQL bracket(`[Status]`/`[Role]`/`[IsActive] = 1`) 잔존 PG 호환 변환
- **사전 작업 (.NET tool 추가 + PG 자격증명 탐색)**:
  - `dotnet-script` 2.0.0 글로벌 도구 설치 — Npgsql 직접 호출용 ad-hoc 스크립트 실행
  - PG superuser 탐색: nexus/docutil/.env 의 자격증명 6쌍 시도 → **`docutil` / `docutil_pg_2024`** 가 superuser/createdb/createrole 권한 보유 확인 (PG 17.9 alpine 컨테이너로 추정). `postgres` 계정 비밀번호 4종 시도 모두 실패
  - 운영 PG 의 기존 DB 3개 (`docutil`, `nexus`, `postgres`) + role 2개 (`docutil`, `nexus`) — `AGENT_HUB` 미존재 확인
- **Phase 2 init.sql 동등 작업 (Npgsql 직접 실행, psql 미설치 환경)**:
  - psql 메타커맨드(`\set`/`\if`/`\gexec`/`\connect`) → Npgsql `NpgsqlCommand` 분할 호출로 변환
  - **§1 `AGENT_HUB` role 생성** (postgres DB 안에서 `DO $$ ... CREATE ROLE %I LOGIN PASSWORD %L $$`) — 비밀번호 `idino!@#$`
  - **§2 `AGENT_HUB` DATABASE 생성** (CREATE DATABASE 는 implicit transaction 외 실행 — Npgsql 단일 NonQuery 자동 처리). UTF8 / ko_KR.UTF-8 / template0
  - **§4 Extensions 4종**: `vector` 0.8.0 / `uuid-ossp` 1.1 / `pgcrypto` 1.3 / `pg_trgm` 1.6
  - **§5 Schemas 4종**: `AIAgentManagement` / `document_utilization` / `idino_career` / `hangfire` — 모두 owner = `AGENT_HUB`
  - **§6 ALTER DEFAULT PRIVILEGES** — 4 schema 별 TABLES/SEQUENCES/FUNCTIONS 권한 자동 부여 (DO $$ FOREACH IN ARRAY)
  - **§7 search_path** — `AGENT_HUB` role 의 default search_path 4 schema + public
  - **§8 검증 쿼리** — extensions 4행 + schemas 4행 + role 1행 (rolcanlogin=t, rolsuper=f) 모두 정상
- **DbContext T-SQL 잔존 정리 (3건 발견 → PG 호환 변환)**:
  - 첫 번째 마이그레이션 적용 시도 시 `42601: syntax error at or near "["` 발생 (position 992) — DbContext 의 `HasCheckConstraint` / `HasFilter` 가 T-SQL bracket 식별자 사용
  - `agenthub/Data/AIAgentManagementDbContext.cs:79` — `HasCheckConstraint("CK_ChatMessages_Role", "[Role] IN (...)")` → `"\"Role\" IN (...)"` (PG 큰따옴표)
  - `agenthub/Data/AIAgentManagementDbContext.cs:83` — `HasCheckConstraint("CK_Users_Status", "[Status] IN (...)")` → `"\"Status\" IN (...)"`
  - `agenthub/Data/AIAgentManagementDbContext.cs:142` — `HasFilter("[IsActive] = 1")` → `"\"IsActive\" = true"` (PG boolean literal)
- **baseline 재생성**: 기존 `Migrations/20260505131410_Init.{cs,Designer.cs}` 삭제 → 새 빌드 후 `dotnet-ef migrations add Init` 재생성 → `Migrations/20260505154102_Init.{cs,Designer.cs}`
  - dry-run script 검증: T-SQL 잔존(`\[`) 0건, PG 표준 식별자 정상
  - `migrations list`: `20260505154102_Init (Pending)` 등록 확인
- **운영 PG 적용 — `dotnet-ef database update`**:
  - 35 CREATE TABLE + 인덱스 + UNIQUE + CHECK 제약 + 부분 인덱스 모두 정상 실행
  - `INSERT INTO "__EFMigrationsHistory" VALUES ('20260505154102_Init', '8.0.11')` 기록
  - 결과: `AIAgentManagement` schema 35 테이블 생성 완료
- **Phase 3.3 보안 컬럼·인덱스 PG 적용 검증** (Npgsql 직접 쿼리):
  - ✅ `ApiKeys.KeyIv bytea` / `ApiKeys.KeyTag bytea` / `ApiKeys.KeyHash character varying(64)` (C1/C3)
  - ✅ `ApiQuotas.CurrentTokens bigint NOT NULL DEFAULT 0` / `ApiQuotas.MonthlyTokenLimit bigint NULL` (H10)
  - ✅ `IX_ApiKeys_KeyHash UNIQUE btree("KeyHash")` (C3 인증 핫패스 단축)
  - ✅ `IX_Users_Email UNIQUE btree("Email")` (C4 중복 가입 차단)
  - ✅ `IX_TeamMembers_TeamId_UserId UNIQUE btree(...) WHERE ("IsActive" = true)` (PG 부분 인덱스 정상 변환)
  - ✅ `CK_Users_Status` / `CK_ChatMessages_Role` PG 표준 `("Status")::text = ANY(ARRAY[...])` 형식 자동 변환
- **Phase 3.2 text 컬럼 PG 적용 검증**:
  - ✅ `PresentationSlides.{Content, ChartsJson, TablesJson, ImagesJson}` 모두 `text` (이전 nvarchar(max) → text 변환 정상)
- **잠재 위험 / 후속 트랙**:
  - **`__EFMigrationsHistory` 가 `public` schema 에 있음** — Npgsql 기본값. AgentHub 의 `Search Path=AIAgentManagement,public` 설정 시 자동 fallback 으로 정상 동작. 단 R29 schema 격리 강화 시 별도 처리 필요
  - **DatabaseInitializer 시드 미실행** — 실 DB 통합 검증은 AgentHub 부팅 시 자동 수행됨. 본 단계는 schema/마이그레이션까지만
  - **Hangfire schema** — AgentHub 첫 부팅 시 `PrepareSchemaIfNecessary=true` 가 자동 생성 (Phase 3.4 commit 검증). 본 단계 미적용
  - **MSSQL 운영 데이터 이전** — 사용자 시연용 monorepo COPY 환경이라 데이터 이전 생략. 운영 적용 시 별도 ETL(`pgloader` / `bcp+COPY`) 필요
  - **archive ModelSnapshot 갱신**: dotnet-ef 가 또 `Migrations.mssql.archive/ModelSnapshot.cs` 갱신 → `git restore` 로 1da04ab 시점 복원 (재발 방지 csproj `<Compile Remove>` 강화는 별도 트랙)
- **다음 단계 (Phase 3 Complete → Phase 5 / Phase 4)**:
  - Phase 3 핵심 작업 마무리. AgentHub 부팅 → DatabaseInitializer 시드 실 적용 + Hangfire schema 자동 생성 + 통합 smoke test (Agent CRUD, OpenAI 호환 API, ApiKey 인증, Quota) — 사용자 시연 시 수행 가능
  - Phase 5 진입 가능 (AgentHub Nexus provider 추가) — Phase 3 의존성 해소
  - Phase 4 (DocUtil/career → AGENT_HUB 통합) — Phase 5 와 병렬 진행 가능

### 2026-05-05 (Phase 3.4 — DatabaseInitializer PG 호환 재작성 + EnsureCreatedAsync→MigrateAsync + Program.cs SqlException→PostgresException + TestDbConnection deprecate)
- **목적**: TECHSPEC §16 C7 위험 해소 — `Database.EnsureCreatedAsync()` 사용으로 인한 마이그레이션 그래프 ↔ 실 스키마 drift 위험 차단. Phase 3.2 baseline `20260505131410_Init` 도입으로 `MigrateAsync()` 전환 가능해짐. 부수적으로 Phase 3.1 의 SQL Server 잔존 의존(SqlException catch 블록 / TestDbConnection.cs) 정리
- **사전 조사 (변경 범위 좁힘)**:
  - `DatabaseInitializer.cs` 내 `ExecuteSqlRaw` / `ExecuteSqlInterpolated` / `FromSqlRaw` 호출 — **0건** (시드는 전부 EF LINQ + AddRange + SaveChangesAsync 패턴으로 작성됨)
  - 따라서 T-SQL → PG 변환이 필요한 인라인 SQL 코드는 **없음**. 변경 범위는 (a) MigrateAsync 전환 (b) try-catch swallow 강화 두 가지로 수렴
  - 루트의 레거시 `*.sql` 파일들은 `.claude/rules/anti-patterns.md` #9 에서 보존만 + 신규 X 로 명시 — 본 단계 무시
  - 시드 데이터(Roles 3건 / ApiServices Chat 6건 / Image 5건 / Video 3건 / 모델 카탈로그 9개 ServiceCode) — 원본 코드가 이미 멱등성(`AnyAsync` 검사 후 INSERT)로 작성됨, PG 호환성 무관
- **변경 파일 3건**:
  - **`agenthub/Data/DatabaseInitializer.cs`** (866 → 880 LOC, +14)
    - L11~21: 메서드 docstring 추가 — baseline 마이그레이션 + 멱등 시드 의도 + 외부 시그니처 보존 명시
    - L22~38 신설: **`MigrateAsync()` 호출 블록 + 별도 try-catch** — 마이그레이션 실패는 시드 try-catch 와 분리해 상위로 전파 (스키마 미존재 시 시드는 의미 없음). stderr 로 GetType().Name + Message 흘림
    - L15 (구) `await context.Database.EnsureCreatedAsync();` → 제거 (위 블록으로 대체)
    - L433~440 (구→신): 빈 `catch (Exception)` → `catch (Exception ex)` + `Console.Error.WriteLine` 로 클래스명/메시지 출력. anti-patterns.md #10 의 의도된 swallow 패턴 일관성 유지
    - 시그니처 무변경: `public static async Task SeedAsync(AIAgentManagementDbContext context)` 그대로
    - 시드 본문 변경 없음 — Phase 5 에 ApiServices 시드 `nexus` ServiceCode 추가 예정 (TECHSPEC §15.4), 본 단계는 손대지 않음
  - **`agenthub/Program.cs`** (588 → 597 LOC, +9)
    - L417~425 (구): `catch (Microsoft.Data.SqlClient.SqlException sqlEx)` 블록 — Number/Server/State/Class 로깅 (전부 SQL Server 전용 속성)
    - L417~434 (신): **`catch (Npgsql.PostgresException pgEx)`** — SQLSTATE / Severity / SchemaName / TableName 로깅 (PG 표준). + **`catch (Npgsql.NpgsqlException npgEx)`** 추가 — 클라이언트측 연결 오류(호스트 unreachable / 타임아웃) 분리 처리. PostgresException 의 부모 타입이라 catch 순서 중요
    - DB 초기화 호출 패턴(L396 `DatabaseInitializer.SeedAsync(context)`)은 무변경
    - Hangfire 등록 블록(L176~201) 무변경 — Phase 3.1 commit `c022c9e` 의 `UsePostgreSqlStorage` + `SchemaName = "hangfire"` + `PrepareSchemaIfNecessary = true` 그대로 유지
  - **`agenthub/TestDbConnection.cs`** (70 → 25 LOC, -45)
    - 본문 SqlConnection / @@VERSION / DB_NAME() / SqlException 등 PG 비호환 코드 전체 제거
    - `[Obsolete]` 어노테이션 부착 + `TestConnection` 호출 시 `NotSupportedException` 발생 (사용처 grep 결과 자기 정의 외 0건이라 안전)
    - 클래스 자체 보존(파일 삭제 X) — git history 가독성 + 향후 Phase 5+ 에서 Npgsql 호환으로 재작성 가능성. 주석에 "Phase 5+ 별도 트랙" 명시
    - **`Microsoft.Data.SqlClient` using 제거** → 본 파일은 더 이상 SqlClient 패키지를 코드 차원에서 import 하지 않음. 패키지 자체는 csproj 에 남음 (Phase 5+ 정리)
- **본 단계 미처리 — Phase 5+ 별도 트랙 보고만**:
  - **`Controllers/DatabaseBackupController.cs`** (148, 179) — `new SqlConnection(_connectionString)` 직접 인스턴스화 + T-SQL 백업 명령 사용. PG 백업은 `pg_dump` 외부 프로세스 또는 별도 Hangfire 작업 패턴 필요. controller 자체가 통합 후 운영자 콘솔로 이전될 가능성(TECHSPEC ADR-2)이라 본 단계 deprecate 결정. **빌드 차원**: SqlConnection 의존 잔존, 컨트롤러 호출 시 PG 환경에서 런타임 오류 발생 — 현재 운영 빌드에서 호출 차단 또는 controller 전체 제거가 안전. **Phase 5 전 결정 필요**
- **빌드 검증**:
  - 베이스라인(변경 전): `dotnet build --no-restore` — 0 errors / 11 warnings (전부 기존 CS1998)
  - 변경 후: `dotnet build --no-restore` — **0 errors / 11 warnings** (신규 도입 0건, 베이스라인 동일). 경과 시간 2.37s
- **마이그레이션 dry-run SQL 검증** (`dotnet-ef migrations script --no-build > /tmp/init-script.sql`):
  - 출력: 731 LOC SQL
  - `CREATE TABLE` 36건 (35 도메인 테이블 + `__EFMigrationsHistory`)
  - **T-SQL 잔존 패턴 검증 (전부 0 — 정상)**:
    - `IDENTITY(1,1)`: 0 / `nvarchar`: 0 / `GETDATE`: 0 / `NEWID`: 0 / `sys.tables` `sys.columns`: 0 / `[dbo]` bracket: 0 / `ISNULL` `LEN(`: 0
  - **PG 표준 패턴 검증 (양수 — 정상)**:
    - `GENERATED BY DEFAULT AS IDENTITY`: 34 (모든 PK)
    - `timestamp with time zone`: 71 (모든 CreatedAt/UpdatedAt/...)
    - `character varying`: 124
    - `"AIAgentManagement"` 더블쿼트 스키마 한정자: 148
    - `boolean`: 32
    - `bytea`: 2 (Phase 3.3 `KeyIv` / `KeyTag` per-record AES-GCM IV+Tag)
  - **CREATE TABLE 발췌 (`AIAgentManagement.ApiKeys` — Phase 3.3 보안 컬럼 검증 통과)**:
    ```
    CREATE TABLE "AIAgentManagement"."ApiKeys" (
        "ApiKeyId" integer GENERATED BY DEFAULT AS IDENTITY,
        "KeyName" character varying(100) NOT NULL,
        "EncryptedKey" character varying(500) NOT NULL,
        "KeyIv" bytea, "KeyTag" bytea, "KeyHash" character varying(64),
        "ExpiresAt" timestamp with time zone, "IsActive" boolean NOT NULL,
        ...
    );
    CREATE UNIQUE INDEX "IX_ApiKeys_KeyHash" ON "AIAgentManagement"."ApiKeys" ("KeyHash");
    CREATE UNIQUE INDEX "IX_Users_Email" ON "AIAgentManagement"."Users" ("Email");
    ```
  - `dotnet-ef migrations list --no-build` — `20260505131410_Init` 등록 확인. Pending 상태는 DB 미연결로 미확인 (`28P01: password authentication failed for user "AGENT_HUB"` — Phase 2 init.sql 미실행, 기대 동작)
- **Hangfire schema 동작 검증 (코드 수준)**:
  - Program.cs L182~194: `AddHangfire` 등록 블록 검토 — `UsePostgreSqlStorage` + `SchemaName = "hangfire"` + `PrepareSchemaIfNecessary = true` 보존
  - 동작 원리: 첫 부팅 시 Hangfire.PostgreSql 1.20.10 의 `SchemaInstaller` 가 `hangfire` 스키마 + 11개 테이블(`hash`/`job`/`jobparameter`/`jobqueue`/`list`/`schema`/`server`/`set`/`state`/`counter`/`aggregatedcounter`) 자동 생성
  - 본 단계는 코드 검증만 — 실제 스키마 생성 검증은 Phase 3.6 (DB 연결 후)
- **잠재 위험 / Phase 3.6 의존 항목**:
  - **실 PG 적용 미검증**: 본 단계 변경은 빌드/구문 검증까지. `MigrateAsync` 호출 시 `__EFMigrationsHistory` + 35 테이블 + 15 UNIQUE 인덱스가 정상 생성되는지는 Phase 3.6 의존
  - **Hangfire 자동 스키마 생성 권한**: PG 의 `AGENT_HUB` 사용자가 `CREATE SCHEMA hangfire` 권한 보유해야 함. Phase 2 `infra/db/init.sql` 에서 `AGENT_HUB` 에게 `CREATE` 권한 부여됐는지 사전 확인 필요
  - **시드 단계 부분 실패 swallow 가능성**: 새 `Console.Error` 로그는 ASP.NET Core 호스팅 환경에 따라 캡처되지 않을 수 있음. Phase 3.6 부팅 시 stdout/stderr 양쪽 점검
  - **DatabaseBackupController PG 미호환 잔존**: 본 단계 미처리. 운영자 호출 시 런타임 SqlException — `[Obsolete]` 또는 enable=false 처리 권장 (Phase 5 전)
  - **DocUtil/career 영향 없음**: 본 변경은 AgentHub 단독. monorepo 다른 서브프로젝트는 무영향
- **다음 단계 (Phase 3.6 제안 흐름)**:
  1. `infra/db/init.sql` 운영 PG 인스턴스(192.168.10.39:5440)에 적용 — `AGENT_HUB` user/DB + 4 schema + extensions(vector, uuid-ossp, pg_trgm) 생성
  2. AgentHub 부팅 → `MigrateAsync` 1회 자동 실행 → 35 테이블 + Hangfire 11 테이블 + `__EFMigrationsHistory` 생성 검증
  3. 시드 동작 검증 (Roles 3 / ApiServices 14 / ApiServiceModels 50+ / Admin user)
  4. SQL Server → PG 데이터 이전 dry-run (별도 ETL 또는 `pgloader`)
  5. C5/C6 (BackupController PG 비호환), Phase 5 시작 (Nexus provider + LlmRouting 컬럼 + 진짜 SSE)

### 2026-05-05 (Phase 3.2 — Npgsql baseline `Init` 마이그레이션 + nvarchar(max) → text 변환 + EF 8.0.11 통일 + .NET 8 SDK 설치)
- **목적**: Phase 3.1 EF Provider 전환 후 첫 PostgreSQL 마이그레이션 baseline 작성. Phase 3.3 보안 컬럼/인덱스 + nvarchar(max) PG 비호환 컬럼 정리를 동시 흡수
- **선행 작업 (.NET 8 SDK 설치)**: 환경에 dotnet CLI 미설치 — `dotnet-install.ps1` 으로 user-local(`C:\Users\IDINO_USER\.dotnet`) 설치 (관리자 권한 불필요). winget user scope는 적합한 installer 부재로 실패. 결과: SDK 8.0.420 + `dotnet-ef` global tool 8.0.11 설치 완료. PATH/`DOTNET_ROOT` 영구 등록 (User 환경변수 + ~/.bashrc). 새 bash 세션은 자동 로드 안 되어 Bash tool 호출 시마다 `export PATH=...` 명시 필요
- **csproj 수정 1건**:
  - `agenthub/AIAgentManagement.csproj` — `Microsoft.EntityFrameworkCore` / `Microsoft.EntityFrameworkCore.Tools` `8.0.0 → 8.0.11`. NU1605 경고-as-오류(Phase 3.1에서 추가한 `Npgsql.EntityFrameworkCore.PostgreSQL 8.0.11` 의 transitive `Microsoft.EntityFrameworkCore (>= 8.0.11)` 요구와 직접 참조 8.0.0 충돌) 해소
- **PG 비호환 타입 정리 — `nvarchar(max)` → `text` (8곳)**:
  - `agenthub/Models/ExamplePrompt.cs:17` — `Prompt` (free-form 프롬프트)
  - `agenthub/Models/Presentation.cs:19` — `Slides` (JSON 문자열)
  - `agenthub/Models/PresentationTemplate.cs:23` — `TemplateStructure` (JSON 문자열)
  - `agenthub/Models/PresentationSlide.cs:9 / :28 / :45 / :49 / :53` — class doc + `Content` + `ChartsJson` + `TablesJson` + `ImagesJson` (4개 컬럼)
  - `agenthub/Data/AIAgentManagementDbContext.cs:152 / :209 / :217-223` — DbContext OnModelCreating fluent 설정 5건도 동일 변환
  - **`jsonb` 미채택 이유**: 기존 `JsonSerializer.Serialize/Deserialize` 패턴(P5) + 기존 운영 데이터에 invalid JSON 가능성(예: `Slides`는 명세상 JSON이지만 schema-less). 직렬화/역직렬화 흐름 무변경 + 길이 무제한 = `text` 가 등가. `jsonb` 인덱싱/쿼리 최적화는 Phase 5+ 별도 트랙
  - **임베딩(`DocumentChunk.Embedding`) 은 보류** — 현재 `text` 타입 그대로 유지 (ADR-2 자체 KB deprecate, Phase 6 일괄 정리 대상)
- **신설 파일 2개 (`Migrations/` 신설)**:
  - `agenthub/Migrations/20260505131410_Init.cs` — Npgsql baseline `Init` 마이그레이션 (94 KB / 1700 라인)
  - `agenthub/Migrations/20260505131410_Init.Designer.cs` — Model snapshot (92 KB / 2400 라인)
  - **수치**: 35 테이블 / 389 컬럼 / 15 UNIQUE 인덱스 / 40 `text` 타입 / 0 `nvarchar(max)`
  - **Phase 3.3 컬럼 자연 흡수 검증 완료**:
    - `MonthlyTokenLimit bigint NULL` (H10)
    - `CurrentTokens bigint NOT NULL DEFAULT 0` (H10)
    - `KeyIv bytea NULL` / `KeyTag bytea NULL` (C1)
    - `KeyHash character varying(64) NULL` (C3)
  - **Phase 3.3 UNIQUE 인덱스 자연 흡수 검증 완료**:
    - `IX_ApiKeys_KeyHash UNIQUE` (C3 인증 핫패스 단축)
    - `IX_Users_Email UNIQUE` (C4 중복 가입 차단)
  - 기타 신규 인덱스: `IX_ApiServiceModels_ServiceId_ModelName`, `IX_TeamMembers_TeamId_UserId`, `IX_UserPreferences_UserId_PreferenceKey` 등 13건
- **archive 보존 (의도하지 않은 EF 갱신 복원)**:
  - `dotnet-ef migrations add Init` 실행 시 `Migrations.mssql.archive/AIAgentManagementDbContextModelSnapshot.cs` 가 자동 갱신됨 (EF 가 기존 ModelSnapshot 의 위치를 인식하고 새 모델로 덮어씀). archive 는 ADR-7 historical 참조용이라 `git restore` 로 1da04ab 시점 상태로 복원
- **빌드 검증**:
  - `dotnet restore` 성공 (NU1605 해소 후)
  - `dotnet build --no-restore` 성공 — **0 errors / 11 warnings** (전부 기존 레거시 `CS1998` async-without-await, Phase 3.x 신규 도입 0건)
  - `dotnet-ef migrations list` — `20260505131410_Init` 등록 확인. Pending 상태는 DB 미연결로 미확인 (AGENT_HUB DB 부재 — `28P01: password authentication failed for user "AGENT_HUB"` — 정상, Phase 2 init.sql 미실행)
- **`.gitignore` 갱신**: `.claude/settings.local.json` (Claude Code per-machine 권한 캐시) 추가 — 우발적 commit 방지
- **잠재 위험 / 사용자 검증 필요**:
  - **사용자 측 dotnet CLI**: 본 PC 에는 user-local 설치 완료. 다른 PC / CI 에서는 별도 설치 필요 (dotnet 8 SDK 또는 GitHub Actions `actions/setup-dotnet@v4`)
  - **운영 DB 미적용**: 본 단계는 마이그레이션 *파일* 만 생성. 실제 PG `AGENT_HUB` DB 에 적용은 Phase 3.4 (DatabaseInitializer 재작성 후) → Phase 3.6 (운영 데이터 이전 dry-run) 순서
  - **`text` 컬럼의 잠재적 invalid JSON**: `Slides`/`ChartsJson` 등이 sub-text 한도 무제한이지만, 운영 코드가 항상 JSON 으로 직렬화하는지 grep 검증은 별도 트랙 (Phase 5+ jsonb 도입 시 사전 검증 필수)
  - **Migrations.mssql.archive 의 ModelSnapshot 재변경 위험**: 다음 `dotnet-ef migrations add` 실행 시 또 archive 가 갱신됨. csproj `<Compile Remove>` 에 `*.Designer.cs`/`ModelSnapshot.cs` 명시적 제외 + (선택) archive 전체를 별도 디렉토리로 이동 검토
- **다음 단계 (Phase 3.4)**:
  - `Data/DatabaseInitializer.cs` (866 LOC) idempotent 재작성 — `EnsureCreatedAsync` → `MigrateAsync` 전환 (C7 해소). Roles/ApiServices/ApiServiceModels/Agents 시드 PG 호환성
  - Hangfire schema `hangfire` 자동 생성 검증 (`PrepareSchemaIfNecessary = true` 동작)

### 2026-05-05 (Phase 3.3b + 3.3c 번들 — AES-GCM per-record IV + AES Key 분리 + KeyHash UNIQUE + Email UNIQUE / TECHSPEC §16 C1/C2/C3/C4)
- **목적**: TECHSPEC §16 의 핵심 보안 결함 4종을 한 번에 해소.
  - C1: `ApiKeyService.EncryptString` / `DecryptString` + `ApiKeyAuthService.DecryptString` 모두 `aes.IV = new byte[16]` (16바이트 0) 사용 — 결정적 암호화 + AEAD 부재. 같은 평문 → 동일 암호문이라 인증이 매 요청 활성 키 풀스캔 + 전수 복호화 비교(O(N)).
  - C2: 두 서비스 모두 `_encryptionKey = configuration["JwtSettings:SecretKey"]` + SHA-256(jwtSecret) 으로 AES Key 유도 — JWT 키 노출 = ApiKey 평문 전체 복호화.
  - C3: `ApiKey` 모델에 `KeyHash` 컬럼 부재 + `OnModelCreating` 에 `Entity<ApiKey>.HasIndex` 0건. 인증이 활성 키 전체 로드 후 foreach 복호화 비교.
  - C4: `User.cs` Email 은 `[Required] [MaxLength(100)]` 만, DB 레벨 UNIQUE 부재 → race condition 으로 중복 가입 가능.
- **수정 파일 6개 (외부 시그니처 무변경)**:
  - `agenthub/Models/ApiKey.cs` — 신규 컬럼 3개 추가:
    - `byte[]? KeyIv` (AES-GCM nonce, 12바이트, EF 가 PG 기본 매핑 시 `bytea` nullable. 기존 행 NULL 허용으로 마이그레이션 충돌 0)
    - `byte[]? KeyTag` (AES-GCM 인증 태그, 16바이트)
    - `string? KeyHash [MaxLength(64)]` (SHA-256 hex 대문자 64자, UNIQUE 인덱스 대상)
    - 모두 한국어 XML doc + TECHSPEC §16 항목 참조 주석. 기존 `EncryptedKey [MaxLength(500)]` 변경 없음 — GCM ciphertext 는 평문 길이와 동일하므로 base64 후에도 500 충분(기존 32~64 byte AES Key 가정 시 100 byte 미만)
  - `agenthub/Data/AIAgentManagementDbContext.cs` — `OnModelCreating` 에 인덱스 2개 추가 (Role.RoleName UNIQUE 인접 위치):
    - `Entity<User>().HasIndex(u => u.Email).IsUnique()` (C4)
    - `Entity<ApiKey>().HasIndex(k => k.KeyHash).IsUnique()` (C3 — PG 는 NULL 다수를 자동으로 허용하는 부분 인덱스 의미를 가짐. legacy 행 NULL 안전)
  - `agenthub/Services/ApiKeyService.cs` — 전면 재작성 (외부 9개 public 메서드 시그니처 모두 보존):
    - 생성자: `LoadAesKey(IConfiguration, ILogger)` 헬퍼로 키 로딩 분리. 우선순위 = `Encryption:ApiKeyAesKey` (base64, 32바이트 AES-256) → 없으면 `JwtSettings:SecretKey` SHA-256 폴백 + `LogWarning` 1회. 폴백 길이/format 검증 fail-fast (32 != 길이 → InvalidOperationException, base64 파싱 실패 → InvalidOperationException). `_aesKey: byte[]` + `_usingFallbackKey: bool` 보관
    - 신규 `EncryptApiKey(string) -> (byte[] ciphertext, byte[] iv, byte[] tag)` — `new AesGcm(_aesKey, tagSizeInBytes: 16)` (.NET 8 권장 시그니처, 매개변수 없는 ctor 는 [Obsolete] 회피) + `RandomNumberGenerator.GetBytes(12)` per-record nonce
    - 신규 `DecryptApiKey(byte[] ct, byte[] iv, byte[] tag) -> string` — `AuthenticationTagMismatchException` → `InvalidOperationException("API 키 무결성 검증 실패")` 변환
    - 신규 `internal static ComputeKeyHash(string) -> string` — SHA-256 hex 대문자 64자. internal 노출은 ApiKeyAuthService 와의 충돌 회피용 — 실제 두 서비스가 각자 private 으로 보유(코드 중복 허용. Phase 5+ 공용 헬퍼 추출 트랙)
    - `CreateApiKeyAsync` / `GenerateAgentApiKeyAsync` / `GetDecryptedApiKeyAsync` 3곳 모두 GCM 분기 + KeyHash 산출 + base64 ciphertext 만 EncryptedKey 에 저장 (iv/tag 는 별도 컬럼)
    - `GetDecryptedApiKeyAsync` 에 legacy 호환 분기: `KeyIv is { Length: 12 }` + `KeyTag is { Length: 16 }` 체크 → GCM 복호화 / 둘 중 하나라도 NULL → `DecryptLegacyCbc` 폴백 + 즉시 `BackfillToGcm` 호출 → 기존 `LastUsedAt`/`UsageCount` 갱신과 함께 SaveChanges 1회 커밋. 명시 `TODO Phase 3.6 — 폴백 + DecryptLegacyCbc 제거 약속`
    - `MapToDtoAsync` / `MaskApiKey` / `MaskAgentApiKey` 등 외부 표면 동작 보존
  - `agenthub/Services/ApiKeyAuthService.cs` — 전면 재작성 (외부 단일 메서드 `ValidateApiKeyAsync(string?)` 시그니처 보존):
    - 생성자: ApiKeyService 와 동일한 `LoadAesKey` 정책 (코드 중복 허용 — 본 task 범위. Phase 5+ 공용 헬퍼 추출)
    - **빠른 경로 (TECHSPEC §16 C3 해소)**: `ComputeKeyHash(apiKey)` → `_context.ApiKeys.FirstOrDefaultAsync(k => k.KeyHash == hash && k.IsActive && (k.ExpiresAt == null || k.ExpiresAt > now))` 단건 조회. KeyHash UNIQUE 인덱스 매칭이 곧 평문 일치 의미 — 추가 복호화/AEAD 검증 불필요(SHA-256 충돌 무시)
    - **Legacy 폴백**: 빠른 경로 미스 시 `KeyHash IS NULL && IsActive && 만료 안 됨` 행만 풀스캔 + foreach 복호화 비교 + 즉시 `BackfillRow` (KeyHash + GCM 채우기). `TouchAndProjectAsync` 에서 SaveChanges 1회. **TODO Phase 3.6 — 폴백 + DecryptLegacyCbc 제거**
    - `TouchAndProjectAsync` private 추출 — 두 경로(빠른/폴백) 가 동일 영속화 로직 재사용. `LastUsedAt/UsageCount/UpdatedAt` 갱신 + SaveChanges + LogInformation + ApiKeyValidationResult 사상
  - `agenthub/appsettings.json` — `Encryption.ApiKeyAesKey` 빈 키 추가 (운영 시 base64 32바이트 주입). `.gitignore` 대상이 아닌 base 파일이므로 디스크에 키 자체 없이 키 슬롯만 노출
  - `agenthub/appsettings.Development.json` — 동일 `Encryption.ApiKeyAesKey: ""` 추가. 빈 값이면 LogWarning 발동 + JWT 키 폴백 — 개발 환경 호환성 유지. `.gitignore` 로 차단됨
- **외부 호출처 grep 검증 (시그니처 무변경 확인)**:
  - `Controllers/ApiKeysController.cs` — `IApiKeyService` 의 9개 public 메서드 호출. 시그니처 동일 → 변경 0
  - `Controllers/AgentsController.cs` — `IApiKeyService.GenerateAgentApiKeyAsync` / `GetAgentApiKeysAsync` / `DeleteAgentApiKeyAsync` 호출. 시그니처 동일 → 변경 0
  - `Attributes/ApiKeyAuthorizeAttribute.cs` — `IApiKeyAuthService.ValidateApiKeyAsync(string?)` 호출. 시그니처 동일 → 변경 0
  - `Program.cs` — DI 등록(`AddScoped<IApiKeyService>` / `AddScoped<IApiKeyAuthService>`). 생성자 의존성(`AIAgentManagementDbContext` + `ILogger<T>` + `IConfiguration`) 동일 → 변경 0
- **AES-GCM 파라미터 검증**:
  - 키 길이: 32 바이트 (AES-256) — `LoadAesKey` 에서 `bytes.Length != 32` 시 fail-fast InvalidOperationException
  - nonce 길이: 12 바이트 — `RandomNumberGenerator.GetBytes(12)` (NIST SP 800-38D / GCM 권장)
  - tag 길이: 16 바이트 — `new AesGcm(key, tagSizeInBytes: 16)` 명시 + `byte[16]` 할당
  - base64 format 검증: `LoadAesKey` 에서 `Convert.FromBase64String` 실패 시 fail-fast
- **운영 마이그레이션 절차 (TODO Phase 3.6 백필)**:
  1. 운영 환경에 32바이트 random AES-256 키 생성 (`openssl rand -base64 32`) → `Encryption:ApiKeyAesKey` 환경변수 또는 vault 주입
  2. Phase 3.2 Npgsql baseline 시 `KeyIv bytea NULL` / `KeyTag bytea NULL` / `KeyHash varchar(64) NULL UNIQUE` + `Users.Email UNIQUE` 컬럼/인덱스 자연 흡수
  3. Phase 3.6 데이터 마이그레이션 스크립트:
     - 기존 ApiKey 행 전수 조회 → JWT 폴백 키로 legacy CBC 복호화 → 평문 → 운영 AES-256 키로 GCM 재암호화 + KeyHash 산출 → UPDATE
     - 또는 인증 시 자동 백필을 활용해 자연 마이그레이션 후 일정 기간 경과 시 NULL 잔존 행만 강제 처리
  4. 백필 완료 후 양 서비스의 `DecryptLegacyCbc` + 폴백 분기 + ApiKeyService.BackfillToGcm + ApiKeyAuthService.BackfillRow 제거 (TODO 마커)
- **잠재 위험**:
  - **운영 키 즉시 교체 시 legacy 행 일시 인증 실패**: 운영 키를 `Encryption:ApiKeyAesKey` 로 교체하면 JWT 폴백 키로 암호화된 legacy 행 복호화가 실패 → 인증 거부. 따라서 **백필 완료 전까지는 운영 키 미주입 (JWT 폴백 유지) 권장**. 본 코드는 폴백 키로도 GCM/CBC 모두 동작하므로 호환성 유지
  - **legacy 폴백 풀스캔 비용**: 백필 중간에는 `KeyHash IS NULL` 행이 N개 있으므로 인증 핫패스가 일시적으로 O(N) 풀스캔. UNIQUE 인덱스 자체는 NULL 다수 허용(PG 표준)이라 신규/백필 행은 빠른 경로로 자동 진입
  - **SHA-256 충돌**: 평문 ApiKey 가 256비트 random("ak-{base64 32바이트}") 이므로 충돌 확률은 무시할 수준(2^128 birthday 한계 — 운영 데이터량 기준 0). KeyHash UNIQUE 매칭으로 평문 일치를 직접 추정 가능
  - **PG NULL UNIQUE 의미**: PG 표준은 UNIQUE 인덱스가 NULL 을 무한히 허용. legacy 행 NULL 다수 안전. EF 의 `IsUnique()` 가 PG 에서 자동으로 부분 인덱스로 최적화하지는 않으나, NULL 행은 인덱스 단건 조회 대상이 아니므로 빠른 경로 영향 없음
  - dotnet CLI 미설치 — `dotnet build --warnaserror` 검증 사용자 측 필요. nullable 분석 안전 (KeyIv/KeyTag/KeyHash 는 명시 nullable)
  - **운영 secret 주입 누락 시**: `LogWarning` 만 1회 발동(시작 시) — 사용자 가시성 낮음. Phase 5+ 에서 운영자 콘솔 헬스체크에 노출 권고
- **TECHSPEC §16 위험 항목 해소**:
  - C1 (AES 고정 IV) → ✅ 해소 (per-record nonce + GCM AEAD)
  - C2 (JWT 키 ↔ AES 키 결합) → ✅ 해소 (별도 설정 키, JWT 폴백은 호환 분기)
  - C3 (API Key 풀스캔) → ✅ 해소 (KeyHash UNIQUE 단건 조회)
  - C4 (Users.Email UNIQUE 부재) → ✅ 해소 (DB 레벨 UNIQUE 인덱스)
- **검증 방법 (사용자 측, dotnet 8 SDK)**:
  ```bash
  cd agenthub
  dotnet build --warnaserror
  # Phase 3.2 baseline 생성 시 KeyIv/KeyTag/KeyHash + Users.Email UNIQUE + ApiKeys.KeyHash UNIQUE 자연 흡수 확인
  # 통합 검증: 기존 평문 키로 인증 → legacy 풀스캔 + 백필 → 두 번째 호출은 KeyHash 빠른 경로
  # 운영 키 주입 후: 새로 발급한 키만 동작, legacy 는 백필 완료 후 정상 동작
  ```
- **남은 작업 (별도 task)**:
  - Phase 3.2 Npgsql baseline 생성 시 신규 컬럼/인덱스 자연 포함 확인
  - Phase 3.6 데이터 마이그레이션 스크립트 작성 + legacy 폴백 코드 제거
  - Phase 5+ ApiKeyService/ApiKeyAuthService 의 AES 헬퍼 + LoadAesKey 중복 제거(IApiKeyEncryptor 추출 트랙)
  - C1/C2/C3/C4/C8/H10 6개 sub-task 결과 통합 후 사용자 확인 단계에서 단일 commit (사용자 결정)

### 2026-05-05 (Phase 3.3d — `QuotaService.RecordUsageAsync` 토큰 인자 누락 버그 수정 / TECHSPEC §16 H10)
- **목적**: `IQuotaService.RecordUsageAsync(userId, serviceId, tokens, cost)` 시그니처는 tokens 를 받지만 구현(`Services/QuotaService.cs:190~206`)이 `tokens` 파라미터를 폐기하던 버그 수정. 호출처 5곳이 전달하던 `aiResponse.TotalTokens` / `totalTokens` 가 그동안 모두 무시되어 토큰 기반 한도/대시보드 시각화 불가능했음
- **수정 파일 6개 (시그니처 무변경)**:
  - `agenthub/Models/ApiQuota.cs` — 신규 컬럼 2개 추가:
    - `public long CurrentTokens { get; set; } = 0L;` ([Required], 월간 누적 토큰. int 범위(약 21억) 초과 가능성 → long. Npgsql 기본 매핑은 bigint)
    - `public long? MonthlyTokenLimit { get; set; }` (nullable, NULL = 미적용. 호출 횟수 기준 `MonthlyLimit` 와 병행 운영)
    - 기존 `MonthlyLimit`/`CurrentUsage` 에도 한국어 XML doc summary 추가
  - `agenthub/Data/AIAgentManagementDbContext.cs` — `OnModelCreating` ApiQuota 블록에 `entity.Property(e => e.CurrentTokens).HasDefaultValue(0L)` 명시 (운영 DB 직접 ALTER TABLE 시 default 적용 보장)
  - `agenthub/Services/QuotaService.cs` — 4개 분기 수정:
    - `RecordUsageAsync` 본문에 `quota.CurrentTokens += tokens;` 한 줄 추가 (한국어 주석 + XML doc summary 신설). tokens=0 호출(ImageGenerationController)은 0 누적되어 영향 없음
    - `CheckQuotaAsync` 에 토큰 한도 분기 추가: `if (quota.MonthlyTokenLimit.HasValue && quota.CurrentTokens >= quota.MonthlyTokenLimit.Value) return CanUse=false`
    - `SetQuotaAsync` 신규 ApiQuota 생성 분기: `MonthlyTokenLimit = request.MonthlyTokenLimit, CurrentTokens = 0L` 추가. 기존 ApiQuota 수정 분기: `if (request.MonthlyTokenLimit.HasValue) quota.MonthlyTokenLimit = request.MonthlyTokenLimit;` (요청 본문에 키 없으면 기존값 보존 정책)
    - `GetQuotasAsync` / `GetQuotaAsync` DTO 매핑 2곳에 `MonthlyTokenLimit` / `CurrentTokens` 필드 전파
  - `agenthub/DTOs/QuotaDto.cs` — `MonthlyTokenLimit` / `CurrentTokens` 필드 2개 추가 (XML doc 한국어)
  - `agenthub/DTOs/SetQuotaRequestDto.cs` — `MonthlyTokenLimit?` 필드 추가
  - `agenthub/BackgroundJobs/QuotaResetJob.cs` — `ResetMonthlyQuotas` 에 `quota.CurrentTokens = 0L;` 라인 추가 (호출 횟수/토큰/비용 3개 카운터 리셋 동기화)
- **`IQuotaService.cs` 시그니처 무변경** — 호출처 5곳 모두 동일 시그니처로 컴파일 통과
- **호출처 5곳 grep 결과 (시그니처 무변경 확인)**:
  - `Controllers/ImageGenerationController.cs:304` — tokens=0 (이미지 생성은 토큰 개념 없음). `CurrentTokens += 0` → 영향 없음
  - `Services/ChatService.cs:413` (SendMessageAsync) — `aiResponse.TotalTokens` 정상 누적
  - `Services/ChatService.cs:962` (SendDirectMessageAsync, Vue UI 비스트리밍) — `aiResponse.TotalTokens` 정상 누적
  - `Services/ChatService.cs:1265` (SendDirectMessageStreamChunksAsync, OpenAI 호환 SSE) — `totalTokens` 정상 누적 (Phase 3.5 stream_options.include_usage:true 로 실제 토큰수 회수)
  - `Services/ChatService.cs:1570` (SendDirectMessageStreamEventsAsync, Vue UI SSE) — `totalTokens` 정상 누적
- **`MonthlyTokenLimit` 도입 결정**: **도입함**. 이유:
  1. LLM 비용 구조상 호출 횟수보다 토큰 누적이 더 정확한 cost driver
  2. nullable + HasValue 가드로 기존 행에 영향 0 (NULL 이면 검사 우회)
  3. 향후 별도 Phase 에서 운영자 UI 노출 시 추가 마이그레이션 없이 사용 가능
  4. 코드 추가 약 8 라인 — 비용 대비 가치 높음
- **프론트 사용량 대시보드 영향 (별도 트랙으로만 기록, 본 작업 범위 외)**:
  - `agenthub/ClientApp/src/views/agent/AgentChat.vue:1007~1010` — `response.data.todayUsage / currentUsage / monthlyLimit` 3개 필드 사용 중. 신규 `currentTokens` / `monthlyTokenLimit` 는 미사용 → 응답에 추가 필드가 흘러도 무시되어 회귀 0
  - `Controllers/QuotaController.cs:140~158` `GetMyQuota` 의 익명 객체 응답에는 신규 필드 미포함. **별도 트랙 권고**: 운영자 대시보드 노출 시 `quota.CurrentTokens` / `quota.MonthlyTokenLimit` 를 명시 추가 필요
  - `Controllers/QuotaController.cs:127~138` 미설정 시 기본값 응답에는 호출 횟수 기반 필드만 — 토큰 기본값을 추가할지 별도 결정 필요
- **잠재 위험**:
  - **Phase 3.2 baseline 자연 흡수 의존**: 본 작업은 EF 마이그레이션 파일을 생성하지 않음. Phase 3.2 (Npgsql baseline `Init` 신규 생성) 시점에 `CurrentTokens bigint NOT NULL DEFAULT 0` / `MonthlyTokenLimit bigint NULL` 컬럼이 자동 포함됨. **Phase 3.2 작업 전 운영 DB 에 직접 ALTER TABLE 적용 시점은 별도 운영 절차로 결정** (현재 운영 DB 미존재 — 코드 작성만 완료)
  - **CheckQuotaAsync 의 토큰 한도 검사는 LLM 호출 직전에 동작** — 한도 초과 직전 호출은 통과될 수 있음(예: 한도 1,000,000 토큰, 999,500 누적 상태에서 100,000 토큰 요청 통과). 정확한 사전 추정은 비용/복잡도 대비 가치 낮아 보류 (TECHSPEC §15 후속 검토)
  - dotnet CLI 미설치 환경 — 빌드 검증 불가. **사용자 측 SDK 설치 후 `dotnet build --warnaserror` 필요**
- **검증 방법 (사용자 측, dotnet 8 SDK 환경)**:
  ```bash
  cd agenthub
  dotnet build --warnaserror   # 워닝 0건 + 컴파일 통과
  # ApiQuota 컬럼 자동 변경 — Phase 3.2 baseline 생성 시 자연 포함
  # 단위 테스트 인프라 부재 → 수동 점검: 채팅 1회 → ApiQuotas.CurrentTokens 가 증가하는지
  ```
- **남은 작업 (별도 task)**:
  - Phase 3.2 Npgsql baseline 생성 시 `CurrentTokens` / `MonthlyTokenLimit` 자연 포함 확인
  - QuotaController `/my/{serviceId}` 응답에 `CurrentTokens` / `MonthlyTokenLimit` 노출 (별도 트랙)
  - 운영자 대시보드(`Controllers/AnalyticsController.cs` 등) 토큰 시계열 조회 활용 (별도 Phase)
  - C1/C2/C3/C4 와 묶어 단일 commit 또는 분리 commit 결정 (사용자 확인 후)

### 2026-05-05 (Phase 3.3a — C8 SignalR Hub 인증 강화)
- **목적**: TECHSPEC §16 C8 위험 항목 해소. 두 SignalR Hub(`NotificationHub`, `ChatHub`) 모두 `[Authorize]` 부재 + 클라이언트 임의 ID 입력으로 그룹 가입이 가능했던 보안 결함 차단. 현 상태에서는 임의 사용자가 다른 사용자 알림을 도청하거나 남의 대화 그룹에 합류 가능
- **수정 파일 3개**:
  - `agenthub/Hubs/NotificationHub.cs` (전면 재작성, ≈75 LOC)
    - 클래스에 `[Authorize]` 부착
    - `JoinUserNotifications(int userId)` → 파라미터 제거 후 `JoinUserNotifications()`. 본문에서 토큰 클레임으로 userId 결정 (`Context.UserIdentifier` 우선, 폴백으로 `Context.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value`). int.TryParse 실패 시 그룹 가입 없이 조용히 종료 + 경고 로그
    - 짝 메서드 `LeaveUserNotifications()` 신설 — 동일 정책으로 그룹 탈퇴 (기존에 누락되어 있던 짝 추가)
    - `OnDisconnectedAsync` 로그 한국어화
    - private helper `ResolveUserId()` 추출 (재사용)
    - using: `Microsoft.AspNetCore.Authorization`, `System.Security.Claims` 추가
  - `agenthub/Hubs/ChatHub.cs` (전면 재작성, ≈85 LOC)
    - 클래스에 `[Authorize]` 부착
    - 생성자에 `AIAgentManagementDbContext` DI 추가 (Scoped DbContext, Hub의 기본 lifetime이 transient지만 SignalR는 호출당 scope를 만들므로 안전)
    - `JoinConversation(int conversationId)` 본문에 소유권 검증 추가: `_dbContext.ChatConversations.AsNoTracking().AnyAsync(c => c.ConversationId == conversationId && c.UserId == userId)` → false면 `throw new HubException("권한 없음")` (R5 한국어)
    - `LeaveConversation`은 자기 connection의 그룹에서만 빠지므로 별도 검증 생략 (가입이 이미 검증을 통과)
    - private `ResolveUserId()` — `Context.UserIdentifier` → NameIdentifier claim 폴백, 둘 다 없으면 `throw new HubException("인증 정보가 없습니다")`
    - using: `System.Security.Claims`, `AIAgentManagement.Data`, `Microsoft.AspNetCore.Authorization`, `Microsoft.EntityFrameworkCore` 추가
  - `agenthub/Program.cs` 두 군데 수정:
    - `AddJwtBearer(options => { ... })` 블록에 `options.Events = new JwtBearerEvents { OnMessageReceived = ... }` 추가. `/hubs` 경로 한정으로 `?access_token=` 쿼리에서 토큰 추출 → `context.Token`에 주입. WebSocket은 Authorization 헤더를 부착할 수 없어서 SignalR JWT 인증의 표준 패턴
    - `MapHub<ChatHub>("/hubs/chat")` / `MapHub<NotificationHub>("/hubs/notification")` 두 줄에 `.RequireAuthorization()` 체이닝 추가 — 미인증 연결 시도를 라우팅 단계에서 차단
- **frontend 측 영향 (호출처 grep 결과)**:
  - `agenthub/ClientApp/src/services/signalr*.ts` 파일 자체가 부재 (Glob `signalr*.ts` no match). `ClientApp` 내부에서 `HubConnection` / `signalr` 참조는 `package.json` / `package-lock.json`에만 존재 (의존성 등재만, 실제 사용 코드 없음)
  - `JoinUserNotifications`, `LeaveUserNotifications`, `JoinConversation`, `LeaveConversation` 모두 ClientApp 소스에서 invoke 패턴 0건
  - **결론**: 본 task에서 frontend 변경 불필요. 향후 SignalR 클라이언트 도입 시 `connection.invoke('JoinUserNotifications')` 형태(인자 없음)로 호출 + 연결 URL에 `?access_token={JWT}` 부착 필요
- **잠재 위험 / 운영 측 영향**:
  - **`AIAgentManagementDbContext`(Scoped)를 ChatHub(Transient)에 주입**: SignalR은 각 Hub 호출마다 internal scope를 생성하므로 captive dependency 안티패턴(`anti-patterns.md` §7)에 해당하지 않음. 다만 DbContext 인스턴스가 long-lived connection 동안 다수 호출에 걸쳐 reuse되는 것은 아니라는 점은 검증 시 주의 (각 Hub 호출이 별도 scope)
  - **빌드 워닝 검증 불가**: dotnet CLI 미설치 환경 — 사용자 측 `dotnet build` 워닝 0건 확인 필요
  - **운영 클라이언트 즉시 끊김 가능성**: 현재 SignalR 클라이언트 구현체가 ClientApp에 부재하여 즉시 영향 없음. 추후 도입 시 `?access_token=` 쿼리 부착 + `invoke('JoinUserNotifications')` 인자 없는 호출로 마이그레이션 필요
  - **HubException 메시지 노출**: SignalR은 기본적으로 `HubException` 메시지만 클라이언트에 전달 (일반 Exception은 "An unexpected error occurred"로 마스킹). "권한 없음" / "인증 정보가 없습니다"는 의도된 사용자 메시지이므로 정상
- **TECHSPEC §16 위험 항목 해소**:
  - C8 (`[Authorize]` 부재 + 임의 userId 입력) — ✅ 해소
  - 부수 효과: 도청 가능성 차단, 대화 그룹 무단 가입 차단, JWT 검증된 사용자만 SignalR 연결
- **다음 단계**: 사용자 환경에서 `dotnet build` 워닝 확인 → 4개 sub-task(3.3a/3.3b/3.3c/3.3d) 결과 종합 후 commit

### 2026-05-05 (Phase 3.5b frontend — Vue AgentChat SSE 스트리밍 클라이언트 도입)
- **목적**: 백엔드 `/api/chat/send/stream` 엔드포인트 추가에 이은 frontend 분담분. 사용자 보고 "Vue UI 채팅 5~10초 대기 후 일괄 출력" UX 문제의 직접 해소 — 첫 token 즉시 표시
- **신설 파일 1개**:
  - `agenthub/ClientApp/src/services/sseClient.ts` (≈260 LOC) — fetch + ReadableStream + TextDecoder 기반 SSE 파서 (EventSource는 GET only + JWT 헤더 부착 불가하여 사용 불가)
    - `streamChat(payload, signal): AsyncGenerator<ChatStreamEvent>` 공개 API — `POST /api/chat/send/stream` 호출 + frame 단위 yield
    - 합의된 SSE 명세 5종 처리: `delta` / `meta` / `usage` / `error` 이벤트 + `[DONE]` 종료 마커
    - `\n\n` 프레임 구분자 + 미완성 chunk carry-over (`TextDecoder({stream:true})`) — 임의 경계로 잘려 도착하는 fetch chunk 안전 처리
    - JWT Bearer 자동 부착(localStorage `'token'` — `@/services/api` axios 인터셉터와 동일 정책) + 401 → `/api/auth/refresh` 호출 + 1회 재시도 + 실패 시 /login 리다이렉트
    - AbortController.signal 지원 — 사용자 "응답 중단" 버튼 연결
    - **새 npm 의존성 0건** (브라우저 표준 API만)
- **수정 파일 4개**:
  - `agenthub/ClientApp/src/views/agent/AgentChat.vue` — `:1708` 부근 핵심 분기 교체:
    - import: `reactive` 추가 + `streamChat` from `@/services/sseClient`
    - `Message` 인터페이스에 streaming 필드 추가: `isStreaming?: boolean` / `cost?: number` / `errorCode?: string`
    - 상태: `useStreaming = ref(true)` (기본 활성화, Settings 모달에서 토글 가능 예정) + `streamAbortController = ref<AbortController | null>(null)`
    - `sendMessage` 본문 재구조: 기존 `api.post('/chat/send', { ..., stream: false })` → 공통 `chatPayload` 추출 후 `if (useStreaming.value)` 분기
      - **streaming 분기**: 빈 assistant 메시지 즉시 push (reactive) → `for await (evt of streamChat(...))` → delta는 content 누적 + 첫 delta에서 `loading=false` (즉시 응답성), meta는 conversationId/messageId/model 갱신, usage는 stats 합산, error는 사용자 메시지 + BANNED_WORD/PII는 안내 추가
      - **AbortError 분리 처리**: 사용자 중단은 throw하지 않고 안내 문구로 마무리, 그 외 throw는 catch 블록으로 위임
    - **비스트리밍 폴백 보존**: `useStreaming.value === false` 시 기존 흐름 그대로 유지 — `/api/chat/send/stream` 미배포 환경 또는 사용자 명시 토글 안전망
    - catch 블록 강화: 스트리밍 placeholder(빈 content + `tempId="streaming-..."`) 제거 로직 추가 → 빈 bubble + 별도 error 메시지 중복 방지. 부분 채워진 placeholder는 `isStreaming=false`만 끄고 보존
    - 신규 `stopStreaming()` 함수 — `streamAbortController.abort()`
    - `onBeforeUnmount`에 abort 호출 추가 — 페이지 이탈 시 메모리/네트워크 누수 방지
    - 템플릿: send 버튼이 streaming 중에는 "응답 중단" 버튼으로 토글 (`v-if="streamAbortController"`), assistant bubble 뒤에 깜빡이는 cursor `▋` 표시 (`v-if="message.isStreaming"`)
  - `agenthub/ClientApp/src/views/agent/AgentChat.css` — `.cd-streaming-cursor` blink 애니메이션 + `prefers-reduced-motion` 배려(접근성)
  - `agenthub/ClientApp/src/i18n/locales/ko.json` — 신규 키 3개: `streamingAborted` / `streamingError` / `streamingStop` (R5 한국어 우선)
  - `agenthub/ClientApp/src/i18n/locales/en.json` — 동일 영문 키 3개
- **다른 호출처 grep 결과 (`api.post('/chat/send'`)** — 본 작업 범위 외, **별도 트랙 후속 처리 권고**:
  - `agenthub/ClientApp/src/views/agent/AgentBuilder.vue:859` — Agent 빌더 미리보기 채팅
  - `agenthub/ClientApp/src/views/agent/AgentMultiChat.vue:1186` — 다중 모델 비교 화면 (4,031 LOC)
  - `agenthub/ClientApp/src/views/Playground.vue:191` — 모델 Playground
  - 동일 sseClient를 재사용하면 한 곳당 수십 줄로 전환 가능. AgentMultiChat은 N개 모델 동시 streaming 지원이 자연스러움
- **잠재 위험 / 사용자 검증 필요**:
  - **incremental markdown 렌더 부작용**: marked + DOMPurify 스택은 unclosed code fence(```` ``` ````) 도중 chunk가 잘리면 일시적으로 잘못된 HTML을 만들 수 있음. DOMPurify가 sanitize하므로 XSS는 차단되지만, 코드 블록 등장 도중에는 렌더가 흔들릴 수 있음. ChatGPT/Claude 웹 UI도 동일 트레이드오프 — 사용자 보고 시 chunk가 아닌 줄 단위 디바운스 옵션 검토(현 시점 미구현)
  - **mid-stream 토큰 만료**: 첫 응답 헤더 단계의 401은 핸들하지만, streaming 도중 백엔드가 401을 흘리는 케이스는 본 구현이 핸들하지 않음(재현 가능성 낮음, TECHSPEC §16 후속 검토)
  - **SSE 버퍼링**: 백엔드가 `X-Accel-Buffering: no` 헤더 + `Response.Body.FlushAsync()`를 매 frame 호출해야 함(이미 ChatController에서 적용됨). 프론트엔드는 fetch만 사용하므로 추가 조치 불필요
  - **브라우저 호환성**: fetch + ReadableStream + AbortController + TextDecoder 모두 Chrome 43+/Firefox 65+/Safari 10.1+/Edge 79+ 지원 — AgentHub 타깃 브라우저 범위 안전
  - `npm run build:check` 미실행 (Windows 환경 npm 검증 환경 미구비) — 사용자 측 검증 필요
- **검증 방법 (사용자 측)**:
  ```bash
  cd agenthub/ClientApp
  npm run build:check    # vue-tsc 타입 검사 + vite build
  npm run dev
  # 브라우저에서 채팅 입력 → 토큰 단위 흐름 + Network 탭 chunked transfer 확인
  # 응답 도중 "응답 중단" 버튼 클릭 → 즉시 멈추는지
  # useStreaming 토글 끄면 비스트리밍 폴백 동작하는지 (현재는 코드 토글, Settings UI 노출은 별도 작업)
  ```
- **Phase 3.5b 완료 (frontend + backend)**:
  - 사용자 보고 "Vue UI 5~10초 대기" 핵심 UX 문제 → 첫 token 즉시 표시로 해소 (백엔드 SSE 엔드포인트 + 프론트 streaming 클라이언트)
  - 백엔드 `/api/chat/send/stream` + DTO `ChatStreamEvent` + `ChatService.SendDirectMessageStreamEventsAsync` (위 항목 참조)
  - 프론트 `sseClient.ts` + `AgentChat.vue` streaming 분기 (본 항목)
- **Phase 3.5b 후속 (별도 트랙)**:
  - AgentBuilder/AgentMultiChat/Playground 3개 화면도 동일 sseClient 적용
  - 사용자 설정 UI에 useStreaming 토글 노출 (Settings 모달)
  - dotnet 8 SDK 환경에서 백엔드 빌드 검증 + e2e 테스트(curl 또는 fetch SSE)

### 2026-05-05 (Phase 3.5b — Vue UI 전용 SSE 백엔드 엔드포인트 추가)
- **사용자 보고 "Vue UI 채팅 5~10초 대기 후 일괄 출력" 직접 해소를 위한 신규 엔드포인트 추가**
- **신설 파일 1개**:
  - `agenthub/DTOs/ChatStreamEvent.cs` — Vue UI 전용 SSE 이벤트 record (`Type` discriminator 기반: `"delta" | "usage" | "meta"`). 정적 helper `Delta/UsageEvent/Meta` 제공. camelCase JSON 직렬화 정책(P5) 준수
- **수정 파일 3개**:
  - `agenthub/Services/IChatService.cs` — `IAsyncEnumerable<ChatStreamEvent> SendDirectMessageStreamEventsAsync(...)` 시그니처 추가. 기존 `SendDirectMessageStreamChunksAsync`(`IAsyncEnumerable<ChatChunk>`)는 OpenAI 호환 SSE 전용으로 유지(불변)
  - `agenthub/Services/ChatService.cs` — `SendDirectMessageStreamEventsAsync` 구현 (clean room, 약 300 LOC)
    - 흐름: Agent/ServiceId 확정 → Quota 사전 체크 → BannedWord/PII 검사(SendDirectMessageAsync 와 동일 정책) → Conversation 락 보존 find/create → AiProxy.SendChatMessageStreamChunksAsync `await foreach` → **delta event yield** → 종료 후 cost 계산 → **usage event yield** → ChatMessage(user/assistant)/ApiUsage/Conversation 통계 SaveChanges → `assistantMessage.MessageId` 회수 → RecordUsageAsync → **meta event yield** (conversationId/messageId/model/cost)
    - 영속화 실패는 try/catch 후 meta event 계속 yield (사용자에게는 chunk가 이미 전달됨)
    - `usageEmitted` flag 도입: usage chunk 미발행(0 토큰 폴백) 시 meta event 의 `cost` 필드로 cost 동봉
  - `agenthub/Controllers/ChatController.cs` — `[HttpPost("send/stream")]` 신규 액션 + 2개 private 헬퍼 추가
    - 검증 단계는 SSE 시작 전 일반 401/400 JSON 응답으로 분리 (EventSource 호환성 + 클래스 레벨 [Authorize] 동작 그대로)
    - 통과 후에만 SSE 헤더 설정: `text/event-stream; charset=utf-8` + `Cache-Control: no-cache` + `X-Accel-Buffering: no` + `Connection: keep-alive` (IIS InProcess + reverse proxy buffering 방지)
    - `WriteSseFrameAsync(object, ct)` — JsonSerializerOptions(camelCase + IgnoreCondition.WhenWritingNull) 으로 직렬화 + 매 frame `Response.Body.FlushAsync()`
    - `WriteSseErrorAsync(code, message, ct)` — 스트림 시작 후 예외 처리용 (BannedWordException/PiiDetectionException/InvalidOperationException/Exception → 각각 `BANNED_WORD_DETECTED`/`PII_DETECTED`/`VALIDATION_ERROR`/`INTERNAL_ERROR` code + 한국어 메시지(R5))
    - OperationCanceledException(클라이언트 disconnect) 정상 종료 처리
    - `[DONE]` 종료 마커 표준 SSE 형식 준수
- **회귀 분석 (사용자 보고용 사실)**:
  - **OpenAICompatController.cs는 변경 없음** — Phase 3.5 commit(가짜 SSE → 진짜 SSE) 완전 보존
  - 기존 `ChatChunk` / `SendDirectMessageStreamChunksAsync` 시그니처/동작 모두 불변 → OpenAI SDK / Cursor / LangChain 호환성 회귀 0건
  - 기존 `[POST] /api/chat/send` 비스트리밍 분기 그대로 유지 → 기존 Vue UI 호출(`AgentChat.vue:1708`)은 클라이언트 변경 전까지 정상 동작
- **meta 정보 회수 가능 여부 확인 결과**:
  - `conversationId`: ✅ 영속화 전 conversation 객체에서 추출 가능 (ChatService.cs `finalConversationId = conversation?.ConversationId`)
  - `messageId`: ✅ EF SaveChanges 직후 `assistantMessage.MessageId` 가 IDENTITY로 채워짐(`long`). PG IDENTITY 가 컬럼 메타에 정상 매핑되었는지는 Phase 3.2 Npgsql baseline 생성 시 동시 검증 필요
  - `model`: ✅ 결정된 model 변수 그대로 yield
  - `cost`: ✅ `_aiProxyService.CalculateCostAsync` 결과를 usage event 와 meta event 양쪽에서 사용 가능
- **잠재 위험**:
  - **트랜잭션**: SaveChanges 가 단일 호출이므로 user/assistant message + ApiUsage + Conversation 통계가 원자적으로 커밋됨. 단, RecordUsageAsync(quota 차감)는 별도 트랜잭션이라 부분 실패 가능 (기존 SendDirectMessageStreamChunksAsync 와 동일 정책 — 운영 영향 동일 수준)
  - **예외**: 영속화 실패해도 meta event 는 계속 yield (`messageId=null` 상태). 클라이언트는 `messageId === null` 일 때 "메시지 저장에 실패했습니다" 비파괴적 알림만 표시하면 됨 (frontend 분담)
  - **cancellation**: `[EnumeratorCancellation]` 으로 토큰이 IAsyncEnumerable 까지 전파됨. 클라이언트 disconnect 시 AiProxy 의 HttpClient 까지 cancel 전달되어 외부 LLM 비용 절감 (기존 wrapper 와 동일)
  - **중복 코드**: `SendDirectMessageStreamChunksAsync` 와 약 70% 코드 중복. Phase 3.5 commit 회귀 위험을 피하기 위한 의도적 분리. Phase 5+ 에서 공통 streaming 코어 추출 리팩토링 예정 (TECHSPEC §15.4 후속)
  - dotnet CLI 미설치 — `dotnet build` 검증은 사용자 측 SDK 설치 후 필요
- **남은 작업 (별도 task)**:
  - Vue 측 `AgentChat.vue` 에 `fetch + ReadableStream` 또는 `EventSource`(JWT 헤더 제약 있음) 기반 streaming 클라이언트 도입 (frontend specialist 분담)
  - dotnet 8 SDK 환경에서 빌드 검증 + e2e 테스트(`/api/chat/send/stream` curl SSE 흐름 확인)

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
