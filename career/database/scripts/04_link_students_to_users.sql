-- ============================================
-- 2021-2025 전체 입학년도 학생 tb_user 연동 스크립트
-- ============================================
-- 목적: admission_year가 2021~2025인 전체 학생을 tb_user와 연동
--       역량 점수, 누적 성적, 진로 정보, 코칭 목표 데이터 생성
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. 2025년 입학생 데이터 생성 (없는 경우)
-- ============================================
DO $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count FROM tb_student WHERE admission_year = 2025;
    IF v_count = 0 THEN
        RAISE NOTICE '2025년 입학생 데이터가 없습니다. 생성을 시작합니다...';
    ELSE
        RAISE NOTICE '2025년 입학생 데이터 % 건 존재', v_count;
    END IF;
END $$;

-- 2025년 입학생 추가 (다양한 학과별로 2건 이상)
INSERT INTO tb_student (student_id, student_nm, university_cd, department_cd, admission_year, current_grade, current_semester, email, phone, birth_date, gender, status, career_goal, ins_user_id, ins_dt)
SELECT * FROM (VALUES
-- 컴퓨터공학과 (DEPT001)
('2025010001', '김하늘', 'UNIV001', 'DEPT001', 2025, 1, 1, 'haneul.kim25@kstu.ac.kr', '010-2525-0001', '2006-03-15'::DATE, 'F', 'enrolled', 'AI엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010002', '이준혁', 'UNIV001', 'DEPT001', 2025, 1, 1, 'junhyuk.lee25@kstu.ac.kr', '010-2525-0002', '2006-05-22'::DATE, 'M', 'enrolled', '백엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010003', '박서연', 'UNIV001', 'DEPT001', 2025, 1, 1, 'seoyeon.park25@kstu.ac.kr', '010-2525-0003', '2006-08-10'::DATE, 'F', 'enrolled', '데이터엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
-- 소프트웨어학과 (DEPT002)
('2025020001', '정민서', 'UNIV001', 'DEPT002', 2025, 1, 1, 'minseo.jung25@kstu.ac.kr', '010-2525-0004', '2006-01-28'::DATE, 'F', 'enrolled', '프론트엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020002', '최우진', 'UNIV001', 'DEPT002', 2025, 1, 1, 'woojin.choi25@kstu.ac.kr', '010-2525-0005', '2006-04-05'::DATE, 'M', 'enrolled', '게임개발자', 'SYSTEM', CURRENT_TIMESTAMP),
-- 전자공학과 (DEPT003)
('2025030001', '강예린', 'UNIV001', 'DEPT003', 2025, 1, 1, 'yerin.kang25@kstu.ac.kr', '010-2525-0006', '2006-02-18'::DATE, 'F', 'enrolled', '반도체엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030002', '윤태준', 'UNIV001', 'DEPT003', 2025, 1, 1, 'taejun.yoon25@kstu.ac.kr', '010-2525-0007', '2006-06-25'::DATE, 'M', 'enrolled', 'IoT엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
-- 경영학과 (DEPT014)
('2025140001', '임소현', 'UNIV001', 'DEPT014', 2025, 1, 1, 'sohyun.lim25@kstu.ac.kr', '010-2525-0008', '2006-09-30'::DATE, 'F', 'enrolled', '마케팅전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140002', '한도윤', 'UNIV001', 'DEPT014', 2025, 1, 1, 'doyun.han25@kstu.ac.kr', '010-2525-0009', '2006-03-08'::DATE, 'M', 'enrolled', '경영컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),
-- 통계학과 (DEPT013)
('2025130001', '오지민', 'UNIV001', 'DEPT013', 2025, 1, 1, 'jimin.oh25@kstu.ac.kr', '010-2525-0010', '2006-05-14'::DATE, 'F', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130002', '서현우', 'UNIV001', 'DEPT013', 2025, 1, 1, 'hyunwoo.seo25@kstu.ac.kr', '010-2525-0011', '2006-08-21'::DATE, 'M', 'enrolled', 'AI연구원', 'SYSTEM', CURRENT_TIMESTAMP),
-- 산업공학과 (DEPT006)
('2025060001', '배지원', 'UNIV001', 'DEPT006', 2025, 1, 1, 'jiwon.bae25@kstu.ac.kr', '010-2525-0012', '2006-11-03'::DATE, 'F', 'enrolled', '생산관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060002', '황민재', 'UNIV001', 'DEPT006', 2025, 1, 1, 'minjae.hwang25@kstu.ac.kr', '010-2525-0013', '2006-12-17'::DATE, 'M', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP)
) AS v(student_id, student_nm, university_cd, department_cd, admission_year, current_grade, current_semester, email, phone, birth_date, gender, status, career_goal, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_student s WHERE s.student_id = v.student_id);

-- ============================================
-- 2. 2021-2025 전체 입학생 tb_user 연동
-- ============================================
-- 비밀번호: student123 (bcrypt hash)
-- $2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi

-- 전체 입학생 연동 (2021-2025)
INSERT INTO tb_user (user_id, login_id, password_hash, user_nm, user_type, student_id, email, status, mfa_enabled, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,  -- login_id = 학번
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',  -- student123
    s.student_nm,  -- user_nm = 학생 이름
    'student',
    s.student_id,
    s.email,
    'active',
    FALSE,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_user u WHERE u.student_id = s.student_id)
ON CONFLICT (login_id) DO NOTHING;

-- ============================================
-- 3. 전체 연동 학생 역량 점수 생성 (누락분)
-- ============================================
INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    c.competency_cd,
    CASE
        WHEN s.admission_year <= 2022 THEN ROUND((55 + RANDOM() * 40)::numeric, 1)  -- 3-4학년: 높은 점수
        WHEN s.admission_year = 2023 THEN ROUND((45 + RANDOM() * 40)::numeric, 1)   -- 2학년: 중간 점수
        WHEN s.admission_year = 2024 THEN ROUND((35 + RANDOM() * 40)::numeric, 1)   -- 1학년: 낮은 점수
        ELSE ROUND((30 + RANDOM() * 40)::numeric, 1)                                 -- 신입생
    END as current_score,
    85 as target_score,
    0 as gap_score,
    CASE
        WHEN RANDOM() < 0.15 THEN 'excellent'
        WHEN RANDOM() < 0.35 THEN 'good'
        WHEN RANDOM() < 0.6 THEN 'average'
        WHEN RANDOM() < 0.8 THEN 'improve'
        ELSE 'focus'
    END as status,
    CASE
        WHEN RANDOM() < 0.4 THEN 'up'
        WHEN RANDOM() < 0.7 THEN 'stable'
        ELSE 'down'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_competency c
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_student_competency sc
    WHERE sc.student_id = s.student_id AND sc.competency_cd = c.competency_cd
);

-- gap_score 업데이트
UPDATE tb_student_competency
SET gap_score = target_score - current_score
WHERE student_id IN (SELECT student_id FROM tb_student WHERE admission_year IN (2021, 2022, 2023, 2024, 2025))
AND gap_score = 0;

-- ============================================
-- 4. 전체 연동 학생 누적 성적 요약 생성 (누락분)
-- ============================================
INSERT INTO tb_cumulative_summary (student_id, total_credits_earned, major_credits_earned, liberal_credits_earned, cumulative_gpa, major_gpa, completion_rate, ins_user_id, ins_dt)
SELECT
    student_id,
    CASE
        WHEN admission_year = 2021 THEN FLOOR(100 + RANDOM() * 30)
        WHEN admission_year = 2022 THEN FLOOR(70 + RANDOM() * 25)
        WHEN admission_year = 2023 THEN FLOOR(40 + RANDOM() * 20)
        WHEN admission_year = 2024 THEN FLOOR(15 + RANDOM() * 15)
        ELSE FLOOR(0 + RANDOM() * 15)
    END as total_credits_earned,
    CASE
        WHEN admission_year = 2021 THEN FLOOR(45 + RANDOM() * 15)
        WHEN admission_year = 2022 THEN FLOOR(30 + RANDOM() * 12)
        WHEN admission_year = 2023 THEN FLOOR(18 + RANDOM() * 10)
        WHEN admission_year = 2024 THEN FLOOR(6 + RANDOM() * 8)
        ELSE FLOOR(0 + RANDOM() * 6)
    END as major_credits_earned,
    CASE
        WHEN admission_year = 2021 THEN FLOOR(25 + RANDOM() * 10)
        WHEN admission_year = 2022 THEN FLOOR(18 + RANDOM() * 8)
        WHEN admission_year = 2023 THEN FLOOR(12 + RANDOM() * 6)
        WHEN admission_year = 2024 THEN FLOOR(6 + RANDOM() * 5)
        ELSE FLOOR(0 + RANDOM() * 6)
    END as liberal_credits_earned,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as cumulative_gpa,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as major_gpa,
    CASE
        WHEN admission_year = 2021 THEN ROUND((70 + RANDOM() * 25)::numeric, 1)
        WHEN admission_year = 2022 THEN ROUND((50 + RANDOM() * 30)::numeric, 1)
        WHEN admission_year = 2023 THEN ROUND((30 + RANDOM() * 25)::numeric, 1)
        WHEN admission_year = 2024 THEN ROUND((10 + RANDOM() * 20)::numeric, 1)
        ELSE ROUND((0 + RANDOM() * 10)::numeric, 1)
    END as completion_rate,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_cumulative_summary cs WHERE cs.student_id = tb_student.student_id);

-- ============================================
-- 5. 전체 연동 학생 진로 정보 생성 (누락분)
-- ============================================
INSERT INTO tb_student_career (
    student_id,
    primary_career_goal,
    primary_role_cd,
    interest_role_cds,
    interest_industries,
    preferred_company_size,
    preferred_work_style,
    preferred_regions,
    resume_prepared,
    portfolio_prepared,
    interview_ready,
    career_notes,
    ins_user_id,
    ins_dt
)
SELECT
    s.student_id,
    s.career_goal,
    (SELECT role_cd FROM tb_role ORDER BY RANDOM() LIMIT 1),
    ARRAY[(SELECT role_cd FROM tb_role ORDER BY RANDOM() LIMIT 1)],
    ARRAY['IT', '스타트업'],
    CASE WHEN RANDOM() < 0.5 THEN 'startup' ELSE 'large' END,
    CASE WHEN RANDOM() < 0.5 THEN 'hybrid' ELSE 'remote' END,
    ARRAY['서울', '경기'],
    CASE WHEN s.admission_year <= 2022 THEN TRUE ELSE FALSE END,
    CASE WHEN s.admission_year <= 2022 THEN TRUE ELSE FALSE END,
    CASE WHEN s.admission_year = 2021 THEN TRUE ELSE FALSE END,
    CASE
        WHEN s.admission_year = 2021 THEN '취업 준비 중'
        WHEN s.admission_year = 2022 THEN '진로 구체화 단계'
        WHEN s.admission_year = 2023 THEN '진로 탐색 중'
        ELSE '진로 탐색 시작'
    END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (SELECT 1 FROM tb_student_career sc WHERE sc.student_id = s.student_id);

-- ============================================
-- 6. 코칭 목표 데이터 생성 (Sprint 메뉴용)
-- ============================================
-- 2021-2025 학생들의 스프린트 목표 생성
INSERT INTO tb_coaching_goal (std_id, title, description, priority, status, progress_percentage, ins_user_id, ins_dt)
SELECT
    s.student_id,
    goals.title,
    goals.description,
    goals.priority,
    goals.status,
    goals.progress,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
    ('전공 기초 역량 강화', '전공 필수 과목 이수 및 기초 프로그래밍 학습', 'high', 'in_progress', 30),
    ('영어 능력 향상', 'TOEIC 700점 이상 목표', 'medium', 'pending', 0),
    ('진로 탐색 활동', '멘토링 프로그램 참여 및 직무 탐색', 'medium', 'in_progress', 50),
    ('자격증 준비', '관련 분야 자격증 취득 준비', 'low', 'pending', 0)
) AS goals(title, description, priority, status, progress)
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
AND NOT EXISTS (
    SELECT 1 FROM tb_coaching_goal cg
    WHERE cg.std_id = s.student_id AND cg.title = goals.title
);

-- ============================================
-- 7. 결과 확인
-- ============================================
DO $$
DECLARE
    v_student_2025 INT;
    v_student_2024 INT;
    v_student_2023 INT;
    v_student_2022 INT;
    v_student_2021 INT;
    v_user_2025 INT;
    v_user_2024 INT;
    v_user_2023 INT;
    v_user_2022 INT;
    v_user_2021 INT;
BEGIN
    SELECT COUNT(*) INTO v_student_2025 FROM tb_student WHERE admission_year = 2025;
    SELECT COUNT(*) INTO v_student_2024 FROM tb_student WHERE admission_year = 2024;
    SELECT COUNT(*) INTO v_student_2023 FROM tb_student WHERE admission_year = 2023;
    SELECT COUNT(*) INTO v_student_2022 FROM tb_student WHERE admission_year = 2022;
    SELECT COUNT(*) INTO v_student_2021 FROM tb_student WHERE admission_year = 2021;

    SELECT COUNT(*) INTO v_user_2025
    FROM tb_user u JOIN tb_student s ON u.student_id = s.student_id
    WHERE s.admission_year = 2025;

    SELECT COUNT(*) INTO v_user_2024
    FROM tb_user u JOIN tb_student s ON u.student_id = s.student_id
    WHERE s.admission_year = 2024;

    SELECT COUNT(*) INTO v_user_2023
    FROM tb_user u JOIN tb_student s ON u.student_id = s.student_id
    WHERE s.admission_year = 2023;

    SELECT COUNT(*) INTO v_user_2022
    FROM tb_user u JOIN tb_student s ON u.student_id = s.student_id
    WHERE s.admission_year = 2022;

    SELECT COUNT(*) INTO v_user_2021
    FROM tb_user u JOIN tb_student s ON u.student_id = s.student_id
    WHERE s.admission_year = 2021;

    RAISE NOTICE '======================================';
    RAISE NOTICE '학생-사용자 연동 결과';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE '2021년: 학생 % 명 / 사용자 연동 % 명', v_student_2021, v_user_2021;
    RAISE NOTICE '2022년: 학생 % 명 / 사용자 연동 % 명', v_student_2022, v_user_2022;
    RAISE NOTICE '2023년: 학생 % 명 / 사용자 연동 % 명', v_student_2023, v_user_2023;
    RAISE NOTICE '2024년: 학생 % 명 / 사용자 연동 % 명', v_student_2024, v_user_2024;
    RAISE NOTICE '2025년: 학생 % 명 / 사용자 연동 % 명', v_student_2025, v_user_2025;
    RAISE NOTICE '======================================';
    RAISE NOTICE '';
    RAISE NOTICE '테스트 계정 정보:';
    RAISE NOTICE '  로그인 ID: 학번 (예: 2021010001, 2025010001)';
    RAISE NOTICE '  비밀번호: student123';
    RAISE NOTICE '======================================';
END $$;

-- 연동된 학생 목록 샘플 조회
SELECT
    u.login_id,
    s.student_nm,
    s.admission_year,
    d.department_nm,
    s.career_goal
FROM tb_user u
JOIN tb_student s ON u.student_id = s.student_id
LEFT JOIN tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year IN (2021, 2022, 2023, 2024, 2025)
ORDER BY s.admission_year DESC, u.login_id
LIMIT 30;
