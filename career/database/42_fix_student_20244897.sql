-- =====================================================
-- Fix Student 20244897 (하**, 의예과) Data
-- Issues: missing grades, IT-related skills/simulation/portfolio
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Step 1: Update student profile (phone, email)
-- =====================================================
UPDATE tb_student
SET phone = '010-9876-4897',
    email = 'ha4897@inje.ac.kr',
    upd_user_id = 'SYSTEM',
    upd_dt = NOW()
WHERE student_id = '20244897';

-- =====================================================
-- Step 2: Create grade records for all 28 enrollments
-- 의예과 학생 합리적 성적: A+~B+ (GPA ~3.8 목표)
-- =====================================================

-- Delete any existing grades first (safety)
DELETE FROM tb_grade WHERE student_id = '20244897';

-- 1학기 과목 (18 enrollments, 10 distinct courses with duplicates)
-- 영어회화 (ARA030, 2학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '6be1537c-ac9e-5c8a-bcd9-0e87b35f96b8', '20244897', 'ARA030', '1', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());
-- 영어회화 (ARA030, 2학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '446b6795-4f34-5387-864c-fd2583c231d4', '20244897', 'ARA030', '1', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());

-- 인간심리의이해 (AOA625, 3학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '1ea3bf3c-09bb-5daa-b9ec-a789184743bc', '20244897', 'AOA625', '1', 'B+', 3.50, 3, 'N', 'SYSTEM', NOW());
-- 인간심리의이해 (AOA625, 3학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'da32f855-e4da-5f5a-a985-ce6dccefd4a9', '20244897', 'AOA625', '1', 'B+', 3.50, 3, 'N', 'SYSTEM', NOW());

-- 과학의 역사 (AMA441, 2학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'c1c06fe7-e3bc-54c1-97eb-fabb427ba318', '20244897', 'AMA441', '1', 'A+', 4.50, 2, 'N', 'SYSTEM', NOW());
-- 과학의 역사 (AMA441, 2학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '996cf88a-5814-58d3-ab91-e7bdcdfe9285', '20244897', 'AMA441', '1', 'A+', 4.50, 2, 'N', 'SYSTEM', NOW());

-- 문화와 예술 (ARB408, 2학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'e003bb38-5b45-5cc3-a843-9555eb43369a', '20244897', 'ARB408', '1', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());
-- 문화와 예술 (ARB408, 2학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '8ae8db53-4dab-5812-a0fe-f66fc2c8dfce', '20244897', 'ARB408', '1', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());

-- 의료와 문화 (AMA337, 2학점) - single enrollment
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'b2d0bb86-c7f7-5d4a-88db-9a7744e8ce04', '20244897', 'AMA337', '1', 'A+', 4.50, 2, 'N', 'SYSTEM', NOW());

-- 의학과 문학 (AMA341, 2학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '508a33ac-b960-54f9-ae76-ffe770c7c76b', '20244897', 'AMA341', '1', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());
-- 의학과 문학 (AMA341, 2학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'ba15c83e-3f29-529d-acc7-181c07d60000', '20244897', 'AMA341', '1', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());

-- 창의력 개발 디지털 디딤돌 (AMA484, 2학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'eef41a18-cb4a-5f2f-bca3-61629f1880cf', '20244897', 'AMA484', '1', 'B+', 3.50, 2, 'N', 'SYSTEM', NOW());
-- 창의력 개발 디지털 디딤돌 (AMA484, 2학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '422e6d53-4fe6-5a7e-ab2a-41c7269987cf', '20244897', 'AMA484', '1', 'B+', 3.50, 2, 'N', 'SYSTEM', NOW());

-- 인제 플랫폼 코스 (AMA475, 1학점) - single enrollment
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '1ca0e2f4-650b-58ac-99da-f93cde6590ca', '20244897', 'AMA475', '1', 'A+', 4.50, 1, 'N', 'SYSTEM', NOW());

-- 의학입문1 (AMA324, 3학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'e2d3aa1d-4630-5d6b-b888-2d2b13754a97', '20244897', 'AMA324', '1', 'A+', 4.50, 3, 'N', 'SYSTEM', NOW());
-- 의학입문1 (AMA324, 3학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'b753ddfb-960d-5cbf-817b-d71c575c1461', '20244897', 'AMA324', '1', 'A+', 4.50, 3, 'N', 'SYSTEM', NOW());

-- 생물학 I (AMA265, 3학점) - enrollment 1
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'd0299d02-5fc3-59ce-b6c1-b94ba664e12f', '20244897', 'AMA265', '1', 'A0', 4.00, 3, 'N', 'SYSTEM', NOW());
-- 생물학 I (AMA265, 3학점) - enrollment 2
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'aa72970d-dc55-5288-b9e7-a6f1a4a09a19', '20244897', 'AMA265', '1', 'A0', 4.00, 3, 'N', 'SYSTEM', NOW());

