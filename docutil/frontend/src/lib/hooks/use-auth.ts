import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface User {
  id: string;
  username: string;
  email: string;
  role: "super_admin" | "admin" | "member" | "viewer";
  organization_id: string;
  department_id?: string;
  department_name?: string;
  organization_name?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  tokenExpiresAt: number | null;
  _hasHydrated: boolean;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setAccessToken: (token: string) => void;
  setTokenExpiresAt: (t: number) => void;
  setHasHydrated: (state: boolean) => void;
}

/** JWT payload에서 exp 클레임을 추출하여 밀리초 단위 타임스탬프로 반환 */
function parseJwtExp(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      tokenExpiresAt: null,
      _hasHydrated: false,
      login: (user, accessToken, refreshToken) => {
        const expiresAt = parseJwtExp(accessToken);
        set({ user, accessToken, refreshToken, isAuthenticated: true, tokenExpiresAt: expiresAt });
      },
      logout: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          tokenExpiresAt: null,
        }),
      setAccessToken: (accessToken) => {
        const expiresAt = parseJwtExp(accessToken);
        set({ accessToken, tokenExpiresAt: expiresAt });
      },
      setTokenExpiresAt: (t) => set({ tokenExpiresAt: t }),
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: "auth-storage",
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);

// Cross-tab 동기화: 다른 탭에서 auth-storage가 변경되면 현재 탭도 동기화
// storage 이벤트는 같은 origin의 "다른" 탭에서만 발생하므로 무한 루프 없음
if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    // auth-storage 키 변경만 처리
    if (event.key !== "auth-storage") return;

    if (event.newValue === null) {
      // 다른 탭에서 localStorage 삭제 (로그아웃)
      useAuth.getState().logout();
      window.location.href = "/login";
      return;
    }

    try {
      const parsed = JSON.parse(event.newValue);
      const state = parsed?.state;
      if (!state) return;

      if (!state.isAuthenticated || !state.accessToken) {
        // 다른 탭에서 로그아웃 상태로 변경됨
        useAuth.getState().logout();
        window.location.href = "/login";
      } else {
        // 다른 탭에서 토큰 갱신 또는 새 로그인 — 현재 탭 인메모리 상태 동기화
        useAuth.setState({
          user: state.user,
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
          isAuthenticated: state.isAuthenticated,
          tokenExpiresAt: state.tokenExpiresAt ?? null,
        });
      }
    } catch {
      // JSON 파싱 실패 시 무시
    }
  });
}
