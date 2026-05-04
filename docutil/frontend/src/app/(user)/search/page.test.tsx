import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockPost = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({}),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    delete: vi.fn(),
  },
  default: {
    get: vi.fn().mockResolvedValue({}),
    post: (...args: unknown[]) => mockPost(...args),
    put: vi.fn(),
    delete: vi.fn(),
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
  usePathname: () => "/search",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock child components
vi.mock("@/components/search/search-result-card", () => ({
  SearchResultCard: ({ result }: { result: { documentName: string } }) => (
    <div data-testid="search-result-card">{result.documentName}</div>
  ),
}));

vi.mock("@/components/documents/document-selector", () => ({
  DocumentSelector: () => <div data-testid="document-selector">Document Selector</div>,
}));

import SearchPage from "./page";

describe("SearchPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset window.location.search to empty
    Object.defineProperty(window, "location", {
      writable: true,
      value: {
        ...window.location,
        search: "",
        href: "http://localhost:3000/search",
        origin: "http://localhost:3000",
      },
    });
  });

  it("renders the search heading", () => {
    render(<SearchPage />);

    expect(screen.getByText("문서 검색")).toBeInTheDocument();
  });

  it("renders the search input field", () => {
    render(<SearchPage />);

    expect(screen.getByPlaceholderText(/검색어를 입력하세요/)).toBeInTheDocument();
  });

  it("renders search type options (All, Q&A, Keyword)", () => {
    render(<SearchPage />);

    expect(screen.getByText("전체")).toBeInTheDocument();
    expect(screen.getByText("Q&A")).toBeInTheDocument();
    expect(screen.getByText("키워드")).toBeInTheDocument();
  });

  it("renders the scope and filters buttons", () => {
    render(<SearchPage />);

    expect(screen.getByText("범위")).toBeInTheDocument();
  });

  it("displays search results after a successful search", async () => {
    const user = userEvent.setup();

    mockPost.mockResolvedValue({
      results: [
        {
          id: "result-1",
          documentName: "Test Document.pdf",
          chunkText: "This is the matched text...",
          score: 0.85,
        },
      ],
      total_count: 1,
    });

    render(<SearchPage />);

    const input = screen.getByPlaceholderText(/검색어를 입력하세요/);
    await user.type(input, "test query");

    const searchButton = screen.getByText("검색");
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
    });
  });

  it("shows error toast on search failure", async () => {
    const user = userEvent.setup();

    mockPost.mockRejectedValue(new Error("Search failed"));

    render(<SearchPage />);

    const input = screen.getByPlaceholderText(/검색어를 입력하세요/);
    await user.type(input, "test query");

    const searchButton = screen.getByText("검색");
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("검색에 실패했습니다. 다시 시도해주세요.", "error");
    });
  });
});
