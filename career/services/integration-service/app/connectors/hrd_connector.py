"""
HRD-Net API Connector.

Handles connection to HRD-Net (Human Resources Development Service of Korea) API.
Uses database query when USE_MOCK_DATA is enabled (instead of JSON mock).
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

import httpx
from sqlalchemy import text

from ..config import settings
from ..database import get_db_session
from ..schemas.integration import HRDAlumniResponse

logger = logging.getLogger(__name__)


class HRDConnector:
    """Connector for HRD-Net API."""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.api_url = settings.HRD_API_URL
        self.api_key = settings.HRD_API_KEY
        self.use_mock = settings.USE_MOCK_DATA

    async def _get_alumni_from_db(
        self,
        department_id: Optional[str] = None,
        graduation_year: Optional[int] = None,
        limit: int = 50,
    ) -> List[HRDAlumniResponse]:
        """Get alumni data from database (tb_alumni_cohort)."""
        session = await get_db_session()
        try:
            # Build dynamic SQL based on filters to avoid NULL parameter issues with asyncpg
            where_clauses = ["s.status IN ('32', '41', '42', '51')"]
            params = {"limit": limit}

            if department_id:
                where_clauses.append("s.department_cd = :department_id")
                params["department_id"] = department_id

            if graduation_year:
                where_clauses.append("s.admission_year + 4 = :graduation_year")
                params["graduation_year"] = graduation_year

            where_sql = " AND ".join(where_clauses)

            sql = text(f"""
                SELECT
                    s.student_id,
                    s.department_cd as department_id,
                    s.admission_year + 4 as graduation_year,
                    s.career_goal,
                    COALESCE(gs.total_gpa, 0) as final_gpa,
                    COALESCE(gs.total_credits, 0) as total_credits,
                    ac.employment_rate,
                    ac.avg_salary,
                    ac.top_employers,
                    ac.top_roles,
                    ac.avg_competency_scores
                FROM tb_student s
                LEFT JOIN (
                    SELECT
                        student_id,
                        SUM(earned_credits) as total_credits,
                        ROUND(SUM(gpa * earned_credits) / NULLIF(SUM(earned_credits), 0), 2) as total_gpa
                    FROM tb_grade_summary
                    GROUP BY student_id
                ) gs ON s.student_id = gs.student_id
                LEFT JOIN tb_alumni_cohort ac ON s.department_cd = ac.department_cd
                    AND s.admission_year + 4 = ac.graduation_year
                WHERE {where_sql}
                ORDER BY s.admission_year DESC
                LIMIT :limit
            """)

            result = await session.execute(sql, params)
            rows = result.fetchall()

            alumni_list = []
            for row in rows:
                # Generate employment info based on cohort statistics
                is_employed = True if row.employment_rate and float(row.employment_rate) > 0.5 else False
                company_name = None
                job_title = None
                job_category = None

                if is_employed and row.top_employers:
                    employers = row.top_employers if isinstance(row.top_employers, list) else []
                    if employers:
                        company_name = employers[0] if len(employers) > 0 else None

                if row.top_roles:
                    roles = row.top_roles if isinstance(row.top_roles, list) else []
                    if roles:
                        job_title = roles[0] if len(roles) > 0 else None
                        job_category = "IT/개발" if any(r in (job_title or "") for r in ["개발", "엔지니어", "프로그래머"]) else "일반"

                # Get certifications and activities from student's achievements
                certifications = []
                activities = []

                # Get competency scores
                competency_scores = {}
                if row.avg_competency_scores:
                    competency_scores = row.avg_competency_scores if isinstance(row.avg_competency_scores, dict) else {}

                alumni_list.append(HRDAlumniResponse(
                    alumni_id=f"ALM-{row.student_id}",
                    department_id=row.department_id,
                    graduation_year=row.graduation_year,
                    is_employed=is_employed,
                    employment_date=datetime(row.graduation_year, 3, 1) if is_employed else None,
                    company_name=company_name,
                    job_category=job_category,
                    job_title=job_title,
                    final_gpa=float(row.final_gpa) if row.final_gpa else None,
                    total_credits=int(row.total_credits) if row.total_credits else None,
                    certifications=certifications,
                    activities=activities,
                    final_competency_scores=competency_scores
                ))

            return alumni_list

        except Exception as e:
            logger.error(f"Failed to get alumni from DB: {e}")
            return []
        finally:
            await session.close()

    async def get_alumni(
        self,
        department_id: Optional[str] = None,
        graduation_year: Optional[int] = None,
        limit: int = 50,
    ) -> List[HRDAlumniResponse]:
        """Get alumni employment data."""

        cache_key = f"hrd_alumni:{department_id or 'all'}:{graduation_year or 'all'}"

        # Check cache first
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return [HRDAlumniResponse(**a) for a in data]

        if self.use_mock:
            # Use database query instead of JSON mock
            results = await self._get_alumni_from_db(department_id, graduation_year, limit)

            # Cache results
            if self.redis and results:
                await self.redis.set(
                    cache_key,
                    json.dumps([r.model_dump(mode="json") for r in results]),
                    ex=settings.CACHE_TTL_SECONDS
                )

            return results

        # Real API call (for future integration)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"limit": limit}
                if department_id:
                    params["department_id"] = department_id
                if graduation_year:
                    params["graduation_year"] = graduation_year

                response = await client.get(
                    f"{self.api_url}/alumni",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    results = [
                        HRDAlumniResponse(**a)
                        for a in response.json().get("alumni", [])
                    ]

                    if self.redis and results:
                        await self.redis.set(
                            cache_key,
                            json.dumps([r.model_dump(mode="json") for r in results]),
                            ex=settings.CACHE_TTL_SECONDS
                        )

                    return results
        except Exception as e:
            logger.error(f"Failed to fetch alumni from HRD-Net: {e}")

        return []

    async def get_employment_statistics(
        self,
        department_id: str,
        graduation_year: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get employment statistics for a department."""

        if self.use_mock:
            # Query from tb_alumni_cohort
            session = await get_db_session()
            try:
                if graduation_year:
                    sql = text("""
                        SELECT
                            cohort_size,
                            employment_rate,
                            avg_salary,
                            avg_gpa,
                            top_employers,
                            top_roles,
                            avg_competency_scores
                        FROM tb_alumni_cohort
                        WHERE department_cd = :department_id
                          AND graduation_year = :graduation_year
                    """)
                    result = await session.execute(sql, {
                        "department_id": department_id,
                        "graduation_year": graduation_year
                    })
                    row = result.fetchone()

                    if row:
                        return {
                            "cohort_size": row.cohort_size,
                            "employment_rate": float(row.employment_rate) if row.employment_rate else None,
                            "avg_salary": float(row.avg_salary) if row.avg_salary else None,
                            "avg_gpa": float(row.avg_gpa) if row.avg_gpa else None,
                            "top_employers": row.top_employers or [],
                            "top_roles": row.top_roles or [],
                            "avg_competency_scores": row.avg_competency_scores or {}
                        }
                else:
                    # Return all years
                    sql = text("""
                        SELECT
                            graduation_year,
                            cohort_size,
                            employment_rate,
                            avg_salary,
                            avg_gpa,
                            top_employers,
                            top_roles,
                            avg_competency_scores
                        FROM tb_alumni_cohort
                        WHERE department_cd = :department_id
                        ORDER BY graduation_year DESC
                    """)
                    result = await session.execute(sql, {"department_id": department_id})
                    rows = result.fetchall()

                    stats = {}
                    for row in rows:
                        stats[str(row.graduation_year)] = {
                            "cohort_size": row.cohort_size,
                            "employment_rate": float(row.employment_rate) if row.employment_rate else None,
                            "avg_salary": float(row.avg_salary) if row.avg_salary else None,
                            "avg_gpa": float(row.avg_gpa) if row.avg_gpa else None,
                            "top_employers": row.top_employers or [],
                            "top_roles": row.top_roles or [],
                            "avg_competency_scores": row.avg_competency_scores or {}
                        }
                    return stats

            except Exception as e:
                logger.error(f"Failed to get employment statistics from DB: {e}")
                return None
            finally:
                await session.close()

        # Real API call (for future integration)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"department_id": department_id}
                if graduation_year:
                    params["graduation_year"] = graduation_year

                response = await client.get(
                    f"{self.api_url}/statistics",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch statistics from HRD-Net: {e}")

        return None

    async def get_alumni_by_id(self, alumni_id: str) -> Optional[HRDAlumniResponse]:
        """Get specific alumni by ID."""

        if self.use_mock:
            # Extract student_id from alumni_id (format: ALM-{student_id})
            student_id = alumni_id.replace("ALM-", "") if alumni_id.startswith("ALM-") else alumni_id

            session = await get_db_session()
            try:
                sql = text("""
                    SELECT
                        s.student_id,
                        s.department_cd as department_id,
                        s.admission_year + 4 as graduation_year,
                        s.career_goal,
                        COALESCE(gs.total_gpa, 0) as final_gpa,
                        COALESCE(gs.total_credits, 0) as total_credits,
                        ac.employment_rate,
                        ac.avg_salary,
                        ac.top_employers,
                        ac.top_roles,
                        ac.avg_competency_scores
                    FROM tb_student s
                    LEFT JOIN (
                        SELECT
                            student_id,
                            SUM(earned_credits) as total_credits,
                            ROUND(SUM(gpa * earned_credits) / NULLIF(SUM(earned_credits), 0), 2) as total_gpa
                        FROM tb_grade_summary
                        GROUP BY student_id
                    ) gs ON s.student_id = gs.student_id
                    LEFT JOIN tb_alumni_cohort ac ON s.department_cd = ac.department_cd
                        AND s.admission_year + 4 = ac.graduation_year
                    WHERE s.student_id = :student_id
                """)

                result = await session.execute(sql, {"student_id": student_id})
                row = result.fetchone()

                if not row:
                    return None

                is_employed = True if row.employment_rate and float(row.employment_rate) > 0.5 else False
                company_name = None
                job_title = None

                if is_employed and row.top_employers:
                    employers = row.top_employers if isinstance(row.top_employers, list) else []
                    if employers:
                        company_name = employers[0]

                if row.top_roles:
                    roles = row.top_roles if isinstance(row.top_roles, list) else []
                    if roles:
                        job_title = roles[0]

                return HRDAlumniResponse(
                    alumni_id=f"ALM-{row.student_id}",
                    department_id=row.department_id,
                    graduation_year=row.graduation_year,
                    is_employed=is_employed,
                    employment_date=datetime(row.graduation_year, 3, 1) if is_employed else None,
                    company_name=company_name,
                    job_category="IT/개발" if row.career_goal and "개발" in row.career_goal else None,
                    job_title=job_title,
                    final_gpa=float(row.final_gpa) if row.final_gpa else None,
                    total_credits=int(row.total_credits) if row.total_credits else None,
                    certifications=[],
                    activities=[],
                    final_competency_scores=row.avg_competency_scores or {}
                )

            except Exception as e:
                logger.error(f"Failed to get alumni by ID from DB: {e}")
                return None
            finally:
                await session.close()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/alumni/{alumni_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    return HRDAlumniResponse(**response.json())
        except Exception as e:
            logger.error(f"Failed to fetch alumni: {e}")

        return None
