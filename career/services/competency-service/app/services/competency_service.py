"""
Competency service business logic.
Matches database schema: idino_career
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import httpx

from ..config import settings
from ..models import Competency, StudentCompetency
from ..schemas.competency import (
    CompetencyResponse,
    StudentCompetencyResponse,
    StudentCompetencyWithNameResponse,
    CompetencyReportResponse,
)

logger = logging.getLogger(__name__)


class CompetencyService:
    """Competency service for handling competency-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Competency Definition Operations ====================

    async def get_competencies(self) -> List[CompetencyResponse]:
        """Get all competency definitions."""
        result = await self.db.execute(
            select(Competency)
            .order_by(Competency.competency_cd)
        )
        competencies = result.scalars().all()

        return [
            CompetencyResponse(
                competency_cd=c.competency_cd,
                competency_nm=c.competency_nm,
                competency_nm_en=c.competency_nm_en,
                definition=c.definition,
                category=c.category,
                weight=float(c.weight) if c.weight else 0,
                max_score=c.max_score or 100,
            )
            for c in competencies
        ]

    # ==================== Student Competency Operations ====================

    async def get_student_competencies(
        self, student_id: str
    ) -> List[StudentCompetencyWithNameResponse]:
        """Get all competency scores for a student with competency names.
        Only returns competencies where use_fg='Y' (active).
        Includes per-competency percentile within the same department.
        """
        result = await self.db.execute(
            select(StudentCompetency)
            .options(selectinload(StudentCompetency.competency))
            .where(StudentCompetency.student_id == student_id)
            .order_by(StudentCompetency.competency_cd)
        )
        student_comps = result.scalars().all()

        # Calculate per-competency percentiles
        percentiles = await self._calculate_competency_percentiles(student_id)

        responses = []
        for sc in student_comps:
            # Skip competencies where use_fg != 'Y'
            if sc.competency and getattr(sc.competency, 'use_fg', 'Y') != 'Y':
                continue
            current = float(sc.current_score) if sc.current_score else 0
            target = float(sc.target_score) if sc.target_score else 85
            gap = current - target  # Negative means below target

            responses.append(
                StudentCompetencyWithNameResponse(
                    student_competency_id=sc.student_competency_id,
                    student_id=sc.student_id,
                    competency_cd=sc.competency_cd,
                    competency_nm=sc.competency.competency_nm if sc.competency else sc.competency_cd,
                    competency_nm_en=sc.competency.competency_nm_en if sc.competency else None,
                    definition=sc.competency.definition if sc.competency else None,
                    current_score=current,
                    target_score=target,
                    gap_score=round(gap, 2),
                    status=sc.status or "improve",
                    trend=sc.trend,
                    percentile=percentiles.get(sc.competency_cd),
                )
            )
        return responses

    # ==================== Report Operations ====================

    async def get_report(self, student_id: str) -> Optional[CompetencyReportResponse]:
        """Get comprehensive competency report for a student."""
        competencies = await self.get_student_competencies(student_id)

        if not competencies:
            logger.warning(f"No competency data found for student {student_id}")
            return None

        # Calculate overall score as SUM of all competency scores
        overall_score = sum(c.current_score for c in competencies)

        # Calculate department-based percentile rank (using SUM)
        percentile_rank = await self._calculate_percentile(student_id, overall_score)

        # Generate improvement suggestions (GPT with template fallback)
        suggestions = await self._generate_suggestions(student_id, competencies)

        return CompetencyReportResponse(
            student_id=student_id,
            report_date=datetime.utcnow(),
            overall_score=round(overall_score, 2),
            percentile_rank=percentile_rank,
            competencies=competencies,
            improvement_suggestions=suggestions,
        )

    async def _calculate_percentile(self, student_id: str, my_total: float) -> Optional[int]:
        """Calculate percentile rank within the same department using SUM of scores."""
        try:
            percentile_sql = text("""
                WITH dept_scores AS (
                    SELECT sc.student_id, SUM(sc.current_score) as total
                    FROM tb_student_competency sc
                    JOIN tb_student s ON sc.student_id = s.student_id
                    JOIN tb_competency c ON sc.competency_cd = c.competency_cd AND c.use_fg = 'Y'
                    WHERE s.department_cd = (
                        SELECT department_cd FROM tb_student WHERE student_id = :student_id
                    )
                    GROUP BY sc.student_id
                )
                SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE total < :my_total) / NULLIF(COUNT(*), 0)) as pct
                FROM dept_scores
            """)
            result = await self.db.execute(percentile_sql, {
                "student_id": student_id,
                "my_total": my_total,
            })
            row = result.fetchone()
            if row and row.pct is not None:
                return int(row.pct)
        except Exception as e:
            logger.warning(f"Failed to calculate percentile for {student_id}: {e}")
        return None

    async def _calculate_competency_percentiles(self, student_id: str) -> dict:
        """Calculate per-competency percentile ranks within the same department.
        Returns dict of {competency_cd: percentile_int}.
        """
        try:
            sql = text("""
                WITH ranked AS (
                    SELECT
                        sc.student_id,
                        sc.competency_cd,
                        ROUND(100.0 * PERCENT_RANK() OVER (
                            PARTITION BY s.department_cd, sc.competency_cd
                            ORDER BY sc.current_score
                        )) AS pct
                    FROM tb_student_competency sc
                    JOIN tb_student s ON sc.student_id = s.student_id
                    JOIN tb_competency c ON sc.competency_cd = c.competency_cd AND c.use_fg = 'Y'
                    WHERE s.department_cd = (
                        SELECT department_cd FROM tb_student WHERE student_id = :student_id
                    )
                )
                SELECT competency_cd, pct
                FROM ranked
                WHERE student_id = :student_id
            """)
            result = await self.db.execute(sql, {"student_id": student_id})
            rows = result.fetchall()
            return {row.competency_cd: int(row.pct) for row in rows if row.pct is not None}
        except Exception as e:
            logger.warning(f"Failed to calculate competency percentiles for {student_id}: {e}")
            return {}

    async def _generate_suggestions(
        self, student_id: str, competencies: List[StudentCompetencyWithNameResponse]
    ) -> List[str]:
        """Generate improvement suggestions via ai-service GPT, with template fallback."""
        # 1차: ai-service GPT 호출 시도
        try:
            payload = {
                "student_id": student_id,
                "competencies": [
                    {
                        "name": c.competency_nm,
                        "score": c.current_score,
                        "status": c.status,
                        "gap": c.gap_score,
                    }
                    for c in competencies
                ],
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.AI_SERVICE_URL}/ai/analyze", json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    suggestions = data.get("improvement_suggestions", [])
                    if suggestions:
                        return suggestions[:3]
        except Exception as e:
            logger.warning(f"AI suggestion failed for {student_id}: {e}")

        # 2차: 폴백 - 기존 템플릿 로직
        return self._generate_template_suggestions(competencies)

    def _generate_template_suggestions(
        self, competencies: List[StudentCompetencyWithNameResponse]
    ) -> List[str]:
        """Fallback: generate template-based suggestions when AI is unavailable."""
        suggestions = []

        for comp in competencies:
            if comp.status in ("focus", "improve", "needs_improvement"):
                suggestions.append(
                    f"'{comp.competency_nm}' 역량이 목표 대비 부족합니다. "
                    "관련 교과목 이수와 비교과 활동 참여를 권장합니다."
                )
            elif comp.gap_score < -10:
                suggestions.append(
                    f"'{comp.competency_nm}' 역량 향상을 위해 "
                    "관련 활동에 더 집중하세요."
                )

        return suggestions[:3]
