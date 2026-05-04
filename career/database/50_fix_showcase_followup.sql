-- =====================================================
-- 50_fix_showcase_followup.sql
-- 쇼케이스 데이터 3건 후속 수정
--
-- 문제 1: FIX_49 시뮬레이션 시나리오 JSONB flat → 구조화
-- 문제 2: system 시드 coaching_goal "Career Goal NNN" 전체 삭제
-- 문제 3: 쇼케이스 40명 active 위험 알림 부재 → 학과별 INSERT
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 대상 학생 및 학과-카테고리 매핑
-- =====================================================

CREATE TEMP TABLE tmp_dept_cat_50 AS
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

CREATE TEMP TABLE tmp_showcase_50 AS
SELECT
    s.student_id,
    s.department_cd,
    dc.category,
    dc.department_nm,
    abs(hashtext(s.student_id)) % 100 AS h
FROM tb_student s
JOIN tmp_dept_cat_50 dc ON s.department_cd = dc.department_cd
WHERE s.student_id IN (
    '2021A143', '20203008', '20203033', '20201861', '20202956', '20201481', '20202999', '20201478',
    '20201499', '20201333', '20201341', '20202487', '20202493', '20202510', '20214632', '2020A066',
    '2021A060', '2021A056', '2021A146', '20214314', '20214364', '20202733', '20202883', '20202887',
    '20202924', '20202333', '20201265', '20214819', '20201126', '20201132', '20202358', '20202362',
    '20202364', '20202379', '20202722', '20214353', '20201220', '20214383', '20201352', '20201882'
);

CREATE INDEX idx_tmp_showcase_50_sid ON tmp_showcase_50(student_id);
CREATE INDEX idx_tmp_showcase_50_cat ON tmp_showcase_50(category);

DO $$ BEGIN
    RAISE NOTICE 'Part 0: 쇼케이스 학생 % 명', (SELECT count(*) FROM tmp_showcase_50);
END $$;


-- =====================================================
-- Part 1: FIX_49 시뮬레이션 시나리오 JSONB 구조화
-- base_state → {"variables": [...]}
-- predicted_outcomes → {"results": [...], "recommendation": "...", "ai_analysis": null}
-- =====================================================

-- FIX_44 패턴과 동일한 구조의 변환 매핑 테이블
-- FIX_49의 세분화 카테고리(it_engineering, electrical, mechanical, architecture, etc.) 포함
CREATE TEMP TABLE tmp_sim_transform_50 (
    category VARCHAR(20),
    scenario_type VARCHAR(30),
    variables_json TEXT,
    results_json TEXT,
    recommendation TEXT
);

INSERT INTO tmp_sim_transform_50 VALUES
-- medical × skill_development
('medical', 'skill_development',
 '[{"name":"study_hours","current_value":"10","simulated_value":"20","impact_description":"주간 학습 시간 증가"},{"name":"study_group","current_value":"미참여","simulated_value":"참여","impact_description":"스터디 그룹 참여"}]',
 '[{"metric_name":"기초의학 이해도","current_value":50,"simulated_value":85,"change_percent":70.0,"impact_level":"positive","explanation":"심화 학습으로 기초의학 역량 크게 향상"},{"metric_name":"시험 준비도","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"체계적 학습으로 시험 대비 강화"}]',
 '기초의학 과목 스터디 그룹 참여와 주간 학습 시간 확대를 권장합니다.'),

-- medical × career_path
('medical', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"의사","impact_description":"의사 커리어 목표 설정"},{"name":"gpa_target","current_value":"3.5","simulated_value":"4.0","impact_description":"GPA 목표 상향"},{"name":"clinical_hours","current_value":"0","simulated_value":"500","impact_description":"임상실습 시간 확보"}]',
 '[{"metric_name":"커리어 준비도","current_value":45,"simulated_value":75,"change_percent":66.7,"impact_level":"positive","explanation":"의사 국가시험 준비 경로 확보"},{"metric_name":"임상 경험","current_value":10,"simulated_value":60,"change_percent":500.0,"impact_level":"positive","explanation":"임상실습으로 실무 역량 대폭 향상"},{"metric_name":"학업 성취","current_value":70,"simulated_value":85,"change_percent":21.4,"impact_level":"positive","explanation":"GPA 향상으로 본과 진학 경쟁력 강화"}]',
 '본과 진학을 위해 기초의학 과목 성적 관리와 임상실습 경험을 병행하세요.'),

-- medical × opportunity
('medical', 'opportunity',
 '[{"name":"volunteer_hours","current_value":"0","simulated_value":"100","impact_description":"의료 봉사시간 확보"},{"name":"clinical_observation","current_value":"미참여","simulated_value":"참여","impact_description":"임상 관찰 프로그램 참여"}]',
 '[{"metric_name":"공감 능력","current_value":50,"simulated_value":90,"change_percent":80.0,"impact_level":"positive","explanation":"봉사활동으로 환자 공감 능력 향상"},{"metric_name":"포트폴리오 강도","current_value":30,"simulated_value":85,"change_percent":183.3,"impact_level":"positive","explanation":"봉사 경험이 포트폴리오 크게 강화"}]',
 '지역사회 의료봉사와 임상관찰 프로그램에 적극 참여하세요.'),

-- nursing × skill_development
('nursing', 'skill_development',
 '[{"name":"simulation_lab","current_value":"미참여","simulated_value":"참여","impact_description":"시뮬레이션 실습 참여"},{"name":"additional_courses","current_value":"0","simulated_value":"2","impact_description":"추가 전공 과목 수강"}]',
 '[{"metric_name":"임상 스킬","current_value":45,"simulated_value":82,"change_percent":82.2,"impact_level":"positive","explanation":"시뮬레이션 실습으로 임상 역량 강화"},{"metric_name":"응급 대응","current_value":30,"simulated_value":70,"change_percent":133.3,"impact_level":"positive","explanation":"응급 상황 대응 능력 향상"}]',
 '시뮬레이션 실습실 활용과 아동/모성간호학 추가 수강을 권장합니다.'),

-- nursing × career_path
('nursing', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"간호사","impact_description":"간호사 커리어 목표 설정"},{"name":"clinical_hours","current_value":"0","simulated_value":"1000","impact_description":"임상실습 시간 확보"}]',
 '[{"metric_name":"커리어 준비도","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"간호사 면허시험 준비 경로 확보"},{"metric_name":"임상 역량","current_value":15,"simulated_value":65,"change_percent":333.3,"impact_level":"positive","explanation":"임상실습으로 실무 역량 대폭 향상"}]',
 '간호사 국가시험 준비와 병원 임상실습을 병행하세요.'),

-- nursing × opportunity
('nursing', 'opportunity',
 '[{"name":"hospital_practice","current_value":"미참여","simulated_value":"대학병원","impact_description":"대학병원 임상실습"},{"name":"mentoring","current_value":"미참여","simulated_value":"참여","impact_description":"선배 간호사 멘토링"}]',
 '[{"metric_name":"실무 능력","current_value":20,"simulated_value":88,"change_percent":340.0,"impact_level":"positive","explanation":"병원 실습으로 실무 능력 대폭 향상"},{"metric_name":"전문성","current_value":35,"simulated_value":85,"change_percent":142.9,"impact_level":"positive","explanation":"멘토링으로 전문 역량 강화"}]',
 '대학병원 임상실습 참여와 선배 간호사 멘토링을 적극 활용하세요.'),

