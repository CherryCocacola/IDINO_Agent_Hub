-- ============================================
-- 39. 비교과 프로그램 학과 매핑
-- 목적: tb_program에 department_cds 컬럼 추가 및 학과별 프로그램 시드 데이터
-- ============================================

SET search_path TO idino_career;

-- Step 1: ALTER TABLE - department_cds 컬럼 추가
ALTER TABLE tb_program ADD COLUMN IF NOT EXISTS department_cds VARCHAR(20)[];

COMMENT ON COLUMN tb_program.department_cds IS '대상 학과코드 배열 (NULL=전학과 공통)';

-- Step 2: 기존 프로그램에 학과코드 매핑 (IT/공학 계열)
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002','DEPT003','DEPT006','DEPT008'] WHERE program_cd = 'PGM001'; -- 삼성 SDS 인턴십
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002','DEPT013'] WHERE program_cd = 'PGM002'; -- 네이버 부트캠프
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002','DEPT003','DEPT013'] WHERE program_cd = 'PGM003'; -- AI 경진대회
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002'] WHERE program_cd = 'PGM004'; -- 창업동아리 SEED
UPDATE tb_program SET department_cds = NULL WHERE program_cd = 'PGM005'; -- 해외 봉사활동 (전학과 공통)
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002','DEPT003'] WHERE program_cd = 'PGM006'; -- AWS 자격증
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002'] WHERE program_cd = 'PGM007'; -- Google Developer Student Club
UPDATE tb_program SET department_cds = ARRAY['DEPT001','DEPT002','DEPT003'] WHERE program_cd = 'PGM008'; -- 산학연 프로젝트

-- Step 3: 학과 그룹별 신규 프로그램 INSERT
INSERT INTO tb_program (program_cd, program_nm, program_type, organizer, start_date, end_date, description, competency_contributions, department_cds, use_fg, ins_user_id, ins_dt) VALUES

