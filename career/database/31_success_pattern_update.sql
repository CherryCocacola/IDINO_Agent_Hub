-- ============================================
-- IDINO Career - Success Pattern Update
-- 취업 성공 패턴 전공/이수과목 매칭 개선
-- 실제 학과코드 사용: 2059(컴공), 1160(컴응과), 3554(AI소프트), 1101(데이터정보), 1440(경영), 436(디자인)
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. 기존 성공 패턴 삭제 및 재생성
-- ============================================

DELETE FROM tb_success_pattern;

-- ============================================
-- 2. 컴퓨터공학과 (2059) 성공 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- 백엔드 개발자 (ROLE07)
('백엔드 개발자 취업 성공 패턴', 'employment', '2059', 'ROLE07',
 '컴퓨터공학과 학생의 백엔드 개발자 취업 성공 패턴. 자료구조, 알고리즘, 데이터베이스 중심 학습 권장.',
 '3.3-4.0', ARRAY['CS201', 'CS301', 'CS302', 'CS303', 'CS401'],
 ARRAY['프로젝트 2개 이상', '포트폴리오 작성', '코딩 테스트 준비'],
 ARRAY['Java', 'Python', 'SQL', 'Spring Boot', 'REST API'],
 '{"1학년": "기초 프로그래밍", "2학년": "자료구조/알고리즘", "3학년": "데이터베이스/웹개발", "4학년": "프로젝트/취업준비"}'::jsonb,
 0.85, 48, 'SYSTEM', CURRENT_TIMESTAMP),

-- AI 엔지니어 (ROLE06)
('AI 엔지니어 취업 성공 패턴', 'employment', '2059', 'ROLE06',
 '컴퓨터공학과 학생의 AI 엔지니어 취업 성공 패턴. 머신러닝, 딥러닝 과목 필수.',
 '3.5-4.5', ARRAY['CS202', 'CS301', 'CS401', 'CS402', 'MA301'],
 ARRAY['연구실 참여', 'AI 프로젝트', '논문 작성'],
 ARRAY['Python', 'PyTorch', 'TensorFlow', 'Mathematics', 'Statistics'],
 '{"1학년": "프로그래밍/수학기초", "2학년": "확률통계/선형대수", "3학년": "머신러닝/딥러닝", "4학년": "연구/프로젝트"}'::jsonb,
 0.81, 32, 'SYSTEM', CURRENT_TIMESTAMP),

-- 풀스택 개발자 (ROLE01 - 소프트웨어 엔지니어)
('풀스택 개발자 취업 성공 패턴', 'employment', '2059', 'ROLE01',
 '컴퓨터공학과 학생의 풀스택 개발자 취업 성공 패턴. 프론트엔드와 백엔드 모두 경험 필요.',
 '3.2-4.0', ARRAY['CS201', 'CS301', 'CS302', 'SW301', 'SW401'],
 ARRAY['프로젝트 3개 이상', '포트폴리오', '해커톤 참여'],
 ARRAY['JavaScript', 'React', 'Node.js', 'SQL', 'REST API', 'Git'],
 '{"1학년": "웹 기초", "2학년": "프론트엔드", "3학년": "백엔드/DB", "4학년": "풀스택 프로젝트"}'::jsonb,
 0.79, 45, 'SYSTEM', CURRENT_TIMESTAMP),

-- 데이터분석가 (ROLE09)
('데이터분석가 취업 성공 패턴 (컴공)', 'employment', '2059', 'ROLE09',
 '컴퓨터공학과 학생의 데이터분석가 취업 성공 패턴. SQL, Python 필수.',
 '3.4-4.0', ARRAY['CS201', 'CS301', 'CS402', 'ST301', 'ST302'],
 ARRAY['데이터 분석 프로젝트', 'ADsP 자격증'],
 ARRAY['Python', 'SQL', 'Pandas', 'Visualization', 'Statistics'],
 '{"1학년": "프로그래밍 기초", "2학년": "통계/SQL", "3학년": "데이터분석", "4학년": "실무 프로젝트"}'::jsonb,
 0.76, 38, 'SYSTEM', CURRENT_TIMESTAMP),