-- pharmacy × skill_development
('pharmacy', 'skill_development',
 '[{"name":"lab_practice","current_value":"기본","simulated_value":"심화","impact_description":"실험실습 심화"},{"name":"additional_courses","current_value":"0","simulated_value":"2","impact_description":"임상약학 추가 수강"}]',
 '[{"metric_name":"약학 스킬","current_value":45,"simulated_value":83,"change_percent":84.4,"impact_level":"positive","explanation":"심화 실습으로 약학 역량 강화"},{"metric_name":"약물 지식","current_value":50,"simulated_value":80,"change_percent":60.0,"impact_level":"positive","explanation":"추가 과목으로 약물 지식 확대"}]',
 '약리학 심화 실습과 임상약학 추가 수강을 권장합니다.'),

-- pharmacy × career_path
('pharmacy', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"약사","impact_description":"약사 커리어 목표 설정"},{"name":"target_exam","current_value":"미정","simulated_value":"약사국가시험","impact_description":"국가시험 준비"}]',
 '[{"metric_name":"커리어 준비도","current_value":38,"simulated_value":76,"change_percent":100.0,"impact_level":"positive","explanation":"약사 면허시험 준비 경로 확보"},{"metric_name":"약학 전문성","current_value":40,"simulated_value":72,"change_percent":80.0,"impact_level":"positive","explanation":"전문 약학 역량 향상"}]',
 '약사 국가시험 준비와 제약 실습 경험을 병행하세요.'),

-- pharmacy × opportunity
('pharmacy', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"제약회사","impact_description":"제약회사 인턴십"},{"name":"research_project","current_value":"미참여","simulated_value":"참여","impact_description":"연구 프로젝트 참여"}]',
 '[{"metric_name":"산업 이해도","current_value":20,"simulated_value":85,"change_percent":325.0,"impact_level":"positive","explanation":"인턴십으로 제약 산업 이해도 대폭 향상"},{"metric_name":"네트워크","current_value":10,"simulated_value":80,"change_percent":700.0,"impact_level":"positive","explanation":"업계 네트워크 구축"}]',
 '제약회사 인턴십 참여와 연구 프로젝트 경험을 쌓으세요.'),

-- health × skill_development
('health', 'skill_development',
 '[{"name":"practical_training","current_value":"기본","simulated_value":"심화","impact_description":"실습 훈련 심화"},{"name":"additional_courses","current_value":"0","simulated_value":"2","impact_description":"재활의학 등 추가 수강"}]',
 '[{"metric_name":"의료 지식","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"심화 학습으로 의료 지식 향상"},{"metric_name":"실무 능력","current_value":35,"simulated_value":75,"change_percent":114.3,"impact_level":"positive","explanation":"실습 훈련으로 실무 역량 강화"}]',
 '재활의학, 병리학 추가 수강과 실습 훈련 심화를 권장합니다.'),

-- health × career_path
('health', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"보건전문가","impact_description":"보건 전문가 목표 설정"},{"name":"certification","current_value":"미취득","simulated_value":"보건전문자격증","impact_description":"자격증 취득 계획"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":74,"change_percent":111.4,"impact_level":"positive","explanation":"보건 전문가 경로 확보"},{"metric_name":"자격증 준비","current_value":20,"simulated_value":78,"change_percent":290.0,"impact_level":"positive","explanation":"자격증 취득 준비 강화"}]',
 '보건 전문 자격증 취득과 의료기관 실습을 병행하세요.'),

-- health × opportunity
('health', 'opportunity',
 '[{"name":"facility_practice","current_value":"미참여","simulated_value":"의료기관","impact_description":"의료기관 현장실습"},{"name":"mentoring","current_value":"미참여","simulated_value":"참여","impact_description":"지도교수 멘토링"}]',
 '[{"metric_name":"실무 역량","current_value":25,"simulated_value":85,"change_percent":240.0,"impact_level":"positive","explanation":"현장실습으로 실무 역량 대폭 향상"},{"metric_name":"전문 성장","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"멘토링으로 전문가 성장 경로 확보"}]',
 '의료기관 현장실습 참여와 지도교수 멘토링을 활용하세요.'),

-- it_engineering × skill_development
('it_engineering', 'skill_development',
 '[{"name":"coding_practice","current_value":"주 5시간","simulated_value":"주 15시간","impact_description":"코딩 연습 시간 증가"},{"name":"algorithm_study","current_value":"미시작","simulated_value":"매일 1문제","impact_description":"알고리즘 학습 시작"}]',
 '[{"metric_name":"코딩 실력","current_value":50,"simulated_value":85,"change_percent":70.0,"impact_level":"positive","explanation":"집중 연습으로 코딩 실력 향상"},{"metric_name":"알고리즘","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"알고리즘 학습으로 문제해결력 강화"}]',
 'Python/Java 코딩 연습과 알고리즘 문제풀이를 꾸준히 하세요.'),

-- it_engineering × career_path
('it_engineering', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"소프트웨어 개발자","impact_description":"개발자 커리어 목표"},{"name":"certifications","current_value":"0","simulated_value":"정보처리기사","impact_description":"자격증 취득"},{"name":"portfolio","current_value":"없음","simulated_value":"3개 프로젝트","impact_description":"포트폴리오 구축"}]',
 '[{"metric_name":"커리어 준비도","current_value":40,"simulated_value":76,"change_percent":90.0,"impact_level":"positive","explanation":"IT 전문가 취업 경쟁력 확보"},{"metric_name":"기술 역량","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"포트폴리오로 기술력 입증"}]',
 '정보처리기사 자격증 취득과 개인 프로젝트 포트폴리오 구축을 병행하세요.'),

-- it_engineering × opportunity
('it_engineering', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"IT기업","impact_description":"IT 기업 인턴십"},{"name":"team_project","current_value":"0","simulated_value":"1","impact_description":"팀 프로젝트 참여"}]',
 '[{"metric_name":"실무 경험","current_value":15,"simulated_value":88,"change_percent":486.7,"impact_level":"positive","explanation":"인턴십으로 실무 경험 대폭 확보"},{"metric_name":"업계 이해","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"IT 산업 현장 이해도 향상"}]',
 'IT 기업 인턴십 참여와 팀 프로젝트 경험을 적극 쌓으세요.'),

-- architecture × skill_development
('architecture', 'skill_development',
 '[{"name":"design_tool","current_value":"기초","simulated_value":"숙련","impact_description":"BIM/CAD 도구 숙달"},{"name":"design_studio","current_value":"미참여","simulated_value":"참여","impact_description":"설계 스튜디오 참여"}]',
 '[{"metric_name":"설계 역량","current_value":45,"simulated_value":83,"change_percent":84.4,"impact_level":"positive","explanation":"BIM/CAD 숙달로 설계 역량 강화"},{"metric_name":"창의력","current_value":50,"simulated_value":80,"change_percent":60.0,"impact_level":"positive","explanation":"스튜디오 참여로 창의적 설계 능력 향상"}]',
 'BIM/CAD 도구 숙달과 설계 스튜디오 참여를 권장합니다.'),

-- architecture × career_path
('architecture', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"건축사","impact_description":"건축사 커리어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"건축기사","impact_description":"건축기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":74,"change_percent":111.4,"impact_level":"positive","explanation":"건축사 자격 경로 확보"},{"metric_name":"포트폴리오","current_value":30,"simulated_value":72,"change_percent":140.0,"impact_level":"positive","explanation":"설계 포트폴리오 구축으로 경쟁력 강화"}]',
 '건축기사 자격증 취득과 설계 포트폴리오 구축을 병행하세요.'),

