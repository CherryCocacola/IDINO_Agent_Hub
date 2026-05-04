-- ============================================
-- IDINO Career - P1 Phase 9: Coaching Seed Data
-- Coaching Goals, Plans, Check-ins, Retrospectives
-- Created: 2026-01-07
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Coaching Goals (~220 records - 110 students 횞 2 goals avg)
-- ============================================

DELETE FROM tb_coaching_retrospective WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_coaching_checkin WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_coaching_plan WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT';

-- Career-focused goals for IT students
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'career',
    '諛깆뿏??媛쒕컻??痍⑥뾽 以鍮?,
    'Python/Java 湲곕컲 諛깆뿏??媛쒕컻????웾??媛뽰텛???湲곗뾽 ?먮뒗 IT 湲곗뾽??痍⑥뾽',
    'ROLE001',
    '{"skill_python": 4, "skill_java": 4, "skill_sql": 4, "projects": 3}'::JSONB,
    ('{"skill_python": ' || (2 + (RANDOM() * 2)::INT)::TEXT || ', "skill_java": ' || (1 + (RANDOM() * 2)::INT)::TEXT || ', "skill_sql": ' || (2 + (RANDOM() * 1)::INT)::TEXT || ', "projects": ' || (RANDOM() * 2)::INT::TEXT || '}')::JSONB,
    '2025-12-31',
    1,
    CASE WHEN RANDOM() > 0.2 THEN 'active' ELSE 'achieved' END,
    (RANDOM() * 70 + 20)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '180 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002')
LIMIT 20;

-- AI Engineer career goals
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'career',
    'AI ?붿??덉뼱 ??웾 媛쒕컻',
    'Machine Learning怨?Deep Learning ??웾??媛쒕컻?섏뿬 AI 遺꾩빞 痍⑥뾽 ?먮뒗 ??숈썝 吏꾪븰',
    'ROLE005',
    '{"skill_ml": 4, "skill_dl": 4, "skill_python": 5, "research_papers": 1}'::JSONB,
    ('{"skill_ml": ' || (1 + (RANDOM() * 2)::INT)::TEXT || ', "skill_dl": ' || (RANDOM() * 2)::INT::TEXT || ', "skill_python": ' || (2 + (RANDOM() * 2)::INT)::TEXT || ', "research_papers": 0}')::JSONB,
    '2026-06-30',
    1,
    'active',
    (RANDOM() * 50 + 10)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '120 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT013')
AND s.student_id NOT IN (SELECT student_id FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT')
LIMIT 15;

-- Competency improvement goals
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'competency',
    '臾몄젣?닿껐 ??웾 媛뺥솕',
    '?뚭퀬由ъ쬁 臾몄젣??댁? ?꾨줈?앺듃 寃쏀뿕???듯빐 臾몄젣?닿껐 ??웾??80???댁긽?쇰줈 ?μ긽',
    NULL,
    '{"COMP002": 80, "algorithm_problems": 100, "projects": 2}'::JSONB,
    ('{"COMP002": ' || (50 + (RANDOM() * 20)::INT)::TEXT || ', "algorithm_problems": ' || (10 + (RANDOM() * 40)::INT)::TEXT || ', "projects": ' || (RANDOM() * 2)::INT::TEXT || '}')::JSONB,
    '2025-08-31',
    2,
    'active',
    (RANDOM() * 60 + 20)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '90 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002', 'DEPT003')
LIMIT 25;

-- Skill development goals
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'skill',
    '?대씪?곕뱶 而댄벂???ㅽ궗 ?듬뱷',
    'AWS ?먮뒗 GCP ?먭꺽利?痍⑤뱷 諛??대씪?곕뱶 湲곕컲 ?꾨줈?앺듃 寃쏀뿕 異뺤쟻',
    NULL,
    '{"skill_cloud": 4, "certificates": 1, "cloud_projects": 2}'::JSONB,
    ('{"skill_cloud": ' || (1 + (RANDOM() * 1)::INT)::TEXT || ', "certificates": 0, "cloud_projects": ' || (RANDOM() * 1)::INT::TEXT || '}')::JSONB,
    '2025-10-31',
    2,
    'active',
    (RANDOM() * 40 + 10)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '60 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002', 'DEPT006')
LIMIT 20;

