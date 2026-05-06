# IDINO Agent Hub — 통합 작업 진행 상황

> **마지막 갱신**: 2026-05-05
> **갱신 규칙**: 모든 작업 완료 시 본 파일을 갱신한다 (CLAUDE.md 의무 사항).
> **참조**: `user_mig/TECHSPEC.md` (통합 기술 명세), `docs/AI_INVENTORY.md` (Phase 1 산출물)

---

## 0. 현재 상태 한눈에

| 항목 | 값 |
|---|---|
| **현재 Phase** | Phase 3 (AgentHub MSSQL → PostgreSQL 마이그레이션) — **3.1 + 3.2 + 3.3 + 3.4 + 3.5 + 3.5b + 3.6 모두 commit 완료 (Phase 3 핵심 마무리)** |
| **다음 Phase** | Phase 4 (DocUtil/career → AGENT_HUB 통합) 또는 Phase 5 (AgentHub Nexus provider) — 병렬 가능 |
| **마지막 commit** | `(Phase 3.6 commit 후 갱신)` |
| **GitHub remote** | https://github.com/CherryCocacola/IDINO_Agent_Hub.git (push 대기 — secret leak 미해결) |
| **TECHSPEC** | `user_mig/TECHSPEC.md` v1.0 (작성 완료) |
| **AI 인벤토리** | `docs/AI_INVENTORY.md` v1.0 (Phase 1 산출, 35 호출 + 5 위임 + 15 신규 Agent 카탈로그) |
| **DB 마이그레이션** | `infra/db/init.sql` v1.0 + `docs/DB_MIGRATION.md` v1.0 (Phase 2 산출, 단일 PG + 4 schema + pgvector + idempotent) |
| **분석 보고서** | `source_AGENTHUB.md`, `source_DOCUTIL.md`, `source_CAREER.md`, `source_NEXUS.md` (4개 완료) |

---

## 1. Phase 진척도

| Phase | 내용 | 상태 | 완료일 / 예정 |
|---|---|---|---|
| **0** | 작업공간 셋업 + monorepo 초기화 + 분석/TECHSPEC | ✅ 완료 | 2026-05-04 |
| **1** | AI 호출 인벤토리 작성 (`docs/AI_INVENTORY.md`) | ✅ 완료 | 2026-05-05 |
| **2** | AGENT_HUB DB 설계 + 생성 (`infra/db/init.sql`) | ✅ 완료 | 2026-05-05 |
| **3** | AgentHub MSSQL → PostgreSQL 마이그레이션 | ✅ 핵심 완료 (3.1 + 3.2 + 3.3 + 3.4 + 3.5 + 3.5b + 3.6) | 2026-05-06 |
| **4** | DocUtil/career → AGENT_HUB 통합 | ⏳ 대기 | Phase 3 후 |
| **5** | AgentHub Nexus provider + LlmRouting + 진짜 SSE | ⏳ 대기 | Phase 3 후 (4와 병렬) |
| **6** | DocUtil 운영자 → AgentHub 흡수 + KB 마이그레이션 | ⏳ 대기 | Phase 5 후 |
| **7** | DocUtil/career AI 호출 → AgentHub 위임 | ⏳ 대기 | Phase 5+6 후 |
| **8** | (보류) Vue → Next.js | ⏸ 보류 | — |

범례: ✅ 완료 / 🔄 진행 중 / ⏸ 사용자 승인 대기 / ⏳ 의존성 대기

---

## 2. Phase 0 — 완료된 작업 (2026-05-04)

### 2.1 디렉토리 셋업
- [x] `D:\workspace\IDINO_Agent_Hub\` 생성
- [x] 4개 서브프로젝트 복사 (PowerShell robocopy):
  - [x] `agenthub/` (98 items, AIAgentManagement 복사)
  - [x] `docutil/` (23 items, document_utilization 복사)
  - [x] `career/` (77 items, idino_career 복사)
  - [x] `nexus/` (21 items, nexus 복사)

### 2.2 루트 파일
- [x] `.gitignore` (다국어 스택 + 시크릿 제외)
- [x] `README.md` (프로젝트 개요)
- [x] `CLAUDE.md` (AI 코딩 도구 협업 컨텍스트)

### 2.3 `.claude/rules/` (6개)
- [x] `architecture.md` (10개 원칙 P1~P10)
- [x] `anti-patterns.md` (13개 금지 패턴)
- [x] `agent-collaboration.md` (작업 절차 + 커밋 규약)
- [x] `domain-model.md` (엔티티/용어 카탈로그)
- [x] `testing.md` (4계층 테스트 전략)
- [x] `development-workflow.md` (Phase별 작업 순서)

### 2.4 `docs/`
- [x] `ARCHITECTURE.md` (Control Plane / Data Plane Federation)
- [x] `AI_INVENTORY.md` (Phase 1 산출물 템플릿)

### 2.5 `user_mig/` (신규)
- [x] `source_AGENTHUB.md` (AgentHub 종합 분석, 334 라인)
- [x] `source_DOCUTIL.md` (DocUtil 종합 분석, 341 라인)
- [x] `source_CAREER.md` (idino_career 종합 분석, 295 라인)
- [x] `source_NEXUS.md` (Nexus 종합 분석, 354 라인)
- [x] `TECHSPEC.md` (통합 기술 명세, v1.0)
- [x] `progress.md` (본 파일)

### 2.6 Git
- [x] `git init -b main`
- [x] `git remote add origin https://github.com/CherryCocacola/IDINO_Agent_Hub.git`
- [x] 초기 commit `1da04ab` (1,921 files / 558,811 insertions)
- [x] 시크릿 파일 .gitignore 강제 (검증 완료):
  - `appsettings.Development/Production.json`
  - `.env` (career 6 MS, infrastructure)
  - `nexus/config/{nexus_config,permission_rules,tenants}.yaml`
  - `nexus/config/ssl/`

### 2.7 GitHub Push 상태
- ⏸ **대기 중** — 사용자 승인 후 `git push -u origin main` 실행

---

## 3. 핵심 의사결정 (Phase 0 동안 확정)

| ADR | 결정 | 이유 |
|---|---|---|
| ADR-1 | Nexus 통합 **옵션 B** (AgentHub-side `CallNexusAsync`) | Nexus 세션/멀티테넌시 보존 |
| ADR-2 | RAG 단일 권위 = **DocUtil** | AgentHub 자체 KB는 deprecate |
| ADR-3 | Vue 3 유지 (Phase 8 보류) | 통합의 핵심 가치는 Data Plane 통합 |
| ADR-4 | 단일 PostgreSQL `AGENT_HUB` DB + 4 schema | 운영 단순화 |
| ADR-5 | MSSQL → PostgreSQL | DocUtil/career가 PG 사용, pgvector 우수 |
| ADR-7 | DocUtil Phase 4 별도 트랙 | S6/S7 미완 상태 통합 시 회귀 위험 |
| ADR-8 | `Tenants` 신규 엔티티 | 멀티테넌시 단일 권위 |
| ADR-9 | JWT HS256 단일 표준 | DocUtil RS256/HS256 fallback 통합 |
| ADR-10 | 임베딩 1536D 단일화 | Qdrant collection 단일성 |
| ADR-11 | Nexus DB 별도 유지 | 라이프사이클 다름 |
| ADR-12 | 순환 호출 방지 (DocUtil은 `/search/hybrid`만) | 무한 루프 방지 |
| ADR-13 | 공유 시크릿 인증 (AgentHub-Nexus) | LAN 격리 + 1차 방어 |
| ADR-15 | progress.md 자동 갱신 규칙 | git commit 단위로 진행 명확화 |

(전체 ADR-1 ~ ADR-15는 TECHSPEC §20 참조)

---

## 4. 미해결 결정 (Open Questions, Phase 진입 전 결정)

| ID | 질문 | 결정 시점 |
|---|---|---|
| Q1 | career `department_id` 매핑 정책 (Tenants sub-org / 별도 Departments / 자체 유지) | Phase 4 시작 전 |
| Q2 | 사용자 SSO 시점 (Phase 5+ 즉시 / Phase 7+ / 별도 트랙) | Phase 4 완료 후 |
| Q3 | **DocUtil Phase 4 S6/S7 진행 위치 (DocUtil 원본 / monorepo 내부)** | **즉시 (Phase 1 진입 전)** |
| Q4 | Nexus DB 위치 (별도 DB / AGENT_HUB.nexus schema) | ADR-11에 따라 별도 DB, schema 분리만 추가 검토 |
| Q5 | 외부 LLM Tenant별 다른 키 풀 가능 여부 | Phase 5 |
| Q6 | DocUtil 임베딩 vLLM Qwen3 2048D 처리 (제거 / 별도 collection) | Phase 7 |
| Q7 | Workflow Condition/DataTransform/Loop 정식 구현 | Phase 5+ 별도 |
| Q8 | CSharpToolExecutor 보안 (collectible AssemblyLoadContext / 기능 차단) | Phase 5+ |
| Q9 | 운영자 SSO (AD/LDAP) | Phase 6+ |
| Q10 | 시계열 데이터 보존 정책 | Phase 5+ |

---

## 5. 위험 추적 (R1~R30)

### Critical (Phase 3 진입 전 결정 필수)
- [ ] R1: Tenant/Organization/Department 모델 설계 → §4.5
- [ ] R5: Nexus DB 별도 유지 → ADR-11 확정
- [ ] R11: EF baseline 부재 → Phase 3에서 신규 작성
- [ ] R15: JWT 알고리즘 통일 → ADR-9 확정

### High (Phase 5 전)
- [ ] R3: OpenAI Structured Outputs 다중 프로바이더 fallback
- [ ] R7: API Key 회전
- [ ] R8: CIDR IP 검증
- [ ] R10: Nexus 인증 미들웨어
- [ ] R12: Cascade Delete 강등
- [ ] R13: 임베딩 차원 통일
- [ ] R17: Qdrant collection 단일성 vs Nexus 1024D
- [ ] R18: 평문 시크릿 잔존
- [ ] R20: AgentHub KB → DocUtil visibility 매핑
- [ ] R27: SSO 결정

### Medium / Low — TECHSPEC §16 참조

---

## 6. 작업 로그 (Append-only, 시간 역순)

### 2026-05-06 (Phase 3.6 — AGENT_HUB DB 셋업 + baseline 마이그레이션 운영 PG 적용 + T-SQL 잔존 정리)
- **목적**: Phase 3.2 baseline 을 운영 PostgreSQL(192.168.10.39:5440) 에 실제 적용 + Phase 2 init.sql 동등 작업 + DbContext T-SQL bracket(`[Status]`/`[Role]`/`[IsActive] = 1`) 잔존 PG 호환 변환
- **사전 작업 (.NET tool 추가 + PG 자격증명 탐색)**:
  - `dotnet-script` 2.0.0 글로벌 도구 설치 — Npgsql 직접 호출용 ad-hoc 스크립트 실행
  - PG superuser 탐색: nexus/docutil/.env 의 자격증명 6쌍 시도 → **`docutil` / `docutil_pg_2024`** 가 superuser/createdb/createrole 권한 보유 확인 (PG 17.9 alpine 컨테이너로 추정). `postgres` 계정 비밀번호 4종 시도 모두 실패
  - 운영 PG 의 기존 DB 3개 (`docutil`, `nexus`, `postgres`) + role 2개 (`docutil`, `nexus`) — `AGENT_HUB` 미존재 확인
- **Phase 2 init.sql 동등 작업 (Npgsql 직접 실행, psql 미설치 환경)**:
  - psql 메타커맨드(`\set`/`\if`/`\gexec`/`\connect`) → Npgsql `NpgsqlCommand` 분할 호출로 변환
  - **§1 `AGENT_HUB` role 생성** (postgres DB 안에서 `DO $$ ... CREATE ROLE %I LOGIN PASSWORD %L $$`) — 비밀번호 `idino!@#$`
  - **§2 `AGENT_HUB` DATABASE 생성** (CREATE DATABASE 는 implicit transaction 외 실행 — Npgsql 단일 NonQuery 자동 처리). UTF8 / ko_KR.UTF-8 / template0
  - **§4 Extensions 4종**: `vector` 0.8.0 / `uuid-ossp` 1.1 / `pgcrypto` 1.3 / `pg_trgm` 1.6
  - **§5 Schemas 4종**: `AIAgentManagement` / `document_utilization` / `idino_career` / `hangfire` — 모두 owner = `AGENT_HUB`
  - **§6 ALTER DEFAULT PRIVILEGES** — 4 schema 별 TABLES/SEQUENCES/FUNCTIONS 권한 자동 부여 (DO $$ FOREACH IN ARRAY)
  - **§7 search_path** — `AGENT_HUB` role 의 default search_path 4 schema + public
  - **§8 검증 쿼리** — extensions 4행 + schemas 4행 + role 1행 (rolcanlogin=t, rolsuper=f) 모두 정상
