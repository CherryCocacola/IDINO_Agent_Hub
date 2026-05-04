-- =====================================================
-- IDINO Career - Korean Names Update Script
-- Updates tb_student.student_nm and tb_user.user_nm to Korean names
-- =====================================================

-- 1. Create temporary function to generate Korean names
CREATE OR REPLACE FUNCTION generate_korean_name(seed INTEGER) RETURNS VARCHAR AS $$
DECLARE
    last_names VARCHAR[] := ARRAY[
        '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
        '한', '오', '서', '신', '권', '황', '안', '송', '유', '홍',
        '백', '고', '문', '양', '손', '배', '조', '하', '남', '차'
    ];
    first_names VARCHAR[] := ARRAY[
        '민준', '서준', '도윤', '예준', '시우', '하준', '주원', '지호', '지후', '준서',
        '준우', '현우', '도현', '지훈', '건우', '우진', '선우', '서진', '민재', '현준',
        '서연', '서윤', '지우', '서현', '민서', '하은', '하윤', '윤서', '지민', '채원',
        '지수', '수빈', '지원', '소율', '예은', '지아', '수아', '지유', '다은', '채은',
        '태민', '승우', '재민', '진우', '성민', '은우', '재현', '승현', '지성', '우빈',
        '은서', '연우', '지안', '소윤', '예진', '유진', '예나', '민지', '유나', '채린'
    ];
    last_name_idx INTEGER;
    first_name_idx INTEGER;
BEGIN
    -- Use the seed to deterministically select names
    last_name_idx := (seed % array_length(last_names, 1)) + 1;
    first_name_idx := (seed % array_length(first_names, 1)) + 1;

    RETURN last_names[last_name_idx] || first_names[first_name_idx];
END;
$$ LANGUAGE plpgsql;

-- 2. Update tb_student with Korean names
-- Using row_number to generate unique names for each student
WITH numbered_students AS (
    SELECT student_id, ROW_NUMBER() OVER (ORDER BY student_id) as rn
    FROM tb_student
)
UPDATE tb_student s
SET student_nm = generate_korean_name((ns.rn * 7 + ns.rn)::INTEGER),
    upd_dt = NOW(),
    upd_user_id = 'MIGRATION'
FROM numbered_students ns
WHERE s.student_id = ns.student_id;

-- 3. Update tb_user with Korean names (sync with tb_student for student users)
-- For student users, copy the name from tb_student
UPDATE tb_user u
SET user_nm = s.student_nm,
    upd_dt = NOW(),
    upd_user_id = 'MIGRATION'
FROM tb_student s
WHERE u.student_id = s.student_id
AND u.user_type = 'student';

-- 4. Update professor users to have Korean names
WITH numbered_professors AS (
    SELECT u.user_id, ROW_NUMBER() OVER (ORDER BY u.user_id) as rn
    FROM tb_user u
    WHERE u.user_type = 'professor' OR u.user_type = 'advisor'
)
UPDATE tb_user u
SET user_nm = generate_korean_name((np.rn * 13 + 100)::INTEGER),
    upd_dt = NOW(),
    upd_user_id = 'MIGRATION'
FROM numbered_professors np
WHERE u.user_id = np.user_id;

-- 5. Keep admin users with descriptive names
UPDATE tb_user
SET user_nm = '시스템관리자'
WHERE user_type = 'admin' AND user_nm = 'Administrator';

UPDATE tb_user
SET user_nm = '취업지원관리자'
WHERE user_type = 'career_admin';

-- 6. Update tb_professor with Korean names (sync with tb_user if linked)
UPDATE tb_professor p
SET professor_nm = u.user_nm,
    upd_dt = NOW(),
    upd_user_id = 'MIGRATION'
FROM tb_user u
WHERE p.professor_cd = u.professor_cd
AND u.professor_cd IS NOT NULL;

-- 7. If professors don't have a linked user, generate Korean names
WITH numbered_unlinked AS (
    SELECT p.professor_cd, ROW_NUMBER() OVER (ORDER BY p.professor_cd) as rn
    FROM tb_professor p
    LEFT JOIN tb_user u ON p.professor_cd = u.professor_cd
    WHERE u.professor_cd IS NULL
)
UPDATE tb_professor p
SET professor_nm = generate_korean_name((nu.rn * 17 + 200)::INTEGER),
    upd_dt = NOW(),
    upd_user_id = 'MIGRATION'
FROM numbered_unlinked nu
WHERE p.professor_cd = nu.professor_cd;

-- 8. Cleanup - Drop temporary function
DROP FUNCTION IF EXISTS generate_korean_name(INTEGER);

-- 9. Verify changes
SELECT 'tb_student 한글 이름 업데이트 완료' as status, COUNT(*) as count FROM tb_student WHERE student_nm ~ '[가-힣]';
SELECT 'tb_user 한글 이름 업데이트 완료' as status, COUNT(*) as count FROM tb_user WHERE user_nm ~ '[가-힣]';
SELECT 'tb_professor 한글 이름 업데이트 완료' as status, COUNT(*) as count FROM tb_professor WHERE professor_nm ~ '[가-힣]';

-- 10. Sample check
SELECT '학생 샘플 확인' as type, student_id, student_nm FROM tb_student LIMIT 5;
SELECT '사용자 샘플 확인' as type, login_id, user_nm, user_type FROM tb_user LIMIT 10;
