#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career Data Migration Configuration

FK 종속성 순서에 따른 테이블 생성 설정 및 목표 데이터 건수 정의
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os

# ============================================
# Database Configuration
# ============================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '2012')
}
SCHEMA = 'idino_career'

# ============================================
# FK Dependency Levels (7-Level Hierarchy)
# ============================================

# Level 1: Independent tables (No FK dependencies)
LEVEL_1_TABLES = [
    'tb_university',
    'tb_competency',
    'tb_skill',
    'tb_term',
    'tb_badge',
    'tb_role',
    'tb_program',
]

# Level 2: References Level 1 only
LEVEL_2_TABLES = [
    'tb_college',           # → university
    'tb_role_skill_map',    # → role, skill
    'tb_skill_competency_map',  # → skill, competency
    'tb_skill_relation',    # → skill (self-referencing)
]

# Level 3: References Level 2 or Level 1
LEVEL_3_TABLES = [
    'tb_department',        # → college
    'tb_course',            # → department (optional)
]

# Level 4: References Level 3 or lower
LEVEL_4_TABLES = [
    'tb_professor',         # → department
    'tb_advisor',           # → department
    'tb_student',           # → university, department
    'tb_prerequisite',      # → course (self-ref)
    'tb_prerequisite_rule', # → course
    'tb_course_competency_map',  # → course, competency
    'tb_alumni_cohort',     # → department
    'tb_success_pattern',   # → department, role
]

# Level 5: References Level 4 or lower
LEVEL_5_TABLES = [
    'tb_user',              # → student (optional)
    'tb_course_offering',   # → course, term, professor
    'tb_professor_course',  # → professor, course
    'tb_advisor_assignment', # → advisor, student
    'tb_opportunity',       # standalone (no strict FK in schema)
]

# Level 6: References Level 5 or lower
LEVEL_6_TABLES = [
    'tb_enrollment',        # → student, course_offering
    'tb_student_skill',     # → student, skill
    'tb_student_competency', # → student, competency
    'tb_student_badge',     # → student, badge
    'tb_skill_passport',    # → student
    'tb_coaching_goal',     # → student, role
    'tb_activity',          # → student, program
    'tb_achievement',       # → student
    'tb_risk_alert',        # → student
    'tb_simulation_scenario', # → student
    'tb_recommendation_run', # → student
    'tb_opportunity_recommendation', # → student, opportunity
    'tb_opportunity_application',    # → student, opportunity
    'tb_user_session',      # → user
    'tb_cohort_snapshot',   # → department
    'tb_advisor_intervention', # → advisor_assignment
    'tb_advisor_note',      # → advisor_assignment
]

# Level 7: References Level 6 or lower (deepest dependencies)
LEVEL_7_TABLES = [
    'tb_grade',             # → enrollment
    'tb_grade_summary',     # → student, term
    'tb_cumulative_summary', # → student
    'tb_coaching_plan',     # → coaching_goal
    'tb_coaching_checkin',  # → coaching_plan
    'tb_coaching_retrospective', # → coaching_goal
    'tb_recommendation_item', # → recommendation_run
    'tb_eval_feedback',     # → recommendation_run, user
    'tb_scenario_comparison', # → student, simulation_scenario (array)
    'tb_skill_gap_analysis', # → student, role
]

# All levels in order
TABLE_LEVELS = [
    ('Level 1', LEVEL_1_TABLES),
    ('Level 2', LEVEL_2_TABLES),
    ('Level 3', LEVEL_3_TABLES),
    ('Level 4', LEVEL_4_TABLES),
    ('Level 5', LEVEL_5_TABLES),
    ('Level 6', LEVEL_6_TABLES),
    ('Level 7', LEVEL_7_TABLES),
]

# ============================================
# Target Row Counts (Excel 기반)
# ============================================
TARGET_ROW_COUNTS = {
    # Level 1 - Master data
    'tb_university': 1,
    'tb_competency': 6,
    'tb_skill': 15,
    'tb_term': 12,      # 2020-1 ~ 2025-2
    'tb_badge': 10,
    'tb_role': 15,
    'tb_program': 30,

    # Level 2
    'tb_college': 8,
    'tb_role_skill_map': 60,   # ~4 skills per role
    'tb_skill_competency_map': 45,  # ~3 competencies per skill
    'tb_skill_relation': 30,

    # Level 3
    'tb_department': 30,
    'tb_course': 100,

    # Level 4
    'tb_professor': 50,
    'tb_advisor': 20,
    'tb_student': 204,
    'tb_prerequisite': 50,
    'tb_prerequisite_rule': 30,
    'tb_course_competency_map': 300,
    'tb_alumni_cohort': 150,   # dept × years
    'tb_success_pattern': 45,

    # Level 5
    'tb_user': 225,            # 204 students + 20 advisors + 1 admin
    'tb_course_offering': 600, # 100 courses × 6 terms avg
    'tb_professor_course': 150,
    'tb_advisor_assignment': 200,
    'tb_opportunity': 50,

    # Level 6
    'tb_enrollment': 4000,     # ~20 enrollments per student
    'tb_student_skill': 1500,  # ~7 skills per student
    'tb_student_competency': 1224,  # 204 students × 6 competencies
    'tb_student_badge': 700,
    'tb_skill_passport': 204,
    'tb_coaching_goal': 300,
    'tb_activity': 400,
    'tb_achievement': 300,
    'tb_risk_alert': 100,
    'tb_simulation_scenario': 200,
    'tb_recommendation_run': 200,
    'tb_opportunity_recommendation': 400,
    'tb_opportunity_application': 300,
    'tb_user_session': 500,
    'tb_cohort_snapshot': 500,
    'tb_advisor_intervention': 100,
    'tb_advisor_note': 300,

    # Level 7
    'tb_grade': 4000,          # 1:1 with enrollment (completed only)
    'tb_grade_summary': 1500,  # student × completed terms
    'tb_cumulative_summary': 204,
    'tb_coaching_plan': 300,   # 1:1 with goals
    'tb_coaching_checkin': 600,
    'tb_coaching_retrospective': 150,
    'tb_recommendation_item': 500,
    'tb_eval_feedback': 500,
    'tb_scenario_comparison': 150,
    'tb_skill_gap_analysis': 1000,
}

