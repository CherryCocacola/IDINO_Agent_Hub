# AI 호출 인벤토리

> **Phase 1 산출물** — 4개 서브프로젝트(`agenthub`/`docutil`/`career`/`nexus`)에서 발생하는 모든 LLM/임베딩/이미지 호출 지점을 카탈로그화한 문서.
> Phase 5에서 AgentHub `LlmRouting` 도입 시, Phase 7에서 본 인벤토리를 기준으로 직접 호출 → AgentHub Agent 위임으로 일괄 교체한다.
>
> **작성일**: 2026-05-05
> **기준 자료**: `user_mig/source_*.md` (4개 시스템 분석 보고서) + 본 작업의 grep 검증
> **참조**: `user_mig/TECHSPEC.md` §8 / §10, `.claude/rules/anti-patterns.md` #1·#3·#7·#8

---

## 0. 작성 가이드

### 0.1 항목별 기록 규약
| 필드 | 설명 |
|---|---|
| ID | 시스템 prefix + 일련번호 (`AH-1`, `DU-1`, `CA-1`, `NX-1`) |
| 위치 | `subproject/path/to/file.ext:line` (절대 경로 변환은 IDE에 위임) |
| 호출 방식 | OpenAI SDK / Anthropic SDK / Google SDK / LangChain / httpx / 내부 wrapper / 위임(httpx) |
| Provider | openai / claude / gemini / mistral / perplexity / copilot / azure-openai / nexus / dalle / unsplash 등 |
| Model | 하드코딩 모델명 또는 설정 키 |
| 트리거 | 사용자 액션 / 백그라운드 잡 / 스케줄러 / 다른 MS의 위임 |
| 입력 데이터 | 사용자 입력 / DB 데이터 / RAG 컨텍스트 / 학생 데이터 / 기타 |
| 민감도 | public / internal / confidential / pii |
| 우선순위 | P0~P3 (§0.2) |
| 목표 Agent (Phase 5+) | AgentHub의 어느 `AgentCode`로 매핑할지 |
| 비고 | 단일 진입점 위반, fallback 정책, 보안 위험 등 |

### 0.2 우선순위 분류
- **P0** — 사용자 트래픽 직접 영향 (메인 챗봇, 핵심 추천, 실시간 대화)
- **P1** — 사용자 보조 기능 (요약, 분류, 분석, Mode A 생성)
- **P2** — 백그라운드/배치 (인덱싱, 임베딩, 일일 리포트, RAGAS 평가)
- **P3** — 개발자 도구 / 학습 데이터 생성 / 사용 빈도 낮음

### 0.3 민감도 분류 (PII 정책)
- **public** — 공개 가능 (예: 일반 챗봇 인사)
- **internal** — 조직 내부 (예: 부서 문서 RAG)
- **confidential** — 기밀 (예: 학생 성적/평가, 인사 평가)
- **pii** — 개인 식별 가능 (이름·연락처·주민번호 포함 가능 입력)

> Hybrid 라우팅 정책(§10): `pii` → Internal(Nexus) 강제 / `confidential` → Internal 우선 / `internal/public` → External 허용.

---

## 1. 통계 요약

### 1.1 직접 LLM 호출 지점 (단일 진입점 위반 또는 게이트웨이 자체)

| 시스템 | Chat | Image | Embedding | Web/Tool | 합계 |
|---|---:|---:|---:|---:|---:|
| **agenthub** (게이트웨이 자체) | 7 (× sync+stream = 14 메서드) | 5 | 1 (`text-embedding-3-small`) | 1 (Tavily) | 8 분기 |
| **docutil** | 6 (단일 진입점 1 + 위반 5) | 1 (DALL-E) | 1 (자체 임베딩 워커) | 1 (Unsplash) | 9 |
| **career** | 11 (LangChain 4 + OpenAI SDK 7) | 0 | 1 (`text-embedding-3-small`) | 0 | 12 |
| **nexus** | 0 (외부 호출 없음 — LAN GPU만) | 0 | 0 | 0 | 0 |
| **합계** | **24** | **6** | **3** | **2** | **35** |

### 1.2 위임 호출 (이미 다른 MS의 AI 서비스를 호출 중인 형태)

| 호출자 | 호출 대상 | 위치 | Phase 7 변환 |
|---|---|---|---|
| coaching-service | `ai-service /ai/chat` | `coaching_service.py:560-562` | AgentHub `/v1/chat/completions` (Agent=`career-chatbot`) |
| competency-service | `ai-service /ai/analyze` | `competency_service.py:209-211` | AgentHub Agent=`career-competency-analyzer` |
| roadmap-service | `ai-service /ai/recommendations/tools` | `roadmap_service.py:578-580` | AgentHub Agent=`career-actionboard-orchestrator` |
| opportunity-service | (config만 정의, 실제 호출 미발견) | `config.py:25` | 호출 추가 시 AgentHub로 |
| skill-service | (config만 정의, 실제 호출 미발견) | `config.py:25` | 호출 추가 시 AgentHub로 |
| frontend (career) | `ai-service /ai/*` | `frontend/lib/api/ai.ts:5-9` | AgentHub로 직접 또는 BFF |

### 1.3 Provider별 사용 통계

