"""
FastAPI router for projects, boards, and folders.

Route hierarchy
---------------
- ``/projects``                             -- project CRUD
- ``/projects/{project_id}/boards``         -- board CRUD (nested under project)
- ``/boards/{board_id}/folders``            -- folder CRUD (nested under board)

Access control
--------------
- **read** endpoints require ``member`` role or above.
- **create / update / delete** endpoints require ``admin`` or ``org_admin``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import TokenData
from app.modules.audit.service import AuditService

from .schemas import (
    BoardCreate,
    BoardListResponse,
    BoardResponse,
    BoardUpdate,
    FolderCreate,
    FolderListResponse,
    FolderResponse,
    FolderUpdate,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from .service import BoardService, FolderService, ProjectService

router = APIRouter(prefix="", tags=["projects"])

# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------
_require_admin = require_role(["super_admin", "admin", "org_admin"])
_require_member = require_role(["super_admin", "admin", "org_admin", "manager", "member", "editor", "viewer"])


# ===========================================================================
# Project endpoints
# ===========================================================================


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """List all projects in the user's organisation (paginated)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    items, total = await ProjectService.get_projects(
        db, organization_id=current_user.organization_id, page=page, size=size,
    )
    return ProjectListResponse(items=items, total=total, page=page, size=size)


