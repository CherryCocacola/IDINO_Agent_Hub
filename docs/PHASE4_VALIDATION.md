# Phase 4.5 — 통합 검증 보고서

> **작성일**: 2026-05-06
> **대상**: AGENT_HUB DB (192.168.10.39:5440, PostgreSQL 17.9, pgvector 0.8.0)
> **검증 범위**: AIAgentManagement / document_utilization / idino_career / hangfire 4 schema
> **참조**: `user_mig/TECHSPEC.md` §3 (P1~P10), §16 (R1~R30), `user_mig/progress.md`
> **검증 방법**: `user_mig/scripts/phase45_validate.csx` (dotnet-script + Npgsql 직접)
> **본 문서 성격**: 검증 산출물 (수정/마이그레이션 별도 트랙)

---

## 0. 요약 — 검증 결과 한눈에

| 항목 | 결과 | 비고 |
|---|---|---|
| 4 schema 테이블 수 | **127개** | AgentHub 37 + DocUtil 28 + career 62 (+ hangfire 0) |
| 인덱스 총수 | **342개** (UNIQUE 175 + Vector 3) | Vector 인덱스 = idino_career 3 (Phase 4.4) |
| FK 총수 | **186개** | AgentHub 47 + DocUtil 57 + career 82 |
| **R3 cross-schema FK** | **0개 [PASS]** | schema 격리 강제 확인 |
| **R3 격리 시뮬레이션** | **3/3 PASS** | 각 connection 은 자기 schema 만 보임 |
| Phase 5 Nexus 시드 | 1건 | `ServiceCode='nexus'`, ServiceType=Chat |
| Phase 7.1 Agent 시드 | 15건 | docutil 4 / career 9 / 공용 2 |
| Phase 7.2 ApiKey 발급 | 2건 | docutil-master-key, career-master-key |
| Phase 4.3 Tenants/Departments | Tenants=1, Departments=1 | bootstrap row |
| Phase 4.4 vector 컬럼 | 3개 (1536D) | tb_course/tb_program/tb_success_pattern |
| PK 누락 BASE TABLE | **0건** | 187 BASE TABLE 모두 PK 보유 |
| audit 컬럼 누락 | AgentHub 5 / DocUtil 10 / career 0 | DocUtil은 ins_dt 패턴이 표준 (별도 트랙) |

**결론**: Phase 4.1 + 4.2 + 4.3 + 4.4 + 5 + 7.1 + 7.2 적용분 모두 운영 PG 에 안정적으로 반영. R3 격리 강제 PASS, Phase 4 종합 완료 처리 가능.

---

## 1. 4 Schema 통합 통계

### 1.1 BASE TABLE 수

| schema | 테이블 수 | 비고 |
|---|---|---|
| AIAgentManagement | 37 | 35 (AgentHub) + Tenants + Departments (Phase 4.3) |
| document_utilization | 28 | 27 tb_* + alembic_version |
| idino_career | 62 | Phase 4.2 적용분 |
| hangfire | 0 | AgentHub 부팅 시 자동 생성 (미실행 상태) |
| **합계** | **127** | (hangfire 제외 시) |

### 1.2 인덱스 통계

| schema | total | UNIQUE | Vector (IVFFlat cosine) |
|---|---|---|---|
| AIAgentManagement | 110 | 54 | 0 |
| document_utilization | 101 | 38 | 0 |
| idino_career | 131 | 83 | **3** |
| **합계** | **342** | **175** | **3** |

Vector 인덱스 3개는 모두 idino_career schema (Phase 4.4):
- `ix_tb_course_embedding`
- `ix_tb_program_embedding`
- `ix_tb_success_pattern_embedding`

모두 `USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)`.

### 1.3 FK / UNIQUE / PK

| 항목 | AgentHub | DocUtil | career | 합계 |
|---|---|---|---|---|
| FK 수 | 47 | 57 | 82 | 186 |
| UNIQUE 제약 | (PK + UNIQUE 인덱스 분포로 산출) | 10 | 21 | — |
| PK 누락 BASE TABLE | 0 | 0 | 0 | **0** |

