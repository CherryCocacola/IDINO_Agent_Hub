"""documents_v2 FastAPI 라우터 (Phase 4 S1 D7).

엔드포인트 4종
----------------
- POST   /v2/documents              : Mode A 자유 생성 (DocumentServiceV2.generate)
- GET    /v2/documents              : 목록 조회 (limit/offset/document_type/mode 필터)
- GET    /v2/documents/{id}         : 단건 조회 (org_id 권한 검증)
- PATCH  /v2/documents/{id}         : 부분 패치 (D7 스텁 — 501, D8 본구현 예정)

설계 원칙
--------
- P4 (Router→Service→Integration) 엄수: 라우터는 ``DocumentServiceV2`` 외
  다른 모듈의 서비스를 호출하지 않는다. 목록·단건 조회도 ``DocumentV2``
  ORM 을 SQL 로 질의하는 정도까지 라우터에 허용한다 (integration 층이 따로
  필요 없는 단순 쿼리 경로). 복잡해지면 service.py 로 이관해야 한다.
- 예외 매핑:
    * ``RAGContextError``             → 503 Service Unavailable
    * ``DocumentSchemaValidationError`` → 422 Unprocessable Entity
    * ``DocumentGenerationError``     → 502 Bad Gateway (LLM 외부 실패)
  모든 detail 메시지는 한국어로 제공한다 (P5 에러 핸들링 규칙).
- 조직 스코프: 모든 조회/생성은 ``current_user.organization_id`` 기반이며,
  조회 단계에서도 ``WHERE organization_id = ...`` 을 SQL 레벨로 강제해
  권한 우회를 차단한다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote
from uuid import UUID  # noqa: TC003 — FastAPI 가 런타임에 평가함

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.core.database import get_db
from app.core.dependencies import require_role
from app.modules.documents_v2.exceptions import (
    ConcurrentModificationError,
    DocumentGenerationError,
    DocumentSchemaValidationError,
    DocumentV2Error,
    RAGContextError,
)
from app.modules.documents_v2.models import DocumentV2
from app.modules.documents_v2.schemas import (
    DocumentV2Response,
    ExportJobRequest,
    ExportJobResponse,
    ExportStatusResponse,
    GenerateDocumentRequest,
    PaginatedDocumentListResponse,
    PartialDocumentPatch,
)
from app.modules.documents_v2.service import DocumentServiceV2

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.security import TokenData


# ---------------------------------------------------------------------------
# 라우터 정의
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/v2", tags=["Documents V2"])


# 역할 게이트: 문서 생성은 편집 권한 이상, 조회는 열람 권한까지 허용.
# 트랙 #104(2026-05-19) fix: 'user' role (tb_users default) 도 reader 권한 부여.
_require_author = require_role(["super_admin", "admin", "org_admin", "editor", "member"])
_require_reader = require_role(
    ["super_admin", "admin", "org_admin", "editor", "member", "viewer", "user"]
)


# ---------------------------------------------------------------------------
# 헬퍼 — ORM → DTO 변환
# ---------------------------------------------------------------------------


def _to_response(doc: DocumentV2) -> DocumentV2Response:
    """``DocumentV2`` ORM 인스턴스를 응답 DTO 로 변환한다.

    created_at 은 ORM 의 ``ins_dt`` 컬럼을 사용한다 (``Base`` 의 AuditMixin
    이 주입). completed_at 은 성공 케이스에만 값이 있다.
    """

    return DocumentV2Response(
        id=doc.id,
        organization_id=doc.organization_id,
        generated_by_user_id=doc.generated_by_user_id,
        agent_id=doc.agent_id,
        template_id=doc.template_id,
        document_type=doc.document_type,
        mode=doc.mode,
        title=doc.title,
        status=doc.status,
        error_message=doc.error_message,
        llm_provider=doc.llm_provider,
        llm_model=doc.llm_model,
        prompt_tokens=doc.prompt_tokens,
        completion_tokens=doc.completion_tokens,
        created_at=doc.ins_dt,
        completed_at=doc.completed_at,
        document_schema=doc.document_schema,
    )


def _require_org(current_user: TokenData) -> UUID:
    """current_user 의 organization_id 를 반환하거나 403 을 발생시킨다."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사용자가 조직에 소속되어 있지 않습니다.",
        )
    return current_user.organization_id


# ---------------------------------------------------------------------------
# POST /v2/documents — Mode A 생성
# ---------------------------------------------------------------------------


