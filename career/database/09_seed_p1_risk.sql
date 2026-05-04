-- ============================================
-- IDINO Career - P1 Phase 10: Risk Seed Data
-- Risk Alerts, Constraint Checks, Prerequisite Rules
-- Created: 2026-01-07
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Prerequisite Rules (~45 records)
-- ============================================

DELETE FROM tb_constraint_check WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_risk_alert WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_prerequisite_rule WHERE ins_user_id = 'SEED_SCRIPT';

-- Computer Science prerequisites
INSERT INTO tb_prerequisite_rule (course_cd, prerequisite_course_cd, rule_type, min_grade, ins_user_id, ins_dt) VALUES
('CS201', 'CS101', 'required', 'D+', 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- ?먮즺援ъ“ ???꾨줈洹몃옒諛띻린珥?('CS202', 'CS201', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?뚭퀬由ъ쬁 ???먮즺援ъ“
('CS203', 'CS102', 'required', 'D+', 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- ?댁쁺泥댁젣 ??而댄벂?곌뎄議?('CS301', 'CS201', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?곗씠?곕쿋?댁뒪 ???먮즺援ъ“
('CS302', 'CS201', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?뚰봽?몄썾?닿났?????먮즺援ъ“
('CS303', 'CS203', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- 而댄벂?곕꽕?몄썙?????댁쁺泥댁젣
('CS401', 'CS202', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?멸났吏?????뚭퀬由ъ쬁
('CS401', 'CS201', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?멸났吏?????먮즺援ъ“
('CS402', 'CS301', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- 鍮낅뜲?댄꽣遺꾩꽍 ???곗씠?곕쿋?댁뒪
('CS402', 'CS401', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- 鍮낅뜲?댄꽣遺꾩꽍 ???멸났吏??('CS403', 'CS302', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- 罹≪뒪?ㅻ뵒?먯씤 ???뚰봽?몄썾?닿났??('CS404', 'CS303', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP);   -- ?뺣낫蹂댁븞 ??而댄벂?곕꽕?몄썙??
-- Software Engineering prerequisites
INSERT INTO tb_prerequisite_rule (course_cd, prerequisite_course_cd, rule_type, min_grade, ins_user_id, ins_dt) VALUES
('SW201', 'SW101', 'required', 'D+', 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- 媛앹껜吏?ν봽濡쒓렇?섎컢 ???뱁봽濡쒓렇?섎컢
('SW301', 'SW201', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- 紐⑤컮?쇱빋媛쒕컻 ??媛앹껜吏?ν봽濡쒓렇?섎컢
('SW302', 'SW201', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?대씪?곕뱶而댄벂????媛앹껜吏?ν봽濡쒓렇?섎컢
('SW303', 'SW302', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?곕툕?듭뒪 ???대씪?곕뱶而댄벂??('SW401', 'SW301', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ??ㅽ깮媛쒕컻 ??紐⑤컮?쇱빋媛쒕컻
('SW402', 'SW302', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- MSA ???대씪?곕뱶而댄벂??('SW403', 'CS401', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- AI?쒕퉬?ㅺ컻諛????멸났吏??
-- Electronics Engineering prerequisites
INSERT INTO tb_prerequisite_rule (course_cd, prerequisite_course_cd, rule_type, min_grade, ins_user_id, ins_dt) VALUES
('EE201', 'EE101', 'required', 'D+', 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- ?붿??몃끉由ъ꽕怨????꾧린?뚮줈
('EE301', 'EE201', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- 諛섎룄泥닿났?????붿??몃끉由ъ꽕怨?('EE302', 'EE201', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?듭떊?쒖뒪?????붿??몃끉由ъ꽕怨?('EE401', 'EE301', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?꾨쿋?붾뱶?쒖뒪????諛섎룄泥닿났??('EE402', 'EE302', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- IoT?쒖뒪?????듭떊?쒖뒪??
-- Business prerequisites
INSERT INTO tb_prerequisite_rule (course_cd, prerequisite_course_cd, rule_type, min_grade, ins_user_id, ins_dt) VALUES
('BA201', 'BA101', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- 留덉??낆썝濡???寃쎌쁺?숈썝濡?('BA301', 'BA102', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?щТ愿由????뚭퀎?먮━
('BA302', 'BA101', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?꾨왂寃쎌쁺 ??寃쎌쁺?숈썝濡?('BA401', 'BA301', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- 寃쎌쁺?뺣낫?쒖뒪?????щТ愿由?
-- Math/Statistics prerequisites
INSERT INTO tb_prerequisite_rule (course_cd, prerequisite_course_cd, rule_type, min_grade, ins_user_id, ins_dt) VALUES
('MA201', 'MA101', 'required', 'D+', 'SEED_SCRIPT', CURRENT_TIMESTAMP),  -- ?좏삎??섑븰 ??誘몄쟻遺꾪븰
('MA301', 'MA201', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?뺣쪧濡????좏삎??섑븰
('ST201', 'ST101', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?섎━?듦퀎?????듦퀎?숆컻濡?('ST301', 'ST201', 'required', 'C', 'SEED_SCRIPT', CURRENT_TIMESTAMP),   -- ?뚭?遺꾩꽍 ???섎━?듦퀎??('ST302', 'ST201', 'recommended', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- ?곗씠?곕쭏?대떇 ???섎━?듦퀎??
-- Corequisites (?숈떆?섍컯)
INSERT INTO tb_prerequisite_rule (course_cd, prerequisite_course_cd, rule_type, min_grade, ins_user_id, ins_dt) VALUES
('CS203', 'CS201', 'corequisite', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP), -- ?댁쁺泥댁젣 ???먮즺援ъ“
('SW302', 'CS301', 'corequisite', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP); -- ?대씪?곕뱶 ???곗씠?곕쿋?댁뒪

-- ============================================
-- 2. Risk Alerts (~80 records)
-- ============================================

-- Credit shortage alerts (?숈젏 遺議?
INSERT INTO tb_risk_alert (student_id, alert_type, severity, title, description, affected_items, recommended_actions, detected_at, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'credit_shortage',
    CASE WHEN s.current_grade >= 3 THEN 'critical' ELSE 'warning' END,
    '議몄뾽 ?숈젏 遺議?寃쎄퀬',
    '?꾩옱 ?댁닔 ?숈젏??議몄뾽 ?붽굔 ?鍮?' || (10 + (RANDOM() * 20)::INT)::TEXT || '?숈젏 遺議깊빀?덈떎.',
    ('{"required_credits": 130, "current_credits": ' || (70 + s.current_grade * 15 + (RANDOM() * 10)::INT)::TEXT || ', "shortage": ' || (10 + (RANDOM() * 20)::INT)::TEXT || '}')::JSONB,
    '{"actions": ["?ㅼ쓬 ?숆린 理쒕? ?숈젏 ?좎껌", "怨꾩젅?숆린 ?섍컯 怨좊젮", "?숆낵 ?щТ???곷떞"]}'::JSONB,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '60 days'),
    CASE WHEN RANDOM() > 0.3 THEN 'active' ELSE 'acknowledged' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (3, 4)
AND RANDOM() > 0.6
LIMIT 25;

-- Prerequisite missing alerts (?좎닔怨쇰ぉ 誘몄씠??
INSERT INTO tb_risk_alert (student_id, alert_type, severity, title, description, affected_items, recommended_actions, detected_at, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'prerequisite_missing',
    'warning',
    '?좎닔怨쇰ぉ 誘몄씠???뚮┝',
    '?ㅼ쓬 ?숆린 ?섍컯 ?덉젙 怨쇰ぉ???좎닔怨쇰ぉ??誘몄씠???곹깭?낅땲??',
    CASE
        WHEN s.department_cd = 'DEPT001' THEN '{"target_course": "CS401", "missing_prerequisite": "CS202", "course_name": "?멸났吏??}'::JSONB
        WHEN s.department_cd = 'DEPT002' THEN '{"target_course": "SW401", "missing_prerequisite": "SW301", "course_name": "??ㅽ깮媛쒕컻"}'::JSONB
        ELSE '{"target_course": "CS301", "missing_prerequisite": "CS201", "course_name": "?곗씠?곕쿋?댁뒪"}'::JSONB
    END,
    '{"actions": ["?대쾲 ?숆린 ?좎닔怨쇰ぉ ?섍컯", "?숆낵 ?щТ???좎닔怨쇰ぉ 硫댁젣 臾몄쓽", "?泥?怨쇰ぉ ?뺤씤"]}'::JSONB,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '30 days'),
    'active',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002')
AND s.current_grade IN (2, 3)
AND RANDOM() > 0.5
LIMIT 20;

-- GPA warning alerts (?숈젏 寃쎄퀬)
INSERT INTO tb_risk_alert (student_id, alert_type, severity, title, description, affected_items, recommended_actions, detected_at, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'gpa_warning',
    CASE WHEN RANDOM() > 0.5 THEN 'critical' ELSE 'warning' END,
    '?숈젏 寃쎄퀬',
    '吏곸쟾 ?숆린 ?깆쟻??湲곗? 誘몃떖?낅땲?? ?숈궗 寃쎄퀬 ?꾩쟻??二쇱쓽?섏꽭??',
    ('{"current_gpa": ' || (1.5 + RANDOM())::DECIMAL(3,2)::TEXT || ', "required_gpa": 2.0, "warning_count": ' || ((RANDOM() * 2)::INT + 1)::TEXT || '}')::JSONB,
    '{"actions": ["?숈뒿 ?곷떞 ?좎껌", "?쒗꽣留??꾨줈洹몃옩 李몄뿬", "?섍컯 怨쇰ぉ 議곗젙 ?곷떞"]}'::JSONB,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '90 days'),
    CASE WHEN RANDOM() > 0.4 THEN 'active' ELSE 'resolved' END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE RANDOM() > 0.85
LIMIT 15;

-- Graduation delay risk (議몄뾽 吏???꾪뿕)
INSERT INTO tb_risk_alert (student_id, alert_type, severity, title, description, affected_items, recommended_actions, detected_at, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'graduation_delay',
    'critical',
    '議몄뾽 吏???꾪뿕',
    '?꾩옱 吏꾪뻾 ?곹솴?쇰줈???뺤떆 議몄뾽???대젮?????덉뒿?덈떎.',
    ('{"expected_graduation": "2026-02", "current_trajectory": "2026-08", "main_issues": ["?숈젏 遺議?, "?꾩닔怨쇰ぉ 誘몄씠??]}')::JSONB,
    '{"actions": ["怨꾩젅?숆린 ?쒖슜", "?숆낵 ?곷떞", "?숈젏 愿由?怨꾪쉷 ?섎┰"]}'::JSONB,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '45 days'),
    'active',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade = 4
AND RANDOM() > 0.7
LIMIT 10;

-- Timetable conflict alerts (?쒓컙??異⑸룎)
INSERT INTO tb_risk_alert (student_id, alert_type, severity, title, description, affected_items, recommended_actions, detected_at, status, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'timetable_conflict',
    'info',
    '?쒓컙??異⑸룎 ?뚮┝',
    '?섍컯 ?щ쭩 怨쇰ぉ 媛??쒓컙 異⑸룎???덉긽?⑸땲??',
    '{"course_1": "CS301", "course_2": "CS302", "conflict_time": "??10:00-12:00"}'::JSONB,
    '{"actions": ["?ㅻⅨ 遺꾨컲 ?뺤씤", "李⑥꽑梨?怨쇰ぉ 以鍮?, "援먯닔???곷떞"]}'::JSONB,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '14 days'),
    'active',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002')
AND RANDOM() > 0.75
LIMIT 10;

-- ============================================
-- 3. Constraint Checks (~120 records)
-- ============================================

-- Prerequisite constraint checks
INSERT INTO tb_constraint_check (student_id, check_type, check_date, target_term_cd, input_data, result_passed, violations, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'prerequisite',
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '30 days'),
    '2025-1',
    '{"requested_courses": ["CS401", "CS301", "CS303"]}'::JSONB,
    RANDOM() > 0.3,
    CASE WHEN RANDOM() > 0.3 THEN NULL
         ELSE '[{"rule": "CS202 required for CS401", "message": "?좎닔怨쇰ぉ CS202(?뚭퀬由ъ쬁) 誘몄씠??}]'::JSONB
    END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002')
AND s.current_grade IN (2, 3, 4)
LIMIT 40;

-- Credit limit constraint checks
INSERT INTO tb_constraint_check (student_id, check_type, check_date, target_term_cd, input_data, result_passed, violations, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'credit',
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '20 days'),
    '2025-1',
    ('{"requested_credits": ' || (18 + (RANDOM() * 6)::INT)::TEXT || ', "max_credits": 21}')::JSONB,
    RANDOM() > 0.2,
    CASE WHEN RANDOM() > 0.2 THEN NULL
         ELSE '[{"rule": "max_credits_exceeded", "message": "理쒕? ?댁닔 ?숈젏 21?숈젏 珥덇낵"}]'::JSONB
    END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (1, 2, 3, 4)
LIMIT 50;

-- Graduation requirement checks
INSERT INTO tb_constraint_check (student_id, check_type, check_date, target_term_cd, input_data, result_passed, violations, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'graduation',
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '60 days'),
    '2025-2',
    ('{"total_credits": ' || (90 + s.current_grade * 10 + (RANDOM() * 20)::INT)::TEXT ||
     ', "major_credits": ' || (40 + (RANDOM() * 15)::INT)::TEXT ||
     ', "elective_credits": ' || (20 + (RANDOM() * 10)::INT)::TEXT ||
     ', "required_total": 130, "required_major": 60}')::JSONB,
    CASE WHEN s.current_grade >= 3 AND RANDOM() > 0.4 THEN FALSE ELSE TRUE END,
    CASE WHEN s.current_grade >= 3 AND RANDOM() > 0.4
         THEN '[{"rule": "major_credits_shortage", "message": "?꾧났 ?꾩닔 ?숈젏 遺議?}]'::JSONB
         ELSE NULL
    END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (3, 4)
LIMIT 30;

-- GPA requirement checks
INSERT INTO tb_constraint_check (student_id, check_type, check_date, target_term_cd, input_data, result_passed, violations, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'gpa',
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '45 days'),
    '2024-2',
    ('{"semester_gpa": ' || (2.0 + RANDOM() * 2.5)::DECIMAL(3,2)::TEXT ||
     ', "cumulative_gpa": ' || (2.5 + RANDOM() * 2.0)::DECIMAL(3,2)::TEXT ||
     ', "required_gpa": 2.0}')::JSONB,
    RANDOM() > 0.15,
    CASE WHEN RANDOM() > 0.15 THEN NULL
         ELSE '[{"rule": "semester_gpa_below_threshold", "message": "?숆린 ?됱젏 2.0 誘몃쭔, ?숈궗 寃쎄퀬"}]'::JSONB
    END,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
LIMIT 40;

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    prereq_count INT;
    alert_count INT;
    check_count INT;
BEGIN
    SELECT COUNT(*) INTO prereq_count FROM tb_prerequisite_rule WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO alert_count FROM tb_risk_alert WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO check_count FROM tb_constraint_check WHERE ins_user_id = 'SEED_SCRIPT';

    RAISE NOTICE '=== P1 Risk Seed Data Created ===';
    RAISE NOTICE 'tb_prerequisite_rule: % records', prereq_count;
    RAISE NOTICE 'tb_risk_alert: % records', alert_count;
    RAISE NOTICE 'tb_constraint_check: % records', check_count;
END $$;
