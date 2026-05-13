<template>
  <div class="page-content-wrap qi-page container-fluid py-4">
    <div class="row align-items-start qi-header-row">
      <!-- Page Header (폼과 나란히) -->
      <div class="col-12 col-lg-4 col-xl-3 qi-header-col">
        <div class="page-header">
          <div>
            <h1 class="page-heading">{{ $t('nav.quickImageGeneration') }}</h1>
            <p class="page-desc">{{ $t('agentChat.quickImage.modelHint') }}</p>
          </div>
        </div>
      </div>
      <!-- Form Card -->
      <div class="col-12 col-lg-8 col-xl-9">

        <!-- Gemini 서비스 없음 안내 -->
        <div v-if="!serviceReady && !loadingService" class="alert alert-warning">
          <i class="bi bi-exclamation-triangle me-2"></i>
          {{ $t('agentChat.quickImage.noService') }}
          <router-link to="/image-generation" class="alert-link ms-1">{{ $t('agentChat.quickImage.goFull') }}</router-link>
        </div>

        <template v-else>
          <!-- Input Card -->
          <div class="card qi-card mb-4">
            <div class="card-body">
              <label class="form-label qi-label">{{ $t('agentChat.quickImage.promptLabel') }}</label>
              <textarea
                v-model="prompt"
                class="form-control qi-textarea"
                rows="4"
                :placeholder="$t('agentChat.quickImage.promptPlaceholder')"
                :disabled="loading"
              ></textarea>
              <div class="qi-char-row"><span>{{ (prompt || '').length }}</span> / 1000</div>
              <div class="mt-3 d-flex flex-wrap gap-3 align-items-center">
                <!-- 트랙 #88 H5 (2026-05-13): 버튼에 경과 시간 노출 + 스피너 아이콘 -->
                <button
                  type="button"
                  class="btn btn-primary qi-submit-btn"
                  :disabled="loading || !prompt.trim()"
                  @click="generate"
                >
                  <span
                    v-if="loading"
                    class="spinner-border spinner-border-sm me-2"
                    role="status"
                    aria-hidden="true"
                  ></span>
                  <i v-else class="bi bi-magic me-2"></i>
                  <span v-if="loading">{{ $t('agentChat.quickImage.generating') }} ({{ elapsedSec }}초)</span>
                  <span v-else>{{ $t('agentChat.quickImage.generate') }}</span>
                </button>
                <small class="text-muted qi-model-hint">{{ $t('agentChat.quickImage.modelHint') }}</small>
              </div>
            </div>
          </div>

          <!-- 에러 -->
          <div v-if="error" class="alert alert-danger">
            <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
          </div>

          <!-- Result Card -->
          <div class="card qi-card">
            <div class="card-header qi-result-header">
              <div>
                <h5 class="card-title mb-0">{{ $t('agentChat.quickImage.result') }}</h5>
                <p class="card-subtitle mb-0 qi-result-sub">생성된 이미지</p>
              </div>
              <button
                v-if="response && response.imageUrls.length > 0"
                class="btn btn-primary qi-download-btn"
                @click="downloadImage"
              >
                <i class="bi bi-download me-1"></i>{{ $t('agentChat.quickImage.download') }}
              </button>
            </div>

            <div class="card-body qi-result-body">
              <!-- Empty state -->
              <div v-if="!response && !loading" class="qi-empty-state">
                <div class="qi-empty-icon"><i class="bi bi-image"></i></div>
                <p class="qi-empty-text">{{ $t('agentChat.quickImage.emptyHint') }}</p>
                <p class="qi-empty-sub">{{ $t('agentChat.quickImage.emptySub') }}</p>
              </div>

              <!-- Loading state -->
              <!-- 트랙 #88 H5 (2026-05-13): 진행률 UI 보강 — 경과 시간 + 예상 대기 시간 안내 -->
              <div v-else-if="loading" class="qi-loading-state">
                <div class="qi-loading-inner">
                  <div class="qi-loading-icon">
                    <div class="qi-ring"></div>
                    <div class="qi-ring qi-ring2"></div>
                    <div class="qi-ring qi-ring3"></div>
                    <i class="bi bi-image qi-ring-icon"></i>
                  </div>
                  <p class="qi-loading-text">이미지를 생성하는 중입니다...</p>
                  <div class="qi-loading-bar-wrap">
                    <div class="qi-loading-bar"></div>
                  </div>
                  <p class="qi-loading-elapsed">
                    <i class="bi bi-clock-history me-1"></i>경과 시간: {{ elapsedSec }}초
                  </p>
                  <small class="qi-loading-hint">{{ loadingHintText }}</small>
                  <small class="qi-loading-hint mt-2 d-block">
                    <i class="bi bi-info-circle me-1"></i>
                    이미지 생성은 일반적으로 10~30초, 최대 60초까지 걸릴 수 있습니다.
                  </small>
                </div>
              </div>

              <!-- Image result -->
              <div v-else-if="response && response.imageUrls.length > 0" class="qi-image-wrap">
                <div class="qi-img-container rounded overflow-hidden">
                  <img
                    :src="getImageDisplayUrl(response.imageUrls[0])"
                    alt="Generated"
                    class="qi-canvas img-fluid"
                    @error="handleImageError"
                    loading="lazy"
                  >
                </div>
                <p class="qi-img-caption text-muted small mt-2 mb-0">{{ response.prompt }}</p>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Toast -->
    <div class="qi-toast" :class="{ show: showToast }">
      <i class="bi bi-check-circle"></i>
      <span>{{ toastText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'
import type { ApiServiceDto, ImageGenerationRequestDto, ImageGenerationResponseDto } from '@/types'
import './QuickImageGeneration.css'

const GEMINI_IMAGE_SERVICE_CODE = 'gemini-image'
const MODEL = 'gemini-2.5-flash-image'

const prompt = ref('')
const loading = ref(false)
const loadingService = ref(true)
const error = ref<string | null>(null)
const response = ref<ImageGenerationResponseDto | null>(null)
const geminiServiceId = ref<number | null>(null)
const serviceReady = ref(false)
const showToast = ref(false)
const toastText = ref('완료')

// 트랙 #88 H5 (2026-05-13): 이미지 생성 진행률 — 경과 시간 카운터.
const elapsedSec = ref(0)
let elapsedTimer: number | null = null

const loadingHintText = computed(() => {
  if (elapsedSec.value < 10) return 'Gemini 2.5 Flash Image가 이미지를 그리고 있어요'
  if (elapsedSec.value < 30) return '고품질 이미지를 그리는 중입니다. 잠시만 기다려 주세요'
  if (elapsedSec.value < 60) return '생성에 평소보다 시간이 소요되고 있습니다. 거의 다 되었습니다'
  return '생성이 오래 걸리고 있습니다. 네트워크 또는 서비스 상태에 따라 지연될 수 있습니다'
})

const startElapsedTimer = () => {
  elapsedSec.value = 0
  if (elapsedTimer !== null) {
    window.clearInterval(elapsedTimer)
  }
  elapsedTimer = window.setInterval(() => {
    elapsedSec.value += 1
  }, 1000)
}

const stopElapsedTimer = () => {
  if (elapsedTimer !== null) {
    window.clearInterval(elapsedTimer)
    elapsedTimer = null
  }
}

onUnmounted(() => {
  // 트랙 #88 H5 (2026-05-13): 진행 중 페이지 이탈 시 타이머 누수 방지
  stopElapsedTimer()
})

onMounted(async () => {
  try {
    const res = await api.get<ApiServiceDto[]>('/apiservices')
    const list = (res.data || []).filter(
      s => s.serviceType === 'ImageGeneration' || s.serviceType === 'Both'
    )
    const gemini = list.find(
      s => (s.serviceCode || '').toLowerCase() === GEMINI_IMAGE_SERVICE_CODE
    )
    if (gemini) {
      geminiServiceId.value = gemini.serviceId
      serviceReady.value = true
    }
  } catch (e) {
    console.error('Failed to load image services', e)
  } finally {
    loadingService.value = false
  }
})

async function generate() {
  if (!prompt.value.trim() || geminiServiceId.value == null) return

  loading.value = true
  error.value = null
  response.value = null
  startElapsedTimer()

  try {
    const requestData: ImageGenerationRequestDto = {
      prompt: prompt.value.trim(),
      model: MODEL,
      serviceId: geminiServiceId.value,
      size: '1024x1024',
      quality: 'standard',
      numberOfImages: 1
    }
    const apiResponse = await api.post<ImageGenerationResponseDto>(
      '/image-generation/generate',
      requestData
    )
    response.value = apiResponse.data
    toastText.value = '이미지가 생성되었습니다.'
    showToast.value = true
    setTimeout(() => { showToast.value = false }, 2500)
  } catch (err: unknown) {
    const e = err as { response?: { data?: { message?: string }; status?: number }; message?: string }
    error.value =
      e.response?.data?.message || e.message || '이미지 생성에 실패했습니다.'
  } finally {
    stopElapsedTimer()
    loading.value = false
  }
}

async function downloadImage() {
  if (!response.value?.imageUrls?.length) return

  const imageUrl = response.value.imageUrls[0]
  const downloadFilename = `quick-image-${Date.now()}.png`

  try {
    // data URL(base64)인 경우 API를 거치지 않고 클라이언트에서 직접 다운로드 (URL 길이 제한 414 회피)
    if (imageUrl.startsWith('data:')) {
      const base64Match = imageUrl.match(/^data:([^;]+);base64,(.+)$/)
      if (base64Match) {
        const mimeType = base64Match[1] || 'image/png'
        const base64Data = base64Match[2]
        const byteCharacters = atob(base64Data)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], { type: mimeType })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = downloadFilename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        return
      }
    }

    // http(s) URL인 경우 API를 통해 다운로드
    const downloadUrl = `image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(downloadFilename)}`
    const res = await api.get(downloadUrl, { responseType: 'blob' })
    const blob = new Blob([res.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = downloadFilename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } }; message?: string }
    console.error('Download failed', err)
    alert('다운로드에 실패했습니다: ' + (err.response?.data?.message || err.message || '알 수 없는 오류'))
  }
}

/** 외부 URL은 CORS/만료 방지를 위해 프록시 경로로 변환 */
function getImageDisplayUrl(imageUrl: string): string {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('data:')) return imageUrl
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return `/api/image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}`
  }
  return imageUrl
}

function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23f0f0f0" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3E이미지를 불러올 수 없습니다%3C/text%3E%3C/svg%3E'
}
</script>
