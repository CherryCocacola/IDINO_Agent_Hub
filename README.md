# IDINO Agent Hub

다중 시스템(에이전트 관리 / 문서 활용 / 학생 진로 / 내부망 LLM)을 통합한 IDINO의 AI Agent 플랫폼.

## 통합 비전

**AgentHub를 AI Control Plane으로 두고, 나머지 시스템은 AgentHub에 정의된 Agent를 소비**하는 구조.

- **외부망 모드**: External LLM (GPT/Claude/Gemini/Mistral 등) → AgentHub → DocUtil + idino_career
- **내부망 모드**: Nexus (Qwen 27B + ExaOne 7.8B, 에어갭) → AgentHub → DocUtil + idino_career
- **하이브리드 모드**: PII/데이터 라벨 기반 동적 라우팅 (External ↔ Internal)

## 디렉토리 구조

```
IDINO_Agent_Hub/
├── agenthub/    AI 운영자 콘솔 + AI Gateway
│                .NET 8 + Vue 3 + PostgreSQL
│                Agent 정의 + LLM 라우팅 + 사용량/비용/PII/감사
│
├── docutil/     문서 활용 / RAG 데이터 플레인 + 사용자 챗봇
│                FastAPI + Next.js 16 + PostgreSQL + Qdrant
│                AI 호출은 AgentHub로 위임
│
├── career/      학생 진로 포털 (인제대 IU-나비 위에 얹는 구조)
│                FastAPI 18-MS + Next.js 14 + PostgreSQL (pgvector)
│                각 MS의 AI 호출은 AgentHub로 위임
│
├── nexus/       내부망 LLM 오케스트레이터 (LAN-only)
│                Python asyncio + vLLM + PostgreSQL (pgvector)
│                AgentHub가 /v1/chat 호출 (옵션 B)
│
└── docs/
    ├── ARCHITECTURE.md     통합 아키텍처
    ├── AI_INVENTORY.md     AI 호출 지점 카탈로그
    ├── DB_MIGRATION.md     AGENT_HUB DB 설계 + 마이그레이션
    └── DEPLOYMENT.md       외부망/내부망/하이브리드 배포
```

## 데이터 측면 — 단일 PostgreSQL 인스턴스, 3 스키마

```
PostgreSQL (192.168.10.39:5440, AGENT_HUB user)
└── Database: AGENT_HUB
    ├── schema: AIAgentManagement     ← AgentHub 테이블 (35개)
    ├── schema: document_utilization  ← DocUtil 테이블
    ├── schema: idino_career          ← idino_career 테이블
    └── schema: hangfire              ← Hangfire 자체 테이블

Nexus는 별도 PG 인스턴스 유지 (에어갭 격리)
```

## 빠른 시작

### 사전 요구사항
- .NET 8 SDK
- Node.js 20+
- Python 3.11+
- PostgreSQL 17 (192.168.10.39:5440 — 사내 인스턴스)
- Redis (선택)
- LibreOffice (HWP/PPTX↔PDF 변환)

### 각 서브프로젝트별 README
- [agenthub/README.md](agenthub/README.md)
- [docutil/README.md](docutil/README.md)
- [career/README.md](career/README.md)
- [nexus/README.md](nexus/README.md)

## 통합 작업 단계

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | 작업공간 셋업, 4개 시스템 copy, init 설정 | 진행 중 |
| 1 | AI 호출 인벤토리 작성 (`docs/AI_INVENTORY.md`) | 대기 |
| 2 | PostgreSQL AGENT_HUB DB + 3개 스키마 생성 | 대기 |
| 3 | AgentHub MSSQL → PostgreSQL 마이그레이션 | 대기 |
| 4 | DocUtil/idino_career → AGENT_HUB 스키마 통합 | 대기 |
| 5 | AgentHub에 Nexus provider 추가 (옵션 B) | 대기 |
| 6 | DocUtil 운영자 기능 → AgentHub 흡수 | 대기 |
| 7 | DocUtil/idino_career AI 호출 → AgentHub 위임 | 대기 |
| 8 | (선택) Vue Frontend → Next.js 점진 이행 | 보류 |

## 라이선스

내부 사용 전용.
