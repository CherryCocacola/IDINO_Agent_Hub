-- =============================================================
-- 54_seed_department_skills.sql
-- 학과별 전공 관련 스킬 데이터 추가
-- 의료/보건, 경영, 교육, 예술/미디어, 약학, 공학(비IT) 등
-- =============================================================
SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 1: 학과별 전공 스킬 추가 (tb_skill)
-- =====================================================

-- 의료/보건 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKMD01', '환자진료', 'Patient Care', '의료', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD02', '의료기록관리', 'Medical Record Management', '의료', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD03', '응급처치', 'First Aid', '의료', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD04', '간호처치', 'Nursing Care', '의료', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD05', '물리치료', 'Physical Therapy', '의료', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD06', '운동처방', 'Exercise Prescription', '의료', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD07', '임상검사', 'Clinical Testing', '의료', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD08', '재활운동', 'Rehabilitation Exercise', '의료', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD09', '건강평가', 'Health Assessment', '의료', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKMD10', '환자상담', 'Patient Counseling', '의료', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 경영 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKBZ01', '재무분석', 'Financial Analysis', '경영', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKBZ02', '회계', 'Accounting', '경영', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKBZ03', '마케팅전략', 'Marketing Strategy', '경영', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKBZ04', '경영분석', 'Business Analysis', '경영', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKBZ05', '인사관리', 'HR Management', '경영', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKBZ06', '기업전략', 'Corporate Strategy', '경영', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKBZ07', '세무', 'Tax', '경영', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 교육 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKED01', '교육과정설계', 'Curriculum Design', '교육', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKED02', '학생지도', 'Student Guidance', '교육', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKED03', '수업설계', 'Lesson Planning', '교육', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKED04', '교육평가', 'Education Assessment', '교육', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKED05', '교육공학', 'Educational Technology', '교육', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKED06', '학급운영', 'Classroom Management', '교육', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 예술/미디어 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKART01', '그래픽디자인', 'Graphic Design', '예술', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKART02', '영상편집', 'Video Editing', '예술', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKART03', '포트폴리오제작', 'Portfolio Creation', '예술', 2, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKART04', 'UI설계', 'UI Design', '예술', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKART05', '타이포그래피', 'Typography', '예술', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKART06', '3D모델링', '3D Modeling', '예술', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKART07', 'Adobe도구', 'Adobe Tools', '예술', 2, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 약학 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKPH01', '약리학', 'Pharmacology', '약학', 5, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKPH02', '조제기술', 'Dispensing', '약학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKPH03', '임상약학', 'Clinical Pharmacy', '약학', 5, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKPH04', '약물상호작용', 'Drug Interaction', '약학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKPH05', '의약품관리', 'Drug Management', '약학', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 비IT 공학 스킬 (기계, 전기, 토목 등 공통)
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKEG01', '설계', 'Engineering Design', '공학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKEG02', 'CAD/CAM', 'CAD/CAM', '공학', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKEG03', '안전관리', 'Safety Management', '공학', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKEG04', '품질관리', 'Quality Control', '공학', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKEG05', '시공관리', 'Construction Management', '공학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKEG06', '구조해석', 'Structural Analysis', '공학', 5, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKEG07', '재료역학', 'Mechanics of Materials', '공학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 사회과학/인문 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKSC01', '사례관리', 'Case Management', '사회과학', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKSC02', '상담기법', 'Counseling Techniques', '사회과학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKSC03', '정책분석', 'Policy Analysis', '사회과학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKSC04', '연구방법론', 'Research Methodology', '사회과학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKSC05', '논문작성', 'Academic Writing', '인문', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKSC06', '외국어', 'Foreign Language', '인문', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- 자연과학 스킬
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKNS01', '실험설계', 'Experimental Design', '자연과학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKNS02', '통계분석', 'Statistical Analysis', '자연과학', 4, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('SKNS03', '데이터시각화', 'Data Visualization', '자연과학', 3, 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;


-- =====================================================
-- Part 2: 역할-스킬 매핑 추가 (tb_role_skill_map)
-- =====================================================

-- 먼저 학과 카테고리별 역할이 있는지 확인 후 역할 추가
-- Medical roles
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE101', '의사', 'Medical Doctor', '의료', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE102', '간호사', 'Nurse', '의료', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE103', '물리치료사', 'Physical Therapist', '의료', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE104', '스포츠트레이너', 'Sports Trainer', '보건', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE105', '약사', 'Pharmacist', '약학', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- Education roles
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE201', '초등교사', 'Elementary Teacher', '교육', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE202', '중등교사', 'Secondary Teacher', '교육', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- Arts roles
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE301', '그래픽디자이너', 'Graphic Designer', '예술', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE302', '영상편집자', 'Video Editor', '예술', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- Business roles (some may already exist)
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE401', '공인회계사', 'CPA', '경영', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE402', '금융분석가', 'Financial Analyst', '경영', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- Science roles
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE501', '연구원', 'Researcher', '연구', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- Engineering roles
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE601', '기계엔지니어', 'Mechanical Engineer', '공학', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE602', '전기엔지니어', 'Electrical Engineer', '공학', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE603', '토목엔지니어', 'Civil Engineer', '공학', 'Y', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;


