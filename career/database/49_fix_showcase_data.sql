-- =====================================================
-- 49_fix_showcase_data.sql
-- 쇼케이스 40명 학과별 데이터 정합성 수정
--
-- 문제 1: tb_simulation_scenario — 전원 IT 전용 시나리오
-- 문제 2: tb_student_skill — 비IT 학생에게 IT 스킬
-- 문제 3: tb_coaching_goal — 19명 generic 영어 목표
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 대상 학생 및 학과-카테고리 매핑
-- =====================================================

CREATE TEMP TABLE tmp_dept_cat_49 AS
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

-- 쇼케이스 40명
CREATE TEMP TABLE tmp_showcase_49 AS
SELECT
    s.student_id,
    s.department_cd,
    s.admission_year,
    dc.category,
    dc.department_nm,
    abs(hashtext(s.student_id)) % 100 AS h
FROM tb_student s
JOIN tmp_dept_cat_49 dc ON s.department_cd = dc.department_cd
WHERE s.student_id IN (
    '2021A143', '20203008', '20203033', '20201861', '20202956', '20201481', '20202999', '20201478',
    '20201499', '20201333', '20201341', '20202487', '20202493', '20202510', '20214632', '2020A066',
    '2021A060', '2021A056', '2021A146', '20214314', '20214364', '20202733', '20202883', '20202887',
    '20202924', '20202333', '20201265', '20214819', '20201126', '20201132', '20202358', '20202362',
    '20202364', '20202379', '20202722', '20214353', '20201220', '20214383', '20201352', '20201882'
);

CREATE INDEX idx_tmp_showcase_49_sid ON tmp_showcase_49(student_id);
CREATE INDEX idx_tmp_showcase_49_cat ON tmp_showcase_49(category);

DO $$ BEGIN
    RAISE NOTICE 'Part 0: 쇼케이스 학생 % 명 선정', (SELECT count(*) FROM tmp_showcase_49);
END $$;


-- =====================================================
-- Part 1: tb_simulation_scenario 수정
-- =====================================================

-- Step 1a: 40명의 system 시나리오 DELETE
DELETE FROM tb_simulation_scenario
WHERE student_id IN (SELECT student_id FROM tmp_showcase_49)
  AND ins_user_id = 'system';

DO $$ BEGIN RAISE NOTICE 'Part 1a: system 시뮬레이션 시나리오 삭제 완료'; END $$;

-- Step 1b: 카테고리별 시나리오 데이터
CREATE TEMP TABLE tmp_sim_data_49 (
    category VARCHAR(20),
    scenario_type VARCHAR(30),
    title VARCHAR(200),
    description TEXT,
    base_state_template TEXT,
    changes_template TEXT,
    outcomes_template TEXT,
    confidence DECIMAL(3,2)
);

INSERT INTO tmp_sim_data_49 VALUES
-- medical
('medical', 'skill_development', '기초의학 역량 강화', '해부학, 생리학, 생화학 등 기초의학 과목 심화 학습 시나리오',
 '{"key_subjects": ["생물학", "의학입문"]}', '{"additional_courses": ["해부학", "생리학", "생화학"], "study_group": true}', '{"career_readiness": 0.85, "exam_readiness": 0.78, "confidence_boost": 0.70}', 0.80),
('medical', 'career_path', '의사 커리어 준비', '본과 진학 후 의사 국가시험 준비까지의 커리어 로드맵 시나리오',
 '{"career_goal": "의사", "field": "의학"}', '{"next_step": "본과 진학", "target_exam": "의사국가시험", "additional_activities": ["임상실습", "의학연구"]}', '{"career_readiness": 0.75, "exam_preparation": 0.80, "clinical_experience": 0.60}', 0.82),
('medical', 'opportunity', '의료 봉사활동 참여 효과', '지역사회 의료봉사 및 임상관찰 프로그램 참여 시 예상 효과',
 '{"volunteer_experience": 0, "clinical_observation_hours": 0}', '{"volunteer_hours": 100, "clinical_observation": true, "target_organizations": ["지역보건소", "대학병원"]}', '{"empathy_development": 0.90, "clinical_awareness": 0.75, "portfolio_strength": 0.85}', 0.78),

-- nursing
('nursing', 'skill_development', '임상간호 역량 강화', '기본간호, 성인간호 등 임상간호 핵심 역량 강화 시나리오',
 '{"key_subjects": ["기본간호학", "성인간호학"]}', '{"additional_courses": ["아동간호학", "모성간호학"], "simulation_lab": true}', '{"clinical_skill": 0.82, "patient_care": 0.78, "emergency_response": 0.70}', 0.79),
('nursing', 'career_path', '간호사 커리어 준비', '간호사 면허시험 준비 및 임상간호 전문가 성장 경로 시나리오',
 '{"career_goal": "간호사", "field": "간호학"}', '{"target_exam": "간호사국가시험", "clinical_hours": 1000, "additional_activities": ["병원실습"]}', '{"career_readiness": 0.78, "exam_preparation": 0.82, "clinical_competency": 0.65}', 0.80),
('nursing', 'opportunity', '병원 실습 참여 효과', '대학병원 임상실습 참여를 통한 실무 역량 향상 시나리오',
 '{"clinical_hours": 0, "hospital_experience": false}', '{"target_hospital": "대학병원", "clinical_hours": 500, "mentoring": true}', '{"practical_skill": 0.88, "teamwork": 0.80, "professionalism": 0.85}', 0.81),

-- pharmacy
('pharmacy', 'skill_development', '약학 전문 역량 강화', '약리학, 약물분석 등 약학 핵심 과목 심화 학습 시나리오',
 '{"key_subjects": ["약리학", "유기화학"]}', '{"additional_courses": ["임상약학", "약물분석"], "lab_practice": true}', '{"pharmaceutical_skill": 0.83, "lab_competency": 0.78, "drug_knowledge": 0.80}', 0.79),