PK 누락 0건 — Phase 3.6/4.1/4.2 적용분에서 모든 BASE TABLE 이 PK 보유 (alembic_version 포함).

---

## 2. R3 Schema 격리 검증 — PASS

### 2.1 Cross-schema FK = 0 [PASS]

```sql
SELECT con.contype='f' AND pgn1.nspname <> pgn2.nspname  → 0행
```

**의미**: 어떤 FK 도 다른 schema 의 테이블을 참조하지 않음. anti-patterns.md §3 (cross-schema join 금지) 의 DDL-level 보장.

특히:
- AgentHub Tenants/Departments (Phase 4.3) 가 idino_career.tb_user 를 FK 로 묶지 않음 — 스키마 격리 + 옵션 B (별도 Departments 신규) 디자인이 DDL 에 반영됨
- DocUtil tb_user 와 AgentHub Users 는 서로 독립

### 2.2 search_path 시뮬레이션 (3 connection)

각 시스템의 connection 을 시뮬레이션 (`SET search_path TO ...`):

| connection | search_path | Users (AgentHub) | tb_documents (DocUtil) | tb_student (career) |
|---|---|---|---|---|
| **agenthub** | `"AIAgentManagement",public` | OK | FAIL (`relation "tb_documents" does not exist`) | FAIL |
| **docutil** | `document_utilization,public` | FAIL | OK | FAIL |
| **career** | `idino_career,public` | FAIL | FAIL | OK |

**해석**: 각 connection 은 자기 schema 의 unqualified table 만 접근 가능. 다른 schema 의 테이블은 schema-qualified (`AIAgentManagement.Users` 등) 로만 접근 가능 — DB user 가 동일하더라도 search_path 만으로 의도하지 않은 cross-schema 참조를 차단.

운영 환경에서는 추가로 schema-level GRANT 차등 부여로 권한도 격리 권장 (별도 트랙 — TECHSPEC §13).

---

## 3. FK ON DELETE 정책 분포

| schema | CASCADE | NO ACTION | RESTRICT | SET NULL | 합계 |
|---|---|---|---|---|---|
| AIAgentManagement | 32 | 12 | 2 | 1 | 47 |
| document_utilization | 30 | 0 | 1 | 26 | 57 |
| idino_career | 0 | 82 | 0 | 0 | 82 |

### 3.1 분석

**AgentHub (32 CASCADE / 47)**:
- 부모 삭제 시 자식 자동 삭제. ChatConversation → ChatMessages, Agent → AgentTools 같은 소유 관계
- TECHSPEC §16 R12 (Cascade Delete 강등) 권고 일부 적용 필요 — 운영 데이터 (Conversations, ApiUsages) 에서 의도치 않은 대량 삭제 위험
- SET NULL 1건만 — User 삭제 정책이 자식 row 의 ownership 만 풀고 데이터 보존하는 패턴이 부족

**DocUtil (30 CASCADE / 26 SET NULL)**:
- 균형 있게 분포 — 문서 → 청크는 CASCADE, 사용자 → 활동 로그는 SET NULL 패턴
- 가장 디자인 의도가 명확

**career (82 NO ACTION 100%)**:
- 모두 NO ACTION (= deferred 검사, 명시적 삭제 정책 없음). Phase 4.2 적용 시 원본 SQL 의 default 유지
- **권장 (별도 트랙)**: 핵심 마스터(tb_university, tb_college, tb_department, tb_user) 는 RESTRICT 로 명시화, 활동/이력 테이블은 CASCADE 검토
- 현재 시연용 빈 테이블이라 운영 영향 없음. 운영 데이터 적재 전 정책 확정 필요

### 3.2 권장 (별도 트랙)

