"""Tests for project, board, and folder management endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Reusable identifiers and helpers
# ---------------------------------------------------------------------------
FAKE_ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
FAKE_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
FAKE_PROJECT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FAKE_BOARD_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
FAKE_FOLDER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
FAKE_DEPT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
NOW = datetime(2025, 6, 1, tzinfo=UTC)


def _make_fake_project(**overrides):
    """Return a mock that behaves like a Project ORM instance.

    ProjectResponse uses validation_alias="ins_dt" / "upd_dt" for
    created_at / updated_at, so the mock exposes those attributes.
    """
    defaults = {
        "id": FAKE_PROJECT_ID,
        "name": "Test Project",
        "description": "A test project",
        "allow_original_download": True,
        "organization_id": FAKE_ORG_ID,
        "created_by": FAKE_USER_ID,
        "ins_dt": NOW,
        "upd_dt": NOW,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for key, val in defaults.items():
        setattr(obj, key, val)
    return obj


def _make_fake_board(**overrides):
    """Return a mock that behaves like a Board ORM instance.

    BoardResponse uses validation_alias="ins_dt" / "upd_dt" for
    created_at / updated_at.
    """
    defaults = {
        "id": FAKE_BOARD_ID,
        "project_id": FAKE_PROJECT_ID,
        "name": "Test Board",
        "description": "A test board",
        "created_by": FAKE_USER_ID,
        "ins_dt": NOW,
        "upd_dt": NOW,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for key, val in defaults.items():
        setattr(obj, key, val)
    return obj


def _make_fake_folder(**overrides):
    """Return a mock that behaves like a Folder ORM instance.

    FolderResponse uses validation_alias="ins_dt" / "upd_dt" for
    created_at / updated_at.
    """
    defaults = {
        "id": FAKE_FOLDER_ID,
        "board_id": FAKE_BOARD_ID,
        "name": "Test Folder",
        "description": "A test folder",
        "created_by": FAKE_USER_ID,
        "ins_dt": NOW,
        "upd_dt": NOW,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for key, val in defaults.items():
        setattr(obj, key, val)
    return obj


# ===========================================================================
# GET /api/v1/projects  (list)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_projects_success(client, admin_headers):
    """Listing projects returns a paginated response with 200."""
    fake_project = _make_fake_project()

    with (
        patch(
            "app.modules.projects.router.ProjectService.get_projects",
            new_callable=AsyncMock,
            return_value=([fake_project], 1),
        ),
        patch(
            # 프로젝트 목록 조회 시 각 프로젝트의 부서 정보를 enrichment하는 서비스 mock
            "app.modules.projects.router.ProjectDepartmentService.list_departments",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            # 프로젝트 목록 조회 시 각 프로젝트의 멤버 정보를 enrichment하는 서비스 mock
            "app.modules.projects.router.ProjectMemberService.list_members",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        resp = await client.get(
            "/api/v1/projects",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Test Project"


@pytest.mark.asyncio
async def test_list_projects_empty(client, admin_headers):
    """An organization with no projects returns an empty page."""
    with patch(
        "app.modules.projects.router.ProjectService.get_projects",
        new_callable=AsyncMock,
        return_value=([], 0),
    ):
        resp = await client.get(
            "/api/v1/projects",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


# ===========================================================================
# POST /api/v1/projects  (create)
# ===========================================================================


@pytest.mark.asyncio
async def test_create_project_success(client, admin_headers):
    """Creating a project with valid data returns 201."""
    fake_project = _make_fake_project(name="New Project")

    with (
        patch(
            "app.modules.projects.router.ProjectService.create_project",
            new_callable=AsyncMock,
            return_value=fake_project,
        ),
        patch(
            "app.modules.projects.router.ProjectDepartmentService.list_departments",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.modules.projects.router.ProjectMemberService.list_members",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        resp = await client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "description": "desc",
                "department_ids": [str(FAKE_DEPT_ID)],
            },
            headers=admin_headers,
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Project"


@pytest.mark.asyncio
async def test_create_project_missing_name(client, admin_headers):
    """Missing required 'name' field returns 422."""
    resp = await client.post(
        "/api/v1/projects",
        json={"description": "no name provided"},
        headers=admin_headers,
    )
    assert resp.status_code == 422


# ===========================================================================
# GET /api/v1/projects/{project_id}  (detail)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_project_success(client, admin_headers):
    """Retrieving an existing project by ID returns 200."""
    fake_project = _make_fake_project()

    with (
        patch(
            "app.modules.projects.router.ProjectService.get_project",
            new_callable=AsyncMock,
            return_value=fake_project,
        ),
        patch(
            # 프로젝트 상세 조회 시 부서 정보를 enrichment하는 서비스 mock
            "app.modules.projects.router.ProjectDepartmentService.list_departments",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            # 프로젝트 상세 조회 시 멤버 정보를 enrichment하는 서비스 mock
            "app.modules.projects.router.ProjectMemberService.list_members",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        resp = await client.get(
            f"/api/v1/projects/{FAKE_PROJECT_ID}",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(FAKE_PROJECT_ID)


@pytest.mark.asyncio
async def test_get_project_not_found(client, admin_headers):
    """Requesting a non-existent project returns 404."""
    missing_id = uuid.uuid4()

    with patch(
        "app.modules.projects.router.ProjectService.get_project",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=404, detail="Not found"),
    ):
        resp = await client.get(
            f"/api/v1/projects/{missing_id}",
            headers=admin_headers,
        )

    assert resp.status_code == 404


# ===========================================================================
# GET /api/v1/projects/{project_id}/boards  (list boards)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_boards_success(client, admin_headers):
    """Listing boards for a project returns a paginated response."""
    fake_board = _make_fake_board()

    with patch(
        "app.modules.projects.router.BoardService.get_boards",
        new_callable=AsyncMock,
        return_value=([fake_board], 1),
    ):
        resp = await client.get(
            f"/api/v1/projects/{FAKE_PROJECT_ID}/boards",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Test Board"


# ===========================================================================
# GET /api/v1/boards/{board_id}/folders  (list folders)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_folders_success(client, admin_headers):
    """Listing folders for a board returns a paginated response."""
    fake_folder = _make_fake_folder()

    with patch(
        "app.modules.projects.router.FolderService.get_folders",
        new_callable=AsyncMock,
        return_value=([fake_folder], 1),
    ):
        resp = await client.get(
            f"/api/v1/boards/{FAKE_BOARD_ID}/folders",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Test Folder"


# ===========================================================================
# Auth / RBAC
# ===========================================================================


@pytest.mark.asyncio
async def test_list_projects_no_auth(unauth_client):
    """Unauthenticated request to list projects returns 401."""
    resp = await unauth_client.get("/api/v1/projects")
    assert resp.status_code == 401
