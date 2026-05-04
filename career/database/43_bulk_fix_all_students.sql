-- =====================================================
-- 43_bulk_fix_all_students.sql
-- 전체 학생(2023~2025) 데이터 정합성 일괄 생성
-- 대상: 7,436명 / 161개 학과
-- =====================================================
-- 실행: psql -f database/43_bulk_fix_all_students.sql
-- 또는 docker exec 로 실행
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 대상 학생 + 학과 카테고리 매핑 TEMP TABLE
-- =====================================================

CREATE TEMP TABLE tmp_dept_category AS
SELECT
    d.department_cd,
    d.department_nm,
    CASE
        WHEN d.department_nm ~ '의예|의학|의생명|의공학|의료IT|식의약' THEN 'medical'
        WHEN d.department_nm ~ '간호' THEN 'nursing'
        WHEN d.department_nm ~ '약학|제약' THEN 'pharmacy'
        WHEN d.department_nm ~ '물리치료|임상병리|작업치료|응급구조|보건|방사선|반려동물|헬스케어|스포츠|재활' THEN 'health'
        WHEN d.department_nm ~ '컴퓨터|AI|소프트웨어|반도체|전자|기계|전기|게임|멀티미디어|나노|건축|건설|소방|스마트물류|산업|로봇|융합기술|배터리|웹툰영상|정보통신' THEN 'engineering'
        WHEN d.department_nm ~ '경영|통상|MBA' THEN 'business'
        WHEN d.department_nm ~ '법학|경찰|행정' THEN 'law_admin'
        WHEN d.department_nm ~ '교육|상담|사회복지|발달|특수교육|유아' THEN 'education'
        WHEN d.department_nm ~ '어문|인문|역사|문화콘텐츠|문화유산|차문화|통일|영어영문' THEN 'humanities'
        WHEN d.department_nm ~ '음악|디자인|미디어|공연|영상' THEN 'arts'
        WHEN d.department_nm ~ '생명과학|화학|통계|환경|신소재' THEN 'science'
        ELSE 'general'
    END AS category
FROM tb_department d;

-- 대상 학생 목록 (2023~2025 입학) + 카테고리
CREATE TEMP TABLE tmp_target_students AS
SELECT
    s.student_id,
    s.student_nm,
    s.department_cd,
    s.admission_year,
    s.current_grade,
    dc.category
FROM tb_student s
JOIN tmp_dept_category dc ON s.department_cd = dc.department_cd
WHERE s.admission_year BETWEEN 2023 AND 2025;

CREATE INDEX idx_tmp_target_sid ON tmp_target_students(student_id);
CREATE INDEX idx_tmp_target_cat ON tmp_target_students(category);

DO $$ BEGIN RAISE NOTICE 'Part 0 완료: 대상 학생 및 카테고리 매핑 생성'; END $$;

-- =====================================================
-- Part 1: 연락처 생성 (phone, email)
-- =====================================================

UPDATE tb_student s
SET
    phone = '010-' || LPAD(((hashtext(s.student_id)::bigint % 9000 + 1000 + 10000) % 10000)::text, 4, '0') || '-' || RIGHT(s.student_id, 4),
    email = s.student_id || '@inje.ac.kr',
    upd_user_id = 'BULK_FIX',
    upd_dt = NOW()
FROM tmp_target_students ts
WHERE s.student_id = ts.student_id
  AND (s.phone IS NULL OR s.email IS NULL);

DO $$ BEGIN RAISE NOTICE 'Part 1 완료: 연락처 생성'; END $$;

-- =====================================================
-- Part 2: 성적(tb_grade) 일괄 생성
-- 대상: enrollment 있지만 grade 없는 학생
-- =====================================================