| Provider | 사용 시스템 | 호출 지점 수 | 모델 (하드코딩) |
|---|---|---:|---|
| **OpenAI** | agenthub / docutil / career | 19 | `gpt-4o`(docutil 기본), `gpt-4o-mini`(career 기본), `text-embedding-3-small`(1536D) |
| **Anthropic Claude** | agenthub / docutil | 4 | `claude-sonnet-4-20250514`(docutil 기본) |
| **Google Gemini** | agenthub / docutil | 4 | `gemini-2.0-flash`(docutil 기본) |
| **Azure OpenAI** | agenthub / docutil | 3 | env `azure_openai_deployment` |
| **Mistral** | agenthub | 2 | env / API에서 모델 선택 |
| **Perplexity** | agenthub | 2 | env / API에서 모델 선택 |
| **Copilot (MS)** | agenthub | 2 | (azure-openai 별칭으로 처리) |
| **Tavily 검색** | agenthub | 1 | (검색 도구) |
| **vLLM (DocUtil 내부)** | docutil | (factory 분기) | 사내 호스팅 |
| **SGLang (DocUtil 내부)** | docutil | (factory 분기) | 사내 호스팅 |
| **DALL-E 3** | agenthub / docutil | 2 | `dall-e-3` |
| **Imagen 4 / Gemini Image** | agenthub | 2 | Vertex AI / Gemini API |
| **Flux 2 / Gen4 Image** | agenthub | 2 | Vertex AI |
| **Unsplash** | docutil | 1 | (스톡 이미지 fallback) |

### 1.4 우선순위별 분포

| 우선순위 | 건수 | 대표 호출 |
|---|---:|---|
| **P0** (사용자 직접) | 12 | docutil 챗봇 / career ActionBoard / agenthub 사용자 채팅 / agenthub OpenAI 호환 |
| **P1** (보조) | 13 | docutil Mode A 생성 / career 시뮬레이션 분석 / docutil 요약 / career 코칭 |
| **P2** (백그라운드) | 8 | docutil 임베딩 / career 임베딩 / docutil RAGAS 평가 / agenthub Tavily 검색 |
| **P3** (개발자) | 4 | docutil training/data_generator / docutil graph_rag(비활성) / agentic_search |

---

## 2. agenthub — 게이트웨이 자체

> AgentHub는 그 자체로 LLM 게이트웨이 (`AiProxyService.cs` 3,749 LOC, god class — H13).
> **이 표는 "프로바이더별 분기 위치"**이며, Phase 7에서 다른 시스템이 호출하게 되는 진입점이다.
> Phase 5에서 `LlmRouting` + `nexus` 분기 신설 시 이 자리에 추가된다.

### 2.1 Chat 분기 (`Services/AiProxyService.cs`)

| ID | 위치 (라인) | Provider | Stream 메서드 | 비고 |
|---|---|---|---|---|
| AH-1 | `:213` switch 진입 + `:297` `CallOpenAiAsync` | openai | `:720` `CallOpenAiStreamAsync` | 추론 모델(o1/o3/gpt-5)은 `max_completion_tokens` 사용, temperature 미전송 |
| AH-2 | `:651` `CallClaudeAsync` | claude | `:774` `CallClaudeStreamAsync` | system은 별도 파라미터 |
| AH-3 | `:814` `CallGeminiAsync` | gemini | `:1080` `CallGeminiStreamAsync` | role: `model` (assistant 대신) |
| AH-4 | `:1150` `CallPerplexityAsync` | perplexity | `:1253` `CallPerplexityStreamAsync` | sonar 시리즈 |
| AH-5 | `:1290` `CallMistralAsync` | mistral | `:1375` `CallMistralStreamAsync` | OpenAI 호환 변형 |
| AH-6 | `:1415` `CallCopilotAsync` | copilot (MS) | `:1510` `CallCopilotStreamAsync` | `azure-openai`/`microsoft-copilot` 별칭으로 라우팅 |
| AH-7 | `:1596` `CallAzureOpenAiAsync` | azure-openai | `:1759` `CallAzureOpenAiStreamAsync` | deployment 명 기반 |
| AH-8 | **(신규 Phase 5)** `CallNexusAsync` | nexus | (스트리밍 진짜 SSE) | TECHSPEC §10, ADR-1 옵션 B. 입력: messages + sessionId + tenantId, 출력: SSE 프레임 |

호출자(switch): `:213` (sync), `:240` (stream). `service.ServiceCode.ToLower()` 비교 → `_ => throw NotSupportedException` 폴백.

### 2.2 Image 분기 (`Services/AiProxyService.cs`)

| ID | 위치 (라인) | Provider | 비고 |
|---|---|---|---|
| AH-9 | `:2762` switch 진입 + `:2808` `CallDallEAsync` | dalle | OpenAI Images API |
| AH-10 | `:2892` `CallGeminiImageAsync` | gemini-image | Gemini 2.0 Image |
| AH-11 | `:3219` `CallImagen4Async` | imagen4 | Vertex AI 폴백 안내 (`:3331-3351` 주석) |
| AH-12 | `:3429` `CallGen4ImageAsync` | gen4-image | Vertex AI 인증 (OAuth, `AccessToken` 필요) — 운영 미설정 시 503 |
| AH-13 | `:3570` `CallFlux2Async` | flux2 | Vertex AI |

