-- Extended skills seed data for idino_career
-- Adds more technical, domain, and soft skills
-- Then links skills to students based on department relevance

SET search_path TO idino_career, public;

-- ================================================================
-- 1. ADD MORE SKILLS
-- ================================================================

-- Technical Skills (Development)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK16', 'TypeScript', 'technical', 'Y', 'system', NOW()),
    ('SK17', 'Node.js', 'technical', 'Y', 'system', NOW()),
    ('SK18', 'Spring Boot', 'technical', 'Y', 'system', NOW()),
    ('SK19', 'Django', 'technical', 'Y', 'system', NOW()),
    ('SK20', 'Vue.js', 'technical', 'Y', 'system', NOW()),
    ('SK21', 'Angular', 'technical', 'Y', 'system', NOW()),
    ('SK22', 'Docker', 'technical', 'Y', 'system', NOW()),
    ('SK23', 'Kubernetes', 'technical', 'Y', 'system', NOW()),
    ('SK24', 'AWS', 'technical', 'Y', 'system', NOW()),
    ('SK25', 'Git', 'technical', 'Y', 'system', NOW()),
    ('SK26', 'Linux', 'technical', 'Y', 'system', NOW()),
    ('SK27', 'MongoDB', 'technical', 'Y', 'system', NOW()),
    ('SK28', 'Redis', 'technical', 'Y', 'system', NOW()),
    ('SK29', 'GraphQL', 'technical', 'Y', 'system', NOW()),
    ('SK30', 'REST API', 'technical', 'Y', 'system', NOW()),
    ('SK31', 'C/C++', 'technical', 'Y', 'system', NOW()),
    ('SK32', 'Go', 'technical', 'Y', 'system', NOW()),
    ('SK33', 'Rust', 'technical', 'Y', 'system', NOW()),
    ('SK34', 'Kotlin', 'technical', 'Y', 'system', NOW()),
    ('SK35', 'Swift', 'technical', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Technical Skills (Data & AI)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK36', '딥러닝', 'technical', 'Y', 'system', NOW()),
    ('SK37', 'TensorFlow', 'technical', 'Y', 'system', NOW()),
    ('SK38', 'PyTorch', 'technical', 'Y', 'system', NOW()),
    ('SK39', 'Pandas', 'technical', 'Y', 'system', NOW()),
    ('SK40', 'Spark', 'technical', 'Y', 'system', NOW()),
    ('SK41', 'Tableau', 'technical', 'Y', 'system', NOW()),
    ('SK42', 'Power BI', 'technical', 'Y', 'system', NOW()),
    ('SK43', 'R', 'technical', 'Y', 'system', NOW()),
    ('SK44', 'SAS', 'technical', 'Y', 'system', NOW()),
    ('SK45', 'Excel VBA', 'technical', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Domain Skills (Business & Management)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK46', '재무분석', 'domain', 'Y', 'system', NOW()),
    ('SK47', '마케팅', 'domain', 'Y', 'system', NOW()),
    ('SK48', '회계', 'domain', 'Y', 'system', NOW()),
    ('SK49', '인사관리', 'domain', 'Y', 'system', NOW()),
    ('SK50', '경영전략', 'domain', 'Y', 'system', NOW()),
    ('SK51', '무역실무', 'domain', 'Y', 'system', NOW()),
    ('SK52', '물류관리', 'domain', 'Y', 'system', NOW()),
    ('SK53', '세무', 'domain', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Domain Skills (Engineering)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK54', 'CAD', 'domain', 'Y', 'system', NOW()),
    ('SK55', 'CATIA', 'domain', 'Y', 'system', NOW()),
    ('SK56', 'SolidWorks', 'domain', 'Y', 'system', NOW()),
    ('SK57', 'AutoCAD', 'domain', 'Y', 'system', NOW()),
    ('SK58', 'MATLAB', 'domain', 'Y', 'system', NOW()),
    ('SK59', '전자회로설계', 'domain', 'Y', 'system', NOW()),
    ('SK60', 'PLC', 'domain', 'Y', 'system', NOW()),
    ('SK61', '임베디드', 'domain', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Domain Skills (Healthcare & Science)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK62', '간호실무', 'domain', 'Y', 'system', NOW()),
    ('SK63', '임상병리', 'domain', 'Y', 'system', NOW()),
    ('SK64', '약학', 'domain', 'Y', 'system', NOW()),
    ('SK65', '생명공학', 'domain', 'Y', 'system', NOW()),
    ('SK66', '화학분석', 'domain', 'Y', 'system', NOW()),
    ('SK67', '환경분석', 'domain', 'Y', 'system', NOW()),
    ('SK68', '식품안전', 'domain', 'Y', 'system', NOW()),
    ('SK69', '품질관리', 'domain', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Domain Skills (Design & Media)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK70', 'Photoshop', 'domain', 'Y', 'system', NOW()),
    ('SK71', 'Illustrator', 'domain', 'Y', 'system', NOW()),
    ('SK72', 'Premiere Pro', 'domain', 'Y', 'system', NOW()),
    ('SK73', 'After Effects', 'domain', 'Y', 'system', NOW()),
    ('SK74', 'Figma', 'domain', 'Y', 'system', NOW()),
    ('SK75', 'UI/UX디자인', 'domain', 'Y', 'system', NOW()),
    ('SK76', '3D 모델링', 'domain', 'Y', 'system', NOW()),
    ('SK77', '영상편집', 'domain', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Domain Skills (Languages & Communication)
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK78', '일본어', 'domain', 'Y', 'system', NOW()),
    ('SK79', '중국어', 'domain', 'Y', 'system', NOW()),
    ('SK80', '스페인어', 'domain', 'Y', 'system', NOW()),
    ('SK81', '프랑스어', 'domain', 'Y', 'system', NOW()),
    ('SK82', '통번역', 'domain', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- Additional Soft Skills
INSERT INTO tb_skill (skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
    ('SK83', '창의적사고', 'soft', 'Y', 'system', NOW()),
    ('SK84', '비판적사고', 'soft', 'Y', 'system', NOW()),
    ('SK85', '협상력', 'soft', 'Y', 'system', NOW()),
    ('SK86', '글쓰기', 'soft', 'Y', 'system', NOW()),
    ('SK87', '시간관리', 'soft', 'Y', 'system', NOW()),
    ('SK88', '스트레스관리', 'soft', 'Y', 'system', NOW()),
    ('SK89', '기획력', 'soft', 'Y', 'system', NOW()),
    ('SK90', '분석력', 'soft', 'Y', 'system', NOW())
) AS t(skill_cd, skill_nm, category, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill WHERE skill_cd = t.skill_cd);

-- ================================================================
-- 2. CREATE STUDENT-SKILL LINKS BASED ON DEPARTMENT
-- ================================================================

-- Create a temporary table for department-skill mapping
CREATE TEMPORARY TABLE IF NOT EXISTS temp_dept_skills (
    dept_pattern VARCHAR(100),
    skill_codes TEXT[]
);

TRUNCATE temp_dept_skills;

INSERT INTO temp_dept_skills (dept_pattern, skill_codes) VALUES
-- Computer Science / IT departments
('컴퓨터', ARRAY['SK01','SK02','SK03','SK04','SK05','SK16','SK17','SK22','SK25','SK26','SK30']),
('소프트웨어', ARRAY['SK01','SK02','SK04','SK16','SK17','SK18','SK22','SK25','SK30']),
('AI', ARRAY['SK01','SK06','SK07','SK36','SK37','SK38','SK39']),
('데이터', ARRAY['SK01','SK03','SK07','SK39','SK40','SK41','SK42']),
('정보', ARRAY['SK01','SK03','SK04','SK25','SK26','SK30']),
('전자', ARRAY['SK31','SK58','SK59','SK60','SK61']),
('기계', ARRAY['SK54','SK55','SK56','SK57','SK58']),
('산업공학', ARRAY['SK03','SK07','SK45','SK69']),
('로봇', ARRAY['SK01','SK31','SK58','SK60','SK61']),
('반도체', ARRAY['SK31','SK59','SK61']),

-- Business / Economics departments
('경영', ARRAY['SK45','SK46','SK47','SK48','SK50','SK89','SK90']),
('경제', ARRAY['SK03','SK45','SK46','SK48','SK90']),
('회계', ARRAY['SK45','SK48','SK53']),
('무역', ARRAY['SK13','SK51','SK52','SK85']),
('물류', ARRAY['SK52','SK45']),
('마케팅', ARRAY['SK47','SK41','SK42','SK89']),
('금융', ARRAY['SK03','SK45','SK46','SK48']),
('세무', ARRAY['SK45','SK48','SK53']),

-- Healthcare / Medical departments
('간호', ARRAY['SK62','SK09','SK11']),
('의학', ARRAY['SK62','SK63']),
('임상', ARRAY['SK63','SK69']),
('약학', ARRAY['SK64','SK66']),
('치위생', ARRAY['SK62','SK69']),
('물리치료', ARRAY['SK62']),
('작업치료', ARRAY['SK62']),
('방사선', ARRAY['SK62','SK63']),
('치기공', ARRAY['SK62']),

-- Science departments
('화학', ARRAY['SK66','SK67','SK65']),
('생명', ARRAY['SK65','SK66']),
('바이오', ARRAY['SK65','SK66','SK01']),
('환경', ARRAY['SK67','SK66']),
('식품', ARRAY['SK68','SK66','SK69']),

-- Design / Media departments
('디자인', ARRAY['SK70','SK71','SK74','SK75','SK76']),
('미디어', ARRAY['SK70','SK72','SK73','SK77']),
('시각', ARRAY['SK70','SK71','SK74']),
('영상', ARRAY['SK72','SK73','SK77']),
('애니메이션', ARRAY['SK70','SK73','SK76']),
('게임', ARRAY['SK01','SK04','SK31','SK76']),
('방송', ARRAY['SK72','SK73','SK77']),

-- Language departments
('영어', ARRAY['SK13','SK82']),
('일본', ARRAY['SK78','SK82']),
('중국', ARRAY['SK79','SK82']),
('스페인', ARRAY['SK80','SK82']),
('프랑스', ARRAY['SK81','SK82']),
('통역', ARRAY['SK13','SK82']),
('번역', ARRAY['SK13','SK82','SK86']),
('국제', ARRAY['SK13','SK51','SK82']),

-- Social Science / Humanities
('사회', ARRAY['SK09','SK86','SK89','SK90']),
('행정', ARRAY['SK45','SK86','SK89']),
('법학', ARRAY['SK86','SK84','SK85']),
('심리', ARRAY['SK84','SK90']),
('교육', ARRAY['SK09','SK14','SK86']),
('문학', ARRAY['SK86','SK84']),

-- Architecture / Construction
('건축', ARRAY['SK54','SK57']),
('토목', ARRAY['SK54','SK57']),
('건설', ARRAY['SK54','SK57']),

-- Common patterns (will be added as additional skills)
('학과', ARRAY['SK09','SK10','SK11']),  -- Default soft skills
('학부', ARRAY['SK09','SK10','SK11']);  -- Default soft skills

-- Insert student-skill links for students without skills
-- Each student gets skills based on their department
WITH students_without_skills AS (
    SELECT s.student_id, d.department_nm
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    LEFT JOIN tb_student_skill ss ON s.student_id = ss.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    AND ss.student_skill_id IS NULL
),
matched_skills AS (
    SELECT
        sws.student_id,
        sws.department_nm,
        unnest(tds.skill_codes) as skill_cd
    FROM students_without_skills sws
    JOIN temp_dept_skills tds ON sws.department_nm LIKE '%' || tds.dept_pattern || '%'
)
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT DISTINCT
    gen_random_uuid(),
    ms.student_id,
    ms.skill_cd,
    CASE
        WHEN random() < 0.2 THEN 4  -- Expert
        WHEN random() < 0.5 THEN 3  -- Advanced
        WHEN random() < 0.8 THEN 2  -- Intermediate
        ELSE 1  -- Beginner
    END,
    CASE
        WHEN random() < 0.3 THEN 5
        WHEN random() < 0.7 THEN 4
        ELSE 3
    END,
    FLOOR(random() * 5)::INT,
    CASE
        WHEN random() < 0.5 THEN 'UP'
        WHEN random() < 0.8 THEN 'STABLE'
        ELSE 'DOWN'
    END,
    'system',
    NOW()
FROM matched_skills ms
WHERE EXISTS (SELECT 1 FROM tb_skill sk WHERE sk.skill_cd = ms.skill_cd)
ON CONFLICT DO NOTHING;

-- For students still without skills (no department match), add default soft skills
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    s.student_id,
    sk.skill_cd,
    CASE
        WHEN random() < 0.2 THEN 4
        WHEN random() < 0.5 THEN 3
        WHEN random() < 0.8 THEN 2
        ELSE 1
    END,
    CASE
        WHEN random() < 0.3 THEN 5
        WHEN random() < 0.7 THEN 4
        ELSE 3
    END,
    FLOOR(random() * 5)::INT,
    CASE
        WHEN random() < 0.5 THEN 'UP'
        WHEN random() < 0.8 THEN 'STABLE'
        ELSE 'DOWN'
    END,
    'system',
    NOW()
FROM tb_student s
CROSS JOIN (
    SELECT skill_cd FROM tb_skill WHERE skill_cd IN ('SK09', 'SK10', 'SK11', 'SK14', 'SK15')
) sk
LEFT JOIN tb_student_skill ss ON s.student_id = ss.student_id
WHERE s.admission_year IN (2023, 2024, 2025)
AND ss.student_skill_id IS NULL
ON CONFLICT DO NOTHING;

-- Clean up
DROP TABLE IF EXISTS temp_dept_skills;
