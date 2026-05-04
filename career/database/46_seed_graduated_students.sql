-- ============================================
-- IDINO Career - 2020~2021 입학 졸업생 전체 시드 스크립트
-- File: 46_seed_graduated_students.sql
-- Description: 졸업생(2020~2021 입학) 1,974명에 대해
--   성적, 역량, 스킬, 로드맵, 포트폴리오, 코칭, 성취, 리스크, 배지, 지도교수 등
--   전체 기능 작동에 필요한 데이터를 시드합니다.
-- Pattern: hashtext() 기반 결정적 랜덤, 기존 스크립트 43/44 패턴 준수
-- ============================================

SET search_path TO idino_career, public;

BEGIN;

-- ============================================
-- Part 0: 대상 학생 + 학과 카테고리 CTE (Temp Tables)
-- ============================================

-- 학과별 카테고리 매핑
CREATE TEMP TABLE tmp_dept_category_46 AS
SELECT d.department_cd,
       d.department_nm,
       CASE
           WHEN d.department_nm ~ '의예|의학' THEN 'medical'
           WHEN d.department_nm ~ '간호' THEN 'nursing'
           WHEN d.department_nm ~ '약학|약' THEN 'pharmacy'
           WHEN d.department_nm ~ '보건|치위생|치기공|물리치료|작업치료|방사선|임상병리|응급구조|의공학|재활|언어치료' THEN 'health'
           WHEN d.department_nm ~ '컴퓨터|소프트웨어|전자|전기|기계|토목|건축|화학공학|환경공학|산업공학|정보통신|AI|인공지능|데이터|IT' THEN 'engineering'
           WHEN d.department_nm ~ '경영|경제|회계|무역|금융|마케팅|국제통상|관광|호텔' THEN 'business'
           WHEN d.department_nm ~ '법학|행정|정치|외교|공공' THEN 'law_admin'
           WHEN d.department_nm ~ '교육|사범|유아|특수교육' THEN 'education'
           WHEN d.department_nm ~ '국어|영어|일어|중국어|불어|독어|철학|사학|문학|어문|문헌정보' THEN 'humanities'
           WHEN d.department_nm ~ '디자인|미술|음악|영화|연극|애니메이션|만화|패션|실내|공예' THEN 'arts'
           WHEN d.department_nm ~ '수학|물리|화학|생물|생명|식품|통계|지구|해양|천문' THEN 'science'
           ELSE 'general'
       END AS category
FROM tb_department d;

CREATE INDEX idx_tmp_dept_cat_46 ON tmp_dept_category_46(department_cd);

-- 2020~2021 대상 학생
CREATE TEMP TABLE tmp_grad_students AS
SELECT s.student_id,
       s.student_nm,
       s.department_cd,
       s.admission_year,
       s.current_grade,
       dc.category,
       abs(hashtext(s.student_id)) % 100 AS h
FROM tb_student s
JOIN tmp_dept_category_46 dc ON s.department_cd = dc.department_cd
WHERE s.admission_year IN (2020, 2021);

CREATE INDEX idx_tmp_grad_sid ON tmp_grad_students(student_id);
CREATE INDEX idx_tmp_grad_cat ON tmp_grad_students(category);

DO $$ BEGIN RAISE NOTICE 'Part 0 완료: 대상 학생 임시 테이블 생성'; END $$;


-- ============================================
-- Part 1: 성적 데이터 (tb_grade)
-- 졸업생이므로 성적 분포 상향: A+:25%, A0:30%, B+:25%, B0:12%, C+:5%, C0:3%
-- ============================================

