-- 57_fix_alumni_comparison_data.sql
-- Alumni cohort에 avg_extras JSONB 컬럼 추가 및 학과별 평균값 seed
-- Issue: 졸업생 비교 수치가 전부 하드코딩 (credits=95, certifications=2, activities=5 등)

-- 1. avg_extras 컬럼 추가
ALTER TABLE tb_alumni_cohort
ADD COLUMN IF NOT EXISTS avg_extras JSONB DEFAULT '{}';

COMMENT ON COLUMN tb_alumni_cohort.avg_extras IS '졸업생 평균 추가 정보 (avg_credits, avg_certifications, avg_activities 등)';

-- 2. 학과 카테고리별 합리적인 평균값 seed
-- IT/컴퓨터 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 134,
    'avg_certifications', 3,
    'avg_activities', 6
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '컴퓨터|소프트웨어|정보|AI|게임|반도체|멀티미디어|정보통신'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 공학 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 140,
    'avg_certifications', 3,
    'avg_activities', 5
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '기계|전기|토목|건축|건설|로봇|화공|재료|소방|나노|산업|환경|배터리|스마트물류'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 보건/의료 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 145,
    'avg_certifications', 4,
    'avg_activities', 7
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '의예|의학|간호|보건|치위생|임상|물리치료|방사선|치기공|응급|헬스케어'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 약학/제약 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 150,
    'avg_certifications', 4,
    'avg_activities', 6
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '약학|제약'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 경영/경제 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 132,
    'avg_certifications', 3,
    'avg_activities', 6
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '경영|경제|회계|금융|무역|통상|세무|비즈니스'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 교육 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 138,
    'avg_certifications', 2,
    'avg_activities', 8
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '교육|사범'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 예술/디자인 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 130,
    'avg_certifications', 2,
    'avg_activities', 8
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '디자인|미술|영상|미디어|애니메이션|음악|공연|예술|웹툰'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 사회과학 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 133,
    'avg_certifications', 2,
    'avg_activities', 7
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '사회|법학|행정|정치|경찰|심리|복지'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 인문 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 130,
    'avg_certifications', 2,
    'avg_activities', 6
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '어문|인문|역사|문화|영어|통일|철학|문학|국제|외국어'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 자연과학 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 136,
    'avg_certifications', 2,
    'avg_activities', 5
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '식품|화학|물리|생명|수학|통계|바이오|신소재'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 스포츠/체육 계열
UPDATE tb_alumni_cohort ac
SET avg_extras = jsonb_build_object(
    'avg_credits', 132,
    'avg_certifications', 3,
    'avg_activities', 9
)
FROM tb_department d
WHERE ac.department_cd = d.department_cd
  AND d.department_nm ~ '스포츠|체육|운동'
  AND (ac.avg_extras IS NULL OR ac.avg_extras = '{}');

-- 나머지 (매칭되지 않은 학과) - 기본값
UPDATE tb_alumni_cohort
SET avg_extras = jsonb_build_object(
    'avg_credits', 132,
    'avg_certifications', 2,
    'avg_activities', 6
)
WHERE avg_extras IS NULL OR avg_extras = '{}';
