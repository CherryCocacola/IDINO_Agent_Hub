# IDINO Career Architecture Rules

18개 FastAPI 마이크로서비스 + Next.js 14 프론트엔드 구조의 아키텍처 원칙.

## P1. 단일 구현 원칙 (Single Implementation)

각 외부 의존은 **단 하나의 진입점**을 통해서만 접근한다. 두 가지 방법이 공존하면 에이전트가 어느 쪽을 써야 할지 혼란스러워진다.

| 외부 의존 | 유일한 진입점 |
|---|---|
| OpenAI/LLM 호출 | `services/ai-service/app/services/llm_service.py:LLMService` |
| Kafka producer/consumer | `shared/common/kafka.py` |
| DB 연결/세션 | `shared/database/connection.py` |
| 공통 인증/JWT | `shared/common/auth.py` |
| 구조화 로깅 | `shared/common/logging.py` |
| 프론트엔드 HTTP 호출 | `frontend/lib/api/client.ts` (서비스별 axios 인스턴스) |

**Why**: 마이크로서비스 18개에 동일한 호출 패턴을 반복하지 않기 위함. 변경 시 한 곳만 수정.

## P2. 고정된 모듈 구조 (Fixed Module Structure)

각 서비스 `services/{service-name}/app/` 하위에 허용되는 파일/디렉토리:

```
app/
  __init__.py
  main.py            # FastAPI 앱 + 라우터 등록 + 미들웨어
  config.py          # pydantic Settings (env에서 로드)
  database.py        # AsyncSession 의존성 (DB 사용 시)
  routers/           # API 엔드포인트만 (비즈니스 로직 금지)
  services/          # 비즈니스 로직
  schemas/           # Pydantic 요청/응답 모델
  models/            # SQLAlchemy ORM 모델 (DB 보유 서비스만)
  repositories/      # ORM 쿼리 래핑 (auth-service 등)
  clients/           # 외부 API 호출 래퍼 (ai-service, roadmap-service)
  tools/             # OpenAI Tool Calling 도구 (ai-service만)
  exceptions.py      # 서비스 고유 예외
```

**거부**: `helpers.py`, `handler.py`, `controller.py`, `manager.py`, `*_service.py`(파일명 단수형 강제), `utils.py`(공통 utils는 `shared/common/`).

## P3. 의존성 방향 (Dependency Direction)

```
Router → Service → Repository → DB
            ↓
            Client → 외부 서비스(httpx via Kong)
            ↓
            Kafka producer (shared)
```

규칙:
- Router는 비즈니스 로직을 수행하지 않는다 — 입력 검증 후 Service 호출만
- Service는 다른 Service를 직접 import하지 않는다 (같은 서비스 내부 제외)
- 다른 마이크로서비스의 데이터가 필요하면: (a) Kong 경유 httpx 호출 또는 (b) Kafka 이벤트 구독
- Repository는 SQLAlchemy 쿼리를 캡슐화 — Service가 직접 ORM을 조작하지 않음

순환 import는 lazy import로 해결, 계층 역방향 import는 즉시 거부.

## P4. Import 순서

```python
# 1. 표준 라이브러리
import asyncio
from datetime import datetime

# 2. 서드파티
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 3. shared (절대 import만)
from shared.common.auth import get_current_user
from shared.database.connection import get_db_session

# 4. app 내부 (절대 import만)
from app.services.competency_service import CompetencyService
from app.schemas.competency import CompetencyResponse
```

**금지**: 상대 import(`from .service import ...`).

## P5. 서비스 간 통신 계약

서비스 A가 서비스 B의 데이터를 필요로 할 때 허용되는 방식은 **두 가지뿐**.

### (a) 동기 호출 — Kong 게이트웨이 경유 httpx
```python
# services/ai-service/app/clients/student_client.py
async with httpx.AsyncClient(base_url=settings.kong_gateway_url) as client:
    response = await client.get(f"/api/v1/students/{student_id}",
                                headers={"Authorization": f"Bearer {token}"})
```
- `settings.kong_gateway_url`은 `app/config.py`에서 환경변수로 로드
- 절대 `http://student-service:8002`처럼 직접 호출하지 않음 (Kong 라우팅 우회 금지)

### (b) 비동기 이벤트 — Kafka
```python
# 발행
from shared.common.kafka import KafkaProducer
from shared.schemas.events import StudentCreatedEvent

await producer.send("student.created", StudentCreatedEvent(student_id=..., ...))
```
- 토픽명: `{aggregate}.{action}` 형식 (`student.created`, `competency.calculated`, `risk.alerted`)
- 이벤트 스키마는 **반드시** `shared/schemas/events.py`에 Pydantic v2 모델로 정의

## P6. 프론트엔드 (Next.js 14 App Router)

```
frontend/
  app/                    # App Router 페이지 (route segments)
    (auth)/login/         # 인증 그룹
    (dashboard)/          # 인증된 대시보드 그룹
  components/
    sections/             # 페이지 단위 큰 섹션 (Overview, Competency, Risk 등)
    dashboard/            # 대시보드 전용 컴포넌트
    layout/               # 헤더, 사이드바 등 레이아웃
    charts/               # 차트 컴포넌트
    ui/                   # 재사용 UI 원자 (Card, Modal, ProgressBar)
  lib/
    api/
      client.ts           # 단일 axios 인스턴스 + 서비스별 export (authApi, studentApi, ...)
      {service}.ts        # 서비스별 함수 정의
  hooks/                  # React Query 훅, 도메인 훅(useDashboard 등)
  stores/                 # 전역 상태 (현재 비어있음, 필요 시에만 도입)
  types/                  # TypeScript 타입 정의
```

규칙:
- **모든 HTTP 호출은 `lib/api/client.ts`의 axios 인스턴스를 사용한다**. 컴포넌트나 훅에서 `fetch()` 또는 새 axios 인스턴스 생성 금지
- 컴포넌트에서 직접 API URL을 하드코딩하지 않음 — `lib/api/{service}.ts`의 함수 호출
- 데이터 페칭은 React Query 훅(`hooks/`)으로 캡슐화
- API 응답은 백엔드 snake_case → 프론트 boundary에서 camelCase로 매핑 (또는 Pydantic alias 활용)

## P7. 인프라 — 포트와 라우팅

- Kong 게이트웨이: `8000` (외부 진입점, `/api/v1/{service-prefix}`)
- 마이크로서비스: `8001~8020` 범위 (auth=8011, student=8002, competency=8003, ai=8006, skill=8007, risk=8010, badge=8012, simulation=8013, roadmap=8015 등)
- PostgreSQL: `5432` (pgvector 확장)
- Redis: `6379`
- Kafka: `9092`
- 프론트엔드: `3000` (개발), nginx reverse proxy

새 서비스 포트 할당 시 `infrastructure/docker/docker-compose.yml`과 `gateway/kong.yml`을 동시에 갱신.
