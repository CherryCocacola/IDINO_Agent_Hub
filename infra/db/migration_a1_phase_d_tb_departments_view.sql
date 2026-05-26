-- 트랙 A1 Phase D (2026-05-26) — DocUtil tb_departments 진정한 단일 통합.
-- 사용자 결정: "옵션 3 = 전체 자동 import" — DocUtil 9건 전부를 AgentHub.Departments 에
-- 매핑 (exact match) 또는 INSERT (없는 7건) 한 뒤 VIEW + INSTEAD OF TRIGGER 로 변환하여
-- AIAgentManagement.Departments 가 단일 SOT 가 되도록 한다.
-- tb_users 패턴 (트랙 #98 Phase 3, 2026-05-18) 그대로 재사용.
--
-- 전제:
--   - AIAgentManagement.Departments 에 OriginalDocutilUuid 컬럼이 이미 추가됨
--     (트랙 A1 Phase D EF migration: 20260526120000_TrackA1PhaseD_DepartmentDocutilUuid)
--   - tb_users 는 이미 VIEW 화 완료 (트랙 #98 Phase 3)
--
-- 전략 (옵션 3 = 전체 자동 import):
--   D-1a) exact name match (2건 = "교육사업팀", "사업지원팀") — OriginalDocutilUuid UPDATE
--   D-1b) 매핑 안 된 7건 INSERT — AgentHub.Departments 에 신규 행 추가
--          (DepartmentCode = 'DEPT_DU_' + uuid 앞 8자리)
--   D-1c) parent_id 2차 매핑 — DocUtil.parent_id uuid → AgentHub.ParentDepartmentId int
--   D-1d) 검증 — 9건 모두 OriginalDocutilUuid 매핑 확인
--   D-2~D-7) FK DROP + RENAME + VIEW + 3 TRIGGER (insert/update/delete)
--   D-8) 검증
--
-- 결과: AgentHub 32 + 신규 7 = 총 35건. DocUtil VIEW 는 9건만 노출 (매핑된 것만).
-- DocUtil ORM 코드 무변경 + 물리 SOT 가 AIAgentManagement.Departments 단일화.
-- 트랜잭션 단위로 적용. 실패 시 자동 rollback.

BEGIN;

-- ====================================================================
-- D-1a. exact name match (UPDATE) — 이름 일치하는 2건 처리
-- ====================================================================
UPDATE "AIAgentManagement"."Departments" ah
SET "OriginalDocutilUuid" = du.id,
    "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
FROM document_utilization.tb_departments du
WHERE ah."DepartmentName" = du.name
  AND ah."OriginalDocutilUuid" IS NULL;

-- ====================================================================
-- D-1b. 매핑 안 된 DocUtil 부서를 AgentHub 에 신규 INSERT (옵션 3)
--   - DepartmentCode = 'DEPT_DU_' + uuid 앞 8자리 (UNIQUE 충돌 회피)
--   - TenantId = AgentHub 의 단일 운영 tenant (자동 선택 = 최소 TenantId)
--   - ParentDepartmentId 는 D-1c 에서 2차 매핑
-- ====================================================================
INSERT INTO "AIAgentManagement"."Departments"
  ("DepartmentCode", "DepartmentName", "TenantId", "ParentDepartmentId",
   "IsActive", "OriginalDocutilUuid", "CreatedAt", "UpdatedAt")
SELECT
  'DEPT_DU_' || substring(replace(du.id::text, '-', ''), 1, 8),
  du.name,
  (SELECT MIN("TenantId") FROM "AIAgentManagement"."Departments"),  -- 단일 tenant
  NULL,  -- parent 는 D-1c 에서 2차 매핑
  TRUE,
  du.id,
  COALESCE(du.ins_dt, NOW() AT TIME ZONE 'UTC'),
  COALESCE(du.upd_dt, NOW() AT TIME ZONE 'UTC')
FROM document_utilization.tb_departments du
WHERE NOT EXISTS (
  SELECT 1 FROM "AIAgentManagement"."Departments" ah
  WHERE ah."OriginalDocutilUuid" = du.id
);

-- ====================================================================
-- D-1c. parent_id 2차 매핑 — DocUtil.parent_id uuid → AgentHub.ParentDepartmentId int
--   - DocUtil 의 parent_id (uuid) 가 가리키는 부서의 AgentHub DepartmentId 를 lookup
--   - 신규 INSERT 된 7건 + 기존 매핑된 2건 모두 적용
-- ====================================================================
UPDATE "AIAgentManagement"."Departments" child
SET "ParentDepartmentId" = parent_ah."DepartmentId",
    "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
