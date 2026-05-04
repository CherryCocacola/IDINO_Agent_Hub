import { useAuth } from "@/lib/hooks/use-auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

/**
 * API 에러 클래스 — HTTP 상태 코드와 서버 detail 메시지를 보존한다.
 *
 * Phase 4 S2 D7: /reports POST/DELETE 경로가 410 Gone을 반환하도록 변경되어,
 * 호출 측에서 status === 410 을 감지해 디자이너 이관 토스트를 띄울 수 있어야 한다.
 * 기존 `new Error(detail)` 방식은 상태 코드를 잃어버리므로 ApiError 로 교체한다.
 */
export class ApiError extends Error {
  /** HTTP 상태 코드 (예: 410, 403, 500) */
  readonly status: number;
  /** 서버 응답 detail (한국어 메시지가 들어있음) */
  readonly detail: string;
  /** X-Deprecated-API 헤더 값 ("true" 이면 deprecated API) */
  readonly deprecated: boolean;

  constructor(status: number, detail: string, deprecated: boolean = false) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.deprecated = deprecated;
  }
}

/** 에러가 ApiError 인스턴스인지 안전하게 판별한다 (HMR 환경에서도 동작) */
export function isApiError(err: unknown): err is ApiError {
  return err instanceof ApiError || (err instanceof Error && err.name === "ApiError");
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = localStorage.getItem("auth-storage");
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed?.state?.accessToken || null;
    }
  } catch {
    // ignore parse errors
  }
  return null;
}

