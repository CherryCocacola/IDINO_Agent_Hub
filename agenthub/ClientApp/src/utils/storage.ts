/**
 * localStorage 안전하게 접근 (Tracking Prevention 방지)
 * 브라우저의 Enhanced Tracking Prevention이 localStorage 접근을 차단하는 경우를 대비
 */

export const safeGetLocalStorage = (key: string): string | null => {
  try {
    return localStorage.getItem(key)
  } catch (error) {
    // Tracking Prevention 또는 다른 이유로 localStorage 접근이 차단된 경우
    console.warn(`[storage] Failed to access localStorage for key "${key}":`, error)
    return null
  }
}

export const safeSetLocalStorage = (key: string, value: string): boolean => {
  try {
    localStorage.setItem(key, value)
    return true
  } catch (error) {
    // Tracking Prevention 또는 스토리지 용량 초과 등의 이유로 실패한 경우
    console.warn(`[storage] Failed to set localStorage for key "${key}":`, error)
    return false
  }
}

export const safeRemoveLocalStorage = (key: string): boolean => {
  try {
    localStorage.removeItem(key)
    return true
  } catch (error) {
    console.warn(`[storage] Failed to remove localStorage for key "${key}":`, error)
    return false
  }
}

export const safeClearLocalStorage = (): boolean => {
  try {
    localStorage.clear()
    return true
  } catch (error) {
    console.warn('[storage] Failed to clear localStorage:', error)
    return false
  }
}
