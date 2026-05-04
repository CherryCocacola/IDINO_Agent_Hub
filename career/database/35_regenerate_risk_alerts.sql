-- ============================================
-- IDINO Career - Risk Alert Regeneration
-- Regenerate risk alerts based on actual student grade data
-- Replaces generic "Risk Alert N" entries with meaningful alerts
-- Created: 2026-01-29
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- Step 1: Delete existing system-generated risk alerts
-- ============================================
DELETE FROM tb_risk_alert WHERE ins_user_id = 'system';

-- ============================================
-- Step 2: GPA-based alerts
-- Calculate actual average GPA per student from tb_grade
-- ============================================
WITH student_gpa AS (
    SELECT
        g.student_id,
        ROUND(AVG(g.grade_point), 2) AS avg_gpa,
        COUNT(*) AS course_count
    FROM tb_grade g
    JOIN tb_student s ON s.student_id = g.student_id
    WHERE g.grade_point IS NOT NULL
    GROUP BY g.student_id
    HAVING COUNT(*) >= 1
),
gpa_alerts AS (
    SELECT
        sg.student_id,
        sg.avg_gpa,
        CASE
            WHEN sg.avg_gpa < 2.0 THEN 'critical'
            WHEN sg.avg_gpa < 2.5 THEN 'high'
            WHEN sg.avg_gpa < 3.0 THEN 'medium'
        END AS severity,
        CASE
            WHEN sg.avg_gpa < 2.0 THEN '학점 경고: 평균 성적 미달'
            WHEN sg.avg_gpa < 2.5 THEN '학점 주의: 성적 부진'
            WHEN sg.avg_gpa < 3.0 THEN '학점 관리 필요'
        END AS title,
        CASE
            WHEN sg.avg_gpa < 2.0 THEN '현재 GPA ' || sg.avg_gpa || '로 학사 경고 기준(2.0) 미만입니다. 학업 상담이 필요합니다.'
            WHEN sg.avg_gpa < 2.5 THEN '현재 GPA ' || sg.avg_gpa || '로 학업 부진 기준(2.5) 미만입니다.'
            WHEN sg.avg_gpa < 3.0 THEN '현재 GPA ' || sg.avg_gpa || '입니다. 성적 향상을 위한 노력이 필요합니다.'
        END AS description,
        CASE
            WHEN sg.avg_gpa < 2.0 THEN 2.0
            WHEN sg.avg_gpa < 2.5 THEN 2.5
            WHEN sg.avg_gpa < 3.0 THEN 3.0
        END AS threshold
    FROM student_gpa sg
    WHERE sg.avg_gpa < 3.0
    ORDER BY sg.avg_gpa ASC
    LIMIT 250
)
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity, title, description,
    trigger_value, threshold_value, related_entity_type, related_entity_id,
    status, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ga.student_id,
    'gpa_drop',
    ga.severity,
    ga.title,
    ga.description,
    ga.avg_gpa,
    ga.threshold,
    'academic',
    ga.student_id,
    'active',
    'RISK_REGEN',
    NOW()
FROM gpa_alerts ga;

-- ============================================
-- Step 3: Credits-based alerts
-- Compare earned credits vs expected by grade level
-- Expected: 1학년=30, 2학년=60, 3학년=90, 4학년=120
-- ============================================
WITH student_credits AS (
    SELECT
        s.student_id,
        s.current_grade,
        COALESCE(
            (SELECT SUM(gs.earned_credits) FROM tb_grade_summary gs WHERE gs.student_id = s.student_id),
            COALESCE((SELECT SUM(g.credits_earned) FROM tb_grade g WHERE g.student_id = s.student_id AND g.credits_earned IS NOT NULL), 0)
        ) AS total_credits,
        CASE s.current_grade
            WHEN 1 THEN 30
            WHEN 2 THEN 60
            WHEN 3 THEN 90
            WHEN 4 THEN 120
        END AS expected_credits
    FROM tb_student s
    WHERE s.status IN ('11', '12', '13')
),
credit_ratio AS (
    SELECT
        sc.student_id,
        sc.current_grade,
        sc.total_credits,
        sc.expected_credits,
        CASE
            WHEN sc.expected_credits > 0
            THEN ROUND((sc.total_credits::numeric / sc.expected_credits) * 100, 1)
            ELSE 100
        END AS pct
    FROM student_credits sc
),
credit_alerts AS (
    SELECT
        cr.student_id,
        cr.total_credits,
        cr.expected_credits,
        cr.pct,
        CASE
            WHEN cr.pct < 50 THEN 'critical'
            WHEN cr.pct < 70 THEN 'high'
            WHEN cr.pct < 85 THEN 'medium'
        END AS severity,
        CASE
            WHEN cr.pct < 50 THEN '이수학점 심각 부족'
            WHEN cr.pct < 70 THEN '이수학점 부족'
            WHEN cr.pct < 85 THEN '이수학점 관리 필요'
        END AS title,
        CASE
            WHEN cr.pct < 50 THEN '현재 이수학점 ' || cr.total_credits || '학점으로 ' || cr.current_grade || '학년 기대학점(' || cr.expected_credits || '학점) 대비 ' || cr.pct || '% 수준입니다. 즉각적인 학점 관리가 필요합니다.'
            WHEN cr.pct < 70 THEN '현재 이수학점 ' || cr.total_credits || '학점으로 ' || cr.current_grade || '학년 기대학점(' || cr.expected_credits || '학점) 대비 ' || cr.pct || '% 수준입니다. 추가 이수 계획을 수립하세요.'
            WHEN cr.pct < 85 THEN '현재 이수학점 ' || cr.total_credits || '학점으로 ' || cr.current_grade || '학년 기대학점(' || cr.expected_credits || '학점) 대비 ' || cr.pct || '% 수준입니다. 학점 관리에 유의하세요.'
        END AS description
    FROM credit_ratio cr
    WHERE cr.pct < 85
    ORDER BY cr.pct ASC
    LIMIT 250
)
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity, title, description,
    trigger_value, threshold_value, related_entity_type, related_entity_id,
    status, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ca.student_id,
    'credits',
    ca.severity,
    ca.title,
    ca.description,
    ca.total_credits,
    ca.expected_credits,
    'academic',
    ca.student_id,
    'active',
    'RISK_REGEN',
    NOW()
