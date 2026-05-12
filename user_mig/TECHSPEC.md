# IDINO Agent Hub — 통합 기술 명세서 (TECHSPEC)

> **버전**: v1.0 (2026-05-04)
> **위치**: `D:\workspace\IDINO_Agent_Hub\user_mig\TECHSPEC.md`
> **상태**: Phase 0 완료 / Phase 1~8 계획
> **참조 보고서**:
> - `user_mig/source_AGENTHUB.md` (AIAgentManagement 분석)
> - `user_mig/source_DOCUTIL.md` (document_utilization 분석)
> - `user_mig/source_CAREER.md` (idino_career 분석)
> - `user_mig/source_NEXUS.md` (nexus 분석)
> **진행 추적**: `user_mig/progress.md` (모든 작업 후 갱신)

---

## 목차

1. [개요와 통합 비전](#1-개요와-통합-비전)
2. [시스템 카탈로그](#2-시스템-카탈로그)
3. [아키텍처 — Control Plane / Data Plane](#3-아키텍처--control-plane--data-plane)
4. [통합 도메인 모델](#4-통합-도메인-모델)
5. [데이터 아키텍처](#5-데이터-아키텍처)
6. [API 명세](#6-api-명세)
7. [인증 / 권한 / 멀티테넌시](#7-인증--권한--멀티테넌시)
8. [AI 호출 인벤토리 + Agent 카탈로그](#8-ai-호출-인벤토리--agent-카탈로그)
9. [RAG 통합 — DocUtil 단일 권위](#9-rag-통합--docutil-단일-권위)
10. [LLM 라우팅 — External/Internal/Hybrid](#10-llm-라우팅--externalinternalhybrid)
11. [운영자 콘솔 — AgentHub Vue + BFF](#11-운영자-콘솔--agenthub-vue--bff)
12. [마이그레이션 전략 (Phase 0~8)](#12-마이그레이션-전략-phase-08)
13. [보안 / 시크릿 / 암호화](#13-보안--시크릿--암호화)
14. [환경별 배포 / 포트 매트릭스](#14-환경별-배포--포트-매트릭스)
15. [미완성 부분 보강 계획](#15-미완성-부분-보강-계획)
16. [위험 분석 및 완화 (R1~R30)](#16-위험-분석-및-완화-r1r30)
17. [테스트 전략](#17-테스트-전략)
18. [모니터링 / 관찰성 / 운영](#18-모니터링--관찰성--운영)
19. [일정 / 마일스톤 / 의존성](#19-일정--마일스톤--의존성)
20. [의사결정 기록 (ADR 요약)](#20-의사결정-기록-adr-요약)
21. [미해결 결정 / Open Questions](#21-미해결-결정--open-questions)

---

## 1. 개요와 통합 비전

### 1.1 목적

기존 4개 독립 시스템을 단일 monorepo `IDINO_Agent_Hub`로 묶고, **AgentHub를 단일 AI 운영(Control Plane)으로 격상**, 나머지 시스템은 **사용자/도메인 앱(Data Plane)** 으로 재정의한다. 모든 AI 호출(LLM, 임베딩, 이미지 생성)은 AgentHub를 단일 진입점으로 경유하며, 라우팅(External/Internal/Hybrid)·사용량·할당량·PII·보안은 AgentHub에 집중된다.

### 1.2 통합 전 상태 (2026-05-04 기준)

| 시스템 | 한 줄 정의 | 완성도 | 핵심 미완성 |
|---|---|---|---|
| **AgentHub** (`agenthub/`) | 다중 LLM 게이트웨이 + Agent 빌더 + RAG | 운영 단계, 부채 누적 | EF baseline 부재, 가짜 SSE, AES 고정 IV, AiProxyService 3,749 LOC god class |
| **DocUtil** (`docutil/`) | 문서 RAG 챗봇 + 보고서/PPT 생성 | Phase 4 ~54% (S1~S3 완료) | Mode B(S4)·HWPX(S5)·회의록 RAG(S6)·jinja 폐기(S7) 미완 |
| **idino_career** (`career/`) | 학생/진로 18 MS + AI ActionBoard | Phase 100% 표기, 실측 갭 존재 | pgvector DDL 미적용, 자동테스트 부재, Kafka 미사용 |
| **Nexus** (`nexus/`) | LAN-only 내부 LLM 서버 (vLLM) | 운영 단계 | 외부 노출 시 인증 부재 (LAN 격리에 의존) |

### 1.3 통합 후 목표

1. **단일 AI 게이트웨이**: 4개 시스템 어디서 발생한 LLM 호출이든 AgentHub `/v1/chat/completions`를 경유.
2. **단일 RAG 권위**: DocUtil이 모든 문서/벡터/검색을 담당. AgentHub 자체 KB는 deprecate.
3. **단일 운영자 콘솔**: AgentHub Vue UI가 Agent/Key/Quota/사용량/KB(BFF)를 일원화 관리.
4. **단일 PostgreSQL 인스턴스**: `AGENT_HUB` DB 하나에 4개 schema 격리.
5. **환경별 활성화**: 외부망(External만) / 내부망(Nexus만) / 하이브리드 — 동일 코드베이스, 시드/환경변수만 다름.
6. **각 시스템의 미완성 부분을 통합 과정에서 함께 보강** (TechSpec 표기와 실측 갭 해소).

### 1.4 비목표 (Non-goals)

- Vue 3 → Next.js 전면 이행은 본 통합의 핵심 가치가 아니며 **Phase 8(보류)** 로 분리.
- DocUtil의 사용자 챗봇 UI를 AgentHub로 흡수하지 않는다 (사용자 앱은 도메인별로 유지).
- career의 18 MS를 단일 모놀리스로 합치지 않는다 (각 MS 책임 유지, AI 호출만 위임).
- Nexus 자체를 재작성하지 않는다 (옵션 B — AgentHub에 클라이언트 추가).

### 1.5 본 문서 작성 원칙

- **설계 오류 방지**: 4개 시스템의 충돌 가능 지점(스키마, 인증, 임베딩 차원, agent_type, role 등)을 명시.
- **추측 최소화**: 보고서(`source_*.md`)에서 실측된 사실만 인용. 추정/가정은 명시.
- **위치 참조**: 코드 변경 지점은 `subproject/path/file.ext:line` 형식.
- **한국어 설명 + 영문 식별자**: 사용자 메시지/주석은 한국어, 변수/함수/커밋은 영어.
- **모든 작업 완료 시 `progress.md` 갱신** (agent-collaboration.md 규칙).

---

## 2. 시스템 카탈로그

### 2.1 4개 서브프로젝트

| ID | 디렉토리 | 역할 (통합 후) | 기술 스택 | 상태 |
|---|---|---|---|---|
| `agenthub` | `agenthub/` | **Control Plane** (운영자 + LLM 게이트웨이) | .NET 8 / EF Core / Vue 3 / SignalR / Hangfire | MSSQL→PG 전환 + Nexus provider + DocUtil BFF 추가 |
| `docutil` | `docutil/` | **Data Plane** (사용자 챗봇) + **RAG 단일 권위** | FastAPI / Next.js 16 / Qdrant / Redis / RabbitMQ | Phase 4 진행 중, LLM 호출 위임화 + 운영자 UI 일부 흡수 |
| `career` | `career/` | **Data Plane** (학생/진로 18 MS + 사용자 포털) | FastAPI 18 MS / Next.js 14 / Kong | LLM 직접 호출 → AgentHub 위임, pgvector 활성화 |
| `nexus` | `nexus/` | **Internal LLM Provider** (LAN-only) | Python asyncio / vLLM / Qwen 3.5 27B | 코드 변경 최소, AgentHub `CallNexusAsync` 클라이언트 신설 |

### 2.2 외부 의존성

| 의존성 | 용도 | 통합 정책 |
|---|---|---|
| **PostgreSQL 17** (192.168.10.39:5440) | 모든 OLTP 데이터 | 단일 인스턴스 + 4 schema + pgvector |
| **Qdrant 1.16** | 문서 벡터 검색 | DocUtil 단일 collection (`documents`), AgentHub 자체 KB는 deprecate |
| **Redis 7** | 세션 / OTP / Rate Limit / 캐시 | 단일 인스턴스, key prefix 분리(`agenthub:`, `docutil:`, `career:`, `nexus:`) |
| **RabbitMQ 4** | DocUtil Celery 워커 | DocUtil 전용 유지 (다른 시스템은 Hangfire/Channels) |
| **MinIO** | DocUtil 객체 저장 (문서 원본) | DocUtil 전용 |
| **Kong** | career API Gateway | career 전용 유지 |
| **External LLM** (OpenAI/Claude/Gemini/Mistral/Perplexity/Vertex/Copilot/Azure) | External 라우팅 | AgentHub만 호출 가능 |
| **Nexus vLLM GPU 서버** (192.168.22.28:8001) | Internal LLM | AgentHub `CallNexusAsync`만 호출 |
| **Unsplash + DALL-E 3** | 이미지 생성 | DocUtil → AgentHub 위임 (Phase 7) |
| **LibreOffice** | HWP/PPTX↔PDF | AgentHub(현재) + DocUtil(S5 사이드카) |
| **docling VLM** | 문서 OCR 파싱 | DocUtil 전용 |

### 2.3 외부 노출 / 내부 호출 그래프 (목표)

```
[외부 사용자]
  ├─ docutil-user (Next.js 3000) ────────┐
  ├─ career-student (Next.js 3001) ──────┤
  ├─ embed-public (iframe) ──────────────┤
  └─ external-sdk (OpenAI 호환) ─────────┤
                                          ▼
                               [AgentHub Gateway :5001]
                                /v1/chat/completions
                                /api/admin/* (운영자)
                                /signalr/* (실시간)
                                          │
        ┌─────────────────────────────────┼──────────────────────┐
        ▼                                 ▼                      ▼
   External LLM                    Nexus :8001 (LAN)       DocUtil :8000
   (OpenAI/Claude/...)              CallNexusAsync         /api/v1/search/*
                                                           /api/v1/documents/*
                                                                  │
                                                                  ▼
                                                          Qdrant :6333
                                                                  │
   ──────────────────────────────────────────────────────────────┴──────
                              PostgreSQL :5440 / AGENT_HUB DB
                              ┌──────────────┬──────────────────┐
                              │ AIAgent...   │ document_util... │ idino_career │ hangfire │
                              └──────────────┴──────────────────┘
```

career의 18 MS는 내부적으로 Kong을 거쳐 통신하지만, **AI 호출만은 AgentHub로 직행** (Kong을 거치지 않거나 Kong이 AgentHub로 라우팅 추가).

---

## 3. 아키텍처 — Control Plane / Data Plane

### 3.1 핵심 원칙 (10개)

| ID | 원칙 | 의미 |
|---|---|---|
| **P1** | **Control Plane = AgentHub** | Agent/Key/Quota/Usage/Routing의 단일 권위 |
| **P2** | **Data Plane = End-User Apps** | 사용자 경험 + 도메인 로직만 담당, AI는 위임 |
| **P3** | **단일 AI 진입점** | 모든 LLM 호출은 AgentHub `/v1/chat/completions` 경유. SDK 직접 import 금지 |
| **P4** | **스키마 격리** | `AGENT_HUB` DB 안에 4개 schema, **cross-schema join 금지** |
| **P5** | **Nexus 옵션 B** | AgentHub-side `CallNexusAsync`, Nexus 네이티브 API 직접 호출 (세션/멀티테넌시 보존) |
| **P6** | **RAG 단일 권위 = DocUtil** | AgentHub 자체 KB deprecate, 모든 문서/벡터/검색은 DocUtil. AgentHub는 BFF로 노출 |
| **P7** | **운영자 단일 콘솔 = AgentHub UI** | DocUtil/career 운영자 화면 중 AI/사용자/Key/Quota는 AgentHub로 흡수, 도메인 전용은 BFF |
| **P8** | **순환 호출 금지** | DocUtil은 컨텍스트만 반환(`/search/hybrid`), LLM 합성은 AgentHub 단일 책임 |
| **P9** | **언어/런타임 격리** | .NET, Python, Node.js 간 통신은 HTTP/SSE/WebSocket만 |
| **P10** | **시크릿 비커밋** | `.env`, `appsettings.*.json`, `nexus_config.yaml` 모두 `.gitignore` |

### 3.2 책임 매트릭스

| 책임 | AgentHub | DocUtil | career | Nexus |
|---|:---:|:---:|:---:|:---:|
| 사용자 인증 발급 (JWT) | ◎ | ○ (자체 검증) | ○ (자체 검증) | × |
| API Key 발급/검증 | ◎ | × | × | × |
| LLM 호출 진입점 | ◎ | × (위임) | × (위임) | △ (서빙) |
| 라우팅 결정 (External/Internal/Hybrid) | ◎ | × | × | × |
| 사용량/할당량 추적 | ◎ | × | × | △ (자체 카운터) |
| PII 감지/마스킹 | ◎ | △ (보조) | △ (보조) | × |
| BannedWord 검사 | ◎ | × | × | × |
| 문서 업로드/파싱 | × (BFF) | ◎ | × | × |
| 청크/임베딩/벡터 저장 | × | ◎ | × | △ (자체 RAG) |
| 검색 (hybrid) | × (BFF) | ◎ | × | △ (자체 RAG) |
| 학생/진로 도메인 데이터 | × | × | ◎ | × |
| Agent 정의 저장 (SystemPrompt 등) | ◎ | × | × | × |
| Tool 정의 / 실행 | ◎ | × | × | △ (web 도구 8개) |
| 사용자 챗봇 UI | △ (embed/admin) | ◎ (DocUtil 사용자) | ◎ (학생 포털) | △ (테스트 UI) |
| 운영자 콘솔 UI | ◎ | × (흡수) | × (흡수) | × |
| 활동 로그 (감사) | ◎ | △ (자체) | △ (자체) | △ |
| 백그라운드 작업 | ◎ (Hangfire) | ◎ (Celery) | × | × |
| 헬스체크 / 메트릭 | ◎ | ◎ | ◎ | ◎ |

범례: ◎ 단일 권위 / ○ 보조 권위 / △ 부분 책임 / × 미담당

### 3.3 통신 프로토콜 표준

| 패턴 | 프로토콜 | 인증 |
|---|---|---|
| End-User 앱 → AgentHub (LLM 호출) | HTTPS + SSE | API Key (`X-API-Key: ak-{base64}`) |
| 운영자 UI(AgentHub Vue) → AgentHub API | HTTPS | JWT Bearer (`Authorization: Bearer ...`) |
| AgentHub → External LLM | HTTPS | 프로바이더별 API Key (Named HttpClient 풀) |
| AgentHub → Nexus | HTTPS LAN + SSE | `X-Tenant-ID` + 공유 시크릿(신설) `X-Hub-Auth: Bearer ...` |
| AgentHub → DocUtil (BFF) | HTTPS | 내부 mTLS 또는 공유 시크릿 |
| AgentHub → SignalR Client | WebSocket + SSE 폴백 | JWT (Hub `[Authorize]` 강제 — C8 해결) |
| career MS 간 | HTTP/JSON via Kong | JWT (자체 검증) |
| 모든 시스템 → PostgreSQL | TCP+TLS | DB user `AGENT_HUB` + schema-level GRANT |
| DocUtil → Qdrant | HTTP | 내부 LAN |
| 모든 시스템 → Redis | TCP | 비밀번호 + key prefix 분리 |

---

## 4. 통합 도메인 모델

### 4.1 핵심 엔티티 (Master, AgentHub Control Plane)

#### 4.1.1 `Agent` (AgentHub `Agents` 테이블)

| 필드 | 타입 | 설명 |
|---|---|---|
| `AgentId` | int identity | 내부 PK |
| `AgentCode` | nvarchar(80) UNIQUE | **외부 노출 식별자** (예: `career-coaching`, `docutil-rag-chat`) |
| `DisplayName` | nvarchar(200) | UI용 |
| `Description` | nvarchar(1000) | |
| `Persona` | nvarchar(MAX) | |
| `SystemPrompt` | nvarchar(MAX) | |
| `Temperature` | decimal(3,2) | 기본 0.7 |
| `DefaultModel` | nvarchar(100) | `gpt-4o-mini`, `claude-sonnet-4`, `nexus-phase3` 등 |
| `LlmRouting` | int (enum) | 0=External, 1=Internal, 2=Hybrid (**신규**) |
| `RoutingPolicyJson` | jsonb | Hybrid 규칙 (§10) (**신규**) |
| `KnowledgeBaseSource` | int (enum) | 0=AgentHubLegacy(deprecate), 1=DocUtil (**신규**) |
| `KnowledgeBaseRef` | nvarchar(200) | DocUtil collection or scope ID (**신규**) |
| `ConsumerSystems` | jsonb | 어느 End-User 앱이 사용 가능한지 (`["docutil-user","career-coaching"]`) (**신규**) |
| `ResponseFormat` | jsonb null | JSON Schema strict (career의 ActionBoard용) (**신규**) |
| `EnableRag` | bit | |
| `EnableWebSearch` | bit | |
| `PiiProtection` | bit | |
| `PiiMode` | nvarchar(20) | `block` / `mask` |
| `IsPublic` | bit | |
| `AllowGuestChat` | bit | |
| `AllowedEmbedDomains` | jsonb | |
| `WelcomeMessage` | nvarchar(500) | |
| `CreatedBy` | int FK Users | |
| `CreatedAt` | timestamptz | |
| `UpdatedAt` | timestamptz | |
| `IsActive` | bit | |

**ServiceId Cascade Delete 위험 해소** (R12 참조): FK to ApiServices를 Restrict로 강등.

#### 4.1.2 `ApiService` (LLM 프로바이더 카탈로그)

| 필드 | 타입 | 설명 |
|---|---|---|
| `ApiServiceId` | int identity | |
| `ServiceCode` | varchar(40) UNIQUE | `openai`, `claude`, `gemini`, `vertex`, `mistral`, `perplexity`, `azureopenai`, `copilot`, `tavily`, `nexus`(신규), `dalle`, `gemini-image`, `imagen4`, `flux2`, `gen4-image`, `gen4-video`, `veo`, `openai-video` |
| `ServiceType` | varchar(40) | Chat / ImageGeneration / VideoGeneration / Embedding |
| `BaseUrl` | varchar(500) | |
| `IsActive` | bit | |
| `Tier` | varchar(20) | External / Internal |

#### 4.1.3 `ApiServiceModel` (모델 카탈로그)

`ApiServiceId` FK + `ModelCode` (`gpt-4o-mini`, `claude-sonnet-4-20250514`, `gemini-2.0-flash`, `nexus-phase3`, `qwen3.5-27b`, `text-embedding-3-small`, `multilingual-e5-large` 등).

#### 4.1.4 `ApiKey` (외부 시스템 → AgentHub 인증)

| 필드 | 타입 | 설명 |
|---|---|---|
| `ApiKeyId` | int | |
| `KeyHash` | varchar(64) UNIQUE INDEX | **신규** SHA-256 (C3 해결) |
| `EncryptedKey` | varbytea(...) | per-record random IV + AES-GCM (C1 해결) |
| `KeyPreview` | varchar(20) | UI용 (`ak-XXXX****`) |
| `AgentId` | int FK null | 키 ↔ Agent 1:N |
| `Scopes` | varchar(200) | `chat,stream,info,usage,admin` |
| `ConsumerSystem` | varchar(40) | `docutil-user`, `career-coaching`, `external-sdk` |
| `AllowedIps` | jsonb | CIDR 지원 (R8 해결) |
| `RateLimitPerMinute/Hour/Day` | int | |
| `ExpiresAt` | timestamptz null | |
| `RevokedAt` | timestamptz null | |
| `LastUsedAt` | timestamptz null | |
| `PreviousKeyHash` | varchar(64) null | 회전 시 24h 유예 (**신규**) |
| `RotatedAt` | timestamptz null | (**신규**) |

#### 4.1.5 `ApiQuota`, `ApiUsage`, `ChatConversation`, `ChatMessage`

기존 AgentHub 설계 유지. 변경점:
- `ChatConversation`에 `NexusSessionId varchar(64) null` 컬럼 추가 (Nexus 1:1 매핑) (**신규**).
- `ChatConversation`에 `OrganizationId varchar(64) null` 컬럼 추가 (DocUtil multi-tenant 동기) (**신규**).
- `ApiUsage`의 `Cost`는 internal(nexus) 호출 시 0 또는 GPU 단가 환산.
- `QuotaService.RecordUsageAsync`의 **토큰수 무시 버그 수정** (H10).

### 4.2 도메인 엔티티 (Data Plane)

#### 4.2.1 DocUtil (`document_utilization` schema)

핵심 엔티티 그대로 유지: `tb_documents`, `tb_document_chunks`, `tb_chat_sessions`, `tb_chat_messages`, `tb_documents_v2`, `tb_documents_v2_templates`, `tb_search_scopes`, `tb_organization_quotas`, `tb_generated_reports_archive`(deprecate).

**제거 대상** (AgentHub로 흡수):
- `tb_users` — AgentHub `Users`로 통합 (DocUtil은 view 또는 캐시)
- `tb_organizations` — AgentHub `Organizations`(신규) 또는 `Tenants`(신규)로 통합
- `tb_user_roles` / `tb_api_keys` — AgentHub `UserRoles` / `ApiKeys`로 통합
- `tb_agents` — AgentHub `Agents`로 통합 (agent_type은 metadata.tag로 보존)
- `tb_audit_log` — AgentHub `ActivityLog`로 통합

**이전 매핑**:
| DocUtil agent_type | AgentHub AgentCode (예시) |
|---|---|
| `chatbot` | `docutil-rag-chat` |
| `report` | `docutil-report-generator` |
| `proposal` | `docutil-proposal-generator` |
| `minutes` | `docutil-meeting-minutes` |

#### 4.2.2 idino_career (`idino_career` schema)

**유지**: 53 테이블 그대로 (`tb_university`, `tb_student`, `tb_competency`, `tb_skill`, `tb_recommendation_run`, `tb_opportunity`, `tb_coaching_*`, `tb_simulation_*`, `tb_advisor_*`, `tb_badge`, ...).

**변경**:
- `tb_user` (career 자체) → AgentHub `Users`로 단방향 통합 (career는 view 또는 별칭)
- `role_level` 정수 → AgentHub `Role` enum 매핑 (Student=1, Advisor=2, DepartmentAdmin=3, CareerCenterAdmin=4, SystemAdmin=5)
- audit 컬럼(`ins_user_id, ins_dt, upd_user_id, upd_dt`) — AgentHub 표준 `CreatedAt/UpdatedAt`과 **병행 유지** (이미 적재된 53 테이블 데이터 보존)
- `pgvector` extension 활성화 + `tb_course/tb_program/tb_success_pattern.embedding vector(1536)` 컬럼 추가 + 백필

#### 4.2.3 nexus (`nexus` schema 또는 별도 DB)

**결정 (R5)**: Nexus DB는 **별도 인스턴스 또는 별도 schema 유지**. 통합하지 않음.
이유: `tb_knowledge` 100만 청크 + 1024D 벡터 + IVFFlat 인덱스 + 멀티테넌시는 AgentHub와 라이프사이클이 다름.
대안: `AGENT_HUB.nexus` schema로 두되 AgentHub는 직접 접근 금지, Nexus만 R/W.

### 4.3 통합 후 ER 관계도 (논리)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT_HUB.AIAgentManagement                      │
│                                                                       │
│  Users ─── UserRoles ─── Roles                                        │
│   │                                                                   │
│   ├── Teams ─── TeamMembers                                           │
│   ├── ApiQuotas ── ApiServices ── ApiServiceModels                   │
│   ├── ApiKeys ── (ApiServiceCode, AgentId)                            │
│   ├── Agents ─── AgentDocuments ─── DocUtilDocumentRef (FK 문자열)    │
│   │                                                                   │
│   ├── ChatConversations ─── ChatMessages                              │
│   │     └── NexusSessionId (Nexus 매핑)                              │
│   │     └── OrganizationId (DocUtil 매핑)                            │
│   ├── ApiUsages (시계열, bigint)                                      │
│   ├── ActivityLogs (시계열)                                           │
│   ├── PiiDetectionLogs                                                │
│   ├── BannedWords                                                     │
│   ├── Tools ─── ToolVersions ─── ToolExecutions                       │
│   ├── Workflows ─── WorkflowNodes ─── WorkflowExecutions              │
│   └── Presentations ─── PresentationSlides ─── PresentationTemplates  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────┐
│ document_utilization │  │   idino_career       │  │ nexus / hangfire│
│                      │  │                      │  │                 │
│ tb_documents         │  │ tb_university        │  │ tb_knowledge    │
│ tb_document_chunks   │  │ tb_student           │  │ tb_memories     │
│ tb_chat_sessions     │  │ tb_competency        │  │ tb_symbols      │
│ tb_chat_messages     │  │ tb_skill             │  │ ...             │
│ tb_documents_v2      │  │ tb_recommendation_*  │  │ Hangfire jobs   │
│ tb_search_scopes     │  │ tb_coaching_*        │  │                 │
│ tb_organization_*    │  │ tb_simulation_*      │  │                 │
│ ...                  │  │ tb_advisor_*         │  │                 │
└──────────────────────┘  │ ...                  │  └─────────────────┘
                          └──────────────────────┘
```

**중요 제약**:
- 4 schema 간 **외래키 금지**, 데이터 합성은 HTTP API.
- `Users` / `Organizations` / `ApiKeys`는 AIAgentManagement 단일 권위. DocUtil/career는 read-only 참조 또는 자체 캐시.

### 4.4 용어 표준 (혼용 금지)

| 정확한 용어 | 금지 용어 |
|---|---|
| Agent | bot, assistant, character, persona |
| LLM Provider / ApiService | provider, vendor, llm |
| Routing | dispatch, decision (의사결정 ≠ 라우팅) |
| Internal LLM = Nexus | local llm, on-prem llm, private llm |
| External LLM | cloud llm, public llm |
| Knowledge Base | document store, vector db |
| Conversation | session, thread, chat (단독) |
| AgentCode | agent slug, agent name |
| ApiKey (외부) | secret, token (JWT와 혼동 방지) |
| Tenant | organization (DocUtil의 organization과는 별개 의미) |

### 4.5 Tenant / Organization 모델

DocUtil/career의 `organization_id` ↔ AgentHub의 `Tenant` 개념을 **통합**한다 (**신규**).

- 신규 엔티티 `Tenants` (AIAgentManagement schema):
  - `TenantId int identity`, `TenantCode varchar(80) UNIQUE`, `DisplayName`, `Slug`, `OrganizationType` (`internal` / `school` / `enterprise`), `Settings jsonb`, `IsActive`.
- 모든 사용자/Agent/ApiKey는 `TenantId` FK 보유.
- DocUtil `tb_organizations.id` ↔ `Tenants.TenantId` 매핑 (시드 시 1:1 import).
- career `department_id`는 `Tenants` 하위 sub-org 또는 자체 유지 (미정 — Q1 §21).

---

## 5. 데이터 아키텍처

### 5.1 PostgreSQL 단일 인스턴스

**연결 정보**:
- Host: `192.168.10.39`
- Port: `5440`
- DB: `AGENT_HUB`
- User: `AGENT_HUB`
- Password: `idino!@#$` (**환경변수/Vault, .gitignore 강제**)
- Search Path: schema별 dynamic (각 시스템이 자기 schema만)

**Extensions** (DB 단위 1회):
- `pgvector` — 벡터 임베딩 (career, AIAgentManagement 사용)
- `uuid-ossp` — UUID 생성
- `pg_trgm` — 한국어 부분일치 검색 보조
- `pgcrypto` — `gen_random_uuid()` (NEWID 대체)

### 5.2 Schema 정책

| Schema | 소유 시스템 | 표 prefix | 마이그레이션 도구 |
|---|---|---|---|
| `AIAgentManagement` | agenthub | (PascalCase, EF naming) | EF Core 8 (Npgsql) |
| `document_utilization` | docutil | `tb_*` | Alembic |
| `idino_career` | career | `tb_*` | SQL files (`database/01_*.sql~60_*.sql`) |
| `hangfire` | agenthub | (Hangfire 자체) | Hangfire.PostgreSql 자동 |
| `nexus` | nexus (선택, R5) | `tb_*` | DDL in `core/rag/knowledge_store.py` |

**GRANT 정책** (R29):
- DB user `AGENT_HUB`는 모든 schema 소유.
- 향후 schema별 user 분리 가능성 보존 (Phase 9+).

### 5.3 데이터 타입 변환 (MSSQL → PostgreSQL)

| 영역 | MSSQL | PostgreSQL | 비고 |
|---|---|---|---|
| 문자열 | `nvarchar(N)` | `varchar(N)` 또는 `text` | EF 자동 매핑 |
| 시간 | `datetime2` | `timestamptz` | UTC 통일 (M13) |
| boolean | `bit` | `boolean` | EF 자동 |
| 정수 자동증가 | `IDENTITY` | `GENERATED BY DEFAULT AS IDENTITY` | EF 자동 |
| Money | `decimal(10,4)` | `numeric(10,4)` | 호환 |
| JSON 문자열 | `nvarchar(MAX)` (수동 직렬화) | `jsonb` (네이티브) | **권장 전환**: `Agent.AllowedEmbedDomains`, `WorkflowNode.Connections`, `Presentation.Slides`, `Agent.RoutingPolicyJson` 등 |
| 임베딩 | `nvarchar(MAX)` JSON | `vector(1536)` | **필수 전환**: `DocumentChunk.Embedding`, career `tb_course/tb_program/tb_success_pattern.embedding` |
| GUID 디폴트 | `NEWID()` | `gen_random_uuid()` (pgcrypto) | |
| Cascade Delete | 동일 | 동일 | ApiServices→Agents는 Restrict로 강등 (R12) |

### 5.4 Qdrant 정책

- **단일 클러스터, 단일 collection `documents`** — DocUtil 전용.
- AgentHub의 자체 KB(`KnowledgeBaseDocument`/`DocumentChunk`)는 deprecate, 데이터 이전(Phase 6).
- 임베딩 차원 통일: **1536D 표준** (`text-embedding-3-small`).
  - DocUtil의 vLLM Qwen3-Embedding 2048D 분기는 **제거 또는 별도 collection으로 분리** (R17).
- payload 스키마: `document_id, organization_id, chunk_index, chunk_type, visibility, department_id, project_id`.

### 5.5 Redis Key Prefix

| 시스템 | Prefix | 예시 |
|---|---|---|
| AgentHub | `agenthub:` | `agenthub:chat:resp:{agentId}:{model}:{hash}` |
| DocUtil | `docutil:` | `docutil:auth:otp:{user_id}` |
| career | `career:` | `career:auth:session:{user_id}` |
| Nexus | `nexus:` 또는 `session:` | `session:{session_id}:context` |

DB 분리도 가능: AgentHub=db0, DocUtil=db1, career=db2, Nexus=db6 (현재 nexus는 db=6 사용).

### 5.6 데이터 마이그레이션 단계 (Phase 2~4)

1. **AgentHub MSSQL → PostgreSQL** (Phase 3):
   - `dotnet ef migrations add Init -- --provider Npgsql` (PG용 baseline 신규 작성, 구 SqlServer migration 폐기).
   - `bcp` MSSQL export → CSV → `COPY` PostgreSQL import 또는 pgloader.
   - JSON nvarchar(MAX) 컬럼은 `text` → `jsonb` 변환 + 인덱싱.
   - 임베딩 컬럼 `vector(1536)` 신설 + 백필 + 구 컬럼 drop.
2. **DocUtil PG (단일) → AGENT_HUB.document_utilization schema** (Phase 4):
   - DocUtil은 이미 PG라 schema 이전만: `pg_dump --schema=public` → 신규 schema rename.
   - Alembic head 재정렬 (009 기준 → AGENT_HUB DB에 새 head 생성).
3. **career PG → AGENT_HUB.idino_career schema** (Phase 4):
   - `pg_dump --schema=idino_career` → `pg_restore`.
   - audit 컬럼 보존, FK 재설정.
   - pgvector extension 활성화 + 임베딩 컬럼 백필.
4. **Nexus** (Phase 4): 별도 유지(R5).

### 5.7 시드 데이터 (Phase 2)

`infra/db/init.sql`:
```sql
CREATE USER "AGENT_HUB" WITH PASSWORD :'idino_pw';
CREATE DATABASE "AGENT_HUB" OWNER "AGENT_HUB" ENCODING 'UTF8' TEMPLATE template0;
\c AGENT_HUB
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA "AIAgentManagement"   AUTHORIZATION "AGENT_HUB";
CREATE SCHEMA "document_utilization" AUTHORIZATION "AGENT_HUB";
CREATE SCHEMA "idino_career"         AUTHORIZATION "AGENT_HUB";
CREATE SCHEMA "hangfire"             AUTHORIZATION "AGENT_HUB";
```

AgentHub `DatabaseInitializer.cs` (866 LOC) → idempotent 시드 재작성:
- `Roles`: SuperAdmin / Admin / Developer / User / Student / Advisor (career RBAC 매핑) (**신규**)
- `ApiServices`: `openai, claude, gemini, vertex, mistral, perplexity, copilot, azureopenai, tavily, nexus`(신규), `dalle, imagen4, flux2, gen4-image, gen4-video, veo, openai-video`
- `ApiServiceModels`: `gpt-4o-mini, claude-sonnet-4-20250514, gemini-2.0-flash, nexus-phase3, qwen3.5-27b, exaone-7.8b, text-embedding-3-small, multilingual-e5-large` 등
- `Agents` 시드 (career 8개 + docutil 4개 + 일반 1개 = 13개) (§8.4)

---

## 6. API 명세

### 6.1 게이트웨이 라우팅 (AgentHub :5001)

| 경로 | 인증 | Rate Limit | 책임 |
|---|---|---|---|
| `/api/auth/*` | Anonymous (login/register), Authorize (logout/refresh) | — | JWT 발급 / RefreshToken 회전 |
| `/api/admin/*` | JWT (Admin/SuperAdmin) | per-user 60/min | 운영자 콘솔 |
| `/api/admin/kb/*` | JWT (Admin) | per-user 60/min | **DocUtil BFF** (문서/검색범위/템플릿/평가) (**신규**) |
| `/api/admin/users/*` | JWT (Admin) | per-user 60/min | 사용자 관리 (DocUtil/career 통합) |
| `/api/agents/*` | JWT | per-user 60/min | Agent CRUD (5단계 위저드 + **편집 모드**) |
| `/api/chat/*` | JWT | per-user 60/min | 단일/멀티 채팅 |
| `/api/chat/public/{code}/*` | Anonymous + 도메인 화이트리스트 | ip-guest 20/min | 게스트 임베드 |
| `/v1/chat/completions` | API Key | ip-openai 30/min | **OpenAI 호환 단일 진입점** (External 사용) |
| `/v1/chat/completions` (stream) | API Key | ip-openai 30/min | **진짜 SSE** (C9 해결) |
| `/v1/embeddings` | API Key | ip-openai 30/min | (**신규**) 통합 임베딩 게이트웨이 |
| `/v1/images/generations` | API Key | ip-openai 30/min | DALL-E/Imagen/Flux2 통합 |
| `/v1/models` | API Key | ip-openai 30/min | AgentHub Agent 목록을 OpenAI 모델 형식으로 |
| `/api/nexus/*` (옵션) | JWT (Admin) | per-user 60/min | Nexus 헬스/메트릭 조회용 BFF (**신규**) |
| `/hubs/chat`, `/hubs/notification` | JWT `[Authorize]` (**C8 해결**) | — | SignalR |
| `/hangfire` | HangfireAuthorizationFilter (Admin) | — | 잡 대시보드 |
| `/health`, `/metrics` | Anonymous | — | 헬스/메트릭 |
| `/swagger` | Dev only | — | API 문서 |

### 6.2 OpenAI 호환 API 명세 (`/v1/chat/completions`)

**요청 (snake_case)**:
```json
{
  "model": "career-coaching",       // AgentCode (모델명 = Agent 식별자)
  "messages": [
    {"role": "user", "content": "..."}
  ],
  "stream": true,
  "temperature": 0.7,
  "max_tokens": 2000,
  "response_format": {"type": "json_schema", "json_schema": {...}},  // 선택, Agent 정의 우선
  "tools": [...],                   // 선택, Agent 정의 우선
  "metadata": {                     // (신규) AgentHub 확장
    "session_id": "uuid",           // ChatConversation 1:1 매핑
    "tenant_id": "school-a",        // multi-tenant
    "user_id": "external-uid",      // 외부 시스템 사용자 식별
    "consumer_system": "career-coaching"  // 호출 출처
  }
}
```

**응답 — 비스트리밍**:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1730000000,
  "model": "career-coaching",
  "choices": [{"index": 0, "message": {...}, "finish_reason": "stop"}],
  "usage": {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}
}
```

**응답 — 스트리밍 (진짜 SSE, C9 해결)**:
```
data: {"id":"...","object":"chat.completion.chunk","created":...,"model":"career-coaching","choices":[{"index":0,"delta":{"role":"assistant"}}]}

data: {"id":"...","object":"chat.completion.chunk","created":...,"model":"career-coaching","choices":[{"index":0,"delta":{"content":"안녕"}}]}

data: {"id":"...","object":"chat.completion.chunk","created":...,"model":"career-coaching","choices":[{"index":0,"delta":{"content":"하세요"}}]}

data: {"id":"...","object":"chat.completion.chunk","created":...,"model":"career-coaching","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**구현 위치**:
- `agenthub/Controllers/OpenAICompatController.cs` — 진짜 SSE 재구현 (현재 `:138` 가짜 SSE 제거)
- `agenthub/Services/AiProxyService.cs` — `SendChatMessageStreamAsync` 시그니처 `IAsyncEnumerable<ChatChunk>` 반환 + ApiKeyPool/Cooldown 적용 (H5 해결)

### 6.3 AgentHub → Nexus 클라이언트 명세 (옵션 B)

`agenthub/Services/NexusClient.cs` (**신규**, 약 200 LOC):

| 메서드 | 엔드포인트 | 사용 |
|---|---|---|
| `CallAsync(messages, sessionId, tenantId, model, ct)` | `POST {NexusBase}/v1/chat` | 비스트리밍 |
| `StreamAsync(messages, sessionId, tenantId, model, ct)` | `POST {NexusBase}/v1/chat/stream` (SSE) | 스트리밍 |
| `GetHealthAsync(ct)` | `GET {NexusBase}/health` | 헬스체크 |
| `GetMetricsAsync(ct)` | `GET {NexusBase}/metrics` | 메트릭 |
| `EmbedAsync(texts, ct)` (선택) | `POST {NexusBase}/v1/embeddings` | (Nexus 멀티링구얼-e5) |

**헤더**:
- `X-Tenant-ID: {tenant}` — 명시
- `Authorization: Bearer {SharedSecret}` — AgentHub-Nexus 공유 시크릿 (**신규**, R10 완화)
- `Content-Type: application/json`

**SSE 프레임 변환**:
- `text_delta` → AgentHub의 OpenAI 호환 `delta.content`
- `tool_use` → AgentHub `tool_calls` (선택, ConsumerSystem이 허용 시)
- `usage_update` → `ApiUsage.PromptTokens / CompletionTokens` 기록
- `message_stop` → `finish_reason`
- `error` → AgentHub fallback 트리거 (External LLM 폴백)

### 6.4 AgentHub → DocUtil BFF 명세

`agenthub/Services/DocUtilClient.cs` (**신규**):

| 메서드 | DocUtil 엔드포인트 | 용도 |
|---|---|---|
| `UploadDocumentAsync(file, scopeId, ct)` | `POST /api/v1/documents/upload` (multipart) | 운영자 KB 등록 |
| `BulkUploadAsync(files, scopeId, ct)` | `POST /api/v1/documents/bulk-upload` | 일괄 |
| `GetUploadProgressAsync(jobId)` (SSE) | `GET /api/v1/documents/upload-progress/{jobId}` | 진척률 |
| `ListDocumentsAsync(...)` | `GET /api/v1/documents` | 카탈로그 |
| `GetDocumentAsync(id, ct)` | `GET /api/v1/documents/{id}` | 상세 |
| `DeleteDocumentAsync(id, ct)` | `DELETE /api/v1/documents/{id}` | 삭제 |
| `SearchHybridAsync(query, scopeId, maxResults, ct)` | `POST /api/v1/search/hybrid` | **RAG 컨텍스트 검색** (LLM 미포함, 순환 호출 방지 P8) |
| `ListSearchScopesAsync` / `CreateScopeAsync` / `UpdateScopeAsync` / `DeleteScopeAsync` | `/api/v1/search-scopes/*` | 검색 범위 CRUD |
| `RunEvaluationAsync(scopeId, ct)` | `POST /api/v1/evaluation/runs` | RAGAS 품질 평가 |

**인증**: AgentHub-DocUtil 공유 시크릿 (`X-Internal-Auth: Bearer ...`) 또는 mTLS.

### 6.5 career → AgentHub 사용 패턴

career의 ai-service를 **제거** 후, 다른 MS는 직접 AgentHub 호출:

```python
# career/services/coaching-service/.../coaching_service.py 변경 후
from career.shared.agenthub_client import AgentHubClient

agenthub = AgentHubClient(base_url=AGENTHUB_URL, api_key=AGENTHUB_API_KEY)

response = await agenthub.chat_completion(
    model="career-chatbot",  # AgentCode
    messages=[{"role": "user", "content": query}],
    stream=True,
    metadata={
        "session_id": str(coaching_session_id),
        "tenant_id": tenant_id,
        "user_id": str(student_id),
        "consumer_system": "career-coaching"
    }
)
```

**`career/shared/agenthub_client.py`** (**신규**, 약 150 LOC) — 모든 career MS가 import.

### 6.6 DocUtil → AgentHub 사용 패턴

`docutil/backend/integrations/llm/factory.py:create_llm_client` 단일 함수만 변경 (DocUtil 분석 보고서 §13.2):

```python
# Before
def create_llm_client(provider: str) -> BaseLLMClient:
    if provider == "openai": return OpenAIClient(...)
    elif provider == "anthropic": return ClaudeClient(...)
    # ...

# After
def create_llm_client(provider: str = "agenthub", task: str = "chat") -> BaseLLMClient:
    return AgentHubProxyClient(
        base_url=settings.agenthub_url,
        api_key=settings.agenthub_api_key,
        agent_code=settings.agent_code_for_task(task)  # task → AgentCode 매핑
    )
```

DocUtil의 `chat_llm_provider`, `report_llm_provider`, `template_llm_provider` env는 → `chat_agent_code`, `report_agent_code` 등으로 의미 변경.

---

## 7. 인증 / 권한 / 멀티테넌시

### 7.1 JWT 표준화 (R5, R15)

**알고리즘**: HS256 단일 (RSA RS256은 Phase 5+ 도입). DocUtil의 RS256/HS256 fallback 제거.

**Claims 표준 (모든 시스템 공통)**:
```json
{
  "sub": "user_id (int)",
  "iss": "agenthub.idino.co.kr",
  "aud": ["agenthub", "docutil", "career"],
  "exp": 1730000000,
  "iat": 1730000000,
  "jti": "uuid (RefreshToken 쌍 식별)",
  "tenant_id": "school-a",
  "organization_id": "uuid (DocUtil 호환)",
  "department_id": "career 호환",
  "role": "Admin | Developer | User | Student | Advisor | DepartmentAdmin | CareerCenterAdmin | SystemAdmin",
  "role_level": 1-5,
  "consumer_system": "agenthub-admin | docutil-user | career-student | embed-public"
}
```

**발급/검증**:
- 발급: AgentHub `IJwtService` 단일 권위.
- 검증:
  - AgentHub: `Microsoft.AspNetCore.Authentication.JwtBearer`
  - DocUtil: `python-jose` + 공유 secret env (`JWT_SHARED_SECRET`)
  - career: 동일 (`shared/common/auth.py:JWTBearer`)
- **시크릿 공유 방식**: Vault/환경변수, .env에 `JWT_SHARED_SECRET=<256bit hex>` (R26).

### 7.2 API Key (외부 시스템 → AgentHub)

`ak-{base64-22}` 형식 유지. 중요 변경:
- `KeyHash UNIQUE` SHA-256 인덱스 (C3 해결)
- AES-GCM + per-record random IV (C1, C2 해결)
- 회전 (`PreviousKeyHash`, 24h 유예) (R7 해결)
- `Scopes`: `chat,stream,info,usage,admin,kb,embed`
- `ConsumerSystem` enum 검증

**발급 단위**:
- 1 키 = 1 AgentId (특정 Agent 전용) 또는 1 Tenant (멀티 Agent 공유)
- 외부 시스템마다 별도 키 발급:
  - `docutil-user` 키 → DocUtil이 사용자 챗 호출 시 사용
  - `career-coaching` 키 → career 코칭 MS가 사용
  - `external-sdk` 키 → 외부 OpenAI SDK 호환 사용

### 7.3 RBAC 통합

| AgentHub Role | career role_level | DocUtil role | 권한 범위 |
|---|---|---|---|
| `SuperAdmin` | 5 (SystemAdmin) | `super_admin` | 시스템 전역, DB 백업, 시크릿 |
| `Admin` | 4 (CareerCenterAdmin) | `admin`, `org_admin` | 운영자 콘솔 모든 기능 |
| `Developer` | — | `manager`, `editor` | Agent/Tool 빌더 |
| `Advisor` | 2 (Advisor) | `manager` (career 한정) | 학생 코호트 개입 |
| `DepartmentAdmin` | 3 | `org_admin` (department) | 부서 단위 관리 |
| `User` | — | `member` | 자기 자원 |
| `Student` | 1 (Student) | — | career 학생 포털 |
| (게스트) | — | `viewer` | 공개 채팅 |

**시드 위치**: AgentHub `Data/DatabaseInitializer.cs:Seed`Roles + `UserRoles` 매핑 시 career `tb_user.role_level` → AgentHub Role enum 변환 함수 추가 (Phase 4).

### 7.4 Multi-Tenant

- `Tenants` 테이블 (§4.5)이 단일 권위.
- DocUtil `tb_organizations` → `Tenants`와 1:1 매핑 (시드 시 `default` slug 1개).
- career `department_id` → `Tenants.SubOrgId` 또는 별도 `Departments` 테이블 (Q1 결정 필요).
- 모든 핵심 쿼리는 `WHERE tenant_id = current_user.tenant_id` 강제 (DocUtil의 기존 정책 유지).

### 7.5 6단계 Visibility (DocUtil 보존)

DocUtil의 `Document.visibility` (`public / all_departments / department_only / project_only / confidential / hidden`) **그대로 유지**.
- AgentHub Vue Admin은 BFF로 호출 시 visibility CRUD 필요.
- AgentHub는 자체 visibility 모델 미보유 — DocUtil 정책에 위임.

---

## 8. AI 호출 인벤토리 + Agent 카탈로그

### 8.1 인벤토리 요약

| 시스템 | 직접 LLM 호출 위치 수 | 임베딩 호출 | 이미지 생성 | 위임 형태 |
|---|---|---|---|---|
| AgentHub | (자체 게이트웨이) | 자체 (`text-embedding-3-small`) | DALL-E/Imagen/Flux2 | (게이트웨이) |
| DocUtil | LLM 1진입점 (`integrations/llm/factory.py`) + P1 위반 2곳 (`graph_rag.py:105`, `image_generation/service.py:189`) | `workers/embedding_generator.py:148` (1536D vs 2048D 분기) | DALL-E 3 (`image_generation/service.py:189`) | factory만 교체 → 자동 위임 |
| career | **11곳 직접 호출** (ai-service 9 + simulation-service 2) | `embedding_service.py:49` (1536D, 동일) | (없음) | ai-service 제거 + 다른 MS는 AgentHub 호출 |
| Nexus | (자체 vLLM 서빙) | 자체 (multilingual-e5-large 1024D) | (없음) | (Internal Provider) |

### 8.2 AgentHub Agent 카탈로그 (시드, Phase 5+)

총 13개 시드 Agent (career 8 + docutil 4 + 일반 1).

#### 8.2.1 career용 Agent (8개)

| AgentCode | DisplayName | DefaultModel | LlmRouting | EnableRag | ResponseFormat | 사용처 |
|---|---|---|---|---|---|---|
| `career-actionboard-orchestrator` | 진로 액션보드 오케스트레이터 | gpt-4o-mini | External | × | (Tool Calling) | ai-service `/ai/recommendations/tools` |
| `career-rag-actionboard` | RAG 액션보드 | gpt-4o-mini | External | ✓ | JSON_SCHEMA_ACTIONBOARD | ai-service `/ai/recommendations/rag` |
| `career-competency-analyzer` | 역량 분석가 | gpt-4o-mini | External | × | (분석 JSON) | competency-service, frontend |
| `career-action-recommender` | 액션 추천 | gpt-4o-mini | External | × | (액션 JSON) | ai-service `/ai/actions/{id}` |
| `career-chatbot` | 진로 챗봇 | gpt-4o-mini | Hybrid | × | × | coaching-service, frontend chat |
| `career-semester-planner` | 학기 플래너 | gpt-4o-mini | External | × | (목표 JSON) | ai-service `/ai/sprint/{id}` |
| `career-simulation-suggester` | 시뮬레이션 추천 | gpt-4o-mini | External | × | (4 시나리오 JSON) | simulation-service |
| `career-simulation-analyzer` | 시뮬레이션 분석 | gpt-4o-mini | External | × | (종합점수 JSON) | simulation-service |

**SystemPrompt 출처**: `career/services/ai-service/app/services/llm_service.py` 의 11곳 prompt를 추출하여 AgentHub `Agent.SystemPrompt` DB로 이전. 코드에서 prompt 제거.

#### 8.2.2 DocUtil용 Agent (4개)

| AgentCode | DisplayName | DefaultModel | LlmRouting | EnableRag | ResponseFormat | 사용처 |
|---|---|---|---|---|---|---|
| `docutil-rag-chat` | 문서 RAG 챗봇 | gpt-4o | Hybrid | ✓ (DocUtil 위임) | × | DocUtil `chat/service.py` |
| `docutil-report-generator` | 보고서 생성 | gpt-4o | External | ✓ | DocumentSchema | DocUtil `documents_v2/service.py` |
| `docutil-proposal-generator` | 제안서 생성 | gpt-4o | External | ✓ | DocumentSchema | DocUtil `documents_v2/service.py` |
| `docutil-meeting-minutes` | 회의록 정제 | gpt-4o | External | ✓ | (특화 schema) | DocUtil S6 작업 |

#### 8.2.3 공용 (1개)

| AgentCode | DisplayName | 비고 |
|---|---|---|
| `agenthub-default-assistant` | 기본 어시스턴트 | embed-public, external-sdk 디폴트 |

### 8.3 Tool 카탈로그 (career의 4 Tool 이전)

career `tool_definitions.py`의 4개 Tool을 AgentHub `Tools` 테이블로 이전:

| ToolCode | Type | Endpoint | 용도 |
|---|---|---|---|
| `get_student_profile` | API | `http://student-service:8002/students/{id}` | 학생 프로필 |
| `get_competency_scores` | API | `http://competency-service:8003/competencies/{student_id}` | 역량 점수 |
| `search_alumni_patterns` | API | `http://alumni-service:8005/patterns/search` | 동문 패턴 |
| `check_constraints` | API | `http://student-service:8002/constraints` | 학사 제약 |

**위치**: AgentHub `Services/ApiToolExecutor.cs` 가 실행. JWT/API Key는 AgentHub가 자체 발급 후 첨부.

### 8.4 ResponseFormat 신설 (R3 완화)

AgentHub `Agent` 엔티티에 `ResponseFormat jsonb null` 컬럼 추가 (§4.1.1).
- OpenAI Structured Outputs (`response_format: {type: "json_schema", strict: true}`) 정의 저장.
- **OpenAI 전용** — Claude/Gemini 위임 시 fallback 정책:
  - Claude: Tool Use 변환 (DocUtil의 `claude_client.py:247` 패턴 참조)
  - Gemini: Discriminated Union 평탄화 (`gemini_client.py:143` 패턴 참조)
- `AiProxyService`의 provider별 분기에서 `Agent.ResponseFormat`을 변환.

---

## 9. RAG 통합 — DocUtil 단일 권위

### 9.1 권위 매트릭스

| 자원 | 단일 권위 | 비고 |
|---|---|---|
| 문서 원본 (PDF/DOCX/PPTX/HWP/HWPX/이미지) | DocUtil MinIO | |
| 문서 메타 | DocUtil `tb_documents` | |
| 청크 | DocUtil `tb_document_chunks` | |
| 벡터 (dense + sparse) | DocUtil Qdrant `documents` collection | |
| 검색 (hybrid + rerank) | DocUtil `search/service.py` | |
| 문서 생성 (DocumentSchema, PPTX/DOCX) | DocUtil `documents_v2/service.py` | |
| 검색 범위 / Visibility | DocUtil | |
| 평가 (RAGAS) | DocUtil | |
| 운영자 KB UI (BFF) | AgentHub Vue Admin | |
| LLM 합성 (검색 결과 → 답변) | **AgentHub** (P8 순환 호출 방지) | |
| 임베딩 차원 | 1536D 표준 | OpenAI `text-embedding-3-small` |

### 9.2 AgentHub 자체 KB Deprecate 절차 (Phase 6)

1. AgentHub `KnowledgeBaseDocument` / `DocumentChunk` / `AgentDocument` 테이블 데이터 → DocUtil `tb_documents` / `tb_document_chunks` / `tb_search_scopes`로 이전.
   - 임베딩 차원 통일 (1536D 동일이라 변환 불필요).
   - visibility 매핑: AgentHub는 visibility 미보유 → 기본 `department_only` + 운영자 검수 (R20).
2. AgentHub `Models/KnowledgeBaseDocument.cs` 등 코드 → `[Obsolete]` 마킹 + 신규 INSERT 차단 (410 Gone).
3. `AgentHub Agent.KnowledgeBaseSource = DocUtil` (default 변경).
4. `AgentHub Agent.KnowledgeBaseRef`에 DocUtil scope_id 또는 collection 식별자 저장.
5. `RagService.RetrieveAsync` 내부 → `DocUtilClient.SearchHybridAsync` 호출로 교체.
6. `EmbeddingService` (SIMD cosine) 제거 (DocUtil로 흡수).
7. 임베딩 워커 `workers/embedding_generator.py:148`의 1536D vs 2048D 분기 제거 → 1536D 단일.

### 9.3 순환 호출 방지

```
[NG] AgentHub Chat → DocUtil /search/chatbot (DocUtil이 LLM 합성) → DocUtil이 AgentHub 호출 → 무한 루프

[OK] AgentHub Chat → DocUtil /search/hybrid (컨텍스트만) → AgentHub가 LLM 합성 → 사용자
```

**규칙**: DocUtil의 `chat/service.py`, `search/chatbot/qa` 등 LLM 호출이 포함된 엔드포인트는 **AgentHub BFF에서 호출 금지**. 컨텍스트 조회는 `/search/hybrid` 만 사용.

### 9.4 임베딩 정책

- **1536D 표준** (OpenAI `text-embedding-3-small`).
- AgentHub `/v1/embeddings` 게이트웨이 신설 (§6.1).
- DocUtil/career의 임베딩 호출 → AgentHub로 위임.
- Nexus의 1024D (multilingual-e5-large)는 **별도 Qdrant collection 또는 별도 DB 인덱스**로 격리 — DocUtil collection과 혼용 금지 (R17).
- vLLM Qwen3-Embedding 8B (2048D)는 DocUtil의 옵션 분기 → 통합 시점에 제거 결정 또는 별도 collection.

---

## 10. LLM 라우팅 — External/Internal/Hybrid

### 10.1 모드 정의

- **External**: External LLM(OpenAI/Claude/...)만 사용. 외부망 환경.
- **Internal**: Nexus만 사용. 내부망/에어갭 환경.
- **Hybrid**: 정책 기반 동적 분기 (`RoutingPolicyJson`).

### 10.2 RoutingPolicyJson 스키마

```json
{
  "default": "external",
  "fallbacks": ["internal/nexus-phase3"],
  "rules": [
    {
      "if": {"piiDetected": true},
      "use": "internal",
      "model": "nexus-phase3"
    },
    {
      "if": {"dataLabel": "confidential"},
      "use": "internal"
    },
    {
      "if": {"dataLabel": "public"},
      "use": "external"
    },
    {
      "if": {"capability": "vision"},
      "use": "external",
      "model": "gpt-4o"
    },
    {
      "if": {"capability": "longContext", "minTokens": 32000},
      "use": "external",
      "model": "claude-sonnet-4"
    },
    {
      "if": {"costPerRequest": {"$gt": 0.10}},
      "use": "internal"
    },
    {
      "if": {"contextLength": {"$gt": 8192}},
      "use": "external"
    }
  ],
  "providerOverrides": {
    "external": {
      "primary": "openai/gpt-4o-mini",
      "fallbacks": ["anthropic/claude-haiku", "gemini/flash"]
    }
  }
}
```

### 10.3 결정 엔진 (`HybridRouter`)

`agenthub/Services/HybridRouter.cs` (**신규**):

```csharp
public interface IHybridRouter
{
    Task<ResolvedRoute> ResolveAsync(Agent agent, ChatRequest request, CancellationToken ct);
}

public record ResolvedRoute(string ServiceCode, string Model, string Tier);
```

처리 단계:
1. Agent.LlmRouting이 External/Internal이면 즉시 반환.
2. Hybrid이면 `RoutingPolicyJson` 파싱.
3. 입력 검사: PII 감지 / dataLabel / 토큰 추정 / capability / cost 추정.
4. 각 rule의 if 조건 평가 → 첫 매치를 선택.
5. 매치 없으면 default 사용.
6. 선택한 ServiceCode가 Cooldown 중이면 다음 fallback.

### 10.4 PII 처리 (Internal 강제)

- `IPiiDetectionService.DetectAsync(text)` → 한국어 PII 8종 (주민번호, 핸드폰, 카드, 이메일, 주소, 계좌, 운전면허, 여권).
- 검출 시 `Agent.PiiMode`:
  - `block` → 400 BadRequest.
  - `mask` → 마스킹 후 진행.
- Hybrid 모드 + PII 검출 시 **자동으로 Internal(Nexus) 강제** (외부 LLM 누수 방지).

### 10.5 라우팅 진입 위치

```
Controller → ChatService → IHybridRouter.ResolveAsync(agent, request)
   → IAiProxyService.SendChatAsync(resolvedRoute, messages, ct)
       → switch(resolvedRoute.ServiceCode)
           "openai|claude|gemini|...": External provider 호출 (기존)
           "nexus": INexusClient.CallAsync (신규)
   → IApiKeyPoolService.GetNextKey + Cooldown
   → 응답 → IPiiDetectionService.MaskAsync (출력 보호) → Client
```

기존의 `ChatService.GetDefaultFallbackModel` 12종 매핑은 `LlmRouting` 정책으로 흡수 (코드 단순화).

---

## 11. 운영자 콘솔 — AgentHub Vue + BFF

### 11.1 메뉴 구조 (Vue Admin)

```
/admin
├── /dashboard               기존 + DocUtil/career 메트릭 흡수
├── /agents                  Agent CRUD (+ 편집 모드, ResponseFormat)
├── /tools                   Tool 빌더 (career 4 Tool 이전)
├── /workflows               기존
├── /knowledge               (신규 BFF) DocUtil 문서/검색범위/템플릿/평가
│   ├── /documents           DocUtil tb_documents 카탈로그
│   ├── /upload              운영자 KB 등록
│   ├── /scopes              검색 범위 CRUD
│   ├── /templates           Mode B 디자이너 (S4)
│   ├── /evaluation          RAGAS 결과
│   └── /test                검색 테스트
├── /api-keys                ApiKey 발급/회전 (DocUtil ApiKey 흡수)
├── /quotas                  ApiQuota (DocUtil tb_organization_quotas 흡수)
├── /usage                   사용량/비용 분석
├── /users                   사용자 관리 (DocUtil/career 통합)
├── /tenants                 (신규) Tenant/Organization 관리
├── /content                 ExamplePrompt / FAQ / Tutorial
├── /system                  Settings, BannedWord, Hangfire 링크
└── /providers               ApiServices/ApiServiceModels
```

### 11.2 BFF 패턴

AgentHub Vue → AgentHub `/api/admin/kb/*` → DocUtilClient → DocUtil API.

이점:
- 운영자는 단일 JWT로 모든 운영 자원 접근.
- DocUtil 외부 노출 차단 가능 (LAN/private network).
- ActivityLog가 모든 운영 행위를 단일 감사 로그에 기록.
- Vue 컴포넌트는 `@/services/api`(axios) 그대로 사용 (raw axios 4건 제거 — H 부채).

### 11.3 DocUtil Frontend 정리 (Phase 6)

DocUtil `frontend/(admin)/*` 라우트 중:
- **삭제**: dashboard, admin-accounts, departments, agents, api-keys, quotas, help, quick-guide, settings (AgentHub로 이관).
- **유지**: documents, search-scopes, search-test, evaluation, templates, template-designer (도메인 전용).
- **사용자 라우트** `(user)/*`, `(auth)/*`는 그대로.

운영자가 DocUtil 사용자 화면을 보려면 AgentHub Vue Admin → "DocUtil 운영자 페이지" 링크(iframe 또는 새 탭).

### 11.4 career Frontend 정리 (Phase 6 일부)

career frontend `(dashboard)` 하위는 기능별로 검토:
- AI 설정 관련 (Agent prompt 편집 등)은 career에 미존재 → AgentHub Admin이 단일 권위.
- 학생/교사/어드바이저 도메인 화면은 career 자체 유지.
- 운영자가 career 학생 데이터를 보려면 career frontend 직접 접속 (도메인 분리).

---

## 12. 마이그레이션 전략 (Phase 0~8)

### 12.1 Phase 개요

| Phase | 내용 | 산출물 | 의존 |
|---|---|---|---|
| **0** | 작업공간 셋업 | `IDINO_Agent_Hub/` + 4 서브프로젝트 + init | (시작) |
| **1** | AI 호출 인벤토리 | `docs/AI_INVENTORY.md` (전수 grep) | 0 |
| **2** | AGENT_HUB DB 설계 + 생성 | `infra/db/init.sql`, `docs/DB_MIGRATION.md` | 1 |
| **3** | AgentHub MSSQL → PostgreSQL | EF baseline, 데이터 이전 스크립트 | 2 |
| **4** | DocUtil/career → AGENT_HUB 통합 | schema 이전, FK 재설정, pgvector | 3 |
| **5** | AgentHub에 Nexus provider 추가 | `Services/NexusClient.cs`, `AiProxyService` 분기, `Agent.LlmRouting` | 3 |
| **6** | DocUtil 운영자 → AgentHub 흡수 | Vue Admin BFF, DocUtil admin 정리 | 5 |
| **7** | DocUtil/career AI 호출 → AgentHub 위임 | factory 교체, Agent 시드, API Key 발급 | 5, 6 |
| **8** | (보류) Vue → Next.js 점진 이행 | 별도 트랙 | — |

각 Phase는 사용자 승인 후 시작. Phase 내부에서 발견된 추가 작업은 사용자 보고 후 진행. (`development-workflow.md` 규칙)

### 12.2 Phase 0: 작업공간 셋업 (완료)

- 루트 `.gitignore` (다국어 + 시크릿 제외)
- 루트 `README.md`, `CLAUDE.md`
- `.claude/rules/` 6개
- `docs/ARCHITECTURE.md`, `docs/AI_INVENTORY.md`
- `git init` + remote `origin` (https://github.com/CherryCocacola/IDINO_Agent_Hub.git)
- 초기 commit `1da04ab` (1,921 files)
- 4 서브프로젝트 복사 (agenthub/docutil/career/nexus)
- 시크릿 파일 .gitignore 강제 (nexus_config.yaml, .env*, appsettings.*.json, ssl/)
- `user_mig/source_*.md` 4개 분석 보고서
- 본 `user_mig/TECHSPEC.md`
- `user_mig/progress.md`

### 12.3 Phase 1: AI 호출 인벤토리

`docs/AI_INVENTORY.md` 작성 (Phase 0의 템플릿 → 실측 데이터로 채움):
- 각 서브프로젝트 grep으로 전수 조사 (`from openai`, `from anthropic`, `httpx.post.*api.openai`, `OpenAI(`, `ChatOpenAI`)
- 우선순위(P0~P3) 부여
- Provider/Model 통계
- 민감도(PII) 분류
- 목표 Agent 매핑 초안

**예상 결과**:
- agenthub: 자체 게이트웨이 분기 9곳 (openai/claude/gemini/perplexity/mistral/copilot/azureopenai/vertex/이미지)
- docutil: factory 1진입점 + P1 위반 2곳 + 임베딩 1곳 + 이미지 1곳
- career: 11곳 직접 + 임베딩 1곳 + 다른 MS 위임 4곳
- nexus: 외부 호출 없음 (자체 vLLM)

### 12.4 Phase 2: DB 설계 + 생성

**작업**:
1. `infra/db/init.sql` 작성 (§5.7).
2. `192.168.10.39:5440`에 `psql` 접속하여 실행 (사용자 확인 후).
3. 4개 schema 생성, extension 활성화, GRANT 적용.
4. `docs/DB_MIGRATION.md`에 모든 변경 기록.
5. 헬스체크: 각 schema에 빈 테이블 생성/조회로 검증.

**위험**:
- 기존 `nexus` DB와 별개 인스턴스인지 확인 (현재는 동일 192.168.10.39:5440의 `nexus` DB와 혼재). `AGENT_HUB` DB는 신규 생성.

### 12.5 Phase 3: AgentHub MSSQL → PostgreSQL

**작업**:
1. AgentHub 코드 변경:
   - `Microsoft.EntityFrameworkCore.SqlServer` → `Npgsql.EntityFrameworkCore.PostgreSQL`
   - `Hangfire.SqlServer` → `Hangfire.PostgreSql`
   - `Program.cs`: `UseSqlServer` → `UseNpgsql`, ConnectionString 형식 변경
   - `appsettings.Development.json`: 연결 정보 (시크릿 env)
   - `DbContext.OnModelCreating`: `HasDefaultSchema("AIAgentManagement")` 추가
   - JSON 컬럼 → `jsonb` 매핑 변경
2. **EF baseline 마이그레이션 신규 작성** (C7 해결):
   - 기존 단일 마이그레이션(`20260320012331_AddApiUsagePromptAndIndexes`) 폐기.
   - `dotnet ef migrations add Init --output-dir Migrations` (PG용).
   - 35 테이블 모두 포함 + `Users.Email UNIQUE` 추가 (C4 해결).
   - `vector(1536)` 컬럼 별도 추가 + 백필 + 구 nvarchar 컬럼 drop.
3. 데이터 이전:
   - MSSQL `bcp out` → CSV
   - PG `COPY ... FROM CSV` (또는 pgloader)
   - 시계열 (ApiUsages, ChatMessages, DocumentChunks, ActivityLogs) bigint identity 보존
   - 임베딩 JSON → vector 변환 스크립트 (Python `numpy.frombuffer` 또는 PG `string_to_array::float[]::vector`)
4. 시드 재실행 (`DatabaseInitializer.cs` PG idempotent 변환).
5. **부채 해결 동시**:
   - C1, C2: AES-GCM + per-record IV (마이그레이션 시 재암호화)
   - C3: KeyHash 컬럼 + UNIQUE 인덱스
   - C4: Users.Email UNIQUE
   - C6: DB 평문 비번 → 환경변수
   - C8: SignalR Hub `[Authorize]` + `Context.UserIdentifier`
   - C10: appsettings.Production.json 시크릿 → User Secrets / IIS env

**위험**:
- IIS InProcess 환경에서 Npgsql 호환성 (검증 필요)
- Hangfire 작업 데이터 유실 방지 (현 DB 중지 → 신 DB 시작 시 재등록)
- LibreOffice 경로/MS SQL 의존 코드 잔존 검색

### 12.6 Phase 4: DocUtil/career → AGENT_HUB 통합

**작업**:
1. DocUtil:
   - `pg_dump --schema=public` (현재 DocUtil DB) → `pg_restore` to `AGENT_HUB.document_utilization`.
   - Alembic head 재설정 (009 → AGENT_HUB DB 적응).
   - DocUtil `tb_users`, `tb_organizations`, `tb_user_roles`, `tb_api_keys`, `tb_agents`, `tb_audit_log` 데이터 → AgentHub 통합 테이블로 이전 (시드 + UPSERT).
   - DocUtil 코드: `core/config.py`의 DB URL을 `AGENT_HUB`로 변경, schema=`document_utilization`.
2. career:
   - `pg_dump --schema=idino_career` → `pg_restore`.
   - audit 컬럼 보존, FK 재설정.
   - pgvector extension은 AGENT_HUB DB에 이미 활성 (Phase 2).
   - `tb_course/tb_program/tb_success_pattern.embedding vector(1536)` 컬럼 신설 + 백필 작업 (career의 기존 코드는 NULL 허용).
   - career `tb_user.role_level` → AgentHub `Users + UserRoles`로 이전 (단방향).
   - career 18 MS의 `shared/database/connection.py` URL을 `AGENT_HUB.idino_career`로 변경.
3. 검증:
   - schema 격리 (cross-schema query 차단 — view 또는 GRANT 제한)
   - 각 시스템 정상 기동 (3000/3001/8000/8001~8019 포트 모두 응답)
   - 데이터 무결성 검증 스크립트

### 12.7 Phase 5: AgentHub Nexus provider

**작업**:
1. `Settings/NexusSettings.cs` (BaseUrl, EmbeddingUrl, SharedSecret, DefaultTenantId, Timeouts).
2. `Services/INexusClient.cs` + `NexusClient.cs` (§6.3).
3. `Program.cs`: Named HttpClient `"nexus"`.
4. `AiProxyService` switch에 `"nexus"` 분기 추가 (`CallNexusAsync`).
5. `DatabaseInitializer.cs`: `ApiServices` 시드에 `nexus` + 모델 카탈로그.
6. `Agent` 엔티티에 `LlmRouting`, `RoutingPolicyJson`, `KnowledgeBaseSource`, `KnowledgeBaseRef`, `ConsumerSystems`, `ResponseFormat` 컬럼 추가 (마이그레이션).
7. `IHybridRouter` + `HybridRouter` 구현 (§10.3).
8. Nexus 측: 공유 시크릿 검증 미들웨어 1개 추가 (옵션).
9. 통합 테스트:
   - `dotnet test` — `WebApplicationFactory` + `NexusClient` mock
   - 실제 Nexus 인스턴스로 E2E (옵션 환경변수 `INTEGRATION_TEST_REAL_NEXUS=true`)

**예상 작업량**: 5~8일 (NexusClient 200 LOC + HybridRouter 300 LOC + 컬럼 추가 + 테스트).

### 12.8 Phase 6: DocUtil 운영자 흡수

**작업**:
1. AgentHub Vue Admin에 메뉴 추가 (§11.1).
2. AgentHub `Services/DocUtilClient.cs` (§6.4).
3. `Controllers/Admin/KbController.cs` (운영자 KB BFF).
4. DocUtil의 `(admin)/*` 라우트 정리:
   - 삭제: dashboard, admin-accounts, departments, agents, api-keys, quotas, help, quick-guide, settings.
   - 유지: documents, search-scopes, search-test, evaluation, templates, template-designer.
5. AgentHub 자체 KB → DocUtil 데이터 이전:
   - `KnowledgeBaseDocument` 엔티티 → DocUtil `tb_documents` (운영자 일괄 import).
   - 임베딩은 차원 동일(1536D)이라 변환 불요, payload 매핑만.
   - 이전 후 AgentHub 자체 KB 테이블 deprecate.
6. SignalR로 DocUtil의 인덱싱 진척률 → AgentHub Vue로 푸시 (DocUtil SSE → AgentHub `IHubContext<NotificationHub>` 전달).

### 12.9 Phase 7: AI 호출 위임

**작업**:
1. AgentHub에 13개 Agent 시드 (`DatabaseInitializer.cs`):
   - career 8 (§8.2.1)
   - docutil 4 (§8.2.2)
   - 공용 1 (§8.2.3)
2. 각 Agent별 ApiKey 발급 (운영자 콘솔 또는 시드):
   - `career-coaching-key`, `career-recommendation-key`, ...
   - `docutil-rag-key`, `docutil-report-key`, ...
3. DocUtil 변경:
   - `integrations/llm/factory.py:create_llm_client` → `AgentHubProxyClient` 단일화.
   - `integrations/image_generation/service.py:189` (DALL-E 직접) → AgentHub `/v1/images/generations` 위임.
   - `integrations/rag/graph_rag.py:105` (P1 위반) → AgentHub 또는 graph_rag 비활성.
   - `workers/embedding_generator.py:148` → AgentHub `/v1/embeddings` 위임.
   - `core/config.py`: `openai_api_key`, `anthropic_api_key`, `google_api_key`, `azure_openai_*` 제거.
4. career 변경:
   - `services/ai-service` 디렉토리 **제거** 또는 thin proxy로 (모든 호출을 AgentHub로 단순 forward).
   - `services/coaching-service:560-562`, `services/roadmap-service:578-580`, `services/competency-service:209-211` → `AGENTHUB_URL`로 직접 호출 (이미 위임 형태).
   - `services/simulation-service:973, 1764` → AgentHub 직접 호출 (현재 직접 호출 위치).
   - `career/shared/agenthub_client.py` (**신규**) — 모든 MS가 import.
   - 4 Tool은 AgentHub `Tools` 테이블에 등록되어 있어야 함 (§8.3).
5. SystemPrompt 추출 + 이전:
   - career `llm_service.py`의 11곳 prompt → DB Agent.SystemPrompt 컬럼.
   - docutil의 task별 prompt → 동일.
   - 코드에서 prompt 제거 후 Agent 호출만 남김.

### 12.10 Phase 8: (보류) Vue → Next.js

별도 트랙. 통합의 핵심 가치가 아니므로 통합 완료 후 결정.

대안 — 그대로 Vue 유지:
- AgentHub Vue Admin 부채 정리 (AgentChat 5,286줄 분해, raw axios 4건 → @/services/api 통합)
- Frontend 정리만 진행, 프레임워크는 그대로.

### 12.11 Phase별 의존성 그래프

```
0(셋업)
 └─ 1(인벤토리)
      └─ 2(DB)
           └─ 3(AgentHub→PG)
                ├─ 4(DocUtil/career→통합)
                │    └─ 6(운영자 흡수)
                │         └─ 7(AI 위임) ← 5의 산출물 필요
                └─ 5(Nexus provider) ─┘
                     (4와 병렬 가능)
```

5와 4는 병렬 가능. 6은 4 완료 후. 7은 5와 6 완료 후.

---

## 13. 보안 / 시크릿 / 암호화

### 13.1 시크릿 관리

| 시크릿 | 저장 위치 | 비커밋 |
|---|---|---|
| PG password (`idino!@#$`) | env (`PG_PASSWORD`) | ✓ |
| JWT shared secret (256bit) | env (`JWT_SHARED_SECRET`) | ✓ |
| AES encryption key (256bit, JWT와 분리) | env (`AES_KEY`) | ✓ (C2 해결) |
| External LLM API keys (OpenAI/Claude/...) | env (`OPENAI_API_KEY`, ...) | ✓ |
| AgentHub API keys (외부 시스템 발급) | DB (`KeyHash` + AES-GCM) | ✓ |
| Nexus shared secret | env (`NEXUS_SHARED_SECRET`) | ✓ |
| DocUtil-AgentHub mTLS / shared | env | ✓ |
| Redis password | env | ✓ |
| SSL 인증서 | `nexus/config/ssl/` | ✓ (.gitignore) |

**Vault 도입 (Phase 5+)**: 환경변수가 분산되면 HashiCorp Vault 또는 Azure Key Vault로 통합 (R26).

### 13.2 암호화 표준

- **AES-GCM** (per-record random IV, 256bit key) — ApiKey 저장 (C1, C2 해결)
- **bcrypt** (cost factor ≥ 12) — 사용자 비밀번호 (기존 유지)
- **HS256** (JWT, 256bit secret) — 토큰 서명
- **TLS 1.3** — 모든 외부 통신
- **mTLS** (Phase 6+) — AgentHub ↔ DocUtil 내부 통신 (선택)

### 13.3 PII 보호

- `IPiiDetectionService` (한국어 8종 + 영문 4종) — AgentHub 단일 권위.
- 모든 LLM 호출 진입 시 검사.
- `Agent.PiiMode = "block"`이면 PII 검출 시 400.
- `Agent.PiiMode = "mask"`이면 마스킹 후 진행.
- Hybrid 라우팅 + PII 검출 시 자동으로 Internal(Nexus) 강제 (외부 LLM 누수 방지).
- 검출 로그는 `PiiDetectionLog` 테이블에 기록 (감사).

### 13.4 BannedWord

- AgentHub `IBannedWordService` — 5분 캐시 (전역 + Agent별).
- 모든 사용자 입력 LLM 전송 전 검사.
- 검출 시 400 + `errorCode: "BANNED_WORD_DETECTED"`.

### 13.5 외부 노출 차단

- **Nexus**: LAN-only (192.168.x, 10.x, 172.16~31.x). CORS 미들웨어 + 방화벽.
- **DocUtil**: 사용자 챗봇 화면은 외부 노출, 운영자 API는 LAN 또는 mTLS.
- **career**: 학생 포털 외부 노출, 18 MS는 Kong 뒤 LAN.
- **AgentHub**: `/api/*`, `/v1/*` 외부 노출. `/api/admin/*`은 IP allowlist 또는 VPN 권장.

### 13.6 SignalR 보안 (C8 해결)

- `[Authorize]` 부착.
- `JoinUserNotifications`에서 `Context.UserIdentifier` 사용 (사용자 입력 userId 무시).
- 그룹 키: `user_{ClaimsPrincipal.UserIdentifier}`.

### 13.7 API Key 회전 (R7)

- `ApiKey.PreviousKeyHash` + `RotatedAt` (24h 유예).
- 회전 API: `POST /api/admin/api-keys/{id}/rotate` (Admin only).
- Hangfire `ApiKeyCleanupJob` (일 1회) — 24h 지난 PreviousKeyHash 삭제.

### 13.8 IP allowlist + CIDR (R8)

- `ApiKey.AllowedIps jsonb` — 단순 문자열 일치 → CIDR 지원 (`10.0.0.0/8`, `192.168.0.0/16`).
- `IpAddressRange` 라이브러리 또는 `System.Net.IPNetwork` 사용.

---

## 14. 환경별 배포 / 포트 매트릭스

### 14.1 환경 정의

| 환경 | 외부 LLM | Nexus | 사용 시나리오 |
|---|---|---|---|
| **외부망** | ON | OFF (미배포) | SaaS 외부 고객, 일반 학교 |
| **내부망** | OFF (방화벽 차단) | ON | 군/공공기관 에어갭, 보안 강화 |
| **하이브리드** | ON | ON | 일반 사용 + 민감 데이터만 내부 |

각 환경: 동일 코드베이스, **다른 ApiServices 시드** + **다른 환경변수**.

### 14.2 포트 매트릭스

#### 14.2.1 개발 (로컬)

| 서비스 | 프로토콜 | 포트 | 비고 |
|---|---|---|---|
| AgentHub API | HTTPS | 5001 | Kestrel, dev only |
| AgentHub UI (vite) | HTTP | 5173 | Vue dev server |
| DocUtil API | HTTP | 8000 | FastAPI |
| DocUtil UI | HTTP | 3000 | Next.js |
| career frontend | HTTP | 3001 | Next.js |
| career auth-service | HTTP | 8011 | |
| career student-service | HTTP | 8002 | |
| career competency-service | HTTP | 8003 | |
| career ai-service | HTTP | 8000 + 8006 | (Phase 7 이후 제거 또는 thin proxy) |
| career alumni-service | HTTP | 8005 | |
| career skill-service | HTTP | 8007 | |
| career opportunity-service | HTTP | 8008 | |
| career coaching-service | HTTP | 8009 | |
| career risk-service | HTTP | 8010 | |
| career badge-service | HTTP | 8012 | |
| career simulation-service | HTTP | 8013 | |
| career advisor-service | HTTP | 8014 | |
| career roadmap-service | HTTP | 8015 | |
| career portfolio-service | HTTP | 8016 | |
| career privacy-service | HTTP | 8017 | |
| career worknet-service | HTTP | 8018 | |
| career integration-service | HTTP | 8019 | |
| career notification-service | HTTP | 8020 (가정) | |
| career Kong | HTTP | 8000 (Kong default) | career ai-service와 충돌 — Kong을 8200으로 이동 권장 (R30) |
| nexus web | HTTP | 8001 | LAN-only |
| nexus vLLM | HTTP | 8001 (192.168.22.28) | LAN GPU 머신 |
| PostgreSQL | TCP | 5440 | 192.168.10.39 |
| Redis | TCP | 6340 | docutil-redis 컨테이너 (192.168.10.39) |
| Qdrant | HTTP | 6333 | DocUtil 전용 |
| RabbitMQ | TCP | 5672 / 15672 | DocUtil 전용 |
| MinIO | HTTP | 9000 / 9001 | DocUtil 전용 |

**충돌 해결 (R30)**: career의 ai-service가 8000을 점유하고 DocUtil API도 8000 — 통합 시:
- 옵션 A: career ai-service 제거 (Phase 7 목표) → 8000은 DocUtil 전용.
- 옵션 B: career ai-service는 8006만 유지, 8000 점유 해제.
- 옵션 C: 모든 career MS를 81xx 대역 (8101~8118)로 재할당.

권장: **옵션 A + Phase 1에서 8000 점유 매핑 명확화**.

#### 14.2.2 운영 (프로덕션)

도메인 구조 (예시):
- `agenthub.idino.co.kr` → AgentHub (IIS)
- `docutil.idino.co.kr` → DocUtil (Docker on Linux)
- `career.idino.co.kr` → career frontend (Next.js)
- `api-career.idino.co.kr` → career Kong gateway
- (nexus는 외부 노출 없음 — `192.168.x.x:8001`)

각 도메인 뒤에 reverse proxy (nginx) → 내부 포트 라우팅.

**TLS**: Let's Encrypt 또는 사내 CA. 모든 외부 도메인 HTTPS only (`RequireHttpsForDomainMiddleware` 유지).

### 14.3 배포 토폴로지

| 환경 | AgentHub | DocUtil | career | nexus |
|---|---|---|---|---|
| 개발 (Windows) | IIS Express / Kestrel | Docker Compose | Docker Compose | (LAN GPU) |
| 운영 외부망 | IIS Server | Linux Docker (192.168.10.39) | Linux Docker | (없음) |
| 운영 내부망 | IIS Server (LAN) | LAN Docker | LAN Docker | LAN GPU 머신 |
| 운영 하이브리드 | (LAN, 외부 LLM 허용) | LAN | LAN | LAN |

**모니터링**: Prometheus + Grafana + Loki (DocUtil 기존 14컨테이너 스택 활용 + AgentHub 메트릭 추가).

---

## 15. 미완성 부분 보강 계획

각 시스템의 부채를 통합 작업과 함께 해결한다.

### 15.1 AgentHub 부채 (TECHSPEC.md §16 요약)

| ID | 부채 | Phase 처리 |
|---|---|---|
| C1 | AES-CBC 고정 IV | **Phase 3** (마이그레이션과 함께 재암호화) |
| C2 | JWT-AES 키 재사용 | **Phase 3** (`AES_KEY` env 분리) |
| C3 | API Key O(N) 풀스캔 | **Phase 3** (`KeyHash` 컬럼 + UNIQUE) |
| C4 | Users.Email UNIQUE 누락 | **Phase 3** (baseline 마이그레이션) |
| C5 | CSharpToolExecutor 코드 인젝션 | **Phase 5** 또는 별도 (collectible AssemblyLoadContext + 권한 제한) |
| C6 | DB 평문 비번 하드코딩 | **Phase 3** (env 분리) |
| C7 | EF EnsureCreated drift | **Phase 3** (baseline) |
| C8 | SignalR Hub Authorize 부재 | **Phase 3** |
| C9 | 가짜 SSE | **Phase 5** (HybridRouter + 진짜 SSE) |
| C10 | appsettings 시크릿 | **Phase 0** (.gitignore + Phase 3 env 이관) |
| H1 | RagService 전체 청크 메모리 로드 | **Phase 6** (DocUtil 위임으로 자연 해결) |
| H2 | Workflow scoped DbContext 캡처 | **Phase 5** (`IServiceScopeFactory`) |
| H3 | Workflow Condition/Loop NO-OP | **Phase 5+** (별도 진척) |
| H4 | ChatService _convLocks 무한 증가 | **Phase 5** (TTL evict) |
| H5 | Stream API 키 풀 우회 | **Phase 5** (HybridRouter + 진짜 SSE) |
| H8 | per-user Rate Limit 미부착 | **Phase 5** (모든 `/api/*` 컨트롤러) |
| H10 | Quota 토큰수 무시 | **Phase 5** |
| H13 | AiProxyService 3,749 LOC | **Phase 5+** (Strategy 패턴, Nexus 추가가 트리거) |
| H14 | Fallback 1단계만 | **Phase 5** (LlmRouting 통합) |
| 미구현 | Agent 편집 모드 | **Phase 6+** (운영자 콘솔 강화) |

### 15.2 DocUtil 부채

| 항목 | 처리 |
|---|---|
| Phase 4 S4~S7 미완 (Mode B / HWPX / 회의록 RAG / jinja 폐기) | **Phase 6 진입 전 S6/S7 완료 권장** (R29) |
| `report_generator.py` 3702 LOC | S7에 폐기 |
| `graph_rag.py` P1 위반 | **Phase 7** (위임 또는 비활성) |
| 회의록·요약 R1~R5 부실 | **Phase 6 전** S6 완료 |
| HWP 생성 불가 (포기 결정) | 변경 없음 |
| HWPX 한컴 호환성 미검증 | S5 PoC 필요 |
| 한국어 출력 비율 0.56~0.66 | S6 프롬프트 개선 |
| 챗봇 응답 3.6s | S6 |
| OpenAI TPM 502 | **Phase 7** (AgentHub 위임 후 AgentHub 측 재시도/백오프) |
| `cors_origins=["*"]` | **Phase 6** (도메인 화이트리스트) |
| `encryption_key` 더미 기본값 | **Phase 0** (.env 강제) |
| WebSocket query string 토큰 | **Phase 6** (Subprotocol 또는 첫 메시지 인증) |
| Nginx 4440 connection refused | 인프라 |
| 임베딩 차원 1536 vs 2048 | **Phase 7** (1536D 단일화) |

### 15.3 career 부채

| 항목 | 처리 |
|---|---|
| pgvector 미적용 (DDL) | **Phase 4** (extension + 컬럼 + 백필) |
| 자동테스트 부재 | **Phase 7+** (pytest + httpx mock 도입) |
| Kafka 미사용 (디렉토리만) | **Phase 4** (삭제 또는 명시적 NO-OP) |
| `httpx.AsyncClient` per-request | **Phase 7** (공유 모듈에 singleton DI) |
| DB 비번 `"2012"` 하드코딩 | **Phase 4** (env 강제) |
| CORS `*` | **Phase 4** (도메인 화이트리스트) |
| `role_level` 정수 | **Phase 4** (AgentHub `Role` 매핑) |
| 30s 고정 timeout | **Phase 7** (AgentHub 표준) |
| 다국어 메시지 혼재 | **Phase 7** (한국어 표준) |
| `tb_recommendation_evidence` 불일치 | **Phase 7** (AgentHub Eval 모델로) |
| 53 audit 컬럼 표준 충돌 | **Phase 4** (병행 유지 + AgentHub 표준 추가) |
| SimulationService 1764줄 단일 파일 | **Phase 7** (Strategy 패턴) |

### 15.4 Nexus 부채

| 항목 | 처리 |
|---|---|
| 인증 미들웨어 부재 (LAN 격리에만 의존) | **Phase 5** (공유 시크릿 미들웨어 추가) |
| 시크릿 평문 yaml | **Phase 0/5** (.env로 이동, 이미 .gitignore) |
| `/health` 응답 풍부화 | **Phase 5** (vLLM 모델 ID, GPU VRAM, 큐 깊이) |
| Redis 인메모리 폴백 | 변경 없음 (개발 편의) |
| 컨텍스트 8192 토큰 한계 | 변경 없음 (모델 한계) |
| 단일 GPU max_num_seqs=1 | 변경 없음, AgentHub 측 동시성 제한으로 보호 |

### 15.5 통합 차원 신규 부채 (보강 계획)

| 항목 | Phase |
|---|---|
| 통합 테스트 인프라 (`tests/integration/` + docker-compose.test.yml) | **Phase 5+** |
| 모니터링 통합 (Prometheus + Grafana + AgentHub 메트릭) | **Phase 5+** |
| Vault / 시크릿 관리 통합 | **Phase 5+** |
| reverse proxy / 도메인 라우팅 | **Phase 7+** (운영 배포 전) |
| CI 게이트 (lint + test + integration) | **Phase 7+** |
| 사용자 SSO (옵션 B 인증) | **Phase 5+** 결정 |

---

## 16. 위험 분석 및 완화 (R1~R30)

### 16.1 통합 차원 위험

| ID | 위험 | 영향 | 완화 |
|---|---|---|---|
| R1 | Tenant/Organization/Department 모델 통합 부재 | 권한/멀티테넌시 불일치 | §4.5 + §7.4, Phase 4 단계에서 `Tenants` 신설 |
| R2 | DocUtil 6단계 visibility를 AgentHub가 미보유 | 권한 폭증 | Phase 6에서 BFF 호출 시 visibility 전파, AgentHub Admin UI는 visibility CRUD 신설 |
| R3 | OpenAI Structured Outputs는 OpenAI/Azure 전용 | Claude/Gemini 위임 시 strict JSON 미지원 | Agent.ResponseFormat 신설 + provider별 fallback (Claude Tool Use, Gemini Discriminated Union) |
| R4 | career의 `role_level` 정수 vs AgentHub Role enum | 인증 깨짐 | Phase 4 매핑 함수 (§7.3) |
| R5 | Nexus DB 통합 여부 | 라이프사이클 충돌 / 데이터 부피 | **별도 유지** 결정 (§5.1, §8.2) |
| R6 | 순환 호출 (AgentHub → DocUtil → AgentHub) | 무한 루프 / 타임아웃 | DocUtil은 `/search/hybrid`만 노출 (P8) |
| R7 | API Key 회전 미구현 | 키 누출 시 즉시 invalidation 불가 | Phase 5에서 `PreviousKeyHash`/24h 유예 도입 |
| R8 | CIDR IP 검증 부재 | 내부 IP 대역 단일 일치만 | Phase 5에서 `IPNetwork` 라이브러리 |
| R9 | Redis 분산 Rate Limit 부재 | 다중 인스턴스 배포 시 카운터 분리 | Phase 5+에서 `IApiKeyRateLimiter` Redis 백엔드 |
| R10 | Nexus 인증 부재 (LAN에만 의존) | 외부 노출 시 즉시 위험 | Phase 5에서 공유 시크릿 미들웨어 |
| R11 | EF baseline 부재 (현재 EnsureCreated) | 환경별 schema drift | Phase 3에서 baseline 신규 작성 |
| R12 | Cascade Delete 위험 (ApiServices→Agents) | 서비스 1개 삭제 시 모든 Agent 연쇄 삭제 | Restrict로 강등 |
| R13 | 임베딩 차원 1536 vs 2048 분기 | Qdrant collection 재생성 필요 | Phase 7에서 1536D 단일화 |
| R14 | DocUtil Phase 4 진행 중 통합 시작 | 코드 충돌 | S7 완료 후 또는 monorepo 내부에서 마무리 (R29) |
| R15 | JWT 알고리즘/시크릿 불일치 (DocUtil RS256/HS256 fallback vs AgentHub HS256) | 인증 단절 | Phase 4에서 HS256 단일 표준 |
| R16 | DocUtil `tb_organization_quotas` vs AgentHub `ApiQuota` 정책 충돌 | 비용 폭주 또는 차단 | Phase 6에서 `ApiQuota` 단일화, DocUtil은 위임 |
| R17 | Qdrant collection 단일성 vs 1024D Nexus 임베딩 | 차원 충돌 | Nexus 자체 RAG는 별도 collection 또는 별도 DB |
| R18 | 평문 시크릿 잔존 위험 (nexus_config.yaml, career DB `"2012"`) | 깃 이력 누출 | Phase 0 `.gitignore` + Phase 4/5에서 env 이관, git filter-branch (이미 첫 commit이라 영향 적음) |
| R19 | 가짜 SSE 외부 SDK 호환성 | OpenAI SDK/Cursor/LangChain 깨짐 | Phase 5에서 진짜 SSE (C9) |
| R20 | AgentHub 자체 KB → DocUtil 마이그레이션 시 visibility/department/project 매핑 손실 | 권한 손실 | 기본 visibility=`department_only` + 운영자 검수 |
| R21 | DocUtil agent_type CHECK 제약 vs AgentHub Agent 일반 | Agent 동작 변경 | metadata.tag로 보존 |
| R22 | career 1700 LOC SimulationService 분리 호출 2곳 | 위임 시 큰 변경 | Phase 7 Strategy 패턴 |
| R23 | DocUtil 14컨테이너 + AgentHub IIS 운영 모델 상이 | 배포 복잡도 | reverse proxy로 라우팅 |
| R24 | Phase 100% 표기와 실제 갭 (career pgvector / 자동테스트 / Kafka) | "이미 완료"로 간주 시 회귀 | Phase 1 인벤토리 + Phase 4에서 재검증 |
| R25 | DocUtil 회의록·요약 R1~R5 부실 | 사용자 체감 품질 | S6 완료 (Phase 6 전) |
| R26 | 시크릿 분산 (.env 다수) | 시크릿 누출 / 운영 부담 | Phase 5+에서 Vault 도입 |
| R27 | 사용자 SSO (DocUtil/career JWT 통합) | Phase 5+ 미결정 | 옵션 결정 후 통합 (옵션 B 권장) |
| R28 | docling/MinIO/RabbitMQ는 DocUtil 전용 | 운영 학습 곡선 | DocUtil Linux 컨테이너 그대로 유지 |
| R29 | DocUtil Phase 4 미완 상태에서 통합 진행 | 일정 지연 / 체감 품질 | S6/S7 완료 후 Phase 6 진입 (~6주 추가) 또는 monorepo 내부에서 S6/S7 진행 |
| R30 | 포트 8000 충돌 (career ai-service + DocUtil) | 로컬 개발 혼란 | Phase 1에서 정의 + Phase 7에서 ai-service 제거 |

### 16.2 위험 우선순위

**Critical (Phase 3 진입 전 결정 필수)**:
- R1 (Tenant 모델), R5 (Nexus DB 별도), R11 (EF baseline), R15 (JWT)

**High (Phase 5 전)**:
- R3, R7, R8, R10, R12, R13, R17, R18, R20, R27

**Medium (Phase 6 전)**:
- R2, R6, R14, R16, R19, R21, R22, R23, R25, R29, R30

**Low (보강 가능)**:
- R4, R9, R24, R26, R28

---

## 17. 테스트 전략

### 17.1 4 계층

| 계층 | 위치 | 도구 | 책임 |
|---|---|---|---|
| Unit | 각 서브프로젝트 | xUnit / pytest | 함수/클래스 단위 |
| Integration (서브프로젝트) | 각 서브프로젝트 | xUnit + Testcontainers / pytest + httpx | 서비스 다중 조합 |
| **Cross-System Integration** | **monorepo 루트** `tests/integration/` (**신규**) | pytest + httpx + docker-compose | 서브프로젝트 간 통합 |
| E2E | 사용자 앱 | Playwright | UI 시나리오 |

### 17.2 우선순위 테스트 대상

1. **AgentHub Nexus provider** (`AiProxyService.CallNexusAsync`) — mock + 실 인스턴스
2. **AgentHub LlmRouting 결정 엔진** (`HybridRouter`)
3. **AgentHub 진짜 SSE** (`/v1/chat/completions stream:true`)
4. **DocUtil → AgentHub Agent API 클라이언트**
5. **career → AgentHub Agent API 클라이언트**
6. **DB 스키마 격리** (cross-schema query 차단)
7. **API Key 인증 + Scope + Rate Limit** (회전 + CIDR 포함)
8. **운영자 KB 등록 → DocUtil 동기화**
9. **PII 감지 → Internal 강제 라우팅**
10. **Multi-Tenant 격리** (다른 tenant_id 데이터 노출 차단)

### 17.3 외부 의존성 Mock

| 대상 | Mock |
|---|---|
| External LLM | Moq.Contrib.HttpClient (.NET), respx (Python) |
| Nexus | mock FastAPI (`tests/mocks/nexus-mock`) |
| DocUtil API | mock FastAPI (`tests/mocks/docutil-mock`) |
| PostgreSQL | Testcontainers PostgreSQL |
| Redis | fakeredis.aioredis (Python), Testcontainers (.NET) |
| Qdrant | mock 클라이언트 또는 Testcontainers |
| SignalR | Moq IHubContext |

### 17.4 통합 테스트 스택 (`tests/docker-compose.test.yml`)

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: AGENT_HUB_TEST
      POSTGRES_USER: AGENT_HUB_TEST
      POSTGRES_PASSWORD: test_pw
  redis:
    image: redis:7
  qdrant:
    image: qdrant/qdrant
  nexus-mock:
    build: tests/mocks/nexus-mock
    ports: ["18000:8001"]
  docutil-mock:
    build: tests/mocks/docutil-mock
    ports: ["18100:8000"]
  agenthub:
    build: ./agenthub
    depends_on: [postgres, redis, nexus-mock, docutil-mock]
    environment:
      ConnectionStrings__DefaultConnection: "Host=postgres;..."
      Nexus__BaseUrl: "http://nexus-mock:8001"
      DocUtil__BaseUrl: "http://docutil-mock:8000"
```

### 17.5 CI 게이트 (Phase 7+)

```
1. lint:
   agenthub: dotnet format --verify-no-changes
   docutil/backend: ruff check .
   docutil/frontend: eslint .
   career: ruff check + eslint
   nexus: ruff check .
2. type-check:
   agenthub/ClientApp: vue-tsc --noEmit
   docutil/frontend: tsc --noEmit
   career/frontend: tsc --noEmit
3. unit:
   dotnet test
   pytest (각 서브프로젝트)
4. integration:
   docker-compose -f tests/docker-compose.test.yml up
   pytest tests/integration/
5. e2e:
   playwright (smoke만)
```

전 단계 통과 시 PR 머지 허용.

### 17.6 테스트 금지 사항

- 실제 OpenAI/Claude API 호출 금지 (비용 + 결과 비결정성)
- 실제 운영 PostgreSQL 인스턴스 접근 금지
- 실제 Nexus 인스턴스 호출은 별도 환경변수 (`INTEGRATION_TEST_REAL_NEXUS=true`)
- 테스트 간 실행 순서 의존 금지
- wwwroot/uploads/data 디렉토리 오염 금지

---

## 18. 모니터링 / 관찰성 / 운영

### 18.1 헬스체크

각 시스템 `/health` 표준 응답:
```json
{
  "status": "healthy | degraded | unhealthy",
  "version": "1.0.0",
  "deps": [
    {"name": "postgres", "status": "healthy", "latency_ms": 5},
    {"name": "redis", "status": "healthy"},
    {"name": "qdrant", "status": "healthy"},
    {"name": "openai", "status": "degraded", "reason": "rate_limited"}
  ],
  "checked_at": "2026-05-04T12:00:00Z"
}
```

AgentHub Hangfire 작업이 각 시스템 `/health` 주기 폴링 → 알림.

### 18.2 메트릭

각 시스템 `/metrics` (Prometheus 호환):
- HTTP 요청 수 / 지연 / 에러율
- LLM 호출 수 / 토큰 / 비용 / 라우팅 분포 (External/Internal)
- API Key 사용률
- DB 커넥션 풀 사용률
- Redis hit/miss
- Qdrant 검색 지연 (DocUtil)
- 사용자 활성도 (DAU/MAU)

### 18.3 로깅

- **모든 시스템**: 구조화 로그 (JSON), 로그 레벨 표준 (INFO/WARN/ERROR/DEBUG)
- **AgentHub**: Serilog → 파일 + (옵션) Elasticsearch
- **DocUtil**: Loguru → 파일 + Loki
- **career**: 표준 logging → Loki
- **nexus**: 자체 로깅 → 파일

### 18.4 활동 로그 (감사)

AgentHub `ActivityLog` 단일 권위:
- 모든 운영자 행위 (Agent 생성/수정/삭제, KB 업로드, Key 발급 등)
- 모든 LLM 호출 (`ApiUsage` 시계열)
- DocUtil/career의 운영자 행위는 BFF를 통해 AgentHub로 전파.

### 18.5 알림 / Webhook (Phase 7+)

`POST /api/webhooks/{event_type}` (운영자 등록):
- `key.expiring` (24h 전)
- `quota.exceeded`
- `agent.message.failed`
- `pii.detected` (관리자만)
- `rag.indexing.failed`

---

## 19. 일정 / 마일스톤 / 의존성

### 19.1 Phase별 예상 기간 (영업일 기준)

| Phase | 작업 | 영업일 | 누적 |
|---|---|---|---|
| 0 | 셋업 (완료) | 1 | 1 |
| 1 | 인벤토리 | 3 | 4 |
| 2 | DB 설계 + 생성 | 2 | 6 |
| 3 | AgentHub MSSQL→PG + 부채 정리 | 10 | 16 |
| 4 | DocUtil/career → 통합 + pgvector | 8 | 24 |
| 5 | Nexus provider + LlmRouting + 진짜 SSE | 8 | 32 |
| 6 | 운영자 흡수 + KB 마이그레이션 | 10 | 42 |
| 7 | AI 호출 위임 (DocUtil + career) | 10 | 52 |
| 8 | (보류) Vue→Next.js | — | — |

**총 ≈ 52 영업일 (10주)** + DocUtil S6/S7 완료 시간(~6주) = **약 16주 (4개월)**.

### 19.2 마일스톤

- **M1 (Phase 2 완료)**: AGENT_HUB DB 가동 ✓
- **M2 (Phase 3 완료)**: AgentHub PG 위에서 정상 동작 ✓
- **M3 (Phase 4 완료)**: 단일 PG에 4 schema 통합 ✓
- **M4 (Phase 5 완료)**: AgentHub가 Internal/External 모두 라우팅 가능 ✓
- **M5 (Phase 6 완료)**: 운영자가 단일 콘솔에서 전체 관리 ✓
- **M6 (Phase 7 완료)**: DocUtil/career의 모든 AI 호출이 AgentHub 경유 ✓ — **통합 완료**

### 19.3 위험-기반 일정 조정

- DocUtil Phase 4 S6/S7 미완 → Phase 6 6주 지연 가능 (R29)
- MSSQL→PG 데이터 이전 실패 시 Phase 3 5일 추가
- pgvector 백필 시간 (career 53 테이블 + AgentHub 1536D) → Phase 4 +3일

### 19.4 의존 그래프

```
M1 ─┐
    ├──→ M2 ──┬──→ M3 ──┬──→ M5 ──→ M6 (통합 완료)
              │         │
              │         ├──→ M4 ────────┐
              └─────────┘                │
                                         │
                              (M4와 M3 모두 충족 시 M5 진입)
```

---

## 20. 의사결정 기록 (ADR 요약)

| ADR | 결정 | 대안 | 이유 |
|---|---|---|---|
| ADR-1 | **Nexus 통합 옵션 B (AgentHub-side 클라이언트)** | 옵션 A (Nexus가 OpenAI 호환 어댑터 추가) | Nexus의 세션/멀티테넌시 강점 보존, AgentHub의 기존 패턴(Claude/Gemini도 네이티브 호출)과 일치 |
| ADR-2 | **RAG 단일 권위 = DocUtil** | AgentHub 자체 KB 유지 | 중복 권위 제거, DocUtil은 RAG 전문 시스템 |
| ADR-3 | **Vue 3 유지 (Phase 8 보류)** | Next.js 전면 이행 | 통합의 핵심 가치는 Data Plane 통합. 프레임워크 마이그레이션은 별도 트랙 |
| ADR-4 | **단일 PostgreSQL `AGENT_HUB` DB + 4 schema** | 시스템별 별도 DB | 운영 단순화, schema 격리로 충분, 단일 인스턴스 백업 |
| ADR-5 | **MSSQL → PostgreSQL** | MSSQL 유지 | DocUtil/career가 PG 사용, pgvector + jsonb + timestamptz 우수 |
| ADR-6 | **EF Core baseline 신규 작성** | 기존 마이그레이션 재활용 | 단일 마이그레이션밖에 없고 EnsureCreated drift 해결 |
| ADR-7 | **DocUtil Phase 4 별도 트랙** | 즉시 통합 시작 | S6/S7 미완 상태 통합 시 회귀 위험 (R29) |
| ADR-8 | **Tenants 신규 엔티티** | 시스템별 organization 모델 유지 | 멀티테넌시 단일 권위 |
| ADR-9 | **JWT HS256 단일 표준** | RS256 또는 dual | DocUtil RS256/HS256 fallback 통합 (R15) |
| ADR-10 | **임베딩 1536D 단일화** | 1536D + 2048D 공존 | Qdrant collection 단일성, AgentHub `text-embedding-3-small` 표준 |
| ADR-11 | **Nexus DB 별도 유지** | AGENT_HUB로 통합 | 라이프사이클 다름, 데이터 부피, 차원 불일치 |
| ADR-12 | **순환 호출 방지**: DocUtil은 `/search/hybrid`만 노출 | DocUtil이 LLM 합성 | 무한 루프 방지, LLM 합성은 AgentHub 단일 책임 |
| ADR-13 | **공유 시크릿 인증 (AgentHub-Nexus)** | mTLS | 단순성, LAN 격리에 추가하는 1차 방어 |
| ADR-14 | **포트 8000 충돌 해결: career ai-service 제거** | 다른 포트 재할당 | Phase 7 목표가 ai-service 제거이므로 자연 해결 |
| ADR-15 | **`progress.md` 자동 갱신 규칙** | 별도 트래킹 도구 | git commit 단위로 진행 상황 명확화 |
| ADR-16 | **AES-GCM + per-record 12바이트 nonce + 별도 운영 키** (트랙 #64 후, 2026-05-12) | JWT-derived 키 + CBC + 고정 IV (Phase 9 이전) | TECHSPEC §16 C1/C2 보강, 키 강도 256bit, 회전 재발 방지 위해 validator 강화(ADR-17) |
| ADR-17 | **DocUtil ENCRYPTION_KEY validator 강화 + db_schema validator** (트랙 #65/#67, 2026-05-12) | 길이만 검증 | 약한 키(엔트로피<64bit, 반복 패턴) 부팅 차단 + Phase 4.1 ADR-5 schema 격리 우회 차단. 단위 테스트 22건 PASS |
| ADR-18 | **DocUtil alembic 마이그레이션은 schema-agnostic** (트랙 #66/#67, 2026-05-12) | `op.create_table(..., schema="...")` 명시 | env.py 의 5중 안전(`version_table_schema`/`include_schemas`/`CREATE SCHEMA`/`SET LOCAL search_path`/`connect_args`)에 일임. 마이그레이션 파일은 `op.create_table("tb_X")` 만, schema-qualified identifier 도 금지. `docs/DB_MIGRATION.md v1.1 §10` 참조 |
| ADR-19 | **운영 임시 secrets 파일은 적용 후 즉시 삭제** (트랙 #62, 2026-05-12) | 회복용 보관 | `.env` 백업(`.env.bak.*` 0600)이 회복 경로 제공. 평문 키 별도 보관은 lateral move 위험 |

---

## 21. 미해결 결정 / Open Questions

다음 항목은 통합 진행 중 결정 필요:

### Q1. career `department_id` 매핑 정책
- 옵션 A: `Tenants` 하위 sub-org (계층 구조).
- 옵션 B: 별도 `Departments` 테이블, `Tenants`와 N:M.
- 옵션 C: career 자체 유지, AgentHub는 미보유.
- **결정 시점**: Phase 4 시작 전.

### Q2. 사용자 SSO 시점
- 옵션 A: Phase 5+ 즉시 통합 (AgentHub `IJwtService` 단일 발급).
- 옵션 B: Phase 7+ 또는 별도 트랙.
- **결정 시점**: Phase 4 완료 후 평가.

### Q3. DocUtil Phase 4 S6/S7 진행 위치
- 옵션 A: DocUtil 원본 워크트리에서 완료 후 monorepo로 흡수.
- 옵션 B: monorepo 내부 `docutil/`에서 진행.
- **결정 시점**: 즉시 (Phase 1 진입 전).

### Q4. Nexus DB 위치
- 옵션 A: 별도 DB `nexus` (현재 192.168.10.39:5440의 `nexus` DB 그대로).
- 옵션 B: `AGENT_HUB.nexus` schema (이전).
- **결정**: ADR-11에 따라 옵션 A. 단 schema 분리만 추가 검토.

### Q5. 외부 LLM API Key 풀 (다중 키)
- AgentHub가 제공자별 다중 키 라운드로빈 풀 (현재). Tenant별 다른 키 풀 가능?
- **결정 시점**: Phase 5.

### Q6. DocUtil 임베딩 (vLLM Qwen3-Embedding 2048D) 처리
- 옵션 A: 제거, 1536D 단일.
- 옵션 B: 별도 collection 유지 (옵션 사용 가능).
- **결정 시점**: Phase 7 (R17).

### Q7. Workflow Condition/DataTransform/Loop 정식 구현
- 현재 NO-OP 스텁. 실 구현 또는 노드 비활성?
- **결정 시점**: Phase 5+ 별도 (H3).

### Q8. CSharpToolExecutor 보안
- 코드 인젝션 + AssemblyLoadContext 누수 (C5).
- 옵션 A: collectible AssemblyLoadContext + 권한 제한 (Roslyn 안전 컴파일).
- 옵션 B: 기능 차단 (Tool type=csharp 비활성).
- **결정 시점**: Phase 5+.

### Q9. 운영자 SSO (Active Directory 등)
- 학교/기업 환경에서 AD/LDAP 연동 요구 가능.
- **결정 시점**: Phase 6+.

### Q10. 데이터 보존 정책
- ApiUsage / ChatMessage / ActivityLog 시계열 데이터 보존 기간.
- **결정 시점**: Phase 5+ (스토리지 비용 추정 후).

---

## 부록 A. 파일 위치 카탈로그

### A.1 monorepo 루트
- `D:\workspace\IDINO_Agent_Hub\.gitignore`
- `D:\workspace\IDINO_Agent_Hub\README.md`
- `D:\workspace\IDINO_Agent_Hub\CLAUDE.md`
- `D:\workspace\IDINO_Agent_Hub\.claude\rules\*.md` (6개)
- `D:\workspace\IDINO_Agent_Hub\docs\ARCHITECTURE.md`
- `D:\workspace\IDINO_Agent_Hub\docs\AI_INVENTORY.md`
- `D:\workspace\IDINO_Agent_Hub\user_mig\TECHSPEC.md` (본 문서)
- `D:\workspace\IDINO_Agent_Hub\user_mig\progress.md`
- `D:\workspace\IDINO_Agent_Hub\user_mig\source_AGENTHUB.md`
- `D:\workspace\IDINO_Agent_Hub\user_mig\source_DOCUTIL.md`
- `D:\workspace\IDINO_Agent_Hub\user_mig\source_CAREER.md`
- `D:\workspace\IDINO_Agent_Hub\user_mig\source_NEXUS.md`

### A.2 서브프로젝트 핵심 파일

#### agenthub (변경 대상)
- `agenthub\Program.cs` — DI/미들웨어/Hangfire (PG 전환)
- `agenthub\Data\AIAgentManagementDbContext.cs` — `HasDefaultSchema`
- `agenthub\Data\DatabaseInitializer.cs` (866 LOC) — 시드 idempotent 재작성
- `agenthub\Migrations\` — baseline 신규 작성
- `agenthub\Services\AiProxyService.cs` (3,749 LOC) — Nexus 분기 + Strategy 분리
- `agenthub\Services\NexusClient.cs` (**신규**)
- `agenthub\Services\HybridRouter.cs` (**신규**)
- `agenthub\Services\DocUtilClient.cs` (**신규**)
- `agenthub\Controllers\OpenAICompatController.cs:138` — 진짜 SSE
- `agenthub\Controllers\Admin\KbController.cs` (**신규**)
- `agenthub\Hubs\ChatHub.cs`, `NotificationHub.cs` — `[Authorize]`
- `agenthub\Models\Agent.cs` — `LlmRouting` 등 신규 컬럼
- `agenthub\Models\ApiKey.cs` — `KeyHash` 등
- `agenthub\Settings\NexusSettings.cs` (**신규**)
- `agenthub\appsettings.json` — `Nexus` 섹션 추가, 시크릿 env 이관

#### docutil (변경 대상)
- `docutil\backend\integrations\llm\factory.py:32` — `AgentHubProxyClient`로 단일화
- `docutil\backend\integrations\image_generation\service.py:189` — AgentHub 위임
- `docutil\backend\integrations\rag\graph_rag.py:105` — AgentHub 위임 또는 비활성
- `docutil\backend\workers\embedding_generator.py:148` — AgentHub 위임
- `docutil\backend\core\config.py` — DB URL `AGENT_HUB`, OpenAI keys 제거
- `docutil\frontend\app\(admin)\*` — 운영자 페이지 정리

#### career (변경 대상)
- `career\services\ai-service\` — Phase 7에서 제거 또는 thin proxy
- `career\services\simulation-service\app\services\simulation_service.py:973, 1764` — AgentHub 위임
- `career\services\coaching-service\app\services\coaching_service.py:560-562` — `AGENTHUB_URL`로 변경
- `career\services\roadmap-service\app\services\roadmap_service.py:578-580` — 동일
- `career\services\competency-service\app\services\competency_service.py:209-211` — 동일
- `career\shared\agenthub_client.py` (**신규**)
- `career\shared\common\auth.py` — JWT 표준 클레임
- `career\shared\database\connection.py` — DB URL `AGENT_HUB.idino_career`, 평문 비번 제거
- `career\database\` — pgvector extension + 임베딩 컬럼 백필 SQL 추가

#### nexus (변경 최소)
- `nexus\config\nexus_config.yaml` — 시크릿 env로 이동 (이미 .gitignore)
- `nexus\web\app.py` — 공유 시크릿 검증 미들웨어 (선택)
- `nexus\web\app.py:/health` — 풍부화 (모델 ID, GPU VRAM, 큐)

### A.3 인프라
- `D:\workspace\IDINO_Agent_Hub\infra\db\init.sql` (**신규**)
- `D:\workspace\IDINO_Agent_Hub\docker-compose.dev.yml` (**신규**, Phase 4+)
- `D:\workspace\IDINO_Agent_Hub\tests\docker-compose.test.yml` (**신규**, Phase 5+)
- `D:\workspace\IDINO_Agent_Hub\tests\integration\` (**신규**, Phase 5+)
- `D:\workspace\IDINO_Agent_Hub\tests\mocks\nexus-mock\` (**신규**)
- `D:\workspace\IDINO_Agent_Hub\tests\mocks\docutil-mock\` (**신규**)

---

## 부록 B. 변경 카탈로그 요약 (Phase 5~7 핵심)

### B.1 Phase 5 변경 (AgentHub 중심)
- 신규 파일: `NexusClient.cs`, `INexusClient.cs`, `HybridRouter.cs`, `IHybridRouter.cs`, `NexusSettings.cs`, 마이그레이션
- 변경 파일: `Program.cs` (Named HttpClient + DI), `AiProxyService.cs` (switch 추가), `Agent.cs`/`ApiKey.cs` (컬럼), `OpenAICompatController.cs` (진짜 SSE), `ChatService.cs` (`HybridRouter` 통합), `Hubs/*.cs` (`[Authorize]`), `appsettings.json` (env)
- 삭제: 가짜 SSE 코드 (`OpenAICompatController.cs:138`)
- 시드: ApiServices에 `nexus`, ApiServiceModels에 Nexus 모델 카탈로그

### B.2 Phase 6 변경 (운영자 흡수)
- 신규 파일: `DocUtilClient.cs`, `IDocUtilClient.cs`, `Controllers\Admin\KbController.cs`, Vue Admin 메뉴 (`/admin/knowledge`, `/admin/tenants` 등)
- 변경 파일: AgentHub Vue Pinia 스토어, services/api 경로
- 삭제: AgentHub 자체 KB 컨트롤러/엔티티 (deprecate 후 410), DocUtil `(admin)/dashboard`, `admin-accounts`, `departments`, `agents`, `api-keys`, `quotas`, `help`, `quick-guide`, `settings`
- 데이터 이전: AgentHub `KnowledgeBaseDocument` → DocUtil `tb_documents`

### B.3 Phase 7 변경 (AI 위임)
- 신규 파일: `agenthub_client.py` (career), `AgentHubProxyClient` (docutil)
- 변경 파일: docutil `factory.py`, `image_generation/service.py:189`, `graph_rag.py:105`, `embedding_generator.py:148`, `core/config.py`
- 변경 파일: career `ai-service/llm_service.py` 제거 또는 thin proxy, `simulation_service.py`, `coaching_service.py`, `roadmap_service.py`, `competency_service.py`
- 시드: AgentHub 13개 Agent + 4개 Tool + Agent별 ApiKey 발급
- 환경변수: `AGENTHUB_URL`, `AGENTHUB_API_KEY` (각 시스템)
- 삭제: 각 시스템의 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` 등

### B.4 자율 트랙 변경 (2026-05-12, ADR-16~19)
- 신규 파일: `docs/DB_MIGRATION.md v1.1 §10` (운영 사고 이력 + 재발 방지), `docutil/backend/tests/test_config_validator.py` (22 단위 테스트), `infra/db/seeds/phase5_phase7_seeds.sql` (시드 reproducibility, 트랙 #47)
- 변경 파일: `docutil/backend/app/core/config.py` (validator 강화: ENCRYPTION_KEY 3중 + db_schema 4중), `docutil/backend/tests/conftest.py` (테스트용 강한 키), `agenthub/Controllers/OpenAICompatController.cs` (POST /v1/images/generations, 트랙 DU-14), `agenthub/Exceptions/DocUtilUpstreamException.cs` (신규, Reports 410 deprecation), `agenthub/Services/{IDocUtilClient, DocUtilClient, DocUtilTokenProvider}.cs` (R2 잔여 7건 보강 + 95 BFF endpoint 누적), Phase 10.1a~10.2e 운영자 BFF 13 Vue 메뉴
- 운영 변경: 트랙 #63 `ALTER TABLE public.<X> SET SCHEMA document_utilization` 28회 + alembic_version + ALTER ROLE search_path / 트랙 #64 ENCRYPTION_KEY 회전 (Bulk Re-encrypt, tb_llm_api_keys 1행) / 트랙 #62 임시 secrets 파일 shred + rm 3개 / Phase 7 코드 배포 (docutil-api/celery 3 컨테이너) / 5 서비스 비번 강화 (Redis/RabbitMQ/MinIO/Flower/Grafana) / JWT_SECRET_KEY 강화 (256bit) / docutil .env 에 AGENTHUB_URL + AGENTHUB_API_KEY 추가
- 삭제: `docutil/backend/app/integrations/llm/{claude_client, gemini_client}.py` (806 LOC dead code, anti-patterns §1)
- 시드: AgentHub Phase 7.1 15 Agent + Phase 2.x 16 ApiServices `infra/db/seeds/phase5_phase7_seeds.sql` codify (idempotent)

---

## 부록 C. 변경 영향 매트릭스

각 변경이 영향을 미치는 시스템 / 영역:

| 변경 | agenthub | docutil | career | nexus | infra | tests |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| MSSQL→PG | ◎ | ○ (확인) | ○ (확인) | × | ◎ | ◎ |
| Nexus provider 추가 | ◎ | × | × | △ | ○ | ◎ |
| LlmRouting | ◎ | ○ (호출) | ○ (호출) | × | × | ◎ |
| 진짜 SSE | ◎ | ○ (호환) | ○ (호환) | × | × | ◎ |
| DocUtil 운영자 흡수 | ◎ | ◎ | × | × | × | ◎ |
| RAG 단일 권위 (DocUtil) | ◎ | ◎ | × | × | × | ◎ |
| AI 호출 위임 (Phase 7) | ◎ | ◎ | ◎ | × | × | ◎ |
| Tenant 신설 | ◎ | ○ (매핑) | ○ (매핑) | × | × | ◎ |
| pgvector 활성화 | ◎ | × | ◎ | × | ◎ | × |
| JWT 통일 | ◎ | ◎ | ◎ | × | × | ◎ |
| 시크릿 env 이관 | ◎ | ◎ | ◎ | ◎ | ◎ | × |
| 포트 충돌 해결 | × | × | ◎ | × | × | × |

범례: ◎ 직접 변경 / ○ 영향 받음 / △ 선택적 / × 무관

---

## 결언

본 TECHSPEC은 4개 시스템의 통합을 **점진적이고 안전하게** 진행하기 위한 계획서다. 각 Phase는 사용자 승인 후 시작하며, 완료 시 `progress.md`를 갱신한다. 위험(R1~R30)을 우선순위별로 관리하고, 미해결 결정(Q1~Q10)은 해당 Phase 진입 전에 결정한다.

**다음 작업** (현재 Phase 0 완료 직후):
1. `progress.md` 작성 (본 문서 다음 단계)
2. Phase 1 (AI 호출 인벤토리) 사용자 승인 요청
3. Q3 결정 (DocUtil S6/S7 진행 위치)

— 작성: 2026-05-04