-- 기존에 grade가 있는 학생 (198명) 보호: 그들은 제외
INSERT INTO tb_grade (grade_id, enrollment_id, student_id, course_cd, term_cd, grade_letter, grade_point, credits_earned, is_retake, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    e.enrollment_id,
    e.student_id,
    co.course_cd,
    e.term_cd,
    CASE
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 20 THEN 'A+'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 50 THEN 'A0'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 75 THEN 'B+'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 90 THEN 'B0'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 98 THEN 'C+'
        ELSE 'C0'
    END,
    CASE
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 20 THEN 4.50
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 50 THEN 4.00
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 75 THEN 3.50
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 90 THEN 3.00
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 98 THEN 2.50
        ELSE 2.00
    END,
    c.credits,
    'N',
    'BULK_FIX',
    NOW()
FROM tb_enrollment e
JOIN tb_course_offering co ON e.course_offering_id = co.offering_id
JOIN tb_course c ON co.course_cd = c.course_cd
JOIN tmp_target_students ts ON e.student_id = ts.student_id
WHERE NOT EXISTS (
    SELECT 1 FROM tb_grade g WHERE g.enrollment_id = e.enrollment_id
);

DO $$ BEGIN RAISE NOTICE 'Part 2 완료: 성적 생성'; END $$;

-- =====================================================
-- Part 3: 학기별 성적요약(tb_grade_summary) 생성
-- =====================================================

-- 기존 요약 삭제 (대상 학생만)
DELETE FROM tb_grade_summary gs
USING tmp_target_students ts
WHERE gs.student_id = ts.student_id;

INSERT INTO tb_grade_summary (summary_id, student_id, term_cd, total_credits, earned_credits, gpa, major_gpa, class_rank, total_students, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    g.student_id,
    g.term_cd,
    SUM(g.credits_earned),
    SUM(g.credits_earned),
    ROUND(SUM(g.grade_point * g.credits_earned) / NULLIF(SUM(g.credits_earned), 0), 2),
    ROUND(SUM(g.grade_point * g.credits_earned) / NULLIF(SUM(g.credits_earned), 0), 2) + ROUND((hashtext(g.student_id || g.term_cd)::numeric % 30) / 100.0, 2),
    GREATEST(1, abs(hashtext(g.student_id || g.term_cd)) % 40 + 1),
    40,
    'BULK_FIX',
    NOW()
FROM tb_grade g
JOIN tmp_target_students ts ON g.student_id = ts.student_id
GROUP BY g.student_id, g.term_cd;

DO $$ BEGIN RAISE NOTICE 'Part 3 완료: 학기별 성적요약 생성'; END $$;

-- =====================================================
-- Part 4: 누적 요약(tb_cumulative_summary) 생성
-- =====================================================

DELETE FROM tb_cumulative_summary cs
USING tmp_target_students ts
WHERE cs.student_id = ts.student_id;

INSERT INTO tb_cumulative_summary (
    summary_id, student_id,
    total_credits_required, total_credits_earned,
    major_credits_required, major_credits_earned,
    liberal_credits_required, liberal_credits_earned,
    cumulative_gpa, major_gpa, completion_rate,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    agg.student_id,
    -- total_credits_required (졸업학점)
    CASE ts.category
        WHEN 'medical' THEN 140
        WHEN 'pharmacy' THEN 150
        ELSE 130
    END,
    -- total_credits_earned
    agg.total_earned,
    -- major_credits_required
    CASE ts.category
        WHEN 'medical' THEN ROUND(140 * 0.55)
        WHEN 'nursing' THEN ROUND(140 * 0.55)
        WHEN 'pharmacy' THEN ROUND(150 * 0.55)
        WHEN 'health' THEN ROUND(140 * 0.55)
        WHEN 'engineering' THEN ROUND(130 * 0.50)
        WHEN 'humanities' THEN ROUND(130 * 0.40)
        WHEN 'education' THEN ROUND(130 * 0.40)
        WHEN 'law_admin' THEN ROUND(130 * 0.40)
        ELSE ROUND(130 * 0.45)
    END,
    -- major_credits_earned
    CASE ts.category
        WHEN 'medical' THEN ROUND(agg.total_earned * 0.55)
        WHEN 'nursing' THEN ROUND(agg.total_earned * 0.55)
        WHEN 'pharmacy' THEN ROUND(agg.total_earned * 0.55)
        WHEN 'health' THEN ROUND(agg.total_earned * 0.55)
        WHEN 'engineering' THEN ROUND(agg.total_earned * 0.50)
        WHEN 'humanities' THEN ROUND(agg.total_earned * 0.40)
        WHEN 'education' THEN ROUND(agg.total_earned * 0.40)
        WHEN 'law_admin' THEN ROUND(agg.total_earned * 0.40)
        ELSE ROUND(agg.total_earned * 0.45)
    END,
    -- liberal_credits_required
    CASE ts.category
        WHEN 'medical' THEN ROUND(140 * 0.35)
        WHEN 'nursing' THEN ROUND(140 * 0.35)
        WHEN 'pharmacy' THEN ROUND(150 * 0.35)
        WHEN 'health' THEN ROUND(140 * 0.35)
        WHEN 'engineering' THEN ROUND(130 * 0.35)
        WHEN 'humanities' THEN ROUND(130 * 0.45)
        WHEN 'education' THEN ROUND(130 * 0.45)
        WHEN 'law_admin' THEN ROUND(130 * 0.45)
        ELSE ROUND(130 * 0.40)
    END,
    -- liberal_credits_earned
    CASE ts.category
        WHEN 'medical' THEN ROUND(agg.total_earned * 0.35)
        WHEN 'nursing' THEN ROUND(agg.total_earned * 0.35)
        WHEN 'pharmacy' THEN ROUND(agg.total_earned * 0.35)
        WHEN 'health' THEN ROUND(agg.total_earned * 0.35)
        WHEN 'engineering' THEN ROUND(agg.total_earned * 0.35)
        WHEN 'humanities' THEN ROUND(agg.total_earned * 0.45)
        WHEN 'education' THEN ROUND(agg.total_earned * 0.45)
        WHEN 'law_admin' THEN ROUND(agg.total_earned * 0.45)
        ELSE ROUND(agg.total_earned * 0.40)
    END,
    -- cumulative_gpa
    agg.cum_gpa,
    -- major_gpa (약간 높게)
    LEAST(4.50, agg.cum_gpa + ROUND(abs(hashtext(agg.student_id)::numeric % 30) / 100.0, 2)),
    -- completion_rate
    ROUND(agg.total_earned * 100.0 / CASE ts.category WHEN 'medical' THEN 140 WHEN 'pharmacy' THEN 150 ELSE 130 END, 1),
    'BULK_FIX',
    NOW()
FROM (
    SELECT
        g.student_id,
        SUM(g.credits_earned) AS total_earned,
        ROUND(SUM(g.grade_point * g.credits_earned) / NULLIF(SUM(g.credits_earned), 0), 2) AS cum_gpa
    FROM tb_grade g
    JOIN tmp_target_students ts2 ON g.student_id = ts2.student_id
    GROUP BY g.student_id
) agg
JOIN tmp_target_students ts ON agg.student_id = ts.student_id;

-- 수강 없는 학생(863명)에 대해서도 기본 누적요약 생성
INSERT INTO tb_cumulative_summary (
    summary_id, student_id,
    total_credits_required, total_credits_earned,
    major_credits_required, major_credits_earned,
    liberal_credits_required, liberal_credits_earned,
    cumulative_gpa, major_gpa, completion_rate,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    CASE ts.category WHEN 'medical' THEN 140 WHEN 'pharmacy' THEN 150 ELSE 130 END,
    0, -- no credits
    CASE ts.category
        WHEN 'medical' THEN ROUND(140 * 0.55)
        WHEN 'nursing' THEN ROUND(140 * 0.55)
        WHEN 'pharmacy' THEN ROUND(150 * 0.55)
        WHEN 'health' THEN ROUND(140 * 0.55)
        WHEN 'engineering' THEN ROUND(130 * 0.50)
        WHEN 'humanities' THEN ROUND(130 * 0.40)
        WHEN 'education' THEN ROUND(130 * 0.40)
        WHEN 'law_admin' THEN ROUND(130 * 0.40)
        ELSE ROUND(130 * 0.45)
    END,
    0,
    CASE ts.category
        WHEN 'medical' THEN ROUND(140 * 0.35)
        WHEN 'nursing' THEN ROUND(140 * 0.35)
        WHEN 'pharmacy' THEN ROUND(150 * 0.35)
        WHEN 'health' THEN ROUND(140 * 0.35)
        WHEN 'engineering' THEN ROUND(130 * 0.35)
        WHEN 'humanities' THEN ROUND(130 * 0.45)
        WHEN 'education' THEN ROUND(130 * 0.45)
        WHEN 'law_admin' THEN ROUND(130 * 0.45)
        ELSE ROUND(130 * 0.40)
    END,
    0,
    0.00,
    0.00,
    0.0,
    'BULK_FIX',
    NOW()
FROM tmp_target_students ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_cumulative_summary cs WHERE cs.student_id = ts.student_id
);

DO $$ BEGIN RAISE NOTICE 'Part 4 완료: 누적 요약 생성'; END $$;

-- =====================================================
-- Part 5: 카테고리별 스킬 마스터 데이터 + 학생 스킬
-- =====================================================

-- 5-1: 스킬 마스터 데이터 삽입 (ON CONFLICT DO NOTHING)
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    -- medical
    ('SKM001', '생물학', 'Biology', ARRAY['생물','생명과학','Biology'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKM002', '의학입문', 'Introduction to Medicine', ARRAY['의학개론','의학기초','PreMed'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKM003', '화학', 'Chemistry', ARRAY['일반화학','Chemistry','화학기초'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKM004', '인체해부학', 'Human Anatomy', ARRAY['해부학','Anatomy','인체구조'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKM005', '의학영어', 'Medical English', ARRAY['Medical English','의학용어'], 'language', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKM006', '의료윤리', 'Medical Ethics', ARRAY['생명윤리','Bioethics'], 'domain', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKM007', '의학통계', 'Medical Statistics', ARRAY['생물통계','Biostatistics'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    -- nursing
    ('SKN001', '기본간호학', 'Fundamentals of Nursing', ARRAY['기본간호','간호기초'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKN002', '성인간호학', 'Adult Nursing', ARRAY['성인간호','Adult Health Nursing'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKN003', '해부학', 'Anatomy', ARRAY['인체해부','해부생리'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKN004', '약리학', 'Pharmacology', ARRAY['약물학','Pharmacology'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKN005', '간호윤리', 'Nursing Ethics', ARRAY['간호전문직','Nursing Professionalism'], 'domain', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKN006', '의학용어', 'Medical Terminology', ARRAY['의학용어','Medical Term'], 'language', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKN007', '건강사정', 'Health Assessment', ARRAY['건강사정','Physical Assessment'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    -- pharmacy
    ('SKP001', '약리학_P', 'Pharmacology', ARRAY['약리','약물작용'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKP002', '유기화학', 'Organic Chemistry', ARRAY['유기화학','Organic Chem'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKP003', '생화학', 'Biochemistry', ARRAY['생화학','Biochem'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKP004', '약물분석', 'Drug Analysis', ARRAY['약물분석','Drug Assay'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKP005', '제약공정', 'Pharmaceutical Process', ARRAY['제약','제조공정'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKP006', '약사법규', 'Pharmacy Law', ARRAY['약사법','약사윤리'], 'domain', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKP007', '임상약학', 'Clinical Pharmacy', ARRAY['임상약학','Clinical Pharm'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    -- health
    ('SKH001', '해부학_H', 'Anatomy', ARRAY['해부학','인체해부'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKH002', '생리학', 'Physiology', ARRAY['생리학','인체생리'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKH003', '병리학', 'Pathology', ARRAY['병리학','Pathology'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKH004', '재활의학', 'Rehabilitation Medicine', ARRAY['재활','물리치료'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKH005', '의료법규', 'Medical Law', ARRAY['의료법','보건법규'], 'domain', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKH006', '건강관리', 'Health Management', ARRAY['건강관리','건강증진'], 'domain', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKH007', '응급처치', 'First Aid', ARRAY['응급처치','Emergency Care'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    -- engineering
    ('SKE001', 'Python', 'Python', ARRAY['파이썬','Python3'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKE002', 'Java', 'Java', ARRAY['자바','Java SE'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKE003', 'SQL', 'SQL', ARRAY['SQL','RDBMS','데이터베이스'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKE004', '데이터구조', 'Data Structures', ARRAY['자료구조','Data Structure'], 'technical', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKE005', '알고리즘', 'Algorithms', ARRAY['알고리즘','Algorithm'], 'technical', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKE006', 'Git', 'Git', ARRAY['Git','버전관리','GitHub'], 'technical', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKE007', '클라우드', 'Cloud Computing', ARRAY['클라우드','AWS','Cloud'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    -- business
    ('SKB001', '경영전략', 'Business Strategy', ARRAY['경영전략','Strategy'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKB002', '마케팅', 'Marketing', ARRAY['마케팅','Marketing'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKB003', '회계학', 'Accounting', ARRAY['회계','Accounting'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKB004', '재무관리', 'Financial Management', ARRAY['재무','Finance'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKB005', '데이터분석', 'Data Analysis', ARRAY['데이터분석','Analytics'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKB006', '비즈니스영어', 'Business English', ARRAY['비즈니스영어','Business Eng'], 'language', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKB007', '프레젠테이션', 'Presentation', ARRAY['프레젠테이션','발표'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    -- law_admin
    ('SKL001', '헌법', 'Constitutional Law', ARRAY['헌법','Constitutional'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKL002', '민법', 'Civil Law', ARRAY['민법','Civil Law'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKL003', '행정법', 'Administrative Law', ARRAY['행정법','Admin Law'], 'domain', 4, 'Y', 'BULK_FIX', NOW()),
    ('SKL004', '법률영어', 'Legal English', ARRAY['법률영어','Legal English'], 'language', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKL005', '논리적사고', 'Logical Thinking', ARRAY['논리학','논리적사고'], 'soft', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKL006', '판례분석', 'Case Analysis', ARRAY['판례분석','Case Study'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKL007', '법률문서작성', 'Legal Writing', ARRAY['법률문서','Legal Writing'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    -- education
    ('SKD001', '교육심리', 'Educational Psychology', ARRAY['교육심리','Edu Psychology'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKD002', '교수법', 'Teaching Methods', ARRAY['교수법','교수학습'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKD003', '상담기법', 'Counseling Techniques', ARRAY['상담','Counseling'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKD004', '교육과정', 'Curriculum Studies', ARRAY['교육과정','Curriculum'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKD005', '아동발달', 'Child Development', ARRAY['아동발달','발달심리'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKD006', '교육평가', 'Educational Assessment', ARRAY['교육평가','평가'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKD007', '특수교육', 'Special Education', ARRAY['특수교육','장애교육'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    -- humanities
    ('SKU001', '글쓰기', 'Writing', ARRAY['글쓰기','작문','Writing'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKU002', '비판적사고', 'Critical Thinking', ARRAY['비판적사고','Critical Thinking'], 'soft', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKU003', '외국어', 'Foreign Languages', ARRAY['외국어','어학'], 'language', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKU004', '연구방법론', 'Research Methodology', ARRAY['연구방법','Research Method'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKU005', '문화분석', 'Cultural Analysis', ARRAY['문화분석','문화연구'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKU006', '문헌해독', 'Textual Analysis', ARRAY['문헌해독','문헌분석'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKU007', '토론', 'Debate', ARRAY['토론','발표','Debate'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    -- arts
    ('SKA001', '예술이론', 'Art Theory', ARRAY['예술이론','예술학'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKA002', '디자인기초', 'Design Fundamentals', ARRAY['디자인기초','기초디자인'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKA003', '미디어제작', 'Media Production', ARRAY['미디어제작','영상제작'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKA004', '음악이론', 'Music Theory', ARRAY['음악이론','Music Theory'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKA005', '공연기획', 'Performance Planning', ARRAY['공연기획','공연제작'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKA006', '창작실습', 'Creative Practice', ARRAY['창작실습','창작'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKA007', '포트폴리오제작', 'Portfolio Production', ARRAY['포트폴리오제작','작품집'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    -- science
    ('SKS001', '일반화학', 'General Chemistry', ARRAY['일반화학','Gen Chem'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKS002', '일반물리', 'General Physics', ARRAY['일반물리','Physics'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKS003', '실험설계', 'Experimental Design', ARRAY['실험설계','실험방법'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKS004', '통계분석', 'Statistical Analysis', ARRAY['통계분석','통계학'], 'domain', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKS005', '데이터처리', 'Data Processing', ARRAY['데이터처리','데이터분석'], 'technical', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKS006', '논문작성', 'Academic Writing', ARRAY['논문작성','학술작성'], 'soft', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKS007', '연구윤리', 'Research Ethics', ARRAY['연구윤리','Research Ethics'], 'domain', 2, 'Y', 'BULK_FIX', NOW()),
    -- general
    ('SKG001', '의사소통', 'Communication', ARRAY['의사소통','커뮤니케이션'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKG002', '리더십', 'Leadership', ARRAY['리더십','Leadership'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKG003', '팀워크', 'Teamwork', ARRAY['팀워크','협업','Teamwork'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKG004', '문제해결', 'Problem Solving', ARRAY['문제해결','Problem Solving'], 'soft', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKG005', '영어', 'English', ARRAY['영어','English','TOEIC'], 'language', 3, 'Y', 'BULK_FIX', NOW()),
    ('SKG006', '프레젠테이션_G', 'Presentation', ARRAY['프레젠테이션','발표'], 'soft', 2, 'Y', 'BULK_FIX', NOW()),
    ('SKG007', '시간관리', 'Time Management', ARRAY['시간관리','Time Management'], 'soft', 2, 'Y', 'BULK_FIX', NOW())
ON CONFLICT (skill_cd) DO NOTHING;

-- 5-2: 기존 학생 스킬 삭제 (대상 학생)
DELETE FROM tb_student_skill ss
USING tmp_target_students ts
WHERE ss.student_id = ts.student_id;

-- 5-3: 카테고리별 스킬 매핑 TEMP TABLE
CREATE TEMP TABLE tmp_category_skills (category VARCHAR(20), skill_cd VARCHAR(20), skill_order INT);
INSERT INTO tmp_category_skills VALUES
    ('medical','SKM001',1),('medical','SKM002',2),('medical','SKM003',3),('medical','SKM004',4),('medical','SKM005',5),('medical','SKM006',6),('medical','SKM007',7),
    ('nursing','SKN001',1),('nursing','SKN002',2),('nursing','SKN003',3),('nursing','SKN004',4),('nursing','SKN005',5),('nursing','SKN006',6),('nursing','SKN007',7),
    ('pharmacy','SKP001',1),('pharmacy','SKP002',2),('pharmacy','SKP003',3),('pharmacy','SKP004',4),('pharmacy','SKP005',5),('pharmacy','SKP006',6),('pharmacy','SKP007',7),
    ('health','SKH001',1),('health','SKH002',2),('health','SKH003',3),('health','SKH004',4),('health','SKH005',5),('health','SKH006',6),('health','SKH007',7),
    ('engineering','SKE001',1),('engineering','SKE002',2),('engineering','SKE003',3),('engineering','SKE004',4),('engineering','SKE005',5),('engineering','SKE006',6),('engineering','SKE007',7),
    ('business','SKB001',1),('business','SKB002',2),('business','SKB003',3),('business','SKB004',4),('business','SKB005',5),('business','SKB006',6),('business','SKB007',7),
    ('law_admin','SKL001',1),('law_admin','SKL002',2),('law_admin','SKL003',3),('law_admin','SKL004',4),('law_admin','SKL005',5),('law_admin','SKL006',6),('law_admin','SKL007',7),
    ('education','SKD001',1),('education','SKD002',2),('education','SKD003',3),('education','SKD004',4),('education','SKD005',5),('education','SKD006',6),('education','SKD007',7),
    ('humanities','SKU001',1),('humanities','SKU002',2),('humanities','SKU003',3),('humanities','SKU004',4),('humanities','SKU005',5),('humanities','SKU006',6),('humanities','SKU007',7),
    ('arts','SKA001',1),('arts','SKA002',2),('arts','SKA003',3),('arts','SKA004',4),('arts','SKA005',5),('arts','SKA006',6),('arts','SKA007',7),
    ('science','SKS001',1),('science','SKS002',2),('science','SKS003',3),('science','SKS004',4),('science','SKS005',5),('science','SKS006',6),('science','SKS007',7),
    ('general','SKG001',1),('general','SKG002',2),('general','SKG003',3),('general','SKG004',4),('general','SKG005',5),('general','SKG006',6),('general','SKG007',7);

-- 5-4: 학생별 카테고리 기반 스킬 INSERT (7개씩)
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    ts.student_id,
    cs.skill_cd,
    -- current_level: 학년 기반 (1학년→1~2, 2학년→2~3, 3학년→3~4)
    LEAST(5, GREATEST(1, ts.current_grade + (abs(hashtext(ts.student_id || cs.skill_cd)) % 2))),
    -- target_level: current + 1~2
    LEAST(5, GREATEST(3, ts.current_grade + (abs(hashtext(ts.student_id || cs.skill_cd)) % 2) + 1 + abs(hashtext(cs.skill_cd || ts.student_id)) % 2)),
    -- evidence_count
    abs(hashtext(ts.student_id || cs.skill_cd)) % 5,
    -- last_verified_date
    CASE WHEN abs(hashtext(ts.student_id || cs.skill_cd)) % 3 = 0 THEN NULL ELSE '2025-12-15'::date END,
    -- verification_source
    CASE abs(hashtext(ts.student_id || cs.skill_cd)) % 3
        WHEN 0 THEN 'self_assessment'
        WHEN 1 THEN 'course'
        ELSE 'project'
    END,
    -- trend
    CASE abs(hashtext(ts.student_id || cs.skill_cd || 'trend')) % 3
        WHEN 0 THEN 'up'
        WHEN 1 THEN 'stable'
        ELSE 'up'
    END,
    'BULK_FIX',
    NOW()
FROM tmp_target_students ts
JOIN tmp_category_skills cs ON ts.category = cs.category;

DO $$ BEGIN RAISE NOTICE 'Part 5 완료: 스킬 마스터 및 학생 스킬 생성'; END $$;

-- =====================================================
-- Part 6: 카테고리별 시뮬레이션 시나리오 교체
-- =====================================================

-- 기존 시나리오 삭제 (대상 학생)
DELETE FROM tb_simulation_scenario ss
USING tmp_target_students ts
WHERE ss.student_id = ts.student_id;

-- 카테고리별 시나리오 데이터 TEMP TABLE
CREATE TEMP TABLE tmp_scenario_data (
    category VARCHAR(20),
    scenario_type VARCHAR(30),
    title VARCHAR(200),
    description TEXT,
    base_state_template TEXT,
    changes_template TEXT,
    outcomes_template TEXT,
    confidence DECIMAL(3,2)
);

INSERT INTO tmp_scenario_data VALUES
-- medical
('medical', 'career_path', '의사 커리어 준비', '본과 진학 후 의사 국가시험 준비까지의 커리어 로드맵 시나리오',
 '{"career_goal": "의사", "field": "의학"}', '{"next_step": "본과 진학", "target_exam": "의사국가시험", "additional_activities": ["임상실습", "의학연구"]}', '{"career_readiness": 0.75, "exam_preparation": 0.80, "clinical_experience": 0.60}', 0.82),
('medical', 'skill_development', '기초의학 역량 강화', '해부학, 생리학, 생화학 등 기초의학 과목 심화 학습 시나리오',
 '{"key_subjects": ["생물학", "의학입문"]}', '{"additional_courses": ["해부학", "생리학", "생화학"], "study_group": true}', '{"knowledge_improvement": 0.85, "exam_readiness": 0.78, "confidence_boost": 0.70}', 0.80),
('medical', 'opportunity', '의료 봉사활동 참여 효과', '지역사회 의료봉사 및 임상관찰 프로그램 참여 시 예상 효과',
 '{"volunteer_experience": 0, "clinical_observation_hours": 0}', '{"volunteer_hours": 100, "clinical_observation": true, "target_organizations": ["지역보건소", "대학병원"]}', '{"empathy_development": 0.90, "clinical_awareness": 0.75, "portfolio_strength": 0.85}', 0.78),
-- nursing
('nursing', 'career_path', '간호사 커리어 준비', '간호사 면허시험 준비 및 임상간호 전문가 성장 경로 시나리오',
 '{"career_goal": "간호사", "field": "간호학"}', '{"target_exam": "간호사국가시험", "clinical_hours": 1000, "additional_activities": ["병원실습"]}', '{"career_readiness": 0.78, "exam_preparation": 0.82, "clinical_competency": 0.65}', 0.80),
('nursing', 'skill_development', '임상간호 역량 강화', '기본간호, 성인간호 등 임상간호 핵심 역량 강화 시나리오',
 '{"key_subjects": ["기본간호학", "성인간호학"]}', '{"additional_courses": ["아동간호학", "모성간호학"], "simulation_lab": true}', '{"clinical_skill": 0.82, "patient_care": 0.78, "emergency_response": 0.70}', 0.79),
('nursing', 'opportunity', '병원 실습 참여 효과', '대학병원 임상실습 참여를 통한 실무 역량 향상 시나리오',
 '{"clinical_hours": 0, "hospital_experience": false}', '{"target_hospital": "대학병원", "clinical_hours": 500, "mentoring": true}', '{"practical_skill": 0.88, "teamwork": 0.80, "professionalism": 0.85}', 0.81),
-- pharmacy
('pharmacy', 'career_path', '약사 커리어 준비', '약사 면허시험 준비 및 약학 전문가 성장 경로 시나리오',
 '{"career_goal": "약사", "field": "약학"}', '{"target_exam": "약사국가시험", "pharmacy_practice": true, "research_participation": true}', '{"career_readiness": 0.76, "exam_preparation": 0.80, "pharmaceutical_knowledge": 0.72}', 0.80),
('pharmacy', 'skill_development', '약학 전문 역량 강화', '약리학, 약물분석 등 약학 핵심 과목 심화 학습 시나리오',
 '{"key_subjects": ["약리학", "유기화학"]}', '{"additional_courses": ["임상약학", "약물분석"], "lab_practice": true}', '{"pharmaceutical_skill": 0.83, "lab_competency": 0.78, "drug_knowledge": 0.80}', 0.79),
('pharmacy', 'opportunity', '제약회사 인턴십 참여', '제약회사 인턴십을 통한 산업 현장 경험 및 네트워크 구축',
 '{"internship_experience": false, "industry_contact": 0}', '{"target_company": "제약회사", "internship_months": 3, "research_project": true}', '{"industry_knowledge": 0.85, "practical_skill": 0.78, "network_building": 0.80}', 0.77),
-- health
('health', 'career_path', '보건전문가 커리어 준비', '보건의료 전문가 자격 취득 및 의료기관 취업 경로 시나리오',
 '{"career_goal": "보건전문가", "field": "보건"}', '{"target_certification": "보건전문자격증", "clinical_practice": true}', '{"career_readiness": 0.74, "certification_prep": 0.78, "clinical_skill": 0.68}', 0.78),
('health', 'skill_development', '보건의료 역량 강화', '해부학, 생리학, 재활의학 등 보건의료 핵심 역량 강화 시나리오',
 '{"key_subjects": ["해부학", "생리학"]}', '{"additional_courses": ["재활의학", "병리학"], "practical_training": true}', '{"medical_knowledge": 0.80, "practical_skill": 0.75, "patient_care": 0.72}', 0.78),
('health', 'opportunity', '의료기관 실습 참여', '의료기관 현장실습을 통한 실무 능력 배양 시나리오',
 '{"clinical_hours": 0, "facility_experience": false}', '{"target_facility": "의료기관", "practice_hours": 300, "supervisor_mentoring": true}', '{"practical_competency": 0.85, "professional_growth": 0.78, "teamwork": 0.80}', 0.79),
-- engineering
('engineering', 'career_path', 'IT 전문가 커리어 준비', 'IT 개발자/엔지니어 취업 준비 및 기술 역량 강화 시나리오',
 '{"career_goal": "IT전문가", "field": "공학"}', '{"target_role": "소프트웨어 개발자", "certifications": ["정보처리기사"], "project_portfolio": true}', '{"career_readiness": 0.76, "technical_skill": 0.80, "portfolio_strength": 0.72}', 0.80),
('engineering', 'skill_development', '프로그래밍 역량 강화', 'Python, Java 등 프로그래밍 언어 및 알고리즘 역량 강화 시나리오',
 '{"key_subjects": ["Python", "Java"]}', '{"additional_skills": ["알고리즘", "클라우드"], "coding_test_prep": true}', '{"coding_skill": 0.85, "algorithm_ability": 0.78, "system_design": 0.70}', 0.81),
('engineering', 'opportunity', 'IT 기업 인턴십 참여', 'IT 기업 인턴십을 통한 실무 경험 및 기술 스택 확장',
 '{"internship_experience": false, "project_count": 0}', '{"target_company": "IT기업", "internship_months": 6, "team_project": true}', '{"practical_skill": 0.88, "industry_knowledge": 0.80, "network": 0.75}', 0.79),
-- business
('business', 'career_path', '경영 전문가 커리어 준비', '경영 컨설턴트/기업 관리자 커리어 준비 시나리오',
 '{"career_goal": "경영전문가", "field": "경영학"}', '{"target_role": "경영 컨설턴트", "certifications": ["CPA", "경영지도사"], "mba_plan": true}', '{"career_readiness": 0.74, "business_acumen": 0.78, "leadership": 0.70}', 0.78),
('business', 'skill_development', '비즈니스 분석 역량 강화', '데이터 분석, 재무 분석 등 비즈니스 핵심 역량 강화 시나리오',
 '{"key_subjects": ["경영전략", "마케팅"]}', '{"additional_skills": ["데이터분석", "재무분석"], "case_study": true}', '{"analytical_skill": 0.83, "strategic_thinking": 0.78, "presentation": 0.80}', 0.79),
('business', 'opportunity', '기업 인턴십 참여 효과', '대기업/중견기업 인턴십을 통한 실무 경험 시나리오',
 '{"internship_experience": false, "business_project": 0}', '{"target_company": "대기업", "internship_months": 3, "department": "경영기획"}', '{"business_skill": 0.85, "network": 0.80, "career_clarity": 0.82}', 0.80),
-- law_admin
('law_admin', 'career_path', '법률/행정 전문가 커리어', '법조인/행정 전문가 자격 취득 및 진로 설계 시나리오',
 '{"career_goal": "법률전문가", "field": "법학/행정"}', '{"target_exam": "법학적성시험", "certifications": ["행정사"], "bar_exam": true}', '{"career_readiness": 0.72, "legal_knowledge": 0.78, "exam_preparation": 0.70}', 0.77),
('law_admin', 'skill_development', '법률 전문 역량 강화', '헌법, 민법, 행정법 등 법학 핵심 과목 심화 학습 시나리오',
 '{"key_subjects": ["헌법", "민법"]}', '{"additional_courses": ["형법", "상법"], "moot_court": true}', '{"legal_analysis": 0.83, "writing_skill": 0.78, "argumentation": 0.80}', 0.79),
('law_admin', 'opportunity', '법률사무소 실습 참여', '법률사무소/공공기관 실습을 통한 실무 경험 시나리오',
 '{"internship_experience": false, "case_count": 0}', '{"target_firm": "법률사무소", "practice_months": 3, "case_study": true}', '{"practical_skill": 0.85, "legal_writing": 0.80, "client_communication": 0.75}', 0.78),
-- education
('education', 'career_path', '교육 전문가 커리어 준비', '교원 임용시험 준비 및 교육 전문가 성장 경로 시나리오',
 '{"career_goal": "교육전문가", "field": "교육학"}', '{"target_exam": "교원임용시험", "teaching_practice": true, "counseling_cert": true}', '{"career_readiness": 0.75, "teaching_skill": 0.80, "counseling_ability": 0.68}', 0.79),
('education', 'skill_development', '교육·상담 역량 강화', '교육심리, 교수법, 상담기법 등 교육 핵심 역량 강화 시나리오',
 '{"key_subjects": ["교육심리", "교수법"]}', '{"additional_skills": ["상담기법", "교육평가"], "micro_teaching": true}', '{"teaching_method": 0.83, "student_understanding": 0.80, "assessment_skill": 0.75}', 0.80),
('education', 'opportunity', '교육기관 실습 참여', '학교/교육기관 교생실습을 통한 교육 현장 경험 시나리오',
 '{"teaching_hours": 0, "school_experience": false}', '{"target_school": "중학교", "practice_weeks": 4, "class_management": true}', '{"practical_teaching": 0.88, "classroom_management": 0.78, "student_rapport": 0.82}', 0.80),
-- humanities
('humanities', 'career_path', '인문학 전문가 커리어', '학술연구/문화산업/교육 분야 커리어 설계 시나리오',
 '{"career_goal": "인문학전문가", "field": "인문학"}', '{"target_path": "대학원/문화산업", "language_cert": true, "research_paper": true}', '{"career_readiness": 0.70, "academic_skill": 0.78, "cultural_literacy": 0.75}', 0.76),
('humanities', 'skill_development', '학술 연구 역량 강화', '글쓰기, 연구방법론, 비판적사고 등 학술 역량 강화 시나리오',
 '{"key_subjects": ["글쓰기", "연구방법론"]}', '{"additional_skills": ["외국어", "문헌해독"], "thesis_writing": true}', '{"research_skill": 0.82, "writing_quality": 0.80, "critical_analysis": 0.78}', 0.78),
('humanities', 'opportunity', '해외 교환학생 참여 효과', '해외 대학 교환학생 프로그램 참여를 통한 글로벌 역량 강화',
 '{"exchange_experience": false, "language_level": "intermediate"}', '{"target_country": "영어권", "exchange_semester": 1, "cultural_immersion": true}', '{"language_improvement": 0.88, "cultural_competency": 0.85, "global_perspective": 0.82}', 0.80),
-- arts
('arts', 'career_path', '예술 전문가 커리어 준비', '예술/디자인/공연 분야 전문가 성장 및 진로 설계 시나리오',
 '{"career_goal": "예술전문가", "field": "예술"}', '{"target_path": "크리에이터/디자이너", "portfolio_building": true, "exhibition": true}', '{"career_readiness": 0.72, "creative_skill": 0.80, "portfolio_quality": 0.75}', 0.77),
('arts', 'skill_development', '창작·디자인 역량 강화', '예술이론, 디자인, 미디어 제작 등 창작 역량 강화 시나리오',
 '{"key_subjects": ["예술이론", "디자인기초"]}', '{"additional_skills": ["미디어제작", "창작실습"], "workshop": true}', '{"creative_ability": 0.85, "technical_skill": 0.78, "aesthetic_sense": 0.80}', 0.79),
('arts', 'opportunity', '공모전·전시회 참여 효과', '작품 공모전/전시회 참여를 통한 포트폴리오 강화 시나리오',
 '{"competition_count": 0, "exhibition_count": 0}', '{"target_competitions": 3, "solo_exhibition": true, "collaboration_project": true}', '{"portfolio_strength": 0.88, "recognition": 0.75, "creative_confidence": 0.82}', 0.78),
-- science
('science', 'career_path', '연구원 커리어 준비', '연구원/과학자 진로 설계 및 대학원 진학 준비 시나리오',
 '{"career_goal": "연구원", "field": "자연과학"}', '{"target_path": "대학원/연구소", "research_paper": true, "lab_experience": true}', '{"career_readiness": 0.74, "research_skill": 0.80, "academic_achievement": 0.72}', 0.78),
('science', 'skill_development', '연구·실험 역량 강화', '실험설계, 통계분석, 데이터처리 등 연구 역량 강화 시나리오',
 '{"key_subjects": ["일반화학", "일반물리"]}', '{"additional_skills": ["실험설계", "통계분석"], "research_project": true}', '{"experimental_skill": 0.83, "data_analysis": 0.80, "scientific_writing": 0.75}', 0.79),
('science', 'opportunity', '연구실 인턴 참여 효과', '대학 연구실 학부 인턴 참여를 통한 연구 경험 축적',
 '{"lab_experience": false, "research_hours": 0}', '{"target_lab": "대학연구실", "intern_months": 6, "paper_contribution": true}', '{"research_competency": 0.88, "lab_skill": 0.82, "academic_network": 0.78}', 0.80),
-- general
('general', 'career_path', '전공 관련 커리어 준비', '전공 분야 관련 진로 탐색 및 커리어 설계 시나리오',
 '{"career_goal": "전공관련직", "field": "일반"}', '{"career_exploration": true, "skill_assessment": true, "mentoring": true}', '{"career_readiness": 0.70, "self_awareness": 0.75, "skill_development": 0.68}', 0.75),
('general', 'skill_development', '핵심 역량 강화', '의사소통, 문제해결, 리더십 등 핵심 역량 강화 시나리오',
 '{"key_subjects": ["의사소통", "문제해결"]}', '{"additional_skills": ["리더십", "팀워크"], "soft_skill_workshop": true}', '{"communication": 0.82, "problem_solving": 0.78, "leadership": 0.75}', 0.78),
('general', 'opportunity', '해외 교환학생 참여 효과', '해외 교환학생 프로그램을 통한 글로벌 역량 및 시야 확장',
 '{"exchange_experience": false, "global_competency": "low"}', '{"target_program": "교환학생", "semester_count": 1, "language_study": true}', '{"global_perspective": 0.85, "language_skill": 0.80, "adaptability": 0.82}', 0.78);

-- 시나리오 INSERT (학생별 3개씩)
INSERT INTO tb_simulation_scenario (scenario_id, student_id, scenario_type, title, description, base_state, changes, predicted_outcomes, confidence_level, created_at, is_favorite, ins_user_id, ins_dt)
SELECT
    gen_random_uuid(),
    ts.student_id,
    sd.scenario_type,
    sd.title,
    sd.description,
    sd.base_state_template::jsonb || jsonb_build_object('current_grade', ts.current_grade, 'gpa', COALESCE((SELECT cs.cumulative_gpa FROM tb_cumulative_summary cs WHERE cs.student_id = ts.student_id), 0.00)),
    sd.changes_template::jsonb,
    sd.outcomes_template::jsonb,
    sd.confidence,
    NOW(),
    CASE WHEN sd.scenario_type = 'career_path' THEN true ELSE false END,
    'BULK_FIX',
    NOW()
FROM tmp_target_students ts
JOIN tmp_scenario_data sd ON ts.category = sd.category;

DO $$ BEGIN RAISE NOTICE 'Part 6 완료: 시뮬레이션 시나리오 생성'; END $$;

-- =====================================================
-- Part 7: 카테고리별 포트폴리오 교체
-- =====================================================

-- 기존 포트폴리오 삭제 (대상 학생)
DELETE FROM tb_portfolio p
USING tmp_target_students ts
WHERE p.student_id = ts.student_id;

-- 카테고리별 포트폴리오 데이터 TEMP TABLE
CREATE TEMP TABLE tmp_portfolio_data (
    category VARCHAR(20),
    item_type VARCHAR(50),
    artifact_type VARCHAR(50),
    title_suffix VARCHAR(200),
    description TEXT,
    skills_json TEXT,
    display_order INT
);

INSERT INTO tmp_portfolio_data VALUES
-- medical
('medical', 'certification', 'certification', 'TOEIC 850점', '의학 논문 독해 및 국제 학회 참여를 위한 영어 능력 인증', '["영어", "의학영어", "학술영어"]', 1),
('medical', 'project', 'project', '기초의학 연구 참여', '생물학 실험실에서 기초 연구에 학부생으로 참여하여 실험 보조 및 데이터 분석 수행', '["생물학", "실험설계", "데이터분석"]', 2),
('medical', 'experience', 'experience', '지역사회 의료봉사', '지역 보건소 건강검진 보조 및 건강교육 봉사활동 참여', '["의료봉사", "건강교육", "의료윤리"]', 3),
('medical', 'paper', 'paper', '의학입문 학술보고서', '의학입문 수업에서 작성한 학술 보고서 (우수 보고서 선정)', '["의학입문", "학술작성", "비판적사고"]', 4),
-- nursing
('nursing', 'certification', 'certification', 'BLS 자격증', '기본심폐소생술(BLS) Provider 자격 취득', '["응급처치", "심폐소생술", "환자관리"]', 1),
('nursing', 'project', 'project', '간호 사례연구', '성인간호학 수업에서 수행한 임상 사례연구 프로젝트', '["성인간호학", "사례분석", "비판적사고"]', 2),
('nursing', 'experience', 'experience', '병원 임상실습', '대학병원에서 수행한 임상간호 실습 경험', '["기본간호학", "환자관리", "의료커뮤니케이션"]', 3),
('nursing', 'award', 'award', '간호학술대회 발표', '교내 간호학술대회에서 우수 발표상 수상', '["학술발표", "간호연구", "프레젠테이션"]', 4),
-- pharmacy
('pharmacy', 'certification', 'certification', '약사면허 준비 TOEIC', '약학 관련 해외 저널 독해를 위한 영어 능력 인증', '["영어", "약학영어", "학술영어"]', 1),
('pharmacy', 'project', 'project', '약물 분석 프로젝트', '약물분석 실험실에서 의약품 분석 프로젝트 수행', '["약물분석", "유기화학", "실험설계"]', 2),
('pharmacy', 'experience', 'experience', '약국 실습 경험', '지역 약국에서의 약제 조제 및 복약 지도 실습', '["약리학", "복약지도", "약사법규"]', 3),
('pharmacy', 'paper', 'paper', '약학 논문 발표', '약리학 관련 학부 논문 작성 및 학술대회 발표', '["약리학", "논문작성", "연구방법론"]', 4),
-- health
('health', 'certification', 'certification', '보건교육사 자격증', '보건교육사 3급 자격증 취득', '["보건교육", "건강관리", "건강증진"]', 1),
('health', 'project', 'project', '건강증진 프로그램 개발', '지역사회 건강증진 프로그램 기획 및 운영 프로젝트', '["건강관리", "프로그램기획", "보건교육"]', 2),
('health', 'experience', 'experience', '의료기관 실습', '의료기관에서의 보건의료 현장실습 경험', '["해부학", "생리학", "의료법규"]', 3),
('health', 'award', 'award', '보건 학술대회 발표', '교내 보건 학술대회에서 우수 논문 발표상 수상', '["연구방법론", "통계분석", "학술발표"]', 4),
-- engineering
('engineering', 'certification', 'certification', '정보처리기사 자격증', '한국산업인력공단 정보처리기사 자격증 취득', '["Python", "SQL", "알고리즘"]', 1),
('engineering', 'project', 'project', '웹 애플리케이션 개발', '팀 프로젝트로 웹 애플리케이션 설계 및 개발', '["Java", "SQL", "Git"]', 2),
('engineering', 'experience', 'experience', 'IT 기업 인턴십', 'IT 기업에서 소프트웨어 개발 인턴십 경험', '["Python", "클라우드", "Git"]', 3),
('engineering', 'award', 'award', '교내 해커톤 수상', '교내 해커톤 대회에서 우수상 수상', '["Python", "알고리즘", "팀워크"]', 4),
-- business
('business', 'certification', 'certification', 'TOEIC 900점', '글로벌 비즈니스 커뮤니케이션을 위한 영어 능력 인증', '["비즈니스영어", "영어", "프레젠테이션"]', 1),
('business', 'project', 'project', '비즈니스 전략 분석', '경영전략 수업에서 실제 기업 사례 분석 프로젝트 수행', '["경영전략", "데이터분석", "마케팅"]', 2),
('business', 'experience', 'experience', '기업 인턴십 경험', '기업 경영기획팀에서의 인턴십 실무 경험', '["경영전략", "재무관리", "프레젠테이션"]', 3),
('business', 'award', 'award', '창업 경진대회 수상', '교내 창업 경진대회에서 우수상 수상', '["비즈니스모델", "마케팅", "프레젠테이션"]', 4),
-- law_admin
('law_admin', 'certification', 'certification', '한국사능력검정시험', '한국사능력검정시험 1급 취득', '["한국사", "역사분석", "논리적사고"]', 1),
('law_admin', 'project', 'project', '법률 사례 분석', '민법/헌법 수업에서 주요 판례 분석 프로젝트 수행', '["민법", "헌법", "판례분석"]', 2),
('law_admin', 'experience', 'experience', '법률사무소 실습', '법률사무소에서의 법률 실무 실습 경험', '["법률문서작성", "판례분석", "법률영어"]', 3),
('law_admin', 'award', 'award', '모의재판 대회 수상', '교내 모의재판 대회에서 우수 변론상 수상', '["논리적사고", "법률문서작성", "프레젠테이션"]', 4),
-- education
('education', 'certification', 'certification', '교원자격증 준비', '교원자격증 취득을 위한 교직 이수 과정 수료', '["교육과정", "교수법", "교육평가"]', 1),
('education', 'project', 'project', '교육프로그램 개발', '교육학 수업에서 수행한 교육 프로그램 기획 및 개발 프로젝트', '["교수법", "교육과정", "아동발달"]', 2),
('education', 'experience', 'experience', '교육봉사활동', '지역사회 아동센터에서의 교육봉사 및 멘토링 활동', '["교육심리", "상담기법", "아동발달"]', 3),
('education', 'award', 'award', '교육 학술발표', '교내 교육학 학술대회에서 우수 발표상 수상', '["연구방법론", "교육평가", "학술발표"]', 4),
-- humanities
('humanities', 'certification', 'certification', 'TOEIC 800점', '인문학 연구 및 해외 학술 교류를 위한 영어 능력 인증', '["외국어", "영어", "학술영어"]', 1),
('humanities', 'project', 'project', '문화콘텐츠 기획', '문화콘텐츠 기획 수업에서 수행한 프로젝트', '["문화분석", "글쓰기", "비판적사고"]', 2),
('humanities', 'experience', 'experience', '해외 교환학생', '해외 대학 교환학생 프로그램 참여 경험', '["외국어", "문화분석", "글로벌역량"]', 3),
('humanities', 'paper', 'paper', '학술 논문 발표', '인문학 학술대회에서 연구 논문 발표', '["연구방법론", "글쓰기", "문헌해독"]', 4),
-- arts
('arts', 'certification', 'certification', '포트폴리오 인증', '전문가 심사를 통한 창작 포트폴리오 인증', '["창작실습", "포트폴리오제작", "디자인기초"]', 1),
('arts', 'project', 'project', '창작 작품 프로젝트', '예술 창작 수업에서 수행한 개인/팀 창작 프로젝트', '["예술이론", "창작실습", "디자인기초"]', 2),
('arts', 'experience', 'experience', '전시회/공연 참여', '교내외 전시회 또는 공연에 작품 출품 및 참여', '["공연기획", "창작실습", "미디어제작"]', 3),
('arts', 'award', 'award', '공모전 수상', '예술/디자인 공모전에서 수상', '["창작실습", "디자인기초", "포트폴리오제작"]', 4),
-- science
('science', 'certification', 'certification', '연구윤리 인증', '연구윤리 교육 이수 및 인증 취득', '["연구윤리", "실험설계", "학술규범"]', 1),
('science', 'project', 'project', '실험 연구 프로젝트', '자연과학 분야 실험 연구 프로젝트 수행', '["실험설계", "통계분석", "데이터처리"]', 2),
('science', 'experience', 'experience', '연구실 인턴십', '대학 연구실에서의 학부 연구 인턴십 경험', '["일반화학", "일반물리", "실험설계"]', 3),
('science', 'paper', 'paper', '학술대회 포스터 발표', '자연과학 학술대회에서 포스터 발표', '["논문작성", "통계분석", "연구윤리"]', 4),
-- general
('general', 'certification', 'certification', 'TOEIC 750점', '취업 준비를 위한 공인 영어 능력 인증', '["영어", "의사소통", "자기개발"]', 1),
('general', 'project', 'project', '자유주제 프로젝트', '교과 수업에서 수행한 자유주제 팀 프로젝트', '["팀워크", "문제해결", "프레젠테이션"]', 2),
('general', 'experience', 'experience', '교환학생 경험', '해외 또는 국내 타 대학 교환학생 프로그램 참여', '["의사소통", "리더십", "글로벌역량"]', 3),
('general', 'award', 'award', '교내 경진대회 수상', '교내 경진대회에서 입상', '["문제해결", "프레젠테이션", "팀워크"]', 4);

-- 포트폴리오 INSERT (학생별 4개씩)
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, image_url, is_featured, display_order, ins_user_id, ins_dt, artifact_type, url, is_primary)
SELECT
    gen_random_uuid(),
    ts.student_id,
    pd.item_type,
    pd.title_suffix || ' - ' || ts.student_nm,
    pd.description,
    -- start_date: 입학연도 기반 랜덤
    (ts.admission_year || '-' || LPAD((3 + abs(hashtext(ts.student_id || pd.item_type)) % 10)::text, 2, '0') || '-' ||
     LPAD((1 + abs(hashtext(ts.student_id || pd.title_suffix)) % 28)::text, 2, '0'))::date,
    -- end_date: start + 1~6개월
    (ts.admission_year || '-' || LPAD((3 + abs(hashtext(ts.student_id || pd.item_type)) % 10)::text, 2, '0') || '-' ||
     LPAD((1 + abs(hashtext(ts.student_id || pd.title_suffix)) % 28)::text, 2, '0'))::date + (30 + abs(hashtext(pd.item_type || ts.student_id)) % 150),
    pd.skills_json::jsonb,
    NULL,
    NULL,
    CASE WHEN pd.display_order = 1 THEN 'Y' ELSE 'N' END,
    pd.display_order,
    'BULK_FIX',
    NOW(),
    pd.artifact_type,
    NULL,
    CASE WHEN pd.display_order = 1 THEN true ELSE false END
FROM tmp_target_students ts
JOIN tmp_portfolio_data pd ON ts.category = pd.category;

DO $$ BEGIN RAISE NOTICE 'Part 7 완료: 포트폴리오 생성'; END $$;

-- =====================================================
-- Part 8: 정리 및 검증 카운트
-- =====================================================

-- TEMP TABLE은 트랜잭션 종료 시 자동 삭제되지만 명시적으로 삭제
DROP TABLE IF EXISTS tmp_portfolio_data;
DROP TABLE IF EXISTS tmp_scenario_data;
DROP TABLE IF EXISTS tmp_category_skills;
DROP TABLE IF EXISTS tmp_target_students;
DROP TABLE IF EXISTS tmp_dept_category;

DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE '전체 데이터 정합성 일괄 생성 완료';
    RAISE NOTICE '========================================';
END $$;

COMMIT;
