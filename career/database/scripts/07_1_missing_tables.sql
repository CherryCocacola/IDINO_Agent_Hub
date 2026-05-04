-- =====================================================
-- IDINO Career - Missing Tables DDL
-- Creates tb_portfolio, tb_roadmap, tb_roadmap_item
-- =====================================================

-- Set schema
SET search_path TO idino_career;

-- =====================================================
-- 1. tb_portfolio - Portfolio items for students
-- =====================================================
CREATE TABLE IF NOT EXISTS tb_portfolio (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) NOT NULL,
    item_type VARCHAR(50) NOT NULL, -- project, certificate, award, activity, experience
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    skills_used JSONB,
    evidence_url VARCHAR(500),
    image_url VARCHAR(500),
    is_featured CHAR(1) DEFAULT 'N',
    display_order INT DEFAULT 0,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    CONSTRAINT fk_portfolio_student FOREIGN KEY (student_id)
        REFERENCES tb_student(student_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_portfolio_student ON tb_portfolio(student_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_type ON tb_portfolio(item_type);

COMMENT ON TABLE tb_portfolio IS 'Student portfolio items - projects, certificates, awards, activities';
COMMENT ON COLUMN tb_portfolio.item_type IS 'Type: project, certificate, award, activity, experience';
COMMENT ON COLUMN tb_portfolio.skills_used IS 'JSON array of skill codes used in this item';
COMMENT ON COLUMN tb_portfolio.is_featured IS 'Y=Featured item, N=Normal';

-- =====================================================
-- 2. tb_roadmap - Career development roadmap per student
-- =====================================================
CREATE TABLE IF NOT EXISTS tb_roadmap (
    roadmap_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_role VARCHAR(100),
    target_company VARCHAR(100),
    target_year INT,
    status VARCHAR(20) DEFAULT 'active', -- active, completed, archived
    progress_percent INT DEFAULT 0,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    CONSTRAINT fk_roadmap_student FOREIGN KEY (student_id)
        REFERENCES tb_student(student_id),
    CONSTRAINT uq_roadmap_student UNIQUE (student_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_roadmap_student ON tb_roadmap(student_id);

COMMENT ON TABLE tb_roadmap IS 'Career development roadmap per student (one per student)';
COMMENT ON COLUMN tb_roadmap.target_role IS 'Target career role (e.g., Backend Developer)';
COMMENT ON COLUMN tb_roadmap.progress_percent IS 'Overall roadmap completion percentage';

-- =====================================================
-- 3. tb_roadmap_item - Individual items in a roadmap
-- =====================================================
CREATE TABLE IF NOT EXISTS tb_roadmap_item (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id UUID NOT NULL,
    category VARCHAR(50) NOT NULL, -- course, certification, skill, activity, internship
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_grade INT CHECK (target_grade BETWEEN 1 AND 4),
    target_semester INT CHECK (target_semester BETWEEN 1 AND 2),
    status VARCHAR(20) DEFAULT 'planned', -- planned, in_progress, completed, skipped
    priority INT DEFAULT 0, -- Higher = more important
    display_order INT DEFAULT 0,
    due_date DATE,
    completed_date DATE,
    notes TEXT,
    -- Audit columns
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP,
    CONSTRAINT fk_roadmap_item_roadmap FOREIGN KEY (roadmap_id)
        REFERENCES tb_roadmap(roadmap_id) ON DELETE CASCADE
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_roadmap_item_roadmap ON tb_roadmap_item(roadmap_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_item_category ON tb_roadmap_item(category);
CREATE INDEX IF NOT EXISTS idx_roadmap_item_grade_sem ON tb_roadmap_item(target_grade, target_semester);

COMMENT ON TABLE tb_roadmap_item IS 'Individual items in career roadmap';
COMMENT ON COLUMN tb_roadmap_item.category IS 'Type: course, certification, skill, activity, internship';
COMMENT ON COLUMN tb_roadmap_item.target_grade IS 'Target academic year (1-4)';
COMMENT ON COLUMN tb_roadmap_item.target_semester IS 'Target semester (1 or 2)';

-- =====================================================
-- Verification
-- =====================================================
SELECT 'tb_portfolio created' as status WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tb_portfolio');
SELECT 'tb_roadmap created' as status WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tb_roadmap');
SELECT 'tb_roadmap_item created' as status WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tb_roadmap_item');
