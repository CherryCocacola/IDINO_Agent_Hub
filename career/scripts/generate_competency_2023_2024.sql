-- Generate competency data for 2023/2024 students
SET search_path TO idino_career;

INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    c.competency_cd,
    CASE s.admission_year
        WHEN 2023 THEN ROUND((50 + RANDOM() * 40)::numeric, 1)
        WHEN 2024 THEN ROUND((40 + RANDOM() * 40)::numeric, 1)
    END as current_score,
    85 as target_score,
    0 as gap_score,
    CASE
        WHEN RANDOM() < 0.2 THEN 'good'
        WHEN RANDOM() < 0.5 THEN 'average'
        WHEN RANDOM() < 0.8 THEN 'improve'
        ELSE 'focus'
    END as status,
    CASE
        WHEN RANDOM() < 0.5 THEN 'up'
        WHEN RANDOM() < 0.8 THEN 'stable'
        ELSE 'down'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_competency c
WHERE s.admission_year IN (2023, 2024)
AND NOT EXISTS (
    SELECT 1 FROM tb_student_competency sc
    WHERE sc.student_id = s.student_id AND sc.competency_cd = c.competency_cd
);

-- Update gap_score
UPDATE tb_student_competency
SET gap_score = target_score - current_score
WHERE student_id IN (SELECT student_id FROM tb_student WHERE admission_year IN (2023, 2024));

-- Verify
SELECT s.admission_year, COUNT(DISTINCT sc.student_id) as with_competency
FROM tb_student s
JOIN tb_student_competency sc ON s.student_id = sc.student_id
WHERE s.admission_year IN (2023, 2024, 2025)
GROUP BY s.admission_year
ORDER BY s.admission_year;