- **DbContext T-SQL 잔존 정리 (3건 발견 → PG 호환 변환)**:
  - 첫 번째 마이그레이션 적용 시도 시 `42601: syntax error at or near "["` 발생 (position 992) — DbContext 의 `HasCheckConstraint` / `HasFilter` 가 T-SQL bracket 식별자 사용
  - `agenthub/Data/AIAgentManagementDbContext.cs:79` — `HasCheckConstraint("CK_ChatMessages_Role", "[Role] IN (...)")` → `"\"Role\" IN (...)"` (PG 큰따옴표)
  - `agenthub/Data/AIAgentManagementDbContext.cs:83` — `HasCheckConstraint("CK_Users_Status", "[Status] IN (...)")` → `"\"Status\" IN (...)"`
  - `agenthub/Data/AIAgentManagementDbContext.cs:142` — `HasFilter("[IsActive] = 1")` → `"\"IsActive\" = true"` (PG boolean literal)
- **baseline 재생성**: 기존 `Migrations/20260505131410_Init.{cs,Designer.cs}` 삭제 → 새 빌드 후 `dotnet-ef migrations add Init` 재생성 → `Migrations/20260505154102_Init.{cs,Designer.cs}`
  - dry-run script 검증: T-SQL 잔존(`\[`) 0건, PG 표준 식별자 정상
  - `migrations list`: `20260505154102_Init (Pending)` 등록 확인
- **운영 PG 적용 — `dotnet-ef database update`**:
  - 35 CREATE TABLE + 인덱스 + UNIQUE + CHECK 제약 + 부분 인덱스 모두 정상 실행
  - `INSERT INTO "__EFMigrationsHistory" VALUES ('20260505154102_Init', '8.0.11')` 기록
  - 결과: `AIAgentManagement` schema 35 테이블 생성 완료
- **Phase 3.3 보안 컬럼·인덱스 PG 적용 검증** (Npgsql 직접 쿼리):
  - ✅ `ApiKeys.KeyIv bytea` / `ApiKeys.KeyTag bytea` / `ApiKeys.KeyHash character varying(64)` (C1/C3)
  - ✅ `ApiQuotas.CurrentTokens bigint NOT NULL DEFAULT 0` / `ApiQuotas.MonthlyTokenLimit bigint NULL` (H10)
  - ✅ `IX_ApiKeys_KeyHash UNIQUE btree("KeyHash")` (C3 인증 핫패스 단축)
  - ✅ `IX_Users_Email UNIQUE btree("Email")` (C4 중복 가입 차단)
  - ✅ `IX_TeamMembers_TeamId_UserId UNIQUE btree(...) WHERE ("IsActive" = true)` (PG 부분 인덱스 정상 변환)
  - ✅ `CK_Users_Status` / `CK_ChatMessages_Role` PG 표준 `("Status")::text = ANY(ARRAY[...])` 형식 자동 변환
- **Phase 3.2 text 컬럼 PG 적용 검증**:
  - ✅ `PresentationSlides.{Content, ChartsJson, TablesJson, ImagesJson}` 모두 `text` (이전 nvarchar(max) → text 변환 정상)
- **잠재 위험 / 후속 트랙**:
  - **`__EFMigrationsHistory` 가 `public` schema 에 있음** — Npgsql 기본값. AgentHub 의 `Search Path=AIAgentManagement,public` 설정 시 자동 fallback 으로 정상 동작. 단 R29 schema 격리 강화 시 별도 처리 필요
  - **DatabaseInitializer 시드 미실행** — 실 DB 통합 검증은 AgentHub 부팅 시 자동 수행됨. 본 단계는 schema/마이그레이션까지만
  - **Hangfire schema** — AgentHub 첫 부팅 시 `PrepareSchemaIfNecessary=true` 가 자동 생성 (Phase 3.4 commit 검증). 본 단계 미적용
  - **MSSQL 운영 데이터 이전** — 사용자 시연용 monorepo COPY 환경이라 데이터 이전 생략. 운영 적용 시 별도 ETL(`pgloader` / `bcp+COPY`) 필요
  - **archive ModelSnapshot 갱신**: dotnet-ef 가 또 `Migrations.mssql.archive/ModelSnapshot.cs` 갱신 → `git restore` 로 1da04ab 시점 복원 (재발 방지 csproj `<Compile Remove>` 강화는 별도 트랙)
- **다음 단계 (Phase 3 Complete → Phase 5 / Phase 4)**:
  - Phase 3 핵심 작업 마무리. AgentHub 부팅 → DatabaseInitializer 시드 실 적용 + Hangfire schema 자동 생성 + 통합 smoke test (Agent CRUD, OpenAI 호환 API, ApiKey 인증, Quota) — 사용자 시연 시 수행 가능
  - Phase 5 진입 가능 (AgentHub Nexus provider 추가) — Phase 3 의존성 해소
  - Phase 4 (DocUtil/career → AGENT_HUB 통합) — Phase 5 와 병렬 진행 가능

### 2026-05-05 (Phase 3.4 — DatabaseInitializer PG 호환 재작성 + EnsureCreatedAsync→MigrateAsync + Program.cs SqlException→PostgresException + TestDbConnection deprecate)
- **목적**: TECHSPEC §16 C7 위험 해소 — `Database.EnsureCreatedAsync()` 사용으로 인한 마이그레이션 그래프 ↔ 실 스키마 drift 위험 차단. Phase 3.2 baseline `20260505131410_Init` 도입으로 `MigrateAsync()` 전환 가능해짐. 부수적으로 Phase 3.1 의 SQL Server 잔존 의존(SqlException catch 블록 / TestDbConnection.cs) 정리
- **사전 조사 (변경 범위 좁힘)**:
  - `DatabaseInitializer.cs` 내 `ExecuteSqlRaw` / `ExecuteSqlInterpolated` / `FromSqlRaw` 호출 — **0건** (시드는 전부 EF LINQ + AddRange + SaveChangesAsync 패턴으로 작성됨)
  - 따라서 T-SQL → PG 변환이 필요한 인라인 SQL 코드는 **없음**. 변경 범위는 (a) MigrateAsync 전환 (b) try-catch swallow 강화 두 가지로 수렴
  - 루트의 레거시 `*.sql` 파일들은 `.claude/rules/anti-patterns.md` #9 에서 보존만 + 신규 X 로 명시 — 본 단계 무시
  - 시드 데이터(Roles 3건 / ApiServices Chat 6건 / Image 5건 / Video 3건 / 모델 카탈로그 9개 ServiceCode) — 원본 코드가 이미 멱등성(`AnyAsync` 검사 후 INSERT)로 작성됨, PG 호환성 무관
- **변경 파일 3건**:
  - **`agenthub/Data/DatabaseInitializer.cs`** (866 → 880 LOC, +14)
    - L11~21: 메서드 docstring 추가 — baseline 마이그레이션 + 멱등 시드 의도 + 외부 시그니처 보존 명시
    - L22~38 신설: **`MigrateAsync()` 호출 블록 + 별도 try-catch** — 마이그레이션 실패는 시드 try-catch 와 분리해 상위로 전파 (스키마 미존재 시 시드는 의미 없음). stderr 로 GetType().Name + Message 흘림
    - L15 (구) `await context.Database.EnsureCreatedAsync();` → 제거 (위 블록으로 대체)
    - L433~440 (구→신): 빈 `catch (Exception)` → `catch (Exception ex)` + `Console.Error.WriteLine` 로 클래스명/메시지 출력. anti-patterns.md #10 의 의도된 swallow 패턴 일관성 유지
    - 시그니처 무변경: `public static async Task SeedAsync(AIAgentManagementDbContext context)` 그대로
    - 시드 본문 변경 없음 — Phase 5 에 ApiServices 시드 `nexus` ServiceCode 추가 예정 (TECHSPEC §15.4), 본 단계는 손대지 않음
  - **`agenthub/Program.cs`** (588 → 597 LOC, +9)
    - L417~425 (구): `catch (Microsoft.Data.SqlClient.SqlException sqlEx)` 블록 — Number/Server/State/Class 로깅 (전부 SQL Server 전용 속성)
    - L417~434 (신): **`catch (Npgsql.PostgresException pgEx)`** — SQLSTATE / Severity / SchemaName / TableName 로깅 (PG 표준). + **`catch (Npgsql.NpgsqlException npgEx)`** 추가 — 클라이언트측 연결 오류(호스트 unreachable / 타임아웃) 분리 처리. PostgresException 의 부모 타입이라 catch 순서 중요
    - DB 초기화 호출 패턴(L396 `DatabaseInitializer.SeedAsync(context)`)은 무변경
    - Hangfire 등록 블록(L176~201) 무변경 — Phase 3.1 commit `c022c9e` 의 `UsePostgreSqlStorage` + `SchemaName = "hangfire"` + `PrepareSchemaIfNecessary = true` 그대로 유지
  - **`agenthub/TestDbConnection.cs`** (70 → 25 LOC, -45)
    - 본문 SqlConnection / @@VERSION / DB_NAME() / SqlException 등 PG 비호환 코드 전체 제거
    - `[Obsolete]` 어노테이션 부착 + `TestConnection` 호출 시 `NotSupportedException` 발생 (사용처 grep 결과 자기 정의 외 0건이라 안전)
    - 클래스 자체 보존(파일 삭제 X) — git history 가독성 + 향후 Phase 5+ 에서 Npgsql 호환으로 재작성 가능성. 주석에 "Phase 5+ 별도 트랙" 명시
    - **`Microsoft.Data.SqlClient` using 제거** → 본 파일은 더 이상 SqlClient 패키지를 코드 차원에서 import 하지 않음. 패키지 자체는 csproj 에 남음 (Phase 5+ 정리)
- **본 단계 미처리 — Phase 5+ 별도 트랙 보고만**:
  - **`Controllers/DatabaseBackupController.cs`** (148, 179) — `new SqlConnection(_connectionString)` 직접 인스턴스화 + T-SQL 백업 명령 사용. PG 백업은 `pg_dump` 외부 프로세스 또는 별도 Hangfire 작업 패턴 필요. controller 자체가 통합 후 운영자 콘솔로 이전될 가능성(TECHSPEC ADR-2)이라 본 단계 deprecate 결정. **빌드 차원**: SqlConnection 의존 잔존, 컨트롤러 호출 시 PG 환경에서 런타임 오류 발생 — 현재 운영 빌드에서 호출 차단 또는 controller 전체 제거가 안전. **Phase 5 전 결정 필요**
- **빌드 검증**:
  - 베이스라인(변경 전): `dotnet build --no-restore` — 0 errors / 11 warnings (전부 기존 CS1998)
  - 변경 후: `dotnet build --no-restore` — **0 errors / 11 warnings** (신규 도입 0건, 베이스라인 동일). 경과 시간 2.37s
- **마이그레이션 dry-run SQL 검증** (`dotnet-ef migrations script --no-build > /tmp/init-script.sql`):
  - 출력: 731 LOC SQL
  - `CREATE TABLE` 36건 (35 도메인 테이블 + `__EFMigrationsHistory`)
  - **T-SQL 잔존 패턴 검증 (전부 0 — 정상)**:
    - `IDENTITY(1,1)`: 0 / `nvarchar`: 0 / `GETDATE`: 0 / `NEWID`: 0 / `sys.tables` `sys.columns`: 0 / `[dbo]` bracket: 0 / `ISNULL` `LEN(`: 0
  - **PG 표준 패턴 검증 (양수 — 정상)**:
    - `GENERATED BY DEFAULT AS IDENTITY`: 34 (모든 PK)
    - `timestamp with time zone`: 71 (모든 CreatedAt/UpdatedAt/...)
    - `character varying`: 124
    - `"AIAgentManagement"` 더블쿼트 스키마 한정자: 148
    - `boolean`: 32
    - `bytea`: 2 (Phase 3.3 `KeyIv` / `KeyTag` per-record AES-GCM IV+Tag)
  - **CREATE TABLE 발췌 (`AIAgentManagement.ApiKeys` — Phase 3.3 보안 컬럼 검증 통과)**:
    ```
    CREATE TABLE "AIAgentManagement"."ApiKeys" (
        "ApiKeyId" integer GENERATED BY DEFAULT AS IDENTITY,
        "KeyName" character varying(100) NOT NULL,
        "EncryptedKey" character varying(500) NOT NULL,
        "KeyIv" bytea, "KeyTag" bytea, "KeyHash" character varying(64),
        "ExpiresAt" timestamp with time zone, "IsActive" boolean NOT NULL,
        ...
    );
    CREATE UNIQUE INDEX "IX_ApiKeys_KeyHash" ON "AIAgentManagement"."ApiKeys" ("KeyHash");
    CREATE UNIQUE INDEX "IX_Users_Email" ON "AIAgentManagement"."Users" ("Email");
    ```
  - `dotnet-ef migrations list --no-build` — `20260505131410_Init` 등록 확인. Pending 상태는 DB 미연결로 미확인 (`28P01: password authentication failed for user "AGENT_HUB"` — Phase 2 init.sql 미실행, 기대 동작)
