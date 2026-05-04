-- ============================================
-- IDINO Career - Seed Data Supplement
-- Date: 2026-01-29
-- Purpose: 누락 데이터 보완 (학번별 검증 + 스킬패스포트 + 포트폴리오)
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- C-1: 학번별 데이터 검증 및 보완
-- 2023/2024/2025 학번에 누락된 tb_achievement, tb_portfolio, tb_activity 보완
-- ============================================

-- ============================================
-- SECTION 1: 2023학번 (2학년) Achievement 보완
-- ============================================
INSERT INTO tb_achievement (student_id, achievement_type, achievement_nm, issuing_org, issue_date, verified_fg, ins_user_id, ins_dt)
SELECT val.student_id, val.achievement_type, val.achievement_nm, val.issuing_org, val.issue_date::date, 'Y', 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  -- 컴퓨터공학과 2023
  ('2023010001', 'certification', 'SQLD', '한국데이터산업진흥원', '2025-03-15'),
  ('2023010002', 'certification', 'TOEIC 850', 'ETS', '2025-01-20'),
  ('2023010003', 'certification', '정보처리산업기사', '한국산업인력공단', '2025-06-10'),
  -- 소프트웨어공학과 2023
  ('2023020001', 'certification', 'AWS Cloud Practitioner', 'Amazon', '2025-04-12'),
  ('2023020002', 'certification', 'TOEIC 800', 'ETS', '2025-02-18'),
  ('2023020003', 'certification', 'OCJP', 'Oracle', '2025-05-22'),
  -- 전자공학과 2023
  ('2023030001', 'certification', '전자기사', '한국산업인력공단', '2025-07-05'),
  ('2023030002', 'certification', 'TOEIC 780', 'ETS', '2025-03-10'),
  -- 경영학과 2023
  ('2023140001', 'certification', '매경TEST 우수', '매일경제', '2025-04-20'),
  ('2023140002', 'certification', 'TOEIC 820', 'ETS', '2025-05-15'),
  -- 통계학과 2023
  ('2023130001', 'certification', 'ADsP', '한국데이터산업진흥원', '2025-06-08'),
  ('2023130002', 'certification', 'TOEIC 830', 'ETS', '2025-02-25')
) AS val(student_id, achievement_type, achievement_nm, issuing_org, issue_date)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_achievement a
  WHERE a.student_id = val.student_id AND a.achievement_nm = val.achievement_nm
);

-- ============================================
-- SECTION 2: 2024학번 (1학년) Achievement 보완
-- ============================================
INSERT INTO tb_achievement (student_id, achievement_type, achievement_nm, issuing_org, issue_date, verified_fg, ins_user_id, ins_dt)
SELECT val.student_id, val.achievement_type, val.achievement_nm, val.issuing_org, val.issue_date::date, 'Y', 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  -- 컴퓨터공학과 2024
  ('2024010001', 'certification', 'TOEIC 750', 'ETS', '2025-09-10'),
  ('2024010002', 'certification', 'TOEIC 720', 'ETS', '2025-11-15'),
  ('2024010003', 'award', '교내 프로그래밍 대회 장려상', '한국과기대', '2025-12-05'),
  -- 소프트웨어공학과 2024
  ('2024020001', 'certification', 'TOEIC 700', 'ETS', '2025-10-20'),
  ('2024020002', 'award', '교내 해커톤 입상', '한국과기대', '2025-11-25'),
  -- 경영학과 2024
  ('2024140001', 'certification', 'TOEIC 680', 'ETS', '2025-09-30'),
  ('2024140002', 'certification', '컴퓨터활용능력 2급', '대한상공회의소', '2025-10-15'),
  -- 통계학과 2024
  ('2024130001', 'certification', 'TOEIC 710', 'ETS', '2025-10-05')
) AS val(student_id, achievement_type, achievement_nm, issuing_org, issue_date)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_achievement a
  WHERE a.student_id = val.student_id AND a.achievement_nm = val.achievement_nm
);

