# DocUtil — IDINO Agent Hub 통합 사전 조사

> 조사일: 2026-05-04 / 대상 워킹디렉토리: `D:\workspace\document_utilization`
> 통합 위치: AgentHub monorepo의 사용자 챗봇·RAG 단일 권위 (Data Plane + KB)
> 참고: `docs/techspec.md` v1.6, `docs/phase4_s1~s3_completion_report.md`, `docs/s0_inventory_report.md`

---

## 1. 시스템 한 줄 요약 + 기술 스택

DocUtil은 **조직 문서를 업로드·파싱·벡터화하여 RAG 챗봇·검색·보고서/PPT 생성을 제공하는 풀스택 시스템**이며, 2026-04-19부터 DocumentSchema 기반 신규 생성 엔진(Mode A 자유 생성 + Mode B 양식 채우기)으로 전면 재설계 중(Phase 4, 14.6주 중 ~54% 완료).

| 계층 | 기술 |
|---|---|
| Frontend | Next.js 16 (App Router, Turbopack), TypeScript, Tailwind, shadcn/ui, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2 async, Pydantic v2, Alembic |
| DB / Vector / Cache / MQ | PostgreSQL 17 / Qdrant 1.16 (dense 1536D + sparse BM25) / Redis 7 / RabbitMQ 4 + Celery |
| Object Storage | MinIO (`documents` 버킷, presigned URL 미사용 정책) |
| LLM | OpenAI / Azure OpenAI / Gemini / Anthropic Claude / vLLM / SGLang (멀티 프로바이더) |
| 이미지 생성 | OpenAI DALL-E 3 + Unsplash 스톡 자동 fallback |
| OCR | docling (granite-docling-258M) + pdf2image + pytesseract + easyocr + surya-ocr |
| 모니터링 | Prometheus + Grafana + Loki + Flower (14컨테이너 운영) |
| Infra | Docker Compose, Nginx, Ubuntu 24.04 사내 서버 (192.168.10.39) |

외부 의존성(런타임): PostgreSQL · Qdrant · Redis · RabbitMQ · MinIO · Unsplash API · OpenAI · (옵션) Azure / Gemini / Claude / vLLM / SGLang / Docling VLM / Reranker. **LibreOffice는 미설치 상태**(S5 사이드카 후보).

---

## 2. 현재 완성도 (Phase 4 진척)

| 스프린트 | 상태 | QA | 주요 산출 |
|---|---|---|---|
| S1 (DocumentSchema MVP) | 완료 (2026-04-23) | 84 | DocumentSchema + 6 컴포넌트, `/v2/documents` POST/GET/PATCH, `agentic_rag.py` dead code 삭제 |
| S2 (PPTX Mode A + archive) | 완료 (2026-04-23) | 86 | 8 컴포넌트 PPTX 빌더, `layout_resolver` (Phase0 하드코딩 해소), export_worker, `/reports` 410 Gone |
| S3 (컴포넌트 확장 + 이미지) | 완료 (2026-04-23) | 80 | 14 컴포넌트, Unsplash→DALL-E auto_select, `tb_organization_quotas` |
| S4 (Mode B + 전환) | 대기 | — | slot-fill, `POST /v2/documents/{id}/switch-mode`, `(admin)/template-designer/` |
| S5 (HWPX + DOCX) | 대기 | — | python-hwpx, lxml fallback, LibreOffice 사이드카 |
| S6 (RAG 품질 + 색상) | 대기 | — | 회의록 전용 프롬프트, Agentic RAG 챗봇 활성화 |
| S7 (인라인 편집 + 병존 제거) | 대기 | — | `report_generator.py`/`jinja2_engine.py` 폐기 |

37/68 영업일 (≈54%) 완료. 미완성/연기:
- **Mode B 전환 매핑** (S4) — 자동 매핑 ≥85% 목표
- **HWP 생성** — Linux/Docker에서 사실상 불가, **포기 결정**(UI에서 HWPX 안내). HWPX 생성도 `python-hwpx` 신생 라이브러리라 한컴 2020/2022 실기 열기 PoC 필요
- **회의록·요약 RAG 품질** (S6) — Phase 0 진단 R1~R5 (`source_chat_session_id` 증발, `_load_source_chunks` LIMIT 100, 회의록 전용 스키마 부재) 대부분 코드 잔존
- **`reports`·`templates`·`workers/report_generator.py`** — `/reports` 410 Gone 상태로 읽기만 유지, S7에 완전 삭제 예정
- 챗봇 응답 평균 3.6s (목표 3s 미달, W2)
- 한국어 출력 비율 0.56~0.66 (W5)

