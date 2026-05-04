-- ============================================
-- IDINO Career: 취업 성공 패턴 현실화 수정
-- 문제점: 비현실적 패턴 유형 및 직업 매핑
-- ============================================

SET search_path TO idino_career;

BEGIN;

-- ============================================
-- 1. 비현실적 패턴 삭제 (의료 계열의 startup 패턴)
-- ============================================

-- 의료 계열 학과에서 startup 패턴 삭제
DELETE FROM tb_success_pattern
WHERE pattern_nm LIKE '%Medical%'
  AND pattern_type = 'startup';

-- 교육 계열 학과에서 startup 패턴 삭제 (교사는 창업 경로가 일반적이지 않음)
DELETE FROM tb_success_pattern
WHERE pattern_nm LIKE '%Education%'
  AND pattern_type = 'startup';

-- ============================================
-- 2. 비현실적 직업 매핑 수정
-- ============================================

-- 의예과/의학과에서 약사, 임상병리사, 물리치료사 등 비관련 직업 삭제
DELETE FROM tb_success_pattern
WHERE pattern_nm LIKE '%의예과%' OR pattern_nm LIKE '%의학과%'
  AND role_cd IN ('ROLE103', 'ROLE104', 'ROLE105', 'ROLE106');

-- 간호학과에서 의사 직업 삭제
DELETE FROM tb_success_pattern
WHERE pattern_nm LIKE '%간호%'
  AND role_cd = 'ROLE101';

-- 약학과에서 의사, 간호사 직업 삭제
DELETE FROM tb_success_pattern
WHERE pattern_nm LIKE '%약%'
  AND role_cd IN ('ROLE101', 'ROLE102');

-- ============================================
-- 3. 현실적인 성공 패턴 추가/업데이트
-- ============================================

-- 3.1 IT/소프트웨어 계열 현실적 패턴
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    'IT 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE07', -- 백엔드 개발자
    '삼성전자, 네이버, 카카오 등 대기업 취업 성공 패턴. 정보처리기사 자격증 취득, 2회 이상 인턴십 경험, GitHub 포트폴리오 필수.',
    '3.5-4.0',
    ARRAY['자료구조', '알고리즘', '데이터베이스', '운영체제', '소프트웨어공학']::varchar[],
    ARRAY['삼성 SW 역량테스트', '카카오 코딩테스트', 'GitHub 프로젝트', '인턴십', '오픈소스 기여']::varchar[],
    ARRAY['Python', 'Java', 'Spring Boot', 'SQL', 'Git', 'Docker']::varchar[],
    jsonb_build_object(
        '1학년', '프로그래밍 기초, 수학/과학 기초',
        '2학년', '자료구조/알고리즘, 코딩테스트 준비 시작',
        '3학년', '인턴십 지원, 정보처리기사 취득, 프로젝트 경험',
        '4학년', '대기업 공채 지원, 면접 준비'
    ),
    85.5,
    120,
    'SYSTEM_FIX',
    now()
FROM tb_department d
WHERE d.department_nm LIKE '%컴퓨터%'
   OR d.department_nm LIKE '%소프트웨어%'
   OR d.department_nm LIKE '%AI%'
ON CONFLICT DO NOTHING;

-- 3.2 간호학과 현실적 패턴
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    '간호사 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE102', -- 간호사
    '서울대병원, 삼성서울병원, 세브란스병원 등 대형병원 취업 성공 패턴. 국가고시 합격, 임상실습 우수, BLS 자격 취득 필수.',
    '3.5-4.0',
    ARRAY['기본간호학', '성인간호학', '아동간호학', '모성간호학', '정신간호학', '지역사회간호학']::varchar[],
    ARRAY['임상실습', '병원 자원봉사', 'BLS/ACLS 자격증', '학술대회 참여', '간호 연구']::varchar[],
    ARRAY['환자간호', '투약관리', '응급처치', '의료기록', 'EMR시스템', '의사소통']::varchar[],
    jsonb_build_object(
        '1학년', '기초과학, 해부학/생리학 기초',
        '2학년', '기본간호학, 간호술기 실습',
        '3학년', '임상실습 시작, 전공심화',
        '4학년', '국가고시 준비, 대형병원 취업 지원'
    ),
    92.0,
    180,
    'SYSTEM_FIX',
    now()
