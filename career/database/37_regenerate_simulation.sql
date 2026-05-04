-- ============================================
-- IDINO Career - Simulation Scenario Data Integrity Fix
-- File: 37_regenerate_simulation.sql
-- Date: 2026-01-29
-- Purpose:
--   1. Verify existing simulation scenario data
--   2. Clean orphaned records referencing non-existent students
--   3. Update course_selection scenarios with real course codes
--   4. Add new diverse scenarios for students without any scenarios
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- STEP 1: Verify existing data distribution
-- ============================================
DO $$
DECLARE
    v_total_scenarios BIGINT;
    v_total_comparisons BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_total_scenarios FROM tb_simulation_scenario;
    SELECT COUNT(*) INTO v_total_comparisons FROM tb_scenario_comparison;
    RAISE NOTICE '[VERIFY] tb_simulation_scenario total records: %', v_total_scenarios;
    RAISE NOTICE '[VERIFY] tb_scenario_comparison total records: %', v_total_comparisons;
END $$;

-- Show scenario_type distribution
DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE '[VERIFY] Scenario type distribution:';
    FOR rec IN
        SELECT scenario_type, COUNT(*) AS cnt
        FROM tb_simulation_scenario
        GROUP BY scenario_type
        ORDER BY cnt DESC
    LOOP
        RAISE NOTICE '  % : %', rec.scenario_type, rec.cnt;
    END LOOP;
END $$;

-- Show ins_user_id distribution
DO $$
DECLARE
    rec RECORD;
BEGIN
    RAISE NOTICE '[VERIFY] ins_user_id distribution:';
    FOR rec IN
        SELECT ins_user_id, COUNT(*) AS cnt
        FROM tb_simulation_scenario
        GROUP BY ins_user_id
        ORDER BY cnt DESC
    LOOP
        RAISE NOTICE '  % : %', rec.ins_user_id, rec.cnt;
    END LOOP;
END $$;


-- ============================================
-- STEP 2: Clean orphaned scenario records
-- Remove scenarios referencing non-existent students
-- ============================================
DO $$
DECLARE
    v_orphan_scenarios BIGINT;
    v_orphan_comparisons BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_orphan_scenarios
    FROM tb_simulation_scenario
    WHERE student_id NOT IN (SELECT student_id FROM tb_student);

    SELECT COUNT(*) INTO v_orphan_comparisons
    FROM tb_scenario_comparison
    WHERE student_id NOT IN (SELECT student_id FROM tb_student);

    RAISE NOTICE '[CLEANUP] Orphaned scenarios to remove: %', v_orphan_scenarios;
    RAISE NOTICE '[CLEANUP] Orphaned comparisons to remove: %', v_orphan_comparisons;
END $$;

-- Delete orphaned scenario_comparison records first (may reference scenario_ids)
DELETE FROM tb_scenario_comparison
WHERE student_id NOT IN (SELECT student_id FROM tb_student);

-- Delete orphaned simulation_scenario records
DELETE FROM tb_simulation_scenario
WHERE student_id NOT IN (SELECT student_id FROM tb_student);


-- ============================================
-- STEP 3: Update course_selection scenarios with real course codes
-- Pick 10 random course_selection scenarios and update their
-- changes JSONB to include real course_cd values from tb_course
-- matching the student's department_cd
-- ============================================
DO $$
DECLARE
    rec RECORD;
    v_courses JSONB;
    v_dept_cd VARCHAR(20);
    v_updated INT := 0;
BEGIN
    FOR rec IN
        SELECT ss.scenario_id, ss.student_id, s.department_cd
        FROM tb_simulation_scenario ss
        JOIN tb_student s ON ss.student_id = s.student_id
        WHERE ss.scenario_type = 'course_selection'
        ORDER BY RANDOM()
        LIMIT 10
    LOOP
        v_dept_cd := rec.department_cd;

        -- Build a JSONB array of real courses from the student's department
        SELECT jsonb_build_object(
            'simulated_changes', jsonb_agg(
                jsonb_build_object(
                    'type', 'add_course',
                    'course_cd', c.course_cd,
                    'course_nm', c.course_nm,
                    'credits', c.credits
                )
            )
        )
        INTO v_courses
        FROM (
            SELECT course_cd, course_nm, credits
            FROM tb_course
            WHERE department_cd = v_dept_cd
            ORDER BY RANDOM()
            LIMIT 3
        ) c;

        -- If no department-specific courses found, use general education courses
        IF v_courses IS NULL THEN
            SELECT jsonb_build_object(
                'simulated_changes', jsonb_agg(
                    jsonb_build_object(
                        'type', 'add_course',
                        'course_cd', c.course_cd,
                        'course_nm', c.course_nm,
                        'credits', c.credits
                    )
                )
            )
            INTO v_courses
            FROM (
                SELECT course_cd, course_nm, credits
                FROM tb_course
                WHERE department_cd IS NULL
                ORDER BY RANDOM()
                LIMIT 3
            ) c;
        END IF;

        IF v_courses IS NOT NULL THEN
            UPDATE tb_simulation_scenario
            SET changes = v_courses,
                upd_user_id = 'SCENARIO_FIX',
                upd_dt = CURRENT_TIMESTAMP
            WHERE scenario_id = rec.scenario_id;

            v_updated := v_updated + 1;
        END IF;
    END LOOP;

    RAISE NOTICE '[COURSE_FIX] Updated % course_selection scenarios with real course codes', v_updated;
END $$;


-- ============================================
-- STEP 4: Add ~50 new diverse scenarios for students
-- who currently have NO scenarios at all.
-- Covers all 5 scenario types with Korean text.
-- ins_user_id = 'SCENARIO_FIX'
-- ============================================

