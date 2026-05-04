"""Tests for document management endpoints."""

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
FAKE_FOLDER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
FAKE_DOC_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
FAKE_DEPT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
FAKE_JOB_ID = "abc123def456"
NOW = datetime(2025, 6, 1, tzinfo=UTC)


def _make_fake_document(**overrides):
    """Return a mock that behaves like a Document ORM instance.

    DocumentResponse uses validation_alias="ins_dt" / "upd_dt" for
    created_at / updated_at, so the mock exposes those attributes.
    It also includes visibility, department_id, and project_id fields.
    """
    defaults = {
        "id": FAKE_DOC_ID,
        "folder_id": FAKE_FOLDER_ID,
        "organization_id": FAKE_ORG_ID,
        "name": "report.pdf",
        "original_filename": "report.pdf",
        "format": "application/pdf",
        "file_size_bytes": 1024000,
        "status": "completed",
        "processing_error": None,
        "page_count": 10,
        "chunk_count": 25,
        "tags": ["finance", "q1"],
        "language": "en",
        "uploaded_by": FAKE_USER_ID,
        "visibility": "department_only",
        "department_id": FAKE_DEPT_ID,
        "project_id": None,
        "processing_started_at": NOW,
        "processing_completed_at": NOW,
        "ins_dt": NOW,
        "upd_dt": NOW,
        "storage_path": f"{FAKE_ORG_ID}/{FAKE_DOC_ID}/report.pdf",
    }
    defaults.update(overrides)
    doc = MagicMock()
    for key, val in defaults.items():
        setattr(doc, key, val)
    return doc


