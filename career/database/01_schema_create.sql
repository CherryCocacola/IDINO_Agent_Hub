-- ============================================
-- IDINO Career Database Schema
-- Database: PostgreSQL 16
-- Schema: idino_career
-- Created: 2026-01-03
-- ============================================

-- Create Schema
CREATE SCHEMA IF NOT EXISTS idino_career;
SET search_path TO idino_career;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- Common Audit Column Comment
-- INS_* : Insert (?앹꽦) 愿???뺣낫
-- UPD_* : Update (?섏젙) 愿???뺣낫
-- ============================================

-- ============================================
-- 1. ?숆탳/?숆낵 留덉뒪???뚯씠釉?-- ============================================

-- ?숆탳 ?뺣낫
CREATE TABLE IF NOT EXISTS tb_university (
    university_cd VARCHAR(20) PRIMARY KEY,
    university_nm VARCHAR(100) NOT NULL,
    university_nm_en VARCHAR(100),
    address VARCHAR(500),
    phone VARCHAR(20),
    website VARCHAR(200),
    use_fg CHAR(1) DEFAULT 'Y',
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_university IS '?숆탳 ?뺣낫 留덉뒪??;
COMMENT ON COLUMN tb_university.university_cd IS '?숆탳 肄붾뱶';
COMMENT ON COLUMN tb_university.university_nm IS '?숆탳紐?;
COMMENT ON COLUMN tb_university.use_fg IS '?ъ슜?щ? (Y/N)';

-- ?④낵????뺣낫
CREATE TABLE IF NOT EXISTS tb_college (
    college_cd VARCHAR(20) PRIMARY KEY,
    university_cd VARCHAR(20) REFERENCES tb_university(university_cd),
    college_nm VARCHAR(100) NOT NULL,
    college_nm_en VARCHAR(100),
    use_fg CHAR(1) DEFAULT 'Y',
    sort_order INT DEFAULT 0,
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_college IS '?④낵????뺣낫 留덉뒪??;

-- ?숆낵 ?뺣낫
CREATE TABLE IF NOT EXISTS tb_department (
    department_cd VARCHAR(20) PRIMARY KEY,
    college_cd VARCHAR(20) REFERENCES tb_college(college_cd),
    department_nm VARCHAR(100) NOT NULL,
    department_nm_en VARCHAR(100),
    dept_type VARCHAR(20) DEFAULT 'major', -- major, minor, double_major
    graduation_credits INT DEFAULT 130,
    use_fg CHAR(1) DEFAULT 'Y',
    sort_order INT DEFAULT 0,
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_department IS '?숆낵 ?뺣낫 留덉뒪??;
COMMENT ON COLUMN tb_department.department_cd IS '?숆낵 肄붾뱶';
COMMENT ON COLUMN tb_department.graduation_credits IS '議몄뾽 ?댁닔?숈젏';

-- ============================================
-- 2. 援먯닔 ?뺣낫 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_professor (
    professor_cd VARCHAR(20) PRIMARY KEY,
    professor_nm VARCHAR(50) NOT NULL,
    professor_nm_en VARCHAR(100),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    email VARCHAR(100),
    phone VARCHAR(20),
    office_location VARCHAR(100),
    position VARCHAR(50), -- 援먯닔, 遺援먯닔, 議곌탳?? 媛뺤궗
    specialty VARCHAR(500),
    use_fg CHAR(1) DEFAULT 'Y',
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_professor IS '援먯닔 ?뺣낫 留덉뒪??;

-- ============================================
-- 3. 怨쇰ぉ ?뺣낫 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_course (
    course_cd VARCHAR(20) PRIMARY KEY,
    course_nm VARCHAR(200) NOT NULL,
    course_nm_en VARCHAR(200),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    credits INT NOT NULL DEFAULT 3,
    course_type VARCHAR(20) NOT NULL, -- ?꾧났?꾩닔, ?꾧났?좏깮, 援먯뼇?꾩닔, 援먯뼇?좏깮, ?쇰컲?좏깮
    course_category VARCHAR(50), -- 湲곗큹, ?ы솕, ?묒슜, ?ㅼ뒿
    grade_level INT, -- 1,2,3,4 ?숇뀈 沅뚯옣
    description TEXT,
    use_fg CHAR(1) DEFAULT 'Y',
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_course IS '怨쇰ぉ ?뺣낫 留덉뒪??;
COMMENT ON COLUMN tb_course.course_type IS '?댁닔援щ텇 (?꾧났?꾩닔/?꾧났?좏깮/援먯뼇?꾩닔/援먯뼇?좏깮/?쇰컲?좏깮)';

-- ?좎닔怨쇰ぉ ?뺣낫
CREATE TABLE IF NOT EXISTS tb_prerequisite (
    prerequisite_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    prerequisite_course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    prerequisite_type VARCHAR(20) DEFAULT 'required', -- required, recommended
    -- Audit Columns
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
    UNIQUE(course_cd, prerequisite_course_cd)
);

COMMENT ON TABLE tb_prerequisite IS '?좎닔怨쇰ぉ ?뺣낫';

-- 援먯닔-?대떦怨쇰ぉ 留ㅽ븨
CREATE TABLE IF NOT EXISTS tb_professor_course (
    professor_course_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    is_primary CHAR(1) DEFAULT 'Y',
    -- Audit Columns
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
    UNIQUE(professor_cd, course_cd)
);

COMMENT ON TABLE tb_professor_course IS '援먯닔-?대떦怨쇰ぉ 留ㅽ븨';

-- ============================================
-- 4. ?숈깮 ?뺣낫 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_student (
    student_id VARCHAR(20) PRIMARY KEY,
    student_nm VARCHAR(50) NOT NULL,
    student_nm_en VARCHAR(100),
    university_cd VARCHAR(20) REFERENCES tb_university(university_cd),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    admission_year INT NOT NULL,
    current_grade INT NOT NULL CHECK (current_grade BETWEEN 1 AND 4),
    current_semester INT NOT NULL CHECK (current_semester BETWEEN 1 AND 8),
    email VARCHAR(100),
    phone VARCHAR(20),
    birth_date DATE,
    gender CHAR(1), -- M, F
    status VARCHAR(20) DEFAULT 'enrolled', -- enrolled, leave, graduated, expelled
    career_goal VARCHAR(200),
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_student IS '?숈깮 ?뺣낫';
COMMENT ON COLUMN tb_student.student_id IS '?숇쾲';
COMMENT ON COLUMN tb_student.career_goal IS '?щ쭩 吏꾨줈';

-- ============================================
-- 5. ?숆린 ?뺣낫 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_term (
    term_cd VARCHAR(10) PRIMARY KEY, -- ?? 2025-1, 2025-2
    term_nm VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    registration_start DATE,
    registration_end DATE,
    use_fg CHAR(1) DEFAULT 'Y',
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_term IS '?숆린 ?뺣낫';

-- ============================================
-- 6. 媛쒖꽕媛뺤쥖 ?뺣낫 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_course_offering (
    offering_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),
    class_no INT DEFAULT 1, -- 遺꾨컲
    capacity INT DEFAULT 40,
    enrolled_count INT DEFAULT 0,
    schedule VARCHAR(200), -- ?? "??,4 ??,4"
    classroom VARCHAR(100),
    use_fg CHAR(1) DEFAULT 'Y',
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_course_offering IS '媛쒖꽕媛뺤쥖 ?뺣낫';

-- ============================================
-- 7. ?섍컯?좎껌 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_enrollment (
    enrollment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    offering_id UUID REFERENCES tb_course_offering(offering_id),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    status VARCHAR(20) DEFAULT 'enrolled', -- enrolled, dropped, completed
    -- Audit Columns
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
    UNIQUE(student_id, offering_id)
);

COMMENT ON TABLE tb_enrollment IS '?섍컯?좎껌 ?뺣낫';

-- ============================================
-- 8. ?깆쟻 ?뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_grade (
    grade_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enrollment_id UUID REFERENCES tb_enrollment(enrollment_id),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    grade_letter VARCHAR(5), -- A+, A0, B+, B0, C+, C0, D+, D0, F, P, NP
    grade_point DECIMAL(3,2), -- 4.50, 4.00, 3.50, ...
    credits_earned INT,
    is_retake CHAR(1) DEFAULT 'N',
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_grade IS '?깆쟻 ?뺣낫';

-- ?숆린蹂??깆쟻 ?붿빟
CREATE TABLE IF NOT EXISTS tb_grade_summary (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    total_credits INT DEFAULT 0,
    earned_credits INT DEFAULT 0,
    gpa DECIMAL(3,2) DEFAULT 0.00,
    major_gpa DECIMAL(3,2) DEFAULT 0.00,
    class_rank INT,
    total_students INT,
    -- Audit Columns
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
    UNIQUE(student_id, term_cd)
);

COMMENT ON TABLE tb_grade_summary IS '?숆린蹂??깆쟻 ?붿빟';

-- ?꾩쟻 ?깆쟻 ?붿빟
CREATE TABLE IF NOT EXISTS tb_cumulative_summary (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id) UNIQUE,
    total_credits_required INT DEFAULT 130,
    total_credits_earned INT DEFAULT 0,
    major_credits_required INT DEFAULT 60,
    major_credits_earned INT DEFAULT 0,
    liberal_credits_required INT DEFAULT 30,
    liberal_credits_earned INT DEFAULT 0,
    cumulative_gpa DECIMAL(3,2) DEFAULT 0.00,
    major_gpa DECIMAL(3,2) DEFAULT 0.00,
    completion_rate DECIMAL(5,2) DEFAULT 0.00,
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_system_gcd VARCHAR(10),
    ins_menu_cd VARCHAR(20),
    upd_user_id VARCHAR(50),
    upd_user_ip VARCHAR(50),
    upd_dt TIMESTAMP,
    upd_system_gcd VARCHAR(10),
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_cumulative_summary IS '?꾩쟻 ?깆쟻 ?붿빟';

-- ============================================
-- Indexes
-- ============================================

CREATE INDEX idx_student_department ON tb_student(department_cd);
CREATE INDEX idx_student_status ON tb_student(status);
CREATE INDEX idx_enrollment_student ON tb_enrollment(student_id);
CREATE INDEX idx_enrollment_term ON tb_enrollment(term_cd);
CREATE INDEX idx_grade_student ON tb_grade(student_id);
CREATE INDEX idx_grade_term ON tb_grade(term_cd);
CREATE INDEX idx_course_department ON tb_course(department_cd);
CREATE INDEX idx_professor_department ON tb_professor(department_cd);
