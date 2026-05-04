-- ============================================
-- IDINO Career - P1 Phase 7: Skills Seed Data
-- Role-Skill Map, Student Skills, Skill Relations, Gap Analysis
-- Created: 2026-01-07
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Role-Skill Mappings (12 roles 횞 5-8 skills = ~80 records)
-- ============================================

-- Clear existing data (if re-running)
DELETE FROM tb_role_skill_map WHERE ins_user_id = 'SEED_SCRIPT';

-- Backend Developer (ROLE001)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE001', 'SKL001', 4, 'critical', 92.5, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE001', 'SKL002', 4, 'critical', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Java
('ROLE001', 'SKL004', 4, 'critical', 90.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- SQL
('ROLE001', 'SKL008', 3, 'important', 95.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Cloud
('ROLE001', 'SKL009', 3, 'important', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE001', 'SKL011', 3, 'nice_to_have', 80.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);  -- Teamwork

-- Frontend Developer (ROLE002)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE002', 'SKL003', 5, 'critical', 94.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- JavaScript
('ROLE002', 'SKL001', 3, 'important', 85.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Python
('ROLE002', 'SKL009', 3, 'important', 82.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE002', 'SKL010', 4, 'important', 80.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Communication
('ROLE002', 'SKL011', 3, 'important', 78.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);     -- Teamwork

-- Data Analyst (ROLE003)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE003', 'SKL001', 4, 'critical', 95.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE003', 'SKL004', 5, 'critical', 92.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- SQL
('ROLE003', 'SKL007', 5, 'critical', 96.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Data Analysis
('ROLE003', 'SKL009', 4, 'important', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE003', 'SKL015', 3, 'important', 82.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Presentation
('ROLE003', 'SKL010', 3, 'nice_to_have', 78.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);  -- Communication

-- Data Engineer (ROLE004)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE004', 'SKL001', 5, 'critical', 94.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE004', 'SKL004', 5, 'critical', 93.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- SQL
('ROLE004', 'SKL008', 4, 'critical', 96.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Cloud
('ROLE004', 'SKL007', 4, 'important', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Data Analysis
('ROLE004', 'SKL009', 3, 'important', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);     -- Problem Solving

-- AI Engineer (ROLE005)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE005', 'SKL001', 5, 'critical', 98.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE005', 'SKL005', 5, 'critical', 97.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Machine Learning
('ROLE005', 'SKL006', 4, 'critical', 96.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Deep Learning
('ROLE005', 'SKL007', 4, 'important', 92.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Data Analysis
('ROLE005', 'SKL008', 3, 'important', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Cloud
('ROLE005', 'SKL009', 4, 'important', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE005', 'SKL014', 3, 'nice_to_have', 80.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);  -- English

-- DevOps Engineer (ROLE006)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE006', 'SKL001', 4, 'critical', 92.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE006', 'SKL008', 5, 'critical', 98.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Cloud
('ROLE006', 'SKL009', 4, 'important', 86.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE006', 'SKL011', 3, 'important', 82.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Teamwork
('ROLE006', 'SKL013', 3, 'nice_to_have', 80.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- Project Management

-- Full Stack Developer (ROLE007)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE007', 'SKL001', 4, 'critical', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE007', 'SKL003', 4, 'critical', 92.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- JavaScript
('ROLE007', 'SKL004', 4, 'critical', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- SQL
('ROLE007', 'SKL008', 3, 'important', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Cloud
('ROLE007', 'SKL009', 4, 'important', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE007', 'SKL011', 3, 'nice_to_have', 78.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);  -- Teamwork

-- Security Specialist (ROLE008)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE008', 'SKL001', 4, 'critical', 88.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Python
('ROLE008', 'SKL004', 3, 'important', 82.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- SQL
('ROLE008', 'SKL009', 5, 'critical', 92.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Problem Solving
('ROLE008', 'SKL010', 3, 'important', 78.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Communication
('ROLE008', 'SKL014', 3, 'nice_to_have', 75.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);  -- English

-- Management Consultant (ROLE009)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE009', 'SKL007', 4, 'critical', 90.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Data Analysis
('ROLE009', 'SKL009', 5, 'critical', 95.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Problem Solving
('ROLE009', 'SKL010', 5, 'critical', 92.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Communication
('ROLE009', 'SKL012', 4, 'important', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Leadership
('ROLE009', 'SKL015', 5, 'critical', 90.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Presentation
('ROLE009', 'SKL014', 4, 'important', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- English
('ROLE009', 'SKL013', 3, 'important', 82.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP);    -- Project Management

-- Marketing Specialist (ROLE010)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE010', 'SKL007', 3, 'important', 85.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Data Analysis
('ROLE010', 'SKL010', 5, 'critical', 90.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Communication
('ROLE010', 'SKL009', 4, 'important', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Problem Solving
('ROLE010', 'SKL015', 4, 'important', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Presentation
('ROLE010', 'SKL011', 3, 'important', 80.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);     -- Teamwork

-- UX Designer (ROLE011)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE011', 'SKL009', 4, 'critical', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Problem Solving
('ROLE011', 'SKL010', 4, 'critical', 85.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Communication
('ROLE011', 'SKL015', 4, 'important', 86.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Presentation
('ROLE011', 'SKL011', 4, 'important', 82.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Teamwork
('ROLE011', 'SKL003', 2, 'nice_to_have', 75.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- JavaScript

-- Product Manager (ROLE012)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt) VALUES
('ROLE012', 'SKL013', 5, 'critical', 94.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Project Management
('ROLE012', 'SKL010', 5, 'critical', 92.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Communication
('ROLE012', 'SKL009', 4, 'critical', 90.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Problem Solving
('ROLE012', 'SKL012', 4, 'important', 88.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP),     -- Leadership
('ROLE012', 'SKL007', 3, 'important', 85.0, 'growing', 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Data Analysis
('ROLE012', 'SKL015', 4, 'important', 86.0, 'stable', 'SEED_SCRIPT', CURRENT_TIMESTAMP);     -- Presentation

-- ============================================
-- 2. Skill Relations (?좎닔/蹂댁셿 愿怨?~40 records)
-- ============================================

DELETE FROM tb_skill_relation WHERE ins_user_id = 'SEED_SCRIPT';

-- Prerequisite relations (?좎닔 ?ㅽ궗)
INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength, ins_user_id, ins_dt) VALUES
-- Python is prerequisite for ML, DL, Data Analysis
('SKL001', 'SKL005', 'prerequisite', 0.95, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- Python ??ML
('SKL001', 'SKL006', 'prerequisite', 0.90, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- Python ??DL
('SKL001', 'SKL007', 'prerequisite', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- Python ??Data Analysis
-- ML is prerequisite for DL
('SKL005', 'SKL006', 'prerequisite', 0.90, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ML ??DL
-- SQL prerequisite for Data Analysis
('SKL004', 'SKL007', 'prerequisite', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- SQL ??Data Analysis

-- Builds_on relations (諛쒖쟾 愿怨?
INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength, ins_user_id, ins_dt) VALUES
('SKL001', 'SKL002', 'builds_on', 0.70, 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Python ??Java (OOP concepts)
('SKL002', 'SKL003', 'builds_on', 0.60, 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Java ??JavaScript
('SKL010', 'SKL015', 'builds_on', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Communication ??Presentation
('SKL011', 'SKL012', 'builds_on', 0.75, 'SEED_SCRIPT', CURRENT_TIMESTAMP),      -- Teamwork ??Leadership
('SKL013', 'SKL012', 'builds_on', 0.70, 'SEED_SCRIPT', CURRENT_TIMESTAMP);      -- PM ??Leadership

-- Complementary relations (蹂댁셿 愿怨?
INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength, ins_user_id, ins_dt) VALUES
-- Technical + Soft skills
('SKL001', 'SKL009', 'complementary', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Python + Problem Solving
('SKL005', 'SKL007', 'complementary', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- ML + Data Analysis
('SKL008', 'SKL001', 'complementary', 0.75, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Cloud + Python
('SKL003', 'SKL001', 'complementary', 0.70, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- JavaScript + Python
-- Soft skill complements
('SKL010', 'SKL011', 'complementary', 0.90, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Communication + Teamwork
('SKL012', 'SKL010', 'complementary', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Leadership + Communication
('SKL013', 'SKL011', 'complementary', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- PM + Teamwork
('SKL015', 'SKL010', 'complementary', 0.85, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Presentation + Communication
-- Technical complements
('SKL004', 'SKL001', 'complementary', 0.75, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- SQL + Python
('SKL002', 'SKL004', 'complementary', 0.70, 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- Java + SQL
('SKL006', 'SKL008', 'complementary', 0.80, 'SEED_SCRIPT', CURRENT_TIMESTAMP);  -- Deep Learning + Cloud

-- Alternative relations (?泥?媛??
INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength, ins_user_id, ins_dt) VALUES
('SKL001', 'SKL002', 'alternative', 0.60, 'SEED_SCRIPT', CURRENT_TIMESTAMP),    -- Python / Java (for some tasks)
('SKL002', 'SKL003', 'alternative', 0.50, 'SEED_SCRIPT', CURRENT_TIMESTAMP);    -- Java / JavaScript (for some tasks)

-- ============================================
-- 3. Student Skills (~600 records for 110 students)
-- Each student gets 5-8 skills based on their department
-- ============================================

DELETE FROM tb_student_skill WHERE ins_user_id = 'SEED_SCRIPT';

-- Computer Science students (DEPT001) - 15 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 90)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.6 THEN 'up' WHEN RANDOM() > 0.3 THEN 'stable' ELSE 'down' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 3, 5, 5, 'course'),        -- Python
        ('SKL004', 3, 4, 4, 'course'),        -- SQL
        ('SKL002', 2, 4, 3, 'course'),        -- Java
        ('SKL009', 3, 4, 4, 'self_assessment'), -- Problem Solving
        ('SKL008', 2, 4, 2, 'certificate'),  -- Cloud
        ('SKL011', 3, 4, 3, 'project')       -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT001';

-- Software Engineering students (DEPT002) - 12 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level + (RANDOM() * 1)::INT,
    skill_data.target_level,
    skill_data.evidence_count + (RANDOM() * 3)::INT,
    CURRENT_DATE - (RANDOM() * 60)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.5 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL003', 3, 5, 4, 'course'),        -- JavaScript
        ('SKL001', 3, 4, 3, 'course'),        -- Python
        ('SKL004', 2, 4, 3, 'course'),        -- SQL
        ('SKL008', 2, 5, 2, 'certificate'),  -- Cloud
        ('SKL013', 2, 4, 2, 'project'),      -- PM
        ('SKL011', 3, 4, 4, 'project')       -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT002';

-- Electronics Engineering students (DEPT003) - 10 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 120)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.7 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 4, 3, 'course'),        -- Python
        ('SKL009', 3, 4, 3, 'self_assessment'), -- Problem Solving
        ('SKL011', 3, 4, 3, 'project'),      -- Teamwork
        ('SKL010', 3, 4, 2, 'self_assessment') -- Communication
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT003';

-- Business Administration students (DEPT014) - 12 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level + (RANDOM() * 1)::INT,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 90)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL007', 2, 4, 3, 'course'),        -- Data Analysis
        ('SKL010', 3, 5, 4, 'self_assessment'), -- Communication
        ('SKL015', 3, 5, 4, 'course'),        -- Presentation
        ('SKL012', 2, 4, 2, 'self_assessment'), -- Leadership
        ('SKL013', 2, 4, 3, 'project'),      -- PM
        ('SKL014', 3, 4, 3, 'certificate'),  -- English
        ('SKL011', 3, 4, 4, 'project')       -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT014';

-- Statistics students (DEPT013) - 10 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count + (RANDOM() * 2)::INT,
    CURRENT_DATE - (RANDOM() * 60)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.5 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 3, 5, 4, 'course'),        -- Python
        ('SKL004', 3, 4, 4, 'course'),        -- SQL
        ('SKL007', 4, 5, 5, 'course'),        -- Data Analysis
        ('SKL005', 2, 4, 2, 'course'),        -- ML
        ('SKL009', 3, 4, 3, 'self_assessment') -- Problem Solving
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT013';

-- Industrial Engineering students (DEPT006) - 8 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 100)::INT,
    skill_data.verification_source,
    'stable',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 4, 2, 'course'),        -- Python
        ('SKL004', 2, 4, 2, 'course'),        -- SQL
        ('SKL007', 3, 4, 3, 'course'),        -- Data Analysis
        ('SKL009', 3, 4, 4, 'self_assessment'), -- Problem Solving
        ('SKL013', 3, 5, 3, 'project'),      -- PM
        ('SKL011', 3, 4, 3, 'project')       -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT006';

-- Design students (DEPT025) - 8 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 80)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.6 THEN 'up' ELSE 'stable' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL003', 2, 4, 2, 'course'),        -- JavaScript (for web design)
        ('SKL010', 4, 5, 4, 'self_assessment'), -- Communication
        ('SKL015', 4, 5, 5, 'course'),        -- Presentation
        ('SKL009', 3, 4, 3, 'self_assessment'), -- Problem Solving
        ('SKL011', 4, 5, 4, 'project')       -- Teamwork
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT025';

-- Psychology students (DEPT023) - 8 students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 90)::INT,
    skill_data.verification_source,
    'stable',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL007', 2, 4, 2, 'course'),        -- Data Analysis (for research)
        ('SKL010', 4, 5, 4, 'self_assessment'), -- Communication
        ('SKL009', 3, 4, 3, 'self_assessment'), -- Problem Solving
        ('SKL014', 3, 4, 3, 'certificate'),  -- English
        ('SKL015', 3, 4, 3, 'course')        -- Presentation
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT023';

-- Other departments - basic skills for remaining students
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 120)::INT,
    skill_data.verification_source,
    'stable',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL010', 3, 4, 2, 'self_assessment'), -- Communication
        ('SKL009', 2, 4, 2, 'self_assessment'), -- Problem Solving
        ('SKL011', 3, 4, 2, 'project'),      -- Teamwork
        ('SKL014', 2, 4, 2, 'certificate')   -- English
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd NOT IN ('DEPT001', 'DEPT002', 'DEPT003', 'DEPT014', 'DEPT013', 'DEPT006', 'DEPT025', 'DEPT023')
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- ============================================
-- 4. Skill Gap Analysis (~80 records)
-- ============================================

DELETE FROM tb_skill_gap_analysis WHERE ins_user_id = 'SEED_SCRIPT';

-- Generate gap analysis for students in tech-focused departments
INSERT INTO tb_skill_gap_analysis (student_id, target_role_cd, analysis_date, overall_gap_score, gap_details, top_priority_skills, recommended_actions, ins_user_id, ins_dt)
SELECT
    s.student_id,
    role_data.role_cd,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '30 days'),
    role_data.base_gap_score + (RANDOM() * 15)::DECIMAL(5,2),
    role_data.gap_details::JSONB,
    role_data.priority_skills,
    role_data.actions::JSONB,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('ROLE001', 32.5, '[{"skill_cd": "SKL001", "current": 3, "required": 4, "gap": 1}, {"skill_cd": "SKL008", "current": 2, "required": 3, "gap": 1}]',
         ARRAY['SKL001', 'SKL008'], '{"courses": ["CS401", "SW302"], "programs": ["PGM006"], "activities": ["AWS ?먭꺽利?痍⑤뱷"]}'),
        ('ROLE005', 45.0, '[{"skill_cd": "SKL005", "current": 2, "required": 5, "gap": 3}, {"skill_cd": "SKL006", "current": 1, "required": 4, "gap": 3}]',
         ARRAY['SKL005', 'SKL006', 'SKL001'], '{"courses": ["CS401", "CS402"], "programs": ["PGM002"], "activities": ["AI 寃쎌쭊???李멸?"]}'),
        ('ROLE003', 28.0, '[{"skill_cd": "SKL007", "current": 3, "required": 5, "gap": 2}, {"skill_cd": "SKL015", "current": 2, "required": 3, "gap": 1}]',
         ARRAY['SKL007', 'SKL004'], '{"courses": ["ST302", "CS402"], "programs": ["PGM003"], "activities": ["?곗씠??遺꾩꽍 ?꾨줈?앺듃"]}')
) AS role_data(role_cd, base_gap_score, gap_details, priority_skills, actions)
WHERE s.department_cd IN ('DEPT001', 'DEPT002', 'DEPT013');

-- Business/Management focused gap analysis
INSERT INTO tb_skill_gap_analysis (student_id, target_role_cd, analysis_date, overall_gap_score, gap_details, top_priority_skills, recommended_actions, ins_user_id, ins_dt)
SELECT
    s.student_id,
    role_data.role_cd,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '45 days'),
    role_data.base_gap_score + (RANDOM() * 10)::DECIMAL(5,2),
    role_data.gap_details::JSONB,
    role_data.priority_skills,
    role_data.actions::JSONB,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('ROLE009', 25.0, '[{"skill_cd": "SKL012", "current": 2, "required": 4, "gap": 2}, {"skill_cd": "SKL014", "current": 3, "required": 4, "gap": 1}]',
         ARRAY['SKL012', 'SKL010', 'SKL015'], '{"courses": ["BA302", "GE301"], "programs": ["PGM004"], "activities": ["由щ뜑???꾨줈洹몃옩 李몄뿬"]}'),
        ('ROLE012', 30.0, '[{"skill_cd": "SKL013", "current": 2, "required": 5, "gap": 3}, {"skill_cd": "SKL007", "current": 2, "required": 3, "gap": 1}]',
         ARRAY['SKL013', 'SKL012'], '{"courses": ["BA401", "BA302"], "programs": ["PGM008"], "activities": ["?고븰?묐젰 ?꾨줈?앺듃 李몄뿬"]}')
) AS role_data(role_cd, base_gap_score, gap_details, priority_skills, actions)
WHERE s.department_cd IN ('DEPT014', 'DEPT006');

-- Design focused gap analysis
INSERT INTO tb_skill_gap_analysis (student_id, target_role_cd, analysis_date, overall_gap_score, gap_details, top_priority_skills, recommended_actions, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'ROLE011',
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '20 days'),
    22.0 + (RANDOM() * 12)::DECIMAL(5,2),
    '[{"skill_cd": "SKL003", "current": 2, "required": 4, "gap": 2}, {"skill_cd": "SKL009", "current": 3, "required": 4, "gap": 1}]'::JSONB,
    ARRAY['SKL003', 'SKL009'],
    '{"courses": ["SW101"], "programs": ["PGM007"], "activities": ["UX/UI ?ы듃?대━??援ъ텞"]}'::JSONB,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd = 'DEPT025';

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    role_skill_count INT;
    skill_relation_count INT;
    student_skill_count INT;
    gap_analysis_count INT;
BEGIN
    SELECT COUNT(*) INTO role_skill_count FROM tb_role_skill_map WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO skill_relation_count FROM tb_skill_relation WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO student_skill_count FROM tb_student_skill WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO gap_analysis_count FROM tb_skill_gap_analysis WHERE ins_user_id = 'SEED_SCRIPT';

    RAISE NOTICE '=== P1 Skills Seed Data Created ===';
    RAISE NOTICE 'tb_role_skill_map: % records', role_skill_count;
    RAISE NOTICE 'tb_skill_relation: % records', skill_relation_count;
    RAISE NOTICE 'tb_student_skill: % records', student_skill_count;
    RAISE NOTICE 'tb_skill_gap_analysis: % records', gap_analysis_count;
END $$;
