# 트랙 A1 Phase D — `tb_users`/`tb_departments` VIEW 폐기 영향 분석

> **2026-06-01** — 사용자 결정 필요 (옵션 1 vs 옵션 2 vs 옵션 3).

---

## 1. 현 상태 (트랙 #98 phase 3 이후)

### 1.1 VIEW + INSTEAD OF TRIGGER 구조

`docutil-postgres` PG 인스턴스 `document_utilization` 스키마에:

| 객체 | 종류 | 정의 | 작성 시점 |
|---|---|---|---|
| `tb_users` | **VIEW** | `SELECT … FROM "AIAgentManagement"."Users"` (cross-schema) | 트랙 #98 phase 3 |
| `tb_departments` | **VIEW** | `SELECT … FROM "AIAgentManagement"."Departments"` (cross-schema) | 트랙 #98 phase 3 |
| `tb_users_instead_{insert,update,delete}` | INSTEAD OF TRIGGER | AgentHub Users 로 mutation 위임 | 동일 |
| `tb_departments_instead_{insert,update,delete}` | INSTEAD OF TRIGGER | AgentHub Departments 로 mutation 위임 | 동일 |
| `tb_organizations` | **BASE TABLE** | 영향 없음 | — |

### 1.2 VIEW 정의 핵심

**`tb_users`**:
- `id` = `Users.OriginalDocutilUuid` (uuid)
- `organization_id` = `Users.OrganizationId`
- **`department_id` = NULL** (하드코딩) ← 결함 1
- `role` = `UserRoles` join → 첫 row 의 RoleName (lowercase)
- 그 외: `Status`/`Email`/`PasswordHash` 등 lower 변환 매핑
- WHERE: `IsDeleted=false AND OriginalDocutilUuid IS NOT NULL`

**`tb_departments`**:
- `id` = `Departments.OriginalDocutilUuid`
- `organization_id` = **하드코딩 `00000000-0000-4000-a000-000000000001`** ← 결함 2
- `parent_id` = parent.OriginalDocutilUuid (self-join)
- `depth` = **0 하드코딩** ← 결함 3
- `path` = **NULL** ← 결함 4

### 1.3 의존 코드 카탈로그 (19 파일)

| 파일 | 의존 패턴 | 옵션 1 영향 |
|---|---|---|
| `users/models.py` | `__tablename__ = "tb_users"` | **재정의 필수** |
| `organizations/models.py` | `__tablename__ = "tb_departments"` | **재정의 필수** |
| `chat/models.py` | `ForeignKey("tb_users.id")` | **FK 제거 + uuid → int 또는 비-FK uuid** |
| `documents/models.py` | `ForeignKey("tb_users.id")` × 2, `ForeignKey("tb_departments.id")` | **3 FK 제거** |
| `documents_v2/models.py` | `ForeignKey("tb_users.id")` × 2 | **2 FK 제거** |
| `projects/models.py` | `ForeignKey("tb_users.id")` × 3 (FK 부착 안 함 주석 — 이미 application 레벨 검증) | 검증만 |
| `reports/models.py` | (검토 필요) | |
| `search/models.py` | `ForeignKey("tb_users.id")` | **FK 제거** |
| `search_scopes/models.py` | `ForeignKey("tb_users.id")` | **FK 제거** |
| `documents/service.py:552/560` | **raw SQL JOIN tb_users** (uploader 표시) | **AgentHub API 호출로 교체** |
| `projects/router.py:394` | **raw SQL JOIN tb_users** (member 표시) | **교체** |
| `projects/router.py:516` | **raw SQL JOIN tb_departments** | **교체** |
| `projects/service.py:273~276` | `SELECT 1 FROM tb_users WHERE id = :id` (검증) | **AgentHub `/api/users/{id}` 호출** |
| `documents_v2/router.py` | 권한 체크 시 user role 참조 (안티패턴 아님) | 안정 |
| `users/router.py` | 트랙 A1 Phase C — mutation 410 차단 완료 | 안정 |
| `organizations/router.py` | 트랙 A1 Phase C — mutation 410 차단 완료 | 안정 |
| `core/security.py:221` | JWT `sub` → tb_users 매핑 주석 | **AgentHub API 또는 직접 join 으로 교체** |

### 1.4 운영 데이터 카탈로그

```
docutil-postgres / document_utilization 스키마:
- tb_organizations (BASE TABLE, 1+ rows)
- tb_users (VIEW, AgentHub Users 131 rows 의 OriginalDocutilUuid != NULL 부분만 노출)
- tb_departments (VIEW, AgentHub Departments 의 OriginalDocutilUuid != NULL 부분만)
- tb_chat_sessions, tb_documents, tb_document_chunks, tb_projects, ...
  → 모두 FK 컬럼에 uuid 값 보관 (tb_users.id 와 동일 도메인)
```

---

## 2. 옵션 비교

### 옵션 1: VIEW 폐기 + DocUtil 모델에서 FK 제거 (plan 의 선호안)