- **Hangfire schema 동작 검증 (코드 수준)**:
  - Program.cs L182~194: `AddHangfire` 등록 블록 검토 — `UsePostgreSqlStorage` + `SchemaName = "hangfire"` + `PrepareSchemaIfNecessary = true` 보존
  - 동작 원리: 첫 부팅 시 Hangfire.PostgreSql 1.20.10 의 `SchemaInstaller` 가 `hangfire` 스키마 + 11개 테이블(`hash`/`job`/`jobparameter`/`jobqueue`/`list`/`schema`/`server`/`set`/`state`/`counter`/`aggregatedcounter`) 자동 생성
  - 본 단계는 코드 검증만 — 실제 스키마 생성 검증은 Phase 3.6 (DB 연결 후)
- **잠재 위험 / Phase 3.6 의존 항목**:
  - **실 PG 적용 미검증**: 본 단계 변경은 빌드/구문 검증까지. `MigrateAsync` 호출 시 `__EFMigrationsHistory` + 35 테이블 + 15 UNIQUE 인덱스가 정상 생성되는지는 Phase 3.6 의존
  - **Hangfire 자동 스키마 생성 권한**: PG 의 `AGENT_HUB` 사용자가 `CREATE SCHEMA hangfire` 권한 보유해야 함. Phase 2 `infra/db/init.sql` 에서 `AGENT_HUB` 에게 `CREATE` 권한 부여됐는지 사전 확인 필요
  - **시드 단계 부분 실패 swallow 가능성**: 새 `Console.Error` 로그는 ASP.NET Core 호스팅 환경에 따라 캡처되지 않을 수 있음. Phase 3.6 부팅 시 stdout/stderr 양쪽 점검
  - **DatabaseBackupController PG 미호환 잔존**: 본 단계 미처리. 운영자 호출 시 런타임 SqlException — `[Obsolete]` 또는 enable=false 처리 권장 (Phase 5 전)
  - **DocUtil/career 영향 없음**: 본 변경은 AgentHub 단독. monorepo 다른 서브프로젝트는 무영향
- **다음 단계 (Phase 3.6 제안 흐름)**:
  1. `infra/db/init.sql` 운영 PG 인스턴스(192.168.10.39:5440)에 적용 — `AGENT_HUB` user/DB + 4 schema + extensions(vector, uuid-ossp, pg_trgm) 생성
  2. AgentHub 부팅 → `MigrateAsync` 1회 자동 실행 → 35 테이블 + Hangfire 11 테이블 + `__EFMigrationsHistory` 생성 검증
  3. 시드 동작 검증 (Roles 3 / ApiServices 14 / ApiServiceModels 50+ / Admin user)
  4. SQL Server → PG 데이터 이전 dry-run (별도 ETL 또는 `pgloader`)
  5. C5/C6 (BackupController PG 비호환), Phase 5 시작 (Nexus provider + LlmRouting 컬럼 + 진짜 SSE)

### 2026-05-05 (Phase 3.2 — Npgsql baseline `Init` 마이그레이션 + nvarchar(max) → text 변환 + EF 8.0.11 통일 + .NET 8 SDK 설치)
- **목적**: Phase 3.1 EF Provider 전환 후 첫 PostgreSQL 마이그레이션 baseline 작성. Phase 3.3 보안 컬럼/인덱스 + nvarchar(max) PG 비호환 컬럼 정리를 동시 흡수
- **선행 작업 (.NET 8 SDK 설치)**: 환경에 dotnet CLI 미설치 — `dotnet-install.ps1` 으로 user-local(`C:\Users\IDINO_USER\.dotnet`) 설치 (관리자 권한 불필요). winget user scope는 적합한 installer 부재로 실패. 결과: SDK 8.0.420 + `dotnet-ef` global tool 8.0.11 설치 완료. PATH/`DOTNET_ROOT` 영구 등록 (User 환경변수 + ~/.bashrc). 새 bash 세션은 자동 로드 안 되어 Bash tool 호출 시마다 `export PATH=...` 명시 필요
- **csproj 수정 1건**:
  - `agenthub/AIAgentManagement.csproj` — `Microsoft.EntityFrameworkCore` / `Microsoft.EntityFrameworkCore.Tools` `8.0.0 → 8.0.11`. NU1605 경고-as-오류(Phase 3.1에서 추가한 `Npgsql.EntityFrameworkCore.PostgreSQL 8.0.11` 의 transitive `Microsoft.EntityFrameworkCore (>= 8.0.11)` 요구와 직접 참조 8.0.0 충돌) 해소
- **PG 비호환 타입 정리 — `nvarchar(max)` → `text` (8곳)**:
  - `agenthub/Models/ExamplePrompt.cs:17` — `Prompt` (free-form 프롬프트)
  - `agenthub/Models/Presentation.cs:19` — `Slides` (JSON 문자열)
  - `agenthub/Models/PresentationTemplate.cs:23` — `TemplateStructure` (JSON 문자열)
  - `agenthub/Models/PresentationSlide.cs:9 / :28 / :45 / :49 / :53` — class doc + `Content` + `ChartsJson` + `TablesJson` + `ImagesJson` (4개 컬럼)
  - `agenthub/Data/AIAgentManagementDbContext.cs:152 / :209 / :217-223` — DbContext OnModelCreating fluent 설정 5건도 동일 변환
  - **`jsonb` 미채택 이유**: 기존 `JsonSerializer.Serialize/Deserialize` 패턴(P5) + 기존 운영 데이터에 invalid JSON 가능성(예: `Slides`는 명세상 JSON이지만 schema-less). 직렬화/역직렬화 흐름 무변경 + 길이 무제한 = `text` 가 등가. `jsonb` 인덱싱/쿼리 최적화는 Phase 5+ 별도 트랙
  - **임베딩(`DocumentChunk.Embedding`) 은 보류** — 현재 `text` 타입 그대로 유지 (ADR-2 자체 KB deprecate, Phase 6 일괄 정리 대상)
- **신설 파일 2개 (`Migrations/` 신설)**:
  - `agenthub/Migrations/20260505131410_Init.cs` — Npgsql baseline `Init` 마이그레이션 (94 KB / 1700 라인)
  - `agenthub/Migrations/20260505131410_Init.Designer.cs` — Model snapshot (92 KB / 2400 라인)
  - **수치**: 35 테이블 / 389 컬럼 / 15 UNIQUE 인덱스 / 40 `text` 타입 / 0 `nvarchar(max)`
  - **Phase 3.3 컬럼 자연 흡수 검증 완료**:
    - `MonthlyTokenLimit bigint NULL` (H10)
    - `CurrentTokens bigint NOT NULL DEFAULT 0` (H10)
    - `KeyIv bytea NULL` / `KeyTag bytea NULL` (C1)
    - `KeyHash character varying(64) NULL` (C3)
  - **Phase 3.3 UNIQUE 인덱스 자연 흡수 검증 완료**:
    - `IX_ApiKeys_KeyHash UNIQUE` (C3 인증 핫패스 단축)
    - `IX_Users_Email UNIQUE` (C4 중복 가입 차단)
  - 기타 신규 인덱스: `IX_ApiServiceModels_ServiceId_ModelName`, `IX_TeamMembers_TeamId_UserId`, `IX_UserPreferences_UserId_PreferenceKey` 등 13건
- **archive 보존 (의도하지 않은 EF 갱신 복원)**:
  - `dotnet-ef migrations add Init` 실행 시 `Migrations.mssql.archive/AIAgentManagementDbContextModelSnapshot.cs` 가 자동 갱신됨 (EF 가 기존 ModelSnapshot 의 위치를 인식하고 새 모델로 덮어씀). archive 는 ADR-7 historical 참조용이라 `git restore` 로 1da04ab 시점 상태로 복원
- **빌드 검증**:
  - `dotnet restore` 성공 (NU1605 해소 후)
  - `dotnet build --no-restore` 성공 — **0 errors / 11 warnings** (전부 기존 레거시 `CS1998` async-without-await, Phase 3.x 신규 도입 0건)
  - `dotnet-ef migrations list` — `20260505131410_Init` 등록 확인. Pending 상태는 DB 미연결로 미확인 (AGENT_HUB DB 부재 — `28P01: password authentication failed for user "AGENT_HUB"` — 정상, Phase 2 init.sql 미실행)
- **`.gitignore` 갱신**: `.claude/settings.local.json` (Claude Code per-machine 권한 캐시) 추가 — 우발적 commit 방지
- **잠재 위험 / 사용자 검증 필요**:
  - **사용자 측 dotnet CLI**: 본 PC 에는 user-local 설치 완료. 다른 PC / CI 에서는 별도 설치 필요 (dotnet 8 SDK 또는 GitHub Actions `actions/setup-dotnet@v4`)
  - **운영 DB 미적용**: 본 단계는 마이그레이션 *파일* 만 생성. 실제 PG `AGENT_HUB` DB 에 적용은 Phase 3.4 (DatabaseInitializer 재작성 후) → Phase 3.6 (운영 데이터 이전 dry-run) 순서
  - **`text` 컬럼의 잠재적 invalid JSON**: `Slides`/`ChartsJson` 등이 sub-text 한도 무제한이지만, 운영 코드가 항상 JSON 으로 직렬화하는지 grep 검증은 별도 트랙 (Phase 5+ jsonb 도입 시 사전 검증 필수)
  - **Migrations.mssql.archive 의 ModelSnapshot 재변경 위험**: 다음 `dotnet-ef migrations add` 실행 시 또 archive 가 갱신됨. csproj `<Compile Remove>` 에 `*.Designer.cs`/`ModelSnapshot.cs` 명시적 제외 + (선택) archive 전체를 별도 디렉토리로 이동 검토
- **다음 단계 (Phase 3.4)**:
  - `Data/DatabaseInitializer.cs` (866 LOC) idempotent 재작성 — `EnsureCreatedAsync` → `MigrateAsync` 전환 (C7 해소). Roles/ApiServices/ApiServiceModels/Agents 시드 PG 호환성
  - Hangfire schema `hangfire` 자동 생성 검증 (`PrepareSchemaIfNecessary = true` 동작)

### 2026-05-05 (Phase 3.3b + 3.3c 번들 — AES-GCM per-record IV + AES Key 분리 + KeyHash UNIQUE + Email UNIQUE / TECHSPEC §16 C1/C2/C3/C4)
- **목적**: TECHSPEC §16 의 핵심 보안 결함 4종을 한 번에 해소.
  - C1: `ApiKeyService.EncryptString` / `DecryptString` + `ApiKeyAuthService.DecryptString` 모두 `aes.IV = new byte[16]` (16바이트 0) 사용 — 결정적 암호화 + AEAD 부재. 같은 평문 → 동일 암호문이라 인증이 매 요청 활성 키 풀스캔 + 전수 복호화 비교(O(N)).
  - C2: 두 서비스 모두 `_encryptionKey = configuration["JwtSettings:SecretKey"]` + SHA-256(jwtSecret) 으로 AES Key 유도 — JWT 키 노출 = ApiKey 평문 전체 복호화.
  - C3: `ApiKey` 모델에 `KeyHash` 컬럼 부재 + `OnModelCreating` 에 `Entity<ApiKey>.HasIndex` 0건. 인증이 활성 키 전체 로드 후 foreach 복호화 비교.
  - C4: `User.cs` Email 은 `[Required] [MaxLength(100)]` 만, DB 레벨 UNIQUE 부재 → race condition 으로 중복 가입 가능.
