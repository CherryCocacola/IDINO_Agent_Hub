"""
Service layer for document management.

Handles upload (single and bulk), retrieval, deletion (across MinIO,
Qdrant, and PostgreSQL), chunk access, and status transitions.
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, delete, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import ClauseElement

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# -- 가시성(visibility) 허용 값 -----------------------------------------------
# models.py 의 DocumentVisibility enum 과 동기화되어야 함.
_VISIBILITY_VALUES: frozenset[str] = frozenset({
    "public",
    "all_departments",
    "department_only",
    "project_only",
    "confidential",
    "hidden",
})


def _visibility_disabled() -> bool:
    """긴급 롤백용 kill switch.

    환경변수 ``DOCUTIL_DISABLE_VISIBILITY=1`` 가 설정되면 모든 권한 체크를
    bypass 한다. 플랜의 리스크 대응책(§리스크·롤백).
    """
    return os.getenv("DOCUTIL_DISABLE_VISIBILITY", "").strip() in {"1", "true", "True"}

# ---------------------------------------------------------------------------
# Lazy model imports
# ---------------------------------------------------------------------------


def _get_document_model():
    from app.modules.documents.models import Document  # noqa: WPS433
    return Document


def _get_chunk_model():
    from app.modules.documents.models import DocumentChunk  # noqa: WPS433
    return DocumentChunk


def _get_user_model():
    """User 모델 지연 import.

    Service 계층에서 UserService 를 직접 호출하지 않고(P4 데이터 흐름 준수),
    필요한 컬럼만 SELECT 하기 위해 ORM 모델만 가져온다.
    """
    from app.modules.users.models import User  # noqa: WPS433
    return User


def _get_department_model():
    """Department 모델 지연 import (materialized path 해석용)."""
    from app.modules.organizations.models import Department  # noqa: WPS433
    return Department


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minio_object_key(org_id: UUID, doc_id: UUID, filename: str) -> str:
    """Build a deterministic MinIO object key."""
    return f"{org_id}/{doc_id}/{filename}"


# ---------------------------------------------------------------------------
# DocumentService
# ---------------------------------------------------------------------------


class DocumentService:
    """CRUD and lifecycle operations for documents."""

    # -- Upload (single) ----------------------------------------------------

    @staticmethod
    async def upload_document(
        db: AsyncSession,
        *,
        file: UploadFile,
        folder_id: UUID | None,
        org_id: UUID,
        user_id: UUID,
        visibility: str = "department_only",
        department_id: UUID | None = None,
        project_id: UUID | None = None,
    ):
        """Upload a single file.

        Workflow:
        1. Validate file type, size, and visibility 파라미터.
        2. Store the binary in MinIO.
        3. Create a ``Document`` row with ``status='waiting'``.
        4. Enqueue an async processing job (Celery / RabbitMQ).
        5. Return the new document record.

        Parameters
        ----------
        visibility:
            문서 공개 범위 (6종). 기본값은 ``department_only``. 허용 값 밖이면
            ``department_only`` 로 fallback 하고 warning 로그를 남긴다.
        department_id:
            문서가 소속될 부서. ``department_only`` 일 때 ``None`` 이면
            업로더의 ``department_id`` 로 자동 설정한다.
        project_id:
            문서가 소속될 프로젝트. ``project_only`` 일 때 반드시 제공돼야 한다.
        """
        Document = _get_document_model()
        settings = get_settings()

        # -- visibility/권한 파라미터 검증 -----------------------------------
        # enum 밖의 값은 안전한 기본값으로 fallback (클라이언트 오류를 보안
        # 완화로 막아야 하므로 더 느슨한 쪽이 아니라 기본값인 department_only).
        if visibility not in _VISIBILITY_VALUES:
            logger.warning(
                "Unknown visibility '%s'; falling back to 'department_only'.",
                visibility,
            )
            visibility = "department_only"

        # project_only 는 반드시 project_id 가 있어야 접근 제어가 성립한다
        if visibility == "project_only" and project_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="프로젝트 전용 문서는 project_id 가 반드시 필요합니다.",
            )

        # department_only 인데 department_id 미전달 → 업로더 부서로 자동 설정
        if visibility == "department_only" and department_id is None:
            User = _get_user_model()
            uploader = await db.execute(
                select(User.department_id).where(User.id == user_id)
            )
            uploader_dept = uploader.scalar_one_or_none()
            if uploader_dept is not None:
                department_id = uploader_dept
            else:
                logger.warning(
                    "Uploader %s has no department; document %s will be "
                    "admin-only (department_id IS NULL safety default).",
                    user_id, "(new)",
                )

        # -- validation -----------------------------------------------------
        content_type = file.content_type or "application/octet-stream"
        if content_type not in settings.allowed_upload_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {content_type}",
            )

        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File exceeds the maximum allowed size "
                    f"of {settings.max_upload_size_mb} MB."
                ),
            )

        # -- persist to object storage --------------------------------------
        doc_id = uuid.uuid4()
        original_filename = file.filename or "unnamed"
        object_key = _minio_object_key(org_id, doc_id, original_filename)

        try:
            # MinIOService 인스턴스를 생성하여 파일을 업로드한다
            from app.integrations.object_storage.minio_client import MinIOService

            minio_svc = MinIOService()
            minio_svc.upload_file(
                bucket=settings.minio_bucket,
                object_name=object_key,
                file_data=file_content,
                content_type=content_type,
            )
        except ImportError:
            logger.warning(
                "MinIO client not configured; skipping object storage upload."
            )
        except Exception:
            logger.exception("Failed to upload file to MinIO.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to store file in object storage.",
            )

        # -- create DB record -----------------------------------------------
        checksum = hashlib.sha256(file_content).hexdigest()
        job_id = uuid.uuid4().hex
        document = Document(
            id=doc_id,
            folder_id=folder_id,
            organization_id=org_id,
            name=original_filename,
            original_filename=original_filename,
            format=content_type,
            file_size_bytes=file_size,
            status="waiting",
            uploaded_by=user_id,
            storage_path=object_key,
            checksum_sha256=checksum,
            # 부서/프로젝트 권한 필드 영속화 (기존 누락으로 인한 보안 이슈 수정)
            visibility=visibility,
            department_id=department_id,
            project_id=project_id,
        )
        db.add(document)
        await db.flush()
        await db.refresh(document)

        # -- enqueue processing task ----------------------------------------
        try:
            from app.workers.document_processor import process_document  # noqa: WPS433

            process_document.delay(str(doc_id))
        except ImportError:
            logger.warning(
                "Celery task 'process_document' not available; "
                "document will remain in 'pending' status."
            )
        except Exception:
            logger.exception("Failed to enqueue document processing task.")

        # Attach ephemeral job_id for the response (not persisted on model)
        document._job_id = job_id  # type: ignore[attr-defined]
        return document, job_id

    # -- Bulk upload --------------------------------------------------------

    @staticmethod
    async def bulk_upload(
        db: AsyncSession,
        *,
        files: list[UploadFile],
        folder_id: UUID | None,
        org_id: UUID,
        user_id: UUID,
        visibility: str = "department_only",
        department_id: UUID | None = None,
        project_id: UUID | None = None,
    ) -> tuple[list[tuple[Any, str]], list[dict]]:
        """Upload multiple files in one request.

        visibility/department_id/project_id 는 단일 업로드와 동일하게 모든
        파일에 동일한 값이 적용된다.

        Returns ``(uploaded, failed)`` where *uploaded* is a list of
        ``(Document, job_id)`` tuples and *failed* is a list of error dicts.
        """
        uploaded: list[tuple[Any, str]] = []
        failed: list[dict] = []

        for file in files:
            try:
                doc, job_id = await DocumentService.upload_document(
                    db,
                    file=file,
                    folder_id=folder_id,
                    org_id=org_id,
                    user_id=user_id,
                    visibility=visibility,
                    department_id=department_id,
                    project_id=project_id,
                )
                uploaded.append((doc, job_id))
            except HTTPException as exc:
                failed.append({
                    "filename": file.filename or "unnamed",
                    "error": exc.detail,
                })
            except Exception as exc:
                logger.exception("Unexpected error during bulk upload.")
                failed.append({
                    "filename": file.filename or "unnamed",
                    "error": str(exc),
                })

        return uploaded, failed

    # -- List documents -----------------------------------------------------

    @staticmethod
    async def get_documents(
        db: AsyncSession,
        *,
        org_id: UUID,
        folder_id: UUID | None = None,
        board_id: UUID | None = None,
        project_id: UUID | None = None,
        status_filter: str | None = None,
        visibility_filter: str | None = None,
        current_user_id: UUID | None = None,
        current_user_role: str | None = None,
        current_user_dept_id: UUID | None = None,
        as_user_view: bool = False,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """Return a paginated, filtered list of documents.

        권한 처리:
        - ``super_admin``/``admin``/``org_admin`` 은 기본적으로 모든 visibility bypass.
        - ``as_user_view=True`` 가 명시되면 admin 계열도 일반 사용자처럼 visibility
          스코프가 적용된다 (사용자 화면 — my-documents, search 등에서 사용).
        - 그 외 role 은 :func:`_build_list_visibility_scope` 가 빌드한 스코프
          조건을 WHERE 에 추가한다 (공개범위별 or_ 절).
        - ``DOCUTIL_DISABLE_VISIBILITY=1`` 이면 kill switch 로 bypass.
        """
        Document = _get_document_model()

        conditions = [Document.organization_id == org_id]

        if folder_id is not None:
            conditions.append(Document.folder_id == folder_id)

        if board_id is not None:
            # Join through folder -> board to filter by board_id
            from app.modules.projects.models import Folder  # noqa: WPS433

            folder_ids_stmt = select(Folder.id).where(Folder.board_id == board_id)
            conditions.append(Document.folder_id.in_(folder_ids_stmt))

        if project_id is not None:
            # 두 경로를 OR 로 결합:
            # 1) 폴더를 갖는 문서: folder → board → project 트리 매칭
            # 2) folder-less 문서: tb_documents.project_id 컬럼을 직접 매칭
            # 자동 보관 보드/폴더 생성 제거 이후 (2) 경로가 필수가 됐다.
            from app.modules.projects.models import Board, Folder  # noqa: WPS433

            board_ids_stmt = select(Board.id).where(Board.project_id == project_id)
            folder_ids_stmt = select(Folder.id).where(
                Folder.board_id.in_(board_ids_stmt)
            )
            conditions.append(
                or_(
                    Document.folder_id.in_(folder_ids_stmt),
                    Document.project_id == project_id,
                )
            )

        if status_filter is not None:
            conditions.append(Document.status == status_filter)

        # visibility 필터 (FE page.tsx 에서 전송). enum 검증 후 적용.
        if visibility_filter is not None and visibility_filter in _VISIBILITY_VALUES:
            conditions.append(Document.visibility == visibility_filter)

        # -- 권한 스코프 적용 ---------------------------------------------------
        # 기본적으로 admin 계열은 bypass. 그러나 as_user_view=True 인 경우
        # (사용자 화면에서 본인 권한으로 조회하는 흐름) admin 도 visibility
        # 스코프 검증을 받는다.
        admin_roles = {"super_admin", "admin", "org_admin"}
        is_bypass_admin = current_user_role in admin_roles and not as_user_view
        if (
            not _visibility_disabled()
            and current_user_role is not None
            and not is_bypass_admin
            and current_user_id is not None
        ):
            scope_clauses = await DocumentService._build_list_visibility_scope(
                db,
                user_id=current_user_id,
                user_role=current_user_role,
                user_dept_id=current_user_dept_id,
                org_id=org_id,
            )
            if scope_clauses:
                # 여러 가시성 분기 중 하나라도 허용되면 보이도록 OR 결합
                conditions.append(or_(*scope_clauses))

        # Total count
        count_stmt = (
            select(func.count()).select_from(Document).where(*conditions)
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        # Items
        offset = (page - 1) * size
        items_stmt = (
            select(Document)
            .where(*conditions)
            .order_by(Document.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Get single document ------------------------------------------------

    @staticmethod
    async def get_document(
        db: AsyncSession,
        *,
        doc_id: UUID,
        org_id: UUID,
        current_user_id: UUID | None = None,
        current_user_role: str | None = None,
        current_user_dept_id: UUID | None = None,
        as_user_view: bool = False,
    ):
        """Fetch a single document by ID within the organisation, or 404.

        권한이 없는 사용자에게도 **404** 를 반환한다 (403 이 아님).
        이유: ``visibility=hidden`` 문서의 존재 자체를 노출하면 안 된다.

        ``as_user_view=True`` 이면 admin/super_admin/org_admin 도 일반 사용자
        시점으로 visibility 검증을 거친다 (사용자 화면 단건 조회용).
        """
        Document = _get_document_model()
        stmt = select(Document).where(
            Document.id == doc_id,
            Document.organization_id == org_id,
        )
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문서를 찾을 수 없습니다.",
            )

        # 권한 정보가 넘어왔을 때만 체크 (레거시 호출 호환 — 내부 삭제 경로 등)
        if current_user_role is not None:
            allowed = await DocumentService._can_access_document(
                db,
                document=document,
                user_id=current_user_id,
                user_role=current_user_role,
                user_dept_id=current_user_dept_id,
                as_user_view=as_user_view,
            )
            if not allowed:
                # hidden 존재 노출 방지를 위해 404 반환
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="문서를 찾을 수 없습니다.",
                )
        return document

    # -- Get document detail (표시용 부가 정보 포함) ---------------------------

    @staticmethod
    async def get_document_detail(
        db: AsyncSession,
        *,
        doc_id: UUID,
        org_id: UUID,
        current_user_id: UUID | None,
        current_user_role: str | None,
        current_user_dept_id: UUID | None,
        as_user_view: bool = False,
    ) -> dict:
        """단건 조회 + 상세 다이얼로그용 표시 정보를 dict 로 반환한다.

        결과 dict 는 :class:`DocumentDetailResponse` 와 1:1 로 매핑된다.
        라우터에서 from_attributes 가 아닌 직접 dict 검증으로 직렬화하려고
        ORM 객체 대신 dict 를 돌려준다.
        """
        Document = _get_document_model()
        User = _get_user_model()
        Department = _get_department_model()

        document = await DocumentService.get_document(
            db,
            doc_id=doc_id,
            org_id=org_id,
            current_user_id=current_user_id,
            current_user_role=current_user_role,
            current_user_dept_id=current_user_dept_id,
            as_user_view=as_user_view,
        )

        # 1) 업로더 username (한글 이름이 들어 있는 컬럼)
        uploaded_by_name: str | None = None
        if document.uploaded_by is not None:
            row = await db.execute(
                select(User.username).where(User.id == document.uploaded_by)
            )
            uploaded_by_name = row.scalar_one_or_none()

        # 2) 부서명 + 가시 부서 목록 (visibility 별로 분기)
        department_name: str | None = None
        visible_department_names: list[str] = []
        if document.department_id is not None:
            row = await db.execute(
                select(Department.name, Department.path).where(
                    Department.id == document.department_id
                )
            )
            row_data = row.first()
            if row_data is not None:
                department_name = row_data[0]
                # department_only 면 본인 + 하위 부서까지 모두 가시 대상
                subtree = await db.execute(
                    select(Department.name)
                    .where(Department.path.like(f"{row_data[1]}%"))
                    .order_by(Department.path)
                )
                visible_department_names = [r[0] for r in subtree.all()]

        # all_departments 는 조직 전체 부서가 가시 대상
        if document.visibility == "all_departments":
            all_d = await db.execute(
                select(Department.name)
                .where(Department.organization_id == org_id)
                .order_by(Department.path)
            )
            visible_department_names = [r[0] for r in all_d.all()]

        # 3) 프로젝트 정보 + 가시 사용자 목록
        project_name: str | None = None
        project_member_names: list[str] = []
        if document.project_id is not None:
            from app.modules.projects.models import Project  # noqa: WPS433

            row = await db.execute(
                select(Project.name).where(Project.id == document.project_id)
            )
            project_name = row.scalar_one_or_none()

            # 직접 멤버 (tb_project_members)
            direct_rows = await db.execute(
                text(
                    "SELECT u.username FROM tb_users u "
                    "JOIN tb_project_members pm ON pm.user_id = u.id "
                    "WHERE pm.project_id = :pid"
                ),
                {"pid": document.project_id},
            )
            direct = [r[0] for r in direct_rows.all() if r[0]]

            # 참여 부서의 사용자 (tb_project_departments → tb_users.department_id)
            dept_rows = await db.execute(
                text(
                    "SELECT u.username FROM tb_users u "
                    "WHERE u.department_id IN ("
                    "  SELECT department_id FROM tb_project_departments "
                    "  WHERE project_id = :pid"
                    ")"
                ),
                {"pid": document.project_id},
            )
            indirect = [r[0] for r in dept_rows.all() if r[0]]

            seen: set[str] = set()
            for n in direct + indirect:
                if n not in seen:
                    seen.add(n)
                    project_member_names.append(n)

        # 4) 사용자 친화적 한 줄 요약
        summary_map = {
            "public": "전체 공개 — 조직 내 모든 사용자",
            "all_departments": f"전부서 공개 ({len(visible_department_names)}개 부서)",
            "department_only": (
                f"부서 내 공개 — {department_name} (+하위 {max(0, len(visible_department_names) - 1)}개)"
                if department_name
                else "부서 내 공개"
            ),
            "project_only": (
                f"프로젝트 내 공개 — {project_name} ({len(project_member_names)}명)"
                if project_name
                else "프로젝트 내 공개"
            ),
            "confidential": "비밀 — 별도 권한 부여된 사용자만",
            "hidden": "숨김 — 업로더와 관리자만",
        }
        visibility_summary = summary_map.get(document.visibility, document.visibility)

        # 5) ORM → dict (DocumentResponse 매핑 후 부가 필드 병합)
        from .schemas import DocumentResponse  # noqa: WPS433  -- 순환 방지용 지연 import

        base = DocumentResponse.model_validate(document).model_dump()
        base.update(
            {
                "uploaded_by_name": uploaded_by_name,
                "department_name": department_name,
                "project_name": project_name,
                "visible_department_names": visible_department_names,
                "project_member_names": project_member_names,
                "visibility_summary": visibility_summary,
            }
        )
        return base

    # -- Delete document ----------------------------------------------------

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        *,
        doc_id: UUID,
        org_id: UUID,
    ) -> None:
        """Delete a document from MinIO, Qdrant, and the database."""
        Document = _get_document_model()
        settings = get_settings()

        # Fetch first to get the storage key
        document = await DocumentService.get_document(
            db, doc_id=doc_id, org_id=org_id,
        )

        # -- remove from object storage -------------------------------------
        try:
            from app.integrations.object_storage.minio_client import MinIOService

            minio_svc = MinIOService()
            minio_svc.delete_file(
                bucket=settings.minio_bucket,
                object_name=document.storage_path,
            )
        except ImportError:
            logger.warning("MinIO client not configured; skipping object removal.")
        except Exception:
            logger.exception("Failed to remove object from MinIO (non-fatal).")

        # -- remove vectors from Qdrant -------------------------------------
        try:
            from app.integrations.vector_store import qdrant_client  # noqa: WPS433

            qdrant_client.delete(
                collection_name=settings.qdrant_collection_name,
                points_selector={"filter": {"must": [
                    {"key": "document_id", "match": {"value": str(doc_id)}},
                ]}},
            )
        except ImportError:
            logger.warning("Qdrant client not configured; skipping vector removal.")
        except Exception:
            logger.exception("Failed to remove vectors from Qdrant (non-fatal).")

        # -- remove chunks from DB ------------------------------------------
        DocumentChunk = _get_chunk_model()
        await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == doc_id)
        )

        # -- remove document record -----------------------------------------
        await db.execute(
            delete(Document).where(
                Document.id == doc_id,
                Document.organization_id == org_id,
            )
        )
        await db.flush()

    # -- Get chunks ---------------------------------------------------------

    @staticmethod
    async def get_chunks(
        db: AsyncSession,
        *,
        doc_id: UUID,
    ) -> list:
        """Return all chunks for a document, ordered by chunk_index."""
        DocumentChunk = _get_chunk_model()
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == doc_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # -- Update status ------------------------------------------------------

    @staticmethod
    async def update_status(
        db: AsyncSession,
        *,
        doc_id: UUID,
        doc_status: str,
        error: str | None = None,
    ):
        """Transition a document to a new processing status."""
        Document = _get_document_model()

        values: dict[str, Any] = {"status": doc_status}
        if error is not None:
            values["processing_error"] = error

        # Set timestamps based on status
        from datetime import datetime, timezone

        if doc_status == "processing":
            values["processing_started_at"] = datetime.now(timezone.utc)
        elif doc_status in ("completed", "failed"):
            values["processing_completed_at"] = datetime.now(timezone.utc)

        stmt = (
            update(Document)
            .where(Document.id == doc_id)
            .values(**values)
            .returning(Document)
        )
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found.",
            )
        await db.flush()
        await db.refresh(document)
        return document

    # =====================================================================
    # 권한 / 가시성(visibility) 헬퍼
    #
    # P2 모듈 구조 유지를 위해 별도 파일이 아니라 service.py 하단에 staticmethod
    # 로 배치한다. P4 (Router → Service → Integration) 준수를 위해 다른
    # Service 를 호출하지 않고 Department/User/ProjectMember/DocumentAccess
    # 테이블을 직접 SELECT 만 수행한다.
    # =====================================================================

    @staticmethod
    async def _can_access_document(
        db: AsyncSession,
        *,
        document: Any,
        user_id: UUID | None,
        user_role: str | None,
        user_dept_id: UUID | None,
        as_user_view: bool = False,
    ) -> bool:
        """단일 문서에 대한 접근 가능 여부 판정 (6가지 visibility 각각).

        규칙:
        - admin/super_admin/org_admin: 기본적으로 전 문서 허용 (운영자 화면용).
          단, ``as_user_view=True`` 가 명시되면 admin 도 일반 사용자처럼
          visibility 검사를 거친다 (사용자 화면용).
        - 업로더 본인: 항상 허용 (confidential/hidden bypass)
        - public / all_departments: 조직 내 모두 허용
        - department_only: 사용자 부서 + 하위 부서 (materialized path) 만 허용
        - project_only: tb_project_members 조인으로 멤버만 허용
        - confidential: tb_document_access 에 명시된 사용자만 허용
        - hidden: 업로더 외 일반 사용자는 차단 (admin 은 위에서 이미 허용)
        - 안전 기본값: ``document.department_id IS NULL`` 이면 admin 만 허용
        """
        # Kill switch — 긴급 롤백
        if _visibility_disabled():
            return True

        admin_roles = {"super_admin", "admin", "org_admin"}
        # 운영자 화면(default)에서는 admin 계열은 visibility 무시. 사용자 화면
        # (as_user_view=True)에서는 admin 도 일반 사용자처럼 검증한다.
        if user_role in admin_roles and not as_user_view:
            return True

        # 업로더 본인은 모든 visibility 통과 (본인이 올린 문서)
        if user_id is not None and document.uploaded_by == user_id:
            return True

        visibility = getattr(document, "visibility", None) or "department_only"

        if visibility == "hidden":
            # 업로더+admin 외에는 접근 불가 (위에서 이미 필터됨)
            return False

        if visibility in ("public", "all_departments"):
            # 조직 내 누구나 (org 필터는 get_document 에서 이미 적용)
            return True

        if visibility == "department_only":
            doc_dept = getattr(document, "department_id", None)
            # 안전 기본값: department_id 가 NULL 인 문서는 admin 만 허용
            if doc_dept is None:
                return False
            if user_dept_id is None:
                return False
            # 같은 부서면 바로 허용
            if doc_dept == user_dept_id:
                return True
            # 부모-자식 관계 확인: 문서 부서가 사용자 부서의 하위에 속하는지
            # materialized path 로 판단 (subtree 내 포함 여부)
            subtree_ids = await DocumentService._resolve_department_subtree_ids(
                db, dept_id=user_dept_id,
            )
            return doc_dept in subtree_ids

        if visibility == "project_only":
            doc_proj = getattr(document, "project_id", None)
            if doc_proj is None or user_id is None:
                return False
            # tb_project_members 멤버 여부 확인
            result = await db.execute(
                text(
                    "SELECT 1 FROM tb_project_members "
                    "WHERE project_id = :pid AND user_id = :uid LIMIT 1"
                ),
                {"pid": doc_proj, "uid": user_id},
            )
            return result.first() is not None

        if visibility == "confidential":
            if user_id is None:
                return False
            # tb_document_access 에 grant 되어 있는지 확인
            result = await db.execute(
                text(
                    "SELECT 1 FROM tb_document_access "
                    "WHERE document_id = :did AND user_id = :uid LIMIT 1"
                ),
                {"did": document.id, "uid": user_id},
            )
            return result.first() is not None

        # 알 수 없는 visibility 는 차단 (fail-closed)
        logger.warning(
            "Unknown visibility '%s' on document %s; denying access.",
            visibility, document.id,
        )
        return False

    @staticmethod
    async def _build_list_visibility_scope(
        db: AsyncSession,
        *,
        user_id: UUID,
        user_role: str,
        user_dept_id: UUID | None,
        org_id: UUID,
    ) -> list[ClauseElement]:
        """목록 조회용 WHERE 스코프(or_ 결합용 절 리스트) 생성.

        admin 계열은 애초에 이 함수를 호출하지 않는다(상위에서 bypass).
        빈 리스트가 반환되면 어떤 문서도 보이지 않는다 (fail-closed).
        """
        Document = _get_document_model()
        clauses: list[ClauseElement] = []

        # 1) 업로더 본인 문서는 언제나 허용
        clauses.append(Document.uploaded_by == user_id)

        # 2) public / all_departments — 조직 내 전체 공개
        clauses.append(Document.visibility.in_(("public", "all_departments")))

        # 3) department_only — 사용자 부서 + 하위 부서
        if user_dept_id is not None:
            subtree_ids = await DocumentService._resolve_department_subtree_ids(
                db, dept_id=user_dept_id,
            )
            if subtree_ids:
                clauses.append(
                    and_(
                        Document.visibility == "department_only",
                        Document.department_id.in_(subtree_ids),
                    )
                )

        # 4) project_only — 사용자가 멤버로 있는 프로젝트의 문서
        proj_rows = await db.execute(
            text(
                "SELECT project_id FROM tb_project_members WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        member_proj_ids = [row[0] for row in proj_rows.all()]
        if member_proj_ids:
            clauses.append(
                and_(
                    Document.visibility == "project_only",
                    Document.project_id.in_(member_proj_ids),
                )
            )

        # 5) confidential — tb_document_access 에 grant 된 문서
        access_rows = await db.execute(
            text(
                "SELECT document_id FROM tb_document_access WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        granted_doc_ids = [row[0] for row in access_rows.all()]
        if granted_doc_ids:
            clauses.append(
                and_(
                    Document.visibility == "confidential",
                    Document.id.in_(granted_doc_ids),
                )
            )

        # hidden 은 업로더만 볼 수 있는데 이미 (1) 절로 커버됨.
        # department_id IS NULL 인 문서는 admin 만 허용하므로 여기 포함시키지 않는다.
        return clauses

    @staticmethod
    async def _resolve_department_subtree_ids(
        db: AsyncSession,
        *,
        dept_id: UUID,
    ) -> list[UUID]:
        """주어진 부서의 서브트리 ID 목록 반환.

        Department.path 는 materialized path (예: ``/root/a/b/``) 형태로
        저장돼 있어 ``LIKE :prefix || '%'`` 로 하위 노드까지 탐색한다.
        기준 부서 자신도 결과에 포함된다.
        """
        Department = _get_department_model()

        # 기준 부서의 path 조회
        result = await db.execute(
            select(Department.id, Department.path).where(Department.id == dept_id)
        )
        row = result.first()
        if row is None:
            # 기준 부서 자체를 못 찾으면 빈 리스트 (fail-closed)
            return []

        base_id, base_path = row[0], row[1]
        if not base_path:
            # path 가 비어 있으면 자신만 반환
            return [base_id]

        # path LIKE 'base_path%' 로 서브트리 조회
        subtree = await db.execute(
            select(Department.id).where(Department.path.like(f"{base_path}%"))
        )
        ids = [rid for (rid,) in subtree.all()]
        # path 조회 결과에 기준 부서가 미포함될 수도 있으니 안전하게 추가
        if base_id not in ids:
            ids.append(base_id)
        return ids