('pharmacy', 'career_path', '약사 커리어 준비', '약사 면허시험 준비 및 약학 전문가 성장 경로 시나리오',
 '{"career_goal": "약사", "field": "약학"}', '{"target_exam": "약사국가시험", "pharmacy_practice": true, "research_participation": true}', '{"career_readiness": 0.76, "exam_preparation": 0.80, "pharmaceutical_knowledge": 0.72}', 0.80),
('pharmacy', 'opportunity', '제약회사 인턴십 참여', '제약회사 인턴십을 통한 산업 현장 경험 및 네트워크 구축',
 '{"internship_experience": false, "industry_contact": 0}', '{"target_company": "제약회사", "internship_months": 3, "research_project": true}', '{"industry_knowledge": 0.85, "practical_skill": 0.78, "network_building": 0.80}', 0.77),

-- health
('health', 'skill_development', '보건의료 역량 강화', '해부학, 생리학, 재활의학 등 보건의료 핵심 역량 강화 시나리오',
 '{"key_subjects": ["해부학", "생리학"]}', '{"additional_courses": ["재활의학", "병리학"], "practical_training": true}', '{"medical_knowledge": 0.80, "practical_skill": 0.75, "patient_care": 0.72}', 0.78),
('health', 'career_path', '보건전문가 커리어 준비', '보건의료 전문가 자격 취득 및 의료기관 취업 경로 시나리오',
 '{"career_goal": "보건전문가", "field": "보건"}', '{"target_certification": "보건전문자격증", "clinical_practice": true}', '{"career_readiness": 0.74, "certification_prep": 0.78, "clinical_skill": 0.68}', 0.78),
('health', 'opportunity', '의료기관 실습 참여', '의료기관 현장실습을 통한 실무 능력 배양 시나리오',
 '{"clinical_hours": 0, "facility_experience": false}', '{"target_facility": "의료기관", "practice_hours": 300, "supervisor_mentoring": true}', '{"practical_competency": 0.85, "professional_growth": 0.78, "teamwork": 0.80}', 0.79),

-- architecture
('architecture', 'skill_development', '건축설계 역량 강화', 'BIM, CAD 등 건축설계 도구 및 디자인 역량 강화 시나리오',
 '{"key_subjects": ["건축설계", "건축구조"]}', '{"additional_skills": ["BIM", "CAD", "3D모델링"], "design_studio": true}', '{"design_skill": 0.83, "technical_tool": 0.78, "creativity": 0.80}', 0.79),
('architecture', 'career_path', '건축사 커리어 준비', '건축사 자격증 취득 및 건축 전문가 성장 경로 시나리오',
 '{"career_goal": "건축사", "field": "건축학"}', '{"target_certification": "건축기사", "portfolio_building": true, "design_competition": true}', '{"career_readiness": 0.74, "certification_prep": 0.78, "portfolio_quality": 0.72}', 0.78),
('architecture', 'opportunity', '설계사무소 실습 참여', '건축사사무소 인턴십을 통한 실무 설계 경험 축적',
 '{"internship_experience": false, "design_portfolio": 0}', '{"target_firm": "건축사사무소", "internship_months": 3, "competition_count": 2}', '{"practical_skill": 0.85, "portfolio_strength": 0.80, "industry_network": 0.75}', 0.78),

-- business
('business', 'skill_development', '비즈니스 분석 역량 강화', '데이터 분석, 재무 분석 등 비즈니스 핵심 역량 강화 시나리오',
 '{"key_subjects": ["경영전략", "마케팅"]}', '{"additional_skills": ["데이터분석", "재무분석"], "case_study": true}', '{"analytical_skill": 0.83, "strategic_thinking": 0.78, "presentation": 0.80}', 0.79),
('business', 'career_path', '경영 전문가 커리어 준비', '경영 컨설턴트/기업 관리자 커리어 준비 시나리오',
 '{"career_goal": "경영전문가", "field": "경영학"}', '{"target_role": "경영 컨설턴트", "certifications": ["CPA", "경영지도사"], "mba_plan": true}', '{"career_readiness": 0.74, "business_acumen": 0.78, "leadership": 0.70}', 0.78),
('business', 'opportunity', '기업 인턴십 참여 효과', '대기업/중견기업 인턴십을 통한 실무 경험 시나리오',
 '{"internship_experience": false, "business_project": 0}', '{"target_company": "대기업", "internship_months": 3, "department": "경영기획"}', '{"business_skill": 0.85, "network": 0.80, "career_clarity": 0.82}', 0.80),

-- law_admin
('law_admin', 'skill_development', '법률 전문 역량 강화', '헌법, 민법, 행정법 등 법학 핵심 과목 심화 학습 시나리오',
 '{"key_subjects": ["헌법", "민법"]}', '{"additional_courses": ["형법", "상법"], "moot_court": true}', '{"legal_analysis": 0.83, "writing_skill": 0.78, "argumentation": 0.80}', 0.79),
('law_admin', 'career_path', '법률/행정 전문가 커리어', '법조인/행정 전문가 자격 취득 및 진로 설계 시나리오',
 '{"career_goal": "법률전문가", "field": "법학/행정"}', '{"target_exam": "법학적성시험", "certifications": ["행정사"], "bar_exam": true}', '{"career_readiness": 0.72, "legal_knowledge": 0.78, "exam_preparation": 0.70}', 0.77),
