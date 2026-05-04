-- =====================================================
-- IDINO Career - Sample Data for All Pages
-- Ensures at least 1 record displays on each page
-- Run after: 07_1_missing_tables.sql
-- =====================================================

SET search_path TO idino_career;

-- =====================================================
-- Test Student IDs (Grade 4 - 2020 admission)
-- 2020010000 - DEPT01, 장지후
-- 2020010020 - DEPT01, 안선우
-- 2020020025 - DEPT02, 손민서
-- 2020020045 - DEPT02, 박지원
-- 2020030050 - DEPT03, 한태민
-- 2020040075 - DEPT04, 조예나
-- 2020050000 - DEPT05, 서도현
-- =====================================================

-- =====================================================
-- 1. Student Skills (tb_student_skill) - 스킬관리 페이지
-- =====================================================
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, trend, ins_user_id)
VALUES
-- 2020010000 - CS 학생 (Python, Java, SQL, ML, Git 전문)
('2020010000', 'SK01', 4, 5, 8, 'up', 'SEED'),      -- Python
('2020010000', 'SK02', 3, 4, 5, 'up', 'SEED'),      -- Java
('2020010000', 'SK03', 4, 5, 6, 'stable', 'SEED'),  -- SQL
('2020010000', 'SK04', 3, 4, 3, 'up', 'SEED'),      -- Machine Learning
('2020010000', 'SK05', 4, 4, 7, 'stable', 'SEED'),  -- Git

-- 2020010020 - CS 학생 (JavaScript, React, Node 전문)
('2020010020', 'SK06', 4, 5, 6, 'up', 'SEED'),      -- JavaScript
('2020010020', 'SK07', 3, 5, 4, 'up', 'SEED'),      -- React
('2020010020', 'SK08', 3, 4, 3, 'stable', 'SEED'),  -- Node.js
('2020010020', 'SK03', 3, 4, 4, 'up', 'SEED'),      -- SQL

-- 2020020025 - CS 학생 (AI/ML 전문)
('2020020025', 'SK01', 3, 5, 5, 'up', 'SEED'),      -- Python
('2020020025', 'SK09', 4, 5, 6, 'up', 'SEED'),      -- TensorFlow
('2020020025', 'SK04', 4, 5, 5, 'up', 'SEED'),      -- Machine Learning
('2020020025', 'SK10', 3, 4, 3, 'up', 'SEED'),      -- Deep Learning

-- 2020020045 - SW Eng 학생 (Java, Spring, DevOps)
('2020020045', 'SK02', 4, 5, 7, 'up', 'SEED'),      -- Java
('2020020045', 'SK11', 3, 4, 4, 'up', 'SEED'),      -- Spring
('2020020045', 'SK12', 3, 4, 2, 'up', 'SEED'),      -- Docker
('2020020045', 'SK13', 2, 4, 1, 'up', 'SEED'),      -- AWS

-- 2020030050 - Electronics 학생 (C++, Embedded)
('2020030050', 'SK14', 4, 5, 6, 'stable', 'SEED'), -- C++
('2020030050', 'SK15', 3, 4, 4, 'up', 'SEED'),     -- Embedded Systems

-- 2020040075 - Business 학생 (데이터 분석)
('2020040075', 'SK03', 3, 4, 4, 'up', 'SEED'),     -- SQL
('2020040075', 'SK01', 2, 3, 2, 'up', 'SEED'),     -- Python

-- 2020050000 - Statistics 학생 (R, 통계)
('2020050000', 'SK01', 3, 4, 5, 'up', 'SEED'),     -- Python
('2020050000', 'SK04', 3, 4, 3, 'up', 'SEED')      -- Machine Learning
ON CONFLICT (student_id, skill_cd) DO UPDATE SET
    current_level = EXCLUDED.current_level,
    target_level = EXCLUDED.target_level,
    evidence_count = EXCLUDED.evidence_count,
    trend = EXCLUDED.trend;

-- =====================================================
-- 2. Activities (tb_activity) - 비교과활동 페이지
-- =====================================================
INSERT INTO tb_activity (student_id, program_cd, activity_type, title, description, start_date, end_date, hours, status, ins_user_id)
VALUES
-- 2020010000 활동
('2020010000', 'PROG001', 'seminar', '인공지능 세미나', 'AI/ML 최신 트렌드 세미나 참여', '2024-03-01', '2024-03-15', 20, 'completed', 'SEED'),
('2020010000', 'PROG002', 'contest', '해커톤 대회', '24시간 코딩 해커톤 참가', '2024-05-10', '2024-05-11', 24, 'completed', 'SEED'),
('2020010000', 'PROG003', 'contest', 'AI 경진대회', 'AI 모델 개발 경진대회 참가', '2024-06-01', '2024-06-30', 40, 'completed', 'SEED'),

