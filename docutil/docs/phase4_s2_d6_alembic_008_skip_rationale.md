# Phase 4 S2 D6 — Alembic 008 Skip Rationale

> **작성일**: 2026-04-22
> **작성자**: database-architect
> **상위 문서**: `docs/phase3_execution_roadmap.md` §2.2 S2 D6, `docs/phase4_s1_d2_alembic_007_report.md`, `docs/phase2_transition_plan.md` §2.6 D4
> **범위**: Phase 4 S2 D6 의 Alembic 008 신규 작성을 **생략(skip)** 하는 사유 기록

---

## 0. 요약

- Phase 3 로드맵 §2.2 S2 D6 에 명시된 "`tb_generated_reports` → `_archive` 리네이밍 Alembic 008" 작업은 **S1 D2 의 Alembic 007** 에서 이미 완료됨.
- 따라서 본 S2 D6 에서는 **Alembic 008 migration 을 신규 작성하지 않는다.**
- 대신 S2 D6 범위를 **ORM/라우터/서비스 레이어의 archive 일치화**(ISSUE-D2-1 해소)로 재정의해 실행했다.

---

## 1. 중복 방지 근거

### 1.1 007 에서 이미 완료된 작업

`backend/alembic/versions/007_documents_v2_and_template_consolidation.py` upgrade 4단계:

```python
# =====================================================================
# 4. tb_generated_reports 리네이밍 -> tb_generated_reports_archive
#    - 소프트 폐기. 읽기 전용으로만 유지하고 신규 insert 는 없음.
#    - FK / index 는 PostgreSQL 이 자동으로 따라온다. 제약 이름은 그대로.
#    - Phase 4 S7 에서 tb_report_templates 와 함께 완전 drop.
# =====================================================================
op.rename_table("tb_generated_reports", "tb_generated_reports_archive")
```

### 1.2 운영 DB 검증 결과 (S1 D2 보고서)

`docs/phase4_s1_d2_alembic_007_report.md` §1.5 (Step 5 스키마 적용 검증):

> - 원본 `tb_generated_reports` **존재하지 않음** (리네이밍 완료)
> - `tb_generated_reports_archive` **존재, 57건 보존**
> - archive 인덱스 4개 모두 자동 이동

Alembic head: `007_documents_v2` ✓. 동일한 rename 을 008 로 다시 수행하면 `rename_table` 소스 테이블이 없어 실패하거나, no-op 이 될 경우 설계 의도(단일 책임 migration 파일)를 흐트린다.

### 1.3 번호 충돌 회피

Alembic 008 번호는 `docs/phase1_decisions.md` §v1.2 에서 **외부 고객사 온보딩 시 `tb_organizations.organization_type` 컬럼 추가** 용도로 예약되어 있다 (Phase 1~4 범위 외). 본 D6 에서 008 을 소모하면 이후 예약된 용도와 충돌한다.

---

## 2. 대안 범위 (S2 D6 실제 수행)

007 로 DB 스키마는 정합되었으나, 애플리케이션 ORM 레이어의 ISSUE-D2-1 이 미해결 상태였다. 본 D6 는 그 해소에 집중한다:

1. **ORM tablename 정합화** — `app/modules/reports/models.py` 의 `GeneratedReport.__tablename__` 을 `tb_generated_reports_archive` 로 고정 (클래스명 `GeneratedReport` 는 유지 — S7 완전 제거 시 파일 통째 삭제).
2. **라우터 읽기 전용 전환** — POST/PUT/DELETE (generate/create/update/delete 계열) 5개 엔드포인트를 **410 Gone** 으로 차단하고 한국어 안내("해당 기능은 /v2/documents 로 이관되었습니다. 디자이너(/designer/create) 를 사용하세요.") 반환. GET/LIST/DOWNLOAD 3~5 개 엔드포인트는 archive 읽기 전용으로 유지하되 응답 헤더 `X-Deprecated-API: true` 주입.
3. **서비스 레이어 쓰기 메서드 deprecated 표기** — `create_template`/`update_template`/`delete_template`/`generate_report`/`delete_report` 메서드 docstring 에 `[DEPRECATED, S7 제거 예정]` 명시. 라우터 우회 호출이 없도록 하되, 기존 테스트 import 가 깨지지 않게 메서드 본체는 보존.
4. **회귀 방지 테스트** — `backend/tests/test_reports.py` 에 410 Gone 검증 3건 + deprecated 헤더 검증 2건 추가 (내용 상세는 S2 D6 산출물 보고 참조).

---

## 3. S7 에서 할 일 (후행 migration 번호 예약)

| 작업 | migration 번호 (안) |
|---|---|
| `tb_report_templates` drop | Phase 4 S7 (010 예정, `docs/phase3_execution_roadmap.md` §3.10 D7) |
| `tb_document_templates` drop | 동일 |
| `tb_generated_reports_archive` drop | 동일 |
| `source_document_ids` 정규화 (Q2 결정 시) | 동일 |
| `app/modules/reports/` 모듈 전체 삭제 | Phase 4 S7 D6 (B5 폐기) |

> S7 에서의 Alembic migration 번호는 008(organization_type) 과 009(TBD) 예약 후 **010** 로 착수함을 권장한다 (로드맵 §3.10 D7 일치).

---

## 4. 롤백 / 역방향 고려

- 본 D6 에서는 DB 변경이 없으므로 **Alembic 다운그레이드 불필요**.
- 라우터 410 Gone 은 FE 영향 있음(아래 §5). 회귀 시 가장 빠른 복구 경로는 라우터 파일만 git revert.

---

## 5. FE 영향 (D6 범위 밖, 기록용)

- `frontend/src/app/(user)/reports/page.tsx` 의 S1 D1 단계에서 추가된 "Mode A 디자이너 promo" 배너는 유지.
- 기존 reports UI 는 **살려둠** (archive 이력 조회 용). 쓰기 버튼(생성/수정/삭제)은 S7 범위에서 UI 제거 예정.
- 현 단계에서 FE 가 POST/DELETE 를 호출하면 **410** 을 받게 되며 한국어 detail 메시지를 토스트로 노출할 수 있음. FE 팀 공지 필요 (별도 항목으로 전달).

---

## 6. 참조

- `docs/phase3_execution_roadmap.md` §2.2 S2 D6
- `docs/phase4_s1_d2_alembic_007_report.md` §1.5, §5 (ISSUE-D2-1)
- `docs/phase2_transition_plan.md` §2.6 B5, D4/D5
- `docs/phase1_decisions.md` §v1.2 (008 예약)
- `backend/alembic/versions/007_documents_v2_and_template_consolidation.py` upgrade() 4단계
- `backend/app/modules/reports/{models,router,service}.py` (본 D6 수정)

_작성 종료._