-- 4a. career_path scenarios (10 scenarios)
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level,
    ins_user_id, ins_dt
)
SELECT
    s.student_id,
    'career_path',
    titles.title,
    titles.description,
    jsonb_build_object(
        'variables', jsonb_build_array(
            jsonb_build_object('name', 'career_goal', 'current_value', COALESCE(s.career_goal, '미정'), 'simulated_value', titles.goal_value)
        )
    ),
    jsonb_build_object(
        'simulated_changes', jsonb_build_array(
            jsonb_build_object('name', 'career_goal', 'value', titles.goal_value)
        )
    ),
    jsonb_build_object(
        'results', jsonb_build_array(
            jsonb_build_object('metric_name', '직무 준비도', 'current_value', 35 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 20, 'simulated_value', 65 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'change_percent', 40 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 30, 'impact_level', 'positive', 'explanation', titles.result_explanation),
            jsonb_build_object('metric_name', '핵심 부족 역량', 'current_value', 4, 'simulated_value', 2, 'change_percent', -50.0, 'impact_level', 'positive', 'explanation', '집중 역량 개발로 부족 역량 감소 예상')
        ),
        'recommendation', titles.recommendation,
        'ai_analysis', jsonb_build_object(
            'summary', titles.ai_summary,
            'strengths', ARRAY['전공 기초 역량 보유', '학습 의지 높음', '관련 활동 경험 있음'],
            'risks', ARRAY['실무 경험 부족', '목표 설정 구체화 필요'],
            'recommendations', ARRAY['관련 자격증 취득 권장', '인턴십 경험 필수', '멘토링 프로그램 참여'],
            'next_steps', ARRAY['구체적 목표 기업 리서치', '필요 역량 리스트 작성'],
            'confidence_reason', '취업 시장 데이터 기반 분석'
        )
    ),
    0.60 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.02,
    'SCENARIO_FIX',
    CURRENT_TIMESTAMP
FROM (
    SELECT student_id, career_goal, department_cd
    FROM tb_student
    WHERE student_id NOT IN (SELECT DISTINCT student_id FROM tb_simulation_scenario)
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    SELECT *
    FROM (VALUES
        (1, '취업 목표 시나리오', '대기업 및 중견기업 취업을 목표로 한 역량 개발 시뮬레이션. 서류/면접 준비도를 분석합니다.', 'corporate_employment', '전공 역량과 직무 매칭도를 분석하여 부족한 역량을 도출합니다.', '대기업 취업을 위해 전공 역량 강화와 자격증 취득을 병행하세요.', '대기업 취업 시장은 경쟁이 치열하며 전공 역량과 인턴 경험이 핵심입니다.'),
        (2, '대학원 진학 시나리오', '석사/박사 대학원 진학을 위한 준비도 분석. GPA, 연구 경험, 영어 성적을 종합 평가합니다.', 'graduate_school', '대학원 입학에 필요한 학점, 연구 실적, 외국어 능력을 분석합니다.', '대학원 진학을 위해 GPA 관리와 연구 프로젝트 참여를 권장합니다.', '대학원 진학은 연구 역량과 학업 성취도가 핵심 평가 요소입니다.'),
        (3, '공무원 시험 준비 시나리오', '5급/7급/9급 공무원 시험 합격을 목표로 한 준비 전략 분석. 학습 계획과 예상 합격률을 제시합니다.', 'civil_service', '공무원 시험에 필요한 과목별 준비도를 분석합니다.', '공무원 시험은 장기 준비가 필요합니다. 체계적인 학습 계획을 수립하세요.', '공무원 시험 합격률과 준비 기간을 고려한 현실적인 분석입니다.'),
        (4, 'IT 기업 개발자 목표', 'IT 기업 소프트웨어 개발자 포지션을 목표로 한 기술 역량 준비도 분석입니다.', 'software_developer', '프로그래밍 역량, 프로젝트 경험, 코딩 테스트 준비도를 평가합니다.', 'IT 개발자 취업을 위해 알고리즘과 프로젝트 경험을 쌓으세요.', 'IT 개발자 시장은 실무 역량과 포트폴리오가 핵심 경쟁력입니다.'),
        (5, '스타트업 창업 시나리오', '졸업 후 스타트업 창업을 목표로 한 역량 준비도 분석. 사업 계획, 기술 역량, 네트워크를 종합 평가합니다.', 'startup_founder', '창업에 필요한 기술력, 비즈니스 감각, 팀 빌딩 역량을 분석합니다.', '창업을 위해 기술 역량과 비즈니스 모델 개발 경험을 쌓으세요.', '스타트업 창업은 기술력과 시장 이해, 팀 구성이 핵심 성공 요인입니다.'),
        (6, '금융권 취업 시나리오', '은행, 증권사, 보험사 등 금융권 취업을 목표로 한 역량 분석입니다.', 'finance_career', '금융권 취업에 필요한 전공, 자격증, 인턴 경험을 종합 분석합니다.', '금융권 취업을 위해 관련 자격증 취득과 인턴 경험을 쌓으세요.', '금융권은 전공 지식과 자격증, 인턴 경험을 중시합니다.'),
        (7, '해외 취업 시나리오', '해외 기업 취업을 목표로 한 글로벌 역량 준비도 분석. 어학, 해외 경험, 전문 기술을 평가합니다.', 'global_career', '해외 취업에 필요한 어학 능력, 글로벌 경험, 전문 역량을 분석합니다.', '해외 취업을 위해 영어 실력 향상과 해외 인턴 경험을 권장합니다.', '해외 취업은 어학 능력과 문화 적응력, 전문 기술이 핵심입니다.'),
        (8, '대기업 엔지니어 시나리오', '삼성, LG, SK 등 대기업 엔지니어 포지션을 목표로 한 준비도 분석입니다.', 'corporate_engineer', '대기업 엔지니어에 필요한 전공 역량, 프로젝트 경험을 분석합니다.', '대기업 엔지니어 취업을 위해 전공 심화와 프로젝트 경험을 강화하세요.', '대기업 엔지니어 채용은 전공 역량과 실무 프로젝트 경험이 핵심입니다.'),
        (9, '교직 이수 후 교사 목표', '교원 임용고시를 목표로 한 교직 이수 및 시험 준비 분석입니다.', 'teacher', '교직 이수 과목과 임용고시 준비도를 종합적으로 분석합니다.', '교사 목표를 위해 교직 과목 이수와 임용 준비를 병행하세요.', '교원 임용고시는 전공 지식과 교육학 역량이 모두 필요합니다.'),
        (10, '공기업 취업 시나리오', '한국전력, 코레일 등 공기업 취업을 목표로 한 NCS 기반 준비도 분석입니다.', 'public_enterprise', '공기업 NCS 채용에 필요한 직업기초능력과 전공 역량을 분석합니다.', '공기업 취업을 위해 NCS 학습과 전공 자격증 취득을 권장합니다.', '공기업은 NCS 기반 채용으로 직업기초능력과 직무수행능력이 핵심입니다.')
    ) AS t(rn, title, description, goal_value, result_explanation, recommendation, ai_summary)
    WHERE t.rn = (ROW_NUMBER() OVER (ORDER BY s.student_id))
) titles;