-- Academic goals (GPA improvement)
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'academic',
    '?숈젏 ?μ긽 ?꾨줈?앺듃',
    '???숆린 GPA 3.5 ?댁긽 ?ъ꽦???꾪븳 泥닿퀎?곸씤 ?숈뒿 怨꾪쉷 ?섎┰ 諛??ㅽ뻾',
    NULL,
    '{"gpa": 3.5, "study_hours_weekly": 30, "assignments_on_time": 100}'::JSONB,
    ('{"gpa": ' || (2.5 + RANDOM())::DECIMAL(3,2)::TEXT || ', "study_hours_weekly": ' || (15 + (RANDOM() * 10)::INT)::TEXT || ', "assignments_on_time": ' || (70 + (RANDOM() * 20)::INT)::TEXT || '}')::JSONB,
    '2025-06-20',
    1,
    'active',
    (RANDOM() * 55 + 25)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '45 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (1, 2)
LIMIT 30;

-- Activity goals (extracurricular)
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'activity',
    '?명꽩??諛???명솢??李몄뿬',
    '?숆린 以??먮뒗 諛⑺븰 湲곌컙 ?숈븞 ?명꽩????명솢?숈쓣 ?듯븳 ?ㅻТ 寃쏀뿕 異뺤쟻',
    NULL,
    '{"internships": 1, "competitions": 1, "club_activities": 2}'::JSONB,
    ('{"internships": 0, "competitions": ' || (RANDOM() * 1)::INT::TEXT || ', "club_activities": ' || (RANDOM() * 2)::INT::TEXT || '}')::JSONB,
    '2025-08-31',
    2,
    CASE WHEN RANDOM() > 0.3 THEN 'active' ELSE 'paused' END,
    (RANDOM() * 45 + 15)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '75 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (2, 3)
LIMIT 25;

-- Communication skills goals for business students
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'skill',
    '?꾨젅?좏뀒?댁뀡 ??웾 媛뺥솕',
    '諛쒗몴 ?λ젰怨??ㅻ뱷???덈뒗 而ㅻ??덉??댁뀡 ??웾 媛쒕컻',
    NULL,
    '{"presentation_score": 85, "public_speaking": 5, "feedback_score": 4.5}'::JSONB,
    ('{"presentation_score": ' || (60 + (RANDOM() * 20)::INT)::TEXT || ', "public_speaking": ' || (2 + (RANDOM() * 2)::INT)::TEXT || ', "feedback_score": ' || (3.0 + RANDOM())::DECIMAL(2,1)::TEXT || '}')::JSONB,
    '2025-09-30',
    2,
    'active',
    (RANDOM() * 50 + 30)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '50 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT014', 'DEPT025')
LIMIT 15;

-- Management Consultant career goals
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'career',
    '寃쎌쁺 而⑥꽕?댄듃 以鍮?,
    '遺꾩꽍?? 而ㅻ??덉??댁뀡, 由щ뜑????웾??媛뽰텣 寃쎌쁺 而⑥꽕?댄듃濡??깆옣',
    'ROLE009',
    '{"data_analysis": 4, "communication": 5, "leadership": 4, "english": 4}'::JSONB,
    ('{"data_analysis": ' || (2 + (RANDOM() * 1)::INT)::TEXT || ', "communication": ' || (3 + (RANDOM() * 1)::INT)::TEXT || ', "leadership": ' || (2 + (RANDOM() * 1)::INT)::TEXT || ', "english": ' || (2 + (RANDOM() * 2)::INT)::TEXT || '}')::JSONB,
    '2026-02-28',
    1,
    'active',
    (RANDOM() * 40 + 20)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '100 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd = 'DEPT014'
LIMIT 10;

