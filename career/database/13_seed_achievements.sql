-- ============================================
-- Seed Data: tb_achievement (Excel Format Standard)
-- Date: 2026-01-26
-- Achievement Types: certificate, language, award, publication
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. CERTIFICATE ACHIEVEMENTS (IT/Professional Certifications)
-- ============================================

INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, competency_contributions, verified, ins_user_id, ins_dt) VALUES
-- DEPT001 (Computer Science) Students
('2021001001', 'certificate', '정보처리기사', '한국산업인력공단', '2024-06-15', NULL, '기사', NULL, '{"technical": 0.3, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021001002', 'certificate', 'SQLD (SQL 개발자)', '한국데이터산업진흥원', '2024-03-20', NULL, '전문가', NULL, '{"technical": 0.25, "data_analysis": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021001003', 'certificate', 'AWS Solutions Architect Associate', 'Amazon Web Services', '2024-09-10', '2027-09-10', 'Associate', NULL, '{"technical": 0.35, "cloud": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001001', 'certificate', '정보처리산업기사', '한국산업인력공단', '2024-11-20', NULL, '산업기사', NULL, '{"technical": 0.2, "problem_solving": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001002', 'certificate', '리눅스마스터 2급', '한국정보통신진흥협회', '2024-05-15', NULL, '2급', NULL, '{"technical": 0.2, "system": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023001001', 'certificate', '네트워크관리사 2급', '한국정보통신자격협회', '2024-08-10', NULL, '2급', NULL, '{"technical": 0.15, "network": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023001002', 'certificate', 'ADSP (데이터분석 준전문가)', '한국데이터산업진흥원', '2025-01-15', NULL, '준전문가', NULL, '{"technical": 0.2, "data_analysis": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024001001', 'certificate', 'ITQ 엑셀 A등급', '한국생산성본부', '2024-09-20', NULL, 'A등급', NULL, '{"digital_literacy": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT002 (Software Engineering) Students
('2021002001', 'certificate', '정보처리기사', '한국산업인력공단', '2024-05-10', NULL, '기사', NULL, '{"technical": 0.3, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002002', 'certificate', 'OCJP (Oracle Certified Java Programmer)', 'Oracle', '2024-07-25', NULL, 'Professional', NULL, '{"technical": 0.35, "java": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022002001', 'certificate', 'Kubernetes Administrator (CKA)', 'CNCF', '2024-10-15', '2027-10-15', 'Administrator', NULL, '{"technical": 0.4, "devops": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022002002', 'certificate', 'AWS Developer Associate', 'Amazon Web Services', '2024-08-20', '2027-08-20', 'Associate', NULL, '{"technical": 0.3, "cloud": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023002001', 'certificate', 'SQLD (SQL 개발자)', '한국데이터산업진흥원', '2025-01-10', NULL, '전문가', NULL, '{"technical": 0.25, "data_analysis": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024002001', 'certificate', '컴퓨터활용능력 1급', '대한상공회의소', '2024-11-05', NULL, '1급', NULL, '{"digital_literacy": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT003 (Electrical Engineering) Students
('2021003001', 'certificate', '전기기사', '한국산업인력공단', '2024-06-20', NULL, '기사', NULL, '{"technical": 0.35, "electrical": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021003002', 'certificate', '전자기사', '한국산업인력공단', '2024-05-15', NULL, '기사', NULL, '{"technical": 0.35, "electronics": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022003001', 'certificate', '임베디드SW개발전문가', 'TTA', '2024-09-10', NULL, '전문가', NULL, '{"technical": 0.3, "embedded": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023003001', 'certificate', '전기산업기사', '한국산업인력공단', '2024-11-15', NULL, '산업기사', NULL, '{"technical": 0.25, "electrical": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT014 (Business Administration) Students
('2021014001', 'certificate', '경영지도사', '한국산업인력공단', '2024-07-10', NULL, '지도사', NULL, '{"business": 0.4, "management": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014002', 'certificate', 'AFPK (재무설계사)', '한국FPSB', '2024-08-20', NULL, 'AFPK', NULL, '{"finance": 0.35, "planning": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022014001', 'certificate', 'ERP정보관리사 회계', '한국생산성본부', '2024-06-15', NULL, '1급', NULL, '{"accounting": 0.3, "erp": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023014001', 'certificate', '전산세무 2급', '한국세무사회', '2024-12-10', NULL, '2급', NULL, '{"accounting": 0.25, "tax": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT013 (Statistics) Students
('2021013001', 'certificate', '빅데이터분석기사', '한국데이터산업진흥원', '2024-09-05', NULL, '기사', NULL, '{"data_analysis": 0.4, "statistics": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022013001', 'certificate', 'ADsP (데이터분석 준전문가)', '한국데이터산업진흥원', '2024-03-20', NULL, '준전문가', NULL, '{"data_analysis": 0.25, "statistics": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023013001', 'certificate', '사회조사분석사 2급', '한국산업인력공단', '2024-11-20', NULL, '2급', NULL, '{"research": 0.25, "statistics": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- DEPT006 (Mechanical Engineering) Students
('2021006001', 'certificate', '기계설계기사', '한국산업인력공단', '2024-06-25', NULL, '기사', NULL, '{"technical": 0.35, "mechanical": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022006001', 'certificate', '일반기계기사', '한국산업인력공단', '2024-08-15', NULL, '기사', NULL, '{"technical": 0.3, "mechanical": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023006001', 'certificate', 'AutoCAD 국제자격증', 'Autodesk', '2024-05-10', NULL, 'Professional', NULL, '{"technical": 0.2, "cad": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- 2025 Students (Recent certifications)
('2025001001', 'certificate', 'ITQ 한글 A등급', '한국생산성본부', '2025-01-10', NULL, 'A등급', NULL, '{"digital_literacy": 0.1}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025002001', 'certificate', '컴퓨터활용능력 2급', '대한상공회의소', '2025-01-15', NULL, '2급', NULL, '{"digital_literacy": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025014001', 'certificate', 'MOS Excel Expert', 'Microsoft', '2025-01-20', NULL, 'Expert', NULL, '{"digital_literacy": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 2. LANGUAGE ACHIEVEMENTS
-- ============================================

INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, competency_contributions, verified, ins_user_id, ins_dt) VALUES
-- TOEIC Scores
('2021001001', 'language', 'TOEIC', 'ETS', '2024-08-15', '2026-08-15', 'Advanced', '925', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021001002', 'language', 'TOEIC', 'ETS', '2024-06-20', '2026-06-20', 'Advanced', '890', '{"communication": 0.28, "global": 0.23}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002001', 'language', 'TOEIC', 'ETS', '2024-09-10', '2026-09-10', 'Advanced', '945', '{"communication": 0.32, "global": 0.27}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001001', 'language', 'TOEIC', 'ETS', '2024-11-05', '2026-11-05', 'Intermediate', '785', '{"communication": 0.22, "global": 0.18}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022002001', 'language', 'TOEIC', 'ETS', '2024-10-20', '2026-10-20', 'Advanced', '865', '{"communication": 0.26, "global": 0.22}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023001001', 'language', 'TOEIC', 'ETS', '2025-01-10', '2027-01-10', 'Intermediate', '750', '{"communication": 0.2, "global": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014001', 'language', 'TOEIC', 'ETS', '2024-07-25', '2026-07-25', 'Advanced', '910', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014002', 'language', 'TOEIC', 'ETS', '2024-05-30', '2026-05-30', 'Advanced', '875', '{"communication": 0.27, "global": 0.22}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- TOEIC Speaking
('2021001003', 'language', 'TOEIC Speaking', 'ETS', '2024-10-15', '2026-10-15', 'Level 7', '170', '{"communication": 0.35, "presentation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002002', 'language', 'TOEIC Speaking', 'ETS', '2024-08-20', '2026-08-20', 'Level 8', '190', '{"communication": 0.4, "presentation": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022014001', 'language', 'TOEIC Speaking', 'ETS', '2024-09-25', '2026-09-25', 'Level 6', '150', '{"communication": 0.28, "presentation": 0.22}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- OPIC
('2021001001', 'language', 'OPIc', 'ACTFL', '2024-09-20', '2026-09-20', 'IH', 'IH', '{"communication": 0.35, "global": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014001', 'language', 'OPIc', 'ACTFL', '2024-11-10', '2026-11-10', 'AL', 'AL', '{"communication": 0.4, "global": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001002', 'language', 'OPIc', 'ACTFL', '2024-12-05', '2026-12-05', 'IM3', 'IM3', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- TEPS
('2021003001', 'language', 'TEPS', '서울대학교 언어교육원', '2024-07-15', '2026-07-15', '1등급', '478', '{"communication": 0.32, "academic": 0.28}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022003001', 'language', 'TEPS', '서울대학교 언어교육원', '2024-10-10', '2026-10-10', '2등급', '398', '{"communication": 0.25, "academic": 0.22}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Japanese (JPT, JLPT)
('2021001002', 'language', 'JLPT N2', '일본국제교류기금', '2024-07-10', NULL, 'N2', 'N2', '{"communication": 0.25, "global": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022002002', 'language', 'JPT', '일본어능력시험위원회', '2024-09-15', '2026-09-15', '상급', '750', '{"communication": 0.28, "global": 0.23}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014002', 'language', 'JLPT N1', '일본국제교류기금', '2024-12-05', NULL, 'N1', 'N1', '{"communication": 0.35, "global": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Chinese (HSK)
('2021014001', 'language', 'HSK 5급', '중국국가한반', '2024-06-20', NULL, '5급', '230', '{"communication": 0.3, "global": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022014001', 'language', 'HSK 4급', '중국국가한반', '2024-11-15', NULL, '4급', '265', '{"communication": 0.22, "global": 0.18}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- 2025 Students Language
('2025001002', 'language', 'TOEIC', 'ETS', '2025-01-05', '2027-01-05', 'Intermediate', '720', '{"communication": 0.18, "global": 0.12}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025014002', 'language', 'TOEIC', 'ETS', '2025-01-18', '2027-01-18', 'Intermediate', '765', '{"communication": 0.2, "global": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 3. AWARD ACHIEVEMENTS (Competition Awards)
-- ============================================

INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, competency_contributions, verified, ins_user_id, ins_dt) VALUES
-- Programming/Hackathon Awards
('2021001001', 'award', '대학생 프로그래밍 경진대회 금상', '한국정보올림피아드', '2024-09-20', NULL, '금상', NULL, '{"technical": 0.4, "problem_solving": 0.35, "teamwork": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021001003', 'award', '카카오 코드 페스티벌 3등', '카카오', '2024-10-15', NULL, '3등', NULL, '{"technical": 0.35, "algorithm": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002001', 'award', 'Junction Asia 해커톤 대상', 'Junction', '2024-08-25', NULL, '대상', NULL, '{"technical": 0.35, "creativity": 0.3, "teamwork": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002002', 'award', 'ICPC 아시아 리저널 동메달', 'ICPC', '2024-11-10', NULL, '동메달', NULL, '{"technical": 0.4, "algorithm": 0.45, "teamwork": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001001', 'award', '삼성 알고리즘 역량강화 Pro 등급', '삼성전자', '2024-06-30', NULL, 'Pro', NULL, '{"technical": 0.35, "algorithm": 0.4}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001002', 'award', '네이버 개발자 컨퍼런스 장려상', '네이버', '2024-10-20', NULL, '장려상', NULL, '{"technical": 0.3, "presentation": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022002001', 'award', '구글 솔루션 챌린지 Top 50', 'Google', '2024-07-15', NULL, 'Top 50', NULL, '{"technical": 0.35, "creativity": 0.3, "social_impact": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023001001', 'award', '교내 프로그래밍 경시대회 은상', '서울대학교', '2024-12-10', NULL, '은상', NULL, '{"technical": 0.25, "problem_solving": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023001002', 'award', 'ACM-ICPC 예선 통과', 'ACM', '2024-10-25', NULL, '예선 통과', NULL, '{"technical": 0.3, "algorithm": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- AI/Data Science Competition Awards
('2021013001', 'award', 'DACON AI 경진대회 금상', 'DACON', '2024-09-30', NULL, '금상', NULL, '{"data_analysis": 0.4, "ml": 0.35, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022013001', 'award', '공공데이터 활용 창업경진대회 최우수상', '행정안전부', '2024-11-05', NULL, '최우수상', NULL, '{"data_analysis": 0.35, "creativity": 0.3, "presentation": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021001002', 'award', '빅콘테스트 챔피언부문 장려상', '한국정보화진흥원', '2024-10-30', NULL, '장려상', NULL, '{"data_analysis": 0.35, "statistics": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Business Competition Awards
('2021014001', 'award', '창업 아이디어 경진대회 대상', '중소벤처기업부', '2024-08-20', NULL, '대상', NULL, '{"business": 0.4, "creativity": 0.35, "presentation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014002', 'award', '마케팅 전략 공모전 금상', '대한상공회의소', '2024-09-15', NULL, '금상', NULL, '{"marketing": 0.4, "creativity": 0.3, "teamwork": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022014001', 'award', '사회적 기업 아이디어 공모전 은상', '고용노동부', '2024-10-25', NULL, '은상', NULL, '{"social_impact": 0.35, "business": 0.3, "presentation": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2023014001', 'award', '교내 창업 아이디어 경진대회 장려상', '서울대학교 창업지원단', '2024-12-05', NULL, '장려상', NULL, '{"business": 0.25, "creativity": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Engineering Competition Awards
('2021003001', 'award', '임베디드 소프트웨어 경진대회 은상', '산업통상자원부', '2024-11-20', NULL, '은상', NULL, '{"technical": 0.35, "embedded": 0.4, "creativity": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021003002', 'award', '스마트디바이스 공학경진대회 동상', '한국전자통신연구원', '2024-09-25', NULL, '동상', NULL, '{"technical": 0.3, "electronics": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022003001', 'award', 'IoT 아이디어 공모전 장려상', 'KT', '2024-08-30', NULL, '장려상', NULL, '{"technical": 0.25, "iot": 0.3, "creativity": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021006001', 'award', '기계설계 창의 경진대회 금상', '한국기계산업진흥회', '2024-10-10', NULL, '금상', NULL, '{"technical": 0.35, "mechanical": 0.4, "creativity": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022006001', 'award', '3D프린팅 아이디어 경진대회 은상', '3D프린팅산업협회', '2024-11-15', NULL, '은상', NULL, '{"technical": 0.3, "design": 0.35, "creativity": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 4. PUBLICATION ACHIEVEMENTS
-- ============================================

INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, competency_contributions, verified, ins_user_id, ins_dt) VALUES
-- Conference Papers
('2021001001', 'publication', 'Deep Learning 기반 자연어 처리 모델 성능 개선에 관한 연구', '한국정보과학회', '2024-10-20', NULL, 'KCI등재', NULL, '{"research": 0.4, "technical": 0.35, "writing": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021001003', 'publication', 'Transformer 모델의 경량화 기법 비교 분석', '한국컴퓨터종합학술대회', '2024-06-25', NULL, '학술대회', NULL, '{"research": 0.35, "technical": 0.3, "presentation": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002001', 'publication', '마이크로서비스 아키텍처에서의 효율적인 로깅 시스템 설계', '한국소프트웨어공학학회', '2024-11-15', NULL, 'KCI등재후보', NULL, '{"research": 0.35, "technical": 0.35, "writing": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002002', 'publication', 'Kubernetes 기반 자동 스케일링 최적화 연구', '대한전자공학회', '2024-09-10', NULL, '학술대회', NULL, '{"research": 0.3, "technical": 0.35, "devops": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021003001', 'publication', 'Edge Computing 환경에서의 실시간 데이터 처리 기법', '한국통신학회', '2024-08-20', NULL, 'SCI', NULL, '{"research": 0.45, "technical": 0.4, "writing": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021003002', 'publication', 'FPGA 기반 CNN 가속기 설계 및 구현', '대한전자공학회', '2024-07-15', NULL, 'KCI등재', NULL, '{"research": 0.4, "technical": 0.4, "hardware": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021013001', 'publication', '시계열 데이터 분석을 위한 새로운 이상치 탐지 알고리즘', '한국통계학회', '2024-10-05', NULL, 'KCI등재', NULL, '{"research": 0.4, "statistics": 0.4, "writing": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022013001', 'publication', '머신러닝 기반 고객 이탈 예측 모델 연구', '한국데이터정보과학회', '2024-12-10', NULL, '학술대회', NULL, '{"research": 0.3, "data_analysis": 0.35, "ml": 0.25}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Patents
('2021001001', 'publication', '딥러닝 기반 이미지 분류 시스템 및 방법', '특허청', '2024-11-25', NULL, '특허출원', '10-2024-XXXXX', '{"research": 0.35, "technical": 0.4, "innovation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021002001', 'publication', '분산 시스템에서의 효율적인 데이터 동기화 방법', '특허청', '2024-10-30', NULL, '특허출원', '10-2024-YYYYY', '{"research": 0.35, "technical": 0.4, "innovation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021003001', 'publication', 'IoT 센서 데이터 압축 전송 장치 및 방법', '특허청', '2024-09-15', NULL, '특허등록', '10-2024-ZZZZZ', '{"research": 0.4, "technical": 0.45, "innovation": 0.35}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021006001', 'publication', '3D 프린팅을 이용한 정밀 부품 제조 방법', '특허청', '2024-08-10', NULL, '특허출원', '10-2024-AAAAA', '{"research": 0.3, "mechanical": 0.35, "innovation": 0.3}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- 5. ADDITIONAL ACHIEVEMENTS (Mixed Types)
-- ============================================

INSERT INTO tb_achievement (student_id, achievement_type, title, issuer, issue_date, expire_date, level, score, competency_contributions, verified, ins_user_id, ins_dt) VALUES
-- More Certificates
('2024001002', 'certificate', 'GTQ (그래픽기술자격) 1급', '한국생산성본부', '2024-12-15', NULL, '1급', NULL, '{"design": 0.25, "digital_literacy": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024002002', 'certificate', '웹디자인기능사', '한국산업인력공단', '2025-01-10', NULL, '기능사', NULL, '{"design": 0.2, "technical": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024003001', 'certificate', '3D프린터운용기능사', '한국산업인력공단', '2024-11-25', NULL, '기능사', NULL, '{"technical": 0.15, "manufacturing": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024014002', 'certificate', '유통관리사 2급', '대한상공회의소', '2025-01-05', NULL, '2급', NULL, '{"business": 0.2, "logistics": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024013001', 'certificate', '사회조사분석사 2급', '한국산업인력공단', '2025-01-20', NULL, '2급', NULL, '{"statistics": 0.2, "research": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- More Awards (2024/2025 students)
('2024001001', 'award', '신입생 프로그래밍 경진대회 장려상', '서울대학교 컴퓨터공학부', '2024-12-20', NULL, '장려상', NULL, '{"technical": 0.15, "problem_solving": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2024002001', 'award', '교내 해커톤 참가상', '서울대학교 소프트웨어학부', '2024-11-30', NULL, '참가상', NULL, '{"technical": 0.1, "teamwork": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2025001003', 'award', '코딩 부트캠프 수료 우수상', '삼성 멀티캠퍼스', '2025-01-25', NULL, '우수상', NULL, '{"technical": 0.2, "learning": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- Volunteer/Social Activities
('2021001001', 'certificate', 'SW 교육 봉사활동 100시간 인증서', '한국정보화진흥원', '2024-12-10', NULL, '우수', '100시간', '{"social_impact": 0.25, "communication": 0.2, "leadership": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2021014001', 'certificate', '창업 멘토링 활동 인증서', '중소벤처기업진흥공단', '2024-11-20', NULL, '인증', '50시간', '{"leadership": 0.25, "communication": 0.2, "business": 0.15}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('2022001001', 'certificate', '오픈소스 컨트리뷰션 아카데미 수료', '정보통신산업진흥원', '2024-10-30', NULL, '수료', NULL, '{"technical": 0.25, "collaboration": 0.2, "open_source": 0.2}', 'Y', 'SYSTEM', CURRENT_TIMESTAMP);

-- ============================================
-- Verify inserted data
-- ============================================
SELECT achievement_type, COUNT(*) as count
FROM tb_achievement
GROUP BY achievement_type
ORDER BY achievement_type;
