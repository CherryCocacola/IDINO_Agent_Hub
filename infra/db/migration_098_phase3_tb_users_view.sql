-- 트랙 #98 Phase 3 (2026-05-18) — DocUtil tb_users 진정한 단일 통합.
-- 사용자 의도: "DocUtil tb_users 테이블을 삭제해도 될 정도로 통합".
--
-- 전략 (VIEW + INSTEAD OF TRIGGER):
--   1) 14개 FK DROP (application-level + INSTEAD OF trigger 가 무결성 검증)
--   2) tb_users 테이블을 tb_users_legacy_20260518 로 RENAME (7일 read-only 유예)
--   3) tb_users 라는 동일 이름의 VIEW 생성 — AIAgentManagement.Users 의 컬럼 alias
--   4) INSTEAD OF INSERT/UPDATE/DELETE TRIGGER 3개 — DocUtil ORM 의 write 를 AgentHub.Users 로 위임
--
-- 결과: DocUtil ORM 코드 무변경 + 물리 SOT 가 AIAgentManagement.Users 단일화.
-- 트랜잭션 단위로 적용. 실패 시 자동 rollback.

BEGIN;

-- ====================================================================
-- 3-1. 14개 FK DROP (application-level constraint 로 전환)
-- ====================================================================
ALTER TABLE document_utilization.tb_boards DROP CONSTRAINT IF EXISTS fk_tb_boards_created_by_tb_users;
ALTER TABLE document_utilization.tb_chat_sessions DROP CONSTRAINT IF EXISTS fk_tb_chat_sessions_user_id_tb_users;
ALTER TABLE document_utilization.tb_departments DROP CONSTRAINT IF EXISTS fk_tb_departments_head_user_id_tb_users;
ALTER TABLE document_utilization.tb_document_access DROP CONSTRAINT IF EXISTS fk_tb_document_access_user_id_tb_users;
ALTER TABLE document_utilization.tb_documents DROP CONSTRAINT IF EXISTS fk_tb_documents_uploaded_by_tb_users;
ALTER TABLE document_utilization.tb_documents_v2 DROP CONSTRAINT IF EXISTS fk_tb_documents_v2_generated_by_user_id_tb_users;
ALTER TABLE document_utilization.tb_documents_v2_templates DROP CONSTRAINT IF EXISTS fk_tb_documents_v2_templates_created_by_user_id_tb_users;
ALTER TABLE document_utilization.tb_folders DROP CONSTRAINT IF EXISTS fk_tb_folders_created_by_tb_users;
ALTER TABLE document_utilization.tb_generated_reports_archive DROP CONSTRAINT IF EXISTS fk_tb_generated_reports_generated_by_tb_users;
ALTER TABLE document_utilization.tb_project_members DROP CONSTRAINT IF EXISTS fk_tb_project_members_user_id_tb_users;
ALTER TABLE document_utilization.tb_projects DROP CONSTRAINT IF EXISTS fk_tb_projects_created_by_tb_users;
ALTER TABLE document_utilization.tb_report_templates DROP CONSTRAINT IF EXISTS fk_tb_report_templates_created_by_tb_users;
ALTER TABLE document_utilization.tb_search_history DROP CONSTRAINT IF EXISTS fk_tb_search_history_user_id_tb_users;
ALTER TABLE document_utilization.tb_search_scopes DROP CONSTRAINT IF EXISTS fk_tb_search_scopes_created_by_tb_users;

-- ====================================================================
-- 3-2. tb_users 테이블 → tb_users_legacy_20260518 RENAME (7일 read-only 유예)
-- ====================================================================
ALTER TABLE document_utilization.tb_users RENAME TO tb_users_legacy_20260518;

-- 관련 인덱스/제약도 자동 RENAME 됨 (PostgreSQL 기본 동작).
-- UNIQUE 제약 uq_tb_users_org_username / uq_tb_users_org_email 도 자동으로 RENAME됨.

COMMENT ON TABLE document_utilization.tb_users_legacy_20260518 IS
  '트랙 #98 — DocUtil tb_users 통합 (2026-05-18) 직전 보관. AIAgentManagement.Users 가 단일 SOT. 7일 후 DROP 예정.';

