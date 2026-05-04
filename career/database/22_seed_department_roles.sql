-- ============================================
-- IDINO Career: 학과 카테고리별 직업(Role) 및 Success Pattern
-- 의료/보건, 교육, 예술/디자인, 경영/사회 계열 직업 추가
-- ============================================

SET search_path TO idino_career;

BEGIN;

-- ============================================
-- 1. 추가 직업(Role) 정의
-- ============================================

-- 의료/보건 계열 직업
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, use_fg, ins_user_id, ins_dt) VALUES
('ROLE101', '의사', 'Medical Doctor', '의료/보건', '환자 진료 및 치료, 의학 연구', 120000000, 3.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE102', '간호사', 'Registered Nurse', '의료/보건', '환자 간호 및 의료 지원', 55000000, 4.2, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE103', '물리치료사', 'Physical Therapist', '의료/보건', '재활 치료 및 물리 요법 제공', 50000000, 5.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE104', '임상병리사', 'Medical Laboratory Scientist', '의료/보건', '의료 검사 및 진단 지원', 48000000, 3.8, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE105', '약사', 'Pharmacist', '의료/보건', '의약품 조제 및 복약 지도', 75000000, 2.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE106', '치과위생사', 'Dental Hygienist', '의료/보건', '구강 건강 관리 및 예방 치료', 45000000, 4.0, 'Y', 'SEED', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- 교육 계열 직업
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, use_fg, ins_user_id, ins_dt) VALUES
('ROLE201', '초등교사', 'Elementary School Teacher', '교육', '초등학교 학생 교육 및 지도', 50000000, 1.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE202', '중등교사', 'Secondary School Teacher', '교육', '중고등학교 학생 교육 및 지도', 52000000, 1.2, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE203', '유아교사', 'Early Childhood Educator', '교육', '유아 교육 및 보육', 38000000, 3.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE204', '교육행정가', 'Education Administrator', '교육', '교육 기관 운영 및 관리', 60000000, 2.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE205', '교육컨설턴트', 'Education Consultant', '교육', '교육 프로그램 기획 및 컨설팅', 55000000, 4.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE206', '특수교육교사', 'Special Education Teacher', '교육', '특수교육 대상 학생 교육', 52000000, 2.8, 'Y', 'SEED', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- 예술/디자인 계열 직업
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, use_fg, ins_user_id, ins_dt) VALUES
('ROLE301', '그래픽디자이너', 'Graphic Designer', '예술/디자인', '시각 디자인 및 브랜딩', 42000000, 3.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE302', '산업디자이너', 'Industrial Designer', '예술/디자인', '제품 및 산업 디자인', 50000000, 4.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE303', '영상편집자', 'Video Editor', '예술/디자인', '영상 콘텐츠 편집 및 제작', 45000000, 6.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE304', '공연기획자', 'Performance Producer', '예술/디자인', '공연 기획 및 연출', 40000000, 2.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE305', '음악감독', 'Music Director', '예술/디자인', '음악 제작 및 감독', 55000000, 2.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE306', '실내디자이너', 'Interior Designer', '예술/디자인', '실내 공간 디자인', 45000000, 3.2, 'Y', 'SEED', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- 경영/사회 계열 직업
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, use_fg, ins_user_id, ins_dt) VALUES
('ROLE401', '공무원', 'Government Official', '공공/행정', '정부 기관 행정 업무', 48000000, 1.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE402', '사회복지사', 'Social Worker', '공공/행정', '사회복지 서비스 제공', 35000000, 4.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE403', '심리상담사', 'Counseling Psychologist', '공공/행정', '심리 상담 및 치료', 45000000, 5.2, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE404', '회계사', 'Accountant', '경영/금융', '재무 회계 및 감사', 70000000, 2.8, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE405', '금융분석가', 'Financial Analyst', '경영/금융', '투자 분석 및 금융 자문', 80000000, 4.0, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE406', '인사관리자', 'HR Manager', '경영/금융', '인사 관리 및 조직 개발', 60000000, 3.0, 'Y', 'SEED', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- 자연과학 계열 직업
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, use_fg, ins_user_id, ins_dt) VALUES
('ROLE501', '연구원', 'Researcher', '연구/과학', '과학 연구 및 실험', 55000000, 3.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE502', '바이오엔지니어', 'Biomedical Engineer', '연구/과학', '생명공학 연구 및 개발', 65000000, 6.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE503', '화학분석사', 'Chemical Analyst', '연구/과학', '화학 물질 분석 및 검사', 50000000, 2.5, 'Y', 'SEED', CURRENT_TIMESTAMP),
('ROLE504', '환경전문가', 'Environmental Specialist', '연구/과학', '환경 영향 평가 및 관리', 52000000, 5.0, 'Y', 'SEED', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- ============================================
-- 2. 기존 Success Pattern 삭제
-- ============================================
DELETE FROM tb_success_pattern WHERE ins_user_id = 'system' OR ins_user_id = 'SEED';

-- ============================================
-- 3. 학과 카테고리별 Success Pattern 생성
-- ============================================
WITH department_category_map AS (
    SELECT
        d.department_cd,
        d.department_nm,
        CASE
            WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%'
                 OR d.department_nm LIKE '%정보%' OR d.department_nm LIKE '%AI%' THEN 'IT'
            WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%전기%'
                 OR d.department_nm LIKE '%기계%' OR d.department_nm LIKE '%산업%'
                 OR d.department_nm LIKE '%건축%' OR d.department_nm LIKE '%재료%'
                 OR d.department_nm LIKE '%화공%' OR d.department_nm LIKE '%화학공%' THEN 'Engineering'
            WHEN d.department_nm LIKE '%의%과' OR d.department_nm LIKE '%의학%'
                 OR d.department_nm LIKE '%간호%' OR d.department_nm LIKE '%약%'
                 OR d.department_nm LIKE '%치%' OR d.department_nm LIKE '%보건%'
                 OR d.department_nm LIKE '%물리치료%' OR d.department_nm LIKE '%임상%' THEN 'Medical'
            WHEN d.department_nm LIKE '%교육%' OR d.department_nm LIKE '%사범%' THEN 'Education'
            WHEN d.department_nm LIKE '%디자인%' OR d.department_nm LIKE '%미술%'
                 OR d.department_nm LIKE '%음악%' OR d.department_nm LIKE '%예술%'
                 OR d.department_nm LIKE '%공연%' OR d.department_nm LIKE '%영상%' THEN 'Arts'
            WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%'
                 OR d.department_nm LIKE '%회계%' OR d.department_nm LIKE '%금융%'
                 OR d.department_nm LIKE '%무역%' OR d.department_nm LIKE '%통상%' THEN 'Business'
            WHEN d.department_nm LIKE '%행정%' OR d.department_nm LIKE '%사회%'
                 OR d.department_nm LIKE '%심리%' OR d.department_nm LIKE '%복지%'
                 OR d.department_nm LIKE '%정치%' OR d.department_nm LIKE '%법%' THEN 'Social'
            WHEN d.department_nm LIKE '%문학%' OR d.department_nm LIKE '%어%'
                 OR d.department_nm LIKE '%철학%' OR d.department_nm LIKE '%역사%'
                 OR d.department_nm LIKE '%국문%' OR d.department_nm LIKE '%영문%' THEN 'Humanities'
            WHEN d.department_nm LIKE '%수학%' OR d.department_nm LIKE '%물리%'
                 OR d.department_nm LIKE '%화학%' OR d.department_nm LIKE '%생명%'
                 OR d.department_nm LIKE '%통계%' OR d.department_nm LIKE '%생물%' THEN 'Science'
            ELSE 'General'
        END as category
    FROM tb_department d
),
category_roles AS (
    SELECT * FROM (VALUES
        ('IT', ARRAY['ROLE01', 'ROLE02', 'ROLE03', 'ROLE07', 'ROLE08']),
        ('Engineering', ARRAY['ROLE01', 'ROLE02', 'ROLE06', 'ROLE07', 'ROLE08']),
        ('Medical', ARRAY['ROLE101', 'ROLE102', 'ROLE103', 'ROLE104', 'ROLE105']),
        ('Education', ARRAY['ROLE201', 'ROLE202', 'ROLE203', 'ROLE204', 'ROLE205']),
        ('Arts', ARRAY['ROLE301', 'ROLE302', 'ROLE303', 'ROLE011', 'ROLE306']),
        ('Business', ARRAY['ROLE009', 'ROLE010', 'ROLE012', 'ROLE404', 'ROLE405']),
        ('Social', ARRAY['ROLE401', 'ROLE402', 'ROLE403', 'ROLE009', 'ROLE406']),
        ('Humanities', ARRAY['ROLE009', 'ROLE010', 'ROLE401', 'ROLE205', 'ROLE304']),
        ('Science', ARRAY['ROLE501', 'ROLE502', 'ROLE503', 'ROLE504', 'ROLE03']),
        ('General', ARRAY['ROLE009', 'ROLE010', 'ROLE012', 'ROLE401', 'ROLE406'])
    ) AS t(category, role_codes)
),
category_courses AS (
    SELECT * FROM (VALUES
        ('IT', ARRAY['Programming', 'Data Science', 'Software Engineering', 'AI/ML', 'Database']),
        ('Engineering', ARRAY['Engineering Math', 'Physics', 'CAD/CAM', 'Materials Science', 'Project Management']),
        ('Medical', ARRAY['Anatomy', 'Pharmacology', 'Clinical Practice', 'Patient Care', 'Medical Ethics']),
        ('Education', ARRAY['Educational Psychology', 'Teaching Methods', 'Curriculum Development', 'Child Development', 'Assessment']),
        ('Arts', ARRAY['Design Fundamentals', 'Art History', 'Portfolio Development', 'Digital Media', 'Creative Practice']),
        ('Business', ARRAY['Accounting', 'Marketing', 'Finance', 'Business Strategy', 'Management']),
        ('Social', ARRAY['Social Research', 'Public Policy', 'Psychology', 'Statistics', 'Communication']),
        ('Humanities', ARRAY['Writing', 'Literature', 'Philosophy', 'History', 'Cultural Studies']),
        ('Science', ARRAY['Research Methods', 'Laboratory Practice', 'Statistics', 'Scientific Writing', 'Data Analysis']),
        ('General', ARRAY['Communication', 'Problem Solving', 'Critical Thinking', 'Leadership', 'Teamwork'])
    ) AS t(category, courses)
),
category_skills AS (
    SELECT * FROM (VALUES
        ('IT', ARRAY['Python', 'Java', 'SQL', 'Cloud', 'Git']),
        ('Engineering', ARRAY['CAD', 'MATLAB', 'Problem Solving', 'Technical Writing', 'Project Management']),
        ('Medical', ARRAY['Patient Care', 'Medical Records', 'Clinical Skills', 'Communication', 'Emergency Response']),
        ('Education', ARRAY['Lesson Planning', 'Classroom Management', 'Assessment', 'Communication', 'Patience']),
        ('Arts', ARRAY['Adobe Creative Suite', 'Portfolio', 'Creativity', 'Visual Communication', 'Digital Media']),
        ('Business', ARRAY['Excel', 'Financial Analysis', 'Presentation', 'Negotiation', 'Strategic Thinking']),
        ('Social', ARRAY['Research', 'Data Analysis', 'Policy Analysis', 'Communication', 'Empathy']),
        ('Humanities', ARRAY['Writing', 'Research', 'Critical Analysis', 'Foreign Languages', 'Public Speaking']),
        ('Science', ARRAY['Data Analysis', 'Lab Techniques', 'Statistical Software', 'Scientific Writing', 'Research Design']),
        ('General', ARRAY['Communication', 'Problem Solving', 'Teamwork', 'Time Management', 'Adaptability'])
    ) AS t(category, skills)
)
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    dcm.category || ' 취업 경로 - ' || dcm.department_nm,
    pattern_type,
    dcm.department_cd,
    role_code,
    '학과 특성에 맞는 ' || pattern_type || ' 경로를 통한 성공 패턴',
    CASE
        WHEN random() < 0.3 THEN '3.0-3.5'
        WHEN random() < 0.6 THEN '3.5-4.0'
        ELSE '4.0-4.5'
    END,
    cc.courses,
    ARRAY['Internship', 'Project', 'Competition', 'Study Group', 'Certification']::varchar[],
    cs.skills,
    jsonb_build_object(
        'year1', 'Foundation courses and basic skills',
        'year2', 'Core courses and first project',
        'year3', 'Specialization and internship',
        'year4', 'Capstone project and job preparation'
    ),
    round((60 + random() * 35)::numeric, 1),
    (50 + (random() * 150))::int,
    'SEED',
    now()
FROM department_category_map dcm
JOIN category_roles cr ON dcm.category = cr.category
JOIN category_courses cc ON dcm.category = cc.category
JOIN category_skills cs ON dcm.category = cs.category
CROSS JOIN (VALUES ('employment'), ('graduate_school'), ('startup')) AS pt(pattern_type)
CROSS JOIN LATERAL unnest(cr.role_codes) AS role_code
WHERE EXISTS (SELECT 1 FROM tb_role r WHERE r.role_cd = role_code)
ON CONFLICT DO NOTHING;

-- ============================================
-- 4. 기존 Alumni Cohort 삭제
-- ============================================
DELETE FROM tb_alumni_cohort WHERE ins_user_id = 'system' OR ins_user_id = 'SEED';

-- ============================================
-- 5. 학과 카테고리별 Alumni Cohort 생성
-- ============================================
WITH department_category_map AS (
    SELECT
        d.department_cd,
        d.department_nm,
        CASE
            WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%'
                 OR d.department_nm LIKE '%정보%' OR d.department_nm LIKE '%AI%' THEN 'IT'
            WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%전기%'
                 OR d.department_nm LIKE '%기계%' OR d.department_nm LIKE '%산업%'
                 OR d.department_nm LIKE '%건축%' OR d.department_nm LIKE '%재료%'
                 OR d.department_nm LIKE '%화공%' OR d.department_nm LIKE '%화학공%' THEN 'Engineering'
            WHEN d.department_nm LIKE '%의%과' OR d.department_nm LIKE '%의학%'
                 OR d.department_nm LIKE '%간호%' OR d.department_nm LIKE '%약%'
                 OR d.department_nm LIKE '%치%' OR d.department_nm LIKE '%보건%'
                 OR d.department_nm LIKE '%물리치료%' OR d.department_nm LIKE '%임상%' THEN 'Medical'
            WHEN d.department_nm LIKE '%교육%' OR d.department_nm LIKE '%사범%' THEN 'Education'
            WHEN d.department_nm LIKE '%디자인%' OR d.department_nm LIKE '%미술%'
                 OR d.department_nm LIKE '%음악%' OR d.department_nm LIKE '%예술%'
                 OR d.department_nm LIKE '%공연%' OR d.department_nm LIKE '%영상%' THEN 'Arts'
            WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%'
                 OR d.department_nm LIKE '%회계%' OR d.department_nm LIKE '%금융%'
                 OR d.department_nm LIKE '%무역%' OR d.department_nm LIKE '%통상%' THEN 'Business'
            WHEN d.department_nm LIKE '%행정%' OR d.department_nm LIKE '%사회%'
                 OR d.department_nm LIKE '%심리%' OR d.department_nm LIKE '%복지%'
                 OR d.department_nm LIKE '%정치%' OR d.department_nm LIKE '%법%' THEN 'Social'
            WHEN d.department_nm LIKE '%문학%' OR d.department_nm LIKE '%어%'
                 OR d.department_nm LIKE '%철학%' OR d.department_nm LIKE '%역사%'
                 OR d.department_nm LIKE '%국문%' OR d.department_nm LIKE '%영문%' THEN 'Humanities'
            WHEN d.department_nm LIKE '%수학%' OR d.department_nm LIKE '%물리%'
                 OR d.department_nm LIKE '%화학%' OR d.department_nm LIKE '%생명%'
                 OR d.department_nm LIKE '%통계%' OR d.department_nm LIKE '%생물%' THEN 'Science'
            ELSE 'General'
        END as category
    FROM tb_department d
),
category_employers AS (
    SELECT * FROM (VALUES
        ('IT', ARRAY['Samsung', 'Naver', 'Kakao', 'LG', 'SK', 'Coupang', 'Line', 'Toss']),
        ('Engineering', ARRAY['Samsung', 'Hyundai', 'LG', 'SK', 'POSCO', 'Doosan', 'Hanwha']),
        ('Medical', ARRAY['서울대병원', '세브란스병원', '삼성서울병원', '아산병원', '고려대병원', '이화의료원']),
        ('Education', ARRAY['교육청', '사립학교', 'EBS', '대성학원', '메가스터디', '청담어학원']),
        ('Arts', ARRAY['CJ ENM', 'SM Entertainment', 'HYBE', '넷플릭스코리아', '삼성디자인센터', 'NHN']),
        ('Business', ARRAY['삼성', 'SK', 'LG', '현대', '롯데', 'CJ', '신세계']),
        ('Social', ARRAY['행정안전부', '복지부', '시청', '구청', 'NGO', '사회복지관']),
        ('Humanities', ARRAY['언론사', '출판사', '번역기관', '문화기관', '연구소', '기업홍보팀']),
        ('Science', ARRAY['KIST', 'KAIST', '생명연', '화학연', '삼성바이오', 'SK바이오팜']),
        ('General', ARRAY['대기업', '공기업', '중견기업', '스타트업', '외국계기업'])
    ) AS t(category, employers)
),
category_top_roles AS (
    SELECT * FROM (VALUES
        ('IT', ARRAY['Developer', 'Data Scientist', 'AI Engineer', 'DevOps', 'Security']),
        ('Engineering', ARRAY['Engineer', 'R&D', 'Project Manager', 'Quality', 'Production']),
        ('Medical', ARRAY['의사', '간호사', '약사', '물리치료사', '임상병리사']),
        ('Education', ARRAY['교사', '교육행정', '교육컨설턴트', '학원강사', '교육기획']),
        ('Arts', ARRAY['Designer', 'Director', 'Artist', 'Producer', 'Editor']),
        ('Business', ARRAY['Manager', 'Consultant', 'Analyst', 'Marketer', 'Planner']),
        ('Social', ARRAY['공무원', '사회복지사', '상담사', '연구원', '정책분석가']),
        ('Humanities', ARRAY['기자', '번역가', '작가', '연구원', '홍보담당']),
        ('Science', ARRAY['연구원', '분석가', '개발자', '컨설턴트', '교수']),
        ('General', ARRAY['Manager', 'Consultant', 'Analyst', 'Planner', 'Coordinator'])
    ) AS t(category, roles)
)
INSERT INTO tb_alumni_cohort (
    cohort_id, department_cd, graduation_year, cohort_size,
    avg_gpa, employment_rate, avg_salary, top_employers,
    top_roles, avg_competency_scores, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    dcm.department_cd,
    year,
    (20 + (random() * 50))::int as cohort_size,
    round((3.0 + random() * 1.0)::numeric, 2) as avg_gpa,
    round((70 + random() * 25)::numeric, 1) as employment_rate,
    CASE dcm.category
        WHEN 'Medical' THEN (50000000 + (random() * 70000000))::int
        WHEN 'IT' THEN (40000000 + (random() * 40000000))::int
        WHEN 'Business' THEN (35000000 + (random() * 35000000))::int
        ELSE (30000000 + (random() * 30000000))::int
    END as avg_salary,
    ce.employers,
    ctr.roles,
    jsonb_build_object(
        'communication', round((60 + random() * 35)::numeric, 1),
        'problem_solving', round((60 + random() * 35)::numeric, 1),
        'teamwork', round((60 + random() * 35)::numeric, 1)
    ),
    'SEED',
    now()
FROM department_category_map dcm
JOIN category_employers ce ON dcm.category = ce.category
JOIN category_top_roles ctr ON dcm.category = ctr.category
CROSS JOIN generate_series(2020, 2024) as year
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================
-- 6. 확인 쿼리 (수동 실행)
-- ============================================

-- 학과별 Success Pattern 수 확인
SELECT
    d.department_nm,
    dcm.category,
    COUNT(*) as pattern_count
FROM tb_success_pattern sp
JOIN tb_department d ON sp.department_cd = d.department_cd
CROSS JOIN LATERAL (
    SELECT CASE
        WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' THEN 'IT'
        WHEN d.department_nm LIKE '%의%과' OR d.department_nm LIKE '%보건%' THEN 'Medical'
        WHEN d.department_nm LIKE '%교육%' THEN 'Education'
        ELSE 'Other'
    END as category
) dcm
GROUP BY d.department_nm, dcm.category
ORDER BY dcm.category, pattern_count DESC
LIMIT 20;