### 2.3 Web/검색 도구

| ID | 위치 | Provider | 비고 |
|---|---|---|---|
| AH-14 | `:440` 사용 + `:2589-2691` `SearchWithTavilyAsync` | tavily | `AiApiSettings:Tavily:ApiKey`, EnableWebSearch=true Agent에서 호출 |

### 2.4 OpenAI 호환 진입점 (외부 시스템 → AgentHub)

| ID | 위치 | 종류 | 비고 |
|---|---|---|---|
| AH-15 | `Controllers/OpenAICompatController.cs:135-180` | `POST /v1/chat/completions` | API Key 인증 (`X-API-Key` 또는 `Bearer ak-…`) |
| AH-16 | **가짜 SSE 핵심**: `:343` `Content.Split(' ')` + `:357` `Task.Delay(15)` + `:374` `data: [DONE]` | SSE 위장 (C9) | Phase 5에서 `IAsyncEnumerable<ChatChunk>` 진짜 SSE로 교체 |

### 2.5 Phase 1 분석 작업 (이미 완료)

- [x] 각 프로바이더별 입력/출력 변환 메서드 라인 매핑
- [x] SSE 스트리밍 처리 일관성 점검 — **AH-16 가짜 SSE 발견** (C9)
- [x] Stream 메서드의 ApiKeyPool/Cooldown 우회 위험 (H5)
- [x] AH-12 (Gen4) 운영 환경에서 503 가능성

---

## 3. docutil — 단일 진입점 + 위반 잔존

> DocUtil은 `integrations/llm/factory.py:32`를 통해 6개 Provider(openai/azure_openai/gemini/anthropic/vllm/sglang)를 단일 진입점으로 정리해 두었다.
> 단, **5건의 직접 호출 잔존**이 있고 본 인벤토리 작업으로 2건이 추가 발견되었다.

### 3.1 단일 진입점 (정상 경로)

| ID | 위치 | 호출 방식 | Provider | Model | 우선순위 | 민감도 | 목표 Agent |
|---|---|---|---|---|:---:|:---:|---|
| DU-1 | `backend/app/integrations/llm/factory.py:32` `create_llm_client(provider)` | factory | openai/azure/gemini/anthropic/vllm/sglang | `core/config.py`의 task별 (chat/report/template) | P0 | internal | (게이트웨이 함수 자체 — Phase 7에서 `AgentHubProxyClient`로 대체) |

### 3.2 LLM 클라이언트 구현체 (factory가 호출)

| ID | 위치 | 비고 |
|---|---|---|
| DU-2 | `backend/app/integrations/llm/client.py:54,510` `OpenAIClient` (Structured Outputs strict) | `gpt-4o` 기본 (`config.py:131`) |
| DU-3 | `backend/app/integrations/llm/azure_client.py:23-31` `AzureOpenAIClient` | OpenAI 호환 |
| DU-4 | `backend/app/integrations/llm/gemini_client.py:124-143` `GeminiClient` | `gemini-2.0-flash`, Discriminated Union 평탄화 |
| DU-5 | `backend/app/integrations/llm/claude_client.py:37,247` `ClaudeClient` | `from anthropic import Anthropic, AsyncAnthropic` (정상 — 클라이언트 구현 위치) |
| DU-6 | `backend/app/integrations/llm/client.py` `VLLMClient`/`SGLangClient` | OpenAI 호환 자체 호스팅 |

### 3.3 LLM 사용처 (factory 경유)

| ID | 위치 | 기능 | 우선순위 | 민감도 | 목표 Agent |
|---|---|---|:---:|:---:|---|
| DU-7 | `backend/app/modules/chat/service.py` (호출 체인) | RAG 챗봇 응답 (task=`chatbot`) | P0 | internal | `agent-docutil-rag-chat` |
| DU-8 | `backend/app/modules/search/service.py` `chatbot/qa` | 검색-증강 답변 (task=`chat`) | P0 | internal | `agent-docutil-rag-chat` (DU-7과 통합) |
| DU-9 | `backend/app/modules/documents_v2/service.py:307,319` | Mode A 문서 생성 (task=`report`) | P1 | internal | `agent-docutil-report-generator` |
| DU-10 | `backend/app/modules/templates/service.py:423` | 템플릿(Jinja) `model="gpt-4o"` 하드코딩 (S7에 폐기) | P3 | internal | (제거 예정) |
| DU-11 | `backend/app/workers/report_generator.py:906,932-945` | 구 Jinja2 보고서 (`/reports` 410 Gone) | P3 | internal | (제거 예정 — S7) |
| DU-12 | `backend/app/workers/jinja2_engine.py:835` `model="gpt-4o"` 기본 | 변수 치환 → LLM | P3 | internal | (제거 예정 — S7) |
| DU-13 | `backend/app/workers/evaluation_runner.py:55-58` | RAGAS 평가 (LLM-as-judge, daily-evaluation Celery beat) | P2 | internal | `agent-docutil-evaluator` |

### 3.4 단일 진입점 위반 (P1 위반 — Phase 7 우선순위)

