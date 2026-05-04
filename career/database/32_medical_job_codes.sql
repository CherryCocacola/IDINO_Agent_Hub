-- ============================================
-- IDINO Career - Medical Field Worknet Job Codes
-- 의료 분야 워크넷 직업 코드 및 매핑 데이터
-- 워크넷(worknet.go.kr) 한국표준직업분류(KSCO) 기반
-- ============================================

SET search_path TO idino_career;

BEGIN;

-- ============================================
-- 1. tb_worknet_job에 의료 직업 추가
-- 워크넷 KSCO 코드 기준 보건/의료 분야 직업
-- ============================================

INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES

-- 의사 직군
('241101', '일반의사', 'General Practitioner', '보건/의료', '진료의사', '환자의 질병을 진단하고 치료하며, 건강 관리 및 예방 의료 서비스를 제공하는 의료 전문가',
 ARRAY['진단능력', '임상술기', '의사소통', '응급처치', 'EMR시스템', '의학지식'],
 ARRAY['의학과', '의예과'],
 6000, 12000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),

('241201', '전문의', 'Medical Specialist', '보건/의료', '전문진료의사', '특정 의료 분야(내과, 외과, 소아과 등)를 전문으로 진료하는 의사',
 ARRAY['전문진료', '수술기술', '연구능력', '임상술기', '최신의학지식'],
 ARRAY['의학과', '의예과'],
 8000, 20000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),

