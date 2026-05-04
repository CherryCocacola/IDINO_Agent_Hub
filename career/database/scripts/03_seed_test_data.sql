-- ============================================
-- 03. 테스트 데이터 INSERT 스크립트
-- ============================================
-- 실행 전: migration_001_auth_and_career.sql 먼저 실행
--
-- 테스트 계정 정보:
-- ┌───────────────┬──────────────┬──────────────┐
-- │ Login ID      │ Password     │ Type         │
-- ├───────────────┼──────────────┼──────────────┤
-- │ admin         │ admin123     │ admin        │
-- │ career_admin  │ admin123     │ career_admin │
-- │ student_hong  │ student123   │ student      │
-- │ student_lee   │ student123   │ student      │
-- │ prof_kim      │ prof123      │ professor    │
-- └───────────────┴──────────────┴──────────────┘
--
-- 비밀번호 해시: bcrypt (passlib[bcrypt] 라이브러리 사용)
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. 테스트 사용자 계정 INSERT
-- ============================================
-- 주의: 비밀번호 해시는 bcrypt로 생성됨
-- Python: from passlib.context import CryptContext
--         pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
--         pwd_context.hash("admin123")

-- 관리자 계정
INSERT INTO tb_user (
    user_id, login_id, password_hash, user_type,
    email, status, mfa_enabled,
    ins_user_id, ins_dt
) VALUES (
    uuid_generate_v4(),
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdpPscXgUi7Qolu',  -- admin123
    'admin',
    'admin@university.ac.kr',
    'active',
    FALSE,
    'system',
    CURRENT_TIMESTAMP
) ON CONFLICT (login_id) DO NOTHING;

-- 취업지원센터 관리자
INSERT INTO tb_user (
    user_id, login_id, password_hash, user_type,
    email, status, mfa_enabled,
    ins_user_id, ins_dt
) VALUES (
    uuid_generate_v4(),
    'career_admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdpPscXgUi7Qolu',  -- admin123
    'career_admin',
    'career@university.ac.kr',
    'active',
    FALSE,
    'system',
    CURRENT_TIMESTAMP
) ON CONFLICT (login_id) DO NOTHING;

-- 학생 계정 1 (홍길동)
-- 먼저 학생이 존재하는지 확인 후 연결
INSERT INTO tb_user (
    user_id, login_id, password_hash, user_type,
    student_id, email, status, mfa_enabled,
    ins_user_id, ins_dt
) VALUES (
    uuid_generate_v4(),
    'student_hong',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',  -- student123
    'student',
    (SELECT student_id FROM tb_student WHERE student_nm = '홍길동' LIMIT 1),
    'hong@student.ac.kr',
    'active',
    FALSE,
    'system',
    CURRENT_TIMESTAMP
) ON CONFLICT (login_id) DO NOTHING;

-- 학생 계정 2 (이영희)
INSERT INTO tb_user (
    user_id, login_id, password_hash, user_type,
    student_id, email, status, mfa_enabled,
    ins_user_id, ins_dt
) VALUES (
    uuid_generate_v4(),
    'student_lee',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',  -- student123
    'student',
    (SELECT student_id FROM tb_student WHERE student_nm = '이영희' LIMIT 1),
    'lee@student.ac.kr',
    'active',
    FALSE,
    'system',
    CURRENT_TIMESTAMP
) ON CONFLICT (login_id) DO NOTHING;

-- 교수 계정
INSERT INTO tb_user (
    user_id, login_id, password_hash, user_type,
    professor_cd, email, status, mfa_enabled,
    ins_user_id, ins_dt
) VALUES (
    uuid_generate_v4(),
    'prof_kim',
    '$2b$12$K4e5X8qR.Pv9y8W3h2J/z.B.vN1FpG6cL0DmHjA8nQ5kI9tYuVwXi',  -- prof123
    'professor',
    (SELECT professor_cd FROM tb_professor WHERE professor_nm LIKE '김%' LIMIT 1),
    'prof@university.ac.kr',
    'active',
    FALSE,
    'system',
    CURRENT_TIMESTAMP
) ON CONFLICT (login_id) DO NOTHING;

