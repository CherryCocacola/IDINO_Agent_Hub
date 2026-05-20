"""Pydantic v2 schemas for the templates module."""

from __future__ import annotations

import uuid
from uuid import UUID
from datetime import datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TemplateCreate(BaseModel):
    """새 문서 템플릿 생성 요청 페이로드.

    template_type은 자유 텍스트로 입력 가능하며(예: 'report', 'proposal', '계약서' 등),
    rendering_mode는 렌더링 방식을 지정한다(기본값: 'jinja2').
    """

    name: str = Field(..., min_length=1, max_length=255, description="템플릿 이름.")
    description: str | None = Field(default=None, max_length=2000, description="템플릿 설명.")
    template_type: str = Field(
        ...,
        max_length=100,
        description="템플릿 유형 — 자유 텍스트 (예: 'report', 'proposal', '계약서').",
    )
    tone: str = Field(
        default="formal",
        max_length=20,
        description="문서 어조 (예: 'formal', 'casual').",
    )
    output_format: str = Field(
        ...,
        max_length=20,
        description="출력 형식 (예: 'docx', 'pdf', 'html', 'pptx').",
    )
    schema_: dict[str, Any] | None = Field(
        default=None,
        alias="schema",
        description="템플릿 변수 정의 JSON 스키마.",
    )
    sample_prompt: str | None = Field(
        default=None,
        max_length=5000,
        description="이 템플릿에 대한 예시 프롬프트.",
    )
    # Jinja2 등 렌더링 방식 지정 ('jinja2' 또는 'structured' 등)
    rendering_mode: str = Field(
        default="jinja2",
        max_length=20,
        description="렌더링 방식 (예: 'jinja2', 'structured').",
    )
    # 이미지 생성 설정 (예: {"provider": "dalle3", "enabled": true})
    # FE 의 image_source 단일 문자열을 저장하는 방식.
    # 핫픽스: FE 가 이 필드로 보내도 schema 에 정의가 없으면 Pydantic extra='ignore' 로
    # 버려져 DALL-E 3 활성화가 DB 에 저장되지 않는 버그를 수정함.
    image_generation_config: dict[str, Any] | None = Field(
        default=None,
        description="이미지 생성 설정 (provider, enabled 등).",
    )


