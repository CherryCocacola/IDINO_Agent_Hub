/**
 * preview-host.tsx — iframe **내부** 에서 실행되는 호스트 컴포넌트
 *
 * 역할:
 *   1. 부모 shell 로부터 `docutil/token-update`, `docutil/schema-patch-local` 수신.
 *   2. 로컬 state(DocumentSchema 스냅샷)를 갱신하고 `--doc-*` CSS 변수를 override.
 *   3. 컴포넌트 클릭 시 `docutil/element-select` 를 부모에게 송신.
 *   4. 22종 컴포넌트 중 D1~D2 완료 6종만 렌더하고, 나머지는 placeholder.
 *
 * Phase 4 S1 D3 범위:
 *   - 본 파일은 `/preview-host` Next.js 라우트에서 렌더되는 클라이언트 컴포넌트.
 *   - 실제 `/preview-host/page.tsx` 라우트 생성은 **D4 작업** (본 작업 범위 밖,
 *     preview-pane 디렉토리 외부이므로 수정 금지). 본 파일은 라우트가 import 할
 *     "완성된 호스트" 를 미리 제공한다.
 *
 * 제약:
 *   - `apiClient` / `fetch()` 직접 호출 금지 — 본 host 는 네트워크를 전혀 쓰지
 *     않는다. 데이터는 전적으로 parent 로부터 postMessage 로 주입됨.
 *   - hex 하드코딩 금지 — 모든 색상은 `var(--doc-*)`.
 *   - 본격 `<ComponentSwitch>` 22종 분기는 D4+ 과제. 여기서는 D1~D2 6종만 처리.
 */

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BulletList } from "@/components/document-schema/components/BulletList";
import { Callout } from "@/components/document-schema/components/Callout";
import { Chart } from "@/components/document-schema/components/Chart";
import { DataTable } from "@/components/document-schema/components/DataTable";
import { Heading } from "@/components/document-schema/components/Heading";
import { IconRow } from "@/components/document-schema/components/IconRow";
import { ImageGrid } from "@/components/document-schema/components/ImageGrid";
import { KPI } from "@/components/document-schema/components/KPI";
import { Paragraph } from "@/components/document-schema/components/Paragraph";
import { Quote } from "@/components/document-schema/components/Quote";
import { SlideSubtitle } from "@/components/document-schema/components/SlideSubtitle";
import { SlideTitle } from "@/components/document-schema/components/SlideTitle";
import { Timeline } from "@/components/document-schema/components/Timeline";
import type { Component, DesignTokens, DocumentSchema, Page } from "@/types/document-schema";

import {
  buildElementSelectMessage,
  decode,
  mergeTokens,
  type PreviewMessage,
  verifyOrigin,
} from "./postmessage-protocol";

// ─── DesignTokens → CSS 변수 매핑 ────────────────────────────────────────

/**
 * DesignTokens 필드를 `--doc-*` CSS 변수로 변환해 `document.documentElement` 에
 * 주입한다. 필드가 undefined 이면 해당 변수 removeProperty 로 되돌린다.
 *
 * spacing / brand_preset 은 CSS 변수가 아닌 data-* 속성으로 변환해 CSS 선택자
 * (`.document-preview-root[data-spacing="compact"]`)가 파생 변수를 맞게 재계산
 * 하도록 한다.
 */
function applyTokensToDocument(tokens: DesignTokens): void {
  const root = document.documentElement;

  root.style.setProperty("--doc-primary", tokens.primary_color);
  root.style.setProperty("--doc-accent", tokens.accent_color);
  root.style.setProperty("--doc-text", tokens.text_color);
  root.style.setProperty("--doc-background", tokens.background_color);

  // font_family 는 리터럴 enum → CSS 실제 font-family 문자열로 매핑
  const FONT_FAMILY_MAP: Record<DesignTokens["font_family"], string> = {
    Pretendard: '"Pretendard", "Noto Sans KR", ui-sans-serif, system-ui, sans-serif',
    NotoSansKR: '"Noto Sans KR", ui-sans-serif, system-ui, sans-serif',
    System: "ui-sans-serif, system-ui, sans-serif",
  };
  root.style.setProperty("--doc-font-family", FONT_FAMILY_MAP[tokens.font_family]);

  // preview root 데이터 속성 (파생 변수 재계산용)
  root.setAttribute("data-spacing", tokens.spacing);
  root.setAttribute("data-brand-preset", tokens.brand_preset);
  // CSS 셀렉터가 `.document-preview-root` 기준이므로 root 에 클래스 부여.
  root.classList.add("document-preview-root");
}

