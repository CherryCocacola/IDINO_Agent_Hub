-- ============================================
-- 14. 전체 메뉴 데이터 시드 스크립트
-- ============================================
-- 대상 메뉴: 스킬관리, AI 코칭, 위험 알림, 기회탐색, 스프린트,
--           WHAT-IF 시뮬레이션, 스킬 패스포트, 포트폴리오, 로드맵 플래너
-- 대상 학생: admission_year 2023, 2024, 2025
-- 목표: 각 학과별 최소 2건 이상 데이터 생성
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. 스킬 갭 분석 데이터 (스킬관리 메뉴)
-- ============================================
INSERT INTO tb_skill_gap_analysis (analysis_id, student_id, target_role_cd, analysis_date, overall_gap_score, gap_details, top_priority_skills, recommended_actions, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    CASE
        WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' OR d.department_nm LIKE '%AI%' OR d.department_nm LIKE '%정보%' THEN 'ROLE_BE'
        WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%' THEN 'ROLE_DA'
        WHEN d.department_nm LIKE '%디자인%' THEN 'ROLE_FE'
        WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%' THEN 'ROLE_HW'
        ELSE 'ROLE_PM'
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
-- 2. 코칭 계획 데이터 (AI 코칭 메뉴)
-- ============================================
INSERT INTO tb_coaching_plan (plan_id, goal_id, title, description, start_date, end_date, status, priority, ins_user_id, ins_dt)
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
    CURRENT_DATE,
    CURRENT_DATE + INTERVAL '3 months',
    CASE WHEN RANDOM() < 0.3 THEN 'completed' WHEN RANDOM() < 0.7 THEN 'in_progress' ELSE 'pending' END,
    CASE WHEN RANDOM() < 0.3 THEN 1 WHEN RANDOM() < 0.7 THEN 2 ELSE 3 END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal cg
JOIN tb_student s ON cg.std_id = s.student_id
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_coaching_plan cp WHERE cp.goal_id = cg.goal_id)
LIMIT 10000;

-- ============================================
-- 3. 기회 추천 데이터 (기회탐색 메뉴)
-- ============================================
INSERT INTO tb_opportunity_recommendation (recommendation_id, student_id, opportunity_id, match_score, match_reasons, status, recommended_at, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    o.opportunity_id,
    ROUND((60 + RANDOM() * 35)::NUMERIC, 1),
    jsonb_build_array(
        jsonb_build_object('reason', '전공 관련성 높음', 'weight', 0.3),
        jsonb_build_object('reason', '경력 목표와 일치', 'weight', 0.3),
        jsonb_build_object('reason', '지원 자격 충족', 'weight', 0.2),
        jsonb_build_object('reason', '학년 적합성', 'weight', 0.2)
    ),
    CASE WHEN RANDOM() < 0.1 THEN 'applied' WHEN RANDOM() < 0.3 THEN 'viewed' ELSE 'new' END,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 14)::INT,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (SELECT opportunity_id FROM tb_opportunity ORDER BY RANDOM() LIMIT 5) o
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_opportunity_recommendation r
    WHERE r.student_id = s.student_id AND r.opportunity_id = o.opportunity_id
);

