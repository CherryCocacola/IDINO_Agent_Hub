-- ============================================
-- IDINO Career - Additional Opportunities Seed Data
-- Target: 50+ opportunities total
-- Created: 2026-01-26
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- Additional Internships (15개 추가)
-- ============================================

INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
-- IT 대기업 인턴
('internship', '삼성SDS 클라우드 인턴십', '삼성SDS', '기업용 클라우드 플랫폼 개발 및 운영 경험', '{"min_gpa": 3.3, "skills": ["AWS", "Kubernetes", "Java"], "grade": [3, 4]}', '{"salary": "월 300만원", "meal": true, "housing": true}', '2025-06-01', '2025-06-30', '2025-08-01', '2025-10-31', '서울특별시 송파구', FALSE, 20, 'open', ARRAY['클라우드', 'DevOps', 'Java'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP002": 0.3}', '{"SKL008": 0.5, "SKL002": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '두나무 블록체인 개발 인턴', '두나무', '업비트 블록체인 기술 개발 인턴십', '{"min_gpa": 3.5, "skills": ["Solidity", "JavaScript", "Node.js"], "grade": [3, 4]}', '{"salary": "월 350만원", "meal": true}', '2025-07-01', '2025-07-31', '2025-09-01', '2025-11-30', '서울특별시 강남구', TRUE, 8, 'open', ARRAY['블록체인', 'Web3', 'Crypto'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL003": 0.5, "SKL001": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '당근마켓 ML 엔지니어 인턴', '당근마켓', '추천 시스템 및 ML 파이프라인 개발', '{"min_gpa": 3.6, "skills": ["Python", "PyTorch", "SQL"], "grade": [3, 4]}', '{"salary": "월 380만원", "meal": true, "stock": true}', '2025-05-15', '2025-06-15', '2025-07-15', '2025-09-30', '서울특별시 서초구', TRUE, 6, 'open', ARRAY['ML', '추천시스템', 'Python'], ARRAY['DEPT001', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL005": 0.5, "SKL001": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '토스 서버 개발 인턴', '비바리퍼블리카', '핀테크 서버 및 결제 시스템 개발', '{"min_gpa": 3.5, "skills": ["Kotlin", "Spring Boot", "MySQL"], "grade": [3, 4]}', '{"salary": "월 400만원", "meal": true}', '2025-08-01', '2025-08-31', '2025-10-01', '2025-12-31', '서울특별시 강남구', FALSE, 15, 'open', ARRAY['핀테크', 'Kotlin', 'Spring'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP003": 0.3}', '{"SKL002": 0.5, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '쏘카 데이터 엔지니어 인턴', '쏘카', '차량 데이터 파이프라인 및 분석 시스템 개발', '{"min_gpa": 3.4, "skills": ["Python", "Spark", "AWS"], "grade": [3, 4]}', '{"salary": "월 280만원", "meal": true}', '2025-06-15', '2025-07-15', '2025-08-15', '2025-10-31', '서울특별시 성동구', TRUE, 10, 'open', ARRAY['데이터엔지니어링', 'Spark', 'AWS'], ARRAY['DEPT001', 'DEPT013'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL001": 0.4, "SKL008": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '네이버 Z (제페토) 3D 개발 인턴', '네이버Z', '메타버스 플랫폼 3D 콘텐츠 개발', '{"min_gpa": 3.3, "skills": ["Unity", "C#", "3D Modeling"], "grade": [3, 4]}', '{"salary": "월 320만원", "meal": true}', '2025-07-01', '2025-07-31', '2025-09-01', '2025-11-30', '경기도 성남시 분당구', FALSE, 12, 'open', ARRAY['메타버스', 'Unity', '3D'], ARRAY['DEPT001', 'DEPT025'], '{"COMP001": 0.4, "COMP002": 0.3}', '{"SKL003": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '배달의민족 UX 리서치 인턴', '우아한형제들', 'UX 리서치 및 사용자 조사 인턴십', '{"min_gpa": 3.4, "skills": ["UX Research", "Figma"], "grade": [3, 4]}', '{"salary": "월 300만원", "meal": true, "books": true}', '2025-05-01', '2025-05-31', '2025-07-01', '2025-08-31', '서울특별시 송파구', TRUE, 5, 'open', ARRAY['UX리서치', 'Figma', '사용자조사'], ARRAY['DEPT025', 'DEPT023'], '{"COMP002": 0.5, "COMP003": 0.3}', '{"SKL009": 0.4, "SKL010": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '야놀자 Platform 개발 인턴', '야놀자', '여행 플랫폼 백엔드 시스템 개발', '{"min_gpa": 3.3, "skills": ["Java", "Spring", "Redis"], "grade": [3, 4]}', '{"salary": "월 290만원", "meal": true}', '2025-08-15', '2025-09-15', '2025-10-15', '2025-12-31', '서울특별시 강남구', FALSE, 10, 'open', ARRAY['여행플랫폼', 'Java', 'Redis'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP003": 0.3}', '{"SKL002": 0.5, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '무신사 데이터 분석 인턴', '무신사', '패션 이커머스 데이터 분석 및 마케팅 인사이트 도출', '{"min_gpa": 3.3, "skills": ["Python", "SQL", "Tableau"], "grade": [3, 4]}', '{"salary": "월 270만원", "meal": true, "fashion_discount": true}', '2025-06-01', '2025-06-30', '2025-08-01', '2025-09-30', '서울특별시 성동구', TRUE, 8, 'open', ARRAY['데이터분석', 'Tableau', '이커머스'], ARRAY['DEPT013', 'DEPT014'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL007": 0.5, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '리디 iOS 개발 인턴', '리디', '전자책 플랫폼 iOS 앱 개발', '{"min_gpa": 3.4, "skills": ["Swift", "iOS", "Xcode"], "grade": [3, 4]}', '{"salary": "월 280만원", "meal": true, "books": true}', '2025-07-15', '2025-08-15', '2025-09-15', '2025-11-30', '서울특별시 강남구', TRUE, 5, 'open', ARRAY['iOS', 'Swift', '모바일'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP002": 0.3}', '{"SKL003": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

-- 스타트업 인턴
('internship', '딥노이드 AI 의료영상 인턴', '딥노이드', 'AI 기반 의료 영상 분석 모델 개발', '{"min_gpa": 3.6, "skills": ["Python", "PyTorch", "Computer Vision"], "grade": [3, 4]}', '{"salary": "월 300만원", "research_support": true}', '2025-05-01', '2025-05-31', '2025-07-01', '2025-09-30', '서울특별시 금천구', FALSE, 4, 'open', ARRAY['의료AI', 'CV', 'PyTorch'], ARRAY['DEPT001', 'DEPT010'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL006": 0.5, "SKL001": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '마켓컬리 물류 최적화 인턴', '컬리', '신선식품 물류 최적화 알고리즘 개발', '{"min_gpa": 3.4, "skills": ["Python", "OR", "Statistics"], "grade": [3, 4]}', '{"salary": "월 270만원", "meal": true}', '2025-06-15', '2025-07-15', '2025-08-15', '2025-10-31', '경기도 김포시', FALSE, 6, 'open', ARRAY['물류최적화', 'OR', '알고리즘'], ARRAY['DEPT006', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL001": 0.4, "SKL007": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '센드버드 Backend 인턴', '센드버드', '글로벌 채팅 API 플랫폼 개발', '{"min_gpa": 3.5, "skills": ["Python", "Go", "gRPC"], "grade": [3, 4]}', '{"salary": "월 350만원", "meal": true, "english_support": true}', '2025-08-01', '2025-08-31', '2025-10-01', '2025-12-31', '서울특별시 서초구', TRUE, 8, 'open', ARRAY['API', 'Go', '글로벌'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP005": 0.3}', '{"SKL001": 0.4, "SKL014": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '버킷플레이스 (오늘의집) 프론트엔드 인턴', '버킷플레이스', '인테리어 플랫폼 프론트엔드 개발', '{"min_gpa": 3.4, "skills": ["React", "TypeScript", "Next.js"], "grade": [3, 4]}', '{"salary": "월 300만원", "meal": true}', '2025-07-01', '2025-07-31', '2025-09-01', '2025-11-30', '서울특별시 서초구', TRUE, 10, 'open', ARRAY['프론트엔드', 'React', 'TypeScript'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP002": 0.3}', '{"SKL003": 0.6, "SKL001": 0.2}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('internship', '직방 부동산 AI 인턴', '직방', '부동산 시세 예측 AI 모델 개발', '{"min_gpa": 3.5, "skills": ["Python", "ML", "TensorFlow"], "grade": [3, 4]}', '{"salary": "월 280만원", "meal": true}', '2025-06-01', '2025-06-30', '2025-08-01', '2025-10-31', '서울특별시 강남구', TRUE, 5, 'open', ARRAY['PropTech', 'ML', 'TensorFlow'], ARRAY['DEPT001', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL005": 0.5, "SKL001": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- ============================================
-- Additional Contests (10개 추가)
-- ============================================

INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('contest', '네이버 AI 해커톤', '네이버', 'AI 기술을 활용한 창의적 솔루션 개발 대회', '{"skills": ["Python", "ML"], "grade": [2, 3, 4]}', '{"prize": "총 5000만원", "internship_opportunity": true}', '2025-08-01', '2025-09-30', '2025-10-15', '2025-10-17', '경기도 성남시', FALSE, 200, 'open', ARRAY['AI', '해커톤', '네이버'], ARRAY['DEPT001', 'DEPT002', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL005": 0.5, "SKL001": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'K-Digital Platform 공모전', '과학기술정보통신부', '디지털 플랫폼 서비스 아이디어 공모전', '{"grade": [1, 2, 3, 4]}', '{"prize": "총 3000만원", "government_support": true}', '2025-05-01', '2025-07-31', '2025-08-15', '2025-09-30', '전국', TRUE, 500, 'open', ARRAY['디지털플랫폼', '공모전', '정부지원'], ARRAY['DEPT001', 'DEPT002', 'DEPT014'], '{"COMP002": 0.4, "COMP003": 0.4}', '{"SKL013": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '카카오 if 개발자 컨퍼런스 해커톤', '카카오', '카카오 API를 활용한 24시간 해커톤', '{"skills": ["Any Programming Language"], "grade": [2, 3, 4]}', '{"prize": "총 2000만원", "networking": true}', '2025-09-01', '2025-09-30', '2025-10-20', '2025-10-21', '경기도 성남시', FALSE, 150, 'open', ARRAY['해커톤', '카카오', 'API'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL009": 0.4, "SKL011": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '한국데이터산업진흥원 데이터 분석 경진대회', '한국데이터산업진흥원', '공공데이터 활용 분석 대회', '{"skills": ["Python", "R", "SQL"], "grade": [2, 3, 4]}', '{"prize": "총 2500만원", "certificate": true}', '2025-06-01', '2025-08-31', '2025-09-15', '2025-11-15', '온라인', TRUE, 400, 'open', ARRAY['데이터분석', '공공데이터', '경진대회'], ARRAY['DEPT001', 'DEPT013', 'DEPT014'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL007": 0.5, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'Google Solution Challenge', 'Google', 'UN SDGs 해결을 위한 글로벌 해커톤', '{"grade": [1, 2, 3, 4]}', '{"prize": "글로벌 본선 진출", "google_mentoring": true}', '2025-01-15', '2025-03-31', '2025-04-01', '2025-05-31', '글로벌', TRUE, 1000, 'open', ARRAY['Google', 'SDGs', '글로벌'], ARRAY['DEPT001', 'DEPT002', 'DEPT025'], '{"COMP002": 0.4, "COMP003": 0.4, "COMP005": 0.2}', '{"SKL009": 0.4, "SKL014": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'SW 스타트업 챌린지', '정보통신산업진흥원', 'SW 분야 창업 아이디어 경진대회', '{"grade": [3, 4]}', '{"prize": "총 4000만원", "incubating": true}', '2025-04-01', '2025-06-30', '2025-07-15', '2025-09-30', '서울', FALSE, 300, 'open', ARRAY['스타트업', '창업', 'SW'], ARRAY['DEPT001', 'DEPT002', 'DEPT014'], '{"COMP002": 0.4, "COMP003": 0.5}', '{"SKL013": 0.4, "SKL015": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'LG Aimers AI 해커톤', 'LG AI연구원', 'AI 기술 실전 문제 해결 해커톤', '{"skills": ["Python", "ML", "DL"], "grade": [2, 3, 4]}', '{"prize": "총 2000만원", "lg_internship": true}', '2025-07-01', '2025-08-31', '2025-09-15', '2025-10-15', '온라인', TRUE, 500, 'open', ARRAY['AI', 'LG', '해커톤'], ARRAY['DEPT001', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL005": 0.5, "SKL006": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', 'SKT AI Fellowship', 'SK텔레콤', 'AI 연구 펠로우십 프로그램', '{"min_gpa": 3.7, "skills": ["Python", "Research"], "grade": [3, 4]}', '{"prize": "월 200만원 장학금", "research_support": true}', '2025-03-01', '2025-04-30', '2025-06-01', '2025-11-30', '서울', FALSE, 30, 'open', ARRAY['AI', 'Fellowship', '연구'], ARRAY['DEPT001', 'DEPT010', 'DEPT013'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL005": 0.5, "SKL006": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '현대모비스 자율주행 챌린지', '현대모비스', '자율주행 알고리즘 개발 경진대회', '{"skills": ["Python", "C++", "ROS"], "grade": [3, 4]}', '{"prize": "총 3000만원", "internship": true}', '2025-05-15', '2025-07-15', '2025-08-01', '2025-10-31', '경기도 용인시', FALSE, 100, 'open', ARRAY['자율주행', '모빌리티', 'ROS'], ARRAY['DEPT001', 'DEPT003', 'DEPT004'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL001": 0.4, "SKL009": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('contest', '삼성전자 휴먼테크 논문대상', '삼성전자', '대학(원)생 과학기술 논문 공모전', '{"min_gpa": 3.5, "grade": [3, 4]}', '{"prize": "총 1억원", "samsung_internship": true}', '2025-09-01', '2025-11-30', '2025-12-15', '2026-02-28', '전국', TRUE, 1000, 'open', ARRAY['논문', '연구', '삼성'], ARRAY['DEPT001', 'DEPT003', 'DEPT010', 'DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL009": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- ============================================
-- Additional Labs (5개 추가)
-- ============================================

INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('lab', '강화학습 연구실 학부연구생', '인공지능학과', 'Deep RL 및 로봇 제어 연구', '{"min_gpa": 3.7, "skills": ["Python", "PyTorch", "RL"], "grade": [3, 4]}', '{"stipend": "월 35만원", "conference": true}', '2025-02-01', '2025-02-28', '2025-03-01', '2025-12-31', '교내', FALSE, 2, 'open', ARRAY['강화학습', 'RL', '로봇'], ARRAY['DEPT001'], '{"COMP001": 0.6, "COMP002": 0.3}', '{"SKL005": 0.5, "SKL006": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', 'HCI 연구실 학부연구생', '소프트웨어학과', '인간-컴퓨터 상호작용 및 UX 연구', '{"min_gpa": 3.5, "skills": ["Prototyping", "User Study"], "grade": [3, 4]}', '{"stipend": "월 25만원", "paper_coauthor": true}', '2025-02-15', '2025-03-15', '2025-03-01', '2025-12-31', '교내', TRUE, 3, 'open', ARRAY['HCI', 'UX', '사용자연구'], ARRAY['DEPT002', 'DEPT025'], '{"COMP002": 0.5, "COMP003": 0.3}', '{"SKL009": 0.4, "SKL010": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', '빅데이터 분석 연구실 학부연구생', '통계학과', '대규모 데이터 분석 및 시각화 연구', '{"min_gpa": 3.6, "skills": ["Python", "R", "Spark"], "grade": [3, 4]}', '{"stipend": "월 30만원", "conference": true}', '2025-03-01', '2025-03-31', '2025-04-01', '2025-12-31', '교내', TRUE, 3, 'open', ARRAY['빅데이터', 'Spark', '시각화'], ARRAY['DEPT013'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL007": 0.5, "SKL001": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', '네트워크 보안 연구실 학부연구생', '컴퓨터공학과', '네트워크 보안 및 암호학 연구', '{"min_gpa": 3.6, "skills": ["C", "Network", "Security"], "grade": [3, 4]}', '{"stipend": "월 30만원", "conference": true}', '2025-02-01', '2025-02-28', '2025-03-01', '2025-12-31', '교내', FALSE, 2, 'open', ARRAY['보안', '네트워크', '암호학'], ARRAY['DEPT001'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL009": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('lab', '계산화학 연구실 학부연구생', '화학공학과', 'AI 기반 분자 시뮬레이션 연구', '{"min_gpa": 3.7, "skills": ["Python", "Chemistry", "ML"], "grade": [3, 4]}', '{"stipend": "월 25만원", "paper_coauthor": true}', '2025-03-01', '2025-03-31', '2025-04-01', '2025-12-31', '교내', FALSE, 2, 'open', ARRAY['계산화학', 'AI', '시뮬레이션'], ARRAY['DEPT005', 'DEPT001'], '{"COMP001": 0.5, "COMP002": 0.4}', '{"SKL001": 0.4, "SKL005": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- ============================================
-- Additional Projects (5개 추가)
-- ============================================

INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('project', '스마트 캠퍼스 앱 개발 프로젝트', '교내IT센터', '학교 공식 모바일 앱 기능 개발 참여', '{"skills": ["Flutter", "Firebase"], "grade": [2, 3, 4]}', '{"stipend": "프로젝트당 100만원", "certificate": true}', '2025-03-01', '2025-03-31', '2025-04-01', '2025-07-31', '교내', TRUE, 10, 'open', ARRAY['모바일', 'Flutter', '캠퍼스'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.4, "COMP003": 0.3}', '{"SKL003": 0.5}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', 'AI 챗봇 개발 프로젝트', '창업보육센터', 'AI 기반 고객 상담 챗봇 MVP 개발', '{"skills": ["Python", "NLP", "LLM"], "grade": [3, 4]}', '{"stipend": "월 80만원", "mentoring": true}', '2025-04-15', '2025-05-15', '2025-06-01', '2025-08-31', '창업보육센터', TRUE, 6, 'open', ARRAY['챗봇', 'NLP', 'LLM'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.5, "COMP002": 0.3}', '{"SKL001": 0.5, "SKL005": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', '지역사회 디지털 격차 해소 프로젝트', '사회봉사센터', '노인/장애인을 위한 디지털 교육 앱 개발', '{"grade": [2, 3, 4]}', '{"certificate": true, "volunteer_hours": 60}', '2025-03-15', '2025-04-15', '2025-05-01', '2025-08-31', '교내/지역사회', FALSE, 15, 'open', ARRAY['봉사', '디지털교육', '사회공헌'], ARRAY['DEPT001', 'DEPT002', 'DEPT023'], '{"COMP003": 0.5, "COMP004": 0.3}', '{"SKL010": 0.4, "SKL011": 0.4}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', '데이터 시각화 대시보드 프로젝트', '경영대학', '경영 데이터 분석 대시보드 개발', '{"skills": ["Python", "Tableau", "SQL"], "grade": [3, 4]}', '{"stipend": "프로젝트당 80만원", "reference": true}', '2025-05-01', '2025-05-31', '2025-06-15', '2025-09-30', '경영대학', TRUE, 5, 'open', ARRAY['대시보드', 'Tableau', '시각화'], ARRAY['DEPT013', 'DEPT014'], '{"COMP001": 0.4, "COMP002": 0.4}', '{"SKL007": 0.5, "SKL004": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('project', 'ESG 데이터 플랫폼 개발 프로젝트', '지속가능경영센터', 'ESG 지표 수집 및 분석 플랫폼 개발', '{"skills": ["Python", "React", "PostgreSQL"], "grade": [3, 4]}', '{"stipend": "월 100만원", "certificate": true}', '2025-06-01', '2025-06-30', '2025-07-15', '2025-11-30', '교내', TRUE, 8, 'open', ARRAY['ESG', '플랫폼', '지속가능경영'], ARRAY['DEPT001', 'DEPT014'], '{"COMP001": 0.4, "COMP003": 0.4}', '{"SKL001": 0.4, "SKL003": 0.3}', 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- ============================================
-- Additional Scholarships (5개 추가)
-- ============================================

INSERT INTO tb_opportunity (opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, tags, department_cds, competency_contributions, skill_contributions, ins_user_id, ins_dt) VALUES
('scholarship', '네이버 커넥트재단 SW 장학금', '네이버커넥트재단', 'SW 분야 우수 학생 장학금', '{"min_gpa": 3.7, "grade": [2, 3]}', '{"amount": "연 600만원", "mentoring": true}', '2025-02-01', '2025-03-31', '2025-04-01', '2026-03-31', '해당없음', TRUE, 50, 'open', ARRAY['장학금', 'SW', '네이버'], ARRAY['DEPT001', 'DEPT002'], '{"COMP001": 0.3}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', 'LG 유플러스 디지털인재 장학금', 'LG유플러스', '디지털 분야 인재 육성 장학금', '{"min_gpa": 3.5, "grade": [2, 3]}', '{"amount": "연 500만원", "internship_priority": true}', '2025-03-01', '2025-04-30', '2025-05-01', '2026-04-30', '해당없음', TRUE, 30, 'open', ARRAY['장학금', '디지털', 'LG'], ARRAY['DEPT001', 'DEPT002', 'DEPT003'], '{"COMP001": 0.2}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', 'SK하이닉스 반도체 장학금', 'SK하이닉스', '반도체 분야 전공 학생 장학금', '{"min_gpa": 3.6, "grade": [2, 3, 4]}', '{"amount": "연 700만원", "internship": true}', '2025-02-15', '2025-03-15', '2025-04-01', '2026-03-31', '해당없음', TRUE, 40, 'open', ARRAY['장학금', '반도체', 'SK'], ARRAY['DEPT003', 'DEPT004'], '{"COMP001": 0.3}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', '정보통신기획평가원 ICT 장학금', '정보통신기획평가원', 'ICT 분야 우수 학생 지원', '{"min_gpa": 3.5, "grade": [1, 2, 3, 4]}', '{"amount": "연 400만원", "research_support": true}', '2025-01-15', '2025-02-28', '2025-03-01', '2026-02-28', '해당없음', TRUE, 100, 'open', ARRAY['장학금', 'ICT', '정부지원'], ARRAY['DEPT001', 'DEPT002', 'DEPT003'], '{"COMP001": 0.2}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP),

('scholarship', '여성과학기술인회 WE-STEM 장학금', '여성과학기술인회', '여성 이공계 학생 장학금', '{"min_gpa": 3.4, "gender": "F", "grade": [2, 3]}', '{"amount": "연 300만원", "mentoring": true}', '2025-04-01', '2025-05-31', '2025-06-01', '2026-05-31', '해당없음', TRUE, 80, 'open', ARRAY['장학금', '여성', 'STEM'], ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT005', 'DEPT010', 'DEPT013'], '{"COMP001": 0.2, "COMP005": 0.2}', NULL, 'SEED_SCRIPT', CURRENT_TIMESTAMP);

-- ============================================
-- Success message
-- ============================================
DO $$
DECLARE
    total_count INT;
BEGIN
    SELECT COUNT(*) INTO total_count FROM tb_opportunity;
    RAISE NOTICE '=== Additional Opportunities Seed Data Created ===';
    RAISE NOTICE 'Total tb_opportunity records: % (target: 50+)', total_count;
END $$;
