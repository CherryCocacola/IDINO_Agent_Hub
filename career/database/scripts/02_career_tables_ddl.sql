-- ============================================
-- 02. Career 데이터 분리 테이블 DDL
-- ============================================
-- 주의: 이 스크립트는 migration_001_auth_and_career.sql 이후에
--       추가 변경이 필요한 경우에만 실행하세요.
--       tb_student_career, tb_career_history는 이미 migration_001에서 생성됨
--
-- 실행 전: migration_001_auth_and_career.sql 먼저 실행 필요
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. 학생 진로 정보 테이블 (migration_001에서 이미 생성됨)
-- ============================================
-- 참고용: 실제 스키마 정의 (CREATE는 migration_001에서 완료)
/*
CREATE TABLE IF NOT EXISTS tb_student_career (
    career_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL REFERENCES tb_student(student_id) ON DELETE CASCADE,

    -- 희망 진로 (Primary)
    primary_career_goal VARCHAR(200),
    primary_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),

    -- 관심 직무 (Multiple)
    interest_role_cds VARCHAR(20)[],
    interest_industries VARCHAR(100)[],             -- 관심 산업

    -- 선호도
    preferred_company_size VARCHAR(20) CHECK (preferred_company_size IN ('startup', 'sme', 'midsize', 'large', 'any')),
    preferred_work_style VARCHAR(20) CHECK (preferred_work_style IN ('office', 'remote', 'hybrid', 'any')),
    preferred_regions VARCHAR(50)[],                -- 선호 지역

    -- 준비 상태
    resume_prepared BOOLEAN DEFAULT FALSE,
    portfolio_prepared BOOLEAN DEFAULT FALSE,
    interview_ready BOOLEAN DEFAULT FALSE,

    -- 타임라인
    job_search_start_date DATE,
    target_employment_date DATE,

    -- 추가 정보
    career_notes TEXT,
    advisor_comments TEXT,

    -- 마지막 상담
    last_counseling_date DATE,
    next_counseling_date DATE,

    -- Audit
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20),

    UNIQUE(student_id)
);
*/

COMMENT ON TABLE tb_student_career IS '학생 진로 정보 테이블 - tb_student에서 career_goal 분리';
COMMENT ON COLUMN tb_student_career.primary_career_goal IS '기존 tb_student.career_goal에서 이전된 데이터';
COMMENT ON COLUMN tb_student_career.interest_role_cds IS '관심 있는 직무 코드 배열 (복수 선택)';
COMMENT ON COLUMN tb_student_career.interest_industries IS '관심 산업 분야 배열';
COMMENT ON COLUMN tb_student_career.preferred_regions IS '선호 근무 지역 배열';

-- 인덱스 (IF NOT EXISTS로 중복 방지)
CREATE INDEX IF NOT EXISTS idx_student_career_student_id ON tb_student_career(student_id);
CREATE INDEX IF NOT EXISTS idx_student_career_primary_role ON tb_student_career(primary_role_cd);

-- ============================================
-- 2. 진로 목표 변경 이력 테이블 (migration_001에서 이미 생성됨)
-- ============================================
-- 참고용: 실제 스키마 정의
/*
CREATE TABLE IF NOT EXISTS tb_career_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL REFERENCES tb_student(student_id) ON DELETE CASCADE,

    -- 변경 전후
    previous_career_goal VARCHAR(200),
    new_career_goal VARCHAR(200),
    previous_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    new_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),

    -- 변경 사유
    change_reason TEXT,
    triggered_by VARCHAR(50),                       -- 'student', 'advisor', 'system'

    -- 시간
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
*/

COMMENT ON TABLE tb_career_history IS '진로 목표 변경 이력 테이블 - 상담 및 분석용';
COMMENT ON COLUMN tb_career_history.triggered_by IS '변경 계기: student(본인), advisor(상담), system(시스템)';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_career_history_student_id ON tb_career_history(student_id);
CREATE INDEX IF NOT EXISTS idx_career_history_changed_at ON tb_career_history(changed_at);

-- ============================================
-- 3. 뷰 생성 (기존 뷰 대체)
-- ============================================

