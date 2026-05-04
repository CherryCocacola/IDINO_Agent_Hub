-- =====================================================
-- 48_e2e_showcase_students.sql
-- E2E 테스트용 쇼케이스 학생 데이터 생성
-- 2020-2021 입학 4학년 학생 중 과별 2명씩 (~60명) 선정
-- 모든 빈 테이블에 다양한 데이터를 채워 전 API가 데이터를 반환하도록 함
-- =====================================================
-- 채우는 테이블 (15개):
--   1.  tb_roadmap_item              (8건/학생)
--   2.  tb_coaching_checkin          (12건/학생 = 4회×3목표)
--   3.  tb_coaching_retrospective    (~2건/학생, completed 목표만)
--   4a. tb_assessment                (2건/학생)
--   4b. tb_assessment_result         (12건/학생 = 6comp×2)
--   5.  tb_opportunity_recommendation (5건/학생)
--   6.  tb_opportunity_application    (2건/학생)
--   7.  tb_skill_passport            (1건/학생)
--   8.  tb_advisor_intervention      (2건/학생)
--   9.  tb_advisor_note              (3건/학생)
--  10.  tb_scenario_comparison       (1건/학생)
--  11a. tb_recommendation_run        (1건/학생)
--  11b. tb_recommendation_item       (3건/학생)
--  11c. tb_recommendation_evidence   (6건/학생)
--  12.  tb_feedback_event            (1건/학생)
--  13.  tb_worknet_diagnosis         (1건/학생)
--  14.  tb_constraint_check          (3건/학생)
--  합계: ~65건/학생, 총 ~3,900건
-- =====================================================

SET search_path TO idino_career, public;

BEGIN;

-- =====================================================
-- Part 0: 대상 학생 선정
-- 2020-2021 입학 학생 중 기존 데이터가 가장 많은 상위 2명/학과
-- =====================================================

CREATE TEMP TABLE tmp_dept_cat_48 AS
SELECT
    d.department_cd,
    d.department_nm,
    CASE
        WHEN d.department_nm ~ '의예|의학' THEN 'medical'
        WHEN d.department_nm ~ '간호' THEN 'nursing'
        WHEN d.department_nm ~ '약학|약' THEN 'pharmacy'
        WHEN d.department_nm ~ '보건|치위생|치기공|물리치료|작업치료|방사선|임상병리|응급구조|의공학|재활|언어치료' THEN 'health'
        WHEN d.department_nm ~ '컴퓨터|소프트웨어|AI|인공지능|데이터|IT|정보통신|정보보안|멀티미디어|게임|웹툰영상' THEN 'it_engineering'
        WHEN d.department_nm ~ '건축' THEN 'architecture'
        WHEN d.department_nm ~ '토목|건설환경|건설' THEN 'civil_eng'
        WHEN d.department_nm ~ '기계|자동차|기계자동차|로봇' THEN 'mechanical'
        WHEN d.department_nm ~ '전자|전기|반도체|배터리' THEN 'electrical'
        WHEN d.department_nm ~ '화학공학|환경공학|에너지|나노|신소재|융합기술' THEN 'chemical_env'
        WHEN d.department_nm ~ '산업공학|산업경영|산업|스마트물류|소방' THEN 'industrial'
        WHEN d.department_nm ~ '경영|경제|회계|무역|금융|마케팅|국제통상|관광|호텔' THEN 'business'
        WHEN d.department_nm ~ '법학|행정|정치|외교|공공|경찰' THEN 'law_admin'
        WHEN d.department_nm ~ '교육|사범|유아|특수교육|상담|사회복지|발달' THEN 'education'
        WHEN d.department_nm ~ '국어|영어|일어|중국어|불어|독어|철학|사학|문학|어문|문헌정보|인문|역사|문화콘텐츠|문화유산' THEN 'humanities'
        WHEN d.department_nm ~ '디자인|미술|음악|영화|연극|애니메이션|만화|패션|공예|공연|미디어' THEN 'arts'
        WHEN d.department_nm ~ '수학|물리|화학|생물|생명|식품|통계|지구|해양|천문|환경' THEN 'science'
        ELSE 'general'
    END AS category
FROM tb_department d;

CREATE INDEX idx_tmp_dept_cat_48 ON tmp_dept_cat_48(department_cd);

CREATE TEMP TABLE tmp_showcase_48 AS
WITH student_counts AS (
    SELECT
        s.student_id,
        s.student_nm,
        s.department_cd,
        s.admission_year,
        dc.category,
        dc.department_nm,
        abs(hashtext(s.student_id)) % 100 AS h,
        (SELECT count(*) FROM tb_grade g WHERE g.student_id = s.student_id)
        + (SELECT count(*) FROM tb_student_skill ss WHERE ss.student_id = s.student_id)
        + (SELECT count(*) FROM tb_portfolio p WHERE p.student_id = s.student_id)
        + (SELECT count(*) FROM tb_coaching_goal cg WHERE cg.std_id = s.student_id)
        + (SELECT count(*) FROM tb_student_competency sc WHERE sc.student_id = s.student_id)
        + (SELECT count(*) FROM tb_simulation_scenario sim WHERE sim.student_id = s.student_id)
        + (SELECT count(*) FROM tb_roadmap r WHERE r.student_id = s.student_id)
        + (SELECT count(*) FROM tb_student_badge sb WHERE sb.student_id = s.student_id)
        + (SELECT count(*) FROM tb_risk_alert ra WHERE ra.student_id = s.student_id)
        + (SELECT count(*) FROM tb_achievement a WHERE a.student_id = s.student_id)
        AS data_count
    FROM tb_student s
    JOIN tmp_dept_cat_48 dc ON s.department_cd = dc.department_cd
    WHERE s.admission_year IN (2020, 2021)
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY department_cd
               ORDER BY data_count DESC, student_id
           ) AS rn
    FROM student_counts
)
SELECT student_id, student_nm, department_cd, admission_year,
       category, department_nm, h, data_count
FROM ranked
WHERE rn <= 2;

CREATE INDEX idx_tmp_showcase_48_sid ON tmp_showcase_48(student_id);
CREATE INDEX idx_tmp_showcase_48_cat ON tmp_showcase_48(category);

DO $$ BEGIN
    RAISE NOTICE 'Part 0 완료: 쇼케이스 학생 선정 (% 명, % 학과)',
        (SELECT count(*) FROM tmp_showcase_48),
        (SELECT count(DISTINCT department_cd) FROM tmp_showcase_48);
END $$;


-- =====================================================
-- Part 1: tb_roadmap_item (8건/학생)
-- 기존 tb_roadmap 헤더의 roadmap_id 참조
-- =====================================================

CREATE TEMP TABLE tmp_roadmap_items_48 (
    seq INT,
    target_grade INT,
    target_semester INT,
    cat VARCHAR(50),
    cat_key VARCHAR(20),
    title VARCHAR(200),
    description TEXT
);

INSERT INTO tmp_roadmap_items_48 VALUES
    (1, 3, 1, 'course',        'ALL', '', '전공 심화 과목 이수를 통한 학문적 역량 강화'),
    (2, 3, 1, 'certification', 'ALL', '', '전문 자격증 취득을 통한 경쟁력 확보'),
    (3, 3, 2, 'skill',         'ALL', '', '실무 역량 개발 및 전문성 심화'),
    (4, 3, 2, 'activity',      'ALL', '', '대외활동 참여를 통한 경험 확장'),
    (5, 4, 1, 'course',        'ALL', '', '전공 심화 과목 이수를 통한 학문적 역량 강화'),
    (6, 4, 1, 'internship',    'ALL', '', '현장 실습을 통한 실무 경험 확보'),
    (7, 4, 2, 'certification', 'ALL', '', '전문 자격증 취득을 통한 경쟁력 확보'),
    (8, 4, 2, 'skill',         'ALL', '', '실무 역량 개발 및 전문성 심화');

