# AI 호출 인벤토리 (Phase 1 작업 대상)

> 각 서브프로젝트에서 발생하는 모든 LLM/AI 호출 지점을 카탈로그화한 문서.
> Phase 7에서 이 인벤토리를 기준으로 직접 호출 → AgentHub Agent 위임으로 일괄 교체.

---

## 0. 작성 가이드

### 항목별 기록 항목
| 필드 | 설명 |
|---|---|
| 위치 | `subproject/path/to/file.ext:line` |
| 호출 방식 | OpenAI SDK / Anthropic SDK / Google SDK / httpx 직접 / LangChain / 기타 |
| Provider | openai / claude / gemini / ... |
| Model | gpt-4o, claude-sonnet-4, ... |
| 트리거 | 사용자 액션 / 백그라운드 잡 / 스케줄러 |
| 입력 데이터 | 사용자 입력 / DB 데이터 / 파일 / 기타 |
| 민감도 | public / internal / confidential / pii |
| 현재 라우팅 | External / Internal / 혼재 |
| 목표 Agent (Phase 5+) | AgentHub의 어느 AgentCode로 매핑할지 |
| 비고 | 특이사항, 마이그레이션 시 주의점 |

### 우선순위 분류
- **P0**: 사용자 트래픽 직접 영향 (메인 챗봇, 핵심 기능)
- **P1**: 사용자 보조 기능 (요약, 추천, 분류)
- **P2**: 백그라운드/배치 (인덱싱, 일일 분석)
- **P3**: 개발자 디버깅용 / 사용 빈도 낮음

---

## 1. agenthub (이미 게이트웨이)

> AgentHub는 그 자체로 LLM 게이트웨이. 인벤토리 작성 시 "프로바이더별 호출 분기"를 정리.

| ID | 위치 | Provider | 비고 |
|---|---|---|---|
| AH-1 | `Services/AiProxyService.cs::CallOpenAIAsync` | openai | 기존 |
| AH-2 | `Services/AiProxyService.cs::CallClaudeAsync` | claude | 기존 |
| AH-3 | `Services/AiProxyService.cs::CallGeminiAsync` | gemini | 기존 |
| AH-4 | `Services/AiProxyService.cs::CallMistralAsync` | mistral | 기존 |
| AH-5 | `Services/AiProxyService.cs::CallPerplexityAsync` | perplexity | 기존 |
| AH-6 | `Services/AiProxyService.cs::CallAzureOpenAIAsync` | azureopenai | 기존 |
| AH-7 | `Services/AiProxyService.cs::CallCopilotAsync` | copilot | 기존 |
| AH-8 | **(신규 Phase 5)** `Services/AiProxyService.cs::CallNexusAsync` | nexus | **추가 예정** |
| AH-9 | `Services/AiProxyService.cs` 이미지/비디오 분기 | dalle, gemini-image, ... | 멀티미디어 |

**분석 작업 (Phase 1 시)**:
- [ ] 각 프로바이더별 입력/출력 변환 로직 매핑
- [ ] SSE 스트리밍 처리 일관성 점검 (현재 가짜 SSE → 진짜 SSE 전환 필요 항목)
- [ ] 에러 처리/재시도 로직 통일성

---

## 2. docutil

### 2.1 RAG 챗봇 메인 흐름
| ID | 위치 (예상) | Provider | Model | 우선순위 | 목표 Agent |
|---|---|---|---|---|---|
| DU-1 | `app/modules/llm/openai_client.py` (또는 `services/chat`) | openai | gpt-4o-mini? | P0 | `agent-docutil-rag-chat` |
| DU-2 | 임베딩 생성 (Qdrant 인덱싱) | openai | text-embedding-3-small | P2 | (임베딩은 AgentHub로 위임할지 별도 결정 필요) |
| DU-3 | 문서 요약 (업로드 후 자동 요약) | openai | gpt-4o-mini | P1 | `agent-docutil-summarize` |
| DU-4 | 질의 재작성 / HyDE | openai | gpt-4o-mini | P1 | (RAG agent 내부 단계) |

### 2.2 분석 작업 (Phase 1)
- [ ] `from openai import` / `from anthropic import` grep
- [ ] `httpx.post` + `api.openai.com` / `api.anthropic.com` grep
- [ ] LangChain `ChatOpenAI`, `OpenAIEmbeddings` 사용처
- [ ] 환경변수 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 참조 위치
- [ ] 모델 하드코딩 위치 (`"gpt-4o"`, `"claude-3-5-sonnet"` 등)

