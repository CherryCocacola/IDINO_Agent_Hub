-- ============================================
-- MFA 활성화된 테스트 사용자 생성
-- ============================================
-- 실행 방법:
-- set PGPASSWORD=2012 && psql -h localhost -p 5432 -U postgres -d postgres -f "E:\workspace\idino_career\database\scripts\06_seed_mfa_test_user.sql"
--
-- 테스트 자격증명:
-- Login ID: 2021010001
-- Password: 1234
-- TOTP Secret: 4OG4ZZFCVLVTGVZ6WQRMBFEK2KXRUPYJ
-- ============================================

SET search_path TO idino_career, public;

-- 1. 기존 사용자 삭제 (재실행 가능하도록)
DELETE FROM tb_user WHERE login_id = '2021010001';

-- 2. MFA 활성화된 학생 사용자 생성
-- NOTE: 실제 DB 스키마에 맞춤 (mfa_secret, user_nm 사용)
INSERT INTO tb_user (
    user_id,
    login_id,
    password_hash,
    user_nm,
    email,
    user_type,
    student_id,
    role,
    status,
    mfa_enabled,
    mfa_secret,
    ins_user_id,
    ins_dt
) VALUES (
    uuid_generate_v4(),
    '2021010001',                                                -- login_id = 학번
    '$2b$12$1OGVs0Oue9x.OvIue3vYMeGPmdSgZVplQdu9vLt3Kyl/a57WlP2fO',  -- password: '1234'
    '김민준',                                                     -- user_nm
    'minjun.kim@kust.ac.kr',
    'student',
    '2021010001',                                                -- student_id
    'user',                                                      -- role
    'active',
    TRUE,                                                        -- MFA 활성화
    '4OG4ZZFCVLVTGVZ6WQRMBFEK2KXRUPYJ',                         -- mfa_secret (TOTP)
    'SYSTEM',
    CURRENT_TIMESTAMP
);

-- 확인 쿼리
SELECT
    login_id,
    user_nm,
    student_id,
    user_type,
    status,
    mfa_enabled,
    CASE WHEN mfa_secret IS NOT NULL THEN 'SET' ELSE 'NOT SET' END as mfa_secret_status
FROM tb_user
WHERE login_id = '2021010001';

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '======================================';
    RAISE NOTICE 'MFA 테스트 사용자 생성 완료';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE 'Login ID: 2021010001';
    RAISE NOTICE 'Password: 1234';
    RAISE NOTICE 'MFA: TOTP 활성화';
    RAISE NOTICE '';
    RAISE NOTICE 'TOTP 코드 생성:';
    RAISE NOTICE 'python -c "import pyotp; print(pyotp.TOTP(''4OG4ZZFCVLVTGVZ6WQRMBFEK2KXRUPYJ'').now())"';
    RAISE NOTICE '======================================';
END $$;
