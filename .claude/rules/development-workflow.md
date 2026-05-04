# IDINO Agent Hub — 개발 워크플로우

monorepo 구조에서 작업 진행 흐름과 환경 셋업 가이드.

## Phase별 작업 순서 (확정)

| Phase | 내용 | 산출물 |
|---|---|---|
| 0 | 작업공간 셋업 | `IDINO_Agent_Hub/` + 4개 서브프로젝트 + init 파일 |
| 1 | AI 호출 인벤토리 | `docs/AI_INVENTORY.md` |
| 2 | AGENT_HUB DB 설계 + 생성 | `infra/db/init.sql`, `docs/DB_MIGRATION.md` |
| 3 | AgentHub MSSQL → PostgreSQL 마이그레이션 | EF baseline, 데이터 이전 스크립트 |
| 4 | DocUtil/career → AGENT_HUB 통합 | 스키마별 connection 변경, 데이터 이전 |
| 5 | AgentHub에 Nexus provider 추가 | `Services/NexusClient.cs`, `AiProxyService` 분기, Agent.LlmRouting |
| 6 | DocUtil 운영자 → AgentHub 흡수 | AgentHub UI에 KB 메뉴, BFF 클라이언트 |
| 7 | DocUtil/career AI 호출 → AgentHub 위임 | 인벤토리 기준 코드 교체, API Key 발급 |
| 8 | (보류) Vue → Next.js 점진 이행 | 별도 트랙 |

각 Phase는 사용자 승인 후 시작. Phase 내부에서 발견된 추가 작업은 사용자 보고 후 진행.

## 로컬 개발 환경 셋업

### 사전 요구사항
- .NET 8 SDK
- Node.js 20+
- Python 3.11+
- Docker Desktop (Windows)
- PostgreSQL 클라이언트 (`psql` 또는 DBeaver)
- LibreOffice (HWP/PPTX↔PDF 변환)
- Git + GitHub credentials

### 첫 셋업
```bash
# 1. 저장소 clone
git clone https://github.com/CherryCocacola/IDINO_Agent_Hub.git
cd IDINO_Agent_Hub

# 2. 환경 변수 파일 작성 (예시 복사)
cp agenthub/appsettings.Development.example.json agenthub/appsettings.Development.json
cp docutil/.env.example docutil/.env
cp career/.env.example career/.env
cp nexus/.env.example nexus/.env

# 3. 시크릿 입력 (DB 비밀번호, LLM API 키 등)
# DB: AGENT_HUB / idino!@#$ (192.168.10.39:5440)

# 4. 각 서브프로젝트별 의존성 설치
cd agenthub && dotnet restore && cd ClientApp && npm install && cd ../..
cd docutil && docker compose pull && cd ..
cd career && cd frontend && npm install && cd ../..
cd nexus && python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt && cd ..
```

## 서브프로젝트별 실행

### agenthub (.NET 8 + Vue 3)
```bash
cd agenthub
dotnet ef database update                         # DB 마이그레이션 (PG 전환 후)
dotnet run                                        # https://localhost:5001
# 별도 터미널
cd ClientApp && npm run dev                       # http://localhost:5173
```

### docutil (FastAPI + Next.js)
```bash
cd docutil
docker compose up -d --build
docker exec docutil-api alembic upgrade head
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### career (FastAPI 18-MS + Next.js)
```bash
cd career
docker compose -f infrastructure/docker-compose.yml up -d
cd frontend && npm run dev                        # http://localhost:3001
```

### nexus (Python asyncio)
```bash
cd nexus
.venv/Scripts/activate
python -m web.app                                 # http://localhost:8001 (LAN)
```

## 통합 dev 모드 (옵션)

루트에 `docker-compose.dev.yml` 작성 (Phase 1 이후):
```bash
docker compose -f docker-compose.dev.yml up
```
- 모든 서브프로젝트 + PostgreSQL + Redis + Qdrant + nexus-mock 동시 기동

## 작업 분기 / 머지 정책

```
main         ─ 통합 안정 브랜치
develop      ─ 통합 개발 브랜치
feature/*    ─ 기능 개발 (예: feature/agenthub-nexus-provider)
fix/*        ─ 버그 수정
phase/{N}    ─ Phase별 통합 작업 (예: phase/2-db-init)
```

PR 규칙:
- `feature/*` → `develop`
- `develop` → `main` (Phase 완료 시)
- 코드 리뷰 1+ 필요
- CI 게이트 통과 (Phase 1 이후)

## 자주 사용하는 도구 / 위치

| 작업 | 위치 |
|---|---|
| Agent 생성/관리 | agenthub Vue UI `http://localhost:5173/agents/builder` |
| 사용량/비용 분석 | agenthub UI `/analytics` |
| DocUtil 문서 업로드 | docutil UI 또는 (Phase 6 이후) agenthub UI |
| career 학생 데이터 | career frontend |
| Nexus 모니터링 | nexus `/health`, `/metrics`, (Phase 6 이후) agenthub UI |
| DB 직접 접근 | psql `postgresql://AGENT_HUB:idino!@#$@192.168.10.39:5440/AGENT_HUB` |

## 트러블슈팅

### "Database connection failed"
- PostgreSQL 인스턴스(192.168.10.39:5440) 접근 가능한지 확인
- `AGENT_HUB` user/DB가 생성되었는지 확인 (Phase 2)
- 방화벽 또는 VPN 필요 여부

### "AgentHub Vue dev server CORS 오류"
- agenthub `Program.cs`의 CORS origin 목록 확인
- `http://localhost:5173`이 포함되어 있어야 함

### "Nexus 응답 타임아웃"
- LAN 연결 확인
- nexus `health` 엔드포인트 응답 확인
- 쿨다운 상태인 키가 있는지 (`/v1/sessions` 또는 ApiKeyPool 모니터링)

### "DocUtil RAG 결과 없음"
- Qdrant 컨테이너 기동 확인
- 문서 인덱싱 상태 확인 (`is_indexed`)
- 임베딩 차원 일치 (1536)

## 환경별 배포

| 환경 | 활성 시스템 | 비활성 |
|---|---|---|
| 외부망 | agenthub + docutil + career + External LLM | nexus 미배포 |
| 내부망 | agenthub + docutil + career + nexus | External LLM 차단 (방화벽) |
| 하이브리드 | 전부 | — |

각 환경은 동일 코드베이스, 다른 ApiServices 시드 + 다른 환경변수.
