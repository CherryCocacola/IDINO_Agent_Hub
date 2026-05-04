# DocUtil — Phase 1 DB 설계 기준선 (database-architect)

> **작성일**: 2026-04-19
> **작성자**: database-architect (Claude Opus 4.7)
> **상위 문서**: `docs/phase1_architecture.md` 부록 E.1
> **상태**: Phase 1 설계 기준선 확정. Alembic 실행·데이터 이관은 Phase 4 에서 수행.

---

## 0. 요약

Phase 1 DB 설계의 중심은 **DocumentSchema(JSONB) 를 SSOT 로 저장하는 `tb_documents_v2`** 와 **Mode B 양식 템플릿 `tb_documents_v2_templates`** 두 신규 테이블이다. 기존 `tb_document_templates`(Jinja2 기반)·`tb_report_templates`(PPTX 파일 기반)·`tb_generated_reports`(보고서 생성 이력)의 **세 갈래 이중화**를 단일 경로로 수렴시킨다.

스키마 수준의 핵심 결정은 다음과 같다.

1. **JSONB + 비정규화 필터 컬럼 하이브리드**. `document_schema` JSONB 에 전체 구조를 보관하되, `document_type / mode / organization_id / status` 등 목록 API 의 필터 축은 독립 컬럼으로 복제한다. GIN 인덱스만으로는 B-tree 범위 스캔을 이기기 어렵다.
2. **`schema_version INT NOT NULL`** 컬럼으로 JSONB 스키마 메이저 버저닝. 향후 v1.1 필드 추가는 서비스 레이어에서 loader 로 처리하되, 메이저 변경은 row-level 에서 구분 가능하도록 만든다.
3. **마이그레이션은 단계적 소프트 폐기**. 기존 `tb_generated_reports` → `*_archive` 리네이밍 (Phase 4 S4), 기존 `tb_document_templates` 는 S4 에 반자동 변환 후 존치 → S7 에 drop. 데이터 손실 없는 되돌리기 가능한 경로만 채택.
4. **파일명 충돌 회피**. 사용자 요청 원문은 "Alembic 006" 이었으나 이미 `006_evaluation_module` 이 존재하여 **007** 로 승격. 콘텐츠·범위는 동일. (`backend/alembic/versions/007_documents_v2_and_template_consolidation.py`)

---

## 1. 신규 테이블 DDL

### 1.1 `tb_documents_v2`

"생성된 문서" 본체. 보고서·회의록·제안서·자유문서를 하나의 엔티티로 통합한다.

```sql
CREATE TABLE tb_documents_v2 (
    -- 공통 (Base 에서 제공)
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ins_dt                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    ins_user                 UUID,
    ins_ip                   VARCHAR(45),
    upd_dt                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    upd_user                 UUID,
    upd_ip                   VARCHAR(45),

    -- JSONB 스키마 버저닝
    schema_version           INTEGER NOT NULL DEFAULT 1,

    -- 비정규화 필터 컬럼 (JSONB 사본)
    document_type            VARCHAR(32)  NOT NULL,  -- slide_report | docx_report | proposal | minutes | one_pager | weekly_status | freeform_doc
    mode                     VARCHAR(20)  NOT NULL,  -- free_generation | template_fill

    -- 관계
    organization_id          UUID NOT NULL REFERENCES tb_organizations(id) ON DELETE CASCADE,
    generated_by_user_id     UUID REFERENCES tb_users(id)             ON DELETE SET NULL,
    agent_id                 UUID REFERENCES tb_agents(id)            ON DELETE SET NULL,
    template_id              UUID REFERENCES tb_documents_v2_templates(id) ON DELETE RESTRICT,
    source_chat_session_id   UUID REFERENCES tb_chat_sessions(id)     ON DELETE SET NULL,

    -- 출처 문서 (FK 대신 ARRAY; 대량/선택 삭제 비용 회피)
    source_document_ids      UUID[],

    -- 상태 / 식별
    title                    VARCHAR(512) NOT NULL,
    status                   VARCHAR(20)  NOT NULL DEFAULT 'draft',   -- draft | generating | completed | error | archived
    error_message            TEXT,
    completed_at             TIMESTAMPTZ,

    -- LLM 통계 (집계용 사본)
    llm_provider             VARCHAR(32),
    llm_model                VARCHAR(128),
    prompt_tokens            INTEGER,
    completion_tokens        INTEGER,

    -- DocumentSchema 본체
    document_schema          JSONB NOT NULL,

    -- 제약
    CONSTRAINT ck_tb_documents_v2_document_type
        CHECK (document_type IN ('slide_report','docx_report','proposal','minutes',
                                 'one_pager','weekly_status','freeform_doc')),
    CONSTRAINT ck_tb_documents_v2_mode
        CHECK (mode IN ('free_generation','template_fill')),
    CONSTRAINT ck_tb_documents_v2_status
        CHECK (status IN ('draft','generating','completed','error','archived')),
    CONSTRAINT ck_tb_documents_v2_schema_version
        CHECK (schema_version >= 1),
    CONSTRAINT ck_tb_documents_v2_template_consistency
        CHECK ((mode = 'template_fill' AND template_id IS NOT NULL)
            OR (mode = 'free_generation' AND template_id IS NULL))
);
```

