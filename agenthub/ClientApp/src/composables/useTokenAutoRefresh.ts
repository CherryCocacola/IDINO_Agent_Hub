import { onMounted, onBeforeUnmount, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { safeGetAuthStorage } from '@/utils/storage'
import type { RefreshTokenResponseDto } from '@/types'

/**
 * 토큰 만료 임박 사전 갱신 composable.
 *
 * 트랙 #88 C2 (2026-05-13):
 *   사용자가 60분 시점에 첫 API 호출을 하기 전까지는 클라이언트가 만료 사실을 모른다.
 *   → 백엔드가 응답에 `tokenExpiresAt` (ISO 8601 UTC) 을 내려주면,
 *      만료 5분 전 자동으로 /auth/refresh 를 호출해 토큰을 회전한다.
 *   → 사용자는 무알림 강제 로그아웃을 경험하지 않는다.
 *
 * 동작:
 *   - 인증된 상태에서 onMounted 시 한 번 스케줄링
 *   - authStore.tokenExpiresAt 가 갱신되면(예: refresh 직후) 자동으로 재스케줄
 *   - 컴포넌트 unmount 시 timer 정리
 *
 * 사용 예 (MainLayout.vue):
 *   import { useTokenAutoRefresh } from '@/composables/useTokenAutoRefresh'
 *   useTokenAutoRefresh()
 */

// 만료 몇 분 전에 갱신할지. 너무 짧으면 네트워크 지연 사이에 만료될 수 있고,
// 너무 길면 같은 세션에서 불필요하게 자주 회전한다.
const REFRESH_LEAD_TIME_MS = 5 * 60 * 1000  // 5분
// setTimeout 의 최소 지연 — 음수/0 을 피하기 위함
const MIN_SCHEDULE_DELAY_MS = 1000
// 같은 인스턴스에서 동시에 여러 refresh 가 발사되지 않게 하는 가드
let isRefreshInFlight = false

export function useTokenAutoRefresh() {
  const authStore = useAuthStore()
  let timerId: ReturnType<typeof setTimeout> | null = null

  /**
   * 만료 5분 전 시점에 refresh 를 한 번 실행하도록 timer 예약.
   * tokenExpiresAt 이 없거나 이미 지난 경우엔 스킵 (인터셉터 401 흐름으로 처리).
   */
  function schedule() {
    clearTimer()

    if (!authStore.isAuthenticated) return
    const expiresAtRaw = authStore.tokenExpiresAt
    if (!expiresAtRaw) {
      // 백엔드가 만료 시각을 내려주지 않는 환경(레거시 응답 등). 사전 갱신 비활성.
      return
    }

    const expiresAtMs = new Date(expiresAtRaw).getTime()
    if (Number.isNaN(expiresAtMs)) {
      console.warn('[useTokenAutoRefresh] invalid tokenExpiresAt:', expiresAtRaw)
      return
    }

    const now = Date.now()
    const delay = Math.max(expiresAtMs - now - REFRESH_LEAD_TIME_MS, MIN_SCHEDULE_DELAY_MS)
    // 만료가 이미 지난 경우엔 인터셉터가 처리하도록 두고 우리는 호출하지 않는다
    if (expiresAtMs - now <= 0) {
      return
    }

    timerId = setTimeout(refreshNow, delay)
  }

  function clearTimer() {
    if (timerId !== null) {
      clearTimeout(timerId)
      timerId = null
    }
  }

  /**
   * 실제 refresh 호출.
   * - api.ts 인터셉터를 거치지 않기 위해 plain axios 사용 (401 시 인터셉터가 무한 루프에 빠지지 않도록).
   * - 성공 시 store.updateTokens 로 메모리 + 저장소 동시 갱신.
   * - 실패 시 인터셉터의 401 흐름에 맡긴다 (다음 API 호출에서 자연스럽게 처리).
   */
  async function refreshNow() {
    if (isRefreshInFlight) return
    isRefreshInFlight = true
    try {
      const refreshToken = safeGetAuthStorage('refreshToken')
      if (!refreshToken) return  // 토큰이 없으면 더 할 일 없음

      const response = await axios.post<RefreshTokenResponseDto>(
        '/api/auth/refresh',
        { refreshToken }
      )

      authStore.updateTokens({
        token: response.data.token,
        refreshToken: response.data.refreshToken ?? null,
        tokenExpiresAt: response.data.tokenExpiresAt ?? null,
        refreshTokenExpiresAt: response.data.refreshTokenExpiresAt ?? null
      })

      // 새 만료 시각으로 다음 스케줄 잡기는 watch 가 자동 처리 (아래)
    } catch (error) {
      console.warn('[useTokenAutoRefresh] preemptive refresh failed:', error)
      // 실패는 인터셉터에 맡긴다 — 다음 API 호출 시 401 → 안내 → /login
    } finally {
      isRefreshInFlight = false
    }
  }

  onMounted(() => {
    schedule()
  })

  // tokenExpiresAt 가 갱신되면(login / 사전 갱신 성공 / 401 흐름의 인터셉터 갱신) 즉시 재스케줄
  const stopWatch = watch(
    () => [authStore.tokenExpiresAt, authStore.isAuthenticated] as const,
    () => {
      schedule()
    }
  )

  onBeforeUnmount(() => {
    clearTimer()
    stopWatch()
  })
}
