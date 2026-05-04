/**
 * use-patch-document.test.tsx — Phase 4 S1 D8 usePatchDocument 단위 테스트
 *
 * 검증 항목 (작업지시서 최소 5건):
 *   1. patchPage → apiClient.patch 호출 + 올바른 body
 *   2. patchComponent → component_id 포함 body
 *   3. patchTokens → patch_type=tokens body
 *   4. 에러 응답 → throw + error state
 *   5. documentId null → 즉시 throw (호출 차단)
 *   6. 성공 응답 → document-store 가 서버 응답으로 교체
 *   7. 동시 실행 시 isPatching 플래그
 */

import { act, render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DesignTokens, DocumentSchema, Page } from "@/types/document-schema";

// ─── apiClient mock ───────────────────────────────────────────────────────

const mockPatch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
}));

import { useDocumentStore } from "../document-store";
import { usePatchDocument } from "../use-patch-document";

// ─── fixture ──────────────────────────────────────────────────────────────

const DOC_ID = "00000000-0000-4000-8000-000000000001";

function buildDocumentSchema(): DocumentSchema {
  return {
    document_id: DOC_ID,
    schema_version: "1.0",
    type: "slide_report",
    mode: "free_generation",
    template_id: null,
    design_tokens: {
      primary_color: "#0A4FC2",
      accent_color: "#FF6B35",
      text_color: "#1F2937",
      background_color: "#FFFFFF",
      font_family: "Pretendard",
      spacing: "normal",
      brand_preset: "idino_default",
    },
    pages: [
      {
        id: "p1",
        page_kind: "slide",
        layout: "title_slide",
        title: "첫 페이지",
        locked: false,
        speaker_notes: null,
        page_number_visible: true,
        components: [{ id: "c1", type: "SlideTitle", locked: false, anchor: null, text: "제목" }],
      },
    ],
    metadata: {
      created_at: "2026-04-19T00:00:00Z",
      updated_at: "2026-04-19T00:00:00Z",
      generated_by_user_id: null,
      llm_provider: "openai",
      llm_model: "gpt-4o",
      prompt_tokens: 100,
      completion_tokens: 200,
      source_document_ids: [],
      source_chat_session_id: null,
      citations: [],
      degraded_components: [],
    },
  };
}

// ─── renderHook helper ────────────────────────────────────────────────────

function renderUseHook<T>(hook: () => T): {
  result: { current: T };
} {
  const result = { current: undefined as unknown as T };
  function Harness() {
    result.current = hook();
    return null;
  }
  render(<Harness />);
  return { result };
}

beforeEach(() => {
  mockPatch.mockReset();
  useDocumentStore.getState().reset();
});

// ─── 1) patchPage ────────────────────────────────────────────────────────

describe("usePatchDocument — patchPage", () => {
  it("patch_type=page 로 apiClient.patch 를 호출한다", async () => {
    const schema = buildDocumentSchema();
    mockPatch.mockResolvedValue(schema);

    const { result } = renderUseHook(() => usePatchDocument(DOC_ID));

    const pagePatch: Partial<Page> = { title: "수정된 제목" };
    await act(async () => {
      await result.current.patchPage("p1", pagePatch);
    });

    expect(mockPatch).toHaveBeenCalledTimes(1);
    expect(mockPatch).toHaveBeenCalledWith(`/v2/documents/${DOC_ID}`, {
      patch_type: "page",
      page_id: "p1",
      data: pagePatch,
    });
  });
});

// ─── 2) patchComponent ───────────────────────────────────────────────────

describe("usePatchDocument — patchComponent", () => {
  it("patch_type=component 로 component_id 를 포함해 호출한다", async () => {
    const schema = buildDocumentSchema();
    mockPatch.mockResolvedValue(schema);

    const { result } = renderUseHook(() => usePatchDocument(DOC_ID));

    await act(async () => {
      await result.current.patchComponent("p1", "c1", { text: "새 제목" });
    });

    expect(mockPatch).toHaveBeenCalledWith(`/v2/documents/${DOC_ID}`, {
      patch_type: "component",
      page_id: "p1",
      component_id: "c1",
      data: { text: "새 제목" },
    });
  });
});

