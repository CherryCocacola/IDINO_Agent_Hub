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
  usePathname: () => "/chat",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock child components
vi.mock("@/components/chat/chat-message", () => ({
  ChatMessage: ({ content, role }: { content: string; role: string }) => (
    <div data-testid={`chat-message-${role}`}>{content}</div>
  ),
}));

vi.mock("@/components/chat/document-scope-modal", () => ({
  DocumentScopeModal: ({ open, onClose }: { open: boolean; onClose: () => void }) =>
    open ? (
      <div data-testid="scope-modal">
        <button onClick={onClose}>Close Modal</button>
      </div>
    ) : null,
}));

// Mock WebSocket
const mockWsSend = vi.fn();
const mockWsClose = vi.fn();

vi.stubGlobal(
  "WebSocket",
  vi.fn().mockImplementation(() => ({
    send: mockWsSend,
    close: mockWsClose,
    readyState: 1,
    onopen: null,
    onmessage: null,
    onclose: null,
    onerror: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    OPEN: 1,
  })),
);

import ChatPage from "./page";

const mockSessions = {
  sessions: [
    {
      id: "session-1",
      title: "First Chat",
      createdAt: "2025-01-01T00:00:00Z",
      updatedAt: "2025-01-01T12:00:00Z",
      scopedDocumentIds: ["doc-1", "doc-2"],
    },
    {
      id: "session-2",
      title: "Second Chat",
      createdAt: "2025-01-02T00:00:00Z",
      updatedAt: "2025-01-02T12:00:00Z",
      scopedDocumentIds: [],
    },
  ],
};

describe("ChatPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockGet.mockImplementation((endpoint: string) => {
      if (endpoint === "/chat/sessions") return Promise.resolve(mockSessions);
      if (endpoint.includes("/messages")) return Promise.resolve({ messages: [] });
      return Promise.resolve({});
    });
  });

  it("renders the new chat button", async () => {
    render(<ChatPage />);

    // There may be multiple "New Chat" buttons (desktop + mobile)
    const newChatButtons = screen.getAllByText("새 채팅");
    expect(newChatButtons.length).toBeGreaterThan(0);
  });

  it("renders the session list after loading", async () => {
    render(<ChatPage />);

    await waitFor(() => {
      expect(screen.getByText("First Chat")).toBeInTheDocument();
      expect(screen.getByText("Second Chat")).toBeInTheDocument();
    });
  });

  it("renders the empty state when no session is selected", () => {
    render(<ChatPage />);

    expect(screen.getByText("다중 문서 Q&A 채팅")).toBeInTheDocument();
    expect(
      screen.getByText(/기존 채팅 세션을 선택하거나 새로 생성하여 문서에 대해 질문하세요/),
    ).toBeInTheDocument();
  });

  it("renders the message input area when a session is selected", async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    await waitFor(() => {
      expect(screen.getByText("First Chat")).toBeInTheDocument();
    });

    await user.click(screen.getByText("First Chat"));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/메시지를 입력하세요/)).toBeInTheDocument();
    });
  });

  it("shows error toast when session load fails", async () => {
    mockGet.mockRejectedValue(new Error("Session load failed"));

    render(<ChatPage />);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("채팅 세션을 불러오지 못했습니다.", "error");
    });
  });
});