---

## 3. 도메인 모델 (RAG 중심)

| 엔티티 (테이블) | 핵심 컬럼 | 위치 |
|---|---|---|
| `Organization` (`tb_organizations`) | id, name, slug, settings(JSONB) — `organization_type` 컬럼 없음(Q4 외부 고객사 온보딩 시 추가) | `modules/organizations/models.py` |
| `User` (`tb_users`) | username, email, password_hash, role, organization_id, department_id | `modules/users/models.py` |
| `Document` (`tb_documents`) | folder_id, organization_id, **visibility(6단계)**, department_id, project_id, format(15종), storage_path, status, page_count, chunk_count, language, checksum_sha256 | `modules/documents/models.py:94` |
| `DocumentChunk` (`tb_document_chunks`) | document_id, chunk_index, chunk_type(text/table/image_caption/header/list/code), content, page_number, section_title, **qdrant_point_id** | `modules/documents/models.py:170` |
| `ChatSession` (`tb_chat_sessions`) | user_id, organization_id, search_scope_id, scoped_document_ids(UUID[]), is_active | `modules/chat/models.py:26` |
| `ChatMessage` (`tb_chat_messages`) | session_id, role(user/assistant/system), content, **citations(JSONB)**, retrieved_chunks(JSONB), model_used, token_count_in/out, latency_ms, hallucination_score | `modules/chat/models.py:67` |
| `DocumentV2` (`tb_documents_v2`) | document_type(7종), mode(free_generation/template_fill), status, schema_version, **document_schema(JSONB)**, llm_provider/model, prompt/completion_tokens, source_document_ids(UUID[]), source_chat_session_id, agent_id, template_id | `modules/documents_v2/models.py:49` |
| `DocumentV2Template` (`tb_documents_v2_templates`) | name, document_type, **skeleton_schema(JSONB)**, slot_definitions(JSONB), sample_prompt, is_active | `modules/documents_v2/models.py:205` |
| `Agent` (`tb_agents`) | agent_type(chatbot/report/proposal/minutes), system_prompt, llm_model, temperature, max_tokens | `modules/agents/models.py` |
| `SearchScope` (`tb_search_scopes`) | 검색 범위(프로젝트/부서/조직 단위) — 챗봇·검색이 참조 | `modules/search_scopes/models.py` |
| `tb_documents` 6단계 visibility | public / all_departments / department_only / project_only / confidential / hidden | `modules/documents/models.py:40` |
| `tb_organization_quotas` | (organization_id, quota_type, year_month) UNIQUE — DALL-E 월 쿼터 | Alembic 009 |
| `tb_generated_reports_archive` | (구) 보고서 결과. S2 D6에 archive 리네이밍, 읽기 전용. S7에 drop 예정 | `modules/reports/models.py` |

벡터 저장소(Qdrant): collection `documents`, dense 1536D + sparse BM25 (named vectors). payload에 `document_id`, `organization_id`, `chunk_index`, `chunk_type`, `visibility`, `department_id`, `project_id` 등 필터 키 포함.

---

## 4. API 표면적 (`/api/v1/...`)

`backend/app/main.py:144-163` — 라우터 18개 등록.

**사용자 API** (인증 후 본인/소속 조직 자원만):
- `auth/*` (login, refresh, logout, password_reset)
- `documents/*` (upload, bulk-upload, list, detail, download, delete, chunks, SSE 진척률)
- `search/*` (hybrid, keyword, chatbot, qa, history)
- `chat/*` + WebSocket `chat/ws/{session_id}` (REST + WS 병행)
- `v2/documents/*` (Mode A 생성, 목록, PATCH locked 보호, export PPTX/DOCX, presigned 대신 API 프록시 다운로드)
- `reports/*` (읽기만, 쓰기 410 Gone)
- `templates/*` (구 jinja2 템플릿, S7에 제거)
- `agents/*`, `projects/*`, `search_scopes/*`, `faq/*`