@router.post(
    "/documents",
    response_model=DocumentV2Response,
    status_code=status.HTTP_202_ACCEPTED,
    summary="자유 생성 모드로 문서 생성",
    description=(
        "사용자 프롬프트 + 에이전트 프롬프트 + RAG 컨텍스트를 조합해 "
        "LLM Structured Outputs 로 ``DocumentSchema`` 를 생성하고 저장한다. "
        "Mode A (free_generation) 만 지원하며 Mode B 는 D8 에서 활성화된다."
    ),
)
async def create_document(
    payload: GenerateDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_author),
) -> DocumentV2Response:
    """Mode A 로 새 문서를 생성한다 (202 Accepted)."""

    org_id = _require_org(current_user)

    # D7: Mode B (template_fill) 는 본 엔드포인트에서 거부한다.
    # D8 에서 전용 처리 분기를 추가할 예정.
    if payload.mode != "free_generation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 엔드포인트는 mode='free_generation' 만 지원합니다.",
        )

    try:
        doc = await DocumentServiceV2.generate(
            db=db,
            user_id=current_user.user_id,
            org_id=org_id,
            prompt=payload.prompt,
            document_type=payload.document_type,
            source_document_ids=payload.source_document_ids,
            agent_id=payload.agent_id,
            design_tokens=(
                payload.design_tokens.model_dump(mode="json") if payload.design_tokens is not None else None
            ),
        )
    except RAGContextError as exc:
        # 외부 RAG 파이프라인 (Qdrant/DB) 실패 — 일시적, 재시도 가능.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc) or "RAG 컨텍스트 조립 중 외부 서비스 오류가 발생했습니다.",
        ) from exc
    except DocumentSchemaValidationError as exc:
        # LLM 이 생성했으나 DocumentSchema 검증 실패 — 클라이언트 관점 재시도 불가.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc) or "LLM 응답이 문서 스키마를 만족하지 못했습니다.",
        ) from exc
    except DocumentGenerationError as exc:
        # 에이전트 조회 실패 / 조직 불일치 / LLM 호출 실패 등.
        # 조직 권한 위반은 명시적으로 403 으로 매핑한다.
        message = str(exc)
        if "다른 조직의 에이전트" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from exc
        if "에이전트를 찾을 수 없습니다" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc
        if "지원하지 않는 문서 타입" in message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message or "문서 생성 LLM 호출에 실패했습니다.",
        ) from exc
    except DocumentV2Error as exc:
        # 상위 베이스 예외 — 위에서 잡히지 않은 경우 일반 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "문서 생성에 실패했습니다.",
        ) from exc

    return _to_response(doc)


# ---------------------------------------------------------------------------
# GET /v2/documents — 목록 조회
# ---------------------------------------------------------------------------


@router.get(
    "/documents",
    response_model=PaginatedDocumentListResponse,
    summary="조직 범위 문서 목록 조회",
)
async def list_documents(
    document_type: str | None = Query(
        default=None,
        description="문서 타입 필터 (slide_report, minutes, proposal 등).",
    ),
    mode: str | None = Query(
        default=None,
        description="모드 필터 (free_generation | template_fill).",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="페이지 크기."),
    offset: int = Query(default=0, ge=0, description="조회 시작 오프셋."),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_reader),
) -> PaginatedDocumentListResponse:
    """조직 범위의 ``DocumentV2`` 목록을 페이지네이션해서 반환한다.

    organization_id 필터는 SQL 레벨에서 적용되며, RBAC 우회를 차단한다.
    최신 생성 순(``ins_dt DESC``)으로 정렬한다.
    """

    org_id = _require_org(current_user)

    base_stmt = select(DocumentV2).where(DocumentV2.organization_id == org_id)
    count_stmt = select(func.count(DocumentV2.id)).where(DocumentV2.organization_id == org_id)

    if document_type is not None:
        base_stmt = base_stmt.where(DocumentV2.document_type == document_type)
        count_stmt = count_stmt.where(DocumentV2.document_type == document_type)
    if mode is not None:
        base_stmt = base_stmt.where(DocumentV2.mode == mode)
        count_stmt = count_stmt.where(DocumentV2.mode == mode)

    # 최신 생성순 + 페이지네이션.
    base_stmt = base_stmt.order_by(DocumentV2.ins_dt.desc()).limit(limit).offset(offset)

    result = await db.execute(base_stmt)
    docs = list(result.scalars().all())

    total_result = await db.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)

    return PaginatedDocumentListResponse(
        items=[_to_response(d) for d in docs],
        total=total,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# GET /v2/documents/{id} — 단건 조회
# ---------------------------------------------------------------------------


@router.get(
    "/documents/{document_id}",
    response_model=DocumentV2Response,
    summary="문서 단건 조회",
)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_reader),
) -> DocumentV2Response:
    """문서 단건을 조회한다.

    404: 문서가 존재하지 않음.
    403: 문서가 존재하지만 타 조직 소속 (존재 여부 노출 최소화 목적으로
    먼저 조직 일치 여부를 검증한 뒤 404 vs 403 을 구분).
    """

    org_id = _require_org(current_user)

    doc = await db.get(DocumentV2, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="요청한 문서를 찾을 수 없습니다.",
        )
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 조직의 문서에는 접근할 수 없습니다.",
        )

    return _to_response(doc)


