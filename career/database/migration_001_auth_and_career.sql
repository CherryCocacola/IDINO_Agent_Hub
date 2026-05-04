-- ============================================
-- Migration 001: Authentication System & Career Data Separation
-- ============================================
--
-- ?ㅽ뻾 諛⑸쾿:
-- psql -h localhost -p 5432 -U postgres -d postgres -f migration_001_auth_and_career.sql
--
-- 蹂寃??ы빆:
-- 1. ?ъ슜???몄쬆 ?뚯씠釉??앹꽦 (tb_user, tb_auth_*)
-- 2. 濡쒓렇??愿???뚯씠釉??앹꽦 (tb_login_*)
-- 3. Career ?곗씠??遺꾨━ (tb_student_career)
-- 4. 湲곗〈 tb_student???由대젅?댁뀡 ?ㅼ젙
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- PART 1: User Authentication Tables
-- ============================================

-- ?ъ슜??怨꾩젙 ?뚯씠釉?(?숈깮/援먯닔/愿由ъ옄 ?듯빀)
CREATE TABLE IF NOT EXISTS tb_user (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    login_id VARCHAR(50) UNIQUE NOT NULL,           -- 濡쒓렇??ID (?숇쾲, 援먮쾲, ?대찓??
    password_hash VARCHAR(255) NOT NULL,            -- bcrypt ?댁떆
    password_salt VARCHAR(64),                       -- 異붽? ?뷀듃 (?듭뀡)
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('student', 'professor', 'advisor', 'admin', 'career_admin')),

    -- ?곌껐 ??(user_type???곕씪 ?섎굹留??ъ슜)
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),

    -- 怨꾩젙 ?곹깭
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked', 'pending')),
    email VARCHAR(100) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20),
    phone_verified BOOLEAN DEFAULT FALSE,

    -- 2FA ?ㅼ젙
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_type VARCHAR(20) CHECK (mfa_type IN ('totp', 'email', 'sms', 'both')),
    totp_secret VARCHAR(64),                        -- TOTP 鍮꾨???(?뷀샇?????
    totp_verified BOOLEAN DEFAULT FALSE,

    -- 蹂댁븞 ?뺤콉
    password_changed_at TIMESTAMP,
    password_expires_at TIMESTAMP,
    failed_login_count INT DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(50),

    -- ?쎄? ?숈쓽
    terms_agreed_at TIMESTAMP,
    privacy_agreed_at TIMESTAMP,
    marketing_agreed BOOLEAN DEFAULT FALSE,

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
    upd_menu_cd VARCHAR(20)
);

COMMENT ON TABLE tb_user IS '?ъ슜???몄쬆 ?뺣낫 ?뚯씠釉?- ?숈깮/援먯닔/愿由ъ옄 ?듯빀 怨꾩젙 愿由?;
COMMENT ON COLUMN tb_user.totp_secret IS 'TOTP 鍮꾨???(AES-256 ?뷀샇???????';

-- ============================================
-- PART 2: Session & Token Management
-- ============================================

