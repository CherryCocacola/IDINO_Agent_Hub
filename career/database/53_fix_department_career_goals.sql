-- =============================================================
-- 53_fix_department_career_goals.sql
-- 학과별 career_goal 구체화 및 성공 패턴 추가
-- 특히 스포츠헬스케어학과 등 모호한 career_goal 수정
-- =============================================================
SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 1: 학과별 career_goal 구체화
-- CTE + ROW_NUMBER() 패턴 사용 (PostgreSQL window function 제약 우회)
-- =====================================================

-- 스포츠헬스케어학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '스포츠|헬스케어|체육|운동'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', ''))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 4
        WHEN 0 THEN '스포츠트레이너'
        WHEN 1 THEN '운동처방사'
        WHEN 2 THEN '건강운동관리사'
        WHEN 3 THEN '스포츠재활전문가'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 간호학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '간호'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', ''))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '간호사'
        WHEN 1 THEN '전문간호사'
        WHEN 2 THEN '보건교사'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 물리치료학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '물리치료'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', ''))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '물리치료사'
        WHEN 1 THEN '재활전문가'
        WHEN 2 THEN '스포츠물리치료사'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 디자인학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '디자인|미술|예술'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', '', '크리에이터/디자이너', '예술전문가'))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 4
        WHEN 0 THEN '그래픽디자이너'
        WHEN 1 THEN 'UX/UI디자이너'
        WHEN 2 THEN '영상편집자'
        WHEN 3 THEN '브랜드디자이너'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 교육학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '교육|사범'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', '', '교육전문가'))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '초등교사'
        WHEN 1 THEN '중등교사'
        WHEN 2 THEN '교육행정가'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 경영/경제학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '경영|경제|회계|통상|무역'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', '', '경영전문가'))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 4
        WHEN 0 THEN '경영컨설턴트'
        WHEN 1 THEN '재무분석가'
        WHEN 2 THEN '마케팅전문가'
        WHEN 3 THEN '공인회계사'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 심리학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '심리'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', ''))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '상담심리사'
        WHEN 1 THEN '임상심리사'
        WHEN 2 THEN '심리연구원'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 사회학/행정학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '사회|행정|정치'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', ''))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '사회복지사'
        WHEN 1 THEN '공무원'
        WHEN 2 THEN '정책연구원'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 음악과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '음악'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', '', '예술전문가'))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '음악교사'
        WHEN 1 THEN '공연기획자'
        WHEN 2 THEN '실용음악가'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 인문학과
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '국문|영문|사학|철학|어문|인문|역사|문화'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', '', '인문학전문가'))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '언론인'
        WHEN 1 THEN '학술연구원'
        WHEN 2 THEN '번역가'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;

-- 자연과학
WITH numbered AS (
    SELECT s.student_id,
           ROW_NUMBER() OVER (ORDER BY s.student_id) AS rn
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE d.department_nm ~ '수학|물리|화학|생명과학|통계'
      AND (s.career_goal IS NULL OR s.career_goal IN ('전공 관련 전문가', '전공관련직', '미정', '', '과학자'))
)
UPDATE tb_student s
SET career_goal = CASE n.rn % 3
        WHEN 0 THEN '연구원'
        WHEN 1 THEN '데이터사이언티스트'
        WHEN 2 THEN '과학교사'
    END,
    upd_dt = CURRENT_TIMESTAMP,
    upd_user_id = 'FIX_CAREER_GOAL'
FROM numbered n
WHERE s.student_id = n.student_id;


-- =====================================================
-- Part 2: 스포츠헬스케어학과 전용 성공 패턴 추가
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '스포츠트레이너 취업 성공 패턴',
    'career',
    '생활체육지도사 2급 + 현장실습 + 운동처방 역량을 갖춘 졸업생의 취업 성공 패턴',
    '3.0-4.0',
    ARRAY['운동생리학', '운동처방론', '스포츠의학', '체력측정평가', '트레이닝방법론'],
    ARRAY['생활체육지도사 2급 취득', '스포츠센터 현장실습', '재활센터 인턴십', '체육대회 봉사'],
    ARRAY['운동처방', '체력측정', '재활운동', '트레이닝', '응급처치'],
    '{"1학년": "기초체육과학", "2학년": "전공심화+자격증준비", "3학년": "현장실습+자격증취득", "4학년": "취업준비"}',
    78.5, 85,
    'FIX_CAREER_GOAL', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '스포츠|헬스케어|체육|운동'
LIMIT 1;

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '운동처방사 취업 성공 패턴',
    'career',
    '건강운동관리사 자격 + 임상실습을 통한 운동처방 전문가 경로',
    '3.2-4.2',
    ARRAY['운동처방론', '병태생리학', '운동검사법', '운동영양학', '건강체력평가'],
    ARRAY['건강운동관리사 취득', '병원 임상실습', '재활센터 인턴십', '건강관리 봉사'],
    ARRAY['운동처방', '건강평가', '재활운동', '환자상담', '체력측정'],
    '{"1학년": "기초의학지식", "2학년": "운동과학심화", "3학년": "자격증+임상실습", "4학년": "취업+전문성강화"}',
    75.0, 60,
    'FIX_CAREER_GOAL', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '스포츠|헬스케어|체육|운동'
LIMIT 1;

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '교원임용 합격 패턴',
    'career',
    '교원임용시험 합격을 위한 체계적 준비 경로',
    '3.5-4.5',
    ARRAY['교육학개론', '교육심리학', '교육과정론', '교육방법및교육공학', '교육평가'],
    ARRAY['교원임용시험 준비', '교육실습', '교육봉사 100시간', '교과연구회 참여'],
    ARRAY['교육과정설계', '학생지도', '수업설계', '교육평가', '학급운영'],
    '{"1학년": "교직기초과목", "2학년": "전공교육학심화", "3학년": "임용준비+교육실습", "4학년": "임용시험+교생실습"}',
    72.0, 150,
    'FIX_CAREER_GOAL', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '교육'
LIMIT 1;

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '디자이너 취업 성공 패턴',
    'career',
    '포트폴리오 + 공모전 수상 + 에이전시 인턴십을 통한 디자이너 취업 경로',
    '3.0-4.0',
    ARRAY['시각디자인', 'UI/UX디자인', '타이포그래피', '브랜딩디자인', '디지털미디어'],
    ARRAY['GTQ 1급 취득', '디자인 공모전 수상', '에이전시 인턴십', '포트폴리오 전시'],
    ARRAY['그래픽디자인', '영상편집', 'UI설계', '포트폴리오', 'Adobe도구'],
    '{"1학년": "기초디자인", "2학년": "전공심화+공모전", "3학년": "인턴십+포트폴리오", "4학년": "취업+졸업전시"}',
    70.0, 110,
    'FIX_CAREER_GOAL', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '디자인'
LIMIT 1;

COMMIT;