-- architecture × opportunity
('architecture', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"건축사사무소","impact_description":"건축사사무소 인턴십"},{"name":"competition","current_value":"0","simulated_value":"2회","impact_description":"설계 공모전 참여"}]',
 '[{"metric_name":"실무 능력","current_value":20,"simulated_value":85,"change_percent":325.0,"impact_level":"positive","explanation":"인턴십으로 실무 설계 역량 대폭 향상"},{"metric_name":"포트폴리오 강도","current_value":25,"simulated_value":80,"change_percent":220.0,"impact_level":"positive","explanation":"공모전 참여로 포트폴리오 강화"}]',
 '건축사사무소 인턴십과 설계 공모전에 적극 참여하세요.'),

-- civil_eng × skill_development
('civil_eng', 'skill_development',
 '[{"name":"cad_practice","current_value":"기초","simulated_value":"숙련","impact_description":"CAD/구조해석 도구 숙달"},{"name":"field_survey","current_value":"미경험","simulated_value":"경험","impact_description":"현장 측량 실습"}]',
 '[{"metric_name":"설계 역량","current_value":40,"simulated_value":82,"change_percent":105.0,"impact_level":"positive","explanation":"CAD 숙달로 구조설계 역량 강화"},{"metric_name":"현장 능력","current_value":30,"simulated_value":75,"change_percent":150.0,"impact_level":"positive","explanation":"측량 실습으로 현장 역량 향상"}]',
 'CAD/구조해석 도구 숙달과 현장 측량 실습을 권장합니다.'),

-- civil_eng × career_path
('civil_eng', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"토목기술자","impact_description":"토목 엔지니어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"토목기사","impact_description":"토목기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":76,"change_percent":117.1,"impact_level":"positive","explanation":"토목기사 자격 경로 확보"},{"metric_name":"기술 역량","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"전문 기술 역량 강화"}]',
 '토목기사 자격증 취득과 현장 실습 경험을 병행하세요.'),

-- civil_eng × opportunity
('civil_eng', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"건설회사","impact_description":"건설회사 인턴십"},{"name":"site_visit","current_value":"0","simulated_value":"5회","impact_description":"현장 견학"}]',
 '[{"metric_name":"실무 경험","current_value":15,"simulated_value":85,"change_percent":466.7,"impact_level":"positive","explanation":"인턴십으로 현장 실무 역량 대폭 확보"},{"metric_name":"산업 이해","current_value":25,"simulated_value":78,"change_percent":212.0,"impact_level":"positive","explanation":"현장 경험으로 산업 이해도 향상"}]',
 '건설회사 인턴십과 현장 견학에 적극 참여하세요.'),

-- mechanical × skill_development
('mechanical', 'skill_development',
 '[{"name":"cad_cam","current_value":"기초","simulated_value":"숙련","impact_description":"SolidWorks/ANSYS 숙달"},{"name":"capstone","current_value":"미참여","simulated_value":"참여","impact_description":"캡스톤 프로젝트 참여"}]',
 '[{"metric_name":"설계 도구","current_value":40,"simulated_value":85,"change_percent":112.5,"impact_level":"positive","explanation":"CAD/CAM 숙달로 설계 역량 강화"},{"metric_name":"해석 능력","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"해석 도구 활용 능력 향상"}]',
 'SolidWorks/ANSYS 숙달과 캡스톤 프로젝트 참여를 권장합니다.'),

-- mechanical × career_path
('mechanical', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"기계설계엔지니어","impact_description":"기계 엔지니어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"일반기계기사","impact_description":"기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":38,"simulated_value":76,"change_percent":100.0,"impact_level":"positive","explanation":"기계설계 엔지니어 경로 확보"},{"metric_name":"기술 역량","current_value":42,"simulated_value":80,"change_percent":90.5,"impact_level":"positive","explanation":"전문 기술 역량 강화"}]',
 '일반기계기사 자격증 취득과 프로젝트 포트폴리오 구축을 병행하세요.'),

-- mechanical × opportunity
('mechanical', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"제조기업","impact_description":"제조기업 인턴십"},{"name":"team_project","current_value":"0","simulated_value":"1","impact_description":"팀 프로젝트 참여"}]',
 '[{"metric_name":"실무 경험","current_value":15,"simulated_value":88,"change_percent":486.7,"impact_level":"positive","explanation":"인턴십으로 제조 실무 역량 대폭 확보"},{"metric_name":"업계 이해","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"제조 산업 현장 이해도 향상"}]',
 '제조기업 인턴십 참여와 팀 프로젝트 경험을 적극 쌓으세요.'),

-- electrical × skill_development
('electrical', 'skill_development',
 '[{"name":"circuit_design","current_value":"기초","simulated_value":"숙련","impact_description":"회로설계 도구 숙달"},{"name":"embedded","current_value":"미경험","simulated_value":"경험","impact_description":"임베디드 실습"}]',
 '[{"metric_name":"회로 설계","current_value":40,"simulated_value":85,"change_percent":112.5,"impact_level":"positive","explanation":"PCB/FPGA 숙달로 설계 역량 강화"},{"metric_name":"임베디드","current_value":30,"simulated_value":78,"change_percent":160.0,"impact_level":"positive","explanation":"임베디드 실습으로 역량 향상"}]',
 '회로설계 도구 숙달과 임베디드 프로젝트 참여를 권장합니다.'),

-- electrical × career_path
('electrical', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"반도체엔지니어","impact_description":"반도체 엔지니어 목표"},{"name":"certification","current_value":"미취득","simulated_value":"전자기사","impact_description":"전자기사 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":38,"simulated_value":76,"change_percent":100.0,"impact_level":"positive","explanation":"반도체 엔지니어 경로 확보"},{"metric_name":"기술 역량","current_value":42,"simulated_value":80,"change_percent":90.5,"impact_level":"positive","explanation":"전자 전문 기술 역량 강화"}]',
 '전자기사 자격증 취득과 프로젝트 포트폴리오 구축을 병행하세요.'),

-- electrical × opportunity
('electrical', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"반도체기업","impact_description":"반도체 기업 인턴십"},{"name":"team_project","current_value":"0","simulated_value":"1","impact_description":"팀 프로젝트 참여"}]',
 '[{"metric_name":"실무 경험","current_value":15,"simulated_value":88,"change_percent":486.7,"impact_level":"positive","explanation":"인턴십으로 반도체 실무 역량 대폭 확보"},{"metric_name":"업계 이해","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"반도체 산업 현장 이해도 향상"}]',
 '반도체 기업 인턴십 참여와 팀 프로젝트 경험을 적극 쌓으세요.'),

-- chemical_env × skill_development
('chemical_env', 'skill_development',
 '[{"name":"research_project","current_value":"미참여","simulated_value":"참여","impact_description":"연구 프로젝트 참여"},{"name":"statistical_analysis","current_value":"기초","simulated_value":"중급","impact_description":"통계분석 역량 향상"}]',
 '[{"metric_name":"실험 역량","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"연구 프로젝트로 실험 역량 향상"},{"metric_name":"데이터 분석","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"통계분석 역량 강화"}]',
 '실험 연구 프로젝트 참여와 통계분석 심화 학습을 권장합니다.'),

