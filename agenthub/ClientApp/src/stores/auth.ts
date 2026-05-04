import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { UserDto, LoginRequestDto, LoginResponseDto } from '@/types'
import { safeGetLocalStorage, safeSetLocalStorage, safeRemoveLocalStorage } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(safeGetLocalStorage('token'))
  const refreshToken = ref<string | null>(safeGetLocalStorage('refreshToken'))
  const user = ref<UserDto | null>(null)
  const isAuthenticated = ref<boolean>(!!token.value)

  async function login(credentials: LoginRequestDto) {
    try {
      console.log('[authStore] Attempting login for:', credentials.email)
      const response = await api.post<LoginResponseDto>('/auth/login', credentials)
      
      console.log('[authStore] Login response received:', {
        hasToken: !!response.data.token,
        tokenLength: response.data.token?.length,
        hasRefreshToken: !!response.data.refreshToken,
        hasUser: !!response.data.user
      })
      
      if (!response.data.token) {
        console.error('[authStore] No token in response:', response.data)
        throw new Error('로그인 응답에 토큰이 없습니다.')
      }
      
      token.value = response.data.token
      refreshToken.value = response.data.refreshToken || null
      user.value = response.data.user
      isAuthenticated.value = true

      // localStorage에 토큰 저장 (Tracking Prevention 방지)
      const tokenSaved = safeSetLocalStorage('token', token.value)
      const refreshTokenSaved = safeSetLocalStorage('refreshToken', refreshToken.value ?? '')
      
      if (!tokenSaved || !refreshTokenSaved) {
        console.warn('[authStore] Failed to save tokens to localStorage, but login succeeded')
        // localStorage 저장 실패해도 메모리에 저장되어 있으므로 계속 진행
      } else {
        console.log('[authStore] Tokens saved to localStorage successfully')
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

      safeRemoveLocalStorage('token')
      safeRemoveLocalStorage('refreshToken')
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
    login,
    logout,
    loadUser
  }
})