-- Role-Skill mappings for medical roles
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    -- 스포츠트레이너
    ('ROLE104', 'SKMD06', 4, 'critical', 80.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE104', 'SKMD08', 4, 'critical', 78.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE104', 'SKMD09', 3, 'important', 75.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE104', 'SKMD03', 3, 'important', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE104', 'SKMD10', 2, 'nice_to_have', 70.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE104', 'SKMD05', 3, 'important', 75.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    -- 간호사
    ('ROLE102', 'SKMD04', 5, 'critical', 90.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE102', 'SKMD01', 4, 'critical', 88.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE102', 'SKMD03', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE102', 'SKMD02', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE102', 'SKMD10', 3, 'important', 78.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    -- 물리치료사
    ('ROLE103', 'SKMD05', 5, 'critical', 85.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE103', 'SKMD08', 4, 'critical', 82.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE103', 'SKMD09', 3, 'important', 78.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE103', 'SKMD10', 3, 'important', 76.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    -- 약사
    ('ROLE105', 'SKPH01', 5, 'critical', 90.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE105', 'SKPH02', 5, 'critical', 88.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE105', 'SKPH03', 4, 'critical', 85.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE105', 'SKPH04', 4, 'important', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE105', 'SKPH05', 3, 'important', 78.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Role-Skill mappings for education roles
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    ('ROLE201', 'SKED01', 4, 'critical', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE201', 'SKED02', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE201', 'SKED03', 4, 'critical', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE201', 'SKED04', 3, 'important', 78.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE201', 'SKED06', 3, 'important', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE201', 'SKED05', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE202', 'SKED01', 4, 'critical', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE202', 'SKED03', 4, 'critical', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE202', 'SKED04', 3, 'important', 78.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE202', 'SKED05', 3, 'important', 75.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Role-Skill mappings for arts roles
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    ('ROLE301', 'SKART01', 5, 'critical', 88.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE301', 'SKART07', 4, 'critical', 90.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE301', 'SKART05', 3, 'important', 78.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE301', 'SKART03', 4, 'important', 85.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE302', 'SKART02', 5, 'critical', 85.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE302', 'SKART07', 4, 'critical', 88.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE302', 'SKART06', 3, 'important', 75.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE302', 'SKART03', 4, 'important', 82.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Role-Skill mappings for business roles
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    ('ROLE401', 'SKBZ01', 5, 'critical', 90.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE401', 'SKBZ02', 5, 'critical', 92.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE401', 'SKBZ07', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE401', 'SKBZ04', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE402', 'SKBZ01', 5, 'critical', 92.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE402', 'SKBZ04', 4, 'critical', 85.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE402', 'SKBZ03', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE402', 'SKL007', 4, 'important', 88.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Role-Skill mappings for engineering roles
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    ('ROLE601', 'SKEG01', 4, 'critical', 88.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE601', 'SKEG02', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE601', 'SKEG07', 4, 'critical', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE601', 'SKEG04', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE602', 'SKEG01', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE602', 'SKEG03', 3, 'important', 82.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE602', 'SKEG04', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE603', 'SKEG01', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE603', 'SKEG02', 4, 'critical', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE603', 'SKEG05', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE603', 'SKEG06', 4, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;

-- Role-Skill mappings for researcher
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    ('ROLE501', 'SKNS01', 4, 'critical', 85.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE501', 'SKNS02', 4, 'critical', 88.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE501', 'SKNS03', 3, 'important', 80.0, 'growing', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE501', 'SKSC04', 4, 'critical', 82.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE501', 'SKSC05', 3, 'important', 78.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP),
    ('ROLE501', 'SKNS03', 3, 'important', 80.0, 'stable', 'SEED_DEPT_SKILL', CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;


-- =====================================================
-- Part 3: 학생별 스킬 레벨 시딩 (tb_student_skill)
-- 학과 기반으로 관련 스킬 부여
-- =====================================================

-- 의료/보건 학과 학생들에게 의료 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    -- Level based on grade: 1학년=1, 2학년=2, 3학년=3, 4학년=4 (with some variance)
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    -- Target level based on role requirements
    CASE WHEN sk.difficulty >= 4 THEN 5 ELSE 4 END,
    -- Evidence count: more for higher grades
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd IN ('SKMD01','SKMD02','SKMD03','SKMD04','SKMD05','SKMD06','SKMD07','SKMD08','SKMD09','SKMD10')
) sk
WHERE d.department_nm ~ '의예|의학|간호|물리치료|임상|보건|치위생|방사선|응급|스포츠|헬스케어|체육'
  -- Only assign relevant skills per department
  AND (
    (d.department_nm ~ '간호' AND sk.skill_cd IN ('SKMD01','SKMD02','SKMD03','SKMD04','SKMD10'))
    OR (d.department_nm ~ '물리치료' AND sk.skill_cd IN ('SKMD05','SKMD08','SKMD09','SKMD10'))
    OR (d.department_nm ~ '스포츠|헬스케어|체육' AND sk.skill_cd IN ('SKMD06','SKMD08','SKMD09','SKMD03'))
    OR (d.department_nm ~ '의예|의학' AND sk.skill_cd IN ('SKMD01','SKMD02','SKMD03','SKMD07'))
    OR (d.department_nm ~ '보건|임상|치위생|방사선|응급' AND sk.skill_cd IN ('SKMD01','SKMD03','SKMD07','SKMD09'))
  )
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- 경영학과 학생들에게 경영 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    CASE WHEN sk.difficulty >= 4 THEN 5 ELSE 4 END,
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd IN ('SKBZ01','SKBZ02','SKBZ03','SKBZ04','SKBZ05','SKBZ06','SKBZ07')
) sk
WHERE d.department_nm ~ '경영|경제|회계|통상|무역|금융|세무'
  AND (
    (d.department_nm ~ '회계' AND sk.skill_cd IN ('SKBZ01','SKBZ02','SKBZ07'))
    OR (d.department_nm ~ '경영|경제|통상|무역|금융|세무' AND sk.skill_cd IN ('SKBZ01','SKBZ03','SKBZ04','SKBZ05','SKBZ06'))
  )
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- 교육학과 학생들에게 교육 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    4,
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd LIKE 'SKED%'
) sk
WHERE d.department_nm ~ '교육|사범'
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- 예술/디자인 학과 학생들에게 예술 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    CASE WHEN sk.difficulty >= 4 THEN 5 ELSE 4 END,
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd LIKE 'SKART%'
) sk
WHERE d.department_nm ~ '디자인|미술|예술|영상|미디어|애니|음악|방송'
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- 공학(비IT) 학과 학생들에게 공학 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    CASE WHEN sk.difficulty >= 4 THEN 5 ELSE 4 END,
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd LIKE 'SKEG%'
) sk
WHERE d.department_nm ~ '기계|전기|토목|건축|건설|화공|재료|산업|로봇|나노|소방'
  AND NOT d.department_nm ~ '컴퓨터|소프트웨어|정보|AI'
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- 자연과학 학과 학생들에게 과학 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    4,
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd IN ('SKNS01','SKNS02','SKNS03','SKSC04','SKSC05')
) sk
WHERE d.department_nm ~ '수학|물리|화학|생명과학|통계|환경|바이오'
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- 사회과학/인문 학과 학생들에게 관련 스킬 부여
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    sk.skill_cd,
    LEAST(5, GREATEST(1, s.current_grade + (CASE WHEN random() > 0.5 THEN 0 ELSE -1 END))),
    4,
    s.current_grade * 2 + floor(random() * 3)::int,
    CASE WHEN random() < 0.5 THEN 'improving' WHEN random() < 0.8 THEN 'stable' ELSE 'declining' END,
    'SEED_DEPT_SKILL',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN (
    SELECT skill_cd, difficulty FROM tb_skill WHERE skill_cd IN ('SKSC01','SKSC02','SKSC03','SKSC04','SKSC05','SKSC06')
) sk
WHERE d.department_nm ~ '사회|심리|행정|정치|법학|경찰|국문|영문|사학|철학|어문|인문|역사|문화'
  AND (
    (d.department_nm ~ '심리|상담' AND sk.skill_cd IN ('SKSC01','SKSC02','SKSC04'))
    OR (d.department_nm ~ '행정|정치|법학|경찰' AND sk.skill_cd IN ('SKSC03','SKSC04','SKSC05'))
    OR (d.department_nm ~ '사회|복지' AND sk.skill_cd IN ('SKSC01','SKSC02','SKSC03'))
    OR (d.department_nm ~ '국문|영문|사학|철학|어문|인문|역사|문화' AND sk.skill_cd IN ('SKSC04','SKSC05','SKSC06'))
  )
ON CONFLICT (student_id, skill_cd) DO NOTHING;

COMMIT;