-- ============================================
-- SECTION 3: 2025학번 (1학년) Achievement 보완
-- ============================================
INSERT INTO tb_achievement (student_id, achievement_type, achievement_nm, issuing_org, issue_date, verified_fg, ins_user_id, ins_dt)
SELECT val.student_id, val.achievement_type, val.achievement_nm, val.issuing_org, val.issue_date::date, 'Y', 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  ('2025010001', 'certification', 'TOEIC 700', 'ETS', '2025-12-10'),
  ('2025010003', 'certification', 'TOEIC 680', 'ETS', '2025-11-20'),
  ('2025020001', 'certification', 'TOEIC 720', 'ETS', '2025-12-15'),
  ('2025140001', 'certification', '컴퓨터활용능력 2급', '대한상공회의소', '2025-11-30'),
  ('2025130001', 'certification', 'TOEIC 690', 'ETS', '2025-12-05')
) AS val(student_id, achievement_type, achievement_nm, issuing_org, issue_date)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_achievement a
  WHERE a.student_id = val.student_id AND a.achievement_nm = val.achievement_nm
);

-- ============================================
-- C-2: 스킬 패스포트 데이터 검증 및 보완
-- tb_student_skill: 전공 연관 스킬 보강
-- tb_student_badge: 성취 기반 배지 보강
-- ============================================

-- 2025학번 학생 스킬 보완 (tb_student_skill)
INSERT INTO tb_student_skill (student_id, skill_cd, current_level, target_level, learning_source, ins_user_id, ins_dt)
SELECT val.student_id, val.skill_cd, val.current_level, val.target_level, val.learning_source, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  -- 컴퓨터공학과 2025 (기초 스킬)
  ('2025010001', 'SK001', 1, 4, 'course'), -- Python
  ('2025010001', 'SK003', 1, 3, 'course'), -- Java
  ('2025010001', 'SK007', 1, 3, 'self'),   -- SQL
  ('2025010002', 'SK001', 2, 4, 'course'),
  ('2025010002', 'SK003', 1, 4, 'course'),
  ('2025010002', 'SK007', 1, 3, 'course'),
  ('2025010003', 'SK001', 1, 4, 'course'),
  ('2025010003', 'SK010', 1, 3, 'self'),   -- Statistics
  ('2025010004', 'SK001', 2, 4, 'course'),
  ('2025010004', 'SK002', 1, 3, 'self'),   -- JavaScript
  ('2025010005', 'SK001', 1, 3, 'course'),
  ('2025010005', 'SK013', 1, 3, 'self'),   -- Security
  ('2025010006', 'SK001', 1, 3, 'course'),
  ('2025010006', 'SK012', 1, 4, 'self'),   -- DevOps
  ('2025010007', 'SK001', 2, 5, 'course'),
  ('2025010007', 'SK004', 1, 4, 'self'),   -- ML
  ('2025010008', 'SK001', 1, 3, 'course'),
  ('2025010008', 'SK011', 1, 4, 'self'),   -- Cloud

  -- 소프트웨어공학과 2025
  ('2025020001', 'SK002', 2, 4, 'course'),
  ('2025020001', 'SK001', 1, 3, 'course'),
  ('2025020002', 'SK003', 1, 4, 'course'),
  ('2025020002', 'SK002', 1, 3, 'self'),
  ('2025020003', 'SK002', 1, 3, 'course'),
  ('2025020003', 'SK006', 1, 3, 'self'),   -- UX
  ('2025020004', 'SK003', 2, 4, 'course'),
  ('2025020004', 'SK007', 1, 3, 'course'),
  ('2025020005', 'SK001', 1, 3, 'course'),
  ('2025020005', 'SK008', 1, 3, 'self'),   -- Testing
  ('2025020006', 'SK002', 1, 4, 'course'),
  ('2025020006', 'SK001', 1, 3, 'self'),

  -- 경영학과 2025
  ('2025140001', 'SK010', 1, 3, 'course'),
  ('2025140001', 'SK014', 1, 3, 'self'),   -- Communication
  ('2025140002', 'SK014', 2, 4, 'course'),
  ('2025140002', 'SK015', 1, 3, 'self'),   -- Marketing
  ('2025140003', 'SK010', 1, 3, 'course'),
  ('2025140003', 'SK016', 1, 3, 'self'),   -- Finance
  ('2025140004', 'SK014', 1, 3, 'course'),
  ('2025140004', 'SK017', 1, 3, 'self'),   -- PM
  ('2025140005', 'SK014', 1, 4, 'course'),
  ('2025140005', 'SK018', 1, 3, 'self'),   -- HR
  ('2025140006', 'SK014', 1, 3, 'course'),
  ('2025140006', 'SK010', 1, 3, 'self'),

  -- 통계학과 2025
  ('2025130001', 'SK001', 1, 4, 'course'),
  ('2025130001', 'SK010', 2, 4, 'course'),
  ('2025130002', 'SK001', 2, 5, 'course'),
  ('2025130002', 'SK004', 1, 4, 'self'),
  ('2025130003', 'SK001', 1, 4, 'course'),
  ('2025130003', 'SK010', 1, 4, 'course'),
  ('2025130004', 'SK001', 1, 3, 'course'),
  ('2025130004', 'SK010', 2, 5, 'course'),
  ('2025130005', 'SK010', 1, 4, 'course'),
  ('2025130005', 'SK001', 1, 3, 'self')
) AS val(student_id, skill_cd, current_level, target_level, learning_source)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_student_skill ss
  WHERE ss.student_id = val.student_id AND ss.skill_cd = val.skill_cd
);