# ---------------------------------------------------------------------------
# PATCH /v2/documents/{id} — Phase 4 S1 D8 본구현
# ---------------------------------------------------------------------------


@router.patch(
    "/documents/{document_id}",
    response_model=DocumentV2Response,
    summary="DocumentSchema 부분 패치",
    description=(
        "DocumentSchema 의 부분 업데이트를 적용한다 (Q10 결정).\n\n"
        "patch_type:\n"
        "- ``page`` : pages[page_id] 를 ``data`` 로 교체 (components 포함).\n"
        "- ``component`` : 컴포넌트 필드를 병합 (``type`` 필드는 보호).\n"
        "- ``tokens`` : design_tokens 를 교체.\n\n"
        "``expected_version`` 을 포함하면 낙관적 락이 적용되어 다른 사용자가 "
        "먼저 수정한 경우 409 Conflict 를 반환한다."
    ),
)
async def patch_document(
    document_id: UUID,
    payload: PartialDocumentPatch,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_author),
) -> DocumentV2Response:
    """DocumentSchema 부분 패치 (Phase 4 S1 D8).

    상태 코드 매핑
    --------------
    - 200: 성공.
    - 400: patch_type/식별자 불일치, 대상 page/component 미존재, type 변경 시도.
    - 403: 타 조직 문서 접근.
    - 404: 문서 자체가 존재하지 않음.
    - 409: ``expected_version`` 불일치 (낙관적 락 실패).
    - 422: patch 결과 스키마 재검증 실패.
    """

    org_id = _require_org(current_user)

    try:
        doc = await DocumentServiceV2.apply_patch(
            db=db,
            user_id=current_user.user_id,
            org_id=org_id,
            document_id=document_id,
            patch_type=payload.patch_type,
            page_id=payload.page_id,
            component_id=payload.component_id,
            data=payload.data,
            expected_version=payload.expected_version,
        )
    except ConcurrentModificationError as exc:
        # 낙관적 락 실패 — 클라이언트가 최신 버전을 재조회 후 재시도해야 함.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc) or "문서가 다른 사용자에 의해 이미 수정되었습니다.",
        ) from exc
    except DocumentSchemaValidationError as exc:
        # 패치 결과가 DocumentSchema 검증을 통과하지 못함.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc) or "패치 결과 문서 스키마 검증에 실패했습니다.",
        ) from exc
    except DocumentGenerationError as exc:
        # 존재/권한/식별자 관련 실패 — 메시지 기반으로 404/403/400 매핑.
        message = str(exc)
        if "다른 조직" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from exc
        if "찾을 수 없" in message and "페이지" not in message and "컴포넌트" not in message:
            # "요청한 문서를 찾을 수 없습니다." → 404.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc
        # 그 외 (page/component 미존재, type 변경 시도, 식별자 검증) → 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message or "문서 패치 요청이 유효하지 않습니다.",
        ) from exc
    except DocumentV2Error as exc:
        # 상위 베이스 — 위에서 잡히지 않은 경우 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "문서 패치에 실패했습니다.",
        ) from exc

    return _to_response(doc)


# ---------------------------------------------------------------------------
# Phase 4 S2 D4 — Export 비동기 작업 (Celery dispatch + 상태 폴링)
# ---------------------------------------------------------------------------
#
# FE `export-menu` 의 `requestExportJob` / `getExportStatus` 와 1:1 매칭되는
# 2 개 엔드포인트. 실제 파일 빌드는 `app.workers.export_worker` 의
# `generate_document_export` Celery 태스크가 담당하며, 본 라우터는
# DocumentServiceV2 를 통해 dispatch 하고 상태 저장소 (Redis) 에서 조회한다.
#
# 상태 머신 / 응답 필드는 `schemas.ExportStatusResponse` 와
# `frontend/.../export-menu/types.ts` 를 참고.
#
# 경로
# ----
# - POST `/v2/documents/{id}/export` → 202 Accepted + { job_id }
# - GET  `/v2/documents/exports/{job_id}` → 200 + { status, progress, download_url, error }
#
# 예외 매핑
# ---------
# - 문서 없음 / job 만료 → 404
# - 타 조직 문서 / 타 사용자 job → 403
# - 미지원 포맷 / dispatch 실패 → 400 / 502
# - 알 수 없는 내부 오류 → 500 (FastAPI 기본 처리)