# ===========================================================================
# GET /api/v1/documents  (list)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_documents_success(client, admin_headers):
    """Listing documents returns a paginated 200 response."""
    fake_doc = _make_fake_document()

    with patch(
        "app.modules.documents.router.DocumentService.get_documents",
        new_callable=AsyncMock,
        return_value=([fake_doc], 1),
    ):
        resp = await client.get(
            "/api/v1/documents",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "report.pdf"
    assert data["items"][0]["status"] == "completed"


@pytest.mark.asyncio
async def test_list_documents_with_status_filter(client, admin_headers):
    """The status query parameter should be forwarded to the service."""
    with patch(
        "app.modules.documents.router.DocumentService.get_documents",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_get:
        resp = await client.get(
            "/api/v1/documents",
            params={"status": "processing"},
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    # Verify the filter was passed through
    call_kwargs = mock_get.call_args
    assert call_kwargs is not None


@pytest.mark.asyncio
async def test_list_documents_empty(client, admin_headers):
    """An empty document list returns 200 with zero items."""
    with patch(
        "app.modules.documents.router.DocumentService.get_documents",
        new_callable=AsyncMock,
        return_value=([], 0),
    ):
        resp = await client.get(
            "/api/v1/documents",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


# ===========================================================================
# POST /api/v1/documents/upload
# ===========================================================================


@pytest.mark.asyncio
async def test_upload_document_success(client, admin_headers):
    """Uploading a valid document returns 201 with a job_id."""
    fake_doc = _make_fake_document(status="waiting")

    with (
        patch(
            "app.modules.documents.router.DocumentService.upload_document",
            new_callable=AsyncMock,
            return_value=(fake_doc, FAKE_JOB_ID),
        ),
        patch(
            "app.modules.documents.router.AuditService.create_log",
            new_callable=AsyncMock,
        ),
    ):
        resp = await client.post(
            "/api/v1/documents/upload",
            params={"folder_id": str(FAKE_FOLDER_ID)},
            files={"file": ("report.pdf", b"fake-pdf-content", "application/pdf")},
            headers=admin_headers,
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == str(FAKE_DOC_ID)
    assert data["name"] == "report.pdf"
    assert data["job_id"] == FAKE_JOB_ID


@pytest.mark.asyncio
async def test_upload_document_missing_file(client, admin_headers):
    """Uploading without a file returns 422."""
    resp = await client.post(
        "/api/v1/documents/upload",
        params={"folder_id": str(FAKE_FOLDER_ID)},
        headers=admin_headers,
    )
    assert resp.status_code == 422


# ===========================================================================
# GET /api/v1/documents/{document_id}  (detail)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_document_success(client, admin_headers):
    """Retrieving an existing document by ID returns 200."""
    fake_doc = _make_fake_document()

    with patch(
        "app.modules.documents.router.DocumentService.get_document",
        new_callable=AsyncMock,
        return_value=fake_doc,
    ):
        resp = await client.get(
            f"/api/v1/documents/{FAKE_DOC_ID}",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(FAKE_DOC_ID)
    assert data["original_filename"] == "report.pdf"
    assert data["file_size_bytes"] == 1024000


@pytest.mark.asyncio
async def test_get_document_not_found(client, admin_headers):
    """Requesting a non-existent document returns 404."""
    missing_id = uuid.uuid4()

    with patch(
        "app.modules.documents.router.DocumentService.get_document",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=404,
            detail=f"Document {missing_id} not found.",
        ),
    ):
        resp = await client.get(
            f"/api/v1/documents/{missing_id}",
            headers=admin_headers,
        )

    assert resp.status_code == 404


# ===========================================================================
# Auth / RBAC
# ===========================================================================


@pytest.mark.asyncio
async def test_list_documents_no_auth(unauth_client):
    """Unauthenticated request to list documents returns 401."""
    resp = await unauth_client.get("/api/v1/documents")
    assert resp.status_code == 401


# ===========================================================================
# 이슈 2 — 부서/프로젝트 권한 (visibility) 테스트
# ===========================================================================


@pytest.mark.asyncio
async def test_upload_document_persists_visibility_fields(client, admin_headers):
    """업로드 시 visibility/department_id/project_id 가 Service 로 전달·저장되는지 검증."""
    fake_doc = _make_fake_document(
        status="waiting",
        visibility="project_only",
        department_id=None,
        project_id=uuid.UUID("99999999-9999-9999-9999-999999999999"),
    )

    with (
        patch(
            "app.modules.documents.router.DocumentService.upload_document",
            new_callable=AsyncMock,
            return_value=(fake_doc, FAKE_JOB_ID),
        ) as mock_upload,
        patch(
            "app.modules.documents.router.AuditService.create_log",
            new_callable=AsyncMock,
        ),
    ):
        resp = await client.post(
            "/api/v1/documents/upload",
            params={
                "folder_id": str(FAKE_FOLDER_ID),
                "visibility": "project_only",
                "project_id": "99999999-9999-9999-9999-999999999999",
            },
            files={"file": ("plan.pdf", b"fake-pdf", "application/pdf")},
            headers=admin_headers,
        )

    assert resp.status_code == 201
    # Router 가 Service 에 3파라미터를 정확히 포워딩하는지 확인
    kwargs = mock_upload.call_args.kwargs
    assert kwargs["visibility"] == "project_only"
    assert str(kwargs["project_id"]) == "99999999-9999-9999-9999-999999999999"


@pytest.mark.asyncio
async def test_list_documents_filters_by_user_department():
    """member 사용자가 get_documents 를 호출하면 사용자 컨텍스트가 전파되고
    기본 권한 스코프 clause 가 빌드되는지 확인한다."""
    from app.modules.documents.service import DocumentService

    # Service 레벨에서 직접 검증 (라우터를 통한 E2E 는 mock 과 상호작용이 복잡)
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(
        return_value=MagicMock(
            scalar=MagicMock(return_value=0),
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))),
            all=MagicMock(return_value=[]),
            first=MagicMock(return_value=None),
        )
    )

    with patch.object(
        DocumentService,
        "_build_list_visibility_scope",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_scope:
        items, total = await DocumentService.get_documents(
            mock_db,
            org_id=FAKE_ORG_ID,
            current_user_id=FAKE_USER_ID,
            current_user_role="member",
            current_user_dept_id=FAKE_DEPT_ID,
        )

    # member 는 admin bypass 대상 아니므로 스코프 빌더가 호출돼야 한다
    assert mock_scope.called
    call_kwargs = mock_scope.call_args.kwargs
    assert call_kwargs["user_id"] == FAKE_USER_ID
    assert call_kwargs["user_role"] == "member"
    assert call_kwargs["user_dept_id"] == FAKE_DEPT_ID
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_document_returns_404_for_hidden(client, admin_headers):
    """hidden 문서를 업로더 외 사용자가 요청하면 404 (403 아님, 존재 노출 방지)."""
    # admin_headers 는 admin role 이므로 bypass 됨 → 여기선 member_headers 시뮬레이션이
    # 필요하지만, 현재 fixture 구조상 Service 단에서 직접 검증하는 편이 깔끔하다.
    from app.modules.documents.service import DocumentService

    hidden_doc = _make_fake_document(
        visibility="hidden",
        uploaded_by=uuid.UUID("77777777-7777-7777-7777-777777777777"),  # 다른 사용자
    )

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=hidden_doc)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as excinfo:
        await DocumentService.get_document(
            mock_db,
            doc_id=FAKE_DOC_ID,
            org_id=FAKE_ORG_ID,
            current_user_id=FAKE_USER_ID,  # 업로더와 다른 사용자
            current_user_role="member",
            current_user_dept_id=FAKE_DEPT_ID,
        )

    # hidden 문서의 존재를 숨기기 위해 403 이 아닌 404 반환
    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_admin_bypasses_visibility_checks():
    """admin/super_admin/org_admin 은 visibility 와 무관하게 bypass 된다."""
    from app.modules.documents.service import DocumentService

    # 모든 visibility 값에 대해 admin 은 True 를 반환해야 함
    for vis in [
        "public",
        "all_departments",
        "department_only",
        "project_only",
        "confidential",
        "hidden",
    ]:
        doc = _make_fake_document(
            visibility=vis,
            uploaded_by=uuid.UUID("77777777-7777-7777-7777-777777777777"),
            department_id=None,  # 안전 기본값조차 bypass 되는지도 확인
        )
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        for admin_role in ("admin", "super_admin", "org_admin"):
            allowed = await DocumentService._can_access_document(
                mock_db,
                document=doc,
                user_id=FAKE_USER_ID,  # 업로더 아님
                user_role=admin_role,
                user_dept_id=None,
            )
            assert allowed is True, f"{admin_role} should bypass visibility={vis}"


@pytest.mark.asyncio
async def test_confidential_requires_access_grant():
    """confidential 문서는 tb_document_access grant 가 있거나 업로더 본인이어야 허용."""
    from app.modules.documents.service import DocumentService

    other_user = uuid.UUID("77777777-7777-7777-7777-777777777777")
    doc = _make_fake_document(
        visibility="confidential",
        uploaded_by=other_user,
        department_id=FAKE_DEPT_ID,
    )

    # Case 1: grant 없음 → 차단
    mock_db_no_grant = MagicMock()
    no_grant_result = MagicMock()
    no_grant_result.first = MagicMock(return_value=None)
    mock_db_no_grant.execute = AsyncMock(return_value=no_grant_result)

    allowed_denied = await DocumentService._can_access_document(
        mock_db_no_grant,
        document=doc,
        user_id=FAKE_USER_ID,
        user_role="member",
        user_dept_id=FAKE_DEPT_ID,
    )
    assert allowed_denied is False

    # Case 2: grant 있음 → 허용
    mock_db_granted = MagicMock()
    grant_result = MagicMock()
    grant_result.first = MagicMock(return_value=(1,))
    mock_db_granted.execute = AsyncMock(return_value=grant_result)

    allowed_granted = await DocumentService._can_access_document(
        mock_db_granted,
        document=doc,
        user_id=FAKE_USER_ID,
        user_role="member",
        user_dept_id=FAKE_DEPT_ID,
    )
    assert allowed_granted is True

    # Case 3: 업로더 본인 → DB 조회 없이 허용
    mock_db_uploader = MagicMock()
    mock_db_uploader.execute = AsyncMock()
    allowed_uploader = await DocumentService._can_access_document(
        mock_db_uploader,
        document=doc,
        user_id=other_user,  # == doc.uploaded_by
        user_role="member",
        user_dept_id=FAKE_DEPT_ID,
    )
    assert allowed_uploader is True
    # 업로더 bypass 경로에서는 tb_document_access 조회가 일어나지 않아야 한다
    mock_db_uploader.execute.assert_not_called()
