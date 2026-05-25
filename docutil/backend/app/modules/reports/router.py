"""
FastAPI router for report management.

Phase 4 S2 D6 — Archive 읽기 전용 전환 (ISSUE-D2-1 해소):
--------------------------------------------------------
``tb_generated_reports`` 가 Alembic 007 에서 ``_archive`` 로 리네이밍된 이후,
본 라우터는 **읽기 경로만 유지**하고 쓰기 경로는 **410 Gone** 을 반환한다.

- 읽기(응답 헤더 ``X-Deprecated-API: true`` 포함):
    - GET    /reports                   -- 기존 보고서 이력 조회(archive)
    - GET    /reports/{id}              -- 개별 보고서 조회(archive)
    - GET    /reports/{id}/download     -- 완료 보고서 다운로드(archive)
- 쓰기(410 Gone, 한국어 안내):
    - POST   /reports/generate          -- 신규 생성은 /api/v1/v2/documents 사용
    - DELETE /reports/{id}              -- archive 보존 정책상 차단
- 템플릿(GET/LIST 는 유지, POST/PUT/DELETE 는 410 Gone):
    - GET    /reports/templates         -- 기존 템플릿 목록 조회
    - GET    /reports/templates/{id}    -- 개별 템플릿 조회
    - POST   /reports/templates         -- **410** (신규 등록은 신규 경로 사용)
    - PUT    /reports/templates/{id}    -- **410**
    - DELETE /reports/templates/{id}    -- **410**

신규 생성 경로: ``/api/v1/v2/documents`` (디자이너: ``/designer/create``).
S7 (Phase 4 최종) 에서 본 모듈 전체를 삭제한다
(``docs/phase2_transition_plan.md`` §2.6 B5/B4, §3.10 D6).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import TokenData

from .schemas import (
    GeneratedReportListResponse,
    GeneratedReportResponse,
    ReportGenerateRequest,
    ReportTemplateListResponse,
    ReportTemplateResponse,
    ReportTemplateUpdate,
)

# S2 D6 주의: 쓰기 경로를 410 Gone 으로 차단했으나 GET/LIST 엔드포인트는
# 서비스 레이어(ReportGenerationService / ReportTemplateService) 를 통해
# archive 테이블을 그대로 읽는다. 따라서 두 서비스 클래스는 계속 import 한다.
from .service import ReportGenerationService, ReportTemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["reports"])

# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------
_require_admin = require_role(["super_admin", "admin", "org_admin"])
_require_member = require_role(["super_admin", "admin", "org_admin", "manager", "member", "editor", "viewer", "user"])


# ---------------------------------------------------------------------------
# Deprecation helpers (S2 D6)
# ---------------------------------------------------------------------------

# 쓰기 엔드포인트에서 반환할 통일 메시지. FE 가 토스트로 그대로 노출해도
# 사용자가 바로 신규 경로로 이동할 수 있도록 한국어로 안내한다.
GONE_MESSAGE = (
    "해당 기능은 /v2/documents 로 이관되었습니다. "
    "디자이너(/designer/create) 를 사용하세요."
)

# 읽기 엔드포인트 응답에 붙이는 비표준 헤더. FE/클라이언트가 이 값을 감지해
# deprecated UI 를 표시할 수 있다 (`true` 고정, 대소문자 무관).
DEPRECATED_HEADER_NAME = "X-Deprecated-API"
DEPRECATED_HEADER_VALUE = "true"


def _mark_deprecated(response: Response) -> None:
    """응답에 ``X-Deprecated-API: true`` 헤더를 주입한다.

    archive 전환으로 인한 읽기 경로임을 호출측(프론트엔드·외부 클라이언트)이
    인지할 수 있도록 표준화된 헤더를 추가한다. S7 에서 본 모듈과 함께 제거.
    """

    response.headers[DEPRECATED_HEADER_NAME] = DEPRECATED_HEADER_VALUE


def _raise_gone() -> None:
    """쓰기 엔드포인트에서 호출되는 410 Gone 공용 예외 발생기.

    Phase 4 S2 D6: ``tb_generated_reports_archive`` 는 읽기 전용이며 신규
    INSERT/UPDATE/DELETE 는 허용되지 않는다. ``GONE_MESSAGE`` 한국어 안내를
    detail 로 내려 사용자가 즉시 신규 경로로 이동할 수 있게 한다.
    """

    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=GONE_MESSAGE,
    )


# ---------------------------------------------------------------------------
# Session user resolver (H3 핫픽스)
# ---------------------------------------------------------------------------


async def _resolve_session_user(db: AsyncSession, current_user: TokenData) -> dict[str, Any]:
    """로그인 사용자의 소속/성명 정보를 DB에서 조회해 dict로 반환한다.

    TokenData에는 user_id / organization_id / department_id 만 담기므로,
    Jinja2 템플릿의 session_auto 카테고리 변수(소속, 부서, 성명 등)를
    채우기 위해 실제 이름을 User / Organization / Department 테이블에서 로드한다.

    H3 핫픽스 배경: 워커(`report_generator.py`)가 ``_session_user`` 키를
    참조하는 로직은 이미 있었지만, 라우터가 이를 주입하지 않아
    session_auto 변수들이 항상 빈 문자열로 렌더링되었다.

    견고성 원칙: DB 조회 실패(세션 만료, soft-delete 사용자, 테스트 fixture
    누락 등) 시에도 보고서 생성 자체가 막혀서는 안 되므로 각 조회를
    개별 try/except로 감싸고, 실패 시 빈 문자열로 fallback 한다.
    """

    import logging

    from app.modules.organizations.models import Department, Organization
    from app.modules.users.models import User

    logger = logging.getLogger(__name__)

    user_info: dict[str, Any] = {
        "user_id": str(current_user.user_id),
        "username": "",
        "organization_name": "",
        "department_name": "",
    }

    # User 기본 정보
    try:
        user_row = (
            await db.execute(select(User).where(User.id == current_user.user_id))
        ).scalar_one_or_none()
        if user_row is not None:
            user_info["username"] = user_row.username or ""
            user_info["email"] = user_row.email or ""
    except Exception as exc:
        logger.warning("session_user: User 조회 실패 - %s", exc)

    # Organization 이름
    if current_user.organization_id is not None:
        try:
            org_row = (
                await db.execute(
                    select(Organization).where(Organization.id == current_user.organization_id)
                )
            ).scalar_one_or_none()
            if org_row is not None:
                user_info["organization_name"] = org_row.name or ""
        except Exception as exc:
            logger.warning("session_user: Organization 조회 실패 - %s", exc)

    # Department 이름 (있으면)
    if current_user.department_id is not None:
        try:
            dept_row = (
                await db.execute(
                    select(Department).where(Department.id == current_user.department_id)
                )
            ).scalar_one_or_none()
            if dept_row is not None:
                user_info["department_name"] = dept_row.name or ""
        except Exception as exc:
            logger.warning("session_user: Department 조회 실패 - %s", exc)

    # 워커는 ``department``/``username`` 키를 먼저 참조하므로 alias를 둔다.
    # (기존 SESSION_MAPPING 상수와의 하위 호환성 유지)
    user_info["department"] = user_info["department_name"]

    return user_info


# ===========================================================================
# Report templates -- CRUD (admin+)
# ===========================================================================


# -- List templates ---------------------------------------------------------


@router.get(
    "/reports/templates",
    response_model=ReportTemplateListResponse,
    summary="List report templates (deprecated, archive read-only)",
    description=(
        "Return a paginated list of report templates for the organisation. "
        "Deprecated — `X-Deprecated-API: true` 헤더가 포함된다. "
        "신규 템플릿 등록은 /v2/documents 템플릿 경로를 사용하세요."
    ),
)
async def list_templates(
    response: Response,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """기존 보고서 템플릿 목록을 조회한다 (archive 읽기 전용).

    S2 D6: 응답에 ``X-Deprecated-API: true`` 헤더를 추가해 FE 가 deprecated
    UI 를 표시할 수 있게 한다. S7 에서 본 엔드포인트와 함께 삭제 예정.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    items, total = await ReportTemplateService.get_templates(
        db,
        org_id=current_user.organization_id,
        page=page,
        size=size,
    )
    _mark_deprecated(response)
    return ReportTemplateListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


