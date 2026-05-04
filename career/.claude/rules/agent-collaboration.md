# IDINO Career AI Agent Collaboration Rules

Claude Code 또는 다른 AI 코딩 도구가 이 프로젝트에서 작업할 때 따라야 하는 규칙. CLAUDE.md의 Session Convention Protocol을 보완한다.

## 코드 작성 전

1. 수정할 파일을 **먼저 Read 도구로 읽고** 기존 패턴을 파악한다
2. `architecture.md`의 P2 모듈 구조와 P3 의존성 방향을 위반하지 않는지 확인
3. 관련 테스트 파일 존재 여부 확인 (`services/{name}/tests/` 또는 `frontend/e2e/`)
4. **3개 이상 파일 수정 시** → `EnterPlanMode`로 한글 계획서 제시 후 승인받고 진행
5. 다른 마이크로서비스의 데이터가 필요하면 `architecture.md` P5의 두 가지 통신 방식 중 하나를 선택 (Kong 경유 httpx 또는 Kafka 이벤트)

## 코드 작성 중

1. **모든 함수/클래스/복잡한 로직에 한글 주석을 작성한다**
   - 함수/클래스 위에 역할과 목적
   - 복잡한 로직에는 단계별 설명
   - "왜(why)" 이렇게 하는지 중심
2. 데이터 모델은 Pydantic v2 BaseModel 사용 — `model_config = ConfigDict(...)`
3. 새 API 엔드포인트:
   - `schemas/`에 요청/응답 모델 먼저 정의
   - `routers/`에 입력 검증 + Service 호출만
   - 비즈니스 로직은 `services/`에
4. 새 LLM 호출:
   - ai-service 외부에서는 ai-service의 엔드포인트를 Kong 경유로 호출
   - ai-service 내부에서는 `llm_service.LLMService` 클래스만 사용
5. 새 Kafka 이벤트:
   - 스키마는 `shared/schemas/events.py`에만 정의
   - 발행은 `shared/common/kafka.py:KafkaProducer`
   - 토픽명은 `{aggregate}.{action}` 형식
6. 새 DB 테이블:
   - `tb_*` 접두사
   - 감사열 3종(`ins_dt`, `upd_dt`, `ins_user_id`) 의무
   - `database/scripts/`에 SQL 또는 Alembic 마이그레이션 추가
7. 프론트엔드 새 API 호출:
   - `frontend/lib/api/{service}.ts`에 함수 추가
   - React Query 훅으로 컴포넌트에 노출
   - 컴포넌트는 `apiClient` 직접 호출 금지

## 코드 작성 후

1. **백엔드**: `cd services/{service} && ruff check . && ruff format .`
2. **프론트엔드**: `cd frontend && npx eslint . && npx tsc --noEmit`
3. 관련 테스트 실행 (있는 경우)
4. **sdet-agent를 자동으로 호출**하여 신규 코드의 테스트 커버리지 확보 (CLAUDE.md §2 참조)
5. 의존성 방향 위반 여부 자체 점검
6. 변경 요약을 한글로 작성해 사용자에게 보고

## 커밋 메시지 형식

```
[service-name] 변경내용 (한글 설명)

예시:
[auth-service] JWT refresh 토큰 회전 로직 구현
[competency-service] 점수 계산 시 음수 가중치 방어 로직 추가
[ai-service] Tool Calling 결과 검증 단계 추가
[frontend] 대시보드 RiskAlertsSection 컴포넌트 추가
[shared] StudentCreatedEvent Kafka 스키마 정의
[database] tb_alumni_cohort 인덱스 추가 마이그레이션
[infrastructure] Kong 라우팅에 worknet-service 등록
```

## 에이전트 위임 (CLAUDE.md §2 보강)

| 작업 유형 | 위임 에이전트 | 이유 |
|---|---|---|
| 새 마이크로서비스 추가 | enterprise-architect → backend-specialist | 서비스 경계와 통신 패턴 결정이 우선 |
| 단일 서비스 내 라우터/서비스 수정 | backend-specialist | 단일 도메인 |
| DB 스키마 변경 + 마이그레이션 | database-architect | 데이터 무결성 검증 필요 |
| Next.js 컴포넌트/훅 작성 | frontend-specialist | UI/접근성/성능 |
| 코드 작성 직후 | sdet-agent (자동) | 테스트 커버리지 확보 |
| 기존 서비스 분석/리뷰 | code-analysis-specialist | 코드 작성 X, 분석 전용 |
| 한국어 문서/사용자 데이터 분석 | data-analyst | 통계/시각화 |
| 라이브러리/프레임워크 비교 조사 | research-assistant | 트레이드오프 분석 |

복수 도메인이 걸친 작업은 위 에이전트들을 **병렬로** 호출 (Task 도구 다중 호출).

## 보안 체크 (필수)

다음을 코드에 도입한 흔적이 발견되면 즉시 거부 또는 수정한다.
- SQL injection (raw SQL + 문자열 포매팅)
- XSS (사용자 입력을 dangerouslySetInnerHTML에 그대로 삽입)
- 인증 우회 (보호된 엔드포인트에 `Depends(get_current_user)` 누락)
- 시크릿 하드코딩
- CORS allow_origins=["*"] (개발 환경 외)
- 파일 업로드 시 확장자/MIME 검증 누락