FROM tb_department d
WHERE d.department_nm LIKE '%간호%'
ON CONFLICT DO NOTHING;

-- 3.3 경영학과 현실적 패턴
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    '경영 컨설턴트 취업 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE11', -- 컨설턴트
    'McKinsey, BCG, Bain 등 전략 컨설팅펌 취업 성공 패턴. TOEIC 900+, 케이스 인터뷰 준비, 공모전 수상 경력 중요.',
    '3.7-4.3',
    ARRAY['경영전략', '재무관리', '마케팅원론', '회계원리', '조직행동론']::varchar[],
    ARRAY['경영 공모전', '해외 교환학생', '컨설팅 인턴십', '학회 활동', '케이스 스터디']::varchar[],
    ARRAY['Excel', 'PowerPoint', '재무분석', '문제해결', '프레젠테이션', '영어']::varchar[],
    jsonb_build_object(
        '1학년', '경영학 기초, 어학 준비',
        '2학년', '전공심화, 공모전 참여 시작',
        '3학년', '인턴십, 해외경험, 어학점수 확보',
        '4학년', '컨설팅펌 채용 프로세스 준비'
    ),
    72.0,
    85,
    'SYSTEM_FIX',
    now()
FROM tb_department d
WHERE d.department_nm LIKE '%경영%'
ON CONFLICT DO NOTHING;

-- 3.4 의예과/의학과 현실적 패턴 (대학원/전문의 과정)
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    '의사 전문의 과정 성공 패턴 - ' || d.department_nm,
    'graduate_school',
    d.department_cd,
    'ROLE101', -- 의사
    '서울대병원, 삼성서울병원, 아산병원 등 빅5 전문의 과정 합격 패턴. 의사국가고시 합격, 임상실습 우수, 연구 경험 중요.',
    '4.0-4.5',
    ARRAY['해부학', '생리학', '병리학', '약리학', '내과학', '외과학']::varchar[],
    ARRAY['임상실습', '의학 연구', '학술대회 발표', 'USMLE 준비', '해외 연수']::varchar[],
    ARRAY['진료', '진단', '처방', '수술보조', '환자상담', '의료기록']::varchar[],
    jsonb_build_object(
        '예과 1-2년', '기초의학, 해부학/생리학',
        '본과 1-2년', '임상의학 기초, 병태생리학',
        '본과 3-4년', '임상실습, 국가고시 준비',
        '졸업 후', '인턴 1년 → 레지던트 3-4년 → 전문의'
    ),
    98.5,
    60,
    'SYSTEM_FIX',
    now()
FROM tb_department d
WHERE d.department_nm LIKE '%의예과%' OR d.department_nm LIKE '%의학과%'
ON CONFLICT DO NOTHING;

-- 3.5 교육학과 현실적 패턴 (교사 임용)
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    '교사 임용 성공 패턴 - ' || d.department_nm,
    'employment',
    d.department_cd,
    'ROLE201', -- 교사
    '공립학교 교사 임용고시 합격 패턴. 교원자격증 취득, 교육실습 우수, 임용고시 1차/2차 통과.',
    '3.5-4.0',
    ARRAY['교육학개론', '교육심리학', '교육과정', '교육방법', '교육평가']::varchar[],
    ARRAY['교육실습', '교육봉사', '교사 동아리', '임용스터디', '모의수업']::varchar[],
    ARRAY['수업설계', '학급운영', '학생상담', '교육평가', '학부모소통']::varchar[],
    jsonb_build_object(
        '1학년', '교육학 기초, 전공 탐색',
        '2학년', '전공심화, 교육봉사 시작',
        '3학년', '교육실습, 임용고시 준비 시작',
        '4학년', '임용고시 1차/2차 준비 및 응시'
    ),
    15.0,
    200,
    'SYSTEM_FIX',
    now()
FROM tb_department d
WHERE d.department_nm LIKE '%교육%'
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================
-- 4. 결과 확인
-- ============================================
SELECT
    pattern_type,
    COUNT(*) as count,
    ROUND(AVG(success_rate)::numeric, 1) as avg_success_rate
FROM tb_success_pattern
GROUP BY pattern_type
ORDER BY count DESC;

SELECT
    pattern_nm,
    pattern_type,
    description,
    typical_gpa_range,
    success_rate
FROM tb_success_pattern
WHERE ins_user_id = 'SYSTEM_FIX'
LIMIT 10;
