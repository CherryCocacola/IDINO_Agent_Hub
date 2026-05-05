# AGENT_HUB DB 마이그레이션 가이드

> **Phase 2 산출물** — 단일 PostgreSQL 인스턴스에 4개 schema(`AIAgentManagement` / `document_utilization` / `idino_career` / `hangfire`)를 셋업하고 Phase 3 이후의 데이터 이전 절차를 명시한다.
>
> **작성일**: 2026-05-05
> **연관 파일**: `infra/db/init.sql`, `user_mig/TECHSPEC.md` §4 §5 §7
> **연관 ADR**: ADR-4(단일 PG), ADR-10(임베딩 1536D), ADR-11(Nexus DB 별도)
> **연관 위험**: R5 / R11 / R12 / R13 / R17 / R18 / R26 / R29

---

## 0. 개요

### 0.1 전체 그림

```
PostgreSQL 17  (192.168.10.39:5440)
 └── DATABASE: AGENT_HUB           (Phase 2: init.sql)
      ├── extensions: vector / uuid-ossp / pgcrypto / pg_trgm
      ├── schema: AIAgentManagement     (Phase 3: EF Core baseline)
      ├── schema: document_utilization  (Phase 4: Alembic head 재정렬)
      ├── schema: idino_career          (Phase 4: SQL files 적용)
      └── schema: hangfire              (Hangfire 자동 생성)

별도 인스턴스(통합 대상 아님 — ADR-11):
PostgreSQL  (Nexus 측)
 └── DATABASE: nexus  (tb_knowledge / tb_memories / tb_symbols)
```

### 0.2 Phase별 책임

| Phase | 작업 | 산출물 / 대상 |
|---|---|---|
| **2** | DB 셋업 (본 가이드) | `infra/db/init.sql`, AGENT_HUB role/DB/4 schema/4 extensions |
| **3** | AgentHub MSSQL → PG 전환 | EF baseline 마이그레이션, MSSQL 데이터 이전 |
| **4** | DocUtil/career schema 이전 | Alembic head 재정렬, SQL files 재실행, pgvector 활성화 |
| **5+** | Nexus provider, 운영자 흡수 등 | 본 가이드 이후 단계 (별도 문서) |

---

## 1. 사전 준비

### 1.1 운영 PostgreSQL 인스턴스 점검

```bash
# 슈퍼유저 접근 확인 (postgres 계정 / OS 단의 pg_hba.conf 신뢰 경로)
psql -h 192.168.10.39 -p 5440 -U postgres -c "SELECT version();"

# 기존 DB / role 확인 (충돌 방지)
psql -h 192.168.10.39 -p 5440 -U postgres -c "\l" | grep -i agent_hub
psql -h 192.168.10.39 -p 5440 -U postgres -c "\du" | grep -i agent_hub

# 인스턴스의 한국어 로케일 가용성 확인
psql -h 192.168.10.39 -p 5440 -U postgres -c "SELECT * FROM pg_collation WHERE collname LIKE '%ko%';"
```

기대값:
- PostgreSQL 17.x.
- `AGENT_HUB` role 미존재 또는 본 가이드의 비밀번호 정책과 일치.
- `ko_KR.UTF-8` 로케일 사용 가능 (Linux의 경우 `locale -a | grep ko`).

### 1.2 비밀번호 / 시크릿 처리

- 본 가이드에서 사용하는 비밀번호는 **반드시 환경변수 또는 Vault에서 주입**한다.
- 운영용 비밀번호는 TECHSPEC §13.2의 Vault 정책을 따른다 (R26).
- **Git에 커밋된 yaml/sql/env에 평문 비밀번호 저장 금지** (P10).
- 본 가이드의 예시는 `idino!@#$` 같은 더미가 아니라, 실행 시점에 `-v idino_pw=` 변수로 주입한다.

```bash
# 비밀번호 주입 예 (Linux/macOS)
export AGENT_HUB_PW="실제_비밀번호"
psql -h 192.168.10.39 -p 5440 -U postgres \
     -v idino_pw="'${AGENT_HUB_PW}'" \
     -f infra/db/init.sql
```

