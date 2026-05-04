-- ============================================
-- IDINO Career - P1/P2 Extensions Tables
-- Phase 7-13: Skill Graph, Opportunity, AI Coach, Risk Alerts, Badges, What-if, Advisor
-- Created: 2026-01-05
-- ============================================

-- PostgreSQL 13+ ?댁옣 gen_random_uuid() ?ъ슜 (?뺤옣 遺덊븘??
SET search_path TO idino_career;

-- ============================================
-- Phase 7: Skill Graph & Gap (LinkedIn Career Explorer style)
-- ============================================

-- 吏곷Т-?ㅽ궗 留ㅽ븨 (Role?봖kill Graph)
CREATE TABLE IF NOT EXISTS tb_role_skill_map (
    map_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    skill_cd VARCHAR(20) REFERENCES tb_skill(skill_cd),
    required_level INT NOT NULL CHECK (required_level BETWEEN 1 AND 5),
    importance VARCHAR(15) NOT NULL CHECK (importance IN ('critical', 'important', 'nice_to_have')),
    market_demand_score DECIMAL(5,2), -- ?쒖옣 ?섏슂 ?먯닔
    growth_trend VARCHAR(20) DEFAULT 'stable', -- growing, stable, declining
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
    UNIQUE(role_cd, skill_cd)
);

COMMENT ON TABLE tb_role_skill_map IS '吏곷Т-?ㅽ궗 留ㅽ븨 (Skill Graph)';

-- ?숈깮 ?ㅽ궗 ?꾪솴
CREATE TABLE IF NOT EXISTS tb_student_skill (
    student_skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    skill_cd VARCHAR(20) REFERENCES tb_skill(skill_cd),
    current_level INT DEFAULT 1 CHECK (current_level BETWEEN 1 AND 5),
    target_level INT DEFAULT 3 CHECK (target_level BETWEEN 1 AND 5),
    evidence_count INT DEFAULT 0,
    last_verified_date DATE,
    verification_source VARCHAR(50), -- course, certificate, project, self_assessment
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
    UNIQUE(student_id, skill_cd)
);

COMMENT ON TABLE tb_student_skill IS '?숈깮 ?ㅽ궗 ?꾪솴';

-- ?ㅽ궗 媛?遺꾩꽍 寃곌낵
CREATE TABLE IF NOT EXISTS tb_skill_gap_analysis (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    target_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_gap_score DECIMAL(5,2), -- 0-100, ??쓣?섎줉 醫뗭쓬
    gap_details JSONB NOT NULL, -- [{"skill_cd": "SK01", "current": 2, "required": 4, "gap": 2}]
    top_priority_skills VARCHAR(20)[], -- ?곗꽑 媛쒕컻 ?꾩슂 ?ㅽ궗
    recommended_actions JSONB, -- 異붿쿇 ?≪뀡
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

COMMENT ON TABLE tb_skill_gap_analysis IS '?ㅽ궗 媛?遺꾩꽍 寃곌낵';

-- ?ㅽ궗 ?곌?愿怨?(Skill Graph edges)
CREATE TABLE IF NOT EXISTS tb_skill_relation (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_cd_from VARCHAR(20) REFERENCES tb_skill(skill_cd),
    skill_cd_to VARCHAR(20) REFERENCES tb_skill(skill_cd),
    relation_type VARCHAR(30) NOT NULL, -- prerequisite, complementary, alternative, builds_on
    strength DECIMAL(3,2) DEFAULT 1.0, -- 0.0-1.0
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(skill_cd_from, skill_cd_to, relation_type)
);

COMMENT ON TABLE tb_skill_relation IS '?ㅽ궗 ?곌?愿怨?(Graph edges)';

-- ============================================
-- Phase 8: Opportunity Marketplace (Handshake style)
-- ============================================

-- 湲고쉶 (?명꽩?? ?꾨줈?앺듃, ?곌뎄?? 怨듬え????
CREATE TABLE IF NOT EXISTS tb_opportunity (
    opportunity_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_type VARCHAR(30) NOT NULL, -- internship, project, lab, contest, scholarship, job
    title VARCHAR(300) NOT NULL,
    organization VARCHAR(200),
    description TEXT,
    requirements JSONB, -- {"min_gpa": 3.0, "skills": ["Python", "ML"], "grade": [3, 4]}
    benefits JSONB, -- {"salary": "??300留뚯썝", "certificate": true}
    application_start DATE,
    application_end DATE,
    start_date DATE,
    end_date DATE,
    location VARCHAR(200),
    remote_available BOOLEAN DEFAULT FALSE,
    slots INT,
    status VARCHAR(20) DEFAULT 'open', -- open, closed, filled, cancelled
    external_url TEXT,
    tags VARCHAR(50)[],
    department_cds VARCHAR(20)[], -- 愿???숆낵
    competency_contributions JSONB, -- {"COMP01": 0.3, "COMP02": 0.2}
    skill_contributions JSONB, -- {"SK01": 0.4, "SK02": 0.3}
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

COMMENT ON TABLE tb_opportunity IS '湲고쉶 (?명꽩?? ?꾨줈?앺듃, ?곌뎄?? 怨듬え????';

-- 湲고쉶 異붿쿇
CREATE TABLE IF NOT EXISTS tb_opportunity_recommendation (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    opportunity_id UUID REFERENCES tb_opportunity(opportunity_id),
    match_score DECIMAL(5,2) NOT NULL, -- 0-100
    match_reasons JSONB, -- ["skill_match", "department_match", "gpa_eligible"]
    status VARCHAR(20) DEFAULT 'recommended', -- recommended, viewed, saved, applied, dismissed
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, opportunity_id)
);

COMMENT ON TABLE tb_opportunity_recommendation IS '湲고쉶 異붿쿇';

-- 湲고쉶 吏???대젰
CREATE TABLE IF NOT EXISTS tb_opportunity_application (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    opportunity_id UUID REFERENCES tb_opportunity(opportunity_id),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'submitted', -- submitted, under_review, accepted, rejected, withdrawn
    cover_letter TEXT,
    attachments JSONB, -- [{"name": "resume.pdf", "url": "..."}]
    reviewer_notes TEXT,
    decision_at TIMESTAMP,
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

COMMENT ON TABLE tb_opportunity_application IS '湲고쉶 吏???대젰';

-- ============================================
-- Phase 9: AI Coach Loop
-- ============================================

-- 肄붿묶 紐⑺몴
CREATE TABLE IF NOT EXISTS tb_coaching_goal (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    goal_type VARCHAR(30) NOT NULL, -- career, competency, skill, academic, activity
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    target_metrics JSONB, -- {"gpa": 3.8, "skill_python": 4, "competency_COMP01": 85}
    current_metrics JSONB,
    deadline DATE,
    priority INT DEFAULT 1, -- 1=highest
    status VARCHAR(20) DEFAULT 'active', -- active, achieved, abandoned, paused
    achievement_rate DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    achieved_at TIMESTAMP,
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

COMMENT ON TABLE tb_coaching_goal IS '肄붿묶 紐⑺몴';

-- 肄붿묶 怨꾪쉷
CREATE TABLE IF NOT EXISTS tb_coaching_plan (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id),
    plan_version INT DEFAULT 1,
    milestones JSONB NOT NULL, -- [{"week": 1, "task": "...", "target": "..."}]
    weekly_hours_target DECIMAL(4,1) DEFAULT 10,
    current_week INT DEFAULT 1,
    total_weeks INT,
    ai_generated BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, replanned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

COMMENT ON TABLE tb_coaching_plan IS '肄붿묶 怨꾪쉷';

-- 二쇨컙 泥댄겕??CREATE TABLE IF NOT EXISTS tb_coaching_checkin (
    checkin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES tb_coaching_plan(plan_id),
    week_number INT NOT NULL,
    checkin_date DATE NOT NULL,
    -- Self-reported progress
    completed_tasks JSONB, -- [{"task_id": "...", "completed": true, "notes": "..."}]
    hours_spent DECIMAL(4,1),
    blockers TEXT,
    wins TEXT,
    mood_score INT CHECK (mood_score BETWEEN 1 AND 5), -- 1=struggling, 5=thriving
    -- AI Analysis
    ai_feedback TEXT,
    ai_suggestions JSONB,
    progress_score DECIMAL(5,2), -- 0-100
    on_track BOOLEAN,
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

COMMENT ON TABLE tb_coaching_checkin IS '二쇨컙 泥댄겕??;

-- ?뚭퀬 (Retrospective)
CREATE TABLE IF NOT EXISTS tb_coaching_retrospective (
    retrospective_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    -- Self-reflection
    what_went_well TEXT,
    what_could_improve TEXT,
    lessons_learned TEXT,
    -- Metrics
    initial_metrics JSONB,
    final_metrics JSONB,
    improvement_percentage DECIMAL(5,2),
    -- AI Analysis
    ai_summary TEXT,
    ai_insights JSONB,
    next_period_recommendations JSONB,
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

COMMENT ON TABLE tb_coaching_retrospective IS '?뚭퀬';

-- ============================================
-- Phase 10: Risk Alerts
-- ============================================

-- ?꾪뿕 ?뚮┝
CREATE TABLE IF NOT EXISTS tb_risk_alert (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    alert_type VARCHAR(50) NOT NULL, -- credit_shortage, prerequisite_missing, timetable_conflict, gpa_warning, graduation_delay
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'warning', 'info')),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    affected_items JSONB, -- {"course_cd": "CS101", "reason": "prerequisite_missing"}
    recommended_actions JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved, dismissed
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
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

COMMENT ON TABLE tb_risk_alert IS '?꾪뿕 ?뚮┝';

-- ?쒖빟 議곌굔 寃???대젰
CREATE TABLE IF NOT EXISTS tb_constraint_check (
    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    check_type VARCHAR(50) NOT NULL, -- prerequisite, credit, timetable, graduation, gpa
    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_term_cd VARCHAR(10),
    input_data JSONB, -- 寃??????곗씠??    result_passed BOOLEAN NOT NULL,
    violations JSONB, -- [{"rule": "...", "message": "..."}]
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_constraint_check IS '?쒖빟 議곌굔 寃???대젰';

-- ?좎닔怨쇰ぉ 洹쒖튃
CREATE TABLE IF NOT EXISTS tb_prerequisite_rule (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    prerequisite_course_cd VARCHAR(20) REFERENCES tb_course(course_cd),
    rule_type VARCHAR(20) DEFAULT 'required', -- required, recommended, corequisite
    min_grade VARCHAR(5), -- 理쒖냼 ?깆쟻 (?? C+)
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_cd, prerequisite_course_cd)
);

COMMENT ON TABLE tb_prerequisite_rule IS '?좎닔怨쇰ぉ 洹쒖튃';

-- ============================================
-- Phase 11: Skill Passport/Badges
-- ============================================

-- 諭껋? ?뺤쓽
CREATE TABLE IF NOT EXISTS tb_badge (
    badge_cd VARCHAR(30) PRIMARY KEY,
    badge_nm VARCHAR(100) NOT NULL,
    badge_nm_en VARCHAR(100),
    description TEXT,
    category VARCHAR(50), -- skill, competency, achievement, milestone
    icon_url TEXT,
    criteria JSONB NOT NULL, -- {"type": "skill", "skill_cd": "SK01", "level": 4}
    points INT DEFAULT 0, -- 寃뚯씠誘명뵾耳?댁뀡 ?ъ씤??    rarity VARCHAR(20) DEFAULT 'common', -- common, uncommon, rare, epic, legendary
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

COMMENT ON TABLE tb_badge IS '諭껋? ?뺤쓽';

-- ?숈깮 諭껋? ?띾뱷
CREATE TABLE IF NOT EXISTS tb_student_badge (
    student_badge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    badge_cd VARCHAR(30) REFERENCES tb_badge(badge_cd),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evidence_items JSONB, -- [{"type": "course", "id": "CS101", "grade": "A+"}]
    verification_status VARCHAR(20) DEFAULT 'verified', -- pending, verified, revoked
    share_url TEXT, -- 怨듭쑀 媛?ν븳 URL
    display_order INT DEFAULT 0,
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
    UNIQUE(student_id, badge_cd)
);

COMMENT ON TABLE tb_student_badge IS '?숈깮 諭껋? ?띾뱷';

-- ?ㅽ궗 ?⑥뒪?ы듃 (醫낇빀 ?꾨줈??
CREATE TABLE IF NOT EXISTS tb_skill_passport (
    passport_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) UNIQUE REFERENCES tb_student(student_id),
    public_url_slug VARCHAR(100) UNIQUE, -- 怨듦컻 URL???щ윭洹?    is_public BOOLEAN DEFAULT FALSE,
    headline VARCHAR(200), -- ??以??뚭컻
    bio TEXT,
    featured_badges VARCHAR(30)[], -- ???諭껋?
    featured_skills VARCHAR(20)[], -- ????ㅽ궗
    featured_projects UUID[], -- ????꾨줈?앺듃
    social_links JSONB, -- {"linkedin": "...", "github": "..."}
    view_count INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

COMMENT ON TABLE tb_skill_passport IS '?ㅽ궗 ?⑥뒪?ы듃 (醫낇빀 ?꾨줈??';

-- ============================================
-- Phase 12: What-if Planner
-- ============================================

-- ?쒕??덉씠???쒕굹由ъ삤
CREATE TABLE IF NOT EXISTS tb_simulation_scenario (
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    scenario_name VARCHAR(200) NOT NULL,
    scenario_type VARCHAR(50) NOT NULL, -- course_selection, career_change, skill_focus, activity_plan
    base_snapshot JSONB NOT NULL, -- ?꾩옱 ?곹깭 ?ㅻ깄??    changes JSONB NOT NULL, -- 蹂寃??ы빆 [{"type": "add_course", "course_cd": "CS201"}]
    -- ?쒕??덉씠??寃곌낵
    projected_gpa DECIMAL(3,2),
    projected_competencies JSONB,
    projected_skills JSONB,
    projected_graduation_date DATE,
    projected_role_fit JSONB, -- {"ROLE01": 85, "ROLE02": 72}
    risk_assessment JSONB,
    ai_analysis TEXT,
    recommendation_score INT, -- 1-100
    -- ?곹깭
    status VARCHAR(20) DEFAULT 'draft', -- draft, analyzed, saved, applied
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP,
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

COMMENT ON TABLE tb_simulation_scenario IS '?쒕??덉씠???쒕굹由ъ삤 (What-if)';

-- ?쒕굹由ъ삤 鍮꾧탳
CREATE TABLE IF NOT EXISTS tb_scenario_comparison (
    comparison_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    scenario_ids UUID[] NOT NULL, -- 鍮꾧탳 ????쒕굹由ъ삤??    comparison_metrics JSONB NOT NULL, -- 鍮꾧탳 吏??    winner_scenario_id UUID,
    comparison_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_scenario_comparison IS '?쒕굹由ъ삤 鍮꾧탳';

-- ============================================
-- Phase 13: Advisor Workspace
-- ============================================

-- ?대뱶諛붿씠? ?좊떦
CREATE TABLE IF NOT EXISTS tb_advisor_assignment (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_user_id UUID REFERENCES tb_user(user_id),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    assignment_type VARCHAR(30) DEFAULT 'primary', -- primary, secondary, temporary
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, transferred
    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(advisor_user_id, student_id, assignment_type)
);

COMMENT ON TABLE tb_advisor_assignment IS '?대뱶諛붿씠? ?좊떦';

-- ?대뱶諛붿씠? 媛쒖엯
CREATE TABLE IF NOT EXISTS tb_advisor_intervention (
    intervention_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_user_id UUID REFERENCES tb_user(user_id),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    intervention_type VARCHAR(50) NOT NULL, -- goal_review, plan_override, risk_escalation, recommendation_edit
    title VARCHAR(200) NOT NULL,
    description TEXT,
    related_entity_type VARCHAR(50), -- goal, plan, alert, recommendation
    related_entity_id UUID,
    original_value JSONB,
    new_value JSONB,
    reason TEXT,
    student_notified BOOLEAN DEFAULT FALSE,
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

COMMENT ON TABLE tb_advisor_intervention IS '?대뱶諛붿씠? 媛쒖엯';

-- 肄뷀샇????쒕낫???ㅻ깄??CREATE TABLE IF NOT EXISTS tb_cohort_snapshot (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_cd VARCHAR(20) REFERENCES tb_department(department_cd),
    grade_level INT CHECK (grade_level BETWEEN 1 AND 4),
    term_cd VARCHAR(10) REFERENCES tb_term(term_cd),
    snapshot_date DATE NOT NULL,
    -- 吏묎퀎 ?듦퀎
    total_students INT NOT NULL,
    avg_gpa DECIMAL(3,2),
    avg_competency_scores JSONB, -- {"COMP01": 72, "COMP02": 68}
    avg_skill_levels JSONB,
    -- ?꾪뿕 ?듦퀎
    risk_distribution JSONB, -- {"critical": 5, "warning": 15, "info": 30}
    at_risk_students VARCHAR(20)[], -- 二쇱쓽 ?꾩슂 ?숈깮 ID
    -- ?깃낵 ?듦퀎
    goal_achievement_rate DECIMAL(5,2),
    opportunity_application_rate DECIMAL(5,2),
    badge_earning_rate DECIMAL(5,2),
    -- 鍮꾧탳
    vs_prev_term JSONB, -- ???숆린 ?鍮?蹂??    -- Audit Columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_cohort_snapshot IS '肄뷀샇????쒕낫???ㅻ깄??;

-- ?대뱶諛붿씠? 硫붾え
CREATE TABLE IF NOT EXISTS tb_advisor_note (
    note_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    advisor_user_id UUID REFERENCES tb_user(user_id),
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    note_type VARCHAR(30) DEFAULT 'general', -- general, meeting, observation, action_item
    title VARCHAR(200),
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT TRUE, -- ?숈깮?먭쾶 怨듦컻 ?щ?
    meeting_date DATE,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
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

COMMENT ON TABLE tb_advisor_note IS '?대뱶諛붿씠? 硫붾え';

-- ============================================
-- Indexes for Performance
-- ============================================

-- Phase 7
CREATE INDEX idx_role_skill_map_role ON tb_role_skill_map(role_cd);
CREATE INDEX idx_role_skill_map_skill ON tb_role_skill_map(skill_cd);
CREATE INDEX idx_student_skill_student ON tb_student_skill(student_id);
CREATE INDEX idx_skill_gap_analysis_student ON tb_skill_gap_analysis(student_id);
CREATE INDEX idx_skill_relation_from ON tb_skill_relation(skill_cd_from);

-- Phase 8
CREATE INDEX idx_opportunity_type ON tb_opportunity(opportunity_type);
CREATE INDEX idx_opportunity_status ON tb_opportunity(status);
CREATE INDEX idx_opportunity_dates ON tb_opportunity(application_start, application_end);
CREATE INDEX idx_opportunity_recommendation_student ON tb_opportunity_recommendation(student_id);
CREATE INDEX idx_opportunity_application_student ON tb_opportunity_application(student_id);

-- Phase 9
CREATE INDEX idx_coaching_goal_student ON tb_coaching_goal(student_id);
CREATE INDEX idx_coaching_goal_status ON tb_coaching_goal(status);
CREATE INDEX idx_coaching_plan_goal ON tb_coaching_plan(goal_id);
CREATE INDEX idx_coaching_checkin_plan ON tb_coaching_checkin(plan_id);
CREATE INDEX idx_coaching_retrospective_goal ON tb_coaching_retrospective(goal_id);

-- Phase 10
CREATE INDEX idx_risk_alert_student ON tb_risk_alert(student_id);
CREATE INDEX idx_risk_alert_status ON tb_risk_alert(status);
CREATE INDEX idx_risk_alert_severity ON tb_risk_alert(severity);
CREATE INDEX idx_constraint_check_student ON tb_constraint_check(student_id);

-- Phase 11
CREATE INDEX idx_student_badge_student ON tb_student_badge(student_id);
CREATE INDEX idx_skill_passport_slug ON tb_skill_passport(public_url_slug);

-- Phase 12
CREATE INDEX idx_simulation_scenario_student ON tb_simulation_scenario(student_id);
CREATE INDEX idx_scenario_comparison_student ON tb_scenario_comparison(student_id);

-- Phase 13
CREATE INDEX idx_advisor_assignment_advisor ON tb_advisor_assignment(advisor_user_id);
CREATE INDEX idx_advisor_assignment_student ON tb_advisor_assignment(student_id);
CREATE INDEX idx_advisor_intervention_student ON tb_advisor_intervention(student_id);
CREATE INDEX idx_cohort_snapshot_dept ON tb_cohort_snapshot(department_cd);
CREATE INDEX idx_advisor_note_student ON tb_advisor_note(student_id);

-- ============================================
-- Seed Data for Testing (湲곗〈 ?곗씠??議댁옱?쒖뿉留??쎌엯)
-- ============================================

-- P1: Role-Skill Mappings (湲곗〈 role, skill???덉쓣 ?뚮쭔)
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend)
SELECT r.role_cd, s.skill_cd,
    3 + (RANDOM() * 2)::INT,
    CASE WHEN RANDOM() > 0.7 THEN 'critical' WHEN RANDOM() > 0.4 THEN 'important' ELSE 'nice_to_have' END,
    70.0 + RANDOM() * 30,
    CASE WHEN RANDOM() > 0.6 THEN 'growing' WHEN RANDOM() > 0.3 THEN 'stable' ELSE 'declining' END
FROM (SELECT role_cd FROM tb_role LIMIT 3) r
CROSS JOIN (SELECT skill_cd FROM tb_skill LIMIT 5) s
ON CONFLICT DO NOTHING;

-- P1: Skill Relations (湲곗〈 skill???덉쓣 ?뚮쭔)
INSERT INTO tb_skill_relation (skill_cd_from, skill_cd_to, relation_type, strength)
SELECT s1.skill_cd, s2.skill_cd, 'complementary', 0.7 + RANDOM() * 0.3
FROM (SELECT skill_cd FROM tb_skill ORDER BY skill_cd LIMIT 2) s1
CROSS JOIN (SELECT skill_cd FROM tb_skill ORDER BY skill_cd DESC LIMIT 2) s2
WHERE s1.skill_cd != s2.skill_cd
ON CONFLICT DO NOTHING;

-- P8: Sample Opportunities (FK ?놁쓬, 吏곸젒 ?쎌엯 媛??
INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, status, tags)
VALUES
    ('internship', 'AI ?곌뎄 ?명꽩??, '?쇱꽦 SDS', 'AI/ML ?곌뎄 ?명꽩 紐⑥쭛', '{"min_gpa": 3.5, "skills": ["Python", "TensorFlow"]}', 'open', ARRAY['AI', 'ML', 'Python']),
    ('contest', '?뚰봽?몄썾??媛쒕컻 怨듬え??, '?ㅼ씠踰?, '李쎌쓽??SW ?꾩씠?붿뼱 怨듬え', '{"grade": [3, 4]}', 'open', ARRAY['媛쒕컻', '李쎌뾽']),
    ('project', '罹≪뒪???붿옄???꾨줈?앺듃', '?고븰?묐젰??, '湲곗뾽 ?곌퀎 ?꾨줈?앺듃', '{"min_gpa": 3.0}', 'open', ARRAY['罹≪뒪??, '?고븰?묐젰']),
    ('lab', 'AI ?곌뎄???숇??곌뎄??, 'AI?듯빀?숆낵', '?λ윭???곌뎄 李몄뿬', '{"min_gpa": 3.7, "skills": ["Python", "PyTorch"]}', 'open', ARRAY['?곌뎄', 'AI'])
ON CONFLICT DO NOTHING;

-- P11: Sample Badges (FK ?놁쓬, 吏곸젒 ?쎌엯 媛??
INSERT INTO tb_badge (badge_cd, badge_nm, badge_nm_en, description, category, criteria, points, rarity)
VALUES
    ('BADGE_PY_MASTER', 'Python 留덉뒪??, 'Python Master', 'Python ?ㅽ궗 ?덈꺼 5 ?ъ꽦', 'skill', '{"type": "skill", "skill_cd": "SK01", "level": 5}', 100, 'epic'),
    ('BADGE_FIRST_INTERN', '泥??명꽩??, 'First Internship', '?명꽩???꾨줈洹몃옩 ?꾨즺', 'achievement', '{"type": "opportunity", "opportunity_type": "internship"}', 50, 'uncommon'),
    ('BADGE_GPA_HIGH', '?곕벑??, 'Honor Student', 'GPA 4.0 ?댁긽 ?ъ꽦', 'milestone', '{"type": "gpa", "min_gpa": 4.0}', 80, 'rare'),
    ('BADGE_CONTEST_WIN', '怨듬え???섏긽', 'Contest Winner', '怨듬え???낆긽 ?ъ꽦', 'achievement', '{"type": "contest", "result": "winner"}', 70, 'rare'),
    ('BADGE_FULL_COMPETENCY', '??웾 ?꾩꽦', 'Competency Complete', '紐⑤뱺 ??웾 80???댁긽', 'competency', '{"type": "competency", "min_score": 80}', 150, 'legendary')
ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'P1/P2 Extensions tables created successfully!';
    RAISE NOTICE 'Tables created: 24 new tables for Phase 7-13';
END $$;
