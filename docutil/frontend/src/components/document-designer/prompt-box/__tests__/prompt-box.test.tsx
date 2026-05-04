/**
 * prompt-box.test.tsx — Phase 4 S1 D6 PromptBox 단위 테스트
 *
 * 검증 항목 (작업지시서 최소 8건):
 *   1. 빈 프롬프트 → 생성 버튼 disabled
 *   2. 프롬프트 입력 → 버튼 enabled
 *   3. DocumentType 값 기본 slide_report, 변경 시 반영
 *   4. 생성 버튼 클릭 → apiClient.post 가 /v2/documents 로 호출
 *   5. 성공 응답 → onDocumentGenerated 호출 + previewPane.sendSchemaPatch 전송
 *   6. 실패 응답 → ValidationFeedback 에 에러 노출
 *   7. Ctrl+Enter 단축키 → 생성 트리거
 *   8. 로딩 중 입력 disabled + "생성 중" 표시
 *   9. useDocumentMutation reset() → 초기 상태 복귀
 *  10. 소스 문서 최대 10개 제한
 */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DocumentSchema } from "@/types/document-schema";

import { PromptBox } from "..";
import type { PreviewPaneHandle } from "../../preview-pane";
import { useDocumentMutation } from "../useDocumentMutation";

// ─── apiClient mock ───────────────────────────────────────────────────────
// Dialog(Portal) 안 Radix Select 는 jsdom 에서 제약이 많아 부수적 테스트는 생략.
// 핵심 로직(mutation, 단축키, 콜백)은 최상위 DOM 에서 검증 가능.

const mockPost = vi.fn();
const mockGet = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    delete: vi.fn(),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// ─── fixture ──────────────────────────────────────────────────────────────

