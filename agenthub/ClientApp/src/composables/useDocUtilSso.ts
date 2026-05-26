/**
 * useDocUtilSso — AgentHub → DocUtil SSO (옵션 A) 도우미.
 *
 * 트랙 1-5 SSO (2026-05-26):
 *   AgentHub 와 DocUtil 은 같은 host (192.168.10.39) 다른 port (64005 / 8041) 로 배포된다.
 *   양 시스템은 같은 JWT SecretKey 를 공유하며, DocUtil 의 verify_token 이 AgentHub 토큰을 검증한다.
 *
 *   본 composable 은 AgentHub 사용자가 DocUtil 사용자 화면 (/search, /chat 등) 진입 시
 *   현재 AgentHub JWT 를 DocUtil 이 읽을 수 있도록 cookie + URL fragment 두 경로로 전달한다.
 *
 *   왜 두 경로 모두?
 *   - cookie domain=192.168.10.39 — IP cookie 는 Chrome 73+ 에서 정상이지만, 일부 브라우저
 *     (Safari ITP 등) 에서 IP host 의 명시 domain 을 거부할 수 있다.
 *   - URL fragment (#sso_token=...) — fragment 는 server 에 전송되지 않으며 (보안), DocUtil
 *     의 sso-bootstrap 컴포넌트가 mount 시 읽어서 localStorage 에 주입한다.
 *   - 둘 중 하나만 도달해도 SSO 가 성립하므로 안정적.
 *
 *   보안:
 *   - cookie: SameSite=Lax + max-age=300 (5분 만료 — 진입 직후 DocUtil 이 즉시 제거)
 *   - HTTP 환경 운영이므로 Secure 미지정. HTTPS 도입 시 SameSite=None; Secure 로 강화.
 *   - URL fragment 는 history 에 남으므로 DocUtil 측에서 `history.replaceState` 로 제거 필수.
 *
 *   사용:
 *     const { redirectToDocUtil } = useDocUtilSso()
 *     redirectToDocUtil('/search')     // → http://192.168.10.39:8041/search
 *     redirectToDocUtil('/chat', { newTab: true })
 */
import { useAuthStore } from '@/stores/auth'

/** DocUtil 사용자 화면의 base URL — 운영 / 환경별 분기 가능 (env var 미지원 시 default) */
const DOCUTIL_USER_BASE_URL = 'http://192.168.10.39:8041'

/** cookie 가 도달할 공유 host. AgentHub / DocUtil 양쪽이 같은 IP host 일 때만 유효. */
const SHARED_COOKIE_DOMAIN = '192.168.10.39'

/** SSO 토큰 cookie 이름 — DocUtil 의 sso-bootstrap 과 합의된 키 */
const SSO_COOKIE_NAME = 'du_sso_token'

/** URL fragment 키 — DocUtil 의 sso-bootstrap 과 합의된 키 */
const SSO_FRAGMENT_KEY = 'sso_token'

/** cookie 유효 시간 (초). 짧을수록 안전. DocUtil 진입 즉시 제거하므로 5분이면 충분. */
const SSO_COOKIE_MAX_AGE_SEC = 300

export interface RedirectOptions {
  /** 새 탭으로 열기. 기본 false (같은 탭에서 이동) */
  newTab?: boolean
}

export function useDocUtilSso() {
  const authStore = useAuthStore()

  /**
   * AgentHub JWT 를 cookie 로 설정한다.
   *
   * 주의: domain= 명시는 IP host 일 때 일부 브라우저가 거부 가능. 거부되어도
   * silently 실패하므로 URL fragment fallback 이 항상 함께 보내진다.
   */
  function setSsoCookie(token: string): void {
    const cookieParts = [
      `${SSO_COOKIE_NAME}=${encodeURIComponent(token)}`,
      `domain=${SHARED_COOKIE_DOMAIN}`,
      `path=/`,
      `max-age=${SSO_COOKIE_MAX_AGE_SEC}`,
      `SameSite=Lax`
      // 운영 HTTPS 도입 시: 'Secure' 추가 + SameSite=None
    ]
    document.cookie = cookieParts.join('; ')
  }

  /**
   * DocUtil 사용자 화면으로 이동한다.
   *
   * 흐름:
   *   1) AgentHub authStore.token 존재 확인 (없으면 SSO 불가 — fallback 으로 일반 navigate)
   *   2) cookie 설정 (도달 가능성 1)
   *   3) URL fragment 추가 (도달 가능성 2 — 항상 동작)
   *   4) window.location.href 으로 navigate (Vue Router 우회)
   *
   * @param path DocUtil 의 내부 경로. 슬래시 포함 ('/search' 등)
   * @param options newTab=true 면 새 탭으로
   */
  function redirectToDocUtil(path: string, options: RedirectOptions = {}): void {
    const token = authStore.token

    // path 정규화 — 항상 / 로 시작하도록
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    const baseUrl = `${DOCUTIL_USER_BASE_URL}${normalizedPath}`

    let finalUrl = baseUrl

    if (token) {
      // cookie 설정 (silently 실패 가능, 그래도 진행)
      try {
        setSsoCookie(token)
      } catch (err) {
        console.warn('[useDocUtilSso] cookie 설정 실패 — fragment fallback 사용', err)
      }

      // URL fragment 추가 — 항상 동작
      finalUrl = `${baseUrl}#${SSO_FRAGMENT_KEY}=${encodeURIComponent(token)}`
    } else {
      console.warn('[useDocUtilSso] AgentHub token 없음 — DocUtil 로그인 화면이 노출됨')
    }

    if (options.newTab) {
      window.open(finalUrl, '_blank', 'noopener,noreferrer')
    } else {
      // SPA 라우터 우회 — 외부 origin 으로 이동
      window.location.href = finalUrl
    }
  }

  return {
    redirectToDocUtil
  }
}