INSERT INTO tb_grade (
    grade_id, enrollment_id, student_id, course_cd, term_cd,
    grade_letter, grade_point, credits_earned, is_retake,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    e.enrollment_id,
    e.student_id,
    co.course_cd,
    co.term_cd,
    CASE
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 25 THEN 'A+'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 55 THEN 'A0'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 80 THEN 'B+'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 92 THEN 'B0'
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 97 THEN 'C+'
        ELSE 'C0'
    END,
    CASE
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 25 THEN 4.50
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 55 THEN 4.00
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 80 THEN 3.50
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 92 THEN 3.00
        WHEN abs(hashtext(e.enrollment_id::text)) % 100 < 97 THEN 2.50
        ELSE 2.00
    END,
    c.credits,
    'N',
    'SEED_46',
    NOW()
FROM tb_enrollment e
JOIN tb_course_offering co ON e.course_offering_id = co.offering_id
JOIN tb_course c ON co.course_cd = c.course_cd
JOIN tmp_grad_students ts ON e.student_id = ts.student_id
WHERE NOT EXISTS (
    SELECT 1 FROM tb_grade g WHERE g.enrollment_id = e.enrollment_id
);

DO $$ BEGIN RAISE NOTICE 'Part 1 완료: 성적 데이터 생성'; END $$;


-- ============================================
-- Part 2: 학기별 성적 요약 (tb_grade_summary)
-- tb_grade 기반 집계
-- ============================================

DELETE FROM tb_grade_summary gs
USING tmp_grad_students ts
WHERE gs.student_id = ts.student_id;

INSERT INTO tb_grade_summary (
    summary_id, student_id, term_cd,
    total_credits, earned_credits, gpa, major_gpa,
    class_rank, total_students,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    g.student_id,
    g.term_cd,
    SUM(g.credits_earned)::int,
    SUM(g.credits_earned)::int,
    ROUND(SUM(g.grade_point * g.credits_earned) / NULLIF(SUM(g.credits_earned), 0), 2),
    LEAST(4.50, ROUND(SUM(g.grade_point * g.credits_earned) / NULLIF(SUM(g.credits_earned), 0)
        + (abs(hashtext(g.student_id || g.term_cd)) % 30)::numeric / 100, 2)),
    GREATEST(1, abs(hashtext(g.student_id || g.term_cd)) % 40 + 1),
    40,
    'SEED_46',
    NOW()
FROM tb_grade g
JOIN tmp_grad_students ts ON g.student_id = ts.student_id
GROUP BY g.student_id, g.term_cd;

DO $$ BEGIN RAISE NOTICE 'Part 2 완료: 학기별 성적 요약 생성'; END $$;


-- ============================================
-- Part 3: 누적 요약 (tb_cumulative_summary)
-- 카테고리별 졸업 학점, 졸업생이므로 completion_rate 높음
-- ============================================

DELETE FROM tb_cumulative_summary cs
USING tmp_grad_students ts
WHERE cs.student_id = ts.student_id;

-- 성적 데이터 기반 집계
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
    -- total_credits_required (카테고리별)
    CASE ts.category
        WHEN 'medical' THEN 150
        WHEN 'pharmacy' THEN 150
        WHEN 'nursing' THEN 140
        WHEN 'engineering' THEN 130
        ELSE 130
    END,
    -- total_credits_earned: 졸업생이므로 required의 85~100%
    GREATEST(
        agg.total_earned,
        CASE ts.category
            WHEN 'medical' THEN 150
            WHEN 'pharmacy' THEN 150
            WHEN 'nursing' THEN 140
            WHEN 'engineering' THEN 130
            ELSE 130
        END * (85 + abs(hashtext(ts.student_id || 'cum')) % 16)::numeric / 100
    )::int,
    -- major_credits_required
    CASE ts.category
        WHEN 'medical' THEN 90
        WHEN 'pharmacy' THEN 85
        WHEN 'nursing' THEN 80
        WHEN 'engineering' THEN 70
        ELSE 60
    END,
    -- major_credits_earned
    GREATEST(
        (agg.total_earned * 0.55)::int,
        CASE ts.category
            WHEN 'medical' THEN 90
            WHEN 'pharmacy' THEN 85
            WHEN 'nursing' THEN 80
            WHEN 'engineering' THEN 70
            ELSE 60
        END * (85 + abs(hashtext(ts.student_id || 'maj')) % 16)::numeric / 100
    )::int,
    -- liberal_credits_required
    CASE ts.category
        WHEN 'medical' THEN 25
        WHEN 'pharmacy' THEN 25
        ELSE 30
    END,
    -- liberal_credits_earned
    GREATEST(
        (agg.total_earned * 0.25)::int,
        CASE ts.category
            WHEN 'medical' THEN 25
            WHEN 'pharmacy' THEN 25
            ELSE 30
        END * (90 + abs(hashtext(ts.student_id || 'lib')) % 11)::numeric / 100
    )::int,
    -- cumulative_gpa
    agg.cum_gpa,
    -- major_gpa
    LEAST(4.50, agg.cum_gpa + (abs(hashtext(ts.student_id || 'mgpa')) % 30)::numeric / 100),
    -- completion_rate: 졸업생이므로 85~100%
    (85 + abs(hashtext(ts.student_id || 'comp')) % 16)::numeric,
    'SEED_46',
    NOW()
FROM (
    SELECT g.student_id,
           SUM(g.credits_earned) AS total_earned,
           ROUND(SUM(g.grade_point * g.credits_earned) / NULLIF(SUM(g.credits_earned), 0), 2) AS cum_gpa
    FROM tb_grade g
    JOIN tmp_grad_students ts2 ON g.student_id = ts2.student_id
    GROUP BY g.student_id
) agg
JOIN tmp_grad_students ts ON agg.student_id = ts.student_id;

-- enrollment이 없는 학생에 대한 기본 누적 요약 생성
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
    CASE ts.category
        WHEN 'medical' THEN 150 WHEN 'pharmacy' THEN 150
        WHEN 'nursing' THEN 140 WHEN 'engineering' THEN 130
        ELSE 130
    END,
    CASE ts.category
        WHEN 'medical' THEN 140 WHEN 'pharmacy' THEN 140
        WHEN 'nursing' THEN 130 WHEN 'engineering' THEN 120
        ELSE 120
    END + (abs(hashtext(ts.student_id || 'te')) % 15),
    CASE ts.category
        WHEN 'medical' THEN 90 WHEN 'pharmacy' THEN 85
        WHEN 'nursing' THEN 80 WHEN 'engineering' THEN 70
        ELSE 60
    END,
    CASE ts.category
        WHEN 'medical' THEN 85 WHEN 'pharmacy' THEN 80
        WHEN 'nursing' THEN 75 WHEN 'engineering' THEN 65
        ELSE 55
    END + (abs(hashtext(ts.student_id || 'me')) % 10),
    CASE ts.category WHEN 'medical' THEN 25 WHEN 'pharmacy' THEN 25 ELSE 30 END,
    CASE ts.category WHEN 'medical' THEN 24 WHEN 'pharmacy' THEN 24 ELSE 28 END + (abs(hashtext(ts.student_id || 'le')) % 5),
    LEAST(4.50, 3.20 + (abs(hashtext(ts.student_id || 'gpa')) % 130)::numeric / 100),
    LEAST(4.50, 3.30 + (abs(hashtext(ts.student_id || 'mgp')) % 120)::numeric / 100),
    (85 + abs(hashtext(ts.student_id || 'cr')) % 16)::numeric,
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_cumulative_summary cs WHERE cs.student_id = ts.student_id
);

DO $$ BEGIN RAISE NOTICE 'Part 3 완료: 누적 요약 생성'; END $$;


-- ============================================
-- Part 4: 역량 점수 (tb_student_competency)
-- 6개 역량(COMP001~COMP006) × 학생
-- 졸업생 current_score: 65~95
-- ============================================

INSERT INTO tb_student_competency (
    student_competency_id, student_id, competency_cd,
    current_score, target_score, gap_score,
    status, last_assessment_date, trend,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    comp.competency_cd,
    -- current_score: 졸업생 65~95
    (65 + abs(hashtext(ts.student_id || comp.competency_cd)) % 31)::numeric,
    -- target_score: 85~95
    (85 + abs(hashtext(ts.student_id || comp.competency_cd || 't')) % 11)::numeric,
    -- gap_score = current - target
    (65 + abs(hashtext(ts.student_id || comp.competency_cd)) % 31)::numeric
    - (85 + abs(hashtext(ts.student_id || comp.competency_cd || 't')) % 11)::numeric,
    -- status
    CASE
        WHEN (65 + abs(hashtext(ts.student_id || comp.competency_cd)) % 31) >= 85 THEN 'excellent'
        WHEN (65 + abs(hashtext(ts.student_id || comp.competency_cd)) % 31) >= 75 THEN 'good'
        WHEN (65 + abs(hashtext(ts.student_id || comp.competency_cd)) % 31) >= 70 THEN 'average'
        ELSE 'improve'
    END,
    -- last_assessment_date: 졸업 무렵 (2023~2024년)
    ('2023-06-01'::date + (abs(hashtext(ts.student_id || comp.competency_cd || 'd')) % 400)::int),
    -- trend: 졸업생은 대부분 up 또는 stable
    CASE WHEN abs(hashtext(ts.student_id || comp.competency_cd || 'tr')) % 3 < 2 THEN 'up' ELSE 'stable' END,
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
CROSS JOIN (
    SELECT competency_cd FROM tb_competency
) comp
WHERE NOT EXISTS (
    SELECT 1 FROM tb_student_competency sc
    WHERE sc.student_id = ts.student_id AND sc.competency_cd = comp.competency_cd
);

DO $$ BEGIN RAISE NOTICE 'Part 4 완료: 역량 점수 생성'; END $$;


-- ============================================
-- Part 5: 스킬 (tb_student_skill)
-- 학과 카테고리별 7개 스킬 매핑, 기존 데이터 없는 학생만
-- 졸업생 current_level: 3~5
-- ============================================

-- 카테고리-스킬 매핑 (기존 스크립트 43에서 사용한 스킬 코드)
CREATE TEMP TABLE tmp_category_skills_46 (
    category VARCHAR(20),
    skill_cd VARCHAR(20),
    skill_order INT
);

INSERT INTO tmp_category_skills_46 (category, skill_cd, skill_order) VALUES
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

INSERT INTO tb_student_skill (
    student_skill_id, student_id, skill_cd,
    current_level, target_level, evidence_count,
    last_verified_date, verification_source, trend,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    cs.skill_cd,
    -- current_level: 졸업생 3~5
    LEAST(5, 3 + abs(hashtext(ts.student_id || cs.skill_cd)) % 3),
    -- target_level: 4~5
    LEAST(5, 4 + abs(hashtext(ts.student_id || cs.skill_cd || 't')) % 2),
    -- evidence_count: 졸업생이므로 2~6개
    2 + abs(hashtext(ts.student_id || cs.skill_cd || 'e')) % 5,
    -- last_verified_date
    ('2023-03-01'::date + (abs(hashtext(ts.student_id || cs.skill_cd || 'd')) % 500)::int),
    -- verification_source
    CASE abs(hashtext(ts.student_id || cs.skill_cd || 'v')) % 4
        WHEN 0 THEN 'course'
        WHEN 1 THEN 'certificate'
        WHEN 2 THEN 'project'
        ELSE 'self_assessment'
    END,
    -- trend: 졸업생 대부분 stable 또는 up
    CASE WHEN abs(hashtext(ts.student_id || cs.skill_cd || 'r')) % 3 = 0 THEN 'up' ELSE 'stable' END,
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
JOIN tmp_category_skills_46 cs ON ts.category = cs.category
WHERE NOT EXISTS (
    SELECT 1 FROM tb_student_skill ss
    WHERE ss.student_id = ts.student_id AND ss.skill_cd = cs.skill_cd
);

DO $$ BEGIN RAISE NOTICE 'Part 5 완료: 스킬 데이터 생성'; END $$;


-- ============================================
-- Part 6: 로드맵 (tb_roadmap)
-- 졸업생이므로 status: completed(80%) 또는 active(20%)
-- progress_percent: 80~100%
-- ============================================

INSERT INTO tb_roadmap (
    roadmap_id, student_id, title, description,
    target_role, target_company, target_year,
    status, progress_percent,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    -- title (카테고리별)
    CASE ts.category
        WHEN 'medical' THEN '의료 전문가 커리어 로드맵'
        WHEN 'nursing' THEN '간호 전문가 커리어 로드맵'
        WHEN 'pharmacy' THEN '약학 전문가 커리어 로드맵'
        WHEN 'health' THEN '보건의료 전문가 커리어 로드맵'
        WHEN 'engineering' THEN 'IT/공학 전문가 커리어 로드맵'
        WHEN 'business' THEN '경영/비즈니스 커리어 로드맵'
        WHEN 'law_admin' THEN '법학/행정 전문가 커리어 로드맵'
        WHEN 'education' THEN '교육 전문가 커리어 로드맵'
        WHEN 'humanities' THEN '인문학 기반 커리어 로드맵'
        WHEN 'arts' THEN '예술/디자인 커리어 로드맵'
        WHEN 'science' THEN '자연과학 연구자 커리어 로드맵'
        ELSE '통합 역량 커리어 로드맵'
    END,
    -- description
    CASE ts.category
        WHEN 'medical' THEN '의료 분야 진출을 위한 체계적 역량 개발 계획'
        WHEN 'nursing' THEN '간호 전문성 강화를 위한 단계별 성장 계획'
        WHEN 'pharmacy' THEN '약학 전문가로 성장하기 위한 로드맵'
        WHEN 'health' THEN '보건의료 분야 전문가 양성 로드맵'
        WHEN 'engineering' THEN 'IT/공학 분야 취업을 위한 기술 역량 로드맵'
        WHEN 'business' THEN '경영/비즈니스 분야 커리어 개발 로드맵'
        WHEN 'law_admin' THEN '법률/행정 분야 전문가 커리어 로드맵'
        WHEN 'education' THEN '교육 분야 전문가 성장 로드맵'
        WHEN 'humanities' THEN '인문학 기반 다양한 진로 탐색 로드맵'
        WHEN 'arts' THEN '예술/디자인 분야 창작자 성장 로드맵'
        WHEN 'science' THEN '자연과학 연구자/전문가 성장 로드맵'
        ELSE '융합 역량 기반 커리어 개발 로드맵'
    END,
    -- target_role
    CASE ts.category
        WHEN 'medical' THEN '전공의/레지던트'
        WHEN 'nursing' THEN '전문간호사'
        WHEN 'pharmacy' THEN '임상약사'
        WHEN 'health' THEN '보건의료 전문가'
        WHEN 'engineering' THEN '소프트웨어 엔지니어'
        WHEN 'business' THEN '경영 컨설턴트'
        WHEN 'law_admin' THEN '법률/행정 전문가'
        WHEN 'education' THEN '교사/교육전문가'
        WHEN 'humanities' THEN '콘텐츠 기획자'
        WHEN 'arts' THEN '디자이너/아티스트'
        WHEN 'science' THEN '연구원'
        ELSE '기획/관리자'
    END,
    -- target_company
    CASE ts.category
        WHEN 'medical' THEN CASE ts.h % 3 WHEN 0 THEN '서울대병원' WHEN 1 THEN '연세세브란스' ELSE '삼성서울병원' END
        WHEN 'nursing' THEN CASE ts.h % 3 WHEN 0 THEN '서울아산병원' WHEN 1 THEN '국립중앙의료원' ELSE '서울대병원' END
        WHEN 'pharmacy' THEN CASE ts.h % 3 WHEN 0 THEN '삼성바이오로직스' WHEN 1 THEN '셀트리온' ELSE '녹십자' END
        WHEN 'health' THEN CASE ts.h % 3 WHEN 0 THEN '건강보험심사평가원' WHEN 1 THEN '질병관리청' ELSE '국민건강보험공단' END
        WHEN 'engineering' THEN CASE ts.h % 4 WHEN 0 THEN '삼성전자' WHEN 1 THEN 'LG전자' WHEN 2 THEN '네이버' ELSE '카카오' END
        WHEN 'business' THEN CASE ts.h % 3 WHEN 0 THEN '맥킨지' WHEN 1 THEN 'BCG' ELSE '삼성물산' END
        WHEN 'law_admin' THEN CASE ts.h % 3 WHEN 0 THEN '김앤장' WHEN 1 THEN '행정안전부' ELSE '법무부' END
        WHEN 'education' THEN CASE ts.h % 3 WHEN 0 THEN '공립학교' WHEN 1 THEN '사립학교' ELSE '교육청' END
        WHEN 'humanities' THEN CASE ts.h % 3 WHEN 0 THEN 'CJ ENM' WHEN 1 THEN 'HYBE' ELSE '출판사' END
        WHEN 'arts' THEN CASE ts.h % 3 WHEN 0 THEN '삼성디자인' WHEN 1 THEN 'NHN' ELSE '넥슨' END
        WHEN 'science' THEN CASE ts.h % 3 WHEN 0 THEN 'KAIST' WHEN 1 THEN 'KIST' ELSE 'ETRI' END
        ELSE CASE ts.h % 3 WHEN 0 THEN '공기업' WHEN 1 THEN '대기업' ELSE '스타트업' END
    END,
    -- target_year
    ts.admission_year + 4 + (ts.h % 2),
    -- status: 졸업생 80% completed, 20% active
    CASE WHEN ts.h < 80 THEN 'completed' ELSE 'active' END,
    -- progress_percent: 80~100%
    80 + abs(hashtext(ts.student_id || 'road')) % 21,
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_roadmap r WHERE r.student_id = ts.student_id
);

DO $$ BEGIN RAISE NOTICE 'Part 6 완료: 로드맵 생성'; END $$;


-- ============================================
-- Part 7: 포트폴리오 (tb_portfolio)
-- 학생당 4개 (certification, project, experience, award)
-- 졸업생이므로 날짜 범위 2020~2024
-- ============================================

-- 카테고리별 포트폴리오 템플릿
CREATE TEMP TABLE tmp_portfolio_data_46 (
    category VARCHAR(20),
    item_type VARCHAR(50),
    artifact_type VARCHAR(50),
    title_suffix VARCHAR(200),
    description TEXT,
    skills_json TEXT,
    display_order INT
);

INSERT INTO tmp_portfolio_data_46 VALUES
    -- medical
    ('medical','certificate','certification','의료정보관리사 자격증','의료정보 관리 및 분석 역량 인증','["의료정보학","데이터분석","의학용어"]',1),
    ('medical','project','project','임상 사례 연구 프로젝트','실제 임상 사례를 기반으로 한 의학 연구 프로젝트','["임상연구","의학통계","논문작성"]',2),
    ('medical','activity','experience','병원 임상실습','대학병원 임상실습 경험','["환자소통","의료윤리","임상술기"]',3),
    ('medical','award','award','학술 연구 발표 수상','교내 의학 학술대회 우수 발표상','["학술발표","연구방법론","프레젠테이션"]',4),
    -- nursing
    ('nursing','certificate','certification','BLS/ACLS 자격증','기본소생술/전문심장소생술 자격 인증','["응급처치","심폐소생술","환자평가"]',1),
    ('nursing','project','project','간호 질 향상 프로젝트','간호 서비스 질 향상을 위한 개선 프로젝트','["간호과정","질향상","데이터분석"]',2),
    ('nursing','activity','experience','종합병원 임상실습','종합병원 각 병동 순환 실습','["환자간호","투약관리","간호기록"]',3),
    ('nursing','award','award','간호 술기 대회 수상','교내 간호 술기 경진대회 수상','["간호술기","응급처치","팀워크"]',4),
    -- pharmacy
    ('pharmacy','certificate','certification','약사 면허','약사 국가시험 합격','["약학","약물치료","조제"]',1),
    ('pharmacy','project','project','신약 개발 연구 참여','제약 연구실 신약 개발 프로젝트 참여','["약물학","생화학","실험설계"]',2),
    ('pharmacy','activity','experience','약국 실무 실습','지역 약국 및 병원 약국 실무 실습','["조제실무","복약지도","약물상호작용"]',3),
    ('pharmacy','award','award','약학 학술상','약학대학 학술 우수 연구상','["약학연구","논문작성","발표"]',4),
    -- health
    ('health','certificate','certification','보건의료정보관리사','보건의료정보 관리 자격 인증','["보건정보","의료통계","데이터관리"]',1),
    ('health','project','project','건강증진 프로그램 기획','지역사회 건강증진 프로그램 기획 및 운영','["건강증진","프로그램기획","지역사회보건"]',2),
    ('health','activity','experience','보건소 현장실습','지역 보건소 현장 실습 경험','["보건행정","건강검진","보건교육"]',3),
    ('health','award','award','보건 분야 공모전 수상','보건의료 혁신 아이디어 공모전 수상','["창의력","문제해결","보건정책"]',4),
    -- engineering
    ('engineering','certificate','certification','정보처리기사 자격증','국가공인 정보처리기사 자격 취득','["소프트웨어개발","데이터베이스","시스템분석"]',1),
    ('engineering','project','project','캡스톤 디자인 프로젝트','졸업 캡스톤 디자인 프로젝트','["프로그래밍","시스템설계","팀프로젝트"]',2),
    ('engineering','activity','experience','IT 기업 인턴십','IT 기업 소프트웨어 개발 인턴십','["실무개발","애자일","코드리뷰"]',3),
    ('engineering','award','award','프로그래밍 대회 수상','ACM-ICPC 또는 교내 프로그래밍 대회 수상','["알고리즘","문제해결","프로그래밍"]',4),
    -- business
    ('business','certificate','certification','SQLD/빅데이터분석기사','데이터 분석 관련 자격증 취득','["SQL","데이터분석","통계"]',1),
    ('business','project','project','창업 프로젝트','비즈니스 모델 수립 및 창업 프로젝트','["사업계획","마케팅","재무분석"]',2),
    ('business','activity','experience','기업 마케팅 인턴십','대기업 마케팅팀 인턴십 경험','["마케팅전략","시장조사","데이터분석"]',3),
    ('business','award','award','비즈니스 공모전 수상','전국 대학생 비즈니스 플랜 공모전 수상','["사업기획","프레젠테이션","팀워크"]',4),
    -- law_admin
    ('law_admin','certificate','certification','행정사/법무사 자격','행정 또는 법률 관련 자격 취득','["행정법","민법","법률문서"]',1),
    ('law_admin','project','project','법률 사례 연구','주요 판례 분석 및 법률 사례 연구','["판례분석","법률해석","논증"]',2),
    ('law_admin','activity','experience','법률사무소 실습','법률사무소 또는 공공기관 인턴십','["법률실무","문서작성","고객상담"]',3),
    ('law_admin','award','award','모의재판 대회 수상','교내/전국 모의재판 대회 수상','["변론","법률지식","논리력"]',4),
    -- education
    ('education','certificate','certification','교원자격증','정교사 2급 자격증 취득','["교수법","교육과정","학생평가"]',1),
    ('education','project','project','교육 프로그램 개발','혁신 교육 프로그램 개발 프로젝트','["교육설계","교재개발","수업설계"]',2),
    ('education','activity','experience','교육실습','초중고 교육실습 경험','["수업운영","학생지도","학급경영"]',3),
    ('education','award','award','교육 봉사 우수상','교육 봉사활동 우수 수상','["교육봉사","멘토링","커뮤니케이션"]',4),
    -- humanities
    ('humanities','certificate','certification','한국어교원자격증','한국어 교육 자격 인증','["한국어교육","언어학","교수법"]',1),
    ('humanities','project','project','인문학 연구 프로젝트','인문학 분야 학술 연구 프로젝트','["문헌연구","비평","학술작성"]',2),
    ('humanities','activity','experience','출판사/미디어 인턴십','출판사 또는 미디어 기업 인턴십','["편집","콘텐츠기획","글쓰기"]',3),
    ('humanities','award','award','인문학 에세이 공모전 수상','전국 대학생 인문학 에세이 공모전 수상','["글쓰기","비판적사고","창의력"]',4),
    -- arts
    ('arts','certificate','certification','GTQ/컬러리스트 자격증','그래픽/디자인 관련 자격 인증','["그래픽디자인","색채학","시각디자인"]',1),
    ('arts','project','project','졸업 작품 프로젝트','졸업 전시/공연 작품 프로젝트','["창작","기획","예술표현"]',2),
    ('arts','activity','experience','디자인 스튜디오 인턴십','디자인 스튜디오/에이전시 인턴십','["실무디자인","클라이언트소통","포트폴리오"]',3),
    ('arts','award','award','디자인/예술 공모전 수상','전국 대학생 디자인/예술 공모전 수상','["창의력","예술성","표현력"]',4),
    -- science
    ('science','certificate','certification','실험동물기술원/분석화학 자격','과학 연구 관련 자격 인증','["실험기법","분석화학","연구윤리"]',1),
    ('science','project','project','연구실 프로젝트','교수 연구실 연구 프로젝트 참여','["실험설계","데이터분석","논문작성"]',2),
    ('science','activity','experience','연구소 인턴십','국공립 연구소 인턴십 경험','["연구실무","장비운영","데이터수집"]',3),
    ('science','award','award','학술 논문 발표상','학술대회 우수 논문 발표 수상','["연구발표","학술작성","분석력"]',4),
    -- general
    ('general','certificate','certification','컴퓨터활용능력 1급','컴퓨터 활용 능력 국가 자격 취득','["엑셀","데이터관리","문서작성"]',1),
    ('general','project','project','융합 프로젝트','학제간 융합 프로젝트','["팀워크","문제해결","기획력"]',2),
    ('general','activity','experience','기업 인턴십','기업 인턴십 경험','["실무경험","커뮤니케이션","업무관리"]',3),
    ('general','award','award','교내 공모전 수상','교내 아이디어 공모전 수상','["창의력","발표","기획"]',4);

DELETE FROM tb_portfolio p
USING tmp_grad_students ts
WHERE p.student_id = ts.student_id
  AND p.ins_user_id = 'SEED_46';

INSERT INTO tb_portfolio (
    portfolio_id, student_id, item_type, title, description,
    start_date, end_date, skills_used,
    evidence_url, image_url, is_featured, display_order,
    ins_user_id, ins_dt,
    artifact_type, url, is_primary
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    pd.item_type,
    ts.student_nm || ' - ' || pd.title_suffix,
    pd.description,
    -- start_date: 입학년도+1 ~ 입학년도+3
    ((ts.admission_year + 1)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || pd.item_type || 's')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || pd.item_type || 'sd')) % 28 + 1)::text, 2, '0'))::date,
    -- end_date: 입학년도+2 ~ 입학년도+4
    ((ts.admission_year + 2 + abs(hashtext(ts.student_id || pd.item_type || 'ey')) % 2)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || pd.item_type || 'em')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || pd.item_type || 'ed')) % 28 + 1)::text, 2, '0'))::date,
    pd.skills_json::jsonb,
    'https://portfolio.inje.ac.kr/' || ts.student_id || '/' || pd.item_type,
    NULL,
    CASE WHEN pd.display_order = 1 THEN 'Y' ELSE 'N' END,
    pd.display_order,
    'SEED_46',
    NOW(),
    pd.artifact_type,
    'https://portfolio.inje.ac.kr/' || ts.student_id || '/' || pd.artifact_type,
    CASE WHEN pd.display_order = 1 THEN true ELSE false END