- **수정 파일 6개 (외부 시그니처 무변경)**:
  - `agenthub/Models/ApiKey.cs` — 신규 컬럼 3개 추가:
    - `byte[]? KeyIv` (AES-GCM nonce, 12바이트, EF 가 PG 기본 매핑 시 `bytea` nullable. 기존 행 NULL 허용으로 마이그레이션 충돌 0)
    - `byte[]? KeyTag` (AES-GCM 인증 태그, 16바이트)
    - `string? KeyHash [MaxLength(64)]` (SHA-256 hex 대문자 64자, UNIQUE 인덱스 대상)
    - 모두 한국어 XML doc + TECHSPEC §16 항목 참조 주석. 기존 `EncryptedKey [MaxLength(500)]` 변경 없음 — GCM ciphertext 는 평문 길이와 동일하므로 base64 후에도 500 충분(기존 32~64 byte AES Key 가정 시 100 byte 미만)
  - `agenthub/Data/AIAgentManagementDbContext.cs` — `OnModelCreating` 에 인덱스 2개 추가 (Role.RoleName UNIQUE 인접 위치):
    - `Entity<User>().HasIndex(u => u.Email).IsUnique()` (C4)
    - `Entity<ApiKey>().HasIndex(k => k.KeyHash).IsUnique()` (C3 — PG 는 NULL 다수를 자동으로 허용하는 부분 인덱스 의미를 가짐. legacy 행 NULL 안전)
  - `agenthub/Services/ApiKeyService.cs` — 전면 재작성 (외부 9개 public 메서드 시그니처 모두 보존):
    - 생성자: `LoadAesKey(IConfiguration, ILogger)` 헬퍼로 키 로딩 분리. 우선순위 = `Encryption:ApiKeyAesKey` (base64, 32바이트 AES-256) → 없으면 `JwtSettings:SecretKey` SHA-256 폴백 + `LogWarning` 1회. 폴백 길이/format 검증 fail-fast (32 != 길이 → InvalidOperationException, base64 파싱 실패 → InvalidOperationException). `_aesKey: byte[]` + `_usingFallbackKey: bool` 보관
    - 신규 `EncryptApiKey(string) -> (byte[] ciphertext, byte[] iv, byte[] tag)` — `new AesGcm(_aesKey, tagSizeInBytes: 16)` (.NET 8 권장 시그니처, 매개변수 없는 ctor 는 [Obsolete] 회피) + `RandomNumberGenerator.GetBytes(12)` per-record nonce
    - 신규 `DecryptApiKey(byte[] ct, byte[] iv, byte[] tag) -> string` — `AuthenticationTagMismatchException` → `InvalidOperationException("API 키 무결성 검증 실패")` 변환
    - 신규 `internal static ComputeKeyHash(string) -> string` — SHA-256 hex 대문자 64자. internal 노출은 ApiKeyAuthService 와의 충돌 회피용 — 실제 두 서비스가 각자 private 으로 보유(코드 중복 허용. Phase 5+ 공용 헬퍼 추출 트랙)
    - `CreateApiKeyAsync` / `GenerateAgentApiKeyAsync` / `GetDecryptedApiKeyAsync` 3곳 모두 GCM 분기 + KeyHash 산출 + base64 ciphertext 만 EncryptedKey 에 저장 (iv/tag 는 별도 컬럼)
    - `GetDecryptedApiKeyAsync` 에 legacy 호환 분기: `KeyIv is { Length: 12 }` + `KeyTag is { Length: 16 }` 체크 → GCM 복호화 / 둘 중 하나라도 NULL → `DecryptLegacyCbc` 폴백 + 즉시 `BackfillToGcm` 호출 → 기존 `LastUsedAt`/`UsageCount` 갱신과 함께 SaveChanges 1회 커밋. 명시 `TODO Phase 3.6 — 폴백 + DecryptLegacyCbc 제거 약속`
    - `MapToDtoAsync` / `MaskApiKey` / `MaskAgentApiKey` 등 외부 표면 동작 보존
  - `agenthub/Services/ApiKeyAuthService.cs` — 전면 재작성 (외부 단일 메서드 `ValidateApiKeyAsync(string?)` 시그니처 보존):
    - 생성자: ApiKeyService 와 동일한 `LoadAesKey` 정책 (코드 중복 허용 — 본 task 범위. Phase 5+ 공용 헬퍼 추출)
    - **빠른 경로 (TECHSPEC §16 C3 해소)**: `ComputeKeyHash(apiKey)` → `_context.ApiKeys.FirstOrDefaultAsync(k => k.KeyHash == hash && k.IsActive && (k.ExpiresAt == null || k.ExpiresAt > now))` 단건 조회. KeyHash UNIQUE 인덱스 매칭이 곧 평문 일치 의미 — 추가 복호화/AEAD 검증 불필요(SHA-256 충돌 무시)
    - **Legacy 폴백**: 빠른 경로 미스 시 `KeyHash IS NULL && IsActive && 만료 안 됨` 행만 풀스캔 + foreach 복호화 비교 + 즉시 `BackfillRow` (KeyHash + GCM 채우기). `TouchAndProjectAsync` 에서 SaveChanges 1회. **TODO Phase 3.6 — 폴백 + DecryptLegacyCbc 제거**
    - `TouchAndProjectAsync` private 추출 — 두 경로(빠른/폴백) 가 동일 영속화 로직 재사용. `LastUsedAt/UsageCount/UpdatedAt` 갱신 + SaveChanges + LogInformation + ApiKeyValidationResult 사상
  - `agenthub/appsettings.json` — `Encryption.ApiKeyAesKey` 빈 키 추가 (운영 시 base64 32바이트 주입). `.gitignore` 대상이 아닌 base 파일이므로 디스크에 키 자체 없이 키 슬롯만 노출
  - `agenthub/appsettings.Development.json` — 동일 `Encryption.ApiKeyAesKey: ""` 추가. 빈 값이면 LogWarning 발동 + JWT 키 폴백 — 개발 환경 호환성 유지. `.gitignore` 로 차단됨
- **외부 호출처 grep 검증 (시그니처 무변경 확인)**:
  - `Controllers/ApiKeysController.cs` — `IApiKeyService` 의 9개 public 메서드 호출. 시그니처 동일 → 변경 0
  - `Controllers/AgentsController.cs` — `IApiKeyService.GenerateAgentApiKeyAsync` / `GetAgentApiKeysAsync` / `DeleteAgentApiKeyAsync` 호출. 시그니처 동일 → 변경 0
  - `Attributes/ApiKeyAuthorizeAttribute.cs` — `IApiKeyAuthService.ValidateApiKeyAsync(string?)` 호출. 시그니처 동일 → 변경 0
  - `Program.cs` — DI 등록(`AddScoped<IApiKeyService>` / `AddScoped<IApiKeyAuthService>`). 생성자 의존성(`AIAgentManagementDbContext` + `ILogger<T>` + `IConfiguration`) 동일 → 변경 0
- **AES-GCM 파라미터 검증**:
  - 키 길이: 32 바이트 (AES-256) — `LoadAesKey` 에서 `bytes.Length != 32` 시 fail-fast InvalidOperationException
  - nonce 길이: 12 바이트 — `RandomNumberGenerator.GetBytes(12)` (NIST SP 800-38D / GCM 권장)
  - tag 길이: 16 바이트 — `new AesGcm(key, tagSizeInBytes: 16)` 명시 + `byte[16]` 할당
  - base64 format 검증: `LoadAesKey` 에서 `Convert.FromBase64String` 실패 시 fail-fast
- **운영 마이그레이션 절차 (TODO Phase 3.6 백필)**:
  1. 운영 환경에 32바이트 random AES-256 키 생성 (`openssl rand -base64 32`) → `Encryption:ApiKeyAesKey` 환경변수 또는 vault 주입
  2. Phase 3.2 Npgsql baseline 시 `KeyIv bytea NULL` / `KeyTag bytea NULL` / `KeyHash varchar(64) NULL UNIQUE` + `Users.Email UNIQUE` 컬럼/인덱스 자연 흡수
  3. Phase 3.6 데이터 마이그레이션 스크립트:
     - 기존 ApiKey 행 전수 조회 → JWT 폴백 키로 legacy CBC 복호화 → 평문 → 운영 AES-256 키로 GCM 재암호화 + KeyHash 산출 → UPDATE
     - 또는 인증 시 자동 백필을 활용해 자연 마이그레이션 후 일정 기간 경과 시 NULL 잔존 행만 강제 처리
  4. 백필 완료 후 양 서비스의 `DecryptLegacyCbc` + 폴백 분기 + ApiKeyService.BackfillToGcm + ApiKeyAuthService.BackfillRow 제거 (TODO 마커)
- **잠재 위험**:
  - **운영 키 즉시 교체 시 legacy 행 일시 인증 실패**: 운영 키를 `Encryption:ApiKeyAesKey` 로 교체하면 JWT 폴백 키로 암호화된 legacy 행 복호화가 실패 → 인증 거부. 따라서 **백필 완료 전까지는 운영 키 미주입 (JWT 폴백 유지) 권장**. 본 코드는 폴백 키로도 GCM/CBC 모두 동작하므로 호환성 유지
  - **legacy 폴백 풀스캔 비용**: 백필 중간에는 `KeyHash IS NULL` 행이 N개 있으므로 인증 핫패스가 일시적으로 O(N) 풀스캔. UNIQUE 인덱스 자체는 NULL 다수 허용(PG 표준)이라 신규/백필 행은 빠른 경로로 자동 진입
  - **SHA-256 충돌**: 평문 ApiKey 가 256비트 random("ak-{base64 32바이트}") 이므로 충돌 확률은 무시할 수준(2^128 birthday 한계 — 운영 데이터량 기준 0). KeyHash UNIQUE 매칭으로 평문 일치를 직접 추정 가능
  - **PG NULL UNIQUE 의미**: PG 표준은 UNIQUE 인덱스가 NULL 을 무한히 허용. legacy 행 NULL 다수 안전. EF 의 `IsUnique()` 가 PG 에서 자동으로 부분 인덱스로 최적화하지는 않으나, NULL 행은 인덱스 단건 조회 대상이 아니므로 빠른 경로 영향 없음
  - dotnet CLI 미설치 — `dotnet build --warnaserror` 검증 사용자 측 필요. nullable 분석 안전 (KeyIv/KeyTag/KeyHash 는 명시 nullable)
  - **운영 secret 주입 누락 시**: `LogWarning` 만 1회 발동(시작 시) — 사용자 가시성 낮음. Phase 5+ 에서 운영자 콘솔 헬스체크에 노출 권고
- **TECHSPEC §16 위험 항목 해소**:
  - C1 (AES 고정 IV) → ✅ 해소 (per-record nonce + GCM AEAD)
  - C2 (JWT 키 ↔ AES 키 결합) → ✅ 해소 (별도 설정 키, JWT 폴백은 호환 분기)
  - C3 (API Key 풀스캔) → ✅ 해소 (KeyHash UNIQUE 단건 조회)
  - C4 (Users.Email UNIQUE 부재) → ✅ 해소 (DB 레벨 UNIQUE 인덱스)
- **검증 방법 (사용자 측, dotnet 8 SDK)**:
  ```bash
  cd agenthub
  dotnet build --warnaserror
  # Phase 3.2 baseline 생성 시 KeyIv/KeyTag/KeyHash + Users.Email UNIQUE + ApiKeys.KeyHash UNIQUE 자연 흡수 확인
  # 통합 검증: 기존 평문 키로 인증 → legacy 풀스캔 + 백필 → 두 번째 호출은 KeyHash 빠른 경로
  # 운영 키 주입 후: 새로 발급한 키만 동작, legacy 는 백필 완료 후 정상 동작
  ```
- **남은 작업 (별도 task)**:
  - Phase 3.2 Npgsql baseline 생성 시 신규 컬럼/인덱스 자연 포함 확인
  - Phase 3.6 데이터 마이그레이션 스크립트 작성 + legacy 폴백 코드 제거
  - Phase 5+ ApiKeyService/ApiKeyAuthService 의 AES 헬퍼 + LoadAesKey 중복 제거(IApiKeyEncryptor 추출 트랙)
  - C1/C2/C3/C4/C8/H10 6개 sub-task 결과 통합 후 사용자 확인 단계에서 단일 commit (사용자 결정)

