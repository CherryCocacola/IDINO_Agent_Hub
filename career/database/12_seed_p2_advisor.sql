-- ============================================
-- IDINO Career - P2 Advisor Seed Data
-- Phase 13: Advisor Workspace
-- Created: 2026-01-07
-- Description: ?대뱶諛붿씠? ?좊떦, 媛쒖엯, ?명듃, 肄뷀샇???ㅻ깄???곗씠??-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. tb_advisor_assignment - ?대뱶諛붿씠? ?좊떦 (~110媛?
-- ============================================

-- 湲곗〈 ?곗씠????젣 (seed script濡??앹꽦??寃껊쭔)
DELETE FROM tb_advisor_note WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_advisor_intervention WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_cohort_snapshot WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_advisor_assignment WHERE ins_user_id = 'SEED_SCRIPT';

-- 援먯닔 ??븷???ъ슜?먮? ?대뱶諛붿씠?濡??좊떦 (user_type = 'PROF' ?먮뒗 role_level <= 3)
-- ?숆낵蹂꾨줈 援먯닔-?숈깮 留ㅽ븨
INSERT INTO tb_advisor_assignment (
    advisor_user_id,
    student_id,
    assignment_type,
    status,
    ins_user_id
)
SELECT
    u.user_id,
    s.student_id,
    CASE
        WHEN ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY RANDOM()) = 1 THEN 'primary'
        ELSE 'secondary'
    END,
    'active',
    'SEED_SCRIPT'
FROM tb_student s
CROSS JOIN LATERAL (
    -- 媛숈? ?숆낵???ъ슜??以??쒕뜡 ?좏깮 (?먮뒗 ?꾩껜 ?ъ슜??以??좏깮)
    SELECT user_id
    FROM tb_user
    WHERE use_fg = 'Y'
    ORDER BY RANDOM()
    LIMIT 1
) u
ON CONFLICT (advisor_user_id, student_id, assignment_type) DO NOTHING;

