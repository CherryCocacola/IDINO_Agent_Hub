import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { UserDto, LoginRequestDto, LoginResponseDto } from '@/types'
import {
  safeGetAuthStorage,
  safeSetAuthStorage,
  safeRemoveAuthStorage,
  safeGetLocalStorage
} from '@/utils/storage'

/**
 * 인증 스토어.
 *
 * 트랙 #88 C2 (2026-05-13) — "자동 로그인 유지" 분기:
 *   - rememberMe = true  → localStorage 사용 (브라우저 재시작 후에도 유지)
 *   - rememberMe = false → sessionStorage 사용 (탭/창 닫으면 사라짐)
 * 초기 로드 시 양쪽 저장소를 모두 살펴 토큰을 찾는다.
 */
export const useAuthStore = defineStore('auth', () => {
  // 초기 로드: local → session 순으로 탐색
  const token = ref<string | null>(safeGetAuthStorage('token'))
  const refreshToken = ref<string | null>(safeGetAuthStorage('refreshToken'))
  const user = ref<UserDto | null>(null)
  const isAuthenticated = ref<boolean>(!!token.value)

  // 현재 세션의 영구 보관 여부 — 초기엔 "localStorage 에 토큰이 있느냐"로 판단.
  // 이후 login() 호출 시 사용자 선택으로 갱신된다.
  const rememberMe = ref<boolean>(!!safeGetLocalStorage('token'))

  // 트랙 #88 C2: 토큰 만료 임박 사전 갱신 composable 이 참조할 만료 시각 (ISO 8601 UTC).
  // 백엔드가 응답에 포함시키지 않으면 null — 이 경우 사전 갱신은 비활성.
  const tokenExpiresAt = ref<string | null>(null)
  const refreshTokenExpiresAt = ref<string | null>(null)

  /**
   * 로그인.
   * @param credentials 이메일/비밀번호
   * @param persistent  "로그인 상태 유지" 체크 여부. true 면 localStorage, false 면 sessionStorage.
   */
  async function login(credentials: LoginRequestDto, persistent: boolean = false) {
    try {
      console.log('[authStore] Attempting login for:', credentials.email, '(persistent =', persistent, ')')
      const response = await api.post<LoginResponseDto>('/auth/login', credentials)

      console.log('[authStore] Login response received:', {
        hasToken: !!response.data.token,
        tokenLength: response.data.token?.length,
        hasRefreshToken: !!response.data.refreshToken,
        hasUser: !!response.data.user,
        hasTokenExpiresAt: !!response.data.tokenExpiresAt
      })

      if (!response.data.token) {
        console.error('[authStore] No token in response:', response.data)
        throw new Error('로그인 응답에 토큰이 없습니다.')
      }

      // 메모리 상태 갱신
      token.value = response.data.token
      refreshToken.value = response.data.refreshToken || null
      user.value = response.data.user
      isAuthenticated.value = true
      rememberMe.value = persistent
      tokenExpiresAt.value = response.data.tokenExpiresAt ?? null
      refreshTokenExpiresAt.value = response.data.refreshTokenExpiresAt ?? null

      // 저장소에 영구/휘발 분기 저장 (Tracking Prevention 환경에서도 메모리는 살아 있으므로 실패해도 진행)
      const tokenSaved = safeSetAuthStorage('token', token.value, persistent)
      const refreshTokenSaved = safeSetAuthStorage('refreshToken', refreshToken.value ?? '', persistent)

      if (!tokenSaved || !refreshTokenSaved) {
        console.warn('[authStore] Failed to save tokens to storage, but login succeeded')
      } else {
        console.log(
          '[authStore] Tokens saved to',
          persistent ? 'localStorage (persistent)' : 'sessionStorage (per-tab)'
        )
      }

      return response.data
    } catch (error: any) {
      console.error('[authStore] Login error:', error)
      console.error('[authStore] Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText
      })
      throw error
    }
  }

  async function logout() {
    try {
      if (refreshToken.value) {
        await api.post('/auth/logout', { refreshToken: refreshToken.value })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      token.value = null
      refreshToken.value = null
      user.value = null
      isAuthenticated.value = false
      tokenExpiresAt.value = null
      refreshTokenExpiresAt.value = null

      // 두 저장소 모두 청소 — 사용자가 과거에 어느 모드로 로그인했든 안전하게 제거
      safeRemoveAuthStorage('token')
      safeRemoveAuthStorage('refreshToken')
    }
  }

  /**
   * 인터셉터 / composable 에서 외부 갱신된 토큰을 store 에 반영할 때 사용.
   * 현재 rememberMe 모드를 그대로 유지하면서 같은 저장소(local/session)에 덮어쓴다.
   */
  function updateTokens(payload: {
    token: string
    refreshToken?: string | null
    tokenExpiresAt?: string | null
    refreshTokenExpiresAt?: string | null
  }) {
    token.value = payload.token
    safeSetAuthStorage('token', payload.token, rememberMe.value)

    if (payload.refreshToken !== undefined && payload.refreshToken !== null) {
      refreshToken.value = payload.refreshToken
      safeSetAuthStorage('refreshToken', payload.refreshToken, rememberMe.value)
    }
    if (payload.tokenExpiresAt !== undefined) {
      tokenExpiresAt.value = payload.tokenExpiresAt ?? null
    }
    if (payload.refreshTokenExpiresAt !== undefined) {
      refreshTokenExpiresAt.value = payload.refreshTokenExpiresAt ?? null
    }
  }

  async function loadUser() {
    try {
      const response = await api.get<UserDto>('/users/me')
      if (response.data) {
        user.value = response.data
      } else {
        console.error('User data is null or undefined')
        user.value = null
        await logout()
      }
    } catch (error) {
      console.error('Load user error:', error)
      user.value = null
      await logout()
    }
  }

  return {
    token,
    refreshToken,
    user,
    isAuthenticated,
    rememberMe,
    tokenExpiresAt,
    refreshTokenExpiresAt,
    login,
    logout,
    loadUser,
    updateTokens
  }
})