-- 간호사 직군
('243001', '간호사', 'Registered Nurse', '보건/의료', '간호', '환자의 건강 회복을 돕고 의료진을 보조하며, 투약 및 치료를 수행하는 의료 전문가',
 ARRAY['환자간호', '투약관리', '응급처치', '의료기록', 'EMR시스템', '의사소통', 'BLS/ACLS'],
 ARRAY['간호학과'],
 3800, 5500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 의료기사 직군
('244201', '임상병리사', 'Medical Laboratory Scientist', '보건/의료', '의료기사', '혈액, 소변, 조직 등의 검체를 분석하여 질병 진단에 필요한 정보를 제공하는 전문가',
 ARRAY['검체분석', '임상검사', '혈액검사', '미생물검사', '의료장비운용', '품질관리'],
 ARRAY['임상병리학과', '보건학과'],
 3200, 4800, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

('244301', '치과위생사', 'Dental Hygienist', '보건/의료', '의료기사', '구강 건강을 관리하고 예방 치료를 제공하며, 치과 의사를 보조하는 전문가',
 ARRAY['구강관리', '스케일링', '치아관리교육', '치과기구사용', '환자상담', '감염관리'],
 ARRAY['치위생학과', '치의학과'],
 3000, 4500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

('244401', '방사선사', 'Radiologic Technologist', '보건/의료', '의료기사', 'X선, CT, MRI 등 방사선 장비를 이용하여 진단에 필요한 영상을 촬영하는 전문가',
 ARRAY['방사선촬영', 'X-ray', 'CT촬영', 'MRI촬영', '영상분석', '방사선안전관리'],
 ARRAY['방사선학과', '보건학과'],
 3300, 5000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 물리치료사/작업치료사
('245101', '물리치료사', 'Physical Therapist', '보건/의료', '재활치료', '근골격계 및 신경계 질환 환자의 기능 회복을 위한 물리치료를 제공하는 전문가',
 ARRAY['물리치료', '재활치료', '운동치료', '도수치료', '전기치료', '환자평가'],
 ARRAY['물리치료학과', '재활학과'],
 3000, 4800, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

('245102', '작업치료사', 'Occupational Therapist', '보건/의료', '재활치료', '일상생활 활동 및 작업 수행 능력 회복을 위한 치료를 제공하는 전문가',
 ARRAY['작업치료', '재활치료', '인지치료', '일상생활훈련', '보조기기적용', '환자평가'],
 ARRAY['작업치료학과', '재활학과'],
 2900, 4500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 응급구조사
('245201', '응급구조사', 'Emergency Medical Technician', '보건/의료', '응급의료', '응급 상황에서 환자에게 응급처치 및 이송 서비스를 제공하는 전문가',
 ARRAY['응급처치', 'CPR', 'BLS', 'ACLS', '외상처치', '환자이송', '의료장비운용'],
 ARRAY['응급구조학과', '보건학과'],
 3000, 4500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 약사
('246101', '약사', 'Pharmacist', '보건/의료', '약학', '의약품을 조제하고 복약 지도를 제공하며, 의약품 관리 및 상담을 수행하는 전문가',
 ARRAY['의약품조제', '복약지도', '의약품관리', '약물상호작용분석', '환자상담', '임상약학'],
 ARRAY['약학과', '제약학과'],
 5500, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)

ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    job_subcategory = EXCLUDED.job_subcategory,
    description = EXCLUDED.description,
    required_skills = EXCLUDED.required_skills,
    related_majors = EXCLUDED.related_majors,
    avg_salary_entry = EXCLUDED.avg_salary_entry,
    avg_salary_experienced = EXCLUDED.avg_salary_experienced,
    job_outlook = EXCLUDED.job_outlook,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 2. tb_role에 worknet_code 업데이트 (의료 직업)
-- 기존 ROLE101~ROLE106 직업에 워크넷 코드 매핑
-- ============================================

-- worknet_code 컬럼이 없으면 추가 (이미 30_worknet_job_codes.sql에서 추가되었을 수 있음)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'idino_career'
        AND table_name = 'tb_role'
        AND column_name = 'worknet_code'
    ) THEN
        ALTER TABLE tb_role ADD COLUMN worknet_code VARCHAR(10);
        COMMENT ON COLUMN tb_role.worknet_code IS '워크넷 직업코드 (6자리)';
    END IF;
END $$;

-- 의료 직업 워크넷 코드 매핑
UPDATE tb_role SET worknet_code = '241101' WHERE role_cd = 'ROLE101'; -- 의사 → 일반의사
UPDATE tb_role SET worknet_code = '243001' WHERE role_cd = 'ROLE102'; -- 간호사
UPDATE tb_role SET worknet_code = '245101' WHERE role_cd = 'ROLE103'; -- 물리치료사
UPDATE tb_role SET worknet_code = '244201' WHERE role_cd = 'ROLE104'; -- 임상병리사
UPDATE tb_role SET worknet_code = '246101' WHERE role_cd = 'ROLE105'; -- 약사
UPDATE tb_role SET worknet_code = '244301' WHERE role_cd = 'ROLE106'; -- 치과위생사

-- ============================================
-- 3. 의료 분야 추가 역할 정의 (작업치료사, 방사선사, 응급구조사)
-- ============================================

INSERT INTO tb_role (role_cd, role_nm, role_nm_en, worknet_code, category, description, average_salary, growth_rate, use_fg, ins_user_id, ins_dt) VALUES
('ROLE107', '작업치료사', 'Occupational Therapist', '245102', '의료/보건', '일상생활 및 작업 수행 능력 회복을 위한 재활 치료 제공', 42000000, 5.5, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE108', '방사선사', 'Radiologic Technologist', '244401', '의료/보건', '방사선 장비를 이용한 의료 영상 촬영 및 분석', 48000000, 4.5, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE109', '응급구조사', 'Emergency Medical Technician', '245201', '의료/보건', '응급 상황에서 환자 응급처치 및 이송', 42000000, 4.0, 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    description = EXCLUDED.description,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 4. tb_student_interested_job에 의료 학과 학생 매핑
-- 학과명 패턴 매칭으로 의료 관련 학과 학생에게 관심 직업 추가
-- ============================================

-- 4.1 간호학과 학생 → 간호사, 의사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '243001' THEN 5  -- 간호사 (최우선)
        WHEN '241101' THEN 3  -- 일반의사
        WHEN '245201' THEN 3  -- 응급구조사
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE d.department_nm LIKE '%간호%'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('243001', '241101', '245201')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.2 물리치료학과 학생 → 물리치료사, 작업치료사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '245101' THEN 5  -- 물리치료사 (최우선)
        WHEN '245102' THEN 4  -- 작업치료사
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE d.department_nm LIKE '%물리치료%'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('245101', '245102')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.3 임상병리학과 학생 → 임상병리사, 방사선사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '244201' THEN 5  -- 임상병리사 (최우선)
        WHEN '244401' THEN 4  -- 방사선사
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE (d.department_nm LIKE '%임상병리%' OR d.department_nm LIKE '%병리%')
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('244201', '244401')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.4 약학과 학생 → 약사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    5, -- 약사 (최우선)
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE d.department_nm LIKE '%약학%'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd = '246101'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.5 작업치료학과 학생 → 작업치료사, 물리치료사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '245102' THEN 5  -- 작업치료사 (최우선)
        WHEN '245101' THEN 4  -- 물리치료사
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE d.department_nm LIKE '%작업치료%'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('245102', '245101')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.6 의예과/의학과 학생 → 의사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '241201' THEN 5  -- 전문의 (최우선)
        WHEN '241101' THEN 5  -- 일반의사
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE (d.department_nm LIKE '%의예%' OR d.department_nm LIKE '%의학%' OR d.department_nm = '의예과')
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('241101', '241201')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.7 치위생학과 학생 → 치과위생사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    5, -- 치과위생사 (최우선)
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE (d.department_nm LIKE '%치위생%' OR d.department_nm LIKE '%치과위생%')
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd = '244301'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.8 방사선학과 학생 → 방사선사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    5, -- 방사선사 (최우선)
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE d.department_nm LIKE '%방사선%'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd = '244401'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 4.9 응급구조학과 학생 → 응급구조사 관심 직업
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT DISTINCT s.student_id, j.job_cd,
    5, -- 응급구조사 (최우선)
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job j
WHERE d.department_nm LIKE '%응급구조%'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd = '245201'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- ============================================
-- 5. tb_success_pattern에 의료 분야 성공 패턴 추가
-- 학과별 의료 직업 취업 성공 패턴
-- ============================================

-- 5.1 간호학과 → 간호사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    '간호사 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE102', -- 간호사
    '간호학과 학생의 간호사 취업 성공 패턴. 국가고시 합격과 임상실습 경험이 핵심.',
    '3.0-4.0',
    ARRAY['기본간호학', '성인간호학', '아동간호학', '모성간호학', '정신간호학', '지역사회간호학']::varchar[],
    ARRAY['임상실습(1000시간 이상)', '병원 자원봉사', 'BLS/ACLS 자격증', '학술대회 참여', '간호 스터디그룹']::varchar[],
    ARRAY['환자간호', '투약관리', '응급처치', '의료기록', 'EMR시스템', '의사소통', 'BLS', 'ACLS']::varchar[],
    jsonb_build_object(
        '1학년', '기초의학, 간호학개론',
        '2학년', '기본간호학, 간호술기 실습',
        '3학년', '임상간호학, 병원실습 시작',
        '4학년', '심화실습, 국가고시 준비'
    ),
    0.95, -- 간호사 국시 합격률 높음
    120,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%간호%'
ON CONFLICT DO NOTHING;

-- 5.2 물리치료학과 → 물리치료사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    '물리치료사 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE103', -- 물리치료사
    '물리치료학과 학생의 물리치료사 취업 성공 패턴. 해부학 기초와 다양한 치료 기법 숙달이 핵심.',
    '3.2-4.0',
    ARRAY['해부학', '생리학', '운동치료학', '전기치료학', '도수치료학', '신경계물리치료']::varchar[],
    ARRAY['임상실습', '재활병원 봉사', '물리치료 학회 참여', '도수치료 세미나', '스포츠재활 프로그램']::varchar[],
    ARRAY['물리치료', '운동치료', '도수치료', '전기치료', '환자평가', '재활계획수립']::varchar[],
    jsonb_build_object(
        '1학년', '해부학, 생리학 기초',
        '2학년', '치료학 기초, 실기 입문',
        '3학년', '전문 치료기법, 임상실습',
        '4학년', '심화실습, 국가고시 준비'
    ),
    0.85,
    80,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%물리치료%'
ON CONFLICT DO NOTHING;

-- 5.3 임상병리학과 → 임상병리사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    '임상병리사 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE104', -- 임상병리사
    '임상병리학과 학생의 임상병리사 취업 성공 패턴. 정확한 검사 수행 능력과 품질관리 역량이 핵심.',
    '3.3-4.0',
    ARRAY['임상화학', '임상혈액학', '임상미생물학', '조직병리학', '분자진단학', '수혈의학']::varchar[],
    ARRAY['검사실 실습', '병원 인턴십', '품질관리 교육', '최신 검사법 세미나', '학술 발표']::varchar[],
    ARRAY['검체분석', '혈액검사', '미생물검사', '품질관리', '의료장비운용', '데이터분석']::varchar[],
    jsonb_build_object(
        '1학년', '기초의학, 화학 기초',
        '2학년', '검사학 기초, 실험 실습',
        '3학년', '전문검사학, 병원실습',
        '4학년', '심화실습, 국가고시 준비'
    ),
    0.88,
    65,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%임상병리%' OR d.department_nm LIKE '%병리%'
ON CONFLICT DO NOTHING;

-- 5.4 약학과 → 약사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    '약사 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE105', -- 약사
    '약학과 학생의 약사 취업 성공 패턴. 약학 전문지식과 환자 상담 역량이 핵심.',
    '3.5-4.5',
    ARRAY['약물학', '약제학', '약물치료학', '임상약학', '약전학', '독성학']::varchar[],
    ARRAY['약국 실습', '병원약국 인턴십', '약학 학술대회', '의약품 정보 연구', '환자상담 실습']::varchar[],
    ARRAY['의약품조제', '복약지도', '약물상호작용분석', '환자상담', '의약품관리', '임상약학']::varchar[],
    jsonb_build_object(
        '1-2학년', '예과 과정, 기초과학',
        '3학년', '약학 기초, 약물학',
        '4학년', '임상약학, 약국실습',
        '5-6학년', '심화실습, 국가고시 준비'
    ),
    0.92,
    50,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%약학%'
ON CONFLICT DO NOTHING;

-- 5.5 작업치료학과 → 작업치료사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    '작업치료사 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE107', -- 작업치료사
    '작업치료학과 학생의 작업치료사 취업 성공 패턴. 일상생활 활동 분석 및 치료 계획 수립 역량이 핵심.',
    '3.2-4.0',
    ARRAY['작업치료학개론', '인지재활치료', '신경과학', '정신사회작업치료', '아동작업치료', '노인작업치료']::varchar[],
    ARRAY['임상실습', '재활센터 봉사', '작업치료 학회', '보조기기 워크숍', '인지재활 프로그램']::varchar[],
    ARRAY['작업치료', '인지치료', '일상생활훈련', '보조기기적용', '환자평가', '치료계획수립']::varchar[],
    jsonb_build_object(
        '1학년', '해부학, 작업치료 개론',
        '2학년', '치료학 기초, 실기 입문',
        '3학년', '전문 치료기법, 임상실습',
        '4학년', '심화실습, 국가고시 준비'
    ),
    0.82,
    55,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%작업치료%'
ON CONFLICT DO NOTHING;

-- 5.6 의예과/의학과 → 의사 취업 성공 패턴 (대학원 진학 포함)
INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    '전문의 진로 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE101', -- 의사
    '의예과/의학과 학생의 전문의 진로 성공 패턴. 기초의학, 임상실습, 전공의 과정이 핵심.',
    '3.8-4.5',
    ARRAY['해부학', '생리학', '병리학', '약리학', '내과학', '외과학', '소아과학', '산부인과학']::varchar[],
    ARRAY['병원실습', '연구참여', '학술발표', '의료봉사', '국제학회']::varchar[],
    ARRAY['진단능력', '임상술기', '수술기술', '의학지식', '의사소통', '연구능력']::varchar[],
    jsonb_build_object(
        '예과 1-2학년', '기초과학, 의학개론',
        '본과 1-2학년', '기초의학, 해부학실습',
        '본과 3-4학년', '임상의학, 병원실습',
        '졸업 후', '인턴, 레지던트 과정'
    ),
    0.98, -- 의사 국시 합격률
    40,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%의예%' OR d.department_nm LIKE '%의학%' OR d.department_nm = '의예과'
ON CONFLICT DO NOTHING;

-- ============================================
-- 6. 인덱스 생성 (의료 직업 검색 최적화)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_worknet_job_medical ON tb_worknet_job(job_cd)
    WHERE job_category = '보건/의료';

-- ============================================
-- 7. tb_worknet_diagnosis 의료 학과 학생 진단 결과 업데이트
-- (테이블이 존재하는 경우에만 실행)
-- ============================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'idino_career' AND table_name = 'tb_worknet_diagnosis'
    ) THEN
        -- 간호학과 학생
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"243001": 95, "241101": 70, "245201": 65}'::jsonb
        WHERE student_id IN (
            SELECT s.student_id FROM tb_student s
            JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE d.department_nm LIKE '%간호%'
        );

        -- 물리치료학과 학생
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"245101": 92, "245102": 85, "243001": 60}'::jsonb
        WHERE student_id IN (
            SELECT s.student_id FROM tb_student s
            JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE d.department_nm LIKE '%물리치료%'
        );

        -- 임상병리학과 학생
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"244201": 90, "244401": 80, "243001": 55}'::jsonb
        WHERE student_id IN (
            SELECT s.student_id FROM tb_student s
            JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE d.department_nm LIKE '%임상병리%' OR d.department_nm LIKE '%병리%'
        );

        -- 약학과 학생
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"246101": 95, "241101": 50}'::jsonb
        WHERE student_id IN (
            SELECT s.student_id FROM tb_student s
            JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE d.department_nm LIKE '%약학%'
        );

        -- 작업치료학과 학생
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"245102": 90, "245101": 82, "243001": 55}'::jsonb
        WHERE student_id IN (
            SELECT s.student_id FROM tb_student s
            JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE d.department_nm LIKE '%작업치료%'
        );

        -- 의예과/의학과 학생
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"241201": 98, "241101": 98}'::jsonb
        WHERE student_id IN (
            SELECT s.student_id FROM tb_student s
            JOIN tb_department d ON s.department_cd = d.department_cd
            WHERE d.department_nm LIKE '%의예%' OR d.department_nm LIKE '%의학%'
        );
    END IF;