-- ====================================================================
-- 3-3. tb_users VIEW 생성 — AgentHub.Users 의 alias
-- ====================================================================
-- DocUtil ORM (SQLAlchemy 2 async) 이 기대하는 컬럼 명세:
--   id (uuid PK) ← AgentHub.Users.OriginalDocutilUuid
--   organization_id (uuid NOT NULL) ← AgentHub.Users.OrganizationId
--   department_id (uuid NULL) ← DocUtil tb_departments.id 매핑 (현재 미매핑, NULL)
--   username (varchar) ← AgentHub.Users.FullName (한글명 우선)
--   email (varchar) ← AgentHub.Users.Email
--   password_hash (varchar) ← AgentHub.Users.PasswordHash
--   role (varchar) ← AgentHub.Users.UserRoles.Role.RoleName (최우선 1개)
--   status (varchar) ← AgentHub.Users.Status (Active/Pending → active/pending 소문자 정규화)
--   failed_login_count (int) ← AgentHub.Users.FailedLoginCount
--   locked_until (timestamptz) ← AgentHub.Users.LockedUntil
--   last_login_at (timestamptz) ← AgentHub.Users.LastLoginAt
--   language (varchar) ← AgentHub.Users.Language
--   password_reset_token (varchar) ← AgentHub.Users.PasswordResetToken
--   password_reset_expires_at (timestamptz) ← AgentHub.Users.PasswordResetTokenExpiry
--   ins_dt (timestamptz) ← AgentHub.Users.CreatedAt
--   ins_user (uuid NULL) ← 항상 NULL (감사 컬럼 — DocUtil 만의 개념)
--   ins_ip (varchar NULL) ← 항상 NULL
--   upd_dt (timestamptz) ← AgentHub.Users.UpdatedAt
--   upd_user (uuid NULL) ← 항상 NULL
--   upd_ip (varchar NULL) ← 항상 NULL
--
-- WHERE: IsDeleted = false AND OriginalDocutilUuid IS NOT NULL
--   (DocUtil 매핑이 없는 사용자는 DocUtil 에 노출 안 함)

CREATE OR REPLACE VIEW document_utilization.tb_users AS
SELECT
  u."OriginalDocutilUuid" AS id,
  u."OrganizationId" AS organization_id,
  NULL::uuid AS department_id,  -- DocUtil tb_departments 매핑은 별도 트랙 (사용자가 세부 데이터 정리)
  u."FullName" AS username,
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
  '트랙 #98 (2026-05-18) — AIAgentManagement.Users 의 DocUtil 호환 VIEW. INSERT/UPDATE/DELETE 는 INSTEAD OF trigger 가 자동 위임.';

-- ====================================================================
-- 3-4. INSTEAD OF INSERT TRIGGER
--   DocUtil ORM 의 새 사용자 INSERT 를 AgentHub.Users 에 위임.
--   - id (uuid) 가 NEW 에 있으면 OriginalDocutilUuid 로 채움 (DocUtil 이 미리 uuid 생성)
--   - 없으면 gen_random_uuid() 로 생성
--   - role 은 LOWER(NEW.role) 을 RoleName 매칭 (super_admin / admin / member / viewer)
--     → AgentHub Roles 에 같은 이름 행이 없으면 'User' role 로 fallback
-- ====================================================================
CREATE OR REPLACE FUNCTION document_utilization.tb_users_insert_fn()
RETURNS TRIGGER AS $$
DECLARE
  new_uuid UUID;
  new_user_id INT;
  matched_role_id INT;
BEGIN
  -- 1) UUID 결정
  new_uuid := COALESCE(NEW.id, gen_random_uuid());

  -- 2) 매칭되는 Role 찾기 (대소문자 무시)
  SELECT "RoleId" INTO matched_role_id
  FROM "AIAgentManagement"."Roles"
  WHERE LOWER("RoleName") = LOWER(COALESCE(NEW.role, 'member'))
  LIMIT 1;

  IF matched_role_id IS NULL THEN
    -- fallback: 'User' role (시드에 항상 존재)
    SELECT "RoleId" INTO matched_role_id
    FROM "AIAgentManagement"."Roles" WHERE "RoleName" = 'User' LIMIT 1;
  END IF;

  -- 3) AgentHub.Users INSERT
  INSERT INTO "AIAgentManagement"."Users"
    ("Email", "PasswordHash", "FullName",
     "OrganizationId", "Language", "FailedLoginCount", "LockedUntil",
     "Status", "LastLoginAt", "OriginalDocutilUuid",
     "PasswordResetToken", "PasswordResetTokenExpiry",
     "IsEmailVerified", "IsDeleted", "IsTwoFactorEnabled",
     "CreatedAt", "UpdatedAt")
  VALUES
    (NEW.email, NEW.password_hash, COALESCE(NEW.username, NEW.email),
     COALESCE(NEW.organization_id, '00000000-0000-4000-a000-000000000001'::uuid),
     COALESCE(NEW.language, 'ko'),
     COALESCE(NEW.failed_login_count, 0),
     NEW.locked_until,
     INITCAP(COALESCE(NEW.status, 'active')),  -- 'active' → 'Active'
     NEW.last_login_at, new_uuid,
     NEW.password_reset_token, NEW.password_reset_expires_at,
     FALSE, FALSE, FALSE,
     COALESCE(NEW.ins_dt, NOW() AT TIME ZONE 'UTC'),
     COALESCE(NEW.upd_dt, NOW() AT TIME ZONE 'UTC'))
  RETURNING "UserId" INTO new_user_id;

  -- 4) UserRoles 행 추가
  INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt")
  VALUES (new_user_id, matched_role_id, NOW() AT TIME ZONE 'UTC');

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tb_users_instead_insert
INSTEAD OF INSERT ON document_utilization.tb_users
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_users_insert_fn();

