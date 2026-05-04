-- ============================================
-- IDINO Career - ?섍컯?좎껌 諛??깆쟻 ?곗씠??-- 媛쒖꽕媛뺤쥖, ?섍컯?좎껌, ?깆쟻 ?앹꽦
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. 媛쒖꽕媛뺤쥖 ?앹꽦 (2024-2, 2025-1 ?숆린)
-- ============================================

-- 2024-2?숆린 媛쒖꽕媛뺤쥖
INSERT INTO tb_course_offering (course_cd, term_cd, professor_cd, class_no, capacity, schedule, classroom, ins_user_id, ins_dt)
SELECT
    c.course_cd,
    '2024-2',
    p.professor_cd,
    1,
    40,
    CASE FLOOR(RANDOM() * 4)::int
        WHEN 0 THEN '??,2,3 ??,2,3'
        WHEN 1 THEN '??,3,4 紐?,3,4'
        WHEN 2 THEN '??,5,6 ??,5,6'
        ELSE '??,6,7 紐?,6,7'
    END,
    CASE FLOOR(RANDOM() * 5)::int
        WHEN 0 THEN '怨듯븰愿 301??
        WHEN 1 THEN '怨듯븰愿 402??
        WHEN 2 THEN '寃쎌쁺愿 201??
        WHEN 3 THEN '?먯뿰愿 105??
        ELSE '醫낇빀愿 501??
    END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_course c
LEFT JOIN tb_professor_course pc ON c.course_cd = pc.course_cd AND pc.is_primary = 'Y'
LEFT JOIN tb_professor p ON pc.professor_cd = p.professor_cd
WHERE c.course_cd IN ('CS201', 'CS202', 'CS301', 'CS302', 'CS303', 'CS401', 'CS402',
                       'SW201', 'SW301', 'SW302', 'SW401',
                       'EE201', 'EE301', 'EE302',
                       'BA201', 'BA301', 'BA302',
                       'MA201', 'MA301',
                       'ST201', 'ST301', 'ST302',
                       'GE201', 'GE202', 'GE301', 'GE302');

-- 2025-1?숆린 媛쒖꽕媛뺤쥖
INSERT INTO tb_course_offering (course_cd, term_cd, professor_cd, class_no, capacity, schedule, classroom, ins_user_id, ins_dt)
SELECT
    c.course_cd,
    '2025-1',
    p.professor_cd,
    1,
    40,
    CASE FLOOR(RANDOM() * 4)::int
        WHEN 0 THEN '??,2,3 ??,2,3'
        WHEN 1 THEN '??,3,4 紐?,3,4'
        WHEN 2 THEN '??,5,6 ??,5,6'
        ELSE '??,6,7 紐?,6,7'
    END,
    CASE FLOOR(RANDOM() * 5)::int
        WHEN 0 THEN '怨듯븰愿 301??
        WHEN 1 THEN '怨듯븰愿 402??
        WHEN 2 THEN '寃쎌쁺愿 201??
        WHEN 3 THEN '?먯뿰愿 105??
        ELSE '醫낇빀愿 501??
    END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_course c
LEFT JOIN tb_professor_course pc ON c.course_cd = pc.course_cd AND pc.is_primary = 'Y'
LEFT JOIN tb_professor p ON pc.professor_cd = p.professor_cd
WHERE c.course_cd IN ('CS101', 'CS102', 'CS201', 'CS202', 'CS203', 'CS301', 'CS302', 'CS303', 'CS401', 'CS402', 'CS403', 'CS404',
                       'SW101', 'SW201', 'SW301', 'SW302', 'SW303', 'SW401', 'SW402', 'SW403',
                       'EE101', 'EE201', 'EE301', 'EE302', 'EE401', 'EE402',
                       'BA101', 'BA102', 'BA201', 'BA202', 'BA301', 'BA302', 'BA401', 'BA402',
                       'MA101', 'MA201', 'MA301', 'MA302',
                       'ST101', 'ST201', 'ST301', 'ST302',
                       'GE101', 'GE102', 'GE103', 'GE201', 'GE202', 'GE203', 'GE301', 'GE302', 'GE303');

