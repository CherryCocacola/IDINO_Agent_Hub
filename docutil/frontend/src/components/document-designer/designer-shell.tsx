/**
 * DesignerShell — 3분할 편집기 셸 (좌 30% · 중앙 55% · 우 15%)
 *
 * Phase 4 S1 D8 산출물. S1 D1~D7 에서 완성된 6종 컴포넌트 · preview-pane ·
 * edit-sidebar (forms) · prompt-box · design-token-picker 를
 * `useDocument` / `usePatchDocument` 데이터 계층으로 연결한다.
 *
 * 레이아웃:
 *   ┌────────────┬──────────────────────────────┬────────┐
 *   │ prompt-box │                              │        │
 *   │    +       │        preview-pane          │ token  │
 *   │ edit-side  │   (iframe live preview)      │ picker │
 *   │   bar      │                              │        │
 *   └────────────┴──────────────────────────────┴────────┘
 *
 * 데이터 흐름 (phase1_decisions.md v1.2 Q10):
 *   1. prompt-box.useDocumentMutation → POST /v2/documents → state.documentId
 *   2. useDocument(documentId) → 서버 조회 → useDocumentStore
 *   3. PreviewPane element-select → setSelected (zustand) → edit-sidebar 렌더
 *   4. 편집 폼 onLocalPatch → previewPaneRef.sendSchemaPatch (iframe)
 *      편집 폼 onCommitPatch → usePatchDocument.patchComponent (server)
 *   5. DesignTokenPicker onPreview → previewPaneRef.sendTokenUpdate
 *      DesignTokenPicker onCommit → usePatchDocument.patchTokens
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - preview-pane / edit-sidebar-forms / design-token-picker / prompt-box 디렉터리
 *     **수정 금지** — 모든 wiring 은 본 파일에서 수행.
 *   - `fetch()` 직접 호출 금지 — apiClient 경유.
 *   - hex 하드코딩 금지 — DEFAULT_DESIGN_TOKENS 를 사용.
 */

"use client";

import { useCallback, useMemo, useRef } from "react";

import {
  findComponent,
  useDocumentStore,
  type SelectedElement,
} from "@/lib/document-schema/document-store";
import { useDocument } from "@/lib/document-schema/use-document";
import { usePatchDocument } from "@/lib/document-schema/use-patch-document";
import type { Component, DesignTokens, DocumentSchema, Page } from "@/types/document-schema";

import { DesignTokenPicker } from "./design-token-picker";
import { DEFAULT_DESIGN_TOKENS } from "./design-token-picker/tokens";
import { resolveFormFor, useFormPatch } from "./edit-sidebar/forms";
import { ExportMenu } from "./export-menu";
import { PreviewPane, type PreviewPaneHandle } from "./preview-pane";
import type { ElementSelectPayload } from "./preview-pane/postmessage-protocol";
import { PromptBox } from "./prompt-box";

// ─── Props ────────────────────────────────────────────────────────────────

export interface DesignerShellProps {
  /**
   * 이미 로드된 문서의 ID. 라우트 params 에서 주입하는 경로.
   * 미지정(null) 시 사용자가 prompt-box 로 새 문서를 생성하면 state 에 저장된다.
   */
  initialDocumentId?: string | null;
  className?: string;
  dataTestId?: string;
}

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────