-- 2020010020 활동
('2020010020', 'PROG004', 'club', '프로그래밍 동아리', '웹 개발 스터디 활동', '2024-03-01', '2024-12-31', 100, 'completed', 'SEED'),
('2020010020', 'PROG001', 'seminar', '프론트엔드 세미나', 'React 심화 세미나', '2024-04-15', '2024-04-20', 15, 'completed', 'SEED'),

-- 2020020025 활동
('2020020025', 'PROG001', 'seminar', '딥러닝 워크샵', 'TensorFlow 실전 워크샵', '2024-05-01', '2024-05-15', 30, 'completed', 'SEED'),
('2020020025', 'PROG005', 'volunteer', 'IT 교육 봉사', '지역 청소년 코딩 교육', '2024-07-01', '2024-08-31', 40, 'completed', 'SEED'),

-- 2020020045 활동
('2020020045', 'PROG002', 'contest', 'SW 개발 대회', '소프트웨어 개발 공모전', '2024-04-01', '2024-05-15', 50, 'completed', 'SEED'),

-- 2020030050 활동
('2020030050', 'PROG003', 'contest', '임베디드 경진대회', 'IoT 프로젝트 경진대회', '2024-06-01', '2024-07-15', 60, 'completed', 'SEED'),

-- 2020040075 활동
('2020040075', 'PROG001', 'seminar', '데이터분석 세미나', '비즈니스 데이터 분석 세미나', '2024-03-10', '2024-03-20', 15, 'completed', 'SEED'),

-- 2020050000 활동
('2020050000', 'PROG001', 'seminar', '통계분석 워크샵', 'R을 활용한 통계분석', '2024-04-01', '2024-04-15', 20, 'completed', 'SEED');

-- =====================================================
-- 3. Additional Achievements (tb_achievement) - 자격증 페이지
-- =====================================================
INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, ins_user_id)
VALUES
-- 2020010000 자격증/수상
('2020010000', 'certification', '정보처리기사', '한국산업인력공단', '2024-06-15', NULL, '기사', NULL, 'SEED'),
('2020010000', 'certification', 'SQLD', '한국데이터산업진흥원', '2024-03-20', '2027-03-20', '전문가', NULL, 'SEED'),
('2020010000', 'award', '해커톤 대상', 'SW중심대학', '2024-05-11', NULL, '대상', NULL, 'SEED'),

-- 2020010020 자격증/수상
('2020010020', 'certification', '리눅스마스터 2급', '한국정보통신진흥협회', '2024-04-10', NULL, '2급', NULL, 'SEED'),
('2020010020', 'certification', '웹디자인기능사', '한국산업인력공단', '2023-12-15', NULL, '기능사', NULL, 'SEED'),

-- 2020020025 자격증/수상
('2020020025', 'certification', 'TensorFlow Certificate', 'Google', '2024-07-01', '2027-07-01', 'Professional', NULL, 'SEED'),
('2020020025', 'award', 'AI 경진대회 최우수상', '정보통신산업진흥원', '2024-06-30', NULL, '최우수', NULL, 'SEED'),

-- 2020020045 자격증
('2020020045', 'certification', 'AWS Solutions Architect', 'Amazon', '2024-05-20', '2027-05-20', 'Associate', NULL, 'SEED'),

-- 2020030050 자격증
('2020030050', 'certification', '전자기기기능사', '한국산업인력공단', '2023-11-20', NULL, '기능사', NULL, 'SEED'),
('2020030050', 'certification', '임베디드SW기사', '한국산업인력공단', '2024-08-15', NULL, '기사', NULL, 'SEED'),

-- 2020040075 자격증
('2020040075', 'certification', 'ADsP', '한국데이터산업진흥원', '2024-04-01', '2027-04-01', '전문가', NULL, 'SEED'),

-- 2020050000 자격증
('2020050000', 'certification', '사회조사분석사 2급', '한국산업인력공단', '2024-03-10', NULL, '2급', NULL, 'SEED');