FROM tmp_grad_students ts
JOIN tmp_portfolio_data_46 pd ON ts.category = pd.category;

DO $$ BEGIN RAISE NOTICE 'Part 7 완료: 포트폴리오 생성'; END $$;


-- ============================================
-- Part 8: 코칭 목표 + 코칭 계획 (tb_coaching_goal + tb_coaching_plan)
-- 3개 목표 (academic, skill, career)
-- 졸업생이므로 status: completed 위주, progress: 80~100%
-- ============================================

-- 기존 코칭 데이터 없는 학생 식별
CREATE TEMP TABLE tmp_grad_no_coaching AS
SELECT ts.student_id, ts.category, ts.admission_year, ts.h
FROM tmp_grad_students ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_coaching_goal cg WHERE cg.std_id = ts.student_id
);

-- 목표 1: Academic
INSERT INTO tb_coaching_goal (
    goal_id, std_id, title, description, goal_type, priority,
    target_date, related_skills, success_criteria, motivation,
    status, progress_percentage, created_at, completed_at,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    CASE ts.category
        WHEN 'medical' THEN '의학 전공 학업 우수 달성'
        WHEN 'nursing' THEN '간호학 전공 심화 학습'
        WHEN 'pharmacy' THEN '약학 전공 학업 목표 달성'
        WHEN 'engineering' THEN '공학 전공 GPA 목표 달성'
        ELSE '전공 학업 우수 달성'
    END,
    '졸업 시까지 전공 GPA 3.5 이상 유지 및 핵심 과목 우수 성적 확보',
    'academic',
    'high',
    ((ts.admission_year + 4)::text || '-02-28')::date,
    ARRAY['전공지식', '학습능력', '자기주도학습'],
    '전공 GPA 3.5 이상 달성',
    '전문 분야 역량 강화를 위한 학업 기반 확립',
    CASE WHEN ts.h < 85 THEN 'completed' ELSE 'active' END,
    80 + abs(hashtext(ts.student_id || 'acad')) % 21,
    (ts.admission_year::text || '-03-15')::timestamp,
    CASE WHEN ts.h < 85 THEN ((ts.admission_year + 4)::text || '-02-20')::timestamp ELSE NULL END,
    'SEED_46',
    NOW()
FROM tmp_grad_no_coaching ts;

-- 목표 2: Skill
INSERT INTO tb_coaching_goal (
    goal_id, std_id, title, description, goal_type, priority,
    target_date, related_skills, success_criteria, motivation,
    status, progress_percentage, created_at, completed_at,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    CASE ts.category
        WHEN 'medical' THEN '임상 역량 강화'
        WHEN 'nursing' THEN '간호 실무 역량 향상'
        WHEN 'pharmacy' THEN '약물치료 전문성 개발'
        WHEN 'engineering' THEN '개발 실무 역량 강화'
        WHEN 'business' THEN '비즈니스 분석 역량 향상'
        ELSE '전문 역량 개발'
    END,
    '졸업 전 핵심 실무 역량 확보 및 자격증 취득',
    'skill',
    'medium',
    ((ts.admission_year + 3)::text || '-12-31')::date,
    ARRAY['실무능력', '자격증', '프로젝트경험'],
    '관련 자격증 1개 이상 취득 및 실무 프로젝트 완수',
    '취업 경쟁력 확보를 위한 실질적 역량 개발',
    CASE WHEN ts.h < 80 THEN 'completed' ELSE 'active' END,
    75 + abs(hashtext(ts.student_id || 'skill')) % 26,
    (ts.admission_year::text || '-09-01')::timestamp,
    CASE WHEN ts.h < 80 THEN ((ts.admission_year + 3)::text || '-12-15')::timestamp ELSE NULL END,
    'SEED_46',
    NOW()
FROM tmp_grad_no_coaching ts;

-- 목표 3: Career
INSERT INTO tb_coaching_goal (
    goal_id, std_id, title, description, goal_type, priority,
    target_date, related_skills, success_criteria, motivation,
    status, progress_percentage, created_at, completed_at,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    CASE ts.category
        WHEN 'medical' THEN '전공의 매칭 준비'
        WHEN 'nursing' THEN '종합병원 취업 준비'
        WHEN 'pharmacy' THEN '약사 면허 및 취업 준비'
        WHEN 'engineering' THEN 'IT 기업 취업 준비'
        WHEN 'business' THEN '기업 취업/창업 준비'
        ELSE '진로 설계 및 취업 준비'
    END,
    '졸업 후 진로 목표 달성을 위한 체계적 준비',
    'career',
    'high',
    ((ts.admission_year + 4)::text || '-06-30')::date,
    ARRAY['이력서작성', '면접준비', '직무분석'],
    '목표 기업/기관 취업 또는 진학 확정',
    '안정적인 사회 진출을 위한 준비',
    CASE WHEN ts.h < 70 THEN 'completed' ELSE 'active' END,
    70 + abs(hashtext(ts.student_id || 'career')) % 31,
    ((ts.admission_year + 1)::text || '-03-01')::timestamp,
    CASE WHEN ts.h < 70 THEN ((ts.admission_year + 4)::text || '-06-15')::timestamp ELSE NULL END,
    'SEED_46',
    NOW()
FROM tmp_grad_no_coaching ts;

-- 각 목표에 대한 coaching_plan 생성 (목표당 2개)
INSERT INTO tb_coaching_plan (
    plan_id, goal_id, title, description, order_index,
    due_date, estimated_hours, is_completed, completed_at,
    actual_hours, notes, created_at,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    cg.goal_id,
    CASE cg.goal_type
        WHEN 'academic' THEN
            CASE rn WHEN 1 THEN '핵심 전공과목 수강 계획 수립' ELSE '학습 그룹 참여 및 성적 모니터링' END
        WHEN 'skill' THEN
            CASE rn WHEN 1 THEN '관련 자격증 시험 준비' ELSE '실무 프로젝트 참여' END
        WHEN 'career' THEN
            CASE rn WHEN 1 THEN '이력서/자기소개서 작성 및 피드백' ELSE '모의면접 참여 및 기업 분석' END
        ELSE
            CASE rn WHEN 1 THEN '단계별 실행 계획 수립' ELSE '주기적 점검 및 피드백' END
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN
            CASE rn WHEN 1 THEN '학기별 핵심 과목을 선정하고 체계적으로 수강' ELSE '스터디 그룹 참여를 통한 학업 향상' END
        WHEN 'skill' THEN
            CASE rn WHEN 1 THEN '목표 자격증 시험 일정 확인 및 준비 계획' ELSE '실무 프로젝트 또는 인턴십 참여' END
        WHEN 'career' THEN
            CASE rn WHEN 1 THEN '경력 목표에 맞는 이력서 및 자기소개서 작성' ELSE '모의면접 및 취업 박람회 참여' END
        ELSE
            CASE rn WHEN 1 THEN '목표 세분화 및 구체적 실행 계획' ELSE '월별 진행 상황 점검' END
    END,
    rn - 1,
    cg.target_date - (30 * (3 - rn)),
    CASE rn WHEN 1 THEN 20.0 ELSE 15.0 END,
    CASE WHEN cg.status = 'completed' THEN true ELSE (rn = 1) END,
    CASE WHEN cg.status = 'completed' THEN cg.completed_at
         WHEN rn = 1 THEN cg.created_at + interval '90 days'
         ELSE NULL END,
    CASE WHEN cg.status = 'completed' OR rn = 1 THEN
        CASE rn WHEN 1 THEN 18.0 ELSE 14.0 END
    ELSE NULL END,
    NULL,
    cg.created_at,
    'SEED_46',
    NOW()
FROM tb_coaching_goal cg
JOIN tmp_grad_no_coaching ts ON cg.std_id = ts.student_id
CROSS JOIN generate_series(1, 2) AS rn
WHERE cg.ins_user_id = 'SEED_46';

DROP TABLE IF EXISTS tmp_grad_no_coaching;

DO $$ BEGIN RAISE NOTICE 'Part 8 완료: 코칭 목표 및 계획 생성'; END $$;


-- ============================================
-- Part 9: 성취 (tb_achievement)
-- 기존 데이터 없는 학생만
-- 졸업생이므로 1~3개 성취
-- ============================================

-- 성취 1: 자격증 (전체 학생)
INSERT INTO tb_achievement (
    achievement_id, student_id, achievement_type,
    title, issuer, issue_date, level, score,
    verified, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    'certificate',
    CASE ts.category
        WHEN 'medical' THEN '의사 국가시험 합격'
        WHEN 'nursing' THEN '간호사 면허'
        WHEN 'pharmacy' THEN '약사 면허'
        WHEN 'health' THEN '보건의료정보관리사'
        WHEN 'engineering' THEN '정보처리기사'
        WHEN 'business' THEN 'SQLD'
        WHEN 'law_admin' THEN '행정사'
        WHEN 'education' THEN '정교사 2급'
        WHEN 'humanities' THEN '한국어교원자격증'
        WHEN 'arts' THEN 'GTQ 1급'
        WHEN 'science' THEN '품질경영기사'
        ELSE '컴퓨터활용능력 1급'
    END,
    CASE ts.category
        WHEN 'medical' THEN '보건복지부'
        WHEN 'nursing' THEN '보건복지부'
        WHEN 'pharmacy' THEN '보건복지부'
        WHEN 'health' THEN '보건의료정보관리사협회'
        WHEN 'engineering' THEN '한국산업인력공단'
        WHEN 'business' THEN '한국데이터산업진흥원'
        WHEN 'law_admin' THEN '법무부'
        WHEN 'education' THEN '교육부'
        WHEN 'humanities' THEN '국립국어원'
        WHEN 'arts' THEN '한국생산성본부'
        WHEN 'science' THEN '한국산업인력공단'
        ELSE '대한상공회의소'
    END,
    ((ts.admission_year + 3)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'cert')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'certd')) % 28 + 1)::text, 2, '0'))::date,
    CASE WHEN ts.h % 3 = 0 THEN '상급' WHEN ts.h % 3 = 1 THEN '중급' ELSE '1급' END,
    NULL,
    'Y',
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_achievement a WHERE a.student_id = ts.student_id
);

