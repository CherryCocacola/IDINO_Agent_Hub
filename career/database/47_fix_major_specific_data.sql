-- =====================================================
-- 47_fix_major_specific_data.sql
-- 전공별 데이터 정합성 수정 (시뮬레이션, 스킬, 포트폴리오, 갭분석)
-- =====================================================
-- 문제:
--   1. 스킬: engineering 카테고리가 건축/토목/기계/전자/화공/산업을 IT 스킬(SKE001-007)로 배정
--   2. 시뮬레이션: 모든 시나리오가 IT 직군 중심
--   3. 포트폴리오: 비IT 공학 학과에 IT 포트폴리오(프로그래밍, 정보처리기사) 배정
--   4. 갭분석: 거의 전원 데이터 부재, 기존 건축학과에 IT role 매핑
-- 해결:
--   engineering → it_engineering, architecture, civil_eng, mechanical, electrical, chemical_env, industrial
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 세분화된 학과 카테고리 매핑
-- 기존 engineering → 7개 세부 카테고리로 분리
-- =====================================================

CREATE TEMP TABLE tmp_dept_cat_47 AS
SELECT
    d.department_cd,
    d.department_nm,
    CASE
        WHEN d.department_nm ~ '의예|의학' THEN 'medical'
        WHEN d.department_nm ~ '간호' THEN 'nursing'
        WHEN d.department_nm ~ '약학|약' THEN 'pharmacy'
        WHEN d.department_nm ~ '보건|치위생|치기공|물리치료|작업치료|방사선|임상병리|응급구조|의공학|재활|언어치료' THEN 'health'
        -- engineering 세분화
        WHEN d.department_nm ~ '컴퓨터|소프트웨어|AI|인공지능|데이터|IT|정보통신|정보보안|멀티미디어|게임|웹툰영상' THEN 'it_engineering'
        WHEN d.department_nm ~ '건축' THEN 'architecture'
        WHEN d.department_nm ~ '토목|건설환경|건설' THEN 'civil_eng'
        WHEN d.department_nm ~ '기계|자동차|기계자동차|로봇' THEN 'mechanical'
        WHEN d.department_nm ~ '전자|전기|반도체|배터리' THEN 'electrical'
        WHEN d.department_nm ~ '화학공학|환경공학|에너지|나노|신소재|융합기술' THEN 'chemical_env'
        WHEN d.department_nm ~ '산업공학|산업경영|산업|스마트물류|소방' THEN 'industrial'
        -- 나머지 유지
        WHEN d.department_nm ~ '경영|경제|회계|무역|금융|마케팅|국제통상|관광|호텔' THEN 'business'
        WHEN d.department_nm ~ '법학|행정|정치|외교|공공|경찰' THEN 'law_admin'
        WHEN d.department_nm ~ '교육|사범|유아|특수교육|상담|사회복지|발달' THEN 'education'
        WHEN d.department_nm ~ '국어|영어|일어|중국어|불어|독어|철학|사학|문학|어문|문헌정보|인문|역사|문화콘텐츠|문화유산' THEN 'humanities'
        WHEN d.department_nm ~ '디자인|미술|음악|영화|연극|애니메이션|만화|패션|공예|공연|미디어' THEN 'arts'
        WHEN d.department_nm ~ '수학|물리|화학|생물|생명|식품|통계|지구|해양|천문|환경' THEN 'science'
        ELSE 'general'
    END AS category
FROM tb_department d;

CREATE INDEX idx_tmp_dept_cat_47 ON tmp_dept_cat_47(department_cd);
CREATE INDEX idx_tmp_dept_cat_47_cat ON tmp_dept_cat_47(category);

-- 전체 학생 + 세분화된 카테고리
CREATE TEMP TABLE tmp_all_students_47 AS
SELECT s.student_id,
       s.student_nm,
       s.department_cd,
       s.admission_year,
       s.current_grade,
       dc.category,
       dc.department_nm,
       abs(hashtext(s.student_id)) % 100 AS h
FROM tb_student s
JOIN tmp_dept_cat_47 dc ON s.department_cd = dc.department_cd;

CREATE INDEX idx_tmp_all_47_sid ON tmp_all_students_47(student_id);
CREATE INDEX idx_tmp_all_47_cat ON tmp_all_students_47(category);

DO $$ BEGIN RAISE NOTICE 'Part 0 완료: 세분화 카테고리 매핑 (%s 학생)', (SELECT count(*) FROM tmp_all_students_47); END $$;


-- =====================================================
-- Part 1: 신규 스킬 생성 (tb_skill)
-- 6개 공학 세부 카테고리 × 7개 스킬 = 42개 신규 스킬
-- it_engineering은 기존 SKE001-007 유지
-- =====================================================

INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt)
VALUES
    -- architecture (SKAR001-007)
    ('SKAR001', '건축설계', 'Architectural Design', ARRAY['건축설계','건축디자인','Architectural Design'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKAR002', 'CAD/BIM', 'CAD/BIM', ARRAY['CAD','BIM','AutoCAD','Revit','건축CAD'], 'technical', 3, 'Y', 'FIX_47', NOW()),
    ('SKAR003', '건축구조', 'Structural Engineering', ARRAY['건축구조','구조역학','Structural'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKAR004', '건축법규', 'Building Codes', ARRAY['건축법규','건축법','Building Code'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKAR005', '건축시공', 'Building Construction', ARRAY['건축시공','시공학','Construction'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKAR006', '건축환경', 'Building Environment', ARRAY['건축환경','환경설비','환경공학'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKAR007', '3D모델링', '3D Modeling', ARRAY['3D모델링','3D Modeling','SketchUp','Rhino'], 'technical', 3, 'Y', 'FIX_47', NOW()),

    -- civil_eng (SKCV001-007)
    ('SKCV001', '구조역학', 'Structural Mechanics', ARRAY['구조역학','구조해석','Structural Mechanics'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKCV002', '수리학', 'Hydraulics', ARRAY['수리학','수문학','Hydraulics'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKCV003', '토질역학', 'Soil Mechanics', ARRAY['토질역학','지반공학','Geotechnical'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKCV004', '측량학', 'Surveying', ARRAY['측량학','측량','Surveying','GIS'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKCV005', '도로공학', 'Highway Engineering', ARRAY['도로공학','교통공학','Highway Eng'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKCV006', '시공관리', 'Construction Management', ARRAY['시공관리','건설관리','CM'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKCV007', '토목CAD', 'Civil CAD', ARRAY['토목CAD','Civil3D','AutoCAD Civil'], 'technical', 3, 'Y', 'FIX_47', NOW()),

    -- mechanical (SKME001-007)
    ('SKME001', '열역학', 'Thermodynamics', ARRAY['열역학','열공학','Thermodynamics'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKME002', '유체역학', 'Fluid Mechanics', ARRAY['유체역학','유체공학','Fluid Mechanics'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKME003', '재료역학', 'Mechanics of Materials', ARRAY['재료역학','고체역학','Solid Mechanics'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKME004', '기계설계', 'Mechanical Design', ARRAY['기계설계','Machine Design','메카니즘'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKME005', 'CAD/CAM', 'CAD/CAM', ARRAY['CAD/CAM','SolidWorks','CATIA','CAD'], 'technical', 3, 'Y', 'FIX_47', NOW()),
    ('SKME006', '제어공학', 'Control Engineering', ARRAY['제어공학','자동제어','Control Systems'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKME007', '자동화시스템', 'Automation Systems', ARRAY['자동화','자동화시스템','PLC','로봇공학'], 'technical', 3, 'Y', 'FIX_47', NOW()),

    -- electrical (SKEL001-007)
    ('SKEL001', '회로이론', 'Circuit Theory', ARRAY['회로이론','전기회로','Circuit Theory'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKEL002', '전자기학', 'Electromagnetics', ARRAY['전자기학','전자기','EM'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKEL003', '신호처리', 'Signal Processing', ARRAY['신호처리','DSP','Signal Processing'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKEL004', '반도체', 'Semiconductor', ARRAY['반도체','Semiconductor','반도체공학'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKEL005', '디지털시스템', 'Digital Systems', ARRAY['디지털시스템','디지털회로','Digital Logic'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKEL006', '임베디드', 'Embedded Systems', ARRAY['임베디드','임베디드시스템','Embedded'], 'technical', 3, 'Y', 'FIX_47', NOW()),
    ('SKEL007', 'PCB설계', 'PCB Design', ARRAY['PCB설계','PCB','회로설계','Altium'], 'technical', 3, 'Y', 'FIX_47', NOW()),

    -- chemical_env (SKCE001-007)
    ('SKCE001', '화학공정', 'Chemical Process', ARRAY['화학공정','화공','Chemical Process'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKCE002', '반응공학', 'Reaction Engineering', ARRAY['반응공학','화학반응','Chemical Reaction'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKCE003', '열전달', 'Heat Transfer', ARRAY['열전달','전열','Heat Transfer'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKCE004', '환경영향평가', 'Environmental Impact Assessment', ARRAY['환경영향평가','환경평가','EIA'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKCE005', '수처리', 'Water Treatment', ARRAY['수처리','수질관리','Water Treatment'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKCE006', '대기관리', 'Air Quality Management', ARRAY['대기관리','대기오염','Air Quality'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKCE007', '폐기물처리', 'Waste Management', ARRAY['폐기물처리','폐기물관리','Waste Management'], 'domain', 3, 'Y', 'FIX_47', NOW()),

    -- industrial (SKIN001-007)
    ('SKIN001', '생산관리', 'Production Management', ARRAY['생산관리','생산공학','Production Mgmt'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKIN002', '품질관리', 'Quality Management', ARRAY['품질관리','QC','Quality Control','6시그마'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKIN003', '인간공학', 'Ergonomics', ARRAY['인간공학','인체공학','Ergonomics','HCI'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKIN004', '최적화', 'Optimization', ARRAY['최적화','OR','Operations Research'], 'domain', 4, 'Y', 'FIX_47', NOW()),
    ('SKIN005', '공급망관리', 'Supply Chain Management', ARRAY['공급망관리','SCM','물류관리'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKIN006', '경영과학', 'Management Science', ARRAY['경영과학','경영공학','Management Science'], 'domain', 3, 'Y', 'FIX_47', NOW()),
    ('SKIN007', '시스템공학', 'Systems Engineering', ARRAY['시스템공학','시스템설계','Systems Eng'], 'domain', 4, 'Y', 'FIX_47', NOW())
ON CONFLICT (skill_cd) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 1 완료: 신규 스킬 42개 생성'; END $$;


-- =====================================================
-- Part 1-B: 역할-스킬 매핑 추가 (tb_role_skill_map)
-- 세분화된 카테고리에 맞는 role 신규 생성 + 매핑
-- =====================================================

-- 세분화된 공학 카테고리용 role 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, role_category, description, avg_salary, growth_rate, use_fg, ins_user_id, ins_dt)
VALUES
    ('ROLE231', '건축설계사', 'Architect', 'architecture', '건물 및 구조물의 설계를 담당하는 전문가', 45000000, 3.5, 'Y', 'FIX_47', NOW()),
    ('ROLE232', '건축시공관리자', 'Construction Manager', 'architecture', '건축 현장의 시공 관리를 담당하는 전문가', 48000000, 4.0, 'Y', 'FIX_47', NOW()),
    ('ROLE233', '토목설계엔지니어', 'Civil Engineer', 'civil_engineering', '도로, 교량, 터널 등의 설계를 담당하는 엔지니어', 46000000, 3.0, 'Y', 'FIX_47', NOW()),
    ('ROLE234', '건설현장관리자', 'Site Manager', 'civil_engineering', '건설 현장의 전반적인 관리를 담당', 50000000, 3.5, 'Y', 'FIX_47', NOW()),
    ('ROLE235', '기계설계엔지니어', 'Mechanical Engineer', 'mechanical', '기계장치 및 시스템의 설계를 담당하는 엔지니어', 48000000, 4.0, 'Y', 'FIX_47', NOW()),
    ('ROLE236', '자동차엔지니어', 'Automotive Engineer', 'mechanical', '자동차 부품 및 시스템 개발 엔지니어', 52000000, 4.5, 'Y', 'FIX_47', NOW()),
    ('ROLE237', '전자회로엔지니어', 'Electronics Engineer', 'electrical', '전자회로 및 시스템 설계 엔지니어', 50000000, 5.0, 'Y', 'FIX_47', NOW()),
    ('ROLE238', '반도체엔지니어', 'Semiconductor Engineer', 'electrical', '반도체 설계 및 공정 엔지니어', 55000000, 6.0, 'Y', 'FIX_47', NOW()),
    ('ROLE239', '화학공정엔지니어', 'Chemical Process Engineer', 'chemical', '화학 공정 설계 및 관리 엔지니어', 47000000, 3.0, 'Y', 'FIX_47', NOW()),
    ('ROLE240', '환경엔지니어', 'Environmental Engineer', 'environmental', '환경 문제 해결 및 관리를 담당하는 엔지니어', 44000000, 5.0, 'Y', 'FIX_47', NOW()),
    ('ROLE261', '산업엔지니어', 'Industrial Engineer', 'industrial', '생산 시스템 최적화 및 관리를 담당하는 엔지니어', 47000000, 4.0, 'Y', 'FIX_47', NOW()),
    ('ROLE262', '품질관리전문가', 'Quality Engineer', 'industrial', '제품 및 공정 품질관리를 담당하는 전문가', 45000000, 3.5, 'Y', 'FIX_47', NOW())
ON CONFLICT (role_cd) DO NOTHING;

-- 역할-스킬 매핑 추가
INSERT INTO tb_role_skill_map (role_cd, skill_cd, required_level, importance, market_demand_score, growth_trend, ins_user_id, ins_dt)
VALUES
    -- ROLE231(건축설계사) → SKAR001-007
    ('ROLE231', 'SKAR001', 5, 'critical',    95.0, 'stable',  'FIX_47', NOW()),
    ('ROLE231', 'SKAR002', 5, 'critical',    92.0, 'growing', 'FIX_47', NOW()),
    ('ROLE231', 'SKAR003', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE231', 'SKAR004', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),
    ('ROLE231', 'SKAR005', 3, 'important',   80.0, 'stable',  'FIX_47', NOW()),
    ('ROLE231', 'SKAR006', 3, 'nice_to_have',75.0, 'growing', 'FIX_47', NOW()),
    ('ROLE231', 'SKAR007', 4, 'important',   88.0, 'growing', 'FIX_47', NOW()),

    -- ROLE232(건축시공관리자) → SKAR001-007
    ('ROLE232', 'SKAR001', 3, 'important',   82.0, 'stable',  'FIX_47', NOW()),
    ('ROLE232', 'SKAR002', 4, 'critical',    90.0, 'growing', 'FIX_47', NOW()),
    ('ROLE232', 'SKAR003', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE232', 'SKAR004', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE232', 'SKAR005', 5, 'critical',    96.0, 'stable',  'FIX_47', NOW()),
    ('ROLE232', 'SKAR006', 3, 'important',   78.0, 'growing', 'FIX_47', NOW()),
    ('ROLE232', 'SKAR007', 3, 'nice_to_have',72.0, 'stable',  'FIX_47', NOW()),

    -- ROLE233(토목설계엔지니어) → SKCV001-007
    ('ROLE233', 'SKCV001', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE233', 'SKCV002', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE233', 'SKCV003', 5, 'critical',    92.0, 'stable',  'FIX_47', NOW()),
    ('ROLE233', 'SKCV004', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),
    ('ROLE233', 'SKCV005', 4, 'important',   82.0, 'stable',  'FIX_47', NOW()),
    ('ROLE233', 'SKCV006', 3, 'important',   78.0, 'stable',  'FIX_47', NOW()),
    ('ROLE233', 'SKCV007', 4, 'critical',    88.0, 'growing', 'FIX_47', NOW()),

    -- ROLE234(건설현장관리자) → SKCV001-007
    ('ROLE234', 'SKCV001', 3, 'important',   82.0, 'stable',  'FIX_47', NOW()),
    ('ROLE234', 'SKCV002', 3, 'important',   78.0, 'stable',  'FIX_47', NOW()),
    ('ROLE234', 'SKCV003', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE234', 'SKCV004', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE234', 'SKCV005', 3, 'important',   80.0, 'stable',  'FIX_47', NOW()),
    ('ROLE234', 'SKCV006', 5, 'critical',    96.0, 'stable',  'FIX_47', NOW()),
    ('ROLE234', 'SKCV007', 3, 'nice_to_have',75.0, 'growing', 'FIX_47', NOW()),

    -- ROLE235(기계설계엔지니어) → SKME001-007
    ('ROLE235', 'SKME001', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE235', 'SKME002', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE235', 'SKME003', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE235', 'SKME004', 5, 'critical',    96.0, 'stable',  'FIX_47', NOW()),
    ('ROLE235', 'SKME005', 5, 'critical',    92.0, 'growing', 'FIX_47', NOW()),
    ('ROLE235', 'SKME006', 3, 'important',   80.0, 'stable',  'FIX_47', NOW()),
    ('ROLE235', 'SKME007', 3, 'nice_to_have',75.0, 'growing', 'FIX_47', NOW()),

    -- ROLE236(자동차엔지니어) → SKME001-007
    ('ROLE236', 'SKME001', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE236', 'SKME002', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE236', 'SKME003', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE236', 'SKME004', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),
    ('ROLE236', 'SKME005', 4, 'critical',    90.0, 'growing', 'FIX_47', NOW()),
    ('ROLE236', 'SKME006', 5, 'critical',    96.0, 'growing', 'FIX_47', NOW()),
    ('ROLE236', 'SKME007', 4, 'critical',    92.0, 'growing', 'FIX_47', NOW()),

    -- ROLE237(전자회로엔지니어) → SKEL001-007
    ('ROLE237', 'SKEL001', 5, 'critical',    96.0, 'stable',  'FIX_47', NOW()),
    ('ROLE237', 'SKEL002', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE237', 'SKEL003', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),
    ('ROLE237', 'SKEL004', 3, 'important',   82.0, 'growing', 'FIX_47', NOW()),
    ('ROLE237', 'SKEL005', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE237', 'SKEL006', 4, 'critical',    88.0, 'growing', 'FIX_47', NOW()),
    ('ROLE237', 'SKEL007', 5, 'critical',    92.0, 'stable',  'FIX_47', NOW()),

    -- ROLE238(반도체엔지니어) → SKEL001-007
    ('ROLE238', 'SKEL001', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE238', 'SKEL002', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE238', 'SKEL003', 4, 'important',   85.0, 'growing', 'FIX_47', NOW()),
    ('ROLE238', 'SKEL004', 5, 'critical',    98.0, 'growing', 'FIX_47', NOW()),
    ('ROLE238', 'SKEL005', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE238', 'SKEL006', 4, 'important',   82.0, 'growing', 'FIX_47', NOW()),
    ('ROLE238', 'SKEL007', 3, 'important',   78.0, 'stable',  'FIX_47', NOW()),

    -- ROLE239(화학공정엔지니어) → SKCE001-007
    ('ROLE239', 'SKCE001', 5, 'critical',    96.0, 'stable',  'FIX_47', NOW()),
    ('ROLE239', 'SKCE002', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE239', 'SKCE003', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE239', 'SKCE004', 3, 'important',   78.0, 'growing', 'FIX_47', NOW()),
    ('ROLE239', 'SKCE005', 3, 'nice_to_have',72.0, 'stable',  'FIX_47', NOW()),
    ('ROLE239', 'SKCE006', 3, 'nice_to_have',70.0, 'stable',  'FIX_47', NOW()),
    ('ROLE239', 'SKCE007', 3, 'nice_to_have',68.0, 'stable',  'FIX_47', NOW()),

    -- ROLE240(환경엔지니어) → SKCE001-007
    ('ROLE240', 'SKCE001', 3, 'important',   80.0, 'stable',  'FIX_47', NOW()),
    ('ROLE240', 'SKCE002', 3, 'important',   78.0, 'stable',  'FIX_47', NOW()),
    ('ROLE240', 'SKCE003', 3, 'nice_to_have',72.0, 'stable',  'FIX_47', NOW()),
    ('ROLE240', 'SKCE004', 5, 'critical',    96.0, 'growing', 'FIX_47', NOW()),
    ('ROLE240', 'SKCE005', 5, 'critical',    94.0, 'growing', 'FIX_47', NOW()),
    ('ROLE240', 'SKCE006', 5, 'critical',    92.0, 'growing', 'FIX_47', NOW()),
    ('ROLE240', 'SKCE007', 4, 'critical',    90.0, 'growing', 'FIX_47', NOW()),

    -- ROLE261(산업엔지니어) → SKIN001-007
    ('ROLE261', 'SKIN001', 5, 'critical',    94.0, 'stable',  'FIX_47', NOW()),
    ('ROLE261', 'SKIN002', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE261', 'SKIN003', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),
    ('ROLE261', 'SKIN004', 5, 'critical',    96.0, 'growing', 'FIX_47', NOW()),
    ('ROLE261', 'SKIN005', 4, 'critical',    88.0, 'growing', 'FIX_47', NOW()),
    ('ROLE261', 'SKIN006', 3, 'important',   80.0, 'stable',  'FIX_47', NOW()),
    ('ROLE261', 'SKIN007', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),

    -- ROLE262(품질관리전문가) → SKIN001-007
    ('ROLE262', 'SKIN001', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW()),
    ('ROLE262', 'SKIN002', 5, 'critical',    96.0, 'stable',  'FIX_47', NOW()),
    ('ROLE262', 'SKIN003', 4, 'critical',    90.0, 'stable',  'FIX_47', NOW()),
    ('ROLE262', 'SKIN004', 3, 'important',   82.0, 'growing', 'FIX_47', NOW()),
    ('ROLE262', 'SKIN005', 3, 'important',   80.0, 'growing', 'FIX_47', NOW()),
    ('ROLE262', 'SKIN006', 4, 'important',   85.0, 'stable',  'FIX_47', NOW()),
    ('ROLE262', 'SKIN007', 4, 'critical',    88.0, 'stable',  'FIX_47', NOW())
ON CONFLICT DO NOTHING;

-- 스킬 관계 추가
INSERT INTO tb_skill_relation (source_skill_cd, target_skill_cd, relation_type, strength, ins_user_id, ins_dt)
VALUES
    -- architecture
    ('SKAR001', 'SKAR002', 'builds_on',      0.90, 'FIX_47', NOW()),
    ('SKAR001', 'SKAR007', 'builds_on',      0.85, 'FIX_47', NOW()),
    ('SKAR003', 'SKAR005', 'prerequisite',   0.90, 'FIX_47', NOW()),
    ('SKAR004', 'SKAR005', 'complementary',  0.80, 'FIX_47', NOW()),
    ('SKAR002', 'SKAR007', 'complementary',  0.85, 'FIX_47', NOW()),
    -- civil_eng
    ('SKCV001', 'SKCV003', 'prerequisite',   0.90, 'FIX_47', NOW()),
    ('SKCV002', 'SKCV005', 'builds_on',      0.80, 'FIX_47', NOW()),
    ('SKCV004', 'SKCV007', 'builds_on',      0.85, 'FIX_47', NOW()),
    ('SKCV001', 'SKCV006', 'complementary',  0.75, 'FIX_47', NOW()),
    -- mechanical
    ('SKME001', 'SKME002', 'complementary',  0.90, 'FIX_47', NOW()),
    ('SKME003', 'SKME004', 'prerequisite',   0.90, 'FIX_47', NOW()),
    ('SKME004', 'SKME005', 'builds_on',      0.85, 'FIX_47', NOW()),
    ('SKME006', 'SKME007', 'builds_on',      0.80, 'FIX_47', NOW()),
    -- electrical
    ('SKEL001', 'SKEL005', 'prerequisite',   0.90, 'FIX_47', NOW()),
    ('SKEL002', 'SKEL003', 'builds_on',      0.85, 'FIX_47', NOW()),
    ('SKEL004', 'SKEL006', 'builds_on',      0.80, 'FIX_47', NOW()),
    ('SKEL005', 'SKEL006', 'prerequisite',   0.85, 'FIX_47', NOW()),
    ('SKEL006', 'SKEL007', 'builds_on',      0.80, 'FIX_47', NOW()),
    -- chemical_env
    ('SKCE001', 'SKCE002', 'prerequisite',   0.90, 'FIX_47', NOW()),
    ('SKCE001', 'SKCE003', 'complementary',  0.85, 'FIX_47', NOW()),
    ('SKCE004', 'SKCE005', 'complementary',  0.80, 'FIX_47', NOW()),
    ('SKCE005', 'SKCE006', 'complementary',  0.75, 'FIX_47', NOW()),
    -- industrial
    ('SKIN001', 'SKIN002', 'complementary',  0.90, 'FIX_47', NOW()),
    ('SKIN004', 'SKIN005', 'builds_on',      0.85, 'FIX_47', NOW()),
    ('SKIN006', 'SKIN007', 'builds_on',      0.80, 'FIX_47', NOW()),
    ('SKIN003', 'SKIN001', 'complementary',  0.75, 'FIX_47', NOW())
ON CONFLICT DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 1-B 완료: 역할-스킬 매핑 및 스킬 관계 추가'; END $$;


-- =====================================================
-- Part 2: 스킬 데이터 수정 (tb_student_skill)
-- 1. 비IT 공학 카테고리 학생의 SKE001-007 삭제
-- 2. 비IT 카테고리 학생의 SK01-SK08 (system 시드) 삭제
-- 3. 올바른 카테고리별 스킬 삽입
-- =====================================================

-- 2-1: 비IT 공학 카테고리에서 SKE001-007 삭제
DELETE FROM tb_student_skill ss
USING tmp_all_students_47 ts
WHERE ss.student_id = ts.student_id
  AND ts.category IN ('architecture','civil_eng','mechanical','electrical','chemical_env','industrial')
  AND ss.skill_cd IN ('SKE001','SKE002','SKE003','SKE004','SKE005','SKE006','SKE007');

DO $$ BEGIN RAISE NOTICE 'Part 2-1 완료: 비IT 공학 카테고리 SKE001-007 삭제 (%s rows)',
    (SELECT count(*) FROM tmp_all_students_47 WHERE category IN ('architecture','civil_eng','mechanical','electrical','chemical_env','industrial')); END $$;

-- 2-2: 비IT 카테고리 학생의 system 시드 SK01-SK08 삭제
DELETE FROM tb_student_skill ss
USING tmp_all_students_47 ts
WHERE ss.student_id = ts.student_id
  AND ts.category NOT IN ('it_engineering')
  AND ss.skill_cd IN ('SK01','SK02','SK03','SK04','SK05','SK06','SK07','SK08');

DO $$ BEGIN RAISE NOTICE 'Part 2-2 완료: 비IT 카테고리 SK01-SK08 삭제'; END $$;

-- 2-3: 새 카테고리별 스킬 매핑
CREATE TEMP TABLE tmp_cat_skills_47 (category VARCHAR(20), skill_cd VARCHAR(20), skill_order INT);
INSERT INTO tmp_cat_skills_47 VALUES
    ('architecture','SKAR001',1),('architecture','SKAR002',2),('architecture','SKAR003',3),('architecture','SKAR004',4),('architecture','SKAR005',5),('architecture','SKAR006',6),('architecture','SKAR007',7),
    ('civil_eng','SKCV001',1),('civil_eng','SKCV002',2),('civil_eng','SKCV003',3),('civil_eng','SKCV004',4),('civil_eng','SKCV005',5),('civil_eng','SKCV006',6),('civil_eng','SKCV007',7),
    ('mechanical','SKME001',1),('mechanical','SKME002',2),('mechanical','SKME003',3),('mechanical','SKME004',4),('mechanical','SKME005',5),('mechanical','SKME006',6),('mechanical','SKME007',7),
    ('electrical','SKEL001',1),('electrical','SKEL002',2),('electrical','SKEL003',3),('electrical','SKEL004',4),('electrical','SKEL005',5),('electrical','SKEL006',6),('electrical','SKEL007',7),
    ('chemical_env','SKCE001',1),('chemical_env','SKCE002',2),('chemical_env','SKCE003',3),('chemical_env','SKCE004',4),('chemical_env','SKCE005',5),('chemical_env','SKCE006',6),('chemical_env','SKCE007',7),
    ('industrial','SKIN001',1),('industrial','SKIN002',2),('industrial','SKIN003',3),('industrial','SKIN004',4),('industrial','SKIN005',5),('industrial','SKIN006',6),('industrial','SKIN007',7);

-- 2-4: 세분화 카테고리 학생에 올바른 스킬 삽입
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
    -- current_level: 재학생 1~4, 졸업생 3~5
    CASE
        WHEN ts.admission_year <= 2021 THEN LEAST(5, 3 + abs(hashtext(ts.student_id || cs.skill_cd)) % 3)
        ELSE LEAST(4, 1 + ts.current_grade + abs(hashtext(ts.student_id || cs.skill_cd)) % 2)
    END,
    -- target_level: 4~5
    LEAST(5, 4 + abs(hashtext(ts.student_id || cs.skill_cd || 't')) % 2),
    -- evidence_count
    CASE
        WHEN ts.admission_year <= 2021 THEN 2 + abs(hashtext(ts.student_id || cs.skill_cd || 'e')) % 5
        ELSE 1 + abs(hashtext(ts.student_id || cs.skill_cd || 'e')) % 4
    END,
    -- last_verified_date
    CASE
        WHEN ts.admission_year <= 2021 THEN ('2023-03-01'::date + (abs(hashtext(ts.student_id || cs.skill_cd || 'd')) % 500)::int)
        ELSE ('2024-03-01'::date + (abs(hashtext(ts.student_id || cs.skill_cd || 'd')) % 300)::int)
    END,
    -- verification_source
    CASE abs(hashtext(ts.student_id || cs.skill_cd || 'v')) % 4
        WHEN 0 THEN 'course'
        WHEN 1 THEN 'certificate'
        WHEN 2 THEN 'project'
        ELSE 'self_assessment'
    END,
    -- trend
    CASE
        WHEN ts.admission_year <= 2021 THEN
            CASE WHEN abs(hashtext(ts.student_id || cs.skill_cd || 'r')) % 3 = 0 THEN 'up' ELSE 'stable' END
        ELSE
            CASE abs(hashtext(ts.student_id || cs.skill_cd || 'r')) % 3
                WHEN 0 THEN 'up'
                WHEN 1 THEN 'stable'
                ELSE 'up'
            END
    END,
    'FIX_47',
    NOW()
FROM tmp_all_students_47 ts
JOIN tmp_cat_skills_47 cs ON ts.category = cs.category
WHERE NOT EXISTS (
    SELECT 1 FROM tb_student_skill ss
    WHERE ss.student_id = ts.student_id AND ss.skill_cd = cs.skill_cd
);

DO $$ BEGIN RAISE NOTICE 'Part 2 완료: 세분화 카테고리별 스킬 삽입'; END $$;


-- =====================================================
-- Part 3: 시뮬레이션 수정 (tb_simulation_scenario)
-- 1. 비IT 카테고리 학생의 기존 IT 시뮬레이션 삭제
-- 2. 카테고리별 전공 맞춤 시나리오 삽입
-- =====================================================

-- 3-1: 비IT 카테고리 학생의 기존 시뮬레이션 삭제
-- (system 시드 = 기존 IT 시뮬레이션)
DELETE FROM tb_simulation_scenario ss
USING tmp_all_students_47 ts
WHERE ss.student_id = ts.student_id
  AND ts.category IN ('architecture','civil_eng','mechanical','electrical','chemical_env','industrial')
  AND ss.ins_user_id IN ('BULK_FIX','SEED_46','system');

DO $$ BEGIN RAISE NOTICE 'Part 3-1 완료: 비IT 카테고리 기존 시뮬레이션 삭제'; END $$;

-- 3-2: 카테고리별 시뮬레이션 시나리오 temp table
CREATE TEMP TABLE tmp_sim_scenarios_47 (
    category VARCHAR(20),
    scenario_type VARCHAR(30),
    scenario_name VARCHAR(200),
    variables_json TEXT,
    results_json TEXT,
    recommendation TEXT
);

INSERT INTO tmp_sim_scenarios_47 VALUES
-- architecture × career_path
('architecture', 'career_path',
 '건축사 자격증 취득 경로',
 '[{"name":"target_role","current_value":"미정","simulated_value":"건축설계사","impact_description":"건축설계사 커리어 목표 설정"},{"name":"certification","current_value":"미취득","simulated_value":"건축기사","impact_description":"건축기사 자격증 취득"},{"name":"portfolio","current_value":"없음","simulated_value":"설계 포트폴리오 3건","impact_description":"설계 작품집 구축"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"건축사 자격증 경로 확보로 전문성 강화"},{"metric_name":"설계 역량","current_value":40,"simulated_value":82,"change_percent":105.0,"impact_level":"positive","explanation":"포트폴리오 구축으로 설계 역량 입증"},{"metric_name":"취업 경쟁력","current_value":30,"simulated_value":75,"change_percent":150.0,"impact_level":"positive","explanation":"자격증+포트폴리오로 취업 경쟁력 확보"}]',
 '건축기사 자격증 준비와 설계 포트폴리오 구축을 병행하세요. BIM 역량도 함께 키우면 경쟁력이 높아집니다.'),

-- architecture × skill_development
('architecture', 'skill_development',
 'BIM/CAD 역량 강화 계획',
 '[{"name":"bim_training","current_value":"기초","simulated_value":"고급","impact_description":"BIM 역량 고급 수준 달성"},{"name":"design_practice","current_value":"주 3시간","simulated_value":"주 10시간","impact_description":"설계 실습 시간 대폭 증가"}]',
 '[{"metric_name":"BIM 활용도","current_value":30,"simulated_value":85,"change_percent":183.3,"impact_level":"positive","explanation":"BIM 심화 학습으로 디지털 건축 역량 확보"},{"metric_name":"설계 품질","current_value":40,"simulated_value":80,"change_percent":100.0,"impact_level":"positive","explanation":"집중 실습으로 설계 품질 향상"}]',
 'Revit/ArchiCAD 등 BIM 소프트웨어 심화 학습과 설계 스튜디오 프로젝트에 적극 참여하세요.'),

-- architecture × opportunity
('architecture', 'opportunity',
 '건축 설계 사무소 인턴십',
 '[{"name":"internship","current_value":"미참여","simulated_value":"건축사사무소","impact_description":"건축사사무소 인턴십 참여"},{"name":"competition","current_value":"0회","simulated_value":"2회","impact_description":"건축 설계 공모전 참여"}]',
 '[{"metric_name":"실무 경험","current_value":10,"simulated_value":85,"change_percent":750.0,"impact_level":"positive","explanation":"인턴십으로 실무 설계 경험 확보"},{"metric_name":"포트폴리오","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"공모전 참여로 포트폴리오 강화"}]',
 '건축사사무소 인턴십과 건축 설계 공모전에 적극 참여하세요.'),

-- civil_eng × career_path
('civil_eng', 'career_path',
 '토목기사 취득 및 건설현장 경력',
 '[{"name":"target_role","current_value":"미정","simulated_value":"토목엔지니어","impact_description":"토목 엔지니어 커리어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"토목기사","impact_description":"토목기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":75,"change_percent":150.0,"impact_level":"positive","explanation":"토목기사 자격증으로 전문성 확보"},{"metric_name":"현장 역량","current_value":20,"simulated_value":70,"change_percent":250.0,"impact_level":"positive","explanation":"현장 실습으로 실무 역량 향상"}]',
 '토목기사 자격증 취득과 건설현장 실습 경험을 쌓으세요.'),

-- civil_eng × skill_development
('civil_eng', 'skill_development',
 '구조해석 및 CAD 역량 강화',
 '[{"name":"structural_analysis","current_value":"기초","simulated_value":"고급","impact_description":"구조해석 역량 심화"},{"name":"civil_cad","current_value":"기초","simulated_value":"중급","impact_description":"토목 CAD 역량 향상"}]',
 '[{"metric_name":"구조 해석","current_value":35,"simulated_value":82,"change_percent":134.3,"impact_level":"positive","explanation":"구조역학 심화로 설계 역량 향상"},{"metric_name":"CAD 활용","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"Civil3D 활용 능력 강화"}]',
 '구조해석 심화학습과 Civil3D/AutoCAD 실습을 병행하세요.'),

-- civil_eng × opportunity
('civil_eng', 'opportunity',
 '건설회사 현장실습',
 '[{"name":"field_practice","current_value":"미참여","simulated_value":"건설현장","impact_description":"건설현장 실습 참여"},{"name":"project_experience","current_value":"0건","simulated_value":"2건","impact_description":"설계 프로젝트 참여"}]',
 '[{"metric_name":"현장 경험","current_value":10,"simulated_value":85,"change_percent":750.0,"impact_level":"positive","explanation":"건설현장 실습으로 실무 경험 확보"},{"metric_name":"설계 역량","current_value":25,"simulated_value":78,"change_percent":212.0,"impact_level":"positive","explanation":"프로젝트 참여로 설계 경험 축적"}]',
 '건설회사 현장실습과 토목 설계 프로젝트에 참여하세요.'),

-- mechanical × career_path
('mechanical', 'career_path',
 '기계설계 엔지니어 경력 경로',
 '[{"name":"target_role","current_value":"미정","simulated_value":"기계설계엔지니어","impact_description":"기계설계 엔지니어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"일반기계기사","impact_description":"일반기계기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":32,"simulated_value":76,"change_percent":137.5,"impact_level":"positive","explanation":"기계설계 전문가 경로 확보"},{"metric_name":"기술 역량","current_value":38,"simulated_value":80,"change_percent":110.5,"impact_level":"positive","explanation":"설계/해석 역량 강화"}]',
 '일반기계기사 자격증과 CAD/CAM 실무 역량을 병행하여 준비하세요.'),

-- mechanical × skill_development
('mechanical', 'skill_development',
 'CAD/CAM 및 해석 도구 숙달',
 '[{"name":"cad_level","current_value":"기초","simulated_value":"고급","impact_description":"SolidWorks/CATIA 숙달"},{"name":"simulation_tool","current_value":"미사용","simulated_value":"ANSYS 활용","impact_description":"FEA 해석 도구 활용"}]',
 '[{"metric_name":"설계 도구","current_value":30,"simulated_value":85,"change_percent":183.3,"impact_level":"positive","explanation":"CAD/CAM 도구 숙달로 설계 효율 향상"},{"metric_name":"해석 역량","current_value":20,"simulated_value":75,"change_percent":275.0,"impact_level":"positive","explanation":"구조/열 해석 역량 확보"}]',
 'SolidWorks/CATIA 숙달과 ANSYS 구조해석 학습을 권장합니다.'),

-- mechanical × opportunity
('mechanical', 'opportunity',
 '제조기업 인턴십 경험',
 '[{"name":"internship","current_value":"미참여","simulated_value":"제조기업","impact_description":"제조기업 설계팀 인턴십"},{"name":"capstone","current_value":"미참여","simulated_value":"참여","impact_description":"캡스톤 디자인 참여"}]',
 '[{"metric_name":"실무 경험","current_value":10,"simulated_value":82,"change_percent":720.0,"impact_level":"positive","explanation":"인턴십으로 실무 설계 경험 확보"},{"metric_name":"프로젝트 역량","current_value":25,"simulated_value":80,"change_percent":220.0,"impact_level":"positive","explanation":"캡스톤 프로젝트로 종합 역량 향상"}]',
 '제조기업 설계팀 인턴십과 캡스톤 디자인 프로젝트에 참여하세요.'),

-- electrical × career_path
('electrical', 'career_path',
 '반도체/전자 엔지니어 경력 경로',
 '[{"name":"target_role","current_value":"미정","simulated_value":"반도체엔지니어","impact_description":"반도체 엔지니어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"전자기사","impact_description":"전자기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"반도체/전자 전문가 경로 확보"},{"metric_name":"기술 역량","current_value":35,"simulated_value":82,"change_percent":134.3,"impact_level":"positive","explanation":"전자공학 핵심 역량 강화"}]',
 '전자기사 자격증과 반도체 설계/공정 실무 역량을 키우세요.'),

-- electrical × skill_development
('electrical', 'skill_development',
 '회로설계 및 임베디드 역량 강화',
 '[{"name":"circuit_design","current_value":"기초","simulated_value":"고급","impact_description":"회로설계 역량 심화"},{"name":"embedded","current_value":"미경험","simulated_value":"프로젝트 수행","impact_description":"임베디드 시스템 프로젝트"}]',
 '[{"metric_name":"회로 설계","current_value":35,"simulated_value":85,"change_percent":142.9,"impact_level":"positive","explanation":"회로설계 심화로 전문성 확보"},{"metric_name":"임베디드","current_value":20,"simulated_value":78,"change_percent":290.0,"impact_level":"positive","explanation":"임베디드 프로젝트 경험 확보"}]',
 'PCB 설계 도구(Altium/OrCAD) 학습과 Arduino/STM32 기반 프로젝트를 수행하세요.'),

-- electrical × opportunity
('electrical', 'opportunity',
 '반도체 기업 인턴십',
 '[{"name":"internship","current_value":"미참여","simulated_value":"반도체기업","impact_description":"반도체 기업 인턴십"},{"name":"lab_experience","current_value":"미참여","simulated_value":"연구실","impact_description":"전자공학 연구실 참여"}]',
 '[{"metric_name":"산업 이해","current_value":15,"simulated_value":88,"change_percent":486.7,"impact_level":"positive","explanation":"반도체 기업 인턴십으로 업계 이해도 향상"},{"metric_name":"연구 역량","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"연구실 경험으로 심화 역량 확보"}]',
 '반도체 기업(삼성전자, SK하이닉스 등) 인턴십에 지원하세요.'),

-- chemical_env × career_path
('chemical_env', 'career_path',
 '화학공정/환경 엔지니어 경력 경로',
 '[{"name":"target_role","current_value":"미정","simulated_value":"화학공정엔지니어","impact_description":"화공 엔지니어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"화학분석기사","impact_description":"화학분석기사 자격증"}]',
 '[{"metric_name":"커리어 준비도","current_value":28,"simulated_value":74,"change_percent":164.3,"impact_level":"positive","explanation":"화공/환경 전문가 경로 확보"},{"metric_name":"전문 역량","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"화학공정 전문 역량 강화"}]',
 '화학분석기사/환경기사 자격증과 공정 시뮬레이션 역량을 키우세요.'),

-- chemical_env × skill_development
('chemical_env', 'skill_development',
 '공정 시뮬레이션 역량 강화',
 '[{"name":"process_sim","current_value":"미경험","simulated_value":"ASPEN Plus","impact_description":"공정 시뮬레이션 도구 학습"},{"name":"lab_skill","current_value":"기초","simulated_value":"심화","impact_description":"실험 역량 심화"}]',
 '[{"metric_name":"공정 설계","current_value":30,"simulated_value":82,"change_percent":173.3,"impact_level":"positive","explanation":"시뮬레이션 도구로 공정 설계 역량 확보"},{"metric_name":"실험 역량","current_value":40,"simulated_value":80,"change_percent":100.0,"impact_level":"positive","explanation":"심화 실험으로 분석 역량 향상"}]',
 'ASPEN Plus/HYSYS 등 공정 시뮬레이션 도구 학습과 실험실 심화 실습을 권장합니다.'),

-- chemical_env × opportunity
('chemical_env', 'opportunity',
 '화학/환경 기업 현장실습',
 '[{"name":"internship","current_value":"미참여","simulated_value":"화학기업","impact_description":"화학/에너지 기업 인턴십"},{"name":"research","current_value":"미참여","simulated_value":"연구실","impact_description":"화공 연구실 참여"}]',
 '[{"metric_name":"산업 이해","current_value":15,"simulated_value":85,"change_percent":466.7,"impact_level":"positive","explanation":"화학기업 인턴십으로 산업 현장 이해"},{"metric_name":"연구 역량","current_value":25,"simulated_value":80,"change_percent":220.0,"impact_level":"positive","explanation":"연구실 경험으로 연구 역량 강화"}]',
 '화학/에너지/환경 기업 인턴십과 연구실 프로젝트에 참여하세요.'),

-- industrial × career_path
('industrial', 'career_path',
 '산업엔지니어/품질관리 경력 경로',
 '[{"name":"target_role","current_value":"미정","simulated_value":"산업엔지니어","impact_description":"산업공학 전문가 목표"},{"name":"certification","current_value":"미취득","simulated_value":"품질경영기사","impact_description":"품질경영기사 자격증"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":76,"change_percent":153.3,"impact_level":"positive","explanation":"산업공학 전문가 경로 확보"},{"metric_name":"관리 역량","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"생산/품질 관리 역량 강화"}]',
 '품질경영기사/산업안전기사 자격증과 데이터 분석 역량을 키우세요.'),

-- industrial × skill_development
('industrial', 'skill_development',
 '생산최적화 및 데이터 분석 역량',
 '[{"name":"optimization","current_value":"기초","simulated_value":"고급","impact_description":"최적화 기법 심화"},{"name":"data_tool","current_value":"미경험","simulated_value":"Python/R","impact_description":"데이터 분석 도구 학습"}]',
 '[{"metric_name":"최적화 역량","current_value":30,"simulated_value":83,"change_percent":176.7,"impact_level":"positive","explanation":"최적화 기법 심화로 문제해결 역량 향상"},{"metric_name":"데이터 분석","current_value":25,"simulated_value":78,"change_percent":212.0,"impact_level":"positive","explanation":"데이터 분석으로 의사결정 역량 강화"}]',
 '최적화 알고리즘 심화학습과 Python/R 기반 데이터 분석을 병행하세요.'),

-- industrial × opportunity
('industrial', 'opportunity',
 '제조/물류 기업 현장실습',
 '[{"name":"internship","current_value":"미참여","simulated_value":"제조기업","impact_description":"제조/물류 기업 인턴십"},{"name":"project","current_value":"미참여","simulated_value":"개선 프로젝트","impact_description":"현장 개선 프로젝트 참여"}]',
 '[{"metric_name":"실무 경험","current_value":10,"simulated_value":85,"change_percent":750.0,"impact_level":"positive","explanation":"인턴십으로 생산현장 실무 경험 확보"},{"metric_name":"문제해결","current_value":30,"simulated_value":80,"change_percent":166.7,"impact_level":"positive","explanation":"현장 개선 프로젝트로 문제해결 역량 향상"}]',
 '제조/물류 기업 현장실습과 공정 개선 프로젝트에 참여하세요.');

-- 3-3: 시뮬레이션 삽입 (세분화 카테고리 학생 전체)
INSERT INTO tb_simulation_scenario (
    scenario_id, student_id, scenario_name, scenario_type,
    base_state, predicted_outcomes,
    recommendation_score, status,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    sc.scenario_name,
    sc.scenario_type,
    jsonb_build_object('variables', sc.variables_json::jsonb),
    jsonb_build_object(
        'results', sc.results_json::jsonb,
        'recommendation', sc.recommendation,
        'ai_analysis', null
    ),
    60 + abs(hashtext(ts.student_id || sc.scenario_type)) % 30,
    CASE WHEN ts.admission_year <= 2021 THEN 'completed' ELSE 'active' END,
    'FIX_47',
    NOW()
FROM tmp_all_students_47 ts
JOIN tmp_sim_scenarios_47 sc ON ts.category = sc.category
WHERE NOT EXISTS (
    SELECT 1 FROM tb_simulation_scenario ss
    WHERE ss.student_id = ts.student_id AND ss.scenario_type = sc.scenario_type
      AND ss.ins_user_id = 'FIX_47'
);

DROP TABLE IF EXISTS tmp_sim_scenarios_47;

DO $$ BEGIN RAISE NOTICE 'Part 3 완료: 카테고리별 시뮬레이션 삽입'; END $$;


-- =====================================================
-- Part 4: 포트폴리오 수정 (tb_portfolio)
-- 비IT 공학 카테고리 학생의 포트폴리오를 전공 맞춤으로 UPDATE
-- =====================================================

-- 4-1: 포트폴리오 항목 temp table
CREATE TEMP TABLE tmp_portfolio_fix_47 (
    category VARCHAR(20),
    item_type VARCHAR(50),
    artifact_type VARCHAR(50),
    title_suffix VARCHAR(200),
    description TEXT,
    skills_json TEXT,
    display_order INT
);

INSERT INTO tmp_portfolio_fix_47 VALUES
    -- architecture
    ('architecture','certificate','certification','건축기사 자격증','건축 설계 및 시공 전문 자격 인증','["건축설계","건축법규","건축시공"]',1),
    ('architecture','project','project','졸업 설계 프로젝트','건축 졸업설계 작품 프로젝트','["건축설계","CAD/BIM","3D모델링"]',2),
    ('architecture','activity','experience','건축 설계 사무소 실습','건축사사무소 설계 실무 실습','["건축설계","BIM","도면작성"]',3),
    ('architecture','award','award','건축 설계 공모전 수상','전국 대학생 건축 설계 공모전 수상','["건축설계","창의력","3D모델링"]',4),
    -- civil_eng
    ('civil_eng','certificate','certification','토목기사 자격증','토목공학 전문 자격 인증','["구조역학","토질역학","시공관리"]',1),
    ('civil_eng','project','project','구조물 설계 프로젝트','교량/터널 등 구조물 설계 프로젝트','["구조역학","토목CAD","시공관리"]',2),
    ('civil_eng','activity','experience','건설현장 실습','건설회사 현장 실습 경험','["시공관리","측량학","현장관리"]',3),
    ('civil_eng','award','award','토목 설계 공모전 수상','대학생 토목구조물 설계 공모전 수상','["구조역학","창의설계","팀워크"]',4),
    -- mechanical
    ('mechanical','certificate','certification','일반기계기사 자격증','기계공학 전문 자격 인증','["열역학","기계설계","재료역학"]',1),
    ('mechanical','project','project','캡스톤 기계설계 프로젝트','기계장치 설계 및 제작 프로젝트','["기계설계","CAD/CAM","제어공학"]',2),
    ('mechanical','activity','experience','제조기업 설계팀 인턴십','제조기업 설계팀 실무 인턴십','["기계설계","SolidWorks","도면작성"]',3),
    ('mechanical','award','award','기계설계 경진대회 수상','전국 대학생 기계설계 경진대회 수상','["기계설계","창의력","팀워크"]',4),
    -- electrical
    ('electrical','certificate','certification','전자기사 자격증','전자공학 전문 자격 인증','["회로이론","전자기학","디지털시스템"]',1),
    ('electrical','project','project','임베디드 시스템 프로젝트','임베디드 시스템 설계 및 구현 프로젝트','["임베디드","회로설계","PCB설계"]',2),
    ('electrical','activity','experience','반도체/전자 기업 인턴십','반도체/전자 기업 실무 인턴십','["반도체","회로이론","클린룸"]',3),
    ('electrical','award','award','전자회로 설계 대회 수상','대학생 전자회로 설계 경진대회 수상','["회로설계","디지털시스템","문제해결"]',4),
    -- chemical_env
    ('chemical_env','certificate','certification','화학분석기사 자격증','화학공학/환경 전문 자격 인증','["화학공정","반응공학","환경영향평가"]',1),
    ('chemical_env','project','project','공정설계 프로젝트','화학 공정 설계 및 시뮬레이션 프로젝트','["화학공정","반응공학","열전달"]',2),
    ('chemical_env','activity','experience','화학/에너지 기업 실습','화학/에너지 기업 현장 실습','["화학공정","공정운전","안전관리"]',3),
    ('chemical_env','award','award','화학공학 학술 발표상','화학공학 학술대회 우수 발표상','["화학공정","연구발표","데이터분석"]',4),
    -- industrial
    ('industrial','certificate','certification','품질경영기사 자격증','품질관리 및 산업공학 자격 인증','["품질관리","생산관리","통계분석"]',1),
    ('industrial','project','project','공정 최적화 프로젝트','생산공정 최적화 및 개선 프로젝트','["생산관리","최적화","데이터분석"]',2),
    ('industrial','activity','experience','제조기업 생산관리 실습','제조기업 생산관리팀 실습','["생산관리","품질관리","공급망관리"]',3),
    ('industrial','award','award','산업공학 경진대회 수상','대학생 산업공학 경진대회 수상','["최적화","문제해결","팀워크"]',4);

-- 4-2: 기존 잘못된 포트폴리오 삭제 (비IT 공학 카테고리)
DELETE FROM tb_portfolio p
USING tmp_all_students_47 ts
WHERE p.student_id = ts.student_id
  AND ts.category IN ('architecture','civil_eng','mechanical','electrical','chemical_env','industrial')
  AND p.ins_user_id IN ('SEED_46','BULK_FIX');

-- 4-3: 올바른 포트폴리오 삽입
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
    pf.item_type,
    ts.student_nm || ' - ' || pf.title_suffix,
    pf.description,
    -- start_date
    ((ts.admission_year + 1)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || pf.item_type || 's')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || pf.item_type || 'sd')) % 28 + 1)::text, 2, '0'))::date,
    -- end_date
    ((ts.admission_year + 2 + abs(hashtext(ts.student_id || pf.item_type || 'ey')) % 2)::text || '-' ||
     LPAD((abs(hashtext(ts.student_id || pf.item_type || 'em')) % 12 + 1)::text, 2, '0') || '-' ||
     LPAD((abs(hashtext(ts.student_id || pf.item_type || 'ed')) % 28 + 1)::text, 2, '0'))::date,
    pf.skills_json::jsonb,
    'https://portfolio.inje.ac.kr/' || ts.student_id || '/' || pf.item_type,
    NULL,
    CASE WHEN pf.display_order = 1 THEN 'Y' ELSE 'N' END,
    pf.display_order,
    'FIX_47',
    NOW(),
    pf.artifact_type,
    'https://portfolio.inje.ac.kr/' || ts.student_id || '/' || pf.artifact_type,
    CASE WHEN pf.display_order = 1 THEN true ELSE false END
FROM tmp_all_students_47 ts
JOIN tmp_portfolio_fix_47 pf ON ts.category = pf.category;

DROP TABLE IF EXISTS tmp_portfolio_fix_47;

DO $$ BEGIN RAISE NOTICE 'Part 4 완료: 포트폴리오 수정'; END $$;


-- =====================================================
-- Part 5: 갭분석 생성 (tb_skill_gap_analysis)
-- 전 카테고리 학생에 2건씩 (주 목표 role + 보조 role)
-- =====================================================

-- 5-1: 기존 잘못된 갭분석 삭제 (비IT 공학 카테고리에 IT role 매핑된 것)
DELETE FROM tb_skill_gap_analysis sga
USING tmp_all_students_47 ts
WHERE sga.student_id = ts.student_id
  AND ts.category IN ('architecture','civil_eng','mechanical','electrical','chemical_env','industrial')
  AND sga.target_role_cd IN ('ROLE01','ROLE02','ROLE03','ROLE04','ROLE05','ROLE06','ROLE07','ROLE08');

-- 5-2: 카테고리별 gap analysis 매핑 temp table
CREATE TEMP TABLE tmp_gap_roles_47 (
    category VARCHAR(20),
    role_cd VARCHAR(20),
    role_order INT,  -- 1=주 목표, 2=보조
    base_gap_score NUMERIC(5,2),
    gap_details_json TEXT,
    priority_skills TEXT[],
    actions_json TEXT
);

INSERT INTO tmp_gap_roles_47 VALUES
-- medical
('medical', 'ROLE101', 1, 35.0,
 '[{"skill_cd":"SKM001","current":3,"required":5,"gap":2},{"skill_cd":"SKM004","current":2,"required":5,"gap":3},{"skill_cd":"SKM007","current":3,"required":4,"gap":1}]',
 ARRAY['SKM001','SKM004','SKM007'],
 '{"courses":["MD101","MD201"],"programs":["PGM_MED01"],"activities":["임상실습 참여","의학 학술대회 발표"]}'),
('medical', 'ROLE103', 2, 42.0,
 '[{"skill_cd":"SKM001","current":3,"required":4,"gap":1},{"skill_cd":"SKM003","current":3,"required":4,"gap":1},{"skill_cd":"SKM006","current":2,"required":4,"gap":2}]',
 ARRAY['SKM006','SKM001','SKM003'],
 '{"courses":["MD102","MD301"],"programs":["PGM_MED02"],"activities":["의료 봉사활동","연구 프로젝트 참여"]}'),

-- nursing
('nursing', 'ROLE102', 1, 38.0,
 '[{"skill_cd":"SKN001","current":3,"required":5,"gap":2},{"skill_cd":"SKN002","current":2,"required":5,"gap":3},{"skill_cd":"SKN007","current":3,"required":4,"gap":1}]',
 ARRAY['SKN002','SKN001','SKN007'],
 '{"courses":["NR201","NR301"],"programs":["PGM_NR01"],"activities":["병원 임상실습","BLS/ACLS 자격 취득"]}'),
('nursing', 'ROLE106', 2, 45.0,
 '[{"skill_cd":"SKN003","current":3,"required":4,"gap":1},{"skill_cd":"SKN004","current":2,"required":4,"gap":2},{"skill_cd":"SKN005","current":2,"required":4,"gap":2}]',
 ARRAY['SKN004','SKN005','SKN003'],
 '{"courses":["NR202","NR302"],"programs":["PGM_NR02"],"activities":["전문간호사 과정 탐색","간호 질 향상 프로젝트"]}'),

-- pharmacy
('pharmacy', 'ROLE105', 1, 36.0,
 '[{"skill_cd":"SKP001","current":3,"required":5,"gap":2},{"skill_cd":"SKP007","current":2,"required":5,"gap":3},{"skill_cd":"SKP003","current":3,"required":4,"gap":1}]',
 ARRAY['SKP007','SKP001','SKP003'],
 '{"courses":["PH301","PH401"],"programs":["PGM_PH01"],"activities":["약국 실무실습","약사 국가시험 준비"]}'),
('pharmacy', 'ROLE105', 2, 40.0,
 '[{"skill_cd":"SKP002","current":3,"required":4,"gap":1},{"skill_cd":"SKP004","current":2,"required":4,"gap":2},{"skill_cd":"SKP006","current":3,"required":4,"gap":1}]',
 ARRAY['SKP004','SKP002','SKP006'],
 '{"courses":["PH302","PH402"],"programs":["PGM_PH02"],"activities":["제약회사 인턴십","신약 연구 참여"]}'),

-- health
('health', 'ROLE103', 1, 40.0,
 '[{"skill_cd":"SKH001","current":3,"required":5,"gap":2},{"skill_cd":"SKH004","current":2,"required":4,"gap":2},{"skill_cd":"SKH007","current":3,"required":4,"gap":1}]',
 ARRAY['SKH001','SKH004','SKH007'],
 '{"courses":["HE201","HE301"],"programs":["PGM_HE01"],"activities":["보건소 현장실습","보건의료정보관리사 취득"]}'),
('health', 'ROLE106', 2, 44.0,
 '[{"skill_cd":"SKH002","current":3,"required":4,"gap":1},{"skill_cd":"SKH003","current":2,"required":4,"gap":2},{"skill_cd":"SKH006","current":3,"required":4,"gap":1}]',
 ARRAY['SKH003','SKH002','SKH006'],
 '{"courses":["HE202","HE302"],"programs":["PGM_HE02"],"activities":["건강증진 프로그램 기획","의료기관 인턴십"]}'),

-- it_engineering
('it_engineering', 'ROLE01', 1, 32.0,
 '[{"skill_cd":"SKE001","current":3,"required":5,"gap":2},{"skill_cd":"SKE003","current":3,"required":5,"gap":2},{"skill_cd":"SKE007","current":2,"required":4,"gap":2}]',
 ARRAY['SKE001','SKE003','SKE007'],
 '{"courses":["CS401","CS301"],"programs":["PGM006"],"activities":["AWS 자격증 취득","오픈소스 프로젝트 기여"]}'),
('it_engineering', 'ROLE02', 2, 38.0,
 '[{"skill_cd":"SKE001","current":3,"required":4,"gap":1},{"skill_cd":"SKE004","current":2,"required":4,"gap":2},{"skill_cd":"SKE005","current":2,"required":4,"gap":2}]',
 ARRAY['SKE004','SKE005','SKE001'],
 '{"courses":["CS301","CS302"],"programs":["PGM005"],"activities":["알고리즘 대회 참여","개인 프로젝트 포트폴리오"]}'),

-- architecture
('architecture', 'ROLE231', 1, 38.0,
 '[{"skill_cd":"SKAR001","current":3,"required":5,"gap":2},{"skill_cd":"SKAR002","current":2,"required":5,"gap":3},{"skill_cd":"SKAR003","current":3,"required":4,"gap":1}]',
 ARRAY['SKAR002','SKAR001','SKAR003'],
 '{"courses":["AR301","AR401"],"programs":["PGM_AR01"],"activities":["건축사사무소 실습","건축 설계 공모전 참여"]}'),
('architecture', 'ROLE232', 2, 42.0,
 '[{"skill_cd":"SKAR004","current":2,"required":5,"gap":3},{"skill_cd":"SKAR005","current":2,"required":5,"gap":3},{"skill_cd":"SKAR003","current":3,"required":4,"gap":1}]',
 ARRAY['SKAR004','SKAR005','SKAR003'],
 '{"courses":["AR302","AR402"],"programs":["PGM_AR02"],"activities":["건설현장 실습","건축기사 자격증 취득"]}'),

-- civil_eng
('civil_eng', 'ROLE233', 1, 40.0,
 '[{"skill_cd":"SKCV001","current":3,"required":5,"gap":2},{"skill_cd":"SKCV003","current":2,"required":5,"gap":3},{"skill_cd":"SKCV007","current":2,"required":4,"gap":2}]',
 ARRAY['SKCV003','SKCV001','SKCV007'],
 '{"courses":["CE301","CE401"],"programs":["PGM_CE01"],"activities":["건설현장 실습","토목기사 자격증 취득"]}'),
('civil_eng', 'ROLE234', 2, 44.0,
 '[{"skill_cd":"SKCV004","current":3,"required":4,"gap":1},{"skill_cd":"SKCV006","current":2,"required":5,"gap":3},{"skill_cd":"SKCV005","current":2,"required":3,"gap":1}]',
 ARRAY['SKCV006','SKCV004','SKCV005'],
 '{"courses":["CE302","CE402"],"programs":["PGM_CE02"],"activities":["측량실습","건설기술인 교육 참여"]}'),

-- mechanical
('mechanical', 'ROLE235', 1, 36.0,
 '[{"skill_cd":"SKME003","current":3,"required":5,"gap":2},{"skill_cd":"SKME004","current":2,"required":5,"gap":3},{"skill_cd":"SKME005","current":2,"required":5,"gap":3}]',
 ARRAY['SKME004','SKME005','SKME003'],
 '{"courses":["ME301","ME401"],"programs":["PGM_ME01"],"activities":["CAD/CAM 실습","일반기계기사 취득"]}'),
('mechanical', 'ROLE236', 2, 42.0,
 '[{"skill_cd":"SKME001","current":3,"required":5,"gap":2},{"skill_cd":"SKME006","current":2,"required":5,"gap":3},{"skill_cd":"SKME007","current":2,"required":4,"gap":2}]',
 ARRAY['SKME006','SKME001','SKME007'],
 '{"courses":["ME302","ME402"],"programs":["PGM_ME02"],"activities":["자동차기업 인턴십","제어시스템 프로젝트"]}'),

-- electrical
('electrical', 'ROLE237', 1, 38.0,
 '[{"skill_cd":"SKEL001","current":3,"required":5,"gap":2},{"skill_cd":"SKEL005","current":2,"required":5,"gap":3},{"skill_cd":"SKEL007","current":2,"required":5,"gap":3}]',
 ARRAY['SKEL005','SKEL001','SKEL007'],
 '{"courses":["EE301","EE401"],"programs":["PGM_EE01"],"activities":["PCB 설계 실습","전자기사 자격증 취득"]}'),
('electrical', 'ROLE238', 2, 44.0,
 '[{"skill_cd":"SKEL004","current":2,"required":5,"gap":3},{"skill_cd":"SKEL002","current":3,"required":4,"gap":1},{"skill_cd":"SKEL006","current":2,"required":4,"gap":2}]',
 ARRAY['SKEL004','SKEL006','SKEL002'],
 '{"courses":["EE302","EE402"],"programs":["PGM_EE02"],"activities":["반도체 기업 인턴십","클린룸 실습"]}'),

-- chemical_env
('chemical_env', 'ROLE239', 1, 40.0,
 '[{"skill_cd":"SKCE001","current":3,"required":5,"gap":2},{"skill_cd":"SKCE002","current":2,"required":5,"gap":3},{"skill_cd":"SKCE003","current":3,"required":4,"gap":1}]',
 ARRAY['SKCE002','SKCE001','SKCE003'],
 '{"courses":["CH301","CH401"],"programs":["PGM_CH01"],"activities":["화학기업 현장실습","화학분석기사 취득"]}'),
('chemical_env', 'ROLE240', 2, 44.0,
 '[{"skill_cd":"SKCE004","current":2,"required":5,"gap":3},{"skill_cd":"SKCE005","current":2,"required":5,"gap":3},{"skill_cd":"SKCE006","current":3,"required":5,"gap":2}]',
 ARRAY['SKCE004','SKCE005','SKCE006'],
 '{"courses":["CH302","EN401"],"programs":["PGM_EN01"],"activities":["환경기사 자격증 취득","환경영향평가 프로젝트"]}'),

-- industrial
('industrial', 'ROLE261', 1, 36.0,
 '[{"skill_cd":"SKIN001","current":3,"required":5,"gap":2},{"skill_cd":"SKIN004","current":2,"required":5,"gap":3},{"skill_cd":"SKIN005","current":2,"required":4,"gap":2}]',
 ARRAY['SKIN004','SKIN001','SKIN005'],
 '{"courses":["IE301","IE401"],"programs":["PGM_IE01"],"activities":["제조기업 인턴십","품질경영기사 취득"]}'),
('industrial', 'ROLE262', 2, 40.0,
 '[{"skill_cd":"SKIN002","current":3,"required":5,"gap":2},{"skill_cd":"SKIN003","current":2,"required":4,"gap":2},{"skill_cd":"SKIN006","current":3,"required":4,"gap":1}]',
 ARRAY['SKIN002','SKIN003','SKIN006'],
 '{"courses":["IE302","IE402"],"programs":["PGM_IE02"],"activities":["6시그마 교육","생산현장 개선 프로젝트"]}'),

-- business
('business', 'ROLE09', 1, 34.0,
 '[{"skill_cd":"SKB001","current":3,"required":5,"gap":2},{"skill_cd":"SKB003","current":2,"required":4,"gap":2},{"skill_cd":"SKB005","current":3,"required":4,"gap":1}]',
 ARRAY['SKB001','SKB003','SKB005'],
 '{"courses":["BA301","BA401"],"programs":["PGM_BA01"],"activities":["CPA/경영지도사 준비","기업 인턴십"]}'),
('business', 'ROLE12', 2, 40.0,
 '[{"skill_cd":"SKB002","current":3,"required":5,"gap":2},{"skill_cd":"SKB005","current":3,"required":4,"gap":1},{"skill_cd":"SKB007","current":2,"required":4,"gap":2}]',
 ARRAY['SKB002','SKB005','SKB007'],
 '{"courses":["BA302","MK401"],"programs":["PGM_BA02"],"activities":["마케팅 공모전 참여","데이터분석 자격증 취득"]}'),

-- law_admin
('law_admin', 'ROLE201', 1, 42.0,
 '[{"skill_cd":"SKL001","current":3,"required":5,"gap":2},{"skill_cd":"SKL002","current":2,"required":5,"gap":3},{"skill_cd":"SKL006","current":3,"required":4,"gap":1}]',
 ARRAY['SKL002','SKL001','SKL006'],
 '{"courses":["LW301","LW401"],"programs":["PGM_LW01"],"activities":["법학적성시험 준비","모의재판 참여"]}'),
('law_admin', 'ROLE264', 2, 38.0,
 '[{"skill_cd":"SKL003","current":3,"required":5,"gap":2},{"skill_cd":"SKL005","current":3,"required":4,"gap":1},{"skill_cd":"SKL007","current":2,"required":4,"gap":2}]',
 ARRAY['SKL003','SKL005','SKL007'],
 '{"courses":["PA301","PA401"],"programs":["PGM_PA01"],"activities":["행정사 자격증 준비","공공기관 인턴십"]}'),

-- education
('education', 'ROLE221', 1, 36.0,
 '[{"skill_cd":"SKD001","current":3,"required":5,"gap":2},{"skill_cd":"SKD002","current":2,"required":5,"gap":3},{"skill_cd":"SKD006","current":3,"required":4,"gap":1}]',
 ARRAY['SKD002','SKD001','SKD006'],
 '{"courses":["ED301","ED401"],"programs":["PGM_ED01"],"activities":["교원임용시험 준비","교생실습"]}'),
('education', 'ROLE253', 2, 40.0,
 '[{"skill_cd":"SKD003","current":3,"required":4,"gap":1},{"skill_cd":"SKD005","current":2,"required":4,"gap":2},{"skill_cd":"SKD004","current":3,"required":4,"gap":1}]',
 ARRAY['SKD005','SKD003','SKD004'],
 '{"courses":["ED302","ED402"],"programs":["PGM_ED02"],"activities":["상담교육 실습","교육봉사활동"]}'),

-- humanities
('humanities', 'ROLE241', 1, 40.0,
 '[{"skill_cd":"SKU001","current":3,"required":5,"gap":2},{"skill_cd":"SKU004","current":2,"required":4,"gap":2},{"skill_cd":"SKU003","current":3,"required":5,"gap":2}]',
 ARRAY['SKU001','SKU003','SKU004'],
 '{"courses":["HM301","HM401"],"programs":["PGM_HM01"],"activities":["대학원 진학 준비","어학 자격증 취득"]}'),
('humanities', 'ROLE242', 2, 44.0,
 '[{"skill_cd":"SKU002","current":3,"required":4,"gap":1},{"skill_cd":"SKU005","current":2,"required":4,"gap":2},{"skill_cd":"SKU006","current":3,"required":4,"gap":1}]',
 ARRAY['SKU005','SKU002','SKU006'],
 '{"courses":["HM302","HM402"],"programs":["PGM_HM02"],"activities":["출판사 인턴십","문화콘텐츠 기획"]}'),

-- arts
('arts', 'ROLE304', 1, 38.0,
 '[{"skill_cd":"SKA001","current":3,"required":4,"gap":1},{"skill_cd":"SKA005","current":2,"required":5,"gap":3},{"skill_cd":"SKA003","current":3,"required":4,"gap":1}]',
 ARRAY['SKA005','SKA001','SKA003'],
 '{"courses":["AR301","AR401"],"programs":["PGM_ART01"],"activities":["공연/전시 기획","포트폴리오 구축"]}'),
('arts', 'ROLE301', 2, 42.0,
 '[{"skill_cd":"SKA002","current":3,"required":5,"gap":2},{"skill_cd":"SKA006","current":2,"required":4,"gap":2},{"skill_cd":"SKA007","current":3,"required":5,"gap":2}]',
 ARRAY['SKA002','SKA006','SKA007'],
 '{"courses":["DS301","DS401"],"programs":["PGM_ART02"],"activities":["디자인 공모전 참여","스튜디오 인턴십"]}'),

-- science
('science', 'ROLE501', 1, 38.0,
 '[{"skill_cd":"SKS001","current":3,"required":5,"gap":2},{"skill_cd":"SKS003","current":2,"required":5,"gap":3},{"skill_cd":"SKS004","current":3,"required":4,"gap":1}]',
 ARRAY['SKS003','SKS001','SKS004'],
 '{"courses":["SC301","SC401"],"programs":["PGM_SC01"],"activities":["연구실 인턴","학술대회 발표"]}'),
('science', 'ROLE504', 2, 42.0,
 '[{"skill_cd":"SKS005","current":3,"required":4,"gap":1},{"skill_cd":"SKS006","current":2,"required":4,"gap":2},{"skill_cd":"SKS007","current":3,"required":4,"gap":1}]',
 ARRAY['SKS006','SKS005','SKS007'],
 '{"courses":["SC302","SC402"],"programs":["PGM_SC02"],"activities":["대학원 진학 준비","논문 공동저자 참여"]}'),

-- general
('general', 'ROLE401', 1, 44.0,
 '[{"skill_cd":"SKG001","current":3,"required":4,"gap":1},{"skill_cd":"SKG004","current":2,"required":4,"gap":2},{"skill_cd":"SKG005","current":3,"required":4,"gap":1}]',
 ARRAY['SKG004','SKG001','SKG005'],
 '{"courses":["GE301","GE401"],"programs":["PGM_GE01"],"activities":["진로 탐색 프로그램","소프트스킬 워크숍"]}'),
('general', 'ROLE403', 2, 48.0,
 '[{"skill_cd":"SKG002","current":2,"required":4,"gap":2},{"skill_cd":"SKG003","current":3,"required":4,"gap":1},{"skill_cd":"SKG006","current":2,"required":4,"gap":2}]',
 ARRAY['SKG002','SKG006','SKG003'],
 '{"courses":["GE302","GE402"],"programs":["PGM_GE02"],"activities":["교환학생 프로그램","리더십 캠프 참여"]}');

-- 5-3: 기존 잘못된 갭분석 전체 삭제 후 재생성 (데이터가 거의 없으므로)
-- 기존 3건 보존 없이 깨끗하게 재생성
DELETE FROM tb_skill_gap_analysis;

-- 5-4: 전 카테고리 학생에 2건씩 갭분석 삽입
INSERT INTO tb_skill_gap_analysis (
    analysis_id, student_id, target_role_cd,
    analysis_date, overall_gap_score,
    gap_details, top_priority_skills, recommended_actions,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    gr.role_cd,
    -- analysis_date: 최근 3개월 이내
    NOW() - ((abs(hashtext(ts.student_id || gr.role_cd)) % 90) || ' days')::interval,
    -- overall_gap_score: base + 학년 보정 + 개인 변동
    LEAST(80.0, GREATEST(15.0,
        gr.base_gap_score
        - (ts.current_grade * 3)::numeric  -- 고학년일수록 갭 줄어듦
        + (abs(hashtext(ts.student_id || gr.role_cd || 'g')) % 15)::numeric
    )),
    gr.gap_details_json::jsonb,
    gr.priority_skills,
    gr.actions_json::jsonb,
    'FIX_47',
    NOW()
FROM tmp_all_students_47 ts
JOIN tmp_gap_roles_47 gr ON ts.category = gr.category;

DROP TABLE IF EXISTS tmp_gap_roles_47;

DO $$ BEGIN RAISE NOTICE 'Part 5 완료: 갭분석 생성 (학생당 2건)'; END $$;


-- =====================================================
-- Cleanup
-- =====================================================

DROP TABLE IF EXISTS tmp_cat_skills_47;
DROP TABLE IF EXISTS tmp_all_students_47;
DROP TABLE IF EXISTS tmp_dept_cat_47;

COMMIT;

-- =====================================================
-- 검증 쿼리 (수동 실행)
-- =====================================================

-- 1. 카테고리별 학생 수 확인
-- SELECT category, count(*) FROM tmp_dept_cat_47 dc JOIN tb_student s ON s.department_cd = dc.department_cd GROUP BY category ORDER BY category;

-- 2. 건축학과 학생 스킬 확인 (IT 스킬 없어야 함)
-- SELECT d.department_nm, sk.skill_nm FROM tb_student_skill ss
-- JOIN tb_student s ON ss.student_id = s.student_id
-- JOIN tb_department d ON s.department_cd = d.department_cd
-- JOIN tb_skill sk ON ss.skill_cd = sk.skill_cd
-- WHERE d.department_nm ~ '건축' LIMIT 20;

-- 3. 시뮬레이션: 비IT 학과에 IT 시나리오가 없는지
-- SELECT d.department_nm, ss.scenario_name FROM tb_simulation_scenario ss
-- JOIN tb_student s ON ss.student_id = s.student_id
-- JOIN tb_department d ON s.department_cd = d.department_cd
-- WHERE d.department_nm ~ '건축' AND ss.ins_user_id = 'FIX_47';

-- 4. 포트폴리오: 건축학과에 프로그래밍 포트폴리오가 없는지
-- SELECT p.title FROM tb_portfolio p
-- JOIN tb_student s ON p.student_id = s.student_id
-- JOIN tb_department d ON s.department_cd = d.department_cd
-- WHERE d.department_nm ~ '건축' AND p.title NOT LIKE '%건축%';

-- 5. 갭분석: 카테고리별 적절한 role
-- SELECT d.department_nm, sga.target_role_cd, r.role_nm, sga.overall_gap_score
-- FROM tb_skill_gap_analysis sga
-- JOIN tb_student s ON sga.student_id = s.student_id
-- JOIN tb_department d ON s.department_cd = d.department_cd
-- JOIN tb_role r ON sga.target_role_cd = r.role_cd
-- WHERE d.department_nm ~ '건축'
-- LIMIT 10;

-- 6. 전체 갭분석 건수 확인
-- SELECT count(*) FROM tb_skill_gap_analysis WHERE ins_user_id = 'FIX_47';