1. **AgentHub**: CASCADE 32건 중 ApiUsages/PiiDetectionLogs 등 감사 성격 테이블은 SET NULL 또는 RESTRICT 로 강등
2. **DocUtil**: 분포 양호, 변경 권고 없음
3. **career**: 운영 데이터 적재 전 NO ACTION → 명시적 정책 (RESTRICT/CASCADE) 전환 필수
4. 본 작업은 마이그레이션이 필요하므로 **별도 트랙** (예: Phase 4.6 또는 Phase 8) 으로 분리

---

## 4. Audit 컬럼 일관성

### 4.1 schema 별 패턴

| schema | 표준 컬럼 | 보유 테이블 / 총 |
|---|---|---|
| AIAgentManagement | `CreatedAt` (PascalCase) | 32 / 37 |
| document_utilization | `created_at` (snake_case) + `ins_dt` (legacy) | 27 / 28 |
| idino_career | `ins_dt` + `ins_user_id` + `upd_dt` + `upd_user_id` | 62 / 62 |

### 4.2 schema 별 audit 컬럼 분포

```
AIAgentManagement    CreatedAt       32   ← 표준
                     UpdatedAt       24
                     CreatedBy        6   ← 일부만
document_utilization created_at      미집계 (별도 통계 — 6b 결과로 18개 보유)
                     ins_dt          27   ← legacy 표준 (snake_case 컬럼이지만 timestamptz)
                     upd_dt          27
                     created_by       7
idino_career         ins_dt          62   ← 100% 보유
                     ins_user_id     62
                     upd_dt          55
                     upd_user_id     55
                     created_at       4   ← 일부 마이그레이션 잔존
```

### 4.3 누락 테이블 (각 schema 별 표준 컬럼 기준)

**AIAgentManagement (CreatedAt 누락 5건)**:
- `PiiDetectionLogs`, `TeamMembers`, `UserRoles`, `WorkflowExecutions`, `WorkflowNodeExecutions`
- 일부 (PiiDetectionLogs 등) 는 자체 `Timestamp`/`StartedAt` 컬럼 보유 — 표준화 필요

**document_utilization (created_at 누락 10건)**:
- `alembic_version` (예외 정상)
- `tb_agents`, `tb_audit_logs`, `tb_boards`, `tb_chat_messages`, `tb_chat_sessions`, `tb_departments`, `tb_document_access`, `tb_document_chunks`, `tb_document_templates`
- DocUtil 표준은 **`ins_dt` (snake_case + timestamptz)** — 27건 모두 보유 → 실제 누락 1건뿐 (alembic_version 정상)

**idino_career (ins_dt 누락 0건)**:
- 100% 보유. Phase 4.2 의 ETL 표준 적용

### 4.4 권장 통일 방안 (별도 트랙)

세 schema 의 audit 컬럼이 **시스템 별 다른 표준** 으로 분기되어 있음 — 통합 운영 시 cross-schema 분석 어려움:

| 옵션 | 비용 | 효과 |
|---|---|---|
| **A. 각 schema 표준 유지** (현재) | 0 | 시스템별 격리 유지, 분석 시 변환 필요 |
| **B. AgentHub/DocUtil 만 통일 (snake_case + ins_dt)** | 중 | EF Core 모델 모두 변경 필요 (영향 큼) |
| **C. 글로벌 view (`v_audit_log`) 신규** | 저 | 각 schema audit 컬럼을 통합한 read-only view |

**권장**: **옵션 C** — 본 검증 작업의 책임 범위 밖이므로 별도 트랙으로 처리. 본 Phase 4.5 는 발견만.

---

## 5. Phase 5 / 7 시드 검증

### 5.1 Phase 5 — Nexus ApiService

```
ServiceCode  ServiceName       ServiceType
nexus        Project Nexus     Chat
```

PASS — 단일 row 등록. 별도 키 풀(ApiKeyPool) 은 LAN 격리 + 공유 시크릿 (ADR-13) 으로 처리.

### 5.2 Phase 7.1 — Agent 시드 (15건)

