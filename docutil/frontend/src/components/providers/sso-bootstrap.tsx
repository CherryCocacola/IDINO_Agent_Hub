"use client";

/**
 * SsoBootstrap — AgentHub → DocUtil SSO (옵션 A) 클라이언트 수신부.
 *
 * 트랙 1-5 SSO (2026-05-26):
 *   AgentHub 사이드바의 "DocUtil 사용자 화면" 메뉴는 useDocUtilSso composable 을 통해
 *   DocUtil URL 으로 이동할 때 JWT 를 두 경로로 동봉한다:
 *     1) cookie:    du_sso_token=<JWT>; domain=192.168.10.39; path=/
 *     2) fragment:  http://192.168.10.39:8041/search#sso_token=<JWT>
 *
 *   본 컴포넌트는 (user)/layout.tsx 에서 마운트되어:
 *     a) fragment / cookie 에서 토큰 추출
 *     b) JWT 만료 여부 확인 (만료된 토큰 무시)
 *     c) Zustand persist 의 localStorage('auth-storage') 갱신 + useAuth 인메모리 갱신
 *     d) /api/v1/users/me 호출로 사용자 정보 채움
 *     e) cookie / URL fragment 즉시 제거 (보안)
 *
 *   설계 결정:
 *   - 이미 로그인된 사용자에 대해 SSO 토큰이 들어와도 강제 갱신 — AgentHub 가 진입점이라
 *     "AgentHub 의 현재 사용자" 와 "DocUtil 의 현재 사용자" 가 다르면 혼란을 일으킴.
 *     단, 토큰 만료된 경우는 무시 (기존 세션이 더 유효).
 *   - users/me 호출 실패 시 토큰을 폐기하고 정상 로그인 화면으로 fallback (영향 없음).
 *   - 새 탭/창에서 storage 이벤트가 발생하여 다른 탭도 자동 동기화 (use-auth.ts 의 핸들러).
 */

import { useEffect, useRef } from "react";

import { useAuth, type User } from "@/lib/hooks/use-auth";

/** AgentHub 와 합의된 cookie 이름 (useDocUtilSso.ts 참조) */
const SSO_COOKIE_NAME = "du_sso_token";

/** AgentHub 와 합의된 URL fragment 키 (useDocUtilSso.ts 참조) */
const SSO_FRAGMENT_KEY = "sso_token";

/** cookie 제거 시 사용할 공유 도메인 (AgentHub 와 동일해야 함) */
const SHARED_COOKIE_DOMAIN = "192.168.10.39";

/** Zustand persist 가 사용하는 localStorage 키 (use-auth.ts 의 `name`) */
const AUTH_STORAGE_KEY = "auth-storage";

/** DocUtil 사용자 정보 조회 API */
const ME_ENDPOINT = "/api/v1/users/me";

