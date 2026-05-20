"""
FastAPI router for search scopes.

Endpoints
---------
- ``GET    /search-scopes``                    -- list (paginated)
- ``POST   /search-scopes``                    -- create
- ``GET    /search-scopes/{id}``               -- detail
- ``PUT    /search-scopes/{id}``               -- update metadata
- ``DELETE /search-scopes/{id}``               -- delete
- ``PUT    /search-scopes/{id}/environment``   -- update environment settings
- ``GET    /search-scopes/{id}/valid-id``      -- get embed UUID

Access control
--------------
- **read** endpoints require ``member`` role or above.
- **create / update / delete** endpoints require ``admin`` or ``org_admin``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.security import TokenData

from .schemas import (
    LocationOption,
    SearchScopeCreate,
    SearchScopeEnvironment,
    SearchScopeListResponse,
    SearchScopeOption,
    SearchScopeResponse,
    SearchScopeUpdate,
)
from .service import SearchScopeService

router = APIRouter(prefix="", tags=["search-scopes"])

# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------
_require_admin = require_role(["super_admin", "admin", "org_admin"])
_require_member = require_role(["super_admin", "admin", "org_admin", "manager", "member", "editor", "viewer", "user"])


# ===========================================================================
# List search scopes
# ===========================================================================


@router.get("/search-scopes", response_model=SearchScopeListResponse)
async def list_search_scopes(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """List all search scopes in the user's organisation (paginated)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    items, total = await SearchScopeService.get_search_scopes(
        db,
        organization_id=current_user.organization_id,
        page=page,
        size=size,
    )
    return SearchScopeListResponse(
        items=items, total=total, page=page, size=size,
    )


# ===========================================================================
# List search scope options (simplified, for dropdowns)
# ===========================================================================


@router.get(
    "/search-scopes/options",
    response_model=list[SearchScopeOption],
)
async def list_search_scope_options(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Return a simplified list of search scopes for dropdown selectors."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    from sqlalchemy import select as sa_select

    SearchScope = __import__(
        "app.modules.search_scopes.models", fromlist=["SearchScope"]
    ).SearchScope

    stmt = (
        sa_select(SearchScope.id, SearchScope.name, SearchScope.location_path)
        .where(SearchScope.organization_id == current_user.organization_id)
        .order_by(SearchScope.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        SearchScopeOption(id=row.id, name=row.name, location_path=row.location_path)
        for row in rows
    ]


# ===========================================================================
# List available locations for scope assignment
# ===========================================================================


@router.get(
    "/search-scopes/locations",
    response_model=list[LocationOption],
)
async def list_locations(
    location_type: str = Query(
        ..., description="Location type: 'project', 'board', or 'folder'."
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Return available projects, boards, or folders for scope assignment."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    from sqlalchemy import select as sa_select

    org_id = current_user.organization_id
    items: list[LocationOption] = []

    if location_type == "project":
        from app.modules.projects.models import Project

        stmt = (
            sa_select(Project)
            .where(Project.organization_id == org_id)
            .order_by(Project.name)
        )
        result = await db.execute(stmt)
        for p in result.scalars().all():
            items.append(LocationOption(
                id=p.id, name=p.name, type="project", path=p.name,
            ))

    elif location_type == "board":
        from app.modules.projects.models import Board, Project

        stmt = (
            sa_select(Board, Project.name.label("project_name"))
            .join(Project, Board.project_id == Project.id)
            .where(Project.organization_id == org_id)
            .order_by(Project.name, Board.name)
        )
        result = await db.execute(stmt)
        for row in result.all():
            board = row[0]
            project_name = row[1]
            items.append(LocationOption(
                id=board.id,
                name=board.name,
                type="board",
                path=f"{project_name} / {board.name}",
            ))

    elif location_type == "folder":
        from app.modules.projects.models import Board, Folder, Project

        stmt = (
            sa_select(
                Folder,
                Board.name.label("board_name"),
                Project.name.label("project_name"),
            )
            .join(Board, Folder.board_id == Board.id)
            .join(Project, Board.project_id == Project.id)
            .where(Project.organization_id == org_id)
            .order_by(Project.name, Board.name, Folder.name)
        )
        result = await db.execute(stmt)
        for row in result.all():
            folder = row[0]
            board_name = row[1]
            project_name = row[2]
            items.append(LocationOption(
                id=folder.id,
                name=folder.name,
                type="folder",
                path=f"{project_name} / {board_name} / {folder.name}",
            ))

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="location_type must be 'project', 'board', or 'folder'.",
        )

    return items


# ===========================================================================
# Create search scope
# ===========================================================================


@router.post(
    "/search-scopes",
    response_model=SearchScopeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_search_scope(
    body: SearchScopeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Create a new search scope (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    scope = await SearchScopeService.create_search_scope(
        db,
        name=body.name,
        description=body.description,
        organization_id=current_user.organization_id,
        created_by=current_user.user_id,
        project_id=body.project_id,
        board_id=body.board_id,
        folder_id=body.folder_id,
    )

    # Apply optional environment fields if provided
    env_fields = body.model_dump(
        include={
            "chatbot_enabled", "qa_enabled", "keyword_search_enabled",
            "agent_enabled", "chunk_size", "chunk_overlap", "title_weight",
            "keyword_weight", "content_weight", "max_results",
            "similarity_threshold",
        },
        exclude_none=True,
    )
    if env_fields:
        scope = await SearchScopeService.update_environment(
            db,
            scope_id=scope.id,
            organization_id=current_user.organization_id,
            data=env_fields,
        )

    return scope


# ===========================================================================
# Get search scope
# ===========================================================================


@router.get(
    "/search-scopes/{scope_id}",
    response_model=SearchScopeResponse,
)
async def get_search_scope(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Retrieve a single search scope by ID."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return await SearchScopeService.get_search_scope(
        db,
        scope_id=scope_id,
        organization_id=current_user.organization_id,
    )


# ===========================================================================
# Update search scope
# ===========================================================================


@router.put(
    "/search-scopes/{scope_id}",
    response_model=SearchScopeResponse,
)
async def update_search_scope(
    scope_id: UUID,
    body: SearchScopeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Update a search scope's metadata (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return await SearchScopeService.update_search_scope(
        db,
        scope_id=scope_id,
        organization_id=current_user.organization_id,
        data=body.model_dump(exclude_unset=True),
    )


# ===========================================================================
# Delete search scope
# ===========================================================================


@router.delete(
    "/search-scopes/{scope_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_search_scope(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Delete a search scope (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    await SearchScopeService.delete_search_scope(
        db,
        scope_id=scope_id,
        organization_id=current_user.organization_id,
    )


# ===========================================================================
# Update environment settings
# ===========================================================================


@router.put(
    "/search-scopes/{scope_id}/environment",
    response_model=SearchScopeResponse,
)
async def update_search_scope_environment(
    scope_id: UUID,
    body: SearchScopeEnvironment,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Update the environment / tuning settings for a search scope (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return await SearchScopeService.update_environment(
        db,
        scope_id=scope_id,
        organization_id=current_user.organization_id,
        data=body.model_dump(exclude_unset=True),
    )


# ===========================================================================
# Get valid ID (for embed)
# ===========================================================================


@router.get("/search-scopes/{scope_id}/valid-id")
async def get_valid_id(
    scope_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Return the validated UUID of a search scope (for embed widgets)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    valid_id = await SearchScopeService.get_valid_id(
        db,
        scope_id=scope_id,
        organization_id=current_user.organization_id,
    )
    return {"id": valid_id}