-- ============================================
-- 보건/의료 계열 (DEPT028 의예과, DEPT029 간호학과)
-- ============================================
('PGM101', '병원 임상실습 프로그램', 'internship', '대학병원 교육센터', '2025-07-01', '2025-08-31',
 '대학병원에서 진행하는 임상실습으로 의료 현장 경험을 쌓습니다',
 '{"COMP01": 0.4, "COMP03": 0.3}', ARRAY['DEPT028','DEPT029'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM102', '보건의료 봉사단', 'volunteer', '적십자사', '2025-03-01', '2025-12-31',
 '지역사회 건강검진 및 보건교육 봉사활동',
 '{"COMP03": 0.4, "COMP05": 0.3}', ARRAY['DEPT028','DEPT029'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM103', '건강증진 캠페인 기획', 'project', '보건복지부', '2025-04-01', '2025-06-30',
 '대학생이 기획하는 건강증진 캠페인 프로젝트',
 '{"COMP02": 0.3, "COMP03": 0.3}', ARRAY['DEPT028','DEPT029'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM104', 'BLS/ACLS 자격증 과정', 'certificate', '대한심폐소생협회', '2025-05-01', '2025-06-30',
 '기본 및 전문 심폐소생술 자격증 취득 과정',
 '{"COMP01": 0.5, "COMP06": 0.3}', ARRAY['DEPT028','DEPT029'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM105', '의료기기 활용 세미나', 'seminar', '식품의약품안전처', '2025-09-01', '2025-10-31',
 '최신 의료기기 활용법 및 안전관리 세미나',
 '{"COMP01": 0.3, "COMP06": 0.4}', ARRAY['DEPT028','DEPT029'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM106', '보건의료 논문 경진대회', 'contest', '대한의학회', '2025-06-01', '2025-11-30',
 '학부생 대상 보건의료 분야 논문 발표 대회',
 '{"COMP01": 0.3, "COMP02": 0.4}', ARRAY['DEPT028','DEPT029'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 경영/사회 계열 (DEPT014~017 경영, DEPT022~024 사회과학)
-- ============================================
('PGM201', '마케팅 전략 공모전', 'contest', '대한상공회의소', '2025-05-01', '2025-10-31',
 '기업 마케팅 전략을 기획하고 발표하는 대학생 공모전',
 '{"COMP02": 0.4, "COMP03": 0.3}', ARRAY['DEPT014','DEPT015','DEPT016','DEPT017'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM202', '창업 동아리 비즈플랜', 'club', '창업지원센터', '2025-03-01', '2025-12-31',
 '비즈니스 모델 수립부터 투자 유치까지 경험하는 창업 동아리',
 '{"COMP02": 0.3, "COMP03": 0.4}', ARRAY['DEPT014','DEPT016','DEPT017'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM203', '경영 사례 분석 스터디', 'club', '경영대학 학생회', '2025-03-01', '2025-12-31',
 'Harvard Business Review 등 경영 사례를 분석하는 스터디',
 '{"COMP01": 0.3, "COMP02": 0.4}', ARRAY['DEPT014','DEPT015','DEPT016','DEPT017'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM204', '전산회계 자격증 과정', 'certificate', '한국세무사회', '2025-04-01', '2025-06-30',
 '전산회계 1급/2급 자격증 취득 준비 과정',
 '{"COMP01": 0.5, "COMP06": 0.3}', ARRAY['DEPT014','DEPT015'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM205', '경영컨설팅 인턴십', 'internship', '주요 컨설팅펌', '2025-07-01', '2025-08-31',
 '컨설팅 기업에서 진행하는 하계 인턴십 프로그램',
 '{"COMP01": 0.3, "COMP03": 0.4}', ARRAY['DEPT014','DEPT015','DEPT016','DEPT017'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM206', '사회조사분석사 자격증', 'certificate', '한국산업인력공단', '2025-03-01', '2025-05-31',
 '사회조사분석사 2급 자격증 취득 과정',
 '{"COMP01": 0.4, "COMP06": 0.3}', ARRAY['DEPT022','DEPT023','DEPT024'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM207', '사회복지 현장실습', 'internship', '사회복지관', '2025-07-01', '2025-08-31',
 '사회복지기관에서 진행하는 현장실습 프로그램',
 '{"COMP03": 0.4, "COMP05": 0.3}', ARRAY['DEPT022','DEPT023','DEPT024'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 공학 계열 (DEPT003~008: 전자, 기계, 화학, 산업, 건축, 신소재)
-- ============================================
('PGM301', '캡스톤 디자인 경진대회', 'contest', '공학교육혁신센터', '2025-03-01', '2025-11-30',
 '산업체 문제를 해결하는 캡스톤 디자인 프로젝트 대회',
 '{"COMP01": 0.3, "COMP02": 0.3, "COMP03": 0.3}', ARRAY['DEPT003','DEPT004','DEPT005','DEPT006','DEPT007','DEPT008'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM302', '공학설계 경진대회', 'contest', '한국공학교육학회', '2025-06-01', '2025-11-30',
 '창의적 공학설계 능력을 겨루는 대회',
 '{"COMP01": 0.4, "COMP02": 0.3}', ARRAY['DEPT003','DEPT004','DEPT005','DEPT006','DEPT007','DEPT008'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM303', '엔지니어 현장실습', 'internship', '주요 제조기업', '2025-07-01', '2025-08-31',
 '제조/건설 기업에서의 엔지니어 인턴십',
 '{"COMP01": 0.4, "COMP03": 0.3}', ARRAY['DEPT003','DEPT004','DEPT005','DEPT006','DEPT007','DEPT008'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM304', '기술사 기초 자격증', 'certificate', '한국산업인력공단', '2025-04-01', '2025-06-30',
 '기사/산업기사 자격증 취득 준비 과정',
 '{"COMP01": 0.5, "COMP06": 0.3}', ARRAY['DEPT003','DEPT004','DEPT005','DEPT006','DEPT007','DEPT008'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM305', '로봇공학 동아리', 'club', '공과대학 학생회', '2025-03-01', '2025-12-31',
 '로봇 설계 및 제작을 경험하는 동아리',
 '{"COMP01": 0.3, "COMP02": 0.3}', ARRAY['DEPT003','DEPT004','DEPT006'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- IT/데이터 계열 (DEPT001 컴퓨터공학, DEPT002 소프트웨어공학, DEPT013 통계학)
-- ============================================
('PGM401', '프로그래밍 동아리 코딩랩', 'club', '정보통신대학', '2025-03-01', '2025-12-31',
 '알고리즘 스터디와 프로젝트를 진행하는 프로그래밍 동아리',
 '{"COMP01": 0.4, "COMP02": 0.3}', ARRAY['DEPT001','DEPT002','DEPT013'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM402', 'AI 해커톤', 'contest', '과학기술정보통신부', '2025-09-01', '2025-11-30',
 'AI/ML 기술을 활용한 문제 해결 해커톤',
 '{"COMP01": 0.4, "COMP02": 0.4}', ARRAY['DEPT001','DEPT002','DEPT013'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM403', '클라우드 자격증 과정', 'certificate', 'AWS/Azure', '2025-04-01', '2025-06-30',
 '클라우드 아키텍처 관련 자격증 취득 과정',
 '{"COMP01": 0.5, "COMP06": 0.3}', ARRAY['DEPT001','DEPT002'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM404', '오픈소스 컨트리뷰션', 'project', '정보통신산업진흥원', '2025-06-01', '2025-11-30',
 '오픈소스 프로젝트 기여를 통한 실무 역량 강화',
 '{"COMP01": 0.3, "COMP02": 0.3, "COMP03": 0.3}', ARRAY['DEPT001','DEPT002'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM405', 'IT 기업 인턴십', 'internship', '주요 IT 기업', '2025-07-01', '2025-08-31',
 'IT 기업에서의 소프트웨어 개발 인턴십',
 '{"COMP01": 0.4, "COMP03": 0.3}', ARRAY['DEPT001','DEPT002','DEPT013'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 자연과학 계열 (DEPT009~012: 수학, 물리, 화학, 생명과학)
-- ============================================
('PGM501', '실험실 인턴 프로그램', 'internship', '자연과학대학 연구실', '2025-07-01', '2025-08-31',
 '교내 연구실에서 진행하는 학부생 연구 인턴십',
 '{"COMP01": 0.4, "COMP02": 0.3}', ARRAY['DEPT009','DEPT010','DEPT011','DEPT012'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM502', '학술 논문 발표 대회', 'contest', '한국과학기술단체총연합회', '2025-06-01', '2025-11-30',
 '학부생 대상 과학 분야 논문 발표 대회',
 '{"COMP01": 0.3, "COMP02": 0.4}', ARRAY['DEPT009','DEPT010','DEPT011','DEPT012'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM503', '과학실험 지도 봉사', 'volunteer', '과학교육원', '2025-03-01', '2025-12-31',
 '중고등학생 대상 과학실험 지도 봉사활동',
 '{"COMP03": 0.3, "COMP05": 0.4}', ARRAY['DEPT009','DEPT010','DEPT011','DEPT012'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM504', '수리과학 튜터링 프로그램', 'club', '자연과학대학', '2025-03-01', '2025-12-31',
 '수학/통계 기초를 다지는 학습 튜터링 프로그램',
 '{"COMP01": 0.4, "COMP03": 0.3}', ARRAY['DEPT009','DEPT013'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 디자인/예술 계열 (DEPT025 디자인, DEPT026 음악, DEPT027 미술)
-- ============================================
('PGM601', 'UX/UI 디자인 공모전', 'contest', '한국디자인진흥원', '2025-05-01', '2025-10-31',
 'UX/UI 디자인 실력을 겨루는 대학생 공모전',
 '{"COMP01": 0.3, "COMP02": 0.4}', ARRAY['DEPT025','DEPT027'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM602', '포트폴리오 프로젝트', 'project', '예술대학', '2025-03-01', '2025-11-30',
 '개인 포트폴리오 완성을 위한 실전 프로젝트',
 '{"COMP01": 0.3, "COMP02": 0.3, "COMP03": 0.3}', ARRAY['DEPT025','DEPT026','DEPT027'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM603', '디자인씽킹 워크숍', 'seminar', '디자인혁신센터', '2025-04-01', '2025-05-31',
 '디자인씽킹 방법론을 활용한 문제 해결 워크숍',
 '{"COMP02": 0.4, "COMP03": 0.3}', ARRAY['DEPT025','DEPT027'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM604', '디자인 스튜디오 인턴십', 'internship', '주요 디자인 에이전시', '2025-07-01', '2025-08-31',
 '디자인 에이전시에서의 실무 인턴십',
 '{"COMP01": 0.3, "COMP03": 0.4}', ARRAY['DEPT025','DEPT027'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM605', '예술작품 전시회 기획', 'project', '예술대학 학생회', '2025-09-01', '2025-12-31',
 '학생 주도 전시회 기획 및 운영 프로젝트',
 '{"COMP02": 0.3, "COMP03": 0.4}', ARRAY['DEPT025','DEPT026','DEPT027'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 인문학 계열 (DEPT018~021: 국문, 영문, 철학, 역사)
-- ============================================
('PGM701', '글쓰기 공모전', 'contest', '한국문학회', '2025-04-01', '2025-10-31',
 '대학생 대상 창작 및 학술 글쓰기 공모전',
 '{"COMP02": 0.4, "COMP03": 0.3}', ARRAY['DEPT018','DEPT019','DEPT020','DEPT021'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM702', '인문학 독서 토론 동아리', 'club', '인문대학', '2025-03-01', '2025-12-31',
 '고전 및 현대 인문학 서적을 읽고 토론하는 동아리',
 '{"COMP01": 0.3, "COMP03": 0.4}', ARRAY['DEPT018','DEPT019','DEPT020','DEPT021'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM703', '번역/통역 인턴십', 'internship', '출판사/번역기관', '2025-07-01', '2025-08-31',
 '번역/통역 분야 실무 인턴십',
 '{"COMP01": 0.4, "COMP03": 0.3}', ARRAY['DEPT018','DEPT019'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM704', '한국어교육능력검정시험 준비', 'certificate', '국립국어원', '2025-04-01', '2025-07-31',
 '한국어교원 자격증 취득을 위한 준비 과정',
 '{"COMP01": 0.4, "COMP06": 0.3}', ARRAY['DEPT018','DEPT019'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 교육학 계열 (DEPT030)
-- ============================================
('PGM801', '교육봉사 프로그램', 'volunteer', '교육대학', '2025-03-01', '2025-12-31',
 '지역 학교에서 진행하는 교육봉사 활동',
 '{"COMP03": 0.4, "COMP05": 0.3}', ARRAY['DEPT030'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM802', '교원임용 스터디', 'club', '사범대학', '2025-03-01', '2025-12-31',
 '교원임용시험 대비 스터디 그룹',
 '{"COMP01": 0.4, "COMP06": 0.3}', ARRAY['DEPT030'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM803', '교육실습', 'internship', '협력학교', '2025-04-01', '2025-06-30',
 '초중고 학교에서 진행하는 교생실습',
 '{"COMP01": 0.3, "COMP03": 0.4}', ARRAY['DEPT030'], 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

-- ============================================
-- 전학과 공통 (department_cds = NULL)
-- ============================================
('PGM901', '대학생 봉사활동 리더십', 'volunteer', '대학 봉사센터', '2025-03-01', '2025-12-31',
 '지역사회 봉사활동을 통한 리더십 역량 개발',
 '{"COMP03": 0.3, "COMP05": 0.4}', NULL, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM902', '리더십 아카데미', 'seminar', '학생처', '2025-04-01', '2025-05-31',
 '대학생 리더십 역량 강화를 위한 교육 프로그램',
 '{"COMP03": 0.4, "COMP04": 0.3}', NULL, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM903', '취업역량 강화 프로그램', 'seminar', '취업지원센터', '2025-09-01', '2025-11-30',
 '이력서/자기소개서 작성, 면접 준비 등 취업역량 강화',
 '{"COMP04": 0.4, "COMP06": 0.3}', NULL, 'Y', 'SYSTEM', CURRENT_TIMESTAMP),

('PGM904', '글로벌 교환학생 준비', 'project', '국제교류센터', '2025-03-01', '2025-06-30',
 '해외 교환학생 프로그램 준비 및 어학역량 강화',
 '{"COMP03": 0.3, "COMP05": 0.4}', NULL, 'Y', 'SYSTEM', CURRENT_TIMESTAMP)

ON CONFLICT (program_cd) DO NOTHING;

-- 인덱스 추가 (학과코드 검색 성능)
CREATE INDEX IF NOT EXISTS idx_program_department_cds ON tb_program USING GIN (department_cds);
