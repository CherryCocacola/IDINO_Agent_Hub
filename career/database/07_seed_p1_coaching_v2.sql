-- ============================================
-- IDINO Career - P1 Phase 9: Coaching Seed Data (V2)
-- Updated to match new schema in 11_coaching_schema_fix.sql
-- Created: 2026-01-15
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. Clean existing data
-- ============================================

DELETE FROM tb_coaching_retrospective WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_coaching_checkin WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_coaching_plan WHERE ins_user_id = 'SEED_SCRIPT';
DELETE FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT';

-- ============================================
-- 2. Coaching Goals
-- ============================================

-- Career-focused goals for IT students
INSERT INTO tb_coaching_goal (
    std_id, title, description, goal_type, priority, target_date,
    target_role_cd, related_skills, success_criteria, motivation,
    status, progress_percentage, created_at, ins_user_id, ins_dt
)
SELECT
    s.student_id,
    '백엔드 개발자 취업 준비',
    'Python/Java 기반 백엔드 개발 역량을 갖춰 금융 기업 또는 IT 기업에 취업',
    'career',
    'high',
    CURRENT_DATE + INTERVAL '180 days',
    'ROLE001',
    ARRAY['Python', 'Java', 'SQL', 'Spring Boot'],
    '포트폴리오 프로젝트 3개 완성, 기술 면접 준비 완료',
    '좋은 회사에서 백엔드 개발자로 성장하고 싶습니다',
    CASE WHEN RANDOM() > 0.2 THEN 'active' ELSE 'completed' END,
    (RANDOM() * 70 + 20)::INT,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '180 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002')
LIMIT 20;

-- AI Engineer career goals
INSERT INTO tb_coaching_goal (
    std_id, title, description, goal_type, priority, target_date,
    target_role_cd, related_skills, success_criteria, motivation,
    status, progress_percentage, created_at, ins_user_id, ins_dt
)
SELECT
    s.student_id,
    'AI 엔지니어 역량 개발',
    'Machine Learning과 Deep Learning 역량을 개발하여 AI 분야 취업 또는 대학원 진학',
    'career',
    'high',
    CURRENT_DATE + INTERVAL '365 days',
    'ROLE005',
    ARRAY['Python', 'TensorFlow', 'PyTorch', 'MLOps'],
    'Kaggle 경진대회 Top 10% 달성, AI 관련 프로젝트 2개',
    'AI 기술로 세상에 기여하고 싶습니다',
    'active',
    (RANDOM() * 50 + 10)::INT,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '120 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT013')