### 1.2 `tb_documents_v2_templates`

Mode B 양식 채우기 템플릿. `skeleton_schema` 는 `locked=true` 컴포넌트가 포함된 DocumentSchema 이다.

```sql
CREATE TABLE tb_documents_v2_templates (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ins_dt                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    ins_user                 UUID,
    ins_ip                   VARCHAR(45),
    upd_dt                   TIMESTAMPTZ NOT NULL DEFAULT now(),
    upd_user                 UUID,
    upd_ip                   VARCHAR(45),

    organization_id          UUID NOT NULL REFERENCES tb_organizations(id) ON DELETE CASCADE,
    name                     VARCHAR(255) NOT NULL,
    description              TEXT,
    document_type            VARCHAR(32)  NOT NULL,
    schema_version           INTEGER NOT NULL DEFAULT 1,

    skeleton_schema          JSONB NOT NULL,
    slot_definitions         JSONB,            -- [{anchor, category, description, default_value, required}]
    sample_prompt            TEXT,

    is_active                BOOLEAN NOT NULL DEFAULT true,
    created_by_user_id       UUID NOT NULL REFERENCES tb_users(id) ON DELETE SET NULL,

    CONSTRAINT ck_tb_documents_v2_templates_document_type
        CHECK (document_type IN ('slide_report','docx_report','proposal','minutes',
                                 'one_pager','weekly_status','freeform_doc')),
    CONSTRAINT ck_tb_documents_v2_templates_schema_version CHECK (schema_version >= 1),
    CONSTRAINT uq_tb_documents_v2_templates_org_name UNIQUE (organization_id, name)
);
```

`slot_definitions.category` 는 `session_auto`·`user_input`·`ai_generated` 3 종. 기존 Jinja2 템플릿의 변수 카테고리 분류 의미를 그대로 계승한다.

### 1.3 `tb_agents` CHECK 제약 확장

기존 `tb_agents.agent_type VARCHAR(20)` 에는 CHECK 제약이 없었다 (003 migration 시점 실수로 추정). 본 migration 에서 처음으로 5종 enum 을 강제한다.

```sql
ALTER TABLE tb_agents ADD CONSTRAINT ck_tb_agents_agent_type
    CHECK (agent_type IN ('chatbot','report','proposal','minutes','freeform_doc'));
```

- `VARCHAR(20)` 길이 확인: 가장 긴 `freeform_doc` 이 12자이므로 수용 가능.
- 기존 데이터에 위 5 종 외 값이 존재하면 제약 추가가 실패한다. Phase 4 S0 점검 항목에 "`SELECT DISTINCT agent_type FROM tb_agents` 결과 검증" 을 추가해야 한다.

### 1.4 `tb_generated_reports` → `*_archive` 리네이밍