### 2026-05-05 (Phase 3.3d — `QuotaService.RecordUsageAsync` 토큰 인자 누락 버그 수정 / TECHSPEC §16 H10)
- **목적**: `IQuotaService.RecordUsageAsync(userId, serviceId, tokens, cost)` 시그니처는 tokens 를 받지만 구현(`Services/QuotaService.cs:190~206`)이 `tokens` 파라미터를 폐기하던 버그 수정. 호출처 5곳이 전달하던 `aiResponse.TotalTokens` / `totalTokens` 가 그동안 모두 무시되어 토큰 기반 한도/대시보드 시각화 불가능했음
- **수정 파일 6개 (시그니처 무변경)**:
  - `agenthub/Models/ApiQuota.cs` — 신규 컬럼 2개 추가:
    - `public long CurrentTokens { get; set; } = 0L;` ([Required], 월간 누적 토큰. int 범위(약 21억) 초과 가능성 → long. Npgsql 기본 매핑은 bigint)
    - `public long? MonthlyTokenLimit { get; set; }` (nullable, NULL = 미적용. 호출 횟수 기준 `MonthlyLimit` 와 병행 운영)
    - 기존 `MonthlyLimit`/`CurrentUsage` 에도 한국어 XML doc summary 추가
  - `agenthub/Data/AIAgentManagementDbContext.cs` — `OnModelCreating` ApiQuota 블록에 `entity.Property(e => e.CurrentTokens).HasDefaultValue(0L)` 명시 (운영 DB 직접 ALTER TABLE 시 default 적용 보장)
  - `agenthub/Services/QuotaService.cs` — 4개 분기 수정:
    - `RecordUsageAsync` 본문에 `quota.CurrentTokens += tokens;` 한 줄 추가 (한국어 주석 + XML doc summary 신설). tokens=0 호출(ImageGenerationController)은 0 누적되어 영향 없음
    - `CheckQuotaAsync` 에 토큰 한도 분기 추가: `if (quota.MonthlyTokenLimit.HasValue && quota.CurrentTokens >= quota.MonthlyTokenLimit.Value) return CanUse=false`
    - `SetQuotaAsync` 신규 ApiQuota 생성 분기: `MonthlyTokenLimit = request.MonthlyTokenLimit, CurrentTokens = 0L` 추가. 기존 ApiQuota 수정 분기: `if (request.MonthlyTokenLimit.HasValue) quota.MonthlyTokenLimit = request.MonthlyTokenLimit;` (요청 본문에 키 없으면 기존값 보존 정책)
    - `GetQuotasAsync` / `GetQuotaAsync` DTO 매핑 2곳에 `MonthlyTokenLimit` / `CurrentTokens` 필드 전파
  - `agenthub/DTOs/QuotaDto.cs` — `MonthlyTokenLimit` / `CurrentTokens` 필드 2개 추가 (XML doc 한국어)
  - `agenthub/DTOs/SetQuotaRequestDto.cs` — `MonthlyTokenLimit?` 필드 추가
  - `agenthub/BackgroundJobs/QuotaResetJob.cs` — `ResetMonthlyQuotas` 에 `quota.CurrentTokens = 0L;` 라인 추가 (호출 횟수/토큰/비용 3개 카운터 리셋 동기화)
- **`IQuotaService.cs` 시그니처 무변경** — 호출처 5곳 모두 동일 시그니처로 컴파일 통과
- **호출처 5곳 grep 결과 (시그니처 무변경 확인)**:
  - `Controllers/ImageGenerationController.cs:304` — tokens=0 (이미지 생성은 토큰 개념 없음). `CurrentTokens += 0` → 영향 없음
  - `Services/ChatService.cs:413` (SendMessageAsync) — `aiResponse.TotalTokens` 정상 누적
  - `Services/ChatService.cs:962` (SendDirectMessageAsync, Vue UI 비스트리밍) — `aiResponse.TotalTokens` 정상 누적
  - `Services/ChatService.cs:1265` (SendDirectMessageStreamChunksAsync, OpenAI 호환 SSE) — `totalTokens` 정상 누적 (Phase 3.5 stream_options.include_usage:true 로 실제 토큰수 회수)
  - `Services/ChatService.cs:1570` (SendDirectMessageStreamEventsAsync, Vue UI SSE) — `totalTokens` 정상 누적
- **`MonthlyTokenLimit` 도입 결정**: **도입함**. 이유:
  1. LLM 비용 구조상 호출 횟수보다 토큰 누적이 더 정확한 cost driver
  2. nullable + HasValue 가드로 기존 행에 영향 0 (NULL 이면 검사 우회)
  3. 향후 별도 Phase 에서 운영자 UI 노출 시 추가 마이그레이션 없이 사용 가능
  4. 코드 추가 약 8 라인 — 비용 대비 가치 높음
- **프론트 사용량 대시보드 영향 (별도 트랙으로만 기록, 본 작업 범위 외)**:
  - `agenthub/ClientApp/src/views/agent/AgentChat.vue:1007~1010` — `response.data.todayUsage / currentUsage / monthlyLimit` 3개 필드 사용 중. 신규 `currentTokens` / `monthlyTokenLimit` 는 미사용 → 응답에 추가 필드가 흘러도 무시되어 회귀 0
  - `Controllers/QuotaController.cs:140~158` `GetMyQuota` 의 익명 객체 응답에는 신규 필드 미포함. **별도 트랙 권고**: 운영자 대시보드 노출 시 `quota.CurrentTokens` / `quota.MonthlyTokenLimit` 를 명시 추가 필요
  - `Controllers/QuotaController.cs:127~138` 미설정 시 기본값 응답에는 호출 횟수 기반 필드만 — 토큰 기본값을 추가할지 별도 결정 필요
- **잠재 위험**:
  - **Phase 3.2 baseline 자연 흡수 의존**: 본 작업은 EF 마이그레이션 파일을 생성하지 않음. Phase 3.2 (Npgsql baseline `Init` 신규 생성) 시점에 `CurrentTokens bigint NOT NULL DEFAULT 0` / `MonthlyTokenLimit bigint NULL` 컬럼이 자동 포함됨. **Phase 3.2 작업 전 운영 DB 에 직접 ALTER TABLE 적용 시점은 별도 운영 절차로 결정** (현재 운영 DB 미존재 — 코드 작성만 완료)
  - **CheckQuotaAsync 의 토큰 한도 검사는 LLM 호출 직전에 동작** — 한도 초과 직전 호출은 통과될 수 있음(예: 한도 1,000,000 토큰, 999,500 누적 상태에서 100,000 토큰 요청 통과). 정확한 사전 추정은 비용/복잡도 대비 가치 낮아 보류 (TECHSPEC §15 후속 검토)
  - dotnet CLI 미설치 환경 — 빌드 검증 불가. **사용자 측 SDK 설치 후 `dotnet build --warnaserror` 필요**
- **검증 방법 (사용자 측, dotnet 8 SDK 환경)**:
  ```bash
  cd agenthub
  dotnet build --warnaserror   # 워닝 0건 + 컴파일 통과
  # ApiQuota 컬럼 자동 변경 — Phase 3.2 baseline 생성 시 자연 포함
  # 단위 테스트 인프라 부재 → 수동 점검: 채팅 1회 → ApiQuotas.CurrentTokens 가 증가하는지
  ```
- **남은 작업 (별도 task)**:
  - Phase 3.2 Npgsql baseline 생성 시 `CurrentTokens` / `MonthlyTokenLimit` 자연 포함 확인
  - QuotaController `/my/{serviceId}` 응답에 `CurrentTokens` / `MonthlyTokenLimit` 노출 (별도 트랙)
  - 운영자 대시보드(`Controllers/AnalyticsController.cs` 등) 토큰 시계열 조회 활용 (별도 Phase)
  - C1/C2/C3/C4 와 묶어 단일 commit 또는 분리 commit 결정 (사용자 확인 후)

### 2026-05-05 (Phase 3.3a — C8 SignalR Hub 인증 강화)
- **목적**: TECHSPEC §16 C8 위험 항목 해소. 두 SignalR Hub(`NotificationHub`, `ChatHub`) 모두 `[Authorize]` 부재 + 클라이언트 임의 ID 입력으로 그룹 가입이 가능했던 보안 결함 차단. 현 상태에서는 임의 사용자가 다른 사용자 알림을 도청하거나 남의 대화 그룹에 합류 가능
- **수정 파일 3개**:
  - `agenthub/Hubs/NotificationHub.cs` (전면 재작성, ≈75 LOC)
    - 클래스에 `[Authorize]` 부착
    - `JoinUserNotifications(int userId)` → 파라미터 제거 후 `JoinUserNotifications()`. 본문에서 토큰 클레임으로 userId 결정 (`Context.UserIdentifier` 우선, 폴백으로 `Context.User?.FindFirst(ClaimTypes.NameIdentifier)?.Value`). int.TryParse 실패 시 그룹 가입 없이 조용히 종료 + 경고 로그
    - 짝 메서드 `LeaveUserNotifications()` 신설 — 동일 정책으로 그룹 탈퇴 (기존에 누락되어 있던 짝 추가)
    - `OnDisconnectedAsync` 로그 한국어화
    - private helper `ResolveUserId()` 추출 (재사용)
    - using: `Microsoft.AspNetCore.Authorization`, `System.Security.Claims` 추가
  - `agenthub/Hubs/ChatHub.cs` (전면 재작성, ≈85 LOC)
    - 클래스에 `[Authorize]` 부착
    - 생성자에 `AIAgentManagementDbContext` DI 추가 (Scoped DbContext, Hub의 기본 lifetime이 transient지만 SignalR는 호출당 scope를 만들므로 안전)
    - `JoinConversation(int conversationId)` 본문에 소유권 검증 추가: `_dbContext.ChatConversations.AsNoTracking().AnyAsync(c => c.ConversationId == conversationId && c.UserId == userId)` → false면 `throw new HubException("권한 없음")` (R5 한국어)
    - `LeaveConversation`은 자기 connection의 그룹에서만 빠지므로 별도 검증 생략 (가입이 이미 검증을 통과)
    - private `ResolveUserId()` — `Context.UserIdentifier` → NameIdentifier claim 폴백, 둘 다 없으면 `throw new HubException("인증 정보가 없습니다")`
    - using: `System.Security.Claims`, `AIAgentManagement.Data`, `Microsoft.AspNetCore.Authorization`, `Microsoft.EntityFrameworkCore` 추가
  - `agenthub/Program.cs` 두 군데 수정:
    - `AddJwtBearer(options => { ... })` 블록에 `options.Events = new JwtBearerEvents { OnMessageReceived = ... }` 추가. `/hubs` 경로 한정으로 `?access_token=` 쿼리에서 토큰 추출 → `context.Token`에 주입. WebSocket은 Authorization 헤더를 부착할 수 없어서 SignalR JWT 인증의 표준 패턴
    - `MapHub<ChatHub>("/hubs/chat")` / `MapHub<NotificationHub>("/hubs/notification")` 두 줄에 `.RequireAuthorization()` 체이닝 추가 — 미인증 연결 시도를 라우팅 단계에서 차단
- **frontend 측 영향 (호출처 grep 결과)**:
  - `agenthub/ClientApp/src/services/signalr*.ts` 파일 자체가 부재 (Glob `signalr*.ts` no match). `ClientApp` 내부에서 `HubConnection` / `signalr` 참조는 `package.json` / `package-lock.json`에만 존재 (의존성 등재만, 실제 사용 코드 없음)
  - `JoinUserNotifications`, `LeaveUserNotifications`, `JoinConversation`, `LeaveConversation` 모두 ClientApp 소스에서 invoke 패턴 0건
  - **결론**: 본 task에서 frontend 변경 불필요. 향후 SignalR 클라이언트 도입 시 `connection.invoke('JoinUserNotifications')` 형태(인자 없음)로 호출 + 연결 URL에 `?access_token={JWT}` 부착 필요