FROM document_utilization.tb_departments du
JOIN "AIAgentManagement"."Departments" parent_ah
  ON parent_ah."OriginalDocutilUuid" = du.parent_id
WHERE child."OriginalDocutilUuid" = du.id
  AND du.parent_id IS NOT NULL
  AND (child."ParentDepartmentId" IS NULL OR child."ParentDepartmentId" <> parent_ah."DepartmentId");

-- ====================================================================
-- D-1d. 매핑 검증 — DocUtil 9건 모두 OriginalDocutilUuid 매핑되었는지
-- ====================================================================
DO $$
DECLARE
  mapped_count INT;
  total_du INT;
  unmapped_du INT;
BEGIN
  SELECT COUNT(*) INTO mapped_count
  FROM "AIAgentManagement"."Departments"
  WHERE "OriginalDocutilUuid" IS NOT NULL;

  SELECT COUNT(*) INTO total_du FROM document_utilization.tb_departments;

  SELECT COUNT(*) INTO unmapped_du
  FROM document_utilization.tb_departments du
  WHERE NOT EXISTS (
    SELECT 1 FROM "AIAgentManagement"."Departments" ah
    WHERE ah."OriginalDocutilUuid" = du.id
  );

  IF unmapped_du > 0 THEN
    RAISE EXCEPTION 'D-1 매핑 실패: DocUtil 중 % 건이 AgentHub 에 매핑 안 됨 (mapped=% / docutil_total=%)',
      unmapped_du, mapped_count, total_du;
  END IF;

  RAISE NOTICE 'D-1 OK — DocUtil % 건 모두 OriginalDocutilUuid 매핑 완료 (AgentHub 매핑 합계: %)',
    total_du, mapped_count;
END $$;

-- ====================================================================
-- D-2. tb_departments 를 참조하는 FK DROP (application-level 무결성으로 전환)
--
-- 주의: tb_users 는 트랙 #98 Phase 3 (2026-05-18) 에서 이미 VIEW 화 되었음 — VIEW 에는
-- FK 자체가 존재하지 않으므로 ALTER TABLE 호출 자체가 에러. 동적 SQL + 테이블 타입
-- 검사로 우회한다. tb_documents / tb_project_departments / tb_users_legacy_20260518 은
-- BASE TABLE 이므로 안전.
-- ====================================================================
DO $$
DECLARE
  fk_rec RECORD;
BEGIN
  FOR fk_rec IN
    SELECT tc.table_schema, tc.table_name, tc.constraint_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu
      ON tc.constraint_name = ccu.constraint_name
     AND tc.table_schema = ccu.table_schema
    JOIN information_schema.tables t
      ON t.table_schema = tc.table_schema
     AND t.table_name = tc.table_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_schema = 'document_utilization'
      AND ccu.table_name = 'tb_departments'
      AND t.table_type = 'BASE TABLE'  -- VIEW 는 제외 (tb_users 등)
  LOOP
    EXECUTE format(
      'ALTER TABLE %I.%I DROP CONSTRAINT IF EXISTS %I',
      fk_rec.table_schema, fk_rec.table_name, fk_rec.constraint_name
    );
    RAISE NOTICE 'D-2 DROP FK: %.% (% )', fk_rec.table_schema, fk_rec.table_name, fk_rec.constraint_name;
  END LOOP;
END $$;

-- tb_departments.head_user_id → tb_users 는 트랙 #98 Phase 3 에서 이미 DROP
-- (안전 가드 — 본 테이블도 BASE TABLE 이므로 직접 호출 가능)
ALTER TABLE document_utilization.tb_departments
  DROP CONSTRAINT IF EXISTS fk_tb_departments_head_user_id_tb_users;

-- ====================================================================
-- D-3. tb_departments 테이블 → tb_departments_legacy_20260526 RENAME
-- ====================================================================
ALTER TABLE document_utilization.tb_departments RENAME TO tb_departments_legacy_20260526;

COMMENT ON TABLE document_utilization.tb_departments_legacy_20260526 IS
  '트랙 A1 Phase D — DocUtil tb_departments 통합 (2026-05-26) 직전 보관. AIAgentManagement.Departments 가 단일 SOT. 7일 후 DROP 예정 (2026-06-02).';

