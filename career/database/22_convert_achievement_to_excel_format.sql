-- ============================================
-- tb_achievement: Excel 형식 변환
-- Date: 2026-01-26
-- Purpose: DB 데이터를 Excel 표준 형식에 맞춤
-- 변환: project → certificate, patent → publication
-- 분리: certificate 중 어학 항목 → language
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 0. 변환 전 현황 확인
-- ============================================
DO $$
DECLARE
    project_cnt INTEGER;
    patent_cnt INTEGER;
    certificate_cnt INTEGER;
    award_cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO project_cnt FROM tb_achievement WHERE achievement_type = 'project';
    SELECT COUNT(*) INTO patent_cnt FROM tb_achievement WHERE achievement_type = 'patent';
    SELECT COUNT(*) INTO certificate_cnt FROM tb_achievement WHERE achievement_type = 'certificate';
    SELECT COUNT(*) INTO award_cnt FROM tb_achievement WHERE achievement_type = 'award';

    RAISE NOTICE '변환 전 현황:';
    RAISE NOTICE '  project: %', project_cnt;
    RAISE NOTICE '  patent: %', patent_cnt;
    RAISE NOTICE '  certificate: %', certificate_cnt;
    RAISE NOTICE '  award: %', award_cnt;
END $$;

-- ============================================
-- 1. project → certificate 변환
-- ============================================
UPDATE tb_achievement
SET achievement_type = 'certificate'
WHERE achievement_type = 'project';

-- ============================================
-- 2. patent → publication 변환
-- ============================================
UPDATE tb_achievement
SET achievement_type = 'publication'
WHERE achievement_type = 'patent';

-- ============================================
-- 3. 어학 관련 certificate → language 분리
-- 대상: TOEIC, TOEFL, OPIc, TEPS, JLPT, JPT, HSK 등
-- ============================================
UPDATE tb_achievement
SET achievement_type = 'language'
WHERE achievement_type = 'certificate'
AND (
    title ILIKE '%TOEIC%'
    OR title ILIKE '%TOEFL%'
    OR title ILIKE '%OPIC%'
    OR title ILIKE '%OPIc%'
    OR title ILIKE '%TEPS%'
    OR title ILIKE '%JLPT%'
    OR title ILIKE '%JPT%'
    OR title ILIKE '%HSK%'
    OR title ILIKE '%영어%'
    OR title ILIKE '%일본어%'
    OR title ILIKE '%중국어%'
    OR title ILIKE '%Speaking%'
    OR title ILIKE '%Writing%'
    OR issuer = 'ETS'
    OR issuer = 'ACTFL'
    OR issuer ILIKE '%언어%'
);

-- ============================================
-- 4. 변환 후 현황 확인
-- ============================================
DO $$
DECLARE
    certificate_cnt INTEGER;
    language_cnt INTEGER;
    award_cnt INTEGER;
    publication_cnt INTEGER;
    other_cnt INTEGER;
BEGIN
    SELECT COUNT(*) INTO certificate_cnt FROM tb_achievement WHERE achievement_type = 'certificate';
    SELECT COUNT(*) INTO language_cnt FROM tb_achievement WHERE achievement_type = 'language';
    SELECT COUNT(*) INTO award_cnt FROM tb_achievement WHERE achievement_type = 'award';
    SELECT COUNT(*) INTO publication_cnt FROM tb_achievement WHERE achievement_type = 'publication';
    SELECT COUNT(*) INTO other_cnt FROM tb_achievement WHERE achievement_type NOT IN ('certificate', 'language', 'award', 'publication');

    RAISE NOTICE '변환 후 현황:';
    RAISE NOTICE '  certificate: %', certificate_cnt;
    RAISE NOTICE '  language: %', language_cnt;
    RAISE NOTICE '  award: %', award_cnt;
    RAISE NOTICE '  publication: %', publication_cnt;
    RAISE NOTICE '  other: %', other_cnt;
END $$;

-- ============================================
-- 5. 최종 분포 확인 (2023-2025년 학생)
-- ============================================
SELECT
    achievement_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM tb_achievement
WHERE student_id IN (
    SELECT student_id FROM tb_student WHERE admission_year IN (2023, 2024, 2025)
)
GROUP BY achievement_type
ORDER BY count DESC;

-- ============================================
-- 6. 샘플 데이터 확인
-- ============================================
SELECT achievement_type, title, issuer, level
FROM tb_achievement
WHERE student_id IN (
    SELECT student_id FROM tb_student WHERE admission_year IN (2023, 2024, 2025)
)
ORDER BY achievement_type, random()
LIMIT 20;
