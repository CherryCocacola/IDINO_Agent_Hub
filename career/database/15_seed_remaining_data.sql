-- ============================================
-- 15. 남은 메뉴 데이터 시드 스크립트
-- ============================================
SET search_path TO idino_career, public;

-- ============================================
-- 1. 스킬 갭 분석 데이터 (올바른 role_cd 사용)
-- ============================================
INSERT INTO tb_skill_gap_analysis (analysis_id, student_id, target_role_cd, analysis_date, overall_gap_score, gap_details, top_priority_skills, recommended_actions, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    CASE
        WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' OR d.department_nm LIKE '%AI%' OR d.department_nm LIKE '%정보%' THEN 'ROLE07'
        WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%' THEN 'ROLE09'
        WHEN d.department_nm LIKE '%디자인%' THEN 'ROLE04'
        WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%' THEN 'ROLE01'
        ELSE 'ROLE03'
    END,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 30)::INT,
    ROUND((30 + RANDOM() * 40)::NUMERIC, 1),
    jsonb_build_object(
        'programming', jsonb_build_object('current', ROUND((40 + RANDOM() * 40)::NUMERIC, 1), 'required', 80, 'gap', ROUND((20 + RANDOM() * 30)::NUMERIC, 1)),
        'communication', jsonb_build_object('current', ROUND((50 + RANDOM() * 30)::NUMERIC, 1), 'required', 75, 'gap', ROUND((10 + RANDOM() * 20)::NUMERIC, 1)),
        'problem_solving', jsonb_build_object('current', ROUND((45 + RANDOM() * 35)::NUMERIC, 1), 'required', 85, 'gap', ROUND((15 + RANDOM() * 25)::NUMERIC, 1))
    ),
    ARRAY['프로그래밍', '데이터분석', '커뮤니케이션']::VARCHAR[],
    jsonb_build_array(
        jsonb_build_object('action', '온라인 코딩 강좌 수강', 'priority', 'high', 'expected_improvement', 15),
        jsonb_build_object('action', '프로젝트 경험 쌓기', 'priority', 'medium', 'expected_improvement', 20)
    ),
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd::VARCHAR = d.department_cd::VARCHAR
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_skill_gap_analysis sg WHERE sg.student_id = s.student_id);

-- ============================================
-- 2. 코칭 계획 데이터 (올바른 컬럼명)
-- ============================================
INSERT INTO tb_coaching_plan (plan_id, goal_id, title, description, order_index, due_date, estimated_hours, is_completed, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    cg.goal_id,
    CASE (ROW_NUMBER() OVER (PARTITION BY cg.std_id ORDER BY cg.goal_id)) % 4
        WHEN 0 THEN '전공 기초 학습 계획'
        WHEN 1 THEN '자격증 취득 로드맵'
        WHEN 2 THEN '인턴십 준비 계획'
        ELSE '포트폴리오 구축 계획'
    END,
    CASE (ROW_NUMBER() OVER (PARTITION BY cg.std_id ORDER BY cg.goal_id)) % 4
        WHEN 0 THEN '전공 핵심 과목을 체계적으로 학습하고 실습 프로젝트를 진행합니다.'
        WHEN 1 THEN '관련 자격증 취득을 위한 학습 일정과 모의고사 계획입니다.'
        WHEN 2 THEN '인턴십 지원을 위한 이력서 작성, 면접 준비, 기업 리서치 계획입니다.'
        ELSE '개인 프로젝트와 협업 경험을 정리하여 포트폴리오를 완성합니다.'
    END,
    (ROW_NUMBER() OVER (PARTITION BY cg.std_id ORDER BY cg.goal_id))::INT,
    CURRENT_DATE + INTERVAL '3 months',
    FLOOR(20 + RANDOM() * 80)::INT,
    RANDOM() < 0.3,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal cg
JOIN tb_student s ON cg.std_id = s.student_id
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_coaching_plan cp WHERE cp.goal_id = cg.goal_id)
LIMIT 10000;

-- ============================================
-- 3. 시뮬레이션 시나리오 (올바른 컬럼명)
-- ============================================
INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, description, base_state, changes, predicted_outcomes, confidence_level, created_at, is_favorite, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    scenarios.scenario_type,
    scenarios.title,
    scenarios.description,
    scenarios.base_state::JSONB,
    scenarios.changes::JSONB,
    scenarios.predicted_outcomes::JSONB,
    ROUND((0.65 + RANDOM() * 0.25)::NUMERIC, 2),
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 30)::INT,
    RANDOM() < 0.2,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd::VARCHAR = d.department_cd::VARCHAR