-- 2025학번 배지 보완 (tb_student_badge)
INSERT INTO tb_student_badge (student_id, badge_cd, earned_at, ins_user_id, ins_dt)
SELECT val.student_id, val.badge_cd, val.earned_at::timestamp, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  ('2025010001', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010002', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010003', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010004', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010005', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010006', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010007', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025010008', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025020001', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025020002', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025020003', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025020004', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025020005', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025020006', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025140001', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025140002', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025140003', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025140004', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025140005', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025140006', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025130001', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025130002', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025130003', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025130004', 'BADGE_NEWCOMER', '2025-09-01 09:00:00'),
  ('2025130005', 'BADGE_NEWCOMER', '2025-09-01 09:00:00')
) AS val(student_id, badge_cd, earned_at)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_student_badge sb
  WHERE sb.student_id = val.student_id AND sb.badge_cd = val.badge_cd
);

-- 성취 기반 배지: 2023학번 자격증 취득자에게 CERT 배지
INSERT INTO tb_student_badge (student_id, badge_cd, earned_at, ins_user_id, ins_dt)
SELECT val.student_id, val.badge_cd, val.earned_at::timestamp, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  ('2023010001', 'BADGE_CERT_1', '2025-03-15 10:00:00'),
  ('2023010003', 'BADGE_CERT_1', '2025-06-10 10:00:00'),
  ('2023020001', 'BADGE_CERT_1', '2025-04-12 10:00:00'),
  ('2023020003', 'BADGE_CERT_1', '2025-05-22 10:00:00'),
  ('2023030001', 'BADGE_CERT_1', '2025-07-05 10:00:00'),
  ('2023130001', 'BADGE_CERT_1', '2025-06-08 10:00:00')
) AS val(student_id, badge_cd, earned_at)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_student_badge sb
  WHERE sb.student_id = val.student_id AND sb.badge_cd = val.badge_cd
);

-- ============================================
-- C-3: 포트폴리오 데이터 보완
-- 전공/이수과목/관심직업 관련 포트폴리오
-- ============================================

