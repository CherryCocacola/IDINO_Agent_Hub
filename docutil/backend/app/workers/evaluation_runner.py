"""
Evaluation Celery worker.

Scheduled daily at 3 AM (Asia/Seoul) to run the test question set through
the search pipeline, then judge response quality using LLM-as-judge.

Also supports manual runs triggered from the admin API.
"""

from __future__ import annotations

import asyncio
import logging
import uuid as uuid_mod
from typing import Any

from app.core.config import get_settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def _get_worker_session():
    """Celery Worker 전용 async session factory."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def _get_llm_client():
    """LLM 클라이언트를 팩토리에서 가져온다."""
    from app.integrations.llm.factory import create_llm_client, get_provider_for_task

    provider = get_provider_for_task("evaluation")
    return create_llm_client(provider)


def _get_search_answer(org_id: str, question: str) -> dict[str, Any]:
    """Run a QA search to get answer + contexts for a question (sync wrapper)."""

    async def _search():
        from uuid import UUID

        from app.modules.search.service import SearchService

        session_factory = _get_worker_session()
        async with session_factory() as db:
            result = await SearchService.hybrid_search(
                db=db,
                query=question,
                scope_id=None,
                doc_ids=None,
                org_id=UUID(org_id),
                max_results=5,
            )

            contexts = [r.content for r in result.results if r.content]

            # Generate answer using RAG QA
            from app.integrations.llm.prompts import RAG_QA_PROMPT

            context_text = "\n\n---\n\n".join(
                f"[Source {i + 1}]: {c}" for i, c in enumerate(contexts)
            )
            prompt = RAG_QA_PROMPT.format(context=context_text, query=question)

            llm = _get_llm_client()
            answer = await llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048,
            )

            return {
                "answer": answer,
                "contexts": contexts,
            }

    return _run_async(_search())


def _get_all_org_ids() -> list[str]:
    """Get all active organization IDs from DB."""

    async def _load():
        from sqlalchemy import select

        from app.modules.organizations.models import Organization

        async with _get_worker_session()() as db:
            result = await db.execute(select(Organization.id))
            return [str(row[0]) for row in result.all()]

    return _run_async(_load())


def _get_weights(org_id: str) -> dict[str, float]:
    """Load metric weights for an org."""

    async def _load():
        from uuid import UUID

        from app.modules.evaluation.service import EvaluationService

        async with _get_worker_session()() as db:
            return await EvaluationService.get_weights(db, UUID(org_id))

    return _run_async(_load())


def _save_log(org_id: str, run_id: str, question: str, answer: str,
              contexts: list[str] | None, metrics: dict, run_type: str,
              question_index: int) -> None:
    """Persist evaluation result to DB."""

    async def _persist():
        from uuid import UUID

        from app.modules.evaluation.service import EvaluationService

        async with _get_worker_session()() as db:
            await EvaluationService.create_log(
                db,
                org_id=UUID(org_id),
                run_id=run_id,
                question=question,
                answer=answer,
                contexts=contexts,
                metrics=metrics,
                run_type=run_type,
                question_index=question_index,
            )
            await db.commit()

    _run_async(_persist())


def _update_prometheus_metrics(org_id: str, metrics: dict[str, float]) -> None:
    """Push evaluation metrics to Prometheus via Redis (for Prometheus exporter)."""
    try:
        import redis

        r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        import json

        r.setex(
            f"eval_metrics:org:{org_id}",
            86400,  # 24h TTL
            json.dumps(metrics),
        )
        r.close()
    except Exception as exc:
        logger.warning("Failed to update Prometheus metrics in Redis: %s", exc)


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------


@celery_app.task(
    bind=True,
    name="workers.evaluation_runner.run_evaluation",
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
    track_started=True,
)
def run_evaluation(
    self,
    org_id: str,
    run_id: str | None = None,
    run_type: str = "scheduled",
    custom_questions: list[str] | None = None,
) -> dict[str, Any]:
    """Run evaluation for a single organization.

    Args:
        org_id: Organization UUID string.
        run_id: Unique run identifier (auto-generated if None).
        run_type: "scheduled" or "manual".
        custom_questions: Optional custom question list. If None, uses default set.
    """
    if run_id is None:
        run_id = uuid_mod.uuid4().hex[:16]

    logger.info("Starting evaluation run %s for org %s (type=%s)", run_id, org_id, run_type)

    # Load questions
    if custom_questions:
        questions = custom_questions
    else:
        from app.modules.evaluation.service import EvaluationService
        test_set = EvaluationService.load_test_questions()
        questions = [q["question"] for q in test_set]

    # Load weights
    weights = _get_weights(org_id)

    # Get LLM judge client
    llm_judge = _get_llm_client()

    from app.modules.evaluation.service import EvaluationService

    total_scores: dict[str, float] = {
        "context_relevancy": 0.0,
        "answer_faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "hallucination_score": 0.0,
        "composite_score": 0.0,
    }
    evaluated_count = 0

    for idx, question in enumerate(questions):
        try:
            # 1. Get answer via search pipeline
            search_result = _get_search_answer(org_id, question)
            answer = search_result["answer"]
            contexts = search_result["contexts"]

            # 2. Judge the response
            metrics = EvaluationService.evaluate_single_sync(
                llm_client=llm_judge,
                question=question,
                answer=answer,
                contexts=contexts,
                weights=weights,
            )

            # 3. Persist
            _save_log(
                org_id=org_id,
                run_id=run_id,
                question=question,
                answer=answer,
                contexts=contexts,
                metrics=metrics,
                run_type=run_type,
                question_index=idx,
            )

            # Accumulate
            for key in total_scores:
                total_scores[key] += metrics.get(key, 0.0)
            evaluated_count += 1

            logger.info(
                "Evaluated Q%d/%d: composite=%.3f",
                idx + 1,
                len(questions),
                metrics["composite_score"],
            )

        except Exception as exc:
            logger.exception("Failed to evaluate question %d: %s", idx, exc)
            continue

    # Compute averages
    if evaluated_count > 0:
        avg_scores = {k: round(v / evaluated_count, 4) for k, v in total_scores.items()}
    else:
        avg_scores = total_scores

    # Update Prometheus-compatible metrics in Redis
    _update_prometheus_metrics(org_id, avg_scores)

    logger.info(
        "Evaluation run %s complete: %d/%d questions, avg_composite=%.3f",
        run_id,
        evaluated_count,
        len(questions),
        avg_scores.get("composite_score", 0.0),
    )

    return {
        "run_id": run_id,
        "org_id": org_id,
        "evaluated_count": evaluated_count,
        "total_questions": len(questions),
        "avg_scores": avg_scores,
    }


@celery_app.task(
    name="workers.evaluation_runner.run_scheduled_evaluation",
    ignore_result=True,
)
def run_scheduled_evaluation() -> None:
    """Scheduled task: run evaluation for all organizations.

    Triggered daily at 3 AM via Celery Beat.
    """
    logger.info("Starting scheduled evaluation for all organizations")

    org_ids = _get_all_org_ids()
    logger.info("Found %d organizations to evaluate", len(org_ids))

    for org_id in org_ids:
        run_id = uuid_mod.uuid4().hex[:16]
        try:
            run_evaluation.delay(org_id, run_id, "scheduled")
        except Exception as exc:
            logger.exception("Failed to enqueue evaluation for org %s: %s", org_id, exc)
            continue

    logger.info("Scheduled evaluation enqueued for %d organizations", len(org_ids))
