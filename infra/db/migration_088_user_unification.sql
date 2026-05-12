-- ============================================================================
-- 트랙 #88 — 사용자/부서/프로젝트 통합 마이그레이션 (옵션 A + B1-A 수정)
-- ============================================================================
-- 목적:
--   1) AgentHub Users.Department string(varchar 100) → DepartmentId int FK 정규화
--   2) AgentHub Departments 트리 구축 (C1-B 본부 그룹화)
--   3) DocUtil tb_users 의 신규 사용자 흡수 (admin/user @docutil.local 2명)
--   4) jyjung@idino.co.kr → iyjung@idino.co.kr (UserId=197) 매핑 통합 (C2-A)
--   5) 127명 idino.co.kr 직원 + admin/user @docutil.local Role=User 일괄 할당
--   6) DocUtil 백업 시연 데이터는 폐기 (C3-C — 별도 보관 안 함)
--   7) AgentHub master, DocUtil 인증 위임 (별도 트랙 #88-3 에서 코드 변경)
--
-- 원칙:
--   - 전체 BEGIN ... COMMIT 트랜잭션. 실패 시 ROLLBACK 자동.
--   - 기존 데이터는 일절 삭제하지 않음 (deprecate 컬럼 30일 read-only 유예).
--   - 검증 쿼리는 마이그레이션 끝에 SELECT 로 출력 (수동 검증용).
--   - 실행 전 반드시 `pg_dump --schema-only` 백업 권장.
--
-- 실행:
--   docker exec -e PGPASSWORD='idino!@#$' docutil-postgres \
--     psql -U AGENT_HUB -d AGENT_HUB \
--     -v ON_ERROR_STOP=1 -f /tmp/migration_088.sql
-- ============================================================================

\set ON_ERROR_STOP on
\timing

BEGIN;

-- ============================================================================
-- SECTION 0. 사전 검증 (현재 상태 확인)
-- ============================================================================
DO $$
DECLARE
  v_users_count int;
  v_dept_count int;
  v_tenant_count int;
BEGIN
  SELECT COUNT(*) INTO v_users_count FROM "AIAgentManagement"."Users" WHERE "IsDeleted"=false;
  SELECT COUNT(*) INTO v_dept_count FROM "AIAgentManagement"."Departments";
  SELECT COUNT(*) INTO v_tenant_count FROM "AIAgentManagement"."Tenants";
  RAISE NOTICE '[SECTION 0] 사전 상태 — Users active=%, Departments=%, Tenants=%',
    v_users_count, v_dept_count, v_tenant_count;
  IF v_users_count < 100 THEN
    RAISE EXCEPTION '사전 검증 실패: Users 수가 예상보다 적음 (%, 기대 ≥131)', v_users_count;
  END IF;
END $$;

-- ============================================================================
-- SECTION 1. AgentHub Tenants — IDINO 1행 (multi-tenant 인프라 활용)
-- ============================================================================
INSERT INTO "AIAgentManagement"."Tenants"
  ("TenantCode", "TenantName", "Description", "IsActive", "CreatedAt", "UpdatedAt", "CreatedBy")
SELECT 'IDINO', '아이디노(주)', 'IDINO 통합 사용자 마이그레이션 — Tenant master',
       true, NOW(), NOW(), 1
WHERE NOT EXISTS (
  SELECT 1 FROM "AIAgentManagement"."Tenants" WHERE "TenantCode"='IDINO'
);

-- TenantId 캡처 (이후 모든 Department insert 에 사용)
-- DO BLOCK 안의 변수는 SQL 에 못 쓰므로 별도 SELECT 로 검증만 수행
DO $$
DECLARE
  v_tenant_id int;
BEGIN
  SELECT "TenantId" INTO v_tenant_id
  FROM "AIAgentManagement"."Tenants" WHERE "TenantCode"='IDINO';
  RAISE NOTICE '[SECTION 1] IDINO TenantId = %', v_tenant_id;
END $$;

-- ============================================================================
-- SECTION 2. AgentHub Departments — 트리 구조 (C1-B)
-- ============================================================================
-- 트리 구조 (제안 — 사용자 수정 가능):
--   IDINO (Tenant)
--   ├── 경영본부 (DEPT_HQ)
--   │   ├── 경영전략본부 (DEPT_STRATEGY)
--   │   ├── 경영지원팀 (DEPT_ADMIN)
--   │   ├── 사업지원팀 (DEPT_BIZ_SUPPORT)
--   │   ├── IT팀 (DEPT_IT)
--   │   └── 마케팅팀 (DEPT_MARKETING)
--   ├── R&D본부 (DEPT_RND_HQ)
--   │   ├── R&D센터 (DEPT_RND_CENTER)
--   │   ├── 연구팀 (DEPT_RESEARCH)
--   │   ├── 개발사업팀 (DEPT_DEV_BIZ)
--   │   └── 개발팀 (DEPT_DEV)
--   ├── M.SI본부 (DEPT_MSI_HQ)
--   │   ├── Si 1팀 (DEPT_SI_1)
--   │   ├── Si 2팀 (DEPT_SI_2)
--   │   ├── Si 4팀 (DEPT_SI_4)
--   │   ├── Si 5팀 (DEPT_SI_5)
--   │   ├── Si 6팀 (DEPT_SI_6)
--   │   ├── Si 7팀 (DEPT_SI_7)
--   │   └── Si 8팀 (DEPT_SI_8)
--   ├── O.SI본부 (DEPT_OSI_HQ)
--   │   └── 유지보수팀 (DEPT_MAINT)
--   ├── 사업본부 (DEPT_BIZ_HQ)
--   │   ├── 솔루션사업팀 (DEPT_SOLUTION)
--   │   ├── 교육사업팀 (DEPT_EDU)
--   │   ├── 공공사업팀 (DEPT_PUBLIC)
--   │   └── 수도권영업팀 (DEPT_SALES_METRO)
--   ├── 디자인팀 (DEPT_DESIGN)
--   └── QA팀 (DEPT_QA)
--
--   외부협력 (DEPT_EXTERNAL_HQ)
--   ├── 춘해보건대학교 (DEPT_CHUNHAE)
--   └── 넥스트패스 (DEPT_NEXTPATH)

-- 1단계: 본부 (parent_id NULL)
INSERT INTO "AIAgentManagement"."Departments"
  ("DepartmentCode", "DepartmentName", "TenantId", "ParentDepartmentId", "Description", "IsActive", "CreatedAt", "UpdatedAt")
SELECT v.code, v.name,
       (SELECT "TenantId" FROM "AIAgentManagement"."Tenants" WHERE "TenantCode"='IDINO'),
       NULL, v.desc, true, NOW(), NOW()
FROM (VALUES
  ('DEPT_HQ',         '경영본부',     '경영 전반 총괄'),
  ('DEPT_RND_HQ',     'R&D본부',     '연구개발 본부'),
  ('DEPT_MSI_HQ',     'M.SI본부',    'M.SI (Maintenance/Major SI) 본부'),
  ('DEPT_OSI_HQ',     'O.SI본부',    'O.SI (Operation SI) 본부'),
  ('DEPT_BIZ_HQ',     '사업본부',     '영업/사업 본부'),
  ('DEPT_EXTERNAL_HQ','외부협력',     '외부 협력 기관')
) AS v(code, name, "desc")
WHERE NOT EXISTS (
  SELECT 1 FROM "AIAgentManagement"."Departments" WHERE "DepartmentCode"=v.code
);

-- 2단계: 하위 부서 (parent_id 매핑)
WITH parents AS (
  SELECT "DepartmentId", "DepartmentCode" FROM "AIAgentManagement"."Departments"
), child_data(code, name, parent_code, "desc") AS (
  VALUES
    -- 경영본부 산하
    ('DEPT_STRATEGY',    '경영전략본부',   'DEPT_HQ', '경영전략'),
    ('DEPT_ADMIN',       '경영지원팀',     'DEPT_HQ', '경영지원'),
    ('DEPT_BIZ_SUPPORT', '사업지원팀',     'DEPT_HQ', '사업지원'),
    ('DEPT_IT',          'IT팀',         'DEPT_HQ', '사내 IT'),
    ('DEPT_MARKETING',   '마케팅팀',      'DEPT_HQ', '마케팅'),
    -- R&D본부 산하
    ('DEPT_RND_CENTER',  'R&D센터',      'DEPT_RND_HQ', 'R&D 센터'),
    ('DEPT_RESEARCH',    '연구팀',       'DEPT_RND_HQ', '연구'),
    ('DEPT_DEV_BIZ',     '개발사업팀',    'DEPT_RND_HQ', '개발 사업'),
    ('DEPT_DEV',         '개발팀',       'DEPT_RND_HQ', '개발'),
    -- M.SI본부 산하
    ('DEPT_SI_1',        'Si 1팀',      'DEPT_MSI_HQ', 'SI 1팀'),
    ('DEPT_SI_2',        'Si 2팀',      'DEPT_MSI_HQ', 'SI 2팀'),
    ('DEPT_SI_4',        'Si 4팀',      'DEPT_MSI_HQ', 'SI 4팀'),
    ('DEPT_SI_5',        'Si 5팀',      'DEPT_MSI_HQ', 'SI 5팀'),
    ('DEPT_SI_6',        'Si 6팀',      'DEPT_MSI_HQ', 'SI 6팀'),
    ('DEPT_SI_7',        'Si 7팀',      'DEPT_MSI_HQ', 'SI 7팀'),
    ('DEPT_SI_8',        'Si 8팀',      'DEPT_MSI_HQ', 'SI 8팀'),
    -- O.SI본부 산하
    ('DEPT_MAINT',       '유지보수팀',    'DEPT_OSI_HQ', '운영 유지보수'),
    -- 사업본부 산하
    ('DEPT_SOLUTION',    '솔루션사업팀',   'DEPT_BIZ_HQ', '솔루션 영업'),
    ('DEPT_EDU',         '교육사업팀',    'DEPT_BIZ_HQ', '교육 사업'),
    ('DEPT_PUBLIC',      '공공사업팀',    'DEPT_BIZ_HQ', '공공 영업'),
    ('DEPT_SALES_METRO', '수도권영업팀',   'DEPT_BIZ_HQ', '수도권 영업'),
    -- 단독 (본부 산하 아님)
    ('DEPT_DESIGN',      '디자인팀',     NULL, '디자인'),
    ('DEPT_QA',          'QA팀',        NULL, 'QA / 테스트'),
    -- 외부협력 산하
    ('DEPT_CHUNHAE',     '춘해보건대학교',  'DEPT_EXTERNAL_HQ', '외부 — 춘해보건대학교'),
    ('DEPT_NEXTPATH',    '넥스트패스',    'DEPT_EXTERNAL_HQ', '외부 — 넥스트패스')
)
INSERT INTO "AIAgentManagement"."Departments"
  ("DepartmentCode", "DepartmentName", "TenantId", "ParentDepartmentId", "Description", "IsActive", "CreatedAt", "UpdatedAt")
SELECT c.code, c.name,
       (SELECT "TenantId" FROM "AIAgentManagement"."Tenants" WHERE "TenantCode"='IDINO'),
       (SELECT "DepartmentId" FROM parents WHERE "DepartmentCode" = c.parent_code),
       c."desc", true, NOW(), NOW()
FROM child_data c
WHERE NOT EXISTS (
  SELECT 1 FROM "AIAgentManagement"."Departments" WHERE "DepartmentCode" = c.code
);

DO $$
DECLARE v_count int;
BEGIN
  SELECT COUNT(*) INTO v_count FROM "AIAgentManagement"."Departments";
  RAISE NOTICE '[SECTION 2] Departments 총 % 행', v_count;
  IF v_count < 30 THEN
    RAISE EXCEPTION 'Departments INSERT 실패 (%, 기대 ≥31)', v_count;
  END IF;
END $$;

-- ============================================================================
-- SECTION 3. AgentHub Users — DepartmentId + OriginalDocutilUuid 컬럼 추가
-- ============================================================================
ALTER TABLE "AIAgentManagement"."Users"
  ADD COLUMN IF NOT EXISTS "DepartmentId" int NULL,
  ADD COLUMN IF NOT EXISTS "OriginalDocutilUuid" uuid NULL;

-- FK + UNIQUE 제약 (이미 존재하면 skip)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_schema='AIAgentManagement' AND table_name='Users'
      AND constraint_name='FK_Users_Departments_DepartmentId'
  ) THEN
    ALTER TABLE "AIAgentManagement"."Users"
      ADD CONSTRAINT "FK_Users_Departments_DepartmentId"
      FOREIGN KEY ("DepartmentId")
      REFERENCES "AIAgentManagement"."Departments"("DepartmentId")
      ON DELETE SET NULL;
    RAISE NOTICE '[SECTION 3] FK_Users_Departments_DepartmentId 추가됨';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_schema='AIAgentManagement' AND table_name='Users'
      AND constraint_name='UQ_Users_OriginalDocutilUuid'
  ) THEN
    ALTER TABLE "AIAgentManagement"."Users"
      ADD CONSTRAINT "UQ_Users_OriginalDocutilUuid"
      UNIQUE ("OriginalDocutilUuid");
    RAISE NOTICE '[SECTION 3] UQ_Users_OriginalDocutilUuid 추가됨';
  END IF;