-- 4b. skill_development scenarios (10 scenarios)
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level,
    ins_user_id, ins_dt
)
SELECT
    s.student_id,
    'skill_development',
    titles.title,
    titles.description,
    jsonb_build_object(
        'variables', jsonb_build_array(
            jsonb_build_object('name', titles.skill_name, 'current_value', 1 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 3, 'simulated_value', 3 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 2)
        )
    ),
    jsonb_build_object(
        'simulated_changes', jsonb_build_array(
            jsonb_build_object('name', titles.skill_name, 'value', 3 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 2),
            jsonb_build_object('name', 'hours_per_week', 'value', 8 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 8)
        )
    ),
    jsonb_build_object(
        'results', jsonb_build_array(
            jsonb_build_object('metric_name', titles.metric_name, 'current_value', 30 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 20, 'simulated_value', 70 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'change_percent', 60 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 30, 'impact_level', 'positive', 'explanation', titles.result_explanation),
            jsonb_build_object('metric_name', '예상 소요 시간', 'current_value', 0, 'simulated_value', 80 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int * 10, 'change_percent', 100.0, 'impact_level', 'neutral', 'explanation', titles.time_explanation)
        ),
        'recommendation', titles.recommendation,
        'ai_analysis', jsonb_build_object(
            'summary', titles.ai_summary,
            'strengths', ARRAY['기초 학습 능력 보유', '자기주도 학습 가능'],
            'risks', ARRAY['학습 시간 확보 필요', '실습 환경 구축 필요'],
            'recommendations', ARRAY['온라인 강좌 활용', '프로젝트 기반 학습 권장', '스터디 그룹 참여'],
            'next_steps', ARRAY['학습 계획 수립', '관련 강좌 등록'],
            'confidence_reason', '역량 개발 효과 데이터 기반 분석'
        )
    ),
    0.70 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.015,
    'SCENARIO_FIX',
    CURRENT_TIMESTAMP
