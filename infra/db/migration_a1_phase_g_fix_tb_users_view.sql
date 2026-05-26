-- 트랙 #107 (2026-05-26) — tb_users VIEW schema 명시 fix.
-- 트랙 #98 phase 3 의 VIEW 가 `FROM "Users" u` (schema 미명시) 로 정의됨.
-- AGENT_HUB user (search_path 에 "AIAgentManagement" 포함) 로는 정상 동작했으나,
-- DocUtil app 이 docutil user 로 connect 시 search_path = document_utilization,public 뿐 →
-- VIEW 의 unqualified "Users" 가 잘못된 schema 에서 검색 → admin@example.com / 신규 user
-- 일부 fetch 안 됨 → DocUtil 로그인 401 (모든 신규 계정).
--
-- 동일 패턴 tb_departments VIEW (트랙 A1 Phase D) 는 이미 `"AIAgentManagement"."Departments"`
-- 명시되어 영향 없음.
--
-- 본 마이그레이션 = VIEW DROP + 재생성 (TRIGGER 보존). 단일 트랜잭션, 실패 시 ROLLBACK.

BEGIN;

-- 1) 기존 VIEW 정의를 schema 명시로 재생성 (TRIGGER 는 VIEW 에 attach 되므로 DROP 안 함)
CREATE OR REPLACE VIEW document_utilization.tb_users AS
SELECT
  u."OriginalDocutilUuid" AS id,
  u."OrganizationId" AS organization_id,
  NULL::uuid AS department_id,
  COALESCE(u."DocutilUsername", u."FullName") AS username,
  u."Email" AS email,
  u."PasswordHash" AS password_hash,
  COALESCE(
    (SELECT LOWER(r."RoleName"::text)
     FROM "AIAgentManagement"."UserRoles" ur
     JOIN "AIAgentManagement"."Roles" r ON ur."RoleId" = r."RoleId"
     WHERE ur."UserId" = u."UserId"
     ORDER BY ur."AssignedAt"
     LIMIT 1),
    'member'::text
  ) AS role,
  LOWER(u."Status"::text) AS status,
  COALESCE(u."FailedLoginCount", 0) AS failed_login_count,
  u."LockedUntil" AS locked_until,
  u."LastLoginAt" AS last_login_at,
  COALESCE(u."Language", 'ko'::character varying) AS language,
  u."PasswordResetToken" AS password_reset_token,
  u."PasswordResetTokenExpiry" AS password_reset_expires_at,
  u."CreatedAt" AS ins_dt,
  NULL::uuid AS ins_user,
  NULL::character varying(45) AS ins_ip,
  u."UpdatedAt" AS upd_dt,
  NULL::uuid AS upd_user,
  NULL::character varying(45) AS upd_ip
FROM "AIAgentManagement"."Users" u
WHERE u."IsDeleted" = FALSE
  AND u."OriginalDocutilUuid" IS NOT NULL;

COMMENT ON VIEW document_utilization.tb_users IS
  '트랙 #98 Phase 3 + #107 (2026-05-26 schema 명시 fix) — AIAgentManagement.Users alias VIEW. INSTEAD OF TRIGGER 가 INSERT/UPDATE/DELETE 위임.';

-- 2) docutil user search_path ALTER 는 SUPERUSER 필요 — 별도로 사용자가 수동 적용:
--    sudo -u postgres psql -c 'ALTER USER docutil SET search_path = document_utilization, "AIAgentManagement", public;'
--    본 마이그레이션에서는 VIEW schema 명시만으로 충분 (보조 안전망만 별도).

-- 3) 검증
DO $$
DECLARE
  v_count INT;
  v_admin_found INT;
BEGIN
  SELECT COUNT(*) INTO v_count FROM document_utilization.tb_users;
  SELECT COUNT(*) INTO v_admin_found FROM document_utilization.tb_users WHERE email = 'admin@example.com';
  IF v_admin_found <> 1 THEN
    RAISE EXCEPTION '#107 fix 검증 실패: admin@example.com fetch 결과 % (예상 1)', v_admin_found;
  END IF;
  RAISE NOTICE '#107 fix OK — VIEW rows=%, admin@example.com fetch=%', v_count, v_admin_found;
END $$;

COMMIT;