FROM credit_alerts ca;

-- ============================================
-- Step 4: Graduation risk alerts
-- For grade 3 and 4 students, check progress toward 130 credits
-- 4학년 with < 100 credits → critical
-- 3학년 with < 70 credits → high
-- ============================================
WITH graduation_candidates AS (
    SELECT
        s.student_id,
        s.current_grade,
        COALESCE(SUM(g.credits_earned), 0) AS total_credits
    FROM tb_student s
    LEFT JOIN tb_grade g ON g.student_id = s.student_id AND g.credits_earned IS NOT NULL
    WHERE s.current_grade IN (3, 4)
      AND s.status IN ('11', '12', '13')
    GROUP BY s.student_id, s.current_grade
),
graduation_alerts AS (
    SELECT
        gc.student_id,
        gc.current_grade,
        gc.total_credits,
        CASE
            WHEN gc.current_grade = 4 AND gc.total_credits < 100 THEN 'critical'
            WHEN gc.current_grade = 3 AND gc.total_credits < 70  THEN 'high'
        END AS severity,
        CASE
            WHEN gc.current_grade = 4 AND gc.total_credits < 100 THEN '졸업요건 미달 위험'
            WHEN gc.current_grade = 3 AND gc.total_credits < 70  THEN '졸업요건 관리 필요'
        END AS title,
        CASE
            WHEN gc.current_grade = 4 AND gc.total_credits < 100
                THEN '4학년 현재 ' || gc.total_credits || '학점 이수로 졸업요건(130학점) 충족이 어렵습니다. 남은 학기 동안 ' || (130 - gc.total_credits) || '학점 추가 이수가 필요합니다.'
            WHEN gc.current_grade = 3 AND gc.total_credits < 70
                THEN '3학년 현재 ' || gc.total_credits || '학점 이수로 졸업요건(130학점) 달성에 차질이 예상됩니다. 학점 이수 계획을 재수립하세요.'
        END AS description
    FROM graduation_candidates gc
    WHERE (gc.current_grade = 4 AND gc.total_credits < 100)
       OR (gc.current_grade = 3 AND gc.total_credits < 70)
    ORDER BY gc.total_credits ASC
    LIMIT 200
)
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity, title, description,
    trigger_value, threshold_value, related_entity_type, related_entity_id,
    status, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ga.student_id,
    'credits',
    ga.severity,
    ga.title,
    ga.description,
    ga.total_credits,
    CASE
        WHEN ga.current_grade = 4 THEN 100
        WHEN ga.current_grade = 3 THEN 70
    END,
    'academic',
    ga.student_id,
    'active',
    'RISK_REGEN',
    NOW()
FROM graduation_alerts ga;

-- ============================================
-- Summary: Report generated alert counts
-- ============================================
DO $$
DECLARE
    gpa_count INT;
    credit_count INT;
    graduation_count INT;
    total_count INT;
BEGIN
    SELECT COUNT(*) INTO total_count
    FROM tb_risk_alert
    WHERE ins_user_id = 'RISK_REGEN';

    SELECT COUNT(*) INTO gpa_count
    FROM tb_risk_alert
    WHERE ins_user_id = 'RISK_REGEN' AND risk_type = 'gpa_drop';

    SELECT COUNT(*) INTO credit_count
    FROM tb_risk_alert
    WHERE ins_user_id = 'RISK_REGEN' AND risk_type = 'credits';

    graduation_count := credit_count;

    RAISE NOTICE '=== Risk Alert Regeneration Complete ===';
    RAISE NOTICE 'GPA alerts (gpa_drop): % records', gpa_count;
    RAISE NOTICE 'Credit + Graduation alerts (credits): % records', credit_count;
    RAISE NOTICE 'Total new alerts: % records', total_count;
END $$;
