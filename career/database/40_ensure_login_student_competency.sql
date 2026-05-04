-- ============================================
-- Ensure competency data exists for login test students
-- Idempotent: only inserts if data doesn't already exist
-- ============================================

SET search_path TO idino_career;

-- Ensure student 2021010001 exists in tb_student
INSERT INTO tb_student (student_id, student_nm, university_cd, department_cd, admission_year, current_grade, current_semester, email, phone, birth_date, gender, status, career_goal, ins_user_id, ins_dt)
VALUES ('2021010001', '김민준', 'UNIV001', 'DEPT001', 2021, 4, 7, 'minjun.kim@kstu.ac.kr', '010-1234-0001', '2002-03-15', 'M', 'enrolled', '백엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (student_id) DO NOTHING;

-- Ensure competency data for login student 2021010001
INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    '2021010001',
    c.competency_cd,
    CASE c.competency_cd
        WHEN 'COMP001' THEN 78.5   -- Professional Knowledge
        WHEN 'COMP002' THEN 82.3   -- Problem Solving
        WHEN 'COMP003' THEN 71.0   -- Communication & Collaboration
        WHEN 'COMP004' THEN 88.2   -- Professional Ethics
        WHEN 'COMP005' THEN 65.7   -- Global Competency
        WHEN 'COMP006' THEN 75.4   -- Self-directed Learning
        ELSE ROUND((40 + RANDOM() * 55)::numeric, 1)
    END as current_score,
    85 as target_score,
    0 as gap_score,
    CASE c.competency_cd
        WHEN 'COMP001' THEN 'good'
        WHEN 'COMP002' THEN 'good'
        WHEN 'COMP003' THEN 'average'
        WHEN 'COMP004' THEN 'excellent'
        WHEN 'COMP005' THEN 'improve'
        WHEN 'COMP006' THEN 'average'
        ELSE 'average'
    END as status,
    CASE c.competency_cd
        WHEN 'COMP001' THEN 'up'
        WHEN 'COMP002' THEN 'up'
        WHEN 'COMP003' THEN 'stable'
        WHEN 'COMP004' THEN 'up'
        WHEN 'COMP005' THEN 'up'
        WHEN 'COMP006' THEN 'stable'
        ELSE 'stable'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_competency c
WHERE NOT EXISTS (
    SELECT 1 FROM tb_student_competency sc
    WHERE sc.student_id = '2021010001' AND sc.competency_cd = c.competency_cd
);

-- Update gap_score for the inserted records
UPDATE tb_student_competency
SET gap_score = current_score - target_score
WHERE student_id = '2021010001' AND gap_score = 0;

-- Ensure cumulative summary exists for login student
INSERT INTO tb_cumulative_summary (student_id, total_credits_earned, major_credits_earned, liberal_credits_earned, cumulative_gpa, major_gpa, completion_rate, ins_user_id, ins_dt)
VALUES ('2021010001', 108, 52, 27, 3.72, 3.85, 82.5, 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (student_id) DO NOTHING;

-- Also ensure competency data for other commonly tested students (2021010002, 2021010003)
INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    c.competency_cd,
    ROUND((40 + RANDOM() * 55)::numeric, 1) as current_score,
    85 as target_score,
    0 as gap_score,
    CASE
        WHEN RANDOM() < 0.2 THEN 'excellent'
        WHEN RANDOM() < 0.4 THEN 'good'
        WHEN RANDOM() < 0.6 THEN 'average'
        WHEN RANDOM() < 0.8 THEN 'improve'
        ELSE 'focus'
    END as status,
    CASE
        WHEN RANDOM() < 0.3 THEN 'up'
        WHEN RANDOM() < 0.6 THEN 'stable'
        ELSE 'down'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_competency c
WHERE s.student_id IN ('2021010002', '2021010003', '2021010004')
AND NOT EXISTS (
    SELECT 1 FROM tb_student_competency sc
    WHERE sc.student_id = s.student_id AND sc.competency_cd = c.competency_cd
);

-- Update gap_score for newly inserted records
UPDATE tb_student_competency
SET gap_score = current_score - target_score
WHERE student_id IN ('2021010002', '2021010003', '2021010004') AND gap_score = 0;