| ID | 위치 | 위반 종류 | 우선순위 | 비고 |
|---|---|---|:---:|---|
| DU-14 | `backend/app/integrations/image_generation/service.py:188-192` | `from openai import AsyncOpenAI` 외부 SDK 직접 import + `AsyncOpenAI(api_key=settings.openai_api_key)` | P1 | DALL-E 3 이미지 생성. Phase 7에서 AgentHub 이미지 API(AH-9) 위임 |
| DU-15 | `backend/app/integrations/rag/graph_rag.py:105` | `self._llm = OpenAIClient()` factory 우회 | P3 | `graph_rag_enabled=False` 기본 (비활성) |
| DU-16 | `backend/app/modules/search/agentic_search.py:215,237` | `llm = OpenAIClient()` factory 우회 (2곳) | P1 | **본 인벤토리 작업으로 신규 발견** — Agentic Search 모듈 |
| DU-17 | `backend/app/workers/training/data_generator.py:68-69` | `self._source_llm = OpenAIClient()`, `self._judge_llm = OpenAIClient()` | P3 | **본 인벤토리 작업으로 신규 발견** — 학습 데이터 생성/판정용 |

### 3.5 임베딩 / 이미지 / 검색 (factory 외)

| ID | 위치 | 호출 방식 | Provider | Model | 우선순위 | 비고 |
|---|---|---|---|---|:---:|---|
| DU-18 | `backend/app/workers/embedding_generator.py:148-186` | 자체 워커 | openai 또는 vLLM | `text-embedding-3-small` (1536D) 또는 vLLM Qwen3 (2048D) | P2 | **차원 분기**: `embedding_provider=local` 시 2048D. 통합 정책상 1536D로 단일화 권장 (W1) |
| DU-19 | `backend/app/integrations/image_generation/service.py:189` | DU-14와 동일 | dalle | `dall-e-3` 하드코딩 | P1 | base64 응답(`b64_json`) |
| DU-20 | `backend/app/integrations/image_generation/service.py:238+` | httpx 직접 | unsplash | (스톡 검색) | P1 | DALL-E 우선 + Unsplash fallback (`auto_select.py`) |

---

## 4. career — 직접 호출 11곳 + 위임 5곳

> career는 18 MS 중 **3 MS(ai-service / simulation-service / coaching-service)** 가 LLM 라이브러리 의존을 갖지만, coaching은 위임만 한다.
> 실제 LLM SDK를 직접 호출하는 위치는 **`ai-service` 9곳 + `simulation-service` 2곳 = 11곳** + 임베딩 2곳.

### 4.1 ai-service 직접 호출 (`services/ai-service/`)

| ID | 위치 | 함수 | 호출 방식 | Model | 우선순위 | 민감도 | 목표 Agent |
|---|---|---|---|---|:---:|:---:|---|
| CA-1 | `app/services/llm_service.py:21` | `LLMService.__init__` | LangChain `ChatOpenAI(temperature=0.7, max_tokens=2000)` | gpt-4o-mini | — | — | (인스턴스화) |
| CA-2 | `app/services/llm_service.py:28` | `LLMService.__init__` | OpenAI SDK `AsyncOpenAI(api_key=…)` | gpt-4o-mini | — | — | (인스턴스화) |
| CA-3 | `app/services/llm_service.py:90` | `generate_action_recommendations()` | LangChain `ainvoke` | gpt-4o-mini | P0 | confidential | `agent-career-action-recommender` |
| CA-4 | `app/services/llm_service.py:146` | `analyze_competencies()` | LangChain `ainvoke` | gpt-4o-mini | P0 | confidential | `agent-career-competency-analyzer` |
| CA-5 | `app/services/llm_service.py:203` | `chat()` | LangChain `ainvoke` | gpt-4o-mini | P0 | pii | `agent-career-chatbot` |
| CA-6 | `app/services/llm_service.py:260` | `generate_semester_goals()` | LangChain `ainvoke` | gpt-4o-mini | P1 | confidential | `agent-career-semester-planner` |
| CA-7 | `app/services/llm_service.py:317` | `generate_with_tools()` 1차 | OpenAI SDK `chat.completions.create(tools=TOOLS, tool_choice="auto")` | gpt-4o-mini | P0 | confidential | `agent-career-actionboard-orchestrator` |
| CA-8 | `app/services/llm_service.py:334` | `generate_with_tools()` 최종 | OpenAI SDK `response_format=json_schema` (Structured Outputs strict) | gpt-4o-mini | P0 | confidential | (CA-7 fan-out) |
| CA-9 | `app/services/llm_service.py:507` | `generate_with_tools_and_rag()` 1차 | OpenAI SDK + RAG context prepend | gpt-4o-mini | P0 | confidential | `agent-career-rag-actionboard` |
| CA-10 | `app/services/llm_service.py:524` | `generate_with_tools_and_rag()` 최종 | OpenAI SDK `response_format=json_schema` | gpt-4o-mini | P0 | confidential | (CA-9 fan-out) |

### 4.2 simulation-service 직접 호출