- 읽기 전용 이력 보존용. 신규 insert 경로는 `modules/reports` 폐기와 동시에 차단.
- 외래키·인덱스 이름은 개명하지 않는다 (Phase 4 S7 에서 테이블 통째로 drop 예정).
- downgrade 는 단순 역-rename.

---

## 2. 인덱스 전략 및 근거

### 2.1 `tb_documents_v2` 인덱스

| 이름 | 타입 | 컬럼 | 근거 |
|---|---|---|---|
| `idx_tb_documents_v2_org_created` | B-tree | `(organization_id, ins_dt DESC)` | 목록 API 기본 경로. 최근 문서 N 건 조회 커버. 조직별 데이터 분리가 가장 선행하는 필터. |
| `idx_tb_documents_v2_user_created` | B-tree | `(generated_by_user_id, ins_dt DESC)` | "내가 만든 문서" 페이지. covering index 에 가까움. |
| `idx_tb_documents_v2_document_type` | B-tree | `(document_type)` | 회의록/제안서 등 타입별 목록. 카디널리티 7 이나 필터 빈도 매우 높음. |
| `idx_tb_documents_v2_mode` | B-tree | `(mode)` | Mode A vs B 통계. |
| `idx_tb_documents_v2_status` | B-tree | `(status)` | `generating` 상태 모니터링/워커 큐 보조. |
| `idx_tb_documents_v2_agent_id` | B-tree | `(agent_id)` | 에이전트별 이용량. |
| `idx_tb_documents_v2_template_id` | B-tree | `(template_id)` | Mode B 템플릿별 생성 이력. |
| `idx_tb_documents_v2_schema_gin` | **GIN (jsonb_path_ops)** | `(document_schema)` | JSONB 컨테인먼트 쿼리 (특정 컴포넌트 타입 포함 문서 검색, anchor 검색, locked 플래그 기반 감사). |

**`jsonb_path_ops` 선택 근거**: 기본 GIN 인덱스는 `?`·`?&`·`@>`·`@?`·`@@` 를 전부 지원하지만 크기가 크고 쓰기 비용이 높다. DocUtil 은 `@>` 중심 (컴포넌트 타입 포함·anchor 포함) 이 우세하므로 `jsonb_path_ops` 로 약 30~40% 인덱스 크기를 절감한다. `?` 키 존재 쿼리가 실측 후 필요하다고 판단되면 보조 `GIN` (기본 opclass) 을 추가한다.

**함수 기반 인덱스 후보 (Phase 4 관찰 후 활성화)**:

```sql
-- 인용(Citation) 보유 문서만 빠르게 필터.
CREATE INDEX idx_tb_documents_v2_has_citations
  ON tb_documents_v2 ((jsonb_array_length(document_schema->'metadata'->'citations') > 0))
  WHERE jsonb_array_length(document_schema->'metadata'->'citations') > 0;

-- degraded_components 가 비어있지 않은 문서 (HWPX 품질 저하 감사).
CREATE INDEX idx_tb_documents_v2_has_degraded
  ON tb_documents_v2 ((jsonb_array_length(document_schema->'metadata'->'degraded_components') > 0))
  WHERE jsonb_array_length(document_schema->'metadata'->'degraded_components') > 0;
```

두 인덱스 모두 **부분 인덱스 (partial)** 로 선언하여 미사용 행은 제외한다. Phase 4 에서 `pg_stat_statements` 관찰 후 선택 활성화.

### 2.2 `tb_documents_v2_templates` 인덱스

| 이름 | 타입 | 컬럼 | 근거 |
|---|---|---|---|
| `idx_tb_documents_v2_templates_org_type` | B-tree | `(organization_id, document_type)` | 관리자 페이지의 템플릿 목록 기본 필터. |
| `idx_tb_documents_v2_templates_is_active` | B-tree | `(is_active)` | 활성 템플릿만 노출되는 플로우 빈도 높음. |
| `idx_tb_documents_v2_templates_skeleton_gin` | GIN (jsonb_path_ops) | `(skeleton_schema)` | slot anchor 검색·컴포넌트 타입 감사. |
| `uq_tb_documents_v2_templates_org_name` | UNIQUE B-tree | `(organization_id, name)` | 조직 내 이름 충돌 방지. |