```powershell
# Windows PowerShell
$env:AGENT_HUB_PW = "실제_비밀번호"
psql -h 192.168.10.39 -p 5440 -U postgres `
     -v idino_pw="'$env:AGENT_HUB_PW'" `
     -f infra/db/init.sql
```

### 1.3 백업 사전 확보 (운영 DB일 경우)

기존 운영 PostgreSQL에 `AGENT_HUB` 또는 동명 객체가 이미 있는 경우, 본 스크립트는 **idempotent**하지만 안전을 위해 사전 백업 필수:

```bash
pg_dumpall -h 192.168.10.39 -p 5440 -U postgres -f backup_$(date +%Y%m%d_%H%M).sql
```

---

## 2. Phase 2 — `infra/db/init.sql` 적용

### 2.1 적용 명령

```bash
# 슈퍼유저로 1회 실행 (idempotent — 재실행해도 안전)
psql -h 192.168.10.39 -p 5440 -U postgres \
     -v idino_pw="'${AGENT_HUB_PW}'" \
     -f infra/db/init.sql
```

### 2.2 적용 후 검증

```sql
-- AGENT_HUB DB로 접속 후 확인
\c AGENT_HUB

-- Extensions 4종
SELECT extname, extversion FROM pg_extension
WHERE extname IN ('vector','uuid-ossp','pgcrypto','pg_trgm')
ORDER BY extname;
-- 기대: 4행

-- Schema 4종
SELECT schema_name, schema_owner FROM information_schema.schemata
WHERE schema_name IN ('AIAgentManagement','document_utilization','idino_career','hangfire')
ORDER BY schema_name;
-- 기대: 4행 (모두 owner = AGENT_HUB)

-- Role
SELECT rolname, rolcanlogin, rolsuper FROM pg_roles WHERE rolname = 'AGENT_HUB';
-- 기대: rolcanlogin=t, rolsuper=f

-- pgvector 동작 확인
CREATE TABLE IF NOT EXISTS public._vec_check (id int, v vector(3));
INSERT INTO public._vec_check VALUES (1, '[1,2,3]'), (2, '[2,3,4]');
SELECT id, v <=> '[1,2,3]' AS distance FROM public._vec_check ORDER BY distance;
DROP TABLE public._vec_check;
-- 기대: id=1 distance=0, id=2 distance≈0.025
```

### 2.3 롤백 (Phase 2만 되돌리고 싶을 때)

```sql
-- 운영자만 실행. 데이터가 들어 있으면 절대 사용 금지.
\c postgres
DROP DATABASE IF EXISTS "AGENT_HUB";
DROP ROLE IF EXISTS "AGENT_HUB";
```

위 명령은 Phase 3 이후 데이터가 적재되면 **모든 데이터 손실**을 일으킨다. Phase 3+ 진입 후에는 §5의 부분 롤백 절차를 사용한다.

---

## 3. Phase 3 — AgentHub MSSQL → PostgreSQL

> 본 절은 Phase 3 시작 시 본 문서를 함께 갱신할 가이드다. 현재는 **계획**.

### 3.1 EF Core baseline 마이그레이션 (Npgsql)

```bash
cd agenthub

# Provider 교체: SqlServer → Npgsql (csproj 수정)
# 패키지: Npgsql.EntityFrameworkCore.PostgreSQL 8.x
dotnet remove package Microsoft.EntityFrameworkCore.SqlServer
dotnet add    package Npgsql.EntityFrameworkCore.PostgreSQL --version 8.*

# 기존 SqlServer migration 폴더 백업 후 폐기
mv Migrations Migrations.mssql.archive

# Npgsql용 baseline 신규 작성
dotnet ef migrations add Init \
    --context AIAgentManagementDbContext \
    --output-dir Migrations
dotnet ef database update --context AIAgentManagementDbContext
```

### 3.2 데이터 이전 (MSSQL → PostgreSQL)

권장 도구: **pgloader** (자동 타입 변환) 또는 **bcp + COPY** (수동).

```bash
# pgloader 예 (별도 머신에 설치)
pgloader \
    "mssql://user:pwd@MSSQL_HOST/AIAgentManagement" \
    "postgresql://AGENT_HUB:${AGENT_HUB_PW}@192.168.10.39:5440/AGENT_HUB?sslmode=disable&search_path=AIAgentManagement"
```

