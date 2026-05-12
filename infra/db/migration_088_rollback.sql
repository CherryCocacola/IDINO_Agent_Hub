-- ============================================================================
-- 트랙 #88 — 롤백 SQL (긴급 복구용)
-- ============================================================================
-- 적용 시점: migration_088_user_unification.sql 적용 후 문제 발견 시
-- 원칙: 새로 INSERT 된 데이터만 제거. 기존 운영 데이터는 절대 손대지 않음.

\set ON_ERROR_STOP on
BEGIN;

-- 1. 신규 흡수된 DocUtil 사용자 제거
DELETE FROM "AIAgentManagement"."UserRoles"
WHERE "UserId" IN (
  SELECT "UserId" FROM "AIAgentManagement"."Users"
  WHERE LOWER("Email") IN ('admin@docutil.local','user@docutil.local')
);
DELETE FROM "AIAgentManagement"."Users"
WHERE LOWER("Email") IN ('admin@docutil.local','user@docutil.local');

-- 2. 127명에게 일괄 할당된 User Role 제거 (단, 시드 사용자 1~4 + 255 제외)
DELETE FROM "AIAgentManagement"."UserRoles"
WHERE "UserId" NOT IN (1, 2, 3, 4, 255)
  AND "RoleId" = (SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName"='User');

-- 3. iyjung→jyjung 매핑 제거
UPDATE "AIAgentManagement"."Users"
SET "OriginalDocutilUuid" = NULL
WHERE "UserId" = 197;

-- 4. Department string → DepartmentId 매핑 제거
UPDATE "AIAgentManagement"."Users"
SET "DepartmentId" = NULL;

-- 5. FK / UNIQUE / 인덱스 DROP
ALTER TABLE "AIAgentManagement"."Users"
  DROP CONSTRAINT IF EXISTS "FK_Users_Departments_DepartmentId",
  DROP CONSTRAINT IF EXISTS "UQ_Users_OriginalDocutilUuid";
DROP INDEX IF EXISTS "AIAgentManagement"."IX_Users_DepartmentId";
DROP INDEX IF EXISTS "AIAgentManagement"."IX_Users_Email_Unique";

-- 6. 컬럼 DROP
ALTER TABLE "AIAgentManagement"."Users"
  DROP COLUMN IF EXISTS "DepartmentId",
  DROP COLUMN IF EXISTS "OriginalDocutilUuid";

-- 7. Department string 컬럼 COMMENT 복원
COMMENT ON COLUMN "AIAgentManagement"."Users"."Department" IS NULL;

-- 8. Departments 신규 INSERT 제거 (모두 — 운영에서 0행이었음)
DELETE FROM "AIAgentManagement"."Departments"
WHERE "DepartmentCode" LIKE 'DEPT_%';

-- 9. Tenants IDINO 제거
DELETE FROM "AIAgentManagement"."Tenants" WHERE "TenantCode" = 'IDINO';

COMMIT;

\echo '=== 롤백 완료 — 트랙 #88 적용 전 상태로 복원 ==='
