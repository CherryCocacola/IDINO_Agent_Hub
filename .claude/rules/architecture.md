# IDINO Agent Hub — 통합 아키텍처 원칙

> 4개 서브프로젝트(`agenthub`/`docutil`/`career`/`nexus`)를 federation 형태로 통합한 monorepo의 공통 아키텍처 규칙.

## P1. Control Plane / Data Plane 분리

```
[Control Plane]                              [Data Plane]
agenthub (운영자 콘솔)                        docutil-user (사용자 챗봇)
  ├─ Agent 정의                              career (학생 포털)
  ├─ LLM 라우팅 결정                          embed iframe / public chatbot
  ├─ 사용량/비용/PII/감사
  ├─ DocUtil KB 운영자 흡수                    ↓ AgentHub Agent API 호출
  └─ Nexus 모니터링                          /v1/chat/completions
                                             /api/agents/{id}/chat
```

- 운영자 작업은 항상 AgentHub UI에서
- End-User 앱은 자체 LLM 호출 금지, AgentHub Agent를 소비

## P2. AI 호출 단일 진입점

| 호출자 | 진입점 |
|---|---|
| docutil/career의 모든 AI 기능 | AgentHub `/v1/chat/completions` (OpenAI 호환) |
| 외부 시스템 (Postman, OpenAI SDK) | AgentHub `/v1/chat/completions` |
| AgentHub 자체 (Agent 빌더 미리보기 등) | AgentHub `IAiProxyService` |
| AgentHub → Nexus (옵션 B) | AgentHub `AiProxyService.CallNexusAsync` → Nexus `/v1/chat` |

- LLM SDK 직접 import 금지 (DocUtil/career)
- HttpClient 직접 외부 LLM API 호출 금지

## P3. LLM 라우팅 정책 (Agent 단위)

`Agent.LlmRouting` 값:

- `External` → `AiProxyService` → ApiKeyPool → OpenAI/Claude/Gemini/...
- `Internal` → `AiProxyService.CallNexusAsync` → Nexus (LAN)
- `Hybrid` → `HybridRouter`가 결정 규칙으로 분기
  - 결정 규칙 (`RoutingPolicyJson`):
    - PII 감지 → Internal 강제
    - 데이터 라벨 (confidential/internal/public) → 매핑
    - 모델 capability 요구 (vision, large context) → External
    - 비용 예산 초과 → Internal

## P4. 데이터베이스 — 단일 PG, 스키마 격리

```
PostgreSQL (192.168.10.39:5440) — AGENT_HUB DB
  ├─ AIAgentManagement   (agenthub)
  ├─ document_utilization (docutil)
  ├─ idino_career         (career)
  └─ hangfire             (작업 스케줄러)

Nexus는 자체 PG (에어갭 격리, 통합 대상 아님)
```

- 각 서브프로젝트는 자기 스키마만 read/write
- Cross-schema 조인 금지 → API 호출로 데이터 가져오기
- 운영자 콘솔(AgentHub)은 다른 스키마 read-only 가능 (사용량/감사 집계 목적)

## P5. 인증 — 다층 구조

| 호출 패턴 | 인증 |
|---|---|
| 운영자 ↔ AgentHub UI | JWT (AgentHub 자체 발급) |
| docutil/career → AgentHub | API Key (`X-API-Key: ak-...`) + 스코프 |
| AgentHub → Nexus | LAN-only + (선택) Tenant 헤더 |
| AgentHub → External LLM | ApiKeyPool에서 라운드로빈 발급된 키 |

- (장기) Keycloak 또는 IdentityServer로 SSO 통합 검토

## P6. 폴더/모듈 경계

각 서브프로젝트는 자체 구조 유지:

- `agenthub/` — `Controllers/Services/Models/DTOs/Data/Migrations/...` (.NET 표준)
- `docutil/backend/app/modules/{name}/` — `router.py/service.py/schemas.py/models.py/utils.py/constants.py/exceptions.py` 7개 파일만
- `career/` — 18개 FastAPI MS 각자의 구조
- `nexus/core/` — 4-Tier AsyncGenerator 체인

→ **서브프로젝트 간 직접 import 금지**, 통신은 HTTP/SignalR/Channel.

## P7. 비동기 처리 / 백그라운드 작업

| 시스템 | 백그라운드 |
|---|---|
| agenthub | Hangfire (할당량 리셋, 리포트, ActivityLog Worker) |
| docutil | Celery + RabbitMQ |
| career | (각 MS별 결정) |
| nexus | asyncio + Redis |

각자 도구 유지, 상호 호환성은 HTTP/SSE 인터페이스로 확보.

## P8. RAG — DocUtil 단일 권한

- AgentHub의 자체 KnowledgeBase는 deprecate (작업 후 제거)
- 모든 RAG는 DocUtil의 `/api/v1/search`, `/api/v1/documents`에 위임
- AgentHub의 `Agent.KnowledgeBaseRef`는 DocUtil의 collection ID

## P9. 환경 분기 — 외부망 / 내부망 / 하이브리드

| 환경 | 활성 | 비활성 |
|---|---|---|
| 외부망 | External LLM, AgentHub, DocUtil, career | Nexus (미배포) |
| 내부망 | Nexus, AgentHub, DocUtil, career | External LLM (방화벽 차단) |
| 하이브리드 | 모두 | — |

- AgentHub `Agent.LlmRouting` 정책으로 환경별 동작
- 같은 코드베이스, 다른 배포 패키지 + 다른 ApiServices 시드

## P10. 시크릿 / 설정

- 시크릿은 환경변수 + 외부 vault (절대 git 커밋 금지)
- 4개 시스템 모두 `.env` / `appsettings.*.json`을 `.gitignore`로 제외
- 공통 시크릿은 단일 소스(예: AGENT_HUB DB 비밀번호)에서 가져와 각 시스템 환경변수로 주입