@router.get("/projects/tree")
async def get_projects_tree(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Get a tree view of all projects with their boards and folders."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    tree = await ProjectService.get_projects_tree(
        db, organization_id=current_user.organization_id
    )
    return tree


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Create a new project (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    project = await ProjectService.create_project(
        db,
        name=body.name,
        description=body.description,
        allow_original_download=body.allow_original_download,
        organization_id=current_user.organization_id,
        created_by=current_user.user_id,
    )
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Retrieve a single project by ID."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return await ProjectService.get_project(
        db, project_id=project_id, organization_id=current_user.organization_id,
    )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Update a project (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return await ProjectService.update_project(
        db,
        project_id=project_id,
        organization_id=current_user.organization_id,
        data=body.model_dump(exclude_unset=True),
    )


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Delete a project (admin+ only)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    await ProjectService.delete_project(
        db, project_id=project_id, organization_id=current_user.organization_id,
    )


# ===========================================================================
# Board endpoints (nested under /projects/{project_id}/boards)
# ===========================================================================


@router.get(
    "/projects/{project_id}/boards",
    response_model=BoardListResponse,
)
async def list_boards(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """List all boards in a project (paginated)."""
    items, total = await BoardService.get_boards(
        db, project_id=project_id, page=page, size=size,
    )
    return BoardListResponse(items=items, total=total, page=page, size=size)


@router.post(
    "/projects/{project_id}/boards",
    response_model=BoardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_board(
    project_id: UUID,
    body: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Create a new board inside a project (admin+ only)."""
    return await BoardService.create_board(
        db,
        project_id=project_id,
        name=body.name,
        description=body.description,
        created_by=current_user.user_id,
    )


@router.get(
    "/projects/{project_id}/boards/{board_id}",
    response_model=BoardResponse,
)
async def get_board(
    project_id: UUID,
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Retrieve a single board by ID."""
    return await BoardService.get_board(
        db, board_id=board_id, project_id=project_id,
    )


@router.put(
    "/projects/{project_id}/boards/{board_id}",
    response_model=BoardResponse,
)
async def update_board(
    project_id: UUID,
    board_id: UUID,
    body: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Update a board (admin+ only)."""
    return await BoardService.update_board(
        db,
        board_id=board_id,
        project_id=project_id,
        data=body.model_dump(exclude_unset=True),
    )


@router.delete(
    "/projects/{project_id}/boards/{board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_board(
    project_id: UUID,
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Delete a board (admin+ only)."""
    await BoardService.delete_board(
        db, board_id=board_id, project_id=project_id,
    )


# ===========================================================================
# Folder endpoints (nested under /boards/{board_id}/folders)
# ===========================================================================


@router.get(
    "/boards/{board_id}/folders",
    response_model=FolderListResponse,
)
async def list_folders(
    board_id: UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """List all folders in a board (paginated)."""
    items, total = await FolderService.get_folders(
        db, board_id=board_id, page=page, size=size,
    )
    return FolderListResponse(items=items, total=total, page=page, size=size)


@router.post(
    "/boards/{board_id}/folders",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_folder(
    board_id: UUID,
    body: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Create a new folder inside a board (admin+ only)."""
    return await FolderService.create_folder(
        db,
        board_id=board_id,
        name=body.name,
        description=body.description,
        created_by=current_user.user_id,
    )


@router.get(
    "/boards/{board_id}/folders/{folder_id}",
    response_model=FolderResponse,
)
async def get_folder(
    board_id: UUID,
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Retrieve a single folder by ID."""
    return await FolderService.get_folder(
        db, folder_id=folder_id, board_id=board_id,
    )


@router.put(
    "/boards/{board_id}/folders/{folder_id}",
    response_model=FolderResponse,
)
async def update_folder(
    board_id: UUID,
    folder_id: UUID,
    body: FolderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Update a folder (admin+ only)."""
    return await FolderService.update_folder(
        db,
        folder_id=folder_id,
        board_id=board_id,
        data=body.model_dump(exclude_unset=True),
    )


@router.delete(
    "/boards/{board_id}/folders/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_folder(
    board_id: UUID,
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """Delete a folder (admin+ only)."""
    await FolderService.delete_folder(
        db, folder_id=folder_id, board_id=board_id,
    )


# ===========================================================================
# Project members and departments
# ===========================================================================


@router.get("/projects/{project_id}/members")
async def list_project_members(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Return users who are members of this project."""
    from sqlalchemy import text

    result = await db.execute(
        text(
            "SELECT u.id, u.username, u.email, u.role "
            "FROM tb_project_members pm "
            "JOIN tb_users u ON pm.user_id = u.id "
            "WHERE pm.project_id = :pid"
        ),
        {"pid": project_id},
    )
    return [
        {"id": str(row.id), "username": row.username, "email": row.email, "role": row.role}
        for row in result.all()
    ]


# ---------------------------------------------------------------------------
# Project member mutation (트랙 #101 F8)
# ---------------------------------------------------------------------------
#
# - POST   /projects/{project_id}/members          → 201 ProjectMemberResponse
# - DELETE /projects/{project_id}/members/{user_id} → 204
#
# 권한: admin / org_admin / super_admin (_require_admin).
# 감사 로그: project.member.add / project.member.remove (best-effort — 실패 시 무시).
# ---------------------------------------------------------------------------


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    body: ProjectMemberCreate,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """프로젝트에 사용자 추가 (admin+ 전용, 트랙 #101 F8)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    created = await ProjectService.add_member(
        db,
        project_id=project_id,
        user_id=body.user_id,
        role=body.role,
        organization_id=current_user.organization_id,
    )

    # 감사 로그 — 실패가 주 흐름을 막지 않도록 swallow.
    try:
        await AuditService.create_log(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.user_id,
            action="project.member.add",
            resource_type="project",
            resource_id=str(project_id),
            details={"user_id": str(body.user_id), "role": created["role"]},
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass

    return created


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """프로젝트에서 사용자 제거 (admin+ 전용, 트랙 #101 F8)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    await ProjectService.remove_member(
        db,
        project_id=project_id,
        user_id=user_id,
        organization_id=current_user.organization_id,
    )

    try:
        await AuditService.create_log(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.user_id,
            action="project.member.remove",
            resource_type="project",
            resource_id=str(project_id),
            details={"user_id": str(user_id)},
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass


@router.get("/projects/{project_id}/departments")
async def list_project_departments(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Return departments participating in this project."""
    from sqlalchemy import text

    result = await db.execute(
        text(
            "SELECT d.id, d.name, d.path, d.depth "
            "FROM tb_project_departments pd "
            "JOIN tb_departments d ON pd.department_id = d.id "
            "WHERE pd.project_id = :pid"
        ),
        {"pid": project_id},
    )
    return [
        {"id": str(row.id), "name": row.name, "path": row.path, "depth": row.depth}
        for row in result.all()
    ]
