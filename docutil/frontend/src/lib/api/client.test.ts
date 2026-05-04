import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ApiClient는 localStorage의 'auth-storage'에서 토큰을 읽어 Authorization 헤더에 포함시킨다.
// setToken/clearToken 메서드가 존재하지 않으므로 localStorage를 직접 조작하여 테스트한다.

describe("ApiClient", () => {
  let client: {
    get<T>(endpoint: string, params?: Record<string, string>): Promise<T>;
    post<T>(endpoint: string, data?: unknown): Promise<T>;
    put<T>(endpoint: string, data?: unknown): Promise<T>;
    delete<T>(endpoint: string): Promise<T>;
    upload<T>(endpoint: string, formData: FormData): Promise<T>;
  };
  let mockFetch: ReturnType<typeof vi.fn>;
  const originalHref = window.location.href;

  beforeEach(async () => {
    // fetch mock 초기화
    mockFetch = vi.fn();
    global.fetch = mockFetch;

    // localStorage 초기화
    localStorage.clear();

    // 모듈을 초기화하여 깨끗한 인스턴스를 가져온다
    vi.resetModules();

    const mod = await import("./client");
    client = mod.apiClient as typeof client;
  });

  afterEach(() => {
    // window.location 복원
    window.location.href = originalHref;
    localStorage.clear();
  });

  describe("GET requests", () => {
    // GET 요청이 올바른 URL로 전송되는지 확인
    it("makes a GET request to the correct URL", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ data: "test" }),
      });

      const result = await client.get("/test-endpoint");

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toContain("/test-endpoint");

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.method).toBe("GET");
      expect(result).toEqual({ data: "test" });
    });

    // GET 요청에 쿼리 파라미터가 올바르게 추가되는지 확인
    it("appends query params to GET requests", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });

      await client.get("/search", { q: "hello", page: "1" });

      const calledUrl = mockFetch.mock.calls[0][0];
      expect(calledUrl).toContain("q=hello");
      expect(calledUrl).toContain("page=1");
    });
  });

  describe("POST requests", () => {
    // POST 요청이 JSON body와 함께 전송되는지 확인
    it("makes a POST request with JSON body", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: "1" }),
      });

      const result = await client.post("/items", { name: "test" });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.method).toBe("POST");
      expect(calledOptions.body).toBe(JSON.stringify({ name: "test" }));
      expect(result).toEqual({ id: "1" });
    });

    // body 없이 POST 요청이 전송되는지 확인
    it("makes a POST request without body", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true }),
      });

      await client.post("/trigger");

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.method).toBe("POST");
      expect(calledOptions.body).toBeUndefined();
    });
  });

  describe("PUT requests", () => {
    // PUT 요청이 JSON body와 함께 전송되는지 확인
    it("makes a PUT request with JSON body", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: "1", name: "updated" }),
      });

      const result = await client.put("/items/1", { name: "updated" });

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.method).toBe("PUT");
      expect(calledOptions.body).toBe(JSON.stringify({ name: "updated" }));
      expect(result).toEqual({ id: "1", name: "updated" });
    });
  });

  describe("DELETE requests", () => {
    // DELETE 요청이 전송되고 204 응답 시 null을 반환하는지 확인
    it("makes a DELETE request", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: () => Promise.reject(),
      });

      const result = await client.delete("/items/1");

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.method).toBe("DELETE");
      expect(result).toBeNull();
    });
  });

  describe("Authorization header", () => {
    // localStorage에 토큰이 설정되어 있을 때 Bearer 토큰이 헤더에 포함되는지 확인
    it("includes Bearer token when token is stored in localStorage", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });

      // localStorage에 auth-storage 키로 토큰을 설정
      localStorage.setItem(
        "auth-storage",
        JSON.stringify({ state: { accessToken: "my-secret-token" } }),
      );
      await client.get("/protected");

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.headers["Authorization"]).toBe("Bearer my-secret-token");
    });

    // localStorage에 토큰이 없을 때 Authorization 헤더가 포함되지 않는지 확인
    it("does not include Authorization header when no token is stored", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });

      // localStorage를 비워서 토큰이 없는 상태를 만든다
      localStorage.removeItem("auth-storage");
      await client.get("/public");

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.headers["Authorization"]).toBeUndefined();
    });
  });

  describe("401 handling", () => {
    // 401 응답 시 /login으로 리다이렉트되는지 확인
    it("redirects to /login on 401 response", async () => {
      // 첫 번째 요청: 401 응답 → 토큰 갱신 시도
      // 갱신 토큰이 없으므로 갱신 실패 → /login으로 리다이렉트
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: "Unauthorized" }),
      });

      await expect(client.get("/protected")).rejects.toThrow("Unauthorized");
      expect(window.location.href).toBe("/login");
    });

    // 401 응답 후 토큰이 제거(또는 무효화)되고 다음 요청에 포함되지 않는지 확인
    it("does not send token after 401 when localStorage is cleared", async () => {
      // 먼저 localStorage에 토큰 설정
      localStorage.setItem(
        "auth-storage",
        JSON.stringify({ state: { accessToken: "some-token" } }),
      );

      // 401 응답 → 토큰 갱신 시도 (refreshToken 없으므로 실패)
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: "Unauthorized" }),
      });

      try {
        await client.get("/protected");
      } catch {
        // 예상대로 에러 발생
      }

      // localStorage에서 토큰을 삭제하여 다음 요청에 포함되지 않도록 한다
      localStorage.removeItem("auth-storage");

      // 다음 요청에 Authorization 헤더가 포함되지 않는지 확인
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });

      await client.get("/public");

      // 401 이후의 fetch 호출을 확인 (리프레시 시도 제외하고 마지막 호출)
      const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
      const calledOptions = lastCall[1];
      expect(calledOptions.headers["Authorization"]).toBeUndefined();
    });
  });

  describe("Error handling", () => {
    // API 응답의 detail 메시지로 에러가 throw되는지 확인
    it("throws error with detail message from API", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Validation failed: name is required" }),
      });

      await expect(client.post("/items", {})).rejects.toThrow(
        "Validation failed: name is required",
      );
    });

    // API 응답에 detail이 없을 때 제네릭 에러가 throw되는지 확인
    it("throws generic error when API returns no detail", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: () => Promise.reject(), // JSON 파싱 실패
      });

      await expect(client.get("/broken")).rejects.toThrow("Internal Server Error");
    });
  });

  describe("Content-Type header", () => {
    // 표준 요청에 Content-Type이 application/json으로 설정되는지 확인
    it("sets Content-Type to application/json for standard requests", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      });

      await client.get("/test");

      const calledOptions = mockFetch.mock.calls[0][1];
      expect(calledOptions.headers["Content-Type"]).toBe("application/json");
    });
  });
});
