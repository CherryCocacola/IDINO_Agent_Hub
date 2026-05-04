import { createI18n } from 'vue-i18n'
import ko from './locales/ko.json'
import en from './locales/en.json'
import { safeGetLocalStorage } from '@/utils/storage'

// 브라우저 언어 감지 또는 localStorage에서 가져오기
const getDefaultLocale = (): string => {
  try {
    const saved = safeGetLocalStorage('i18n_locale')
    if (saved && (saved === 'ko' || saved === 'en')) {
      return saved
    }
  } catch (error) {
    console.warn('[i18n] Failed to get locale from localStorage:', error)
  }
  
  // 브라우저 언어 감지
  try {
    const browserLang = navigator.language || (navigator as any).userLanguage
    if (browserLang && browserLang.startsWith('ko')) {
      return 'ko'
    }
  } catch (error) {
    console.warn('[i18n] Failed to detect browser language:', error)
  }
  
  return 'en'
}

const i18n = createI18n({
  legacy: false, // Composition API 사용
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: {
    ko,
    en
  }
})

export default i18n