-- ====================================================================
-- D-4. tb_departments VIEW 생성 — AgentHub.Departments 의 alias
-- ====================================================================
-- DocUtil ORM (SQLAlchemy 2 async, app/modules/organizations/models.py) 이 기대하는 컬럼:
--   id (uuid PK)            ← AgentHub.Departments.OriginalDocutilUuid
--   organization_id (uuid)  ← 단일 조직 hardcoded (00000000-0000-4000-a000-000000000001)
--   parent_id (uuid NULL)   ← parent.OriginalDocutilUuid (parent 매핑 lookup)
--   name (varchar 255)      ← AgentHub.Departments.DepartmentName
--   depth (int)             ← 0
--   path (varchar 1024)     ← NULL
--   ins_dt (timestamptz)    ← AgentHub.Departments.CreatedAt
--   ins_user (uuid NULL)    ← 항상 NULL (감사 컬럼 — DocUtil 만의 개념)
--   ins_ip (varchar NULL)   ← 항상 NULL
--   upd_dt (timestamptz)    ← AgentHub.Departments.UpdatedAt
--   upd_user (uuid NULL)    ← 항상 NULL
--   upd_ip (varchar NULL)   ← 항상 NULL
--
-- WHERE: IsActive = true AND OriginalDocutilUuid IS NOT NULL
--   (DocUtil 미매핑 AgentHub 부서는 VIEW 에서 숨김)

CREATE OR REPLACE VIEW document_utilization.tb_departments AS
SELECT
  ah."OriginalDocutilUuid" AS id,
  '00000000-0000-4000-a000-000000000001'::uuid AS organization_id,
  parent."OriginalDocutilUuid" AS parent_id,
  ah."DepartmentName" AS name,
  0 AS depth,
  CAST(NULL AS varchar(1024)) AS path,
  ah."CreatedAt" AS ins_dt,
  CAST(NULL AS uuid) AS ins_user,
  CAST(NULL AS varchar(45)) AS ins_ip,
  ah."UpdatedAt" AS upd_dt,
  CAST(NULL AS uuid) AS upd_user,
  CAST(NULL AS varchar(45)) AS upd_ip
FROM "AIAgentManagement"."Departments" ah
LEFT JOIN "AIAgentManagement"."Departments" parent
  ON parent."DepartmentId" = ah."ParentDepartmentId"
WHERE ah."IsActive" = TRUE
  AND ah."OriginalDocutilUuid" IS NOT NULL;

COMMENT ON VIEW document_utilization.tb_departments IS
  '트랙 A1 Phase D (2026-05-26) — AIAgentManagement.Departments 의 DocUtil 호환 VIEW. INSERT/UPDATE/DELETE 는 INSTEAD OF trigger 가 자동 위임.';

-- ====================================================================
-- D-5. INSTEAD OF INSERT TRIGGER
-- ====================================================================
CREATE OR REPLACE FUNCTION document_utilization.tb_departments_insert_fn()
RETURNS TRIGGER AS $$
DECLARE
  new_uuid UUID;
  new_dept_id INT;
  parent_dept_id INT;
  default_tenant_id INT;
BEGIN
  -- 1) UUID 결정 (DocUtil 이 미리 생성한 uuid 우선)
  new_uuid := COALESCE(NEW.id, gen_random_uuid());

  -- 2) parent_id (uuid) → ParentDepartmentId (int) 변환
  IF NEW.parent_id IS NOT NULL THEN
    SELECT "DepartmentId" INTO parent_dept_id
    FROM "AIAgentManagement"."Departments"
    WHERE "OriginalDocutilUuid" = NEW.parent_id
    LIMIT 1;
  END IF;

  -- 3) 단일 운영 tenant 식별 (Tenants 의 최소 TenantId 사용)
  SELECT "TenantId" INTO default_tenant_id
  FROM "AIAgentManagement"."Tenants"
  ORDER BY "TenantId" LIMIT 1;
  IF default_tenant_id IS NULL THEN
    default_tenant_id := 1;
  END IF;

  -- 4) AgentHub.Departments INSERT
  INSERT INTO "AIAgentManagement"."Departments"
    ("DepartmentCode", "DepartmentName", "TenantId", "ParentDepartmentId",
     "IsActive", "OriginalDocutilUuid", "CreatedAt", "UpdatedAt")
  VALUES
    ('AUTO_' || replace(new_uuid::text, '-', '_'),
     COALESCE(NEW.name, '(unnamed)'),
     default_tenant_id,
     parent_dept_id,
     TRUE,
     new_uuid,
     COALESCE(NEW.ins_dt, NOW() AT TIME ZONE 'UTC'),
     COALESCE(NEW.upd_dt, NOW() AT TIME ZONE 'UTC'))
  RETURNING "DepartmentId" INTO new_dept_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tb_departments_instead_insert