// ─── 컴포넌트 타입 분기 (D1~D2 6종 + placeholder) ─────────────────────────

interface RenderComponentProps {
  component: Component;
  isSelected: boolean;
  onSelect: (componentId: string) => void;
}

/**
 * MVP 6종 + S3 D1~D2 4종 + S3 D3~D4 3종 = 13종 분기.
 * 나머지 9종은 "unknown" placeholder. 정식 `ComponentSwitch` 는 S3 이후 레지스트리
 * 방식으로 재구축 예정.
 */
function RenderComponent({ component, isSelected, onSelect }: RenderComponentProps) {
  switch (component.type) {
    case "SlideTitle":
      return <SlideTitle component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "SlideSubtitle":
      return <SlideSubtitle component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "Heading":
      return <Heading component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "Paragraph":
      return <Paragraph component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "Quote":
      return <Quote component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "Callout":
      return <Callout component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "BulletList":
      return <BulletList component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "KPI":
      return <KPI component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "DataTable":
      return <DataTable component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "Timeline":
      return <Timeline component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "ImageGrid":
      return <ImageGrid component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "IconRow":
      return <IconRow component={component} isSelected={isSelected} onSelect={onSelect} />;
    case "Chart":
      return <Chart component={component} isSelected={isSelected} onSelect={onSelect} />;
    default:
      return (
        <div
          data-component="Unknown"
          data-component-id={component.id}
          data-component-type={component.type}
          style={{
            padding: "var(--doc-spacing-md)",
            border: "1px dashed var(--doc-border)",
            borderRadius: "var(--doc-radius-md)",
            color: "var(--doc-text-muted)",
            fontFamily: "var(--doc-font-family)",
            fontSize: "var(--doc-font-size-sm)",
          }}
        >
          unknown {component.type}
        </div>
      );
  }
}

// ─── Partial 적용 유틸 ────────────────────────────────────────────────────

function applyPagePatch(page: Page, patch: Partial<Page>): Page {
  return { ...page, ...patch };
}

function applyComponentPatch(component: Component, patch: Partial<Component>): Component {
  // discriminated union 이므로 `type` 은 변경 불가 — 안전하게 같은 type 유지.
  return { ...component, ...patch, type: component.type } as Component;
}

// ─── 선택 상태 ────────────────────────────────────────────────────────────

interface Selection {
  pageId: string;
  componentId: string;
}

// ─── Host 컴포넌트 Props ─────────────────────────────────────────────────

export interface PreviewHostProps {
  /** 초기 DocumentSchema. 부모가 iframe 마운트 직후 postMessage(schema-patch-local) 로
   *  교체할 수도 있지만, 본 D3 범위에서는 초기 schema 를 props 로 받도록 한다. */
  initialSchema: DocumentSchema;
  /**
   * 허용할 parent origin. default 는 `window.location.origin`(same-origin 라우트).
   * 테스트 목적으로만 `"*"` 허용.
   */
  expectedParentOrigin?: string;
}

