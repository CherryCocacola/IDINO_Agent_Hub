-- ============================================
-- 대상 사용자들 MFA 활성화
-- ============================================
-- 실행 방법:
-- set PGPASSWORD=2012 && psql -h localhost -p 5432 -U postgres -d postgres -f "E:\workspace\idino_career\database\scripts\07_enable_mfa_target_users.sql"
--
-- 대상 사용자: 2020010000, 2020010020, 2020020025, 2020020045, 2020030050, 2020040075, 2020050000
-- ============================================

SET search_path TO idino_career, public;

-- 1. 대상 사용자별 MFA 활성화 및 TOTP 비밀키 설정
-- 각 사용자마다 고유한 TOTP Secret 생성 (base32 32자리)

-- 2020010000 (장지후)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = 'XEGPI5IIE24QFJUST7ILHUN7TP6FZJAT',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020010000';

-- 2020010020 (안선우)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = 'MHA47PCTDCKHODJAV4Q52VP4PPW4ENI5',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020010020';

-- 2020020025 (손민서)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = 'Q6SBXRDBDK3GH3ZSDRP2MHLJNEDNJIXH',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020020025';

-- 2020020045 (박지원)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = '6SZJ35DBP6SVWFBFTNEOOM4FAKNFGASD',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020020045';

-- 2020030050 (한태민)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = 'BERVG5RM3VYZ2KGTONGIDHO3EUCDDJGU',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020030050';

-- 2020040075 (조예나)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = 'NTMYL2U6MYEJMFFG2J327G5U5OOMVCH3',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020040075';

-- 2020050000 (서도현)
UPDATE tb_user SET
    mfa_enabled = TRUE,
    mfa_secret = 'Q66OZOXD2P5VICDGTYF2ZXZHVUBHNOOP',
    upd_dt = CURRENT_TIMESTAMP
WHERE login_id = '2020050000';

-- 2. 결과 확인
SELECT
    login_id,
    user_nm,
    student_id,
    mfa_enabled,
    CASE WHEN mfa_secret IS NOT NULL THEN 'SET' ELSE 'NOT SET' END as mfa_secret_status
FROM tb_user
WHERE login_id IN ('2020010000', '2020010020', '2020020025', '2020020045', '2020030050', '2020040075', '2020050000')
ORDER BY login_id;

-- ============================================
-- TOTP 코드 생성 방법
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '======================================';
    RAISE NOTICE 'MFA 활성화 완료 - 대상 사용자 7명';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE '';
    RAISE NOTICE '사용자별 TOTP Secret:';
    RAISE NOTICE '2020010000 (장지후): XEGPI5IIE24QFJUST7ILHUN7TP6FZJAT';
    RAISE NOTICE '2020010020 (안선우): MHA47PCTDCKHODJAV4Q52VP4PPW4ENI5';
    RAISE NOTICE '2020020025 (손민서): Q6SBXRDBDK3GH3ZSDRP2MHLJNEDNJIXH';
    RAISE NOTICE '2020020045 (박지원): 6SZJ35DBP6SVWFBFTNEOOM4FAKNFGASD';
    RAISE NOTICE '2020030050 (한태민): BERVG5RM3VYZ2KGTONGIDHO3EUCDDJGU';
    RAISE NOTICE '2020040075 (조예나): NTMYL2U6MYEJMFFG2J327G5U5OOMVCH3';
    RAISE NOTICE '2020050000 (서도현): Q66OZOXD2P5VICDGTYF2ZXZHVUBHNOOP';
    RAISE NOTICE '';
    RAISE NOTICE 'TOTP 코드 생성 예시:';
    RAISE NOTICE 'python -c "import pyotp; print(pyotp.TOTP(''XEGPI5IIE24QFJUST7ILHUN7TP6FZJAT'').now())"';
    RAISE NOTICE '======================================';
END $$;
