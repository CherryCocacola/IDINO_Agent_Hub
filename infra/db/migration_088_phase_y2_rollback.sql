-- ============================================================================
-- 옵션 Y Phase 2 — Part 2 잘못된 마이그레이션 롤백
-- ============================================================================
-- 목적:
--   1) AGENT_HUB.document_utilization 의 모든 tb_* 테이블 TRUNCATE
--      (alembic_version 유지, schema 자체는 유지)
--   2) AgentHub Users 의 OriginalDocutilUuid 중 잘못 매핑된 121명 → NULL 복원
--   3) 정확한 매핑 (진짜 docutil DB uuid 와 일치) 11명만 유지
-- ============================================================================

\set ON_ERROR_STOP on
\timing

BEGIN;

-- ============================================================================
-- SECTION 1. AGENT_HUB.document_utilization 의 데이터 TRUNCATE
-- ============================================================================
-- FK 의존성 처리를 위해 CASCADE 사용
TRUNCATE TABLE document_utilization.tb_users CASCADE;
TRUNCATE TABLE document_utilization.tb_organizations CASCADE;
-- 외에 있을 수 있는 schema 내 다른 tb_* 도 TRUNCATE
DO $$
DECLARE
  v_tbl record;
BEGIN
  FOR v_tbl IN
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='document_utilization'
      AND table_type='BASE TABLE'
      AND table_name <> 'alembic_version'
  LOOP
    EXECUTE format('TRUNCATE TABLE document_utilization.%I CASCADE', v_tbl.table_name);
    RAISE NOTICE '  TRUNCATE document_utilization.% CASCADE', v_tbl.table_name;
  END LOOP;
END $$;

-- ============================================================================
-- SECTION 2. AgentHub Users.OriginalDocutilUuid 잘못된 매핑 NULL 복원
-- ============================================================================
-- 정확한 매핑 11명만 유지 (진짜 docutil DB uuid 와 일치):
--   135 yhkim    → 29a58dae-c933-4645-b903-2fe587bd047d
--   136 gaze     → de3587d2-600a-4248-b2dc-25ad133572d8
--   137 wjlee    → 01c0f2d4-0a30-42f8-84d7-69d4693cc16c
--   138 dglee    → 52ff0252-d940-4357-8b19-6a1bda9b4cb3
--   143 dongun   → 8baf9e41-20d9-4db6-b195-b04c8bab88f4
--   166 jyj7970  → bafe866b-b7e2-4d26-8165-af62295e62f0
--   197 iyjung   → 8c07639f-f5b3-4901-a550-b5eb32efa2ca  (jyjung@idino 매핑)
--   220 shbaek   → 40811ca9-d838-4457-a8fe-a8a3cade70dd
--   221 hslee    → b54f6c80-85f4-4810-bf5a-ecc4452e68ca
--   260 admin@docutil.local → 00000000-0000-4000-a000-000000000002
--   261 user@docutil.local  → a0000000-0000-4000-a000-000000000003

UPDATE "AIAgentManagement"."Users"
SET "OriginalDocutilUuid" = NULL,
    "UpdatedAt" = NOW()
WHERE "UserId" NOT IN (135, 136, 137, 138, 143, 166, 197, 220, 221, 260, 261)
  AND "OriginalDocutilUuid" IS NOT NULL;

-- 만약 위 11명 매핑이 깨졌다면 정확한 uuid 로 복원
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '29a58dae-c933-4645-b903-2fe587bd047d'::uuid WHERE "UserId" = 135;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'de3587d2-600a-4248-b2dc-25ad133572d8'::uuid WHERE "UserId" = 136;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '01c0f2d4-0a30-42f8-84d7-69d4693cc16c'::uuid WHERE "UserId" = 137;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '52ff0252-d940-4357-8b19-6a1bda9b4cb3'::uuid WHERE "UserId" = 138;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '8baf9e41-20d9-4db6-b195-b04c8bab88f4'::uuid WHERE "UserId" = 143;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'bafe866b-b7e2-4d26-8165-af62295e62f0'::uuid WHERE "UserId" = 166;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '8c07639f-f5b3-4901-a550-b5eb32efa2ca'::uuid WHERE "UserId" = 197;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '40811ca9-d838-4457-a8fe-a8a3cade70dd'::uuid WHERE "UserId" = 220;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'b54f6c80-85f4-4810-bf5a-ecc4452e68ca'::uuid WHERE "UserId" = 221;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '00000000-0000-4000-a000-000000000002'::uuid WHERE "UserId" = 260;
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'a0000000-0000-4000-a000-000000000003'::uuid WHERE "UserId" = 261;

-- ============================================================================
-- SECTION 3. 검증
-- ============================================================================
\echo '\n=== 검증 1: AGENT_HUB.document_utilization 의 tb_users (TRUNCATE 후) ==='
SELECT COUNT(*) AS tb_users_count FROM document_utilization.tb_users;

\echo '\n=== 검증 2: AgentHub Users.OriginalDocutilUuid 매핑 (11명만 남아야) ==='
SELECT "UserId", "Email", "OriginalDocutilUuid"
FROM "AIAgentManagement"."Users"
WHERE "OriginalDocutilUuid" IS NOT NULL
ORDER BY "UserId";

\echo '\n=== 검증 3: 잘못 매핑 121명 NULL 복원 확인 ==='
SELECT COUNT(*) AS unmapped_count
FROM "AIAgentManagement"."Users"
WHERE "IsDeleted"=false AND "OriginalDocutilUuid" IS NULL;

COMMIT;

\echo '\n=== Phase Y-2 완료 ==='