class TemplateUpdate(BaseModel):
    """문서 템플릿 부분 수정 요청 페이로드.

    수정하고 싶은 필드만 전달하면 된다 (나머지는 기존 값 유지).
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    template_type: str | None = Field(
        default=None,
        max_length=100,
        description="템플릿 유형 — 자유 텍스트.",
    )
    tone: str | None = Field(default=None, max_length=20)
    output_format: str | None = Field(default=None, max_length=20)
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    sample_prompt: str | None = Field(default=None, max_length=5000)
    is_active: bool | None = Field(default=None)
    # 렌더링 방식 수정 (None이면 기존 값 유지)
    rendering_mode: str | None = Field(
        default=None,
        max_length=20,
        description="렌더링 방식 수정 (예: 'jinja2', 'structured').",
    )
    # 이미지 생성 설정 수정 (None이면 기존 값 유지).
    # FE 가 PUT 요청에 이 키로 값을 전달하면 자동으로 DB 에 반영된다
    # (update_template 의 model_dump(exclude_unset=True) + setattr 패턴).
    image_generation_config: dict[str, Any] | None = Field(
        default=None,
        description="이미지 생성 설정 수정 (provider, enabled 등).",
    )


# ---------------------------------------------------------------------------
# Variable metadata schema
# ---------------------------------------------------------------------------


class TemplateVariableSchema(BaseModel):
    """Jinja2 변수 메타데이터.

    템플릿 파일(DOCX/PPTX)에서 추출된 각 변수의 이름, 타입, 라벨, 설명 등을
    기술한다. 프론트엔드에서 동적 폼을 렌더링할 때 사용된다.

    category 필드로 변수의 입력 방식을 구분한다:
      - "user_input": 사용자가 보고서 생성 시 직접 입력 (보고서명, 기간 등 최소 항목)
      - "session_auto": 로그인 세션 정보로 자동 채움 (소속, 작성자 등)
      - "ai_generated": AI가 소스 문서 기반으로 자동 생성 (보고내용, 문제점 등)
    """

    # 변수 이름 (Jinja2 템플릿 내 {{ name }} 에 해당)
    name: str
    # 변수 타입 — 'string', 'array', 'boolean', 'image' 중 하나
    var_type: str = "string"
    # 사용자에게 보여줄 라벨 (한글 등)
    label: str | None = None
    # 변수에 대한 상세 설명
    description: str | None = None
    # 필수 입력 여부 (기본: True)
    required: bool = True
    # 변수 카테고리 — 입력 방식을 결정한다
    # "user_input": 사용자 직접 입력 (프론트에서 입력 폼 표시)
    # "session_auto": 세션 정보 자동 채움 (프론트에서 입력 폼 안 보임)
    # "ai_generated": AI 자동 생성 (프론트에서 입력 폼 안 보임)
    # 기본값은 "ai_generated" — 기존 데이터와의 하위호환을 위해
    category: str = "ai_generated"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TemplateResponse(BaseModel):
    """문서 템플릿의 읽기 전용 응답 모델.

    DB의 DocumentTemplate ORM 모델을 직렬화한다.
    Jinja2 관련 필드(template_storage_path, jinja2_variables 등)도 포함.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str | None = None
    template_type: str
    tone: str
    output_format: str
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")
    sample_prompt: str | None = None
    is_active: bool
    created_by: UUID
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")

    # -- Jinja2 렌더링 관련 필드 --
    # MinIO에 저장된 Jinja2 템플릿 파일 경로
    template_storage_path: str | None = None
    # 추출된 Jinja2 변수 목록 (JSON)
    jinja2_variables: dict[str, Any] | None = None
    # 렌더링 방식 ('jinja2', 'structured' 등)
    rendering_mode: str = "jinja2"
    # 이미지 자동 생성 설정 (DALL-E 등)
    image_generation_config: dict[str, Any] | None = None