-- 2학기 과목 (10 enrollments, 10 distinct courses - no duplicates)
-- 영어발표 (ARA146, 2학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '39e184a9-fc2d-5068-a549-71989f8e8452', '20244897', 'ARA146', '2', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());

-- 생활속의심리학 (AOA496, 3학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '3e256538-d1d5-5c06-83b4-682371822d77', '20244897', 'AOA496', '2', 'A0', 4.00, 3, 'N', 'SYSTEM', NOW());

-- 인간심리의이해 (AOA625, 3학점) - 2학기 재수강
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '31911687-6161-5621-9db0-0df732d3a370', '20244897', 'AOA625', '2', 'A0', 4.00, 3, 'N', 'SYSTEM', NOW());

-- 현대사회와 시민 (ARB391, 2학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '875ad4a7-4ed2-5e7b-96a8-01b7d43be642', '20244897', 'ARB391', '2', 'B+', 3.50, 2, 'N', 'SYSTEM', NOW());

-- 의학의 역사 (AMA430, 2학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '6077905e-f67a-59a1-a2b7-8d65ee49080a', '20244897', 'AMA430', '2', 'A+', 4.50, 2, 'N', 'SYSTEM', NOW());

-- 의학과 창의적 상상력 (AMA340, 2학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '4f1299e0-037b-5401-81d0-236cc0a97342', '20244897', 'AMA340', '2', 'A0', 4.00, 2, 'N', 'SYSTEM', NOW());

-- 노년의 삶과 죽음 (AMA491, 2학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '785e1dbd-b5c3-5804-8ecb-efacaa578e79', '20244897', 'AMA491', '2', 'A+', 4.50, 2, 'N', 'SYSTEM', NOW());

-- 좋은 의사 되기 (AMA449, 2학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'f79b31c3-5443-5f9f-8a84-8448614aec1f', '20244897', 'AMA449', '2', 'A+', 4.50, 2, 'N', 'SYSTEM', NOW());

-- 의학입문2 (AMA325, 3학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'deb8af97-7f05-531f-8290-d5e4671aa9ef', '20244897', 'AMA325', '2', 'A+', 4.50, 3, 'N', 'SYSTEM', NOW());

-- 생물학 II (AMA266, 3학점)
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), 'efcc485a-79a9-568b-9731-921e93b1b082', '20244897', 'AMA266', '2', 'A0', 4.00, 3, 'N', 'SYSTEM', NOW());


-- =====================================================
-- Step 3: Create cumulative summary and grade summary
-- =====================================================

-- Delete any existing summary data first
DELETE FROM tb_cumulative_summary WHERE student_id = '20244897';
DELETE FROM tb_grade_summary WHERE student_id = '20244897';

-- Cumulative summary
-- 1학기: 18 enrollments, credits total = sum of all enrollment credits
-- But since there are duplicate enrollments, we compute based on unique courses per term
-- Actually the grade records are per enrollment, so total credits = sum of all grade credits_earned
-- Let the system calculate from grades, but we also provide summary for fallback

-- 1학기 grade_summary (18 enrollments = 42 credits from grades)
INSERT INTO tb_grade_summary (summary_id, student_id, term_cd, total_credits, earned_credits, gpa, major_gpa, class_rank, total_students, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '20244897', '1', 42, 42, 4.07, 4.25, 5, 40, 'SYSTEM', NOW());

-- 2학기 grade_summary (10 enrollments = 24 credits from grades)
INSERT INTO tb_grade_summary (summary_id, student_id, term_cd, total_credits, earned_credits, gpa, major_gpa, class_rank, total_students, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '20244897', '2', 24, 24, 4.18, 4.38, 3, 40, 'SYSTEM', NOW());

-- Cumulative summary (overall)
-- Total credits earned: 66 (42 + 24)
-- 의예과 졸업요건 약 140학점 기준
-- All course_type='1' so we split: major 의학 관련, liberal 교양/일반
-- For 의예과: 의학입문, 생물학, 의료/의학 관련 = 전공, 나머지 = 교양
-- 전공 과목: 의학입문1(6), 의학입문2(3), 생물학I(6), 생물학II(3), 의료와문화(2), 의학과문학(4), 의학의역사(2), 의학과창의적상상력(2), 노년의삶과죽음(2), 좋은의사되기(2), 과학의역사(4) = 36
-- 교양 과목: 영어회화(4), 인간심리의이해(9), 문화와예술(4), 창의력개발(4), 인제플랫폼(1), 영어발표(2), 생활속의심리학(3), 현대사회와시민(2) = 29
-- 선택: 나머지 = 66 - 36 - 29 = 1 → 0 (잔류 없음, 위 계산 확인)
-- 실제: 전공 36 + 교양 30 = 66 (인제플랫폼 1학점을 교양에 포함)

