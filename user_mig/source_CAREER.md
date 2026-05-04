# idino_career — IDINO_Agent_Hub 통합 소스 분석

> **작성일**: 2026-05-04
> **분석 대상**: `D:\workspace\idino_career`
> **목적**: IDINO_Agent_Hub monorepo 통합을 위한 idino_career(CAREER V5) Data Plane 소스 자료
> **참조**: `user_mig/CAREER_V5_TechSpec_Final_EN.md`, `TECHSPEC_PROGRESS.md`, `TABLE_DEFINITION_AND_USAGE.md`, `inje_integration_design.md`, `vp_tb_mapping_analysis.md`

---

## 1. 시스템 한 줄 요약 + 기술 스택 + 18개 MS 카탈로그

**한 줄 요약**: 학생/교수/운영자/어드바이저를 대상으로 5탭 + AI ActionBoard + 학기 스프린트를 제공하는 18개 마이크로서비스 기반 AI 코어 역량 스튜디오. 학생 데이터에 OpenAI GPT-4o-mini Tool Calling + RAG + Structured Outputs를 결합하여 근거 기반 추천을 생성한다.

### 기술 스택

| Layer | 기술 |
|-------|-----|
| Backend | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy 2.0 (asyncio), asyncpg |
| Frontend | Next.js 14.2.18 (App Router, TypeScript), React 18, TailwindCSS, Recharts, @tanstack/react-query, axios |
| DB | PostgreSQL 16, 단일 DB(`postgres`) 내 `idino_career` 스키마, 53+ 테이블 |
| AI | OpenAI `gpt-4o-mini` (chat/completions, tool_calls, JSON Schema response_format), `text-embedding-3-small` (1536d), LangChain 0.3.1 (`langchain-openai`) |
| RAG | pgvector (TechSpec에 명시되었으나 실제 DDL은 미적용 — 코드는 fallback 분기 보유) + PostgreSQL FTS BM25 hybrid (α=0.7) |
| Auth | JWT (jose), bcrypt(passlib), pyotp TOTP/Email OTP MFA, Redis(asyncio) for OTP 캐시 |
| Inter-service | httpx.AsyncClient, Kong API Gateway (`gateway/kong.yml`) |
| Infra | Docker Compose, Kubernetes manifests(`infrastructure/k8s/`), Kafka(`infrastructure/kafka/`, 미사용 추정) |

### 18개 마이크로서비스 카탈로그

| # | 서비스 | 포트 | 책임 | LLM 직접 호출 |
|---|-------|-----|------|:---:|
| 1 | auth-service | 8011 | 로그인, JWT 발급, MFA(TOTP/Email), Redis OTP 캐시 | ✗ |
| 2 | student-service | 8002 | 학생 프로필, 수강이력, 성적, 졸업요건 조회 | ✗ |
| 3 | competency-service | 8003 | 6대 핵심역량 점수/갭 계산, 레이더 차트 데이터 | ✗ (AI 호출은 ai-service 위임) |
| 4 | alumni-service | 8005 | 졸업생 코호트 통계, 성공 패턴 검색, 익명화 벤치마크 | ✗ |
| 5 | ai-service | **8000 + 8006** | Tool Calling, RAG, Structured Outputs, Eval | **✓ (메인 호출자)** |
| 6 | skill-service | 8007 | 스킬 그래프, 스킬 갭 분석, 직무-스킬 매핑 | ✗ |
| 7 | opportunity-service | 8008 | 인턴/공모전/연구실/장학금 마켓플레이스, 추천 | ✗ |
| 8 | coaching-service | 8009 | AI 코칭 루프(Goal/Plan/Checkin/Retro), AI 코칭 대화 | ✗ (`/ai/chat` 위임) |
| 9 | risk-service | 8010 | 학사 위험(학점/선수/시간표) 알림 | ✗ |
| 10 | badge-service | 8012 | 뱃지/스킬 패스포트 발급 | ✗ |
| 11 | simulation-service | 8013 | What-if 시나리오(진로/스킬/과목/타임라인), GPT 기반 분석/추천 | **✓ (직접 호출)** |
| 12 | advisor-service | 8014 | 어드바이저 워크스페이스, 코호트 개입 | ✗ |
| 13 | roadmap-service | 8015 | 4년×2학기 학년 로드맵, AI 로드맵 적용 | ✗ (`/ai/recommendations/tools` 호출) |
| 14 | portfolio-service | 8016 | github/notion/project/paper 아티팩트 관리 | ✗ |
| 15 | privacy-service | 8017 | DSR(데이터주체 권리) 요청, 동의 기록 | ✗ |
| 16 | worknet-service | 8018 | 워크넷 직업적성 코드 매핑 | ✗ |
| 17 | integration-service | 8019 | HRD/대학/워크넷 외부 시스템 커넥터 | ✗ |
| 18 | notification-service | (HTTP 미할당) | 알림 큐, 채널별 발송 | ✗ |

