#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IDINO Career Data Migration Validators

데이터 무결성 검증을 위한 검증 함수들
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """검증 결과"""
    check_name: str
    passed: bool
    expected: Any
    actual: Any
    message: str = ""


class DataValidator:
    """데이터 무결성 검증 클래스"""

    def __init__(self, conn, schema: str = 'idino_career'):
        self.conn = conn
        self.cur = conn.cursor()
        self.schema = schema
        self.cur.execute(f"SET search_path TO {schema}")

    def _execute(self, query: str) -> Any:
        """쿼리 실행 및 단일 결과 반환"""
        self.cur.execute(query)
        result = self.cur.fetchone()
        return result[0] if result else None

    def _execute_all(self, query: str) -> List[Tuple]:
        """쿼리 실행 및 모든 결과 반환"""
        self.cur.execute(query)
        return self.cur.fetchall()

    # ==========================================
    # FK Reference Integrity Checks
    # ==========================================

    def check_fk_student_department(self) -> ValidationResult:
        """학생 → 학과 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_student s
            LEFT JOIN {self.schema}.tb_department d ON s.department_cd = d.department_cd
            WHERE s.department_cd IS NOT NULL AND d.department_cd IS NULL
        """)
        return ValidationResult(
            check_name="FK: student → department",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan student records found" if count > 0 else "OK"
        )

    def check_fk_enrollment_student(self) -> ValidationResult:
        """수강신청 → 학생 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_enrollment e
            LEFT JOIN {self.schema}.tb_student s ON e.student_id = s.student_id
            WHERE e.student_id IS NOT NULL AND s.student_id IS NULL
        """)
        return ValidationResult(
            check_name="FK: enrollment → student",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan enrollment records found" if count > 0 else "OK"
        )

    def check_fk_enrollment_offering(self) -> ValidationResult:
        """수강신청 → 개설과목 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_enrollment e
            LEFT JOIN {self.schema}.tb_course_offering co ON e.course_offering_id = co.offering_id
            WHERE e.course_offering_id IS NOT NULL AND co.offering_id IS NULL
        """)
        return ValidationResult(
            check_name="FK: enrollment → course_offering",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan enrollment records found" if count > 0 else "OK"
        )

    def check_fk_grade_enrollment(self) -> ValidationResult:
        """성적 → 수강신청 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_grade g
            LEFT JOIN {self.schema}.tb_enrollment e ON g.enrollment_id = e.enrollment_id
            WHERE g.enrollment_id IS NOT NULL AND e.enrollment_id IS NULL
        """)
        return ValidationResult(
            check_name="FK: grade → enrollment",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan grade records found" if count > 0 else "OK"
        )

    def check_fk_student_skill(self) -> ValidationResult:
        """학생스킬 → 학생, 스킬 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_student_skill ss
            LEFT JOIN {self.schema}.tb_student s ON ss.student_id = s.student_id
            LEFT JOIN {self.schema}.tb_skill sk ON ss.skill_cd = sk.skill_cd
            WHERE (ss.student_id IS NOT NULL AND s.student_id IS NULL)
               OR (ss.skill_cd IS NOT NULL AND sk.skill_cd IS NULL)
        """)
        return ValidationResult(
            check_name="FK: student_skill → student, skill",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan student_skill records found" if count > 0 else "OK"
        )

    def check_fk_student_competency(self) -> ValidationResult:
        """학생역량 → 학생, 역량 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_student_competency sc
            LEFT JOIN {self.schema}.tb_student s ON sc.student_id = s.student_id
            LEFT JOIN {self.schema}.tb_competency c ON sc.competency_cd = c.competency_cd
            WHERE (sc.student_id IS NOT NULL AND s.student_id IS NULL)
               OR (sc.competency_cd IS NOT NULL AND c.competency_cd IS NULL)
        """)
        return ValidationResult(
            check_name="FK: student_competency → student, competency",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan student_competency records found" if count > 0 else "OK"
        )

    def check_fk_coaching_goal_student(self) -> ValidationResult:
        """코칭목표 → 학생 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_coaching_goal cg
            LEFT JOIN {self.schema}.tb_student s ON cg.std_id = s.student_id
            WHERE cg.std_id IS NOT NULL AND s.student_id IS NULL
        """)
        return ValidationResult(
            check_name="FK: coaching_goal → student",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan coaching_goal records found" if count > 0 else "OK"
        )

    def check_fk_coaching_plan_goal(self) -> ValidationResult:
        """코칭계획 → 코칭목표 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_coaching_plan cp
            LEFT JOIN {self.schema}.tb_coaching_goal cg ON cp.goal_id = cg.goal_id
            WHERE cp.goal_id IS NOT NULL AND cg.goal_id IS NULL
        """)
        return ValidationResult(
            check_name="FK: coaching_plan → coaching_goal",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan coaching_plan records found" if count > 0 else "OK"
        )

    def check_fk_advisor_assignment(self) -> ValidationResult:
        """상담배정 → 상담사, 학생 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_advisor_assignment aa
            LEFT JOIN {self.schema}.tb_advisor a ON aa.advisor_id = a.advisor_id
            LEFT JOIN {self.schema}.tb_student s ON aa.student_id = s.student_id
            WHERE (aa.advisor_id IS NOT NULL AND a.advisor_id IS NULL)
               OR (aa.student_id IS NOT NULL AND s.student_id IS NULL)
        """)
        return ValidationResult(
            check_name="FK: advisor_assignment → advisor, student",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan advisor_assignment records found" if count > 0 else "OK"
        )

    def check_fk_course_offering(self) -> ValidationResult:
        """개설과목 → 과목, 학기, 교수 FK 검증"""
        count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_course_offering co
            LEFT JOIN {self.schema}.tb_course c ON co.course_cd = c.course_cd
            LEFT JOIN {self.schema}.tb_term t ON co.term_cd = t.term_cd
            LEFT JOIN {self.schema}.tb_professor p ON co.professor_cd = p.professor_cd
            WHERE (co.course_cd IS NOT NULL AND c.course_cd IS NULL)
               OR (co.term_cd IS NOT NULL AND t.term_cd IS NULL)
               OR (co.professor_cd IS NOT NULL AND p.professor_cd IS NULL)
        """)
        return ValidationResult(
            check_name="FK: course_offering → course, term, professor",
            passed=(count == 0),
            expected=0,
            actual=count,
            message=f"{count} orphan course_offering records found" if count > 0 else "OK"
        )

    # ==========================================
    # Uniqueness Constraints
    # ==========================================

    def check_unique_student_id(self) -> ValidationResult:
        """학생 ID 유일성 검증"""
        duplicates = self._execute(f"""
            SELECT COUNT(*) FROM (
                SELECT student_id FROM {self.schema}.tb_student
                GROUP BY student_id HAVING COUNT(*) > 1
            ) dup
        """)
        return ValidationResult(
            check_name="UNIQUE: student_id",
            passed=(duplicates == 0),
            expected=0,
            actual=duplicates,
            message=f"{duplicates} duplicate student_id found" if duplicates > 0 else "OK"
        )

    def check_unique_user_login_id(self) -> ValidationResult:
        """사용자 로그인 ID 유일성 검증"""
        duplicates = self._execute(f"""
            SELECT COUNT(*) FROM (
                SELECT login_id FROM {self.schema}.tb_user
                GROUP BY login_id HAVING COUNT(*) > 1
            ) dup
        """)
        return ValidationResult(
            check_name="UNIQUE: user.login_id",
            passed=(duplicates == 0),
            expected=0,
            actual=duplicates,
            message=f"{duplicates} duplicate login_id found" if duplicates > 0 else "OK"
        )

    def check_unique_student_competency(self) -> ValidationResult:
        """학생-역량 조합 유일성 검증"""
        duplicates = self._execute(f"""
            SELECT COUNT(*) FROM (
                SELECT student_id, competency_cd FROM {self.schema}.tb_student_competency
                GROUP BY student_id, competency_cd HAVING COUNT(*) > 1
            ) dup
        """)
        return ValidationResult(
            check_name="UNIQUE: student_competency(student_id, competency_cd)",
            passed=(duplicates == 0),
            expected=0,
            actual=duplicates,
            message=f"{duplicates} duplicate combinations found" if duplicates > 0 else "OK"
        )

    # ==========================================
    # 1:1 Relationship Checks
    # ==========================================

    def check_one_to_one_grade_enrollment(self) -> ValidationResult:
        """성적-수강신청 1:1 관계 검증"""
        duplicates = self._execute(f"""
            SELECT COUNT(*) FROM (
                SELECT enrollment_id FROM {self.schema}.tb_grade
                WHERE enrollment_id IS NOT NULL
                GROUP BY enrollment_id HAVING COUNT(*) > 1
            ) dup
        """)
        return ValidationResult(
            check_name="1:1: grade ↔ enrollment",
            passed=(duplicates == 0),
            expected=0,
            actual=duplicates,
            message=f"{duplicates} enrollments with multiple grades" if duplicates > 0 else "OK"
        )

    def check_one_to_one_skill_passport(self) -> ValidationResult:
        """스킬패스포트-학생 1:1 관계 검증"""
        duplicates = self._execute(f"""
            SELECT COUNT(*) FROM (
                SELECT student_id FROM {self.schema}.tb_skill_passport
                WHERE student_id IS NOT NULL
                GROUP BY student_id HAVING COUNT(*) > 1
            ) dup
        """)
        return ValidationResult(
            check_name="1:1: skill_passport ↔ student",
            passed=(duplicates == 0),
            expected=0,
            actual=duplicates,
            message=f"{duplicates} students with multiple passports" if duplicates > 0 else "OK"
        )

    def check_one_to_one_cumulative_summary(self) -> ValidationResult:
        """누적성적요약-학생 1:1 관계 검증"""
        duplicates = self._execute(f"""
            SELECT COUNT(*) FROM (
                SELECT student_id FROM {self.schema}.tb_cumulative_summary
                WHERE student_id IS NOT NULL
                GROUP BY student_id HAVING COUNT(*) > 1
            ) dup
        """)
        return ValidationResult(
            check_name="1:1: cumulative_summary ↔ student",
            passed=(duplicates == 0),
            expected=0,
            actual=duplicates,
            message=f"{duplicates} students with multiple summaries" if duplicates > 0 else "OK"
        )

    # ==========================================
    # Data Range Checks
    # ==========================================

    def check_gpa_range(self) -> ValidationResult:
        """GPA 범위 검증 (0.0 ~ 4.5)"""
        out_of_range = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_grade
            WHERE grade_point IS NOT NULL
              AND (grade_point < 0 OR grade_point > 4.5)
        """)
        return ValidationResult(
            check_name="RANGE: grade_point (0.0-4.5)",
            passed=(out_of_range == 0),
            expected=0,
            actual=out_of_range,
            message=f"{out_of_range} grades out of range" if out_of_range > 0 else "OK"
        )

    def check_competency_score_range(self) -> ValidationResult:
        """역량 점수 범위 검증 (0 ~ 100)"""
        out_of_range = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_student_competency
            WHERE (current_score IS NOT NULL AND (current_score < 0 OR current_score > 100))
               OR (target_score IS NOT NULL AND (target_score < 0 OR target_score > 100))
        """)
        return ValidationResult(
            check_name="RANGE: competency_score (0-100)",
            passed=(out_of_range == 0),
            expected=0,
            actual=out_of_range,
            message=f"{out_of_range} scores out of range" if out_of_range > 0 else "OK"
        )

    def check_skill_level_range(self) -> ValidationResult:
        """스킬 레벨 범위 검증 (1 ~ 5)"""
        out_of_range = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_student_skill
            WHERE (current_level IS NOT NULL AND (current_level < 1 OR current_level > 5))
               OR (target_level IS NOT NULL AND (target_level < 1 OR target_level > 5))
        """)
        return ValidationResult(
            check_name="RANGE: skill_level (1-5)",
            passed=(out_of_range == 0),
            expected=0,
            actual=out_of_range,
            message=f"{out_of_range} levels out of range" if out_of_range > 0 else "OK"
        )

    def check_credits_range(self) -> ValidationResult:
        """학점 범위 검증 (1 ~ 6)"""
        out_of_range = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_grade
            WHERE credits_earned IS NOT NULL
              AND (credits_earned < 1 OR credits_earned > 6)
        """)
        return ValidationResult(
            check_name="RANGE: credits_earned (1-6)",
            passed=(out_of_range == 0),
            expected=0,
            actual=out_of_range,
            message=f"{out_of_range} credits out of range" if out_of_range > 0 else "OK"
        )

    # ==========================================
    # NOT NULL Constraints
    # ==========================================

    def check_notnull_student_id(self) -> ValidationResult:
        """학생 ID NOT NULL 검증"""
        null_count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_student
            WHERE student_id IS NULL
        """)
        return ValidationResult(
            check_name="NOT NULL: student.student_id",
            passed=(null_count == 0),
            expected=0,
            actual=null_count,
            message=f"{null_count} null student_id found" if null_count > 0 else "OK"
        )

    def check_notnull_enrollment_required(self) -> ValidationResult:
        """수강신청 필수 컬럼 NOT NULL 검증"""
        null_count = self._execute(f"""
            SELECT COUNT(*) FROM {self.schema}.tb_enrollment
            WHERE student_id IS NULL OR course_offering_id IS NULL
        """)
        return ValidationResult(
            check_name="NOT NULL: enrollment (student_id, course_offering_id)",
            passed=(null_count == 0),
            expected=0,
            actual=null_count,
            message=f"{null_count} records with null required fields" if null_count > 0 else "OK"
        )

    # ==========================================
    # Row Count Checks
    # ==========================================

    def check_row_count(self, table_name: str, expected: int, tolerance: float = 0.1) -> ValidationResult:
        """테이블 행 수 검증"""
        actual = self._execute(f"SELECT COUNT(*) FROM {self.schema}.{table_name}")
        min_expected = int(expected * (1 - tolerance))
        max_expected = int(expected * (1 + tolerance))
        passed = min_expected <= actual <= max_expected

        return ValidationResult(
            check_name=f"ROW_COUNT: {table_name}",
            passed=passed,
            expected=f"{expected} (±{int(tolerance*100)}%)",
            actual=actual,
            message=f"Expected ~{expected}, got {actual}" if not passed else "OK"
        )

    # ==========================================
    # Run All Validations
    # ==========================================

    def run_all_checks(self, row_count_targets: Dict[str, int] = None) -> List[ValidationResult]:
        """모든 검증 실행"""
        results = []

        # FK 참조 무결성
        print("\n[1/5] FK Reference Integrity Checks...")
        results.append(self.check_fk_student_department())
        results.append(self.check_fk_enrollment_student())
        results.append(self.check_fk_enrollment_offering())
        results.append(self.check_fk_grade_enrollment())
        results.append(self.check_fk_student_skill())
        results.append(self.check_fk_student_competency())
        results.append(self.check_fk_coaching_goal_student())
        results.append(self.check_fk_coaching_plan_goal())
        results.append(self.check_fk_advisor_assignment())
        results.append(self.check_fk_course_offering())

        # 유일성 제약
        print("[2/5] Uniqueness Constraint Checks...")
        results.append(self.check_unique_student_id())
        results.append(self.check_unique_user_login_id())
        results.append(self.check_unique_student_competency())

        # 1:1 관계
        print("[3/5] 1:1 Relationship Checks...")
        results.append(self.check_one_to_one_grade_enrollment())
        results.append(self.check_one_to_one_skill_passport())
        results.append(self.check_one_to_one_cumulative_summary())

        # 데이터 범위
        print("[4/5] Data Range Checks...")
        results.append(self.check_gpa_range())
        results.append(self.check_competency_score_range())
        results.append(self.check_skill_level_range())
        results.append(self.check_credits_range())

        # NOT NULL
        print("[5/5] NOT NULL Constraint Checks...")
        results.append(self.check_notnull_student_id())
        results.append(self.check_notnull_enrollment_required())

        # Row counts (optional)
        if row_count_targets:
            print("[Bonus] Row Count Checks...")
            for table, expected in row_count_targets.items():
                results.append(self.check_row_count(table, expected))

        return results

    def print_results(self, results: List[ValidationResult]):
        """검증 결과 출력"""
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        if failed:
            print(f"\n❌ FAILED: {len(failed)} checks")
            for r in failed:
                print(f"  - {r.check_name}")
                print(f"    Expected: {r.expected}, Actual: {r.actual}")
                print(f"    {r.message}")

        print(f"\n✅ PASSED: {len(passed)} checks")
        for r in passed:
            print(f"  - {r.check_name}: {r.message}")

        print(f"\n{'=' * 60}")
        print(f"Total: {len(results)} checks, {len(passed)} passed, {len(failed)} failed")
        print("=" * 60)

        return len(failed) == 0