| ID | 위치 | 함수 | 호출 방식 | Model | 우선순위 | 민감도 | 목표 Agent |
|---|---|---|---|---|:---:|:---:|---|
| CA-11 | `services/simulation-service/app/services/simulation_service.py:51` | `SimulationService.__init__` | OpenAI SDK `AsyncOpenAI(...)` | gpt-4o-mini | — | — | (인스턴스화) |
| CA-12 | `services/simulation-service/app/services/simulation_service.py:973` | `_generate_ai_suggestions()` | OpenAI SDK `chat.completions.create` (max=2000) | gpt-4o-mini | P1 | confidential | `agent-career-simulation-suggester` |
| CA-13 | `services/simulation-service/app/services/simulation_service.py:1764` | `_generate_ai_analysis()` | OpenAI SDK `chat.completions.create` (temp=0.7, max=1500) | gpt-4o-mini | P1 | confidential | `agent-career-simulation-analyzer` |

### 4.3 임베딩 (직접 호출)

| ID | 위치 | 호출 방식 | Provider | Model | 우선순위 | 비고 |
|---|---|---|---|---|:---:|---|
| CA-14 | `services/ai-service/app/services/embedding_service.py:30` | `AsyncOpenAI(...)` 인스턴스화 | openai | text-embedding-3-small (1536D) | — | — |
| CA-15 | `services/ai-service/app/services/embedding_service.py:49` | `client.embeddings.create(...)` 단일 텍스트 | openai | text-embedding-3-small | P2 | RAG 인덱싱 |
| CA-16 | `services/ai-service/app/services/embedding_service.py:91` | `client.embeddings.create(...)` 배치 | openai | text-embedding-3-small | P2 | 대량 인덱싱 |

### 4.4 위임 호출 (이미 ai-service 위임 형태 — Phase 7 시 AgentHub로 직접 전환)

| ID | 위치 | 대상 | 페이로드 | 우선순위 | 목표 Agent |
|---|---|---|---|:---:|---|
| CA-17 | `services/coaching-service/app/services/coaching_service.py:560-562` | `POST {AI_SERVICE_URL}/ai/chat` | `{message, history, context}` | P0 | `agent-career-chatbot` |
| CA-18 | `services/competency-service/app/services/competency_service.py:209-211` | `POST {AI_SERVICE_URL}/ai/analyze` | `{student, competencies, target_role}` | P1 | `agent-career-competency-analyzer` |
| CA-19 | `services/roadmap-service/app/services/roadmap_service.py:578-580` | `POST {AI_SERVICE_URL}/ai/recommendations/tools` | `{student, sprint, …}` | P0 | `agent-career-actionboard-orchestrator` |
| CA-20 | `services/opportunity-service/app/config.py:25` `AI_SERVICE_URL` | (config만 정의, 호출 미발견) | — | — | (호출 추가 시 매핑) |
| CA-21 | `services/skill-service/app/config.py:25` `AI_SERVICE_URL` | (config만 정의, 호출 미발견) | — | — | (호출 추가 시 매핑) |

### 4.5 Tool Calling (4개 도구 — AgentHub `Tool` 도메인으로 이전 후보)

> ai-service의 LLM이 Tool Calling으로 호출하는 4개 내부 API. AgentHub `ApiToolExecutor`가 실행하면 ai-service 자체를 제거할 수 있음.

| ID | 위치 | 도구명 | 대상 MS | 비고 |
|---|---|---|---|---|
| CA-T1 | `app/tools/tool_definitions.py:72+` + `tool_executor.py:30` | `get_student_profile` | student-service (8002) | |
| CA-T2 | 동일 | `get_competency_scores` | competency-service (8003) | |
| CA-T3 | 동일 | `search_alumni_patterns` | alumni-service (8005) | 익명화 통계 |
| CA-T4 | 동일 | `check_constraints` | student-service (8002) | 학사 위험 확인 |

### 4.6 환경변수 / 설정 (career)

| 위치 | 키 | 값 |
|---|---|---|
| `services/ai-service/app/config.py:13` | `OPENAI_MODEL` | `gpt-4o-mini` |
| `services/simulation-service/app/config.py:22` | `OPENAI_MODEL` | `gpt-4o-mini` |
| `services/coaching-service/app/config.py:25` | `AI_SERVICE_URL` | `http://localhost:8006` |
| `services/competency-service/app/config.py:32` | `AI_SERVICE_URL` | `http://localhost:8006` |
| `services/skill-service/app/config.py:25` | `AI_SERVICE_URL` | `http://localhost:8000` ← 포트 불일치 |
| `services/opportunity-service/app/config.py:25` | `AI_SERVICE_URL` | `http://localhost:8006` |
| `services/roadmap-service/app/config.py:23` | `AI_SERVICE_URL` | env `AI_SERVICE_URL` |
| `infrastructure/docker/docker-compose.yml:194,329,404,429,454` | `AI_SERVICE_URL` | `http://ai-service:8006` |
| `frontend/lib/api/ai.ts:5` | `NEXT_PUBLIC_AI_API_URL` | `http://localhost:8006` |

---

## 5. nexus — 외부 LLM 호출 없음

> Nexus는 **LAN-only 자체 LLM 서버** (vLLM + Qwen 3.5 27B). 외부 OpenAI/Anthropic/Google API를 호출하지 않는다.
> grep 검증: `api.openai.com`/`api.anthropic.com`/`generativelanguage.googleapis` 패턴은 anti-patterns 문서와 단위 테스트의 음성 케이스(`gpu_server_url="https://api.openai.com"` 검증용)에서만 발견.