이전 후 변환 작업:
1. `nvarchar(MAX)` JSON 컬럼 → `jsonb` 변환 + GIN 인덱스
   - `Agent.AllowedEmbedDomains`, `WorkflowNode.Connections`, `Presentation.Slides`, `Agent.RoutingPolicyJson` (Phase 5에서 추가)
2. `DocumentChunk.Embedding` (`nvarchar(MAX)` JSON `float[1536]`) → `vector(1536)` 변환 + IVFFlat 인덱스
3. `IDENTITY` → `GENERATED BY DEFAULT AS IDENTITY` (EF가 baseline 시 자동 처리)
4. `bigint identity` 시퀀스 last_value 동기화 (`SELECT setval('seq_name', max(id))`)
5. `GETDATE()` 같은 raw SQL 함수 호출이 코드/시드에 잔존하면 PG의 `now() AT TIME ZONE 'UTC'`로 교체

### 3.3 부채 정리 (Phase 3 동시 처리 — TECHSPEC §15)

| ID | 항목 | 위치 | 처리 방식 |
|---|---|---|---|
| C1 | AES-CBC 고정 IV → per-record random IV + AES-GCM | `ApiKeyService.cs:318`, `ApiKeyAuthService.cs:89` | baseline에 `KeyIv`/`KeyTag` 컬럼 추가 + 재암호화 마이그레이션 |
| C2 | JWT SecretKey ↔ AES Key 재사용 | `ApiKeyService.cs:24` | KMS/User Secrets로 분리 |
| C3 | API Key 풀스캔 → `KeyHash UNIQUE` SHA-256 | `ApiKeyAuthService.cs:34-66` | `KeyHash` 컬럼 + UNIQUE 인덱스 |
| C4 | `Users.Email` UNIQUE 미설정 | DB 제약 | baseline에 추가 |
| C7 | `EnsureCreatedAsync` → `MigrateAsync` | DI 부트스트랩 | baseline 적용으로 자연 해결 |
| C8 | SignalR Hub `[Authorize]` 부재 | `Hubs/ChatHub.cs`, `NotificationHub.cs` | 코드 변경 (DB 무관) |
| H10 | `QuotaService.RecordUsageAsync` 토큰수 무시 | `QuotaService.cs` | 코드 변경 (DB 무관) |

→ Phase 3은 **DB 전환 + 코드 부채를 동시에** 처리한다. EF baseline 작성 시점이 유일한 기회.

### 3.4 Hangfire 전환

```csharp
// Program.cs
services.AddHangfire(cfg => cfg.UsePostgreSqlStorage(
    options => options.UseNpgsqlConnection(connectionString),
    new PostgreSqlStorageOptions { SchemaName = "hangfire" }
));
```

기존 SqlServer Hangfire 잡은 폐기(잡 큐는 일시 데이터). 운영 시 cron 시간을 다시 설정한다.

---

## 4. Phase 4 — DocUtil / career schema 이전

> 본 절도 Phase 4 시작 시 갱신할 가이드. 현재는 **계획**.

### 4.1 DocUtil — 단일 PG 안에서 schema rename

DocUtil은 이미 PostgreSQL 사용. 별도 인스턴스 → AGENT_HUB 인스턴스로 데이터만 이전.

```bash
# 1. 기존 인스턴스에서 dump
pg_dump -h <docutil-current-host> -U docutil -d docutil_db \
        --schema=public --no-owner --no-acl \
        > docutil_dump.sql

# 2. dump의 schema 이름 변경 (public → document_utilization)
sed -i 's/SET search_path = public/SET search_path = document_utilization/g' docutil_dump.sql
sed -i 's/CREATE SCHEMA public/CREATE SCHEMA IF NOT EXISTS document_utilization/g' docutil_dump.sql

# 3. AGENT_HUB DB로 import
psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB \
     -v ON_ERROR_STOP=1 \
     -f docutil_dump.sql

# 4. Alembic head 재정렬
docker exec docutil-api alembic stamp head    # 새 환경에 이미 head 적용된 상태로 표시
```

