import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockDeleteApi = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    delete: (...args: unknown[]) => mockDeleteApi(...args),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    delete: (...args: unknown[]) => mockDeleteApi(...args),
  },
}));

vi.mock("@/lib/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", username: "user1", role: "member" },
    accessToken: "test-token",
    isAuthenticated: true,
  }),
}));

const mockAddToast = vi.fn();

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({
    toasts: [],
    toast: vi.fn(),
    dismiss: vi.fn(),
    addToast: mockAddToast,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  usePathname: () => "/reports",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock child components
vi.mock("@/components/documents/document-selector", () => ({
  DocumentSelector: () => <div data-testid="document-selector">Document Selector</div>,
}));

import ReportsPage from "./page";

describe("ReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/reports/templates") return Promise.resolve({ templates: [] });
      if (endpoint === "/reports") return Promise.resolve({ reports: [] });
      if (endpoint === "/chat/sessions") return Promise.resolve({ sessions: [] });
      return Promise.resolve({});
    });
  });

  it("renders the reports heading", () => {
    render(<ReportsPage />);

    expect(screen.getByText("보고서")).toBeInTheDocument();
    expect(screen.getByText(/문서 및 채팅 세션에서 보고서를 생성합니다/i)).toBeInTheDocument();
  });

  it("renders Generate and My Reports tabs", () => {
    render(<ReportsPage />);

    expect(screen.getByText("생성")).toBeInTheDocument();
    expect(screen.getByText("내 보고서")).toBeInTheDocument();
  });

  it("renders template cards on the generate tab", () => {
    render(<ReportsPage />);

    // Demo templates are shown by default
    expect(screen.getByText("Summary Report")).toBeInTheDocument();
    expect(screen.getByText("Comparison Analysis")).toBeInTheDocument();
    expect(screen.getByText("Meeting Minutes")).toBeInTheDocument();
    expect(screen.getByText("Data Extraction")).toBeInTheDocument();
  });

  it("renders the generate button", () => {
    render(<ReportsPage />);

    expect(screen.getByRole("button", { name: /보고서 생성/ })).toBeInTheDocument();
  });

  it("disables generate button when no template is selected", async () => {
    render(<ReportsPage />);

    const generateButton = screen.getByRole("button", { name: /보고서 생성/ });
    expect(generateButton).toBeDisabled();
  });

  it("switches to My Reports tab and shows empty state", async () => {
    const user = userEvent.setup();
    render(<ReportsPage />);

    await user.click(screen.getByText("내 보고서"));

    await waitFor(() => {
      expect(screen.getByText("아직 보고서가 없습니다")).toBeInTheDocument();
      expect(screen.getByText(/생성 탭에서 보고서를 생성하세요/i)).toBeInTheDocument();
    });
  });

  it("renders output format options", () => {
    render(<ReportsPage />);

    expect(screen.getByText("DOCX")).toBeInTheDocument();
    expect(screen.getByText("PDF")).toBeInTheDocument();
    expect(screen.getByText("HTML")).toBeInTheDocument();
    expect(screen.getByText("HWP")).toBeInTheDocument();
  });
});