-- ============================================
-- 2. 학생 없이 생성된 계정을 위한 더미 학생 데이터
-- ============================================
-- 만약 기존 학생 데이터가 없다면 아래 데이터 사용

-- 학생 데이터 확인 및 생성
DO $$
BEGIN
    -- 홍길동 학생이 없으면 생성
    IF NOT EXISTS (SELECT 1 FROM tb_student WHERE student_nm = '홍길동') THEN
        INSERT INTO tb_student (
            student_id, student_nm, university_cd, department_cd,
            admission_year, current_grade, current_semester,
            email, status, career_goal,
            ins_user_id, ins_dt
        ) VALUES (
            '2021010001',
            '홍길동',
            (SELECT university_cd FROM tb_university LIMIT 1),
            (SELECT department_cd FROM tb_department WHERE department_nm LIKE '%컴퓨터%' OR department_nm LIKE '%소프트웨어%' LIMIT 1),
            2021,
            3,
            5,
            'hong@student.ac.kr',
            'enrolled',
            '백엔드 개발자',
            'system',
            CURRENT_TIMESTAMP
        );

        -- 사용자 계정 업데이트
        UPDATE tb_user SET student_id = '2021010001' WHERE login_id = 'student_hong';

        RAISE NOTICE '홍길동 학생 데이터 생성 완료';
    END IF;

    -- 이영희 학생이 없으면 생성
    IF NOT EXISTS (SELECT 1 FROM tb_student WHERE student_nm = '이영희') THEN
        INSERT INTO tb_student (
            student_id, student_nm, university_cd, department_cd,
            admission_year, current_grade, current_semester,
            email, status, career_goal,
            ins_user_id, ins_dt
        ) VALUES (
            '2022010002',
            '이영희',
            (SELECT university_cd FROM tb_university LIMIT 1),
            (SELECT department_cd FROM tb_department WHERE department_nm LIKE '%컴퓨터%' OR department_nm LIKE '%소프트웨어%' LIMIT 1),
            2022,
            2,
            3,
            'lee@student.ac.kr',
            'enrolled',
            '프론트엔드 개발자',
            'system',
            CURRENT_TIMESTAMP
        );

        -- 사용자 계정 업데이트
        UPDATE tb_user SET student_id = '2022010002' WHERE login_id = 'student_lee';

        RAISE NOTICE '이영희 학생 데이터 생성 완료';
    END IF;
END $$;

-- ============================================
-- 3. 학생 진로 정보 테스트 데이터
-- ============================================
-- tb_student_career에 테스트 데이터 추가
-- 실제 스키마에 맞춤: interest_industries, preferred_regions, interview_ready 사용

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
    student_id,
    career_goal,
    (SELECT role_cd FROM tb_role WHERE role_nm LIKE '%백엔드%' OR role_nm LIKE '%개발%' LIMIT 1),
    ARRAY[(SELECT role_cd FROM tb_role WHERE role_nm LIKE '%풀스택%' LIMIT 1)],
    ARRAY['IT', '스타트업'],                       -- interest_industries
    'sme',                                          -- preferred_company_size (startup, sme, midsize, large, any)
    'hybrid',                                       -- preferred_work_style
    ARRAY['서울', '경기'],                          -- preferred_regions
    FALSE,                                          -- resume_prepared
    FALSE,                                          -- portfolio_prepared
    FALSE,                                          -- interview_ready
    '백엔드 개발자를 목표로 준비 중',               -- career_notes
    'system',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE student_nm = '홍길동'
ON CONFLICT (student_id) DO UPDATE SET
    primary_career_goal = EXCLUDED.primary_career_goal,
    upd_dt = CURRENT_TIMESTAMP;

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
    student_id,
    career_goal,
    (SELECT role_cd FROM tb_role WHERE role_nm LIKE '%프론트%' OR role_nm LIKE '%개발%' LIMIT 1),
    ARRAY[(SELECT role_cd FROM tb_role WHERE role_nm LIKE '%UI%' OR role_nm LIKE '%UX%' LIMIT 1)],
    ARRAY['IT', '디자인'],                          -- interest_industries
    'startup',                                      -- preferred_company_size
    'remote',                                       -- preferred_work_style
    ARRAY['서울'],                                  -- preferred_regions
    FALSE,                                          -- resume_prepared
    TRUE,                                           -- portfolio_prepared
    FALSE,                                          -- interview_ready
    '프론트엔드 개발과 UI/UX에 관심',               -- career_notes
    'system',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE student_nm = '이영희'
