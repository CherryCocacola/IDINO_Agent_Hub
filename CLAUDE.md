# IDINO Agent Hub — 통합 컨텍스트

> 4개 서브프로젝트(`agenthub`/`docutil`/`career`/`nexus`)를 단일 monorepo로 통합한 IDINO의 AI Agent 플랫폼.

---

## ⚠️ 신규 세션 진입 시 자동 로드 (필수)

**모든 신규 세션은 첫 응답 전에 다음 두 파일을 반드시 `Read`로 로드한다**:

1. **`user_mig/progress.md`** — 현재 Phase, 마지막 commit, 미해결 이슈, Open Questions
2. **`user_mig/TECHSPEC.md`** — 통합 기술 명세 (현재 Phase 관련 섹션 정독)

이는 **단순 권장이 아니라 강제 사항**이다. 두 파일을 읽지 않은 상태로 작업을 진행하면:
- 이미 결정된 ADR을 다시 논의하게 됨
- 진행 중인 위험/이슈를 놓침 (예: secret leak, push 차단 등)
- 사용자가 같은 컨텍스트를 반복 설명해야 함

진입 절차:
```
1. Read user_mig/progress.md (전체)
2. Read user_mig/TECHSPEC.md 의 §0~§3 (개요/카탈로그/아키텍처) + 현재 Phase 해당 섹션
3. progress.md의 "다음 작업" 섹션을 사용자에게 보고
4. 사용자 지시 받기
```

**작업 종료 시**: `user_mig/progress.md` 갱신 (R7 규칙). 갱신 없이 세션 종료 금지.

---

## 통합 비전 (필수 숙지)

**AgentHub를 AI Control Plane으로**, 나머지 시스템은 AgentHub Agent를 소비:

- AgentHub: AI 설정 운영자 콘솔 + AI Gateway (Agent 정의, LLM 라우팅, 할당량, PII, 감사)
- DocUtil: RAG 데이터 플레인 + 사용자 챗봇 — AI 호출은 AgentHub로 위임
- idino_career: 학생 진로 포털 — 18개 MS의 AI 호출은 AgentHub로 위임
- nexus: 내부망 LLM 오케스트레이터 (LAN-only, 에어갭)

**LLM 라우팅**:
- 외부망 = OpenAI/Claude/Gemini/Mistral 등 (External)
- 내부망 = Nexus (Internal, LAN-only)
- 하이브리드 = PII/데이터 라벨 기반 동적 분기

## 서브프로젝트 기술 스택

| 디렉토리 | 스택 | DB 스키마 |
|---|---|---|
| `agenthub/` | .NET 8 + Vue 3 + EF Core | `AGENT_HUB.AIAgentManagement` |
| `docutil/` | FastAPI + Next.js 16 + SQLAlchemy 2 async | `AGENT_HUB.document_utilization` |
| `career/` | FastAPI 18-MS + Next.js 14 + Kong Gateway | `AGENT_HUB.idino_career` |
| `nexus/` | Python asyncio + vLLM + Pydantic v2 | (별도 PG, 에어갭 격리) |

## 통합 데이터베이스

```
PostgreSQL: 192.168.10.39:5440
Database: AGENT_HUB
User: AGENT_HUB / Password: idino!@#$
Schemas: AIAgentManagement / document_utilization / idino_career / hangfire
Extensions: vector (pgvector), uuid-ossp, pg_trgm
```

> Nexus는 자체 PG 인스턴스 유지 (에어갭 원칙).

## 작업 시 절대 규칙

### R1. 서브프로젝트 경계 존중
- 작업 전 어느 서브프로젝트(`agenthub`/`docutil`/`career`/`nexus`)인지 명시
- 서브프로젝트별 `CLAUDE.md`와 `.claude/rules/`가 별도 존재 — 그 규칙도 따른다
- 서브프로젝트 간 직접 import 금지. 통신은 HTTP/SignalR/Channel로만

### R2. AI 호출 단일 진입점 = AgentHub
- DocUtil/career에서 OpenAI/Claude/Gemini SDK 직접 사용 금지
- 모든 LLM 호출은 AgentHub의 `/v1/chat/completions` 또는 `/api/agents/{id}/chat`로
- Nexus 호출도 AgentHub의 `AiProxyService.CallNexusAsync`를 경유 (옵션 B)

### R3. 데이터베이스 스키마 격리
- 각 서브프로젝트는 자기 스키마만 접근
- Cross-schema 조인 금지 — 필요하면 API 호출로 데이터 가져오기
- 단, AgentHub는 운영자 콘솔이므로 공통 메타(예: 사용량 조회)에서 다른 스키마 read 가능 (read-only)

### R4. 시크릿 관리
- `.env`, `appsettings.*.json`은 `.gitignore`로 제외
- 프로덕션 시크릿은 환경변수 또는 외부 vault
- 코드에 평문 시크릿 하드코딩 금지

### R5. 한국어 우선
- 모든 사용자향 메시지: 한국어
- 코드 주석: 초보자도 이해할 수 있는 한국어
- 변수/함수/커밋 메시지: 영어

### R6. 커밋 메시지 형식
```
[scope/모듈] 한글 설명

scope: agenthub | docutil | career | nexus | docs | infra | user_mig
예시:
  [agenthub/aiproxy] Nexus provider 추가 — CallNexusAsync 구현
  [docutil/llm] AgentHub /v1/chat 호출로 전환
  [career/coaching] 학생 코칭 Agent ID 매핑 추가
  [docs] AI_INVENTORY.md 작성
  [infra/db] AGENT_HUB DB + 3개 스키마 생성 SQL
  [user_mig] TECHSPEC v1.1 — Tenant 모델 결정 반영
```