INSERT INTO tb_roadmap_item (
    item_id, roadmap_id, category, title, description,
    target_grade, target_semester, status, priority, display_order,
    due_date, completed_date, notes,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    r.roadmap_id,
    ri.cat,
    CASE ri.cat
      WHEN 'course' THEN
        CASE ts.category
          WHEN 'medical'       THEN CASE ri.seq WHEN 1 THEN '기초의학 심화 수강' ELSE '임상의학 실습' END
          WHEN 'nursing'       THEN CASE ri.seq WHEN 1 THEN '간호학 심화 수강' ELSE '임상간호 실습' END
          WHEN 'pharmacy'      THEN CASE ri.seq WHEN 1 THEN '약물치료학 수강' ELSE '임상약학 실습' END
          WHEN 'health'        THEN CASE ri.seq WHEN 1 THEN '보건학 심화 수강' ELSE '보건의료 실습' END
          WHEN 'it_engineering' THEN CASE ri.seq WHEN 1 THEN '알고리즘 심화 수강' ELSE '소프트웨어공학 실습' END
          WHEN 'architecture'  THEN CASE ri.seq WHEN 1 THEN '건축설계 심화 수강' ELSE '건축시공학 실습' END
          WHEN 'civil_eng'     THEN CASE ri.seq WHEN 1 THEN '구조역학 심화 수강' ELSE '토목설계 실습' END
          WHEN 'mechanical'    THEN CASE ri.seq WHEN 1 THEN '기계설계 심화 수강' ELSE '열유체공학 실습' END
          WHEN 'electrical'    THEN CASE ri.seq WHEN 1 THEN '전자회로 심화 수강' ELSE '반도체공학 실습' END
          WHEN 'chemical_env'  THEN CASE ri.seq WHEN 1 THEN '화학공정 심화 수강' ELSE '환경공학 실습' END
          WHEN 'industrial'    THEN CASE ri.seq WHEN 1 THEN '생산관리 심화 수강' ELSE '품질공학 실습' END
          WHEN 'business'      THEN CASE ri.seq WHEN 1 THEN '경영전략 수강' ELSE '재무관리 실습' END
          WHEN 'law_admin'     THEN CASE ri.seq WHEN 1 THEN '법학 심화 수강' ELSE '행정법 실습' END
          WHEN 'education'     THEN CASE ri.seq WHEN 1 THEN '교육학 심화 수강' ELSE '교육실습' END
          WHEN 'humanities'    THEN CASE ri.seq WHEN 1 THEN '인문학 심화 수강' ELSE '문헌연구 실습' END
          WHEN 'arts'          THEN CASE ri.seq WHEN 1 THEN '예술 심화 수강' ELSE '디자인 스튜디오' END
          WHEN 'science'       THEN CASE ri.seq WHEN 1 THEN '전공실험 심화 수강' ELSE '연구방법론 실습' END
          ELSE CASE ri.seq WHEN 1 THEN '전공 심화 수강' ELSE '전공 실습' END
        END
      WHEN 'certification' THEN
        CASE ts.category
          WHEN 'medical'       THEN CASE ri.seq WHEN 2 THEN '의료정보관리사 취득' ELSE 'BLS 자격증 취득' END
          WHEN 'nursing'       THEN CASE ri.seq WHEN 2 THEN 'BLS/ACLS 취득' ELSE '전문간호사 준비' END
          WHEN 'pharmacy'      THEN CASE ri.seq WHEN 2 THEN '약사면허 준비' ELSE '임상시험 자격' END
          WHEN 'health'        THEN CASE ri.seq WHEN 2 THEN '보건의료정보관리사' ELSE '위생사 자격' END
          WHEN 'it_engineering' THEN CASE ri.seq WHEN 2 THEN '정보처리기사 취득' ELSE 'AWS 자격증 취득' END
          WHEN 'architecture'  THEN CASE ri.seq WHEN 2 THEN '건축기사 준비' ELSE 'BIM 자격증 취득' END
          WHEN 'civil_eng'     THEN CASE ri.seq WHEN 2 THEN '토목기사 준비' ELSE '측량기사 취득' END
          WHEN 'mechanical'    THEN CASE ri.seq WHEN 2 THEN '일반기계기사 준비' ELSE 'CAD 자격증' END
          WHEN 'electrical'    THEN CASE ri.seq WHEN 2 THEN '전자기사 준비' ELSE '임베디드 자격' END
          WHEN 'chemical_env'  THEN CASE ri.seq WHEN 2 THEN '화학분석기사 준비' ELSE '환경기사 취득' END
          WHEN 'industrial'    THEN CASE ri.seq WHEN 2 THEN '품질경영기사 준비' ELSE '산업안전기사' END
          WHEN 'business'      THEN CASE ri.seq WHEN 2 THEN 'SQLD 취득' ELSE '빅데이터분석기사' END
          WHEN 'law_admin'     THEN CASE ri.seq WHEN 2 THEN '행정사 준비' ELSE '법무사 자격' END
          WHEN 'education'     THEN CASE ri.seq WHEN 2 THEN '교원자격증 취득' ELSE '상담사 자격' END
          WHEN 'humanities'    THEN CASE ri.seq WHEN 2 THEN '한국어교원 자격' ELSE 'TOPIK 시험관' END
          WHEN 'arts'          THEN CASE ri.seq WHEN 2 THEN 'GTQ 자격증' ELSE '컬러리스트 취득' END
          WHEN 'science'       THEN CASE ri.seq WHEN 2 THEN '분석화학 자격' ELSE '실험동물기술원' END
          ELSE CASE ri.seq WHEN 2 THEN '컴활 1급 취득' ELSE '자격증 준비' END
        END
      WHEN 'skill' THEN
        CASE ts.category
          WHEN 'medical'       THEN CASE ri.seq WHEN 3 THEN '임상술기 역량 강화' ELSE '의학논문 작성 역량' END
          WHEN 'nursing'       THEN CASE ri.seq WHEN 3 THEN '환자평가 역량 강화' ELSE '간호기록 작성 역량' END
          WHEN 'pharmacy'      THEN CASE ri.seq WHEN 3 THEN '복약지도 역량 강화' ELSE '약물분석 역량' END
          WHEN 'it_engineering' THEN CASE ri.seq WHEN 3 THEN 'Python 심화 학습' ELSE '클라우드 역량 개발' END
          WHEN 'architecture'  THEN CASE ri.seq WHEN 3 THEN 'BIM 모델링 심화' ELSE '3D 렌더링 역량' END
          WHEN 'civil_eng'     THEN CASE ri.seq WHEN 3 THEN '구조해석 심화' ELSE 'GIS 활용 역량' END
          WHEN 'mechanical'    THEN CASE ri.seq WHEN 3 THEN 'CAD/CAM 심화' ELSE 'FEA 해석 역량' END
          WHEN 'electrical'    THEN CASE ri.seq WHEN 3 THEN 'PCB 설계 심화' ELSE '임베디드 프로그래밍' END
          WHEN 'chemical_env'  THEN CASE ri.seq WHEN 3 THEN '공정 시뮬레이션 심화' ELSE '환경분석 역량' END
          WHEN 'industrial'    THEN CASE ri.seq WHEN 3 THEN '데이터 분석 심화' ELSE '최적화 기법 학습' END
          WHEN 'business'      THEN CASE ri.seq WHEN 3 THEN '데이터 분석 역량' ELSE '재무모델링 역량' END
          WHEN 'law_admin'     THEN CASE ri.seq WHEN 3 THEN '법률문서 작성 역량' ELSE '행정실무 역량' END
          WHEN 'education'     THEN CASE ri.seq WHEN 3 THEN '수업설계 역량 강화' ELSE '학생상담 역량' END
          WHEN 'humanities'    THEN CASE ri.seq WHEN 3 THEN '비평적 글쓰기 역량' ELSE '번역 역량 개발' END
          WHEN 'arts'          THEN CASE ri.seq WHEN 3 THEN '디지털 디자인 심화' ELSE '포트폴리오 구축' END
          WHEN 'science'       THEN CASE ri.seq WHEN 3 THEN '실험설계 역량 강화' ELSE '데이터분석 역량' END
          ELSE CASE ri.seq WHEN 3 THEN '직무 역량 개발' ELSE '소프트스킬 강화' END
        END
      WHEN 'activity' THEN
        CASE ts.category
          WHEN 'medical' THEN '의학 학술대회 참가'       WHEN 'nursing' THEN '간호 봉사활동 참여'
          WHEN 'pharmacy' THEN '약학 세미나 참가'        WHEN 'it_engineering' THEN '해커톤 참가'
          WHEN 'architecture' THEN '건축 설계 공모전'    WHEN 'civil_eng' THEN '토목 학술대회 참가'
          WHEN 'mechanical' THEN '기계설계 경진대회'     WHEN 'electrical' THEN '전자회로 경진대회'
          WHEN 'chemical_env' THEN '화학공학 학술대회'   WHEN 'industrial' THEN '산업공학 경진대회'
          WHEN 'business' THEN '비즈니스 공모전 참가'    WHEN 'law_admin' THEN '모의재판 참가'
          WHEN 'education' THEN '교육 봉사활동 참여'     WHEN 'humanities' THEN '에세이 공모전 참가'
          WHEN 'arts' THEN '예술 전시회 참가'            WHEN 'science' THEN '과학 연구 발표회'
          ELSE '교내 공모전 참가'
        END
      WHEN 'internship' THEN
        CASE ts.category
          WHEN 'medical' THEN '대학병원 임상실습'        WHEN 'nursing' THEN '종합병원 실습'
          WHEN 'pharmacy' THEN '병원약국 실습'           WHEN 'it_engineering' THEN 'IT기업 개발 인턴십'
          WHEN 'architecture' THEN '건축사사무소 인턴'   WHEN 'civil_eng' THEN '건설회사 현장실습'
          WHEN 'mechanical' THEN '제조기업 설계 인턴'    WHEN 'electrical' THEN '반도체기업 인턴십'
          WHEN 'chemical_env' THEN '화학기업 현장실습'   WHEN 'industrial' THEN '제조기업 생산관리 인턴'
          WHEN 'business' THEN '기업 경영기획 인턴십'    WHEN 'law_admin' THEN '법률사무소 인턴십'
          WHEN 'education' THEN '학교 교육실습'          WHEN 'humanities' THEN '출판사 인턴십'
          WHEN 'arts' THEN '디자인 스튜디오 인턴'        WHEN 'science' THEN '연구소 인턴십'
          ELSE '기업 인턴십'
        END
      ELSE '기타 활동'
    END,
    ri.description,
    ri.target_grade,
    ri.target_semester,
    -- 졸업생이므로 90% completed
    CASE WHEN abs(hashtext(ts.student_id || ri.seq::text)) % 10 < 9
         THEN 'completed' ELSE 'in_progress' END,
    ri.seq,
    ri.seq,
    -- due_date
    CASE ri.target_semester
        WHEN 1 THEN ((ts.admission_year + ri.target_grade - 1)::text || '-06-30')::date
        ELSE ((ts.admission_year + ri.target_grade - 1)::text || '-12-31')::date
    END,
    -- completed_date
    CASE WHEN abs(hashtext(ts.student_id || ri.seq::text)) % 10 < 9
         THEN CASE ri.target_semester
              WHEN 1 THEN ((ts.admission_year + ri.target_grade - 1)::text || '-06-' ||
                           LPAD((15 + abs(hashtext(ts.student_id || ri.seq::text || 'cd')) % 15)::text, 2, '0'))::date
              ELSE ((ts.admission_year + ri.target_grade - 1)::text || '-12-' ||
                    LPAD((10 + abs(hashtext(ts.student_id || ri.seq::text || 'cd')) % 18)::text, 2, '0'))::date
              END
         ELSE NULL END,
    NULL,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_roadmap r ON r.student_id = ts.student_id
CROSS JOIN tmp_roadmap_items_48 ri
WHERE NOT EXISTS (
    SELECT 1 FROM tb_roadmap_item ri2
    WHERE ri2.roadmap_id = r.roadmap_id AND ri2.ins_user_id = 'SEED_48'
);

DO $$ BEGIN RAISE NOTICE 'Part 1 완료: tb_roadmap_item 생성 (% 건)',
    (SELECT count(*) FROM tb_roadmap_item WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 2: tb_coaching_checkin (12건/학생)
-- 기존 3개 goal × 4회 체크인
-- =====================================================

INSERT INTO tb_coaching_checkin (
    checkin_id, goal_id, mood, progress_note, blockers,
    next_steps, reflection, ai_feedback, ai_suggestions,
    created_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    cg.goal_id,
    CASE (abs(hashtext(cg.goal_id::text || ci_num::text)) % 10)
        WHEN 0 THEN 'great' WHEN 1 THEN 'great'
        WHEN 2 THEN 'good'  WHEN 3 THEN 'good'  WHEN 4 THEN 'good'
        WHEN 5 THEN 'neutral' WHEN 6 THEN 'neutral' WHEN 7 THEN 'neutral'
        WHEN 8 THEN 'struggling'
        ELSE 'good'
    END,
    CASE ci_num
        WHEN 1 THEN '목표를 설정하고 초기 계획을 수립했습니다. 관련 자료를 수집하기 시작했습니다.'
        WHEN 2 THEN '중간 점검 단계입니다. 계획대로 진행 중이며, 일부 조정이 필요합니다.'
        WHEN 3 THEN '상당한 진전이 있었습니다. 핵심 마일스톤을 달성했습니다.'
        ELSE '최종 점검입니다. 대부분의 목표를 달성했으며, 마무리 작업 중입니다.'
    END,
    CASE WHEN abs(hashtext(cg.goal_id::text || ci_num::text || 'b')) % 3 = 0
         THEN CASE ci_num
              WHEN 1 THEN '시간 관리가 어렵습니다.'
              WHEN 2 THEN '관련 자원 접근이 제한적입니다.'
              WHEN 3 THEN '다른 과목과 일정이 겹칩니다.'
              ELSE NULL END
         ELSE NULL END,
    CASE ci_num
        WHEN 1 THEN '세부 실행 계획 수립 및 1차 목표 달성'
        WHEN 2 THEN '중간 성과 검토 및 계획 수정'
        WHEN 3 THEN '최종 목표 향한 집중 실행'
        ELSE '성과 정리 및 회고 준비'
    END,
    CASE ci_num
        WHEN 1 THEN '시작이 반이라는 말처럼 첫 발을 내딛었습니다.'
        WHEN 2 THEN '예상보다 진행이 순조롭습니다. 꾸준함이 중요합니다.'
        WHEN 3 THEN '어려운 부분도 있었지만 성장을 느낍니다.'
        ELSE '전체 과정을 돌아보며 많은 것을 배웠습니다.'
    END,
    CASE ci_num
        WHEN 1 THEN '좋은 출발입니다. 구체적인 일정표를 작성하면 실행력이 높아집니다.'
        WHEN 2 THEN '꾸준한 노력이 돋보입니다. 작은 성과를 축하하며 동기를 유지하세요.'
        WHEN 3 THEN '핵심 역량이 성장하고 있습니다. 남은 기간 집중하면 목표 달성이 가능합니다.'
        ELSE '훌륭한 여정이었습니다. 이 경험을 바탕으로 다음 단계를 계획하세요.'
    END,
    CASE ci_num
        WHEN 1 THEN ARRAY['주간 목표를 설정하세요', '관련 스터디 그룹에 참여하세요']
        WHEN 2 THEN ARRAY['진행 상황을 시각화하세요', '멘토와 상담을 예약하세요']
        WHEN 3 THEN ARRAY['포트폴리오에 성과를 기록하세요', '부족한 부분을 집중 보강하세요']
        ELSE ARRAY['회고를 통해 교훈을 정리하세요', '다음 목표를 구상하세요']
    END,
    cg.created_at + (ci_num * INTERVAL '4 weeks'),
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_coaching_goal cg ON cg.std_id = ts.student_id
CROSS JOIN generate_series(1, 4) AS ci_num
WHERE NOT EXISTS (
    SELECT 1 FROM tb_coaching_checkin cc
    WHERE cc.goal_id = cg.goal_id AND cc.ins_user_id = 'SEED_48'
);

DO $$ BEGIN RAISE NOTICE 'Part 2 완료: tb_coaching_checkin 생성 (% 건)',
    (SELECT count(*) FROM tb_coaching_checkin WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 3: tb_coaching_retrospective (~2건/학생)
-- status='completed'인 목표만
-- =====================================================

INSERT INTO tb_coaching_retrospective (
    retrospective_id, goal_id, what_went_well, what_could_improve,
    lessons_learned, next_goals, satisfaction_rating,
    ai_analysis, ai_recommendations,
    created_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    cg.goal_id,
    CASE cg.goal_type
        WHEN 'academic' THEN '전공 과목에서 목표 성적을 달성했습니다. 체계적인 학습 계획이 효과적이었습니다.'
        WHEN 'skill' THEN '핵심 실무 역량을 개발했습니다. 자격증 취득과 프로젝트 경험이 쌓였습니다.'
        WHEN 'career' THEN '목표 직군에 대한 이해도가 높아졌습니다. 인턴십 경험이 큰 도움이 되었습니다.'
        ELSE '목표한 바를 대부분 달성했습니다.'
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN '시간 관리를 더 효율적으로 해야 합니다. 일부 과목에서 추가 학습이 필요합니다.'
        WHEN 'skill' THEN '실습 시간을 더 확보하고, 다양한 프로젝트에 참여할 필요가 있습니다.'
        WHEN 'career' THEN '네트워킹 활동을 더 적극적으로 하고, 면접 준비를 체계화해야 합니다.'
        ELSE '시간 배분과 우선순위 설정을 개선할 수 있습니다.'
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN '꾸준한 학습이 가장 중요하다는 것을 배웠습니다.'
        WHEN 'skill' THEN '이론과 실습의 균형이 중요합니다. 실제 프로젝트 경험이 가장 큰 학습입니다.'
        WHEN 'career' THEN '명확한 목표 설정과 단계적 접근이 효과적입니다.'
        ELSE '목표를 세분화하고 지속적으로 점검하는 것이 성공의 열쇠입니다.'
    END,
    CASE cg.goal_type
        WHEN 'academic' THEN '대학원 진학 또는 전문 분야 심화 학습 계획 수립'
        WHEN 'skill' THEN '전문 자격증 추가 취득 및 실무 역량 고도화'
        WHEN 'career' THEN '취업 후 1년 내 핵심 역량 확보 및 커리어 개발'
        ELSE '졸업 후 커리어 목표 달성을 위한 구체적 계획 수립'
    END,
    3 + abs(hashtext(cg.goal_id::text || 'sat')) % 3,
    '목표 달성 과정에서 지속적인 노력과 체계적인 접근이 돋보였습니다. ' ||
    '특히 중간 점검을 통한 계획 수정이 효과적이었습니다.',
    ARRAY[
        '달성한 성과를 포트폴리오에 체계적으로 정리하세요',
        '관련 분야 전문가와 네트워킹을 지속하세요',
        '다음 목표를 SMART 기준으로 설정하세요'
    ],
    COALESCE(cg.completed_at, cg.created_at + INTERVAL '6 months'),
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_coaching_goal cg ON cg.std_id = ts.student_id
WHERE cg.status = 'completed'
  AND NOT EXISTS (
    SELECT 1 FROM tb_coaching_retrospective cr
    WHERE cr.goal_id = cg.goal_id
);

DO $$ BEGIN RAISE NOTICE 'Part 3 완료: tb_coaching_retrospective 생성 (% 건)',
    (SELECT count(*) FROM tb_coaching_retrospective WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 4a: tb_assessment (2건/학생)
-- assessment_type: system@2024-1, self@2024-2
-- =====================================================

INSERT INTO tb_assessment (
    assessment_id, student_id, assessment_type, assessment_date, term_cd,
    ins_user_id, ins_dt
)
SELECT
    uuid_generate_v5(uuid_ns_oid(), ts.student_id || asmt.term_cd || asmt.assessment_type),
    ts.student_id,
    asmt.assessment_type,
    asmt.assessment_date,
    asmt.term_cd,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
CROSS JOIN (
    VALUES
        ('system', '2024-03-15'::date, '2024-1'),
        ('self',   '2024-09-20'::date, '2024-2')
) AS asmt(assessment_type, assessment_date, term_cd)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_assessment a
    WHERE a.student_id = ts.student_id AND a.term_cd = asmt.term_cd AND a.assessment_type = asmt.assessment_type
)
ON CONFLICT (assessment_id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 4a 완료: tb_assessment 생성 (% 건)',
    (SELECT count(*) FROM tb_assessment WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 4b: tb_assessment_result (12건/학생 = 6comp × 2)
-- raw_score: 60~95, final_score: raw_score ±5
-- =====================================================

INSERT INTO tb_assessment_result (
    result_id, assessment_id, competency_cd,
    raw_score, adjusted_score, academic_contribution, extracurricular_boost,
    final_score, status, gap_score,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    a.assessment_id,
    comp.competency_cd,
    raw_s,
    raw_s + (abs(hashtext(ts.student_id || comp.competency_cd || a.term_cd || 'adj')) % 5 - 2)::numeric,
    (raw_s * 0.7)::numeric(5,2),
    (raw_s * 0.3)::numeric(5,2),
    LEAST(100, raw_s + (abs(hashtext(ts.student_id || comp.competency_cd || a.term_cd || 'fin')) % 6 - 2))::numeric(5,2),
    CASE
        WHEN raw_s >= 85 THEN 'excellent'
        WHEN raw_s >= 75 THEN 'good'
        WHEN raw_s >= 65 THEN 'average'
        ELSE 'improve'
    END,
    GREATEST(0, 85 - raw_s)::numeric(5,2),
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_assessment a ON a.student_id = ts.student_id AND a.ins_user_id = 'SEED_48'
CROSS JOIN (
    SELECT competency_cd FROM tb_competency ORDER BY competency_cd LIMIT 6
) AS comp
CROSS JOIN LATERAL (
    SELECT (60 + abs(hashtext(ts.student_id || comp.competency_cd || a.term_cd)) % 36)::numeric(5,2) AS raw_s
) calc
WHERE NOT EXISTS (
    SELECT 1 FROM tb_assessment_result ar
    WHERE ar.assessment_id = a.assessment_id AND ar.competency_cd = comp.competency_cd
);

DO $$ BEGIN RAISE NOTICE 'Part 4b 완료: tb_assessment_result 생성 (% 건)',
    (SELECT count(*) FROM tb_assessment_result WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 5: tb_opportunity_recommendation (5건/학생)
-- =====================================================

INSERT INTO tb_opportunity_recommendation (
    recommendation_id, student_id, opportunity_id,
    match_score, match_reasons, status,
    recommended_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    opp.opportunity_id,
    (65 + abs(hashtext(ts.student_id || opp.opportunity_id::text)) % 34)::numeric(5,2),
    CASE abs(hashtext(ts.student_id || opp.opportunity_id::text || 'mr')) % 4
        WHEN 0 THEN '["skill_match", "department_match"]'::jsonb
        WHEN 1 THEN '["skill_match", "gpa_eligible", "department_match"]'::jsonb
        WHEN 2 THEN '["department_match", "interest_match"]'::jsonb
        ELSE '["skill_match", "interest_match", "gpa_eligible"]'::jsonb
    END,
    CASE abs(hashtext(ts.student_id || opp.opportunity_id::text || 'st')) % 10
        WHEN 0 THEN 'recommended' WHEN 1 THEN 'recommended'
        WHEN 2 THEN 'viewed' WHEN 3 THEN 'viewed' WHEN 4 THEN 'viewed'
        WHEN 5 THEN 'saved' WHEN 6 THEN 'saved'
        WHEN 7 THEN 'applied' WHEN 8 THEN 'applied'
        ELSE 'dismissed'
    END,
    NOW() - (abs(hashtext(ts.student_id || opp.opportunity_id::text || 'ra')) % 180 || ' days')::interval,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
CROSS JOIN LATERAL (
    SELECT o.opportunity_id
    FROM tb_opportunity o
    WHERE o.status = 'open'
    ORDER BY abs(hashtext(ts.student_id || o.opportunity_id::text))
    LIMIT 5
) opp
ON CONFLICT (student_id, opportunity_id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 5 완료: tb_opportunity_recommendation 생성 (% 건)',
    (SELECT count(*) FROM tb_opportunity_recommendation WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 6: tb_opportunity_application (2건/학생)
-- =====================================================

INSERT INTO tb_opportunity_application (
    application_id, student_id, opportunity_id,
    applied_at, status, cover_letter, attachments,
    reviewer_notes, decision_at,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    sub.student_id,
    sub.opportunity_id,
    sub.recommended_at + INTERVAL '7 days',
    sub.app_status,
    sub.cover_letter,
    ('[{"name": "이력서.pdf", "url": "https://portfolio.inje.ac.kr/' || sub.student_id || '/resume.pdf"}]')::jsonb,
    NULL,
    CASE WHEN sub.app_status IN ('accepted','rejected')
         THEN sub.recommended_at + INTERVAL '30 days' ELSE NULL END,
    'SEED_48',
    NOW()
FROM (
    SELECT
        rec.student_id,
        rec.opportunity_id,
        rec.recommended_at,
        rec.app_rank,
        ts.category,
        CASE WHEN rec.app_rank = 1
             THEN CASE abs(hashtext(rec.student_id || rec.opportunity_id::text || 'app')) % 4
                  WHEN 0 THEN 'accepted' WHEN 1 THEN 'under_review' WHEN 2 THEN 'submitted' ELSE 'rejected' END
             ELSE CASE abs(hashtext(rec.student_id || rec.opportunity_id::text || 'app2')) % 3
                  WHEN 0 THEN 'submitted' WHEN 1 THEN 'under_review' ELSE 'accepted' END
        END AS app_status,
        CASE ts.category
            WHEN 'medical' THEN '의학 분야에 대한 열정과 임상 경험을 바탕으로 지원합니다.'
            WHEN 'nursing' THEN '간호학 전공 역량과 실습 경험을 살려 기여하고자 합니다.'
            WHEN 'pharmacy' THEN '약학 전문 지식과 연구 경험을 기반으로 지원합니다.'
            WHEN 'health' THEN '보건의료 분야의 전문성을 발휘하고자 합니다.'
            WHEN 'it_engineering' THEN 'SW 개발 역량과 프로젝트 경험을 바탕으로 지원합니다.'
            WHEN 'architecture' THEN '건축 설계 역량과 BIM 실무 경험을 바탕으로 지원합니다.'
            WHEN 'civil_eng' THEN '토목공학 전문 지식과 현장 경험을 살려 기여하겠습니다.'
            WHEN 'mechanical' THEN '기계설계 역량과 CAD/CAM 실무 경험을 바탕으로 지원합니다.'
            WHEN 'electrical' THEN '전자공학 전문성과 회로설계 경험을 기반으로 지원합니다.'
            WHEN 'chemical_env' THEN '화학공정 지식과 실험 역량을 활용하고자 합니다.'
            WHEN 'industrial' THEN '산업공학 전문성과 데이터 분석 역량으로 기여하겠습니다.'
            WHEN 'business' THEN '경영학 전공 지식과 인턴십 경험을 바탕으로 지원합니다.'
            WHEN 'law_admin' THEN '법학/행정 전문 지식을 활용하여 기여하고 싶습니다.'
            WHEN 'education' THEN '교육학 역량과 교육실습 경험을 바탕으로 지원합니다.'
            WHEN 'humanities' THEN '인문학적 사고력과 글쓰기 역량으로 기여하겠습니다.'
            WHEN 'arts' THEN '창작 역량과 디자인 포트폴리오를 바탕으로 지원합니다.'
            WHEN 'science' THEN '과학적 연구 방법론과 실험 역량을 활용하고자 합니다.'
            ELSE '전공 역량과 다양한 활동 경험을 바탕으로 지원합니다.'
        END AS cover_letter
    FROM (
        SELECT r2.student_id, r2.opportunity_id, r2.recommended_at,
               ROW_NUMBER() OVER (PARTITION BY r2.student_id ORDER BY r2.match_score DESC) AS app_rank
        FROM tb_opportunity_recommendation r2
        WHERE r2.ins_user_id = 'SEED_48'
    ) rec
    JOIN tmp_showcase_48 ts ON rec.student_id = ts.student_id
    WHERE rec.app_rank <= 2
) sub
WHERE NOT EXISTS (
    SELECT 1 FROM tb_opportunity_application oa
    WHERE oa.student_id = sub.student_id AND oa.opportunity_id = sub.opportunity_id
);

DO $$ BEGIN RAISE NOTICE 'Part 6 완료: tb_opportunity_application 생성 (% 건)',
    (SELECT count(*) FROM tb_opportunity_application WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 7: tb_skill_passport (1건/학생)
-- 스키마: passport_id, student_id(UNIQUE), overall_score,
--   total_badges, total_skills, verified_skills,
--   passport_data(JSONB), last_updated, public_share_url, is_public
-- =====================================================

INSERT INTO tb_skill_passport (
    passport_id, student_id, overall_score,
    total_badges, total_skills, verified_skills,
    passport_data, last_updated,
    public_share_url, is_public,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    (65 + abs(hashtext(ts.student_id || 'score')) % 31)::numeric,
    COALESCE((SELECT count(*) FROM tb_student_badge sb WHERE sb.student_id = ts.student_id), 0)::int,
    COALESCE((SELECT count(*) FROM tb_student_skill ss WHERE ss.student_id = ts.student_id), 0)::int,
    GREATEST(1, COALESCE((SELECT count(*) FROM tb_student_skill ss
                          WHERE ss.student_id = ts.student_id AND ss.verification_source != 'self_assessment'), 0))::int,
    jsonb_build_object(
        'headline',
        CASE ts.category
            WHEN 'medical' THEN '의학 전공 졸업생 | 임상 경험 보유'
            WHEN 'nursing' THEN '간호학 전공 졸업생 | 임상간호 전문가'
            WHEN 'pharmacy' THEN '약학 전공 졸업생 | 약물치료 전문가'
            WHEN 'health' THEN '보건의료 전공 졸업생 | 건강관리 전문가'
            WHEN 'it_engineering' THEN 'IT/SW 전공 졸업생 | 소프트웨어 엔지니어'
            WHEN 'architecture' THEN '건축학 전공 졸업생 | 건축설계 전문가'
            WHEN 'civil_eng' THEN '토목공학 전공 졸업생 | 구조설계 전문가'
            WHEN 'mechanical' THEN '기계공학 전공 졸업생 | 기계설계 전문가'
            WHEN 'electrical' THEN '전자공학 전공 졸업생 | 회로설계 전문가'
            WHEN 'chemical_env' THEN '화학공학 전공 졸업생 | 공정설계 전문가'
            WHEN 'industrial' THEN '산업공학 전공 졸업생 | 생산최적화 전문가'
            WHEN 'business' THEN '경영학 전공 졸업생 | 비즈니스 애널리스트'
            WHEN 'law_admin' THEN '법학/행정 전공 졸업생 | 법률/행정 전문가'
            WHEN 'education' THEN '교육학 전공 졸업생 | 교육 전문가'
            WHEN 'humanities' THEN '인문학 전공 졸업생 | 콘텐츠 전문가'
            WHEN 'arts' THEN '예술/디자인 전공 졸업생 | 크리에이터'
            WHEN 'science' THEN '자연과학 전공 졸업생 | 연구원'
            ELSE '졸업생 | 역량 개발 전문가'
        END,
        'bio', ts.department_nm || ' 전공 ' || ts.admission_year || '년 입학 졸업생',
        'featured_badges', COALESCE(
            (SELECT jsonb_agg(sb2.badge_id) FROM (
                SELECT badge_id FROM tb_student_badge WHERE student_id = ts.student_id ORDER BY ins_dt DESC LIMIT 2
            ) sb2), '[]'::jsonb),
        'featured_skills', COALESCE(
            (SELECT jsonb_agg(ss2.skill_cd) FROM (
                SELECT skill_cd FROM tb_student_skill WHERE student_id = ts.student_id ORDER BY current_level DESC LIMIT 3
            ) ss2), '[]'::jsonb),
        'social_links', jsonb_build_object(
            'linkedin', 'https://linkedin.com/in/' || ts.student_id,
            'github', 'https://github.com/' || ts.student_id
        )
    ),
    NOW() - (abs(hashtext(ts.student_id || 'lu')) % 90 || ' days')::interval,
    'https://career.inje.ac.kr/passport/' || ts.student_id,
    CASE WHEN abs(hashtext(ts.student_id || 'pub')) % 10 < 3 THEN TRUE ELSE FALSE END,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_skill_passport sp WHERE sp.student_id = ts.student_id
)
ON CONFLICT (student_id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 7 완료: tb_skill_passport 생성 (% 건)',
    (SELECT count(*) FROM tb_skill_passport WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 8: tb_advisor_intervention (2건/학생)
-- 스키마: assignment_id(FK→tb_advisor_assignment), intervention_type,
--   trigger_alert_id, scheduled_at, completed_at, status,
--   notes, outcome, follow_up_required, follow_up_date
-- =====================================================

INSERT INTO tb_advisor_intervention (
    intervention_id, assignment_id, intervention_type,
    trigger_alert_id, scheduled_at, completed_at,
    status, notes, outcome,
    follow_up_required, follow_up_date,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    aa.assignment_id,
    interv.intervention_type,
    interv.trigger_alert_id,
    interv.scheduled_at,
    interv.completed_at,
    interv.status,
    interv.notes,
    interv.outcome,
    interv.follow_up_required,
    interv.follow_up_date,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_advisor_assignment aa ON aa.student_id = ts.student_id AND aa.status = 'active'
CROSS JOIN LATERAL (
    VALUES
        (1, 'goal_review'::varchar,
         NULL::uuid,
         (NOW() - INTERVAL '3 months')::timestamp,
         (NOW() - INTERVAL '3 months' + INTERVAL '1 hour')::timestamp,
         'completed'::varchar,
         '학생의 학업 목표 진행 상황을 점검하고 방향성을 재설정했습니다.',
         '학업 목표 달성률 80% 이상, 추가 지도 불필요',
         FALSE, NULL::date),
        (2, 'risk_escalation'::varchar,
         (SELECT alert_id FROM tb_risk_alert WHERE student_id = ts.student_id ORDER BY ins_dt DESC LIMIT 1),
         (NOW() - INTERVAL '1 month')::timestamp,
         (NOW() - INTERVAL '1 month' + INTERVAL '2 hours')::timestamp,
         'completed'::varchar,
         '위험 알림 검토 후 대응 방안을 수립했습니다.',
         '위험 요소 해소, 학생 상태 양호',
         TRUE, (CURRENT_DATE + INTERVAL '1 month')::date)
) AS interv(seq, intervention_type, trigger_alert_id, scheduled_at, completed_at, status, notes, outcome, follow_up_required, follow_up_date)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_advisor_intervention ai
    WHERE ai.assignment_id = aa.assignment_id AND ai.ins_user_id = 'SEED_48'
);

DO $$ BEGIN RAISE NOTICE 'Part 8 완료: tb_advisor_intervention 생성 (% 건)',
    (SELECT count(*) FROM tb_advisor_intervention WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 9: tb_advisor_note (3건/학생)
-- 스키마: assignment_id(FK), note_type, content,
--   is_private, created_at
-- =====================================================

INSERT INTO tb_advisor_note (
    note_id, assignment_id, note_type, content, is_private,
    created_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    aa.assignment_id,
    note.note_type,
    note.content,
    note.is_private,
    note.created_at,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_advisor_assignment aa ON aa.student_id = ts.student_id AND aa.status = 'active'
CROSS JOIN LATERAL (
    VALUES
        (1, 'general'::varchar,
         ts.student_nm || ' 학생의 전반적인 학업 및 진로 상담 내용. ' ||
         CASE ts.category
             WHEN 'medical' THEN '의학 분야 진출에 대한 구체적인 계획을 논의함.'
             WHEN 'nursing' THEN '간호 분야 진출 계획과 자격증 준비 상황 확인.'
             WHEN 'it_engineering' THEN 'SW 개발 직군 취업 준비 상황 점검.'
             WHEN 'architecture' THEN '건축 분야 진로와 포트폴리오 준비 논의.'
             WHEN 'business' THEN '경영/컨설팅 분야 취업 준비 현황 확인.'
             WHEN 'civil_eng' THEN '토목/건설 분야 현장실습 계획 논의.'
             WHEN 'mechanical' THEN '기계 분야 취업 및 대학원 진학 상담.'
             WHEN 'electrical' THEN '전자/반도체 분야 취업 전략 논의.'
             WHEN 'pharmacy' THEN '약학 분야 면허 준비 및 진로 상담.'
             WHEN 'education' THEN '교육 분야 임용시험 준비 현황 확인.'
             ELSE '전공 분야 진로 계획을 함께 검토함.'
         END,
         TRUE,
         NOW() - INTERVAL '6 months'),
        (2, 'meeting'::varchar,
         ts.student_nm || ' 학생과의 정기 면담. 학업 성취도와 역량 개발 현황을 점검하고 졸업 후 계획을 구체화함.',
         TRUE,
         NOW() - INTERVAL '3 months'),
        (3, 'observation'::varchar,
         ts.student_nm || ' 학생의 수업 참여도와 과제 수행 태도가 우수함. 팀 프로젝트에서 리더십 발휘.',
         FALSE,
         NOW() - INTERVAL '1 month')
) AS note(seq, note_type, content, is_private, created_at)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_advisor_note an
    WHERE an.assignment_id = aa.assignment_id AND an.ins_user_id = 'SEED_48'
);

DO $$ BEGIN RAISE NOTICE 'Part 9 완료: tb_advisor_note 생성 (% 건)',
    (SELECT count(*) FROM tb_advisor_note WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 10: tb_scenario_comparison (1건/학생)
-- 스키마: scenario_ids(UUID[]), comparison_metrics(JSONB),
--   recommendation(TEXT), ai_analysis(JSONB),
--   winner_scenario_id(UUID), comparison_summary(TEXT)
-- =====================================================

INSERT INTO tb_scenario_comparison (
    comparison_id, student_id, scenario_ids,
    comparison_metrics, recommendation, ai_analysis,
    created_at, ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    ARRAY[scen.s1_id, scen.s2_id],
    jsonb_build_object(
        'gpa_impact', jsonb_build_array(
            jsonb_build_object('scenario_id', scen.s1_id, 'value', 3.5 + (abs(hashtext(ts.student_id || 'gpa1')) % 10)::numeric / 10),
            jsonb_build_object('scenario_id', scen.s2_id, 'value', 3.3 + (abs(hashtext(ts.student_id || 'gpa2')) % 12)::numeric / 10)
        ),
        'skill_growth', jsonb_build_array(
            jsonb_build_object('scenario_id', scen.s1_id, 'value', 15 + abs(hashtext(ts.student_id || 'sg1')) % 20),
            jsonb_build_object('scenario_id', scen.s2_id, 'value', 10 + abs(hashtext(ts.student_id || 'sg2')) % 25)
        ),
        'career_readiness', jsonb_build_array(
            jsonb_build_object('scenario_id', scen.s1_id, 'value', 70 + abs(hashtext(ts.student_id || 'cr1')) % 20),
            jsonb_build_object('scenario_id', scen.s2_id, 'value', 65 + abs(hashtext(ts.student_id || 'cr2')) % 25)
        )
    ),
    '시나리오 1이 전반적인 역량 개발 및 커리어 준비도에서 더 높은 점수를 기록했습니다. ' ||
    '두 시나리오 모두 긍정적인 성장을 보여주지만, 시나리오 1의 균형 잡힌 접근이 더 효과적입니다.',
    jsonb_build_object(
        'winner', scen.s1_id,
        'analysis', '첫 번째 시나리오가 GPA, 스킬 성장, 커리어 준비도 모든 지표에서 우위',
        'confidence', 0.85
    ),
    NOW(),
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
CROSS JOIN LATERAL (
    SELECT
        (ARRAY_AGG(ss.scenario_id ORDER BY ss.ins_dt DESC))[1] AS s1_id,
        (ARRAY_AGG(ss.scenario_id ORDER BY ss.ins_dt DESC))[2] AS s2_id
    FROM tb_simulation_scenario ss
    WHERE ss.student_id = ts.student_id
    HAVING count(*) >= 2
) scen
WHERE NOT EXISTS (
    SELECT 1 FROM tb_scenario_comparison sc
    WHERE sc.student_id = ts.student_id AND sc.ins_user_id = 'SEED_48'
);

DO $$ BEGIN RAISE NOTICE 'Part 10 완료: tb_scenario_comparison 생성 (% 건)',
    (SELECT count(*) FROM tb_scenario_comparison WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 11a: tb_recommendation_run (1건/학생)
-- 스키마: run_type, model_version, prompt_tokens,
--   completion_tokens, latency_ms, status, context_data, run_dt
-- =====================================================

INSERT INTO tb_recommendation_run (
    run_id, student_id, run_type, model_version,
    prompt_tokens, completion_tokens, latency_ms,
    status, error_message, context_data, run_dt
)
SELECT
    uuid_generate_v5(uuid_ns_oid(), ts.student_id || 'rec_run_48'),
    ts.student_id,
    'career_recommendation',
    'v1.0',
    300 + abs(hashtext(ts.student_id || 'pt')) % 200,
    200 + abs(hashtext(ts.student_id || 'ct')) % 300,
    1500 + abs(hashtext(ts.student_id || 'lat')) % 1000,
    'completed',
    NULL,
    jsonb_build_object(
        'department', ts.department_nm,
        'category', ts.category,
        'admission_year', ts.admission_year,
        'trigger', 'scheduled'
    ),
    NOW() - (abs(hashtext(ts.student_id || 'rdt')) % 30 || ' days')::interval
FROM tmp_showcase_48 ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_recommendation_run rr
    WHERE rr.student_id = ts.student_id
)
ON CONFLICT (run_id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 11a 완료: tb_recommendation_run 생성 (% 건)',
    (SELECT count(*) FROM tb_recommendation_run WHERE status = 'completed' AND model_version = 'v1.0'); END $$;


-- =====================================================
-- Part 11b: tb_recommendation_item (3건/run)
-- =====================================================

INSERT INTO tb_recommendation_item (
    item_id, run_id, item_type, title, description,
    priority, target_competency, reasoning,
    confidence_score, deadline, ins_dt
)
SELECT
    uuid_generate_v5(uuid_ns_oid(), ts.student_id || 'rec_item_48_' || item.n::text),
    rr.run_id,
    item.item_type,
    item.title,
    item.description,
    item.priority,
    item.target_competency,
    item.reasoning,
    item.confidence_score,
    item.deadline,
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_recommendation_run rr ON rr.student_id = ts.student_id
CROSS JOIN (
    VALUES
        (1, 'course'::varchar,
         '전공 심화 과목 이수 권장'::varchar,
         '현재 역량 갭을 줄이기 위해 전공 심화 과목 이수를 권장합니다.',
         'high'::varchar, 'COMP001'::varchar,
         '전공 심화 과목은 핵심 역량 향상에 가장 높은 기여도를 보입니다.',
         0.92::numeric, '2024-2'::varchar),
        (2, 'certification'::varchar,
         '전문 자격증 취득 추천'::varchar,
         '취업 경쟁력 강화를 위해 관련 전문 자격증 취득을 추천합니다.',
         'medium'::varchar, 'COMP003'::varchar,
         '자격증 취득은 실무 역량 입증에 효과적이며 동일 학과 졸업생 85%가 보유합니다.',
         0.85::numeric, '2024-2'::varchar),
        (3, 'project'::varchar,
         '실무 프로젝트 참여 권장'::varchar,
         '실무 역량 개발을 위해 캡스톤 또는 산학 프로젝트에 참여하세요.',
         'high'::varchar, 'COMP002'::varchar,
         '프로젝트 참여는 종합적 역량 개발에 가장 효과적인 방법입니다.',
         0.88::numeric, '2024-2'::varchar)
) AS item(n, item_type, title, description, priority, target_competency, reasoning, confidence_score, deadline)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_recommendation_item ri
    WHERE ri.run_id = rr.run_id
)
ON CONFLICT (item_id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 11b 완료: tb_recommendation_item 생성 (% 건)',
    (SELECT count(*) FROM tb_recommendation_item ri
     JOIN tb_recommendation_run rr ON ri.run_id = rr.run_id
     WHERE rr.model_version = 'v1.0'); END $$;


-- =====================================================
-- Part 11c: tb_recommendation_evidence (6건/학생 = 2건/item × 3items)
-- 스키마: evidence_id, item_id(FK), source_type, source_id,
--   source_version, snippet_text, snippet_hash, retrieval_score, retrieval_method
-- =====================================================

INSERT INTO tb_recommendation_evidence (
    evidence_id, item_id, source_type, source_id,
    source_version, snippet_text, snippet_hash,
    retrieval_score, retrieval_method,
    ins_user_id, ins_dt
)
SELECT
    uuid_generate_v5(uuid_ns_oid(), ts.student_id || 'rec_evid_48_' || item_n::text || '_' || ev_n::text),
    uuid_generate_v5(uuid_ns_oid(), ts.student_id || 'rec_item_48_' || item_n::text),
    ev.source_type,
    ev.source_id,
    'v1.0',
    ev.snippet_text,
    md5(ev.snippet_text),
    ev.retrieval_score,
    ev.retrieval_method,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
CROSS JOIN (
    VALUES
        -- item 1 (course) 의 evidence 2개
        (1, 1, 'course'::varchar, 'CS401'::varchar,
         '전공 심화 과목 이수는 핵심 역량 COMP001 향상에 0.85 기여도를 보임',
         0.92::numeric, 'hybrid'::varchar),
        (1, 2, 'alumni_stat'::varchar, 'COHORT_2023'::varchar,
         '동일 학과 졸업생 중 전공 심화 과목 3과목 이상 이수자의 취업률이 15% 높음',
         0.87::numeric, 'bm25'::varchar),
        -- item 2 (certification) 의 evidence 2개
        (2, 1, 'course'::varchar, 'CERT_PREP'::varchar,
         '자격증 보유 졸업생의 초봉이 평균 8% 높으며, 취업 소요기간이 2개월 단축됨',
         0.89::numeric, 'vector'::varchar),
        (2, 2, 'alumni_stat'::varchar, 'COHORT_2022'::varchar,
         '관련 자격증 보유자 비율: 학과 평균 72%, 취업자 평균 89%',
         0.84::numeric, 'hybrid'::varchar),
        -- item 3 (project) 의 evidence 2개
        (3, 1, 'course'::varchar, 'CAP_DESIGN'::varchar,
         '캡스톤 프로젝트 참여 학생의 COMP002(문제해결) 역량 점수가 평균 12점 높음',
         0.91::numeric, 'hybrid'::varchar),
        (3, 2, 'alumni_stat'::varchar, 'COHORT_2023'::varchar,
         '산학 프로젝트 경험자의 희망직군 취업 성공률이 23% 높음',
         0.86::numeric, 'bm25'::varchar)
) AS ev(item_n, ev_n, source_type, source_id, snippet_text, retrieval_score, retrieval_method)
-- run이 존재하는 학생만
WHERE EXISTS (
    SELECT 1 FROM tb_recommendation_run rr WHERE rr.student_id = ts.student_id
)
AND NOT EXISTS (
    SELECT 1 FROM tb_recommendation_evidence re
    WHERE re.item_id = uuid_generate_v5(uuid_ns_oid(), ts.student_id || 'rec_item_48_' || ev.item_n::text)
      AND re.ins_user_id = 'SEED_48'
)
ON CONFLICT (evidence_id) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'Part 11c 완료: tb_recommendation_evidence 생성 (% 건)',
    (SELECT count(*) FROM tb_recommendation_evidence WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 12: tb_feedback_event (1건/학생)
-- 스키마: feedback_id, run_id(FK), user_id(VARCHAR),
--   feedback_type(thumbs_up/thumbs_down/edit), details
-- =====================================================

INSERT INTO tb_feedback_event (
    feedback_id, run_id, user_id,
    feedback_type, details,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    rr.run_id,
    ts.student_id,
    CASE WHEN abs(hashtext(ts.student_id || 'fb')) % 10 < 8 THEN 'thumbs_up'
         WHEN abs(hashtext(ts.student_id || 'fb')) % 10 = 8 THEN 'thumbs_down'
         ELSE 'edit'
    END,
    CASE WHEN abs(hashtext(ts.student_id || 'fb')) % 10 < 8 THEN '추천 내용이 도움이 되었습니다. 전공 관련 추천이 정확합니다.'
         WHEN abs(hashtext(ts.student_id || 'fb')) % 10 = 8 THEN '일부 추천이 현재 상황과 맞지 않습니다. 이미 이수한 과목이 포함되어 있습니다.'
         ELSE '자격증 추천을 더 구체적으로 수정했습니다. 전공 특화 자격증으로 변경.'
    END,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
JOIN tb_recommendation_run rr ON rr.student_id = ts.student_id
WHERE NOT EXISTS (
    SELECT 1 FROM tb_feedback_event fe WHERE fe.run_id = rr.run_id
);

DO $$ BEGIN RAISE NOTICE 'Part 12 완료: tb_feedback_event 생성 (% 건)',
    (SELECT count(*) FROM tb_feedback_event fe
     JOIN tb_recommendation_run rr ON fe.run_id = rr.run_id
     WHERE rr.model_version = 'v1.0'); END $$;


-- =====================================================
-- Part 13: tb_worknet_diagnosis (1건/학생)
-- 스키마: diagnosis_id, student_id(FK), diagnosis_date,
--   aptitude_codes(VARCHAR[]), interest_codes(VARCHAR[]),
--   job_match_scores(JSONB), raw_result(JSONB)
-- =====================================================

INSERT INTO tb_worknet_diagnosis (
    diagnosis_id, student_id, diagnosis_date,
    aptitude_codes, interest_codes,
    job_match_scores, raw_result,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    ((ts.admission_year + 2)::text || '-' ||
    LPAD((3 + abs(hashtext(ts.student_id || 'dmon')) % 8)::text, 2, '0') || '-' ||
    LPAD((5 + abs(hashtext(ts.student_id || 'dday')) % 20)::text, 2, '0'))::date,
    -- Holland RIASEC aptitude codes by category
    CASE ts.category
        WHEN 'medical'       THEN ARRAY['I','R','S']
        WHEN 'nursing'       THEN ARRAY['S','I','C']
        WHEN 'pharmacy'      THEN ARRAY['I','C','R']
        WHEN 'health'        THEN ARRAY['S','I','R']
        WHEN 'it_engineering' THEN ARRAY['I','R','C']
        WHEN 'architecture'  THEN ARRAY['R','A','I']
        WHEN 'civil_eng'     THEN ARRAY['R','I','C']
        WHEN 'mechanical'    THEN ARRAY['R','I','C']
        WHEN 'electrical'    THEN ARRAY['I','R','C']
        WHEN 'chemical_env'  THEN ARRAY['I','R','C']
        WHEN 'industrial'    THEN ARRAY['I','E','C']
        WHEN 'business'      THEN ARRAY['E','C','S']
        WHEN 'law_admin'     THEN ARRAY['E','C','I']
        WHEN 'education'     THEN ARRAY['S','A','E']
        WHEN 'humanities'    THEN ARRAY['A','S','I']
        WHEN 'arts'          THEN ARRAY['A','S','E']
        WHEN 'science'       THEN ARRAY['I','R','A']
        ELSE ARRAY['I','E','S']
    END,
    -- Interest codes (slightly different from aptitude)
    CASE ts.category
        WHEN 'medical'       THEN ARRAY['I','S','R']
        WHEN 'nursing'       THEN ARRAY['S','C','I']
        WHEN 'pharmacy'      THEN ARRAY['I','R','C']
        WHEN 'health'        THEN ARRAY['S','R','I']
        WHEN 'it_engineering' THEN ARRAY['I','C','R']
        WHEN 'architecture'  THEN ARRAY['A','R','I']
        WHEN 'civil_eng'     THEN ARRAY['R','C','I']
        WHEN 'mechanical'    THEN ARRAY['R','C','I']
        WHEN 'electrical'    THEN ARRAY['I','C','R']
        WHEN 'chemical_env'  THEN ARRAY['I','C','R']
        WHEN 'industrial'    THEN ARRAY['E','I','C']
        WHEN 'business'      THEN ARRAY['E','S','C']
        WHEN 'law_admin'     THEN ARRAY['C','E','I']
        WHEN 'education'     THEN ARRAY['S','E','A']
        WHEN 'humanities'    THEN ARRAY['A','I','S']
        WHEN 'arts'          THEN ARRAY['A','E','S']
        WHEN 'science'       THEN ARRAY['I','A','R']
        ELSE ARRAY['E','I','S']
    END,
    -- job_match_scores: 3 roles per category
    CASE ts.category
        WHEN 'medical'       THEN '{"의사": 92, "의학연구원": 85, "보건관리자": 78}'::jsonb
        WHEN 'nursing'       THEN '{"간호사": 94, "보건교육사": 82, "의료코디네이터": 76}'::jsonb
        WHEN 'pharmacy'      THEN '{"약사": 93, "제약연구원": 86, "임상시험관리자": 79}'::jsonb
        WHEN 'health'        THEN '{"보건관리자": 88, "건강관리사": 82, "의료행정가": 75}'::jsonb
        WHEN 'it_engineering' THEN '{"소프트웨어엔지니어": 91, "데이터분석가": 84, "시스템관리자": 78}'::jsonb
        WHEN 'architecture'  THEN '{"건축설계사": 93, "건축시공관리자": 85, "인테리어디자이너": 77}'::jsonb
        WHEN 'civil_eng'     THEN '{"토목엔지니어": 92, "건설관리자": 86, "환경엔지니어": 78}'::jsonb
        WHEN 'mechanical'    THEN '{"기계설계엔지니어": 91, "자동차엔지니어": 85, "품질관리자": 77}'::jsonb
        WHEN 'electrical'    THEN '{"전자엔지니어": 92, "반도체엔지니어": 88, "임베디드개발자": 80}'::jsonb
        WHEN 'chemical_env'  THEN '{"화학공정엔지니어": 90, "환경엔지니어": 84, "연구원": 78}'::jsonb
        WHEN 'industrial'    THEN '{"산업엔지니어": 89, "품질관리전문가": 83, "물류관리자": 76}'::jsonb
        WHEN 'business'      THEN '{"경영컨설턴트": 87, "재무분석가": 82, "마케터": 76}'::jsonb
        WHEN 'law_admin'     THEN '{"법률전문가": 88, "행정관": 83, "정책분석가": 77}'::jsonb
        WHEN 'education'     THEN '{"교사": 92, "교육컨설턴트": 84, "상담사": 78}'::jsonb
        WHEN 'humanities'    THEN '{"연구원": 85, "편집자": 80, "콘텐츠기획자": 76}'::jsonb
        WHEN 'arts'          THEN '{"디자이너": 89, "아트디렉터": 83, "큐레이터": 77}'::jsonb
        WHEN 'science'       THEN '{"연구원": 91, "데이터과학자": 84, "기술직공무원": 77}'::jsonb
        ELSE '{"사무직": 80, "영업직": 75, "서비스직": 70}'::jsonb
    END,
    jsonb_build_object(
        'test_type', 'Holland RIASEC',
        'test_version', '2024.1',
        'test_duration_minutes', 40 + abs(hashtext(ts.student_id || 'dur')) % 20,
        'reliability_score', 0.85 + (abs(hashtext(ts.student_id || 'rel')) % 10)::numeric / 100
    ),
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
WHERE NOT EXISTS (
    SELECT 1 FROM tb_worknet_diagnosis wd WHERE wd.student_id = ts.student_id
);

DO $$ BEGIN RAISE NOTICE 'Part 13 완료: tb_worknet_diagnosis 생성 (% 건)',
    (SELECT count(*) FROM tb_worknet_diagnosis WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 14: tb_constraint_check (3건/학생)
-- check_type: graduation, gpa, credit
-- 졸업생이므로 result_passed = TRUE
-- =====================================================

INSERT INTO tb_constraint_check (
    check_id, student_id, check_type, check_date,
    target_term_cd, input_data, result_passed, violations,
    ins_user_id, ins_dt
)
SELECT
    gen_random_uuid(),
    ts.student_id,
    chk.check_type,
    NOW() - (abs(hashtext(ts.student_id || chk.check_type || 'cd')) % 60 || ' days')::interval,
    '2024-2',
    chk.input_data,
    TRUE,
    NULL,
    'SEED_48',
    NOW()
FROM tmp_showcase_48 ts
CROSS JOIN (
    VALUES
        ('graduation'::varchar,
         '{"total_credits": 140, "required_credits": 130, "major_credits": 72, "required_major": 66, "general_credits": 42, "required_general": 36}'::jsonb),
        ('gpa'::varchar,
         '{"current_gpa": 3.5, "required_gpa": 2.0, "major_gpa": 3.6, "required_major_gpa": 2.5}'::jsonb),
        ('credit'::varchar,
         '{"earned_credits": 140, "registered_credits": 18, "max_credits": 21, "remaining_required": 0}'::jsonb)
) AS chk(check_type, input_data)
WHERE NOT EXISTS (
    SELECT 1 FROM tb_constraint_check cc
    WHERE cc.student_id = ts.student_id AND cc.check_type = chk.check_type AND cc.ins_user_id = 'SEED_48'
);

DO $$ BEGIN RAISE NOTICE 'Part 14 완료: tb_constraint_check 생성 (% 건)',
    (SELECT count(*) FROM tb_constraint_check WHERE ins_user_id = 'SEED_48'); END $$;


-- =====================================================
-- Part 15: Cleanup + 통계 출력
-- =====================================================

DROP TABLE IF EXISTS tmp_dept_cat_48;
DROP TABLE IF EXISTS tmp_showcase_48;
DROP TABLE IF EXISTS tmp_roadmap_items_48;

COMMIT;

-- 통계 출력
DO $$
DECLARE
    v_roadmap_items INT;
    v_checkins INT;
    v_retros INT;
    v_assessments INT;
    v_assessment_results INT;
    v_opp_recs INT;
    v_opp_apps INT;
    v_passports INT;
    v_interventions INT;
    v_notes INT;
    v_comparisons INT;
    v_runs INT;
    v_items INT;
    v_evidences INT;
    v_feedbacks INT;
    v_diagnoses INT;
    v_constraints INT;
    v_total INT;
BEGIN
    SELECT count(*) INTO v_roadmap_items FROM tb_roadmap_item WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_checkins FROM tb_coaching_checkin WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_retros FROM tb_coaching_retrospective WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_assessments FROM tb_assessment WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_assessment_results FROM tb_assessment_result WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_opp_recs FROM tb_opportunity_recommendation WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_opp_apps FROM tb_opportunity_application WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_passports FROM tb_skill_passport WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_interventions FROM tb_advisor_intervention WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_notes FROM tb_advisor_note WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_comparisons FROM tb_scenario_comparison WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_runs FROM tb_recommendation_run rr WHERE rr.model_version = 'v1.0' AND rr.status = 'completed'
        AND rr.context_data ? 'trigger';
    SELECT count(*) INTO v_items FROM tb_recommendation_item ri
        JOIN tb_recommendation_run rr ON ri.run_id = rr.run_id
        WHERE rr.model_version = 'v1.0' AND rr.context_data ? 'trigger';
    SELECT count(*) INTO v_evidences FROM tb_recommendation_evidence WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_feedbacks FROM tb_feedback_event fe
        JOIN tb_recommendation_run rr ON fe.run_id = rr.run_id
        WHERE rr.model_version = 'v1.0';
    SELECT count(*) INTO v_diagnoses FROM tb_worknet_diagnosis WHERE ins_user_id = 'SEED_48';
    SELECT count(*) INTO v_constraints FROM tb_constraint_check WHERE ins_user_id = 'SEED_48';

    v_total := v_roadmap_items + v_checkins + v_retros + v_assessments + v_assessment_results +
               v_opp_recs + v_opp_apps + v_passports + v_interventions + v_notes +
               v_comparisons + v_runs + v_items + v_evidences + v_feedbacks +
               v_diagnoses + v_constraints;

    RAISE NOTICE '================================================';
    RAISE NOTICE '48_e2e_showcase_students.sql 실행 완료';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'tb_roadmap_item:              % 건', v_roadmap_items;
    RAISE NOTICE 'tb_coaching_checkin:           % 건', v_checkins;
    RAISE NOTICE 'tb_coaching_retrospective:     % 건', v_retros;
    RAISE NOTICE 'tb_assessment:                 % 건', v_assessments;
    RAISE NOTICE 'tb_assessment_result:          % 건', v_assessment_results;
    RAISE NOTICE 'tb_opportunity_recommendation: % 건', v_opp_recs;
    RAISE NOTICE 'tb_opportunity_application:    % 건', v_opp_apps;
    RAISE NOTICE 'tb_skill_passport:             % 건', v_passports;
    RAISE NOTICE 'tb_advisor_intervention:       % 건', v_interventions;
    RAISE NOTICE 'tb_advisor_note:               % 건', v_notes;
    RAISE NOTICE 'tb_scenario_comparison:        % 건', v_comparisons;
    RAISE NOTICE 'tb_recommendation_run:         % 건', v_runs;
    RAISE NOTICE 'tb_recommendation_item:        % 건', v_items;
    RAISE NOTICE 'tb_recommendation_evidence:    % 건', v_evidences;
    RAISE NOTICE 'tb_feedback_event:             % 건', v_feedbacks;
    RAISE NOTICE 'tb_worknet_diagnosis:          % 건', v_diagnoses;
    RAISE NOTICE 'tb_constraint_check:           % 건', v_constraints;
    RAISE NOTICE '총합:                          % 건', v_total;
    RAISE NOTICE '================================================';
END $$;