**운영자 API**:
- `admin/dashboard/*` (metrics, search-usage, upload-status, response-time, search-errors)
- `users/*`, `organizations/*`, `api_keys/*` (사용자/조직/API 키 CRUD)
- `audit/*` (감사 로그)
- `evaluation/*` (RAGAS 기반 품질 평가)
- `organizations/{id}/quotas/*` (DALL-E 월 쿼터 GET/PUT)

**인증 흐름** (`core/dependencies.py:51-131`):
- JWT (RS256, RSA 키 미설정 시 HS256 fallback / `core/config.py:209`) → `TokenData(user_id, organization_id, role)` 추출
- 역할 7단계 — `super_admin`, `admin`, `org_admin`, `manager`, `editor`, `member`, `viewer`
- `require_role(["super_admin", "admin", "org_admin"])` 데코레이터로 게이트
- WebSocket: 토큰을 query string으로 전달 (보안 약점)

게스트/공개 채팅 경로는 별도로 두지 않는다(모든 `/api/v1/*`가 인증 필수).

---

## 5. RAG 파이프라인

```
업로드(documents/router.py:upload)
  → MinIO 저장 + tb_documents.status='waiting'
  → Celery: document_processor.process_document
    ├─ docling VLM 파싱 (PDF/DOCX/PPTX/HWP/HWPX/이미지 OCR)
    ├─ olefile (HWP) + zipfile (HWPX) 보조
    ├─ Chunk 분할 (chunk_type 분류) → tb_document_chunks
    └─ embedding_generator.generate_embeddings.delay(...)
       ├─ Dense: OpenAI text-embedding-3-small (1536D) 또는 vLLM Qwen3-Embedding (2048D)
       └─ Sparse: fastembed BM25
       → Qdrant upsert (named vectors dense + sparse)
       → tb_documents.status='completed'

검색(search/service.py:hybrid_search)
  1. Visibility scope 적용 (effective_doc_ids 계산)
  2. Dense embedding 생성 → Qdrant dense 검색
  3. SQL BM25 sparse 병행 (PostgreSQL FTS 또는 Qdrant sparse)
  4. RRF (Reciprocal Rank Fusion) 융합
  5. CrossEncoder Reranker (Qwen3-Reranker-8B) Top-K
  6. SearchHistory 기록

챗봇(chat/websocket.py + chat/service.py)
  → SearchService.hybrid_search → 컨텍스트 합성 → LLM 스트리밍
  → tb_chat_messages에 citations + retrieved_chunks 저장

문서 생성 신규(documents_v2/service.py:generate)
  1. 문서 ID 선생성
  2. build_rag_context(prompt) → context_text + citations
  3. Agent 프롬프트 로드
  4. LLM.generate_with_schema(DocumentSchema)
  5. _auto_fill_image_sources (Unsplash → DALL-E fallback)
  6. tb_documents_v2 저장
```

각 단계 위치:
- 파싱: `integrations/docling/docling_service.py`, `workers/document_processor.py`
- 청크: `workers/document_processor.py` (chunking 헬퍼 내부)
- 임베딩: `workers/embedding_generator.py:148` (`_generate_dense_embeddings`, `_generate_sparse_embeddings`)
- Qdrant: `integrations/vector_store/qdrant_client.py` (423 LOC, 단일 클라이언트)
- 검색: `modules/search/service.py:50` (1100+ LOC)
- 챗봇 LLM: `modules/chat/service.py`, `modules/chat/websocket.py`
- 문서 생성: `modules/documents_v2/service.py:307` (LLMClient 직접 사용)

---

## 6. AI 사용 지점 인벤토리

