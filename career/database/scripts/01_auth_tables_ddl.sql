-- ============================================
-- 01. 인증/로그인 테이블 DDL
-- ============================================
-- ⚠️ 주의: migration_001_auth_and_career.sql이 이미 실행된 경우
--          이 스크립트는 실행하지 마세요!
--          migration_001이 최신 스키마를 포함하고 있습니다.
--
-- 실행 전 run_database_setup.sql 먼저 실행 필요
--
-- 2FA 추천:
-- ┌─────────────────┬────────────┬────────────┬────────────────┬─────────────┐
-- │ 방식            │ 보안성     │ 사용자편의 │ 구현복잡도     │ 추천        │
-- ├─────────────────┼────────────┼────────────┼────────────────┼─────────────┤
-- │ TOTP (권장)     │ ★★★★★    │ ★★★★☆    │ ★★★☆☆        │ ✅ Primary  │
-- │ Email OTP       │ ★★★☆☆    │ ★★★★★    │ ★★☆☆☆        │ ✅ Backup   │
-- │ SMS OTP         │ ★★★☆☆    │ ★★★★☆    │ ★★★★☆        │ ❌ 비용높음 │
-- │ WebAuthn/FIDO2  │ ★★★★★    │ ★★★☆☆    │ ★★★★★        │ ❌ 복잡     │
-- └─────────────────┴────────────┴────────────┴────────────────┴─────────────┘
--
-- 최종 추천: TOTP (Google Authenticator) + Email OTP (백업용)
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. 사용자 계정 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS tb_user (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    login_id VARCHAR(50) UNIQUE NOT NULL,           -- 로그인 ID (학번, 교번, 이메일)
    password_hash VARCHAR(255) NOT NULL,            -- bcrypt 해시
    password_salt VARCHAR(64),                       -- 추가 솔트 (옵션)
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('student', 'professor', 'advisor', 'admin', 'career_admin')),

    -- 연결 키 (user_type에 따라 하나만 사용)
    student_id VARCHAR(20) REFERENCES tb_student(student_id),
    professor_cd VARCHAR(20) REFERENCES tb_professor(professor_cd),

    -- 계정 상태
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked', 'pending')),
    email VARCHAR(100) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    phone VARCHAR(20),
    phone_verified BOOLEAN DEFAULT FALSE,

    -- 2FA 설정
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_type VARCHAR(20) CHECK (mfa_type IN ('totp', 'email', 'sms', 'both')),
    totp_secret VARCHAR(64),                        -- TOTP 비밀키 (암호화 저장)
    totp_verified BOOLEAN DEFAULT FALSE,

    -- 보안 정책
    password_changed_at TIMESTAMP,
    password_expires_at TIMESTAMP,
    failed_login_count INT DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(50),

    -- 약관 동의
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

COMMENT ON TABLE tb_user IS '사용자 인증 정보 테이블 - 학생/교수/관리자 통합 계정 관리';
COMMENT ON COLUMN tb_user.totp_secret IS 'TOTP 비밀키 (AES-256 암호화 후 저장 권장)';
COMMENT ON COLUMN tb_user.mfa_type IS 'totp: Google Authenticator, email: 이메일 OTP, both: TOTP+Email';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_user_login_id ON tb_user(login_id);
CREATE INDEX IF NOT EXISTS idx_user_email ON tb_user(email);
CREATE INDEX IF NOT EXISTS idx_user_student_id ON tb_user(student_id);
CREATE INDEX IF NOT EXISTS idx_user_status ON tb_user(status);