-- =====================================================
-- 4. Risk Alerts (tb_risk_alert) - 위험알림 페이지
-- =====================================================
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, status, ins_user_id)
VALUES
-- 2020010000 - 스킬 갭 알림
('2020010000', 'skill_gap', 'medium', 'Python 심화 학습 필요', 'AI 엔지니어 목표 대비 Python ML 라이브러리 숙련도 보강이 필요합니다.', 'active', 'SEED'),

-- 2020010020 - 학점 부족 알림
('2020010020', 'credits', 'high', '졸업 필수 학점 부족', '졸업까지 전공 필수 12학점이 부족합니다. 다음 학기 수강 계획을 확인하세요.', 'active', 'SEED'),

-- 2020020045 - 포트폴리오 알림
('2020020045', 'career', 'low', '포트폴리오 업데이트 권장', '최근 3개월간 포트폴리오 업데이트가 없습니다. 신규 프로젝트 추가를 권장합니다.', 'active', 'SEED'),

-- 2020030050 - GPA 알림
('2020030050', 'gpa', 'medium', '전공 GPA 하락 추세', '최근 2학기 전공 GPA가 하락하고 있습니다. 학습 전략 점검이 필요합니다.', 'active', 'SEED'),

-- 2020040075 - 졸업 요건 알림
('2020040075', 'graduation', 'high', '필수 과목 미이수', '졸업 필수 과목 중 "경영정보시스템"이 미이수 상태입니다.', 'active', 'SEED'),

-- 2020050000 - 인턴십 알림
('2020050000', 'career', 'medium', '인턴십 지원 권장', '4학년 1학기까지 인턴십 경험이 없습니다. 취업 경쟁력 향상을 위해 지원을 권장합니다.', 'active', 'SEED'),

-- 추가 알림들
('2020010000', 'career', 'low', '자격증 갱신 알림', 'SQLD 자격증이 2027년 3월에 만료됩니다.', 'active', 'SEED'),
('2020020025', 'skill_gap', 'low', 'MLOps 스킬 학습 권장', 'ML Engineer로의 취업을 위해 MLOps 관련 스킬 학습을 권장합니다.', 'active', 'SEED');

-- =====================================================
-- 5. Opportunity Applications (tb_opportunity_application) - 기회탐색 페이지
-- =====================================================
-- First, get some opportunity IDs
DO $$
DECLARE
    opp_id1 UUID;
    opp_id2 UUID;
    opp_id3 UUID;
    opp_id4 UUID;
    opp_id5 UUID;
BEGIN
    SELECT opportunity_id INTO opp_id1 FROM tb_opportunity WHERE status = 'open' LIMIT 1 OFFSET 0;
    SELECT opportunity_id INTO opp_id2 FROM tb_opportunity WHERE status = 'open' LIMIT 1 OFFSET 1;
    SELECT opportunity_id INTO opp_id3 FROM tb_opportunity WHERE status = 'open' LIMIT 1 OFFSET 2;
    SELECT opportunity_id INTO opp_id4 FROM tb_opportunity WHERE status = 'open' LIMIT 1 OFFSET 3;
    SELECT opportunity_id INTO opp_id5 FROM tb_opportunity WHERE status = 'open' LIMIT 1 OFFSET 4;

    -- Insert applications if opportunities exist
    IF opp_id1 IS NOT NULL THEN
        INSERT INTO tb_opportunity_application (student_id, opportunity_id, status, cover_letter, ins_user_id)
        VALUES
            ('2020010000', opp_id1, 'submitted', 'AI 분야에 관심이 많은 컴퓨터공학과 4학년입니다.', 'SEED'),
            ('2020010020', opp_id1, 'in_review', '프론트엔드 개발에 열정을 가지고 있습니다.', 'SEED');
    END IF;

    IF opp_id2 IS NOT NULL THEN
        INSERT INTO tb_opportunity_application (student_id, opportunity_id, status, cover_letter, ins_user_id)
        VALUES
            ('2020020025', opp_id2, 'accepted', 'ML 연구 경험을 바탕으로 기여하겠습니다.', 'SEED'),
            ('2020020045', opp_id2, 'submitted', '백엔드 개발 역량을 키우고 싶습니다.', 'SEED');
    END IF;

    IF opp_id3 IS NOT NULL THEN
        INSERT INTO tb_opportunity_application (student_id, opportunity_id, status, cover_letter, ins_user_id)
        VALUES
            ('2020030050', opp_id3, 'submitted', '임베디드 시스템 개발 경험이 있습니다.', 'SEED');
    END IF;

    IF opp_id4 IS NOT NULL THEN
        INSERT INTO tb_opportunity_application (student_id, opportunity_id, status, cover_letter, ins_user_id)
        VALUES
            ('2020040075', opp_id4, 'in_review', '데이터 분석 역량을 발휘하고 싶습니다.', 'SEED');
    END IF;

    IF opp_id5 IS NOT NULL THEN
        INSERT INTO tb_opportunity_application (student_id, opportunity_id, status, cover_letter, ins_user_id)
        VALUES
            ('2020050000', opp_id5, 'submitted', '통계 분석 전문성을 활용하겠습니다.', 'SEED');
    END IF;
