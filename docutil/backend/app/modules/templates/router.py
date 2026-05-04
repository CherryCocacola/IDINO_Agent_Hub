"""FastAPI router for document template management endpoints.

All routes in this module are mounted under the ``/templates`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.

기본 CRUD 엔드포인트 외에 Jinja2 템플릿 파일 업로드, 변환, 변수 관리,
파일 미리보기(다운로드) 엔드포인트를 제공한다.
"""

from __future__ import annotations

import uuid
from uuid import UUID

import io
from pathlib import PurePosixPath

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.database import get_db
from app.core.dependencies import require_role

from .schemas import (
    AutoFillResponse,
    TemplateCreate,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
    TemplateUploadResponse,
    TemplateVariableSchema,
    TemplateVariablesUpdate,
    VariableMappingPayload,
)
from .service import TemplateService

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.security import TokenData

router = APIRouter(prefix="", tags=["templates"])

# ---------------------------------------------------------------------------
# Role helpers — 역할 기반 접근 제어
# ---------------------------------------------------------------------------
# _require_admin: 관리자(super_admin, admin, org_admin)만 접근 가능
_require_admin = require_role(["super_admin", "admin", "org_admin"])
# _require_member: 모든 인증된 사용자 접근 가능 (조회 전용 엔드포인트용)
_require_member = require_role(["super_admin", "admin", "org_admin", "editor", "member", "viewer"])

# 파일 확장자 → MIME 타입 매핑 (StreamingResponse에서 사용)
_CONTENT_TYPES: dict[str, str] = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "pdf": "application/pdf",
    "html": "text/html",
}


# ---------------------------------------------------------------------------
# 헬퍼 함수: 조직 소속 확인
# ---------------------------------------------------------------------------


def _check_org(current_user: TokenData) -> UUID:
    """사용자가 조직에 소속되어 있는지 확인하고 org_id를 반환한다.

    소속 조직이 없으면 403 예외를 발생시킨다.
    """
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )
    return current_user.organization_id