이후 `docutil/.env`의 connection string을:
```
postgresql+asyncpg://AGENT_HUB:${AGENT_HUB_PW}@192.168.10.39:5440/AGENT_HUB?options=-csearch_path=document_utilization
```
로 교체.

### 4.2 career — schema 이전 + pgvector 활성화

```bash
# 1. 기존 SQL files를 idino_career schema로 적용
for f in career/database/01_*.sql career/database/02_*.sql ... career/database/60_*.sql; do
    psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB \
         -v ON_ERROR_STOP=1 \
         --set=search_path="idino_career,public" \
         -f "$f"
done

# 2. pgvector 활성화 (이미 init.sql에서 DB 단위 활성화됨)
# 3. 임베딩 컬럼 추가 + 백필
psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB <<SQL
SET search_path TO idino_career;
ALTER TABLE tb_course           ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE tb_program          ADD COLUMN IF NOT EXISTS embedding vector(1536);
ALTER TABLE tb_success_pattern  ADD COLUMN IF NOT EXISTS embedding vector(1536);
-- 백필은 ai-service의 embedding_service를 통해 별도 잡으로 수행
SQL
```

### 4.3 audit 컬럼 (career) 보존

career의 53 테이블은 `ins_user_id / ins_dt / ins_user_ip / ins_system_gcd / ins_menu_cd / upd_*` audit 컬럼을 모든 테이블에 일관 적용하고 있다. AgentHub 표준(`CreatedAt/UpdatedAt`)과 **병행 유지**한다 (TECHSPEC §4.2.2).

### 4.4 다국어 정렬 / 인덱스

```sql
-- 한국어 부분일치 검색 (BannedWord, 학생 검색 등)
CREATE INDEX IF NOT EXISTS idx_users_username_trgm
  ON "AIAgentManagement"."Users" USING GIN ("Username" gin_trgm_ops);

-- 임베딩 IVFFlat (cosine)
CREATE INDEX IF NOT EXISTS idx_doc_chunk_embedding_ivfflat
  ON "document_utilization".tb_document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

`lists` 값은 데이터 적재 후 행 수에 따라 조정 (대략 √N).

---

## 5. 부분 롤백 / 재시작 시나리오

### 5.1 schema 단위 롤백 (특정 시스템만 되돌리기)

```sql
-- DocUtil schema만 비우기 (career/agenthub은 유지)
\c AGENT_HUB
DROP SCHEMA IF EXISTS "document_utilization" CASCADE;
CREATE SCHEMA "document_utilization" AUTHORIZATION "AGENT_HUB";
COMMENT ON SCHEMA "document_utilization" IS 'docutil RAG Data Plane — tb_documents / tb_document_chunks 등';
```

이후 §4.1 절차로 재이전.

### 5.2 EF baseline 재작성 (AgentHub만)

```bash
cd agenthub

# 1. AIAgentManagement schema만 비우기
psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB <<SQL
DROP SCHEMA IF EXISTS "AIAgentManagement" CASCADE;
CREATE SCHEMA "AIAgentManagement" AUTHORIZATION "AGENT_HUB";
SQL

