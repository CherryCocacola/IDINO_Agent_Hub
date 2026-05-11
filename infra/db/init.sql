-- =====================================================================
-- IDINO Agent Hub — AGENT_HUB DB 초기화 스크립트
-- =====================================================================
--
-- 목적: 단일 PostgreSQL 인스턴스에 통합 DB(`AGENT_HUB`) + 4개 schema +
--       필수 extensions + role/권한 정책을 idempotent하게 셋업한다.
--
-- 적용 위치: PostgreSQL 17 / 192.168.10.39:5440 (TECHSPEC §5.1)
-- 적용 방법: 슈퍼유저(`postgres`)로 본 스크립트를 실행
--           psql -h 192.168.10.39 -p 5440 -U postgres -f init.sql \
--                -v idino_pw="'<여기 비밀번호 주입>'"
--           (비밀번호는 .env / Vault에서 주입; 파일에 평문 금지 — TECHSPEC P10/R26)
--
-- 본 스크립트는 schema/extension/role까지만 만든다. 테이블/시드 데이터는:
--   * AIAgentManagement schema → Phase 3에서 EF Core baseline 마이그레이션 (Npgsql)
--   * document_utilization     → Phase 4에서 Alembic head 재정렬
--   * idino_career             → Phase 4에서 SQL files (`database/01_*.sql~`) 적용
--   * hangfire                 → Hangfire.PostgreSql 첫 부팅 시 자동 생성
--
-- 의존: TECHSPEC v1.0 §4 §5 §7 / ADR-4 / ADR-10 / P4 / P10 / R26 / R29
-- 관련: docs/DB_MIGRATION.md (마이그레이션 절차/롤백)
--
-- ⚠ 안전 수칙:
--   - 운영 DB에 직접 실행하지 말고, 먼저 dev/staging에서 dry-run.
--   - 평문 비밀번호 하드코딩 금지. 본 파일은 Git 추적 대상이므로
--     실제 비밀번호는 반드시 -v 변수로 주입한다.
--   - PostgreSQL `idle_in_transaction_session_timeout` 등 운영 파라미터는
--     본 스크립트가 손대지 않는다. 운영 가이드는 docs/DB_MIGRATION.md 참조.
-- =====================================================================


-- =====================================================================
-- §0. 변수 검증
-- =====================================================================
-- psql -v idino_pw="'<password>'" 형식으로 주입되었는지 확인.
-- 실패 시 이후 CREATE ROLE이 NULL 패스워드로 만들어지지 않도록 가드.

\set ON_ERROR_STOP on

\if :{?idino_pw}
\else
    \echo '[ERROR] -v idino_pw="''<password>''" 변수가 필요합니다.'
    \echo '         예: psql -v idino_pw="''S3cret!''" -f init.sql'
    \quit
\endif


-- =====================================================================
-- §1. DB user (role) 생성 — 멱등
-- =====================================================================
-- AGENT_HUB role: 4개 schema의 owner. LOGIN 권한 부여.
-- (필요 시 Phase 9+에서 schema별 read-only role 분리 가능 — R29)

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'AGENT_HUB') THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', 'AGENT_HUB', :'idino_pw');
        RAISE NOTICE 'role AGENT_HUB 생성 완료';
    ELSE
        -- 비밀번호 회전 시 같은 변수로 주입 가능 (의도하지 않은 변경 방지를 위해 NOTICE만)
        RAISE NOTICE 'role AGENT_HUB 이미 존재 — 비밀번호 변경은 별도 ALTER ROLE로 수행';
    END IF;
END
$$;


-- =====================================================================
-- §2. DATABASE `AGENT_HUB` 생성 — 멱등
-- =====================================================================
-- ENCODING='UTF8', LC_COLLATE='ko_KR.UTF-8' (한국어 정렬).
-- TEMPLATE0를 사용해야 LC_COLLATE/CTYPE 변경 가능.
--
-- 주의: CREATE DATABASE는 트랜잭션 블록에서 실행 불가 → \gexec 패턴 사용.

SELECT 'CREATE DATABASE "AGENT_HUB"
        OWNER "AGENT_HUB"
        ENCODING ''UTF8''
        LC_COLLATE ''ko_KR.UTF-8''
        LC_CTYPE   ''ko_KR.UTF-8''
        TEMPLATE template0;'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'AGENT_HUB')
\gexec


-- =====================================================================
-- §3. 이후 명령은 `AGENT_HUB` DB 안에서 수행
-- =====================================================================

\connect "AGENT_HUB"


-- =====================================================================
-- §4. Extensions — DB 단위 1회
-- =====================================================================
-- TECHSPEC §5.1 표준 4종.
--
-- vector       : pgvector — 임베딩 (1536D 표준, ADR-10)
-- uuid-ossp    : uuid_generate_v4() (호환 보존)
-- pgcrypto     : gen_random_uuid() (NEWID 대체, 권장)
-- pg_trgm      : 한국어 부분일치 / GIN 인덱스 보조

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- =====================================================================
-- §5. Schema 4종 생성 — 멱등
-- =====================================================================
-- TECHSPEC §5.2 / P4 (cross-schema join 금지).
--
-- AIAgentManagement   : agenthub (Control Plane)
-- document_utilization: docutil  (RAG Data Plane)
-- idino_career        : career   (Domain Data Plane)
-- hangfire            : agenthub의 백그라운드 잡 스토리지