`requirements.txt` 기준 LLM 라이브러리(openai, langchain) 의존을 가진 서비스는 **ai-service, simulation-service, coaching-service** 3개. 단 coaching-service는 `OPENAI_API_KEY`만 settings에 두고 실제 호출 코드는 없으며 `httpx`로 ai-service `/ai/chat`을 호출한다(`coaching_service.py:560-562`).

---

## 2. 현재 완성도 평가

`TECHSPEC_PROGRESS.md`상 **0~12 단계 모두 100%** 표기. 시점은 2026-01-12 시뮬레이션 GPT 통합/PPT 콘텐츠 생성까지 완료. 그러나 실측 결과 다음과 같이 검증된다.

| Phase | 상태 | 실제 검증 |
|-------|-----|----------|
| Phase 0~1 (DB+서비스 DB연결) | 100% | DDL `database/01_schema_create.sql`, `02_techspec_tables.sql` 존재. 53테이블 |
| Phase 2-1 Tool Calling | 100% | `ai-service/app/tools/tool_definitions.py` 4 Tool 등록 |
| Phase 2-2 Structured Outputs | 100% | `JSON_SCHEMA_ACTIONBOARD` 적용 (`tool_definitions.py:11-65`) |
| Phase 2-3 RAG | **부분** | `retrieval_service.py:45-59` pgvector 존재 검사 후 fallback. 실제 DDL에 vector 컬럼 없음(`grep CREATE EXTENSION` 결과 `uuid-ossp`/`pgcrypto`만) → 사실상 BM25/FTS만 동작 |
| Phase 4 Eval System | 100% | `eval_service.py`, `eval_router.py` 구현 |
| Phase 5 MFA | 100% | TOTP+Email OTP 분기 (`auth_service.py`) |
| Phase 6 ActionBoard 분리 | 100% | React.lazy/Suspense |
| Phase P1/P2 (Skill/Opportunity/Coaching/Risk/Badge/Simulation/Advisor) | 100% | 7개 서비스 디렉터리 모두 존재 |
| Phase 7~10 통합/Seed/E2E | 100% | 47개+ seed SQL(`05_seed_*` ~ `60_update_*`) |
| Phase 11 Simulation GPT | 100% | `simulation_service.py:973, 1764` 직접 호출 확인 |
| Phase 12 PPT 콘텐츠 | 100%(주장) | 본 분석에선 별도 PPT 생성 코드 미확인 (TechSpec 외 추가 작업) |

**알려진 미완성 영역**:
- 통합 테스트는 체크리스트 형태로만 존재(`TECHSPEC_PROGRESS.md:453-560`), 자동화된 E2E 미실행
- pgvector 의존 RAG는 코드만 존재하고 실제 DB는 키워드 검색에만 의존
- Kafka(`infrastructure/kafka/`) 디렉토리만 있고 실제 토픽/컨슈머 코드 없음

---

## 3. 도메인 모델 핵심 (스키마 그룹화)

총 53 테이블, `TABLE_DEFINITION_AND_USAGE.md`의 8개 카테고리. 모든 테이블은 `idino_career.tb_*` prefix.

