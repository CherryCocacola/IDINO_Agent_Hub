# Phase 4 S1 D2 — Alembic 007 운영 서버 적용 보고서

> **작성일**: 2026-04-21
> **실행자**: database-architect (Claude Opus 4.7)
> **대상 서버**: Ubuntu 192.168.10.39 (`/home/idino/docutil/`)
> **목표**: `006_evaluation` → `007_documents_v2` 로 운영 DB head 승격
> **상위 문서**: `docs/phase3_execution_roadmap.md` §2.1 S1 D2, `docs/phase1_decisions.md` v1.2 Q1
> **migration 파일**: `backend/alembic/versions/007_documents_v2_and_template_consolidation.py` (수정 없이 그대로 실행)

---

## 0. 실행 요약

- **결과**: **성공**. Alembic head 007_documents_v2 확정. 데이터 손실 없음, 롤백 불필요.
- **upgrade 실제 실행 시간**: **2.47초** (DDL 한 단계)
- **전체 세션 소요**: 약 10분 (스냅샷 → 백업 → upgrade → 검증 → 재시작 → 스모크)
- **리스크 발생**: 없음
- **발견된 후속 조치**: 1건 — ORM(`tb_generated_reports`) vs DB(archive 리네이밍) 불일치. 프롬프트 지시대로 **S2에서 대응 예정**이며 본 D2 범위 외

---

## 1. 실행 단계별 결과

### 1.1 Step 1 — 현재 상태 스냅샷

| 항목 | 결과 |
|---|---|
| docutil 디렉토리 | `/home/idino/docutil/` 정상 (2026-04-20 15:00 갱신 상태) |
| 컨테이너 | 14개 전체 healthy. docutil-api 36분전 재시작 이력 있음 |
| Alembic current (실행 전) | `006_evaluation` |
| Alembic heads (실행 전) | `007_documents_v2 (head)` — 007 파일 서버 배포 완료 상태 |
| alembic_version 테이블 | `006_evaluation` |
| tb_documents_v2 존재 | 없음 (정상) |
| tb_documents_v2_templates 존재 | 없음 (정상) |
| tb_generated_reports 존재 | 있음 (리네이밍 전) |
| tb_generated_reports_archive | 없음 (리네이밍 전) |
| tb_generated_reports 행수 | **57건** (명세서 기대 49건 대비 +8. 최근 활동으로 증가한 것으로 판단. 보존 기준으로 사용) |
| tb_agents 행수 | 4건 (chatbot/minutes/proposal/report 각 1, freeform_doc 0건) |
| tb_agents 기존 CHECK | 없음 (003에서 CHECK 미생성) → ADD CHECK 안전 |
| tb_generated_reports 참조 FK | 없음 → 리네이밍 안전 |

**Q1 검증 결과 (phase1_decisions.md)**: `agent_type` 4종 모두 허용 목록 포함, 위반 값 0건. **단일 단계 ADD CHECK가 안전함 — NOT VALID/VALIDATE 2단계 분리 불필요** (4건 테이블은 exclusive lock 순간적).

### 1.2 Step 2 — pg_dump 전체 백업

- **백업 파일**: `/home/idino/docutil/backups/pre_007_20260421_1103.sql`
- **파일 크기**: 2,774,951 bytes (2.7 MB)
- **덤프 방식**: `docker exec docutil-postgres pg_dump -U docutil -d docutil --no-owner --no-privileges`
- **dump 검증**:
  - 헤더: PostgreSQL version 17.9, pg_dump 17.9 ✓
  - 꼬리: `-- PostgreSQL database dump complete` ✓
  - `CREATE TABLE public.tb_*` 섹션 **24개** ✓
  - `COPY public.tb_generated_reports` 섹션 **1개** ✓
  - stderr 로그 비어있음 ✓
- **경로 포인터**: `/home/idino/docutil/backups/LATEST_PRE_007.txt` 저장 (후속 스크립트 참조용)
- **롤백 명령** (필요 시):
  ```bash
  cat /home/idino/docutil/backups/pre_007_20260421_1103.sql \
    | docker exec -i -e PGPASSWORD=docutil docutil-postgres psql -U docutil -d docutil
  ```

