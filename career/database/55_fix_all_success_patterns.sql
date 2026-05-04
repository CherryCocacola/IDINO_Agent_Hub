-- =============================================================
-- 55_fix_all_success_patterns.sql
-- 전체 학과 성공 패턴 확장 (LIMIT 1 제거, 30개 학과 커버)
-- 기존 FIX_CAREER_GOAL 패턴 삭제 후 재생성
-- =============================================================
SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 기존 FIX_CAREER_GOAL 패턴 삭제
-- =====================================================
DELETE FROM tb_success_pattern WHERE ins_user_id = 'FIX_CAREER_GOAL';
DELETE FROM tb_success_pattern WHERE ins_user_id = 'FIX_ALL_PATTERNS';

-- =====================================================
-- Part 1: 스포츠/체육 계열 (모든 해당 학과에 패턴 추가)
-- =====================================================

-- 스포츠트레이너 취업 성공 패턴 (LIMIT 없이 모든 스포츠/체육 학과)
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '스포츠트레이너 취업 성공 패턴',
    'career',
    '생활체육지도사 2급 + 현장실습 + 운동처방 역량을 갖춘 졸업생의 취업 성공 패턴',
    '3.0-4.0',
    ARRAY['운동생리학', '운동처방론', '스포츠의학', '체력측정평가', '트레이닝방법론'],
    ARRAY['생활체육지도사 2급 취득', '스포츠센터 현장실습', '재활센터 인턴십', '체육대회 봉사'],
    ARRAY['운동처방', '체력측정', '재활운동', '트레이닝', '응급처치'],
    '{"1학년": "기초체육과학", "2학년": "전공심화+자격증준비", "3학년": "현장실습+자격증취득", "4학년": "취업준비"}',
    78.5, 85,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '스포츠|헬스케어|체육|운동';

-- 운동처방사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '운동처방사 취업 성공 패턴',
    'career',
    '건강운동관리사 자격 + 임상실습을 통한 운동처방 전문가 경로',
    '3.2-4.2',
    ARRAY['운동처방론', '병태생리학', '운동검사법', '운동영양학', '건강체력평가'],
    ARRAY['건강운동관리사 취득', '병원 임상실습', '재활센터 인턴십', '건강관리 봉사'],
    ARRAY['운동처방', '건강평가', '재활운동', '환자상담', '체력측정'],
    '{"1학년": "기초의학지식", "2학년": "운동과학심화", "3학년": "자격증+임상실습", "4학년": "취업+전문성강화"}',
    75.0, 60,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '스포츠|헬스케어|체육|운동';

-- 건강운동관리사 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '건강운동관리사 취업 성공 패턴',
    'career',
    '건강운동관리사 국가자격 취득 후 병원/센터 취업 경로',
    '3.0-4.0',
    ARRAY['운동생리학', '건강체력평가', '운동처방론', '스포츠심리학', '운동영양학'],
    ARRAY['건강운동관리사 자격 취득', '피트니스센터 실습', '병원 운동치료실 인턴', '생활체육 봉사'],
    ARRAY['운동프로그램설계', '건강평가', '운동지도', '동기부여', '안전관리'],
    '{"1학년": "기초과학", "2학년": "전공심화", "3학년": "자격증준비+실습", "4학년": "취업준비"}',
    72.0, 55,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '스포츠|헬스케어|체육|운동';

-- =====================================================
-- Part 2: 보건의료 계열
-- =====================================================

-- 간호사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '간호사 취업 성공 패턴',
    'career',
    '간호사 국가고시 합격 후 종합병원 취업 성공 경로',
    '3.5-4.5',
    ARRAY['기본간호학', '성인간호학', '아동간호학', '정신간호학', '지역사회간호학'],
    ARRAY['간호사 국가고시 합격', '임상실습 1000시간', 'BLS/ACLS 취득', '병원 봉사활동'],
    ARRAY['환자간호', '투약관리', '응급처치', '의사소통', '팀워크'],
    '{"1학년": "기초의학", "2학년": "전공심화", "3학년": "임상실습+국시준비", "4학년": "국시합격+취업"}',
    92.0, 200,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '간호';

