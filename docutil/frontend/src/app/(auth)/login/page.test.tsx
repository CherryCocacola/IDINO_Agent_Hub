import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

// 의존성 모킹 (컴포넌트 import 전에 수행)
const mockPush = vi.fn();
const mockLogin = vi.fn();
const mockAddToast = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: vi.fn() }),
  usePathname: () => "/login",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/hooks/use-auth", () => ({
  useAuth: () => ({
    user: null,
    accessToken: null,
    isAuthenticated: false,
    login: mockLogin,
    logout: vi.fn(),
  }),
}));

vi.mock("@/lib/hooks/use-toast", () => ({
  useToast: () => ({
    toasts: [],
    toast: vi.fn(),
    dismiss: vi.fn(),
    addToast: mockAddToast,
  }),
}));

import LoginPage from "./page";

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as ReturnType<typeof vi.fn>).mockReset();
  });

  // 로그인 폼이 아이디, 비밀번호 필드와 로그인 버튼으로 올바르게 렌더링되는지 확인
  it("renders the login form with username and password fields", () => {
    render(<LoginPage />);

    // 아이디 입력 필드 (id="username" 속성으로 정확하게 매칭)
    expect(screen.getByPlaceholderText("아이디를 입력하세요")).toBeInTheDocument();
    // 비밀번호 입력 필드 (placeholder: "비밀번호를 입력하세요")
    expect(screen.getByPlaceholderText("비밀번호를 입력하세요")).toBeInTheDocument();
    // 로그인 버튼
    expect(screen.getByRole("button", { name: "로그인" })).toBeInTheDocument();
    // 서브 타이틀 "관리자 로그인"
    expect(screen.getByText("관리자 로그인")).toBeInTheDocument();
  });

  // "아이디 저장" 체크박스가 렌더링되는지 확인
  it("renders remember me checkbox", () => {
    render(<LoginPage />);

    expect(screen.getByLabelText(/아이디 저장/)).toBeInTheDocument();
  });

  // 빈 폼 제출 시 유효성 검증 에러 메시지가 표시되는지 확인
  it("shows validation error when submitting empty form", async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const submitButton = screen.getByRole("button", { name: /로그인/ });
    await user.click(submitButton);

    expect(screen.getByText(/아이디와 비밀번호를 입력해주세요/)).toBeInTheDocument();
  });

  // 올바른 자격증명으로 로그인 시 fetch 호출 및 admin 사용자 리다이렉트 확인
  it("calls fetch and redirects admin on successful login", async () => {
    const user = userEvent.setup();

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          user: {
            id: "1",
            username: "admin",
            email: "admin@example.com",
            role: "admin",
            organization_id: "org-1",
          },
          access_token: "test-access-token",
          refresh_token: "test-refresh-token",
        }),
    });

    render(<LoginPage />);

    await user.type(screen.getByPlaceholderText("아이디를 입력하세요"), "admin");
    await user.type(screen.getByPlaceholderText(/비밀번호를 입력하세요/), "password123");
    await user.click(screen.getByRole("button", { name: /로그인/ }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "admin",
          password: "password123",
          remember_me: false,
        }),
      });
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  // 잘못된 자격증명(401)으로 로그인 시 에러 메시지가 표시되는지 확인
  it("displays error message on failed login (401)", async () => {
    const user = userEvent.setup();

    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ message: "아이디 또는 비밀번호가 올바르지 않습니다." }),
    });

    render(<LoginPage />);

    await user.type(screen.getByPlaceholderText("아이디를 입력하세요"), "wrong");
    await user.type(screen.getByPlaceholderText(/비밀번호를 입력하세요/), "wrong");
    await user.click(screen.getByRole("button", { name: /로그인/ }));

    await waitFor(() => {
      expect(screen.getByText(/아이디 또는 비밀번호가 올바르지 않습니다/)).toBeInTheDocument();
    });
  });

  // 네트워크 오류(fetch 실패) 시 서버 연결 에러 메시지가 표시되는지 확인
  it("displays network error message on fetch failure", async () => {
    const user = userEvent.setup();

    (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error("Network Error"));

    render(<LoginPage />);

    await user.type(screen.getByPlaceholderText("아이디를 입력하세요"), "admin");
    await user.type(screen.getByPlaceholderText(/비밀번호를 입력하세요/), "password123");
    await user.click(screen.getByRole("button", { name: /로그인/ }));

    await waitFor(() => {
      expect(screen.getByText(/서버에 연결할 수 없습니다/)).toBeInTheDocument();
    });
  });
});