FROM (
    SELECT student_id, department_cd
    FROM tb_student
    WHERE student_id NOT IN (SELECT DISTINCT student_id FROM tb_simulation_scenario)
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    SELECT *
    FROM (VALUES
        (1, '코딩 역량 강화', 'Python, Java 등 프로그래밍 언어 역량을 집중적으로 개발하는 시뮬레이션입니다.', 'skill_programming', '프로그래밍 역량 점수', '프로그래밍 역량 레벨 향상으로 취업 경쟁력 강화', '주 10시간 학습 기준 약 12주 소요 예상', '코딩 역량은 IT 직무의 핵심입니다. 꾸준한 실습이 중요합니다.', '프로그래밍 역량은 모든 IT 직무에서 필수적인 핵심 역량입니다.'),
        (2, '영어 능력 향상', 'TOEIC, TOEFL, OPIc 등 영어 능력 향상을 위한 학습 계획 시뮬레이션입니다.', 'skill_english', '영어 점수', '목표 점수 달성으로 취업/유학 경쟁력 향상', '주 8시간 학습 기준 약 16주 소요 예상', '영어 능력은 글로벌 취업과 대학원 진학에 필수적입니다.', '영어 성적은 대부분의 채용 과정에서 기본 평가 요소입니다.'),
        (3, '데이터 분석 역량 개발', 'Python, SQL, 통계 기반 데이터 분석 역량을 체계적으로 개발합니다.', 'skill_data_analysis', '데이터 분석 역량', 'SQL과 Python 데이터 분석 역량 종합 향상', '주 12시간 학습 기준 약 14주 소요 예상', '데이터 분석 역량은 다양한 직무에서 활용 가치가 높습니다.', '데이터 기반 의사결정이 중요해지면서 데이터 분석 역량 수요가 급증하고 있습니다.'),
        (4, '프로젝트 관리 역량 개발', 'PMP, Agile 등 프로젝트 관리 방법론 학습 시뮬레이션입니다.', 'skill_project_mgmt', '프로젝트 관리 역량', '체계적인 프로젝트 수행 능력 향상 예상', '주 6시간 학습 기준 약 10주 소요 예상', '프로젝트 관리 역량은 리더십과 실행력의 기초입니다.', 'Agile/Scrum 기반 프로젝트 관리는 IT 업계의 표준이 되었습니다.'),
        (5, '발표 및 커뮤니케이션 역량', '프레젠테이션 스킬과 비즈니스 커뮤니케이션 역량 개발 시뮬레이션입니다.', 'skill_communication', '커뮤니케이션 역량', '발표력과 비즈니스 소통 능력 향상', '주 4시간 실습 기준 약 8주 소요 예상', '커뮤니케이션 역량은 모든 직무에서 높은 가치를 가집니다.', '효과적인 커뮤니케이션은 팀워크와 성과 달성의 핵심 역량입니다.'),
        (6, '클라우드 기술 역량 강화', 'AWS, Azure 등 클라우드 서비스 활용 역량을 개발하는 시뮬레이션입니다.', 'skill_cloud', '클라우드 역량 점수', '클라우드 기술 역량 향상으로 IT 취업 경쟁력 강화', '주 10시간 학습 기준 약 14주 소요 예상', '클라우드 기술은 현대 IT 인프라의 핵심입니다.', '클라우드 컴퓨팅 시장 성장에 따라 관련 역량 수요가 지속 증가하고 있습니다.'),
        (7, 'UI/UX 디자인 역량 개발', 'Figma, Adobe XD를 활용한 UI/UX 디자인 역량 개발 시뮬레이션입니다.', 'skill_uiux', 'UI/UX 디자인 역량', '사용자 중심 디자인 사고력과 도구 활용 능력 향상', '주 8시간 실습 기준 약 12주 소요 예상', 'UI/UX 역량은 제품 개발에서 점점 더 중요해지고 있습니다.', 'UI/UX 디자인은 사용자 경험 중심의 제품 개발에 필수적인 역량입니다.'),
        (8, '머신러닝 기초 역량 구축', 'Python 기반 머신러닝/딥러닝 기초 역량을 구축하는 시뮬레이션입니다.', 'skill_ml', '머신러닝 역량', 'ML 기초 알고리즘 이해와 구현 능력 향상', '주 12시간 학습 기준 약 16주 소요 예상', '머신러닝은 AI 시대의 핵심 기술 역량입니다.', 'AI/ML 역량은 다양한 산업 분야에서 혁신을 주도하는 핵심 기술입니다.'),
        (9, '한국사 능력 검정 준비', '한국사 능력 검정시험 1급 취득을 위한 학습 시뮬레이션입니다.', 'skill_korean_history', '한국사 역량 점수', '한국사 검정 시험 합격으로 공공기관 가산점 확보', '주 6시간 학습 기준 약 8주 소요 예상', '한국사 능력 검정은 공공기관 취업의 기본 자격입니다.', '한국사 능력 검정시험은 공무원, 공기업 지원 시 필수 자격입니다.'),
        (10, '엑셀/스프레드시트 고급 활용', 'Excel VBA, 피벗테이블 등 고급 엑셀 활용 역량 개발 시뮬레이션입니다.', 'skill_excel', '엑셀 활용 역량', '엑셀 고급 기능 활용으로 업무 효율성 향상', '주 5시간 실습 기준 약 6주 소요 예상', '엑셀 고급 역량은 사무직 취업의 기본 소양입니다.', '데이터 처리와 분석을 위한 엑셀 고급 활용 능력은 모든 사무 직군에서 필수입니다.')
    ) AS t(rn, title, description, skill_name, metric_name, result_explanation, time_explanation, recommendation, ai_summary)
    WHERE t.rn = (ROW_NUMBER() OVER (ORDER BY s.student_id))
) titles;


-- 4c. course_selection scenarios (10 scenarios)
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level,
    ins_user_id, ins_dt
)
SELECT
    sub.student_id,
    'course_selection',
    sub.title,
    sub.description,
    sub.base_state,
    sub.changes,
    sub.predicted_outcomes,
    sub.confidence_level,
    'SCENARIO_FIX',
    CURRENT_TIMESTAMP