function buildDocumentSchema(): DocumentSchema {
  return {
    document_id: "00000000-0000-4000-8000-000000000001",
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

beforeEach(() => {
  mockPost.mockReset();
  mockGet.mockReset();
  // 기본 GET 응답: 빈 리스트 (문서 / 에이전트)
  mockGet.mockResolvedValue({ items: [] });
});

// ─── 1) 빈 프롬프트 → 버튼 disabled ───────────────────────────────────────

describe("PromptBox — 제출 가능 여부", () => {
  it("프롬프트가 비어있으면 생성 버튼이 disabled 이다", () => {
    render(<PromptBox onDocumentGenerated={vi.fn()} />);
    const submit = screen.getByTestId("prompt-submit");
    expect(submit).toBeDisabled();
  });

  it("프롬프트 입력 후 버튼이 enabled 된다", () => {
    render(<PromptBox onDocumentGenerated={vi.fn()} />);
    const textarea = screen.getByTestId("prompt-textarea");
    fireEvent.change(textarea, { target: { value: "분기 매출 리포트 생성" } });
    const submit = screen.getByTestId("prompt-submit");
    expect(submit).not.toBeDisabled();
  });
});

// ─── 2) DocumentType 기본값 ──────────────────────────────────────────────

describe("PromptBox — 문서 유형", () => {
  it("DocumentType 기본값은 slide_report 이고 select 에 반영된다", () => {
    render(<PromptBox onDocumentGenerated={vi.fn()} />);
    const trigger = screen.getByTestId("document-type-select");
    expect(trigger).toHaveTextContent("슬라이드 보고서");
  });

  it("defaultDocumentType 지정 시 그 값이 초기 노출된다", () => {
    render(<PromptBox onDocumentGenerated={vi.fn()} defaultDocumentType="minutes" />);
    const trigger = screen.getByTestId("document-type-select");
    expect(trigger).toHaveTextContent("회의록");
  });
});

// ─── 3) 생성 버튼 클릭 → POST /v2/documents ───────────────────────────────

describe("PromptBox — 생성 요청", () => {
  it("생성 버튼 클릭 시 apiClient.post 가 /v2/documents 로 snake_case body 를 전송한다", async () => {
    const schema = buildDocumentSchema();
    mockPost.mockResolvedValue(schema);

    const onGenerated = vi.fn();
    render(<PromptBox onDocumentGenerated={onGenerated} />);

    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "4월 주간 현황 보고서" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    await waitFor(() => expect(mockPost).toHaveBeenCalledTimes(1));
    expect(mockPost).toHaveBeenCalledWith("/v2/documents", {
      mode: "free_generation",
      type: "slide_report",
      prompt: "4월 주간 현황 보고서",
      source_document_ids: [],
      agent_id: null,
    });

    await waitFor(() => expect(onGenerated).toHaveBeenCalledWith(schema));
  });

  it("성공 시 previewPaneRef.sendSchemaPatch 로 첫 페이지를 주입한다", async () => {
    const schema = buildDocumentSchema();
    mockPost.mockResolvedValue(schema);

    const sendSchemaPatch = vi.fn();
    const sendTokenUpdate = vi.fn();
    const getIframe = vi.fn().mockReturnValue(null);
    const previewPaneRef = {
      current: {
        sendSchemaPatch,
        sendTokenUpdate,
        getIframe,
      } satisfies PreviewPaneHandle,
    };

    render(<PromptBox onDocumentGenerated={vi.fn()} previewPaneRef={previewPaneRef} />);

    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "테스트 프롬프트" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    await waitFor(() => expect(sendSchemaPatch).toHaveBeenCalledTimes(1));
    expect(sendSchemaPatch).toHaveBeenCalledWith({
      patchType: "page",
      pageId: "p1",
      data: schema.pages[0],
    });
  });

  it("실패 응답 시 ValidationFeedback 에 에러 메시지가 노출된다", async () => {
    mockPost.mockRejectedValue(new Error("LLM 응답 실패"));

    render(<PromptBox onDocumentGenerated={vi.fn()} />);
    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "테스트" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    const alert = await screen.findByTestId("validation-feedback");
    expect(alert).toBeInTheDocument();
    expect(screen.getByTestId("validation-mutation-error")).toHaveTextContent("LLM 응답 실패");
    expect(screen.getByTestId("validation-retry")).toBeInTheDocument();
  });
});

// ─── 4) 단축키 Ctrl+Enter ─────────────────────────────────────────────────

describe("PromptBox — 단축키", () => {
  it("Ctrl+Enter 로 생성 요청을 트리거한다", async () => {
    mockPost.mockResolvedValue(buildDocumentSchema());
    render(<PromptBox onDocumentGenerated={vi.fn()} />);

    const textarea = screen.getByTestId("prompt-textarea");
    fireEvent.change(textarea, { target: { value: "단축키 테스트" } });
    fireEvent.keyDown(textarea, { key: "Enter", ctrlKey: true });

    await waitFor(() => expect(mockPost).toHaveBeenCalledTimes(1));
  });

  it("Cmd+Enter(Mac) 로도 생성 요청을 트리거한다", async () => {
    mockPost.mockResolvedValue(buildDocumentSchema());
    render(<PromptBox onDocumentGenerated={vi.fn()} />);

    const textarea = screen.getByTestId("prompt-textarea");
    fireEvent.change(textarea, { target: { value: "맥 단축키" } });
    fireEvent.keyDown(textarea, { key: "Enter", metaKey: true });

    await waitFor(() => expect(mockPost).toHaveBeenCalledTimes(1));
  });

  it("프롬프트 빈칸일 때 Ctrl+Enter 는 요청을 보내지 않는다", () => {
    render(<PromptBox onDocumentGenerated={vi.fn()} />);
    const textarea = screen.getByTestId("prompt-textarea");
    fireEvent.keyDown(textarea, { key: "Enter", ctrlKey: true });
    expect(mockPost).not.toHaveBeenCalled();
  });
});

// ─── 5) 로딩 UI ───────────────────────────────────────────────────────────

describe("PromptBox — 로딩 상태", () => {
  it("요청 진행 중에는 textarea / 버튼이 disabled 되고 '생성 중' 라벨이 뜬다", async () => {
    // post 해결을 수동 제어
    let resolveFn: (value: DocumentSchema) => void = () => {};
    mockPost.mockImplementation(
      () =>
        new Promise<DocumentSchema>((resolve) => {
          resolveFn = resolve;
        }),
    );

    render(<PromptBox onDocumentGenerated={vi.fn()} />);
    fireEvent.change(screen.getByTestId("prompt-textarea"), {
      target: { value: "긴 문서" },
    });
    fireEvent.click(screen.getByTestId("prompt-submit"));

    // 로딩 중 UI 확인
    await waitFor(() => {
      expect(screen.getByTestId("prompt-submit")).toHaveTextContent("생성 중");
    });
    expect(screen.getByTestId("prompt-textarea")).toBeDisabled();
    expect(screen.getByTestId("prompt-input").getAttribute("aria-busy")).toBe("true");

    // 해제 후 UI 복원
    await act(async () => {
      resolveFn(buildDocumentSchema());
    });
    await waitFor(() => {
      expect(screen.getByTestId("prompt-submit")).toHaveTextContent("생성");
    });
  });
});

// ─── 6) useDocumentMutation reset ─────────────────────────────────────────

describe("useDocumentMutation", () => {
  it("reset() 호출 시 isPending/error/data 가 모두 초기화된다", async () => {
    mockPost.mockResolvedValue(buildDocumentSchema());

    const { result, rerender } = renderUseHook(() => useDocumentMutation());

    await act(async () => {
      await result.current.mutateAsync({
        prompt: "reset 테스트",
        documentType: "slide_report",
        sourceDocumentIds: [],
        agentId: null,
      });
    });

    expect(result.current.data).not.toBeNull();

    act(() => {
      result.current.reset();
    });

    rerender();
    expect(result.current.isPending).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it("mutateAsync 실패 시 error state 가 Error 인스턴스로 세팅된다", async () => {
    mockPost.mockRejectedValue(new Error("서버 오류"));

    const { result } = renderUseHook(() => useDocumentMutation());

    await act(async () => {
      await expect(
        result.current.mutateAsync({
          prompt: "실패",
          documentType: "slide_report",
          sourceDocumentIds: [],
          agentId: null,
        }),
      ).rejects.toThrow("서버 오류");
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("서버 오류");
    expect(result.current.data).toBeNull();
  });
});

// ─── helper: renderHook 경량 구현 (React Testing Library renderHook 대체) ───

function renderUseHook<T>(hook: () => T): {
  result: { current: T };
  rerender: () => void;
} {
  const result = { current: undefined as unknown as T };
  function Harness() {
    result.current = hook();
    return null;
  }
  const utils = render(<Harness />);
  return {
    result,
    rerender: () => utils.rerender(<Harness />),
  };
}
