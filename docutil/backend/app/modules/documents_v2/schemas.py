"""documents_v2 Pydantic schemas — DocumentSchema v1.0.

phase1_architecture.md §2 와 부록 A / B 를 정답으로 본 1:1 매칭 정의.

- Pydantic v2 Discriminated Union (Field(discriminator="type")) 기반 22 컴포넌트.
- ``DocumentSchema`` 자체를 LLM Structured Output 의 JSON Schema 로 사용한다.
  (``DocumentSchema.model_json_schema()``).
- 본 모듈은 Phase 1 draft 이며, P2 모듈 구조 상 ``schemas.py`` 단일 파일로
  유지한다 (architecture.md P2 조항의 예외 허용).

LLM structured output 고려사항:
- OpenAI strict JSON Schema 모드는 oneOf + discriminator 를 공식 지원.
- Gemini 는 부분 지원 → ``StrictSchemaFallback`` 평탄화 버전은 LLMClient 층에서
  생성 (P1 단일 구현). 본 스키마는 OpenAI 기준의 canonical 정의.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums (Literal 로 표현하여 JSON Schema enum 으로 자동 변환)
# ---------------------------------------------------------------------------

DocumentType = Literal[
    "slide_report",
    "docx_report",
    "proposal",
    "minutes",
    "one_pager",
    "weekly_status",
    "freeform_doc",
]

Mode = Literal["free_generation", "template_fill"]

PageKind = Literal["slide", "section"]

LayoutId = Literal[
    # MVP 6 (S1)
    "title_slide",
    "section_divider",
    "content_body",
    "kpi_dashboard",
    "two_column",
    "closing",
]

BrandPreset = Literal["idino_default", "idino_mono", "custom"]
FontFamily = Literal["Pretendard", "NotoSansKR", "System"]
Spacing = Literal["compact", "normal", "relaxed"]

SchemaVersion = Literal["1.0"]


# ---------------------------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------------------------


class DesignTokens(BaseModel):
    """IDINO 브랜드 토큰.

    phase1_architecture.md §2.5 와 동일. brand_preset 이 idino_* 인 경우
    hex 필드는 PPTX 빌더에서 무시되고 IDINO 마스터 색상이 우선된다.
    """

    model_config = ConfigDict(extra="forbid")

    primary_color: str = Field(
        default="#0A4FC2",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="IDINO 코퍼레이트 색상(기본).",
    )
    accent_color: str = Field(
        default="#FF6B35",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    text_color: str = Field(
        default="#1F2937",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    background_color: str = Field(
        default="#FFFFFF",
        pattern=r"^#[0-9A-Fa-f]{6}$",
    )
    font_family: FontFamily = "Pretendard"
    spacing: Spacing = "normal"
    brand_preset: BrandPreset = "idino_default"


# ---------------------------------------------------------------------------
# Component Base
# ---------------------------------------------------------------------------


class ComponentBase(BaseModel):
    """모든 컴포넌트의 공통 기반. discriminator 에는 포함되지 않는다."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        pattern=r"^c\d+$",
        description="페이지 내 안정 식별자. 예: 'c1', 'c2'.",
    )
    locked: bool = Field(
        default=False,
        description="Mode B 에서 True 면 LLM 수정 금지.",
    )
    anchor: str | None = Field(
        default=None,
        description="Mode B 에서 슬롯 이름과 매칭.",
        max_length=128,
    )


# ---------------------------------------------------------------------------
# 22 Components — Discriminated Union payload types
# ---------------------------------------------------------------------------

# 1. SlideTitle -------------------------------------------------------------


class SlideTitleComponent(ComponentBase):
    type: Literal["SlideTitle"] = "SlideTitle"
    text: str = Field(..., min_length=1, max_length=200)


# 2. SlideSubtitle ---------------------------------------------------------


class SlideSubtitleComponent(ComponentBase):
    type: Literal["SlideSubtitle"] = "SlideSubtitle"
    text: str = Field(..., min_length=1, max_length=300)


# 3. Heading ---------------------------------------------------------------


class HeadingComponent(ComponentBase):
    type: Literal["Heading"] = "Heading"
    text: str = Field(..., min_length=1, max_length=200)
    level: Literal[1, 2, 3]


# 4. Paragraph -------------------------------------------------------------


