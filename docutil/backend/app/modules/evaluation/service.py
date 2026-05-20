"""
Evaluation service — LLM-as-judge evaluation pipeline.

Orchestrates test question execution through the search pipeline,
then judges response quality using GPT-4o across 4 metrics.
"""

from __future__ import annotations

import json
import logging
import uuid as uuid_mod
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import case, cast, func, select, Date

from app.core.config import get_settings

from .constants import (
    ALL_METRICS,
    DEFAULT_METRIC_WEIGHTS,
    METRIC_ANSWER_FAITHFULNESS,
    METRIC_ANSWER_RELEVANCY,
    METRIC_CONTEXT_RELEVANCY,
    METRIC_HALLUCINATION,
    METRIC_PROMPTS,
)
from .models import EvaluationConfig, EvaluationLog
from .schemas import (
    EvaluationLogFilter,
    EvaluationRunSummary,
    EvaluationTrendPoint,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Path to default test questions
_TEST_QUESTIONS_PATH = Path(__file__).parent / "test_questions.json"


class EvaluationService:
    """Stateless evaluation service."""

    # ------------------------------------------------------------------
    # Test questions
    # ------------------------------------------------------------------

    @staticmethod
    def load_test_questions() -> list[dict[str, str]]:
        """Load default test question set from JSON file."""
        with open(_TEST_QUESTIONS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data["questions"]

    # ------------------------------------------------------------------
    # Metric weights
    # ------------------------------------------------------------------

    @staticmethod
    async def get_weights(
        db: AsyncSession,
        org_id: UUID,
    ) -> dict[str, float]:
        """Get metric weights for an organization, falling back to defaults."""
        result = await db.execute(
            select(EvaluationConfig).where(
                EvaluationConfig.organization_id == org_id,
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            return dict(DEFAULT_METRIC_WEIGHTS)
        return {
            METRIC_CONTEXT_RELEVANCY: config.context_relevancy_weight,
            METRIC_ANSWER_FAITHFULNESS: config.answer_faithfulness_weight,
            METRIC_ANSWER_RELEVANCY: config.answer_relevancy_weight,
            METRIC_HALLUCINATION: config.hallucination_weight,
        }

    @staticmethod
    async def get_config(
        db: AsyncSession,
        org_id: UUID,
    ) -> EvaluationConfig | None:
        """Get evaluation config for an organization."""
        result = await db.execute(
            select(EvaluationConfig).where(
                EvaluationConfig.organization_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_config(
        db: AsyncSession,
        org_id: UUID,
        *,
        context_relevancy_weight: float,
        answer_faithfulness_weight: float,
        answer_relevancy_weight: float,
        hallucination_weight: float,
    ) -> EvaluationConfig:
        """Create or update per-org metric weight configuration."""
        result = await db.execute(
            select(EvaluationConfig).where(
                EvaluationConfig.organization_id == org_id,
            )
        )
        config = result.scalar_one_or_none()
        if config is None:
            config = EvaluationConfig(
                organization_id=org_id,
                context_relevancy_weight=context_relevancy_weight,
                answer_faithfulness_weight=answer_faithfulness_weight,
                answer_relevancy_weight=answer_relevancy_weight,
                hallucination_weight=hallucination_weight,
            )
            db.add(config)
        else:
            config.context_relevancy_weight = context_relevancy_weight
            config.answer_faithfulness_weight = answer_faithfulness_weight
            config.answer_relevancy_weight = answer_relevancy_weight
            config.hallucination_weight = hallucination_weight
        await db.flush()
        await db.refresh(config)
        return config

    # ------------------------------------------------------------------
    # Judge a single question/answer pair
    # ------------------------------------------------------------------

    @staticmethod
    def _judge_metric_sync(
        llm_client: Any,
        metric: str,
        question: str,
        answer: str,
        contexts_text: str,
    ) -> dict[str, Any]:
        """Run a single metric evaluation using LLM judge (sync for Celery)."""
        prompt_template = METRIC_PROMPTS[metric]
        prompt = prompt_template.format(
            question=question,
            answer=answer,
            contexts=contexts_text,
        )
        messages = [
            {"role": "system", "content": "You are an AI evaluation judge. Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            raw = llm_client.generate_sync(
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
            return json.loads(raw)
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Judge parse error for metric %s: %s", metric, exc)
            if metric == METRIC_HALLUCINATION:
                return {"has_hallucination": False, "evidence": [], "score": 0.5}
            return {"score": 0.5, "reasoning": f"Judge error: {str(exc)[:200]}"}

    @staticmethod
    async def _judge_metric_async(
        llm_client: Any,
        metric: str,
        question: str,
        answer: str,
        contexts_text: str,
    ) -> dict[str, Any]:
        """Run a single metric evaluation using LLM judge (async for FastAPI)."""
        prompt_template = METRIC_PROMPTS[metric]
        prompt = prompt_template.format(
            question=question,
            answer=answer,
            contexts=contexts_text,
        )
        messages = [
            {"role": "system", "content": "You are an AI evaluation judge. Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ]

        try:
            raw = await llm_client.generate(
                messages=messages,
                temperature=0.0,
                max_tokens=512,
            )
            return json.loads(raw)
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning("Judge parse error for metric %s: %s", metric, exc)
            if metric == METRIC_HALLUCINATION:
                return {"has_hallucination": False, "evidence": [], "score": 0.5}
            return {"score": 0.5, "reasoning": f"Judge error: {str(exc)[:200]}"}

    # ------------------------------------------------------------------
    # Run evaluation for a single question
    # ------------------------------------------------------------------

    @staticmethod
    def evaluate_single_sync(
        llm_client: Any,
        question: str,
        answer: str,
        contexts: list[str],
        weights: dict[str, float],
    ) -> dict[str, Any]:
        """Evaluate a single Q&A pair (sync for Celery worker)."""
        contexts_text = "\n\n---\n\n".join(
            f"[Source {i + 1}]: {c}" for i, c in enumerate(contexts)
        )

        judge_details: dict[str, Any] = {}

        # Context Relevancy
        cr_result = EvaluationService._judge_metric_sync(
            llm_client, METRIC_CONTEXT_RELEVANCY, question, answer, contexts_text
        )
        judge_details[METRIC_CONTEXT_RELEVANCY] = cr_result
        cr_score = float(cr_result.get("score", 0.0))

        # Answer Faithfulness
        af_result = EvaluationService._judge_metric_sync(
            llm_client, METRIC_ANSWER_FAITHFULNESS, question, answer, contexts_text
        )
        judge_details[METRIC_ANSWER_FAITHFULNESS] = af_result
        af_score = float(af_result.get("score", 0.0))

        # Answer Relevancy
        ar_result = EvaluationService._judge_metric_sync(
            llm_client, METRIC_ANSWER_RELEVANCY, question, answer, contexts_text
        )
        judge_details[METRIC_ANSWER_RELEVANCY] = ar_result
        ar_score = float(ar_result.get("score", 0.0))

        # Hallucination Detection
        hd_result = EvaluationService._judge_metric_sync(
            llm_client, METRIC_HALLUCINATION, question, answer, contexts_text
        )
        judge_details[METRIC_HALLUCINATION] = hd_result
        hd_score = float(hd_result.get("score", 0.0))
        has_hallucination = bool(hd_result.get("has_hallucination", False))
        # 트랙 #105 Phase B.5 — frontend/AgentHub BFF DTO 가 dict 만 처리하므로
        # list 가 반환되면 dict 로 래핑. 비어 있으면 None 으로 저장.
        _evidence_raw = hd_result.get("evidence")
        if not _evidence_raw:
            hallucination_evidence: dict | None = None
        elif isinstance(_evidence_raw, list):
            hallucination_evidence = {"items": _evidence_raw}
        elif isinstance(_evidence_raw, dict):
            hallucination_evidence = _evidence_raw
        else:
            hallucination_evidence = {"value": _evidence_raw}

        # Composite score
        composite = (
            cr_score * weights.get(METRIC_CONTEXT_RELEVANCY, 0.25)
            + af_score * weights.get(METRIC_ANSWER_FAITHFULNESS, 0.30)
            + ar_score * weights.get(METRIC_ANSWER_RELEVANCY, 0.25)
            + hd_score * weights.get(METRIC_HALLUCINATION, 0.20)
        )

        return {
            "context_relevancy": cr_score,
            "answer_faithfulness": af_score,
            "answer_relevancy": ar_score,
            "hallucination_score": hd_score,
            "has_hallucination": has_hallucination,
            "hallucination_evidence": hallucination_evidence,
            "composite_score": round(composite, 4),
            "judge_details": judge_details,
        }

    # ------------------------------------------------------------------
    # CRUD for logs
    # ------------------------------------------------------------------

    @staticmethod
    async def create_log(
        db: AsyncSession,
        *,
        org_id: UUID,
        run_id: str,
        question: str,
        answer: str,
        contexts: list[str] | None,
        metrics: dict[str, Any],
        run_type: str = "scheduled",
        question_index: int = 0,
    ) -> EvaluationLog:
        """Persist a single evaluation result."""
        log = EvaluationLog(
            organization_id=org_id,
            run_id=run_id,
            question=question,
            answer=answer,
            contexts={"sources": contexts} if contexts else None,
            context_relevancy=metrics["context_relevancy"],
            answer_faithfulness=metrics["answer_faithfulness"],
            answer_relevancy=metrics["answer_relevancy"],
            hallucination_score=metrics["hallucination_score"],
            has_hallucination=metrics["has_hallucination"],
            hallucination_evidence=metrics.get("hallucination_evidence"),
            composite_score=metrics["composite_score"],
            judge_details=metrics.get("judge_details"),
            run_type=run_type,
            question_index=question_index,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        org_id: UUID,
        filters: EvaluationLogFilter,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[EvaluationLog], int]:
        """Return filtered, paginated evaluation logs."""
        base = select(EvaluationLog).where(EvaluationLog.organization_id == org_id)

        if filters.run_id is not None:
            base = base.where(EvaluationLog.run_id == filters.run_id)
        if filters.run_type is not None:
            base = base.where(EvaluationLog.run_type == filters.run_type)
        if filters.has_hallucination is not None:
            base = base.where(EvaluationLog.has_hallucination == filters.has_hallucination)
        if filters.min_score is not None:
            base = base.where(EvaluationLog.composite_score >= filters.min_score)
        if filters.max_score is not None:
            base = base.where(EvaluationLog.composite_score <= filters.max_score)

        count_q = select(func.count()).select_from(base.subquery())
        total = (await db.execute(count_q)).scalar_one()

        offset = (page - 1) * size
        items_q = base.order_by(EvaluationLog.ins_dt.desc()).offset(offset).limit(size)
        result = await db.execute(items_q)
        logs = list(result.scalars().all())

        return logs, total

    @staticmethod
    async def get_run_summaries(
        db: AsyncSession,
        org_id: UUID,
        limit: int = 30,
    ) -> list[EvaluationRunSummary]:
        """Get aggregated summaries per run_id, most recent first."""
        q = (
            select(
                EvaluationLog.run_id,
                EvaluationLog.run_type,
                func.min(EvaluationLog.ins_dt).label("created_at"),
                func.count().label("question_count"),
                func.avg(EvaluationLog.context_relevancy).label("avg_context_relevancy"),
                func.avg(EvaluationLog.answer_faithfulness).label("avg_answer_faithfulness"),
                func.avg(EvaluationLog.answer_relevancy).label("avg_answer_relevancy"),
                func.avg(EvaluationLog.hallucination_score).label("avg_hallucination_score"),
                func.avg(EvaluationLog.composite_score).label("avg_composite_score"),
                func.sum(
                    case((EvaluationLog.has_hallucination.is_(True), 1), else_=0)
                ).label("hallucination_count"),
            )
            .where(EvaluationLog.organization_id == org_id)
            .group_by(EvaluationLog.run_id, EvaluationLog.run_type)
            .order_by(func.min(EvaluationLog.ins_dt).desc())
            .limit(limit)
        )
        result = await db.execute(q)
        rows = result.all()

        return [
            EvaluationRunSummary(
                run_id=row.run_id,
                run_type=row.run_type,
                created_at=row.created_at,
                question_count=row.question_count,
                avg_context_relevancy=round(float(row.avg_context_relevancy or 0), 4),
                avg_answer_faithfulness=round(float(row.avg_answer_faithfulness or 0), 4),
                avg_answer_relevancy=round(float(row.avg_answer_relevancy or 0), 4),
                avg_hallucination_score=round(float(row.avg_hallucination_score or 0), 4),
                avg_composite_score=round(float(row.avg_composite_score or 0), 4),
                hallucination_count=int(row.hallucination_count or 0),
            )
            for row in rows
        ]

    @staticmethod
    async def get_trend(
        db: AsyncSession,
        org_id: UUID,
        days: int = 30,
    ) -> list[EvaluationTrendPoint]:
        """Get daily average scores for trend chart."""
        q = (
            select(
                cast(EvaluationLog.ins_dt, Date).label("date"),
                func.avg(EvaluationLog.context_relevancy).label("avg_context_relevancy"),
                func.avg(EvaluationLog.answer_faithfulness).label("avg_answer_faithfulness"),
                func.avg(EvaluationLog.answer_relevancy).label("avg_answer_relevancy"),
                func.avg(EvaluationLog.hallucination_score).label("avg_hallucination_score"),
                func.avg(EvaluationLog.composite_score).label("avg_composite_score"),
            )
            .where(EvaluationLog.organization_id == org_id)
            .group_by(cast(EvaluationLog.ins_dt, Date))
            .order_by(cast(EvaluationLog.ins_dt, Date).desc())
            .limit(days)
        )
        result = await db.execute(q)
        rows = list(result.all())
        rows.reverse()  # chronological order

        return [
            EvaluationTrendPoint(
                date=str(row.date),
                avg_context_relevancy=round(float(row.avg_context_relevancy or 0), 4),
                avg_answer_faithfulness=round(float(row.avg_answer_faithfulness or 0), 4),
                avg_answer_relevancy=round(float(row.avg_answer_relevancy or 0), 4),
                avg_hallucination_score=round(float(row.avg_hallucination_score or 0), 4),
                avg_composite_score=round(float(row.avg_composite_score or 0), 4),
            )
            for row in rows
        ]
