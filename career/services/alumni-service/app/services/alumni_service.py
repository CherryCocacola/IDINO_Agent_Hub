"""
Alumni service business logic.
Matches database schema: idino_career
"""
import logging
from typing import List, Optional, Dict, Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import AlumniCohort, SuccessPattern
from ..schemas.alumni import (
    AlumniCohortResponse,
    SuccessPatternResponse,
    AlumniBenchmarkResponse,
    StudentComparisonResponse,
    CompetencyComparison,
)

logger = logging.getLogger(__name__)


class AlumniService:
    """Service for alumni-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Cohort Operations ====================

    async def get_cohorts(
        self,
        department_cd: Optional[str] = None,
    ) -> List[AlumniCohortResponse]:
        """Get all alumni cohorts, optionally filtered."""
        query = select(AlumniCohort)

        if department_cd:
            query = query.where(AlumniCohort.department_cd == department_cd)

        query = query.order_by(AlumniCohort.graduation_year.desc())

        result = await self.db.execute(query)
        cohorts = result.scalars().all()

        return [
            AlumniCohortResponse(
                cohort_id=c.cohort_id,
                department_cd=c.department_cd,
                graduation_year=c.graduation_year,
                cohort_size=c.cohort_size or 0,
                avg_gpa=float(c.avg_gpa) if c.avg_gpa else None,
                employment_rate=float(c.employment_rate) if c.employment_rate else None,
                avg_salary=float(c.avg_salary) if c.avg_salary else None,
                top_employers=c.top_employers,
                top_roles=c.top_roles,
                avg_competency_scores=c.avg_competency_scores or {},
            )
            for c in cohorts
        ]

    # ==================== Benchmark Operations ====================

    async def get_benchmark(
        self,
        department_cd: str,
        role_cd: Optional[str] = None,
    ) -> AlumniBenchmarkResponse:
        """Get alumni benchmark for a department."""

        # Get cohorts
        query = select(AlumniCohort).where(
            AlumniCohort.department_cd == department_cd
        )

        result = await self.db.execute(query)
        cohorts = result.scalars().all()

        # Get patterns
        patterns_query = select(SuccessPattern).where(
            SuccessPattern.department_cd == department_cd
        ).order_by(SuccessPattern.success_rate.desc()).limit(5)

        if role_cd:
            patterns_query = patterns_query.where(SuccessPattern.role_cd == role_cd)

        patterns_result = await self.db.execute(patterns_query)
        patterns = patterns_result.scalars().all()

        # Calculate average employment rate
        employment_rates = [
            float(c.employment_rate) for c in cohorts if c.employment_rate
        ]
        avg_employment_rate = (
            sum(employment_rates) / len(employment_rates) if employment_rates else None
        )

        return AlumniBenchmarkResponse(
            department_cd=department_cd,
            total_cohorts=len(cohorts),
            avg_employment_rate=round(avg_employment_rate, 2) if avg_employment_rate else None,
            cohorts=[
                AlumniCohortResponse(
                    cohort_id=c.cohort_id,
                    department_cd=c.department_cd,
                    graduation_year=c.graduation_year,
                    cohort_size=c.cohort_size or 0,
                    avg_gpa=float(c.avg_gpa) if c.avg_gpa else None,
                    employment_rate=float(c.employment_rate) if c.employment_rate else None,
                    avg_salary=float(c.avg_salary) if c.avg_salary else None,
                    top_employers=c.top_employers,
                    top_roles=c.top_roles,
                    avg_competency_scores=c.avg_competency_scores or {},
                )
                for c in cohorts
            ],
            success_patterns=[
                SuccessPatternResponse(
                    pattern_id=p.pattern_id,
                    pattern_nm=p.pattern_nm,
                    pattern_type=p.pattern_type,
                    department_cd=p.department_cd,
                    role_cd=p.role_cd,
                    description=p.description,
                    typical_gpa_range=p.typical_gpa_range,
                    key_courses=p.key_courses,
                    key_activities=p.key_activities,
                    key_skills=p.key_skills,
                    timeline=p.timeline,
                    success_rate=float(p.success_rate) if p.success_rate else None,
                    sample_size=p.sample_size or 0,
                )
                for p in patterns
            ],
        )

    # ==================== Pattern Operations ====================

    async def get_patterns(
        self,
        department_cd: str,
        role_cd: Optional[str] = None,
        limit: int = 10,
    ) -> List[SuccessPatternResponse]:
        """Get success patterns for a department.
        Falls back to patterns matching department category if exact match not found.
        """

        query = (
            select(SuccessPattern)
            .where(SuccessPattern.department_cd == department_cd)
            .order_by(SuccessPattern.success_rate.desc())
            .limit(limit)
        )

        if role_cd:
            query = query.where(SuccessPattern.role_cd == role_cd)

        result = await self.db.execute(query)
        patterns = result.scalars().all()

        # Fallback: if no patterns found for exact department, try broader match
        if not patterns and not role_cd:
            try:
                from sqlalchemy import text
                # Get department name for category matching
                dept_result = await self.db.execute(
                    text("SELECT department_nm FROM tb_department WHERE department_cd = :dc"),
                    {"dc": department_cd}
                )
                dept_row = dept_result.fetchone()
                if dept_row and dept_row.department_nm:
                    dept_nm = dept_row.department_nm
                    # Try to find patterns from similar departments
                    similar_result = await self.db.execute(
                        text("""
                            SELECT sp.* FROM tb_success_pattern sp
                            JOIN tb_department d ON sp.department_cd = d.department_cd
                            WHERE d.department_nm ~ :pattern
                            ORDER BY sp.success_rate DESC
                            LIMIT :lim
                        """),
                        {
                            "pattern": dept_nm[:2],  # Use first 2 chars for broader matching
                            "lim": limit,
                        }
                    )
                    from sqlalchemy import inspect
                    similar_rows = similar_result.fetchall()
                    if similar_rows:
                        # Convert to SuccessPattern-like objects
                        patterns = similar_rows
            except Exception as e:
                logger.warning(f"Fallback pattern search failed: {e}")

        return [
            SuccessPatternResponse(
                pattern_id=p.pattern_id,
                pattern_nm=p.pattern_nm,
                pattern_type=p.pattern_type,
                department_cd=p.department_cd,
                role_cd=p.role_cd,
                description=p.description,
                typical_gpa_range=p.typical_gpa_range,
                key_courses=p.key_courses,
                key_activities=p.key_activities,
                key_skills=p.key_skills,
                timeline=p.timeline,
                success_rate=float(p.success_rate) if p.success_rate else None,
                sample_size=p.sample_size or 0,
            )
            for p in patterns
        ]

    # ==================== Comparison Operations ====================

    async def compare_with_student(
        self,
        student_id: str,
        target_role_cd: Optional[str] = None,
    ) -> StudentComparisonResponse:
        """
        Compare student with alumni benchmark.
        Fetches student data from other services.
        """

        # Fetch student data from student-service
        student_data = await self._fetch_student_data(student_id)
        department_cd = student_data.get("department_cd", "")

        # Fetch competency data from competency-service
        competency_data = await self._fetch_competency_data(student_id)

        # Get alumni benchmark
        benchmark = await self.get_benchmark(
            department_cd=department_cd,
            role_cd=target_role_cd,
        )

        # Build competency comparisons
        student_competencies = competency_data.get("competencies", {})
        alumni_competencies = self._aggregate_competencies(benchmark.cohorts)

        # Fetch competency names from database
        competency_names = await self._fetch_competency_names(
            list(alumni_competencies.keys()) + list(student_competencies.keys())
        )

        comparisons = []
        for comp_cd, alumni_score in alumni_competencies.items():
            student_score = student_competencies.get(comp_cd, 0)
            gap = student_score - alumni_score

            status = "at"
            if gap > 5:
                status = "above"
            elif gap < -5:
                status = "below"

            comparisons.append(CompetencyComparison(
                competency_cd=comp_cd,
                competency_nm=competency_names.get(comp_cd, comp_cd),
                student_score=round(student_score, 2),
                alumni_avg_score=round(alumni_score, 2),
                gap=round(gap, 2),
                status=status,
            ))

        # Calculate overall readiness
        if comparisons:
            positive_gaps = sum(1 for c in comparisons if c.gap >= 0)
            overall_readiness = (positive_gaps / len(comparisons)) * 100
        else:
            overall_readiness = 0

        # Find improvement areas
        improvement_areas = [c.competency_nm for c in comparisons if c.gap < -10]

        # Get best matching pattern
        best_pattern = benchmark.success_patterns[0] if benchmark.success_patterns else None

        # Get average GPA from cohorts
        alumni_avg_gpa = None
        if benchmark.cohorts:
            gpas = [c.avg_gpa for c in benchmark.cohorts if c.avg_gpa]
            if gpas:
                alumni_avg_gpa = sum(gpas) / len(gpas)

        # Aggregate avg_extras from cohorts
        alumni_avg_credits, alumni_avg_certs, alumni_avg_acts = await self._aggregate_avg_extras(department_cd)

        return StudentComparisonResponse(
            student_id=student_id,
            department_cd=department_cd,
            target_role_cd=target_role_cd,
            student_gpa=student_data.get("gpa"),
            student_competencies=student_competencies,
            alumni_avg_gpa_range=f"{alumni_avg_gpa:.2f}" if alumni_avg_gpa else None,
            alumni_competencies=alumni_competencies,
            competency_comparisons=comparisons,
            overall_readiness_score=round(overall_readiness, 1),
            improvement_areas=improvement_areas,
            student_credits=student_data.get("completed_credits"),
            student_certifications=student_data.get("achievement_count"),
            student_activities=student_data.get("activity_count"),
            alumni_avg_credits=alumni_avg_credits,
            alumni_avg_certifications=alumni_avg_certs,
            alumni_avg_activities=alumni_avg_acts,
            best_matching_pattern=best_pattern,
        )

    def _aggregate_competencies(
        self, cohorts: List[AlumniCohortResponse]
    ) -> Dict[str, float]:
        """Aggregate competency scores from cohorts."""
        aggregated: Dict[str, List[float]] = {}

        for cohort in cohorts:
            if cohort.avg_competency_scores:
                for comp_cd, score in cohort.avg_competency_scores.items():
                    if comp_cd not in aggregated:
                        aggregated[comp_cd] = []
                    if isinstance(score, (int, float)):
                        aggregated[comp_cd].append(float(score))

        return {
            comp_cd: sum(scores) / len(scores)
            for comp_cd, scores in aggregated.items()
            if scores
        }

    async def _aggregate_avg_extras(
        self, department_cd: Optional[str]
    ) -> tuple:
        """Aggregate avg_extras (credits, certifications, activities) from cohorts."""
        if not department_cd:
            return None, None, None
        try:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT
                        ROUND(AVG((avg_extras->>'avg_credits')::numeric))::int as avg_credits,
                        ROUND(AVG((avg_extras->>'avg_certifications')::numeric))::int as avg_certs,
                        ROUND(AVG((avg_extras->>'avg_activities')::numeric))::int as avg_acts
                    FROM tb_alumni_cohort
                    WHERE department_cd = :dc
                      AND avg_extras IS NOT NULL
                      AND avg_extras != '{}'::jsonb
                """),
                {"dc": department_cd}
            )
            row = result.fetchone()
            if row and row.avg_credits is not None:
                return row.avg_credits, row.avg_certs, row.avg_acts
        except Exception as e:
            logger.warning(f"Failed to aggregate avg_extras: {e}")
        return None, None, None

    async def _fetch_competency_names(
        self, competency_cds: List[str]
    ) -> Dict[str, str]:
        """Fetch competency names from database."""
        if not competency_cds:
            return {}

        try:
            from sqlalchemy import text
            # Remove duplicates
            unique_cds = list(set(competency_cds))
            placeholders = ", ".join([f":cd{i}" for i in range(len(unique_cds))])
            params = {f"cd{i}": cd for i, cd in enumerate(unique_cds)}

            result = await self.db.execute(
                text(f"""
                    SELECT competency_cd, competency_nm
                    FROM tb_competency
                    WHERE competency_cd IN ({placeholders})
                """),
                params
            )
            rows = result.fetchall()
            return {row.competency_cd: row.competency_nm for row in rows}
        except Exception as e:
            logger.warning(f"Failed to fetch competency names: {e}")
            return {}

    async def _fetch_student_data(self, student_id: str) -> Dict[str, Any]:
        """Fetch student data from student-service or directly from database."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.STUDENT_SERVICE_URL}/students/{student_id}"
                )
                if response.status_code == 200:
                    data = response.json()
                    summary = data.get("summary") or {}
                    return {
                        "student_id": data.get("student_id"),
                        "department_cd": data.get("department_cd"),
                        "gpa": data.get("gpa"),
                        "completed_credits": summary.get("completed_credits") or data.get("total_credits", 0),
                        "achievement_count": data.get("achievement_count", 0),
                        "activity_count": data.get("activity_count", 0),
                    }
        except Exception as e:
            logger.warning(f"Student service unavailable, falling back to DB: {e}")

        # Fallback: Query database directly (with GPA from tb_grade_summary)
        try:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT s.student_id, s.department_cd, gs.gpa,
                           gs.completed_credits,
                           (SELECT COUNT(*) FROM tb_achievement a WHERE a.student_id = s.student_id) as achievement_count,
                           (SELECT COUNT(*) FROM tb_activity act WHERE act.student_id = s.student_id) as activity_count
                    FROM tb_student s
                    LEFT JOIN tb_grade_summary gs ON s.student_id = gs.student_id
                    WHERE s.student_id = :student_id
                    ORDER BY gs.term_cd DESC NULLS LAST
                    LIMIT 1
                """),
                {"student_id": student_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "student_id": row.student_id,
                    "department_cd": row.department_cd,
                    "gpa": float(row.gpa) if row.gpa else None,
                    "completed_credits": int(row.completed_credits) if row.completed_credits else 0,
                    "achievement_count": int(row.achievement_count) if row.achievement_count else 0,
                    "activity_count": int(row.activity_count) if row.activity_count else 0,
                }
        except Exception as db_error:
            logger.error(f"Failed to fetch student from DB: {db_error}")

        # Return empty data if both service and DB fail
        return {
            "student_id": student_id,
            "department_cd": None,
            "gpa": None,
            "completed_credits": 0,
            "achievement_count": 0,
            "activity_count": 0,
        }

    async def _fetch_competency_data(self, student_id: str) -> Dict[str, Any]:
        """Fetch competency data from competency-service or directly from database."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.COMPETENCY_SERVICE_URL}/competency/{student_id}/scores"
                )
                if response.status_code == 200:
                    scores = response.json()
                    return {
                        "competencies": {
                            s["competency_cd"]: s["current_score"]
                            for s in scores
                        }
                    }
        except Exception as e:
            logger.warning(f"Competency service unavailable, falling back to DB: {e}")

        # Fallback: Query database directly
        try:
            from sqlalchemy import text
            result = await self.db.execute(
                text("""
                    SELECT competency_cd, current_score
                    FROM tb_student_competency
                    WHERE student_id = :student_id
                """),
                {"student_id": student_id}
            )
            rows = result.fetchall()
            if rows:
                return {
                    "competencies": {
                        row.competency_cd: float(row.current_score) if row.current_score else 0
                        for row in rows
                    }
                }
        except Exception as db_error:
            logger.error(f"Failed to fetch competency from DB: {db_error}")

        # Return empty data if both service and DB fail
        return {"competencies": {}}