/** JWT payload 의 exp 클레임을 ms 타임스탬프로 변환. 형식 오류 시 null. */
function parseJwtExp(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

/** 토큰이 만료되었거나 5초 이내 만료 예정이면 true. */
function isTokenExpired(token: string): boolean {
  const exp = parseJwtExp(token);
  if (exp === null) return true; // 파싱 불가 → 안전하게 만료 처리
  return exp <= Date.now() + 5000;
}

/** URL fragment 에서 sso_token 추출. */
function extractTokenFromFragment(): string | null {
  if (typeof window === "undefined") return null;
  const hash = window.location.hash;
  if (!hash || hash.length < 2) return null;

  // fragment 는 '#key1=val1&key2=val2' 형식 — URLSearchParams 로 파싱
  const params = new URLSearchParams(hash.substring(1));
  const token = params.get(SSO_FRAGMENT_KEY);
  return token && token.length > 0 ? token : null;
}

/** cookie 에서 sso 토큰 추출. */
function extractTokenFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [name, ...rest] = cookie.trim().split("=");
    if (name === SSO_COOKIE_NAME) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

/** URL fragment 에서 sso_token 만 제거하고 다른 fragment 파라미터는 보존. */
function clearFragmentToken(): void {
  if (typeof window === "undefined") return;
  const hash = window.location.hash;
  if (!hash || hash.length < 2) return;

  const params = new URLSearchParams(hash.substring(1));
  if (!params.has(SSO_FRAGMENT_KEY)) return;

  params.delete(SSO_FRAGMENT_KEY);

  const remaining = params.toString();
  const newHash = remaining.length > 0 ? `#${remaining}` : "";
  // history.replaceState 으로 뒤로가기 히스토리 오염 방지
  window.history.replaceState(
    {},
    "",
    `${window.location.pathname}${window.location.search}${newHash}`,
  );
}

/** SSO cookie 제거 — DocUtil 진입 직후 호출되어 토큰 노출을 최소화. */
function clearSsoCookie(): void {
  if (typeof document === "undefined") return;
  // domain 명시 / 미명시 두 가지 패턴 모두 시도 (브라우저에 따라 set 시 domain 이 무시되었을 수 있음)
  document.cookie = `${SSO_COOKIE_NAME}=; path=/; max-age=0; domain=${SHARED_COOKIE_DOMAIN}; SameSite=Lax`;
  document.cookie = `${SSO_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax`;
}

/**
 * Zustand persist 의 localStorage 를 토큰으로 갱신.
 * useAuth 의 setState 만 호출하면 다음 새로고침 시 persist 가 덮어쓰므로,
 * localStorage 와 인메모리 둘 다 동시 갱신해야 한다.
 */
function persistAccessToken(token: string, user: User): void {
  if (typeof window === "undefined") return;

  // 1) localStorage 갱신 — persist 가 다음 hydration 때 읽을 값
  try {
    const stored = window.localStorage.getItem(AUTH_STORAGE_KEY);
    const expiresAt = parseJwtExp(token);
    const parsed = stored ? JSON.parse(stored) : { state: {}, version: 0 };
    parsed.state = {
      ...(parsed.state ?? {}),
      user,
      accessToken: token,
      // SSO 진입 시점에는 refreshToken 을 받지 않음 (AgentHub 의 단순 access token 만 공유).
      // 만료 시 DocUtil 의 기존 refresh 흐름은 실패하고 로그인 화면으로 fallback.
      refreshToken: null,
      isAuthenticated: true,
      tokenExpiresAt: expiresAt,
    };
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(parsed));
  } catch (err) {
    console.warn("[sso-bootstrap] localStorage 갱신 실패", err);
  }

  // 2) 인메모리 zustand 갱신 — 현재 탭의 useAuth 구독자가 즉시 인식
  useAuth.setState({
    user,
    accessToken: token,
    refreshToken: null,
    isAuthenticated: true,
    tokenExpiresAt: parseJwtExp(token),
  });
}

/**
 * DocUtil /api/v1/users/me 호출하여 사용자 정보 획득.
 * apiClient 를 쓰지 않는 이유: apiClient 는 localStorage 에서 토큰을 읽는데,
 * persistAccessToken 이전에 호출되면 stale token 을 사용. 명시적으로 새 토큰을 전달.
 */
async function fetchCurrentUser(token: string): Promise<User | null> {
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    const url = ME_ENDPOINT.replace(/^\/api\/v1/, apiBase);
    const res = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
      console.warn("[sso-bootstrap] /users/me 실패", res.status);
      return null;
    }
    return (await res.json()) as User;
  } catch (err) {
    console.warn("[sso-bootstrap] /users/me 호출 오류", err);
    return null;
  }
}

/**
 * SsoBootstrap — (user)/layout.tsx 에서 마운트되는 클라이언트 컴포넌트.
 * 자식 렌더링이 없으며 (null 반환), 부수효과만 수행.
 */
export function SsoBootstrap(): null {
  // StrictMode 에서 useEffect 가 두 번 실행되는 것을 방지 — 토큰 폐기/네트워크 호출 중복 차단
  const processedRef = useRef(false);

  useEffect(() => {
    if (processedRef.current) return;
    processedRef.current = true;

    // fragment 우선 (브라우저 호환성 100%), 없으면 cookie
    const token = extractTokenFromFragment() ?? extractTokenFromCookie();

    if (!token) {
      // SSO 진입이 아닌 일반 진입 — 아무것도 하지 않음
      return;
    }

    // 즉시 cookie/fragment 제거 — 토큰 노출 시간 최소화 (성공/실패와 무관)
    clearSsoCookie();
    clearFragmentToken();

    if (isTokenExpired(token)) {
      console.warn("[sso-bootstrap] SSO 토큰이 만료됨 — 무시");
      return;
    }

    // 비동기로 사용자 정보 조회 → 성공 시 localStorage + 인메모리 갱신
    void (async () => {
      const user = await fetchCurrentUser(token);
      if (!user) {
        console.warn("[sso-bootstrap] SSO 토큰으로 사용자 조회 실패 — 기존 세션 유지");
        return;
      }
      persistAccessToken(token, user);
      // 성공 로그는 console.info 가 lint 정책상 차단되어 있어 생략.
      // SSO 동작 확인은 useAuth 상태(/users/me 응답 후 isAuthenticated=true) 로 충분.
    })();
  }, []);

  return null;
}

export default SsoBootstrap;
