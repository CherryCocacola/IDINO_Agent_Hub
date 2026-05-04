-- IDINO Career 데이터 수정 SQL
-- 생성 시각: 2026-01-21 21:12:08
-- 스키마: idino_career

SET search_path TO idino_career;


-- tb_college: college_nm과 college_nm_en 값 교환 (한글→영문, 영문→한글)
UPDATE idino_career.tb_college
SET college_nm = college_nm_en, college_nm_en = college_nm
WHERE college_nm ~ '[가-힣]';


-- tb_department: department_nm과 department_nm_en 값 교환 (한글→영문, 영문→한글)
UPDATE idino_career.tb_department
SET department_nm = department_nm_en, department_nm_en = department_nm
WHERE department_nm ~ '[가-힣]';