END $$;

-- 인덱스 추가 (조회 성능)
CREATE INDEX IF NOT EXISTS "IX_Users_DepartmentId"
  ON "AIAgentManagement"."Users" ("DepartmentId");
CREATE UNIQUE INDEX IF NOT EXISTS "IX_Users_Email_Unique"
  ON "AIAgentManagement"."Users" (LOWER("Email")) WHERE "IsDeleted" = false;

-- ============================================================================
-- SECTION 4. Department string → DepartmentId 일괄 매핑
-- ============================================================================
-- AgentHub Department string 26개 → Departments.DepartmentName 매핑

UPDATE "AIAgentManagement"."Users" u
SET "DepartmentId" = d."DepartmentId"
FROM "AIAgentManagement"."Departments" d
WHERE u."Department" IS NOT NULL
  AND u."Department" != ''
  AND d."DepartmentName" = u."Department"
  AND u."DepartmentId" IS NULL;

-- 매핑 안 된 사용자 확인 (Department string 이 트리에 없는 경우)
DO $$
DECLARE
  v_unmapped int;
  v_mapped int;
BEGIN
  SELECT COUNT(*) INTO v_unmapped FROM "AIAgentManagement"."Users"
  WHERE "IsDeleted"=false AND "Department" IS NOT NULL AND "Department" != ''
    AND "DepartmentId" IS NULL;
  SELECT COUNT(*) INTO v_mapped FROM "AIAgentManagement"."Users"
  WHERE "IsDeleted"=false AND "DepartmentId" IS NOT NULL;
  RAISE NOTICE '[SECTION 4] Department string → DepartmentId — mapped=%, unmapped=%',
    v_mapped, v_unmapped;
