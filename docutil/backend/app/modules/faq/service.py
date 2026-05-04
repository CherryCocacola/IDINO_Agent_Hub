"""Business logic for FAQ management."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import FAQEntry as FAQ
from .schemas import FAQCreate, FAQUpdate


class FAQService:
    """Stateless service methods for FAQ CRUD and search."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_faq(
        db: AsyncSession,
        org_id: UUID,
        data: FAQCreate,
    ) -> FAQ:
        """Create a new FAQ entry."""
        faq = FAQ(
            organization_id=org_id,
            search_scope_id=data.search_scope_id,
            question=data.question,
            answer=data.answer,
            category=data.category,
            display_order=data.display_order,
        )
        db.add(faq)
        await db.flush()
        await db.refresh(faq)
        return faq

    # ------------------------------------------------------------------
    # Read (single)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_faq(
        db: AsyncSession,
        faq_id: UUID,
        org_id: UUID,
    ) -> FAQ:
        """Return a single FAQ by ID or raise 404."""
        result = await db.execute(
            select(FAQ).where(
                FAQ.id == faq_id,
                FAQ.organization_id == org_id,
            )
        )
        faq = result.scalar_one_or_none()
        if faq is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FAQ '{faq_id}' not found.",
            )
        return faq

    # ------------------------------------------------------------------
    # List (paginated, optional scope filter)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_faqs(
        db: AsyncSession,
        org_id: UUID,
        page: int = 1,
        size: int = 20,
        scope_id: UUID | None = None,
        category: str | None = None,
    ) -> tuple[list[FAQ], int]:
        """Return a paginated list of FAQs.

        Optionally filtered by ``scope_id`` and/or ``category``.
        Returns ``(items, total_count)``.
        """
        base_query = select(FAQ).where(FAQ.organization_id == org_id)

        if scope_id is not None:
            base_query = base_query.where(FAQ.search_scope_id == scope_id)
        if category is not None:
            base_query = base_query.where(FAQ.category == category)

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Paginated items
        offset = (page - 1) * size
        items_query = (
            base_query
            .order_by(FAQ.display_order.asc(), FAQ.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_query)
        items = list(result.scalars().all())

        return items, total

    # ------------------------------------------------------------------
    # Get by scope
    # ------------------------------------------------------------------

    @staticmethod
    async def get_by_scope(
        db: AsyncSession,
        scope_id: UUID,
    ) -> list[FAQ]:
        """Return all active FAQs for a given search scope, ordered by
        ``display_order``.
        """
        result = await db.execute(
            select(FAQ)
            .where(
                FAQ.search_scope_id == scope_id,
                FAQ.is_active.is_(True),
            )
            .order_by(FAQ.display_order.asc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @staticmethod
    async def search_faq(
        db: AsyncSession,
        org_id: UUID,
        query: str,
    ) -> list[FAQ]:
        """Perform a case-insensitive text search on question and answer fields.

        Returns active FAQs matching the query within the organisation.
        """
        pattern = f"%{query}%"
        result = await db.execute(
            select(FAQ)
            .where(
                FAQ.organization_id == org_id,
                FAQ.is_active.is_(True),
                or_(
                    FAQ.question.ilike(pattern),
                    FAQ.answer.ilike(pattern),
                ),
            )
            .order_by(FAQ.display_order.asc())
            .limit(50)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update_faq(
        db: AsyncSession,
        faq_id: UUID,
        org_id: UUID,
        data: FAQUpdate,
    ) -> FAQ:
        """Update an existing FAQ entry with the supplied fields."""
        faq = await FAQService.get_faq(db, faq_id, org_id)

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(faq, field, value)

        await db.flush()
        await db.refresh(faq)
        return faq

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_faq(
        db: AsyncSession,
        faq_id: UUID,
        org_id: UUID,
    ) -> None:
        """Hard-delete an FAQ entry by ID. Raises 404 if not found."""
        faq = await FAQService.get_faq(db, faq_id, org_id)
        await db.delete(faq)
        await db.flush()
