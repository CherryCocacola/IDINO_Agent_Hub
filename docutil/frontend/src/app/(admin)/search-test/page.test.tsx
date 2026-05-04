import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockGet = vi.fn();
const mockPost = vi.fn();

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
  usePathname: () => "/search-test",
  useSearchParams: () => new URLSearchParams(),
}));

import SearchTestPage from "./page";

describe("SearchTestPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default: return empty arrays (no scopes, no history)
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/search-scopes/options") return Promise.resolve([]);
      if (endpoint === "/search/history") return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  it("renders the search test heading", () => {
    render(<SearchTestPage />);

    expect(screen.getByText("Search Test")).toBeInTheDocument();
  });

  it("renders search type tabs", async () => {
    render(<SearchTestPage />);

    expect(screen.getByRole("tab", { name: /hybrid/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /chatbot/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /q&a/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /keyword/i })).toBeInTheDocument();
  });

  it("renders query input and search button", () => {
    render(<SearchTestPage />);

    expect(screen.getByPlaceholderText(/enter search keywords/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("shows validation toast when searching with empty query", async () => {
    const user = userEvent.setup();
    render(<SearchTestPage />);

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalled();
    });

    // Find the Search button specifically (not icon)
    const searchButton = screen.getByRole("button", { name: /^search$/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Please enter a search query", "error");
    });
  });

  it("performs a search when scope is available and query entered", async () => {
    const user = userEvent.setup();

    // Provide a scope so search can work
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/search-scopes/options")
        return Promise.resolve([{ id: "scope-1", name: "Test Scope", location_path: "Test" }]);
      if (endpoint === "/search/history") return Promise.resolve([]);
      return Promise.resolve([]);
    });

    mockPost.mockResolvedValue([
      {
        id: "chunk-1",
        document_name: "System Requirements.pdf",
        content: "This is a test result chunk...",
        score: 0.95,
        highlights: ["<em>test</em> result"],
      },
    ]);

    render(<SearchTestPage />);

    // Wait for scopes to load
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith("/search-scopes/options");
    });

    const input = screen.getByPlaceholderText(/enter search keywords/i);
    await user.type(input, "test query");

    const searchButton = screen.getByRole("button", { name: /^search$/i });
    await user.click(searchButton);

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
    });
  });

  it("shows error toast on search failure", async () => {
    mockGet.mockRejectedValue(new Error("Failed to load scopes"));

    render(<SearchTestPage />);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Failed to load scopes", "error");
    });
  });
});
