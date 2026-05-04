-- ============================================
-- IDINO Career Database - Complete DDL
-- Database: PostgreSQL 16
-- Schema: idino_career
-- Encoding: UTF-8 (No BOM)
-- Created: 2026-01-08
-- ============================================

-- Create Schema
DROP SCHEMA IF EXISTS idino_career CASCADE;
CREATE SCHEMA idino_career;
SET search_path TO idino_career;

-- Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 1. MASTER DATA TABLES
-- ============================================

-- University
CREATE TABLE tb_university (
    university_cd VARCHAR(20) PRIMARY KEY,
    university_nm VARCHAR(100) NOT NULL,
    university_nm_en VARCHAR(100),
    address VARCHAR(500),
    phone VARCHAR(20),
    website VARCHAR(200),
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_user_ip VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- College
CREATE TABLE tb_college (
    college_cd VARCHAR(20) PRIMARY KEY,
    university_cd VARCHAR(20) REFERENCES tb_university(university_cd),
    college_nm VARCHAR(100) NOT NULL,
    college_nm_en VARCHAR(100),
    use_fg CHAR(1) DEFAULT 'Y',
    sort_order INT DEFAULT 0,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Department
CREATE TABLE tb_department (
    department_cd VARCHAR(20) PRIMARY KEY,
    college_cd VARCHAR(20) REFERENCES tb_college(college_cd),
    department_nm VARCHAR(100) NOT NULL,
    department_nm_en VARCHAR(100),
    dept_type VARCHAR(20) DEFAULT 'major',
    graduation_credits INT DEFAULT 130,
    use_fg CHAR(1) DEFAULT 'Y',
    sort_order INT DEFAULT 0,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Professor
CREATE TABLE tb_professor (
    professor_cd VARCHAR(20) PRIMARY KEY,
    professor_nm VARCHAR(50) NOT NULL,
    professor_nm_en VARCHAR(100),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    email VARCHAR(100),
    phone VARCHAR(20),
    office_location VARCHAR(100),
    position VARCHAR(50),
    specialty VARCHAR(500),
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Term (Semester)
CREATE TABLE tb_term (
    term_cd VARCHAR(10) PRIMARY KEY,
    term_nm VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    registration_start DATE,
    registration_end DATE,
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Course
CREATE TABLE tb_course (
    course_cd VARCHAR(20) PRIMARY KEY,
    course_nm VARCHAR(200) NOT NULL,
    course_nm_en VARCHAR(200),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    credits INT NOT NULL DEFAULT 3,
    course_type VARCHAR(20) NOT NULL,
    course_category VARCHAR(50),
    grade_level INT,
    description TEXT,
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Prerequisite
CREATE TABLE tb_prerequisite (
    prerequisite_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    prerequisite_course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    prerequisite_type VARCHAR(20) DEFAULT 'required',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_cd, prerequisite_course_cd)
);

-- Professor-Course Mapping
CREATE TABLE tb_professor_course (
    professor_course_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    is_primary CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professor_cd, course_cd)
);

-- ============================================
-- 2. STUDENT DATA TABLES
-- ============================================

-- Student
CREATE TABLE tb_student (
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
    gender CHAR(1),
    status VARCHAR(20) DEFAULT 'enrolled',
    career_goal VARCHAR(200),
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Course Offering
CREATE TABLE tb_course_offering (
    offering_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),
    class_no INT DEFAULT 1,
    capacity INT DEFAULT 40,
    enrolled_count INT DEFAULT 0,
    schedule VARCHAR(200),
    classroom VARCHAR(100),
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Enrollment
CREATE TABLE tb_enrollment (
    enrollment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    offering_id UUID REFERENCES tb_course_offering(offering_id),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    status VARCHAR(20) DEFAULT 'enrolled',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(student_id, offering_id)
);

-- Grade
CREATE TABLE tb_grade (
    grade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID REFERENCES tb_enrollment(enrollment_id),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    grade_letter VARCHAR(5),
    grade_point DECIMAL(3,2),
    credits_earned INT,
    is_retake CHAR(1) DEFAULT 'N',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Grade Summary (per term)
CREATE TABLE tb_grade_summary (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    total_credits INT DEFAULT 0,
    earned_credits INT DEFAULT 0,
    gpa DECIMAL(3,2) DEFAULT 0.00,
    major_gpa DECIMAL(3,2) DEFAULT 0.00,
    class_rank INT,
    total_students INT,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(student_id, term_cd)
);

-- Cumulative Summary
CREATE TABLE tb_cumulative_summary (
    summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- ============================================
-- 3. COMPETENCY & SKILL TABLES
-- ============================================

-- Competency Definition
CREATE TABLE tb_competency (
    competency_cd VARCHAR(20) PRIMARY KEY,
    competency_nm VARCHAR(100) NOT NULL,
    competency_nm_en VARCHAR(100),
    definition TEXT,
    category VARCHAR(50),
    weight DECIMAL(5,2) DEFAULT 0,
    max_score INT DEFAULT 100,
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Skill Definition
CREATE TABLE tb_skill (
    skill_cd VARCHAR(20) PRIMARY KEY,
    skill_nm VARCHAR(100) NOT NULL,
    skill_nm_en VARCHAR(100),
    synonyms TEXT[],
    category VARCHAR(50),
    difficulty INT CHECK (difficulty BETWEEN 1 AND 5),
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Skill-Competency Mapping
CREATE TABLE tb_skill_competency_map (
    map_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_cd VARCHAR(20) REFERENCES tb_skill(skill_cd),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    weight DECIMAL(5,2) DEFAULT 1.0,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(skill_cd, competency_cd)
);

-- Course-Competency Mapping
CREATE TABLE tb_course_competency_map (
    map_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    contribution_weight DECIMAL(5,2) NOT NULL,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_cd, competency_cd)
);

-- Student Competency Status
CREATE TABLE tb_student_competency (
    student_competency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    current_score DECIMAL(5,2) DEFAULT 0,
    target_score DECIMAL(5,2) DEFAULT 85,
    gap_score DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'improve',
    last_assessment_date DATE,
    trend VARCHAR(10) DEFAULT 'stable',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(student_id, competency_cd)
);

-- ============================================
-- 4. ACTIVITY & ACHIEVEMENT TABLES
-- ============================================

-- Program (Non-curricular)
CREATE TABLE tb_program (
    program_cd VARCHAR(20) PRIMARY KEY,
    program_nm VARCHAR(200) NOT NULL,
    program_type VARCHAR(50) NOT NULL,
    organizer VARCHAR(200),
    start_date DATE,
    end_date DATE,
    description TEXT,
    competency_contributions JSONB,
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Activity
CREATE TABLE tb_activity (
    activity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    program_cd VARCHAR(20) REFERENCES tb_program(program_cd),
    activity_type VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    description TEXT,
    start_date DATE,
    end_date DATE,
    hours DECIMAL(6,1),
    achievement TEXT,
    status VARCHAR(20) DEFAULT 'completed',
    verified CHAR(1) DEFAULT 'N',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Achievement
CREATE TABLE tb_achievement (
    achievement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    achievement_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    issuer VARCHAR(200),
    issue_date DATE,
    expire_date DATE,
    level VARCHAR(50),
    score VARCHAR(50),
    competency_contributions JSONB,
    verified CHAR(1) DEFAULT 'N',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- ============================================
-- 5. JOB & ALUMNI TABLES
-- ============================================

-- Role (Job/Career)
CREATE TABLE tb_role (
    role_cd VARCHAR(20) PRIMARY KEY,
    role_nm VARCHAR(100) NOT NULL,
    role_nm_en VARCHAR(100),
    category VARCHAR(50),
    description TEXT,
    average_salary DECIMAL(12,0),
    growth_rate DECIMAL(5,2),
    required_competencies JSONB,
    required_skills JSONB,
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Alumni Cohort
CREATE TABLE tb_alumni_cohort (
    cohort_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    graduation_year INT NOT NULL,
    cohort_size INT,
    avg_gpa DECIMAL(3,2),
    employment_rate DECIMAL(5,2),
    avg_salary DECIMAL(12,0),
    top_employers VARCHAR(500)[],
    top_roles VARCHAR(100)[],
    avg_competency_scores JSONB,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(department_cd, graduation_year)
);

-- Success Pattern
CREATE TABLE tb_success_pattern (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_nm VARCHAR(100) NOT NULL,
    pattern_type VARCHAR(50),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    description TEXT,
    typical_gpa_range VARCHAR(20),
    key_courses VARCHAR(20)[],
    key_activities VARCHAR(200)[],
    key_skills VARCHAR(20)[],
    timeline JSONB,
    success_rate DECIMAL(5,2),
    sample_size INT,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- ============================================
-- 6. AUTH TABLES
-- ============================================

-- User
CREATE TABLE tb_user (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    login_id VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    user_nm VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    user_type VARCHAR(20) DEFAULT 'student',
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),
    role VARCHAR(20) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'active',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(100),
    last_login TIMESTAMP,
    login_fail_count INT DEFAULT 0,
    locked_until TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Session
CREATE TABLE tb_user_session (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES tb_user(user_id),
    refresh_token VARCHAR(500),
    device_info VARCHAR(500),
    ip_address VARCHAR(50),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. AI OPERATIONS TABLES
-- ============================================

-- Recommendation Run
CREATE TABLE tb_recommendation_run (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    run_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(50),
    prompt_tokens INT,
    completion_tokens INT,
    latency_ms INT,
    status VARCHAR(20) DEFAULT 'completed',
    error_message TEXT,
    context_data JSONB,
    run_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommendation Item
CREATE TABLE tb_recommendation_item (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES tb_recommendation_run(run_id),
    item_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    priority VARCHAR(20),
    target_competency VARCHAR(20),
    reasoning TEXT,
    confidence_score DECIMAL(3,2),
    deadline VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Eval Feedback
CREATE TABLE tb_eval_feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES tb_recommendation_run(run_id),
    item_id UUID REFERENCES tb_recommendation_item(item_id),
    user_id UUID REFERENCES tb_user(user_id),
    feedback_type VARCHAR(20) NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    is_helpful BOOLEAN,
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. P1/P2 EXTENSION TABLES
-- ============================================

-- Role-Skill Mapping (Skill Graph)
CREATE TABLE tb_role_skill_map (
    map_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    skill_cd VARCHAR(20) REFERENCES tb_skill(skill_cd),
    required_level INT NOT NULL CHECK (required_level BETWEEN 1 AND 5),
    importance VARCHAR(15) NOT NULL CHECK (importance IN ('critical', 'important', 'nice_to_have')),
    market_demand_score DECIMAL(5,2),
    growth_trend VARCHAR(20) DEFAULT 'stable',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_cd, skill_cd)
);

-- Student Skill
CREATE TABLE tb_student_skill (
    student_skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    skill_cd VARCHAR(20) REFERENCES tb_skill(skill_cd),
    current_level INT DEFAULT 1 CHECK (current_level BETWEEN 1 AND 5),
    target_level INT DEFAULT 3 CHECK (target_level BETWEEN 1 AND 5),
    evidence_count INT DEFAULT 0,
    last_verified_date DATE,
    verification_source VARCHAR(50),
    trend VARCHAR(10) DEFAULT 'stable',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(student_id, skill_cd)
);

-- Skill Gap Analysis
CREATE TABLE tb_skill_gap_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    target_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_gap_score DECIMAL(5,2),
    gap_details JSONB NOT NULL,
    top_priority_skills VARCHAR(20)[],
    recommended_actions JSONB,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill Relation (Graph edges)
CREATE TABLE tb_skill_relation (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_cd_from VARCHAR(20) REFERENCES tb_skill(skill_cd),
    skill_cd_to VARCHAR(20) REFERENCES tb_skill(skill_cd),
    relation_type VARCHAR(30) NOT NULL,
    strength DECIMAL(3,2) DEFAULT 1.0,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(skill_cd_from, skill_cd_to, relation_type)
);

-- Opportunity
CREATE TABLE tb_opportunity (
    opportunity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_type VARCHAR(30) NOT NULL,
    title VARCHAR(300) NOT NULL,
    organization VARCHAR(200),
    description TEXT,
    requirements JSONB,
    benefits JSONB,
    application_start DATE,
    application_end DATE,
    start_date DATE,
    end_date DATE,
    location VARCHAR(200),
    remote_available BOOLEAN DEFAULT FALSE,
    slots INT,
    status VARCHAR(20) DEFAULT 'open',
    external_url TEXT,
    tags VARCHAR(50)[],
    department_cds VARCHAR(20)[],
    competency_contributions JSONB,
    skill_contributions JSONB,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Opportunity Recommendation
CREATE TABLE tb_opportunity_recommendation (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    opportunity_id UUID REFERENCES tb_opportunity(opportunity_id),
    match_score DECIMAL(5,2) NOT NULL,
    match_reasons JSONB,
    status VARCHAR(20) DEFAULT 'recommended',
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, opportunity_id)
);

-- Opportunity Application
CREATE TABLE tb_opportunity_application (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    opportunity_id UUID REFERENCES tb_opportunity(opportunity_id),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'submitted',
    cover_letter TEXT,
    attachments JSONB,
    reviewer_notes TEXT,
    decision_at TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Coaching Goal
CREATE TABLE tb_coaching_goal (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    goal_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    target_metrics JSONB,
    current_metrics JSONB,
    deadline DATE,
    priority INT DEFAULT 1,
    status VARCHAR(20) DEFAULT 'active',
    achievement_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    achieved_at TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Coaching Plan
CREATE TABLE tb_coaching_plan (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id),
    plan_version INT DEFAULT 1,
    milestones JSONB NOT NULL,
    weekly_hours_target DECIMAL(4,1) DEFAULT 10,
    current_week INT DEFAULT 1,
    total_weeks INT,
    ai_generated BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Coaching Checkin
CREATE TABLE tb_coaching_checkin (
    checkin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES tb_coaching_plan(plan_id),
    week_number INT NOT NULL,
    checkin_date DATE NOT NULL,
    completed_tasks JSONB,
    hours_spent DECIMAL(4,1),
    blockers TEXT,
    wins TEXT,
    mood_score INT CHECK (mood_score BETWEEN 1 AND 5),
    ai_feedback TEXT,
    ai_suggestions JSONB,
    progress_score DECIMAL(5,2),
    on_track BOOLEAN,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Coaching Retrospective
CREATE TABLE tb_coaching_retrospective (
    retrospective_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    what_went_well TEXT,
    what_could_improve TEXT,
    lessons_learned TEXT,
    initial_metrics JSONB,
    final_metrics JSONB,
    improvement_percentage DECIMAL(5,2),
    ai_summary TEXT,
    ai_insights JSONB,
    next_period_recommendations JSONB,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk Alert
CREATE TABLE tb_risk_alert (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    risk_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    trigger_value DECIMAL(10,2),
    threshold_value DECIMAL(10,2),
    related_entity_type VARCHAR(50),
    related_entity_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Prerequisite Rule
CREATE TABLE tb_prerequisite_rule (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    prerequisite_type VARCHAR(30) NOT NULL,
    condition_expr JSONB NOT NULL,
    error_message VARCHAR(500),
    is_strict BOOLEAN DEFAULT TRUE,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Badge
CREATE TABLE tb_badge (
    badge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    badge_cd VARCHAR(20) UNIQUE NOT NULL,
    badge_nm VARCHAR(100) NOT NULL,
    badge_nm_en VARCHAR(100),
    description TEXT,
    category VARCHAR(50) NOT NULL,
    level VARCHAR(20),
    icon_url VARCHAR(500),
    criteria JSONB NOT NULL,
    points INT DEFAULT 0,
    is_stackable BOOLEAN DEFAULT FALSE,
    use_fg CHAR(1) DEFAULT 'Y',
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Student Badge
CREATE TABLE tb_student_badge (
    student_badge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    badge_id UUID REFERENCES tb_badge(badge_id),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    earned_level INT DEFAULT 1,
    evidence JSONB,
    verified_by VARCHAR(50),
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, badge_id, earned_level)
);

-- Skill Passport
CREATE TABLE tb_skill_passport (
    passport_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id) UNIQUE,
    overall_score DECIMAL(5,2) DEFAULT 0,
    total_badges INT DEFAULT 0,
    total_skills INT DEFAULT 0,
    verified_skills INT DEFAULT 0,
    passport_data JSONB,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    public_share_url VARCHAR(500),
    is_public BOOLEAN DEFAULT FALSE,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Simulation Scenario
CREATE TABLE tb_simulation_scenario (
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    scenario_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    base_state JSONB NOT NULL,
    changes JSONB NOT NULL,
    predicted_outcomes JSONB,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_favorite BOOLEAN DEFAULT FALSE,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Scenario Comparison
CREATE TABLE tb_scenario_comparison (
    comparison_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    scenario_ids UUID[] NOT NULL,
    comparison_metrics JSONB NOT NULL,
    recommendation TEXT,
    ai_analysis JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Advisor
CREATE TABLE tb_advisor (
    advisor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_cd VARCHAR(20) UNIQUE NOT NULL,
    advisor_nm VARCHAR(50) NOT NULL,
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    email VARCHAR(100),
    phone VARCHAR(20),
    max_students INT DEFAULT 30,
    specialties VARCHAR(100)[],
    availability JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Advisor Assignment
CREATE TABLE tb_advisor_assignment (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_id UUID REFERENCES tb_advisor(advisor_id),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assignment_type VARCHAR(30) DEFAULT 'academic',
    status VARCHAR(20) DEFAULT 'active',
    priority INT DEFAULT 2,
    notes TEXT,
    last_contact TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    UNIQUE(advisor_id, student_id, assignment_type)
);

-- Advisor Intervention
CREATE TABLE tb_advisor_intervention (
    intervention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID REFERENCES tb_advisor_assignment(assignment_id),
    intervention_type VARCHAR(50) NOT NULL,
    trigger_alert_id UUID REFERENCES tb_risk_alert(alert_id),
    scheduled_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'scheduled',
    notes TEXT,
    outcome TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Advisor Note
CREATE TABLE tb_advisor_note (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID REFERENCES tb_advisor_assignment(assignment_id),
    note_type VARCHAR(30) NOT NULL,
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Cohort Snapshot
CREATE TABLE tb_cohort_snapshot (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    snapshot_date DATE NOT NULL,
    grade_level INT CHECK (grade_level BETWEEN 1 AND 4),
    total_students INT,
    at_risk_count INT,
    avg_gpa DECIMAL(3,2),
    avg_completion_rate DECIMAL(5,2),
    risk_distribution JSONB,
    competency_distribution JSONB,
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_cd, snapshot_date, grade_level)
);

-- ============================================
-- 9. INDEXES
-- ============================================

CREATE INDEX idx_student_department ON tb_student(department_cd);
CREATE INDEX idx_student_status ON tb_student(status);
CREATE INDEX idx_enrollment_student ON tb_enrollment(student_id);
CREATE INDEX idx_enrollment_term ON tb_enrollment(term_cd);
CREATE INDEX idx_grade_student ON tb_grade(student_id);
CREATE INDEX idx_grade_term ON tb_grade(term_cd);
CREATE INDEX idx_course_department ON tb_course(department_cd);
CREATE INDEX idx_professor_department ON tb_professor(department_cd);
CREATE INDEX idx_student_competency_student ON tb_student_competency(student_id);
CREATE INDEX idx_student_skill_student ON tb_student_skill(student_id);
CREATE INDEX idx_activity_student ON tb_activity(student_id);
CREATE INDEX idx_achievement_student ON tb_achievement(student_id);
CREATE INDEX idx_risk_alert_student ON tb_risk_alert(student_id);
CREATE INDEX idx_risk_alert_status ON tb_risk_alert(status);
CREATE INDEX idx_coaching_goal_student ON tb_coaching_goal(student_id);
CREATE INDEX idx_opportunity_status ON tb_opportunity(status);
CREATE INDEX idx_student_badge_student ON tb_student_badge(student_id);
CREATE INDEX idx_advisor_assignment_student ON tb_advisor_assignment(student_id);
CREATE INDEX idx_user_login_id ON tb_user(login_id);
CREATE INDEX idx_recommendation_run_student ON tb_recommendation_run(student_id);

-- ============================================
-- DONE
-- ============================================
