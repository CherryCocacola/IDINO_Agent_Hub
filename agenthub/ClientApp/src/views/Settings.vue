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
              <div class="row mb-4">
                <div class="col-md-3 text-center">
                  <div class="avatar-large mb-3">
                    <i class="bi bi-person-circle" style="font-size: 4rem;"></i>
                  </div>
                  <button class="btn btn-sm btn-outline-primary">사진 변경</button>
                </div>
                <div class="col-md-9">
                  <form @submit.prevent="handleUpdateProfile">
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label class="form-label">이름</label>
                        <input type="text" class="form-control" v-model="profile.fullName" required>
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">이메일</label>
                        <input type="email" class="form-control" v-model="profile.email" readonly>
                      </div>
                    </div>
                    <div class="row">
                      <div class="col-md-6 mb-3">
                        <label class="form-label">전화번호</label>
                        <input type="tel" class="form-control" v-model="profile.phoneNumber">
                      </div>
                      <div class="col-md-6 mb-3">
                        <label class="form-label">부서</label>
                        <input type="text" class="form-control" v-model="profile.department">
                      </div>
                    </div>
                    <div class="mb-3">
                      <label class="form-label">자기소개</label>
                      <textarea class="form-control" rows="3" v-model="profile.bio"></textarea>
                    </div>
                    <div class="text-end">
                      <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-lg"></i> 저장
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
              <form @submit.prevent="handleSavePreferences">
                <div class="mb-3">
                  <label class="form-label">언어</label>
                  <select class="form-select" v-model="preferences.language" @change="handleLanguageChange">
                    <option value="ko">한국어</option>
                    <option value="en">English</option>
                  </select>
                </div>
                <div class="mb-3">
                  <label class="form-label">시간대</label>
                  <select class="form-select" v-model="preferences.timezone">
                    <option value="Asia/Seoul">Asia/Seoul (KST)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>
                <div class="mb-3">
                  <label class="form-label">테마</label>
                  <select class="form-select" v-model="preferences.theme">
                    <option value="light">라이트</option>
                    <option value="dark">다크</option>
                    <option value="auto">시스템 설정</option>
                  </select>
                </div>
                <div class="text-end">
                  <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> 저장
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
              <form @submit.prevent="handleChangePassword">
                <div class="mb-3">
                  <label class="form-label">현재 비밀번호</label>
                  <input type="password" class="form-control" v-model="passwordForm.currentPassword" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">새 비밀번호</label>
                  <input type="password" class="form-control" v-model="passwordForm.newPassword" required>
                </div>
                <div class="mb-3">
                  <label class="form-label">비밀번호 확인</label>
                  <input type="password" class="form-control" v-model="passwordForm.confirmPassword" required>
                </div>
                <div class="text-end">
                  <button type="submit" class="btn btn-primary">
                    <i class="bi bi-check-lg"></i> 변경
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
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import type { UserDto, UserPreferenceDto } from '@/types'
import { safeGetLocalStorage, safeSetLocalStorage } from '@/utils/storage'

const authStore = useAuthStore()
const { locale } = useI18n()
const activeTab = ref('profile')

const profile = ref({
  fullName: '',
  email: '',
  phoneNumber: '',
  department: '',
  bio: ''
})

const preferences = ref({
  language: 'ko',
  timezone: 'Asia/Seoul',
  theme: 'light'
})

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loadProfile = async () => {
  try {
    if (authStore.user) {
      profile.value = {
        fullName: authStore.user.fullName || '',
        email: authStore.user.email || '',
        phoneNumber: authStore.user.phoneNumber || '',
        department: authStore.user.department || '',
        bio: authStore.user.bio || ''
      }
    } else {
      const response = await api.get<UserDto>('/users/me')
      if (response.data) {
        profile.value = {
          fullName: response.data.fullName || '',
          email: response.data.email || '',
          phoneNumber: response.data.phoneNumber || '',
          department: response.data.department || '',
          bio: response.data.bio || ''
        }
      }
    }
  } catch (error) {
    console.error('Error loading profile:', error)
  }
}

