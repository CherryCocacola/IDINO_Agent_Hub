import axios, { type AxiosInstance } from 'axios'
import { safeGetLocalStorage, safeSetLocalStorage, safeRemoveLocalStorage } from '@/utils/storage'

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = safeGetLocalStorage('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
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
      // 로그인 요청 자체의 401은 인터셉터에서 처리하지 않음
      const requestUrl = error.config?.url || ''
      if (requestUrl.includes('/auth/login')) {
        return Promise.reject(error)
      }

      // Token expired, try to refresh
      const refreshToken = safeGetLocalStorage('refreshToken')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', { refreshToken }, {
            baseURL: '/api'
          })
          const newToken = response.data.token
          safeSetLocalStorage('token', newToken)
          error.config.headers.Authorization = `Bearer ${newToken}`
          return api.request(error.config)
        } catch (refreshError) {
          // Refresh failed, logout
          safeRemoveLocalStorage('token')
          safeRemoveLocalStorage('refreshToken')
          window.location.href = '/login'
        }
      } else {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
