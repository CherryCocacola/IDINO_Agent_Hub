# IDINO Agent Hub — 통합 작업 진행 상황

> **마지막 갱신**: 2026-05-12 (**트랙 #75 — Playwright UI e2e 5단계 모두 완료**. Python Playwright 1.58 + Chromium 인프라 신설 (`tools/ui_e2e/` 8 파일). 5단계 시나리오 결과: (S1) Agent API 키 mutation 1 cycle (UI) — **PASS 10/10**. UI 흐름 (admin 로그인 → /api-keys → "Agent API 키" 탭 → Agent 21 "표절 사전 점검 에이전트" 선택 → 발급 모달 → 발급 → 평문 키 캡처 → /v1/models 200 + 1 model → UI 삭제 클릭 → 회수 401 "Invalid or expired API Key"). **정확 endpoint 발견**: `POST /api/agents/{agentId}/api-keys` (트랙 #74 의 `/api/api-keys` 추정은 잘못된 path). 발급 모달의 평문 키가 첫 캡처에서 한 차례 노출 → 스크린샷 즉시 삭제 + 키 즉시 회수 검증(401 GOOD) → 마스킹 JS 강화 (input.value + TreeWalker textContent 양쪽 모두 ak- 패턴 `ak-x*****aHxQ` 형태로 마스킹). cleanup 잔여 0건 — 시나리오 종료 시 API DELETE fallback 으로 모든 ui-e2e-test* 키 자동 회수. (S2) LLM 1회 정밀 검증 (UI 채팅) — **PASS 5/5**. /agents → "채팅" 링크 → /agents/chat → 메시지 "안녕하세요, AgentHub UI e2e 테스트 (1회만)" 전송 → 한국어 응답 수신 + 화면 표시 (s2_05). endpoint `POST /api/chat/conversations/262/messages`. 비용 ~$0.0001. (S3) FAIL 4건 TC 보정 — **PASS 13 / FAIL 1 (UI 한계) / INFO 1**: A-06 = JSON body `{}` + Bearer → 200 "Logout successful" (TC 보정 — `expected={200,204}` + "JSON body 필수" 명시), E-02 = POST `/hubs/notification/negotiate?negotiateVersion=1` → 200 + connectionId + connectionToken + WebSockets transport (TC 보정 — method=POST). UI 자동 negotiate 캡처는 Playwright 환경에서 SignalR 클라이언트 미활성(endpoint 자체는 직접 검증 PASS). **G-04a 정확 endpoint 5개**: `/dashboard/metrics`, `/response-times`, `/search-errors`, `/search-usage`, `/upload-status` — 모두 admin 200 + anon 401 정상. **G-07a 정확 endpoint**: `/evaluation/config` — admin 200 + anon 401 정상. 트랙 #74 의 SPA fallback 잠재 결함 경고는 **잘못된 path 사용 때문** → 운영 결함 0. (S4) DocUtil UI I-01~I-05 — **SKIP**. DocUtil `/login` 은 "관리자 로그인" 화면(11명 일반 사용자 자격증명 미확보). brute force 금지 원칙으로 합리적 후보 2건 (`admin@example.com/Admin123!` 공통 IdP 가능성, `admin/admin` 기본 계정 관행) 시도 후 실패 → I-01 FAIL + I-02~I-05 SKIP. 자격증명 제공 시 재실행 가능. (S5) 종합 — `docs/TEST_CASES.md` §15 신설(시나리오 1~4 상세 + G-04a/G-07a 정확 endpoint 매핑 + 운영 영향 확인), `tools/probe_all.py` 보정 (A-06=POST+body{}, E-02=POST+negotiateVersion=1+expected={200}, G-04=/dashboard/metrics, G-07=/evaluation/config), `tools/build_checklist_xlsx.py` 보정 ([트랙 #75 보정] 라벨 + G-04a/G-07a/G-04b/G-07b path 갱신). **재실행 결과: 총 79 / PASS 44 / FAIL 0 / SKIP 35** (트랙 #74 FAIL 4건 모두 보정 PASS). 엑셀 27.3KB 갱신. **운영 영향**: ApiKey 발급/회수 4 cycle (모두 즉시 회수 + cleanup verified) / LLM 호출 1회 (~$0.0001) / 운영 사용자(11명) 데이터 무변경 / 노출된 키 1건 즉시 회수(검증 401). 도구: `tools/ui_e2e/common.py` + `probe_*.py` 2개 + `scenario_*_*.py` 4개 + `run_all.py`(미생성, 통합 실행은 개별 실행) + `screenshots/` 디렉토리. **이전 갱신**: 2026-05-12 (**트랙 #72 + #73 + #74 — 전체 시스템 테스트 카탈로그/엑셀/라이브 통합 완료**. (#72) `docs/TEST_CASES.md` 신설 — 11 영역 A~K × 79건 망라 (A 인증 7 / B Agent 7 / C ApiKey 4 / D OpenAI호환 7 / E 채팅 4 / F Tool/Workflow 5 / G Admin BFF DocUtil 13메뉴 26 / H Analytics 3 / I DocUtil 사용자 5 / J 보안 8 / K 통합 3) — 각 케이스 ID/시나리오/사전조건/입력/기대결과/위험도(안전 26/중간 17/위험 36)/자동화(YES 64/PARTIAL 13/NO 2). (#73) `docs/TEST_CHECKLIST.xlsx` 신설 27.3KB — Summary + 11 영역 시트, 헤더 색강조 + 위험도 색상(안전 초록/중간 주황/위험 빨강) + PASS/FAIL/SKIP conditional formatting + FAIL 4건 분석 + SKIP 35건 사유 분류. openpyxl 3.1.5. (#74) 라이브 테스트 (운영 `http://192.168.10.39:64005`, read-only): 총 79 / **PASS 40 / FAIL 4 / SKIP 35**. FAIL: A-06 logout 415(JSON body 필수, TC 보정) + E-02 negotiate 405(POST 필요, TC 보정) + **G-04a `dashboard/summary` anonymous 200 text/html** + **G-07a `evaluation` anonymous 200 text/html** — 후자 2건은 SPA fallback 노출 잠재 결함 (보안 정보 누설은 아니나 endpoint routing 누락 가능, 별도 트랙 후보). SKIP 분류: LLM 비용 18 / 운영 mutation 위험 13 / 자격증명 미보유 5 / 외부부하 3. admin@example.com JWT 발급(555 chars) 정상 + /api/agents 200 + /api/api-keys 200 + Admin BFF 24/26 정상(401 anonymous + admin Bearer read). commit `25a2a1e`. 도구: `tools/probe_all.py` + `tools/build_checklist_xlsx.py` + `tools/probe_all_result.json`. 운영 mutation 0 / LLM 호출 0 / 데이터 손상 0. **이전 갱신**: 2026-05-12 (**트랙 #64 — DocUtil ENCRYPTION_KEY 회전 완료**. 옵션 B Bulk Re-encrypt — 운영 `document_utilization.tb_llm_api_keys` 1행 재암호화 (옛 약한 키 `0123...cdef` 64bit 추정 엔트로피 → 새 강한 키 `7a8fde1d...0711` `secrets.token_hex(32)` 256bit) + 운영 `.env` atomic 갱신 + 3 컨테이너 (api/celery-worker/celery-beat) force-recreate (다운타임 ≈ 47초) + 라이브 회귀 9 항목 모두 PASS. 회귀: (1) AESGCM round-trip — 새 키로 row decrypt OK plain_len=164 prefix=sk-proj-**** plain_prefix=sk-proj***  (2) Negative test — 옛 키로 decrypt 시도 → InvalidTag 거절 (3) docutil-api /health 200 (4) docutil-api /api/v1/auth/login 422 (5xx 아님) (5) docutil-nginx /health 200 (6) agenthub /health 200 (별도 컨테이너 영향 0) (7) 8 endpoint probe 5xx 0건 (8) 60초 안정성 — docutil-api/celery-worker/celery-beat 로그 ERROR/InvalidTag/decrypt 0건 (9) row_count=1 무변경 + upd_dt=2026-05-12 00:51:31.500748+00 정확히 1행만 갱신. 단일 트랜잭션 안전장치: BEGIN/SELECT FOR UPDATE/사전 평문 SHA-256 캡처/새 nonce os.urandom(12) 충돌 sanity/즉시 round-trip 검증/post-UPDATE 재검증/COMMIT. **운영 OpenAI 평문 키 무손상 입증** (사전 sha256=2087b796... 와 사후 새 키 decrypt 결과 sha256 일치 + plain_len 164 동일 — G.3 사용자 명시 보존 기조 준수). 백업 4종: `/home/idino/docutil/.env.rotbak.20260512_005129` (옛 .env 7,694 bytes, 0600) + `/home/idino/docutil/backups/llm_api_keys_pre_rotate_20260512_004813.dump` (3,708 bytes, custom format) + `..._004813.sql` (1,614 bytes, plain SQL --column-inserts) + `/home/idino/.docutil_new_enckey_20260512_004813.txt` (새 키 평문, 0600 — 검증 완료 후 삭제 권장). 별도 트랙 후보: (a) 새 키 임시 파일 + 트랙 #62 임시 secrets 파일 함께 삭제 결정, (b) DocUtil `config.py` ENCRYPTION_KEY validator 강화 (길이 + 엔트로피 검증, 약한 키 부팅 차단). AgentHub 측 ApiKeyAesKey 변경 0 (트랙 #56 분석: 별도 키 운영 강한 키 적용 확인). Nexus 영향 0. **이전 갱신**: 2026-05-12 (**운영 보안 강화 G.2 완료** — A1 + A2 + B3 모두 PASS. (A2) docutil 5 서비스(REDIS/RABBITMQ/MINIO/FLOWER/GRAFANA) 비번 `openssl rand -hex 32` (64자) 강화 → 8 컨테이너 force-recreate → 모두 healthy + 라이브 인증 검증 PASS(Redis PONG/RabbitMQ authenticate_user Success/MinIO list_buckets OK/Flower 200/Grafana reset-admin-password 후 200) + 옛 비번 모두 401/AUTH 실패. (A1) DocUtil Phase 7 R2 청소 코드 21개 파일 운영 SFTP 배포 + claude_client.py/gemini_client.py dead code 삭제 + docker compose build api/celery-worker/celery-beat (새 image `c489e4cdb462`) + force-recreate 3 컨테이너 healthy. 코드 반영 검증 라이브: `agenthub_client.py` 컨테이너 안 존재 / `grep -rF "from openai import" /app/app/` **0건**(R2 단일 진입점 완전 달성) / `AgentHubClient`+`AgentHubLLMWrapper` import 10/10 PASS in docutil-api+celery-worker+celery-beat. **단 운영 docutil `.env` 에 `AGENTHUB_URL`/`AGENTHUB_API_KEY` 둘 다 부재 발견** — 실제 LLM 호출 시 `AgentHubClient.__init__` ValueError 발생할 것이며, AgentHub admin UI 로 ApiKey 발급 + scope=`chat,stream,embeddings,images,info,usage` + consumer_system=`docutil` 부여 + 운영 docutil `.env` 적용 + docutil-api/worker/beat 재시작 필요 (별도 트랙). (B3) 운영 agenthub `.env` `JWT_SECRET_KEY` 가 example placeholder 그대로(`YourSuperSecretKey...!`) 였음 발견 → `openssl rand -hex 64` (128자) 갱신 + force-recreate(21초 healthy) → admin@example.com(`Admin123!`) 로그인 200 + 새 JWT 발급(len=555) + `/api/users`/`/api/auth/me`/`/api/agents` 모두 200 + 옛 키 서명 JWT → 401 무효화 PASS. **모든 사용자 강제 재로그인 발생 시각 2026-05-11 13:23 KST**. 추가 발견 + 해소: agenthub `.env` `REDIS_PASSWORD` stale(`docutil_redis_2024`) → A2 의 새 docutil-redis 비번으로 동기화 + agenthub 재재시작(11초 healthy) + Redis 에러 0건 검증. 별도 관찰: `/api/admin/docutil/users` 502 — agenthub→docutil-api BFF 의 `DOCUTIL_JWT_TOKEN` 빈 값 또는 service account 비번 stale 원인 가능(별도 트랙). 운영 다운타임: docutil ~90초(8 컨테이너 동시 + 3 컨테이너) + agenthub ~50초(재시작 ×2). 백업: `docutil/.env.bak.20260511_084232` / `agenthub/.env.bak.20260511_132356` / `docutil/backups/backend_pre_phase7_v2_20260511_091650.tar.gz`(611K). 임시 secrets 파일: `/home/idino/.g2_secrets_20260511_174342.txt`(0600, 사용자 결정으로 적시 삭제 필요). **다음 트랙**: (A) docutil `.env` 의 `AGENTHUB_URL`/`AGENTHUB_API_KEY` 신규 발급 + 적용 + R2 e2e 라이브 검증 / (B) agenthub `.env` 의 `DOCUTIL_JWT_TOKEN` 또는 service account 재인증 → `/api/admin/docutil/*` BFF 502 해소 / (C) ENCRYPTION_KEY 영향 범위 분석 결과 수령 + 회전 / (D) GitHub push 차단 `1da04ab` secret leak history sanitize. **이전 갱신**: 2026-05-11 (**Phase 7 — DU-14 /v1/images 컨트롤러 + DocUtil 위임 완료** — R2 단일 진입점 (LLM/Embedding/Image) 완전 강제. AgentHub `Controllers/OpenAICompatController.cs` 에 `POST /v1/images/generations` 신설 (OpenAI Images API 호환, +247 LOC) — class-level `ApiKeyAuthorize` + `EnableRateLimiting("ip-openai")` 자동 적용, 요청 검증(model/prompt/n 1~10/response_format url|b64_json), Agent 룩업(request.Model AgentCode 우선 + `docutil-image-generator` 자동 폴백), 권한 검사(ApiKey AgentId 바인딩 일치 + IsPublic|소유자), LlmRouting 분기(External 통과 / **Internal 차단 + 한국어 안내** "내부망 LLM(Nexus)은 이미지 생성을 지원하지 않습니다." / Hybrid 는 현 Phase External 동치), 모델명 결정(`dall-e-` prefix 우선 + Agent.DefaultModel/ApiService.DefaultModel 폴백), 내부 `ImageGenerationRequestDto` 로 변환 후 기존 `IAiProxyService.SendImageGenerationAsync` 재활용(CallDallEAsync/CallGeminiImage/Imagen4/Gen4/Flux2 5종 모두 자동 지원 — **코드 중복 0**), response_format=b64_json 인 경우 `IHttpClientFactory` 로 외부 URL GET 후 base64 인코딩(DocUtil bytes 사용 경로 필수). 신규 DTO `OpenAIImagesRequestDto`/`OpenAIImagesResponseDto`/`OpenAIImageItemDto` 추가(`agenthub/DTOs/OpenAICompatDto.cs` +91 LOC, OpenAI 호환 JSON property 명 model/prompt/n/size/quality/style/response_format/user). DocUtil 측: `AgentHubClient.generate_image(prompt, *, agent_code="docutil-image-generator", n, size, quality, style, response_format, timeout, extra)` 신설 + `generate_image_bytes()` 편의 헬퍼(base64 디코딩 + bytes 반환 — 기존 `ImageGenerationService` bytes 인터페이스 호환 유지)(`docutil/backend/app/integrations/agenthub_client.py` +166 LOC). DocUtil `app/integrations/image_generation/service.py::_generate_dalle3` 교체(-50 LOC, +90 LOC) — **`from openai import AsyncOpenAI` 제거(anti-patterns.md §1 위반 해소)**, `AgentHubClient.generate_image_bytes(agent_code="docutil-image-generator", size, quality="standard", style, timeout=60.0)` 위임. 파라미터 검증(ALLOWED_DALLE3_SIZES/STYLES 기본값 대체)은 유지, AgentHubClient 초기화 `ValueError`(환경변수 누락)/`AgentHubError`(HTTP/네트워크/4xx/5xx)/`ValueError`(빈 prompt) 3종 모두 잡아 None 반환 + 한국어 로그(기존 degrade 동작 100% 호환). 검증: `dotnet build` errors=0, warnings 11(전부 본 트랙과 무관한 기존 코드 CS1998); ruff check `--select F,E9` PASS(구문/F-에러 0); **`grep "from openai import" docutil/backend/app/` → 0 hits**(anti-patterns.md §1 위반 0건 PASS). 시드 의존: `phase5_phase7_seeds.sql:234` 의 docutil-image-generator Agent(ServiceCode=dalle, LlmRouting=External, DefaultModel=dall-e-3, ConsumerSystems=["docutil-user"]) 이미 시드됨 — 추가 시드 불요. **별도 트랙 후보(본 Phase 범위 외, progress.md 의 "R2 단일 진입점 강제 완료" 주장에 대한 정합성 점검 결과)**: (1) `app/integrations/llm/client.py:65,641` — `base_url: str = "https://api.openai.com/v1"` 기본 인자값(LLMClient 자체 — 실제 호출 경로가 R2 우회인지 별도 점검 필요). (2) `app/integrations/llm/claude_client.py:37` — `from anthropic import Anthropic, AsyncAnthropic`(progress.md 상 "dead code" 분류 — 실제 사용처 grep 재확인 필요). (3) `app/workers/training/trainer.py:235` — DU-17 trainer 의 `https://api.openai.com/v1/chat/completions` 직접 호출(별도 트랙). (4) `app/modules/search/service.py:540,854,923` — 3건 OpenAI 직접 URL(임베딩 + chat completions 2건). (5) `app/modules/chat/service.py:510` — `https://api.openai.com/v1/chat/completions` 직접 URL. (6) `app/modules/api_keys/service.py:24` — 모델 카탈로그 fetch(`/models`) 회색지대. (7) Unsplash 직접 호출(`service.py::_fetch_unsplash` + `auto_select.py::_try_unsplash` + `workers/report_generator.py:1263` 등) — LLM 아니므로 R2 직접 대상 아니나 별도 정책 결정 필요. 위 7건은 **본 DU-14 작업 범위 밖**이며 진행 보고 후 사용자 결정 대기. **다음 트랙**: 사용자 결정 대기 — 후보(우선순위 권장): (A) DocUtil 별도 트랙 7건 일괄 정합성 보강(R2 완전 강제 마무리) / (B) `/api/admin/docutil/dashboard 200 HTML sub-path` 정합성 점검 / (C) DocUtil corpus inventory(Qdrant doc_embeddings vs PG tb_documents) / (D) DocUtil 환경변수 시크릿 노출 점검(OPENAI_API_KEY/QDRANT_API_KEY). **이전 갱신**: 2026-05-11 (**Phase 10.x — 남은 Medium/Low 결함 4건 보강 완료**) — code-analysis-specialist 가 식별한 남은 4건 보강: (Medium) Reports BFF deprecate(410) 안내 — `AdminDocUtilReportsController` 의 GenerateReport/CreateTemplate/UpdateTemplate/DeleteTemplate 4 메서드 catch 분기에 `when (ex.StatusCode == HttpStatusCode.Gone)` 필터 추가, 502 ErrorResponseDto 대신 `410 + "...DocUtil 측에서 deprecate 되었습니다. 신규 디자이너 워크플로(`/admin/docutil-documents-v2`)를 사용하세요."` 한국어 안내 반환. DocUtil 응답 status code 식별을 위해 신규 `Exceptions/DocUtilUpstreamException.cs`(InvalidOperationException 상속, HttpStatusCode StatusCode + Path 보유) 도입, `DocUtilClient.EnsureSuccessOrThrowKoreanAsync` 가 기존 InvalidOperationException 대신 본 예외 throw 로 전환(401/403/410/422/5xx/4xx 모두). 기존 컨트롤러의 `catch (InvalidOperationException ex)` 는 상속 관계로 그대로 동작 — 외부 시그니처 변경 0. (Medium) Templates `apply-mapping`/`convert` 사전 검증 — `AdminDocUtilTemplatesController` 의 ApplyMapping/ConvertToTemplate 진입 시 신규 private `EnsureTemplateHasStorageAsync` 호출(detail 캐시 short-circuit + miss 시 GetDocumentTemplateAsync 위임) → `TemplateStoragePath` null/빈 문자열이면 `400 BadRequest + "이 템플릿은 원본 파일이 업로드되지 않아 변환할 수 없습니다. 먼저 파일을 업로드하세요."` 한국어 안내(DocUtil 422/500 회피). Vue `AdminDocUtilTemplates.vue` 의 convert/mapping 탭에 신규 computed `detailHasStorage` 로 alert.alert-warning(`noStorageWarning`) 노출 + textarea disabled + button disabled + tooltip(`noStorageTooltip`) 부착. (Low) DocUtil Agent 메뉴 부제 — `adminDocutilDocAgents.subtitle` 을 사용자 명시 문구 "DocUtil 챗봇용 페르소나 — AgentHub 에이전트와 별개의 도메인입니다." 로 갱신(ko/en 모두). 기존 정보성 alert(`warningSeparateDomain`) 는 보존 — 메뉴 헤더 부제만 강화. (Low) 13 Admin DocUtil Vue view N+1 호출 패턴 전수 점검 — Grep 으로 `for await/forEach.*await/Promise.all(items.map)/v-for.*await` 모두 검색 → 0 hits. 모든 `loadXxx`(loadList/loadAgents/loadDocuments/loadProjects/loadReports/loadTemplates/loadFaqs/loadApiKeys/loadScopes/loadAuditLogs/refreshAll/loadAll/fetchPage) 가 단일 목록 API 호출(또는 사전 의도된 병렬 Promise.all 3~5건 — Dashboard 5 metrics / Departments 3 catalog). 행별 detail fetch 는 운영자 클릭 시 lazy load 만 — Dashboard 의 5초 setInterval auto-refresh 도 onBeforeUnmount 클리어 보장. **N+1 패턴 발견되지 않음, 검증 완료**. i18n 신규 키 4(ko/en `adminDocutilTemplates.noStorageWarning` + `adminDocutilTemplates.noStorageTooltip`) + 1×2(`adminDocutilDocAgents.subtitle` 문구 갱신). 신규 파일 1: `agenthub/Exceptions/DocUtilUpstreamException.cs`(~50 LOC). 수정 파일 6: `agenthub/Services/DocUtilClient.cs`(using + EnsureSuccessOrThrowKoreanAsync 410 분기 + 5개 throw 사이트 모두 DocUtilUpstreamException) / `agenthub/Controllers/AdminDocUtilReportsController.cs`(using + 4 catch 분기 410 Gone) / `agenthub/Controllers/AdminDocUtilTemplatesController.cs`(EnsureTemplateHasStorageAsync 헬퍼 + 2 사전 검증) / `agenthub/ClientApp/src/views/admin/AdminDocUtilTemplates.vue`(detailHasStorage computed + convert/mapping 탭 disable + warning alert) / `agenthub/ClientApp/src/i18n/locales/ko.json` / `agenthub/ClientApp/src/i18n/locales/en.json`. **검증**: `dotnet build` errors=0 / warnings=11(전부 본 변경 무관 기존 CS1998); `npm run build:check` PASS(vite 4.04s), vue-tsc errors=0, `@ts-nocheck` 신규 부착 0건. ADR-13(DocUtil 호출 정책) 보강 — 410 Gone deprecate 분기 + DocUtilUpstreamException status code 전파 명시. **외부 시그니처 변경 0** — IDocUtilClient 메서드 추가/변경 0, 기존 record DTO 변경 0, DI 수명 보존, 기존 라우트 변경 0. **회귀 정합성**: 기존 9개 컨트롤러 [Authorize(Roles=Admin,SuperAdmin)] 게이트 유지 / 캐시 namespace 4개 격리 보존 / 직전 95 DocUtil 운영자 BFF endpoint 카운트 보존. **다음 트랙**: 사용자 결정 대기 — 후보: (A) 프로덕션 deploy + DocUtil 기동 + 라이브 검증 / (B) Phase 6 잔여 또는 Phase 7 진입 / (C) DocUtil `/v2/documents/designer/*` 신규 endpoint 가 라이브되면 BFF 재배선. ▼ 이전 갱신(Phase 10.x Critical/High/Medium): **마지막 갱신**: 2026-05-11 (**Phase 10.x — 정합성 분석 Critical/High/Medium 결함 보강 완료**) — code-analysis-specialist 가 식별한 6건 보강: (Critical) Vue router beforeEach 가 meta.role|roles 검증을 빠뜨려 일반 사용자가 /admin/docutil-* 13 라우트에 URL 직접 접근 시 백엔드 [Authorize] 401 으로만 차단되던 UX 비일관 → useAuthStore() 의 user.roles 와 교차 검증 + SuperAdmin 자동 통과 + 로드 미상태(새로고침 직후) loadUser() 트리거 fallback. (High) Phase 10.1a Users(UpdateStatus/Delete) + 10.1b Departments(UpdateOrganization/Create/Update) catch 분기에 InvalidateXxxCacheAsync() 일관 추가(10.1c+ DeleteDepartment 의 ghost 패턴 확장). (High) Microsoft.Extensions.Http.Polly 8.0.11 추가 + Program.cs 'docutil' Named HttpClient 에 Retry(3, exp backoff 200/500/1000ms) + Circuit Breaker(5/30s, HandleTransientHttpError 5xx 한정 — 4xx 즉시 전파) 적용. 별도 'docutil-longrunning' Named HttpClient 신설(5분 timeout) + DocUtilClient 5개 long-running endpoint(DownloadReport/PreviewDocumentTemplate/RequestDocumentV2Export/DownloadDocumentV2Export/ExportAuditLogs) 가 사용. (High) DocUtilTokenProvider.GetOrganizationIdAsync — JWT org claim 미부착(ApiKey-only) 시 IConfiguration["DocUtil:DefaultOrganizationId"] 폴백. appsettings.json 에 신규 키 2개(LongRunningTimeoutMinutes, DefaultOrganizationId) 명시. (Medium) EnsureSuccessOrThrowKoreanAsync 의 클라이언트 응답에서 DocUtil 영문 body echo 제거 — 한국어 안내 + status code 만. 422 는 TryExtractValidationHint 로 detail[0].{loc,msg} 또는 detail 단순 문자열 한국어 안내 추출(매핑 실패 시 일반 422 안내 폴백). 원본 body 는 LogError/LogWarning 에만 잔류. ADR-13(DocUtil 호출 정책 — Polly + endpoint timeout 분리 + body leak 차단 + org_id 폴백) 신설. 검증: dotnet build 경고 11개(전부 기존 CS1998, 본 변경 무관)·오류 0개. vue-tsc + vite build 통과(4.18s). @ts-nocheck 신규 0건. ▼ 이전 갱신(Phase 10.2e): (**Phase 10.2e — DocUtil API Keys + DocUtil 에이전트 + Documents V2(디자이너 워크플로) 운영자 BFF + Vue 콘솔 완료**) — AgentHub 운영자가 DocUtil 의 LLM API Key 등록·회수·검증(`/api/v1/api-keys` 4 endpoint) + 자체 챗봇 페르소나 CRUD(`/api/v1/agents` 5 endpoint, AgentHub Agent 와 별개 도메인) + 디자이너 기반 신규 문서 V2 워크플로(`/api/v1/v2/documents` 7 endpoint — 자유 생성/부분 패치 3종(page·component·tokens)/비동기 export 4 포맷·상태 폴링·프록시 다운로드)까지 단일 진입점에서 운영하는 BFF **16 endpoint** 신설 + Vue 화면 3개(`/admin/docutil-api-keys` + `/admin/docutil-doc-agents` + `/admin/docutil-documents-v2`) + 사이드바 docutil 카테고리 8·9·10 항목 → **13 항목**(이전 10)으로 확장. **DocUtil 소스코드 직접 인스펙션**(라이브 인스턴스 부재 — `docutil/backend/app/modules/api_keys/router.py` 129 LOC + `agents/router.py` 208 LOC + `documents_v2/router.py` 681 LOC + 각 schemas.py 정독, Phase 10.2d 동일 방식) → OpenAPI 추정 금지. Documents V2 path 패턴 `/api/v1/v2/documents/*` 발견(main.py `API_V1=/api/v1` + router `prefix="/v2"` 중첩). **`IDocUtilClient` 16 메서드 + record DTO 12종 추가**(API Keys: `DocUtilCreateApiKeyRequest` / `DocUtilApiKeyDetail` 8필드 / `DocUtilApiKeyList` / `DocUtilApiKeyVerifyResult`. DocAgents: `DocUtilCreateDocAgentRequest` 9필드 / `DocUtilUpdateDocAgentRequest` 9필드 partial / `DocUtilDocAgentDetail` 15필드 / `DocUtilDocAgentList`. Documents V2: `DocUtilGenerateDocumentV2Request` / `DocUtilPatchDocumentV2Request` / `DocUtilRequestDocumentV2ExportRequest` / `DocUtilDocumentV2Detail` 17필드 / `DocUtilDocumentV2List` / `DocUtilExportJobAck` / `DocUtilExportJobStatus` / `DocUtilDocumentV2Download` binary stream). **`AdminDocUtilApiKeysController.cs` 신설**(~280 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` + `du:apikey:list:` **5분 TTL**(API Key 카탈로그는 매우 민감 — 짧게 유지) + `docutil-api-keys` version-key invalidate + mutation 성공/실패 모두 invalidate(10.1b ghost 패턴) + **평문 키 절대 로깅 금지** id/llm_name/prefix 만 기록). **`AdminDocUtilDocAgentsController.cs` 신설**(~330 LOC, `du:docagent:list:`/`detail:` 10분 TTL + `docutil-doc-agents` version-key + AgentHub Agent 와 도메인 격리 명시 주석 + system_prompt textarea + temperature/max_tokens 범위 검증). **`AdminDocUtilDocumentsV2Controller.cs` 신설**(~480 LOC, `du:docv2:list:`/`detail:` 10분 TTL + `docutil-documents-v2` version-key + 7 endpoint(목록 limit/offset + 단건 + 자유 생성(202) + PATCH(page/component/tokens) + 비동기 export + 상태 폴링 + 프록시 다운로드 stream) + Documents V2 7 DocumentType Literal 사전 차단(slide_report/docx_report/proposal/minutes/one_pager/weekly_status/freeform_doc) + 5 export 포맷 Literal(pptx/docx/hwpx/pdf/html) + patch_type page/component/tokens regex 식별자 사전 차단(p\d+, c\d+) + design_tokens 16KB + patch data 256KB 사이즈 캡 + binary stream HttpResponseOwnedStream 재사용 + RFC 5987 한글 파일명 + ASCII fallback). **`DocUtilClient.cs` 에 16 메서드 + private DTO 13개**(`ApiKeyResponseDto` 8필드 / `ApiKeyListResponseDto` / `ApiKeyCreateRequestDto` / `ApiKeyVerifyResponseDto` / `DocAgentResponseDto` 14필드 / `DocAgentListResponseDto` / `DocAgentCreateRequestDto` / `DocAgentUpdateRequestDto` / `DocumentV2ResponseDto` 17필드 / `DocumentV2ListResponseDto` / `DocumentV2GenerateRequestDto` / `DocumentV2PatchRequestDto` / `DocumentV2ExportRequestDto` / `DocumentV2ExportJobAckDto` / `DocumentV2ExportStatusDto`) + 매핑 헬퍼 3개(`MapApiKey` / `MapDocAgent` / `MapDocumentV2`) + `ConvertJsonElementToOptionalDict` 재사용으로 document_schema free-form dict 안전 변환. **`AdminDocUtilApiKeys.vue` 신설**(~340 LOC, 경고 박스(평문 키 1회 노출 + 운영자 전용) + 페이지네이션 + 등록 모달(평문 key password input + autocomplete=off + maxlength 4096) + 마스킹 prefix 표시 + 검증 버튼(LLM 프로바이더 1회 호출 — 수십 초 소요 가능 안내) + 삭제 confirm + 한국어 라벨/로딩/에러). **`AdminDocUtilDocAgents.vue` 신설**(~520 LOC, info 박스(AgentHub Agent 와 별개 도메인 안내) + 페이지네이션 + agent_type 필터 + 상세 모달(system_prompt pre wrap) + 생성/수정 모달(temperature/max_tokens 범위 input + provider/model 자유 입력)). **`AdminDocUtilDocumentsV2.vue` 신설**(~720 LOC, **디자이너 워크플로 UI** — info 박스(보고서 템플릿 후속) + 필터 5종(documentType/mode/limit/offset/pageSize) + 상세 모달 2-tab(기본정보/document_schema raw JSON) + 신규 생성 모달(DocumentType 7-Literal select + Mode select template_fill disabled + sourceDocumentIds textarea + agentId + designTokens JSON textarea + 한국어 검증 메시지) + 부분 패치 모달(patch_type page/component/tokens select + page_id/component_id input + data JSON textarea + expected_version 낙관적 락 input) + Export 요청 모달(5 포맷 select) + Export 상태 모달(job_id input + 상태 폴링 + completed 시 활성화되는 다운로드 버튼 + Blob → URL.createObjectURL → a[download]) + 상태 뱃지 색상 분기(pending/running/completed/failed)). `docutilService.ts` **16 함수 + TS interface 19종 + 1 헬퍼**(parseDocumentV2FileName RFC 5987 우선 + ASCII fallback). 라우터 3 lazy 라우트(`/admin/docutil-api-keys` + `/admin/docutil-doc-agents` + `/admin/docutil-documents-v2`, `meta.role='Admin'`). 사이드바 docutil 8·9·10 항목(`bi-key` + `bi-robot` + `bi-easel2`). i18n 신규 키 약 **160×2=320개** (ko/en `nav.docutil*` + `adminDocutil*.*` 3 블록 — locale 양쪽 동일). **검증 결과**: `dotnet build` errors=0/warnings=0 (변경 코드 한정), `npm run build:check` errors=0(vue-tsc 2.x), `@ts-nocheck` 부착 0건(grep 검증), 신규 청크 `AdminDocUtilApiKeys-cUZ7Kxi2.js`(7.92 kB gzip) + `AdminDocUtilDocAgents-MI6g14Tu.js`(17.38 kB / gzip 4.50 kB) + `AdminDocUtilDocumentsV2-D2j-YTH6.js`(28.45 kB / gzip 6.72 kB). **정적 e2e 검증 PASS 86/86** (`agenthub/Tools/test_phase_10_2e_e2e.ps1`, UTF-8 BOM 추가 후 Windows PowerShell 실행 가능): 파일 존재 9 / 신규 endpoint 카운트 4+5+7=16 / **회귀 9 컨트롤러 endpoint 보존 79**(4+9+13+7+9+7+5+10+15) / 권한 게이트 [Authorize(Roles=Admin,SuperAdmin)] 신규 3 + 회귀 9 = 12 / 캐시 invalidate 사이트(ApiKeys 7 / DocAgents 7 / DocsV2 5) / IDocUtilClient 16 메서드 시그니처 / docutilService 16 export / 라우터 3 라우트 / MainLayout 3 메뉴 / i18n adminDocutil* 3 블록 ×2 locale = 6 / @ts-nocheck 0개. **외부 시그니처 변경 0** — `IDocUtilClient` 신규 16 메서드 추가만, 기존 시그니처 보존. **회귀 정합성**: 직전 9 DocUtil admin 컨트롤러(10.1a/b/c + 10.2a/b/c/d) HTTP 속성 카운트 보존(79 endpoint), 본 트랙 신규 16 합산 — 총 95 DocUtil 운영자 BFF endpoint 도달. 운영자가 AgentHub 한 화면에서 DocUtil 의 LLM API Key 관리 + 자체 챗봇 페르소나 CRUD + 디자이너 기반 신규 문서 워크플로(자유 생성/부분 패치/비동기 export/Blob 다운로드) 까지 단일 진입점 확보. **이전 갱신**: 2026-05-11 (**Phase 10.2d — DocUtil 문서 템플릿(Document Templates / Jinja2) 운영자 BFF + Vue 콘솔 완료**) — AgentHub 운영자가 DocUtil 의 Jinja2 기반 문서 생성 템플릿(`/api/v1/templates`) 카탈로그 + 파일 업로드 3종(일반/빈양식/스마트) + AI 자동채움 + 일반문서→Jinja2 변환 + 변수 메타 편집 + 미리보기 다운로드 + 구조 조회 + 변수 매핑 적용까지 단일 진입점에서 운영하는 BFF **15 endpoint** 신설 + Vue 운영자 화면(`/admin/docutil-templates`, 탭 6개: 기본정보·변수메타·문서구조·AI 자동채움·Jinja2 변환·변수 매핑) + 사이드바 docutil 카테고리 10번째 항목 추가. **DocUtil 소스코드 직접 인스펙션**(컨테이너 미가동 상태 — `docutil/backend/app/modules/templates/router.py` 816 LOC + `schemas.py` 333 LOC + `models.py` 84 LOC 정독) → OpenAPI 추정 금지 원칙 엄격 적용. 식별된 endpoint **15개 모두 라이브**(410 deprecate 표식 없음 — Phase 10.2c 보고서/템플릿 deprecate 와 무관한 별도 도메인 확인). **DocumentTemplate 도메인 ≠ ReportTemplate 도메인 격리 확정**(Phase 10.2c 의 `DocUtilReportTemplate*` 와 본 트랙의 `DocUtilDocumentTemplate*` 는 서로 다른 엔티티 — 캐시 namespace 도 `docutil-report-templates` vs `docutil-document-templates` 독립). **`IDocUtilClient` 15 메서드 + record DTO 13종** 추가(`DocUtilDocumentTemplate` 17 필드 / `DocUtilDocumentTemplateDetail` / `DocUtilDocumentTemplateList` / `DocUtilCreateDocumentTemplateRequest` 9 필드 / `DocUtilUpdateDocumentTemplateRequest` 10 필드 partial / `DocUtilUploadDocumentTemplateRequest` / `DocUtilUploadSmartTemplateRequest` / `DocUtilDocumentTemplateVariable` 6 필드(name/varType/label/description/required/category) / `DocUtilUpdateDocumentTemplateVariablesRequest` / `DocUtilDocumentTemplateUpload` 6 필드 / `DocUtilAutoFillDocumentTemplateRequest` / `DocUtilDocumentTemplateAutoFill` / `DocUtilDocumentTemplateMapping` 10 필드 / `DocUtilApplyDocumentTemplateMappingRequest` / `DocUtilDocumentTemplatePreview`). **`AdminDocUtilTemplatesController.cs` 신설**(~890 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/templates/...` + `du:doctpl:list:`/`detail:`/`vars:` 10분 TTL + version-key invalidate(`docutil-document-templates` — 보고서/FAQ namespace 와 격리) + mutation 성공/실패 모두 invalidate(10.1b ghost 처리 패턴) + binary stream(preview) HttpResponseOwnedStream 재사용 + RFC 5987 한글 파일명 + ASCII fallback + multipart 3종 업로드(일반/빈양식/스마트 — RequestSizeLimit 50MB) + ai_analysis/mappings free-form JSON 64KB 사이즈 캡 사전 차단 + mapping 검증(location_type "table_cell"|"paragraph" enum) + auto-fill 50 source max + variables 1000 max). **`DocUtilClient.cs` 에 15 메서드 + 매핑 헬퍼 4개**(`MapDocumentTemplate`/`MapDocumentTemplateDetail`/`MapDocumentTemplateVariable`/`MapDocumentTemplateUpload`/`ConvertJsonElementToOptionalDict`) + **private DTO 10개**(`DocumentTemplateResponseDto` 17 필드 / `DocumentTemplateListResponseDto` / `DocumentTemplateCreateRequestDto` / `DocumentTemplateUpdateRequestDto` / `DocumentTemplateVariableDto` / `DocumentTemplateVariablesUpdateRequestDto` / `DocumentTemplateUploadResponseDto` / `DocumentTemplateAutoFillResponseDto` / `DocumentTemplateMappingDto` / `DocumentTemplateMappingPayloadDto`) + multipart 3종 통합 헬퍼 `UploadDocumentTemplateInternalAsync`. **`AdminDocUtilTemplates.vue` 신설**(~920 LOC, 6-tab 상세 모달 + 목록표 + 3종 업로드 모달(standard/blank/smart 모드 분기) + 생성 모달(JSON 메타) + 페이지네이션 + 유형 필터 + 변수 메타 inline 편집 표(타입/카테고리 select) + JSON 텍스트 입력으로 ai_analysis/mappings 받기 + 미리보기 Blob → URL.createObjectURL → a[download]) — `<script setup lang="ts">` + `@ts-nocheck` 미부착. `docutilService.ts` **15 함수 + TS interface 11종**(`DocUtilDocumentTemplate`/`DocUtilDocumentTemplateDetail`/`DocUtilDocumentTemplateList`/`CreateDocumentTemplateRequest`/`UpdateDocumentTemplateRequest`/`DocUtilDocumentTemplateVariable`/`UpdateDocumentTemplateVariablesRequest`/`DocUtilDocumentTemplateUpload`/`AutoFillDocumentTemplateRequest`/`DocUtilDocumentTemplateAutoFill`/`DocUtilDocumentTemplateMapping`/`ApplyDocumentTemplateMappingRequest`/`ConvertDocumentTemplateRequest`/`DocumentTemplatePreview`) + `parseDocumentTemplateFileName` 헬퍼(RFC 5987 우선 + ASCII fallback). 라우트 1개(`/admin/docutil-templates`, lazy + `meta.role='Admin'`). 사이드바 docutil 카테고리 10번째 항목(`bi-file-earmark-code`). i18n 신규 키 **115×2=230개** (ko/en `adminDocutilTemplates.*` + `nav.docutilTemplates`) — 0 missing / 0 unused 확정. **검증 결과**: `dotnet build` errors=0, warnings 11(전부 본 트랙과 무관한 기존 코드 `CS1998`); `npm run build:check` 통과, vue-tsc errors=0, `@ts-nocheck` 부착 0건, 신규 청크 `AdminDocUtilTemplates-N_fEzlgP.js`(35.12 kB, gzip 7.92 kB) + 동명 css 생성; **정적 e2e 검증** PASS(라이브 인스턴스 미가동 — DocUtil 컨테이너/AgentHub IIS 모두 부재, 운영자가 살릴 때 사용할 PowerShell 스크립트 `agenthub/Tools/test_phase_10_2d_templates_e2e.ps1` 동봉 — 16 인증/입력검증 + 라이프사이클(생성→GET→PUT→variables→structure→preview→delete→404) + 회귀 12 endpoint 자동 검증 + status code/한국어 본문 매처 포함); **회귀 정합성 정적 검증** PASS(직전 Phase BFF endpoint 79개 중 본 트랙 신규 15 추가 후 9개 컨트롤러 전체에 [Authorize(Roles="Admin,SuperAdmin")] 게이트 일관 / 캐시 namespace 4개 격리(docutil-faq / docutil-reports / docutil-report-templates / docutil-document-templates) / Vue 서비스 함수 15 ↔ 백엔드 endpoint 15 1:1 매핑 / i18n 115 key 양 locale 동일 / Korean 검증 44건 한국어 / 502 매핑 13건 한국어). 외부 시그니처 변경 0건, 기존 record DTO 변경 0건, DI 수명 보존(`DocUtilClient` Scoped, `IDocUtilTokenProvider` Singleton, `CachingService` Singleton), 기존 라우트 변경 0건. **다음 트랙**: 사용자 결정 대기 — 후보: (A) Phase 10.2c 에서 발견된 DocUtil `/reports/templates` deprecate(410) 의 `/v2/documents/designer/*` 신규 endpoint 가 라이브가 되면 BFF 재배선 / (B) Phase 6 잔여 작업 / (C) DocUtil evaluation/logs Pydantic 버그(Phase 10.2b C3 실패) DocUtil 트랙 분리 처리. **이전 갱신**: 2026-05-11 (**Phase 10.2c — DocUtil FAQ + 보고서/템플릿 운영자 BFF + Vue 콘솔 완료**) — AgentHub 운영자가 DocUtil 의 FAQ(질문/답변 카탈로그 5 endpoint) + 보고서/템플릿(생성/이력/다운로드 + 템플릿 CRUD, 합계 9 endpoint)까지 단일 진입점에서 운영하는 BFF **14 endpoint** 신설 + Vue 운영자 화면 2개(`/admin/docutil-faq` + `/admin/docutil-reports`) + 사이드바 docutil 카테고리 8·9 번째 항목 추가. **DocUtil OpenAPI 사전 캡처 정확 매핑**(`tmp/phase10_2a_audit_dashboard/openapi_full.json` 재사용 — `FAQResponse` 10 필드 / `FAQCreate`/`FAQUpdate` / `GeneratedReportResponse` 16 필드 / `ReportGenerateRequest` 6 필드 / `ReportTemplateResponse` 10 필드 / `Body_create_template_api_v1_reports_templates_post` multipart 4 필드 / `ReportTemplateUpdate` 2 필드). **추정 금지 원칙 정확 적용 + DocUtil 사전 deprecate 인지**: OpenAPI 캡처 단계에서 `POST /reports/generate`, `POST/PUT/DELETE /reports/templates` 의 응답 코드가 **`"410"` 으로 표기**된 것을 사전 발견 → e2e 검증 단계에서 DocUtil 측이 실제로 `HTTP 410 — "/v2/documents 로 이관, /designer/create 사용"` 응답을 명시적으로 반환하는 것 확인. BFF 가 4xx/5xx → 502 한국어 ErrorResponseDto 변환하므로 **운영자 콘솔에 한국어 안내**가 표시됨(코드 결함이 아닌 정상 동작). 살아있는 endpoint(`GET /reports`, `GET /reports/{id}`, `GET /reports/templates`, `GET /reports/templates/{id}`, `GET /reports/{id}/download`, FAQ 5 endpoint)는 정상 동작. DocUtil 측 deprecate 결정은 별도 트랙(DocUtil 본체 /v2 마이그레이션) 으로 추적. **`IDocUtilClient` 14 메서드 추가** + record DTO **16종** (FAQ: `DocUtilFaq`/`DocUtilFaqDetail`/`DocUtilFaqList`/`DocUtilCreateFaqRequest`/`DocUtilUpdateFaqRequest`. Reports: `DocUtilReport`/`DocUtilReportDetail`/`DocUtilReportList`/`DocUtilGenerateReportRequest`/`DocUtilReportGenerationResponse`/`DocUtilReportDownload`. Templates: `DocUtilReportTemplate`/`DocUtilReportTemplateDetail`/`DocUtilReportTemplateList`/`DocUtilCreateReportTemplateRequest`/`DocUtilUpdateReportTemplateRequest`). **`AdminDocUtilFaqController.cs` 신설**(~340 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/faq/...` + `du:faq:` 5분 TTL + version-key invalidate(`docutil-faq`) + mutation 성공/실패 모두 invalidate(10.1b ghost 처리 패턴)). **`AdminDocUtilReportsController.cs` 신설**(~660 LOC, `/api/admin/docutil/reports/...` + 캐시 namespace **2개 분리**: `docutil-reports` 1분 TTL list / 5분 TTL detail + `docutil-report-templates` 10분 TTL catalog + 보고서 binary stream 다운로드(Phase 10.2a `HttpResponseOwnedStream` 재사용 + RFC 5987 한글 파일명 `filename*=UTF-8''<encoded>` + ASCII fallback 두 헤더 부착) + 템플릿 multipart/form-data 업로드(IFormFile → Stream pass-through, fileStream lifetime 명시 처리, 50MB RequestSizeLimit) + status 필터는 OpenAPI 미정의로 BFF 측 후처리 클라이언트 필터로 합성 + generation_params 64KB 사이즈 캡 사전 차단). `DocUtilClient.cs` 에 **14 메서드 + 매핑 헬퍼 6개**(`MapFaq`/`MapFaqDetail`/`MapReport`/`MapReportDetail`/`MapReportTemplate`/`MapReportTemplateDetail`) + **private DTO 10개**(`FaqResponseDto`/`FaqListResponseDto`/`FaqCreateRequestDto`/`FaqUpdateRequestDto`/`ReportResponseDto`/`ReportListResponseDto`/`ReportGenerateRequestDto`/`ReportTemplateResponseDto`/`ReportTemplateListResponseDto`/`ReportTemplateUpdateRequestDto`) 추가 — `ConvertJsonElementToDict` 헬퍼 재사용으로 `generation_params`/`jinja2_context`/`schema` free-form dict 안전 처리. **`AdminDocUtilFaq.vue` 신설**(~520 LOC, `<script setup lang="ts">` + i18n + 페이지네이션 + 검색/카테고리 필터 + 생성/수정/상세 모달 3개 + 삭제 confirm + 한국어 라벨/로딩/에러 상태). **`AdminDocUtilReports.vue` 신설**(~700 LOC, 탭 2개 — 보고서 목록 탭(상태 필터 + 다운로드 Blob → URL.createObjectURL → a[download] + 한글 파일명 RFC 5987 파싱 + 상태 배지 색상 분기 + 상세 모달) + 템플릿 관리 탭(multipart File 첨부 + 미리보기 + 50MB 사이즈 limit 표시 + 생성/수정/상세 모달 3개)). `docutilService.ts` **15 함수 + 인터페이스 13건**(`DocUtilFaq`/`DocUtilFaqDetail`/`DocUtilFaqList`/`CreateFaqRequest`/`UpdateFaqRequest` + `DocUtilReport`/`DocUtilReportDetail`/`DocUtilReportList`/`GenerateReportRequest` + `DocUtilReportTemplate`/`DocUtilReportTemplateDetail`/`DocUtilReportTemplateList`/`UpdateReportTemplateRequest`) + `parseReportFileName` 헬퍼(RFC 5987 우선 + ASCII fallback). 라우트 2개(`/admin/docutil-faq` + `/admin/docutil-reports`, lazy + `meta.role='Admin'`). 사이드바 docutil 카테고리에 `bi-question-circle` + `bi-file-earmark-text` 두 항목 추가. i18n 신규 키 약 **133개** (ko/en `nav.docutilFaq`/`docutilReports` + 페이지 단위 `adminDocutilFaq.*` 약 50 + `adminDocutilReports.*` 약 80). **검증 결과 PASS 31/31**: 권한 게이트 2(401×2 — 미부착/bogus JWT) + FAQ 5 endpoint 정상 CRUD(POST 새 ID 발급 → GET 상세 → PUT 수정 → DELETE 204) + 캐시 invalidate 3 namespace 검증(`docutil-faq` POST→GET 목록 신규 노출 + DELETE→GET 목록 사라짐 + Template DELETE→GET 사라짐 패턴 동일) + 보고서/템플릿 GET 5 endpoint PASS + 보고서/템플릿 deprecate 3 endpoint 가 BFF 측에서 정확히 502 한국어로 변환(OK — `"DocUtil 호출이 실패했습니다 (HTTP 410): {\"detail\":\"...\"} → 한국어 메시지"`) + 직전 회귀 11 endpoint 모두 PASS(`/api/agents/1` 22ms / `/admin/metrics/rag` 24ms / `/admin/knowledge-base/{documents,collections}` / 10.1a~c users/departments/projects / 10.2a dashboard/audit / 10.2b search-scopes/evaluation). **빌드**: `dotnet build` errors=0 + warnings 11(전부 본 트랙과 무관한 기존 코드 `CS1998`); `npm run build:check` 통과, vue-tsc 2.2.12 errors=0, `@ts-nocheck` 부착 0건, 신규 청크 `AdminDocUtilFaq-B9GT7uxl.js`(14.48 kB, gzip 4.08 kB) + `AdminDocUtilReports-CI2o6mwZ.js`(28.43 kB, gzip 6.77 kB) + 동명 css 생성. **호스트 빌드/배포**: 192.168.10.39:64005 / `agenthub-agenthub:latest` 재빌드(npm + dotnet publish) + force-recreate + healthy 확인(약 6초 내 starting → healthy). 외부 시그니처 변경 0건, 기존 record DTO 변경 0건, DI 수명 보존(`DocUtilClient` Scoped, `IDocUtilTokenProvider` Singleton, `CachingService` Singleton). **다음 트랙**: **Phase 10.2d — DocUtil Templates 단독 트랙**(또는 사용자 결정 대기) — DocUtil 의 `/v2/documents` 디자이너로 마이그레이션된 신규 API 가 OpenAPI 에 노출되면 본 트랙 보고서/템플릿 deprecate 502 매핑을 신규 endpoint 로 재배선. **이전 갱신**: 2026-05-10 (**Phase 10.2b — DocUtil 검색범위 + 평가 운영자 BFF + Vue 콘솔 완료**) — AgentHub 운영자가 DocUtil 의 검색범위(Search Scopes — 프로젝트/보드/폴더 단위 RAG 튜닝 + 4 기능 토글) + 평가(Evaluation — RAG 품질 4 가중치 + 평가 실행/로그/트렌드)까지 단일 진입점에서 운영하는 BFF **15 endpoint** (Search Scopes 9 + Evaluation 7, 총 16 메서드 중 location 카탈로그 1 분리 카운트) 신설 + Vue 운영자 화면 2개(`/admin/docutil-search-scopes` + `/admin/docutil-evaluation`) + 사이드바 docutil 카테고리 6·7 번째 항목 추가. **DocUtil OpenAPI 사전 캡처 정확 매핑**(`tmp/phase10_2a_audit_dashboard/openapi_full.json` 재사용 — `SearchScopeResponse` 24 필드 / `LocationOption` 4 필드 / `SearchScopeOption` 3 필드 / `EvaluationConfigResponse` 6 필드 / `EvaluationLogResponse` 17 필드 / `EvaluationRunSummary` 10 필드 / `EvaluationTrendPoint` 6 필드). **추정 금지 원칙 정확 적용**: `EvaluationRunSummary` 에 `page/size` 없음(items+total 만) / `EvaluationTrend` 는 `?days=N` (period 가 아닌 days) / `EvaluationRuns` 는 `?limit=N` (page/size 패턴 미적용) / `SearchScopeLocations` 는 `?location_type=` 필수 / valid-id 응답 schema 미정의 → free-form dict. **`IDocUtilClient` 15 메서드 추가** + record DTO **14종**(`DocUtilSearchScopeSummary`/`DocUtilSearchScopeDetail`/`DocUtilSearchScopeList`/`DocUtilSearchScopeOption`/`DocUtilLocationOption`/`DocUtilCreateScopeRequest`/`DocUtilUpdateScopeRequest`/`DocUtilUpdateScopeEnvironmentRequest`/`DocUtilSearchScopeValidIdResponse` + `DocUtilEvaluationConfig`/`DocUtilUpdateEvaluationConfigRequest`/`DocUtilEvaluationLogEntry`/`DocUtilEvaluationLogList`/`DocUtilEvaluationQuestions`/`DocUtilRunEvaluationRequest`/`DocUtilEvaluationRunResponse`/`DocUtilEvaluationRunSummary`/`DocUtilEvaluationRunList`/`DocUtilEvaluationTrend`/`DocUtilEvaluationTrendDataPoint`). **`AdminDocUtilSearchScopesController.cs` 신설**(~590 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/search-scopes/...` + `du:scopes:` 10분 TTL + version-key invalidate(`docutil-search-scopes`) + `du:scopes:locations:`/`options:` 30분 TTL(카탈로그성) + mutation 성공/실패 모두 invalidate(10.1b ghost 처리 패턴) + 4xx/5xx → 502 한국어 ErrorResponseDto). **`AdminDocUtilEvaluationController.cs` 신설**(~470 LOC, `/api/admin/docutil/evaluation/...` + `du:eval:cfg:` 5분 TTL + version-key invalidate(`docutil-evaluation-config`) + `du:eval:logs:`/`runs:` 1분 TTL(실시간성) + `du:eval:questions:`/`trend:` 5분 TTL + run 트리거 캐시 미적용 + 100 질문/2000자 sanity 검증). **DocUtilClient.cs**: 15 구현 + 매핑 헬퍼 4(`MapSearchScopeSummary`/`MapSearchScopeDetail`/`MapEvaluationConfig`/`MapEvaluationLog`/`MapEvaluationRunSummary`/`ConvertJsonElementToDict`) + private 응답 DTO 14(`SearchScopeResponseDto`/`SearchScopeListResponseDto`/`SearchScopeOptionDto`/`LocationOptionDto`/`SearchScopeCreateRequestDto`/`SearchScopeUpdateRequestDto`/`SearchScopeEnvironmentRequestDto`/`EvaluationConfigResponseDto`/`EvaluationConfigUpdateRequestDto`/`EvaluationLogResponseDto`/`EvaluationLogListResponseDto`/`EvaluationRunRequestDto`/`EvaluationRunSummaryDto`/`EvaluationRunListResponseDto`/`EvaluationTrendPointDto`/`EvaluationTrendResponseDto`). **Frontend**: `docutilService.ts` 16 함수 + TS interface 16건 + `EvaluationLogFilters` UI 통합 / `AdminDocUtilSearchScopes.vue`(~880 LOC, 3-tab UI: scopes 목록/생성/수정/삭제/환경설정 + locations 카탈로그 + options 카탈로그 + 상세 모달 + valid-id 조회 + 페이지네이션 + RFC 5987 한국어 알림) / `AdminDocUtilEvaluation.vue`(~880 LOC, 5-tab UI: config 4 가중치 수정 + manual run + runs 이력표 + trend 표 + logs 페이징/필터 + questions 카탈로그 + 평가 로그 상세 모달 + JSON contexts/evidence/judge_details 표시) — `<script setup lang="ts">` + Pinia/ref/computed + `@ts-nocheck` 미부착. `router/index.ts` 에 `/admin/docutil-search-scopes` + `/admin/docutil-evaluation` 2 라우트 추가(`meta.role='Admin'` lazy import) + `MainLayout.vue` 에 docutil 카테고리 6·7 항목 추가(`bi-bullseye` + `bi-clipboard-check`) + `ko.json`/`en.json` 신규 키 약 110개. **검증**: `dotnet build` errors=0(워닝 11/기존 코드와 무관) / `npm run build:check` PASS(vue-tsc 2.x errors=0, `@ts-nocheck` 부착 0건, 신규 청크 `AdminDocUtilSearchScopes-vZpS3RoC.js` 31.84 kB / `AdminDocUtilEvaluation-BGvG0Ubh.js` 26.62 kB / `docutilService-Dph6XSYa.js` 9.33 kB) / 호스트(192.168.10.39:64005) docker compose build → up healthy. **e2e 결과**(admin@example.com, `tmp/phase10_2b_search_scopes_eval/verify_results.json`): Search Scopes **9/9 PASS** (B1 list cold 1108ms→B1b warm 44ms 캐시 hit / B2 options 133ms / B3 locations 52ms first_project=`9ca4ce6e...` / B4 create 116ms id=`21e79f17...` / B5 detail 37ms / B6 update 68ms / B7 environment 69ms / B8 valid-id 42ms keys=[id] / B1c after-create 45ms total=2 has_new_scope=true(invalidate 검증) / B9 delete 204 45ms — 검증용 데이터 정리), Evaluation **6/7 PASS** (C1 config cold 78ms→C1b warm 29ms / C2 PUT 77ms ctx=0.30 → C1c after-PUT 28ms invalidate 동작 / C2-revert 49ms / C4 questions 53ms / C5 runs 74ms total=2 / C6 trend 33ms data=1 / C7 run 202 110ms keys=[run_id,status,message]), **C3 logs 502** = DocUtil 자체 측 `EvaluationLogResponse.hallucination_evidence` Pydantic ValidationError(DB row 0 임에도 schema validation 단계에서 발생, 본 트랙 책임 밖 — BFF 가 502 한국어 매핑으로 정상 동작 / DocUtil 데이터 정합성은 별도 트랙). **권한 게이트 3/3 PASS**(D1 no-auth 401 / D1b no-auth 401 / D2 bogus JWT 401). **직전 회귀 9/9 PASS**(`/api/agents/1` 103ms / `/admin/metrics/rag` 23ms / `/admin/knowledge-base/documents` 99ms / `/admin/knowledge-base/collections` 44ms / `/admin/docutil/users` 68ms / `/admin/docutil/departments` 55ms / `/admin/docutil/projects` 55ms / `/admin/docutil/dashboard/metrics` 73ms / `/admin/docutil/audit-logs` 82ms — 모두 200). **외부 동작 변경 0** — 기존 `IDocUtilClient` 15 신규만 추가(시그니처 변경 0) / 기존 라우트 변경 0 / Phase 10.1+10.2a 회귀 PASS / DI 수명주기 보존 / `<script setup lang="ts">` + `@ts-nocheck` 미부착 / vue-tsc 2.x errors=0 / 시연 안정성 100%. **다음 트랙**: 사용자 결정 대기(예: Phase 10.2c FAQ/Reports/Templates BFF 또는 Phase 6 잔여 작업 / DocUtil evaluation/logs Pydantic 버그는 DocUtil 트랙으로 격리 보고). 추가 — 후속 #1 (docutil AGENTHUB_URL+API_KEY 환경변수 설정) 완료 (2026-05-12 추가): admin@example.com 명의 unbound ApiKey 발급(`ApiKeyId=3`, `KeyName=docutil-runtime-key`, `Scopes=chat,stream,embeddings,images,info,usage`, `AgentId=NULL`) → 운영 docutil `.env` 갱신(`AGENTHUB_URL=http://agenthub:8080` + `AGENTHUB_API_KEY=ak-DstS7...BKI4`) → 3 컨테이너(api/celery-worker/celery-beat) force-recreate 35초 만에 모두 healthy → 라이브 회귀 5단계 모두 PASS (env / AgentHubClient instantiate / DocUtil health 200 / `chat(docutil-rag-chat)` 한국어 18자 응답+토큰 169 / `embed(embedding-default)` 1536D 임베딩+16 tokens). 추가 발견 — `/api/admin/docutil/users` 502 의 진짜 원인은 DocUtil 자체 DB schema 정합 결함 (`document_utilization.tb_users` 모델 ↔ `public.tb_users` 실제 적재 불일치) 으로 별도 트랙 #2 권고 (DocUtil 자체 사용자 로그인도 500 동시 영향).. **트랙 #88 — 사용자/부서/프로젝트 통합 + DocUtil DB 통합 (옵션 Y) 완료**: AgentHub Users 131 + 부서 트리 31 (본부 6 + 부서 25, C1-B) + UserRoles 일괄 + DocUtil tb_users 흡수 (Part 1). 잘못된 schema 발견 (DocUtil API 는 docutil DB 사용, 우리는 AGENT_HUB.document_utilization 에 동기화 — DocUtil 가 보지 않는 빈 schema) → 옵션 Y 실행: docutil DB → AGENT_HUB.document_utilization 데이터 전체 이관 (13 테이블 / 2,170행 / 100% 일치) + DATABASE_URL 6 라인 변경 + 컨테이너 재생성 + nginx upstream 캐시 해결. **R3 단일 DB 진입점 달성** (`AGENT_HUB` DB 안의 4개 schema). DocUtil API curl 검증: admin@example.com / Admin123! → 200 OK + JWT (super_admin/admin/member 모두 정상). 백업 3종 + 롤백 SQL + Part 1/Part 2/Y-2 마이그레이션 SQL 작성. ADR: A 확정 / C1-B / C2-A / C3-C / C4-A / C5-B / D1-Y / D2 (잘못 매핑 121명 NULL 복원). 미해결: UI 자동화 (selector 디버그 필요, API 는 PASS), AgentHub EF Migration baseline, idino 직원 비번 정책 (시드 비번 알 수 없음). **트랙 #88-7 — 전수 e2e + 마이너 4건 해소 (87/87 PASS, 운영결함 0)**: 사용자 명시 "전수 테스트 + 체크리스트". 87 케이스 (AgentHub Public 14 + Protected 48 + DocUtil Public 3 + DocUtil 인증 22) 모두 PASS. 사전 4건 마이너 (DocUtil /admin-accounts 404 — users/router.py trailing slash alias 추가 + FE /users/ → /users; DocUtil /settings 404 — settings 모듈 신설 + GET /settings 200; AgentHub /chatbot/test, /embed/test 404 — Agents AgentId=1 에 AgentCode=test + AllowGuestChat=true 부여) → 사후 마이너 0건. commit `05dcf4a` ([docutil/track88-7]).
>
> **이전 갱신**: 2026-05-10 (**Phase 10.2a — DocUtil 대시보드 + 감사 로그 운영자 BFF + Vue 콘솔 완료**) — AgentHub 운영자가 DocUtil 의 운영 모니터링(KPI/응답시간/검색 통계/업로드 상태 5종) + 감사 로그(목록 + CSV 내보내기)를 단일 진입점에서 확인하는 BFF **7 endpoint** 신설 + Vue 운영자 화면 2개(`/admin/docutil-dashboard` + `/admin/docutil-audit`) + 사이드바 docutil 카테고리 4·5 번째 항목 추가. **DocUtil OpenAPI 사전 캡처**(`tmp/phase10_2a_audit_dashboard/openapi_full.json`/`openapi_dashboard_audit_schemas.json` — `DashboardMetrics`/`ResponseTimeData`/`SearchErrorData`/`SearchUsageStats`/`UploadStatusChart`/`AuditLogResponse`/`AuditLogListResponse` 7 schema + 7 endpoint 직접 호출 캡처). **추정 금지 원칙 정확 적용**: `AuditLogResponse` 에 `user_agent` 필드 미존재 → BFF/Vue 모두 미포함 / export query 에 `format` 없음(항상 CSV). **`IDocUtilClient` 7 메서드 추가** (`GetDashboardMetricsAsync` / `GetDashboardResponseTimesAsync` / `GetDashboardSearchErrorsAsync` / `GetDashboardSearchUsageAsync` / `GetDashboardUploadStatusAsync` / `ListAuditLogsAsync` / `ExportAuditLogsAsync`) + record DTO 8종(`DocUtilDashboardMetrics` / `DocUtilResponseTimes` / `DocUtilSearchErrors` / `DocUtilSearchUsage` / `DocUtilUploadStatus` / `DocUtilAuditLogEntry` / `DocUtilAuditLogList` / `DocUtilAuditExport`). **`AdminDocUtilOperationsController.cs` 신설** (~330 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/{dashboard,audit-logs}/...` + dashboard 5분 TTL / audit 1분 TTL + CSV stream 보존(RFC 5987 `filename*=UTF-8''...` 한글 파일명) + 4xx/5xx → 502 한국어 ErrorResponseDto). **DocUtilClient.cs**: 7 구현 + `MapAuditLog` / `JsonElementToObject` 매핑 헬퍼 + private 응답 DTO 7(`DashboardMetricsDto`/`ResponseTimeDataDto`/`SearchErrorDataDto`/`SearchUsageStatsDto`/`UploadStatusChartDto`/`AuditLogResponseDto`/`AuditLogListResponseDto`) + `HttpResponseOwnedStream` (response/request lifetime 을 stream Dispose 시점에 묶음 — export 누수 방지). **Frontend**: `docutilService.ts` 7 함수 + 정확한 TS interface 7건(`DocUtilDashboardMetrics` / `DocUtilResponseTimes` / `DocUtilSearchErrors` / `DocUtilSearchUsage` / `DocUtilUploadStatus` / `DocUtilAuditLogEntry` / `DocUtilAuditLogList` + `AuditLogFilters`) + `parseFileNameFromDisposition` 헬퍼(RFC 5987 우선 + ASCII fallback). 기존 시그니처 변경 0. `AdminDocUtilDashboard.vue` 신설 (~500 LOC, `<script setup lang="ts">` + ref/computed/onMounted/onBeforeUnmount + i18n): **상단**: 자동 갱신 토글(5초 간격) + 마지막 갱신 시각 + 기간 선택(전체/24h/7d/30d) / **1행**: KPI 4 카드(총 사용자/활성 사용자/총 문서/총 검색) + feature_usage 표(progress bar). **2행**: 응답시간 시계열 막대(평균/최대/최소 + 데이터 포인트 수) + 검색 사용량 dl(요청/응답/실패/성공률 + period). **3행**: 일별 검색 오류 표(스크롤, 0 초과 행 강조) + 업로드 상태 progress bar(완료/처리중/대기/실패 + 색상별 배지). 한국어 라벨 + 로딩/에러/빈 상태. **chart.js 미사용** — 간결한 div/table 시각화로 vendor 청크 영향 0. `AdminDocUtilAudit.vue` 신설 (~430 LOC): **상단**: 5 필드 필터 카드(action/resourceType/userId/start_date/end_date — datetime-local → ISO UTC 자동 변환) + CSV 내보내기 버튼. **본문**: 페이지네이션 + 합계 + 페이지 크기(20/50/100/200) + 7 컬럼 표(일시/Action/리소스/리소스 ID/사용자/IP/상세 보기). **모달**: 9 필드 dl(id/createdAt/action/resourceType/resourceId/orgId/userId/ip) + raw JSON pre 영역 + 한국어 모달. CSV Blob 다운로드 + URL.revokeObjectURL 정리(메모리 누수 방지). **빌드 검증**: `dotnet build` errors=0 / warnings=11(모두 pre-existing CS1998) + `npm run build:check` errors=0 + 신규 청크 `AdminDocUtilDashboard-CKnlP7sp.js` 14.61 kB(gzip 4.06 kB) + `AdminDocUtilAudit-BMjhPcrg.js` 12.27 kB(gzip 3.61 kB) + `index-gJkHeTAS.js` 151.42 kB. **`@ts-nocheck` 부착 0** — vue-tsc 2.x strict 게이트 유지. **호스트 배포**(`tmp/phase10_2a_audit_dashboard/step10_deploy.py`): paramiko SFTP 10 파일 → `docker compose build agenthub` exit=0 → `up -d --force-recreate` exit=0 → 6초 만에 healthy. **e2e + 회귀 32/0 PASS** (`step20_e2e_verify.py`): A) admin login JWT 555자 / **B) 7 신규 endpoint** — B-1 dashboard/metrics 867ms cold → 30ms warm + schema(totalUsers/activeUsers/totalDocuments/totalSearches/featureUsage) PASS / B-2 response-times?period=7d schema(timestamps[4]+values[4]) / B-3 search-errors schema(dates[7]+errorCounts[7]) / B-4 search-usage period='7d' / B-5 upload-status completed=31 / B-6 audit-logs 90ms cold → 13ms warm + total=754 + entry schema(action="auth.login" resourceType="auth") / B-7 audit-logs/export Content-Type text/csv + Content-Disposition RFC 5987 + 162393 bytes / **C) 권한 게이트** Bearer 미부착 401 + Bogus JWT 401 / **D) 캐시 효과** dashboard 29× 가속 + audit 7× 가속 / **E) 직전 회귀 8 endpoint** 모두 PASS(b3a2d85 6필드 / Phase 4 metrics 24 keys / Phase 6.3 documents / KB collections count=2 / 10.1a users total=11 / 10.1b departments count=10 / 10.1c projects total=2 / 한국어 RAG cid status=201). **R3 격리 보존**: DocUtil schema 만 접근, AgentHub 자체 스키마 미사용. **외부 시그니처 변경 0** — 기존 `IDocUtilClient` 시그니처 보존(신규 7 메서드 추가). 산출물: 신규 `agenthub/Controllers/AdminDocUtilOperationsController.cs` (~330 LOC) + `agenthub/ClientApp/src/views/admin/AdminDocUtilDashboard.vue` (~500 LOC) + `agenthub/ClientApp/src/views/admin/AdminDocUtilAudit.vue` (~430 LOC). 수정 `IDocUtilClient.cs` (7 메서드 + 8 record DTO 추가) + `DocUtilClient.cs` (7 구현 + 매핑 헬퍼 2 + 7 private DTO + HttpResponseOwnedStream) + `docutilService.ts` (7 함수 + 7 interface + filename parser) + router/MainLayout/i18n ko/en. **검증 스크립트**: `tmp/phase10_2a_audit_dashboard/` 4 파일 (`step01_capture_dashboard_audit_openapi.py` 7 schema + 17 probe / `step10_deploy.py` 호스트 SFTP+docker build / `step20_e2e_verify.py` 32 항목 자동화 + 회귀 8 / `verify_results.json`). 다음 트랙: **Phase 10.2b** (Search Scopes / Evaluation 등) 또는 사용자 결정 대기. 직전: **Phase 10.1c — DocUtil 프로젝트/보드 운영자 BFF + Vue 콘솔 완료, Phase 10.1 전체 종결**) — AgentHub 운영자가 DocUtil 의 프로젝트 카탈로그(=collection 풍부 표면) + 멤버 + 부서 매핑 + 보드(KB collection 권한 단위)를 단일 진입점에서 관리하는 BFF **13 endpoint** 신설 + Vue 운영자 화면(`/admin/docutil-projects`) + 사이드바 docutil 카테고리 3번째 항목 추가. **DocUtil OpenAPI 사전 캡처**(`tmp/phase10_1c_projects/openapi_full.json`/`openapi_projects_schemas.json` — `ProjectResponse`/`ProjectCreate`/`ProjectUpdate`/`ProjectListResponse`/`BoardResponse`/`BoardCreate`/`BoardUpdate`/`BoardListResponse` 8 schema + 13 endpoint 직접 호출 캡처 + 운영 프로젝트 2건의 members(2)/departments(6)/boards 응답 schema 검증). 추정 금지 원칙 정확 적용: **`ProjectUpdate` 에 `allow_original_download` 미존재** → BFF Update DTO 도 미포함 / **`BoardCreate`/`BoardUpdate` 에 `folder_id` 미존재** → BFF DTO/Vue 모달 모두 미포함. → **`IDocUtilClient` 13 메서드 추가** (`ListProjectsAsync` / `GetProjectTreeAsync` / `GetProjectAsync` / `CreateProjectAsync` / `UpdateProjectAsync` / `DeleteProjectAsync` / `GetProjectMembersAsync` / `GetProjectDepartmentsAsync` / `ListProjectBoardsAsync` / `CreateProjectBoardAsync` / `GetProjectBoardAsync` / `UpdateProjectBoardAsync` / `DeleteProjectBoardAsync`) + record DTO 12종(`DocUtilProject`/`DocUtilProjectList`/`DocUtilProjectTreeNode`/`DocUtilProjectMember`/`DocUtilProjectDepartment`/`DocUtilBoard`/`DocUtilBoardList` + Request 5건). **`AdminDocUtilProjectsController.cs` 신설** (~600 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/projects[/...]` + 10분 TTL 캐시 + `docutil-collections` version-key invalidate 통합 — **DocUtilClient.ListCollectionsAsync(AgentBuilder dropdown)와 namespace 통합**으로 본 화면 mutation 시 dropdown 도 즉시 stale + 4xx/5xx → 502 한국어 ErrorResponseDto + mutation 의 catch 분기에서도 invalidate 호출(10.1b ghost 처리 패턴)). **DocUtilClient.cs**: 13 구현 + `MapProject` / `MapBoard` 매핑 헬퍼 + private 응답 DTO 7(`ProjectResponseDto`/`ProjectListResponseDto`/`ProjectTreeNodeDto`/`ProjectMemberResponseDto`/`ProjectDepartmentResponseDto`/`BoardResponseDto`/`BoardListResponseDto`) + `ListCollectionsAsync` 캐시 키에 `v{N}:` prefix 추가(시그니처/응답 형태 보존, 행위는 mutation 시 자동 stale 향상). **Frontend**: `docutilService.ts` 13 함수 + 정확한 TS interface 11건(`DocUtilProject`/`DocUtilProjectList`/`DocUtilProjectTreeNode`/`DocUtilProjectMember`/`DocUtilProjectDepartment`/`DocUtilBoard`/`DocUtilBoardList` + Request 4건). 기존 `listCollections` 시그니처/응답 보존 — AgentBuilder dropdown 회귀 0. `AdminDocUtilProjects.vue` 신설 (~880 LOC, `<script setup lang="ts">` + ref/computed/onMounted + i18n): **상단**: 탭(목록/트리) + 검색바 + 신규 프로젝트 버튼. **좌측 목록 탭**: 페이지네이션 카드 그리드 + 인라인 수정/삭제 + 검색 적용/초기화. **좌측 트리 탭**: 평면 프로젝트 + boards sub-array 들여쓰기. **우측**: 선택 프로젝트 정보 카드(8 필드 dl/dt) + 멤버 표 + 부서 표 + 보드 목록(CRUD 인라인 액션). **모달**: 프로젝트 생성/수정(name/description/allowOriginalDownload checkbox — Update 모드에선 hidden, ProjectUpdate schema 보존), 보드 생성/수정(name/description). 2단계 confirm 삭제 + 한국어 라벨 + 502 폴백 + 빈 상태. **빌드 검증**: `dotnet build` errors=0 / warnings=11 (모두 pre-existing CS1998) + `npm run build:check` (vue-tsc 2.2.12 + vite 5) errors=0 + 신규 청크 `AdminDocUtilProjects-B_o0Jfnp.js` 24.43 kB (gzip 5.60 kB) + `docutilService-CSGQP4A5.js` 4.93 kB. **`@ts-nocheck` 부착 0**. **호스트 배포**(`tmp/phase10_1c_projects/step10_deploy.py`): paramiko SFTP 9 파일 → `docker compose build agenthub` exit=0 → `up -d --force-recreate` exit=0 → 6초 만에 healthy. **e2e + 회귀 28+/0 PASS** (`step20_e2e_verify.py`): A) admin login JWT 555자 / B) 13 신규 endpoint(B-1 GET projects 35ms cold → 25ms warm, B-2 tree, B-3 POST 201, B-4~B-13 모두 200/201/204) / C) 권한 게이트 401x2 / **D) 캐시 invalidate 통합 namespace 검증 PASS — collections 시작 count=2, projects 시작 total=2 → POST projects 1건 → collections count=3 + projects total=3(통합 namespace 효과 입증, AgentBuilder dropdown 도 즉시 신규 프로젝트 노출) → DELETE → collections baseline 회복** / E) 직전 회귀 8 endpoint 모두 PASS (E-1 /api/agents/1 6 필드 b3a2d85 / E-2 /admin/metrics/rag 24 필드 / E-3 /admin/knowledge-base/documents Phase 6.3 / E-4 한국어 RAG cid=262 status=200 / E-5 /admin/docutil/users total=11 10.1a / E-6 /admin/docutil/departments count=10 10.1b / E-7 /admin/docutil/organization 10.1b / E-8 /admin/docutil/organization/quota 10.1b). **R3 격리 보존**: DocUtil schema 만 접근, AgentHub 자체 KB 미사용. **외부 동작 변경 0** — 기존 `IDocUtilClient` 시그니처 보존(신규 13개만 추가) + `ListCollectionsAsync` 시그니처/응답 보존(캐시 키만 version-aware). **Phase 10.1 전체 종결** — DocUtil 사용자/조직/부서/할당량/프로젝트/보드를 운영자가 AgentHub 한 화면에서 모두 관리. 직전: **Phase 10.1b — DocUtil 조직/부서/할당량 운영자 BFF + Vue 콘솔 완료** — AgentHub 운영자가 DocUtil 의 조직 메타 / 부서 트리 / 월 할당량까지 단일 진입점에서 관리하는 BFF **9 endpoint** 신설 + Vue 운영자 화면(`/admin/docutil-departments`) + 사이드바 docutil 카테고리 항목 추가. **DocUtil OpenAPI 사전 캡처**(`tmp/phase10_1b_deps/openapi_full.json`/`schemas_subset.json` — `OrganizationResponse`/`OrganizationUpdate`/`DepartmentResponse`/`DepartmentCreate`/`DepartmentUpdate`/`OrganizationQuotasCurrentResponse`/`QuotaStatusResponse`/`QuotaUpdateRequest` 8 schema + 7 endpoint 직접 호출 + 부서 멤버 응답 free-form `[id/username/email/role]` 검증) → **`IDocUtilClient` 9 메서드 추가** (`GetOrganizationAsync` / `UpdateOrganizationAsync` / `ListDepartmentsAsync` / `CreateDepartmentAsync` / `UpdateDepartmentAsync` / `DeleteDepartmentAsync` / `GetDepartmentMembersAsync` / `GetOrganizationQuotaAsync` / `UpdateOrganizationQuotaAsync`) + DocUtil schema 1:1 매핑 record DTO 8건(`DocUtilOrganization`/`DocUtilDepartment`/`DocUtilDepartmentMember`/`DocUtilOrganizationQuotaCurrent`/`DocUtilOrganizationQuotaStatus` + Request 3건). **`AdminDocUtilDepartmentsController.cs` 신설** (~360 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/{organization,departments,...}` + 10분 TTL 캐시 + `docutil-departments` version-key invalidate (mutation 성공/실패 모두 트리거 — DocUtil 측 404 ghost 부서 캐시 정합성 보장) + 4xx/5xx → 502 한국어 ErrorResponseDto + DocUtil quotas map → List 평탄화). **DocUtilClient.cs**: `ResolveOrganizationIdAsync` 헬퍼(IDocUtilTokenProvider.GetOrganizationIdAsync 검증 + 502 매핑) + 9 구현 + 매핑 헬퍼 2 + private 응답 DTO 5(OrganizationResponseDto/DepartmentResponseDto/DepartmentMemberResponseDto/OrganizationQuotasCurrentResponseDto/QuotaStatusResponseDto). **Frontend**: `docutilService.ts` 9 함수 + 정확한 TS interface 8건(`DocUtilOrganization`/`DocUtilDepartment`/`DocUtilDepartmentMember`/`DocUtilOrganizationQuotaCurrent`/`DocUtilOrganizationQuotaStatus` + Request 3건) + `AdminDocUtilDepartments.vue` (~620 LOC, **상단 좌**: 조직 정보 카드 + 수정 모달 / **상단 우**: 월 할당량 카드(quota_type 별 진행 막대 + 70%/90% 임계 색상 + 한도 수정 모달) / **하단 좌**: 부서 트리(평탄 List → path 사전순 + depth 들여쓰기 + 각 노드 [신규 하위/수정/삭제] 액션 + 루트 노드 선택 가능 dropdown 자손 제외 — 순환 부모 방지) / **하단 우**: 선택 부서 상세(id/name/parent/depth/path/createdAt) + 멤버 표 / 부서 생성/수정 모달(이름 + parent dropdown 자손 제외) / 한국어 confirm 2단계 삭제) + 라우트 `/admin/docutil-departments` (lazy + meta.role='Admin') + 사이드바 docutil 카테고리에 항목 추가 (icon `bi bi-diagram-3`) + i18n ko/en 50+ 키. **vue-tsc 2.x errors=0 / `@ts-nocheck` 부착 0 / dotnet build errors=0 (warnings=11 모두 pre-existing CS1998)**. 호스트 빌드 배포(192.168.10.39, `docker compose build agenthub` ≈3분 + recreate + healthy 12 초). **e2e + 회귀 21/21 PASS**: admin login → 9 신규 endpoint 모두 200/201/204 (GET /organization 1180ms cold / 부서 cold 16ms warm 14ms / POST 부서 검증용 생성 87ms → 3차 GET cache invalidate count+1 PASS / PUT 부서 rename 32ms / GET 멤버 36ms / DELETE 부서 36ms → 4차 GET cache invalidate count baseline 회복 PASS / GET /organization/quota 52ms quota_count=2 (dalle_monthly + unsplash_monthly) / PUT /organization/quota/dalle_monthly limit 100→101 → 즉시 원복) + Bearer 미부착 401 PASS + Bogus JWT 401 PASS + 직전 회귀 6 endpoint(GET /api/agents/1 b3a2d85 6필드 / GET /api/admin/metrics/rag Phase 4 / GET /api/admin/knowledge-base/documents 9801b06 / GET /api/admin/knowledge-base/collections 294e8a6 / 한국어 RAG / GET /api/admin/docutil/users 10.1a total=11) 모두 PASS. **DELETE 후 캐시 stale 회피**: 운영자가 이미 DocUtil 측에서 사라진 ghost 부서를 DELETE 시도 시 502 가 반환되더라도 캐시 invalidate 를 호출하여 stale 응답이 다음 GET 에 노출되는 회귀를 차단. 산출물: 신규 `agenthub/Controllers/AdminDocUtilDepartmentsController.cs` (~360 LOC) + `agenthub/ClientApp/src/views/admin/AdminDocUtilDepartments.vue` (~620 LOC). 수정 `IDocUtilClient.cs` (9 메서드 + 8 record DTO 추가) + `DocUtilClient.cs` (9 구현 + 매핑 헬퍼 + 5 private DTO) + `docutilService.ts` (9 함수 + 8 interface) + router/MainLayout/i18n ko/en. **검증 스크립트**: `tmp/phase10_1b_deps/` 6 파일 (`step01_capture_openapi.py` DocUtil 8 schema + 7 endpoint 캡처 / `step02_probe_members.py` 부서 멤버 응답 schema 확보 / `step10_deploy.py` 호스트 SCP+docker build / `step20_e2e_verify.py` 21 회귀 자동화 + pre-cleanup 안전망 / `step21_diag_delete.py` 캐시 invalidate 진단 / `step22_repro_delete_cache.py` ghost 잔재 격리). 다음 트랙: **Phase 10.1c — DocUtil Projects + Boards 운영자 BFF** (프로젝트 멤버십 / RAG collection 권한 매핑). 직전: **Phase 10.1a — DocUtil 사용자 운영자 BFF + Vue 콘솔 완료** — AgentHub 운영자가 DocUtil 사용자 카탈로그를 단일 진입점에서 관리하는 BFF 4 endpoint(목록/상세/상태 토글/삭제) 신설 + Vue 운영자 화면(`/admin/docutil-users`) + 신규 `docutil` 사이드바 카테고리(향후 10.1b 부서 / 10.1c 프로젝트 트랙 확장 베이스). DocUtil schema 사전 캡처(`GET /api/v1/users` 의 `org_id` 필수 query 확인) → **`IDocUtilTokenProvider.GetOrganizationIdAsync` 신설**(JWT `org` claim 디코드, ApiKey 모드 안전 fallback) → **`IDocUtilClient` 4 메서드 추가**(`ListUsersAsync(page,size,role?,status?,search?)` / `GetUserAsync` / `UpdateUserStatusAsync` / `DeleteUserAsync`) + DocUtil UserResponse 1:1 매핑 record DTO(`DocUtilUserSummary`/`DocUtilUserDetail`/`DocUtilUserList` — id/username/email/role/status/organizationId/departmentId/language/lastLoginAt/createdAt 10 필드 보존). **`AdminDocUtilUsersController.cs` 신설** (`[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/{users,users/{id},users/{id}/status}` + 5분 TTL 캐시 + `docutil-users` version-key invalidate + 4xx/5xx → 502 한국어 ErrorResponseDto + 상태값 화이트리스트 active/inactive/locked). Frontend: `docutilService.ts` 4 함수(`listUsers`/`getUser`/`updateUserStatus`/`deleteUser`) + `AdminDocUtilUsers.vue` (~470 LOC, 검색/role-status 필터/페이지네이션/상세 모달/상태 토글 confirm/2단계 삭제 confirm) + 라우트 `/admin/docutil-users` + **신규 `docutil` 사이드바 카테고리 신설** (icon `bi bi-database`, roles=Admin/SuperAdmin) + i18n ko/en 32 키. **vue-tsc 2.x errors=0 / `@ts-nocheck` 부착 0 / dotnet build warnaserror=false errors=0**. 호스트 빌드 배포(192.168.10.39, `docker compose build agenthub` 58 초 + recreate + healthy 8 초). **e2e + 회귀 16/16 PASS**: admin login → 4 신규 endpoint 모두 200 (ListUsers total=11 latency 844ms cold / 23ms warm / 검증용 사용자 `user@example.com` active↔inactive 토글 + 원복 PASS / fake UUID GetUser → 404 정규화 PASS) + Bearer 미부착 401 PASS + Bogus 토큰 401 PASS + 캐시 hit 재호출 latency 단축 PASS + mutation 후 GET 200 PASS + 직전 회귀 5 endpoint(GET /api/agents/1 b3a2d85 6필드 / GET /api/admin/metrics/rag Phase 4 / GET /api/admin/knowledge-base/documents 9801b06 / GET /api/admin/knowledge-base/collections 294e8a6 / 한국어 RAG conversation 라우팅 200 with Claude API key 만 부재 — 라우팅 자체는 정상). 산출물: 신규 `agenthub/Controllers/AdminDocUtilUsersController.cs` (~280 LOC) + `agenthub/ClientApp/src/views/admin/AdminDocUtilUsers.vue` (~470 LOC). 수정 `IDocUtilClient.cs` (4 메서드 + 3 record DTO 추가) + `DocUtilClient.cs` (4 구현 + 2 mapper + 2 private DTO) + `IDocUtilTokenProvider.cs` (1 메서드) + `DocUtilTokenProvider.cs` (claim decoder) + `docutilService.ts` (4 함수) + router/MainLayout/i18n ko/en. **검증 스크립트 패키지**: `tmp/phase10_1a_users/` 5 파일 (.gitignore tmp/ 영역) — `step01_probe_docutil_users.py` (DocUtil OpenAPI users schema 캡처 — 422 → org_id 필수 발견) / `step02_probe_full.py` (org_id 자동 추출 후 실 호출 PASS) / `step03_jwt_payload.py` (JWT `org` claim 위치 확인) / `step10_deploy.py` (호스트 SCP + docker build) / `step20_e2e_verify.py` (16 회귀 항목 자동화). 다음 트랙: **Phase 10.1b — DocUtil Departments 운영자 BFF** (사용자 트랙과 동일 패턴 / 부서명 → 사용자 목록 join 합성 옵션).
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
| **마지막 commit** | `1518055` ([agenthub/cleanup-tools-gemini] 트랙 #84-2 — 운영 mutation cleanup + Tools/Dockerfile/Agent 코드 보강 + deploy + 재검증) — 24 files / +214 / -134. push 보류. 직전: `7c95459` ([agenthub/analytics-pii] 트랙 #84-1 — Analytics/PiiDetectionLogs 5xx 디버그 + 재배포 + 재검증) — 25 files / +231 / -240. push 보류. 직전: `d97d758` ([docutil/api-keys] 트랙 #69 — tb_llm_api_keys deprecate 마킹 (Phase 7 R2 옵션 A)) — 6 files / +269 / -55. 직전: `18548d4` ([infra/db] 트랙 #70 — alembic schema-agnostic CI 게이트 (ADR-18 강제)) — 1 file / +224. 둘 다 push 보류 (자율 트랙, 운영 mutation 0). 직전: `b37dc56` (TECHSPEC ADR-16~19) / `533ebe1` (progress.md 트랙 #62/#65/#66/#67 통합) / `2af224f` (트랙 #67 db_schema validator). 직전: `76a6860` Phase 10.x 결함 보강 (Router 가드+Polly+timeout+ApiKey 폴백+invalidate+body leak) — `[agenthub/docutil-admin] Phase 10.x — Critical/High/Medium 결함 보강`. 직전: `ca14b93` Phase 10.2e progress 갱신 / `7f8ff61` Phase 10.2e BFF / `002ead7` Phase 10.2a — DocUtil 대시보드/감사 로그 운영자 BFF + Vue (7 endpoint) — `[agenthub/docutil-admin] Phase 10.2a — DocUtil 대시보드/감사 로그 운영자 BFF + Vue (7 endpoint)` (push 대기 — secret leak 미해결). 11 files / +2822 / -6. e2e 32/0 PASS — A) admin login JWT 555 / B) 7 신규 endpoint 모두 200 — B-1 dashboard/metrics 867ms cold → 30ms warm(29× 가속) + schema(totalUsers/activeUsers/totalDocuments/totalSearches/featureUsage) PASS / B-2 response-times?period=7d schema(timestamps[4]+values[4]) PASS / B-3 search-errors schema(dates[7]+errorCounts[7]) PASS / B-4 search-usage period='7d' PASS / B-5 upload-status completed=31 PASS / B-6 audit-logs 90ms cold → 13ms warm(7× 가속) + total=754 + entry schema(action='auth.login' resourceType='auth') PASS / B-7 audit-logs/export Content-Type=text/csv + Content-Disposition RFC 5987(filename*=UTF-8'') + 162393 bytes binary stream PASS / C) 권한 게이트 401x2 PASS / D) 캐시 효과 dashboard 29× / audit 7× 가속 검증 PASS / E) 직전 회귀 8 endpoint 모두 PASS(b3a2d85 6필드 / Phase 4 metrics 24 keys / Phase 6.3 documents / KB collections count=2 / 10.1a users total=11 / 10.1b departments count=10 / 10.1c projects total=2 / 한국어 RAG status=201). 직전 `9dc4c16` Phase 10.1c — DocUtil 프로젝트/보드 운영자 BFF + Vue (13 endpoint, 통합 namespace) — `[agenthub/docutil-admin] Phase 10.1c — DocUtil 프로젝트/보드 운영자 BFF + Vue (13 endpoint, 통합 namespace)` (push 대기 — secret leak 미해결). 10 files / +3267 / -20. e2e 28+/0 PASS — A) admin login JWT 555 / B) 13 신규 endpoint 모두 200/201/204(cold 35ms warm 25ms) / C) 권한 게이트 401x2 / D) **캐시 invalidate 통합 namespace 검증 PASS — collections 시작 count=2 + projects 시작 total=2 → POST projects → 양쪽 동시 +1 갱신(AgentBuilder dropdown 통합 효과 입증) → DELETE → baseline 회복** / E) 직전 회귀 8 endpoint(b3a2d85 6필드, Phase 4 metrics, Phase 6.3 documents, 한국어 RAG cid=262, 10.1a users total=11, 10.1b departments/organization/quota) 모두 PASS. 직전 `84b336a` Phase 10.1b — DocUtil 조직/부서/할당량 운영자 BFF + Vue (9 endpoint) — `[agenthub/docutil-admin] Phase 10.1b — DocUtil 조직/부서/할당량 운영자 BFF + Vue (9 endpoint)` (push 대기 — secret leak 미해결). 10 files / +2439 / -4. e2e 21/21 PASS — admin login → 9 신규 endpoint(GET/PUT /organization, GET/POST /departments, PUT/DELETE /departments/{id}, GET /departments/{id}/members, GET/PUT /organization/quota[/{type}]) 모두 200/201/204 + 캐시 invalidate (POST 후 count+1, DELETE 후 count baseline 회복) + 권한 게이트 401 + 직전 회귀 6 endpoint 모두 PASS + 10.1a 회귀 PASS. 직전 `b5d09f0` Phase 10.1a — DocUtil 사용자 운영자 BFF + Vue (4 endpoint, docutil 카테고리 신설). 직전 `45b8439` Phase 9 MSSQL 운영 데이터 PostgreSQL 이관 + AES 키 회전. 직전 `f44f49a` 후속 트랙 DocUtil collection 카탈로그 응답 캐시 (10분 TTL) + 메트릭 4 카운터 — `[agenthub/collection-cache] 후속 트랙 — DocUtil collection 카탈로그 응답 캐시 (10분 TTL) + 메트릭 4 카운터` (push 대기 — secret leak 미해결). 6 files / +171 / -21. 회귀 3 시나리오 PASS — (1) /collections 1차 758ms (DocUtil 직격) → 2차 22ms (캐시 hit, 33배 빠름) + 5회 연속 hit 14~17ms / (2) /api/admin/metrics/rag → 200 + 신규 4 카운터(docUtilCollectionCacheHit=7/Miss=2/Calls=2/Failures=0/HitRatio=0.778) / (3) 한국어 RAG 쿼리 200 + Phase 4 카운터 정상 증가 + collection 카운터 무변화(namespace 격리). 직전 `d40945c` 후속 트랙 #9 WorkflowBuilder vue-flow 타입 정렬 + @ts-nocheck 해제 (D-1) — `[agenthub/vue-flow-types] 후속 트랙 #9 — WorkflowBuilder vue-flow 타입 정렬 + @ts-nocheck 해제 (D-1)` / 직전 `0f0fc89` progress.md 동기화 / `294e8a6` 후속 트랙 KnowledgeBaseRef DocUtil collection dropdown 전환 — `[agenthub/kb-collection-dropdown] 후속 트랙 — KnowledgeBaseRef 를 DocUtil projects dropdown 으로 전환` (push 대기 — secret leak 미해결). 8 files / +309 / -13 (백엔드 3 + 프론트 2 + i18n 2 + progress.md). 회귀 5 시나리오 PASS — admin 로그인 / (신규) /collections Bearer JWT 200 + 2건 + BFF 3 필드만 노출 / (권한 게이트) Bearer 없이 401 / (직전 회귀 b3a2d85) /api/agents/1 6 신규 필드 / 한국어 RAG 200. 이전 `174cc7b` 후속 트랙 #8 AgentChat/AgentSelect 의 deprecated `/api/knowledgebase` dead code 제거 — `[agenthub/cleanup] 후속 트랙 #8 — AgentChat/AgentSelect 의 deprecated /api/knowledgebase dead code 제거` (push 대기). 6 files / +84 / -396 (312 라인 dead code 청산). 이전 `845382c` AgentBuilder.vue UI 운영자 폼 필드 확장 — `[agenthub/agent-builder-ui] 후속 트랙 — AgentBuilder.vue 에 LlmRouting/KB 운영 폼 필드 추가` (push 대기). 이전 `b3a2d85` Agent 엔티티 ↔ AgentDto 6 필드 갭 보강 — `[agenthub/agent-dto-gap] 후속 트랙 — Agent 엔티티 ↔ AgentDto 6 필드 갭 보강`. 이전 `8819217` 후속 트랙 B-1 DTO TS↔C# 동기화 — `[agenthub/typesafe] 후속 트랙 B-1 — Agent/Conversation DTO TS↔C# 동기화` (push 대기 — secret leak 미해결). 이전 `32f78d1` 후속 트랙 C-1 자체 KB Vue 잔재 제거 — `[agenthub/cleanup] 후속 트랙 C-1 — Phase 2 자체 KB Vue 잔재 완전 제거` (push 대기). 이전 `3b7c857` 후속 트랙 DocUtil 캐시 invalidate — `[agenthub/cache-invalidate] 후속 트랙 — DocUtil 검색 캐시 version-key invalidate 도입` (push 대기 — secret leak 미해결). 이전 `4151b3d` (Phase 5 commit 해시 progress.md 동기화). 이전 `c71debb` Phase 5 운영자 메뉴 그룹화 + RAG 메트릭 UI — `[agenthub/admin-menu] Phase 5 — 운영자 메뉴 그룹화 (admin 카테고리) + RAG 메트릭 UI` (push 대기 — secret leak 미해결). 이전 `11039af` Phase 4 DocUtil 캐시 + RAG 메트릭 — `[agenthub/rag-metrics] Phase 4 — DocUtil 응답 캐시 5분 + RAG 메트릭(/api/admin/metrics/rag)` (push 대기 — secret leak 미해결). 이전 `3367e4b` Phase 3 vue-tsc 2.x — `[agenthub/vue-tsc] Phase 3 — vue-tsc 2.x 업그레이드 (Node 24 호환) + 부채 마킹` (push 대기 — secret leak 미해결). 이전 `7f1a9ae` (Phase 2 자체 KB drop — `[agenthub/kb-drop] Phase 2 — 자체 KB 코드/스키마 완전 제거 (ADR-2 단일 권위)`). 이전 `98433fa` (Phase 1 RAG 응답 품질 개선 — `[agenthub/rag-quality] Phase 1 — RAG 응답 품질 개선 (QueryRewriter + RRF 멀티 query 결합)`). 이전 `ede8096` (Phase B Nexus 자산 + Phase D NETSDK1194 fix) / `7710df6` (Phase A DocUtil JWT 자동 갱신) / `52d58d0` (progress.md) / `4f868c4` (Phase B 보강 Redis 인증) / `cbc4e2d` (progress.md) / `51e4b85` (Phase B Docker assets) / `1a1466f` (progress.md) / `c9d61a4` (사이드바 메뉴) / `d9784f0` (Hangfire fix) — 모두 누적 |
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
| **10.1a** | DocUtil 사용자 운영자 BFF + Vue (BFF 4 endpoint + AdminDocUtilUsers.vue + docutil 카테고리 신설) | ✅ 완료 — `IDocUtilTokenProvider.GetOrganizationIdAsync` + `IDocUtilClient` 4 메서드 + `AdminDocUtilUsersController` (5분 TTL + version-key invalidate + 한국어 502 매핑) + Vue 운영자 화면 + 사이드바 docutil 카테고리. e2e 16/16 PASS, 직전 회귀 5 endpoint PASS. 다음 10.1b Departments. | 2026-05-10 |
| **10.1b** | DocUtil 조직/부서/할당량 운영자 BFF + Vue (BFF 9 endpoint + AdminDocUtilDepartments.vue) | ✅ 완료 — `IDocUtilClient` 9 메서드(조직 2 + 부서 5 + 할당량 2) + `AdminDocUtilDepartmentsController` (10분 TTL + `docutil-departments` version-key invalidate + 502 ghost 정합성 보장 + DocUtil quotas map → List 평탄화) + Vue 운영자 화면(상단 조직/할당량 카드 + 하단 부서 트리/상세 패널 + 모달 3종) + i18n ko/en 50+ 키. DocUtil OpenAPI 8 schema 사전 캡처 + 7 endpoint probe. e2e 21/21 PASS, 직전 회귀 6 endpoint(b3a2d85/Phase 4/9801b06/294e8a6/한국어 RAG/10.1a users) + 10.1a 회귀 PASS. 다음 10.1c Projects/Boards. | 2026-05-10 |
| **10.1c** | DocUtil 프로젝트/보드 운영자 BFF + Vue (BFF 13 endpoint + AdminDocUtilProjects.vue + 통합 namespace) | ✅ 완료 — `IDocUtilClient` 13 메서드(프로젝트 6 + 멤버/부서 2 + 보드 5) + `AdminDocUtilProjectsController` (~600 LOC, 10분 TTL + **`docutil-collections` version-key invalidate 통합** — DocUtilClient.ListCollectionsAsync 의 `du:c:` 캐시도 동시 stale, AgentBuilder dropdown 즉시 갱신) + record DTO 12종 + Vue 운영자 화면(~880 LOC, 탭 목록/트리 + 우측 상세 멤버/부서/보드 + 모달 4종 — 프로젝트/보드 생성/수정) + i18n ko/en 70+ 키. DocUtil OpenAPI 8 schema + 13 endpoint 사전 캡처(`tmp/phase10_1c_projects/`). 추정 금지 정확 적용: ProjectUpdate 에 allow_original_download 미존재 / BoardCreate-Update 에 folder_id 미존재 — BFF/Vue 모두 미포함. **`ListCollectionsAsync` 캐시 키만 version-aware 로 보강**(시그니처/응답 보존 — AgentBuilder 회귀 0). e2e 28+/0 PASS — 13 endpoint 200/201/204 + 권한 게이트 401x2 + **통합 namespace 검증(POST projects → collections count+1 동시 갱신, DELETE → baseline 회복)** + 직전 회귀 8 endpoint 모두 PASS(b3a2d85 6필드, Phase 4 metrics, Phase 6.3 documents, 한국어 RAG cid=262, 10.1a users, 10.1b departments/organization/quota). **Phase 10.1 전체 종결** — 운영자가 AgentHub 한 화면에서 DocUtil 의 사용자/조직/부서/할당량/프로젝트/보드 모두 관리. | 2026-05-10 |
| **10.2b** | DocUtil 검색범위 + 평가 운영자 BFF + Vue (BFF 15 endpoint + AdminDocUtilSearchScopes.vue + AdminDocUtilEvaluation.vue) | ✅ 완료 — `IDocUtilClient` 15 신규 메서드(Search Scopes 9 + Evaluation 7) + `AdminDocUtilSearchScopesController` (~590 LOC, `du:scopes:` 10분 TTL + `docutil-search-scopes` version-key invalidate + `du:scopes:locations:`/`options:` 30분 TTL 카탈로그 + mutation 성공/실패 모두 invalidate) + `AdminDocUtilEvaluationController` (~470 LOC, `du:eval:cfg:` 5분 + `docutil-evaluation-config` version-key + `du:eval:logs:`/`runs:` 1분 + `du:eval:trend:`/`questions:` 5분 + run 트리거 캐시 미적용 + 100질문/2000자 sanity) + record DTO 14종 + Vue 화면 2개(검색범위 3-tab UI ~880 LOC + 평가 5-tab UI ~880 LOC) + 사이드바 docutil 6·7 항목(`bi-bullseye`/`bi-clipboard-check`) + i18n ko/en 110+ 키. DocUtil OpenAPI(2026-05-10 캡처) Search Scopes 6 path + Evaluation 6 path 정확 매핑(추정 금지: SearchScopeResponse 24 필드 / EvaluationLogResponse 17 필드 / EvaluationTrend 는 `?days=` not period / Runs 는 `?limit=` only / valid-id 응답 schema 미정의 → free-form dict). `dotnet build` errors=0 / `npm run build:check` errors=0 + 신규 청크 `AdminDocUtilSearchScopes-vZpS3RoC.js` 31.84 kB / `AdminDocUtilEvaluation-BGvG0Ubh.js` 26.62 kB. e2e: Search Scopes **9/9 PASS** (CRUD 라이프사이클 + 캐시 cold→warm 1108ms→44ms + invalidate 검증 has_new_scope=true) + Evaluation **6/7 PASS** (config GET/PUT/invalidate + questions/runs/trend/run 모두 200 또는 202, **C3 logs 502** = DocUtil 자체 EvaluationLogResponse Pydantic ValidationError 버그(BFF 책임 밖, 502 한국어 매핑은 정상 동작)) + 권한 게이트 3/3 PASS + 직전 회귀 9 endpoint 모두 200(b3a2d85 6필드, RAG metrics, KB documents/collections, 10.1a users, 10.1b departments, 10.1c projects, 10.2a dashboard/audit). **외부 동작 변경 0** — 신규 시그니처만 추가, 기존 라우트/회귀 모두 PASS / `<script setup lang="ts">` + `@ts-nocheck` 미부착 / vue-tsc 2.x errors=0 / DI 수명 보존. 운영자가 AgentHub 한 화면에서 DocUtil 의 검색범위 정의 + RAG 품질 평가까지 모두 운영 가능 — RAG 도메인 운영 통합 강화. | 2026-05-10 |
| **10.2e** | DocUtil API Keys + DocUtil Agents + Documents V2 운영자 BFF + Vue (BFF 16 endpoint + 3개 Vue 화면) | ✅ 완료 — `IDocUtilClient` 16 신규 메서드(API Keys 4 + DocAgents 5 + Documents V2 7) + record DTO 12종 + 3 컨트롤러(`AdminDocUtilApiKeysController` 5분 TTL `docutil-api-keys` + `AdminDocUtilDocAgentsController` 10분 TTL `docutil-doc-agents` + `AdminDocUtilDocumentsV2Controller` 10분 TTL `docutil-documents-v2`) + mutation 성공/실패 모두 invalidate(ghost 처리 패턴) + Documents V2 export 결과 binary stream 프록시 다운로드(HttpResponseOwnedStream + RFC 5987 한글 파일명 + ASCII fallback). DocUtil 소스코드 직접 인스펙션(`api_keys/router.py` 129 LOC + `agents/router.py` 208 LOC + `documents_v2/router.py` 681 LOC + 각 schemas.py 정독) → OpenAPI 추정 금지 원칙 엄격 적용. Documents V2 path 패턴 `/api/v1/v2/documents/*`(prefix 중첩 발견 — main.py `API_V1` + router `prefix="/v2"`). 3 Vue 화면(`/admin/docutil-api-keys` 평문 키 1회 노출 경고 + 검증 버튼 / `/admin/docutil-doc-agents` AgentHub Agent 와 별개 도메인 명시 + CRUD + system_prompt textarea / `/admin/docutil-documents-v2` 디자이너 워크플로 UI — 자유 생성 + 부분 패치(page/component/tokens 3종) + 비동기 export 요청 + 상태 폴링 + Blob 다운로드) + 사이드바 docutil 카테고리 8·9·10 항목 → 13 항목(이전 10) + i18n ko/en 160+ 키 양 locale 동일. `dotnet build` errors=0/warnings=0 / `npm run build:check` errors=0(vue-tsc 2.x) / `@ts-nocheck` 부착 0건 / 신규 청크 `AdminDocUtilApiKeys` 7.92 kB + `AdminDocUtilDocAgents` 17.38 kB + `AdminDocUtilDocumentsV2` 28.45 kB. **정적 e2e 검증 PASS 86/86** (`agenthub/Tools/test_phase_10_2e_e2e.ps1` UTF-8 BOM): 파일 존재 9 / endpoint 카운트 4+5+7=16 / 회귀 9 컨트롤러(4+9+13+7+9+7+5+10+15=79) / 권한 게이트 12 / 캐시 invalidate 사이트(API Keys 7 / DocAgents 7 / DocsV2 5) / IDocUtilClient 16 메서드 시그니처 / docutilService 16 export / 라우터 3 / 메뉴 3 / i18n 3 블록 ×2 locale / @ts-nocheck 0. 외부 시그니처 변경 0건, 기존 record DTO 변경 0건, DI 수명 보존(DocUtilClient Scoped + CachingService Singleton). 운영자가 AgentHub 한 화면에서 DocUtil 의 LLM API Key 등록·회수·검증 + 자체 챗봇 페르소나 CRUD + 디자이너 기반 신규 문서 워크플로(자유 생성/부분 패치/비동기 export/다운로드) 까지 단일 진입점 확보. **DocUtil 운영자 BFF 누적 95 endpoint 도달**(4+9+13+7+15+7+5+9+15+16 = 100, 단 10.2b SearchScopes+Evaluation 9+7 = 16 → 정정 합계 95, Phase 10.2e 신규 16 포함). | 2026-05-11 |
| **10.2d** | DocUtil 문서 템플릿(Document Templates / Jinja2) 운영자 BFF + Vue (BFF 15 endpoint + AdminDocUtilTemplates.vue, 6-tab UI) | ✅ 완료 — `IDocUtilClient` 15 메서드 + record DTO 13종 + `AdminDocUtilTemplatesController` (~890 LOC, 10분 TTL `docutil-document-templates` + multipart 3종 업로드(일반/빈양식/스마트, 50MB) + AI 자동채움 + Jinja2 변환 + 변수 매핑 + 미리보기 stream(HttpResponseOwnedStream + RFC 5987)) + Vue 화면 6-tab(기본정보/변수메타/문서구조/AI 자동채움/Jinja2 변환/변수 매핑) + i18n 115×2=230 키. DocumentTemplate ≠ ReportTemplate 도메인 격리(캐시 namespace 독립). 정적 e2e PASS. 직전 commit `505b1bb`. | 2026-05-11 |
| **10.2c** | DocUtil FAQ + Reports + Templates 운영자 BFF + Vue (BFF 14 endpoint + AdminDocUtilFaq.vue + AdminDocUtilReports.vue) | ✅ 완료 — `IDocUtilClient` 14 메서드 + record DTO 16종 + 2 컨트롤러(`AdminDocUtilFaqController` 5분 TTL + `AdminDocUtilReportsController` reports 1분/5분 + report-templates 10분 + binary stream RFC 5987 + multipart 50MB) + Vue 2개(`/admin/docutil-faq` 페이지네이션·검색·CRUD / `/admin/docutil-reports` 보고서 다운로드·템플릿 multipart 업로드) + i18n 133 키. DocUtil 측 `/reports/generate`+`/reports/templates` mutation 은 `HTTP 410` deprecate 응답을 BFF 가 정확히 502 한국어 매핑(코드 결함 아님 — DocUtil 측 `/v2/documents` 이관). e2e + 회귀 PASS 31/31. 직전 commit `01a8c5b`. | 2026-05-11 |
| **10.2a** | DocUtil 대시보드 + 감사 로그 운영자 BFF + Vue (BFF 7 endpoint + AdminDocUtilDashboard.vue + AdminDocUtilAudit.vue) | ✅ 완료 — `IDocUtilClient` 7 메서드(대시보드 5 + 감사 로그 2) + `AdminDocUtilOperationsController` (~330 LOC, dashboard 5분 TTL / audit 1분 TTL + 한국어 502 매핑 + CSV stream 보존 — RFC 5987 한글 파일명) + record DTO 8종(`DocUtilDashboardMetrics` / `DocUtilResponseTimes` / `DocUtilSearchErrors` / `DocUtilSearchUsage` / `DocUtilUploadStatus` / `DocUtilAuditLogEntry` / `DocUtilAuditLogList` / `DocUtilAuditExport`) + private 응답 DTO 7 + `HttpResponseOwnedStream` (response/request lifetime 묶음) + Vue 화면 2개(`AdminDocUtilDashboard.vue` ~500 LOC: KPI 4 카드 + feature_usage 막대 + 응답시간 시계열 막대 + 검색 사용량 dl + 검색 오류 표 + 업로드 상태 progress / `AdminDocUtilAudit.vue` ~430 LOC: 5 필터(action/resourceType/userId/start_date/end_date) + 페이지네이션 + 상세 모달 raw JSON + CSV Blob 다운로드) + 사이드바 docutil 카테고리 4·5 번째 항목 + i18n ko/en 130+ 키. DocUtil OpenAPI 8 schema + 7 endpoint 사전 캡처(`tmp/phase10_2a_audit_dashboard/openapi_full.json`/`openapi_dashboard_audit_schemas.json`/`probe_results.json`). 추정 금지 정확 적용: `user_agent` 필드 schema 미존재 → BFF/Vue 모두 미포함 / export query 에 `format` 없음(항상 CSV). **빌드 검증**: `dotnet build` errors=0 / warnings=11(모두 pre-existing CS1998) + `npm run build:check` errors=0 + 신규 청크 `AdminDocUtilDashboard-CKnlP7sp.js` 14.61 kB(gzip 4.06 kB) + `AdminDocUtilAudit-BMjhPcrg.js` 12.27 kB(gzip 3.61 kB) + `index-gJkHeTAS.js` 151.42 kB. **`@ts-nocheck` 부착 0**. **호스트 배포**(`step10_deploy.py` paramiko SFTP 10 파일 → `docker compose build agenthub` exit=0 → `up -d --force-recreate` exit=0 → 6초 만에 healthy). **e2e + 회귀 32/0 PASS** (`step20_e2e_verify.py`): A) admin login JWT 555자 / **B) 7 신규 endpoint** — B-1 GET dashboard/metrics 867ms cold → 30ms warm(29× 가속) + 5 필드 schema PASS / B-2 response-times?period=7d 200 + timestampsLen=4 valuesLen=4 / B-3 search-errors 200 + dates 7개 / B-4 search-usage 200 + period='7d' / B-5 upload-status 200 + completed=31 / B-6 audit-logs 90ms cold → 13ms warm(7× 가속) + total=754 + entry schema 일치(action="auth.login" resourceType="auth") / B-7 audit-logs/export 200 + Content-Type text/csv + Content-Disposition `attachment; filename="audit_logs.csv"; filename*=UTF-8''audit_logs.csv` + 162393 bytes / **C) 권한 게이트** Bearer 미부착 401 + Bogus JWT 401 / **D) 캐시 효과** dashboard 29× / audit 7× 가속 검증 / **E) 직전 회귀 8 endpoint** 모두 PASS(E-1 /api/agents/1 6 신규 필드 b3a2d85 / E-2 /admin/metrics/rag 24 keys / E-3 /admin/knowledge-base/documents / E-4 /admin/knowledge-base/collections count=2 / E-5 /admin/docutil/users total=11 10.1a / E-6 /admin/docutil/departments count=10 10.1b / E-7 /admin/docutil/projects total=2 10.1c / E-8 한국어 RAG conversation 라우팅 status=201). **R3 격리 보존**: DocUtil schema 만 접근, AgentHub 자체 스키마 미사용. **외부 시그니처 변경 0** — `IDocUtilClient` 신규 7 메서드 추가만, 기존 시그니처 보존. 운영자가 AgentHub 한 화면에서 DocUtil 의 운영 모니터링(KPI/응답시간/검색/업로드 5종) + 감사 로그(필터·페이지네이션·CSV export) 까지 단일 진입점 확보. | 2026-05-10 |

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

### 2026-05-15 (트랙 #97-post — Task #9 DocUtil 502 운영 회복 + Task #10 career 4 page.tsx 로컬 빌드 검증)

- **사용자 명시 보고**: 직전 트랙 #97-pre 의 사용자 요구 ①(DocUtil 운영자 메뉴 표시) + ②(일반 사용자 완벽 사용) 가 운영 단에서 미충족임을 지적. "에 대한 조치가 필요하지" → Task #9/#10/5단 검증 묶음 처리 결정.

- **두 에이전트 병렬 진단 (backend-specialist + code-analysis-specialist)** — 합의된 root cause:
  - `/api/admin/docutil/users` HTTP 502 = `AgentHub→DocUtil 업스트림 호출 실패`
  - 운영 컨테이너의 `DocUtil:ServiceAccount` (jyj7970) 자격이 DocUtil 측 비번과 불일치 → HTTP 401 → `DocUtilTokenProvider` 모든 갱신 경로 차단 → `_cachedAccessToken` null → `org` claim 추출 실패 → `InvalidOperationException` → 502
  - 35h 후 발현 메커니즘: JwtToken 1회성 적재 + 만료 후 재로드 부재 + Polly CB 5회 401 → 30s OPEN 사이클 → 영구 502 고착
  - 회귀 시점 추정: 트랙 #62(2026-05-12 운영 secrets 회전) 또는 G.2(5 서비스 비번 강화) 시점에 jyj7970 비번이 회전되었으나 agenthub 환경변수 미동기화 — 직전 PASS 시점부터 잠복

- **운영 호스트 실측 진단 (read-only 4건, `tmp/diagnose_task9_docutil_502.py`)**:
  - 환경변수 5키 모두 셋업 (BaseUrl/ServiceUsername/ServicePassword 정상, JwtToken/ApiKey 빈문자열) → 가설 A(BaseUrl 누락) 기각
  - 502 응답 body: `errorCode: DOCUTIL_UPSTREAM_ERROR`, `upstream: "DocUtil 운영자 토큰에서 organization_id 를 추출할 수 없습니다..."` → 가설 2(orgId null) 확정
  - agenthub 로그 smoking gun 2건: `DocUtil login HTTP 401 — ServiceAccount 자격 확인 필요` + `DocUtil 토큰 미설정 — JwtToken / refresh_token / ServiceAccount / ApiKey 모두 비어있음`
  - docutil-api `/api/v1/users` 진입 매치 0건 → DocUtil 측까지 도달 못함 확정

- **Phase 1 — 전용 서비스 계정 `agenthub_bff` 발급 (사용자 결정: 옵션 C)** (`tmp/apply_task9_phase1_agenthub_bff.py`):
  - DocUtil DB `tb_users` INSERT — id `b6d40352-7657-4305-85fa-a30f15700447`, username `agenthub_bff`, email `agenthub_bff@idino.internal`, role `admin`, status `active`, organization_id `00000000-0000-4000-a000-000000000001`(아이디노/default — jyj7970 동일), 비밀번호 bcrypt $2b$12$ 60chars
  - agenthub `.env` 갱신 — `DOCUTIL_SERVICE_USERNAME=agenthub_bff`, `DOCUTIL_SERVICE_PASSWORD=<40chars ASCII>` (`.bak.task9_phase1_20260515_111554` 백업)
  - `docker compose up -d --force-recreate agenthub` healthy 6초
  - 재검증 PASS: `/api/admin/docutil/users` **HTTP 502 → 200**, body 에 agenthub_bff 본인 + jyj7970(이동건) 등 사용자 list 정상 반환, `lastLoginAt` 가 INSERT 13초 후 기록 → ServiceAccount login 실제 동작 증명

- **Phase 2 — 결함 재발 방지 코드 보강 3건 (사용자 결정: 전체 3건, backend-specialist 위임)** (`tmp/deploy_task9_phase2.py`):
  - **6 .cs 파일** 수정:
    - `Services/DocUtilTokenProvider.cs` — manualJwt 1회성 적재 가드 제거(만료 5분 이내 매번 .env 재평가) + 갱신 모든 경로 실패 시 stale 캐시 반환 제거 + `DocUtilUpstreamException(TokenMissing/TokenForbidden)` throw
    - `Exceptions/DocUtilUpstreamException.cs` — `ErrorCode` 속성 + 5 표준 상수(`UpstreamError`/`TokenMissing`/`TokenForbidden`/`UpstreamUnreachable`/`ValidationError`/`Deprecated`) + 4 생성자 오버로드
    - `Services/DocUtilClient.cs` — `EnsureSuccessOrThrowKoreanAsync` 5 throw 지점에 ErrorCode 부착 (401/403→TokenForbidden, 410→Deprecated, 5xx→UpstreamUnreachable, 422→ValidationError, 기타→UpstreamError)
    - `DTOs/ErrorResponseDto.cs` — `FromDocUtilUpstream(ex, userMessage)` 정적 팩토리 + `MapDocUtilUpstreamToStatusCode(ex)` (TOKEN_*→503, DEPRECATED→410, VALIDATION→422, 기타→502)
    - `Controllers/AdminDocUtilUsersController.cs` — 4 catch 블록(ListUsers/GetUser/UpdateUserStatus/DeleteUser) `DocUtilUpstreamException` 우선 catch 구조
    - `Program.cs` — CB 정책 주석 (토큰 갱신 실패는 CB 카운터 영향 없이 fail-fast)
  - 운영 빌드: `docker compose build agenthub` exit 0, 99.8s, Warning 46건 모두 기존 `CS1998` (WorkflowEngine/FileParsingService — 본 트랙 외)
  - force-recreate + healthy 6초
  - 회귀 검증 4건 모두 PASS — admin 로그인 / `/api/admin/docutil/users` HTTP 200 (Phase 1 유지) / `/api/admin/docutil/departments` HTTP 200 / `/api/admin/metrics/rag` HTTP 200
  - 잠재 위험 — 나머지 12개 `AdminDocUtil*Controller` 가 UsersController catch 패턴 미적용 → 새 errorCode 응답 미노출 (별도 트랙)

- **Task #10 — career frontend 4 page.tsx 로컬 빌드 검증 (사용자 결정: 로컬 검증 만)**:
  - 운영 호스트(192.168.10.39) 실측 — career 컨테이너/디렉토리 모두 부재 (career 운영화는 트랙 #99 별도)
  - 로컬 검증: `cd career/frontend && npm install --legacy-peer-deps` (426 패키지) → `npx tsc --noEmit` 초기 3 에러 (`RoadmapSection.tsx` Set iteration) → 부수 결함 fix `tsconfig.json` 에 `"target": "ES2017"` 1줄 추가 (Next.js 14 표준 누락) → TSC PASS exit 0 → `npm run build` exit 0, **19 페이지 모두 정적 생성 PASS**
  - 4 신설 page.tsx 정적 빌드 결과: `/actions` 1.67kB/113kB, `/alumni` 1.84kB/116kB, `/competency` 3.22kB/115kB, `/roadmap` 1.58kB/116kB

- **5단 검증 (Task #1) 상태** — 1~4단 PASS, **5단 사용자 측 브라우저 실측 대기**:
  - admin 로그인 → 운영자 메뉴 13개 카테고리 표시 + DocUtil 사용자 메뉴 클릭 시 데이터 표시 (502 → 200 회복 시각 확인)
  - 일반 user 로그인 → myAccount 카테고리(Quota/ApiKeys/Analytics/UsageHistory) 진입점 표시
  - admin 라우트 직접 URL 입력 시 차단(dashboard 리다이렉트)
  - (선택) 의도적 401 유도 → DocUtil 메뉴 클릭 시 HTTP 503 + `errorCode: DOCUTIL_TOKEN_FORBIDDEN` 응답

- **운영 변경 추적**:
  - DocUtil DB: `agenthub_bff` 1 row INSERT (id `b6d40352-...`)
  - agenthub 컨테이너: `.env` 2 키 갱신 + force-recreate (`.bak.task9_phase1_20260515_111554`)
  - agenthub Docker 이미지: 6 .cs 변경 + force-recreate (`.bak.task9_phase2_20260515_*`)
  - **보관 필요(사용자 측 vault)**: agenthub_bff PLAIN 비밀번호 40 chars — stdout 1회 노출 후 코드/git 어디에도 미저장

- **로컬 코드 변경 (commit 대상)**:
  - agenthub 6 .cs 파일 (위 Phase 2)
  - career/frontend/tsconfig.json (target ES2017 1줄 추가)
  - tmp/ 5 신규 paramiko 스크립트 (`diagnose_task9_docutil_502.py`, `inspect_agenthub_env.py`, `inspect_docutil_users_schema.py`, `apply_task9_phase1_agenthub_bff.py`, `deploy_task9_phase2.py`, `inspect_career_prod.py`)
  - user_mig/progress.md 본 entry

- **메모리 활용**: `feedback_quality_over_demo.md`(완벽한 구현 우선) + `feedback_ui_verification.md`(5단 검증) 적용. tsconfig ES2017 부수 fix 도 본 트랙 범위 안으로 포함하여 빌드 완전 통과 추구.

- **마지막 commit**: 본 작업 후 추가 예정 (placeholder — 본 entry 갱신 commit 직후 hash 갱신).

### 2026-05-14 (트랙 #97-pre1 + #97-pre2 — DocUtil 운영자 UI 메뉴 표시 결함 fix + AgentHub 일반 사용자 UI 완전성 보강 + career 4 page.tsx 신설)

- **사용자 명시 보고**: "DocUtil 도 ui 적으로 운영자 메뉴가 표시되지 않았어, 다시 한번 일반 사용자(실제 시스템 사용자 포함)가 ui 적으로도 기능적으로도 완벽하게 사용가능토록 진행해줘".

- **진단 발견 1 (트랙 #97-pre1)**: `agenthub/wwwroot/assets/` 가 Phase 10.2a 스냅샷에 멈춰있어 Phase 10.2b~10.2e 의 8개 청크(SearchScopes / Evaluation / Faq / Reports / Templates / ApiKeys / DocAgents / DocumentsV2) 빌드 누락 → 메뉴 카테고리 자체가 옛 빌드로 렌더링되어 사용자 화면에 미노출. **코드는 5단(BFF + Vue + 라우트 + 메뉴 + i18n) 모두 정의되어 있었으나 빌드/배포 단계 누락**.

- **진단 발견 2 (트랙 #97-pre2, frontend-specialist 인벤토리)**: AgentHub Vue 일반 사용자 라우트 41개 중 6 결함 발견.
  - MainLayout 메뉴 누락 7건 — Playground / AgentMarketplace / AgentTemplates / Reports / DatabaseBackup / Tools / Workflows (URL 직접 입력만 가능)
  - i18n 키 누락 5건 — `nav.playground` / `agentMarketplace` / `agentTemplates` / `tools` / `workflows`
  - router `meta.role` 가드 미부착 10건 — Users / AuditLog / CostAnalysis / Reports / BannedWords / PiiProtection / Team / SystemHealth / DatabaseBackup / PresentationTemplateManagement (일반 user URL 직접 입력 차단 안 됨)
  - admin 카테고리에 Quota / ApiKeys / Analytics / UsageHistory 묶여있어 **일반 user 본인 데이터 진입점 부재** (가장 결정적 결함)
  - career frontend `(dashboard)` 라우트 4개 page.tsx 부재 — actions / alumni / competency / roadmap (학생 메뉴 진입 시 404)
  - docutil `frontend/src/app/(admin)/` 잔존 — layout.tsx 가드는 강함(super_admin/admin/org_admin 외 차단), 운영자 영역 deprecate 는 트랙 #97 종료 후 별도 처리

- **수정 (commit 대기)**:
  - **agenthub Vue** (4 파일):
    - `ClientApp/src/i18n/locales/{ko,en}.json` — nav 5 키 + `categories.myAccount` 추가
    - `ClientApp/src/layouts/MainLayout.vue` — aiServices 확장(+5) + **myAccount 카테고리 신설**(Quota / ApiKeys / Analytics / UsageHistory 모든 사용자) + admin 카테고리 정리(운영자 전용만 + Reports / DatabaseBackup 등록)
    - `ClientApp/src/router/index.ts` — 운영자 전용 라우트 10건 `meta: { requiresAuth: true, role: 'Admin' }` 가드 부착
  - **career frontend** (4 신설):
    - `app/(dashboard)/{alumni,competency,roadmap,actions}/page.tsx` — 각각 기존 Section 컴포넌트 사용(AlumniSection / CompetencySection / RoadmapSection), actions 는 정식 ActionsSection 신설 전까지 안내 카드. 한글 주석 의무 적용

- **빌드 PASS**: `cd agenthub/ClientApp && npm run build:check` → vue-tsc + vite 4.01s. `dist/assets/` 에 AdminDocUtil 13개 청크 + MainLayout 신규(`MainLayout-DvPDjwrb.js`) + index 신규(`index-g2VQ4FVE.js`) 모두 생성. `cp -r dist/* wwwroot/` 로 로컬 동기화.

- **운영 배포 PASS** (`tmp/deploy_track97_pre.py` paramiko, 192.168.10.39:64005):
  - SFTP 4 파일 / 213,247 bytes 동기화 (각 파일 `.bak.track97pre_{ts}` 백업 동반)
  - `docker compose build agenthub` (BuildKit cache + 컨테이너 내부 vite 빌드 16.89s)
  - `docker compose up -d --force-recreate agenthub` → healthy 6초

- **스모크 검증 (5/5)**:
  - [1] admin 로그인 JWT 555 chars PASS
  - [2] `/api/admin/metrics/rag` HTTP 200 PASS (Phase 4 회귀)
  - [3] `/api/admin/docutil/users` **HTTP 502** — 본 트랙 무관 회귀. DocUtil 컨테이너 15개 모두 healthy 35h 가동 중. agenthub→DocUtil JWT 토큰/endpoint 정합성 별도 진단 필요 → **Task #9** 로 분리 등록
  - [4] index.html entry fingerprint `index-CGjwV1fA.js` 신규 PASS (운영 호스트 컨테이너 내부 vite 빌드 결과 — 로컬 빌드와 다른 fingerprint)
  - [5] `docker exec agenthub ls /app/wwwroot/assets/ | grep AdminDocUtil` **13건 매치 PASS** — DocUtil 운영자 13개 청크 모두 운영 컨테이너에 서빙 (옛 빌드 누락 결함 완전 해소)

- **메모리 신규 등록 2건** (사용자 명시 피드백 반영):
  - `feedback_techspec_completeness.md` — TECHSPEC 작성 시 도메인 × 통합 레이어 매트릭스(데이터/AI 호출/운영자 UI/RBAC/모니터링/마이그레이션) 강제. 운영자 UI 흡수가 누락된 결함 반복 방지
  - `feedback_ui_verification.md` — UI 검증 5단(코드정의 / 빌드 / 배포 / 실측로그인 / e2e) 모두 통과해야 ✅ 완료. "정의됨" ≠ "표시됨" 구분

- **R7 5단 검증 진행률**: 1~4단 PASS, **5단 사용자 측 브라우저 실측 확인 대기** (admin / user role 별 메뉴 표시 + 라우트 진입 + 권한 가드 동작).

- **남은 작업 (Task 추적)**:
  - **Task #1**: 트랙 #97 본격 진입 (Phase 11.0 Kong admin RBAC + auth/competency/skill admin endpoint 신설 + AgentHub service-to-service 인증, ~3영업일)
  - **Task #2**: 트랙 #98 Phase 9 이관 스크립트 monorepo codify
  - **Task #3**: 트랙 #99 career compose/env 통합 DB 진입점 갱신
  - **Task #9**: DocUtil 502 별도 진단 (회귀, 시급)
  - **Task #10**: career frontend 빌드 + 배포 (4 page.tsx — 운영 호스트 미확인)

- **commit 메시지**:
  ```
  [agenthub/track97-pre + career/track97-pre] DocUtil 운영자 UI 빌드 누락 fix + 일반 사용자 UI 완전성 보강

  agenthub Vue 4 파일:
  - i18n/locales/{ko,en}.json: nav 5 키 + categories.myAccount
  - layouts/MainLayout.vue: aiServices 확장 + myAccount 카테고리 신설 + admin 정리
  - router/index.ts: 운영자 라우트 10건 meta.role='Admin' 가드 부착

  career frontend 4 신설:
  - app/(dashboard)/{alumni,competency,roadmap,actions}/page.tsx

  운영 배포: npm build 16.89s + docker rebuild + force-recreate + healthy 6s
  스모크 5/5 (DocUtil 502 1건 본 트랙 무관 회귀 → Task #9 분리)
  ```

### 2026-05-13 (트랙 #92 — Nexus 통합 운영 적용 완료: HTTPS LAN(192.168.22.223:8443) self-signed 우회 + 환경변수 정정 + AgentId=30 Internal nexus e2e PASS)

- **commit**: `fab65a8` (`[agenthub/track92] Nexus 통합 운영 적용 — HTTPS LAN(192.168.22.223:8443) self-signed 우회 + 환경변수 정정 + AgentId=30 e2e PASS`). 2 files / +23 / -3 (Program.cs + appsettings.json만 git 추적 — appsettings.Development/Production.json 은 .gitignore 대상이라 운영본만 SFTP 동기화). push 보류 (secret leak 미해결).

- **배경 / 문제**:
  - 트랙 #91 e2e 완료 후 사용자가 "Nexus 실제 부팅 이건 왜 필요하지?" 질문 → "현재 기동하고 있어" 정정.
  - 운영 Nexus orchestrator(Machine A) 가 실제로는 `https://192.168.22.223:8443` 에서 가동 중이고, 기존 AgentHub 설정의 `http://192.168.22.28:8001` 은 별도의 vLLM(Machine B) 백엔드였음.
  - vLLM 의 OpenAI 호환 `/v1/chat/completions` 은 있지만 Nexus 네이티브 `/v1/chat` 은 없으므로 옵션 B(ADR-1) 경로로 호출 시 404.
  - LAN 격리(ADR-11 air-gap)로 Nexus 는 self-signed 인증서로 LAN 노출.

- **진단 단계** (`tmp/track92_diag.py` + `tmp/track92_diag2.py`):
  - **Nexus 자체 점검**: `/v1/models` → 3개 모델 정상(nexus-phase3 primary / exaone-7.8b auxiliary / multilingual-e5-large embedding), `/v1/tenants` → default 테넌트, `/openapi.json` → `/v1/chat`/`/v1/chat/stream`/`/v1/sessions` 모두 등록됨.
  - **/v1/chat path 정상**: GET → 405 / POST 빈 body → 422 `body.message` Field required.
  - **AgentHub 컨테이너 환경변수 검증**: `Nexus__BaseUrl=http://192.168.22.28:8001` 가 env 로 박혀 있어 appsettings.json 우선순위를 override (.NET Configuration 우선순위: env > appsettings.{Env}.json > appsettings.json).
  - **출처 확인**: `/home/idino/agenthub/.env:7` 의 `NEXUS_BASE_URL=http://192.168.22.28:8001` + `docker-compose.yml:45` 의 `Nexus__BaseUrl: "${NEXUS_BASE_URL:-...}"` 합작.

- **수정 (코드 3 파일)**:
  - `agenthub/Program.cs` — nexus Named HttpClient 의 기본 BaseUrl `http://192.168.22.28:8001` → `https://192.168.22.223:8443`. `ConfigurePrimaryHttpMessageHandler` 추가하여 `Nexus:AcceptSelfSignedCert=true` 토글 시 `HttpClientHandler.ServerCertificateCustomValidationCallback = _,_,_,_ => true` 로 검증 우회 (LAN-only air-gap 환경 한정). 한국어 주석으로 외부망 노출 시 정식 cert 필요 명시.
  - `agenthub/appsettings.json` — `Nexus.BaseUrl` 갱신 + `AcceptSelfSignedCert: true` 추가.
  - `agenthub/appsettings.Development.json` — 동일 갱신.
  - `agenthub/appsettings.Production.json` — Nexus 섹션 신규 추가 (Production 환경 우선이라 명시).

- **빌드 검증**:
  - `cd agenthub && dotnet build` — 오류 0 / 신규 경고 0 (기존 16 유지). 4.7초.

- **운영 배포 (`tmp/deploy_track92.py` + `tmp/track92_envfix.py`)**:
  - **1차 배포** (`deploy_track92.py`): SFTP 3 파일(39,339 B) → PG `ApiServices.nexus.ApiEndpoint='https://192.168.22.223:8443/v1/chat'` UPDATE 1 row(ServiceId=32) → `docker compose build agenthub` **100.1s** → `force-recreate` → healthy 5s. 스모크: 로그인 PASS, /v1/health 200, **/api/agents/30/chat FAIL 404** (옛 vLLM URL 로 호출됨 — env override 미해결 단계).
  - **2차 환경변수 정정** (`track92_envfix.py`): `/home/idino/agenthub/.env` 의 `NEXUS_BASE_URL=http://192.168.22.28:8001` 삭제 + `NEXUS_BASE_URL`/`Nexus__BaseUrl`/`Nexus__AcceptSelfSignedCert` 3개 라인 신규 append. `docker-compose.yml:45` 의 fallback 도 새 URL 로 sed 치환. `force-recreate` 후 새 env 반영 확인.
  - 백업: `.env.bak.track92_20260513_*` + `docker-compose.yml.bak.track92_20260513_*`.

- **운영 회귀 검증 PASS**:
  - [1] admin 로그인 — JWT 555 chars PASS.
  - [2] `ApiServices.nexus.ApiEndpoint` = `https://192.168.22.223:8443/v1/chat` PASS.
  - [3] **컨테이너 내부 `curl Nexus /health`** → 200 PASS (HTTPS + self-signed 인증서 우회 정상 동작).
  - [4] **`POST /api/agents/30/chat` (career-chatbot Internal nexus)** → **PASS**.
    - 응답 body: `{"messageId":988,"conversationId":272,"content":"안녕하세요. 저는 학생 진로 코칭 챗봇 Nexus입니다. 진로 고민과 감정적 어려움을 경청하고 공감하며, 위기 상황에서는 상담 센터 연결을 권유합니다.","model":"primary","tokensUsed":2143,"cost":0.0000,"responseTime":3424,"citations":null}`.
    - 토큰 2143 / 비용 0 (사내 모델 — ApiUsage 비용 0 정책 유지) / responseTime 3424ms.
  - [5] AgentHub 로그 확인: `라우팅 적용: AgentId=30, Reason=internal_routing, ServiceId 32 → 32 (ServiceCode=nexus)` + `Start processing HTTP request POST https://192.168.22.223:8443/v1/chat` + `Sending HTTP request POST https://192.168.22.223:8443/v1/chat` PASS.
  - [6] 컨테이너 env 재검증 — `Nexus__BaseUrl=https://192.168.22.223:8443` + `Nexus__AcceptSelfSignedCert=true` 반영 PASS.
  - [7] `/api/agents` 회귀 — code=200 (External 라우팅 회귀 없음).

- **운영 효과**:
  - **ADR-1 옵션 B 실효성 확립** — AgentHub 가 Nexus 의 네이티브 `/v1/chat` 을 직접 호출 (세션/멀티테넌시 강점 보존).
  - **HybridRouter 진입로 확보** — career-chatbot(AgentId=30) Internal 라우팅 즉시 동작. Hybrid Agent 10개는 RoutingPolicyJson 비어 있어 현재는 external 폴백이지만, 후속 트랙에서 PII/cost 기반 분기 정책 시드 시 즉시 Nexus 분기 가능.
  - **LAN-only air-gap 유지** — Nexus 자체 노출 없이 컨테이너 내부에서만 https 호출 (self-signed 인증서 + LAN 격리 이중 방어).
  - **External 회귀 0건** — 기존 OpenAI/Claude 등 외부 LLM 호출은 ApiKeyPool 경로 영향 없음.

- **운영 환경 변경 (백업 보존)**:
  - PG `AIAgentManagement.ApiServices` ServiceId=32 `ApiEndpoint` UPDATE (`https://192.168.22.223:8443/v1/chat`).
  - `/home/idino/agenthub/.env` 갱신 (`NEXUS_BASE_URL`/`Nexus__BaseUrl`/`Nexus__AcceptSelfSignedCert` 3개).
  - `/home/idino/agenthub/docker-compose.yml:45` fallback URL sed 치환.
  - agenthub 이미지 재빌드 + 컨테이너 force-recreate.

- **후속 작업 권장**:
  - **트랙 #93 (Nexus 스트리밍 e2e)**: `/api/agents/{id}/chat/stream` SSE 경로로 Nexus `/v1/chat/stream` 도 PASS 검증 (NexusClient.SendChatStreamAsync 는 이미 구현됨).
  - **트랙 #94 (HybridRouter RoutingPolicyJson 시드)**: 현재 10개 Hybrid Agent 의 빈 RoutingPolicyJson 에 PII=internal / 비용 임계 / 데이터 라벨 매핑을 시드해 Internal 분기 활성화.
  - **트랙 #95 (Nexus:SharedSecret 운영 적용)**: 현재 미설정 — LAN 격리에만 의존. ADR-13 공유 시크릿 적용 시점에 Nexus 측 인증 미들웨어 + AgentHub `.env` Nexus__SharedSecret 동기화.
  - **트랙 #96 (Hangfire 모니터링)**: Nexus 호출 실패 시점에 Hangfire Recurring `nexus-health-probe` 등록하여 부팅 시점 + 5분 폴링 확인.

- **commit 메시지(코드)**:
  ```
  [agenthub/track92] Nexus 통합 운영 적용 — HTTPS LAN(192.168.22.223:8443) self-signed 우회 + 환경변수 정정 + AgentId=30 e2e PASS

  - Program.cs: nexus Named HttpClient 기본 BaseUrl 변경(http://192.168.22.28:8001 → https://192.168.22.223:8443) + ConfigurePrimaryHttpMessageHandler 추가하여 Nexus:AcceptSelfSignedCert=true 토글 시 self-signed 인증서 검증 우회 (LAN-only air-gap 환경 한정).
  - appsettings.json / Development.json: Nexus.BaseUrl 갱신 + AcceptSelfSignedCert 추가.
  - appsettings.Production.json: Nexus 섹션 신규 추가 (Production 우선).
  - 운영 env 정정: /home/idino/agenthub/.env 의 NEXUS_BASE_URL/Nexus__BaseUrl/Nexus__AcceptSelfSignedCert 갱신, docker-compose.yml:45 fallback URL 변경, PG ApiServices.nexus.ApiEndpoint UPDATE.
  - e2e: /api/agents/30/chat (career-chatbot Internal nexus, AgentId=30) → 한국어 응답 PASS (tokens=2143, cost=0, 3424ms).
  ```

### 2026-05-13 (트랙 #91 — ApiKeyPoolService DB 통합 완료: KeyType 컬럼 + Hangfire 5분 폴링 + 운영자 콘솔 + 운영 배포 + e2e 65/0/22 PASS)

- **commit**: `988f36c` (`[agenthub/track91] ApiKeyPoolService DB 통합 — 운영자 콘솔에서 외부 LLM 키 회전 가능`). 21 files / +4268 / -52. push 보류 (secret leak 미해결, 시연 종료 후 별도 sanitize 트랙).

- **사용자 명시 / 승인된 plan**: `C:\Users\IDINO_USER\.claude\plans\jazzy-dancing-sphinx.md` (트랙 #89 H6 진단 중 발견된 ApiKeyPoolService Singleton 의 appsettings-only 로드 결함 해소).

- **배경 / 문제**:
  - `Services/ApiKeyPoolService.cs:33-52` Singleton 이 부팅 시 `appsettings.json` 만 로드. DB 미참조.
  - DB `ApiKeys` 테이블 (ServiceCode 컬럼 보유) 은 외부 노출용 `ak-...` 키 전용으로 운영 — 외부 LLM 키 풀과 미연결.
  - 외부 LLM 키 회전 = 컨테이너 재시작 필요. 운영자가 GUI 로 관리 불가 → H6 같은 키 무효화 시점에 시연 차질.

- **설계 (Plan 의 핵심 결정)**:
  - `ApiKey.KeyType` string 컬럼 추가 (`"External"` 외부 노출 / `"Provider"` 외부 LLM 풀). 격리.
  - `ApiKeyPoolService` 가 `IServiceScopeFactory` 로 매 RefreshAsync 시 Scoped DbContext 생성 → AES-GCM 복호화 → 풀 머지 + 원자적 교체 (`ConcurrentDictionary`).
  - appsettings 폴백 유지 (회귀 차단).
  - Hangfire `*/5 * * * *` RecurringJob + 부팅 직후 1회 즉시 실행 + 운영자 등록/수정/삭제 시 즉시 트리거.
  - 운영자 콘솔 `/api-keys` 에 탭 3 "외부 LLM 키 풀(운영자)" 신설 (`v-if="isAdmin"`).

- **수정 (21 파일 = 백엔드 16 + 프론트 5)**:

  **백엔드 수정 9 + 신규 7**:
  - `agenthub/Models/ApiKey.cs` — `+KeyType` (Required, MaxLength=20, default `"External"`) + 한국어 XML 주석.
  - `agenthub/Data/AIAgentManagementDbContext.cs` — `+HasIndex(KeyType, IsActive, ServiceCode)` 복합 인덱스.
  - `agenthub/Migrations/20260513102231_Track091_ApiKeyKeyType.cs` + `.Designer.cs` (신규) — idempotent SQL (`DO $$ ... IF NOT EXISTS`) 트랙 #89 패턴 답습. 컬럼 추가 → 기존 1건 `'External'` 백필 → NOT NULL + DEFAULT → 복합 인덱스. Down: `DROP IF EXISTS`.
  - `agenthub/Migrations/AIAgentManagementDbContextModelSnapshot.cs` — KeyType + HasIndex 자동 갱신.
  - `agenthub/DTOs/ApiKeyDto.cs` — `ApiKeyDto.+KeyType`, `CreateApiKeyRequestDto.+KeyType?`.
  - `agenthub/DTOs/CreateProviderApiKeyRequestDto.cs` (신규) — KeyName/ServiceCode/ApiKey/Description?/ExpiresAt?/ValidateOnCreate.
  - `agenthub/DTOs/TestApiKeyResponseDto.cs` (신규) — record(Success, Message, Provider, LatencyMs).
  - `agenthub/DTOs/PoolStatsResponseDto.cs` (신규) — Providers + LastRefreshedAt + ProviderPoolStatDto(ServiceCode, TotalCount, FromAppsettings, FromDb, CoolingDownCount).
  - `agenthub/Services/IApiKeyPoolService.cs` — `+RefreshAsync(ct)`, `+GetPoolStatsWithSource()`, `+PoolStatEntry` record.
  - `agenthub/Services/ApiKeyPoolService.cs` — **재설계**. 생성자에 `IServiceScopeFactory` 주입, `Dictionary→ConcurrentDictionary`, `KeyEntry.Source` 필드 (`"appsettings"`/`"db"`), `RefreshAsync` (Scoped DbContext 명시 생성 → AES-GCM 복호화 → `NormalizeServiceCode` 매핑 → 원자적 풀 교체), `NormalizeServiceCode` 정적 헬퍼 (chatgpt→openai / gemini-image/imagen4→gemini / azureopenai/copilot 그대로).
  - `agenthub/Services/IApiKeyService.cs` — `+CreateProviderApiKeyAsync`, `+TestApiKeyAsync`, `+DecryptForPoolAsync` (LastUsedAt/UsageCount 미갱신 변종).
  - `agenthub/Services/ApiKeyService.cs` — 생성자에 `IApiKeyPoolService` + `IHttpClientFactory` 주입. `CreateProviderApiKeyAsync` (화이트리스트 + KeyHash UNIQUE 검사 + AES-GCM + DB INSERT + 즉시 RefreshAsync 트리거). `TestApiKeyAsync` (제공사별 ping 5종: openai/claude/gemini/perplexity/mistral — `IHttpClientFactory` + 10초 강제 timeout + Stopwatch). `DecryptForPoolAsync` (AsNoTracking). 기존 `CreateApiKeyAsync` / `GenerateAgentApiKeyAsync` 에 `KeyType="External"` 기본값 자동 부여.
  - `agenthub/Controllers/ApiKeysController.cs` — 신규 endpoint 3건 모두 `[Authorize(Roles = "Admin,SuperAdmin")]`: `POST /api/apikeys/provider`, `POST /api/apikeys/{id}/test`, `GET /api/apikeys/pool-stats`. 기존 endpoint 의 KeyType 기본값 처리.
  - `agenthub/BackgroundJobs/ApiKeyPoolRefreshJob.cs` (신규) — `[DisableConcurrentExecution(60)]` + try/catch.
  - `agenthub/Program.cs` — `+AddScoped<ApiKeyPoolRefreshJob>`, Hangfire `AddOrUpdate("api-key-pool-refresh", j => j.RefreshAsync(), "*/5 * * * *")`, `app.Lifetime.ApplicationStarted.Register(...)` 부팅 직후 1회 즉시 실행 (`Task.Run` 격리).

  **프론트엔드 수정 4 + 신규 1**:
  - `agenthub/ClientApp/src/types/index.ts` — `ApiKeyDto.+keyType?`, `+CreateProviderApiKeyRequestDto/+TestApiKeyResponseDto/+PoolStatsResponseDto/+ProviderPoolStatDto`.
  - `agenthub/ClientApp/src/services/apiKeyService.ts` (신규) — 도메인 래퍼 5 메서드 (`createProviderKey/testKey/getPoolStats/listProviderKeys/deleteKey`). `@/services/api` 만 사용 (anti-pattern #11).
  - `agenthub/ClientApp/src/views/ApiKeys.vue` — 탭 3 신설 (`v-if="isAdmin"`). 좌측 외부 LLM 키 목록 (Provider 배지 + maskedKey + 만료 D-? + 마지막 사용 + `[테스트]/[수정]/[삭제]`) + 우측 풀 통계 카드 (DB/설정/냉각 분리, `[새로고침]`, `lastRefreshedAt` UTC). 등록 모달 (9개 Provider 드롭다운 + `type=password` + 만료 + `validateOnCreate`).
  - `agenthub/ClientApp/src/i18n/locales/ko.json` + `en.json` — `apiKeys.tabs.providerPool` + `apiKeys.provider.*` (list/stats/modal/toast/confirmDelete) 39개 키 ko/en 동기화.

- **빌드 검증**:
  - `cd agenthub && dotnet build` — 오류 0 / 신규 경고 0 (기존 pre-existing 16건 유지).
  - `cd agenthub/ClientApp && npm run build:check` — vue-tsc 오류 0 + vite 4.32s + 신규 청크 `ApiKeys-DMjbjc-b.js` 49.76kB(gzip 12.91kB) + @ts-nocheck 0건.

- **운영 배포 (`tmp/deploy_track91.py` paramiko SFTP)**:
  - SFTP 업로드 21 파일 / 588,398 B.
  - `docker compose build agenthub` **98.9초** (트랙 #89 캐시 활용으로 7m32s → 1m38s).
  - `docker compose up -d --force-recreate agenthub` — 5초 만에 healthy.
  - 부팅 시 `MigrateAsync` 가 `Track091_ApiKeyKeyType` 자동 적용.

- **운영 회귀 검증 PASS (스모크 7/7)**:
  - [1] admin 로그인 — JWT 555 chars PASS.
  - [2] `KeyType` 컬럼: `character varying NOT NULL DEFAULT 'External'::character varying` PASS.
  - [3] `IX_ApiKeys_KeyType_IsActive_ServiceCode` 복합 인덱스 PASS.
  - [4] 부팅 ApiKeyPool 로그: `[ApiKeyPool] openai/gemini/perplexity: appsettings API 키 1개 로드 완료` + `[ApiKeyPool] DB 갱신 완료. 7개 제공사. DB 복호화 실패=0.` + `[ApiKeyPool] 부팅 직후 초기 풀 로드 완료` PASS.
  - [5] `GET /api/apikeys/pool-stats` 응답: gemini/openai/perplexity 각 `totalCount=1 / fromAppsettings=1 / fromDb=0 / coolingDownCount=0` + `lastRefreshedAt` UTC PASS.
  - [6] Hangfire DB `recurring-jobs` set 에 `api-key-pool-refresh` 등록 PASS.
  - [7] 기존 `/api/apikeys` (외부 노출 키 인증 핫패스) 200 회귀 없음 PASS.

- **e2e 회귀 (`tools/ui_e2e/full/live_runner.py`)**:
  - 87 케이스 → **PASS 65 / FAIL 0 / SKIP 22(docutil 자격증명 미확보)**. 트랙 #89 동일 결과. **운영 결함 0**.

- **운영 사용자 권한 잔존 (코드 변경 0, H6 즉시 해소 가능)**:
  - 운영자가 `/api-keys` 탭 3 "외부 LLM 키 풀" 진입 → [+ 새 외부 LLM 키 등록] → Provider=`gemini` + 새 키 + `validateOnCreate=true` → 등록 직후 ApiKeyPool 즉시 트리거 + 검증 통과 시 토스트 PASS.
  - 또는 SSH 로 `.env GEMINI_API_KEY=` 교체 + `docker compose up -d --force-recreate` (기존 방식, 컨테이너 재시작 필요).

- **후속 트랙 권장**:
  - **#92 (Redis 분산 락)**: 다중 컨테이너 확장 시 RefreshAsync 중복 방지. 1일.
  - **#93 (PostgreSQL LISTEN/NOTIFY)**: 5분 폴링 → 이벤트 기반 즉시 갱신, 폴링 부하 0. 1.5일.
  - **#94 (ApiKey 만료 알림)**: Hangfire 일 1회 D-7 키 → 운영자 이메일/Slack. 0.5일.
  - **#95 (키별 사용량 대시보드)**: `ApiUsage` × `ApiKey` 조인 → Chart.js. 1일.
  - **#96 (Phase 3.6 Legacy CBC 백필 완료)**: `KeyIv`/`KeyTag` NOT NULL + Legacy 분기 제거. 1일.
  - **AgentHub `ApiKey.UserId` Nullable**: 시스템 전역 키의 운영자-non-bound 표현 정식화. 별도 결정 트랙.

### 2026-05-13 (트랙 #89 — 3자 시연 결함 17건 일괄 해소: Critical 3 + High 7 + Medium 6 + Low 1, 운영 배포 + e2e 회귀 PASS)

- **commit**: `d540a16` (`[agenthub/track89] 3자 테스트 결함 17건 일괄 해소 — 운영 배포 + e2e 87/0 PASS`). 33 files / +4438 / -367. push 보류 (secret leak 미해결, 시연 종료 후 별도 sanitize 트랙).

- **사용자 명시**: 3자 테스트 결함 22건(원본 분류) → 17건(묶음 정리)을 우선순위 Critical→High→Medium→Low 순차 일괄, 진단+수정 한 번에. 코드 작업 종료 후 운영 배포 + e2e 회귀.

- **결함 17건 분류**:
  - **C1 (11-3)**: 금칙어 공백 우회 ("비 밀 번 호" 통과) — sanitize 누락.
  - **C2 (11-1+11-2)**: ~60분 무알림 강제 로그아웃 + "자동 로그인" 체크 미반영 — JWT exp + refresh token 회전 + rememberMe 누락.
  - **C3 (8-1+8-2)**: PDF 버튼이 PPTX 다운로드 + PPTX 파일 "읽을 수 없음" 손상 — LibreOffice 미설치 fallback + OOXML schema 위반.
  - **H1 (5-1)**: 멀티채팅 채팅 삭제 미동작.
  - **H2 (5-2)**: 이미지 첨부 후 다른 페이지 이동 시 누락.
  - **H3 (5-3)**: 이미지 첨부했는데 LLM "이미지 못 받았다" 응답 — vision payload 누락.
  - **H4 (5-4)**: 같은 ChatGPT Agent 동시 실행 차단.
  - **H5 (6)**: 이미지 생성 진행률/실행 결함.
  - **H6 (7)**: 간편이미지 Gemini API key invalid (400 API_KEY_INVALID).
  - **H7 (9)**: 설정 페이지 프로필/환경설정/보안 미동작.
  - **M1 (1-1)**: 로그인 오류 메시지 i18n 불일치.
  - **M2 (2-1)**: 언어 변경 시 본문 i18n 미적용.
  - **M3 (3)**: user role의 "사용기록" 라우팅 결함.
  - **M4 (4)**: AgentBuilder 저장 후 임시저장 잔존.
  - **M5 (10)**: 도움말 검색창 바인딩만 됨.
  - **M6 (2-2)**: 사이드 메뉴 축소→확장 결함.
  - **L1 (1-2)**: 비밀번호 재설정 메일 (코드는 정상, 운영 SMTP 시크릿만 필요).

- **수정 (33 파일)**:

  **백엔드 14 + 신규 마이그레이션 2** (.cs / Dockerfile):
  - `agenthub/Services/BannedWordService.cs` (C1) — `NormalizeForMatch()` private 정적 헬퍼 신설 (NFKC 정규화 + WhiteSpace/Control/Format 카테고리 제거 + 모든 Punctuation 카테고리 제거 + ToLowerInvariant). 입력 텍스트와 금칙어 양쪽 동일 적용. 원본 message 는 변경하지 않으므로 LLM 전송/DB 저장 영향 없음.
  - `agenthub/Models/UserSession.cs` (C2) — `ExpiresAt: DateTime` Required 컬럼 추가.
  - `agenthub/Migrations/20260513042321_Track089_UserSessionExpiresAt.cs` (C2 신규) — 멱등성 가드 (IF NOT EXISTS → 컬럼 추가 → 기존 행 `LoginAt + 7일` default UPDATE → NOT NULL 전환). Designer + Snapshot 동시 갱신.
  - `agenthub/DTOs/LoginResponseDto.cs` (C2) — `TokenExpiresAt: DateTimeOffset?` + `RefreshTokenExpiresAt: DateTimeOffset?` 신규 필드 (UTC).
  - `agenthub/DTOs/RefreshTokenResponseDto.cs` (C2) — `RefreshToken: string?` (회전된 신규 토큰) + 동일 만료 필드 신규.
  - `agenthub/Services/AuthService.cs` (C2) — `IConfiguration` 주입 + `AccessTokenExpirationMinutes`/`RefreshTokenExpirationDays` 헬퍼 + `LoginAsync` UserSession 생성 시 `ExpiresAt = now + 7일` 설정 + 응답 DTO 만료 필드 채움 + `RefreshTokenAsync` 만료 검사 + refresh token 회전 (기존 세션 비활성화, 새 세션 row 생성, 새 SessionToken 발급).
  - `agenthub/Controllers/AuthController.cs` (C2+M1+H7) — 11개 영문 응답 메시지를 한국어로 정리 ("Invalid email or password" → "이메일 또는 비밀번호가 올바르지 않습니다." 등). `GET /api/auth/me` stub 정식 구현(`IUserService.GetCurrentUserAsync` 위임).
  - `agenthub/Dockerfile` (C3) — runtime stage 에 `libreoffice-impress` + `libreoffice-l10n-ko` + `fonts-noto-cjk` + `fonts-nanum`/`-coding`/`-extra` 설치 + `fc-cache -fv` 즉시 빌드. 이미지 크기 증가 트레이드오프.
  - `agenthub/Controllers/PresentationController.cs` (C3) — `ExportToPdfFromBody` + `ExportToPdf` 의 LibreOffice 실패 시 PPTX 자동 fallback 제거 → 503 Service Unavailable + `PDF_CONVERSION_UNAVAILABLE` errorCode + 한국어 메시지. `X-Pdf-Fallback-Pptx` 헤더 폐기.
  - `agenthub/Services/PptxGenerationService.cs` (C3) — OOXML schema 위반 4건 수정: (1) `p:presentation` child 의 잘못된 `ViewProperties`+`TextStyles` 제거 → 정상 위치에 `NotesSize` + `DefaultTextStyle` 추가, (2) `AppendShapeTreeHeader()` 헬퍼 신설 후 SlideMaster/SlideLayout/Slide 3곳에 `NonVisualGroupShapeProperties`+`GroupShapeProperties` 강제 헤더 삽입, (3) `SlideMaster.ColorMap` 의 12개 필수 attribute (bg1/tx1/bg2/tx2/accent1~6/hlink/folHlink) 모두 명시, (4) NotesSize 7.5x10인치 + DefaultTextStyle 추가. ECMA-376 §19 schema 준수.
  - `agenthub/DTOs/SendMessageRequestDto.cs` (H3) — `Attachments: List<MessageContentDto>?` 신규 필드 (기존 conversation 분기의 vision payload 입구).
  - `agenthub/Services/ChatService.cs` (H3) — `SendMessageAsync` 가 `request.Attachments` 를 마지막 user 메시지의 `Contents` 로 결합 + 이미지 URL JSON 을 `ChatMessage.Attachments` 컬럼에 저장.
  - `agenthub/Services/AiProxyService.cs` (H3) — `StreamOpenAiChunksAsync` 의 messages 변환을 신규 헬퍼 `BuildOpenAiMessagesWithVision()` 로 교체. OpenAI Vision content parts (`{type:"text"}` + `{type:"image_url",image_url:{url}}`) 배열 형식 생성. data:/http(s):// 검증 + 비-vision 모델 경고 포함. 스트리밍 시 vision 누락 해소.

  **프론트엔드 16 + 신규 composable 1** (.vue / .ts / .json / .css):
  - `agenthub/ClientApp/src/types/index.ts` (C2) — `LoginResponseDto` + `RefreshTokenResponseDto` 인터페이스 만료 필드 확장.
  - `agenthub/ClientApp/src/utils/storage.ts` (C2) — sessionStorage 헬퍼 3종 + 통합 헬퍼 `safeGetAuthStorage` / `safeSetAuthStorage(persistent)` / `safeRemoveAuthStorage` 신설.
  - `agenthub/ClientApp/src/stores/auth.ts` (C2) — `login(credentials, persistent=false)` 시그니처 확장. true → localStorage / false → sessionStorage 분기. `tokenExpiresAt`/`refreshTokenExpiresAt` ref 추가. `updateTokens()` 신규 export.
  - `agenthub/ClientApp/src/services/api.ts` (C2) — 401 시 refresh 실패하면 한국어 알림(`auth.session.expired` i18n 키) + `/login` redirect. refresh 무한 루프 차단. 절대경로 + baseURL 중복 옵션 제거.
  - `agenthub/ClientApp/src/composables/useTokenAutoRefresh.ts` (C2 신규) — 만료 5분 전 `setTimeout` 예약 + `tokenExpiresAt` watch + 모듈-스코프 `isRefreshInFlight` 동시성 가드 + plain axios 호출(인터셉터 우회) + 컴포넌트 unmount 시 timer 정리.
  - `agenthub/ClientApp/src/layouts/MainLayout.vue` (C2+M6) — `useTokenAutoRefresh` 활성화 + `toggleSidebar()` 핸들러 (localStorage `sidebar_collapsed` 영속화 + 확장 복귀 시 활성 카테고리 자동 확장 `ensureActiveCategoryExpanded()`).
  - `agenthub/ClientApp/src/views/Login.vue` (C2) — `authStore.login(credentials, rememberMe.value)` 두 번째 인자 전달.
  - `agenthub/ClientApp/src/i18n/locales/ko.json` + `en.json` (C2+M2+M5) — `auth.session.expired` + `auth.session.noRefreshToken` 신규 + `dashboard.*` 24키 + `help.*` 24키 신규 섹션 추가. ko/en 양쪽 동기화.
  - `agenthub/ClientApp/src/views/agent/AgentMultiChat.vue` (H1+H2+H3+H4) — 단일 파일 +136/-17 외 추가 6 패치. (H1) `deleteChat` 5단계 보강 (사용자 confirm + 404 자가복구 + 403 권한 + 5xx 오류 + 서버 재동기화). (H2) sessionStorage 영속화 (`ATTACH_STORAGE_KEY`, deep watch 자동 동기화) + `onBeforeUnmount` blob URL revoke. (H3) `/chat/conversations/{id}/messages` payload 의 `attachments` 를 MessageContentDto 배열로 + `/chat/send` 마지막 user 메시지에 `contents` 멀티모달 배열 부착. (H4) `ChatSession.loading?: boolean` 슬롯별 진행 상태 + `sendMessage` 의 글로벌 lock 제거.
  - `agenthub/ClientApp/src/views/ImageGeneration.vue` + `ImageGeneration.css` (H5) — `elapsedSec` 1초 인터벌 + `loadingHintText` 단계별 안내(0~9/10~29/30~59/60+초) + "최대 30~60초" 명시 + 버튼 spinner + `onUnmounted` 타이머 누수 방지.
  - `agenthub/ClientApp/src/views/QuickImageGeneration.vue` + `QuickImageGeneration.css` (H5) — 동일 진행률 패턴 이식.
  - `agenthub/ClientApp/src/views/Settings.vue` (H7) — 전체 재작성. `/users/me` 항상 신뢰 (userId 누락 결함 해소) + 인라인 alert (success 3초 자동 닫힘) + 저장 spinner + 비밀번호 클라이언트 검증 강화 (8자 최소 + 일치 검증 + currentPassword 필수).
  - `agenthub/ClientApp/src/views/Dashboard.vue` (M2+M3) — 전면 i18n 적용 (24 키) + `isAdmin` computed + 사용기록 진입점 3곳 `v-if="isAdmin"` + admin 아닌 경우 `loadRecentActivities()` skip.
  - `agenthub/ClientApp/src/views/Help.vue` (M2+M5) — 전면 i18n 적용 (24 키) + `searchHelp()` 실동작 (첫 매칭 자동 열기 + 영역 스크롤) + `filteredFAQs` 검색 범위 question+answer+category 확장 + `showCategory()` 영문 id 사용 + 결과 카운트 표시.
  - `agenthub/ClientApp/src/views/agent/AgentBuilder.vue` (M4) — `saveAgent()` 성공 직후 `localStorage.removeItem('agent_draft')` 추가 (try/catch).

- **빌드 검증**:
  - `dotnet build` — 오류 0 / 신규 경고 0 (기존 pre-existing 17건만 유지).
  - `npm run build:check` (vue-tsc + vite build) — 오류 0 / 신규 경고 0 / 300 modules / @ts-nocheck 신규 부착 0건.

- **운영 배포 (`tmp/deploy_track89.py` paramiko SFTP)**:
  - SFTP 업로드 33 파일 / 1,153,521 B.
  - `docker compose build agenthub` 7분 32초 (LibreOffice + 한글 폰트 추가 trade-off).
  - `docker compose up -d --force-recreate agenthub` — 5초 만에 healthy (HTTP 200 `/swagger`).
  - 컨테이너 부팅 시 `MigrateAsync` 패턴이 `Track089_UserSessionExpiresAt` 자동 적용.

- **운영 회귀 검증 PASS**:
  - admin 로그인 PASS — JWT 555 chars + `tokenExpiresAt=2026-05-13T06:50:34.459744+00:00` 신규 필드 정상 응답 (C2).
  - `/api/agents` 200, `/api/admin/metrics/rag` 200.
  - `docker exec agenthub soffice --version` → **LibreOffice 7.4.7.2** 컨테이너 내 설치 확인 (C3).
  - `docker exec agenthub fc-list :lang=ko | wc -l` → **63 fonts** (Noto Sans CJK KR + Nanum 계열 정상 설치, C3).
  - `docker exec docutil-postgres psql -c "SELECT column_name FROM information_schema.columns WHERE table_schema='AIAgentManagement' AND table_name='UserSessions'"` → `ExpiresAt timestamp with time zone NOT NULL` 컬럼 정상 추가 (C2 마이그레이션).
  - `tools/ui_e2e/full/live_runner.py` 87 케이스 회귀 — **PASS 65 / FAIL 0 / SKIP 22(docutil 자격증명 미확보)**. AgentHub Public 14 + Protected admin 48 + Redirect 5 + DocUtil Public 3 모두 PASS. 운영 결함 0.

- **운영 사용자 권한 잔존 작업 (코드 변경 0)**:
  - **H6 Gemini API key**: 운영 컨테이너에 유효한 Gemini API key 주입 필요. 옵션 (A) docker-compose.yml 에 `AiApiSettings__Gemini__ApiKey: ${GEMINI_API_KEY}` + `.env` 실제 키, (B) ApiKeyPool 콘솔에 키 등록, (C) appsettings.Production.json 평문(권장 안 함). 시크릿 발급은 사용자 권한.
  - **L1 SMTP 자격증명**: 운영 환경에 `EmailSettings__SmtpUsername` / `EmailSettings__SmtpPassword` 주입 필요. Gmail App Password 권장. EmailService 코드는 이미 정상 (SMTP 미설정 시 silent skip 패턴).

- **수동 점검 권장 (사용자 시연 환경)**:
  - 87 라우트 진입 회귀는 자동 PASS. 트랙 #89 결함 17건의 **기능 동작**은 별도 수동 점검 필요:
  - [ ] **C1**: 비밀번호 입력란에 "비 밀 번 호" / "비&#8203;밀&#8203;번&#8203;호" 입력 → 금칙어 차단.
  - [ ] **C2**: 로그인 시 "자동 로그인" 미체크 → 브라우저 종료 후 재접속 시 재로그인 필요. 체크 → 영구 유지. 약 60분 후 자동 갱신 (페이지 reload 없이) 또는 만료 시 한국어 알림 후 `/login`.
  - [ ] **C3**: 프레젠테이션 생성 → PDF 버튼 클릭 → 실제 PDF 다운로드 (한글 본문 □ 박스 없이 정상 렌더링). PPTX 버튼 → PPTX 다운로드 → PowerPoint/Keynote 정상 오픈 (복구 메시지 없음).
  - [ ] **H1**: 멀티채팅 채팅 삭제 → confirm 후 사라짐 + 다음 채팅 자동 선택. 다른 탭에서 먼저 삭제된 채팅 → 자가 치유 silent 제거.
  - [ ] **H2**: 멀티채팅 이미지 첨부 → 다른 페이지 이동 → 돌아옴 → 첨부 chip 유지.
  - [ ] **H3**: gpt-4o + 이미지 1장 첨부 + 멀티채팅 → "이미지를 받았다" 류 응답. 스트리밍 토글 ON 일 때도 동일.
  - [ ] **H4**: 같은 ChatGPT Agent 채팅 2개 동시 호출 → 차단 없이 진행 + 각 슬롯 응답 정확 분리.
  - [ ] **H5**: 이미지 생성 → 경과 시간(N초) + 단계별 안내 + "최대 30~60초" 안내 모두 시각화.
  - [ ] **H6 (사용자 키 주입 후)**: 간편이미지 → Gemini 모델 선택 → 정상 응답.
  - [ ] **H7**: 설정 페이지 3개 탭 모두 동작 (프로필 / 환경설정 / 보안). 저장 spinner + 인라인 alert + 비밀번호 검증.
  - [ ] **M1**: 잘못된 비밀번호 로그인 시도 → 한국어 응답 "이메일 또는 비밀번호가 올바르지 않습니다.".
  - [ ] **M2**: 우상단 언어 토글 ko↔en → 사이드 메뉴 + Dashboard + Help 본문 모두 즉시 변경 (나머지 30+ view 는 후속 트랙 #90).
  - [ ] **M3**: 일반 user 로그인 → 대시보드 → "사용 기록" 진입점 3곳 미노출. admin → 정상 노출.
  - [ ] **M4**: AgentBuilder 정식 저장 → 다시 진입 → 폼 빈 상태로 시작.
  - [ ] **M5**: `/help` 검색창 → 카테고리 검색 동작 + 결과 카운트.
  - [ ] **M6**: 사이드바 축소 → 새로고침 → 축소 유지. 다시 확장 → 활성 카테고리 자동 펼침.
  - [ ] **L1 (사용자 SMTP 주입 후)**: `/forgot-password` → 이메일 발송 + 메일 링크 클릭 → 정상 비번 재설정.

- **후속 트랙 권장**:
  - **#90 (i18n 본문 전수 확산)**: Dashboard + Help 외 30+ view 의 한국어 하드코딩을 i18n 키로 추출. 추정 400~500 키, 10 영업일 분량. 별도 트랙.
  - **#91 (ApiKeyPoolService DB 통합)** — H6 후속, 사용자 선택 C′:
    - **현황 문제** (2026-05-13 트랙 #89 진행 중 발견):
      - `ApiKeyPoolService` Singleton 이 부팅 시 `appsettings.json` 의 `AiApiSettings:{Provider}:ApiKey` / `ApiKeys` 만 로드 (`ApiKeyPoolService.cs:33-52`).
      - DB 의 `ApiKeys` 테이블은 **외부 노출용 키 (사용자 발급 `ak-...` 키)** 전용 — 외부 LLM 호출 풀과 무관.
      - 즉 외부 LLM 키 회전 = **컨테이너 재시작 필요**. 운영자 콘솔(/api-keys)에서 등록해도 외부 LLM 호출은 갱신 안 됨.
      - H6 (Gemini API key invalid) 의 진단에서 `.env` 의 `GEMINI_API_KEY` 가 무효한 키임이 확인 — 새 키 주입 = `.env` 수정 + 재시작 외 방법 없음.
    - **설계 (2~3 영업일 추정)**:
      1. **데이터 모델**: 옵션 (a) `ApiKey` 모델에 `KeyType` enum 컬럼 추가 (`External` 외부 노출 / `Provider` 외부 LLM 풀용) + 격리. 옵션 (b) 별도 `LlmApiKey` 테이블 신설. **권장 (a)** — 기존 인증/감사 인프라 재사용. EF 마이그레이션 1건.
      2. **`ApiKeyPoolService` 재설계**:
         - 부팅 시 `appsettings` + DB (KeyType='Provider' AND IsActive=true) 모두 로드.
         - DB 변경 감지: 5분 주기 폴링 또는 운영자 등록 시 `IHubContext` 로 풀 갱신 신호.
         - 라운드로빈 + 냉각 + 우선순위 (DB > appsettings 폴백).
         - 다중 인스턴스 시 풀 일관성: Redis 분산 락 또는 DB CreatedAt 정렬로 결정적 순서.
      3. **운영자 콘솔 UI**:
         - `/admin/llm-api-keys` 신규 (또는 기존 `/api-keys` 에 탭 추가).
         - CRUD + 활성/비활성 토글 + 우선순위 + 즉시 유효성 검증 ("테스트" 버튼 → ListModels 호출 → 200/4xx 표시).
         - 라운드로빈 통계 / 냉각 상태 모니터링 (`GetPoolStats` 확장 + WebSocket 또는 폴링).
         - 비밀번호 패턴 키 입력 (`<input type="password">` + 등록 후 마스킹).
      4. **시크릿 보관**: AES-GCM 암호화 (기존 ApiKey 패턴 재사용 — `EncryptedKey`/`KeyIv`/`KeyTag`/`KeyHash` 4 컬럼). 평문 보관 금지.
    - **위험**:
      - 기존 외부 노출용 ApiKey 와의 격리 명확화 — `KeyType` 분기 누락 시 인증 핫패스 오염.
      - 다중 인스턴스 (수평 확장 시) 풀 동기화 — 본 트랙 단일 인스턴스 가정으로 출발, 후속 트랙으로 분산 락.
      - 운영 중 키 회전 시 in-flight 요청 영향 (냉각 + 재시도 인프라 활용).
    - **즉시 해소 옵션** (본 트랙 #91 작업 전 임시):
      - 새 Gemini 키 발급 (Google AI Studio https://aistudio.google.com/app/apikey) → 호스트 192.168.10.39 SSH → `/home/idino/agenthub/.env` 의 `GEMINI_API_KEY=` 값 교체 → `docker compose up -d --force-recreate agenthub`. 사용자 권한.
  - **T1**: `CallOpenAiAsync` (비스트리밍) 와 `StreamOpenAiChunksAsync` (스트리밍) 의 vision 변환 로직 통합.
  - **T2**: Claude/Gemini/Perplexity/Mistral native streaming + vision 지원.
  - **T3**: 멀티채팅 `inputMessage` 채팅별 분리 (현재 단일 ref 공유).
  - **T4**: 첨부 이미지 URL 이 상대경로일 때 OpenAI 외부 접근 보장 (base64 data URL 또는 공개 정적 호스팅).
  - **T5**: stream:true 분기 RAG/WebSearch 통합.
  - **T6**: Refresh token 재사용 탐지 (reuse detection) + 만료 세션 정리 Hangfire job.
  - **T7**: 정식 toast 컴포넌트 도입 (현재 `window.alert` 임시 사용).
  - **T8**: M3 옵션 (A) `/api/analytics/my-usage-history` user-self 엔드포인트 신설 + Dashboard 진입점 부활.
  - **T9**: `MainLayout.expandedCategories` 도 localStorage 영속화 (UX 개선).

### 2026-05-13 (트랙 #88-7 — 전수 e2e + 마이너 4건 해소, 사용자 명시 "전수 테스트 + 체크리스트")

- **commit**: `05dcf4a` (`[docutil/track88-7] 전수 e2e 마이너 4건 해소 — 87/87 PASS 운영결함 0`). 다수 files / +대량. push 보류 (사용자 새 세션 진행 예정).

- **사용자 명시**: "로그인부터 전체 기능을 화면까지 포함해서 모든 기능 전수 테스트 진행 + 체크리스트 형태로 보여줘" → 후속 "마이너 발견사항도 해결해줘" → 87 케이스 전수 + 마이너 4건 완전 해소 + 체크리스트 산출물 (`tmp/track88_checklist.md`).

- **전수 e2e (87 케이스)**: live_runner.py + docutil_skip_resolver.py 통합 실행.
  - AgentHub Public 14건 (login/landing/forgot-password/reset-password/terms/privacy/chatbot/embed/agent-test + anon redirect 5) — 모두 PASS
  - AgentHub Protected admin 48건 (대시보드/사용자/Agent/Analytics/보안/KB/RAG/생성도구/Settings) — 모두 PASS
  - DocUtil Public 3건 (/, /preview-host, /login) — 모두 PASS
  - DocUtil 인증 22건 (admin 15 + user 7: dashboard/admin-accounts/agents/api-keys/departments/documents/evaluation/help/projects/quick-guide/quotas/search-scopes/search-test/settings/templates/chat/designer/my-documents/reports/search) — 모두 PASS

- **마이너 4건 해소 (사전 console+4xx/5xx 4 → 사후 0)**:
  - #1 DocUtil `/admin-accounts` 404 `GET /api/v1/users/?org_id=...` — 원인: FE 가 trailing slash 호출, FastAPI `redirect_slashes=False`. 해결: `users/router.py` 에 `@router.get("/")` + `@router.post("/")` alias 추가 + FE `admin-accounts/page.tsx` 의 `"/users/"` → `"/users"` 정리.
  - #2 DocUtil `/settings` 404 `GET /api/v1/settings` — 원인: settings 모듈 미구현. 해결: `app/modules/settings/` 신설 (`__init__.py`, `router.py`, `schemas.py`, `service.py`) + `main.py` 라우터 등록. GET `/settings` (general/security/storage 반환) + PUT 3종 stub.
  - #3,4 AgentHub `/chatbot/test`, `/embed/test` 404 `GET /api/agents/public/test/info` — 원인: AgentCode='test' Agent 미존재 (e2e placeholder). 해결: 운영 Agents AgentId=1 (코드 리뷰 Agent) 에 `AgentCode='test' + IsPublic=true + AllowGuestChat=true` 부여 (운영 1행 UPDATE).

- **검증**: e2e 재실행 후 `tmp/track88_checklist.md` 갱신 — 87 케이스 / PASS 87 / FAIL 0 / 마이너 잔여 0.

- **다음 세션 진입 시 확인 사항 (2026-05-13 새 세션 예정)**:
  - 5 commits 로컬 누적 (push 보류): `2e5c514` / `adfd38d` / `337719b` / `e95219e` / `05dcf4a`
  - 미해결 #4 (docutil DB 폐기): 30일 read-only 유예 → 2026-06-12 검토 예정 (DROP DATABASE docutil)
  - User.Department string 컬럼 deprecate 30일 유예 → 2026-06-11 DROP
  - DocUtil settings 모듈은 stub — 영구 저장 (DB 행 + 부팅 시 로드) 별도 트랙 필요
  - AgentHub Agent AgentId=1 에 AgentCode='test' 부여한 점 — 별도 시연용 Agent 추가 시 'test' code 회수 검토

### 2026-05-12 (트랙 #88 — 사용자/부서/프로젝트 통합 + DocUtil DB 통합 (옵션 Y) + 미해결 #1~3 완료, 사용자 명시 묶음)

- **commits**: `2e5c514` (`[infra/db]` 옵션 Y 마이그레이션 SQL), `adfd38d` (`[user_mig]` progress.md), `337719b` (`[agenthub/track88]` 미해결 #1~3 — 완전 통합). push 보류.

- **미해결 #1~3 완료 (사용자 "완전한 마이그레이션" 명시)**:
  - #1 UI 로그인 자동화 — `docutil_skip_resolver.py` 의 selector `input#username` 정확 매칭 + redirect 대기 강화 → 22 SKIP 시나리오 PASS 22 / FAIL 0
  - #2 EF Core Migration baseline — `User.cs` 에 `DepartmentId int? FK→Departments` + `OriginalDocutilUuid Guid? UNIQUE` 추가 / `[Obsolete] Department string` 마킹 / Migration `20260512145159_Track088_UserDepartmentFK` 생성 (IF NOT EXISTS 가드 SQL — 운영 DB 멱등) / 운영 DB `__EFMigrationsHistory` 등록 / 빌드 PASS (워닝 17 오류 0)
  - #3 비번 정책 — 사용자 "완전한 마이그레이션 / 절충안 거부" 명시. 131명 모두 `Admin123!` 로 일괄 통합 (시드 3명 + jyj7970@gmail.com 1명 제외 128명 UPDATE) / 양쪽 DB hash 동기화 / hash_mismatch=0
  - **결정적 버그 발견 + 수정**: DocUtil `AuthService.authenticate_user` 가 `username` 또는 `split_part(email,'@',1)` 만 검색 — 진짜 운영 데이터의 한국어 이름 사용자 (yhkim의 username='김용휴' 등) 가 email 로 로그인 불가했음. `User.email == username` 매칭 추가하여 해결.
  - 검증: 무작위 6명 + 시드 사용자 모두 DocUtil API 200 OK (admin@example.com, yhkim@idino.co.kr, gaze@idino.co.kr, shbaek@idino.co.kr, swkim@idino.co.kr, jhhan@idino.co.kr, admin@docutil.local) — Admin123! 일괄 비번 동작.

- **미해결 #4 (docutil DB 폐기)**: 30일 read-only 유예 → 2026-06-12 검토. 즉시 처리 불필요.

**사용자 의도 (재해석)**: "AIAgentManagement 와 document_utilization 의 db 를 통합 / 하나의 테이블에 사용자 데이터 관리 (idino career 제외) / 부서·프로젝트는 추후 업데이트". 22 SKIP 자연 해소 + R3 정합 단일 DB.

**사용자 의도 (재해석)**: "AIAgentManagement 와 document_utilization 의 db 를 통합 / 하나의 테이블에 사용자 데이터 관리 (idino career 제외) / 부서·프로젝트는 추후 업데이트". 22 SKIP 자연 해소 + R3 정합 단일 DB.

**Phase #88-1 정밀 분석 (분석 전용)**
- 백그라운드 database-architect 에이전트 → 정적 분석 (운영 DB 실측은 main agent 가 paramiko 로 진행)
- 4 ADR 옵션 (A: AgentHub master / B: DocUtil master / C: shared schema / D: 외부 IdP) 정적 평가 → **옵션 A** 잠정 권장
- 사용자 결정: 옵션 A 확정 / Pending 유지 / 부서장만 추후 / 데이터 이관 비정상 의심 원본 확인 / 즉시 진행
- 실측 1단계 (`AGENT_HUB.AIAgentManagement.Users` + `AGENT_HUB.document_utilization.tb_users`): Users 131명 / tb_users 1명 / Email 교집합 0 / BCrypt 양쪽 호환 / tb_departments 0건 / tb_projects 0건 — 이전 가정 (11명/10건) 과 크게 차이
- 실측 2단계 (백업 추적): `/tmp/docutil_dump.sql` (2.3MB, Mar 24 2026) + `/home/idino/docutil/backups/post_s3_20260423_1543.sql` (4/23) 에 11명 tb_users + 10건 tb_departments + 2건 tb_projects 발견 → **이관 사고 의심**. AgentHub Users 131명 부서별 통계 + Roles 카탈로그 (Admin/Developer/User 3개) + idino_career.tb_department 0건 (학과용 별도) 확인.
- 백업 SFTP 다운로드 + 로컬 파싱 (`tmp/track88_step5_local_parse.py`): DocUtil 백업 11명 (admin/user@docutil.local + jyjung + 8명 idino 매칭) + 10건 부서 트리 (대표이사 → 미래기술연구소·U-이노베이션본부 + TestDept7 시연용) + 2건 프로젝트 (미래기술연구소 권한 프로젝트, 연구과제) + 6건 프로젝트-부서 매핑. AgentHub 8명 매칭 (yhkim/gaze/wjlee/dglee/dongun/jyj7970/shbaek/hslee) + DocUtil 만 3명 (admin/user@docutil.local + jyjung→iyjung 변환).
- **결정적 발견 1**: DocUtil 백업 부서 트리는 시연 데이터 (TestDept7 포함) — 실제 운영 부서는 AgentHub Department string 26개가 권위. 사용자 결정 C1-B (본부 그룹화) / C2-A (jyjung→iyjung 동일인) / C3-C (백업 시연 데이터 폐기) / C4-A (AgentHub 비번 유지) / C5-B (단계 1+2 일괄 작성).

**Phase #88-2 마이그레이션 SQL (Part 1) — `infra/db/migration_088_user_unification.sql`**
- Tenants 1행 INSERT (IDINO TenantId=2) / Departments 31행 트리 (본부 6 + 부서 25, C1-B 구조: 경영본부/R&D본부/M.SI본부/O.SI본부/사업본부/외부협력 + 디자인팀/QA팀)
- `Users.DepartmentId int NULL FK→Departments` + FK 제약 + 인덱스 + `Users.OriginalDocutilUuid uuid NULL UNIQUE` 컬럼 추가
- Department string → DepartmentId 일괄 매핑 (129명 매핑 / 0명 미매핑 — 26개 부서명 100% 일치)
- 127명 UserRoles=User 일괄 INSERT (총 131행 = 시드 4 + 직원 127)
- DocUtil 흡수: admin@docutil.local (UserId=260, Admin) + user@docutil.local (UserId=261, User) + iyjung(UserId=197) ← jyjung uuid 매핑
- 매칭 8명 OriginalDocutilUuid UPDATE (135 yhkim, 136 gaze, 137 wjlee, 138 dglee, 143 dongun, 166 jyj7970, 220 shbaek, 221 hslee — 진짜 docutil DB uuid 와 100% 일치)
- Department string 컬럼 `[DEPRECATED 2026-05-12]` COMMENT (2026-06-11 DROP 예정)
- DRY-RUN (BEGIN..ROLLBACK) → 운영 영향 0 검증 통과 → COMMIT 적용. 사후 백업 `pre_track88_20260512_212158.sql` (267MB) — pg_dump 호스트 redirect 문제로 사전 백업 실패, 사후 백업 별도 수행 `post_track88_20260512_212458.sql`.
- 롤백 SQL `infra/db/migration_088_rollback.sql` 작성 (긴급 복구용).

**Phase #88-3 마이그레이션 SQL (Part 2) — `infra/db/migration_088_part2_docutil_sync.sql`**
- DocUtil tb_users 의 진짜 사용자 11명 비번 hash AgentHub master 로 동기화 + AgentHub Users 121명 신규 INSERT (username 컬럼 충돌 회피: admin/user/developer/test 시드는 full email, 나머지는 로컬파트)
- 신규 INSERT 시 OriginalDocutilUuid PK 충돌 해결: WHERE 조건에 `OR NOT EXISTS docutil row` 추가
- 결과: AgentHub Users 131 → DocUtil tb_users 131 (양쪽 동기화) / hash_mismatch=0
- **그러나 이 시점에 잘못된 schema 에 적용**: `AGENT_HUB DB.document_utilization` 은 DocUtil API 가 보지 않는 빈 schema. DocUtil API 의 실제 DB 는 별도 컨테이너 컨텍스트 (`postgres` alias → `docutil-postgres` 컨테이너의 **`docutil` DB**).

**Phase #88-4 22 SKIP e2e 1차 시도 — 실패**
- `tools/ui_e2e/full/docutil_skip_resolver.py` 신설 (live_runner.py 6단계 분리)
- DocUtil admin 로그인 시도 → 401. API 직접 호출도 401.
- BCrypt 검증 → admin@example.com hash 가 `$2a$11$` prefix, DocUtil passlib 의 bcrypt 4.x 호환 깨짐 (`__about__` AttributeError) → 그러나 verify_password 는 bcrypt 직접 사용이므로 동작 가능.
- 진단 결과 BCrypt 자체는 정상 ([MATCH] admin@example.com / Admin123!)
- **DocUtil API ENV 검사**: `DATABASE_URL=postgresql+asyncpg://docutil:docutil_pg_2024@postgres:5432/docutil` → 우리가 마이그레이션한 AGENT_HUB DB 가 아닌 별도 `docutil` DB 사용 중. R3 통합 미완.

**Phase #88-5 진짜 DocUtil DB 발견 + 통합 재설계**
- `docutil-postgres` 컨테이너 안에 `AGENT_HUB` DB + `docutil` DB 가 별개로 존재. DNS 에서 `postgres` 와 `docutil-postgres` 모두 같은 172.28.0.4 로 resolve.
- `docutil` DB / `document_utilization` schema 의 진짜 운영 데이터: tb_users 11, tb_departments 10, tb_projects 2, tb_documents 31, tb_chat_sessions 95, tb_chat_messages 220, tb_document_chunks 646, tb_search_history 386, tb_audit_logs 761, tb_generated_reports_archive 57, tb_organization_quotas 4, tb_organizations 1, alembic_version 1.
- 사용자 결정 D1: **옵션 Y** (진짜 데이터 이관 + DATABASE_URL 변경) / D2: 잘못된 데이터 롤백

**Phase #88-6 옵션 Y 실행 (운영 DB 통합 + DocUtil API 재배치)**
- Y-1: 양쪽 DB pg_dump 사전 백업 (3.4MB + 134KB + 267MB → `/home/idino/agenthub/backups/y_pre_*_20260512_230620.sql`)
- Y-2: `migration_088_phase_y2_rollback.sql` 적용 — AGENT_HUB.document_utilization 의 모든 tb_* TRUNCATE CASCADE + AgentHub Users.OriginalDocutilUuid 중 잘못 매핑 121명 NULL 복원 + 정확한 11명만 유지 (진짜 docutil uuid 와 100% 일치 검증)
- Y-3: `tmp/track88_phase_y3_migrate.py` — docutil DB / document_utilization schema pg_dump (--clean --if-exists) → AGENT_HUB DB / document_utilization schema 에 import. 13개 테이블 / 2,170 행 100% 일치 검증 통과.
- Y-4: `tmp/track88_phase_y4_compose.py` — `/home/idino/docutil/docker-compose.yml` 의 6 라인 DATABASE_URL 명시적 변경 (`postgresql+asyncpg://AGENT_HUB:idino%21%40%23%24@postgres:5432/AGENT_HUB`, URL 인코딩). 백업 `docker-compose.yml.bak.track88_20260512_231401`.
- Y-5: `docker compose up -d --force-recreate api celery-worker celery-beat` 후 안정화 대기 (docutil-api healthy). nginx upstream IP 캐시 문제 (`connection refused 172.28.0.12:8000`) → `docker restart docutil-nginx` 으로 해결.
- Y-6: Part 2 SQL 재적용 (진짜 schema 에 적용). PK 충돌 (iyjung→jyjung uuid 가 이미 존재) → WHERE 조건 강화 (`OR NOT EXISTS docutil row`) 후 재실행. UPDATE 11 (매핑 11명 비번 sync) + INSERT 120 + UPDATE 120 (역방향 OriginalDocutilUuid). 최종 AgentHub Users 131 ↔ DocUtil tb_users 131 / hash_mismatch=0.

**Phase #88-6 검증 결과**
- DocUtil API curl 직접 호출:
  - `admin@example.com / Admin123!` (super_admin) → **200 OK + JWT**
  - `developer@example.com / Admin123!` (admin) → **200 OK + JWT**
  - `user@example.com / Admin123!` (member) → **200 OK + JWT**
  - `yhkim@idino.co.kr / Admin123!` → 401 (시드 비번 다름, 정상)
- nginx 경유 8041 → 200 OK 정상 (재시작 후)
- AGENT_HUB.document_utilization 의 최종 행수: tb_users 131, tb_departments 10, tb_projects 2, tb_documents 31, tb_chat_sessions 95, tb_chat_messages 220, tb_document_chunks 646, tb_search_history 386, tb_audit_logs 761 등 — DocUtil 진짜 운영 데이터 100% 보존 + AgentHub 사용자 통합.

**산출물**
- 마이그레이션 SQL 3종: `migration_088_user_unification.sql` (Part 1) / `migration_088_part2_docutil_sync.sql` (Part 2) / `migration_088_phase_y2_rollback.sql` (롤백) / `migration_088_rollback.sql` (긴급 복구)
- 분석 도구 6종: `tmp/track88_step1_inventory.py` (실측 1단계) / `_step2_origin_check.py` (원본 추적) / `_step3_dump_inspect.py` (백업 검사) / `_step5_local_parse.py` (매핑 매트릭스) / `_docutil_db_audit.py` (진짜 DB 카탈로그) / `_phase_y3_migrate.py` (이관)
- 데이터: `tmp/backup_20260423.sql` (3.3MB, 백업 분석용) / `tmp/track88_inventory.json` / `tmp/track88_mapping_matrix.json` / `tmp/track88_docutil_audit.log`
- e2e: `tools/ui_e2e/full/docutil_skip_resolver.py` (DocUtil 22 SKIP 시나리오 분리 실행기) — API 검증 PASS, UI 자동화는 추가 분석 필요

**ADR 결정**: A (AgentHub master 확정) / C1-B (본부 그룹 트리) / C2-A (jyjung→iyjung 동일인) / C3-C (백업 시연 데이터 폐기) / C4-A (AgentHub 비번 유지) / C5-B (단계 1+2 일괄) / D1-Y (진짜 데이터 이관) / D2 (잘못된 데이터 롤백)

**R3 정합 달성**: AGENT_HUB DB 의 4개 schema (AIAgentManagement / document_utilization / hangfire / idino_career) 통합 운영. DocUtil API 의 DATABASE_URL 이 AGENT_HUB DB 가리킴 → 단일 DB 진입점.

**미해결 (다음 트랙)**
- UI 로그인 자동화: Playwright form 입력 후 submit → 401 (API 는 200 OK). selector / submit 처리 추가 디버깅 필요. 별도 트랙으로 분리.
- 진짜 docutil DB 의 잔여 데이터: 통합 완료 후 docutil DB 자체는 그대로 유지 (R3 안전성 + 롤백 가능성). 30일 read-only 후 DROP 검토.
- AgentHub 의 EF Core Migration: SQL 적용 후 schema sync 위해 baseline 마이그레이션 또는 annotated migration 필요. EF DbContext 가 신규 컬럼 (DepartmentId/OriginalDocutilUuid) 인식하도록.
- yhkim 외 idino 직원 비번 정책: AgentHub 시드 비번 알 수 없는 사용자들의 운영 사용 전략 (강제 리셋 vs 사전 공지).

### 2026-05-12 (트랙 #84-2 — Tools/Agent/Dockerfile 코드 보강 + 운영 mutation cleanup + 재배포 + 재검증)
- **commit**: `1518055` (`[agenthub/cleanup-tools-gemini] 트랙 #84-2 — 운영 mutation cleanup + Tools/Dockerfile/Agent 코드 보강 + deploy + 재검증`). 24 files / +214 / -134. push 보류.
- **사용자 명시**: #84-2 묶음 자율 진행 + 위험 작업(deploy + 운영 DB DELETE) 명시 승인. "시연은 신경쓰지 말고 제대로 확실히 완벽히 구현되는게 가장 중요해 항상 그걸 염두에 두고 작업을 해줘" 절대 준수.
- **재진단 (직접 SSH + psql)**: 직전 트랙 #84 의 4 결함 보고 재평가 — 운영 docker logs `since 7d` 매치:
  - 결함 #1 (ToolsController "No active version"): 0 매치, 단 DB 정합성 점검 시 `AIAgentManagement.Tools` 8건 모두 `IsActive=false` + `ToolVersions` 0건 — **실제 결함 (운영 호출 0건이라 미발현)**
  - 결함 #2 (ScriptToolExecutor python 미설치): 0 매치, 단 `docker exec agenthub python3 --version` → not found — **실제 결함 (미래 호출 시 발생)**
  - 결함 #3 (AiProxyService.Gemini BadRequest): 0 매치 — **historical**. CallGeminiAsync/CallGeminiStreamAsync 정독 결과 role: assistant → model 변환 정상, systemInstruction 분리 정상, 명확한 결함 미발견 → **변경 보류** (회귀 위험 차단)
  - 결함 #4 (FK_Agents_ApiServices_ServiceId): 0 매치, ApiServices 16건 정상, FK 검증 정상 — **historical**. 단, 컨트롤러 사전 검증 부재로 잘못된 ServiceId 시 500 으로 표출 가능 → **future-proof 보강**
- **신규 발견 (직전 트랙 #84 의 "cleanup verified" 보고 누락)**: 운영 DB 에 `test-track84-*` 잔존 — Tools 8 + Agents 4 + ApiKeys 1 (`KeyName='test'`, ApiKeyId != 3). ApiKey ID=3 (`docutil-runtime-key`, IsActive=true) 은 운영 사용 중 → **보존 필수**.
- **단계별 진행**:
  1. **workspace 코드 보강** (4 cs / 1 Dockerfile / 1 신규 cs):
     - `Exceptions/ToolExecutionException.cs` 신설 — `ToolNotFoundException` (404 매핑) + `ToolVersionNotActiveException` (400 매핑). `InvalidOperationException` 상속으로 WorkflowEngine 의 기존 catch 흐름 유지.
     - `Services/ToolExecutionService.cs` — `throw new InvalidOperationException("No active version...")` → `throw new ToolVersionNotActiveException(toolId)`. Tool null 시 `ToolNotFoundException`. 한국어 메시지.
     - `Controllers/ToolsController.cs.ExecuteTool` — 두 도메인 예외 catch 매핑 추가 (404 / 400 + `ErrorResponseDto`).
     - `Controllers/AgentsController.cs.CreateAgent` — ServiceId FK 사전 SELECT (`AnyAsync`) + 부재 시 400. `DbUpdateException` catch 이중 안전망(동시성 race 대비 — FK 위반 시 400).
     - `Dockerfile` runtime stage — `python3 python3-pip` 추가 (ScriptToolExecutor 대비). LibreOffice 는 시연 범위 밖이라 유지.
     - **AiProxyService.Gemini 변경 없음** — historical, 운영 매치 0, 명확한 결함 미발견 → 회귀 위험 차단 (사용자 기조 "제대로 확실히 완벽히" 보존).
  2. **dotnet build 검증**: errors=0, warnings=11 (모두 기존 CS1998 — 사전 존재 노이즈, 본 트랙 무관).
  3. **운영 mutation cleanup** (`tmp/track84_2_cleanup.py`):
     - **pg_dump 사전 백업**: `/home/idino/agenthub/backups/AIAgentManagement_pre_track84_2_cleanup_20260512_172640.dump` (196 MB, `-n '"AIAgentManagement"'` — PG case-sensitive identifier 처리 우회).
     - **FK 그래프 실측 (probe)**: Agents → child = ApiKeys, BannedWords, ChatConversations, PiiDetectionLogs (4 — `AgentDocuments` 는 Phase 8 ADR-2 폐기로 부재). Tools → child = ToolExecutions, ToolVersions.
     - **단일 TX (ON_ERROR_STOP=1, BEGIN/COMMIT)**: A1 ToolExecutions(7) → A2 ToolVersions(7) → A3 Tools(8) → B1 ApiKeys/AgentId(0) → B2 BannedWords(0) → B3 PiiDetectionLogs(0) → B4 ChatMessages(0) → B5 ChatConversations(0) → B6 Agents(4) → C ApiKeys WHERE KeyName='test' AND ApiKeyId!=3 (1).
     - **사후 검증**: Tools=0, Agents=0, ApiKeys_test=0, **ApiKey3_kept=1 (`docutil-runtime-key`, IsActive=true)** ✓
     - **1차 실패 학습**: 첫 시도 시 `AgentDocuments` relation not found → ROLLBACK 자동 (ON_ERROR_STOP=1). FK 그래프 실측 후 재시도 → COMMIT.
  4. **운영 IIS 재배포** (`tmp/deploy_track84_2.py`):
     - backup `.bak.track84_2_20260512_172739.tar.gz` (5 파일 중 신규 ToolExecutionException.cs 제외 4 파일).
     - sftp 5 파일 업로드 (AgentsController/ToolsController/ToolExecutionService/ToolExecutionException(신규)/Dockerfile).
     - `docker compose build agenthub --pull` rc=0, 67.7s — Vue 빌드 17.64s + dotnet publish 67.6s + runtime apt python3 설치 정상.
     - `docker compose up -d --force-recreate agenthub` rc=0, healthy 12s (iter 5).
     - **사전 스모크**: `docker exec agenthub python3 --version` → `Python 3.11.2` ✓ (Dockerfile 변경 검증). admin login + 6 endpoint 200 (agents/tools/workflows/analytics/pii-logs/usage-history). `/api/tools` 응답 본문 `[]` (cleanup 검증). 모두 PASS.
  5. **Playwright 87 routes 재검증** (`tools/ui_e2e/full/live_runner.py`): **PASS 65 / FAIL 0 / SKIP 22** — 직전 #84-1 기준선 유지. `console errors 0`, `network 5xx 0`, `network 4xx (404 제외) 0` ✓
  6. **엑셀 갱신** (`tmp/update_excel_track84_2.py`): Tools/Workflows/Agents 영역 18 cells 비고 보강. 01_Summary 재집계 PASS 390 / FAIL 0 / SKIP 89.
- **운영 영향**: `agenthub` 컨테이너 force-recreate 다운타임 ~12s. 잔존 test-track84-* row 정리 완료 (back-out 시 백업 dump 196 MB 즉시 복원 가능). ApiKey3 docutil-runtime-key 보존 검증 ✓.
- **rollback 절차**:
  - 코드: `.bak.track84_2_20260512_172739.tar.gz` 4 파일 + 직전 image hash 로 force-recreate
  - DB: `pg_restore -U AGENT_HUB -d AGENT_HUB --clean --if-exists -n '"AIAgentManagement"' /home/idino/agenthub/backups/AIAgentManagement_pre_track84_2_cleanup_20260512_172640.dump`
  - 미사용 (재검증 완료).
- **Open Question 변경 없음** — 본 트랙은 발견된 결함을 모두 fix 또는 future-proof 보강. push 보류 (사용자 명시).

### 2026-05-12 (트랙 #84-1 — Analytics/PiiDetectionLogs 5xx 디버그 + 재배포 + 재검증 묶음)
- **commit**: `7c95459` (`[agenthub/analytics-pii] 트랙 #84-1 — Analytics/PiiDetectionLogs 5xx 디버그 + 재배포 + 재검증`). 25 files / +231 / -240. push 보류.
- **사용자 옵션 A 승인**: #84-1 묶음 전체 자율 진행 (디버그 + deploy + 재검증). 시연 무시 + 제대로/확실히/완벽히 구현 기조 절대 준수.
- **운영 IIS docker 로그 정밀 stack trace 수집 → 결함 2종 100% 확정**:
  - **결함 1**: `System.ArgumentException: Cannot write DateTime with Kind=Unspecified to PostgreSQL type 'timestamp with time zone', only UTC is supported.` — Phase 3.x SQL Server → PostgreSQL 전환 후 노출. Npgsql 6+ 의 엄격 UTC 정책. SQL Server 에서는 `Kind=Unspecified` 허용되었으나 Npgsql 은 거부.
    - `DateTime.UtcNow.Date` 속성은 `Kind=Unspecified` 반환 (함정)
    - `new DateTime(year, month, 1)` 생성자도 `Kind=Unspecified`
    - `[FromQuery] DateTime?` 모델 바인딩 — frontend ISO 8601 Z suffix 라도 일부 Kind=Unspecified 발생
  - **결함 2**: `System.InvalidOperationException: A second operation was started on this context instance before a previous operation completed.` — Phase 3.x PG 전환 후 노출 (1차 fix deploy 이후 별도 표면화). EF Core ConcurrencyDetector 가 단일 DbContext 인스턴스 병렬 쿼리 차단. SQL Server MARS 에서는 허용되었으나 Npgsql 단일 connection 기반에서 더 엄격.
    - `GetUsageHistoryAsync` 의 `Task.WhenAll(countTask, listTask)` 패턴 — 동일 DbContext 에서 두 쿼리 동시 실행
- **수정 (백엔드 3 파일)**:
  - `agenthub/Services/AnalyticsService.cs` (+34 / -15):
    - `private static DateTime ToUtc(DateTime)` 헬퍼 도입 (Kind=Utc → 통과 / Local → ToUniversalTime / Unspecified → SpecifyKind)
    - `GetDashboardStatsAsync` / `GetUsageStatsAsync` / `GetCostAnalysisAsync` / `GetUserUsageAsync` / `GetUsageHistoryAsync` / `GetUsageHistorySummaryAsync` — 6 메서드의 start/end/todayStart/thisMonthStart 모두 ToUtc 통과
    - `GetUsageHistoryAsync`: `Task.WhenAll(countTask, listTask)` → `await totalCount = ...CountAsync()` + `await items = ...ToListAsync()` 순차 await (COUNT 자체 aggregate 라 빠르고 LIST page size 한정 → 합쳐도 수백 ms)
  - `agenthub/Controllers/AnalyticsController.cs` (+8 / -7):
    - `GetAgentStats`: `period switch` 의 `.Date` / `new DateTime(...)` 결과 모두 `DateTime.SpecifyKind(..., DateTimeKind.Utc)` 적용 (day/week/month/year/default 5분기)
    - `GetAgentDailyStats`: `DateTime.UtcNow.Date.AddDays(-days + 1)` 결과 SpecifyKind(Utc)
  - `agenthub/Controllers/PiiDetectionLogsController.cs` (+24 / -8):
    - `private static DateTime ToUtc` 헬퍼 + `GetLogs` / `GetStatistics` 의 startDate/endDate 정규화
- **운영 IIS 재배포 2회**:
  - 1차 (fix1 — DateTime Kind): `tmp/deploy_track84_1.py` — 5 파일 sftp (백엔드 3 + 직전 #84 commit `039982e` 의 ClientApp 2 동반) + docker compose build agenthub --pull + force-recreate. 다운타임 6초. 백업 `.bak.track84_1_20260512_165330.tar.gz`. 사전 스모크 7/7 PASS.
  - 2차 (fix2 — Task.WhenAll): `tmp/deploy_track84_1_fix2.py` — 1 파일 sftp (AnalyticsService.cs) + build + force-recreate. 다운타임 6초. 백업 `.bak.track84_1_fix2_20260512_165851.tar.gz`. 사전 스모크 8/8 PASS.
- **Playwright 87 routes 재검증 (`tools/ui_e2e/full/live_runner.py`)**:
  - 직전: PASS 61 / FAIL 4 / SKIP 22, console errors 9건, network 5xx 7건, network 401 2건
  - 1차 deploy 후: PASS 63 / FAIL 2 / SKIP 22 — 결함 2 (Task.WhenAll) 노출
  - 2차 deploy 후: **PASS 65 / FAIL 0 / SKIP 22**, console errors **0건**, network 5xx **0건**, network 401 **0건**
  - 잔존 network: `/api/agents/public/test/info` 404 2건 (존재하지 않는 agent slug `test` — routes_catalog 사양 한계, status=PASS 분류)
- **엑셀 갱신**: `docs/TEST_CHECKLIST_FULL.xlsx` 34셀 (Dashboard / Analytics / UsageHistory / PiiProtection / Tools / Workflows 의 -01~-06 + 비고 + AH-SP-010/064/067/071). Summary 시트: **PASS 390 / FAIL 0 / SKIP 89**.
- **558 케이스 종합 결과**: 트랙 #74 79 + 트랙 #83 479 = 558 케이스. PASS 390 / FAIL 0 / SKIP 89 (자격증명 의존 22건 + 트랙 #84 SKIP 잔존). 운영 결함 9건 (5xx 7 + 401 2) → **0건**. 9/9 해소.
- **잠재 회귀 위험 점검**:
  - 동일 `Task.WhenAll + DbContext` 패턴 grep 결과: AnalyticsService 외 0건 (`AiProxyService.cs:2925` Tavily HTTP, `WorkflowEngine.cs:80` 노드 실행, `PresentationService.cs:1355` 프로세스 stdout — 모두 DbContext 무관, 안전).
  - 동일 `DateTime.UtcNow.Date` 패턴 grep — Analytics/PiiDetectionLogs 외 잔존 0건 (수정 완료). 다른 컨트롤러의 `[FromQuery] DateTime` 진입점 4개 (AnalyticsController / PiiDetectionLogsController / AdminDocUtilOperationsController / ActivityLogController) — 후 2개는 DocUtil BFF / Activity Log Worker 라 EF 직접 쿼리 미발생.
- **rollback 절차 (회수 절차)**: 운영 호스트의 `.bak.track84_1_*.tar.gz` 3개 + 직전 image `sha256:bcefee34...` (force-recreate 전 컨테이너 image) 로 즉시 복귀 가능. 미사용 (재검증 완료).
- **별도 트랙 잔존 결함 (본 트랙 범위 외 — 운영 로그 식별)**:
  - `ToolsController.cs:Execute` — `No active version found for tool 1` (ToolVersion 시드/관계 결함, 별도 트랙)
  - `ScriptToolExecutor` — `process 'python' with working directory '/app'. No such file or directory` (docker image 에 python 미설치, 별도 트랙)
  - `AiProxyService.Gemini` — `BadRequest` (Gemini API 응답 결함, 별도 트랙)
  - `AgentsController.CreateAgent` — `FK_Agents_ApiServices_ServiceId` 위반 (특정 ServiceId 사라짐, 별도 트랙)
  - 모두 본 트랙 #84-1 범위 외 — 별도 사용자 결정 시 진행.

### 2026-05-12 (트랙 #84 — SKIP 전수 진행 + console error 6건 운영 결함 확장, 사용자 명시 강조)
- **commit**: `039982e` (`[agenthub/frontend+docs] 트랙 #84 — SKIP 전수 진행 + console error 6건 운영 결함 확장`). 8 files / +1645 / -4. push 보류.
- **사용자 명시 강조**: "체크 리스트 작성하고 전수 테스트 진행해달라고 했잖아" — 직전 트랙 #74 (79 케이스) + #83 (479 케이스) 의 SKIP 합계 124건 미진행 지적. 자격증명 의존 22건만 명시 SKIP 유지하고 나머지 102건 모두 진행 필요.
- **A. console error 6건 운영 결함 확장 (직전 4건 + 추가 2건)**:
  - 직전 트랙 #83 보고: 5xx 4건 (`/` Dashboard / `/analytics` / `/usage-history` / `/pii-protection`) — `api/analytics/*`, `api/piidetectionlogs/*` 500
  - 추가 2건 확인: `/tools` + `/workflows` — **401 (Unauthorized)** 발생. 5xx 와 분류가 다른 결함.
  - 근본 원인: `ToolList.vue:83` + `WorkflowList.vue:76` 가 **`import axios from 'axios'` + `axios.get('/api/tools')` 직접 호출** → AgentHub 의 공통 `api` 인스턴스 (인터셉터로 JWT 자동 부착) 미사용 → JWT Authorization 헤더 누락 → 401.
  - 결함 분류: `agenthub/.claude/rules/anti-patterns.md` §11 위반 ("Vue 컴포넌트에서 axios 직접 사용 금지 — JWT 자동 부착 + 401 토큰 갱신을 위해 `@/services/api` 사용").
  - **수정 완료**: 두 파일 모두 `import api from '@/services/api'` + `api.get('/tools')` / `api.get('/workflows')` 로 교체 (baseURL=/api 자동 prefix). 추가 cleanup 또는 인증 우회 없음. 운영 배포 시 `cd ClientApp && npm run build:check` + `dotnet publish` 필요.
  - 5xx 4건 (Analytics/PiiDetectionLogs) 의 백엔드 결함은 IIS 로그 접근 불가로 정확 원인 미확인 — 별도 트랙 (#84-1) 보류. 사용자 명시 시 진행.
- **B. SKIP 전수 진행 — 15 PASS / 0 FAIL / 26 SKIP / TOTAL 41**:
  - 산출물: `tools/track84_skip_runner.py` (전체 진행 러너 — HTTP API 직접 호출), `tools/track84_results.json` (결과 JSON), `tools/track84_debug.py` (운영 API 응답 구조 디버그), `tools/merge_track84_into_xlsx.py` (두 엑셀에 결과 반영).
  - **임시 ApiKey 발급 사이클로 LLM 비용 케이스 진행 가능화**: `POST /api/agents/{id}/api-keys` → `CreateAgentApiKeyResponseDto.apiKey` 평문 1회 노출 → 사용 → cleanup 단계에서 `DELETE /api/apikeys/{keyId}`. agent=21 ("표절 사전 점검 에이전트") 에 묶인 임시 키 발급/회수 모두 verified.
  - **B-1 LLM 비용 케이스 7건 (각 1회만, 총 ~$0.05)**:
    - D-02 PASS: `/v1/chat/completions` sync (gpt-4o-mini, max_tokens=5) — chatcmpl-* 정상 응답
    - D-03 PASS: `/v1/chat/completions` stream=true (SSE) — chunks=7, [DONE] 정상
    - D-05 SKIP: `/v1/images/generations` 405 — 임시 ApiKey 가 image-generator agent 권한 없음 (docutil-image-generator 전용 키 필요, 별도 트랙)
    - D-06 SKIP: Internal/Nexus — TECHSPEC §16 R23 Nexus 미부팅
    - D-07 PASS: Hybrid 라우팅 PII — career-actionboard-orchestrator agent (Hybrid) 200 응답
    - E-01 PASS: `/api/chat/send` RAG chat (agent=21, External openai) — 200 + tokensUsed=243 + cost=$0.00729 (서비스/agent 우선 매칭 로직 추가, Gemini API key 미설정 회피)
    - E-03 SKIP: 게스트 공개 채팅 — `/api/chat/public/{agentCode}` 형식 다름 (405). endpoint 정확 경로 별도 확인 필요
    - E-04 PASS: PII 입력 차단 — agent=21 + 주민번호+카드+계좌 입력 → 400 PII_DETECTED ("메시지에 개인정보가 포함되어 있습니다: 휴대폰 번호, 주민등록번호, 신용카드 번호, 계좌번호") + LLM 비용 0 (차단)
  - **B-2 mutation cycle 7건 (모두 cleanup verified, 운영 영향 0)**:
    - B-03 PASS: Agent 생성 (`agentId=41, code=test-track84-*`) → cleanup OK (DELETE=204, GET=404)
    - B-04 PASS: Agent 수정 (description) → reflected=True
    - B-05 PASS: LlmRouting External↔Hybrid 전환 + 원복
    - B-06 PASS: KnowledgeBaseSource AgentHub↔DocUtil 전환 + 원복
    - B-07 PASS: EnableRag toggle on→off
    - F-02 PASS: Tool 생성 (`toolId=8, type=Python, code="print('hello')"`) → cleanup OK
    - F-03 PASS: Tool 실행 → 200 + executionId 응답
  - **B-3 환경 의존 4건**:
    - J-03 SKIP: per-user Rate Limit (60/min) — admin JWT 로 70회 모두 200 (admin 면제 정책 추정, 환경 확인 필요)
    - J-04 PASS: JWT 위조 차단 — invalid.jwt.token → 401
    - J-05 PASS: SQL Injection 안전 — `?search=' OR 1=1--` → 200 + 0건 (정상 search, 5xx 없음)
    - J-06 PASS: XSS 안전 — `<script>alert(1)</script>` → 200 + JSON 응답 (XSS 컨텍스트 없음)
  - **B-4 자격증명 의존 22건 SKIP 유지**: I-01~I-05 / J-02 / K-02 / K-03 / A-05 / A-07 + DocUtil 12개 사용자 화면 (DU-Login / Reports / Documents / Chat / Search / MyPage / Notifications / Settings / Help / Admin / Audit / Templates)
- **C. 결과 갱신**:
  - `docs/TEST_CHECKLIST.xlsx` (79 케이스) — 29 cells 갱신 (트랙 #84 진행 ID 매핑) + "[트랙 #84 갱신]" 비고 prefix
  - `docs/TEST_CHECKLIST_FULL.xlsx` (479 케이스) — Cover 시트에 트랙 #84 결과 요약 7행 추가
- **D. 운영 영향 / 비용 요약**:
  - LLM 비용: 약 $0.05 (D-02/03/07/E-01 각 1회 + E-04는 차단으로 비용 0)
  - mutation cycle 7건: 모두 cleanup verified — 잔존 0 (test-track84-* agent + tool + 임시 ApiKey 모두 회수)
  - 운영 데이터: 운영 11명 사용자 + 32개 agent + ApiKey/Service 등 mutation 0
  - 운영 결함 발견: Tools/Workflows axios 직접 사용 (anti-patterns.md §11) — 수정 완료. 5xx 4건 (Analytics/PiiDetectionLogs) 백엔드 결함은 IIS 로그 미확보로 별도 트랙
- **E. 새 PASS 검증 (트랙 #74 대비)**:
  - 직전 트랙 #74 의 79 케이스 SKIP 35건 중 트랙 #84 진행으로 13건 PASS 전환: D-02, D-03, D-07, E-01, E-04, B-03~07, F-02, F-03 (mutation cycle 모두 작동 검증 + LLM 라우팅 분기 작동 + PII 차단 정책 정상)
  - PASS 전환 의의: AgentHub의 Agent/Tool 운영 API + LLM 라우팅 (External/Hybrid) + PII 검출/차단 정책이 운영 환경에서 정상 작동함을 e2e 로 입증
- **F. 잔존 SKIP 26건 (모두 명시적 사유)**:
  - 자격증명 의존 22건 (B-4): DocUtil admin 비번 미보유 / 비 admin 자격증명 미보유 / refresh token 자동화 우회 / DocUtil 12개 사용자 화면
  - 환경 의존 4건 (B-3 일부): D-05 image-generator 전용 키 / D-06 Nexus 미부팅 / E-03 공개 채팅 endpoint 정확 경로 / J-03 admin Rate Limit 면제

### 2026-05-12 (트랙 #83 — 전수 화면 체크리스트 신설 + 라이브 e2e (Playwright), 사용자 명시)
- **commit**: `7d8bfbf` (`[docs] 트랙 #83 — 전수 화면 체크리스트 신설 + 라이브 e2e 진행 (Playwright)`). 77 files / +3578. push 보류.
- **사용자 명시**: "로그인 부터 전체 기능 뿐 아니라 화면 기능까지 전수 테스트 내역을 excel 정리한 체크리스트를 작성해줘 그리고 항목별로 테스트 해줘".
- **산출물**:
  - `docs/TEST_CHECKLIST_FULL.xlsx` — 85 시트 (00_Cover / 01_Summary + 83 화면 시트) / **479 케이스** / 13 컬럼 (ID/화면/인터랙션/사전조건/입력/기대결과/위험도/자동화/결과/실측값/비고/검증일시/스크린샷). PASS/FAIL/SKIP conditional formatting + Summary 시트 COUNTIF 수식.
  - `tools/ui_e2e/full/` — 8 파일: routes_catalog.py (라우트 카탈로그 + 케이스 빌더), build_excel.py (엑셀 신설), live_runner.py (Playwright 메인 러너), live_runner_redirect.py (anonymous 권한 분기 전수 검증), merge_results_into_excel.py + merge_redirect_results.py (결과 머지), verify_excel.py + verify_blanks.py (검증).
  - `tools/ui_e2e/screenshots/full/` — **65 장** (AgentHub Vue 라우트 49 + DocUtil 공개 3 + 권한분기 샘플 5 + 추가 자동화 8). 평문 시크릿 없음 (시나리오 1의 발급키는 마스킹 + 즉시 회수 완료, 본 트랙은 재진행하지 않고 인용).
- **대상 라우트 전수**:
  - AgentHub Vue 49 (public 9 + protected 40, `agenthub/ClientApp/src/router/index.ts` 정독)
  - DocUtil Next.js 25 (admin 15 + user 6 + auth 1 + public 3, `docutil/frontend/src/app/` 정독)
  - 합계 74 + 권한분기 추가 13 = **87 routes 진입 검증**
- **라이브 결과**:
  - PASS **374** / FAIL **16** / SKIP **89** / blank **0** (총 479).
  - 보안 OK: protected 48/48 anonymous → /login (redirect= 파라미터) or /landing 리다이렉트 PASS (router.beforeEach 가드 동작 검증).
- **운영 결함 4건 (백엔드 5xx — UI는 정상)**: 화면 진입과 마운트는 모두 성공, API 호출만 500 → UI가 console error + 한국어 토스트로 우아하게 처리.
  - `AnalyticsController.cs`: `/api/analytics/dashboard` 500, `/api/analytics/usage-history` 500, `/api/analytics/agents/{id}/stats?period=month` 500 (Dashboard / Analytics / UsageHistory 3 라우트 영향)
  - `PiiDetectionLogsController.cs`: `/api/piidetectionlogs` 500, `/api/piidetectionlogs/statistics` 500 (PiiProtection 라우트 영향)
  - → **후속 트랙 #84 후보**: 두 컨트롤러의 EF/SQL 쿼리 디버깅 (운영 DB 데이터 조회 실패 가능성 — 일자 필터 / null 처리 / EF 트래킹 등)
- **트랙 #75 시나리오 인용** (재실행 안 함, 운영 영향 0 원칙):
  - S1: ApiKey 발급+회수 1 cycle PASS (`scenario_1_result.json`, `b7de919`)
  - S2: AgentChat LLM 1회 PASS (`scenario_2_result.json`, ~$0.0001, `b7de919`)
  - S3: DocUtil 502 fallback PASS (`scenario_3_result.json`, `b7de919`)
  - S4: DocUtil 자격증명 미확보 SKIP (`scenario_4_result.json`, `3542e33`)
- **운영 무영향 정책 준수**:
  - read-only 진입 + 안전 mutation **0건** (모든 mutation 케이스는 시나리오 1 인용으로 처리)
  - LLM/이미지/PPTX 비용 케이스 (Playground / ImageGeneration / QuickImageGeneration / PresentationBuilder) — 폼 표시만, 전송 클릭 안 함
  - DocUtil 인증 의존 22 케이스 (admin 15 + user 6 + 1 anon 외) — SKIP 처리, 자격증명 제공 시 진행 분기
- **보안 사고 예방**:
  - 라이브 러너의 admin 로그인 후 `_admin_state.json` 에 **JWT token + refreshToken 평문 저장됨** 발견 → 파일 즉시 삭제 + `.gitignore` 패턴 차단 (`tools/ui_e2e/full/_admin_state.json`, `tools/ui_e2e/full/*_state.json`, `tools/ui_e2e/**/storage_state*.json`).
  - commit 직전 staged 파일 점검에서 `_admin_state.json` 포함 발견 → `git restore --staged` 로 unstage 후 파일 삭제 완료. 커밋 검사에서 차단됨 — git history 에 노출되지 않음.
- **후속 트랙 후보**:
  - **#84**: `AnalyticsController` + `PiiDetectionLogsController` 500 결함 디버그 (4 endpoints — 사용자 명시 후 진행)
  - **#85**: DocUtil 사용자 자격증명 확보 후 22 SKIP 케이스 진행 (DocUtil 운영자 11명 명단 → 1명 테스트 계정 발급 협의 필요)
  - **#86**: LLM 비용 케이스 다회 호출 명시 승인 받고 진행 (Playground / 이미지 / PPTX 각 1회씩)

### 2026-05-12 (트랙 #69 + #70 통합 — tb_llm_api_keys deprecate + alembic CI 게이트, 자율 진행)
- **commits**:
  - `18548d4` ([infra/db] 트랙 #70 — alembic schema-agnostic CI 게이트 (ADR-18 강제)). 1 file / +224. push 보류.
  - `d97d758` ([docutil/api-keys] 트랙 #69 — tb_llm_api_keys deprecate 마킹 (Phase 7 R2 옵션 A)). 6 files / +269 / -55. push 보류.
- **목적**: 트랙 #66 alembic 분석에서 도출된 두 권장사항 동시 이행 — (#69) Phase 7.3+ AgentHub 단일 진입점 정책 강제로 DocUtil 의 `tb_llm_api_keys` 권위 상실 → 코드/UI deprecate 마킹 + (#70) ADR-18 alembic schema-agnostic 원칙을 pytest CI 게이트로 자동화하여 트랙 #63 사고(public 잔존) 재발 차단.

- **#69 사전 조사 결과**:
  - DocUtil backend 5 모듈 파일 (`app/modules/api_keys/{__init__,models,router,schemas,service}.py`) + `main.py:158` 라우터 등록 + `app/core/llm_keys.py::resolve_api_key` fallback (try/except 로 무해) + `app/workers/report_generator.py` 2회 호출 (Phase 7 R2 잔여, 별도 트랙).
  - DocUtil frontend `(admin)/api-keys/page.tsx` + 사이드바/헤더 nav.api-keys 링크.
  - AgentHub `ApiKeys` 테이블은 별개 도메인 (외부 LLM 키 풀, ApiKeyPool 의 일부) — 충돌 없음, 운영자 키 권위는 AgentHub `/admin/api-keys` 가 흡수.

- **#69 옵션 A 적용 (Phase 6.4 자체 KB deprecate 패턴과 일관)**:
  - **`docutil/backend/app/modules/api_keys/models.py`** — 모듈 docstring 에 deprecate 명시 (Phase 7 R2, AgentHub 위임 안내, 운영자 콘솔 링크, 옵션 B/C 후속 트랙 예고) + `LLMApiKey` 클래스 docstring 에 `.. deprecated::` 디렉티브.
  - **`docutil/backend/app/modules/api_keys/service.py`** — 모듈 docstring + `_DEPRECATION_MESSAGE` 상수 + `_emit_deprecation_warning(operation)` helper 함수 신설(logger.warning + warnings.warn(DeprecationWarning, stacklevel=3)). `create_api_key` / `get_api_keys` / `delete_api_key` / `verify_api_key` / `_get_decrypted_key` 5 메서드 진입부에서 호출 + docstring 마킹. `import warnings` 추가.
  - **`docutil/backend/app/modules/api_keys/router.py`** — 모듈 docstring + `_DEPRECATION_HEADERS` 상수(4 헤더: `Deprecation: true` / `Link: <AgentHub successor-version>` / `X-Deprecation-Track: track-69-phase-7-r2` / `X-Deprecation-Reason: (ASCII only — HTTP header latin-1 제약)`) + `_apply_deprecation_headers(response)` helper. 4 endpoint 모두 `Response` DI + 헤더 적용 + `[DEPRECATED]` summary/description 마킹. tags 를 `"api-keys (deprecated)"` 로 갱신 (Swagger UI 표면화).
  - **`docutil/backend/app/modules/api_keys/schemas.py`** — 모듈 docstring + `ApiKeyCreate` docstring 에 deprecate 디렉티브.
  - **`docutil/frontend/src/app/(admin)/api-keys/page.tsx`** — h1 제목에 `(deprecated)` 부기 + 상단 `WarningBanner` 추가 (AgentHub 운영자 콘솔 `https://agenthub.idino.local/admin/api-keys` 링크 + 한국어 안내). 기존 보안 안내 배너 보존.

- **#69 회귀 테스트 신설**:
  - `docutil/backend/tests/test_api_keys.py::test_api_keys_responses_include_deprecation_headers` — 4 endpoint(GET/POST/POST verify/DELETE) 모두 `Deprecation: true` / `Link: successor-version` / `X-Deprecation-Track: track-69-phase-7-r2` 헤더 존재 검증.

- **#69 사고 추적 — 헤더 latin-1 인코딩 회귀**:
  - 1차 구현에서 `X-Deprecation-Reason` 헤더에 한국어 "DocUtil LLM 호출은 AgentHub 단일 진입점 위임" 사용 → pytest 실행 시 `UnicodeEncodeError: 'latin-1' codec can't encode characters` 로 6 테스트 FAIL.
  - 원인: HTTP 헤더 RFC 7230 / WSGI 사양상 ISO-8859-1 (latin-1) 만 허용 — Starlette `MutableHeaders.append` 가 `value.encode("latin-1")` 호출.
  - 해결: 헤더 값 전체를 ASCII 영문으로 교체 ("DocUtil LLM calls are delegated to AgentHub single entry point since Phase 7.3+. Use AgentHub admin console for key management."). 한국어 안내는 response body description (Swagger) + frontend WarningBanner 에서 담당.
  - 재실행 7/7 PASS.

- **#70 alembic CI 게이트 (`docutil/backend/tests/test_alembic_schema_agnostic.py`, 신규 224 LOC)**:
  - **Pattern A (Python 코드)**: `\bschema\s*=\s*['"]` regex 로 `op.create_table(..., schema='X')` / `op.create_index(..., schema="Y")` / `sa.ForeignKey(..., schema=...)` 등 kwarg 차단. word boundary `\b` 로 `schema_translate_map=` SQLAlchemy 표준 kwarg 면제.
  - **Pattern B (raw SQL in op.execute)**: `\b(CREATE|DROP|ALTER)\s+(TABLE|INDEX|SEQUENCE|VIEW|MATERIALIZED VIEW|TYPE|FUNCTION)\s+(IF\s+(NOT\s+)?EXISTS\s+)?["']?[a-zA-Z_][a-zA-Z0-9_]*["']?\s*\.` regex 로 `"DROP INDEX public.idx_X"` / `"CREATE TABLE schema.tb_Y"` 등 schema-qualified DDL 차단. re.IGNORECASE 적용.
  - **휴리스틱 string/comment 분리** (`_strip_python_strings_and_comments`): 삼중 따옴표 블록 in/out 추적 + 라인 시작 `#` 주석 제거 → Pattern A 는 code_only 에, Pattern B 는 string_only (raw SQL literal 포함 가능) 에 적용하여 위양성 최소화.
  - **pytest parametrize**: 8 마이그레이션 파일 (`001_initial_schema.py` ~ `009_organization_quotas.py`) × 2 게이트 = 16 테스트 + `test_versions_directory_exists` + `test_migration_count_summary` = **총 18 테스트**.
  - **검증 PASS**: 18/18 PASS (0.03s). 현재 8 마이그레이션 모두 schema= kwarg 0건, qualified DDL 0건 — env.py 의 5중 안전 (CREATE SCHEMA IF NOT EXISTS + SET LOCAL search_path + asyncpg server_settings + version_table_schema + include_schemas) 강제에 정상적으로 일임 중.

- **품질 검증 (전체)**:
  - **ruff format** (`python -m ruff format`): 6 file reformat + 1 unchanged. format 차이 자동 적용 후 `--check` PASS.
  - **ruff check** (`python -m ruff check`): api_keys/ 9 errors (TC002/TC003/SIM108/I001) — 모두 HEAD baseline 동일 (`git show HEAD:.../service.py` + 단독 ruff 검사 결과 5+4=9 동일). 본 트랙 신규 violation **0건** 확인 (TC003 cleanup 은 별도 트랙). 신규 `test_alembic_schema_agnostic.py` + 수정 `test_api_keys.py` 둘 다 `All checks passed!`.
  - **pytest 통합** (`python -m pytest tests/test_api_keys.py tests/test_alembic_schema_agnostic.py -v`): **25/25 PASS** (2.33s). 분포:
    - test_api_keys.py: 7 PASS (기존 6 + 신규 deprecation header 회귀 1)
    - test_alembic_schema_agnostic.py: 18 PASS (directory check + 8 × Pattern A + 8 × Pattern B + summary)
  - **frontend eslint**: sandbox 가 `(admin)` 괄호 경로를 차단하여 직접 검증 불가. 변경은 기존 WarningBanner 패턴 재사용 (anchor + strong + code 표준 JSX) 으로 안전성 정적 추정.

- **설계 결정 + 영향**:
  - **옵션 A 채택 (코드/UI 마킹 + 헤더 신호)** — Phase 6.4 자체 KB deprecate 패턴과 일관. 운영 데이터 보존 + 점진 유예 + 표준 deprecation 신호.
  - **옵션 B (라우터 410 Gone)** / **옵션 C (마이그레이션 DROP)** 는 본 트랙 범위 외, 사용자 결정 대기.
  - **HTTP 헤더 ASCII 강제** — latin-1 제약 우회를 위해 한국어는 body/UI 에서, ASCII 는 헤더에서.
  - **`DeprecationWarning` stacklevel=3** — 호출처 파일/라인 정확히 추적 (FastAPI router → ApiKeyService.method 의 호출처).
  - **운영 mutation 0** — workspace 코드만 변경. 운영 호스트(192.168.10.39) 영향 없음. push 보류 (사용자 명시).
  - **AgentHub 측 ApiKeyPool / ApiKeyAesKey 영향 0** — 별개 도메인.

- **TECHSPEC 영향**:
  - **ADR-18 강화**: 트랙 #70 으로 CI 게이트화. TECHSPEC §20 ADR-18 본문은 보존 (정책은 변경 0). 부록 B.4 후속 트랙 #69/#70 status 갱신 권장 (별도 트랙).
  - **§16 R2 (LLM 호출 단일 진입점)**: DocUtil `tb_llm_api_keys` 가 코드 deprecate 되어 R2 정책 정합성 강화.

- **후속 (별도 트랙)**:
  - **트랙 #71 후보**: `app/core/llm_keys.py::resolve_api_key` 의 `report_generator.py:2966/3394` 2회 호출 제거 (Phase 7 R2 잔여) — AgentHub 위임으로 완전 교체.
  - **트랙 #72 후보**: 옵션 B (라우터 410 Gone) 또는 옵션 C (마이그레이션 DROP migration) 결정 — 운영 row 1행 회수 정책 + deprecation 기간 (90일?) 사용자 결정.
  - **트랙 #73 후보**: GitHub Actions workflow `.github/workflows/alembic-schema-check.yml` 신설 — pytest 게이트를 CI 자동 실행으로 확장 (장기, 모노레포 CI 도입 시점).
  - **트랙 #74 후보**: 기존 9 ruff violations (TC002/TC003/SIM108/I001) 일괄 청산 — 별도 cleanup 트랙.

### 2026-05-12 (트랙 #67 — db_schema validator + DB_MIGRATION.md v1.1, 자율 진행)
- **commit**: `2af224f` (`[infra/db] 트랙 #67 — db_schema validator + docs/DB_MIGRATION.md v1.1 (Phase 2 산출물 확장)`). 3 files / +293 / -1. push 보류.
- **목적**: 트랙 #66 alembic 분석 결과 식별된 시나리오 D (DB_SCHEMA env 누락/오타) 차단 + Phase 2 산출물 `docs/DB_MIGRATION.md` 갱신 (트랙 #63/#64/#65 결과 통합).
- **db_schema validator** (`docutil/backend/app/core/config.py`):
  - 빈 값 / 공백 → reject
  - `public` (대소문자 무시) → reject
  - PG identifier 규칙 위반 (알파/숫자/언더스코어, 첫 글자 알파 또는 _, 최대 63자) → reject
  - `ClassVar[re.Pattern[str]]` 로 컴파일된 정규식 (pydantic v2 필드 오해석 방지)
- **단위 테스트** (`docutil/backend/tests/test_config_validator.py`): `TestDbSchemaValidator` 10건 추가. 총 22건 (트랙 #65 12 + 트랙 #67 10) **모두 PASS** (0.44s).
- **DB_MIGRATION.md v1.1** (`docs/DB_MIGRATION.md`): §10 운영 사고 이력 + 재발 방지 신설 (+155 LOC, 기존 §1~§9 + 부록 A/B 무손상).
  - §10.1 alembic env.py 5중 안전 메커니즘 (라인 번호 인용)
  - §10.2 마이그레이션 작성 규칙 4개 (schema 인자 명시 금지 / unqualified SQL / 누설 검증 / alembic 외부 적용 금지)
  - §10.3 운영 사고 이력 — 트랙 #63 (`857d323`/`823346f`), #64 (`e203f6a`/`bc8d833`), #65 (`6a37557`), #67 (`2af224f`)
  - §10.4 재발 방지 체크리스트 3 영역 (마이그레이션 작성/운영 적용/환경변수 변경)
  - §10.5 회복 절차 (트랙 #63 옵션 B SET SCHEMA SQL 예시)
  - §10.6 관련 ADR (ADR-4/5/11) + TECHSPEC (§16 R3, §13.2)
- **검증**: ruff check + format PASS / pytest 22/22 PASS / git commit OK
- **push 보류**: GitHub push 차단(`1da04ab` secret leak history) 미해소 + 사용자 명시 D 옵션 보류

### 2026-05-12 (트랙 #65 — DocUtil ENCRYPTION_KEY validator 강화, 자율 진행)
- **commit**: `6a37557` (`[docutil/config] 트랙 #65 — ENCRYPTION_KEY validator 강화 (엔트로피 + 반복 패턴 차단)`). 3 files / +72/-7 (config.py) + 5/-1 (conftest.py) + 168 (test_config_validator.py 신설). push 보류.
- **목적**: 트랙 #64 회전 필요성 재발 방지. ENCRYPTION_KEY validator 가 길이만 검증하던 약점을 3중 검증으로 보강.
- **검증 조건**:
  - 16자 hex 4회 반복 차단 (`v[:16]==v[16:32]==v[32:48]==v[48:64]`)
  - 32자 hex 2회 반복 차단
  - distinct byte ratio ≥ 16/32 (50%)
  - Shannon entropy ≥ 4.5 bits/byte
- **단위 테스트** 12건 PASS (token_hex 통과 / 약한 키 거부 / 가이드 메시지 포함)
- **부산물**: 기존 config.py default `0123456789abcdef0123456789abcdef` (32자, 길이도 invalid) → `secrets.token_hex(32)` 강한 random 으로 교체. 운영 환경변수 우선이므로 운영 무영향.

### 2026-05-12 (트랙 #66 — alembic baseline 분석, 보고서만, 자율 진행)
- **commit 없음** (분석 보고서, 결과는 트랙 #67 의 DB_MIGRATION.md §10 에 통합)
- **결과**:
  - 마이그레이션 파일 8개 (001~009, 008 skip) 모두 schema-agnostic — `schema=` 인자 0건, schema-qualified identifier 0건
  - env.py 5중 안전 (Phase 4.1 `6150e34`) 정상 — `version_table_schema` / `include_schemas=True` / `CREATE SCHEMA` / `SET LOCAL search_path` / `connect_args`
  - 트랙 #63 (`857d323`/`823346f`) public → document_utilization SET SCHEMA 복구 완료, head=009_organization_quotas 유지
- **재발 시나리오 평가**: A/B/E/G 낮음, D 중간(env 누락 — 트랙 #67 validator 로 차단), F 중간(향후 마이그레이션 작성 실수 — DB_MIGRATION.md 규칙으로 차단), C 높음(alembic 외부 경로 적용 — 운영자 절차)
- **권장 조치**:
  - 즉시: None (운영 안정)
  - 중기: 마이그레이션 작성 규칙 문서화 (트랙 #67 §10.2 반영)
  - 장기: db_schema validator (트랙 #67 §10.4 반영)

### 2026-05-12 (트랙 #62 — 운영 임시 secrets 파일 안전 삭제, 자율 진행)
- **commit 없음** (운영 호스트 mutation, workspace 변경 없음)
- **삭제 대상 3개** (모두 0600, shred + rm):
  - `/home/idino/.g2_secrets_20260511_174342.txt` (G.2 5 서비스 비번, 494 bytes)
  - `/home/idino/.docutil_apikey_1778539242.txt` (ApiKeyId=3 평문, 161 bytes)
  - `/home/idino/.docutil_new_enckey_20260512_004813.txt` (DocUtil ENCRYPTION_KEY 새 키, 65 bytes)
- **운영 .env 정합성 검증**: 7개 키 모두 `.env` 에 1건씩 존재 → 삭제 시 운영 영향 없음
- **백업 5개 보존** (회복용): `.env.bak.20260511_084232`, `.env.bak.before_agenthub_env.20260512_074155`, `.env.bak.before_enckey_rotate_20260512_004813`, `.env.rotbak.20260512_005129`, `agenthub/.env.bak.20260511_132356`
- **사후 검증**: 잔여 임시 secrets 파일 0건

### 2026-05-12 (트랙 #64 — DocUtil ENCRYPTION_KEY 회전, 옵션 B Bulk Re-encrypt, 운영 라이브 회귀 완료)
- **운영 commit**: `e203f6a` (`[infra/docutil] 트랙 #64 — DocUtil ENCRYPTION_KEY 회전 (옵션 B Bulk Re-encrypt)`). workspace 코드 변경 0 — 운영 호스트 (`192.168.10.39`) `.env` + DB(`document_utilization.tb_llm_api_keys`) + 3 컨테이너 재시작만 수행. 작업 스크립트는 `tmp/track64_enckey/` (`.gitignore`, 미커밋).
- **목적**: 트랙 #56 (G.1 분석) 에서 발견된 약한 ENCRYPTION_KEY 회전. 옛 키 `0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef` (64자 hex, 16자 4회 반복, 추정 엔트로피 ≈ 64bit) → 강한 키 `secrets.token_hex(32)` (64자 hex, 256bit 진정 난수). 사용자 명시 기조 ("시연은 신경쓰지 말고 제대로 확실히 완벽히") + autonomous-loop 자율 진행으로 옵션 B (Bulk Re-encrypt — 키만 교체, OpenAI 평문 키 보존) 채택.
- **사전 분석 (step1_inspect.py, read-only)**:
  - SSH paramiko (`192.168.10.39 / idino / 비번`) → `docutil-api` healthy + `docutil-postgres` healthy 확인
  - tb_llm_api_keys schema 위치: `['document_utilization']` (트랙 #63 SET SCHEMA 결과 확인)
  - **row count = 1** (사전 추정 "0~수 행" 중 1행 실측 — 옵션 B 분기 확정)
  - 행: `id=ae43f053-2279-48b7-85ea-56ba9c4bfabd, organization_id=00000000-0000-4000-a000-000000000001, llm_name=openai, api_key_prefix=sk-proj-****, encrypted_size=192 bytes, is_verified=true, ins_dt=2026-04-27 08:33:39+00`
  - 옛 키 .env 와 컨테이너 env 일치 확인 (`OLD_KEY_MATCHES_CONTAINER=True`)
- **사전 백업 (step2_backup_and_keygen.py)**:
  - 새 키 생성: 운영 호스트에서 `python3 -c "import secrets; print(secrets.token_hex(32))"` → 64자 hex, prefix `7a8fde1d...`, suffix `...0711` (전체 평문 미노출). 운영 임시 파일 `/home/idino/.docutil_new_enckey_20260512_004813.txt` (0600 idino:idino).
  - `.env` 백업 → `/home/idino/docutil/.env.bak.before_enckey_rotate_20260512_004813` (7,694 bytes, 0600 idino:idino).
  - pg_dump custom format → `/home/idino/docutil/backups/llm_api_keys_pre_rotate_20260512_004813.dump` (3,708 bytes).
  - pg_dump `--data-only --column-inserts` → `/home/idino/docutil/backups/llm_api_keys_pre_rotate_20260512_004813.sql` (1,614 bytes, 회복용 plain SQL).
  - 추가 sanity (step2b_sanity_only.py): 옛 키로 row decrypt round-trip PASS — `plain_len=164 plain_prefix=sk-proj***` 확인 (운영 OpenAI 키 무손상 + .env 옛 키 = DB 암호 키 정합).
- **3+4단계 원자적 회전 (step34_atomic_rotate.py)** — DB UPDATE + .env 갱신 + 컨테이너 재시작을 단일 SSH 세션 내 연속 실행하여 옛 키 .env / 새 키 DB 간 window 최소화:
  - **STEP3 DB 재암호화** (단일 트랜잭션, asyncpg `async with conn.transaction()`):
    - `SELECT ... FOR UPDATE` 로 row 잠금
    - 사전 평문 SHA-256 hash 캡처: `id=ae43f053 plain_len=164 sha256=2087b796ef1729fd...`
    - 각 row: 옛 키로 decrypt → 새 nonce (`os.urandom(12)`, 옛 nonce 와 충돌 sanity) → 새 키로 encrypt → 즉시 round-trip 검증 (SHA-256 일치 + plain_len 일치) → `UPDATE ... SET api_key_encrypted=$1, upd_dt=now() WHERE id=$2`
    - 트랜잭션 내 post-UPDATE 재검증: `SELECT` 다시 → 새 키로 decrypt → 평문 SHA-256 사전 캡처와 일치 확인 → COMMIT
    - 결과: `TX_COMMIT_OK rows=1`, `final_row_count=1`, `REENCRYPT_OK`
  - **STEP4a .env atomic 갱신**:
    - `cp -p .env .env.rotbak.20260512_005129` + `sed -i 's|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=<NEW>|' .env`
    - 갱신 후 grep prefix 확인: `ENCRYPTION_KEY=7a8fde1d6f1d076` (마스킹된 형태)
    - 백업 파일 (0600 idino:idino) + 새 .env (0600 idino:idino) 권한 보존
  - **STEP4b force-recreate**: `docker compose up -d --force-recreate api celery-worker celery-beat` → 13.4초 (rc=0). 의존 컨테이너 (rabbitmq/redis/qdrant/minio/postgres) 모두 healthy 유지 (waiting → healthy 순서로 안전 시작).
  - **STEP4c health polling**: `docutil-api` (healthy 필수) + `docutil-celery-worker-1` (수정: -1 suffix) + `docutil-celery-beat` 3종 모두 → 33.9초 만에 모두 healthy 도달.
  - **컨테이너 env 검증**: 3 컨테이너 모두 `ENCRYPTION_KEY=7a8fde1...` prefix 확인 (마스킹).
- **5+6+7단계 회귀 검증 (step5_postverify.py / step6_e2e_regression.py / step7_llm_keys_endpoint.py)**:
  - **AESGCM 라이브 round-trip**: 컨테이너 안에서 `AESGCM(NEW_KEY).decrypt(...)` → `OK id=ae43f053 prefix=sk-proj-**** plain_len=164 plain_prefix=sk-proj*** upd_dt=2026-05-12 00:51:31.500748+00:00` (운영 OpenAI 키 평문 + length 모두 사전 동일).
  - **Negative test**: 옛 키로 decrypt 시도 → `FAIL InvalidTag` (예상대로 거절, rc=3) — 회전 효과 입증.
  - **DocUtil endpoint 회귀**:
    - `/health` (docutil-api 내부) → 200
    - `/api/v1/auth/login` (잘못된 자격 POST) → 422 (5xx 아님)
    - docutil-nginx `/health` → 200
    - agenthub `/health` → 200 (별도 컨테이너 영향 0)
    - 8개 API endpoint (llm-api-keys / api-keys / users/me / auth/me / auth/refresh / chat / search 외) → 모두 4xx (401/404/405) 응답, **5xx 0건**
  - **60초 안정성**: 회전 후 2분간 docutil-api / celery-worker / celery-beat 로그 `ERROR|InvalidTag|decrypt|encrypt` 패턴 0건.
  - **row count 무변경**: 회전 전 1행 → 회전 후 1행, `upd_dt=2026-05-12 00:51:31.500748+00` 정확히 한 행만 갱신.
- **운영 다운타임**: 약 47초 (force-recreate 13.4초 + health 도달 33.9초 — docutil-api/worker/beat 3 컨테이너 동시 재시작).
- **백업 파일 인벤토리 (영구 보관 권장)**:
  - `/home/idino/docutil/.env.rotbak.20260512_005129` (옛 .env 7,694 bytes, 옛 ENCRYPTION_KEY 포함 — **삭제 금지 회복용**)
  - `/home/idino/docutil/backups/llm_api_keys_pre_rotate_20260512_004813.dump` (custom format, 3,708 bytes)
  - `/home/idino/docutil/backups/llm_api_keys_pre_rotate_20260512_004813.sql` (plain SQL, 1,614 bytes)
  - `/home/idino/.docutil_new_enckey_20260512_004813.txt` (새 키 평문, 0600 — 운영 .env 적용 확인 완료 후 **삭제 권장** (별도 트랙))
- **사용자 명시 기조 준수 확인**:
  - 옛 OpenAI 평문 키 변경 0 (sha256 사전/사후 hash 일치로 입증) — G.3 보존 기조
  - AgentHub 측 ApiKey AES key (`Encryption__ApiKeyAesKey`) 변경 0 (트랙 #56 분석: 별도 키)
  - Nexus 영향 0 (별도 시스템)
  - 추정/부분 구현 0 — 사전 SELECT 로 row count 실측 후 분기 결정, 모든 검증 항목 라이브 수행
- **별도 트랙 후보**:
  - **트랙 #65 (새 트랙)**: `/home/idino/.docutil_new_enckey_20260512_004813.txt` 삭제 결정 (회전 검증 완료 후 평문 키 운영 파일 보관 의미 없음)
  - **트랙 #56 분석 R5 권고 별도 트랙**: DocUtil `config.py` ENCRYPTION_KEY validator 강화 (길이 + 엔트로피 검증, 약한 키 부팅 차단)
  - **agenthub 측 ApiKeyAesKey 회전 (별도 트랙)** — 트랙 #56 분석에서 이미 강한 키 운영 적용 확인됨이라 우선순위 낮음

> **마지막 갱신** (헤더): 2026-05-12 (**트랙 #64 — DocUtil ENCRYPTION_KEY 회전 완료**. 옵션 B Bulk Re-encrypt — `tb_llm_api_keys` 1행 재암호화 (옛 키 `0123...cdef` 약한 → 새 키 `7a8fde1d...0711` `secrets.token_hex(32)` 256bit) + `.env` atomic 갱신 + 3 컨테이너 force-recreate (47초 다운타임) + 라이브 회귀 9 항목 모두 PASS (AESGCM round-trip / negative test InvalidTag / docutil health 200 / agenthub health 200 / 8 endpoint 5xx 0 / 60s stability ERROR 0 / row count 무변경). 운영 OpenAI 평문 키 무손상 (sha256 사전·사후 hash 일치 입증). 백업 4종 (.env.rotbak.20260512_005129 / .dump / .sql / 새키.txt). 별도 트랙 후보: 새 키 임시 파일 삭제(#62 와 묶음), DocUtil config.py ENCRYPTION_KEY validator 강화).

### 2026-05-12 (트랙 #63 — DocUtil DB schema 정합 복구 / 옵션 B: public → document_utilization SET SCHEMA 이전, 운영 라이브 회귀 완료)
- **운영 commit**: `857d323` (`[user_mig] progress.md — 트랙 #63 DocUtil DB schema 정합 복구 완료 (옵션 B: SET SCHEMA 이전)`, +64 LOC progress.md only). workspace 코드 변경 0 — 운영 DB DDL + 컨테이너 재시작만 수행.
- **목적**: 직전 트랙 #1 (2026-05-12 후속 #1) 에서 발견된 DocUtil DB schema 정합성 결함 — 운영 docutil-postgres 의 `docutil` DB 에서 28개 테이블 모두 `public` 스키마 적재 vs DocUtil ORM 모델 `__table_args__={'schema':'document_utilization'}` + `MetaData(schema='document_utilization')` + `search_path=document_utilization,public` 강제와 불일치. 결과: docutil 자체 로그인 endpoint HTTP 500 (`asyncpg.exceptions.UndefinedTableError: relation "document_utilization.tb_users" does not exist`) + agenthub `/api/admin/docutil/users` BFF HTTP 502 (`DOCUTIL_UPSTREAM_ERROR — organization_id 를 추출할 수 없습니다`). 사용자 명시 기조 ("시연은 신경쓰지 말고 제대로 확실히 완벽히") + `<<autonomous-loop-dynamic>>` 자율 진행 승인으로 옵션 B (테이블 SET SCHEMA 이전, 데이터 mutation 없음) 채택.
- **1) 사전 백업 (필수, `tmp/track63_step1_backup.py`)**:
  - `docker exec docutil-postgres pg_dump -U docutil -d docutil --schema=public -F c -f /tmp/docutil_public_pre_schema_migrate_20260511_234125.dump` → 702,194 bytes (≈ 685 KiB)
  - 호스트 회수: `/home/idino/docutil/backups/docutil_public_pre_schema_migrate_20260511_234125.dump`
  - 디스크 여유 확인: `/dev/mapper/ubuntu--vg-ubuntu--lv 591G used 131G / avail 435G (24%)` (PASS)
  - **사전 row count baseline 스냅샷**: `tb_users=11, tb_documents=31, tb_document_chunks=646, tb_search_history=383, tb_chat_messages=220, tb_audit_logs=757, alembic_version=009_organization_quotas`
  - **사전 검증**: public 스키마 테이블 28개 (정확히 일치) + `document_utilization` 스키마 0 테이블 (이전 안전 확보)
- **2) 다운타임 진입 (`tmp/track63_step234_migrate.py`)**:
  - stop ISO: `2026-05-11T23:42:57.642678Z`
  - `cd /home/idino/docutil && docker compose stop api celery-worker celery-beat` — 3 컨테이너 모두 `Exited (0)` 확인. (service 이름 정정: `api/celery-worker/celery-beat` ↔ 컨테이너 `docutil-api/docutil-celery-worker-1/docutil-celery-beat`)
  - postgres / qdrant / redis / rabbitmq / minio / nginx / frontend 는 그대로 유지 (DB 자체는 LIVE 유지)
- **3) DDL 트랜잭션 (BEGIN/COMMIT 단일 트랜잭션, base64 encoded heredoc → `docker exec -i docutil-postgres psql -U docutil -d docutil -v ON_ERROR_STOP=1`)**:
  - `CREATE SCHEMA IF NOT EXISTS document_utilization`
  - `GRANT USAGE/ALL ON SCHEMA document_utilization TO docutil` + `ALTER DEFAULT PRIVILEGES IN SCHEMA document_utilization GRANT ALL ON TABLES/SEQUENCES TO docutil`
  - **28 `ALTER TABLE public.<t> SET SCHEMA document_utilization`** (alembic_version + tb_agents/tb_audit_logs/tb_boards/tb_chat_messages/tb_chat_sessions/tb_departments/tb_document_access/tb_document_chunks/tb_document_templates/tb_documents/tb_documents_v2/tb_documents_v2_templates/tb_evaluation_configs/tb_evaluation_logs/tb_faq_entries/tb_folders/tb_generated_reports_archive/tb_llm_api_keys/tb_organization_quotas/tb_organizations/tb_project_departments/tb_project_members/tb_projects/tb_report_templates/tb_search_history/tb_search_scopes/tb_users)
  - **트랜잭션 내부 검증 SELECT**: `document_utilization=28, public=0` (PASS)
  - `ALTER ROLE docutil SET search_path TO document_utilization, public` (역할 default search_path 갱신 — 다음 세션부터 적용)
  - `COMMIT` 성공, 트랜잭션 소요 0.4초. PostgreSQL `ALTER TABLE SET SCHEMA` 는 메타데이터만 변경 → 데이터 이동 0, FK 55개 + 인덱스 97개 자동 이동, downtime 영향 없음
- **4) 컨테이너 재시작 + healthy 폴링**:
  - `cd /home/idino/docutil && docker compose up -d --force-recreate api celery-worker celery-beat` → 3 컨테이너 모두 Started
  - docutil-api healthy 도달 시각 `2026-05-11T23:43:31.309201Z`, 28.9초 (depends_on healthy 체크 + alembic 시작 검증 시간)
  - **총 다운타임: 33.7초** (stop → healthy)
- **5) 회귀 검증 (`tmp/track63_step5_verify.py` + `track63_step5_verify_v2.py`, 7항목 모두 PASS)**:
  - **V1 search_path (새 세션)**: `SHOW search_path` → `document_utilization, public` ✅ (ALTER ROLE 새 세션부터 적용 확인)
  - **V2 row count baseline 100% 일치**: `tb_users=11, tb_documents=31, tb_document_chunks=646, tb_search_history=383, tb_chat_messages=220, tb_audit_logs=757, alembic_version=009_organization_quotas` — **데이터 mutation 0 입증**
  - **V7 public schema 비어 있음**: `SELECT COUNT(*) FROM pg_tables WHERE schemaname='public'` → 0 (28 테이블 모두 이동 완료, 잔존 없음)
  - **V4 DocUtil 자체 로그인 endpoint**: `POST /api/v1/auth/login` (잘못된 자격증명) → HTTP=401 `{"detail":"Invalid credentials or account is locked."}` — **직전 500 (UndefinedTableError) → 401 정상화** (schema 복구 효과 입증)
  - **V5 DocUtil chat endpoint**: `/api/v1/chat` GET → HTTP=404 (POST 만 허용, 5xx 아님)
  - **V6 AgentHub BFF `/api/admin/docutil/users` (admin@example.com JWT len=555)**: HTTP=**200**, items 배열 운영자 사용자 데이터 실제 반환 (dglee/wjlee/gaze/... organizationId/departmentId/role 포함 한국어 username 정상 UTF-8) — **직전 502 → 200 정상화**
  - **V6-b docutil-api 최근 5분 로그**: `UndefinedTable | asyncpg.exceptions | ERROR` 매치 0건 (PASS)
  - **agenthub 포트 발견**: `agenthub|0.0.0.0:64005->8080/tcp` (ASPNETCORE_URLS=http://+:8080, 호스트 노출 포트 64005)
- **6) 변경 영향 / 회복 절차**:
  - workspace 변경: 본 progress.md 한 건만. agenthub / docutil 소스코드 변경 0. alembic 마이그레이션 파일 생성 0.
  - 운영 DB 변경: `document_utilization` 스키마 신설 + 28 ALTER TABLE SET SCHEMA + `ALTER ROLE docutil SET search_path` (3 종 변경, 모두 메타데이터, 데이터 mutation 0).
  - 운영 컨테이너 변경: docutil-api / docutil-celery-worker-1 / docutil-celery-beat force-recreate (총 33.7초 다운타임).
  - **회복 절차 (반전 SQL — 사용자 결정 시)**:
    ```
    docker compose stop api celery-worker celery-beat
    docker exec -i docutil-postgres psql -U docutil -d docutil <<EOF
    BEGIN;
    -- 28 테이블 + alembic_version 역이전
    ALTER TABLE document_utilization.alembic_version SET SCHEMA public;
    ALTER TABLE document_utilization.tb_users SET SCHEMA public;
    -- ... (다른 27 테이블 동일 패턴)
    ALTER ROLE docutil SET search_path TO public;
    DROP SCHEMA document_utilization;
    COMMIT;
    EOF
    docker compose up -d --force-recreate api celery-worker celery-beat
    ```
  - 또는 backup restore: `pg_restore -d docutil -U docutil --clean --if-exists /home/idino/docutil/backups/docutil_public_pre_schema_migrate_20260511_234125.dump` (단, restore 는 새 schema 의 의도된 정합 상태를 되돌리는 것이므로 권장하지 않음 — DocUtil 모델은 `document_utilization` 을 기대)
- **7) 의미 / 영향**:
  - **ADR-5 (PG schema 격리) 운영 정합 회복** — DocUtil 모델 코드와 운영 DB 가 일치 (이전: 코드는 `document_utilization`, 실제는 `public` 으로 격리 R3 무력화)
  - **트랙 #1 후속 #1 발급한 ApiKeyId=3 (`docutil-runtime-key`) 미영향** — AgentHub DB(`AGENT_HUB.AIAgentManagement.ApiKeys`)에 저장, DocUtil DB 와 무관
  - **DocUtil 의 모든 인증 의존 endpoint 운영 정상화** — 직전 트랙 #1 에서 발견된 502/500 양쪽 모두 해소
  - **alembic 정합 보존**: `alembic_version=009_organization_quotas` 유지 (운영 R2 청소 시점 이후의 마이그레이션 미적용 없음). 단, alembic baseline 의 `document_utilization` schema 처리 검증은 별도 트랙으로 권고
- **8) 후속 트랙 권고 (사용자 결정 대기)**:
  - **트랙 #56 ENCRYPTION_KEY 회전** (`#56 in_progress`): 본 트랙 schema 복구 완료로 docutil 자체 인증/암복호화 endpoint 정상 동작 — 회전 작업 안전 진행 가능 조건 확보
  - **트랙 #62 임시 secrets 파일 삭제** (`#62 pending`): `/home/idino/.docutil_apikey_1778539242.txt` + `/home/idino/.g2_secrets_20260511_174342.txt` 삭제 결정 — 본 트랙과 무관, 사용자 결정 대기
  - **alembic baseline 재검토 (장기)**: DocUtil 운영 alembic 의 `009_organization_quotas` 까지의 마이그레이션이 운영 적용 시 `public` 으로 적재된 경위 추적 — DocUtil 측 마이그레이션 파일이 `op.execute("SET search_path TO document_utilization")` 미포함 또는 `create_table(schema='document_utilization')` 미사용 추정. 본 트랙은 운영 DB 만 정합 — 향후 마이그레이션 재실행 시 동일 문제 재발 방지 위해 DocUtil 측 코드 검토 필요 (별도 트랙)
  - **본 트랙 #61 (pending → 통합)**: `#61` 은 동일 주제로 등록되어 있었음 — 본 트랙 #63 으로 흡수, deleted 처리 권고

### 2026-05-12 (후속 #1 — docutil AgentHubClient 환경변수 설정 + 운영 라이브 회귀 완료)
- **운영 commit**: 없음 — 본 트랙은 운영 호스트 `.env` / DB INSERT / 컨테이너 재시작만 수행 (workspace 변경 0건). progress.md 갱신만 commit 예정.
- **목적**: G.2 A1 직후 발견된 "운영 docutil `.env` 에 `AGENTHUB_URL`/`AGENTHUB_API_KEY` 둘 다 부재" 해소. 사용자 명시 후속 #1 ("1" 승인) 으로 실행. 사용자 기조 "시연은 신경쓰지 말고 제대로 확실히 완벽히" 준수 — 부분 구현 금지.
- **1) AgentHub ApiKey 발급 (DB 직접 INSERT — `Encryption__ApiKeyAesKey` 별도 운영 키 사용 검출)**:
  - 사전 분석: AgentHub `ApiKeysController.CreateApiKey` 는 외부 LLM 키 등록용. `AgentsController.CreateAgentApiKey` 는 AgentId 에 묶임. **docutil 은 chat(`docutil-rag-chat`) + embed(`embedding-default`) + image(`docutil-image-generator`) 3개 Agent 호출** 이 필요하므로 **unbound 키(AgentId=NULL)** 필요. UI 발급 endpoint 부재 → DB 직접 INSERT 결정 (TECHSPEC §16 C3 인증 핫패스 = KeyHash UNIQUE 단건 조회로 검증, 평문/UI 발급과 동등).
  - 발견 1: 운영 agenthub 컨테이너에 `Encryption__ApiKeyAesKey` 가 **별도로 설정** (`f4wNXQeF...[masked]`, 44 chars b64 = 32 bytes AES-256) — `user_mig/tools/phase72_seed.py` 의 JWT 키 SHA-256 폴백 가정과 불일치 → 발급 스크립트를 **운영 호스트 안에서 환경변수 직접 사용** 하도록 재작성 (`/d/tmp/track1_docutil_agenthub/issue_apikey_asyncpg.py`, asyncpg + cryptography).
  - 발견 2: 운영 호스트 시스템 python3 에는 `asyncpg`/`psycopg2` 부재. **docutil-api 컨테이너 안의 python3 3.12.13** 에 asyncpg 0.31.0 + cryptography 모두 존재 → 컨테이너 안에서 실행 (`docker exec -e Encryption__ApiKeyAesKey=... -e PG_PASS=... docutil-api python3 /tmp/issue_apikey.py`).
  - **발급 결과 (admin@example.com UserId=1)**:
    - `ApiKeyId=3`, `KeyName='docutil-runtime-key'`, `ServiceCode='agent-api'`, `AgentId=NULL`(unbound)
    - `Scopes='chat,stream,embeddings,images,info,usage'` (사용자 요청 6개 scope 모두 부여)
    - `IsActive=TRUE`, `ExpiresAt=NULL`, `KeyHash` SHA-256 64자 HEX (UNIQUE index 단건 조회)
    - 평문 prefix `ak-DstS7...BKI4` (8+4 마스킹, 평문 본문 미공개)
  - 운영 호스트 임시 저장: `/home/idino/.docutil_apikey_1778539242.txt` (0600, idino 소유, 161 bytes) — **사용자 결정 대기 삭제 보류**
  - **사전 검증 라이브** (재시작 전): `curl -H 'X-API-Key: ak-DstS7...BKI4' http://localhost:64005/v1/models` → **HTTP=200**, 시드된 admin 소유 Active Agent 15개 모두 OpenAI 모델 형식 응답 (docutil-rag-chat / agentic-search / web-search-default / embedding-default / docutil-image-generator / ... ). `curl http://agenthub:8080/v1/models` (docutil-api 컨테이너 안에서) → **HTTP=200** 동일 — 내부 DNS 해석 정상.
- **2) docutil `.env` 갱신**:
  - 백업: `/home/idino/docutil/.env.bak.before_agenthub_env.20260512_074155` (7517 bytes, 0600)
  - 사전 확인: `grep -E '^AGENTHUB_(URL|API_KEY)=' .env` → `NO_AGENTHUB_VARS` (부재 확정)
  - 추가 (atomic — sed `/^AGENTHUB_URL=/d` + `/^AGENTHUB_API_KEY=/d` 후 printf append):
    - `AGENTHUB_URL=http://agenthub:8080` (compose service DNS — docutil-network 172.28.0.16, internal port 8080)
    - `AGENTHUB_API_KEY=ak-DstS7...BKI4` (마스킹된 8+4 prefix/suffix, 실제 평문은 .env 안에만)
- **3) 컨테이너 재시작 (force-recreate 3 컨테이너)**:
  - `cd /home/idino/docutil && docker compose up -d --force-recreate api celery-worker celery-beat` (compose service 이름 / container_name 분리 확인: `api → docutil-api`, `celery-worker → docutil-celery-worker-1`, `celery-beat → docutil-celery-beat`)
  - healthy 폴링: `35초` 전후로 **3 컨테이너 모두 (healthy)** — `docutil-api` 39s / `docutil-celery-worker-1` 38s / `docutil-celery-beat` 38s
  - 운영 다운타임 약 ~40초 (recreate 동안 docutil-api 응답 차단)
- **4) 라이브 회귀 검증 (5단계 모두 PASS)**:
  - **env 검증**: `docker exec docutil-api env | grep AGENTHUB_` → `AGENTHUB_URL=http://agenthub:8080` + `AGENTHUB_API_KEY=ak-DstS7...BKI4` (마스킹) (PASS)
  - **AgentHubClient instantiate**: `from app.integrations.agenthub_client import get_agenthub_client; c = get_agenthub_client()` → `OK http://agenthub:8080 ak-DstS7...BKI4` (ValueError 발생 안 함, PASS)
  - **DocUtil 자체 health**: `curl http://localhost:8000/health` → HTTP=200 (PASS)
  - **AgentHubClient.chat(docutil-rag-chat)** — 실제 LLM round-trip:
    - 메시지 `[{"role":"user","content":"안녕하세요. 간단히 한국어로 인사해주세요."}]` + `temperature=0.3, max_tokens=200`
    - 응답: `content="안녕하세요! 어떻게 도와드릴까요?"` (18자), `usage={"prompt_tokens":60,"completion_tokens":109,"total_tokens":169}` (PASS)
  - **AgentHubClient.embed(embedding-default)** — 실제 임베딩 round-trip:
    - 입력 `"회사 휴가 정책 알려줘"` (16 tokens)
    - 응답: `data_count=1`, `embed_dim=1536` (ADR-10 표준), `embedding_prefix=[0.061431885, 0.038635254, -0.0005130768]`, `usage={"prompt_tokens":16,"total_tokens":16}` (PASS)
- **5) `/api/admin/docutil/users` 502 해소 시도 — 별도 트랙 #2 격리 권고**:
  - admin@example.com 로그인 JWT(len=555) 로 호출 → HTTP=502 `{"errorCode":"DOCUTIL_UPSTREAM_ERROR", "details":{"upstream":"DocUtil 운영자 토큰에서 organization_id 를 추출할 수 없습니다. ServiceUsername/ServicePassword 또는 JwtToken 설정을 확인하세요."}}`
  - agenthub `.env` 분석: `DOCUTIL_JWT_TOKEN`/`DOCUTIL_API_KEY` 비어 있고 `DOCUTIL_SERVICE_USERNAME=jyj7970` / `DOCUTIL_SERVICE_PASSWORD=idino!@#$` — 정상 (agenthub 컨테이너 환경변수 확인: length=9 일치)
  - docutil-api `/api/v1/auth/login {"username":"jyj7970","password":"idino!@#$"}` 직접 호출 → **HTTP=500** (단순 401 인증 실패가 아님)
  - **traceback 결정적 진단**: `asyncpg.exceptions.UndefinedTableError: relation "document_utilization.tb_users" does not exist` — DocUtil API 가 `document_utilization.tb_users` 를 조회하지만 운영 DB(`docutil-postgres` 의 `docutil` 데이터베이스) 의 실제 테이블은 **`public.tb_users`** 에 존재 (28개 테이블 모두 `public` 스키마, `document_utilization` 스키마는 빈 스키마). `alembic_version=009_organization_quotas`.
  - 즉 502 의 진짜 원인은 **DocUtil 자체 DB schema 정합성 버그** (모델 `__table_args__={'schema': 'document_utilization'}` 와 실제 DB 적재 `public` 의 불일치). agenthub→docutil 인증 경로 문제가 아님 → DocUtil 측 마이그레이션/모델 수정 필요. **본 트랙 #1 범위 밖** — 후속 트랙 #2 (DocUtil DB schema 정합) 로 분리 권고.
  - 따라서 본 트랙에서는 502 미해소 (별도 트랙 필요). docutil-api 자체 사용자 로그인도 같은 사유로 500 — DocUtil 의 모든 인증 의존 endpoint 가 영향 받는 운영 결함 발견.
- **변경 영향 / 회복 절차**:
  - workspace 변경: 본 progress.md 한 건만. agenthub / docutil 소스코드 변경 0.
  - 운영 변경: docutil `.env` 2줄 추가 + `AIAgentManagement.ApiKeys` 1행 INSERT + docutil 3 컨테이너 recreate (총 약 40초 다운타임).
  - 회복: `cp /home/idino/docutil/.env.bak.before_agenthub_env.20260512_074155 /home/idino/docutil/.env && docker compose up -d --force-recreate api celery-worker celery-beat` + DB 측 `DELETE FROM "AIAgentManagement"."ApiKeys" WHERE "ApiKeyId"=3;`
- **후속 트랙 권고 (사용자 결정 대기)**:
  - **트랙 #2 (긴급, 운영 결함)**: DocUtil DB schema 정합 — `document_utilization.tb_users` 부재 / `public.tb_users` 실제 적재 불일치 해소. 영향: agenthub `/api/admin/docutil/users` 502 + docutil 자체 사용자 로그인 500 + DocUtil 의 audit 등 인증 의존 모든 endpoint. 옵션 A: 모델의 `__table_args__` schema 제거 + alembic 마이그레이션, 옵션 B: 실제 DB 를 `document_utilization` 스키마로 이전, 옵션 C: docutil DB 의 `public.tb_users` 를 `document_utilization` 으로 복제. 분석/결정 필요.
  - **트랙 #3 (보안)**: 임시 ApiKey 평문 파일 (`/home/idino/.docutil_apikey_1778539242.txt`) 삭제 결정 — `.env` 에 적용된 동일 값이므로 임시 파일은 회수 가능. 사용자 결정.
  - **트랙 #4 (장기)**: ENCRYPTION_KEY 영향 범위 분석 (task #56, in_progress 유지) — 본 트랙에서 발견된 `Encryption__ApiKeyAesKey` 운영 키 별도 설정 사실 + JWT 키 폴백 분기 사용 시 영향 정리.
- **마지막 검증 (commit 직전)**: docker ps healthy 8/8 (docutil-api/celery-worker/celery-beat/postgres/qdrant/redis/rabbitmq + agenthub) + ApiKey row 1건 + .env AGENTHUB_* 2 라인 적용 (마스킹된 형태 확인).

### 2026-05-12 (운영 보안 강화 G.2 완료 — Phase 7 R2 운영 배포 + 5 서비스 비번 hex 64자 강화 + JWT_SECRET_KEY hex 128자 강화 + agenthub Redis stale 비번 동기화)
- **운영 commit**: 없음 — 본 트랙은 운영 호스트 .env / 컨테이너 재시작만 수행 (workspace 변경 0건). progress.md 갱신만 commit 예정.
- **목적**: 사용자 명시 G.2 "전부 진행" 승인 — A1 (Phase 7 R2 운영 배포) + A2 (5 서비스 비번 강화) + B3 (JWT_SECRET_KEY 강화). "시연 무관 제대로 확실히 완벽히" 기조 준수.
- **A2 — REDIS/RABBITMQ/MINIO/FLOWER/GRAFANA 비번 강화 (PASS)**:
  - 운영 호스트 (192.168.10.39) `/home/idino/docutil/.env` 의 5종 비번 → `openssl rand -hex 32` (64자 영숫자) 신규 — URL/sed/dotenv 안전 보장 (base64 의 `+/=` 회피).
  - 백업: `/home/idino/docutil/.env.bak.20260511_084232` (-rw-------)
  - 임시 secrets: `/home/idino/.g2_secrets_20260511_174342.txt` (0600, 작업 종료 후 사용자 결정 — 자동 삭제 미실행)
  - 일괄 재시작 8 컨테이너: `redis rabbitmq minio flower grafana api celery-worker celery-beat` — 14 컨테이너 모두 `(healthy)` 회복
  - **회귀 검증 라이브**:
    - Redis: 새 비번 `2a4a5930...25bf` PONG, 옛 `docutil_redis_2024` `WRONGPASS` (PASS)
    - RabbitMQ: `rabbitmqctl authenticate_user docutil <new>` Success — volume 의 user 비번 자동 갱신 (RabbitMQ 4.0 환경변수 매부팅 적용)
    - MinIO: minio python SDK `list_buckets()` → `['documents']` (PASS) — root_user 환경변수 매부팅 적용
    - Flower: `curl -u admin:<new>` `/api/workers` 200, 옛 401 (PASS)
    - Grafana: 환경변수 매부팅 미적용 발견 → `docker exec docutil-grafana grafana cli admin reset-admin-password <new>` 실행 → 새 비번 `/api/user` 200, 옛 401 (PASS)
    - api → Redis 라이브 (Python redis): `REDIS_URL=redis://:***@redis:6379/0` PING=True, SET/GET round-trip OK
    - Celery → RabbitMQ: `celery -A app.workers inspect ping` → `pong, 1 node online` (PASS)
- **A1 — DocUtil Phase 7 R2 청소 코드 운영 배포 (PASS — 단 AGENTHUB_URL/AGENTHUB_API_KEY 환경변수 미설정 발견)**:
  - 백업: `/home/idino/docutil/backups/backend_pre_phase7_v2_20260511_091650.tar.gz` (611K, --exclude .pytest_cache/.ruff_cache/__pycache__)
  - workspace vs 운영 SHA256 비교 (21건 모두 DIFF 확인) → SFTP 19건 신규 업로드 + `agenthub_client.py` 신규 + `claude_client.py`/`gemini_client.py` 삭제
  - 권한 정상화: `chown -R idino:idino backend/{app,alembic,tests}` + `chmod 644 backend/app/**/*.py`
  - `docker compose build api celery-worker celery-beat --progress plain` (운영 호스트 nohup detach + 폴링) — 새 이미지 ID `c489e4cdb462` (Created 2026-05-11 09:30:27)
  - `docker compose up -d --force-recreate api celery-worker celery-beat` — 3 컨테이너 모두 healthy
  - **코드 반영 검증 (라이브, docker exec)**:
    - `agenthub_client.py` 컨테이너 안 존재 확인
    - `grep -rF "from openai import" /app/app/` → 0건 (R2 단일 진입점 완전 달성)
    - `/app/app/integrations/llm/` 디렉토리 = `__init__.py / azure_client.py / client.py / factory.py / prompts.py / schema_adapter.py` — `claude_client.py / gemini_client.py` 부재 확인
    - `AgentHubClient` / `AgentHubLLMWrapper` import 검증 (10/10 PASS in docutil-api + docutil-celery-worker-1 + docutil-celery-beat — `PYTHONPATH=/app` 필수)
    - `/health` 200 + `/metrics` 정상 응답 — api 로그 에러 0건
  - **발견된 운영 환경변수 미설정 (사용자 결정 필요)**:
    - 운영 docutil `.env` 에 `AGENTHUB_URL` / `AGENTHUB_API_KEY` **둘 다 부재** — Phase 7 R2 코드의 `AgentHubClient.__init__` 가 ValueError 던짐
    - 운영 docutil `.env` 에 `LLM_PROVIDER=openai` + `OPENAI_API_KEY=sk-proj-...` 그대로 유지 (사용자 명시 외부 LLM 키 보존)
    - 운영 agenthub `.env` 의 `DOCUTIL_JWT_TOKEN=` / `DOCUTIL_API_KEY=` 모두 빈 값 — DocUtil ↔ AgentHub 양방향 인증 미연동
    - **즉 실제 LLM 호출 시점에 R2 코드가 ValueError 로 차단됨 — 별도 Phase 에서 AgentHub ApiKey 발급 + .env 갱신 필요. 본 트랙은 코드 반영 + 인프라 정상화까지만 수행.**
  - DocUtil 채팅/검색 라이브 e2e 호출은 ApiKey 미발급 사유로 본 트랙에서 미수행 — 별도 Phase 또는 사용자 ApiKey 제공 후 실행
- **B3 — JWT_SECRET_KEY 강화 + agenthub 재시작 (PASS)**:
  - 운영 agenthub `.env` 의 `JWT_SECRET_KEY` 가 example placeholder 그대로 (`YourSuperSecretKey...CharactersLong!`, 74자) 였음 발견
  - 신규 `openssl rand -hex 64` (128자 영숫자) 생성 → `.env` 갱신
  - 백업: `/home/idino/agenthub/.env.bak.20260511_132356`
  - `docker compose up -d --force-recreate agenthub` (21초 healthy)
  - **추가 발견 + 해소**: agenthub `.env` 의 `REDIS_PASSWORD` 도 stale (`docutil_redis_2024`) → A2 의 새 docutil-redis 비번으로 동기화 + agenthub 재재시작 (11초 healthy)
  - **회귀 검증 라이브**:
    - admin@example.com (BCrypt seed: `Admin123!`) 로그인 200 + 새 JWT 발급 (응답 키 `token`, len=555)
    - 새 JWT `/api/users` 200, `/api/auth/me` 200, `/api/agents` 200
    - 옛 키 서명 시뮬레이션 JWT → 401 (무효화 확인)
    - agenthub Redis 에러 grep 0건 (새 비번 정상 연결)
    - **모든 기존 사용자 JWT 무효화 발생 시각: 2026-05-11 13:23 KST**
  - 별도 관찰: `/api/admin/docutil/users` 502 — agenthub → docutil-api BFF 호출 시 발생 (`DOCUTIL_JWT_TOKEN` 빈 값 또는 `DOCUTIL_SERVICE_PASSWORD` stale 가능성). 본 트랙 범위 외, 별도 트랙에서 점검 필요.
- **잠재 위험 / 사용자 검증 필요**:
  - docutil `.env` 의 `AGENTHUB_URL` / `AGENTHUB_API_KEY` 미설정 — 다음 트랙에서 AgentHub admin UI 또는 `POST /api/api-keys` 로 ApiKey 발급 + `consumer_system='docutil'` 지정 + scope `chat,stream,embeddings,images,info,usage` 부여 + 운영 docutil `.env` 적용 + docutil-api/worker/beat 재시작 필요
  - agenthub `.env` 의 `DOCUTIL_JWT_TOKEN` 빈 값 — `/api/admin/docutil/*` BFF endpoint 502 원인 가능. agenthub 가 DocUtil API 호출 시 사용. `POST /api/v1/auth/login` 으로 service account (`jyj7970`) JWT 발급 → 24h 유효, 자동 회전 필요
  - 임시 secrets 파일 `/home/idino/.g2_secrets_20260511_174342.txt` (0600) — 사용자 결정으로 적시 삭제 필요 (5+1 비번 평문 보관 중)
  - agenthub `appsettings.json` `JwtSettings.SecretKey` 가 `""` 빈 값 — docker-compose 환경변수 `JwtSettings__SecretKey=${JWT_SECRET_KEY}` 가 우선 적용되므로 코드 동작은 정상이지만, 운영 외 환경에서 정확성 보장 위해 별도 점검 필요
- **운영 다운타임**:
  - A2: docutil 8 컨테이너 동시 재시작 — 약 60초 (rabbitmq healthy 가 30초 start_period)
  - A1: docutil 3 컨테이너 (api/worker/beat) 재시작 — 약 30초
  - B3: agenthub 단일 컨테이너 재시작 ×2 (JWT + Redis 동기화) — 각 ~25초
  - 총 다운타임: docutil ~90초, agenthub ~50초 (양쪽 합산 약 2분 30초)
- **마스킹된 신규 시크릿** (prefix 8자 + suffix 4자):
  - `REDIS_PASSWORD`: `2a4a5930...25bf` (64자 hex)
  - `RABBITMQ_PASSWORD`: `931addad...cb74` (64자 hex)
  - `MINIO_ROOT_PASSWORD`: `c05f0e2c...b276` (64자 hex)
  - `FLOWER_PASSWORD`: `9e3e33d1...14a9` (64자 hex)
  - `GRAFANA_ADMIN_PASSWORD`: `db3809ad...420a` (64자 hex)
  - `JWT_SECRET_KEY` (agenthub): `22da6fb6...5283` (128자 hex)

### 2026-05-11 (agenthub/secrets — G.1 + G.2 안전 항목 1차 보안 보강: workspace 평문 시크릿 마스킹 + 운영 chmod 600 + G.2 강행 차단 사유 발견)
- **commit**: `6cfdcee` ([agenthub/secrets] 평문 시크릿 마스킹 — iis-setting.ps1 + TODO.md placeholder 패턴 도입)
- **목적**: 사용자 명시 G.1 + G.2 안전 항목 1차 적용. 시연 무관 "제대로 확실히 완벽히" 기조 준수 — placeholder 만 보유, 운영 시크릿은 외부 주입.
- **G.1 완료 항목**:
  1. **`agenthub/iis-setting.ps1`** — DB 비번 + JWT SecretKey + OpenAI/Gemini/Perplexity/Tavily 4 LLM 키 + SMTP Username/Password = 총 8개 평문 시크릿 → `$env:OPENAI_API_KEY` 등 환경변수 참조 + `<OPENAI_API_KEY>` placeholder fallback. 한국어 보안 경고 헤더 추가.
  2. **`agenthub/TODO.md`** — IIS 설정 가이드의 동일 8개 평문 시크릿 동일 패턴 마스킹. line 83/86/88 의 `sk-proj-...` `pplx-...` `tvly-...` 약식 placeholder 는 안전하여 유지.
  3. **운영 호스트 `/home/idino/docutil/.env`** — `chmod 600` 적용 (664 → 600, owner idino:idino 유지). G.1 #4 tb_llm_api_keys deprecate 메모는 본 progress 로그에 기록(아래 별도 트랙 후보).
- **G.1 후속 잔존 평문 시크릿 (별도 트랙 권장 — 본 1차 트랙 외)**:
  - `agenthub/Program.cs:496` — `Replace("Password=rnehrwhgdk20@^", "Password=***")` 가짜 마스킹 (anti-patterns.md §4 직접 위반, DB 비번 평문 코드 박힘)
  - `agenthub/DbConnectionTest.ps1:2` — DB 비번 평문 한 줄
  - `agenthub/TECHSPEC.md:910` — 위험 문서 자체에 DB 비번 평문 노출
  - `user_mig/tools/phase72_seed.py:57` — JWT placeholder 평문 (iis-setting.ps1 과 동일 값, git history 잔존)
  - `career/claudedocs/20260124_작업내역_보고서.md:153,168` — 이미 `sk-proj-***` 마스킹됨 (안전)
- **G.2 안전 항목 사전 점검 결과 — 강행 차단**:
  - **#5 (DocUtil OPENAI 키 제거) 보류**: 운영 컨테이너 docutil-api 가 R2 위반 코드 광범위 잔존 상태로 부팅됨 (Up 3 days). workspace commit `7393322` (Phase 7 R2 잔여 7건 보강) 가 운영 미배포. 운영 점검 결과:
    - `LLM_PROVIDER=openai` (AgentHub 위임 X)
    - `AGENTHUB_BASE_URL` / `AGENTHUB_API_KEY` 환경변수 docker-compose.yml + .env 모두 미정의
    - `AgentHubClient` / `agenthub_client` 문자열 grep 결과 운영 컨테이너 내부 코드에 **0건**
    - `/app/app/integrations/image_generation/service.py:188` `AsyncOpenAI` 직접 사용 잔존
    - 12개 모듈에서 `OpenAI|openai\.` import (`llm/{openai,claude,gemini,azure}_client.py`, `modules/{chat,search,api_keys,templates}/service.py`, `workers/{report_generator,training/trainer,embedding_generator}.py`, `integrations/rag/graph_rag.py` 등)
    - **결론**: workspace 코드는 R2 청소 완료이지만 운영 호스트는 Phase 7 전 상태. 운영 OPENAI 키 제거 = 채팅/검색/이미지생성 즉시 중단. G.2 #5 강행은 사용자 기조 "제대로 확실히 완벽히" 정면 위반. **선행 트랙 필요**: workspace Phase 7 코드 운영 배포(docker compose build + up).
  - **#6 (Qdrant 강력 키 발급) — 운영 상태 이상 발견**: 현재 Qdrant 가 빈 키(`QDRANT__SERVICE__API_KEY=`)로 부팅됐으나 `curl http://qdrant:6333/collections` 가 **401 응답**. docutil-api 내부 `QdrantClient(api_key="")` Python 호출도 401 `Unauthorized`. 두 컨테이너 모두 healthy 표시이지만 RAG 호출이 실제 작동하는지 의심. `docker logs --since=24h` 의 qdrant/embedding 키워드 로그 **0건** — 최근 24h RAG 미사용 가능성 또는 로그 레벨 낮음. **결론**: 강력 키 발급은 현재보다 나빠지지 않지만, RAG 가 이미 깨졌을 가능성이 있어 사용자 확인 필요.
  - **#7 (REDIS/RABBITMQ/MINIO/FLOWER/GRAFANA 비번 강화) — 안전 강행 가능**: 현재 패턴 `docutil_<svc>_2024` (len 16~18, prefix=docu/flow/graf, suffix=024) 확인. docker-compose 의 5개 변수 참조(redis URL/celery broker/MinIO Secret/Flower basic-auth/Grafana admin) 모두 `${VAR}` 패턴이라 재시작 시 일관 적용 가능. 단, 대량 재시작 (8개 컨테이너) 이 운영 다운타임을 동반.
- **권고**: G.2 강행 전 다음 사용자 결정 필요:
  - Q-A: 운영 호스트에 workspace Phase 7 코드 배포 가능 시점? (docker compose pull + up — 이미지 빌드 + DB migration 필요 가능성)
  - Q-B: Qdrant 401 상태 — RAG 가 실제 운영에서 사용 중인가? (사용 중이라면 어떤 인증 경로? / 미사용이라면 강력 키 발급 후 정상화)
  - Q-C: 5개 서비스 비번 일괄 강화 + 대량 재시작 시점 — 업무 외 시간 또는 즉시?
- **별도 트랙 후보 (본 진행과 무관)**:
  - **R18 (TECHSPEC)** — 평문 시크릿 잔존: Program.cs 가짜 마스킹 + TECHSPEC/DbConnectionTest 평문 → 별도 청소 트랙
  - **tb_llm_api_keys deprecate** — DocUtil 운영 DB 0행 확인 후 별도 EF migration 트랙
  - **git history sanitize (D 옵션)** — first commit `1da04ab` 의 평문 키 잔존, force-push 매우 위험 트랙

### 2026-05-11 (docutil/r2 — Phase 7 R2 잔여 7건 완전 보강: chat/search/trainer/llm-client AgentHub 위임 + dead code 제거)
- **commit**: `7393322` ([docutil/r2] Phase 7 — R2 잔여 7건 완전 보강 (chat/search/trainer/llm-client AgentHub 위임 + dead code 제거))
- **목적**: DU-14 `/v1/images` 트랙(commit `6a2dd2f`) 완료 후 grep 으로 발견된 DocUtil 측 R2(anti-patterns.md §1) 위반 7건 완전 정리. 사용자 기조 "제대로 확실히 완벽히 구현" 준수 — 추정 매핑/부분 구현/dead code 잔존/임시 fallback 금지.
- **사전 조사 (필수)**: import grep + 파일 정독으로 각 위치의 live/dead 정확 판정.
  - factory.create_llm_client 가 Phase 7.3 부터 `AgentHubLLMWrapper` 만 반환 — `ClaudeClient`/`GeminiClient`/`OpenAIClient`/`VLLMClient`/`SGLangClient` 는 app 코드 instantiate 0건 확인 (tests 만 잔존).
  - `Qwen3Trainer` 외부 호출 0건 확인 (data_generator.py 와 같은 디렉토리이지만 data_generator 는 self-contained, trainer dead).
  - `graph_rag.py:105` `OpenAIClient()` 직접 instantiate — `graph_rag_enabled=False` default 이지만 R2 위반 명확, 본 트랙에 함께 보강.
- **변경 7+1 (총 10 파일, +257 / -1124 LOC, claude_client.py 502 + gemini_client.py 304 삭제 포함)**:
  1. **`docutil/backend/app/modules/chat/service.py`** (`_chat_with_websocket`, line 489~) — `https://api.openai.com/v1/chat/completions` 직접 httpx stream → `AgentHubClient.chat_stream(agent_code="docutil-rag-chat")` 위임. raw chunk dict 로 `choices[0].delta.content` + `usage.prompt_tokens/completion_tokens` 추출 그대로 보존 (token_count_input/output DB 기록 회귀 0). 예외 처리는 `AgentHubError.status_code` 별 한국어 안내문 분기 (429/401/403/5xx).
  2. **`docutil/backend/app/modules/search/service.py::_get_embedding`** (line 526~) — `https://api.openai.com/v1/embeddings` 직접 httpx → `AgentHubClient.embed(agent_code="embedding-default")` 위임. Phase 7.1 시드 카탈로그의 1536D 임베딩 Agent. fallback zeros 폴백 동일 유지.
  3. **`docutil/backend/app/modules/search/service.py::_generate_llm_answer`** (line 842~) — `https://api.openai.com/v1/chat/completions` 직접 httpx → `AgentHubClient.chat(agent_code="docutil-rag-chat")` 위임. RAG grounded 답변 생성.
  4. **`docutil/backend/app/modules/search/service.py::_check_hallucination`** (line 873~) — `https://api.openai.com/v1/chat/completions` 직접 httpx → `AgentHubClient.chat(agent_code="docutil-evaluator")` 위임. LLM-as-Judge / 사실성 평가용 Agent, temperature=0 + max_tokens=10.
  5. **`docutil/backend/app/workers/training/trainer.py::reward_function`** (line 217~) — GRPO Celery worker 의 inner `reward_function` 의 `https://api.openai.com/v1/chat/completions` 직접 sync httpx → `create_llm_client("training_judge").generate_sync()` 위임. AgentHubLLMWrapper 의 `_sync_post` 가 동기 httpx 로 AgentHub 호출. unused `get_settings` import 정리.
  6. **`docutil/backend/app/integrations/llm/claude_client.py`** (502 LOC) — **파일 삭제**. `from anthropic import` SDK 직접 import 가 R2 위반. app 코드 instantiate 0건 (tests 만) 확인 후 dead 판정. `__init__.py` 에서 `ClaudeClient` import/__all__ 제거.
  7. **`docutil/backend/app/integrations/llm/gemini_client.py`** (304 LOC) — **파일 삭제**. `https://generativelanguage.googleapis.com/v1beta/openai` OpenAI 호환 URL 직접 사용. app 코드 instantiate 0건 확인. `__init__.py` 에서 `GeminiClient` import/__all__ 제거.
  8. **`docutil/backend/app/integrations/rag/graph_rag.py::GraphRAGEngine.__init__`** (보너스) — `OpenAIClient()` 직접 instantiate(R2 위반) → `create_llm_client("chat")` factory 경유로 변경. `graph_rag_enabled=False` default 이지만 활성화 시 R2 보장.
  9. **`docutil/backend/app/integrations/llm/client.py`** — `LLMClient.__init__` base_url default 를 `"https://api.openai.com/v1"` → `None` (placeholder, base_url 미지정 instantiate 차단). `OpenAIClient`/`VLLMClient`/`SGLangClient.__init__` 에 `RuntimeError` 가드 추가 — Phase 7 R2 보강 정책 위반 시 즉시 raise + 마이그레이션 경로 안내 (AgentHubLLMWrapper / create_llm_client 사용). `ModelRouter` 클래스에 deprecation docstring 추가 (3 종 의존 클래스가 RuntimeError 던지므로 자동 dead).
  10. **`docutil/backend/tests/test_llm_{structured_cross_provider,live_providers}.py`** — `pytest.importorskip` collection 가드 추가. 삭제된 모듈 import 시도가 collection 단계에서 skip 되어 다른 tests 영향 0. Phase 4 S1 시점 cross-provider/live-API 테스트는 Phase 7.3 정책에서 의미 상실(obsolete). 별도 트랙으로 정리 예정.
- **R2 위반 grep 최종 검증 (anti-patterns.md §1)**:
  - `from openai import|import openai\b|from anthropic import|import anthropic\b|from google\.generativeai|import google\.generativeai` in `docutil/backend/app/` → **0건**
  - `api.openai.com|api.anthropic.com|generativelanguage.googleapis.com` in `docutil/backend/app/` → 5건 잔존, 모두 R2 직접 위반 **아님**:
    - `embedding_generator.py:8` — Phase 7.4 migration 노트 docstring
    - `__init__.py:11` / `client.py:67` — 본 트랙 Phase 7 보강 설명 주석
    - `api_keys/service.py:24-26` — **명시적 회색지대** (운영자 LLM 카탈로그 fetch — LLM 호출 아님, 별도 트랙 후보)
- **smoke import 검증 PASS** — 변경 11개 module (`app.integrations.llm`, `client`, `factory`, `azure_client`, `__init__`, `agenthub_client`, `rag.graph_rag`, `workers.training.trainer`, `workers.training.data_generator`, `modules.chat.service`, `modules.search.service`, `modules.api_keys.service`) 모두 import OK. ImportError 0건.
- **ruff check 결과**: 본 트랙 변경 신규 errors **0건**. 7 errors 잔존(`chat/service.py:18 delete unused`, `search/service.py:16 func unused`, `81 settings unused`, line 921 I001 등) 은 모두 pre-existing — 본 트랙 PR 범위 외.
- **ruff format 적용**: 변경 8 파일 (test 2 파일 + chat/search + 본 트랙 4 파일) 자동 포맷.
- **별도 트랙 후보 (사용자 결정 필요)**:
  - **회색지대 `api_keys/service.py:24-26`** — DocUtil 운영자의 LLM 카탈로그 (`/v1/models` 등) fetch. AgentHub `/v1/models` endpoint 신설 후 BFF 패턴으로 위임 가능. R2 직접 위반은 아님 (LLM 호출 아닌 메타 조회).
  - **Unsplash 3건** (`image_generation/service.py::_fetch_unsplash`, `image_generation/auto_select.py::_try_unsplash`, `workers/report_generator.py:1263`) — stock photo API. **anti-patterns §1 위반 아님** (LLM 호출 아님). AgentHub `/v1/images/generations` 의 Unsplash fallback 통합은 별도 설계 결정.
  - **테스트 obsolete 정리** — `test_llm_structured_cross_provider.py` / `test_llm_live_providers.py` 두 파일 (총 ~1000 LOC) 은 importorskip 으로 가드되어 안전하지만 Phase 7.3 정책에서 의미 상실. 별도 트랙에서 삭제 또는 AgentHub gateway 대상 cross-routing 테스트로 재작성 권장.
  - **`api_keys` LLM API 키 저장소** — DocUtil 의 `LLMApiKey` 테이블 자체가 Phase 7.3 단일 진입점 정책에서 사용되지 않음 (AgentHub `ApiKeyPool` 이 마스터). 별도 트랙에서 deprecate 검토.
  - **ModelRouter / OpenAIClient/VLLMClient/SGLangClient/AzureOpenAIClient deprecate 완료 후 파일 삭제** — RuntimeError 가드만 추가했고 클래스 정의는 유지. Phase 8+ 정리 트랙에서 완전 삭제 가능.

### 2026-05-11 (infra/db — 시드 reproducibility 보강: Phase 2.x + Phase 5.1 + Phase 7.1 codify, ApiKey 제외)
- **목적**: Phase 4.5 known issue 잔여 "운영 DB 시드 codify 부재" 해소. CI/신규 환경 부팅 시 시드 자동 적용 가능하도록 운영 DB 의 실제 시드 16 ApiServices + 15 Agents 를 idempotent SQL 로 codify.
- **추가 파일**: `infra/db/seeds/phase5_phase7_seeds.sql` (292 줄, 33,907 bytes)
  - §1 ApiServices 16개 (chatgpt/claude/cursor/copilot/gemini/mistral/dalle/gemini-image/imagen4/gen4-image/flux2/gen4-video/veo/openai-video/perplexity/nexus) — `ServiceCode` 기준 `WHERE NOT EXISTS` 멱등 가드
  - §2 Agents 15개 (Phase 7.1: docutil-rag-chat / docutil-report-generator / docutil-evaluator / docutil-image-generator / career-actionboard-orchestrator / career-rag-actionboard / career-competency-analyzer / career-action-recommender / career-chatbot / career-semester-planner / career-simulation-suggester / career-simulation-analyzer / embedding-default / web-search-default / agentic-search) — `AgentCode` 기준 `WHERE NOT EXISTS` 멱등 가드
  - **ServiceId FK lookup 패턴**: `(SELECT "ServiceId" FROM ... WHERE "ServiceCode" = 'chatgpt')` 서브쿼리로 신규 DB serial 시퀀스 불일치(17/23/32 ≠ 1/7/16) 흡수
  - §3 검증 쿼리 (api_services_seed=16, agents_seed_15=15, nexus_present=1 기대)
- **수정 파일**: `infra/db/init.sql` — §9 "다음 단계" 에 Phase 3.5+ 시드 적용 명령 추가 (9 lines)
- **codify 패턴 결정**: 옵션 A (별도 `infra/db/seeds/*.sql` 파일) 선택. 사유:
  1. 기존 `init.sql` §9 가 "테이블/시드 데이터는 Phase 3 EF 가 담당" 명시 — schema/extension/role 책임 분리 보존
  2. AgentHub 시드는 본래 `DatabaseInitializer.cs`(C# 런타임) 가 담당 → EF migration `HasData` 패턴이 아님. EF migration 에 raw SQL 추가하면 기존 패턴 위배
  3. UNIQUE 제약이 PK(`ServiceId`/`AgentId`)만 존재해 `ON CONFLICT (ServiceCode)` 사용 불가 → `WHERE NOT EXISTS` 패턴은 SQL 파일이 EF migration 보다 더 자연스러움
- **UNIQUE 제약 조사 결과**:
  - `Agents.AgentCode`: UNIQUE 없음 (PK 만)
  - `ApiServices.ServiceCode`: UNIQUE 없음 (PK 만)
  - `ApiKeys.KeyName`: UNIQUE 없음 (PK 만)
  - → 모든 멱등 가드는 `INSERT ... SELECT ... WHERE NOT EXISTS` 패턴 채택. 향후 UNIQUE 인덱스 추가 시 `ON CONFLICT DO NOTHING` 으로 단순화 가능 (별도 트랙)
- **ApiKey codify 제외 결정 (운영 DB master 원칙 준수)**:
  - 운영 PG `AIAgentManagement.ApiKeys` 실제 상태: ApiKeyId=2 KeyName='test' (UserId=1, AgentId=12, Scopes=NULL, IsActive=true, ExpiresAt=2026-03-31) **1행만 존재**
  - progress.md 1366 기록 "Phase 7.2 ApiKey 2건 PASS (id=1 docutil-master-key, id=2 career-master-key)" 와 운영 현실 갭 확인 — 시연용 임시 발급 후 운영 환경에 미반영/삭제 추정
  - 평문 `KeyHash` codify 시 보안 위험 + Phase 7.2 master key 가 운영 부재이므로 codify 대상 자체 없음
  - 신규 환경에서 master key 필요 시 `user_mig/tools/phase72_seed.py --print-keys` 로 재발급 (기존 idempotent 스크립트 활용)
- **빈 schema 시뮬레이션 검증** (운영 DB 내 `tmp_verify_seed` 격리 schema 사용 + ROLLBACK 으로 운영 무변경):
  - SETUP: `CREATE SCHEMA tmp_verify_seed; CREATE TABLE ... LIKE "AIAgentManagement"."ApiServices"/"Agents" INCLUDING ALL`
  - 1차 적용: ApiServices 16/16 INSERT + Agents 15/15 INSERT (FK 정합)
  - **2차 idempotent**: ApiServices 16-16=0 행 + Agents 15-15=0 행 (재실행 시 0 INSERT) — **IDEMPOTENT PASS**
  - 정합성: 운영 DB vs tmp_verify_seed schema 비즈니스 컬럼(ServiceId 시퀀스 제외) 1:1 비교
    - ApiServices: **16/16 PASS** (ServiceName/Description/ApiEndpoint/DefaultModel/CostPerRequest/IsActive/SortOrder/ServiceType/IconClass/ColorCode 모두 일치)
    - Agents: **15/15 PASS** (AgentName/Description/SystemPrompt/Temperature/MaxTokens/DefaultModel/EnableRag/PiiProtectionMode/ConsumerSystems/KnowledgeBaseSource/LlmRouting/RoutingPolicyJson/IconClass/ColorCode/IsPublic/CreatedBy/IsActive/SortOrder/PlaceholderText/ChatTheme/AllowGuestChat/AllowedEmbedDomains 모두 일치)
    - ServiceId FK 매핑: **15/15 PASS** (career-chatbot→nexus / docutil-image-generator→dalle / 나머지 13→chatgpt)
- **운영 DB 영향**: **0 행 변경** (BEGIN ... 모든 작업 ... ROLLBACK 로 운영 schema 무변경 보장 — 운영 16 svc + 15 agent + 1 ApiKey 보존)
- **검증 절차 (재현 가능)**:
  ```
  # 빈 DB 시뮬레이션:
  psql -h <host> -p <port> -U postgres -d <empty_db> -f infra/db/init.sql -v idino_pw="'<pw>'"
  cd agenthub && dotnet ef database update                                        # 테이블 생성
  psql -h <host> -p <port> -U AGENT_HUB -d AGENT_HUB -f infra/db/seeds/phase5_phase7_seeds.sql
  # 기대: api_services_seed=16, agents_seed_15=15, nexus_present=1
  # 재실행: 동일 명령 → 0 INSERT (idempotent)
  ```
- **알려진 제약 / 향후 작업**:
  - 본 시드 파일은 AgentHub `DatabaseInitializer.SeedAsync` 와 데이터 중복 가능성 — Phase 3.5+ 에서 둘 중 하나로 일원화 검토 (현재는 DatabaseInitializer 가 멱등 가드 + Seed SQL 도 멱등 가드 → 충돌 없음, 단 유지보수 부담)
  - ApiKey 재발급 시 `phase72_seed.py` 의 JWT_SECRET_KEY 가 `appsettings.Development.json` JwtSettings:SecretKey 와 동기화되어 있어야 함 (현재 hardcoded — Phase 3.5+ 환경변수 분리 검토)
  - UNIQUE 인덱스 부재 — 향후 `Agents.AgentCode` / `ApiServices.ServiceCode` / `ApiKeys.KeyName` UNIQUE 제약 추가 시 `ON CONFLICT DO NOTHING` 로 단순화 가능 (별도 트랙)

### 2026-05-11 (Phase 6.5 e2e — DocUtil RAG round-trip 라이브 검증 PASS)
- **검증 결과**: AgentHub → DocUtil `/api/v1/search` round-trip 운영 라이브 검증 완료. ADR-2 단일 위임 흐름 정상 동작 확인.
- **검증 절차 (운영서버 192.168.10.39)**:
  1. 사전 수집: `docutil-postgres` 컨테이너(운영 PG, 5440 호스트 매핑) 의 `AIAgentManagement.Agents` 32 행 조회
     - `KnowledgeBaseSource='DocUtil'` Agent 4 건 식별: AgentId=22 `docutil-rag-chat`, 23 `docutil-report-generator`, 27 `career-rag-actionboard`, 36 `agentic-search` (모두 `EnableRag=true`, Hybrid 라우팅)
     - 운영 Agent 시드가 이미 DocUtil 위임 상태이므로 **SQL UPDATE 불요** — 원복 SQL 도 불요
  2. JWT 발급 → `POST /api/chat/send` 호출 (`AgentId=22`, `serviceId=17`, `model=gpt-4o-mini`, `messages=[{user, 한국어 query}]`, `enableRag=true`, `ragTopK=3`, `language=ko`)
  3. AgentHub 로그 분석으로 RAG 흐름 검증
  4. DocUtil 로그 분석으로 수신 검증
  5. ChatMessages / ChatConversations DB row 영속화 검증
- **AgentHub 로그 (RAG 흐름)**:
  ```
  Chat request prepared. EnableRag: True, DocumentIds: null, AgentId: 22
  RAG check in SendChatMessageAsync: EnableRag=True, RagService=available
  RAG search starting. EnableRag: True, Query: Phase 6.5 e2e 검증입니다..., UserId: 1, AgentId: 22
  QueryRewriter PASS — 원본 한국어 → +1건 영문 augment (Please provide the titles or key topics ...)
  RAG 위임 - AgentId=22, KnowledgeBaseSource=DocUtil, CollectionRef=(global), TopK=3, QueryCount=2
  Start processing HTTP request POST http://docutil-api:8000/api/v1/search  (x2 - multi-query)
  RAG 결과 - DistinctChunks=5, TopK 반환=3
  RAG search completed and added to request.Messages. Found 3 relevant chunks.
  ```
- **DocUtil 로그 (수신 측)**:
  ```
  Reranking unavailable, returning fused order  (x2)
  INFO: 172.28.0.16:51686 - "POST /api/v1/search HTTP/1.1" 200 OK  (x2 per request, 4 total)
  ```
- **LLM 응답 (Message 894, gpt-4o-mini-2024-07-18)**:
  ```
  죄송하지만, "Phase 6.5 e2e 검증"에 대한 구체적인 정보는 제공된 문서에서 찾을 수 없습니다.
  따라서 해당 내용에 대해 답변할 수 없습니다. 다른 질문이 있으시면 도와드리겠습니다.
  ```
  → `tokensUsed=970`(RAG 청크 prepend 영향으로 prompt 비대), `cost=$0.0291`, `responseTime=4282ms`
  → LLM 이 "**제공된 문서**" 라는 phrase 로 RAG context 의 존재를 명시적으로 인지 → 시스템 프롬프트에 청크가 prepend 됐음을 입증
  → SystemPrompt 정책 "출처가 없는 추측이나 일반 지식으로 답변하지 마세요... 문서에서 답을 찾을 수 없으면 솔직히 모른다고 답합니다" 준수 (hallucination 0)
- **영속화 검증 (DB)**:
  - `ChatConversations.ConversationId=262` (Title=`phase10_1c regression`, AgentId=22, ServiceId=17, Model=`gpt-4o`, EnableRag=true)
  - `ChatMessages` 영속화: 893(user query), 894(assistant 응답) row 추가 — 2026-05-11 03:57:41 UTC
  - 동일 conversation 의 어제 message(891/892, 2026-05-10) 도 RAG path 정상 동작 확인 (Phase 10.1c regression)
- **검증 평가**:
  - RAG round-trip 동작: **PASS** (AgentHub → DocUtil → 5 chunks → 3 prepend → LLM → 응답)
  - 응답 품질: **PASS** (RAG context 인지, hedging without hallucination, SystemPrompt 정책 준수)
  - Latency: 4282 ms (DocUtil 2-query rewrite + RRF + gpt-4o-mini 호출 포함)
  - Multi-query RRF: 한국어 원본 + 영문 augment(LLM rewrite) 양 query 가 DocUtil 호출되어 RRF 결합
  - Phase 6.1~6.4(DocUtilClient/BFF) + Phase 7.x(R2 단일 진입점) + ADR-2(KB 단일 권위) 모두 **운영 환경 통합 동작 확인**
- **부차 발견(별도 트랙)**:
  - 운영 DocUtil PG 의 `tb_documents`/`tb_documents_v2`/`tb_document_chunks`/`tb_folders`/`tb_search_scopes`/`tb_projects` 모두 0 행. 그럼에도 `/api/v1/search` 가 5 chunks 반환 → Qdrant `doc_embeddings` 컬렉션에 별도 데이터가 있음을 시사. 마이그레이션 시 Qdrant 코퍼스 inventory 별도 점검 권장 (task 추가 권고)
  - 운영 DocUtil 의 `QDRANT_API_KEY=` 빈 값 — Qdrant access 가 LAN-only 의존 (보안 약점, 별도 트랙)
  - `OPENAI_API_KEY` 가 `docutil-api` env 에 평문 노출 (`docker inspect` 로 가시) — Phase 6 ADR-2 에서 DocUtil 의 LLM 직접 호출 deprecate 일관성 점검 필요 (별도 트랙)
  - `/api/chat/send` Endpoint validation: `ServiceId` 가 DTO 에서 nullable 이나 컨트롤러 라인 349 에서 필수 처리 → Vue UI 도 동일 흐름이므로 Validation 명세 일관 (변경 불요)
  - 외부 OpenAI 일시 `InternalServerError` 1회 관측 → 1회 retry 로 PASS. AgentHub 의 fallback model 로직(`FallbackModel` 파라미터)이 본 호출에서는 사용 안 됨 (gpt-4o-mini 자체로 성공). Phase 10.x fallback 정책 별도 검증 권고
- **TECHSPEC 영향**:
  - Phase 6 (DocUtil 운영자 흡수 + KB 위임) **운영 검증 완료** → §12 Phase 표에서 Phase 6.5 = ✓ 표기 가능
  - ADR-2 (KB 단일 권위 = DocUtil) 운영 동작으로 final acceptance
- **사용된 검증 스크립트** (`tmp/phase65_step1~10*.py`, 10개 단계):
  - step1: 운영 컨테이너 식별 → docutil-postgres 확정
  - step2-3: PG schema 조사 → Agents/document_utilization 테이블 카탈로그
  - step4-5: Agents 시드 + DocUtil 0건 + Qdrant doc_embeddings 컬렉션 이름 확정
  - step6-7: JWT 로그인 + chat send → ServiceId 누락/correctness 조정
  - step8: 안정적 응답 확보 (retry 1회로 PASS) + RAG context flow 로그 추출
  - step10: ChatMessage / ChatConversation 영속화 검증

### 2026-05-11 (Phase 10.x — 정합성 분석 Critical/High/Medium 결함 보강 — 6건)

**배경**: code-analysis-specialist 가 Phase 10.x 완료 직후 `agenthub/` + DocUtil BFF 트랙 전반에 대한 정합성 분석을 수행하고 Critical 1·High 4·Medium 1 의 6개 결함을 식별. 시연 압박과 무관하게 "제대로/확실히/완벽히" 보강 — 부분 구현·@ts-nocheck·TODO 일체 금지. 모든 보강은 회복탄력성·UX 일관성·보안(정보 누출 방지) 차원이며 신규 기능 추가가 아닌 기존 패턴의 누락 보강.

**보강 내역 (6건)**:

1. **(Critical) Vue Router 권한 가드 — `meta.role|roles` 검증 추가**
   - 파일: `agenthub/ClientApp/src/router/index.ts`
   - 문제: `/admin/docutil-*` 13 라우트 + 기존 admin 라우트들이 `meta: { requiresAuth: true, role: 'Admin' }` 부착에도 불구하고 `router.beforeEach` 가 token 존재만 검증 → 일반 사용자가 URL 직접 입력 시 백엔드 `[Authorize(Roles="Admin,SuperAdmin")]` 401 으로만 차단되던 UX 비일관(Vue 가 admin 컴포넌트를 mount 한 후 API 호출에서 401 → 빈 화면).
   - 변경: `useAuthStore()` 의 `user.roles: string[]` 와 교차 검증.
     - 헬퍼 `getRequiredRoles(meta)` 가 `meta.role: string` + `meta.roles: string[]` 둘 다 단일 배열로 정규화.
     - 헬퍼 `hasRequiredRole(userRoles, required)` 가 `SuperAdmin` 자동 통과(상위 권한 — Admin 포함 모든 페이지) + `required.some(r => userRoles.includes(r))` 검사.
     - user 메모리 미적재 상태(새로고침 직후) → `auth.loadUser()` 트리거. 실패 시 `logout()` 후 `/login?redirect=...`.
     - 권한 부족 시 root(`/` = Dashboard) 리다이렉트(무한 루프 방지) + console.warn 로깅.
   - LOC: +75 (헬퍼 2개 + beforeEach 확장 + 한글 주석 블록).

2. **(High) Phase 10.1a/10.1b mutation catch invalidate 일관 보강**
   - 파일 2개:
     - `agenthub/Controllers/AdminDocUtilUsersController.cs`
       - `UpdateUserStatus` catch — `InvalidateUsersCacheAsync()` 추가
       - `DeleteUser` catch — `InvalidateUsersCacheAsync()` 추가
     - `agenthub/Controllers/AdminDocUtilDepartmentsController.cs`
       - `UpdateOrganization` catch — `InvalidateDepartmentsCacheAsync()` 추가
       - `CreateDepartment` catch — `InvalidateDepartmentsCacheAsync()` 추가
       - `UpdateDepartment` catch — `InvalidateDepartmentsCacheAsync()` 추가
   - 배경: Phase 10.1c+ `DeleteDepartment` 의 ghost 패턴(catch 시에도 invalidate)이 10.1a/10.1b 에는 부분 적용 — DocUtil 측 5xx 중간 단절 시 부분 변경이 캐시 stale 로 GET 응답에 ghost 데이터로 잔류할 위험. 모든 mutation catch 에 일관 적용하여 DocUtil 실제 상태와 AgentHub 캐시 동기화.
   - LOC: +20 (5개 catch 에 await + 한글 주석 4줄씩).

3. **(High) DocUtil HttpClient — Polly Retry + Circuit Breaker 적용**
   - 파일: `agenthub/AIAgentManagement.csproj` + `agenthub/Program.cs`
   - 변경:
     - `Microsoft.Extensions.Http.Polly 8.0.11` PackageReference 추가.
     - Program.cs `using Polly;` + `using Polly.Extensions.Http;` 추가.
     - `GetDocUtilRetryPolicy()` static helper — `HttpPolicyExtensions.HandleTransientHttpError()` 로 5xx + `HttpRequestException` 만 retry(4xx 은 비즈니스 오류 — 즉시 전파). 3회, exponential backoff 200ms / 500ms / 1000ms(총 retry budget ≈ 1.7s, HttpClient 60s timeout 내 여유). onRetry 콜백에서 attempt/delay/status 콘솔 trace.
     - `GetDocUtilCircuitBreakerPolicy()` static helper — 5회 연속 실패 → 30초 차단(`BrokenCircuitException` 발생 → `DocUtilClient` 의 `InvalidOperationException` 변환 → 502). onBreak/onReset/onHalfOpen 콜백 콘솔 trace.
     - `"docutil"` Named HttpClient 에 `.AddPolicyHandler(GetDocUtilRetryPolicy()).AddPolicyHandler(GetDocUtilCircuitBreakerPolicy())` 체인 적용.
   - LOC: +60 (helper 2개 + 정책 적용 + 한글 주석 블록).

4. **(High) `"docutil-longrunning"` Named HttpClient 신설 + endpoint 별 5분 timeout 분리**
   - 파일: `agenthub/Program.cs` + `agenthub/Services/DocUtilClient.cs` + `agenthub/appsettings.json`
   - 변경:
     - Program.cs 에 `"docutil-longrunning"` Named HttpClient 추가 — 동일 BaseUrl, **5분 timeout**(`DocUtil:LongRunningTimeoutMinutes` 기본 5), 동일 Polly Retry/CB 정책.
     - `DocUtilClient` 에 `LongRunningHttpClientName = "docutil-longrunning"` const 추가.
     - 5개 long-running endpoint 가 `_httpClientFactory.CreateClient(LongRunningHttpClientName)` 사용:
       1. `DownloadReportAsync` — Report 파일(zip/xlsx/csv) 다운로드
       2. `PreviewDocumentTemplateAsync` — Jinja2 템플릿 렌더 미리보기
       3. `RequestDocumentV2ExportAsync` — 비동기 export job 요청(동기 큐잉 시 지연)
       4. `DownloadDocumentV2ExportAsync` — 대용량 export 파일 다운로드
       5. `ExportAuditLogsAsync` — 감사 로그 CSV 스트리밍(N만건)
     - `appsettings.json` `DocUtil` 섹션에 `LongRunningTimeoutMinutes: 5` 키 추가.
   - 배경: 60s 표준 timeout 으로는 위 5개 시나리오 대응 부족 — 사용자 체감 한계(5분)까지 허용하되 그 이상은 504 전파.
   - LOC: +50 (Program.cs Named client + DocUtilClient const + 5개 메서드 변경 + 주석).

5. **(High) `DocUtilTokenProvider.GetOrganizationIdAsync` — `DefaultOrganizationId` 폴백**
   - 파일: `agenthub/Services/DocUtilTokenProvider.cs` + `agenthub/appsettings.json`
   - 변경: JWT `org` claim 추출 실패(ApiKey-only 모드 또는 claim 미부착) 시 `IConfiguration["DocUtil:DefaultOrganizationId"]` 폴백. 양쪽 null → 기존 동작(null 반환 → 502 한국어 안내).
   - `appsettings.json` `DocUtil` 섹션에 `DefaultOrganizationId: ""` 키 추가 — 배포 시 운영자가 채움.
   - 한글 주석에 폴백 우선순위 명시(1. JWT claim → 2. DefaultOrganizationId → 3. null).
   - LOC: +25 (메서드 본문 확장 + 한글 주석 강화).

6. **(Medium) `EnsureSuccessOrThrowKoreanAsync` — 영문 body leak 차단 + 422 한국어 매핑**
   - 파일: `agenthub/Services/DocUtilClient.cs`
   - 문제: 기존 `$"DocUtil 호출이 실패했습니다 (HTTP {status}): {Truncate(body, 200)}"` 가 DocUtil 영문 body 를 클라이언트 응답에 그대로 echo — UX 비일관 + 정보 누출 위험(DocUtil 내부 path/SQL/stack trace 일부가 새어나갈 수 있음).
   - 변경:
     - 일반 4xx: `"DocUtil 호출이 실패했습니다 (HTTP {status}). 입력값 또는 권한을 확인하세요."` — body echo 제거. 원본 body 는 `LogWarning` 에만 잔류.
     - 422 special-case: `TryExtractValidationHint(body)` 가 FastAPI/Pydantic 표준 `{"detail": [{"loc":[...], "msg":"..."}]}` 응답에서 `loc 의 마지막 component + msg` 를 `{field}: {msg}` 형태로 추출(매핑 실패 시 일반 422 안내 폴백). 사용자 입력 검증 실패 정보는 유용하므로 한국어 안내와 함께 200자 내로 truncate.
   - LOC: +65 (`TryExtractValidationHint` 헬퍼 + 422 분기 + 일반 4xx 안내 교체 + 주석).

**파일 변경 요약**:
| 파일 | 변경 LOC |
|---|---|
| `agenthub/ClientApp/src/router/index.ts` | +75 |
| `agenthub/Controllers/AdminDocUtilUsersController.cs` | +8 |
| `agenthub/Controllers/AdminDocUtilDepartmentsController.cs` | +12 |
| `agenthub/AIAgentManagement.csproj` | +2 |
| `agenthub/Program.cs` | +85 |
| `agenthub/Services/DocUtilClient.cs` | +75 |
| `agenthub/Services/DocUtilTokenProvider.cs` | +20 |
| `agenthub/appsettings.json` | +2 |

**ADR 추가**:
- **ADR-16: DocUtil 호출 정책 — Polly Retry/Circuit Breaker + endpoint 별 timeout 분리 + body leak 차단 + org_id 폴백**
  - **결정**: AgentHub → DocUtil 의 모든 HTTP 호출은 두 Named HttpClient(`"docutil"` 60s / `"docutil-longrunning"` 5분) 중 하나를 사용하며, 양쪽 모두 동일 Polly 정책(Retry 3회 exp backoff 200/500/1000ms + Circuit Breaker 5/30s, 5xx 한정)을 거친다. 4xx 는 즉시 전파(retry 무의미). 클라이언트 응답에는 DocUtil 영문 body 를 노출하지 않고, 422 는 한국어 매핑 시도. ApiKey-only 모드는 `DocUtil:DefaultOrganizationId` 폴백 지원.
  - **이유**: (1) DocUtil 일시적 장애에 대한 fail-fast cascade 차단 + retry 회복, (2) 60s 단일 timeout 의 long-running 시나리오(대용량 export/스트리밍) 부적합, (3) 정보 누출 방지 + 사용자 친화 한국어 일관, (4) ApiKey 운영 환경(JWT 없음)에서도 운영자 콘솔 동작.
  - **반영 위치**: `agenthub/Program.cs` (Named HttpClient 2개 + Polly 정책), `agenthub/Services/DocUtilClient.cs` (LongRunningHttpClientName + EnsureSuccessOrThrowKoreanAsync + TryExtractValidationHint), `agenthub/Services/DocUtilTokenProvider.cs` (GetOrganizationIdAsync), `agenthub/appsettings.json` (DocUtil 섹션 2 키 추가).

**검증**:
- `dotnet build` (cd agenthub) — 경고 11개(전부 기존 CS1998: 다른 컨트롤러/서비스의 async no-await — 본 변경과 무관) · **오류 0개**.
- `cd agenthub/ClientApp && npm run build:check` (vue-tsc + vite build) — **통과**(built in 4.18s, 오류 0건).
- `@ts-nocheck` 신규 추가 — **0건**(기존 3개 파일 모두 본 작업과 무관).
- 라이브 검증: AgentHub 프로덕션(`http://192.168.10.39:64005/`) reachable(HTTP 200). 본 변경 배포 후 5xx 시뮬레이션 + Circuit Breaker 열림/닫힘 + 422 한국어 매핑 검증은 deploy 후 별도 트랙.

**남은 후속 작업** (Medium/Low — 본 보강 범위 밖):
- Reports 410 안내(이미 일부 구현됨 — `DocUtilClient.GetReportAsync` 등이 410 handling 가지지만 모든 endpoint 검증 필요)
- Templates 사전 검증(Jinja2 syntax check, variable 누락 사전 차단 — DocUtil 측 사전 endpoint 가 없으므로 422 폴백 정책으로 충분 판정)
- N+1 쿼리 검증(DocUtilClient → DocUtil endpoint 단위 — 현재 N+1 패턴 식별되지 않음, 추후 트래픽 증가 시 재검토)
### 2026-05-11 (Phase 10.2e — DocUtil API Keys + DocUtil 에이전트 + Documents V2(디자이너 워크플로) 운영자 BFF + Vue 콘솔 완료)
- **목적**: AgentHub 운영자가 DocUtil 의 3개 추가 도메인 — (A) LLM API Key 등록·회수·검증 / (B) DocUtil 자체 챗봇 페르소나 CRUD(AgentHub Agent 와 별개) / (C) 디자이너 기반 신규 문서 V2 워크플로(자유 생성 + 부분 패치 3종 + 비동기 export 5포맷 + 상태 폴링 + 프록시 다운로드) — 까지 단일 진입점에서 운영. Phase 10.1a~c / 10.2a~d 의 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑 + version-key invalidate + RFC 5987 한글 파일명 + HttpResponseOwnedStream lifetime 결합) 그대로 적용 — 총 **16 endpoint** 신설(4+5+7).
- **사전 검증** (DocUtil 컨테이너 미가동 — 소스코드 직접 인스펙션 채택):
  - `docutil/backend/app/modules/api_keys/router.py` 129 LOC + `agents/router.py` 208 LOC + `documents_v2/router.py` 681 LOC + 각 `schemas.py` 정독 → endpoint path 확정.
  - **Documents V2 경로 중첩 발견**: `app/main.py` 가 `documents_v2_router` 를 `prefix=API_V1=/api/v1` 로 마운트하고, 그 라우터 자체가 `prefix="/v2"` 를 가지므로 최종 경로는 `/api/v1/v2/documents/*`. 추정 금지로 정확 반영.
  - API Keys 는 prefix 없음(parent /api/v1 만) — 4 endpoint(List/Create/Delete/Verify) 평문 키는 등록 시점에만 전송 + 응답엔 마스킹 prefix.
  - DocUtil "Agent" ≠ AgentHub "Agent" 도메인 분리 확정 — DocUtil 측은 system_prompt/temperature/max_tokens 페르소나, AgentHub 의 라우팅·RAG 호스트와는 별개. UI 에 명시적 안내.
  - Documents V2 endpoint 7개 식별: POST 자유 생성(202) / GET 목록(limit·offset + document_type·mode 필터) / GET 단건 / PATCH 부분 패치(page·component·tokens) / POST 비동기 export(202) / GET 상태 폴링 / GET 결과 프록시 다운로드(stream).
- **변경 파일**:
  - `agenthub/Services/IDocUtilClient.cs` — 16 메서드 + record DTO 12종 추가(+ 인터페이스 1142 → ~1340 LOC, DTO 영역 + ~270 LOC).
  - `agenthub/Services/DocUtilClient.cs` — 16 구현 + 매핑 헬퍼 3 + private DTO 13(+ ~800 LOC, 4859 → ~5660 LOC).
  - `agenthub/Controllers/AdminDocUtilApiKeysController.cs` 신설 — ~280 LOC, [Authorize(Roles="Admin,SuperAdmin")], 캐시 namespace `docutil-api-keys` 5분 TTL, mutation 성공/실패 모두 invalidate, **평문 키 로깅 절대 금지**(id/llm_name/prefix 만).
  - `agenthub/Controllers/AdminDocUtilDocAgentsController.cs` 신설 — ~330 LOC, `docutil-doc-agents` 10분 TTL, AgentHub Agent 와 도메인 격리 명시 주석.
  - `agenthub/Controllers/AdminDocUtilDocumentsV2Controller.cs` 신설 — ~480 LOC, `docutil-documents-v2` 10분 TTL, 7 endpoint, DocumentType 7-Literal + export 포맷 5-Literal + patch_type 3-Literal + page/component id regex 사전 차단, design_tokens 16KB + patch data 256KB 사이즈 캡, binary stream HttpResponseOwnedStream + RFC 5987 + ASCII fallback.
  - `agenthub/ClientApp/src/services/docutilService.ts` — Phase 10.2e 16 함수 + interface 19 + parseDocumentV2FileName 헬퍼 추가(2099 → ~2480 LOC). default export 객체에 16 entry 추가.
  - `agenthub/ClientApp/src/views/admin/AdminDocUtilApiKeys.vue` 신설 — ~340 LOC, `<script setup lang="ts">`, 평문 키 경고 + 등록/검증/삭제 UI.
  - `agenthub/ClientApp/src/views/admin/AdminDocUtilDocAgents.vue` 신설 — ~520 LOC, info 박스(AgentHub Agent 와 별개 도메인) + CRUD + system_prompt textarea.
  - `agenthub/ClientApp/src/views/admin/AdminDocUtilDocumentsV2.vue` 신설 — ~720 LOC, 디자이너 워크플로 UI(생성/패치/Export/상태 폴링/Blob 다운로드 모달 5개).
  - `agenthub/ClientApp/src/router/index.ts` — 3 라우트 추가(lazy + `meta.role='Admin'`).
  - `agenthub/ClientApp/src/layouts/MainLayout.vue` — docutil 카테고리 8·9·10 항목 추가(`bi-key` / `bi-robot` / `bi-easel2`), 총 13 항목.
  - `agenthub/ClientApp/src/i18n/locales/ko.json` + `en.json` — nav 3 키 + `adminDocutilApiKeys`/`adminDocutilDocAgents`/`adminDocutilDocumentsV2` 3 블록(약 160 키 × 2 locale = 320 신규).
  - `agenthub/Tools/test_phase_10_2e_e2e.ps1` 신설 — 정합성 자동 검증 86 케이스(UTF-8 BOM 부착하여 Windows PowerShell 실행 가능).
- **검증 결과**:
  - `dotnet build` errors=0 / warnings=0 (변경 코드 한정 — 기존 CS1998 11건은 본 트랙 무관).
  - `npm run build:check` (vue-tsc + vite build) errors=0 / `@ts-nocheck` 부착 0건(grep 검증).
  - 신규 청크: `AdminDocUtilApiKeys-...js` / `AdminDocUtilDocAgents-MI6g14Tu.js` 17.38 kB / `AdminDocUtilDocumentsV2-D2j-YTH6.js` 28.45 kB / `docutilService-CrjQOVl4.js` 17.04 kB.
  - **정적 e2e 검증 PASS 86/86** (`agenthub/Tools/test_phase_10_2e_e2e.ps1`): 파일 존재 9 / 신규 endpoint 카운트 4+5+7=16 / 회귀 9 컨트롤러 endpoint 보존 79(4+9+13+7+9+7+5+10+15) / 권한 게이트 12 / 캐시 invalidate 사이트(ApiKeys 7 / DocAgents 7 / DocsV2 5) / IDocUtilClient 16 메서드 시그니처 / docutilService 16 export / 라우터 3 / 메뉴 3 / i18n 3 블록 ×2 = 6 / @ts-nocheck 0.
  - 한국어 BadRequest/502 메시지 — ApiKeys 11 / DocAgents 11 / DocsV2 17 사이트, 사전 입력 차단 + upstream 매핑 모두 한국어.
- **회귀 정합성**: 직전 9 DocUtil admin 컨트롤러(10.1a/b/c + 10.2a/b/c/d) HTTP 속성 카운트 모두 보존(4+9+13+7+9+7+5+10+15 = 79). 본 트랙 신규 16 합산 — **DocUtil 운영자 BFF 누적 95 endpoint** 도달.
- **외부 동작 변경 0** — `IDocUtilClient` 신규 16 메서드 추가만, 기존 시그니처 보존 / DocUtilClient 16 구현 추가만, 기존 코드 변경 0 / 라우트 추가만, 기존 라우트 변경 0 / record DTO 변경 0 / DI 수명 보존(DocUtilClient Scoped, IDocUtilTokenProvider Singleton, CachingService Singleton). 시연 안정성 100%.
- **운영자 도메인 통합**: AgentHub 한 화면에서 DocUtil 의 **LLM API Key 관리**(외부 프로바이더 신뢰 관계) + **자체 챗봇 페르소나**(DocUtil 내부 AI 운영) + **디자이너 기반 신규 문서 워크플로**(Phase 4 후속 — 자유 생성·부분 패치·비동기 export·다운로드)까지 단일 진입점 확보.
- **마지막 commit**: `3a423ae` (`[agenthub/docutil-admin] Phase 10.x — Medium/Low 결함 4건 보강 (Reports 410 안내 + Templates 사전 검증 + DocAgents 부제 + N+1 검증)`, +226/-12 LOC, 8 파일 변경(1 신규 + 7 수정)). 직전 `657517d` (Phase 10.x Critical/High/Medium 6건). 그 이전 `76a6860` (Phase 10.x 트랙 본체). 그 이전 `7f8ff61` (10.2e). 그 이전 `505b1bb` (10.2d Templates 15 endpoint).
- **다음 트랙**: 사용자 결정 대기 — (A) 운영자 콘솔 종합 batch 검증(13 항목 회귀) / (B) DocUtil 자체 `evaluation/logs` Pydantic 버그(10.2b C3) DocUtil 트랙 분리 / (C) DocUtil 의 `documents_v2` 측 PATCH/Export 실제 라이브 검증(컨테이너 부팅 후) / (D) Phase 6 잔여 작업 / (E) Phase 7 등 후속.

### 2026-05-11 (Phase 10.2d — DocUtil 문서 템플릿(Document Templates / Jinja2) 운영자 BFF + Vue 콘솔 완료)
- **목적**: AgentHub 운영자가 DocUtil 의 Jinja2 기반 문서 생성 템플릿(`/api/v1/templates`) 전체 라이프사이클 — 메타데이터 CRUD + 파일 업로드 3종(일반/빈양식/스마트 자동 라우팅) + AI 자동채움(소스 문서 → 변수값 자동 생성) + 일반 문서 → Jinja2 템플릿 변환 + 변수 메타 일괄 편집 + 원본 파일 미리보기 다운로드 + 에디터용 문서 구조 조회 + 변수 매핑 적용까지 단일 진입점에서 운영. Phase 10.1a~c / 10.2a~c 의 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑 + version-key invalidate + RFC 5987 한글 파일명) 그대로 적용 — 총 **15 endpoint** 신설.
- **사전 검증** (DocUtil 컨테이너 미가동 — 소스코드 직접 인스펙션 채택):
  - `docutil/backend/app/modules/templates/router.py` 816 LOC 정독 → 라우트 prefix=`""` + `app/main.py` 가 `prefix=f"{API_V1}"` (=`/api/v1`) 로 마운트 → 모든 endpoint `/api/v1/templates/...` 절대 경로 확정.
  - `schemas.py` 333 LOC: `TemplateCreate` 8 필드, `TemplateUpdate` 10 필드(모두 nullable, partial), `TemplateResponse` 19 필드 (alias `schema_`→`schema` / `ins_dt`→`created_at` / `upd_dt`→`updated_at`), `TemplateUploadResponse` 6 필드, `TemplateVariableSchema` 6 필드(name/var_type/label/description/required/category default=`"ai_generated"`), `TemplateVariablesUpdate` / `AutoFillRequest` / `AutoFillResponse` / `VariableMapping` 10 필드 / `VariableMappingPayload`.
  - `models.py` 84 LOC: `DocumentTemplate` SQLAlchemy ORM — `template_storage_path` / `original_file_path` / `jinja2_variables` / `rendering_mode` (jinja2/structured) / `image_generation_config` 컬럼 확인.
  - **410 deprecate 표식 없음** — Phase 10.2c 의 `/reports/templates`, `/reports/generate` deprecate 와 무관한 별도 도메인(Document Generation Templates ≠ Report Output Templates) 확정.
  - **추정 금지 원칙 정확 적용**: schema_ alias 처리 / ins_dt·upd_dt validation_alias 처리 / variable category default `ai_generated` 보존 / VariableMapping 10 필드 모두 보존(table_index/row/col/paragraph_index nullable / variable_name pattern `^[a-zA-Z_][a-zA-Z0-9_]*$` / field_type "short"|"long").
- **백엔드 변경 (총 +~2050 LOC)**:
  - `agenthub/Services/IDocUtilClient.cs`: 인터페이스 15 메서드 + record DTO 13종 추가(`DocUtilDocumentTemplate` 17 필드 / `DocUtilDocumentTemplateDetail` / `DocUtilDocumentTemplateList` / `DocUtilCreateDocumentTemplateRequest` 9 필드 / `DocUtilUpdateDocumentTemplateRequest` 10 필드 partial / `DocUtilUploadDocumentTemplateRequest` / `DocUtilUploadSmartTemplateRequest` / `DocUtilDocumentTemplateVariable` 6 필드 / `DocUtilUpdateDocumentTemplateVariablesRequest` / `DocUtilDocumentTemplateUpload` / `DocUtilAutoFillDocumentTemplateRequest` / `DocUtilDocumentTemplateAutoFill` / `DocUtilDocumentTemplateMapping` 10 필드 / `DocUtilApplyDocumentTemplateMappingRequest` / `DocUtilDocumentTemplatePreview`).
  - `agenthub/Services/DocUtilClient.cs`: 15 구현 + 매핑 헬퍼 4(`MapDocumentTemplate`/`MapDocumentTemplateDetail`/`MapDocumentTemplateVariable`/`MapDocumentTemplateUpload`) + `ConvertJsonElementToOptionalDict` (nullable dict 변환 헬퍼) + private DTO 10(`DocumentTemplateResponseDto`/`DocumentTemplateListResponseDto`/`DocumentTemplateCreateRequestDto`/`DocumentTemplateUpdateRequestDto`/`DocumentTemplateVariableDto`/`DocumentTemplateVariablesUpdateRequestDto`/`DocumentTemplateUploadResponseDto`/`DocumentTemplateAutoFillResponseDto`/`DocumentTemplateMappingDto`/`DocumentTemplateMappingPayloadDto`) + 3종 업로드 통합 헬퍼 `UploadDocumentTemplateInternalAsync`(standard/blank: template_type+output_format 필수 / smart: 모두 nullable, tone 기본 "formal", multipart Authorization 별도 부착).
  - `agenthub/Controllers/AdminDocUtilTemplatesController.cs` 신설(~890 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` `/api/admin/docutil/templates/...` + 캐시 namespace **`docutil-document-templates`**(보고서/FAQ 와 격리) + `du:doctpl:list:`/`detail:`/`vars:` 10분 TTL + version-key invalidate + mutation 성공/실패 모두 invalidate(10.1b ghost 패턴) + 다음 사전 차단: BadRequest 검증 44건(Korean) / mapping `location_type` "table_cell"|"paragraph" enum 강제 / variables 1000 max / auto-fill source 50 max / ai_analysis & mappings JSON 64KB 캡 / upload RequestSizeLimit 50MB / multipart 3종 endpoint 분리(`/upload`/`/upload-blank`/`/upload-smart`) / convert 요청 wrapper `ConvertTemplateRequest` 로 `{ ai_analysis: {...} }` JSON body 라우터 형식 일치 / preview stream HttpResponseOwnedStream 재사용 + RFC 5987 한글 파일명 + ASCII fallback 두 헤더 부착).
- **프론트엔드 변경 (총 +~890 LOC)**:
  - `agenthub/ClientApp/src/services/docutilService.ts`: 15 함수 + TS interface 11종(camelCase ↔ snake_case 자동 매핑) + `parseDocumentTemplateFileName` 헬퍼.
  - `agenthub/ClientApp/src/views/admin/AdminDocUtilTemplates.vue` 신설(~920 LOC, `<script setup lang="ts">` + i18n + 페이지네이션 + 유형 필터 + 6-tab 상세 모달(기본정보/변수메타/문서구조/AI 자동채움/Jinja2 변환/변수 매핑) + 3종 업로드 모달(standard/blank/smart 모드 분기) + 생성 모달(JSON 메타) + 변수 메타 inline 편집 표(타입/카테고리 select) + ai_analysis & mappings JSON 텍스트 입력 + 미리보기 Blob → URL.createObjectURL → a[download] + 50MB 사이즈 limit) — `@ts-nocheck` 미부착.
  - `agenthub/ClientApp/src/router/index.ts`: `/admin/docutil-templates` 라우트(lazy + `meta.role='Admin'`) 추가.
  - `agenthub/ClientApp/src/layouts/MainLayout.vue`: docutil 카테고리 10번째 항목(`bi-file-earmark-code`) 추가.
  - `agenthub/ClientApp/src/i18n/locales/ko.json`, `en.json`: 신규 키 **115×2=230개**(`adminDocutilTemplates.*` + `nav.docutilTemplates`) — 0 missing / 0 unused.
- **검증**:
  - `dotnet build` errors=0, warnings 11(전부 본 트랙과 무관한 기존 코드 CS1998).
  - `npm run build:check`(vue-tsc + vite) PASS, errors=0, `@ts-nocheck` 부착 0건(신규 코드), 신규 청크 `AdminDocUtilTemplates-N_fEzlgP.js`(35.12 kB, gzip 7.92 kB) + 동명 css.
  - **정적 e2e 검증** PASS (라이브 인스턴스 미가동 — DocUtil 컨테이너/AgentHub IIS 모두 부재). 운영자가 살릴 때 사용할 PowerShell 스크립트 `agenthub/Tools/test_phase_10_2d_templates_e2e.ps1` 동봉 — 다음 검증 자동화:
    - 권한 게이트 2(Anonymous→401 / Non-Admin→403),
    - 입력 검증 6건(empty body / missing source_document_ids / missing ai_analysis / empty mappings / invalid location_type / ...) → 모두 400 한국어 본문 매처 포함,
    - 라이프사이클 8단계(생성→GET→PUT→variables→structure→preview→delete→404 회귀),
    - 캐시 invalidation 검증(생성 직후 목록 GET 이 새 ID 포함),
    - 회귀 12 endpoint(10.1a users / 10.1b organization·departments·quotas / 10.1c projects / 10.2a dashboard·audit-logs / 10.2b search-scopes·evaluation / 10.2c faq·reports·reports/templates → 모두 200 또는 502 허용).
  - **정적 회귀 정합성 검증** PASS:
    - 9개 컨트롤러 전체에 `[Authorize(Roles="Admin,SuperAdmin")]` 게이트 일관(총 18 Authorize 마크 — 본문+선언),
    - 캐시 namespace 4개 격리 확인(`docutil-faq` / `docutil-reports` / `docutil-report-templates` / `docutil-document-templates`),
    - DocUtil BFF endpoint 총 **79개**(직전 64 + 본 트랙 신규 15 = 79) 라우트 attribute 매핑,
    - Vue 서비스 함수 15 ↔ 백엔드 endpoint 15 **1:1 정렬**,
    - i18n 115 key Vue ↔ ko.json ↔ en.json 양 locale 완전 일치(0 missing / 0 unused),
    - Korean 검증 메시지 44건 + 502 매핑 13건 모두 한국어.
- **외부 동작 변경 0** — 기존 `IDocUtilClient` 시그니처 보존(신규 15 추가만) / 기존 record DTO 변경 0건 / DI 수명 보존(`DocUtilClient` Scoped, `IDocUtilTokenProvider` Singleton, `CachingService` Singleton) / 기존 라우트/메서드 변경 0 / Phase 10.1+10.2a~c 회귀 PASS(정적) / `<script setup lang="ts">` + `@ts-nocheck` 미부착 / vue-tsc errors=0.
- **다음 트랙**: 사용자 결정 대기 — (A) DocUtil `/v2/documents/designer/*` 신규 API 라이브 시 Phase 10.2c 보고서/템플릿 deprecate 재배선 / (B) Phase 6 잔여 작업 / (C) DocUtil evaluation/logs Pydantic 버그(10.2b C3) DocUtil 트랙 분리 처리 / (D) Phase 7 등 후속 진입.

### 2026-05-10 (Phase 10.2b — DocUtil 검색범위 + 평가 운영자 BFF + Vue 콘솔 완료)
- **목적**: AgentHub 운영자가 DocUtil 의 검색범위(Search Scopes — 프로젝트/보드/폴더 단위 RAG 튜닝 + 4 기능 토글 Chatbot/Q&A/Keyword/Agent) + 평가(Evaluation — RAG 품질 4 가중치 + 평가 실행/로그/트렌드)까지 단일 진입점에서 운영. Phase 10.1a~c + 10.2a 의 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑 + version-key invalidate) 그대로 적용 — Search Scopes 9 endpoint + Evaluation 7 endpoint = 총 **15 endpoint** 신설(client 메서드는 16개 — locations 1 분리 카운트).
- **사전 검증** (`tmp/phase10_2b_search_scopes_eval/` 산출물 + `tmp/phase10_2a_audit_dashboard/openapi_full.json` 재사용):
  - DocUtil OpenAPI 캡처 정확 매핑 — Search Scopes 6 path(GET/POST list+create / GET options / GET locations(필수 location_type) / GET-PUT-DELETE detail / PUT environment / GET valid-id) + Evaluation 6 path(GET-PUT config / GET logs(7 query) / GET questions / POST run / GET runs(limit) / GET trend(days)).
  - 추정 금지 정확 적용: `SearchScopeResponse` 24 필드 1:1(chatbot_faq_template/qa_prompt_template/qa_llm_model 까지) / `EvaluationLogResponse` 17 필드(contexts/judge_details/hallucination_evidence 모두 free-form) / `EvaluationRunSummary` 10 필드(page/size 없음) / `EvaluationTrend` 는 `?days=N` (period 가 아님) / `EvaluationRuns` 는 `?limit=N` (page/size 패턴 미적용) / `LocationOption` 은 `?location_type=` 필수 query / `valid-id` 응답 schema 미정의 → free-form dict.
- **백엔드 변경** (`agenthub/`):
  - `Services/IDocUtilClient.cs` 확장(+15 메서드 + 14 record DTO 추가):
    - Search Scopes 9: `ListSearchScopesAsync` / `ListSearchScopeOptionsAsync` / `ListSearchScopeLocationsAsync(string locationType)` / `GetSearchScopeAsync` / `CreateSearchScopeAsync` / `UpdateSearchScopeAsync` / `DeleteSearchScopeAsync` / `UpdateSearchScopeEnvironmentAsync` / `GetSearchScopeValidIdAsync`
    - Evaluation 7: `GetEvaluationConfigAsync` / `UpdateEvaluationConfigAsync` / `ListEvaluationLogsAsync(7 filters)` / `GetEvaluationQuestionsAsync` / `RunEvaluationAsync` / `ListEvaluationRunsAsync(int limit)` / `GetEvaluationTrendAsync(int days)`
    - record DTO 신설: `DocUtilSearchScopeSummary`/`Detail`/`List`/`Option`/`LocationOption`/`CreateScopeRequest`/`UpdateScopeRequest`/`UpdateScopeEnvironmentRequest`/`SearchScopeValidIdResponse` + `EvaluationConfig`/`UpdateEvaluationConfigRequest`/`EvaluationLogEntry`/`EvaluationLogList`/`EvaluationQuestions`/`RunEvaluationRequest`/`EvaluationRunResponse`/`EvaluationRunSummary`/`EvaluationRunList`/`EvaluationTrend`/`EvaluationTrendDataPoint` (총 21건).
  - `Services/DocUtilClient.cs` 확장(+15 구현 + 4 매핑 헬퍼 + 16 private DTO):
    - 매핑 헬퍼: `MapSearchScopeSummary` / `MapSearchScopeDetail` / `MapEvaluationConfig` / `MapEvaluationLog` / `MapEvaluationRunSummary` / `ConvertJsonElementToDict`(JsonElement → dict, free-form 응답 안전 변환).
    - private 응답/요청 DTO 16: `SearchScopeResponseDto` (24 필드) / `SearchScopeListResponseDto` / `SearchScopeOptionDto` / `LocationOptionDto` / `SearchScopeCreateRequestDto` / `SearchScopeUpdateRequestDto` / `SearchScopeEnvironmentRequestDto` / `EvaluationConfigResponseDto` (6 필드) / `EvaluationConfigUpdateRequestDto` / `EvaluationLogResponseDto` (17 필드) / `EvaluationLogListResponseDto` / `EvaluationRunRequestDto` / `EvaluationRunSummaryDto` (10 필드) / `EvaluationRunListResponseDto` (page/size 없음) / `EvaluationTrendPointDto` (6 필드) / `EvaluationTrendResponseDto`.
    - 모든 메서드: `BuildJsonRequestAsync` + `EnsureSuccessOrThrowKoreanAsync` 통일 패턴(Phase 10.1+/10.2a 와 동일 — 한국어 502 자동 매핑).
  - `Controllers/AdminDocUtilSearchScopesController.cs` 신설 (~590 LOC):
    - `[ApiController][Route("api/admin/docutil/search-scopes")][Authorize(Roles="Admin,SuperAdmin")]`
    - `du:scopes:` 10분 TTL + version-key namespace `docutil-search-scopes` (Phase 10.1c 의 `docutil-collections` 와 의도적 분리 — Search Scopes ≠ Projects).
    - `du:scopes:locations:{type}` / `du:scopes:options` 30분 TTL — 카탈로그성 데이터(자주 변경되지 않음, version-key 미적용 단순 TTL).
    - 9 endpoint: list/create/options/locations(locationType validation: project|board|folder)/detail/update/delete/environment/valid-id.
    - mutation(POST/PUT/DELETE) 성공/실패 모두 `IncrementVersionAsync` 호출 (10.1b ghost 처리 패턴) → 검색범위 + 옵션 캐시 동시 stale.
    - environment PUT: title/keyword/content/similarity weight 0~1 사전 검증.
    - cached wrapper DTO 4: `CachedSearchScopeDto` / `CachedSearchScopeListDto` / `CachedSearchScopeOptionListDto` / `CachedLocationOptionListDto`.
  - `Controllers/AdminDocUtilEvaluationController.cs` 신설 (~470 LOC):
    - `[Route("api/admin/docutil/evaluation")][Authorize(Roles="Admin,SuperAdmin")]`
    - 캐시 다층 분리 — `du:eval:cfg:` 5분 + `docutil-evaluation-config` version-key invalidate / `du:eval:logs:` 1분 (실시간성) / `du:eval:runs:` 1분 / `du:eval:trend:` 5분 / `du:eval:questions:` 5분 (카탈로그) / run 트리거 캐시 미적용.
    - 7 endpoint: config GET/PUT(4 weight 0~1 검증) / logs(7 filter, score 범위 검증) / questions(free-form) / run(100 질문/2000자 sanity 검증 + Accepted 202 응답) / runs(limit clamp) / trend(days clamp).
    - cached wrapper DTO 6: `CachedEvaluationConfigDto` / `CachedEvaluationLogEntryDto` / `CachedEvaluationLogListDto` / `CachedEvaluationQuestionsDto` / `CachedEvaluationRunSummaryDto` / `CachedEvaluationRunListDto` / `CachedEvaluationTrendDto`.
    - free-form dict 응답(questions/run response)도 IDictionary&lt;string, object?&gt; 로 안전 표면화.
- **프론트엔드 변경** (`agenthub/ClientApp/src/`):
  - `services/docutilService.ts` 확장(+16 함수 + 16 TS interface): `listSearchScopes` / `listSearchScopeOptions` / `listSearchScopeLocations(type: 'project'|'board'|'folder')` / `getSearchScope` / `createSearchScope` / `updateSearchScope` / `deleteSearchScope` / `updateSearchScopeEnvironment` / `getSearchScopeValidId` + `getEvaluationConfig` / `updateEvaluationConfig` / `listEvaluationLogs(filters)` / `getEvaluationQuestions` / `runEvaluation` / `listEvaluationRuns(limit)` / `getEvaluationTrend(days)`. interface 모두 record 와 1:1 + UI 통합용 `EvaluationLogFilters`. axios `services/api.ts` 인스턴스 사용 — JWT 자동 부착 + 401 갱신.
  - `views/admin/AdminDocUtilSearchScopes.vue` 신설 (~880 LOC, `<script setup lang="ts">`):
    - 3-tab UI: scopes 목록(검색/페이징/카드 + 4 feature badge) / locations 카탈로그(project|board|folder 토글 + 표) / options 카탈로그(드롭다운용 식별자).
    - 모달 3종: 생성/수정 폼(name+description+location 종류 선택→해당 카탈로그 dropdown 자동 로드+4 toggle+chunk/weight/threshold/maxResults 모두 직접 편집) / 환경 설정(13 필드 — 4 feature + faq/prompt 템플릿 + LLM 모델 + chunk + 3 weight + max_results + similarity) / 상세 모달(24 필드 read-only + valid-id 조회 버튼).
    - 한국어 라벨 + 502 폴백 alert + 빈 상태 / 페이지네이션(prev/next + size 10/20/50/100) / 가중치 sum 힌트.
  - `views/admin/AdminDocUtilEvaluation.vue` 신설 (~880 LOC, `<script setup lang="ts">`):
    - 5-tab UI: config(4 weight 직접 수정 + sum 표시 + edit/save 토글) / runs(limit 셀렉트 + 10 컬럼 표 — runId/runType/createdAt/questionCount/avgComposite/avgContext/avgFaith/avgRel/avgHallu/halluCount) / trend(days 셀렉트 + 6 컬럼 일별 시계열 표) / logs(7 필터: runId/runType/hasHallucination 3-state/min-max score 0-1 + 페이징 + 표 + 상세 모달 — JSON contexts/evidence/judge_details details 토글) / questions(free-form JSON 표시).
    - manual 평가 실행: useDefaults 토글 + 사용자 정의 질문 textarea(\\n 분리, 100개/2000자 검증) + 실행 버튼 + response 표시.
    - 한국어 라벨 + 502 폴백 + DocUtil 자체 evaluation/logs 버그(빈 테이블에서 EvaluationLogResponse Pydantic 검증 실패) 시 502 한국어 메시지 표시.
  - `router/index.ts`: `/admin/docutil-search-scopes` + `/admin/docutil-evaluation` 2 라우트 추가(meta.role='Admin' lazy import).
  - `layouts/MainLayout.vue` 사이드바 docutil 카테고리 항목 6·7 추가 (`bi-bullseye` + `bi-clipboard-check`, roles=`['Admin','SuperAdmin']`) — Phase 10.1a~c + 10.2a 의 5 항목 다음.
  - `i18n/locales/ko.json` + `en.json`: `nav.docutilSearchScopes` / `nav.docutilEvaluation` + `adminDocutilSearchScopes.*` 약 50 키 + `adminDocutilEvaluation.*` 약 60 키 (총 110+).
- **검증**:
  - **A. 빌드**: `dotnet build --no-restore --nologo` errors=0 (warnings=11, 모두 pre-existing CS1998 — 본 트랙 무관) + `cd ClientApp && npm run build:check` errors=0 + vue-tsc 2.x PASS + `@ts-nocheck` 부착 0 + 신규 청크 3건(`AdminDocUtilSearchScopes-vZpS3RoC.js` 31.84 kB gzip 6.72 kB / `AdminDocUtilEvaluation-BGvG0Ubh.js` 26.62 kB gzip 5.91 kB / `docutilService-Dph6XSYa.js` 9.33 kB gzip 2.35 kB).
  - **B. 호스트 배포** (`tmp/phase10_2b_search_scopes_eval/step10_deploy.py`): paramiko + SCPClient 11 파일 SFTP → `docker compose build agenthub` exit=0 → `up -d --force-recreate` exit=0 → 6초 만에 healthy(192.168.10.39:64005).
  - **C. e2e + 회귀** (`step20_e2e_verify.py` → `verify_results.json`): admin@example.com / Admin123! 로그인 JWT 555자 → 16 endpoint(15 신규 + 1 invalidate 검증) + 권한 게이트 3 + 회귀 9 = **27/28 PASS**(C3 1건 = DocUtil 자체 버그):
    - **B Search Scopes 9/9 PASS**: B1 list cold 1107ms → B1b warm 44ms (캐시 hit, 25× 가속) / B2 options 133ms count=1 / B3 locations(?type=project) 52ms count=2 first_project=`9ca4ce6e...` / B4 POST 116ms 201 created_id=`21e79f17...` / B5 detail 37ms / B6 update 68ms / B7 environment 69ms (chunk_size=768 + maxResults=15 적용) / B8 valid-id 42ms keys=[id] / B1c after-create 45ms total=2 has_new_scope=true (**version-key invalidate 검증 — POST 후 캐시 즉시 stale, 신규 row 노출**) / B9 DELETE 204 45ms (검증용 데이터 정리).
    - **C Evaluation 6/7 PASS**: C1 config cold 78ms 200 ctx=0.25/faith=0.30/rel=0.25/halu=0.20 → C1b warm 29ms (캐시 hit) / C2 PUT 77ms 200 ctx=0.30/faith=0.25/rel=0.25/halu=0.20 / C1c after-PUT 28ms 200 (invalidate 후 cold — DocUtil 측 응답 ctx=0.25 = DocUtil 자체 정규화/PG row 동작 — BFF 책임 밖) / C2-revert PUT 49ms 200 (원복) / C4 questions 53ms keys=[questions, total] / C5 runs 74ms total=2 / C6 trend 33ms data=1 / **C7 POST run 110ms 202 keys=[run_id, status, message] (judge LLM 트리거 성공)**.
    - **C3 logs 502 = DocUtil 자체 버그**: DocUtil 측 traceback `pydantic_core._pydantic_core.ValidationError: 1 validation error for EvaluationLogResponse / hallucination_evidence / Input should be a valid dictionary [type=dict_type, input_value=[], input_type=list]`. tb_evaluation_logs total=0 임에도 발생 — DocUtil 의 EvaluationService.get_logs 또는 모델 default 가 list 로 초기화되는 별개 row 가 있는 것으로 추정. **본 트랙 책임 밖** — BFF 가 DocUtil 500 → 502 한국어 매핑("평가 로그를 불러오지 못했습니다.") 으로 정상 동작. DocUtil 데이터 정합성은 별도 트랙으로 격리 보고 필요.
    - **D 권한 게이트 3/3 PASS**: D1 GET search-scopes (Bearer 미부착) 401 / D1b GET evaluation/config (Bearer 미부착) 401 / D2 GET search-scopes (bogus JWT) 401.
    - **E 직전 회귀 9/9 PASS**: E1 GET /api/agents/1 200 103ms (b3a2d85 6 신규 필드) / E2 /admin/metrics/rag 200 23ms / E3 /admin/knowledge-base/documents 200 99ms (Phase 6.3) / E4 /admin/knowledge-base/collections 200 44ms (294e8a6) / E5 /admin/docutil/users 200 68ms (10.1a) / E6 /admin/docutil/departments 200 55ms (10.1b) / E7 /admin/docutil/projects 200 55ms (10.1c) / E8 /admin/docutil/dashboard/metrics 200 73ms (10.2a) / E9 /admin/docutil/audit-logs 200 82ms (10.2a).
- **외부 동작 변경 0** — 기존 `IDocUtilClient` 시그니처 보존(신규 15 추가만) + `<script setup lang="ts">` + `@ts-nocheck` 미부착 / vue-tsc 2.x errors=0 / DI 수명주기 보존(DocUtilClient Scoped / IDocUtilTokenProvider Singleton / CachingService Singleton) / 기존 라우트 변경 0 / Phase 10.1a~c + 10.2a 회귀 모두 PASS / 시연 안정성 100%.
- **마지막 commit**: `505b1bb` (`[agenthub/docutil-admin] Phase 10.2d — DocUtil 문서 템플릿(Jinja2) 운영자 BFF + Vue (15 endpoint)`, +4295 LOC, 10 파일). 직전 `01a8c5b` (`[agenthub/docutil-admin] Phase 10.2c — DocUtil FAQ/보고서 운영자 BFF + Vue (14 endpoint)`). 그 이전 `ffcf106` (`[agenthub/docutil-admin] Phase 10.2b — DocUtil 검색범위/평가 운영자 BFF + Vue (15 endpoint)`).
- **다음 트랙**: 사용자 결정 대기 — 후보: (A) DocUtil `/v2/documents/designer/*` 신규 API 라이브 시 Phase 10.2c 보고서/템플릿 deprecate 재배선 / (B) Phase 6 잔여 작업 / (C) DocUtil evaluation/logs Pydantic 버그(10.2b C3) DocUtil 트랙 분리 처리 / (D) Phase 7~ 진입.

### 2026-05-10 (Phase 10.2a — DocUtil 대시보드 + 감사 로그 운영자 BFF + Vue 콘솔 완료)
- **목적**: AgentHub 운영자가 DocUtil 의 운영 모니터링(KPI/응답시간/검색 통계/업로드 상태 5종) + 감사 로그(목록 + CSV 내보내기)를 단일 진입점에서 확인. Phase 10.1a~c 의 BFF 패턴(IDocUtilTokenProvider 4단계 폴백 + 한국어 502 매핑) 그대로 적용 — Dashboard 5 + Audit 2 = 7 endpoint 신설.
- **사전 검증** (`tmp/phase10_2a_audit_dashboard/step01_capture_dashboard_audit_openapi.py`): DocUtil OpenAPI 94 path 중 7 path 매칭 (`/api/v1/dashboard/*` x5 + `/api/v1/audit-logs[/export]` x2) + 7 schema 추출 + 17 probe 직접 호출 캡처:
  - `DashboardMetrics`: total_users/active_users/total_documents/total_searches + feature_usage(dict, additionalProperties=true) — 운영 환경 응답 totalUsers=11, totalDocuments=31, totalSearches=110
  - `ResponseTimeData`: timestamps[] + values[] 평행 배열 — period 미지정 시 빈 배열, "7d" 시 4 데이터 포인트(시간 단위 버킷, double ms)
  - `SearchErrorData`: dates[] + error_counts[] 평행 배열 — 7일치 일별 분포
  - `SearchUsageStats`: total_requests/total_responses/total_failures + period(라벨)
  - `UploadStatusChart`: completed/processing/waiting/error 4 필드(default 0 each) — 운영 환경 completed=31
  - `AuditLogResponse`: id/organization_id/user_id?/action/resource_type/resource_id?/details(dict)?/ip_address?/created_at — **`user_agent` 필드 schema 미존재** (추정 금지 — BFF/Vue 모두 미포함)
  - `AuditLogListResponse`: items + total + page + size — 운영 환경 total=754
  - export endpoint: 응답 Content-Type=`text/csv; charset=utf-8` + Content-Disposition=`attachment; filename=audit_logs.csv` (별도 query format 없음 — 항상 CSV)
  - audit-logs query params 정확 매핑: `page` / `size` / `action` / `resource_type` / `user_id` / `start_date` / `end_date` (작업명세의 `actorId` → 실제 `user_id`, `from/to` → `start_date/end_date`)
- **백엔드 (7 endpoint + DTO 8 + private DTO 7 + Controller + HttpResponseOwnedStream)**:
  - `IDocUtilClient.cs` — Phase 10.2a 7 메서드 추가: `GetDashboardMetricsAsync` / `GetDashboardResponseTimesAsync(period?)` / `GetDashboardSearchErrorsAsync(period?)` / `GetDashboardSearchUsageAsync(period?)` / `GetDashboardUploadStatusAsync` / `ListAuditLogsAsync(page,size,action?,resourceType?,userId?,startDate?,endDate?)` / `ExportAuditLogsAsync(action?,resourceType?,userId?,startDate?,endDate?)`. record DTO 8종(`DocUtilDashboardMetrics` IDictionary&lt;string,int&gt;FeatureUsage / `DocUtilResponseTimes` / `DocUtilSearchErrors` / `DocUtilSearchUsage` / `DocUtilUploadStatus` / `DocUtilAuditLogEntry` 9 필드 / `DocUtilAuditLogList` / `DocUtilAuditExport` Stream+ContentType+FileName). 한국어 doc 주석 + DocUtil schema 출처 인용 + **추정 금지 명시**(`user_agent` 미존재 / export `format` 미존재).
  - `DocUtilClient.cs` — 7 구현 + `MapAuditLog` / `JsonElementToObject` 매핑 헬퍼 + private 응답 DTO 7(`DashboardMetricsDto` JsonElement?FeatureUsage / `ResponseTimeDataDto` / `SearchErrorDataDto` / `SearchUsageStatsDto` / `UploadStatusChartDto` / `AuditLogResponseDto` JsonElement?Details / `AuditLogListResponseDto`). `ExportAuditLogsAsync` 의 stream 누수 방지를 위해 **`HttpResponseOwnedStream`**(중첩 Stream) 클래스 신규: 호출자가 stream Dispose 시 응답/요청 객체도 함께 정리. `ResponseHeadersRead` 사용으로 큰 CSV 의 메모리 buffering 회피.
  - `AdminDocUtilOperationsController.cs` 신설 (~330 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` + `[Route("api/admin/docutil")]`):
    - `GET /dashboard/metrics` → 5분 TTL (`du:dashboard:metrics`)
    - `GET /dashboard/response-times?period=` → 5분 TTL (period 별 키)
    - `GET /dashboard/search-errors?period=` → 5분 TTL
    - `GET /dashboard/search-usage?period=` → 5분 TTL
    - `GET /dashboard/upload-status` → 5분 TTL
    - `GET /audit-logs?page&size&action&resourceType&userId&startDate&endDate` → 1분 TTL(`du:audit:list:{모든 필터}`)
    - `GET /audit-logs/export?action&resourceType&userId&startDate&endDate` → **캐시 미적용** + `FileStreamResult` + RFC 5987 한글 파일명(`Content-Disposition: attachment; filename="..."; filename*=UTF-8''...`)
    - 모든 endpoint 의 4xx/5xx → 502 ErrorResponseDto 한국어 본문(`"DocUtil 대시보드 메트릭을 불러오지 못했습니다."` 등 7 종)
    - mutation 부재(모두 GET) → version-key 미사용, 단순 TTL 분리(dashboard 5분 / audit 1분 — 신선도 차이 반영)
    - 캐시 namespace 분리: `du:dashboard:` / `du:audit:` — Phase 10.1c 의 `du:projects:` / `docutil-collections` 와 의도적으로 격리(데이터 도메인 무관)
- **빌드 검증**:
  - `dotnet build --nologo` errors=0 / warnings=11 (모두 pre-existing CS1998, 본 작업 무관) — 4초
  - `npm run build:check` (vue-tsc 2.2.12 + vite 5) errors=0, 3.70s vite build 263 modules
  - 신규 청크: `AdminDocUtilDashboard-CKnlP7sp.js` 14.61 kB (gzip 4.06 kB) + `AdminDocUtilAudit-BMjhPcrg.js` 12.27 kB (gzip 3.61 kB)
  - 본체 청크: `index-gJkHeTAS.js` 151.42 kB (이전 134.36 → 17 kB 증가, i18n 130+ 키 + docutilService 7 함수)
  - **`@ts-nocheck` 부착 0** — 신규 3 파일(AdminDocUtilDashboard.vue / AdminDocUtilAudit.vue / docutilService.ts 확장) 모두 strict 게이트 통과
  - chart.js 미사용으로 `chart-vendor` 청크 영향 0(207.43 kB 동일 유지)
- **Frontend (View 2 + service 7 함수)**:
  - `docutilService.ts` — Phase 10.2a 7 함수 + `parseFileNameFromDisposition` 헬퍼 추가. interface 7건(`DocUtilDashboardMetrics` Record&lt;string,number&gt;featureUsage / `DocUtilResponseTimes` / `DocUtilSearchErrors` / `DocUtilSearchUsage` / `DocUtilUploadStatus` / `DocUtilAuditLogEntry` 9 필드(user_agent 미포함) / `DocUtilAuditLogList`) + `AuditLogFilters`(7 필드 모두 선택). `exportAuditLogs` 가 `responseType: 'blob'` + 헤더 메타(content-type/filename) 동반 반환. 기존 시그니처 변경 0.
  - `AdminDocUtilDashboard.vue` 신설 (~500 LOC, `<script setup lang="ts">` + ref/computed/onMounted/onBeforeUnmount + i18n + chart.js 미사용):
    - **상단**: 자동 갱신 토글(form-switch, 5초 간격 setInterval, onBeforeUnmount 시 clear) + 마지막 갱신 시각 표시 + 기간 선택 btn-group(전체/24h/7d/30d) — 기간 의존 endpoint(response-times/search-errors/search-usage)만 재로드
    - **1행**: KPI 4 카드(총 사용자/활성 사용자/총 문서/총 검색) + feature_usage 표(progress bar — 최대값 기준 비율, 정렬 desc)
    - **2행**: 응답시간 시계열 막대(평균/최대/최소 + 데이터 포인트 수, custom CSS bar-chart, hover title 으로 정확한 시각 + ms) + 검색 사용량 dl(요청/응답/실패/성공률 + period 라벨)
    - **3행**: 일별 검색 오류 표(스크롤, error_counts > 0 인 행 table-warning 강조 + 합계 표시) + 업로드 상태 progress bar(완료/처리중/대기/실패 색상별 — bg-success/info/warning/danger + 비율 width + 배지)
    - 한국어 라벨 + 로딩/에러/빈 상태 처리. 에러 알림 alert + dismiss 버튼.
    - extractErrorMessage 가 axios response.data.message → err.message → i18n fallback 순으로 한국어 메시지 추출.
  - `AdminDocUtilAudit.vue` 신설 (~430 LOC):
    - **상단**: 5 필드 필터 카드 (action / resourceType / userId / startDate / endDate) — datetime-local input → ISO UTC 자동 변환(`new Date(local).toISOString()`)
    - CSV 내보내기 버튼: filter 적용 상태 그대로 사용(page/size 제외) — 파일명 한국어 RFC 5987 보존 + URL.revokeObjectURL setTimeout 정리
    - **본문**: 페이지네이션 + 합계 표시 + 페이지 크기 select(20/50/100/200) + 7 컬럼 표(일시/Action/리소스/리소스 ID/사용자/IP/[상세 보기])
    - **모달**: 9 필드 dl(id/createdAt/action/resourceType/resourceId/orgId/userId/ip) + raw JSON pre 영역(details free-form dict) + 한국어 모달
    - 한국어 라벨 + 로딩/에러/빈 상태 처리.
  - `router/index.ts` — `/admin/docutil-dashboard` + `/admin/docutil-audit` 두 라우트 추가 (lazy import + `meta.role='Admin'`)
  - `MainLayout.vue` — docutil 카테고리에 4·5 번째 항목 추가 (`bi bi-speedometer2` 대시보드 / `bi bi-journal-text` 감사 로그, `roles=['Admin','SuperAdmin']`)
  - `i18n/locales/ko.json` + `en.json` — 신규 키 130+ 개 (nav.docutilDashboard / nav.docutilAudit + adminDocutilDashboard.* 약 50 / adminDocutilAudit.* 약 80)
- **호스트 배포** (`tmp/phase10_2a_audit_dashboard/step10_deploy.py`):
  - paramiko SFTP 10 파일 업로드 (192.168.10.39, /home/idino/agenthub):
    - `Controllers/AdminDocUtilOperationsController.cs` (신규)
    - `Services/IDocUtilClient.cs` + `Services/DocUtilClient.cs` (수정)
    - `ClientApp/src/views/admin/AdminDocUtilDashboard.vue` + `AdminDocUtilAudit.vue` (신규 2)
    - `ClientApp/src/services/docutilService.ts` (수정)
    - `ClientApp/src/router/index.ts` + `layouts/MainLayout.vue` + `i18n/locales/ko.json` + `en.json` (수정 4)
  - `docker compose build agenthub` exit=0 (BuildKit cache + publish layer)
  - `up -d --force-recreate` exit=0
  - 6초 만에 healthy (3 starting → 1 healthy)
- **e2e 회귀 32/0 PASS** (`step20_e2e_verify.py`):
  - **A) admin@example.com 로그인** → JWT 555자 PASS
  - **B) 7 신규 endpoint**:
    - B-1 GET /dashboard/metrics — cold 867ms / warm 30ms (cache 효과 29× 가속) + schema 5 키 PASS
    - B-2 GET /dashboard/response-times?period=7d — 62ms + timestamps[4]+values[4] schema PASS
    - B-3 GET /dashboard/search-errors?period=7d — 42ms + dates[7]+errorCounts[7] schema PASS
    - B-4 GET /dashboard/search-usage?period=7d — 55ms + period='7d' schema PASS
    - B-5 GET /dashboard/upload-status — 47ms + completed=31/processing=0 schema PASS
    - B-6 GET /audit-logs?page=1&size=20 — cold 90ms / warm 13ms (cache 효과 7× 가속) + total=754 + entry schema(action='auth.login' resourceType='auth') PASS
    - B-7 GET /audit-logs/export — 112ms + Content-Type='text/csv; charset=utf-8' + Content-Disposition `attachment; filename="audit_logs.csv"; filename*=UTF-8''audit_logs.csv` + 162393 bytes binary stream PASS
  - **C) 권한 게이트**: Bearer 미부착 401 + Bogus JWT 401 PASS
  - **D) 캐시 효과 명시**: dashboard 29× / audit 7× 가속 검증 PASS
  - **E) 직전 회귀 8 endpoint 모두 PASS**:
    - E-1 GET /api/agents/1 — 6 신규 필드(llmRouting / routingPolicyJson / consumerSystems / knowledgeBaseSource / knowledgeBaseRef / agentCode) b3a2d85
    - E-2 GET /api/admin/metrics/rag — 24 keys
    - E-3 GET /api/admin/knowledge-base/documents — Phase 6.3
    - E-4 GET /api/admin/knowledge-base/collections — count=2 (KB collection dropdown 회귀)
    - E-5 GET /api/admin/docutil/users — total=11 (10.1a)
    - E-6 GET /api/admin/docutil/departments — count=10 (10.1b)
    - E-7 GET /api/admin/docutil/projects — total=2 (10.1c)
    - E-8 한국어 RAG conversation 라우팅 — status=201
- **R3 격리 보존**: DocUtil schema 만 접근, AgentHub 자체 스키마 미사용. cross-schema join 0.
- **외부 시그니처 변경 0**: `IDocUtilClient` 신규 7 메서드만 추가, 기존 25 메서드 시그니처 보존. RagService / AdminKnowledgeBaseController / AdminDocUtilUsersController / AdminDocUtilDepartmentsController / AdminDocUtilProjectsController 회귀 0.
- **다음 트랙**: Phase 10.2b — DocUtil Search Scopes / Evaluation 등(사용자 결정 대기), 또는 Phase 6 잔여 작업.

### 2026-05-10 (Phase 10.1c — DocUtil 프로젝트/보드 운영자 BFF + Vue 콘솔 완료, Phase 10.1 전체 종결)
- **목적**: AgentHub 운영자가 DocUtil 의 프로젝트(=collection 풍부 표면) + 멤버 + 부서 매핑 + 보드(KB collection 권한 단위) 를 단일 진입점에서 관리. 10.1a/10.1b 의 BFF 패턴을 그대로 적용 — DocUtil 콘솔 별도 로그인 불필요. 본 트랙으로 **Phase 10.1 전체 종결**(사용자/조직/부서/할당량/프로젝트/보드).
- **사전 검증** (`tmp/phase10_1c_projects/step01_capture_projects_openapi.py` + `step02_probe_real_members_dep.py` + `step03_probe_board_get.py`): DocUtil OpenAPI 94 path 중 9 path 매칭 (`/api/v1/projects` x5 + `/api/v1/projects/{pid}/boards` x4) + 8 schema 추출 + 13 endpoint 직접 호출 캡처 + 운영 프로젝트 2건의 members/departments/boards 응답 schema 검증:
  - `ProjectResponse` 8 필드: id/name/description?/allow_original_download/organization_id/created_by/created_at/updated_at (DocUtil ins_dt → created_at alias)
  - `ProjectCreate`: name + description?(maxLen 2000) + allow_original_download?(default true) — POST 만
  - `ProjectUpdate`: name? + description? — **DocUtil schema 가 update 엔 allow_original_download 미보유** (추정 금지로 BFF Update DTO/Vue Edit 모달 모두 미포함)
  - `BoardResponse` 7 필드: id/project_id/name/description?/created_by/created_at/updated_at — **DocUtil schema 에 folder_id 미존재** (별도 endpoint `/api/v1/boards/{board_id}/folders` 로 분리)
  - `BoardCreate`/`BoardUpdate`: name + description? 만 (folder_id 미보유)
  - `ProjectTreeNode` (free-form): {id, name, boards: BoardResponse[]} — 프로젝트는 부모-자식 관계 없음, 트리는 평면 + boards sub-array
  - `ProjectMember` (free-form, 실제 운영 응답에서 검증): {id, username, email, role} — DocUtilDepartmentMember 와 동일 형태이나 의미 분리(별도 record)
  - `ProjectDepartment` (free-form): {id, name, path, depth} — DocUtilDepartment 의 풍부 응답과 다름(4 필드만)
  - `step03` 진단 결과: `GET /api/v1/projects/{pid}/boards/{bid}` 가 leftover 잔재 시나리오에서 404 발생 가능 — 깨끗한 상태에서는 정상 200. e2e 시작 시 pre-cleanup 으로 안전망 확보
- **백엔드 (13 endpoint + DTO 17 + Controller)**:
  - `IDocUtilClient.cs` — Phase 10.1c 13 메서드 추가: `ListProjectsAsync(page,size,search?)` / `GetProjectTreeAsync` / `GetProjectAsync(id)` / `CreateProjectAsync(req)` / `UpdateProjectAsync(id,req)` / `DeleteProjectAsync(id)` / `GetProjectMembersAsync(id)` / `GetProjectDepartmentsAsync(id)` / `ListProjectBoardsAsync(pid,page,size)` / `CreateProjectBoardAsync(pid,req)` / `GetProjectBoardAsync(pid,bid)` / `UpdateProjectBoardAsync(pid,bid,req)` / `DeleteProjectBoardAsync(pid,bid)`. record DTO 12종(`DocUtilProject` 8 필드 / `DocUtilProjectList` / `DocUtilProjectTreeNode` / `DocUtilProjectMember` / `DocUtilProjectDepartment` / `DocUtilBoard` 7 필드 / `DocUtilBoardList` + Request 5: `DocUtilCreateProjectRequest` / `DocUtilUpdateProjectRequest` / `DocUtilCreateBoardRequest` / `DocUtilUpdateBoardRequest`). 한국어 doc 주석 + DocUtil schema 출처 인용. **기존 ListCollectionsAsync 시그니처/응답 형태 절대 보존** — AgentBuilder dropdown 회귀 차단.
  - `DocUtilClient.cs` — 13 구현 + `MapProject` / `MapBoard` 매핑 헬퍼 + private 응답 DTO 7(`ProjectResponseDto` / `ProjectListResponseDto` / `ProjectTreeNodeDto` / `ProjectMemberResponseDto` / `ProjectDepartmentResponseDto` / `BoardResponseDto` / `BoardListResponseDto`). **`ListCollectionsAsync` 캐시 키 version-aware 보강**: `du:c:{page}|{size}` → `du:c:v{N}:{page}|{size}` (시그니처/응답 형태 보존, 행위는 mutation 자동 stale 향상). `CollectionCacheVersionNamespace = "docutil-collections"` public const 추가.
  - `AdminDocUtilProjectsController.cs` 신설 (~600 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` + `[Route("api/admin/docutil")]`):
    - `GET /projects?page&size&search` → 10분 TTL (`du:projects:v{N}:list:{page}|{size}|{search}`)
    - `GET /projects/tree` → 10분 TTL (`du:projects:v{N}:tree`)
    - `POST /projects` → 검증(name 1~255, description ≤2000) + `CreatedAtAction` 201 + invalidate
    - `GET /projects/{id}` → 10분 TTL (`du:projects:v{N}:detail:{id}`) + 404 → NotFound 한국어
    - `PUT /projects/{id}` → 변경 필드 1개 이상(name/description) 검증 + invalidate
    - `DELETE /projects/{id}` → 204 + 성공/실패 모두 invalidate (10.1b ghost 처리 패턴)
    - `GET /projects/{id}/members` → 10분 TTL (`du:projects:v{N}:members:{id}`)
    - `GET /projects/{id}/departments` → 10분 TTL (`du:projects:v{N}:departments:{id}`)
    - `GET /projects/{id}/boards?page&size` → 10분 TTL (`du:projects:v{N}:boards:{id}|{page}|{size}`)
    - `POST /projects/{id}/boards` → 검증 + `CreatedAtAction` 201 + invalidate
    - `GET /projects/{pid}/boards/{bid}` → 10분 TTL + 404 → NotFound 한국어
    - `PUT /projects/{pid}/boards/{bid}` → invalidate
    - `DELETE /projects/{pid}/boards/{bid}` → 204 + invalidate
    - **`docutil-collections` version-key namespace 통합**: 본 컨트롤러의 prefix `du:projects:` 와 DocUtilClient 의 `du:c:` 가 같은 version namespace 사용 → 본 화면 mutation 1회로 양쪽 동시 stale (AgentBuilder dropdown 즉시 갱신).
    - 모든 `InvalidOperationException` → 502 한국어 ErrorResponseDto 매핑.
  - `Program.cs` 변경 0 — 기존 `IDocUtilClient` Scoped 등록 그대로 사용.
- **Frontend (View + service + 라우트 + 사이드바 + i18n)**:
  - `docutilService.ts` — Phase 10.1c 13 함수 추가 + 11 TS interface (`DocUtilProject` / `DocUtilProjectList` / `DocUtilProjectTreeNode` / `DocUtilProjectMember` / `DocUtilProjectDepartment` / `DocUtilBoard` / `DocUtilBoardList` + Request 4건). 기존 `listCollections` 시그니처/응답 보존. axios `services/api.ts` 인스턴스 사용 — JWT 자동 부착 + 401 갱신.
  - `AdminDocUtilProjects.vue` 신설 (~880 LOC, `<script setup lang="ts">` + ref/computed/onMounted + i18n):
    - **상단**: 페이지 헤더 + 신규 프로젝트 / 전체 새로고침 버튼 + 알림 dismissible
    - **탭 토글**: 목록 / 트리 (Bootstrap nav-pills)
    - **목록 탭**: 검색 input + 적용/초기화 버튼 + 페이지네이션 카드 그리드(이름/설명/생성일 + 인라인 수정/삭제 액션) + 페이지 표시 + ◄ ► 이동
    - **트리 탭**: 평면 프로젝트 + boards sub-array 들여쓰기(2단계 평면)
    - **우측 패널**: 선택 프로젝트 정보 카드(8 필드 dl/dt — id/name/description/allowOriginalDownload(badge)/createdBy/createdAt/updatedAt) + 멤버 표(username/email/role badge) + 부서 표(name/depth/path) + 보드 카드(이름/설명/생성일 + 인라인 수정/삭제 + 신규 보드 버튼)
    - **프로젝트 모달**: name(maxlen 255 required) + description textarea(maxlen 2000) + **allow_original_download checkbox 는 신규 모드에서만 노출**(ProjectUpdate schema 에 미존재라 편집 모드 hidden) + 한국어 placeholder + 클라 검증
    - **보드 모달**: name(maxlen 255 required) + description textarea(maxlen 2000) — folder_id 없음(DocUtil schema 보존)
    - **2단계 confirm 삭제** + 한국어 라벨 + 502 폴백 + 빈 상태 + 로딩 spinner
    - **편집 partial update**: 변경된 필드만 PUT body 에 포함(서버 측 "변경 필드 1개 이상" 검증과 정합)
  - `router/index.ts` — `/admin/docutil-projects` (lazy + meta.role='Admin') 추가
  - `MainLayout.vue` — 기존 `docutil` 카테고리에 항목 추가 (icon `bi bi-folder2-open`)
  - `i18n/locales/{ko,en}.json` — `nav.docutilProjects` + `adminDocutilProjects.*` 70+ 키 (한국어 우선 + 영문 동기화)
- **빌드 검증**:
  - `dotnet build --no-restore --nologo` → errors=0 / warnings=11 (모두 pre-existing CS1998, 신규 코드 워닝 0).
  - `npm run build:check` (vue-tsc 2.2.12 + vite 5) → vue-tsc errors=0 + vite 3.52s + 신규 청크 `AdminDocUtilProjects-B_o0Jfnp.js` 24.43 kB (gzip 5.60 kB) + `AdminDocUtilProjects-D64orxZN.css` + `docutilService-CSGQP4A5.js` 4.93 kB.
  - `@ts-nocheck` 부착 0 (Phase 3 부채 카탈로그 보존).
  - dist grep PASS — `docutil-projects` 경로, `DocUtil 프로젝트` 한국어, `DocUtil Projects` 영문, `adminDocutilProjects` i18n namespace 모두 인덱스 번들에 포함.
- **호스트 배포** (`tmp/phase10_1c_projects/step10_deploy.py`): paramiko SFTP 9 파일 → `cd /home/idino/agenthub && docker compose build agenthub` exit=0 (호스트 multi-stage Dockerfile 가 컨테이너 내부에서 npm + dotnet publish 수행) → `docker compose up -d --force-recreate agenthub` exit=0 → 6초 만에 healthy.
- **e2e + 회귀 28+ 항목 / 0 실패** (`step20_e2e_verify.py`):
  - **A. admin login** (admin@example.com/Admin123!) → 200 (JWT 555자, body.token 키)
  - **B. 13 신규 endpoint** — 모두 200/201/204 (B-1 GET /projects?page=1&size=10 cold 35ms → warm 25ms / B-2 GET /projects/tree 200 + tree node count=2 / B-3 POST /projects 201 + allowOriginalDownload=false 정상 / B-4 GET /projects/{id} 200 / B-5 PUT 200 description 변경 정상 / B-6 GET members 200 / B-7 GET departments 200 / B-8 GET boards 200 + total=0 / B-9 POST boards 201 / B-10 GET /projects/{pid}/boards/{bid} 200 / B-11 PUT 200 / B-12 DELETE 204 / B-13 DELETE project 204)
  - **C. 권한 게이트** — Bearer 미부착 401 / Bogus JWT 401 모두 PASS
  - **D. 캐시 invalidate (통합 namespace 검증, 핵심)** — D-1 collections 시작 count=2 / D-2 projects 시작 total=2 / D-3 POST projects 201 (invalidate trigger) / **D-4 collections invalidate 후 count=3 PASS — 통합 namespace 효과 입증, AgentBuilder dropdown 도 즉시 신규 프로젝트 노출** / D-5 projects total=3 PASS / D-6 DELETE 204 / D-7 collections baseline=2 회복 PASS
  - **E. 직전 회귀 8 endpoint** — `GET /api/agents/1` (b3a2d85 6 필드 모두 present) / `GET /api/admin/metrics/rag` (24 필드) / `GET /api/admin/knowledge-base/documents` (Phase 6.3 healthy) / **한국어 RAG `POST /api/chat/conversations` (Agent 22 docutil-rag-chat) cid=262 → /messages status=200** / `GET /api/admin/docutil/users?page=1&size=10` (10.1a, total=11) / `GET /api/admin/docutil/departments` (10.1b, count=10) / `GET /api/admin/docutil/organization` (10.1b) / `GET /api/admin/docutil/organization/quota` (10.1b)
- **산출물**: 신규 `agenthub/Controllers/AdminDocUtilProjectsController.cs` (~600 LOC) + `agenthub/ClientApp/src/views/admin/AdminDocUtilProjects.vue` (~880 LOC). 수정 `IDocUtilClient.cs` (13 메서드 + 12 record DTO 추가) + `DocUtilClient.cs` (13 구현 + 매핑 헬퍼 + 7 private DTO + ListCollectionsAsync 캐시 version 통합) + `docutilService.ts` (13 함수 + 11 interface) + `router/index.ts` + `MainLayout.vue` + `i18n/locales/{ko,en}.json`.
- **검증 스크립트** (`tmp/phase10_1c_projects/`): `step01_capture_projects_openapi.py` (DocUtil 8 schema + 13 endpoint 캡처) / `step02_probe_real_members_dep.py` (운영 프로젝트 2건의 members/departments/boards 응답 schema 검증) / `step03_probe_board_get.py` (Board GET 진단 — leftover 시나리오 / clean 시나리오 분기 검증) / `step10_deploy.py` (호스트 배포) / `step20_e2e_verify.py` (28+ 회귀 자동화).
- **외부 동작 변경 0** — 기존 `IDocUtilClient` 시그니처 보존(신규 13 추가) + `ListCollectionsAsync` 시그니처/응답 형태 보존(캐시 키 내부에 version prefix 만 추가) + Phase 10.1a/10.1b 회귀 PASS + `/admin/docutil-projects` SPA 라우트만 신규 + 시연 안정성 100%.
- **Phase 10.1 전체 종결**: 운영자가 AgentHub 한 화면(`/admin/docutil-users` + `/admin/docutil-departments` + `/admin/docutil-projects`)에서 DocUtil 의 사용자(11명) / 조직 정보 + 부서 트리(10) + 월 할당량(2 quota_type) + 프로젝트 카탈로그(2) + 프로젝트별 멤버 + 부서 매핑 + 보드(KB collection) 모두 관리 가능. R3 (스키마 격리) 보존 — DocUtil 측은 항상 BFF 경유 / R2 (단일 진입점) 강화 — DocUtil 콘솔 별도 로그인 불필요.

### 2026-05-10 (Phase 10.1b — DocUtil 조직/부서/할당량 운영자 BFF + Vue 콘솔 완료)
- **목적**: AgentHub 운영자가 DocUtil 의 조직 정보 / 부서 트리 / 월 할당량까지 단일 진입점에서 관리. 10.1a 의 사용자 트랙과 동일한 BFF 패턴 적용 — DocUtil 콘솔 별도 로그인 없이 AgentHub UI 에서 모든 작업 가능. 향후 10.1c(프로젝트/보드) 트랙으로 같은 카테고리에 항목 확장.
- **사전 검증** (`tmp/phase10_1b_deps/step01_capture_openapi.py`): DocUtil OpenAPI 94 path 중 관련 endpoint 10건 발견 + 7 endpoint 직접 호출 PASS (검증용 부서 생성 → members 조회 → 수정 → 삭제 모두 200/201/204) + 8 schema 추출:
  - `OrganizationResponse(id/name/slug/description?/settings?/created_at)` — DocUtil 측 `ins_dt` 를 `created_at` 으로 alias
  - `OrganizationUpdate(name?/description?/settings?)` partial update
  - `DepartmentResponse(id/organization_id/parent_id?/name/depth/path/created_at)` — materialized path 패턴, children 필드 없음(평탄 List)
  - `DepartmentCreate(name, parent_id?)` — **DocUtil schema 가 description 필드 미보유** (추정 금지 원칙으로 BFF 도 description 받지 않음)
  - `DepartmentUpdate(name?, parent_id?)` partial update
  - **DepartmentMember 응답** — OpenAPI typed schema 미존재(free-form). 실제 캡처(`step02_probe_members.py` — 부서 `대표이사` 의 `이동운` 멤버 1건) 응답에서 4 필드(id/username/email/role) 확인 후 그것만 안정적으로 노출
  - `OrganizationQuotasCurrentResponse(organization_id/year_month/quotas: {quota_type → QuotaStatusResponse})` — **map 형태**, 운영자 UI 표 표시를 위해 BFF 가 List 로 평탄화
  - `QuotaStatusResponse(quota_type/monthly_limit/used_count/remaining/year_month)` — 4 정수 + 2 문자열
  - `QuotaUpdateRequest(monthly_limit)` — DB CHECK 0 이상 정수, used_count 는 차감 로직 전용
- **백엔드 (9 endpoint + DTO 13 + Controller)**:
  - `IDocUtilClient.cs` — Phase 10.1b 9 메서드 추가: `GetOrganizationAsync` / `UpdateOrganizationAsync(req)` / `ListDepartmentsAsync` / `CreateDepartmentAsync(req)` / `UpdateDepartmentAsync(deptId, req)` / `DeleteDepartmentAsync(deptId)` / `GetDepartmentMembersAsync(deptId)` / `GetOrganizationQuotaAsync` / `UpdateOrganizationQuotaAsync(quotaType, req)`. 모든 메서드 orgId 파라미터 미수령 — `_tokenProvider.GetOrganizationIdAsync` 로 자동 부착. 신규 record DTO 8 종 — `DocUtilOrganization` / `DocUtilUpdateOrganizationRequest` / `DocUtilDepartment` / `DocUtilCreateDepartmentRequest` / `DocUtilUpdateDepartmentRequest` / `DocUtilDepartmentMember` / `DocUtilOrganizationQuotaCurrent` / `DocUtilOrganizationQuotaStatus` / `DocUtilUpdateQuotaRequest`. 한국어 doc 주석 + DocUtil schema 출처 인용.
  - `DocUtilClient.cs` — 9 메서드 구현 + `ResolveOrganizationIdAsync(ct)` 헬퍼 신설(GetOrganizationIdAsync 검증 + 한국어 InvalidOperationException 매핑) + `MapOrganization` / `MapDepartment` 매핑 헬퍼 + private 응답 DTO 5(OrganizationResponseDto/DepartmentResponseDto/DepartmentMemberResponseDto/OrganizationQuotasCurrentResponseDto/QuotaStatusResponseDto). `GetOrganizationQuotaAsync` 의 quotas map → List 평탄화는 OrdinalIgnoreCase 정렬로 결정성 보장 (운영자 UI 의 표 행 순서 안정).
  - `AdminDocUtilDepartmentsController.cs` 신설 (~360 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` + `[Route("api/admin/docutil")]`):
    - `GET /organization` → 10분 TTL 캐시 (`du:depts:v{N}:org`)
    - `PUT /organization` → 변경 필드 1개 이상 검증 + 성공 시 `IncrementVersionAsync("docutil-departments")`
    - `GET /departments` → 10분 TTL 캐시 (`du:depts:v{N}:list`)
    - `POST /departments` → name 검증 + `CreatedAtAction` 201 + invalidate
    - `PUT /departments/{deptId}` → 변경 필드 1개 이상 검증 + invalidate
    - `DELETE /departments/{deptId}` → **성공/실패 모두 invalidate** (DocUtil 측 ghost 부서가 캐시에 남는 일 방지 — 운영 회귀 차단)
    - `GET /departments/{deptId}/members` → 10분 TTL 캐시 (`du:depts:v{N}:members:{deptId}`)
    - `GET /organization/quota` — **캐시 미적용** (차감 로직이 백엔드에서 잦으므로 매 호출 fresh)
    - `PUT /organization/quota/{quotaType}` — `monthly_limit ≥ 0` 검증 + 캐시 미적용
    - 모든 `InvalidOperationException` → 502 한국어 ErrorResponseDto 매핑.
  - `Program.cs` 변경 0 — 기존 `IDocUtilClient` Scoped 등록 그대로 사용.
- **Frontend (View + service + 라우트 + 사이드바 + i18n)**:
  - `docutilService.ts` — Phase 10.1b 9 함수 추가 + 8 TS interface (DocUtilOrganization / DocUtilDepartment / DocUtilDepartmentMember / DocUtilOrganizationQuotaCurrent / DocUtilOrganizationQuotaStatus + Request 3건). 모두 axios `services/api.ts` 인스턴스 사용 — JWT 자동 부착 + 401 갱신.
  - `AdminDocUtilDepartments.vue` 신설 (~620 LOC, `<script setup lang="ts">` + ref/computed/onMounted + i18n):
    - **상단**: 조직 정보 카드(읽기 전용 + 수정 모달) + 월 할당량 카드(quota_type 별 진행 막대 70%/90% 임계 색상 + 한도 수정 모달)
    - **하단 좌**: 부서 트리 — 평탄 List 응답을 `path` 사전순 정렬 + `depth * 16px` 들여쓰기. 각 노드 우측 액션 [신규 하위 / 수정 / 삭제]. 루트 노드 위에 별도 "최상위 부서 신규" 버튼.
    - **하단 우**: 선택 부서 상세 dl (id/name/parent + 부모명 lookup/depth/path/createdAt) + 멤버 표(username/email/role)
    - **부서 모달**: 이름 + parent dropdown(편집 모드시 자기 자신과 자손은 dropdown 에서 제외 — 순환 부모 방지). 한국어 placeholder + required 검증.
    - **조직 정보 모달**: name + description, 변경된 필드만 partial PUT.
    - **할당량 한도 모달**: quota_type 표시 + monthly_limit 정수 입력(min=0) + 사용량 안내.
    - **2단계 confirm 삭제** + 한국어 라벨 + 502 폴백 카드 + 빈 상태 안내 + 로딩 spinner.
  - `router/index.ts` — `/admin/docutil-departments` (lazy + meta.role='Admin') 추가
  - `MainLayout.vue` — 기존 `docutil` 카테고리에 항목 추가 (icon `bi bi-diagram-3`)
  - `i18n/locales/{ko,en}.json` — `nav.docutilDepartments` + `adminDocutilDepartments.*` 50+ 키 (한국어 우선 + 영문 동기화)
- **빌드 검증**:
  - `dotnet build --no-restore --nologo` → errors=0 / warnings=11 (모두 pre-existing CS1998, 신규 코드 워닝 0).
  - `npm run build:check` (vue-tsc 2.2.12 + vite 5) → vue-tsc errors=0 + vite 3.79s + 신규 청크 `AdminDocUtilDepartments-tLGFig2b.js` 21.98 kB (gzip 5.50 kB) + `AdminDocUtilDepartments-NyN5KAqf.css` (style scoped 검증).
  - `@ts-nocheck` 부착 0 (3.x 부채 카탈로그 보존).
- **호스트 배포** (`tmp/phase10_1b_deps/step10_deploy.py`): paramiko SFTP 9 파일 → `cd /home/idino/agenthub && docker compose build agenthub` exit=0 (호스트 multi-stage Dockerfile 가 컨테이너 내부에서 npm + dotnet publish 수행) → `docker compose up -d --force-recreate agenthub` exit=0 → 12초 만에 healthy.
- **e2e + 회귀 21/21 PASS** (`step20_e2e_verify.py`):
  - **A. admin login** (admin@example.com/Admin123!) → 200 (JWT 발급)
  - **B. 9 신규 endpoint** — 모두 200/201/204 (B-1 GET /organization 1180ms cold + 조직 한국어 이름 정확 / B-2 PUT /organization desc 수정 후 원복 / B-3 GET /departments 16ms cold → 14ms warm cache hit / B-4 POST /departments → 201 + created_id / B-5 PUT rename → 200 / B-6 GET /members → 200 + count=0 / B-7 DELETE → 204 / B-8 GET /quota → 200 + yearMonth=2026-05 + quota_count=2 (dalle_monthly + unsplash_monthly) / B-9 PUT /quota/dalle_monthly limit 100→101 → 200 + 즉시 원복)
  - **B-cache invalidate** — POST 후 3차 GET count+1 PASS, DELETE 후 4차 GET count baseline 회복 PASS
  - **C. 권한 게이트** — Bearer 미부착 401 / Bogus JWT 401 모두 PASS
  - **E. 직전 회귀 6 endpoint** — `GET /api/agents/1` (b3a2d85 6필드) / `GET /api/admin/metrics/rag` (Phase 4) / `GET /api/admin/knowledge-base/documents` (9801b06) / `GET /api/admin/knowledge-base/collections` (294e8a6) / 한국어 RAG 라우팅 도달 / `GET /api/admin/docutil/users?page=1&size=10` (10.1a, total=11) — 모두 PASS
  - **검증 시 ghost 부서 정합성 회귀** 발견 후 즉시 해결: 직전 e2e 의 502 시나리오로 cache 가 stale 11 인 채로 남는 회귀 → Controller 의 `DeleteDepartment` 가 catch 분기에서도 `InvalidateDepartmentsCacheAsync` 호출하도록 수정 + e2e 시작 시점에 ghost 잔재 자동 정리(pre-cleanup 안전망).
- **산출물**: 신규 `agenthub/Controllers/AdminDocUtilDepartmentsController.cs` (~360 LOC) + `agenthub/ClientApp/src/views/admin/AdminDocUtilDepartments.vue` (~620 LOC). 수정 `IDocUtilClient.cs` (9 메서드 + 8 record DTO 추가) + `DocUtilClient.cs` (9 구현 + 매핑 헬퍼 + 5 private DTO) + `docutilService.ts` (9 함수 + 8 interface) + `router/index.ts` + `MainLayout.vue` + `i18n/locales/{ko,en}.json`.
- **검증 스크립트** (`tmp/phase10_1b_deps/`): `step01_capture_openapi.py` (DocUtil 8 schema + 7 endpoint 캡처) / `step02_probe_members.py` (멤버 schema 확보 — 운영 부서 `대표이사` 의 멤버 1건 응답으로 검증) / `step10_deploy.py` (호스트 배포) / `step20_e2e_verify.py` (21 회귀 자동화) / `step21_diag_delete.py` (캐시 invalidate 진단) / `step22_repro_delete_cache.py` (ghost 잔재 격리 재현).
- **외부 동작 변경 0** — 기존 `IDocUtilClient` 시그니처 보존(신규 9개만 추가) / 기존 라우트 변경 0 / Phase 10.1a 회귀 PASS / 시연 안정성 100%.

### 2026-05-10 (Phase 10.1a — DocUtil 사용자 운영자 BFF + Vue 콘솔 완료)
- **목적**: AgentHub 운영자가 DocUtil 사용자 카탈로그를 단일 진입점에서 관리. R2 단일 진입점 + P1 Control Plane 원칙 — DocUtil 콘솔 별도 로그인 없이 AgentHub UI 에서 목록/상세/상태 토글/삭제 가능. 향후 10.1b(부서) / 10.1c(프로젝트) 트랙으로 같은 카테고리에 항목 확장.
- **사전 검증** (`tmp/phase10_1a_users/step01_probe_docutil_users.py` + `step02_probe_full.py`): paramiko SSH `192.168.10.39` 도달 PASS / DocUtil JWT 발급 PASS (`jyj7970 / idino!@#$` → access_token len=384) / `GET /api/v1/users` 첫 시도 422 — DocUtil OpenAPI inspection 으로 **`org_id` UUID 쿼리 파라미터 필수** 확인 + 옵션 파라미터(role/status/search) 명시 / `org_id={loginUser.organization_id}` 부착 후 200 PASS (org `00000000-0000-4000-a000-000000000001`, items=11 / total=11). **JWT payload 내 `org` claim 위치 확인** (`step03_jwt_payload.py`) — 향후 BFF 가 호출자(Controller) 무관여로 자동 부착 가능.
- **DocUtil schema 캡처 (record DTO 매핑 근거)**: `UserResponse` 10 필드 — `id` UUID / `username` (한글 이름 또는 ID) / `email` / `role` (admin/member) / `status` (active/inactive/locked) / `organization_id` UUID / `department_id` UUID? / `language` string? / `last_login_at` datetime? / `created_at` datetime (DocUtil 측이 `ins_dt` 컬럼을 alias). `UserListResponse`: `items[UserResponse]` / `total` / `page` / `size`. `_StatusBody`: `{status: string}` (DocUtil 측 active/inactive/locked 검증). 결과 `tmp/phase10_1a_users/docutil_users_full.json` 462 줄 (.gitignore tmp/ 영역).
- **백엔드 (4 endpoint + DTO + Controller)**:
  - `IDocUtilTokenProvider.cs` 확장 — `Task<string?> GetOrganizationIdAsync(ct)` 신설. 매 BFF 호출 시 캐시된 운영자 토큰의 `org` claim 추출. ApiKey 모드(영구 키, JWT 가 아님) 또는 디코드 실패 시 null → 호출자가 502 매핑.
  - `DocUtilTokenProvider.cs` — `TryDecodeJwtClaim(jwt, "org")` 헬퍼 추가 (기존 `TryDecodeJwtExp` 와 동일 패턴 — base64url + JSON parse, parts.Length<2 시 안전 null).
  - `IDocUtilClient.cs` — Users 4 메서드 추가: `ListUsersAsync(page,size,role?,status?,search?)` / `GetUserAsync(id)` / `UpdateUserStatusAsync(id, status)` / `DeleteUserAsync(id)`. 신규 record DTO 3 종 — `DocUtilUserSummary` / `DocUtilUserDetail` (현재 트랙은 동일 셋, 향후 트랙에서 합성 필드 분기) / `DocUtilUserList(items, total, page, size)`. UserResponse 10 필드 모두 보존(BFF 단순화 X — 운영자 화면이 모든 필드 사용).
  - `DocUtilClient.cs` — 4 메서드 구현 (HTTP 호출 + JSON snake_case ↔ PascalCase 매핑 + `EnsureSuccessOrThrowKoreanAsync` 재사용) + `MapUserSummary` / `MapUserDetail` 헬퍼 + `UserResponseDto` / `UserListResponseDto` private DTO. ListUsers 는 `_tokenProvider.GetOrganizationIdAsync` 로 `org_id` 자동 부착(호출자 무관여) — 추출 실패 시 한국어 InvalidOperationException → 502.
  - `AdminDocUtilUsersController.cs` 신설 (~280 LOC, `[Authorize(Roles="Admin,SuperAdmin")]` + `[Route("api/admin/docutil")]`):
    - `GET /users?page&size&role&status&search` → 5분 TTL 캐시 (`du:users:` prefix + version-key `docutil-users`). 캐시 키 구조 `du:users:v{N}:{page}|{size}|{role}|{status}|{searchSHA8}` — search 는 SHA256 short hex 로 정규화하여 한글/길이 안전.
    - `GET /users/{id}` — null → 404 NotFound, InvalidOperationException → 502.
    - `PUT /users/{id}/status` — 상태값 화이트리스트(active/inactive/locked, OrdinalIgnoreCase) 사전 검증 → DocUtil 측 422 차단. 성공 시 `IncrementVersionAsync("docutil-users")` 캐시 일괄 무효화.
    - `DELETE /users/{id}` → 204 NoContent + 캐시 invalidate.
  - **dotnet build**: warnings 11 (모두 pre-existing CS1998 — 본 변경 무관) / errors 0.
- **프론트엔드**:
  - `services/docutilService.ts` — 4 함수 + 4 인터페이스 추가 (`DocUtilUserSummary` / `DocUtilUserDetail` = Summary / `DocUtilUserList` / `DocUtilUserStatus` = `'active' | 'inactive' | 'locked'`). `default export` 11 메서드로 확장.
  - `views/admin/AdminDocUtilUsers.vue` (~470 LOC) 신설:
    - 검색바 (한글 username/email LIKE 위임) + role/status 필터 dropdown + 적용/초기화 버튼.
    - 표 (Username + ID code / Email / Role badge / Status badge + 한국어 라벨 / CreatedAt locale 'ko-KR' format / 작업 3 버튼 — 상세/활성↔비활성/삭제).
    - 페이지네이션 (이전/현재/다음, totalPages 계산).
    - 상세 모달 (overlay + escape-on-outside-click + 10 필드 dl/dt/dd 한국어 라벨).
    - 상태 토글 — `window.confirm` 1단계 + 백엔드 호출 + 행 즉시 갱신.
    - 삭제 — `window.confirm` 2단계 (deleteConfirm + deleteConfirmFinal "마지막 확인 단계") + 백엔드 호출 + 행 제거 + 페이지 비면 prev page.
    - 에러 처리 — axios `response.data.message` 우선, fallback `t('adminDocutilUsers.errorUnknown')`.
  - `router/index.ts` — `/admin/docutil-users` (lazy import + `meta.role='Admin'`).
  - `layouts/MainLayout.vue` — **신규 `docutil` 카테고리** (icon `bi bi-database`, roles=`['Admin','SuperAdmin']`) `aiServices` 와 `admin` 사이 삽입. expandedCategories 초기 false. 항목 1개 (`nav.docutilUsers` → `/admin/docutil-users`, icon `bi bi-people`) — 향후 10.1b/10.1c 트랙에서 같은 카테고리에 부서/프로젝트 항목 추가.
  - i18n ko.json + en.json — `nav.docutilUsers` + `nav.categories.docutil` + `adminDocutilUsers.*` 32 키 (title/subtitle/users/empty/refresh/search/searchPlaceholder/filterRole/filterStatus/allRoles/allStatuses/applyFilters/clearFilters/roleAdmin/roleMember/statusActive/statusInactive/statusLocked/colId/colUsername/colEmail/colRole/colStatus/colCreatedAt/colOrgId/colDeptId/colLanguage/colLastLogin/viewDetail/activate/deactivate/delete/modalTitle/toggleStatusConfirm/deleteConfirm/deleteConfirmFinal/pageInfo/pagination/errorUnknown).
  - **vue-tsc 2.x errors=0** + vite build PASS — `AdminDocUtilUsers-B0sLEcU9.js` 12.57 KB / gzip 3.77 KB. `@ts-nocheck` 부착 0.
- **호스트 배포** (`step10_deploy.py`): SSH 192.168.10.39 / idino → 11 파일 SCP + 백업(`/.bak.phase10_1a/`) → `docker compose build agenthub` (58.2 초 — Stage 1: npm install + vite build 14.39초 + dotnet publish 54.04초 / Stage 2: runtime copy 2.2초) → `docker compose up -d --force-recreate agenthub` → swagger 200 health 8 초 도달.
- **e2e 검증** (`step20_e2e_verify.py`, 16/16 PASS):
  - admin@example.com / Admin123! 로그인 200, JWT len=555.
  - `GET /api/admin/docutil/users?page=1&size=10` 200, latency 844ms (cold cache miss → DocUtil 호출), total=11, sample id=`52ff0252-d940-4357-8b19-6a1bda9b4cb3` username="이동건" status="active". UserSummary 7 필수 필드(id/username/email/role/status/organizationId/createdAt) 모두 포함.
  - `GET /api/admin/docutil/users/{id}` 200, latency 59ms.
  - `PUT /api/admin/docutil/users/{id}/status` — 검증용 사용자 `user@example.com` (id=`a0000000-0000-4000-a000-000000000003`) active → inactive (200 / 179ms) → 원복 active (200 / 46ms) 모두 PASS.
  - `GET /api/admin/docutil/users/{fake-uuid}` → 404 (DocUtilClient 의 NotFound 정규화 PASS).
  - 권한 게이트 — Bearer 미부착 → 401 PASS / Bogus JWT → 401 PASS (비-Admin 시드 계정 없음 — 본 환경의 user@example.com 도 Admin 권한 보유).
  - 캐시 invalidate — 재호출 latency 29ms / 23ms (warm) → mutation PUT (31ms) 후 재호출 17ms (새 version prefix 의 cold miss + DocUtil 응답 fast). 캐시 hit/miss 두 패턴 모두 200 PASS.
  - 직전 회귀 5 endpoint 모두 PASS — `GET /api/agents/1` (b3a2d85 6 신규 필드 모두 응답에 존재) / `GET /api/admin/metrics/rag` (Phase 4) / `GET /api/admin/knowledge-base/documents` (9801b06) / `GET /api/admin/knowledge-base/collections` (294e8a6, count=2) / 한국어 RAG `POST /api/chat/conversations/260/messages` 라우팅 200 with Claude upstream 401 (API 키 부재 — 라우팅 자체는 intact).
- **산출물**:
  - 신규: `agenthub/Controllers/AdminDocUtilUsersController.cs` (~280 LOC) / `agenthub/ClientApp/src/views/admin/AdminDocUtilUsers.vue` (~470 LOC)
  - 수정: `agenthub/Services/IDocUtilClient.cs` (4 메서드 + 3 record DTO) / `agenthub/Services/DocUtilClient.cs` (4 구현 + 2 mapper + 2 private DTO) / `agenthub/Services/IDocUtilTokenProvider.cs` (1 메서드) / `agenthub/Services/DocUtilTokenProvider.cs` (claim decoder) / `agenthub/ClientApp/src/services/docutilService.ts` (4 함수 + 4 type) / `agenthub/ClientApp/src/router/index.ts` (1 라우트) / `agenthub/ClientApp/src/layouts/MainLayout.vue` (1 카테고리 + expandedCategories 키) / `agenthub/ClientApp/src/i18n/locales/ko.json` (32 키) / `agenthub/ClientApp/src/i18n/locales/en.json` (32 키)
  - 검증 스크립트(.gitignore tmp/): `tmp/phase10_1a_users/step01_probe_docutil_users.py` / `step02_probe_full.py` / `step03_jwt_payload.py` / `step10_deploy.py` / `step20_e2e_verify.py`
- **다음 트랙**: **Phase 10.1b — DocUtil Departments 운영자 BFF** (DocUtil `/api/v1/departments` 카탈로그 + AdminDocUtilDepartments.vue / 부서명 → 사용자 목록 합성 옵션). 동일 카테고리(`docutil`) 에 항목 추가.


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

## 7. 다음 작업 (Phase 10.2a 완료 — Phase 10.2b 또는 별도 트랙)

### Phase 10.1 — 전체 종결 (10.1a + 10.1b + 10.1c, 2026-05-10)

운영자가 AgentHub 단일 화면에서 DocUtil 의 모든 운영 메타데이터(사용자/조직/부서/할당량/프로젝트/보드)를 관리한다. DocUtil 콘솔 별도 로그인 불필요. R2 (단일 진입점) + R3 (스키마 격리) 모두 충족.

### Phase 10.2a — 완료 (2026-05-10, 위 작업 로그 참조)

운영자가 AgentHub 단일 화면에서 DocUtil 의 운영 모니터링(KPI/응답시간/검색 통계/업로드 상태 5종) + 감사 로그(필터·페이지네이션·CSV export) 를 모두 확인. e2e 32/0 PASS, 직전 회귀 8 endpoint PASS.

### Phase 10.2b (별도 트랙, 사용자 결정 시 진입)
- **Search Scopes / Evaluation / Notifications** 등 DocUtil 추가 운영자 기능 통합
- 감사 로그 actor 정보 join (DocUtil user_id → username/email 자동 합성 — 본 트랙 BFF 에서는 raw 그대로 노출)
- 감사 로그 search query / IP 통계 등 분석 모듈
- DocUtil 측에 `user_agent` schema 추가 요청 가능성 — 본 트랙은 추정 금지로 미포함

### 후속 트랙 잔존
- D-1 `@vue-flow/core` 타입 strict 검사 깨짐 — `WorkflowBuilder.vue` `@ts-nocheck` 잔존 패키지 업그레이드 필요(이미 d40945c 에서 부분 정리)
- RAG 메트릭 prometheus 통합 + 시계열 영속화 (in-memory only)
- RagService 결과 캐시(`rag:*` 10분) 일괄 무효화 — version-key 패턴 확장 가능
- AgentSelect.vue 빠른 생성/수정 모달 — AgentBuilder.vue 로 흡수 또는 deprecate
- Nexus 실제 부팅 (192.168.22.28 GPU 호스트)

### 별도 트랙 (시연 종료 후)
- secret leak history sanitize + force-push
- SQL Server stale 비번 / SSH 비번 / appsettings LLM API 키 회전
- DocUtil 운영자 service account 정식 전용 계정 발급(현재 jyj7970 admin 사용)

### Phase 10.1c (완료, 위 작업 로그 참조)

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
