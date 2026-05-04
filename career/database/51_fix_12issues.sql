-- =====================================================
-- 51_fix_12issues.sql
-- 12건 이슈 일괄 수정 (DB 관련 항목)
--
-- 이슈 3:  핵심역량 코드 6-14 비활성화 (5개만 사용)
-- 이슈 8:  사회복지사 중복 ROLE402 비활성화
-- 이슈 9:  위험 알림 학과/학년별 맞춤 재생성
-- 이슈 12: 77명 대상 일괄 적용
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 대상 학생 선정 (77명)
-- 4학년 17명 + 3학년 20명 + 2학년 20명 + 1학년 20명
-- =====================================================

CREATE TEMP TABLE tmp_dept_cat_51 AS
SELECT
    d.department_cd,
    d.department_nm,
    CASE
        WHEN d.department_nm ~ '의예|의학' THEN 'medical'
        WHEN d.department_nm ~ '간호' THEN 'nursing'
        WHEN d.department_nm ~ '약학|제약' THEN 'pharmacy'
        WHEN d.department_nm ~ '보건|치위생|치기공|물리치료|작업치료|방사선|임상병리|응급구조|의공학|재활|언어치료' THEN 'health'
        WHEN d.department_nm ~ '컴퓨터|소프트웨어|AI|인공지능|데이터|IT|정보통신|정보보안|멀티미디어|게임|웹툰영상' THEN 'it_engineering'
        WHEN d.department_nm ~ '건축' THEN 'architecture'
        WHEN d.department_nm ~ '토목|건설환경|건설' THEN 'civil_eng'
        WHEN d.department_nm ~ '기계|자동차|기계자동차|로봇' THEN 'mechanical'
        WHEN d.department_nm ~ '전자|전기|반도체|배터리' THEN 'electrical'
        WHEN d.department_nm ~ '화학공학|환경공학|에너지|나노|신소재|융합기술' THEN 'chemical_env'
        WHEN d.department_nm ~ '산업공학|산업경영|산업|스마트물류|소방' THEN 'industrial'
        WHEN d.department_nm ~ '경영|경제|회계|무역|금융|마케팅|국제통상|관광|호텔' THEN 'business'
        WHEN d.department_nm ~ '법학|행정|정치|외교|공공|경찰' THEN 'law_admin'
        WHEN d.department_nm ~ '교육|사범|유아|특수교육|상담|사회복지|발달' THEN 'education'
        WHEN d.department_nm ~ '국어|영어|일어|중국어|불어|독어|철학|사학|문학|어문|문헌정보|인문|역사|문화콘텐츠|문화유산' THEN 'humanities'
        WHEN d.department_nm ~ '디자인|미술|음악|영화|연극|애니메이션|만화|패션|공예|공연|미디어' THEN 'arts'
        WHEN d.department_nm ~ '수학|물리|화학|생물|생명|식품|통계|지구|해양|천문|환경' THEN 'science'
        ELSE 'general'
    END AS category
FROM tb_department d;

CREATE INDEX idx_tmp_dept_cat_51 ON tmp_dept_cat_51(department_cd);

CREATE TEMP TABLE tmp_target_51 AS
WITH ranked AS (
    SELECT
        s.student_id,
        s.student_nm,
        s.department_cd,
        s.admission_year,
        s.current_grade,
        dc.category,
        dc.department_nm,
        (SELECT count(*) FROM tb_grade g WHERE g.student_id = s.student_id)
        + (SELECT count(*) FROM tb_achievement a WHERE a.student_id = s.student_id)
        + (SELECT count(*) FROM tb_student_competency sc WHERE sc.student_id = s.student_id)
        AS data_count,
        ROW_NUMBER() OVER (
            PARTITION BY s.current_grade
            ORDER BY
                (SELECT count(*) FROM tb_grade g WHERE g.student_id = s.student_id) DESC,
                s.student_id
        ) AS rn
    FROM tb_student s
    JOIN tb_user u ON s.student_id = u.student_id
    JOIN tmp_dept_cat_51 dc ON s.department_cd = dc.department_cd
    WHERE s.current_grade IN (1, 2, 3, 4)
)
SELECT student_id, student_nm, department_cd, admission_year,
       current_grade, category, department_nm, data_count
