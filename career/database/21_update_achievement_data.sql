-- ============================================
-- tb_achievement 데이터 Excel 형식 맞춤 업데이트
-- Version: v1
-- 목적: 플레이스홀더 데이터를 실제 한국 자격증/성과 데이터로 변환
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. achievement_type 값 변환
-- certification → certificate (Excel 형식)
-- project → patent (특허) 또는 유지
-- ============================================

UPDATE tb_achievement
SET achievement_type = 'certificate'
WHERE achievement_type = 'certification';

-- project 타입 일부를 patent로 변경
UPDATE tb_achievement
SET achievement_type = 'patent'
WHERE achievement_type = 'project'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'project'
    ORDER BY random()
    LIMIT 3000
);

-- ============================================
-- 2. certificate 타입: 실제 자격증명으로 업데이트
-- ============================================

-- 정보처리기사 (가장 일반적인 IT 자격증)
UPDATE tb_achievement
SET
    title = '정보처리기사',
    issuer = '한국산업인력공단',
    level = '기사'
WHERE achievement_type = 'certificate'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 800
);

-- 빅데이터분석기사
UPDATE tb_achievement
SET
    title = '빅데이터분석기사',
    issuer = '한국데이터산업진흥원',
    level = '기사'
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 600
);

-- SQLD (SQL 개발자)
UPDATE tb_achievement
SET
    title = 'SQLD',
    issuer = '한국데이터산업진흥원',
    level = '전문가'
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 500
);

-- ADsP (데이터분석 준전문가)
UPDATE tb_achievement
SET
    title = 'ADsP',
    issuer = '한국데이터산업진흥원',
    level = '준전문가'
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 500
);

-- TOEIC
UPDATE tb_achievement
SET
    title = 'TOEIC',
    issuer = 'ETS',
    level = 'gold',
    score = (700 + floor(random() * 250))::text
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 800
);

-- TOEFL
UPDATE tb_achievement
SET
    title = 'TOEFL',
    issuer = 'ETS',
    level = 'gold',
    score = (80 + floor(random() * 35))::text
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 400
);

-- OPIC
UPDATE tb_achievement
SET
    title = 'OPIc',
    issuer = 'ACTFL',
    level = CASE floor(random() * 3)::int
        WHEN 0 THEN 'IH'
        WHEN 1 THEN 'IM3'
        ELSE 'AL'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 400
);

-- 컴퓨터활용능력
UPDATE tb_achievement
SET
    title = '컴퓨터활용능력',
    issuer = '대한상공회의소',
    level = CASE floor(random() * 2)::int
        WHEN 0 THEN '1급'
        ELSE '2급'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 600
);

-- 한국사능력검정시험
UPDATE tb_achievement
SET
    title = '한국사능력검정시험',
    issuer = '국사편찬위원회',
    level = CASE floor(random() * 3)::int
        WHEN 0 THEN '1급'
        WHEN 1 THEN '2급'
        ELSE '3급'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 500
);

-- MOS (Microsoft Office Specialist)
UPDATE tb_achievement
SET
    title = 'MOS',
    issuer = 'Microsoft',
    level = CASE floor(random() * 2)::int
        WHEN 0 THEN 'Expert'
        ELSE 'Master'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 400
);

-- 전기기사/전자기사
UPDATE tb_achievement
SET
    title = CASE floor(random() * 2)::int
        WHEN 0 THEN '전기기사'
        ELSE '전자기사'
    END,
    issuer = '한국산업인력공단',
    level = '기사'
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 500
);

-- 정보보안기사
UPDATE tb_achievement
SET
    title = '정보보안기사',
    issuer = '한국인터넷진흥원',
    level = '기사'
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 300
);

-- 네트워크관리사
UPDATE tb_achievement
SET
    title = '네트워크관리사',
    issuer = '한국정보통신자격협회',
    level = CASE floor(random() * 2)::int
        WHEN 0 THEN '1급'
        ELSE '2급'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 300
);

-- 리눅스마스터
UPDATE tb_achievement
SET
    title = '리눅스마스터',
    issuer = '한국정보통신진흥협회',
    level = CASE floor(random() * 2)::int
        WHEN 0 THEN '1급'
        ELSE '2급'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 300
);

-- AWS 자격증
UPDATE tb_achievement
SET
    title = CASE floor(random() * 3)::int
        WHEN 0 THEN 'AWS Solutions Architect Associate'
        WHEN 1 THEN 'AWS Developer Associate'
        ELSE 'AWS Cloud Practitioner'
    END,
    issuer = 'Amazon Web Services',
    level = CASE floor(random() * 2)::int
        WHEN 0 THEN 'Associate'
        ELSE 'Professional'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%'
