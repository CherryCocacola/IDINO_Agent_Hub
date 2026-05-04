# IDINO Agent Hub — 통합 도메인 모델 / 용어 정의

서브프로젝트 간 일관된 용어 사용을 위한 카탈로그. 각 서브프로젝트가 자체적으로 사용하던 용어 중 통합 차원에서 표준화한 것.

## 핵심 엔티티 (통합 차원)

### Agent (에이전트) — AgentHub의 중심 엔티티
- 사용자가 정의하는 AI 인격체
- `AgentCode` UNIQUE 식별자 (외부 노출용)
- `LlmRouting`: External / Internal / Hybrid
- `RoutingPolicyJson`: 하이브리드 모드의 결정 규칙 (JSON)
- `KnowledgeBaseSource`: AgentHub | DocUtil (Phase 6 이후 DocUtil로 통일)
- `KnowledgeBaseRef`: DocUtil collection ID
- `ConsumerSystems`: 어느 End-User 앱이 사용 가능한지 (예: `["docutil-user", "career-coaching"]`)
- 채팅(`ChatConversation`)의 호스트

### ApiService (LLM 프로바이더)
- AgentHub의 ApiServices 테이블에 등록된 LLM 카탈로그
- `ServiceCode`: `openai`, `claude`, `gemini`, `mistral`, `perplexity`, `azureopenai`, `copilot`, `nexus`(신규)
- `ServiceType`: Chat / ImageGeneration / VideoGeneration

### ApiKey (외부 노출 키)
- AgentHub가 발급하는 API Key (`ak-{base64}`)
- `Scopes`: `chat,stream,info,usage` 콤마 분리
- `AgentId int?` — 특정 Agent에만 묶이거나 사용자 전체 권한
- `ConsumerSystem`: docutil/career/외부 — 사용 주체 식별

### KnowledgeBase (지식베이스) — DocUtil 단일 권한
- DocUtil의 collection
- 문서 업로드 → 청크 분할 → 임베딩 → Qdrant 저장
- AgentHub가 BFF 패턴으로 운영자 UI 노출

### Conversation (대화)
- AgentHub의 `ChatConversation` ↔ Nexus의 `session_id` 1:1 매핑
- 각 End-User 앱에서 시작된 대화는 모두 AgentHub에 기록 (감사/사용량 집계)

## 시스템별 매핑

| 추상 개념 | agenthub | docutil | career | nexus |
|---|---|---|---|---|
| 사용자 | `User` | `app.modules.users.models.User` | `auth_users` | (테넌트로 추상화) |
| 대화 | `ChatConversation` | `Conversation` | (서비스별) | `session_id` (Redis) |
| 메시지 | `ChatMessage` | `Message` | (서비스별) | `core.message.Message` |
| 도구 | `Tool` | (없음) | (없음) | `BaseTool` |
| 문서 | `KnowledgeBaseDocument` (deprecate) | `Document` (RAG 마스터) | (서비스별) | `core.rag.*` |

## 라우팅 결정 데이터 모델

`Agent.RoutingPolicyJson` 스키마 (Hybrid 모드용):
```json
{
  "piiThreshold": "block",
  "piiAction": "internal",
  "dataLabels": {
    "confidential": "internal",
    "internal": "internal",
    "public": "external"
  },
  "modelCapability": {
    "vision": "external",
    "longContext": "external"
  },
  "costThreshold": {
    "perRequest": 0.10,
    "exceedAction": "internal"
  },
  "default": "external"
}
```

## End-User App 카탈로그

| App ID | 위치 | 설명 | 인증 |
|---|---|---|---|
| `docutil-user` | `docutil/frontend/` | DocUtil 사용자 챗봇 | DocUtil JWT |
| `career-student` | `career/frontend/` | idino_career 학생 포털 | career JWT |
| `embed-public` | iframe | AgentHub 공개 챗봇 임베드 | 게스트 (IP Rate Limit) |
| `external-sdk` | OpenAI SDK 호환 | 외부 시스템 통합 | API Key |

## ServiceCode 표준 값

문자열 비교 시 항상 소문자:
```
openai, claude, gemini, perplexity, mistral,
azureopenai, copilot, nexus, tavily,
dalle, gemini-image, imagen4, gen4-image, flux2,
gen4-video, veo, openai-video
```

## Role / 권한 모델

### AgentHub RBAC
- `SuperAdmin`: 시스템 전역 관리 (DB 백업, 시크릿)
- `Admin`: 운영자 콘솔 모든 기능
- `Developer`: Agent 빌더 + Tool 빌더
- `User`: 자신의 Agent + 채팅

### docutil/career
각 시스템이 자체 RBAC 유지. AgentHub와의 매핑은 SSO 도입 시 재정의.

## 용어 통일 (혼용 금지)

| 정확한 용어 | 금지 용어 (대안) |
|---|---|
| Agent (에이전트) | bot, assistant, character, persona |
| LLM Provider / ApiService | provider name, vendor, llm |
| Routing (라우팅) | dispatch, decision (의사결정 ≠ 라우팅) |
| Internal LLM = Nexus | local llm, on-prem llm, private llm |
| External LLM = OpenAI/Claude/... | cloud llm, public llm |
| Knowledge Base | document store, vector db (구현 디테일) |
| Conversation | session, thread, chat (단독 사용 시) |
| Agent Code (외부 식별자) | agent slug, agent name |
| ApiKey (외부) | secret, token (JWT와 혼동 방지) |
| JWT (운영자 토큰) | session token (UserSession이 별도 의미) |
| Tenant (멀티테넌시) | organization (사용자가 그룹화하는 단위와 별개) |

## ChatMessage Role

```
"user" | "assistant" | "system" | "tool"
```

프로바이더별 형식 차이는 `AiProxyService` 내부에서 변환:
- Anthropic: `system`은 별도 파라미터
- Google: `model` (assistant 대신)
- Nexus: 단일 `message` 문자열

## Source of Truth

| 정보 | 마스터 시스템 |
|---|---|
| Agent 정의 | AgentHub `Agents` 테이블 |
| ApiService/Model 카탈로그 | AgentHub `ApiServices`, `ApiServiceModels` |
| ApiKey 발급/검증 | AgentHub `ApiKeys` |
| 사용량/할당량 | AgentHub `ApiUsages`, `ApiQuotas` |
| 사용자 (장기) | (Phase 5+ 도입될) IdP, 현재는 각자 |
| 문서/RAG | DocUtil |
| 학생 데이터 | career 자체 스키마 |
| Nexus 모델 상태 | Nexus 자체 |
