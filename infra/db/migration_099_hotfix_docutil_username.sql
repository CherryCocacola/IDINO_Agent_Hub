-- 트랙 #99 hotfix (2026-05-18) — DocUtil VIEW username alias 결함 + agenthub_bff 시드 누락 fix.
--
-- 결함 카탈로그:
--   1) 트랙 #98 phase 3 VIEW 의 username = FullName(한국어) → DocUtil 의
--      username='agenthub_bff' / 'admin' / 'user' 등 영문 short 검색이 실패.
--   2) AgentHub.Users 에 agenthub_bff 시드 누락 → ServiceAccount 로그인 401 → BFF 14건 5xx.
--   3) DocUtil admin/user 짧은 username 검색 시 email LIKE 폴백 → MultipleResultsFound 500.
--
-- 통합 fix:
--   1) AgentHub.Users 에 DocutilUsername VARCHAR(150) 컬럼 신규 추가
--   2) legacy 테이블에서 132명 원본 영문 username (hslee/shbaek/admin/user/agenthub_bff/...) 복원
--   3) agenthub_bff 시스템 계정 행 INSERT (legacy 의 원본 데이터 사용)
--   4) VIEW DROP + 재생성 — username alias 를 COALESCE(DocutilUsername, FullName) 로 변경
--
-- 트랜잭션 단위. 사후 검증 DO 블록 포함.

BEGIN;

-- ====================================================================
-- 1) AgentHub.Users 에 DocutilUsername 컬럼 추가
-- ====================================================================
ALTER TABLE "AIAgentManagement"."Users"
  ADD COLUMN IF NOT EXISTS "DocutilUsername" VARCHAR(150);

-- ====================================================================
-- 2) legacy 테이블에서 원본 username 복원 (132명, 매핑 100%)
-- ====================================================================
UPDATE "AIAgentManagement"."Users" u
SET "DocutilUsername" = l.username
FROM document_utilization.tb_users_legacy_20260518 l
WHERE u."OriginalDocutilUuid" = l.id
  AND u."DocutilUsername" IS NULL;

-- ====================================================================
-- 3) agenthub_bff 시스템 계정 누락 보완 — legacy 의 데이터로 INSERT
--    OriginalDocutilUuid = b6d40352-7657-4305-85fa-a30f15700447 (legacy 확인)
-- ====================================================================
DO $$
DECLARE
  bff_user_id INT;
  admin_role_id INT;
BEGIN
  -- 이미 존재하면 skip (idempotent)
  IF EXISTS (
    SELECT 1 FROM "AIAgentManagement"."Users"
    WHERE "OriginalDocutilUuid" = 'b6d40352-7657-4305-85fa-a30f15700447'::uuid
  ) THEN
    RAISE NOTICE 'agenthub_bff 이미 존재 — INSERT 생략';
  ELSE
    -- legacy 의 데이터 그대로 INSERT (password_hash 포함)
    INSERT INTO "AIAgentManagement"."Users" (
      "Email", "PasswordHash", "FullName", "Status",
      "OrganizationId", "Language", "FailedLoginCount",
      "IsEmailVerified", "IsDeleted", "IsTwoFactorEnabled",
      "OriginalDocutilUuid", "DocutilUsername",
      "CreatedAt", "UpdatedAt")
    SELECT
      l.email,
      l.password_hash,
      'AgentHub BFF (시스템)',  -- 운영자 콘솔 UI 표시용 한국어명
      'Active',
      '00000000-0000-4000-a000-000000000001'::uuid,
      COALESCE(l.language, 'ko'),
      COALESCE(l.failed_login_count, 0),
      TRUE,  -- 시스템 계정은 이메일 검증 완료로 간주
      FALSE,
      FALSE,
      l.id,
      l.username,  -- 'agenthub_bff' 원본 보존
      l.ins_dt,
      COALESCE(l.upd_dt, l.ins_dt)
    FROM document_utilization.tb_users_legacy_20260518 l
    WHERE l.id = 'b6d40352-7657-4305-85fa-a30f15700447'::uuid
    RETURNING "UserId" INTO bff_user_id;

    -- Admin role 부여 (legacy 의 role='admin' 그대로)
    SELECT "RoleId" INTO admin_role_id FROM "AIAgentManagement"."Roles" WHERE "RoleName" = 'Admin' LIMIT 1;
    IF admin_role_id IS NOT NULL THEN
      INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt")
      VALUES (bff_user_id, admin_role_id, NOW() AT TIME ZONE 'UTC');
    END IF;

    RAISE NOTICE 'agenthub_bff 시스템 계정 복원 완료 — UserId=%, Admin role 부여', bff_user_id;
  END IF;
END $$;

-- ====================================================================
-- 4) VIEW 재생성 — username alias 변경
-- ====================================================================
-- 기존 VIEW DROP (관련 INSTEAD OF TRIGGER 도 자동 DROP)
DROP VIEW IF EXISTS document_utilization.tb_users CASCADE;

