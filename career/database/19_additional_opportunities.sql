-- ============================================
-- IDINO Career - Additional Opportunities (50+ more)
-- Date: 2026-01-26
-- Web-based real program references
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Additional Internship Programs (15건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

-- IT/Tech Companies
(gen_random_uuid(), 'internship', '2025년 라인플러스 신입/인턴 개발자 채용', '라인플러스',
'라인 메신저, 라인 뮤직 등 글로벌 서비스 개발 인턴십. 백엔드, iOS, Android, 데이터 엔지니어링.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘", "자료구조"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true, "meal": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'경기도 성남시', true, 50, 'open',
'https://careers.linepluscorp.com',
ARRAY['라인', '메신저', '개발', '글로벌'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 쿠팡 Engineering 인턴', '쿠팡',
'쿠팡 물류/이커머스 기술 인턴십. 백엔드, 프론트엔드, 데이터 사이언스, ML 엔지니어링.',
'{"min_gpa": 3.0, "skills": ["Java", "Python", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 280만원", "certificate": true, "meal": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 송파구', false, 80, 'open',
'https://www.coupang.jobs',
ARRAY['쿠팡', '이커머스', '물류', 'Engineering'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 배달의민족 인턴십', '우아한형제들',
'배달의민족 서비스 개발 인턴십. 서버, 웹/앱, 데이터, ML 분야.',
'{"min_gpa": 3.0, "skills": ["Java", "Kotlin", "Spring"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'서울시 송파구', true, 40, 'open',
'https://www.woowahan.com',
ARRAY['배민', '우아한형제들', '개발', '서버'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 토스 Tech 인턴십', '비바리퍼블리카',
'토스 핀테크 서비스 개발 인턴십. Server, Frontend, Data, Security.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 280만원", "certificate": true, "meal": true}',
'2025-03-01', '2025-04-15', '2025-07-01', '2025-08-31',
'서울시 강남구', true, 60, 'open',
'https://toss.im/career',
ARRAY['토스', '핀테크', '금융', 'Tech'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 당근마켓 인턴십', '당근마켓',
'당근마켓 서비스 개발 인턴십. 백엔드, iOS/Android, 웹 프론트엔드.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 서초구', true, 30, 'open',
'https://about.daangn.com/jobs',
ARRAY['당근마켓', '커뮤니티', '개발'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

-- 제조/반도체
(gen_random_uuid(), 'internship', '2025년 삼성SDI 배터리 연구 인턴', '삼성SDI',
'삼성SDI 2차전지 연구개발 인턴십. 배터리 소재, 셀 설계, 공정 기술.',
'{"min_gpa": 3.2, "major": ["화학공학", "재료공학", "전자공학"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'경기도 수원시', false, 50, 'open',
'https://www.samsungsdi.co.kr',
ARRAY['삼성SDI', '배터리', '2차전지'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 LG에너지솔루션 인턴십', 'LG에너지솔루션',
'LG에너지솔루션 배터리 기술 인턴십. 배터리 연구, 생산기술, 품질관리.',
'{"min_gpa": 3.0, "major": ["화학공학", "재료공학", "기계공학"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true, "housing": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'대전광역시', false, 80, 'open',
'https://www.lgensol.com',
ARRAY['LG에너지솔루션', '배터리', '전기차'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP),

-- 금융/컨설팅
(gen_random_uuid(), 'internship', '2025년 삼성카드 디지털/IT 인턴', '삼성카드',
'삼성카드 디지털/IT 인턴십. 빅데이터 분석, AI, 핀테크 서비스 개발.',
'{"min_gpa": 3.0, "skills": ["데이터분석", "Python"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 중구', true, 30, 'open',
'https://www.samsungcard.com',
ARRAY['삼성카드', '금융', 'IT', '핀테크'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 신한은행 디지털 인턴', '신한은행',
'신한은행 디지털/IT 인턴십. AI, 빅데이터, 디지털 채널 개발.',
'{"min_gpa": 3.0, "skills": ["데이터분석", "프로그래밍"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 중구', true, 40, 'open',
'https://www.shinhan.com',
ARRAY['신한은행', '금융', '디지털', 'AI'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 맥킨지 인턴십', '맥킨지 앤드 컴퍼니',
'맥킨지 컨설팅 인턴십. 경영/전략 컨설팅 프로젝트 참여.',
'{"min_gpa": 3.5, "language": "영어 비즈니스 수준", "grade": [3, 4]}',
'{"salary": "월 350만원", "certificate": true}',
'2025-02-01', '2025-03-31', '2025-07-01', '2025-08-31',
'서울시 종로구', false, 20, 'open',
'https://www.mckinsey.com',
ARRAY['맥킨지', '컨설팅', '전략'],
ARRAY['DEPT014', 'DEPT013'], 'SEED_V3', CURRENT_TIMESTAMP),

-- 게임/엔터테인먼트
(gen_random_uuid(), 'internship', '2025년 크래프톤 게임 개발 인턴', '크래프톤',
'크래프톤 게임 개발 인턴십. 게임 프로그래밍, 아트, 기획.',
'{"min_gpa": 2.8, "skills": ["C++", "Unreal", "Unity"], "grade": [3, 4]}',
'{"salary": "월 230만원", "certificate": true, "meal": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 강남구', false, 40, 'open',
'https://www.krafton.com',
ARRAY['크래프톤', '게임', 'PUBG'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 NC소프트 인턴십', 'NC소프트',
'NC소프트 게임 개발 인턴십. AI/ML, 게임 서버, 클라이언트.',
'{"min_gpa": 3.0, "skills": ["C++", "Python", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'경기도 성남시', false, 50, 'open',
'https://careers.ncsoft.com',
ARRAY['NC소프트', '게임', '리니지', 'AI'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 스마일게이트 인턴십', '스마일게이트',
'스마일게이트 게임/미디어 인턴십. 게임 개발, AI, 콘텐츠.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "게임개발"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'경기도 성남시', false, 30, 'open',
'https://www.smilegate.com',
ARRAY['스마일게이트', '게임', '로스트아크'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

-- 미디어/콘텐츠
(gen_random_uuid(), 'internship', '2025년 네이버웹툰 인턴십', '네이버웹툰',
'네이버웹툰 기술 인턴십. 플랫폼 개발, AI/ML, 데이터 분석.',
'{"min_gpa": 3.0, "skills": ["Python", "프로그래밍"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'경기도 성남시', true, 30, 'open',
'https://webtoonscorp.com',
ARRAY['네이버웹툰', '콘텐츠', '플랫폼'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 넷마블 인턴십', '넷마블',
'넷마블 게임 개발/운영 인턴십. 게임 서버, 클라이언트, 데이터.',
'{"min_gpa": 3.0, "skills": ["C++", "Unity", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 구로구', false, 40, 'open',
'https://company.netmarble.com',
ARRAY['넷마블', '게임', '모바일'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP);

-- ============================================
-- 2. Additional Contest/Competition (15건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'contest', '2025 Kaggle Competition: AI for Good', 'Kaggle/Google',
'사회문제 해결을 위한 AI 모델 개발 경진대회. 환경, 헬스케어, 교육 분야.',
'{"skills": ["Python", "머신러닝", "딥러닝"]}',
'{"prize": "총 상금 $100,000", "certificate": true}',
'2025-04-01', '2025-07-31', '2025-04-01', '2025-08-31',
'온라인', true, null, 'open',
'https://www.kaggle.com',
ARRAY['Kaggle', 'AI', '머신러닝', '글로벌'],
ARRAY['DEPT001', 'DEPT002', 'DEPT013'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 Google Hash Code', 'Google',
'구글 해시코드 알고리즘 경진대회. 2-4인 팀 구성.',
'{"team_size": 4, "skills": ["알고리즘", "프로그래밍"]}',
'{"prize": "Google 굿즈 및 채용 우대", "certificate": true}',
'2025-01-15', '2025-02-28', '2025-02-15', '2025-04-30',
'온라인', true, null, 'open',
'https://codingcompetitions.withgoogle.com',
ARRAY['Google', '해시코드', '알고리즘'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 Microsoft Imagine Cup', 'Microsoft',
'마이크로소프트 글로벌 학생 기술 경진대회. AI, 웹, 모바일 솔루션.',
'{"skills": ["프로그래밍", "기획", "디자인"]}',
'{"prize": "대상 $100,000", "certificate": true, "멘토링": true}',
'2025-01-01', '2025-05-31', '2025-01-01', '2025-07-31',
'온라인/미국', true, null, 'open',
'https://imaginecup.microsoft.com',
ARRAY['Microsoft', 'Imagine Cup', '글로벌', '스타트업'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 AWS DeepRacer League', 'Amazon Web Services',
'AWS 자율주행 레이싱 경진대회. 강화학습 기반 자율주행 모델 개발.',
'{"skills": ["Python", "강화학습", "AWS"]}',
'{"prize": "총 상금 $500,000+", "certificate": true}',
'2025-03-01', '2025-10-31', '2025-03-01', '2025-11-30',
'온라인/라스베이거스', true, null, 'open',
'https://aws.amazon.com/deepracer',
ARRAY['AWS', 'DeepRacer', '자율주행', '강화학습'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 네이버 CLOVA AI Rush', '네이버클라우드',
'네이버 클로바 AI 기술 챌린지. 자연어처리, 음성인식, 컴퓨터비전.',
'{"skills": ["Python", "딥러닝", "NLP"]}',
'{"prize": "총 상금 5000만원", "certificate": true, "채용우대": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-09-30',
'온라인', true, null, 'open',
'https://clova.ai',
ARRAY['네이버', 'CLOVA', 'AI', 'NLP'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 카카오 if(kakao) 개발자 컨퍼런스 공모전', '카카오',
'카카오 개발자 컨퍼런스 발표자 공모. 기술 세션 발표 기회.',
'{"skills": ["기술발표", "개발경험"]}',
'{"prize": "발표 기회 및 컨퍼런스 참가권", "certificate": true}',
'2025-06-01', '2025-08-15', '2025-10-01', '2025-10-03',
'서울', false, 30, 'open',
'https://if.kakao.com',
ARRAY['카카오', 'if(kakao)', '컨퍼런스', '발표'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 대한민국 인재상 (SW 분야)', '교육부',
'대한민국 인재상 SW 분야. 프로그래밍 및 SW 분야 우수 인재 선발.',
'{"skills": ["프로그래밍", "SW개발"], "grade": [3, 4]}',
'{"prize": "교육부 장관상 및 장학금", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-10-31',
'전국', false, 50, 'open',
'https://www.moe.go.kr',
ARRAY['인재상', '교육부', 'SW', '장학금'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 삼성 AI Challenge', '삼성전자',
'삼성 AI 문제 해결 챌린지. 실제 비즈니스 문제 AI 솔루션 개발.',
'{"skills": ["AI", "머신러닝", "Python"]}',
'{"prize": "대상 3000만원", "certificate": true, "채용연계": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-09-30',
'온라인/서울', true, null, 'open',
'https://research.samsung.com',
ARRAY['삼성', 'AI', '챌린지', '채용연계'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 창업진흥원 대학생 창업 경진대회', '창업진흥원',
'대학생 창업 아이디어 경진대회. 기술 기반 스타트업 아이디어.',
'{"skills": ["기획", "사업계획서", "프레젠테이션"]}',
'{"prize": "대상 5000만원 창업지원금", "certificate": true, "멘토링": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-10-31',
'전국', true, null, 'open',
'https://www.kised.or.kr',
ARRAY['창업진흥원', '창업', '스타트업'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 산업통상자원부 AI 그랜드 챌린지', '산업통상자원부',
'AI 기술 기반 산업 혁신 솔루션 경진대회.',
'{"skills": ["AI", "빅데이터", "산업지식"]}',
'{"prize": "총 상금 10억원", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-12-31',
'온라인/전국', true, null, 'open',
'https://www.motie.go.kr',
ARRAY['산업부', 'AI', '그랜드챌린지'],
ARRAY['DEPT001', 'DEPT002', 'DEPT006'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 과기정통부 ICT 멘토링 프로젝트', '과학기술정보통신부',
'ICT 분야 멘토-멘티 매칭 프로젝트. 기업 실무 프로젝트 수행.',
'{"skills": ["프로그래밍", "프로젝트관리"], "grade": [2, 3, 4]}',
'{"prize": "참가비 지원 및 수료증", "certificate": true, "멘토링": true}',
'2025-03-01', '2025-04-30', '2025-05-01', '2025-10-31',
'온라인/전국', true, 500, 'open',
'https://www.msit.go.kr',
ARRAY['과기정통부', 'ICT', '멘토링'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 제약/바이오 데이터 AI 경진대회', '한국제약바이오협회',
'제약/바이오 분야 AI 활용 데이터 분석 경진대회.',
'{"skills": ["AI", "바이오인포매틱스", "데이터분석"]}',
'{"prize": "총 상금 3000만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-10-31',
'온라인', true, null, 'open',
'https://www.kpbma.or.kr',
ARRAY['제약', '바이오', 'AI', '데이터'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 스마트시티 아이디어 공모전', '국토교통부',
'스마트시티 혁신 아이디어 공모전. 도시문제 해결 솔루션.',
'{"skills": ["기획", "IoT", "데이터분석"]}',
'{"prize": "대상 2000만원", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-09-30',
'온라인', true, null, 'open',
'https://www.molit.go.kr',
ARRAY['국토부', '스마트시티', '혁신'],
ARRAY['DEPT001', 'DEPT006'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 금융보안원 FinTech 보안 챌린지', '금융보안원',
'핀테크 보안 취약점 발견 및 보안 솔루션 개발 챌린지.',
'{"skills": ["보안", "해킹", "핀테크"]}',
'{"prize": "총 상금 2000만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-09-30',
'온라인', true, null, 'open',
'https://www.fsec.or.kr',
ARRAY['금융보안원', '핀테크', '보안', '해킹'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 디자인코리아 UX/UI 공모전', '한국디자인진흥원',
'UX/UI 디자인 공모전. 사용자 경험 혁신 디자인 작품.',
'{"skills": ["UX", "UI", "Figma", "디자인"]}',
'{"prize": "대상 1000만원", "certificate": true}',
'2025-06-01', '2025-08-31', '2025-06-01', '2025-11-30',
'온라인/서울', true, null, 'open',
'https://www.designkorea.or.kr',
ARRAY['디자인코리아', 'UX', 'UI', '디자인'],
ARRAY['DEPT025', 'DEPT023'], 'SEED_V3', CURRENT_TIMESTAMP);

-- ============================================
-- 3. Additional Research/Project Opportunities (10건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'lab', '2025 NAVER AI Lab 연구연수생', '네이버 AI Lab',
'네이버 AI 연구소 학부연구생 프로그램. 자연어처리, 컴퓨터비전, 추천시스템.',
'{"min_gpa": 3.5, "skills": ["Python", "딥러닝"], "grade": [3, 4]}',
'{"salary": "월 150만원", "certificate": true, "논문공동저자": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-12-31',
'경기도 성남시', true, 30, 'open',
'https://clova.ai/en/research',
ARRAY['네이버', 'AI Lab', '연구', 'NLP'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 삼성리서치 학부연구프로그램', '삼성리서치',
'삼성리서치 학부연구 프로그램. AI, 네트워크, 보안, 미래기술 연구.',
'{"min_gpa": 3.5, "skills": ["연구", "프로그래밍"], "grade": [3, 4]}',
'{"salary": "월 180만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'서울시 서초구', false, 50, 'open',
'https://research.samsung.com',
ARRAY['삼성리서치', '연구', 'AI', '6G'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 카카오 클라우드 스쿨', '카카오클라우드',
'카카오 클라우드 기술 교육 프로그램. 클라우드 인프라, 쿠버네티스, DevOps.',
'{"skills": ["Linux", "Docker", "클라우드"], "grade": [3, 4, "졸업자"]}',
'{"교육비": "전액무료", "취업연계": true, "수료증": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-12-31',
'온라인/판교', true, 100, 'open',
'https://kakaocloud.com',
ARRAY['카카오클라우드', '클라우드', 'DevOps'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 네이버 부스트코스 AI 트랙', '네이버커넥트재단',
'AI 엔지니어 양성 온라인 교육. 머신러닝, 딥러닝, 자연어처리.',
'{"skills": ["Python", "수학"], "grade": [2, 3, 4]}',
'{"교육비": "전액무료", "수료증": true, "멘토링": true}',
'2025-02-01', '2025-03-31', '2025-05-01', '2025-08-31',
'온라인', true, 500, 'open',
'https://www.boostcourse.org',
ARRAY['네이버', '부스트코스', 'AI', '딥러닝'],
ARRAY['DEPT001', 'DEPT002', 'DEPT013'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 토스 NEXT 개발자 챌린지', '비바리퍼블리카',
'토스 개발자 양성 프로그램. 3개월 집중 교육 후 인턴십 연계.',
'{"skills": ["프로그래밍", "알고리즘"], "grade": [3, 4, "졸업자"]}',
'{"교육비": "전액무료", "인턴연계": true, "멘토링": true}',
'2025-03-01', '2025-04-30', '2025-06-01', '2025-08-31',
'서울시 강남구', false, 50, 'open',
'https://toss.im/career',
ARRAY['토스', 'NEXT', '개발자', '양성'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 POSTECH AI 연구 인턴십', 'POSTECH AI대학원',
'POSTECH AI 대학원 학부연구 인턴십. 최첨단 AI 연구 참여.',
'{"min_gpa": 3.7, "skills": ["Python", "딥러닝"], "grade": [3, 4]}',
'{"salary": "월 120만원", "certificate": true, "숙소제공": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'경상북도 포항시', false, 30, 'open',
'https://ai.postech.ac.kr',
ARRAY['POSTECH', 'AI', '연구', '대학원'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 서울대 AI연구원 학부연구생', '서울대학교 AI연구원',
'서울대 AI연구원 학부연구 프로그램. 다양한 AI 연구 프로젝트 참여.',
'{"min_gpa": 3.5, "skills": ["Python", "머신러닝"], "grade": [3, 4]}',
'{"salary": "월 100만원", "certificate": true}',
'2025-02-01', '2025-03-31', '2025-03-01', '2025-08-31',
'서울시 관악구', false, 50, 'open',
'https://aiis.snu.ac.kr',
ARRAY['서울대', 'AI연구원', '학부연구'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 삼성 DX Academy', '삼성전자',
'삼성 디지털 전환 전문가 양성 프로그램. AI, 클라우드, 데이터.',
'{"skills": ["프로그래밍", "데이터분석"], "grade": [4, "졸업자"]}',
'{"교육비": "전액무료", "월지원금": "100만원", "취업연계": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-12-31',
'서울/대전/수원', false, 500, 'open',
'https://www.samsungcareers.com',
ARRAY['삼성', 'DX', 'Academy', '디지털전환'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 구글 개발자 그룹 (GDG) 리드 프로그램', 'Google',
'GDG 커뮤니티 리더 양성 프로그램. 기술 커뮤니티 운영 및 이벤트 기획.',
'{"skills": ["커뮤니케이션", "기술지식", "리더십"]}',
'{"혜택": "구글 리소스 지원, 글로벌 네트워킹", "certificate": true}',
'2025-01-01', '2025-02-28', '2025-03-01', '2026-02-28',
'전국', true, 30, 'open',
'https://developers.google.com/community/gdg',
ARRAY['구글', 'GDG', '커뮤니티', '리더'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 마이크로소프트 MLSA 프로그램', 'Microsoft',
'Microsoft Learn Student Ambassadors 학생 앰배서더 프로그램.',
'{"skills": ["기술지식", "커뮤니케이션", "리더십"]}',
'{"혜택": "Azure 크레딧, 인증시험 바우처, 글로벌 네트워킹", "certificate": true}',
'2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31',
'전국', true, 100, 'open',
'https://studentambassadors.microsoft.com',
ARRAY['Microsoft', 'MLSA', '앰배서더', 'Azure'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP);

-- ============================================
-- 4. Additional Scholarship Programs (10건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'scholarship', '2025 네이버 D2SF 장학금', '네이버',
'네이버 D2 Startup Factory 장학금. SW/AI 분야 우수 학생.',
'{"min_gpa": 3.3, "major": ["컴퓨터공학", "소프트웨어"]}',
'{"amount": "연 500만원", "duration": "1년", "멘토링": true}',
'2025-03-01', '2025-05-31', '2025-03-01', '2026-02-28',
'전국', true, 30, 'open',
'https://d2.naver.com',
ARRAY['네이버', 'D2SF', '장학금', 'SW'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 카카오 장학금', '카카오임팩트재단',
'카카오 사회공헌 장학금. IT/SW 분야 저소득층 대학생.',
'{"min_gpa": 3.0, "income": "저소득층", "major": ["IT", "SW"]}',
'{"amount": "등록금 전액", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 50, 'open',
'https://www.kakaoimpact.org',
ARRAY['카카오', '장학금', 'IT', '사회공헌'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 구글 Women Techmakers 장학금', 'Google',
'구글 여성 기술인 장학금. CS/Engineering 전공 여학생.',
'{"min_gpa": 3.5, "gender": "여성", "major": ["CS", "공학"]}',
'{"amount": "$10,000", "duration": "1년", "글로벌프로그램": true}',
'2025-01-01', '2025-04-30', '2025-09-01', '2026-08-31',
'전국', true, 10, 'open',
'https://www.womentechmakers.com',
ARRAY['구글', '여성', '장학금', 'WTM'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 삼성물산 장학금', '삼성물산',
'삼성물산 건설/엔지니어링 장학금. 건축, 토목, 기계 전공.',
'{"min_gpa": 3.3, "major": ["건축", "토목", "기계"]}',
'{"amount": "연 400만원", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 30, 'open',
'https://www.samsungcnt.com',
ARRAY['삼성물산', '장학금', '건설', '엔지니어링'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 CJ문화재단 장학금', 'CJ문화재단',
'CJ 문화예술 장학금. 문화, 예술, 미디어 분야 학생.',
'{"min_gpa": 3.0, "major": ["문화", "예술", "미디어", "디자인"]}',
'{"amount": "연 400만원", "duration": "졸업시까지"}',
'2025-03-01', '2025-05-31', '2025-03-01', '2029-02-28',
'전국', true, 50, 'open',
'https://www.cjazit.org',
ARRAY['CJ', '장학금', '문화', '예술'],
ARRAY['DEPT025'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 농협 농촌 인재 장학금', '농협',
'농협 농촌 출신 인재 장학금. 농촌 출신 우수 대학생.',
'{"min_gpa": 3.0, "지역": "농촌출신"}',
'{"amount": "연 300만원", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 100, 'open',
'https://www.nonghyup.com',
ARRAY['농협', '장학금', '농촌', '인재'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 롯데장학재단 장학금', '롯데장학재단',
'롯데 인재양성 장학금. 이공계 및 경상계 우수 학생.',
'{"min_gpa": 3.3}',
'{"amount": "등록금+생활비", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 80, 'open',
'https://www.lottescholarship.or.kr',
ARRAY['롯데', '장학금', '이공계', '경상계'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT014'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 한화 미래세대 장학금', '한화그룹',
'한화그룹 미래세대 장학금. 과학기술 분야 우수 학생.',
'{"min_gpa": 3.3, "major": ["과학", "기술", "공학"]}',
'{"amount": "연 500만원", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 50, 'open',
'https://www.hanwha.co.kr',
ARRAY['한화', '장학금', '미래세대', '과학기술'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 GS칼텍스 장학금', 'GS칼텍스',
'GS칼텍스 인재양성 장학금. 화학, 에너지, 공학 분야.',
'{"min_gpa": 3.3, "major": ["화학", "에너지", "공학"]}',
'{"amount": "등록금 전액", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 30, 'open',
'https://www.gscaltex.com',
ARRAY['GS칼텍스', '장학금', '에너지', '화학'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 두산 장학금', '두산연강재단',
'두산 인재양성 장학금. 이공계 우수 학생 대상.',
'{"min_gpa": 3.3, "major": ["이공계"]}',
'{"amount": "연 400만원", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 40, 'open',
'https://www.doosan.com',
ARRAY['두산', '장학금', '이공계'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V3', CURRENT_TIMESTAMP);

-- ============================================
-- Verify Results
-- ============================================

DO $$
DECLARE
    v_total INT;
    v_new_count INT;
    v_by_type TEXT;
BEGIN
    SELECT COUNT(*) INTO v_total FROM tb_opportunity;
    SELECT COUNT(*) INTO v_new_count FROM tb_opportunity WHERE ins_user_id = 'SEED_V3';

    SELECT string_agg(opportunity_type || ': ' || cnt, ', ')
    INTO v_by_type
    FROM (
        SELECT opportunity_type, COUNT(*) as cnt
        FROM tb_opportunity
        GROUP BY opportunity_type
        ORDER BY cnt DESC
    ) t;

    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Additional Opportunities Added';
    RAISE NOTICE '------------------------------------------';
    RAISE NOTICE 'New records added: %', v_new_count;
    RAISE NOTICE 'Total tb_opportunity: % records', v_total;
    RAISE NOTICE 'By type: %', v_by_type;
    RAISE NOTICE '==========================================';
END $$;