FROM (
    SELECT
        s.student_id,
        s.department_cd,
        s.current_grade,
        titles.title,
        titles.description,
        jsonb_build_object(
            'variables', jsonb_build_array(
                jsonb_build_object('name', 'current_grade', 'current_value', s.current_grade, 'simulated_value', s.current_grade),
                jsonb_build_object('name', 'course_plan', 'current_value', '미정', 'simulated_value', titles.plan_value)
            )
        ) AS base_state,
        -- Build changes with real course_cd from the student's department
        COALESCE(
            (
                SELECT jsonb_build_object(
                    'simulated_changes', jsonb_agg(
                        jsonb_build_object(
                            'type', 'add_course',
                            'course_cd', c.course_cd,
                            'course_nm', c.course_nm,
                            'credits', c.credits
                        )
                    )
                )
                FROM (
                    SELECT course_cd, course_nm, credits
                    FROM tb_course
                    WHERE department_cd = s.department_cd
                    ORDER BY RANDOM()
                    LIMIT 3
                ) c
            ),
            -- Fallback to general education courses
            (
                SELECT jsonb_build_object(
                    'simulated_changes', jsonb_agg(
                        jsonb_build_object(
                            'type', 'add_course',
                            'course_cd', c.course_cd,
                            'course_nm', c.course_nm,
                            'credits', c.credits
                        )
                    )
                )
                FROM (
                    SELECT course_cd, course_nm, credits
                    FROM tb_course
                    WHERE course_cd LIKE 'GE%'
                    ORDER BY RANDOM()
                    LIMIT 3
                ) c
            )
        ) AS changes,
        jsonb_build_object(
            'results', jsonb_build_array(
                jsonb_build_object('metric_name', '학점 예상 변화', 'current_value', 3.2 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.05, 'simulated_value', 3.5 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.04, 'change_percent', 5 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 10, 'impact_level', 'positive', 'explanation', titles.result_explanation),
                jsonb_build_object('metric_name', '역량 향상 예상', 'current_value', 50 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'simulated_value', 70 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'change_percent', 20 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'impact_level', 'positive', 'explanation', '선택 과목 이수를 통한 역량 향상 예상')
            ),
            'recommendation', titles.recommendation,
            'ai_analysis', jsonb_build_object(
                'summary', titles.ai_summary,
                'strengths', ARRAY['기초 과목 이수 완료', '학점 관리 양호'],
                'risks', ARRAY['학점 과부하 주의', '선수과목 확인 필요'],
                'recommendations', ARRAY['전공 심화 과목 우선 이수', '교양 과목으로 균형 유지', '학점 부담 적절히 조절'],
                'next_steps', ARRAY['수강 신청 일정 확인', '교수 상담 예약'],
                'confidence_reason', '졸업 요건 및 역량 매핑 데이터 기반 분석'
            )
        ) AS predicted_outcomes,
        0.72 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.02 AS confidence_level,
        ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM (
        SELECT student_id, department_cd, current_grade
        FROM tb_student
        WHERE student_id NOT IN (SELECT DISTINCT student_id FROM tb_simulation_scenario)
        ORDER BY RANDOM()
        LIMIT 10
    ) s
    CROSS JOIN LATERAL (
        SELECT *
        FROM (VALUES
            (1, '전공심화 과목 선택', '전공 심화 과목 수강을 통한 전문성 강화 시뮬레이션입니다. 졸업 요건과 역량 향상을 분석합니다.', 'major_depth', '전공 심화 과목 이수로 전문 역량 점수 향상 예상', '전공 심화 과목을 우선 수강하여 전문성을 높이세요.', '전공 심화 과목은 졸업 후 직무 역량의 기반이 됩니다.'),
            (2, '융합전공 도전', '타 학과 융합전공을 통한 복수 역량 확보 시뮬레이션입니다.', 'convergence_major', '융합전공 과목 이수로 다학제 역량 확보 예상', '융합전공을 통해 차별화된 역량을 갖추세요.', '융합전공은 학문간 경계를 넘는 창의적 역량을 키울 수 있습니다.'),
            (3, '교직 이수 시나리오', '교직 과목 이수를 통한 교원 자격증 취득 시뮬레이션입니다.', 'teaching_cert', '교직 과목 이수로 교원 자격 취득 가능성 분석', '교직 이수를 원한다면 조기에 신청하여 과목을 계획적으로 이수하세요.', '교직 이수는 추가 학점 부담이 있으나 교원 자격 취득이 가능합니다.'),
            (4, '부전공 이수 계획', '부전공 과목 이수를 통한 복수 전문성 확보 시뮬레이션입니다.', 'minor_degree', '부전공 이수로 취업 경쟁력 향상 예상', '부전공 이수는 취업 시 차별화 포인트가 됩니다.', '부전공은 주전공과 시너지를 내는 분야를 선택하는 것이 효과적입니다.'),
            (5, '졸업학점 최적화 계획', '남은 학기 동안의 최적 수강 계획 시뮬레이션입니다.', 'credit_optimization', '최적 과목 선택으로 졸업 요건 충족 및 역량 극대화', '졸업 요건을 꼼꼼히 확인하고 남은 학점을 효율적으로 채우세요.', '졸업 요건 충족과 역량 극대화를 동시에 달성하는 최적 수강 계획입니다.'),
            (6, '캡스톤 프로젝트 과목 선택', '졸업 캡스톤 프로젝트 관련 과목 선택 시뮬레이션입니다.', 'capstone_project', '캡스톤 프로젝트 관련 과목 이수로 실무 역량 강화', '캡스톤 프로젝트에 필요한 선수 과목을 미리 이수하세요.', '캡스톤 프로젝트는 종합적인 문제 해결 능력을 평가하는 핵심 과목입니다.'),
            (7, '계절학기 활용 계획', '방학 중 계절학기를 활용한 학점 이수 시뮬레이션입니다.', 'seasonal_semester', '계절학기 활용으로 정규 학기 부담 경감 예상', '계절학기를 활용하면 정규 학기에 여유가 생깁니다.', '계절학기는 핵심 과목 집중 학습에 효과적입니다.'),
            (8, '교양 과목 전략 선택', '교양 필수/선택 과목의 전략적 선택 시뮬레이션입니다.', 'liberal_arts_strategy', '교양 과목 전략 선택으로 종합 역량 균형 달성', '교양 과목도 전략적으로 선택하면 역량 개발에 도움됩니다.', '교양 과목은 전공 외 역량을 균형 있게 개발하는 기회입니다.'),
            (9, '실습/현장실습 과목 선택', '산업체 연계 실습 과목 선택 시뮬레이션입니다.', 'internship_course', '현장실습 과목 이수로 실무 경험 확보 예상', '현장실습 과목은 실무 경험을 쌓는 최고의 기회입니다.', '산업체 연계 실습은 이론과 실무를 연결하는 핵심 교육과정입니다.'),
            (10, '복수전공 수강 계획', '복수전공 과목 이수를 위한 수강 계획 시뮬레이션입니다.', 'double_major', '복수전공 이수로 취업 경쟁력 대폭 향상 예상', '복수전공은 계획적인 수강이 필수입니다. 학점 부담을 고려하세요.', '복수전공은 두 분야의 전문성을 갖출 수 있는 효과적인 전략입니다.')
        ) AS t(rn, title, description, plan_value, result_explanation, recommendation, ai_summary)
        WHERE t.rn = (ROW_NUMBER() OVER (ORDER BY s.student_id))
    ) titles
) sub
WHERE sub.changes IS NOT NULL;


