#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career Full Data Validator

53개 테이블 전수 검증 및 Excel 스펙 일치 확인
"""

import sys
import os

# Windows 콘솔 UTF-8 출력 지원
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import psycopg2
import re
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional, Set
from enum import Enum

from migration_config import (
    DB_CONFIG, SCHEMA, TABLE_LEVELS, TARGET_ROW_COUNTS,
    get_all_tables_in_order
)


class IssueType(Enum):
    """이슈 유형"""
    FK_VIOLATION = "FK Violation"
    UNIQUE_VIOLATION = "Unique Violation"
    NULL_VIOLATION = "NOT NULL Violation"
    RANGE_VIOLATION = "Range Violation"
    ENUM_VIOLATION = "ENUM Violation"
    PATTERN_VIOLATION = "Pattern Violation"
    DATA_SWAP = "Data Swap Needed"
    ROW_COUNT_MISMATCH = "Row Count Mismatch"


class IssueSeverity(Enum):
    """이슈 심각도"""
    CRITICAL = "CRITICAL"  # 데이터 무결성 위반
    HIGH = "HIGH"          # Excel 스펙 불일치
    MEDIUM = "MEDIUM"      # 권장 사항 불일치
    LOW = "LOW"            # 참고 사항


@dataclass
class ValidationIssue:
    """검증 이슈"""
    table_name: str
    column_name: str
    issue_type: IssueType
    severity: IssueSeverity
    message: str
    affected_rows: int = 0
    sample_values: List[Any] = field(default_factory=list)
    fix_sql: Optional[str] = None


@dataclass
class TableValidationResult:
    """테이블별 검증 결과"""
    table_name: str
    row_count: int
    issues: List[ValidationIssue] = field(default_factory=list)
    passed: bool = True

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]:
            self.passed = False


# ============================================
# Excel 스펙 기반 검증 규칙 정의
# ============================================

# 허용된 상태 값 (ENUM)
ALLOWED_STATUS_VALUES = {
    'tb_student': {'status': ['enrolled', 'graduated', 'leave_of_absence', 'expelled', 'withdrawn']},
    'tb_coaching_goal': {'status': ['draft', 'active', 'paused', 'completed', 'abandoned', 'achieved']},
    'tb_coaching_plan': {'status': ['draft', 'active', 'completed', 'cancelled']},
    'tb_enrollment': {'status': ['enrolled', 'completed', 'withdrawn', 'failed']},
    'tb_opportunity': {'status': ['draft', 'open', 'closed', 'cancelled']},
    'tb_advisor_assignment': {'status': ['active', 'paused', 'completed', 'terminated']},
    'tb_risk_alert': {'status': ['active', 'resolved', 'dismissed', 'escalated']},
    'tb_activity': {'status': ['registered', 'ongoing', 'completed', 'cancelled']},
    'tb_user': {'status': ['active', 'inactive', 'suspended', 'deleted']},
}

# 허용된 카테고리 값
ALLOWED_CATEGORY_VALUES = {
    'tb_skill': {'category': ['technical', 'soft', 'domain']},
    'tb_badge': {'category': ['skill', 'achievement', 'activity', 'academic', 'special']},
    'tb_badge': {'level': ['bronze', 'silver', 'gold', 'platinum']},
    'tb_role': {'category': ['IT', 'Business', 'Finance', 'Research', 'Management', 'Design']},
    'tb_program': {'program_type': ['seminar', 'contest', 'club', 'volunteer', 'certificate', 'internship']},
    'tb_role_skill_map': {'importance': ['critical', 'important', 'nice_to_have']},
    'tb_role_skill_map': {'growth_trend': ['growing', 'stable', 'declining']},
    'tb_risk_alert': {'severity': ['low', 'medium', 'high', 'critical']},
    'tb_advisor_assignment': {'assignment_type': ['academic', 'career', 'mentoring', 'emergency']},
}

# 값 범위 검증 규칙
VALUE_RANGE_RULES = {
    'tb_grade': {
        'grade_point': (0.0, 4.5),
        'credits_earned': (1, 6),
    },
    'tb_student_competency': {
        'current_score': (0, 100),
        'target_score': (0, 100),
        'gap_score': (0, 100),
    },
    'tb_student_skill': {
        'current_level': (1, 5),
        'target_level': (1, 5),
    },
    'tb_skill': {
        'difficulty': (1, 5),
    },
    'tb_course': {
        'credits': (1, 6),
        'grade_level': (1, 4),
    },
    'tb_student': {
        'current_grade': (1, 4),
        'current_semester': (1, 8),
        'admission_year': (2015, 2030),
    },
    'tb_competency': {
        'weight': (0.0, 1.0),
        'max_score': (1, 100),
    },
    'tb_advisor_assignment': {
        'priority': (1, 5),
    },
    'tb_coaching_goal': {
        'priority': (1, 5),
        'achievement_rate': (0, 100),
    },
}

# 영문명 패턴 검증 (한글 포함 시 오류)
ENGLISH_ONLY_COLUMNS = {
    'tb_college': ['college_nm', 'college_nm_en'],
    'tb_department': ['department_nm', 'department_nm_en'],
    'tb_university': ['university_nm'],
}

# FK 관계 정의 (테이블: [(fk_column, ref_table, ref_column), ...])
FK_RELATIONSHIPS = {
    'tb_college': [('university_cd', 'tb_university', 'university_cd')],
    'tb_department': [('college_cd', 'tb_college', 'college_cd')],
    'tb_student': [
        ('university_cd', 'tb_university', 'university_cd'),
        ('department_cd', 'tb_department', 'department_cd'),
    ],
    'tb_professor': [('department_cd', 'tb_department', 'department_cd')],
    'tb_advisor': [('department_cd', 'tb_department', 'department_cd')],
    'tb_course': [('department_cd', 'tb_department', 'department_cd')],
    'tb_course_offering': [
        ('course_cd', 'tb_course', 'course_cd'),
        ('term_cd', 'tb_term', 'term_cd'),
        ('professor_cd', 'tb_professor', 'professor_cd'),
    ],
    'tb_enrollment': [
        ('student_id', 'tb_student', 'student_id'),
        ('offering_id', 'tb_course_offering', 'offering_id'),
        ('term_cd', 'tb_term', 'term_cd'),
    ],
    'tb_grade': [
        ('enrollment_id', 'tb_enrollment', 'enrollment_id'),
        ('student_id', 'tb_student', 'student_id'),
        ('course_cd', 'tb_course', 'course_cd'),
        ('term_cd', 'tb_term', 'term_cd'),
    ],
    'tb_student_skill': [
        ('student_id', 'tb_student', 'student_id'),
        ('skill_cd', 'tb_skill', 'skill_cd'),
    ],
    'tb_student_competency': [
        ('student_id', 'tb_student', 'student_id'),
        ('competency_cd', 'tb_competency', 'competency_cd'),
    ],
    'tb_student_badge': [
        ('student_id', 'tb_student', 'student_id'),
        ('badge_id', 'tb_badge', 'badge_id'),
    ],
    'tb_coaching_goal': [
        ('std_id', 'tb_student', 'student_id'),
        ('target_role_cd', 'tb_role', 'role_cd'),
    ],
    'tb_coaching_plan': [('goal_id', 'tb_coaching_goal', 'goal_id')],
    'tb_advisor_assignment': [
        ('advisor_id', 'tb_advisor', 'advisor_id'),
        ('student_id', 'tb_student', 'student_id'),
    ],
    'tb_advisor_note': [('assignment_id', 'tb_advisor_assignment', 'assignment_id')],
    'tb_advisor_intervention': [('assignment_id', 'tb_advisor_assignment', 'assignment_id')],
    'tb_activity': [
        ('student_id', 'tb_student', 'student_id'),
        ('program_cd', 'tb_program', 'program_cd'),
    ],
    'tb_achievement': [('student_id', 'tb_student', 'student_id')],
    'tb_risk_alert': [('student_id', 'tb_student', 'student_id')],
    'tb_skill_passport': [('student_id', 'tb_student', 'student_id')],
    'tb_simulation_scenario': [('student_id', 'tb_student', 'student_id')],
    'tb_role_skill_map': [
        ('role_cd', 'tb_role', 'role_cd'),
        ('skill_cd', 'tb_skill', 'skill_cd'),
    ],
    'tb_skill_competency_map': [
        ('skill_cd', 'tb_skill', 'skill_cd'),
        ('competency_cd', 'tb_competency', 'competency_cd'),
    ],
    'tb_course_competency_map': [
        ('course_cd', 'tb_course', 'course_cd'),
        ('competency_cd', 'tb_competency', 'competency_cd'),
    ],
    'tb_grade_summary': [
        ('student_id', 'tb_student', 'student_id'),
        ('term_cd', 'tb_term', 'term_cd'),
    ],
    'tb_cumulative_summary': [('student_id', 'tb_student', 'student_id')],
    'tb_alumni_cohort': [('department_cd', 'tb_department', 'department_cd')],
    'tb_success_pattern': [
        ('department_cd', 'tb_department', 'department_cd'),
        ('role_cd', 'tb_role', 'role_cd'),
    ],
    'tb_user': [('student_id', 'tb_student', 'student_id')],
    'tb_user_session': [('user_id', 'tb_user', 'user_id')],
    'tb_recommendation_run': [('student_id', 'tb_student', 'student_id')],
    'tb_recommendation_item': [('run_id', 'tb_recommendation_run', 'run_id')],
    'tb_opportunity_recommendation': [
        ('student_id', 'tb_student', 'student_id'),
        ('opportunity_id', 'tb_opportunity', 'opportunity_id'),
    ],
    'tb_opportunity_application': [
        ('student_id', 'tb_student', 'student_id'),
        ('opportunity_id', 'tb_opportunity', 'opportunity_id'),
    ],
    'tb_cohort_snapshot': [('department_cd', 'tb_department', 'department_cd')],
    'tb_skill_gap_analysis': [
        ('student_id', 'tb_student', 'student_id'),
        ('target_role_cd', 'tb_role', 'role_cd'),
    ],
    'tb_skill_relation': [
        ('skill_cd_from', 'tb_skill', 'skill_cd'),
        ('skill_cd_to', 'tb_skill', 'skill_cd'),
    ],
    'tb_prerequisite': [
        ('course_cd', 'tb_course', 'course_cd'),
        ('prerequisite_course_cd', 'tb_course', 'course_cd'),
    ],
    'tb_professor_course': [
        ('professor_cd', 'tb_professor', 'professor_cd'),
        ('course_cd', 'tb_course', 'course_cd'),
    ],
    'tb_coaching_checkin': [('goal_id', 'tb_coaching_goal', 'goal_id')],
    'tb_coaching_retrospective': [('goal_id', 'tb_coaching_goal', 'goal_id')],
    'tb_scenario_comparison': [('student_id', 'tb_student', 'student_id')],
    'tb_eval_feedback': [('run_id', 'tb_recommendation_run', 'run_id')],
}

# 1:1 관계 검증 (한 쪽에서 중복 불가)
ONE_TO_ONE_RELATIONSHIPS = {
    'tb_skill_passport': ('student_id', 'tb_student'),  # 학생당 1개
    'tb_cumulative_summary': ('student_id', 'tb_student'),  # 학생당 1개
}

# 유일성 제약 검증
UNIQUE_CONSTRAINTS = {
    'tb_student': [['student_id']],
    'tb_user': [['login_id']],
    'tb_college': [['college_cd']],
    'tb_department': [['department_cd']],
    'tb_course': [['course_cd']],
    'tb_professor': [['professor_cd']],
    'tb_term': [['term_cd']],
    'tb_competency': [['competency_cd']],
    'tb_skill': [['skill_cd']],
    'tb_role': [['role_cd']],
    'tb_badge': [['badge_cd']],
    'tb_program': [['program_cd']],
    'tb_advisor': [['advisor_cd']],
    'tb_student_competency': [['student_id', 'competency_cd']],
}


class FullDataValidator:
    """전수 데이터 검증기"""

    def __init__(self, conn, schema: str = SCHEMA):
        self.conn = conn
        self.cur = conn.cursor()
        self.schema = schema
        self.cur.execute(f"SET search_path TO {schema}")
        self.results: List[TableValidationResult] = []
        self.fix_sqls: List[str] = []

    def _execute(self, query: str) -> Any:
        """단일 값 반환 쿼리 실행"""
        try:
            self.cur.execute(query)
            result = self.cur.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.conn.rollback()
            self.cur.execute(f"SET search_path TO {self.schema}")
            raise

    def _execute_all(self, query: str) -> List[Tuple]:
        """모든 결과 반환"""
        try:
            self.cur.execute(query)
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            self.cur.execute(f"SET search_path TO {self.schema}")
            raise

    def _table_exists(self, table_name: str) -> bool:
        """테이블 존재 여부"""
        query = f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = '{self.schema}'
                AND table_name = '{table_name}'
            )
        """
        return self._execute(query)

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """컬럼 존재 여부"""
        query = f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = '{self.schema}'
                AND table_name = '{table_name}'
                AND column_name = '{column_name}'
            )
        """
        return self._execute(query)

    def _get_row_count(self, table_name: str) -> int:
        """테이블 행 수"""
        return self._execute(f"SELECT COUNT(*) FROM {self.schema}.{table_name}") or 0

    # ==========================================
    # 검증 메서드들
    # ==========================================

    def check_korean_in_english_columns(self, table_name: str, result: TableValidationResult):
        """영문 컬럼에 한글 포함 여부 검증"""
        if table_name not in ENGLISH_ONLY_COLUMNS:
            return

        columns = ENGLISH_ONLY_COLUMNS[table_name]
        for col in columns:
            if not self._column_exists(table_name, col):
                continue

            # 한글 포함 행 검색
            query = f"""
                SELECT COUNT(*), (SELECT ARRAY_AGG(sub.{col}) FROM (
                    SELECT {col} FROM {self.schema}.{table_name}
                    WHERE {col} ~ '[가-힣]'
                    ORDER BY {col} LIMIT 5
                ) sub)
                FROM {self.schema}.{table_name}
                WHERE {col} ~ '[가-힣]'
            """
            try:
                count, samples = self._execute_all(query)[0]
                if count and count > 0:
                    # 데이터 스왑 필요 여부 확인
                    col_en = f"{col.replace('_nm', '_nm_en')}" if '_nm_en' not in col else col
                    if col != col_en and self._column_exists(table_name, col_en):
                        fix_sql = f"""