---

## 3. JSONB 쿼리 성능 분석

### 3.1 전제

- 단일 문서 JSONB 크기: 페이지 20 × 컴포넌트 10 = 200 컴포넌트.
  - 평균 컴포넌트 크기 ~500 bytes → 1 문서 ~100KB JSONB.
  - PostgreSQL 17 TOAST 임계 2KB 초과 → 대부분 외부 TOAST 테이블로 저장.
- 예상 규모: 첫해 10만 건, 3년 내 100만 건.
- 목표 P95 지연: 단건 조회 < 20ms, 목록 조회 (20 건 페이지네이션) < 100ms.

### 3.2 대표 쿼리 예시

**Q1 — 조직의 최근 회의록 20 건 (페이지네이션)**

```sql
SELECT id, title, ins_dt, status
  FROM tb_documents_v2
 WHERE organization_id = :org
   AND document_type  = 'minutes'
 ORDER BY ins_dt DESC
 LIMIT 20 OFFSET :offset;
```

- 실행 계획 (예측): `idx_tb_documents_v2_org_created` 인덱스 스캔 → `document_type` 필터 `BitmapAnd`. 선행 컬럼 카디널리티(org) 가 높으므로 필터 효율 충분.
- **개선**: 필요 시 `(organization_id, document_type, ins_dt DESC)` 복합 인덱스 추가. 단, 현재 `document_type` 카디널리티(7) 가 낮아 이득이 크지 않을 전망. pg_stat_statements 관찰 후 결정.

**Q2 — DataTable 을 포함한 문서 검색 (컴포넌트 타입 포함 질의)**

```sql
SELECT id, title
  FROM tb_documents_v2
 WHERE organization_id = :org
   AND document_schema @> jsonb_build_object(
         'pages', jsonb_build_array(
           jsonb_build_object(
             'components', jsonb_build_array(
               jsonb_build_object('type','DataTable')
             )
           )
         )
       );
```

- 실행 계획: `idx_tb_documents_v2_schema_gin` (jsonb_path_ops) 로 `@>` containment 인덱스 스캔. `organization_id` 는 rechecked filter.
- P95 예상 < 80ms (100만 건 기준). GIN 인덱스 페치 후 row recheck 가 병목이 될 수 있음.

**Q3 — locked 컴포넌트가 편집된 흔적(무결성 감사)**

```sql
SELECT d.id, d.title
  FROM tb_documents_v2 d
  JOIN tb_documents_v2_templates t ON t.id = d.template_id
 WHERE d.mode = 'template_fill'
   AND jsonb_path_exists(
         d.document_schema,
         '$.pages[*].components[?(@.locked == true)]'
       )
   AND NOT jsonb_path_exists(
         t.skeleton_schema,
         '$.pages[*].components[?(@.locked == true)]'
       );
```

- `jsonb_path_exists` 는 GIN 으로 직접 가속되지 않지만, 선행 `mode` B-tree 필터 후 행 수가 작아 문제되지 않음.
- 비상 감사용이므로 P95 목표 외.

### 3.3 P95 < 100ms 전략

1. **비정규화 필터 컬럼 우선**. 목록 API 가 JSONB 내부로 들어가지 않게 Pydantic 응답 직렬화 단계에서 `document_schema->'pages'->0->>'title'` 같은 경로 접근을 금지하고, 필요한 필드는 모두 독립 컬럼에 사본을 유지한다.
2. **페이지네이션은 keyset (`(ins_dt, id) < (:last_ins_dt, :last_id)`)** 권장. OFFSET 성장 문제 회피.
3. **전용 컬럼으로 덮을 수 없는 집계 (컴포넌트 사용 통계 등)** 는 **materialized view** 로 밤마다 갱신. 실시간 필요 없음.
4. **JSONB payload 자체는 목록에서 반환 금지**. 프리뷰 화면에서 단건 fetch 시에만 포함.
5. **PostgreSQL 17 jsonb_path_ops + work_mem ≥ 16MB** 권장.

### 3.4 `pg_stat_statements` 모니터링 후보