-- 성취 2: 어학 (h < 70, 약 70%)
INSERT INTO tb_achievement (
    achievement_id, student_id, achievement_type,
    title, issuer, issue_date, level, score,
    verified, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    'language',
    CASE abs(hashtext(ts.student_id || 'lang')) % 3
        WHEN 0 THEN 'TOEIC'
        WHEN 1 THEN 'TOEFL iBT'
        ELSE 'IELTS'
    END,
    CASE abs(hashtext(ts.student_id || 'lang')) % 3
        WHEN 0 THEN 'ETS'
        WHEN 1 THEN 'ETS'
        ELSE 'British Council'
    END,
    ((ts.admission_year + 2)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'langm')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'langd')) % 28 + 1)::text, 2, '0'))::date,
    CASE WHEN ts.h % 4 = 0 THEN '상급' ELSE '중상급' END,
    CASE abs(hashtext(ts.student_id || 'lang')) % 3
        WHEN 0 THEN (750 + abs(hashtext(ts.student_id || 'lscore')) % 200)::text
        WHEN 1 THEN (85 + abs(hashtext(ts.student_id || 'lscore')) % 30)::text
        ELSE (6.0 + (abs(hashtext(ts.student_id || 'lscore')) % 25)::numeric / 10)::text
    END,
    'Y',
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE ts.h < 70
  AND NOT EXISTS (
    SELECT 1 FROM tb_achievement a
    WHERE a.student_id = ts.student_id AND a.achievement_type = 'language'
  );