INSERT INTO tb_cumulative_summary (summary_id, student_id, total_credits_required, total_credits_earned, major_credits_required, major_credits_earned, liberal_credits_required, liberal_credits_earned, cumulative_gpa, major_gpa, completion_rate, ins_user_id, ins_dt)
VALUES (gen_random_uuid(), '20244897', 140, 66, 84, 36, 42, 30, 4.11, 4.30, 47.1, 'SYSTEM', NOW());


-- =====================================================
-- Step 4: Replace student skills (IT → 의예과 관련)
-- =====================================================

-- Delete existing IT-related skills
DELETE FROM tb_student_skill WHERE student_id = '20244897';

-- Add medical-related skills to tb_skill (if not exist)
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    ('SKM001', '생물학', 'Biology', ARRAY['생물','생명과학','Biology'], 'domain', 3, 'Y', 'SYSTEM', NOW()),
    ('SKM002', '의학입문', 'Introduction to Medicine', ARRAY['의학개론','의학기초','PreMed'], 'domain', 3, 'Y', 'SYSTEM', NOW()),
    ('SKM003', '화학', 'Chemistry', ARRAY['일반화학','Chemistry','화학기초'], 'domain', 3, 'Y', 'SYSTEM', NOW()),
    ('SKM004', '인체해부학', 'Human Anatomy', ARRAY['해부학','Anatomy','인체구조'], 'domain', 4, 'Y', 'SYSTEM', NOW()),
    ('SKM005', '의학영어', 'Medical English', ARRAY['Medical English','의학용어','의학영어'], 'language', 3, 'Y', 'SYSTEM', NOW()),
    ('SKM006', '의료윤리', 'Medical Ethics', ARRAY['생명윤리','Bioethics','의료윤리학'], 'domain', 2, 'Y', 'SYSTEM', NOW()),
    ('SKM007', '의학통계', 'Medical Statistics', ARRAY['생물통계','Biostatistics','의학통계학'], 'domain', 3, 'Y', 'SYSTEM', NOW())
ON CONFLICT (skill_cd) DO NOTHING;

-- Add medical skills for student
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
VALUES
    (gen_random_uuid(), '20244897', 'SKM001', 3, 5, 2, '2025-12-15', 'course', 'up', 'SYSTEM', NOW()),
    (gen_random_uuid(), '20244897', 'SKM002', 3, 5, 2, '2025-12-15', 'course', 'up', 'SYSTEM', NOW()),
    (gen_random_uuid(), '20244897', 'SKM003', 2, 4, 1, '2025-12-15', 'course', 'stable', 'SYSTEM', NOW()),
    (gen_random_uuid(), '20244897', 'SKM004', 1, 5, 0, NULL, 'self_assessment', 'up', 'SYSTEM', NOW()),
    (gen_random_uuid(), '20244897', 'SKM005', 2, 4, 1, '2025-12-15', 'course', 'up', 'SYSTEM', NOW()),
    (gen_random_uuid(), '20244897', 'SKM006', 2, 4, 1, '2025-12-15', 'course', 'stable', 'SYSTEM', NOW()),
    (gen_random_uuid(), '20244897', 'SKM007', 1, 3, 0, NULL, 'self_assessment', 'stable', 'SYSTEM', NOW());


-- =====================================================
-- Step 5: Replace simulation scenarios (IT → 의예과)
-- =====================================================

-- Delete existing IT-related scenarios
DELETE FROM tb_simulation_scenario WHERE student_id = '20244897';

-- Add medical-related scenarios
-- Scenario 1: career_path - 의사 커리어 준비
INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, description, base_state, changes, predicted_outcomes, confidence_level, created_at, is_favorite, ins_user_id, ins_dt)
VALUES (
    gen_random_uuid(),
    '20244897',
    'career_path',
    '의사 커리어 준비',
    '본과 진학 후 의사 국가시험 준비까지의 커리어 로드맵 시나리오',
    '{"current_grade": "의예과 2학년", "gpa": 4.11, "career_goal": "의사"}'::jsonb,
    '{"next_step": "본과 진학", "target_exam": "의사국가시험", "additional_activities": ["임상실습", "의학연구", "병원봉사"]}'::jsonb,
    '{"career_readiness": 0.75, "exam_preparation": 0.80, "clinical_experience": 0.60}'::jsonb,
    0.82,
    NOW(),
    true,
    'SYSTEM',
    NOW()
);