class ParagraphComponent(ComponentBase):
    type: Literal["Paragraph"] = "Paragraph"
    text: str = Field(..., min_length=1)
    emphasis: Literal["normal", "bold", "italic"] = "normal"


# 5. Quote -----------------------------------------------------------------


class QuoteComponent(ComponentBase):
    type: Literal["Quote"] = "Quote"
    text: str = Field(..., min_length=1)
    author: str | None = None


# 6. Callout ---------------------------------------------------------------


class CalloutComponent(ComponentBase):
    type: Literal["Callout"] = "Callout"
    text: str = Field(..., min_length=1)
    variant: Literal["info", "warning", "success", "danger"] = "info"


# 7. BulletList ------------------------------------------------------------


class BulletItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    sub_items: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="2 레벨 제한. 각 항목은 문자열.",
    )
    emphasis: Literal["normal", "bold", "highlight"] = "normal"


class BulletListComponent(ComponentBase):
    type: Literal["BulletList"] = "BulletList"
    items: list[BulletItem] = Field(..., min_length=1, max_length=12)
    numbered: bool = False


# 8. KPI -------------------------------------------------------------------


class KPIComponent(ComponentBase):
    type: Literal["KPI"] = "KPI"
    label: str = Field(..., min_length=1, max_length=80)
    value: str = Field(..., min_length=1, max_length=40)
    delta: str | None = Field(default=None, max_length=40)
    delta_direction: Literal["up", "down", "flat"] | None = None
    description: str | None = Field(default=None, max_length=200)


# 9. DataTable -------------------------------------------------------------


class DataTableComponent(ComponentBase):
    type: Literal["DataTable"] = "DataTable"
    headers: list[str] = Field(..., min_length=1, max_length=8)
    rows: list[list[str]] = Field(..., min_length=0, max_length=20)
    emphasis_column_index: int | None = Field(default=None, ge=0)
    caption: str | None = None

    @model_validator(mode="after")
    def _validate_rectangular(self) -> "DataTableComponent":
        header_len = len(self.headers)
        for idx, row in enumerate(self.rows):
            if len(row) != header_len:
                raise ValueError(
                    f"rows[{idx}] 길이 {len(row)} 가 headers 길이 {header_len} 와 다릅니다."
                )
        if (
            self.emphasis_column_index is not None
            and self.emphasis_column_index >= header_len
        ):
            raise ValueError("emphasis_column_index 가 headers 범위를 벗어났습니다.")
        return self


# 10. Chart ----------------------------------------------------------------


class ChartSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    values: list[float]


class ChartData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    labels: list[str] = Field(..., min_length=1, max_length=24)
    series: list[ChartSeries] = Field(..., min_length=1, max_length=6)

    @model_validator(mode="after")
    def _validate_series_length(self) -> "ChartData":
        expected = len(self.labels)
        for s in self.series:
            if len(s.values) != expected:
                raise ValueError(
                    f"series[{s.name}].values 길이가 labels 길이({expected}) 와 다릅니다."
                )
        return self


class ChartComponent(ComponentBase):
    type: Literal["Chart"] = "Chart"
    chart_type: Literal["bar", "line", "pie"]
    title: str = Field(..., min_length=1)
    data: ChartData


# 11. Image ----------------------------------------------------------------


class ImageComponent(ComponentBase):
    type: Literal["Image"] = "Image"
    src: str | None = Field(
        default=None,
        description="URL 또는 MinIO 키. prompt 와 최소 하나 필수.",
    )
    prompt: str | None = Field(
        default=None,
        description="이미지 자동 생성 프롬프트. src 와 최소 하나 필수.",
    )
    alt: str = Field(..., min_length=1, max_length=200)
    caption: str | None = None

    @model_validator(mode="after")
    def _require_src_or_prompt(self) -> "ImageComponent":
        if not self.src and not self.prompt:
            raise ValueError("Image 는 src 또는 prompt 중 하나 이상이 필요합니다.")
        return self


# 12. Timeline -------------------------------------------------------------


class TimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str = Field(..., description="ISO-8601 권장. 자유 텍스트 허용 (예: 'Q1').")
    title: str = Field(..., min_length=1)
    description: str | None = None


class TimelineComponent(ComponentBase):
    type: Literal["Timeline"] = "Timeline"
    events: list[TimelineEvent] = Field(..., min_length=1, max_length=10)


