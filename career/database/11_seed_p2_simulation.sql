-- ============================================
-- IDINO Career - P2 Simulation Seed Data
-- Phase 12: What-if Planner
-- Created: 2026-01-07
-- Description: ?쒕??덉씠???쒕굹由ъ삤, ?쒕굹由ъ삤 鍮꾧탳 ?곗씠??-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. tb_simulation_scenario - ?쒕??덉씠???쒕굹由ъ삤 (~70媛?
-- ============================================

-- 湲곗〈 ?곗씠????젣 (seed script濡??앹꽦??寃껊쭔)
DELETE FROM tb_scenario_comparison WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_simulation_scenario WHERE ins_user_id = 'SEED_SCRIPT';

-- 怨쇰ぉ ?좏깮 ?쒕굹由ъ삤 (course_selection) - 3,4?숇뀈 ?숈깮??INSERT INTO tb_simulation_scenario (
    student_id,
    scenario_name,
    scenario_type,
    base_snapshot,
    changes,
    projected_gpa,
    projected_competencies,
    projected_skills,
    projected_graduation_date,
    projected_role_fit,
    risk_assessment,
    ai_analysis,
    recommendation_score,
    status,
    analyzed_at,
    ins_user_id
)
SELECT
    s.student_id,
    '2026??1?숆린 怨쇰ぉ ?좏깮 ?쒕굹由ъ삤 A',
    'course_selection',
    jsonb_build_object(
        'gpa', s.gpa,
        'grade_level', s.current_grade,
        'total_credits', 90 + (s.current_grade - 1) * 20,
        'snapshot_date', CURRENT_DATE
    ),
    jsonb_build_array(
        jsonb_build_object('type', 'add_course', 'course_cd', 'CS301', 'credits', 3),
        jsonb_build_object('type', 'add_course', 'course_cd', 'CS302', 'credits', 3),
        jsonb_build_object('type', 'add_course', 'course_cd', 'CS401', 'credits', 3)
    ),
    s.gpa + (RANDOM() * 0.2 - 0.1)::DECIMAL(3,2),
    jsonb_build_object(
        'COMP001', 75 + FLOOR(RANDOM() * 15),
        'COMP002', 70 + FLOOR(RANDOM() * 15),
        'COMP006', 80 + FLOOR(RANDOM() * 10)
    ),
    jsonb_build_object(
        'SKL001', 3 + FLOOR(RANDOM() * 2),
        'SKL002', 3 + FLOOR(RANDOM() * 2),
        'SKL004', 3 + FLOOR(RANDOM() * 2)
    ),
    DATE '2027-02-28',
    jsonb_build_object(
        'ROLE001', 75 + FLOOR(RANDOM() * 15),
        'ROLE002', 70 + FLOOR(RANDOM() * 15),
        'ROLE003', 65 + FLOOR(RANDOM() * 20)
    ),
    jsonb_build_object(
        'credit_overload', FALSE,
        'prerequisite_issue', FALSE,
        'graduation_risk', 'low'
    ),
    '???쒕굹由ъ삤??諛깆뿏??媛쒕컻 ??웾 媛뺥솕??珥덉젏??留욎텛怨??덉뒿?덈떎. CS301(?곗씠?곕쿋?댁뒪)怨?CS302(?쒖뒪?쒗봽濡쒓렇?섎컢)??諛깆뿏??媛쒕컻????븷???꾩닔?곸씤 怨쇰ぉ?낅땲??',
    82,
    'analyzed',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.current_grade IN (3, 4) AND s.department_cd IN ('CS', 'SW', 'AI')
LIMIT 15;

-- 怨쇰ぉ ?좏깮 ?쒕굹由ъ삤 B (?꾨줎?몄뿏??吏묒쨷)
INSERT INTO tb_simulation_scenario (
    student_id,
    scenario_name,
    scenario_type,
    base_snapshot,
    changes,
    projected_gpa,
    projected_competencies,
    projected_skills,
    projected_graduation_date,
    projected_role_fit,
    risk_assessment,
    ai_analysis,
    recommendation_score,
    status,
    analyzed_at,
    ins_user_id
)
SELECT
    s.student_id,
    '2026??1?숆린 怨쇰ぉ ?좏깮 ?쒕굹由ъ삤 B (?꾨줎?몄뿏??',
    'course_selection',
    jsonb_build_object(
        'gpa', s.gpa,
        'grade_level', s.current_grade,
        'total_credits', 90 + (s.current_grade - 1) * 20,
        'snapshot_date', CURRENT_DATE
    ),
    jsonb_build_array(
        jsonb_build_object('type', 'add_course', 'course_cd', 'SW201', 'credits', 3),
        jsonb_build_object('type', 'add_course', 'course_cd', 'SW202', 'credits', 3),
        jsonb_build_object('type', 'add_course', 'course_cd', 'SW301', 'credits', 3)
    ),
    s.gpa + (RANDOM() * 0.15)::DECIMAL(3,2),
    jsonb_build_object(
        'COMP001', 72 + FLOOR(RANDOM() * 15),
        'COMP002', 78 + FLOOR(RANDOM() * 12),
        'COMP006', 82 + FLOOR(RANDOM() * 10)
    ),
    jsonb_build_object(
        'SKL003', 4 + FLOOR(RANDOM() * 1),
        'SKL007', 3 + FLOOR(RANDOM() * 2),
        'SKL008', 3 + FLOOR(RANDOM() * 2)
    ),
    DATE '2027-02-28',
    jsonb_build_object(
        'ROLE002', 85 + FLOOR(RANDOM() * 10),
        'ROLE001', 65 + FLOOR(RANDOM() * 15),
        'ROLE006', 70 + FLOOR(RANDOM() * 15)
    ),
    jsonb_build_object(
        'credit_overload', FALSE,
        'prerequisite_issue', FALSE,
        'graduation_risk', 'low'
    ),
    '?꾨줎?몄뿏??媛쒕컻 ??웾 媛뺥솕???곹빀??怨쇰ぉ 議고빀?낅땲?? JavaScript? React ?ㅽ궗???ш쾶 ?μ긽??寃껋쑝濡??덉긽?⑸땲??',
    78,
    'analyzed',
    CURRENT_TIMESTAMP - INTERVAL '1 day',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.current_grade IN (3, 4) AND s.department_cd IN ('CS', 'SW')
LIMIT 10;

-- 而ㅻ━???꾪솚 ?쒕굹由ъ삤 (career_change)
INSERT INTO tb_simulation_scenario (
    student_id,
    scenario_name,
    scenario_type,
    base_snapshot,
    changes,
    projected_gpa,
    projected_competencies,
    projected_skills,
    projected_graduation_date,
    projected_role_fit,
    risk_assessment,
    ai_analysis,
    recommendation_score,
    status,
    analyzed_at,
    ins_user_id
)
SELECT
    s.student_id,
    '?곗씠??遺꾩꽍媛濡?而ㅻ━???꾪솚',
    'career_change',
    jsonb_build_object(
        'current_target_role', 'ROLE001',
        'gpa', s.gpa,
        'current_skills', '["SKL001", "SKL002"]'::jsonb
    ),
    jsonb_build_array(
        jsonb_build_object('type', 'change_target_role', 'from', 'ROLE001', 'to', 'ROLE003'),
        jsonb_build_object('type', 'add_skill_focus', 'skill_cd', 'SKL004'),
        jsonb_build_object('type', 'add_skill_focus', 'skill_cd', 'SKL005')
    ),
    s.gpa,
    jsonb_build_object(
        'COMP001', 78 + FLOOR(RANDOM() * 12),
        'COMP002', 75 + FLOOR(RANDOM() * 10),
        'COMP006', 85 + FLOOR(RANDOM() * 10)
    ),
    jsonb_build_object(
        'SKL004', 4,
        'SKL005', 3,
        'SKL001', 4
    ),
    DATE '2027-02-28',
    jsonb_build_object(
        'ROLE003', 88 + FLOOR(RANDOM() * 10),
        'ROLE001', 70 + FLOOR(RANDOM() * 10),
        'ROLE004', 75 + FLOOR(RANDOM() * 15)
    ),
    jsonb_build_object(
        'skill_gap', 'medium',
        'time_required', '6-12 months',
        'feasibility', 'high'
    ),
    '諛깆뿏??媛쒕컻?먯뿉???곗씠??遺꾩꽍媛濡쒖쓽 ?꾪솚? Python ?ㅽ궗???쒖슜?????덉뼱 ?좊━?⑸땲?? SQL怨?ML ?ㅽ궗 媛뺥솕媛 ?꾩슂?섎ŉ, ??6-12媛쒖썡??以鍮?湲곌컙???덉긽?⑸땲??',
    75,
    'analyzed',
    CURRENT_TIMESTAMP - INTERVAL '5 days',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.current_grade >= 2 AND s.department_cd IN ('CS', 'SW', 'BA', 'STAT')
LIMIT 12;

-- ?ㅽ궗 吏묒쨷 ?쒕굹由ъ삤 (skill_focus) - AI/ML 吏묒쨷
INSERT INTO tb_simulation_scenario (
    student_id,
    scenario_name,
    scenario_type,
    base_snapshot,
    changes,
    projected_gpa,
    projected_competencies,
    projected_skills,
    projected_graduation_date,
    projected_role_fit,
    risk_assessment,
    ai_analysis,
    recommendation_score,
    status,
    analyzed_at,
    ins_user_id
)
SELECT
    s.student_id,
    'AI/ML ?ㅽ궗 吏묒쨷 媛쒕컻',
    'skill_focus',
    jsonb_build_object(
        'current_skills', (
            SELECT jsonb_agg(jsonb_build_object('skill_cd', ss.skill_cd, 'level', ss.current_level))
            FROM tb_student_skill ss WHERE ss.student_id = s.student_id LIMIT 5
        )
    ),
    jsonb_build_array(
        jsonb_build_object('type', 'skill_target', 'skill_cd', 'SKL005', 'target_level', 4),
        jsonb_build_object('type', 'skill_target', 'skill_cd', 'SKL006', 'target_level', 3),
        jsonb_build_object('type', 'add_certification', 'name', 'TensorFlow Developer Certificate')
    ),
    s.gpa,
    jsonb_build_object(
        'COMP001', 80 + FLOOR(RANDOM() * 10),
        'COMP002', 82 + FLOOR(RANDOM() * 10),
        'COMP006', 90 + FLOOR(RANDOM() * 5)
    ),
    jsonb_build_object(
        'SKL005', 4,
        'SKL006', 3,
        'SKL001', 4
    ),
    NULL,
    jsonb_build_object(
        'ROLE004', 90 + FLOOR(RANDOM() * 8),
        'ROLE003', 82 + FLOOR(RANDOM() * 10),
        'ROLE005', 75 + FLOOR(RANDOM() * 15)
    ),
    jsonb_build_object(
        'time_investment', 'high',
        'resource_requirement', 'GPU access needed',
        'market_demand', 'very_high'
    ),
    'AI/ML ?ㅽ궗 吏묒쨷? ?꾩옱 ?쒖옣?먯꽌 留ㅼ슦 ?믪? ?섏슂媛 ?덉뒿?덈떎. Python 湲곕컲???꾪깂?섎㈃ ML ?숈뒿???섏썡?⑸땲?? TensorFlow ?먭꺽利앹? 痍⑥뾽?????꾩????⑸땲??',
    92,
    'analyzed',
    CURRENT_TIMESTAMP - INTERVAL '3 days',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.department_cd IN ('CS', 'SW', 'AI', 'STAT')
LIMIT 15;

-- ?쒕룞 怨꾪쉷 ?쒕굹由ъ삤 (activity_plan) - ?명꽩??+ ?꾨줈?앺듃
INSERT INTO tb_simulation_scenario (
    student_id,
    scenario_name,
    scenario_type,
    base_snapshot,
    changes,
    projected_gpa,
    projected_competencies,
    projected_skills,
    projected_graduation_date,
    projected_role_fit,
    risk_assessment,
    ai_analysis,
    recommendation_score,
    status,
    ins_user_id
)
SELECT
    s.student_id,
    '?щ쫫 ?명꽩??+ ?꾨줈?앺듃 怨꾪쉷',
    'activity_plan',
    jsonb_build_object(
        'current_activities', '[]'::jsonb,
        'available_time', 'summer_vacation',
        'grade_level', s.current_grade
    ),
    jsonb_build_array(
        jsonb_build_object('type', 'add_activity', 'activity_type', 'internship', 'duration', '8 weeks'),
        jsonb_build_object('type', 'add_activity', 'activity_type', 'side_project', 'duration', '4 weeks')
    ),
    s.gpa,
    jsonb_build_object(
        'COMP001', 75 + FLOOR(RANDOM() * 15),
        'COMP003', 80 + FLOOR(RANDOM() * 10),
        'COMP004', 82 + FLOOR(RANDOM() * 10)
    ),
    NULL,
    NULL,
    jsonb_build_object(
        'ROLE001', 80 + FLOOR(RANDOM() * 15),
        'ROLE002', 78 + FLOOR(RANDOM() * 15)
    ),
    jsonb_build_object(
        'schedule_conflict', FALSE,
        'academic_impact', 'minimal'
    ),
    '?щ쫫 諛⑺븰 ?숈븞 ?명꽩??낵 ?ъ씠???꾨줈?앺듃瑜?蹂묓뻾?섎뒗 寃껋? ?ㅻТ 寃쏀뿕怨??ы듃?대━??援ъ텞??留ㅼ슦 ?④낵?곸엯?덈떎. ?쒓컙 愿由ъ뿉 二쇱쓽媛 ?꾩슂?⑸땲??',
    85,
    'draft',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.current_grade IN (2, 3)
LIMIT 18;

-- ============================================
-- 2. tb_scenario_comparison - ?쒕굹由ъ삤 鍮꾧탳 (~40媛?
-- ============================================

-- 媛숈? ?숈깮???쒕굹由ъ삤?ㅼ쓣 鍮꾧탳
INSERT INTO tb_scenario_comparison (
    student_id,
    scenario_ids,
    comparison_metrics,
    winner_scenario_id,
    comparison_summary,
    ins_user_id
)
SELECT
    s1.student_id,
    ARRAY[s1.scenario_id, s2.scenario_id],
    jsonb_build_object(
        'gpa_difference', ABS(COALESCE(s1.projected_gpa, 0) - COALESCE(s2.projected_gpa, 0)),
        'role_fit_comparison', jsonb_build_object(
            'scenario_a_avg', 75 + FLOOR(RANDOM() * 15),
            'scenario_b_avg', 70 + FLOOR(RANDOM() * 20)
        ),
        'risk_comparison', jsonb_build_object(
            'scenario_a_risk', 'low',
            'scenario_b_risk', 'medium'
        ),
        'recommendation_score_diff', ABS(COALESCE(s1.recommendation_score, 0) - COALESCE(s2.recommendation_score, 0))
    ),
    CASE WHEN s1.recommendation_score > s2.recommendation_score THEN s1.scenario_id ELSE s2.scenario_id END,
    '???쒕굹由ъ삤瑜?鍮꾧탳??寃곌낵, ' ||
    CASE WHEN s1.recommendation_score > s2.recommendation_score
        THEN '?쒕굹由ъ삤 A媛 ???믪? 異붿쿇 ?먯닔瑜?諛쏆븯?듬땲?? '
        ELSE '?쒕굹由ъ삤 B媛 ???믪? 異붿쿇 ?먯닔瑜?諛쏆븯?듬땲?? '
    END ||
    '??븷 ?곹빀?꾩? 由ъ뒪???섏???醫낇빀?곸쑝濡?怨좊젮??寃곌낵?낅땲??',
    'SEED_SCRIPT'
FROM tb_simulation_scenario s1
JOIN tb_simulation_scenario s2
    ON s1.student_id = s2.student_id
    AND s1.scenario_id < s2.scenario_id
    AND s1.scenario_type = s2.scenario_type
WHERE s1.ins_user_id = 'SEED_SCRIPT' AND s2.ins_user_id = 'SEED_SCRIPT'
LIMIT 40;

-- ============================================
-- 寃利?荑쇰━
-- ============================================

-- SELECT 'tb_simulation_scenario' as table_name, COUNT(*) as count FROM tb_simulation_scenario WHERE ins_user_id = 'SEED_SCRIPT'
-- UNION ALL
-- SELECT 'tb_scenario_comparison', COUNT(*) FROM tb_scenario_comparison WHERE ins_user_id = 'SEED_SCRIPT';
