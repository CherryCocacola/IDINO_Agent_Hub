-- ============================================
-- IDINO Career - Portfolio Seed Data
-- Portfolio data linked to students by department/major
-- Created: 2026-01-26
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- Delete existing seed data
-- ============================================
DELETE FROM tb_portfolio WHERE ins_user_id = 'SEED_SCRIPT';

-- ============================================
-- Computer Science (DEPT001) Portfolios
-- ============================================

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
        ('github', 'Algorithm Study', 'https://github.com/{student_id}/algorithm-study', '알고리즘 문제 풀이 레포지토리 - LeetCode, 백준 1000+ 문제 해결'),
        ('github', 'ML Projects', 'https://github.com/{student_id}/ml-projects', '머신러닝 프로젝트 모음 - 이미지 분류, 자연어 처리, 추천 시스템'),
        ('notion', 'Tech Blog', 'https://notion.so/{student_id}/tech-blog', '기술 블로그 - Python, Java, 시스템 설계 관련 글 50+ 작성'),
        ('project', 'AI 챗봇 프로젝트', 'https://github.com/{student_id}/ai-chatbot', 'GPT API를 활용한 학교 문의 응답 챗봇 개발 (팀 프로젝트)'),
        ('paper', '딥러닝 기반 이미지 분류 연구', 'https://arxiv.org/abs/example/{student_id}', 'CNN과 Vision Transformer 비교 연구 논문 (학부연구생)')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT001'
AND s.current_grade >= 3;  -- 3, 4학년만

-- Computer Science 1, 2학년 (간단한 포트폴리오)
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
        ('github', 'Coding Practice', 'https://github.com/{student_id}/coding-practice', '코딩 연습 레포지토리 - Python, C 기초 프로젝트'),
        ('notion', '학습 노트', 'https://notion.so/{student_id}/study-notes', '프로그래밍 학습 기록 및 정리')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT001'
AND s.current_grade IN (1, 2);

-- ============================================
-- Software Engineering (DEPT002) Portfolios
-- ============================================

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
        ('github', 'React Portfolio', 'https://github.com/{student_id}/react-portfolio', 'React + TypeScript로 개발한 개인 포트폴리오 웹사이트'),
        ('github', 'Full Stack Project', 'https://github.com/{student_id}/fullstack-project', 'Node.js + React 기반 할일 관리 웹앱 (풀스택)'),
        ('notion', 'Project Documentation', 'https://notion.so/{student_id}/project-docs', '프로젝트 기획서, 설계 문서, 회고록 모음'),
        ('project', '캠퍼스 커뮤니티 앱', 'https://github.com/{student_id}/campus-community', 'Flutter로 개발한 학교 커뮤니티 앱 (팀 프로젝트, PM 역할)')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT002'
AND s.current_grade >= 3;

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
        ('github', 'Web Projects', 'https://github.com/{student_id}/web-projects', 'HTML, CSS, JavaScript 웹 프로젝트 모음'),
        ('notion', '개발 일지', 'https://notion.so/{student_id}/dev-journal', '웹 개발 학습 기록 및 프로젝트 진행 일지')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT002'
AND s.current_grade IN (1, 2);

-- ============================================
-- Statistics (DEPT013) Portfolios
-- ============================================

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
        ('github', 'Data Analysis Projects', 'https://github.com/{student_id}/data-analysis', '데이터 분석 프로젝트 - Pandas, NumPy, Matplotlib 활용'),
        ('github', 'Kaggle Competitions', 'https://kaggle.com/{student_id}', 'Kaggle 경진대회 참가 기록 - 상위 10% 달성'),
        ('notion', 'Statistics Notes', 'https://notion.so/{student_id}/stats-notes', '통계학 이론 정리 및 R/Python 실습 노트'),
        ('project', '서울시 교통 데이터 분석', 'https://github.com/{student_id}/traffic-analysis', '공공데이터 활용 교통량 예측 프로젝트 (데이터분석 경진대회 입상)'),
        ('paper', '시계열 분석을 통한 주가 예측 연구', 'https://papers.ssrn.com/{student_id}', 'ARIMA, LSTM 모델 비교 연구 (학부논문)')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT013'