FROM ranked
WHERE (current_grade = 4 AND rn <= 17)
   OR (current_grade = 3 AND rn <= 20)
   OR (current_grade = 2 AND rn <= 20)
   OR (current_grade = 1 AND rn <= 20);

CREATE INDEX idx_tmp_target_51_sid ON tmp_target_51(student_id);
CREATE INDEX idx_tmp_target_51_grade ON tmp_target_51(current_grade);
CREATE INDEX idx_tmp_target_51_cat ON tmp_target_51(category);

DO $$ BEGIN
    RAISE NOTICE 'Part 0 완료: 대상 학생 선정 (% 명)', (SELECT count(*) FROM tmp_target_51);
    RAISE NOTICE '  4학년: % 명', (SELECT count(*) FROM tmp_target_51 WHERE current_grade = 4);
    RAISE NOTICE '  3학년: % 명', (SELECT count(*) FROM tmp_target_51 WHERE current_grade = 3);
    RAISE NOTICE '  2학년: % 명', (SELECT count(*) FROM tmp_target_51 WHERE current_grade = 2);
    RAISE NOTICE '  1학년: % 명', (SELECT count(*) FROM tmp_target_51 WHERE current_grade = 1);
END $$;


-- =====================================================
-- Part 1: 이슈 3 - 핵심역량 (코드 6-14 비활성화, 1-5만 사용)
-- DB competency_cd: '1'(창의), '2'(융복합), '3'(소통), '4'(협력), '5'(도전)
-- 비활성화: '6'-'14'
-- =====================================================

-- 1a. 코드 6-14 비활성화
UPDATE tb_competency
SET use_fg = 'N', upd_user_id = 'FIX_51', upd_dt = NOW()
WHERE competency_cd IN ('6','7','8','9','10','11','12','13','14')
  AND use_fg = 'Y';

-- 1b. 77명 대상 코드 6-14 student_competency 삭제
DELETE FROM tb_student_competency
WHERE student_id IN (SELECT student_id FROM tmp_target_51)
  AND competency_cd IN ('6','7','8','9','10','11','12','13','14');

-- 1c. 역량 이름 보강 (이미 창의/융복합/소통/협력/도전이지만 역량 접미사 추가)
UPDATE tb_competency SET competency_nm = '창의역량',   competency_nm_en = 'Creativity',    upd_user_id = 'FIX_51', upd_dt = NOW() WHERE competency_cd = '1';
UPDATE tb_competency SET competency_nm = '융복합역량', competency_nm_en = 'Convergence',   upd_user_id = 'FIX_51', upd_dt = NOW() WHERE competency_cd = '2';
UPDATE tb_competency SET competency_nm = '소통역량',   competency_nm_en = 'Communication', upd_user_id = 'FIX_51', upd_dt = NOW() WHERE competency_cd = '3';
UPDATE tb_competency SET competency_nm = '협력역량',   competency_nm_en = 'Collaboration', upd_user_id = 'FIX_51', upd_dt = NOW() WHERE competency_cd = '4';
UPDATE tb_competency SET competency_nm = '도전역량',   competency_nm_en = 'Challenge',     upd_user_id = 'FIX_51', upd_dt = NOW() WHERE competency_cd = '5';