---

## 3. career

### 3.1 18개 MS 중 AI 사용처
> career는 18 MS이므로 MS 단위로 분류. (실제 MS명은 Phase 1에서 코드 확인 후 채움)

| ID | MS / 위치 (예상) | 기능 | Provider | 우선순위 | 목표 Agent |
|---|---|---|---|---|---|
| CA-1 | `coaching` | 학생 코칭 응답 생성 | openai | P0 | `agent-career-coaching` |
| CA-2 | `recommendation` | 진로 추천 | openai | P0 | `agent-career-recommend` |
| CA-3 | `learning_content` | 학습 콘텐츠 자동 생성 | openai | P1 | `agent-career-content-gen` |
| CA-4 | `assessment` | 학생 평가 분석 | openai | P1 | `agent-career-assess` |
| CA-5 | `chatbot` (있다면) | 일반 챗봇 | openai | P0 | `agent-career-chatbot` |

### 3.2 분석 작업 (Phase 1)
- [ ] 각 MS의 `requirements.txt`에서 LLM 라이브러리 식별
- [ ] `services/` 또는 `app/` 하위 OpenAI/Anthropic 호출 위치
- [ ] 임베딩 사용처 (pgvector → DocUtil 위임 대상)
- [ ] 프롬프트 템플릿 위치 (`prompts/`, `templates/`)

---

## 4. nexus

> Nexus는 LLM 서버 자체이므로 인벤토리 대상이 아님.
> 단, **Nexus가 외부 LLM을 호출하는 경우**는 기록 (Provider 어댑터, 외부 검색 등).

| ID | 위치 (예상) | 외부 호출 | 비고 |
|---|---|---|---|
| NX-1 | `core/providers/openai_provider.py` (있다면) | OpenAI API | 외부 LLM 폴백? |
| NX-2 | Tavily/검색 도구 | tavily | 도구 호출 |

### 분석 작업 (Phase 1)
- [ ] `core/providers/` 어떤 외부 LLM을 호출하는지 식별
- [ ] Nexus 자체가 호출하는 외부 의존성과 AgentHub의 차이 정리

---

## 5. 마이그레이션 매핑 (Phase 7)

각 호출 지점의 변경 패턴:

### Before
```python
# docutil 또는 career 내부
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resp = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": query}]
)
```

### After
```python
# AgentHub Agent 위임
import httpx
AGENTHUB_URL = os.getenv("AGENTHUB_URL")
AGENTHUB_API_KEY = os.getenv("AGENTHUB_API_KEY")

async with httpx.AsyncClient(base_url=AGENTHUB_URL) as client:
    resp = await client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": AGENTHUB_API_KEY},
        json={
            "model": "agent-docutil-rag-chat",  # AgentHub의 AgentCode
            "messages": [{"role": "user", "content": query}],
            "stream": True,
        },
        timeout=60.0,
    )
```

### 환경변수 전환표
| Before | After |
|---|---|
| `OPENAI_API_KEY` | `AGENTHUB_API_KEY` (각 서브프로젝트별 발급) |
| `ANTHROPIC_API_KEY` | (불필요 — AgentHub에 통합) |
| `GEMINI_API_KEY` | (불필요 — AgentHub에 통합) |
| `OPENAI_MODEL` | (불필요 — Agent에 매핑) |
| 신규: `AGENTHUB_URL` | `https://agenthub.internal` 또는 환경별 |

---

## 6. 인벤토리 작성 진행 추적

| 서브프로젝트 | 분석 시작 | 완료 | 작성자 | 비고 |
|---|---|---|---|---|
| agenthub | - | - | - | 분기 매핑 |
| docutil | - | - | - | RAG 흐름 위주 |
| career | - | - | - | 18 MS 전체 스캔 |
| nexus | - | - | - | 외부 호출만 |

---

## 7. Phase 1 산출물 체크리스트

- [ ] 각 서브프로젝트별 호출 지점 전수 조사
- [ ] 우선순위(P0~P3) 부여
- [ ] Provider/Model 통계
- [ ] 민감도(PII) 분류
- [ ] 목표 Agent 매핑 초안
- [ ] Phase 7 작업 견적 (호출 지점 수 × 평균 변경 시간)
