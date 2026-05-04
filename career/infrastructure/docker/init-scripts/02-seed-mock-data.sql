-- ============================================
-- IDINO Career System - Mock Data Seeding
-- ============================================

-- ============================================
-- AUTH: Sample Users
-- ============================================

SET search_path TO idino_career_auth;

INSERT INTO tb_users (user_id, username, email, password_hash, role_level) VALUES
    ('11111111-1111-1111-1111-111111111111', 'admin', 'admin@university.ac.kr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.aqPhwPKFDB7tP.', 1),
    ('22222222-2222-2222-2222-222222222222', 'professor_kim', 'kim@university.ac.kr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.aqPhwPKFDB7tP.', 3),
    ('33333333-3333-3333-3333-333333333333', 'student_hong', 'hong@student.ac.kr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.aqPhwPKFDB7tP.', 5),
    ('44444444-4444-4444-4444-444444444444', 'student_lee', 'lee@student.ac.kr', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.aqPhwPKFDB7tP.', 5)
ON CONFLICT (user_id) DO NOTHING;

-- ============================================
-- STUDENT: Departments and Sample Students
-- ============================================

SET search_path TO idino_career_student;

-- Departments
INSERT INTO tb_departments (department_id, department_name, college) VALUES
    ('CS001', '컴퓨터공학과', '공과대학'),
    ('SW001', '소프트웨어학과', '소프트웨어융합대학'),
    ('AI001', '인공지능학과', '소프트웨어융합대학'),
    ('BA001', '경영학과', '경영대학'),
    ('DS001', '데이터사이언스학과', '소프트웨어융합대학')
ON CONFLICT (department_id) DO NOTHING;

-- Sample Students
INSERT INTO tb_students (student_id, user_id, name, department_id, major, grade, total_credits, gpa, career_goal, target_job_codes, enrollment_year, enrollment_semester) VALUES
    ('2021001234', '33333333-3333-3333-3333-333333333333', '홍길동', 'SW001', '소프트웨어학', 3, 85, 3.75, '백엔드 개발자', '["134010", "134020"]', 2021, 1),
    ('2022005678', '44444444-4444-4444-4444-444444444444', '이영희', 'AI001', '인공지능', 2, 45, 4.10, 'AI 엔지니어', '["134030", "134040"]', 2022, 1),
    ('2020003456', NULL, '김철수', 'CS001', '컴퓨터공학', 4, 120, 3.50, '풀스택 개발자', '["134010"]', 2020, 1),
    ('2023007890', NULL, '박민수', 'DS001', '데이터사이언스', 1, 18, 3.90, '데이터 분석가', '["133010"]', 2023, 1)
ON CONFLICT (student_id) DO NOTHING;

-- Sample Course Records
INSERT INTO tb_course_records (student_id, course_code, course_name, semester, credits, grade, grade_point, course_type, competency_mappings) VALUES
    ('2021001234', 'SW201', '자료구조', '2022-1', 3, 'A+', 4.5, '전공필수', '{"C001": 0.4, "C002": 0.3, "C003": 0.3}'),
    ('2021001234', 'SW202', '알고리즘', '2022-2', 3, 'A0', 4.0, '전공필수', '{"C001": 0.5, "C002": 0.3, "C003": 0.2}'),
    ('2021001234', 'SW301', '소프트웨어공학', '2023-1', 3, 'B+', 3.5, '전공필수', '{"C002": 0.4, "C004": 0.4, "C003": 0.2}'),
    ('2021001234', 'SW302', '데이터베이스', '2023-1', 3, 'A0', 4.0, '전공필수', '{"C001": 0.3, "C002": 0.4, "C003": 0.3}'),
    ('2022005678', 'AI101', 'AI개론', '2023-1', 3, 'A+', 4.5, '전공필수', '{"C001": 0.4, "C003": 0.3, "C004": 0.3}'),
    ('2022005678', 'AI201', '머신러닝', '2023-2', 3, 'A+', 4.5, '전공필수', '{"C001": 0.5, "C003": 0.3, "C004": 0.2}')
ON CONFLICT DO NOTHING;

-- Sample Extracurricular Activities
INSERT INTO tb_extracurricular_activities (student_id, activity_name, activity_type, status, start_date, end_date, hours_completed, competency_gains) VALUES
    ('2021001234', '네이버 인턴십', '인턴십', 'completed', '2023-07-01', '2023-08-31', 320, '{"C001": 15, "C002": 20, "C004": 10}'),
    ('2021001234', 'SW 봉사단', '봉사활동', 'completed', '2023-03-01', '2023-06-30', 80, '{"C004": 10, "C003": 5}'),
    ('2021001234', '해커톤 대회', '공모전', 'completed', '2023-09-15', '2023-09-17', 48, '{"C001": 10, "C002": 15, "C003": 10}'),
    ('2022005678', 'AI 스터디', '동아리', 'in_progress', '2023-09-01', NULL, 40, '{"C001": 8, "C003": 5}')
ON CONFLICT DO NOTHING;

-- Sample Personal Achievements
INSERT INTO tb_personal_achievements (student_id, achievement_type, name, issuer, acquired_date, score, level) VALUES
    ('2021001234', '자격증', '정보처리기사', '한국산업인력공단', '2023-06-15', NULL, '기사'),
    ('2021001234', '어학', 'TOEIC', 'ETS', '2023-05-20', '850', NULL),
    ('2021001234', '자격증', 'SQLD', '한국데이터산업진흥원', '2023-08-10', NULL, NULL),
    ('2022005678', '어학', 'TOEIC', 'ETS', '2023-11-10', '920', NULL),
    ('2022005678', '수상', 'AI 경진대회 우수상', '대학교', '2023-11-25', NULL, NULL)
ON CONFLICT DO NOTHING;

-- ============================================
-- COMPETENCY: Definitions and Sample Data
-- ============================================

SET search_path TO idino_career_competency;

-- Core Competency Definitions (4대 핵심역량)
INSERT INTO tb_competency_definitions (competency_id, competency_name, competency_name_en, category, description, max_score, icon_name, color_code) VALUES
    ('C001', '전문지식역량', 'Professional Knowledge', '대학핵심역량', '전공 분야의 깊이 있는 이론적 지식과 실무 능력', 100, 'book', '#4F46E5'),
    ('C002', '실무수행역량', 'Practical Skills', '대학핵심역량', '실제 업무 환경에서의 문제 해결 및 프로젝트 수행 능력', 100, 'briefcase', '#10B981'),
    ('C003', '자기개발역량', 'Self Development', '대학핵심역량', '지속적인 학습과 성장을 위한 자기주도적 역량', 100, 'trending-up', '#F59E0B'),
    ('C004', '대인관계역량', 'Interpersonal Skills', '대학핵심역량', '팀워크, 의사소통, 리더십 등 협업 역량', 100, 'users', '#EC4899')
ON CONFLICT (competency_id) DO NOTHING;

-- Sample Competency Assessments
INSERT INTO tb_competency_assessments (student_id, assessment_date, assessment_type, raw_scores, weighted_scores, percentile_ranks, total_score) VALUES
    ('2021001234', '2024-01-15', 'curriculum',
     '{"C001": 78, "C002": 82, "C003": 70, "C004": 75}',
     '{"C001": 78, "C002": 82, "C003": 70, "C004": 75}',
     '{"C001": 72, "C002": 78, "C003": 65, "C004": 70}',
     76.25),
    ('2022005678', '2024-01-15', 'curriculum',
     '{"C001": 85, "C002": 70, "C003": 80, "C004": 65}',
     '{"C001": 85, "C002": 70, "C003": 80, "C004": 65}',
     '{"C001": 82, "C002": 65, "C003": 75, "C004": 60}',
     75.00)
ON CONFLICT DO NOTHING;

-- ============================================
-- ALUMNI: Statistics and Patterns
-- ============================================

SET search_path TO idino_career_alumni;

-- Sample Alumni Statistics
INSERT INTO tb_alumni_statistics (department_id, graduation_year, job_category, avg_gpa, avg_credits, common_certifications, common_activities, competency_profile, employment_rate, sample_size, data_year) VALUES
    ('SW001', 2023, '백엔드 개발자', 3.65, 135,
     '["정보처리기사", "SQLD", "AWS SAA"]',
     '["인턴십", "해커톤", "오픈소스 기여"]',
     '{"C001": 82, "C002": 85, "C003": 78, "C004": 75}',
     92.5, 45, 2024),
    ('SW001', 2023, '프론트엔드 개발자', 3.55, 132,
     '["정보처리기사", "웹디자인기능사"]',
     '["UI/UX 프로젝트", "동아리", "공모전"]',
     '{"C001": 78, "C002": 80, "C003": 82, "C004": 78}',
     90.0, 30, 2024),
    ('AI001', 2023, 'AI 엔지니어', 3.80, 138,
     '["정보처리기사", "빅데이터분석기사", "TOEIC 850+"]',
     '["연구실 인턴", "AI 경진대회", "논문 작성"]',
     '{"C001": 88, "C002": 82, "C003": 85, "C004": 72}',
     88.0, 25, 2024)
ON CONFLICT DO NOTHING;

-- Sample Success Patterns
INSERT INTO tb_success_patterns (department_id, job_category, pattern_name, pattern_description, required_courses, required_activities, required_certifications, min_gpa, competency_requirements, success_rate, sample_size) VALUES
    ('SW001', '백엔드 개발자', '실무형 개발자 패턴', '인턴십과 프로젝트 경험을 중시하는 실무 지향 경로',
     '["자료구조", "알고리즘", "데이터베이스", "운영체제", "소프트웨어공학"]',
     '["인턴십 1회 이상", "해커톤 참여", "개인 프로젝트 3개 이상"]',
     '["정보처리기사"]',
     3.5, '{"C001": 75, "C002": 80, "C003": 70, "C004": 70}',
     85.0, 35),
    ('AI001', 'AI 엔지니어', '연구형 AI 전문가 패턴', '연구실 경험과 깊이 있는 이론 학습을 강조하는 경로',
     '["머신러닝", "딥러닝", "수학", "통계학", "자연어처리"]',
     '["연구실 참여", "논문 작성", "AI 경진대회"]',
     '["빅데이터분석기사", "정보처리기사"]',
     3.7, '{"C001": 85, "C002": 75, "C003": 80, "C004": 70}',
     80.0, 20)
ON CONFLICT DO NOTHING;

-- ============================================
-- INTEGRATION: Mock External Data
-- ============================================

SET search_path TO idino_career_integration;

-- Worknet Job Data
INSERT INTO tb_worknet_jobs (job_code, job_name, job_category, description, main_tasks, required_education, required_certifications, required_skills, related_majors, salary_info, employment_outlook, growth_rate) VALUES
    ('134010', '백엔드 개발자', 'IT/소프트웨어',
     '서버 측 애플리케이션과 데이터베이스를 설계하고 개발하는 전문가',
     '서버 애플리케이션 개발, API 설계, 데이터베이스 관리, 시스템 최적화',
     '대졸 이상',
     '["정보처리기사", "SQLD", "클라우드 자격증"]',
     '["Python", "Java", "SQL", "AWS/GCP", "Docker"]',
     '["컴퓨터공학", "소프트웨어학", "정보통신공학"]',
     '{"entry": "3500-4500만원", "mid": "5000-7000만원", "senior": "8000만원+"}',
     '매우 좋음',
     15.2),
    ('134020', '프론트엔드 개발자', 'IT/소프트웨어',
     '웹 및 모바일 사용자 인터페이스를 설계하고 구현하는 전문가',
     'UI 개발, 사용자 경험 최적화, 반응형 웹 구현',
     '대졸 이상',
     '["정보처리기사", "웹디자인기능사"]',
     '["JavaScript", "React", "TypeScript", "CSS", "HTML"]',
     '["컴퓨터공학", "소프트웨어학", "디자인학"]',
     '{"entry": "3200-4200만원", "mid": "4500-6500만원", "senior": "7500만원+"}',
     '좋음',
     12.8),
    ('134030', 'AI 엔지니어', 'IT/소프트웨어',
     '인공지능 모델을 설계, 개발, 배포하는 전문가',
     '머신러닝 모델 개발, 데이터 파이프라인 구축, MLOps 운영',
     '대졸 이상 (석사 우대)',
     '["빅데이터분석기사", "정보처리기사"]',
     '["Python", "TensorFlow", "PyTorch", "MLOps", "SQL"]',
     '["인공지능학", "컴퓨터공학", "데이터사이언스"]',
     '{"entry": "4000-5000만원", "mid": "6000-8000만원", "senior": "1억원+"}',
     '매우 좋음',
     25.5),
    ('134040', '데이터 사이언티스트', 'IT/소프트웨어',
     '데이터를 분석하고 인사이트를 도출하는 전문가',
     '데이터 분석, 통계 모델링, 비즈니스 인사이트 도출, 시각화',
     '대졸 이상',
     '["빅데이터분석기사", "ADsP"]',
     '["Python", "R", "SQL", "Tableau", "통계분석"]',
     '["데이터사이언스", "통계학", "수학"]',
     '{"entry": "3800-4800만원", "mid": "5500-7500만원", "senior": "9000만원+"}',
     '매우 좋음',
     20.3),
    ('133010', '데이터 분석가', 'IT/데이터',
     '비즈니스 데이터를 분석하여 의사결정을 지원하는 전문가',
     '데이터 수집/정제, 분석 리포트 작성, 대시보드 구축',
     '대졸 이상',
     '["ADsP", "SQLD"]',
     '["SQL", "Excel", "Tableau", "Python"]',
     '["경영학", "통계학", "데이터사이언스"]',
     '{"entry": "3200-4000만원", "mid": "4500-6000만원", "senior": "7000만원+"}',
     '좋음',
     18.7)
ON CONFLICT (job_code) DO NOTHING;

-- HRD Training Data
INSERT INTO tb_hrd_trainings (training_id, training_name, training_type, provider, related_job_codes, duration_hours, cost, support_available) VALUES
    ('HRD001', 'AWS 클라우드 아키텍트 과정', '직무향상', 'AWS 공인 교육센터', '["134010", "134030"]', 120, 2500000, true),
    ('HRD002', '빅데이터 분석 전문가 양성', '국가기간전략훈련', '한국IT교육원', '["134040", "133010"]', 960, 0, true),
    ('HRD003', 'AI/머신러닝 부트캠프', '직무향상', '패스트캠퍼스', '["134030", "134040"]', 480, 3000000, true),
    ('HRD004', '풀스택 웹개발자 양성과정', '국가기간전략훈련', '그린컴퓨터아카데미', '["134010", "134020"]', 1200, 0, true)
ON CONFLICT (training_id) DO NOTHING;

-- ============================================
-- Reset search_path
-- ============================================

RESET search_path;

DO $$
BEGIN
    RAISE NOTICE 'Mock data seeding completed!';
END $$;