- GIN recheck 비용이 높은 쿼리 (`document_schema @>` 사용 쿼리 top 10).
- OFFSET > 10000 쿼리.
- `document_schema->'metadata'->'citations'` 경로 접근 빈도 — 임계치 넘으면 부분 인덱스 활성화.

---

## 4. 데이터 마이그레이션 전략

| 기존 객체 | Phase 1 결정 | 실행 시점 | 왜 |
|---|---|---|---|
| `tb_generated_reports` | **리네이밍 → `tb_generated_reports_archive`** (본 007 migration 에 포함) | Phase 4 S4 | 이력 보존 + 읽기 전용. 신규 쓰기는 중단. Phase 4 S7 에서 완전 drop. 손실 없는 되돌리기 가능. |
| `tb_report_templates` | **존치 → Phase 4 S7 drop** | S7 | PPTX 파일 템플릿은 이제 DocumentSchema+IDINO 마스터 조합으로 대체. 자동 변환 시도 시 결과 품질 보장 어려움 → 관리자 재작성 전제. S7 이전까지 read-only 로 운영. |
| `tb_document_templates` (Jinja2) | **반자동 변환 → `tb_documents_v2_templates`**, 이후 S7 drop | S4~S7 | `.docx/.pptx` 원본 + `jinja2_variables` dict 를 파싱해 DocumentSchema skeleton 으로 변환. 16 개 템플릿 중 상위 5 개를 우선 변환, 나머지는 관리자 수동 재작성. S5 중에도 신규 업로드 경로 read-only 유지. |
| `tb_chat_sessions.agent_id`, `tb_generated_reports.agent_id` | **tb_agents FK 유지** | 변경 없음 | `tb_agents` 는 계속 사용. agent_type 만 확장. |
| `tb_agents` | **agent_type CHECK 추가** (007 포함) | Phase 4 S1 이전 | 기존 레코드 값 사전 점검 후 적용. |

### 4.1 변환 스크립트 (개요, S4 에서 구현)

```
for row in tb_document_templates:
    parsed_docx = parse_docx_template(row.template_storage_path)
    skeleton = build_skeleton_from_parsed(
        parsed_docx,
        jinja2_variables=row.jinja2_variables,
    )
    insert tb_documents_v2_templates(
        organization_id=row.organization_id,
        name=row.name,
        document_type=infer_document_type(row.template_type),
        skeleton_schema=skeleton,           # locked=true 컴포넌트 포함
        slot_definitions=to_slot_defs(row.jinja2_variables),
        sample_prompt=row.sample_prompt,
        created_by_user_id=row.created_by,
    )
```

변환 실패 시 알림 → 관리자 수동 재작성. 성공·실패 레코드는 별도 운영 테이블(예: `tb_template_migration_log`, S4 scope) 에서 관리.

### 4.2 Phase 4 스프린트별 데이터 이관 타임라인

| 시점 | 조치 | 되돌리기 |
|---|---|---|
| S1 이전 | `007_documents_v2_*` 적용 (본 파일). 빈 테이블 생성 + `tb_generated_reports` 리네이밍 | downgrade 존재 |
| S4 | Jinja2 템플릿 자동 변환 스크립트 실행 (실패 목록 보존) | 변환 결과 행만 delete |
| S5 완료 | 새 경로 검증 → 구 `tb_document_templates` **write-lock** (업로드 API disable) | 앱 레벨 플래그 |
| S7 | `tb_document_templates`, `tb_report_templates`, `tb_generated_reports_archive` drop | Alembic `008` |

---

## 5. 리스크 매트릭스