INSERT INTO tb_portfolio (student_id, portfolio_type, title, description, url, ins_user_id, ins_dt)
SELECT val.student_id, val.portfolio_type, val.title, val.description, val.url, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  -- 컴퓨터공학과 4학년 (2021)
  ('2021010001', 'github', 'Spring Boot REST API 프로젝트', '백엔드 개발 포트폴리오 - Spring Boot + JPA + PostgreSQL 기반 REST API', 'https://github.com/minjun-kim/spring-api'),
  ('2021010001', 'project', '캡스톤 프로젝트: AI 추천 시스템', 'TensorFlow를 활용한 개인화 추천 시스템 개발', NULL),
  ('2021010002', 'github', 'AI/ML 프로젝트 모음', 'PyTorch, TensorFlow 기반 딥러닝 프로젝트', 'https://github.com/seoyeon-lee/ai-projects'),
  ('2021010003', 'notion', '풀스택 개발 포트폴리오', 'React + Node.js 기반 웹 애플리케이션 개발 정리', 'https://notion.so/jiho-portfolio'),

  -- 소프트웨어공학과 4학년 (2021)
  ('2021020001', 'github', '프론트엔드 프로젝트', 'React, Vue.js 기반 SPA 개발 포트폴리오', 'https://github.com/yuna-shin/frontend'),
  ('2021020002', 'project', '캡스톤: 모바일 헬스케어 앱', 'Flutter 기반 건강관리 앱 개발', NULL),

  -- 컴퓨터공학과 3학년 (2022)
  ('2022010001', 'github', '데이터 분석 프로젝트', 'Python/Pandas 기반 데이터 분석 및 시각화', 'https://github.com/yeeun-choi/data-analysis'),
  ('2022010002', 'project', '웹 서비스 개발 프로젝트', 'Django + React 풀스택 웹 서비스', NULL),

  -- 소프트웨어공학과 3학년 (2022)
  ('2022020001', 'github', 'DevOps 파이프라인', 'Docker, K8s, Jenkins 기반 CI/CD 구축', 'https://github.com/nayeon-kwon/devops'),
  ('2022020002', 'project', '백엔드 API 개발', 'Express.js + MongoDB 기반 RESTful API', NULL),

  -- 경영학과 3학년 (2022)
  ('2022140001', 'notion', '마케팅 사례 분석', '글로벌 기업 마케팅 전략 분석 포트폴리오', 'https://notion.so/minseo-marketing'),
  ('2022140002', 'project', '경영 컨설팅 프로젝트', '중소기업 경영 개선 컨설팅 보고서', NULL),

  -- 통계학과 3학년 (2022)
  ('2022130001', 'github', 'R 통계 분석 포트폴리오', 'R 기반 통계 분석 및 데이터 시각화 프로젝트', 'https://github.com/hayoung-park/r-stats'),
  ('2022130002', 'github', 'AI/ML 연구 프로젝트', 'Kaggle 대회 참가 프로젝트 모음', 'https://github.com/woohyuk-choi/ml-research'),

  -- 컴퓨터공학과 2학년 (2023)
  ('2023010001', 'github', '학습 프로젝트 모음', 'Python, Java 학습 프로젝트', 'https://github.com/junseo-yoon/learning'),
  ('2023010002', 'project', '프론트엔드 개인 프로젝트', 'React 기반 개인 블로그 개발', NULL),

  -- 경영학과 2학년 (2023)
  ('2023140001', 'notion', '경영 분석 노트', '재무분석 및 사업계획서 작성', 'https://notion.so/subin-biz'),

  -- 통계학과 2학년 (2023)
  ('2023130001', 'github', '데이터 분석 연습', 'Python/R 기반 통계 분석 연습', 'https://github.com/yewon-jung/data-practice'),

  -- 디자인학과 4학년 (2021)
  ('2021250001', 'project', 'UX/UI 디자인 포트폴리오', 'Figma 기반 모바일/웹 UI 디자인 프로젝트', NULL),
  ('2021250002', 'notion', '비주얼 디자인 아카이브', 'Adobe Creative Suite 작업물 모음', 'https://notion.so/minjae-design'),

  -- 심리학과 3학년 (2022)
  ('2022230001', 'project', 'UX 리서치 보고서', '사용자 경험 연구 방법론 및 결과 보고서', NULL),

  -- 전자공학과 3학년 (2022)
  ('2022030001', 'github', '임베디드 시스템 프로젝트', 'Arduino/Raspberry Pi 기반 IoT 프로젝트', 'https://github.com/harin-jung/embedded'),
  ('2022030002', 'project', '반도체 공정 시뮬레이션', 'MATLAB 기반 반도체 공정 분석', NULL)
) AS val(student_id, portfolio_type, title, description, url)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_portfolio p
  WHERE p.student_id = val.student_id AND p.title = val.title
);