-- 물리치료사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '물리치료사 취업 성공 패턴',
    'career',
    '물리치료사 국가고시 합격 후 재활병원 취업 경로',
    '3.3-4.3',
    ARRAY['근골격계물리치료', '신경계물리치료', '운동치료학', '전기치료학', '재활의학'],
    ARRAY['물리치료사 국가고시 합격', '재활병원 실습', '스포츠재활 인턴십', '도수치료 자격과정'],
    ARRAY['도수치료', '운동치료', '전기치료', '환자평가', '재활계획'],
    '{"1학년": "기초의학", "2학년": "전공심화", "3학년": "임상실습+국시준비", "4학년": "국시합격+취업"}',
    88.0, 120,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '물리치료';

-- 임상병리사 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '임상병리사 취업 성공 패턴',
    'career',
    '임상병리사 국가고시 합격 후 병원 검사실 취업 경로',
    '3.3-4.3',
    ARRAY['임상화학', '혈액학', '미생물학', '조직병리학', '면역학'],
    ARRAY['임상병리사 국가고시 합격', '병원 검사실 실습', '학술대회 참가', '연구 프로젝트'],
    ARRAY['검체분석', '혈액검사', '미생물배양', '품질관리', '의료정보'],
    '{"1학년": "기초과학", "2학년": "전공심화", "3학년": "임상실습+국시준비", "4학년": "국시합격+취업"}',
    85.0, 90,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '임상병리|병리';

-- 보건/방사선/치위생/응급 등 보건의료 일반
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '보건의료 전문직 취업 성공 패턴',
    'career',
    '보건의료 국가면허 취득 후 의료기관 취업 성공 경로',
    '3.2-4.2',
    ARRAY['해부학', '생리학', '공중보건학', '의료법규', '보건통계학'],
    ARRAY['국가면허 취득', '의료기관 임상실습', '보건의료 봉사', '학술대회 참가'],
    ARRAY['환자관리', '의료기기', '감염관리', '의사소통', '의료윤리'],
    '{"1학년": "기초의학", "2학년": "전공심화", "3학년": "임상실습+면허준비", "4학년": "면허취득+취업"}',
    82.0, 100,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '보건|방사선|치위생|치기공|응급'
  AND d.department_nm !~ '스포츠|헬스케어|체육|운동|간호|물리치료|임상병리';

-- =====================================================
-- Part 3: 교육 계열
-- =====================================================

-- 교원임용 합격 패턴 (모든 교육학과)
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '교원임용 합격 패턴',
    'career',
    '교원임용시험 합격을 위한 체계적 준비 경로',
    '3.5-4.5',
    ARRAY['교육학개론', '교육심리학', '교육과정론', '교육방법및교육공학', '교육평가'],
    ARRAY['교원임용시험 준비', '교육실습', '교육봉사 100시간', '교과연구회 참여'],
    ARRAY['교육과정설계', '학생지도', '수업설계', '교육평가', '학급운영'],
    '{"1학년": "교직기초과목", "2학년": "전공교육학심화", "3학년": "임용준비+교육실습", "4학년": "임용시험+교생실습"}',
    72.0, 150,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '교육|사범|유아교육|특수교육';

-- 상담전문가 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '상담전문가 취업 성공 패턴',
    'career',
    '상담심리사 자격 취득 후 상담센터/학교 취업 경로',
    '3.3-4.3',
    ARRAY['상담심리학', '발달심리학', '이상심리학', '집단상담', '상담실습'],
    ARRAY['상담심리사 2급 취득', '상담센터 인턴십', '상담봉사 활동', '사례발표회 참가'],
    ARRAY['개인상담', '집단상담', '심리평가', '위기개입', '사례관리'],
    '{"1학년": "심리학기초", "2학년": "상담이론심화", "3학년": "상담실습+자격준비", "4학년": "자격취득+취업"}',
    68.0, 80,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '상담|심리|사회복지|발달';

-- =====================================================
-- Part 4: 예술/디자인 계열
-- =====================================================