class TemplateUploadResponse(BaseModel):
    """템플릿 파일 업로드 응답 — 추출된 변수 목록 포함.

    파일 업로드 후 Jinja2 엔진이 추출한 변수 정보를 함께 반환하여
    프론트엔드에서 바로 변수 편집 UI를 표시할 수 있도록 한다.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    output_format: str
    rendering_mode: str
    # MinIO 저장 경로
    template_storage_path: str | None = None
    # 파일에서 자동 추출된 Jinja2 변수 목록
    variables: list[TemplateVariableSchema] = []


class TemplateVariablesUpdate(BaseModel):
    """변수 메타데이터 수동 편집 요청.

    프론트엔드에서 변수의 라벨, 타입, 필수 여부 등을 수동으로
    수정할 때 사용한다.
    """

    variables: list[TemplateVariableSchema]


class TemplateListResponse(BaseModel):
    """페이지네이션된 문서 템플릿 목록 응답."""

    items: list[TemplateResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# AI 자동 채우기 (Auto-fill) 스키마
# ---------------------------------------------------------------------------


class AutoFillRequest(BaseModel):
    """AI 자동 채우기 요청.

    사용자가 소스 문서를 지정하면, AI가 해당 문서 내용을 분석하여
    템플릿 변수에 맞는 값을 자동으로 생성한다.

    Attributes:
        source_document_ids: 참고할 소스 문서 ID 목록
        ai_prompt: AI에게 전달할 추가 지시사항 (선택)
    """

    # 참고할 소스 문서 ID 목록 (최소 1개 이상)
    source_document_ids: list[UUID]
    # AI에게 전달할 추가 프롬프트 (예: "간결하게 작성해줘", "영어로 작성해줘")
    ai_prompt: str | None = None


class AutoFillResponse(BaseModel):
    """AI 자동 채우기 응답.

    AI가 생성한 변수값을 context 딕셔너리로 반환한다.
    키는 변수 이름, 값은 AI가 생성한 내용이다.

    Attributes:
        context: 변수명 → 생성된 값 매핑 딕셔너리
    """

    # AI가 생성한 변수값 딕셔너리 (예: {"title": "보고서 제목", "items": ["항목1", "항목2"]})
    context: dict[str, Any]


# ---------------------------------------------------------------------------
# 변수 매핑 에디터 스키마
# ---------------------------------------------------------------------------
# 프론트엔드의 변수 매핑 에디터에서 사용자가 표 셀이나 문단에
# 변수를 직접 매핑할 때 사용하는 요청/응답 스키마


class VariableMapping(BaseModel):
    """개별 변수 매핑 정보.

    사용자가 에디터에서 특정 표 셀이나 문단에 변수를 매핑하면,
    그 위치 정보와 변수 메타데이터를 담는다.

    Attributes:
        location_type: 매핑 위치 유형 — "table_cell" (표 셀) 또는 "paragraph" (문단)
        table_index: 표 인덱스 (location_type이 "table_cell"일 때 필수)
        row: 표의 행 인덱스 (location_type이 "table_cell"일 때 필수)
        col: 표의 열 인덱스 (location_type이 "table_cell"일 때 필수)
        paragraph_index: 문단 인덱스 (location_type이 "paragraph"일 때 필수)
        variable_name: 매핑할 Jinja2 변수명 (예: "장소", "회의일자")
        var_type: 변수 타입 (기본: "string")
        label: 사용자에게 보여줄 라벨 (한글, 선택)
        category: 변수 카테고리 (기본: "ai_generated")
        field_type: 입력란 유형 — "short" (한 줄) 또는 "long" (여러 줄)
    """

    location_type: str = Field(
        ...,
        description="매핑 위치 유형: 'table_cell' 또는 'paragraph'",
    )
    table_index: int | None = Field(
        default=None,
        description="표 인덱스 (table_cell일 때 사용)",
    )
    row: int | None = Field(
        default=None,
        description="표의 행 인덱스 (table_cell일 때 사용)",
    )
    col: int | None = Field(
        default=None,
        description="표의 열 인덱스 (table_cell일 때 사용)",
    )
    paragraph_index: int | None = Field(
        default=None,
        description="문단 인덱스 (paragraph일 때 사용)",
    )
    variable_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="매핑할 Jinja2 변수명 (한글/영문/숫자/언더스코어, 숫자로 시작 불가). "
                    "Python identifier 표준 — Jinja2 가 한글 식별자도 정상 렌더링한다. "
                    "트랙 #106: ASCII-only 정규식 → str.isidentifier() validator 로 교체.",
    )

    @field_validator("variable_name")
    @classmethod
    def _validate_variable_name(cls, v: str) -> str:
        # Python 식별자 검증 — 한글/유니코드 식별자 허용 (Jinja2 호환).
        # 거부: 공백/특수문자/숫자 시작 등 Python 가 식별자로 인정 안 하는 패턴.
        if not v.isidentifier():
            raise ValueError(
                "변수명은 유효한 식별자여야 합니다 "
                "(한글/영문/숫자/언더스코어 사용 가능, 숫자로 시작 불가, 공백/특수문자 금지)."
            )
        return v
    var_type: str = Field(
        default="string",
        description="변수 타입: 'string', 'date', 'array'",
    )
    label: str | None = Field(
        default=None,
        description="사용자에게 보여줄 라벨 (한글)",
    )
    category: str = Field(
        default="ai_generated",
        description="변수 카테고리: 'session_auto', 'user_input', 'ai_generated'",
    )
    field_type: str = Field(
        default="short",
        description="입력란 유형: 'short' (한 줄) 또는 'long' (여러 줄)",
    )


class VariableMappingPayload(BaseModel):
    """변수 매핑 적용 요청 페이로드.

    에디터에서 사용자가 설정한 모든 변수 매핑을 배열로 전달한다.
    서버는 이 매핑 정보를 기반으로 원본 DOCX 파일에 {{ 변수명 }}을
    삽입하고 MinIO에 저장한다.
    """

    mappings: list[VariableMapping] = Field(
        ...,
        description="변수 매핑 목록",
    )