CROSS JOIN (
    VALUES
    ('career_path', '대기업 취업 시나리오', '삼성전자 등 대기업 취업을 목표로 한 시나리오 분석',
     '{"current_gpa": 3.5, "current_skills": ["프로그래밍", "영어"], "career_goal": "개발자"}',
     '{"added_skills": ["알고리즘", "시스템설계"], "target_company": "삼성전자", "timeline": "2년"}',
     '{"employability_score": 0.78, "skill_match": 0.82, "market_demand": 0.75}'),
    ('skill_development', '프로그래밍 역량 강화', '6개월 내 프로그래밍 역량 중급 이상 달성 시나리오',
     '{"current_level": "초급", "study_hours_per_week": 10}',
     '{"target_level": "중급", "additional_courses": ["자료구조", "알고리즘"], "project_count": 2}',
     '{"skill_improvement": 0.85, "portfolio_strength": 0.70, "confidence_boost": 0.60}'),
    ('opportunity', '해외 인턴십 기회', '해외 인턴십 지원 및 합격 시나리오',
     '{"english_score": "TOEIC 800", "current_experience": "교내 프로젝트 2건"}',
     '{"target_score": "TOEIC 900", "add_experience": ["국내 인턴십", "오픈소스 기여"]}',
     '{"acceptance_probability": 0.45, "network_expansion": 0.80, "career_impact": 0.90}')
) AS scenarios(scenario_type, title, description, base_state, changes, predicted_outcomes)
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_simulation_scenario ss
    WHERE ss.student_id = s.student_id AND ss.title = scenarios.title
)
AND RANDOM() < 0.3;

-- ============================================
-- 4. 스킬 패스포트 (올바른 컬럼명)
-- ============================================
INSERT INTO tb_skill_passport (passport_id, student_id, overall_score, total_badges, total_skills, verified_skills, passport_data, last_updated, is_public, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    FLOOR(30 + RANDOM() * 70)::INT,
    FLOOR(2 + RANDOM() * 8)::INT,
    FLOOR(3 + RANDOM() * 7)::INT,
    jsonb_build_array(
        jsonb_build_object('skill', '프로그래밍', 'level', 'intermediate', 'verified_at', CURRENT_DATE - 30),
        jsonb_build_object('skill', '커뮤니케이션', 'level', 'basic', 'verified_at', CURRENT_DATE - 60),
        jsonb_build_object('skill', '문제해결', 'level', 'advanced', 'verified_at', CURRENT_DATE - 15)
    ),
    jsonb_build_object(
        'summary', jsonb_build_object('strengths', ARRAY['문제해결', '협업'], 'areas_to_improve', ARRAY['영어', '발표']),
        'certifications', jsonb_build_array('TOEIC 750', '정보처리기사(준비중)'),
        'experiences', jsonb_build_array('교내 프로젝트 2건', '동아리 활동')
    ),
    CURRENT_TIMESTAMP,
    RANDOM() < 0.3,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_skill_passport sp WHERE sp.student_id = s.student_id);

-- ============================================
-- 5. 결과 확인
-- ============================================
DO $$
DECLARE
    v_skill_gap INT;
    v_coaching_plan INT;
    v_simulation INT;
    v_passport INT;
BEGIN
    SELECT COUNT(*) INTO v_skill_gap FROM tb_skill_gap_analysis sg JOIN tb_student s ON sg.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_coaching_plan FROM tb_coaching_plan cp JOIN tb_coaching_goal cg ON cp.goal_id = cg.goal_id JOIN tb_student s ON cg.std_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_simulation FROM tb_simulation_scenario ss JOIN tb_student s ON ss.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_passport FROM tb_skill_passport sp JOIN tb_student s ON sp.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);

    RAISE NOTICE '======================================';
    RAISE NOTICE '남은 메뉴 데이터 생성 결과 (2023-2025)';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE '스킬 갭 분석: % 건', v_skill_gap;
    RAISE NOTICE '코칭 계획: % 건', v_coaching_plan;
    RAISE NOTICE '시뮬레이션: % 건', v_simulation;
    RAISE NOTICE '스킬 패스포트: % 건', v_passport;
    RAISE NOTICE '======================================';
END $$;
