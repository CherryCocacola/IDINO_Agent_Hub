# IDINO Career 테이블 정의서

> 생성일시: 2026-01-07 21:30:25
> 스키마: `idino_career`
> 테이블 수: 70개

---

## 목차

### Academic Base
- [tb_college](#tb-college)
- [tb_course](#tb-course)
- [tb_course_offering](#tb-course-offering)
- [tb_department](#tb-department)
- [tb_prerequisite](#tb-prerequisite)
- [tb_professor](#tb-professor)
- [tb_professor_course](#tb-professor-course)
- [tb_university](#tb-university)

### Student & Enrollment
- [tb_cumulative_summary](#tb-cumulative-summary)
- [tb_enrollment](#tb-enrollment)
- [tb_grade](#tb-grade)
- [tb_grade_summary](#tb-grade-summary)
- [tb_student](#tb-student)
- [tb_term](#tb-term)

### Competency & Skill
- [tb_assessment](#tb-assessment)
- [tb_assessment_result](#tb-assessment-result)
- [tb_competency](#tb-competency)
- [tb_course_competency_map](#tb-course-competency-map)
- [tb_skill](#tb-skill)
- [tb_skill_competency_map](#tb-skill-competency-map)
- [tb_skill_gap_analysis](#tb-skill-gap-analysis)
- [tb_student_competency](#tb-student-competency)
- [tb_student_skill](#tb-student-skill)

### Activity & Achievement
- [tb_achievement](#tb-achievement)
- [tb_opportunity](#tb-opportunity)
- [tb_opportunity_application](#tb-opportunity-application)
- [tb_participation](#tb-participation)
- [tb_portfolio](#tb-portfolio)
- [tb_program](#tb-program)

### Job & Alumni
- [tb_alumni_cohort](#tb-alumni-cohort)
- [tb_role](#tb-role)
- [tb_role_requirement](#tb-role-requirement)
- [tb_success_pattern](#tb-success-pattern)
- [tb_worknet_diagnosis](#tb-worknet-diagnosis)

### Career
- [tb_career_history](#tb-career-history)
- [tb_student_career](#tb-student-career)

### Coaching & Risk
- [tb_coaching_goal](#tb-coaching-goal)
- [tb_risk_alert](#tb-risk-alert)

### Badge & Simulation
- [tb_simulation_scenario](#tb-simulation-scenario)
- [tb_student_badge](#tb-student-badge)

### Advisor
- [tb_advisor_intervention](#tb-advisor-intervention)

### Authentication
- [tb_auth_backup_code](#tb-auth-backup-code)
- [tb_auth_otp](#tb-auth-otp)
- [tb_auth_session](#tb-auth-session)
- [tb_login_history](#tb-login-history)
- [tb_user](#tb-user)
- [tb_user_device](#tb-user-device)

### AI Ops
- [tb_eval_case](#tb-eval-case)
- [tb_eval_result](#tb-eval-result)
- [tb_feedback_event](#tb-feedback-event)
- [tb_model_version](#tb-model-version)
- [tb_policy_version](#tb-policy-version)
- [tb_prompt_version](#tb-prompt-version)
- [tb_recommendation_evidence](#tb-recommendation-evidence)
- [tb_recommendation_item](#tb-recommendation-item)
- [tb_recommendation_run](#tb-recommendation-run)

### Other
- [tb_advisor_assignment](#tb-advisor-assignment)
- [tb_advisor_note](#tb-advisor-note)
- [tb_badge](#tb-badge)
- [tb_coaching_checkin](#tb-coaching-checkin)
- [tb_coaching_plan](#tb-coaching-plan)
- [tb_coaching_retrospective](#tb-coaching-retrospective)
- [tb_cohort_snapshot](#tb-cohort-snapshot)
- [tb_constraint_check](#tb-constraint-check)
- [tb_opportunity_recommendation](#tb-opportunity-recommendation)
- [tb_prerequisite_rule](#tb-prerequisite-rule)
- [tb_role_skill_map](#tb-role-skill-map)
- [tb_scenario_comparison](#tb-scenario-comparison)
- [tb_skill_passport](#tb-skill-passport)
- [tb_skill_relation](#tb-skill-relation)

---

# Academic Base

## tb_college

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `college_cd` | varchar(20) | X | - |  |
| 2 | `university_cd` | varchar(20) | O | - |  |
| 3 | `college_nm` | varchar(100) | X | - |  |
| 4 | `college_nm_en` | varchar(100) | O | - |  |
| 5 | `sort_order` | integer | O | - |  |
| 6 | `ins_user_id` | varchar(50) | O | - |  |
| 7 | `ins_user_ip` | varchar(50) | O | - |  |
| 8 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 9 | `ins_system_gcd` | varchar(10) | O | - |  |
| 10 | `ins_menu_cd` | varchar(20) | O | - |  |
| 11 | `upd_user_id` | varchar(50) | O | - |  |
| 12 | `upd_user_ip` | varchar(50) | O | - |  |
| 13 | `upd_dt` | timestamp | O | - |  |
| 14 | `upd_system_gcd` | varchar(10) | O | - |  |
| 15 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `college_cd`
- **FK**: `university_cd` → `tb_university(university_cd)`

---

## tb_course

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `course_cd` | varchar(20) | X | - |  |
| 2 | `course_nm` | varchar(100) | X | - |  |
| 3 | `course_nm_en` | varchar(100) | O | - |  |
| 4 | `department_cd` | varchar(20) | O | - |  |
| 5 | `credits` | integer | X | 3 |  |
| 6 | `course_type` | varchar(20) | O | - |  |
| 7 | `grade_level` | integer | O | - |  |
| 8 | `description` | text | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_user_ip` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 12 | `ins_system_gcd` | varchar(10) | O | - |  |
| 13 | `ins_menu_cd` | varchar(20) | O | - |  |
| 14 | `upd_user_id` | varchar(50) | O | - |  |
| 15 | `upd_user_ip` | varchar(50) | O | - |  |
| 16 | `upd_dt` | timestamp | O | - |  |
| 17 | `upd_system_gcd` | varchar(10) | O | - |  |
| 18 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `course_cd`
- **FK**: `department_cd` → `tb_department(department_cd)`

---

## tb_course_offering

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `offering_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `course_cd` | varchar(20) | O | - |  |
| 3 | `term_cd` | varchar(10) | O | - |  |
| 4 | `professor_cd` | varchar(20) | O | - |  |
| 5 | `section` | varchar(10) | O | - |  |
| 6 | `capacity` | integer | O | 40 |  |
| 7 | `enrolled_count` | integer | O | 0 |  |
| 8 | `schedule` | varchar(100) | O | - |  |
| 9 | `classroom` | varchar(50) | O | - |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `offering_id`
- **FK**: `course_cd` → `tb_course(course_cd)`
- **FK**: `professor_cd` → `tb_professor(professor_cd)`
- **FK**: `term_cd` → `tb_term(term_cd)`
- **UNIQUE**: `term_cd, term_cd, term_cd, section, section, section, course_cd, course_cd, course_cd`

### 인덱스

- `tb_course_offering_course_cd_term_cd_section_key`

---

## tb_department

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `department_cd` | varchar(20) | X | - |  |
| 2 | `college_cd` | varchar(20) | O | - |  |
| 3 | `department_nm` | varchar(100) | X | - |  |
| 4 | `department_nm_en` | varchar(100) | O | - |  |
| 5 | `graduation_credits` | integer | O | 130 |  |
| 6 | `sort_order` | integer | O | - |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_user_ip` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 10 | `ins_system_gcd` | varchar(10) | O | - |  |
| 11 | `ins_menu_cd` | varchar(20) | O | - |  |
| 12 | `upd_user_id` | varchar(50) | O | - |  |
| 13 | `upd_user_ip` | varchar(50) | O | - |  |
| 14 | `upd_dt` | timestamp | O | - |  |
| 15 | `upd_system_gcd` | varchar(10) | O | - |  |
| 16 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `department_cd`
- **FK**: `college_cd` → `tb_college(college_cd)`

---

## tb_prerequisite

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `prerequisite_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `course_cd` | varchar(20) | O | - |  |
| 3 | `prerequisite_course_cd` | varchar(20) | O | - |  |
| 4 | `is_required` | boolean | O | true |  |
| 5 | `ins_user_id` | varchar(50) | O | - |  |
| 6 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `prerequisite_id`
- **FK**: `course_cd` → `tb_course(course_cd)`
- **FK**: `prerequisite_course_cd` → `tb_course(course_cd)`
- **UNIQUE**: `prerequisite_course_cd, prerequisite_course_cd, course_cd, course_cd`

### 인덱스

- `tb_prerequisite_course_cd_prerequisite_course_cd_key`

---

## tb_professor

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `professor_cd` | varchar(20) | X | - |  |
| 2 | `professor_nm` | varchar(50) | X | - |  |
| 3 | `department_cd` | varchar(20) | O | - |  |
| 4 | `email` | varchar(100) | O | - |  |
| 5 | `phone` | varchar(20) | O | - |  |
| 6 | `office` | varchar(100) | O | - |  |
| 7 | `specialty` | varchar(200) | O | - |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_user_ip` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 11 | `ins_system_gcd` | varchar(10) | O | - |  |
| 12 | `ins_menu_cd` | varchar(20) | O | - |  |
| 13 | `upd_user_id` | varchar(50) | O | - |  |
| 14 | `upd_user_ip` | varchar(50) | O | - |  |
| 15 | `upd_dt` | timestamp | O | - |  |
| 16 | `upd_system_gcd` | varchar(10) | O | - |  |
| 17 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `professor_cd`
- **FK**: `department_cd` → `tb_department(department_cd)`

---

## tb_professor_course

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `mapping_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `professor_cd` | varchar(20) | O | - |  |
| 3 | `course_cd` | varchar(20) | O | - |  |
| 4 | `is_primary` | boolean | O | true |  |
| 5 | `ins_user_id` | varchar(50) | O | - |  |
| 6 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `mapping_id`
- **FK**: `course_cd` → `tb_course(course_cd)`
- **FK**: `professor_cd` → `tb_professor(professor_cd)`
- **UNIQUE**: `course_cd, professor_cd, professor_cd, course_cd`

### 인덱스

- `tb_professor_course_professor_cd_course_cd_key`

---

## tb_university

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `university_cd` | varchar(20) | X | - |  |
| 2 | `university_nm` | varchar(100) | X | - |  |
| 3 | `university_nm_en` | varchar(100) | O | - |  |
| 4 | `address` | varchar(200) | O | - |  |
| 5 | `phone` | varchar(20) | O | - |  |
| 6 | `website` | varchar(100) | O | - |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_user_ip` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 10 | `ins_system_gcd` | varchar(10) | O | - |  |
| 11 | `ins_menu_cd` | varchar(20) | O | - |  |
| 12 | `upd_user_id` | varchar(50) | O | - |  |
| 13 | `upd_user_ip` | varchar(50) | O | - |  |
| 14 | `upd_dt` | timestamp | O | - |  |
| 15 | `upd_system_gcd` | varchar(10) | O | - |  |
| 16 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `university_cd`

---

# Student & Enrollment

## tb_cumulative_summary

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `summary_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `total_credits_attempted` | integer | O | 0 |  |
| 4 | `total_credits_earned` | integer | O | 0 |  |
| 5 | `total_grade_points` | decimal(7,2) | O | 0 |  |
| 6 | `cumulative_gpa` | decimal(3,2) | O | 0 |  |
| 7 | `major_credits` | integer | O | 0 |  |
| 8 | `major_gpa` | decimal(3,2) | O | 0 |  |
| 9 | `last_updated` | timestamp | O | CURRENT_TIMESTAMP |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `summary_id`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `student_id`

### 인덱스

- `tb_cumulative_summary_student_id_key`

---

## tb_enrollment

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `enrollment_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `offering_id` | uuid | O | - |  |
| 4 | `enrollment_status` | varchar(20) | O | 'enrolled'::character varying |  |
| 5 | `enrollment_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 6 | `ins_user_id` | varchar(50) | O | - |  |
| 7 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `enrollment_id`
- **FK**: `offering_id` → `tb_course_offering(offering_id)`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_enrollment_offering`
- `idx_enrollment_student`

---

## tb_grade

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `grade_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `enrollment_id` | uuid | O | - |  |
| 3 | `grade` | varchar(5) | O | - |  |
| 4 | `grade_point` | decimal(3,2) | O | - |  |
| 5 | `is_pass` | boolean | O | true |  |
| 6 | `ins_user_id` | varchar(50) | O | - |  |
| 7 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `grade_id`
- **FK**: `enrollment_id` → `tb_enrollment(enrollment_id)`

### 인덱스

- `idx_grade_enrollment`

---

## tb_grade_summary

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `summary_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `term_cd` | varchar(10) | O | - |  |
| 4 | `credits_attempted` | integer | O | 0 |  |
| 5 | `credits_earned` | integer | O | 0 |  |
| 6 | `grade_points` | decimal(5,2) | O | 0 |  |
| 7 | `gpa` | decimal(3,2) | O | 0 |  |
| 8 | `major_gpa` | decimal(3,2) | O | 0 |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `summary_id`
- **FK**: `student_id` → `tb_student(student_id)`
- **FK**: `term_cd` → `tb_term(term_cd)`
- **UNIQUE**: `term_cd, student_id, student_id, term_cd`

### 인덱스

- `tb_grade_summary_student_id_term_cd_key`

---

## tb_student

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `student_id` | varchar(20) | X | - |  |
| 2 | `student_nm` | varchar(50) | X | - |  |
| 3 | `university_cd` | varchar(20) | O | - |  |
| 4 | `department_cd` | varchar(20) | O | - |  |
| 5 | `admission_year` | integer | X | - |  |
| 6 | `current_grade` | integer | X | - |  |
| 7 | `current_semester` | integer | X | - |  |
| 8 | `email` | varchar(100) | O | - |  |
| 9 | `phone` | varchar(20) | O | - |  |
| 10 | `birth_date` | date | O | - |  |
| 11 | `gender` | char(1) | O | - |  |
| 12 | `status` | varchar(20) | O | 'enrolled'::character varying |  |
| 13 | `career_goal` | varchar(200) | O | - |  |
| 14 | `ins_user_id` | varchar(50) | O | - |  |
| 15 | `ins_user_ip` | varchar(50) | O | - |  |
| 16 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 17 | `ins_system_gcd` | varchar(10) | O | - |  |
| 18 | `ins_menu_cd` | varchar(20) | O | - |  |
| 19 | `upd_user_id` | varchar(50) | O | - |  |
| 20 | `upd_user_ip` | varchar(50) | O | - |  |
| 21 | `upd_dt` | timestamp | O | - |  |
| 22 | `upd_system_gcd` | varchar(10) | O | - |  |
| 23 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `student_id`
- **FK**: `department_cd` → `tb_department(department_cd)`
- **FK**: `university_cd` → `tb_university(university_cd)`

### 인덱스

- `idx_student_department`
- `idx_student_grade`
- `idx_student_status`

---

## tb_term

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `term_cd` | varchar(10) | X | - |  |
| 2 | `term_nm` | varchar(50) | X | - |  |
| 3 | `start_date` | date | X | - |  |
| 4 | `end_date` | date | X | - |  |
| 5 | `registration_start` | date | O | - |  |
| 6 | `registration_end` | date | O | - |  |
| 7 | `is_current` | boolean | O | false |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `term_cd`

---

# Competency & Skill

## tb_assessment

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `assessment_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `assessment_type` | varchar(20) | X | - |  |
| 4 | `assessment_dt` | timestamp | X | - |  |
| 5 | `ins_user_id` | varchar(50) | O | - |  |
| 6 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `assessment_id`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_assessment_student`

---

## tb_assessment_result

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `result_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `assessment_id` | uuid | O | - |  |
| 3 | `competency_cd` | varchar(20) | O | - |  |
| 4 | `raw_score` | decimal(5,2) | X | - |  |
| 5 | `adjusted_score` | decimal(5,2) | O | - |  |
| 6 | `academic_contribution` | decimal(5,2) | O | - |  |
| 7 | `extracurricular_boost` | decimal(5,2) | O | - |  |
| 8 | `final_score` | decimal(5,2) | X | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `result_id`
- **FK**: `assessment_id` → `tb_assessment(assessment_id)`
- **FK**: `competency_cd` → `tb_competency(competency_cd)`

---

## tb_competency

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `competency_cd` | varchar(20) | X | - |  |
| 2 | `competency_nm` | varchar(100) | X | - |  |
| 3 | `competency_nm_en` | varchar(100) | O | - |  |
| 4 | `description` | text | O | - |  |
| 5 | `weight` | decimal(5,2) | O | 0.00 |  |
| 6 | `max_score` | integer | O | 100 |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `competency_cd`

---

## tb_course_competency_map

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `mapping_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `course_cd` | varchar(20) | O | - |  |
| 3 | `competency_cd` | varchar(20) | O | - |  |
| 4 | `contribution_weight` | decimal(5,2) | X | - |  |

### 제약조건

- **PK**: `mapping_id`
- **FK**: `competency_cd` → `tb_competency(competency_cd)`
- **FK**: `course_cd` → `tb_course(course_cd)`
- **UNIQUE**: `competency_cd, competency_cd, course_cd, course_cd`

### 인덱스

- `tb_course_competency_map_course_cd_competency_cd_key`

---

## tb_skill

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `skill_cd` | varchar(20) | X | - |  |
| 2 | `skill_nm` | varchar(100) | X | - |  |
| 3 | `skill_nm_en` | varchar(100) | O | - |  |
| 4 | `category` | varchar(50) | O | - |  |
| 5 | `difficulty_level` | integer | O | - |  |
| 6 | `synonyms` | text[] | O | - |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `skill_cd`

---

## tb_skill_competency_map

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `mapping_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `skill_cd` | varchar(20) | O | - |  |
| 3 | `competency_cd` | varchar(20) | O | - |  |
| 4 | `contribution_weight` | decimal(5,2) | O | 1.00 |  |

### 제약조건

- **PK**: `mapping_id`
- **FK**: `competency_cd` → `tb_competency(competency_cd)`
- **FK**: `skill_cd` → `tb_skill(skill_cd)`
- **UNIQUE**: `competency_cd, skill_cd, skill_cd, competency_cd`

### 인덱스

- `tb_skill_competency_map_skill_cd_competency_cd_key`

---

## tb_skill_gap_analysis

**설명**: 스킬 갭 분석 결과

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `analysis_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `target_role_cd` | varchar(20) | O | - |  |
| 4 | `analysis_date` | timestamp | O | CURRENT_TIMESTAMP |  |
| 5 | `overall_gap_score` | decimal(5,2) | O | - |  |
| 6 | `gap_details` | jsonb | X | - |  |
| 7 | `top_priority_skills` | varchar[] | O | - |  |
| 8 | `recommended_actions` | jsonb | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_user_ip` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 12 | `ins_system_gcd` | varchar(10) | O | - |  |
| 13 | `ins_menu_cd` | varchar(20) | O | - |  |
| 14 | `upd_user_id` | varchar(50) | O | - |  |
| 15 | `upd_user_ip` | varchar(50) | O | - |  |
| 16 | `upd_dt` | timestamp | O | - |  |
| 17 | `upd_system_gcd` | varchar(10) | O | - |  |
| 18 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `analysis_id`
- **FK**: `student_id` → `tb_student(student_id)`
- **FK**: `target_role_cd` → `tb_role(role_cd)`

### 인덱스

- `idx_skill_gap_analysis_student`

---

## tb_student_competency

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `record_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `competency_cd` | varchar(20) | O | - |  |
| 4 | `current_score` | decimal(5,2) | O | 0 |  |
| 5 | `target_score` | decimal(5,2) | O | 100 |  |
| 6 | `status` | varchar(20) | O | 'developing'::character varying |  |
| 7 | `last_updated` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `record_id`
- **FK**: `competency_cd` → `tb_competency(competency_cd)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `competency_cd, student_id, student_id, competency_cd`

### 인덱스

- `idx_student_competency_student`
- `tb_student_competency_student_id_competency_cd_key`

---

## tb_student_skill

**설명**: 학생 스킬 현황

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `student_skill_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `skill_cd` | varchar(20) | O | - |  |
| 4 | `current_level` | integer | O | 1 |  |
| 5 | `target_level` | integer | O | 3 |  |
| 6 | `evidence_count` | integer | O | 0 |  |
| 7 | `last_verified_date` | date | O | - |  |
| 8 | `verification_source` | varchar(50) | O | - |  |
| 9 | `trend` | varchar(10) | O | 'stable'::character varying |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_user_ip` | varchar(50) | O | - |  |
| 12 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 13 | `ins_system_gcd` | varchar(10) | O | - |  |
| 14 | `ins_menu_cd` | varchar(20) | O | - |  |
| 15 | `upd_user_id` | varchar(50) | O | - |  |
| 16 | `upd_user_ip` | varchar(50) | O | - |  |
| 17 | `upd_dt` | timestamp | O | - |  |
| 18 | `upd_system_gcd` | varchar(10) | O | - |  |
| 19 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `student_skill_id`
- **FK**: `skill_cd` → `tb_skill(skill_cd)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `skill_cd, student_id, student_id, skill_cd`

### 인덱스

- `idx_student_skill_student`
- `tb_student_skill_student_id_skill_cd_key`

---

# Activity & Achievement

## tb_achievement

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `achievement_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `achievement_type` | varchar(50) | X | - |  |
| 4 | `achievement_nm` | varchar(200) | X | - |  |
| 5 | `issuing_organization` | varchar(200) | O | - |  |
| 6 | `acquired_date` | date | O | - |  |
| 7 | `expiry_date` | date | O | - |  |
| 8 | `score` | varchar(50) | O | - |  |
| 9 | `verified` | boolean | O | false |  |
| 10 | `evidence_url` | text | O | - |  |
| 11 | `ins_user_id` | varchar(50) | O | - |  |
| 12 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `achievement_id`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_achievement_student`

---

## tb_opportunity

**설명**: 기회 (인턴십, 프로젝트, 연구실, 공모전 등)

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `opportunity_id` | uuid | X | gen_random_uuid() |  |
| 2 | `opportunity_type` | varchar(30) | X | - |  |
| 3 | `title` | varchar(300) | X | - |  |
| 4 | `organization` | varchar(200) | O | - |  |
| 5 | `description` | text | O | - |  |
| 6 | `requirements` | jsonb | O | - |  |
| 7 | `benefits` | jsonb | O | - |  |
| 8 | `application_start` | date | O | - |  |
| 9 | `application_end` | date | O | - |  |
| 10 | `start_date` | date | O | - |  |
| 11 | `end_date` | date | O | - |  |
| 12 | `location` | varchar(200) | O | - |  |
| 13 | `remote_available` | boolean | O | false |  |
| 14 | `slots` | integer | O | - |  |
| 15 | `status` | varchar(20) | O | 'open'::character varying |  |
| 16 | `external_url` | text | O | - |  |
| 17 | `tags` | varchar[] | O | - |  |
| 18 | `department_cds` | varchar[] | O | - |  |
| 19 | `competency_contributions` | jsonb | O | - |  |
| 20 | `skill_contributions` | jsonb | O | - |  |
| 21 | `ins_user_id` | varchar(50) | O | - |  |
| 22 | `ins_user_ip` | varchar(50) | O | - |  |
| 23 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 24 | `ins_system_gcd` | varchar(10) | O | - |  |
| 25 | `ins_menu_cd` | varchar(20) | O | - |  |
| 26 | `upd_user_id` | varchar(50) | O | - |  |
| 27 | `upd_user_ip` | varchar(50) | O | - |  |
| 28 | `upd_dt` | timestamp | O | - |  |
| 29 | `upd_system_gcd` | varchar(10) | O | - |  |
| 30 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `opportunity_id`

### 인덱스

- `idx_opportunity_dates`
- `idx_opportunity_status`
- `idx_opportunity_type`

---

## tb_opportunity_application

**설명**: 기회 지원 이력

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `application_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `opportunity_id` | uuid | O | - |  |
| 4 | `applied_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 5 | `status` | varchar(20) | O | 'submitted'::character varying |  |
| 6 | `cover_letter` | text | O | - |  |
| 7 | `attachments` | jsonb | O | - |  |
| 8 | `reviewer_notes` | text | O | - |  |
| 9 | `decision_at` | timestamp | O | - |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_user_ip` | varchar(50) | O | - |  |
| 12 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 13 | `ins_system_gcd` | varchar(10) | O | - |  |
| 14 | `ins_menu_cd` | varchar(20) | O | - |  |
| 15 | `upd_user_id` | varchar(50) | O | - |  |
| 16 | `upd_user_ip` | varchar(50) | O | - |  |
| 17 | `upd_dt` | timestamp | O | - |  |
| 18 | `upd_system_gcd` | varchar(10) | O | - |  |
| 19 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `application_id`
- **FK**: `opportunity_id` → `tb_opportunity(opportunity_id)`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_opportunity_application_student`

---

## tb_participation

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `participation_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `program_cd` | varchar(20) | O | - |  |
| 4 | `participation_status` | varchar(20) | X | - |  |
| 5 | `role` | varchar(50) | O | - |  |
| 6 | `started_at` | timestamp | O | - |  |
| 7 | `completed_at` | timestamp | O | - |  |
| 8 | `certificate_url` | text | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `participation_id`
- **FK**: `program_cd` → `tb_program(program_cd)`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_participation_student`

---

## tb_portfolio

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `portfolio_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `artifact_type` | varchar(50) | X | - |  |
| 4 | `title` | varchar(200) | X | - |  |
| 5 | `url` | text | X | - |  |
| 6 | `description` | text | O | - |  |
| 7 | `is_primary` | boolean | O | false |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `portfolio_id`
- **FK**: `student_id` → `tb_student(student_id)`

---

## tb_program

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `program_cd` | varchar(20) | X | - |  |
| 2 | `program_nm` | varchar(200) | X | - |  |
| 3 | `program_type` | varchar(50) | X | - |  |
| 4 | `organizer` | varchar(200) | O | - |  |
| 5 | `description` | text | O | - |  |
| 6 | `start_date` | date | O | - |  |
| 7 | `end_date` | date | O | - |  |
| 8 | `competency_contributions` | jsonb | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `program_cd`

---

# Job & Alumni

## tb_alumni_cohort

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `cohort_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `department_cd` | varchar(20) | O | - |  |
| 3 | `graduation_year` | integer | X | - |  |
| 4 | `role_cd` | varchar(20) | O | - |  |
| 5 | `sample_size` | integer | X | - |  |
| 6 | `avg_gpa_range` | varchar(20) | O | - |  |
| 7 | `avg_salary_range` | varchar(50) | O | - |  |
| 8 | `competency_profile` | jsonb | O | - |  |
| 9 | `employment_rate` | decimal(5,2) | O | - |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `cohort_id`
- **FK**: `department_cd` → `tb_department(department_cd)`
- **FK**: `role_cd` → `tb_role(role_cd)`

### 인덱스

- `idx_alumni_cohort_department`

---

## tb_role

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `role_cd` | varchar(20) | X | - |  |
| 2 | `role_nm` | varchar(100) | X | - |  |
| 3 | `role_nm_en` | varchar(100) | O | - |  |
| 4 | `worknet_code` | varchar(20) | O | - |  |
| 5 | `category` | varchar(50) | O | - |  |
| 6 | `description` | text | O | - |  |
| 7 | `average_salary` | varchar(50) | O | - |  |
| 8 | `job_outlook` | varchar(200) | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `role_cd`

---

## tb_role_requirement

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `requirement_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `role_cd` | varchar(20) | O | - |  |
| 3 | `competency_cd` | varchar(20) | O | - |  |
| 4 | `required_level` | integer | X | - |  |
| 5 | `importance` | varchar(10) | X | - |  |

### 제약조건

- **PK**: `requirement_id`
- **FK**: `competency_cd` → `tb_competency(competency_cd)`
- **FK**: `role_cd` → `tb_role(role_cd)`
- **UNIQUE**: `competency_cd, role_cd, role_cd, competency_cd`

### 인덱스

- `tb_role_requirement_role_cd_competency_cd_key`

---

## tb_success_pattern

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `pattern_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `department_cd` | varchar(20) | O | - |  |
| 3 | `role_cd` | varchar(20) | O | - |  |
| 4 | `pattern_nm` | varchar(200) | X | - |  |
| 5 | `pattern_rules` | jsonb | X | - |  |
| 6 | `correlation_score` | decimal(5,4) | O | - |  |
| 7 | `lift` | decimal(5,2) | O | - |  |
| 8 | `sample_size` | integer | X | - |  |
| 9 | `description` | text | O | - |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `pattern_id`
- **FK**: `department_cd` → `tb_department(department_cd)`
- **FK**: `role_cd` → `tb_role(role_cd)`

---

## tb_worknet_diagnosis

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `diagnosis_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `diagnosis_type` | varchar(50) | X | - |  |
| 4 | `diagnosis_date` | date | X | - |  |
| 5 | `aptitude_codes` | varchar(50) | O | - |  |
| 6 | `result_summary` | text | O | - |  |
| 7 | `detailed_result` | jsonb | O | - |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `diagnosis_id`
- **FK**: `student_id` → `tb_student(student_id)`

---

# Career

## tb_career_history

**설명**: 진로 목표 변경 이력 테이블 - 상담 및 분석용

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `history_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | X | - |  |
| 3 | `previous_career_goal` | varchar(200) | O | - |  |
| 4 | `new_career_goal` | varchar(200) | O | - |  |
| 5 | `previous_role_cd` | varchar(20) | O | - |  |
| 6 | `new_role_cd` | varchar(20) | O | - |  |
| 7 | `change_reason` | text | O | - |  |
| 8 | `triggered_by` | varchar(50) | O | - | 변경 계기: student(본인), advisor(상담), system(시스템) |
| 9 | `changed_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `history_id`
- **FK**: `new_role_cd` → `tb_role(role_cd)`
- **FK**: `previous_role_cd` → `tb_role(role_cd)`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_career_history_changed_at`
- `idx_career_history_student`
- `idx_career_history_student_id`

---

## tb_student_career

**설명**: 학생 진로 정보 테이블 - tb_student에서 career_goal 분리

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `career_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | X | - |  |
| 3 | `primary_career_goal` | varchar(200) | O | - | 기존 tb_student.career_goal에서 이전된 데이터 |
| 4 | `primary_role_cd` | varchar(20) | O | - |  |
| 5 | `interest_role_cds` | varchar[] | O | - | 관심 있는 직무 코드 배열 (복수 선택) |
| 6 | `interest_industries` | varchar[] | O | - | 관심 산업 분야 배열 |
| 7 | `preferred_company_size` | varchar(20) | O | - |  |
| 8 | `preferred_work_style` | varchar(20) | O | - |  |
| 9 | `preferred_regions` | varchar[] | O | - | 선호 근무 지역 배열 |
| 10 | `resume_prepared` | boolean | O | false |  |
| 11 | `portfolio_prepared` | boolean | O | false |  |
| 12 | `interview_ready` | boolean | O | false |  |
| 13 | `job_search_start_date` | date | O | - |  |
| 14 | `target_employment_date` | date | O | - |  |
| 15 | `career_notes` | text | O | - |  |
| 16 | `advisor_comments` | text | O | - |  |
| 17 | `last_counseling_date` | date | O | - |  |
| 18 | `next_counseling_date` | date | O | - |  |
| 19 | `ins_user_id` | varchar(50) | O | - |  |
| 20 | `ins_user_ip` | varchar(50) | O | - |  |
| 21 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 22 | `ins_system_gcd` | varchar(10) | O | - |  |
| 23 | `ins_menu_cd` | varchar(20) | O | - |  |
| 24 | `upd_user_id` | varchar(50) | O | - |  |
| 25 | `upd_user_ip` | varchar(50) | O | - |  |
| 26 | `upd_dt` | timestamp | O | - |  |
| 27 | `upd_system_gcd` | varchar(10) | O | - |  |
| 28 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `career_id`
- **FK**: `primary_role_cd` → `tb_role(role_cd)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `student_id`

### 인덱스

- `idx_student_career_primary_role`
- `idx_student_career_role`
- `idx_student_career_student`
- `idx_student_career_student_id`
- `tb_student_career_student_id_key`

---

# Coaching & Risk

## tb_coaching_goal

**설명**: 코칭 목표

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `goal_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `goal_type` | varchar(30) | X | - |  |
| 4 | `title` | varchar(200) | X | - |  |
| 5 | `description` | text | O | - |  |
| 6 | `target_role_cd` | varchar(20) | O | - |  |
| 7 | `target_metrics` | jsonb | O | - |  |
| 8 | `current_metrics` | jsonb | O | - |  |
| 9 | `deadline` | date | O | - |  |
| 10 | `priority` | integer | O | 1 |  |
| 11 | `status` | varchar(20) | O | 'active'::character varying |  |
| 12 | `achievement_rate` | decimal(5,2) | O | 0 |  |
| 13 | `created_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 14 | `achieved_at` | timestamp | O | - |  |
| 15 | `ins_user_id` | varchar(50) | O | - |  |
| 16 | `ins_user_ip` | varchar(50) | O | - |  |
| 17 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 18 | `ins_system_gcd` | varchar(10) | O | - |  |
| 19 | `ins_menu_cd` | varchar(20) | O | - |  |
| 20 | `upd_user_id` | varchar(50) | O | - |  |
| 21 | `upd_user_ip` | varchar(50) | O | - |  |
| 22 | `upd_dt` | timestamp | O | - |  |
| 23 | `upd_system_gcd` | varchar(10) | O | - |  |
| 24 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `goal_id`
- **FK**: `student_id` → `tb_student(student_id)`
- **FK**: `target_role_cd` → `tb_role(role_cd)`

### 인덱스

- `idx_coaching_goal_status`
- `idx_coaching_goal_student`

---

## tb_risk_alert

**설명**: 위험 알림

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `alert_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `alert_type` | varchar(50) | X | - |  |
| 4 | `severity` | varchar(20) | X | - |  |
| 5 | `title` | varchar(200) | X | - |  |
| 6 | `description` | text | O | - |  |
| 7 | `affected_items` | jsonb | O | - |  |
| 8 | `recommended_actions` | jsonb | O | - |  |
| 9 | `detected_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 10 | `status` | varchar(20) | O | 'active'::character varying |  |
| 11 | `acknowledged_at` | timestamp | O | - |  |
| 12 | `resolved_at` | timestamp | O | - |  |
| 13 | `resolution_notes` | text | O | - |  |
| 14 | `ins_user_id` | varchar(50) | O | - |  |
| 15 | `ins_user_ip` | varchar(50) | O | - |  |
| 16 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 17 | `ins_system_gcd` | varchar(10) | O | - |  |
| 18 | `ins_menu_cd` | varchar(20) | O | - |  |
| 19 | `upd_user_id` | varchar(50) | O | - |  |
| 20 | `upd_user_ip` | varchar(50) | O | - |  |
| 21 | `upd_dt` | timestamp | O | - |  |
| 22 | `upd_system_gcd` | varchar(10) | O | - |  |
| 23 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `alert_id`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_risk_alert_severity`
- `idx_risk_alert_status`
- `idx_risk_alert_student`

---

# Badge & Simulation

## tb_simulation_scenario

**설명**: 시뮬레이션 시나리오 (What-if)

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `scenario_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `scenario_name` | varchar(200) | X | - |  |
| 4 | `scenario_type` | varchar(50) | X | - |  |
| 5 | `base_snapshot` | jsonb | X | - |  |
| 6 | `changes` | jsonb | X | - |  |
| 7 | `projected_gpa` | decimal(3,2) | O | - |  |
| 8 | `projected_competencies` | jsonb | O | - |  |
| 9 | `projected_skills` | jsonb | O | - |  |
| 10 | `projected_graduation_date` | date | O | - |  |
| 11 | `projected_role_fit` | jsonb | O | - |  |
| 12 | `risk_assessment` | jsonb | O | - |  |
| 13 | `ai_analysis` | text | O | - |  |
| 14 | `recommendation_score` | integer | O | - |  |
| 15 | `status` | varchar(20) | O | 'draft'::character varying |  |
| 16 | `created_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 17 | `analyzed_at` | timestamp | O | - |  |
| 18 | `ins_user_id` | varchar(50) | O | - |  |
| 19 | `ins_user_ip` | varchar(50) | O | - |  |
| 20 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 21 | `ins_system_gcd` | varchar(10) | O | - |  |
| 22 | `ins_menu_cd` | varchar(20) | O | - |  |
| 23 | `upd_user_id` | varchar(50) | O | - |  |
| 24 | `upd_user_ip` | varchar(50) | O | - |  |
| 25 | `upd_dt` | timestamp | O | - |  |
| 26 | `upd_system_gcd` | varchar(10) | O | - |  |
| 27 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `scenario_id`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_simulation_scenario_student`

---

## tb_student_badge

**설명**: 학생 뱃지 획득

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `student_badge_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `badge_cd` | varchar(30) | O | - |  |
| 4 | `earned_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 5 | `evidence_items` | jsonb | O | - |  |
| 6 | `verification_status` | varchar(20) | O | 'verified'::character varying |  |
| 7 | `share_url` | text | O | - |  |
| 8 | `display_order` | integer | O | 0 |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_user_ip` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 12 | `ins_system_gcd` | varchar(10) | O | - |  |
| 13 | `ins_menu_cd` | varchar(20) | O | - |  |
| 14 | `upd_user_id` | varchar(50) | O | - |  |
| 15 | `upd_user_ip` | varchar(50) | O | - |  |
| 16 | `upd_dt` | timestamp | O | - |  |
| 17 | `upd_system_gcd` | varchar(10) | O | - |  |
| 18 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `student_badge_id`
- **FK**: `badge_cd` → `tb_badge(badge_cd)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `badge_cd, student_id, student_id, badge_cd`

### 인덱스

- `idx_student_badge_student`
- `tb_student_badge_student_id_badge_cd_key`

---

# Advisor

## tb_advisor_intervention

**설명**: 어드바이저 개입

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `intervention_id` | uuid | X | gen_random_uuid() |  |
| 2 | `advisor_user_id` | uuid | O | - |  |
| 3 | `student_id` | varchar(20) | O | - |  |
| 4 | `intervention_type` | varchar(50) | X | - |  |
| 5 | `title` | varchar(200) | X | - |  |
| 6 | `description` | text | O | - |  |
| 7 | `related_entity_type` | varchar(50) | O | - |  |
| 8 | `related_entity_id` | uuid | O | - |  |
| 9 | `original_value` | jsonb | O | - |  |
| 10 | `new_value` | jsonb | O | - |  |
| 11 | `reason` | text | O | - |  |
| 12 | `student_notified` | boolean | O | false |  |
| 13 | `ins_user_id` | varchar(50) | O | - |  |
| 14 | `ins_user_ip` | varchar(50) | O | - |  |
| 15 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 16 | `ins_system_gcd` | varchar(10) | O | - |  |
| 17 | `ins_menu_cd` | varchar(20) | O | - |  |
| 18 | `upd_user_id` | varchar(50) | O | - |  |
| 19 | `upd_user_ip` | varchar(50) | O | - |  |
| 20 | `upd_dt` | timestamp | O | - |  |
| 21 | `upd_system_gcd` | varchar(10) | O | - |  |
| 22 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `intervention_id`
- **FK**: `advisor_user_id` → `tb_user(user_id)`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_advisor_intervention_student`

---

# Authentication

## tb_auth_backup_code

**설명**: TOTP 2FA 백업 코드 테이블 - 사용자당 10개 발급

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `code_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `user_id` | uuid | X | - |  |
| 3 | `code_hash` | varchar(64) | X | - |  |
| 4 | `is_used` | boolean | O | false |  |
| 5 | `used_at` | timestamp | O | - |  |
| 6 | `used_ip` | varchar(50) | O | - |  |
| 7 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `code_id`
- **FK**: `user_id` → `tb_user(user_id)`

### 인덱스

- `idx_auth_backup_user`
- `idx_backup_code_user_id`

---

## tb_auth_otp

**설명**: Email/SMS OTP 관리 테이블 - 유효시간 5분

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `otp_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `user_id` | uuid | X | - |  |
| 3 | `otp_type` | varchar(20) | X | - |  |
| 4 | `otp_code` | varchar(10) | X | - |  |
| 5 | `otp_hash` | varchar(64) | O | - |  |
| 6 | `target_email` | varchar(100) | O | - |  |
| 7 | `target_phone` | varchar(20) | O | - |  |
| 8 | `is_used` | boolean | O | false |  |
| 9 | `attempt_count` | integer | O | 0 |  |
| 10 | `max_attempts` | integer | O | 5 |  |
| 11 | `created_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 12 | `expires_at` | timestamp | X | - |  |
| 13 | `used_at` | timestamp | O | - |  |
| 14 | `request_ip` | varchar(50) | O | - |  |
| 15 | `verification_ip` | varchar(50) | O | - |  |
| 16 | `ins_user_id` | varchar(50) | O | - |  |
| 17 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `otp_id`
- **FK**: `user_id` → `tb_user(user_id)`

### 인덱스

- `idx_auth_otp_code`
- `idx_auth_otp_user`
- `idx_otp_type`
- `idx_otp_user_id`

---

## tb_auth_session

**설명**: JWT 세션 관리 테이블 - Access Token 15분, Refresh Token 7일

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `session_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `user_id` | uuid | X | - |  |
| 3 | `access_token_hash` | varchar(64) | O | - |  |
| 4 | `refresh_token_hash` | varchar(64) | O | - |  |
| 5 | `device_id` | varchar(100) | O | - |  |
| 6 | `device_type` | varchar(50) | O | - |  |
| 7 | `device_name` | varchar(100) | O | - |  |
| 8 | `user_agent` | text | O | - |  |
| 9 | `ip_address` | varchar(50) | O | - |  |
| 10 | `is_active` | boolean | O | true |  |
| 11 | `mfa_verified` | boolean | O | false |  |
| 12 | `issued_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 13 | `expires_at` | timestamp | X | - |  |
| 14 | `last_activity_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 15 | `revoked_at` | timestamp | O | - |  |
| 16 | `revoked_reason` | varchar(100) | O | - |  |
| 17 | `ins_user_id` | varchar(50) | O | - |  |
| 18 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `session_id`
- **FK**: `user_id` → `tb_user(user_id)`
- **UNIQUE**: `refresh_token_hash`

### 인덱스

- `idx_auth_session_active`
- `idx_auth_session_refresh`
- `idx_auth_session_user`
- `idx_session_active`
- `idx_session_refresh_token`
- `idx_session_user_id`
- `tb_auth_session_refresh_token_hash_key`

---

## tb_login_history

**설명**: 로그인 시도 이력 테이블 - 보안 감사용

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `history_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `user_id` | uuid | O | - |  |
| 3 | `login_id` | varchar(50) | X | - |  |
| 4 | `login_result` | varchar(20) | X | - |  |
| 5 | `ip_address` | varchar(50) | O | - |  |
| 6 | `user_agent` | text | O | - |  |
| 7 | `device_type` | varchar(50) | O | - |  |
| 8 | `device_fingerprint` | varchar(100) | O | - |  |
| 9 | `geo_country` | varchar(50) | O | - |  |
| 10 | `geo_city` | varchar(100) | O | - |  |
| 11 | `is_suspicious` | boolean | O | false |  |
| 12 | `risk_score` | integer | O | 0 | 로그인 위험도 점수 (0-100): 새기기+새위치=+30, 해외접속=+40, 야간접속=+10 |
| 13 | `attempted_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 14 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `history_id`
- **FK**: `user_id` → `tb_user(user_id)`

### 인덱스

- `idx_login_history_ip`
- `idx_login_history_login_id`
- `idx_login_history_result`
- `idx_login_history_suspicious`
- `idx_login_history_time`
- `idx_login_history_user`
- `idx_login_history_user_id`

---

## tb_user

**설명**: 사용자 인증 정보 테이블 - 학생/교수/관리자 통합 계정 관리

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `user_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `login_id` | varchar(50) | X | - |  |
| 3 | `password_hash` | varchar(255) | X | - |  |
| 4 | `password_salt` | varchar(64) | O | - |  |
| 5 | `user_type` | varchar(20) | X | - |  |
| 6 | `student_id` | varchar(20) | O | - |  |
| 7 | `professor_cd` | varchar(20) | O | - |  |
| 8 | `status` | varchar(20) | O | 'active'::character varying |  |
| 9 | `email` | varchar(100) | X | - |  |
| 10 | `email_verified` | boolean | O | false |  |
| 11 | `phone` | varchar(20) | O | - |  |
| 12 | `phone_verified` | boolean | O | false |  |
| 13 | `mfa_enabled` | boolean | O | false |  |
| 14 | `mfa_type` | varchar(20) | O | - | totp: Google Authenticator, email: 이메일 OTP, both: TOTP+Email |
| 15 | `totp_secret` | varchar(64) | O | - | TOTP 비밀키 (AES-256 암호화 후 저장 권장) |
| 16 | `totp_verified` | boolean | O | false |  |
| 17 | `password_changed_at` | timestamp | O | - |  |
| 18 | `password_expires_at` | timestamp | O | - |  |
| 19 | `failed_login_count` | integer | O | 0 |  |
| 20 | `locked_until` | timestamp | O | - |  |
| 21 | `last_login_at` | timestamp | O | - |  |
| 22 | `last_login_ip` | varchar(50) | O | - |  |
| 23 | `terms_agreed_at` | timestamp | O | - |  |
| 24 | `privacy_agreed_at` | timestamp | O | - |  |
| 25 | `marketing_agreed` | boolean | O | false |  |
| 26 | `ins_user_id` | varchar(50) | O | - |  |
| 27 | `ins_user_ip` | varchar(50) | O | - |  |
| 28 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 29 | `ins_system_gcd` | varchar(10) | O | - |  |
| 30 | `ins_menu_cd` | varchar(20) | O | - |  |
| 31 | `upd_user_id` | varchar(50) | O | - |  |
| 32 | `upd_user_ip` | varchar(50) | O | - |  |
| 33 | `upd_dt` | timestamp | O | - |  |
| 34 | `upd_system_gcd` | varchar(10) | O | - |  |
| 35 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `user_id`
- **FK**: `professor_cd` → `tb_professor(professor_cd)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `login_id`

### 인덱스

- `idx_user_email`
- `idx_user_login_id`
- `idx_user_professor`
- `idx_user_status`
- `idx_user_student`
- `idx_user_student_id`
- `idx_user_type`
- `tb_user_login_id_key`

---

## tb_user_device

**설명**: 사용자 기기 관리 테이블 - 신뢰 기기는 2FA 스킵 가능

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `device_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `user_id` | uuid | X | - |  |
| 3 | `device_fingerprint` | varchar(100) | X | - |  |
| 4 | `device_name` | varchar(100) | O | - |  |
| 5 | `device_type` | varchar(50) | O | - |  |
| 6 | `browser` | varchar(50) | O | - |  |
| 7 | `os` | varchar(50) | O | - |  |
| 8 | `is_trusted` | boolean | O | false |  |
| 9 | `trust_level` | integer | O | 0 | 신뢰 레벨: 0=새기기, 1=확인됨, 2=자주사용, 3=신뢰됨(2FA스킵가능) |
| 10 | `first_seen_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 11 | `last_seen_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 12 | `trusted_at` | timestamp | O | - |  |
| 13 | `last_ip` | varchar(50) | O | - |  |
| 14 | `last_location` | varchar(100) | O | - |  |
| 15 | `ins_user_id` | varchar(50) | O | - |  |
| 16 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 17 | `upd_user_id` | varchar(50) | O | - |  |
| 18 | `upd_dt` | timestamp | O | - |  |

### 제약조건

- **PK**: `device_id`
- **FK**: `user_id` → `tb_user(user_id)`
- **UNIQUE**: `device_fingerprint`

### 인덱스

- `idx_device_fingerprint`
- `idx_device_user_id`
- `idx_user_device_fp`
- `idx_user_device_user`
- `tb_user_device_device_fingerprint_key`

---

# AI Ops

## tb_eval_case

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `case_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `case_nm` | varchar(200) | X | - |  |
| 3 | `case_type` | varchar(50) | X | - |  |
| 4 | `input_data` | jsonb | X | - |  |
| 5 | `expected_schema` | jsonb | X | - |  |
| 6 | `quality_criteria` | jsonb | X | - |  |
| 7 | `is_active` | boolean | O | true |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `case_id`

---

## tb_eval_result

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `result_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `case_id` | uuid | O | - |  |
| 3 | `run_id` | uuid | O | - |  |
| 4 | `model_version` | varchar(50) | X | - |  |
| 5 | `passed` | boolean | X | - |  |
| 6 | `schema_valid` | boolean | X | - |  |
| 7 | `evidence_grounded` | boolean | X | - |  |
| 8 | `constraint_compliant` | boolean | X | - |  |
| 9 | `scores` | jsonb | X | - |  |
| 10 | `failure_reasons` | jsonb | O | - |  |
| 11 | `ins_user_id` | varchar(50) | O | - |  |
| 12 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `result_id`
- **FK**: `case_id` → `tb_eval_case(case_id)`
- **FK**: `run_id` → `tb_recommendation_run(run_id)`

---

## tb_feedback_event

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `feedback_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `run_id` | uuid | O | - |  |
| 3 | `user_id` | varchar(50) | X | - |  |
| 4 | `feedback_type` | varchar(20) | X | - |  |
| 5 | `item_id` | uuid | O | - |  |
| 6 | `details` | text | O | - |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `feedback_id`
- **FK**: `run_id` → `tb_recommendation_run(run_id)`

---

## tb_model_version

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `model_version_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `version` | varchar(50) | X | - |  |
| 3 | `base_model` | varchar(100) | X | - |  |
| 4 | `fine_tuned_id` | varchar(200) | O | - |  |
| 5 | `training_data_version` | varchar(50) | O | - |  |
| 6 | `metrics` | jsonb | O | - |  |
| 7 | `is_active` | boolean | O | false |  |
| 8 | `deployed_at` | timestamp | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `model_version_id`
- **UNIQUE**: `version`

### 인덱스

- `tb_model_version_version_key`

---

## tb_policy_version

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `policy_version_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `version` | varchar(50) | X | - |  |
| 3 | `policy_type` | varchar(50) | X | - |  |
| 4 | `rules` | jsonb | X | - |  |
| 5 | `description` | text | O | - |  |
| 6 | `is_active` | boolean | O | false |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `policy_version_id`
- **UNIQUE**: `version, version, policy_type, policy_type`

### 인덱스

- `tb_policy_version_version_policy_type_key`

---

## tb_prompt_version

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `prompt_version_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `version` | varchar(50) | X | - |  |
| 3 | `prompt_type` | varchar(50) | X | - |  |
| 4 | `content` | text | X | - |  |
| 5 | `description` | text | O | - |  |
| 6 | `is_active` | boolean | O | false |  |
| 7 | `ins_user_id` | varchar(50) | O | - |  |
| 8 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `prompt_version_id`
- **UNIQUE**: `version, version, prompt_type, prompt_type`

### 인덱스

- `tb_prompt_version_version_prompt_type_key`

---

## tb_recommendation_evidence

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `evidence_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `item_id` | uuid | O | - |  |
| 3 | `source_type` | varchar(50) | X | - |  |
| 4 | `source_id` | varchar(100) | X | - |  |
| 5 | `source_version` | varchar(50) | O | - |  |
| 6 | `snippet_text` | text | X | - |  |
| 7 | `snippet_hash` | varchar(64) | X | - |  |
| 8 | `retrieval_score` | decimal(5,4) | O | - |  |
| 9 | `retrieval_method` | varchar(20) | O | - |  |
| 10 | `ins_user_id` | varchar(50) | O | - |  |
| 11 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `evidence_id`
- **FK**: `item_id` → `tb_recommendation_item(item_id)`

---

## tb_recommendation_item

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `item_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `run_id` | uuid | O | - |  |
| 3 | `action_type` | varchar(50) | X | - |  |
| 4 | `title` | varchar(200) | X | - |  |
| 5 | `description` | text | O | - |  |
| 6 | `rationale` | text[] | O | - |  |
| 7 | `impact_score` | decimal(5,2) | O | - |  |
| 8 | `effort_hours` | decimal(5,2) | O | - |  |
| 9 | `priority` | integer | O | - |  |
| 10 | `semester` | varchar(10) | O | - |  |
| 11 | `dependencies` | text[] | O | - |  |
| 12 | `ins_user_id` | varchar(50) | O | - |  |
| 13 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `item_id`
- **FK**: `run_id` → `tb_recommendation_run(run_id)`

---

## tb_recommendation_run

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `run_id` | uuid | X | uuid_generate_v4() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `target_role_cd` | varchar(20) | O | - |  |
| 4 | `model_version` | varchar(50) | X | - |  |
| 5 | `prompt_version` | varchar(50) | X | - |  |
| 6 | `policy_version` | varchar(50) | X | - |  |
| 7 | `input_snapshot` | jsonb | X | - |  |
| 8 | `retrieval_results` | jsonb | O | - |  |
| 9 | `output_json` | jsonb | X | - |  |
| 10 | `schema_valid` | boolean | X | true |  |
| 11 | `constraints_passed` | boolean | X | true |  |
| 12 | `evidence_count` | integer | X | 0 |  |
| 13 | `latency_ms` | integer | O | - |  |
| 14 | `total_tokens` | integer | O | - |  |
| 15 | `cost_usd` | decimal(10,6) | O | - |  |
| 16 | `ins_user_id` | varchar(50) | O | - |  |
| 17 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `run_id`
- **FK**: `student_id` → `tb_student(student_id)`
- **FK**: `target_role_cd` → `tb_role(role_cd)`

### 인덱스

- `idx_recommendation_run_student`

---

# Other

## tb_advisor_assignment

**설명**: 어드바이저 할당

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `assignment_id` | uuid | X | gen_random_uuid() |  |
| 2 | `advisor_user_id` | uuid | O | - |  |
| 3 | `student_id` | varchar(20) | O | - |  |
| 4 | `assignment_type` | varchar(30) | O | 'primary'::character varying |  |
| 5 | `assigned_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 6 | `expires_at` | timestamp | O | - |  |
| 7 | `status` | varchar(20) | O | 'active'::character varying |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `assignment_id`
- **FK**: `advisor_user_id` → `tb_user(user_id)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `advisor_user_id, student_id, student_id, student_id, assignment_type, assignment_type, assignment_type, advisor_user_id, advisor_user_id`

### 인덱스

- `idx_advisor_assignment_advisor`
- `idx_advisor_assignment_student`
- `tb_advisor_assignment_advisor_user_id_student_id_assignment_key`

---

## tb_advisor_note

**설명**: 어드바이저 메모

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `note_id` | uuid | X | gen_random_uuid() |  |
| 2 | `advisor_user_id` | uuid | O | - |  |
| 3 | `student_id` | varchar(20) | O | - |  |
| 4 | `note_type` | varchar(30) | O | 'general'::character varying |  |
| 5 | `title` | varchar(200) | O | - |  |
| 6 | `content` | text | X | - |  |
| 7 | `is_private` | boolean | O | true |  |
| 8 | `meeting_date` | date | O | - |  |
| 9 | `follow_up_required` | boolean | O | false |  |
| 10 | `follow_up_date` | date | O | - |  |
| 11 | `ins_user_id` | varchar(50) | O | - |  |
| 12 | `ins_user_ip` | varchar(50) | O | - |  |
| 13 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 14 | `ins_system_gcd` | varchar(10) | O | - |  |
| 15 | `ins_menu_cd` | varchar(20) | O | - |  |
| 16 | `upd_user_id` | varchar(50) | O | - |  |
| 17 | `upd_user_ip` | varchar(50) | O | - |  |
| 18 | `upd_dt` | timestamp | O | - |  |
| 19 | `upd_system_gcd` | varchar(10) | O | - |  |
| 20 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `note_id`
- **FK**: `advisor_user_id` → `tb_user(user_id)`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_advisor_note_student`

---

## tb_badge

**설명**: 뱃지 정의

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `badge_cd` | varchar(30) | X | - |  |
| 2 | `badge_nm` | varchar(100) | X | - |  |
| 3 | `badge_nm_en` | varchar(100) | O | - |  |
| 4 | `description` | text | O | - |  |
| 5 | `category` | varchar(50) | O | - |  |
| 6 | `icon_url` | text | O | - |  |
| 7 | `criteria` | jsonb | X | - |  |
| 8 | `points` | integer | O | 0 |  |
| 9 | `rarity` | varchar(20) | O | 'common'::character varying |  |
| 10 | `use_fg` | char(1) | O | 'Y'::bpchar |  |
| 11 | `ins_user_id` | varchar(50) | O | - |  |
| 12 | `ins_user_ip` | varchar(50) | O | - |  |
| 13 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 14 | `ins_system_gcd` | varchar(10) | O | - |  |
| 15 | `ins_menu_cd` | varchar(20) | O | - |  |
| 16 | `upd_user_id` | varchar(50) | O | - |  |
| 17 | `upd_user_ip` | varchar(50) | O | - |  |
| 18 | `upd_dt` | timestamp | O | - |  |
| 19 | `upd_system_gcd` | varchar(10) | O | - |  |
| 20 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `badge_cd`

---

## tb_coaching_checkin

**설명**: 주간 체크인

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `checkin_id` | uuid | X | gen_random_uuid() |  |
| 2 | `plan_id` | uuid | O | - |  |
| 3 | `week_number` | integer | X | - |  |
| 4 | `checkin_date` | date | X | - |  |
| 5 | `completed_tasks` | jsonb | O | - |  |
| 6 | `hours_spent` | decimal(4,1) | O | - |  |
| 7 | `blockers` | text | O | - |  |
| 8 | `wins` | text | O | - |  |
| 9 | `mood_score` | integer | O | - |  |
| 10 | `ai_feedback` | text | O | - |  |
| 11 | `ai_suggestions` | jsonb | O | - |  |
| 12 | `progress_score` | decimal(5,2) | O | - |  |
| 13 | `on_track` | boolean | O | - |  |
| 14 | `ins_user_id` | varchar(50) | O | - |  |
| 15 | `ins_user_ip` | varchar(50) | O | - |  |
| 16 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 17 | `ins_system_gcd` | varchar(10) | O | - |  |
| 18 | `ins_menu_cd` | varchar(20) | O | - |  |
| 19 | `upd_user_id` | varchar(50) | O | - |  |
| 20 | `upd_user_ip` | varchar(50) | O | - |  |
| 21 | `upd_dt` | timestamp | O | - |  |
| 22 | `upd_system_gcd` | varchar(10) | O | - |  |
| 23 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `checkin_id`
- **FK**: `plan_id` → `tb_coaching_plan(plan_id)`

### 인덱스

- `idx_coaching_checkin_plan`

---

## tb_coaching_plan

**설명**: 코칭 계획

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `plan_id` | uuid | X | gen_random_uuid() |  |
| 2 | `goal_id` | uuid | O | - |  |
| 3 | `plan_version` | integer | O | 1 |  |
| 4 | `milestones` | jsonb | X | - |  |
| 5 | `weekly_hours_target` | decimal(4,1) | O | 10 |  |
| 6 | `current_week` | integer | O | 1 |  |
| 7 | `total_weeks` | integer | O | - |  |
| 8 | `ai_generated` | boolean | O | true |  |
| 9 | `status` | varchar(20) | O | 'active'::character varying |  |
| 10 | `created_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 11 | `ins_user_id` | varchar(50) | O | - |  |
| 12 | `ins_user_ip` | varchar(50) | O | - |  |
| 13 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 14 | `ins_system_gcd` | varchar(10) | O | - |  |
| 15 | `ins_menu_cd` | varchar(20) | O | - |  |
| 16 | `upd_user_id` | varchar(50) | O | - |  |
| 17 | `upd_user_ip` | varchar(50) | O | - |  |
| 18 | `upd_dt` | timestamp | O | - |  |
| 19 | `upd_system_gcd` | varchar(10) | O | - |  |
| 20 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `plan_id`
- **FK**: `goal_id` → `tb_coaching_goal(goal_id)`

### 인덱스

- `idx_coaching_plan_goal`

---

## tb_coaching_retrospective

**설명**: 회고

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `retrospective_id` | uuid | X | gen_random_uuid() |  |
| 2 | `goal_id` | uuid | O | - |  |
| 3 | `period_start` | date | X | - |  |
| 4 | `period_end` | date | X | - |  |
| 5 | `what_went_well` | text | O | - |  |
| 6 | `what_could_improve` | text | O | - |  |
| 7 | `lessons_learned` | text | O | - |  |
| 8 | `initial_metrics` | jsonb | O | - |  |
| 9 | `final_metrics` | jsonb | O | - |  |
| 10 | `improvement_percentage` | decimal(5,2) | O | - |  |
| 11 | `ai_summary` | text | O | - |  |
| 12 | `ai_insights` | jsonb | O | - |  |
| 13 | `next_period_recommendations` | jsonb | O | - |  |
| 14 | `ins_user_id` | varchar(50) | O | - |  |
| 15 | `ins_user_ip` | varchar(50) | O | - |  |
| 16 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 17 | `ins_system_gcd` | varchar(10) | O | - |  |
| 18 | `ins_menu_cd` | varchar(20) | O | - |  |
| 19 | `upd_user_id` | varchar(50) | O | - |  |
| 20 | `upd_user_ip` | varchar(50) | O | - |  |
| 21 | `upd_dt` | timestamp | O | - |  |
| 22 | `upd_system_gcd` | varchar(10) | O | - |  |
| 23 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `retrospective_id`
- **FK**: `goal_id` → `tb_coaching_goal(goal_id)`

### 인덱스

- `idx_coaching_retrospective_goal`

---

## tb_cohort_snapshot

**설명**: 코호트 대시보드 스냅샷

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `snapshot_id` | uuid | X | gen_random_uuid() |  |
| 2 | `department_cd` | varchar(20) | O | - |  |
| 3 | `grade_level` | integer | O | - |  |
| 4 | `term_cd` | varchar(10) | O | - |  |
| 5 | `snapshot_date` | date | X | - |  |
| 6 | `total_students` | integer | X | - |  |
| 7 | `avg_gpa` | decimal(3,2) | O | - |  |
| 8 | `avg_competency_scores` | jsonb | O | - |  |
| 9 | `avg_skill_levels` | jsonb | O | - |  |
| 10 | `risk_distribution` | jsonb | O | - |  |
| 11 | `at_risk_students` | varchar[] | O | - |  |
| 12 | `goal_achievement_rate` | decimal(5,2) | O | - |  |
| 13 | `opportunity_application_rate` | decimal(5,2) | O | - |  |
| 14 | `badge_earning_rate` | decimal(5,2) | O | - |  |
| 15 | `vs_prev_term` | jsonb | O | - |  |
| 16 | `ins_user_id` | varchar(50) | O | - |  |
| 17 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `snapshot_id`
- **FK**: `department_cd` → `tb_department(department_cd)`
- **FK**: `term_cd` → `tb_term(term_cd)`

### 인덱스

- `idx_cohort_snapshot_dept`

---

## tb_constraint_check

**설명**: 제약 조건 검사 이력

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `check_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `check_type` | varchar(50) | X | - |  |
| 4 | `check_date` | timestamp | O | CURRENT_TIMESTAMP |  |
| 5 | `target_term_cd` | varchar(10) | O | - |  |
| 6 | `input_data` | jsonb | O | - |  |
| 7 | `result_passed` | boolean | X | - |  |
| 8 | `violations` | jsonb | O | - |  |
| 9 | `ins_user_id` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `check_id`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_constraint_check_student`

---

## tb_opportunity_recommendation

**설명**: 기회 추천

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `recommendation_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `opportunity_id` | uuid | O | - |  |
| 4 | `match_score` | decimal(5,2) | X | - |  |
| 5 | `match_reasons` | jsonb | O | - |  |
| 6 | `status` | varchar(20) | O | 'recommended'::character varying |  |
| 7 | `recommended_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `recommendation_id`
- **FK**: `opportunity_id` → `tb_opportunity(opportunity_id)`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `opportunity_id, student_id, student_id, opportunity_id`

### 인덱스

- `idx_opportunity_recommendation_student`
- `tb_opportunity_recommendation_student_id_opportunity_id_key`

---

## tb_prerequisite_rule

**설명**: 선수과목 규칙

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `rule_id` | uuid | X | gen_random_uuid() |  |
| 2 | `course_cd` | varchar(20) | O | - |  |
| 3 | `prerequisite_course_cd` | varchar(20) | O | - |  |
| 4 | `rule_type` | varchar(20) | O | 'required'::character varying |  |
| 5 | `min_grade` | varchar(5) | O | - |  |
| 6 | `ins_user_id` | varchar(50) | O | - |  |
| 7 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `rule_id`
- **FK**: `course_cd` → `tb_course(course_cd)`
- **FK**: `prerequisite_course_cd` → `tb_course(course_cd)`
- **UNIQUE**: `prerequisite_course_cd, prerequisite_course_cd, course_cd, course_cd`

### 인덱스

- `tb_prerequisite_rule_course_cd_prerequisite_course_cd_key`

---

## tb_role_skill_map

**설명**: 직무-스킬 매핑 (Skill Graph)

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `map_id` | uuid | X | gen_random_uuid() |  |
| 2 | `role_cd` | varchar(20) | O | - |  |
| 3 | `skill_cd` | varchar(20) | O | - |  |
| 4 | `required_level` | integer | X | - |  |
| 5 | `importance` | varchar(15) | X | - |  |
| 6 | `market_demand_score` | decimal(5,2) | O | - |  |
| 7 | `growth_trend` | varchar(20) | O | 'stable'::character varying |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_user_ip` | varchar(50) | O | - |  |
| 10 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 11 | `ins_system_gcd` | varchar(10) | O | - |  |
| 12 | `ins_menu_cd` | varchar(20) | O | - |  |
| 13 | `upd_user_id` | varchar(50) | O | - |  |
| 14 | `upd_user_ip` | varchar(50) | O | - |  |
| 15 | `upd_dt` | timestamp | O | - |  |
| 16 | `upd_system_gcd` | varchar(10) | O | - |  |
| 17 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `map_id`
- **FK**: `role_cd` → `tb_role(role_cd)`
- **FK**: `skill_cd` → `tb_skill(skill_cd)`
- **UNIQUE**: `skill_cd, role_cd, role_cd, skill_cd`

### 인덱스

- `idx_role_skill_map_role`
- `idx_role_skill_map_skill`
- `tb_role_skill_map_role_cd_skill_cd_key`

---

## tb_scenario_comparison

**설명**: 시나리오 비교

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `comparison_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `scenario_ids` | uuid[] | X | - |  |
| 4 | `comparison_metrics` | jsonb | X | - |  |
| 5 | `winner_scenario_id` | uuid | O | - |  |
| 6 | `comparison_summary` | text | O | - |  |
| 7 | `created_at` | timestamp | O | CURRENT_TIMESTAMP |  |
| 8 | `ins_user_id` | varchar(50) | O | - |  |
| 9 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `comparison_id`
- **FK**: `student_id` → `tb_student(student_id)`

### 인덱스

- `idx_scenario_comparison_student`

---

## tb_skill_passport

**설명**: 스킬 패스포트 (종합 프로필)

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `passport_id` | uuid | X | gen_random_uuid() |  |
| 2 | `student_id` | varchar(20) | O | - |  |
| 3 | `public_url_slug` | varchar(100) | O | - |  |
| 4 | `is_public` | boolean | O | false |  |
| 5 | `headline` | varchar(200) | O | - |  |
| 6 | `bio` | text | O | - |  |
| 7 | `featured_badges` | varchar[] | O | - |  |
| 8 | `featured_skills` | varchar[] | O | - |  |
| 9 | `featured_projects` | uuid[] | O | - |  |
| 10 | `social_links` | jsonb | O | - |  |
| 11 | `view_count` | integer | O | 0 |  |
| 12 | `last_updated` | timestamp | O | CURRENT_TIMESTAMP |  |
| 13 | `ins_user_id` | varchar(50) | O | - |  |
| 14 | `ins_user_ip` | varchar(50) | O | - |  |
| 15 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |
| 16 | `ins_system_gcd` | varchar(10) | O | - |  |
| 17 | `ins_menu_cd` | varchar(20) | O | - |  |
| 18 | `upd_user_id` | varchar(50) | O | - |  |
| 19 | `upd_user_ip` | varchar(50) | O | - |  |
| 20 | `upd_dt` | timestamp | O | - |  |
| 21 | `upd_system_gcd` | varchar(10) | O | - |  |
| 22 | `upd_menu_cd` | varchar(20) | O | - |  |

### 제약조건

- **PK**: `passport_id`
- **FK**: `student_id` → `tb_student(student_id)`
- **UNIQUE**: `public_url_slug`
- **UNIQUE**: `student_id`

### 인덱스

- `idx_skill_passport_slug`
- `tb_skill_passport_public_url_slug_key`
- `tb_skill_passport_student_id_key`

---

## tb_skill_relation

**설명**: 스킬 연관관계 (Graph edges)

### 컬럼 정의

| # | 컬럼명 | 데이터 타입 | NULL | 기본값 | 설명 |
|--:|--------|-------------|:----:|--------|------|
| 1 | `relation_id` | uuid | X | gen_random_uuid() |  |
| 2 | `skill_cd_from` | varchar(20) | O | - |  |
| 3 | `skill_cd_to` | varchar(20) | O | - |  |
| 4 | `relation_type` | varchar(30) | X | - |  |
| 5 | `strength` | decimal(3,2) | O | 1.0 |  |
| 6 | `ins_user_id` | varchar(50) | O | - |  |
| 7 | `ins_dt` | timestamp | O | CURRENT_TIMESTAMP |  |

### 제약조건

- **PK**: `relation_id`
- **FK**: `skill_cd_from` → `tb_skill(skill_cd)`
- **FK**: `skill_cd_to` → `tb_skill(skill_cd)`
- **UNIQUE**: `skill_cd_from, skill_cd_from, skill_cd_to, skill_cd_to, skill_cd_to, relation_type, relation_type, relation_type, skill_cd_from`

### 인덱스

- `idx_skill_relation_from`
- `tb_skill_relation_skill_cd_from_skill_cd_to_relation_type_key`

---