| ID | 비고 |
|---|---|
| NX-1 | **외부 LLM 호출 없음** |
| NX-2 | 자체 vLLM 호출(`core/model/inference.py:201` `LocalModelProvider`) — `192.168.22.28:8001` LAN GPU |
| NX-3 | 자체 임베딩(`multilingual-e5-large`, 1024D) — 별도 vLLM 인스턴스 `:8002` |
| NX-4 | Web 도구(`WebFetch`/`WebSearch`)는 `permission_rules.yaml:12`에 의해 **차단** |

> Nexus는 인벤토리 대상이 아님. Phase 5에서 AgentHub의 `CallNexusAsync` 클라이언트가 호출하는 **목적지**가 된다.

---

## 6. 목표 Agent 카탈로그 (Phase 5+)

> Phase 5에서 AgentHub `Agents` 테이블에 신규 등록할 Agent들. `AgentCode`(UNIQUE) + `LlmRouting` + `KnowledgeBaseRef` + `ConsumerSystems` 필드 활용.

### 6.1 docutil 영역 (4 Agent)

| AgentCode | 호출자 | DefaultModel | LlmRouting | EnableRag | KB Ref | 매핑 ID |
|---|---|---|---|:---:|---|---|
| `docutil-rag-chat` | docutil chat / search | gpt-4o (configurable) | Hybrid | ✅ | `docutil:default` | DU-7, DU-8 |
| `docutil-report-generator` | docutil documents_v2 (Mode A) | gpt-4o | Hybrid | ✅ | `docutil:report-context` | DU-9 |
| `docutil-evaluator` | RAGAS 평가 worker | gpt-4o (LLM-as-judge) | External (정확도 우선) | ❌ | — | DU-13 |
| `docutil-image-generator` | 이미지 자동 채움 | dall-e-3 + unsplash fallback | External | ❌ | — | DU-14, DU-19, DU-20 |

### 6.2 career 영역 (8 Agent)

| AgentCode | 호출자 | DefaultModel | LlmRouting | ResponseFormat | 매핑 ID |
|---|---|---|---|---|---|
| `career-actionboard-orchestrator` | ai-service `/ai/recommendations/tools`, roadmap-service | gpt-4o-mini | Hybrid | `JSON_SCHEMA_ACTIONBOARD` (strict) | CA-7, CA-8, CA-19 |
| `career-rag-actionboard` | ai-service `/ai/recommendations/rag` | gpt-4o-mini | Hybrid | `JSON_SCHEMA_ACTIONBOARD` (strict) | CA-9, CA-10 |
| `career-competency-analyzer` | competency-service, ai-service | gpt-4o-mini | Hybrid | (구조화 응답) | CA-4, CA-18 |
| `career-action-recommender` | ai-service `/ai/actions/{id}` | gpt-4o-mini | Hybrid | (구조화 응답) | CA-3 |
| `career-chatbot` | coaching-service, frontend | gpt-4o-mini | **Internal** (PII 가능성) | (자유 응답) | CA-5, CA-17 |
| `career-semester-planner` | ai-service `/ai/sprint/{id}` | gpt-4o-mini | Hybrid | (구조화 응답) | CA-6 |
| `career-simulation-suggester` | simulation-service | gpt-4o-mini | Hybrid | (4개 시나리오 추천 JSON) | CA-12 |
| `career-simulation-analyzer` | simulation-service | gpt-4o-mini | Hybrid | (분석 JSON) | CA-13 |

### 6.3 공통 영역 (3 Agent)

| AgentCode | 용도 | DefaultModel | LlmRouting | 비고 |
|---|---|---|---|---|
| `embedding-default` | 모든 시스템의 임베딩 위임 | text-embedding-3-small (1536D) | External 우선 / Internal fallback (multilingual-e5-large 1024D는 차원 변환 필요) | DU-18, CA-14~16 통합. **차원 정책**: 1536D 표준, 2048D는 별도 collection |
| `web-search-default` | Tavily 검색 위임 | (검색 도구) | External | AH-14 |
| `agentic-search` | DocUtil agentic_search 모듈 | gpt-4o-mini | Hybrid | DU-16 (P1 위반 신규 발견) |

> **합계 신규 Agent**: 15개 (docutil 4 + career 8 + 공통 3).

---

## 7. Phase 7 마이그레이션 패턴

### 7.1 Before / After (Python)

```python
# BEFORE — career의 ai-service llm_service.py:317
response = await self.openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": user_prompt}],
    tools=TOOLS,
    tool_choice="auto",
)
```

```python
# AFTER — AgentHub Agent 위임
import httpx
AGENTHUB_URL = os.getenv("AGENTHUB_URL")
AGENTHUB_API_KEY = os.getenv("AGENTHUB_API_KEY")

async with httpx.AsyncClient(base_url=AGENTHUB_URL, timeout=60.0) as client:
    response = await client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": AGENTHUB_API_KEY},
        json={
            "model": "career-actionboard-orchestrator",  # AgentCode
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": True,
            # tools / tool_choice / response_format은 Agent에 사전 등록되어 자동 적용
        },
    )
```

