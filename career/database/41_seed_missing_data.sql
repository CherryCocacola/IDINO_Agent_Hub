-- ============================================
-- Seed missing data for 2021-2025 students
-- Ensures all data tables have at least 1 record per student
-- ============================================
SET search_path TO idino_career;

-- 1. Achievements
INSERT INTO tb_achievement (achievement_id, student_id, achievement_type, title, issuer, issue_date, level, score, verified, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    s.student_id,
    (ARRAY['certificate','language','award','publication'])[1 + floor(random()*4)::int],
    CASE (floor(random()*6)::int)
        WHEN 0 THEN '정보처리기사'
        WHEN 1 THEN 'TOEIC 800+'
        WHEN 2 THEN '학술대회 우수상'
        WHEN 3 THEN 'SQLD'
        WHEN 4 THEN 'ADsP'
        ELSE '교내 프로그래밍 대회 입상'
    END,
    CASE (floor(random()*4)::int)
        WHEN 0 THEN '한국산업인력공단'
        WHEN 1 THEN 'ETS'
        WHEN 2 THEN '한국데이터산업진흥원'
        ELSE '대학교'
    END,
    CURRENT_DATE - (random()*365)::int,
    CASE (floor(random()*3)::int) WHEN 0 THEN 'gold' WHEN 1 THEN 'silver' ELSE 'bronze' END,
    (700 + floor(random()*300))::text,
    'Y',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_user u ON s.student_id = u.student_id
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_achievement a WHERE a.student_id = s.student_id);

-- 2. Student Skills (5 random skills per student)
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    sub.student_id,
    sub.skill_cd,
    1 + floor(random()*4)::int,
    3 + floor(random()*3)::int,
    floor(random()*5)::int,
    (ARRAY['up','stable','down'])[1 + floor(random()*3)::int],
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM (
    SELECT s.student_id, sk.skill_cd,
           ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY random()) as rn
    FROM tb_student s
    JOIN tb_user u ON s.student_id = u.student_id
    CROSS JOIN tb_skill sk
    WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
    AND NOT EXISTS (SELECT 1 FROM tb_student_skill ss WHERE ss.student_id = s.student_id)
) sub
WHERE sub.rn <= 5;

-- 3. Risk Alerts
INSERT INTO tb_risk_alert (alert_id, student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    s.student_id,
    (ARRAY['academic','attendance','competency','career'])[1 + floor(random()*4)::int],
    (ARRAY['low','medium','high'])[1 + floor(random()*3)::int],
    CASE (floor(random()*4)::int)
        WHEN 0 THEN '학점 하락 경고'
        WHEN 1 THEN '출석률 저하'
        WHEN 2 THEN '역량 점수 미달'
        ELSE '진로 활동 부족'
    END,
    '최근 학기 지표가 기준치 이하입니다.',
    round((random()*50 + 20)::numeric, 1)::text,
    '60',
    (ARRAY['active','resolved','dismissed'])[1 + floor(random()*3)::int],
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_user u ON s.student_id = u.student_id
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_risk_alert ra WHERE ra.student_id = s.student_id);

-- 4. Activities
INSERT INTO tb_activity (activity_id, student_id, activity_type, title, description, start_date, end_date, hours, status, verified, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    s.student_id,
    (ARRAY['competition','volunteer','internship','club','seminar','project'])[1 + floor(random()*6)::int],
    CASE (floor(random()*6)::int)
        WHEN 0 THEN '프로그래밍 경진대회'
        WHEN 1 THEN '교내 봉사활동'
        WHEN 2 THEN 'IT기업 인턴십'
        WHEN 3 THEN '학술동아리 활동'
        WHEN 4 THEN 'AI 세미나 참석'
        ELSE '캡스톤 프로젝트'
    END,
    '비교과 활동 참여',
    CURRENT_DATE - (random()*180)::int,
    CURRENT_DATE - (random()*30)::int,
    10 + floor(random()*40)::int,
    'completed',
    'Y',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_user u ON s.student_id = u.student_id
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_activity a WHERE a.student_id = s.student_id);