// ─── 3) patchTokens ──────────────────────────────────────────────────────

describe("usePatchDocument — patchTokens", () => {
  it("patch_type=tokens 로 디자인 토큰 전체 교체를 보낸다", async () => {
    const schema = buildDocumentSchema();
    mockPatch.mockResolvedValue(schema);

    const tokens: DesignTokens = {
      ...schema.design_tokens,
      brand_preset: "idino_mono",
      primary_color: "#2B2B2B",
    };

    const { result } = renderUseHook(() => usePatchDocument(DOC_ID));

    await act(async () => {
      await result.current.patchTokens(tokens);
    });

    expect(mockPatch).toHaveBeenCalledWith(`/v2/documents/${DOC_ID}`, {
      patch_type: "tokens",
      data: tokens,
    });
  });
});

// ─── 4) 에러 처리 ────────────────────────────────────────────────────────

describe("usePatchDocument — 에러 처리", () => {
  it("서버가 에러를 던지면 error state 가 세팅되고 호출자에게 throw 된다", async () => {
    mockPatch.mockRejectedValue(new Error("409 conflict"));

    const { result } = renderUseHook(() => usePatchDocument(DOC_ID));

    await act(async () => {
      await expect(result.current.patchComponent("p1", "c1", { text: "x" })).rejects.toThrow(
        "409 conflict",
      );
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("409 conflict");
    expect(result.current.isPatching).toBe(false);
  });
});

// ─── 5) documentId null ──────────────────────────────────────────────────

describe("usePatchDocument — documentId null", () => {
  it("documentId 가 null 이면 즉시 throw 되고 API 를 호출하지 않는다", async () => {
    const { result } = renderUseHook(() => usePatchDocument(null));

    await act(async () => {
      await expect(result.current.patchPage("p1", {})).rejects.toThrow(/문서가 선택되지 않아/);
    });

    expect(mockPatch).not.toHaveBeenCalled();
  });
});

// ─── 6) store 갱신 ───────────────────────────────────────────────────────

describe("usePatchDocument — store 반영", () => {
  it("성공 응답의 DocumentSchema 로 useDocumentStore.document 를 갱신한다", async () => {
    const updated = buildDocumentSchema();
    updated.pages[0].title = "patch 후 제목";
    mockPatch.mockResolvedValue(updated);

    const { result } = renderUseHook(() => usePatchDocument(DOC_ID));

    await act(async () => {
      await result.current.patchPage("p1", { title: "patch 후 제목" });
    });

    await waitFor(() => {
      expect(useDocumentStore.getState().document?.pages[0].title).toBe("patch 후 제목");
    });
  });
});

// ─── 7) isPatching 플래그 ────────────────────────────────────────────────

describe("usePatchDocument — 동시성", () => {
  it("요청 중에는 isPatching=true 이고 완료 후 false 로 돌아온다", async () => {
    let resolveFn: (value: DocumentSchema) => void = () => {};
    mockPatch.mockImplementation(
      () =>
        new Promise<DocumentSchema>((resolve) => {
          resolveFn = resolve;
        }),
    );

    const { result } = renderUseHook(() => usePatchDocument(DOC_ID));

    let pending: Promise<DocumentSchema> | undefined;
    act(() => {
      pending = result.current.patchTokens({
        primary_color: "#000000",
        accent_color: "#FFFFFF",
        text_color: "#333333",
        background_color: "#FFFFFF",
        font_family: "Pretendard",
        spacing: "normal",
        brand_preset: "custom",
      });
    });

    await waitFor(() => expect(result.current.isPatching).toBe(true));

    await act(async () => {
      resolveFn(buildDocumentSchema());
      await pending;
    });

    await waitFor(() => expect(result.current.isPatching).toBe(false));
  });
});
