-- ============================================
-- tb_opportunity.department_cds 가짜 학과코드 → 실제 학과코드 변환
-- Version: v1
-- 목적: DEPT001, CS, SW 등 가짜/약어 코드를 tb_department의 실제 숫자 코드로 교체
-- ============================================

SET search_path TO idino_career;

BEGIN;

-- ============================================
-- 1. 개별 코드 치환 (array_replace)
--    각 가짜 코드를 실제 department_cd로 1:1 변환
-- ============================================

-- DEPT001 → 1160 (컴퓨터응용과학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT001', '1160')
WHERE 'DEPT001' = ANY(department_cds);

-- DEPT002 → 1169 (전자정보통신공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT002', '1169')
WHERE 'DEPT002' = ANY(department_cds);

-- DEPT003 → 1083 (전자공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT003', '1083')
WHERE 'DEPT003' = ANY(department_cds);

-- DEPT004 → 1034 (기계공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT004', '1034')
WHERE 'DEPT004' = ANY(department_cds);

-- DEPT005 → 1086 (화학공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT005', '1086')
WHERE 'DEPT005' = ANY(department_cds);

-- DEPT006 → 1196 (산업시스템공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT006', '1196')
WHERE 'DEPT006' = ANY(department_cds);

-- DEPT010 → 1101 (데이터정보학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT010', '1101')
WHERE 'DEPT010' = ANY(department_cds);

-- DEPT013 → 1101 (데이터정보학과 - 데이터과학 계열)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT013', '1101')
WHERE 'DEPT013' = ANY(department_cds);

-- DEPT014 → 1214 (생명공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT014', '1214')
WHERE 'DEPT014' = ANY(department_cds);

-- DEPT023 → 1127 (디자인학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT023', '1127')
WHERE 'DEPT023' = ANY(department_cds);

-- DEPT025 → 1127 (디자인학과 - 창의/디자인 계열)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DEPT025', '1127')
WHERE 'DEPT025' = ANY(department_cds);

-- CS → 1160 (컴퓨터응용과학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'CS', '1160')
WHERE 'CS' = ANY(department_cds);

-- SW → 1169 (전자정보통신공학과 - 소프트웨어 계열)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'SW', '1169')
WHERE 'SW' = ANY(department_cds);

-- EE → 1083 (전자공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'EE', '1083')
WHERE 'EE' = ANY(department_cds);

-- ME → 1034 (기계공학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'ME', '1034')
WHERE 'ME' = ANY(department_cds);

-- AI → 1160 (컴퓨터응용과학과 - AI 과정 포함)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'AI', '1160')
WHERE 'AI' = ANY(department_cds);

-- BA → 1440 (경영학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'BA', '1440')
WHERE 'BA' = ANY(department_cds);

-- DS → 1101 (데이터정보학과)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'DS', '1101')
WHERE 'DS' = ANY(department_cds);

-- STAT → 1101 (데이터정보학과 - 통계 계열)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'STAT', '1101')
WHERE 'STAT' = ANY(department_cds);

-- MSE → 1190 (나노공학과 - 재료과학/공학)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'MSE', '1190')
WHERE 'MSE' = ANY(department_cds);

-- ID → 1127 (디자인학과 - 산업디자인)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'ID', '1127')
WHERE 'ID' = ANY(department_cds);

-- IT → 1169 (전자정보통신공학과 - IT 계열)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'IT', '1169')
WHERE 'IT' = ANY(department_cds);

-- ENTR → 1440 (경영학과 - 창업/기업가정신)
UPDATE tb_opportunity
SET department_cds = array_replace(department_cds, 'ENTR', '1440')
WHERE 'ENTR' = ANY(department_cds);

-- ============================================
-- 2. 'ALL' 코드 → 주요 학과 전체 배열로 교체
--    'ALL'이 포함된 행은 전 학과 대상이므로
--    대표 학과 코드 목록으로 대체한다.
-- ============================================

UPDATE tb_opportunity
SET department_cds = '{1160,1169,1083,1034,1086,1196,1101,1214,1440,1127,1144,1289,1012,1079}'::text[]
WHERE 'ALL' = ANY(department_cds);

-- ============================================
-- 3. 배열 내 중복 제거
--    array_replace로 여러 가짜 코드가 같은 실제 코드로
--    변환되면 중복이 생길 수 있으므로 정리한다.
-- ============================================

UPDATE tb_opportunity
SET department_cds = (
    SELECT ARRAY(
        SELECT DISTINCT unnest(department_cds)
        ORDER BY 1
    )
)
WHERE array_length(department_cds, 1) > 0
  AND array_length(department_cds, 1) <> (
    SELECT count(DISTINCT v)
    FROM unnest(department_cds) AS v
  );

-- ============================================
-- 4. 검증 쿼리
--    변환 후 가짜 코드(DEPT..., 영문 약어)가
--    남아있는 행이 없는지 확인한다.
-- ============================================

SELECT opportunity_id, title, department_cds
FROM tb_opportunity
WHERE department_cds::text LIKE '%DEPT%'
   OR department_cds::text ~ '[A-Z]{2,}';

COMMIT;
