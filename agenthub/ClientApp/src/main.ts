import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './assets/utilities.css'

// 트랙 #149 (2026-06-01) P1 — 다크모드 정식 구현. 앱 부팅 시점에 저장된 theme
// (localStorage 또는 preferences) 를 즉시 <html data-bs-theme> 에 반영. auto 면
// prefers-color-scheme 따라가고 시스템 변경 시 동기화. Settings.vue 의 handleThemeChange
// 와 동일한 동작.
function bootstrapTheme() {
  try {
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | 'auto' | null
    const theme = saved ?? 'light'
    const apply = (t: 'light' | 'dark' | 'auto') => {
      let effective: 'light' | 'dark' = t as 'light' | 'dark'
      if (t === 'auto') {
        effective = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      }
      document.documentElement.setAttribute('data-bs-theme', effective)
    }
    apply(theme)
    if (theme === 'auto' && window.matchMedia) {
      const mql = window.matchMedia('(prefers-color-scheme: dark)')
      const onChange = () => apply('auto')
      if (mql.addEventListener) mql.addEventListener('change', onChange)
      else mql.addListener(onChange)
    }
  } catch {
    // 로컬스토리지 차단 환경 — 라이트 기본 유지
    document.documentElement.setAttribute('data-bs-theme', 'light')
  }
}
bootstrapTheme()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(i18n)

app.mount('#app')