-- 성취 3: 수상 (h < 40, 약 40%)
INSERT INTO tb_achievement (
    achievement_id, student_id, achievement_type,
    title, issuer, issue_date, level, score,
    verified, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    'award',
    CASE abs(hashtext(ts.student_id || 'awd')) % 4
        WHEN 0 THEN '교내 학술 우수상'
        WHEN 1 THEN '전국 대학생 공모전 입상'
        WHEN 2 THEN '캡스톤 디자인 우수상'
        ELSE '학과 우수 졸업생상'
    END,
    CASE abs(hashtext(ts.student_id || 'awd')) % 4
        WHEN 0 THEN '인제대학교'
        WHEN 1 THEN '한국대학교육협의회'
        WHEN 2 THEN '인제대학교 공과대학'
        ELSE '인제대학교'
    END,
    ((ts.admission_year + 3)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'awdm')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'awdd')) % 28 + 1)::text, 2, '0'))::date,
    CASE WHEN ts.h % 3 = 0 THEN '대상' WHEN ts.h % 3 = 1 THEN '최우수' ELSE '우수' END,
    NULL,
    'Y',
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE ts.h < 40
  AND NOT EXISTS (
    SELECT 1 FROM tb_achievement a
    WHERE a.student_id = ts.student_id AND a.achievement_type = 'award'
  );

