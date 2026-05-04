-- ============================================
-- IDINO Career - 2025년 입학생 추가 데이터
-- Target: admission_year 2025 학생들
-- Created: 2026-01-26
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 2025년 입학 학생 정보 (각 학과별 5-8명)
-- ============================================

INSERT INTO tb_student (student_id, student_nm, university_cd, department_cd, admission_year, current_grade, current_semester, email, phone, birth_date, gender, status, career_goal, ins_user_id, ins_dt) VALUES
-- 컴퓨터공학과 (8명)
('2025010001', '김현서', 'UNIV01', 'DEPT001', 2025, 1, 1, 'hyunseo.kim25@kstu.ac.kr', '010-2501-0001', '2006-03-15', 'F', 'enrolled', 'AI엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010002', '이도윤', 'UNIV01', 'DEPT001', 2025, 1, 1, 'doyun.lee25@kstu.ac.kr', '010-2501-0002', '2006-05-22', 'M', 'enrolled', '백엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010003', '박서연', 'UNIV01', 'DEPT001', 2025, 1, 1, 'seoyeon.park25@kstu.ac.kr', '010-2501-0003', '2006-08-10', 'F', 'enrolled', '데이터사이언티스트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010004', '최민재', 'UNIV01', 'DEPT001', 2025, 1, 1, 'minjae.choi25@kstu.ac.kr', '010-2501-0004', '2006-01-28', 'M', 'enrolled', '풀스택개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010005', '정하은', 'UNIV01', 'DEPT001', 2025, 1, 1, 'haeun.jung25@kstu.ac.kr', '010-2501-0005', '2006-04-05', 'F', 'enrolled', '보안전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010006', '강준호', 'UNIV01', 'DEPT001', 2025, 1, 1, 'junho.kang25@kstu.ac.kr', '010-2501-0006', '2006-07-12', 'M', 'enrolled', 'DevOps엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010007', '윤서아', 'UNIV01', 'DEPT001', 2025, 1, 1, 'seoa.yoon25@kstu.ac.kr', '010-2501-0007', '2006-02-18', 'F', 'enrolled', 'ML엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025010008', '임지훈', 'UNIV01', 'DEPT001', 2025, 1, 1, 'jihoon.lim25@kstu.ac.kr', '010-2501-0008', '2006-06-25', 'M', 'enrolled', '클라우드엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),

-- 소프트웨어공학과 (6명)
('2025020001', '한지민', 'UNIV01', 'DEPT002', 2025, 1, 1, 'jimin.han25@kstu.ac.kr', '010-2502-0001', '2006-02-14', 'F', 'enrolled', '프론트엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020002', '오승현', 'UNIV01', 'DEPT002', 2025, 1, 1, 'seunghyun.oh25@kstu.ac.kr', '010-2502-0002', '2006-04-28', 'M', 'enrolled', '모바일개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020003', '배수빈', 'UNIV01', 'DEPT002', 2025, 1, 1, 'subin.bae25@kstu.ac.kr', '010-2502-0003', '2006-03-19', 'F', 'enrolled', 'UX엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020004', '황민서', 'UNIV01', 'DEPT002', 2025, 1, 1, 'minseo.hwang25@kstu.ac.kr', '010-2502-0004', '2006-06-07', 'M', 'enrolled', '백엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020005', '문채원', 'UNIV01', 'DEPT002', 2025, 1, 1, 'chaewon.moon25@kstu.ac.kr', '010-2502-0005', '2006-01-11', 'F', 'enrolled', 'QA엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025020006', '송도현', 'UNIV01', 'DEPT002', 2025, 1, 1, 'dohyun.song25@kstu.ac.kr', '010-2502-0006', '2006-04-23', 'M', 'enrolled', '프론트엔드개발자', 'SYSTEM', CURRENT_TIMESTAMP),

-- 전자공학과 (5명)
('2025030001', '신예린', 'UNIV01', 'DEPT003', 2025, 1, 1, 'yerin.shin25@kstu.ac.kr', '010-2503-0001', '2006-01-20', 'F', 'enrolled', 'IoT엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030002', '김태윤', 'UNIV01', 'DEPT003', 2025, 1, 1, 'taeyun.kim25@kstu.ac.kr', '010-2503-0002', '2006-06-13', 'M', 'enrolled', '반도체엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030003', '이나연', 'UNIV01', 'DEPT003', 2025, 1, 1, 'nayeon.lee25@kstu.ac.kr', '010-2503-0003', '2006-02-25', 'F', 'enrolled', '임베디드개발자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030004', '박건우', 'UNIV01', 'DEPT003', 2025, 1, 1, 'gunwoo.park25@kstu.ac.kr', '010-2503-0004', '2006-05-18', 'M', 'enrolled', '통신엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025030005', '최서윤', 'UNIV01', 'DEPT003', 2025, 1, 1, 'seoyun.choi25@kstu.ac.kr', '010-2503-0005', '2006-03-07', 'F', 'enrolled', 'HW엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),

-- 경영학과 (6명)
('2025140001', '정유나', 'UNIV01', 'DEPT014', 2025, 1, 1, 'yuna.jung25@kstu.ac.kr', '010-2514-0001', '2006-02-28', 'F', 'enrolled', '경영컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140002', '강민준', 'UNIV01', 'DEPT014', 2025, 1, 1, 'minjun.kang25@kstu.ac.kr', '010-2514-0002', '2006-05-10', 'M', 'enrolled', '마케팅전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140003', '윤서영', 'UNIV01', 'DEPT014', 2025, 1, 1, 'seoyoung.yoon25@kstu.ac.kr', '010-2514-0003', '2006-01-15', 'F', 'enrolled', '재무분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140004', '임재현', 'UNIV01', 'DEPT014', 2025, 1, 1, 'jaehyun.lim25@kstu.ac.kr', '010-2514-0004', '2006-04-22', 'M', 'enrolled', '제품관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140005', '한소희', 'UNIV01', 'DEPT014', 2025, 1, 1, 'sohee.han25@kstu.ac.kr', '010-2514-0005', '2006-02-08', 'F', 'enrolled', 'HR전문가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025140006', '오준서', 'UNIV01', 'DEPT014', 2025, 1, 1, 'junseo.oh25@kstu.ac.kr', '010-2514-0006', '2006-06-30', 'M', 'enrolled', '스타트업창업', 'SYSTEM', CURRENT_TIMESTAMP),

-- 통계학과 (5명)
('2025130001', '서지우', 'UNIV01', 'DEPT013', 2025, 1, 1, 'jiwoo.seo25@kstu.ac.kr', '010-2513-0001', '2006-01-08', 'F', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130002', '이현우', 'UNIV01', 'DEPT013', 2025, 1, 1, 'hyunwoo.lee25@kstu.ac.kr', '010-2513-0002', '2006-04-15', 'M', 'enrolled', 'AI엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130003', '박소연', 'UNIV01', 'DEPT013', 2025, 1, 1, 'soyeon.park25@kstu.ac.kr', '010-2513-0003', '2006-03-22', 'F', 'enrolled', '데이터사이언티스트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130004', '김도현', 'UNIV01', 'DEPT013', 2025, 1, 1, 'dohyun.kim25@kstu.ac.kr', '010-2513-0004', '2006-06-28', 'M', 'enrolled', '퀀트분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025130005', '최예원', 'UNIV01', 'DEPT013', 2025, 1, 1, 'yewon.choi25@kstu.ac.kr', '010-2513-0005', '2006-01-05', 'F', 'enrolled', '통계컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),

-- 산업공학과 (5명)
('2025060001', '장민석', 'UNIV01', 'DEPT006', 2025, 1, 1, 'minseok.jang25@kstu.ac.kr', '010-2506-0001', '2006-03-25', 'M', 'enrolled', '품질관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060002', '김하린', 'UNIV01', 'DEPT006', 2025, 1, 1, 'harin.kim25@kstu.ac.kr', '010-2506-0002', '2006-07-18', 'F', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060003', '이준영', 'UNIV01', 'DEPT006', 2025, 1, 1, 'junyoung.lee25@kstu.ac.kr', '010-2506-0003', '2006-02-14', 'M', 'enrolled', '프로젝트관리자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060004', '박서현', 'UNIV01', 'DEPT006', 2025, 1, 1, 'seohyun.park25@kstu.ac.kr', '010-2506-0004', '2006-05-30', 'F', 'enrolled', '컨설턴트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025060005', '최우진', 'UNIV01', 'DEPT006', 2025, 1, 1, 'woojin.choi25@kstu.ac.kr', '010-2506-0005', '2006-04-10', 'M', 'enrolled', '생산관리자', 'SYSTEM', CURRENT_TIMESTAMP),

-- 디자인학과 (5명)
('2025250001', '윤채아', 'UNIV01', 'DEPT025', 2025, 1, 1, 'chaea.yoon25@kstu.ac.kr', '010-2525-0001', '2006-02-05', 'F', 'enrolled', 'UX디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250002', '임동훈', 'UNIV01', 'DEPT025', 2025, 1, 1, 'donghun.lim25@kstu.ac.kr', '010-2525-0002', '2006-06-20', 'M', 'enrolled', '제품디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250003', '한지연', 'UNIV01', 'DEPT025', 2025, 1, 1, 'jiyeon.han25@kstu.ac.kr', '010-2525-0003', '2006-01-28', 'F', 'enrolled', 'UI디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250004', '오승민', 'UNIV01', 'DEPT025', 2025, 1, 1, 'seungmin.oh25@kstu.ac.kr', '010-2525-0004', '2006-04-15', 'M', 'enrolled', '브랜드디자이너', 'SYSTEM', CURRENT_TIMESTAMP),
('2025250005', '배수아', 'UNIV01', 'DEPT025', 2025, 1, 1, 'sua.bae25@kstu.ac.kr', '010-2525-0005', '2006-03-10', 'F', 'enrolled', '그래픽디자이너', 'SYSTEM', CURRENT_TIMESTAMP),

-- 심리학과 (4명)
('2025230001', '김다은', 'UNIV01', 'DEPT023', 2025, 1, 1, 'daeun.kim25@kstu.ac.kr', '010-2523-0001', '2006-01-12', 'F', 'enrolled', 'UX리서처', 'SYSTEM', CURRENT_TIMESTAMP),
('2025230002', '이정민', 'UNIV01', 'DEPT023', 2025, 1, 1, 'jungmin.lee25@kstu.ac.kr', '010-2523-0002', '2006-05-28', 'M', 'enrolled', 'HR담당자', 'SYSTEM', CURRENT_TIMESTAMP),
('2025230003', '박시현', 'UNIV01', 'DEPT023', 2025, 1, 1, 'sihyun.park25@kstu.ac.kr', '010-2523-0003', '2006-02-08', 'F', 'enrolled', '상담심리사', 'SYSTEM', CURRENT_TIMESTAMP),
('2025230004', '최재훈', 'UNIV01', 'DEPT023', 2025, 1, 1, 'jaehoon.choi25@kstu.ac.kr', '010-2523-0004', '2006-06-15', 'M', 'enrolled', '데이터분석가', 'SYSTEM', CURRENT_TIMESTAMP),

-- 기계공학과 (4명)
('2025040001', '정승우', 'UNIV01', 'DEPT004', 2025, 1, 1, 'seungwoo.jung25@kstu.ac.kr', '010-2504-0001', '2006-01-28', 'M', 'enrolled', '자동차엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025040002', '강민지', 'UNIV01', 'DEPT004', 2025, 1, 1, 'minji.kang25@kstu.ac.kr', '010-2504-0002', '2006-04-10', 'F', 'enrolled', '로봇엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025040003', '윤태호', 'UNIV01', 'DEPT004', 2025, 1, 1, 'taeho.yoon25@kstu.ac.kr', '010-2504-0003', '2006-08-22', 'M', 'enrolled', '에너지엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025040004', '임서연', 'UNIV01', 'DEPT004', 2025, 1, 1, 'seoyeon.lim25@kstu.ac.kr', '010-2504-0004', '2006-03-18', 'F', 'enrolled', '항공엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),

-- 물리학과 (3명)
('2025100001', '김준혁', 'UNIV01', 'DEPT010', 2025, 1, 1, 'junhyuk.kim25@kstu.ac.kr', '010-2510-0001', '2006-03-10', 'M', 'enrolled', '양자컴퓨팅연구원', 'SYSTEM', CURRENT_TIMESTAMP),
('2025100002', '이서진', 'UNIV01', 'DEPT010', 2025, 1, 1, 'seojin.lee25@kstu.ac.kr', '010-2510-0002', '2006-01-25', 'F', 'enrolled', '광학엔지니어', 'SYSTEM', CURRENT_TIMESTAMP),
('2025100003', '박현준', 'UNIV01', 'DEPT010', 2025, 1, 1, 'hyunjun.park25@kstu.ac.kr', '010-2510-0003', '2006-02-15', 'M', 'enrolled', '연구원', 'SYSTEM', CURRENT_TIMESTAMP),

-- 수학과 (3명)
('2025090001', '최예진', 'UNIV01', 'DEPT009', 2025, 1, 1, 'yejin.choi25@kstu.ac.kr', '010-2509-0001', '2006-02-18', 'F', 'enrolled', '퀀트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025090002', '정민규', 'UNIV01', 'DEPT009', 2025, 1, 1, 'mingyu.jung25@kstu.ac.kr', '010-2509-0002', '2006-06-25', 'M', 'enrolled', '데이터사이언티스트', 'SYSTEM', CURRENT_TIMESTAMP),
('2025090003', '한소율', 'UNIV01', 'DEPT009', 2025, 1, 1, 'soyul.han25@kstu.ac.kr', '010-2509-0003', '2006-03-12', 'F', 'enrolled', '암호학연구원', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 2025년 입학생 학점 현황 생성
-- ============================================

INSERT INTO tb_cumulative_summary (student_id, total_credits_earned, major_credits_earned, liberal_credits_earned, cumulative_gpa, major_gpa, completion_rate, ins_user_id, ins_dt)
SELECT
    student_id,
    FLOOR(0 + RANDOM() * 10) as total_credits_earned,  -- 1학년 1학기라 0-10학점
    FLOOR(0 + RANDOM() * 5) as major_credits_earned,
    FLOOR(0 + RANDOM() * 3) as liberal_credits_earned,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as cumulative_gpa,
    ROUND((2.5 + RANDOM() * 2.0)::numeric, 2) as major_gpa,
    ROUND((0 + RANDOM() * 8)::numeric, 1) as completion_rate,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student
WHERE admission_year = 2025;

-- ============================================
-- 2025년 입학생 역량 현황 생성
-- ============================================

INSERT INTO tb_student_competency (student_id, competency_cd, current_score, target_score, gap_score, status, trend, ins_user_id, ins_dt)
SELECT
    s.student_id,
    c.competency_cd,
    ROUND((30 + RANDOM() * 40)::numeric, 1) as current_score,  -- 1학년이라 낮은 점수
    85 as target_score,
    0 as gap_score,
    CASE
        WHEN RANDOM() < 0.1 THEN 'good'
        WHEN RANDOM() < 0.3 THEN 'average'
        WHEN RANDOM() < 0.6 THEN 'improve'
        ELSE 'focus'
    END as status,
    CASE
        WHEN RANDOM() < 0.5 THEN 'up'  -- 1학년이라 상승세 많음
        WHEN RANDOM() < 0.8 THEN 'stable'
        ELSE 'down'
    END as trend,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN tb_competency c
WHERE s.admission_year = 2025;

-- gap_score 업데이트
UPDATE tb_student_competency sc
SET gap_score = sc.current_score - sc.target_score
FROM tb_student s
WHERE sc.student_id = s.student_id
AND s.admission_year = 2025;

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    student_2025_count INT;
    summary_count INT;
    competency_count INT;
BEGIN
    SELECT COUNT(*) INTO student_2025_count FROM tb_student WHERE admission_year = 2025;
    SELECT COUNT(*) INTO summary_count FROM tb_cumulative_summary cs JOIN tb_student s ON cs.student_id = s.student_id WHERE s.admission_year = 2025;
    SELECT COUNT(*) INTO competency_count FROM tb_student_competency sc JOIN tb_student s ON sc.student_id = s.student_id WHERE s.admission_year = 2025;

    RAISE NOTICE '=== 2025 Students Seed Data Created ===';
    RAISE NOTICE 'tb_student (2025): % records', student_2025_count;
    RAISE NOTICE 'tb_cumulative_summary (2025): % records', summary_count;
    RAISE NOTICE 'tb_student_competency (2025): % records', competency_count;
END $$;