class ApiClient {
  private baseUrl: string;
  // 토큰 갱신 중복 요청 방지를 위한 플래그
  private isRefreshing = false;
  // 토큰 갱신 중 대기하는 요청들의 큐
  private refreshQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: Error) => void;
  }> = [];

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    return getStoredToken();
  }

  /**
   * localStorage에서 리프레시 토큰을 가져온다.
   */
  private getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    try {
      const stored = localStorage.getItem("auth-storage");
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed?.state?.refreshToken || null;
      }
    } catch {
      // JSON 파싱 오류 무시
    }
    return null;
  }

  /**
   * 리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급받는다.
   * 이미 갱신 중이면 기존 갱신이 완료될 때까지 대기한다.
   */
  private async refreshAccessToken(): Promise<string> {
    // 이미 토큰 갱신 중이면 큐에 추가하여 대기
    if (this.isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        this.refreshQueue.push({ resolve, reject });
      });
    }

    this.isRefreshing = true;

    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        throw new Error("No refresh token available");
      }

      const res = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!res.ok) {
        throw new Error("Token refresh failed");
      }

      const data = await res.json();
      const newAccessToken: string = data.access_token;

      // Zustand persist 스토어의 액세스 토큰을 갱신
      const stored = localStorage.getItem("auth-storage");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed?.state) {
          parsed.state.accessToken = newAccessToken;
          // 리프레시 토큰도 갱신된 경우 함께 업데이트
          if (data.refresh_token) {
            parsed.state.refreshToken = data.refresh_token;
          }
          localStorage.setItem("auth-storage", JSON.stringify(parsed));
        }
      }

      // Zustand 인메모리 상태도 동기화 (localStorage만 업데이트하면 UI가 stale 상태 유지됨)
      useAuth.getState().setAccessToken(newAccessToken);

      // 대기 중인 요청들에 새 토큰 전달
      this.refreshQueue.forEach((pending) => pending.resolve(newAccessToken));
      this.refreshQueue = [];

      return newAccessToken;
    } catch (error) {
      // 갱신 실패 시 대기 중인 요청들에도 오류 전파
      this.refreshQueue.forEach((pending) =>
        pending.reject(error instanceof Error ? error : new Error("Token refresh failed")),
      );
      this.refreshQueue = [];
      throw error;
    } finally {
      this.isRefreshing = false;
    }
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    if (typeof window === "undefined") {
      throw new Error("API client can only be used on the client side");
    }
    const { params, ...init } = options;
    const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }

    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(init.headers as Record<string, string>),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(url.toString(), { ...init, headers });

    if (res.status === 401) {
      // 401 발생 시 토큰 갱신을 시도한 후, 성공하면 원래 요청을 재시도한다.
      // 갱신도 실패하면 로그인 페이지로 리다이렉트한다.
      try {
        const newToken = await this.refreshAccessToken();

        // 갱신된 토큰으로 원래 요청을 재시도
        const retryHeaders: Record<string, string> = {
          ...headers,
          Authorization: `Bearer ${newToken}`,
        };
        const retryRes = await fetch(url.toString(), { ...init, headers: retryHeaders });

        if (retryRes.status === 401) {
          // 재시도도 401이면 로그인 페이지로 이동
          window.location.href = "/login";
          throw new Error("Unauthorized");
        }

        if (!retryRes.ok) {
          const error = await retryRes.json().catch(() => ({ detail: retryRes.statusText }));
          const deprecated = retryRes.headers.get("X-Deprecated-API") === "true";
          throw new ApiError(retryRes.status, error.detail || "Request failed", deprecated);
        }

        if (retryRes.status === 204) return null as T;
        return retryRes.json();
      } catch {
        // 토큰 갱신 자체가 실패한 경우 로그인 페이지로 리다이렉트
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      const deprecated = res.headers.get("X-Deprecated-API") === "true";
      throw new ApiError(res.status, error.detail || "Request failed", deprecated);
    }

    if (res.status === 204) {
      // API 요청 성공 → 세션 타이머 갱신 (30분 연장)
      this.extendSession();
      return null as T;
    }
    // API 요청 성공 → 세션 타이머 갱신 (30분 연장)
    this.extendSession();
    return res.json();
  }

  /** API 요청 성공 시 세션 만료 시각을 현재 + 30분으로 연장한다. */
  private extendSession() {
    try {
      const { tokenExpiresAt, setTokenExpiresAt } = useAuth.getState();
      if (tokenExpiresAt && setTokenExpiresAt) {
        // 현재 시각 + 30분 (밀리초)
        setTokenExpiresAt(Date.now() + 30 * 60 * 1000);
      }
    } catch {
      // 세션 연장 실패해도 API 동작에 영향 없음
    }
  }

  get<T>(endpoint: string, params?: Record<string, string>) {
    return this.request<T>(endpoint, { method: "GET", params });
  }

  post<T>(endpoint: string, data?: unknown) {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T>(endpoint: string, data?: unknown) {
    return this.request<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  patch<T>(endpoint: string, data?: unknown) {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  async getBlob(endpoint: string): Promise<Blob> {
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${this.baseUrl}${endpoint}`, { method: "GET", headers });

    if (res.status === 401) {
      const newToken = await this.refreshAccessToken();
      const retryRes = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "GET",
        headers: { Authorization: `Bearer ${newToken}` },
      });
      if (!retryRes.ok) throw new Error("Download failed");
      return retryRes.blob();
    }

    if (!res.ok) throw new Error("Download failed");
    return res.blob();
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    // 업로드 전에 토큰 유효성을 확인하고, 만료 임박 시 먼저 갱신한다.
    // Nginx(8041) 크로스 오리진 요청에서 401 발생 시 CORS 문제로
    // 브라우저가 응답을 읽지 못할 수 있으므로, 사전 갱신이 안전하다.
    let token = this.getToken();
    const { tokenExpiresAt } = useAuth.getState();
    if (tokenExpiresAt && tokenExpiresAt - Date.now() < 60 * 1000) {
      // 만료 1분 이내이면 미리 갱신
      try {
        token = await this.refreshAccessToken();
      } catch {
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }
    }

    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    // 파일 업로드는 Nginx 리버스 프록시(포트 8041)를 경유한다.
    // Next.js rewrite 프록시(포트 3040)는 30초 타임아웃이 있어 대용량 파일에서 실패하므로,
    // Nginx(proxy_read_timeout 300s)를 직접 사용하여 안정적으로 전송한다.
    const uploadBase =
      typeof window !== "undefined"
        ? `${window.location.protocol}//${window.location.hostname}:8041/api/v1`
        : this.baseUrl;
    const res = await fetch(`${uploadBase}${endpoint}`, {
      method: "POST",
      headers,
      body: formData,
    });

    // 401 발생 시 토큰 갱신 후 재시도 (getBlob과 동일 패턴)
    if (res.status === 401) {
      try {
        const newToken = await this.refreshAccessToken();
        const retryRes = await fetch(`${uploadBase}${endpoint}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${newToken}` },
          body: formData,
        });
        if (retryRes.status === 401) {
          window.location.href = "/login";
          throw new Error("Unauthorized");
        }
        if (!retryRes.ok) {
          // 재시도 실패 시에도 서버 detail 을 보존해 사용자에게 노출한다.
          const error = await retryRes.json().catch(() => ({ detail: retryRes.statusText }));
          const deprecated = retryRes.headers.get("X-Deprecated-API") === "true";
          throw new ApiError(retryRes.status, error.detail || "업로드에 실패했습니다.", deprecated);
        }
        return retryRes.json();
      } catch (err) {
        // ApiError 는 그대로 상위로 전달 (서버 detail 보존)
        if (isApiError(err)) throw err;
        // 토큰 갱신 실패 등 인증 오류만 로그인 페이지로 유도
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }
    }

    if (!res.ok) {
      // 기존 `throw new Error("Upload failed")` 는 서버의 422/400 detail 을
      // 삼켜 사용자가 실패 원인을 알 수 없게 했다. ApiError 로 교체해
      // 부서/프로젝트 검증 메시지 등 한국어 detail 을 toast 로 노출한다.
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      const deprecated = res.headers.get("X-Deprecated-API") === "true";
      throw new ApiError(res.status, error.detail || "업로드에 실패했습니다.", deprecated);
    }
    return res.json();
  }
}

export const apiClient = new ApiClient(API_BASE);
export default apiClient;