# 13. ImageGrid ------------------------------------------------------------


class ImageGridItem(BaseModel):
    """ImageGrid 내 개별 이미지. ImageComponent 와 동일 의미이나 안쪽 id 는 선택."""

    model_config = ConfigDict(extra="forbid")

    src: str | None = None
    prompt: str | None = None
    alt: str
    caption: str | None = None

    @model_validator(mode="after")
    def _require_src_or_prompt(self) -> "ImageGridItem":
        if not self.src and not self.prompt:
            raise ValueError("ImageGridItem 은 src 또는 prompt 중 하나 이상이 필요합니다.")
        return self


class ImageGridComponent(ComponentBase):
    type: Literal["ImageGrid"] = "ImageGrid"
    images: list[ImageGridItem] = Field(..., min_length=2, max_length=4)


# 14. IconRow --------------------------------------------------------------


class IconItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    icon: str = Field(
        ...,
        min_length=1,
        description="lucide 아이콘 이름 (예: 'rocket').",
    )
    label: str = Field(..., min_length=1, max_length=40)
    description: str | None = None


class IconRowComponent(ComponentBase):
    type: Literal["IconRow"] = "IconRow"
    items: list[IconItem] = Field(..., min_length=2, max_length=6)


# 15~17. Layout containers --------------------------------------------------
#
# TwoColumn / ThreeColumn 은 좌/우(또는 3 개 열) 안에 컴포넌트를 포함한다.
# 재귀 Union 은 Pydantic v2 forward ref 로 정의한다.


class TwoColumnComponent(ComponentBase):
    type: Literal["TwoColumn"] = "TwoColumn"
    left: list["Component"] = Field(..., min_length=1, max_length=6)
    right: list["Component"] = Field(..., min_length=1, max_length=6)
    ratio: Literal["50-50", "60-40", "40-60"] = "50-50"


class ThreeColumnComponent(ComponentBase):
    type: Literal["ThreeColumn"] = "ThreeColumn"
    columns: list[list["Component"]] = Field(..., min_length=3, max_length=3)

    @field_validator("columns")
    @classmethod
    def _each_column_nonempty(cls, v: list[list["Component"]]) -> list[list["Component"]]:
        for idx, col in enumerate(v):
            if len(col) == 0:
                raise ValueError(f"ThreeColumn.columns[{idx}] 가 비어있습니다.")
            if len(col) > 6:
                raise ValueError(f"ThreeColumn.columns[{idx}] 는 최대 6 개까지 허용.")
        return v


# 17. Hero -----------------------------------------------------------------


class HeroImage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    src: str | None = None
    prompt: str | None = None
    alt: str

    @model_validator(mode="after")
    def _require_src_or_prompt(self) -> "HeroImage":
        if not self.src and not self.prompt:
            raise ValueError("HeroImage 는 src 또는 prompt 중 하나 이상이 필요합니다.")
        return self


class HeroComponent(ComponentBase):
    type: Literal["Hero"] = "Hero"
    title: str = Field(..., min_length=1, max_length=120)
    subtitle: str | None = Field(default=None, max_length=200)
    background: Literal["primary", "accent", "image"] = "primary"
    image: HeroImage | None = None


# 18. Comparison -----------------------------------------------------------


class ComparisonSide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=80)
    items: list[str] = Field(..., min_length=1, max_length=8)


class ComparisonComponent(ComponentBase):
    type: Literal["Comparison"] = "Comparison"
    left: ComparisonSide
    right: ComparisonSide


# 19. ExecutiveSummary -----------------------------------------------------


class ExecutiveSummaryComponent(ComponentBase):
    type: Literal["ExecutiveSummary"] = "ExecutiveSummary"
    bullets: list[str] = Field(..., min_length=3, max_length=5)
    conclusion: str = Field(..., min_length=1)


# 20. RiskMatrix -----------------------------------------------------------


class RiskEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=120)
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    mitigation: str = Field(..., min_length=1)


class RiskMatrixComponent(ComponentBase):
    type: Literal["RiskMatrix"] = "RiskMatrix"
    risks: list[RiskEntry] = Field(..., min_length=1, max_length=12)


# 21. ActionItemList -------------------------------------------------------