END $$;

-- =====================================================
-- 6. Simulation Scenarios (tb_simulation_scenario) - What-if 시뮬레이션 페이지
-- =====================================================
INSERT INTO tb_simulation_scenario (student_id, scenario_type, title, base_state, changes, predicted_outcomes, ins_user_id)
VALUES
('2020010000', 'course_selection', '다음 학기 수강 계획',
    '{"current_credits": 108, "current_gpa": 3.8, "skills": ["Python", "ML"]}'::jsonb,
    '{"add_courses": ["딥러닝실습", "빅데이터분석"], "credits": 6}'::jsonb,
    '{"predicted_gpa": 3.75, "skill_improvement": {"DL": "+1", "BigData": "+1"}, "graduation_readiness": 95}'::jsonb,
    'SEED'),

('2020010000', 'career_path', '백엔드 개발자 경로',
    '{"target_role": "Backend Developer", "current_skills": ["Python", "SQL"]}'::jsonb,
    '{"learn_skills": ["Spring", "Docker", "AWS"], "get_certifications": ["AWS SAA"]}'::jsonb,
    '{"job_match_score": 85, "skill_gap_reduced": 60, "estimated_months": 6}'::jsonb,
    'SEED'),

('2020010020', 'skill_development', '풀스택 개발자 플랜',
    '{"current_level": {"React": 3, "Node": 3}}'::jsonb,
    '{"improve_skills": ["React", "Node", "TypeScript"], "projects": 2}'::jsonb,
    '{"target_level": {"React": 5, "Node": 4, "TypeScript": 3}, "portfolio_items": 2}'::jsonb,
    'SEED'),

('2020020025', 'career_path', 'AI 연구원 경로',
    '{"target_role": "AI Researcher", "current_skills": ["TensorFlow", "ML"]}'::jsonb,
    '{"publish_papers": 1, "learn_skills": ["PyTorch", "NLP"], "get_degree": "Masters"}'::jsonb,
    '{"research_readiness": 80, "job_match_score": 90}'::jsonb,
    'SEED'),

('2020020045', 'course_selection', 'DevOps 역량 강화',
    '{"current_skills": ["Java", "Spring"]}'::jsonb,
    '{"add_courses": ["클라우드컴퓨팅", "컨테이너기술"], "learn_skills": ["K8s", "CI/CD"]}'::jsonb,
    '{"devops_readiness": 75, "job_prospects": "improved"}'::jsonb,
    'SEED');

-- =====================================================
-- 7. Skill Passports (tb_skill_passport) - 스킬패스포트 페이지
-- Update existing or insert new
-- =====================================================
INSERT INTO tb_skill_passport (student_id, overall_score, total_badges, total_skills, verified_skills, is_public, ins_user_id)
VALUES
('2020010000', 85.5, 5, 5, 4, TRUE, 'SEED'),
('2020010020', 78.2, 3, 4, 3, TRUE, 'SEED'),
('2020020025', 82.0, 4, 4, 3, TRUE, 'SEED'),
('2020020045', 75.5, 3, 4, 2, FALSE, 'SEED'),
('2020030050', 70.0, 2, 2, 2, FALSE, 'SEED'),
('2020040075', 65.0, 2, 2, 1, FALSE, 'SEED'),
('2020050000', 68.5, 2, 2, 1, TRUE, 'SEED')
ON CONFLICT (student_id) DO UPDATE SET
    overall_score = EXCLUDED.overall_score,
    total_badges = EXCLUDED.total_badges,
    total_skills = EXCLUDED.total_skills,
    verified_skills = EXCLUDED.verified_skills,
    is_public = EXCLUDED.is_public;

