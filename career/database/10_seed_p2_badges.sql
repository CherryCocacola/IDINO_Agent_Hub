-- ============================================
-- IDINO Career - P2 Badges Seed Data
-- Phase 11: Skill Passport/Badges
-- Created: 2026-01-07
-- Description: 諭껋? ?뺤쓽, ?숈깮 諭껋?, ?ㅽ궗 ?⑥뒪?ы듃 ?곗씠??-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. tb_badge - 諭껋? ?뺤쓽 (25媛?
-- ============================================

-- 湲곗〈 ?곗씠????젣 (seed script濡??앹꽦??寃껊쭔)
DELETE FROM tb_student_badge WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_skill_passport WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_badge WHERE ins_user_id = 'SEED_SCRIPT';

-- ?ㅽ궗 湲곕컲 諭껋? (10媛?
INSERT INTO tb_badge (badge_cd, badge_nm, badge_nm_en, description, category, criteria, points, rarity, ins_user_id) VALUES
('BADGE_SKL_PY', 'Python 留덉뒪??, 'Python Master', 'Python ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL001", "level": 4}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_SKL_JV', 'Java ?꾨Ц媛', 'Java Expert', 'Java ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL002", "level": 4}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_SKL_JS', 'JavaScript ?μ닕??, 'JavaScript Proficient', 'JavaScript ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL003", "level": 4}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_SKL_ML', 'ML ?곌뎄??, 'ML Researcher', 'Machine Learning ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL005", "level": 4}', 150, 'epic', 'SEED_SCRIPT'),
('BADGE_SKL_DL', 'Deep Learning ?꾨Ц媛', 'Deep Learning Expert', 'Deep Learning ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL006", "level": 4}', 200, 'epic', 'SEED_SCRIPT'),
('BADGE_SKL_SQL', 'SQL 留덉뒪??, 'SQL Master', 'SQL ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL004", "level": 4}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_SKL_COMM', '而ㅻ??덉??댄꽣', 'Communicator', '而ㅻ??덉??댁뀡 ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL010", "level": 4}', 80, 'uncommon', 'SEED_SCRIPT'),
('BADGE_SKL_LEAD', '由щ뜑??諛쒗쐶', 'Leadership Excellence', '由щ뜑???ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL011", "level": 4}', 120, 'rare', 'SEED_SCRIPT'),
('BADGE_SKL_REACT', 'React 媛쒕컻??, 'React Developer', 'React ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL007", "level": 4}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_SKL_CLOUD', '?대씪?곕뱶 ?꾨Ц媛', 'Cloud Expert', 'Cloud Computing ?ㅽ궗 ?덈꺼 4 ?댁긽 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SKL009", "level": 4}', 150, 'epic', 'SEED_SCRIPT');

-- ??웾 湲곕컲 諭껋? (6媛?
INSERT INTO tb_badge (badge_cd, badge_nm, badge_nm_en, description, category, criteria, points, rarity, ins_user_id) VALUES
('BADGE_CMP_PS', '臾몄젣?닿껐 ?ъ씤', 'Problem Solver', '臾몄젣?닿껐 ??웾 ?먯닔 80???댁긽', 'competency', '{"type": "competency", "competency_cd": "COMP001", "score": 80}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_CMP_CR', '李쎌쓽???ш퀬', 'Creative Thinker', '李쎌쓽?듯빀 ??웾 ?먯닔 80???댁긽', 'competency', '{"type": "competency", "competency_cd": "COMP002", "score": 80}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_CMP_CM', '?뚰넻 ?꾨Ц媛', 'Communication Pro', '?섏궗?뚰넻 ??웾 ?먯닔 80???댁긽', 'competency', '{"type": "competency", "competency_cd": "COMP003", "score": 80}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_CMP_TB', '? ?뚮젅?댁뼱', 'Team Player', '?묒뾽 ??웾 ?먯닔 80???댁긽', 'competency', '{"type": "competency", "competency_cd": "COMP004", "score": 80}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_CMP_GL', '湲濡쒕쾶 ?몄옱', 'Global Talent', '湲濡쒕쾶 ??웾 ?먯닔 80???댁긽', 'competency', '{"type": "competency", "competency_cd": "COMP005", "score": 80}', 120, 'epic', 'SEED_SCRIPT'),
('BADGE_CMP_DG', '?붿????먯＜誘?, 'Digital Native', '?붿??몄뿭???먯닔 80???댁긽', 'competency', '{"type": "competency", "competency_cd": "COMP006", "score": 80}', 100, 'rare', 'SEED_SCRIPT');

-- ?깆랬 湲곕컲 諭껋? (5媛?
INSERT INTO tb_badge (badge_cd, badge_nm, badge_nm_en, description, category, criteria, points, rarity, ins_user_id) VALUES
('BADGE_ACH_DEAN', '?숈옣??, 'Dean''s List', 'GPA 4.0 ?댁긽 ?ъ꽦', 'achievement', '{"type": "gpa", "min_gpa": 4.0}', 200, 'legendary', 'SEED_SCRIPT'),
('BADGE_ACH_HONOR', '?곕벑??, 'Honor Student', 'GPA 3.5 ?댁긽 ?ъ꽦', 'achievement', '{"type": "gpa", "min_gpa": 3.5}', 100, 'rare', 'SEED_SCRIPT'),
('BADGE_ACH_INTERN', '?명꽩???꾨즺', 'Internship Complete', '?명꽩??1???댁긽 ?꾨즺', 'achievement', '{"type": "opportunity", "opportunity_type": "internship", "count": 1}', 150, 'epic', 'SEED_SCRIPT'),
('BADGE_ACH_CONTEST', '怨듬え???섏긽', 'Contest Winner', '怨듬え???섏긽 寃쎈젰', 'achievement', '{"type": "opportunity", "opportunity_type": "contest", "status": "accepted"}', 180, 'epic', 'SEED_SCRIPT'),
('BADGE_ACH_RESEARCH', '?곌뎄 李몄뿬', 'Research Participant', '?곌뎄???꾨줈?앺듃 李몄뿬', 'achievement', '{"type": "opportunity", "opportunity_type": "lab", "count": 1}', 120, 'rare', 'SEED_SCRIPT');

-- 留덉씪?ㅽ넠 諭껋? (4媛?
INSERT INTO tb_badge (badge_cd, badge_nm, badge_nm_en, description, category, criteria, points, rarity, ins_user_id) VALUES
('BADGE_MS_START', '泥?諛쒓구??, 'First Step', '?ㅽ궗 1媛??댁긽 ?깅줉', 'milestone', '{"type": "skill_count", "count": 1}', 10, 'common', 'SEED_SCRIPT'),
('BADGE_MS_GROW', '?깆옣 以?, 'Growing', '?ㅽ궗 5媛??댁긽 ?깅줉', 'milestone', '{"type": "skill_count", "count": 5}', 30, 'uncommon', 'SEED_SCRIPT'),
('BADGE_MS_EXPERT', '?ㅼ옱?ㅻ뒫', 'Multi-talented', '?ㅽ궗 10媛??댁긽 ?깅줉', 'milestone', '{"type": "skill_count", "count": 10}', 80, 'rare', 'SEED_SCRIPT'),
('BADGE_MS_GOAL', '紐⑺몴 ?ъ꽦??, 'Goal Achiever', '肄붿묶 紐⑺몴 3媛??댁긽 ?꾨즺', 'milestone', '{"type": "goal_count", "status": "completed", "count": 3}', 100, 'rare', 'SEED_SCRIPT');

-- ============================================
-- 2. tb_student_badge - ?숈깮 諭껋? ?띾뱷 (~300媛?
-- ============================================

-- 留덉씪?ㅽ넠 諭껋? - 泥?諛쒓구??(紐⑤뱺 ?숈깮)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    s.student_id,
    'BADGE_MS_START',
    '[{"type": "skill_registration", "count": 1}]'::jsonb,
    'verified',
    'SEED_SCRIPT'
FROM tb_student s
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- 留덉씪?ㅽ넠 諭껋? - ?깆옣 以?(?ㅽ궗 5媛??댁긽 ?숈깮)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_MS_GROW',
    jsonb_build_array(jsonb_build_object('type', 'skill_count', 'count', COUNT(*))),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
GROUP BY ss.student_id
HAVING COUNT(*) >= 5
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?ㅽ궗 諭껋? - Python 留덉뒪??(Python ?덈꺼 4+ ?숈깮)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_SKL_PY',
    jsonb_build_array(jsonb_build_object('type', 'skill', 'skill_cd', 'SKL001', 'level', ss.current_level)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
WHERE ss.skill_cd = 'SKL001' AND ss.current_level >= 4
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?ㅽ궗 諭껋? - Java ?꾨Ц媛
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_SKL_JV',
    jsonb_build_array(jsonb_build_object('type', 'skill', 'skill_cd', 'SKL002', 'level', ss.current_level)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
WHERE ss.skill_cd = 'SKL002' AND ss.current_level >= 4
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?ㅽ궗 諭껋? - SQL 留덉뒪??INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_SKL_SQL',
    jsonb_build_array(jsonb_build_object('type', 'skill', 'skill_cd', 'SKL004', 'level', ss.current_level)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
WHERE ss.skill_cd = 'SKL004' AND ss.current_level >= 4
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?ㅽ궗 諭껋? - ML ?곌뎄??INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_SKL_ML',
    jsonb_build_array(jsonb_build_object('type', 'skill', 'skill_cd', 'SKL005', 'level', ss.current_level)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
WHERE ss.skill_cd = 'SKL005' AND ss.current_level >= 4
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?ㅽ궗 諭껋? - 而ㅻ??덉??댄꽣
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_SKL_COMM',
    jsonb_build_array(jsonb_build_object('type', 'skill', 'skill_cd', 'SKL010', 'level', ss.current_level)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
WHERE ss.skill_cd = 'SKL010' AND ss.current_level >= 4
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?ㅽ궗 諭껋? - 由щ뜑??諛쒗쐶
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    ss.student_id,
    'BADGE_SKL_LEAD',
    jsonb_build_array(jsonb_build_object('type', 'skill', 'skill_cd', 'SKL011', 'level', ss.current_level)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_skill ss
WHERE ss.skill_cd = 'SKL011' AND ss.current_level >= 4
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?깆랬 諭껋? - ?곕벑??(GPA 3.5+)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    s.student_id,
    'BADGE_ACH_HONOR',
    jsonb_build_array(jsonb_build_object('type', 'gpa', 'value', s.gpa)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.gpa >= 3.5
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?깆랬 諭껋? - ?숈옣??(GPA 4.0+)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    s.student_id,
    'BADGE_ACH_DEAN',
    jsonb_build_array(jsonb_build_object('type', 'gpa', 'value', s.gpa)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student s
WHERE s.gpa >= 4.0
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ?깆랬 諭껋? - ?명꽩???꾨즺 (吏??accepted ?숈깮)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT DISTINCT
    oa.student_id,
    'BADGE_ACH_INTERN',
    jsonb_build_array(jsonb_build_object('type', 'opportunity', 'opportunity_type', 'internship')),
    'verified',
    'SEED_SCRIPT'
FROM tb_opportunity_application oa
JOIN tb_opportunity o ON oa.opportunity_id = o.opportunity_id
WHERE o.opportunity_type = 'internship' AND oa.status = 'accepted'
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ??웾 諭껋? - 臾몄젣?닿껐 ?ъ씤 (?먯닔 80+)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    sc.student_id,
    'BADGE_CMP_PS',
    jsonb_build_array(jsonb_build_object('type', 'competency', 'competency_cd', 'COMP001', 'score', sc.score)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_competency sc
WHERE sc.competency_cd = 'COMP001' AND sc.score >= 80
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ??웾 諭껋? - ?뚰넻 ?꾨Ц媛
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    sc.student_id,
    'BADGE_CMP_CM',
    jsonb_build_array(jsonb_build_object('type', 'competency', 'competency_cd', 'COMP003', 'score', sc.score)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_competency sc
WHERE sc.competency_cd = 'COMP003' AND sc.score >= 80
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ??웾 諭껋? - ? ?뚮젅?댁뼱
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    sc.student_id,
    'BADGE_CMP_TB',
    jsonb_build_array(jsonb_build_object('type', 'competency', 'competency_cd', 'COMP004', 'score', sc.score)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_competency sc
WHERE sc.competency_cd = 'COMP004' AND sc.score >= 80
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ??웾 諭껋? - ?붿????먯＜誘?INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    sc.student_id,
    'BADGE_CMP_DG',
    jsonb_build_array(jsonb_build_object('type', 'competency', 'competency_cd', 'COMP006', 'score', sc.score)),
    'verified',
    'SEED_SCRIPT'
FROM tb_student_competency sc
WHERE sc.competency_cd = 'COMP006' AND sc.score >= 80
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- 紐⑺몴 ?ъ꽦??諭껋? (?꾨즺??紐⑺몴 3媛??댁긽)
INSERT INTO tb_student_badge (student_id, badge_cd, evidence_items, verification_status, ins_user_id)
SELECT
    cg.student_id,
    'BADGE_MS_GOAL',
    jsonb_build_array(jsonb_build_object('type', 'goal_count', 'count', COUNT(*))),
    'verified',
    'SEED_SCRIPT'
FROM tb_coaching_goal cg
WHERE cg.status = 'completed'
GROUP BY cg.student_id
HAVING COUNT(*) >= 3
ON CONFLICT (student_id, badge_cd) DO NOTHING;

-- ============================================
-- 3. tb_skill_passport - ?ㅽ궗 ?⑥뒪?ы듃 (~110媛?
-- ============================================

-- 紐⑤뱺 ?숈깮??????ㅽ궗 ?⑥뒪?ы듃 ?앹꽦
INSERT INTO tb_skill_passport (
    student_id,
    public_url_slug,
    is_public,
    headline,
    bio,
    featured_badges,
    featured_skills,
    social_links,
    view_count,
    ins_user_id
)
SELECT
    s.student_id,
    LOWER(REPLACE(s.student_nm, ' ', '-')) || '-' || s.student_id,
    CASE WHEN s.current_grade >= 3 THEN TRUE ELSE FALSE END,
    CASE s.current_grade
        WHEN 1 THEN '?댁젙?곸씤 1?숇뀈 ?숈깮?낅땲??
        WHEN 2 THEN '?깆옣?섎뒗 2?숇뀈 ?숈깮?낅땲??
        WHEN 3 THEN '痍⑥뾽??以鍮꾪븯??3?숇뀈 ?숈깮?낅땲??
        WHEN 4 THEN '議몄뾽???욌몦 4?숇뀈 ?숈깮?낅땲??
    END,
    d.department_nm || ' ?꾧났?쇰줈 ' ||
    CASE
        WHEN d.department_cd IN ('CS', 'SW', 'AI') THEN '?뚰봽?몄썾??媛쒕컻 諛?AI 遺꾩빞??愿?ъ씠 ?덉뒿?덈떎.'
        WHEN d.department_cd IN ('EE', 'ME') THEN '?섎뱶?⑥뼱? ?쒖뒪???ㅺ퀎??愿?ъ씠 ?덉뒿?덈떎.'
        WHEN d.department_cd IN ('BA', 'ECON') THEN '鍮꾩쫰?덉뒪? ?곗씠??遺꾩꽍??愿?ъ씠 ?덉뒿?덈떎.'
        ELSE '?ㅼ뼇??遺꾩빞??愿?ъ쓣 媛吏怨?怨듬??섍퀬 ?덉뒿?덈떎.'
    END,
    -- featured_badges: ?숈깮???띾뱷??諭껋? 以??곸쐞 3媛?    (SELECT ARRAY_AGG(sb.badge_cd) FROM (
        SELECT badge_cd FROM tb_student_badge
        WHERE student_id = s.student_id
        ORDER BY earned_at DESC LIMIT 3
    ) sb),
    -- featured_skills: ?숈깮???곸쐞 3媛??ㅽ궗
    (SELECT ARRAY_AGG(ss.skill_cd) FROM (
        SELECT skill_cd FROM tb_student_skill
        WHERE student_id = s.student_id
        ORDER BY current_level DESC LIMIT 3
    ) ss),
    CASE
        WHEN s.current_grade >= 3 THEN '{"github": "https://github.com/student' || s.student_id || '", "linkedin": "https://linkedin.com/in/student' || s.student_id || '"}'::jsonb
        ELSE '{}'::jsonb
    END,
    FLOOR(RANDOM() * 100)::INT,
    'SEED_SCRIPT'
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
ON CONFLICT (student_id) DO NOTHING;

-- ============================================
-- 寃利?荑쇰━
-- ============================================

-- SELECT 'tb_badge' as table_name, COUNT(*) as count FROM tb_badge WHERE ins_user_id = 'SEED_SCRIPT'
-- UNION ALL
-- SELECT 'tb_student_badge', COUNT(*) FROM tb_student_badge WHERE ins_user_id = 'SEED_SCRIPT'
-- UNION ALL
-- SELECT 'tb_skill_passport', COUNT(*) FROM tb_skill_passport WHERE ins_user_id = 'SEED_SCRIPT';