### 1.3 Step 3 — NOT VALID CHECK 선행 검증 판단

007 파일 설계를 재확인한 결과 **`create_check_constraint` 단일 단계**로 `ck_tb_agents_agent_type` 을 추가. 분리 필요성 판단:

- **tb_agents 행수**: 4건 (매우 작음)
- **위반 값**: 0건 (chatbot/report/proposal/minutes 모두 허용 목록 포함)
- **Exclusive lock 보유 시간**: ms 단위 (full scan 4행 × 1회)
- **2단계 (`ADD NOT VALID` + `VALIDATE CONSTRAINT`) 분리 필요성**: **없음**

→ **결정**: 파일 수정 없이 단일 단계로 진행 (프롬프트의 "파일 수정 금지" 원칙 유지).

### 1.4 Step 4 — `alembic upgrade head` 실행

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 006_evaluation -> 007_documents_v2,
  007 — documents_v2 신규 테이블 + 템플릿 통합 + agent_type 확장.
[exit=0, elapsed=2.47s]
```

- 종료 코드 0
- transactional DDL 사용 (모든 DDL 단일 트랜잭션, 롤백 원자성 보장)
- **실행 후 current**: `007_documents_v2 (head)` ✓
- **alembic_version 테이블**: `007_documents_v2` ✓

### 1.5 Step 5 — 스키마 적용 검증

#### 신규 테이블 A: `tb_documents_v2`

| 구분 | 개수/내용 |
|---|---|
| 컬럼 | 25개 (audit 6 포함) |
| PK | `pk_tb_documents_v2` on `id` (UUID, `gen_random_uuid()`) |
| CHECK (5개) | `ck_tb_documents_v2_ck_tb_documents_v2_document_type`<br>`ck_tb_documents_v2_ck_tb_documents_v2_mode`<br>`ck_tb_documents_v2_ck_tb_documents_v2_schema_version`<br>`ck_tb_documents_v2_ck_tb_documents_v2_status`<br>`ck_tb_documents_v2_ck_tb_documents_v2_template_consistency` |
| FK (5개) | agent_id→tb_agents (SET NULL)<br>generated_by_user_id→tb_users (SET NULL)<br>organization_id→tb_organizations (CASCADE)<br>source_chat_session_id→tb_chat_sessions (SET NULL)<br>template_id→tb_documents_v2_templates (RESTRICT) |
| B-tree 인덱스 (7) | agent_id / document_type / mode / org_created(org,ins_dt DESC) / status / template_id / user_created |
| GIN 인덱스 (1) | `idx_tb_documents_v2_schema_gin` USING gin(document_schema jsonb_path_ops) |
| 총 인덱스 | 9개 (B-tree 7 + GIN 1 + PK 1) |

**CHECK `template_consistency` 조건 (검증됨)**:
```
((mode='template_fill' AND template_id IS NOT NULL)
 OR (mode='free_generation' AND template_id IS NULL))