const handleUpdateProfile = async () => {
  try {
    if (!authStore.user?.userId) {
      alert('사용자 정보를 불러올 수 없습니다.')
      return
    }
    await api.put(`/users/${authStore.user.userId}`, profile.value)
    await authStore.loadUser()
    alert('프로필이 업데이트되었습니다.')
  } catch (error: any) {
    console.error('Error updating profile:', error)
    alert(error.response?.data?.message || '프로필 업데이트 중 오류가 발생했습니다.')
  }
}


const loadPreferences = async () => {
  try {
    const response = await api.get<UserPreferenceDto[]>('/userpreferences')
    const prefs = response.data || []
    
    // 데이터베이스에서 가져온 설정으로 preferences 초기화
    prefs.forEach(pref => {
      if (pref.preferenceKey === 'language') {
        preferences.value.language = pref.preferenceValue || 'ko'
      } else if (pref.preferenceKey === 'timezone') {
        preferences.value.timezone = pref.preferenceValue || 'Asia/Seoul'
      } else if (pref.preferenceKey === 'theme') {
        preferences.value.theme = pref.preferenceValue || 'light'
      }
    })
    
    // localStorage에서도 로드 (하위 호환성)
    const saved = safeGetLocalStorage('preferences')
    if (saved) {
      try {
        const localPrefs = JSON.parse(saved)
        // 데이터베이스에 없는 설정만 localStorage에서 사용
        if (!prefs.find(p => p.preferenceKey === 'language')) {
          preferences.value.language = localPrefs.language || preferences.value.language
        }
        if (!prefs.find(p => p.preferenceKey === 'timezone')) {
          preferences.value.timezone = localPrefs.timezone || preferences.value.timezone
        }
        if (!prefs.find(p => p.preferenceKey === 'theme')) {
          preferences.value.theme = localPrefs.theme || preferences.value.theme
        }
      } catch (error) {
        console.error('Error parsing localStorage preferences:', error)
      }
    }
    
    // 언어 설정 적용
    const savedLocale = safeGetLocalStorage('i18n_locale')
    if (savedLocale && (savedLocale === 'ko' || savedLocale === 'en')) {
      preferences.value.language = savedLocale
    }
    locale.value = preferences.value.language as 'ko' | 'en'
  } catch (error) {
    console.error('Error loading preferences:', error)
    // 오류 시 localStorage에서 로드
    const saved = safeGetLocalStorage('preferences')
    if (saved) {
      try {
        preferences.value = JSON.parse(saved)
      } catch (e) {
        console.error('Error parsing preferences:', e)
      }
    }
    const savedLocale = safeGetLocalStorage('i18n_locale')
    if (savedLocale && (savedLocale === 'ko' || savedLocale === 'en')) {
      preferences.value.language = savedLocale
      locale.value = savedLocale as 'ko' | 'en'
    }
  }
}

const handleLanguageChange = () => {
  locale.value = preferences.value.language as 'ko' | 'en'
  safeSetLocalStorage('i18n_locale', preferences.value.language)
}

const handleSavePreferences = async () => {
  try {
    // 언어 설정 저장 및 적용
    handleLanguageChange()
    
    // UserPreferences API에 저장
    const preferenceKeys = ['language', 'timezone', 'theme']
    const savePromises = preferenceKeys.map(key => {
      const value = preferences.value[key as keyof typeof preferences.value]
      return api.post('/userpreferences', {
        preferenceKey: key,
        preferenceValue: String(value),
        dataType: 'String',
        category: 'UI'
      })
    })
    
    await Promise.all(savePromises)
    
    // localStorage에도 저장 (하위 호환성)
    safeSetLocalStorage('preferences', JSON.stringify(preferences.value))
    
    alert('환경 설정이 저장되었습니다.')
  } catch (error: any) {
    console.error('Error saving preferences:', error)
    alert(error.response?.data?.message || '환경 설정 저장 중 오류가 발생했습니다.')
  }
}

const handleChangePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }

  try {
    if (!authStore.user?.userId) {
      alert('사용자 정보를 불러올 수 없습니다.')
      return
    }
    await api.put(`/users/${authStore.user.userId}`, {
      currentPassword: passwordForm.value.currentPassword,
      password: passwordForm.value.newPassword
    })
    alert('비밀번호가 변경되었습니다.')
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error: any) {
    console.error('Error changing password:', error)
    alert(error.response?.data?.message || '비밀번호 변경 중 오류가 발생했습니다.')
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
