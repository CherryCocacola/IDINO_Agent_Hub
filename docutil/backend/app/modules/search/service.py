"""
Search business logic.

Orchestrates hybrid (dense + sparse), keyword, chatbot, and QA search
pipelines by combining Qdrant vector retrieval, BM25 sparse scoring,
re-ranking, and LLM-based answer generation.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

from .schemas import (
    ChatbotSearchResponse,
    Citation,
    QASearchResponse,
    SearchHistoryItem,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SearchService:
    """Stateless service that encapsulates all search operations.

    All public methods receive their dependencies (database session, IDs)
    explicitly so that callers control the transaction boundary.
    """

    # ------------------------------------------------------------------
    # Hybrid search (dense + sparse + RRF + rerank)
    # ------------------------------------------------------------------

    @staticmethod
    async def hybrid_search(
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
        """Execute a hybrid retrieval pipeline.

        Steps
        -----
        1. Generate a dense embedding for *query* via the embedding service.
        2. Query Qdrant with organisation-scoped filters (scope / doc IDs).
        3. Run a parallel sparse BM25 search over the same corpus slice.
        4. Fuse rankings using Reciprocal Rank Fusion (RRF).
        5. Re-rank the top candidates with a cross-encoder model.
        6. Persist the query in search history and return scored results.

        Visibility 권한 처리:
        - ``as_user_view=True`` 인 경우 admin 계열도 일반 사용자처럼 visibility
          필터를 적용한다. 사용자 화면(/search, /search/chatbot 등)에서 사용한다.
        - ``as_user_view=False`` (기본값) 이고 user_role 이 admin 계열이면
          visibility 검사 bypass. 운영자 검색 테스트(/search/test)에서 사용한다.
        """

        start = time.perf_counter()
        settings = get_settings()

        # 0. Visibility 권한 적용 ---------------------------------------------
        # 사용자가 접근 가능한 document_id 목록을 사전에 한 번만 계산하여
        # Qdrant 필터와 BM25 SQL 의 doc_ids 에 모두 적용한다.
        effective_doc_ids = await SearchService._apply_visibility_scope(
            db=db,
            org_id=org_id,
            doc_ids=doc_ids,
            user_id=user_id,
            user_role=user_role,
            user_dept_id=user_dept_id,
            as_user_view=as_user_view,
        )

        # 권한상 볼 수 있는 문서가 하나도 없으면 즉시 빈 결과 반환.
        # (effective_doc_ids 가 빈 list 인 경우와 None 인 경우를 구분해야 함)
        if effective_doc_ids is not None and len(effective_doc_ids) == 0:
            latency_ms = int((time.perf_counter() - start) * 1000)
            await SearchService._save_search_history(
                db=db,
                query=query,
                search_type="hybrid",
                result_count=0,
                org_id=org_id,
                user_id=user_id,
            )
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_type="hybrid",
                latency_ms=latency_ms,
            )

        # 1. Dense embedding ---------------------------------------------------
        query_embedding = await SearchService._get_embedding(query)

        # 2. Qdrant dense search -----------------------------------------------
        qdrant_filter = SearchService._build_qdrant_filter(
            org_id=org_id,
            scope_id=scope_id,
            doc_ids=effective_doc_ids,
        )

        # org별 Qdrant 컬렉션명 생성 (org_{uuid_with_underscores})
        org_collection = f"org_{str(org_id).replace('-', '_')}"

        dense_results = await SearchService._dense_search(
            query_embedding=query_embedding,
            qdrant_filter=qdrant_filter,
            collection=org_collection,
            limit=max_results * 3,  # over-fetch for fusion
        )

        # 3. BM25 sparse search ------------------------------------------------
        sparse_results = await SearchService._sparse_bm25_search(
            query=query,
            org_id=org_id,
            scope_id=scope_id,
            doc_ids=effective_doc_ids,
            limit=max_results * 3,
        )

        # 4. RRF fusion --------------------------------------------------------
        fused = SearchService._rrf_fusion(
            dense_results=dense_results,
            sparse_results=sparse_results,
            k=60,
        )

        # 5. Re-rank top candidates --------------------------------------------
        top_candidates = fused[: max_results * 2]
        reranked = await SearchService._rerank_results(
            query=query,
            candidates=top_candidates,
        )
        final_results = reranked[:max_results]

        # 6. Build response -----------------------------------------------------
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Persist to search history (fire-and-forget flush)
        await SearchService._save_search_history(
            db=db,
            query=query,
            search_type="hybrid",
            result_count=len(final_results),
            org_id=org_id,
            user_id=user_id,
        )

        return SearchResponse(
            query=query,
            results=final_results,
            total_results=len(final_results),
            search_type="hybrid",
            latency_ms=latency_ms,
        )

    # ------------------------------------------------------------------
    # Chatbot search (search + FAQ + LLM answer)
    # ------------------------------------------------------------------

    @staticmethod
    async def chatbot_search(
        db: AsyncSession,
        query: str,
        scope_id: UUID,
        org_id: UUID,
        include_faq: bool = True,
        user_id: UUID | None = None,
        user_role: str | None = None,
        user_dept_id: UUID | None = None,
        as_user_view: bool = False,
    ) -> ChatbotSearchResponse:
        """Search scoped documents, optionally check FAQs, and generate an
        LLM-grounded answer.

        Parameters
        ----------
        db:
            Active database session.
        query:
            User question.
        scope_id:
            Search scope defining the chatbot's knowledge base.
        org_id:
            Organisation that owns the data.
        include_faq:
            When ``True`` the FAQ store is checked first; matching FAQ
            entries are included alongside the generated answer.
        user_id, user_role, user_dept_id, as_user_view:
            ``hybrid_search`` 로 그대로 전달되어 visibility 검사를 수행한다.
        """

        # Check FAQ store first ------------------------------------------------
        faq_matches: list[dict] | None = None
        if include_faq:
            faq_matches = await SearchService._check_faq(
                query=query,
                scope_id=scope_id,
                org_id=org_id,
            )

        # Retrieve relevant chunks ---------------------------------------------
        search_response = await SearchService.hybrid_search(
            db=db,
            query=query,
            scope_id=scope_id,
            doc_ids=None,
            org_id=org_id,
            max_results=10,
            user_id=user_id,
            user_role=user_role,
            user_dept_id=user_dept_id,
            as_user_view=as_user_view,
        )

        # Generate LLM answer --------------------------------------------------
        context_chunks = [r.content for r in search_response.results]
        answer = await SearchService._generate_answer(
            query=query,
            context_chunks=context_chunks,
            system_prompt=(
                "You are a helpful document-based chatbot. Answer the user's "
                "question using ONLY the provided context. If the context does "
                "not contain enough information, say so clearly."
            ),
        )

        # Build citations from top results -------------------------------------
        citations = SearchService._build_citations(search_response.results)

        return ChatbotSearchResponse(
            answer=answer,
            citations=citations,
            faq_matches=faq_matches,
        )

    # ------------------------------------------------------------------
    # QA search (search + LLM answer + citation enforcement + hallucination)
    # ------------------------------------------------------------------

    @staticmethod
    async def qa_search(
        db: AsyncSession,
        query: str,
        scope_id: UUID | None,
        doc_ids: list[UUID] | None,
        org_id: UUID,
        user_id: UUID | None = None,
        user_role: str | None = None,
        user_dept_id: UUID | None = None,
        as_user_view: bool = False,
    ) -> QASearchResponse:
        """Retrieve documents, generate an answer with enforced citations,
        and estimate a hallucination score.

        The LLM is instructed to include inline citations (e.g. ``[1]``,
        ``[2]``) referencing the source chunks.  A secondary check computes
        a hallucination score between 0 (fully faithful) and 1.

        Visibility 인자는 ``hybrid_search`` 로 전달되어 사용자 권한에 맞게
        검색 결과가 필터링된다.
        """

        settings = get_settings()

        # Retrieve relevant chunks
        search_response = await SearchService.hybrid_search(
            db=db,
            query=query,
            scope_id=scope_id,
            doc_ids=doc_ids,
            org_id=org_id,
            max_results=10,
            user_id=user_id,
            user_role=user_role,
            user_dept_id=user_dept_id,
            as_user_view=as_user_view,
        )

        context_chunks = [r.content for r in search_response.results]

        # Generate answer with citation enforcement
        answer = await SearchService._generate_answer(
            query=query,
            context_chunks=context_chunks,
            system_prompt=(
                "You are a precise question-answering system. Answer the "
                "question using ONLY the provided context. You MUST include "
                "inline citation markers [1], [2], etc. referencing the "
                "context passages. If the context is insufficient, state "
                "that explicitly."
            ),
        )

        # Build citations
        citations = SearchService._build_citations(search_response.results)

        # Hallucination check
        hallucination_score = await SearchService._check_hallucination(
            answer=answer,
            context_chunks=context_chunks,
        )

        return QASearchResponse(
            answer=answer,
            citations=citations,
            hallucination_score=hallucination_score,
            model_used=settings.llm_model,
        )

    # ------------------------------------------------------------------
    # Keyword-only search (BM25)
    # ------------------------------------------------------------------

    @staticmethod
    async def keyword_search(
        db: AsyncSession,
        query: str,
        scope_id: UUID | None,
        org_id: UUID,
        filters: dict | None = None,
        max_results: int = 10,
        user_id: UUID | None = None,
        user_role: str | None = None,
        user_dept_id: UUID | None = None,
        as_user_view: bool = False,
    ) -> SearchResponse:
        """Perform a BM25-only keyword search without dense retrieval.

        This is useful when the user explicitly wants lexical matching
        (exact terms, codes, identifiers, etc.).

        Visibility 권한 적용은 ``hybrid_search`` 와 동일한 ``as_user_view`` 룰을
        따른다.
        """

        start = time.perf_counter()

        doc_ids: list[UUID] | None = None
        if filters and "document_ids" in filters:
            raw_ids = filters["document_ids"]
            doc_ids = [UUID(str(d)) for d in raw_ids] if raw_ids else None

        # Visibility 권한 적용 (사용자 가시 문서 ID 사전 계산)
        effective_doc_ids = await SearchService._apply_visibility_scope(
            db=db,
            org_id=org_id,
            doc_ids=doc_ids,
            user_id=user_id,
            user_role=user_role,
            user_dept_id=user_dept_id,
            as_user_view=as_user_view,
        )

        # 가시 문서가 없으면 빈 결과 즉시 반환
        if effective_doc_ids is not None and len(effective_doc_ids) == 0:
            latency_ms = int((time.perf_counter() - start) * 1000)
            await SearchService._save_search_history(
                db=db,
                query=query,
                search_type="keyword",
                result_count=0,
                org_id=org_id,
                user_id=user_id,
            )
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_type="keyword",
                latency_ms=latency_ms,
            )

        sparse_results = await SearchService._sparse_bm25_search(
            query=query,
            org_id=org_id,
            scope_id=scope_id,
            doc_ids=effective_doc_ids,
            limit=max_results,
        )

        latency_ms = int((time.perf_counter() - start) * 1000)

        await SearchService._save_search_history(
            db=db,
            query=query,
            search_type="keyword",
            result_count=len(sparse_results),
            org_id=org_id,
            user_id=user_id,
        )

        return SearchResponse(
            query=query,
            results=sparse_results,
            total_results=len(sparse_results),
            search_type="keyword",
            latency_ms=latency_ms,
        )

    # ------------------------------------------------------------------
    # Search history
    # ------------------------------------------------------------------

    @staticmethod
    async def get_search_history(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> list[SearchHistoryItem]:
        """Return a paginated list of the user's recent search queries.

        Parameters
        ----------
        db:
            Active database session.
        user_id:
            Owner of the search-history entries.
        org_id:
            Organisation scope for multi-tenancy.
        page:
            1-based page number.
        size:
            Items per page.
        """

        from app.modules.search.models import SearchHistory

        offset = (page - 1) * size

        stmt = (
            select(SearchHistory)
            .where(
                SearchHistory.user_id == user_id,
                SearchHistory.organization_id == org_id,
            )
            .order_by(SearchHistory.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )

        result = await db.execute(stmt)
        rows = result.scalars().all()

        return [
            SearchHistoryItem(
                id=row.id,
                query=row.query,
                search_type=row.search_type,
                result_count=row.result_count,
                created_at=row.ins_dt,
            )
            for row in rows
        ]

    # ==================================================================
    # Private / helper methods
    # ==================================================================

    @staticmethod
    def _build_qdrant_filter(
        org_id: UUID,
        scope_id: UUID | None = None,
        doc_ids: list[UUID] | None = None,
    ) -> dict[str, Any]:
        """Construct a Qdrant filter payload scoped to the organisation.

        The filter always includes the organisation constraint.  When
        *scope_id* or *doc_ids* are provided they are added as additional
        ``must`` clauses.
        """

        must_clauses: list[dict[str, Any]] = [
            {
                "key": "organization_id",
                "match": {"value": str(org_id)},
            },
        ]

        if scope_id is not None:
            must_clauses.append(
                {
                    "key": "search_scope_id",
                    "match": {"value": str(scope_id)},
                }
            )

        if doc_ids:
            must_clauses.append(
                {
                    "key": "document_id",
                    "match": {
                        "any": [str(d) for d in doc_ids],
                    },
                }
            )

        return {"must": must_clauses}

    @staticmethod
    async def _get_embedding(text: str) -> list[float]:
        """Dense 임베딩 벡터를 생성한다.

        EMBEDDING_PROVIDER에 따라 OpenAI API 또는 내부 GPU 서비스를 사용한다.
        """

        settings = get_settings()

        try:
            import httpx

            # 프로바이더별 엔드포인트/모델 선택
            if settings.embedding_provider == "openai":
                url = "https://api.openai.com/v1/embeddings"
                model = settings.openai_embedding_model
                headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            else:
                url = f"{settings.vllm_url}/embeddings"
                model = settings.embedding_model
                headers = {"Authorization": f"Bearer {settings.openai_api_key or ''}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={"model": model, "input": text},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
        except Exception:
            logger.exception("Failed to obtain embedding, returning zeros")
            return [0.0] * settings.embedding_dimension

    @staticmethod
    async def _dense_search(
        query_embedding: list[float],
        qdrant_filter: dict[str, Any],
        collection: str,
        limit: int = 30,
    ) -> list[SearchResult]:
        """Query Qdrant for nearest neighbours using dense vectors."""

        try:
            import httpx

            settings = get_settings()
            qdrant_url = f"http://{settings.qdrant_host}:{settings.qdrant_port}"

            # Qdrant는 api-key 헤더가 없으면 401을 반환하므로 항상 전달한다
            headers: dict[str, str] = {
                "api-key": settings.qdrant_api_key or "",
            }

            # named vector "dense"를 사용하여 검색한다
            payload: dict[str, Any] = {
                "vector": {
                    "name": "dense",
                    "vector": query_embedding,
                },
                "filter": qdrant_filter if qdrant_filter else None,
                "limit": limit,
                "with_payload": True,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{qdrant_url}/collections/{collection}/points/search",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            results: list[SearchResult] = []
            for point in data.get("result", []):
                p = point.get("payload", {})
                results.append(
                    SearchResult(
                        document_id=p.get("document_id", ""),
                        document_name=p.get("document_name", ""),
                        chunk_id=p.get("chunk_id", point.get("id", "")),
                        chunk_index=p.get("chunk_index", 0),
                        content=p.get("content", ""),
                        score=point.get("score", 0.0),
                        page_number=p.get("page_number"),
                        section_title=p.get("section_title"),
                        chunk_type=p.get("chunk_type", "text"),
                        highlights=None,
                    )
                )
            return results

        except Exception:
            logger.exception("Dense search failed")
            return []

    @staticmethod
    async def _sparse_bm25_search(
        query: str,
        org_id: UUID,
        scope_id: UUID | None = None,
        doc_ids: list[UUID] | None = None,
        limit: int = 30,
    ) -> list[SearchResult]:
        """Perform a BM25 sparse search via PostgreSQL full-text search.

        Falls back gracefully to an empty list on errors so that the
        hybrid pipeline is not fully blocked by a sparse-search failure.
        """

        try:
            from sqlalchemy import text as sa_text

            from app.core.database import async_session_factory

            # SQL Injection 방지: 모든 값을 파라미터 바인딩으로 전달
            # 올바른 테이블명(tb_document_chunks, tb_documents) 사용
            ts_query = " & ".join(query.split())

            # 동적 WHERE 절을 안전하게 구성
            conditions = [
                "d.organization_id = :org_id",
                "dc.content ILIKE :like_query",
            ]
            params: dict[str, Any] = {
                "ts_query": ts_query,
                "org_id": str(org_id),
                "like_query": f"%{query}%",
                "limit": limit,
            }

            if scope_id:
                conditions.append("dc.search_scope_id = :scope_id")
                params["scope_id"] = str(scope_id)
            if doc_ids:
                conditions.append("dc.document_id = ANY(:doc_ids)")
                params["doc_ids"] = [str(d) for d in doc_ids]

            where_clause = " AND ".join(conditions)

            sql = sa_text(f"""
                SELECT
                    dc.document_id,
                    d.name AS document_name,
                    dc.id AS chunk_id,
                    dc.chunk_index,
                    dc.content,
                    1.0 AS score,
                    dc.page_number,
                    dc.section_title,
                    dc.chunk_type
                FROM tb_document_chunks dc
                JOIN tb_documents d ON d.id = dc.document_id
                WHERE {where_clause}
                ORDER BY dc.chunk_index
                LIMIT :limit
            """)

            async with async_session_factory() as session:
                result = await session.execute(sql, params)
                rows = result.fetchall()

            results: list[SearchResult] = []
            for row in rows:
                results.append(
                    SearchResult(
                        document_id=row.document_id,
                        document_name=row.document_name,
                        chunk_id=row.chunk_id,
                        chunk_index=row.chunk_index,
                        content=row.content,
                        score=float(row.score),
                        page_number=row.page_number,
                        section_title=row.section_title,
                        chunk_type=row.chunk_type or "text",
                        highlights=None,
                    )
                )
            return results

        except Exception:
            logger.exception("BM25 sparse search failed")
            return []

    @staticmethod
    def _rrf_fusion(
        dense_results: list[SearchResult],
        sparse_results: list[SearchResult],
        k: int = 60,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion of two ranked lists.

        Each result's fused score is the sum of ``1 / (k + rank)`` across
        all input lists in which it appears.  The constant *k* (default 60)
        controls the diminishing influence of lower-ranked items.
        """

        scores: dict[str, float] = {}
        result_map: dict[str, SearchResult] = {}

        for rank, r in enumerate(dense_results, start=1):
            key = str(r.chunk_id)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            result_map[key] = r

        for rank, r in enumerate(sparse_results, start=1):
            key = str(r.chunk_id)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in result_map:
                result_map[key] = r

        sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)

        fused: list[SearchResult] = []
        for key in sorted_keys:
            r = result_map[key]
            fused.append(
                SearchResult(
                    document_id=r.document_id,
                    document_name=r.document_name,
                    chunk_id=r.chunk_id,
                    chunk_index=r.chunk_index,
                    content=r.content,
                    score=scores[key],
                    page_number=r.page_number,
                    section_title=r.section_title,
                    chunk_type=r.chunk_type,
                    highlights=r.highlights,
                )
            )
        return fused

    @staticmethod
    async def _rerank_results(
        query: str,
        candidates: list[SearchResult],
    ) -> list[SearchResult]:
        """Re-rank candidates using a cross-encoder or LLM-based scoring.

        When an external reranker is unavailable the candidates are returned
        in their current (RRF-fused) order.
        """

        if not candidates:
            return candidates

        try:
            import httpx

            settings = get_settings()

            passages = [c.content for c in candidates]

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{settings.reranker_url}/rerank",
                    json={
                        "model": settings.reranker_model,
                        "query": query,
                        "documents": passages,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            rerank_scores = data.get("results", [])
            for i, entry in enumerate(rerank_scores):
                if i < len(candidates):
                    candidates[i] = SearchResult(
                        document_id=candidates[i].document_id,
                        document_name=candidates[i].document_name,
                        chunk_id=candidates[i].chunk_id,
                        chunk_index=candidates[i].chunk_index,
                        content=candidates[i].content,
                        score=float(entry.get("relevance_score", candidates[i].score)),
                        page_number=candidates[i].page_number,
                        section_title=candidates[i].section_title,
                        chunk_type=candidates[i].chunk_type,
                        highlights=candidates[i].highlights,
                    )

            candidates.sort(key=lambda c: c.score, reverse=True)
            return candidates

        except Exception:
            logger.warning("Reranking unavailable, returning fused order")
            return candidates

    @staticmethod
    async def _generate_answer(
        query: str,
        context_chunks: list[str],
        system_prompt: str | None = None,
    ) -> str:
        """Generate an LLM answer grounded in *context_chunks*.

        Uses the configured LLM endpoint (OpenAI-compatible API).
        """

        settings = get_settings()

        # Build numbered context
        numbered = "\n\n".join(
            f"[{i + 1}] {chunk}" for i, chunk in enumerate(context_chunks)
        )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append(
            {
                "role": "user",
                "content": (
                    f"Context:\n{numbered}\n\n"
                    f"Question: {query}\n\n"
                    "Answer:"
                ),
            }
        )

        try:
            import httpx

            # LLM 프로바이더별 엔드포인트 선택
            if settings.llm_provider == "openai":
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            else:
                url = f"{settings.vllm_url}/chat/completions"
                headers = {"Authorization": f"Bearer {settings.openai_api_key or ''}"}

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "model": settings.llm_model,
                        "messages": messages,
                        "temperature": settings.llm_temperature,
                        "max_tokens": settings.llm_max_tokens,
                    },
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

        except Exception:
            logger.exception("LLM answer generation failed")
            return (
                "I was unable to generate an answer at this time. "
                "Please try again later."
            )

    @staticmethod
    async def _check_hallucination(
        answer: str,
        context_chunks: list[str],
    ) -> float:
        """Estimate the hallucination score of *answer* against context.

        Returns a float between 0.0 (fully faithful) and 1.0 (likely
        hallucinated).  Uses a secondary LLM call to judge faithfulness.
        """

        settings = get_settings()

        context_text = "\n\n".join(context_chunks)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a hallucination detection system. Given a "
                    "context and an answer, evaluate whether the answer is "
                    "faithful to the context. Respond with ONLY a number "
                    "between 0.0 (completely faithful) and 1.0 (completely "
                    "hallucinated)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context_text}\n\n"
                    f"Answer:\n{answer}\n\n"
                    "Hallucination score (0.0 to 1.0):"
                ),
            },
        ]

        try:
            import httpx

            # LLM 프로바이더별 엔드포인트 선택
            if settings.llm_provider == "openai":
                llm_url = "https://api.openai.com/v1/chat/completions"
                llm_headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            else:
                llm_url = f"{settings.vllm_url}/chat/completions"
                llm_headers = {"Authorization": f"Bearer {settings.openai_api_key or ''}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    llm_url,
                    json={
                        "model": settings.llm_model,
                        "messages": messages,
                        "temperature": 0.0,
                        "max_tokens": 10,
                    },
                    headers=llm_headers,
                )
                resp.raise_for_status()
                data = resp.json()
                score_text = data["choices"][0]["message"]["content"].strip()
                return max(0.0, min(1.0, float(score_text)))

        except Exception:
            logger.warning("Hallucination check failed, returning default 0.5")
            return 0.5

    @staticmethod
    async def _check_faq(
        query: str,
        scope_id: UUID,
        org_id: UUID,
    ) -> list[dict] | None:
        """Check the FAQ store for matching entries.

        Returns a list of matching FAQ dicts or ``None`` when nothing
        matches or the FAQ service is unavailable.
        """

        try:
            from app.core.database import async_session_factory
            from sqlalchemy import text as sa_text

            sql = sa_text("""
                SELECT id, question, answer, score
                FROM (
                    SELECT
                        f.id,
                        f.question,
                        f.answer,
                        similarity(f.question, :query) AS score
                    FROM faqs f
                    WHERE f.organization_id = :org_id
                        AND f.search_scope_id = :scope_id
                        AND f.is_active = true
                ) sub
                WHERE score > 0.3
                ORDER BY score DESC
                LIMIT 5
            """)

            async with async_session_factory() as session:
                result = await session.execute(
                    sql,
                    {
                        "query": query,
                        "org_id": str(org_id),
                        "scope_id": str(scope_id),
                    },
                )
                rows = result.fetchall()

            if not rows:
                return None

            return [
                {
                    "id": str(row.id),
                    "question": row.question,
                    "answer": row.answer,
                    "score": float(row.score),
                }
                for row in rows
            ]

        except Exception:
            logger.warning("FAQ lookup failed, skipping")
            return None

    @staticmethod
    def _build_citations(results: list[SearchResult]) -> list[Citation]:
        """Convert a list of ``SearchResult`` objects to ``Citation`` objects."""

        citations: list[Citation] = []
        seen_chunks: set[str] = set()

        for r in results:
            key = str(r.chunk_id)
            if key in seen_chunks:
                continue
            seen_chunks.add(key)

            snippet = r.content[:500] if len(r.content) > 500 else r.content

            citations.append(
                Citation(
                    document_id=r.document_id,
                    document_name=r.document_name,
                    page_number=r.page_number,
                    snippet=snippet,
                    relevance_score=min(r.score, 1.0),
                )
            )

        return citations

    # ------------------------------------------------------------------
    # Visibility 권한 헬퍼
    # ------------------------------------------------------------------

    @staticmethod
    async def _apply_visibility_scope(
        db: AsyncSession,
        *,
        org_id: UUID,
        doc_ids: list[UUID] | None,
        user_id: UUID | None,
        user_role: str | None,
        user_dept_id: UUID | None,
        as_user_view: bool,
    ) -> list[UUID] | None:
        """검색 대상에 대해 사용자 visibility 권한을 적용한다.

        반환값 규칙:
        - ``None`` : 권한 제약 없음 (admin bypass 또는 visibility kill switch).
          호출자는 doc_ids 필터를 기존대로 사용해야 한다.
        - 비어있지 않은 ``list[UUID]`` : 사용자가 접근 가능한 문서 ID 목록.
          호출자는 이 목록만으로 Qdrant/SQL 필터를 구성해야 한다.
        - 빈 ``list`` : 사용자가 접근 가능한 문서가 0건. 호출자는 즉시 빈 결과를
          반환해야 한다 (검색 자체를 건너뛴다).

        구현 메모:
        - documents 모듈의 ``_build_list_visibility_scope`` 헬퍼를 재사용해
          공개범위별 OR 절을 가져온 뒤 ``Document.organization_id`` 와 함께
          단일 SELECT 로 가시 ID 집합을 계산한다.
        - 호출자가 명시적으로 doc_ids 를 지정한 경우엔 가시 집합과 교집합을
          취해 권한 밖 ID 가 새지 않도록 한다.
        - P4 (Service → Service 직접 호출 금지) 대응: DocumentService 의
          staticmethod 헬퍼만 import 해 사용하며, 비즈니스 로직 메서드는
          호출하지 않는다.
        """
        # documents 모듈의 staticmethod 헬퍼 (지연 import — 순환 import 회피)
        from app.modules.documents.models import Document
        from app.modules.documents.service import (
            DocumentService,
            _visibility_disabled,
        )

        # Kill switch 가 켜져 있으면 모든 문서 허용
        if _visibility_disabled():
            return doc_ids

        admin_roles = {"super_admin", "admin", "org_admin"}
        is_admin = user_role in admin_roles

        # 운영자는 기본적으로 bypass; 단 사용자 화면(as_user_view=True) 에선
        # 일반 사용자처럼 visibility 적용
        if is_admin and not as_user_view:
            return doc_ids

        # 비로그인 / user_role 정보가 없는 경우 — 안전하게 빈 결과 반환.
        # 운영 환경에서 user_id 가 None 이라면 인증 누락이므로 fail-closed.
        if user_id is None or user_role is None:
            logger.warning(
                "Search visibility check requires user_id/user_role; "
                "returning empty result. user_id=%s role=%s",
                user_id, user_role,
            )
            return []

        # 공개범위별 절 빌드 (admin 이 아닌 일반 사용자 경로)
        scope_clauses = await DocumentService._build_list_visibility_scope(
            db,
            user_id=user_id,
            user_role=user_role,
            user_dept_id=user_dept_id,
            org_id=org_id,
        )

        # 공개범위 절이 0개 (이론상 업로더 본인 절은 항상 들어가므로 발생 어려움)
        if not scope_clauses:
            return []

        # 가시 문서 ID SELECT
        stmt = (
            select(Document.id)
            .where(
                Document.organization_id == org_id,
                or_(*scope_clauses),
            )
        )
        # 호출자가 doc_ids 를 명시한 경우 — 권한 밖 ID 가 새지 않도록 교집합
        if doc_ids:
            stmt = stmt.where(Document.id.in_(doc_ids))

        result = await db.execute(stmt)
        visible_ids: list[UUID] = [row[0] for row in result.all()]
        return visible_ids

    @staticmethod
    async def _save_search_history(
        db: AsyncSession,
        query: str,
        search_type: str,
        result_count: int,
        org_id: UUID,
        user_id: UUID | None = None,
    ) -> None:
        """검색 기록을 저장한다.

        user_id를 포함하여 누가 검색했는지 추적할 수 있도록 한다.
        오류가 발생해도 주 검색 흐름에 영향을 주지 않도록 예외를 전파하지 않는다.
        """

        try:
            from app.modules.search.models import SearchHistory

            entry = SearchHistory(
                query=query,
                search_type=search_type,
                result_count=result_count,
                organization_id=org_id,
                user_id=user_id,
            )
            db.add(entry)
            await db.flush()
        except Exception:
            logger.warning("Failed to save search history entry")