# ---------------------------------------------------------------------------
# GET /templates — 템플릿 목록 조회
# ---------------------------------------------------------------------------


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List document templates",
    description="조직의 문서 템플릿 목록을 페이지네이션하여 반환한다.",
)
async def list_templates(
    template_type: str | None = Query(
        default=None,
        description="템플릿 유형으로 필터링 (예: 'report', 'proposal').",
    ),
    page: int = Query(1, ge=1, description="페이지 번호."),
    size: int = Query(20, ge=1, le=100, description="페이지당 항목 수."),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> TemplateListResponse:
    """조직 내 모든 문서 템플릿 목록을 조회한다."""
    org_id = _check_org(current_user)

    items, total = await TemplateService.get_templates(
        db,
        org_id=org_id,
        template_type=template_type,
        page=page,
        size=size,
    )
    return TemplateListResponse(
        items=[TemplateResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /templates — 템플릿 생성 (JSON)
# ---------------------------------------------------------------------------


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a document template",
    description="새 문서 생성 템플릿을 등록한다 (메타데이터만, 파일 업로드는 별도).",
)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateResponse:
    """새 문서 템플릿을 생성한다."""
    org_id = _check_org(current_user)

    template = await TemplateService.create_template(
        db,
        org_id=org_id,
        user_id=current_user.user_id,
        data=data,
    )
    return TemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# POST /templates/upload — 템플릿 파일 업로드 + 변수 자동 추출
# ---------------------------------------------------------------------------


@router.post(
    "/templates/upload",
    response_model=TemplateUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a template file",
    description=(
        "DOCX/PPTX 등의 Jinja2 템플릿 파일을 업로드한다. "
        "파일 내 Jinja2 변수({{ }}, {% %})를 자동 추출하여 응답에 포함한다."
    ),
)
async def upload_template(
    file: UploadFile,
    template_type: str = Form(..., max_length=100, description="템플릿 유형"),
    tone: str = Form(default="formal", max_length=20, description="문서 어조"),
    output_format: str = Form(..., max_length=20, description="출력 형식 (docx, pptx 등)"),
    name: str | None = Form(default=None, max_length=255, description="템플릿 이름 (생략 시 파일명 사용)"),
    description: str | None = Form(default=None, max_length=2000, description="템플릿 설명"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateUploadResponse:
    """Jinja2 템플릿 파일을 업로드하고 자동 추출된 변수 목록을 반환한다."""
    org_id = _check_org(current_user)

    # 업로드된 파일 바이트 읽기
    file_bytes = await file.read()
    filename = file.filename or "template"

    # 서비스 레이어에서 MinIO 업로드 + 변수 추출 + DB 저장
    template = await TemplateService.upload_template(
        db=db,
        org_id=org_id,
        user_id=current_user.user_id,
        file_bytes=file_bytes,
        filename=filename,
        template_type=template_type,
        tone=tone,
        output_format=output_format,
        name=name,
        description=description,
    )

    # 추출된 변수를 TemplateVariableSchema 리스트로 변환
    variables: list[TemplateVariableSchema] = []
    if template.jinja2_variables and "variables" in template.jinja2_variables:
        for var in template.jinja2_variables["variables"]:
            variables.append(
                TemplateVariableSchema(
                    name=var.get("name", ""),
                    var_type=var.get("type", "string"),
                    label=var.get("label"),
                    description=var.get("description"),
                    required=var.get("required", True),
                )
            )

    return TemplateUploadResponse(
        id=template.id,
        name=template.name,
        output_format=template.output_format,
        rendering_mode=template.rendering_mode,
        template_storage_path=template.template_storage_path,
        variables=variables,
    )


# ---------------------------------------------------------------------------
# POST /templates/upload-blank — 빈 양식 업로드 → 자동 Jinja2 변환
# ---------------------------------------------------------------------------


@router.post(
    "/templates/upload-blank",
    response_model=TemplateUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="빈 양식 업로드 → 자동 Jinja2 변환",
    description=(
        "항목/제목만 있는 빈 양식 DOCX/PPTX를 업로드하면, "
        "AI가 구조를 분석하고 각 빈 섹션에 Jinja2 변수를 자동 삽입하여 "
        "템플릿으로 변환한다. Jinja2 문법을 모르는 사용자도 손쉽게 "
        "템플릿을 만들 수 있다."
    ),
)
async def upload_blank_form(
    file: UploadFile,
    template_type: str = Form(..., max_length=100, description="템플릿 유형 (예: 'report', 'proposal')"),
    tone: str = Form(default="formal", max_length=20, description="문서 어조 (예: 'formal', 'casual')"),
    output_format: str = Form(..., max_length=20, description="출력 형식 (docx 또는 pptx)"),
    name: str | None = Form(default=None, max_length=255, description="템플릿 이름 (생략 시 파일명 사용)"),
    description: str | None = Form(default=None, max_length=2000, description="템플릿 설명"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateUploadResponse:
    """빈 양식 파일을 업로드하고 자동으로 Jinja2 변수를 삽입한 템플릿을 생성한다.

    처리 흐름:
      1. 파일 바이트 읽기 및 확장자 확인
      2. analyze_blank_form()으로 빈 양식 구조 분석
      3. auto_generate_jinja2_from_structure()로 Jinja2 변수 자동 삽입
      4. 변환된 파일과 원본을 MinIO에 저장
      5. DB에 rendering_mode='jinja2' + jinja2_variables 저장
      6. TemplateUploadResponse 반환
    """
    org_id = _check_org(current_user)

    # 업로드된 파일의 바이트 데이터를 읽는다
    file_bytes = await file.read()
    filename = file.filename or "blank_form"

    # 서비스 레이어에 위임한다
    template = await TemplateService.upload_blank_form(
        db=db,
        org_id=org_id,
        user_id=current_user.user_id,
        file_bytes=file_bytes,
        filename=filename,
        template_type=template_type,
        tone=tone,
        output_format=output_format,
        name=name,
        description=description,
    )

    # 추출된 변수를 TemplateVariableSchema 리스트로 변환한다
    variables: list[TemplateVariableSchema] = []
    if template.jinja2_variables and "variables" in template.jinja2_variables:
        for var in template.jinja2_variables["variables"]:
            variables.append(
                TemplateVariableSchema(
                    name=var.get("name", ""),
                    var_type=var.get("type", "string"),
                    label=var.get("label"),
                    description=var.get("description"),
                    required=var.get("required", True),
                )
            )

    return TemplateUploadResponse(
        id=template.id,
        name=template.name,
        output_format=template.output_format,
        rendering_mode=template.rendering_mode,
        template_storage_path=template.template_storage_path,
        variables=variables,
    )


# ---------------------------------------------------------------------------
# POST /templates/upload-smart — 스마트 업로드 (파일 분석 후 자동 처리)
# ---------------------------------------------------------------------------


@router.post(
    "/templates/upload-smart",
    response_model=TemplateUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="스마트 업로드 — 파일 분석 후 자동 처리",
    description=(
        "DOCX/PPTX 파일을 업로드하면 내용을 자동 분석하여 적절한 처리를 수행한다. "
        "파일 내에 {{ }} Jinja2 패턴이 있으면 변수 추출(기존 upload 로직), "
        "없으면 빈 양식으로 간주하여 구조 분석 + AI 변수 자동 삽입(기존 upload-blank 로직)을 수행한다. "
        "name과 template_type을 생략하면 파일명/내용에서 자동으로 결정한다."
    ),
)
async def upload_smart(
    file: UploadFile,
    # 템플릿 이름 — 생략하면 파일명(확장자 제외)을 기본값으로 사용한다
    name: str | None = Form(
        default=None,
        max_length=255,
        description="템플릿 이름 (생략 시 파일명 사용)",
    ),
    # 템플릿 설명 — 선택 사항이다
    description: str | None = Form(
        default=None,
        max_length=2000,
        description="템플릿 설명",
    ),
    # 템플릿 유형 — 생략하면 파일 내용에서 키워드 매칭으로 자동 추측한다
    # (예: "회의록", "보고서", "제안서", "기타")
    template_type: str | None = Form(
        default=None,
        max_length=100,
        description="템플릿 유형 (생략 시 파일 내용에서 자동 추측)",
    ),
    # 문서 어조 — 기본값은 "formal" (격식체)
    tone: str = Form(
        default="formal",
        max_length=20,
        description="문서 어조 (예: formal, casual)",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateUploadResponse:
    """파일을 업로드하면 자동으로 분석하여 적절한 처리 경로를 결정한다.

    자동 판단 기준:
      - 파일 내 {{ }} 패턴 존재 → Jinja2 템플릿으로 처리 (변수 자동 추출)
      - 파일 내 {{ }} 패턴 없음 → 빈 양식으로 처리 (구조 분석 + 변수 자동 삽입)

    자동 채움 필드:
      - name 생략 시 → 파일명에서 확장자를 제거한 값 사용
      - template_type 생략 시 → 파일명/내용의 키워드 매칭으로 추측
      - output_format → 파일 확장자에서 자동 결정 (docx/pptx)
    """
    # 사용자가 조직에 소속되어 있는지 확인한다
    org_id = _check_org(current_user)

    # 업로드된 파일의 바이트 데이터를 메모리로 읽어온다
    file_bytes = await file.read()
    filename = file.filename or "template"

    # 서비스 레이어에 모든 판단 로직을 위임한다
    template = await TemplateService.upload_smart(
        db=db,
        org_id=org_id,
        user_id=current_user.user_id,
        file_bytes=file_bytes,
        filename=filename,
        name=name,
        description=description,
        template_type=template_type,
        tone=tone,
    )

    # DB에 저장된 변수 정보를 TemplateVariableSchema 리스트로 변환한다
    # jinja2_variables 구조: {"variables": [{"name": "...", "type": "...", ...}]}
    variables: list[TemplateVariableSchema] = []
    if template.jinja2_variables and "variables" in template.jinja2_variables:
        for var in template.jinja2_variables["variables"]:
            variables.append(
                TemplateVariableSchema(
                    name=var.get("name", ""),
                    var_type=var.get("type", "string"),
                    label=var.get("label"),
                    description=var.get("description"),
                    required=var.get("required", True),
                )
            )

    # 응답에 rendering_mode를 반드시 포함하여 반환한다
    # - "jinja2": {{ }} 패턴이 있어서 Jinja2 변수 파싱 경로로 처리됨
    # - "structured": {{ }} 패턴 없이 구조 분석 경로로 처리됨
    return TemplateUploadResponse(
        id=template.id,
        name=template.name,
        output_format=template.output_format,
        rendering_mode=template.rendering_mode,
        template_storage_path=template.template_storage_path,
        variables=variables,
    )


# ---------------------------------------------------------------------------
# GET /templates/{template_id} — 템플릿 상세 조회
# ---------------------------------------------------------------------------


@router.get(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Get document template details",
)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> TemplateResponse:
    """ID로 단일 문서 템플릿을 조회한다."""
    org_id = _check_org(current_user)

    template = await TemplateService.get_template(
        db,
        template_id=template_id,
        org_id=org_id,
    )
    return TemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# PUT /templates/{template_id} — 템플릿 수정
# ---------------------------------------------------------------------------


@router.put(
    "/templates/{template_id}",
    response_model=TemplateResponse,
    summary="Update a document template",
)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateResponse:
    """기존 문서 템플릿의 필드를 수정한다."""
    org_id = _check_org(current_user)

    template = await TemplateService.update_template(
        db,
        template_id=template_id,
        org_id=org_id,
        data=payload,
    )
    return TemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# DELETE /templates/{template_id} — 템플릿 삭제
# ---------------------------------------------------------------------------


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a document template",
)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> Response:
    """문서 템플릿을 영구 삭제한다.

    반환 타입이 Response 이지만 FastAPI 가 자동으로 response_model 을
    추론하려 하면 204 에는 body 가 허용되지 않아 AssertionError 가
    발생한다. response_model=None 을 명시해 이 추론을 차단한다.
    """
    org_id = _check_org(current_user)

    await TemplateService.delete_template(
        db,
        template_id=template_id,
        org_id=org_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# POST /templates/{template_id}/convert — 일반 문서 → Jinja2 템플릿 변환
# ---------------------------------------------------------------------------


@router.post(
    "/templates/{template_id}/convert",
    response_model=TemplateResponse,
    summary="Convert document to Jinja2 template",
    description=(
        "AI 분석 결과를 적용하여 일반 문서를 Jinja2 템플릿으로 변환한다. "
        "원본 파일의 특정 텍스트를 {{ variable }} 패턴으로 치환한다."
    ),
)
async def convert_to_template(
    template_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateResponse:
    """AI 분석 결과를 바탕으로 원본 문서를 Jinja2 템플릿으로 변환한다.

    요청 body 예시:
        {
            "ai_analysis": {
                "replacements": [
                    {"original": "홍길동", "variable": "author_name"},
                    {"original": "2026년 1분기", "variable": "period"}
                ]
            }
        }
    """
    org_id = _check_org(current_user)

    # body에서 ai_analysis 추출
    ai_analysis = body.get("ai_analysis", {})

    template = await TemplateService.convert_to_template(
        db=db,
        template_id=template_id,
        org_id=org_id,
        ai_analysis=ai_analysis,
    )
    return TemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# POST /templates/{template_id}/auto-fill — AI 자동 채우기
# ---------------------------------------------------------------------------


@router.post(
    "/templates/{template_id}/auto-fill",
    response_model=AutoFillResponse,
    summary="AI 자동 채우기 — 소스 문서 기반 변수값 생성",
    description=(
        "소스 문서의 내용을 AI가 분석하여 템플릿 변수에 맞는 값을 자동으로 생성한다. "
        "사용자가 직접 변수값을 입력하지 않아도 문서 내용을 기반으로 "
        "적절한 값을 AI가 추천해준다."
    ),
)
async def auto_fill_variables(
    template_id: UUID,
    # 참고할 소스 문서 ID 목록 (AI가 이 문서들의 내용을 분석한다)
    source_document_ids: list[UUID] = Body(..., description="참고할 소스 문서 ID 목록"),
    # AI에게 전달할 추가 지시사항 (선택, 예: "간결하게 작성해줘")
    ai_prompt: str | None = Body(default=None, description="AI에게 전달할 추가 지시사항"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> AutoFillResponse:
    """소스 문서 내용을 참고하여 AI가 템플릿 변수값을 자동으로 생성한다.

    처리 흐름:
      1. 템플릿의 jinja2_variables 스키마를 로드한다
      2. source_document_ids로 문서 청크를 DB에서 조회한다
      3. OpenAI GPT-4o에 Structured Outputs로 호출한다
      4. AI가 생성한 변수값을 JSON으로 반환한다

    요청 body 예시:
        {
            "source_document_ids": ["uuid-1", "uuid-2"],
            "ai_prompt": "간결하게 작성해줘"
        }

    응답 예시:
        {
            "context": {
                "title": "2026년 1분기 보고서",
                "author": "홍길동",
                "items": ["항목1", "항목2", "항목3"]
            }
        }
    """
    # 사용자가 조직에 소속되어 있는지 확인한다
    org_id = _check_org(current_user)

    # 서비스 레이어에 위임하여 AI 자동 채우기를 수행한다
    result = await TemplateService.auto_fill_variables(
        db=db,
        template_id=template_id,
        org_id=org_id,
        source_document_ids=source_document_ids,
        ai_prompt=ai_prompt,
    )

    # AutoFillResponse 형식으로 반환한다
    return AutoFillResponse(context=result)


# ---------------------------------------------------------------------------
# GET /templates/{template_id}/variables — 변수 목록 조회
# ---------------------------------------------------------------------------


@router.get(
    "/templates/{template_id}/variables",
    response_model=list[TemplateVariableSchema],
    summary="Get template variables",
    description="템플릿에서 추출된 Jinja2 변수 목록을 반환한다.",
)
async def get_template_variables(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> list[TemplateVariableSchema]:
    """템플릿의 Jinja2 변수 메타데이터를 조회한다."""
    org_id = _check_org(current_user)

    template = await TemplateService.get_template(db, template_id=template_id, org_id=org_id)

    # jinja2_variables가 없으면 빈 리스트 반환
    if not template.jinja2_variables or "variables" not in template.jinja2_variables:
        return []

    # DB에 저장된 변수 데이터를 TemplateVariableSchema 리스트로 변환
    variables: list[TemplateVariableSchema] = []
    for var in template.jinja2_variables["variables"]:
        variables.append(
            TemplateVariableSchema(
                name=var.get("name", ""),
                var_type=var.get("type", var.get("var_type", "string")),
                label=var.get("label"),
                description=var.get("description"),
                required=var.get("required", True),
                category=var.get("category", "ai_generated"),  # DB에 저장된 카테고리 반영
            )
        )

    return variables


# ---------------------------------------------------------------------------
# GET /templates/{template_id}/preview — 템플릿 파일 미리보기(다운로드)
# ---------------------------------------------------------------------------


@router.get(
    "/templates/{template_id}/preview",
    summary="Preview / download template file",
    description="MinIO에 저장된 템플릿 파일을 스트리밍으로 다운로드한다.",
)
async def preview_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> StreamingResponse:
    """템플릿 파일을 스트리밍 응답으로 반환한다 (다운로드/미리보기용)."""
    org_id = _check_org(current_user)

    # 서비스에서 파일 바이트와 파일명을 가져온다
    file_bytes, filename = await TemplateService.get_template_file(
        db=db,
        template_id=template_id,
        org_id=org_id,
    )

    # 파일 확장자로 MIME 타입 결정
    ext = PurePosixPath(filename).suffix.lower().lstrip(".")
    content_type = _CONTENT_TYPES.get(ext, "application/octet-stream")

    # StreamingResponse로 파일 전송 (한글 파일명 RFC 5987 인코딩)
    from urllib.parse import quote

    encoded_filename = quote(filename, safe="")
    return StreamingResponse(
        content=io.BytesIO(file_bytes),
        media_type=content_type,
        headers={
            "Content-Disposition": (f"attachment; filename*=UTF-8''{encoded_filename}"),
        },
    )


# ---------------------------------------------------------------------------
# PUT /templates/{template_id}/variables — 변수 메타데이터 수동 편집
# ---------------------------------------------------------------------------


@router.put(
    "/templates/{template_id}/variables",
    response_model=TemplateResponse,
    summary="Update template variables",
    description="템플릿 변수의 라벨, 타입, 설명, 필수 여부 등 메타데이터를 수동으로 편집한다.",
)
async def update_template_variables(
    template_id: UUID,
    payload: TemplateVariablesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateResponse:
    """사용자가 편집한 변수 메타데이터를 저장한다."""
    org_id = _check_org(current_user)

    # Pydantic 모델 → dict 리스트로 변환하여 서비스에 전달
    variables_data = [v.model_dump() for v in payload.variables]

    template = await TemplateService.update_variables(
        db=db,
        template_id=template_id,
        org_id=org_id,
        variables_data=variables_data,
    )
    return TemplateResponse.model_validate(template)


# ---------------------------------------------------------------------------
# GET /templates/{template_id}/structure — 에디터용 문서 구조 조회
# ---------------------------------------------------------------------------


@router.get(
    "/templates/{template_id}/structure",
    summary="에디터용 문서 구조 조회",
    description=(
        "템플릿 원본 DOCX 파일의 문단/표 구조를 JSON으로 반환한다. "
        "프론트엔드의 변수 매핑 에디터에서 문서 구조를 시각적으로 표시하고, "
        "사용자가 셀/문단에 변수를 클릭으로 매핑할 수 있도록 한다."
    ),
)
async def get_template_structure(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> dict:
    """템플릿 원본 DOCX의 문단/표 구조를 에디터용 JSON으로 반환한다.

    응답 구조:
        {
            "paragraphs": [{"index": 0, "text": "...", "style": "...", ...}],
            "tables": [{"index": 0, "total_rows": N, "total_cols": N, "rows": [...]}],
            "existing_variables": [{"name": "...", "var_type": "...", ...}]
        }
    """
    org_id = _check_org(current_user)

    structure = await TemplateService.get_template_structure(
        db=db,
        template_id=template_id,
        org_id=org_id,
    )
    return structure


# ---------------------------------------------------------------------------
# POST /templates/{template_id}/apply-mapping — 변수 매핑 적용
# ---------------------------------------------------------------------------


@router.post(
    "/templates/{template_id}/apply-mapping",
    response_model=TemplateResponse,
    summary="변수 매핑 적용 — 에디터에서 설정한 매핑을 원본에 반영",
    description=(
        "에디터에서 사용자가 설정한 변수 매핑(표 셀/문단 → 변수명)을 "
        "원본 DOCX 파일에 적용하여 {{ 변수명 }}을 삽입하고, "
        "변환된 파일을 MinIO에 저장한 뒤 jinja2_variables를 업데이트한다."
    ),
)
async def apply_variable_mapping(
    template_id: UUID,
    payload: VariableMappingPayload,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> TemplateResponse:
    """에디터에서 설정한 변수 매핑을 원본 DOCX에 적용한다.

    요청 body 예시:
        {
            "mappings": [
                {
                    "location_type": "table_cell",
                    "table_index": 0,
                    "row": 2,
                    "col": 1,
                    "variable_name": "장소",
                    "var_type": "string",
                    "label": "장 소",
                    "category": "user_input",
                    "field_type": "short"
                },
                {
                    "location_type": "paragraph",
                    "paragraph_index": 0,
                    "variable_name": "제목",
                    "var_type": "string",
                    "label": "문서 제목",
                    "category": "user_input",
                    "field_type": "short"
                }
            ]
        }
    """
    org_id = _check_org(current_user)

    # Pydantic 모델 → dict 리스트로 변환하여 서비스에 전달한다
    mappings_data = [m.model_dump() for m in payload.mappings]

    template = await TemplateService.apply_variable_mapping(
        db=db,
        template_id=template_id,
        org_id=org_id,
        mappings=mappings_data,
    )
    return TemplateResponse.model_validate(template)
