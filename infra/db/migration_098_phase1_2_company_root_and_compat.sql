-- 트랙 #98 Phase 1 + 2 (2026-05-18)
-- DocUtil tb_users 진정한 단일 통합 사전 준비:
--   Phase 1) AgentHub Departments 에 회사 root "아이디노(주)" 추가 + 기존 root 8개 종속화
--   Phase 2) AgentHub Users 에 DocUtil 호환 컬럼 4개 추가 + 기본값 채움
--
-- 트랜잭션 단위로 적용. 실패 시 자동 rollback.
-- DRY-RUN 검증을 위해 ROLLBACK 으로 종료하려면 마지막 COMMIT 을 ROLLBACK 으로 교체.

BEGIN;

-- ====================================================================
-- Phase 1: 회사 root 부서 추가
-- ====================================================================

-- 1-1. 회사 root row 신규 INSERT (DepartmentId 는 sequence 자동 할당)
--      트랙 #88 에서 본부 6개 (32~37) + 디자인팀(52) + QA팀(58) 이 모두 ParentDepartmentId=NULL
--      → 이 8개를 새 회사 root 의 하위로 종속화하여 단일 root 트리 완성.
INSERT INTO "AIAgentManagement"."Departments"
  ("DepartmentName", "DepartmentCode", "TenantId", "ParentDepartmentId", "Description",
   "IsActive", "CreatedAt", "UpdatedAt")
VALUES
  ('아이디노(주)', 'DEPT_COMPANY', 2, NULL,
   '회사 root — 트랙 #98 (2026-05-18). 모든 본부의 단일 부모.',
   TRUE, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC');

-- 1-2. 방금 추가한 회사 root 의 DepartmentId 캡처 (DepartmentCode UNIQUE 가정 — 없으면 ORDER BY DESC LIMIT 1)
--      이후 본부 8개를 이 ID 로 종속화.
WITH company_root AS (
  SELECT "DepartmentId" AS root_id
  FROM "AIAgentManagement"."Departments"
  WHERE "DepartmentCode" = 'DEPT_COMPANY'
)
UPDATE "AIAgentManagement"."Departments" d
SET "ParentDepartmentId" = (SELECT root_id FROM company_root),
    "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
WHERE d."ParentDepartmentId" IS NULL
  AND d."DepartmentCode" <> 'DEPT_COMPANY';

-- 1-3. 검증 (assert 처럼 사용 — 잘못되면 RAISE 로 트랜잭션 fail)
DO $$
DECLARE
  root_count INT;
  total_count INT;
  hslee_path TEXT;
BEGIN
  -- root 가 정확히 1개 ("아이디노(주)") 여야 함
  SELECT COUNT(*) INTO root_count
  FROM "AIAgentManagement"."Departments"
  WHERE "ParentDepartmentId" IS NULL;

  IF root_count <> 1 THEN
    RAISE EXCEPTION 'Phase 1 검증 실패: root 부서가 % 개 (예상: 1)', root_count;
  END IF;

  -- 전체 행수가 32개 (기존 31 + 회사 root 1)
  SELECT COUNT(*) INTO total_count FROM "AIAgentManagement"."Departments";
  IF total_count <> 32 THEN
    RAISE EXCEPTION 'Phase 1 검증 실패: 부서 총 행수 % (예상: 32)', total_count;
  END IF;

  RAISE NOTICE 'Phase 1 OK — root=1 (아이디노(주)), total=32, hslee 트리: %', hslee_path;
END $$;


-- ====================================================================
-- Phase 2: AgentHub Users 호환 컬럼 4개 추가
-- ====================================================================

-- 2-1. OrganizationId — DocUtil tb_organizations.id 와 매핑 (UUID, 단일 조직)
ALTER TABLE "AIAgentManagement"."Users"
  ADD COLUMN IF NOT EXISTS "OrganizationId" UUID
    DEFAULT '00000000-0000-4000-a000-000000000001'::uuid;

-- 2-2. Language — DocUtil tb_users.language ('ko'/'en'/'vi' 등)
ALTER TABLE "AIAgentManagement"."Users"
  ADD COLUMN IF NOT EXISTS "Language" VARCHAR(10) DEFAULT 'ko';

-- 2-3. FailedLoginCount — DocUtil tb_users.failed_login_count
ALTER TABLE "AIAgentManagement"."Users"
  ADD COLUMN IF NOT EXISTS "FailedLoginCount" INTEGER NOT NULL DEFAULT 0;

-- 2-4. LockedUntil — DocUtil tb_users.locked_until (계정 잠금 시각)
ALTER TABLE "AIAgentManagement"."Users"
  ADD COLUMN IF NOT EXISTS "LockedUntil" TIMESTAMP WITH TIME ZONE NULL;

-- 2-5. 기존 행에 default 채움 (ALTER ADD DEFAULT 가 기존 행에 안 적용되는 경우 대비)
UPDATE "AIAgentManagement"."Users"
SET "OrganizationId" = '00000000-0000-4000-a000-000000000001'::uuid
WHERE "OrganizationId" IS NULL;

UPDATE "AIAgentManagement"."Users"
SET "Language" = 'ko'
WHERE "Language" IS NULL;

-- 2-6. 검증
DO $$
DECLARE
  org_null INT;
  lang_null INT;
  user_total INT;
BEGIN
  SELECT COUNT(*) INTO user_total FROM "AIAgentManagement"."Users";
  SELECT COUNT(*) INTO org_null FROM "AIAgentManagement"."Users" WHERE "OrganizationId" IS NULL;
  SELECT COUNT(*) INTO lang_null FROM "AIAgentManagement"."Users" WHERE "Language" IS NULL;

  IF org_null > 0 OR lang_null > 0 THEN
    RAISE EXCEPTION 'Phase 2 검증 실패: OrganizationId NULL=%, Language NULL=%', org_null, lang_null;
  END IF;

  RAISE NOTICE 'Phase 2 OK — users=%, OrganizationId 100%% 채움, Language 100%% 채움', user_total;
END $$;

COMMIT;