-- ============================================
-- 4. 포트폴리오 데이터 (포트폴리오 메뉴)
-- ============================================
-- 먼저 기존 데이터 확인 후 각 학과별 2건 이상 생성
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, is_featured, display_order, artifact_type, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    item_types.item_type,
    item_types.title || ' - ' || s.student_nm,
    item_types.description,
    CURRENT_DATE - INTERVAL '1 month' * (1 + (RANDOM() * 6)::INT),
    CASE WHEN RANDOM() < 0.7 THEN CURRENT_DATE - INTERVAL '1 day' * (RANDOM() * 30)::INT ELSE NULL END,
    jsonb_build_array(item_types.skill1, item_types.skill2, item_types.skill3),
    CASE WHEN RANDOM() < 0.3 THEN 'Y' ELSE 'N' END,
    (ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY RANDOM()))::INT,
    item_types.artifact_type,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
    ('project', '웹 애플리케이션 개발 프로젝트', 'React와 Node.js를 활용한 풀스택 웹 애플리케이션 개발', 'JavaScript', 'React', 'Node.js', 'project'),
    ('project', '데이터 분석 프로젝트', 'Python과 Pandas를 활용한 데이터 분석 및 시각화', 'Python', 'Pandas', 'Matplotlib', 'project'),
    ('certification', '정보처리기사 자격증', '국가공인 정보처리기사 자격증 취득', '프로그래밍', '데이터베이스', 'SW설계', 'certification'),
    ('award', '교내 해커톤 수상', '24시간 해커톤에서 팀 프로젝트로 우수상 수상', '협업', '문제해결', '프레젠테이션', 'award'),
    ('experience', '스타트업 인턴십 경험', 'IT 스타트업에서 백엔드 개발 인턴으로 근무', 'Git', 'Docker', 'AWS', 'experience')
) AS item_types(item_type, title, description, skill1, skill2, skill3, artifact_type)
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_portfolio p
    WHERE p.student_id = s.student_id AND p.item_type = item_types.item_type
)
AND RANDOM() < 0.4;

-- ============================================
-- 5. 로드맵 데이터 (로드맵 플래너 메뉴)
-- ============================================
-- 로드맵 기본 데이터 생성
INSERT INTO tb_roadmap (roadmap_id, student_id, title, description, target_role, target_company, target_year, status, progress_percent, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    CASE
        WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' OR d.department_nm LIKE '%AI%' THEN '소프트웨어 개발자 로드맵'
        WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%' THEN '경영/컨설팅 전문가 로드맵'
        WHEN d.department_nm LIKE '%간호%' OR d.department_nm LIKE '%의%' OR d.department_nm LIKE '%치료%' THEN '의료/헬스케어 전문가 로드맵'
        WHEN d.department_nm LIKE '%디자인%' THEN 'UX/UI 디자이너 로드맵'
        WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%' THEN '하드웨어 엔지니어 로드맵'
        ELSE '전문직 커리어 로드맵'
    END,
    CASE
        WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' OR d.department_nm LIKE '%AI%' THEN '프로그래밍 역량 강화 및 실무 프로젝트 경험을 통한 취업 준비'
        WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%' THEN '경영학 이론 학습 및 인턴십을 통한 실무 경험 축적'
        WHEN d.department_nm LIKE '%간호%' OR d.department_nm LIKE '%의%' OR d.department_nm LIKE '%치료%' THEN '임상 실습 및 전문 자격증 취득을 통한 전문성 확보'
        WHEN d.department_nm LIKE '%디자인%' THEN '디자인 포트폴리오 구축 및 UX 리서치 역량 강화'
        WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%' THEN '하드웨어 설계 및 반도체 공정 이해를 통한 취업 준비'
        ELSE '전공 역량 강화 및 관련 분야 경험 축적'
    END,
    CASE
        WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' OR d.department_nm LIKE '%AI%' THEN '백엔드 개발자'
        WHEN d.department_nm LIKE '%경영%' OR d.department_nm LIKE '%경제%' THEN '경영 컨설턴트'
        WHEN d.department_nm LIKE '%간호%' OR d.department_nm LIKE '%의%' OR d.department_nm LIKE '%치료%' THEN '의료 전문가'
        WHEN d.department_nm LIKE '%디자인%' THEN 'UX 디자이너'
        WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%' THEN '하드웨어 엔지니어'
        ELSE '전문직'
    END,
    CASE WHEN RANDOM() < 0.3 THEN '삼성전자' WHEN RANDOM() < 0.6 THEN 'LG전자' WHEN RANDOM() < 0.8 THEN '네이버' ELSE '카카오' END,
    2025 + s.current_grade,
    CASE WHEN RANDOM() < 0.3 THEN 'completed' WHEN RANDOM() < 0.7 THEN 'in_progress' ELSE 'draft' END,
    FLOOR(RANDOM() * 100)::INT,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd::VARCHAR = d.department_cd::VARCHAR
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_roadmap r WHERE r.student_id = s.student_id);

