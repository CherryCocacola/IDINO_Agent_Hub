-- ============================================
-- IDINO Career - Additional Opportunities V4 (55+ more)
-- Date: 2026-01-26
-- Based on 2025 real program web search results
-- ============================================

SET search_path TO idino_career;

-- ============================================
-- 1. Additional Internship Programs (18건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

-- 대기업 인턴십
(gen_random_uuid(), 'internship', '2025년 현대자동차 채용연계형 인턴', '현대자동차',
'현대자동차 연구개발/생산기술/경영지원 인턴십. 6개월 인턴 후 정규직 전환 기회.',
'{"min_gpa": 3.0, "skills": ["전공지식", "영어"], "grade": [3, 4]}',
'{"salary": "월 280만원", "certificate": true, "conversion": "정규직 전환 가능"}',
'2025-03-01', '2025-04-15', '2025-07-01', '2025-12-31',
'경기도 화성시', false, 200, 'open',
'https://talent.hyundai.com',
ARRAY['현대자동차', '자동차', '연구개발', '채용연계'],
ARRAY['DEPT003', 'DEPT004', 'DEPT006'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 기아 글로벌 인턴십', '기아',
'기아 글로벌 사업 인턴십. 해외사업, 마케팅, 디자인 분야.',
'{"min_gpa": 3.2, "skills": ["영어", "제2외국어"], "grade": [3, 4]}',
'{"salary": "월 260만원", "certificate": true, "overseas": "해외 출장 기회"}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 서초구', false, 80, 'open',
'https://careers.kia.com',
ARRAY['기아', '글로벌', '마케팅', '디자인'],
ARRAY['DEPT014', 'DEPT025'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 포스코 인턴십 프로그램', '포스코',
'포스코 철강/에너지 기술 인턴십. 설비기술, 공정관리, 연구개발.',
'{"min_gpa": 3.0, "major": ["재료공학", "기계공학", "화학공학"], "grade": [3, 4]}',
'{"salary": "월 230만원", "certificate": true, "housing": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'경상북도 포항시', false, 100, 'open',
'https://www.posco.com',
ARRAY['포스코', '철강', '에너지', '연구개발'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 HD현대 조선해양 인턴', 'HD현대중공업',
'HD현대 조선해양 기술 인턴십. 선박설계, 해양플랜트, 엔진 개발.',
'{"min_gpa": 3.0, "major": ["조선해양", "기계공학"], "grade": [3, 4]}',
'{"salary": "월 240만원", "certificate": true, "housing": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'울산광역시', false, 80, 'open',
'https://www.hd-hhi.co.kr',
ARRAY['HD현대', '조선', '해양', '엔지니어링'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 한화에어로스페이스 인턴', '한화에어로스페이스',
'한화에어로스페이스 항공/방산 인턴십. 항공엔진, 우주발사체, 방산기술.',
'{"min_gpa": 3.2, "major": ["기계공학", "항공우주공학"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'경상남도 창원시', false, 60, 'open',
'https://www.hanwhaaerospace.co.kr',
ARRAY['한화', '항공', '우주', '방산'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V4', CURRENT_TIMESTAMP),

-- IT 스타트업
(gen_random_uuid(), 'internship', '2025년 직방 Tech 인턴십', '직방',
'직방 부동산 플랫폼 개발 인턴십. 백엔드, 프론트엔드, 데이터.',
'{"min_gpa": 3.0, "skills": ["Python", "JavaScript", "SQL"], "grade": [3, 4]}',
'{"salary": "월 230만원", "certificate": true, "remote": "주3일 재택"}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 강남구', true, 30, 'open',
'https://career.zigbang.com',
ARRAY['직방', '부동산', '프롭테크', '개발'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 야놀자 Engineering 인턴', '야놀자',
'야놀자 여행/숙박 플랫폼 개발 인턴십. 서버, 앱, AI/ML.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "알고리즘"], "grade": [3, 4]}',
'{"salary": "월 260만원", "certificate": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'서울시 강남구', true, 40, 'open',
'https://careers.yanolja.com',
ARRAY['야놀자', '여행', '숙박', 'Tech'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 무신사 Tech 인턴십', '무신사',
'무신사 패션 이커머스 개발 인턴십. 웹/앱, 데이터, 인프라.',
'{"min_gpa": 3.0, "skills": ["Python", "React", "Kotlin"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 강남구', true, 35, 'open',
'https://corp.musinsa.com',
ARRAY['무신사', '패션', '이커머스', 'Tech'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

-- 금융/핀테크
(gen_random_uuid(), 'internship', '2025년 KB국민은행 IT 인턴', 'KB국민은행',
'KB국민은행 디지털/IT 인턴십. AI, 빅데이터, 핀테크 서비스.',
'{"min_gpa": 3.0, "skills": ["데이터분석", "프로그래밍"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'서울시 영등포구', true, 50, 'open',
'https://kbstar.com',
ARRAY['KB국민은행', '금융', 'IT', '핀테크'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 NH농협은행 디지털 인턴', 'NH농협은행',
'NH농협은행 디지털 금융 인턴십. AI 챗봇, 모바일뱅킹, 데이터.',
'{"min_gpa": 3.0, "skills": ["프로그래밍", "데이터분석"], "grade": [3, 4]}',
'{"salary": "월 200만원", "certificate": true}',
'2025-04-01', '2025-05-20', '2025-07-01', '2025-08-31',
'서울시 중구', true, 40, 'open',
'https://www.nhbank.com',
ARRAY['NH농협', '금융', '디지털', '데이터'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 하나금융그룹 IT 인턴', '하나금융그룹',
'하나금융 IT/디지털 인턴십. 핀테크, 블록체인, AI.',
'{"min_gpa": 3.2, "skills": ["프로그래밍", "금융지식"], "grade": [3, 4]}',
'{"salary": "월 230만원", "certificate": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'서울시 중구', true, 45, 'open',
'https://www.hanafn.com',
ARRAY['하나금융', '금융', 'IT', '블록체인'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

-- 제조/바이오
(gen_random_uuid(), 'internship', '2025년 셀트리온 연구개발 인턴', '셀트리온',
'셀트리온 바이오의약품 연구개발 인턴십. 세포배양, 정제, 분석.',
'{"min_gpa": 3.3, "major": ["생명공학", "화학공학", "약학"], "grade": [3, 4]}',
'{"salary": "월 220만원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-01', '2025-08-31',
'인천광역시 연수구', false, 40, 'open',
'https://www.celltrion.com',
ARRAY['셀트리온', '바이오', '제약', '연구개발'],
ARRAY['DEPT003'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 삼성바이오로직스 인턴', '삼성바이오로직스',
'삼성바이오 CMO 생산기술 인턴십. 바이오의약품 생산, 품질관리.',
'{"min_gpa": 3.0, "major": ["생명공학", "화학공학"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true}',
'2025-04-01', '2025-05-30', '2025-07-01', '2025-08-31',
'인천광역시 연수구', false, 60, 'open',
'https://www.samsungbiologics.com',
ARRAY['삼성바이오', '바이오', 'CMO', '제약'],
ARRAY['DEPT003'], 'SEED_V4', CURRENT_TIMESTAMP),

-- 미디어/콘텐츠
(gen_random_uuid(), 'internship', '2025년 CJ ENM 미디어/Tech 인턴', 'CJ ENM',
'CJ ENM 콘텐츠/기술 인턴십. 영상 AI, 스트리밍, 콘텐츠 기획.',
'{"min_gpa": 3.0, "skills": ["영상편집", "프로그래밍"], "grade": [3, 4]}',
'{"salary": "월 230만원", "certificate": true}',
'2025-04-01', '2025-05-15', '2025-07-01', '2025-08-31',
'서울시 마포구', true, 50, 'open',
'https://www.cjenm.com',
ARRAY['CJ ENM', '미디어', '콘텐츠', 'Tech'],
ARRAY['DEPT001', 'DEPT025'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 하이브 Tech 인턴십', '하이브',
'하이브 엔터테인먼트 기술 인턴십. 팬 플랫폼, AI, 데이터 분석.',
'{"min_gpa": 3.0, "skills": ["Python", "데이터분석"], "grade": [3, 4]}',
'{"salary": "월 250만원", "certificate": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'서울시 용산구', true, 30, 'open',
'https://careers.hybe.com',
ARRAY['하이브', 'K-POP', '엔터테인먼트', 'Tech'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

-- 글로벌 기업 한국지사
(gen_random_uuid(), 'internship', '2025년 마이크로소프트 코리아 인턴', 'Microsoft Korea',
'MS 코리아 기술영업/마케팅 인턴십. Azure, AI 솔루션 사업.',
'{"min_gpa": 3.3, "skills": ["영어", "클라우드", "프레젠테이션"], "grade": [3, 4]}',
'{"salary": "월 300만원", "certificate": true}',
'2025-03-01', '2025-04-15', '2025-07-01', '2025-12-31',
'서울시 종로구', true, 30, 'open',
'https://careers.microsoft.com',
ARRAY['Microsoft', '클라우드', 'Azure', '글로벌'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 구글 코리아 STEP 인턴', 'Google Korea',
'구글 코리아 엔지니어링 인턴십 (STEP). 소프트웨어 개발.',
'{"min_gpa": 3.5, "skills": ["알고리즘", "자료구조", "영어"], "grade": [2, 3]}',
'{"salary": "월 350만원", "certificate": true}',
'2025-02-01', '2025-03-31', '2025-06-01', '2025-08-31',
'서울시 강남구', true, 20, 'open',
'https://careers.google.com',
ARRAY['Google', 'STEP', '소프트웨어', '글로벌'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'internship', '2025년 아마존 AWS 인턴', 'Amazon Web Services',
'AWS 코리아 솔루션 아키텍트 인턴십. 클라우드 기술 지원.',
'{"min_gpa": 3.3, "skills": ["클라우드", "Linux", "Python"], "grade": [3, 4]}',
'{"salary": "월 320만원", "certificate": true}',
'2025-03-01', '2025-04-30', '2025-07-01', '2025-08-31',
'서울시 강남구', true, 25, 'open',
'https://www.amazon.jobs',
ARRAY['AWS', 'Amazon', '클라우드', '글로벌'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP);

-- ============================================
-- 2. Additional Contest/Competition (15건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'contest', '2025 삼성 Collegiate Programming Challenge', '삼성전자',
'삼성 알고리즘 프로그래밍 경진대회. 총 상금 6,000만원.',
'{"skills": ["알고리즘", "C++", "Python"]}',
'{"prize": "대상 2,000만원", "certificate": true, "채용우대": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-09-30',
'온라인/서울', true, null, 'open',
'https://dacon.io',
ARRAY['삼성', 'SCPC', '알고리즘', '프로그래밍'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 DACON 한솔테코 건설안전 AI 경진대회', 'DACON/한솔테코',
'건설현장 사고 예방 AI 모델 개발 경진대회.',
'{"skills": ["Python", "딥러닝", "컴퓨터비전"]}',
'{"prize": "총 상금 3,000만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-08-31',
'온라인', true, null, 'open',
'https://dacon.io',
ARRAY['DACON', '한솔테코', 'AI', '안전'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 KISTI DATA·AI 분석 경진대회', 'KISTI',
'KISTI AI 데이터 분석 경진대회. 과학기술 데이터 활용.',
'{"skills": ["데이터분석", "Python", "머신러닝"]}',
'{"prize": "총 상금 2,000만원", "certificate": true}',
'2025-06-01', '2025-08-31', '2025-06-01', '2025-10-31',
'온라인', true, null, 'open',
'https://aida.kisti.re.kr',
ARRAY['KISTI', '데이터', 'AI', '분석'],
ARRAY['DEPT001', 'DEPT013'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 SW마에스트로 프롬프트 엔지니어링 대회', 'SW마에스트로',
'LLM 프롬프트 엔지니어링 경진대회. GPT, Claude 활용.',
'{"skills": ["LLM", "프롬프트엔지니어링", "Python"]}',
'{"prize": "총 상금 1,500만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-09-30',
'온라인', true, null, 'open',
'https://swmaestro.org',
ARRAY['SW마에스트로', 'LLM', '프롬프트', 'AI'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 Tech-GPT 서비스 경진대회', '산업통상자원부',
'DATA·AI 융합 신사업 아이디어 공모전.',
'{"skills": ["AI", "기획", "프레젠테이션"]}',
'{"prize": "대상 3,000만원 창업지원금", "certificate": true}',
'2025-10-01', '2025-10-24', '2025-10-01', '2025-12-31',
'온라인/서울', true, null, 'open',
'https://tech-gpt.ai',
ARRAY['산업부', 'Tech-GPT', 'AI', '창업'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 LG AI 해커톤', 'LG CNS',
'LG AI 솔루션 해커톤. 48시간 집중 개발.',
'{"skills": ["AI", "머신러닝", "프로그래밍"]}',
'{"prize": "대상 1,000만원", "certificate": true, "채용연계": true}',
'2025-05-01', '2025-06-30', '2025-08-01', '2025-08-03',
'서울시 마포구', false, 100, 'open',
'https://www.lgcns.com',
ARRAY['LG', 'AI', '해커톤', 'CNS'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 정보올림피아드 대학부', '한국정보올림피아드',
'전국 대학생 프로그래밍 경시대회.',
'{"skills": ["알고리즘", "자료구조", "프로그래밍"]}',
'{"prize": "금상 500만원", "certificate": true, "병역특례": "병역특례 가점"}',
'2025-04-01', '2025-05-31', '2025-06-01', '2025-09-30',
'전국', false, null, 'open',
'https://www.koi.or.kr',
ARRAY['정보올림피아드', '알고리즘', '프로그래밍'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 ACM-ICPC 아시아 서울 리저널', 'ACM',
'국제 대학생 프로그래밍 대회. 팀 3명 구성.',
'{"team_size": 3, "skills": ["알고리즘", "C++", "협업"]}',
'{"prize": "월드 파이널 진출권", "certificate": true}',
'2025-08-01', '2025-09-30', '2025-11-01', '2025-11-03',
'서울', false, null, 'open',
'https://icpc.global',
ARRAY['ICPC', 'ACM', '프로그래밍', '글로벌'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 산림분야 빅데이터·AI 창업 경진대회', '산림청',
'산림 데이터 활용 AI 솔루션 공모전.',
'{"skills": ["빅데이터", "AI", "창업기획"]}',
'{"prize": "대상 2,000만원", "certificate": true, "창업지원": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-10-31',
'온라인', true, null, 'open',
'https://www.data.go.kr',
ARRAY['산림청', '빅데이터', 'AI', '창업'],
ARRAY['DEPT001', 'DEPT013'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 문화 디지털혁신 데이터 활용 공모전', '문화체육관광부',
'문화 데이터 활용 디지털 서비스 아이디어 공모.',
'{"skills": ["데이터분석", "기획", "디자인"]}',
'{"prize": "대상 1,500만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-10-31',
'온라인', true, null, 'open',
'https://www.mcst.go.kr',
ARRAY['문화부', '디지털혁신', '데이터', '문화'],
ARRAY['DEPT001', 'DEPT025'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 공공데이터 활용 창업경진대회', '행정안전부',
'공공데이터 기반 스타트업 아이디어 공모전.',
'{"skills": ["데이터분석", "기획", "프레젠테이션"]}',
'{"prize": "대상 3,000만원 창업지원금", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-04-01', '2025-11-30',
'전국', true, null, 'open',
'https://www.data.go.kr',
ARRAY['행안부', '공공데이터', '창업', '스타트업'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 병무청/방위사업청/질병관리청 데이터 공모전', '병무청',
'3청 합동 데이터 분석 및 아이디어 공모전.',
'{"skills": ["데이터분석", "시각화", "기획"]}',
'{"prize": "대상 1,000만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-09-30',
'온라인', true, null, 'open',
'https://www.data.go.kr',
ARRAY['병무청', '데이터', '공공', '분석'],
ARRAY['DEPT001', 'DEPT013'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 Junction Asia 해커톤', 'Junction',
'아시아 최대 해커톤. 48시간 글로벌 팀 프로젝트.',
'{"skills": ["프로그래밍", "디자인", "기획"]}',
'{"prize": "대상 $10,000", "certificate": true, "네트워킹": true}',
'2025-06-01', '2025-07-31', '2025-08-15', '2025-08-17',
'서울시 강남구', false, 500, 'open',
'https://asia.junction2025.com',
ARRAY['Junction', '해커톤', '글로벌', '스타트업'],
ARRAY['DEPT001', 'DEPT002', 'DEPT025'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 코리아 스타트업 서밋 피칭 대회', '창업진흥원',
'대학생 스타트업 피칭 경진대회.',
'{"skills": ["기획", "피칭", "사업계획"]}',
'{"prize": "대상 5,000만원 투자유치", "certificate": true, "멘토링": true}',
'2025-05-01', '2025-07-31', '2025-09-01', '2025-09-03',
'서울시 강남구', false, 100, 'open',
'https://www.kised.or.kr',
ARRAY['창업진흥원', '스타트업', '피칭', '투자'],
ARRAY['DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'contest', '2025 로봇AI 융합 공모전', '한국로봇산업진흥원',
'로봇+AI 융합 기술 솔루션 공모전.',
'{"skills": ["로봇공학", "AI", "프로그래밍"]}',
'{"prize": "대상 2,000만원", "certificate": true}',
'2025-05-01', '2025-07-31', '2025-05-01', '2025-10-31',
'온라인/대구', true, null, 'open',
'https://www.kiria.org',
ARRAY['로봇', 'AI', '융합', '기술'],
ARRAY['DEPT001', 'DEPT003', 'DEPT004'], 'SEED_V4', CURRENT_TIMESTAMP);

-- ============================================
-- 3. Additional Volunteer Programs (8건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'volunteer', '2025년 KOICA WFK 청년봉사단', 'KOICA',
'KOICA 해외봉사단. 개발도상국 교육, 보건, IT 분야 봉사.',
'{"age": "만 20-35세", "health": "건강한 자", "language": "영어 가능자"}',
'{"지원금": "월 생활비 지원", "certificate": true, "경력인정": "공무원 경력 인정"}',
'2025-02-01', '2025-04-30', '2025-07-01', '2027-06-30',
'해외 30개국', false, 500, 'open',
'https://www.koica.go.kr',
ARRAY['KOICA', '해외봉사', '글로벌', '공적개발원조'],
ARRAY['DEPT001', 'DEPT002', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 KT&G 상상위더스 해외봉사단', 'KT&G복지재단',
'인도네시아 대학생 해외봉사단. 아동교육, 환경개선.',
'{"grade": [1, 2, 3, 4], "health": "건강한 자"}',
'{"지원금": "참가비 전액지원", "certificate": true}',
'2025-04-01', '2025-05-31', '2025-07-12', '2025-07-21',
'인도네시아', false, 30, 'open',
'https://www.ktngwelfare.org',
ARRAY['KT&G', '해외봉사', '인도네시아', '아동교육'],
ARRAY['DEPT001', 'DEPT002', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 LS 대학생 해외봉사단', 'LS그룹',
'LS그룹 해외봉사단. 베트남/인도네시아 IT교육, 시설개선.',
'{"min_gpa": 3.0, "grade": [2, 3, 4]}',
'{"지원금": "항공/숙박 전액지원", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-07-15', '2025-07-28',
'베트남/인도네시아', false, 40, 'open',
'https://www.lsholdings.com',
ARRAY['LS그룹', '해외봉사', 'IT교육', '시설개선'],
ARRAY['DEPT001', 'DEPT003'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 유엔 자원봉사단 대학생 파견', '외교부',
'UN 자원봉사단 대학생 파견 프로그램.',
'{"age": "만 18-29세", "language": "영어 유창", "grade": [3, 4]}',
'{"지원금": "생활비 전액지원", "certificate": true, "UN경력": true}',
'2025-03-01', '2025-05-31', '2025-07-01', '2025-12-31',
'UN 현지사무소', false, 30, 'open',
'https://www.mofa.go.kr/youth',
ARRAY['UN', '자원봉사', '글로벌', '외교부'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 코피온 대학생 해외봉사', '코피온',
'아시아/아프리카 교육봉사 프로그램.',
'{"grade": [1, 2, 3, 4], "health": "건강한 자"}',
'{"참가비": "일부 자부담", "certificate": true}',
'2025-05-01', '2025-06-30', '2025-07-20', '2025-08-05',
'캄보디아/탄자니아', false, 100, 'open',
'https://copion.or.kr',
ARRAY['코피온', '해외봉사', '교육', '아시아'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 삼성 드림클래스 대학생 멘토', '삼성전자',
'저소득층 중고등학생 학습 멘토링 봉사.',
'{"min_gpa": 3.0, "grade": [2, 3, 4]}',
'{"장학금": "월 20만원", "certificate": true}',
'2025-02-01', '2025-03-31', '2025-04-01', '2025-12-31',
'전국', false, 2000, 'open',
'https://www.dreamclass.org',
ARRAY['삼성', '드림클래스', '멘토링', '교육봉사'],
ARRAY['DEPT001', 'DEPT002', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 현대차 해피무브 글로벌 청년봉사단', '현대자동차그룹',
'현대차 글로벌 청년봉사단. 친환경, 교육, 지역개발.',
'{"age": "만 19-29세", "language": "영어 가능자"}',
'{"지원금": "항공/숙박 전액", "certificate": true}',
'2025-04-01', '2025-06-30', '2025-07-15', '2025-07-29',
'인도/인도네시아/가나', false, 60, 'open',
'https://www.hyundai.com',
ARRAY['현대차', '해피무브', '글로벌', '청년봉사'],
ARRAY['DEPT001', 'DEPT003', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'volunteer', '2025년 서울시 청년 지역사회 봉사단', '서울특별시',
'서울시 취약계층 지원 봉사 프로그램.',
'{"age": "만 19-34세", "residence": "서울 거주자"}',
'{"지원금": "활동비 월 30만원", "certificate": true}',
'2025-03-01', '2025-04-30', '2025-05-01', '2025-11-30',
'서울시 전역', false, 500, 'open',
'https://volunteer.seoul.go.kr',
ARRAY['서울시', '지역봉사', '취약계층', '청년'],
ARRAY['DEPT001', 'DEPT014', 'DEPT023'], 'SEED_V4', CURRENT_TIMESTAMP);

-- ============================================
-- 4. Additional Certification Programs (8건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'certification', '2025년 제1회 정보처리기사 시험', '한국산업인력공단',
'국가기술자격 정보처리기사. IT 분야 필수 자격증.',
'{"education": "4년제 졸업자 또는 관련 경력자"}',
'{"취업우대": "IT 기업 채용 필수", "가점": "공무원/공기업 가점"}',
'2025-01-06', '2025-01-09', '2025-02-22', '2025-02-22',
'전국 시험장', false, null, 'open',
'https://www.q-net.or.kr',
ARRAY['정보처리기사', '국가자격증', 'IT', '필수'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 제2회 빅데이터분석기사 시험', '한국데이터산업진흥원',
'국가기술자격 빅데이터분석기사. 데이터 분야 자격증.',
'{"education": "4년제 졸업자 또는 관련 경력자"}',
'{"취업우대": "데이터 직군 채용 우대", "가점": "공기업 가점"}',
'2025-03-01', '2025-03-31', '2025-05-17', '2025-05-17',
'전국 CBT 시험장', false, null, 'open',
'https://www.dataq.or.kr',
ARRAY['빅데이터분석기사', '데이터', '국가자격증', 'AI'],
ARRAY['DEPT001', 'DEPT013'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 SQLD SQL개발자 시험', '한국데이터산업진흥원',
'SQL 개발자 자격증. 데이터베이스 필수 자격.',
'{"education": "제한없음"}',
'{"취업우대": "IT 채용 우대"}',
'2025-02-01', '2025-02-28', '2025-03-15', '2025-03-15',
'전국 CBT 시험장', false, null, 'open',
'https://www.dataq.or.kr',
ARRAY['SQLD', 'SQL', '데이터베이스', '자격증'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 AWS Solutions Architect 자격증', 'Amazon Web Services',
'AWS 클라우드 아키텍트 자격증. Associate/Professional.',
'{"skills": ["클라우드", "네트워크", "보안"]}',
'{"취업우대": "클라우드 직군 필수", "글로벌인증": true}',
'2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31',
'온라인/테스트센터', true, null, 'open',
'https://aws.amazon.com/certification',
ARRAY['AWS', '클라우드', '자격증', '글로벌'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 TOEIC 정기시험', 'ETS',
'TOEIC 영어능력시험. 취업 필수 어학 자격.',
'{"education": "제한없음"}',
'{"취업우대": "채용시 필수", "점수유효": "2년"}',
'2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31',
'전국 시험장', false, null, 'open',
'https://www.toeic.co.kr',
ARRAY['TOEIC', '영어', '어학', '취업'],
ARRAY['DEPT001', 'DEPT002', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 Google Cloud Professional 자격증', 'Google Cloud',
'구글 클라우드 전문가 자격증. Cloud Engineer/Architect.',
'{"skills": ["클라우드", "GCP", "네트워크"]}',
'{"취업우대": "클라우드 직군", "글로벌인증": true}',
'2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31',
'온라인/테스트센터', true, null, 'open',
'https://cloud.google.com/certification',
ARRAY['GCP', '클라우드', '자격증', 'Google'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 Kubernetes CKA/CKAD 자격증', 'CNCF',
'쿠버네티스 관리자/개발자 자격증.',
'{"skills": ["Kubernetes", "Docker", "Linux"]}',
'{"취업우대": "DevOps 직군 필수", "글로벌인증": true}',
'2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31',
'온라인 프록터', true, null, 'open',
'https://www.cncf.io/certification',
ARRAY['Kubernetes', 'CKA', 'DevOps', '컨테이너'],
ARRAY['DEPT001', 'DEPT002'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'certification', '2025년 PMP 프로젝트관리 자격증', 'PMI',
'PMP 프로젝트관리 전문가 자격증.',
'{"experience": "프로젝트 경험 35시간 교육이수"}',
'{"취업우대": "PM 직군 필수", "글로벌인증": true}',
'2025-01-01', '2025-12-31', '2025-01-01', '2025-12-31',
'온라인/테스트센터', true, null, 'open',
'https://www.pmi.org',
ARRAY['PMP', '프로젝트관리', 'PM', '글로벌'],
ARRAY['DEPT006', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP);

-- ============================================
-- 5. Additional Scholarship (6건)
-- ============================================

INSERT INTO tb_opportunity (opportunity_id, opportunity_type, title, organization, description, requirements, benefits, application_start, application_end, start_date, end_date, location, remote_available, slots, status, external_url, tags, department_cds, ins_user_id, ins_dt) VALUES

(gen_random_uuid(), 'scholarship', '2025년 삼성꿈장학재단 대학 장학금', '삼성꿈장학재단',
'삼성 꿈장학생 대학 장학금. 저소득층 우수인재.',
'{"min_gpa": 3.5, "income": "저소득층"}',
'{"amount": "등록금 전액 + 생활비", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 100, 'open',
'https://www.sdream.or.kr',
ARRAY['삼성', '꿈장학재단', '저소득층', '장학금'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025년 현대차 정몽구재단 장학금', '현대차 정몽구재단',
'현대차그룹 미래인재 장학금. 이공계 우수학생.',
'{"min_gpa": 3.5, "major": ["이공계"]}',
'{"amount": "연 1,000만원", "duration": "졸업시까지", "멘토링": true}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 200, 'open',
'https://www.chungmong-koo.org',
ARRAY['현대차', '정몽구재단', '이공계', '장학금'],
ARRAY['DEPT001', 'DEPT003', 'DEPT004'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025년 SK 행복장학재단 장학금', 'SK 행복장학재단',
'SK 행복 장학금. 사회적가치 실현 인재.',
'{"min_gpa": 3.3, "activity": "사회공헌활동 경험"}',
'{"amount": "등록금 전액", "duration": "2년", "멘토링": true}',
'2025-02-01', '2025-04-30', '2025-03-01', '2027-02-28',
'전국', true, 150, 'open',
'https://www.skhappiness.org',
ARRAY['SK', '행복장학재단', '사회공헌', '장학금'],
ARRAY['DEPT001', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025년 부산지역인재 IT장학금', '부산광역시',
'부산지역 IT/상경계열 대학생 장학금.',
'{"min_gpa": 3.5, "region": "부산지역대학", "income": "소득 9분위 이하"}',
'{"amount": "학기당 150만원", "duration": "2년"}',
'2025-02-01', '2025-03-31', '2025-03-01', '2027-02-28',
'부산', true, 195, 'open',
'https://young.busan.go.kr',
ARRAY['부산', '지역인재', 'IT', '장학금'],
ARRAY['DEPT001', 'DEPT002', 'DEPT014'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025년 한전 전력그룹사 장학금', '한국전력공사',
'한전 전력그룹사 이공계 장학금.',
'{"min_gpa": 3.5, "major": ["전기공학", "전자공학", "에너지공학"]}',
'{"amount": "등록금 전액", "duration": "졸업시까지"}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 100, 'open',
'https://www.kepco.co.kr',
ARRAY['한전', '전력그룹', '이공계', '장학금'],
ARRAY['DEPT003', 'DEPT004'], 'SEED_V4', CURRENT_TIMESTAMP),

(gen_random_uuid(), 'scholarship', '2025년 IT 여성인재 장학금', '한국여성과학기술인육성재단',
'IT/과학기술 분야 여성인재 장학금.',
'{"min_gpa": 3.3, "gender": "여성", "major": ["IT", "과학기술"]}',
'{"amount": "연 300만원", "duration": "졸업시까지", "멘토링": true}',
'2025-02-01', '2025-04-30', '2025-03-01', '2029-02-28',
'전국', true, 100, 'open',
'https://www.wiset.or.kr',
ARRAY['여성인재', 'IT', '과학기술', '장학금'],
ARRAY['DEPT001', 'DEPT002', 'DEPT003'], 'SEED_V4', CURRENT_TIMESTAMP);

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
    SELECT COUNT(*) INTO v_new_count FROM tb_opportunity WHERE ins_user_id = 'SEED_V4';

    SELECT string_agg(opportunity_type || ': ' || cnt, ', ')
    INTO v_by_type
    FROM (
        SELECT opportunity_type, COUNT(*) as cnt
        FROM tb_opportunity
        GROUP BY opportunity_type
        ORDER BY cnt DESC
    ) t;

    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Additional Opportunities V4 Added';
    RAISE NOTICE '------------------------------------------';
    RAISE NOTICE 'New records added (SEED_V4): %', v_new_count;
    RAISE NOTICE 'Total tb_opportunity: % records', v_total;
    RAISE NOTICE 'By type: %', v_by_type;
    RAISE NOTICE '==========================================';
END $$;
