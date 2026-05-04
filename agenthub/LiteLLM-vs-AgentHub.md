# LiteLLM vs Agent Hub — 비교 분석

> 작성일: 2026-03-13
> 대상: 기술 의사결정자, 개발팀

---

## 한 줄 요약

| | LiteLLM | Agent Hub (현 프로젝트) |
|--|---------|----------------------|
| **정체성** | LLM API 통합 **게이트웨이 / 프록시** | AI 에이전트 **생성·관리·공유 플랫폼** |
| **핵심 사용자** | 개발자, DevOps, MLOps | 비기술 업무 담당자 + 개발자 |
| **비유** | 고속도로 톨게이트 (모든 차량을 통일된 방식으로 통과) | 자동차 공장 + 전시장 (차량을 만들고 운전하고 공유) |

---

## 1. 개요

### LiteLLM
- **개발사**: BerriAI (오픈소스, MIT 라이선스)
- **방식**: Python SDK + Proxy Server
- **역할**: 100개 이상의 LLM 제공사(OpenAI, Claude, Mistral, Gemini 등) API를 **단일 OpenAI 호환 인터페이스**로 통합
- **주요 고객**: Stripe, Netflix, OpenAI Agents SDK, Google ADK 등
- **GitHub**: ⭐ 18,000+

### Agent Hub (현 프로젝트)
- **개발사**: 자체 개발 (ASP.NET Core 8 + Vue 3)
- **방식**: 풀스택 웹 플랫폼
- **역할**: AI 에이전트를 **코딩 없이 만들고**, 채팅·공유·임베드·RAG 연동까지 제공하는 엔드-투-엔드 플랫폼
- **주요 사용자**: 사내 팀, 업무 자동화 담당자, 챗봇 운영자

---

## 2. 기능 비교 매트릭스