DO $$ BEGIN RAISE NOTICE 'Part 9 완료: 성취 데이터 생성'; END $$;


-- ============================================
-- Part 10: 리스크 알림 (tb_risk_alert)
-- 졸업생이므로 대부분 resolved, ~10%만 active (졸업 후 진로)
-- ============================================

-- resolved 리스크 (90%): 재학 중 발생했던 리스크들
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity,
    title, description, status,
    resolved_at, resolution_notes,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    -- risk_type
    CASE abs(hashtext(ts.student_id || 'rtype')) % 5
        WHEN 0 THEN 'gpa_warning'
        WHEN 1 THEN 'credit_shortage'
        WHEN 2 THEN 'prerequisite_missing'
        WHEN 3 THEN 'graduation_delay'
        ELSE 'gpa_warning'
    END,
    -- severity
    CASE abs(hashtext(ts.student_id || 'rsev')) % 3
        WHEN 0 THEN 'low'
        WHEN 1 THEN 'medium'
        ELSE 'low'
    END,
    -- title
    CASE abs(hashtext(ts.student_id || 'rtype')) % 5
        WHEN 0 THEN 'GPA 관리 알림 (해결됨)'
        WHEN 1 THEN '학점 이수 알림 (해결됨)'
        WHEN 2 THEN '선수과목 미이수 알림 (해결됨)'
        WHEN 3 THEN '졸업 요건 주의 알림 (해결됨)'
        ELSE 'GPA 경고 알림 (해결됨)'
    END,
    -- description
    CASE abs(hashtext(ts.student_id || 'rtype')) % 5
        WHEN 0 THEN '학기 GPA가 기준 이하였으나, 이후 학기에서 성적을 회복하였습니다.'
        WHEN 1 THEN '학점 이수 계획에 차질이 있었으나, 추가 수강으로 해결하였습니다.'
        WHEN 2 THEN '선수과목 미이수가 있었으나, 해당 과목을 수강 완료하였습니다.'
        WHEN 3 THEN '졸업 요건 미충족 우려가 있었으나, 필요 학점을 모두 이수하였습니다.'
        ELSE '학업 성취도 알림이 있었으나, 성적 향상으로 해결되었습니다.'
    END,
    'resolved',
    -- resolved_at
    ((ts.admission_year + 3)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'rres')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'rresd')) % 28 + 1)::text, 2, '0'))::timestamp,
    '재학 중 조치 완료됨',
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE ts.h >= 10  -- 90% resolved
  AND NOT EXISTS (
    SELECT 1 FROM tb_risk_alert ra WHERE ra.student_id = ts.student_id
  );

