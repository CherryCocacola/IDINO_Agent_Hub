-- ============================================================================
-- 트랙 #88 Part 2 — DocUtil tb_users 동기화 (응급 처리)
-- ============================================================================
-- 목적:
--   AgentHub Users 131명 → DocUtil document_utilization.tb_users 에 동기화.
--   동일 사용자가 양쪽 시스템에 같은 비번 hash 로 로그인 가능.
--   22 SKIP e2e 시나리오 즉시 해소.
--
-- 원칙:
--   - 비번 hash 복제 (BCrypt 양쪽 호환) — C4-A 결정 따름
--   - AgentHub Users.OriginalDocutilUuid 가 있으면 그 uuid 사용 (8명 매칭 + 신규 흡수 2명)
--   - 없으면 신규 uuid 생성 — 그 후 AgentHub Users.OriginalDocutilUuid 에 역방향 UPDATE
--   - organization_id = '00000000-0000-4000-a000-000000000001' (기존 Default Organization)
--   - department_id = NULL (DocUtil tb_departments 가 비어있어 매핑 불가, 추후 보강)
--   - role: AgentHub UserRoles 기반 매핑
--
-- 적용:
--   docker exec -e PGPASSWORD='idino!@#$' docutil-postgres \
--     psql -U AGENT_HUB -d AGENT_HUB \
--     -v ON_ERROR_STOP=1 -f /tmp/migration_088_part2.sql
-- ============================================================================

\set ON_ERROR_STOP on
\timing

BEGIN;

-- 사전 상태
DO $$
DECLARE v_ah int; v_du int;
BEGIN
  SELECT COUNT(*) INTO v_ah FROM "AIAgentManagement"."Users" WHERE "IsDeleted"=false;
  SELECT COUNT(*) INTO v_du FROM document_utilization.tb_users;
  RAISE NOTICE '[SECTION 0] 사전 — AgentHub Users active=%, DocUtil tb_users=%', v_ah, v_du;
END $$;

-- ============================================================================
-- SECTION 1. AgentHub Users → DocUtil tb_users 동기화
-- ============================================================================

-- 1-1. 매핑된 OriginalDocutilUuid 가 있는 사용자 (11명) — UPDATE
-- 비번 hash + 상태 동기화. 단, AgentHub master 비번 유지 (C4-A)
UPDATE document_utilization.tb_users du
SET password_hash = u."PasswordHash",
    upd_dt = NOW()
FROM "AIAgentManagement"."Users" u
WHERE u."OriginalDocutilUuid" = du.id
  AND u."IsDeleted" = false;

-- 1-2. DocUtil tb_users 에 존재하지 않는 모든 AgentHub Users → INSERT
-- (매핑된 OriginalDocutilUuid 가 있어도, DocUtil 행이 실제로 없으면 신규 INSERT)
-- 매핑된 사람은 COALESCE 로 기존 uuid 보존, 신규 사람은 gen_random_uuid()
WITH new_users AS (
  INSERT INTO document_utilization.tb_users
    (id, organization_id, department_id, username, email, password_hash,
     role, status, failed_login_count, language, ins_dt, upd_dt)
  SELECT
    COALESCE(u."OriginalDocutilUuid", gen_random_uuid()) AS id,
    '00000000-0000-4000-a000-000000000001'::uuid AS organization_id,
    NULL::uuid AS department_id,
    -- username: email 의 로컬파트가 admin/user 등 시드와 충돌하면 전체 email 사용
    CASE
      WHEN LOWER(SPLIT_PART(u."Email", '@', 1)) IN ('admin','user','developer','test')
        THEN LOWER(u."Email")
      ELSE LOWER(SPLIT_PART(u."Email", '@', 1))
    END AS username,
    LOWER(u."Email") AS email,
    u."PasswordHash" AS password_hash,
    -- role 매핑: AgentHub UserRoles 기반
    CASE
      WHEN EXISTS (
        SELECT 1 FROM "AIAgentManagement"."UserRoles" ur
        JOIN "AIAgentManagement"."Roles" r ON r."RoleId" = ur."RoleId"
        WHERE ur."UserId" = u."UserId" AND r."RoleName" = 'Admin'
      ) THEN 'super_admin'
      WHEN EXISTS (
        SELECT 1 FROM "AIAgentManagement"."UserRoles" ur
        JOIN "AIAgentManagement"."Roles" r ON r."RoleId" = ur."RoleId"
        WHERE ur."UserId" = u."UserId" AND r."RoleName" = 'Developer'
      ) THEN 'admin'
      ELSE 'member'
    END AS role,
    LOWER(u."Status") AS status,
    0 AS failed_login_count,
    'ko' AS language,
    COALESCE(u."CreatedAt", NOW()) AS ins_dt,
    NOW() AS upd_dt
  FROM "AIAgentManagement"."Users" u
  WHERE u."IsDeleted" = false
    -- DocUtil tb_users 에 같은 email 이 없는 경우만 INSERT
    AND NOT EXISTS (
      SELECT 1 FROM document_utilization.tb_users d
      WHERE LOWER(d.email) = LOWER(u."Email")
        AND d.organization_id = '00000000-0000-4000-a000-000000000001'::uuid
    )
    -- OriginalDocutilUuid 가 이미 docutil tb_users 에 있으면 skip (다른 email 로 매핑된 경우)
    AND (u."OriginalDocutilUuid" IS NULL
         OR NOT EXISTS (
           SELECT 1 FROM document_utilization.tb_users d
           WHERE d.id = u."OriginalDocutilUuid"
         ))
  RETURNING id, email
)
-- 1-3. 신규 INSERT 된 사용자 중 OriginalDocutilUuid 가 NULL 이었던 사람만 역방향 UPDATE
UPDATE "AIAgentManagement"."Users" u
SET "OriginalDocutilUuid" = nu.id,
    "UpdatedAt" = NOW()