AND s.current_grade >= 3;

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
        ('github', 'Python Practice', 'https://github.com/{student_id}/python-practice', 'Python 데이터 분석 기초 연습'),
        ('notion', '통계 학습 노트', 'https://notion.so/{student_id}/stats-study', '확률론, 통계학 학습 정리')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT013'
AND s.current_grade IN (1, 2);

-- ============================================
-- Business Administration (DEPT014) Portfolios
-- ============================================

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
        ('notion', 'Business Case Study', 'https://notion.so/{student_id}/case-study', '경영 전략 케이스 스터디 분석 20+ 편'),
        ('notion', 'Marketing Portfolio', 'https://notion.so/{student_id}/marketing', '마케팅 프로젝트 포트폴리오 - SNS 캠페인, 브랜드 분석'),
        ('project', '스타트업 사업계획서', 'https://notion.so/{student_id}/startup-plan', '창업경진대회 우수상 수상 사업계획서'),
        ('github', 'Data Analysis for Business', 'https://github.com/{student_id}/biz-analytics', '비즈니스 데이터 분석 - Excel, Python 활용')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT014'
AND s.current_grade >= 3;

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
        ('notion', '경영학 학습 노트', 'https://notion.so/{student_id}/biz-notes', '경영학원론, 회계원리 학습 정리'),
        ('notion', '팀 프로젝트 기록', 'https://notion.so/{student_id}/team-projects', '경영학과 팀 프로젝트 활동 기록')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT014'
AND s.current_grade IN (1, 2);

-- ============================================
-- Design (DEPT025) Portfolios
-- ============================================

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
        ('notion', 'UX/UI Portfolio', 'https://notion.so/{student_id}/ux-portfolio', 'UX/UI 디자인 포트폴리오 - 모바일 앱, 웹 서비스 15+ 프로젝트'),
        ('project', 'Figma Design System', 'https://figma.com/@{student_id}/design-system', '개인 디자인 시스템 라이브러리 (컴포넌트 100+)'),
        ('github', 'Interactive Prototypes', 'https://github.com/{student_id}/prototypes', 'Framer, Principle 인터랙션 프로토타입 모음'),
        ('paper', 'UX 리서치: 대학생 학습 앱 사용성 연구', 'https://uxjournal.org/{student_id}', '정성 조사 기반 UX 리서치 보고서 (학회 발표)')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT025'
AND s.current_grade >= 3;

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
        ('notion', 'Design Works', 'https://notion.so/{student_id}/design-works', '그래픽 디자인, 타이포그래피 작업물 모음'),
        ('project', 'Figma Practice', 'https://figma.com/@{student_id}/practice', 'Figma 연습 작업물 및 UI 클론')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT025'
AND s.current_grade IN (1, 2);

-- ============================================
-- Electronics Engineering (DEPT003) Portfolios
-- ============================================

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
        ('github', 'Embedded Projects', 'https://github.com/{student_id}/embedded', '임베디드 시스템 프로젝트 - Arduino, Raspberry Pi'),
        ('notion', 'Electronics Lab Notes', 'https://notion.so/{student_id}/lab-notes', '전자회로 실험 보고서 및 설계 문서'),
        ('project', 'IoT 스마트홈 시스템', 'https://github.com/{student_id}/smart-home', 'IoT 센서 기반 스마트홈 자동화 시스템 (졸업작품)'),
        ('paper', 'RF 회로 설계 최적화 연구', 'https://ieee.org/xplore/{student_id}', 'RF 신호처리 최적화 연구 논문')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT003'
AND s.current_grade >= 3;

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
        ('github', 'Circuit Projects', 'https://github.com/{student_id}/circuits', '기초 회로 설계 프로젝트'),
        ('notion', '전자공학 학습 노트', 'https://notion.so/{student_id}/ee-notes', '회로이론, 전자회로 학습 정리')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT003'
AND s.current_grade IN (1, 2);

-- ============================================
-- Industrial Engineering (DEPT006) Portfolios
-- ============================================

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
        ('notion', 'OR/Optimization Projects', 'https://notion.so/{student_id}/or-projects', '최적화 문제 해결 프로젝트 - 선형계획, 시뮬레이션'),
        ('github', 'Data Analytics', 'https://github.com/{student_id}/ie-analytics', '산업데이터 분석 프로젝트 - Python, R 활용'),
        ('project', '물류센터 최적화 시뮬레이션', 'https://github.com/{student_id}/logistics-sim', '물류 창고 배치 최적화 시뮬레이션 (산학협력 프로젝트)'),
        ('notion', 'PM Portfolio', 'https://notion.so/{student_id}/pm-portfolio', '프로젝트 관리 경험 포트폴리오 - 애자일, 스크럼 활용')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT006'