### 7.2 Before / After (Frontend, Next.js)

```ts
// BEFORE — career frontend/lib/api/ai.ts
const AI_SERVICE_URL = process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8006';
const aiApi = axios.create({ baseURL: AI_SERVICE_URL });

// AFTER — AgentHub로 직접 (또는 BFF 경유)
const AGENTHUB_URL = process.env.NEXT_PUBLIC_AGENTHUB_URL;
const aiApi = axios.create({
  baseURL: AGENTHUB_URL,
  headers: { 'X-API-Key': process.env.NEXT_PUBLIC_AGENTHUB_KEY },
});
```

### 7.3 환경변수 전환표

| Before (각 시스템) | After (단일) | 비고 |
|---|---|---|
| `OPENAI_API_KEY` | `AGENTHUB_API_KEY` (시스템별 발급) | 키별 ConsumerSystem 라벨 부여 |
| `OPENAI_MODEL=gpt-4o-mini` | (불필요) | Agent에 매핑 |
| `ANTHROPIC_API_KEY` | (제거) | AgentHub 통합 |
| `GEMINI_API_KEY` | (제거) | AgentHub 통합 |
| `AZURE_OPENAI_KEY/ENDPOINT/DEPLOYMENT` | (제거) | AgentHub 통합 |
| `AI_SERVICE_URL` (career) | `AGENTHUB_URL` | `https://agenthub.idino.co.kr` 또는 환경별 |
| (신규) | `AGENTHUB_URL` | 모든 호출 진입점 |

---

## 8. PII / 민감도 분석

### 8.1 PII 가능 입력 위치

| ID | 시스템 | 위치 | PII 종류 |
|---|---|---|---|
| CA-5, CA-17 | career | 코칭 챗봇 | 학생 이름, 성적, 진로 고민 (감정/심리 발화) |
| CA-3, CA-7, CA-9 | career | ActionBoard 추천 입력 | 학번, 학생 프로필, 성적 |
| DU-7 | docutil | RAG 챗봇 | 사용자가 업로드한 문서 내용에 따라 모든 종류 가능 |
| CA-15, CA-16 | career | 임베딩 입력 (학생 데이터) | 학번, 성적 |

### 8.2 라우팅 정책 권장 (Phase 5 LlmRouting)

| 시나리오 | 라우팅 | 근거 |
|---|---|---|
| career 코칭 챗봇 (`career-chatbot`) | **Internal (Nexus)** | 학생 PII 노출 위험 |
| career ActionBoard | Hybrid (PII 감지 시 Internal) | Tool Calling은 OpenAI Structured Outputs strict 의존 (R3 — Claude/Gemini fallback 미지원) |
| docutil RAG 챗봇 | Hybrid (조직 정책 따라) | 문서 visibility 6단계 + tenant 정책 |
| docutil 평가 (RAGAS) | External | 정확도 우선, 평가 데이터에 PII 없도록 사전 마스킹 |
| 임베딩 | Hybrid | confidential은 Internal, 단 차원 정책에 묶임 |

---

## 9. 위험 / 미해결 이슈

| ID | 위험 | 영향 | 완화 |
|---|---|---|---|
| W1 | **임베딩 차원 분기** (1536D vs 2048D vs 1024D) | Qdrant collection 단일성 깨짐 | Phase 7 전 1536D 표준화 (TECHSPEC ADR-10) |
| W2 | **OpenAI Structured Outputs strict 의존** (CA-7~10) | Claude/Gemini fallback 시 schema 호환 안 됨 | Agent에 `ServiceType="openai"` 강제 또는 후처리 분기 (TECHSPEC R3) |
| W3 | **AgentHub 가짜 SSE** (AH-16) | OpenAI 호환 SDK·Cursor·LangChain 외부 호환성 깨짐 | Phase 5 진짜 SSE로 교체 (C9) |
| W4 | **DocUtil 단일 진입점 위반 5건** (DU-14~17) | factory 우회 시 multi-provider 라우팅 정책 무력화 | Phase 7 우선 처리 (P1 위반은 P1으로 분류) |
| W5 | **Skill-service 포트 불일치** (`AI_SERVICE_URL=:8000` vs 실제 ai-service `:8006`) | 위임 호출이 실패하거나 Nexus(:8001)로 잘못 가는 위험 | Phase 7 통합 시 환경변수 일괄 교체로 자연 해결 |
| W6 | **DocUtil training/data_generator** (DU-17) | 학습 데이터 생성 비용이 AgentHub 사용량에 잡히지 않음 | Phase 7 시 AgentHub `ApiKey.ConsumerSystem=docutil-training` 별도 발급 |
| W7 | **career Tool Calling 4 도구 (CA-T1~T4)** | AgentHub `ApiToolExecutor`로 이전 시 student/competency/alumni-service 인증 합의 필요 | 내부 mTLS 또는 공유 시크릿 |
| W8 | **AgentHub Vertex AI 운영 미설정** (AH-12 Gen4) | 운영 환경에서 503 반환 | 운영자가 `AiApiSettings:VertexAI:*` 설정 후 활성화 또는 비활성 시 UI에서 숨김 |