# 2. EF migration 폴더 비우기 (운영 적용 전이면)
rm -rf Migrations
dotnet ef migrations add Init --context AIAgentManagementDbContext
dotnet ef database update
```

운영 적용 후 baseline 재작성은 `dotnet ef migrations add Reset` + 데이터 보존을 위한 마이그레이션 스크립트 직접 작성 필요.

---

## 6. 운영 점검 체크리스트

| 항목 | 명령 | 기대 |
|---|---|---|
| 연결 확인 | `psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB -c '\dn'` | 4 schema 표시 |
| 권한 확인 | `psql ... -c "\du AGENT_HUB"` | rolcanlogin=t |
| Search path | `psql ... -c 'SHOW search_path;'` | `"AIAgentManagement","document_utilization","idino_career","hangfire",public` |
| pgvector | `psql ... -c "SELECT '[1,2,3]'::vector;"` | `[1,2,3]` |
| pg_trgm | `psql ... -c "SELECT show_trgm('한국어');"` | trigram 배열 |
| 한국어 정렬 | `psql ... -c "SELECT 'ㄱ' < 'ㄴ';"` | `t` |

---

## 7. 보안 / 시크릿 정책 (R26 / P10)

- AGENT_HUB role 비밀번호는 **환경변수/Vault만으로** 관리.
- 본 문서에 적힌 명령은 모두 `${AGENT_HUB_PW}` 같은 환경변수 참조 형태.
- 비밀번호를 변경할 때:
  ```sql
  ALTER ROLE "AGENT_HUB" WITH PASSWORD '<신규>';
  ```
  + 모든 시스템(`agenthub/appsettings.*.json`, `docutil/.env`, `career/.env`)의 connection string도 동시 갱신.
- TECHSPEC §13.2의 Vault 정책 도입 후에는 시스템들이 Vault에서 직접 가져오도록 전환한다.

---

## 8. 모니터링 (Phase 5+ 적용)

| 지표 | 도구 | 임계 |
|---|---|---|
| 연결 수 | `pg_stat_activity` | max_connections의 80% |
| 데드락 | `pg_locks` + `pg_stat_database.deadlocks` | 0 유지 |
| 슬로우 쿼리 | `pg_stat_statements` | 평균 > 1s 상위 10건 추적 |
| Bloat | `pg_stat_user_tables` | dead_tup_ratio > 20% |
| 임베딩 인덱스 hit율 | `pg_stat_user_indexes` | < 80%면 lists 재계산 |

상세 운영 가이드는 `docs/DEPLOYMENT.md` (Phase 7+ 작성 예정)에서 다룬다.

---

## 9. 변경 이력

| 일자 | 작업 | 파일 |
|---|---|---|
| 2026-05-05 | 본 가이드 v1.0 초안 작성 (Phase 2 산출) | `infra/db/init.sql`, `docs/DB_MIGRATION.md` |

---

## 부록 A — 4 schema 책임 매트릭스 (참조)

| Schema | 소유 시스템 | 마이그레이션 도구 | 주요 객체 | RAG | pgvector |
|---|---|---|---|:---:|:---:|
| `AIAgentManagement` | agenthub | EF Core 8 (Npgsql) | `Users`, `Agents`, `ApiKeys`, `ApiUsages`, `ChatConversations`, `Workflows`, `Tools` 등 35 | (deprecate, Phase 6 후 사용 안 함) | (선택) |
| `document_utilization` | docutil | Alembic | `tb_documents`, `tb_document_chunks`, `tb_chat_sessions`, `tb_documents_v2` 등 | ✅ 단일 권위 | (Qdrant + 보조용으로 PG 컬럼) |
| `idino_career` | career | SQL files | 53 `tb_*` (`tb_student`, `tb_competency`, `tb_recommendation_*`, `tb_simulation_*`, `tb_advisor_*` 등) | (검색 보조) | ✅ (`tb_course / tb_program / tb_success_pattern.embedding`) |
| `hangfire` | agenthub | Hangfire.PostgreSql 자동 | Hangfire 잡 테이블들 | ✗ | ✗ |

## 부록 B — 자주 발생하는 오류

### B.1 `extension "vector" is not available`

```
ERROR:  could not open extension control file ".../vector.control": No such file
```

→ PostgreSQL 호스트에 `pgvector` 패키지 미설치. PostgreSQL 17 + Ubuntu의 경우:
```bash
sudo apt-get install postgresql-17-pgvector
```

### B.2 `permission denied for schema "AIAgentManagement"`

→ AGENT_HUB role의 search_path 또는 connection string의 `search_path` 옵션이 schema에 도달하지 못함. `\dn+` 으로 owner 확인 후, 필요 시:
```sql
GRANT ALL ON SCHEMA "AIAgentManagement" TO "AGENT_HUB";
```

### B.3 `idle_in_transaction_session_timeout`

장시간 idle 트랜잭션이 잡혀 마이그레이션이 멈출 수 있음. 운영 인스턴스 파라미터를 확인.
```sql
SHOW idle_in_transaction_session_timeout;
```

### B.4 `lc_collate "ko_KR.UTF-8" not recognized`

OS에 한국어 로케일 미설정. Linux:
```bash
sudo locale-gen ko_KR.UTF-8
sudo update-locale
```
설정 후 PostgreSQL 재시작.