-- 새 VIEW — username = COALESCE(DocutilUsername, FullName)
CREATE OR REPLACE VIEW document_utilization.tb_users AS
SELECT
  u."OriginalDocutilUuid" AS id,
  u."OrganizationId" AS organization_id,
  NULL::uuid AS department_id,  -- 매핑 차이로 NULL (사용자 정리 영역)
  -- 트랙 #99 hotfix: 원본 영문 username 우선, FullName fallback.
  -- 이로써 DocUtil 의 username='hslee'/'agenthub_bff' 등 영문 검색이 정상 매칭됨.
  COALESCE(u."DocutilUsername", u."FullName") AS username,
  u."Email" AS email,
  u."PasswordHash" AS password_hash,
  COALESCE(
    (SELECT LOWER(r."RoleName")
     FROM "AIAgentManagement"."UserRoles" ur
     JOIN "AIAgentManagement"."Roles" r ON ur."RoleId" = r."RoleId"
     WHERE ur."UserId" = u."UserId"
     ORDER BY ur."AssignedAt" LIMIT 1),
    'member'
  ) AS role,
  LOWER(u."Status") AS status,
  COALESCE(u."FailedLoginCount", 0) AS failed_login_count,
  u."LockedUntil" AS locked_until,
  u."LastLoginAt" AS last_login_at,
  COALESCE(u."Language", 'ko') AS language,
  u."PasswordResetToken" AS password_reset_token,
  u."PasswordResetTokenExpiry" AS password_reset_expires_at,
  u."CreatedAt" AS ins_dt,
  NULL::uuid AS ins_user,
  NULL::varchar(45) AS ins_ip,
  u."UpdatedAt" AS upd_dt,
  NULL::uuid AS upd_user,
  NULL::varchar(45) AS upd_ip
FROM "AIAgentManagement"."Users" u
WHERE u."IsDeleted" = FALSE
  AND u."OriginalDocutilUuid" IS NOT NULL;

COMMENT ON VIEW document_utilization.tb_users IS
  '트랙 #99 hotfix (2026-05-18) — username = COALESCE(DocutilUsername, FullName). admin/user/agenthub_bff 등 영문 short username 매칭 가능.';

-- INSTEAD OF TRIGGER 재생성 (DROP CASCADE 로 함께 사라짐)
-- INSERT TRIGGER
CREATE TRIGGER tb_users_instead_insert
INSTEAD OF INSERT ON document_utilization.tb_users
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_users_insert_fn();

-- UPDATE TRIGGER
CREATE TRIGGER tb_users_instead_update
INSTEAD OF UPDATE ON document_utilization.tb_users
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_users_update_fn();

-- DELETE TRIGGER
CREATE TRIGGER tb_users_instead_delete
INSTEAD OF DELETE ON document_utilization.tb_users
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_users_delete_fn();

-- ====================================================================
-- 5) 검증
-- ====================================================================
DO $$
DECLARE
  view_count INT;
  username_filled INT;
  agenthub_bff_in_view INT;
  admin_in_view INT;
  user_in_view INT;
  trigger_count INT;
BEGIN
  SELECT COUNT(*) INTO view_count FROM document_utilization.tb_users;
  SELECT COUNT(*) INTO username_filled
  FROM "AIAgentManagement"."Users" WHERE "DocutilUsername" IS NOT NULL;
  -- 핵심 검증: 영문 short username 으로 view 검색 매칭 (DocUtil ServiceAccount/admin/user 로그인 가능)
  SELECT COUNT(*) INTO agenthub_bff_in_view
  FROM document_utilization.tb_users WHERE username = 'agenthub_bff';
  SELECT COUNT(*) INTO admin_in_view
  FROM document_utilization.tb_users WHERE username = 'admin';
  SELECT COUNT(*) INTO user_in_view
  FROM document_utilization.tb_users WHERE username = 'user';
  SELECT COUNT(*) INTO trigger_count
  FROM information_schema.triggers
  WHERE event_object_schema = 'document_utilization'
    AND event_object_table = 'tb_users'
    AND trigger_name LIKE 'tb_users_instead_%';

  IF agenthub_bff_in_view <> 1 THEN
    RAISE EXCEPTION 'hotfix 검증 실패: agenthub_bff VIEW 매칭 % (예상: 1) — ServiceAccount 로그인 fix 안됨', agenthub_bff_in_view;
  END IF;

  -- admin/user 는 legacy 에 1행씩 (admin@docutil.local + user@docutil.local) — 매칭 필수
  IF admin_in_view <> 1 OR user_in_view <> 1 THEN
    RAISE EXCEPTION 'hotfix 검증 실패: admin/user VIEW 매칭 admin=% user=% (예상: 1/1) — DocUtil 시드 로그인 fix 안됨', admin_in_view, user_in_view;
  END IF;

  IF trigger_count <> 3 THEN
    RAISE EXCEPTION 'hotfix 검증 실패: trigger 수 % (예상: 3)', trigger_count;
  END IF;

  RAISE NOTICE 'hotfix OK — VIEW rows=%, DocutilUsername 채움=%, agenthub_bff=%, admin=%, user=%, triggers=%',
    view_count, username_filled, agenthub_bff_in_view, admin_in_view, user_in_view, trigger_count;
END $$;

COMMIT;