-- ?몄뀡 ?뚯씠釉?(JWT ?좏겙 愿由?
CREATE TABLE IF NOT EXISTS tb_auth_session (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    -- ?좏겙 ?뺣낫
    access_token_hash VARCHAR(64),                  -- SHA256 ?댁떆
    refresh_token_hash VARCHAR(64) UNIQUE,          -- SHA256 ?댁떆

    -- ?몄뀡 ?뺣낫
    device_id VARCHAR(100),
    device_type VARCHAR(50),                        -- web, mobile, tablet
    device_name VARCHAR(100),                       -- Chrome on Windows, Safari on iPhone
    user_agent TEXT,
    ip_address VARCHAR(50),

    -- ?곹깭
    is_active BOOLEAN DEFAULT TRUE,
    mfa_verified BOOLEAN DEFAULT FALSE,             -- 2FA ?꾨즺 ?щ?

    -- ?쒓컙
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(100),

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_session_user ON tb_auth_session(user_id);
CREATE INDEX idx_auth_session_refresh ON tb_auth_session(refresh_token_hash);
CREATE INDEX idx_auth_session_active ON tb_auth_session(user_id, is_active);

-- ============================================
-- PART 3: 2FA OTP Management
-- ============================================

-- OTP 肄붾뱶 ?뚯씠釉?(Email, SMS OTP??
CREATE TABLE IF NOT EXISTS tb_auth_otp (
    otp_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    -- OTP ?뺣낫
    otp_type VARCHAR(20) NOT NULL CHECK (otp_type IN ('email', 'sms', 'password_reset', 'email_verify', 'phone_verify')),
    otp_code VARCHAR(10) NOT NULL,                  -- 6?먮━ 肄붾뱶
    otp_hash VARCHAR(64),                           -- SHA256 ?댁떆 (蹂댁븞 媛뺥솕)

    -- ?꾩넚 ???    target_email VARCHAR(100),
    target_phone VARCHAR(20),

    -- ?곹깭
    is_used BOOLEAN DEFAULT FALSE,
    attempt_count INT DEFAULT 0,                    -- 寃利??쒕룄 ?잛닔
    max_attempts INT DEFAULT 5,                     -- 理쒕? ?쒕룄 ?잛닔

    -- ?쒓컙
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,                  -- 蹂댄넻 5遺?    used_at TIMESTAMP,

    -- 蹂댁븞
    request_ip VARCHAR(50),
    verification_ip VARCHAR(50),

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_otp_user ON tb_auth_otp(user_id, otp_type);
CREATE INDEX idx_auth_otp_code ON tb_auth_otp(otp_code, otp_type, is_used);

-- TOTP 諛깆뾽 肄붾뱶 ?뚯씠釉?CREATE TABLE IF NOT EXISTS tb_auth_backup_code (
    code_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    code_hash VARCHAR(64) NOT NULL,                 -- SHA256 ?댁떆
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    used_ip VARCHAR(50),

    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_auth_backup_user ON tb_auth_backup_code(user_id, is_used);

-- ============================================
-- PART 4: Login History & Security Audit
-- ============================================

-- 濡쒓렇???대젰 ?뚯씠釉?CREATE TABLE IF NOT EXISTS tb_login_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES tb_user(user_id),
    login_id VARCHAR(50) NOT NULL,                  -- 濡쒓렇???쒕룄??ID (?ㅽ뙣?대룄 湲곕줉)

    -- 濡쒓렇??寃곌낵
    login_result VARCHAR(20) NOT NULL CHECK (login_result IN (
        'success',           -- 濡쒓렇???깃났
        'mfa_pending',       -- 2FA ?湲?        'mfa_success',       -- 2FA ?깃났
        'mfa_failed',        -- 2FA ?ㅽ뙣
        'failed_password',   -- 鍮꾨?踰덊샇 ?ㅻ쪟
        'failed_mfa',        -- 2FA 肄붾뱶 ?ㅻ쪟
        'account_locked',    -- 怨꾩젙 ?좉?
        'account_inactive',  -- 鍮꾪솢??怨꾩젙
        'user_not_found'     -- ?ъ슜???놁쓬
    )),

    -- ?묒냽 ?뺣낫
    ip_address VARCHAR(50),
    user_agent TEXT,
    device_type VARCHAR(50),
    device_fingerprint VARCHAR(100),

    -- ?꾩튂 ?뺣낫 (?듭뀡)
    geo_country VARCHAR(50),
    geo_city VARCHAR(100),

    -- 蹂댁븞 ?뚮옒洹?    is_suspicious BOOLEAN DEFAULT FALSE,
    risk_score INT DEFAULT 0,                       -- 0-100 ?꾪뿕???먯닔

    -- ?쒓컙
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Audit
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_login_history_user ON tb_login_history(user_id, attempted_at DESC);
CREATE INDEX idx_login_history_ip ON tb_login_history(ip_address, attempted_at DESC);
CREATE INDEX idx_login_history_result ON tb_login_history(login_result, attempted_at DESC);

-- ?좊ː 湲곌린 ?뚯씠釉?CREATE TABLE IF NOT EXISTS tb_user_device (
    device_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    -- 湲곌린 ?뺣낫
    device_fingerprint VARCHAR(100) UNIQUE NOT NULL,
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    browser VARCHAR(50),
    os VARCHAR(50),

    -- ?좊ː ?곹깭
    is_trusted BOOLEAN DEFAULT FALSE,
    trust_level INT DEFAULT 0,                      -- 0-3 ?좊ː ?덈꺼

    -- ?쒓컙
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trusted_at TIMESTAMP,

    -- ?꾩튂
    last_ip VARCHAR(50),
    last_location VARCHAR(100),

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

CREATE INDEX idx_user_device_user ON tb_user_device(user_id);
CREATE INDEX idx_user_device_fp ON tb_user_device(device_fingerprint);

-- ============================================
-- PART 5: Career Data Separation
-- ============================================

-- ?숈깮 吏꾨줈 ?뺣낫 ?뚯씠釉?(tb_student?먯꽌 遺꾨━)
CREATE TABLE IF NOT EXISTS tb_student_career (
    career_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL REFERENCES tb_student(student_id) ON DELETE CASCADE,

    -- ?щ쭩 吏꾨줈 (Primary)
    primary_career_goal VARCHAR(200),               -- 二??щ쭩 吏곷Т
    primary_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),

    -- 愿??吏곷Т (Multiple)
    interest_role_cds VARCHAR(20)[],                -- 愿??吏곷Т 紐⑸줉
    interest_industries VARCHAR(100)[],             -- 愿???곗뾽

    -- ?좏샇??    preferred_company_size VARCHAR(20) CHECK (preferred_company_size IN ('startup', 'sme', 'midsize', 'large', 'any')),
    preferred_work_style VARCHAR(20) CHECK (preferred_work_style IN ('office', 'remote', 'hybrid', 'any')),
    preferred_regions VARCHAR(50)[],                -- ?좏샇 吏??
    -- 以鍮??곹깭
    resume_prepared BOOLEAN DEFAULT FALSE,
    portfolio_prepared BOOLEAN DEFAULT FALSE,
    interview_ready BOOLEAN DEFAULT FALSE,

    -- ??꾨씪??    job_search_start_date DATE,                     -- 援ъ쭅 ?쒖옉 ?덉젙??    target_employment_date DATE,                    -- 痍⑥뾽 紐⑺몴??
    -- 異붽? ?뺣낫
    career_notes TEXT,                              -- 吏꾨줈 愿??硫붾え
    advisor_comments TEXT,                          -- 吏?꾧탳??肄붾찘??
    -- 留덉?留??곷떞
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

    -- ???숈깮???섎굹??吏꾨줈 ?뺣낫留?    UNIQUE(student_id)
);

COMMENT ON TABLE tb_student_career IS '?숈깮 吏꾨줈 ?뺣낫 ?뚯씠釉?- tb_student?먯꽌 career_goal 遺꾨━';

CREATE INDEX idx_student_career_student ON tb_student_career(student_id);
CREATE INDEX idx_student_career_role ON tb_student_career(primary_role_cd);

-- 吏꾨줈 ?щ쭩 ?대젰 ?뚯씠釉?(蹂寃??대젰 異붿쟻)
CREATE TABLE IF NOT EXISTS tb_career_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(20) NOT NULL REFERENCES tb_student(student_id) ON DELETE CASCADE,

    -- 蹂寃??꾪썑
    previous_career_goal VARCHAR(200),
    new_career_goal VARCHAR(200),
    previous_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),
    new_role_cd VARCHAR(20) REFERENCES tb_role(role_cd),

    -- 蹂寃??ъ쑀
    change_reason TEXT,
    triggered_by VARCHAR(50),                       -- 'student', 'advisor', 'system'

    -- ?쒓컙
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_career_history_student ON tb_career_history(student_id, changed_at DESC);

-- ============================================
-- PART 6: Data Migration
-- ============================================

-- 6.1 湲곗〈 tb_student??career_goal??tb_student_career濡?留덉씠洹몃젅?댁뀡
INSERT INTO tb_student_career (student_id, primary_career_goal, ins_user_id, ins_dt)
SELECT
    student_id,
    career_goal,
    'MIGRATION',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE career_goal IS NOT NULL
ON CONFLICT (student_id) DO NOTHING;

-- 6.2 career_goal?먯꽌 role_cd 留ㅽ븨 (?쒓? 吏곷Т紐???role_cd)
UPDATE tb_student_career sc
SET primary_role_cd = r.role_cd
FROM tb_role r
WHERE sc.primary_career_goal LIKE '%' || r.role_nm || '%'
   OR sc.primary_career_goal = r.role_nm;

-- 6.3 ?ъ슜??怨꾩젙 ?앹꽦 (?숈깮)
-- 湲곕낯 鍮꾨?踰덊샇: ?숇쾲 + 'kust!' ??bcrypt ?댁떆??蹂꾨룄 泥섎━ ?꾩슂
INSERT INTO tb_user (
    login_id,
    password_hash,
    user_type,
    student_id,
    email,
    status,
    ins_user_id,
    ins_dt
)
SELECT
    s.student_id AS login_id,
    -- ?꾩떆 ?댁떆 (?ㅼ젣濡쒕뒗 bcrypt('?숇쾲+kust!') ?ъ슜)
    '$2b$12$PLACEHOLDER_HASH_NEEDS_UPDATE' AS password_hash,
    'student' AS user_type,
    s.student_id,
    COALESCE(s.email, s.student_id || '@kust.ac.kr'),
    'pending' AS status,  -- 泥?濡쒓렇????鍮꾨?踰덊샇 蹂寃??꾩슂
    'MIGRATION',
    CURRENT_TIMESTAMP
FROM tb_student s
ON CONFLICT (login_id) DO NOTHING;

-- 6.4 ?ъ슜??怨꾩젙 ?앹꽦 (援먯닔)
INSERT INTO tb_user (
    login_id,
    password_hash,
    user_type,
    professor_cd,
    email,
    status,
    ins_user_id,
    ins_dt
)
SELECT
    p.professor_cd AS login_id,
    '$2b$12$PLACEHOLDER_HASH_NEEDS_UPDATE' AS password_hash,
    'professor' AS user_type,
    p.professor_cd,
    COALESCE(p.email, p.professor_cd || '@kust.ac.kr'),
    'pending' AS status,
    'MIGRATION',
    CURRENT_TIMESTAMP
FROM tb_professor p
ON CONFLICT (login_id) DO NOTHING;

-- ============================================
-- PART 7: Views for Backward Compatibility
-- ============================================

-- ?숈깮 ?뺣낫 + 吏꾨줈 ?뺣낫 ?듯빀 酉?CREATE OR REPLACE VIEW vw_student_with_career AS
SELECT
    s.*,
    sc.primary_career_goal,
    sc.primary_role_cd,
    sc.interest_role_cds,
    sc.preferred_company_size,
    sc.preferred_work_style,
    sc.job_search_start_date,
    sc.target_employment_date,
    r.role_nm AS primary_role_nm,
    r.category AS primary_role_category
FROM tb_student s
LEFT JOIN tb_student_career sc ON s.student_id = sc.student_id
LEFT JOIN tb_role r ON sc.primary_role_cd = r.role_cd;

COMMENT ON VIEW vw_student_with_career IS '?숈깮 ?뺣낫? 吏꾨줈 ?뺣낫 ?듯빀 酉?(?섏쐞 ?명솚??';

-- ?ъ슜???몄쬆 ?뺣낫 酉?CREATE OR REPLACE VIEW vw_user_auth_info AS
SELECT
    u.user_id,
    u.login_id,
    u.user_type,
    u.status,
    u.email,
    u.email_verified,
    u.mfa_enabled,
    u.mfa_type,
    u.totp_verified,
    u.failed_login_count,
    u.locked_until,
    u.last_login_at,
    u.last_login_ip,
    CASE u.user_type
        WHEN 'student' THEN s.student_nm
        WHEN 'professor' THEN p.professor_nm
        ELSE u.login_id
    END AS user_nm,
    CASE u.user_type
        WHEN 'student' THEN d1.department_nm
        WHEN 'professor' THEN d2.department_nm
        ELSE NULL
    END AS department_nm
FROM tb_user u
LEFT JOIN tb_student s ON u.student_id = s.student_id
LEFT JOIN tb_professor p ON u.professor_cd = p.professor_cd
LEFT JOIN tb_department d1 ON s.department_cd = d1.department_cd
LEFT JOIN tb_department d2 ON p.department_cd = d2.department_cd;

COMMENT ON VIEW vw_user_auth_info IS '?ъ슜???몄쬆 ?뺣낫 ?듯빀 酉?;

-- ============================================
-- PART 8: Indexes for Performance
-- ============================================

CREATE INDEX idx_user_login_id ON tb_user(login_id);
CREATE INDEX idx_user_student ON tb_user(student_id) WHERE student_id IS NOT NULL;
CREATE INDEX idx_user_professor ON tb_user(professor_cd) WHERE professor_cd IS NOT NULL;
CREATE INDEX idx_user_status ON tb_user(status);
CREATE INDEX idx_user_type ON tb_user(user_type);

-- ============================================
-- PART 9: Comments & Documentation
-- ============================================

COMMENT ON COLUMN tb_user.mfa_type IS 'totp: Google Authenticator, email: ?대찓??OTP, sms: SMS OTP, both: TOTP + 諛깆뾽';
COMMENT ON COLUMN tb_login_history.risk_score IS '濡쒓렇???꾪뿕???먯닔 (0-100): ?덇린湲??덉쐞移?+30, ?댁쇅?묒냽=+40, ?쇨컙?묒냽=+10';
COMMENT ON COLUMN tb_user_device.trust_level IS '?좊ː ?덈꺼: 0=?덇린湲? 1=?뺤씤?? 2=?먯＜?ъ슜, 3=?좊ː??2FA?ㅽ궢媛??';

-- ============================================
-- Summary
-- ============================================
-- ?앹꽦???뚯씠釉?
-- 1. tb_user - ?ъ슜???몄쬆 ?뺣낫
-- 2. tb_auth_session - ?몄뀡/?좏겙 愿由?-- 3. tb_auth_otp - OTP 肄붾뱶 愿由?-- 4. tb_auth_backup_code - TOTP 諛깆뾽 肄붾뱶
-- 5. tb_login_history - 濡쒓렇???대젰
-- 6. tb_user_device - ?좊ː 湲곌린
-- 7. tb_student_career - ?숈깮 吏꾨줈 ?뺣낫
-- 8. tb_career_history - 吏꾨줈 蹂寃??대젰
--
-- ?앹꽦??酉?
-- 1. vw_student_with_career - ?숈깮+吏꾨줈 ?듯빀 酉?-- 2. vw_user_auth_info - ?ъ슜???몄쬆 ?뺣낫 酉?