('law_admin', 'opportunity', '법률사무소 실습 참여', '법률사무소/공공기관 실습을 통한 실무 경험 시나리오',
 '{"internship_experience": false, "case_count": 0}', '{"target_firm": "법률사무소", "practice_months": 3, "case_study": true}', '{"practical_skill": 0.85, "legal_writing": 0.80, "client_communication": 0.75}', 0.78),

-- education
('education', 'skill_development', '교육·상담 역량 강화', '교육심리, 교수법, 상담기법 등 교육 핵심 역량 강화 시나리오',
 '{"key_subjects": ["교육심리", "교수법"]}', '{"additional_skills": ["상담기법", "교육평가"], "micro_teaching": true}', '{"teaching_method": 0.83, "student_understanding": 0.80, "assessment_skill": 0.75}', 0.80),
('education', 'career_path', '교육 전문가 커리어 준비', '교원 임용시험 준비 및 교육 전문가 성장 경로 시나리오',
 '{"career_goal": "교육전문가", "field": "교육학"}', '{"target_exam": "교원임용시험", "teaching_practice": true, "counseling_cert": true}', '{"career_readiness": 0.75, "teaching_skill": 0.80, "counseling_ability": 0.68}', 0.79),
('education', 'opportunity', '교육기관 실습 참여', '학교/교육기관 교생실습을 통한 교육 현장 경험 시나리오',
 '{"teaching_hours": 0, "school_experience": false}', '{"target_school": "중학교", "practice_weeks": 4, "class_management": true}', '{"practical_teaching": 0.88, "classroom_management": 0.78, "student_rapport": 0.82}', 0.80),

-- humanities
('humanities', 'skill_development', '학술 연구 역량 강화', '글쓰기, 연구방법론, 비판적사고 등 학술 역량 강화 시나리오',
 '{"key_subjects": ["글쓰기", "연구방법론"]}', '{"additional_skills": ["외국어", "문헌해독"], "thesis_writing": true}', '{"research_skill": 0.82, "writing_quality": 0.80, "critical_analysis": 0.78}', 0.78),
('humanities', 'career_path', '인문학 전문가 커리어', '학술연구/문화산업/교육 분야 커리어 설계 시나리오',
 '{"career_goal": "인문학전문가", "field": "인문학"}', '{"target_path": "대학원/문화산업", "language_cert": true, "research_paper": true}', '{"career_readiness": 0.70, "academic_skill": 0.78, "cultural_literacy": 0.75}', 0.76),
('humanities', 'opportunity', '해외 교환학생 참여 효과', '해외 대학 교환학생 프로그램 참여를 통한 글로벌 역량 강화',
 '{"exchange_experience": false, "language_level": "intermediate"}', '{"target_country": "영어권", "exchange_semester": 1, "cultural_immersion": true}', '{"language_improvement": 0.88, "cultural_competency": 0.85, "global_perspective": 0.82}', 0.80),

-- arts
('arts', 'skill_development', '창작·디자인 역량 강화', '예술이론, 디자인, 미디어 제작 등 창작 역량 강화 시나리오',
 '{"key_subjects": ["예술이론", "디자인기초"]}', '{"additional_skills": ["미디어제작", "창작실습"], "workshop": true}', '{"creative_ability": 0.85, "technical_skill": 0.78, "aesthetic_sense": 0.80}', 0.79),
('arts', 'career_path', '예술 전문가 커리어 준비', '예술/디자인/공연 분야 전문가 성장 및 진로 설계 시나리오',
 '{"career_goal": "예술전문가", "field": "예술"}', '{"target_path": "크리에이터/디자이너", "portfolio_building": true, "exhibition": true}', '{"career_readiness": 0.72, "creative_skill": 0.80, "portfolio_quality": 0.75}', 0.77),
('arts', 'opportunity', '공모전·전시회 참여 효과', '작품 공모전/전시회 참여를 통한 포트폴리오 강화 시나리오',
 '{"competition_count": 0, "exhibition_count": 0}', '{"target_competitions": 3, "solo_exhibition": true, "collaboration_project": true}', '{"portfolio_strength": 0.88, "recognition": 0.75, "creative_confidence": 0.82}', 0.78),

-- science / chemical_env
('science', 'skill_development', '연구·실험 역량 강화', '실험설계, 통계분석, 데이터처리 등 연구 역량 강화 시나리오',
 '{"key_subjects": ["일반화학", "일반물리"]}', '{"additional_skills": ["실험설계", "통계분석"], "research_project": true}', '{"experimental_skill": 0.83, "data_analysis": 0.80, "scientific_writing": 0.75}', 0.79),
('science', 'career_path', '연구원 커리어 준비', '연구원/과학자 진로 설계 및 대학원 진학 준비 시나리오',
 '{"career_goal": "연구원", "field": "자연과학"}', '{"target_path": "대학원/연구소", "research_paper": true, "lab_experience": true}', '{"career_readiness": 0.74, "research_skill": 0.80, "academic_achievement": 0.72}', 0.78),
('science', 'opportunity', '연구실 인턴 참여 효과', '대학 연구실 학부 인턴 참여를 통한 연구 경험 축적',
 '{"lab_experience": false, "research_hours": 0}', '{"target_lab": "대학연구실", "intern_months": 6, "paper_contribution": true}', '{"research_competency": 0.88, "lab_skill": 0.82, "academic_network": 0.78}', 0.80),

-- chemical_env (science와 동일한 시나리오)
('chemical_env', 'skill_development', '연구·실험 역량 강화', '실험설계, 통계분석, 데이터처리 등 연구 역량 강화 시나리오',
 '{"key_subjects": ["일반화학", "일반물리"]}', '{"additional_skills": ["실험설계", "통계분석"], "research_project": true}', '{"experimental_skill": 0.83, "data_analysis": 0.80, "scientific_writing": 0.75}', 0.79),
