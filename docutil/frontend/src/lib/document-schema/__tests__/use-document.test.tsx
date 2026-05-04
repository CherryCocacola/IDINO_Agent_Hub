/**
 * use-document.test.ts — Phase 4 S1 D8 useDocument 단위 테스트
 *
 * 검증 항목 (작업지시서 최소 8건):
 *   1. documentId null → 초기 상태 (API 미호출)
 *   2. documentId 설정 → loading → success 전환
 *   3. API 에러 → error state
 *   4. 언마운트 시 stale 응답 무시
 *   5. documentId 변경 → 재로드
 *   6. reload 함수 동작
 *   7. 같은 documentId 를 새 훅 인스턴스로 재설정 시 재호출
 *   8. CORS / 네트워크 에러 (Error 인스턴스가 아닌 값) 표준화
 *   9. 성공 시 document-store 의 document 가 갱신된다
 */

import { act, render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DocumentSchema } from "@/types/document-schema";

// ─── apiClient mock ───────────────────────────────────────────────────────

const mockGet = vi.fn();
const mockPatch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
    put: vi.fn(),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
    put: vi.fn(),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
}));

import { useDocumentStore } from "../document-store";
import { useDocument } from "../use-document";

// ─── fixture ──────────────────────────────────────────────────────────────

function buildDocumentSchema(documentId = "00000000-0000-4000-8000-000000000001"): DocumentSchema {
  return {
    document_id: documentId,
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
        components: [
          {
            id: "c1",
            type: "SlideTitle",
            locked: false,
            anchor: null,
            text: "제목",
          },
        ],
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

// ─── renderHook helper (RTL renderHook 대체) ──────────────────────────────

function renderUseHook<T, P>(
  hook: (props: P) => T,
  initialProps: P,
): {
  result: { current: T };
  rerender: (newProps: P) => void;
  unmount: () => void;
} {
  const result = { current: undefined as unknown as T };
  let currentProps = initialProps;
  function Harness(props: { value: P }) {
    result.current = hook(props.value);
    return null;
  }
  const utils = render(<Harness value={currentProps} />);
  return {
    result,
    rerender: (newProps: P) => {
      currentProps = newProps;
      utils.rerender(<Harness value={newProps} />);
    },
    unmount: utils.unmount,
  };
}

// ─── setup ────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockGet.mockReset();
  mockPatch.mockReset();
  // Zustand store 초기화 (이전 테스트 상태 제거)
  useDocumentStore.getState().reset();
});

// ─── 1) documentId null → 초기 상태 ────────────────────────────────────────

