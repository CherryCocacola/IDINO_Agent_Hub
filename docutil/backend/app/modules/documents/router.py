"""
FastAPI router for document management.

Endpoints
---------
- ``GET  /documents``                     -- list with filters & pagination
- ``POST /documents/upload``              -- single file upload (multipart)
- ``POST /documents/bulk-upload``         -- multiple file upload (multipart)
- ``GET  /documents/{id}``                -- document detail
- ``DELETE /documents/{id}``              -- delete document
- ``GET  /documents/{id}/download``       -- download original file
- ``GET  /documents/{id}/chunks``         -- list extracted chunks
- ``GET  /documents/upload-progress/{job_id}`` -- SSE progress stream

Access control
--------------
- **read / download** endpoints require ``member`` role or above.
- **upload / delete** endpoints require ``admin`` or ``org_admin``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid as uuid_mod
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.security import TokenData

from .schemas import (
    BulkUploadItemError,
    BulkUploadResponse,
    DocumentChunkResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.modules.audit.service import AuditService
from .service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["documents"])

# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------
_require_admin = require_role(["super_admin", "admin", "org_admin"])
_require_member = require_role(["super_admin", "admin", "org_admin", "manager", "member", "editor", "viewer"])


# ---------------------------------------------------------------------------
# Folder resolution helper
# ---------------------------------------------------------------------------


async def _resolve_default_folder(
    db: AsyncSession,
    *,
    project_id: UUID | None,
    org_id: UUID,
    user_id: UUID,
) -> UUID | None:
    """프로젝트가 명시되었을 때, 기존 폴더가 있으면 사용하고 없으면 None을 반환한다.

    동작 방식
    ---------
    - ``project_id`` 가 있으면 해당 프로젝트의 **이미 존재하는** 첫 번째 보드/폴더를
      찾아 반환한다. 사용자가 미리 만들어둔 폴더 구조가 있으면 자동으로 그곳에 보관.
    - 적합한 폴더가 없으면 ``None`` 을 반환해 folder-less 로 저장한다.
      ``tb_documents.folder_id`` 컬럼이 nullable 이고 ``project_id`` 컬럼이 별도로
      있어 프로젝트 매핑은 그대로 유지된다 (list_documents 의 project_id 필터에서
      folder 트리와 OR 결합되어 노출된다).
    - ``project_id`` 가 ``None`` 이면 그대로 ``None`` 반환 (부서/공개 업로드 흐름).

    왜 자동 생성을 하지 않게 바꿨는가?
    ---------------------------------
    이전에는 폴더가 없으면 "자동 보관 보드/폴더"를 자동 생성해 트리 깊이가
    불필요하게 깊어지고, 사용자가 의도하지 않은 노드들이 화면에 노출되었다.
    프로젝트 직속(folder 없이) 문서를 허용하는 것이 더 단순한 UX 이며,
    명시적으로 폴더 구조를 만든 사용자만 그 폴더를 사용한다.
    """
    if project_id is None:
        return None

    from sqlalchemy import select as sa_select  # noqa: WPS433
    from app.modules.projects.models import Board, Folder  # noqa: WPS433

    # 프로젝트의 첫 번째 보드에서 첫 번째 폴더를 찾는다
    stmt = (
        sa_select(Folder)
        .join(Board, Folder.board_id == Board.id)
        .where(Board.project_id == project_id)
        .order_by(Board.ins_dt, Folder.ins_dt)
        .limit(1)
    )
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()

    if folder is not None:
        return folder.id

    # 자동 보드/폴더 생성을 더 이상 하지 않는다 (트리 노이즈 방지).
    # folder-less 로 저장하면 list_documents 의 project_id 필터가
    # ``Document.folder_id IN (...) OR Document.project_id == project_id`` 로
    # 매칭하므로 프로젝트 노드 클릭 시 그대로 노출된다.
    return None


# ===========================================================================
# List documents
# ===========================================================================


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    folder_id: UUID | None = Query(default=None),
    board_id: UUID | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    # FE (documents/page.tsx:341) 에서 이미 전송 중인 쿼리 파라미터
    visibility: str | None = Query(default=None),
    # 사용자 화면(my-documents/search 등)에서 본인 권한으로 조회할 때 True.
    # 기본값(False)은 운영자 화면에서 admin 계열이 모든 문서를 보던 기존 동작.
    as_user_view: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """List documents with optional filters (folder, board, project, status).

    Service 계층이 visibility 스코프를 자동으로 적용하므로 Router 는 사용자
    컨텍스트(role/id/dept_id)와 ``as_user_view`` 만 전달하면 된다.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    items, total = await DocumentService.get_documents(
        db,
        org_id=current_user.organization_id,
        folder_id=folder_id,
        board_id=board_id,
        project_id=project_id,
        status_filter=status_filter,
        visibility_filter=visibility,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
        current_user_dept_id=current_user.department_id,
        as_user_view=as_user_view,
        page=page,
        size=size,
    )
    return DocumentListResponse(items=items, total=total, page=page, size=size)