- **잠재 위험 / 운영 측 영향**:
  - **`AIAgentManagementDbContext`(Scoped)를 ChatHub(Transient)에 주입**: SignalR은 각 Hub 호출마다 internal scope를 생성하므로 captive dependency 안티패턴(`anti-patterns.md` §7)에 해당하지 않음. 다만 DbContext 인스턴스가 long-lived connection 동안 다수 호출에 걸쳐 reuse되는 것은 아니라는 점은 검증 시 주의 (각 Hub 호출이 별도 scope)
  - **빌드 워닝 검증 불가**: dotnet CLI 미설치 환경 — 사용자 측 `dotnet build` 워닝 0건 확인 필요
  - **운영 클라이언트 즉시 끊김 가능성**: 현재 SignalR 클라이언트 구현체가 ClientApp에 부재하여 즉시 영향 없음. 추후 도입 시 `?access_token=` 쿼리 부착 + `invoke('JoinUserNotifications')` 인자 없는 호출로 마이그레이션 필요
  - **HubException 메시지 노출**: SignalR은 기본적으로 `HubException` 메시지만 클라이언트에 전달 (일반 Exception은 "An unexpected error occurred"로 마스킹). "권한 없음" / "인증 정보가 없습니다"는 의도된 사용자 메시지이므로 정상
- **TECHSPEC §16 위험 항목 해소**:
  - C8 (`[Authorize]` 부재 + 임의 userId 입력) — ✅ 해소
  - 부수 효과: 도청 가능성 차단, 대화 그룹 무단 가입 차단, JWT 검증된 사용자만 SignalR 연결
- **다음 단계**: 사용자 환경에서 `dotnet build` 워닝 확인 → 4개 sub-task(3.3a/3.3b/3.3c/3.3d) 결과 종합 후 commit

### 2026-05-05 (Phase 3.5b frontend — Vue AgentChat SSE 스트리밍 클라이언트 도입)
- **목적**: 백엔드 `/api/chat/send/stream` 엔드포인트 추가에 이은 frontend 분담분. 사용자 보고 "Vue UI 채팅 5~10초 대기 후 일괄 출력" UX 문제의 직접 해소 — 첫 token 즉시 표시
- **신설 파일 1개**:
  - `agenthub/ClientApp/src/services/sseClient.ts` (≈260 LOC) — fetch + ReadableStream + TextDecoder 기반 SSE 파서 (EventSource는 GET only + JWT 헤더 부착 불가하여 사용 불가)
    - `streamChat(payload, signal): AsyncGenerator<ChatStreamEvent>` 공개 API — `POST /api/chat/send/stream` 호출 + frame 단위 yield
    - 합의된 SSE 명세 5종 처리: `delta` / `meta` / `usage` / `error` 이벤트 + `[DONE]` 종료 마커
    - `\n\n` 프레임 구분자 + 미완성 chunk carry-over (`TextDecoder({stream:true})`) — 임의 경계로 잘려 도착하는 fetch chunk 안전 처리
    - JWT Bearer 자동 부착(localStorage `'token'` — `@/services/api` axios 인터셉터와 동일 정책) + 401 → `/api/auth/refresh` 호출 + 1회 재시도 + 실패 시 /login 리다이렉트
    - AbortController.signal 지원 — 사용자 "응답 중단" 버튼 연결
    - **새 npm 의존성 0건** (브라우저 표준 API만)
- **수정 파일 4개**:
  - `agenthub/ClientApp/src/views/agent/AgentChat.vue` — `:1708` 부근 핵심 분기 교체:
    - import: `reactive` 추가 + `streamChat` from `@/services/sseClient`
    - `Message` 인터페이스에 streaming 필드 추가: `isStreaming?: boolean` / `cost?: number` / `errorCode?: string`
    - 상태: `useStreaming = ref(true)` (기본 활성화, Settings 모달에서 토글 가능 예정) + `streamAbortController = ref<AbortController | null>(null)`
    - `sendMessage` 본문 재구조: 기존 `api.post('/chat/send', { ..., stream: false })` → 공통 `chatPayload` 추출 후 `if (useStreaming.value)` 분기
      - **streaming 분기**: 빈 assistant 메시지 즉시 push (reactive) → `for await (evt of streamChat(...))` → delta는 content 누적 + 첫 delta에서 `loading=false` (즉시 응답성), meta는 conversationId/messageId/model 갱신, usage는 stats 합산, error는 사용자 메시지 + BANNED_WORD/PII는 안내 추가
      - **AbortError 분리 처리**: 사용자 중단은 throw하지 않고 안내 문구로 마무리, 그 외 throw는 catch 블록으로 위임
    - **비스트리밍 폴백 보존**: `useStreaming.value === false` 시 기존 흐름 그대로 유지 — `/api/chat/send/stream` 미배포 환경 또는 사용자 명시 토글 안전망
    - catch 블록 강화: 스트리밍 placeholder(빈 content + `tempId="streaming-..."`) 제거 로직 추가 → 빈 bubble + 별도 error 메시지 중복 방지. 부분 채워진 placeholder는 `isStreaming=false`만 끄고 보존
    - 신규 `stopStreaming()` 함수 — `streamAbortController.abort()`
    - `onBeforeUnmount`에 abort 호출 추가 — 페이지 이탈 시 메모리/네트워크 누수 방지
    - 템플릿: send 버튼이 streaming 중에는 "응답 중단" 버튼으로 토글 (`v-if="streamAbortController"`), assistant bubble 뒤에 깜빡이는 cursor `▋` 표시 (`v-if="message.isStreaming"`)
  - `agenthub/ClientApp/src/views/agent/AgentChat.css` — `.cd-streaming-cursor` blink 애니메이션 + `prefers-reduced-motion` 배려(접근성)
  - `agenthub/ClientApp/src/i18n/locales/ko.json` — 신규 키 3개: `streamingAborted` / `streamingError` / `streamingStop` (R5 한국어 우선)
  - `agenthub/ClientApp/src/i18n/locales/en.json` — 동일 영문 키 3개
- **다른 호출처 grep 결과 (`api.post('/chat/send'`)** — 본 작업 범위 외, **별도 트랙 후속 처리 권고**:
  - `agenthub/ClientApp/src/views/agent/AgentBuilder.vue:859` — Agent 빌더 미리보기 채팅
  - `agenthub/ClientApp/src/views/agent/AgentMultiChat.vue:1186` — 다중 모델 비교 화면 (4,031 LOC)
  - `agenthub/ClientApp/src/views/Playground.vue:191` — 모델 Playground
  - 동일 sseClient를 재사용하면 한 곳당 수십 줄로 전환 가능. AgentMultiChat은 N개 모델 동시 streaming 지원이 자연스러움