AND achievement_id IN (
    SELECT achievement_id FROM tb_achievement
    WHERE achievement_type = 'certificate'
    AND title LIKE 'Achievement%'
    ORDER BY achievement_id
    LIMIT 200
);

-- 나머지 certificate 타입 처리
UPDATE tb_achievement
SET
    title = CASE floor(random() * 5)::int
        WHEN 0 THEN '사회조사분석사 2급'
        WHEN 1 THEN '전산세무회계'
        WHEN 2 THEN '워드프로세서'
        WHEN 3 THEN 'ITQ'
        ELSE 'GTQ'
    END,
    issuer = CASE floor(random() * 3)::int
        WHEN 0 THEN '한국산업인력공단'
        WHEN 1 THEN '대한상공회의소'
        ELSE '한국정보통신자격협회'
    END,
    level = CASE floor(random() * 3)::int
        WHEN 0 THEN '1급'
        WHEN 1 THEN '2급'
        ELSE 'A등급'
    END
WHERE achievement_type = 'certificate'
AND title LIKE 'Achievement%';

-- ============================================
-- 3. award 타입: 실제 수상명으로 업데이트
-- ============================================

-- 학술대회 수상
UPDATE tb_achievement
SET
    title = CASE floor(random() * 8)::int
        WHEN 0 THEN '한국정보과학회 학술발표대회 우수논문상'
        WHEN 1 THEN '대한전자공학회 학술대회 장려상'
        WHEN 2 THEN '한국소프트웨어공학회 논문경진대회 최우수상'
        WHEN 3 THEN '캡스톤디자인 경진대회 대상'
        WHEN 4 THEN '창업경진대회 우수상'
        WHEN 5 THEN '해커톤 대회 입상'
        WHEN 6 THEN 'SW개발 공모전 장려상'
        ELSE '학과 성적우수상'
    END,
    issuer = CASE floor(random() * 5)::int
        WHEN 0 THEN '한국정보과학회'
        WHEN 1 THEN '대한전자공학회'
        WHEN 2 THEN '한국소프트웨어공학회'
        WHEN 3 THEN '본교'
        ELSE '한국대학생학술회'
    END,
    level = CASE floor(random() * 4)::int
        WHEN 0 THEN '대상'
        WHEN 1 THEN '최우수상'
        WHEN 2 THEN '우수상'
        ELSE '장려상'
    END
WHERE achievement_type = 'award'
AND title LIKE 'Achievement%';

-- ============================================
-- 4. patent 타입: 실제 특허명으로 업데이트
-- ============================================

UPDATE tb_achievement
SET
    title = CASE floor(random() * 10)::int
        WHEN 0 THEN '딥러닝 기반 이미지 분류 시스템'
        WHEN 1 THEN '자연어 처리를 이용한 챗봇 시스템'
        WHEN 2 THEN '블록체인 기반 인증 시스템'
        WHEN 3 THEN 'IoT 센서 데이터 수집 장치'
        WHEN 4 THEN '모바일 앱 기반 헬스케어 시스템'
        WHEN 5 THEN '빅데이터 분석 플랫폼'
        WHEN 6 THEN '클라우드 기반 협업 시스템'
        WHEN 7 THEN '스마트팜 관리 시스템'
        WHEN 8 THEN 'AR/VR 교육 콘텐츠 시스템'
        ELSE '에너지 효율 최적화 알고리즘'
    END,
    issuer = '특허청',
    level = CASE floor(random() * 2)::int
        WHEN 0 THEN '출원'
        ELSE '등록'
    END
WHERE achievement_type = 'patent'
AND title LIKE 'Achievement%';

-- ============================================
-- 5. 남은 project 타입 처리
-- ============================================

UPDATE tb_achievement
SET
    title = CASE floor(random() * 6)::int
        WHEN 0 THEN '산학협력 프로젝트 우수 참여'
        WHEN 1 THEN 'SW중심대학 사업 참여 인증'
        WHEN 2 THEN '학부연구생 프로그램 수료'
        WHEN 3 THEN '인턴십 프로그램 이수'
        WHEN 4 THEN '오픈소스 기여 인증'
        ELSE '멘토링 프로그램 수료'
    END,
    issuer = CASE floor(random() * 3)::int
        WHEN 0 THEN '본교 산학협력단'
        WHEN 1 THEN 'SW중심대학사업단'
        ELSE '학과'
    END,
    level = 'participant'
WHERE achievement_type = 'project'
AND title LIKE 'Achievement%';

-- ============================================
-- 6. 결과 확인
-- ============================================

-- 업데이트 후 데이터 분포 확인
SELECT achievement_type, COUNT(*) as cnt
FROM tb_achievement
GROUP BY achievement_type
ORDER BY cnt DESC;

-- 샘플 데이터 확인
SELECT achievement_type, title, issuer, level
FROM tb_achievement
ORDER BY random()
LIMIT 20;
