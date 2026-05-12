# IDINO Agent Hub — 통합 아키텍처

> 4개 서브프로젝트(`agenthub`, `docutil`, `career`, `nexus`)를 하나의 monorepo로 묶고
> AgentHub를 단일 AI 게이트웨이로 삼는 Control Plane / Data Plane Federation 구조.

---

## 1. 시스템 구성도

```
┌───────────────────────────────────────────────────────────────────────┐
│                          End-User Apps (Data Plane)                     │
│                                                                         │
│   ┌───────────────────┐  ┌───────────────────┐  ┌──────────────────┐  │
│   │ docutil/frontend  │  │ career/frontend   │  │ embed-public     │  │
│   │  (Next.js 16)     │  │  (Next.js 14)     │  │  (iframe SDK)    │  │
│   └─────────┬─────────┘  └─────────┬─────────┘  └────────┬─────────┘  │
│             │                      │                      │            │
└─────────────┼──────────────────────┼──────────────────────┼────────────┘
              │                      │                      │
              │  HTTPS (X-API-Key)   │                      │
              ▼                      ▼                      ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        AgentHub (Control Plane)                         │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              ASP.NET Core 8 + EF Core + Vue 3                     │  │
│  │                                                                   │  │
│  │   /v1/chat/completions  ─ OpenAI 호환 통합 진입점                  │  │
│  │   /api/admin/*          ─ 운영자 콘솔 (Agent/KB/Key/Usage)         │  │
│  │   /signalr/notifications─ 실시간 알림                              │  │
│  │                                                                   │  │
│  │   ┌──────────────┐  ┌────────────┐  ┌──────────────────────┐    │  │
│  │   │ AiProxySvc   │→│ HybridRouter│→│ Provider Branch      │    │  │
│  │   │ (entry)      │  │ (PII/Cost) │  │ openai/claude/...    │    │  │
│  │   └──────────────┘  └────────────┘  │ + nexus (옵션 B)     │    │  │
│  │                                     └──────────┬───────────┘    │  │
│  │   ┌──────────────┐  ┌────────────┐             │                │  │
│  │   │ ApiKeyAuth   │  │ Quota/Usage│             │                │  │
│  │   └──────────────┘  └────────────┘             │                │  │
│  │   ┌──────────────────────────────────────┐    │                │  │
│  │   │ RagService (BFF → DocUtil)           │    │                │  │
│  │   └──────────────────────────────────────┘    │                │  │
│  └─────────────────────────────────────────────────┼────────────────┘  │
└─────────────────────────────────────────────────────┼──────────────────┘
        │                              │              │
        │ External LLM                 │ Internal LLM │ RAG/KB
        │ (외부망/하이브리드)             │ (내부망)      │
        ▼                              ▼              ▼
┌──────────────────┐        ┌───────────────┐  ┌───────────────────┐
│ OpenAI / Claude  │        │ Nexus         │  │ DocUtil           │
│ Gemini / Mistral │        │ (LAN-only,    │  │ (FastAPI +        │
│ Perplexity / ... │        │  air-gapped)  │  │  Qdrant + RAG)    │
└──────────────────┘        └───────────────┘  └───────────────────┘
                                                        │
                                                        ▼
                                          ┌─────────────────────────┐
                                          │  PostgreSQL: AGENT_HUB   │
                                          │  ┌──────────────────┐   │
                                          │  │ AIAgentManagement│   │
                                          │  │ document_util... │   │
                                          │  │ idino_career     │   │
                                          │  │ hangfire         │   │
                                          │  │ + pgvector       │   │
                                          │  └──────────────────┘   │
                                          └─────────────────────────┘
```

---

## 2. 핵심 원칙

| ID | 원칙 | 의미 |
|---|---|---|
| P1 | **Control Plane = AgentHub** | Agent 정의, ApiKey 발급, 사용량 집계, 라우팅 정책의 단일 권위 |
| P2 | **Data Plane = End-User Apps** | docutil/career는 사용자 경험만 담당, AI 호출은 모두 AgentHub 위임 |
| P3 | **단일 AI 진입점** | LLM SDK 직접 호출 금지 — 항상 `AgentHub /v1/chat/completions` |
| P4 | **스키마 격리** | `AGENT_HUB` DB 안에 4개 schema, cross-schema join 금지 |
| P5 | **Nexus 옵션 B** | AgentHub-side `CallNexusAsync`로 Nexus 네이티브 API 직접 호출 |
| P6 | **RAG 단일 권위 = DocUtil** | AgentHub 자체 KB는 deprecate, 모든 문서/벡터는 DocUtil |
| P7 | **운영자 = AgentHub UI** | DocUtil/career의 운영자 화면 → AgentHub로 흡수, 사용자 화면만 자체 유지 |
| P8 | **환경별 선택적 활성화** | 외부망/내부망/하이브리드 — 동일 코드베이스, 시드/환경변수만 다름 |
| P9 | **언어/런타임 격리** | .NET, Python, Node.js — 통신은 HTTP/SSE만 |
| P10 | **시크릿은 환경변수/Vault** | `.env`, `appsettings.*.json`은 모두 `.gitignore` |

