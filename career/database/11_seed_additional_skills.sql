-- ============================================
-- IDINO Career - Additional Skills Seed Data
-- More skills and student-skill linkages
-- Created: 2026-01-26
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Additional Skills (20개 추가)
-- ============================================

INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt) VALUES
-- Technical Skills
('SKL016', 'TypeScript', 'TypeScript', ARRAY['TS', '타입스크립트'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL017', 'React', 'React', ARRAY['리액트', 'ReactJS', 'React.js'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL018', 'Node.js', 'Node.js', ARRAY['노드', 'NodeJS'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL019', 'Docker', 'Docker', ARRAY['도커', '컨테이너'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL020', 'Kubernetes', 'Kubernetes', ARRAY['쿠버네티스', 'K8s'], 'technical', 4, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL021', 'Git', 'Git', ARRAY['깃', 'GitHub', '깃허브', 'GitLab'], 'technical', 2, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL022', 'Linux', 'Linux', ARRAY['리눅스', 'Ubuntu', '우분투'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL023', 'MongoDB', 'MongoDB', ARRAY['몽고디비', 'NoSQL'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL024', 'GraphQL', 'GraphQL', ARRAY['그래프큐엘'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL025', 'Figma', 'Figma', ARRAY['피그마'], 'technical', 2, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL026', 'Swift', 'Swift', ARRAY['스위프트', 'iOS개발'], 'technical', 4, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL027', 'Kotlin', 'Kotlin', ARRAY['코틀린', '안드로이드개발'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL028', 'Go', 'Go', ARRAY['Golang', '고랭'], 'technical', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL029', 'Rust', 'Rust', ARRAY['러스트'], 'technical', 5, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL030', 'Spark', 'Apache Spark', ARRAY['스파크', '아파치 스파크'], 'technical', 4, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

-- Soft Skills
('SKL031', '비판적사고', 'Critical Thinking', ARRAY['비평적 사고', '분석적 사고'], 'soft', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL032', '창의력', 'Creativity', ARRAY['창의성', '창조성'], 'soft', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL033', '적응력', 'Adaptability', ARRAY['유연성', '변화적응'], 'soft', 3, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL034', '시간관리', 'Time Management', ARRAY['일정관리', '자기관리'], 'soft', 2, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP),
('SKL035', '협상력', 'Negotiation', ARRAY['협상 스킬', '설득력'], 'soft', 4, 'Y', 'SEED_SCRIPT', CURRENT_TIMESTAMP)

ON CONFLICT (skill_cd) DO UPDATE SET
    skill_nm = EXCLUDED.skill_nm,
    skill_nm_en = EXCLUDED.skill_nm_en,
    synonyms = EXCLUDED.synonyms;

-- ============================================
-- 2. Additional Skill Relations
-- ============================================

INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength, ins_user_id, ins_dt) VALUES
-- TypeScript/JavaScript relations
('SKL003', 'SKL016', 'prerequisite', 0.90, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- JS -> TS
('SKL016', 'SKL017', 'complementary', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- TS + React
('SKL003', 'SKL018', 'complementary', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- JS + Node.js
('SKL017', 'SKL018', 'complementary', 0.75, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- React + Node.js

-- DevOps relations
('SKL019', 'SKL020', 'builds_on', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Docker -> K8s
('SKL022', 'SKL019', 'prerequisite', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Linux -> Docker
('SKL008', 'SKL020', 'complementary', 0.90, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Cloud + K8s

-- Database relations
('SKL004', 'SKL023', 'alternative', 0.60, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- SQL / MongoDB
('SKL004', 'SKL024', 'complementary', 0.70, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- SQL + GraphQL

-- Mobile development
('SKL003', 'SKL026', 'alternative', 0.40, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- JS / Swift
('SKL002', 'SKL027', 'builds_on', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Java -> Kotlin

-- Big Data
('SKL001', 'SKL030', 'prerequisite', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Python -> Spark
('SKL030', 'SKL007', 'complementary', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Spark + Data Analysis

-- Design
('SKL025', 'SKL009', 'complementary', 0.75, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Figma + Problem Solving

-- Soft skills
('SKL031', 'SKL009', 'complementary', 0.90, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Critical Thinking + Problem Solving
('SKL032', 'SKL031', 'complementary', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Creativity + Critical Thinking
('SKL033', 'SKL011', 'complementary', 0.75, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Adaptability + Teamwork
('SKL034', 'SKL013', 'complementary', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- Time Mgmt + PM
('SKL035', 'SKL010', 'builds_on', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP)      -- Negotiation -> Communication

ON CONFLICT DO NOTHING;

-- ============================================
-- 3. Student Skills for 2025 students
-- ============================================

-- Computer Science 2025 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,  -- 1학년이라 성장 추세
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 5, 2, 'course'),        -- Python
        ('SKL021', 2, 4, 3, 'project'),       -- Git
        ('SKL009', 2, 4, 2, 'self_assessment'),-- Problem Solving
        ('SKL034', 2, 4, 2, 'self_assessment'),-- Time Management
        ('SKL033', 2, 4, 2, 'self_assessment') -- Adaptability
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT001' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- Software Engineering 2025 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL003', 2, 5, 2, 'course'),        -- JavaScript
        ('SKL021', 2, 4, 3, 'project'),       -- Git
        ('SKL017', 1, 4, 1, 'self_assessment'),-- React (starting)
        ('SKL009', 2, 4, 2, 'self_assessment'),-- Problem Solving
        ('SKL011', 2, 4, 3, 'project')        -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT002' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- Statistics 2025 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 5, 2, 'course'),        -- Python
        ('SKL004', 2, 4, 2, 'course'),        -- SQL
        ('SKL007', 2, 5, 3, 'course'),        -- Data Analysis
        ('SKL009', 2, 4, 2, 'self_assessment'),-- Problem Solving
        ('SKL031', 2, 4, 2, 'self_assessment') -- Critical Thinking
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT013' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- Business Administration 2025 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL010', 2, 5, 3, 'self_assessment'),-- Communication
        ('SKL015', 2, 5, 3, 'course'),        -- Presentation
        ('SKL034', 2, 4, 2, 'self_assessment'),-- Time Management
        ('SKL011', 2, 4, 3, 'project'),       -- Teamwork
        ('SKL014', 2, 4, 2, 'certificate')    -- English
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT014' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- Design 2025 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL025', 2, 5, 3, 'course'),        -- Figma
        ('SKL032', 3, 5, 3, 'self_assessment'),-- Creativity
        ('SKL010', 2, 4, 2, 'self_assessment'),-- Communication
        ('SKL015', 2, 5, 3, 'course'),        -- Presentation
        ('SKL011', 2, 4, 3, 'project')        -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT025' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- Electronics 2025 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 4, 2, 'course'),        -- Python
        ('SKL009', 2, 4, 2, 'self_assessment'),-- Problem Solving
        ('SKL022', 1, 4, 1, 'self_assessment'),-- Linux
        ('SKL011', 2, 4, 2, 'project')        -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT003' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- Other departments (Industrial Eng, Psychology, Mechanical Eng, etc.)
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.5 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL009', 2, 4, 2, 'self_assessment'),-- Problem Solving
        ('SKL010', 2, 4, 2, 'self_assessment'),-- Communication
        ('SKL011', 2, 4, 2, 'project'),       -- Teamwork
        ('SKL034', 2, 4, 2, 'self_assessment') -- Time Management
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd IN ('DEPT004', 'DEPT006', 'DEPT009', 'DEPT010', 'DEPT023') AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- ============================================
-- 4. Additional Role-Skill Mappings for new skills
-- ============================================

INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
-- Frontend Developer needs React, TypeScript
('ROLE002', 'SKL016', 4, 'critical', 95.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- TypeScript
('ROLE002', 'SKL017', 5, 'critical', 96.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- React

-- Full Stack needs Node.js, TypeScript, React
('ROLE007', 'SKL016', 4, 'important', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- TypeScript
('ROLE007', 'SKL017', 4, 'important', 94.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- React
('ROLE007', 'SKL018', 4, 'critical', 92.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Node.js

-- DevOps needs Docker, K8s, Linux
('ROLE006', 'SKL019', 5, 'critical', 96.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Docker
('ROLE006', 'SKL020', 4, 'critical', 94.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- K8s
('ROLE006', 'SKL022', 4, 'critical', 90.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Linux

-- Data Engineer needs Spark
('ROLE004', 'SKL030', 4, 'critical', 92.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Spark

-- Backend needs Git, Docker
('ROLE001', 'SKL021', 3, 'important', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Git
('ROLE001', 'SKL019', 3, 'important', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Docker

-- UX Designer needs Figma
('ROLE011', 'SKL025', 5, 'critical', 95.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Figma
('ROLE011', 'SKL032', 4, 'critical', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Creativity

-- Product Manager needs soft skills
('ROLE012', 'SKL031', 4, 'important', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Critical Thinking
('ROLE012', 'SKL033', 4, 'important', 87.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Adaptability
('ROLE012', 'SKL035', 3, 'nice_to_have', 80.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP)   -- Negotiation

ON CONFLICT DO NOTHING;

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    skill_count INT;
    relation_count INT;
    student_skill_count INT;
    role_skill_count INT;
BEGIN
    SELECT COUNT(*) INTO skill_count FROM tb_skill;
    SELECT COUNT(*) INTO relation_count FROM tb_skill_relation;
    SELECT COUNT(*) INTO student_skill_count FROM tb_student_skill;
    SELECT COUNT(*) INTO role_skill_count FROM tb_role_skill_map;

    RAISE NOTICE '=== Additional Skills Seed Data Created ===';
    RAISE NOTICE 'Total tb_skill: % records', skill_count;
    RAISE NOTICE 'Total tb_skill_relation: % records', relation_count;
    RAISE NOTICE 'Total tb_student_skill: % records', student_skill_count;
    RAISE NOTICE 'Total tb_role_skill_map: % records', role_skill_count;
END $$;
