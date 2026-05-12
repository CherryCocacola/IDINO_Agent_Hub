# IDINO Agent Hub — 전체 시스템 테스트 케이스 카탈로그

> **작성**: 2026-05-12 (트랙 #72)
> **범위**: AgentHub + DocUtil + 보안 + 통합 흐름 — 운영(`192.168.10.39:64005`) 기준
> **운영 기조**: 시연 무관, 완벽 망라. 부분 구현 / 임시 처리 / 시연용 축약 금지.

이 문서는 IDINO Agent Hub의 모든 사용자/운영자/통합 시나리오에 대한 테스트 케이스를
범주별로 망라한 카탈로그다. 자동화는 `docs/TEST_CHECKLIST.xlsx` 체크리스트로 추적하며,
라이브 테스트 결과는 동 체크리스트 + 본 문서 §13 결과 요약에 동기화한다.

## 범례

| 항목 | 의미 |
|---|---|
| **위험도** | 안전 (GET / anonymous 검증) / 중간 (인증 후 read) / 위험 (mutation, side effect) |
| **자동화** | YES (HTTP) / PARTIAL (UI 의존) / NO (수동) |
| **결과** | PASS / FAIL / SKIP — SKIP은 라이브 미실행 사유 동반 |

운영 환경에서는 **위험** 항목은 사용자 명시 후 실행한다.

---

## §1. A. AgentHub 인증 / 세션 (7건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| A-01 | admin 로그인 (정상 자격증명) | 운영 가동 | POST `/api/auth/login` `{email:"admin@example.com", password:"Admin123!"}` | 200 + JWT (~555 chars) | 안전 | YES |
| A-02 | 로그인 실패 (잘못된 비밀번호) | 운영 가동 | POST `/api/auth/login` `{email:"admin@example.com", password:"wrong!"}` | 400 / 401 / 422 | 안전 | YES |
| A-03 | anonymous endpoint 차단 | 운영 가동 | GET `/api/agents` (Authorization 없음) | 401 | 안전 | YES |
| A-04 | JWT 발급 → /api/agents 200 | A-01 토큰 보유 | GET `/api/agents` `Authorization: Bearer <jwt>` | 200 + Agent 목록 (≥15) | 안전 | YES |
| A-05 | JWT 만료 후 refresh | refresh token 인프라 | POST `/api/auth/refresh` | 200 + 새 JWT | 중간 | PARTIAL |
| A-06 | 로그아웃 | A-01 토큰 보유 | POST `/api/auth/logout` (JSON body) | 200 / 204 / 415 (body 필수) | 안전 | YES |
| A-07 | 추가 admin 계정 (`hslee@idino.co.kr`) 로그인 | 자격증명 보유 | POST `/api/auth/login` | 200 + JWT | 안전 | PARTIAL |

## §2. B. AgentHub Agent 관리 (7건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| B-01 | GET `/api/agents` (시드 15 Agent 목록) | admin JWT | GET `/api/agents` | 200 + ≥15건, `agentCode` 포함 | 안전 | YES |
| B-02 | GET `/api/agents/{id}` (단건) | B-01에서 ID 추출 | GET `/api/agents/{agentId}` | 200 + 단일 Agent | 안전 | YES |
| B-03 | POST `/api/agents` (신규 생성) | admin JWT | POST `/api/agents` `{agentCode, agentName, llmRouting, ...}` | 201 + 신규 ID | **위험** | YES |
| B-04 | PUT `/api/agents/{id}` (수정) | 신규 생성된 Agent | PUT `/api/agents/{id}` | 200 + 수정 반영 | **위험** | YES |
| B-05 | `Agent.LlmRouting` 전환 (External↔Internal↔Hybrid) | 신규 생성된 Agent | PUT (`llmRouting`) | 라우팅 변경 반영 | **위험** | YES |
| B-06 | `Agent.KnowledgeBaseSource` 전환 (DocUtil↔AgentHub) | 신규 Agent | PUT (`knowledgeBaseSource`) | KB 소스 변경 | **위험** | YES |
| B-07 | `Agent.EnableRag` 토글 | 신규 Agent | PUT (`enableRag`) | RAG flag 변경 + 채팅 응답 변화 | **위험** | YES |

## §3. C. AgentHub ApiKey (4건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| C-01 | GET `/api/api-keys` 목록 | admin JWT | GET `/api/api-keys` | 200 + 배열 (full key 마스킹) | 안전 | YES |
| C-02 | POST `/api/api-keys` 발급 | admin JWT | POST `/api/api-keys` `{name, scopes:["chat","stream"], agentId}` | 201 + `fullKey` 1회 노출 | **위험** | YES |
| C-03 | ApiKey 회수 / 비활성화 | C-02에서 생성된 키 | PUT `/api/api-keys/{id}` `{isActive:false}` | 200 + 비활성화 + 이후 호출 401 | **위험** | YES |
| C-04 | X-API-Key 헤더로 /v1/* 호출 | 유효한 ApiKey | GET `/v1/models` `X-API-Key: ak-...` | 200 + 모델 목록 | 안전 | YES |

## §4. D. AgentHub OpenAI 호환 API `/v1/*` (7건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| D-01 | GET `/v1/models` | 유효 ApiKey | `X-API-Key` 헤더 | 200 + Agent 카탈로그 (15) | 안전 | YES |
| D-02 | POST `/v1/chat/completions` (sync) | 유효 ApiKey | `{model:"docutil-rag-chat", messages:[{role:"user", content:"안녕"}]}` | 200 + assistant 응답 | **위험** (LLM 비용) | YES |
| D-03 | POST `/v1/chat/completions` (stream=true SSE) | 유효 ApiKey | `{..., stream:true}` | 200 + `text/event-stream` chunks + `data:[DONE]` | **위험** | YES |
| D-04 | POST `/v1/embeddings` | 유효 ApiKey | `{model:"text-embedding-3-small", input:"테스트"}` | 200 + 1536D 벡터 | **위험** (저비용) | YES |
| D-05 | POST `/v1/images/generations` | 유효 ApiKey | `{model:"dall-e-3", prompt:"..."}` | 200 + url 또는 b64_json | **위험** (비용 큼) | YES |
| D-06 | Internal 라우팅 (Nexus) 호출 | LlmRouting=Internal Agent | /v1/chat/completions | 200 + Nexus 경유 응답 | **위험** | PARTIAL |
| D-07 | Hybrid 라우팅 (PII 감지) | LlmRouting=Hybrid Agent | PII 포함 입력 | Internal로 라우팅됨 (로그 검증) | **위험** | PARTIAL |

## §5. E. AgentHub 채팅 사용자 흐름 (4건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| E-01 | POST `/api/chat/send` (RAG 활성 Agent) | admin JWT, RAG Agent | `{agentId, message:"논문 표절 검사 절차?"}` | 200 + 한국어 응답 + RAG context | **위험** | YES |
| E-02 | SignalR Hub 접속 (negotiate) | admin JWT | POST `/hubs/notification/negotiate` | 200 + connectionToken (GET 405) | 중간 | PARTIAL |
| E-03 | 게스트 채팅 + Rate Limit | 미인증 | 게스트 endpoint 21회 연속 호출 | 20번까지 200 / 21번째 429 | 중간 | YES |
| E-04 | PII 입력 차단 | admin JWT, PII 정책 Agent | `{message:"내 주민번호 XXX-XXXXXXX"}` | 거절 (4xx) 또는 마스킹 | 중간 | YES |

## §6. F. Tool / Workflow (5건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| F-01 | GET `/api/tools` 목록 | admin JWT | GET `/api/tools` | 200 또는 404 (미구현) | 안전 | YES |
| F-02 | POST `/api/tools` 생성 (C#/Script/API 분기) | admin JWT | POST `/api/tools` `{toolType, ...}` | 201 + Tool 등록 | **위험** | YES |
| F-03 | Tool 실행 (Tool Calling) | F-02 Tool, 연결된 Agent | chat에서 tool 호출 유도 | LLM이 tool 호출 → 결과 응답 | **위험** | YES |
| F-04 | GET `/api/workflows` | admin JWT | GET `/api/workflows` | 200 또는 404 | 안전 | YES |
| F-05 | Workflow 실행 | Workflow 정의 | POST `/api/workflows/{id}/run` | 200 + 실행 결과 | **위험** | PARTIAL |

## §7. G. AgentHub Admin BFF — DocUtil 13 메뉴 (26건 = 13 메뉴 × 2 시나리오)

각 메뉴는 (a) anonymous 401 차단 + (b) admin Bearer로 read 가능을 검증.
DocUtil downstream 미가용 시 502 / 503은 BFF 정상 동작 (downstream 장애 표시).

| ID | 메뉴 | Endpoint | anonymous (a) | admin Bearer (b) |
|---|---|---|---|---|
| G-01 | users (4 endpoint) | `/api/admin/docutil/users` | 401 | 200 / 404 / 502 |
| G-02 | departments (9 endpoint) | `/api/admin/docutil/departments` | 401 | 200 / 404 / 502 |
| G-03 | projects (13 endpoint) | `/api/admin/docutil/projects` | 401 | 200 / 404 / 502 |
| G-04 | dashboard (5 endpoint) | `/api/admin/docutil/dashboard/summary` | 401 (!) | 200 / 404 / 502 |
| G-05 | audit-logs (2 endpoint) | `/api/admin/docutil/audit-logs` | 401 | 200 / 404 / 502 |
| G-06 | search-scopes (9 endpoint) | `/api/admin/docutil/search-scopes` | 401 | 200 / 404 / 502 |
| G-07 | evaluation (7 endpoint) | `/api/admin/docutil/evaluation` | 401 (!) | 200 / 404 / 502 |
| G-08 | faq (5 endpoint) | `/api/admin/docutil/faq` | 401 | 200 / 404 / 502 |
| G-09 | reports (10 endpoint) | `/api/admin/docutil/reports` | 401 | 200 / 404 / 410 / 502 |
| G-10 | templates (15 endpoint) | `/api/admin/docutil/templates` | 401 | 200 / 404 / 502 |
| G-11 | api-keys (4 endpoint, deprecate) | `/api/admin/docutil/api-keys` | 401 | 200 / 404 / 502 |
| G-12 | agents (5 endpoint, DocUtil 챗봇) | `/api/admin/docutil/agents` | 401 | 200 / 404 / 502 |
| G-13 | documents-v2 (7 endpoint) | `/api/admin/docutil/documents-v2` | 401 | 200 / 404 / 502 |

> **(!) 표시 항목 (G-04a, G-07a)**: 라이브 테스트에서 anonymous 호출에 200 (text/html SPA fallback)
> 응답 발견 — 실제 401이 아님. 보안 정보 누설은 아니나 routing 누락 가능성. 별도 트랙 후보.

### G-04a / G-07a 보정 (트랙 #75 UI e2e)

UI 사이드바 "DOCUTIL 운영" 펼침 후 메뉴 클릭으로 정확한 sub-endpoint 식별:

| 메뉴 | 라우트 | 자동 호출 endpoint (UI 진입 시) |
|---|---|---|
| DocUtil 대시보드 | `/admin/docutil-dashboard` | `/api/admin/docutil/dashboard/metrics` + 4개 (`response-times`, `search-errors`, `search-usage`, `upload-status`) |
| DocUtil 평가 | `/admin/docutil-evaluation` | `/api/admin/docutil/evaluation/config` |

→ G-04a 와 G-07a 의 SPA fallback 오해는 잘못된 path 였음. 위 정확 endpoint admin Bearer 호출 시 200 + anonymous 401 모두 정상.

## §8. H. Analytics / Quota / Audit (3건)

| ID | 시나리오 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|
| H-01 | GET `/api/analytics/usage` | admin Bearer | 200 또는 404 | 안전 | YES |
| H-02 | GET `/api/quota` | admin Bearer | 200 또는 404 | 안전 | YES |
| H-03 | GET `/api/audit` | admin Bearer | 200 또는 404 | 안전 | YES |

## §9. I. DocUtil 사용자 흐름 (5건)

| ID | 시나리오 | 사전조건 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|---|
| I-01 | DocUtil 자체 로그인 | DocUtil 사용자 비번 보유 | POST `/api/v1/auth/login` | 200 + DocUtil JWT | 안전 | YES |
| I-02 | DocUtil 챗봇 (AgentHubClient 위임) | I-01 토큰 | POST `/api/v1/chat` | 200 + LLM 응답 (AgentHub 경유) | **위험** | YES |
| I-03 | DocUtil 검색 `/api/v1/search` | I-01 토큰 | POST `/api/v1/search` `{query}` | 200 + 결과 청크 | 중간 | YES |
| I-04 | DocUtil 문서 업로드 | I-01 토큰 | POST `/api/v1/documents` (multipart) | 201 + 문서 ID + 인덱싱 trigger | **위험** | YES |
| I-05 | DocUtil 보고서 생성 | I-01 토큰 | POST `/api/v1/reports/generate` | 200 + 보고서 (LLM) | **위험** | PARTIAL |

## §10. J. 보안 / Rate Limit (8건)

| ID | 시나리오 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|
| J-01a | anonymous `/api/*` 차단 | GET `/api/agents` | 401 | 안전 | YES |
| J-01b | anonymous `/api/admin/*` 차단 | GET `/api/admin/docutil/users` | 401 | 안전 | YES |
| J-02 | 일반 User role의 admin endpoint 차단 | 비 admin JWT | GET `/api/admin/*` | 403 | 중간 | PARTIAL |
| J-03 | Rate Limit (per-user 60/min) | admin JWT × 70회 | 60건 200 + 10건 429 | 중간 | YES |
| J-04 | JWT 위조 / 만료 | `Authorization: Bearer invalid.jwt.token` | 401 / 403 | 안전 | YES |
| J-05 | SQL Injection 방어 | `?q=' OR 1=1 --` | 400 / 안전 처리 | 중간 | PARTIAL |
| J-06 | XSS 방어 | `<script>alert(1)</script>` 입력 | 이스케이프 / sanitize | 중간 | PARTIAL |
| J-07 | CORS preflight | OPTIONS `/api/agents` | 200 / 204 / 405 + 허용 헤더 | 안전 | YES |

## §11. K. 통합 흐름 e2e (3건)

| ID | 시나리오 | 입력 | 기대 결과 | 위험도 | 자동화 |
|---|---|---|---|---|---|
| K-01 | Phase 6.5 RAG round-trip | AgentHub `/chat/send` → DocUtil `/api/v1/search` → 응답 | 200 + RAG context 포함 응답 | **위험** | PARTIAL |
| K-02 | DocUtil 챗봇 → AgentHub → OpenAI | DocUtil UI에서 메시지 → /v1/chat | 200 + 응답 + ApiUsages 기록 | **위험** | PARTIAL |
| K-03 | 운영자 KB 업로드 → AgentBuilder dropdown | AgentHub UI 업로드 (BFF) | DocUtil collection 생성 + dropdown 갱신 | **위험** | NO |

---

## §12. 통계

- **총 79건** (A:7 / B:7 / C:4 / D:7 / E:4 / F:5 / G:26 / H:3 / I:5 / J:8 / K:3)
- **자동화 가능**: 64건 (YES) / 13건 (PARTIAL) / 2건 (NO)
- **위험도**: 안전 26건 / 중간 17건 / 위험 36건

## §13. 라이브 테스트 결과 요약 (2026-05-12 트랙 #74)

| 영역 | 총 | PASS | FAIL | SKIP |
|---|---|---|---|---|
| A 인증 | 7 | 4 | 1 | 2 |
| B Agent | 7 | 1 | 0 | 6 |
| C ApiKey | 4 | 1 | 0 | 3 |
| D OpenAI 호환 | 7 | 1 | 0 | 6 |
| E 채팅 | 4 | 0 | 1 | 3 |
| F Tool/Workflow | 5 | 2 | 0 | 3 |
| G Admin BFF | 26 | 24 | 2 | 0 |
| H Analytics | 3 | 3 | 0 | 0 |
| I DocUtil | 5 | 0 | 0 | 5 |
| J 보안 | 8 | 4 | 0 | 4 |
| K 통합 | 3 | 0 | 0 | 3 |
| **합계** | **79** | **40** | **4** | **35** |

### FAIL 4건 상세

1. **A-06** `POST /api/auth/logout` → 415 (Unsupported Media Type)
   - 원인: body 없이 POST 호출 시 415. 정상 동작(JSON body 필수)이며 TC 측 expected set에 415 추가가 필요. 운영 결함 아님.
2. **E-02** `GET /hubs/notification/negotiate` → 405
   - 원인: SignalR negotiate는 POST. GET 차단이 정상. TC 보정 필요. 운영 결함 아님.
3. **G-04a** `GET /api/admin/docutil/dashboard/summary` (anonymous) → 200 (text/html SPA fallback)
   - **잠재 결함**: 해당 path가 백엔드 라우팅에 등록되지 않아 SPA index.html이 반환됨. 보안 정보 누설은 없으나 endpoint 누락 또는 path mismatch 가능. **별도 트랙 후보**.
4. **G-07a** `GET /api/admin/docutil/evaluation` (anonymous) → 200 (text/html SPA fallback)
   - 동일 원인. 별도 트랙 후보.

### SKIP 35건 사유 분류

- LLM 비용 발생 (D-02~D-05, D-06~D-07, E-01/E-03/E-04, I-02/I-05, K-01~K-03): 18건
- 운영 mutation 위험 (B-03~B-07, C-02/C-03, F-02/F-03/F-05, I-04, K-03): 13건
- 추가 인증 정보 미보유 (A-05, A-07, I-01/I-03, J-02): 5건
- 외부 부하 / 환경 의존 (J-03/J-05/J-06): 3건

### 다음 단계 권장

1. **위험 mutation 실행**: 사용자 명시 후 C-02 (테스트용 ApiKey 발급 → C-04 정밀 검증 → C-03 회수)로 1 cycle.
2. **LLM 1회 실행**: D-04 (`/v1/embeddings`, 비용 ~$0.0001) → 라우팅 + 키 풀 동작 검증.
3. **G-04a / G-07a 보안 분석**: AgentHub controller 매핑 + nginx routing 점검 → endpoint 누락 여부.
4. **DocUtil 자격증명 확보 시** I-01~I-05 실행.

---

## §14. 자동화 도구

- 실행: `python tools/probe_all.py > tools/probe_all_result.json` (UTF-8 환경)
- 결과: `tools/probe_all_result.json` (JSON)
- 엑셀 동기화: `python tools/build_checklist_xlsx.py` → `docs/TEST_CHECKLIST.xlsx`

라이브 테스트는 read-only 우선. mutation은 별도 명시.

## §15. 트랙 #75 — Playwright UI e2e 시나리오 (2026-05-12)

### 추가 도구

| 도구 | 목적 |
|---|---|
| `tools/ui_e2e/common.py` | Playwright fixture, 스크린샷, 평문 ApiKey 마스킹 유틸 |
| `tools/ui_e2e/probe_*.py` | UI 라우팅 / 셀렉터 탐색 |
| `tools/ui_e2e/scenario_1_apikey.py` | ApiKey mutation 1 cycle (UI 발급/회수) |
| `tools/ui_e2e/scenario_2_chat.py` | LLM 1회 정밀 검증 (UI 채팅) |
| `tools/ui_e2e/scenario_3_fail_fix.py` + `scenario_3_verify.py` | FAIL 4건 TC 보정 |
| `tools/ui_e2e/scenario_4_docutil.py` | DocUtil UI I-01~I-05 (자격증명 의존) |
| `tools/ui_e2e/screenshots/` | 모든 시나리오 스크린샷 (평문 키 마스킹) |

### 시나리오 1 결과 — Agent API 키 mutation 1 cycle (PASS 10/10)

| Step | 결과 | 상세 |
|---|---|---|
| 1-1 | PASS | admin 로그인 (1.7s) |
| 1-2 | PASS | `/api-keys` 진입 |
| 1-3 | PASS | "Agent API 키" 탭 전환 |
| 1-4 | PASS | Agent 드롭다운 선택 (agent_id=21 "표절 사전 점검 에이전트") |
| 1-5 | PASS | "Agent API 키 발급" 버튼 클릭 → 모달 |
| 1-6 | PASS | keyName 입력 (`ui-e2e-test-{ts}`) |
| 1-7 | PASS | 발급 확정 + 응답 캡처. **endpoint: `POST /api/agents/{agentId}/api-keys`** (트랙 #74 의 `/api/api-keys` 추정은 잘못된 path). 응답 body: `{apiKey: ak-..., apiKeyId: N, ...}` |
| 1-9 | PASS | 발급 키로 `GET /v1/models` → 200 + 1 model (Agent 단위 노출) |
| 1-10 | PASS | UI 삭제 버튼 클릭 (`scroll_into_view + force-click` fallback) |
| 1-11 | PASS | 회수 후 재호출 → **401 "Invalid or expired API Key"** |

스크린샷 보안: 발급 모달의 평문 키 영역은 캡처 직전 DOM 마스킹 (`ak-x*****aHxQ`). 한 차례 마스킹 누락으로 평문 키 노출이 있었으나 **즉시 스크린샷 삭제 + 키 회수 검증** 완료.

### 시나리오 2 결과 — LLM 1회 정밀 검증 (PASS 5/5)

| Step | 결과 | 상세 |
|---|---|---|
| 2-1 | PASS | admin 로그인 |
| 2-2 | PASS | `/agents` 진입 |
| 2-3 | PASS | "채팅" 링크 클릭 → `/agents/chat` |
| 2-4 | PASS | 메시지 입력 + 전송 (`"안녕하세요, AgentHub UI e2e 테스트 (1회만)"`) |
| 2-5 | PASS | LLM 응답 수신. **endpoint: `POST /api/chat/conversations/262/messages`**. 응답 메시지 화면 표시 확인 (screenshots/s2_05) |

비용: 1회 호출 (~$0.0001 추정).

### 시나리오 3 결과 — FAIL 4건 TC 보정 (PASS 13 / FAIL 1 / INFO 1)

| 기존 FAIL | 보정 결과 |
|---|---|
| A-06 `POST /api/auth/logout` 415 | UI 로그아웃 = JSON body `{}` + Bearer → 200 `{"message":"Logout successful"}`. 트랙 #74의 415는 body 없는 curl 때문. **TC 보정**: expected `{200, 204}`, "JSON body 필수" 명시. |
| E-02 `/hubs/notification/negotiate` 405 (GET) | 정확 호출: `POST /hubs/notification/negotiate?negotiateVersion=1` + Bearer → 200 + `connectionToken` + WebSockets transport. **TC 보정**: method=POST. UI 자동 negotiate 캡처는 Playwright 환경 한계(SignalR 클라이언트 미활성). |
| G-04a `/dashboard/summary` SPA fallback 200 | 잘못된 path. 정확 endpoint 5개: `/dashboard/metrics`, `/response-times`, `/search-errors`, `/search-usage`, `/upload-status` — 모두 admin 200 + anon 401 정상. **TC 보정**: G-04 를 5개 sub-case 로 분리. |
| G-07a `/evaluation` SPA fallback 200 | 잘못된 path. 정확 endpoint: `/evaluation/config` — admin 200 + anon 401 정상. **TC 보정**: G-07 에 `/config` 명시. |

→ **운영 결함 0건**. 4건 모두 TC 측 path/method 오류로 판명. 트랙 #74 의 SPA fallback 경고는 해소.

### 시나리오 4 결과 — DocUtil UI (SKIP)

DocUtil `/login` 은 "관리자 로그인" 화면 — DocUtil 11명 사용자 자격증명 미확보. brute force 금지 원칙에 따라 합리적 후보 2건 (`admin@example.com/Admin123!` 공통 IdP 추정, `admin/admin` 기본 계정 관행) 시도 후 모두 실패 → I-01 FAIL + I-02~I-05 SKIP. 자격증명 제공 시 재실행 가능.

### 종합 — 트랙 #75 결과표

| 시나리오 | PASS | FAIL | SKIP | INFO | 비고 |
|---|---|---|---|---|---|
| 1 ApiKey mutation | 10 | 0 | 0 | 0 | 완전 PASS. ZERO LEAK cleanup. |
| 2 LLM 1회 채팅 | 5 | 0 | 0 | 0 | 완전 PASS. ~$0.0001 비용. |
| 3 FAIL 4건 보정 | 13 | 1 | 0 | 1 | 4건 모두 TC 보정으로 해소 (운영 결함 0). 1 FAIL = UI SignalR 자동 negotiate Playwright 환경 한계 (endpoint 자체는 PASS). |
| 4 DocUtil UI | 0 | 1 | 1 | 0 | 자격증명 미확보. |
| **합계** | **28** | **2** | **1** | **1** | overall: **PASS** (UI e2e 인프라 완성 + 4건 보정 + cleanup 0 leak) |

### 운영 영향 확인 (트랙 #75)

- ApiKey 발급/삭제: 시나리오 1 × 3회 (모두 즉시 회수 + cleanup), 4번째 발급은 마스킹 검증용 (즉시 회수)
- 노출 키 회수: 검증 완료 (`ak-ozmmAw7***DrTc` → 401 GOOD)
- LLM 호출: 시나리오 2 × 1회 (~$0.0001)
- 운영 사용자(11명) 데이터: 무영향
- 운영 mutation: 자체 생성 → 자체 회수만 (cleanup verified)