| 위치 | 호출 종류 | 모델/엔드포인트 | 비고 |
|---|---|---|---|
| `integrations/llm/factory.py:32` | LLM 클라이언트 팩토리 (단일 진입점) | openai / azure_openai / gemini / anthropic / vllm / sglang | task별 오버라이드(`chat_llm_provider` 등) |
| `integrations/llm/client.py:404` | OpenAIClient | `gpt-4o` (default, `core/config.py:131`) | Structured Outputs (strict) |
| `integrations/llm/azure_client.py:23` | AzureOpenAIClient | `azure_openai_deployment` env | OpenAI 호환 |
| `integrations/llm/gemini_client.py:143` | GeminiClient | `gemini-2.0-flash` | Discriminated Union 평탄화 fallback |
| `integrations/llm/claude_client.py:247` | ClaudeClient | `claude-sonnet-4-20250514` | Tool Use 변환으로 Structured 모사 |
| `integrations/llm/client.py` | VLLMClient / SGLangClient | `vllm_url`, `sglang_url` | OpenAI 호환 자체 호스팅 |
| `modules/documents_v2/service.py:307,319` | Mode A LLM 생성 | task=`report` 오버라이드 | `generate_with_schema(DocumentSchema)` |
| `modules/chat/service.py` (호출 체인) | 챗봇 응답 | task=`chatbot` | streaming + citations |
| `modules/search/service.py` (chatbot/qa) | 검색-증강 답변 | task=`chat` | hybrid 결과 → LLM |
| `workers/report_generator.py:932-945` | 구 Jinja2 보고서(레거시) | `generate_structured_sync` | S7에 폐기 |
| `workers/evaluation_runner.py:55-58` | RAGAS 평가 | LLM-as-judge | daily-evaluation Celery beat |
| `integrations/rag/graph_rag.py:105` | KG 추출 (옵션, `graph_rag_enabled=False`) | `OpenAIClient` 직접 사용 | 단일 진입점 우회 (P1 위반) |
| `workers/embedding_generator.py:148` | Dense embedding | `text-embedding-3-small` (1536D) **하드코딩 분기** | `embedding_provider=local`이면 vLLM Qwen3 (2048D) |
| `workers/embedding_generator.py:186` | Sparse BM25 | fastembed `Qdrant/bm25` | local-only (외부 호출 없음) |
| `integrations/image_generation/service.py:189-205` | DALL-E 3 이미지 | `dall-e-3` 하드코딩, `b64_json` | `from openai import AsyncOpenAI` 직접 import |
| `integrations/image_generation/service.py:238+` | Unsplash 검색 | `unsplash_access_key` | DALL-E 우선 fallback (`auto_select.py`) |

**모델 하드코딩 위치**:
- `core/config.py:131` `llm_model="gpt-4o"`, `:120` `anthropic_model="claude-sonnet-4-20250514"`, `:124` `google_model="gemini-2.0-flash"`
- `integrations/image_generation/service.py:198` `model="dall-e-3"`
- `core/config.py:140` `reranker_model="Qwen/Qwen3-Reranker-8B"`
- `core/config.py:145` `docling_model="ibm-granite/granite-docling-258M"`

**임베딩 차원**:
- OpenAI: 1536D (`openai_embedding_dimension`)
- 내부 GPU(vLLM Qwen3-Embedding-8B): 2048D (`embedding_dimension`)
- Qdrant collection은 단일 차원으로 고정 → 프로바이더 전환 시 collection 재생성 필요

---

## 7. 인증 / 권한 / Multi-Tenant

- **JWT**: `core/security.py` create/verify, RS256 우선 + RSA 키 없으면 HS256 (`core/config.py:209`)
- **역할 7단계**: super_admin, admin, org_admin, manager, editor, member, viewer
- **Multi-Tenant**: 모든 핵심 테이블에 `organization_id` FK (CASCADE). 모든 쿼리에 `WHERE organization_id = current_user.organization_id` 강제
- **6단계 visibility** (`modules/documents/models.py:40`): public / all_departments / department_only / project_only / confidential / hidden
- **`tb_document_access`**: confidential 가시성 명시 허용 사용자
- **API Key 인증**: `modules/api_keys/` — 외부 시스템 호출용. AES-256 (`encryption_key` env, 32바이트 hex 검증)
- **현재 조직**: 1개 (아이디노 / `default` slug). 외부 고객사 온보딩 미실시

---

## 8. 운영자 기능 카탈로그

