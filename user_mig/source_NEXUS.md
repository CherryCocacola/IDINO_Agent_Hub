# source_NEXUS.md — Project Nexus 소스 분석 (IDINO_Agent_Hub 통합 자료)

작성일: 2026-05-04 · 분석 기준: `D:\workspace\nexus\` (현재 운영 중인 v0.14.x / v7.0 Phase 9)

---

## 1. 시스템 한 줄 요약

> **Nexus는 에어갭(LAN-only) 환경에서 동작하는 로컬 LLM 오케스트레이션 플랫폼**으로, vLLM 위에 Claude Code 류의 4-Tier AsyncGenerator 체인 + 도구 시스템 + 멀티테넌시 + RAG를 얹은 Python 비동기 서버다.

### 기술 스택

- **언어/런타임**: Python 3.11+, `asyncio`, FastAPI 0.112+, Uvicorn
- **추론 백엔드**: vLLM (OpenAI 호환 `/v1/chat/completions` SSE), 별도 LAN GPU 머신(`192.168.22.28:8001`)에 배치
- **모델**:
  - Primary — `nexus-phase3` (Qwen 3.5 27B Dense AWQ + Phase3 LoRA, 도구 호출 특화)
  - Knowledge/Chat — `qwen3.5-27b` 베이스 (LoRA OFF, 일반 지식 + 인사·잡담)
  - Auxiliary — `exaone-7.8b` (한국어 보조)
  - Embedding — `multilingual-e5-large` (1024차원, 별도 vLLM 인스턴스 `:8002`)
- **저장소**: Redis (단기/세션, `192.168.10.39:6340`, db=6, docutil-redis 컨테이너 공유), PostgreSQL 17 + pgvector (`192.168.10.39:5440`, DB명 `nexus`)
- **데이터 모델**: Pydantic v2
- **설정**: YAML (`config/`) + 환경변수(`NEXUS_` 접두사) + 기본값 3단계
- **CLI/UI**: Rich/Textual (터미널), 정적 HTML 채팅 UI (`web/static/index.html`)
- **학습**: QLoRA/LoRA (training/, scripts/train_lora.py)

위치: `D:\workspace\nexus\CLAUDE.md`, `requirements.txt`, `config/nexus_config.yaml`

---

## 2. API 표면적 (FastAPI)

진입점: `web/app.py`. 모든 엔드포인트는 `/v1/*` 프리픽스 또는 표준 운영 경로.

| Method | Path | 인증 | 용도 |
|---|---|---|---|
| POST | `/v1/chat` | (테넌트 해석) | 비스트리밍 채팅. 모든 StreamEvent를 모아 단일 응답으로 반환 |
| POST | `/v1/chat/stream` | (테넌트 해석) | **SSE 스트리밍 채팅** (메인 통합 진입점) |
| GET | `/v1/sessions` | - | Redis + JSONL 트랜스크립트 머지 세션 목록 |
| GET | `/v1/sessions/{session_id}/messages` | - | 세션 대화 복원 (Redis 우선, 디스크 폴백) |
| DELETE | `/v1/sessions/{session_id}` | - | 세션 삭제 (Redis + 디스크 best-effort) |
| GET | `/v1/tools` | - | 등록된 ToolRegistry 조회 |
| GET | `/v1/models` | - | 모델 카탈로그 |
| GET | `/v1/tenants` | - | 테넌트 목록 (api_keys 원본은 비노출, count만) |
| POST | `/v1/upload` | - | 첨부파일 임시 저장(`/tmp/nexus_uploads/`) |
| GET | `/health` | - | 자체 + GPU 서버(`/health` 프록시) 상태 |
| GET | `/metrics` | - | HTTP/세션/Scout/Agent/캐시/테넌트 통계 |
| GET | `/` | - | 채팅 UI HTML |

### 인증/테넌트 해석 (`web/app.py:88` `_resolve_tenant`)

**우선순위:** `body.tenant_id` → `X-Tenant-ID` 헤더 → `Authorization: Bearer <api_key>` → `default_tenant`.

- API 키는 `tenants.yaml`의 각 테넌트 `api_keys[]` 배열에서 선형 검색(`config.py:372` `resolve_by_api_key`).
- **현재 인증은 "테넌트 식별" 용도일 뿐, 인증 거부(401) 미들웨어는 없다.** API 키가 일치하지 않으면 그냥 `default_tenant`로 폴백.
- LAN-only가 외부 노출 차단의 1차 방어선 (CORS도 192.168.x / 10.x / 172.16~31.x만 허용 — `web/middleware.py:189`).

---

## 3. 4-Tier 비동기 체인 구조

`CLAUDE.md`와 `core/orchestrator/query_engine.py:14`에 명시된 핵심 아키텍처.

```
Tier 1  QueryEngine.submit_message()      세션 오케스트레이터
        - 대화 히스토리 관리, 시스템 프롬프트 조립, 라우팅 결정
        位置: core/orchestrator/query_engine.py
            ↓ (AsyncGenerator[StreamEvent])
Tier 2  query_loop()                       에이전트 턴 루프 (while True)
        - LLM stream 호출 → tool_use 감지 → 도구 실행 → 다시 stream
        位置: core/orchestrator/query_loop.py
            ↓
Tier 3  ModelProvider.stream()             SSE 스트림 파싱
        - vLLM /v1/chat/completions → text_delta/tool_use/usage/stop
        位置: core/model/inference.py:201 (LocalModelProvider)
            ↓
Tier 4  with_retry() + httpx               9-카테고리 에러 분류 재시도
        位置: core/orchestrator/retry.py
```

각 Tier는 **AsyncGenerator로 위쪽 Tier에 StreamEvent를 yield**한다. 이 체인은 절대 우회 금지(`.claude/rules/architecture.md`, `.claude/rules/anti-patterns.md`).

스트림 안정화: `web/app.py:687` 이벤트 큐 + 20초 SSE heartbeat (`: heartbeat Ns\n\n` 주석 프레임)로 프록시 끊김 방지.

---

## 4. 세션 / 멀티테넌시

### 세션 (`core/memory/short_term.py`, `core/memory/transcript.py`)
- **session_id**: 클라이언트가 미지정 시 서버가 `uuid.uuid4()` 생성. SSE 응답 헤더 `X-Session-ID`로 반환.
- **2-tier 영속화**:
  1. **Redis** (`session:{id}:context`, TTL 24h) — 인메모리 + write-through. JSON 직렬화된 `[{role, content, turn, ts}]`.
  2. **JSONL 트랜스크립트** (`.nexus/sessions/{session_id}/transcript.jsonl`) — 영구 기록.
- **단방향 토큰 예산 복원** (`web/app.py:649`): SSE 핸들러가 budget 6,000자(≈ 2K 토큰) 안에서 최근 user/assistant 텍스트만 복원. tool_use / tool_result 메시지는 토큰 절약을 위해 저장 자체를 안 함.
- **`<think>` 정제** (`web/app.py:45` `_strip_thinking`) — Qwen 3.5 thinking 잔여 태그가 다음 턴 in-context 모방을 유발하므로 저장 전 1회성 sanitize.

### 멀티테넌시 (`config/tenants.yaml`, `core/config.py:311 TenantConfig`)
각 테넌트 필드:
- `id`, `name`, `description`
- `model_override`: 테넌트 전용 LoRA 어댑터 (예: `nexus-school-a`). null이면 라우팅 기본값.
- `allowed_knowledge_sources`: `tb_knowledge.source` 화이트리스트 (빈 배열=전체 허용).
- `api_keys`: 테넌트 식별용 토큰 목록.
- `adapter_name_prefix`, `metadata`(JSON).

기본 등록: `default` (kowiki + sample만 접근). 학교/기업 예시는 주석 처리되어 있음.

---

## 5. Provider 추상화

위치: `core/model/inference.py:65 ModelProvider` (ABC) + `:134 LocalModelProvider` (구현).

**ABC 인터페이스**:
- `async stream(messages, system_prompt, tools, temperature, max_tokens, stop_sequences, model_override, enable_thinking) -> AsyncGenerator[StreamEvent]`
- `async embed(texts) -> list[list[float]]`
- `async health_check() -> bool`
- `async count_tokens(messages) -> int`
- `get_config() -> ModelConfig`

**LocalModelProvider** (유일한 구현체):
- vLLM OpenAI 호환 `/v1/chat/completions`로 SSE 스트리밍.
- `model_override` 파라미터로 런타임 LoRA 어댑터 전환 (Part 2.5 라우팅).
- `enable_thinking` 3-state: `False`(빈 `<think></think>` 강제, 기본), `True`(thinking 허용), `None`(파라미터 자체 생략 — Scout/llama.cpp용).
- httpx 단일 클라이언트 (`max_connections=20, max_keepalive=10`, read timeout 300s).
- 컨텍스트 초과 자동 재시도(최대 3회): vLLM 에러 본문에서 실제 input_tokens 파싱 → max_tokens 자동 축소.
- Scout(Qwen3.5-4B on llama.cpp) 별도 프로바이더: `core/model/scout_provider.py`.

`core/orchestrator/model_dispatcher.py`가 hardware tier에 따라 worker/scout 프로바이더를 합성.

라우팅(`core/orchestrator/routing.py`, config: `nexus_config.yaml:58 routing`):
- `KNOWLEDGE_MODE` → `qwen3.5-27b` 베이스, T=0.2, 2048 tokens.
- `TOOL_MODE` → `nexus-phase3` LoRA, T=0.3, 4096 tokens.
- `CHAT_MODE` → 베이스, T=0.5, 512 tokens, RAG 미주입.
- 분류기 종류 `heuristic` (현재). YAML로 키워드/단어경계/regex 패턴 외부화 가능.

---

## 6. API Key Pool / Rate Limiting / 쿨다운

**현재 Nexus는 외부 LLM Provider가 아니라 자체 vLLM 1대만 호출한다.** 따라서 AgentHub식 "여러 LLM 키 라운드로빈 풀"은 없음.

대신 다음이 있다:
- **에러 분류 + 지수 백오프 재시도** (`core/orchestrator/retry.py:35 ErrorCategory`):
  - 9 카테고리: `TRANSIENT(5xx)`, `RATE_LIMIT(429)`, `CONTEXT_TOO_LONG`, `OOM`, `MODEL_ERROR`, `INVALID_OUTPUT`, `STREAM_STALL`, `CONNECTION`, `FATAL`.
  - 카테고리별 max retries (기본): TRANSIENT=5, RATE_LIMIT=8, OOM=3, FATAL=0.
- **API 측 rate limit 미들웨어 없음** (LAN-only가 1차 방어).
- **테넌트 호출 통계만 수집** (`web/app.py:115 tenant_stats`) — 한도 강제 X.

**AgentHub 통합 시점에서 `IApiKeyRateLimiter`/쿨다운 로직은 Nexus 외부(=AgentHub `CallNexusAsync` 클라이언트 측)에서 수행해야 한다.** Nexus는 한 대의 GPU만 보호하면 되므로 `429`를 받으면 그대로 클라이언트에 전파.

---

## 7. AgentHub 옵션 B 통합 — 클라이언트가 알아야 할 것

### 7.1 호출 엔드포인트

AgentHub의 `CallNexusAsync` 클라이언트는 다음 두 엔드포인트를 사용한다:

**A) 비스트리밍 (단순 채팅)**
- `POST {NEXUS_BASE}/v1/chat`
- 요청 본문 (Pydantic `ChatRequest` — `web/app.py:258`):
  ```json
  {
    "message": "사용자 입력 텍스트",
    "session_id": "uuid-from-AgentHub-ChatConversation",
    "model": "primary",
    "tenant_id": "school-a"
  }
  ```
- 응답 (`ChatResponse` — `web/app.py:291`):
  ```json
  {
    "session_id": "...",
    "response": "어시스턴트 응답 텍스트(누적)",
    "tool_calls": [],
    "usage": {"input_tokens": N, "output_tokens": N, "total_tokens": N}
  }
  ```

**B) SSE 스트리밍 (메인 채팅 흐름)**
- `POST {NEXUS_BASE}/v1/chat/stream`
- 요청 동일.
- 응답: `text/event-stream`, `data: {json}\n\n` 프레임. SSE 주석 `: heartbeat Ns\n\n`도 섞여 옴 — 클라이언트 JSON 파서는 `data:` 프레임만 처리.
- 데이터 프레임 type 종류 (`StreamEventType`): `message_start`, `text_delta`, `tool_use`, `tool_result`, `usage_update`, `message_stop`, `error`.
- 응답 헤더 `X-Session-ID` (서버가 새로 생성한 경우 포함).

### 7.2 헤더/인증

3가지 방식 중 **하나 이상**:
- `X-Tenant-ID: <tenant_id>` (권장, 명시적)
- `Authorization: Bearer <api_key>` (api_keys[]에 등록된 토큰)
- 본문 `tenant_id` 필드

**우선순위는 body > header > Bearer > default.** AgentHub는 자기 ChatConversation에 매핑되는 tenant_id를 `X-Tenant-ID`로 보내는 것이 가장 명확. Nexus 자체 API 키는 1차적으로 LAN 격리 + 테넌트 격리 용도이지 인증 강제는 아니다 → AgentHub와 Nexus 사이에 별도 공유 시크릿(예: `Nexus__SharedSecret`)을 추가하면 운영 안전성 강화 가능 (현재는 미구현, 추가 항목).

### 7.3 session_id ↔ ChatConversation 매핑

- AgentHub `ChatConversation.Id` (또는 별도 `NexusSessionId` 컬럼)을 Nexus session_id로 1:1 매핑 권장.
- Nexus는 session_id가 들어오면 Redis(`session:{id}:context`)에서 이전 대화를 자동 복원하므로, AgentHub는 매 호출마다 전체 히스토리를 재전송할 필요 **없음** — `message`(이번 턴 사용자 발화) + `session_id`만 보내면 충분.
- 단 AgentHub가 자체 히스토리를 정본(source of truth)으로 삼으려면 매번 `DELETE /v1/sessions/{id}` 후 재시작 또는 Nexus 측 `clear_messages()` 강제 호출 같은 정책을 협의해야 함.
- session_id 검증: 슬래시/백슬래시/`..`/널 문자 포함 시 400 (`web/app.py:906`).

### 7.4 SSE 형식 (구체)

샘플 프레임:
```
data: {"type":"message_start","session_id":"...","model_id":"nexus-phase3"}

data: {"type":"text_delta","session_id":"...","text":"안녕하"}

data: {"type":"text_delta","session_id":"...","text":"세요"}

: heartbeat 20s

data: {"type":"usage_update","session_id":"...","usage":{"input_tokens":120,"output_tokens":42}}

data: {"type":"message_stop","session_id":"...","stop_reason":"end_turn"}
```
에러 시:
```
data: {"type":"error","session_id":"...","error_code":"stream_aborted","message":"HTTPError: ..."}
```

AgentHub의 SignalR `ChatHub`로 그대로 다시 푸시할 때는 `text_delta`만 누적하여 `ReceiveMessage`로 보내고, `usage_update`는 `ApiUsage` 엔티티 기록용으로 분리하는 패턴 권장.

### 7.5 에러 / 타임아웃

- **타임아웃 권장값** (AgentHub `HttpClient` 측):
  - connect timeout: 10s
  - read timeout: 300s (Nexus 자체도 `read_timeout=300`)
  - SSE의 경우 클라이언트가 5분 이상 무이벤트 시 끊는 게 합리적 (heartbeat 20s 주기로 옴).
- **재시도**: Nexus 응답 5xx, `error_code: HTTP_5xx`, `error_code: stream_aborted`는 AgentHub 측에서 ApiKeyPool 쿨다운 + 폴백 모델로 fallback. `error_code: CONTEXT_OVERFLOW`는 사용자에게 즉시 표시.
- **GPU 서버 부재**: `/health`에서 `gpu_server: "unreachable"` 또는 `"unhealthy"` 반환 — AgentHub 헬스체크가 이를 보고 Nexus를 일시 비활성.

### 7.6 도구 (tool_use)

Nexus는 자체 24+ 내부 도구(Read/Write/Edit/Bash/Glob/Grep/Agent/...)를 가지고 있고 LLM이 직접 호출한다. 그러나 **이 도구는 nexus 내부 컨텍스트(파일시스템, 작업 디렉토리)에서 실행**되는 것이므로, AgentHub의 일반 사용자 채팅 시 비활성화하거나 web 전용 8개 도구 풀(`web/app.py:388` "웹 도구 8개로 축소")만 노출하는 것이 맞다. 현재 web 모드는 이미 24→8로 축소되어 있음. AgentHub 통합 시 추가로 `tool_calls`를 클라이언트에 전달할지 여부 결정 필요.

---

## 8. DB 스키마

### 8.1 PostgreSQL — `nexus` 데이터베이스 (`192.168.10.39:5440`)

**핵심 테이블** (운영 중):
- `tb_knowledge` (`core/rag/knowledge_store.py:55 _DDL_SCHEMA`): id PK, source, title, section, content, chunk_index/total_chunks, tags TEXT[], embedding vector(1024), created_at, metadata JSONB. 인덱스: source / title / GIN(tags) / IVFFlat(embedding cosine).
- `tb_memories` — 장기 EPISODIC 대화 기억 (`core/memory/long_term.py`).
- `tb_symbols` — 코드 심볼 인덱스 (`core/rag/symbol_store.py`, Phase 10.0).

### 8.2 통합 DB로 이전할 것인가?

**권고: 유지 (별도 `nexus` DB)**.

이유:
1. Nexus는 에어갭 GPU 머신 인접 인프라(`192.168.10.39`)에서 컨테이너로 운영. AgentHub 본 서비스 DB(MSSQL→PostgreSQL 마이그레이션 후 Agent_Hub 스키마)와 라이프사이클이 다름.
2. `tb_knowledge`는 위키덤프 100만 청크 + IVFFlat 인덱스로 데이터 부피가 크고 빌드 비용이 높다.
3. AgentHub의 `KnowledgeBaseDocument` / `DocumentChunk`(1536d, `text-embedding-3-small`)와 차원이 다르고 (Nexus=1024, AgentHub=1536), 모델·컬럼·정책이 모두 상이.
4. 멀티테넌시는 Nexus 자체에서 `allowed_knowledge_sources` 화이트리스트로 격리.

대신 통합 항목은 **운영 메타만 동기화**: AgentHub `ApiServices` 시드에 `serviceType="nexus"`로 등록하고, 사용량/호출 로그는 AgentHub `ApiUsage`에 기록(Nexus는 `/metrics`로 노출만).

### 8.3 Redis 공유

`nexus` Redis는 `docutil-redis:6340 db=6`을 공유. AgentHub Redis(다른 db 또는 다른 인스턴스)와 키 충돌 없도록 prefix 분리(`nexus:`/`session:`) 유지.

---

## 9. 외부 노출 금지 강제 메커니즘

다층:
1. **`air_gap_mode: true`** (`config/nexus_config.yaml:232`) — 운영 플래그.
2. **`GPUServerConfig.validate_url_is_local`** (`core/config.py:42`) — GPU URL이 localhost / 10. / 172. / 192.168.이 아니면 `UserWarning`.
3. **CORS LAN-only** (`web/middleware.py:142 ALLOWED_ORIGINS` + `:177 add_lan_origin`) — `192.168.*`, `10.*`, `172.16~31.*`만 허용. 외부 IP 추가 시도 시 거부 + 경고 로그.
4. **Permission deny rules** (`config/permission_rules.yaml:12`) — `WebFetch`, `WebSearch` 도구 자체 차단.
5. **Bash deny patterns** — `curl|wget|nc|ncat` 차단(`permission_rules.yaml:58`).
6. **방화벽** (배포 측) — Nexus 포트는 LAN 인터페이스에만 바인딩 (운영자 책임).

**AgentHub와의 결합:** AgentHub 서버는 동일 LAN(또는 VPN/Tailscale로 연결된 보안망) 안에서 Nexus를 호출해야 한다. 외부에서 AgentHub로 들어오는 사용자 요청은 AgentHub의 `IPiiDetectionService` + `IBannedWordService`를 통과한 뒤에야 Nexus로 위임.

---

## 10. 알려진 한계 / 위험

- **컨텍스트 8,192 토큰** (`max_context_tokens: 8192`) — 긴 문서 RAG는 조각 검색 + 요약 필요. 긴 시스템 프롬프트는 입력만으로 컨텍스트를 잡아먹을 수 있고, `CONTEXT_OVERFLOW` 에러로 사용자에게 표시됨.
- **단일 GPU(RTX 5090) + `max_num_seqs: 1`** (`config/model_profiles.yaml:19`) — Primary 모델 동시 처리 1건. 많은 사용자가 동시에 보내면 큐잉 발생 → AgentHub 측에서 동시 호출 제한(per-tenant semaphore) 권장.
- **자체 모델 응답 품질**: Phase3 LoRA가 도구 호출은 강화했지만 일반 지식 표현이 좁아져서 Part 2.5 라우팅으로 해결 — 라우팅 분류기 오탐(예: "파일" 키워드 포함된 인사)이 TOOL_MODE를 트리거할 수 있음.
- **인증 부재**: Nexus 자체는 401을 반환하는 미들웨어가 없다. 외부에서 도달 가능한 환경에서는 즉시 노출. 1차 방어는 LAN 격리.
- **Redis 인메모리 폴백** (`core/memory/short_term.py:48`) — Redis 장애 시 단일 프로세스 메모리로 폴백되어 멀티 프로세스/재시작 시 세션 유실. 폴백은 개발 편의용.
- **세션 history budget 6,000자** — 정확한 토큰 카운트가 아니라 글자 수 휴리스틱이라 Worker가 입력 토큰 초과 시 자동 축소 재시도에 의존.
- **`tenant_stats` 메모리 누적** (`web/app.py:115`) — 프로세스 메모리에만 저장, 영속화 X. 재시작 시 0.
- **하드코드된 시크릿 위험**: `config/nexus_config.yaml:29 password: "idino@12"` (PostgreSQL), `redis password: "docutil_redis_2024"`가 평문 yaml에 박혀 있음 — `.env`/Vault로 이동 필요. 통합 단계에서 같이 정리.

---

## 11. monorepo 통합 시 변경 필요 항목

### 11.1 Nexus 자체 변경 (최소화)

**원칙: 독립 운영. 코드 변경 없이 IDINO_Agent_Hub의 `nexus/` 워크트리로 그대로 흡수.**

추가 권장 사항만:
1. **공유 시크릿 인증 미들웨어 추가** — `Authorization: Bearer <hub-shared-secret>` 검증 미들웨어 1개 추가, AgentHub만 호출 가능하게. (현재 미구현)
2. **시크릿 외부화** — `config/nexus_config.yaml`의 PG/Redis 패스워드를 `.env`로 빼고 `pydantic-settings`로 합치기. 평문 커밋 제거.
3. **`/health` 응답 풍부화** — vLLM 모델 ID, GPU VRAM 사용률, 큐 깊이를 함께 노출하면 AgentHub 헬스체크가 더 의미 있다.
4. **ServiceType 명세** — `nexus` ServiceType을 AgentHub `ApiServices` 시드에 등록 (모델 카탈로그: `nexus-phase3`, `qwen3.5-27b`, `exaone-7.8b`).

### 11.2 AgentHub 측 변경 (옵션 B 본체)

1. **`Settings/NexusSettings.cs`** 신설 — `BaseUrl`, `EmbeddingUrl`, `SharedSecret`, `DefaultTenantId`, `TimeoutSeconds`, `HealthCheckIntervalSeconds`.
2. **`Services/INexusClient` + `NexusClient`** — Named HttpClient(`"nexus"`) 사용, 위 7.1~7.6 명세에 맞춘 `CallNexusAsync(messages, sessionId, tenantId, model, ct)` (스트리밍/비스트리밍 2메서드).
3. **`AiProxyService`의 ServiceType 분기 추가** — `"nexus"` 케이스에서 `INexusClient`로 위임. 기존 OpenAI/Claude/Gemini와 동일하게 `IApiKeyPoolService`/`IApiKeyRateLimiter` 통과 (Nexus는 단일 키지만 동일 흐름 유지).
4. **`ChatService` SSE 변환** — Nexus의 `text/event-stream` 프레임을 ChatHub `ReceiveMessage`로 재발신.
5. **`ChatConversation` 스키마 보강** — `NexusSessionId`(nullable)로 1:1 매핑 보관.
6. **`ApiUsage` 기록 매핑** — Nexus `usage_update` 이벤트의 `input_tokens` / `output_tokens`를 AgentHub `ApiUsage.PromptTokens` / `CompletionTokens`에 적재.
7. **DI 등록**: `Program.cs`의 Named HttpClient `"nexus"` (BaseUrl from `NexusSettings`, timeout 300s, retry 정책).
8. **PII / BannedWord 통과**: Nexus는 입력 검증을 하지 않으므로 AgentHub의 `IPiiDetectionService` + `IBannedWordService`를 호출 직전에 반드시 통과시킨다 (anti-patterns.md #12).
9. **`appsettings.json`**:
   ```json
   "Nexus": {
     "BaseUrl": "http://192.168.x.x:8000",
     "DefaultTenantId": "default",
     "SharedSecret": "(env)",
     "TimeoutSeconds": 300
   }
   ```
10. **TestServer/통합 테스트** — `WebApplicationFactory`에서 `NexusClient`를 mock으로 교체.

### 11.3 운영/배포

- IDINO_Agent_Hub monorepo에 `nexus/`는 그대로 위치. 빌드/배포는 별도 도커 컨테이너 (`docker-compose nexus`, GPU 머신에서 실행).
- `progress.md` / `CLAUDE.md`(루트)에 "Nexus는 옵션 B로 통합, 외부 노출 금지(LAN)" 라인 명시.
- 모니터링: AgentHub Hangfire가 Nexus `/health`/`/metrics`를 주기 폴링 → 사용량 대시보드.

---

## 부록 — 주요 파일 위치 요약

- 진입: `D:\workspace\nexus\web\app.py`
- 미들웨어/CORS: `D:\workspace\nexus\web\middleware.py`
- 4-Tier 1: `D:\workspace\nexus\core\orchestrator\query_engine.py`
- 4-Tier 2: `D:\workspace\nexus\core\orchestrator\query_loop.py`
- 4-Tier 3: `D:\workspace\nexus\core\model\inference.py`
- 4-Tier 4 / Retry: `D:\workspace\nexus\core\orchestrator\retry.py`
- 라우팅: `D:\workspace\nexus\core\orchestrator\routing.py`
- 디스패처: `D:\workspace\nexus\core\orchestrator\model_dispatcher.py`
- 단기 메모리: `D:\workspace\nexus\core\memory\short_term.py`
- 트랜스크립트: `D:\workspace\nexus\core\memory\transcript.py`
- 지식 스토어: `D:\workspace\nexus\core\rag\knowledge_store.py`
- 설정 모델: `D:\workspace\nexus\core\config.py`
- 메인 yaml: `D:\workspace\nexus\config\nexus_config.yaml`
- 테넌트: `D:\workspace\nexus\config\tenants.yaml`
- 권한: `D:\workspace\nexus\config\permission_rules.yaml`
- 모델 프로필: `D:\workspace\nexus\config\model_profiles.yaml`
- 사양서(상세): `D:\workspace\nexus\user_mig\PROJECT_NEXUS_SPEC_v6.1_EN.md` (~510KB)
- 규칙: `D:\workspace\nexus\.claude\rules\*.md`