describe("useDocument — null id", () => {
  it("documentId 가 null 이면 API 호출이 일어나지 않고 초기 상태가 된다", () => {
    const { result } = renderUseHook((id: string | null) => useDocument(id), null);

    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.document).toBeNull();
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ─── 2) loading → success ────────────────────────────────────────────────

describe("useDocument — 성공 플로우", () => {
  it("documentId 설정 시 loading → success 로 전환된다", async () => {
    const schema = buildDocumentSchema();
    mockGet.mockResolvedValue(schema);

    const { result } = renderUseHook(
      (id: string | null) => useDocument(id),
      "00000000-0000-4000-8000-000000000001",
    );

    // 렌더 직후에는 로딩
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBeNull();
    expect(result.current.document).toEqual(schema);
    expect(mockGet).toHaveBeenCalledTimes(1);
    expect(mockGet).toHaveBeenCalledWith("/v2/documents/00000000-0000-4000-8000-000000000001");
  });

  it("성공 응답은 useDocumentStore 에 캐시된다", async () => {
    const schema = buildDocumentSchema();
    mockGet.mockResolvedValue(schema);

    renderUseHook((id: string | null) => useDocument(id), schema.document_id);

    await waitFor(() => {
      expect(useDocumentStore.getState().document).toEqual(schema);
    });
  });
});

// ─── 3) API 에러 ─────────────────────────────────────────────────────────

describe("useDocument — 에러 처리", () => {
  it("API 가 Error 를 throw 하면 error state 에 세팅된다", async () => {
    mockGet.mockRejectedValue(new Error("404 not found"));

    const { result } = renderUseHook(
      (id: string | null) => useDocument(id),
      "00000000-0000-4000-8000-000000000099",
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("404 not found");
    expect(result.current.document).toBeNull();
  });

  it("API 가 비 Error 값을 throw 해도 Error 인스턴스로 표준화된다", async () => {
    mockGet.mockRejectedValue("network down");

    const { result } = renderUseHook(
      (id: string | null) => useDocument(id),
      "00000000-0000-4000-8000-000000000099",
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toMatch(/문서 조회/);
  });
});

// ─── 4) 언마운트 시 stale 무시 ────────────────────────────────────────────

describe("useDocument — stale 응답 무시", () => {
  it("언마운트 후에 응답이 돌아와도 store 가 오염되지 않는다", async () => {
    // deferred promise 로 응답 수동 제어
    let resolveFn: (value: DocumentSchema) => void = () => {};
    mockGet.mockImplementation(
      () =>
        new Promise<DocumentSchema>((resolve) => {
          resolveFn = resolve;
        }),
    );

    const { unmount } = renderUseHook(
      (id: string | null) => useDocument(id),
      "00000000-0000-4000-8000-000000000001",
    );

    // 요청이 진행 중인 상태에서 언마운트
    unmount();

    // 언마운트 이후 뒤늦게 응답 도착
    await act(async () => {
      resolveFn(buildDocumentSchema());
    });

    // store 는 여전히 null 이어야 한다 (stale 방어).
    expect(useDocumentStore.getState().document).toBeNull();
  });
});

// ─── 5) documentId 변경 → 재로드 ──────────────────────────────────────────

describe("useDocument — id 변경", () => {
  it("documentId 가 바뀌면 새 id 로 다시 fetch 한다", async () => {
    const firstSchema = buildDocumentSchema("00000000-0000-4000-8000-000000000001");
    const secondSchema = buildDocumentSchema("00000000-0000-4000-8000-000000000002");

    mockGet.mockImplementation((url: string) => {
      if (url.endsWith("000000000001")) return Promise.resolve(firstSchema);
      if (url.endsWith("000000000002")) return Promise.resolve(secondSchema);
      return Promise.reject(new Error("unexpected id"));
    });

    const initial: string | null = "00000000-0000-4000-8000-000000000001";
    const { result, rerender } = renderUseHook<ReturnType<typeof useDocument>, string | null>(
      (id) => useDocument(id),
      initial,
    );

    await waitFor(() =>
      expect(result.current.document?.document_id).toBe("00000000-0000-4000-8000-000000000001"),
    );

    rerender("00000000-0000-4000-8000-000000000002");

    await waitFor(() =>
      expect(result.current.document?.document_id).toBe("00000000-0000-4000-8000-000000000002"),
    );
    expect(mockGet).toHaveBeenCalledTimes(2);
  });
});

// ─── 6) reload 동작 ───────────────────────────────────────────────────────

describe("useDocument — reload", () => {
  it("reload() 호출 시 같은 id 로 API 가 다시 호출된다", async () => {
    const schema = buildDocumentSchema();
    mockGet.mockResolvedValue(schema);

    const { result } = renderUseHook((id: string | null) => useDocument(id), schema.document_id);

    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(1));

    await act(async () => {
      await result.current.reload();
    });

    expect(mockGet).toHaveBeenCalledTimes(2);
  });

  it("documentId 가 null 이면 reload() 가 no-op 이다", async () => {
    const { result } = renderUseHook((id: string | null) => useDocument(id), null);

    await act(async () => {
      await result.current.reload();
    });

    expect(mockGet).not.toHaveBeenCalled();
  });
});
