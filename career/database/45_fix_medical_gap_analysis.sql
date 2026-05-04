-- 의예과/의학 관련 학과 학생의 gap analysis target_role을 ROLE101(의사)로 수정
UPDATE tb_skill_gap_analysis sga
SET target_role_cd = 'ROLE101',
    top_priority_skills = ARRAY['생물학', '의학입문', '인체해부학'],
    upd_dt = NOW()
FROM tb_student s
JOIN tb_department d ON s.department_cd = d.department_cd
WHERE sga.student_id = s.student_id
  AND d.department_nm ~ '의예|의학'
  AND sga.target_role_cd NOT IN ('ROLE101','ROLE102','ROLE103','ROLE104','ROLE105');