### R7. 진행 상황 갱신 (필수)
- **모든 작업 완료 후 `user_mig/progress.md`를 갱신**한다.
- 갱신 시점:
  1. 새 Phase 진입 / 완료 시 — Phase 상태표 변경 + 작업 로그 추가
  2. 핵심 작업 완료 시 (파일 신설, 마이그레이션 적용, 의사결정 등) — 작업 로그
  3. ADR / 위험 / Open Question 변경 시 — 해당 섹션
  4. Git commit 후 — 마지막 commit 해시 갱신
- **갱신 없이 작업을 종료하지 않는다.** progress.md는 차기 세션의 컨텍스트 진입점이다.
- TECHSPEC 변경(`user_mig/TECHSPEC.md`)이 발생하면 progress.md의 ADR / Open Question 섹션도 동기화한다.

## 핵심 명령어

### agenthub (.NET)
```bash
cd agenthub
dotnet build
dotnet ef migrations add <Name>
dotnet ef database update
dotnet run                                # https://localhost:5001
cd ClientApp && npm run build:check
```

### docutil (Python + Next.js)
```bash
cd docutil
docker compose up -d --build              # 전체 스택
docker exec docutil-api alembic upgrade head
cd backend && ruff check . && ruff format .
cd frontend && npx eslint . && npx prettier --check .
```

### career (Python 18-MS + Next.js)
```bash
cd career
docker compose -f infrastructure/docker-compose.yml up -d
cd frontend && npm run dev
```

### nexus (Python asyncio)
```bash
cd nexus
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
python -m web.app                         # FastAPI 서버
```

## 문서 안내

### 통합 마스터 문서 (필수 숙지)
- `user_mig/TECHSPEC.md` — **통합 기술 명세서** (도메인 모델, 마이그레이션 전략, 위험 분석 R1~R30, ADR-1~15, Open Questions Q1~10)
- `user_mig/progress.md` — **진행 상황 추적** (Phase 상태, 작업 로그, ADR 결정, 위험 추적). **모든 작업 후 갱신 필수** (R7)

### 시스템별 분석 보고서
- `user_mig/source_AGENTHUB.md` — AgentHub 종합 분석
- `user_mig/source_DOCUTIL.md` — DocUtil 종합 분석
- `user_mig/source_CAREER.md` — idino_career 종합 분석
- `user_mig/source_NEXUS.md` — Nexus 종합 분석

### 운영 문서
- `docs/ARCHITECTURE.md` — 통합 아키텍처 (다이어그램, 시퀀스, 결정사항)
- `docs/AI_INVENTORY.md` — AI 호출 지점 카탈로그 (Phase 1 산출물)
- `docs/DB_MIGRATION.md` — AGENT_HUB DB 설계 + 마이그레이션 가이드 (Phase 2+ 작성)
- `docs/DEPLOYMENT.md` — 외부망/내부망/하이브리드 배포 (Phase 7+ 작성)
- 각 서브프로젝트의 `CLAUDE.md`와 `.claude/rules/`도 함께 참조

### 신규 세션 진입 절차
1. `user_mig/progress.md` 먼저 읽기 (현재 Phase, 마지막 commit, Open Questions 확인)
2. `user_mig/TECHSPEC.md` 의 해당 Phase 섹션 정독
3. 사용자에게 진행 상황 보고 + 다음 작업 제안

## 통합 작업 단계 요약

> 상세 일정/의존성/위험은 `user_mig/TECHSPEC.md` §12, §19 참조.
> 현재 진척은 `user_mig/progress.md` 참조.

| Phase | 내용 | 예상 영업일 |
|---|---|---|
| 0 | 작업공간 셋업 + init + 분석/TECHSPEC | 1 ✅ |
| 1 | AI 호출 인벤토리 (`docs/AI_INVENTORY.md`) | 3 |
| 2 | AGENT_HUB DB 생성 (`infra/db/init.sql`) | 2 |
| 3 | AgentHub MSSQL → PostgreSQL + 부채 정리 (C1~C10) | 10 |
| 4 | DocUtil/career → AGENT_HUB 통합 + pgvector | 8 |
| 5 | AgentHub Nexus provider + LlmRouting + 진짜 SSE | 8 |
| 6 | DocUtil 운영자 → AgentHub 흡수 + KB 마이그레이션 | 10 |
| 7 | DocUtil/career AI 호출 → AgentHub 위임 | 10 |
| 8 | (보류) Vue → Next.js 점진 이행 | — |

**총 ≈ 52 영업일 (10주)** + DocUtil S6/S7 완료(~6주) = **약 16주**.

각 Phase는 사용자 승인 후 시작 (`development-workflow.md` 규칙).

## 보안/시크릿 위치

| 리소스 | 위치 |
|---|---|
| PostgreSQL 접속 | `nexus/config/nexus_config.yaml` (참조용), 각 시스템 `.env` |
| GitHub 토큰 | `nexus/.git/config` 참조 |
| LLM API 키 | 각 시스템 `.env` 또는 IIS 환경변수 |
| JWT/암호화 키 | `agenthub/appsettings.*.json` (gitignore 대상) |

> 시크릿은 모두 `.gitignore`로 제외. 새 시크릿 추가 시 반드시 패턴 추가 확인.
