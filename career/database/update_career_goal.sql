-- 학과별 career_goal 업데이트
SET search_path TO idino_career;

UPDATE tb_student s
SET career_goal = dcm.career_goal
FROM (
    SELECT
        d.department_cd,
        CASE
            -- 의료/보건 계열
            WHEN d.department_nm LIKE '%의%과' OR d.department_nm LIKE '%의학%' THEN '의사'
            WHEN d.department_nm LIKE '%간호%' THEN '간호사'
            WHEN d.department_nm LIKE '%약%학%' OR d.department_nm LIKE '%제약%' THEN '약사'
            WHEN d.department_nm LIKE '%치%의%' OR d.department_nm LIKE '%치과%' THEN '치과의사'
            WHEN d.department_nm LIKE '%물리치료%' THEN '물리치료사'
            WHEN d.department_nm LIKE '%임상%' OR d.department_nm LIKE '%병리%' THEN '임상병리사'
            WHEN d.department_nm LIKE '%보건%' THEN '보건관리사'

            -- IT 계열
            WHEN d.department_nm LIKE '%컴퓨터%' OR d.department_nm LIKE '%소프트웨어%' THEN '소프트웨어 개발자'
            WHEN d.department_nm LIKE '%정보%' OR d.department_nm LIKE '%IT%' THEN '소프트웨어 개발자'
            WHEN d.department_nm LIKE '%AI%' OR d.department_nm LIKE '%인공지능%' THEN 'AI 엔지니어'
            WHEN d.department_nm LIKE '%데이터%' THEN '데이터 분석가'

            -- 공학 계열
            WHEN d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%전기%' THEN '전자 엔지니어'
            WHEN d.department_nm LIKE '%기계%' THEN '기계 엔지니어'
            WHEN d.department_nm LIKE '%건축%' THEN '건축가'
            WHEN d.department_nm LIKE '%화학공%' OR d.department_nm LIKE '%화공%' THEN '화학 엔지니어'
            WHEN d.department_nm LIKE '%토목%' OR d.department_nm LIKE '%환경%' THEN '토목 엔지니어'
            WHEN d.department_nm LIKE '%산업%' THEN '산업 엔지니어'
            WHEN d.department_nm LIKE '%재료%' OR d.department_nm LIKE '%나노%' THEN '재료 연구원'
            WHEN d.department_nm LIKE '%생명공%' OR d.department_nm LIKE '%바이오%' THEN '바이오 연구원'

            -- 교육 계열
            WHEN d.department_nm LIKE '%교육%' OR d.department_nm LIKE '%사범%' THEN '교사'
            WHEN d.department_nm LIKE '%유아%' THEN '유아교사'

            -- 예술/디자인 계열
            WHEN d.department_nm LIKE '%디자인%' THEN '디자이너'
            WHEN d.department_nm LIKE '%미술%' OR d.department_nm LIKE '%예술%' THEN '아티스트'
            WHEN d.department_nm LIKE '%음악%' THEN '음악가'
            WHEN d.department_nm LIKE '%영상%' OR d.department_nm LIKE '%영화%' THEN '영상 제작자'
            WHEN d.department_nm LIKE '%연극%' OR d.department_nm LIKE '%공연%' THEN '공연 기획자'

            -- 경영/경제 계열
            WHEN d.department_nm LIKE '%경영%' THEN '경영 전문가'
            WHEN d.department_nm LIKE '%경제%' THEN '경제 분석가'
            WHEN d.department_nm LIKE '%회계%' THEN '회계사'
            WHEN d.department_nm LIKE '%금융%' THEN '금융 분석가'
            WHEN d.department_nm LIKE '%무역%' OR d.department_nm LIKE '%통상%' THEN '무역 전문가'
            WHEN d.department_nm LIKE '%마케팅%' OR d.department_nm LIKE '%광고%' THEN '마케터'

            -- 사회/행정 계열
            WHEN d.department_nm LIKE '%행정%' THEN '행정가'
            WHEN d.department_nm LIKE '%사회복지%' OR d.department_nm LIKE '%복지%' THEN '사회복지사'
            WHEN d.department_nm LIKE '%심리%' THEN '심리상담사'
            WHEN d.department_nm LIKE '%법%' THEN '법률 전문가'
            WHEN d.department_nm LIKE '%정치%' OR d.department_nm LIKE '%외교%' THEN '정치외교 전문가'

            -- 인문 계열
            WHEN d.department_nm LIKE '%국문%' OR d.department_nm LIKE '%국어%' THEN '작가/편집자'
            WHEN d.department_nm LIKE '%영문%' OR d.department_nm LIKE '%영어%' THEN '번역가'
            WHEN d.department_nm LIKE '%철학%' THEN '연구원'
            WHEN d.department_nm LIKE '%역사%' THEN '연구원'

            -- 자연과학 계열
            WHEN d.department_nm LIKE '%수학%' OR d.department_nm LIKE '%통계%' THEN '데이터 과학자'
            WHEN d.department_nm LIKE '%물리%' THEN '물리학 연구원'
            WHEN d.department_nm LIKE '%화학%' THEN '화학 연구원'
            WHEN d.department_nm LIKE '%생명%' OR d.department_nm LIKE '%생물%' THEN '생명과학 연구원'
            WHEN d.department_nm LIKE '%식품%' OR d.department_nm LIKE '%영양%' THEN '식품 전문가'

            ELSE '전공 관련 전문가'
        END as career_goal
    FROM tb_department d
) dcm
WHERE s.department_cd = dcm.department_cd
AND s.career_goal IS NULL;
