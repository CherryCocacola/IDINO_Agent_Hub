-- ============================================================
-- 학생별 맞춤 스프린트 목표 생성 스크립트
-- 대상: 2023, 2024, 2025 입학 학생
-- 목표: 학과, 학년에 맞는 현실적인 스프린트 목표 3건 이상
-- ============================================================

-- 1. 기존 2023-2025 학생의 기존 목표 삭제 (generic data)
DELETE FROM idino_career.tb_coaching_goal
WHERE std_id IN (
    SELECT student_id FROM idino_career.tb_student
    WHERE admission_year IN (2023, 2024, 2025)
);

-- 2. IT/공학 계열 학생 목표 생성
-- 2023 입학 (3학년) - IT/공학
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '정보처리기사 실기 합격',
    '정보처리기사 실기시험 합격을 목표로 준비. 실기 문제 유형 분석 및 실습 병행',
    'certification',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 70 + 10)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '캡스톤 프로젝트 완료',
    '팀 프로젝트로 실제 서비스 개발. 기획-설계-개발-배포 전 과정 경험',
    'project',
    'high',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 80 + 20)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    'IT 기업 인턴십 지원',
    '네이버, 카카오, 삼성전자 등 IT 기업 하계/동계 인턴십 지원 준비',
    'employment',
    'high',
    CASE WHEN random() < 0.2 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.2 THEN 100 ELSE floor(random() * 60 + 10)::int END,
    CURRENT_DATE + interval '2 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    'GitHub 포트폴리오 정리',
    '프로젝트 README 작성, 코드 리팩토링, 기술 블로그 연동',
    'skill_development',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '1 month'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

-- 2024 입학 (2학년) - IT/공학
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '정보처리기사 필기 합격',
    '정보처리기사 필기시험 준비. 데이터베이스, 소프트웨어공학, 운영체제 이론 학습',
    'certification',
    'high',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '2 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '알고리즘 스터디 참여',
    '백준/프로그래머스 문제풀이 스터디. 주 5문제 이상 풀이 목표',
    'skill_development',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 80 + 10)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '토이 프로젝트 1개 완성',
    '개인 프로젝트로 웹/앱 서비스 개발. 배포까지 완료하여 포트폴리오 구축',
    'project',
    'medium',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 70 + 10)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

-- 2025 입학 (1학년) - IT/공학
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    'Python/Java 기초 완성',
    '프로그래밍 언어 기초 문법 완벽 이해. 기초 알고리즘 문제 50개 이상 풀이',
    'skill_development',
    'high',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 기초 과목 A학점 목표',
    '컴퓨터개론, 프로그래밍기초 등 전공기초 과목 A학점 이상 획득',
    'academic',
    'high',
    'active',
    floor(random() * 50 + 30)::int,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '코딩 동아리 가입',
    '교내 코딩/개발 동아리 가입하여 선배들과 네트워킹 및 멘토링 받기',
    'activity',
    'medium',
    CASE WHEN random() < 0.6 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.6 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '1 month'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과');

-- 3. 의료/보건 계열 학생 목표 생성
-- 2023 입학 (3학년) - 의료/보건
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    CASE
        WHEN d.department_nm = '간호학과' THEN '간호사 국가고시 준비'
        WHEN d.department_nm IN ('의예과', '의학과') THEN '의사 국가고시 1차 준비'
        WHEN d.department_nm = '약학과' THEN '약사 국가고시 준비'
        WHEN d.department_nm = '물리치료학과' THEN '물리치료사 국가고시 준비'
        WHEN d.department_nm = '작업치료학과' THEN '작업치료사 국가고시 준비'
        WHEN d.department_nm = '임상병리학과' THEN '임상병리사 국가고시 준비'
        WHEN d.department_nm = '응급구조학과' THEN '응급구조사 1급 시험 준비'
        ELSE '보건관리사 자격증 준비'
    END,
    '국가고시 기출문제 분석 및 모의고사 풀이. 약점 영역 집중 학습',
    'certification',
    'high',
    CASE WHEN random() < 0.2 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.2 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '임상실습 우수 평가 획득',
    '병원/의료기관 임상실습에서 우수 평가 목표. 실습일지 꼼꼼히 작성',
    'project',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    'BLS/ACLS 자격 취득',
    '기본소생술(BLS) 및 전문심장소생술(ACLS) 자격 취득',
    'certification',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '2 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