-- 로드맵 아이템 데이터 생성
INSERT INTO tb_roadmap_item (item_id, roadmap_id, category, title, description, target_grade, target_semester, status, priority, display_order, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    r.roadmap_id,
    items.category,
    items.title,
    items.description,
    items.target_grade,
    items.target_semester,
    CASE WHEN RANDOM() < 0.3 THEN 'completed' WHEN RANDOM() < 0.7 THEN 'in_progress' ELSE 'planned' END,
    items.priority,
    items.display_order,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_roadmap r
CROSS JOIN (
    VALUES
    ('학업', '전공 필수 과목 이수', '핵심 전공 과목 수강 및 우수한 성적 유지', 1, 1, 1, 1),
    ('자격증', '기초 자격증 취득', '토익 700점 이상 또는 OPIc IM 이상 취득', 1, 2, 2, 2),
    ('활동', '교내 동아리 활동', '전공 관련 동아리에 가입하여 활동', 2, 1, 2, 3),
    ('경험', '단기 인턴십 지원', '방학 기간 인턴십 프로그램 지원 및 참여', 2, 2, 1, 4),
    ('프로젝트', '개인 프로젝트 완료', '포트폴리오용 개인 프로젝트 1개 이상 완료', 3, 1, 1, 5),
    ('자격증', '전문 자격증 취득', '전공 관련 전문 자격증 취득', 3, 2, 1, 6),
    ('취업', '이력서/자소서 작성', '취업 지원을 위한 이력서 및 자기소개서 완성', 4, 1, 1, 7),
    ('취업', '기업 지원 시작', '목표 기업 채용 지원 시작', 4, 1, 1, 8)
) AS items(category, title, description, target_grade, target_semester, priority, display_order)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_roadmap_item ri
    WHERE ri.roadmap_id = r.roadmap_id AND ri.title = items.title
);

-- ============================================
-- 6. 추가 시뮬레이션 시나리오 (2023-2025 학생용)
-- ============================================
INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, description, parameters, result_data, status, created_at, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    scenarios.scenario_type,
    scenarios.title,
    scenarios.description,
    scenarios.parameters::JSONB,
    scenarios.result_data::JSONB,
    'completed',
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 30)::INT,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd::VARCHAR = d.department_cd::VARCHAR
CROSS JOIN (
    VALUES
    ('career_path', '대기업 취업 시나리오', '삼성전자 등 대기업 취업을 목표로 한 시나리오 분석',
     '{"target_company": "삼성전자", "target_role": "개발자", "timeline": "2년"}',
     '{"success_rate": 0.72, "required_skills": ["프로그래밍", "알고리즘", "영어"], "recommended_activities": ["인턴십", "공모전"]}'),
    ('skill_development', '프로그래밍 역량 강화', '6개월 내 프로그래밍 역량 중급 이상 달성 시나리오',
     '{"target_skill": "프로그래밍", "current_level": "초급", "target_level": "중급", "timeline": "6개월"}',
     '{"success_rate": 0.85, "learning_path": ["기초문법", "자료구조", "알고리즘", "프로젝트"], "estimated_hours": 300}'),
    ('opportunity', '해외 인턴십 기회', '해외 인턴십 지원 및 합격 시나리오',
     '{"target_country": "미국", "company_type": "IT기업", "duration": "3개월"}',
     '{"success_rate": 0.45, "requirements": ["TOEIC 900", "관련 경험", "포트폴리오"], "estimated_cost": 5000000}')
) AS scenarios(scenario_type, title, description, parameters, result_data)
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_simulation_scenario ss
    WHERE ss.student_id = s.student_id AND ss.title = scenarios.title
)
AND RANDOM() < 0.5;

