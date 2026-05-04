import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// recharts를 JSDOM 환경에서 렌더링 문제를 방지하기 위해 모킹
vi.mock("recharts", () => ({
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => null,
  Cell: () => null,
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => null,
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Legend: () => null,
}));

const mockGet = vi.fn();

vi.mock("@/lib/api/client", () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  default: {
    get: (...args: unknown[]) => mockGet(...args),
    post: vi.fn(),
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
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

import DashboardPage from "./page";

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 대시보드 API 응답 mock 데이터
    // 컴포넌트가 기대하는 실제 API 응답 구조에 맞춰야 한다:
    //   /dashboard/metrics → DashboardMetricsResponse (active_users, total_documents, total_searches, feature_usage)
    //   /dashboard/upload-status → Record<string, number>
    //   /dashboard/response-times → ResponseTimeResponse { timestamps, values }
    //   /dashboard/search-errors → SearchErrorResponse { dates, error_counts }
    mockGet.mockImplementation((endpoint: string) => {
      switch (endpoint) {
        case "/dashboard/metrics":
          return Promise.resolve({
            total_users: 200,
            active_users: 150,
            total_documents: 420,
            total_searches: 8750,
            feature_usage: { search: 1500, qa: 800, chatbot: 600, agent: 300 },
          });
        case "/dashboard/upload-status":
          return Promise.resolve({
            completed: 350,
            processing: 25,
            waiting: 15,
            error: 10,
          });
        case "/dashboard/response-times":
          return Promise.resolve({
            timestamps: ["00:00", "01:00"],
            values: [120, 115],
          });
        case "/dashboard/search-errors":
          return Promise.resolve({
            dates: ["2025-01-01", "2025-01-02"],
            error_counts: [5, 3],
          });
        default:
          return Promise.resolve({});
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 대시보드 페이지 제목이 렌더링되는지 확인
  it("renders the dashboard heading", () => {
    render(<DashboardPage />);
    expect(screen.getByText("대시보드")).toBeInTheDocument();
  });

  // 3개의 메트릭 카드(검색 사용자 수, 검색 기능 사용 수, 등록 완료 문서 수)가 렌더링되는지 확인
  // "검색 기능 사용 수"는 메트릭 카드와 차트 제목 두 곳에 나타나므로 getAllByText 사용
  it("renders all three metric cards", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("검색 사용자 수")).toBeInTheDocument();
      expect(screen.getAllByText("검색 기능 사용 수").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("등록 완료 문서 수")).toBeInTheDocument();
    });
  });

  // 데이터 로드 후 메트릭 값이 올바르게 표시되는지 확인
  // active_users=150 → search_users → "150"
  // feature_usage 합계(1500+800+600+300=3200) → "3,200"
  // total_documents=420 → registered_docs → "420"
  it("displays metric values after data loads", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("150")).toBeInTheDocument();
      expect(screen.getByText("3,200")).toBeInTheDocument();
      expect(screen.getByText("420")).toBeInTheDocument();
    });
  });

  // 차트 섹션들이 올바른 한글 제목으로 렌더링되는지 확인
  it("renders chart sections", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("문서 업로드 상태")).toBeInTheDocument();
      expect(screen.getByText("시간대별 응답 시간")).toBeInTheDocument();
      expect(screen.getByText("날짜별 검색 오류 수")).toBeInTheDocument();
    });
  });

  // API 에러 발생 시 addToast가 호출되는지 확인
  // 컴포넌트 내부에서 각 API 호출은 .catch(() => null)로 감싸져 있으므로
  // 개별 rejected promise는 조용히 무시된다.
  // 동기적으로 throw하면 Promise.all 바깥에서 에러가 발생하여 catch 블록에 도달한다.
  it("calls addToast on API error", async () => {
    mockGet.mockImplementation(() => {
      throw new Error("Server Error");
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Server Error", "error");
    });
  });
});
