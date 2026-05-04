"""
FastAPI router for search endpoints.

All routes in this module are mounted under the ``/search`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    CurrentUser,
    CurrentOrganizationId,
    RequireAdmin,
)
from app.core.security import TokenData

from .schemas import (
    ChatbotSearchRequest,
    ChatbotSearchResponse,
    KeywordSearchRequest,
    QASearchRequest,
    QASearchResponse,
    SearchHistoryItem,
    SearchRequest,
    SearchResponse,
    SearchTestRequest,
)
from .agentic_search import AgenticSearchService
from .service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["search"])


# ---------------------------------------------------------------------------
# POST /search -- Hybrid search
# ---------------------------------------------------------------------------


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Hybrid search",
    description=(
        "Execute a hybrid (dense + sparse + rerank) search across the "
        "organisation's indexed documents. Results can be scoped to a "
        "specific search scope or a set of document IDs."
    ),
)
async def search(
    payload: SearchRequest,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Run a hybrid search and return ranked results."""

    # 사용자 진입점이므로 admin 도 visibility 검사를 적용한다 (as_user_view=True)
    if payload.agentic:
        return await AgenticSearchService.agentic_search(
            db=db,
            query=payload.query,
            scope_id=payload.search_scope_id,
            doc_ids=payload.document_ids,
            org_id=org_id,
            max_results=payload.max_results,
            user_id=current_user.user_id,
            user_role=current_user.role,
            user_dept_id=current_user.department_id,
            as_user_view=True,
        )

    return await SearchService.hybrid_search(
        db=db,
        query=payload.query,
        scope_id=payload.search_scope_id,
        doc_ids=payload.document_ids,
        org_id=org_id,
        max_results=payload.max_results,
        user_id=current_user.user_id,
        user_role=current_user.role,
        user_dept_id=current_user.department_id,
        as_user_view=True,
    )


# ---------------------------------------------------------------------------
# POST /search/chatbot -- Chatbot search
# ---------------------------------------------------------------------------


@router.post(
    "/search/chatbot",
    response_model=ChatbotSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Chatbot search",
    description=(
        "Search scoped documents and generate an LLM-grounded answer "
        "suitable for chatbot interfaces. Optionally checks the FAQ "
        "store first."
    ),
)
async def chatbot_search(
    payload: ChatbotSearchRequest,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> ChatbotSearchResponse:
    """Search + LLM answer generation with optional FAQ check."""

    return await SearchService.chatbot_search(
        db=db,
        query=payload.query,
        scope_id=payload.search_scope_id,
        org_id=org_id,
        include_faq=payload.include_faq,
        user_id=current_user.user_id,
        user_role=current_user.role,
        user_dept_id=current_user.department_id,
        as_user_view=True,
    )


# ---------------------------------------------------------------------------
# POST /search/qa -- QA search with citations
# ---------------------------------------------------------------------------


@router.post(
    "/search/qa",
    response_model=QASearchResponse,
    status_code=status.HTTP_200_OK,
    summary="QA search with citations",
    description=(
        "Search documents and generate an LLM answer with enforced "
        "inline citations and a hallucination score."
    ),
)
async def qa_search(
    payload: QASearchRequest,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> QASearchResponse:
    """Search + LLM answer with citation enforcement + hallucination scoring."""

    return await SearchService.qa_search(
        db=db,
        query=payload.query,
        scope_id=payload.search_scope_id,
        doc_ids=payload.document_ids,
        org_id=org_id,
        user_id=current_user.user_id,
        user_role=current_user.role,
        user_dept_id=current_user.department_id,
        as_user_view=True,
    )


# ---------------------------------------------------------------------------
# POST /search/keyword -- Keyword search
# ---------------------------------------------------------------------------


@router.post(
    "/search/keyword",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Keyword search",
    description=(
        "BM25-only keyword search. Useful for exact-term or code lookups "
        "where lexical matching outperforms semantic retrieval."
    ),
)
async def keyword_search(
    payload: KeywordSearchRequest,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Keyword (BM25) search without dense retrieval."""

    return await SearchService.keyword_search(
        db=db,
        query=payload.query,
        scope_id=payload.search_scope_id,
        org_id=org_id,
        filters=payload.filters,
        user_id=current_user.user_id,
        user_role=current_user.role,
        user_dept_id=current_user.department_id,
        as_user_view=True,
    )


# ---------------------------------------------------------------------------
# GET /search/history -- Search history
# ---------------------------------------------------------------------------


@router.get(
    "/search/history",
    response_model=list[SearchHistoryItem],
    status_code=status.HTTP_200_OK,
    summary="Search history",
    description="Retrieve the current user's paginated search history.",
)
async def search_history(
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    size: int = Query(default=20, ge=1, le=100, description="Items per page."),
) -> list[SearchHistoryItem]:
    """Return the authenticated user's recent search queries."""

    return await SearchService.get_search_history(
        db=db,
        user_id=current_user.user_id,
        org_id=org_id,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /search/test -- Admin search test
# ---------------------------------------------------------------------------


@router.post(
    "/search/test",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin search test",
    description=(
        "Administrative endpoint for testing search quality against a "
        "specific scope. Requires admin role."
    ),
    dependencies=[RequireAdmin],
)
async def search_test(
    payload: SearchTestRequest,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Run a search test (admin only) and return results for evaluation."""

    # 운영자 검색 테스트 화면 — admin 은 visibility bypass (as_user_view=False)
    return await SearchService.hybrid_search(
        db=db,
        query=payload.query,
        scope_id=payload.search_scope_id,
        doc_ids=None,
        org_id=org_id,
        max_results=20,
        user_id=current_user.user_id,
        user_role=current_user.role,
        user_dept_id=current_user.department_id,
        as_user_view=False,
    )