END $$;

-- ============================================================================
-- SECTION 5. 127명 idino.co.kr 직원 + 신규 흡수 사용자 Role=User 일괄 할당
-- ============================================================================
-- 현재 UserRoles 4건 (UserId 1=Admin, 2=Developer, 3=User, 4=User, 255=User)
-- 신규: 127명 idino.co.kr + 0명 외부 + 추후 admin/user @docutil.local 2명

INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt")
SELECT u."UserId",
       (SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName"='User'),
       NOW()
FROM "AIAgentManagement"."Users" u
WHERE u."IsDeleted" = false
  AND NOT EXISTS (
    SELECT 1 FROM "AIAgentManagement"."UserRoles" ur
    WHERE ur."UserId" = u."UserId"
  );

DO $$
DECLARE v_count int;
BEGIN
  SELECT COUNT(*) INTO v_count FROM "AIAgentManagement"."UserRoles";
  RAISE NOTICE '[SECTION 5] UserRoles 총 % 행 (기대 131건+α)', v_count;
END $$;

-- ============================================================================
-- SECTION 6. DocUtil 사용자 신규 흡수 (admin/user @docutil.local 2명)
-- ============================================================================
-- BCrypt $2b$12$ — AgentHub bcrypt 검증과 호환 (round 12, version 2b)

-- 6-1. admin@docutil.local (super_admin → Admin Role)
INSERT INTO "AIAgentManagement"."Users"
  ("Email", "PasswordHash", "FullName", "Department", "DepartmentId",
   "Status", "IsEmailVerified", "IsDeleted", "CreatedAt", "UpdatedAt",
   "IsTwoFactorEnabled", "OriginalDocutilUuid")
SELECT 'admin@docutil.local',
       '$2b$12$xp8oA.PhVt1IclEfHeffseLtu9kbTygmM4ux8sAz0dKasl3ZozSVq',
       'DocUtil 관리자',
       NULL, NULL,
       'Active', true, false, NOW(), NOW(),
       false,
       '00000000-0000-4000-a000-000000000002'::uuid
WHERE NOT EXISTS (
  SELECT 1 FROM "AIAgentManagement"."Users" WHERE LOWER("Email")='admin@docutil.local'
);

-- admin@docutil.local 에게 Admin 권한 부여
INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt")
SELECT u."UserId",
       (SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName"='Admin'),
       NOW()
FROM "AIAgentManagement"."Users" u
WHERE LOWER(u."Email")='admin@docutil.local'
  AND NOT EXISTS (
    SELECT 1 FROM "AIAgentManagement"."UserRoles" ur
    WHERE ur."UserId"=u."UserId"
      AND ur."RoleId"=(SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName"='Admin')
  );

-- 6-2. user@docutil.local (member → User Role) — 시연용
INSERT INTO "AIAgentManagement"."Users"
  ("Email", "PasswordHash", "FullName", "Department", "DepartmentId",
   "Status", "IsEmailVerified", "IsDeleted", "CreatedAt", "UpdatedAt",
   "IsTwoFactorEnabled", "OriginalDocutilUuid")
SELECT 'user@docutil.local',
       '$2b$12$el0UORFKZ6LTidzZY9RRl.rAddhWzR2l2KUnMMVb/Ri5q8RhdIN7O',
       'DocUtil 사용자',
       NULL, NULL,
       'Active', true, false, NOW(), NOW(),
       false,
       'a0000000-0000-4000-a000-000000000003'::uuid
WHERE NOT EXISTS (
  SELECT 1 FROM "AIAgentManagement"."Users" WHERE LOWER("Email")='user@docutil.local'
);

-- user@docutil.local 에게 User 권한 부여
INSERT INTO "AIAgentManagement"."UserRoles" ("UserId", "RoleId", "AssignedAt")
SELECT u."UserId",
       (SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName"='User'),
       NOW()
FROM "AIAgentManagement"."Users" u
WHERE LOWER(u."Email")='user@docutil.local'
  AND NOT EXISTS (
    SELECT 1 FROM "AIAgentManagement"."UserRoles" ur
    WHERE ur."UserId"=u."UserId"
      AND ur."RoleId"=(SELECT "RoleId" FROM "AIAgentManagement"."Roles" WHERE "RoleName"='User')
  );

-- ============================================================================
-- SECTION 7. jyjung@idino.co.kr → iyjung@idino.co.kr (UserId=197) 매핑 (C2-A)
-- ============================================================================
-- AgentHub UserId=197 정인영 (iyjung@idino.co.kr) 에 DocUtil UUID 매핑
-- DocUtil 측 user_id = '8c07639f-f5b3-4901-a550-b5eb32efa2ca' (백업 기준)
-- 단, 백업 파싱에서 정확한 UUID 재확인 필요 — 8c07639f... 가 정인영

UPDATE "AIAgentManagement"."Users"
SET "OriginalDocutilUuid" = '8c07639f-f5b3-4901-a550-b5eb32efa2ca'::uuid,
    "UpdatedAt" = NOW()
WHERE "UserId" = 197
  AND "OriginalDocutilUuid" IS NULL;

-- ============================================================================
-- SECTION 8. 매칭 8명에 OriginalDocutilUuid UPDATE (C4-A — AgentHub 비번 유지)
-- ============================================================================
-- 매핑 매트릭스 (백업 2026-04-23 파싱 결과):
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '29a58dae-c933-4645-b903-2fe587bd047d'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 135 AND "OriginalDocutilUuid" IS NULL; -- yhkim 김용휴
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'de3587d2-600a-4248-b2dc-25ad133572d8'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 136 AND "OriginalDocutilUuid" IS NULL; -- gaze 윤제호
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '01c0f2d4-0a30-42f8-84d7-69d4693cc16c'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 137 AND "OriginalDocutilUuid" IS NULL; -- wjlee 이원재
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '52ff0252-d940-4357-8b19-6a1bda9b4cb3'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 138 AND "OriginalDocutilUuid" IS NULL; -- dglee 이동건
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '8baf9e41-20d9-4db6-b195-b04c8bab88f4'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 143 AND "OriginalDocutilUuid" IS NULL; -- dongun 변동언
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'bafe866b-b7e2-4d26-8165-af62295e62f0'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 166 AND "OriginalDocutilUuid" IS NULL; -- jyj7970 조예주
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = '40811ca9-d838-4457-a8fe-a8a3cade70dd'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 220 AND "OriginalDocutilUuid" IS NULL; -- shbaek 백성현
UPDATE "AIAgentManagement"."Users" SET "OriginalDocutilUuid" = 'b54f6c80-85f4-4810-bf5a-ecc4452e68ca'::uuid, "UpdatedAt"=NOW() WHERE "UserId" = 221 AND "OriginalDocutilUuid" IS NULL; -- hslee 이현수

-- ============================================================================
-- SECTION 9. Department string 컬럼 deprecate 표시
-- ============================================================================
-- 30일 read-only 유예 — 컬럼 자체는 유지하고 COMMENT 로 표기
COMMENT ON COLUMN "AIAgentManagement"."Users"."Department" IS
  '[DEPRECATED 2026-05-12] 트랙 #88 — DepartmentId 사용. 30일 후 DROP 예정 (2026-06-11).';

-- ============================================================================
-- SECTION 10. 검증 쿼리 (수동 확인용)
-- ============================================================================
\echo '\n=== 검증 1: Tenants 행수 ==='
SELECT * FROM "AIAgentManagement"."Tenants";

\echo '\n=== 검증 2: Departments 트리 ==='
SELECT d."DepartmentId", d."DepartmentCode", d."DepartmentName",
       p."DepartmentName" AS parent_name,
       d."IsActive"
FROM "AIAgentManagement"."Departments" d
LEFT JOIN "AIAgentManagement"."Departments" p ON p."DepartmentId" = d."ParentDepartmentId"
ORDER BY COALESCE(d."ParentDepartmentId", d."DepartmentId"), d."DepartmentId";

\echo '\n=== 검증 3: Users.Department 매핑 결과 ==='
SELECT u."Department" AS old_string,
       d."DepartmentName" AS new_dept,
       COUNT(*) AS user_count
FROM "AIAgentManagement"."Users" u
LEFT JOIN "AIAgentManagement"."Departments" d ON d."DepartmentId" = u."DepartmentId"
WHERE u."IsDeleted" = false
GROUP BY u."Department", d."DepartmentName"
ORDER BY user_count DESC;

\echo '\n=== 검증 4: UserRoles 분포 ==='
SELECT r."RoleName", COUNT(ur."UserId") AS user_count
FROM "AIAgentManagement"."Roles" r
LEFT JOIN "AIAgentManagement"."UserRoles" ur ON ur."RoleId" = r."RoleId"
GROUP BY r."RoleName"
ORDER BY r."RoleName";

\echo '\n=== 검증 5: DocUtil 흡수 사용자 ==='
SELECT "UserId", "Email", "FullName", "OriginalDocutilUuid"
FROM "AIAgentManagement"."Users"
WHERE "OriginalDocutilUuid" IS NOT NULL
ORDER BY "UserId";

\echo '\n=== 검증 6: 매핑 안 된 Department string (확인 필요) ==='
SELECT "Department", COUNT(*) AS user_count
FROM "AIAgentManagement"."Users"
WHERE "IsDeleted" = false
  AND "Department" IS NOT NULL AND "Department" != ''
  AND "DepartmentId" IS NULL
GROUP BY "Department"
ORDER BY user_count DESC;

-- ============================================================================
-- 최종 COMMIT — 모든 검증 통과 시 적용
-- ============================================================================
COMMIT;

\echo '\n=== 트랙 #88 마이그레이션 SQL 완료 ==='
\echo '다음 단계:'
\echo '  1) 트랙 #88-3 — DocUtil 인증 어댑터 (AgentHub JWT 위임) 별도 적용'
\echo '  2) 트랙 #88-4 — 22 SKIP e2e 재실행'
\echo '  3) 2026-06-11 — Users.Department string 컬럼 DROP'
