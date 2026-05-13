<template>
  <div class="page-content-wrap">
    <div class="page-header mb-4">
      <div>
        <h1 class="page-heading">설정</h1>
        <p class="page-desc">프로필, 환경 설정, 보안을 관리합니다</p>
      </div>
    </div>
    <div class="row">
      <!-- 좌측 사이드바 -->
      <div class="col-lg-3 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-white">
            <h5 class="card-title mb-0"><i class="bi bi-gear me-1"></i>설정</h5>
          </div>
          <div class="list-group list-group-flush">
            <a
              href="#"
              class="list-group-item list-group-item-action"
              :class="{ active: activeTab === 'profile' }"
              @click.prevent="activeTab = 'profile'"
            >
              <i class="bi bi-person"></i> 프로필
            </a>
            <a
              href="#"
              class="list-group-item list-group-item-action"
              :class="{ active: activeTab === 'preferences' }"
              @click.prevent="activeTab = 'preferences'"
            >
              <i class="bi bi-sliders"></i> 환경 설정
            </a>
            <a
              href="#"
              class="list-group-item list-group-item-action"
              :class="{ active: activeTab === 'security' }"
              @click.prevent="activeTab = 'security'"
            >
              <i class="bi bi-shield-check"></i> 보안
            </a>
          </div>
        </div>
      </div>

      <!-- 메인 설정 영역 -->
      <div class="col-lg-9">
        <!-- 프로필 설정 -->
        <div v-if="activeTab === 'profile'" class="settings-tab">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-white">
              <div>
                <h5 class="card-title mb-0"><i class="bi bi-person me-1"></i>프로필 정보</h5>
                <p class="card-subtitle mb-0">계정 기본 정보</p>
              </div>
            </div>
            <div class="card-body">
              <!-- 트랙 #88 H7 (2026-05-13): 인라인 상태 메시지 — alert() 대체 -->
              <div v-if="profileStatus.show" class="alert" :class="`alert-${profileStatus.type}`">
                <i class="bi" :class="profileStatus.type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'"></i>
                {{ profileStatus.message }}
              </div>

              <div v-if="profileLoading" class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                  <span class="visually-hidden">불러오는 중...</span>
                </div>
                <p class="text-muted mt-2 mb-0">프로필 정보를 불러오는 중입니다...</p>
              </div>

              <div v-else class="row mb-4">
                <div class="col-md-3 text-center">
                  <div class="avatar-large mb-3">
                    <i class="bi bi-person-circle" style="font-size: 4rem;"></i>
                  </div>
                  <button type="button" class="btn btn-sm btn-outline-primary" disabled>
                    사진 변경
                  </button>
                  <small class="text-muted d-block mt-2">준비 중</small>
                </div>
                <div class="col-md-9">
                  <form @submit.prevent="handleUpdateProfile">
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label class="form-label">이름 <span class="text-danger">*</span></label>
                        <input
                          type="text"
                          class="form-control"
                          v-model="profile.fullName"
                          required
                          :disabled="profileSaving"
                          maxlength="100"
                        >
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">이메일</label>
                        <input
                          type="email"
                          class="form-control"
                          v-model="profile.email"
                          readonly
                        >
                        <small class="text-muted">이메일은 변경할 수 없습니다</small>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label class="form-label">전화번호</label>
                        <input
                          type="tel"
                          class="form-control"
                          v-model="profile.phoneNumber"
                          :disabled="profileSaving"
                          maxlength="20"
                          placeholder="010-1234-5678"
                        >
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">부서</label>
                        <input
                          type="text"
                          class="form-control"
                          v-model="profile.department"
                          :disabled="profileSaving"
                          maxlength="100"
                        >
                      </div>
                    </div>
                    <div class="mb-3">
                      <label class="form-label">자기소개</label>
                      <textarea
                        class="form-control"
                        rows="3"
                        v-model="profile.bio"
                        :disabled="profileSaving"
                        maxlength="500"
                      ></textarea>
                      <small class="text-muted">{{ (profile.bio || '').length }} / 500</small>
                    </div>
                    <div class="text-end">
                      <button
                        type="submit"
                        class="btn btn-primary"
                        :disabled="profileSaving || !profile.fullName"
                      >
                        <span
                          v-if="profileSaving"
                          class="spinner-border spinner-border-sm me-1"
                          role="status"
                          aria-hidden="true"
                        ></span>
                        <i v-else class="bi bi-check-lg"></i>
                        {{ profileSaving ? '저장 중...' : '저장' }}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 환경 설정 -->
        <div v-if="activeTab === 'preferences'" class="settings-tab">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-white">
              <div>
                <h5 class="card-title mb-0"><i class="bi bi-sliders me-1"></i>환경 설정</h5>
                <p class="card-subtitle mb-0">언어, 테마 등</p>
              </div>
            </div>
            <div class="card-body">
              <!-- 트랙 #88 H7 (2026-05-13): 인라인 상태 메시지 -->
              <div v-if="preferencesStatus.show" class="alert" :class="`alert-${preferencesStatus.type}`">
                <i class="bi" :class="preferencesStatus.type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'"></i>
                {{ preferencesStatus.message }}
              </div>

              <form @submit.prevent="handleSavePreferences">
                <div class="mb-3">
                  <label class="form-label">언어</label>
                  <select
                    class="form-select"
                    v-model="preferences.language"
                    @change="handleLanguageChange"
                    :disabled="preferencesSaving"
                  >
                    <option value="ko">한국어</option>
                    <option value="en">English</option>
                  </select>
                  <small class="text-muted">언어 변경은 즉시 적용됩니다</small>
                </div>
                <div class="mb-3">
                  <label class="form-label">시간대</label>
                  <select
                    class="form-select"
                    v-model="preferences.timezone"
                    :disabled="preferencesSaving"
                  >
                    <option value="Asia/Seoul">Asia/Seoul (KST)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>
                <div class="mb-3">
                  <label class="form-label">테마</label>
                  <select
                    class="form-select"
                    v-model="preferences.theme"
                    :disabled="preferencesSaving"
                  >
                    <option value="light">라이트</option>
                    <option value="dark">다크</option>
                    <option value="auto">시스템 설정</option>
                  </select>
                </div>
                <div class="text-end">
                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="preferencesSaving"
                  >
                    <span
                      v-if="preferencesSaving"
                      class="spinner-border spinner-border-sm me-1"
                      role="status"
                      aria-hidden="true"
                    ></span>
                    <i v-else class="bi bi-check-lg"></i>
                    {{ preferencesSaving ? '저장 중...' : '저장' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <!-- 보안 설정 -->
        <div v-if="activeTab === 'security'" class="settings-tab">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-white">
              <div>
                <h5 class="card-title mb-0"><i class="bi bi-shield-check me-1"></i>보안</h5>
                <p class="card-subtitle mb-0">비밀번호 변경</p>
              </div>
            </div>
            <div class="card-body">
              <!-- 트랙 #88 H7 (2026-05-13): 인라인 상태 메시지 -->
              <div v-if="securityStatus.show" class="alert" :class="`alert-${securityStatus.type}`">
                <i class="bi" :class="securityStatus.type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle'"></i>
                {{ securityStatus.message }}
              </div>

              <form @submit.prevent="handleChangePassword">
                <div class="mb-3">
                  <label class="form-label">현재 비밀번호 <span class="text-danger">*</span></label>
                  <input
                    type="password"
                    class="form-control"
                    v-model="passwordForm.currentPassword"
                    required
                    :disabled="passwordSaving"
                    autocomplete="current-password"
                  >
                </div>
                <div class="mb-3">
                  <label class="form-label">새 비밀번호 <span class="text-danger">*</span></label>
                  <input
                    type="password"
                    class="form-control"
                    v-model="passwordForm.newPassword"
                    required
                    :disabled="passwordSaving"
                    minlength="8"
                    autocomplete="new-password"
                  >
                  <small class="text-muted">최소 8자 이상이어야 합니다</small>
                </div>
                <div class="mb-3">
                  <label class="form-label">비밀번호 확인 <span class="text-danger">*</span></label>
                  <input
                    type="password"
                    class="form-control"
                    v-model="passwordForm.confirmPassword"
                    required
                    :disabled="passwordSaving"
                    minlength="8"
                    autocomplete="new-password"
                  >
                  <small
                    v-if="passwordForm.newPassword && passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword"
                    class="text-danger"
                  >
                    새 비밀번호와 일치하지 않습니다
                  </small>
                </div>
                <div class="text-end">
                  <button
                    type="submit"
                    class="btn btn-primary"
                    :disabled="passwordSaving || !canChangePassword"
                  >
                    <span
                      v-if="passwordSaving"
                      class="spinner-border spinner-border-sm me-1"
                      role="status"
                      aria-hidden="true"
                    ></span>
                    <i v-else class="bi bi-check-lg"></i>
                    {{ passwordSaving ? '변경 중...' : '변경' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import type { UserDto, UserPreferenceDto } from '@/types'
import { safeGetLocalStorage, safeSetLocalStorage } from '@/utils/storage'

/**
 * 설정 화면.
 *
 * 트랙 #88 H7 (2026-05-13): 프로필/환경설정/보안 3개 탭 모두 안정화.
 *
 * 주요 개선:
 *  1) 저장 버튼에 로딩 스피너 + disable — 사용자가 클릭이 먹혔는지 즉시 확인 가능
 *  2) blocking alert() 제거 → 카드 상단 인라인 alert 패널 — UX 흐름 끊지 않음
 *  3) 프로필 로드 시 authStore.user 메모리 캐시 의존 제거 → 항상 /users/me 로 최신화
 *     (페이지 직접 진입 시 authStore.user 미로드 가능 — userId 누락으로 저장 실패하던 결함 해소)
 *  4) 비밀번호 변경 클라이언트 검증 — 일치 / 최소 8자 / 현재 비밀번호 필수
 *  5) 환경설정 POST 응답 실패 시에도 localStorage / i18n 적용은 진행 (오프라인 폴백)
 */

const authStore = useAuthStore()
const { locale } = useI18n()
const activeTab = ref<'profile' | 'preferences' | 'security'>('profile')

// 인라인 상태 메시지 — { show, type: 'success'|'danger', message }
interface StatusMessage {
  show: boolean
  type: 'success' | 'danger'
  message: string
}
const profileStatus = ref<StatusMessage>({ show: false, type: 'success', message: '' })
const preferencesStatus = ref<StatusMessage>({ show: false, type: 'success', message: '' })
const securityStatus = ref<StatusMessage>({ show: false, type: 'success', message: '' })

// 각 폼별 저장 진행 상태
const profileLoading = ref(false)
const profileSaving = ref(false)
const preferencesSaving = ref(false)
const passwordSaving = ref(false)

const profile = ref({
  userId: 0,
  fullName: '',
  email: '',
  phoneNumber: '',
  department: '',
  bio: ''
})

const preferences = ref({
  language: 'ko' as 'ko' | 'en',
  timezone: 'Asia/Seoul',
  theme: 'light' as 'light' | 'dark' | 'auto'
})

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const canChangePassword = computed(() => {
  return (
    passwordForm.value.currentPassword.length > 0 &&
    passwordForm.value.newPassword.length >= 8 &&
    passwordForm.value.newPassword === passwordForm.value.confirmPassword
  )
})

/** 일정 시간 후 상태 메시지 자동 닫힘 (성공 시에만) */
function setStatus(target: StatusMessage, type: 'success' | 'danger', message: string) {
  target.show = true
  target.type = type
  target.message = message
  if (type === 'success') {
    setTimeout(() => {
      target.show = false
    }, 3000)
  }
}

/**
 * 프로필 로드 — 항상 /users/me 로부터 최신 데이터.
 *
 * 트랙 #88 H7 (2026-05-13): authStore.user 가 null 일 때 저장이 실패하던 결함 해소.
 * 페이지 새로고침 / 직접 진입 시 authStore.user 가 미로드인 경우가 있어
 * userId 를 안전하게 확보하기 위해 매번 백엔드를 신뢰한다.
 */
const loadProfile = async () => {
  profileLoading.value = true
  try {
    const response = await api.get<UserDto>('/users/me')
    if (response.data) {
      profile.value = {
        userId: response.data.userId,
        fullName: response.data.fullName || '',
        email: response.data.email || '',
        phoneNumber: response.data.phoneNumber || '',
        department: response.data.department || '',
        bio: response.data.bio || ''
      }
    }
  } catch (error) {
    console.error('Error loading profile:', error)
    // authStore 메모리 캐시 폴백
    if (authStore.user) {
      profile.value = {
        userId: authStore.user.userId,
        fullName: authStore.user.fullName || '',
        email: authStore.user.email || '',
        phoneNumber: authStore.user.phoneNumber || '',
        department: authStore.user.department || '',
        bio: authStore.user.bio || ''
      }
    } else {
      setStatus(profileStatus.value, 'danger', '프로필 정보를 불러올 수 없습니다. 다시 로그인해 주세요.')
    }
  } finally {
    profileLoading.value = false
  }
}

const handleUpdateProfile = async () => {
  if (!profile.value.userId) {
    setStatus(profileStatus.value, 'danger', '사용자 정보를 확인할 수 없습니다. 페이지를 새로고침 후 다시 시도해 주세요.')
    return
  }
  if (!profile.value.fullName) {
    setStatus(profileStatus.value, 'danger', '이름을 입력해 주세요.')
    return
  }

  profileSaving.value = true
  try {
    await api.put(`/users/${profile.value.userId}`, {
      fullName: profile.value.fullName,
      phoneNumber: profile.value.phoneNumber,
      department: profile.value.department,
      bio: profile.value.bio
    })
    // authStore 의 user 도 함께 갱신 — 헤더 등 다른 화면에 반영
    await authStore.loadUser()
    setStatus(profileStatus.value, 'success', '프로필이 업데이트되었습니다.')
  } catch (error: unknown) {
    const e = error as { response?: { data?: { message?: string } }; message?: string }
    console.error('Error updating profile:', error)
    setStatus(
      profileStatus.value,
      'danger',
      e.response?.data?.message || e.message || '프로필 업데이트 중 오류가 발생했습니다.'
    )
  } finally {
    profileSaving.value = false
  }
}

const loadPreferences = async () => {
  try {
    const response = await api.get<UserPreferenceDto[]>('/userpreferences')
    const prefs = response.data || []

    // 데이터베이스에서 가져온 설정으로 preferences 초기화
    prefs.forEach((pref) => {
      if (pref.preferenceKey === 'language') {
        preferences.value.language = (pref.preferenceValue as 'ko' | 'en') || 'ko'
      } else if (pref.preferenceKey === 'timezone') {
        preferences.value.timezone = pref.preferenceValue || 'Asia/Seoul'
      } else if (pref.preferenceKey === 'theme') {
        preferences.value.theme = (pref.preferenceValue as 'light' | 'dark' | 'auto') || 'light'
      }
    })

    // localStorage 폴백 (DB 에 미저장된 키만 적용)
    const saved = safeGetLocalStorage('preferences')
    if (saved) {
      try {
        const localPrefs = JSON.parse(saved)
        if (!prefs.find((p) => p.preferenceKey === 'language')) {
          preferences.value.language = localPrefs.language || preferences.value.language
        }
        if (!prefs.find((p) => p.preferenceKey === 'timezone')) {
          preferences.value.timezone = localPrefs.timezone || preferences.value.timezone
        }
        if (!prefs.find((p) => p.preferenceKey === 'theme')) {
          preferences.value.theme = localPrefs.theme || preferences.value.theme
        }
      } catch (parseError) {
        console.error('Error parsing localStorage preferences:', parseError)
      }
    }

    // 언어 설정 적용 (localStorage 의 i18n_locale 이 우선)
    const savedLocale = safeGetLocalStorage('i18n_locale')
    if (savedLocale && (savedLocale === 'ko' || savedLocale === 'en')) {
      preferences.value.language = savedLocale
    }
    locale.value = preferences.value.language
  } catch (error) {
    console.error('Error loading preferences:', error)
    // 오프라인 폴백 — localStorage 만으로 동작
    const saved = safeGetLocalStorage('preferences')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        preferences.value = {
          language: parsed.language || 'ko',
          timezone: parsed.timezone || 'Asia/Seoul',
          theme: parsed.theme || 'light'
        }
      } catch (e) {
        console.error('Error parsing preferences:', e)
      }
    }
    const savedLocale = safeGetLocalStorage('i18n_locale')
    if (savedLocale && (savedLocale === 'ko' || savedLocale === 'en')) {
      preferences.value.language = savedLocale
      locale.value = savedLocale
    }
  }
}

const handleLanguageChange = () => {
  locale.value = preferences.value.language
  safeSetLocalStorage('i18n_locale', preferences.value.language)
}

const handleSavePreferences = async () => {
  preferencesSaving.value = true
  try {
    // 언어 설정은 항상 즉시 적용 (DB 저장 실패와 무관)
    handleLanguageChange()

    // UserPreferences API 에 저장 — POST upsert 동작 (기존 키 있으면 갱신)
    const preferenceKeys: Array<keyof typeof preferences.value> = ['language', 'timezone', 'theme']
    const savePromises = preferenceKeys.map((key) => {
      const value = preferences.value[key]
      return api.post('/userpreferences', {
        preferenceKey: key,
        preferenceValue: String(value),
        dataType: 'String',
        category: 'UI'
      })
    })

    await Promise.all(savePromises)

    // localStorage 폴백 동기화
    safeSetLocalStorage('preferences', JSON.stringify(preferences.value))

    setStatus(preferencesStatus.value, 'success', '환경 설정이 저장되었습니다.')
  } catch (error: unknown) {
    const e = error as { response?: { data?: { message?: string } }; message?: string }
    console.error('Error saving preferences:', error)
    setStatus(
      preferencesStatus.value,
      'danger',
      e.response?.data?.message || e.message || '환경 설정 저장 중 오류가 발생했습니다.'
    )
  } finally {
    preferencesSaving.value = false
  }
}

const handleChangePassword = async () => {
  // 클라이언트 측 사전 검증 — 백엔드 호출 전 명확한 안내
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    setStatus(securityStatus.value, 'danger', '새 비밀번호와 비밀번호 확인이 일치하지 않습니다.')
    return
  }
  if (passwordForm.value.newPassword.length < 8) {
    setStatus(securityStatus.value, 'danger', '새 비밀번호는 최소 8자 이상이어야 합니다.')
    return
  }
  if (!profile.value.userId) {
    setStatus(securityStatus.value, 'danger', '사용자 정보를 확인할 수 없습니다. 페이지를 새로고침 후 다시 시도해 주세요.')
    return
  }

  passwordSaving.value = true
  try {
    // UpdateUserRequestDto: currentPassword + password 두 필드만 전송
    // (FullName 등 다른 필드를 보내면 그 값으로 덮어쓰기 됨 — null 로 두면 기존 유지)
    await api.put(`/users/${profile.value.userId}`, {
      currentPassword: passwordForm.value.currentPassword,
      password: passwordForm.value.newPassword
    })
    setStatus(securityStatus.value, 'success', '비밀번호가 변경되었습니다.')
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error: unknown) {
    const e = error as { response?: { data?: { message?: string } }; message?: string }
    console.error('Error changing password:', error)
    setStatus(
      securityStatus.value,
      'danger',
      e.response?.data?.message || e.message || '비밀번호 변경 중 오류가 발생했습니다.'
    )
  } finally {
    passwordSaving.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadPreferences()
})
</script>

<style scoped>
.avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
</style>