# ============================================
# Sample Data Patterns (Excel 기반)
# ============================================

# 성적 분포 (현실적)
GRADE_DISTRIBUTION = [
    ('A+', 4.5, 0.08),
    ('A0', 4.0, 0.15),
    ('B+', 3.5, 0.22),
    ('B0', 3.0, 0.25),
    ('C+', 2.5, 0.15),
    ('C0', 2.0, 0.10),
    ('D+', 1.5, 0.03),
    ('D0', 1.0, 0.02),
]

# 학생 ID 패턴: 입학년도 + 학과코드 + 순번
# 예: 2020010001 (2020년 입학, 01번 학과, 0001번 학생)

# 한국어 성 목록
KOREAN_SURNAMES = [
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
    '한', '오', '서', '신', '권', '황', '안', '송', '류', '전',
    '홍', '고', '문', '양', '손', '배', '백', '허', '유', '남'
]

# 한국어 이름 (성별 구분 없이 현대적 이름)
KOREAN_GIVEN_NAMES = [
    '민준', '서연', '도윤', '서현', '예준', '지우', '시우', '하은',
    '주원', '지민', '지호', '채원', '윤서', '서준', '수아', '하준',
    '유준', '지아', '건우', '은서', '민서', '수호', '예린', '민재',
    '현우', '소율', '지환', '다은', '유진', '준우', '시현', '하린',
    '우진', '소민', '연우', '윤아', '준서', '지연', '은우', '다인',
    '승우', '지원', '현준', '나윤', '동현', '가은', '재민', '수빈'
]

# 학과별 과목 접두어
COURSE_PREFIXES = {
    'DEPT001': 'CS',   # 컴퓨터공학
    'DEPT002': 'SW',   # 소프트웨어
    'DEPT003': 'EE',   # 전자공학
    'DEPT004': 'ME',   # 기계공학
    'DEPT005': 'CH',   # 화학공학
    'DEPT006': 'IE',   # 산업공학
    'DEPT014': 'BA',   # 경영학
    'DEPT009': 'MA',   # 수학
    'DEPT013': 'ST',   # 통계학
}

# 활동 유형
ACTIVITY_TYPES = ['project', 'research', 'contest', 'club', 'volunteer', 'seminar']

# 성과 유형
ACHIEVEMENT_TYPES = ['certificate', 'patent', 'award', 'publication', 'competition']

# 역량 코드 (6개)
COMPETENCY_CODES = ['COMP01', 'COMP02', 'COMP03', 'COMP04', 'COMP05', 'COMP06']

# 스킬 카테고리
SKILL_CATEGORIES = ['technical', 'soft', 'domain']

# 위험 알림 유형
RISK_TYPES = ['gpa_low', 'deadline_risk', 'engagement_low', 'skill_gap', 'graduation_risk']

# 코칭 목표 유형
GOAL_TYPES = ['academic', 'career', 'skill', 'personal']

# 시뮬레이션 시나리오 유형
SCENARIO_TYPES = ['career', 'skill', 'course', 'opportunity']

# 기회 유형
OPPORTUNITY_TYPES = ['internship', 'project', 'lab', 'scholarship', 'competition']

# 상담 배정 유형
ASSIGNMENT_TYPES = ['academic', 'career', 'mentoring', 'emergency']

# 상담 메모 유형
NOTE_TYPES = ['observation', 'progress', 'action_item', 'follow_up']

# 뱃지 카테고리
BADGE_CATEGORIES = ['skill', 'achievement', 'activity', 'academic', 'special']

# 뱃지 레벨
BADGE_LEVELS = ['bronze', 'silver', 'gold', 'platinum']

# ============================================
# Utility Functions
# ============================================

def get_all_tables_in_order() -> List[str]:
    """FK 의존성 순서대로 모든 테이블 반환"""
    all_tables = []
    for _, tables in TABLE_LEVELS:
        all_tables.extend(tables)
    return all_tables


def get_truncate_order() -> List[str]:
    """TRUNCATE 순서 (역순)"""
    return list(reversed(get_all_tables_in_order()))


def get_table_level(table_name: str) -> int:
    """테이블의 레벨 반환 (1-7)"""
    for i, (_, tables) in enumerate(TABLE_LEVELS, 1):
        if table_name in tables:
            return i
    return 0


def print_migration_summary():
    """마이그레이션 요약 출력"""
    total_rows = sum(TARGET_ROW_COUNTS.values())
    print("=" * 60)
    print("IDINO Career Data Migration Summary")
    print("=" * 60)

    for level_name, tables in TABLE_LEVELS:
        level_rows = sum(TARGET_ROW_COUNTS.get(t, 0) for t in tables)
        print(f"\n{level_name}: {len(tables)} tables, {level_rows:,} rows")
        for table in tables:
            count = TARGET_ROW_COUNTS.get(table, 0)
            print(f"  - {table}: {count:,}")

    print(f"\n{'=' * 60}")
    print(f"Total: {len(get_all_tables_in_order())} tables, {total_rows:,} rows")
    print("=" * 60)


if __name__ == '__main__':
    print_migration_summary()