| 그룹 | 테이블(주요) | 용도 |
|------|-------------|------|
| **Master Data (9)** | tb_university / tb_college / tb_department / tb_professor / tb_term / tb_course / tb_prerequisite / tb_professor_course / tb_course_offering | 학사 마스터, audit 컬럼(ins_*/upd_*) 일관 적용 |
| **Student Data (6)** | tb_student / tb_enrollment / tb_grade / tb_grade_summary / tb_cumulative_summary / tb_activity | 학번 기반 PK(`student_id`), UUID로 enrollment/grade 분리 |
| **Competency & Skill (9)** | tb_competency / tb_skill / tb_skill_competency_map / tb_course_competency_map / tb_student_competency / tb_student_skill / tb_skill_gap_analysis / tb_skill_relation / tb_role_skill_map | 6대 역량 + 35+ 스킬 + 직무 매핑 |
| **Activity & Achievement (3)** | tb_program / tb_activity / tb_achievement | Excel 포맷(title/issuer/issue_date/level/competency_contributions JSONB) |
| **Job & Alumni (3)** | tb_role / tb_alumni_cohort / tb_success_pattern | 코호트 익명화 통계, 룰 기반 패턴(rules/features/lift) |
| **Auth (2)** | tb_user / tb_user_session | bcrypt 해시, role_level 단일 필드 RBAC |
| **AI Operations (3)** | tb_recommendation_run / tb_recommendation_item / tb_eval_feedback | 추천 실행 로그, prompt/policy/model_version은 TechSpec엔 있으나 별도 미생성 |
| **P1 Extensions (9)** | tb_opportunity, tb_opportunity_recommendation, tb_opportunity_application / tb_coaching_goal, tb_coaching_plan, tb_coaching_checkin, tb_coaching_retrospective / tb_risk_alert, tb_prerequisite_rule | 마켓플레이스 + 코칭 4단계 루프 + 위험 알림 |
| **P2 Extensions (10)** | tb_badge, tb_student_badge, tb_skill_passport / tb_simulation_scenario, tb_scenario_comparison / tb_advisor, tb_advisor_assignment, tb_advisor_intervention, tb_advisor_note, tb_cohort_snapshot | 시뮬레이션 + 어드바이저 워크스페이스 |
| **추가 7** | tb_notification, tb_notification_preferences, tb_worknet_sessions, tb_worknet_results, tb_data_subject_request, tb_consent_record, tb_portfolio | 횡단 서비스 |

**Evidence 스키마**: `recommendation_evidence`/`evidence_id`는 TechSpec(`CAREER_V5_TechSpec_Final_EN.md:255-268`)에 정의되어 있으나 별도 테이블이 아니라 `tb_recommendation_item`에 JSONB로 저장되는 구조.

**핵심 불변규칙**: 모든 추천은 `evidence[]` 배열을 포함해야 함(TechSpec 3.1). `retrieval_method` 컬럼이 `tb_recommendation_*`에 존재(`02_techspec_tables.sql:459`).

---

## 4. MS 간 통신 패턴

| 항목 | 채택 |
|------|-----|
| 프로토콜 | **REST(HTTP/JSON)만 사용**. gRPC/메시지큐 없음 |
| 라이브러리 | `httpx.AsyncClient(timeout=N.0)` per-request 인스턴스화 (anti-pattern, 연결 풀 미공유) |
| 서비스 디스커버리 | 환경변수 기반 (`STUDENT_SERVICE_URL`, `AI_SERVICE_URL`, …) |
| API Gateway | **Kong** (`gateway/kong.yml`) — 16개 라우트 등록, `/api/v1/{resource}` → 서비스 매핑 |
| Rate Limiting | Kong plugin `rate-limiting` 분당 100 (전역) |
| CORS | Kong plugin `cors`, `origins: ["*"]` (취약) |
| 인증 전파 | `shared/common/auth.py`의 `JWTBearer` — 각 서비스가 auth-service `/auth/verify`로 토큰 검증, 실패 시 로컬 JWT 디코드 fallback |
| 메시지큐 | `infrastructure/kafka/` 디렉터리만 존재, 실제 토픽/컨슈머 미구현 |

**대표 호출 그래프**:
- `frontend → Kong → ai-service`: `/ai/recommendations/rag` (Tool Calling+RAG 메인)
- `ai-service → student-service / competency-service / alumni-service`: ToolExecutor 4개 도구 (`tool_executor.py:30`)
- `coaching-service → ai-service`: `/ai/chat` (코칭 대화 위임 — `coaching_service.py:560-562`)
- `roadmap-service → ai-service`: `/ai/recommendations/tools` (AI 로드맵 — `roadmap_service.py:578-580`)
- `competency-service → ai-service`: `/ai/analyze` (역량 분석 — `competency_service.py:209-211`)

---

## 5. AI 사용 지점 인벤토리 (가장 중요)

### 5-1. 직접 LLM 호출 (AgentHub 위임 1순위)