END $$;

COMMIT;

-- ============================================
-- 확인 쿼리
-- ============================================

-- 의료 직업 추가 확인
-- SELECT * FROM tb_worknet_job WHERE job_category = '보건/의료' ORDER BY job_cd;

-- 역할 매핑 확인
-- SELECT role_cd, role_nm, worknet_code FROM tb_role WHERE role_cd LIKE 'ROLE10%' ORDER BY role_cd;

-- 학생 관심 직업 확인 (의료 분야)
-- SELECT COUNT(*) as medical_interested_count
-- FROM tb_student_interested_job sij
-- JOIN tb_worknet_job wj ON sij.job_cd = wj.job_cd
-- WHERE wj.job_category = '보건/의료';

-- 성공 패턴 확인 (의료 분야)
-- SELECT pattern_nm, department_cd, role_cd, success_rate
-- FROM tb_success_pattern
-- WHERE role_cd IN ('ROLE101', 'ROLE102', 'ROLE103', 'ROLE104', 'ROLE105', 'ROLE106', 'ROLE107', 'ROLE108', 'ROLE109')
-- ORDER BY role_cd;

-- 의료 학과별 학생-직업 매핑 통계
-- SELECT d.department_nm, COUNT(DISTINCT sij.student_id) as student_count, COUNT(*) as total_mappings
-- FROM tb_student_interested_job sij
-- JOIN tb_student s ON sij.student_id = s.student_id
-- JOIN tb_department d ON s.department_cd = d.department_cd
-- JOIN tb_worknet_job wj ON sij.job_cd = wj.job_cd
-- WHERE wj.job_category = '보건/의료'
-- GROUP BY d.department_nm
-- ORDER BY student_count DESC;