| 기능 | 위치 | AgentHub 이관 vs 유지 |
|---|---|---|
| 대시보드 (메트릭/사용량/응답시간/에러) | `(admin)/dashboard` + `modules/admin/router.py` | **AgentHub로 흡수** — AgentHub의 분석 대시보드와 통합 |
| 사용자 관리 (admin-accounts) | `(admin)/admin-accounts` + `modules/users` | **AgentHub로 흡수** (Control Plane이 단일 사용자 권위) |
| 조직/부서 관리 | `(admin)/departments` + `modules/organizations` | **AgentHub로 흡수** |
| 프로젝트 관리 | `(admin)/projects` + `modules/projects` | **유지** — 문서 분류 축. AgentHub에서 BFF로 노출 |
| **문서 인덱싱 모니터링** | `(admin)/documents` + SSE 진척률 | **유지** — RAG 단일 권위 책임 |
| **검색 범위/스코프 관리** | `(admin)/search-scopes` | **유지** — RAG 도메인 |
| **검색 테스트 (운영자 view)** | `(admin)/search-test` | **유지** |
| **에이전트 관리** | `(admin)/agents` (1 file) + `modules/agents` | **AgentHub로 흡수** (AgentHub의 Agent가 단일 권위) |
| API 키 관리 | `(admin)/api-keys` + `modules/api_keys` | **AgentHub로 흡수** (AgentHub ApiKeyPool과 통합) |
| 평가 (RAGAS) | `(admin)/evaluation` + `modules/evaluation` | **유지** — RAG 품질 회귀 |
| 쿼터 관리 (DALL-E) | `(admin)/quotas` + Alembic 009 | **AgentHub로 흡수** (AgentHub ApiQuota 통합) |
| **템플릿 관리** | `(admin)/templates` (현재 1 file) + `(admin)/template-designer` (S4 신설) | **유지** — 문서 생성 도메인 |
| 도움말/Quick Guide/설정 | `(admin)/help`, `quick-guide`, `settings` | **AgentHub로 흡수** |
| FAQ | `modules/faq` | **AgentHub로 흡수** |
| 감사 로그 | `modules/audit` | **AgentHub와 병합** |

핵심 원칙: **사용자/조직/에이전트/API키/쿼터는 AgentHub Control Plane이 단일 권위**. **문서·청크·검색·임베딩·템플릿·평가는 DocUtil이 RAG 단일 권위**. AgentHub 운영자 화면은 **DocUtil API의 BFF**로만 동작.

---

## 9. Monorepo 통합 시 변경 필요 항목

### Phase 6 (운영자 UI 흡수)
1. DocUtil의 `(admin)/*` 라우트 중 사용자/조직/에이전트/API키/쿼터를 **AgentHub의 Vue Admin으로 이관**. DocUtil frontend는 사용자 화면 `(user)/*` + `(auth)/*`만 유지
2. AgentHub Vue 측에 **운영자 KB 관리 BFF** 추가 — DocUtil의 `documents` / `search-scopes` / `templates` / `evaluation` API를 호출하여 노출
3. DocUtil의 `modules/users`, `modules/organizations`, `modules/api_keys`, `modules/agents`, `modules/audit` **삭제** 후 AgentHub의 동일 도메인으로 위임 (DocUtil은 JWT만 검증)

### Phase 7 (LLM 호출 위임)
4. **`integrations/llm/factory.py`** — `create_llm_client(provider)`을 `AgentHubProxyClient`로 단일화. AgentHub `IAiProxyService` 또는 `/v1/chat/completions` 게이트웨이 호출
5. **`integrations/image_generation/service.py:189`** AsyncOpenAI 직접 import 제거 → AgentHub의 이미지 생성 API 위임 (DALL-E + Unsplash 모두)
6. **`integrations/rag/graph_rag.py:105`** `OpenAIClient()` 직접 사용 제거 (현재도 P1 위반)
7. **`workers/embedding_generator.py:148`** OpenAI Embedding 직접 호출 제거 → AgentHub embedding 게이트웨이 위임. Qdrant collection 차원은 통합 정책에 맞춰 재생성
8. DocUtil `core/config.py`의 `openai_api_key`, `anthropic_api_key`, `google_api_key`, `azure_openai_*` **모두 제거** — AgentHub만 보유
9. DocUtil의 `chat_llm_provider` / `report_llm_provider` / `template_llm_provider` 오버라이드는 AgentHub 측 ServiceType/Model 라우팅 정책으로 이전

### DB 스키마 (AGENT_HUB의 `document_utilization` 스키마)
10. PostgreSQL 단일 인스턴스에 **`document_utilization` 스키마 신설**, `tb_*` 테이블 모두 이관
11. `tb_users`, `tb_organizations`, `tb_user_roles` → AgentHub `auth` 스키마로 단방향 통합 (DocUtil은 view 또는 FK 참조)
12. `tb_agents` (4종 chatbot/report/proposal/minutes) → AgentHub `Agent`와 **통합** (필드 매핑: `system_prompt`, `llm_model`, `temperature`, `max_tokens` 1:1 호환)
13. `tb_api_keys` → AgentHub `ApiKey`로 통합. AES-256 암호화 키도 통일
14. Alembic head=009. AgentHub의 EF Core 마이그레이션과 병행 운영하거나, EF Core를 사용하지 않는 PostgreSQL 영역으로 분리
15. `tb_organization_quotas` → AgentHub `ApiQuota`와 형식 다름 (DocUtil은 `(org, quota_type, year_month)` UNIQUE, AgentHub는 사용자×ApiService). 정책 통합 필요