-- 디자이너 취업 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '디자이너 취업 성공 패턴',
    'career',
    '포트폴리오 + 공모전 수상 + 에이전시 인턴십을 통한 디자이너 취업 경로',
    '3.0-4.0',
    ARRAY['시각디자인', 'UI/UX디자인', '타이포그래피', '브랜딩디자인', '디지털미디어'],
    ARRAY['GTQ 1급 취득', '디자인 공모전 수상', '에이전시 인턴십', '포트폴리오 전시'],
    ARRAY['그래픽디자인', '영상편집', 'UI설계', '포트폴리오', 'Adobe도구'],
    '{"1학년": "기초디자인", "2학년": "전공심화+공모전", "3학년": "인턴십+포트폴리오", "4학년": "취업+졸업전시"}',
    70.0, 110,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '디자인|시각|웹툰|멀티미디어|영상|미디어|애니메이션';

-- 음악/공연 분야 성공 패턴
INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '공연예술 전문가 성공 패턴',
    'career',
    '공연 경험 + 교육자격 취득을 통한 예술분야 취업 경로',
    '3.0-4.0',
    ARRAY['음악이론', '실기레슨', '앙상블', '음악교육론', '공연기획'],
    ARRAY['정기연주회 참가', '외부 공연 경력', '음악지도사 취득', '예술봉사 활동'],
    ARRAY['연주실기', '합주', '음악교육', '공연기획', '예술행정'],
    '{"1학년": "기초실기+이론", "2학년": "전공심화+공연참가", "3학년": "외부활동+자격취득", "4학년": "졸업연주+진로확정"}',
    65.0, 70,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '음악|공연|예술'
  AND d.department_nm !~ '디자인|시각|웹툰|멀티미디어|영상|미디어|애니메이션';

-- =====================================================
-- Part 5: 경영/경제 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '경영전문가 취업 성공 패턴',
    'career',
    '전문자격증 + 기업 인턴십을 통한 경영분야 취업 경로',
    '3.3-4.3',
    ARRAY['경영학원론', '마케팅원론', '재무관리', '인적자원관리', '전략경영'],
    ARRAY['전문자격증 취득(CPA/경영지도사)', '기업 인턴십', '비즈니스 공모전 참가', '해외연수'],
    ARRAY['재무분석', '마케팅전략', '데이터분석', '프레젠테이션', '비즈니스영어'],
    '{"1학년": "경영기초", "2학년": "전공심화+자격준비", "3학년": "인턴십+공모전", "4학년": "취업준비+자격취득"}',
    75.0, 180,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '경영|경제|회계|통상|무역|물류|마케팅|금융|세무';

-- =====================================================
-- Part 6: IT/컴퓨터 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    'IT개발자 취업 성공 패턴',
    'career',
    '프로젝트 포트폴리오 + 인턴십을 통한 개발자 취업 경로',
    '3.0-4.0',
    ARRAY['프로그래밍기초', '자료구조', '알고리즘', '데이터베이스', '소프트웨어공학'],
    ARRAY['개인 프로젝트 포트폴리오 구축', 'IT 기업 인턴십', '해커톤/공모전 참가', '오픈소스 기여'],
    ARRAY['프로그래밍', '웹개발', '데이터베이스', '클라우드', '협업도구'],
    '{"1학년": "프로그래밍기초", "2학년": "전공심화+프로젝트", "3학년": "인턴십+포트폴리오", "4학년": "취업준비"}',
    82.0, 200,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '컴퓨터|AI|소프트웨어|정보|게임|반도체|전자|정보통신';

-- =====================================================
-- Part 7: 공학 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '공학엔지니어 취업 성공 패턴',
    'career',
    '기사자격증 + 산학협력 프로젝트를 통한 엔지니어 취업 경로',
    '3.2-4.2',
    ARRAY['공학수학', '재료역학', '열역학', 'CAD/CAM', '품질관리'],
    ARRAY['기사자격증 취득', '산학협력 프로젝트', '현장실습', '졸업설계 프로젝트'],
    ARRAY['설계', 'CAD/CAM', '품질관리', '안전관리', '프로젝트관리'],
    '{"1학년": "기초공학수학", "2학년": "전공심화+설계", "3학년": "자격증+현장실습", "4학년": "졸업설계+취업"}',
    80.0, 170,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '기계|전기|산업|건축|건설|로봇|나노|화공|재료|배터리|소방|스마트물류'
  AND d.department_nm !~ '컴퓨터|AI|소프트웨어|정보|게임|반도체|전자|정보통신';

