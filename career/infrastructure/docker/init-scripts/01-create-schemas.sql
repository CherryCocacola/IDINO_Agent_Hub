-- ============================================
-- IDINO Career System - Schema Initialization
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================
-- Create Schemas
-- ============================================

CREATE SCHEMA IF NOT EXISTS idino_career_auth;
CREATE SCHEMA IF NOT EXISTS idino_career_student;
CREATE SCHEMA IF NOT EXISTS idino_career_competency;
CREATE SCHEMA IF NOT EXISTS idino_career_roadmap;
CREATE SCHEMA IF NOT EXISTS idino_career_alumni;
CREATE SCHEMA IF NOT EXISTS idino_career_ai;
CREATE SCHEMA IF NOT EXISTS idino_career_integration;

-- ============================================
-- Grant permissions
-- ============================================

GRANT ALL PRIVILEGES ON SCHEMA idino_career_auth TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA idino_career_student TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA idino_career_competency TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA idino_career_roadmap TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA idino_career_alumni TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA idino_career_ai TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA idino_career_integration TO postgres;

-- ============================================
-- AUTH SCHEMA - Minimal (uses Redis primarily)
-- ============================================

SET search_path TO idino_career_auth;

CREATE TABLE IF NOT EXISTS tb_users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_level INTEGER NOT NULL DEFAULT 5,  -- 1: Admin, 2: PM, 3: Faculty, 4: Staff, 5: Student
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tb_user_profiles (
    user_id UUID PRIMARY KEY REFERENCES tb_users(user_id),
    student_id VARCHAR(20) UNIQUE,  -- For student users
    department_id VARCHAR(20),
    name VARCHAR(100),
    phone VARCHAR(20),
    profile_image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- STUDENT SCHEMA
-- ============================================

SET search_path TO idino_career_student;

-- Department/Major definitions
CREATE TABLE IF NOT EXISTS tb_departments (
    department_id VARCHAR(20) PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    college VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student basic info
CREATE TABLE IF NOT EXISTS tb_students (
    student_id VARCHAR(20) PRIMARY KEY,
    user_id UUID,  -- Reference to auth schema
    name VARCHAR(100) NOT NULL,
    department_id VARCHAR(20) REFERENCES tb_departments(department_id),
    major VARCHAR(100),
    grade INTEGER CHECK (grade BETWEEN 1 AND 6),  -- 1-4 학부, 5-6 대학원
    total_credits INTEGER DEFAULT 0,
    gpa DECIMAL(3,2) DEFAULT 0.00,
    career_goal TEXT,
    target_job_codes JSONB DEFAULT '[]'::JSONB,
    enrollment_year INTEGER,
    enrollment_semester INTEGER,  -- 1: 1학기, 2: 2학기
    status VARCHAR(20) DEFAULT 'enrolled',  -- enrolled, leave, graduated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Course records (이수 교과목)
CREATE TABLE IF NOT EXISTS tb_course_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_students(student_id) ON DELETE CASCADE,
    course_code VARCHAR(20) NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    semester VARCHAR(10) NOT NULL,  -- e.g., '2024-1', '2024-2'
    credits INTEGER NOT NULL,
    grade VARCHAR(5),  -- A+, A0, B+, etc.
    grade_point DECIMAL(2,1),  -- 4.5, 4.0, 3.5, etc.
    course_type VARCHAR(20),  -- 전공필수, 전공선택, 교양필수, 교양선택
    competency_mappings JSONB DEFAULT '{}'::JSONB,  -- {competency_id: weight}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_code, semester)
);

-- Extracurricular activities (비교과 활동)
CREATE TABLE IF NOT EXISTS tb_extracurricular_activities (
    activity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_students(student_id) ON DELETE CASCADE,
    activity_name VARCHAR(200) NOT NULL,
    activity_type VARCHAR(50) NOT NULL,  -- 인턴십, 봉사활동, 동아리, 대외활동, 공모전, 자격증, 어학
    status VARCHAR(20) DEFAULT 'in_progress',  -- in_progress, completed, dropped
    start_date DATE,
    end_date DATE,
    hours_completed INTEGER DEFAULT 0,
    description TEXT,
    competency_gains JSONB DEFAULT '{}'::JSONB,  -- {competency_id: points}
    certificate_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personal achievements (개인 역량/자격)
CREATE TABLE IF NOT EXISTS tb_personal_achievements (
    achievement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_students(student_id) ON DELETE CASCADE,
    achievement_type VARCHAR(50) NOT NULL,  -- 자격증, 어학, 수상, 프로젝트, 특허
    name VARCHAR(200) NOT NULL,
    issuer VARCHAR(200),
    acquired_date DATE,
    expiry_date DATE,
    score VARCHAR(50),  -- For language tests: TOEIC 900, etc.
    level VARCHAR(50),  -- 1급, 2급, Expert, etc.
    description TEXT,
    certificate_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Department curriculum (학과 커리큘럼)
CREATE TABLE IF NOT EXISTS tb_department_curriculum (
    curriculum_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id VARCHAR(20) REFERENCES tb_departments(department_id),
    course_code VARCHAR(20) NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    recommended_grade INTEGER,  -- 권장 이수 학년
    recommended_semester INTEGER,  -- 1 or 2
    is_required BOOLEAN DEFAULT FALSE,
    credits INTEGER NOT NULL,
    course_type VARCHAR(20),
    competency_weights JSONB DEFAULT '{}'::JSONB,  -- {competency_id: weight}
    prerequisites JSONB DEFAULT '[]'::JSONB,  -- [course_code, ...]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_id, course_code)
);

CREATE INDEX idx_students_department ON tb_students(department_id);
CREATE INDEX idx_course_records_student ON tb_course_records(student_id);
CREATE INDEX idx_activities_student ON tb_extracurricular_activities(student_id);
CREATE INDEX idx_achievements_student ON tb_personal_achievements(student_id);

-- ============================================
-- COMPETENCY SCHEMA
-- ============================================

SET search_path TO idino_career_competency;

-- Competency definitions (핵심역량 정의)
CREATE TABLE IF NOT EXISTS tb_competency_definitions (
    competency_id VARCHAR(20) PRIMARY KEY,
    competency_name VARCHAR(100) NOT NULL,
    competency_name_en VARCHAR(100),
    description TEXT,
    department_id VARCHAR(20),  -- NULL for university-wide
    category VARCHAR(50),  -- 대학핵심역량, 전공역량, etc.
    sub_competencies JSONB DEFAULT '[]'::JSONB,  -- [{id, name, weight}, ...]
    weight_in_department DECIMAL(3,2) DEFAULT 1.00,
    max_score DECIMAL(5,2) DEFAULT 100.00,
    icon_name VARCHAR(50),
    color_code VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competency assessment results (역량 진단 결과)
CREATE TABLE IF NOT EXISTS tb_competency_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assessment_type VARCHAR(50) NOT NULL,  -- worknet, self, curriculum, ai
    raw_scores JSONB NOT NULL,  -- {competency_id: raw_score}
    weighted_scores JSONB NOT NULL,  -- {competency_id: weighted_score}
    percentile_ranks JSONB,  -- {competency_id: percentile}
    total_score DECIMAL(5,2),
    notes TEXT,
    source_data JSONB,  -- Original assessment data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competency history (역량 점수 이력)
CREATE TABLE IF NOT EXISTS tb_competency_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trigger_type VARCHAR(50),  -- course_completion, activity_completion, assessment, manual
    scores JSONB NOT NULL,  -- {competency_id: score}
    percentiles JSONB,
    course_contribution JSONB,  -- Contribution from courses
    activity_contribution JSONB,  -- Contribution from activities
    achievement_contribution JSONB,  -- Contribution from achievements
    previous_history_id UUID REFERENCES tb_competency_history(history_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assessments_student ON tb_competency_assessments(student_id);
CREATE INDEX idx_assessments_date ON tb_competency_assessments(assessment_date);
CREATE INDEX idx_history_student ON tb_competency_history(student_id);
CREATE INDEX idx_history_date ON tb_competency_history(calculated_at);

-- ============================================
-- ROADMAP SCHEMA
-- ============================================

SET search_path TO idino_career_roadmap;

-- AI-generated roadmaps
CREATE TABLE IF NOT EXISTS tb_ai_roadmaps (
    roadmap_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL,
    target_job_code VARCHAR(20),
    target_job_name VARCHAR(200),
    semester_plans JSONB NOT NULL,  -- [{semester, courses, activities, targets}, ...]
    milestone_targets JSONB,  -- Key milestones to achieve
    current_progress DECIMAL(5,2) DEFAULT 0.00,
    confidence_score DECIMAL(3,2),
    reasoning TEXT,
    generation_method VARCHAR(20) DEFAULT 'ai',  -- ai, rule_based, hybrid
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Semester plans (detailed)
CREATE TABLE IF NOT EXISTS tb_semester_plans (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    roadmap_id UUID REFERENCES tb_ai_roadmaps(roadmap_id) ON DELETE CASCADE,
    semester VARCHAR(10) NOT NULL,  -- e.g., '2024-1'
    grade INTEGER,
    semester_seq INTEGER,  -- 1-8 for undergrad
    recommended_courses JSONB DEFAULT '[]'::JSONB,
    recommended_activities JSONB DEFAULT '[]'::JSONB,
    target_competencies JSONB DEFAULT '{}'::JSONB,  -- {competency_id: target_score}
    notes TEXT,
    status VARCHAR(20) DEFAULT 'planned',  -- planned, in_progress, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's custom milestones
CREATE TABLE IF NOT EXISTS tb_user_milestones (
    milestone_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL,
    roadmap_id UUID REFERENCES tb_ai_roadmaps(roadmap_id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_date DATE,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, skipped
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_roadmaps_student ON tb_ai_roadmaps(student_id);
CREATE INDEX idx_plans_roadmap ON tb_semester_plans(roadmap_id);
CREATE INDEX idx_milestones_student ON tb_user_milestones(student_id);

-- ============================================
-- ALUMNI SCHEMA
-- ============================================

SET search_path TO idino_career_alumni;

-- Alumni statistics (anonymized, aggregated)
CREATE TABLE IF NOT EXISTS tb_alumni_statistics (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id VARCHAR(20) NOT NULL,
    graduation_year INTEGER NOT NULL,
    job_category VARCHAR(100),
    job_code VARCHAR(20),
    avg_gpa DECIMAL(3,2),
    avg_credits INTEGER,
    common_certifications JSONB DEFAULT '[]'::JSONB,  -- Most common certs
    common_activities JSONB DEFAULT '[]'::JSONB,  -- Most common activities
    competency_profile JSONB DEFAULT '{}'::JSONB,  -- Average competency scores
    employment_rate DECIMAL(5,2),
    avg_salary_range VARCHAR(50),  -- Salary bracket
    sample_size INTEGER NOT NULL,
    data_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(department_id, graduation_year, job_category)
);

-- Success patterns
CREATE TABLE IF NOT EXISTS tb_success_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id VARCHAR(20),
    job_category VARCHAR(100),
    job_code VARCHAR(20),
    pattern_name VARCHAR(200),
    pattern_description TEXT,
    required_courses JSONB DEFAULT '[]'::JSONB,
    required_activities JSONB DEFAULT '[]'::JSONB,
    required_certifications JSONB DEFAULT '[]'::JSONB,
    min_gpa DECIMAL(3,2),
    competency_requirements JSONB DEFAULT '{}'::JSONB,
    success_rate DECIMAL(5,2),
    sample_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Career path examples (anonymized)
CREATE TABLE IF NOT EXISTS tb_career_paths (
    path_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id VARCHAR(20) NOT NULL,
    graduation_year INTEGER,
    career_trajectory JSONB NOT NULL,  -- [{year, company_type, position, salary_range}, ...]
    key_factors JSONB,  -- Factors that contributed to success
    competency_profile JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alumni_stats_dept ON tb_alumni_statistics(department_id);
CREATE INDEX idx_alumni_stats_year ON tb_alumni_statistics(graduation_year);
CREATE INDEX idx_patterns_dept ON tb_success_patterns(department_id);
CREATE INDEX idx_patterns_job ON tb_success_patterns(job_category);

-- ============================================
-- AI SCHEMA
-- ============================================

SET search_path TO idino_career_ai;

-- Student embeddings for similarity search
CREATE TABLE IF NOT EXISTS tb_student_embeddings (
    student_id VARCHAR(20) PRIMARY KEY,
    embedding vector(1024),
    profile_summary TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Job embeddings
CREATE TABLE IF NOT EXISTS tb_job_embeddings (
    job_code VARCHAR(20) PRIMARY KEY,
    job_name VARCHAR(200) NOT NULL,
    embedding vector(1024),
    job_description TEXT,
    required_competencies JSONB,
    required_certifications JSONB,
    salary_range VARCHAR(50),
    growth_outlook VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI recommendations cache
CREATE TABLE IF NOT EXISTS tb_ai_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL,
    recommendation_type VARCHAR(50) NOT NULL,  -- action, course, activity, job
    recommendations JSONB NOT NULL,
    reasoning TEXT,
    confidence_score DECIMAL(3,2),
    model_version VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE
);

-- Chat history
CREATE TABLE IF NOT EXISTS tb_chat_history (
    chat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) NOT NULL,
    student_id VARCHAR(20),
    messages JSONB NOT NULL,  -- [{role, content, timestamp}, ...]
    context JSONB,  -- Conversation context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI analysis results
CREATE TABLE IF NOT EXISTS tb_ai_analysis_results (
    analysis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,  -- gap_analysis, trend_analysis, comparison
    results JSONB NOT NULL,
    insights JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_student_embeddings ON tb_student_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_job_embeddings ON tb_job_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_recommendations_student ON tb_ai_recommendations(student_id);
CREATE INDEX idx_recommendations_type ON tb_ai_recommendations(recommendation_type);
CREATE INDEX idx_chat_session ON tb_chat_history(session_id);

-- ============================================
-- INTEGRATION SCHEMA (Mock Data Storage)
-- ============================================

SET search_path TO idino_career_integration;

-- Worknet job data (mock)
CREATE TABLE IF NOT EXISTS tb_worknet_jobs (
    job_code VARCHAR(20) PRIMARY KEY,
    job_name VARCHAR(200) NOT NULL,
    job_category VARCHAR(100),
    description TEXT,
    main_tasks TEXT,
    required_education VARCHAR(100),
    required_certifications JSONB DEFAULT '[]'::JSONB,
    required_skills JSONB DEFAULT '[]'::JSONB,
    related_majors JSONB DEFAULT '[]'::JSONB,
    salary_info JSONB,
    employment_outlook VARCHAR(50),
    growth_rate DECIMAL(5,2),
    work_environment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HRD-Net training data (mock)
CREATE TABLE IF NOT EXISTS tb_hrd_trainings (
    training_id VARCHAR(50) PRIMARY KEY,
    training_name VARCHAR(200) NOT NULL,
    training_type VARCHAR(50),
    provider VARCHAR(200),
    related_job_codes JSONB DEFAULT '[]'::JSONB,
    duration_hours INTEGER,
    cost DECIMAL(10,2),
    support_available BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API call logs
CREATE TABLE IF NOT EXISTS tb_api_call_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_type VARCHAR(50) NOT NULL,  -- worknet, hrd, university
    endpoint VARCHAR(200),
    request_params JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    cached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_worknet_jobs_category ON tb_worknet_jobs(job_category);
CREATE INDEX idx_api_logs_type ON tb_api_call_logs(api_type);
CREATE INDEX idx_api_logs_time ON tb_api_call_logs(created_at);

-- ============================================
-- Reset search_path
-- ============================================

RESET search_path;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'All schemas and tables created successfully!';
END $$;