-- 4d. opportunity scenarios (10 scenarios)
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level,
    ins_user_id, ins_dt
)
SELECT
    s.student_id,
    'opportunity',
    titles.title,
    titles.description,
    jsonb_build_object(
        'variables', jsonb_build_array(
            jsonb_build_object('name', 'opportunity_type', 'current_value', '없음', 'simulated_value', titles.opp_type),
            jsonb_build_object('name', 'duration_months', 'current_value', 0, 'simulated_value', titles.duration)
        )
    ),
    jsonb_build_object(
        'simulated_changes', jsonb_build_array(
            jsonb_build_object('name', 'opportunity_type', 'value', titles.opp_type),
            jsonb_build_object('name', 'duration_months', 'value', titles.duration)
        )
    ),
    jsonb_build_object(
        'results', jsonb_build_array(
            jsonb_build_object('metric_name', '경력 개발 효과', 'current_value', 20 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 20, 'simulated_value', 60 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 20, 'change_percent', 80 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 30, 'impact_level', 'positive', 'explanation', titles.result_explanation),
            jsonb_build_object('metric_name', '취업 경쟁력 변화', 'current_value', 50, 'simulated_value', 70 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 10, 'change_percent', 30 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'impact_level', 'positive', 'explanation', '관련 경험 확보를 통한 취업 경쟁력 향상')
        ),
        'recommendation', titles.recommendation,
        'ai_analysis', jsonb_build_object(
            'summary', titles.ai_summary,
            'strengths', ARRAY['새로운 경험 획득 가능', '네트워크 확대 기회', '실무 역량 향상'],
            'risks', ARRAY['학업과 병행 부담', '기회비용 존재', '선발 경쟁률 고려 필요'],
            'recommendations', ARRAY['지원 마감일 사전 확인', '포트폴리오 사전 준비', '선배 경험담 참고'],
            'next_steps', ARRAY['모집 공고 모니터링', '지원서 초안 작성'],
            'confidence_reason', '유사 프로그램 참여자 성과 데이터 분석'
        )
    ),
    0.65 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.02,
    'SCENARIO_FIX',
    CURRENT_TIMESTAMP
FROM (
    SELECT student_id, department_cd
    FROM tb_student
    WHERE student_id NOT IN (SELECT DISTINCT student_id FROM tb_simulation_scenario)
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    SELECT *
    FROM (VALUES
        (1, '인턴십 지원 시나리오', '국내 대기업 및 IT 기업 인턴십 프로그램 참여 효과를 분석합니다.', 'internship', 2, '인턴십 참여를 통한 실무 경험 확보 및 정규직 전환 가능성 분석', '인턴십은 취업의 가장 확실한 디딤돌입니다. 적극적으로 지원하세요.', '인턴십 경험자의 취업률은 미경험자 대비 약 30% 높습니다.'),
        (2, '공모전 참가 시나리오', '전공 관련 공모전 참가를 통한 포트폴리오 구축 효과를 분석합니다.', 'competition', 3, '공모전 참가를 통한 실전 경험 확보 및 수상 실적 구축', '공모전은 포트폴리오 구축과 팀워크 경험의 좋은 기회입니다.', '공모전 수상 경력은 서류 전형에서 높은 가산점을 받습니다.'),
        (3, '해외연수 시나리오', '해외 교환학생/연수 프로그램 참여 효과를 분석합니다.', 'overseas_program', 6, '해외 연수를 통한 글로벌 역량 및 어학 능력 향상 예상', '해외 연수는 글로벌 역량과 어학 능력을 동시에 키울 수 있습니다.', '해외 경험은 글로벌 기업 취업에서 중요한 차별화 요소입니다.'),
        (4, '학부연구생 참여 시나리오', '교수 연구실 학부연구생으로 참여하는 효과를 분석합니다.', 'research_assistant', 6, '연구 경험 확보로 대학원 진학 및 R&D 취업 경쟁력 향상', '학부연구생 경험은 대학원 진학과 연구직 취업에 큰 도움이 됩니다.', '학부연구생 경험은 연구 역량과 논문 작성 능력을 키울 수 있는 기회입니다.'),
        (5, '창업 동아리 참여 시나리오', '창업 관련 동아리 활동 및 창업경진대회 참여 효과를 분석합니다.', 'startup_club', 12, '창업 경험을 통한 기업가 정신 및 비즈니스 역량 개발', '창업 동아리는 비즈니스 마인드와 리더십을 키울 수 있는 기회입니다.', '창업 경험은 취업 면접에서도 높이 평가받는 차별화 요소입니다.'),
        (6, '봉사활동 참여 시나리오', '사회봉사 활동 참여를 통한 인성 역량 개발 효과를 분석합니다.', 'volunteer', 4, '봉사활동을 통한 사회적 역량 및 소통 능력 향상', '봉사활동은 인성 역량과 사회적 책임감을 키울 수 있습니다.', '봉사활동 경험은 공기업 및 사회적 기업 취업에서 중요한 요소입니다.'),
        (7, '산학협력 프로젝트 참여', '산업체와 연계한 실무 프로젝트 참여 효과를 분석합니다.', 'industry_project', 4, '산학협력을 통한 실무 프로젝트 수행 경험 확보', '산학협력 프로젝트는 실무와 학업을 연결하는 최적의 경험입니다.', '산학협력 프로젝트는 기업이 원하는 실무 역량을 직접 경험할 수 있는 기회입니다.'),
        (8, '멘토링 프로그램 참여', '선배/현직자 멘토링 프로그램 참여 효과를 분석합니다.', 'mentoring', 6, '멘토링을 통한 진로 방향 설정 및 네트워크 확대', '멘토링은 진로 방향 설정에 큰 도움이 됩니다. 적극적으로 참여하세요.', '멘토링 프로그램은 현직자의 경험과 조언을 통해 진로를 구체화하는 기회입니다.'),
        (9, '자격증 부트캠프 참여', '단기 집중 자격증 취득 부트캠프 참여 효과를 분석합니다.', 'bootcamp', 1, '단기 집중 학습으로 자격증 취득 가능성 향상', '부트캠프는 단기간에 집중적으로 역량을 키울 수 있는 효과적인 방법입니다.', '집중 부트캠프는 짧은 기간에 실무 역량을 빠르게 키울 수 있습니다.'),
        (10, '학술 세미나 발표 시나리오', '학술 세미나 또는 학회 발표 참여 효과를 분석합니다.', 'academic_seminar', 1, '학술 발표를 통한 전문성 입증 및 네트워크 구축', '학술 발표 경험은 전문성을 증명하고 학계 네트워크를 구축하는 기회입니다.', '학술 발표 경험은 대학원 진학과 연구직 취업에서 높이 평가됩니다.')
    ) AS t(rn, title, description, opp_type, duration, result_explanation, recommendation, ai_summary)
    WHERE t.rn = (ROW_NUMBER() OVER (ORDER BY s.student_id))
) titles;