export function DesignerShell({
  initialDocumentId = null,
  className,
  dataTestId,
}: DesignerShellProps) {
  // 현재 편집 중 문서 ID. prompt-box 가 새 문서를 만들면 여기서 바뀐다.
  const documentId = useDocumentStore((s) => s.document?.document_id ?? null);
  const selected = useDocumentStore((s) => s.selected);
  const setSelected = useDocumentStore((s) => s.setSelected);
  const setDocument = useDocumentStore((s) => s.setDocument);

  // 초기 문서 ID 로드 (라우트 진입 시 한 번).
  // useDocument 가 내부적으로 store.setDocument 를 호출.
  const effectiveId = documentId ?? initialDocumentId ?? null;
  const { document: loadedDocument, isLoading, error } = useDocument(effectiveId);

  // PATCH 훅 — 편집 폼 · 토큰 피커의 commit 파이프.
  const { patchComponent, patchTokens } = usePatchDocument(effectiveId);

  // preview iframe 컨트롤 ref.
  const previewPaneRef = useRef<PreviewPaneHandle | null>(null);

  // ── 1) 문서 생성 핸들러 (prompt-box → state) ───────────────────────────
  const handleDocumentGenerated = useCallback(
    (result: DocumentSchema) => {
      setDocument(result);
    },
    [setDocument],
  );

  // ── 2) element-select 핸들러 (preview iframe → sidebar 활성화) ─────────
  const handleElementSelect = useCallback(
    (payload: ElementSelectPayload) => {
      const selection: SelectedElement = {
        pageId: payload.pageId,
        componentId: payload.componentId,
      };
      setSelected(selection);
    },
    [setSelected],
  );

  // ── 3) 편집 폼 patch 파이프 ────────────────────────────────────────────
  // 즉시 iframe 프리뷰 반영 (낙관적). pageId/componentId 는 클로저로 고정되지
  // 않게 하기 위해 currentSelection 을 읽어서 사용.
  const handleLocalPatch = useCallback(
    (patch: Partial<Component>) => {
      if (!selected) return;
      previewPaneRef.current?.sendSchemaPatch({
        patchType: "component",
        pageId: selected.pageId,
        componentId: selected.componentId,
        data: patch,
      });
    },
    [selected],
  );

  // 서버 PATCH — useFormPatch 의 onPatch 콜백을 통해 500ms debounce 된 상태로
  // 호출된다. 본 핸들러 자체는 비동기라 fire-and-forget.
  const handleCommitPatchRaw = useCallback(
    ({ pageId, componentId, patch }: { pageId: string; componentId: string; patch: unknown }) => {
      void patchComponent(pageId, componentId, patch as Partial<Component>).catch((err) => {
        // 운영 환경에서는 toast 연결 예정. 현재는 디버깅 로그.
        console.error("[DesignerShell] patchComponent 실패", err);
      });
    },
    [patchComponent],
  );

  // sidebar 컨테이너용 debounce 훅.
  // selected 가 바뀔 때마다 훅 인스턴스를 새로 만들기 위해 key 를 부여한다 —
  // 아래 <EditSidebarPanel /> 내부에서 hook 을 호출한다.
  const selectedComponent = useMemo(
    () => findComponent(loadedDocument, selected),
    [loadedDocument, selected],
  );

  // ── 4) 토큰 파이프 ─────────────────────────────────────────────────────
  const handleTokenPreview = useCallback((patch: Partial<DesignTokens>) => {
    previewPaneRef.current?.sendTokenUpdate(patch);
  }, []);

  const handleTokenCommit = useCallback(
    (patch: Partial<DesignTokens>) => {
      // 토큰은 전체 치환이 서버 정책 — 현재 토큰과 병합해 전송.
      const current = useDocumentStore.getState().document?.design_tokens ?? DEFAULT_DESIGN_TOKENS;
      const merged: DesignTokens = { ...current, ...patch } as DesignTokens;
      void patchTokens(merged).catch((err) => {
        // 운영 환경에서는 toast 연결 예정. 현재는 디버깅 로그.
        console.error("[DesignerShell] patchTokens 실패", err);
      });
    },
    [patchTokens],
  );

  const currentTokens = loadedDocument?.design_tokens ?? DEFAULT_DESIGN_TOKENS;
  const disableTokens = !loadedDocument;

  return (
    <div
      data-testid={dataTestId ?? "designer-shell"}
      data-designer-shell
      className={className}
      style={{
        display: "grid",
        gridTemplateColumns: "30% 55% 15%",
        height: "100vh",
        width: "100%",
        minWidth: 0,
        background: "var(--doc-surface)",
      }}
    >
      {/* 좌측 30% — 프롬프트 + 편집 사이드바 */}
      <aside
        data-testid="designer-shell-left"
        aria-label="문서 생성 및 편집 패널"
        style={{
          borderRight: "1px solid var(--doc-border)",
          overflowY: "auto",
          minWidth: 0,
        }}
      >
        <PromptBox onDocumentGenerated={handleDocumentGenerated} previewPaneRef={previewPaneRef} />

        {selected && selectedComponent ? (
          <EditSidebarPanel
            selected={selected}
            component={selectedComponent}
            onLocalPatch={handleLocalPatch}
            onCommitPatchRaw={handleCommitPatchRaw}
          />
        ) : (
          <section
            data-testid="edit-sidebar-empty"
            aria-label="편집 대상 미선택 안내"
            style={{
              padding: "var(--doc-spacing-md)",
              color: "var(--doc-text-muted)",
              fontSize: "var(--doc-font-size-sm)",
            }}
          >
            프리뷰에서 편집할 요소를 클릭하세요.
          </section>
        )}
      </aside>

      {/* 중앙 55% — 프리뷰 */}
      <main
        data-testid="designer-shell-center"
        aria-label="문서 프리뷰"
        aria-busy={isLoading ? "true" : "false"}
        style={{ minWidth: 0, position: "relative" }}
      >
        {error ? (
          <div
            role="alert"
            data-testid="designer-shell-error"
            style={{
              padding: "var(--doc-spacing-md)",
              color: "var(--doc-accent)",
            }}
          >
            문서 로드 실패: {error.message}
          </div>
        ) : null}
        <PreviewPane
          ref={previewPaneRef}
          schema={loadedDocument}
          onElementSelect={handleElementSelect}
        />
      </main>

      {/* 우측 15% — Export 메뉴 + 토큰 피커 */}
      <aside
        data-testid="designer-shell-right"
        aria-label="내보내기 및 디자인 토큰 조정"
        style={{
          borderLeft: "1px solid var(--doc-border)",
          overflowY: "auto",
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <ExportMenu documentId={effectiveId} />
        <DesignTokenPicker
          tokens={currentTokens}
          onPreview={handleTokenPreview}
          onCommit={handleTokenCommit}
          disabled={disableTokens}
        />
      </aside>
    </div>
  );
}

// ─── 내부: 편집 사이드바 패널 (useFormPatch wiring) ───────────────────────
// useFormPatch 는 componentId/pageId 를 인자로 받으므로 selected 가 바뀔 때마다
// 훅 인스턴스가 리셋될 수 있도록 별도 컴포넌트로 분리한다.

interface EditSidebarPanelProps {
  selected: SelectedElement;
  component: Component;
  onLocalPatch: (patch: Partial<Component>) => void;
  onCommitPatchRaw: (args: { pageId: string; componentId: string; patch: unknown }) => void;
}

function EditSidebarPanel({
  selected,
  component,
  onLocalPatch,
  onCommitPatchRaw,
}: EditSidebarPanelProps) {
  // 500ms debounce 된 서버 PATCH.
  const formPatch = useFormPatch<Component>(selected.componentId, selected.pageId, {
    onPatch: onCommitPatchRaw,
  });

  const handleCommitPatch = useCallback(
    (patch: Partial<Component>) => {
      formPatch.commit(patch);
    },
    [formPatch],
  );

  return (
    <section
      data-testid="edit-sidebar"
      aria-label="컴포넌트 편집"
      style={{
        padding: "var(--doc-spacing-md)",
        borderTop: "1px solid var(--doc-border)",
      }}
    >
      {resolveFormFor({
        component,
        pageId: selected.pageId,
        onLocalPatch,
        onCommitPatch: handleCommitPatch,
      })}
    </section>
  );
}

// 타입 재수출 (테스트 편의).
export type { SelectedElement, Page };