```
agentic-search                       service=1 (openai)  routing=Hybrid
career-action-recommender            service=1           routing=Hybrid
career-actionboard-orchestrator      service=1           routing=Hybrid
career-chatbot                       service=3 (nexus?)  routing=Internal
career-competency-analyzer           service=1           routing=Hybrid
career-rag-actionboard               service=1           routing=Hybrid
career-semester-planner              service=1           routing=Hybrid
career-simulation-analyzer           service=1           routing=Hybrid
career-simulation-suggester          service=1           routing=Hybrid
docutil-evaluator                    service=1           routing=External
docutil-image-generator              service=2 (azure?)  routing=External
docutil-rag-chat                     service=1           routing=Hybrid
docutil-report-generator             service=1           routing=Hybrid
embedding-default                    service=1           routing=External
web-search-default                   service=1           routing=External
```

PASS — 15개 모두 정상 시드. `career-chatbot` 만 Internal (Nexus) 강제 — 학생 PII 보호 의도와 일치 (Phase 7.4 W6 확인 사항).

**주의 (별도 트랙)**: ServiceId=2/3 의 역방향 매핑 검증 — `ApiServices` 테이블의 ServiceId 와 ServiceCode 매핑이 시드 의도와 일치하는지 확인 필요 (예: `service=2` 가 azure_openai 인지, `service=3` 이 nexus 인지). 본 검증에서는 시드 row 존재 + AgentCode 일관성만 확인.

### 5.3 Phase 7.2 — ApiKey

```
id=1  docutil-master-key  scopes=chat,stream,info,usage  active=true
id=2  career-master-key   scopes=chat,stream,info,usage  active=true
```

PASS — 2개 활성. 평문 키는 `.gitignore` 대상 (commit 금지 — TECHSPEC §13).

**주의**: master 키 단일 발급 = 회전 부담 + scope 단위 권한 격리 부족 (TECHSPEC §16 R7). 운영 진입 전 Per-MS 키 분리 + 회전 정책 별도 트랙.

### 5.4 Phase 4.3 — Tenants / Departments

```
Tenants     = 1
Departments = 1
```

bootstrap row 정상. 실제 멀티테넌시는 Phase 5+ 사용자 SSO (Q2) 와 함께 운영 확장.

### 5.5 Phase 4.4 — pgvector

```
idino_career.tb_course.embedding           vector(1536)
idino_career.tb_program.embedding          vector(1536)
idino_career.tb_success_pattern.embedding  vector(1536)
+ 3 IVFFlat cosine 인덱스 (lists=100)
```

PASS — ADR-10 (1536D 단일화) 일치. 빈 테이블 (rows=0) 이므로 백필 미진행, 운영 데이터 적재 후 lists 재조정 별도 트랙.

---

## 6. 통합 부분 롤백 시나리오 (검토만)

각 schema `DROP SCHEMA ... CASCADE` 시 영향 매트릭스:

| schema drop | 손실 | 복구 절차 (별도 트랙) |
|---|---|---|
| **AIAgentManagement** | Agents 15 + ApiServices(nexus 등) + ApiKeys 2 + Users + Tenants 등 전체. **Phase 5/7 무효화** | 1) `infra/db/init.sql` 재실행 → 2) Phase 3.6 마이그레이션 적용 → 3) Phase 4.3 + 5.1 + 7.1/7.2 시드 재적용 |
| **document_utilization** | tb_documents/chunks/users/sessions 전체. **RAG 무효화** | 1) `init.sql` → 2) DocUtil alembic upgrade head → 3) 데이터 백업 복원 |
| **idino_career** | tb_student/competency/role 등 전체 (시연용 빈 테이블). 운영 영향 없음 (현재) | 1) `init.sql` → 2) `career/database/01~02_*.sql` 재실행 → 3) Phase 4.4 ALTER TABLE 재적용 |
| **hangfire** | (현재 미생성) AgentHub 부팅 시 자동 재생성 | 자동 |