---

## 3. 컴포넌트별 책임

### 3.1 AgentHub (`agenthub/`)
| 책임 | 세부 |
|---|---|
| Agent 정의 마스터 | `Agents` 테이블 — Code, Persona, SystemPrompt, LlmRouting, RoutingPolicyJson |
| LLM Provider 카탈로그 | `ApiServices`, `ApiServiceModels` (openai/claude/gemini/.../nexus) |
| LLM 라우팅 결정 | `HybridRouter` — PII / 데이터 라벨 / 비용 / capability 기반 |
| ApiKey 발급/검증 | `ak-{base64}` + Scopes + AgentId 매핑 |
| 사용량 추적 | `ApiUsages`, `ApiQuotas` — 토큰/비용/RPM 집계 |
| 운영자 UI | Vue 3 — Agent 빌더, KB 관리(BFF), Key 발급, 사용량 분석 |
| RAG BFF | DocUtil API 프록시 (운영자 KB 관리 UI를 AgentHub에서) |
| 실시간 알림 | SignalR Hub |

### 3.2 DocUtil (`docutil/`)
| 책임 | 세부 |
|---|---|
| 문서 RAG 권위 | 문서 업로드 → 청크 → 임베딩 → Qdrant 저장 |
| Collection 관리 | DocUtil API가 마스터, AgentHub는 BFF로 노출 |
| 사용자 챗봇 | Next.js — 사용자 화면만 유지 (운영자 페이지는 AgentHub로 이관) |
| AI 호출 | 자체 OpenAI SDK 호출 → AgentHub `/v1/chat/completions`로 전환 |

### 3.3 idino_career (`career/`)
| 책임 | 세부 |
|---|---|
| 18개 MS | 학생 데이터, 코칭, 학습 콘텐츠 등 도메인 로직 |
| 사용자 포털 | Next.js — 학생/교사 사용자 화면 |
| AI 호출 | 각 MS의 LLM 호출 → AgentHub Agent API로 전환 |
| 자체 데이터 | `idino_career` 스키마 — AgentHub와 분리 유지 |

### 3.4 Nexus (`nexus/`)
| 책임 | 세부 |
|---|---|
| 내부망 LLM | vLLM 기반 자체 모델 서빙 |
| 4-Tier 비동기 체인 | Web → Service → Core → Provider |
| API Key Pool | 멀티 키 회전 + 쿨다운 |
| 멀티 테넌시 | `tenant_id` 헤더 기반 격리 |
| 세션 관리 | Redis 세션 + 자체 컨텍스트 윈도우 |
| 외부 노출 금지 | LAN-only, AgentHub만 호출 가능 |

### 3.5 PostgreSQL (`infra/db/`)
| DB | Schema | 소유 시스템 |
|---|---|---|
| `AGENT_HUB` | `AIAgentManagement` | agenthub |
| `AGENT_HUB` | `document_utilization` | docutil |
| `AGENT_HUB` | `idino_career` | career |
| `AGENT_HUB` | `hangfire` | agenthub (백그라운드 작업) |
| `AGENT_HUB` | `public` (확장) | pgvector / uuid-ossp / pg_trgm |

---

## 4. 핵심 시퀀스

### 4.1 End-User 챗 (External 라우팅)
```
사용자(docutil-user)
  → Next.js
  → AgentHub /v1/chat/completions  (X-API-Key)
  → ApiKeyAuth → AgentResolve → HybridRouter
  → 결정: External
  → AiProxyService.CallOpenAIAsync
  → OpenAI API
  → SSE 스트림 ← OpenAI
  → 사용자 (실시간 수신)
  → ApiUsages 기록
```

### 4.2 End-User 챗 (Internal 라우팅 — Nexus)
```
사용자(career-student)
  → Next.js
  → AgentHub /v1/chat/completions  (X-API-Key, PII 포함)
  → HybridRouter: PII detected → Internal
  → AiProxyService.CallNexusAsync  (옵션 B)
  → Nexus /v1/chat (네이티브 API, session_id, tenant_id 헤더)
  → Nexus 4-Tier 체인 → vLLM
  → SSE 스트림 ← Nexus
  → 사용자
  → ApiUsages 기록 (provider=nexus, cost=0)
```

### 4.3 RAG (DocUtil 위임)
```
사용자
  → AgentHub /v1/chat/completions (Agent에 KnowledgeBaseRef 매핑됨)
  → AgentHub: RagService.RetrieveContextAsync(query, collectionId)
    → DocUtil /api/rag/search (BFF 호출)
    → Qdrant 검색
    → 컨텍스트 반환
  → AgentHub: 컨텍스트 + 사용자 질문을 LLM에 전달
  → 응답
```

