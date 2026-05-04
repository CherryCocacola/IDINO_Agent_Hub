-- ============================================================
-- 11_coaching_schema_fix.sql
-- Fix coaching tables schema to match coaching-service code
-- Date: 2026-01-15
-- ============================================================

-- Set schema
SET search_path TO idino_career, public;

-- ============================================================
-- Drop existing coaching tables (with CASCADE for dependencies)
-- ============================================================

DROP TABLE IF EXISTS tb_coaching_retrospective CASCADE;
DROP TABLE IF EXISTS tb_coaching_checkin CASCADE;
DROP TABLE IF EXISTS tb_coaching_plan CASCADE;
DROP TABLE IF EXISTS tb_coaching_goal CASCADE;

-- ============================================================
-- Create new coaching tables matching service schema
-- ============================================================

-- Coaching Goal Table
CREATE TABLE tb_coaching_goal (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    std_id VARCHAR(20) REFERENCES tb_student(student_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    goal_type VARCHAR(30) NOT NULL DEFAULT 'career',  -- career, skill, academic, personal
    priority VARCHAR(20) DEFAULT 'medium',  -- high, medium, low
    target_date DATE,
    target_role_cd VARCHAR(20),
    related_skills TEXT[],
    success_criteria TEXT,
    motivation TEXT,
    status VARCHAR(20) DEFAULT 'active',  -- draft, active, paused, completed, abandoned
    progress_percentage INT DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

-- Add comments
COMMENT ON TABLE tb_coaching_goal IS 'AI Coach Loop - Goal definitions';
COMMENT ON COLUMN tb_coaching_goal.goal_type IS 'career, skill, academic, personal';
COMMENT ON COLUMN tb_coaching_goal.priority IS 'high, medium, low';
COMMENT ON COLUMN tb_coaching_goal.status IS 'draft, active, paused, completed, abandoned';

-- Coaching Plan Table (Action Items)
CREATE TABLE tb_coaching_plan (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    order_index INT DEFAULT 0,
    due_date DATE,
    estimated_hours DECIMAL(4,1),
    related_skill_cd VARCHAR(20),
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    actual_hours DECIMAL(4,1),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

COMMENT ON TABLE tb_coaching_plan IS 'AI Coach Loop - Plan items (action items)';

-- Coaching Checkin Table
CREATE TABLE tb_coaching_checkin (
    checkin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id) ON DELETE CASCADE,
    mood VARCHAR(20) NOT NULL,  -- great, good, neutral, struggling, blocked
    progress_note TEXT,
    blockers TEXT,
    next_steps TEXT,
    reflection TEXT,
    ai_feedback TEXT,
    ai_suggestions TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_coaching_checkin IS 'AI Coach Loop - Check-in records';
COMMENT ON COLUMN tb_coaching_checkin.mood IS 'great, good, neutral, struggling, blocked';

-- Coaching Retrospective Table
CREATE TABLE tb_coaching_retrospective (
    retrospective_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES tb_coaching_goal(goal_id) ON DELETE CASCADE,
    what_went_well TEXT,
    what_could_improve TEXT,
    lessons_learned TEXT,
    next_goals TEXT,
    satisfaction_rating INT DEFAULT 3 CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    ai_analysis TEXT,
    ai_recommendations TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_coaching_retrospective IS 'AI Coach Loop - Retrospective records';
COMMENT ON COLUMN tb_coaching_retrospective.satisfaction_rating IS '1-5 scale';

-- ============================================================
-- Create indexes for performance
-- ============================================================

CREATE INDEX idx_coaching_goal_std_id ON tb_coaching_goal(std_id);
CREATE INDEX idx_coaching_goal_status ON tb_coaching_goal(status);
CREATE INDEX idx_coaching_goal_type ON tb_coaching_goal(goal_type);

CREATE INDEX idx_coaching_plan_goal_id ON tb_coaching_plan(goal_id);
CREATE INDEX idx_coaching_plan_is_completed ON tb_coaching_plan(is_completed);

CREATE INDEX idx_coaching_checkin_goal_id ON tb_coaching_checkin(goal_id);
CREATE INDEX idx_coaching_checkin_created_at ON tb_coaching_checkin(created_at);

CREATE INDEX idx_coaching_retrospective_goal_id ON tb_coaching_retrospective(goal_id);

-- ============================================================
-- Insert sample data for testing
-- ============================================================

-- Sample Goals for test student (2021010001)
INSERT INTO tb_coaching_goal (std_id, title, description, goal_type, priority, target_date, status, progress_percentage)
VALUES
    ('2021010001', 'Python 데이터 분석 역량 강화',
     'Pandas, NumPy, Matplotlib를 활용한 데이터 분석 능력 향상',
     'skill', 'high', CURRENT_DATE + INTERVAL '90 days', 'active', 30),
    ('2021010001', '졸업 프로젝트 완료',
     '4학년 캡스톤 프로젝트 성공적 완료',
     'academic', 'high', CURRENT_DATE + INTERVAL '180 days', 'active', 10),
    ('2021010001', 'AI 엔지니어 취업 준비',
     '머신러닝/딥러닝 포트폴리오 구축 및 면접 준비',
     'career', 'medium', CURRENT_DATE + INTERVAL '365 days', 'active', 5);

-- Sample Plan Items
INSERT INTO tb_coaching_plan (goal_id, title, description, order_index, due_date, estimated_hours)
SELECT
    goal_id,
    'Pandas 기초 학습',
    'Pandas DataFrame 기본 조작법 익히기',
    0,
    CURRENT_DATE + INTERVAL '14 days',
    10
FROM tb_coaching_goal WHERE title LIKE '%Python%' LIMIT 1;

INSERT INTO tb_coaching_plan (goal_id, title, description, order_index, due_date, estimated_hours)
SELECT
    goal_id,
    'NumPy 배열 연산 학습',
    'NumPy 배열 생성, 연산, 인덱싱 마스터',
    1,
    CURRENT_DATE + INTERVAL '28 days',
    8
FROM tb_coaching_goal WHERE title LIKE '%Python%' LIMIT 1;

INSERT INTO tb_coaching_plan (goal_id, title, description, order_index, due_date, estimated_hours)
SELECT
    goal_id,
    'Matplotlib 시각화',
    '다양한 차트 유형으로 데이터 시각화하기',
    2,
    CURRENT_DATE + INTERVAL '42 days',
    12
FROM tb_coaching_goal WHERE title LIKE '%Python%' LIMIT 1;

-- Sample Check-ins
INSERT INTO tb_coaching_checkin (goal_id, mood, progress_note, blockers, next_steps)
SELECT
    goal_id,
    'good',
    'Pandas 기초 강의 50% 수강 완료',
    NULL,
    '이번 주 DataFrame 조작 실습 예정'
FROM tb_coaching_goal WHERE title LIKE '%Python%' LIMIT 1;

-- Verify the fix
SELECT 'Coaching tables created successfully' as status;
SELECT table_name,
       (SELECT count(*) FROM information_schema.columns c WHERE c.table_name = t.table_name AND c.table_schema = 'idino_career') as column_count
FROM information_schema.tables t
WHERE table_schema = 'idino_career'
  AND table_name LIKE 'tb_coaching%'
ORDER BY table_name;
