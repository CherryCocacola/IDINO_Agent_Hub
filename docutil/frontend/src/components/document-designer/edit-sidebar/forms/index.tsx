/**
 * edit-sidebar/forms/index.tsx — 컴포넌트 타입 → Form 컴포넌트 리졸버
 *
 * Phase 4 S1 D4 산출물 + S3 D1~D2 + S3 D3~D4 확장. 좌측 편집 사이드바가 선택된
 * `Component` 의 `type` 에 따라 적절한 편집 폼을 렌더한다.
 *
 * 현재 지원 13종: SlideTitle / SlideSubtitle / Heading / Paragraph / Quote /
 *   Callout / BulletList / KPI / DataTable / Timeline / ImageGrid / IconRow / Chart.
 * 나머지 타입은 fallback 메시지를 보여주며 이후 단계에서 추가된다.
 *
 * 설계:
 *   - `resolveFormFor` 는 JSX 를 반환하는 순수함수 컴포넌트 팩토리.
 *   - Props 는 FormProps<C> 구조 그대로 전달되며, 사이드바 컨테이너가 낙관적
 *     로컬 프리뷰(`onLocalPatch`) 와 서버 PATCH debounce(`onCommitPatch`) 를
 *     wiring 한다.
 *   - 6종 Form 컴포넌트와 `useFormPatch` 훅을 barrel export.
 */

"use client";

import type { Component } from "@/types/document-schema";

import { BulletListForm } from "./BulletListForm";
import { CalloutForm } from "./CalloutForm";
import { ChartForm } from "./ChartForm";
import { DataTableForm } from "./DataTableForm";
import { HeadingForm } from "./HeadingForm";
import { IconRowForm } from "./IconRowForm";
import { ImageForm } from "./ImageForm";
import { ImageGridForm } from "./ImageGridForm";
import { KPIForm } from "./KPIForm";
import { ParagraphForm } from "./ParagraphForm";
import { QuoteForm } from "./QuoteForm";
import type { FormProps } from "./shared";
import { SlideSubtitleForm } from "./SlideSubtitleForm";
import { SlideTitleForm } from "./SlideTitleForm";
import { TimelineForm } from "./TimelineForm";

// ── barrel exports ─────────────────────────────────────────────────────────
export { BulletListForm } from "./BulletListForm";
export type { BulletListFormProps } from "./BulletListForm";
export { CalloutForm } from "./CalloutForm";
export type { CalloutFormProps } from "./CalloutForm";
export { ChartForm, CHART_MAX_SERIES, CHART_MAX_LABELS } from "./ChartForm";
export type { ChartFormProps } from "./ChartForm";
export { DataTableForm } from "./DataTableForm";
export type { DataTableFormProps } from "./DataTableForm";
export { HeadingForm } from "./HeadingForm";
export type { HeadingFormProps } from "./HeadingForm";
export { IconRowForm } from "./IconRowForm";
export type { IconRowFormProps } from "./IconRowForm";
export { ImageForm } from "./ImageForm";
export type { ImageFormProps } from "./ImageForm";
export { ImageGridForm, IMAGE_GRID_MAX_IMAGES } from "./ImageGridForm";
export type { ImageGridFormProps } from "./ImageGridForm";
export { KPIForm } from "./KPIForm";
export type { KPIFormProps } from "./KPIForm";
export { ParagraphForm } from "./ParagraphForm";
export type { ParagraphFormProps } from "./ParagraphForm";
export { QuoteForm } from "./QuoteForm";
export type { QuoteFormProps } from "./QuoteForm";
export { SlideSubtitleForm } from "./SlideSubtitleForm";
export type { SlideSubtitleFormProps } from "./SlideSubtitleForm";
export { SlideTitleForm } from "./SlideTitleForm";
export type { SlideTitleFormProps } from "./SlideTitleForm";
export { TimelineForm, TIMELINE_MAX_EVENTS } from "./TimelineForm";
export type { TimelineFormProps } from "./TimelineForm";
export type { FormProps } from "./shared";
export { useFormPatch, FORM_PATCH_DEBOUNCE_MS } from "./useFormPatch";
export type { UseFormPatchResult, UseFormPatchOptions } from "./useFormPatch";

/**
 * resolveFormFor 의 확장 Props — 공통 FormProps 를 다형적으로 받기 위해
 * `component` 를 생략하고 각 Form 컴포넌트가 자체 타입의 component 를 소비한다.
 *
 * D4 타입 안전 설계 핵심:
 *   switch 의 각 branch 에서 `component.type` discriminated union 이 좁혀지므로
 *   개별 `<XxxForm component={component} />` 캐스트 없이 컴파일이 통과한다.
 */
export type ResolveFormProps = {
  component: Component;
  pageId: string;
  onLocalPatch: FormProps<Component>["onLocalPatch"];
  onCommitPatch: FormProps<Component>["onCommitPatch"];
  /**
   * 현재 사용자 조직 ID (선택). `ImageForm` 이 쿼터 표시용으로 사용.
   * 미전달 시 쿼터 UI 는 숨김 (기능은 정상 동작).
   */
  organizationId?: string;
};

/**
 * 주어진 `component.type` 에 맞는 편집 폼 JSX 를 반환한다.
 * D4 에서 지원하지 않는 타입은 사이드바 내부에 안내 메시지를 출력한다.
 */
export function resolveFormFor(props: ResolveFormProps): React.ReactElement {
  const { component, pageId, onLocalPatch, onCommitPatch, organizationId } = props;

  switch (component.type) {
    case "SlideTitle":
      return (
        <SlideTitleForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "SlideSubtitle":
      return (
        <SlideSubtitleForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Heading":
      return (
        <HeadingForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Paragraph":
      return (
        <ParagraphForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Quote":
      return (
        <QuoteForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Callout":
      return (
        <CalloutForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "BulletList":
      return (
        <BulletListForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "KPI":
      return (
        <KPIForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "DataTable":
      return (
        <DataTableForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Timeline":
      return (
        <TimelineForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Image":
      return (
        <ImageForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
          organizationId={organizationId}
        />
      );
    case "ImageGrid":
      return (
        <ImageGridForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "IconRow":
      return (
        <IconRowForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    case "Chart":
      return (
        <ChartForm
          component={component}
          pageId={pageId}
          onLocalPatch={onLocalPatch as FormProps<typeof component>["onLocalPatch"]}
          onCommitPatch={onCommitPatch as FormProps<typeof component>["onCommitPatch"]}
        />
      );
    default:
      return (
        <div
          data-form="Unsupported"
          data-component-type={component.type}
          className="text-sm"
          style={{ color: "var(--doc-text-muted)" }}
        >
          {component.type} 편집은 S3 이후 지원됩니다.
        </div>
      );
  }
}
