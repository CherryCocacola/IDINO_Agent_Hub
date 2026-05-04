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
    user: { id: "1", username: "admin", role: "admin", organization_id: "org-1" },
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
  usePathname: () => "/projects",
  useSearchParams: () => new URLSearchParams(),
}));

import ProjectsPage from "./page";

describe("ProjectsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint.includes("/departments")) return Promise.resolve([]);
      return Promise.resolve({ items: [], total: 0 });
    });
  });

  it("renders the projects page with heading and create button", async () => {
    render(<ProjectsPage />);

    expect(screen.getByRole("heading", { level: 1, name: "프로젝트" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /프로젝트 생성/ })).toBeInTheDocument();
  });

  it("shows empty state when no projects exist", async () => {
    render(<ProjectsPage />);

    await waitFor(() => {
      expect(screen.getByText("프로젝트가 없습니다")).toBeInTheDocument();
    });
  });

  it("has a search input for filtering projects", () => {
    render(<ProjectsPage />);

    expect(screen.getByPlaceholderText(/프로젝트 검색/i)).toBeInTheDocument();
  });

  it("opens the create project dialog when clicking the create button", async () => {
    const user = userEvent.setup();
    render(<ProjectsPage />);

    await user.click(screen.getByRole("button", { name: /프로젝트 생성/ }));

    await waitFor(() => {
      // 다이얼로그가 열리면 "프로젝트 생성" 텍스트가 2개 (버튼 + 다이얼로그 제목)
      const elements = screen.getAllByText("프로젝트 생성");
      expect(elements.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("shows error toast on API failure", async () => {
    mockGet.mockRejectedValue(new Error("Failed to load projects"));

    render(<ProjectsPage />);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Failed to load projects", "error");
    });
  });
});
