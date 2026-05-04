/**
 * index.test.tsx — ExportMenu UI 단위 테스트 (경량)
 *
 * Radix DropdownMenu 를 jsdom 에서 프로그램적으로 여는 것은 pointer capture
 * 이슈로 까다롭다. 본 테스트는 트리거 자체의 렌더링/상태만 검증하고,
 * 실제 드롭다운 열기/항목 클릭은 Playwright E2E(S2 D5 이후) 로 이관한다.
 *
 * 검증 항목:
 *   1. documentId 가 null 이면 트리거 버튼이 disabled.
 *   2. documentId 가 지정되면 트리거 버튼이 활성화되고 "내보내기" 라벨이 보인다.
 *   3. Download 아이콘이 렌더된다 (idle 상태 기본 아이콘).
 */

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ExportMenu } from "./index";

// ─── 의존성 mock ──────────────────────────────────────────────────────────

const mockRequestExportJob = vi.fn();
const mockGetExportStatus = vi.fn();

vi.mock("@/lib/api/documents-v2", async () => {
  const actual =
    await vi.importActual<typeof import("@/lib/api/documents-v2")>("@/lib/api/documents-v2");
  return {
    ...actual,
    requestExportJob: (...args: unknown[]) => mockRequestExportJob(...args),
    getExportStatus: (...args: unknown[]) => mockGetExportStatus(...args),
  };
});

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    getBlob: vi.fn(() => Promise.resolve(new Blob(["stub"]))),
  },
  default: {
    getBlob: vi.fn(() => Promise.resolve(new Blob(["stub"]))),
  },
}));

const mockAddToast = vi.fn();
vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({
    addToast: mockAddToast,
    toast: vi.fn(),
    toasts: [],
    dismiss: vi.fn(),
  }),
}));

// ─── 테스트 ────────────────────────────────────────────────────────────────

describe("ExportMenu", () => {
  beforeEach(() => {
    mockRequestExportJob.mockReset();
    mockGetExportStatus.mockReset();
    mockAddToast.mockReset();
  });

  it("documentId 가 null 이면 트리거가 비활성화된다", () => {
    render(<ExportMenu documentId={null} />);
    const trigger = screen.getByTestId("export-menu-trigger");
    expect(trigger).toBeDisabled();
  });

  it("documentId 가 주어지면 트리거가 활성화되고 '내보내기' 라벨이 보인다", () => {
    render(<ExportMenu documentId="00000000-0000-4000-8000-000000000001" />);
    const trigger = screen.getByTestId("export-menu-trigger");
    expect(trigger).not.toBeDisabled();
    expect(trigger).toHaveTextContent("내보내기");
    // aria 레이블로 접근성 확인.
    expect(trigger).toHaveAttribute("aria-label", "내보내기 메뉴 열기");
  });

  it("idle 상태에서는 Download 아이콘이 렌더된다", () => {
    render(<ExportMenu documentId="00000000-0000-4000-8000-000000000001" />);
    const trigger = screen.getByTestId("export-menu-trigger");
    // lucide-react 는 SVG 로 렌더되며 class 에 lucide-download 를 포함.
    const svg = trigger.querySelector("svg");
    expect(svg).not.toBeNull();
    expect(svg?.classList.toString()).toContain("lucide-download");
  });
});
