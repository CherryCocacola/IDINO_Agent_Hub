-- ============================================
-- 38. Seed Activities Supplement
-- Date: 2026-01-29
-- Purpose: 비교과활동 데이터 보완 - 활동이 부족한 학생에게 학과별 활동 추가 (~200건)
-- Current: tb_activity has 91,704 records
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- STEP 0: 기존 데이터 현황 확인 (검증용)
-- ============================================

-- 기존 activity_type 분포 확인
DO $$
DECLARE
    v_count BIGINT;
    v_types TEXT;
BEGIN
    SELECT COUNT(*) INTO v_count FROM tb_activity;
    RAISE NOTICE '[사전 검증] tb_activity 현재 총 건수: %', v_count;

    SELECT string_agg(DISTINCT activity_type, ', ' ORDER BY activity_type)
    INTO v_types
    FROM tb_activity;
    RAISE NOTICE '[사전 검증] 기존 activity_type 목록: %', v_types;
END $$;

-- program_cd 참조 무결성 확인
DO $$
DECLARE
    v_orphan BIGINT;
BEGIN
    SELECT COUNT(*) INTO v_orphan
    FROM tb_activity a
    WHERE a.program_cd IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM tb_program p WHERE p.program_cd = a.program_cd);
    RAISE NOTICE '[사전 검증] program_cd 참조 무결성 위반 건수: %', v_orphan;
END $$;

-- ============================================
-- STEP 1: 활동이 2건 미만인 학생에게 학과별 활동 추가
-- ============================================

