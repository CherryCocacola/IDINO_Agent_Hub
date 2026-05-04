/**
 * PreviewPane — Designer Shell 중앙 55% 영역에 배치되는 외부 컴포넌트
 *
 * Phase 4 S1 D3 범위:
 *   - `<PreviewFrame>` 을 감싸고 iframe contentWindow 로 postMessage 를 보내는
 *     커맨드 메서드(ref 핸들)를 노출한다.
 *   - iframe 에서 올라오는 `docutil/element-select` 를 수신해 props 콜백으로
 *     부모에게 bubbling 한다.
 *
 * 현재 D3 범위 밖:
 *   - DocumentSchema fetching (D4+ 에서 `useDocument` 훅 연결)
 *   - selected 상태를 실제 edit-sidebar 와 동기화 (D4 편집 사이드바 작업에서 연결)
 *   - Design token picker 슬라이더 연결 (D5)
 */

"use client";

import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef } from "react";

import type { DesignTokens, DocumentSchema } from "@/types/document-schema";

import {
  buildSchemaPatchMessage,
  buildTokenUpdateMessage,
  decode,
  type ElementSelectPayload,
  type SchemaPatchPayload,
  verifyOrigin,
} from "./postmessage-protocol";
import { PreviewFrame, type PreviewFrameHandle } from "./PreviewFrame";

export interface PreviewPaneProps {
  /**
   * 현재 문서 스냅샷. D3 범위에서는 iframe 초기 주입용 schema 로만 쓰인다.
   * iframe 이 로드되면 부모가 이 schema 를 bootstrap 으로 전달해야 하지만,
   * D3 에서는 초기 주입은 `/preview-host` 라우트의 DEFAULT_SCHEMA 로 대체되고
   * 이후 변경분은 sendSchemaPatch 로 전달한다 (D4 에서 통합 정리).
   */
  schema?: DocumentSchema | null;
  /**
   * iframe 소스. 기본값 `/preview-host`. 테스트 / 샌드박스 환경에서 override.
   */
  src?: string;
  /**
   * iframe 의 예상 origin. 기본값은 `window.location.origin` (same-origin 라우트).
   */
  expectedOrigin?: string;
  /** 사용자가 프리뷰 내 컴포넌트를 클릭했을 때 호출. edit-sidebar 활성화 트리거. */
  onElementSelect?: (payload: ElementSelectPayload) => void;
  /** iframe 로드 완료 콜백. */
  onReady?: () => void;
  className?: string;
  dataTestId?: string;
}

export interface PreviewPaneHandle {
  /** 디자인 토큰 부분 변경을 iframe 으로 전파. */
  sendTokenUpdate: (tokens: Partial<DesignTokens>) => void;
  /** Partial DocumentSchema 부분 갱신을 iframe 으로 전파. */
  sendSchemaPatch: (payload: SchemaPatchPayload) => void;
  /** 내부 iframe 엘리먼트 접근자 (디버깅/테스트). */
  getIframe: () => HTMLIFrameElement | null;
}

export const PreviewPane = forwardRef<PreviewPaneHandle, PreviewPaneProps>(function PreviewPane(
  {
    src,
    expectedOrigin,
    onElementSelect,
    onReady,
    className,
    dataTestId,
    // schema 는 D3 에서 아직 bootstrap 경로가 없으므로 수신만 함.
    schema: _schema,
  },
  ref,
) {
  const frameRef = useRef<PreviewFrameHandle | null>(null);

  // 예상 origin — SSR 안전을 위해 useMemo 로 지연 계산.
  const expectedIframeOrigin = useMemo(() => {
    if (expectedOrigin) return expectedOrigin;
    if (typeof window !== "undefined") return window.location.origin;
    return "*";
  }, [expectedOrigin]);

  const postToIframe = useCallback(
    (message: unknown) => {
      const win = frameRef.current?.getContentWindow();
      if (!win) {
        console.warn("[PreviewPane] iframe contentWindow 가 아직 준비되지 않음.");
        return;
      }
      win.postMessage(message, expectedIframeOrigin);
    },
    [expectedIframeOrigin],
  );

  // ── ref 핸들 ───────────────────────────────────────────────────────────
  useImperativeHandle(
    ref,
    () => ({
      sendTokenUpdate: (tokens) => postToIframe(buildTokenUpdateMessage({ tokens })),
      sendSchemaPatch: (payload) => postToIframe(buildSchemaPatchMessage(payload)),
      getIframe: () => frameRef.current?.getIframe() ?? null,
    }),
    [postToIframe],
  );

  // ── iframe → parent 메시지 수신 ────────────────────────────────────────
  useEffect(() => {
    if (typeof window === "undefined") return;
    const listener = (event: MessageEvent<unknown>) => {
      const { ok } = verifyOrigin(event.origin, expectedIframeOrigin);
      if (!ok) return;
      const message = decode(event.data);
      if (!message) return;
      if (message.type === "docutil/element-select") {
        onElementSelect?.(message.payload);
      }
      // token-update / schema-patch-local 은 parent → iframe 방향이므로 수신 시 무시.
    };
    window.addEventListener("message", listener);
    return () => window.removeEventListener("message", listener);
  }, [expectedIframeOrigin, onElementSelect]);

  const handleFrameLoad = useCallback(() => {
    onReady?.();
  }, [onReady]);

  return (
    <div
      data-preview-pane
      data-testid={dataTestId ?? "preview-pane"}
      className={className}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        background: "var(--doc-surface)",
        overflow: "hidden",
      }}
    >
      <PreviewFrame
        ref={frameRef}
        src={src}
        onFrameLoad={handleFrameLoad}
        dataTestId="preview-frame"
      />
    </div>
  );
});

export default PreviewPane;