-- active 리스크 (~10%): 졸업 후 진로 관련
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity,
    title, description, status,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    'gpa_warning',
    'low',
    '졸업 후 진로 추적 필요',
    '졸업 후 취업/진학 현황 확인이 필요합니다. 동문 네트워크를 통한 추적 관리가 권장됩니다.',
    'active',
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE ts.h < 10  -- 10% active
  AND NOT EXISTS (
    SELECT 1 FROM tb_risk_alert ra WHERE ra.student_id = ts.student_id
  );

DO $$ BEGIN RAISE NOTICE 'Part 10 완료: 리스크 알림 생성'; END $$;


-- ============================================
-- Part 11: 학생 배지 (tb_student_badge)
-- 기존 데이터 없는 학생만, 2~3개 배지
-- ============================================

-- 배지 1: Academic Excellence (BADGE001) - 전체 학생
INSERT INTO tb_student_badge (
    student_badge_id, student_id, badge_id,
    earned_at, evidence,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    (SELECT badge_id FROM tb_badge WHERE badge_cd = 'BADGE001'),
    ((ts.admission_year + 3)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'b1m')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'b1d')) % 28 + 1)::text, 2, '0'))::timestamp,
    jsonb_build_object('description', '졸업 요건 충족 및 전문성 인정'),
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_student_badge sb WHERE sb.student_id = ts.student_id
);

