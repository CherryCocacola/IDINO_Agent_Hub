/**
 * DocumentSchema — Phase 1 수동 작성 TypeScript 타입 (draft)
 *
 * **정답 기준**: `docs/phase1_architecture.md` §2 / 부록 A / 부록 B (2026-04-19 lock).
 *
 * 본 파일은 Phase 4 S1에서 `backend/app/modules/documents_v2/schemas.py`의
 * Pydantic v2 모델로부터 `openapi-typescript`로 자동 생성되어
 * `types/document-schema.generated.ts`로 교체된다. Phase 1에서는 프론트엔드
 * 컴포넌트 스켈레톤 작성이 가능하도록 수동 draft를 둔다.
 *
 * 자동 생성 전환 시점: Phase 4 S1 DoD — `GET /api/v1/v2/documents/schema.json`
 * 엔드포인트 노출 + `scripts/gen-frontend-types.ts` 스크립트 도입.
 *
 * @see docs/phase1_architecture.md
 */

// ─── 기본 타입 ──────────────────────────────────────────────────────────────

/** UUID 문자열(v4). 검증은 백엔드 담당. */
export type UUID = string;

/** ISO 8601 datetime 문자열. */
export type ISODateTimeString = string;

/** ISO 8601 date 문자열 (YYYY-MM-DD). */
export type ISODateString = string;

// ─── DocumentType enum (7종, phase1_architecture.md §2.3) ───────────────────

export type DocumentType =
  | "slide_report"
  | "docx_report"
  | "proposal"
  | "minutes"
  | "one_pager"
  | "weekly_status"
  | "freeform_doc";

export type DocumentMode = "free_generation" | "template_fill";

// ─── DesignTokens (§2.5) ────────────────────────────────────────────────────

/**
 * IDINO 브랜드 토큰. Pydantic과 동일하게 7개 필드.
 * `brand_preset=idino_*`일 때 hex 값은 빌더·렌더러에서 무시하고 IDINO 고정색 적용.
 */
export interface DesignTokens {
  /** hex, default "#0A4FC2" (IDINO 코퍼레이트). */
  primary_color: string;
  /** hex, default "#FF6B35". */
  accent_color: string;
  /** hex, default "#1F2937". */
  text_color: string;
  /** hex, default "#FFFFFF". */
  background_color: string;
  font_family: "Pretendard" | "NotoSansKR" | "System";
  spacing: "compact" | "normal" | "relaxed";
  brand_preset: "idino_default" | "idino_mono" | "custom";
}

// ─── Layout enum (6종, §3.4) ────────────────────────────────────────────────

export type LayoutId =
  | "title_slide"
  | "section_divider"
  | "content_body"
  | "kpi_dashboard"
  | "two_column"
  | "closing";

// ─── ComponentBase 공통 필드 (§2.7) ─────────────────────────────────────────

export interface ComponentBase {
  /** 페이지 내 안정 식별자 ("c1", "c2"...). */
  id: string;
  /** 컴포넌트 단위 잠금 (Mode B). */
  locked: boolean;
  /** Mode B 템플릿 슬롯 이름과 매칭. */
  anchor: string | null;
}

// ─── 22개 컴포넌트 Discriminated Union ──────────────────────────────────────
// 부록 B props 표 1:1 매핑. `type` 필드가 discriminator.

// (1) 텍스트 계열 ─────────────────────────────────────────────────────────

/** SlideTitle — 슬라이드 표제. */
export interface SlideTitleComponent extends ComponentBase {
  type: "SlideTitle";
  text: string;
}

/** SlideSubtitle — 부제. */
export interface SlideSubtitleComponent extends ComponentBase {
  type: "SlideSubtitle";
  text: string;
}

/** Heading — 섹션 제목 (H1~H3). */
export interface HeadingComponent extends ComponentBase {
  type: "Heading";
  text: string;
  level: 1 | 2 | 3;
}

/** Paragraph — 본문 단락. */
export interface ParagraphComponent extends ComponentBase {
  type: "Paragraph";
  text: string;
  emphasis: "normal" | "bold" | "italic";
}

/** Quote — 인용. */
export interface QuoteComponent extends ComponentBase {
  type: "Quote";
  text: string;
  author: string | null;
}

/** Callout — 강조 박스. */
export interface CalloutComponent extends ComponentBase {
  type: "Callout";
  text: string;
  variant: "info" | "warning" | "success" | "danger";
}