-- ====================================================================
-- 3-5. INSTEAD OF UPDATE TRIGGER
--   DocUtil 의 사용자 갱신을 AgentHub.Users 로 위임.
--   - role 변경 시 UserRoles 행 교체 (DELETE + INSERT)
-- ====================================================================
CREATE OR REPLACE FUNCTION document_utilization.tb_users_update_fn()
RETURNS TRIGGER AS $$
DECLARE
  matched_role_id INT;
  matched_user_id INT;
BEGIN
  -- 1) OriginalDocutilUuid 로 AgentHub.Users 찾기
  SELECT "UserId" INTO matched_user_id
  FROM "AIAgentManagement"."Users"
  WHERE "OriginalDocutilUuid" = OLD.id
  LIMIT 1;

  IF matched_user_id IS NULL THEN
    RAISE EXCEPTION 'tb_users UPDATE: AgentHub.Users 에 OriginalDocutilUuid=% 없음', OLD.id;
  END IF;

  -- 2) AgentHub.Users 갱신
  UPDATE "AIAgentManagement"."Users"
  SET
    "Email" = COALESCE(NEW.email, "Email"),
    "PasswordHash" = COALESCE(NEW.password_hash, "PasswordHash"),
    "FullName" = COALESCE(NEW.username, "FullName"),
    "OrganizationId" = COALESCE(NEW.organization_id, "OrganizationId"),
    "Language" = COALESCE(NEW.language, "Language"),
    "FailedLoginCount" = COALESCE(NEW.failed_login_count, "FailedLoginCount"),
    "LockedUntil" = NEW.locked_until,
    "Status" = INITCAP(COALESCE(NEW.status, "Status")),
    "LastLoginAt" = COALESCE(NEW.last_login_at, "LastLoginAt"),
    "PasswordResetToken" = NEW.password_reset_token,
    "PasswordResetTokenExpiry" = NEW.password_reset_expires_at,
    "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
  WHERE "UserId" = matched_user_id;

  -- 3) role 이 변경되었으면 UserRoles 도 교체
  IF NEW.role IS DISTINCT FROM OLD.role THEN
    SELECT "RoleId" INTO matched_role_id
    FROM "AIAgentManagement"."Roles"
    WHERE LOWER("RoleName") = LOWER(NEW.role)
    LIMIT 1;

    IF matched_role_id IS NULL THEN
      SELECT "RoleId" INTO matched_role_id
      FROM "AIAgentManagement"."Roles" WHERE "RoleName" = 'User' LIMIT 1;
    END IF;

    DELETE FROM "AIAgentManagement"."UserRoles" WHERE "UserId" = matched_user_id;
    INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt")
    VALUES (matched_user_id, matched_role_id, NOW() AT TIME ZONE 'UTC');
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tb_users_instead_update
INSTEAD OF UPDATE ON document_utilization.tb_users
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_users_update_fn();

-- ====================================================================
-- 3-6. INSTEAD OF DELETE TRIGGER
--   DocUtil 의 사용자 DELETE 를 AgentHub.Users 의 soft delete (IsDeleted=true) 로 위임.
-- ====================================================================
CREATE OR REPLACE FUNCTION document_utilization.tb_users_delete_fn()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE "AIAgentManagement"."Users"
  SET "IsDeleted" = TRUE, "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
  WHERE "OriginalDocutilUuid" = OLD.id;

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tb_users_instead_delete
INSTEAD OF DELETE ON document_utilization.tb_users
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_users_delete_fn();

-- ====================================================================
-- 3-7. 검증 (view 행수 + trigger 정의 + legacy 보존)
-- ====================================================================
DO $$
DECLARE
  view_count INT;
  legacy_count INT;
  trigger_count INT;
BEGIN
  -- view 가 ORM 이 기대하는 행수 (132) 와 일치하는지
  SELECT COUNT(*) INTO view_count FROM document_utilization.tb_users;
  SELECT COUNT(*) INTO legacy_count FROM document_utilization.tb_users_legacy_20260518;
  SELECT COUNT(*) INTO trigger_count
  FROM information_schema.triggers
  WHERE event_object_schema = 'document_utilization'
    AND event_object_table = 'tb_users'
    AND trigger_name IN ('tb_users_instead_insert', 'tb_users_instead_update', 'tb_users_instead_delete');

  IF trigger_count <> 3 THEN
    RAISE EXCEPTION 'Phase 3 검증 실패: trigger 수 % (예상: 3)', trigger_count;
  END IF;

  IF view_count = 0 THEN
    RAISE EXCEPTION 'Phase 3 검증 실패: tb_users VIEW 행수 0 — alias 매핑 결함 의심';
  END IF;

  RAISE NOTICE 'Phase 3 OK — VIEW rows=%, legacy table rows=%, triggers=%',
    view_count, legacy_count, trigger_count;
END $$;

COMMIT;