-- chemical_env × career_path
('chemical_env', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"대학원/연구소","impact_description":"연구원 커리어 목표"},{"name":"research_paper","current_value":"없음","simulated_value":"1편","impact_description":"연구 논문 발표"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":74,"change_percent":146.7,"impact_level":"positive","explanation":"연구원 경로 확보"},{"metric_name":"연구 역량","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"연구 역량 강화"}]',
 '대학원 진학 준비와 연구 논문 발표 경험을 쌓으세요.'),

-- chemical_env × opportunity
('chemical_env', 'opportunity',
 '[{"name":"lab_intern","current_value":"미참여","simulated_value":"대학연구실","impact_description":"연구실 인턴"},{"name":"paper_contribution","current_value":"없음","simulated_value":"공동저자","impact_description":"논문 기여"}]',
 '[{"metric_name":"연구 역량","current_value":20,"simulated_value":88,"change_percent":340.0,"impact_level":"positive","explanation":"연구실 인턴으로 연구 역량 대폭 향상"},{"metric_name":"학술 네트워크","current_value":10,"simulated_value":78,"change_percent":680.0,"impact_level":"positive","explanation":"학계 네트워크 구축"}]',
 '대학 연구실 학부 인턴에 적극 참여하세요.'),

-- industrial × skill_development
('industrial', 'skill_development',
 '[{"name":"process_analysis","current_value":"기초","simulated_value":"중급","impact_description":"공정분석 역량 향상"},{"name":"data_tool","current_value":"미경험","simulated_value":"Excel/Python","impact_description":"데이터 분석 도구 학습"}]',
 '[{"metric_name":"공정 분석","current_value":40,"simulated_value":82,"change_percent":105.0,"impact_level":"positive","explanation":"공정분석 역량 강화"},{"metric_name":"데이터 활용","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"데이터 도구 활용 능력 향상"}]',
 '공정분석 심화 학습과 데이터 분석 도구 활용을 권장합니다.'),

-- industrial × career_path
('industrial', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"산업엔지니어","impact_description":"산업공학 전문가 목표"},{"name":"certification","current_value":"미취득","simulated_value":"품질경영기사","impact_description":"품질 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":76,"change_percent":117.1,"impact_level":"positive","explanation":"산업공학 전문가 경로 확보"},{"metric_name":"전문 역량","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"품질/공정 전문 역량 강화"}]',
 '품질경영기사 자격증 취득과 현장 실습을 병행하세요.'),

-- industrial × opportunity
('industrial', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"제조/물류기업","impact_description":"제조/물류 기업 인턴십"},{"name":"process_improvement","current_value":"미경험","simulated_value":"경험","impact_description":"공정개선 프로젝트 참여"}]',
 '[{"metric_name":"실무 경험","current_value":15,"simulated_value":85,"change_percent":466.7,"impact_level":"positive","explanation":"인턴십으로 산업 현장 역량 대폭 확보"},{"metric_name":"프로젝트 경험","current_value":20,"simulated_value":78,"change_percent":290.0,"impact_level":"positive","explanation":"공정개선 프로젝트로 실무 역량 향상"}]',
 '제조/물류 기업 인턴십과 공정개선 프로젝트에 적극 참여하세요.'),

-- business × skill_development
('business', 'skill_development',
 '[{"name":"case_study","current_value":"0","simulated_value":"10건","impact_description":"케이스 스터디 수행"},{"name":"data_analysis","current_value":"기초","simulated_value":"중급","impact_description":"데이터 분석 역량 향상"}]',
 '[{"metric_name":"분석 역량","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"케이스 스터디로 분석력 향상"},{"metric_name":"전략 사고","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"전략적 사고력 강화"}]',
 '데이터 분석 역량 강화와 실제 기업 케이스 스터디를 병행하세요.'),

-- business × career_path
('business', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"경영 컨설턴트","impact_description":"컨설턴트 커리어 목표"},{"name":"mba_plan","current_value":"미정","simulated_value":"MBA 진학","impact_description":"MBA 진학 계획"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":74,"change_percent":111.4,"impact_level":"positive","explanation":"경영 전문가 경로 확보"},{"metric_name":"비즈니스 역량","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"비즈니스 분석 역량 강화"}]',
 'CPA/경영지도사 자격증 준비와 MBA 진학 계획을 구체화하세요.'),

-- business × opportunity
('business', 'opportunity',
 '[{"name":"internship","current_value":"미참여","simulated_value":"대기업","impact_description":"대기업 인턴십"},{"name":"department","current_value":"미정","simulated_value":"경영기획","impact_description":"경영기획 부서 배치"}]',
 '[{"metric_name":"비즈니스 스킬","current_value":25,"simulated_value":85,"change_percent":240.0,"impact_level":"positive","explanation":"인턴십으로 비즈니스 스킬 대폭 향상"},{"metric_name":"커리어 명확성","current_value":30,"simulated_value":82,"change_percent":173.3,"impact_level":"positive","explanation":"현장 경험으로 진로 방향 명확화"}]',
 '대기업/중견기업 인턴십에 적극 지원하세요.'),

-- law_admin × skill_development
('law_admin', 'skill_development',
 '[{"name":"moot_court","current_value":"미참여","simulated_value":"참여","impact_description":"모의재판 참여"},{"name":"additional_courses","current_value":"0","simulated_value":"형법,상법","impact_description":"추가 법학 과목 수강"}]',
 '[{"metric_name":"법률 분석","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"법률 분석 역량 크게 향상"},{"metric_name":"논증 능력","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"모의재판으로 논증 능력 강화"}]',
 '모의재판 참여와 형법/상법 추가 수강을 권장합니다.'),

-- law_admin × career_path
('law_admin', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"법률전문가","impact_description":"법조인 커리어 목표"},{"name":"bar_exam","current_value":"미정","simulated_value":"법학적성시험","impact_description":"법학적성시험 준비"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":72,"change_percent":140.0,"impact_level":"positive","explanation":"법률 전문가 경로 확보"},{"metric_name":"법률 지식","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"법학 핵심 과목 역량 강화"}]',
 '법학적성시험 준비와 법률 핵심 과목 성적 관리를 병행하세요.'),

-- law_admin × opportunity
('law_admin', 'opportunity',
 '[{"name":"practice","current_value":"미참여","simulated_value":"법률사무소","impact_description":"법률사무소 실습"},{"name":"case_study","current_value":"0","simulated_value":"5건","impact_description":"실제 사례 분석"}]',
 '[{"metric_name":"실무 능력","current_value":15,"simulated_value":85,"change_percent":466.7,"impact_level":"positive","explanation":"법률사무소 실습으로 실무 역량 대폭 향상"},{"metric_name":"법률 문서","current_value":20,"simulated_value":80,"change_percent":300.0,"impact_level":"positive","explanation":"실무 문서 작성 능력 강화"}]',
 '법률사무소/공공기관 실습에 적극 참여하세요.'),

-- education × skill_development
('education', 'skill_development',
 '[{"name":"micro_teaching","current_value":"미참여","simulated_value":"참여","impact_description":"마이크로 티칭 실습"},{"name":"additional_skills","current_value":"0","simulated_value":"상담기법,교육평가","impact_description":"추가 역량 개발"}]',
 '[{"metric_name":"교수법","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"마이크로 티칭으로 교수법 향상"},{"metric_name":"학생 이해","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"교육심리 역량 강화"}]',
 '마이크로 티칭 실습과 상담기법/교육평가 추가 학습을 권장합니다.'),

