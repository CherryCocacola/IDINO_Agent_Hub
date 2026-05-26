import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import i18n from '@/i18n'
import type { RefreshTokenResponseDto } from '@/types'
import {
  safeGetAuthStorage,
  safeSetAuthStorage,
  safeRemoveAuthStorage,
  safeGetLocalStorage
} from '@/utils/storage'

/**
 * AgentHub API axios 인스턴스.
 *
 * 핵심 정책:
 *  - 요청 인터셉터: localStorage / sessionStorage 어디든 있는 JWT 를 자동 부착
 *  - 응답 인터셉터: 401 시 refresh 토큰으로 1회 갱신 시도, 실패 시 한국어 안내 + /login redirect
 *  - 트랙 #88 C2 (2026-05-13): 사용자에게 "세션이 만료되었습니다" 알림을 보여준 뒤
 *    1초 후 redirect 하여 사용자가 메시지를 읽을 시간을 확보한다.
 */

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// ============================================================================
// 요청 인터셉터: 토큰 부착 (local 또는 session 어디든 있으면 사용)
// ============================================================================
api.interceptors.request.use(
  (config) => {
    const token = safeGetAuthStorage('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 트랙 #111 (2026-05-27): GET 응답 브라우저 cache 차단.
    // AgentHub API 응답에 Cache-Control 헤더가 없어 브라우저 heuristic cache 가
    // mutation (POST/DELETE) 후 GET 응답을 stale 로 보여주는 결함 해소.
    // - Cache-Control: no-cache → 매 요청 server 재검증
    // - Pragma: no-cache → HTTP/1.0 호환
    // - cache buster query param (?_t=) → CDN/proxy 우회
    const method = (config.method || 'get').toLowerCase()
    if (method === 'get') {
      config.headers['Cache-Control'] = 'no-cache'
      config.headers['Pragma'] = 'no-cache'
      config.params = { ...(config.params || {}), _t: Date.now() }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ============================================================================
// 응답 인터셉터: 401 → refresh → 실패 시 안내 후 /login
// ============================================================================

/**
 * 세션 만료 안내 후 일정 지연을 두고 /login 으로 이동.
 *
 * 알림 수단은 점진적 폴백:
 *   1) (TODO) 프로젝트에 정식 toast 컴포넌트가 도입되면 그것을 사용
 *   2) 현재는 window.alert — 즉시 사용자에게 보이고 닫혀야 redirect 가 진행되므로 사용자 통제 가능
 *
 * 호출자가 race 로 여러 번 트리거하지 않도록 in-flight 가드를 둔다.
 */
let isRedirectingToLogin = false
/**
 * 세션 만료/refresh 실패 시 사용자 알림 + storage 양쪽 청소 + /login redirect.
 *
 * sseClient.ts (SSE 경로) 도 axios 인터셉터와 동일 정책을 적용해야 router 가드의
 * "로그인 잔존 토큰" race 가 발생하지 않으므로 named export 하여 재사용한다.
 * (트랙 #97-post3 — SSE 401 시 localStorage 만 청소되어 sessionStorage 토큰 잔존 →
 * router 가드 index.ts:438-441 이 token 있다고 판정 → /login → / (Dashboard) 튕김 결함 해소)
 */
export function notifyAndRedirectToLogin(messageKey: 'auth.session.expired' | 'auth.session.noRefreshToken') {
  if (isRedirectingToLogin) return
  isRedirectingToLogin = true

  // 두 저장소 모두 청소 — 재로그인 시 깨끗한 상태에서 시작
  safeRemoveAuthStorage('token')
  safeRemoveAuthStorage('refreshToken')

  // 현재 i18n locale 로 안내 (Composition API: i18n.global.t)
  const t = i18n.global.t as (key: string) => string
  const message = t(messageKey)

  // 사용자에게 메시지 표시. window.alert 는 사용자가 닫을 때까지 차단되므로
  // 사용자가 메시지를 읽었다는 것이 보장된 뒤 redirect 가 일어난다.
  // (정식 toast 도입 시 비-차단 알림 + setTimeout(1000) 방식으로 전환 권장)
  try {
    window.alert(message)
  } catch {
    // 알림이 차단된 환경 — 그대로 진행
  }

  // 이미 /login 경로면 추가 이동 불필요
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  } else {
    isRedirectingToLogin = false
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Blob 응답은 인터셉터에서 건너뛰기
    if (error.config?.responseType === 'blob') {
      // Blob 에러 응답을 JSON으로 파싱 시도
      if (error.response?.data instanceof Blob) {
        try {
          const text = await error.response.data.text()
          const json = JSON.parse(text)
          error.response.data = json
        } catch {
          // JSON 파싱 실패 시 그대로 반환
        }
      }
      return Promise.reject(error)
    }

    if (error.response?.status === 401) {
      // 로그인 요청 자체의 401은 인터셉터에서 처리하지 않음 (Login.vue 가 인라인 처리)
      const requestUrl = error.config?.url || ''
      if (requestUrl.includes('/auth/login')) {
        return Promise.reject(error)
      }
      // refresh 요청 자체가 401 이면 즉시 만료 처리 (무한 루프 방지)
      if (requestUrl.includes('/auth/refresh')) {
        notifyAndRedirectToLogin('auth.session.expired')
        return Promise.reject(error)
      }

      // 토큰 갱신 시도
      const refreshToken = safeGetAuthStorage('refreshToken')
      if (refreshToken) {
        try {
          // 인터셉터를 거치지 않는 별도 인스턴스로 호출 — 401 재귀 방지 +
          // 만료된 access token 이 Authorization 헤더로 자동 부착되는 것 방지.
          // baseURL 옵션은 절대경로일 때 무용하므로 제거 (이전 코드의 사소한 청소).
          const response = await axios.post<RefreshTokenResponseDto>(
            '/api/auth/refresh',
            { refreshToken }
          )
          const newToken = response.data.token
          const newRefreshToken = response.data.refreshToken ?? refreshToken

          // 사용자가 "자동 로그인 유지" 를 켰는지 여부에 따라 저장소 결정.
          // localStorage 에 기존 토큰이 있었으면 영구 모드.
          const persistent = !!safeGetLocalStorage('token') ||
            (!!safeGetLocalStorage('refreshToken') && refreshToken === safeGetLocalStorage('refreshToken'))

          safeSetAuthStorage('token', newToken, persistent)
          safeSetAuthStorage('refreshToken', newRefreshToken, persistent)

          // 원 요청 재시도 (새 토큰으로 Authorization 헤더 갱신)
          const retryConfig: AxiosRequestConfig = {
            ...error.config,
            headers: {
              ...error.config.headers,
              Authorization: `Bearer ${newToken}`
            }
          }
          return api.request(retryConfig)
        } catch (refreshError) {
          // refresh 실패 → 세션 만료 안내 후 /login
          console.warn('[api] Refresh token failed:', refreshError)
          notifyAndRedirectToLogin('auth.session.expired')
          return Promise.reject(refreshError)
        }
      } else {
        // refresh 토큰 자체가 없는 경우 — 로그인 정보 없음 안내
        notifyAndRedirectToLogin('auth.session.noRefreshToken')
      }
    }
    return Promise.reject(error)
  }
)

export default api