| 기능 영역 | LiteLLM | Agent Hub |
|-----------|---------|-----------|
| **LLM 제공사 지원** | 140개 이상, 2,600+ 모델 | OpenAI / Claude / Mistral (3개 서비스) |
| **API 통합 인터페이스** | ✅ OpenAI 호환 단일 API | ❌ 자체 API (외부 연동 제한) |
| **에이전트 빌더 UI** | ❌ 없음 | ✅ 5단계 위저드, No-code |
| **채팅 UI** | ❌ 없음 | ✅ 내장 채팅 인터페이스 |
| **공개 챗봇 URL 공유** | ❌ 없음 | ✅ `/chatbot/{code}` |
| **웹 임베드 (iframe)** | ❌ 없음 | ✅ `/embed/{code}` |
| **RAG (문서 연동)** | ❌ 없음 | ✅ Knowledge Base 연동 |
| **시스템 프롬프트 관리** | 기본 지원 | ✅ 에이전트별 완전 지원 |
| **멀티 에이전트 채팅** | ❌ | ✅ AgentMultiChat |
| **비용 추적** | ✅ 매우 정밀 (토큰/키/팀별) | ✅ 기본 수준 (ApiUsage 테이블) |
| **Rate Limiting** | ✅ RPM/TPM/사용자별 세밀 제어 | ❌ 미구현 (계획 중) |
| **Load Balancing** | ✅ 1.5k RPS 처리 | ❌ 없음 |
| **Fallback / 자동 재시도** | ✅ | ❌ |
| **캐싱** | ✅ Redis, 로컬, 프롬프트 캐싱 | ❌ |
| **가상 API 키 관리** | ✅ Virtual Keys | ✅ API Key 발급 |
| **팀 관리** | ✅ 팀별 예산/사용량 | ✅ Team 기능 |
| **Admin Dashboard** | ✅ React 기반 (http://host/ui) | ✅ Vue 기반 통합 관리 |
| **SSO (Okta, Google, Azure AD)** | ✅ 엔터프라이즈 | ❌ JWT 자체 인증 |
| **감사 로그 (Audit Log)** | ✅ | ✅ |
| **PII 보호** | ❌ (가드레일로 부분 지원) | ✅ PII 감지·마스킹 |
| **금칙어 필터** | ❌ | ✅ BannedWords |
| **워크플로우** | ❌ | ✅ Workflow Builder |
| **이미지/영상 생성** | ❌ | ✅ (DALL-E 연동) |
| **Observability (OTel)** | ✅ OpenTelemetry 완전 지원 | ❌ |
| **Langfuse/MLflow 연동** | ✅ | ❌ |
| **Docker 배포** | ✅ | ✅ |
| **오픈소스** | ✅ MIT | ❌ 자체 개발 |

---

## 3. 아키텍처 비교

### LiteLLM 아키텍처

```
클라이언트 앱 / LangChain / 기타
         │
         ▼
   LiteLLM Proxy Server (FastAPI, Port 4000)
         │
    ┌────┴────────────────────────────────┐
    │  인증(JWT/키) → Rate Limit → 라우팅 │
    │  캐싱 → 로깅 → 비용 추적           │
    └────┬────────────────────────────────┘
         │ (OpenAI 호환 형식으로 변환)
    ┌────┴──────────────────────────────┐
    │  OpenAI │ Claude │ Mistral │ 140+ │
    └───────────────────────────────────┘
         │
   [PostgreSQL] + [Redis]
```

**특징**: 순수 **API 게이트웨이**. UI 없이 API만 처리.

---

### Agent Hub 아키텍처

```
브라우저 (Vue 3 SPA)
    │  에이전트 빌더 / 채팅 / 공유 / 임베드
    ▼
ASP.NET Core 8 Web API
    │
    ├── AgentsController  ─── AgentService ─── MSSQL
    ├── ChatController    ─── AiProxyService
    ├── PublicController  ─── BannedWords, PII 검사
    └── WorkflowController ─ KnowledgeBase (RAG)
             │
        ┌────┴──────────────┐
        │  OpenAI API       │
        │  Anthropic API    │
        │  Mistral API      │
        └───────────────────┘
```

**특징**: **엔드-투-엔드 플랫폼**. 비기술 사용자가 바로 사용 가능.

---

## 4. 사용 시나리오별 적합성

### 시나리오 1: "여러 AI API를 하나의 엔드포인트로 통합하고 싶다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ✅✅✅ 이것이 LiteLLM의 존재 목적 |
| **Agent Hub** | ❌ 외부 클라이언트가 직접 API를 통합하기 어려움 |

### 시나리오 2: "팀원이 코딩 없이 AI 챗봇을 만들고 싶다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ❌ 개발자가 별도 UI를 만들어야 함 |
| **Agent Hub** | ✅✅✅ 에이전트 빌더가 바로 이 목적 |

### 시나리오 3: "외부 고객에게 AI 챗봇을 URL로 공유하고 싶다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ❌ 불가 |
| **Agent Hub** | ✅✅✅ `/chatbot/{code}` 공개 URL 제공 |

### 시나리오 4: "초당 1,000건 이상의 고트래픽 AI API 처리가 필요하다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ✅✅✅ 1.5k+ RPS, Load Balancing, Fallback 내장 |
| **Agent Hub** | ⚠️ 고트래픽 처리 기능 미구현 |

### 시나리오 5: "AI 비용을 팀/프로젝트별로 정밀하게 추적하고 싶다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ✅✅✅ 가상 키, 팀별 예산 제한, 실시간 비용 모니터링 |
| **Agent Hub** | ✅ 기본 ApiUsage 기록 (세밀한 제어는 부족) |

### 시나리오 6: "내부 문서를 기반으로 답변하는 사내 챗봇이 필요하다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ⚠️ RAG 직접 지원 없음 (다른 도구 필요) |
| **Agent Hub** | ✅✅ Knowledge Base + RAG 내장 |

### 시나리오 7: "웹사이트에 챗봇을 iframe으로 삽입하고 싶다"
| | 적합성 |
|--|--------|
| **LiteLLM** | ❌ 불가 |
| **Agent Hub** | ✅✅✅ `/embed/{code}` 즉시 사용 가능 |

---

## 5. 함께 사용하는 방법 (통합 아키텍처)

LiteLLM과 Agent Hub는 **경쟁이 아닌 상호 보완 관계**입니다.

```
┌─────────────────────────────────────────┐
│           Agent Hub 플랫폼              │
│  (에이전트 생성, 채팅 UI, 공유, RAG)    │
└────────────────────┬────────────────────┘
                     │ HTTP 요청
                     ▼
           ┌─────────────────┐
           │   LiteLLM       │  ← API 게이트웨이 추가 시
           │   Proxy Server  │    (Rate Limit, Fallback,
           │   :4000         │     Load Balancing, 비용추적)
           └────────┬────────┘
                    │
        ┌───────────┼──────────┐
        ▼           ▼          ▼
     OpenAI      Claude     Mistral
```

**통합 효과**: Agent Hub가 AiProxyService에서 직접 OpenAI API를 호출하는 대신, **LiteLLM Proxy**를 경유하면 다음을 얻음:
- 자동 Fallback (OpenAI 장애 시 Claude로 전환)
- Load Balancing (여러 API 키 병렬 운용)
- 정밀한 토큰 비용 추적
- Rate Limiting

---

## 6. 도입 방법 (Agent Hub에 LiteLLM 통합)

AiProxyService.cs의 API Base URL만 변경하면 됩니다.

```csharp
// 현재: OpenAI 직접 호출
var client = new OpenAIClient(new Uri("https://api.openai.com/v1"), ...);

// LiteLLM 경유로 변경
var client = new OpenAIClient(new Uri("http://litellm-proxy:4000"),
    new AzureKeyCredential("sk-master-key"));
```

LiteLLM이 OpenAI 호환 형식을 그대로 지원하므로 **코드 변경 최소화**로 통합 가능합니다.

---

## 7. 결론 요약

| 판단 기준 | LiteLLM 선택 | Agent Hub 선택 |
|-----------|-------------|----------------|
| 사용자 유형 | 개발자 중심 | 비기술 사용자 포함 |
| 목적 | API 인프라 통합 | 에이전트 운영 플랫폼 |
| UI 필요성 | 불필요 | 필수 |
| 지원 모델 수 | 최대한 많이 | 검증된 3개 서비스 |
| 트래픽 규모 | 대용량 (1k+ RPS) | 중소 규모 |
| 공유/임베드 | 불필요 | 핵심 기능 |
| RAG | 다른 도구 조합 | 내장 |
| 오픈소스 | MIT 오픈소스 | 자체 개발 |

---

## 8. Agent Hub 개선 제안 (LiteLLM 벤치마킹)

LiteLLM을 참고하여 Agent Hub에 추가하면 좋은 기능:

| 우선순위 | 기능 | LiteLLM 대응 기능 |
|----------|------|-------------------|
| 🔴 높음 | **Rate Limiting** (IP/사용자별) | MaxParallelRequestsHandler |
| 🔴 높음 | **API 키별 비용 상한 설정** | Virtual Key Budget |
| 🟡 중간 | **모델 Fallback** (장애 시 자동 전환) | Fallback Models |
| 🟡 중간 | **응답 캐싱** (동일 질문 재사용) | Redis/Local Cache |
| 🟢 낮음 | **OpenTelemetry 연동** | OTel 완전 지원 |
| 🟢 낮음 | **추가 LLM 제공사** (Gemini 등) | 140+ 제공사 |

---

*이 문서는 2026년 3월 기준으로 작성되었습니다. LiteLLM은 매우 빠르게 업데이트되므로 최신 정보는 [공식 문서](https://docs.litellm.ai/)를 참조하세요.*