-- education × career_path
('education', 'career_path',
 '[{"name":"target_role","current_value":"미정","simulated_value":"교육전문가","impact_description":"교원 커리어 목표"},{"name":"target_exam","current_value":"미정","simulated_value":"교원임용시험","impact_description":"임용시험 준비"}]',
 '[{"metric_name":"커리어 준비도","current_value":35,"simulated_value":75,"change_percent":114.3,"impact_level":"positive","explanation":"교원 임용 경로 확보"},{"metric_name":"교수 역량","current_value":40,"simulated_value":80,"change_percent":100.0,"impact_level":"positive","explanation":"교육 전문 역량 강화"}]',
 '교원임용시험 준비와 교직 이수 과정을 체계적으로 수행하세요.'),

-- education × opportunity
('education', 'opportunity',
 '[{"name":"teaching_practice","current_value":"미참여","simulated_value":"중학교","impact_description":"교생실습 참여"},{"name":"class_management","current_value":"미경험","simulated_value":"경험","impact_description":"학급 운영 경험"}]',
 '[{"metric_name":"실제 교수","current_value":10,"simulated_value":88,"change_percent":780.0,"impact_level":"positive","explanation":"교생실습으로 실전 교수 역량 확보"},{"metric_name":"학급 운영","current_value":5,"simulated_value":78,"change_percent":1460.0,"impact_level":"positive","explanation":"학급 운영 경험으로 교사 역량 강화"}]',
 '교생실습에 적극 참여하고 학급 운영 경험을 쌓으세요.'),

-- humanities × skill_development
('humanities', 'skill_development',
 '[{"name":"thesis_writing","current_value":"미경험","simulated_value":"경험","impact_description":"논문 작성 경험"},{"name":"foreign_language","current_value":"중급","simulated_value":"고급","impact_description":"외국어 역량 향상"}]',
 '[{"metric_name":"연구 역량","current_value":35,"simulated_value":82,"change_percent":134.3,"impact_level":"positive","explanation":"논문 작성으로 연구 역량 향상"},{"metric_name":"비판적 분석","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"비판적 분석력 강화"}]',
 '외국어 심화 학습과 논문 작성 경험을 권장합니다.'),

-- humanities × career_path
('humanities', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"대학원/문화산업","impact_description":"진로 방향 설정"},{"name":"language_cert","current_value":"미취득","simulated_value":"취득","impact_description":"어학 자격증 취득"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":70,"change_percent":133.3,"impact_level":"positive","explanation":"인문학 전문가 경로 확보"},{"metric_name":"학술 역량","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"학술 연구 역량 강화"}]',
 '대학원 진학 준비와 어학 자격증 취득을 병행하세요.'),

-- humanities × opportunity
('humanities', 'opportunity',
 '[{"name":"exchange_program","current_value":"미참여","simulated_value":"영어권","impact_description":"해외 교환학생"},{"name":"cultural_immersion","current_value":"미경험","simulated_value":"경험","impact_description":"문화 체험"}]',
 '[{"metric_name":"어학 향상","current_value":40,"simulated_value":88,"change_percent":120.0,"impact_level":"positive","explanation":"교환학생으로 어학 역량 대폭 향상"},{"metric_name":"글로벌 시야","current_value":25,"simulated_value":82,"change_percent":228.0,"impact_level":"positive","explanation":"해외 경험으로 글로벌 관점 확대"}]',
 '해외 교환학생 프로그램에 적극 참여하세요.'),

-- arts × skill_development
('arts', 'skill_development',
 '[{"name":"workshop","current_value":"미참여","simulated_value":"참여","impact_description":"창작 워크숍 참여"},{"name":"media_production","current_value":"기초","simulated_value":"중급","impact_description":"미디어 제작 역량 향상"}]',
 '[{"metric_name":"창작 능력","current_value":45,"simulated_value":85,"change_percent":88.9,"impact_level":"positive","explanation":"워크숍으로 창작 능력 향상"},{"metric_name":"기술 스킬","current_value":35,"simulated_value":78,"change_percent":122.9,"impact_level":"positive","explanation":"미디어 제작 기술 강화"}]',
 '창작 워크숍 참여와 미디어 제작 실습을 권장합니다.'),

-- arts × career_path
('arts', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"크리에이터/디자이너","impact_description":"예술 전문가 목표"},{"name":"portfolio","current_value":"없음","simulated_value":"구축","impact_description":"포트폴리오 구축"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":72,"change_percent":140.0,"impact_level":"positive","explanation":"예술 전문가 경로 확보"},{"metric_name":"창작 역량","current_value":45,"simulated_value":80,"change_percent":77.8,"impact_level":"positive","explanation":"창작 역량 강화"}]',
 '포트폴리오 구축과 전시회/공모전 참여를 병행하세요.'),

-- arts × opportunity
('arts', 'opportunity',
 '[{"name":"competitions","current_value":"0","simulated_value":"3회","impact_description":"공모전 참여"},{"name":"exhibition","current_value":"미참여","simulated_value":"개인전","impact_description":"전시회 개최"}]',
 '[{"metric_name":"포트폴리오","current_value":25,"simulated_value":88,"change_percent":252.0,"impact_level":"positive","explanation":"공모전/전시회로 포트폴리오 대폭 강화"},{"metric_name":"인지도","current_value":10,"simulated_value":75,"change_percent":650.0,"impact_level":"positive","explanation":"작품 활동으로 인지도 향상"}]',
 '작품 공모전/전시회에 적극 참여하여 포트폴리오를 강화하세요.'),

-- science × skill_development
('science', 'skill_development',
 '[{"name":"research_project","current_value":"미참여","simulated_value":"참여","impact_description":"연구 프로젝트 참여"},{"name":"statistical_analysis","current_value":"기초","simulated_value":"중급","impact_description":"통계분석 역량 향상"}]',
 '[{"metric_name":"실험 역량","current_value":40,"simulated_value":83,"change_percent":107.5,"impact_level":"positive","explanation":"연구 프로젝트로 실험 역량 향상"},{"metric_name":"데이터 분석","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"통계분석 역량 강화"}]',
 '실험 연구 프로젝트 참여와 통계분석 심화 학습을 권장합니다.'),

-- science × career_path
('science', 'career_path',
 '[{"name":"target_path","current_value":"미정","simulated_value":"대학원/연구소","impact_description":"연구원 커리어 목표"},{"name":"research_paper","current_value":"없음","simulated_value":"1편","impact_description":"연구 논문 발표"}]',
 '[{"metric_name":"커리어 준비도","current_value":30,"simulated_value":74,"change_percent":146.7,"impact_level":"positive","explanation":"연구원 경로 확보"},{"metric_name":"연구 역량","current_value":35,"simulated_value":80,"change_percent":128.6,"impact_level":"positive","explanation":"연구 역량 강화"}]',
 '대학원 진학 준비와 연구 논문 발표 경험을 쌓으세요.'),

-- science × opportunity
('science', 'opportunity',
 '[{"name":"lab_intern","current_value":"미참여","simulated_value":"대학연구실","impact_description":"연구실 인턴"},{"name":"paper_contribution","current_value":"없음","simulated_value":"공동저자","impact_description":"논문 기여"}]',
 '[{"metric_name":"연구 역량","current_value":20,"simulated_value":88,"change_percent":340.0,"impact_level":"positive","explanation":"연구실 인턴으로 연구 역량 대폭 향상"},{"metric_name":"학술 네트워크","current_value":10,"simulated_value":78,"change_percent":680.0,"impact_level":"positive","explanation":"학계 네트워크 구축"}]',
 '대학 연구실 학부 인턴에 적극 참여하세요.'),