class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1, max_length=80)
    due: date
    status: Literal["pending", "in_progress", "done"] = "pending"


class ActionItemListComponent(ComponentBase):
    type: Literal["ActionItemList"] = "ActionItemList"
    items: list[ActionItem] = Field(..., min_length=1, max_length=20)


# 22. AttendeeList ---------------------------------------------------------


class Attendee(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=80)
    role: str | None = Field(default=None, max_length=80)
    present: bool = True


class AttendeeListComponent(ComponentBase):
    type: Literal["AttendeeList"] = "AttendeeList"
    attendees: list[Attendee] = Field(..., min_length=1, max_length=50)


# ---------------------------------------------------------------------------
# Discriminated Union
# ---------------------------------------------------------------------------


Component = Annotated[
    Union[
        SlideTitleComponent,
        SlideSubtitleComponent,
        HeadingComponent,
        ParagraphComponent,
        QuoteComponent,
        CalloutComponent,
        BulletListComponent,
        KPIComponent,
        DataTableComponent,
        ChartComponent,
        ImageComponent,
        TimelineComponent,
        ImageGridComponent,
        IconRowComponent,
        TwoColumnComponent,
        ThreeColumnComponent,
        HeroComponent,
        ComparisonComponent,
        ExecutiveSummaryComponent,
        RiskMatrixComponent,
        ActionItemListComponent,
        AttendeeListComponent,
    ],
    Field(discriminator="type"),
]


# 재귀 union 결합 (TwoColumn / ThreeColumn 의 forward ref).
TwoColumnComponent.model_rebuild()
ThreeColumnComponent.model_rebuild()


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


class Page(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=r"^p\d+$")
    page_kind: PageKind
    layout: LayoutId
    title: str | None = Field(default=None, max_length=200)
    locked: bool = False
    components: list[Component] = Field(..., min_length=1, max_length=10)
    speaker_notes: str | None = None
    page_number_visible: bool = True


# ---------------------------------------------------------------------------
# Metadata / Citation
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        pattern=r"^r\d+$",
        description="본문 내 [cite: rN] 마커와 매칭되는 ID.",
    )
    chunk_id: str | None = None
    document_id: UUID | None = None
    excerpt: str = Field(..., min_length=1)


class DocumentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    updated_at: datetime
    generated_by_user_id: UUID | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    source_document_ids: list[UUID] = Field(default_factory=list)
    source_chat_session_id: UUID | None = None
    citations: list[Citation] = Field(default_factory=list)
    degraded_components: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DocumentSchema (루트)
# ---------------------------------------------------------------------------


class DocumentSchema(BaseModel):
    """Phase 1 DocumentSchema v1.0.

    LLM Structured Output 의 JSON Schema 로 그대로 사용된다
    (``DocumentSchema.model_json_schema()``).

    DB 저장: ``tb_documents_v2.document_schema`` JSONB 컬럼에 dict 로 직렬화.
    """

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    schema_version: SchemaVersion = "1.0"
    type: DocumentType
    mode: Mode
    template_id: UUID | None = None
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)
    pages: list[Page] = Field(..., min_length=1, max_length=20)
    metadata: DocumentMetadata

    @model_validator(mode="after")
    def _template_id_consistency(self) -> "DocumentSchema":
        if self.mode == "template_fill" and self.template_id is None:
            raise ValueError("mode='template_fill' 에서는 template_id 가 필수입니다.")
        if self.mode == "free_generation" and self.template_id is not None:
            raise ValueError(
                "mode='free_generation' 에서는 template_id 가 null 이어야 합니다."
            )
        return self


# ---------------------------------------------------------------------------
# Phase 4 S1 D7 — Router Request/Response 모델
# ---------------------------------------------------------------------------
#
# 주의: 위의 DocumentSchema (Phase 1 설계) 는 수정 금지 영역이다.
# 아래 모델들은 FastAPI 라우터의 진입/응답 계약만을 정의한다.
# Pydantic v2 BaseModel + ConfigDict(extra="forbid") 로 엄격 모드 유지.