INSTEAD OF INSERT ON document_utilization.tb_departments
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_departments_insert_fn();

-- ====================================================================
-- D-6. INSTEAD OF UPDATE TRIGGER
-- ====================================================================
CREATE OR REPLACE FUNCTION document_utilization.tb_departments_update_fn()
RETURNS TRIGGER AS $$
DECLARE
  matched_dept_id INT;
  parent_dept_id INT;
BEGIN
  SELECT "DepartmentId" INTO matched_dept_id
  FROM "AIAgentManagement"."Departments"
  WHERE "OriginalDocutilUuid" = OLD.id
  LIMIT 1;

  IF matched_dept_id IS NULL THEN
    RAISE EXCEPTION 'tb_departments UPDATE: AgentHub.Departments 에 OriginalDocutilUuid=% 없음', OLD.id;
  END IF;

  IF NEW.parent_id IS NOT NULL THEN
    SELECT "DepartmentId" INTO parent_dept_id
    FROM "AIAgentManagement"."Departments"
    WHERE "OriginalDocutilUuid" = NEW.parent_id
    LIMIT 1;
  END IF;

  UPDATE "AIAgentManagement"."Departments"
  SET
    "DepartmentName" = COALESCE(NEW.name, "DepartmentName"),
    "ParentDepartmentId" = parent_dept_id,
    "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
  WHERE "DepartmentId" = matched_dept_id;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tb_departments_instead_update
INSTEAD OF UPDATE ON document_utilization.tb_departments
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_departments_update_fn();

-- ====================================================================
-- D-7. INSTEAD OF DELETE TRIGGER (soft delete via IsActive=false)
-- ====================================================================
CREATE OR REPLACE FUNCTION document_utilization.tb_departments_delete_fn()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE "AIAgentManagement"."Departments"
  SET "IsActive" = FALSE,
      "UpdatedAt" = NOW() AT TIME ZONE 'UTC'
  WHERE "OriginalDocutilUuid" = OLD.id;

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tb_departments_instead_delete
INSTEAD OF DELETE ON document_utilization.tb_departments
FOR EACH ROW EXECUTE FUNCTION document_utilization.tb_departments_delete_fn();

-- ====================================================================
-- D-8. 검증 (view 행수 + trigger 정의 + legacy 보존 + 매핑 통계)
-- ====================================================================
DO $$
DECLARE
  view_count INT;
  legacy_count INT;
  trigger_count INT;
  mapped_count INT;
  unmapped_count INT;
  agenthub_total INT;
BEGIN
  SELECT COUNT(*) INTO view_count FROM document_utilization.tb_departments;
  SELECT COUNT(*) INTO legacy_count FROM document_utilization.tb_departments_legacy_20260526;
  SELECT COUNT(*) INTO trigger_count
  FROM information_schema.triggers
  WHERE event_object_schema = 'document_utilization'
    AND event_object_table = 'tb_departments'
    AND trigger_name IN (
      'tb_departments_instead_insert',
      'tb_departments_instead_update',
      'tb_departments_instead_delete'
    );
  SELECT COUNT(*) INTO mapped_count
  FROM "AIAgentManagement"."Departments"
  WHERE "OriginalDocutilUuid" IS NOT NULL;
  SELECT COUNT(*) INTO agenthub_total
  FROM "AIAgentManagement"."Departments";
  SELECT COUNT(*) INTO unmapped_count
  FROM document_utilization.tb_departments_legacy_20260526 du
  WHERE NOT EXISTS (
    SELECT 1 FROM "AIAgentManagement"."Departments" ah
    WHERE ah."OriginalDocutilUuid" = du.id
  );

  IF trigger_count <> 3 THEN
    RAISE EXCEPTION 'Phase D 검증 실패: trigger 수 % (예상 3)', trigger_count;
  END IF;

  IF unmapped_count > 0 THEN
    RAISE EXCEPTION 'Phase D 검증 실패: DocUtil legacy % 건 미매핑 — 옵션 3 INSERT 누락', unmapped_count;
  END IF;

  RAISE NOTICE
    'Phase D OK — VIEW rows=% / legacy rows=% / triggers=% / AgentHub total=% (mapped=%)',
    view_count, legacy_count, trigger_count, agenthub_total, mapped_count;
END $$;

COMMIT;