/** iframe 내부에서 렌더되는 호스트. */
export function PreviewHost({ initialSchema, expectedParentOrigin }: PreviewHostProps) {
  const [schema, setSchema] = useState<DocumentSchema>(initialSchema);
  const [selection, setSelection] = useState<Selection | null>(null);

  // origin 검증 기준. useRef 로 고정해 리스너 재바인딩 억제.
  const expectedOriginRef = useRef<string>(
    expectedParentOrigin ?? (typeof window !== "undefined" ? window.location.origin : "*"),
  );

  // ── CSS 변수 주입 (최초 + tokens 변경 시) ──────────────────────────────
  useEffect(() => {
    applyTokensToDocument(schema.design_tokens);
  }, [schema.design_tokens]);

  // ── 메시지 수신 ────────────────────────────────────────────────────────
  const applyMessage = useCallback((message: PreviewMessage) => {
    switch (message.type) {
      case "docutil/token-update": {
        setSchema((prev) => ({
          ...prev,
          design_tokens: mergeTokens(prev.design_tokens, message.payload.tokens),
        }));
        return;
      }
      case "docutil/schema-patch-local": {
        setSchema((prev) => applySchemaPatch(prev, message.payload));
        return;
      }
      case "docutil/element-select": {
        // 호스트는 element-select 를 수신하지 않지만(송신 전용), 방어적으로 처리.
        return;
      }
      default: {
        // exhaustive check
        const _exhaustive: never = message;
        return _exhaustive;
      }
    }
  }, []);

  const handleMessage = useCallback(
    (event: MessageEvent<unknown>) => {
      const { ok, reason } = verifyOrigin(event.origin, expectedOriginRef.current);
      if (!ok) {
        // origin 불일치 시 silent drop. console.warn 으로 개발자 가시성 확보.
        console.warn(`[preview-host] 메시지 무시 — ${reason}`);
        return;
      }
      const message = decode(event.data);
      if (!message) {
        // 형태 어긋난 메시지 silent drop (malformed / 다른 앱의 메시지).
        return;
      }
      applyMessage(message);
    },
    [applyMessage],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [handleMessage]);

  // ── 컴포넌트 선택 → parent 통지 ────────────────────────────────────────
  const handleSelectFactory = useCallback(
    (pageId: string) => (componentId: string) => {
      setSelection({ pageId, componentId });
      if (typeof window === "undefined" || !window.parent) return;
      const message = buildElementSelectMessage({ pageId, componentId });
      // targetOrigin 은 반드시 부모의 origin 으로 지정 (보안).
      window.parent.postMessage(message, expectedOriginRef.current);
    },
    [],
  );

  // ── 렌더 ───────────────────────────────────────────────────────────────
  const pages = useMemo(() => schema.pages, [schema.pages]);

  return (
    <main
      data-preview-host
      aria-label="문서 프리뷰 호스트"
      style={{
        width: "100%",
        minHeight: "100vh",
        background: "var(--doc-background)",
        color: "var(--doc-text)",
        fontFamily: "var(--doc-font-family)",
      }}
    >
      {pages.map((page) => (
        <section
          key={page.id}
          data-page-id={page.id}
          data-page-kind={page.page_kind}
          data-page-layout={page.layout}
          aria-label={page.title ?? `페이지 ${page.id}`}
          style={{
            padding: "var(--doc-page-padding)",
            borderBottom: "1px solid var(--doc-border)",
          }}
        >
          {page.components.map((component) => (
            <RenderComponent
              key={component.id}
              component={component}
              isSelected={selection?.pageId === page.id && selection?.componentId === component.id}
              onSelect={handleSelectFactory(page.id)}
            />
          ))}
        </section>
      ))}
    </main>
  );
}

// ─── schema patch 적용 (분리해 테스트 가능하게) ──────────────────────────

/**
 * SchemaPatchPayload 를 기존 DocumentSchema 에 부분 적용해 새 스냅샷을 반환.
 * 순수 함수이므로 __tests__ 에서 직접 호출 가능.
 */
export function applySchemaPatch(
  schema: DocumentSchema,
  payload: import("./postmessage-protocol").SchemaPatchPayload,
): DocumentSchema {
  switch (payload.patchType) {
    case "tokens": {
      return { ...schema, design_tokens: payload.data };
    }
    case "page": {
      const { pageId, data } = payload;
      const pages = schema.pages.map((p) => (p.id === pageId ? applyPagePatch(p, data) : p));
      return { ...schema, pages };
    }
    case "component": {
      const { pageId, componentId, data } = payload;
      const pages = schema.pages.map((page) => {
        if (page.id !== pageId) return page;
        const components = page.components.map((c) =>
          c.id === componentId ? applyComponentPatch(c, data as Partial<Component>) : c,
        );
        return { ...page, components };
      });
      return { ...schema, pages };
    }
    default: {
      const _exhaustive: never = payload;
      return _exhaustive;
    }
  }
}

export default PreviewHost;
