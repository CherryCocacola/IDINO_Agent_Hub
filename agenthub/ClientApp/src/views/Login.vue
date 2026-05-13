<template>
  <div class="lg-body">
    <!-- Background decoration -->
    <div class="lg-bg-orb lg-orb1"></div>
    <div class="lg-bg-orb lg-orb2"></div>
    <div class="lg-bg-orb lg-orb3"></div>

    <div class="lg-wrap">
      <!-- Logo area -->
      <div class="lg-logo-area">
        <div class="lg-logo-icon">
          <i class="bi bi-cpu"></i>
        </div>
        <div class="lg-logo-text">
          <span class="lg-brand">AI Manager</span>
          <span class="lg-brand-sub">통합관리시스템</span>
        </div>
      </div>

      <!-- Card -->
      <div class="lg-card">
        <div class="lg-card-inner">
          <!-- Header -->
          <div class="lg-header">
            <h2 class="lg-title">{{ $t('auth.login') }}</h2>
            <p class="lg-subtitle">{{ $t('auth.loginSubtitle') }}</p>
          </div>

          <!-- Alert -->
          <div class="lg-alert" v-show="error">
            <i class="bi bi-exclamation-circle"></i>
            <span>{{ error }}</span>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleLogin" autocomplete="on">
            <div class="lg-field">
              <label class="lg-label" for="lgEmail">이메일</label>
              <div class="lg-input-wrap">
                <i class="bi bi-envelope lg-input-icon"></i>
                <input
                  v-model="email"
                  type="email"
                  class="lg-input"
                  id="lgEmail"
                  :placeholder="$t('login.emailPlaceholder')"
                  autocomplete="email"
                  required
                >
              </div>
            </div>

            <div class="lg-field">
              <div class="lg-label-row">
                <label class="lg-label" for="lgPassword">비밀번호</label>
                <a href="#" class="lg-forgot" @click.prevent="showForgotModal = true">비밀번호를 잊으셨나요?</a>
              </div>
              <div class="lg-input-wrap">
                <i class="bi bi-lock lg-input-icon"></i>
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  class="lg-input lg-has-pw-toggle"
                  id="lgPassword"
                  :placeholder="$t('login.passwordPlaceholder')"
                  autocomplete="current-password"
                  required
                >
                <button type="button" class="lg-pw-toggle" @click="showPassword = !showPassword" tabindex="-1" :title="showPassword ? $t('login.hidePassword') : $t('login.showPassword')">
                  <i class="bi" :class="showPassword ? 'bi-eye-slash' : 'bi-eye'"></i>
                </button>
              </div>
            </div>

            <div class="lg-remember-row">
              <label class="lg-check-label" for="lgRemember">
                <input type="checkbox" class="lg-check" id="lgRemember" v-model="rememberMe">
                <span class="lg-check-box"></span>
                <span class="lg-check-text">로그인 상태 유지</span>
              </label>
            </div>

            <button type="submit" class="lg-submit-btn" :disabled="loading">
              <span v-if="!loading">로그인</span>
              <div v-else class="lg-submit-spinner"></div>
            </button>
          </form>

          <!-- Divider 

          <div class="lg-divider">
            <span>또는</span>
          </div>-->

          <!-- SSO buttons (placeholder - backend 미구현 시 비활성) 
          <div class="lg-sso-group">
            <button type="button" class="lg-sso-btn lg-sso-google" disabled :title="$t('login.preparing')">
              <i class="bi bi-google"></i>
              <span>Google로 로그인</span>
            </button>
            <button type="button" class="lg-sso-btn lg-sso-microsoft" disabled :title="$t('login.preparing')">
              <i class="bi bi-microsoft"></i>
              <span>Microsoft로 로그인</span>
            </button>
          </div>-->
        
        </div>
      </div>

      <!-- Footer -->
      <p class="lg-footer-text">
        © 2025 AI Manager. All rights reserved.
      </p>
    </div>

    <!-- Forgot PW Modal -->
    <div class="lg-modal-overlay" :class="{ open: showForgotModal }">
      <div class="lg-modal">
        <div class="lg-modal-header">
          <div class="lg-modal-icon"><i class="bi bi-envelope-open"></i></div>
          <div>
            <h5>비밀번호 재설정</h5>
            <p>등록된 이메일로 재설정 링크를 보내드립니다</p>
          </div>
          <button class="lg-modal-close" @click="showForgotModal = false"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="lg-modal-body">
          <div v-if="forgotDone" style="padding:0.5rem 0;color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:0.85rem;font-size:0.9rem;line-height:1.6;">
            <i class="bi bi-check-circle-fill" style="color:#16a34a;margin-right:0.4rem"></i>
            이메일을 발송했습니다. 받은 편지함을 확인해 주세요.
          </div>
          <template v-else>
            <div class="lg-field">
              <label class="lg-label">이메일 주소</label>
              <div class="lg-input-wrap">
                <i class="bi bi-envelope lg-input-icon"></i>
                <input type="email" class="lg-input" v-model="forgotEmail" :placeholder="$t('login.forgotEmailPlaceholder')">
              </div>
            </div>
            <div v-if="forgotError" style="color:#991b1b;font-size:0.875rem;margin-top:0.5rem;">
              <i class="bi bi-exclamation-circle"></i> {{ forgotError }}
            </div>
          </template>
        </div>
        <div class="lg-modal-footer">
          <button class="lg-modal-cancel" @click="showForgotModal = false; forgotDone = false; forgotEmail = ''">
            {{ forgotDone ? '닫기' : '취소' }}
          </button>
          <button v-if="!forgotDone" class="btn btn-primary" @click="handleForgotSubmit" :disabled="!forgotEmail.trim() || forgotLoading">
            <i v-if="forgotLoading" class="bi bi-arrow-clockwise me-2" style="animation:spin .8s linear infinite;display:inline-block"></i>
            <i v-else class="bi bi-send me-2"></i>
            {{ forgotLoading ? '발송 중...' : '재설정 링크 전송' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// localhost / 127.0.0.1 환경에서만 기본값 제공 (개발 편의용) — 실제 도메인에서는 비워 둠
const isLocalhost = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname)
const email = ref(isLocalhost ? 'admin@example.com' : '')
const password = ref(isLocalhost ? 'Admin123!' : '')
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const showForgotModal = ref(false)
const forgotEmail = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''

  try {
    // 트랙 #88 C2 (2026-05-13):
    // "로그인 상태 유지" 체크 여부를 store 에 전달.
    //   - true  → localStorage 영구 보관 (브라우저 재시작 후에도 자동 로그인)
    //   - false → sessionStorage (탭/창 닫으면 로그아웃)
    const result = await authStore.login(
      {
        email: email.value,
        password: password.value
      },
      rememberMe.value
    )
    // 로그인 전 진입하려던 페이지가 있으면 그 페이지로, 없으면 기본 경로로
    const redirectPath = (route.query.redirect as string) || (result.user?.roles?.some((r: string) => r.toLowerCase() === 'admin') ? '/' : '/agents')
    await router.push(redirectPath)
  } catch (err: any) {
    if (err.response?.data?.message) {
      error.value = err.response.data.message
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = t('login.loginFailed')
    }
  } finally {
    loading.value = false
  }
}

const forgotLoading = ref(false)
const forgotDone = ref(false)
const forgotError = ref('')

async function handleForgotSubmit() {
  if (!forgotEmail.value.trim()) return
  forgotLoading.value = true
  forgotError.value = ''
  try {
    await api.post('/auth/forgot-password', { email: forgotEmail.value.trim() })
    forgotDone.value = true
  } catch {
    forgotError.value = '요청 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    forgotLoading.value = false
  }
}
</script>

<style src="@/assets/css/login.css"></style>
