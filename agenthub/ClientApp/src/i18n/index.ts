import { createI18n } from 'vue-i18n'
import ko from './locales/ko.json'
import en from './locales/en.json'
import vi from './locales/vi.json'
import { safeGetLocalStorage } from '@/utils/storage'

// 지원 언어 목록 — Settings UI / MainLayout 토글 / 검증 로직이 동일 소스를 사용하도록 export.
// 트랙 #97-pre2-2 (2026-05-15): 베트남어(vi) 추가. R5 한국어 우선 유지.
export const SUPPORTED_LOCALES = ['ko', 'en', 'vi'] as const
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number]

export const isSupportedLocale = (value: string | null | undefined): value is SupportedLocale => {
  return !!value && (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

// 초기 표시 언어 결정.
// 트랙 #97-pre2-1 (2026-05-14) — R5 한국어 우선. 트랙 #97-pre2-2 (2026-05-15) — vi 추가.
//
// 사용자 보고: "메뉴명이 영문이다가 SETTINGS 진입 후에야 한글로 변경되는 결함이 잔존".
// Root cause: 과거 사용자가 영문 토글했던 localStorage 잔존값('en') 때문에 ko 우선 정책이
//   무력화됨. Settings.vue 의 loadPreferences() 가 DB(/userpreferences) 에서 language=ko 를
//   가져와 locale.value 를 ko 로 덮어쓰기 때문에 "Settings 진입 시 갑자기 한글" 현상.
//
// 부분 해소책: localStorage 우선순위는 유지하되, 운영자 정책이 ko 인 사용자가 다른 브라우저로
//   처음 진입하면 ko 가 즉시 보이도록 보장. DB 우선 동기화는 Settings.vue 와 MainLayout.vue
//   양쪽 onMounted 에서 호출 (이 파일과 별개로 적용).
//
// 우선순위: ① localStorage 저장값(ko/en/vi 만 인정) → ② 브라우저 언어 감지 → ③ 'ko'
const getDefaultLocale = (): SupportedLocale => {
  try {
    const saved = safeGetLocalStorage('i18n_locale')
    if (isSupportedLocale(saved)) {
      return saved
    }
  } catch (error) {
    console.warn('[i18n] Failed to get locale from localStorage:', error)
  }

  // 브라우저 언어 감지 — 베트남어/영어 사용자는 명시적으로 해당 언어 사용 의도가 있다고 봄.
  // 그 외 모든 언어는 R5 한국어 우선으로 ko 로 폴백.
  try {
    const browserLang = (navigator.language || (navigator as { userLanguage?: string }).userLanguage || '').toLowerCase()
    if (browserLang.startsWith('vi')) {
      return 'vi'
    }
    if (browserLang.startsWith('en')) {
      return 'en'
    }
  } catch (error) {
    console.warn('[i18n] Failed to detect browser language:', error)
  }

  // R5: 한국어가 시스템 기본.
  return 'ko'
}

const i18n = createI18n({
  legacy: false, // Composition API 사용
  locale: getDefaultLocale(),
  fallbackLocale: 'ko', // R5 한국어 우선
  // 누락 키 경고 억제 — vi/en 에 일부 키가 누락되어도 ko 로 자동 폴백.
  missingWarn: false,
  fallbackWarn: false,
  messages: {
    ko,
    en,
    vi
  }
})

export default i18n