# -- Create template -------------------------------------------------------


@router.post(
    "/reports/templates",
    status_code=status.HTTP_410_GONE,
    summary="[GONE] Create a report template — 이관됨",
    description=(
        "S2 D6 이후 차단. 신규 템플릿 등록은 /v2/documents 템플릿 경로 또는 "
        "템플릿 디자이너 UI (/designer/create) 를 사용한다."
    ),
    responses={
        410: {"description": "Endpoint removed — 신규 경로로 이관됨."},
    },
)
async def create_template(
    # 기존 multipart 시그니처를 유지한다 (FE 호출 시 422 대신 410 을 받도록).
    name: str = Form(default=""),
    format: str = Form(default=""),
    description: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    current_user: TokenData = Depends(_require_admin),
):
    """보고서 템플릿 등록 엔드포인트 (deprecated, 410 Gone).

    S2 D6: archive 읽기 전용 전환에 따라 신규 등록은 차단한다. 입력 payload 는
    무시하고 즉시 410 Gone 을 반환한다. 실제 템플릿 등록은 ``/v2/documents``
    경로(Mode B skeleton 등록) 또는 템플릿 디자이너에서 수행한다.
    """
    _raise_gone()


# -- Get template -----------------------------------------------------------


@router.get(
    "/reports/templates/{template_id}",
    response_model=ReportTemplateResponse,
    summary="Get report template details (deprecated, archive read-only)",
)
async def get_template(
    response: Response,
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
):
    """단일 템플릿 조회 (archive 읽기 전용). 응답에 deprecated 헤더 추가."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    template = await ReportTemplateService.get_template(
        db,
        template_id=template_id,
        org_id=current_user.organization_id,
    )
    _mark_deprecated(response)
    return template


# -- Update template -------------------------------------------------------


@router.put(
    "/reports/templates/{template_id}",
    status_code=status.HTTP_410_GONE,
    summary="[GONE] Update report template metadata — 이관됨",
    responses={
        410: {"description": "Endpoint removed — 신규 경로로 이관됨."},
    },
)
async def update_template(
    template_id: UUID,
    payload: ReportTemplateUpdate,
    current_user: TokenData = Depends(_require_admin),
):
    """템플릿 메타데이터 수정 — S2 D6 이후 410 Gone.

    archive 테이블 쓰기 차단 정책. 신규 템플릿 수정은 /v2/documents 계열 경로
    또는 템플릿 디자이너에서 처리한다.
    """
    _raise_gone()


# -- Delete template -------------------------------------------------------


@router.delete(
    "/reports/templates/{template_id}",
    status_code=status.HTTP_410_GONE,
    response_model=None,
    summary="[GONE] Delete a report template — 이관됨",
    responses={
        410: {"description": "Endpoint removed — 신규 경로로 이관됨."},
    },
)
async def delete_template(
    template_id: UUID,
    current_user: TokenData = Depends(_require_admin),
) -> Response:
    """템플릿 삭제 — S2 D6 이후 410 Gone.

    archive 보존 정책상 기존 템플릿을 삭제하지 않는다. S7 에서 본 모듈 전체와
    ``tb_report_templates`` 테이블을 함께 drop 할 때 일괄 정리된다.
    """
    _raise_gone()
    # 정적 타입 체커 만족용 (실제로는 _raise_gone() 에서 예외 발생).
    return Response(status_code=status.HTTP_410_GONE)


# ===========================================================================
# Report generation (member+)
# ===========================================================================


# -- Generate report -------------------------------------------------------


@router.post(
    "/reports/generate",
    status_code=status.HTTP_410_GONE,
    summary="[GONE] Generate a report — /v2/documents 로 이관됨",
    description=(
        "S2 D6 이후 차단. 신규 보고서 생성은 ``POST /api/v1/v2/documents`` 또는 "
        "디자이너(/designer/create) 를 사용한다. archive 테이블은 읽기 전용이다."
    ),
    responses={
        410: {"description": "Endpoint removed — /v2/documents 로 이관됨."},
    },
)
async def generate_report(
    payload: ReportGenerateRequest,
    current_user: TokenData = Depends(_require_member),
):
    """보고서 생성 — S2 D6 이후 410 Gone.

    ``tb_generated_reports_archive`` 는 Alembic 007 이후 읽기 전용이므로
    신규 INSERT 를 차단한다. 호출측(FE) 은 이 응답을 받으면 사용자에게
    ``GONE_MESSAGE`` 안내를 노출하고 /v2/documents 경로로 라우팅해야 한다.

    입력 schema 는 하위 호환을 위해 그대로 유지하되(payload 파싱 후 즉시 410),
    실제 파라미터 값은 사용하지 않는다.
    """
    _raise_gone()


# -- List generated reports -------------------------------------------------


@router.get(
    "/reports",
    response_model=GeneratedReportListResponse,
    summary="List generated reports (deprecated, archive read-only)",
    description=(
        "Return a paginated list of reports generated by the current user. "
        "응답에 ``X-Deprecated-API: true`` 헤더가 포함된다. 신규 보고서는 "
        "/v2/documents 에서 조회한다."
    ),
)
async def list_reports(
    response: Response,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """사용자별 보고서 이력 조회 (archive 읽기 전용).

    S2 D6: ``tb_generated_reports_archive`` 의 57건 과거 보고서를 UI 에 노출
    하기 위한 과도기 엔드포인트. 응답 헤더에 deprecated 표식을 추가한다.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    items, total = await ReportGenerationService.get_reports(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.user_id,
        page=page,
        size=size,
    )
    _mark_deprecated(response)
    return GeneratedReportListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