@router.post(
    "/documents/{document_id}/export",
    response_model=ExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="문서를 비동기로 export (Celery 작업 등록)",
    description=(
        "DocumentV2 를 지정 포맷으로 변환하는 Celery 작업을 등록하고 job_id 를 "
        "반환한다 (202 Accepted). 실제 빌드는 백그라운드에서 진행되며, "
        "`GET /v2/documents/exports/{job_id}` 로 상태를 폴링해야 한다."
    ),
)
async def request_export(
    document_id: UUID,
    payload: ExportJobRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_author),
) -> ExportJobResponse:
    """Export 작업을 큐잉한다.

    상태 코드 매핑
    --------------
    - 202: 작업 등록 성공. body 에 `job_id`.
    - 400: 미지원 포맷 (``format`` 이 BuildTarget Literal 이 아님).
    - 403: 타 조직 문서 접근.
    - 404: 문서가 존재하지 않음.
    - 502: Celery/RabbitMQ dispatch 실패.
    """

    org_id = _require_org(current_user)

    try:
        job_id = await DocumentServiceV2.request_export(
            db=db,
            user_id=current_user.user_id,
            org_id=org_id,
            document_id=document_id,
            format=payload.format,
        )
    except DocumentGenerationError as exc:
        message = str(exc)
        if "찾을 수 없습니다" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc
        if "다른 조직" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from exc
        if "지원하지 않는 문서 포맷" in message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            ) from exc
        if "dispatch" in message or "등록에 실패" in message:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            ) from exc
        # 그 외 도메인 오류는 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message or "Export 작업 등록에 실패했습니다.",
        ) from exc
    except DocumentV2Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "Export 작업 등록에 실패했습니다.",
        ) from exc

    return ExportJobResponse(job_id=job_id)


@router.get(
    "/documents/exports/{job_id}",
    response_model=ExportStatusResponse,
    summary="Export 작업 상태 조회",
    description=(
        "Celery export 작업의 진행률/완료 상태를 반환한다. 프론트의 "
        "`useExportStatus` 훅이 2 초 간격으로 호출한다. 완료 시 `download_url` "
        "은 D5 에서 MinIO presigned URL 로 채워진다 (현재 D4 는 항상 null)."
    ),
)
async def get_export_status_endpoint(
    job_id: UUID,
    current_user: TokenData = Depends(_require_reader),
) -> ExportStatusResponse:
    """Export 작업 상태를 반환한다.

    상태 코드 매핑
    --------------
    - 200: 상태 반환 성공.
    - 403: 타 조직/타 사용자 작업.
    - 404: job_id 가 만료되었거나 존재하지 않음.
    """

    org_id = _require_org(current_user)

    try:
        state = await DocumentServiceV2.get_export_status(
            job_id=job_id,
            user_id=current_user.user_id,
            org_id=org_id,
        )
    except DocumentGenerationError as exc:
        message = str(exc)
        # 타 조직/타 사용자 권한 위반을 먼저 검사 (403).
        if "다른 조직" in message or "다른 사용자" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from exc
        # Redis 값 파싱 실패 등 운영 이슈.
        if "해석할 수 없습니다" in message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message,
            ) from exc
        # 그 외 (job 만료/없음, Redis 접근 불가) 는 404 로 단순화.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message or "Export 작업 상태를 찾을 수 없습니다.",
        ) from exc
    except DocumentV2Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "Export 작업 상태 조회에 실패했습니다.",
        ) from exc

    return ExportStatusResponse(
        status=state["status"],
        progress=state["progress"],
        download_url=state.get("download_url"),
        error=state.get("error"),
    )


