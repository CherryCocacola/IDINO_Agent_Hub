<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <i class="bi bi-robot"></i> AIAgent Management
      </div>

      <h2 class="auth-title">새 비밀번호 설정</h2>

      <!-- 성공 -->
      <div v-if="done" class="alert-success">
        <i class="bi bi-check-circle-fill"></i>
        비밀번호가 변경되었습니다.
        <br>
        <router-link to="/login" class="alert-link">로그인 페이지로 이동 →</router-link>
      </div>

      <!-- 토큰 없음 -->
      <div v-else-if="!token || !email" class="alert-error">
        <i class="bi bi-exclamation-circle"></i>
        유효하지 않은 링크입니다. 비밀번호 찾기를 다시 시도해 주세요.
        <br>
        <router-link to="/forgot-password" class="alert-link">비밀번호 찾기 →</router-link>
      </div>

      <!-- 폼 -->
      <form v-else @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">새 비밀번호</label>
          <div class="pw-wrap">
            <input
              :type="showPw ? 'text' : 'password'"
              class="form-control"
              v-model="newPassword"
              placeholder="8자 이상"
              minlength="8"
              required
              autofocus
            >
            <button type="button" class="pw-toggle" @click="showPw = !showPw">
              <i :class="showPw ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
            </button>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">새 비밀번호 확인</label>
          <div class="pw-wrap">
            <input
              :type="showPw2 ? 'text' : 'password'"
              class="form-control"
              v-model="confirmPassword"
              placeholder="비밀번호 재입력"
              required
            >
            <button type="button" class="pw-toggle" @click="showPw2 = !showPw2">
              <i :class="showPw2 ? 'bi bi-eye-slash' : 'bi bi-eye'"></i>
            </button>
          </div>
          <small v-if="confirmPassword && newPassword !== confirmPassword" class="text-danger">
            비밀번호가 일치하지 않습니다.
          </small>
        </div>

        <div v-if="errorMsg" class="alert-error">
          <i class="bi bi-exclamation-circle"></i> {{ errorMsg }}
        </div>

        <button
          type="submit"
          class="btn-auth"
          :disabled="loading || newPassword !== confirmPassword || newPassword.length < 8"
        >
          <span v-if="loading"><i class="bi bi-arrow-clockwise spin"></i> 변경 중...</span>
          <span v-else>비밀번호 변경</span>
        </button>
      </form>

      <div class="auth-footer" v-if="!done">
        <router-link to="/login" class="back-link">
          <i class="bi bi-arrow-left"></i> 로그인으로 돌아가기
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'

const route = useRoute()
const email = ref((route.query.email as string) || '')
const token = ref((route.query.token as string) || '')

const newPassword = ref('')
const confirmPassword = ref('')
const showPw = ref(false)
const showPw2 = ref(false)
const loading = ref(false)
const done = ref(false)
const errorMsg = ref('')

const handleSubmit = async () => {
  if (newPassword.value !== confirmPassword.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    await api.post('/auth/reset-password', {
      email: email.value,
      token: token.value,
      newPassword: newPassword.value
    })
    done.value = true
  } catch (err: any) {
    errorMsg.value = err?.response?.data?.message || '유효하지 않거나 만료된 링크입니다. 비밀번호 찾기를 다시 시도해 주세요.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--ai-bg, #f8f9fa);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.auth-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,.1);
  padding: 2.5rem;
  width: 100%;
  max-width: 420px;
}

.auth-logo {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--ai-primary, #4f46e5);
  margin-bottom: 1.5rem;
  text-align: center;
}

.auth-title {
  font-size: 1.5rem !important;
  font-weight: 700 !important;
  color: var(--ai-text, #111827);
  margin-bottom: 1.5rem;
  text-align: center;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--ai-text, #111827);
  margin-bottom: 0.35rem;
  display: block;
}

.pw-wrap {
  position: relative;
}

.form-control {
  width: 100%;
  padding: 0.6rem 2.5rem 0.6rem 0.875rem;
  border: 1.5px solid var(--ai-border, #e5e7eb);
  border-radius: 8px;
  font-size: 0.9375rem;
  outline: none;
  transition: border-color .2s;
  box-sizing: border-box;
}

.form-control:focus {
  border-color: var(--ai-primary, #4f46e5);
}

.pw-toggle {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ai-text-muted, #6b7280);
  padding: 0;
  line-height: 1;
}

.text-danger {
  color: #dc2626;
  font-size: 0.8rem;
  margin-top: 0.25rem;
  display: block;
}

.btn-auth {
  width: 100%;
  padding: 0.7rem;
  background: var(--ai-primary, #4f46e5);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 0.5rem;
  transition: background .2s;
}

.btn-auth:hover:not(:disabled) {
  background: var(--ai-primary-dark, #4338ca);
}

.btn-auth:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.alert-success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.8;
}

.alert-success i {
  color: #16a34a;
  margin-right: 0.4rem;
}

.alert-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}

.alert-link {
  color: inherit;
  font-weight: 600;
}

.auth-footer {
  margin-top: 1.5rem;
  text-align: center;
}

.back-link {
  color: var(--ai-primary, #4f46e5);
  font-size: 0.875rem;
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}

@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin .8s linear infinite; }
</style>
