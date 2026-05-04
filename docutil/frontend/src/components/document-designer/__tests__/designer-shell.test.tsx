/**
 * designer-shell.test.tsx — Phase 4 S1 D8 DesignerShell 통합 테스트
 *
 * 검증 항목 (작업지시서 최소 3건):
 *   1. Document 생성 시 documentId state 세팅 → PreviewPane 에 schema 주입
 *   2. element-select 메시지 → setSelected → edit-sidebar 노출
 *   3. selected 가 null 이면 edit-sidebar 자리에 안내 메시지
 *   4. DesignTokenPicker 존재 확인
 *   5. error state 렌더
 */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useDocumentStore } from "@/lib/document-schema/document-store";
import type { DocumentSchema } from "@/types/document-schema";

import { DesignerShell } from "../designer-shell";

// ─── apiClient mock ───────────────────────────────────────────────────────

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPatch = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: vi.fn(),
  },
}));

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

beforeEach(() => {
  mockGet.mockReset();
  mockGet.mockResolvedValue({ items: [] }); // prompt-box 내부 list API 대응
  mockPost.mockReset();
  mockPatch.mockReset();
  useDocumentStore.getState().reset();
});

// ─── 1) 3분할 레이아웃 렌더 ──────────────────────────────────────────────

describe("DesignerShell — 레이아웃", () => {
  it("좌/중/우 3분할 패널이 모두 렌더된다", () => {
    render(<DesignerShell />);

    expect(screen.getByTestId("designer-shell-left")).toBeInTheDocument();
    expect(screen.getByTestId("designer-shell-center")).toBeInTheDocument();
    expect(screen.getByTestId("designer-shell-right")).toBeInTheDocument();

    // 내부 주요 구성 요소 (prompt-box / preview-pane / design-token-picker)
    expect(screen.getByTestId("prompt-box")).toBeInTheDocument();
    expect(screen.getByTestId("preview-pane")).toBeInTheDocument();
    expect(screen.getByTestId("design-token-picker")).toBeInTheDocument();
  });

  it("문서가 없으면 편집 사이드바는 empty 안내를 보여준다", () => {
    render(<DesignerShell />);
    expect(screen.getByTestId("edit-sidebar-empty")).toBeInTheDocument();
    expect(screen.queryByTestId("edit-sidebar")).not.toBeInTheDocument();
  });
});

// ─── 2) Document 생성 → documentId state ─────────────────────────────────

describe("DesignerShell — 문서 생성 → store 반영", () => {
  it("prompt-box 로 생성 요청 성공 시 useDocumentStore.document 가 갱신된다", async () => {
    const schema = buildDocumentSchema();
    mockPost.mockResolvedValue(schema);

    render(<DesignerShell />);

    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "테스트 문서" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    await waitFor(() => expect(mockPost).toHaveBeenCalledTimes(1));
    await waitFor(() => {
      expect(useDocumentStore.getState().document?.document_id).toBe(DOC_ID);
    });
  });
});

// ─── 3) initialDocumentId 주입 → GET 호출 ────────────────────────────────

describe("DesignerShell — initialDocumentId 로드", () => {
  it("initialDocumentId 주입 시 useDocument 가 GET 을 호출한다", async () => {
    const schema = buildDocumentSchema();
    mockGet.mockImplementation((url: string) => {
      if (url === `/v2/documents/${DOC_ID}`) return Promise.resolve(schema);
      return Promise.resolve({ items: [] });
    });

    render(<DesignerShell initialDocumentId={DOC_ID} />);

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(`/v2/documents/${DOC_ID}`);
    });

    await waitFor(() => {
      expect(useDocumentStore.getState().document?.document_id).toBe(DOC_ID);
    });
  });
});

// ─── 4) element-select → edit-sidebar 활성화 ─────────────────────────────

describe("DesignerShell — element-select 이벤트", () => {
  it("store 에 selected 를 세팅하면 EditSidebar 가 노출된다", async () => {
    const schema = buildDocumentSchema();
    mockPost.mockResolvedValue(schema);

    render(<DesignerShell />);

    // 문서 생성
    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "문서 생성" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    await waitFor(() => {
      expect(useDocumentStore.getState().document).not.toBeNull();
    });

    // element-select 이벤트 시뮬레이션 (iframe 이 아닌 직접 store mutation 경로)
    act(() => {
      useDocumentStore.getState().setSelected({ pageId: "p1", componentId: "c1" });
    });

    // edit-sidebar 가 나타나고, SlideTitleForm (data-form="SlideTitle") 가 마운트된다.
    await waitFor(() => {
      expect(screen.getByTestId("edit-sidebar")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("edit-sidebar-empty")).not.toBeInTheDocument();
    expect(screen.getByText("제목")).toBeInTheDocument();
  });

  it("selected 가 해제되면 edit-sidebar 가 empty 안내로 돌아간다", async () => {
    const schema = buildDocumentSchema();
    mockPost.mockResolvedValue(schema);
    render(<DesignerShell />);

    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "문서" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    await waitFor(() => {
      expect(useDocumentStore.getState().document).not.toBeNull();
    });

    act(() => {
      useDocumentStore.getState().setSelected({ pageId: "p1", componentId: "c1" });
    });
    await waitFor(() => expect(screen.getByTestId("edit-sidebar")).toBeInTheDocument());

    act(() => {
      useDocumentStore.getState().setSelected(null);
    });
    await waitFor(() => expect(screen.getByTestId("edit-sidebar-empty")).toBeInTheDocument());
  });
});

// ─── 5) 에러 state ───────────────────────────────────────────────────────

describe("DesignerShell — 에러 UI", () => {
  it("useDocument 가 에러를 반환하면 role=alert 가 노출된다", async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === `/v2/documents/${DOC_ID}`) {
        return Promise.reject(new Error("서버 연결 실패"));
      }
      return Promise.resolve({ items: [] });
    });

    render(<DesignerShell initialDocumentId={DOC_ID} />);

    await waitFor(() => {
      expect(screen.getByTestId("designer-shell-error")).toBeInTheDocument();
    });
    expect(screen.getByTestId("designer-shell-error")).toHaveTextContent(/서버 연결 실패/);
  });
});
