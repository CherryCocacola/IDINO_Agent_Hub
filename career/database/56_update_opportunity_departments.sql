-- 56_update_opportunity_departments.sql
-- Map old department codes to include new 77-student department codes
-- Old seed data used codes like 1160, 1169, etc.
-- Our 77 students use codes like 3341, 3698, etc.
SET search_path TO idino_career, public;

-- Category mapping:
-- IT/Computing: 1160(컴퓨터응용과학), 1169(전자정보통신), 1101(데이터정보)
--   → 3680(AI소프트웨어), 3682(게임), 3685(반도체전자공학), 3691(멀티미디어), 3800(멀티미디어학부)
-- Engineering: 1034(기계공학), 1083(전자공학), 1086(화학공학), 1196(산업시스템)
--   → 680(건축), 2418(환경공학), 3338(의공학), 3788(의공학), 3824(나노융합)
-- Sciences: 1214(생명공학)
--   → 3672(의생명공학), 1995(약학), 2586(제약공학), 3673(제약공학), 3667(식품영양), 3670(방사선화학)
-- Healthcare: 1144(간호)
--   → 3027(간호), 354(의학), 842(의학), 352(의예), 2590(물리치료), 3659(물리치료)
--     3662(임상병리), 3663(작업치료), 3665(반려동물보건), 3666(보건안전공학)
--     3669(응급구조), 3698(스포츠헬스케어), 2313(보건행정)
-- Business: 1440(경영)
--   → 3341(경영학과), 3015(경영학부)
-- Design/Arts: 1127(디자인)
--   → 3126(음악), 3798(음악), 3692(웹툰영상), 3693(음악치료공연예술), 3694(미디어커뮤니케이션)
-- Social: 1012(경제), 1079(정치외교), 1289(행정)
--   → 2317(사회복지), 2602(공공인재), 3483(법학), 3136(국제어문)

-- Step 1: Add IT/Computing new codes where old IT codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['3680','3682','3685','3691','3800']
)
WHERE department_cds && ARRAY['1160','1169','1101']::varchar[];

-- Step 2: Add Engineering new codes where old engineering codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['680','2418','3338','3788','3824']
)
WHERE department_cds && ARRAY['1034','1083','1086','1196']::varchar[];

-- Step 3: Add Science new codes where old science codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['3672','1995','2586','3673','3667','3670']
)
WHERE department_cds && ARRAY['1214']::varchar[];

-- Step 4: Add Healthcare new codes where old healthcare codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['3027','354','842','352','2590','3659','3662','3663','3665','3666','3669','3698','2313']
)
WHERE department_cds && ARRAY['1144']::varchar[];

-- Step 5: Add Business new codes where old business codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['3341','3015']
)
WHERE department_cds && ARRAY['1440']::varchar[];

-- Step 6: Add Arts/Design new codes where old design codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['3126','3798','3692','3693','3694']
)
WHERE department_cds && ARRAY['1127']::varchar[];

-- Step 7: Add Social Science new codes where old social codes exist
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['2317','2602','3483','3136']
)
WHERE department_cds && ARRAY['1012','1079','1289']::varchar[];

-- Step 8: For the "ALL" opportunities (those with many old department codes),
-- add education and general departments too
UPDATE tb_opportunity
SET department_cds = array_cat(
    department_cds,
    ARRAY['2325','2319','3562']
)
WHERE array_length(department_cds, 1) >= 10;

