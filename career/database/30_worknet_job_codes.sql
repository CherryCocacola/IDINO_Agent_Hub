-- ============================================
-- IDINO Career - Worknet Job Code Mapping
-- 워크넷 직업 코드 현실 데이터 매핑
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. tb_worknet_job 테이블 생성
-- 워크넷 직업 분류 체계 기반
-- ============================================

CREATE TABLE IF NOT EXISTS tb_worknet_job (
    job_cd VARCHAR(10) PRIMARY KEY,         -- 워크넷 6자리 직업코드
    job_nm VARCHAR(100) NOT NULL,           -- 직업명(국문)
    job_nm_en VARCHAR(100),                 -- 직업명(영문)
    job_category VARCHAR(50),               -- 대분류 (정보통신, 경영/사무, 연구 등)
    job_subcategory VARCHAR(50),            -- 중분류
    description TEXT,                       -- 직업 설명
    required_skills TEXT[],                 -- 필요 스킬
    related_majors TEXT[],                  -- 관련 전공
    avg_salary_entry INT,                   -- 신입 평균 연봉 (만원)
    avg_salary_experienced INT,             -- 경력 평균 연봉 (만원)
    job_outlook VARCHAR(20),                -- 전망 (growing, stable, declining)
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

COMMENT ON TABLE tb_worknet_job IS '워크넷 직업 분류 정보';
COMMENT ON COLUMN tb_worknet_job.job_cd IS '워크넷 직업코드 (6자리)';
COMMENT ON COLUMN tb_worknet_job.job_outlook IS '향후 전망 (growing/stable/declining)';

-- ============================================
-- 2. 워크넷 직업 코드 데이터 삽입
-- 2024-2025 대학생 선호 직업 기준
-- ============================================

INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
-- IT/소프트웨어 개발
('133201', '응용소프트웨어개발자', 'Application Software Developer', '정보통신', '소프트웨어개발', '애플리케이션 소프트웨어를 설계, 개발, 테스트하는 전문가', ARRAY['Java', 'Python', 'Spring', 'Database', 'Algorithm'], ARRAY['컴퓨터공학', '소프트웨어공학', '정보통신공학'], 4000, 7500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('133301', '웹개발자', 'Web Developer', '정보통신', '소프트웨어개발', '웹 애플리케이션 및 웹사이트를 개발하는 전문가', ARRAY['JavaScript', 'React', 'Node.js', 'HTML/CSS', 'Database'], ARRAY['컴퓨터공학', '소프트웨어공학', '미디어학'], 3800, 7000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('133302', '모바일앱개발자', 'Mobile App Developer', '정보통신', '소프트웨어개발', 'iOS, Android 모바일 애플리케이션 개발 전문가', ARRAY['Swift', 'Kotlin', 'Flutter', 'React Native'], ARRAY['컴퓨터공학', '소프트웨어공학', '모바일공학'], 4000, 7500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('133401', '시스템소프트웨어개발자', 'Systems Software Developer', '정보통신', '소프트웨어개발', '운영체제, 시스템 소프트웨어 개발 전문가', ARRAY['C', 'C++', 'Linux', 'OS', 'Network'], ARRAY['컴퓨터공학', '전자공학', '정보통신공학'], 4200, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),

-- 데이터/AI
('134102', '데이터분석가', 'Data Analyst', '정보통신', '데이터/AI', '데이터를 수집, 분석하여 인사이트를 도출하는 전문가', ARRAY['Python', 'SQL', 'Statistics', 'Tableau', 'Excel'], ARRAY['통계학', '컴퓨터공학', '경영학', '산업공학'], 3800, 7200, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('134103', '데이터엔지니어', 'Data Engineer', '정보통신', '데이터/AI', '데이터 파이프라인 및 인프라를 구축하는 전문가', ARRAY['Python', 'Spark', 'Hadoop', 'SQL', 'AWS'], ARRAY['컴퓨터공학', '소프트웨어공학', '산업공학'], 4200, 8500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('134201', '인공지능개발자', 'AI Developer', '정보통신', '데이터/AI', 'AI/ML 모델을 개발하고 서비스화하는 전문가', ARRAY['Python', 'TensorFlow', 'PyTorch', 'Machine Learning', 'Deep Learning'], ARRAY['컴퓨터공학', '통계학', '수학', '전자공학'], 4500, 9000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('134202', '머신러닝엔지니어', 'Machine Learning Engineer', '정보통신', '데이터/AI', 'ML 모델의 개발, 배포, 운영을 담당하는 전문가', ARRAY['Python', 'TensorFlow', 'MLOps', 'Kubernetes', 'Cloud'], ARRAY['컴퓨터공학', '통계학', '수학'], 4500, 9500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 정보보안/인프라
('134301', '정보보안전문가', 'Information Security Specialist', '정보통신', '정보보안', '정보시스템의 보안을 담당하는 전문가', ARRAY['Network Security', 'Penetration Testing', 'Security Tools', 'Compliance'], ARRAY['정보보호학', '컴퓨터공학', '정보통신공학'], 4000, 8000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('134401', '네트워크엔지니어', 'Network Engineer', '정보통신', '네트워크/인프라', '네트워크 설계, 구축, 운영을 담당하는 전문가', ARRAY['Cisco', 'Network Protocol', 'Firewall', 'VPN', 'Cloud'], ARRAY['정보통신공학', '컴퓨터공학', '전자공학'], 3800, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('134402', '클라우드엔지니어', 'Cloud Engineer', '정보통신', '네트워크/인프라', '클라우드 인프라 설계 및 운영 전문가', ARRAY['AWS', 'Azure', 'GCP', 'Kubernetes', 'Docker', 'Terraform'], ARRAY['컴퓨터공학', '정보통신공학'], 4300, 8500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('134403', 'DevOps엔지니어', 'DevOps Engineer', '정보통신', '네트워크/인프라', 'CI/CD 파이프라인 및 인프라 자동화 전문가', ARRAY['Docker', 'Kubernetes', 'Jenkins', 'AWS', 'Linux'], ARRAY['컴퓨터공학', '소프트웨어공학'], 4200, 8500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 경영/사무
('122101', '경영컨설턴트', 'Management Consultant', '경영/사무', '경영/컨설팅', '기업의 경영 전략 및 운영 개선을 컨설팅하는 전문가', ARRAY['Problem Solving', 'Data Analysis', 'Presentation', 'Communication'], ARRAY['경영학', '경제학', '산업공학'], 4500, 10000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('122301', '마케터', 'Marketing Specialist', '경영/사무', '마케팅/광고', '제품 및 서비스의 마케팅 전략을 기획하고 실행하는 전문가', ARRAY['Digital Marketing', 'Data Analysis', 'Content Creation', 'SNS'], ARRAY['경영학', '광고학', '미디어학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('122302', '디지털마케터', 'Digital Marketing Specialist', '경영/사무', '마케팅/광고', '온라인 채널을 통한 마케팅 전략 전문가', ARRAY['Google Analytics', 'SEO/SEM', 'Social Media', 'Content Marketing'], ARRAY['경영학', '광고학', '미디어학'], 3600, 6800, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('123101', '재무분석가', 'Financial Analyst', '경영/사무', '금융/재무', '기업의 재무 상태 분석 및 투자 의사결정 지원 전문가', ARRAY['Financial Modeling', 'Excel', 'Valuation', 'Accounting'], ARRAY['경영학', '경제학', '회계학', '금융학'], 4000, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('123201', '회계사', 'Accountant', '경영/사무', '금융/재무', '회계 및 세무 업무를 수행하는 전문가', ARRAY['Accounting', 'Tax', 'Audit', 'Excel'], ARRAY['회계학', '경영학', '세무학'], 3800, 8500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),

-- 디자인/UX
('285201', 'UI/UX디자이너', 'UI/UX Designer', '예술/디자인', 'UI/UX설계', '사용자 인터페이스 및 경험을 설계하는 전문가', ARRAY['Figma', 'Adobe XD', 'User Research', 'Prototyping'], ARRAY['시각디자인', '산업디자인', '미디어학', '컴퓨터공학'], 3500, 6500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('285202', '그래픽디자이너', 'Graphic Designer', '예술/디자인', '시각디자인', '시각적 콘텐츠를 제작하는 전문가', ARRAY['Photoshop', 'Illustrator', 'InDesign', 'Typography'], ARRAY['시각디자인', '광고학', '미디어학'], 3200, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('285301', '제품디자이너', 'Product Designer', '예술/디자인', '제품디자인', '제품의 형태와 기능을 설계하는 전문가', ARRAY['3D Modeling', 'Sketch', 'Prototyping', 'User Research'], ARRAY['산업디자인', '제품디자인'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),

-- 연구/개발
('211101', '자연과학연구원', 'Natural Science Researcher', '연구', '자연과학연구', '자연과학 분야의 연구를 수행하는 전문가', ARRAY['Research Methodology', 'Data Analysis', 'Laboratory Skills'], ARRAY['물리학', '화학', '생명과학', '수학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('211201', '생명과학연구원', 'Life Science Researcher', '연구', '생명과학연구', '생명과학 분야의 연구를 수행하는 전문가', ARRAY['Molecular Biology', 'Cell Culture', 'Data Analysis'], ARRAY['생명과학', '생물학', '생명공학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('212101', '전자공학기술자', 'Electronics Engineer', '연구', '공학연구', '전자 시스템 및 장치를 설계하고 개발하는 전문가', ARRAY['Circuit Design', 'Embedded Systems', 'PCB Design'], ARRAY['전자공학', '전기공학', '정보통신공학'], 4000, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('212201', '기계공학기술자', 'Mechanical Engineer', '연구', '공학연구', '기계 시스템을 설계하고 개발하는 전문가', ARRAY['CAD', 'Mechanical Design', '3D Modeling', 'Manufacturing'], ARRAY['기계공학', '산업공학', '항공공학'], 4000, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),

-- 교육
('251101', '대학교수', 'University Professor', '교육', '고등교육', '대학에서 교육 및 연구를 수행하는 전문가', ARRAY['Research', 'Teaching', 'Academic Writing'], ARRAY['전공무관(박사학위 필요)'], 4500, 8500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('251201', '교육콘텐츠개발자', 'Educational Content Developer', '교육', '교육기획', '교육 콘텐츠를 기획하고 개발하는 전문가', ARRAY['Content Creation', 'Instructional Design', 'E-learning'], ARRAY['교육학', '교육공학', '미디어학'], 3200, 5500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),

-- 기획/PM
('133501', 'IT기획자', 'IT Planner', '정보통신', 'IT기획/PM', 'IT 프로젝트를 기획하고 관리하는 전문가', ARRAY['Project Management', 'Requirements Analysis', 'Communication'], ARRAY['컴퓨터공학', '경영학', '산업공학'], 4000, 7500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('133502', '프로덕트매니저', 'Product Manager', '정보통신', 'IT기획/PM', '제품의 기획부터 출시까지 전 과정을 관리하는 전문가', ARRAY['Product Strategy', 'Data Analysis', 'User Research', 'Agile'], ARRAY['경영학', '컴퓨터공학', '산업공학'], 4200, 8000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('133503', '서비스기획자', 'Service Planner', '정보통신', 'IT기획/PM', '서비스를 기획하고 설계하는 전문가', ARRAY['Service Design', 'UX Writing', 'Data Analysis'], ARRAY['경영학', '컴퓨터공학', '미디어학'], 3800, 7000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP)
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
-- 3. tb_role에 worknet_code 컬럼 추가 및 업데이트
-- 기존 5자리 코드를 6자리 워크넷 코드로 매핑
-- ============================================

-- 컬럼이 없으면 추가
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

UPDATE tb_role SET worknet_code = '133201' WHERE role_cd = 'ROLE001'; -- 백엔드개발자 → 응용소프트웨어개발자
UPDATE tb_role SET worknet_code = '133301' WHERE role_cd = 'ROLE002'; -- 프론트엔드개발자 → 웹개발자
UPDATE tb_role SET worknet_code = '134102' WHERE role_cd = 'ROLE003'; -- 데이터분석가
UPDATE tb_role SET worknet_code = '134103' WHERE role_cd = 'ROLE004'; -- 데이터엔지니어
UPDATE tb_role SET worknet_code = '134201' WHERE role_cd = 'ROLE005'; -- AI엔지니어 → 인공지능개발자
UPDATE tb_role SET worknet_code = '134403' WHERE role_cd = 'ROLE006'; -- DevOps엔지니어
UPDATE tb_role SET worknet_code = '133201' WHERE role_cd = 'ROLE007'; -- 풀스택개발자 → 응용소프트웨어개발자
UPDATE tb_role SET worknet_code = '134301' WHERE role_cd = 'ROLE008'; -- 보안전문가 → 정보보안전문가
UPDATE tb_role SET worknet_code = '122101' WHERE role_cd = 'ROLE009'; -- 경영컨설턴트
UPDATE tb_role SET worknet_code = '122302' WHERE role_cd = 'ROLE010'; -- 마케팅전문가 → 디지털마케터
UPDATE tb_role SET worknet_code = '285201' WHERE role_cd = 'ROLE011'; -- UI/UX디자이너
UPDATE tb_role SET worknet_code = '133502' WHERE role_cd = 'ROLE012'; -- 프로덕트매니저

-- ============================================
-- 4. tb_student_interested_job 테이블 생성
-- 학생별 관심 직업 (워크넷 코드 기반)
-- ============================================

CREATE TABLE IF NOT EXISTS tb_student_interested_job (
    interested_job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    job_cd VARCHAR(10) REFERENCES tb_worknet_job(job_cd),
    interest_level INT DEFAULT 3 CHECK (interest_level BETWEEN 1 AND 5), -- 1: 낮음 ~ 5: 매우높음
    source VARCHAR(50), -- 'worknet_diagnosis', 'manual', 'recommendation'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(student_id, job_cd)
);

COMMENT ON TABLE tb_student_interested_job IS '학생별 관심 직업';
COMMENT ON COLUMN tb_student_interested_job.interest_level IS '관심도 (1: 낮음 ~ 5: 매우높음)';
COMMENT ON COLUMN tb_student_interested_job.source IS '데이터 출처 (worknet_diagnosis, manual, recommendation)';

CREATE INDEX idx_student_interested_job_student ON tb_student_interested_job(student_id);
CREATE INDEX idx_student_interested_job_job ON tb_student_interested_job(job_cd);

-- ============================================
-- 5. 학생별 관심 직업 데이터 생성
-- 전공 기반 관심 직업 자동 매핑
-- ============================================

-- 컴퓨터공학과 학생 (DEPT001) - 2023, 2024, 2025 입학
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '133201' THEN 5  -- 응용소프트웨어개발자
        WHEN '133301' THEN 4  -- 웹개발자
        WHEN '134201' THEN 4  -- 인공지능개발자
        WHEN '134102' THEN 3  -- 데이터분석가
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd = 'DEPT001'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('133201', '133301', '134201', '134102', '134403')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 소프트웨어학과 학생 (DEPT002)
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '133301' THEN 5  -- 웹개발자
        WHEN '133302' THEN 5  -- 모바일앱개발자
        WHEN '133201' THEN 4  -- 응용소프트웨어개발자
        WHEN '133502' THEN 3  -- 프로덕트매니저
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd = 'DEPT002'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('133301', '133302', '133201', '133502', '285201')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- AI학과 학생 (DEPT003)
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '134201' THEN 5  -- 인공지능개발자
        WHEN '134202' THEN 5  -- 머신러닝엔지니어
        WHEN '134102' THEN 4  -- 데이터분석가
        WHEN '134103' THEN 4  -- 데이터엔지니어
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd = 'DEPT003'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('134201', '134202', '134102', '134103', '133201')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 경영학과 학생 (DEPT014)
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '122101' THEN 5  -- 경영컨설턴트
        WHEN '122302' THEN 4  -- 디지털마케터
        WHEN '123101' THEN 4  -- 재무분석가
        WHEN '133502' THEN 3  -- 프로덕트매니저
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd = 'DEPT014'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('122101', '122302', '123101', '133502', '134102')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 통계학과 학생 (DEPT013)
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '134102' THEN 5  -- 데이터분석가
        WHEN '134103' THEN 4  -- 데이터엔지니어
        WHEN '134201' THEN 4  -- 인공지능개발자
        WHEN '123101' THEN 3  -- 재무분석가
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd = 'DEPT013'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('134102', '134103', '134201', '123101', '211101')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 디자인학과 학생 (DEPT025)
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd,
    CASE j.job_cd
        WHEN '285201' THEN 5  -- UI/UX디자이너
        WHEN '285202' THEN 4  -- 그래픽디자이너
        WHEN '285301' THEN 4  -- 제품디자이너
        WHEN '133503' THEN 3  -- 서비스기획자
        ELSE 3
    END,
    'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd = 'DEPT025'
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('285201', '285202', '285301', '133503', '133301')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 기타 학과 학생 (범용)
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, source, ins_user_id, ins_dt)
SELECT s.student_id, j.job_cd, 3, 'worknet_diagnosis', 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_worknet_job j
WHERE s.department_cd NOT IN ('DEPT001', 'DEPT002', 'DEPT003', 'DEPT013', 'DEPT014', 'DEPT025')
    AND s.admission_year IN (2023, 2024, 2025)
    AND j.job_cd IN ('133201', '122302', '134102')  -- 개발자, 마케터, 데이터분석가 - 범용
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- ============================================
-- 6. tb_worknet_diagnosis job_match_scores 업데이트
-- ROLE 코드 대신 실제 워크넷 코드 사용
-- (테이블이 존재하는 경우에만 실행)
-- ============================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'idino_career' AND table_name = 'tb_worknet_diagnosis'
    ) THEN
        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"133201": 85, "134201": 78, "133301": 72}'::jsonb
        WHERE student_id IN (SELECT student_id FROM tb_student WHERE department_cd = 'DEPT001');

        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"133301": 82, "133302": 80, "133201": 75}'::jsonb
        WHERE student_id IN (SELECT student_id FROM tb_student WHERE department_cd = 'DEPT002');

        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"134201": 80, "134202": 78, "134103": 75}'::jsonb
        WHERE student_id IN (SELECT student_id FROM tb_student WHERE department_cd = 'DEPT003');

        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"122101": 88, "122302": 82, "123101": 78}'::jsonb
        WHERE student_id IN (SELECT student_id FROM tb_student WHERE department_cd = 'DEPT014');

        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"134102": 85, "134103": 80, "134201": 75}'::jsonb
        WHERE student_id IN (SELECT student_id FROM tb_student WHERE department_cd = 'DEPT013');

        UPDATE tb_worknet_diagnosis
        SET job_match_scores = '{"285201": 90, "285202": 78, "133503": 65}'::jsonb
        WHERE student_id IN (SELECT student_id FROM tb_student WHERE department_cd = 'DEPT025');
    END IF;
END $$;

-- ============================================
-- 7. 인덱스 생성
-- ============================================

CREATE INDEX IF NOT EXISTS idx_worknet_job_category ON tb_worknet_job(job_category);
CREATE INDEX IF NOT EXISTS idx_worknet_job_outlook ON tb_worknet_job(job_outlook);
CREATE INDEX IF NOT EXISTS idx_role_worknet_code ON tb_role(worknet_code);

-- ============================================
-- 확인 쿼리
-- ============================================

-- SELECT count(*) as total_jobs FROM tb_worknet_job;
-- SELECT count(*) as total_interested FROM tb_student_interested_job;
-- SELECT s.student_id, s.student_nm, w.job_nm, i.interest_level
-- FROM tb_student s
-- JOIN tb_student_interested_job i ON s.student_id = i.student_id
-- JOIN tb_worknet_job w ON i.job_cd = w.job_cd
-- WHERE s.admission_year IN (2023, 2024, 2025)
-- ORDER BY s.student_id, i.interest_level DESC
-- LIMIT 50;