-- general × skill_development
('general', 'skill_development',
 '[{"name":"soft_skill_workshop","current_value":"미참여","simulated_value":"참여","impact_description":"소프트스킬 워크숍"},{"name":"additional_skills","current_value":"0","simulated_value":"리더십,팀워크","impact_description":"핵심 역량 개발"}]',
 '[{"metric_name":"의사소통","current_value":45,"simulated_value":82,"change_percent":82.2,"impact_level":"positive","explanation":"워크숍으로 의사소통 역량 향상"},{"metric_name":"문제해결","current_value":40,"simulated_value":78,"change_percent":95.0,"impact_level":"positive","explanation":"핵심 역량 강화"}]',
 '소프트스킬 워크숍 참여와 리더십/팀워크 역량 개발을 권장합니다.'),

-- general × career_path
('general', 'career_path',
 '[{"name":"career_exploration","current_value":"미시작","simulated_value":"완료","impact_description":"진로 탐색 수행"},{"name":"skill_assessment","current_value":"미실시","simulated_value":"완료","impact_description":"역량 진단 실시"}]',
 '[{"metric_name":"커리어 준비도","current_value":25,"simulated_value":70,"change_percent":180.0,"impact_level":"positive","explanation":"진로 탐색으로 방향 설정"},{"metric_name":"자기 이해","current_value":30,"simulated_value":75,"change_percent":150.0,"impact_level":"positive","explanation":"역량 진단으로 자기 이해 향상"}]',
 '진로 탐색과 역량 진단을 먼저 수행하세요.'),

-- general × opportunity
('general', 'opportunity',
 '[{"name":"exchange_program","current_value":"미참여","simulated_value":"교환학생","impact_description":"교환학생 프로그램"},{"name":"language_study","current_value":"기초","simulated_value":"중급","impact_description":"어학 학습"}]',
 '[{"metric_name":"글로벌 역량","current_value":20,"simulated_value":85,"change_percent":325.0,"impact_level":"positive","explanation":"교환학생으로 글로벌 역량 대폭 향상"},{"metric_name":"어학 능력","current_value":30,"simulated_value":80,"change_percent":166.7,"impact_level":"positive","explanation":"어학 능력 향상"}]',
 '해외 교환학생 프로그램 참여를 적극 권장합니다.');

-- UPDATE: FIX_49 시나리오의 base_state, predicted_outcomes를 구조화된 JSONB로 변환
UPDATE tb_simulation_scenario ss
SET
    base_state = jsonb_build_object('variables', (st.variables_json)::jsonb),
    predicted_outcomes = jsonb_build_object(
        'results', (st.results_json)::jsonb,
        'recommendation', st.recommendation,
        'ai_analysis', null
    ),
    upd_user_id = 'FIX_50',
    upd_dt = NOW()
FROM tmp_showcase_50 ts
JOIN tmp_sim_transform_50 st ON ts.category = st.category
WHERE ss.student_id = ts.student_id
  AND ss.scenario_type = st.scenario_type
  AND ss.ins_user_id = 'FIX_49';

DO $$ BEGIN
    RAISE NOTICE 'Part 1 완료: FIX_49 시뮬레이션 JSONB 구조화 (% 건)',
        (SELECT count(*) FROM tb_simulation_scenario WHERE upd_user_id = 'FIX_50');
END $$;


-- =====================================================
-- Part 2: system 시드 coaching_goal 전체 삭제
-- "Career Goal NNN" 패턴 제거 (CASCADE → plan/checkin/retrospective 포함)
-- =====================================================

-- 삭제 전 카운트
DO $$ BEGIN
    RAISE NOTICE 'Part 2: 삭제 대상 system coaching_goal % 건',
        (SELECT count(*) FROM tb_coaching_goal WHERE ins_user_id = 'system');
END $$;

DELETE FROM tb_coaching_goal WHERE ins_user_id = 'system';

DO $$ BEGIN
    RAISE NOTICE 'Part 2 완료: system coaching_goal 삭제 (CASCADE: plan/checkin/retrospective 포함)';
END $$;


-- =====================================================
-- Part 3: 쇼케이스 40명 active 위험 알림 INSERT
-- 학과별 맞춤 리스크 2~3건/학생
-- =====================================================

-- 카테고리별 위험 알림 매핑 테이블
CREATE TEMP TABLE tmp_risk_data_50 (
    category VARCHAR(20),
    alert_order INT,              -- 1, 2, 3
    risk_type VARCHAR(50),
    severity VARCHAR(20),
    title VARCHAR(200),
    description TEXT
);

INSERT INTO tmp_risk_data_50 VALUES
-- nursing
('nursing', 1, 'graduation', 'high',
 '간호사 국시 준비 일정 관리 필요',
 '간호사 국가시험까지 남은 기간 대비 학습 진도가 부족합니다. 핵심 과목 복습 및 모의시험 일정을 수립하세요.'),
('nursing', 2, 'graduation', 'medium',
 '종합병원 채용 시즌 임박',
 '주요 종합병원 신규 간호사 채용 시즌이 다가오고 있습니다. 이력서와 자기소개서 준비를 서둘러야 합니다.'),
('nursing', 3, 'skill_gap', 'medium',
 '임상실습 시간 보완 필요',
 '졸업 요건 대비 임상실습 이수 시간이 부족할 수 있습니다. 추가 실습 기회를 확보하세요.'),

-- business
('business', 1, 'graduation', 'medium',
 '졸업학점 충족 확인 필요',
 '졸업 이수학점 요건 충족 여부를 확인하세요. 전공필수 과목 미이수 여부를 점검해야 합니다.'),
('business', 2, 'graduation', 'high',
 '취업 포트폴리오 미비',
 '취업에 필요한 포트폴리오(자격증, 인턴 경험, 프로젝트)가 부족합니다. 남은 기간 내 보완 계획을 수립하세요.'),
('business', 3, 'skill_gap', 'medium',
 '데이터분석 역량 보완 필요',
 '경영 직무에서 요구하는 데이터 분석(Excel, SQL, Python) 역량이 부족합니다. 관련 역량을 강화하세요.'),

-- health
('health', 1, 'graduation', 'high',
 '보건자격증 취득 일정 관리',
 '보건 관련 자격증 시험 일정이 다가오고 있습니다. 체계적인 시험 준비 계획을 수립하세요.'),
('health', 2, 'graduation', 'medium',
 '의료기관 취업 준비 필요',
 '의료기관 채용 시즌에 맞춰 취업 준비를 시작해야 합니다. 이력서와 면접 준비를 진행하세요.'),
('health', 3, 'skill_gap', 'medium',
 '실습시간 기준 미달 우려',
 '졸업 및 자격증 취득에 필요한 현장실습 시간이 기준에 미달할 수 있습니다. 추가 실습을 확보하세요.'),

-- medical
('medical', 1, 'graduation', 'high',
 '의사 국가시험 준비 일정 관리',
 '의사 국가시험까지의 학습 계획을 점검하세요. 핵심 기초의학 과목 복습이 필요합니다.'),