-- 2024 입학 (2학년) - 의료/보건
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 필수 과목 이수',
    '해부학, 생리학, 약리학 등 전공 필수 과목 A학점 이상 목표',
    'academic',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '의료 봉사활동 참여',
    '교내외 의료봉사 동아리 활동. 지역사회 건강증진 프로그램 참여',
    'activity',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '국시 기출문제 풀이 시작',
    '국가고시 기출문제 분석 및 오답노트 작성 시작. 주 50문제 목표',
    'skill_development',
    'medium',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 50 + 20)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

-- 2025 입학 (1학년) - 의료/보건
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '기초의학 과목 A학점',
    '생물학, 화학, 해부학개론 등 기초의학 과목 A학점 이상 획득',
    'academic',
    'high',
    'active',
    floor(random() * 50 + 30)::int,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '의료 관련 동아리 가입',
    '의료봉사 동아리, 학술 동아리 등 가입하여 선배 멘토링 받기',
    'activity',
    'medium',
    CASE WHEN random() < 0.6 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.6 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '1 month'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '진로 탐색 특강 참여',
    '학과 진로 특강, 병원 견학, 선배 멘토링 프로그램 참여',
    'career',
    'medium',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 50 + 30)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과');

-- 4. 경영/사회 계열 학생 목표 생성
-- 2023 입학 (3학년) - 경영/사회
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    CASE
        WHEN d.department_nm = '경영학과' THEN '한국사/매경TEST 자격증'
        WHEN d.department_nm LIKE '%경찰%' THEN '경찰공무원 필기시험 준비'
        WHEN d.department_nm = '사회복지학과' THEN '사회복지사 1급 준비'
        ELSE 'TOEIC 850점 이상'
    END,
    '취업 필수 자격증 취득 목표. 체계적인 학습 계획 수립',
    'certification',
    'high',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '현장실습/인턴십 참여',
    '기업 현장실습 또는 인턴십 프로그램 참여. 실무 경험 획득',
    'employment',
    'high',
    CASE WHEN random() < 0.25 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.25 THEN 100 ELSE floor(random() * 50 + 20)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '공모전/경진대회 참가',
    '마케팅 공모전, 창업경진대회 등 참가하여 수상 경력 확보',
    'activity',
    'medium',
    CASE WHEN random() < 0.35 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.35 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '2 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

-- 2024 입학 (2학년) - 경영/사회
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    'TOEIC 700점 이상 달성',
    'TOEIC 목표 점수 달성. 주 3회 이상 영어 학습',
    'certification',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 심화 과목 이수',
    '회계학, 마케팅, 인적자원관리 등 전공 심화 과목 B+ 이상',
    'academic',
    'high',
    CASE WHEN random() < 0.35 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.35 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교내 학회/동아리 활동',
    '경영학회, 토론동아리, 봉사동아리 등 적극 참여',
    'activity',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

-- 2025 입학 (1학년) - 경영/사회
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 기초 과목 이수',
    '경영학원론, 경제학원론, 회계원리 등 전공기초 B+ 이상',
    'academic',
    'high',
    'active',
    floor(random() * 50 + 30)::int,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '영어 기초 실력 향상',
    'TOEIC 600점 또는 영어회화 기초 과정 수료',
    'skill_development',
    'medium',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 50 + 20)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '진로 탐색 멘토링 참여',
    '학과 선배 멘토링, 취업센터 진로상담 참여',
    'career',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '2 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과');