-- 1-1. 공학 계열 (department_cd IN 1034, 1083, 1086, 1089, 1169, 1196)
--      competition, workshop, project, seminar
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    -- 활동이 2건 미만인 공학계열 학생 (최대 25명)
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1034', '1083', '1086', '1089', '1169', '1196')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id) < 2
    ORDER BY RANDOM()
    LIMIT 25
) s
CROSS JOIN LATERAL (
    VALUES
        ('competition', '전국 대학생 프로그래밍 경진대회',
         '전국 규모의 대학생 프로그래밍 경진대회에 참가하여 알고리즘 문제 해결 능력을 겨루었습니다.',
         DATE '2024-05-10' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-05-12' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         ROUND((10 + RANDOM() * 30)::NUMERIC, 1),
         '예선 통과 및 본선 진출',
         'completed', 'Y'),
        ('workshop', '3D프린팅 워크숍',
         '3D 모델링 소프트웨어 활용 및 3D프린터 실습을 통한 제조 공정 이해 워크숍입니다.',
         DATE '2024-09-01' + (FLOOR(RANDOM() * 90)::INT || ' days')::INTERVAL,
         DATE '2024-09-15' + (FLOOR(RANDOM() * 90)::INT || ' days')::INTERVAL,
         ROUND((15 + RANDOM() * 25)::NUMERIC, 1),
         '3D프린팅 실습 결과물 완성',
         'completed', 'Y'),
        ('project', '캡스톤 디자인 프로젝트',
         '산업체 연계 캡스톤 디자인 프로젝트로 실제 현장 문제를 해결하는 팀 프로젝트입니다.',
         DATE '2025-03-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2025-09-30' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((80 + RANDOM() * 120)::NUMERIC, 1),
         NULL,
         'in_progress', 'N'),
        ('seminar', '4차 산업혁명 세미나',
         '4차 산업혁명 핵심 기술(IoT, AI, 빅데이터, 클라우드) 동향 및 전망에 대한 세미나입니다.',
         DATE '2024-06-15' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-06-16' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         ROUND((10 + RANDOM() * 10)::NUMERIC, 1),
         '수료증 발급',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- 1-2. IT/데이터 계열 (department_cd IN 1160, 1101)
--      hackathon, study, project
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1160', '1101')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id) < 2
    ORDER BY RANDOM()
    LIMIT 20
) s
CROSS JOIN LATERAL (
    VALUES
        ('hackathon', 'AI 해커톤',
         '인공지능 기반 서비스 개발 해커톤 대회에 참가하여 48시간 동안 프로토타입을 개발했습니다.',
         DATE '2024-07-20' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-07-22' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         ROUND((20 + RANDOM() * 30)::NUMERIC, 1),
         '최우수상 수상',
         'completed', 'Y'),
        ('study', '알고리즘 스터디',
         '코딩테스트 대비 알고리즘 스터디 그룹으로 매주 정기적으로 문제풀이를 진행합니다.',
         DATE '2025-03-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2025-11-30' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((60 + RANDOM() * 80)::NUMERIC, 1),
         NULL,
         'in_progress', 'N'),
        ('project', '오픈소스 프로젝트 기여',
         'GitHub 오픈소스 프로젝트에 기여하여 이슈 해결 및 PR을 제출하는 활동입니다.',
         DATE '2024-04-01' + (FLOOR(RANDOM() * 90)::INT || ' days')::INTERVAL,
         DATE '2024-08-31' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((40 + RANDOM() * 60)::NUMERIC, 1),
         'PR 5건 병합 완료',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- 1-3. 경영/사회 계열 (department_cd IN 1440, 1137, 1012, 1079, 1289)
--      competition, volunteer, internship
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1440', '1137', '1012', '1079', '1289')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id) < 2
    ORDER BY RANDOM()
    LIMIT 20
) s
CROSS JOIN LATERAL (
    VALUES
        ('competition', '창업 아이디어 경진대회',
         '대학생 창업 아이디어 경진대회에서 혁신적인 비즈니스 모델을 발표하고 평가받았습니다.',
         DATE '2024-04-01' + (FLOOR(RANDOM() * 90)::INT || ' days')::INTERVAL,
         DATE '2024-06-30' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((30 + RANDOM() * 50)::NUMERIC, 1),
         '우수상 수상',
         'completed', 'Y'),
        ('volunteer', '지역사회 봉사활동',
         '지역사회 소외계층 대상 교육봉사 및 생활지원 봉사활동에 참여했습니다.',
         DATE '2024-08-01' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-08-31' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         ROUND((20 + RANDOM() * 40)::NUMERIC, 1),
         '봉사시간 40시간 인증',
         'completed', 'Y'),
        ('internship', '기업 현장실습',
         '산학협력 기업에서 현장실습을 수행하며 실무 경험을 쌓았습니다.',
         DATE '2024-06-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2024-08-31' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((150 + RANDOM() * 50)::NUMERIC, 1),
         '현장실습 수료증 발급',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- 1-4. 보건/의료 계열 (department_cd IN 1144, 354, 356, 1237)
--      practicum, volunteer
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1144', '354', '356', '1237')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id) < 2
    ORDER BY RANDOM()
    LIMIT 15
) s
CROSS JOIN LATERAL (
    VALUES
        ('practicum', '병원 임상 실습',
         '대학병원 협력기관에서 임상 실습을 수행하며 환자 케어 및 의료 프로세스를 학습합니다.',
         DATE '2025-03-01' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2025-08-31' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((100 + RANDOM() * 100)::NUMERIC, 1),
         NULL,
         'in_progress', 'N'),
        ('volunteer', '의료봉사단 활동',
         '대학 의료봉사단에 소속되어 농어촌 지역 의료봉사 활동에 참여했습니다.',
         DATE '2024-07-15' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-08-15' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((30 + RANDOM() * 50)::NUMERIC, 1),
         '봉사활동 우수 인증',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- ============================================
-- STEP 2: 전체 학과 공통 활동 추가 (leadership, mentoring)
-- 활동이 부족한 학생에게 학생회 및 멘토링 활동 보완
-- ============================================

-- 2-1. 학생회 활동 (leadership)
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'leadership',
    '학생회 활동',
    '학과 또는 단과대학 학생회 임원으로 활동하며 학생 자치 활동과 행사 기획에 참여했습니다.',
    DATE '2024-03-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
    DATE '2024-12-31',
    ROUND((80 + RANDOM() * 120)::NUMERIC, 1),
    '학생회 우수 활동상',
    'completed',
    'Y',
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id) < 2
    ORDER BY RANDOM()
    LIMIT 20
) s
WHERE NOT EXISTS (
    SELECT 1 FROM tb_activity a
    WHERE a.student_id = s.student_id AND a.title = '학생회 활동' AND a.ins_user_id = 'ACTIVITY_SEED'
);

-- 2-2. 신입생 멘토링 (mentoring)
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    'mentoring',
    '신입생 멘토링',
    '신입생 대상 학업 및 대학생활 적응을 위한 선배 멘토링 프로그램에 멘토로 참여했습니다.',
    DATE '2025-03-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
    DATE '2025-06-30' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
    ROUND((20 + RANDOM() * 40)::NUMERIC, 1),
    '멘토링 프로그램 수료',
    'completed',
    'Y',
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.current_grade >= 2
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id) < 2
    ORDER BY RANDOM()
    LIMIT 20
) s
WHERE NOT EXISTS (
    SELECT 1 FROM tb_activity a
    WHERE a.student_id = s.student_id AND a.title = '신입생 멘토링' AND a.ins_user_id = 'ACTIVITY_SEED'
);

-- ============================================
-- STEP 3: 추가 다양성 확보 - 학과별 추가 활동 (나머지 약 60건 보충)
-- ============================================

-- 3-1. 공학 계열 추가 활동 - 기업 견학, 학술대회 참가
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1034', '1083', '1086', '1089', '1169', '1196')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id AND a.ins_user_id = 'ACTIVITY_SEED') < 4
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    VALUES
        ('seminar', '기업 기술 세미나 참관',
         '삼성전자, LG전자 등 주요 기업 기술 세미나에 참관하여 최신 산업 동향을 학습했습니다.',
         DATE '2024-10-01' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-10-02' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         ROUND((10 + RANDOM() * 10)::NUMERIC, 1),
         '참가 확인서 발급',
         'completed', 'Y'),
        ('competition', '교내 공학 설계 경진대회',
         '교내 공학 설계 경진대회에서 팀을 구성하여 창의적 설계 프로젝트를 수행했습니다.',
         DATE '2025-05-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2025-06-15' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((30 + RANDOM() * 50)::NUMERIC, 1),
         '장려상 수상',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- 3-2. IT/데이터 계열 추가 활동 - 데이터 분석 대회, 기술 블로그
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1160', '1101')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id AND a.ins_user_id = 'ACTIVITY_SEED') < 3
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    VALUES
        ('competition', '데이터 분석 경진대회',
         'Kaggle 또는 DACON 데이터 분석 대회에 참가하여 데이터 전처리 및 모델링 역량을 발휘했습니다.',
         DATE '2024-08-01' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-10-31' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((40 + RANDOM() * 60)::NUMERIC, 1),
         '상위 10% 달성',
         'completed', 'Y'),
        ('project', '기술 블로그 운영',
         '개인 기술 블로그를 운영하며 학습 내용과 프로젝트 경험을 정리하고 공유했습니다.',
         DATE '2024-03-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2025-06-30' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((50 + RANDOM() * 50)::NUMERIC, 1),
         '누적 방문자 1만명 달성',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- 3-3. 경영/사회 계열 추가 활동 - 마케팅 공모전, 모의 주식투자
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1440', '1137', '1012', '1079', '1289')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id AND a.ins_user_id = 'ACTIVITY_SEED') < 3
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    VALUES
        ('competition', '대학생 마케팅 공모전',
         '기업 연계 대학생 마케팅 전략 공모전에서 브랜드 마케팅 전략을 기획하고 발표했습니다.',
         DATE '2024-03-15' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-06-15' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((40 + RANDOM() * 40)::NUMERIC, 1),
         '본선 진출',
         'completed', 'Y'),
        ('study', '모의 주식투자 스터디',
         '모의 주식투자 시뮬레이션을 통한 금융시장 분석 및 투자 전략 학습 스터디입니다.',
         DATE '2025-03-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2025-08-31' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((30 + RANDOM() * 50)::NUMERIC, 1),
         NULL,
         'in_progress', 'N')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- 3-4. 보건/의료 계열 추가 활동 - 건강증진 캠페인, 학술 논문 발표
INSERT INTO tb_activity (student_id, activity_type, title, description, start_date, end_date, hours, achievement, status, verified, ins_user_id, ins_dt)
SELECT
    s.student_id,
    act.activity_type,
    act.title,
    act.description,
    act.start_date,
    act.end_date,
    act.hours,
    act.achievement,
    act.status,
    act.verified,
    'ACTIVITY_SEED',
    CURRENT_TIMESTAMP
FROM (
    SELECT st.student_id
    FROM tb_student st
    WHERE st.department_cd IN ('1144', '354', '356', '1237')
      AND (SELECT COUNT(*) FROM tb_activity a WHERE a.student_id = st.student_id AND a.ins_user_id = 'ACTIVITY_SEED') < 2
    ORDER BY RANDOM()
    LIMIT 10
) s
CROSS JOIN LATERAL (
    VALUES
        ('volunteer', '건강증진 캠페인',
         '지역 주민 대상 건강검진 및 건강 생활습관 교육 캠페인에 참여했습니다.',
         DATE '2024-09-01' + (FLOOR(RANDOM() * 60)::INT || ' days')::INTERVAL,
         DATE '2024-09-30' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((15 + RANDOM() * 25)::NUMERIC, 1),
         '캠페인 우수 참여자 선정',
         'completed', 'Y'),
        ('seminar', '보건의료 학술 발표대회',
         '대학 보건의료 학술 발표대회에서 연구 논문을 발표하고 학술 토론에 참여했습니다.',
         DATE '2025-05-01' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         DATE '2025-05-02' + (FLOOR(RANDOM() * 30)::INT || ' days')::INTERVAL,
         ROUND((10 + RANDOM() * 15)::NUMERIC, 1),
         '우수 논문 발표상',
         'completed', 'Y')
) AS act(activity_type, title, description, start_date, end_date, hours, achievement, status, verified);

-- ============================================
-- STEP 4: 결과 검증
-- ============================================

DO $$
DECLARE
    v_new_count BIGINT;
    v_total_count BIGINT;
    v_type_dist TEXT;
BEGIN
    SELECT COUNT(*) INTO v_new_count
    FROM tb_activity
    WHERE ins_user_id = 'ACTIVITY_SEED';

    SELECT COUNT(*) INTO v_total_count
    FROM tb_activity;

    RAISE NOTICE '============================================';
    RAISE NOTICE '[결과 검증] ACTIVITY_SEED로 추가된 건수: %', v_new_count;
    RAISE NOTICE '[결과 검증] tb_activity 총 건수: %', v_total_count;
    RAISE NOTICE '============================================';

    -- 추가된 activity_type별 분포
    FOR v_type_dist IN
        SELECT activity_type || ': ' || COUNT(*)
        FROM tb_activity
        WHERE ins_user_id = 'ACTIVITY_SEED'
        GROUP BY activity_type
        ORDER BY COUNT(*) DESC
    LOOP
        RAISE NOTICE '[분포] %', v_type_dist;
    END LOOP;
END $$;