-- 1d. 77명 대상 코드 1-5 점수를 학년/카테고리별로 UPDATE
UPDATE tb_student_competency sc
SET current_score = ROUND((
    CASE
        WHEN t.current_grade = 1 THEN 35
        WHEN t.current_grade = 2 THEN 50
        WHEN t.current_grade = 3 THEN 60
        WHEN t.current_grade = 4 THEN 70
        ELSE 50
    END
    + CASE
        WHEN t.category IN ('it_engineering') AND sc.competency_cd = '1' THEN 15
        WHEN t.category IN ('it_engineering') AND sc.competency_cd = '2' THEN 12
        WHEN t.category IN ('medical','nursing','pharmacy','health') AND sc.competency_cd = '4' THEN 15
        WHEN t.category IN ('medical','nursing','pharmacy','health') AND sc.competency_cd = '5' THEN 12
        WHEN t.category IN ('education') AND sc.competency_cd = '3' THEN 15
        WHEN t.category IN ('education') AND sc.competency_cd = '4' THEN 12
        WHEN t.category IN ('business') AND sc.competency_cd = '2' THEN 15
        WHEN t.category IN ('business') AND sc.competency_cd = '3' THEN 12
        WHEN t.category IN ('arts') AND sc.competency_cd = '1' THEN 18
        WHEN t.category IN ('humanities') AND sc.competency_cd = '3' THEN 15
        WHEN t.category IN ('science') AND sc.competency_cd = '1' THEN 12
        WHEN t.category IN ('science') AND sc.competency_cd = '2' THEN 15
        ELSE 5
    END
    + (abs(hashtext(t.student_id || sc.competency_cd)) % 17 - 8)
)::numeric, 1),
    gap_score = ROUND((
        target_score - (
            CASE WHEN t.current_grade = 1 THEN 35 WHEN t.current_grade = 2 THEN 50 WHEN t.current_grade = 3 THEN 60 ELSE 70 END
            + 5 + (abs(hashtext(t.student_id || sc.competency_cd)) % 17 - 8)
        )
    )::numeric, 1),
    status = CASE
        WHEN (CASE WHEN t.current_grade = 1 THEN 40 WHEN t.current_grade = 2 THEN 55 WHEN t.current_grade = 3 THEN 65 ELSE 75 END) >= 80 THEN 'excellent'
        WHEN (CASE WHEN t.current_grade = 1 THEN 40 WHEN t.current_grade = 2 THEN 55 WHEN t.current_grade = 3 THEN 65 ELSE 75 END) >= 65 THEN 'good'
        WHEN (CASE WHEN t.current_grade = 1 THEN 40 WHEN t.current_grade = 2 THEN 55 WHEN t.current_grade = 3 THEN 65 ELSE 75 END) >= 50 THEN 'average'
        ELSE 'improve'
    END,
    trend = CASE WHEN t.current_grade >= 3 THEN 'up' ELSE 'stable' END,
    upd_user_id = 'FIX_51',
    upd_dt = NOW()
FROM tmp_target_51 t
WHERE sc.student_id = t.student_id
  AND sc.competency_cd IN ('1','2','3','4','5');

-- 1e. 77명 중 코드 1-5 데이터가 없는 학생에 대해 INSERT
INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    t.student_id,
    c.competency_cd,
    ROUND((
        CASE WHEN t.current_grade = 1 THEN 35 WHEN t.current_grade = 2 THEN 50 WHEN t.current_grade = 3 THEN 60 ELSE 70 END
        + 5 + (abs(hashtext(t.student_id || c.competency_cd)) % 17 - 8)
    )::numeric, 1),
    85,
    ROUND((85 - (
        CASE WHEN t.current_grade = 1 THEN 35 WHEN t.current_grade = 2 THEN 50 WHEN t.current_grade = 3 THEN 60 ELSE 70 END
        + 5 + (abs(hashtext(t.student_id || c.competency_cd)) % 17 - 8)
    ))::numeric, 1),
    CASE
        WHEN (CASE WHEN t.current_grade = 1 THEN 40 WHEN t.current_grade = 2 THEN 55 WHEN t.current_grade = 3 THEN 65 ELSE 75 END) >= 80 THEN 'excellent'
        WHEN (CASE WHEN t.current_grade = 1 THEN 40 WHEN t.current_grade = 2 THEN 55 WHEN t.current_grade = 3 THEN 65 ELSE 75 END) >= 65 THEN 'good'
        WHEN (CASE WHEN t.current_grade = 1 THEN 40 WHEN t.current_grade = 2 THEN 55 WHEN t.current_grade = 3 THEN 65 ELSE 75 END) >= 50 THEN 'average'
        ELSE 'improve'
    END,
    CASE WHEN t.current_grade >= 3 THEN 'up' ELSE 'stable' END,
    'FIX_51',
    NOW()