ON CONFLICT (student_id) DO UPDATE SET
    primary_career_goal = EXCLUDED.primary_career_goal,
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 4. 역할(Role) 테스트 데이터 (기존에 없다면)
-- ============================================
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, ins_user_id, ins_dt)
VALUES
    ('ROLE_BE', '백엔드개발자', 'Backend Developer', 'IT개발', 'API, 서버, 데이터베이스 개발', 'system', CURRENT_TIMESTAMP),
    ('ROLE_FE', '프론트엔드개발자', 'Frontend Developer', 'IT개발', 'UI/UX, 웹 클라이언트 개발', 'system', CURRENT_TIMESTAMP),
    ('ROLE_FS', '풀스택개발자', 'Full-Stack Developer', 'IT개발', '프론트엔드 + 백엔드 개발', 'system', CURRENT_TIMESTAMP),
    ('ROLE_DA', '데이터분석가', 'Data Analyst', '데이터', '데이터 분석 및 인사이트 도출', 'system', CURRENT_TIMESTAMP),
    ('ROLE_PM', '프로젝트매니저', 'Project Manager', 'PM', '프로젝트 기획 및 관리', 'system', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO NOTHING;

-- ============================================
-- 5. 테스트 로그인 이력 데이터
-- ============================================
INSERT INTO tb_login_history (
    user_id, login_id, login_result, ip_address, device_type, attempted_at
)
SELECT
    user_id,
    login_id,
    'success',
    '127.0.0.1',
    'web',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
FROM tb_user
WHERE login_id IN ('admin', 'career_admin', 'student_hong')
ON CONFLICT DO NOTHING;

-- ============================================
-- 6. 데이터 확인 쿼리
-- ============================================
DO $$
DECLARE
    user_count INT;
    student_count INT;
    career_count INT;
BEGIN
    SELECT COUNT(*) INTO user_count FROM tb_user;
    SELECT COUNT(*) INTO student_count FROM tb_student;
    SELECT COUNT(*) INTO career_count FROM tb_student_career;

    RAISE NOTICE '======================================';
    RAISE NOTICE '테스트 데이터 INSERT 완료';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE '  - tb_user: % 건', user_count;
    RAISE NOTICE '  - tb_student: % 건', student_count;
    RAISE NOTICE '  - tb_student_career: % 건', career_count;
    RAISE NOTICE '======================================';
    RAISE NOTICE '';
    RAISE NOTICE '테스트 계정:';
    RAISE NOTICE '  admin / admin123 (시스템 관리자)';
    RAISE NOTICE '  career_admin / admin123 (취업지원센터)';
    RAISE NOTICE '  student_hong / student123 (학생)';
    RAISE NOTICE '  student_lee / student123 (학생)';
    RAISE NOTICE '  prof_kim / prof123 (교수)';
    RAISE NOTICE '======================================';
END $$;

-- ============================================
-- 7. 데이터 검증 쿼리 (선택적 실행)
-- ============================================
/*
-- 사용자 목록 확인
SELECT login_id, user_type, email, status, mfa_enabled
FROM tb_user ORDER BY ins_dt;

-- 학생-사용자 연결 확인
SELECT u.login_id, u.user_type, s.student_nm, s.career_goal
FROM tb_user u
LEFT JOIN tb_student s ON u.student_id = s.student_id
WHERE u.user_type = 'student';

-- 진로 정보 확인 (실제 스키마에 맞춤)
SELECT s.student_nm, sc.primary_career_goal, sc.interview_ready, r.role_nm
FROM tb_student_career sc
JOIN tb_student s ON sc.student_id = s.student_id
LEFT JOIN tb_role r ON sc.primary_role_cd = r.role_cd;

-- 통합 뷰 확인
SELECT student_nm, department_nm, career_goal, target_role_name, interview_ready
FROM vw_student_with_career
WHERE career_goal IS NOT NULL;
*/
