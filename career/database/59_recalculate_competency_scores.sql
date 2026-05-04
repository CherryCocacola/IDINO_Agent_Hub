-- ============================================================
-- 59_recalculate_competency_scores.sql
-- 역량 점수 재계산: 과목-역량 매핑 데이터 기반 + 백분위 status
-- ============================================================

SET search_path TO idino_career, public;

BEGIN;

-- ============================================================
-- 1. 컬럼 타입 확장 (DECIMAL(5,2) → DECIMAL(10,2))
--    재계산 점수가 3000+ 가능하므로 확장 필요
-- ============================================================
ALTER TABLE tb_student_competency
    ALTER COLUMN current_score TYPE DECIMAL(10,2),
    ALTER COLUMN target_score  TYPE DECIMAL(10,2),
    ALTER COLUMN gap_score     TYPE DECIMAL(10,2);

-- ============================================================
-- 2. 과목 데이터로 점수 재계산
--    score = SUM(contribution_weight * grade_point * credits_earned)
--    tb_grade + tb_course_competency_map 조인
--    매핑되는 과목이 있는 학생만 업데이트
-- ============================================================
WITH calculated_scores AS (
    SELECT
        g.student_id,
        ccm.competency_cd,
        SUM(ccm.contribution_weight * g.grade_point * g.credits_earned) AS new_score
    FROM tb_grade g
    JOIN tb_course_competency_map ccm ON g.course_cd = ccm.course_cd
    WHERE g.grade_point IS NOT NULL
      AND g.credits_earned IS NOT NULL
      AND g.credits_earned > 0
    GROUP BY g.student_id, ccm.competency_cd
)
UPDATE tb_student_competency sc
SET
    current_score = cs.new_score,
    gap_score     = cs.new_score - sc.target_score,
    upd_user_id   = 'SYSTEM_RECALC',
    upd_dt        = CURRENT_TIMESTAMP
FROM calculated_scores cs
WHERE sc.student_id   = cs.student_id
  AND sc.competency_cd = cs.competency_cd;

-- ============================================================
-- 3. 동일학과 백분위 기반 status 업데이트
--    >= 75th percentile → 'excellent'
--    >= 50th percentile → 'good'
--    >= 25th percentile → 'average'
--    < 25th percentile  → 'needs_improvement'
-- ============================================================
WITH dept_percentiles AS (
    SELECT
        sc.student_competency_id,
        PERCENT_RANK() OVER (
            PARTITION BY s.department_cd, sc.competency_cd
            ORDER BY sc.current_score
        ) AS pct_rank
    FROM tb_student_competency sc
    JOIN tb_student s ON sc.student_id = s.student_id
    JOIN tb_competency c ON sc.competency_cd = c.competency_cd AND c.use_fg = 'Y'
)
UPDATE tb_student_competency sc
SET
    status = CASE
        WHEN dp.pct_rank >= 0.75 THEN 'excellent'
        WHEN dp.pct_rank >= 0.50 THEN 'good'
        WHEN dp.pct_rank >= 0.25 THEN 'average'
        ELSE 'needs_improvement'
    END,
    upd_user_id = 'SYSTEM_RECALC',
    upd_dt      = CURRENT_TIMESTAMP
FROM dept_percentiles dp
WHERE sc.student_competency_id = dp.student_competency_id;

COMMIT;

-- ============================================================
-- 검증 쿼리 (실행 후 확인용)
-- ============================================================

-- 점수 분포 확인: 100점 고정 학생 수 감소 확인
-- SELECT
--     CASE
--         WHEN current_score = 100 THEN 'exactly_100'
--         WHEN current_score > 100 THEN 'over_100'
--         ELSE 'under_100'
--     END AS score_range,
--     COUNT(DISTINCT student_id) AS student_count
-- FROM tb_student_competency
-- GROUP BY 1;

-- Status 분포 확인
-- SELECT status, COUNT(*) AS cnt
-- FROM tb_student_competency
-- GROUP BY status
-- ORDER BY cnt DESC;

-- 특정 학생 확인
-- SELECT sc.student_id, sc.competency_cd, c.competency_nm,
--        sc.current_score, sc.status
-- FROM tb_student_competency sc
-- JOIN tb_competency c ON sc.competency_cd = c.competency_cd
-- WHERE sc.student_id = '20234317'
-- ORDER BY sc.competency_cd;
