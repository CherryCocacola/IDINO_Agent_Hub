"""
Student service business logic.
Matches database schema: idino_career
Updated to match actual database schema.
"""
import logging
from typing import List, Optional

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from shared.database.query_loader import get_query

from decimal import Decimal
from ..models import (
    Student,
    Department,
    College,
    Enrollment,
    Grade,
    CourseOffering,
    Course,
    Term,
    Program,
    Activity,
    Achievement,
)
from ..schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentDetailResponse,
    StudentSummaryResponse,
    DepartmentResponse,
    EnrollmentWithGradeResponse,
    ActivityResponse,
    ParticipationResponse,
    ParticipationCreate,
    AchievementResponse,
    AchievementCreate,
    DashboardSummary,
)

logger = logging.getLogger(__name__)


class StudentService:
    """Student service for handling student-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== GPA & Credits Calculation ====================

    async def calculate_gpa_and_credits(self, student_id: str) -> tuple[float, int]:
        """
        Calculate GPA and total earned credits for a student.
        First tries tb_grade, then falls back to tb_grade_summary.
        GPA = SUM(grade_point * credits) / SUM(credits)
        Returns: (gpa, total_credits)
        """
        # First, try tb_grade
        sql = text("""
            SELECT
                COALESCE(SUM(g.grade_point * g.credits_earned), 0) as weighted_sum,
                COALESCE(SUM(g.credits_earned), 0) as total_credits
            FROM tb_grade g
            WHERE g.student_id = :student_id
              AND g.grade_point IS NOT NULL
              AND g.credits_earned > 0
        """)

        try:
            result = await self.db.execute(sql, {"student_id": student_id})
            row = result.fetchone()

            if row and row.total_credits > 0:
                weighted_sum = float(row.weighted_sum) if row.weighted_sum else 0.0
                total_credits = int(row.total_credits) if row.total_credits else 0
                gpa = round(weighted_sum / total_credits, 2) if total_credits > 0 else 0.0
                return (gpa, total_credits)

            # Fallback to tb_grade_summary if tb_grade is empty
            summary_sql = text("""
                SELECT
                    COALESCE(SUM(gpa * earned_credits), 0) as weighted_sum,
                    COALESCE(SUM(earned_credits), 0) as total_credits
                FROM tb_grade_summary
                WHERE student_id = :student_id
                  AND gpa IS NOT NULL
                  AND earned_credits > 0
            """)
            summary_result = await self.db.execute(summary_sql, {"student_id": student_id})
            summary_row = summary_result.fetchone()

            if summary_row and summary_row.total_credits > 0:
                weighted_sum = float(summary_row.weighted_sum) if summary_row.weighted_sum else 0.0
                total_credits = int(summary_row.total_credits) if summary_row.total_credits else 0
                gpa = round(weighted_sum / total_credits, 2) if total_credits > 0 else 0.0
                return (gpa, total_credits)

            return (0.0, 0)
        except Exception as e:
            logger.warning(f"Failed to calculate GPA for {student_id}: {e}")
            return (0.0, 0)

    async def calculate_credit_breakdown(self, student_id: str) -> dict:
        """
        Calculate credit breakdown by course_type for a student.
        Returns: dict with major_credits, liberal_credits, elective_credits

        First tries tb_cumulative_summary (pre-computed values).
        Falls back to tb_grade JOIN tb_course method.

        course_type mapping (for fallback):
        - '전공필수', '전공선택', '전필', '전선', 'major' → major_credits
        - '교양필수', '교양선택', '교필', '교선', 'liberal', 'general' → liberal_credits
        - Others (일선, 자유선택, elective, etc.) → elective_credits
        """
        # First try: tb_cumulative_summary (reliable pre-computed values)
        summary_sql = text("""
            SELECT
                major_credits_earned,
                liberal_credits_earned,
                total_credits_earned
            FROM tb_cumulative_summary
            WHERE student_id = :student_id
            LIMIT 1
        """)

        try:
            summary_result = await self.db.execute(summary_sql, {"student_id": student_id})
            summary_row = summary_result.fetchone()

            if summary_row and summary_row.total_credits_earned and summary_row.total_credits_earned > 0:
                major = int(summary_row.major_credits_earned) if summary_row.major_credits_earned else 0
                liberal = int(summary_row.liberal_credits_earned) if summary_row.liberal_credits_earned else 0
                total = int(summary_row.total_credits_earned)
                elective = max(0, total - major - liberal)
                return {
                    'major_credits': major,
                    'liberal_credits': liberal,
                    'elective_credits': elective,
                }
        except Exception as e:
            logger.debug(f"tb_cumulative_summary not available for {student_id}: {e}")

        # Fallback: calculate from tb_grade JOIN tb_course
        sql = text("""
            SELECT
                c.course_type,
                COALESCE(SUM(g.credits_earned), 0) as credits
            FROM tb_grade g
            JOIN tb_course c ON g.course_cd = c.course_cd
            WHERE g.student_id = :student_id
              AND g.credits_earned > 0
            GROUP BY c.course_type
        """)

        try:
            result = await self.db.execute(sql, {"student_id": student_id})
            rows = result.fetchall()

            major_credits = 0
            liberal_credits = 0
            elective_credits = 0

            for row in rows:
                course_type = (row.course_type or '').strip()
                course_type_lower = course_type.lower()
                credits = int(row.credits) if row.credits else 0

                if course_type in ('1', '2') or any(t in course_type_lower for t in ['전공', '전필', '전선', 'major']):
                    major_credits += credits
                elif course_type in ('3', '4') or any(t in course_type_lower for t in ['교양', '교필', '교선', 'liberal', 'general']):
                    liberal_credits += credits
                else:
                    elective_credits += credits

            return {
                'major_credits': major_credits,
                'liberal_credits': liberal_credits,
                'elective_credits': elective_credits,
            }
        except Exception as e:
            logger.warning(f"Failed to calculate credit breakdown for {student_id}: {e}")
            return {
                'major_credits': 0,
                'liberal_credits': 0,
                'elective_credits': 0,
            }

    # ==================== Student Operations ====================

    async def get_student(self, student_id: str) -> Optional[StudentDetailResponse]:
        """Get student by ID with related data."""
        # Load student with department relationship
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.department))
            .where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            return None

        # Get counts (may be 0 if tables don't exist or no data)
        enrollment_count = 0
        activity_count = 0
        achievement_count = 0

        try:
            enrollment_count = await self.db.scalar(
                select(func.count(Enrollment.enrollment_id))
                .where(Enrollment.student_id == student_id)
            ) or 0
        except Exception:
            pass

        try:
            activity_count = await self.db.scalar(
                select(func.count(Activity.activity_id))
                .where(Activity.student_id == student_id)
            ) or 0
        except Exception:
            pass

        try:
            achievement_count = await self.db.scalar(
                select(func.count(Achievement.achievement_id))
                .where(Achievement.student_id == student_id)
            ) or 0
        except Exception:
            pass

        # Calculate GPA and credits
        gpa, completed_credits = await self.calculate_gpa_and_credits(student_id)

        # Calculate credit breakdown by course_type
        credit_breakdown = await self.calculate_credit_breakdown(student_id)

        # Build student summary
        student_summary = StudentSummaryResponse(
            completed_credits=completed_credits,
            remaining_credits=130 - completed_credits if completed_credits < 130 else 0,  # Default graduation credits
            major_credits=credit_breakdown['major_credits'],
            liberal_credits=credit_breakdown['liberal_credits'],
            elective_credits=credit_breakdown['elective_credits'],
            graduation_readiness_pct=round((completed_credits / 130) * 100, 1) if completed_credits > 0 else 0.0,
        )

        # Build department response if available
        department_response = None
        if student.department:
            department_response = DepartmentResponse(
                department_cd=student.department.department_cd,
                department_nm=student.department.department_nm,
                department_nm_en=student.department.department_nm_en,
            )

        # Build response with department relationship
        return StudentDetailResponse(
            student_id=student.student_id,
            student_nm=student.student_nm,
            department_cd=student.department_cd,
            university_cd=student.university_cd,
            email=student.email,
            phone=student.phone,
            admission_year=student.admission_year,
            birth_date=student.birth_date,
            gender=student.gender,
            current_grade=student.current_grade,
            current_semester=student.current_semester,
            career_goal=student.career_goal,
            status=student.status or "enrolled",
            ins_dt=student.ins_dt,
            department=department_response,
            enrollment_count=enrollment_count,
            activity_count=activity_count,
            achievement_count=achievement_count,
            gpa=gpa,
            completed_credits=completed_credits,
            summary=student_summary,
        )

    async def list_students(
        self,
        department_cd: Optional[str] = None,
        current_grade: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[StudentResponse]:
        """List students with optional filtering."""
        # Note: Excel data uses numeric status codes (11, 21, 22, 31, 32, etc.)
        # Temporarily disable status filtering to return all students
        query = select(Student)

        if department_cd:
            query = query.where(Student.department_cd == department_cd)
        if current_grade:
            query = query.where(Student.current_grade == current_grade)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        students = result.scalars().all()

        return [
            StudentResponse(
                student_id=s.student_id,
                student_nm=s.student_nm,
                department_cd=s.department_cd,
                current_grade=s.current_grade,
                current_semester=s.current_semester,
                career_goal=s.career_goal,
                status=s.status or "enrolled",
                ins_dt=s.ins_dt,
            )
            for s in students
        ]

    async def create_student(self, data: StudentCreate) -> StudentResponse:
        """Create a new student."""
        student = Student(
            student_id=data.student_id,
            student_nm=data.student_nm,
            university_cd=data.university_cd,
            department_cd=data.department_cd,
            email=data.email,
            phone=data.phone,
            admission_year=data.admission_year,
            birth_date=data.birth_date,
            gender=data.gender,
            current_grade=data.current_grade,
            current_semester=data.current_semester,
            career_goal=data.career_goal,
            ins_user_id="SYSTEM",
        )
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)

        logger.info(f"Created student: {student.student_id}")
        return StudentResponse.model_validate(student)

    async def update_student(
        self, student_id: str, data: StudentUpdate
    ) -> Optional[StudentResponse]:
        """Update student information."""
        result = await self.db.execute(
            select(Student).where(Student.student_id == student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)
        student.upd_user_id = "SYSTEM"

        await self.db.commit()
        await self.db.refresh(student)

        logger.info(f"Updated student: {student_id}")
        return StudentResponse.model_validate(student)

    # ==================== Enrollment & Grade Operations ====================

    async def get_enrollments(self, student_id: str) -> List[EnrollmentWithGradeResponse]:
        """Get all enrollments with grades for a student."""
        # Use YAML-based query for maintainability
        sql = get_query("student", "get_student_enrollments_with_grades")
        query = text(sql)

        result = await self.db.execute(query, {"student_id": student_id})
        rows = result.fetchall()

        return [
            EnrollmentWithGradeResponse(
                enrollment_id=row.enrollment_id,
                course_nm=row.course_nm,
                course_cd=row.course_cd,
                credits=row.credits,
                course_type=getattr(row, 'course_type', None),
                term_nm=row.term_nm,  # Updated: YAML query returns term_nm
                letter_grade=row.letter_grade,
                grade_point=float(row.grade_point) if row.grade_point else None,
                status_cd=row.status_cd,
            )
            for row in rows
        ]

    # ==================== Activity Operations ====================

    async def get_activities(self, student_id: str) -> List[ActivityResponse]:
        """Get all activities for a student from tb_activity table."""
        try:
            result = await self.db.execute(
                select(Activity)
                .where(Activity.student_id == student_id)
                .order_by(Activity.start_date.desc())
            )
            activities = result.scalars().all()

            return [
                ActivityResponse(
                    activity_id=a.activity_id,
                    student_id=a.student_id,
                    program_cd=a.program_cd,
                    activity_type=a.activity_type,
                    title=a.title,
                    description=a.description,
                    start_date=a.start_date,
                    end_date=a.end_date,
                    hours=float(a.hours) if a.hours else None,
                    achievement=a.achievement,
                    status=a.status or "completed",
                    verified=a.verified or "N",
                    ins_dt=a.ins_dt,
                )
                for a in activities
            ]
        except Exception as e:
            logger.warning(f"Failed to get activities for {student_id}: {e}")
            return []

    async def add_activity(
        self, student_id: str, data: ParticipationCreate
    ) -> ActivityResponse:
        """Add an activity for a student."""
        raise NotImplementedError("Use activity API directly")

    # ==================== Achievement Operations ====================

    async def get_achievements(self, student_id: str) -> List[AchievementResponse]:
        """Get all achievements for a student."""
        result = await self.db.execute(
            select(Achievement)
            .where(Achievement.student_id == student_id)
            .order_by(Achievement.issue_date.desc())
        )
        achievements = result.scalars().all()

        # Manual mapping due to column name differences
        return [
            AchievementResponse(
                achievement_id=a.achievement_id,
                student_id=a.student_id,
                achievement_type=a.achievement_type,
                achievement_nm=a.title,  # DB uses 'title'
                issuing_org=a.issuer,    # DB uses 'issuer'
                issue_date=a.issue_date,
                expiry_date=a.expire_date,  # DB uses 'expire_date'
                level=a.level,
                score=a.score,
                certificate_url=None,  # DB doesn't have this column
                verified_fg=a.verified,  # DB uses 'verified'
                ins_dt=a.ins_dt,
            )
            for a in achievements
        ]

    async def add_achievement(
        self, student_id: str, data: AchievementCreate
    ) -> AchievementResponse:
        """Add an achievement for a student."""
        achievement = Achievement(
            student_id=student_id,
            achievement_type=data.achievement_type,
            title=data.achievement_nm,  # DB uses 'title'
            issuer=data.issuing_org,    # DB uses 'issuer'
            issue_date=data.issue_date,
            expire_date=data.expiry_date,  # DB uses 'expire_date'
            level=data.level,
            score=data.score,
            # certificate_url not in DB
            ins_user_id="SYSTEM",
        )
        self.db.add(achievement)
        await self.db.commit()
        await self.db.refresh(achievement)

        logger.info(f"Added achievement {data.achievement_nm} for student {student_id}")

        return AchievementResponse(
            achievement_id=achievement.achievement_id,
            student_id=achievement.student_id,
            achievement_type=achievement.achievement_type,
            achievement_nm=achievement.title,
            issuing_org=achievement.issuer,
            issue_date=achievement.issue_date,
            expiry_date=achievement.expire_date,
            level=achievement.level,
            score=achievement.score,
            certificate_url=None,
            verified_fg=achievement.verified,
            ins_dt=achievement.ins_dt,
        )

    # ==================== Dashboard Operations ====================

    async def get_dashboard(self, student_id: str) -> Optional[DashboardSummary]:
        """Get complete dashboard data for a student."""
        student = await self.get_student(student_id)
        if not student:
            return None

        enrollments = await self.get_enrollments(student_id)
        activities = await self.get_activities(student_id)
        achievements = await self.get_achievements(student_id)

        return DashboardSummary(
            student=student,
            enrollments=enrollments,
            activities=activities,
            achievements=achievements,
        )

    # ==================== Department Operations ====================

    async def get_departments(self) -> List[DepartmentResponse]:
        """Get all active departments."""
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.college))
            .where(Department.use_fg == 'Y')
            .order_by(Department.department_nm)
        )
        departments = result.scalars().all()
        return [DepartmentResponse.model_validate(d) for d in departments]

    # Legacy compatibility methods
    async def get_courses(self, student_id: str) -> List[EnrollmentWithGradeResponse]:
        """Alias for get_enrollments."""
        return await self.get_enrollments(student_id)

    async def add_course(self, student_id: str, data) -> EnrollmentWithGradeResponse:
        """Legacy method - not fully implemented."""
        raise NotImplementedError("Use enrollment API directly")