| # | 서비스:파일:라인 | 함수 | 모델/API | 입력 | 출력 | 제안 AgentHub 에이전트 |
|---|-----------------|------|---------|------|------|----------------------|
| 1 | ai-service:`services/llm_service.py:21-26` | `LLMService.__init__` (LangChain ChatOpenAI) | gpt-4o-mini, temp=0.7, max=2000 | system+user prompt | text | (대체) AgentHub openai-compat 클라이언트로 |
| 2 | ai-service:`services/llm_service.py:90` | `generate_action_recommendations()` | LangChain `ainvoke` | 학생+역량+목표 직업 | JSON 4개 액션 | **`career-action-recommender`** Agent |
| 3 | ai-service:`services/llm_service.py:146` | `analyze_competencies()` | LangChain `ainvoke` | 역량 점수+목표 직업 | JSON(분석/강약점/개선) | **`career-competency-analyzer`** |
| 4 | ai-service:`services/llm_service.py:203` | `chat()` | LangChain `ainvoke` | message+history+context | JSON(response/suggestions) | **`career-chatbot`** |
| 5 | ai-service:`services/llm_service.py:260` | `generate_semester_goals()` | LangChain `ainvoke` | 학생+역량+현재목표 | JSON(goals/ai_suggestions) | **`career-semester-planner`** |
| 6 | ai-service:`services/llm_service.py:317` | `generate_with_tools()` 1차 호출 | OpenAI `chat.completions.create(tools=TOOLS, tool_choice="auto")` | system+user, 4 Tool 정의 | tool_calls 또는 final | **`career-actionboard-orchestrator`** (Tool Calling 그대로) |
| 7 | ai-service:`services/llm_service.py:334` | `generate_with_tools()` 최종 호출 | OpenAI `response_format=json_schema` | full convo | JSON_SCHEMA_ACTIONBOARD 강제 | (위와 동일 Agent의 fan-out) |
| 8 | ai-service:`services/llm_service.py:507, 524` | `generate_with_tools_and_rag()` 2회 호출 | 위 + RAG 컨텍스트 prepend | + Evidence 5건 | 동일 | **`career-rag-actionboard`** |
| 9 | ai-service:`services/embedding_service.py:49` | `embed_text()` | `text-embedding-3-small` 1536d | text | float[1536] | **AgentHub `IEmbeddingService` 위임** (이미 동일 모델) |
| 10 | simulation-service:`services/simulation_service.py:973-981` | `_generate_ai_suggestions()` | OpenAI 직접, gpt-4o-mini, max=2000 | 학생+과목/스킬/활동 | JSON 4개 시나리오 추천 | **`career-simulation-suggester`** |
| 11 | simulation-service:`services/simulation_service.py:1764-1772` | `_generate_ai_analysis()` | OpenAI 직접, temp=0.7, max=1500 | 시나리오+결과+종합점수 | JSON(summary/strengths/risks/recommendations/next_steps) | **`career-simulation-analyzer`** |

### 5-2. 간접(Tool Calling 경유) 사용

ai-service가 다음 4 Tool로 LLM 의도에 따라 학생/역량/동문 데이터를 동적 조회 (`tool_definitions.py:72+`, `tool_executor.py:30`):
- `get_student_profile` → student-service (8002)
- `get_competency_scores` → competency-service (8003)
- `search_alumni_patterns` → alumni-service (8005)
- `check_constraints` → student-service (8002)

이 4 Tool은 AgentHub의 `Tool` 도메인(API 백엔드)으로 그대로 이전 가능. AgentHub `ApiToolExecutor`가 실행하면 ai-service 자체를 제거할 수 있음.

### 5-3. 다른 서비스에서의 ai-service 위임 호출 (이미 위임 형태)

- `coaching-service:560-562` → `POST {AI_SERVICE_URL}/ai/chat` ⇒ AgentHub `/v1/chat/completions`로 직접 라우팅 가능
- `roadmap-service:578-580` → `POST {AI_SERVICE_URL}/ai/recommendations/tools` ⇒ AgentHub Agent 호출
- `competency-service:209-211` → `POST {AI_SERVICE_URL}/ai/analyze` ⇒ Agent 호출
- `opportunity-service` config에 `AI_SERVICE_URL` 정의(`config.py:25`), 실제 호출은 미확인

**전체 LLM 호출 횟수**(직접): **11곳** (ai-service 9 + simulation-service 2). embedding 1곳.

### 5-4. 위임 매핑 권장안 (AgentHub Agent 카탈로그)