# -- Get report details -----------------------------------------------------


@router.get(
    "/reports/{report_id}",
    response_model=GeneratedReportResponse,
    summary="Get report status and details (deprecated, archive read-only)",
)
async def get_report(
    response: Response,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """개별 보고서 상세 조회 (archive 읽기 전용). deprecated 헤더 추가."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    report = await ReportGenerationService.get_report(
        db,
        report_id=report_id,
        org_id=current_user.organization_id,
    )
    _mark_deprecated(response)
    return report


# -- Delete report ---------------------------------------------------------


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a generated report",
    responses={
        204: {"description": "Report deleted."},
        404: {"description": "Report not found."},
    },
)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> Response:
    """보고서 삭제.

    트랙 #106 — 이전 S2 D6 정책으로 410 Gone 으로 차단됐으나, v2 (documents-v2)
    에 보고서 삭제 대체 기능이 없어 사용자가 막혔던 결함 해소. ReportGenerationService
    의 delete_report 가 실제 DB row + MinIO 파일 정리를 수행하므로 정상 활성화.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자가 조직에 소속되어 있지 않습니다.",
        )
    await ReportGenerationService.delete_report(
        db=db, report_id=report_id, org_id=current_user.organization_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- Download report -------------------------------------------------------


@router.get(
    "/reports/{report_id}/download",
    summary="Download a generated report (deprecated, archive read-only)",
    description=(
        "Stream the completed report file. Returns 400 if the report has not "
        "finished generating. 응답 헤더 ``X-Deprecated-API: true`` 가 함께 "
        "내려간다 (archive 파일 다운로드)."
    ),
    responses={
        200: {"description": "Report file streamed as attachment (deprecated)."},
        400: {"description": "Report not yet completed or has no output file."},
        404: {"description": "Report not found."},
    },
)
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
):
    """완료된 archive 보고서 파일 다운로드 (읽기 전용).

    S2 D6: 응답이 StreamingResponse 이므로 서비스 레이어에서 이미 헤더가
    구성되나, deprecated 표식을 함께 내리기 위해 반환 직후 헤더를 주입한다.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    import contextlib

    stream = await ReportGenerationService.download_report(
        db,
        report_id=report_id,
        org_id=current_user.organization_id,
    )
    # StreamingResponse 에도 헤더를 추가할 수 있다. 헤더 속성이 없는 매우 드문
    # 응답 타입이 들어와도 본 기능은 정상 동작해야 하므로 예외는 무시한다.
    with contextlib.suppress(Exception):
        stream.headers[DEPRECATED_HEADER_NAME] = DEPRECATED_HEADER_VALUE
    return stream