-- 4e. timeline scenarios (10 scenarios)
INSERT INTO tb_simulation_scenario (
    student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes, confidence_level,
    ins_user_id, ins_dt
)
SELECT
    s.student_id,
    'timeline',
    titles.title,
    titles.description,
    jsonb_build_object(
        'variables', jsonb_build_array(
            jsonb_build_object('name', 'timeline_type', 'current_value', '미설정', 'simulated_value', titles.tl_type),
            jsonb_build_object('name', 'current_grade', 'current_value', s.current_grade, 'simulated_value', s.current_grade)
        )
    ),
    jsonb_build_object(
        'simulated_changes', jsonb_build_array(
            jsonb_build_object('name', 'timeline_type', 'value', titles.tl_type),
            jsonb_build_object('name', 'target_completion', 'value', titles.target_date)
        )
    ),
    jsonb_build_object(
        'results', jsonb_build_array(
            jsonb_build_object('metric_name', '목표 달성 예상률', 'current_value', 30 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 20, 'simulated_value', 70 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'change_percent', 60 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 25, 'impact_level', 'positive', 'explanation', titles.result_explanation),
            jsonb_build_object('metric_name', '로드맵 완성도', 'current_value', 20 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 15, 'simulated_value', 75 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 10, 'change_percent', 100 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::int % 50, 'impact_level', 'positive', 'explanation', '체계적인 로드맵 수립으로 목표 달성 가능성 대폭 향상')
        ),
        'recommendation', titles.recommendation,
        'ai_analysis', jsonb_build_object(
            'summary', titles.ai_summary,
            'strengths', ARRAY['체계적 계획 수립 가능', '단계별 목표 설정 명확'],
            'risks', ARRAY['일정 변동 가능성', '예상치 못한 변수 존재', '동기 부여 유지 필요'],
            'recommendations', ARRAY['월별 체크포인트 설정', '멘토와 정기 상담', '유연한 계획 조정 필요'],
            'next_steps', ARRAY['세부 일정표 작성', '첫 달 목표 설정 및 실행'],
            'confidence_reason', '유사 사례 졸업생 데이터 기반 분석'
        )
    ),
    0.62 + (ROW_NUMBER() OVER (ORDER BY s.student_id))::numeric * 0.02,
    'SCENARIO_FIX',
    CURRENT_TIMESTAMP