FROM tmp_target_51 t
CROSS JOIN tb_competency c
WHERE c.competency_cd IN ('1','2','3','4','5')
  AND c.use_fg = 'Y'
  AND NOT EXISTS (
      SELECT 1 FROM tb_student_competency sc
      WHERE sc.student_id = t.student_id AND sc.competency_cd = c.competency_cd
  );

DO $$ BEGIN
    RAISE NOTICE 'Part 1 완료: 역량 데이터 수정';
    RAISE NOTICE '  비활성화된 역량: %', (SELECT count(*) FROM tb_competency WHERE use_fg = 'N');
    RAISE NOTICE '  활성 역량: %', (SELECT count(*) FROM tb_competency WHERE use_fg = 'Y');
    RAISE NOTICE '  77명 코드1-5 역량건수: %', (SELECT count(*) FROM tb_student_competency WHERE student_id IN (SELECT student_id FROM tmp_target_51) AND competency_cd IN ('1','2','3','4','5'));
END $$;


-- =====================================================
-- Part 2: 이슈 8 - ROLE402 비활성화 (사회복지사 중복 제거)
-- =====================================================

UPDATE tb_role
SET use_fg = 'N', upd_user_id = 'FIX_51', upd_dt = NOW()
WHERE role_cd = 'ROLE402'
  AND use_fg = 'Y';

DO $$ BEGIN
    RAISE NOTICE 'Part 2 완료: ROLE402 비활성화';
END $$;


-- =====================================================
-- Part 3: 이슈 9 - 위험 알림 학과/학년별 맞춤 재생성
-- 스키마: risk_type, severity(critical/high/medium/low), title, description
-- trigger_value(numeric), threshold_value(numeric), status
-- =====================================================

-- 3a. 77명 기존 generic alert 삭제
DELETE FROM tb_risk_alert
WHERE student_id IN (SELECT student_id FROM tmp_target_51)
  AND ins_user_id IN ('SYSTEM', 'SEED_SCRIPT', 'FIX_41', 'FIX_44', 'FIX_50', 'system');

-- === 1학년: 학점관리 + 진로탐색 (2건/학생) ===
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'academic',
    CASE WHEN abs(hashtext(t.student_id || 'r1')) % 3 = 0 THEN 'medium' ELSE 'low' END,
    '1학년 학점 관리 주의',
    t.department_nm || ' ' || t.student_nm || ' 학생의 첫 학기 학점 관리가 필요합니다. 전공기초 과목의 학점이 향후 전공심화에 영향을 줍니다.',
    ROUND((2.0 + (abs(hashtext(t.student_id)) % 15) * 0.1)::numeric, 1),
    3.0,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 1;

INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'career',
    'low',
    '전공 적응 및 진로 탐색 필요',
    t.department_nm || ' 전공 적응기입니다. ' ||
    CASE t.category
        WHEN 'medical' THEN '의학 관련 봉사활동과 병원 탐방을 통해 적성을 확인하세요.'
        WHEN 'nursing' THEN '병원 탐방과 간호 봉사를 통해 직업적성을 확인하세요.'
        WHEN 'it_engineering' THEN '프로그래밍 동아리와 코딩 프로젝트로 개발 적성을 탐색하세요.'
        WHEN 'business' THEN '경영 사례 분석과 경제 동아리 활동을 통해 진로를 탐색하세요.'
        WHEN 'education' THEN '교육 봉사와 학습 멘토링으로 교직 적성을 확인하세요.'
        WHEN 'arts' THEN '작품 포트폴리오 준비와 공모전 참여를 시작하세요.'
        WHEN 'law_admin' THEN '시사 토론과 모의재판 동아리로 진로를 탐색하세요.'
        ELSE '전공 관련 동아리와 비교과활동으로 적성을 확인하세요.'
    END,
    0,
    1,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 1;