---

## 10. Phase 7 견적

### 10.1 호출 지점 변경 단가

| 분류 | 평균 변경 시간 | 검증 시간 | 합계 (지점당) |
|---|---:|---:|---:|
| 단순 위임 교체 (CA-3~6, CA-12~13, DU-9) | 30분 | 30분 | 1시간 |
| Structured Outputs 동반 (CA-7~10) | 1시간 | 1시간 | 2시간 |
| 임베딩 위임 (DU-18, CA-14~16) | 1시간 | 1시간 | 2시간 |
| 이미지 위임 (DU-14, DU-19, DU-20) | 1.5시간 | 1시간 | 2.5시간 |
| 위임 호출 환경변수 교체 (CA-17~19, frontend) | 30분 | 30분 | 1시간 |
| 단일 진입점 위반 정리 (DU-15, DU-16) | 1시간 | 30분 | 1.5시간 |

### 10.2 합계 (영업일 환산)

| 항목 | 지점 수 | 시간 |
|---|---:|---:|
| 단순 위임 교체 | 7 | 7h |
| Structured Outputs 동반 | 4 | 8h |
| 임베딩 위임 | 4 | 8h |
| 이미지 위임 | 3 | 7.5h |
| 환경변수 교체 (위임 호출) | 5 | 5h |
| 단일 진입점 위반 정리 | 3 | 4.5h |
| Tool Calling 4 도구 이전 | 4 | 16h (인증 합의 + 마이그레이션) |
| 통합 테스트 (E2E) | — | 16h |
| **합계** | **30** | **72h ≈ 9 영업일** |

> TECHSPEC §12의 Phase 7 "10 영업일" 견적과 일치 — 본 인벤토리 기반으로 1일 여유.

---

## 11. 진행 추적

| 서브프로젝트 | 분석 시작 | 분석 완료 | 작성자 | 비고 |
|---|---|---|---|---|
| agenthub | 2026-05-04 (source 보고서) | 2026-05-05 (라인 검증) | Claude (`source_AGENTHUB.md` + 본 작업) | 7 chat + 5 image 분기 정확화 |
| docutil | 2026-05-04 (source 보고서) | 2026-05-05 (잔존 검증) | Claude (`source_DOCUTIL.md` + 본 작업) | DU-16/DU-17 신규 발견 |
| career | 2026-05-04 (source 보고서) | 2026-05-05 (라인 검증) | Claude (`source_CAREER.md` + 본 작업) | 11곳 직접 + 5 위임 확정 |
| nexus | 2026-05-04 (source 보고서) | 2026-05-05 (검증) | Claude (`source_NEXUS.md` + 본 작업) | 외부 LLM 호출 없음 확정 |

---

## 12. Phase 1 산출물 체크리스트

- [x] 각 서브프로젝트별 호출 지점 전수 조사 (35건 + 위임 5건)
- [x] 우선순위(P0~P3) 부여
- [x] Provider/Model 통계 (§1.3)
- [x] 민감도(PII) 분류 (§8)
- [x] 목표 Agent 매핑 초안 (§6, 15개 신규 Agent)
- [x] Phase 7 작업 견적 (§10, 약 9 영업일)
- [x] 단일 진입점 위반 (P1) 잔존 식별 (DU-14~17)
- [x] OpenAI Structured Outputs 다중 프로바이더 fallback 위험 식별 (W2)
- [x] 임베딩 차원 정책 결정 (W1, ADR-10)

---

## 부록 A — 본 인벤토리 작업 결과 (TECHSPEC 갱신 권고)

본 작업으로 **TECHSPEC.md / source_DOCUTIL.md에 누락된 호출 지점 2건 발견**:

1. `docutil/backend/app/modules/search/agentic_search.py:215, 237` — `OpenAIClient()` factory 우회 2곳
2. `docutil/backend/app/workers/training/data_generator.py:68-69` — `OpenAIClient()` factory 우회 2곳 (학습 데이터 생성/판정)

**조치**:
- TECHSPEC §16에 R31 (DocUtil 단일 진입점 위반 신규 2건) 추가 권고
- DocUtil 측에 P1 anti-pattern 위반 보고서 회신 (Phase 4 S6/S7와 함께 정리하면 효율적)

## 부록 B — 본 인벤토리 작업으로 확정된 사실 (TECHSPEC 보강)

| 항목 | TECHSPEC 표기 | 실측 (본 작업) |
|---|---|---|
| agenthub Chat provider 분기 수 | 8 | **7** (Vertex는 Image-only Gen4Image 내부 호출, Tavily는 검색 도구) |
| AgentHub 가짜 SSE 위치 | `OpenAICompatController.cs:138` | **`:343` `Content.Split(' ')` + `:357` `Task.Delay(15)`** (138은 함수 시작점) |
| career LLM 직접 호출 위치 | 11곳 | 11곳 (검증 완료) |
| career 위임 호출 | 4 (coaching/competency/roadmap + opportunity 추정) | **3 명시 + 2 config-only** (skill, opportunity는 호출 미발견) |
| DocUtil 단일 진입점 위반 | 3건 (image_generation, graph_rag, embedding_generator) | **5건** — 위 부록 A의 2건 추가 |