/** BulletList 하위 아이템 (2레벨까지). */
export interface BulletItem {
  text: string;
  /** 2레벨 서브 항목. 빈 배열이면 단일 레벨. */
  sub_items: string[];
  emphasis: "normal" | "bold" | "highlight";
}

/** BulletList — 불릿 목록. 최대 12개, 2레벨 제한. */
export interface BulletListComponent extends ComponentBase {
  type: "BulletList";
  items: BulletItem[];
  numbered: boolean;
}

// (2) 데이터 계열 ─────────────────────────────────────────────────────────

/** KPI — 핵심지표 카드. */
export interface KPIComponent extends ComponentBase {
  type: "KPI";
  label: string;
  value: string;
  delta: string | null;
  delta_direction: "up" | "down" | "flat" | null;
  description: string | null;
}

/** DataTable — 표. 최대 20행 × 8열. 각 행 길이 === headers 길이. */
export interface DataTableComponent extends ComponentBase {
  type: "DataTable";
  headers: string[];
  rows: string[][];
  /** 강조 열 인덱스(accent 배경). null이면 없음. */
  emphasis_column_index: number | null;
  caption: string | null;
}

/** Chart 데이터 시리즈. */
export interface ChartSeries {
  name: string;
  values: number[];
}

/** Chart — bar/line/pie. HWPX는 PNG 이미지로 degradation. */
export interface ChartComponent extends ComponentBase {
  type: "Chart";
  chart_type: "bar" | "line" | "pie";
  title: string;
  data: {
    labels: string[];
    series: ChartSeries[];
  };
}

/** Timeline 이벤트. */
export interface TimelineEvent {
  date: string;
  title: string;
  description: string | null;
}

/** Timeline — 시간순 이벤트 표시. */
export interface TimelineComponent extends ComponentBase {
  type: "Timeline";
  events: TimelineEvent[];
}

// (3) 미디어 계열 ─────────────────────────────────────────────────────────

/**
 * Image — 단일 이미지.
 * 제약: `src` 또는 `prompt` 둘 중 하나는 반드시 존재.
 */
export interface ImageComponent extends ComponentBase {
  type: "Image";
  /** 이미 업로드된 MinIO URL 또는 외부 URL. */
  src: string | null;
  /** 생성 프롬프트(DALL-E 3 / Unsplash). `src`가 없을 때 사용. */
  prompt: string | null;
  alt: string;
  caption: string | null;
}

/** ImageGrid 내부 이미지 (2~4개). */
export interface ImageGridItem {
  src: string | null;
  prompt: string | null;
  alt: string;
  caption: string | null;
}

/** ImageGrid — 2~4장 그리드. */
export interface ImageGridComponent extends ComponentBase {
  type: "ImageGrid";
  images: ImageGridItem[];
}

/** IconRow 아이템 (lucide 아이콘 이름). */
export interface IconRowItem {
  icon: string;
  label: string;
  description: string | null;
}

/** IconRow — 아이콘+라벨 행. HWPX는 BulletList로 degradation. */
export interface IconRowComponent extends ComponentBase {
  type: "IconRow";
  items: IconRowItem[];
}

// (4) 레이아웃 계열 ───────────────────────────────────────────────────────
// 컨테이너형 컴포넌트는 내부에 다시 Component 배열을 가진다(재귀).

/** TwoColumn — 2단 컨테이너. */
export interface TwoColumnComponent extends ComponentBase {
  type: "TwoColumn";
  left: Component[];
  right: Component[];
  ratio: "50-50" | "60-40" | "40-60";
}

/** ThreeColumn — 3단 컨테이너 (columns.length === 3). */
export interface ThreeColumnComponent extends ComponentBase {
  type: "ThreeColumn";
  columns: Component[][];
}

/** Hero — 표지 히어로 영역. */
export interface HeroComponent extends ComponentBase {
  type: "Hero";
  title: string;
  subtitle: string | null;
  background: "primary" | "accent" | "image";
  image: ImageGridItem | null;
}

/** Comparison — 좌/우 비교 표. */
export interface ComparisonComponent extends ComponentBase {
  type: "Comparison";
  left: {
    title: string;
    items: string[];
  };
  right: {
    title: string;
    items: string[];
  };
}

// (5) 보고서 특화 컴포넌트 (§3.2 #19~22) ──────────────────────────────────

