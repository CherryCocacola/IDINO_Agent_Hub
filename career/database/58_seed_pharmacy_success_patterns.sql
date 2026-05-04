-- 58_seed_pharmacy_success_patterns.sql
-- 약학 전용 성공 패턴 추가
-- Issue: 약학생에게 공학 성공 패턴(기계공학자, 전기전자공학자)이 표시됨
-- Root cause: DB에 약학 패턴이 없어 fallback으로 다른 학과 패턴이 매칭

SET search_path TO idino_career;

-- 1. 필요한 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, use_fg, ins_user_id, ins_dt)
VALUES ('ROLE604', '제약연구원', 'Pharmaceutical Researcher', '의약', '제약회사에서 신약 개발 및 약물 연구를 수행하는 연구원', 'Y', 'SYSTEM', NOW())
ON CONFLICT (role_cd) DO NOTHING;

INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, use_fg, ins_user_id, ins_dt)
VALUES ('ROLE605', '임상약사', 'Clinical Pharmacist', '의약', '병원에서 의료진과 협력하여 약물치료를 최적화하는 약사', 'Y', 'SYSTEM', NOW())
ON CONFLICT (role_cd) DO NOTHING;

-- 2. 약학 관련 학과에 성공 패턴 삽입
-- 약사 패턴 (role_cd = ROLE105, 기존 약사 역할)
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(), '약사 커리어 패턴', 'career', d.department_cd, 'ROLE105',
    '약사 국가고시 합격 후 병원약국 또는 지역약국에서 근무하는 경로입니다. 약학대학 6년제 과정을 이수하고, 조제 및 복약지도 역량을 갖추어야 합니다.',
    '3.5-4.2',
    ARRAY['약리학', '약제학', '생약학', '임상약학', '약물동태학', '약사법규'],
    ARRAY['약사 국가고시 합격', '병원약국 실습', '지역약국 실습', '약학 연구 프로젝트'],
    ARRAY['조제', '복약지도', '의약품정보', '약물상호작용분석', '임상약학'],
    '{"1-2학년": "기초과학 및 약학개론", "3학년": "전공심화 및 조제실습", "4학년": "임상실습 및 국시준비", "졸업후": "약사면허 취득 및 취업"}'::jsonb,
    87.50, 160, 'SYSTEM', NOW()
FROM tb_department d WHERE d.department_nm ~ '약학|제약';

-- 제약연구원 패턴 (role_cd = ROLE604)
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(), '제약연구원 커리어 패턴', 'career', d.department_cd, 'ROLE604',
    '제약회사 연구소에서 신약 개발 및 약물 연구를 수행하는 경로입니다. 약학 전공 지식과 함께 연구 방법론 및 실험 역량이 필요합니다.',
    '3.7-4.3',
    ARRAY['약리학', '약품분석학', '생물약제학', '분자생물학', '통계학', '약물설계'],
    ARRAY['제약회사 인턴십', '연구실 참여', '학술논문 발표', '약학 학회 참가'],
    ARRAY['신약개발', '약물분석', '실험설계', '데이터분석', 'GLP/GMP'],
    '{"1-2학년": "기초과학 및 연구방법론", "3학년": "전공심화 및 연구실 참여", "4학년": "졸업연구 및 인턴십", "졸업후": "대학원 또는 제약사 취업"}'::jsonb,
    74.20, 85, 'SYSTEM', NOW()
FROM tb_department d WHERE d.department_nm ~ '약학|제약';

-- 임상약사 패턴 (role_cd = ROLE605)
INSERT INTO tb_success_pattern (
    pattern_id, pattern_nm, pattern_type, department_cd, role_cd,
    description, typical_gpa_range, key_courses, key_activities,
    key_skills, timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(), '임상약사 커리어 패턴', 'career', d.department_cd, 'ROLE605',
    '병원에서 의료진과 협력하여 약물치료를 최적화하는 임상약사 경로입니다. 임상약학 심화 과정과 병원 실습 경험이 핵심입니다.',
    '3.6-4.2',
    ARRAY['임상약학', '약물치료학', '병태생리학', '약동학', '약물역학', '의약품안전관리'],
    ARRAY['약사 국가고시 합격', '대학병원 임상실습', '임상약학 레지던시', '약물안전 모니터링'],
    ARRAY['약물치료 자문', 'TDM', '의약품부작용모니터링', '다학제팀 협력', '환자교육'],
    '{"1-2학년": "기초약학 및 임상기초", "3학년": "임상약학 심화", "4학년": "병원실습 및 국시준비", "졸업후": "임상약학 레지던시 또는 병원약사"}'::jsonb,
    79.80, 95, 'SYSTEM', NOW()
FROM tb_department d WHERE d.department_nm ~ '약학|제약';