### Qdrant
16. **단일 Qdrant 클러스터 유지**. collection은 `documents`(DocUtil 전용) 1개. AgentHub의 자체 KB(`KnowledgeBaseDocument`/`DocumentChunk`)는 **deprecate**되므로 별도 collection 불필요
17. AgentHub의 기존 KB 데이터 → DocUtil의 `tb_documents` + `tb_document_chunks`로 이전 (UTF-8 파일은 그대로, embedding은 차원 통일 후 재생성)
18. AgentHub `EmbeddingService`(SIMD cosine) 코드는 **단일 collection 정책상 삭제** 또는 DocUtil로 흡수

### 운영자 KB 데이터 마이그레이션
19. AgentHub `KnowledgeBaseDocument` (PDF/Excel/Word/PPTX/HWP) → DocUtil `tb_documents` 일괄 import (uploader=admin, organization_id=AgentHub user의 org)
20. AgentHub `AgentDocument` N:M → DocUtil `search_scope` 또는 새 `tb_agent_documents` 테이블로 매핑

---

## 10. 외부 노출 API (AgentHub BFF용)

AgentHub Vue Admin이 호출할 DocUtil API 후보(인증: AgentHub JWT 또는 내부 mTLS):

| 기능 | DocUtil 엔드포인트 | 비고 |
|---|---|---|
| 문서 업로드 | `POST /api/v1/documents/upload` (multipart) | 운영자 KB 등록 |
| 문서 일괄 업로드 | `POST /api/v1/documents/bulk-upload` | 다중 |
| 인덱싱 진척률 | `GET /api/v1/documents/upload-progress/{job_id}` (SSE) | 실시간 모니터링 |
| 문서 목록 | `GET /api/v1/documents` (filters) | KB 카탈로그 |
| 문서 상세 + 청크 | `GET /api/v1/documents/{id}` + `/chunks` | 디버그 |
| 문서 삭제 | `DELETE /api/v1/documents/{id}` | KB 정리 |
| 검색 범위 CRUD | `/api/v1/search-scopes/*` | 컬렉션 단위 관리 |
| 운영자 검색 테스트 | `GET /api/v1/search/test?q=...` (visibility bypass) | 품질 점검 |
| 하이브리드 검색 (외부) | `POST /api/v1/search/hybrid` | AgentHub 챗봇이 RAG 위임 시 |
| 챗봇 검색-증강 답변 | `POST /api/v1/search/chatbot` | 외부 시스템에서 RAG 단답 |
| 평가 실행 | `POST /api/v1/evaluation/runs` | RAGAS 점수 |
| 템플릿 CRUD | `/api/v1/templates/*` (Mode B), `/api/v1/v2/documents/*` (Mode A) | 운영자 템플릿 디자이너 |
| 인덱싱 트리거(재처리) | `POST /api/v1/documents/{id}/reprocess` (S2 이후 유무 확인 필요) | OCR 실패 시 재시도 |
| 사용량/대시보드 메트릭 | `GET /api/v1/dashboard/*` | 단, AgentHub 자체 메트릭과 중복 |

**RAG 단일 권위 호출 예** (AgentHub 사용자 챗봇이 DocUtil RAG를 사용):
```
AgentHub Chat → POST /api/v1/search/chatbot
  body: { query, scope_id, user_id, organization_id, max_results }
  → DocUtil이 hybrid_search → LLM(AgentHub로 위임) → citations 반환
```

이때 **LLM 호출은 DocUtil 내부에서 하지 않고 AgentHub로 콜백**해야 순환 호출이 발생. → 권장: DocUtil은 `/search/hybrid` (LLM 미포함, 컨텍스트만 반환)을 노출하고, LLM 합성은 AgentHub 측에서 수행.

---

## 11. 미완성 / 기술 부채