-- =====================================================
-- 8. Student Badges (tb_student_badge) - 배지 할당
-- =====================================================
DO $$
DECLARE
    badge_id1 UUID;
    badge_id2 UUID;
    badge_id3 UUID;
    badge_id4 UUID;
    badge_id5 UUID;
BEGIN
    SELECT badge_id INTO badge_id1 FROM tb_badge LIMIT 1 OFFSET 0;
    SELECT badge_id INTO badge_id2 FROM tb_badge LIMIT 1 OFFSET 1;
    SELECT badge_id INTO badge_id3 FROM tb_badge LIMIT 1 OFFSET 2;
    SELECT badge_id INTO badge_id4 FROM tb_badge LIMIT 1 OFFSET 3;
    SELECT badge_id INTO badge_id5 FROM tb_badge LIMIT 1 OFFSET 4;

    IF badge_id1 IS NOT NULL THEN
        INSERT INTO tb_student_badge (student_id, badge_id, earned_at, evidence, ins_user_id)
        VALUES
            ('2020010000', badge_id1, '2024-06-01', '{"reason": "Python 마스터 달성"}'::jsonb, 'SEED'),
            ('2020010020', badge_id1, '2024-07-01', '{"reason": "JavaScript 마스터 달성"}'::jsonb, 'SEED'),
            ('2020020025', badge_id1, '2024-05-01', '{"reason": "ML 마스터 달성"}'::jsonb, 'SEED')
        ON CONFLICT DO NOTHING;
    END IF;

    IF badge_id2 IS NOT NULL THEN
        INSERT INTO tb_student_badge (student_id, badge_id, earned_at, evidence, ins_user_id)
        VALUES
            ('2020010000', badge_id2, '2024-05-11', '{"reason": "해커톤 우승"}'::jsonb, 'SEED'),
            ('2020020025', badge_id2, '2024-06-30', '{"reason": "AI 대회 입상"}'::jsonb, 'SEED')
        ON CONFLICT DO NOTHING;
    END IF;

    IF badge_id3 IS NOT NULL THEN
        INSERT INTO tb_student_badge (student_id, badge_id, earned_at, evidence, ins_user_id)
        VALUES
            ('2020010000', badge_id3, '2024-06-15', '{"reason": "정보처리기사 취득"}'::jsonb, 'SEED'),
            ('2020020045', badge_id3, '2024-05-20', '{"reason": "AWS 자격증 취득"}'::jsonb, 'SEED'),
            ('2020030050', badge_id3, '2024-08-15', '{"reason": "임베디드SW기사 취득"}'::jsonb, 'SEED')
        ON CONFLICT DO NOTHING;
    END IF;

    IF badge_id4 IS NOT NULL THEN
        INSERT INTO tb_student_badge (student_id, badge_id, earned_at, evidence, ins_user_id)
        VALUES
            ('2020010000', badge_id4, '2024-03-01', '{"reason": "세미나 10회 참석"}'::jsonb, 'SEED'),
            ('2020010020', badge_id4, '2024-12-31', '{"reason": "동아리 활동 100시간"}'::jsonb, 'SEED')
        ON CONFLICT DO NOTHING;
    END IF;

    IF badge_id5 IS NOT NULL THEN
        INSERT INTO tb_student_badge (student_id, badge_id, earned_at, evidence, ins_user_id)
        VALUES
            ('2020010000', badge_id5, '2024-08-01', '{"reason": "GPA 3.8 이상"}'::jsonb, 'SEED'),
            ('2020020025', badge_id5, '2024-08-01', '{"reason": "GPA 3.9 이상"}'::jsonb, 'SEED'),
            ('2020040075', badge_id5, '2024-08-01', '{"reason": "GPA 3.7 이상"}'::jsonb, 'SEED')
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