| AgentHub Agent | SystemPrompt 출처 | EnableRag | 호출자 |
|---------------|-------------------|:---:|------|
| `career-actionboard-orchestrator` | `tool_definitions.SYSTEM_PROMPT` | ✗ | ai-service `/ai/recommendations/tools` |
| `career-rag-actionboard` | `SYSTEM_PROMPT` + RAG context | **✓** | ai-service `/ai/recommendations/rag` |
| `career-competency-analyzer` | `llm_service.py:115-131` | ✗ | competency-service, frontend |
| `career-action-recommender` | `llm_service.py:49-70` | ✗ | ai-service `/ai/actions/{id}` |
| `career-chatbot` | `llm_service.py:172-184` | ✗ | coaching-service, frontend chat |
| `career-semester-planner` | `llm_service.py:231-241` | ✗ | ai-service `/ai/sprint/{id}` |
| `career-simulation-suggester` | `simulation_service.py` 추천 prompt | ✗ | simulation-service |
| `career-simulation-analyzer` | `simulation_service.py:1724-1740` | ✗ | simulation-service |

모든 Agent의 `Model` 필드는 `gpt-4o-mini`, `ServiceType="openai"` 동일.

---

## 6. 인증/권한

| 항목 | 구현 |
|------|-----|
| 인증 방식 | JWT Bearer (HS256), 30분 access + 7일 refresh |
| 비밀번호 | bcrypt (passlib `CryptContext`) |
| MFA | TOTP(`pyotp`) + Email OTP, Redis 캐시(asyncio) |
| 토큰 페이로드 | `sub, exp, iat, user_id, username, role_level, department_id` (`shared/common/auth.py:14-23`) |
| RBAC | `role_level` 단일 정수 필드. TechSpec(1.2)에 5단계: Student / Advisor / Department Admin / Career Center Admin / System Admin |
| 토큰 전파 | `JWTBearer.__call__` → auth-service `/auth/verify` 호출, 실패 시 `_verify_token_locally()` JWT 디코드 fallback (`auth.py:75-97`) |
| 게이트웨이 인증 | Kong에 `key-auth`/`jwt` plugin **미설정** — 인증은 각 서비스 책임 |
| 비밀 노출 | DB 비밀번호 `"2012"` 하드코딩 (`shared/database/connection.py:23`) |
| CORS | Kong `origins: ["*"]` |

**RBAC 진단**: `role_level`이 정수 1개로만 표현되어 학생/교수/운영자/어드바이저 분기가 명시적이지 않음. AgentHub 통합 시 명시적 enum 또는 AgentHub의 `Role` 엔티티(`UserRole` N:M)와 매핑 필요.

---

## 7. DB 구조

- **단일 DB(`postgres`) 단일 스키마(`idino_career`)** — MS별 DB 분리 안 함. 모든 서비스가 동일 스키마에 직접 접근.
- 각 서비스는 자기 책임 테이블만 R/W하나 물리적 격리는 없음(`TABLE_DEFINITION_AND_USAGE.md` 3장 매핑 참조).
- `pgvector`: TechSpec 4장에 명시, `retrieval_service.py:45` 런타임 검사 로직 존재. 실제 `CREATE EXTENSION vector` 호출은 어떤 SQL에도 없음 → **현재 RAG는 BM25/FTS만 가동**.
- 마이그레이션: ai-service만 `alembic/` 보유, 나머지 서비스는 SQL 파일(`database/01_*.sql`~`60_*.sql`) 직접 적용.
- 시드: 47개+ SQL 파일, `migrate_mssql_to_pg.py`는 인제대 MSSQL → PG 마이그레이션 스크립트.
- audit 컬럼(ins_user_id, ins_dt, ins_user_ip, ins_system_gcd, ins_menu_cd + upd_*) 모든 테이블에 일관 적용.

---

## 8. monorepo 통합 시 변경 필요 항목

### 8-1. LLM 직접 호출 → AgentHub 위임 (Phase 7)

**제거 대상**:
- `ai-service`의 `llm_service.py` (637 LOC) → AgentHub Agent 호출 wrapper로 대체
- `simulation-service`의 `simulation_service.py:973, 1764` → AgentHub `/v1/chat/completions` 직접 호출 (httpx)
- `embedding_service.py` → AgentHub `IEmbeddingService` 또는 OpenAI 호환 endpoint

