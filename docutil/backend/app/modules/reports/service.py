"""
Service layer for report template management and report generation.

Phase 4 S2 D6 — Archive 읽기 전용 전환 (ISSUE-D2-1 해소):
--------------------------------------------------------
본 서비스는 ``tb_generated_reports_archive`` 를 통해 기존 보고서 이력을 **조회**
하기 위한 읽기 전용 레이어로 재정의되었다. 쓰기 메서드는 이미 라우터에서 410
Gone 으로 차단되므로 호출되지 않는다 (호환성·테스트를 위해 메서드 자체는
남겨두고 docstring 에 deprecated 를 명시).

**읽기 유지 (archive 읽기)**
    - ``ReportTemplateService.get_templates`` / ``get_template``
    - ``ReportGenerationService.get_reports`` / ``get_report``
    - ``ReportGenerationService.download_report``

**쓰기 deprecated (S7 에서 본 모듈 전체 삭제)**
    - ``ReportTemplateService.create_template``
    - ``ReportTemplateService.update_template``
    - ``ReportTemplateService.delete_template``
    - ``ReportGenerationService.generate_report``
    - ``ReportGenerationService.delete_report``

신규 보고서 생성 경로는 ``/api/v1/v2/documents`` 를 사용한다
(``tb_documents_v2``).
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy model imports
# ---------------------------------------------------------------------------


def _get_report_template_model():
    from app.modules.reports.models import ReportTemplate  # noqa: WPS433

    return ReportTemplate


def _get_generated_report_model():
    from app.modules.reports.models import GeneratedReport  # noqa: WPS433

    return GeneratedReport


def _get_document_template_model():
    """tb_document_templates 의 ORM 모델을 지연 로드한다.

    H10 핫픽스 배경: 프론트엔드가 `/templates` 에서 보여주는 템플릿은
    `tb_document_templates` 소속이지만, 과거 보고서 생성 요청은
    `GeneratedReport.template_id` (FK → tb_report_templates) 에 그대로 넣도록
    설계돼 있었다. 그 결과 실제 존재하지 않는 FK 를 참조해 HTTP 500 이
    발생한다(QA 기준선 76→79점 Critical F1). 요청받은 `template_id` 가
    tb_document_templates 의 UUID 인지 확인하기 위해 본 모델이 필요하다.
    """
    from app.modules.templates.models import DocumentTemplate  # noqa: WPS433

    return DocumentTemplate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEMPLATE_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")
"""Regex to extract ``{{variable_name}}`` placeholders from template text."""


def _template_object_key(org_id: UUID, template_id: UUID, filename: str) -> str:
    """Build a deterministic MinIO object key for template files."""
    return f"templates/{org_id}/{template_id}/{filename}"


def _report_object_key(org_id: UUID, report_id: UUID, filename: str) -> str:
    """Build a deterministic MinIO object key for generated reports."""
    return f"reports/{org_id}/{report_id}/{filename}"


def _extract_template_schema(content: bytes) -> dict[str, Any]:
    """Parse raw template bytes and extract ``{{var}}`` variable names.

    Returns a JSON-schema-like dict describing the discovered variables so
    that consumers know which fields to supply at generation time.
    """
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        text = ""

    variables = sorted(set(_TEMPLATE_VAR_PATTERN.findall(text)))

    if not variables:
        return {}

    properties: dict[str, Any] = {}
    for var in variables:
        properties[var] = {"type": "string", "description": f"Value for {{{{{var}}}}}"}

    return {
        "type": "object",
        "properties": properties,
        "required": variables,
    }


# ---------------------------------------------------------------------------
# ReportTemplateService
# ---------------------------------------------------------------------------


class ReportTemplateService:
    """CRUD operations for report templates with MinIO storage."""

    # -- Create template ----------------------------------------------------

    @staticmethod
    async def create_template(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        data: Any,
        file: UploadFile,
    ):
        """[DEPRECATED, S7 제거 예정] Create a new report template.

        Phase 4 S2 D6 기점으로 라우터가 410 Gone 으로 호출을 차단하므로
        실제 runtime 호출 경로는 없다. 기존 테스트·잠재적 내부 호출 경로에서
        import 가 깨지지 않도록 메서드 본체는 유지한다.

        Workflow (호출되는 경우):
        1. Read and store the template file in MinIO.
        2. Parse the file content to extract ``{{var}}`` variable schema.
        3. Persist the template metadata in PostgreSQL.
        """
        ReportTemplate = _get_report_template_model()
        settings = get_settings()

        # -- read file content -------------------------------------------------
        # 이전 경로에서 ``file_size`` 를 직접 사용하지만, MinIOService 는
        # ``bytes`` 길이를 내부에서 계산하므로 로컬 변수가 불필요해졌다.
        file_content = await file.read()
        original_filename = file.filename or "template"
        content_type = file.content_type or "application/octet-stream"

        # -- persist to object storage -----------------------------------------
        template_id = uuid.uuid4()
        object_key = _template_object_key(org_id, template_id, original_filename)

        # P1 원칙: MinIO SDK는 직접 import하지 않고 MinIOService 게이트웨이만 사용한다.
        # 과거 코드가 ``from app.integrations.object_storage import minio_client`` 후
        # ``minio_client.put_object(...)``를 호출했는데, ``minio_client``는 모듈명이지
        # Minio 클라이언트 인스턴스가 아니므로 AttributeError가 발생했다.
        try:
            from app.integrations.object_storage.minio_client import MinIOService  # noqa: WPS433

            minio_svc = MinIOService()
            minio_svc.upload_file(
                bucket=settings.minio_bucket,
                object_name=object_key,
                file_data=file_content,
                content_type=content_type,
            )
        except ImportError:
            logger.warning("MinIO client not configured; skipping template file upload.")
        except Exception:
            logger.exception("Failed to upload template file to MinIO.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to store template file in object storage.",
            )

        # -- extract variable schema -------------------------------------------
        schema = _extract_template_schema(file_content)

        # -- create DB record --------------------------------------------------
        template = ReportTemplate(
            id=template_id,
            organization_id=org_id,
            name=data.name,
            description=data.description,
            format=data.format,
            template_storage_path=object_key,
            schema=schema if schema else None,
            created_by=user_id,
        )
        db.add(template)
        await db.flush()
        await db.refresh(template)

        return template

    # -- List templates -----------------------------------------------------

    @staticmethod
    async def get_templates(
        db: AsyncSession,
        org_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """archive 조직 템플릿 목록 (읽기 전용, S7 제거 예정)."""
        ReportTemplate = _get_report_template_model()

        base_query = select(ReportTemplate).where(
            ReportTemplate.organization_id == org_id,
        )

        # Total count
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        # Paginated items
        offset = (page - 1) * size
        items_stmt = base_query.order_by(ReportTemplate.ins_dt.desc()).offset(offset).limit(size)
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Get single template ------------------------------------------------

    @staticmethod
    async def get_template(
        db: AsyncSession,
        template_id: UUID,
        org_id: UUID,
    ):
        """archive 단일 템플릿 조회 (읽기 전용, S7 제거 예정). 없으면 404."""
        ReportTemplate = _get_report_template_model()

        stmt = select(ReportTemplate).where(
            ReportTemplate.id == template_id,
            ReportTemplate.organization_id == org_id,
        )
        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report template {template_id} not found.",
            )
        return template

    # -- Update template ----------------------------------------------------

    @staticmethod
    async def update_template(
        db: AsyncSession,
        template_id: UUID,
        org_id: UUID,
        data: Any,
    ):
        """[DEPRECATED, S7 제거 예정] Update a template's metadata (name, description).

        S2 D6 이후 라우터가 410 Gone 을 반환하므로 호출되지 않는다.
        """
        template = await ReportTemplateService.get_template(
            db,
            template_id,
            org_id,
        )

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(template, field, value)

        await db.flush()
        await db.refresh(template)
        return template

    # -- Delete template ----------------------------------------------------

    @staticmethod
    async def delete_template(
        db: AsyncSession,
        template_id: UUID,
        org_id: UUID,
    ) -> None:
        """[DEPRECATED, S7 제거 예정] Delete a template + MinIO file.

        S2 D6 이후 라우터가 410 Gone 을 반환하므로 호출되지 않는다. S7 에서
        ``tb_report_templates`` 와 함께 본 메서드도 제거된다.
        """
        settings = get_settings()
        template = await ReportTemplateService.get_template(
            db,
            template_id,
            org_id,
        )

        # -- remove from object storage ----------------------------------------
        # P1 원칙: MinIOService 게이트웨이를 통해서만 접근한다.
        # (기존엔 모듈 자체를 클라이언트처럼 호출해 AttributeError가 발생했다.)
        if template.template_storage_path:
            try:
                from app.integrations.object_storage.minio_client import MinIOService  # noqa: WPS433

                minio_svc = MinIOService()
                minio_svc.delete_file(
                    bucket=settings.minio_bucket,
                    object_name=template.template_storage_path,
                )
            except ImportError:
                logger.warning("MinIO client not configured; skipping template file removal.")
            except Exception:
                logger.exception("Failed to remove template file from MinIO (non-fatal).")

        # -- remove DB record --------------------------------------------------
        await db.delete(template)
        await db.flush()


# ---------------------------------------------------------------------------
# ReportGenerationService
# ---------------------------------------------------------------------------


class ReportGenerationService:
    """Asynchronous report generation and retrieval."""

    # -- Generate report ----------------------------------------------------

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        data: Any,
    ):
        """[DEPRECATED, S7 제거 예정] Enqueue a new report generation job.

        S2 D6 이후 라우터가 410 Gone 을 반환하므로 실제 호출되지 않는다.
        호출되더라도 ``tb_generated_reports_archive`` 는 읽기 전용 정책이므로
        INSERT 는 정책상 허용되지 않는다. 신규 생성은 ``/api/v1/v2/documents``
        경로를 사용한다.

        Workflow (호출되는 경우):
        1. Create a ``GeneratedReport`` row with ``status='pending'``.
        2. Dispatch a Celery task for asynchronous processing.
        3. Return the record immediately so the caller can poll for status.
        """
        GeneratedReport = _get_generated_report_model()
        ReportTemplate = _get_report_template_model()
        DocumentTemplate = _get_document_template_model()

        report_id = uuid.uuid4()

        # H10: template_id 가 tb_document_templates 의 것이면 FK 위반을 피해
        # ORM 의 template_id 는 NULL 로 두고, 실제 사용 템플릿은
        # generation_params["document_template_id"] 로 보존한다.
        # 배경: 프론트엔드 `/templates` UI 는 tb_document_templates 레코드를
        # 노출하는데 기존 요청 스키마는 이 값을 `template_id` 로 받아 그대로
        # FK 에 넣어 HTTP 500 을 일으켰다. Phase 1 §7.1.2 B4 (템플릿 시스템
        # 이중화) 통합이 S7 에서 완성되기 전까지 본 핫픽스가 두 시스템을
        # 투명하게 이어준다.
        orm_template_id = data.template_id
        generation_params = dict(data.generation_params) if data.generation_params else {}
        if data.template_id is not None:
            report_tmpl_exists = (
                await db.execute(
                    select(ReportTemplate.id).where(ReportTemplate.id == data.template_id),
                )
            ).scalar_one_or_none()
            if report_tmpl_exists is None:
                doc_tmpl_exists = (
                    await db.execute(
                        select(DocumentTemplate.id).where(
                            DocumentTemplate.id == data.template_id,
                        ),
                    )
                ).scalar_one_or_none()
                if doc_tmpl_exists is not None:
                    # DocumentTemplate 임이 확인됐으므로 FK 충돌을 방지한다.
                    logger.info(
                        "H10: template_id %s 는 tb_document_templates 소속 — "
                        "generation_params 로 이전, ORM template_id=NULL",
                        data.template_id,
                    )
                    generation_params["document_template_id"] = str(data.template_id)
                    orm_template_id = None

        # H4: 과거 코드는 요청 schema의 ``source_chat_session_id``를 받고도
        # ORM 생성 시 이 필드를 누락하여 DB에 항상 NULL이 저장되었다.
        # Chat 지정 후 보고서 생성 시 후속 워커가 대화 기록을 로드할 수 있도록
        # 요청 값을 그대로 보존한다.
        report = GeneratedReport(
            id=report_id,
            template_id=orm_template_id,
            organization_id=org_id,
            title=data.title,
            status="pending",
            output_format=data.output_format,
            source_document_ids=([str(sid) for sid in data.source_document_ids] if data.source_document_ids else None),
            source_chat_session_id=data.source_chat_session_id,
            generation_params=generation_params,
            generated_by=user_id,
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)

        # -- enqueue Celery task -----------------------------------------------
        try:
            from app.workers.report_generator import generate_report  # noqa: WPS433

            generate_report.delay(str(report_id))
        except ImportError:
            logger.warning("Celery task 'generate_report_task' not available; report will remain in 'pending' status.")
        except Exception:
            logger.exception("Failed to enqueue report generation task.")

        return report

    # -- List generated reports ---------------------------------------------

    @staticmethod
    async def get_reports(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list, int]:
        """archive 사용자 보고서 목록 (읽기 전용, S7 제거 예정)."""
        GeneratedReport = _get_generated_report_model()

        base_query = select(GeneratedReport).where(
            GeneratedReport.organization_id == org_id,
            GeneratedReport.generated_by == user_id,
        )

        # Total count
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        # Paginated items
        offset = (page - 1) * size
        items_stmt = base_query.order_by(GeneratedReport.ins_dt.desc()).offset(offset).limit(size)
        result = await db.execute(items_stmt)
        items = list(result.scalars().all())

        return items, total

    # -- Get single report --------------------------------------------------

    @staticmethod
    async def get_report(
        db: AsyncSession,
        report_id: UUID,
        org_id: UUID,
    ):
        """archive 개별 보고서 조회 (읽기 전용, S7 제거 예정). 없으면 404."""
        GeneratedReport = _get_generated_report_model()

        stmt = select(GeneratedReport).where(
            GeneratedReport.id == report_id,
            GeneratedReport.organization_id == org_id,
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generated report {report_id} not found.",
            )
        return report

    # -- Delete report ------------------------------------------------------

    @staticmethod
    async def delete_report(
        db: AsyncSession,
        report_id: UUID,
        org_id: UUID,
    ) -> None:
        """[DEPRECATED, S7 제거 예정] 보고서 레코드와 MinIO 출력 파일을 삭제.

        S2 D6 정책(옵션 2): archive 테이블은 보존 원칙이므로 라우터가 410 Gone
        을 반환한다. 따라서 본 메서드는 실제 호출되지 않는다. 과거 H2 회귀
        (405 Method Not Allowed) 대응으로 라우트 자체는 존재시키되 서비스
        메서드는 참조만 되고 실행되지 않는다. S7 에서 본 메서드와 모듈 전체를
        함께 제거한다.
        """
        from app.integrations.object_storage.minio_client import MinIOService

        report = await ReportGenerationService.get_report(db, report_id, org_id)

        # 1) MinIO 파일 제거 (실패해도 DB 삭제는 진행 — 고아 레코드 방지)
        if report.output_storage_path:
            settings = get_settings()
            try:
                svc = MinIOService()
                svc.delete_file(
                    bucket=settings.minio_bucket,
                    object_name=report.output_storage_path,
                )
            except Exception as exc:  # noqa: BLE001 — 파일 제거 실패는 로그만
                logger.warning(
                    "Report %s 의 MinIO 파일 삭제 실패: %s",
                    report_id,
                    exc,
                )

        # 2) DB 레코드 삭제
        await db.delete(report)
        await db.flush()

    # -- Download report ----------------------------------------------------

    @staticmethod
    async def download_report(
        db: AsyncSession,
        report_id: UUID,
        org_id: UUID,
    ) -> StreamingResponse:
        """archive 완료 보고서 파일 다운로드 (읽기 전용, S7 제거 예정).

        Raises 404 if the report does not exist and 400 if the report has
        not yet completed or has no stored output.
        """
        settings = get_settings()
        report = await ReportGenerationService.get_report(db, report_id, org_id)

        if report.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"Report is not ready for download (status: {report.status})."),
            )

        if not report.output_storage_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report has no output file available.",
            )

        # -- content-type mapping ----------------------------------------------
        format_media_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf",
            "html": "text/html",
            "hwp": "application/x-hwp",
            "hwpx": "application/vnd.hancom.hwpx",
        }
        media_type = format_media_types.get(
            report.output_format,
            "application/octet-stream",
        )
        download_filename = f"{report.title}.{report.output_format}"

        try:
            from urllib.parse import quote

            from app.integrations.object_storage.minio_client import MinIOService

            minio_svc = MinIOService()
            file_bytes = minio_svc.download_file(
                bucket=settings.minio_bucket,
                object_name=report.output_storage_path,
            )

            encoded_name = quote(download_filename)
            return StreamingResponse(
                content=iter([file_bytes]),
                media_type=media_type,
                headers={
                    "Content-Disposition": (f"attachment; filename*=UTF-8''{encoded_name}"),
                },
            )
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Object storage is not configured.",
            )
        except Exception:
            logger.exception("Failed to retrieve report file from object storage.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve report file from object storage.",
            )