CREATE SCHEMA IF NOT EXISTS "AIAgentManagement"    AUTHORIZATION "AGENT_HUB";
CREATE SCHEMA IF NOT EXISTS "document_utilization" AUTHORIZATION "AGENT_HUB";
CREATE SCHEMA IF NOT EXISTS "idino_career"         AUTHORIZATION "AGENT_HUB";
CREATE SCHEMA IF NOT EXISTS "hangfire"             AUTHORIZATION "AGENT_HUB";

COMMENT ON SCHEMA "AIAgentManagement"    IS 'agenthub Control Plane — Agents/ApiKeys/Quota/Usage/Workflow';
COMMENT ON SCHEMA "document_utilization" IS 'docutil RAG Data Plane — tb_documents / tb_document_chunks 등';
COMMENT ON SCHEMA "idino_career"         IS 'career Domain Data Plane — 53 tb_* (학생/역량/코칭/시뮬레이션)';
COMMENT ON SCHEMA "hangfire"             IS 'AgentHub Hangfire 잡 스토리지 (자동 생성 테이블)';


-- =====================================================================
-- §6. 향후 객체에 대한 기본 권한 — 멱등
-- =====================================================================
-- AGENT_HUB role이 각 schema에 신규로 만들어지는 모든 테이블/시퀀스/함수에
-- 자동으로 권한을 받도록 ALTER DEFAULT PRIVILEGES 설정.
-- (소유자가 같으므로 사실상 형식적이지만, 향후 schema별 사용자 분리 시 의미가 있음)

DO $$
DECLARE
    s text;
BEGIN
    FOREACH s IN ARRAY ARRAY['AIAgentManagement','document_utilization','idino_career','hangfire']
    LOOP
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I
             GRANT ALL ON TABLES    TO %I;', 'AGENT_HUB', s, 'AGENT_HUB');

        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I
             GRANT ALL ON SEQUENCES TO %I;', 'AGENT_HUB', s, 'AGENT_HUB');

        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE %I IN SCHEMA %I
             GRANT EXECUTE ON FUNCTIONS TO %I;', 'AGENT_HUB', s, 'AGENT_HUB');
    END LOOP;
END
$$;


-- =====================================================================
-- §7. AGENT_HUB role의 search_path 기본값
-- =====================================================================
-- DB user 단위 search_path. 각 시스템은 필요 시 connection 단위로 override.
--   - agenthub : "AIAgentManagement", "hangfire", public
--   - docutil  : "document_utilization", public
--   - career   : "idino_career", public
-- 본 단계에서는 AGENT_HUB role 공통으로 4 schema + public 우선순위만 부여.
-- 시스템별 격리는 connection string의 Search Path 옵션에서 처리한다.

ALTER ROLE "AGENT_HUB" SET search_path TO
    "AIAgentManagement",
    "document_utilization",
    "idino_career",
    "hangfire",
    public;


-- =====================================================================
-- §8. 검증 쿼리 (실행 후 결과 확인용)
-- =====================================================================
-- 실행 결과:
--   - extensions: 4행 (vector / uuid-ossp / pgcrypto / pg_trgm)
--   - schemas:    4행 + public/information_schema/pg_catalog 등 시스템 schema
--   - role:       AGENT_HUB rolname 1행, rolcanlogin=t

SELECT extname, extversion FROM pg_extension
WHERE extname IN ('vector','uuid-ossp','pgcrypto','pg_trgm')
ORDER BY extname;

SELECT schema_name, schema_owner FROM information_schema.schemata
WHERE schema_name IN ('AIAgentManagement','document_utilization','idino_career','hangfire')
ORDER BY schema_name;

SELECT rolname, rolcanlogin, rolsuper FROM pg_roles
WHERE rolname = 'AGENT_HUB';


-- =====================================================================
-- §9. 다음 단계 (Phase 3 이후)
-- =====================================================================
-- 본 init.sql 실행 완료 후:
--
-- (Phase 3) AgentHub PostgreSQL baseline 마이그레이션
--   cd agenthub
--   dotnet ef migrations add Init --context AIAgentManagementDbContext
--   dotnet ef database update
--   → AIAgentManagement schema에 35개 테이블 생성
--
-- (Phase 3.5+) Phase 2.x / 5.1 / 7.1 시드 codify 파일 적용
--   psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB \
--        -f infra/db/seeds/phase5_phase7_seeds.sql
--   → ApiServices 16개 (Phase 2.x + Phase 5.1 Nexus 포함)
--   → Agents 15개 (Phase 7.1, DU 4 + career 8 + 공통 3)
--   멱등 가드: INSERT ... WHERE NOT EXISTS (...)  -- 재실행 시 0행 INSERT
--   참고: ApiKey 는 운영 DB 가 master (codify 제외) — 신규 환경에서는
--        `user_mig/tools/phase72_seed.py --print-keys` 로 재발급
--
-- (Phase 4) DocUtil schema 이전
--   docker exec docutil-api alembic upgrade head
--   → document_utilization schema에 기존 tb_* 재배치
--
-- (Phase 4) career schema 이전
--   psql -h 192.168.10.39 -p 5440 -U AGENT_HUB -d AGENT_HUB \
--        -f career/database/01_schema_create.sql
--   → idino_career schema에 53 tb_* 재배치
--
-- (Hangfire) 자동 — AgentHub 첫 부팅 시 hangfire schema에 잡 테이블 생성
-- =====================================================================