AND s.current_grade >= 3;

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
        ('notion', '산업공학 학습 노트', 'https://notion.so/{student_id}/ie-notes', '운영연구, 품질관리 학습 정리'),
        ('github', 'Python Projects', 'https://github.com/{student_id}/python-ie', 'Python 데이터 분석 연습')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT006'
AND s.current_grade IN (1, 2);

-- ============================================
-- Psychology (DEPT023) Portfolios
-- ============================================

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
        ('notion', 'UX Research Portfolio', 'https://notion.so/{student_id}/ux-research', 'UX 리서치 포트폴리오 - 사용자 인터뷰, 설문조사 10+ 건'),
        ('notion', 'Psychology Studies', 'https://notion.so/{student_id}/psych-studies', '심리학 연구 방법론 및 실험 설계 정리'),
        ('project', '사용자 행동 분석 연구', 'https://notion.so/{student_id}/user-behavior', '모바일 앱 사용자 행동 패턴 분석 연구 (학부연구)'),
        ('paper', '인지심리학 기반 UI 설계 가이드라인', 'https://psychology.org/{student_id}', '인지부하이론 적용 UI 설계 연구')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT023'
AND s.current_grade >= 3;

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
        ('notion', '심리학 학습 노트', 'https://notion.so/{student_id}/psych-notes', '발달심리, 인지심리 학습 정리'),
        ('notion', '실험심리 보고서', 'https://notion.so/{student_id}/experiment-reports', '심리학 실험 보고서 모음')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT023'
AND s.current_grade IN (1, 2);

-- ============================================
-- Mechanical Engineering (DEPT004) Portfolios
-- ============================================

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
        ('github', 'CAD/CAE Projects', 'https://github.com/{student_id}/cad-projects', '기계 설계 프로젝트 - SolidWorks, CATIA 활용'),
        ('notion', 'Engineering Portfolio', 'https://notion.so/{student_id}/mech-portfolio', '기계공학 프로젝트 포트폴리오 - 설계, 해석, 제작'),
        ('project', '로봇팔 설계 및 제어', 'https://github.com/{student_id}/robot-arm', '6축 로봇팔 설계 및 제어 시스템 개발 (캡스톤 프로젝트)'),
        ('paper', '유체역학 시뮬레이션 연구', 'https://asme.org/{student_id}', 'CFD 기반 유체 흐름 최적화 연구')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT004'
AND s.current_grade >= 3;

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
        ('notion', '기계공학 학습 노트', 'https://notion.so/{student_id}/mech-notes', '재료역학, 열역학 학습 정리'),
        ('github', 'MATLAB Projects', 'https://github.com/{student_id}/matlab-projects', 'MATLAB 기초 프로젝트')
) AS portfolio_data(artifact_type, title, url, description)
WHERE s.department_cd = 'DEPT004'
AND s.current_grade IN (1, 2);

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    portfolio_count INT;
    dept_counts TEXT;
BEGIN
    SELECT COUNT(*) INTO portfolio_count FROM tb_portfolio WHERE ins_user_id = 'SEED_SCRIPT';

    SELECT string_agg(d.department_cd || ': ' || COALESCE(cnt, 0), ', ')
    INTO dept_counts
    FROM tb_department d
    LEFT JOIN (
        SELECT department_cd, COUNT(*) as cnt
        FROM tb_portfolio p
        JOIN tb_student s ON p.student_id = s.student_id
        WHERE p.ins_user_id = 'SEED_SCRIPT'
        GROUP BY department_cd
    ) pc ON d.department_cd = pc.department_cd
    WHERE d.department_cd IN ('DEPT001', 'DEPT002', 'DEPT003', 'DEPT006', 'DEPT013', 'DEPT014', 'DEPT023', 'DEPT025');

    RAISE NOTICE '=== Portfolio Seed Data Created ===';
    RAISE NOTICE 'Total tb_portfolio: % records', portfolio_count;
    RAISE NOTICE 'By Department: %', dept_counts;
END $$;