| # | 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|---|
| D1 | `document_schema` JSONB 크기가 TOAST 임계를 자주 초과하여 `SELECT *` 성능 저하 | 중 | 중 | 목록 API 는 `document_schema` 컬럼 절대 미조회. SQLAlchemy `defer()` 규칙 레이어 강제. |
| D2 | GIN 인덱스 쓰기 비용으로 대량 생성 워크로드(Mode A batch) 지연 | 낮 | 중 | jsonb_path_ops 선택으로 쓰기 비용 이미 낮음. 워커 배치 처리 시 `SET LOCAL enable_gin=off` 불필요 — row 단위 insert 유지. |
| D3 | 기존 `tb_agents.agent_type` 에 "assistant" 등 예기치 않은 값 존재 → CHECK 추가 실패 | 중 | 낮 | Phase 4 S0 점검에서 `SELECT DISTINCT agent_type FROM tb_agents` 확인 및 데이터 정합성 작업 선행. |
| D4 | `tb_documents_v2 → tb_documents_v2_templates` FK 로 인한 템플릿 삭제 불가 (`ON DELETE RESTRICT`) | 중 | 낮 | 의도된 제약. 사용 중 템플릿은 `is_active=false` soft-disable 로만 처리. |
| D5 | 기존 16 개 Jinja2 템플릿 자동 변환 실패율 > 50% | 중 | 중 | 우선 상위 5 개 수동 변환. 운영 대시보드에 실패 목록 노출. phase1_architecture R3 와 동일. |
| D6 | `source_document_ids UUID[]` 가 FK 가 아니어서 orphan 참조 가능 | 낮 | 낮 | 애플리케이션 레벨 `joinedload` 시점에 존재 확인 + UI 에 "원본 삭제됨" 표시. 대안(N:M 조인 테이블)은 비용 대비 이득 낮음. |
| D7 | `schema_version` B-tree 인덱스 없음 → 전체 재생성 마이그레이션 시 풀스캔 | 낮 | 낮 | 단일 마이그레이션 배치에서만 발생. 수행 시 `CREATE INDEX CONCURRENTLY` 로 임시 인덱스 부여 후 drop. |
| D8 | downgrade 경로에서 `tb_generated_reports_archive` 안의 `agent_id` FK 가 `tb_agents` 변경과 충돌 | 낮 | 중 | 007 downgrade 는 리네이밍 되돌리기만 수행. FK 는 변경 없음. |

### 5.1 Top 3

1. **D3** — `tb_agents.agent_type` CHECK 추가 실패 가능성. Phase 4 S0 에서 데이터 점검을 선행 조건으로 못박는다.
2. **D5** — Jinja2 템플릿 자동 변환 실패율. S4 시작 전 PoC 로 실패율을 실측하고, 50% 초과 시 관리자 수동 재작성 전략으로 선회한다.
3. **D1** — JSONB TOAST 로 인한 `SELECT *` 패턴 오용. ORM 레이어에서 `defer("document_schema")` 를 기본값으로 설정하고, 명시적 `undefer` 만 허용하도록 코드 리뷰 체크리스트 추가 (S1 DoD).

---

## 6. PostgreSQL 17 관련 주의사항

- **row 제약**: PostgreSQL row 크기 한계 8KB(페이지 크기) 이지만 JSONB 는 TOAST 로 외부 저장되므로 실용적 상한은 메모리·IO.
- **JSONB 인덱스 크기**: jsonb_path_ops 기준 원본의 약 20~30%. 100만 문서 × 100KB = 100GB 원본 기준 GIN 인덱스 약 25GB. 디스크 계획 필요.
- **advisory lock**: 본 migration 은 단순 CREATE/ALTER/RENAME 이므로 global advisory lock 불필요. 단, 운영 중 적용 시에는 `SET lock_timeout = '5s'` 로 래핑하여 긴 DDL 대기 회피.
- **`ALTER TABLE ... ADD CONSTRAINT CHECK ... NOT VALID`** 경로: `tb_agents` CHECK 는 현재 데이터가 위반 가능. 운영 적용 시 `NOT VALID` 로 즉시 추가 → `VALIDATE CONSTRAINT` 로 분리 수행하는 것이 downtime-free. 007 draft 에는 단순 `create_check_constraint` 로 두었으므로, Phase 4 적용 단계에서 이 2단계 절차로 변경한다.
- **백업**: 007 적용 전 full backup. downgrade 는 `tb_generated_reports_archive` → `tb_generated_reports` 로직만 포함하며 데이터 손실 없음.

---

## 7. ORM 모델 및 파일 산출물