-- 배지 2: Skill Master / Team Player / Career Ready (h < 80, 약 80%)
INSERT INTO tb_student_badge (
    student_badge_id, student_id, badge_id,
    earned_at, evidence,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    (SELECT badge_id FROM tb_badge WHERE badge_cd =
        CASE abs(hashtext(ts.student_id || 'b2type')) % 3
            WHEN 0 THEN 'BADGE002'
            WHEN 1 THEN 'BADGE004'
            ELSE 'BADGE010'
        END
    ),
    ((ts.admission_year + 2)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'b2m')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'b2d')) % 28 + 1)::text, 2, '0'))::timestamp,
    jsonb_build_object('description', '학업 및 활동 성과 인정'),
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE ts.h < 80
  AND NOT EXISTS (
    SELECT 1 FROM tb_student_badge sb
    WHERE sb.student_id = ts.student_id
      AND sb.badge_id IN (SELECT badge_id FROM tb_badge WHERE badge_cd IN ('BADGE002','BADGE004','BADGE010'))
  );

-- 배지 3: Innovation / Research / Community Leader (h < 50, 약 50%)
INSERT INTO tb_student_badge (
    student_badge_id, student_id, badge_id,
    earned_at, evidence,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    (SELECT badge_id FROM tb_badge WHERE badge_cd =
        CASE abs(hashtext(ts.student_id || 'b3type')) % 3
            WHEN 0 THEN 'BADGE005'
            WHEN 1 THEN 'BADGE006'
            ELSE 'BADGE008'
        END
    ),
    ((ts.admission_year + 3)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'b3m')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || 'b3d')) % 28 + 1)::text, 2, '0'))::timestamp,
    jsonb_build_object('description', '전문 스킬 역량 인증'),
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
WHERE ts.h < 50
  AND NOT EXISTS (
    SELECT 1 FROM tb_student_badge sb
    WHERE sb.student_id = ts.student_id
      AND sb.badge_id IN (SELECT badge_id FROM tb_badge WHERE badge_cd IN ('BADGE005','BADGE006','BADGE008'))
  );

DO $$ BEGIN RAISE NOTICE 'Part 11 완료: 학생 배지 생성'; END $$;


-- ============================================
-- Part 12: 지도교수 배정 (tb_advisor_assignment)
-- 기존 데이터 없는 학생만
-- ============================================

INSERT INTO tb_advisor_assignment (
    assignment_id, advisor_id, student_id,
    assignment_type, status,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    a.advisor_id,
    ts.student_id,
    'academic',
    'active',
    'SEED_46',
    NOW()
FROM tmp_grad_students ts
CROSS JOIN LATERAL (
    SELECT advisor_id
    FROM tb_advisor
    WHERE is_active = true
    ORDER BY hashtext(ts.student_id || advisor_id::text)
    LIMIT 1
) a
WHERE NOT EXISTS (
    SELECT 1 FROM tb_advisor_assignment aa WHERE aa.student_id = ts.student_id
);

DO $$ BEGIN RAISE NOTICE 'Part 12 완료: 지도교수 배정 생성'; END $$;


-- ============================================
-- Cleanup: 임시 테이블 삭제
-- ============================================

DROP TABLE IF EXISTS tmp_dept_category_46;
DROP TABLE IF EXISTS tmp_grad_students;
DROP TABLE IF EXISTS tmp_category_skills_46;
DROP TABLE IF EXISTS tmp_portfolio_data_46;

DO $$ BEGIN RAISE NOTICE '전체 완료: 2020-2021 졸업생 시드 데이터 생성 완료'; END $$;

COMMIT;
