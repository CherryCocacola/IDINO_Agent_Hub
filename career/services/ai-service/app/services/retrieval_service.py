"""
Retrieval Service for RAG Pipeline
Phase 2-3: Hybrid Search (BM25 + Vector Similarity)

This service retrieves relevant evidence from multiple data sources
to ground LLM responses with factual information.

Data Sources:
- tb_course: Course descriptions and competency mappings
- tb_program: Non-curricular programs
- tb_success_pattern: Alumni success patterns
- tb_alumni_cohort: Department statistics
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .embedding_service import EmbeddingService
from ..config import get_settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Hybrid Search service combining:
    - Vector similarity (pgvector cosine distance)
    - Keyword matching (PostgreSQL full-text search)

    Falls back to keyword-only search if pgvector is not available.
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.settings = get_settings()
        self._pgvector_available = None

    async def check_pgvector(self) -> bool:
        """Check if pgvector extension is available."""
        if self._pgvector_available is not None:
            return self._pgvector_available

        try:
            result = await self.db.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            self._pgvector_available = result.scalar() is not None
        except Exception:
            self._pgvector_available = False

        logger.info(f"pgvector available: {self._pgvector_available}")
        return self._pgvector_available

    async def hybrid_search(
        self,
        query: str,
        student_id: Optional[str] = None,
        source_types: Optional[List[str]] = None,
        top_k: int = 5,
        alpha: float = 0.7  # Vector weight (1-alpha = BM25 weight)
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search across evidence sources.

        Args:
            query: The search query
            student_id: Optional student ID for personalized search
            source_types: List of source types to search (course, program, alumni, etc.)
            top_k: Number of results to return
            alpha: Weight for vector similarity (0-1)

        Returns:
            List of evidence dictionaries with scores
        """
        if source_types is None:
            source_types = ["course", "program", "alumni", "pattern"]

        results = []

        # Search each source type
        for source_type in source_types:
            try:
                if source_type == "course":
                    items = await self._search_courses(query, top_k)
                elif source_type == "program":
                    items = await self._search_programs(query, top_k)
                elif source_type == "alumni":
                    items = await self._search_alumni_cohorts(query, student_id, top_k)
                elif source_type == "pattern":
                    items = await self._search_success_patterns(query, top_k)
                else:
                    continue

                results.extend(items)
            except Exception as e:
                logger.warning(f"Search failed for {source_type}: {e}")

        # Sort by combined score and limit
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]

    async def _search_courses(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search course descriptions and competency mappings."""
        sql = text("""
            SELECT
                c.course_cd AS source_id,
                'course' AS source_type,
                c.course_nm AS title,
                COALESCE(c.description, '') AS content,
                c.credits,
                cm.competency_cd,
                cm.weight_pct,
                ts_rank(
                    to_tsvector('simple', COALESCE(c.course_nm, '') || ' ' || COALESCE(c.description, '')),
                    plainto_tsquery('simple', :query)
                ) AS score
            FROM tb_course c
            LEFT JOIN tb_course_competency_map cm ON c.course_cd = cm.course_cd
            WHERE
                to_tsvector('simple', COALESCE(c.course_nm, '') || ' ' || COALESCE(c.description, ''))
                @@ plainto_tsquery('simple', :query)
                OR c.course_nm ILIKE :like_query
            ORDER BY score DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(sql, {
                "query": query,
                "like_query": f"%{query}%",
                "limit": limit
            })
            rows = result.fetchall()

            return [
                {
                    "source_id": row.source_id,
                    "source_type": row.source_type,
                    "title": row.title,
                    "content": f"{row.title}: {row.content}" if row.content else row.title,
                    "score": float(row.score) if row.score else 0.1,
                    "metadata": {
                        "credits": row.credits,
                        "competency_cd": row.competency_cd,
                        "weight_pct": float(row.weight_pct) if row.weight_pct else None
                    }
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Course search failed: {e}")
            return []

    async def _search_programs(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search non-curricular programs."""
        sql = text("""
            SELECT
                p.program_cd AS source_id,
                'program' AS source_type,
                p.program_nm AS title,
                COALESCE(p.description, '') AS content,
                p.category,
                p.recognition_pts,
                ts_rank(
                    to_tsvector('simple', COALESCE(p.program_nm, '') || ' ' || COALESCE(p.description, '')),
                    plainto_tsquery('simple', :query)
                ) AS score
            FROM tb_program p
            WHERE
                p.is_active = 'Y'
                AND (
                    to_tsvector('simple', COALESCE(p.program_nm, '') || ' ' || COALESCE(p.description, ''))
                    @@ plainto_tsquery('simple', :query)
                    OR p.program_nm ILIKE :like_query
                    OR p.category ILIKE :like_query
                )
            ORDER BY score DESC, p.recognition_pts DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(sql, {
                "query": query,
                "like_query": f"%{query}%",
                "limit": limit
            })
            rows = result.fetchall()

            return [
                {
                    "source_id": row.source_id,
                    "source_type": row.source_type,
                    "title": row.title,
                    "content": f"[{row.category}] {row.title}: {row.content}",
                    "score": float(row.score) if row.score else 0.1,
                    "metadata": {
                        "category": row.category,
                        "recognition_pts": row.recognition_pts
                    }
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Program search failed: {e}")
            return []

    async def _search_alumni_cohorts(
        self,
        query: str,
        student_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search alumni cohort statistics."""
        sql = text("""
            SELECT
                ac.cohort_id::text AS source_id,
                'alumni' AS source_type,
                ac.graduate_year || ' ' || ac.department_cd || ' 졸업생' AS title,
                ac.job_title_top3 || ' 등 취업. 평균 연봉 ' || COALESCE(ac.avg_starting_salary::text, 'N/A') AS content,
                ac.graduate_year,
                ac.department_cd,
                ac.job_title_top3,
                ac.avg_starting_salary,
                ac.sample_size,
                CASE
                    WHEN ac.job_title_top3 ILIKE :like_query THEN 1.0
                    WHEN ac.department_cd ILIKE :like_query THEN 0.8
                    ELSE 0.5
                END AS score
            FROM tb_alumni_cohort ac
            WHERE
                ac.job_title_top3 ILIKE :like_query
                OR ac.department_cd ILIKE :like_query
                OR :query ILIKE '%' || ac.department_cd || '%'
            ORDER BY ac.graduate_year DESC, score DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(sql, {
                "query": query,
                "like_query": f"%{query}%",
                "limit": limit
            })
            rows = result.fetchall()

            return [
                {
                    "source_id": row.source_id,
                    "source_type": row.source_type,
                    "title": row.title,
                    "content": row.content,
                    "score": float(row.score),
                    "metadata": {
                        "graduate_year": row.graduate_year,
                        "department_cd": row.department_cd,
                        "sample_size": row.sample_size,
                        "avg_salary": float(row.avg_starting_salary) if row.avg_starting_salary else None
                    }
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Alumni search failed: {e}")
            return []

    async def _search_success_patterns(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search success patterns from alumni data."""
        sql = text("""
            SELECT
                sp.pattern_id::text AS source_id,
                'pattern' AS source_type,
                sp.pattern_nm AS title,
                sp.description AS content,
                sp.target_role,
                sp.avg_competency_scores,
                sp.evidence_count,
                ts_rank(
                    to_tsvector('simple', COALESCE(sp.pattern_nm, '') || ' ' || COALESCE(sp.description, '') || ' ' || COALESCE(sp.target_role, '')),
                    plainto_tsquery('simple', :query)
                ) AS score
            FROM tb_success_pattern sp
            WHERE
                sp.is_active = 'Y'
                AND (
                    to_tsvector('simple', COALESCE(sp.pattern_nm, '') || ' ' || COALESCE(sp.description, '') || ' ' || COALESCE(sp.target_role, ''))
                    @@ plainto_tsquery('simple', :query)
                    OR sp.pattern_nm ILIKE :like_query
                    OR sp.target_role ILIKE :like_query
                )
            ORDER BY score DESC, sp.evidence_count DESC
            LIMIT :limit
        """)

        try:
            result = await self.db.execute(sql, {
                "query": query,
                "like_query": f"%{query}%",
                "limit": limit
            })
            rows = result.fetchall()

            return [
                {
                    "source_id": row.source_id,
                    "source_type": row.source_type,
                    "title": row.title,
                    "content": f"[{row.target_role}] {row.content}",
                    "score": float(row.score) if row.score else 0.1,
                    "metadata": {
                        "target_role": row.target_role,
                        "evidence_count": row.evidence_count,
                        "competency_scores": row.avg_competency_scores
                    }
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Pattern search failed: {e}")
            return []

    async def get_student_context(self, student_id: str) -> Dict[str, Any]:
        """
        Get personalized context for a student.

        Returns:
            Dictionary with student's courses, activities, and achievements
        """
        context = {
            "enrollments": [],
            "activities": [],
            "achievements": []
        }

        # Get recent enrollments
        try:
            enrollments_sql = text("""
                SELECT
                    c.course_nm,
                    c.course_cd,
                    g.letter_grade,
                    t.academic_year,
                    t.semester
                FROM tb_enrollment e
                JOIN tb_course_offering co ON e.course_offering_id = co.course_offering_id
                JOIN tb_course c ON co.course_id = c.course_id
                JOIN tb_term t ON co.term_id = t.term_id
                LEFT JOIN tb_grade g ON e.enrollment_id = g.enrollment_id
                WHERE e.student_id = :student_id
                ORDER BY t.academic_year DESC, t.semester DESC
                LIMIT 10
            """)
            result = await self.db.execute(enrollments_sql, {"student_id": student_id})
            context["enrollments"] = [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Failed to get enrollments: {e}")

        return context

    def format_evidence_for_prompt(self, evidence: List[Dict[str, Any]]) -> str:
        """
        Format retrieved evidence for inclusion in LLM prompt.

        Args:
            evidence: List of evidence dictionaries

        Returns:
            Formatted string for prompt injection
        """
        if not evidence:
            return ""

        lines = ["## 참고 자료 (Evidence)\n"]

        for i, e in enumerate(evidence, 1):
            source_type = e.get("source_type", "unknown")
            title = e.get("title", "")
            content = e.get("content", "")
            score = e.get("score", 0)

            lines.append(f"[{i}] [{source_type.upper()}] {title}")
            if content:
                # Truncate long content
                truncated = content[:300] + "..." if len(content) > 300 else content
                lines.append(f"    {truncated}")
            lines.append(f"    (relevance: {score:.2f})")
            lines.append("")

        return "\n".join(lines)