-- ============================================
-- 2. ?섍컯?좎껌 ?곗씠???앹꽦 (?섑뵆)
-- ============================================

-- 而댄벂?곌났?숆낵 4?숇뀈 ?숈깮?ㅼ쓽 ?섍컯 湲곕줉
INSERT INTO tb_enrollment (student_id, offering_id, term_cd, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    co.offering_id,
    co.term_cd,
    'completed',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_course_offering co
WHERE s.department_cd = 'DEPT001'
  AND s.current_grade = 4
  AND co.term_cd = '2024-2'
  AND co.course_cd IN ('CS301', 'CS302', 'CS401', 'CS402', 'GE301');

-- 而댄벂?곌났?숆낵 3?숇뀈 ?숈깮?ㅼ쓽 ?섍컯 湲곕줉
INSERT INTO tb_enrollment (student_id, offering_id, term_cd, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    co.offering_id,
    co.term_cd,
    'completed',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_course_offering co
WHERE s.department_cd = 'DEPT001'
  AND s.current_grade = 3
  AND co.term_cd = '2024-2'
  AND co.course_cd IN ('CS201', 'CS202', 'CS301', 'GE201', 'GE202');

-- ?뚰봽?몄썾?댄븰怨??숈깮?ㅼ쓽 ?섍컯 湲곕줉
INSERT INTO tb_enrollment (student_id, offering_id, term_cd, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    co.offering_id,
    co.term_cd,
    'completed',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_course_offering co
WHERE s.department_cd = 'DEPT002'
  AND s.current_grade IN (3, 4)
  AND co.term_cd = '2024-2'
  AND co.course_cd IN ('SW201', 'SW301', 'SW302', 'GE201', 'GE301');

-- 寃쎌쁺?숆낵 ?숈깮?ㅼ쓽 ?섍컯 湲곕줉
INSERT INTO tb_enrollment (student_id, offering_id, term_cd, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    co.offering_id,
    co.term_cd,
    'completed',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_course_offering co
WHERE s.department_cd = 'DEPT014'
  AND s.current_grade IN (3, 4)
  AND co.term_cd = '2024-2'
  AND co.course_cd IN ('BA201', 'BA301', 'BA302', 'GE201', 'GE301');

-- ============================================
-- 3. ?깆쟻 ?곗씠???앹꽦
-- ============================================

-- ?깆쟻 ?곗씠???앹꽦 (媛??섍컯 湲곕줉?????
INSERT INTO tb_grade (enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
SELECT
    e.enrollment_id,
    e.student_id,
    co.course_cd,
    e.term_cd,
    CASE FLOOR(RANDOM() * 10)::int
        WHEN 0 THEN 'A+'
        WHEN 1 THEN 'A+'
        WHEN 2 THEN 'A0'
        WHEN 3 THEN 'A0'
        WHEN 4 THEN 'B+'
        WHEN 5 THEN 'B+'
        WHEN 6 THEN 'B0'
        WHEN 7 THEN 'B0'
        WHEN 8 THEN 'C+'
        ELSE 'C0'
    END,
    CASE FLOOR(RANDOM() * 10)::int
        WHEN 0 THEN 4.50
        WHEN 1 THEN 4.50
        WHEN 2 THEN 4.00
        WHEN 3 THEN 4.00
        WHEN 4 THEN 3.50
        WHEN 5 THEN 3.50
        WHEN 6 THEN 3.00
        WHEN 7 THEN 3.00
        WHEN 8 THEN 2.50
        ELSE 2.00
    END,
    c.credits,
    'N',
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_enrollment e
JOIN tb_course_offering co ON e.offering_id = co.offering_id
JOIN tb_course c ON co.course_cd = c.course_cd
WHERE e.status = 'completed';

-- ============================================
-- 4. ?숈깮 ?깆랬 ?곗씠???앹꽦
-- ============================================

-- ?먭꺽利??곗씠??INSERT INTO tb_achievement (student_id, achievement_type, achievement_nm, issuing_organization, acquired_date, score, verified, ins_user_id, ins_dt) VALUES
('2021010001', 'certificate', '?뺣낫泥섎━湲곗궗', '?쒓뎅?곗뾽?몃젰怨듬떒', '2024-06-15', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010001', 'language', 'TOEIC', 'ETS', '2024-03-10', '890', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'certificate', 'SQLD', '?쒓뎅?곗씠?곗궛?낆쭊?μ썝', '2024-05-20', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'language', 'TOEFL', 'ETS', '2024-04-15', '105', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'certificate', 'AWS Solutions Architect', 'Amazon', '2024-07-10', 'Associate', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'language', 'TOEIC', 'ETS', '2024-06-20', '850', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'certificate', 'ADSP', '?쒓뎅?곗씠?곗궛?낆쭊?μ썝', '2024-08-15', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010002', 'certificate', '由щ늼?ㅻ쭏?ㅽ꽣2湲?, '?쒓뎅?뺣낫?듭떊吏꾪씎?묓쉶', '2024-05-25', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'language', 'OPIc', 'ACTFL', '2024-04-20', 'IH', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', 'certificate', '?뺣낫泥섎━湲곗궗', '?쒓뎅?곗뾽?몃젰怨듬떒', '2024-06-15', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'certificate', '留ㅺ꼍TEST', '留ㅼ씪寃쎌젣?좊Ц??, '2024-03-25', '理쒖슦??, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'language', 'TOEIC Speaking', 'ETS', '2024-05-10', 'Level 7', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140002', 'certificate', '?쒓꼍TESAT', '?쒓뎅寃쎌젣?좊Ц', '2024-04-30', '1湲?, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021130001', 'certificate', 'ADsP', '?쒓뎅?곗씠?곗궛?낆쭊?μ썝', '2024-05-15', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021130002', 'certificate', 'SQLD', '?쒓뎅?곗씠?곗궛?낆쭊?μ썝', '2024-06-20', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021250001', 'certificate', 'GTQ 1湲?, '?쒓뎅?앹궛?깅낯遺', '2024-03-15', '?⑷꺽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021250001', 'certificate', 'Google UX Design', 'Google', '2024-07-20', 'Professional', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ?섏긽 ?대젰
INSERT INTO tb_achievement (student_id, achievement_type, achievement_nm, issuing_organization, acquired_date, score, verified, ins_user_id, ins_dt) VALUES
('2021010001', 'award', '援먮궡 ?댁빱?????, '?쒓뎅怨쇳븰湲곗닠??숆탳', '2024-05-20', '???, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'award', 'AI 寃쎌쭊???湲덉긽', '怨쇳븰湲곗닠?뺣낫?듭떊遺', '2024-11-15', '湲덉긽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'award', '鍮낅뜲?댄꽣 遺꾩꽍 寃쎌쭊??????, '?쒓뎅?곗씠?곗궛?낆쭊?μ썝', '2024-10-25', '???, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'award', '紐⑤컮?쇱빋 媛쒕컻????λ젮??, '?뺣낫?듭떊?곗뾽吏꾪씎??, '2024-09-10', '?λ젮??, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'award', '李쎌뾽?꾩씠?붿뼱 寃쎌쭊???理쒖슦?섏긽', '以묒냼踰ㅼ쿂湲곗뾽遺', '2024-08-30', '理쒖슦?섏긽', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 5. ?꾨줈洹몃옩 李몄뿬 ?대젰 ?앹꽦
-- ============================================

INSERT INTO tb_participation (student_id, program_cd, status, completed_at, ins_user_id, ins_dt) VALUES
('2021010001', 'PGM001', 'completed', '2024-08-31', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'PGM002', 'completed', '2024-06-30', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'PGM007', 'in_progress', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'PGM003', 'registered', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2022010002', 'PGM006', 'completed', '2024-05-31', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'PGM004', 'in_progress', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', 'PGM008', 'completed', '2024-11-30', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020001', 'PGM005', 'completed', '2024-08-15', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'PGM004', 'in_progress', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2021140002', 'PGM001', 'registered', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2021130001', 'PGM002', 'completed', '2024-06-30', 'SYSTEM', CURRENT_TIMESTAMP),
('2021130002', 'PGM003', 'registered', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2021250001', 'PGM007', 'in_progress', NULL, 'SYSTEM', CURRENT_TIMESTAMP),
('2021060001', 'PGM008', 'completed', '2024-11-30', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 6. ?ы듃?대━???곗씠???앹꽦
-- ============================================

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt) VALUES
('2021010001', 'github', 'Personal Projects', 'https://github.com/minjunkim', '媛쒖씤 ?꾨줈?앺듃 紐⑥쓬', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010001', 'notion', 'Tech Blog', 'https://notion.so/minjunkim', '湲곗닠 釉붾줈洹?, 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'github', 'AI/ML Projects', 'https://github.com/seoyeonlee', 'AI/ML ?꾨줈?앺듃 紐⑥쓬', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'project', '議몄뾽 ?꾨줈?앺듃', 'https://github.com/jihopark/capstone', '罹≪뒪???붿옄???꾨줈?앺듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'github', 'Data Analysis Portfolio', 'https://github.com/yeeunchoi', '?곗씠??遺꾩꽍 ?ы듃?대━??, 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'notion', 'Frontend Portfolio', 'https://notion.so/yunashin', '?꾨줎?몄뿏???ы듃?대━??, 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', 'github', 'Full Stack Projects', 'https://github.com/seunghyunjang', '??ㅽ깮 ?꾨줈?앺듃', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'notion', 'Business Case Studies', 'https://notion.so/jihyunkim', '鍮꾩쫰?덉뒪 耳?댁뒪 ?ㅽ꽣??, 'SYSTEM', CURRENT_TIMESTAMP),
('2021250001', 'project', 'UI/UX Design Portfolio', 'https://behance.net/soyulkim', 'UI/UX ?붿옄???ы듃?대━??, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 7. ?뚰겕??吏꾨떒 寃곌낵 ?앹꽦
-- ============================================

INSERT INTO tb_worknet_diagnosis (student_id, diagnosis_date, aptitude_codes, interest_codes, job_match_scores, ins_user_id, ins_dt)
SELECT
    student_id,
    '2024-09-15'::date,
    CASE FLOOR(RANDOM() * 4)::int
        WHEN 0 THEN ARRAY['I', 'R']::varchar[]
        WHEN 1 THEN ARRAY['I', 'C']::varchar[]
        WHEN 2 THEN ARRAY['E', 'S']::varchar[]
        ELSE ARRAY['A', 'I']::varchar[]
    END,
    CASE FLOOR(RANDOM() * 4)::int
        WHEN 0 THEN ARRAY['IT', 'Engineering']::varchar[]
        WHEN 1 THEN ARRAY['Business', 'Finance']::varchar[]
        WHEN 2 THEN ARRAY['Science', 'Research']::varchar[]
        ELSE ARRAY['Design', 'Creative']::varchar[]
    END,
    CASE department_cd
        WHEN 'DEPT001' THEN '{"ROLE001": 85, "ROLE005": 78, "ROLE007": 72}'::jsonb
        WHEN 'DEPT002' THEN '{"ROLE002": 82, "ROLE007": 80, "ROLE001": 75}'::jsonb
        WHEN 'DEPT003' THEN '{"ROLE005": 80, "ROLE008": 75, "ROLE006": 70}'::jsonb
        WHEN 'DEPT014' THEN '{"ROLE009": 88, "ROLE010": 82, "ROLE012": 78}'::jsonb
        WHEN 'DEPT013' THEN '{"ROLE003": 85, "ROLE004": 80, "ROLE005": 75}'::jsonb
        WHEN 'DEPT025' THEN '{"ROLE011": 90, "ROLE012": 78, "ROLE002": 65}'::jsonb
        ELSE '{"ROLE001": 70, "ROLE003": 68, "ROLE009": 65}'::jsonb
    END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE current_grade >= 2;

-- ============================================
-- 8. 議몄뾽??肄뷀샇???곗씠???앹꽦
-- ============================================

INSERT INTO tb_alumni_cohort (department_cd, graduation_year, role_cd, sample_size, avg_gpa_range, salary_range, competency_profile, employment_rate, avg_job_search_months, ins_user_id, ins_dt) VALUES
-- 而댄벂?곌났?숆낵
('DEPT001', 2023, 'ROLE001', 25, '3.5-4.0', '4500-5500留뚯썝', '{"COMP001": 82, "COMP002": 78, "COMP003": 72}', 92.5, 2.3, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT001', 2023, 'ROLE005', 18, '3.7-4.3', '5000-6500留뚯썝', '{"COMP001": 88, "COMP002": 85, "COMP005": 75}', 88.0, 2.8, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT001', 2023, 'ROLE007', 15, '3.4-3.9', '4500-5500留뚯썝', '{"COMP001": 80, "COMP002": 75, "COMP003": 78}', 90.0, 2.5, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT001', 2022, 'ROLE001', 28, '3.4-4.0', '4300-5300留뚯썝', '{"COMP001": 80, "COMP002": 76, "COMP003": 70}', 90.5, 2.5, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?뚰봽?몄썾?댄븰怨?('DEPT002', 2023, 'ROLE002', 20, '3.5-4.1', '4500-5500留뚯썝', '{"COMP001": 78, "COMP002": 75, "COMP003": 80}', 91.0, 2.2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT002', 2023, 'ROLE007', 22, '3.4-4.0', '4800-5800留뚯썝', '{"COMP001": 82, "COMP002": 78, "COMP003": 76}', 93.0, 2.0, 'SYSTEM', CURRENT_TIMESTAMP),
-- 寃쎌쁺?숆낵
('DEPT014', 2023, 'ROLE009', 15, '3.6-4.2', '4500-5500留뚯썝', '{"COMP001": 75, "COMP002": 82, "COMP003": 88}', 85.0, 3.2, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT014', 2023, 'ROLE010', 18, '3.4-3.9', '4000-5000留뚯썝', '{"COMP001": 72, "COMP003": 85, "COMP005": 78}', 88.0, 2.8, 'SYSTEM', CURRENT_TIMESTAMP),
-- ?듦퀎?숆낵
('DEPT013', 2023, 'ROLE003', 12, '3.7-4.3', '4800-6000留뚯썝', '{"COMP001": 85, "COMP002": 88, "COMP003": 72}', 90.0, 2.5, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT013', 2023, 'ROLE005', 8, '3.8-4.4', '5200-6500留뚯썝', '{"COMP001": 90, "COMP002": 85, "COMP005": 70}', 87.5, 3.0, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 9. ?깃났 ?⑦꽩 ?곗씠???앹꽦
-- ============================================

INSERT INTO tb_success_pattern (department_cd, role_cd, pattern_nm, pattern_rules, correlation_score, lift, sample_size, ins_user_id, ins_dt) VALUES
('DEPT001', 'ROLE001', '諛깆뿏??媛쒕컻???깃났 ?⑦꽩',
 '{"min_gpa": 3.5, "required_courses": ["CS201", "CS301", "CS303"], "required_certs": ["?뺣낫泥섎━湲곗궗"], "min_projects": 2, "internship_required": true}',
 0.8523, 2.35, 45, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT001', 'ROLE005', 'AI ?붿??덉뼱 ?깃났 ?⑦꽩',
 '{"min_gpa": 3.7, "required_courses": ["CS202", "CS401", "CS402"], "required_skills": ["Python", "ML", "DL"], "research_experience": true}',
 0.8125, 2.78, 32, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT002', 'ROLE007', '??ㅽ깮 媛쒕컻???깃났 ?⑦꽩',
 '{"min_gpa": 3.4, "required_courses": ["SW101", "SW201", "SW301", "SW401"], "portfolio_required": true, "project_count": 3}',
 0.7856, 2.12, 38, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT014', 'ROLE009', '寃쎌쁺 而⑥꽕?댄듃 ?깃났 ?⑦꽩',
 '{"min_gpa": 3.6, "required_courses": ["BA201", "BA301", "BA302"], "language_score": {"TOEIC": 850}, "case_competition": true}',
 0.7425, 1.95, 35, 'SYSTEM', CURRENT_TIMESTAMP),
('DEPT013', 'ROLE003', '?곗씠??遺꾩꽍媛 ?깃났 ?⑦꽩',
 '{"min_gpa": 3.5, "required_courses": ["ST201", "ST301", "ST302"], "required_tools": ["Python", "SQL", "R"], "certification": ["ADsP"]}',
 0.8234, 2.45, 42, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 10. AI 踰꾩쟾 愿由??곗씠???앹꽦
-- ============================================

INSERT INTO tb_prompt_version (version_cd, prompt_content, description, ins_user_id, ins_dt) VALUES
('v1.0.0', '?뱀떊? ??숈깮??而ㅻ━??媛쒕컻???뺣뒗 AI ?곷떞?ъ엯?덈떎...', '珥덇린 ?꾨＼?꾪듃 踰꾩쟾', 'SYSTEM', CURRENT_TIMESTAMP),
('v1.1.0', '?뱀떊? ??숈깮??而ㅻ━??媛쒕컻???뺣뒗 ?꾨Ц AI ?곷떞?ъ엯?덈떎. ?숈깮????웾, ?깆쟻, ?쒕룞??遺꾩꽍?섏뿬 留욎땄???≪뀡??異붿쿇?⑸땲??..', 'Evidence 湲곕컲 異붿쿇 異붽?', 'SYSTEM', CURRENT_TIMESTAMP);

INSERT INTO tb_policy_version (version_cd, rules, description, ins_user_id, ins_dt) VALUES
('v1.0.0', '{"max_actions": 4, "min_evidence": 3, "constraint_check": true}', '珥덇린 ?뺤콉 踰꾩쟾', 'SYSTEM', CURRENT_TIMESTAMP),
('v1.1.0', '{"max_actions": 4, "min_evidence": 3, "constraint_check": true, "prerequisite_check": true, "credit_limit": 21}', '?좎닔怨쇰ぉ/?숈젏 ?쒗븳 異붽?', 'SYSTEM', CURRENT_TIMESTAMP);

INSERT INTO tb_model_version (version_cd, base_model, fine_tuned_id, training_data_version, metrics, deployed_at, ins_user_id, ins_dt) VALUES
('v1.0.0', 'gpt-4o-mini', NULL, NULL, '{"accuracy": 0.85, "satisfaction": 0.78}', '2024-12-01', 'SYSTEM', CURRENT_TIMESTAMP),
('v1.1.0', 'gpt-4o', NULL, NULL, '{"accuracy": 0.92, "satisfaction": 0.88}', '2025-01-02', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 11. Eval 耳?댁뒪 ?곗씠???앹꽦
-- ============================================

INSERT INTO tb_eval_case (case_nm, input_data, expected_schema, quality_criteria, ins_user_id, ins_dt) VALUES
('CS Major Backend Goal',
 '{"student_id": "2021010001", "department": "而댄벂?곌났?숆낵", "career_goal": "諛깆뿏?쒓컻諛쒖옄", "gpa": 3.8}',
 '{"action_items": {"type": "array", "maxItems": 4}, "evidence": {"type": "array", "minItems": 3}}',
 '{"evidence_coverage": 0.8, "constraint_compliance": 1.0, "relevance_score": 0.7}',
 'SYSTEM', CURRENT_TIMESTAMP),
('Statistics Major Data Analyst Goal',
 '{"student_id": "2021130001", "department": "?듦퀎?숆낵", "career_goal": "?곗씠?곕텇?앷?", "gpa": 4.0}',
 '{"action_items": {"type": "array", "maxItems": 4}, "evidence": {"type": "array", "minItems": 3}}',
 '{"evidence_coverage": 0.8, "constraint_compliance": 1.0, "relevance_score": 0.75}',
 'SYSTEM', CURRENT_TIMESTAMP),
('Business Major Consultant Goal',
 '{"student_id": "2021140001", "department": "寃쎌쁺?숆낵", "career_goal": "寃쎌쁺而⑥꽕?댄듃", "gpa": 3.9}',
 '{"action_items": {"type": "array", "maxItems": 4}, "evidence": {"type": "array", "minItems": 3}}',
 '{"evidence_coverage": 0.8, "constraint_compliance": 1.0, "relevance_score": 0.7}',
 'SYSTEM', CURRENT_TIMESTAMP);
