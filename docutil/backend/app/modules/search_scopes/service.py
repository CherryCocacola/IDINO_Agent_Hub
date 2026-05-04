"""
Service layer for search scopes.

Provides CRUD, environment-settings update, and a ``get_valid_id``
helper that returns the UUID suitable for embedding widgets.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Lazy model import
# ---------------------------------------------------------------------------


def _get_search_scope_model():
    from app.modules.search_scopes.models import SearchScope  # noqa: WPS433
    return SearchScope


# ---------------------------------------------------------------------------
# SearchScopeService
# ---------------------------------------------------------------------------


class SearchScopeService:
    """CRUD operations and helpers for search scopes."""

    # -- Create -------------------------------------------------------------

    @staticmethod
    async def create_search_scope(
        db: AsyncSession,
        *,
        name: str,
        organization_id: UUID,
        created_by: UUID,
        description: str | None = None,
        project_id: UUID | None = None,
        board_id: UUID | None = None,
        folder_id: UUID | None = None,
    ):
        """Create a new search scope within an organisation."""
        SearchScope = _get_search_scope_model()
        scope = SearchScope(
            name=name,
            description=description,
            organization_id=organization_id,
            created_by=created_by,
            project_id=project_id,
            board_id=board_id,
            folder_id=folder_id,
        )
        db.add(scope)
        await db.flush()
        await db.refresh(scope)
        return scope

    # -- Read (list) --------------------------------------------------------

    @staticmethod
    async def get_search_scopes(
        db: AsyncSession,
        *,
        organization_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """Return a paginated list of search scopes for the organisation."""
        SearchScope = _get_search_scope_model()

        count_stmt = (
            select(func.count())
            .select_from(SearchScope)
            .where(SearchScope.organization_id == organization_id)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * size
        items_stmt = (
            select(SearchScope)
            .where(SearchScope.organization_id == organization_id)
            .order_by(SearchScope.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Read (single) ------------------------------------------------------

    @staticmethod
    async def get_search_scope(
        db: AsyncSession,
        *,
        scope_id: UUID,
        organization_id: UUID,
    ):
        """Fetch a single search scope by ID, or 404."""
        SearchScope = _get_search_scope_model()
        stmt = select(SearchScope).where(
            SearchScope.id == scope_id,
            SearchScope.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        scope = result.scalar_one_or_none()
        if scope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Search scope {scope_id} not found.",
            )
        return scope

    # -- Update -------------------------------------------------------------

    @staticmethod
    async def update_search_scope(
        db: AsyncSession,
        *,
        scope_id: UUID,
        organization_id: UUID,
        data: dict,
    ):
        """Partially update a search scope. Returns the refreshed instance."""
        SearchScope = _get_search_scope_model()

        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update.",
            )

        stmt = (
            update(SearchScope)
            .where(
                SearchScope.id == scope_id,
                SearchScope.organization_id == organization_id,
            )
            .values(**update_data)
            .returning(SearchScope)
        )
        result = await db.execute(stmt)
        scope = result.scalar_one_or_none()
        if scope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Search scope {scope_id} not found.",
            )
        await db.flush()
        await db.refresh(scope)
        return scope

    # -- Delete -------------------------------------------------------------

    @staticmethod
    async def delete_search_scope(
        db: AsyncSession,
        *,
        scope_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a search scope."""
        SearchScope = _get_search_scope_model()
        stmt = delete(SearchScope).where(
            SearchScope.id == scope_id,
            SearchScope.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Search scope {scope_id} not found.",
            )
        await db.flush()

    # -- Update environment settings ----------------------------------------

    @staticmethod
    async def update_environment(
        db: AsyncSession,
        *,
        scope_id: UUID,
        organization_id: UUID,
        data: dict,
    ):
        """Update only the environment / tuning fields of a search scope.

        Accepts a dict whose keys correspond to
        ``SearchScopeEnvironment`` fields.
        """
        SearchScope = _get_search_scope_model()

        # Allowed environment columns
        env_columns = {
            "chatbot_enabled",
            "chatbot_faq_template",
            "qa_enabled",
            "qa_prompt_template",
            "qa_llm_model",
            "keyword_search_enabled",
            "agent_enabled",
            "chunk_size",
            "chunk_overlap",
            "title_weight",
            "keyword_weight",
            "content_weight",
            "max_results",
            "similarity_threshold",
        }

        update_data = {
            k: v for k, v in data.items()
            if k in env_columns and v is not None
        }
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No environment fields to update.",
            )

        stmt = (
            update(SearchScope)
            .where(
                SearchScope.id == scope_id,
                SearchScope.organization_id == organization_id,
            )
            .values(**update_data)
            .returning(SearchScope)
        )
        result = await db.execute(stmt)
        scope = result.scalar_one_or_none()
        if scope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Search scope {scope_id} not found.",
            )
        await db.flush()
        await db.refresh(scope)
        return scope

    # -- Get valid ID (for embed) -------------------------------------------

    @staticmethod
    async def get_valid_id(
        db: AsyncSession,
        *,
        scope_id: UUID,
        organization_id: UUID,
    ) -> UUID:
        """Return the scope UUID if it exists and belongs to the organisation.

        Intended for external embed / widget integrations that need to
        validate a scope identifier.
        """
        scope = await SearchScopeService.get_search_scope(
            db, scope_id=scope_id, organization_id=organization_id,
        )
        return scope.id