-- ============================================
-- 2. tb_advisor_intervention - ?대뱶諛붿씠? 媛쒖엯 (~50媛?
-- ============================================

-- 紐⑺몴 寃??媛쒖엯 (goal_review)
INSERT INTO tb_advisor_intervention (
    advisor_user_id,
    student_id,
    intervention_type,
    title,
    description,
    related_entity_type,
    original_value,
    new_value,
    reason,
    student_notified,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'goal_review',
    '紐⑺몴 ?ъ꽦??寃??諛?議곗젙',
    cg.title || ' 紐⑺몴?????吏꾪뻾 ?곹솴??寃?좏븯怨?留덉씪?ㅽ넠??議곗젙?덉뒿?덈떎.',
    'goal',
    jsonb_build_object('original_target_date', cg.target_date, 'original_status', cg.status),
    jsonb_build_object('adjusted_target_date', cg.target_date + INTERVAL '30 days', 'reason', 'realistic_adjustment'),
    '?숈깮???꾩옱 ?숈뾽 遺?댁쓣 怨좊젮?섏뿬 紐⑺몴 ?ъ꽦 湲고븳??1媛쒖썡 ?곗옣?덉뒿?덈떎. ?ㅽ쁽 媛?ν븳 紐⑺몴 ?ㅼ젙??以묒슂?⑸땲??',
    TRUE,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
JOIN tb_coaching_goal cg ON aa.student_id = cg.student_id
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 15;

-- 怨꾪쉷 ?섏젙 媛쒖엯 (plan_override)
INSERT INTO tb_advisor_intervention (
    advisor_user_id,
    student_id,
    intervention_type,
    title,
    description,
    related_entity_type,
    original_value,
    new_value,
    reason,
    student_notified,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'plan_override',
    '肄붿묶 怨꾪쉷 ?곗꽑?쒖쐞 議곗젙',
    '?숈깮???곹솴 蹂?붿뿉 ?곕씪 肄붿묶 怨꾪쉷???곗꽑?쒖쐞瑜?議곗젙?덉뒿?덈떎.',
    'plan',
    jsonb_build_object('original_priority', 'high'),
    jsonb_build_object('new_priority', 'critical', 'added_resources', ARRAY['異붽? 硫섑넗留?, '?ㅽ꽣??洹몃９ ?곌껐']),
    '議몄뾽 ?붽굔 異⑹”???꾪빐 ?대떦 怨꾪쉷???곗꽑?쒖쐞瑜??곹뼢 議곗젙?섍퀬 異붽? 吏?먯쓣 ?곌껐?덉뒿?덈떎.',
    TRUE,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 10;

-- 由ъ뒪???먯뒪而щ젅?댁뀡 (risk_escalation)
INSERT INTO tb_advisor_intervention (
    advisor_user_id,
    student_id,
    intervention_type,
    title,
    description,
    related_entity_type,
    original_value,
    new_value,
    reason,
    student_notified,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    ra.student_id,
    'risk_escalation',
    '?꾪뿕 ?뚮┝ ?먯뒪而щ젅?댁뀡',
    ra.title || ' 愿???꾪뿕 ?곹솴???숆낵?μ뿉寃?蹂닿퀬?덉뒿?덈떎.',
    'alert',
    jsonb_build_object('original_severity', ra.severity, 'alert_type', ra.alert_type),
    jsonb_build_object('escalated_to', 'department_head', 'follow_up_meeting', 'scheduled'),
    '?숈깮???숈뾽 ?꾪뿕 ?곹솴??吏?띾릺???숆낵 李⑥썝??吏?먯씠 ?꾩슂?⑸땲??',
    TRUE,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
JOIN tb_risk_alert ra ON aa.student_id = ra.student_id
WHERE aa.assignment_type = 'primary'
    AND ra.severity IN ('critical', 'warning')
    AND ra.status = 'active'
ORDER BY RANDOM()
LIMIT 15;

-- 異붿쿇 ?섏젙 (recommendation_edit)
INSERT INTO tb_advisor_intervention (
    advisor_user_id,
    student_id,
    intervention_type,
    title,
    description,
    related_entity_type,
    original_value,
    new_value,
    reason,
    student_notified,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'recommendation_edit',
    '湲고쉶 異붿쿇 留욎땄??,
    '?숈깮??而ㅻ━??紐⑺몴??留욊쾶 湲고쉶 異붿쿇???섏젙?덉뒿?덈떎.',
    'recommendation',
    jsonb_build_object('auto_recommended', TRUE),
    jsonb_build_object('advisor_curated', TRUE, 'focus_area', 'internship'),
    '?숈깮???щ쭩?섎뒗 遺꾩빞? ?꾩옱 ??웾 ?섏???怨좊젮?섏뿬 ?명꽩??湲고쉶瑜?以묒떖?쇰줈 異붿쿇???ш뎄?깊뻽?듬땲??',
    FALSE,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 10;

-- ============================================
-- 3. tb_advisor_note - ?대뱶諛붿씠? 硫붾え (~70媛?
-- ============================================

-- ?곷떞 湲곕줉 (meeting)
INSERT INTO tb_advisor_note (
    advisor_user_id,
    student_id,
    note_type,
    title,
    content,
    is_private,
    meeting_date,
    follow_up_required,
    follow_up_date,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'meeting',
    '?뺢린 ?곷떞 - ' || TO_CHAR(CURRENT_DATE - (ROW_NUMBER() OVER () * 7), 'YYYY??MM??),
    '?숈깮怨?' || TO_CHAR(CURRENT_DATE - (ROW_NUMBER() OVER () * 7), 'MM??DD??) || ' ?곷떞??吏꾪뻾?덉뒿?덈떎. ' ||
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN '吏꾨줈 諛⑺뼢?????怨좊???怨듭쑀諛쏆븯?듬땲?? ?곗씠??遺꾩꽍 遺꾩빞??愿?ъ씠 ?덉뼱 愿??怨쇰ぉ ?섍컯??沅뚯옣?덉뒿?덈떎.'
        WHEN 1 THEN '?숈뾽 遺?댁뿉 ????댁빞湲곕? ?섎댋?듬땲?? ?쒓컙 愿由?諛⑸쾿怨??숈뒿 ?꾨왂?????議곗뼵?덉뒿?덈떎.'
        WHEN 2 THEN '?명꽩??吏?먯뿉 ????곷떞?덉뒿?덈떎. ?대젰???묒꽦怨?硫댁젒 以鍮??곸쓣 怨듭쑀?덉뒿?덈떎.'
        ELSE '議몄뾽 ??怨꾪쉷??????쇱쓽?덉뒿?덈떎. ??숈썝 吏꾪븰怨?痍⑥뾽 ?듭뀡???λ떒?먯쓣 ?ㅻ챸?덉뒿?덈떎.'
    END,
    FALSE,
    CURRENT_DATE - (ROW_NUMBER() OVER () * 7),
    CASE WHEN ROW_NUMBER() OVER () % 3 = 0 THEN TRUE ELSE FALSE END,
    CASE WHEN ROW_NUMBER() OVER () % 3 = 0 THEN CURRENT_DATE + INTERVAL '14 days' ELSE NULL END,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 25;

-- 愿李?湲곕줉 (observation)
INSERT INTO tb_advisor_note (
    advisor_user_id,
    student_id,
    note_type,
    title,
    content,
    is_private,
    follow_up_required,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'observation',
    '?숈깮 愿李?湲곕줉',
    CASE (ROW_NUMBER() OVER () % 5)
        WHEN 0 THEN '?섏뾽 李몄뿬?꾧? ?믨퀬 吏덈Ц???먯＜ ?⑸땲?? ?꾨줈洹몃옒諛띿뿉 ????댁젙???먭뺨吏묐땲??'
        WHEN 1 THEN '洹몃９ ?꾨줈?앺듃?먯꽌 由щ뜑??쓣 諛쒗쐶?섎뒗 紐⑥뒿??愿李곕릺?덉뒿?덈떎.'
        WHEN 2 THEN '理쒓렐 ?섏뾽 異쒖꽍瑜좎씠 ?議고빀?덈떎. 媛쒖씤?곸씤 ?대젮????덈뒗 寃껋쑝濡?蹂댁엯?덈떎.'
        WHEN 3 THEN '?숈뒿 ?띾룄媛 鍮좊Ⅴ怨?怨쇱젣 ?꾩꽦?꾧? ?믪뒿?덈떎. ?ы솕 怨쇱젙??異붿쿇???덉젙?낅땲??'
        ELSE '?숈븘由??쒕룞???곴레?곸쑝濡?李몄뿬?섍퀬 ?덉쑝硫???멸?怨꾧? ?먮쭔?⑸땲??'
    END,
    TRUE,
    CASE WHEN ROW_NUMBER() OVER () % 5 = 2 THEN TRUE ELSE FALSE END,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 20;

-- ?쇰컲 硫붾え (general)
INSERT INTO tb_advisor_note (
    advisor_user_id,
    student_id,
    note_type,
    title,
    content,
    is_private,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'general',
    '硫붾え',
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN '?ν븰湲??좎껌 ?덈궡 ?꾩슂'
        WHEN 1 THEN '?댁쇅 援먰솚?숈깮 ?꾨줈洹몃옩 愿???덉쓬'
        WHEN 2 THEN '蹂듭닔?꾧났 ?좎껌 ?덉젙 - 寃쎌쁺?숆낵'
        ELSE '?ㅼ쓬 ?숆린 ?섍컯?좎껌 ?곷떞 ?꾩슂'
    END,
    TRUE,
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 15;

-- ?≪뀡 ?꾩씠??(action_item)
INSERT INTO tb_advisor_note (
    advisor_user_id,
    student_id,
    note_type,
    title,
    content,
    is_private,
    follow_up_required,
    follow_up_date,
    ins_user_id
)
SELECT
    aa.advisor_user_id,
    aa.student_id,
    'action_item',
    '?꾩냽 議곗튂 ?꾩슂',
    CASE (ROW_NUMBER() OVER () % 4)
        WHEN 0 THEN '?숈깮?먭쾶 ?곗씠??遺꾩꽍 愿???명꽩???뺣낫 ?꾨떖 ?덉젙'
        WHEN 1 THEN '?대젰??寃?????쇰뱶諛??쒓났 ?덉젙'
        WHEN 2 THEN '?숆낵 ?ㅽ꽣??洹몃９???곌껐 ?덉젙'
        ELSE '硫섑넗留??꾨줈洹몃옩 李몄뿬 沅뚯쑀 ?덉젙'
    END,
    TRUE,
    TRUE,
    CURRENT_DATE + INTERVAL '7 days',
    'SEED_SCRIPT'
FROM tb_advisor_assignment aa
WHERE aa.assignment_type = 'primary' AND aa.status = 'active'
ORDER BY RANDOM()
LIMIT 10;

-- ============================================
-- 4. tb_cohort_snapshot - 肄뷀샇???ㅻ깄??(~30媛?
-- ============================================

-- 媛??숆낵, ?숇뀈蹂??ㅻ깄???앹꽦
INSERT INTO tb_cohort_snapshot (
    department_cd,
    grade_level,
    term_cd,
    snapshot_date,
    total_students,
    avg_gpa,
    avg_competency_scores,
    avg_skill_levels,
    risk_distribution,
    at_risk_students,
    goal_achievement_rate,
    opportunity_application_rate,
    badge_earning_rate,
    vs_prev_term,
    ins_user_id
)
SELECT
    d.department_cd,
    g.grade_level,
    '2025-2',
    CURRENT_DATE,
    COUNT(s.student_id),
    ROUND(AVG(s.gpa)::NUMERIC, 2),
    jsonb_build_object(
        'COMP001', 65 + FLOOR(RANDOM() * 20),
        'COMP002', 60 + FLOOR(RANDOM() * 25),
        'COMP003', 70 + FLOOR(RANDOM() * 15),
        'COMP004', 68 + FLOOR(RANDOM() * 18),
        'COMP005', 55 + FLOOR(RANDOM() * 25),
        'COMP006', 72 + FLOOR(RANDOM() * 18)
    ),
    jsonb_build_object(
        'python', 2.5 + RANDOM() * 1.5,
        'java', 2.0 + RANDOM() * 1.5,
        'sql', 2.3 + RANDOM() * 1.5
    ),
    jsonb_build_object(
        'critical', FLOOR(COUNT(s.student_id) * 0.05),
        'warning', FLOOR(COUNT(s.student_id) * 0.15),
        'info', FLOOR(COUNT(s.student_id) * 0.30)
    ),
    ARRAY(
        SELECT ra.student_id
        FROM tb_risk_alert ra
        WHERE ra.student_id IN (
            SELECT student_id FROM tb_student
            WHERE department_cd = d.department_cd AND current_grade = g.grade_level
        )
        AND ra.severity IN ('critical', 'warning')
        AND ra.status = 'active'
        LIMIT 5
    ),
    50 + FLOOR(RANDOM() * 35)::DECIMAL(5,2),
    20 + FLOOR(RANDOM() * 40)::DECIMAL(5,2),
    30 + FLOOR(RANDOM() * 50)::DECIMAL(5,2),
    jsonb_build_object(
        'gpa_change', ROUND((RANDOM() * 0.4 - 0.2)::NUMERIC, 2),
        'risk_change', CASE WHEN RANDOM() > 0.5 THEN 'improved' ELSE 'stable' END,
        'engagement_change', CASE WHEN RANDOM() > 0.3 THEN 'increased' ELSE 'stable' END
    ),
    'SEED_SCRIPT'
FROM tb_department d
CROSS JOIN (SELECT generate_series(1, 4) AS grade_level) g
LEFT JOIN tb_student s ON d.department_cd = s.department_cd AND g.grade_level = s.current_grade
WHERE d.use_fg = 'Y'
GROUP BY d.department_cd, g.grade_level
HAVING COUNT(s.student_id) > 0;

-- ============================================
-- 寃利?荑쇰━
-- ============================================

-- SELECT 'tb_advisor_assignment' as table_name, COUNT(*) as count FROM tb_advisor_assignment WHERE ins_user_id = 'SEED_SCRIPT'
-- UNION ALL
-- SELECT 'tb_advisor_intervention', COUNT(*) FROM tb_advisor_intervention WHERE ins_user_id = 'SEED_SCRIPT'
-- UNION ALL
-- SELECT 'tb_advisor_note', COUNT(*) FROM tb_advisor_note WHERE ins_user_id = 'SEED_SCRIPT'
-- UNION ALL
-- SELECT 'tb_cohort_snapshot', COUNT(*) FROM tb_cohort_snapshot WHERE ins_user_id = 'SEED_SCRIPT';