-- 5. 교육 계열 학생 목표 생성
-- 2023 입학 (3학년) - 교육
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '임용고시 1차 준비',
    '임용고시 교육학/전공 1차 필기시험 준비. 기출문제 분석',
    'certification',
    'high',
    CASE WHEN random() < 0.2 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.2 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '8 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교육봉사 80시간 이수',
    '교원자격증 취득을 위한 교육봉사 시간 충족',
    'activity',
    'high',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교육실습 우수 평가',
    '4주 교육실습에서 우수 평가 획득. 수업지도안 작성 능력 향상',
    'project',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

-- 2024 입학 (2학년) - 교육
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교직과목 이수',
    '교육심리학, 교육방법론 등 교직 필수과목 B+ 이상 취득',
    'academic',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교육봉사 시작',
    '지역아동센터, 멘토링 프로그램 등 교육봉사 활동 시작',
    'activity',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '한국사능력검정 2급 취득',
    '교원자격증 취득 요건인 한국사능력검정시험 2급 이상 합격',
    'certification',
    'medium',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

-- 2025 입학 (1학년) - 교육
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 기초과목 이수',
    '교육학개론, 심리학개론 등 전공 기초과목 A학점 목표',
    'academic',
    'high',
    'active',
    floor(random() * 50 + 30)::int,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교육 동아리 가입',
    '교육봉사 동아리, 임용스터디 등 가입하여 진로 탐색',
    'activity',
    'medium',
    CASE WHEN random() < 0.6 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.6 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '1 month'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교직 진로 상담 참여',
    '교직 진로 특강, 선배 멘토링 참여하여 임용/사립 진로 탐색',
    'career',
    'medium',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 50 + 30)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과');

-- 6. 예술/디자인 계열 학생 목표 생성
-- 2023 입학 (3학년) - 예술/디자인
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '졸업작품 전시회 참여',
    '졸업작품 제작 및 전시회 참여. 포트폴리오 완성',
    'project',
    'high',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '공모전 수상',
    '전공 관련 공모전 참가하여 수상 경력 확보',
    'activity',
    'high',
    CASE WHEN random() < 0.25 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.25 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '인턴십/현장실습 참여',
    '디자인 스튜디오, 건축사무소 등 현장실습 참여',
    'employment',
    'medium',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 50 + 20)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

-- 2024 입학 (2학년) - 예술/디자인
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '포트폴리오 구축 시작',
    '작품 아카이빙, 웹 포트폴리오 제작 시작',
    'skill_development',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 실기 능력 향상',
    '전공 실기 과목 A학점 이상 취득. 작품 품질 향상',
    'academic',
    'high',
    CASE WHEN random() < 0.35 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.35 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '디자인 툴 마스터',
    'Adobe Creative Suite, AutoCAD, 3D 모델링 등 전문 툴 숙달',
    'skill_development',
    'medium',
    CASE WHEN random() < 0.45 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.45 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

-- 2025 입학 (1학년) - 예술/디자인
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 기초 실기 이수',
    '드로잉, 기초설계, 기초실기 등 전공 기초과목 이수',
    'academic',
    'high',
    'active',
    floor(random() * 50 + 30)::int,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '기초 디자인 툴 학습',
    'Photoshop, Illustrator 기초 기능 숙달',
    'skill_development',
    'medium',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 50 + 30)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 동아리/학회 가입',
    '전공 관련 동아리, 학회 가입하여 선배 네트워킹',
    'activity',
    'medium',
    CASE WHEN random() < 0.6 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.6 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '1 month'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm IN ('미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과');

-- 7. 기타 학과 학생 목표 생성 (스포츠, 식품, 글로벌자유전공 등)
-- 2023 입학 (3학년) - 기타
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    CASE
        WHEN d.department_nm LIKE '%스포츠%' THEN '생활스포츠지도사 2급 취득'
        WHEN d.department_nm LIKE '%식품%' THEN '식품기사/영양사 자격증 취득'
        WHEN d.department_nm LIKE '%자유전공%' THEN '복수전공 이수 완료'
        ELSE '전공 관련 자격증 취득'
    END,
    '취업에 필요한 핵심 자격증 취득 목표',
    'certification',
    'high',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '현장실습/인턴십 참여',
    '전공 관련 기업/기관 현장실습 참여하여 실무 경험 획득',
    'employment',
    'high',
    CASE WHEN random() < 0.25 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.25 THEN 100 ELSE floor(random() * 50 + 20)::int END,
    CURRENT_DATE + interval '3 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '졸업 프로젝트 완료',
    '졸업논문 또는 졸업프로젝트 완료하여 전공 역량 증명',
    'project',
    'medium',
    CASE WHEN random() < 0.35 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.35 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2023
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

