/**
 * 브라우저 스토리지 안전 접근 헬퍼.
 *
 * 두 가지 저장소를 다룬다:
 *  - localStorage : 브라우저를 닫아도 유지 (영구). "자동 로그인 유지" 체크 시 사용.
 *  - sessionStorage : 탭/창을 닫으면 삭제 (휘발). 기본 로그인 시 사용.
 *
 * Edge/Brave 등의 Tracking Prevention 으로 스토리지 접근이 차단되거나,
 * 시크릿 모드에서 quota 가 0 인 경우를 대비해 모든 호출을 try/catch 로 감싼다.
 */

// ============================================================================
// localStorage (영구 보관)
// ============================================================================

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

// ============================================================================
// sessionStorage (탭 종료 시 자동 삭제) — 트랙 #88 C2 (2026-05-13)
// ============================================================================

export const safeGetSessionStorage = (key: string): string | null => {
  try {
    return sessionStorage.getItem(key)
  } catch (error) {
    console.warn(`[storage] Failed to access sessionStorage for key "${key}":`, error)
    return null
  }
}

export const safeSetSessionStorage = (key: string, value: string): boolean => {
  try {
    sessionStorage.setItem(key, value)
    return true
  } catch (error) {
    console.warn(`[storage] Failed to set sessionStorage for key "${key}":`, error)
    return false
  }
}

export const safeRemoveSessionStorage = (key: string): boolean => {
  try {
    sessionStorage.removeItem(key)
    return true
  } catch (error) {
    console.warn(`[storage] Failed to remove sessionStorage for key "${key}":`, error)
    return false
  }
}

// ============================================================================
// 통합 헬퍼 — local 과 session 양쪽을 한 번에 조회/삭제 — 트랙 #88 C2
// ============================================================================

/**
 * 토큰 등 인증 정보 조회 시 local → session 순으로 탐색.
 * "자동 로그인 유지" 사용자는 localStorage 에, 일반 로그인은 sessionStorage 에 저장하므로
 * 어느 저장소에 있든 동일하게 읽어올 수 있게 한다.
 */
export const safeGetAuthStorage = (key: string): string | null => {
  const fromLocal = safeGetLocalStorage(key)
  if (fromLocal) return fromLocal
  return safeGetSessionStorage(key)
}

/**
 * 로그아웃 / 세션 만료 시 두 저장소 모두 정리.
 * 사용자가 "자동 로그인 유지"를 켰다 껐다 한 흔적이 남아도 안전하게 청소된다.
 */
export const safeRemoveAuthStorage = (key: string): void => {
  safeRemoveLocalStorage(key)
  safeRemoveSessionStorage(key)
}

/**
 * 영구(persistent=true)/휘발(persistent=false) 분기 저장.
 * 같은 키가 반대편 저장소에 남아 있으면 오해를 일으키므로 반드시 삭제 후 저장한다.
 */
export const safeSetAuthStorage = (key: string, value: string, persistent: boolean): boolean => {
  if (persistent) {
    safeRemoveSessionStorage(key)
    return safeSetLocalStorage(key, value)
  } else {
    safeRemoveLocalStorage(key)
    return safeSetSessionStorage(key, value)
  }
}
