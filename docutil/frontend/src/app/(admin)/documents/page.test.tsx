import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const mockGet = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    upload: vi.fn(),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    upload: vi.fn(),
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
  usePathname: () => "/documents",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock react-dropzone
vi.mock("react-dropzone", () => ({
  useDropzone: () => ({
    getRootProps: () => ({ role: "presentation" }),
    getInputProps: () => ({ type: "file" }),
    isDragActive: false,
  }),
}));

import DocumentsPage from "./page";

describe("DocumentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/projects/tree") return Promise.resolve([]);
      if (endpoint === "/documents") return Promise.resolve({ items: [], total: 0 });
      if (endpoint.includes("/departments")) return Promise.resolve([]);
      return Promise.resolve([]);
    });
  });

  it("renders the documents heading", async () => {
    render(<DocumentsPage />);

    expect(screen.getByRole("heading", { level: 1, name: "문서" })).toBeInTheDocument();
  });

  it("renders the folder sidebar with all documents option", async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText("전체 문서")).toBeInTheDocument();
    });
  });

  it("renders the upload area with drag-and-drop text", async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText(/파일을 드래그하여 놓거나 클릭하여 선택하세요/i)).toBeInTheDocument();
    });
  });

  it("shows empty state when no documents exist", async () => {
    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.getByText("문서가 없습니다")).toBeInTheDocument();
    });
  });

  it("renders search input for filtering documents", () => {
    render(<DocumentsPage />);

    expect(screen.getByPlaceholderText(/문서 검색/i)).toBeInTheDocument();
  });

  it("shows error toast when tree fetch fails", async () => {
    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/projects/tree") return Promise.reject(new Error("Tree load failed"));
      if (endpoint === "/documents") return Promise.resolve({ items: [], total: 0 });
      return Promise.resolve([]);
    });

    render(<DocumentsPage />);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Tree load failed", "error");
    });
  });
});