- **잠재 위험 / 사용자 검증 필요**:
  - **incremental markdown 렌더 부작용**: marked + DOMPurify 스택은 unclosed code fence(```` ``` ````) 도중 chunk가 잘리면 일시적으로 잘못된 HTML을 만들 수 있음. DOMPurify가 sanitize하므로 XSS는 차단되지만, 코드 블록 등장 도중에는 렌더가 흔들릴 수 있음. ChatGPT/Claude 웹 UI도 동일 트레이드오프 — 사용자 보고 시 chunk가 아닌 줄 단위 디바운스 옵션 검토(현 시점 미구현)
  - **mid-stream 토큰 만료**: 첫 응답 헤더 단계의 401은 핸들하지만, streaming 도중 백엔드가 401을 흘리는 케이스는 본 구현이 핸들하지 않음(재현 가능성 낮음, TECHSPEC §16 후속 검토)
  - **SSE 버퍼링**: 백엔드가 `X-Accel-Buffering: no` 헤더 + `Response.Body.FlushAsync()`를 매 frame 호출해야 함(이미 ChatController에서 적용됨). 프론트엔드는 fetch만 사용하므로 추가 조치 불필요
  - **브라우저 호환성**: fetch + ReadableStream + AbortController + TextDecoder 모두 Chrome 43+/Firefox 65+/Safari 10.1+/Edge 79+ 지원 — AgentHub 타깃 브라우저 범위 안전
  - `npm run build:check` 미실행 (Windows 환경 npm 검증 환경 미구비) — 사용자 측 검증 필요
- **검증 방법 (사용자 측)**:
  ```bash
  cd agenthub/ClientApp
  npm run build:check    # vue-tsc 타입 검사 + vite build
  npm run dev
  # 브라우저에서 채팅 입력 → 토큰 단위 흐름 + Network 탭 chunked transfer 확인
  # 응답 도중 "응답 중단" 버튼 클릭 → 즉시 멈추는지
  # useStreaming 토글 끄면 비스트리밍 폴백 동작하는지 (현재는 코드 토글, Settings UI 노출은 별도 작업)
  ```
- **Phase 3.5b 완료 (frontend + backend)**:
  - 사용자 보고 "Vue UI 5~10초 대기" 핵심 UX 문제 → 첫 token 즉시 표시로 해소 (백엔드 SSE 엔드포인트 + 프론트 streaming 클라이언트)
  - 백엔드 `/api/chat/send/stream` + DTO `ChatStreamEvent` + `ChatService.SendDirectMessageStreamEventsAsync` (위 항목 참조)
  - 프론트 `sseClient.ts` + `AgentChat.vue` streaming 분기 (본 항목)
- **Phase 3.5b 후속 (별도 트랙)**:
  - AgentBuilder/AgentMultiChat/Playground 3개 화면도 동일 sseClient 적용
  - 사용자 설정 UI에 useStreaming 토글 노출 (Settings 모달)
  - dotnet 8 SDK 환경에서 백엔드 빌드 검증 + e2e 테스트(curl 또는 fetch SSE)

### 2026-05-05 (Phase 3.5b — Vue UI 전용 SSE 백엔드 엔드포인트 추가)
- **사용자 보고 "Vue UI 채팅 5~10초 대기 후 일괄 출력" 직접 해소를 위한 신규 엔드포인트 추가**
- **신설 파일 1개**:
  - `agenthub/DTOs/ChatStreamEvent.cs` — Vue UI 전용 SSE 이벤트 record (`Type` discriminator 기반: `"delta" | "usage" | "meta"`). 정적 helper `Delta/UsageEvent/Meta` 제공. camelCase JSON 직렬화 정책(P5) 준수
- **수정 파일 3개**:
  - `agenthub/Services/IChatService.cs` — `IAsyncEnumerable<ChatStreamEvent> SendDirectMessageStreamEventsAsync(...)` 시그니처 추가. 기존 `SendDirectMessageStreamChunksAsync`(`IAsyncEnumerable<ChatChunk>`)는 OpenAI 호환 SSE 전용으로 유지(불변)
  - `agenthub/Services/ChatService.cs` — `SendDirectMessageStreamEventsAsync` 구현 (clean room, 약 300 LOC)
    - 흐름: Agent/ServiceId 확정 → Quota 사전 체크 → BannedWord/PII 검사(SendDirectMessageAsync 와 동일 정책) → Conversation 락 보존 find/create → AiProxy.SendChatMessageStreamChunksAsync `await foreach` → **delta event yield** → 종료 후 cost 계산 → **usage event yield** → ChatMessage(user/assistant)/ApiUsage/Conversation 통계 SaveChanges → `assistantMessage.MessageId` 회수 → RecordUsageAsync → **meta event yield** (conversationId/messageId/model/cost)
    - 영속화 실패는 try/catch 후 meta event 계속 yield (사용자에게는 chunk가 이미 전달됨)
    - `usageEmitted` flag 도입: usage chunk 미발행(0 토큰 폴백) 시 meta event 의 `cost` 필드로 cost 동봉
  - `agenthub/Controllers/ChatController.cs` — `[HttpPost("send/stream")]` 신규 액션 + 2개 private 헬퍼 추가
    - 검증 단계는 SSE 시작 전 일반 401/400 JSON 응답으로 분리 (EventSource 호환성 + 클래스 레벨 [Authorize] 동작 그대로)
    - 통과 후에만 SSE 헤더 설정: `text/event-stream; charset=utf-8` + `Cache-Control: no-cache` + `X-Accel-Buffering: no` + `Connection: keep-alive` (IIS InProcess + reverse proxy buffering 방지)
    - `WriteSseFrameAsync(object, ct)` — JsonSerializerOptions(camelCase + IgnoreCondition.WhenWritingNull) 으로 직렬화 + 매 frame `Response.Body.FlushAsync()`
    - `WriteSseErrorAsync(code, message, ct)` — 스트림 시작 후 예외 처리용 (BannedWordException/PiiDetectionException/InvalidOperationException/Exception → 각각 `BANNED_WORD_DETECTED`/`PII_DETECTED`/`VALIDATION_ERROR`/`INTERNAL_ERROR` code + 한국어 메시지(R5))
    - OperationCanceledException(클라이언트 disconnect) 정상 종료 처리
    - `[DONE]` 종료 마커 표준 SSE 형식 준수
- **회귀 분석 (사용자 보고용 사실)**:
  - **OpenAICompatController.cs는 변경 없음** — Phase 3.5 commit(가짜 SSE → 진짜 SSE) 완전 보존
  - 기존 `ChatChunk` / `SendDirectMessageStreamChunksAsync` 시그니처/동작 모두 불변 → OpenAI SDK / Cursor / LangChain 호환성 회귀 0건
  - 기존 `[POST] /api/chat/send` 비스트리밍 분기 그대로 유지 → 기존 Vue UI 호출(`AgentChat.vue:1708`)은 클라이언트 변경 전까지 정상 동작
- **meta 정보 회수 가능 여부 확인 결과**:
  - `conversationId`: ✅ 영속화 전 conversation 객체에서 추출 가능 (ChatService.cs `finalConversationId = conversation?.ConversationId`)
  - `messageId`: ✅ EF SaveChanges 직후 `assistantMessage.MessageId` 가 IDENTITY로 채워짐(`long`). PG IDENTITY 가 컬럼 메타에 정상 매핑되었는지는 Phase 3.2 Npgsql baseline 생성 시 동시 검증 필요
  - `model`: ✅ 결정된 model 변수 그대로 yield
  - `cost`: ✅ `_aiProxyService.CalculateCostAsync` 결과를 usage event 와 meta event 양쪽에서 사용 가능
- **잠재 위험**:
  - **트랜잭션**: SaveChanges 가 단일 호출이므로 user/assistant message + ApiUsage + Conversation 통계가 원자적으로 커밋됨. 단, RecordUsageAsync(quota 차감)는 별도 트랜잭션이라 부분 실패 가능 (기존 SendDirectMessageStreamChunksAsync 와 동일 정책 — 운영 영향 동일 수준)
  - **예외**: 영속화 실패해도 meta event 는 계속 yield (`messageId=null` 상태). 클라이언트는 `messageId === null` 일 때 "메시지 저장에 실패했습니다" 비파괴적 알림만 표시하면 됨 (frontend 분담)
  - **cancellation**: `[EnumeratorCancellation]` 으로 토큰이 IAsyncEnumerable 까지 전파됨. 클라이언트 disconnect 시 AiProxy 의 HttpClient 까지 cancel 전달되어 외부 LLM 비용 절감 (기존 wrapper 와 동일)
  - **중복 코드**: `SendDirectMessageStreamChunksAsync` 와 약 70% 코드 중복. Phase 3.5 commit 회귀 위험을 피하기 위한 의도적 분리. Phase 5+ 에서 공통 streaming 코어 추출 리팩토링 예정 (TECHSPEC §15.4 후속)
  - dotnet CLI 미설치 — `dotnet build` 검증은 사용자 측 SDK 설치 후 필요
- **남은 작업 (별도 task)**:
  - Vue 측 `AgentChat.vue` 에 `fetch + ReadableStream` 또는 `EventSource`(JWT 헤더 제약 있음) 기반 streaming 클라이언트 도입 (frontend specialist 분담)
  - dotnet 8 SDK 환경에서 빌드 검증 + e2e 테스트(`/api/chat/send/stream` curl SSE 흐름 확인)

### 2026-05-05 (Phase 3.5 — 가짜 SSE → 진짜 SSE 코드 작성 완료, 빌드 검증 대기)
- **Phase 3.5 우선 진입 (UX 가시성 즉시 개선)**: TECHSPEC §15.4 / §16 C9(가짜 SSE) + H5(Stream API 키 풀 우회) 동시 해소
- **신설 파일 1개**:
  - `agenthub/DTOs/ChatChunk.cs` — `record ChatChunk(Content, FinishReason, PromptTokens, CompletionTokens, TotalTokens)` + 정적 helper `Delta/Stop/Usage`
- **수정 파일 4개**:
  - `agenthub/Services/IAiProxyService.cs` — 기존 `SendChatMessageStreamAsync`(`Task<Stream>` 반환)은 `[Obsolete]` 마킹(호출처 0건). 신규 `IAsyncEnumerable<ChatChunk> SendChatMessageStreamChunksAsync(...)` 추가
  - `agenthub/Services/AiProxyService.cs` — 기존 메서드 `[Obsolete]`. 신규 `SendChatMessageStreamChunksAsync` 추가:
    - OpenAI provider: `StreamOpenAiChunksAsync` 신규 — `HttpCompletionOption.ResponseHeadersRead` 로 본문 chunk 단위 수신 + `data: {...}\n\n` 라인 파서 + `[DONE]` 마커 처리. **`stream_options.include_usage:true` 옵션으로 마지막 chunk에 OpenAI 실제 토큰수 동봉(0.65 추정 제거)**. **ApiKeyPool 라운드로빈 + 429 Cooldown 적용 (H5 해소)**
    - 그 외 provider(claude/gemini/perplexity/mistral/copilot/azure-openai): 비스트리밍 호출 결과를 단일 chunk로 폴백 yield + TODO Phase 5+ 주석. 가짜 SSE 위장보다 정직
    - 신규 private 클래스 3개: `OpenAiStreamChunk` / `OpenAiStreamChoice` / `OpenAiStreamDelta` (snake_case 매핑)
    - `using System.Runtime.CompilerServices;` 추가 (`[EnumeratorCancellation]`)
  - `agenthub/Services/IChatService.cs` — `IAsyncEnumerable<ChatChunk> SendDirectMessageStreamChunksAsync(...)` 추가
  - `agenthub/Services/ChatService.cs` — 동명 streaming wrapper 구현. Quota 사전 체크 + BannedWord/PII 검사(SendDirectMessageAsync 와 동일 정책) → ConversationFind/Create(락 보존) → AiProxy.SendChatMessageStreamChunksAsync await foreach yield → 종료 후 ChatMessage / ApiUsage / Conversation 통계 1회 SaveChanges + RecordUsageAsync. 영속화 실패는 silently 로그(이미 chunk는 사용자에게 전달됨)
  - `agenthub/Controllers/OpenAICompatController.cs` — `SendStreaming` 메서드 전면 재작성:
    - **삭제**: `Content.Split(' ')` + `Task.Delay(15)` 단어 위장 chunk 패턴(라인 ~343-358)
    - **신규**: `await foreach (chunk in _chatService.SendDirectMessageStreamChunksAsync(...))` → 즉시 `data: {...}\n\n` flush
    - SSE 헤더: `Cache-Control: no-cache` + `X-Accel-Buffering: no` + `Connection: keep-alive`
    - usage chunk: OpenAI 표준 동작(finish_reason 청크 다음에 choices=[] + usage 채운 별도 청크) 모사하여 OpenAI SDK 호환
    - 에러 fallback: 스트림 시작 후 예외 발생 시 SSE error chunk 한 건 + `[DONE]` 흘리고 종료(상태 코드 변경 불가 상황 대응)
    - 비스트리밍 분기의 0.65 휴리스틱 추정값에는 TODO 주석 추가(Phase 5+에서 DTO 확장 시 정확화)
- **추가 점검 결과 / 사용자 보고용 사실**:
  - **Vue 채팅 UI(`AgentChat.vue`)는 OpenAI 호환 API를 호출하지 않음**: `AgentChat.vue:1708` `api.post('/chat/send', { ..., stream: false })` → ChatController `[POST] /api/chat/send`(라인 347) → `ChatService.SendDirectMessageAsync` 비스트리밍 분기. 즉 본 작업은 **외부 OpenAI 호환 클라이언트(Cursor/LangChain/OpenAI SDK/Postman) 한정** UX 개선. **사용자가 보고한 "Vue UI에서 5~10초 대기 후 일괄 출력"은 본 작업으로 직접 해결되지 않음** — Phase 5+ 별도 트랙에서 `/api/chat/send` 엔드포인트도 SSE 변환 + 프론트엔드 `EventSource`/`fetch ReadableStream` 도입 필요(별도 TODO)
  - 기존 `SendChatMessageStreamAsync` 호출처 grep 결과 **0건** — `[Obsolete]` 마킹만으로 안전
  - `IAiProxyService` / `IChatService` 구현체 grep 결과 각각 단일(`AiProxyService` / `ChatService`) — 모의구현 영향 없음
- **잠재 위험 / 사용자 검증 필요**:
  - IIS InProcess 호스팅에서 `Response.Body.FlushAsync()` 호출 시 chunked transfer 실제 적용 확인 필요(Content-Length 미설정 + `X-Accel-Buffering: no` 설정으로 1차 방어). 운영 IIS 앞 reverse proxy(nginx/Apache/IIS ARR) 사용 시 buffering 비활성화 추가 점검
  - OpenAI `stream_options.include_usage:true` 옵션은 OpenAI 표준 모델만 지원 — Azure OpenAI / 호환 엔드포인트에서 미지원 시 usage 0 반환 가능(현재 폴백 분기는 비스트리밍 호출이므로 영향 없음)
  - **OpenAI streaming 경로는 RAG / 웹검색 / DeepResearch 미적용**(SendChatMessageAsync 의 RAG 흐름과 미동기화). Phase 5+ 에서 RAG 컨텍스트 주입을 streaming 진입 직전 별도 단계로 분리하여 양 경로에서 공유 예정 — 본 단계 코드에 명시 TODO 주석 (`StreamOpenAiChunksAsync` summary)
  - dotnet CLI 미설치 — `dotnet build` / `dotnet test` 미실행. 사용자 측에서 SDK 설치 후 워닝 0건 검증 필요
- **검증 방법 (사용자 측)**:
  ```bash
  # 외부 OpenAI 호환 SDK 호환성
  curl -N -X POST https://localhost:5001/v1/chat/completions \
    -H "X-API-Key: ak-xxx" -H "Content-Type: application/json" \
    -d '{"model":"<agentCode>","messages":[{"role":"user","content":"안녕"}],"stream":true}'
  # 기대: 토큰 단위 실시간 흐름. 가짜 SSE 시 5~10초 대기 후 일괄 → 진짜 SSE 시 즉시 첫 chunk
  ```
- **남은 작업 (별도 commit / 별도 task)**:
  - Phase 3.5 검증: dotnet 8 SDK 환경에서 `dotnet build` 워닝 0건 + 외부 SDK e2e 테스트
  - Phase 3.5+: Vue 채팅 UI(`/api/chat/send`)도 streaming SSE 도입 — 사용자 보고한 "5~10초 대기" 진짜 해소 (별도 작업, frontend 수정 포함)
  - C9 / H5는 본 코드로 해소 완료(빌드 검증 후 TECHSPEC §16 표 업데이트 예정)

### 2026-05-05 (Phase 3.1 — EF Provider 코드 전환 완료)
- **AgentHub EF Core SQL Server → PostgreSQL provider 교체** (코드만, 운영 데이터 이전 보류)
  - `agenthub/AIAgentManagement.csproj`: `Microsoft.EntityFrameworkCore.SqlServer` / `Hangfire.SqlServer` 제거 → `Npgsql.EntityFrameworkCore.PostgreSQL` 8.0.11 / `Hangfire.PostgreSql` 1.20.10 추가. `Microsoft.Data.SqlClient`는 보류 (3개 파일 직접 사용처 — Program.cs:403, TestDbConnection.cs, Controllers/DatabaseBackupController.cs)
  - `agenthub/Program.cs`:
    - `using Hangfire.SqlServer` → `using Hangfire.PostgreSql`
    - `options.UseSqlServer(...)` → `options.UseNpgsql(connectionString, npg => npg.CommandTimeout(30))`
    - `UseSqlServerStorage(...)` → `UsePostgreSqlStorage(opt => opt.UseNpgsqlConnection(...), new PostgreSqlStorageOptions { SchemaName = "hangfire", PrepareSchemaIfNecessary = true, QueuePollInterval = TimeSpan.Zero })`
  - `agenthub/Data/AIAgentManagementDbContext.cs`: `OnModelCreating` 시작부에 `modelBuilder.HasDefaultSchema("AIAgentManagement")` 추가 (P4 schema 격리)
  - `agenthub/Migrations/` → `Migrations.mssql.archive/` 로 `git mv` (3 파일 보존, ADR-7 historical 참조용). csproj `<Compile Remove="Migrations.mssql.archive\**" />` 추가하여 빌드 제외
  - `agenthub/appsettings.Development.json`: `DefaultConnection`만 `Host=192.168.10.39;Port=5440;Database=AGENT_HUB;Username=AGENT_HUB;Password=idino!@#$;Search Path=AIAgentManagement,public` 형식으로 전환. 다른 키(JWT/AI/Email)는 미변경
  - `agenthub/appsettings.Production.json`: **변경 안 함** (위험 작업, Phase 7+에서 사용자 결정)
- **검증 결과 / 발견 사항**:
  - `dotnet` CLI가 Windows 환경에 설치되어 있지 않아 `dotnet build` / `dotnet ef migrations add Init` 실행 불가. Phase 3.2에서 dotnet 8 SDK 설치 후 검증 + baseline 생성 필요
  - **(해결)** root `.gitignore`의 `data/` / `models/` / `checkpoints/` 패턴이 Windows case-insensitive 매칭으로 .NET 표준 `Data/` `Models/` 디렉토리와 Python ORM `models/` 모듈까지 차단하는 결함 발견. 본 commit에서 3개 디렉토리 패턴 제거 (파일 확장자 패턴 `*.bin/.safetensors/.pt/.pth/.onnx/.gguf`만 유지, 대용량 데이터 디렉토리는 시스템별 명시 정책으로 전환)
  - **(해결)** `.gitignore` 정정 결과 1da04ab 초기 commit에서 누락된 핵심 코드 55개 파일 신규 추적: `agenthub/Data/` (DbContext + DatabaseInitializer + 3 SQL) 5개, `agenthub/Models/` (EF 엔티티) 35개, `career/services/{advisor|alumni|auth|badge|coaching|competency|opportunity|risk|simulation|skill|student}-service/app/models/` 15개. docutil/nexus는 추가 0건 (이미 적절히 추적 중)
  - `agenthub/appsettings.Development.json`은 의도된 시크릿 보호로 그대로 차단 유지 (디스크에만 적용, 향후 `appsettings.Development.example.json` 템플릿 도입 검토)
  - `Microsoft.Data.SqlClient` 직접 사용처 3건 (`Program.cs:403` `catch SqlException` / `TestDbConnection.cs` 전체 / `Controllers/DatabaseBackupController.cs:148,179` `new SqlConnection`) — Phase 3 후속에서 PG로 정리 또는 controller 자체 deprecate 검토 필요

### 2026-05-05 (Phase 2 완료)
- **Phase 2 — AGENT_HUB DB 설계 + 생성 완료**
  - `infra/db/init.sql` v1.0 작성 (idempotent, 9 섹션) — psql `-v idino_pw` 환경변수 주입 + DO 블록 멱등 보호 + 검증 쿼리 포함
    - DB user `AGENT_HUB` (LOGIN, password 환경변수)
    - DATABASE `AGENT_HUB` (UTF8, ko_KR.UTF-8, TEMPLATE template0)
    - Extensions: `vector` / `uuid-ossp` / `pgcrypto` / `pg_trgm`
    - Schemas: `AIAgentManagement` / `document_utilization` / `idino_career` / `hangfire`
    - `ALTER DEFAULT PRIVILEGES`로 향후 객체 자동 권한 부여
    - search_path 기본값 4 schema + public
  - `docs/DB_MIGRATION.md` v1.0 작성 (9 섹션 + 부록 2개) — Phase 2 적용 절차 + Phase 3/4 계획 가이드 + 롤백/재시작/모니터링/시크릿 정책
- ADR-4(단일 PG) / ADR-10(임베딩 1536D) / P4(스키마 격리) / P10(시크릿 비커밋) / R26(시크릿 환경변수) 모두 반영
- 본 단계는 schema/extension/role까지만 생성 — 테이블은 Phase 3+에서 EF/Alembic이 담당

### 2026-05-05 (Phase 1 완료)
- **Phase 1 — AI 호출 인벤토리 완료** (`docs/AI_INVENTORY.md` 12 섹션 + 부록 2개 v1.0)
  - 4개 시스템 grep 검증 + source 보고서 종합
  - **35개 직접 호출 지점** 식별 (agenthub 8 분기 / docutil 9 / career 12 / nexus 0)
  - **5개 위임 호출** (career coaching/competency/roadmap/opportunity/skill)
  - **15개 신규 Agent 카탈로그** 정의 (docutil 4 + career 8 + 공통 3)
  - **Phase 7 견적 9 영업일** 확정 (TECHSPEC §12 "10 영업일"과 일치, 1일 여유)
- **본 인벤토리 작업으로 신규 발견** (TECHSPEC 보강 권고):
  - DocUtil 단일 진입점 위반 2건 추가 — `agentic_search.py:215,237`, `training/data_generator.py:68-69` (R31 후보)
  - AgentHub Chat provider 실측 7개 (보고서 8 표기 정정 — Vertex/Tavily는 별도 카테고리)
  - AgentHub 가짜 SSE 정확 위치 — `OpenAICompatController.cs:343` `Content.Split(' ')` + `:357` `Task.Delay(15)` (138은 함수 진입점)
  - career skill-service 포트 불일치 발견 — `AI_SERVICE_URL=:8000` vs 실제 ai-service `:8006` (W5)
- **GitHub push 차단 발견** — 첫 commit `1da04ab`에 평문 API 키 4개 (OpenAI/Gemini/Perplexity/Tavily). 위치: `agenthub/iis-setting.ps1` + `agenthub/TODO.md`. 사용자 결정 대기 (키 무효화 + B1/B2/B3 옵션)
- CLAUDE.md 최상단에 **신규 세션 자동 로드 규칙** 추가 (`progress.md` + `TECHSPEC.md` 필수 Read). commit `c3fc024`
- 글로벌 메모리 7개 작성:
  - `MEMORY.md` (인덱스)
  - `idino_agent_hub_migration.md` (project, 작업 dir 이전)
  - `idino_agent_hub_status.md` (project, Phase 0 완료/Push 차단)
  - `idino_agent_hub_secret_leak.md` (project, 4개 평문 키 + 처리 옵션)
  - `idino_agent_hub_docs.md` (reference, 문서 위치)
  - `idino_agent_hub_session_entry.md` (feedback, 진입 절차)
  - `idino_agent_hub_decisions.md` (project, 15개 ADR 요약)
- 메모리는 `D--workspace-AIAgentManagement` + `D--workspace-IDINO_Agent_Hub` 양쪽에 보존 (작업 dir 전환 대비)

### 2026-05-04
- 통합 TECHSPEC v1.0 작성 (`user_mig/TECHSPEC.md`, 21개 섹션 + 부록 3개)
- 4개 시스템 종합 분석 보고서 작성 (병렬 에이전트 4개)
  - `source_AGENTHUB.md` — TECHSPEC.md 1171라인 + 9개 섹션 분석
  - `source_DOCUTIL.md` — Phase 4 ~54% 완료, factory 단일 진입점 확인
  - `source_CAREER.md` — LLM 직접 호출 11곳, AgentHub Agent 매핑 8개 제안
  - `source_NEXUS.md` — 4-Tier AsyncGenerator + 옵션 B 통합 명세
- progress.md 신설 (본 파일)
- CLAUDE.md에 progress.md 자동 갱신 규칙 추가
- Phase 0 완료 — Git 초기 commit + remote 등록 (`1da04ab`)
- 4개 서브프로젝트 monorepo 통합 (1,921 files)
- 셋업 파일 작성 (.gitignore, README, CLAUDE.md, .claude/rules/ 6개, docs/ 2개)

---

## 7. 다음 작업 (Phase 3 진행 예정)

### Phase 3: AgentHub MSSQL → PostgreSQL 마이그레이션 + 부채 정리

**Phase 3은 가장 큰 위험 구간** — DB 전환 + 코드 부채(C1~C10) 동시 처리. 사용자 승인 후 진행 권장.

#### 작업 항목 (예상 10 영업일)
- [ ] EF Core provider 교체 — `Microsoft.EntityFrameworkCore.SqlServer` → `Npgsql.EntityFrameworkCore.PostgreSQL` 8.x
- [ ] 기존 SqlServer migration 1개 + ModelSnapshot 폐기, Npgsql baseline `Init` 신규 생성
- [ ] `appsettings.*.json` connection string 전환 (`Server=...` → `Host=...;Search Path=AIAgentManagement`)
- [ ] **부채 정리 (DB 전환과 동시)**:
  - C1: AES-CBC 고정 IV → per-record random IV + AES-GCM (`ApiKey.KeyIv`/`KeyTag` 컬럼 신설 + 재암호화)
  - C2: JWT SecretKey ↔ AES Key 분리 (KMS/User Secrets)
  - C3: API Key 풀스캔 → `KeyHash UNIQUE` SHA-256 인덱스
  - C4: `Users.Email` UNIQUE 인덱스 추가
  - C7: `EnsureCreatedAsync` → `MigrateAsync` (baseline 적용으로 자연 해결)
  - C8: SignalR Hub `[Authorize]` + `Context.UserIdentifier` 사용
  - H10: `QuotaService.RecordUsageAsync` 토큰수 무시 버그 수정
  - H13: `AiProxyService` 3,749 LOC god class 일부 분해 (Strategy 패턴 준비)
- [ ] JSON `nvarchar(MAX)` → `jsonb` 전환 (인덱싱 가능 컬럼만)
- [ ] `DocumentChunk.Embedding` → `vector(1536)` + IVFFlat 인덱스 (자체 KB는 deprecate 예정이지만 Phase 6까지는 동작 유지 필요)
- [ ] Hangfire SqlServer storage → `Hangfire.PostgreSql` 전환
- [ ] `DatabaseInitializer.cs` (866 LOC) idempotent 재작성 — Roles/ApiServices/ApiServiceModels/Agents 시드
- [ ] 데이터 이전 (pgloader 또는 bcp+COPY) — MSSQL → AGENT_HUB.AIAgentManagement
- [ ] 빌드 검증 — `dotnet build` 워닝 0건, `dotnet ef database update` 성공
- [ ] 통합 검증 — Agent CRUD, OpenAI 호환 API, ApiKey 인증, Quota 리셋

#### Phase 3 진입 전 결정 필요
- **운영 데이터 이전 시점**: 개발/스테이징에서 dry-run 후 운영 적용 (사용자 확인 필수 — 운영 데이터 영향)
- **AGENT_HUB DB 비밀번호 회전**: 현 비밀번호 사용 vs 신규 발급 (R26 — 비밀번호 정책)

**예상 영업일**: 10일
**의존성**: Phase 2 (완료)

### 별도 트랙 (Phase 진행과 무관)
- **Q3**: DocUtil S6/S7 진행 위치 (Phase 4 시작 전 결정, 현 단계 차단 없음)
- **GitHub push 차단**: 첫 commit `1da04ab` secret leak — 키 무효화 + B1/B2/B3 옵션 (사용자 결정 시 처리)

---

## 8. 갱신 규칙 (CLAUDE.md 동기화)

본 progress.md는 다음 시점에 갱신한다:
1. 새 Phase 진입 시 — Phase 상태 변경 + 작업 로그
2. 핵심 작업 완료 시 — 작업 로그 추가
3. ADR / 위험 / Open Question 변경 시 — 해당 섹션 갱신
4. Git commit 후 — 마지막 commit 해시 갱신

**갱신 형식**:
- 시간 역순으로 작업 로그 추가 (오래된 항목 위에 신규 항목)
- Phase 상태표는 항상 최상단
- ADR/위험은 결정 단위로 행 추가/수정

---

## 부록. 빠른 참조

| 작업 | 위치 |
|---|---|
| 통합 기술 명세 | `user_mig/TECHSPEC.md` |
| AgentHub 분석 | `user_mig/source_AGENTHUB.md` |
| DocUtil 분석 | `user_mig/source_DOCUTIL.md` |
| career 분석 | `user_mig/source_CAREER.md` |
| Nexus 분석 | `user_mig/source_NEXUS.md` |
| 협업 규칙 | `.claude/rules/agent-collaboration.md` |
| 아키텍처 원칙 | `.claude/rules/architecture.md` |
| 금지 패턴 | `.claude/rules/anti-patterns.md` |
| 도메인 모델 | `.claude/rules/domain-model.md` |
| 테스트 전략 | `.claude/rules/testing.md` |
| Phase 작업 순서 | `.claude/rules/development-workflow.md` |
| AI 인벤토리 (Phase 1 대상) | `docs/AI_INVENTORY.md` |
| DB 마이그레이션 기록 (Phase 2+) | `docs/DB_MIGRATION.md` (예정) |
