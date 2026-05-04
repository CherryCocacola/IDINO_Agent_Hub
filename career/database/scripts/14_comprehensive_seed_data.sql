-- ============================================
-- 종합 시드 데이터 생성 스크립트
-- ============================================
-- 작성일: 2026-01-26
-- 목적: tb_opportunity, tb_skill, tb_student_skill, tb_portfolio 데이터 추가
-- ============================================

SET search_path TO idino_career, public;

-- ============================================
-- 1. tb_skill 데이터 추가 (현재 15개 → 60개 이상)
-- ============================================
INSERT INTO tb_skill (skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt)
SELECT * FROM (VALUES
-- Technical Skills - Programming
('SK16', 'TypeScript', 'TypeScript', ARRAY['TS', '타입스크립트'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK17', 'C++', 'C++', ARRAY['C Plus Plus', 'Cpp', '씨쁠쁠'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK18', 'Go', 'Go', ARRAY['Golang', '고랭'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK19', 'Rust', 'Rust', ARRAY['러스트'], 'technical', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK20', 'Kotlin', 'Kotlin', ARRAY['코틀린'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK21', 'Swift', 'Swift', ARRAY['스위프트'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK22', 'C#', 'C Sharp', ARRAY['CSharp', '씨샵'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK23', 'PHP', 'PHP', ARRAY['피에이치피'], 'technical', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK24', 'R', 'R', ARRAY['R언어'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK25', 'Scala', 'Scala', ARRAY['스칼라'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Technical Skills - Frameworks & Libraries
('SK26', 'Node.js', 'Node.js', ARRAY['노드', 'NodeJS'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK27', 'Vue.js', 'Vue.js', ARRAY['뷰', 'Vue', 'VueJS'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK28', 'Angular', 'Angular', ARRAY['앵귤러'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK29', 'Django', 'Django', ARRAY['장고'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK30', 'Spring', 'Spring', ARRAY['스프링', 'Spring Boot', '스프링부트'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK31', 'FastAPI', 'FastAPI', ARRAY['패스트API'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK32', 'Flask', 'Flask', ARRAY['플라스크'], 'technical', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK33', 'TensorFlow', 'TensorFlow', ARRAY['텐서플로우', 'TF'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK34', 'PyTorch', 'PyTorch', ARRAY['파이토치'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK35', 'Keras', 'Keras', ARRAY['케라스'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Technical Skills - DevOps & Cloud
('SK36', 'Docker', 'Docker', ARRAY['도커', '컨테이너'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK37', 'Kubernetes', 'Kubernetes', ARRAY['쿠버네티스', 'K8s'], 'technical', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK38', 'AWS', 'Amazon Web Services', ARRAY['아마존 웹 서비스', 'Amazon'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK39', 'Azure', 'Microsoft Azure', ARRAY['애저', 'MS Azure'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK40', 'GCP', 'Google Cloud Platform', ARRAY['구글 클라우드'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK41', 'CI/CD', 'CI/CD', ARRAY['지속적 통합', '지속적 배포', 'Jenkins', 'GitHub Actions'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK42', 'Git', 'Git', ARRAY['깃', 'GitHub', 'GitLab', '버전관리'], 'technical', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK43', 'Linux', 'Linux', ARRAY['리눅스', 'Ubuntu', 'CentOS'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Technical Skills - Database
('SK44', 'PostgreSQL', 'PostgreSQL', ARRAY['포스트그레스', 'Postgres'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK45', 'MySQL', 'MySQL', ARRAY['마이에스큐엘', 'MariaDB'], 'technical', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK46', 'MongoDB', 'MongoDB', ARRAY['몽고DB', 'NoSQL'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK47', 'Redis', 'Redis', ARRAY['레디스', '캐시'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK48', 'Elasticsearch', 'Elasticsearch', ARRAY['엘라스틱서치', 'ES'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Technical Skills - Data Science & AI
('SK49', '딥러닝', 'Deep Learning', ARRAY['DL', 'Neural Network', '신경망'], 'technical', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK50', '자연어처리', 'Natural Language Processing', ARRAY['NLP', 'LLM'], 'technical', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK51', '컴퓨터비전', 'Computer Vision', ARRAY['CV', '영상처리'], 'technical', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK52', '빅데이터', 'Big Data', ARRAY['Hadoop', 'Spark', '대용량 데이터'], 'technical', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK53', '데이터 시각화', 'Data Visualization', ARRAY['Tableau', 'PowerBI', '시각화'], 'technical', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Design & Creative
('SK54', 'Figma', 'Figma', ARRAY['피그마', 'UI/UX'], 'design', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK55', 'Adobe Photoshop', 'Photoshop', ARRAY['포토샵', 'PS'], 'design', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK56', 'Adobe Illustrator', 'Illustrator', ARRAY['일러스트레이터', 'AI'], 'design', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK57', 'Adobe Premiere', 'Premiere Pro', ARRAY['프리미어', '영상편집'], 'design', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK58', 'After Effects', 'After Effects', ARRAY['에펙', '모션그래픽'], 'design', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK59', 'UI/UX 디자인', 'UI/UX Design', ARRAY['사용자 경험', '인터페이스 디자인'], 'design', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK60', '3D 모델링', '3D Modeling', ARRAY['3D Max', 'Blender', 'Maya'], 'design', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Soft Skills
('SK61', '문제 해결', 'Problem Solving', ARRAY['문제해결력', '분석적 사고'], 'soft', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK62', '팀워크', 'Teamwork', ARRAY['협업', '협동', '팀 협업'], 'soft', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK63', '프레젠테이션', 'Presentation', ARRAY['발표', 'PT', '프리젠테이션'], 'soft', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK64', '프로젝트 관리', 'Project Management', ARRAY['PM', 'PMP', '프로젝트매니지먼트'], 'soft', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK65', '시간 관리', 'Time Management', ARRAY['일정관리', '타임매니지먼트'], 'soft', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK66', '창의적 사고', 'Creative Thinking', ARRAY['창의력', '아이디어'], 'soft', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK67', '비판적 사고', 'Critical Thinking', ARRAY['비판적 분석', '논리적 사고'], 'soft', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK68', '글쓰기', 'Writing', ARRAY['문서작성', '기술 문서', '보고서 작성'], 'soft', 2, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Domain Specific
('SK69', '반도체 공정', 'Semiconductor Process', ARRAY['반도체', 'FAB', '웨이퍼'], 'domain', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK70', '임베디드 시스템', 'Embedded Systems', ARRAY['임베디드', 'MCU', 'ARM'], 'domain', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK71', '네트워크', 'Networking', ARRAY['TCP/IP', '네트워크 관리'], 'domain', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK72', '보안', 'Security', ARRAY['사이버보안', '정보보안', '해킹'], 'domain', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK73', '로봇공학', 'Robotics', ARRAY['로봇', 'ROS'], 'domain', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK74', '의료 데이터', 'Medical Data', ARRAY['헬스케어 데이터', '의료 AI'], 'domain', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK75', '금융공학', 'Financial Engineering', ARRAY['퀀트', '금융 데이터'], 'domain', 5, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),

-- Language Skills
('SK76', '영어', 'English', ARRAY['TOEIC', 'TOEFL', 'IELTS'], 'language', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK77', '일본어', 'Japanese', ARRAY['JLPT', 'JPT'], 'language', 3, 'Y', 'SEED_V3', CURRENT_TIMESTAMP),
('SK78', '중국어', 'Chinese', ARRAY['HSK', '만다린'], 'language', 4, 'Y', 'SEED_V3', CURRENT_TIMESTAMP)
) AS v(skill_cd, skill_nm, skill_nm_en, synonyms, category, difficulty, use_fg, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_skill s WHERE s.skill_cd = v.skill_cd);

-- ============================================
-- 2. tb_opportunity 데이터 추가 (50건 이상)
-- ============================================
-- 기존 데이터 확인 후 새 데이터만 추가
INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt)
SELECT * FROM (VALUES
-- ========== 인턴십 (15건) ==========
(uuid_generate_v4(), 'internship', '2026년 SK하이닉스 대학생 인턴', 'SK하이닉스', 'SK하이닉스 반도체 분야 인턴십. 메모리 반도체 개발, 공정, 품질 직무 체험 기회 제공.',
 '{"grade": [3, 4], "major": ["전자공학", "재료공학", "화학공학", "물리학"], "min_gpa": 3.0, "skills": ["반도체", "전자공학"]}',
 '{"salary": "월 220만원", "meal": true, "housing": true, "certificate": true}',
 '2026-03-01'::DATE, '2026-04-30'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '경기도 이천시', false, 200, 'open',
 'https://www.skhynix.com/kor/recruit', ARRAY['SK하이닉스', '반도체', '인턴', '메모리'], ARRAY['1083', '444', '446'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 현대자동차 글로벌 인턴십', '현대자동차', '현대자동차 글로벌 인턴십 프로그램. R&D, 생산, 마케팅, 기획 등 다양한 직무 체험.',
 '{"grade": [3, 4], "min_gpa": 3.0, "language": "토익 700점 이상", "skills": ["자동차", "기계공학"]}',
 '{"salary": "월 200만원", "meal": true, "certificate": true}',
 '2026-04-01'::DATE, '2026-05-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '서울시 서초구', false, 150, 'open',
 'https://talent.hyundai.com', ARRAY['현대자동차', '인턴', '글로벌', '자동차'], ARRAY['1034', '442', '639'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 네이버 테크 인턴십', '네이버', '네이버 개발 인턴십. 검색, AI, 클라우드, 플랫폼 개발 직무 체험. 코딩테스트 및 기술면접 진행.',
 '{"grade": [3, 4], "skills": ["프로그래밍", "알고리즘", "자료구조"], "min_gpa": 3.2}',
 '{"salary": "월 280만원", "meal": true, "remote": true, "certificate": true}',
 '2026-03-01'::DATE, '2026-04-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '경기도 성남시 분당구', true, 100, 'open',
 'https://recruit.navercorp.com', ARRAY['네이버', '인턴', 'IT', '개발'], ARRAY['1160', '2059', '684'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 카카오 채용연계형 인턴십', '카카오', '카카오 채용연계형 인턴십. 서비스 개발, AI 연구, 데이터 분석 직무. 인턴 수료 후 정규직 전환 기회.',
 '{"grade": [3, 4], "skills": ["Python", "Java", "알고리즘"], "min_gpa": 3.0}',
 '{"salary": "월 260만원", "meal": true, "certificate": true}',
 '2026-05-01'::DATE, '2026-06-15'::DATE, '2026-07-01'::DATE, '2026-12-31'::DATE, '경기도 성남시 분당구', true, 80, 'open',
 'https://careers.kakao.com', ARRAY['카카오', '인턴', 'IT', 'AI'], ARRAY['1160', '2059', '684'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 LG에너지솔루션 배터리 인턴', 'LG에너지솔루션', 'LG에너지솔루션 배터리 연구개발 인턴십. 2차전지 개발, 생산, 품질 직무 체험.',
 '{"grade": [3, 4], "major": ["화학공학", "재료공학", "전자공학"], "min_gpa": 3.0}',
 '{"salary": "월 210만원", "meal": true, "housing": true}',
 '2026-03-15'::DATE, '2026-04-30'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '충청북도 청주시', false, 120, 'open',
 'https://careers.lgensol.com', ARRAY['LG에너지솔루션', '배터리', '2차전지', '인턴'], ARRAY['446', '1083', '1086'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 포스코 그룹 인턴십', '포스코', '포스코그룹 종합 인턴십. 철강, 건설, ICT, 에너지 분야 다양한 직무 체험.',
 '{"grade": [3, 4], "min_gpa": 3.0, "language": "토익 700점 이상"}',
 '{"salary": "월 200만원", "meal": true, "housing": true}',
 '2026-04-01'::DATE, '2026-05-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '경상북도 포항시', false, 100, 'open',
 'https://www.posco.co.kr/homepage/docs/kor6/jsp/hr/', ARRAY['포스코', '철강', '인턴'], ARRAY['1034', '446', '1089'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 쿠팡 테크 인턴', '쿠팡', '쿠팡 테크 인턴십. 이커머스 플랫폼 개발, 물류 시스템 개발, 데이터 분석 직무.',
 '{"grade": [3, 4], "skills": ["Java", "Python", "알고리즘"], "min_gpa": 3.0}',
 '{"salary": "월 300만원", "meal": true, "remote": true}',
 '2026-03-01'::DATE, '2026-04-30'::DATE, '2026-06-01'::DATE, '2026-08-31'::DATE, '서울시 송파구', true, 50, 'open',
 'https://www.coupang.jobs', ARRAY['쿠팡', 'IT', '이커머스', '인턴'], ARRAY['1160', '2059', '684'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 롯데그룹 L-TAB 인턴십', '롯데그룹', '롯데그룹 채용연계형 인턴십 L-TAB. 유통, 제조, 호텔 등 다양한 계열사 직무 체험.',
 '{"grade": [3, 4], "min_gpa": 2.8}',
 '{"salary": "월 180만원", "meal": true, "certificate": true}',
 '2026-05-01'::DATE, '2026-06-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '서울시 송파구', false, 200, 'open',
 'https://job.lotte.co.kr', ARRAY['롯데', '유통', '인턴'], ARRAY['1440', '484', '497'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 토스 개발 인턴십', '토스', '토스 핀테크 개발 인턴십. 금융 서비스 개발, 데이터 분석, 보안 직무.',
 '{"grade": [3, 4], "skills": ["Kotlin", "Java", "React"], "min_gpa": 3.2}',
 '{"salary": "월 350만원", "meal": true, "remote": true}',
 '2026-04-01'::DATE, '2026-05-15'::DATE, '2026-06-01'::DATE, '2026-08-31'::DATE, '서울시 강남구', true, 30, 'open',
 'https://toss.im/career', ARRAY['토스', '핀테크', '개발', '인턴'], ARRAY['1160', '2059', '684'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 기아 AutoLand 산학인턴', '기아', '기아자동차 광명공장 산학인턴. 자동차 제조 라인 실습. 공학계열 학생 대상.',
 '{"grade": [2, 3, 4], "major": ["기계공학", "산업공학", "전자공학"], "min_gpa": 2.5}',
 '{"salary": "월 200만원", "meal": true}',
 '2026-06-01'::DATE, '2026-06-30'::DATE, '2026-12-22'::DATE, '2027-06-30'::DATE, '경기도 광명시', false, 50, 'upcoming',
 'https://career.kia.com', ARRAY['기아', '자동차', '산학인턴'], ARRAY['1034', '442', '658'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 네이버랩스 AI 연구 인턴', '네이버랩스', '네이버랩스 AI/ML 연구 인턴십. 자율주행, 로보틱스, 컴퓨터비전 연구 참여.',
 '{"grade": [3, 4], "major": ["컴퓨터공학", "AI", "데이터사이언스"], "skills": ["Python", "PyTorch"], "min_gpa": 3.5}',
 '{"salary": "월 300만원", "meal": true, "remote": true}',
 '2026-01-15'::DATE, '2026-02-28'::DATE, '2026-03-01'::DATE, '2026-06-30'::DATE, '경기도 성남시 분당구', true, 20, 'open',
 'https://recruit.naverlabs.com', ARRAY['네이버랩스', 'AI', '연구', '인턴'], ARRAY['1160', '2059', '3554'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 라인플러스 개발 인턴', '라인플러스', '라인플러스 개발 인턴십. 메신저, 핀테크, 블록체인 서비스 개발.',
 '{"grade": [3, 4], "skills": ["Java", "Kotlin", "Spring"], "min_gpa": 3.0}',
 '{"salary": "월 280만원", "meal": true}',
 '2026-05-01'::DATE, '2026-06-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '경기도 성남시 분당구', true, 40, 'upcoming',
 'https://careers.linecorp.com', ARRAY['라인', '메신저', '개발', '인턴'], ARRAY['1160', '2059', '684'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 삼성바이오로직스 인턴', '삼성바이오로직스', '삼성바이오로직스 바이오 인턴십. 바이오의약품 개발, 생산, 품질 관리 직무.',
 '{"grade": [3, 4], "major": ["생명공학", "화학공학", "약학"], "min_gpa": 3.0}',
 '{"salary": "월 210만원", "meal": true, "housing": true}',
 '2026-03-01'::DATE, '2026-04-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '인천광역시 연수구', false, 80, 'open',
 'https://www.samsungbiologics.com', ARRAY['삼성바이오', '바이오', '제약', '인턴'], ARRAY['1214', '700', '1995'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 현대모비스 SW 인턴', '현대모비스', '현대모비스 자율주행 SW 개발 인턴십. ADAS, 자율주행 시스템 개발.',
 '{"grade": [3, 4], "major": ["컴퓨터공학", "전자공학"], "skills": ["C++", "Python"], "min_gpa": 3.0}',
 '{"salary": "월 220만원", "meal": true}',
 '2026-04-01'::DATE, '2026-05-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '경기도 용인시', false, 60, 'open',
 'https://www.mobis.co.kr', ARRAY['현대모비스', '자율주행', 'SW', '인턴'], ARRAY['1160', '1083', '2059'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'internship', '2026년 한화에어로스페이스 인턴', '한화에어로스페이스', '한화에어로스페이스 항공우주 인턴십. 항공기 엔진, 우주 시스템 개발.',
 '{"grade": [3, 4], "major": ["기계공학", "항공우주공학"], "min_gpa": 3.2}',
 '{"salary": "월 200만원", "meal": true, "housing": true}',
 '2026-05-01'::DATE, '2026-06-15'::DATE, '2026-07-01'::DATE, '2026-08-31'::DATE, '경상남도 창원시', false, 40, 'upcoming',
 'https://www.hanwhaaerospace.co.kr', ARRAY['한화', '항공우주', '인턴'], ARRAY['1034', '442'], 'SEED_V3', CURRENT_TIMESTAMP),

-- ========== 공모전 (15건) ==========
(uuid_generate_v4(), 'contest', '2026 삼성 AI 챌린지', '삼성전자', '삼성전자 주최 AI/ML 알고리즘 경진대회. 자연어처리, 컴퓨터비전 문제 해결.',
 '{"grade": [1, 2, 3, 4], "skills": ["Python", "AI", "ML"]}',
 '{"prize": "총 상금 1억원", "internship": true}',
 '2026-04-01'::DATE, '2026-05-31'::DATE, '2026-06-01'::DATE, '2026-08-31'::DATE, '온라인', true, 500, 'upcoming',
 'https://www.samsungcareers.com', ARRAY['삼성', 'AI', '공모전', '챌린지'], ARRAY['1160', '2059', '3554'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 프랭크버거 대학생 마케팅 공모전', '프랭크버거', '프랭크버거 마케팅 공모전. 광고/마케팅, 레시피 기획 아이디어 공모.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 500만원"}',
 '2026-01-15'::DATE, '2026-02-15'::DATE, NULL, NULL, '온라인', true, 300, 'open',
 'https://www.wevity.com', ARRAY['마케팅', '공모전', '기획'], ARRAY['1440', '484', '1233'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 ICT콤플렉스 피우다프로젝트 SW개발 공모전', '과학기술정보통신부', 'SW 개발 공모전. 웹/모바일, 게임, IoT 분야 개발 프로젝트 공모.',
 '{"grade": [1, 2, 3, 4], "skills": ["프로그래밍"]}',
 '{"prize": "총 상금 3000만원", "certificate": true}',
 '2026-03-01'::DATE, '2026-05-31'::DATE, '2026-06-01'::DATE, '2026-10-31'::DATE, '온라인/오프라인', true, 200, 'upcoming',
 'https://gcontest.co.kr', ARRAY['SW', '개발', '공모전', 'ICT'], ARRAY['1160', '2059', '3556'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 K리그 AI 경진대회', '한국프로축구연맹', 'K리그 데이터 기반 AI 경진대회. 경기 분석, 선수 성과 예측 모델 개발.',
 '{"grade": [1, 2, 3, 4], "skills": ["Python", "데이터분석", "ML"]}',
 '{"prize": "총 상금 2000만원"}',
 '2026-02-01'::DATE, '2026-03-15'::DATE, '2026-03-20'::DATE, '2026-05-31'::DATE, '온라인', true, 150, 'open',
 'https://www.dacon.io', ARRAY['AI', '스포츠', '데이터', '공모전'], ARRAY['1101', '384', '2334'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 정읍시 동학농민혁명 굿즈 디자인 공모전', '정읍시', '동학농민혁명 기념 굿즈 디자인 공모전. 캐릭터, 상품 디자인.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 800만원"}',
 '2026-02-01'::DATE, '2026-03-15'::DATE, NULL, NULL, '온라인', true, 100, 'upcoming',
 'https://www.contestkorea.com', ARRAY['디자인', '캐릭터', '공모전'], ARRAY['1127', '711', '2532'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 LG 이노베이션 페스티벌', 'LG그룹', 'LG그룹 대학생 아이디어 공모전. 미래 기술, 지속가능성 분야 혁신 아이디어.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 1억원", "internship": true}',
 '2026-03-01'::DATE, '2026-05-15'::DATE, '2026-06-01'::DATE, '2026-08-31'::DATE, '온라인/오프라인', true, 300, 'upcoming',
 'https://www.lgcareers.com', ARRAY['LG', '이노베이션', '아이디어', '공모전'], ARRAY['2006', '1160', '1086'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 보훈 콘텐츠 공모전', '자생의료재단', '보훈 주제 디지털 콘텐츠 공모전. 영상, 디자인, 웹툰 부문.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 600만원"}',
 '2026-01-15'::DATE, '2026-02-28'::DATE, NULL, NULL, '온라인', true, 200, 'open',
 'https://www.contestkorea.com', ARRAY['콘텐츠', '디자인', '영상', '공모전'], ARRAY['1127', '711', '3487'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 GH 청춘 빌드업 창업 공모전', 'GH', '대학생 창업 아이디어 공모전. 스타트업 창업 지원.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 5000만원", "mentoring": true, "office": true}',
 '2026-03-01'::DATE, '2026-04-30'::DATE, '2026-05-15'::DATE, '2026-12-31'::DATE, '온라인/오프라인', true, 100, 'upcoming',
 'https://www.wevity.com', ARRAY['창업', '스타트업', '공모전'], ARRAY['1440', '484'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 현대자동차 아이디어 페스티벌', '현대자동차', '현대자동차 모빌리티 아이디어 공모전. 미래 모빌리티, 친환경 기술.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 1억원", "internship": true}',
 '2026-04-01'::DATE, '2026-06-30'::DATE, '2026-07-15'::DATE, '2026-11-30'::DATE, '온라인/오프라인', true, 300, 'upcoming',
 'https://talent.hyundai.com', ARRAY['현대', '모빌리티', '아이디어', '공모전'], ARRAY['1034', '442', '3551'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 국민은행 금융 아이디어 공모전', 'KB국민은행', '금융 서비스 혁신 아이디어 공모전. 핀테크, 디지털 금융 분야.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 3000만원"}',
 '2026-05-01'::DATE, '2026-07-15'::DATE, NULL, NULL, '온라인', true, 200, 'upcoming',
 'https://www.kbstar.com', ARRAY['금융', '핀테크', '아이디어', '공모전'], ARRAY['488', '1012', '1440'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 ADD 숏폼 공모전', '쥬비스다이어트', '숏폼 영상 콘텐츠 공모전. 건강, 다이어트 주제.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 500만원"}',
 '2026-01-15'::DATE, '2026-02-28'::DATE, NULL, NULL, '온라인', true, 300, 'open',
 'https://www.wevity.com', ARRAY['숏폼', '영상', '콘텐츠', '공모전'], ARRAY['1233', '3137', '3487'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 네이버 D2SF 챌린지', '네이버', '네이버 스타트업 지원 프로그램. AI, 클라우드, 핀테크 스타트업 공모.',
 '{"grade": [3, 4]}',
 '{"prize": "투자 최대 3억원", "mentoring": true, "office": true}',
 '2026-03-01'::DATE, '2026-04-30'::DATE, '2026-05-15'::DATE, '2027-05-14'::DATE, '경기도 성남시', false, 30, 'upcoming',
 'https://d2sf.naver.com', ARRAY['네이버', '스타트업', '투자', '챌린지'], ARRAY['1160', '2059'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 카카오 브레인 AI 챌린지', '카카오브레인', 'AI 연구 챌린지. NLP, 컴퓨터비전, 생성형 AI 문제 해결.',
 '{"grade": [2, 3, 4], "skills": ["Python", "PyTorch", "TensorFlow"]}',
 '{"prize": "총 상금 5000만원", "internship": true}',
 '2026-04-01'::DATE, '2026-06-15'::DATE, '2026-07-01'::DATE, '2026-09-30'::DATE, '온라인', true, 200, 'upcoming',
 'https://www.kakaobrain.com', ARRAY['카카오', 'AI', '딥러닝', '챌린지'], ARRAY['1160', '2059', '3554'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 한국전력 에너지 아이디어 공모전', '한국전력', '에너지 혁신 아이디어 공모전. 신재생에너지, 스마트그리드 분야.',
 '{"grade": [1, 2, 3, 4]}',
 '{"prize": "총 상금 2000만원"}',
 '2026-05-01'::DATE, '2026-07-31'::DATE, NULL, NULL, '온라인', true, 150, 'upcoming',
 'https://www.kepco.co.kr', ARRAY['한전', '에너지', '신재생', '공모전'], ARRAY['1083', '2605', '1293'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'contest', '2026 삼성생명 금융캠퍼스 서포터즈', '삼성생명', '삼성생명 금융 서포터즈 5기. 금융 마케팅, 콘텐츠 제작 활동.',
 '{"grade": [2, 3, 4]}',
 '{"prize": "활동비 100만원", "certificate": true}',
 '2026-01-20'::DATE, '2026-02-28'::DATE, '2026-03-15'::DATE, '2026-12-31'::DATE, '서울', false, 50, 'open',
 'https://www.samsunglife.com', ARRAY['삼성생명', '금융', '서포터즈', '마케팅'], ARRAY['1440', '488', '1233'], 'SEED_V3', CURRENT_TIMESTAMP),

-- ========== 자격증 (12건) ==========
(uuid_generate_v4(), 'certification', '2026년 정보처리기사 자격시험', '한국산업인력공단', '국가기술자격 정보처리기사. IT 분야 대표 자격증. 연 3회 시행.',
 '{"education": "관련학과 졸업예정자 또는 실무경력 2년"}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-01-15'::DATE, '2026-02-15'::DATE, '2026-03-07'::DATE, '2026-03-07'::DATE, '전국 시험장', false, 10000, 'open',
 'https://www.q-net.or.kr', ARRAY['정보처리기사', '자격증', 'IT', '국가자격'], ARRAY['1160', '2059', '684'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'AWS Solutions Architect Associate', 'Amazon Web Services', 'AWS 공인 솔루션스 아키텍트 자격증. 클라우드 아키텍처 설계 능력 인증.',
 '{"skills": ["클라우드", "AWS"]}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-01-01'::DATE, '2026-12-31'::DATE, NULL, NULL, '온라인 시험', true, 1000, 'open',
 'https://aws.amazon.com/certification', ARRAY['AWS', '클라우드', '자격증'], ARRAY['1160', '2059'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', '2026년 빅데이터분석기사 자격시험', '한국데이터산업진흥원', '빅데이터 분석 국가기술자격. 데이터 분석 전문가 인증.',
 '{"education": "관련학과 졸업예정자"}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-02-01'::DATE, '2026-03-15'::DATE, '2026-04-19'::DATE, '2026-04-19'::DATE, '전국 시험장', false, 5000, 'open',
 'https://www.dataq.or.kr', ARRAY['빅데이터', '분석기사', '자격증', '데이터'], ARRAY['1101', '384', '2334'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'SQLD SQL 개발자 자격시험', '한국데이터산업진흥원', 'SQL 개발자 자격증. 데이터베이스 활용 능력 인증.',
 '{"skills": ["SQL", "데이터베이스"]}',
 '{"certificate": true}',
 '2026-02-01'::DATE, '2026-03-10'::DATE, '2026-03-28'::DATE, '2026-03-28'::DATE, '전국 시험장', false, 8000, 'open',
 'https://www.dataq.or.kr', ARRAY['SQLD', 'SQL', '자격증', '데이터베이스'], ARRAY['1160', '2059', '1101'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'Google Cloud Professional Data Engineer', 'Google Cloud', '구글 클라우드 데이터 엔지니어 전문 자격증.',
 '{"skills": ["GCP", "데이터 엔지니어링", "BigQuery"]}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-01-01'::DATE, '2026-12-31'::DATE, NULL, NULL, '온라인 시험', true, 500, 'open',
 'https://cloud.google.com/certification', ARRAY['GCP', '데이터', '클라우드', '자격증'], ARRAY['1160', '1101'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'CFA Level 1 자격시험', 'CFA Institute', '국제 공인 재무분석사 자격증 Level 1.',
 '{"education": "학사 졸업예정자"}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-01-15'::DATE, '2026-02-15'::DATE, '2026-05-20'::DATE, '2026-05-20'::DATE, '서울 시험장', false, 1000, 'open',
 'https://www.cfainstitute.org', ARRAY['CFA', '금융', '재무분석사', '자격증'], ARRAY['488', '1012', '1440'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'TOEIC Speaking 시험', 'ETS', '토익 스피킹 시험. 비즈니스 영어 말하기 능력 평가.',
 '{}',
 '{"certificate": true}',
 '2026-01-01'::DATE, '2026-12-31'::DATE, NULL, NULL, '전국 시험장', false, 50000, 'open',
 'https://www.toeicswt.co.kr', ARRAY['토익스피킹', '영어', '자격증'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'PMP 프로젝트관리전문가 자격증', 'PMI', 'Project Management Professional 국제 자격증.',
 '{"experience": "프로젝트 관리 경험 3년 이상"}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-01-01'::DATE, '2026-12-31'::DATE, NULL, NULL, '온라인/오프라인', true, 500, 'open',
 'https://www.pmi.org', ARRAY['PMP', '프로젝트관리', '자격증'], ARRAY['1440', '658', '1196'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'Microsoft Azure Fundamentals AZ-900', 'Microsoft', 'Azure 기초 자격증. 클라우드 기본 개념 및 Azure 서비스 이해.',
 '{}',
 '{"certificate": true}',
 '2026-01-01'::DATE, '2026-12-31'::DATE, NULL, NULL, '온라인 시험', true, 2000, 'open',
 'https://learn.microsoft.com', ARRAY['Azure', '클라우드', '마이크로소프트', '자격증'], ARRAY['1160', '2059'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', '한국사능력검정시험', '국사편찬위원회', '한국사 능력 인증 시험. 공무원 시험 가산점 적용.',
 '{}',
 '{"certificate": true, "employment_bonus": true}',
 '2026-03-01'::DATE, '2026-04-15'::DATE, '2026-05-10'::DATE, '2026-05-10'::DATE, '전국 시험장', false, 30000, 'upcoming',
 'https://www.historyexam.go.kr', ARRAY['한국사', '역사', '자격증'], ARRAY['2006', '460', '547'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'JLPT N1 일본어능력시험', '일본국제교류기금', '일본어 능력 시험 최고 등급 N1.',
 '{}',
 '{"certificate": true}',
 '2026-04-01'::DATE, '2026-05-15'::DATE, '2026-07-05'::DATE, '2026-07-05'::DATE, '전국 시험장', false, 5000, 'upcoming',
 'https://www.jlpt.or.kr', ARRAY['JLPT', '일본어', '자격증'], ARRAY['458', '749', '2287'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'certification', 'HSK 6급 중국어능력시험', '한반', '중국어 능력 시험 최고 등급.',
 '{}',
 '{"certificate": true}',
 '2026-03-01'::DATE, '2026-04-30'::DATE, '2026-06-14'::DATE, '2026-06-14'::DATE, '전국 시험장', false, 3000, 'upcoming',
 'https://www.hsk.or.kr', ARRAY['HSK', '중국어', '자격증'], ARRAY['456', '748', '2289'], 'SEED_V3', CURRENT_TIMESTAMP),

-- ========== 봉사활동 (8건) ==========
(uuid_generate_v4(), 'volunteer', 'KOICA 청년봉사단 (가나/에콰도르)', 'KOICA', '중기 해외봉사단. 개발도상국에서 6개월~1년 봉사 활동. 교육, 보건, IT 분야.',
 '{"age": [18, 29]}',
 '{"living_expense": true, "flight": true, "insurance": true, "certificate": true}',
 '2026-02-01'::DATE, '2026-04-30'::DATE, '2026-09-01'::DATE, '2027-08-31'::DATE, '가나/에콰도르', false, 60, 'upcoming',
 'https://www.koica.go.kr', ARRAY['KOICA', '해외봉사', '글로벌', '봉사'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', 'LS그룹 대학생 해외봉사단 26기', 'LS그룹', 'LS그룹 해외봉사단. 베트남, 인도네시아 교육봉사. 비용 전액 지원.',
 '{"grade": [2, 3, 4]}',
 '{"travel_expense": true, "certificate": true}',
 '2026-03-01'::DATE, '2026-05-15'::DATE, '2026-07-15'::DATE, '2026-07-30'::DATE, '베트남/인도네시아', false, 30, 'upcoming',
 'https://linkareer.com', ARRAY['LS', '해외봉사', '교육봉사'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', 'KT&G 상상위더스 동계 해외봉사단', 'KT&G복지재단', 'KT&G 대학생 해외봉사단. 동남아시아 교육봉사 및 문화교류.',
 '{"grade": [1, 2, 3, 4]}',
 '{"travel_expense": true, "certificate": true}',
 '2026-10-01'::DATE, '2026-11-15'::DATE, '2027-01-10'::DATE, '2027-01-25'::DATE, '베트남/캄보디아', false, 50, 'upcoming',
 'https://www.ktngwelfare.org', ARRAY['KT&G', '해외봉사', '동계봉사'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', '서울시 청년봉사단', '서울특별시', '서울시 청년 봉사 프로그램. 지역사회 봉사활동.',
 '{"age": [19, 34]}',
 '{"activity_fee": true, "certificate": true}',
 '2026-01-15'::DATE, '2026-02-28'::DATE, '2026-03-15'::DATE, '2026-12-31'::DATE, '서울시', false, 200, 'open',
 'https://youth.seoul.go.kr', ARRAY['서울시', '청년봉사', '지역봉사'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', '유엔 자원봉사단 대학생', 'UNV', '유엔 자원봉사단 대학생 파견. 국제기구 현장 봉사활동.',
 '{"age": [18, 29], "language": "영어 중급 이상"}',
 '{"living_expense": true, "flight": true, "certificate": true}',
 '2026-03-01'::DATE, '2026-05-31'::DATE, '2026-09-01'::DATE, '2027-02-28'::DATE, '해외', false, 30, 'upcoming',
 'https://www.mofa.go.kr/youth', ARRAY['UNV', '유엔', '국제봉사', '해외봉사'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', '월드비전 글로벌 인턴', '월드비전', '월드비전 글로벌 인턴십. 개발협력, 인도주의 분야 현장 활동.',
 '{"grade": [3, 4], "language": "영어 중급 이상"}',
 '{"living_expense": true, "certificate": true}',
 '2026-04-01'::DATE, '2026-06-15'::DATE, '2026-08-01'::DATE, '2027-01-31'::DATE, '아시아/아프리카', false, 20, 'upcoming',
 'https://www.worldvision.or.kr', ARRAY['월드비전', '글로벌인턴', '국제봉사'], ARRAY['2006', '1137', '523'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', '코피온 단기 해외봉사단', '코피온', '코피온 하계 단기 해외봉사단. 2주간 집중 봉사활동.',
 '{"grade": [1, 2, 3, 4]}',
 '{"partial_support": true, "certificate": true}',
 '2026-05-01'::DATE, '2026-06-30'::DATE, '2026-07-20'::DATE, '2026-08-05'::DATE, '동남아시아', false, 100, 'upcoming',
 'https://copion.or.kr', ARRAY['코피온', '단기봉사', '해외봉사'], ARRAY['2006'], 'SEED_V3', CURRENT_TIMESTAMP),

(uuid_generate_v4(), 'volunteer', '대한적십자사 RCY 활동', '대한적십자사', '청소년적십자 RCY 대학생 활동. 응급처치, 재난구호 교육 및 봉사.',
 '{"grade": [1, 2, 3, 4]}',
 '{"certificate": true, "training": true}',
 '2026-01-01'::DATE, '2026-12-31'::DATE, '2026-03-01'::DATE, '2026-12-31'::DATE, '전국', false, 500, 'open',
 'https://www.redcross.or.kr', ARRAY['적십자', 'RCY', '응급처치', '봉사'], ARRAY['2006', '1144', '356'], 'SEED_V3', CURRENT_TIMESTAMP)

) AS v(opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt)
WHERE NOT EXISTS (SELECT 1 FROM tb_opportunity o WHERE o.title = v.title AND o.organization = v.organization);

-- ============================================
-- 3. tb_student_skill 데이터 추가 (2023-2025 학생 연동)
-- ============================================
-- 학과별 관련 스킬 매핑 후 학생에게 할당
-- 컴퓨터/IT 계열 학과
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    sk.skill_cd,
    FLOOR(1 + RANDOM() * 4) as current_level,  -- 1-4
    5 as target_level,
    FLOOR(RANDOM() * 5) as evidence_count,
    CASE WHEN RANDOM() > 0.5 THEN CURRENT_DATE - FLOOR(RANDOM() * 180)::INT ELSE NULL END as last_verified_date,
    CASE WHEN RANDOM() > 0.5 THEN 'self_assessment' ELSE 'course_completion' END as verification_source,
    CASE WHEN RANDOM() < 0.4 THEN 'up' WHEN RANDOM() < 0.7 THEN 'stable' ELSE 'down' END as trend,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT skill_cd FROM (VALUES
        ('SK01'), ('SK02'), ('SK03'), ('SK04'), ('SK05'), ('SK06'), ('SK07'), ('SK42'), ('SK36'), ('SK44')
    ) AS skills(skill_cd)
    ORDER BY RANDOM() LIMIT FLOOR(3 + RANDOM() * 4)::INT  -- 3-6개 스킬 랜덤 할당
) sk
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1160', '2059', '684', '3554', '3680', '2823', '382', '666', '649', '1169', '1337')
AND NOT EXISTS (
    SELECT 1 FROM tb_student_skill ss WHERE ss.student_id = s.student_id AND ss.skill_cd = sk.skill_cd
);

-- 경영/경제 계열 학과
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    sk.skill_cd,
    FLOOR(1 + RANDOM() * 4) as current_level,
    5 as target_level,
    FLOOR(RANDOM() * 5) as evidence_count,
    CASE WHEN RANDOM() > 0.5 THEN CURRENT_DATE - FLOOR(RANDOM() * 180)::INT ELSE NULL END as last_verified_date,
    CASE WHEN RANDOM() > 0.5 THEN 'self_assessment' ELSE 'certification' END as verification_source,
    CASE WHEN RANDOM() < 0.4 THEN 'up' WHEN RANDOM() < 0.7 THEN 'stable' ELSE 'down' END as trend,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT skill_cd FROM (VALUES
        ('SK07'), ('SK03'), ('SK53'), ('SK63'), ('SK64'), ('SK76'), ('SK62'), ('SK10')
    ) AS skills(skill_cd)
    ORDER BY RANDOM() LIMIT FLOOR(3 + RANDOM() * 3)::INT
) sk
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1440', '484', '488', '497', '486', '1012', '1114', '1004', '1443', '1448')
AND NOT EXISTS (
    SELECT 1 FROM tb_student_skill ss WHERE ss.student_id = s.student_id AND ss.skill_cd = sk.skill_cd
);

-- 디자인 계열 학과
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    sk.skill_cd,
    FLOOR(1 + RANDOM() * 4) as current_level,
    5 as target_level,
    FLOOR(RANDOM() * 5) as evidence_count,
    CASE WHEN RANDOM() > 0.5 THEN CURRENT_DATE - FLOOR(RANDOM() * 180)::INT ELSE NULL END as last_verified_date,
    CASE WHEN RANDOM() > 0.5 THEN 'portfolio' ELSE 'course_completion' END as verification_source,
    CASE WHEN RANDOM() < 0.4 THEN 'up' WHEN RANDOM() < 0.7 THEN 'stable' ELSE 'down' END as trend,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT skill_cd FROM (VALUES
        ('SK54'), ('SK55'), ('SK56'), ('SK57'), ('SK58'), ('SK59'), ('SK60'), ('SK66')
    ) AS skills(skill_cd)
    ORDER BY RANDOM() LIMIT FLOOR(3 + RANDOM() * 4)::INT
) sk
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1127', '711', '2532', '2533', '2534', '1250', '436', '723', '2531', '3691')
AND NOT EXISTS (
    SELECT 1 FROM tb_student_skill ss WHERE ss.student_id = s.student_id AND ss.skill_cd = sk.skill_cd
);

-- 공학 계열 학과 (기계, 전자, 화학 등)
INSERT INTO tb_student_skill (student_skill_id, student_id, skill_cd, current_level, target_level, evidence_count, last_verified_date, verification_source, trend, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    sk.skill_cd,
    FLOOR(1 + RANDOM() * 4) as current_level,
    5 as target_level,
    FLOOR(RANDOM() * 5) as evidence_count,
    CASE WHEN RANDOM() > 0.5 THEN CURRENT_DATE - FLOOR(RANDOM() * 180)::INT ELSE NULL END as last_verified_date,
    CASE WHEN RANDOM() > 0.5 THEN 'self_assessment' ELSE 'project' END as verification_source,
    CASE WHEN RANDOM() < 0.4 THEN 'up' WHEN RANDOM() < 0.7 THEN 'stable' ELSE 'down' END as trend,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT skill_cd FROM (VALUES
        ('SK17'), ('SK01'), ('SK43'), ('SK42'), ('SK70'), ('SK69'), ('SK73'), ('SK61')
    ) AS skills(skill_cd)
    ORDER BY RANDOM() LIMIT FLOOR(3 + RANDOM() * 4)::INT
) sk
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1034', '442', '1083', '444', '446', '643', '639', '641', '1089', '645', '1086')
AND NOT EXISTS (
    SELECT 1 FROM tb_student_skill ss WHERE ss.student_id = s.student_id AND ss.skill_cd = sk.skill_cd
);

-- ============================================
-- 4. tb_portfolio 데이터 추가 (학과/전공 맞춤)
-- ============================================
-- IT 계열 학생 포트폴리오
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, is_featured, display_order, artifact_type, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    pt.item_type,
    pt.title || ' - ' || s.student_nm,
    pt.description,
    CURRENT_DATE - FLOOR(RANDOM() * 365)::INT,
    CASE WHEN RANDOM() > 0.3 THEN CURRENT_DATE - FLOOR(RANDOM() * 100)::INT ELSE NULL END,
    pt.skills_used,
    CASE WHEN RANDOM() > 0.5 THEN 'https://github.com/' || s.student_id ELSE NULL END,
    CASE WHEN RANDOM() < 0.2 THEN 'Y' ELSE 'N' END,
    ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY RANDOM()),
    pt.artifact_type,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT * FROM (VALUES
        ('project', '웹 애플리케이션 개발 프로젝트', 'React와 Node.js를 활용한 풀스택 웹 개발 프로젝트', '{"frontend": ["React", "TypeScript"], "backend": ["Node.js", "Express"], "database": ["PostgreSQL"]}'::jsonb, 'code'),
        ('project', 'AI 챗봇 개발', 'OpenAI API를 활용한 대화형 AI 챗봇 개발', '{"ai": ["Python", "OpenAI API"], "backend": ["FastAPI"]}'::jsonb, 'code'),
        ('course', '알고리즘 문제 해결', '백준/프로그래머스 알고리즘 문제 150+ 해결', '{"languages": ["Python", "Java"]}'::jsonb, 'document'),
        ('certification', 'AWS Solutions Architect', 'AWS 공인 솔루션스 아키텍트 자격증 취득', '{"cloud": ["AWS"]}'::jsonb, 'document'),
        ('activity', '오픈소스 기여', 'GitHub 오픈소스 프로젝트 기여 활동', '{"tools": ["Git", "GitHub"]}'::jsonb, 'code')
    ) AS t(item_type, title, description, skills_used, artifact_type)
    ORDER BY RANDOM() LIMIT FLOOR(2 + RANDOM() * 3)::INT
) pt
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1160', '2059', '684', '3554', '3680', '2823', '382', '666', '649', '1169')
AND NOT EXISTS (
    SELECT 1 FROM tb_portfolio p WHERE p.student_id = s.student_id AND p.title LIKE '%' || pt.title || '%'
);

-- 경영/경제 계열 학생 포트폴리오
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, is_featured, display_order, artifact_type, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    pt.item_type,
    pt.title || ' - ' || s.student_nm,
    pt.description,
    CURRENT_DATE - FLOOR(RANDOM() * 365)::INT,
    CASE WHEN RANDOM() > 0.3 THEN CURRENT_DATE - FLOOR(RANDOM() * 100)::INT ELSE NULL END,
    pt.skills_used,
    NULL,
    CASE WHEN RANDOM() < 0.2 THEN 'Y' ELSE 'N' END,
    ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY RANDOM()),
    pt.artifact_type,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT * FROM (VALUES
        ('project', '비즈니스 전략 분석 프로젝트', '실제 기업 사례를 분석하고 전략 제안', '{"analysis": ["Excel", "PowerPoint"], "research": ["Market Analysis"]}'::jsonb, 'document'),
        ('competition', '마케팅 공모전 수상', '대학생 마케팅 공모전 입상 (우수상)', '{"marketing": ["Digital Marketing", "Brand Strategy"]}'::jsonb, 'document'),
        ('activity', '창업 동아리 활동', '대학 창업 동아리에서 비즈니스 모델 개발', '{"startup": ["Business Model Canvas", "Pitch"]}'::jsonb, 'presentation'),
        ('certification', 'TOEIC 900점 이상', 'TOEIC 920점 취득', '{"language": ["English"]}'::jsonb, 'document'),
        ('internship', '기업 인턴십 경험', '대기업 마케팅팀 하계 인턴십', '{"skills": ["Data Analysis", "Presentation"]}'::jsonb, 'document')
    ) AS t(item_type, title, description, skills_used, artifact_type)
    ORDER BY RANDOM() LIMIT FLOOR(2 + RANDOM() * 3)::INT
) pt
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1440', '484', '488', '497', '486', '1012', '1114', '1004', '1443', '1448')
AND NOT EXISTS (
    SELECT 1 FROM tb_portfolio p WHERE p.student_id = s.student_id AND p.title LIKE '%' || pt.title || '%'
);

-- 디자인 계열 학생 포트폴리오
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, is_featured, display_order, artifact_type, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    pt.item_type,
    pt.title || ' - ' || s.student_nm,
    pt.description,
    CURRENT_DATE - FLOOR(RANDOM() * 365)::INT,
    CASE WHEN RANDOM() > 0.3 THEN CURRENT_DATE - FLOOR(RANDOM() * 100)::INT ELSE NULL END,
    pt.skills_used,
    CASE WHEN RANDOM() > 0.5 THEN 'https://behance.net/' || s.student_id ELSE 'https://dribbble.com/' || s.student_id END,
    CASE WHEN RANDOM() < 0.3 THEN 'Y' ELSE 'N' END,
    ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY RANDOM()),
    pt.artifact_type,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT * FROM (VALUES
        ('project', 'UI/UX 디자인 프로젝트', '모바일 앱 UI/UX 디자인 및 프로토타입 제작', '{"design": ["Figma", "Adobe XD"], "prototype": ["Principle"]}'::jsonb, 'design'),
        ('project', '브랜드 아이덴티티 디자인', '스타트업 브랜드 아이덴티티 및 로고 디자인', '{"design": ["Illustrator", "Photoshop"]}'::jsonb, 'design'),
        ('competition', '디자인 공모전 수상', '전국 대학생 디자인 공모전 입상', '{"design": ["Creative Design"]}'::jsonb, 'design'),
        ('activity', '모션그래픽 작업', '유튜브 채널 인트로 및 모션그래픽 제작', '{"motion": ["After Effects", "Premiere Pro"]}'::jsonb, 'video'),
        ('project', '3D 모델링 프로젝트', '제품 3D 모델링 및 렌더링 작업', '{"3d": ["Blender", "3ds Max"]}'::jsonb, 'design')
    ) AS t(item_type, title, description, skills_used, artifact_type)
    ORDER BY RANDOM() LIMIT FLOOR(2 + RANDOM() * 3)::INT
) pt
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1127', '711', '2532', '2533', '2534', '1250', '436', '723', '2531', '3691')
AND NOT EXISTS (
    SELECT 1 FROM tb_portfolio p WHERE p.student_id = s.student_id AND p.title LIKE '%' || pt.title || '%'
);

-- 의료/보건 계열 학생 포트폴리오
INSERT INTO tb_portfolio (portfolio_id, student_id, item_type, title, description, start_date, end_date, skills_used, evidence_url, is_featured, display_order, artifact_type, ins_user_id, ins_dt)
SELECT
    uuid_generate_v4(),
    s.student_id,
    pt.item_type,
    pt.title || ' - ' || s.student_nm,
    pt.description,
    CURRENT_DATE - FLOOR(RANDOM() * 365)::INT,
    CASE WHEN RANDOM() > 0.3 THEN CURRENT_DATE - FLOOR(RANDOM() * 100)::INT ELSE NULL END,
    pt.skills_used,
    NULL,
    CASE WHEN RANDOM() < 0.2 THEN 'Y' ELSE 'N' END,
    ROW_NUMBER() OVER (PARTITION BY s.student_id ORDER BY RANDOM()),
    pt.artifact_type,
    'SEED_V3',
    CURRENT_TIMESTAMP
FROM tb_student s
CROSS JOIN LATERAL (
    SELECT * FROM (VALUES
        ('clinical', '임상실습 기록', '대학병원 임상실습 참여 및 사례 연구', '{"clinical": ["Patient Care", "Medical Records"]}'::jsonb, 'document'),
        ('certification', 'BLS 자격증', '기본 심폐소생술 자격증 취득', '{"certification": ["BLS", "CPR"]}'::jsonb, 'document'),
        ('research', '의료 데이터 연구', '의료 데이터 분석 및 연구 참여', '{"research": ["SPSS", "Medical Statistics"]}'::jsonb, 'document'),
        ('volunteer', '의료봉사 활동', '농촌/해외 의료봉사 활동 참여', '{"volunteer": ["Healthcare", "Community Service"]}'::jsonb, 'document'),
        ('activity', '보건교육 활동', '지역사회 보건교육 프로그램 기획 및 실행', '{"education": ["Health Education", "Presentation"]}'::jsonb, 'presentation')
    ) AS t(item_type, title, description, skills_used, artifact_type)
    ORDER BY RANDOM() LIMIT FLOOR(2 + RANDOM() * 2)::INT
) pt
WHERE s.admission_year IN (2023, 2024, 2025)
AND s.department_cd IN ('1144', '356', '590', '592', '578', '576', '1063', '1051', '1056', '1237', '1271')
AND NOT EXISTS (
    SELECT 1 FROM tb_portfolio p WHERE p.student_id = s.student_id AND p.title LIKE '%' || pt.title || '%'
);

-- ============================================
-- 5. 결과 확인
-- ============================================
DO $$
DECLARE
    v_skill_cnt INT;
    v_opp_cnt INT;
    v_stuskill_cnt INT;
    v_portfolio_cnt INT;
BEGIN
    SELECT COUNT(*) INTO v_skill_cnt FROM tb_skill;
    SELECT COUNT(*) INTO v_opp_cnt FROM tb_opportunity;
    SELECT COUNT(*) INTO v_stuskill_cnt FROM tb_student_skill;
    SELECT COUNT(*) INTO v_portfolio_cnt FROM tb_portfolio;

    RAISE NOTICE '======================================';
    RAISE NOTICE '데이터 생성 결과';
    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE 'tb_skill: % 건', v_skill_cnt;
    RAISE NOTICE 'tb_opportunity: % 건', v_opp_cnt;
    RAISE NOTICE 'tb_student_skill: % 건', v_stuskill_cnt;
    RAISE NOTICE 'tb_portfolio: % 건', v_portfolio_cnt;
    RAISE NOTICE '======================================';
END $$;