### 4.4 운영자 KB 등록
```
운영자(AgentHub UI)
  → Vue: 문서 업로드
  → AgentHub /api/admin/kb/upload (BFF)
    → DocUtil /api/documents/upload
    → 청크/임베딩/Qdrant 저장
  → SignalR로 진행률 푸시
  → 완료 → DocUtil collection_id를 Agent에 매핑
```

---

## 5. 데이터 모델 핵심

`Agent` 엔티티 (AgentHub 관점):
```
AgentId, AgentCode (외부 노출용 식별자)
DisplayName, Description, Persona, SystemPrompt
LlmRouting: External | Internal | Hybrid
RoutingPolicyJson: Hybrid 모드의 결정 규칙
ApiServiceCode + ModelCode: 기본 LLM
KnowledgeBaseSource: AgentHub | DocUtil  (Phase 6 이후 DocUtil 통일)
KnowledgeBaseRef: DocUtil collection ID
ConsumerSystems: ["docutil-user", "career-coaching", ...]
CreatedBy, CreatedAt, IsActive
```

상세 도메인 모델은 `.claude/rules/domain-model.md` 참조.

---

## 6. 주요 결정 사항

| 결정 | 선택 | 이유 |
|---|---|---|
| Nexus 통합 방식 | **옵션 B** (AgentHub-side `CallNexusAsync`) | Nexus의 세션/멀티테넌시 강점 보존, 기존 AgentHub 패턴(Claude/Gemini도 네이티브 호출)과 일치 |
| RAG 권위 | **DocUtil 단일** | AgentHub 자체 KB는 deprecate. 중복 권위 제거 |
| 프론트엔드 | **Vue 3 유지 (Phase 8 보류)** | 본 통합의 핵심 가치는 데이터플레인 통합. 프레임워크 마이그레이션은 별도 트랙 |
| DB | **단일 PostgreSQL `AGENT_HUB`** | 192.168.10.39:5440, 4개 schema |
| MSSQL → PostgreSQL | **EF Core Provider 교체 + 데이터 이전** | Npgsql, Hangfire.PostgreSql, baseline 마이그레이션 |
| 시크릿 | **환경변수 + .gitignore** | `appsettings.Development.json`, `.env` 모두 비커밋 |
| ApiKey 암호화 | **AES-256-GCM + per-record 12B nonce + 별도 운영 키** (ADR-16) | `Encryption:ApiKeyAesKey` 32B raw. Phase 9 이관 시 legacy CBC + 고정 IV 1행 GCM 재암호화. JWT-derived 키 폴백 분리 |
| ENCRYPTION_KEY validator | **3중 검증** (ADR-17) | 16자/32자 반복 차단 + distinct ≥ 16/32 + Shannon entropy ≥ 4.5. 약한 키 부팅 거부 (트랙 #65) |
| db_schema validator | **4중 검증** (ADR-17) | 빈 값 / `public` / 비알파 reject. Phase 4.1 ADR-5 schema 격리 우회 차단 (트랙 #67) |
| alembic 마이그레이션 | **schema-agnostic** (ADR-18) | env.py 5중 안전 (`version_table_schema` / `include_schemas` / `CREATE SCHEMA` / `SET LOCAL search_path` / `connect_args`) 에 일임. CI 게이트 18/18 PASS (트랙 #70) |
| 운영 임시 secrets | **적용 후 즉시 shred + rm** (ADR-19) | `.env.bak.*` (0600) 만 회복 경로. 별도 평문 파일은 lateral move 위험 (트랙 #62) |
| DocUtil tb_llm_api_keys | **Phase 7 R2 deprecate** | AgentHub `/v1/*` 위임 단일 권위. 옵션 A 적용: 모델/라우터/서비스 docstring + 헤더 `Deprecation: true` + 프론트 WarningBanner (트랙 #69) |

---

## 7. 환경별 배포 매트릭스

| 환경 | agenthub | docutil | career | nexus | External LLM |
|---|---|---|---|---|---|
| 외부망 | ON | ON | ON | OFF | ON |
| 내부망 | ON | ON | ON | ON | 차단 |
| 하이브리드 | ON | ON | ON | ON | ON |

동일 코드베이스, 다른 ApiServices 시드 + 환경변수 설정.

---

## 8. 참조

- `CLAUDE.md` — AI 코딩 도구 협업 컨텍스트
- `.claude/rules/architecture.md` — 원칙 P1~P10 상세
- `.claude/rules/domain-model.md` — 엔티티/용어 정의
- `.claude/rules/anti-patterns.md` — 금지 패턴
- `.claude/rules/testing.md` — 테스트 전략
- `.claude/rules/development-workflow.md` — Phase별 작업 순서
- `.claude/rules/agent-collaboration.md` — AI 코딩 도구 협업 절차
- `docs/AI_INVENTORY.md` — AI 호출 인벤토리 (Phase 1 산출물)
- `docs/DB_MIGRATION.md` — DB 마이그레이션 기록 (Phase 2 이후 산출물)
- `agenthub/TECHSPEC.md` — AgentHub 기술 스펙 (이전 분석 산출물)
