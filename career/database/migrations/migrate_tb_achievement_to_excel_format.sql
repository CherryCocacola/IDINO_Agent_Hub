-- ============================================
-- Migration: tb_achievement to Excel Format
-- Date: 2026-01-26
-- Purpose: Align DB schema with Excel standard format
-- ============================================

-- Schema Mapping:
-- DB (02_techspec_tables.sql)    →  Excel (Standard)
-- achievement_nm                 →  title
-- issuing_organization          →  issuer
-- acquired_date                 →  issue_date
-- expiry_date                   →  expire_date
-- score                         →  score (keep)
-- evidence_url                  →  (drop or keep as additional)
-- verified                      →  verified (keep)
-- (new)                         →  level
-- (new)                         →  competency_contributions

SET search_path TO idino_career;

-- Step 1: Add new columns if they don't exist
DO $$
BEGIN
    -- Add level column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'level') THEN
        ALTER TABLE tb_achievement ADD COLUMN level VARCHAR(50);
    END IF;

    -- Add competency_contributions column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'competency_contributions') THEN
        ALTER TABLE tb_achievement ADD COLUMN competency_contributions JSONB;
    END IF;

    -- Add title column (if achievement_nm exists, we'll rename it)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'title') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'achievement_nm') THEN
            ALTER TABLE tb_achievement RENAME COLUMN achievement_nm TO title;
        ELSE
            ALTER TABLE tb_achievement ADD COLUMN title VARCHAR(200);
        END IF;
    END IF;

    -- Add issuer column (if issuing_organization exists, we'll rename it)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'issuer') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'issuing_organization') THEN
            ALTER TABLE tb_achievement RENAME COLUMN issuing_organization TO issuer;
        ELSE
            ALTER TABLE tb_achievement ADD COLUMN issuer VARCHAR(200);
        END IF;
    END IF;

    -- Add issue_date column (if acquired_date exists, we'll rename it)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'issue_date') THEN
        IF EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'idino_career'
                   AND table_name = 'tb_achievement'
                   AND column_name = 'acquired_date') THEN
            ALTER TABLE tb_achievement RENAME COLUMN acquired_date TO issue_date;
        ELSE
            ALTER TABLE tb_achievement ADD COLUMN issue_date DATE;
        END IF;
    END IF;

    -- Rename expiry_date to expire_date if needed
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'idino_career'
               AND table_name = 'tb_achievement'
               AND column_name = 'expiry_date')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'idino_career'
                       AND table_name = 'tb_achievement'
                       AND column_name = 'expire_date') THEN
        ALTER TABLE tb_achievement RENAME COLUMN expiry_date TO expire_date;
    END IF;
END $$;

-- Step 2: Update NOT NULL constraint on title
ALTER TABLE tb_achievement ALTER COLUMN title SET NOT NULL;

-- Step 3: Add comments for clarity
COMMENT ON TABLE tb_achievement IS 'Student achievements: certificates, language scores, awards, publications (Excel format standard)';
COMMENT ON COLUMN tb_achievement.title IS 'Achievement name/title (Excel: title)';
COMMENT ON COLUMN tb_achievement.issuer IS 'Issuing organization (Excel: issuer)';
COMMENT ON COLUMN tb_achievement.issue_date IS 'Date of acquisition (Excel: issue_date)';
COMMENT ON COLUMN tb_achievement.expire_date IS 'Expiration date if applicable (Excel: expire_date)';
COMMENT ON COLUMN tb_achievement.level IS 'Achievement level/grade (Excel: level)';
COMMENT ON COLUMN tb_achievement.score IS 'Numeric score if applicable';
COMMENT ON COLUMN tb_achievement.competency_contributions IS 'JSON mapping of competency contributions (Excel: competency_contributions)';

-- Verify migration
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'idino_career' AND table_name = 'tb_achievement'
ORDER BY ordinal_position;