-- 학생 정보 + 진로 정보 통합 뷰 (하위 호환성)
CREATE OR REPLACE VIEW vw_student_with_career AS
SELECT
    s.student_id,
    s.student_nm,
    s.university_cd,
    s.department_cd,
    d.department_nm,
    s.admission_year,
    s.current_grade,
    s.current_semester,
    s.email,
    s.phone,
    s.status,
    -- Career 정보 (tb_student_career에서)
    sc.primary_career_goal AS career_goal,
    sc.primary_role_cd,
    r.role_nm AS target_role_name,
    sc.interest_role_cds,
    sc.interest_industries,
    sc.preferred_company_size,
    sc.preferred_work_style,
    sc.preferred_regions,
    sc.resume_prepared,
    sc.portfolio_prepared,
    sc.interview_ready,
    sc.job_search_start_date,
    sc.target_employment_date,
    sc.career_notes,
    sc.last_counseling_date,
    sc.next_counseling_date
FROM tb_student s
LEFT JOIN tb_department d ON s.department_cd = d.department_cd
LEFT JOIN tb_student_career sc ON s.student_id = sc.student_id
LEFT JOIN tb_role r ON sc.primary_role_cd = r.role_cd;

COMMENT ON VIEW vw_student_with_career IS '학생 기본정보와 진로정보를 통합한 뷰 (하위 호환성)';

-- 사용자 인증 정보 뷰
CREATE OR REPLACE VIEW vw_user_auth_info AS
SELECT
    u.user_id,
    u.login_id,
    u.user_type,
    u.email,
    u.status,
    u.mfa_enabled,
    u.mfa_type,
    u.last_login_at,
    u.failed_login_count,
    u.locked_until,
    -- 연결된 학생/교수 정보
    CASE
        WHEN u.user_type IN ('student') THEN s.student_nm
        WHEN u.user_type IN ('professor', 'advisor') THEN p.professor_nm
        ELSE u.login_id
    END AS user_nm,
    CASE
        WHEN u.user_type IN ('student') THEN d1.department_nm
        WHEN u.user_type IN ('professor', 'advisor') THEN d2.department_nm
        ELSE NULL
    END AS department_nm
FROM tb_user u
LEFT JOIN tb_student s ON u.student_id = s.student_id
LEFT JOIN tb_professor p ON u.professor_cd = p.professor_cd
LEFT JOIN tb_department d1 ON s.department_cd = d1.department_cd
LEFT JOIN tb_department d2 ON p.department_cd = d2.department_cd;

COMMENT ON VIEW vw_user_auth_info IS '사용자 인증 정보와 연결된 학생/교수 정보 통합 뷰';

-- ============================================
-- 4. 함수: 진로 목표 변경 시 자동 이력 기록
-- ============================================
CREATE OR REPLACE FUNCTION fn_log_career_change()
RETURNS TRIGGER AS $$
BEGIN
    -- 진로 목표가 변경된 경우만 이력 기록
    IF OLD.primary_career_goal IS DISTINCT FROM NEW.primary_career_goal
       OR OLD.primary_role_cd IS DISTINCT FROM NEW.primary_role_cd THEN

        INSERT INTO tb_career_history (
            student_id,
            previous_career_goal,
            new_career_goal,
            previous_role_cd,
            new_role_cd,
            triggered_by,
            ins_user_id
        ) VALUES (
            NEW.student_id,
            OLD.primary_career_goal,
            NEW.primary_career_goal,
            OLD.primary_role_cd,
            NEW.primary_role_cd,
            'system',
            NEW.upd_user_id
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
DROP TRIGGER IF EXISTS trg_career_change ON tb_student_career;
CREATE TRIGGER trg_career_change
AFTER UPDATE ON tb_student_career
FOR EACH ROW
EXECUTE FUNCTION fn_log_career_change();

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '======================================';
    RAISE NOTICE 'Career 데이터 보조 스크립트 완료';
    RAISE NOTICE '- COMMENT 추가';
    RAISE NOTICE '- 인덱스 생성 (IF NOT EXISTS)';
    RAISE NOTICE '- vw_student_with_career 뷰 갱신';
    RAISE NOTICE '- vw_user_auth_info 뷰 갱신';
    RAISE NOTICE '- fn_log_career_change 함수/트리거';
    RAISE NOTICE '======================================';
END $$;