('medical', 2, 'graduation', 'medium',
 '수련병원 지원 준비 필요',
 '인턴/레지던트 수련병원 지원 시기가 다가오고 있습니다. 지원서 및 추천서 준비를 시작하세요.'),
('medical', 3, 'skill_gap', 'medium',
 '임상실습 평가 보완 필요',
 '임상실습 평가에서 일부 영역의 역량이 기대 수준에 미달합니다. 해당 영역의 보완 학습이 필요합니다.'),

-- pharmacy
('pharmacy', 1, 'graduation', 'high',
 '약사 국가시험 준비 일정 관리',
 '약사 국가시험 대비 학습 진도를 점검하세요. 약리학, 약제학 등 핵심 과목 복습이 시급합니다.'),
('pharmacy', 2, 'graduation', 'medium',
 '약국/제약회사 취업 준비',
 '졸업 후 진로(약국 개업, 제약회사 취업)에 대한 구체적 계획과 준비가 필요합니다.'),
('pharmacy', 3, 'skill_gap', 'medium',
 '임상약학 실무 역량 보완',
 '임상약학 분야의 실무 역량이 부족합니다. 약국/병원 실습 경험을 추가로 확보하세요.'),

-- it_engineering
('it_engineering', 1, 'graduation', 'medium',
 '졸업 프로젝트 완성도 점검',
 '졸업 프로젝트(캡스톤 디자인)의 진행 상황을 점검하세요. 기한 내 완성을 위한 일정 관리가 필요합니다.'),
('it_engineering', 2, 'graduation', 'high',
 'IT 기업 채용 준비 필요',
 'IT 기업 공채/수시 채용 시즌에 맞춘 코딩테스트, 기술면접 준비가 필요합니다.'),
('it_engineering', 3, 'skill_gap', 'medium',
 '클라우드/DevOps 역량 보완',
 'IT 취업 시장에서 요구하는 클라우드(AWS/GCP) 및 DevOps 역량이 부족합니다. 관련 학습을 시작하세요.'),

-- architecture
('architecture', 1, 'graduation', 'medium',
 '졸업설계 포트폴리오 완성 필요',
 '졸업설계 작품의 포트폴리오 정리가 미흡합니다. 취업 지원 전 포트폴리오를 완성하세요.'),
('architecture', 2, 'graduation', 'high',
 '건축사사무소 취업 준비',
 '건축사사무소 채용 시기에 맞춰 포트폴리오와 면접 준비를 시작해야 합니다.'),
('architecture', 3, 'skill_gap', 'medium',
 'BIM 실무 역량 보완 필요',
 'BIM(Building Information Modeling) 실무 활용 능력이 업계 요구 수준에 미달합니다. 추가 학습이 필요합니다.'),

-- civil_eng
('civil_eng', 1, 'graduation', 'medium',
 '졸업학점 및 전공필수 확인',
 '졸업 이수학점과 전공필수 과목 이수 여부를 확인하세요. 미이수 과목이 있을 수 있습니다.'),
('civil_eng', 2, 'graduation', 'high',
 '건설회사 취업 준비 필요',
 '건설회사 채용 시즌에 맞춰 자격증(토목기사)과 면접 준비를 진행하세요.'),
('civil_eng', 3, 'skill_gap', 'medium',
 '현장 실무 경험 부족',
 '현장 측량 및 시공관리 경험이 부족합니다. 인턴십 등을 통한 실무 경험 확보가 필요합니다.'),

-- mechanical
('mechanical', 1, 'graduation', 'medium',
 '졸업 캡스톤 프로젝트 완성',
 '캡스톤 디자인 프로젝트의 완성도를 높여야 합니다. 발표 준비와 보고서 작성을 마무리하세요.'),
('mechanical', 2, 'graduation', 'high',
 '제조/자동차 기업 취업 준비',
 '기계 관련 기업 채용 시즌이 다가오고 있습니다. 기사 자격증과 면접 준비가 필요합니다.'),
('mechanical', 3, 'skill_gap', 'medium',
 'CAD/해석 도구 숙련도 부족',
 'SolidWorks, ANSYS 등 설계/해석 도구의 숙련도가 실무 요구 수준에 미달합니다.'),

-- electrical
('electrical', 1, 'graduation', 'medium',
 '졸업 프로젝트 진행 점검',
 '졸업 프로젝트의 하드웨어/소프트웨어 구현이 일정에 맞게 진행되고 있는지 점검하세요.'),
('electrical', 2, 'graduation', 'high',
 '반도체/전자 기업 취업 준비',
 '반도체/전자 기업 채용 시즌이 다가오고 있습니다. 전공 면접과 적성검사 준비가 필요합니다.'),
('electrical', 3, 'skill_gap', 'medium',
 '반도체 공정 지식 보완 필요',
 '반도체 공정 및 설계 관련 실무 지식이 부족합니다. 관련 과목 복습과 온라인 강의 수강을 권장합니다.'),

-- chemical_env
('chemical_env', 1, 'graduation', 'medium',
 '졸업논문/프로젝트 마감 관리',
 '졸업논문 또는 연구 프로젝트의 마감 일정을 점검하세요. 데이터 정리와 논문 작성이 필요합니다.'),
('chemical_env', 2, 'graduation', 'high',
 '대학원/연구소 진학 준비',
 '대학원 또는 연구소 지원 시기가 다가오고 있습니다. 연구계획서와 추천서 준비를 시작하세요.'),
('chemical_env', 3, 'skill_gap', 'medium',
 '실험 데이터 분석 역량 부족',
 '실험 데이터의 통계 분석 및 시각화 역량이 부족합니다. R 또는 Python 활용 능력을 강화하세요.'),

-- industrial
('industrial', 1, 'graduation', 'medium',
 '졸업학점 및 자격증 확인',
 '졸업 요건 충족 여부와 품질경영기사 등 자격증 취득 일정을 점검하세요.'),
('industrial', 2, 'graduation', 'high',
 '제조/물류 기업 취업 준비',
 '산업공학 관련 기업 채용 시즌에 맞춰 취업 준비를 진행해야 합니다.'),
('industrial', 3, 'skill_gap', 'medium',
 '스마트팩토리 관련 역량 부족',
 '스마트팩토리, IoT 등 4차 산업혁명 관련 기술 역량이 부족합니다. 관련 교육 이수를 권장합니다.'),

-- law_admin
('law_admin', 1, 'graduation', 'high',
 '법학적성시험/행정고시 준비 관리',
 '시험 준비 일정 관리가 필요합니다. 핵심 과목별 학습 계획을 재점검하세요.'),
('law_admin', 2, 'graduation', 'medium',
 '법률사무소/공공기관 취업 준비',
 '졸업 후 진로에 맞는 취업 준비(이력서, 자기소개서, 면접)를 시작해야 합니다.'),
('law_admin', 3, 'skill_gap', 'medium',
 '법률 문서 작성 역량 보완',
 '실무에서 요구하는 법률 문서(소장, 의견서, 계약서) 작성 역량이 부족합니다.'),

-- education
('education', 1, 'graduation', 'high',
 '교원임용시험 준비 일정 관리',
 '교원임용시험까지 남은 기간 대비 학습 계획을 재점검하세요. 전공 및 교직 과목 복습이 필요합니다.'),
('education', 2, 'graduation', 'medium',
 '교생실습 평가 보완 필요',
 '교생실습 평가 결과에서 수업 운영 및 학급 관리 영역의 보완이 필요합니다.'),
