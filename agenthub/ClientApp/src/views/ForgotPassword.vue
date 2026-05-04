<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <i class="bi bi-robot"></i> AIAgent Management
      </div>

      <h2 class="auth-title">비밀번호 찾기</h2>
      <p class="auth-desc">가입한 이메일을 입력하시면 재설정 링크를 보내드립니다.</p>

      <div v-if="sent" class="alert-success">
        <i class="bi bi-check-circle-fill"></i>
        이메일을 발송했습니다. 받은 편지함을 확인해 주세요.
        <br><small>메일이 오지 않으면 스팸 폴더도 확인해 주세요.</small>
      </div>

      <form v-else @submit.prevent="handleSubmit">
        <div class="form-group">
          <label class="form-label">이메일</label>
          <input
            type="email"
            class="form-control"
            v-model="email"
            placeholder="가입한 이메일 주소"
            required
            autofocus
          >
        </div>

        <div v-if="errorMsg" class="alert-error">
          <i class="bi bi-exclamation-circle"></i> {{ errorMsg }}
        </div>

        <button type="submit" class="btn-auth" :disabled="loading">
          <span v-if="loading"><i class="bi bi-arrow-clockwise spin"></i> 발송 중...</span>
          <span v-else>재설정 링크 발송</span>
        </button>
      </form>

      <div class="auth-footer">
        <router-link to="/login" class="back-link">
          <i class="bi bi-arrow-left"></i> 로그인으로 돌아가기
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'

const email = ref('')
const loading = ref(false)
const sent = ref(false)
const errorMsg = ref('')

const handleSubmit = async () => {
  errorMsg.value = ''
  loading.value = true
  try {
    await api.post('/auth/forgot-password', { email: email.value })
    sent.value = true
  } catch {
    errorMsg.value = '요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
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
  margin-bottom: 0.5rem;
  text-align: center;
}

.auth-desc {
  color: var(--ai-text-muted, #6b7280);
  font-size: 0.875rem;
  text-align: center;
  margin-bottom: 1.5rem;
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

.form-control {
  width: 100%;
  padding: 0.6rem 0.875rem;
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
  line-height: 1.6;
  margin-bottom: 1rem;
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
  margin-bottom: 0.75rem;
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