-- Data Analyst career goals
INSERT INTO tb_coaching_goal (student_id, goal_type, title, description, target_role_cd, target_metrics, current_metrics, deadline, priority, status, achievement_rate, created_at, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'career',
    '?곗씠??遺꾩꽍媛 ??웾 媛쒕컻',
    'SQL, Python, ?듦퀎 ??웾??媛뽰텣 ?곗씠??遺꾩꽍媛濡??깆옣',
    'ROLE003',
    '{"sql": 5, "python": 4, "statistics": 4, "visualization": 4}'::JSONB,
    ('{"sql": ' || (2 + (RANDOM() * 2)::INT)::TEXT || ', "python": ' || (2 + (RANDOM() * 2)::INT)::TEXT || ', "statistics": ' || (3 + (RANDOM() * 1)::INT)::TEXT || ', "visualization": ' || (1 + (RANDOM() * 2)::INT)::TEXT || '}')::JSONB,
    '2025-12-31',
    1,
    'active',
    (RANDOM() * 50 + 25)::DECIMAL(5,2),
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '80 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd = 'DEPT013'
LIMIT 10;

-- ============================================
-- 2. Coaching Plans (~120 records)
-- ============================================

INSERT INTO tb_coaching_plan (goal_id, plan_version, milestones, weekly_hours_target, current_week, total_weeks, ai_generated, status, created_at, ins_user_id, ins_dt)
SELECT
    g.goal_id,
    1,
    CASE g.goal_type
        WHEN 'career' THEN '[
            {"week": 1, "task": "?꾩옱 ??웾 吏꾨떒 諛?紐⑺몴 ?ㅼ젙", "target": "?먭린 遺꾩꽍 ?꾨즺"},
            {"week": 2, "task": "?꾩슂 ?ㅽ궗 ?숈뒿 怨꾪쉷 ?섎┰", "target": "?숈뒿 濡쒕뱶留??꾩꽦"},
            {"week": 3, "task": "?⑤씪??媛뺤쥖 ?섍컯 ?쒖옉", "target": "1媛?媛뺤쥖 ?꾨즺"},
            {"week": 4, "task": "?꾨줈?앺듃 ?꾩씠?붿뼱 援ъ긽", "target": "?꾨줈?앺듃 怨꾪쉷???묒꽦"},
            {"week": 5, "task": "媛쒖씤 ?꾨줈?앺듃 吏꾪뻾", "target": "MVP ?꾩꽦"},
            {"week": 6, "task": "?ы듃?대━???뺣━", "target": "GitHub ?낅뜲?댄듃"},
            {"week": 7, "task": "?대젰???먭린?뚭컻???묒꽦", "target": "珥덉븞 ?꾩꽦"},
            {"week": 8, "task": "紐⑥쓽 硫댁젒 以鍮?, "target": "硫댁젒 吏덈Ц ?뺣━"}
        ]'::JSONB
        WHEN 'competency' THEN '[
            {"week": 1, "task": "?뚭퀬由ъ쬁 湲곗큹 ?숈뒿", "target": "湲곗큹 臾몄젣 20媛????},
            {"week": 2, "task": "?먮즺援ъ“ 蹂듭뒿", "target": "?듭떖 ?먮즺援ъ“ ?뺣━"},
            {"week": 3, "task": "以묎툒 臾몄젣 ???, "target": "以묎툒 臾몄젣 15媛????},
            {"week": 4, "task": "肄붾뵫?뚯뒪??紐⑥쓽?쒗뿕", "target": "2?쒓컙 ?뚯뒪???묒떆"}
        ]'::JSONB
        WHEN 'skill' THEN '[
            {"week": 1, "task": "湲곗큹 媛쒕뀗 ?숈뒿", "target": "湲곗큹 媛뺤쓽 ?섍컯"},
            {"week": 2, "task": "?몄쫰???ㅼ뒿", "target": "?ㅼ뒿 ?꾨줈?앺듃 1媛?},
            {"week": 3, "task": "?ы솕 ?숈뒿", "target": "?ы솕 媛뺤쓽 ?섍컯"},
            {"week": 4, "task": "?먭꺽利??쒗뿕 以鍮?, "target": "紐⑥쓽?쒗뿕 ?묒떆"},
            {"week": 5, "task": "?먭꺽利??쒗뿕 ?묒떆", "target": "?쒗뿕 ?⑷꺽"},
            {"week": 6, "task": "?ㅼ쟾 ?꾨줈?앺듃 ?곸슜", "target": "?꾨줈?앺듃 ?꾨즺"}
        ]'::JSONB
        WHEN 'academic' THEN '[
            {"week": 1, "task": "?숈뒿 怨꾪쉷 ?섎┰", "target": "二쇨컙 ?숈뒿 ?ㅼ?以??묒꽦"},
            {"week": 2, "task": "怨쇱젣 ?쇱젙 愿由?, "target": "怨쇱젣 留덇컧??罹섎┛???깅줉"},
            {"week": 3, "task": "以묎컙怨좎궗 以鍮?, "target": "蹂듭뒿 ?명듃 ?뺣━"},
            {"week": 4, "task": "?ㅽ꽣??洹몃９ 李몄뿬", "target": "二?2???ㅽ꽣??}
        ]'::JSONB
        ELSE '[
            {"week": 1, "task": "紐⑺몴 援ъ껜??, "target": "?몃? 怨꾪쉷 ?섎┰"},
            {"week": 2, "task": "?ㅽ뻾 ?쒖옉", "target": "泥?踰덉㎏ 留덉씪?ㅽ넠 ?ъ꽦"},
            {"week": 3, "task": "以묎컙 ?먭?", "target": "吏꾪뻾 ?곹솴 ?됯?"},
            {"week": 4, "task": "議곗젙 諛??꾨즺", "target": "紐⑺몴 ?ъ꽦"}
        ]'::JSONB
    END,
    CASE g.goal_type
        WHEN 'career' THEN 15
        WHEN 'academic' THEN 25
        ELSE 10
    END,
    GREATEST(1, (RANDOM() * 4)::INT),
    CASE g.goal_type
        WHEN 'career' THEN 8
        WHEN 'competency' THEN 4
        WHEN 'skill' THEN 6
        WHEN 'academic' THEN 4
        ELSE 4
    END,
    TRUE,
    CASE WHEN RANDOM() > 0.15 THEN 'active' ELSE 'completed' END,
    g.created_at + INTERVAL '1 day',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT';

-- ============================================
-- 3. Coaching Check-ins (~250 records)
-- ============================================

INSERT INTO tb_coaching_checkin (plan_id, week_number, checkin_date, completed_tasks, hours_spent, blockers, wins, mood_score, ai_feedback, ai_suggestions, progress_score, on_track, ins_user_id, ins_dt)
SELECT
    p.plan_id,
    week_num,
    p.created_at::DATE + (week_num * 7),
    CASE
        WHEN week_num <= 2 THEN '[{"task_id": "1", "completed": true, "notes": "?쒖“濡?쾶 吏꾪뻾"}]'::JSONB
        WHEN week_num <= 4 THEN '[{"task_id": "2", "completed": true, "notes": "?덉젙?濡??꾨즺"}, {"task_id": "3", "completed": false, "notes": "異붽? ?쒓컙 ?꾩슂"}]'::JSONB
        ELSE jsonb_build_array(jsonb_build_object('task_id', week_num::TEXT, 'completed', RANDOM() > 0.3, 'notes', '泥댄겕???꾨즺'))
    END,
    (p.weekly_hours_target * (0.6 + RANDOM() * 0.6))::DECIMAL(4,1),
    CASE
        WHEN RANDOM() > 0.7 THEN '?쒓컙 遺議깆쑝濡?怨꾪쉷蹂대떎 吏?곕맖'
        WHEN RANDOM() > 0.5 THEN '?ㅻⅨ 怨쇱젣? 蹂묓뻾?섎뒓??吏묒쨷 ?대젮?'
        ELSE NULL
    END,
    CASE
        WHEN RANDOM() > 0.6 THEN '紐⑺몴??遺꾨웾???꾩닔??
        WHEN RANDOM() > 0.3 THEN '?덈줈??媛쒕뀗???댄빐?섍쾶 ??
        ELSE '袁몄???吏꾪뻾 以?
    END,
    (2 + (RANDOM() * 3)::INT),
    CASE
        WHEN RANDOM() > 0.5 THEN '?꾩옱 吏꾪뻾 ?곹솴??醫뗭뒿?덈떎. ???섏씠?ㅻ? ?좎??섏꽭??'
        ELSE '議곌툑 ??吏묒쨷???꾩슂?⑸땲?? ?묒? 紐⑺몴遺???ъ꽦?대낫?몄슂.'
    END,
    CASE
        WHEN RANDOM() > 0.5 THEN '["二쇰쭚??異붽? ?숈뒿 ?쒓컙 ?뺣낫", "?ㅽ꽣??洹몃９ 李몄뿬 沅뚯옣"]'::JSONB
        ELSE '["?쇱씪 ?숈뒿 ?쒓컙 30遺?利앷?", "蹂듭뒿 ?쒓컙 ?뺣낫"]'::JSONB
    END,
    (50 + RANDOM() * 40)::DECIMAL(5,2),
    RANDOM() > 0.35,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_plan p
CROSS JOIN generate_series(1, LEAST(p.current_week, p.total_weeks)) AS week_num
WHERE p.ins_user_id = 'SEED_SCRIPT';

-- ============================================
-- 4. Coaching Retrospectives (~60 records)
-- ============================================

INSERT INTO tb_coaching_retrospective (goal_id, period_start, period_end, what_went_well, what_could_improve, lessons_learned, initial_metrics, final_metrics, improvement_percentage, ai_summary, ai_insights, next_period_recommendations, ins_user_id, ins_dt)
SELECT
    g.goal_id,
    g.created_at::DATE,
    g.created_at::DATE + INTERVAL '30 days',
    CASE g.goal_type
        WHEN 'career' THEN '袁몄????숈뒿 ?듦????뺤꽦?덇퀬, ?ы듃?대━???꾨줈?앺듃瑜??쒖옉??
        WHEN 'competency' THEN '?뚭퀬由ъ쬁 臾몄젣????ㅻ젰???μ긽??
        WHEN 'skill' THEN '?덈줈??湲곗닠 ?ㅽ깮?????湲곗큹瑜??ㅼ쭚'
        WHEN 'academic' THEN '?섏뾽 異쒖꽍瑜좉낵 怨쇱젣 ?쒖텧瑜좎씠 ?μ긽??
        ELSE '紐⑺몴?????紐낇솗??諛⑺뼢?깆쓣 ?ㅼ젙??
    END,
    CASE g.goal_type
        WHEN 'career' THEN '?ㅻТ 寃쏀뿕 遺議? ?ㅽ듃?뚰궧 湲고쉶 ?뺣? ?꾩슂'
        WHEN 'competency' THEN '?대젮??臾몄젣?먯꽌 留됲엳??寃쎌슦媛 ?덉쓬'
        WHEN 'skill' THEN '?ㅼ쟾 ?꾨줈?앺듃 ?곸슜 寃쏀뿕 遺議?
        WHEN 'academic' THEN '?쒗뿕 湲곌컙 吏묒쨷??愿由??꾩슂'
        ELSE '?쒓컙 愿由?媛쒖꽑 ?꾩슂'
    END,
    CASE g.goal_type
        WHEN 'career' THEN '?묒? ?꾨줈?앺듃遺???꾩꽦?섎뒗 寃껋씠 以묒슂?섎떎??寃껋쓣 諛곗?'
        WHEN 'competency' THEN '諛섎났 ?숈뒿??以묒슂?깆쓣 源⑤떖??
        WHEN 'skill' THEN '?ㅼ뒿???듯븳 ?숈뒿??媛???④낵??
        WHEN 'academic' THEN '怨꾪쉷?곸씤 ?숈뒿???깆쟻 ?μ긽??吏곸젒???곹뼢'
        ELSE '袁몄??⑥씠 媛??以묒슂?섎떎'
    END,
    g.current_metrics,
    (SELECT jsonb_object_agg(key, (value::TEXT::NUMERIC * (1.1 + RANDOM() * 0.2))::INT::TEXT)
     FROM jsonb_each_text(g.current_metrics)),
    (10 + RANDOM() * 25)::DECIMAL(5,2),
    '?대쾲 湲곌컙 ?숈븞 ' || g.title || ' 紐⑺몴瑜??ν빐 袁몄????몃젰?덉뒿?덈떎. ?꾨컲?곸쑝濡?湲띿젙?곸씤 吏꾩쟾???덉뿀?쇰ŉ, 紐?媛吏 媛쒖꽑?먯쓣 諛쒓껄?덉뒿?덈떎.',
    '["紐⑺몴 ?ъ꽦瑜좎씠 ?덉긽蹂대떎 ?믪쓬", "?쒓컙 ?ъ옄 ?鍮??⑥쑉??媛쒖꽑 ?꾩슂", "?ㅼ쓬 ?④퀎 以鍮?沅뚯옣"]'::JSONB,
    '["怨좉툒 怨쇱젙 ?꾩쟾", "?ㅼ쟾 ?꾨줈?앺듃 李몄뿬", "硫섑넗留??꾨줈洹몃옩 ?쒖슜"]'::JSONB,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT'
AND g.status IN ('active', 'achieved')
AND RANDOM() > 0.4;

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    goal_count INT;
    plan_count INT;
    checkin_count INT;
    retro_count INT;
BEGIN
    SELECT COUNT(*) INTO goal_count FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO plan_count FROM tb_coaching_plan WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO checkin_count FROM tb_coaching_checkin WHERE ins_user_id = 'SEED_SCRIPT';
    SELECT COUNT(*) INTO retro_count FROM tb_coaching_retrospective WHERE ins_user_id = 'SEED_SCRIPT';

    RAISE NOTICE '=== P1 Coaching Seed Data Created ===';
    RAISE NOTICE 'tb_coaching_goal: % records', goal_count;
    RAISE NOTICE 'tb_coaching_plan: % records', plan_count;
    RAISE NOTICE 'tb_coaching_checkin: % records', checkin_count;
    RAISE NOTICE 'tb_coaching_retrospective: % records', retro_count;
END $$;
