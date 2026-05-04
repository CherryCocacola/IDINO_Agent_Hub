-- ============================================
-- IDINO Career - Complete Seed Data Fix & Extension
-- Date: 2026-01-26
-- Purpose: Fix student_id mismatches and run all seed data
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- STEP 1: Fix UNIV01 -> UNIV001 in 2025 students
-- ============================================

-- Check if 2025 students exist with UNIV01 and update
UPDATE tb_student
SET university_cd = 'UNIV001'
WHERE university_cd = 'UNIV01' AND admission_year = 2025;

-- ============================================
-- STEP 2: Insert 2025 students if not exist
-- ============================================

INSERT INTO tb_student (student_id, student_nm, university_cd, department_cd, admission_year, current_grade, current_semester, email, phone, birth_date, gender, status, career_goal, ins_user_id, ins_dt) VALUES
-- Computer Science (DEPT001) - 8 students
('2025010001', '김현서', 'UNIV001', 'DEPT001', 2025, 1, 1, 'hyunseo.kim25@kstu.ac.kr', '010-2501-0001', '2006-03-15', 'F', 'enrolled', 'AI엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010002', '이도윤', 'UNIV001', 'DEPT001', 2025, 1, 1, 'doyun.lee25@kstu.ac.kr', '010-2501-0002', '2006-05-22', 'M', 'enrolled', '백엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010003', '박서연', 'UNIV001', 'DEPT001', 2025, 1, 1, 'seoyeon.park25@kstu.ac.kr', '010-2501-0003', '2006-08-10', 'F', 'enrolled', '데이터사이언티스트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010004', '최민재', 'UNIV001', 'DEPT001', 2025, 1, 1, 'minjae.choi25@kstu.ac.kr', '010-2501-0004', '2006-01-28', 'M', 'enrolled', '풀스택개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010005', '정하은', 'UNIV001', 'DEPT001', 2025, 1, 1, 'haeun.jung25@kstu.ac.kr', '010-2501-0005', '2006-04-05', 'F', 'enrolled', '보안전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010006', '강준호', 'UNIV001', 'DEPT001', 2025, 1, 1, 'junho.kang25@kstu.ac.kr', '010-2501-0006', '2006-07-12', 'M', 'enrolled', 'DevOps엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010007', '윤서아', 'UNIV001', 'DEPT001', 2025, 1, 1, 'seoa.yoon25@kstu.ac.kr', '010-2501-0007', '2006-02-18', 'F', 'enrolled', 'ML엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010008', '임지훈', 'UNIV001', 'DEPT001', 2025, 1, 1, 'jihoon.lim25@kstu.ac.kr', '010-2501-0008', '2006-06-25', 'M', 'enrolled', '클라우드엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),

-- Software Engineering (DEPT002) - 6 students
('2025020001', '한지민', 'UNIV001', 'DEPT002', 2025, 1, 1, 'jimin.han25@kstu.ac.kr', '010-2502-0001', '2006-02-14', 'F', 'enrolled', '프론트엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020002', '오승현', 'UNIV001', 'DEPT002', 2025, 1, 1, 'seunghyun.oh25@kstu.ac.kr', '010-2502-0002', '2006-04-28', 'M', 'enrolled', '모바일개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020003', '배수빈', 'UNIV001', 'DEPT002', 2025, 1, 1, 'subin.bae25@kstu.ac.kr', '010-2502-0003', '2006-03-19', 'F', 'enrolled', 'UX엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020004', '황민서', 'UNIV001', 'DEPT002', 2025, 1, 1, 'minseo.hwang25@kstu.ac.kr', '010-2502-0004', '2006-06-07', 'M', 'enrolled', '백엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020005', '문채원', 'UNIV001', 'DEPT002', 2025, 1, 1, 'chaewon.moon25@kstu.ac.kr', '010-2502-0005', '2006-01-11', 'F', 'enrolled', 'QA엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020006', '송도현', 'UNIV001', 'DEPT002', 2025, 1, 1, 'dohyun.song25@kstu.ac.kr', '010-2502-0006', '2006-04-23', 'M', 'enrolled', '프론트엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),

-- Electronics (DEPT003) - 5 students
('2025030001', '신예린', 'UNIV001', 'DEPT003', 2025, 1, 1, 'yerin.shin25@kstu.ac.kr', '010-2503-0001', '2006-01-20', 'F', 'enrolled', 'IoT엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030002', '김태윤', 'UNIV001', 'DEPT003', 2025, 1, 1, 'taeyun.kim25@kstu.ac.kr', '010-2503-0002', '2006-06-13', 'M', 'enrolled', '반도체엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030003', '이나연', 'UNIV001', 'DEPT003', 2025, 1, 1, 'nayeon.lee25@kstu.ac.kr', '010-2503-0003', '2006-02-25', 'F', 'enrolled', '임베디드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030004', '박건우', 'UNIV001', 'DEPT003', 2025, 1, 1, 'gunwoo.park25@kstu.ac.kr', '010-2503-0004', '2006-05-18', 'M', 'enrolled', '통신엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030005', '최서윤', 'UNIV001', 'DEPT003', 2025, 1, 1, 'seoyun.choi25@kstu.ac.kr', '010-2503-0005', '2006-03-07', 'F', 'enrolled', 'HW엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),

-- Business Administration (DEPT014) - 6 students
('2025140001', '정유나', 'UNIV001', 'DEPT014', 2025, 1, 1, 'yuna.jung25@kstu.ac.kr', '010-2514-0001', '2006-02-28', 'F', 'enrolled', '경영컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140002', '강민준', 'UNIV001', 'DEPT014', 2025, 1, 1, 'minjun.kang25@kstu.ac.kr', '010-2514-0002', '2006-05-10', 'M', 'enrolled', '마케팅전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140003', '윤서영', 'UNIV001', 'DEPT014', 2025, 1, 1, 'seoyoung.yoon25@kstu.ac.kr', '010-2514-0003', '2006-01-15', 'F', 'enrolled', '재무분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140004', '임재현', 'UNIV001', 'DEPT014', 2025, 1, 1, 'jaehyun.lim25@kstu.ac.kr', '010-2514-0004', '2006-04-22', 'M', 'enrolled', '제품관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140005', '한소희', 'UNIV001', 'DEPT014', 2025, 1, 1, 'sohee.han25@kstu.ac.kr', '010-2514-0005', '2006-02-08', 'F', 'enrolled', 'HR전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140006', '오준서', 'UNIV001', 'DEPT014', 2025, 1, 1, 'junseo.oh25@kstu.ac.kr', '010-2514-0006', '2006-06-30', 'M', 'enrolled', '스타트업창업', 'SYSTEM', CURRENT_TIMESTAMP),

-- Statistics (DEPT013) - 5 students
('2025130001', '서지우', 'UNIV001', 'DEPT013', 2025, 1, 1, 'jiwoo.seo25@kstu.ac.kr', '010-2513-0001', '2006-01-08', 'F', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130002', '이현우', 'UNIV001', 'DEPT013', 2025, 1, 1, 'hyunwoo.lee25@kstu.ac.kr', '010-2513-0002', '2006-04-15', 'M', 'enrolled', 'AI엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130003', '박소연', 'UNIV001', 'DEPT013', 2025, 1, 1, 'soyeon.park25@kstu.ac.kr', '010-2513-0003', '2006-03-22', 'F', 'enrolled', '데이터사이언티스트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130004', '김도현', 'UNIV001', 'DEPT013', 2025, 1, 1, 'dohyun.kim25@kstu.ac.kr', '010-2513-0004', '2006-06-28', 'M', 'enrolled', '퀀트분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130005', '최예원', 'UNIV001', 'DEPT013', 2025, 1, 1, 'yewon.choi25@kstu.ac.kr', '010-2513-0005', '2006-01-05', 'F', 'enrolled', '통계컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),

-- Industrial Engineering (DEPT006) - 5 students
('2025060001', '장민석', 'UNIV001', 'DEPT006', 2025, 1, 1, 'minseok.jang25@kstu.ac.kr', '010-2506-0001', '2006-03-25', 'M', 'enrolled', '품질관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060002', '김하린', 'UNIV001', 'DEPT006', 2025, 1, 1, 'harin.kim25@kstu.ac.kr', '010-2506-0002', '2006-07-18', 'F', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060003', '이준영', 'UNIV001', 'DEPT006', 2025, 1, 1, 'junyoung.lee25@kstu.ac.kr', '010-2506-0003', '2006-02-14', 'M', 'enrolled', '프로젝트관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060004', '박서현', 'UNIV001', 'DEPT006', 2025, 1, 1, 'seohyun.park25@kstu.ac.kr', '010-2506-0004', '2006-05-30', 'F', 'enrolled', '컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060005', '최우진', 'UNIV001', 'DEPT006', 2025, 1, 1, 'woojin.choi25@kstu.ac.kr', '010-2506-0005', '2006-04-10', 'M', 'enrolled', '생산관리자', 'SYSTEM', CURRENT_TIMESTAMP),

-- Design (DEPT025) - 5 students
('2025250001', '윤채아', 'UNIV001', 'DEPT025', 2025, 1, 1, 'chaea.yoon25@kstu.ac.kr', '010-2525-0001', '2006-02-05', 'F', 'enrolled', 'UX디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250002', '임동훈', 'UNIV001', 'DEPT025', 2025, 1, 1, 'donghun.lim25@kstu.ac.kr', '010-2525-0002', '2006-06-20', 'M', 'enrolled', '제품디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250003', '한지연', 'UNIV001', 'DEPT025', 2025, 1, 1, 'jiyeon.han25@kstu.ac.kr', '010-2525-0003', '2006-01-28', 'F', 'enrolled', 'UI디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250004', '오승민', 'UNIV001', 'DEPT025', 2025, 1, 1, 'seungmin.oh25@kstu.ac.kr', '010-2525-0004', '2006-04-15', 'M', 'enrolled', '브랜드디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250005', '배수아', 'UNIV001', 'DEPT025', 2025, 1, 1, 'sua.bae25@kstu.ac.kr', '010-2525-0005', '2006-03-10', 'F', 'enrolled', '그래픽디자이너', 'SYSTEM', CURRENT_TIMESTAMP),

-- Psychology (DEPT023) - 4 students
('2025230001', '김다은', 'UNIV001', 'DEPT023', 2025, 1, 1, 'daeun.kim25@kstu.ac.kr', '010-2523-0001', '2006-01-12', 'F', 'enrolled', 'UX리서처', 'SYSTEM', CURRENT_TIMESTAMP),
('2025230002', '이정민', 'UNIV001', 'DEPT023', 2025, 1, 1, 'jungmin.lee25@kstu.ac.kr', '010-2523-0002', '2006-05-28', 'M', 'enrolled', 'HR담당자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025230003', '박시현', 'UNIV001', 'DEPT023', 2025, 1, 1, 'sihyun.park25@kstu.ac.kr', '010-2523-0003', '2006-02-08', 'F', 'enrolled', '상담심리사', 'SYSTEM', CURRENT_TIMESTAMP),
('2025230004', '최재훈', 'UNIV001', 'DEPT023', 2025, 1, 1, 'jaehoon.choi25@kstu.ac.kr', '010-2523-0004', '2006-06-15', 'M', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),

-- Mechanical Engineering (DEPT004) - 4 students
('2025040001', '정승우', 'UNIV001', 'DEPT004', 2025, 1, 1, 'seungwoo.jung25@kstu.ac.kr', '010-2504-0001', '2006-01-28', 'M', 'enrolled', '자동차엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025040002', '강민지', 'UNIV001', 'DEPT004', 2025, 1, 1, 'minji.kang25@kstu.ac.kr', '010-2504-0002', '2006-04-10', 'F', 'enrolled', '로봇엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025040003', '윤태호', 'UNIV001', 'DEPT004', 2025, 1, 1, 'taeho.yoon25@kstu.ac.kr', '010-2504-0003', '2006-08-22', 'M', 'enrolled', '에너지엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025040004', '임서연', 'UNIV001', 'DEPT004', 2025, 1, 1, 'seoyeon.lim25@kstu.ac.kr', '010-2504-0004', '2006-03-18', 'F', 'enrolled', '항공엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),

-- Physics (DEPT010) - 3 students
('2025100001', '김준혁', 'UNIV001', 'DEPT010', 2025, 1, 1, 'junhyuk.kim25@kstu.ac.kr', '010-2510-0001', '2006-03-10', 'M', 'enrolled', '양자컴퓨팅연구원', 'SYSTEM', CURRENT_TIMESTAMP),
('2025100002', '이서진', 'UNIV001', 'DEPT010', 2025, 1, 1, 'seojin.lee25@kstu.ac.kr', '010-2510-0002', '2006-01-25', 'F', 'enrolled', '광학엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025100003', '박현준', 'UNIV001', 'DEPT010', 2025, 1, 1, 'hyunjun.park25@kstu.ac.kr', '010-2510-0003', '2006-02-15', 'M', 'enrolled', '연구원', 'SYSTEM', CURRENT_TIMESTAMP),

-- Mathematics (DEPT009) - 3 students
('2025090001', '최예진', 'UNIV001', 'DEPT009', 2025, 1, 1, 'yejin.choi25@kstu.ac.kr', '010-2509-0001', '2006-02-18', 'F', 'enrolled', '퀀트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025090002', '정민규', 'UNIV001', 'DEPT009', 2025, 1, 1, 'mingyu.jung25@kstu.ac.kr', '010-2509-0002', '2006-06-25', 'M', 'enrolled', '데이터사이언티스트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025090003', '한소율', 'UNIV001', 'DEPT009', 2025, 1, 1, 'soyul.han25@kstu.ac.kr', '010-2509-0003', '2006-03-12', 'F', 'enrolled', '암호학연구원', 'SYSTEM', CURRENT_TIMESTAMP)

ON CONFLICT (student_id) DO NOTHING;

-- ============================================
-- STEP 3: Insert cumulative summary for 2025 students
-- ============================================

INSERT INTO tb_cumulative_summary (student_id, total_credits_earned, major_credits_earned, liberal_credits_earned, cumulative_gpa, major_gpa, completion_rate, ins_user_id, ins_dt)
SELECT
    student_id,
    FLOOR(0 + RANDOM() * 10) as total_credits_earned,
    FLOOR(0 + RANDOM() * 5) as major_credits_earned,
    FLOOR(0 + RANDOM() * 3) as liberal_credits_earned,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as cumulative_gpa,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as major_gpa,
    ROUND((0 + RANDOM() * 8)::numeric, 1) as completion_rate,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE admission_year = 2025
AND student_id NOT IN (SELECT student_id FROM tb_cumulative_summary);

-- ============================================
-- STEP 4: Insert student competencies for 2025 students
-- ============================================

INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    c.competency_cd,
    ROUND((30 + RANDOM() * 40)::numeric, 1) as current_score,
    85 as target_score,
    0 as gap_score,
    CASE
        WHEN RANDOM() < 0.1 THEN 'good'
        WHEN RANDOM() < 0.3 THEN 'average'
        WHEN RANDOM() < 0.6 THEN 'improve'
        ELSE 'focus'
    END as status,
    CASE
        WHEN RANDOM() < 0.5 THEN 'up'
        WHEN RANDOM() < 0.8 THEN 'stable'
        ELSE 'down'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_competency c
WHERE s.admission_year = 2025
AND NOT EXISTS (
    SELECT 1 FROM tb_student_competency sc
    WHERE sc.student_id = s.student_id AND sc.competency_cd = c.competency_cd
);

-- Update gap_score
UPDATE tb_student_competency sc
SET gap_score = sc.current_score - sc.target_score
FROM tb_student s
WHERE sc.student_id = s.student_id
AND s.admission_year = 2025;

-- ============================================
-- STEP 5: Insert Achievement Data (Fixed student_ids)
-- ============================================

-- Delete existing achievement data with wrong student_ids
DELETE FROM tb_achievement WHERE ins_user_id = 'SYSTEM';

-- Insert achievements with correct student_id format
INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, competency_contributions, verified, ins_user_id, ins_dt) VALUES
-- DEPT001 (Computer Science) Certificates
('2021010001', 'certificate', '정보처리기사', '한국산업인력공단', '2024-06-15', NULL, '기사', NULL, '{"technical": 0.3, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'certificate', 'SQLD (SQL 개발자)', '한국데이터산업진흥원', '2024-03-20', NULL, '전문가', NULL, '{"technical": 0.25, "data_analysis": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'certificate', 'AWS Solutions Architect Associate', 'Amazon Web Services', '2024-09-10', '2027-09-10', 'Associate', NULL, '{"technical": 0.35, "cloud": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'certificate', '정보처리산업기사', '한국산업인력공단', '2024-11-20', NULL, '산업기사', NULL, '{"technical": 0.2, "problem_solving": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010002', 'certificate', '리눅스마스터 2급', '한국정보통신진흥협회', '2024-05-15', NULL, '2급', NULL, '{"technical": 0.2, "system": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010001', 'certificate', '네트워크관리사 2급', '한국정보통신자격협회', '2024-08-10', NULL, '2급', NULL, '{"technical": 0.15, "network": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010002', 'certificate', 'ADSP (데이터분석 준전문가)', '한국데이터산업진흥원', '2025-01-15', NULL, '준전문가', NULL, '{"technical": 0.2, "data_analysis": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024010001', 'certificate', 'ITQ 엑셀 A등급', '한국생산성본부', '2024-09-20', NULL, 'A등급', NULL, '{"digital_literacy": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT002 (Software Engineering) Certificates
('2021020001', 'certificate', '정보처리기사', '한국산업인력공단', '2024-05-10', NULL, '기사', NULL, '{"technical": 0.3, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', 'certificate', 'OCJP (Oracle Certified Java Programmer)', 'Oracle', '2024-07-25', NULL, 'Professional', NULL, '{"technical": 0.35, "java": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020001', 'certificate', 'Kubernetes Administrator (CKA)', 'CNCF', '2024-10-15', '2027-10-15', 'Administrator', NULL, '{"technical": 0.4, "devops": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020002', 'certificate', 'AWS Developer Associate', 'Amazon Web Services', '2024-08-20', '2027-08-20', 'Associate', NULL, '{"technical": 0.3, "cloud": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023020001', 'certificate', 'SQLD (SQL 개발자)', '한국데이터산업진흥원', '2025-01-10', NULL, '전문가', NULL, '{"technical": 0.25, "data_analysis": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024020001', 'certificate', '컴퓨터활용능력 1급', '대한상공회의소', '2024-11-05', NULL, '1급', NULL, '{"digital_literacy": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT003 (Electronics) Certificates
('2021030001', 'certificate', '전기기사', '한국산업인력공단', '2024-06-20', NULL, '기사', NULL, '{"technical": 0.35, "electrical": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021030002', 'certificate', '전자기사', '한국산업인력공단', '2024-05-15', NULL, '기사', NULL, '{"technical": 0.35, "electronics": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022030001', 'certificate', '임베디드SW개발전문가', 'TTA', '2024-09-10', NULL, '전문가', NULL, '{"technical": 0.3, "embedded": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023030001', 'certificate', '전기산업기사', '한국산업인력공단', '2024-11-15', NULL, '산업기사', NULL, '{"technical": 0.25, "electrical": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT014 (Business Administration) Certificates
('2021140001', 'certificate', '경영지도사', '한국산업인력공단', '2024-07-10', NULL, '지도사', NULL, '{"business": 0.4, "management": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140002', 'certificate', 'AFPK (재무설계사)', '한국FPSB', '2024-08-20', NULL, 'AFPK', NULL, '{"finance": 0.35, "planning": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022140001', 'certificate', 'ERP정보관리사 회계', '한국생산성본부', '2024-06-15', NULL, '1급', NULL, '{"accounting": 0.3, "erp": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023140001', 'certificate', '전산세무 2급', '한국세무사회', '2024-12-10', NULL, '2급', NULL, '{"accounting": 0.25, "tax": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT013 (Statistics) Certificates
('2021130001', 'certificate', '빅데이터분석기사', '한국데이터산업진흥원', '2024-09-05', NULL, '기사', NULL, '{"data_analysis": 0.4, "statistics": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022130001', 'certificate', 'ADsP (데이터분석 준전문가)', '한국데이터산업진흥원', '2024-03-20', NULL, '준전문가', NULL, '{"data_analysis": 0.25, "statistics": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023130001', 'certificate', '사회조사분석사 2급', '한국산업인력공단', '2024-11-20', NULL, '2급', NULL, '{"research": 0.25, "statistics": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT006 (Industrial Engineering) Certificates
('2021060001', 'certificate', '기계설계기사', '한국산업인력공단', '2024-06-25', NULL, '기사', NULL, '{"technical": 0.35, "mechanical": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022060001', 'certificate', '일반기계기사', '한국산업인력공단', '2024-08-15', NULL, '기사', NULL, '{"technical": 0.3, "mechanical": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023060001', 'certificate', 'AutoCAD 국제자격증', 'Autodesk', '2024-05-10', NULL, 'Professional', NULL, '{"technical": 0.2, "cad": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- 2025 Students Certificates
('2025010001', 'certificate', 'ITQ 한글 A등급', '한국생산성본부', '2025-01-10', NULL, 'A등급', NULL, '{"digital_literacy": 0.1}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020001', 'certificate', '컴퓨터활용능력 2급', '대한상공회의소', '2025-01-15', NULL, '2급', NULL, '{"digital_literacy": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140001', 'certificate', 'MOS Excel Expert', 'Microsoft', '2025-01-20', NULL, 'Expert', NULL, '{"digital_literacy": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Language Achievements
('2021010001', 'language', 'TOEIC', 'ETS', '2024-08-15', '2026-08-15', 'Advanced', '925', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'language', 'TOEIC', 'ETS', '2024-06-20', '2026-06-20', 'Advanced', '890', '{"communication": 0.28, "global": 0.23}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'language', 'TOEIC', 'ETS', '2024-09-10', '2026-09-10', 'Advanced', '945', '{"communication": 0.32, "global": 0.27}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'language', 'TOEIC', 'ETS', '2024-11-05', '2026-11-05', 'Intermediate', '785', '{"communication": 0.22, "global": 0.18}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020001', 'language', 'TOEIC', 'ETS', '2024-10-20', '2026-10-20', 'Advanced', '865', '{"communication": 0.26, "global": 0.22}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010001', 'language', 'TOEIC', 'ETS', '2025-01-10', '2027-01-10', 'Intermediate', '750', '{"communication": 0.2, "global": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'language', 'TOEIC', 'ETS', '2024-07-25', '2026-07-25', 'Advanced', '910', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140002', 'language', 'TOEIC', 'ETS', '2024-05-30', '2026-05-30', 'Advanced', '875', '{"communication": 0.27, "global": 0.22}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'language', 'TOEIC Speaking', 'ETS', '2024-10-15', '2026-10-15', 'Level 7', '170', '{"communication": 0.35, "presentation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', 'language', 'TOEIC Speaking', 'ETS', '2024-08-20', '2026-08-20', 'Level 8', '190', '{"communication": 0.4, "presentation": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010001', 'language', 'OPIc', 'ACTFL', '2024-09-20', '2026-09-20', 'IH', 'IH', '{"communication": 0.35, "global": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'language', 'OPIc', 'ACTFL', '2024-11-10', '2026-11-10', 'AL', 'AL', '{"communication": 0.4, "global": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010002', 'language', 'JLPT N2', '일본국제교류기금', '2024-07-10', NULL, 'N2', 'N2', '{"communication": 0.25, "global": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'language', 'HSK 5급', '중국국가한반', '2024-06-20', NULL, '5급', '230', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010002', 'language', 'TOEIC', 'ETS', '2025-01-05', '2027-01-05', 'Intermediate', '720', '{"communication": 0.18, "global": 0.12}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140002', 'language', 'TOEIC', 'ETS', '2025-01-18', '2027-01-18', 'Intermediate', '765', '{"communication": 0.2, "global": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Award Achievements
('2021010001', 'award', '대학생 프로그래밍 경진대회 금상', '한국정보올림피아드', '2024-09-20', NULL, '금상', NULL, '{"technical": 0.4, "problem_solving": 0.35, "teamwork": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'award', '카카오 코드 페스티벌 3등', '카카오', '2024-10-15', NULL, '3등', NULL, '{"technical": 0.35, "algorithm": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'award', 'Junction Asia 해커톤 대상', 'Junction', '2024-08-25', NULL, '대상', NULL, '{"technical": 0.35, "creativity": 0.3, "teamwork": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020002', 'award', 'ICPC 아시아 리저널 동메달', 'ICPC', '2024-11-10', NULL, '동메달', NULL, '{"technical": 0.4, "algorithm": 0.45, "teamwork": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010001', 'award', '삼성 알고리즘 역량강화 Pro 등급', '삼성전자', '2024-06-30', NULL, 'Pro', NULL, '{"technical": 0.35, "algorithm": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022010002', 'award', '네이버 개발자 컨퍼런스 장려상', '네이버', '2024-10-20', NULL, '장려상', NULL, '{"technical": 0.3, "presentation": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022020001', 'award', '구글 솔루션 챌린지 Top 50', 'Google', '2024-07-15', NULL, 'Top 50', NULL, '{"technical": 0.35, "creativity": 0.3, "social_impact": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023010001', 'award', '교내 프로그래밍 경시대회 은상', '서울대학교', '2024-12-10', NULL, '은상', NULL, '{"technical": 0.25, "problem_solving": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021130001', 'award', 'DACON AI 경진대회 금상', 'DACON', '2024-09-30', NULL, '금상', NULL, '{"data_analysis": 0.4, "ml": 0.35, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022130001', 'award', '공공데이터 활용 창업경진대회 최우수상', '행정안전부', '2024-11-05', NULL, '최우수상', NULL, '{"data_analysis": 0.35, "creativity": 0.3, "presentation": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140001', 'award', '창업 아이디어 경진대회 대상', '중소벤처기업부', '2024-08-20', NULL, '대상', NULL, '{"business": 0.4, "creativity": 0.35, "presentation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021140002', 'award', '마케팅 전략 공모전 금상', '대한상공회의소', '2024-09-15', NULL, '금상', NULL, '{"marketing": 0.4, "creativity": 0.3, "teamwork": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021030001', 'award', '임베디드 소프트웨어 경진대회 은상', '산업통상자원부', '2024-11-20', NULL, '은상', NULL, '{"technical": 0.35, "embedded": 0.4, "creativity": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021030002', 'award', '스마트디바이스 공학경진대회 동상', '한국전자통신연구원', '2024-09-25', NULL, '동상', NULL, '{"technical": 0.3, "electronics": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021060001', 'award', '기계설계 창의 경진대회 금상', '한국기계산업진흥회', '2024-10-10', NULL, '금상', NULL, '{"technical": 0.35, "mechanical": 0.4, "creativity": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024010001', 'award', '신입생 프로그래밍 경진대회 장려상', '서울대학교 컴퓨터공학부', '2024-12-20', NULL, '장려상', NULL, '{"technical": 0.15, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010003', 'award', '코딩 부트캠프 수료 우수상', '삼성 멀티캠퍼스', '2025-01-25', NULL, '우수상', NULL, '{"technical": 0.2, "learning": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Publication Achievements
('2021010001', 'publication', 'Deep Learning 기반 자연어 처리 모델 성능 개선에 관한 연구', '한국정보과학회', '2024-10-20', NULL, 'KCI등재', NULL, '{"research": 0.4, "technical": 0.35, "writing": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010003', 'publication', 'Transformer 모델의 경량화 기법 비교 분석', '한국컴퓨터종합학술대회', '2024-06-25', NULL, '학술대회', NULL, '{"research": 0.35, "technical": 0.3, "presentation": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021020001', 'publication', '마이크로서비스 아키텍처에서의 효율적인 로깅 시스템 설계', '한국소프트웨어공학학회', '2024-11-15', NULL, 'KCI등재후보', NULL, '{"research": 0.35, "technical": 0.35, "writing": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021030001', 'publication', 'Edge Computing 환경에서의 실시간 데이터 처리 기법', '한국통신학회', '2024-08-20', NULL, 'SCI', NULL, '{"research": 0.45, "technical": 0.4, "writing": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021130001', 'publication', '시계열 데이터 분석을 위한 새로운 이상치 탐지 알고리즘', '한국통계학회', '2024-10-05', NULL, 'KCI등재', NULL, '{"research": 0.4, "statistics": 0.4, "writing": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021010001', 'publication', '딥러닝 기반 이미지 분류 시스템 및 방법', '특허청', '2024-11-25', NULL, '특허출원', '10-2024-XXXXX', '{"research": 0.35, "technical": 0.4, "innovation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021030001', 'publication', 'IoT 센서 데이터 압축 전송 장치 및 방법', '특허청', '2024-09-15', NULL, '특허등록', '10-2024-ZZZZZ', '{"research": 0.4, "technical": 0.45, "innovation": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)

ON CONFLICT DO NOTHING;

-- ============================================
-- STEP 6: Additional Skills
-- ============================================

INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt) VALUES
('SKL016', 'TypeScript', 'TypeScript', ARRAY['TS', '타입스크립트'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL017', 'React', 'React', ARRAY['리액트', 'ReactJS', 'React.js'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL018', 'Node.js', 'Node.js', ARRAY['노드', 'NodeJS'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL019', 'Docker', 'Docker', ARRAY['도커', '컨테이너'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL020', 'Kubernetes', 'Kubernetes', ARRAY['쿠버네티스', 'K8s'], 'technical', 4, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL021', 'Git', 'Git', ARRAY['깃', 'GitHub', '깃허브', 'GitLab'], 'technical', 2, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL022', 'Linux', 'Linux', ARRAY['리눅스', 'Ubuntu', '우분투'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL023', 'MongoDB', 'MongoDB', ARRAY['몽고디비', 'NoSQL'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL024', 'GraphQL', 'GraphQL', ARRAY['그래프큐엘'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL025', 'Figma', 'Figma', ARRAY['피그마'], 'technical', 2, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL026', 'Swift', 'Swift', ARRAY['스위프트', 'iOS개발'], 'technical', 4, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL027', 'Kotlin', 'Kotlin', ARRAY['코틀린', '안드로이드개발'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL028', 'Go', 'Go', ARRAY['Golang', '고랭'], 'technical', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL029', 'Rust', 'Rust', ARRAY['러스트'], 'technical', 5, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL030', 'Spark', 'Apache Spark', ARRAY['스파크', '아파치 스파크'], 'technical', 4, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL031', '비판적사고', 'Critical Thinking', ARRAY['비평적 사고', '분석적 사고'], 'soft', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL032', '창의력', 'Creativity', ARRAY['창의성', '창조성'], 'soft', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL033', '적응력', 'Adaptability', ARRAY['유연성', '변화적응'], 'soft', 3, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL034', '시간관리', 'Time Management', ARRAY['일정관리', '자기관리'], 'soft', 2, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('SKL035', '협상력', 'Negotiation', ARRAY['협상 스킬', '설득력'], 'soft', 4, 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (skill_cd) DO NOTHING;

-- ============================================
-- STEP 7: Student Skills for 2025 students
-- ============================================

INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 5, 2, 'course'),
        ('SKL021', 2, 4, 3, 'project'),
        ('SKL009', 2, 4, 2, 'self_assessment'),
        ('SKL034', 2, 4, 2, 'self_assessment')
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT001' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL003', 2, 5, 2, 'course'),
        ('SKL021', 2, 4, 3, 'project'),
        ('SKL017', 1, 4, 1, 'self_assessment'),
        ('SKL011', 2, 4, 3, 'project')
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT002' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL001', 2, 5, 2, 'course'),
        ('SKL004', 2, 4, 2, 'course'),
        ('SKL007', 2, 5, 3, 'course'),
        ('SKL031', 2, 4, 2, 'self_assessment')
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT013' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL010', 2, 5, 3, 'self_assessment'),
        ('SKL015', 2, 5, 3, 'course'),
        ('SKL034', 2, 4, 2, 'self_assessment'),
        ('SKL014', 2, 4, 2, 'certificate')
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT014' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.4 THEN 'up' ELSE 'stable' END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL025', 2, 5, 3, 'course'),
        ('SKL032', 3, 5, 3, 'self_assessment'),
        ('SKL010', 2, 4, 2, 'self_assessment'),
        ('SKL011', 2, 4, 3, 'project')
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd = 'DEPT025' AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    skill_data.skill_cd,
    skill_data.current_level,
    skill_data.target_level,
    skill_data.evidence_count,
    CURRENT_DATE - (RANDOM() * 30)::INT,
    skill_data.verification_source,
    CASE WHEN RANDOM() > 0.5 THEN 'up' ELSE 'stable' END,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('SKL009', 2, 4, 2, 'self_assessment'),
        ('SKL010', 2, 4, 2, 'self_assessment'),
        ('SKL011', 2, 4, 2, 'project'),
        ('SKL034', 2, 4, 2, 'self_assessment')
) AS skill_data(skill_cd, current_level, target_level, evidence_count, verification_source)
WHERE s.department_cd IN ('DEPT003', 'DEPT004', 'DEPT006', 'DEPT009', 'DEPT010', 'DEPT023') AND s.admission_year = 2025
ON CONFLICT (student_id, skill_cd) DO NOTHING;

-- ============================================
-- STEP 8: Portfolio data
-- ============================================

DELETE FROM tb_portfolio WHERE ins_user_id = 'SEED_SCRIPT';

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('github', 'Algorithm Study', 'https://github.com/{student_id}/algorithm-study', '알고리즘 문제 풀이 레포지토리'),
        ('github', 'ML Projects', 'https://github.com/{student_id}/ml-projects', '머신러닝 프로젝트 모음'),
        ('notion', 'Tech Blog', 'https://notion.so/{student_id}/tech-blog', '기술 블로그')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT001' AND s.current_grade >= 3;

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('github', 'Coding Practice', 'https://github.com/{student_id}/coding-practice', '코딩 연습 레포지토리'),
        ('notion', '학습 노트', 'https://notion.so/{student_id}/study-notes', '프로그래밍 학습 기록')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT001' AND s.current_grade IN (1, 2);

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('github', 'React Portfolio', 'https://github.com/{student_id}/react-portfolio', 'React + TypeScript 포트폴리오'),
        ('github', 'Full Stack Project', 'https://github.com/{student_id}/fullstack-project', 'Node.js + React 기반 프로젝트'),
        ('notion', 'Project Documentation', 'https://notion.so/{student_id}/project-docs', '프로젝트 기획서, 설계 문서')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT002' AND s.current_grade >= 3;

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('github', 'Web Projects', 'https://github.com/{student_id}/web-projects', 'HTML, CSS, JavaScript 웹 프로젝트'),
        ('notion', '개발 일지', 'https://notion.so/{student_id}/dev-journal', '웹 개발 학습 기록')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT002' AND s.current_grade IN (1, 2);

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('github', 'Data Analysis Projects', 'https://github.com/{student_id}/data-analysis', '데이터 분석 프로젝트'),
        ('github', 'Kaggle Competitions', 'https://kaggle.com/{student_id}', 'Kaggle 경진대회 참가 기록'),
        ('notion', 'Statistics Notes', 'https://notion.so/{student_id}/stats-notes', '통계학 이론 정리')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT013' AND s.current_grade >= 3;

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('notion', 'Business Case Study', 'https://notion.so/{student_id}/case-study', '경영 전략 케이스 스터디'),
        ('notion', 'Marketing Portfolio', 'https://notion.so/{student_id}/marketing', '마케팅 프로젝트 포트폴리오')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT014' AND s.current_grade >= 3;

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('notion', 'UX/UI Portfolio', 'https://notion.so/{student_id}/ux-portfolio', 'UX/UI 디자인 포트폴리오'),
        ('project', 'Figma Design System', 'https://figma.com/@{student_id}/design-system', '개인 디자인 시스템 라이브러리')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT025' AND s.current_grade >= 3;

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('github', 'Embedded Projects', 'https://github.com/{student_id}/embedded', '임베디드 시스템 프로젝트'),
        ('notion', 'Electronics Lab Notes', 'https://notion.so/{student_id}/lab-notes', '전자회로 실험 보고서')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT003' AND s.current_grade >= 3;

INSERT INTO tb_portfolio (student_id, artifact_type, title, url, description, ins_user_id, ins_dt)
SELECT
    s.student_id,
    portfolio_data.artifact_type,
    portfolio_data.title,
    REPLACE(portfolio_data.url, '{student_id}', s.student_id),
    portfolio_data.description,
    'SEED_SCRIPT',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN (
    VALUES
        ('notion', 'OR/Optimization Projects', 'https://notion.so/{student_id}/or-projects', '최적화 문제 해결 프로젝트'),
        ('github', 'Data Analytics', 'https://github.com/{student_id}/ie-analytics', '산업데이터 분석 프로젝트')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT006' AND s.current_grade >= 3;

-- ============================================
-- STEP 9: Verify Data
-- ============================================

DO $$
DECLARE
    v_student_count INT;
    v_student_2025 INT;
    v_achievement_count INT;
    v_skill_count INT;
    v_student_skill_count INT;
    v_portfolio_count INT;
    v_opportunity_count INT;
BEGIN
    SELECT COUNT(*) INTO v_student_count FROM tb_student;
    SELECT COUNT(*) INTO v_student_2025 FROM tb_student WHERE admission_year = 2025;
    SELECT COUNT(*) INTO v_achievement_count FROM tb_achievement;
    SELECT COUNT(*) INTO v_skill_count FROM tb_skill;
    SELECT COUNT(*) INTO v_student_skill_count FROM tb_student_skill;
    SELECT COUNT(*) INTO v_portfolio_count FROM tb_portfolio;
    SELECT COUNT(*) INTO v_opportunity_count FROM tb_opportunity;

    RAISE NOTICE '==========================================';
    RAISE NOTICE 'IDINO Career - Seed Data Summary';
    RAISE NOTICE '------------------------------------------';
    RAISE NOTICE 'tb_student total: % records', v_student_count;
    RAISE NOTICE 'tb_student (2025): % records', v_student_2025;
    RAISE NOTICE 'tb_achievement: % records', v_achievement_count;
    RAISE NOTICE 'tb_skill: % records', v_skill_count;
    RAISE NOTICE 'tb_student_skill: % records', v_student_skill_count;
    RAISE NOTICE 'tb_portfolio: % records', v_portfolio_count;
    RAISE NOTICE 'tb_opportunity: % records', v_opportunity_count;
    RAISE NOTICE '==========================================';
END $$;