- `backend/app/modules/documents_v2/__init__.py` — 빈 패키지 초기화
- `backend/app/modules/documents_v2/models.py` — SQLAlchemy 2.0 async `DocumentV2`, `DocumentV2Template`
- `backend/app/modules/documents_v2/schemas.py` — Pydantic v2 DocumentSchema + 22 컴포넌트 (Discriminated Union)
- `backend/alembic/versions/007_documents_v2_and_template_consolidation.py` — Alembic draft

**ORM 설계 결정**:

- `Base` 가 UUID/audit 컬럼을 자동 주입 → 해당 컬럼은 모델에서 재선언하지 않음.
- 컴포넌트 스키마는 `schemas.py` 단일 파일 (architecture.md P2 타협 조항 — §2.7 분리 금지).
- `TwoColumn / ThreeColumn` 의 재귀 union 은 forward ref + `model_rebuild()` 로 해결.
- DataTable·Chart 는 `model_validator` 로 rows/labels 직사각형 검증. LLM 호출 실패 시 `422` 로 조기 차단.

**Pydantic ↔ DB 직렬화 규약**:

- `DocumentSchema.model_dump(mode="json")` 결과를 `document_schema` JSONB 에 그대로 저장.
- 비정규화 컬럼 (`document_type / mode / title / llm_provider / llm_model / prompt_tokens / completion_tokens`) 은 service 레이어에서 JSONB 저장 직전·직후에 `DocumentV2` ORM 필드로 복제.
- 일관성 확인을 위해 `CHECK` 트리거 대신 **쓰기 경로 단일화** (Service) 로 제약. ORM 외 경로로 쓰는 코드는 금지 (P4 원칙).

---

## 8. 미해결 질문 (enterprise-architect 재확인)

1. **`freeform_doc` 문서타입과 `freeform_doc` 에이전트 타입의 이름 충돌 의도 확인**. 본 설계는 둘 다 동일 문자열로 가정했으나, LLM 프롬프트가 둘을 구분해야 할 경우 접두사 분리(예: `agent_type='freeform_doc_agent'`) 가 필요한지.
2. **`tb_documents_v2.source_document_ids` 가 ARRAY 로 유지될지 별도 조인 테이블(`tb_documents_v2_sources`) 로 정규화할지**. phase1_architecture.md §2.8 는 ARRAY 로 암시되어 ARRAY 로 확정했으나, 향후 "이 원본 문서를 참조한 모든 생성물" 역방향 검색 빈도가 높아지면 정규화가 유리.
3. **Mode A 의 `template_id IS NULL` 제약 타이밍**. 현재는 CHECK 로 강제하지만, "템플릿 없이 생성 후 나중에 템플릿으로 끼워 맞추기" 기능이 혹시 필요하면 제약을 trigger 기반 소프트 체크로 전환해야 함.
4. **`tb_report_templates` 의 PPTX 파일 자산 이관 여부**. 현재 MinIO 에 업로드된 PPTX 파일들이 IDINO 마스터가 아닌 **고객사별 보고서 템플릿** 이라면 Phase 4 에서 별도 변환 경로 필요. phase1_architecture.md §5.3 항목 5 는 "IDINO 슬라이드마스터 16종" 에만 초점을 맞추고 있어, 일반 조직 보고서 템플릿 처리 명시 누락.

---

## 9. 변경 이력

| 날짜 | 버전 | 변경 |
|---|---|---|
| 2026-04-19 | v1.0 | 최초 작성 (database-architect) |
| 2026-04-19 | v1.1 | `phase1_decisions.md` 반영 필요 (Q1~Q4 해소). 본문 변경은 Phase 2 병합 시. 주요 영향: §1.3 `tb_agents` CHECK 5종 확정 (Q1), §4 마이그레이션 표에 `tb_report_templates`의 S4 자동 변환 입력 소스 추가 (Q4), §4.2 타임라인에 "S6: `source_document_ids` 역방향 질의 실측 후 정규화 결정" 한 줄 추가 (Q2), §1.1 CHECK 엄격 유지 (Q3). |