class GenerateDocumentRequest(BaseModel):
    """POST /v2/documents 요청 바디 (Mode A 자유 생성).

    D8 에서 Mode B (``template_fill``) 를 추가할 때는 ``mode`` 필드 값을
    확장하고 ``template_id`` 를 required 로 만드는 별도 모델을 둔다.
    """

    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=8_000,
        description="사용자 자연어 요청. 예: 'Q1 매출 슬라이드 3장'",
    )
    document_type: DocumentType = Field(
        ...,
        description="생성할 문서 타입 (7종 중 하나).",
    )
    mode: Mode = Field(
        default="free_generation",
        description="생성 모드. D7 기준 'free_generation' 만 허용, "
        "'template_fill' 은 D8 에서 활성화.",
    )
    source_document_ids: list[UUID] | None = Field(
        default=None,
        max_length=10,
        description="RAG 근거로 사용할 업로드 문서 ID 목록. "
        "None 이면 조직 전역 에이전틱 검색. 최대 10개 "
        "(Phase 4 S1 validation — P0-1 수정: 토큰·메모리 폭증 방지).",
    )
    agent_id: UUID | None = Field(
        default=None,
        description="사용할 에이전트. null 이면 시스템 기본 프롬프트만 사용.",
    )
    design_tokens: DesignTokens | None = Field(
        default=None,
        description="브랜드 토큰 오버라이드. null 이면 idino_default.",
    )