-- === 2학년: 전공심화 + 자격증준비 (2건/학생) ===
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'academic',
    CASE WHEN abs(hashtext(t.student_id || 'r2a')) % 3 = 0 THEN 'medium' ELSE 'low' END,
    '전공 심화 학점 관리',
    t.department_nm || ' 전공 심화과정에 진입합니다. 핵심 전공과목 이수 계획을 점검하세요.',
    ROUND((2.5 + (abs(hashtext(t.student_id)) % 12) * 0.1)::numeric, 1),
    3.0,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 2;

INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'career',
    'low',
    CASE t.category
        WHEN 'medical' THEN '의료 관련 자격증 준비 시작'
        WHEN 'nursing' THEN '간호 실습 준비 및 BLS 자격'
        WHEN 'it_engineering' THEN 'IT 자격증 취득 준비'
        WHEN 'business' THEN '경영/회계 자격증 준비'
        WHEN 'education' THEN '교원자격 관련 이수 확인'
        WHEN 'health' THEN '보건 관련 면허시험 준비'
        ELSE '전공 관련 자격증 준비'
    END,
    t.department_nm || ' 학과 특성에 맞는 자격증 취득을 시작할 시기입니다. 비교과활동도 함께 계획하세요.',
    0,
    1,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 2;

-- === 3학년: 졸업요건 + 취업준비 + 역량갭 (3건/학생) ===
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'academic',
    'medium',
    '졸업요건 충족 점검 필요',
    t.department_nm || ' 졸업 요건(전공학점, 교양학점, 졸업논문/시험 등) 충족 여부를 점검해야 합니다.',
    ROUND((70 + (abs(hashtext(t.student_id)) % 20))::numeric, 0),
    100,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 3;

INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'career',
    'medium',
    CASE t.category
        WHEN 'medical' THEN '의사국가고시 준비 본격화'
        WHEN 'nursing' THEN '간호사국가고시 준비 시작'
        WHEN 'it_engineering' THEN '개발 포트폴리오/인턴십 경험 확보'
        WHEN 'business' THEN '기업 인턴십/공모전 참여'
        WHEN 'education' THEN '교원임용시험 준비 본격화'
        WHEN 'health' THEN '국가면허시험 준비 본격화'
        ELSE '취업/진학 준비 본격화'
    END,
    t.department_nm || ' 전공 취업 준비를 본격적으로 시작해야 합니다. 역량 갭 분석 결과를 확인하세요.',
    ROUND((40 + (abs(hashtext(t.student_id || 'career')) % 30))::numeric, 0),
    80,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 3;

INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'competency',
    'low',
    '핵심역량 갭 분석 결과 확인',
    '목표 대비 부족한 역량이 있습니다. 남은 학기 동안 집중적으로 보완이 필요합니다.',
    ROUND((55 + (abs(hashtext(t.student_id || 'comp')) % 20))::numeric, 0),
    85,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 3;

-- === 4학년: 졸업임박 + 취업시즌 + 스킬갭 (3건/학생) ===
INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'academic',
    'high',
    '졸업 요건 최종 점검',
    t.department_nm || ' 졸업 예정자입니다. 미충족 졸업 요건이 없는지 최종 확인이 필요합니다.',
    ROUND((85 + (abs(hashtext(t.student_id)) % 15))::numeric, 0),
    130,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 4;

INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'career',
    'high',
    CASE t.category
        WHEN 'medical' THEN '의사국가고시 응시 준비'
        WHEN 'nursing' THEN '간호사국가고시 응시 준비'
        WHEN 'it_engineering' THEN 'IT 기업 하반기 채용 대비'
        WHEN 'business' THEN '기업 공채/수시 채용 지원'
        WHEN 'education' THEN '교원임용시험 최종 준비'
        WHEN 'health' THEN '국가면허시험 최종 준비'
        ELSE '취업/진학 최종 준비'
    END,
    t.department_nm || ' 전공 관련 취업 시즌입니다. 적극적인 취업 활동이 필요합니다.',
    ROUND((30 + (abs(hashtext(t.student_id || 'job')) % 40))::numeric, 0),
    80,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 4;

INSERT INTO tb_risk_alert (student_id, risk_type, severity, title, description, trigger_value, threshold_value, status, ins_user_id, ins_dt)
SELECT
    t.student_id,
    'competency',
    'medium',
    '직무 스킬 갭 보완 시급',
    '목표 직무 대비 부족한 스킬이 확인되었습니다. 졸업 전 집중 보완이 필요합니다.',
    ROUND((60 + (abs(hashtext(t.student_id || 'skill')) % 20))::numeric, 0),
    85,
    'active',
    'FIX_51',
    NOW()
FROM tmp_target_51 t
WHERE t.current_grade = 4;

DO $$ BEGIN
    RAISE NOTICE 'Part 3 완료: 위험 알림 재생성';
    RAISE NOTICE '  총 알림: %', (SELECT count(*) FROM tb_risk_alert WHERE ins_user_id = 'FIX_51');
    RAISE NOTICE '  1학년: %', (SELECT count(*) FROM tb_risk_alert ra JOIN tmp_target_51 t ON ra.student_id = t.student_id WHERE t.current_grade = 1 AND ra.ins_user_id = 'FIX_51');
    RAISE NOTICE '  2학년: %', (SELECT count(*) FROM tb_risk_alert ra JOIN tmp_target_51 t ON ra.student_id = t.student_id WHERE t.current_grade = 2 AND ra.ins_user_id = 'FIX_51');
    RAISE NOTICE '  3학년: %', (SELECT count(*) FROM tb_risk_alert ra JOIN tmp_target_51 t ON ra.student_id = t.student_id WHERE t.current_grade = 3 AND ra.ins_user_id = 'FIX_51');
    RAISE NOTICE '  4학년: %', (SELECT count(*) FROM tb_risk_alert ra JOIN tmp_target_51 t ON ra.student_id = t.student_id WHERE t.current_grade = 4 AND ra.ins_user_id = 'FIX_51');
END $$;


-- =====================================================
-- Part 4: 검증
-- =====================================================

DO $$ BEGIN
    RAISE NOTICE '=== 검증 결과 ===';
    RAISE NOTICE '1. 활성 역량 (5개): %', (SELECT count(*) FROM tb_competency WHERE use_fg = 'Y');
    RAISE NOTICE '2. ROLE402 비활성: %', (SELECT use_fg FROM tb_role WHERE role_cd = 'ROLE402');
    RAISE NOTICE '3. 77명 코드1-5 역량(평균건수): %', (SELECT ROUND(AVG(cnt), 1) FROM (SELECT count(*) cnt FROM tb_student_competency WHERE student_id IN (SELECT student_id FROM tmp_target_51) AND competency_cd IN ('1','2','3','4','5') GROUP BY student_id) sub);
    RAISE NOTICE '4. 77명 활성알림(평균건수): %', (SELECT ROUND(AVG(cnt), 1) FROM (SELECT count(*) cnt FROM tb_risk_alert WHERE student_id IN (SELECT student_id FROM tmp_target_51) AND status = 'active' GROUP BY student_id) sub);
END $$;

DROP TABLE IF EXISTS tmp_target_51;
DROP TABLE IF EXISTS tmp_dept_cat_51;

COMMIT;