FROM new_users nu
WHERE LOWER(u."Email") = nu.email
  AND u."OriginalDocutilUuid" IS NULL
  AND u."IsDeleted" = false;

-- ============================================================================
-- SECTION 2. 검증
-- ============================================================================
DO $$
DECLARE
  v_ah_total int; v_ah_synced int;
  v_du_total int; v_unmapped int;
BEGIN
  SELECT COUNT(*) INTO v_ah_total FROM "AIAgentManagement"."Users" WHERE "IsDeleted"=false;
  SELECT COUNT(*) INTO v_ah_synced FROM "AIAgentManagement"."Users"
    WHERE "IsDeleted"=false AND "OriginalDocutilUuid" IS NOT NULL;
  SELECT COUNT(*) INTO v_du_total FROM document_utilization.tb_users;
  SELECT COUNT(*) INTO v_unmapped FROM "AIAgentManagement"."Users"
    WHERE "IsDeleted"=false AND "OriginalDocutilUuid" IS NULL;
  RAISE NOTICE '[SECTION 2] AgentHub Users=%, AgentHub synced=%, DocUtil tb_users=%, unmapped=%',
    v_ah_total, v_ah_synced, v_du_total, v_unmapped;
  IF v_unmapped > 0 THEN
    RAISE WARNING '동기화 미완료: % 명의 AgentHub Users 가 DocUtil 에 매핑되지 않음', v_unmapped;
  END IF;
END $$;

-- 검증 쿼리
\echo '\n=== 검증 1: 양쪽 시스템 사용자 수 ==='
SELECT 'AgentHub' AS system, COUNT(*) AS users FROM "AIAgentManagement"."Users" WHERE "IsDeleted"=false
UNION ALL
SELECT 'DocUtil', COUNT(*) FROM document_utilization.tb_users
UNION ALL
SELECT 'AgentHub mapped to DocUtil', COUNT(*)
FROM "AIAgentManagement"."Users" WHERE "IsDeleted"=false AND "OriginalDocutilUuid" IS NOT NULL;

\echo '\n=== 검증 2: DocUtil role 분포 ==='
SELECT role, COUNT(*) AS user_count
FROM document_utilization.tb_users
GROUP BY role
ORDER BY user_count DESC;

\echo '\n=== 검증 3: 동기화 샘플 5건 ==='
SELECT u."UserId" AS ah_user_id, u."Email", u."FullName",
       du.id AS du_uuid, du.username, du.role
FROM "AIAgentManagement"."Users" u
JOIN document_utilization.tb_users du ON u."OriginalDocutilUuid" = du.id
WHERE u."IsDeleted" = false
ORDER BY u."UserId" LIMIT 5;

\echo '\n=== 검증 4: 비번 hash 일치 확인 (매핑된 11명 + 신규 INSERT 가 동일) ==='
SELECT COUNT(*) AS hash_mismatch_count
FROM "AIAgentManagement"."Users" u
JOIN document_utilization.tb_users du ON u."OriginalDocutilUuid" = du.id
WHERE u."IsDeleted" = false
  AND u."PasswordHash" != du.password_hash;

COMMIT;

\echo '\n=== Part 2 완료 — 양쪽 시스템 동기화 완료 ==='