-- 정보보안전문가 (ROLE10)
('정보보안전문가 취업 성공 패턴', 'employment', '2059', 'ROLE10',
 '컴퓨터공학과 학생의 정보보안전문가 취업 성공 패턴. 네트워크, 시스템 이해 필수.',
 '3.4-4.0', ARRAY['CS303', 'CS404', 'CS203', 'CS301', 'CS302'],
 ARRAY['보안 자격증', '인턴십', 'CTF 참여'],
 ARRAY['Network', 'Linux', 'Security', 'Cryptography'],
 '{"1학년": "시스템 기초", "2학년": "네트워크/OS", "3학년": "보안 과목", "4학년": "자격증/인턴"}'::jsonb,
 0.74, 30, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 3. 컴퓨터응용과학과 (1160) 성공 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- 프론트엔드 개발자
('프론트엔드 개발자 취업 성공 패턴', 'employment', '1160', 'ROLE08',
 '컴퓨터응용과학과 학생의 프론트엔드 개발자 취업 성공 패턴. UI/UX, JavaScript 중심.',
 '3.2-4.0', ARRAY['SW201', 'SW301', 'SW302', 'SW401'],
 ARRAY['UI/UX 프로젝트', '포트폴리오 웹사이트'],
 ARRAY['JavaScript', 'React', 'TypeScript', 'HTML/CSS', 'Git'],
 '{"1학년": "HTML/CSS", "2학년": "JavaScript", "3학년": "React/Vue", "4학년": "포트폴리오"}'::jsonb,
 0.82, 52, 'SYSTEM', CURRENT_TIMESTAMP),

-- 웹 개발자
('웹 개발자 취업 성공 패턴', 'employment', '1160', 'ROLE08',
 '컴퓨터응용과학과 학생의 웹 개발자 취업 성공 패턴.',
 '3.0-3.8', ARRAY['SW201', 'SW301', 'SW303', 'SW402'],
 ARRAY['웹 프로젝트', '코딩 테스트 준비'],
 ARRAY['JavaScript', 'Node.js', 'React', 'SQL'],
 '{"1학년": "웹 기초", "2학년": "프론트엔드", "3학년": "백엔드", "4학년": "풀스택"}'::jsonb,
 0.78, 60, 'SYSTEM', CURRENT_TIMESTAMP),

-- 모바일 앱 개발자
('모바일 앱 개발자 취업 성공 패턴', 'employment', '1160', 'ROLE01',
 '컴퓨터응용과학과 학생의 모바일 앱 개발자 취업 성공 패턴.',
 '3.2-4.0', ARRAY['SW201', 'SW302', 'SW401', 'SW403'],
 ARRAY['앱 출시 경험', '포트폴리오'],
 ARRAY['Kotlin', 'Swift', 'React Native', 'Flutter'],
 '{"1학년": "프로그래밍 기초", "2학년": "모바일 기초", "3학년": "네이티브 개발", "4학년": "앱 출시"}'::jsonb,
 0.75, 35, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 4. AI소프트웨어학부 (3554) 성공 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- AI 엔지니어
('AI 엔지니어 취업 성공 패턴 (AI학부)', 'employment', '3554', 'ROLE06',
 'AI소프트웨어학부 학생의 AI 엔지니어 취업 성공 패턴. 딥러닝, MLOps 필수.',
 '3.5-4.5', ARRAY['AI201', 'AI301', 'AI302', 'AI401', 'AI402'],
 ARRAY['Kaggle 참여', '연구실 경험', 'AI 논문 작성'],
 ARRAY['Python', 'PyTorch', 'TensorFlow', 'MLOps', 'Docker'],
 '{"1학년": "수학/프로그래밍", "2학년": "ML 기초", "3학년": "DL/NLP/CV", "4학년": "연구/프로젝트"}'::jsonb,
 0.88, 42, 'SYSTEM', CURRENT_TIMESTAMP),

-- ML 엔지니어
('ML 엔지니어 취업 성공 패턴', 'employment', '3554', 'ROLE06',
 'AI소프트웨어학부 학생의 ML 엔지니어 취업 성공 패턴.',
 '3.4-4.5', ARRAY['AI201', 'AI301', 'AI401', 'CS302'],
 ARRAY['ML 프로젝트', '데이터 파이프라인 구축'],
 ARRAY['Python', 'Scikit-learn', 'SQL', 'Spark', 'AWS'],
 '{"1학년": "프로그래밍/수학", "2학년": "ML 기초", "3학년": "ML 심화", "4학년": "MLOps"}'::jsonb,
 0.84, 38, 'SYSTEM', CURRENT_TIMESTAMP),

-- 데이터 사이언티스트
('데이터 사이언티스트 취업 성공 패턴', 'employment', '3554', 'ROLE09',
 'AI소프트웨어학부 학생의 데이터 사이언티스트 취업 성공 패턴.',
 '3.5-4.5', ARRAY['AI201', 'AI302', 'ST301', 'ST302'],
 ARRAY['분석 프로젝트', '시각화 포트폴리오', 'ADsP/ADP 자격증'],
 ARRAY['Python', 'R', 'SQL', 'Statistics', 'Visualization'],
 '{"1학년": "통계/프로그래밍", "2학년": "데이터분석", "3학년": "ML/시각화", "4학년": "실무 프로젝트"}'::jsonb,
 0.82, 35, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 5. 데이터정보학과 (1101) 성공 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- 데이터분석가
('데이터분석가 취업 성공 패턴', 'employment', '1101', 'ROLE09',
 '데이터정보학과 학생의 데이터분석가 취업 성공 패턴.',
 '3.3-4.0', ARRAY['DS201', 'DS301', 'DS302', 'ST301'],
 ARRAY['분석 프로젝트', 'SQL 자격증', '시각화 포트폴리오'],
 ARRAY['Python', 'SQL', 'Tableau', 'Statistics', 'Excel'],
 '{"1학년": "통계 기초", "2학년": "SQL/Python", "3학년": "분석 심화", "4학년": "실무 프로젝트"}'::jsonb,
 0.85, 55, 'SYSTEM', CURRENT_TIMESTAMP),

-- 데이터 엔지니어
('데이터 엔지니어 취업 성공 패턴', 'employment', '1101', 'ROLE05',
 '데이터정보학과 학생의 데이터 엔지니어 취업 성공 패턴.',
 '3.4-4.0', ARRAY['DS201', 'DS302', 'CS302', 'CS303'],
 ARRAY['데이터 파이프라인 프로젝트', 'AWS 자격증'],
 ARRAY['Python', 'SQL', 'Spark', 'Airflow', 'AWS'],
 '{"1학년": "프로그래밍", "2학년": "데이터베이스", "3학년": "빅데이터", "4학년": "클라우드"}'::jsonb,
 0.80, 40, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 6. 경영학과 (1440) 성공 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- 경영컨설턴트
('경영컨설턴트 취업 성공 패턴', 'employment', '1440', 'ROLE11',
 '경영학과 학생의 경영컨설턴트 취업 성공 패턴.',
 '3.7-4.5', ARRAY['BA201', 'BA301', 'BA302', 'BA401'],
 ARRAY['컨설팅 공모전', '학회 활동', '인턴십'],
 ARRAY['PowerPoint', 'Excel', 'Problem Solving', 'Communication'],
 '{"1학년": "경영 기초", "2학년": "재무/마케팅", "3학년": "전략/컨설팅", "4학년": "인턴/취업"}'::jsonb,
 0.72, 28, 'SYSTEM', CURRENT_TIMESTAMP),

-- 마케팅 전문가
('마케팅 전문가 취업 성공 패턴', 'employment', '1440', 'ROLE12',
 '경영학과 학생의 마케팅 전문가 취업 성공 패턴.',
 '3.3-4.0', ARRAY['BA201', 'BA302', 'BA403', 'MK301'],
 ARRAY['마케팅 공모전', '인턴십', 'SNS 마케팅 경험'],
 ARRAY['Marketing', 'Data Analysis', 'Communication', 'Creative'],
 '{"1학년": "경영 기초", "2학년": "마케팅 원론", "3학년": "디지털마케팅", "4학년": "실무 경험"}'::jsonb,
 0.78, 45, 'SYSTEM', CURRENT_TIMESTAMP),

-- 프로덕트 매니저
('프로덕트 매니저 취업 성공 패턴', 'employment', '1440', 'ROLE03',
 '경영학과 학생의 프로덕트 매니저 취업 성공 패턴.',
 '3.4-4.0', ARRAY['BA201', 'BA302', 'CS101', 'SW101'],
 ARRAY['IT 프로젝트 경험', '애자일 방법론 학습'],
 ARRAY['Product Management', 'Data Analysis', 'Communication', 'Agile'],
 '{"1학년": "경영/IT 기초", "2학년": "마케팅/UX", "3학년": "프로젝트 관리", "4학년": "PM 인턴"}'::jsonb,
 0.75, 32, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 7. 디자인학부 (436) 성공 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- UI/UX 디자이너
('UI/UX 디자이너 취업 성공 패턴', 'employment', '436', 'ROLE04',
 '디자인학부 학생의 UI/UX 디자이너 취업 성공 패턴.',
 '3.3-4.0', ARRAY['DES201', 'DES301', 'DES302', 'DES401'],
 ARRAY['UI/UX 포트폴리오', '디자인 공모전'],
 ARRAY['Figma', 'Sketch', 'Adobe XD', 'Prototyping', 'User Research'],
 '{"1학년": "디자인 기초", "2학년": "UI 디자인", "3학년": "UX 리서치", "4학년": "포트폴리오"}'::jsonb,
 0.85, 48, 'SYSTEM', CURRENT_TIMESTAMP),

-- 웹 디자이너
('웹 디자이너 취업 성공 패턴', 'employment', '436', 'ROLE04',
 '디자인학부 학생의 웹 디자이너 취업 성공 패턴.',
 '3.0-3.8', ARRAY['DES201', 'DES301', 'SW201'],
 ARRAY['웹 포트폴리오', 'HTML/CSS 학습'],
 ARRAY['Photoshop', 'Illustrator', 'Figma', 'HTML/CSS'],
 '{"1학년": "디자인 기초", "2학년": "그래픽 디자인", "3학년": "웹 디자인", "4학년": "포트폴리오"}'::jsonb,
 0.80, 42, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 8. 대학원 진학 패턴
-- ============================================

INSERT INTO tb_success_pattern (
    pattern_nm, pattern_type, department_cd, role_cd, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size, ins_user_id, ins_dt
) VALUES
-- AI 대학원
('AI 대학원 진학 성공 패턴', 'graduate_school', '3554', NULL,
 'AI소프트웨어학부 학생의 AI 대학원 진학 성공 패턴.',
 '3.8-4.5', ARRAY['AI301', 'AI302', 'AI401', 'AI402', 'MA301'],
 ARRAY['연구실 참여', '논문 작성', '학회 발표'],
 ARRAY['Deep Learning', 'Research', 'Mathematics', 'Paper Writing'],
 '{"2학년": "연구실 탐색", "3학년": "연구 참여", "4학년": "대학원 준비"}'::jsonb,
 0.75, 25, 'SYSTEM', CURRENT_TIMESTAMP),

-- 컴퓨터공학 대학원
('컴퓨터공학 대학원 진학 성공 패턴', 'graduate_school', '2059', NULL,
 '컴퓨터공학과 학생의 대학원 진학 성공 패턴.',
 '3.7-4.5', ARRAY['CS301', 'CS401', 'CS402', 'CS404'],
 ARRAY['연구실 참여', '논문 작성', '프로젝트 참여'],
 ARRAY['Research', 'Programming', 'Paper Writing', 'Presentation'],
 '{"2학년": "기초 강화", "3학년": "연구실 참여", "4학년": "대학원 준비"}'::jsonb,
 0.72, 30, 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 9. 패턴 매칭 함수 생성
-- ============================================

CREATE OR REPLACE FUNCTION fn_calculate_pattern_match(
    p_student_id VARCHAR,
    p_pattern_id UUID
) RETURNS NUMERIC AS $$
DECLARE
    v_student RECORD;
    v_pattern RECORD;
    v_score NUMERIC := 0;
    v_total_weight NUMERIC := 0;
    v_course_match INT := 0;
    v_skill_match INT := 0;
BEGIN
    -- 학생 정보 조회
    SELECT s.*, gs.cumulative_gpa
    INTO v_student
    FROM tb_student s
    LEFT JOIN tb_grade_summary gs ON s.student_id = gs.student_id
    WHERE s.student_id = p_student_id;

    -- 패턴 정보 조회
    SELECT * INTO v_pattern
    FROM tb_success_pattern
    WHERE pattern_id = p_pattern_id;

    IF v_student IS NULL OR v_pattern IS NULL THEN
        RETURN 0;
    END IF;

    -- 1. GPA 매칭 (가중치 25%)
    IF v_student.cumulative_gpa IS NOT NULL THEN
        v_total_weight := v_total_weight + 25;
        IF v_student.cumulative_gpa >= SPLIT_PART(v_pattern.typical_gpa_range, '-', 1)::NUMERIC THEN
            v_score := v_score + 25;
        ELSIF v_student.cumulative_gpa >= SPLIT_PART(v_pattern.typical_gpa_range, '-', 1)::NUMERIC - 0.3 THEN
            v_score := v_score + 15;
        ELSE
            v_score := v_score + 5;
        END IF;
    END IF;

    -- 2. 필수 과목 이수 여부 (가중치 35%)
    SELECT COUNT(*) INTO v_course_match
    FROM tb_enrollment e
    JOIN tb_course c ON e.course_id = c.course_id
    WHERE e.student_id = p_student_id
      AND c.course_cd = ANY(v_pattern.key_courses)
      AND e.status IN ('completed', 'pass');

    v_total_weight := v_total_weight + 35;
    v_score := v_score + (v_course_match::NUMERIC / GREATEST(array_length(v_pattern.key_courses, 1), 1) * 35);

    -- 3. 스킬 매칭 (가중치 25%)
    SELECT COUNT(*) INTO v_skill_match
    FROM tb_student_skill ss
    JOIN tb_skill sk ON ss.skill_id = sk.skill_id
    WHERE ss.student_id = p_student_id
      AND sk.skill_nm = ANY(v_pattern.key_skills)
      AND ss.skill_level >= 3;

    v_total_weight := v_total_weight + 25;
    v_score := v_score + (v_skill_match::NUMERIC / GREATEST(array_length(v_pattern.key_skills, 1), 1) * 25);

    -- 4. 학과 일치 (가중치 15%)
    v_total_weight := v_total_weight + 15;
    IF v_student.department_cd = v_pattern.department_cd THEN
        v_score := v_score + 15;
    ELSIF v_student.department_cd IN ('2059', '1160', '3554')
      AND v_pattern.department_cd IN ('2059', '1160', '3554') THEN
        -- IT 계열 학과 간 부분 매칭
        v_score := v_score + 10;
    END IF;

    RETURN ROUND(v_score, 2);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_calculate_pattern_match IS '학생과 성공 패턴 간의 매칭 점수 계산 (0-100)';

-- ============================================
-- 확인 쿼리
-- ============================================

-- SELECT * FROM tb_success_pattern ORDER BY department_cd, pattern_nm;
-- SELECT fn_calculate_pattern_match('STU2024001', (SELECT pattern_id FROM tb_success_pattern LIMIT 1));