('education', 3, 'skill_gap', 'medium',
 '디지털 교육 도구 역량 부족',
 '온라인 수업 및 디지털 교육 도구(LMS, 교육용 앱) 활용 역량이 부족합니다.'),

-- humanities
('humanities', 1, 'graduation', 'medium',
 '졸업논문 진행 일정 관리',
 '졸업논문의 연구 진행 상황을 점검하세요. 지도교수 면담과 초안 작성 일정 관리가 필요합니다.'),
('humanities', 2, 'graduation', 'high',
 '졸업 후 진로 구체화 필요',
 '대학원 진학, 문화산업 취업, 교육 분야 등 진로 방향을 구체화하고 준비를 시작해야 합니다.'),
('humanities', 3, 'skill_gap', 'medium',
 '어학 자격증 점수 미달',
 '취업/대학원 진학에 필요한 어학 자격증(TOEIC, TOEFL 등) 점수가 기준에 미달합니다.'),

-- arts
('arts', 1, 'graduation', 'medium',
 '졸업작품 완성도 점검',
 '졸업 전시/공연을 위한 작품 완성도를 높여야 합니다. 마감 일정에 맞춰 작업 계획을 조정하세요.'),
('arts', 2, 'graduation', 'high',
 '취업용 포트폴리오 미완성',
 '디자인/예술 분야 취업에 필요한 전문 포트폴리오가 미완성 상태입니다. 조속한 완성이 필요합니다.'),
('arts', 3, 'skill_gap', 'medium',
 '디지털 도구 활용 역량 부족',
 '업계에서 요구하는 디지털 도구(Adobe CC, Figma 등) 활용 역량이 부족합니다.'),

-- science
('science', 1, 'graduation', 'medium',
 '졸업논문/연구 프로젝트 마감',
 '졸업논문 또는 연구 프로젝트의 데이터 수집과 분석을 마무리해야 합니다. 일정 관리가 필요합니다.'),
('science', 2, 'graduation', 'high',
 '대학원/연구소 진학 준비',
 '대학원 진학 또는 연구소 지원을 위한 연구계획서와 추천서 준비를 시작하세요.'),
('science', 3, 'skill_gap', 'medium',
 '프로그래밍 역량 보완 필요',
 '연구에 필요한 프로그래밍(Python, R) 및 데이터 분석 역량이 부족합니다.'),

-- general
('general', 1, 'graduation', 'medium',
 '졸업학점 충족 여부 확인',
 '졸업에 필요한 총 이수학점과 전공/교양 학점 충족 여부를 확인하세요.'),
('general', 2, 'graduation', 'high',
 '졸업 후 진로 계획 미수립',
 '졸업 후 구체적인 진로 계획이 수립되지 않았습니다. 취업/진학 방향을 결정하고 준비를 시작하세요.'),
('general', 3, 'skill_gap', 'medium',
 '취업 핵심 역량 부족',
 '의사소통, 문제해결, 디지털 리터러시 등 취업에 필요한 핵심 역량이 부족합니다.');

-- alert 1 (graduation): 전체 40명
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity, title, description,
    trigger_value, threshold_value, related_entity_type, related_entity_id,
    status, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    rd.risk_type,
    rd.severity,
    rd.title,
    rd.description,
    CASE rd.risk_type
        WHEN 'graduation' THEN round((50 + (ts.h % 30))::numeric, 2)
        ELSE round((30 + (ts.h % 40))::numeric, 2)
    END,
    80.00,
    'academic',
    ts.student_id,
    'active',
    'FIX_50',
    NOW() - ((ts.h % 14) || ' days')::interval
FROM tmp_showcase_50 ts
JOIN tmp_risk_data_50 rd ON ts.category = rd.category AND rd.alert_order = 1;

-- alert 2 (career): 전체 40명
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity, title, description,
    trigger_value, threshold_value, related_entity_type, related_entity_id,
    status, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    rd.risk_type,
    rd.severity,
    rd.title,
    rd.description,
    CASE rd.risk_type
        WHEN 'graduation' THEN round((45 + (ts.h % 35))::numeric, 2)
        ELSE round((25 + (ts.h % 45))::numeric, 2)
    END,
    75.00,
    'career',
    ts.student_id,
    'active',
    'FIX_50',
    NOW() - ((ts.h % 10 + 1) || ' days')::interval
FROM tmp_showcase_50 ts
JOIN tmp_risk_data_50 rd ON ts.category = rd.category AND rd.alert_order = 2;

-- alert 3 (skill_gap, 선택): h < 70인 학생만 → ~70% 대상 (~28명)
INSERT INTO tb_risk_alert (
    alert_id, student_id, risk_type, severity, title, description,
    trigger_value, threshold_value, related_entity_type, related_entity_id,
    status, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    rd.risk_type,
    rd.severity,
    rd.title,
    rd.description,
    round((20 + (ts.h % 40))::numeric, 2),
    70.00,
    'skill',
    ts.student_id,
    'active',
    'FIX_50',
    NOW() - ((ts.h % 7 + 1) || ' days')::interval
FROM tmp_showcase_50 ts
JOIN tmp_risk_data_50 rd ON ts.category = rd.category AND rd.alert_order = 3
WHERE ts.h < 70;

DO $$ BEGIN
    RAISE NOTICE 'Part 3 완료: 쇼케이스 active 위험 알림 % 건 생성',
        (SELECT count(*) FROM tb_risk_alert WHERE ins_user_id = 'FIX_50');
END $$;


-- =====================================================
-- Cleanup
-- =====================================================

DROP TABLE IF EXISTS tmp_sim_transform_50;
DROP TABLE IF EXISTS tmp_risk_data_50;
DROP TABLE IF EXISTS tmp_showcase_50;
DROP TABLE IF EXISTS tmp_dept_cat_50;

COMMIT;

-- =====================================================
-- 검증 쿼리 (수동 실행)
-- =====================================================

-- 1. 시뮬레이션 JSONB 구조 확인
-- SELECT scenario_type,
--        base_state->'variables' IS NOT NULL as has_vars,
--        predicted_outcomes->'results' IS NOT NULL as has_results,
--        base_state->'variables'->0->>'name' as first_var,
--        predicted_outcomes->'results'->0->>'metric_name' as first_metric
-- FROM tb_simulation_scenario WHERE upd_user_id = 'FIX_50' LIMIT 6;

-- 2. Career Goal 0건 확인
-- SELECT count(*) FROM tb_coaching_goal WHERE title ~ '^Career Goal';

-- 3. active 위험 알림 분포
-- SELECT ts.student_id, count(*) as alert_count
-- FROM tb_risk_alert ra
-- JOIN (SELECT student_id FROM tb_student WHERE student_id IN (
--     '2021A143','20203008','20203033','20201861','20202956','20201481','20202999','20201478',
--     '20201499','20201333','20201341','20202487','20202493','20202510','20214632','2020A066',
--     '2021A060','2021A056','2021A146','20214314','20214364','20202733','20202883','20202887',
--     '20202924','20202333','20201265','20214819','20201126','20201132','20202358','20202362',
--     '20202364','20202379','20202722','20214353','20201220','20214383','20201352','20201882'
-- )) ts ON ra.student_id = ts.student_id
-- WHERE ra.status = 'active' AND ra.ins_user_id = 'FIX_50'
-- GROUP BY ts.student_id ORDER BY ts.student_id;