AND s.student_id NOT IN (SELECT std_id FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT')
LIMIT 15;

-- Skill development goals
INSERT INTO tb_coaching_goal (
    std_id, title, description, goal_type, priority, target_date,
    related_skills, success_criteria, motivation,
    status, progress_percentage, created_at, ins_user_id, ins_dt
)
SELECT
    s.student_id,
    'Python 데이터 분석 역량 강화',
    'Pandas, NumPy, Matplotlib를 활용한 데이터 분석 능력 향상',
    'skill',
    'medium',
    CURRENT_DATE + INTERVAL '90 days',
    ARRAY['Python', 'Pandas', 'NumPy', 'Matplotlib', 'Seaborn'],
    '데이터 분석 프로젝트 3개 완성',
    '데이터 기반 의사결정 역량을 갖추고 싶습니다',
    'active',
    (RANDOM() * 40 + 10)::INT,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '60 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.department_cd IN ('DEPT001', 'DEPT002', 'DEPT006')
AND s.student_id NOT IN (SELECT std_id FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT')
LIMIT 20;

-- Academic goals
INSERT INTO tb_coaching_goal (
    std_id, title, description, goal_type, priority, target_date,
    success_criteria, motivation,
    status, progress_percentage, created_at, ins_user_id, ins_dt
)
SELECT
    s.student_id,
    '학점 향상 프로젝트',
    '이번 학기 GPA 3.5 이상 달성을 위한 체계적인 학습 계획 수립 및 실행',
    'academic',
    'high',
    CURRENT_DATE + INTERVAL '120 days',
    'GPA 3.5 이상, 전공 과목 A 이상',
    '좋은 학점으로 취업과 대학원 선택폭을 넓히고 싶습니다',
    'active',
    (RANDOM() * 55 + 25)::INT,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '45 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (1, 2)
AND s.student_id NOT IN (SELECT std_id FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT')
LIMIT 25;

-- Personal development goals
INSERT INTO tb_coaching_goal (
    std_id, title, description, goal_type, priority, target_date,
    success_criteria, motivation,
    status, progress_percentage, created_at, ins_user_id, ins_dt
)
SELECT
    s.student_id,
    '프레젠테이션 역량 강화',
    '발표 실력과 시각적으로 뛰어난 커뮤니케이션 역량 개발',
    'personal',
    'low',
    CURRENT_DATE + INTERVAL '60 days',
    '월 1회 스터디 발표, 피드백 점수 4점 이상',
    '자신감 있게 발표하고 싶습니다',
    'active',
    (RANDOM() * 50 + 30)::INT,
    CURRENT_TIMESTAMP - (RANDOM() * INTERVAL '30 days'),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.current_grade IN (2, 3)
AND s.student_id NOT IN (SELECT std_id FROM tb_coaching_goal WHERE ins_user_id = 'SEED_SCRIPT')
LIMIT 15;

-- ============================================
-- 3. Coaching Plan Items (Action Items)
-- ============================================

-- Plan items for Python data analysis goals
INSERT INTO tb_coaching_plan (
    goal_id, title, description, order_index, due_date,
    estimated_hours, related_skill_cd, is_completed, notes,
    created_at, ins_user_id, ins_dt
)
SELECT
    g.goal_id,
    unnest(ARRAY['Pandas 기초 학습', 'NumPy 배열 연산', 'Matplotlib 시각화', '실전 프로젝트']),
    unnest(ARRAY[
        'Pandas DataFrame 기본 조작법 익히기',
        'NumPy 배열 생성, 연산, 인덱싱 마스터',
        '다양한 차트 유형으로 데이터 시각화',
        '실제 데이터셋으로 분석 프로젝트 수행'
    ]),
    unnest(ARRAY[0, 1, 2, 3]),
    unnest(ARRAY[
        CURRENT_DATE + INTERVAL '14 days',
        CURRENT_DATE + INTERVAL '28 days',
        CURRENT_DATE + INTERVAL '42 days',
        CURRENT_DATE + INTERVAL '56 days'
    ]::DATE[]),
    unnest(ARRAY[10, 8, 12, 15]),
    NULL,
    unnest(ARRAY[FALSE, FALSE, FALSE, FALSE]),
    NULL,
    g.created_at + INTERVAL '1 day',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT'
AND g.title LIKE '%Python%'
LIMIT 5;

-- Plan items for career goals
INSERT INTO tb_coaching_plan (
    goal_id, title, description, order_index, due_date,
    estimated_hours, is_completed, created_at, ins_user_id, ins_dt
)
SELECT
    g.goal_id,
    unnest(ARRAY['이력서 작성', '포트폴리오 정리', '기술 면접 준비', '기업 분석']),
    unnest(ARRAY[
        '핵심 경력 및 프로젝트 중심 이력서 작성',
        'GitHub 프로젝트 정리 및 README 업데이트',
        '자주 나오는 기술 면접 질문 정리 및 연습',
        '관심 기업 리스트업 및 기업 문화 분석'
    ]),
    unnest(ARRAY[0, 1, 2, 3]),
    unnest(ARRAY[
        CURRENT_DATE + INTERVAL '7 days',
        CURRENT_DATE + INTERVAL '21 days',
        CURRENT_DATE + INTERVAL '35 days',
        CURRENT_DATE + INTERVAL '49 days'
    ]::DATE[]),
    unnest(ARRAY[5, 10, 15, 5]),
    unnest(ARRAY[FALSE, FALSE, FALSE, FALSE]),
    g.created_at + INTERVAL '1 day',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT'
AND g.goal_type = 'career'
LIMIT 10;

-- Plan items for academic goals
INSERT INTO tb_coaching_plan (
    goal_id, title, description, order_index, due_date,
    estimated_hours, is_completed, created_at, ins_user_id, ins_dt
)
SELECT
    g.goal_id,
    unnest(ARRAY['주간 학습 계획', '과제 관리', '시험 준비', '스터디 참여']),
    unnest(ARRAY[
        '매주 과목별 학습 시간 배분 계획',
        '과제 마감일 캘린더 관리',
        '중간/기말고사 2주 전 복습 시작',
        '주 2회 스터디 그룹 참여'
    ]),
    unnest(ARRAY[0, 1, 2, 3]),
    unnest(ARRAY[
        CURRENT_DATE + INTERVAL '7 days',
        CURRENT_DATE + INTERVAL '14 days',
        CURRENT_DATE + INTERVAL '30 days',
        CURRENT_DATE + INTERVAL '14 days'
    ]::DATE[]),
    unnest(ARRAY[3, 5, 20, 4]),
    unnest(ARRAY[FALSE, FALSE, FALSE, FALSE]),
    g.created_at + INTERVAL '1 day',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT'
AND g.goal_type = 'academic'
LIMIT 10;

-- ============================================
-- 4. Coaching Check-ins
-- ============================================

INSERT INTO tb_coaching_checkin (
    goal_id, mood, progress_note, blockers, next_steps,
    reflection, ai_feedback, ai_suggestions,
    created_at, ins_user_id, ins_dt
)
SELECT
    g.goal_id,
    unnest(ARRAY['good', 'great', 'neutral', 'struggling']),
    unnest(ARRAY[
        '이번 주 Pandas 강의 50% 완료',
        '프로젝트 아이디어 구상 완료',
        '시간 부족으로 진도가 느림',
        '어려운 개념에서 막힘'
    ]),
    unnest(ARRAY[
        NULL,
        NULL,
        '다른 과목 시험 준비로 시간 부족',
        '복잡한 알고리즘 이해가 어려움'
    ]),
    unnest(ARRAY[
        'DataFrame 조작 실습 예정',
        '프로젝트 개발 시작',
        '주말에 집중 학습 예정',
        '멘토에게 질문하기'
    ]),
    unnest(ARRAY[
        '꾸준히 하면 될 것 같다',
        '진전이 있어서 기분이 좋다',
        '시간 관리가 필요하다',
        '포기하지 않고 계속 도전'
    ]),
    unnest(ARRAY[
        '좋은 진행 상황이네요! 이 모멘텀을 유지하세요.',
        '훌륭합니다! 이미 절반 이상 왔네요.',
        '꾸준히 진행하고 있군요. 작은 성취도 인정해주세요.',
        '어려움을 겪고 있군요. 잠시 휴식을 취하거나 목표를 작게 나눠보세요.'
    ]),
    unnest(ARRAY[
        ARRAY['매일 30분씩 코딩 연습'],
        ARRAY['주말에 추가 학습 시간 확보'],
        ARRAY['작은 단위로 목표 분해'],
        ARRAY['멘토나 동료에게 조언 구하기']
    ]),
    g.created_at + unnest(ARRAY[
        INTERVAL '7 days',
        INTERVAL '14 days',
        INTERVAL '21 days',
        INTERVAL '28 days'
    ]),
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT'
AND g.status = 'active'
LIMIT 30;

-- ============================================
-- 5. Coaching Retrospectives
-- ============================================

INSERT INTO tb_coaching_retrospective (
    goal_id, what_went_well, what_could_improve,
    lessons_learned, next_goals, satisfaction_rating,
    ai_analysis, ai_recommendations,
    created_at, ins_user_id, ins_dt
)
SELECT
    g.goal_id,
    CASE g.goal_type
        WHEN 'career' THEN '꾸준한 학습 습관이 형성되고, 포트폴리오 프로젝트를 시작함'
        WHEN 'skill' THEN '새로운 기술 스택에 대한 기초를 다짐'
        WHEN 'academic' THEN '출석률과 과제 제출률이 향상됨'
        ELSE '목표에 대한 명확한 방향성을 설정함'
    END,
    CASE g.goal_type
        WHEN 'career' THEN '실전 경험 부족, 네트워킹 기회 탐색 필요'
        WHEN 'skill' THEN '실전 프로젝트 적용 경험 부족'
        WHEN 'academic' THEN '시험 기간 집중력 관리 필요'
        ELSE '시간 관리 개선 필요'
    END,
    CASE g.goal_type
        WHEN 'career' THEN '작은 프로젝트부터 완성하는 것이 중요하다는 것을 배움'
        WHEN 'skill' THEN '반복 학습의 중요성을 깨달음'
        WHEN 'academic' THEN '계획적인 학습이 성적 향상에 직접적인 상관'
        ELSE '꾸준함이 가장 중요하다'
    END,
    CASE g.goal_type
        WHEN 'career' THEN '다음 분기에 인턴십 지원'
        WHEN 'skill' THEN '고급 과정 수강 시작'
        WHEN 'academic' THEN '다음 학기 GPA 3.7 이상 목표'
        ELSE '더 구체적인 액션 플랜 수립'
    END,
    (3 + (RANDOM() * 2)::INT),
    '이번 기간 동안 ' || g.title || ' 목표를 향해 꾸준히 노력했습니다. 전반적으로 긍정적인 진전이 있었으며, 몇 가지 개선점을 발견했습니다.',
    ARRAY['고급 과정 진행', '실전 프로젝트 참여', '멘토링 프로그램 신청'],
    g.created_at + INTERVAL '30 days',
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_coaching_goal g
WHERE g.ins_user_id = 'SEED_SCRIPT'
AND g.status IN ('active', 'completed')
AND RANDOM() > 0.5
LIMIT 25;

-- ============================================
-- Verification
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

    RAISE NOTICE '=== P1 Coaching Seed Data V2 Created ===';
    RAISE NOTICE 'tb_coaching_goal: % records', goal_count;
    RAISE NOTICE 'tb_coaching_plan: % records', plan_count;
    RAISE NOTICE 'tb_coaching_checkin: % records', checkin_count;
    RAISE NOTICE 'tb_coaching_retrospective: % records', retro_count;
END $$;