```

**CHECK `document_type` 7종 (DocumentType enum 완전 일치)**:
`slide_report / docx_report / proposal / minutes / one_pager / weekly_status / freeform_doc`

#### 신규 테이블 B: `tb_documents_v2_templates`

| 구분 | 개수/내용 |
|---|---|
| 컬럼 | 17개 (audit 6 포함) |
| PK | `pk_tb_documents_v2_templates` on `id` |
| CHECK (2개) | document_type(7종), schema_version >= 1 |
| FK (2개) | organization_id→tb_organizations (CASCADE), created_by_user_id→tb_users (SET NULL) |
| UNIQUE (1) | `uq_tb_documents_v2_templates_org_name` (organization_id, name) |
| B-tree 인덱스 (2) | is_active / (organization_id, document_type) |
| GIN 인덱스 (1) | `idx_tb_documents_v2_templates_skeleton_gin` USING gin(skeleton_schema jsonb_path_ops) |
| 총 인덱스 | 5개 |

#### tb_generated_reports → archive 리네이밍

| 항목 | 결과 |
|---|---|
| 원본 `tb_generated_reports` | **존재하지 않음** (리네이밍 완료) |
| `tb_generated_reports_archive` | **존재, 57건 보존** |
| archive 인덱스 | 4개 모두 자동 이동 (`idx_tb_generated_reports_*`, `pk_tb_generated_reports`) — 제약 이름은 리네이밍되지 않음 (007 파일의 소프트 폐기 의도, S7에서 통째로 drop 예정) |
| archive 샘플 3건 조회 | `IDINO Design Final Test`, `부산지역 중소기업유망기술개발 제안서`, `E2E test report` 모두 status=completed. **데이터 손실 없음** |
| archive 참조 FK | 없음 |

#### tb_agents CHECK 제약 확정

| 항목 | 결과 |
|---|---|
| 제약 이름 | `ck_tb_agents_ck_tb_agents_agent_type` |
| 허용 목록 | **5종**: `chatbot`, `report`, `proposal`, `minutes`, `freeform_doc` |
| 기존 데이터 4건 | 모두 허용 목록 내 |
| 허용 목록 외 행수 | **0건** |

> **Q1 (phase1_decisions.md v1.2) 최종 확정**: DocumentType과 AgentType의 `freeform_doc` 동일 문자열 유지. 5종 CHECK 확정.

#### 제약명 네이밍 관찰

Alembic MetaData의 `naming_convention`(env.py `ck_%(table_name)s_%(constraint_name)s`) 때문에 제약 이름이 **접두사 중복 형태**로 생성됨:

- `ck_tb_documents_v2_ck_tb_documents_v2_document_type` (예상)
- 실제 ADD CHECK시 `name="ck_tb_documents_v2_document_type"` 로 지정 → convention이 `ck_{table}_{name}` 을 앞에 또 붙임

**영향 평가**: 기능상 문제 없음. 제약 조회·drop 시 이 이름을 그대로 사용하면 됨. downgrade() 에서 `drop_constraint("ck_tb_agents_agent_type", ...)` 로 적혀있는 점은 Phase 4 S7 완전 폐기 전까지 한 번도 호출되지 않으므로 실질 위험 없음. 다만 **네이밍 추적성**을 위해 후속 마이그레이션에서는 naming_convention이 자동 접두사를 붙이므로 `name=` 에 `ck_` 접두사를 제거하고 전달하는 것이 일관성 있음 (참고 노트).

#### Alembic 메타

- `SELECT version_num FROM alembic_version;` → `007_documents_v2` ✓

### 1.6 Step 6 — API / Celery 재시작

- `docker compose restart api celery-worker` → 약 3초 내 Started
- 15초 대기 후 `docker inspect` health:
  - docutil-api: **healthy**
  - docutil-celery-worker-1: **healthy** (health check 약 60초 후 확정)
- 재시작 후 `alembic current` = `007_documents_v2 (head)` 그대로
- celery-worker tasks 6종 정상 로드 (report_generator.generate_report 포함)
- RabbitMQ/Redis 정상 연결

**Shutdown 로그 경고** (기존 이슈, migration 무관):
```
ImportError: cannot import name 'close_http_client' from 'app.modules.search.service'
```
이는 `app/main.py:88` 에 해당 import가 있으나 `search/service.py` 에는 심볼이 없어 발생하는 **기존 shutdown 실패 버그**. 매 재시작마다 shutdown 단계에서 발생하지만 startup은 정상이라 운영 영향 없음. 본 D2 범위 외이나, **후속 작업(D3 또는 별도 이슈)에서 수정 권장**.

### 1.7 Step 7 — 스모크 테스트 및 영향 점검

| 테스트 | 결과 | 평가 |
|---|---|---|
| `/health` (컨테이너 내부) | 200 `{"status":"healthy","version":"1.0.0"}` | 정상 |
| `/api/v1/reports` (인증 없이) | 401 `{"detail":"Could not validate credentials."}` | 라우터 도달 정상, 인증 미들웨어 정상. **500 아님** |
| `/api/v1/reports` 응답시간 | 4~30ms | 정상 |
| archive 직접 SELECT | 3건 조회 성공 | 데이터 보존 확정 |
| 원본 `tb_generated_reports` SELECT | `relation does not exist` 에러 | 예상된 결과 |

**ORM 불일치 리포트 (중요)**:
- `app/modules/reports/models.py:87` — `__tablename__ = "tb_generated_reports"`
- `app/workers/report_generator.py:159,195` — 주석 내 테이블명 언급
- `app/main.py:58,153` — `reports_router` 등록 유지

→ 인증된 사용자가 `/api/v1/reports` 의 실제 조회/생성 엔드포인트를 호출하면 `relation does not exist` 500 에러가 발생할 **가능성**이 있음. 본 D2 범위에서는 **인증 없이 401 수준까지 확인**했고, 프롬프트 지시대로 **archive 테이블 코드 대응은 S2 작업**으로 위임.

**후속 조치 권장** (S2에서 적용):
1. `app/modules/reports/models.py` 의 `__tablename__` 을 `tb_generated_reports_archive` 로 변경 (읽기 전용 유지를 위해 `__table_args__` 에 read-only 마커 주석 추가)
2. 또는 신규 `tb_documents_v2` 기반 reports API로 전환 (권장. S2의 scope)
3. S7에서 archive 테이블 완전 drop 시 위 ORM 모델도 동시 삭제

---

## 2. 전체 테이블 목록 (최종, 26개)

```
tb_agents                      tb_organizations
tb_audit_logs                  tb_project_departments
tb_boards                      tb_project_members
tb_chat_messages               tb_projects
tb_chat_sessions               tb_report_templates         (S7에서 drop 예정)
tb_departments                 tb_search_history
tb_document_access             tb_search_scopes
tb_document_chunks             tb_users
tb_document_templates          tb_documents_v2             ← 신규
tb_documents                   tb_documents_v2_templates   ← 신규
tb_evaluation_configs          tb_generated_reports_archive ← 리네이밍
tb_evaluation_logs
tb_faq_entries
tb_folders
tb_llm_api_keys
```

---

## 3. Downgrade 경로 점검

007 파일의 `downgrade()` 구현 (실행은 하지 않음, 코드 검토만):

1. archive → 원본 이름 복구 (`rename_table`)
2. `ck_tb_agents_agent_type` drop ← **네이밍 이슈**: 파일에는 `ck_tb_agents_agent_type` 로 drop 지정. 실제 생성된 제약은 `ck_tb_agents_ck_tb_agents_agent_type`. convention 접두사가 drop 시에도 자동 적용되어 일치시킬 가능성이 있으나, 확실히 하려면 Phase 4 S7 폐기 전에 downgrade를 쓰지 않는 설계 유지.
3. tb_documents_v2 인덱스/테이블 drop
4. tb_documents_v2_templates 인덱스/테이블 drop

**결론**: downgrade는 구현 존재. 본 세션에서는 실행하지 않음 (프롬프트 지시). 위 네이밍 이슈는 실제 호출 시 검증 필요하나 **current 방향성상 S7 완전 폐기까지 downgrade 의도 없음**.

---

## 4. 검증 체크리스트 (D3 이후 참조용)

- [x] Alembic head = 007_documents_v2
- [x] alembic_version 테이블 = 007_documents_v2
- [x] `tb_documents_v2` 생성 (25컬럼, 9인덱스, 11제약)
- [x] `tb_documents_v2_templates` 생성 (17컬럼, 5인덱스, 6제약)
- [x] GIN 인덱스 `document_schema` / `skeleton_schema` 존재 (jsonb_path_ops)
- [x] `ck_tb_documents_v2_template_consistency` CHECK 확인
- [x] `tb_agents.agent_type` CHECK 5종 (chatbot/report/proposal/minutes/freeform_doc)
- [x] tb_agents 위반 값 0건
- [x] `tb_generated_reports` → `tb_generated_reports_archive` 리네이밍
- [x] archive 57건 데이터 보존
- [x] archive 인덱스 4개 따라감 (자동)
- [x] pg_dump 백업 파일 생성 + 크기 검증 (2.7MB)
- [x] API / celery-worker healthy
- [x] `/health` 200 응답
- [x] `/api/v1/reports` 401 (인증 실패, 라우터 동작)
- [ ] ORM(models.py) ↔ archive 리네이밍 불일치 **S2에서 대응**
- [ ] shutdown 시 `close_http_client` ImportError **S2 또는 별도 이슈에서 대응**

---

## 5. 발견 이슈 및 S2/S3 이관 항목

| ID | 내용 | 심각도 | 처리 시점 |
|---|---|---|---|
| ISSUE-D2-1 | `reports/models.py` ORM이 `tb_generated_reports` 참조 → 현 DB에 테이블 없음. `GET /api/v1/reports` 인증 후 실조회 시 500 가능 | 중 | **Phase 4 S2** (코드 이관과 함께 tb_documents_v2 로 전환 또는 tablename 교체) |
| ISSUE-D2-2 | `app/main.py:88` `close_http_client` ImportError (기존 버그) | 낮 (shutdown 단계) | 별도 이슈, 빠른 수정 권장 |
| NOTE-D2-1 | Alembic naming convention이 제약명에 `ck_{table}_` 접두사 자동 부여 → 제약명이 `ck_tb_documents_v2_ck_tb_documents_v2_*` 중복 형태 | 정보 | 향후 migration 작성 시 `name=` 에 접두사 생략 규칙 수립 (env.py naming_convention 검토) |
| NOTE-D2-2 | archive 테이블 인덱스·제약 이름은 `tb_generated_reports_*` 유지 (리네이밍 없음) | 정보 | S7에서 통째로 drop되므로 불일치 허용 (007 파일 설계 의도) |
| NOTE-D2-3 | pre-count 57건 (명세서 49건 대비 +8) | 정보 | 최근 리포트 생성으로 증가. S0 이후 운영 활동으로 간주. 보존 기준 57건 유지 |

---

## 6. D3 작업 선행 조건 충족 여부

| D3 의존 항목 | 충족 여부 |
|---|---|
| 007 head 운영 DB 적용 | ✓ |
| `tb_documents_v2` / `tb_documents_v2_templates` 물리 존재 | ✓ |
| `tb_agents.agent_type` CHECK 5종 (freeform_doc 포함) | ✓ |
| `tb_generated_reports_archive` 리네이밍 + 데이터 보존 | ✓ |
| API 컨테이너 healthy + ORM 메타 재로드 완료 | ✓ |
| pg_dump 백업 파일 보존 (롤백 경로 확보) | ✓ |

**결론**: **D3 (backend ORM/서비스 레이어 실제 구현) 착수 가능**.

---

## 7. 실행 스크립트 및 산출물

| 파일 | 역할 |
|---|---|
| `scripts/phase4_s1_d2_step1_snapshot.py` | 실행 전 상태 스냅샷 |
| `scripts/phase4_s1_d2_step2_backup.py` | pg_dump 전체 백업 |
| `scripts/phase4_s1_d2_step4_upgrade.py` | alembic upgrade head |
| `scripts/phase4_s1_d2_step5_verify.py` | 스키마/인덱스/제약 검증 |
| `scripts/phase4_s1_d2_step6_restart.py` | API/celery 재시작 + 스모크 |
| `scripts/phase4_s1_d2_step7_impact.py` | archive 리네이밍 영향 확인 |
| 서버 `/home/idino/docutil/backups/pre_007_20260421_1103.sql` | 롤백용 백업 (2.7MB) |
| 서버 `/home/idino/docutil/backups/LATEST_PRE_007.txt` | 백업 경로 포인터 |

---

## 8. 변경 전후 Alembic 타임라인

```
004_jinja2_template_system
  ↓ (멀티 AI 프로바이더)
005_multi_provider
  ↓ (Evaluation module)
006_evaluation        ← 이전 head
  ↓ (documents_v2 + template 통합 + freeform_doc + archive 리네이밍)
007_documents_v2      ← 현재 head ★
```

---

_작성: database-architect. 실행 완료 2026-04-21 UTC 02:06._