-- 2024 입학 (2학년) - 기타
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 심화과목 이수',
    '전공 심화 과목 B+ 이상 취득. 전공 역량 강화',
    'academic',
    'high',
    CASE WHEN random() < 0.4 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.4 THEN 100 ELSE floor(random() * 70 + 20)::int END,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '교내외 활동 참여',
    '동아리, 학회, 봉사활동 등 적극 참여하여 경험 쌓기',
    'activity',
    'medium',
    CASE WHEN random() < 0.5 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.5 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '6 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '진로 탐색 및 설계',
    '취업/대학원/창업 등 진로 방향 설정. 멘토링 참여',
    'career',
    'medium',
    CASE WHEN random() < 0.3 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.3 THEN 100 ELSE floor(random() * 50 + 20)::int END,
    CURRENT_DATE + interval '4 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2024
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

-- 2025 입학 (1학년) - 기타
INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '전공 기초과목 이수',
    '전공 기초과목 B+ 이상 취득. 전공 기초 역량 확보',
    'academic',
    'high',
    'active',
    floor(random() * 50 + 30)::int,
    CURRENT_DATE + interval '5 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '대학생활 적응',
    '학사일정 파악, 수강신청 방법 숙지, 캠퍼스 시설 활용',
    'activity',
    'medium',
    CASE WHEN random() < 0.7 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.7 THEN 100 ELSE floor(random() * 60 + 30)::int END,
    CURRENT_DATE + interval '1 month'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

INSERT INTO idino_career.tb_coaching_goal (std_id, title, description, goal_type, priority, status, progress_percentage, target_date)
SELECT
    s.student_id,
    '동아리/학회 가입',
    '전공 또는 관심분야 동아리, 학회 가입하여 선배 네트워킹',
    'activity',
    'medium',
    CASE WHEN random() < 0.6 THEN 'completed' ELSE 'active' END,
    CASE WHEN random() < 0.6 THEN 100 ELSE floor(random() * 60 + 20)::int END,
    CURRENT_DATE + interval '2 months'
FROM idino_career.tb_student s
JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
WHERE s.admission_year = 2025
AND d.department_nm NOT IN (
    '컴퓨터공학과', 'AI소프트웨어학과', '반도체·전자공학부', '전자공학과', '정보통신공학과', '소프트웨어학과', '의공학부', '의공학과', '의생명공학과', '게임학과', '멀티미디어학부', '멀티미디어학과',
    '간호학과', '의예과', '의학과', '약학과', '물리치료학과', '작업치료학과', '임상병리학과', '응급구조학과', '보건행정학과', '보건안전공학과', '제약공학과', '보건관리학과', '반려동물보건학과',
    '경영학과', '경찰·행정학과', '사회복지학과', '행정학과', '법학과',
    '교육학과', '상담심리치료학과', '유아교육과', '특수교육과', '초등교육과',
    '미디어커뮤니케이션학과', '실내건축학과', '음악학과', '건축학과', '디자인학과', '미술학과', '시각디자인학과'
);

-- 결과 확인
SELECT
    s.admission_year,
    COUNT(DISTINCT g.std_id) as students_with_goals,
    COUNT(g.goal_id) as total_goals,
    ROUND(COUNT(g.goal_id)::numeric / COUNT(DISTINCT g.std_id), 1) as avg_goals_per_student
FROM idino_career.tb_student s
JOIN idino_career.tb_coaching_goal g ON s.student_id = g.std_id
WHERE s.admission_year IN (2023, 2024, 2025)
GROUP BY s.admission_year
ORDER BY s.admission_year DESC;