# ===========================================================================
# Single upload
# ===========================================================================


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    folder_id: UUID | None = Query(default=None),
    visibility: str | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Upload a single document (multipart form-data)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    # folder_id가 없으면 project_id로 기본 폴더를 찾거나 생성한다
    if folder_id is None:
        folder_id = await _resolve_default_folder(
            db,
            project_id=project_id,
            org_id=current_user.organization_id,
            user_id=current_user.user_id,
        )

    document, job_id = await DocumentService.upload_document(
        db,
        file=file,
        folder_id=folder_id,
        org_id=current_user.organization_id,
        user_id=current_user.user_id,
        # 부서/프로젝트 권한 파라미터를 Service 에 전파한다
        visibility=visibility or "department_only",
        department_id=department_id,
        project_id=project_id,
    )

    # 감사 로그: 문서 업로드 성공 기록
    try:
        await AuditService.create_log(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.user_id,
            action="document.upload",
            resource_type="document",
            resource_id=str(document.id),
            details={"filename": document.name, "folder_id": str(folder_id)},
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함

    return DocumentUploadResponse(
        id=document.id,
        name=document.name,
        status=document.status,
        job_id=job_id,
    )


# ===========================================================================
# Bulk upload
# ===========================================================================


@router.post(
    "/documents/bulk-upload",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_upload_documents(
    folder_id: UUID | None = Query(default=None),
    visibility: str | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
    department_id: UUID | None = Query(default=None),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Upload multiple documents at once (multipart form-data)."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    # folder_id가 없으면 project_id로 기본 폴더를 찾거나 생성한다
    if folder_id is None:
        folder_id = await _resolve_default_folder(
            db,
            project_id=project_id,
            org_id=current_user.organization_id,
            user_id=current_user.user_id,
        )

    uploaded_items, failed_items = await DocumentService.bulk_upload(
        db,
        files=files,
        folder_id=folder_id,
        org_id=current_user.organization_id,
        user_id=current_user.user_id,
        # 일괄 업로드도 동일한 권한 파라미터를 모든 파일에 적용
        visibility=visibility or "department_only",
        department_id=department_id,
        project_id=project_id,
    )

    uploaded = [
        DocumentUploadResponse(
            id=doc.id,
            name=doc.name,
            status=doc.status,
            job_id=job_id,
        )
        for doc, job_id in uploaded_items
    ]
    failed = [
        BulkUploadItemError(filename=item["filename"], error=item["error"])
        for item in failed_items
    ]

    return BulkUploadResponse(uploaded=uploaded, failed=failed)


# ===========================================================================
# Document detail
# ===========================================================================


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    # 사용자 화면 단건 조회 시 True 로 호출하면 admin 도 visibility 검증을 받는다.
    as_user_view: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Retrieve a single document by ID with display-friendly metadata.

    응답에는 업로더 이름, 부서/프로젝트명, 가시성에 따른 공개 대상 목록 등
    상세 다이얼로그 표시용 정보가 포함된다 (DocumentDetailResponse).
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    # Service 가 visibility 기반 접근 제어를 수행하므로 사용자 컨텍스트를 전달
    return await DocumentService.get_document_detail(
        db,
        doc_id=document_id,
        org_id=current_user.organization_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
        current_user_dept_id=current_user.department_id,
        as_user_view=as_user_view,
    )


# ===========================================================================
# Delete document
# ===========================================================================


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_document(
    document_id: UUID,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Delete a document and its associated data."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    await DocumentService.delete_document(
        db, doc_id=document_id, org_id=current_user.organization_id,
    )

    # 감사 로그: 문서 삭제 성공 기록
    try:
        await AuditService.create_log(
            db=db,
            org_id=current_user.organization_id,
            user_id=current_user.user_id,
            action="document.delete",
            resource_type="document",
            resource_id=str(document_id),
            ip_address=request.client.host if request and request.client else None,
        )
    except Exception:
        pass  # 감사 로그 실패가 주 흐름을 막지 않도록 함


# ===========================================================================
# Download original
# ===========================================================================


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """Stream the original file from object storage."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    settings = get_settings()
    # 다운로드도 조회와 동일하게 visibility 검사를 거친다 (Service 내부에서 체크)
    document = await DocumentService.get_document(
        db,
        doc_id=document_id,
        org_id=current_user.organization_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
        current_user_dept_id=current_user.department_id,
    )

    try:
        # MinIOService 인스턴스를 생성하여 파일을 다운로드한다
        from app.integrations.object_storage.minio_client import MinIOService

        minio_svc = MinIOService()
        file_bytes = minio_svc.download_file(
            bucket=settings.minio_bucket,
            object_name=document.storage_path,
        )

        from urllib.parse import quote

        encoded_name = quote(document.original_filename)
        return StreamingResponse(
            content=iter([file_bytes]),
            media_type=document.format,
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{encoded_name}"
                ),
            },
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Object storage is not configured.",
        )
    except Exception:
        logger.exception("Failed to retrieve file from object storage.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve file from object storage.",
        )


# ===========================================================================
# Document chunks
# ===========================================================================


@router.get(
    "/documents/{document_id}/chunks",
    response_model=list[DocumentChunkResponse],
)
async def get_document_chunks(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """List all extracted content chunks for a document."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    # 문서 존재 + 조직 소속 확인 및 visibility 기반 접근 제어
    await DocumentService.get_document(
        db,
        doc_id=document_id,
        org_id=current_user.organization_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
        current_user_dept_id=current_user.department_id,
    )
    return await DocumentService.get_chunks(db, doc_id=document_id)


# ===========================================================================
# Upload progress (Server-Sent Events)
# ===========================================================================


@router.get("/documents/upload-progress/{job_id}")
async def upload_progress(
    job_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Stream upload / processing progress via Server-Sent Events (SSE).

    The client should connect using ``EventSource`` and listen for
    ``progress`` events containing JSON payloads with ``status`` and
    ``percent`` fields.
    """

    async def _event_stream():
        """Poll Redis (or Celery result backend) for job progress."""
        try:
            import redis.asyncio as aioredis  # noqa: WPS433

            settings = get_settings()
            r = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        except ImportError:
            # No Redis client available -- send a single "unknown" event
            yield _sse_event({"status": "unknown", "percent": 0, "message": "Progress tracking unavailable."})
            return

        max_polls = 300  # ~5 minutes at 1-second intervals
        for _ in range(max_polls):
            progress_raw = await r.get(f"job_progress:{job_id}")
            if progress_raw is not None:
                progress = json.loads(progress_raw)
                yield _sse_event(progress)
                if progress.get("status") in ("completed", "failed"):
                    break
            else:
                yield _sse_event({"status": "pending", "percent": 0})
            await asyncio.sleep(1)

        await r.aclose()

    return StreamingResponse(
        content=_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse_event(data: dict) -> str:
    """Format a dict as a Server-Sent Event string."""
    return f"event: progress\ndata: {json.dumps(data)}\n\n"
