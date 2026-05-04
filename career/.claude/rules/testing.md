# IDINO Career Test Strategy

## 현황과 우선순위

현재 서비스별 `tests/` 디렉토리는 대부분 부재이고, 루트의 `tests/test_sample_students.py`와 `frontend/e2e/dashboard.spec.ts`만 존재한다. 신규 코드 작성 시 sdet-agent가 함께 테스트를 추가한다.

## 테스트 디렉토리 구조

```
services/{service-name}/
  tests/
    unit/
      test_{module}.py        # 함수/클래스 단위
    integration/
      test_{module}.py        # DB/Redis/Kafka mock 포함
    fixtures/
      conftest.py             # pytest fixture
frontend/
  e2e/
    {feature}.spec.ts         # Playwright E2E
tests/                        # 프로젝트 루트 — 다중 서비스 통합
  test_e2e_{scenario}.py      # 실제 환경 E2E
```

## 우선 테스트 모듈 (구현 시 반드시 테스트)

| 우선순위 | 서비스/모듈 | 테스트 항목 |
|---|---|---|
| 1 | auth-service | JWT 발급/갱신/만료, RBAC 거부, 2FA |
| 2 | competency-service | 8대 역량 점수 계산, 가중치 검증, 음수/0 처리 |
| 3 | ai-service | Tool Calling 응답 파싱, 추천 로직, 폴백 |
| 4 | risk-service | 룰 기반 위험 감지, AI 분석 결합, 알림 생성 |
| 5 | shared/common/kafka.py | producer/consumer round-trip |
| 6 | shared/common/auth.py | JWT 디코드, role 추출, 만료 처리 |
| 7 | roadmap-service | AI 로드맵 단계 생성, 학생 컨텍스트 반영 |
| 8 | frontend/lib/api/client.ts | 토큰 첨부, 401 처리, 재시도 |

## 파일 / 함수 명명

- 파일: `test_{module_name}.py`
- 함수: `test_{feature}_{scenario}_{expected_result}`
- 예시:
  - `test_jwt_refresh_with_expired_token_returns_401`
  - `test_competency_calculate_with_zero_score_returns_zero`
  - `test_ai_recommend_with_empty_history_falls_back_to_default`
  - `test_kafka_producer_send_event_persists_to_topic`

## 테스트 실행

```bash
# 백엔드 — 서비스별
cd services/auth-service && pytest tests/ -v
cd services/competency-service && pytest tests/ --cov=app --cov-report=html

# 백엔드 — 전체 (워크스페이스 루트에서)
pytest services/*/tests/ -v

# 프론트엔드 E2E
cd frontend && npx playwright test
cd frontend && npx playwright test e2e/dashboard.spec.ts --headed

# 통합
pytest tests/ -v
```

## Mock 전략

| 대상 | Mock 라이브러리 | 이유 |
|---|---|---|
| OpenAI API | `respx` (httpx mock) + 응답 fixture JSON | 비용/속도/확정성 |
| PostgreSQL | `testcontainers-postgres` 또는 SQLite in-memory | 실제 SQL 동작 검증 |
| Redis | `fakeredis` (async) | 캐시 동작 |
| Kafka | `aiokafka` mock 또는 `confluent-kafka` test consumer | 이벤트 round-trip |
| 다른 마이크로서비스 (Kong 경유 호출) | `respx` | 서비스 경계 격리 |
| 파일시스템 | pytest `tmp_path` fixture | 격리 |

## AsyncIO / FastAPI 테스트 패턴

```python
# pytest-asyncio + httpx AsyncClient로 FastAPI 앱 테스트
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_student_get_returns_200():
    """기존 학생 ID로 조회 시 200 OK와 학생 정보 반환을 검증한다."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/students/20244897",
            headers={"Authorization": "Bearer <test-token>"}
        )
    assert response.status_code == 200
    assert response.json()["student_id"] == "20244897"
```

## Kafka 이벤트 테스트 패턴

```python
@pytest.mark.asyncio
async def test_competency_calculated_event_published_after_score_update():
    """점수 갱신 후 competency.calculated 이벤트가 발행되는지 검증."""
    from shared.common.kafka import KafkaProducer
    producer = KafkaProducer(test_mode=True)

    await competency_service.update_score("20244897", "COMP_001", 85.5)

    events = producer.get_sent_events("competency.calculated")
    assert len(events) == 1
    assert events[0].student_id == "20244897"
```

## 테스트 금지 사항

- **실제 OpenAI API 호출 금지** — `respx`로 mock
- **실제 운영 DB 연결 금지** — testcontainers 또는 in-memory
- **테스트 간 실행 순서 의존 금지** — 각 테스트는 독립
- **`time.sleep()` 사용 금지** — `asyncio.wait_for(..., timeout=...)` 사용
- **하드코딩된 토큰/시크릿 금지** — fixture에서 생성
- **운영 환경 학생 데이터 사용 금지** — 더미 학번(20244897 등)으로 fixture 작성

## 커버리지 목표 (참고)

- auth/competency/ai/risk: 80% 이상 (핵심 도메인)
- 그 외 서비스: 60% 이상
- shared/: 90% 이상 (재사용성 높음)

## QA 게이트 (커밋 전)

1. `ruff check . && ruff format .`
2. 영향받은 서비스의 `pytest -x`
3. 프론트엔드 변경 시 `npx tsc --noEmit && npx eslint .`
4. 큰 기능 변경 시 `qa-tester` 에이전트 호출 (`.claude/agents/qa-tester.md`)