-- =====================================================
-- 9. Portfolio Items (tb_portfolio) - 포트폴리오 페이지
-- =====================================================
INSERT INTO tb_portfolio (student_id, item_type, title, description, start_date, end_date, skills_used, is_featured, display_order, ins_user_id)
VALUES
-- 2020010000 포트폴리오
('2020010000', 'project', 'AI 챗봇 시스템', '자연어 처리 기반 챗봇 개발 프로젝트', '2024-03-01', '2024-06-30', '["Python", "TensorFlow", "NLP"]'::jsonb, 'Y', 1, 'SEED'),
('2020010000', 'project', '데이터 분석 대시보드', 'Python과 Streamlit을 활용한 실시간 대시보드', '2024-01-01', '2024-03-15', '["Python", "Streamlit", "SQL"]'::jsonb, 'N', 2, 'SEED'),
('2020010000', 'certificate', '정보처리기사', '한국산업인력공단 자격증', '2024-06-15', NULL, NULL, 'N', 3, 'SEED'),
('2020010000', 'award', '해커톤 대상', 'SW중심대학 해커톤 대상 수상', '2024-05-11', NULL, NULL, 'Y', 4, 'SEED'),

-- 2020010020 포트폴리오
('2020010020', 'project', '쇼핑몰 웹사이트', 'React와 Node.js를 활용한 이커머스 플랫폼', '2024-02-01', '2024-05-31', '["React", "Node.js", "MongoDB"]'::jsonb, 'Y', 1, 'SEED'),
('2020010020', 'project', '실시간 채팅 앱', 'WebSocket 기반 실시간 채팅 어플리케이션', '2024-06-01', '2024-08-15', '["React", "Socket.io", "Redis"]'::jsonb, 'N', 2, 'SEED'),
('2020010020', 'activity', '프로그래밍 동아리', '웹 개발 스터디 및 프로젝트 활동', '2024-03-01', '2024-12-31', NULL, 'N', 3, 'SEED'),

-- 2020020025 포트폴리오
('2020020025', 'project', '이미지 분류 모델', 'CNN 기반 이미지 분류 딥러닝 모델', '2024-04-01', '2024-07-31', '["Python", "TensorFlow", "Keras"]'::jsonb, 'Y', 1, 'SEED'),
('2020020025', 'project', '자연어 감성 분석', 'BERT 모델을 활용한 텍스트 감성 분석', '2024-08-01', '2024-10-31', '["Python", "PyTorch", "Transformers"]'::jsonb, 'Y', 2, 'SEED'),
('2020020025', 'certificate', 'TensorFlow Certificate', 'Google TensorFlow Developer 자격증', '2024-07-01', '2027-07-01', NULL, 'N', 3, 'SEED'),

-- 2020020045 포트폴리오
('2020020045', 'project', 'MSA 백엔드 시스템', 'Spring Boot 기반 마이크로서비스 아키텍처', '2024-03-01', '2024-08-31', '["Java", "Spring Boot", "Docker"]'::jsonb, 'Y', 1, 'SEED'),
('2020020045', 'certificate', 'AWS Solutions Architect', 'AWS 솔루션 아키텍트 어소시에이트', '2024-05-20', '2027-05-20', NULL, 'N', 2, 'SEED'),

-- 2020030050 포트폴리오
('2020030050', 'project', 'IoT 스마트홈 시스템', '아두이노 기반 IoT 홈 오토메이션', '2024-05-01', '2024-09-30', '["C++", "Arduino", "MQTT"]'::jsonb, 'Y', 1, 'SEED'),
('2020030050', 'certificate', '임베디드SW기사', '임베디드 소프트웨어 기사 자격증', '2024-08-15', NULL, NULL, 'N', 2, 'SEED');

-- =====================================================
-- 10. Roadmaps (tb_roadmap + tb_roadmap_item) - 로드맵플래너 페이지
-- =====================================================
-- Create roadmaps for test students
INSERT INTO tb_roadmap (student_id, title, description, target_role, target_company, target_year, progress_percent, ins_user_id)
VALUES
('2020010000', 'AI 엔지니어 커리어 로드맵', 'AI/ML 엔지니어가 되기 위한 단계별 계획', 'AI Engineer', 'NAVER/Kakao', 2025, 65, 'SEED'),
('2020010020', '풀스택 개발자 로드맵', '프론트엔드와 백엔드를 아우르는 풀스택 개발자 계획', 'Full-Stack Developer', 'Tech Startup', 2025, 50, 'SEED'),
('2020020025', 'ML 연구원 로드맵', '머신러닝 연구원 진로 계획', 'ML Researcher', 'Research Lab', 2026, 40, 'SEED'),
('2020020045', '백엔드 엔지니어 로드맵', 'Java 기반 백엔드 전문가 계획', 'Backend Engineer', 'Samsung SDS', 2025, 55, 'SEED'),
('2020030050', '임베디드 개발자 로드맵', '임베디드 시스템 개발자 진로 계획', 'Embedded Developer', 'LG Electronics', 2025, 45, 'SEED')
ON CONFLICT (student_id) DO UPDATE SET
    title = EXCLUDED.title,
    progress_percent = EXCLUDED.progress_percent;