| 항목 | 위치 | 비고 |
|---|---|---|
| `report_generator.py` 3702 LOC | `workers/report_generator.py` | S7에 완전 폐기 예정. 현재 410 Gone |
| `jinja2_engine.py` 2608 LOC | `workers/jinja2_engine.py` | 변수 치환 로직만 S4 이관, 나머지 폐기 |
| `graph_rag.py` `OpenAIClient()` 직접 사용 | `integrations/rag/graph_rag.py:105` | P1 단일 진입점 위반. `graph_rag_enabled=False` 기본 |
| 회의록·요약 부실 (R1~R5) | `reports/service.py:312-326`, `report_generator.py` | `source_chat_session_id` 증발, LIMIT 100, 회의록 전용 스키마 부재. S6 대상 |
| HWP 생성 불가 | — | Linux/Docker에서 한컴 SDK 사용 불가 → **포기**, HWPX 안내 |
| HWPX 한컴 호환성 미검증 | S5 PoC | `python-hwpx` 신생 라이브러리. 한컴 2020/2022 실기 열기 테스트 필요 |
| 한국어 출력 비율 0.56~0.66 | 컴포넌트 LLM | W5, S6 프롬프트 가중 개선 |
| 챗봇 응답 3.6s | `modules/chat` | W2, RAG 병렬화 또는 스트리밍 개선 필요 |
| OpenAI TPM 30k 초과 시 502 | `integrations/llm/client.py` | W6, 재시도/백오프 미구현 |
| `cors_origins=["*"]` 기본값 | `core/config.py:175` | `allow_credentials=True`와 조합 시 보안 약점 |
| `encryption_key` 기본값 노출 | `core/config.py:166-169` | `0123456789abcdef...` 32바이트 더미 |
| JWT WebSocket 토큰 query string | `chat/websocket.py` | 토큰 노출 위험. Subprotocol 또는 첫 메시지 인증 권장 |
| Nginx 4440 포트 connection refused | 인프라 | W1, S1~S3 내내 미해결 |
| `docker-compose.yml -Q` 영속성 | F1, W8 | 재배포 시 `document_export`/`evaluation` queue 재제거 위험 |
| 임베딩 차원 분기 (1536 vs 2048) | `workers/embedding_generator.py:148` | provider 전환 시 collection 재생성 필요. 통합 정책에 맞춰 단일화 |
| pyhwp 혼입 금지 | requirements 검증 | AGPL 라이선스 회피 |
| `graph_rag_enabled` 비활성 / `agentic_rag.py` 삭제됨 | — | S1 D9에 dead code 489줄 제거 |

---

## 12. 위험 요소 (통합 시)

