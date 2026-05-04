-- ============================================
-- 모든 사용자 비밀번호 해시 수정
-- ============================================
-- 비밀번호: 1234
-- ============================================

SET search_path TO idino_career, public;

-- 모든 사용자의 비밀번호를 '1234'의 bcrypt 해시로 업데이트
-- (2021010001 사용자는 이미 올바른 해시를 가지고 있음)
UPDATE tb_user
SET password_hash = '$2b$12$dagfO9TV6ro9rIXNVRjJCuoLrCRF6h6cQEyWURjR.Neo12Jpg6mLO'
WHERE login_id != '2021010001';

-- 확인 쿼리
SELECT
    login_id,
    student_id,
    LEFT(password_hash, 40) as hash_preview,
    mfa_enabled,
    status
FROM tb_user
ORDER BY login_id
LIMIT 15;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '======================================';
    RAISE NOTICE '비밀번호 해시 업데이트 완료';
    RAISE NOTICE '모든 사용자 비밀번호: 1234';
    RAISE NOTICE '======================================';
END $$;