/** ExecutiveSummary — 경영진 요약 (bullets 3~5개 권장). */
export interface ExecutiveSummaryComponent extends ComponentBase {
  type: "ExecutiveSummary";
  bullets: string[];
  conclusion: string;
}

/** RiskMatrix 리스크 항목. likelihood/impact는 1~5 스케일. */
export interface RiskItem {
  title: string;
  likelihood: 1 | 2 | 3 | 4 | 5;
  impact: 1 | 2 | 3 | 4 | 5;
  mitigation: string;
}

/** RiskMatrix — 리스크 매트릭스. */
export interface RiskMatrixComponent extends ComponentBase {
  type: "RiskMatrix";
  risks: RiskItem[];
}

/** ActionItem — 액션 아이템 단일 항목. */
export interface ActionItem {
  text: string;
  owner: string;
  due: ISODateString;
  status: "pending" | "in_progress" | "done";
}

/** ActionItemList — 액션 아이템 목록 (회의록 등에서 사용). */
export interface ActionItemListComponent extends ComponentBase {
  type: "ActionItemList";
  items: ActionItem[];
}

/** Attendee — 회의 참석자. */
export interface Attendee {
  name: string;
  role: string | null;
  present: boolean;
}

/** AttendeeList — 회의 참석자 목록. */
export interface AttendeeListComponent extends ComponentBase {
  type: "AttendeeList";
  attendees: Attendee[];
}

// ─── Component discriminated union (22종) ───────────────────────────────────

export type Component =
  | SlideTitleComponent
  | SlideSubtitleComponent
  | HeadingComponent
  | ParagraphComponent
  | QuoteComponent
  | CalloutComponent
  | BulletListComponent
  | KPIComponent
  | DataTableComponent
  | ChartComponent
  | TimelineComponent
  | ImageComponent
  | ImageGridComponent
  | IconRowComponent
  | TwoColumnComponent
  | ThreeColumnComponent
  | HeroComponent
  | ComparisonComponent
  | ExecutiveSummaryComponent
  | RiskMatrixComponent
  | ActionItemListComponent
  | AttendeeListComponent;

/** Component의 `type` discriminator 리터럴 목록. */
export type ComponentType = Component["type"];

// ─── Page (§2.6) ────────────────────────────────────────────────────────────

export type PageKind = "slide" | "section";

export interface Page {
  /** "p1", "p2"... 안정 식별자. */
  id: string;
  page_kind: PageKind;
  layout: LayoutId;
  title: string | null;
  /** Mode B에서 true면 LLM이 페이지 전체 수정 금지. */
  locked: boolean;
  components: Component[];
  /** slide 전용 발표자 노트. */
  speaker_notes: string | null;
  page_number_visible: boolean;
}

// ─── Metadata (§2.8) ────────────────────────────────────────────────────────

/** Citations — 근거 청크 인용. RAG 결과 페이로드. */
export interface Citation {
  id: string;
  chunk_id: string;
  document_id: UUID;
  excerpt: string;
}

export interface DocumentMetadata {
  created_at: ISODateTimeString;
  updated_at: ISODateTimeString;
  generated_by_user_id: UUID | null;
  llm_provider: "openai" | "azure" | "gemini" | "claude" | "vllm" | null;
  llm_model: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  source_document_ids: UUID[];
  source_chat_session_id: UUID | null;
  citations: Citation[];
  /** 빌더에서 graceful degradation된 컴포넌트 id 목록 (주로 HWPX). */
  degraded_components: string[];
}

// ─── DocumentSchema 루트 (§2.2) ─────────────────────────────────────────────

export interface DocumentSchema {
  document_id: UUID;
  schema_version: "1.0";
  type: DocumentType;
  mode: DocumentMode;
  /** mode === "template_fill"일 때만 non-null. */
  template_id: UUID | null;
  design_tokens: DesignTokens;
  /** 최소 1페이지. */
  pages: Page[];
  metadata: DocumentMetadata;
}

// ─── Export 포맷 enum (§3.6) ────────────────────────────────────────────────

export type ExportFormat = "pptx" | "docx" | "hwpx" | "pdf" | "html";

// ─── 타입 가드 유틸 (Phase 4 S1 구현) ───────────────────────────────────────

/**
 * Component의 `type` 필드를 확인하는 type predicate.
 * ComponentSwitch 레지스트리에서 사용.
 */
export function isComponentOfType<T extends ComponentType>(
  component: Component,
  type: T,
): component is Extract<Component, { type: T }> {
  return component.type === type;
}