('chemical_env', 'career_path', '연구원 커리어 준비', '연구원/과학자 진로 설계 및 대학원 진학 준비 시나리오',
 '{"career_goal": "연구원", "field": "자연과학"}', '{"target_path": "대학원/연구소", "research_paper": true, "lab_experience": true}', '{"career_readiness": 0.74, "research_skill": 0.80, "academic_achievement": 0.72}', 0.78),
('chemical_env', 'opportunity', '연구실 인턴 참여 효과', '대학 연구실 학부 인턴 참여를 통한 연구 경험 축적',
 '{"lab_experience": false, "research_hours": 0}', '{"target_lab": "대학연구실", "intern_months": 6, "paper_contribution": true}', '{"research_competency": 0.88, "lab_skill": 0.82, "academic_network": 0.78}', 0.80),

-- it_engineering / electrical / mechanical (기존 IT 시나리오 유지)
('it_engineering', 'skill_development', '프로그래밍 역량 강화', 'Python, Java 등 프로그래밍 언어 및 알고리즘 역량 강화 시나리오',
 '{"key_subjects": ["Python", "Java"]}', '{"additional_skills": ["알고리즘", "클라우드"], "coding_test_prep": true}', '{"coding_skill": 0.85, "algorithm_ability": 0.78, "system_design": 0.70}', 0.81),
('it_engineering', 'career_path', 'IT 전문가 커리어 준비', 'IT 개발자/엔지니어 취업 준비 및 기술 역량 강화 시나리오',
 '{"career_goal": "IT전문가", "field": "공학"}', '{"target_role": "소프트웨어 개발자", "certifications": ["정보처리기사"], "project_portfolio": true}', '{"career_readiness": 0.76, "technical_skill": 0.80, "portfolio_strength": 0.72}', 0.80),
('it_engineering', 'opportunity', 'IT 기업 인턴십 참여', 'IT 기업 인턴십을 통한 실무 경험 및 기술 스택 확장',
 '{"internship_experience": false, "project_count": 0}', '{"target_company": "IT기업", "internship_months": 6, "team_project": true}', '{"practical_skill": 0.88, "industry_knowledge": 0.80, "network": 0.75}', 0.79),

('electrical', 'skill_development', '프로그래밍 역량 강화', '회로설계 및 임베디드 역량 강화 시나리오',
 '{"key_subjects": ["회로설계", "임베디드"]}', '{"additional_skills": ["PCB설계", "FPGA"], "project": true}', '{"circuit_design": 0.85, "embedded": 0.78, "system_design": 0.70}', 0.81),
('electrical', 'career_path', 'IT 전문가 커리어 준비', '반도체/전자 엔지니어 취업 준비 및 기술 역량 강화 시나리오',
 '{"career_goal": "전자엔지니어", "field": "전자공학"}', '{"target_role": "반도체엔지니어", "certifications": ["전자기사"], "project_portfolio": true}', '{"career_readiness": 0.76, "technical_skill": 0.80, "portfolio_strength": 0.72}', 0.80),
('electrical', 'opportunity', 'IT 기업 인턴십 참여', '반도체 기업 인턴십을 통한 실무 경험 확보',
 '{"internship_experience": false, "project_count": 0}', '{"target_company": "반도체기업", "internship_months": 6, "team_project": true}', '{"practical_skill": 0.88, "industry_knowledge": 0.80, "network": 0.75}', 0.79),

('mechanical', 'skill_development', '프로그래밍 역량 강화', 'CAD/CAM 및 해석 도구 숙달 시나리오',
 '{"key_subjects": ["기계설계", "열역학"]}', '{"additional_skills": ["SolidWorks", "ANSYS"], "capstone": true}', '{"design_tool": 0.85, "analysis_tool": 0.78, "system_design": 0.70}', 0.81),
('mechanical', 'career_path', 'IT 전문가 커리어 준비', '기계설계 엔지니어 취업 준비 및 기술 역량 강화 시나리오',
 '{"career_goal": "기계엔지니어", "field": "기계공학"}', '{"target_role": "기계설계엔지니어", "certifications": ["일반기계기사"], "project_portfolio": true}', '{"career_readiness": 0.76, "technical_skill": 0.80, "portfolio_strength": 0.72}', 0.80),
('mechanical', 'opportunity', 'IT 기업 인턴십 참여', '제조기업 인턴십을 통한 실무 경험 확보',
 '{"internship_experience": false, "project_count": 0}', '{"target_company": "제조기업", "internship_months": 6, "team_project": true}', '{"practical_skill": 0.88, "industry_knowledge": 0.80, "network": 0.75}', 0.79),

-- general
('general', 'skill_development', '핵심 역량 강화', '의사소통, 문제해결, 리더십 등 핵심 역량 강화 시나리오',
 '{"key_subjects": ["의사소통", "문제해결"]}', '{"additional_skills": ["리더십", "팀워크"], "soft_skill_workshop": true}', '{"communication": 0.82, "problem_solving": 0.78, "leadership": 0.75}', 0.78),
('general', 'career_path', '전공 관련 커리어 준비', '전공 분야 관련 진로 탐색 및 커리어 설계 시나리오',
 '{"career_goal": "전공관련직", "field": "일반"}', '{"career_exploration": true, "skill_assessment": true, "mentoring": true}', '{"career_readiness": 0.70, "self_awareness": 0.75, "skill_development": 0.68}', 0.75),
('general', 'opportunity', '해외 교환학생 참여 효과', '해외 교환학생 프로그램을 통한 글로벌 역량 및 시야 확장',
 '{"exchange_experience": false, "global_competency": "low"}', '{"target_program": "교환학생", "semester_count": 1, "language_study": true}', '{"global_perspective": 0.85, "language_skill": 0.80, "adaptability": 0.82}', 0.78);