-- =====================================================
-- Part 8: 사회과학/법학 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '사회과학 전문직 취업 성공 패턴',
    'career',
    '자격증 + 현장실습을 통한 사회과학분야 전문직 취업 경로',
    '3.3-4.3',
    ARRAY['사회학개론', '행정학개론', '법학개론', '정책학', '통계학'],
    ARRAY['관련 자격증 취득', '공공기관 인턴십', '봉사활동', '정책공모전 참가'],
    ARRAY['정책분석', '법률해석', '사회조사', '문서작성', '의사소통'],
    '{"1학년": "기초이론", "2학년": "전공심화", "3학년": "자격증+인턴십", "4학년": "공무원시험/취업준비"}',
    70.0, 130,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '법학|경찰|행정|정치|사회'
  AND d.department_nm !~ '사회복지|상담|심리';

-- =====================================================
-- Part 9: 인문학 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '인문학 전문가 취업 성공 패턴',
    'career',
    '어학자격 + 인턴십을 통한 인문분야 취업 경로',
    '3.3-4.3',
    ARRAY['인문학개론', '논리학', '글쓰기', '어학과목', '비교문화론'],
    ARRAY['어학자격증 취득(TOEIC 900+)', '관련 기관 인턴십', '해외연수', '학술논문 발표'],
    ARRAY['외국어', '글쓰기', '비판적사고', '문화이해', '커뮤니케이션'],
    '{"1학년": "기초교양+어학", "2학년": "전공심화+자격준비", "3학년": "인턴십+연구", "4학년": "취업/대학원진학"}',
    65.0, 100,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '어문|인문|역사|문화콘텐츠|문화유산|영어영문|통일|철학|국문';

-- =====================================================
-- Part 10: 자연과학 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '자연과학 연구직 성공 패턴',
    'career',
    '연구 경험 + 대학원/기업연구소 취업 경로',
    '3.5-4.5',
    ARRAY['일반화학', '일반물리학', '미적분학', '통계학', '실험과목'],
    ARRAY['연구실 참여(학부연구생)', '학술대회 발표', '연구 논문 공저', '관련 자격증 취득'],
    ARRAY['실험설계', '데이터분석', '논문작성', '통계소프트웨어', '연구윤리'],
    '{"1학년": "기초과학", "2학년": "전공심화+연구실참여", "3학년": "연구+학회발표", "4학년": "졸업논문+진로확정"}',
    70.0, 90,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '수학|물리|화학|생명과학|통계|환경|바이오|신소재|식품';

-- =====================================================
-- Part 11: 외국어 계열
-- =====================================================

INSERT INTO tb_success_pattern (
    pattern_id, department_cd, pattern_nm, pattern_type, description,
    typical_gpa_range, key_courses, key_activities, key_skills,
    timeline, success_rate, sample_size,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    d.department_cd,
    '국제전문가 취업 성공 패턴',
    'career',
    '어학 능력 + 해외경험을 통한 국제분야 취업 경로',
    '3.3-4.3',
    ARRAY['회화', '통번역실습', '비즈니스커뮤니케이션', '지역학', '국제관계론'],
    ARRAY['어학자격증 최고급 취득', '해외교환학생', '국제기구 인턴십', '통역봉사'],
    ARRAY['외국어구사', '통번역', '이문화소통', '국제비즈니스', '프레젠테이션'],
    '{"1학년": "어학기초강화", "2학년": "전공심화+해외준비", "3학년": "해외연수+인턴십", "4학년": "취업준비"}',
    73.0, 95,
    'FIX_ALL_PATTERNS', CURRENT_TIMESTAMP
FROM tb_department d
WHERE d.department_nm ~ '국제|외국어'
  AND d.department_nm !~ '영어영문|어문';

COMMIT;