**추가**:
- AgentHub에 8개 Agent 등록 (위 5-4 표). SystemPrompt는 기존 코드에서 추출.
- 4개 Tool(`get_student_profile` 등)은 AgentHub `Tool` 엔티티 등록 (Type=API). Endpoint는 student/competency/alumni-service로 직접.
- ai-service의 `JSON_SCHEMA_ACTIONBOARD`는 AgentHub Agent의 `ResponseFormat` 필드로 이전 (현재 AgentHub에 해당 필드 미존재 → **신설 필요**).
- coaching/roadmap/competency-service의 `AI_SERVICE_URL` → AgentHub `https://agenthub.idino.co.kr/v1/chat/completions` + API Key 인증으로 전환.

### 8-2. PostgreSQL 인스턴스 통합

- 현재: 단일 DB `postgres`, 단일 스키마 `idino_career`. AgentHub는 SQL Server.
- 통합 후: AgentHub 통합 PostgreSQL `AGENT_HUB` DB의 `idino_career` 스키마로 그대로 이전. 53 테이블 + audit 컬럼 보존.
- AgentHub MSSQL → PG 마이그레이션이 선행되어야 함 (Task #13).
- 이미 보유한 `migrate_mssql_to_pg.py` 패턴 재활용 가능 (인제대→PG에 사용된 그대로).
- `pgvector` extension 활성화는 AgentHub DB 셋업 시 한 번에 추가.

### 8-3. 운영자 화면 분리

career의 운영자 영역은 frontend 라우트 그룹 `(dashboard)` 하부. AI 설정 관련(prompt/Agent/Tool 정의) 화면은 현재 idino_career에 **존재하지 않음** (관리자가 코드에 직접 정의). 따라서:
- AgentHub의 운영자 화면(`/admin`)에서 career 관련 Agent/Tool/PromptVersion을 관리.
- idino_career frontend는 학생/교사/어드바이저 소비자 UI만 유지.
- TechSpec의 prompt_versions/policy_versions/model_versions/eval_cases 관리는 AgentHub의 `ApiUsage` + `BannedWord` + `ExamplePrompt` + 신설 Eval 영역으로 이관.

### 8-4. 인증 — AgentHub와 SSO

- 옵션 A: career의 auth-service 유지, AgentHub와 별개 인증 (단기)
- 옵션 B: AgentHub `IJwtService` 통합 발급, career는 토큰 검증만 (Phase 5+ 권장)
- 토큰 페이로드 통일 필요: AgentHub JWT는 AgentHub `User` 기반, career JWT는 `role_level + department_id`. SSO 도입 시 `department_id`/`role_level` extra claim 합의 필요.
- API Key 발급은 AgentHub에서 일괄 (career → AgentHub 호출 시 API Key 사용).

---

## 9. 미완성 부분 / 기술 부채

| 영역 | 상태 | 통합 시 보강 |
|------|-----|------------|
| pgvector RAG | 코드만 존재, DDL 미적용 | AgentHub 통합 DB에 `CREATE EXTENSION vector` + `tb_course/tb_program/tb_success_pattern`에 `embedding vector(1536)` 컬럼 추가, 백필 |
| 자동화 테스트 | xUnit/pytest 단위 테스트 없음, E2E는 manual 체크리스트 | AgentHub `testing.md` 패턴 따라 pytest + httpx mock 도입 |
| Kafka | 디렉토리만, 토픽 없음 | 미사용 → 삭제 또는 AgentHub Hangfire/SignalR로 흡수 |
| `httpx.AsyncClient` per-request | 18 서비스 전반 anti-pattern | 공유 모듈에 `httpx.AsyncClient` singleton or DI |
| DB 비번 하드코딩 `"2012"` | 6+ 서비스에서 default | env 강제 + secret manager |
| CORS `*` | Kong + 각 서비스 | 도메인 화이트리스트 |
| `role_level` 정수 RBAC | 명시적 enum 없음 | AgentHub `Role` 엔티티 + `UserRole` 매핑으로 교체 |
| `tool_executor.py:30` 30s 고정 timeout | 외부 LLM은 더 길어질 수 있음 | AgentHub `IAiProxyService` 표준 timeout 정책 |
| 다국어 | 백엔드 메시지 한/영 혼재 | AgentHub 규칙 따라 사용자향 메시지 한국어 통일 |
| `tb_recommendation_evidence` | TechSpec 정의 vs 실제 구현 불일치 (JSONB 저장) | AgentHub Eval 모델로 분리 또는 정식 테이블화 |

---

## 10. 위험 요소

| 위험 | 영향 | 완화 |
|------|-----|------|
| **AI 호출 11곳이 prompt 본문을 코드에 하드코딩** | AgentHub Agent로 옮길 때 한국어 prompt 누수 가능, 수정 시 배포 필요 | AgentHub `Agent.SystemPrompt` 필드로 이관 + DB 관리. PromptVersion 테이블도 함께 도입 |
| **JSON Schema(`JSON_SCHEMA_ACTIONBOARD`)는 OpenAI Structured Outputs 의존** | AgentHub의 다중 프로바이더 위임 시 Claude/Gemini는 동일 strict JSON schema 미지원 | AgentHub Agent에 `ServiceType="openai"` 고정 또는 fallback 분기 (Claude는 JSON object mode + 후처리) |
| **Tool Calling 4 Tool이 student/competency/alumni-service 직접 호출** | AgentHub의 Tool은 외부 API 호출이므로 인증/RateLimit이 새로 필요 | AgentHub `ApiToolExecutor`에 JWT/API Key 부착, 내부 서비스 ↔ AgentHub 간 인증 합의 필요 |
| **단일 PG 스키마 `idino_career`** | AgentHub 통합 시 schema 충돌(예: `tb_user`는 AgentHub에도 존재할 수 있음) | 스키마 prefix 유지(`idino_career.tb_user` vs AgentHub `dbo.Users`), Cross-DB FK 금지 |
| **`pgvector` 미적용 상태에서 RAG 동작** | 통합 후 BM25만 작동 → 추천 품질 저하 | 마이그레이션 직후 vector 컬럼 백필을 first-class 작업으로 |
| **inje_navi 등 외부 의존 시스템과의 데이터 동기** (`migrate_mssql_to_pg.py`) | 인제대 학사 시스템과의 일회성 마이그레이션 vs 정기 동기 미정 | integration-service 정책 명확화 필요(현 status: 외부 커넥터만 존재) |
| **53 테이블 audit 컬럼(ins_*/upd_*) AgentHub 표준과 불일치** | AgentHub는 EF Core auto-set CreatedAt/UpdatedAt 사용 | 변환 정책 필요(보존 vs CreatedAt 매핑) |
| **role_level 정수 → AgentHub Role 매핑** | 학생(1)/교수/어드바이저/운영자/시스템 5단계 vs AgentHub `Admin/User` | 명시적 매핑 테이블, 학생용 Role을 AgentHub에 신설 |
| **SimulationService 1764라인 단일 파일 1700+ LOC** | 분리 호출 11곳 중 2곳이 이 파일 → 위임 시 큰 변경 | Strategy 패턴으로 분리 후 위임 |
| **Phase 100% 표기와 실제 구현 격차** (pgvector, 자동테스트, Kafka) | 통합 시 "이미 완료"로 간주하면 회귀 발생 | 통합 첫 sprint에서 위 9장 재검증 |

---

## 부록: 핵심 위치 참조

- AI 호출 메인: `services/ai-service/app/services/llm_service.py:21,90,146,203,260,317,507`
- Tool 정의: `services/ai-service/app/tools/tool_definitions.py:11,72`
- RAG hybrid: `services/ai-service/app/services/retrieval_service.py:45,61`
- Embedding: `services/ai-service/app/services/embedding_service.py:30,49`
- Simulation GPT: `services/simulation-service/app/services/simulation_service.py:51,973,1764`
- Coaching → AI 위임: `services/coaching-service/app/services/coaching_service.py:560-562`
- Roadmap → AI 위임: `services/roadmap-service/app/services/roadmap_service.py:578-580`
- Competency → AI 위임: `services/competency-service/app/services/competency_service.py:209-211`
- JWT 공유: `shared/common/auth.py:14,75`
- DB 공유: `shared/database/connection.py:17,23`
- Kong 라우트: `gateway/kong.yml:1-303`
- 테이블 정의 마스터: `user_mig/TABLE_DEFINITION_AND_USAGE.md`
- Phase 진행 마스터: `user_mig/TECHSPEC_PROGRESS.md`
- 통합 설계 마스터: `user_mig/inje_integration_design.md`, `user_mig/vp_tb_mapping_analysis.md`
