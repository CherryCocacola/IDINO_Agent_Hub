"""
Service layer for projects, boards, and folders.

Each service class encapsulates CRUD logic with proper organisation /
parent-entity scoping and async SQLAlchemy queries.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# SQLAlchemy models are expected to live in a shared ``models`` module.
# They are imported lazily here so that this service file can be loaded
# even before the full model graph is resolved.
# ---------------------------------------------------------------------------

def _get_project_model():
    from app.modules.projects.models import Project  # noqa: WPS433
    return Project


def _get_board_model():
    from app.modules.projects.models import Board  # noqa: WPS433
    return Board


def _get_folder_model():
    from app.modules.projects.models import Folder  # noqa: WPS433
    return Folder


def _get_project_member_model():
    from app.modules.projects.models import ProjectMember  # noqa: WPS433
    return ProjectMember


# ---------------------------------------------------------------------------
# ProjectService
# ---------------------------------------------------------------------------


class ProjectService:
    """CRUD operations for projects, scoped to an organisation."""

    # -- Create -------------------------------------------------------------

    @staticmethod
    async def create_project(
        db: AsyncSession,
        *,
        name: str,
        organization_id: UUID,
        created_by: UUID,
        description: str | None = None,
        allow_original_download: bool = True,
    ):
        """Create a new project within an organisation."""
        Project = _get_project_model()
        project = Project(
            name=name,
            description=description,
            allow_original_download=allow_original_download,
            organization_id=organization_id,
            created_by=created_by,
        )
        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    # -- Read (list) --------------------------------------------------------

    @staticmethod
    async def get_projects(
        db: AsyncSession,
        *,
        organization_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """Return a paginated list of projects for the given organisation."""
        Project = _get_project_model()

        # Total count
        count_stmt = (
            select(func.count())
            .select_from(Project)
            .where(Project.organization_id == organization_id)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        # Items
        offset = (page - 1) * size
        items_stmt = (
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Read (tree) --------------------------------------------------------

    @staticmethod
    async def get_projects_tree(
        db: AsyncSession,
        *,
        organization_id: UUID,
    ) -> list[dict]:
        """Return a tree structure of all projects with boards and folders."""
        Project = _get_project_model()
        Board = _get_board_model()
        Folder = _get_folder_model()

        # Fetch all projects
        projects_stmt = (
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.name)
        )
        projects_result = await db.execute(projects_stmt)
        projects = list(projects_result.scalars().all())

        tree = []
        for project in projects:
            # Fetch boards for this project
            boards_stmt = (
                select(Board)
                .where(Board.project_id == project.id)
                .order_by(Board.name)
            )
            boards_result = await db.execute(boards_stmt)
            boards = list(boards_result.scalars().all())

            board_list = []
            for board in boards:
                # Fetch folders for this board
                folders_stmt = (
                    select(Folder)
                    .where(Folder.board_id == board.id)
                    .order_by(Folder.name)
                )
                folders_result = await db.execute(folders_stmt)
                folders = list(folders_result.scalars().all())

                folder_list = [
                    {
                        "id": str(folder.id),
                        "name": folder.name,
                        "board_id": str(folder.board_id),
                    }
                    for folder in folders
                ]

                board_list.append({
                    "id": str(board.id),
                    "name": board.name,
                    "project_id": str(board.project_id),
                    "folders": folder_list,
                })

            tree.append({
                "id": str(project.id),
                "name": project.name,
                "boards": board_list,
            })

        return tree

    # -- Read (single) ------------------------------------------------------

    @staticmethod
    async def get_project(
        db: AsyncSession,
        *,
        project_id: UUID,
        organization_id: UUID,
    ):
        """Fetch a single project by ID within the organisation, or 404."""
        Project = _get_project_model()
        stmt = select(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found.",
            )
        return project

    # -- Update -------------------------------------------------------------

    @staticmethod
    async def update_project(
        db: AsyncSession,
        *,
        project_id: UUID,
        organization_id: UUID,
        data: dict,
    ):
        """Partially update a project. Returns the refreshed instance."""
        Project = _get_project_model()

        # Filter out None values so only supplied fields are updated
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update.",
            )

        stmt = (
            update(Project)
            .where(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
            .values(**update_data)
            .returning(Project)
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found.",
            )
        await db.flush()
        await db.refresh(project)
        return project

    # -- Delete -------------------------------------------------------------

    @staticmethod
    async def delete_project(
        db: AsyncSession,
        *,
        project_id: UUID,
        organization_id: UUID,
    ) -> None:
        """Delete a project (cascades handled at DB level)."""
        Project = _get_project_model()
        stmt = delete(Project).where(
            Project.id == project_id,
            Project.organization_id == organization_id,
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found.",
            )
        await db.flush()

    # -----------------------------------------------------------------------
    # Project members (트랙 #101 F8) — 프로젝트 ↔ 사용자 매핑
    # -----------------------------------------------------------------------
    #
    # 운영 메모:
    #   1. tb_users 는 트랙 #98 phase 3 이후 VIEW 다 (AgentHub User 마스터 →
    #      DocUtil document_utilization 스키마로 read-only 투영). PG 는 VIEW 를
    #      가리키는 FK 를 허용하지 않으므로 ProjectMember.user_id 에는 FK 가 없다.
    #      → 본 서비스가 user 존재 검증을 책임진다(tb_users SELECT 1).
    #   2. UniqueConstraint(project_id, user_id) 가 있으므로 중복 INSERT 는
    #      IntegrityError → 409 로 매핑한다.
    #   3. project 존재 여부도 함께 검증(404) — FK 가 살아 있긴 하나 명시적 404 가
    #      운영자 UX 에 친화적이다.
    # -----------------------------------------------------------------------

    @staticmethod
    async def add_member(
        db: AsyncSession,
        *,
        project_id: UUID,
        user_id: UUID,
        role: str = "member",
        organization_id: UUID,
    ):
        """프로젝트에 사용자 추가 (트랙 #101 F8).

        - 동일 (project_id, user_id) 중복 → 409.
        - 프로젝트 미존재 → 404.
        - 사용자 미존재(tb_users VIEW SELECT 결과 0건) → 404.
        - 반환은 username/email 포함 평탄 dict (ProjectMemberResponse 호환).
        """
        # role 화이트리스트 (router 가 우선 검증하지만 service 도 방어)
        normalized_role = (role or "member").strip().lower()
        if normalized_role not in {"member", "manager"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{role}'. Allowed: ['member', 'manager'].",
            )

        # 1. project 존재 + org scope 검증
        await ProjectService.get_project(
            db, project_id=project_id, organization_id=organization_id,
        )

        # 2. user 존재 검증 (tb_users VIEW)
        user_row = await db.execute(
            text(
                "SELECT id, username, email "
                "FROM tb_users WHERE id = :uid AND organization_id = :oid"
            ),
            {"uid": user_id, "oid": organization_id},
        )
        user = user_row.first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found in organization.",
            )

        # 3. INSERT (중복 → IntegrityError → 409)
        ProjectMember = _get_project_member_model()
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=normalized_role,
        )
        db.add(member)
        try:
            await db.flush()
        except IntegrityError as exc:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"User {user_id} is already a member of project {project_id}."
                ),
            ) from exc
        await db.refresh(member)

        # 트랙 #113 (2026-05-27): 명시적 commit — get_db() cleanup 이 yield 후
        # commit 하므로 HTTP 201 응답 후에야 transaction commit 됨. AgentHub 가
        # 즉시 GET 호출 시 commit 전 SELECT → stale (PostgreSQL Read Committed).
        # 명시 commit 으로 HTTP 응답 전에 transaction 가시화 보장.
        await db.commit()

        return {
            "id": member.id,
            "project_id": member.project_id,
            "user_id": member.user_id,
            "username": user.username,
            "email": user.email,
            "role": member.role,
        }

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        *,
        project_id: UUID,
        user_id: UUID,
        organization_id: UUID,
    ) -> None:
        """프로젝트에서 사용자 제거 (트랙 #101 F8).

        - 매핑 미존재 → 404.
        - project 존재/org scope 는 사전 검증(통합 보안 — 다른 조직의
          멤버를 우연히 건드리지 않도록).
        """
        # 1. project 존재 + org scope 검증 (404)
        await ProjectService.get_project(
            db, project_id=project_id, organization_id=organization_id,
        )

        # 2. DELETE
        ProjectMember = _get_project_member_model()
        stmt = delete(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Project member ({project_id}, {user_id}) not found."
                ),
            )
        await db.flush()
        # 트랙 #113 (2026-05-27): 명시적 commit — get_db() cleanup 이 yield 후 commit
        # 하므로 HTTP 204 응답 후에야 transaction commit. AgentHub 즉시 GET 시 stale.
        # 명시 commit 으로 HTTP 응답 전 transaction 가시화.
        await db.commit()


# ---------------------------------------------------------------------------
# BoardService
# ---------------------------------------------------------------------------


class BoardService:
    """CRUD operations for boards, scoped to a parent project."""

    # -- Create -------------------------------------------------------------

    @staticmethod
    async def create_board(
        db: AsyncSession,
        *,
        project_id: UUID,
        name: str,
        created_by: UUID,
        description: str | None = None,
    ):
        """Create a new board inside a project."""
        Board = _get_board_model()
        board = Board(
            project_id=project_id,
            name=name,
            description=description,
            created_by=created_by,
        )
        db.add(board)
        await db.flush()
        await db.refresh(board)
        return board

    # -- Read (list) --------------------------------------------------------

    @staticmethod
    async def get_boards(
        db: AsyncSession,
        *,
        project_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """Paginated list of boards for a given project."""
        Board = _get_board_model()

        count_stmt = (
            select(func.count())
            .select_from(Board)
            .where(Board.project_id == project_id)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * size
        items_stmt = (
            select(Board)
            .where(Board.project_id == project_id)
            .order_by(Board.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Read (single) ------------------------------------------------------

    @staticmethod
    async def get_board(
        db: AsyncSession,
        *,
        board_id: UUID,
        project_id: UUID,
    ):
        """Fetch a single board or raise 404."""
        Board = _get_board_model()
        stmt = select(Board).where(
            Board.id == board_id,
            Board.project_id == project_id,
        )
        result = await db.execute(stmt)
        board = result.scalar_one_or_none()
        if board is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Board {board_id} not found.",
            )
        return board

    # -- Update -------------------------------------------------------------

    @staticmethod
    async def update_board(
        db: AsyncSession,
        *,
        board_id: UUID,
        project_id: UUID,
        data: dict,
    ):
        """Partially update a board. Returns the refreshed instance."""
        Board = _get_board_model()

        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update.",
            )

        stmt = (
            update(Board)
            .where(Board.id == board_id, Board.project_id == project_id)
            .values(**update_data)
            .returning(Board)
        )
        result = await db.execute(stmt)
        board = result.scalar_one_or_none()
        if board is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Board {board_id} not found.",
            )
        await db.flush()
        await db.refresh(board)
        return board

    # -- Delete -------------------------------------------------------------

    @staticmethod
    async def delete_board(
        db: AsyncSession,
        *,
        board_id: UUID,
        project_id: UUID,
    ) -> None:
        """Delete a board (cascades handled at DB level)."""
        Board = _get_board_model()
        stmt = delete(Board).where(
            Board.id == board_id,
            Board.project_id == project_id,
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Board {board_id} not found.",
            )
        await db.flush()


# ---------------------------------------------------------------------------
# FolderService
# ---------------------------------------------------------------------------


class FolderService:
    """CRUD operations for folders, scoped to a parent board."""

    # -- Create -------------------------------------------------------------

    @staticmethod
    async def create_folder(
        db: AsyncSession,
        *,
        board_id: UUID,
        name: str,
        created_by: UUID,
        description: str | None = None,
    ):
        """Create a new folder inside a board."""
        Folder = _get_folder_model()
        folder = Folder(
            board_id=board_id,
            name=name,
            description=description,
            created_by=created_by,
        )
        db.add(folder)
        await db.flush()
        await db.refresh(folder)
        return folder

    # -- Read (list) --------------------------------------------------------

    @staticmethod
    async def get_folders(
        db: AsyncSession,
        *,
        board_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """Paginated list of folders for a given board."""
        Folder = _get_folder_model()

        count_stmt = (
            select(func.count())
            .select_from(Folder)
            .where(Folder.board_id == board_id)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * size
        items_stmt = (
            select(Folder)
            .where(Folder.board_id == board_id)
            .order_by(Folder.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Read (single) ------------------------------------------------------

    @staticmethod
    async def get_folder(
        db: AsyncSession,
        *,
        folder_id: UUID,
        board_id: UUID,
    ):
        """Fetch a single folder or raise 404."""
        Folder = _get_folder_model()
        stmt = select(Folder).where(
            Folder.id == folder_id,
            Folder.board_id == board_id,
        )
        result = await db.execute(stmt)
        folder = result.scalar_one_or_none()
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Folder {folder_id} not found.",
            )
        return folder

    # -- Update -------------------------------------------------------------

    @staticmethod
    async def update_folder(
        db: AsyncSession,
        *,
        folder_id: UUID,
        board_id: UUID,
        data: dict,
    ):
        """Partially update a folder. Returns the refreshed instance."""
        Folder = _get_folder_model()

        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update.",
            )

        stmt = (
            update(Folder)
            .where(Folder.id == folder_id, Folder.board_id == board_id)
            .values(**update_data)
            .returning(Folder)
        )
        result = await db.execute(stmt)
        folder = result.scalar_one_or_none()
        if folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Folder {folder_id} not found.",
            )
        await db.flush()
        await db.refresh(folder)
        return folder

    # -- Delete -------------------------------------------------------------

    @staticmethod
    async def delete_folder(
        db: AsyncSession,
        *,
        folder_id: UUID,
        board_id: UUID,
    ) -> None:
        """Delete a folder (cascades handled at DB level)."""
        Folder = _get_folder_model()
        stmt = delete(Folder).where(
            Folder.id == folder_id,
            Folder.board_id == board_id,
        )
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Folder {folder_id} not found.",
            )
        await db.flush()
