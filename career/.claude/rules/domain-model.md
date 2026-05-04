# IDINO Career Domain Model Definitions

코드, 변수, API 경로, UI 라벨에서 아래 정의된 용어를 정확히 사용한다. **동의어 혼용 금지**.

## 핵심 엔티티 (테이블 + API 경로)

### Student (학생) — `tb_student`
- PK: `student_id` (학번 문자열, 예: `20244897`)
- 인제대학교 IU-나비 시스템의 사용자 데이터 연동
- API: `/api/v1/students/...`
- **동의어 금지**: user, learner, person → 모두 `student`로 통일

### Competency (역량) — `tb_competency`
- PK: `competency_cd` (역량 코드, 예: `COMP_001`)
- 학생의 8대 핵심역량 (의사소통, 문제해결 등) 정의
- 학생-역량 매핑은 `tb_student_competency`
- API: `/api/v1/competencies/...`
- **동의어 금지**: ability, capacity → `competency`로 통일

### Skill (스킬)
- skill-service에서 메타데이터 관리 (DB 모델 별도 없음)
- Competency의 하위 단위 — 구체적 기술 스킬 (Python, 발표, Excel 등)
- API: `/api/v1/skills/...`
- **주의**: Competency와 Skill은 다른 엔티티 — 절대 혼용하지 않음

### Roadmap (로드맵)
- AI 생성된 단계별 학습/진로 경로
- roadmap-service에서 OpenAI Tool Calling으로 동적 생성
- API: `/api/v1/roadmaps/...`
- 단계 = `step` (NOT phase, NOT stage)

### Risk (위험 신호) — `tb_risk_alert`
- 학생의 학업 부진, 출결, 진로 미설정 등 위험 신호
- risk-service에서 룰 기반 + AI 분석으로 생성
- API: `/api/v1/risks/...`
- **동의어 금지**: warning, alert(엔티티 자체는 risk, 알림 수단이 alert)

### Simulation (시뮬레이션) — `tb_simulation_*`
- "이 진로를 선택하면?"의 가상 시나리오 결과
- simulation-service
- API: `/api/v1/simulations/...`

### Badge (배지)
- 학생의 성취 증빙 (수료증, 자격증, 활동 인증)
- badge-service
- API: `/api/v1/badges/...`

### Alumni (동문) — `tb_alumni_cohort`
- 졸업 동문의 진로 데이터 (코호트 단위)
- alumni-service에서 동문 비교 분석 제공
- API: `/api/v1/alumni/...`
- **단어 주의**: alumni(복수), alumnus(남성 단수), alumna(여성 단수) — 코드는 항상 `alumni`

### Opportunity (기회) — `tb_opportunity`
- 채용 공고, 공모전, 장학금, 인턴십, 교육 프로그램
- opportunity-service
- API: `/api/v1/opportunities/...`
- 하위 분류: `job` / `contest` / `scholarship` / `internship` / `program`

### Portfolio (포트폴리오)
- 학생이 작성한 프로젝트/활동 모음
- portfolio-service
- API: `/api/v1/portfolios/...`

### Coaching (코칭) — `tb_coaching_session`
- 진로 상담 세션 (학생 ↔ Advisor)
- coaching-service
- API: `/api/v1/coaching/...`

### Advisor (지도교수)
- 학생의 진로/학업 지도교수
- advisor-service
- API: `/api/v1/advisors/...`
- **동의어 금지**: counselor, mentor, professor → `advisor`로 통일

### Worknet (워크넷)
- 고용노동부 워크넷의 직업 코드/직무 정보 연동
- worknet-service
- API: `/api/v1/worknet/...`

### Achievement (성취)
- 학생의 성취 이력 (점수, 자격, 수상 등) — Badge와는 별개
- 데이터 출처는 인제대 IU-나비

## 사용자 역할 (Role)

| 역할 코드 | 의미 |
|---|---|
| `student` | 학생 — 자신의 데이터만 조회/수정 |
| `advisor` | 지도교수 — 담당 학생 데이터 조회 |
| `admin` | 관리자 — 전체 시스템 |

JWT의 `role` 클레임에 위 값이 들어간다. `app.shared.common.auth.get_current_user`가 디코딩.

## DB 명명 규칙 (Strict)

| 항목 | 규칙 | 예시 |
|---|---|---|
| 테이블명 | `tb_*` 소문자 스네이크 | `tb_student`, `tb_alumni_cohort` |
| PK 컬럼 | `*_id`(고유 ID) 또는 `*_cd`(코드) | `student_id`, `competency_cd` |
| FK 컬럼 | 참조 테이블의 PK 컬럼명과 동일 | `student_id` (FK to `tb_student`) |
| 감사열 (필수) | `ins_dt`, `upd_dt`, `ins_user_id` | 모든 신규 테이블 |
| 다대다 매핑 테이블 | `tb_{entity_a}_{entity_b}` | `tb_student_competency` |
| 인덱스명 | `ix_{table}_{columns}` | `ix_tb_student_career_goal` |
| 외래키 제약명 | `fk_{table}_{column}` | `fk_tb_student_competency_student_id` |

## API 경로 규칙

- 기본 prefix: `/api/v1/{resource-plural}` (Kong이 strip_path로 제거)
- 컬렉션: `GET /api/v1/students` / `POST /api/v1/students`
- 단일 자원: `GET /api/v1/students/{student_id}`
- 하위 자원: `GET /api/v1/students/{student_id}/competencies`
- 동작 (RPC 스타일은 최소화): `POST /api/v1/roadmaps/generate`
- 모든 응답은 JSON, snake_case (프론트 boundary에서 camelCase로 매핑)

## Kafka 이벤트 명명

| 토픽 | Pydantic 스키마 | 발행 시점 |
|---|---|---|
| `student.created` | `StudentCreatedEvent` | 신규 학생 등록 |
| `student.updated` | `StudentUpdatedEvent` | 학생 정보 변경 |
| `competency.calculated` | `CompetencyCalculatedEvent` | 역량 점수 재계산 |
| `risk.alerted` | `RiskAlertedEvent` | 위험 신호 신규 발생 |
| `roadmap.generated` | `RoadmapGeneratedEvent` | AI 로드맵 생성 완료 |
| `badge.awarded` | `BadgeAwardedEvent` | 배지 획득 |

스키마는 모두 `shared/schemas/events.py`에만 정의.

## 절대 혼용 금지 매핑

| 정확한 용어 | 금지 용어 |
|---|---|
| Student | user, learner |
| Competency | ability, capacity, skill(Skill과 다름) |
| Advisor | counselor, mentor, professor |
| Roadmap step | phase, stage |
| Risk | warning, danger |
| Opportunity | post, job(Opportunity는 더 넓음) |
| Achievement | accomplishment, record |