-- Scenario 2: skill_development - 기초의학 역량 강화
INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, description, base_state, changes, predicted_outcomes, confidence_level, created_at, is_favorite, ins_user_id, ins_dt)
VALUES (
    gen_random_uuid(),
    '20244897',
    'skill_development',
    '기초의학 역량 강화',
    '해부학, 생리학, 생화학 등 기초의학 과목 심화 학습 시나리오',
    '{"current_level": "의예과", "study_hours_per_week": 15, "key_subjects": ["생물학", "의학입문"]}'::jsonb,
    '{"target_level": "본과 준비 완료", "additional_courses": ["해부학", "생리학", "생화학"], "study_group": true}'::jsonb,
    '{"knowledge_improvement": 0.85, "exam_readiness": 0.78, "confidence_boost": 0.70}'::jsonb,
    0.80,
    NOW(),
    false,
    'SYSTEM',
    NOW()
);

-- Scenario 3: opportunity - 의료 봉사활동 참여 효과
INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, description, base_state, changes, predicted_outcomes, confidence_level, created_at, is_favorite, ins_user_id, ins_dt)
VALUES (
    gen_random_uuid(),
    '20244897',
    'opportunity',
    '의료 봉사활동 참여 효과',
    '지역사회 의료봉사 및 임상관찰 프로그램 참여 시 예상 효과 시나리오',
    '{"volunteer_experience": 0, "clinical_observation_hours": 0, "community_service": false}'::jsonb,
    '{"volunteer_hours": 100, "clinical_observation": true, "mentoring_program": true, "target_organizations": ["지역보건소", "대학병원", "의료NGO"]}'::jsonb,
    '{"empathy_development": 0.90, "clinical_awareness": 0.75, "portfolio_strength": 0.85}'::jsonb,
    0.78,
    NOW(),
    false,
    'SYSTEM',
    NOW()
);


-- =====================================================
-- Step 6: Replace portfolio data (IT → 의예과)
-- =====================================================

-- Delete existing IT-related portfolio items
DELETE FROM tb_portfolio WHERE student_id = '20244897';

-- Add medical-related portfolio items
-- 1. certification: TOEIC 850점
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, image_url, is_featured, display_order, ins_user_id, ins_dt, artifact_type, url, is_primary)
VALUES (
    gen_random_uuid(),
    '20244897',
    'certification',
    'TOEIC 850점 - 하**',
    '의학 논문 독해 및 국제 학회 참여를 위한 영어 능력 인증',
    '2025-06-15',
    '2027-06-15',
    '["영어", "의학영어", "학술영어"]'::jsonb,
    NULL, NULL,
    'Y',
    1,
    'SYSTEM',
    NOW(),
    'certification',
    NULL,
    true
);

-- 2. project: 기초의학 연구 참여
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, image_url, is_featured, display_order, ins_user_id, ins_dt, artifact_type, url, is_primary)
VALUES (
    gen_random_uuid(),
    '20244897',
    'project',
    '기초의학 연구 참여 - 하**',
    '생물학 실험실에서 세포생물학 관련 기초 연구에 학부생으로 참여하여 실험 보조 및 데이터 분석 수행',
    '2025-09-01',
    '2025-12-20',
    '["생물학", "실험설계", "데이터분석", "논문작성"]'::jsonb,
    NULL, NULL,
    'Y',
    2,
    'SYSTEM',
    NOW(),
    'project',
    NULL,
    false
);

-- 3. experience: 지역사회 의료봉사
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, image_url, is_featured, display_order, ins_user_id, ins_dt, artifact_type, url, is_primary)
VALUES (
    gen_random_uuid(),
    '20244897',
    'experience',
    '지역사회 의료봉사 - 하**',
    '김해시 지역보건소 건강검진 보조 및 건강교육 봉사활동 참여 (총 40시간)',
    '2025-07-01',
    '2025-08-31',
    '["의료봉사", "건강교육", "환자소통", "의료윤리"]'::jsonb,
    NULL, NULL,
    'N',
    3,
    'SYSTEM',
    NOW(),
    'experience',
    NULL,
    false
);

-- 4. paper: 의학입문 학술보고서
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, image_url, is_featured, display_order, ins_user_id, ins_dt, artifact_type, url, is_primary)
VALUES (
    gen_random_uuid(),
    '20244897',
    'paper',
    '의학입문 학술보고서 - 하**',
    '의학입문2 수업에서 작성한 "한국 의료 시스템의 과제와 미래" 학술 보고서 (우수 보고서 선정)',
    '2025-10-01',
    '2025-12-15',
    '["의학입문", "학술작성", "의료시스템", "비판적사고"]'::jsonb,
    NULL, NULL,
    'Y',
    4,
    'SYSTEM',
    NOW(),
    'paper',
    NULL,
    false
);

COMMIT;