# ---------------------------------------------------------------------------
# Phase 4 S2 D10 — Export 결과 프록시 다운로드
# ---------------------------------------------------------------------------
#
# W4 블로커 (S2 D9 E2E 시연) 해소:
#   - 기존 ``/exports/{job_id}`` 응답의 ``download_url`` 은 MinIO presigned URL
#     이었고, ``MINIO_ENDPOINT`` 가 Docker 내부 hostname (``minio:9000``) 이라
#     FE 브라우저가 resolve 하지 못했다.
#   - URL rewrite 는 AWS SigV4 서명 불일치로 403. 해결책으로 옵션 C (백엔드
#     프록시) 를 채택.
#
# 본 엔드포인트는 기존 ``/reports/{id}/download`` 패턴을 그대로 따른다:
#   1. 서비스 레이어가 권한 검증 + MinIO bytes 획득을 담당.
#   2. 라우터는 StreamingResponse 로 감싸고 RFC 5987 한글 파일명 헤더를 부여.
#
# 예외 매핑 (DocumentGenerationError 의 한국어 메시지로 분기):
#   - "찾을 수 없습니다" / "만료되었거나"  → 404
#   - "아직 완료되지 않은"                → 409 Conflict
#   - "만료되었거나 삭제"                 → 410 Gone
#   - "다른 조직" / "다른 사용자"         → 403
#   - "해석할 수 없습니다" / "접근할 수 없습니다" → 500 / 502
#   - 그 외                              → 502 Bad Gateway (스토리지 의존성 관점)


@router.get(
    "/documents/exports/{job_id}/download",
    summary="Export 결과 파일을 백엔드 프록시로 다운로드",
    description=(
        "완료된 export 작업의 결과물을 MinIO 에서 읽어 StreamingResponse 로 "
        "반환한다. presigned URL 노출을 제거하고, FE 는 access token 기반으로 "
        "바로 다운로드할 수 있다 (기존 `/reports/{id}/download` 패턴과 동일)."
    ),
    responses={
        200: {"description": "파일 바이트를 attachment 로 스트리밍."},
        403: {"description": "타 조직 또는 타 사용자의 작업."},
        404: {"description": "job_id 가 존재하지 않거나 TTL 만료."},
        409: {"description": "작업이 아직 완료되지 않았음."},
        410: {"description": "Storage 에서 파일이 이미 삭제됨."},
    },
)
async def download_export(
    job_id: UUID,
    current_user: TokenData = Depends(_require_reader),
) -> StreamingResponse:
    """Export 결과물을 백엔드 프록시로 다운로드한다 (Phase 4 S2 D10).

    내부적으로 ``DocumentServiceV2.get_export_file`` 을 통해
    권한 검증 + Redis 상태 확인 + MinIO bytes 로드를 수행하고, FastAPI
    StreamingResponse 로 감싸서 반환한다.

    헤더
    ----
    - ``Content-Type``: 포맷에 따른 MIME (PPTX/DOCX/PDF/HWPX/HTML).
    - ``Content-Disposition``: ``attachment; filename*=UTF-8''{encoded}`` 형식.
      한글 문서명 대응을 위해 RFC 5987 percent-encoding 을 사용한다 (프로젝트
      표준 규칙 — ``anti-patterns.md`` 참조).
    """

    org_id = _require_org(current_user)

    try:
        payload, content_type, filename = await DocumentServiceV2.get_export_file(
            job_id=job_id,
            user_id=current_user.user_id,
            org_id=org_id,
        )
    except DocumentGenerationError as exc:
        message = str(exc)
        # 타 조직/타 사용자 → 403.
        if "다른 조직" in message or "다른 사용자" in message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message,
            ) from exc
        # 아직 완료되지 않음 → 409 Conflict (FE 가 폴링 재개할 수 있게 구분).
        if "아직 완료되지 않은" in message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=message,
            ) from exc
        # MinIO 에서 object 가 사라짐 → 410 Gone (파일 만료).
        if "만료되었거나 삭제" in message:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=message,
            ) from exc
        # Redis 값 파싱 실패 등 내부 오류.
        if "해석할 수 없습니다" in message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message,
            ) from exc
        # Redis/스토리지 접근 불가 → 502 Bad Gateway.
        if "접근할 수 없습니다" in message or "가져오지 못했습니다" in message:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=message,
            ) from exc
        # 그 외 (job 만료/없음, 결과 키 누락) 는 404 로 단순화.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message or "Export 결과 파일을 찾을 수 없습니다.",
        ) from exc
    except DocumentV2Error as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc) or "Export 다운로드 요청이 유효하지 않습니다.",
        ) from exc

    # RFC 5987 인코딩 — Korean 파일명 안전 전달 (프로젝트 표준).
    encoded = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{encoded}",
    }
    # 단일 청크 스트리밍 — 평균 PPTX 크기 (<5MB) 에서 충분히 가볍고 단순.
    return StreamingResponse(
        content=iter([payload]),
        media_type=content_type,
        headers=headers,
    )
