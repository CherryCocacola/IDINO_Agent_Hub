"""
University API Connector.

Handles connection to university academic information system.
Uses database query when USE_MOCK_DATA is enabled (instead of JSON mock).
"""
import json
import logging
from typing import List, Optional, Dict, Any

import httpx
from sqlalchemy import text

from ..config import settings
from ..database import get_db_session
from ..schemas.integration import UniversityStudentResponse, UniversityCourseResponse

logger = logging.getLogger(__name__)


class UniversityConnector:
    """Connector for University academic system."""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.api_url = settings.UNIVERSITY_API_URL
        self.api_key = settings.UNIVERSITY_API_KEY
        self.use_mock = settings.USE_MOCK_DATA

    async def _get_student_from_db(self, student_id: str) -> Optional[UniversityStudentResponse]:
        """Get student data from database."""
        session = await get_db_session()
        try:
            # Get student basic info
            student_sql = text("""
                SELECT
                    s.student_id,
                    s.student_nm as name,
                    s.department_cd as department_id,
                    COALESCE(d.department_nm, '학과미지정') as department_name,
                    s.current_grade as grade,
                    CASE
                        WHEN s.status IN ('11', '21') THEN '재학'
                        WHEN s.status IN ('22', '31', '32') THEN '휴학'
                        WHEN s.status IN ('41', '42', '51') THEN '졸업'
                        ELSE '재학'
                    END as status,
                    s.admission_year,
                    s.career_goal as major
                FROM tb_student s
                LEFT JOIN tb_department d ON s.department_cd = d.department_cd
                WHERE s.student_id = :student_id
            """)

            result = await session.execute(student_sql, {"student_id": student_id})
            student_row = result.fetchone()

            if not student_row:
                return None

            # Get GPA and total credits from tb_grade_summary
            gpa_sql = text("""
                SELECT
                    COALESCE(SUM(gpa * earned_credits), 0) as weighted_sum,
                    COALESCE(SUM(earned_credits), 0) as total_credits
                FROM tb_grade_summary
                WHERE student_id = :student_id
                  AND gpa IS NOT NULL
                  AND earned_credits > 0
            """)

            gpa_result = await session.execute(gpa_sql, {"student_id": student_id})
            gpa_row = gpa_result.fetchone()

            total_credits = int(gpa_row.total_credits) if gpa_row and gpa_row.total_credits else 0
            gpa = round(float(gpa_row.weighted_sum) / total_credits, 2) if total_credits > 0 else 0.0

            # Get courses with grades
            courses_sql = text("""
                SELECT
                    g.course_cd as course_code,
                    COALESCE(c.course_nm, g.course_cd) as course_name,
                    COALESCE(c.department_cd, :dept_cd) as department_id,
                    COALESCE(c.credits, g.credits_earned) as credits,
                    COALESCE(c.course_type, '일반') as course_type,
                    g.term_cd as semester,
                    g.grade_letter as grade,
                    g.grade_point
                FROM tb_grade g
                LEFT JOIN tb_course c ON g.course_cd = c.course_cd
                WHERE g.student_id = :student_id
                ORDER BY g.term_cd DESC
            """)

            courses_result = await session.execute(
                courses_sql,
                {"student_id": student_id, "dept_cd": student_row.department_id}
            )
            courses_rows = courses_result.fetchall()

            courses = []
            for row in courses_rows:
                courses.append(UniversityCourseResponse(
                    course_code=row.course_code,
                    course_name=row.course_name,
                    department_id=row.department_id,
                    credits=row.credits or 3,
                    course_type=row.course_type,
                    semester=row.semester,
                    grade=row.grade,
                    grade_point=float(row.grade_point) if row.grade_point else None,
                    competency_mappings={}
                ))

            # Calculate expected graduation
            admission_year = student_row.admission_year
            expected_graduation = f"{admission_year + 4}-02"

            return UniversityStudentResponse(
                student_id=student_row.student_id,
                name=student_row.name,
                department_id=student_row.department_id,
                department_name=student_row.department_name,
                major=student_row.major,
                grade=student_row.grade or 1,
                status=student_row.status,
                total_credits=total_credits,
                gpa=gpa,
                semester_gpa=None,
                courses=courses,
                admission_year=admission_year,
                expected_graduation=expected_graduation
            )

        except Exception as e:
            logger.error(f"Failed to get student from DB: {e}")
            return None
        finally:
            await session.close()

    async def get_student(self, student_id: str) -> Optional[UniversityStudentResponse]:
        """Get student academic information."""

        # Check cache first
        if self.redis:
            cached = await self.redis.get(f"university_student:{student_id}")
            if cached:
                return UniversityStudentResponse.model_validate_json(cached)

        if self.use_mock:
            # Use database query instead of JSON mock
            result = await self._get_student_from_db(student_id)

            if result and self.redis:
                await self.redis.set(
                    f"university_student:{student_id}",
                    result.model_dump_json(),
                    ex=settings.CACHE_TTL_SECONDS
                )

            return result

        # Real API call (for future integration)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/students/{student_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    result = UniversityStudentResponse(**response.json())

                    if self.redis:
                        await self.redis.set(
                            f"university_student:{student_id}",
                            result.model_dump_json(),
                            ex=settings.CACHE_TTL_SECONDS
                        )

                    return result
        except Exception as e:
            logger.error(f"Failed to fetch student from university: {e}")

        return None

    async def get_student_courses(
        self,
        student_id: str,
        semester: Optional[str] = None,
    ) -> List[UniversityCourseResponse]:
        """Get student course records."""

        student = await self.get_student(student_id)
        if not student:
            return []

        courses = student.courses
        if semester:
            courses = [c for c in courses if c.semester == semester]

        return courses

    async def get_departments(self) -> List[Dict[str, str]]:
        """Get list of departments."""
        if self.use_mock:
            # Query from database
            session = await get_db_session()
            try:
                sql = text("""
                    SELECT department_cd as id, department_nm as name
                    FROM tb_department
                    WHERE use_fg = 'Y'
                    ORDER BY department_nm
                """)
                result = await session.execute(sql)
                rows = result.fetchall()
                return [{"id": row.id, "name": row.name} for row in rows]
            except Exception as e:
                logger.error(f"Failed to get departments from DB: {e}")
                return []
            finally:
                await session.close()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/departments",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    return response.json().get("departments", [])
        except Exception as e:
            logger.error(f"Failed to fetch departments: {e}")

        return []

    async def sync_student_data(self, student_id: str) -> bool:
        """Sync student data from university system."""
        # In mock mode, just return success
        if self.use_mock:
            logger.info(f"Mock sync for student {student_id}")
            return True

        # Real implementation would pull fresh data from university
        try:
            student = await self.get_student(student_id)
            if student and self.redis:
                # Invalidate cache to force refresh
                await self.redis.delete(f"university_student:{student_id}")
                # Re-fetch and cache
                await self.get_student(student_id)
                return True
        except Exception as e:
            logger.error(f"Failed to sync student data: {e}")

        return False