-- ============================================
-- 2025학번 학생 기초 역량 데이터 보완 (tb_student_competency)
-- ============================================
INSERT INTO tb_student_competency (student_id, competency_cd, score, percentile, ins_user_id, ins_dt)
SELECT val.student_id, val.competency_cd, val.score, val.percentile, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  -- 2025 CS students
  ('2025010001', 'COMP001', 45, 40), ('2025010001', 'COMP002', 42, 38),
  ('2025010001', 'COMP003', 40, 35), ('2025010001', 'COMP004', 38, 30),
  ('2025010001', 'COMP005', 35, 28), ('2025010001', 'COMP006', 40, 35),
  ('2025010002', 'COMP001', 48, 45), ('2025010002', 'COMP002', 45, 42),
  ('2025010002', 'COMP003', 42, 38), ('2025010002', 'COMP004', 40, 35),
  ('2025010002', 'COMP005', 38, 32), ('2025010002', 'COMP006', 43, 40),
  ('2025010003', 'COMP001', 43, 38), ('2025010003', 'COMP002', 40, 35),
  ('2025010003', 'COMP003', 38, 32), ('2025010003', 'COMP004', 42, 38),
  ('2025010003', 'COMP005', 40, 35), ('2025010003', 'COMP006', 38, 32),
  ('2025010004', 'COMP001', 50, 48), ('2025010004', 'COMP002', 48, 45),
  ('2025010004', 'COMP003', 45, 42), ('2025010004', 'COMP004', 42, 38),
  ('2025010004', 'COMP005', 40, 35), ('2025010004', 'COMP006', 45, 42),

  -- 2025 Business students
  ('2025140001', 'COMP001', 40, 35), ('2025140001', 'COMP002', 38, 32),
  ('2025140001', 'COMP003', 45, 42), ('2025140001', 'COMP004', 48, 45),
  ('2025140001', 'COMP005', 42, 38), ('2025140001', 'COMP006', 40, 35),
  ('2025140002', 'COMP001', 38, 32), ('2025140002', 'COMP002', 35, 28),
  ('2025140002', 'COMP003', 48, 45), ('2025140002', 'COMP004', 50, 48),
  ('2025140002', 'COMP005', 45, 42), ('2025140002', 'COMP006', 42, 38),

  -- 2025 Statistics students
  ('2025130001', 'COMP001', 48, 45), ('2025130001', 'COMP002', 45, 42),
  ('2025130001', 'COMP003', 40, 35), ('2025130001', 'COMP004', 42, 38),
  ('2025130001', 'COMP005', 38, 32), ('2025130001', 'COMP006', 43, 40),
  ('2025130002', 'COMP001', 50, 48), ('2025130002', 'COMP002', 48, 45),
  ('2025130002', 'COMP003', 42, 38), ('2025130002', 'COMP004', 40, 35),
  ('2025130002', 'COMP005', 35, 28), ('2025130002', 'COMP006', 45, 42)
) AS val(student_id, competency_cd, score, percentile)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_student_competency sc
  WHERE sc.student_id = val.student_id AND sc.competency_cd = val.competency_cd
);

-- ============================================
-- 2025학번 학생 학점 요약 보완 (tb_cumulative_summary)
-- ============================================
INSERT INTO tb_cumulative_summary (student_id, completed_credits, cumulative_gpa, major_credits, liberal_credits, elective_credits, graduation_readiness_pct, ins_user_id, ins_dt)
SELECT val.student_id, val.completed_credits, val.cumulative_gpa, val.major_credits, val.liberal_credits, val.elective_credits, val.graduation_pct, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  ('2025010001', 18, 3.85, 9, 6, 3, 13.8),
  ('2025010002', 18, 3.72, 9, 6, 3, 13.8),
  ('2025010003', 18, 3.90, 9, 6, 3, 13.8),
  ('2025010004', 21, 4.05, 12, 6, 3, 16.2),
  ('2025010005', 18, 3.65, 9, 6, 3, 13.8),
  ('2025010006', 18, 3.78, 9, 6, 3, 13.8),
  ('2025010007', 21, 4.10, 12, 6, 3, 16.2),
  ('2025010008', 18, 3.70, 9, 6, 3, 13.8),
  ('2025020001', 18, 3.80, 9, 6, 3, 13.8),
  ('2025020002', 18, 3.68, 9, 6, 3, 13.8),
  ('2025020003', 18, 3.75, 9, 6, 3, 13.8),
  ('2025020004', 21, 3.95, 12, 6, 3, 16.2),
  ('2025020005', 18, 3.82, 9, 6, 3, 13.8),
  ('2025020006', 18, 3.70, 9, 6, 3, 13.8),
  ('2025140001', 18, 3.88, 9, 6, 3, 13.8),
  ('2025140002', 18, 3.72, 9, 6, 3, 13.8),
  ('2025140003', 21, 4.00, 12, 6, 3, 16.2),
  ('2025140004', 18, 3.75, 9, 6, 3, 13.8),
  ('2025140005', 18, 3.80, 9, 6, 3, 13.8),
  ('2025140006', 18, 3.62, 9, 6, 3, 13.8),
  ('2025130001', 18, 3.90, 9, 6, 3, 13.8),
  ('2025130002', 21, 4.05, 12, 6, 3, 16.2),
  ('2025130003', 18, 3.82, 9, 6, 3, 13.8),
  ('2025130004', 18, 3.78, 9, 6, 3, 13.8),
  ('2025130005', 18, 3.85, 9, 6, 3, 13.8)
) AS val(student_id, completed_credits, cumulative_gpa, major_credits, liberal_credits, elective_credits, graduation_pct)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_cumulative_summary cs
  WHERE cs.student_id = val.student_id
);