class DocumentV2Response(BaseModel):
    """단건 조회/생성 응답 스키마 — ORM ``DocumentV2`` 를 변환한 DTO."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    organization_id: UUID
    generated_by_user_id: UUID | None = None
    agent_id: UUID | None = None
    template_id: UUID | None = None
    document_type: str
    mode: str
    title: str
    status: str
    error_message: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    created_at: datetime
    completed_at: datetime | None = None
    document_schema: dict = Field(
        ...,
        description="DocumentSchema JSON (``schemas.DocumentSchema`` 와 1:1).",
    )


class PaginatedDocumentListResponse(BaseModel):
    """GET /v2/documents 페이지네이션 응답."""

    model_config = ConfigDict(extra="forbid")

    items: list[DocumentV2Response]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Phase 4 S1 D8 — PATCH /v2/documents/{id} 요청 스키마
# ---------------------------------------------------------------------------
#
# v1.2 Q10 의 Partial DocumentSchema 규약에 맞춰 3종 discriminator 로 단순화
# 한다. RFC 6902 JSON Patch 는 도입하지 않는다 (단일 사용자 편집 전제).
#
# - ``page``      : pages[page_id] 를 ``data`` 로 교체 (components 배열 포함)
# - ``component`` : pages[page_id].components[component_id] 를 ``data`` 와
#                    shallow 병합. ``type`` discriminator 는 기존 값을 강제로
#                    유지 (무결성 보호).
# - ``tokens``    : design_tokens 를 ``data`` 로 교체 (전체 덮어쓰기).


PatchType = Literal["page", "component", "tokens"]


class PartialDocumentPatch(BaseModel):
    """PATCH /v2/documents/{id} 요청 바디 (Phase 4 S1 D8).

    ``data`` 는 patch_type 별로 의미가 다른 부분 본체이며, 서비스 레이어에서
    discriminator 로 해석한다. Pydantic 재검증을 통과해야 한다.

    - ``page`` 요청 시 ``page_id`` 필수. ``data`` 는 :class:`Page` 전체.
    - ``component`` 요청 시 ``page_id`` + ``component_id`` 필수. ``data`` 는
      병합할 필드만 담는 dict (비어 있어도 됨, ``type`` 필드 변경 금지).
    - ``tokens`` 요청 시 식별자 불필요. ``data`` 는 :class:`DesignTokens` 전체.

    낙관적 락 (선택): ``expected_version`` 을 포함하면 현재 ``schema_version``
    과 비교하여 일치하지 않을 때 409 Conflict 를 반환한다.
    """

    model_config = ConfigDict(extra="forbid")

    patch_type: PatchType
    page_id: str | None = Field(
        default=None,
        pattern=r"^p\d+$",
        description="대상 페이지 id. patch_type='page'|'component' 에 필요.",
    )
    component_id: str | None = Field(
        default=None,
        pattern=r"^c\d+$",
        description="대상 컴포넌트 id. patch_type='component' 에 필요.",
    )
    data: dict = Field(
        default_factory=dict,
        description="patch_type 별 페이로드. page/tokens 는 전체 본체, component 는 병합 필드만.",
    )
    expected_version: int | None = Field(
        default=None,
        ge=1,
        description="낙관적 락. 현재 schema_version 과 일치해야 적용된다. None 이면 락 생략.",
    )

    @model_validator(mode="after")
    def _validate_identifiers(self) -> PartialDocumentPatch:
        """patch_type 별 필수 식별자의 존재 여부를 검증한다."""

        if self.patch_type == "page" and self.page_id is None:
            raise ValueError("patch_type='page' 에는 page_id 가 필요합니다.")
        if self.patch_type == "component" and (
            self.page_id is None or self.component_id is None
        ):
            raise ValueError(
                "patch_type='component' 에는 page_id 와 component_id 가 모두 필요합니다."
            )
        if self.patch_type == "tokens" and (
            self.page_id is not None or self.component_id is not None
        ):
            raise ValueError(
                "patch_type='tokens' 에는 page_id/component_id 를 지정하지 않습니다."
            )
        return self


# ---------------------------------------------------------------------------
# Phase 4 S2 D4 — Export 비동기 작업 요청/상태 응답 스키마
# ---------------------------------------------------------------------------
#
# Celery 기반 비동기 export 작업을 위한 계약. 프론트의 `requestExportJob`,
# `getExportStatus` (`documents-v2.ts`) 와 1:1 매칭되어야 한다.
#
# 상태 머신 (export-menu/types.ts 와 완전히 동일해야 FE 분기가 깨지지 않음):
#     pending  : 작업 등록 직후. Celery worker 픽업 대기 상태.
#     running  : worker 가 빌드 중. progress 는 0-100 정수.
#     completed: 파일 빌드 + (D5 에서) MinIO 업로드 완료. download_url 획득 가능.
#     failed   : 빌더 예외 또는 외부 의존 실패. error 에 한국어 메시지.
#
# D4 범위에서는 MinIO 업로드/presigned URL 은 아직 미구현이므로 완료 상태에서도
# `download_url` 은 null 로 유지된다. D5 에서 채워 넣는다.


ExportFormat = Literal["pptx", "docx", "hwpx", "pdf", "html"]
ExportJobStatus = Literal["pending", "running", "completed", "failed"]


class ExportJobRequest(BaseModel):
    """POST /v2/documents/{id}/export 요청 바디.

    Query parameter `?format=` 도 수용하지만, FE `requestExportJob` 은
    body 로 `{"format": "pptx"}` 형태로 보내므로 body 를 공식 계약으로 둔다.
    """

    model_config = ConfigDict(extra="forbid")

    format: ExportFormat = Field(
        ...,
        description="Export 포맷. pptx/docx/hwpx/pdf/html — S2 범위에선 pptx 만 실제 동작.",
    )


class ExportJobResponse(BaseModel):
    """POST /v2/documents/{id}/export 응답.

    FE `documents-v2.ts` 의 `requestExportJob` 은 `job_id` 필드를 snake_case 로
    받아 camelCase `{ jobId }` 로 매핑한다. 따라서 서버는 snake_case `job_id`
    로 응답한다.
    """

    model_config = ConfigDict(extra="forbid")

    job_id: UUID = Field(
        ...,
        description="생성된 export 작업의 UUID. 상태 조회 엔드포인트의 경로 파라미터로 사용.",
    )


class ExportStatusResponse(BaseModel):
    """GET /v2/documents/exports/{job_id} 응답.

    FE `useExportStatus` 훅이 2 초 간격으로 호출한다. `types.ts` 의
    `ExportStatusResponse` (snake_case) 와 필드명이 일치해야 한다.

    D4 범위에서 `download_url` 은 항상 null — D5 에서 MinIO presigned URL 로 채워진다.
    """

    model_config = ConfigDict(extra="forbid")

    status: ExportJobStatus = Field(
        ...,
        description="작업의 현재 상태 (pending/running/completed/failed).",
    )
    progress: int = Field(
        ...,
        ge=0,
        le=100,
        description="0~100 정수 진행률. D4 는 단계별 고정값 (10/90/100).",
    )
    download_url: str | None = Field(
        default=None,
        description="completed 시 MinIO presigned URL. D5 에서 채움. D4 는 null.",
    )
    error: str | None = Field(
        default=None,
        description="failed 시 한국어 에러 메시지.",
    )
