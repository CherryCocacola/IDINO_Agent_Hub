-- ============================================
-- IDINO Career - Additional Worknet Job Codes
-- 추가 워크넷 직업 코드 (한국표준직업분류 기반)
-- Created: 2025-01-26
-- ============================================

SET search_path TO idino_career;

BEGIN;

-- ============================================
-- 1. 법률 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('261101', '판사', 'Judge', '법률', '사법부', '법원에서 재판을 진행하고 판결을 내리는 법관', ARRAY['법률해석', '판결문작성', '증거평가', '법정관리'], ARRAY['법학'], 6000, 12000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('261102', '검사', 'Prosecutor', '법률', '검찰', '범죄를 수사하고 기소하여 공소를 유지하는 법률 전문가', ARRAY['수사기법', '법률해석', '논증', '기소장작성'], ARRAY['법학'], 5500, 11000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('261201', '변호사', 'Lawyer', '법률', '법률서비스', '의뢰인을 대리하여 법률 자문 및 소송을 수행하는 전문가', ARRAY['법률자문', '소송대리', '계약서작성', '협상'], ARRAY['법학'], 5000, 15000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('261301', '법무사', 'Legal Scrivener', '법률', '법률서비스', '등기, 공탁, 소송 서류 작성을 대리하는 전문가', ARRAY['등기업무', '서류작성', '법률상담', '소송서류'], ARRAY['법학'], 3500, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('261302', '집행관', 'Bailiff', '법률', '사법부', '법원의 결정을 집행하는 공무원', ARRAY['강제집행', '서류송달', '현장집행'], ARRAY['법학', '행정학'], 3500, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('261401', '변리사', 'Patent Attorney', '법률', '지식재산', '특허, 상표, 디자인 등 지식재산권 출원 및 분쟁을 담당하는 전문가', ARRAY['특허출원', '명세서작성', '심판대리', '기술분석'], ARRAY['법학', '이공계열'], 4500, 12000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('261901', '법률사무원', 'Legal Assistant', '법률', '법률서비스', '변호사 및 법무사를 보조하여 법률 사무를 처리하는 직원', ARRAY['서류작성', '사건관리', '법률조사', '고객응대'], ARRAY['법학', '행정학'], 2800, 4500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 2. 경영/금융 전문가 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('271101', '노무사', 'Certified Labor Attorney', '경영/사무', '인사/노무', '노동관계법 전문가로서 노사 분쟁 해결 및 노무관리 자문', ARRAY['노동법', '인사관리', '분쟁조정', '취업규칙작성'], ARRAY['법학', '경영학', '행정학'], 4000, 8000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('271102', '인사컨설턴트', 'HR Consultant', '경영/사무', '인사/노무', '기업의 인사제도 및 조직문화 개선을 컨설팅하는 전문가', ARRAY['조직진단', '인사제도설계', '교육훈련', '성과관리'], ARRAY['경영학', '심리학', '사회학'], 4000, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271103', '헤드헌터', 'Executive Recruiter', '경영/사무', '인사/노무', '기업의 핵심 인재를 발굴하고 채용을 지원하는 전문가', ARRAY['인재발굴', '면접', '네트워킹', '협상'], ARRAY['경영학', '심리학'], 3500, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271201', '공인회계사', 'Certified Public Accountant', '경영/사무', '금융/재무', '회계감사, 세무대리, 경영자문을 수행하는 공인 전문가', ARRAY['회계감사', '재무제표분석', '세무', 'IFRS'], ARRAY['회계학', '경영학'], 5000, 12000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271301', '세무사', 'Tax Accountant', '경영/사무', '금융/재무', '세무신고 대리 및 세무 자문을 수행하는 전문가', ARRAY['세무신고', '절세전략', '세무조사대응', '법인세'], ARRAY['회계학', '세무학', '경영학'], 4000, 9000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271401', '관세사', 'Customs Broker', '경영/사무', '무역/관세', '수출입 통관 및 관세 업무를 대행하는 전문가', ARRAY['통관업무', '관세법', 'FTA활용', '원산지증명'], ARRAY['무역학', '경영학', '법학'], 3800, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271501', '손해사정사', 'Loss Adjuster', '경영/사무', '보험', '보험 사고의 손해액을 조사하고 산정하는 전문가', ARRAY['손해조사', '보험약관해석', '보상협상', '현장조사'], ARRAY['경영학', '법학', '보험학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271502', '보험계리사', 'Actuary', '경영/사무', '보험', '보험상품 개발 및 리스크 분석을 수행하는 전문가', ARRAY['통계분석', '리스크모델링', '상품설계', '수리분석'], ARRAY['수학', '통계학', '보험학'], 5000, 11000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271601', '감정평가사', 'Property Appraiser', '경영/사무', '부동산', '부동산 및 동산의 경제적 가치를 평가하는 전문가', ARRAY['가치평가', '시장분석', '감정평가서작성', '부동산법'], ARRAY['부동산학', '경영학', '법학'], 4000, 9000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('271602', '공인중개사', 'Licensed Real Estate Agent', '경영/사무', '부동산', '부동산 매매, 임대차 중개 업무를 수행하는 전문가', ARRAY['중개업무', '계약서작성', '시장분석', '고객상담'], ARRAY['부동산학', '경영학'], 2500, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 3. 교육 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('211102', '대학강사', 'University Lecturer', '교육', '고등교육', '대학에서 강의를 담당하는 교육자', ARRAY['강의', '연구', '학생지도'], ARRAY['전공무관(석사이상)'], 3000, 5000, 'declining', 'SYSTEM', CURRENT_TIMESTAMP),
('212101', '중등교사', 'Secondary School Teacher', '교육', '중등교육', '중학교 및 고등학교에서 교과목을 가르치는 교사', ARRAY['교과지도', '학급운영', '생활지도', '평가'], ARRAY['사범대학 전공', '교직이수'], 3200, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('212201', '초등교사', 'Elementary School Teacher', '교육', '초등교육', '초등학교에서 학생을 가르치는 교사', ARRAY['전과목지도', '학급운영', '생활지도', '학부모상담'], ARRAY['초등교육과'], 3200, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('212301', '특수교육교사', 'Special Education Teacher', '교육', '특수교육', '장애학생을 대상으로 특수교육을 담당하는 교사', ARRAY['개별화교육', '치료교육', '통합교육', '행동지원'], ARRAY['특수교육과'], 3200, 5500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('213001', '유치원교사', 'Kindergarten Teacher', '교육', '유아교육', '유아의 교육 및 보육을 담당하는 교사', ARRAY['유아교육', '놀이지도', '학부모상담', '안전관리'], ARRAY['유아교육과', '아동학과'], 2500, 4000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('213002', '보육교사', 'Childcare Teacher', '교육', '유아교육', '영유아의 보육을 담당하는 교사', ARRAY['영유아보육', '안전관리', '부모상담', '프로그램운영'], ARRAY['유아교육과', '아동학과', '사회복지학과'], 2300, 3500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('214101', '어학강사', 'Language Instructor', '교육', '사설교육', '외국어를 가르치는 강사', ARRAY['어학교육', '회화지도', '문법지도', '시험대비'], ARRAY['영어영문학', '어문학계열'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('214201', '컴퓨터강사', 'Computer Instructor', '교육', '사설교육', '컴퓨터 및 IT 관련 교육을 담당하는 강사', ARRAY['프로그래밍교육', '자격증교육', '커리큘럼개발'], ARRAY['컴퓨터공학', '교육공학'], 2800, 4500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('214401', '예체능강사', 'Arts/Sports Instructor', '교육', '사설교육', '음악, 미술, 체육 등 예체능 분야를 가르치는 강사', ARRAY['실기지도', '공연/대회준비', '개인레슨'], ARRAY['음악학', '미술학', '체육학'], 2500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('215101', '장학사', 'Education Supervisor', '교육', '교육행정', '교육과정 및 교수법 개선을 지도하는 교육전문직', ARRAY['교육정책', '교육과정개발', '교원연수', '학교평가'], ARRAY['교육학', '교육행정'], 4000, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 4. 공학/기술 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('231101', '건축설계사', 'Architect', '건설/건축', '건축설계', '건축물의 설계 및 감리를 담당하는 전문가', ARRAY['건축설계', 'CAD', 'BIM', '건축법규'], ARRAY['건축학', '건축공학'], 3500, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('231102', '건축시공기술자', 'Construction Engineer', '건설/건축', '건축시공', '건축 현장의 시공 관리를 담당하는 기술자', ARRAY['시공관리', '공정관리', '품질관리', '안전관리'], ARRAY['건축공학', '토목공학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('231201', '토목기술자', 'Civil Engineer', '건설/건축', '토목', '도로, 교량, 터널 등 토목 구조물을 설계하고 시공하는 전문가', ARRAY['토목설계', '구조계산', 'CAD', '현장관리'], ARRAY['토목공학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('231301', '조경기술자', 'Landscape Architect', '건설/건축', '조경', '공원, 정원 등 조경 공간을 설계하고 시공하는 전문가', ARRAY['조경설계', '식재설계', 'CAD', '환경생태'], ARRAY['조경학', '환경학'], 3200, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('231401', '도시계획가', 'Urban Planner', '건설/건축', '도시계획', '도시의 개발 및 정비 계획을 수립하는 전문가', ARRAY['도시계획', 'GIS', '법규분석', '정책수립'], ARRAY['도시공학', '건축학', '지리학'], 3500, 6500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('232101', '기계설계기술자', 'Mechanical Design Engineer', '기계/자동차', '기계설계', '기계 및 장비를 설계하는 전문가', ARRAY['3D CAD', '기계설계', '구조해석', '재료역학'], ARRAY['기계공학'], 3800, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('232102', '자동차설계기술자', 'Automotive Engineer', '기계/자동차', '자동차', '자동차 부품 및 시스템을 설계하는 전문가', ARRAY['자동차설계', 'CATIA', '구조해석', '차량동역학'], ARRAY['기계공학', '자동차공학'], 4000, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('232103', '로봇공학기술자', 'Robotics Engineer', '기계/자동차', '로봇', '산업용/서비스용 로봇을 개발하는 전문가', ARRAY['로봇설계', '제어공학', '프로그래밍', '센서기술'], ARRAY['기계공학', '전자공학', '로봇공학'], 4200, 8000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('233101', '전기공학기술자', 'Electrical Engineer', '전기/전자', '전기', '전기 시스템 및 설비를 설계하고 관리하는 전문가', ARRAY['전기설계', 'PLC', '전력시스템', '전기안전'], ARRAY['전기공학'], 3800, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('233201', '전자공학기술자', 'Electronics Engineer', '전기/전자', '전자', '전자 회로 및 시스템을 개발하는 전문가', ARRAY['회로설계', 'PCB설계', 'FPGA', '임베디드'], ARRAY['전자공학', '정보통신공학'], 4000, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('233301', '반도체공학기술자', 'Semiconductor Engineer', '전기/전자', '반도체', '반도체 소자 및 공정을 개발하는 전문가', ARRAY['공정설계', '소자물리', '클린룸운영', '테스트'], ARRAY['전자공학', '재료공학', '물리학'], 4500, 9000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('234101', '화학공학기술자', 'Chemical Engineer', '화학/에너지', '화학공학', '화학 공정 및 플랜트를 설계하고 운영하는 전문가', ARRAY['공정설계', '화학반응', '플랜트운영', '안전관리'], ARRAY['화학공학', '화학'], 4000, 7500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('234201', '환경공학기술자', 'Environmental Engineer', '화학/에너지', '환경', '환경오염 방지 및 처리 시설을 설계하는 전문가', ARRAY['환경영향평가', '수처리', '대기오염', '폐기물처리'], ARRAY['환경공학', '화학공학'], 3500, 6500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('234301', '신재생에너지기술자', 'Renewable Energy Engineer', '화학/에너지', '에너지', '태양광, 풍력 등 신재생에너지 시스템을 개발하는 전문가', ARRAY['에너지시스템', '전력변환', '설비설계', '효율분석'], ARRAY['에너지공학', '전기공학', '기계공학'], 4000, 7500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('235101', '산업안전기술자', 'Industrial Safety Engineer', '안전/품질', '산업안전', '산업현장의 안전관리 및 재해예방을 담당하는 전문가', ARRAY['안전관리', '위험성평가', '안전교육', '법규준수'], ARRAY['안전공학', '산업공학'], 3500, 6500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('235201', '품질관리기술자', 'Quality Control Engineer', '안전/품질', '품질관리', '제품의 품질을 검사하고 관리하는 전문가', ARRAY['품질검사', 'SPC', 'ISO', '불량분석'], ARRAY['산업공학', '공학계열'], 3500, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 5. 디자인 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('285401', '광고디자이너', 'Advertising Designer', '예술/디자인', '시각디자인', '광고물의 시각적 디자인을 담당하는 전문가', ARRAY['Photoshop', 'Illustrator', '타이포그래피', '광고기획'], ARRAY['시각디자인', '광고학'], 3000, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('285402', '편집디자이너', 'Editorial Designer', '예술/디자인', '시각디자인', '책, 잡지 등 출판물의 레이아웃을 디자인하는 전문가', ARRAY['InDesign', '타이포그래피', '레이아웃', '인쇄지식'], ARRAY['시각디자인', '출판학'], 2800, 5000, 'declining', 'SYSTEM', CURRENT_TIMESTAMP),
('285403', '패키지디자이너', 'Package Designer', '예술/디자인', '시각디자인', '제품 포장의 디자인을 담당하는 전문가', ARRAY['3D모델링', '인쇄지식', '재료이해', '브랜딩'], ARRAY['시각디자인', '산업디자인'], 3000, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('285501', '웹디자이너', 'Web Designer', '예술/디자인', '디지털디자인', '웹사이트의 시각적 디자인을 담당하는 전문가', ARRAY['Figma', 'Adobe XD', 'HTML/CSS', '반응형디자인'], ARRAY['시각디자인', '멀티미디어학'], 3200, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('285502', '멀티미디어디자이너', 'Multimedia Designer', '예술/디자인', '디지털디자인', '영상, 애니메이션 등 멀티미디어 콘텐츠를 제작하는 전문가', ARRAY['After Effects', 'Premiere', '모션그래픽', '영상편집'], ARRAY['영상학', '시각디자인', '미디어학'], 3000, 5500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('285503', '게임그래픽디자이너', 'Game Graphic Designer', '예술/디자인', '디지털디자인', '게임의 그래픽 요소를 디자인하는 전문가', ARRAY['3D모델링', '텍스처링', '캐릭터디자인', 'Unity'], ARRAY['게임학', '시각디자인', '만화애니메이션'], 3200, 6000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('285504', 'UX/UI디자이너', 'UX/UI Designer', '예술/디자인', '디지털디자인', '사용자 경험과 인터페이스를 설계하는 전문가', ARRAY['Figma', '프로토타이핑', '사용자조사', '인터랙션디자인'], ARRAY['시각디자인', '산업디자인', '컴퓨터공학'], 3500, 6500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('285601', '패션디자이너', 'Fashion Designer', '예술/디자인', '패션디자인', '의류 및 패션 제품을 디자인하는 전문가', ARRAY['패턴설계', '소재이해', '트렌드분석', 'CLO'], ARRAY['패션디자인', '의류학'], 2800, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('285701', '실내디자이너', 'Interior Designer', '예술/디자인', '공간디자인', '실내 공간의 디자인을 담당하는 전문가', ARRAY['3D MAX', 'AutoCAD', '색채계획', '가구배치'], ARRAY['실내디자인', '건축학'], 3000, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('285702', '전시디자이너', 'Exhibition Designer', '예술/디자인', '공간디자인', '전시 공간 및 이벤트 공간을 디자인하는 전문가', ARRAY['공간설계', '조명디자인', '그래픽설계', '전시기획'], ARRAY['공간디자인', '시각디자인'], 3000, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 6. 미디어/콘텐츠 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('283101', 'PD(프로듀서)', 'Producer/Director', '미디어/방송', '방송제작', '방송 프로그램의 기획 및 제작을 총괄하는 전문가', ARRAY['기획력', '연출', '스토리텔링', '제작관리'], ARRAY['방송학', '미디어학', '영상학'], 3500, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('283102', '방송작가', 'Broadcasting Writer', '미디어/방송', '방송제작', '방송 프로그램의 대본 및 구성을 작성하는 전문가', ARRAY['글쓰기', '스토리텔링', '취재', '구성력'], ARRAY['문예창작', '방송학', '국문학'], 2500, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('283103', '영상편집자', 'Video Editor', '미디어/방송', '영상제작', '영상물의 편집을 담당하는 전문가', ARRAY['Premiere', 'Final Cut', '색보정', '음향편집'], ARRAY['영상학', '방송학'], 2800, 5000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('283201', '기자', 'Journalist', '미디어/방송', '언론', '뉴스 취재 및 기사 작성을 담당하는 전문가', ARRAY['취재', '글쓰기', '인터뷰', '팩트체크'], ARRAY['신문방송학', '언론학', '정치학'], 3200, 6000, 'declining', 'SYSTEM', CURRENT_TIMESTAMP),
('283202', '아나운서', 'Announcer', '미디어/방송', '언론', '방송에서 뉴스 및 프로그램 진행을 담당하는 전문가', ARRAY['발성', '진행', '인터뷰', '리포팅'], ARRAY['신문방송학', '국문학'], 4000, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('283301', '유튜버/크리에이터', 'YouTuber/Content Creator', '미디어/방송', '1인미디어', '온라인 플랫폼에서 콘텐츠를 제작하는 창작자', ARRAY['영상제작', '편집', '기획', 'SNS마케팅'], ARRAY['미디어학', '영상학'], 1500, 10000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('284101', '소설가', 'Novelist', '문화/예술', '문학', '소설을 창작하는 작가', ARRAY['스토리텔링', '문장력', '상상력', '취재'], ARRAY['문예창작', '국문학'], 1500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('284102', '시나리오작가', 'Screenwriter', '문화/예술', '영상', '영화, 드라마의 시나리오를 작성하는 작가', ARRAY['시나리오작성', '스토리텔링', '대사', '구성'], ARRAY['문예창작', '영상학', '연극영화'], 2500, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('284201', '번역가', 'Translator', '문화/예술', '언어', '문서 및 콘텐츠를 번역하는 전문가', ARRAY['외국어', '문장력', '전문지식', '교정'], ARRAY['어문학계열', '통번역학'], 2500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('284202', '통역사', 'Interpreter', '문화/예술', '언어', '실시간으로 구두 통역을 수행하는 전문가', ARRAY['외국어', '순발력', '전문지식', '커뮤니케이션'], ARRAY['통번역학', '어문학계열'], 3500, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 7. 사회복지/상담 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('241101', '사회복지사', 'Social Worker', '사회복지', '사회복지', '개인 및 가족의 사회적 문제 해결을 지원하는 전문가', ARRAY['상담', '사례관리', '프로그램기획', '자원연계'], ARRAY['사회복지학'], 2500, 4000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('241201', '상담심리사', 'Counseling Psychologist', '사회복지', '상담', '심리 상담을 통해 내담자를 지원하는 전문가', ARRAY['심리상담', '심리검사', '사례개념화', '치료계획'], ARRAY['심리학', '상담학'], 2800, 5000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('241202', '임상심리사', 'Clinical Psychologist', '사회복지', '상담', '정신건강 평가 및 치료를 담당하는 전문가', ARRAY['심리평가', '치료', '진단', '연구'], ARRAY['심리학', '임상심리'], 3000, 5500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('241301', '청소년지도사', 'Youth Counselor', '사회복지', '청소년', '청소년 프로그램 기획 및 지도를 담당하는 전문가', ARRAY['프로그램기획', '상담', '활동지도', '위기개입'], ARRAY['청소년학', '사회복지학', '교육학'], 2300, 3800, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('241302', '직업상담사', 'Career Counselor', '사회복지', '취업지원', '구직자의 취업을 지원하는 상담 전문가', ARRAY['진로상담', '취업알선', '직업정보제공', '이력서작성'], ARRAY['상담학', '교육학', '사회복지학'], 2500, 4000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 8. 서비스/영업 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('311101', '호텔매니저', 'Hotel Manager', '관광/서비스', '호텔', '호텔의 운영 및 관리를 담당하는 전문가', ARRAY['호텔경영', '고객서비스', '인사관리', '매출관리'], ARRAY['호텔관광학', '경영학'], 3000, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('311102', '호텔리어', 'Hotelier', '관광/서비스', '호텔', '호텔의 프론트, 컨시어지 등 서비스를 담당하는 전문가', ARRAY['고객응대', '예약관리', '외국어', '문제해결'], ARRAY['호텔관광학', '외국어'], 2500, 4000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('311201', '항공승무원', 'Flight Attendant', '관광/서비스', '항공', '항공기 내 승객 서비스 및 안전을 담당하는 전문가', ARRAY['고객서비스', '안전관리', '외국어', '응급처치'], ARRAY['항공서비스학', '관광학', '외국어'], 3000, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('311301', '여행기획자', 'Travel Planner', '관광/서비스', '여행', '여행 상품을 기획하고 운영하는 전문가', ARRAY['상품기획', '일정관리', '협력업체관리', '마케팅'], ARRAY['관광학', '경영학'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('311302', '관광가이드', 'Tour Guide', '관광/서비스', '여행', '관광지에서 여행객을 안내하는 전문가', ARRAY['외국어', '지역지식', '커뮤니케이션', '안전관리'], ARRAY['관광학', '역사학', '외국어'], 2500, 4500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('312101', '영업관리자', 'Sales Manager', '영업/판매', '영업', '영업팀을 관리하고 매출 목표를 달성하는 관리자', ARRAY['영업전략', '팀관리', '고객관리', '협상'], ARRAY['경영학', '마케팅'], 3500, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('312102', '기술영업', 'Technical Sales', '영업/판매', '영업', 'IT, 기계 등 기술 제품의 영업을 담당하는 전문가', ARRAY['기술지식', '제안서작성', '프레젠테이션', '고객관리'], ARRAY['공학계열', '경영학'], 3500, 7000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('313101', '바리스타', 'Barista', '식음료', '카페', '커피 및 음료를 제조하는 전문가', ARRAY['커피추출', '라떼아트', '고객서비스', '음료개발'], ARRAY['식품조리학', '호텔관광학'], 2200, 3500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('313102', '조리사', 'Chef', '식음료', '요리', '음식을 조리하는 전문가', ARRAY['조리기술', '메뉴개발', '위생관리', '원가관리'], ARRAY['조리학', '식품영양학'], 2500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('313103', '파티시에', 'Pastry Chef', '식음료', '제과제빵', '제과, 제빵을 전문으로 하는 조리사', ARRAY['제과기술', '제빵기술', '데코레이션', '메뉴개발'], ARRAY['제과제빵학', '조리학'], 2300, 4500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('313104', '소믈리에', 'Sommelier', '식음료', '와인', '와인 선택 및 서비스를 담당하는 전문가', ARRAY['와인지식', '테이스팅', '페어링', '고객서비스'], ARRAY['호텔관광학', '식품학'], 2500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 9. 공공/행정 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('321101', '일반행정직공무원', 'General Administrative Officer', '공공/행정', '행정', '정부기관에서 행정업무를 담당하는 공무원', ARRAY['행정실무', '법규이해', '민원처리', '문서작성'], ARRAY['행정학', '법학', '정치학'], 2800, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('321102', '세무직공무원', 'Tax Officer', '공공/행정', '세무', '세금 부과 및 징수를 담당하는 공무원', ARRAY['세법', '회계', '세무조사', '납세지원'], ARRAY['세무학', '회계학', '행정학'], 2800, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('321201', '경찰공무원', 'Police Officer', '공공/행정', '치안', '치안 유지 및 범죄 예방을 담당하는 공무원', ARRAY['수사', '법집행', '체력', '상황대응'], ARRAY['경찰행정학', '법학'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('321202', '소방공무원', 'Firefighter', '공공/행정', '소방', '화재 진압 및 구조 활동을 담당하는 공무원', ARRAY['화재진압', '구조', '응급처치', '체력'], ARRAY['소방학', '응급구조학'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('321301', '외교관', 'Diplomat', '공공/행정', '외교', '국가 간 외교 업무를 수행하는 공무원', ARRAY['외국어', '협상', '국제관계', '정책분석'], ARRAY['외교학', '정치외교학', '국제학'], 4000, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('321401', '군인', 'Military Officer', '공공/행정', '국방', '국가 방위를 담당하는 직업군인', ARRAY['전술', '지휘', '체력', '리더십'], ARRAY['군사학', '공학계열'], 3000, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 10. 예술/스포츠 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('291101', '배우', 'Actor', '예술/스포츠', '연기', '연극, 영화, 드라마에서 연기를 하는 전문가', ARRAY['연기', '발성', '표현력', '캐릭터분석'], ARRAY['연극영화학', '연기학'], 1500, 10000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291102', '성우', 'Voice Actor', '예술/스포츠', '연기', '애니메이션, 더빙 등 목소리 연기를 하는 전문가', ARRAY['발성', '연기', '더빙', '내레이션'], ARRAY['연극영화학', '방송학'], 2000, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291201', '가수', 'Singer', '예술/스포츠', '음악', '노래를 부르는 전문 음악인', ARRAY['보컬', '퍼포먼스', '음악이론', '작사'], ARRAY['음악학', '실용음악'], 1500, 15000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291202', '작곡가', 'Composer', '예술/스포츠', '음악', '음악을 작곡하는 전문가', ARRAY['작곡', '편곡', 'DAW', '음악이론'], ARRAY['작곡과', '실용음악'], 2000, 8000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291203', '연주자', 'Musician', '예술/스포츠', '음악', '악기를 연주하는 전문 음악인', ARRAY['악기연주', '앙상블', '음악이론', '무대공연'], ARRAY['기악과', '음악학'], 2000, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291301', '화가', 'Painter', '예술/스포츠', '미술', '그림을 그리는 미술가', ARRAY['회화기법', '색채', '구도', '창의성'], ARRAY['회화과', '미술학'], 1500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291302', '조각가', 'Sculptor', '예술/스포츠', '미술', '조각 작품을 만드는 미술가', ARRAY['조각기법', '재료이해', '공간감각', '창의성'], ARRAY['조소과', '미술학'], 1500, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('291401', '무용가', 'Dancer', '예술/스포츠', '무용', '춤을 전문으로 하는 예술가', ARRAY['무용기법', '신체표현', '안무', '체력'], ARRAY['무용과'], 1500, 4500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('292101', '프로게이머', 'Professional Gamer', '예술/스포츠', 'e스포츠', '프로 게임 대회에 참가하는 선수', ARRAY['게임실력', '전략', '팀워크', '체력관리'], ARRAY['e스포츠학'], 2000, 10000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('292201', '스포츠코치', 'Sports Coach', '예술/스포츠', '스포츠', '선수의 훈련 및 경기 전략을 지도하는 전문가', ARRAY['종목전문성', '지도법', '전략수립', '선수관리'], ARRAY['체육학', '스포츠과학'], 2500, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('292202', '스포츠트레이너', 'Athletic Trainer', '예술/스포츠', '스포츠', '선수의 체력 관리 및 재활을 담당하는 전문가', ARRAY['운동처방', '재활', '체력관리', '영양'], ARRAY['스포츠의학', '체육학'], 2500, 5000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('292203', '퍼스널트레이너', 'Personal Trainer', '예술/스포츠', '피트니스', '개인의 운동 및 체력 관리를 지도하는 전문가', ARRAY['운동지도', '영양상담', '체력측정', '동기부여'], ARRAY['체육학', '스포츠과학'], 2200, 5000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 11. 뷰티/패션 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('331101', '메이크업아티스트', 'Makeup Artist', '뷰티', '메이크업', '메이크업을 전문으로 하는 미용인', ARRAY['메이크업', '색채', '트렌드', '고객상담'], ARRAY['미용학', '뷰티학'], 2200, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('331102', '헤어디자이너', 'Hair Designer', '뷰티', '헤어', '헤어 스타일링을 전문으로 하는 미용인', ARRAY['커트', '염색', '펌', '스타일링'], ARRAY['미용학', '뷰티학'], 2000, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('331103', '피부관리사', 'Esthetician', '뷰티', '피부', '피부 관리를 전문으로 하는 미용인', ARRAY['피부관리', '마사지', '제품지식', '고객상담'], ARRAY['미용학', '피부미용'], 2000, 4000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('331104', '네일아티스트', 'Nail Artist', '뷰티', '네일', '네일 아트를 전문으로 하는 미용인', ARRAY['네일아트', '젤네일', '케어', '디자인'], ARRAY['미용학', '뷰티학'], 1800, 3500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('331201', '스타일리스트', 'Fashion Stylist', '패션', '스타일링', '패션 스타일링을 담당하는 전문가', ARRAY['패션코디', '트렌드분석', '이미지컨설팅', '촬영'], ARRAY['패션디자인', '의상학'], 2500, 6000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('331202', 'MD(패션)', 'Fashion Merchandiser', '패션', '유통', '패션 상품의 기획 및 유통을 담당하는 전문가', ARRAY['상품기획', 'VMD', '트렌드분석', '재고관리'], ARRAY['패션마케팅', '의류학'], 3000, 5500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 12. 농림수산/환경 분야 직업 코드 추가
-- ============================================
INSERT INTO tb_worknet_job (job_cd, job_nm, job_nm_en, job_category, job_subcategory, description, required_skills, related_majors, avg_salary_entry, avg_salary_experienced, job_outlook, ins_user_id, ins_dt) VALUES
('341101', '농업기술자', 'Agricultural Technician', '농림수산', '농업', '농작물 재배 및 농업 기술을 연구하는 전문가', ARRAY['재배기술', '병충해관리', '농기계', '스마트팜'], ARRAY['농학', '원예학'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('341102', '축산기술자', 'Livestock Technician', '농림수산', '축산', '가축의 사육 및 관리 기술을 담당하는 전문가', ARRAY['사육관리', '번식', '질병관리', '사료'], ARRAY['축산학', '수의학'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('341201', '수의사', 'Veterinarian', '농림수산', '수의', '동물의 질병 진단 및 치료를 담당하는 전문가', ARRAY['진단', '치료', '수술', '예방의학'], ARRAY['수의학'], 3500, 7000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('341202', '반려동물행동전문가', 'Animal Behaviorist', '농림수산', '반려동물', '반려동물의 행동 문제를 교정하는 전문가', ARRAY['행동분석', '훈련', '상담', '문제해결'], ARRAY['동물학', '심리학'], 2500, 5000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('341301', '조경관리사', 'Landscape Manager', '농림수산', '조경', '공원, 녹지의 유지관리를 담당하는 전문가', ARRAY['식물관리', '조경시공', '장비운용', '병충해관리'], ARRAY['조경학', '원예학'], 2500, 4500, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('341401', '어업기술자', 'Fishery Technician', '농림수산', '어업', '양식 및 어업 기술을 연구하는 전문가', ARRAY['양식기술', '어류관리', '수질관리', '장비운용'], ARRAY['수산학', '해양학'], 2800, 5000, 'stable', 'SYSTEM', CURRENT_TIMESTAMP),
('342101', '환경컨설턴트', 'Environmental Consultant', '환경', '환경', '환경 영향 평가 및 환경 관리를 컨설팅하는 전문가', ARRAY['환경평가', '법규', '오염관리', '보고서작성'], ARRAY['환경공학', '환경학'], 3500, 6500, 'growing', 'SYSTEM', CURRENT_TIMESTAMP),
('342102', '탄소배출관리자', 'Carbon Emission Manager', '환경', '환경', '탄소 배출량 관리 및 감축 전략을 담당하는 전문가', ARRAY['탄소회계', 'ESG', '에너지관리', '법규'], ARRAY['환경공학', '에너지공학'], 4000, 7000, 'growing', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (job_cd) DO UPDATE SET
    job_nm = EXCLUDED.job_nm,
    job_nm_en = EXCLUDED.job_nm_en,
    job_category = EXCLUDED.job_category,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 13. 추가 역할(tb_role) 등록
-- 주요 전문직 역할 추가
-- tb_role 컬럼: role_cd, role_nm, role_nm_en, category, description,
--              average_salary, growth_rate, required_competencies, required_skills,
--              worknet_code, use_fg, ins_user_id, ins_dt
-- ============================================

-- 법률 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE201', '변호사', 'Lawyer', '법률', '법률 자문 및 소송 대리 전문가', 10000, 0.02, '["법률자문", "소송대리", "계약서작성", "협상"]', '261201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE202', '판사', 'Judge', '법률', '법원에서 재판을 진행하는 법관', 9000, 0.01, '["법률해석", "판결문작성", "증거평가"]', '261101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE203', '검사', 'Prosecutor', '법률', '범죄 수사 및 기소를 담당하는 법률 전문가', 8000, 0.01, '["수사기법", "논증", "기소장작성"]', '261102', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE204', '변리사', 'Patent Attorney', '법률', '지식재산권 출원 및 분쟁 담당 전문가', 8000, 0.05, '["특허출원", "명세서작성", "심판대리"]', '261401', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- 경영/금융 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE211', '공인회계사', 'CPA', '경영/금융', '회계감사 및 경영자문 전문가', 8500, 0.02, '["회계감사", "재무제표분석", "IFRS"]', '271201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE212', '세무사', 'Tax Accountant', '경영/금융', '세무신고 대리 및 세무 자문 전문가', 6500, 0.02, '["세무신고", "절세전략", "세무조사대응"]', '271301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE213', '노무사', 'Labor Attorney', '경영/금융', '노동관계법 전문가', 6000, 0.04, '["노동법", "인사관리", "분쟁조정"]', '271101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE214', '관세사', 'Customs Broker', '경영/금융', '수출입 통관 및 관세 업무 전문가', 5500, 0.02, '["통관업무", "관세법", "FTA활용"]', '271401', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE215', '감정평가사', 'Property Appraiser', '경영/금융', '부동산 및 동산 가치 평가 전문가', 6500, 0.02, '["가치평가", "시장분석", "감정평가서작성"]', '271601', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- 교육 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE221', '중등교사', 'Secondary Teacher', '교육', '중학교 및 고등학교 교사', 4500, 0.01, '["교과지도", "학급운영", "생활지도"]', '212101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE222', '초등교사', 'Elementary Teacher', '교육', '초등학교 교사', 4500, 0.01, '["전과목지도", "학급운영", "생활지도"]', '212201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE223', '유치원교사', 'Kindergarten Teacher', '교육', '유아 교육 및 보육 담당 교사', 3200, 0.02, '["유아교육", "놀이지도", "안전관리"]', '213001', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE224', '특수교육교사', 'Special Ed Teacher', '교육', '장애학생 대상 특수교육 교사', 4500, 0.03, '["개별화교육", "치료교육", "통합교육"]', '212301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- 공학 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE231', '건축설계사', 'Architect', '건설/건축', '건축물 설계 및 감리 전문가', 5500, 0.02, '["건축설계", "CAD", "BIM"]', '231101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE232', '토목기술자', 'Civil Engineer', '건설/건축', '토목 구조물 설계/시공 전문가', 5000, 0.02, '["토목설계", "구조계산", "현장관리"]', '231201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE233', '기계설계기술자', 'Mechanical Engineer', '기계/자동차', '기계 및 장비 설계 전문가', 5500, 0.02, '["3D CAD", "기계설계", "구조해석"]', '232101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE234', '전기공학기술자', 'Electrical Engineer', '전기/전자', '전기 시스템 설계 전문가', 5500, 0.02, '["전기설계", "PLC", "전력시스템"]', '233101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE235', '반도체공학기술자', 'Semiconductor Engr', '전기/전자', '반도체 소자 및 공정 개발 전문가', 7000, 0.05, '["공정설계", "소자물리", "테스트"]', '233301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE236', '화학공학기술자', 'Chemical Engineer', '화학/에너지', '화학 공정 및 플랜트 전문가', 5500, 0.02, '["공정설계", "화학반응", "플랜트운영"]', '234101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE237', '환경공학기술자', 'Environmental Engr', '화학/에너지', '환경오염 방지 및 처리 전문가', 5000, 0.04, '["환경영향평가", "수처리", "폐기물처리"]', '234201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- 미디어/예술 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE241', 'PD', 'Producer/Director', '미디어/방송', '방송 프로그램 기획 및 제작 전문가', 6000, 0.02, '["기획력", "연출", "스토리텔링"]', '283101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE242', '기자', 'Journalist', '미디어/방송', '뉴스 취재 및 기사 작성 전문가', 4500, -0.02, '["취재", "글쓰기", "인터뷰"]', '283201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE243', '그래픽디자이너', 'Graphic Designer', '디자인', '시각 콘텐츠 제작 전문가', 4200, 0.02, '["Photoshop", "Illustrator", "타이포그래피"]', '285401', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE244', '웹디자이너', 'Web Designer', '디자인', '웹사이트 시각 디자인 전문가', 4500, 0.02, '["Figma", "HTML/CSS", "반응형디자인"]', '285501', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE245', 'UX/UI디자이너', 'UX/UI Designer', '디자인', '사용자 경험/인터페이스 설계 전문가', 5000, 0.05, '["Figma", "프로토타이핑", "사용자조사"]', '285504', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- 사회복지/상담 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE251', '사회복지사', 'Social Worker', '사회복지', '사회적 문제 해결 지원 전문가', 3200, 0.04, '["상담", "사례관리", "프로그램기획"]', '241101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE252', '상담심리사', 'Counselor', '사회복지', '심리 상담 전문가', 4000, 0.04, '["심리상담", "심리검사", "사례개념화"]', '241201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE253', '임상심리사', 'Clinical Psychologist', '사회복지', '정신건강 평가 및 치료 전문가', 4500, 0.04, '["심리평가", "치료", "진단"]', '241202', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- 공공/행정 분야 역할 추가
INSERT INTO tb_role (role_cd, role_nm, role_nm_en, category, description, average_salary, growth_rate, required_skills, worknet_code, use_fg, ins_user_id, ins_dt)
VALUES
('ROLE261', '일반행정직공무원', 'Admin Officer', '공공/행정', '정부기관 행정업무 담당 공무원', 4200, 0.01, '["행정실무", "법규이해", "민원처리"]', '321101', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE262', '경찰공무원', 'Police Officer', '공공/행정', '치안 유지 및 범죄 예방 공무원', 4000, 0.02, '["수사", "법집행", "상황대응"]', '321201', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE263', '소방공무원', 'Firefighter', '공공/행정', '화재 진압 및 구조 활동 공무원', 4000, 0.02, '["화재진압", "구조", "응급처치"]', '321202', 'Y', 'SYSTEM', CURRENT_TIMESTAMP),
('ROLE264', '외교관', 'Diplomat', '공공/행정', '국가 간 외교 업무 담당 공무원', 6000, 0.01, '["외국어", "협상", "국제관계"]', '321301', 'Y', 'SYSTEM', CURRENT_TIMESTAMP)
ON CONFLICT (role_cd) DO UPDATE SET
    role_nm = EXCLUDED.role_nm,
    worknet_code = EXCLUDED.worknet_code,
    upd_user_id = 'SYSTEM',
    upd_dt = CURRENT_TIMESTAMP;

-- ============================================
-- 14. 학과-직업 관심 매핑 추가
-- ============================================

-- 법학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    CASE
        WHEN wj.job_cd IN ('261201', '261101', '261102') THEN 5  -- 변호사, 판사, 검사
        WHEN wj.job_cd IN ('261301', '261401') THEN 4           -- 법무사, 변리사
        ELSE 3
    END as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE d.department_nm LIKE '%법학%'
  AND wj.job_category = '법률'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 회계/세무 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    CASE
        WHEN wj.job_cd IN ('271201', '271301') THEN 5  -- 회계사, 세무사
        ELSE 3
    END as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%회계%' OR d.department_nm LIKE '%세무%')
  AND wj.job_cd IN ('271201', '271301', '271401', '271501', '271502')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 사범대/교육 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    CASE
        WHEN wj.job_cd IN ('212101', '212201') THEN 5  -- 중등교사, 초등교사
        WHEN wj.job_cd = '251101' THEN 4               -- 대학교수
        ELSE 3
    END as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%교육%' OR d.department_nm LIKE '%사범%')
  AND wj.job_category = '교육'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 건축/토목 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%건축%' OR d.department_nm LIKE '%토목%')
  AND wj.job_category = '건설/건축'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 기계공학 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%기계%' OR d.department_nm LIKE '%자동차%')
  AND wj.job_category = '기계/자동차'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 전기/전자 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%전기%' OR d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%')
  AND wj.job_category = '전기/전자'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 화학/환경 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%화학%' OR d.department_nm LIKE '%환경%' OR d.department_nm LIKE '%에너지%')
  AND wj.job_category = '화학/에너지'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 디자인 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%디자인%' OR d.department_nm LIKE '%시각%' OR d.department_nm LIKE '%산업디자인%')
  AND wj.job_category = '예술/디자인'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 사회복지/심리 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%사회복지%' OR d.department_nm LIKE '%심리%' OR d.department_nm LIKE '%상담%')
  AND wj.job_category = '사회복지'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 미디어/방송 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%방송%' OR d.department_nm LIKE '%미디어%' OR d.department_nm LIKE '%신문%' OR d.department_nm LIKE '%영상%')
  AND wj.job_category = '미디어/방송'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 행정/정치 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%행정%' OR d.department_nm LIKE '%정치%' OR d.department_nm LIKE '%공공%')
  AND wj.job_category = '공공/행정'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 관광/호텔 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%관광%' OR d.department_nm LIKE '%호텔%' OR d.department_nm LIKE '%항공%')
  AND wj.job_category = '관광/서비스'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 조리/식품 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%조리%' OR d.department_nm LIKE '%식품%' OR d.department_nm LIKE '%영양%' OR d.department_nm LIKE '%제과%')
  AND wj.job_category = '식음료'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 뷰티/미용 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%미용%' OR d.department_nm LIKE '%뷰티%' OR d.department_nm LIKE '%피부%')
  AND wj.job_category = '뷰티'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 패션/의류 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%패션%' OR d.department_nm LIKE '%의류%' OR d.department_nm LIKE '%의상%')
  AND wj.job_category = '패션'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 수의/동물 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%수의%' OR d.department_nm LIKE '%동물%')
  AND wj.job_cd IN ('341201', '341202')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 체육/스포츠 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%체육%' OR d.department_nm LIKE '%스포츠%')
  AND wj.job_category = '예술/스포츠'
  AND wj.job_subcategory IN ('스포츠', '피트니스', 'e스포츠')
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 음악/예술 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%음악%' OR d.department_nm LIKE '%작곡%' OR d.department_nm LIKE '%기악%' OR d.department_nm LIKE '%성악%' OR d.department_nm LIKE '%실용음악%')
  AND wj.job_category = '예술/스포츠'
  AND wj.job_subcategory = '음악'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- 연극/영화 관련 학과 학생 관심 직업 매핑
INSERT INTO tb_student_interested_job (student_id, job_cd, interest_level, ins_user_id, ins_dt)
SELECT
    s.student_id,
    wj.job_cd,
    5 as interest_level,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
CROSS JOIN tb_worknet_job wj
WHERE (d.department_nm LIKE '%연극%' OR d.department_nm LIKE '%영화%' OR d.department_nm LIKE '%연기%')
  AND wj.job_category = '예술/스포츠'
  AND wj.job_subcategory = '연기'
ON CONFLICT (student_id, job_cd) DO NOTHING;

-- ============================================
-- 15. 성공 패턴 추가 (실제 테이블 구조 반영)
-- ============================================

-- 법학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 변호사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE201',
    '법학전문대학원을 통한 변호사 취업 경로. LEET 준비와 학점 관리가 중요',
    '3.8-4.5',
    ARRAY['헌법', '민법', '형법', '행정법', '상법']::varchar(100)[],
    ARRAY['법학전문대학원 진학', '변호사시험 합격', '로펌/기업법무 인턴', '모의재판 참가', '법률봉사활동']::varchar(200)[],
    ARRAY['법률해석', '논증력', '문서작성', '의사소통']::varchar(100)[],
    '{"1학년": "기초법학 이수", "2학년": "전공심화 및 LEET 준비", "3학년": "법전원 진학", "4-6년차": "법전원 과정", "7년차": "변호사시험 및 취업"}'::jsonb,
    0.35,
    150,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%법학%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 회계학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 공인회계사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE202',
    '공인회계사 시험을 통한 Big4 회계법인 취업 경로',
    '3.5-4.5',
    ARRAY['회계원리', '재무회계', '원가관리회계', '세법', '감사론']::varchar(100)[],
    ARRAY['CPA 시험 준비', '회계법인 인턴', '재무/회계 관련 자격증', '영어 능력 향상', '전산회계 실습']::varchar(200)[],
    ARRAY['재무분석', '감사', '세무', '회계처리']::varchar(100)[],
    '{"1학년": "회계원리 기초", "2학년": "CPA 1차 준비", "3학년": "CPA 2차 도전", "4학년": "인턴 및 취업준비"}'::jsonb,
    0.25,
    200,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%회계%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 교육학과/사범대 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 중등교사 임용 패턴',
    '취업',
    d.department_cd,
    'ROLE205',
    '교원임용시험을 통한 중등교사 취업 경로',
    '3.5-4.3',
    ARRAY['교육학개론', '교육심리학', '교육과정', '교육평가', '교과교육론']::varchar(100)[],
    ARRAY['교직이수', '교육실습', '임용시험 준비', '교과지도 역량', '생활지도 경험']::varchar(200)[],
    ARRAY['수업설계', '학생지도', '학급운영', '의사소통']::varchar(100)[],
    '{"1-2학년": "교직기초 이수", "3학년": "교육실습", "4학년": "임용시험 준비", "졸업후": "임용시험 응시"}'::jsonb,
    0.30,
    180,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE (d.department_nm LIKE '%교육%' OR d.department_nm LIKE '%사범%')
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 건축학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 건축설계사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE206',
    '건축설계사무소 취업 후 건축사 자격 취득 경로',
    '3.3-4.0',
    ARRAY['건축설계', '건축구조', '건축환경', 'CAD실습', '건축법규']::varchar(100)[],
    ARRAY['건축사 자격 취득', '설계사무소 인턴', '포트폴리오 구축', 'CAD/BIM 역량', '공모전 참가']::varchar(200)[],
    ARRAY['설계능력', 'CAD/BIM', '공간분석', '프레젠테이션']::varchar(100)[],
    '{"1-2학년": "CAD 숙달 및 기초설계", "3학년": "인턴 및 공모전", "4학년": "포트폴리오", "졸업후": "실무경력 후 건축사 시험"}'::jsonb,
    0.40,
    120,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%건축%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 전자공학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 반도체공학기술자 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE208',
    '삼성/SK 등 반도체 대기업 취업 경로',
    '3.5-4.2',
    ARRAY['반도체공학', '전자회로', '디지털시스템', '집적회로', '반도체소자']::varchar(100)[],
    ARRAY['반도체 공정 이론', '클린룸 실습', '대기업 인턴', '관련 자격증', '영어 능력']::varchar(200)[],
    ARRAY['반도체공정', '회로설계', '측정분석', '문제해결']::varchar(100)[],
    '{"1-2학년": "기초이론 학습", "3학년": "실습 및 프로젝트", "4학년": "인턴십 및 취업준비"}'::jsonb,
    0.50,
    250,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE (d.department_nm LIKE '%전자%' OR d.department_nm LIKE '%반도체%')
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 디자인학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → UX/UI디자이너 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE217',
    'IT 기업 및 스타트업 UX/UI 디자이너 취업 경로',
    '3.2-4.0',
    ARRAY['시각디자인', 'UI/UX디자인', '인터랙션디자인', '디지털미디어', '타이포그래피']::varchar(100)[],
    ARRAY['Figma 숙달', '사용자 조사 경험', '포트폴리오 구축', 'IT 기업 인턴', '공모전 수상']::varchar(200)[],
    ARRAY['Figma', '사용자조사', '프로토타이핑', '시각디자인']::varchar(100)[],
    '{"1-2학년": "디자인 툴 학습", "3학년": "프로젝트 및 인턴", "4학년": "포트폴리오 완성 및 취업"}'::jsonb,
    0.45,
    100,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%디자인%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 사회복지학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 사회복지사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE227',
    '사회복지시설/기관 취업 경로',
    '3.0-4.0',
    ARRAY['사회복지개론', '사회복지실천론', '사례관리', '지역사회복지론', '사회복지정책론']::varchar(100)[],
    ARRAY['사회복지사 자격증', '현장실습', '사례관리 경험', '프로그램 기획', '봉사활동']::varchar(200)[],
    ARRAY['사례관리', '상담', '프로그램기획', '자원연계']::varchar(100)[],
    '{"1-2학년": "필수과목 이수", "3학년": "현장실습", "4학년": "자격증 취득 및 취업"}'::jsonb,
    0.60,
    200,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%사회복지%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 심리학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 상담심리사 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE228',
    '상담센터/병원 상담사 취업 경로 (대학원 필수)',
    '3.5-4.3',
    ARRAY['상담심리학', '임상심리학', '발달심리학', '이상심리학', '심리검사']::varchar(100)[],
    ARRAY['상담심리사 자격증', '상담 수련', '심리검사 역량', '대학원 진학', '임상 경험']::varchar(200)[],
    ARRAY['심리상담', '심리검사', '사례개념화', '치료계획']::varchar(100)[],
    '{"1-2학년": "심리학 이론", "3-4학년": "대학원 준비", "대학원": "전문수련", "졸업후": "자격취득 및 취업"}'::jsonb,
    0.35,
    80,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%심리%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

-- 행정학과 성공 패턴
INSERT INTO tb_success_pattern (pattern_nm, pattern_type, department_cd, role_cd, description, typical_gpa_range, key_courses, key_activities, key_skills, timeline, success_rate, sample_size, ins_user_id, ins_dt)
SELECT
    d.department_nm || ' → 일반행정직공무원 취업 패턴',
    '취업',
    d.department_cd,
    'ROLE230',
    '9급/7급 공무원 시험을 통한 공직 진출 경로',
    '3.3-4.0',
    ARRAY['행정학개론', '행정법', '정책학', '조직론', '지방행정론']::varchar(100)[],
    ARRAY['공무원시험 준비', '행정법/행정학 심화', '한국사 자격증', '영어 성적', '면접 준비']::varchar(200)[],
    ARRAY['행정실무', '법률해석', '정책분석', '민원응대']::varchar(100)[],
    '{"1-2학년": "기초과목 이수", "3-4학년": "공무원시험 기초준비", "졸업후": "집중 준비 및 시험 합격"}'::jsonb,
    0.20,
    300,
    'SYSTEM',
    CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm LIKE '%행정%'
  AND d.use_fg = 'Y'
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================
-- 검증 쿼리
-- ============================================
-- SELECT job_category, COUNT(*) as cnt FROM tb_worknet_job GROUP BY job_category ORDER BY cnt DESC;
-- SELECT category, COUNT(*) as cnt FROM tb_role GROUP BY category ORDER BY cnt DESC;
-- SELECT COUNT(*) FROM tb_student_interested_job;
-- SELECT COUNT(*) FROM tb_success_pattern;
