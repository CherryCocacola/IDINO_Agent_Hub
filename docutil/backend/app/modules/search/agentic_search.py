"""
Agentic Search Service.

Wraps the existing SearchService with an LLM-driven loop:
1. Query Analysis  -- extract intent and optimize the query
2. First Search    -- run hybrid search via SearchService
3. Quality Check   -- LLM judges if results are SUFFICIENT or RETRY
4. If RETRY        -- LLM reformulates the query and re-searches
5. Max 3 retries, 15-second total timeout
6. Cache final results in Redis
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.cache import get_redis
from app.core.config import get_settings
from app.integrations.llm.prompts import (
    AGENTIC_QUALITY_JUDGMENT_PROMPT,
    AGENTIC_QUERY_ANALYSIS_PROMPT,
)

from .schemas import SearchResponse
from .service import SearchService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
TOTAL_TIMEOUT_SECONDS = 15.0
REDIS_CACHE_TTL = 300  # 5 minutes


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AgenticSearchService:
    """Search service with LLM-driven query refinement loop.

    Uses the existing ``SearchService.hybrid_search`` for each retrieval
    attempt and wraps it with query analysis, quality judgment, and
    automatic query reformulation.
    """

    @staticmethod
    async def agentic_search(
        db: AsyncSession,
        query: str,
        scope_id: UUID | None,
        doc_ids: list[UUID] | None,
        org_id: UUID,
        max_results: int = 10,
        user_id: UUID | None = None,
        user_role: str | None = None,
        user_dept_id: UUID | None = None,
        as_user_view: bool = False,
    ) -> SearchResponse:
        """Execute an agentic search with automatic query refinement.

        Returns a ``SearchResponse`` augmented with agentic metadata
        (iterations, queries tried).

        Visibility 인자는 내부 ``SearchService.hybrid_search`` 호출에 그대로
        위임된다. ``as_user_view=True`` 일 때 admin 도 일반 사용자처럼 권한
        필터가 적용된다.
        """

        start = time.perf_counter()
        deadline = start + TOTAL_TIMEOUT_SECONDS

        # -- 0. Check Redis cache -----------------------------------------------
        cache_key = AgenticSearchService._cache_key(query, org_id, scope_id)
        cached = await AgenticSearchService._get_cached(cache_key)
        if cached is not None:
            return cached

        # -- 1. Query Analysis --------------------------------------------------
        optimized_query = query
        try:
            analysis = await asyncio.wait_for(
                AgenticSearchService._analyze_query(query),
                timeout=max(deadline - time.perf_counter(), 1.0),
            )
            optimized_query = analysis.get("optimized_query", query)
        except (TimeoutError, Exception):
            logger.debug("Query analysis skipped (timeout or error)")

        # -- 2. Search loop with quality check ----------------------------------
        queries_tried: list[str] = []
        best_response: SearchResponse | None = None
        iteration = 0

        current_query = optimized_query

        while iteration <= MAX_RETRIES:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                logger.debug("Agentic search timeout after %d iterations", iteration)
                break

            queries_tried.append(current_query)
            iteration += 1

            # Run hybrid search
            try:
                response = await asyncio.wait_for(
                    SearchService.hybrid_search(
                        db=db,
                        query=current_query,
                        scope_id=scope_id,
                        doc_ids=doc_ids,
                        org_id=org_id,
                        max_results=max_results,
                        user_id=user_id,
                        user_role=user_role,
                        user_dept_id=user_dept_id,
                        as_user_view=as_user_view,
                    ),
                    timeout=max(remaining, 1.0),
                )
            except (TimeoutError, Exception):
                logger.debug("Search attempt %d failed", iteration)
                break

            # Keep the best response (most results with highest scores)
            if best_response is None or _response_quality(response) > _response_quality(best_response):
                best_response = response

            # First iteration always does quality check; skip on last retry
            if iteration > MAX_RETRIES:
                break

            # Quality judgment
            remaining = deadline - time.perf_counter()
            if remaining <= 2.0:
                break  # not enough time for LLM call + another search

            try:
                judgment = await asyncio.wait_for(
                    AgenticSearchService._judge_quality(
                        query=query,
                        response=response,
                    ),
                    timeout=max(remaining - 1.0, 1.0),
                )
            except (TimeoutError, Exception):
                logger.debug("Quality judgment skipped (timeout or error)")
                break

            if judgment.get("verdict") == "SUFFICIENT":
                break

            # RETRY: use suggested reformulated query
            suggested = judgment.get("suggested_query")
            if suggested and suggested.strip() and suggested != current_query:
                current_query = suggested
            else:
                break  # no useful reformulation

        # -- 3. Build final response --------------------------------------------
        if best_response is None:
            # Fallback: run a plain search with original query
            best_response = await SearchService.hybrid_search(
                db=db,
                query=query,
                scope_id=scope_id,
                doc_ids=doc_ids,
                org_id=org_id,
                max_results=max_results,
                user_id=user_id,
                user_role=user_role,
                user_dept_id=user_dept_id,
                as_user_view=as_user_view,
            )

        total_latency = int((time.perf_counter() - start) * 1000)

        final_response = SearchResponse(
            query=query,
            results=best_response.results,
            total_results=best_response.total_results,
            search_type="agentic",
            latency_ms=total_latency,
        )

        # -- 4. Cache final results ---------------------------------------------
        await AgenticSearchService._set_cached(cache_key, final_response)

        return final_response

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _analyze_query(query: str) -> dict:
        """Use LLM to analyze and optimize the search query.

        Phase 7.3: ``OpenAIClient()`` 직접 호출(R2/anti-patterns.md §1 위반)을 제거하고
        factory 경유로 변경. 내부적으로 ``AgentHubLLMWrapper`` 가 ``agentic-search``
        AgentCode 로 위임하여 AgentHub 의 라우팅/사용량/PII 정책을 적용받는다.
        """
        from app.integrations.llm.factory import create_llm_client

        llm = create_llm_client("agentic_search")
        prompt = AGENTIC_QUERY_ANALYSIS_PROMPT.format(query=query)

        response = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
        )

        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            return {"optimized_query": query}

    @staticmethod
    async def _judge_quality(
        query: str,
        response: SearchResponse,
    ) -> dict:
        """Use LLM to judge whether search results are sufficient.

        Phase 7.3: ``OpenAIClient()`` 직접 호출 제거. ``agentic-search`` AgentCode 로
        AgentHub 위임. 결과 품질 판정은 단일 진입점을 통해 사용량/감사 로그에 집계된다.
        """
        from app.integrations.llm.factory import create_llm_client

        llm = create_llm_client("agentic_search")

        # Build results summary for the LLM
        results_lines = []
        for i, r in enumerate(response.results[:5], 1):
            snippet = r.content[:150].replace("\n", " ")
            results_lines.append(f'  [{i}] score={r.score:.3f} doc="{r.document_name}" snippet="{snippet}..."')
        results_summary = "\n".join(results_lines) if results_lines else "(no results)"

        prompt = AGENTIC_QUALITY_JUDGMENT_PROMPT.format(
            query=query,
            result_count=len(response.results),
            results_summary=results_summary,
        )

        raw = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300,
        )

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"verdict": "SUFFICIENT"}

    # ------------------------------------------------------------------
    # Redis cache helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(query: str, org_id: UUID, scope_id: UUID | None) -> str:
        """Build a Redis cache key for agentic search results."""
        raw = f"agentic:{org_id}:{scope_id or 'all'}:{query}"
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return f"agentic_search:{h}"

    @staticmethod
    async def _get_cached(key: str) -> SearchResponse | None:
        """Retrieve cached agentic search results from Redis."""
        try:
            redis = await get_redis()
            if redis is None:
                return None
            raw = await redis.get(key)
            if raw is None:
                return None
            data = json.loads(raw)
            return SearchResponse(**data)
        except Exception:
            logger.debug("Agentic search cache read failed", exc_info=True)
            return None

    @staticmethod
    async def _set_cached(key: str, response: SearchResponse) -> None:
        """Cache agentic search results in Redis."""
        try:
            redis = await get_redis()
            if redis is None:
                return
            await redis.set(
                key,
                response.model_dump_json(),
                ex=REDIS_CACHE_TTL,
            )
        except Exception:
            logger.debug("Agentic search cache write failed", exc_info=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _response_quality(response: SearchResponse) -> float:
    """Score a SearchResponse for comparison (higher is better)."""
    if not response.results:
        return 0.0
    avg_score = sum(r.score for r in response.results) / len(response.results)
    return avg_score * min(len(response.results), 10)