-- Create roadmap items for 2020010000
DO $$
DECLARE
    roadmap_id_1 UUID;
BEGIN
    SELECT roadmap_id INTO roadmap_id_1 FROM tb_roadmap WHERE student_id = '2020010000';

    IF roadmap_id_1 IS NOT NULL THEN
        INSERT INTO tb_roadmap_item (roadmap_id, category, title, description, target_grade, target_semester, status, priority, display_order, ins_user_id)
        VALUES
        (roadmap_id_1, 'course', '딥러닝 기초', '딥러닝 기초 과목 수강', 3, 1, 'completed', 1, 1, 'SEED'),
        (roadmap_id_1, 'course', '기계학습', '머신러닝 심화 과목', 3, 2, 'completed', 1, 2, 'SEED'),
        (roadmap_id_1, 'certification', '정보처리기사', '국가기술자격증 취득', 4, 1, 'completed', 2, 3, 'SEED'),
        (roadmap_id_1, 'skill', 'TensorFlow 마스터', 'TensorFlow 프레임워크 숙련', 4, 1, 'in_progress', 1, 4, 'SEED'),
        (roadmap_id_1, 'activity', 'AI 해커톤 참가', 'AI 관련 해커톤 대회 참가', 4, 1, 'completed', 2, 5, 'SEED'),
        (roadmap_id_1, 'internship', 'AI 스타트업 인턴', 'AI 스타트업 인턴십 경험', 4, 2, 'planned', 1, 6, 'SEED'),
        (roadmap_id_1, 'course', '졸업 프로젝트', 'AI 응용 졸업 프로젝트', 4, 2, 'planned', 1, 7, 'SEED'),
        (roadmap_id_1, 'certification', 'TensorFlow Certificate', 'Google TensorFlow 자격증', 4, 2, 'planned', 2, 8, 'SEED');
    END IF;
END $$;

-- Create roadmap items for 2020010020
DO $$
DECLARE
    roadmap_id_2 UUID;
BEGIN
    SELECT roadmap_id INTO roadmap_id_2 FROM tb_roadmap WHERE student_id = '2020010020';

    IF roadmap_id_2 IS NOT NULL THEN
        INSERT INTO tb_roadmap_item (roadmap_id, category, title, description, target_grade, target_semester, status, priority, display_order, ins_user_id)
        VALUES
        (roadmap_id_2, 'course', '웹프로그래밍', '웹 개발 기초 과목', 2, 1, 'completed', 1, 1, 'SEED'),
        (roadmap_id_2, 'skill', 'React 심화', 'React 프레임워크 숙련', 3, 1, 'completed', 1, 2, 'SEED'),
        (roadmap_id_2, 'skill', 'Node.js 학습', 'Node.js 백엔드 개발', 3, 2, 'completed', 1, 3, 'SEED'),
        (roadmap_id_2, 'activity', '웹개발 동아리', '동아리 활동 및 프로젝트', 3, 1, 'in_progress', 2, 4, 'SEED'),
        (roadmap_id_2, 'course', '소프트웨어공학', 'SW 개발 방법론', 4, 1, 'in_progress', 1, 5, 'SEED'),
        (roadmap_id_2, 'internship', '스타트업 인턴', '테크 스타트업 인턴십', 4, 2, 'planned', 1, 6, 'SEED');
    END IF;
END $$;

-- Create roadmap items for other students
DO $$
DECLARE
    roadmap_id_3 UUID;
    roadmap_id_4 UUID;
    roadmap_id_5 UUID;