-- ============================================
-- 7. 스킬 패스포트 업데이트 (누락된 학생)
-- ============================================
INSERT INTO tb_skill_passport (passport_id, student_id, verified_skills, total_points, level, issue_date, expiry_date, qr_code, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    jsonb_build_array(
        jsonb_build_object('skill', '프로그래밍', 'level', 'intermediate', 'verified_at', CURRENT_DATE - 30),
        jsonb_build_object('skill', '커뮤니케이션', 'level', 'basic', 'verified_at', CURRENT_DATE - 60),
        jsonb_build_object('skill', '문제해결', 'level', 'advanced', 'verified_at', CURRENT_DATE - 15)
    ),
    FLOOR(100 + RANDOM() * 400)::INT,
    CASE WHEN RANDOM() < 0.3 THEN 'gold' WHEN RANDOM() < 0.7 THEN 'silver' ELSE 'bronze' END,
    CURRENT_DATE - INTERVAL '1 month' * (RANDOM() * 12)::INT,
    CURRENT_DATE + INTERVAL '1 year',
    'QR_' || s.student_id || '_' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD'),
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_skill_passport sp WHERE sp.student_id = s.student_id);

-- ============================================
-- 8. 학생 뱃지 추가 (각 학생당 2개 이상)
-- ============================================
INSERT INTO tb_student_badge (student_badge_id, student_id, badge_id, earned_at, evidence, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    b.badge_id,
    CURRENT_TIMESTAMP - INTERVAL '1 day' * (RANDOM() * 90)::INT,
    jsonb_build_object(
        'type', 'auto_earned',
        'criteria_met', true,
        'verification_date', CURRENT_DATE
    ),
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (SELECT badge_id FROM tb_badge ORDER BY RANDOM() LIMIT 3) b
WHERE s.admission_year IN (2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_student_badge sb
    WHERE sb.student_id = s.student_id AND sb.badge_id = b.badge_id
);

-- ============================================
-- 9. 결과 확인
-- ============================================
DO $$
DECLARE
    v_skill_gap INT;
    v_coaching_plan INT;
    v_opp_rec INT;
    v_portfolio INT;
    v_roadmap INT;
    v_roadmap_item INT;
    v_simulation INT;
    v_passport INT;
    v_badge INT;
BEGIN
    SELECT COUNT(*) INTO v_skill_gap FROM tb_skill_gap_analysis sg JOIN tb_student s ON sg.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_coaching_plan FROM tb_coaching_plan;
    SELECT COUNT(*) INTO v_opp_rec FROM tb_opportunity_recommendation;
    SELECT COUNT(*) INTO v_portfolio FROM tb_portfolio p JOIN tb_student s ON p.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_roadmap FROM tb_roadmap r JOIN tb_student s ON r.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_roadmap_item FROM tb_roadmap_item;
    SELECT COUNT(*) INTO v_simulation FROM tb_simulation_scenario ss JOIN tb_student s ON ss.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_passport FROM tb_skill_passport sp JOIN tb_student s ON sp.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);
    SELECT COUNT(*) INTO v_badge FROM tb_student_badge sb JOIN tb_student s ON sb.student_id = s.student_id WHERE s.admission_year IN (2023, 2024, 2025);

    RAISE NOTICE '======================================';
    RAISE NOTICE '전체 메뉴 데이터 생성 결과 (2023-2025)';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE '스킬 갭 분석: % 건', v_skill_gap;
    RAISE NOTICE '코칭 계획: % 건', v_coaching_plan;
    RAISE NOTICE '기회 추천: % 건', v_opp_rec;
    RAISE NOTICE '포트폴리오: % 건', v_portfolio;
    RAISE NOTICE '로드맵: % 건', v_roadmap;
    RAISE NOTICE '로드맵 아이템: % 건', v_roadmap_item;
    RAISE NOTICE '시뮬레이션: % 건', v_simulation;
    RAISE NOTICE '스킬 패스포트: % 건', v_passport;
    RAISE NOTICE '학생 뱃지: % 건', v_badge;
    RAISE NOTICE '======================================';
END $$;