-- Step 1c: 시나리오 INSERT (학생별 3개씩)
INSERT INTO tb_simulation_scenario (
    scenario_id, student_id, scenario_type, title, description,
    base_state, changes, predicted_outcomes,
    confidence_level, created_at, is_favorite,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    sd.scenario_type,
    sd.title,
    sd.description,
    sd.base_state_template::jsonb,
    sd.changes_template::jsonb,
    sd.outcomes_template::jsonb,
    sd.confidence,
    NOW() - (abs(hashtext(ts.student_id || sd.scenario_type)) % 30 || ' days')::interval,
    CASE WHEN sd.scenario_type = 'career_path' THEN true ELSE false END,
    'FIX_49',
    NOW()
FROM tmp_showcase_49 ts
JOIN tmp_sim_data_49 sd ON ts.category = sd.category
WHERE NOT EXISTS (
    SELECT 1 FROM tb_simulation_scenario ss
    WHERE ss.student_id = ts.student_id
      AND ss.scenario_type = sd.scenario_type
      AND ss.ins_user_id = 'FIX_49'
);

DO $$ BEGIN RAISE NOTICE 'Part 1 완료: 시뮬레이션 시나리오 교체 (% 건 생성)',
    (SELECT count(*) FROM tb_simulation_scenario WHERE ins_user_id = 'FIX_49');
END $$;


-- =====================================================
-- Part 2: tb_student_skill 수정 — 비IT 학생 IT 스킬 제거
-- =====================================================

-- 비IT 학생에서 system 시드 IT 스킬 삭제
-- IT 카테고리(it_engineering, electrical, mechanical)는 제외
DELETE FROM tb_student_skill
WHERE student_id IN (
    SELECT student_id FROM tmp_showcase_49
    WHERE category NOT IN ('it_engineering', 'electrical', 'mechanical')
)
AND ins_user_id = 'system'
AND skill_cd IN ('SK01','SK02','SK03','SK04','SK05','SK06','SK07','SK08');

DO $$ BEGIN RAISE NOTICE 'Part 2 완료: 비IT 학생 IT 스킬 제거'; END $$;


-- =====================================================
-- Part 3: tb_coaching_goal 수정 — 19명 system 목표 교체
-- =====================================================

-- system 코칭 목표가 있는 대상 학생 (Goal이 system인 19명)
CREATE TEMP TABLE tmp_coaching_target_49 AS
SELECT ts.*
FROM tmp_showcase_49 ts
WHERE ts.student_id IN (
    '20203008', '20201861', '20202956', '20201481', '20202999', '20201478', '20201499',
    '20201333', '20201341', '20202487', '20202493', '20202510', '2021A056', '2021A146',
    '20214314', '20202883', '20202887', '20202924', '20201265', '20201132',
    '20202358', '20202362', '20202364', '20202379'
);

CREATE INDEX idx_tmp_ct49_sid ON tmp_coaching_target_49(student_id);

-- Step 3a: system 코칭 목표 DELETE (CASCADE로 checkin/retro/plan 자동 삭제)
DELETE FROM tb_coaching_goal
WHERE std_id IN (SELECT student_id FROM tmp_coaching_target_49)
  AND (ins_user_id = 'system' OR ins_user_id = 'SYSTEM' OR ins_user_id IS NULL);

DO $$ BEGIN RAISE NOTICE 'Part 3a 완료: system 코칭 목표 삭제 (CASCADE: checkin/plan/retro 포함)'; END $$;

-- Step 3b: 학과별 맞춤 코칭 목표 3건/학생 INSERT

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
        WHEN 'nursing' THEN '간호학 전공 심화 학습'
        WHEN 'architecture' THEN '건축설계 전공 심화'
        WHEN 'business' THEN '경영학 전공 핵심 이수'
        WHEN 'arts' THEN '예술 전공 작품 완성'
        WHEN 'health' THEN '보건의료 전공 심화'
        WHEN 'pharmacy' THEN '약학 전공 학업 목표 달성'
        WHEN 'law_admin' THEN '법학/행정 전공 심화'
        WHEN 'education' THEN '교육학 전공 심화'
        WHEN 'humanities' THEN '인문학 전공 연구 심화'
        WHEN 'science' THEN '연구 역량 심화'
        WHEN 'chemical_env' THEN '연구 역량 심화'
        ELSE '전공 학업 우수 달성'
    END,
    '졸업 시까지 전공 GPA 3.5 이상 유지 및 핵심 과목 우수 성적 확보',
    'academic',
    'high',
    ((ts.admission_year + 4)::text || '-02-28')::date,
    ARRAY['전공지식', '학습능력', '자기주도학습'],
    '전공 GPA 3.5 이상 달성',
    '전문 분야 역량 강화를 위한 학업 기반 확립',
    CASE WHEN ts.h < 50 THEN 'completed' ELSE 'active' END,
    80 + abs(hashtext(ts.student_id || 'acad')) % 21,
    (ts.admission_year::text || '-03-15')::timestamp,
    CASE WHEN ts.h < 50 THEN ((ts.admission_year + 4)::text || '-02-20')::timestamp ELSE NULL END,
    'FIX_49',
    NOW()
FROM tmp_coaching_target_49 ts;

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
        WHEN 'nursing' THEN '간호 실무 역량 향상'
        WHEN 'architecture' THEN '건축 실무 역량 개발'
        WHEN 'business' THEN '비즈니스 실무 역량 개발'
        WHEN 'arts' THEN '창작 역량 심화'
        WHEN 'health' THEN '보건 실무 역량 개발'
        WHEN 'pharmacy' THEN '약물치료 전문성 개발'
        WHEN 'law_admin' THEN '법률 실무 역량 개발'
        WHEN 'education' THEN '교육·상담 실무 역량'
        WHEN 'humanities' THEN '학술 연구 역량 개발'
        WHEN 'science' THEN '실험·분석 역량 개발'
        WHEN 'chemical_env' THEN '실험·분석 역량 개발'
        ELSE '전문 역량 개발'
    END,
    '졸업 전 핵심 실무 역량 확보 및 자격증 취득',
    'skill',
    'medium',
    ((ts.admission_year + 3)::text || '-12-31')::date,
    ARRAY['실무능력', '자격증', '프로젝트경험'],
    '관련 자격증 1개 이상 취득 및 실무 프로젝트 완수',
    '취업 경쟁력 확보를 위한 실질적 역량 개발',
    CASE WHEN ts.h < 40 THEN 'completed' ELSE 'active' END,
    75 + abs(hashtext(ts.student_id || 'skill')) % 26,
    (ts.admission_year::text || '-09-01')::timestamp,
    CASE WHEN ts.h < 40 THEN ((ts.admission_year + 3)::text || '-12-15')::timestamp ELSE NULL END,
    'FIX_49',
    NOW()
FROM tmp_coaching_target_49 ts;

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
        WHEN 'nursing' THEN '종합병원 취업 준비'
        WHEN 'architecture' THEN '건축사사무소 취업 준비'
        WHEN 'business' THEN '대기업/컨설팅 취업 준비'
        WHEN 'arts' THEN '예술 분야 진출 준비'
        WHEN 'health' THEN '보건의료기관 취업 준비'
        WHEN 'pharmacy' THEN '약사 면허 및 취업 준비'
        WHEN 'law_admin' THEN '공공기관/법률사무소 취업 준비'
        WHEN 'education' THEN '교육기관 취업 준비'
        WHEN 'humanities' THEN '대학원/연구기관 진출 준비'
        WHEN 'science' THEN '연구소/기업 R&D 취업 준비'
        WHEN 'chemical_env' THEN '연구소/기업 R&D 취업 준비'
        ELSE '진로 설계 및 취업 준비'
    END,
    '졸업 후 진로 목표 달성을 위한 체계적 준비',
    'career',
    'high',
    ((ts.admission_year + 4)::text || '-06-30')::date,
    ARRAY['이력서작성', '면접준비', '직무분석'],
    '목표 기업/기관 취업 또는 진학 확정',
    '안정적인 사회 진출을 위한 준비',
    CASE WHEN ts.h < 30 THEN 'completed' ELSE 'active' END,
    70 + abs(hashtext(ts.student_id || 'career')) % 31,
    ((ts.admission_year + 1)::text || '-03-01')::timestamp,
    CASE WHEN ts.h < 30 THEN ((ts.admission_year + 4)::text || '-06-15')::timestamp ELSE NULL END,
    'FIX_49',
    NOW()
FROM tmp_coaching_target_49 ts;

DO $$ BEGIN RAISE NOTICE 'Part 3b 완료: 학과별 코칭 목표 생성 (% 건)',
    (SELECT count(*) FROM tb_coaching_goal WHERE ins_user_id = 'FIX_49');
END $$;

-- Step 3c: coaching_plan 2건/목표 INSERT (총 6건/학생)
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
    'FIX_49',
    NOW()
FROM tb_coaching_goal cg
JOIN tmp_coaching_target_49 ts ON cg.std_id = ts.student_id
CROSS JOIN generate_series(1, 2) AS rn
WHERE cg.ins_user_id = 'FIX_49';

DO $$ BEGIN RAISE NOTICE 'Part 3c 완료: coaching_plan 생성 (% 건)',
    (SELECT count(*) FROM tb_coaching_plan WHERE ins_user_id = 'FIX_49');
END $$;

-- Step 3d: coaching_checkin 4건/목표 INSERT (총 12건/학생)
INSERT INTO tb_coaching_checkin (
    checkin_id, goal_id, mood, progress_note, blockers,
    next_steps, reflection, ai_feedback, ai_suggestions,
    created_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    cg.goal_id,
    CASE (abs(hashtext(cg.goal_id::text || ci_num::text)) % 10)
        WHEN 0 THEN 'great'
        WHEN 1 THEN 'great'
        WHEN 2 THEN 'good'
        WHEN 3 THEN 'good'
        WHEN 4 THEN 'good'
        WHEN 5 THEN 'neutral'
        WHEN 6 THEN 'neutral'
        WHEN 7 THEN 'neutral'
        WHEN 8 THEN 'struggling'
        ELSE 'good'
    END,
    CASE ci_num
        WHEN 1 THEN '목표를 설정하고 초기 계획을 수립했습니다. 관련 자료를 수집하기 시작했습니다.'
        WHEN 2 THEN '중간 점검 단계입니다. 계획대로 진행 중이며, 일부 조정이 필요합니다.'
        WHEN 3 THEN '상당한 진전이 있었습니다. 핵심 마일스톤을 달성했습니다.'
        ELSE '최종 점검입니다. 대부분의 목표를 달성했으며, 마무리 작업 중입니다.'
    END,
    CASE WHEN abs(hashtext(cg.goal_id::text || ci_num::text || 'b')) % 3 = 0
         THEN CASE ci_num
              WHEN 1 THEN '시간 관리가 어렵습니다.'
              WHEN 2 THEN '관련 자원 접근이 제한적입니다.'
              WHEN 3 THEN '다른 과목과 일정이 겹칩니다.'
              ELSE NULL END
         ELSE NULL END,
    CASE ci_num
        WHEN 1 THEN '세부 실행 계획 수립 및 1차 목표 달성'
        WHEN 2 THEN '중간 성과 검토 및 계획 수정'
        WHEN 3 THEN '최종 목표 향한 집중 실행'
        ELSE '성과 정리 및 회고 준비'
    END,
    CASE ci_num
        WHEN 1 THEN '시작이 반이라는 말처럼 첫 발을 내딛었습니다.'
        WHEN 2 THEN '예상보다 진행이 순조롭습니다. 꾸준함이 중요합니다.'
        WHEN 3 THEN '어려운 부분도 있었지만 성장을 느낍니다.'
        ELSE '전체 과정을 돌아보며 많은 것을 배웠습니다.'
    END,
    CASE ci_num
        WHEN 1 THEN '좋은 출발입니다. 구체적인 일정표를 작성하면 실행력이 높아집니다.'
        WHEN 2 THEN '꾸준한 노력이 돋보입니다. 작은 성과를 축하하며 동기를 유지하세요.'
        WHEN 3 THEN '핵심 역량이 성장하고 있습니다. 남은 기간 집중하면 목표 달성이 가능합니다.'
        ELSE '훌륭한 여정이었습니다. 이 경험을 바탕으로 다음 단계를 계획하세요.'
    END,
    CASE ci_num
        WHEN 1 THEN ARRAY['주간 목표를 설정하세요', '관련 스터디 그룹에 참여하세요']
        WHEN 2 THEN ARRAY['진행 상황을 시각화하세요', '멘토와 상담을 예약하세요']
        WHEN 3 THEN ARRAY['포트폴리오에 성과를 기록하세요', '부족한 부분을 집중 보강하세요']
        ELSE ARRAY['회고를 통해 교훈을 정리하세요', '다음 목표를 구상하세요']
    END,
    cg.created_at + (ci_num * INTERVAL '4 weeks'),
    'FIX_49',
    NOW()
FROM tmp_coaching_target_49 ts
JOIN tb_coaching_goal cg ON cg.std_id = ts.student_id AND cg.ins_user_id = 'FIX_49'
CROSS JOIN generate_series(1, 4) AS ci_num;

DO $$ BEGIN RAISE NOTICE 'Part 3d 완료: coaching_checkin 생성 (% 건)',
    (SELECT count(*) FROM tb_coaching_checkin WHERE ins_user_id = 'FIX_49');
END $$;

-- Step 3e: completed 목표에 대한 coaching_retrospective INSERT
INSERT INTO tb_coaching_retrospective (
    retrospective_id, goal_id, what_went_well, what_could_improve,
    lessons_learned, next_goals, satisfaction_rating,
    ai_analysis, ai_recommendations,
    created_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    cg.goal_id,
    CASE cg.goal_type
        WHEN 'academic' THEN '전공 과목에서 목표 성적을 달성했습니다. 체계적인 학습 계획이 효과적이었습니다.'
        WHEN 'skill' THEN '핵심 실무 역량을 개발했습니다. 자격증 취득과 프로젝트 경험이 쌓였습니다.'
        WHEN 'career' THEN '목표 직군에 대한 이해도가 높아졌습니다. 인턴십 경험이 큰 도움이 되었습니다.'
        ELSE '목표한 바를 대부분 달성했습니다.'
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN '시간 관리를 더 효율적으로 해야 합니다. 일부 과목에서 추가 학습이 필요합니다.'
        WHEN 'skill' THEN '실습 시간을 더 확보하고, 다양한 프로젝트에 참여할 필요가 있습니다.'
        WHEN 'career' THEN '네트워킹 활동을 더 적극적으로 하고, 면접 준비를 체계화해야 합니다.'
        ELSE '시간 배분과 우선순위 설정을 개선할 수 있습니다.'
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN '꾸준한 학습이 가장 중요하다는 것을 배웠습니다.'
        WHEN 'skill' THEN '이론과 실습의 균형이 중요합니다. 실제 프로젝트 경험이 가장 큰 학습입니다.'
        WHEN 'career' THEN '명확한 목표 설정과 단계적 접근이 효과적입니다.'
        ELSE '목표를 세분화하고 지속적으로 점검하는 것이 성공의 열쇠입니다.'
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN '대학원 진학 또는 전문 분야 심화 학습 계획 수립'
        WHEN 'skill' THEN '전문 자격증 추가 취득 및 실무 역량 고도화'
        WHEN 'career' THEN '취업 후 1년 내 핵심 역량 확보 및 커리어 개발'
        ELSE '졸업 후 커리어 목표 달성을 위한 구체적 계획 수립'
    END,
    3 + abs(hashtext(cg.goal_id::text || 'sat')) % 3,
    '목표 달성 과정에서 지속적인 노력과 체계적인 접근이 돋보였습니다. 특히 중간 점검을 통한 계획 수정이 효과적이었습니다.',
    ARRAY[
        '달성한 성과를 포트폴리오에 체계적으로 정리하세요',
        '관련 분야 전문가와 네트워킹을 지속하세요',
        '다음 목표를 SMART 기준으로 설정하세요'
    ],
    COALESCE(cg.completed_at, cg.created_at + INTERVAL '6 months'),
    'FIX_49',
    NOW()
FROM tmp_coaching_target_49 ts
JOIN tb_coaching_goal cg ON cg.std_id = ts.student_id
WHERE cg.ins_user_id = 'FIX_49'
  AND cg.status = 'completed';

DO $$ BEGIN RAISE NOTICE 'Part 3e 완료: coaching_retrospective 생성 (% 건)',
    (SELECT count(*) FROM tb_coaching_retrospective WHERE ins_user_id = 'FIX_49');
END $$;


-- =====================================================
-- Cleanup
-- =====================================================

DROP TABLE IF EXISTS tmp_sim_data_49;
DROP TABLE IF EXISTS tmp_coaching_target_49;
DROP TABLE IF EXISTS tmp_dept_cat_49;
DROP TABLE IF EXISTS tmp_showcase_49;


-- =====================================================
-- 검증 쿼리
-- =====================================================

DO $$ BEGIN RAISE NOTICE '===== 검증 시작 ====='; END $$;

-- 검증 1: system 시뮬레이션 시나리오 0건 확인
DO $$
DECLARE cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM tb_simulation_scenario
    WHERE student_id IN (
        '2021A143','20203008','20203033','20201861','20202956','20201481','20202999','20201478',
        '20201499','20201333','20201341','20202487','20202493','20202510','20214632','2020A066',
        '2021A060','2021A056','2021A146','20214314','20214364','20202733','20202883','20202887',
        '20202924','20202333','20201265','20214819','20201126','20201132','20202358','20202362',
        '20202364','20202379','20202722','20214353','20201220','20214383','20201352','20201882'
    ) AND ins_user_id = 'system';
    RAISE NOTICE '검증 1 - system 시뮬레이션: % 건 (예상: 0)', cnt;
END $$;

-- 검증 2: FIX_49 시뮬레이션 시나리오 수
DO $$
DECLARE cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM tb_simulation_scenario
    WHERE ins_user_id = 'FIX_49';
    RAISE NOTICE '검증 2 - FIX_49 시뮬레이션: % 건 (예상: 120 = 40명 × 3)', cnt;
END $$;

-- 검증 3: system IT 스킬 0건 확인 (비IT 학생)
DO $$
DECLARE cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM tb_student_skill
    WHERE student_id IN (
        '2021A143','20203008','20203033','20201861','20202956','20201481','20202999','20201478',
        '20201499','20201333','20201341','20202487','20202493','20202510','20214632','2020A066',
        '2021A060','2021A056','2021A146','20214314','20214364','20202733','20202883','20202887',
        '20202924','20202333','20201265','20214819','20201126','20201132','20202358','20202362',
        '20202364','20202379','20202722','20214353','20201220','20214383','20201352','20201882'
    ) AND ins_user_id = 'system'
      AND skill_cd IN ('SK01','SK02','SK03','SK04','SK05','SK06','SK07','SK08');
    RAISE NOTICE '검증 3 - system IT 스킬 (비IT): % 건 (예상: 0)', cnt;
END $$;

-- 검증 4: system 코칭 목표 0건 확인
DO $$
DECLARE cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM tb_coaching_goal
    WHERE std_id IN (
        '20203008','20201861','20202956','20201481','20202999','20201478','20201499',
        '20201333','20201341','20202487','20202493','20202510','2021A056','2021A146',
        '20214314','20202883','20202887','20202924','20201265','20201132',
        '20202358','20202362','20202364','20202379'
    ) AND (ins_user_id = 'system' OR ins_user_id = 'SYSTEM');
    RAISE NOTICE '검증 4 - system 코칭 목표: % 건 (예상: 0)', cnt;
END $$;

-- 검증 5: FIX_49 코칭 목표 수
DO $$
DECLARE cnt INT;
BEGIN
    SELECT count(*) INTO cnt FROM tb_coaching_goal WHERE ins_user_id = 'FIX_49';
    RAISE NOTICE '검증 5 - FIX_49 코칭 목표: % 건 (예상: 72 = 24명 × 3)', cnt;
END $$;

-- 검증 6: coaching cascade 확인 (plan, checkin, retro)
DO $$
DECLARE plan_cnt INT; checkin_cnt INT; retro_cnt INT;
BEGIN
    SELECT count(*) INTO plan_cnt FROM tb_coaching_plan WHERE ins_user_id = 'FIX_49';
    SELECT count(*) INTO checkin_cnt FROM tb_coaching_checkin WHERE ins_user_id = 'FIX_49';
    SELECT count(*) INTO retro_cnt FROM tb_coaching_retrospective WHERE ins_user_id = 'FIX_49';
    RAISE NOTICE '검증 6 - FIX_49 plan: % 건, checkin: % 건, retro: % 건', plan_cnt, checkin_cnt, retro_cnt;
END $$;

-- 검증 7: 샘플 학생 시나리오 확인
DO $$ BEGIN RAISE NOTICE '검증 7 - 샘플 학생 시나리오:'; END $$;
SELECT s.student_id, dc.department_nm, ss.title, ss.scenario_type
FROM tb_simulation_scenario ss
JOIN tb_student s ON ss.student_id = s.student_id
JOIN tb_department dc ON s.department_cd = dc.department_cd
WHERE s.student_id IN ('20203008','20201481','20201333','20202358')
  AND ss.ins_user_id = 'FIX_49'
ORDER BY dc.department_nm, ss.scenario_type;

-- 검증 8: 샘플 학생 코칭 목표 확인
DO $$ BEGIN RAISE NOTICE '검증 8 - 샘플 학생 코칭 목표:'; END $$;
SELECT s.student_id, dc.department_nm, cg.title, cg.goal_type, cg.status
FROM tb_coaching_goal cg
JOIN tb_student s ON cg.std_id = s.student_id
JOIN tb_department dc ON s.department_cd = dc.department_cd
WHERE s.student_id IN ('20203008','20201481','20201333','20202358')
  AND cg.ins_user_id = 'FIX_49'
ORDER BY dc.department_nm, cg.goal_type;

DO $$ BEGIN RAISE NOTICE '===== 49_fix_showcase_data.sql 실행 완료 ====='; END $$;

COMMIT;