| # | 위험 | 영향 | 완화 |
|---|---|---|---|
| W1 | **임베딩 차원 통일** — DocUtil 1536(OpenAI) vs 2048(Qwen3) 분기, AgentHub 1536. 단일 차원으로 강제 시 한쪽 collection 재생성 필요 | 인덱싱 다운타임 + 재처리 비용 | Phase 7 전에 차원 정책 확정 → 1536D 표준화 권장. AgentHub 임베딩도 AgentHub→DocUtil 위임으로 단일화 |
| W2 | **AgentHub `KnowledgeBaseDocument` → DocUtil `tb_documents` 마이그레이션** — visibility 6단계, department/project FK가 AgentHub에 없어 매핑 손실 | 권한 손실 위험 | 마이그레이션 시 default visibility=`department_only` + 운영자 검수 |
| W3 | **`tb_agents` 통합** — DocUtil 4종 vs AgentHub의 일반 Agent. agent_type CHECK 제약 + system_prompt 충돌 | Agent 동작 변경 | DocUtil agent_type을 AgentHub Agent의 metadata.tag로 보존 |
| W4 | **순환 호출** — AgentHub 챗봇 → DocUtil RAG → LLM(AgentHub) → ... | 무한 루프 / 타임아웃 | DocUtil은 컨텍스트만 반환(`/search/hybrid`), LLM 합성은 AgentHub 단일 책임 |
| W5 | **JWT 통합** — DocUtil RS256/HS256 fallback vs AgentHub HS256. 서명 키/algorithm 불일치 | 인증 단절 | 단일 키/algorithm 표준화. 클레임도 통일 (sub, organization_id, role) |
| W6 | **Multi-Tenant 정합** — DocUtil의 visibility(6단계) + department + project + scoped_document_ids는 AgentHub에 없음 | 정책 단순화 시 권한 폭증 | DocUtil 정책 그대로 유지, AgentHub Admin UI는 visibility CRUD 신설 |
| W7 | **Qdrant collection 단일성** — AgentHub용 collection 폐기 + 데이터 import 시 payload schema 차이 | RAG 결과 누락 | 사전 dry-run + payload 통일 마이그레이션 스크립트 |
| W8 | **`/v2/documents` 신규 vs `/reports` 410 Gone** — AgentHub BFF가 어떤 엔드포인트를 호출할지 결정 필요 | API 표면 혼란 | `/v2/documents`만 AgentHub에 노출, `/reports`는 내부 archive 전용 |
| W9 | **Phase 4 진행 중 통합 시작** — S4~S7 중에 monorepo 이전 시 코드 충돌 | 일정 지연 | S7 (병존 제거) 완료 후 통합 시작 권장 (~6주 추가 대기) 또는 Phase 4를 monorepo 내부에서 마무리 |
| W10 | **DALL-E / Unsplash 비용** — AgentHub 쿼터(`ApiQuota`)와 DocUtil `tb_organization_quotas` 정책 충돌 | 비용 폭주 또는 차단 | 단일 쿼터 시스템(AgentHub `ApiQuota`)로 통합, DocUtil 측은 호출 시 위임 |
| W11 | **HWP/HWPX 한국어 포맷 처리** — AgentHub는 미지원 | DocUtil 단독 책임 | DocUtil RAG 단일 권위 정책과 일치. AgentHub 흡수 불필요 |
| W12 | **Docker Compose 통합** — DocUtil 14컨테이너 + AgentHub IIS InProcess. 운영 모델 상이 | 배포 복잡도 | DocUtil은 Linux/Docker, AgentHub는 IIS 유지(서로 다른 호스트). LB/Reverse Proxy로 라우팅 |
| W13 | **`encryption_key`, JWT secret, OpenAI key 통합** — `.env` 분산 | 시크릿 누출 | Vault 또는 단일 secrets 저장소 도입 |
| W14 | **운영자 UI 흡수 시 Next.js admin 라우트 손실** — `(admin)/templates`, `template-designer`, `quotas`, `documents` 등은 React 코드를 Vue로 재작성 필요 | FE 재작성 공수 | DocUtil의 admin 페이지 수가 적어(~15개) Vue 재작성 가능. 디자이너만 React iframe로 임베드 |
| W15 | **회의록·요약 RAG 부실** — Phase 0 진단 R1~R5 미해소 상태로 통합되면 사용자 체감 품질 하락 | 출시 후 불만 | 통합 전 S6 완료 권장 |

---

## 13. 핵심 결론 (요약)

1. **DocUtil은 monorepo의 RAG/Data Plane**으로 적합 — 6단계 visibility, multi-tenant, hybrid 검색(dense+sparse+rerank), 14 컴포넌트 PPTX 생성, 14 컨테이너 운영 인프라가 갖춰져 있다.
2. **LLM 호출은 단일 진입점 `integrations/llm/factory.py`로 이미 정리됨** — Phase 7에서 이 파일만 `AgentHubProxyClient`로 교체하면 위임 완료. 단, `image_generation/service.py:189`와 `graph_rag.py:105`는 P1 위반 잔존(예외 처리 필요).
3. **AgentHub 자체 KB는 폐기**, DocUtil로 데이터 이전 후 단일 Qdrant collection 유지. 임베딩 차원은 1536D 표준화 권장.
4. **운영자 UI는 AgentHub Vue가 BFF로 흡수**하되, **문서 인덱싱/검색 범위/템플릿 디자이너/평가는 DocUtil 도메인 유지**. 사용자/조직/에이전트/API키/쿼터/감사는 AgentHub Control Plane이 단일 권위.
5. **통합 타이밍**: Phase 4 S7 완료(~6주) 후 또는 monorepo 내부에서 Phase 4 마무리. **회의록·요약 RAG 부실(S6)** 미해소 상태 통합은 사용자 체감 품질 위험.
6. **DB 통합**: PostgreSQL 단일 인스턴스에 `document_utilization` 스키마. AgentHub의 MSSQL→PostgreSQL 마이그레이션이 선행되어야 함.
7. **순환 호출 방지**: DocUtil은 `/search/hybrid`(컨텍스트만)를 표준 RAG 인터페이스로, LLM 합성은 AgentHub 단일 책임.