BEGIN
    SELECT roadmap_id INTO roadmap_id_3 FROM tb_roadmap WHERE student_id = '2020020025';
    SELECT roadmap_id INTO roadmap_id_4 FROM tb_roadmap WHERE student_id = '2020020045';
    SELECT roadmap_id INTO roadmap_id_5 FROM tb_roadmap WHERE student_id = '2020030050';

    -- 2020020025 items
    IF roadmap_id_3 IS NOT NULL THEN
        INSERT INTO tb_roadmap_item (roadmap_id, category, title, description, target_grade, target_semester, status, priority, display_order, ins_user_id)
        VALUES
        (roadmap_id_3, 'course', '인공지능개론', 'AI 기초 과목', 2, 2, 'completed', 1, 1, 'SEED'),
        (roadmap_id_3, 'skill', 'PyTorch 학습', 'PyTorch 프레임워크', 4, 1, 'in_progress', 1, 2, 'SEED'),
        (roadmap_id_3, 'activity', 'AI 연구실 참여', '연구실 학부연구생', 4, 1, 'in_progress', 1, 3, 'SEED');
    END IF;

    -- 2020020045 items
    IF roadmap_id_4 IS NOT NULL THEN
        INSERT INTO tb_roadmap_item (roadmap_id, category, title, description, target_grade, target_semester, status, priority, display_order, ins_user_id)
        VALUES
        (roadmap_id_4, 'course', 'Java 프로그래밍', 'Java 기초 및 심화', 2, 1, 'completed', 1, 1, 'SEED'),
        (roadmap_id_4, 'skill', 'Spring Boot', 'Spring 프레임워크', 3, 2, 'completed', 1, 2, 'SEED'),
        (roadmap_id_4, 'certification', 'AWS SAA', 'AWS 자격증', 4, 1, 'completed', 2, 3, 'SEED'),
        (roadmap_id_4, 'skill', 'Kubernetes', '컨테이너 오케스트레이션', 4, 2, 'planned', 1, 4, 'SEED');
    END IF;

    -- 2020030050 items
    IF roadmap_id_5 IS NOT NULL THEN
        INSERT INTO tb_roadmap_item (roadmap_id, category, title, description, target_grade, target_semester, status, priority, display_order, ins_user_id)
        VALUES
        (roadmap_id_5, 'course', '마이크로프로세서', '임베디드 시스템 기초', 2, 2, 'completed', 1, 1, 'SEED'),
        (roadmap_id_5, 'skill', 'ARM 프로세서', 'ARM 아키텍처 학습', 3, 1, 'completed', 1, 2, 'SEED'),
        (roadmap_id_5, 'certification', '임베디드SW기사', '국가기술자격증', 4, 1, 'completed', 2, 3, 'SEED');
    END IF;
END $$;

-- =====================================================
-- Verification Queries
-- =====================================================
SELECT '========== 데이터 생성 결과 ==========' as section;
SELECT 'tb_student_skill' as table_name, COUNT(*) as count FROM tb_student_skill;
SELECT 'tb_activity' as table_name, COUNT(*) as count FROM tb_activity;
SELECT 'tb_achievement' as table_name, COUNT(*) as count FROM tb_achievement;
SELECT 'tb_risk_alert' as table_name, COUNT(*) as count FROM tb_risk_alert;
SELECT 'tb_opportunity_application' as table_name, COUNT(*) as count FROM tb_opportunity_application;
SELECT 'tb_simulation_scenario' as table_name, COUNT(*) as count FROM tb_simulation_scenario;
SELECT 'tb_skill_passport' as table_name, COUNT(*) as count FROM tb_skill_passport;
SELECT 'tb_student_badge' as table_name, COUNT(*) as count FROM tb_student_badge;
SELECT 'tb_portfolio' as table_name, COUNT(*) as count FROM tb_portfolio;
SELECT 'tb_roadmap' as table_name, COUNT(*) as count FROM tb_roadmap;
SELECT 'tb_roadmap_item' as table_name, COUNT(*) as count FROM tb_roadmap_item;

SELECT '========== 테스트 학생별 데이터 현황 ==========' as section;
SELECT student_id,
       (SELECT COUNT(*) FROM tb_student_skill ss WHERE ss.student_id = s.student_id) as skills,
       (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = s.student_id) as activities,
       (SELECT COUNT(*) FROM tb_achievement ac WHERE ac.student_id = s.student_id) as achievements,
       (SELECT COUNT(*) FROM tb_risk_alert ra WHERE ra.student_id = s.student_id) as alerts,
       (SELECT COUNT(*) FROM tb_portfolio p WHERE p.student_id = s.student_id) as portfolio
FROM tb_student s
WHERE s.student_id IN ('2020010000', '2020010020', '2020020025', '2020020045', '2020030050', '2020040075', '2020050000')
ORDER BY s.student_id;