**작업**:
- DocUtil 11+ 모델의 user/department FK 제거
- FK 컬럼 타입 유지 가능 (uuid) — 단지 application 레벨 검증 (R3 격리 회복)
- raw SQL JOIN tb_users → AgentHub `/api/users/{id}` 호출 + 캐시 (트랙 #106 패턴)
- VIEW 2개 + INSTEAD OF TRIGGER 6개 DROP
- Alembic 마이그레이션 (FK 제약 제거)

**장점**:
- R3 격리 완전 회복 — cross-schema 참조 0
- 모델 명확 — DocUtil 의 user_id 가 단순 uuid 컬럼
- VIEW 의 derived column 결함 (department_id NULL / depth 0) 해소 의무 없음

**단점**:
- **대규모 변경** (모델 11 + 서비스 6 + raw SQL 5+ 위치)
- DocUtil 의 user/department 정보 표시 시 일시 API call latency
- 운영 데이터 영향 — uploaded_by 등 uuid 컬럼이 살아있는 AgentHub Users.OriginalDocutilUuid 와 정확히 일치해야 (현재는 일치)

**예상 영업일**: 4~5일

---

### 옵션 2: VIEW 유지 + derived column 보정 (낮은 위험)

**작업**:
- VIEW 정의 수정 — `department_id` 를 AgentHub Departments.OriginalDocutilUuid 와 join 하여 정확 매핑
- `tb_departments.depth`/`path` 보정 (materialized path 알고리즘)
- `organization_id` 하드코딩 제거 → Users.OrganizationId 의 uuid 매핑 추가

**장점**:
- 코드 변경 거의 없음 (DB VIEW DDL 만 변경)
- 운영 영향 작음

**단점**:
- R3 격리 단서 활용 지속 (CLAUDE.md "운영자 콘솔만 read 가능" 단서 의존)
- cross-schema 참조 영구 잔존
- VIEW 의 read-only 동작 — INSTEAD OF TRIGGER 가 mutation 처리 (Phase C 의 410 차단으로 dead code)
- 추후 schema 변경 시 매번 VIEW 동기화 부담

**예상 영업일**: 1~2일

---

### 옵션 3: Materialized View + 정기 refresh (절충)

**작업**:
- `tb_users`/`tb_departments` 를 materialized view 로 전환
- `REFRESH MATERIALIZED VIEW CONCURRENTLY` 를 운영자 mutation 후 호출 (AgentHub 측에서)
- read 성능 향상 (인덱싱 가능)

**장점**:
- read 성능 ↑
- VIEW 의 derived column 결함은 옵션 2 와 동일하게 보정 가능

**단점**:
- refresh 타이밍 결함 가능 (운영자 mutation 후 refresh 누락 시 stale)
- 옵션 2 의 R3 격리 문제 동일하게 잔존
- AgentHub 의 모든 Users/Departments mutation 에 refresh 트리거 부착 의무

**예상 영업일**: 2~3일

---

## 3. 결정 권장 사항 + Open Questions

### 선호 (plan witty-spinning-snail.md)
**옵션 1** — R3 격리 완전 회복.

### 결정 전 확인 필요
| ID | 질문 |
|---|---|
| D-Q1 | DocUtil 의 user/department 정보 표시 빈도가 높은가? (옵션 1 시 API call 부담) |
| D-Q2 | 운영 데이터의 uploaded_by 등 uuid 컬럼이 모두 살아있는 AgentHub Users.OriginalDocutilUuid 와 일치하는지 사전 검증 필요 (dangling 0 건 확인) |
| D-Q3 | DocUtil 의 user 정보 캐시 정책 (TTL / version-key invalidate) |
| D-Q4 | DocUtil 의 user/department 표시 캐시 미적용 시 운영 latency 영향 측정 (PoC 1일) |
| D-Q5 | 진입 시점 — Phase E (DocUtil admin 페이지 redirect) 와 동시 진행? Phase E 완료 후 진입? |

### 진입 조건 (옵션 1 선택 시)
1. D-Q2 의 dangling 검증 PASS
2. D-Q4 의 latency 영향 측정 완료 (캐시 시 < 50ms 추가)
3. 백업 + 롤백 시나리오 사전 작성

### 작업 단위 (옵션 1 선택 시)
1. **D.A** Alembic 마이그레이션 작성 — FK 제거 + 데이터 backfill (1일)
2. **D.B** DocUtil 모델 11개 FK 제거 + service.py 6개 raw SQL → AgentHub API 교체 (2일)
3. **D.C** VIEW + INSTEAD OF TRIGGER DROP (0.5일)
4. **D.D** 운영 데이터 backfill dry-run + 검증 (1일)
5. **D.E** 운영 적용 + 회귀 검증 (0.5일)

---

## 4. 회귀 회피 (모든 옵션 공통)

- DocUtil 의 `/chat`, `/my-documents`, `/search`, `/reports` 사용자 화면 정상 동작
- AgentHub 의 `/admin/docutil-users`, `/admin/docutil-departments` 정상 동작 (Phase C 의 mutation refactor 와 정합)
- DocUtil API 의 GET /api/v1/users, /api/v1/departments — VIEW 폐기 후에도 다른 경로 (AgentHub API 위임 또는 직접 join) 로 응답
- 운영자 로그인 후 분석 대시보드 user 라벨 / 부서 목록 / 프로젝트 멤버 표시 정상

---

## 5. 다음 진행

**사용자 결정 필요**:
- 옵션 1 / 옵션 2 / 옵션 3 중 선택
- D-Q1 ~ D-Q5 답변
- 진입 시점 (즉시 / Phase E 후 / 별도 트랙)

승인 후 진행. 옵션 1 선택 시 D.A 부터 단계별 진행 + 각 단계 PASS 확인 후 다음 진입.
