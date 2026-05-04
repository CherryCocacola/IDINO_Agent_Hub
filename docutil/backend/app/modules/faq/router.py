"""FastAPI router for FAQ management endpoints.

All routes in this module are mounted under the ``/faq`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role

from .schemas import FAQCreate, FAQListResponse, FAQResponse, FAQUpdate
from .service import FAQService

router = APIRouter(prefix="", tags=["faq"])


# ---------------------------------------------------------------------------
# GET /faq  (all authenticated users)
# ---------------------------------------------------------------------------


@router.get(
    "/faq",
    response_model=FAQListResponse,
    summary="List FAQs",
    description=(
        "Return a paginated list of FAQ entries. "
        "Optionally filter by search scope or category."
    ),
)
async def list_faqs(
    page: int = Query(1, ge=1, description="Page number."),
    size: int = Query(20, ge=1, le=100, description="Items per page."),
    scope_id: UUID | None = Query(None, description="Filter by search scope."),
    category: str | None = Query(None, description="Filter by category."),
    q: str | None = Query(None, description="Text search on question/answer."),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FAQListResponse:
    """Retrieve FAQs for the current organisation."""
    if q is not None:
        items = await FAQService.search_faq(
            db, org_id=current_user.organization_id, query=q
        )
        return FAQListResponse(
            items=[FAQResponse.model_validate(f) for f in items],
            total=len(items),
            page=1,
            size=len(items),
        )

    items, total = await FAQService.get_faqs(
        db,
        org_id=current_user.organization_id,
        page=page,
        size=size,
        scope_id=scope_id,
        category=category,
    )
    return FAQListResponse(
        items=[FAQResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /faq  (admin+ only)
# ---------------------------------------------------------------------------


@router.post(
    "/faq",
    response_model=FAQResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an FAQ",
    description="Create a new FAQ entry within the current organisation.",
)
async def create_faq(
    data: FAQCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> FAQResponse:
    """Create a new FAQ."""
    faq = await FAQService.create_faq(
        db, org_id=current_user.organization_id, data=data
    )
    return FAQResponse.model_validate(faq)


# ---------------------------------------------------------------------------
# GET /faq/{faq_id}  (all authenticated users)
# ---------------------------------------------------------------------------


@router.get(
    "/faq/{faq_id}",
    response_model=FAQResponse,
    summary="Get a single FAQ",
    description="Retrieve a specific FAQ entry by its ID.",
)
async def get_faq(
    faq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> FAQResponse:
    """Retrieve a single FAQ."""
    faq = await FAQService.get_faq(
        db, faq_id=faq_id, org_id=current_user.organization_id
    )
    return FAQResponse.model_validate(faq)


# ---------------------------------------------------------------------------
# PUT /faq/{faq_id}  (admin+ only)
# ---------------------------------------------------------------------------


@router.put(
    "/faq/{faq_id}",
    response_model=FAQResponse,
    summary="Update an FAQ",
    description="Update an existing FAQ entry.",
)
async def update_faq(
    faq_id: UUID,
    data: FAQUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> FAQResponse:
    """Update an existing FAQ."""
    faq = await FAQService.update_faq(
        db,
        faq_id=faq_id,
        org_id=current_user.organization_id,
        data=data,
    )
    return FAQResponse.model_validate(faq)


# ---------------------------------------------------------------------------
# DELETE /faq/{faq_id}  (admin+ only)
# ---------------------------------------------------------------------------


@router.delete(
    "/faq/{faq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete an FAQ",
    description="Permanently remove an FAQ entry.",
)
async def delete_faq(
    faq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> None:
    """Delete an FAQ entry."""
    await FAQService.delete_faq(
        db, faq_id=faq_id, org_id=current_user.organization_id
    )
