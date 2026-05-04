-- 성공 패턴 추가 (올바른 role_cd 매핑)
SET search_path TO idino_career;

-- 법학과 → 변호사 (ROLE201)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 변호사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE201',
    '법학전문대학원을 통한 변호사 취업 경로',
    '3.8-4.5',
    ARRAY['헌법', '민법', '형법', '행정법', '상법']::varchar(100)[],
    ARRAY['법학전문대학원 진학', '변호사시험 합격', '로펌 인턴']::varchar(200)[],
    ARRAY['법률해석', '논증력', '문서작성']::varchar(100)[],
    '{"1학년": "기초법학", "2학년": "LEET 준비", "3-6년": "법전원"}'::jsonb,
    0.35, 150, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%법학%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 회계학과 → 공인회계사 (ROLE211)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 공인회계사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE211',
    '공인회계사 시험을 통한 Big4 회계법인 취업 경로',
    '3.5-4.5',
    ARRAY['회계원리', '재무회계', '세법', '감사론']::varchar(100)[],
    ARRAY['CPA 시험 준비', '회계법인 인턴']::varchar(200)[],
    ARRAY['재무분석', '감사', '세무']::varchar(100)[],
    '{"1학년": "기초", "2학년": "1차", "3-4학년": "2차 및 취업"}'::jsonb,
    0.25, 200, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%회계%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 교육학과 → 중등교사 (ROLE221)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 중등교사 임용 패턴',
    '취업',
    d.department_cd,
    'ROLE221',
    '교원임용시험을 통한 중등교사 취업 경로',
    '3.5-4.3',
    ARRAY['교육학개론', '교육심리학', '교과교육론']::varchar(100)[],
    ARRAY['교직이수', '교육실습', '임용시험 준비']::varchar(200)[],
    ARRAY['수업설계', '학생지도', '학급운영']::varchar(100)[],
    '{"1-2학년": "교직이수", "3학년": "실습", "4학년-졸업후": "임용시험"}'::jsonb,
    0.30, 180, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE (d.department_nm LIKE '%교육%' OR d.department_nm LIKE '%사범%') AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 건축학과 → 건축설계사 (ROLE231)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 건축설계사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE231',
    '건축설계사무소 취업 후 건축사 자격 취득 경로',
    '3.3-4.0',
    ARRAY['건축설계', '건축구조', 'CAD실습', '건축법규']::varchar(100)[],
    ARRAY['포트폴리오 구축', 'CAD/BIM 역량', '공모전 참가']::varchar(200)[],
    ARRAY['설계능력', 'CAD/BIM', '프레젠테이션']::varchar(100)[],
    '{"1-2학년": "CAD 기초", "3학년": "인턴", "4학년": "포트폴리오"}'::jsonb,
    0.40, 120, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%건축%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 전자공학과 → 반도체공학기술자 (ROLE235)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 반도체공학기술자 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE235',
    '삼성/SK 등 반도체 대기업 취업 경로',
    '3.5-4.2',
    ARRAY['반도체공학', '전자회로', '집적회로']::varchar(100)[],
    ARRAY['클린룸 실습', '대기업 인턴', '영어 능력']::varchar(200)[],
    ARRAY['반도체공정', '회로설계', '측정분석']::varchar(100)[],
    '{"1-2학년": "기초이론", "3학년": "실습", "4학년": "인턴 및 취업"}'::jsonb,
    0.50, 250, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE (d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%') AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 디자인학과 → UX/UI디자이너 (ROLE245)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → UX/UI디자이너 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE245',
    'IT 기업 및 스타트업 UX/UI 디자이너 취업 경로',
    '3.2-4.0',
    ARRAY['시각디자인', 'UI/UX디자인', '인터랙션디자인']::varchar(100)[],
    ARRAY['Figma 숙달', '포트폴리오 구축', '공모전 수상']::varchar(200)[],
    ARRAY['Figma', '사용자조사', '프로토타이핑']::varchar(100)[],
    '{"1-2학년": "툴 학습", "3학년": "인턴", "4학년": "포트폴리오"}'::jsonb,
    0.45, 100, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%디자인%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 사회복지학과 → 사회복지사 (ROLE251)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 사회복지사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE251',
    '사회복지시설/기관 취업 경로',
    '3.0-4.0',
    ARRAY['사회복지개론', '사례관리', '정책론']::varchar(100)[],
    ARRAY['사회복지사 자격증', '현장실습', '봉사활동']::varchar(200)[],
    ARRAY['사례관리', '상담', '프로그램기획']::varchar(100)[],
    '{"1-2학년": "필수과목", "3학년": "실습", "4학년": "자격증 및 취업"}'::jsonb,
    0.60, 200, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%사회복지%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 심리학과 → 상담심리사 (ROLE252)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 상담심리사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE252',
    '상담센터/병원 상담사 취업 경로 (대학원 필수)',
    '3.5-4.3',
    ARRAY['상담심리학', '임상심리학', '심리검사']::varchar(100)[],
    ARRAY['상담심리사 자격증', '대학원 진학', '임상 경험']::varchar(200)[],
    ARRAY['심리상담', '심리검사', '치료계획']::varchar(100)[],
    '{"1-4학년": "이론 및 대학원 준비", "대학원": "수련", "졸업후": "취업"}'::jsonb,
    0.35, 80, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%심리%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 행정학과 → 일반행정직공무원 (ROLE261)
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 일반행정직공무원 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE261',
    '9급/7급 공무원 시험을 통한 공직 진출 경로',
    '3.3-4.0',
    ARRAY['행정학개론', '행정법', '정책학']::varchar(100)[],
    ARRAY['공무원시험 준비', '한국사 자격증', '면접 준비']::varchar(200)[],
    ARRAY['행정실무', '법률해석', '민원응대']::varchar(100)[],
    '{"1-2학년": "기초", "3-4학년": "공무원 기초준비", "졸업후": "집중준비"}'::jsonb,
    0.20, 300, 'SYSTEM', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%행정%' AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;