-- ============================================
-- 비교과활동 데이터 보완 (tb_activity)
-- 2023/2024/2025 학번 학생들의 비교과활동
-- ============================================
INSERT INTO tb_activity (student_id, title, activity_type, status, start_date, end_date, hours, description, ins_user_id, ins_dt)
SELECT val.student_id, val.title, val.activity_type, val.status, val.start_date::date, val.end_date, val.hours, val.description, 'SYSTEM', CURRENT_TIMESTAMP
FROM (VALUES
  -- 2023학번 비교과활동
  ('2023010001', '알고리즘 스터디', 'study', 'completed', '2025-03-01', '2025-06-30'::date, 80, 'Python 알고리즘 문제풀이 스터디'),
  ('2023010001', '교내 프로그래밍 대회', 'competition', 'completed', '2025-05-15', '2025-05-15'::date, 8, '알고리즘 프로그래밍 대회 참가'),
  ('2023010002', '웹개발 동아리', 'club', 'in_progress', '2025-03-01', NULL, 120, 'React/Node.js 기반 웹개발 동아리'),
  ('2023010003', '오픈소스 컨트리뷰톤', 'project', 'completed', '2025-07-01', '2025-08-31'::date, 60, '오픈소스 프로젝트 기여 활동'),
  ('2023020001', 'AWS 클라우드 교육', 'education', 'completed', '2025-04-01', '2025-04-30'::date, 40, 'AWS 기초 과정 수료'),
  ('2023020002', '코딩 멘토링', 'mentoring', 'in_progress', '2025-09-01', NULL, 30, '후배 대상 프로그래밍 멘토링'),
  ('2023140001', '마케팅 공모전', 'competition', 'completed', '2025-04-01', '2025-06-30'::date, 50, '대학생 마케팅 전략 공모전'),
  ('2023140002', '경영 사례 스터디', 'study', 'completed', '2025-03-01', '2025-05-31'::date, 60, 'HBS 케이스 스터디 그룹'),
  ('2023130001', '데이터 분석 프로젝트', 'project', 'completed', '2025-05-01', '2025-07-31'::date, 80, 'Kaggle 대회 팀 프로젝트'),
  ('2023130002', '통계 세미나', 'seminar', 'completed', '2025-06-01', '2025-06-30'::date, 16, '통계학과 주최 학술 세미나'),

  -- 2024학번 비교과활동
  ('2024010001', '프로그래밍 입문 스터디', 'study', 'in_progress', '2025-09-01', NULL, 40, 'Python 기초 학습 스터디'),
  ('2024010002', '코딩 동아리', 'club', 'in_progress', '2025-09-01', NULL, 60, '학과 코딩 동아리 활동'),
  ('2024020001', '해커톤 참가', 'competition', 'completed', '2025-11-15', '2025-11-16'::date, 24, '교내 해커톤 대회 참가'),
  ('2024140001', '경영학 독서 모임', 'study', 'in_progress', '2025-09-01', NULL, 20, '경영 관련 도서 토론 모임'),

  -- 2025학번 비교과활동
  ('2025010001', '신입생 오리엔테이션', 'seminar', 'completed', '2025-09-02', '2025-09-02'::date, 4, '학과 신입생 OT'),
  ('2025010002', '프로그래밍 기초반', 'education', 'in_progress', '2025-09-15', NULL, 30, '프로그래밍 기초 교육과정'),
  ('2025020001', '웹개발 입문 스터디', 'study', 'in_progress', '2025-10-01', NULL, 20, 'HTML/CSS/JS 기초 스터디'),
  ('2025140001', '경영학 입문 세미나', 'seminar', 'completed', '2025-09-10', '2025-09-10'::date, 3, '경영학과 학과소개 세미나'),
  ('2025130001', '통계 프로그래밍 입문', 'education', 'in_progress', '2025-09-15', NULL, 24, 'R 프로그래밍 기초 과정')
) AS val(student_id, title, activity_type, status, start_date, end_date, hours, description)
WHERE NOT EXISTS (
  SELECT 1 FROM tb_activity a
  WHERE a.student_id = val.student_id AND a.title = val.title
);

-- ============================================
-- END OF SUPPLEMENT DATA
-- ============================================
