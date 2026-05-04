import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockGet = vi.fn();
const mockPost = vi.fn();
const mockPut = vi.fn();
const mockDelete = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: (...args: unknown[]) => mockPost(...args),
    put: (...args: unknown[]) => mockPut(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
  },
}));

vi.mock("@/lib/hooks/use-auth", () => ({
  useAuth: () => ({
    user: { id: "1", username: "admin", role: "admin" },
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
  usePathname: () => "/search-scopes",
  useSearchParams: () => new URLSearchParams(),
}));

import SearchScopesPage from "./page";

const mockScopes = [
  {
    id: "scope-1",
    name: "Engineering Scope",
    description: "Search across engineering docs",
    project_id: "proj-1",
    board_id: null,
    folder_id: null,
    location_path: "Engineering Project",
    chatbot_enabled: true,
    qa_enabled: true,
    keyword_search_enabled: true,
    agent_enabled: false,
    chunk_size: 512,
    chunk_overlap: 50,
    title_weight: 0.3,
    keyword_weight: 0.3,
    content_weight: 0.4,
    max_results: 10,
    similarity_threshold: 0.7,
    created_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "scope-2",
    name: "Research Scope",
    description: "Research papers scope",
    project_id: "proj-2",
    board_id: null,
    folder_id: null,
    location_path: "Research Project",
    chatbot_enabled: true,
    qa_enabled: false,
    keyword_search_enabled: true,
    agent_enabled: true,
    chunk_size: 256,
    chunk_overlap: 25,
    title_weight: 0.2,
    keyword_weight: 0.4,
    content_weight: 0.4,
    max_results: 20,
    similarity_threshold: 0.6,
    created_at: "2025-01-15T00:00:00Z",
  },
];

describe("SearchScopesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // 컴포넌트는 { items: [], total: number } 형태의 응답을 기대한다
    mockGet.mockResolvedValue({ items: mockScopes, total: mockScopes.length });
  });

  // 페이지 제목 "검색 범위"와 생성 버튼 "범위 생성"이 렌더링되는지 확인
  it("renders the page heading and create button", () => {
    render(<SearchScopesPage />);

    expect(screen.getByText("검색 범위")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /범위 생성/ })).toBeInTheDocument();
  });

  // 데이터 로드 후 검색 범위 카드들이 렌더링되는지 확인
  it("renders scope cards after data loads", async () => {
    render(<SearchScopesPage />);

    await waitFor(() => {
      expect(screen.getByText("Engineering Scope")).toBeInTheDocument();
      expect(screen.getByText("Research Scope")).toBeInTheDocument();
    });
  });

  // 검색 범위 카드에 기능 배지(Chatbot, Keyword 등)가 표시되는지 확인
  it("renders feature badges on scope cards", async () => {
    render(<SearchScopesPage />);

    await waitFor(() => {
      // Engineering scope는 chatbot, Q&A, keyword가 활성화됨
      const chatbotBadges = screen.getAllByText("챗봇");
      expect(chatbotBadges.length).toBeGreaterThan(0);

      const keywordBadges = screen.getAllByText("키워드");
      expect(keywordBadges.length).toBeGreaterThan(0);
    });
  });

  // 범위 생성 버튼 클릭 시 생성 다이얼로그가 열리는지 확인
  it("opens create dialog when clicking create scope button", async () => {
    const user = userEvent.setup();
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/search-scopes")
        return Promise.resolve({ items: mockScopes, total: mockScopes.length });
      if (endpoint === "/search-scopes/locations") return Promise.resolve([]);
      return Promise.resolve([]);
    });

    render(<SearchScopesPage />);

    await user.click(screen.getByRole("button", { name: /범위 생성/ }));

    await waitFor(() => {
      expect(screen.getByText("검색 범위 생성")).toBeInTheDocument();
    });
  });

  // API 호출 실패 시 에러 토스트가 표시되는지 확인
  it("shows error toast on fetch failure", async () => {
    mockGet.mockRejectedValue(new Error("Network error"));

    render(<SearchScopesPage />);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Network error", "error");
    });
  });
});