FROM (
    SELECT student_id, current_grade, department_cd
    FROM tb_student
    WHERE student_id NOT IN (SELECT DISTINCT student_id FROM tb_simulation_scenario)
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    SELECT *
    FROM (VALUES
        (1, '졸업까지 로드맵', '현재 학년부터 졸업까지의 종합 로드맵 시뮬레이션입니다. 학점, 역량, 활동을 종합적으로 계획합니다.', 'graduation_roadmap', '2027-02-28', '체계적인 졸업 로드맵 수립으로 목표 달성 가능성 향상', '졸업까지의 로드맵을 세우고 매 학기 점검하세요.', '졸업까지의 체계적인 계획은 성공적인 대학 생활의 핵심입니다.'),
        (2, '취업 준비 타임라인', '취업 준비를 위한 단계별 타임라인 시뮬레이션입니다. 자소서, 면접, 코딩테스트 준비 일정을 포함합니다.', 'job_preparation', '2026-12-31', '단계별 취업 준비로 목표 기업 합격 가능성 향상', '취업 준비는 최소 6개월 전부터 시작하세요.', '체계적인 취업 준비 타임라인은 합격률을 크게 높입니다.'),
        (3, '자격증 취득 로드맵', '목표 자격증 취득을 위한 단계별 학습 로드맵 시뮬레이션입니다.', 'certification_roadmap', '2026-06-30', '단계별 자격증 취득 계획으로 합격 가능성 향상', '자격증은 시험 일정에 맞춰 역산하여 학습 계획을 세우세요.', '자격증 취득 로드맵은 시험 일정과 학습 분량을 체계적으로 관리합니다.'),
        (4, '대학원 준비 타임라인', '대학원 입학을 위한 준비 타임라인 시뮬레이션입니다. GPA, 연구, 추천서 준비 일정을 포함합니다.', 'grad_school_prep', '2027-09-01', '체계적인 대학원 준비로 입학 가능성 향상', '대학원 준비는 1년 전부터 시작하는 것이 이상적입니다.', '대학원 진학을 위한 체계적 준비 타임라인으로 합격 가능성을 높입니다.'),
        (5, '어학 성적 달성 타임라인', 'TOEIC, IELTS 등 목표 어학 점수 달성을 위한 학습 타임라인입니다.', 'language_score', '2026-06-30', '단계별 학습으로 목표 어학 점수 달성 예상', '어학 공부는 매일 꾸준히 하는 것이 가장 효과적입니다.', '어학 점수 목표 달성을 위한 단계별 학습 계획을 제시합니다.'),
        (6, '포트폴리오 구축 타임라인', '취업용 포트폴리오 구축을 위한 프로젝트별 타임라인 시뮬레이션입니다.', 'portfolio_build', '2026-09-30', '포트폴리오 프로젝트 완성으로 취업 경쟁력 강화', '포트폴리오는 3-5개의 완성도 높은 프로젝트가 핵심입니다.', '취업용 포트폴리오는 직무에 맞는 프로젝트를 체계적으로 구축해야 합니다.'),
        (7, '1학년 학업 계획 타임라인', '1학년 동안의 학업 및 비교과 활동 타임라인 시뮬레이션입니다.', 'freshman_plan', '2027-02-28', '체계적인 1학년 생활로 탄탄한 기초 역량 구축', '1학년은 기초를 탄탄히 하는 것이 가장 중요합니다.', '대학 1학년은 전공 기초와 학습 습관을 확립하는 핵심 시기입니다.'),
        (8, '인턴 및 대외활동 타임라인', '학기 중과 방학 기간의 인턴/대외활동 참여 타임라인입니다.', 'extracurricular', '2026-12-31', '대외활동과 인턴십의 전략적 배치로 경험 극대화', '방학과 학기를 나누어 인턴과 대외활동을 전략적으로 배치하세요.', '인턴십과 대외활동의 전략적 타임라인은 취업 경쟁력을 극대화합니다.'),
        (9, '코딩테스트 준비 로드맵', '코딩테스트 합격을 위한 알고리즘 학습 단계별 로드맵입니다.', 'coding_test_prep', '2026-06-30', '단계별 알고리즘 학습으로 코딩테스트 합격률 향상', '코딩테스트는 매일 1-2문제씩 꾸준히 풀어야 합니다.', '코딩테스트 준비 로드맵은 기초부터 고급까지 단계별 학습을 안내합니다.'),
        (10, '학기별 역량 개발 타임라인', '각 학기별로 달성할 역량 목표를 설정한 종합 타임라인입니다.', 'semester_competency', '2027-02-28', '학기별 역량 목표 달성으로 종합 역량 수준 향상', '매 학기 초에 역량 목표를 설정하고 학기 말에 점검하세요.', '학기별 역량 개발 타임라인은 체계적인 성장을 위한 종합 로드맵입니다.')
    ) AS t(rn, title, description, tl_type, target_date, result_explanation, recommendation, ai_summary)
    WHERE t.rn = (ROW_NUMBER() OVER (ORDER BY s.student_id))
) titles;


-- ============================================
-- STEP 5: Final verification
-- ============================================
DO $$
DECLARE
    v_total BIGINT;
    v_new_count BIGINT;
    v_comp_total BIGINT;
    rec RECORD;
BEGIN
    SELECT COUNT(*) INTO v_total FROM tb_simulation_scenario;
    SELECT COUNT(*) INTO v_new_count FROM tb_simulation_scenario WHERE ins_user_id = 'SCENARIO_FIX';
    SELECT COUNT(*) INTO v_comp_total FROM tb_scenario_comparison;

    RAISE NOTICE '============================================';
    RAISE NOTICE '[FINAL] tb_simulation_scenario total: %', v_total;
    RAISE NOTICE '[FINAL] New records added (SCENARIO_FIX): %', v_new_count;
    RAISE NOTICE '[FINAL] tb_scenario_comparison total: %', v_comp_total;
    RAISE NOTICE '============================================';

    -- Verify no orphans remain
    RAISE NOTICE '[FINAL] Orphan check:';
    SELECT COUNT(*) INTO v_total
    FROM tb_simulation_scenario
    WHERE student_id NOT IN (SELECT student_id FROM tb_student);
    RAISE NOTICE '  Orphaned scenarios: %', v_total;

    SELECT COUNT(*) INTO v_total
    FROM tb_scenario_comparison
    WHERE student_id NOT IN (SELECT student_id FROM tb_student);
    RAISE NOTICE '  Orphaned comparisons: %', v_total;

    -- Show updated type distribution
    RAISE NOTICE '[FINAL] Updated scenario type distribution:';
    FOR rec IN
        SELECT scenario_type, COUNT(*) AS cnt
        FROM tb_simulation_scenario
        GROUP BY scenario_type
        ORDER BY cnt DESC
    LOOP
        RAISE NOTICE '  % : %', rec.scenario_type, rec.cnt;
    END LOOP;

    -- Show ins_user_id distribution including new records
    RAISE NOTICE '[FINAL] Updated ins_user_id distribution:';
    FOR rec IN
        SELECT ins_user_id, COUNT(*) AS cnt
        FROM tb_simulation_scenario
        GROUP BY ins_user_id
        ORDER BY cnt DESC
    LOOP
        RAISE NOTICE '  % : %', rec.ins_user_id, rec.cnt;
    END LOOP;

    -- Count students with scenarios
    SELECT COUNT(DISTINCT student_id) INTO v_total FROM tb_simulation_scenario;
    RAISE NOTICE '[FINAL] Students with scenarios: %', v_total;
END $$;
