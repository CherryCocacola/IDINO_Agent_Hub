-- ============================================
-- 16. 기회(채용/인턴/공모전/장학금) 확장 데이터
-- 웹 검색 기반 실제 프로그램 참조
-- ============================================
SET search_path TO idino_career, public;

-- 기존 데이터 삭제하지 않고 추가
-- DELETE FROM tb_opportunity WHERE ins_user_id = 'SEED_V2';

-- ============================================
-- 1. 대기업 인턴십 프로그램 (20건)
-- ============================================
INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

-- 삼성전자
(gen_random_uuid(), 'internship', '2025년 삼성전자 DX부문 대학생 인턴', '삼성전자',
'삼성전자 DX부문 인턴십 프로그램. SW개발, AI/ML, 시스템소프트웨어, 보안, 디자인 분야 모집. 7-8월 중 인턴 실습 진행.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘"], "grade": [3, 4], "language": "토익 700점 이상"}',
'{"salary": "월 200만원", "certificate": true, "meal": true, "housing": false}',
'2025-03-01', '2025-04-15', '2025-07-01', '2025-08-31',
'경기도 수원시', false, 200, 'open',
'https://www.samsungcareers.com',
ARRAY['삼성', 'DX', '인턴', 'SW개발', 'AI'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 삼성전자 DS부문 반도체 인턴', '삼성전자',
'삼성전자 반도체사업부 인턴십. 메모리, 시스템LSI, 파운드리 분야 연구개발 체험.',
'{"min_gpa": 3.2, "skills": ["반도체", "전자공학"], "grade": [3, 4], "major": ["전자공학", "재료공학", "물리학"]}',
'{"salary": "월 200만원", "certificate": true, "meal": true}',
'2025-03-01', '2025-04-15', '2025-07-01', '2025-08-31',
'경기도 화성시', false, 150, 'open',
'https://www.samsungcareers.com',
ARRAY['삼성', 'DS', '반도체', '메모리'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

-- LG전자
(gen_random_uuid(), 'internship', '2025년 LG전자 인턴십 프로그램', 'LG전자',
'LG전자 하계 인턴십. SW개발, AI연구, 제품디자인, 마케팅 등 다양한 직무 체험 기회.',
'{"min_gpa": 3.0, "skills": ["SW개발", "AI"], "grade": [3, 4]}',
'{"salary": "월 180만원", "certificate": true, "meal": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 영등포구', false, 100, 'open',
'https://careers.lg.com',
ARRAY['LG', '인턴', 'SW', 'AI'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 LG CNS IT 인턴십', 'LG CNS',
'LG CNS 디지털 전환 인턴십. 클라우드, AI, 빅데이터, 시스템 통합 프로젝트 참여.',
'{"min_gpa": 3.0, "skills": ["클라우드", "빅데이터", "Java"], "grade": [3, 4]}',
'{"salary": "월 180만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 마포구', true, 80, 'open',
'https://careers.lgcns.com',
ARRAY['LG CNS', 'IT', '클라우드', '빅데이터'],
ARRAY['DEPT001'], 'SEED_V2', CURRENT_TIMESTAMP),

-- 현대자동차
(gen_random_uuid(), 'internship', '2025년 현대자동차 NextGen 인턴십', '현대자동차',
'현대자동차 차세대 인재 양성 인턴십. 연구개발, 자율주행, 전기차, 생산기술 분야.',
'{"min_gpa": 3.2, "skills": ["기계공학", "자동차"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true, "meal": true, "housing": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'경기도 화성시', false, 120, 'open',
'https://talent.hyundai.com',
ARRAY['현대', '자동차', '자율주행', '전기차'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 현대모비스 R&D 인턴', '현대모비스',
'현대모비스 연구개발 인턴십. 자율주행 센서, 전장부품, 소프트웨어 개발 분야.',
'{"min_gpa": 3.0, "skills": ["전자공학", "임베디드"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'경기도 용인시', false, 60, 'open',
'https://careers.mobis.co.kr',
ARRAY['현대모비스', 'R&D', '자율주행', '전장'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

-- SK그룹
(gen_random_uuid(), 'internship', '2025년 SK하이닉스 대학생 인턴', 'SK하이닉스',
'SK하이닉스 반도체 인턴십. 메모리 설계, 공정, 품질, AI/ML 분야 체험.',
'{"min_gpa": 3.3, "skills": ["반도체", "전자공학", "AI"], "grade": [3, 4]}',
'{"salary": "월 210만원", "certificate": true, "meal": true, "housing": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'경기도 이천시', false, 100, 'open',
'https://careers.skhynix.com',
ARRAY['SK', '하이닉스', '반도체', 'AI'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 SK텔레콤 AI/DT 인턴십', 'SK텔레콤',
'SK텔레콤 AI/디지털전환 인턴십. AI 서비스 개발, 네트워크 기술, 데이터 분석 분야.',
'{"min_gpa": 3.0, "skills": ["AI", "빅데이터", "Python"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 중구', true, 50, 'open',
'https://careers.sktelecom.com',
ARRAY['SK텔레콤', 'AI', '5G', 'DT'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

-- 카카오/네이버
(gen_random_uuid(), 'internship', '2025년 카카오 개발 인턴십', '카카오',
'카카오 소프트웨어 개발 인턴십. 백엔드, 프론트엔드, AI/ML, 데이터 엔지니어링 분야.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘", "자료구조"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true, "meal": true}',
'2025-03-01', '2025-04-20', '2025-07-01', '2025-08-31',
'경기도 성남시', true, 80, 'open',
'https://careers.kakao.com',
ARRAY['카카오', '개발', '백엔드', 'AI'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 네이버 인턴십', '네이버',
'네이버 기술 인턴십. 검색, AI, 클라우드, 커머스, 콘텐츠 플랫폼 개발.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true, "meal": true}',
'2025-03-01', '2025-04-15', '2025-07-01', '2025-08-31',
'경기도 성남시', true, 100, 'open',
'https://recruit.navercorp.com',
ARRAY['네이버', '검색', 'AI', '클라우드'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

-- 기타 대기업
(gen_random_uuid(), 'internship', '2025년 포스코 엔지니어링 인턴', '포스코',
'포스코 철강/엔지니어링 인턴십. 제철공정, 환경기술, 스마트팩토리 분야.',
'{"min_gpa": 3.0, "skills": ["기계공학", "재료공학"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true, "housing": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'경상북도 포항시', false, 60, 'open',
'https://careers.posco.co.kr',
ARRAY['포스코', '철강', '스마트팩토리'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 한화시스템 방산/ICT 인턴', '한화시스템',
'한화시스템 방산/ICT 인턴십. 항공전자, 통신, 시스템 통합 분야.',
'{"min_gpa": 3.0, "skills": ["전자공학", "통신공학"], "grade": [3, 4]}',
'{"salary": "월 190만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'경기도 용인시', false, 40, 'open',
'https://www.hanwhasystems.com',
ARRAY['한화', '방산', 'ICT', '항공'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 롯데정보통신 IT 인턴', '롯데정보통신',
'롯데정보통신 IT 인턴십. 클라우드, AI, 빅데이터, 디지털커머스 분야.',
'{"min_gpa": 3.0, "skills": ["Java", "클라우드", "빅데이터"], "grade": [3, 4]}',
'{"salary": "월 180만원", "certificate": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'서울시 송파구', true, 30, 'open',
'https://www.ldcc.co.kr',
ARRAY['롯데', 'IT', '클라우드', '빅데이터'],
ARRAY['DEPT001'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 CJ올리브네트웍스 IT 인턴', 'CJ올리브네트웍스',
'CJ그룹 IT 서비스 인턴십. 물류IT, 커머스, 데이터 분석 분야.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "데이터분석"], "grade": [3, 4]}',
'{"salary": "월 180만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 중구', true, 40, 'open',
'https://www.cjolivenetworks.co.kr',
ARRAY['CJ', 'IT', '물류', '데이터'],
ARRAY['DEPT001'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 HD현대 조선/해양 인턴', 'HD현대중공업',
'HD현대 조선/해양 엔지니어링 인턴십. 선박설계, 해양플랜트, 친환경에너지 분야.',
'{"min_gpa": 3.0, "skills": ["기계공학", "조선공학"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true, "housing": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'울산광역시', false, 50, 'open',
'https://careers.hd.com',
ARRAY['HD현대', '조선', '해양', '에너지'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 두산에너빌리티 에너지 인턴', '두산에너빌리티',
'두산에너빌리티 에너지 솔루션 인턴십. 발전설비, 수소/풍력, 스마트에너지 분야.',
'{"min_gpa": 3.0, "skills": ["기계공학", "에너지공학"], "grade": [3, 4]}',
'{"salary": "월 190만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'경상남도 창원시', false, 30, 'open',
'https://careers.doosan.com',
ARRAY['두산', '에너지', '수소', '풍력'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

-- 금융권
(gen_random_uuid(), 'internship', '2025년 KB국민은행 디지털 인턴', 'KB국민은행',
'KB국민은행 디지털/IT 인턴십. 핀테크, AI, 빅데이터 분석 분야.',
'{"min_gpa": 3.0, "skills": ["데이터분석", "Python", "AI"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 영등포구', true, 40, 'open',
'https://kbstar.recruiter.co.kr',
ARRAY['KB', '금융', 'IT', '핀테크'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 삼성SDS IT 컨설팅 인턴', '삼성SDS',
'삼성SDS IT 컨설팅/개발 인턴십. 클라우드, AI, 블록체인, 물류IT 분야.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "클라우드", "AI"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 송파구', true, 60, 'open',
'https://www.samsungsds.com',
ARRAY['삼성SDS', 'IT', '컨설팅', 'AI'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 NHN 게임/IT 인턴', 'NHN',
'NHN 게임/IT 서비스 인턴십. 게임개발, 클라우드, 결제시스템 분야.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "게임개발"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true, "meal": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'경기도 성남시', true, 30, 'open',
'https://recruit.nhn.com',
ARRAY['NHN', '게임', 'IT', '클라우드'],
ARRAY['DEPT001'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 넥슨 게임개발 인턴', '넥슨',
'넥슨 게임개발 인턴십. 게임 프로그래밍, 아트, 기획 분야.',
'{"min_gpa": 2.8, "skills": ["게임개발", "C++", "Unity"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true, "meal": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'경기도 성남시', true, 50, 'open',
'https://career.nexon.com',
ARRAY['넥슨', '게임', '개발', 'Unity'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP);

-- ============================================
-- 2. 공모전/대회 (15건)
-- ============================================
INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'contest', '제24회 대학생 프로그래밍 경시대회(ICPC)', 'ACM-ICPC Korea',
'전국 대학생 알고리즘 프로그래밍 경시대회. 3인 1팀 구성, 알고리즘 문제 해결 능력 평가.',
'{"team_size": 3, "skills": ["알고리즘", "자료구조", "C++/Java/Python"]}',
'{"prize": "대상 500만원, 금상 300만원, 은상 100만원", "certificate": true}',
'2025-08-01', '2025-09-15', '2025-10-01', '2025-10-01',
'서울 (본선)', false, 500, 'open',
'https://icpckorea.org',
ARRAY['ICPC', '프로그래밍', '알고리즘', '대회'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 DACON AI 경진대회', 'DACON',
'AI/머신러닝 데이터 분석 경진대회. 실제 비즈니스 문제 해결 도전.',
'{"skills": ["Python", "머신러닝", "데이터분석"]}',
'{"prize": "총 상금 1000만원", "certificate": true}',
'2025-03-01', '2025-05-31', '2025-03-01', '2025-06-30',
'온라인', true, null, 'open',
'https://dacon.io',
ARRAY['DACON', 'AI', '머신러닝', '데이터'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 공공데이터 활용 창업경진대회', '행정안전부',
'공공데이터를 활용한 혁신 서비스/창업 아이디어 공모전.',
'{"skills": ["데이터분석", "기획", "프로그래밍"]}',
'{"prize": "대상 3000만원, 최우수 1500만원", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-09-30',
'온라인/오프라인', true, null, 'open',
'https://www.data.go.kr',
ARRAY['공공데이터', '창업', '공모전'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 삼성 휴먼테크 논문대상', '삼성전자',
'이공계 대학원생 논문 경진대회. 전자/반도체/소프트웨어 분야.',
'{"degree": "대학원생", "skills": ["연구", "논문작성"]}',
'{"prize": "금상 2000만원, 은상 1000만원", "certificate": true}',
'2025-09-01', '2025-11-30', '2026-01-01', '2026-02-28',
'서울', false, null, 'open',
'https://humantech.samsung.com',
ARRAY['삼성', '논문', '연구', '이공계'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 네이버 AI 해커톤', '네이버',
'AI 기술을 활용한 혁신 서비스 개발 해커톤. 2박 3일 집중 개발.',
'{"skills": ["AI", "프로그래밍", "기획"]}',
'{"prize": "대상 1000만원, 우수상 500만원", "certificate": true, "채용연계": true}',
'2025-05-01', '2025-06-15', '2025-07-01', '2025-07-03',
'경기도 성남시', false, 100, 'open',
'https://recruit.navercorp.com',
ARRAY['네이버', 'AI', '해커톤'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 카카오 브레인 AI 챌린지', '카카오브레인',
'자연어처리/컴퓨터비전 AI 알고리즘 경진대회.',
'{"skills": ["딥러닝", "NLP", "컴퓨터비전", "Python"]}',
'{"prize": "총 상금 5000만원", "certificate": true, "채용우대": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-08-31',
'온라인', true, null, 'open',
'https://www.kakaobrain.com',
ARRAY['카카오', 'AI', '딥러닝', 'NLP'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 LG Aimers AI 경진대회', 'LG AI연구원',
'LG AI 교육 프로그램 수료자 대상 AI 프로젝트 경진대회.',
'{"skills": ["AI", "머신러닝", "Python"]}',
'{"prize": "총 상금 3000만원", "certificate": true, "교육제공": true}',
'2025-03-01', '2025-05-31', '2025-03-01', '2025-07-31',
'온라인', true, 500, 'open',
'https://www.lgaimers.ai',
ARRAY['LG', 'AI', '머신러닝', '교육'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 SK ICT Tech Summit', 'SK그룹',
'SK그룹 ICT 기술 경진대회. AI, 클라우드, 빅데이터, 메타버스 분야.',
'{"skills": ["AI", "클라우드", "빅데이터"]}',
'{"prize": "대상 2000만원", "certificate": true, "채용연계": true}',
'2025-06-01', '2025-08-31', '2025-06-01', '2025-10-31',
'서울', false, null, 'open',
'https://www.sktechsummit.com',
ARRAY['SK', 'ICT', 'AI', '클라우드'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 여성가족부 AI 데이터 공모전', '여성가족부',
'AI/데이터 융복합 아이디어 및 분석활용 공모전.',
'{"skills": ["데이터분석", "AI", "기획"]}',
'{"prize": "총 상금 2000만원", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-08-31',
'온라인', true, null, 'open',
'https://mogefdatacontest.co.kr',
ARRAY['공모전', 'AI', '데이터', '정부'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 강서구 빅데이터 분석 공모전', '서울 강서구',
'공공 빅데이터 분석 아이디어 공모전. 개인 또는 4인 이내 팀.',
'{"team_size": 4, "skills": ["빅데이터", "데이터분석"]}',
'{"prize": "대상 150만원, 최우수 100만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-09-30',
'온라인', true, null, 'open',
'https://www.gangseo.seoul.kr',
ARRAY['빅데이터', '공모전', '공공데이터'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 새만금 공공데이터 활용 경진대회', '새만금개발청',
'새만금 지역 발전을 위한 공공데이터 활용 아이디어 경진대회.',
'{"skills": ["데이터분석", "기획", "시각화"]}',
'{"prize": "총 상금 1500만원", "certificate": true}',
'2025-05-19', '2025-07-31', '2025-05-19', '2025-10-31',
'온라인/새만금', true, null, 'open',
'https://www.saemangeum.go.kr',
ARRAY['새만금', '공공데이터', '경진대회'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 현대자동차 H-모빌리티 클래스', '현대자동차',
'미래 모빌리티 아이디어 공모전. 자율주행, 전기차, UAM 분야.',
'{"skills": ["기획", "자동차", "모빌리티"]}',
'{"prize": "대상 1000만원", "certificate": true, "채용우대": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-09-30',
'서울', false, null, 'open',
'https://talent.hyundai.com',
ARRAY['현대', '모빌리티', '자율주행', '전기차'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 포스코 스마트팩토리 아이디어 공모전', '포스코',
'제철/제조 분야 스마트팩토리 혁신 아이디어 공모전.',
'{"skills": ["AI", "IoT", "스마트팩토리", "기획"]}',
'{"prize": "대상 500만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-10-31',
'온라인/포항', true, null, 'open',
'https://careers.posco.co.kr',
ARRAY['포스코', '스마트팩토리', 'AI', 'IoT'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 한국전력 에너지 AI 경진대회', '한국전력공사',
'에너지 분야 AI/빅데이터 활용 문제 해결 경진대회.',
'{"skills": ["AI", "빅데이터", "에너지"]}',
'{"prize": "총 상금 3000만원", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-09-30',
'온라인', true, null, 'open',
'https://www.kepco.co.kr',
ARRAY['한전', '에너지', 'AI', '빅데이터'],
ARRAY['DEPT001', 'DEPT003'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 금융데이터거래소 데이터 분석 경진대회', '금융데이터거래소',
'금융 데이터를 활용한 분석 및 서비스 아이디어 공모전.',
'{"skills": ["데이터분석", "금융", "Python"]}',
'{"prize": "대상 1000만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-10-31',
'온라인', true, null, 'open',
'https://www.findatamall.or.kr',
ARRAY['금융', '데이터', '분석', '공모전'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP);

-- ============================================
-- 3. 장학금 프로그램 (10건)
-- ============================================
INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'scholarship', '2025 국가우수장학금(이공계) 성적우수', '한국장학재단',
'이공계 우수 인재 양성을 위한 국가장학금. 졸업시까지 등록금 전액 지원.',
'{"min_gpa": 3.3, "major": ["자연과학", "공학"], "grade": [1]}',
'{"amount": "등록금 전액", "duration": "졸업시까지"}',
'2025-02-01', '2025-03-31', '2025-03-01', '2029-02-28',
'전국', true, 1000, 'open',
'https://www.kosaf.go.kr',
ARRAY['국가장학금', '이공계', '등록금'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 국가우수장학금(이공계) 2년지원', '한국장학재단',
'이공계 3학년 대상 2년간 장학금 지원. 대학 추천 필요.',
'{"min_gpa": 3.3, "major": ["자연과학", "공학"], "grade": [3]}',
'{"amount": "등록금 전액", "duration": "2년"}',
'2025-02-01', '2025-04-24', '2025-03-01', '2027-02-28',
'전국', true, 500, 'open',
'https://www.kosaf.go.kr',
ARRAY['국가장학금', '이공계', '2년지원'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 이공계 석사우수장학금', '한국장학재단',
'이공계 석사과정 대상 장학금. 연간 500만원 지원.',
'{"degree": "석사", "major": ["자연과학", "공학"]}',
'{"amount": "연 500만원", "duration": "석사과정"}',
'2025-06-01', '2025-08-31', '2025-09-01', '2027-08-31',
'전국', true, 1000, 'open',
'https://www.kosaf.go.kr',
ARRAY['국가장학금', '이공계', '석사'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 삼성 꿈장학재단 장학생', '삼성꿈장학재단',
'삼성 사회공헌 장학금. 저소득층 이공계 대학생 대상.',
'{"min_gpa": 3.0, "income": "저소득층", "major": ["이공계"]}',
'{"amount": "연 500만원", "duration": "졸업시까지", "mentoring": true}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 200, 'open',
'https://www.sdream.or.kr',
ARRAY['삼성', '장학금', '이공계'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 SK 행복나눔재단 장학금', 'SK행복나눔재단',
'SK그룹 사회공헌 장학금. 이공계 우수 인재 양성.',
'{"min_gpa": 3.2, "major": ["이공계"]}',
'{"amount": "연 600만원", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 100, 'open',
'https://www.skhappiness.org',
ARRAY['SK', '장학금', '이공계'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 현대차 정몽구재단 장학금', '현대차 정몽구재단',
'현대자동차그룹 장학금. 이공계 및 인문계 우수 학생 대상.',
'{"min_gpa": 3.5}',
'{"amount": "연 800만원", "duration": "졸업시까지", "해외연수": true}',
'2025-03-01', '2025-05-31', '2025-03-01', '2029-02-28',
'전국', true, 150, 'open',
'https://www.hyundai-cmkfoundation.org',
ARRAY['현대', '장학금', '장학재단'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 포스코청암재단 장학금', '포스코청암재단',
'포스코 장학금. 이공계 우수 학생 대상 등록금 및 생활비 지원.',
'{"min_gpa": 3.3, "major": ["이공계"]}',
'{"amount": "등록금+생활비", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 100, 'open',
'https://www.postf.org',
ARRAY['포스코', '장학금', '이공계'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 LG연암문화재단 해외연수장학금', 'LG연암문화재단',
'LG 해외 연수 장학금. 이공계 대학원생 해외 연구 지원.',
'{"degree": "대학원생", "min_gpa": 3.5, "language": "영어 능통"}',
'{"amount": "연수비 전액", "duration": "6개월~1년"}',
'2025-03-01', '2025-05-31', '2025-09-01', '2026-08-31',
'해외', false, 50, 'open',
'https://www.lgfoundation.org',
ARRAY['LG', '해외연수', '장학금'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 관정 이종환 교육재단 장학금', '관정 이종환 교육재단',
'국내외 대학(원)생 장학금. 성적 및 봉사활동 우수자.',
'{"min_gpa": 3.5}',
'{"amount": "등록금 전액", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 200, 'open',
'https://www.ikef.or.kr',
ARRAY['관정', '장학금', '등록금'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025 하이브 드림장학재단 장학금', '하이브',
'하이브 장학금. 문화/예술/기술 분야 우수 인재 지원.',
'{"min_gpa": 3.0}',
'{"amount": "연 500만원", "duration": "졸업시까지"}',
'2025-03-01', '2025-05-31', '2025-03-01', '2029-02-28',
'전국', true, 50, 'open',
'https://hybecorp.com',
ARRAY['하이브', '장학금', '문화'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP);

-- ============================================
-- 4. 연구/프로젝트 기회 (10건)
-- ============================================
INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'lab', '2025 ETRI 대학생 연구연수생', '한국전자통신연구원',
'ETRI 연구실 연수 프로그램. AI, 통신, 반도체 분야 연구 참여.',
'{"min_gpa": 3.0, "grade": [3, 4], "major": ["전자", "컴퓨터", "통신"]}',
'{"salary": "월 150만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'대전광역시', false, 100, 'open',
'https://www.etri.re.kr',
ARRAY['ETRI', '연구', 'AI', '통신'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 KAIST 학부연구생 프로그램', 'KAIST',
'KAIST 연구실 학부연구생 프로그램. 다양한 이공계 분야 연구 경험.',
'{"min_gpa": 3.5, "grade": [3, 4]}',
'{"salary": "월 100만원", "certificate": true}',
'2025-02-01', '2025-03-31', '2025-03-01', '2025-08-31',
'대전광역시', false, 200, 'open',
'https://www.kaist.ac.kr',
ARRAY['KAIST', '연구', '학부연구생'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 SW마에스트로 과정', '과학기술정보통신부',
'SW 인재 양성 프로그램. 멘토링, 프로젝트 수행, 해외연수 지원.',
'{"skills": ["프로그래밍", "알고리즘"], "grade": [2, 3, 4]}',
'{"salary": "월 100만원", "교육비": "전액지원", "해외연수": true}',
'2025-02-01', '2025-04-30', '2025-06-01', '2025-11-30',
'서울', false, 200, 'open',
'https://www.swmaestro.org',
ARRAY['SW마에스트로', 'SW', '인재양성'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 K-디지털 트레이닝', '고용노동부',
'디지털 분야 취업연계 교육 프로그램. AI, 클라우드, 빅데이터 과정.',
'{"grade": [4], "취업희망자": true}',
'{"교육비": "전액무료", "취업연계": true}',
'2025-01-01', '2025-12-31', '2025-03-01', '2025-12-31',
'전국', true, 5000, 'open',
'https://www.hrd.go.kr',
ARRAY['K디지털', 'AI', '취업연계'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 KIST 학생연구원', '한국과학기술연구원',
'KIST 연구실 학생연구원 프로그램. 첨단 과학기술 분야 연구 참여.',
'{"min_gpa": 3.3, "grade": [3, 4], "major": ["이공계"]}',
'{"salary": "월 120만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'서울특별시', false, 80, 'open',
'https://www.kist.re.kr',
ARRAY['KIST', '연구', '과학기술'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 부스트캠프 AI Tech', '네이버커넥트재단',
'AI 엔지니어 양성 교육 프로그램. 6개월 집중 교육.',
'{"skills": ["Python", "수학"], "grade": [3, 4, "졸업자"]}',
'{"교육비": "전액무료", "취업연계": true, "장비대여": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-12-31',
'온라인', true, 200, 'open',
'https://boostcamp.connect.or.kr',
ARRAY['부스트캠프', 'AI', '네이버'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 우아한테크코스', '우아한형제들',
'배달의민족 개발자 양성 프로그램. 10개월 교육 후 채용연계.',
'{"skills": ["프로그래밍", "Java"], "grade": [3, 4, "졸업자"]}',
'{"교육비": "전액무료", "채용연계": true}',
'2025-10-01', '2025-11-30', '2026-02-01', '2026-11-30',
'서울', false, 100, 'open',
'https://woowacourse.github.io',
ARRAY['우아한테크코스', '배달의민족', '개발자'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 국립암센터 연구연수생', '국립암센터',
'암 연구 분야 학생연구원. 의생명과학 연구 참여 기회.',
'{"major": ["생명과학", "의공학", "화학"], "grade": [3, 4]}',
'{"salary": "월 100만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'경기도 고양시', false, 30, 'open',
'https://www.ncc.re.kr',
ARRAY['국립암센터', '연구', '의생명'],
ARRAY['DEPT002', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'project', '2025 SSAFY (삼성 청년 SW 아카데미)', '삼성전자',
'삼성 SW 인재 양성 프로그램. 1년 교육 후 취업 지원.',
'{"grade": [4, "졸업자"], "취업희망자": true}',
'{"교육비": "전액무료", "월지원금": "100만원", "취업연계": true}',
'2025-05-01', '2025-06-30', '2025-07-01', '2026-06-30',
'전국 5개 캠퍼스', false, 1500, 'open',
'https://www.ssafy.com',
ARRAY['SSAFY', '삼성', 'SW', '취업연계'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'lab', '2025 한국원자력연구원 인턴', '한국원자력연구원',
'원자력/방사선 분야 연구 인턴십. 원자력공학 연구 경험.',
'{"major": ["원자력공학", "기계공학", "화학공학"], "grade": [3, 4]}',
'{"salary": "월 130만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'대전광역시', false, 40, 'open',
'https://www.kaeri.re.kr',
ARRAY['원자력연구원', '연구', '원자력'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP);

-- ============================================
-- 5. 신입 채용 공고 (5건)
-- ============================================
INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'job', '2025 삼성전자 3급 신입사원 공채', '삼성전자',
'삼성전자 하반기 공채. 연구개발, 경영지원, 영업마케팅 등 전 직군.',
'{"degree": "학사 이상", "language": "토익 700점 이상"}',
'{"연봉": "5000만원~", "복리후생": "삼성 복지"}',
'2025-08-27', '2025-09-03', '2025-12-01', null,
'전국', false, 3000, 'open',
'https://www.samsungcareers.com',
ARRAY['삼성', '공채', '신입'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'job', '2025 현대자동차 신입사원 채용', '현대자동차',
'현대자동차 하반기 신입 채용. 연구개발, 생산기술, 영업 등.',
'{"degree": "학사 이상"}',
'{"연봉": "5500만원~", "복리후생": "현대차 복지"}',
'2025-09-01', '2025-10-15', '2026-01-01', null,
'전국', false, 2000, 'open',
'https://talent.hyundai.com',
ARRAY['현대', '자동차', '공채', '신입'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'job', '2025 LG그룹 신입사원 공채', 'LG그룹',
'LG그룹 계열사 통합 공채. LG전자, LG화학, LG에너지솔루션 등.',
'{"degree": "학사 이상"}',
'{"연봉": "4800만원~", "복리후생": "LG 복지"}',
'2025-09-01', '2025-09-30', '2026-01-01', null,
'전국', false, 2500, 'open',
'https://careers.lg.com',
ARRAY['LG', '공채', '신입'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'job', '2025 SK그룹 신입사원 채용', 'SK그룹',
'SK그룹 SKCT 기반 통합 채용. SK하이닉스, SK텔레콤 등.',
'{"degree": "학사 이상"}',
'{"연봉": "5000만원~", "복리후생": "SK 복지"}',
'2025-09-15', '2025-10-15', '2026-01-01', null,
'전국', false, 1500, 'open',
'https://www.skcareers.com',
ARRAY['SK', '공채', '신입'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003', 'DEPT004'], 'SEED_V2', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'job', '2025 네이버/카카오 개발자 상시채용', '네이버/카카오',
'IT 플랫폼 기업 개발자 상시 채용. 백엔드, 프론트엔드, AI 등.',
'{"skills": ["프로그래밍", "알고리즘"], "degree": "학사 이상"}',
'{"연봉": "5500만원~", "스톡옵션": true}',
'2025-01-01', '2025-12-31', '2025-01-01', null,
'경기도 성남시', true, null, 'open',
'https://recruit.navercorp.com',
ARRAY['네이버', '카카오', '개발자', '상시'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V2', CURRENT_TIMESTAMP);

-- ============================================
-- 결과 확인
-- ============================================
DO $$
DECLARE
    v_total INT;
    v_internship INT;
    v_contest INT;
    v_scholarship INT;
    v_lab INT;
    v_project INT;
    v_job INT;
BEGIN
    SELECT COUNT(*) INTO v_total FROM tb_opportunity;
    SELECT COUNT(*) INTO v_internship FROM tb_opportunity WHERE opportunity_type = 'internship';
    SELECT COUNT(*) INTO v_contest FROM tb_opportunity WHERE opportunity_type = 'contest';
    SELECT COUNT(*) INTO v_scholarship FROM tb_opportunity WHERE opportunity_type = 'scholarship';
    SELECT COUNT(*) INTO v_lab FROM tb_opportunity WHERE opportunity_type = 'lab';
    SELECT COUNT(*) INTO v_project FROM tb_opportunity WHERE opportunity_type = 'project';
    SELECT COUNT(*) INTO v_job FROM tb_opportunity WHERE opportunity_type = 'job';

    RAISE NOTICE '==========================================';
    RAISE NOTICE 'tb_opportunity 데이터 현황';
    RAISE NOTICE '------------------------------------------';
    RAISE NOTICE '전체: % 건', v_total;
    RAISE NOTICE '인턴십: % 건', v_internship;
    RAISE NOTICE '공모전: % 건', v_contest;
    RAISE NOTICE '장학금: % 건', v_scholarship;
    RAISE NOTICE '연구실: % 건', v_lab;
    RAISE NOTICE '프로젝트: % 건', v_project;
    RAISE NOTICE '채용: % 건', v_job;
    RAISE NOTICE '==========================================';
END $$;
