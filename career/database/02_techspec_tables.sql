-- ============================================
-- IDINO Career - TechSpec Related Tables
-- ??웾, ?ㅽ궗, 吏곷Т, 議몄뾽?? AI Ops ?뚯씠釉?-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. ??웾(Competency) 愿???뚯씠釉?-- ============================================

-- ??웾 ?뺤쓽
CREATE TABLE IF NOT EXISTS tb_competency (
    competency_cd VARCHAR(20) PRIMARY KEY,
    competency_nm VARCHAR(100) NOT NULL,
    competency_nm_en VARCHAR(100),
    definition TEXT,
    category VARCHAR(50), -- ?꾨Ц吏?? 臾몄젣?닿껐, ?뚰넻?묒뾽, 吏곸뾽?ㅻ━, 湲濡쒕쾶??웾
    weight DECIMAL(5,2) DEFAULT 0,
    max_score INT DEFAULT 100,
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

COMMENT ON TABLE tb_competency IS '??웾 ?뺤쓽 留덉뒪??;

-- ?ㅽ궗 ?뺤쓽
CREATE TABLE IF NOT EXISTS tb_skill (
    skill_cd VARCHAR(20) PRIMARY KEY,
    skill_nm VARCHAR(100) NOT NULL,
    skill_nm_en VARCHAR(100),
    synonyms TEXT[], -- ?숈쓽??諛곗뿴
    category VARCHAR(50), -- technical, soft, domain
    difficulty INT CHECK (difficulty BETWEEN 1 AND 5),
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

COMMENT ON TABLE tb_skill IS '?ㅽ궗 ?뺤쓽 留덉뒪??;

-- ?ㅽ궗-??웾 留ㅽ븨
CREATE TABLE IF NOT EXISTS tb_skill_competency_map (
    map_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_cd VARCHAR(20) REFERENCES tb_skill(skill_cd),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    weight DECIMAL(5,2) DEFAULT 1.0,
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
    UNIQUE(skill_cd, competency_cd)
);

-- 怨쇰ぉ-??웾 留ㅽ븨
CREATE TABLE IF NOT EXISTS tb_course_competency_map (
    map_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    contribution_weight DECIMAL(5,2) NOT NULL,
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
    UNIQUE(course_cd, competency_cd)
);

-- ??웾 ?됯?
CREATE TABLE IF NOT EXISTS tb_assessment (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    assessment_type VARCHAR(20) NOT NULL, -- self, peer, instructor, system
    assessment_date DATE NOT NULL,
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
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

COMMENT ON TABLE tb_assessment IS '??웾 ?됯?';

-- ??웾 ?됯? 寃곌낵
CREATE TABLE IF NOT EXISTS tb_assessment_result (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID REFERENCES tb_assessment(assessment_id),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    raw_score DECIMAL(5,2) NOT NULL,
    adjusted_score DECIMAL(5,2),
    academic_contribution DECIMAL(5,2),
    extracurricular_boost DECIMAL(5,2),
    final_score DECIMAL(5,2) NOT NULL,
    status VARCHAR(20), -- excellent, good, average, improve, focus
    gap_score DECIMAL(5,2), -- 紐⑺몴 ?鍮?李⑥씠
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

COMMENT ON TABLE tb_assessment_result IS '??웾 ?됯? 寃곌낵';

-- ?숈깮蹂???웾 ?꾪솴 (吏묎퀎)
CREATE TABLE IF NOT EXISTS tb_student_competency (
    student_competency_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    current_score DECIMAL(5,2) DEFAULT 0,
    target_score DECIMAL(5,2) DEFAULT 85,
    gap_score DECIMAL(5,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'improve', -- excellent, good, average, improve, focus
    last_assessment_date DATE,
    trend VARCHAR(10) DEFAULT 'stable', -- up, down, stable
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
    UNIQUE(student_id, competency_cd)
);

COMMENT ON TABLE tb_student_competency IS '?숈깮蹂???웾 ?꾪솴';

-- ============================================
-- 2. ?쒕룞/?깆랬 愿???뚯씠釉?-- ============================================

-- 鍮꾧탳怨??꾨줈洹몃옩
CREATE TABLE IF NOT EXISTS tb_program (
    program_cd VARCHAR(20) PRIMARY KEY,
    program_nm VARCHAR(200) NOT NULL,
    program_type VARCHAR(50) NOT NULL, -- internship, contest, club, volunteer, certificate, seminar
    organizer VARCHAR(200),
    start_date DATE,
    end_date DATE,
    description TEXT,
    competency_contributions JSONB, -- {"COMP01": 0.3, "COMP02": 0.2}
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

COMMENT ON TABLE tb_program IS '鍮꾧탳怨??꾨줈洹몃옩';

-- ?꾨줈洹몃옩 李몄뿬 ?대젰
CREATE TABLE IF NOT EXISTS tb_participation (
    participation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    program_cd VARCHAR(20) REFERENCES tb_program(program_cd),
    status VARCHAR(20) NOT NULL, -- registered, in_progress, completed, cancelled
    completed_at TIMESTAMP,
    certificate_url TEXT,
    achievement_note TEXT,
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

COMMENT ON TABLE tb_participation IS '?꾨줈洹몃옩 李몄뿬 ?대젰';

-- 자격증/어학/수상 성적 (Excel Format Standard)
CREATE TABLE IF NOT EXISTS tb_achievement (
    achievement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    achievement_type VARCHAR(50) NOT NULL, -- certificate, language, award, publication
    title VARCHAR(200) NOT NULL,           -- Excel: title (기존: achievement_nm)
    issuer VARCHAR(200),                   -- Excel: issuer (기존: issuing_organization)
    issue_date DATE,                       -- Excel: issue_date (기존: acquired_date)
    expire_date DATE,                      -- Excel: expire_date (기존: expiry_date)
    level VARCHAR(50),                     -- Excel: level (신규 추가)
    score VARCHAR(50),                     -- TOEIC 850, 정보처리기사, 금상 등
    competency_contributions JSONB,        -- Excel: competency_contributions (신규 추가)
    verified CHAR(1) DEFAULT 'N',
    evidence_url TEXT,                     -- 증빙 URL (DB 전용)
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

COMMENT ON TABLE tb_achievement IS '자격증/어학/수상 성적 (Excel Format Standard)';

-- ?ы듃?대━??CREATE TABLE IF NOT EXISTS tb_portfolio (
    portfolio_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    artifact_type VARCHAR(50) NOT NULL, -- github, notion, project, paper
    title VARCHAR(200) NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
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

COMMENT ON TABLE tb_portfolio IS '?ы듃?대━??;

-- ============================================
-- 3. 吏곷Т/吏곸뾽 愿???뚯씠釉?-- ============================================

-- 吏곷Т ?뺤쓽
CREATE TABLE IF NOT EXISTS tb_role (
    role_cd VARCHAR(20) PRIMARY KEY,
    role_nm VARCHAR(100) NOT NULL,
    role_nm_en VARCHAR(100),
    worknet_code VARCHAR(20), -- ?뚰겕??吏곸뾽肄붾뱶
    description TEXT,
    industry VARCHAR(100),
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

COMMENT ON TABLE tb_role IS '吏곷Т/吏곸뾽 ?뺤쓽';

-- 吏곷Т蹂???웾 ?붽뎄?ы빆
CREATE TABLE IF NOT EXISTS tb_role_requirement (
    requirement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    competency_cd VARCHAR(20) REFERENCES tb_competency(competency_cd),
    required_level INT NOT NULL CHECK (required_level BETWEEN 1 AND 100),
    importance VARCHAR(10) NOT NULL CHECK (importance IN ('high', 'medium', 'low')),
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
    UNIQUE(role_cd, competency_cd)
);

COMMENT ON TABLE tb_role_requirement IS '吏곷Т蹂???웾 ?붽뎄?ы빆';

-- ============================================
-- 4. 議몄뾽??愿???뚯씠釉?-- ============================================

-- 議몄뾽??肄뷀샇??吏묎퀎 (k-?듬챸??蹂댁옣)
CREATE TABLE IF NOT EXISTS tb_alumni_cohort (
    cohort_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    graduation_year INT NOT NULL,
    role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    sample_size INT NOT NULL CHECK (sample_size >= 5), -- k-anonymity
    avg_gpa_range VARCHAR(20),
    salary_range VARCHAR(50),
    competency_profile JSONB, -- {"COMP01": 85, "COMP02": 78}
    employment_rate DECIMAL(5,2),
    avg_job_search_months DECIMAL(5,2),
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

COMMENT ON TABLE tb_alumni_cohort IS '議몄뾽??肄뷀샇??吏묎퀎 (?듬챸??';

-- ?깃났 ?⑦꽩
CREATE TABLE IF NOT EXISTS tb_success_pattern (
    pattern_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    pattern_nm VARCHAR(200) NOT NULL,
    pattern_rules JSONB NOT NULL, -- {"min_gpa": 3.5, "required_certs": ["?뺣낫泥섎━湲곗궗"]}
    correlation_score DECIMAL(5,4),
    lift DECIMAL(5,2),
    sample_size INT NOT NULL CHECK (sample_size >= 30),
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

COMMENT ON TABLE tb_success_pattern IS '議몄뾽???깃났 ?⑦꽩';

-- ============================================
-- 5. AI Ops 愿???뚯씠釉?-- ============================================

-- AI 異붿쿇 ?ㅽ뻾 濡쒓렇
CREATE TABLE IF NOT EXISTS tb_recommendation_run (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    target_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    -- Version tracking
    model_version VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    policy_version VARCHAR(50) NOT NULL,
    -- Input/Output
    input_snapshot JSONB NOT NULL,
    retrieval_results JSONB,
    output_json JSONB NOT NULL,
    -- Validation
    schema_valid CHAR(1) NOT NULL,
    constraints_passed CHAR(1) NOT NULL,
    evidence_count INT NOT NULL,
    -- Performance
    latency_ms INT,
    total_tokens INT,
    cost_usd DECIMAL(10,6),
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

COMMENT ON TABLE tb_recommendation_run IS 'AI 異붿쿇 ?ㅽ뻾 濡쒓렇';

-- AI 異붿쿇 ??ぉ
CREATE TABLE IF NOT EXISTS tb_recommendation_item (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES tb_recommendation_run(run_id),
    action_type VARCHAR(50) NOT NULL, -- course, activity, certification, project, mentoring
    title VARCHAR(200) NOT NULL,
    description TEXT,
    impact_score DECIMAL(5,2),
    effort_hours DECIMAL(5,2),
    priority VARCHAR(10), -- high, medium, low
    semester VARCHAR(10),
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

COMMENT ON TABLE tb_recommendation_item IS 'AI 異붿쿇 ??ぉ';

-- AI 異붿쿇 洹쇨굅 (Evidence)
CREATE TABLE IF NOT EXISTS tb_recommendation_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES tb_recommendation_item(item_id),
    source_type VARCHAR(50) NOT NULL, -- course, rule, program, role_req, alumni_stat, portfolio
    source_id VARCHAR(100) NOT NULL,
    source_version VARCHAR(50),
    snippet_text TEXT NOT NULL,
    snippet_hash VARCHAR(64) NOT NULL,
    retrieval_score DECIMAL(5,4),
    retrieval_method VARCHAR(20), -- bm25, vector, hybrid
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

COMMENT ON TABLE tb_recommendation_evidence IS 'AI 異붿쿇 洹쇨굅';

-- ?쇰뱶諛??대깽??CREATE TABLE IF NOT EXISTS tb_feedback_event (
    feedback_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES tb_recommendation_run(run_id),
    user_id VARCHAR(50) NOT NULL,
    feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('thumbs_up', 'thumbs_down', 'edit')),
    details TEXT,
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

COMMENT ON TABLE tb_feedback_event IS '?쇰뱶諛??대깽??;

-- ?꾨＼?꾪듃 踰꾩쟾
CREATE TABLE IF NOT EXISTS tb_prompt_version (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_cd VARCHAR(50) UNIQUE NOT NULL,
    prompt_content TEXT NOT NULL,
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

-- ?뺤콉 踰꾩쟾
CREATE TABLE IF NOT EXISTS tb_policy_version (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_cd VARCHAR(50) UNIQUE NOT NULL,
    rules JSONB NOT NULL,
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

-- 紐⑤뜽 踰꾩쟾
CREATE TABLE IF NOT EXISTS tb_model_version (
    version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_cd VARCHAR(50) UNIQUE NOT NULL,
    base_model VARCHAR(100) NOT NULL,
    fine_tuned_id VARCHAR(200),
    training_data_version VARCHAR(50),
    metrics JSONB,
    deployed_at TIMESTAMP,
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

-- Eval 耳?댁뒪
CREATE TABLE IF NOT EXISTS tb_eval_case (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_nm VARCHAR(200) NOT NULL,
    input_data JSONB NOT NULL,
    expected_schema JSONB NOT NULL,
    quality_criteria JSONB NOT NULL,
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

-- Eval 寃곌낵
CREATE TABLE IF NOT EXISTS tb_eval_result (
    result_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES tb_eval_case(case_id),
    run_id UUID REFERENCES tb_recommendation_run(run_id),
    model_version VARCHAR(50) NOT NULL,
    passed CHAR(1) NOT NULL,
    schema_valid CHAR(1) NOT NULL,
    evidence_grounded CHAR(1) NOT NULL,
    constraint_compliant CHAR(1) NOT NULL,
    scores JSONB NOT NULL,
    failure_reasons JSONB,
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

-- ============================================
-- 6. ?뚰겕??吏꾨떒 愿???뚯씠釉?-- ============================================

CREATE TABLE IF NOT EXISTS tb_worknet_diagnosis (
    diagnosis_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    diagnosis_date DATE NOT NULL,
    aptitude_codes VARCHAR(50)[], -- ['I', 'R', 'A']
    interest_codes VARCHAR(50)[],
    job_match_scores JSONB, -- {"ROLE01": 85, "ROLE02": 78}
    raw_result JSONB,
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

COMMENT ON TABLE tb_worknet_diagnosis IS '?뚰겕??吏꾨떒 寃곌낵';

-- ============================================
-- Additional Indexes
-- ============================================

CREATE INDEX idx_student_competency_student ON tb_student_competency(student_id);
CREATE INDEX idx_participation_student ON tb_participation(student_id);
CREATE INDEX idx_achievement_student ON tb_achievement(student_id);
CREATE INDEX idx_recommendation_run_student ON tb_recommendation_run(student_id);
CREATE INDEX idx_recommendation_run_created ON tb_recommendation_run(ins_dt);
CREATE INDEX idx_feedback_event_run ON tb_feedback_event(run_id);
CREATE INDEX idx_eval_result_case ON tb_eval_result(case_id);
CREATE INDEX idx_alumni_cohort_dept ON tb_alumni_cohort(department_cd);
CREATE INDEX idx_worknet_diagnosis_student ON tb_worknet_diagnosis(student_id);