-- ============================================
-- 2. 세션 테이블 (JWT 토큰 관리)
-- ============================================
CREATE TABLE IF NOT EXISTS tb_auth_session (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    -- 토큰 정보
    access_token_hash VARCHAR(64),                  -- SHA256 해시
    refresh_token_hash VARCHAR(64) UNIQUE,          -- SHA256 해시

    -- 세션 정보
    device_id VARCHAR(100),
    device_type VARCHAR(50),                        -- web, mobile, tablet
    device_name VARCHAR(100),                       -- Chrome on Windows, Safari on iPhone
    user_agent TEXT,
    ip_address VARCHAR(50),

    -- 상태
    is_active BOOLEAN DEFAULT TRUE,
    mfa_verified BOOLEAN DEFAULT FALSE,             -- 2FA 완료 여부

    -- 시간
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    revoked_reason VARCHAR(100),

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_auth_session IS 'JWT 세션 관리 테이블 - Access Token 15분, Refresh Token 7일';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_session_user_id ON tb_auth_session(user_id);
CREATE INDEX IF NOT EXISTS idx_session_refresh_token ON tb_auth_session(refresh_token_hash);
CREATE INDEX IF NOT EXISTS idx_session_active ON tb_auth_session(is_active, expires_at);

-- ============================================
-- 3. OTP 테이블 (Email/SMS OTP)
-- ============================================
CREATE TABLE IF NOT EXISTS tb_auth_otp (
    otp_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    -- OTP 정보
    otp_type VARCHAR(20) NOT NULL CHECK (otp_type IN ('email', 'sms', 'login_verify', 'password_reset', 'email_verify')),
    otp_code VARCHAR(10) NOT NULL,                  -- 6자리 코드
    otp_hash VARCHAR(64),                           -- SHA256 해시 (옵션)

    -- 전송 대상
    target_email VARCHAR(100),
    target_phone VARCHAR(20),

    -- 상태
    is_used BOOLEAN DEFAULT FALSE,
    attempt_count INT DEFAULT 0,
    max_attempts INT DEFAULT 5,

    -- 시간
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,

    -- 요청 정보
    request_ip VARCHAR(50),
    verification_ip VARCHAR(50),

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_auth_otp IS 'Email/SMS OTP 관리 테이블 - 유효시간 5분';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_otp_user_id ON tb_auth_otp(user_id);
CREATE INDEX IF NOT EXISTS idx_otp_type ON tb_auth_otp(otp_type, is_used);

-- ============================================
-- 4. TOTP 백업 코드 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS tb_auth_backup_code (
    code_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    code_hash VARCHAR(64) NOT NULL,                 -- SHA256 해시
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    used_ip VARCHAR(50),

    -- Audit
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_auth_backup_code IS 'TOTP 2FA 백업 코드 테이블 - 사용자당 10개 발급';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_backup_code_user_id ON tb_auth_backup_code(user_id);

-- ============================================
-- 5. 로그인 이력 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS tb_login_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES tb_user(user_id) ON DELETE SET NULL,
    login_id VARCHAR(50) NOT NULL,                  -- 로그인 시도한 ID

    -- 결과
    login_result VARCHAR(20) NOT NULL CHECK (login_result IN ('success', 'failed', 'locked', 'mfa_required', 'mfa_failed')),
    failure_reason VARCHAR(100),                    -- 실패 이유

    -- 접속 정보
    ip_address VARCHAR(50),
    user_agent TEXT,
    device_type VARCHAR(50),
    device_fingerprint VARCHAR(100),

    -- 보안 분석
    is_suspicious BOOLEAN DEFAULT FALSE,
    risk_score INT DEFAULT 0,                       -- 0-100 위험 점수

    -- 지역 정보
    geo_country VARCHAR(50),
    geo_city VARCHAR(100),

    -- 시간
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE tb_login_history IS '로그인 시도 이력 테이블 - 보안 감사용';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON tb_login_history(user_id);
CREATE INDEX IF NOT EXISTS idx_login_history_login_id ON tb_login_history(login_id);
CREATE INDEX IF NOT EXISTS idx_login_history_time ON tb_login_history(attempted_at);
CREATE INDEX IF NOT EXISTS idx_login_history_suspicious ON tb_login_history(is_suspicious);

-- ============================================
-- 6. 신뢰 기기 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS tb_user_device (
    device_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,

    -- 기기 정보
    device_fingerprint VARCHAR(100) UNIQUE,
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    browser VARCHAR(50),
    os VARCHAR(50),

    -- 신뢰 설정
    is_trusted BOOLEAN DEFAULT FALSE,
    trust_level INT DEFAULT 0,                      -- 0: 미신뢰, 1: 기본, 2: 신뢰, 3: 완전신뢰
    trusted_at TIMESTAMP,

    -- 접속 정보
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_ip VARCHAR(50),
    login_count INT DEFAULT 0,

    -- Audit
    ins_user_id VARCHAR(50),
    ins_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    upd_user_id VARCHAR(50),
    upd_dt TIMESTAMP
);

COMMENT ON TABLE tb_user_device IS '사용자 기기 관리 테이블 - 신뢰 기기는 2FA 스킵 가능';

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_device_user_id ON tb_user_device(user_id);
CREATE INDEX IF NOT EXISTS idx_device_fingerprint ON tb_user_device(device_fingerprint);

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '======================================';
    RAISE NOTICE '인증/로그인 테이블 생성 완료';
    RAISE NOTICE '- tb_user: 사용자 계정';
    RAISE NOTICE '- tb_auth_session: JWT 세션';
    RAISE NOTICE '- tb_auth_otp: Email/SMS OTP';
    RAISE NOTICE '- tb_auth_backup_code: TOTP 백업코드';
    RAISE NOTICE '- tb_login_history: 로그인 이력';
    RAISE NOTICE '- tb_user_device: 신뢰 기기';
    RAISE NOTICE '======================================';
END $$;