-- Step 9: Create some universal healthcare opportunities for our medical students
-- Add healthcare department codes to opportunities that don't have them yet
-- (since healthcare is a large group in our 77 students)
INSERT INTO tb_opportunity (
    opportunity_type, title, description, organization, location,
    start_date, end_date, application_end, status, department_cds,
    requirements, benefits, skill_contributions
)
VALUES
(
    'internship', '병원 임상실습 인턴십', '대학병원 및 종합병원에서의 임상실습 기회. 다양한 진료과 로테이션을 통해 실무 경험을 쌓을 수 있습니다.',
    '대학병원 컨소시엄', '서울/경기', '2026-03-01', '2026-08-31', '2026-02-28', 'open',
    ARRAY['354','842','352','3027','2590','3659','3662','3663','3665','3669','3698','2313','3666','3670','3672','2586','3673','1995','3667'],
    '{"min_gpa": 3.0, "eligible_years": [3,4]}', '{"salary": "월 100만원", "benefits": "식비 지원"}',
    '{"skills": ["SKMD01","SKMD03","SKMD04"]}'
),
(
    'contest', '보건의료 혁신 아이디어 공모전', '보건의료 분야 혁신 아이디어를 제안하는 공모전. 의료 AI, 원격진료, 건강관리 등 다양한 주제.',
    '보건복지부', '온라인', '2026-03-15', '2026-05-15', '2026-04-30', 'open',
    ARRAY['354','842','352','3027','2590','3659','3662','3663','3665','3669','3698','2313','3666','3670','3672','2586','3673','1995','3667','3338','3788'],
    '{"eligible_years": [1,2,3,4]}', '{"salary": "총 상금 500만원"}',
    '{"skills": ["SKMD01","SKMD09"]}'
),
(
    'volunteer', '의료 봉사활동 (해외)', '개발도상국 의료봉사 프로그램. 기본 진료 보조, 건강교육, 위생환경 개선 활동.',
    '국제의료봉사단', '해외', '2026-07-01', '2026-07-31', '2026-05-31', 'open',
    ARRAY['354','842','352','3027','2590','3659','3662','3663','3665','3669','3698','2313','3666','3672'],
    '{"min_gpa": 2.5, "eligible_years": [2,3,4]}', '{"salary": "항공/숙박 지원"}',
    '{"skills": ["SKMD01","SKMD03","SKMD10"]}'
),
(
    'certification', '응급처치 자격증 교육', 'BLS/ACLS 자격증 취득을 위한 교육 프로그램. 보건의료 계열 학생 우대.',
    '대한심폐소생협회', '서울', '2026-04-01', '2026-04-15', '2026-03-20', 'open',
    ARRAY['354','842','352','3027','2590','3659','3662','3663','3665','3669','3698','2313','3666','3672','2586','3673','1995'],
    '{"eligible_years": [1,2,3,4]}', '{"salary": "교육비 50% 지원"}',
    '{"skills": ["SKMD03"]}'
),
-- Education opportunities
(
    'internship', '교육실습 연계 프로그램', '유치원, 초등학교, 특수학교 교육실습 기회. 교육 현장 경험과 교원임용 준비.',
    '교육실습지원센터', '서울/경기', '2026-03-01', '2026-06-30', '2026-02-20', 'open',
    ARRAY['2325','2319','3693'],
    '{"min_gpa": 3.0, "eligible_years": [3,4]}', '{"salary": "실습비 지원"}',
    '{"skills": ["SKED01","SKED02","SKED03"]}'
),
(
    'contest', '교육 콘텐츠 개발 공모전', '혁신적인 교육 콘텐츠 및 교수법을 제안하는 공모전.',
    '한국교육학술정보원', '온라인', '2026-04-01', '2026-06-30', '2026-05-31', 'open',
    ARRAY['2325','2319','3693','3694','3691','3800'],
    '{"eligible_years": [1,2,3,4]}', '{"salary": "총 상금 300만원"}',
    '{"skills": ["SKED01","SKED05"]}'
),
-- Arts/Media opportunities
(
    'internship', '미디어 콘텐츠 제작 인턴십', '영상, 웹툰, 음악 등 미디어 콘텐츠 제작 인턴십. 실무 포트폴리오 구축 기회.',
    '미디어컨텐츠진흥원', '서울', '2026-03-01', '2026-08-31', '2026-02-28', 'open',
    ARRAY['3126','3798','3692','3693','3694','3691','3800','3682'],
    '{"eligible_years": [2,3,4]}', '{"salary": "월 120만원"}',
    '{"skills": ["SKART01","SKART02","SKART07"]}'
),
-- Social Science / Law
(
    'internship', '사회복지 현장실습', '사회복지기관 현장실습 프로그램. 사례관리, 상담, 프로그램 기획 경험.',
    '사회복지협의회', '전국', '2026-03-01', '2026-06-30', '2026-02-28', 'open',
    ARRAY['2317','2602','3483','3136'],
    '{"min_gpa": 2.5, "eligible_years": [3,4]}', '{"salary": "실습비 지원"}',
    '{"skills": ["SKSC01","SKSC02"]}'
),
-- Business
(
    'contest', '비즈니스 전략 경진대회', '기업 사례 분석 및 전략 제안 대회. 경영학 전공 학생 대상.',
    '한국경영학회', '서울', '2026-05-01', '2026-07-31', '2026-06-30', 'open',
    ARRAY['3341','3015','1440'],
    '{"min_gpa": 3.0, "eligible_years": [2,3,4]}', '{"salary": "총 상금 1000만원"}',
    '{"skills": ["SKBZ01","SKBZ03","SKBZ04"]}'
),
-- Pharmacy
(
    'internship', '약국/제약사 현장실습', '약국 및 제약회사 현장실습 프로그램. 조제 실무, 의약품 관리 경험.',
    '대한약사회', '전국', '2026-06-01', '2026-08-31', '2026-05-15', 'open',
    ARRAY['1995','2586','3673','3672','3670'],
    '{"min_gpa": 3.0, "eligible_years": [3,4]}', '{"salary": "월 150만원"}',
    '{"skills": ["SKPH01","SKPH02","SKPH05"]}'
),
-- Sports/Healthcare
(
    'certification', '스포츠트레이너 자격 프로그램', '대한체육회 공인 스포츠트레이너 자격 취득 프로그램.',
    '대한체육회', '서울/경기', '2026-04-01', '2026-06-30', '2026-03-20', 'open',
    ARRAY['3698','2590','3659','3663','3669'],
    '{"eligible_years": [2,3,4]}', '{"salary": "교육비 지원"}',
    '{"skills": ["SKMD06","SKMD08","SKMD09"]}'
),
-- General/All departments
(
    'contest', '대학생 창업 아이디어 경진대회', '전 학과 대상 창업 아이디어 공모전. 팀 구성 및 사업계획서 제출.',
    '중소벤처기업부', '온라인', '2026-04-01', '2026-08-31', '2026-07-31', 'open',
    ARRAY['3680','3682','3685','3691','3800','680','2418','3338','3788','3824','3672','1995','2586','3673','3667','3670','3027','354','842','352','2590','3659','3662','3663','3665','3666','3669','3698','2313','3341','3015','3126','3798','3692','3693','3694','2317','2602','3483','3136','2325','2319','3562'],
    '{"eligible_years": [1,2,3,4]}', '{"salary": "총 상금 2000만원, 창업 지원금"}',
    '{"skills": []}'
);

-- Step 10: Deduplicate department_cds arrays (remove duplicates)
UPDATE tb_opportunity
SET department_cds = (
    SELECT ARRAY(SELECT DISTINCT unnest(department_cds) ORDER BY 1)
)
WHERE department_cds IS NOT NULL;

-- Verify: Check that each of our 77 students' departments has at least some matching opportunities
SELECT d.department_cd, d.department_nm,
       COUNT(o.opportunity_id) as matching_opportunities
FROM tb_department d
JOIN tb_student s ON d.department_cd = s.department_cd
CROSS JOIN LATERAL (
    SELECT opportunity_id FROM tb_opportunity
    WHERE status = 'open' AND d.department_cd = ANY(department_cds)
) o
WHERE s.student_id IN ('2021A143','20203008','20201861','20201481','20234317','20251521','20232525','20241484')
GROUP BY d.department_cd, d.department_nm
ORDER BY matching_opportunities;