핵심: **Phase 5/7 시드는 reproducible 하지 않음** — Phase 7.1 의 15개 Agent + Phase 7.2 의 2개 ApiKey 가 아직 init.sql 또는 EF migration 으로 codify 되어 있지 않음.

**권장 (별도 트랙)**:
1. Phase 5.1 의 nexus 시드 + Phase 7.1 의 15개 Agent + Phase 7.2 의 ApiKey 발급을 EF migration `Up()` 메서드로 codify
2. CI 에 `infra/db/init.sql` + EF `dotnet ef database update` 시 모든 시드가 idempotent 하게 재적용되는지 검증 추가

---

## 7. 잠재 위험 / Known Issues

| 위험 ID | 영역 | 심각도 | 권장 조치 (별도 트랙) |
|---|---|---|---|
| **R12** | AgentHub CASCADE 32건 중 감사성 (ApiUsages 등) | High | SET NULL/RESTRICT 강등 마이그레이션 |
| **R12-c** | career 82 FK 모두 NO ACTION | Medium (운영 전) | 운영 데이터 적재 전 정책 확정 |
| **Audit 분기** | 3 schema 별 다른 표준 (CreatedAt/created_at/ins_dt) | Low | 통합 view (`v_audit_log`) |
| **AgentHub audit 5건 누락** | PiiDetectionLogs 등 | Low | 자체 timestamp 컬럼 활용 검토 |
| **IVFFlat lists=100** | 빈 테이블 + 운영 적재 후 과도 | Low | 백필 후 `lists ≈ sqrt(N)` 재조정 |
| **R7** | master ApiKey 단일 발급 + 회전 부재 | Medium | Per-MS 키 분리 + 회전 정책 |
| **시드 reproducibility** | Phase 5.1/7.1/7.2 시드가 init.sql 미codify | Medium | EF migration `Up()` 으로 이전 |
| **R3 schema GRANT 미구분** | 동일 DB user (`AGENT_HUB`) 가 모든 schema 접근 | Medium | schema-level GRANT 차등 부여 |

---

## 8. Phase 4 종합 완료 평가

| Phase | 상태 | 검증 결과 |
|---|---|---|
| 4.1 (DocUtil schema) | ✅ | 28 테이블 / 57 FK / 101 인덱스 |
| 4.2 (career schema) | ✅ | 62 테이블 / 82 FK / 131 인덱스 |
| 4.3 (Tenants + Departments) | ✅ | bootstrap row 1+1 |
| 4.4 (idino_career pgvector) | ✅ | 3 vector 컬럼 + 3 IVFFlat 인덱스 |
| **4.5 (통합 검증)** | ✅ | **본 보고서** |

**결론**: Phase 4 종합 완료. R3 격리 강제 PASS, cross-schema FK 0건, 시뮬레이션 3/3 PASS. Phase 7.5 또는 Phase 5+ 별도 트랙 진입 가능.

---

## 9. 검증 도구 / 재현

```bash
export PATH="/c/Users/IDINO_USER/.dotnet:/c/Users/IDINO_USER/.dotnet/tools:$PATH"
export DOTNET_ROOT="C:\\Users\\IDINO_USER\\.dotnet"
cd /d/workspace/IDINO_Agent_Hub
dotnet-script user_mig/scripts/phase45_validate.csx
```

스크립트: `D:\workspace\IDINO_Agent_Hub\user_mig\scripts\phase45_validate.csx`

검증 항목 (15개):
1. schema 별 BASE TABLE 수 / 2. cross-schema FK / 3. ON DELETE 정책 분포 / 4. FK 총수 / 5. audit 컬럼 분포 / 6. audit 누락 / 7. 인덱스 통계 / 8. Nexus 시드 / 9. Agent 시드 / 10. ApiKey 시드 / 11. Tenants/Departments / 12. vector 컬럼 / 13. R3 격리 시뮬레이션 / 14. UNIQUE 제약 / 15. PK 누락

---