-- {table_name}: {col}과 {col_en} 값 교환 (한글→영문, 영문→한글)
UPDATE {self.schema}.{table_name}
SET {col} = {col_en}, {col_en} = {col}
WHERE {col} ~ '[가-힣]';
"""
                        issue_type = IssueType.DATA_SWAP
                    else:
                        fix_sql = f"-- {table_name}.{col}: 한글 데이터 수동 확인 필요"
                        issue_type = IssueType.PATTERN_VIOLATION

                    result.add_issue(ValidationIssue(
                        table_name=table_name,
                        column_name=col,
                        issue_type=issue_type,
                        severity=IssueSeverity.HIGH,
                        message=f"영문 컬럼에 한글 포함 ({count}건)",
                        affected_rows=count,
                        sample_values=samples[:5] if samples else [],
                        fix_sql=fix_sql
                    ))
            except Exception as e:
                print(f"  Warning: {table_name}.{col} 검증 중 오류: {e}")

    def check_fk_integrity(self, table_name: str, result: TableValidationResult):
        """FK 참조 무결성 검증"""
        if table_name not in FK_RELATIONSHIPS:
            return

        for fk_col, ref_table, ref_col in FK_RELATIONSHIPS[table_name]:
            if not self._column_exists(table_name, fk_col):
                continue
            if not self._table_exists(ref_table):
                continue

            query = f"""
                SELECT COUNT(*), (SELECT ARRAY_AGG(sub.{fk_col}::text) FROM (
                    SELECT t.{fk_col}
                    FROM {self.schema}.{table_name} t
                    LEFT JOIN {self.schema}.{ref_table} r ON t.{fk_col} = r.{ref_col}
                    WHERE t.{fk_col} IS NOT NULL AND r.{ref_col} IS NULL
                    LIMIT 5
                ) sub)
                FROM {self.schema}.{table_name} t
                LEFT JOIN {self.schema}.{ref_table} r ON t.{fk_col} = r.{ref_col}
                WHERE t.{fk_col} IS NOT NULL AND r.{ref_col} IS NULL
            """
            try:
                count, samples = self._execute_all(query)[0]
                if count and count > 0:
                    result.add_issue(ValidationIssue(
                        table_name=table_name,
                        column_name=fk_col,
                        issue_type=IssueType.FK_VIOLATION,
                        severity=IssueSeverity.CRITICAL,
                        message=f"FK 참조 위반: {ref_table}.{ref_col} ({count}건)",
                        affected_rows=count,
                        sample_values=samples[:5] if samples else [],
                    ))
            except Exception as e:
                print(f"  Warning: {table_name}.{fk_col} FK 검증 중 오류: {e}")

    def check_unique_constraints(self, table_name: str, result: TableValidationResult):
        """유일성 제약 검증"""
        if table_name not in UNIQUE_CONSTRAINTS:
            return

        for cols in UNIQUE_CONSTRAINTS[table_name]:
            if not all(self._column_exists(table_name, c) for c in cols):
                continue

            cols_str = ", ".join(cols)
            query = f"""
                SELECT COUNT(*) FROM (
                    SELECT {cols_str} FROM {self.schema}.{table_name}
                    GROUP BY {cols_str} HAVING COUNT(*) > 1
                ) dup
            """
            try:
                count = self._execute(query) or 0
                if count > 0:
                    result.add_issue(ValidationIssue(
                        table_name=table_name,
                        column_name=cols_str,
                        issue_type=IssueType.UNIQUE_VIOLATION,
                        severity=IssueSeverity.CRITICAL,
                        message=f"중복 데이터 ({count}건)",
                        affected_rows=count,
                    ))
            except Exception as e:
                print(f"  Warning: {table_name} UNIQUE 검증 중 오류: {e}")

    def check_one_to_one(self, table_name: str, result: TableValidationResult):
        """1:1 관계 검증"""
        if table_name not in ONE_TO_ONE_RELATIONSHIPS:
            return

        col, ref_table = ONE_TO_ONE_RELATIONSHIPS[table_name]
        if not self._column_exists(table_name, col):
            return

        query = f"""
            SELECT COUNT(*) FROM (
                SELECT {col} FROM {self.schema}.{table_name}
                WHERE {col} IS NOT NULL
                GROUP BY {col} HAVING COUNT(*) > 1
            ) dup
        """
        try:
            count = self._execute(query) or 0
            if count > 0:
                result.add_issue(ValidationIssue(
                    table_name=table_name,
                    column_name=col,
                    issue_type=IssueType.UNIQUE_VIOLATION,
                    severity=IssueSeverity.CRITICAL,
                    message=f"1:1 관계 위반 - 중복 참조 ({count}건)",
                    affected_rows=count,
                ))
        except Exception as e:
            print(f"  Warning: {table_name} 1:1 검증 중 오류: {e}")

    def check_value_ranges(self, table_name: str, result: TableValidationResult):
        """값 범위 검증"""
        if table_name not in VALUE_RANGE_RULES:
            return

        for col, (min_val, max_val) in VALUE_RANGE_RULES[table_name].items():
            if not self._column_exists(table_name, col):
                continue

            query = f"""
                SELECT COUNT(*), MIN({col}::numeric), MAX({col}::numeric)
                FROM {self.schema}.{table_name}
                WHERE {col} IS NOT NULL
                  AND ({col}::numeric < {min_val} OR {col}::numeric > {max_val})
            """
            try:
                count, actual_min, actual_max = self._execute_all(query)[0]
                if count and count > 0:
                    result.add_issue(ValidationIssue(
                        table_name=table_name,
                        column_name=col,
                        issue_type=IssueType.RANGE_VIOLATION,
                        severity=IssueSeverity.HIGH,
                        message=f"범위 위반 ({min_val}~{max_val}), 실제: {actual_min}~{actual_max} ({count}건)",
                        affected_rows=count,
                    ))
            except Exception as e:
                print(f"  Warning: {table_name}.{col} 범위 검증 중 오류: {e}")

    def check_enum_values(self, table_name: str, result: TableValidationResult):
        """ENUM/상태 값 검증"""
        enum_checks = {}

        # 상태 값 검사
        if table_name in ALLOWED_STATUS_VALUES:
            enum_checks.update(ALLOWED_STATUS_VALUES[table_name])

        # 카테고리 값 검사
        if table_name in ALLOWED_CATEGORY_VALUES:
            enum_checks.update(ALLOWED_CATEGORY_VALUES[table_name])

        for col, allowed_values in enum_checks.items():
            if not self._column_exists(table_name, col):
                continue

            allowed_str = ", ".join([f"'{v}'" for v in allowed_values])
            query = f"""
                SELECT COUNT(*), (SELECT ARRAY_AGG(DISTINCT sub.{col}) FROM (
                    SELECT DISTINCT {col}
                    FROM {self.schema}.{table_name}
                    WHERE {col} IS NOT NULL AND {col} NOT IN ({allowed_str})
                    LIMIT 10
                ) sub)
                FROM {self.schema}.{table_name}
                WHERE {col} IS NOT NULL
                  AND {col} NOT IN ({allowed_str})
            """
            try:
                count, invalid_values = self._execute_all(query)[0]
                if count and count > 0:
                    result.add_issue(ValidationIssue(
                        table_name=table_name,
                        column_name=col,
                        issue_type=IssueType.ENUM_VIOLATION,
                        severity=IssueSeverity.HIGH,
                        message=f"허용되지 않은 값: {invalid_values} ({count}건)",
                        affected_rows=count,
                        sample_values=invalid_values[:5] if invalid_values else [],
                    ))
            except Exception as e:
                print(f"  Warning: {table_name}.{col} ENUM 검증 중 오류: {e}")

    def check_row_count(self, table_name: str, result: TableValidationResult):
        """행 수 검증 (목표치 대비)"""
        if table_name not in TARGET_ROW_COUNTS:
            return

        expected = TARGET_ROW_COUNTS[table_name]
        actual = result.row_count
        tolerance = 0.2  # 20% 허용 오차

        min_expected = int(expected * (1 - tolerance))
        max_expected = int(expected * (1 + tolerance))

        if not (min_expected <= actual <= max_expected):
            severity = IssueSeverity.LOW if actual > 0 else IssueSeverity.MEDIUM
            result.add_issue(ValidationIssue(
                table_name=table_name,
                column_name="*",
                issue_type=IssueType.ROW_COUNT_MISMATCH,
                severity=severity,
                message=f"행 수 불일치: 목표 {expected}, 실제 {actual}",
                affected_rows=abs(expected - actual),
            ))

    def validate_table(self, table_name: str) -> TableValidationResult:
        """단일 테이블 검증"""
        if not self._table_exists(table_name):
            result = TableValidationResult(table_name=table_name, row_count=0, passed=False)
            result.add_issue(ValidationIssue(
                table_name=table_name,
                column_name="*",
                issue_type=IssueType.FK_VIOLATION,
                severity=IssueSeverity.CRITICAL,
                message="테이블이 존재하지 않음",
            ))
            return result

        row_count = self._get_row_count(table_name)
        result = TableValidationResult(table_name=table_name, row_count=row_count)

        # 검증 실행
        self.check_korean_in_english_columns(table_name, result)
        self.check_fk_integrity(table_name, result)
        self.check_unique_constraints(table_name, result)
        self.check_one_to_one(table_name, result)
        self.check_value_ranges(table_name, result)
        self.check_enum_values(table_name, result)
        self.check_row_count(table_name, result)

        return result

    def validate_all(self) -> List[TableValidationResult]:
        """모든 테이블 검증"""
        all_tables = get_all_tables_in_order()
        self.results = []

        print("\n" + "=" * 70)
        print("IDINO Career 전수 데이터 검증")
        print("=" * 70)
        print(f"검증 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"스키마: {self.schema}")
        print(f"대상 테이블: {len(all_tables)}개")
        print("=" * 70)

        for level_name, tables in TABLE_LEVELS:
            print(f"\n[{level_name}] 검증 중...")
            for table in tables:
                result = self.validate_table(table)
                self.results.append(result)

                status = "✅ PASS" if result.passed else "❌ FAIL"
                issue_count = len(result.issues)
                print(f"  {table}: {status} ({result.row_count} rows, {issue_count} issues)")

        return self.results

    def generate_report(self) -> str:
        """검증 리포트 생성"""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("IDINO Career 전수 검증 리포트")
        report_lines.append("=" * 70)
        report_lines.append(f"검증 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        total_tables = len(self.results)
        passed_tables = sum(1 for r in self.results if r.passed)
        failed_tables = total_tables - passed_tables
        total_rows = sum(r.row_count for r in self.results)
        total_issues = sum(len(r.issues) for r in self.results)

        report_lines.append(f"총 테이블: {total_tables}개")
        report_lines.append(f"총 레코드: {total_rows:,}건")
        report_lines.append("")

        report_lines.append("[테이블별 검증 결과]")
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            report_lines.append(f"{result.table_name:35} {status} ({result.row_count} rows, {len(result.issues)} issues)")

            for issue in result.issues:
                severity_icon = {
                    IssueSeverity.CRITICAL: "🔴",
                    IssueSeverity.HIGH: "🟠",
                    IssueSeverity.MEDIUM: "🟡",
                    IssueSeverity.LOW: "🟢",
                }[issue.severity]
                report_lines.append(f"  {severity_icon} [{issue.issue_type.value}] {issue.column_name}: {issue.message}")
                if issue.sample_values:
                    samples_str = str(issue.sample_values[:3])
                    if len(samples_str) > 60:
                        samples_str = samples_str[:60] + "..."
                    report_lines.append(f"     샘플: {samples_str}")

        report_lines.append("")
        report_lines.append("[요약]")
        report_lines.append(f"통과: {passed_tables}/{total_tables} 테이블")
        report_lines.append(f"실패: {failed_tables}/{total_tables} 테이블")
        report_lines.append(f"총 이슈: {total_issues}개")

        # 이슈 유형별 통계
        issue_by_type: Dict[IssueType, int] = {}
        for result in self.results:
            for issue in result.issues:
                issue_by_type[issue.issue_type] = issue_by_type.get(issue.issue_type, 0) + 1

        if issue_by_type:
            report_lines.append("")
            report_lines.append("[이슈 유형별 통계]")
            for itype, count in sorted(issue_by_type.items(), key=lambda x: -x[1]):
                report_lines.append(f"  {itype.value}: {count}건")

        return "\n".join(report_lines)

    def generate_fix_sql(self) -> str:
        """수정 SQL 생성"""
        fix_lines = []
        fix_lines.append("-- IDINO Career 데이터 수정 SQL")
        fix_lines.append(f"-- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        fix_lines.append(f"-- 스키마: {self.schema}")
        fix_lines.append("")
        fix_lines.append(f"SET search_path TO {self.schema};")
        fix_lines.append("")

        has_fixes = False
        for result in self.results:
            for issue in result.issues:
                if issue.fix_sql:
                    has_fixes = True
                    fix_lines.append(issue.fix_sql)

        if not has_fixes:
            fix_lines.append("-- 자동 수정 가능한 이슈가 없습니다.")

        return "\n".join(fix_lines)


def main():
    """메인 실행"""
    print("IDINO Career 데이터 전수 검증기")
    print("-" * 40)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"데이터베이스 연결 성공: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        return 1

    try:
        validator = FullDataValidator(conn, SCHEMA)

        # 전수 검증 실행
        validator.validate_all()

        # 리포트 생성
        report = validator.generate_report()
        print("\n" + report)

        # 수정 SQL 생성
        fix_sql = validator.generate_fix_sql()

        # 파일 저장
        report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n리포트 저장: {report_file}")

        fix_sql_file = f"fix_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with open(fix_sql_file, 'w', encoding='utf-8') as f:
            f.write(fix_sql)
        print(f"수정 SQL 저장: {fix_sql_file}")

        # 결과 요약
        failed = [r for r in validator.results if not r.passed]
        if failed:
            print(f"\n❌ 검증 실패: {len(failed)}개 테이블에서 이슈 발견")
            return 1
        else:
            print(f"\n✅ 검증 통과: 모든 테이블 정상")
            return 0

    except Exception as e:
        print(f"검증 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == '__main__':
    exit(main())
