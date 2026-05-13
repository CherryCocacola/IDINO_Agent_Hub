<template>
  <div class="page-content-wrap ic-page container-fluid py-4">
    <div class="page-header">
      <div>
        <h1 class="page-heading">이미지 생성</h1>
        <p class="page-desc">AI로 이미지를 생성합니다. 서비스와 모델을 선택한 뒤 프롬프트를 입력하세요.</p>
      </div>
    </div>

    <div class="row g-4">
      <!-- 좌측: 설정 영역 -->
      <div class="col-lg-4">
        <div class="card ic-card ic-settings-card">
          <div class="card-header ic-card-header">
            <div>
              <h5 class="card-title mb-0">생성 설정</h5>
              <p class="card-subtitle mb-0 mt-1">서비스·모델·크기 선택</p>
            </div>
          </div>
          <div class="card-body">
            <form @submit.prevent="generateImage">
              <!-- 서비스 선택 -->
              <div class="mb-3">
                <label class="form-label ic-label">이미지 생성 서비스 <span class="text-danger">*</span></label>
                <select class="form-select ic-select" v-model="selectedServiceId" @change="onServiceChange" required>
                  <option value="">서비스를 선택하세요</option>
                  <option v-for="service in imageServices" :key="service.serviceId" :value="service.serviceId">
                    {{ service.serviceName }}
                  </option>
                </select>
              </div>

              <!-- 모델 선택 -->
              <div class="mb-3" v-if="selectedServiceId">
                <label class="form-label ic-label">모델</label>
                <select class="form-select ic-select" v-model="request.model">
                  <option value="">기본 모델 사용</option>
                  <option v-for="model in availableModels" :key="model" :value="model">
                    {{ model }}
                  </option>
                </select>
                <small class="text-muted mt-1 d-block">기본 모델을 사용하려면 비워두세요</small>
              </div>

              <!-- 프롬프트 입력 -->
              <div class="mb-3">
                <label class="form-label ic-label">프롬프트 <span class="text-danger">*</span></label>
                <textarea
                  class="form-control ic-textarea"
                  v-model="request.prompt"
                  rows="5"
                  :placeholder="$t('imageGeneration.promptPlaceholder')"
                  required
                ></textarea>
                <div class="ic-char-row">
                  <span>{{ (request.prompt || '').length }}</span> / 1000
                </div>
              </div>

              <!-- 이미지 크기 (버튼 그리드) -->
              <div class="mb-3">
                <label class="form-label ic-label">이미지 크기</label>
                <div class="ic-size-grid">
                  <button
                    v-for="opt in sizeOptions"
                    :key="opt.value"
                    type="button"
                    class="ic-size-btn"
                    :class="{ active: request.size === opt.value }"
                    @click="request.size = opt.value"
                  >
                    <i :class="opt.icon"></i>
                    <span>{{ opt.value }}</span>
                    <small>{{ opt.label }}</small>
                  </button>
                </div>
              </div>

              <!-- 품질 -->
              <div class="mb-3">
                <label class="form-label ic-label">품질</label>
                <select class="form-select ic-select" v-model="request.quality">
                  <option value="standard">Standard</option>
                  <option value="hd">HD (고화질)</option>
                </select>
              </div>

              <!-- 생성 개수 -->
              <div class="mb-3">
                <label class="form-label ic-label">생성 개수</label>
                <div class="ic-count-row">
                  <button type="button" class="ic-count-btn" @click="request.numberOfImages = Math.max(1, (request.numberOfImages || 1) - 1)">
                    <i class="bi bi-dash"></i>
                  </button>
                  <input type="number" class="form-control ic-count-input" v-model.number="request.numberOfImages" min="1" max="10">
                  <button type="button" class="ic-count-btn" @click="request.numberOfImages = Math.min(10, (request.numberOfImages || 1) + 1)">
                    <i class="bi bi-plus"></i>
                  </button>
                </div>
                <small class="text-muted mt-1 d-block">일부 서비스는 1개만 지원합니다</small>
              </div>

              <!-- 예상 크레딧 -->
              <div class="ic-cost-box mb-3">
                <div class="ic-cost-row">
                  <div class="ic-cost-icon"><i class="bi bi-currency-dollar"></i></div>
                  <span class="ic-cost-label">예상 크레딧:</span>
                  <span class="ic-cost-val" v-if="selectedServiceId && loadingEstimate">...</span>
                  <span class="ic-cost-val" v-else-if="selectedServiceId && estimatedCost !== null">${{ estimatedCost.toFixed(4) }}</span>
                  <span class="ic-cost-val" v-else>$0.0000</span>
                </div>
              </div>

              <!-- 생성 버튼 -->
              <!-- 트랙 #88 H5 (2026-05-13): 버튼에 경과 시간 노출 + 스피너 아이콘 — 사용자가 무한 대기 상태로 느끼지 않도록 -->
              <button
                type="submit"
                class="btn btn-primary w-100 ic-submit-btn"
                :class="{ 'ic-generating': loading }"
                :disabled="loading || !request.prompt || !selectedServiceId"
              >
                <span
                  v-if="loading"
                  class="spinner-border spinner-border-sm me-2"
                  role="status"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-magic me-2"></i>
                <span v-if="loading">{{ $t('imageGeneration.generating') }} ({{ elapsedSec }}초)</span>
                <span v-else>{{ $t('imageGeneration.generate') }}</span>
              </button>
            </form>
          </div>
        </div>
      </div>

      <!-- 우측: 결과 영역 -->
      <div class="col-lg-8">
        <div class="card ic-card">
          <div class="card-header ic-card-header ic-result-header">
            <h5 class="card-title mb-0">생성 결과</h5>
            <button
              v-if="response && response.imageUrls.length > 0"
              class="btn btn-sm btn-outline-primary ic-download-all-btn"
              @click="downloadAllImages"
            >
              <i class="bi bi-download me-1"></i> 모두 다운로드
            </button>
          </div>
          <div class="card-body ic-result-body">
            <!-- Empty state -->
            <div v-if="!response && !loading && !error" class="ic-empty-state">
              <div class="ic-empty-icon">
                <i class="bi bi-image"></i>
              </div>
              <h6 class="ic-empty-title">아직 생성된 이미지가 없습니다</h6>
              <p class="ic-empty-desc">왼쪽에서 서비스와 프롬프트를 설정하고<br>이미지 생성 버튼을 눌러보세요.</p>
            </div>

            <!-- Loading state -->
            <!-- 트랙 #88 H5 (2026-05-13): 진행률 UI 보강 — 경과 시간 카운터 + 예상 대기 시간 안내 + 단계 표시 -->
            <div v-if="loading" class="ic-loading-state">
              <div class="ic-loading-spinner">
                <div class="ic-spinner-ring"></div>
                <div class="ic-spinner-ring ic-ring2"></div>
                <div class="ic-spinner-ring ic-ring3"></div>
              </div>
              <p class="ic-loading-text">이미지를 생성하는 중입니다...</p>
              <div class="ic-loading-bar-wrap">
                <div class="ic-loading-bar"></div>
              </div>
              <p class="ic-loading-elapsed">
                <i class="bi bi-clock-history me-1"></i>경과 시간: {{ elapsedSec }}초
              </p>
              <small class="ic-loading-hint">{{ loadingHintText }}</small>
              <small class="ic-loading-hint mt-2 d-block">
                <i class="bi bi-info-circle me-1"></i>
                이미지 생성은 일반적으로 10~30초, 모델에 따라 최대 60초까지 걸릴 수 있습니다.
              </small>
            </div>

            <!-- Error -->
            <div v-if="error" class="alert alert-danger">
              <i class="bi bi-exclamation-triangle me-2"></i>{{ error }}
            </div>

            <!-- Image results -->
            <div v-if="response && response.imageUrls.length > 0" class="ic-result-grid">
              <div class="row g-3">
                <div
                  v-for="(imageUrl, index) in response.imageUrls"
                  :key="index"
                  class="col-md-6"
                >
                  <div class="ic-img-card">
                    <div
                      class="ic-img-thumb-wrap"
                      :class="{
                        landscape: (request.size || '').includes('1792x1024'),
                        portrait: (request.size || '').includes('1024x1792')
                      }"
                      @click="openImageModal(imageUrl)"
                    >
                      <img
                        v-if="getProxyImageSrc(imageUrl, index)"
                        :src="getProxyImageSrc(imageUrl, index)"
                        :alt="`Generated image ${index + 1}`"
                        class="ic-img-thumb"
                        @error="handleImageError"
                        loading="lazy"
                      >
                      <div v-else class="ic-img-loading">로딩 중...</div>
                    </div>
                    <div class="ic-img-card-body">
                      <span class="ic-img-label">이미지 {{ index + 1 }}</span>
                      <button class="btn btn-sm btn-outline-primary ic-img-download-btn" @click="downloadImage(imageUrl, index)">
                        <i class="bi bi-download me-1"></i>다운로드
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="ic-gen-info">
                <div class="ic-gen-info-grid">
                  <div class="ic-gen-info-item">
                    <div class="ic-gen-info-label">프롬프트</div>
                    <div class="ic-gen-info-val">{{ response.prompt }}</div>
                  </div>
                  <div class="ic-gen-info-item">
                    <div class="ic-gen-info-label">모델</div>
                    <div class="ic-gen-info-val">{{ response.model }}</div>
                  </div>
                  <div class="ic-gen-info-item">
                    <div class="ic-gen-info-label">생성 시간</div>
                    <div class="ic-gen-info-val">{{ formatDate(response.createdAt) }}</div>
                  </div>
                  <div class="ic-gen-info-item">
                    <div class="ic-gen-info-label">응답 시간</div>
                    <div class="ic-gen-info-val">{{ response.responseTime }}ms</div>
                  </div>
                  <div class="ic-gen-info-item">
                    <div class="ic-gen-info-label">비용</div>
                    <div class="ic-gen-info-val">${{ response.cost.toFixed(4) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Lightbox -->
    <div class="ic-lightbox" :class="{ open: showImageModal }" @click.self="showImageModal = false">
      <div class="ic-lb-backdrop" @click="showImageModal = false"></div>
      <div class="ic-lb-box">
        <button class="ic-lb-close" @click="showImageModal = false"><i class="bi bi-x-lg"></i></button>
        <div class="ic-lb-img-wrap">
          <img
            v-if="selectedImageUrl && lightboxImageSrc"
            class="ic-lb-img"
            :src="lightboxImageSrc"
            alt="Preview"
            @error="handleImageError"
          >
          <div v-else-if="selectedImageUrl" class="ic-img-loading">로딩 중...</div>
        </div>
        <div class="ic-lb-footer">
          <span>이미지 미리보기</span>
          <button class="ic-lb-download" @click="downloadImage(selectedImageUrl, 0)">
            <i class="bi bi-download me-1"></i> 다운로드
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <div class="ic-toast" :class="{ show: showToast }">
      <i class="bi bi-check-circle"></i>
      <span>{{ toastText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import type { ApiServiceDto, ImageGenerationRequestDto, ImageGenerationResponseDto } from '@/types'
import './ImageGeneration.css'

const { t } = useI18n()

const imageServices = ref<ApiServiceDto[]>([])
const selectedServiceId = ref<number>(0)
const availableModels = ref<string[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const response = ref<ImageGenerationResponseDto | null>(null)
const showImageModal = ref(false)
const selectedImageUrl = ref('')
const estimatedCost = ref<number | null>(null)
const loadingEstimate = ref(false)

// 트랙 #88 H5 (2026-05-13): 이미지 생성 진행률 표시 — 경과 시간 카운터.
// 사용자가 무한 대기 상태로 느끼지 않도록 1초마다 갱신.
const elapsedSec = ref(0)
let elapsedTimer: number | null = null

const loadingHintText = computed(() => {
  if (elapsedSec.value < 10) return 'AI가 프롬프트를 분석하고 이미지를 그리고 있어요'
  if (elapsedSec.value < 30) return '고품질 이미지를 그리는 중입니다. 잠시만 기다려 주세요'
  if (elapsedSec.value < 60) return '생성에 평소보다 시간이 소요되고 있습니다. 거의 다 되었습니다'
  return '생성이 오래 걸리고 있습니다. 네트워크 또는 서비스 상태에 따라 지연될 수 있습니다'
})

const isDalleService = computed(() => {
  if (!selectedServiceId.value) return false
  const service = imageServices.value.find(s => s.serviceId === selectedServiceId.value)
  return service ? (service.serviceCode?.toLowerCase().includes('dalle') || 
                    service.serviceName?.toLowerCase().includes('dall-e')) : false
})

const sizeOptions = computed(() => {
  if (isDalleService.value) {
    return [
      { value: '1024x1024', label: '정사각형', icon: 'bi bi-square' },
      { value: '1792x1024', label: '가로', icon: 'bi bi-aspect-ratio' },
      { value: '1024x1792', label: '세로', icon: 'bi bi-phone' }
    ]
  }
  return [
    { value: '1024x1024', label: '정사각형', icon: 'bi bi-square' },
    { value: '1792x1024', label: '가로', icon: 'bi bi-aspect-ratio' },
    { value: '1024x1792', label: '세로', icon: 'bi bi-phone' },
    { value: '512x512', label: '소형', icon: 'bi bi-square-half' }
  ]
})

const showToast = ref(false)
const toastText = ref('완료')

const request = ref<ImageGenerationRequestDto>({
  prompt: '',
  model: undefined,
  size: '1024x1024',
  quality: 'standard',
  numberOfImages: 1,
  serviceId: 0
})

const loadImageServices = async () => {
  try {
    const response = await api.get<ApiServiceDto[]>('/apiservices')
    imageServices.value = (response.data || []).filter(
      s => s.serviceType === 'ImageGeneration' || s.serviceType === 'Both'
    )
  } catch (error: any) {
    console.error('이미지 생성 서비스 로드 실패:', error)
    alert('이미지 생성 서비스를 불러오는데 실패했습니다.')
  }
}

const fetchEstimatedCost = async () => {
  if (!selectedServiceId.value) {
    estimatedCost.value = null
    return
  }
  loadingEstimate.value = true
  estimatedCost.value = null
  try {
    const params = new URLSearchParams({
      serviceId: String(selectedServiceId.value),
      size: request.value.size ?? '1024x1024',
      quality: request.value.quality ?? 'standard',
      numberOfImages: String(request.value.numberOfImages ?? 1)
    })
    if (request.value.model) params.set('model', request.value.model)
    const res = await api.get<{ estimatedCost: number }>(`/image-generation/estimate-cost?${params}`)
    estimatedCost.value = res.data?.estimatedCost ?? null
  } catch (e) {
    console.error('예상 비용 조회 실패:', e)
    estimatedCost.value = null
  } finally {
    loadingEstimate.value = false
  }
}

const onServiceChange = async () => {
  if (!selectedServiceId.value) {
    availableModels.value = []
    request.value.serviceId = 0
    estimatedCost.value = null
    return
  }

  request.value.serviceId = selectedServiceId.value
  const service = imageServices.value.find(s => s.serviceId === selectedServiceId.value)
  if (service) {
    request.value.model = service.defaultModel || undefined
    
    // DALL-E 서비스인 경우 지원되는 크기로 제한
    if (service.serviceCode?.toLowerCase().includes('dalle') || 
        service.serviceName?.toLowerCase().includes('dall-e')) {
      // DALL-E 3는 1024x1024, 1024x1792, 1792x1024만 지원
      if (!['1024x1024', '1024x1792', '1792x1024'].includes(request.value.size ?? '')) {
        request.value.size = '1024x1024'
      }
    }
  }

  // 사용 가능한 모델 목록 로드
  try {
    const modelsResponse = await api.get<string[]>(`/apiservices/${selectedServiceId.value}/models`)
    availableModels.value = modelsResponse.data || []
  } catch (error: any) {
    console.error('모델 목록 로드 실패:', error)
    availableModels.value = []
  }
}

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

const generateImage = async () => {
  if (!request.value.prompt || !selectedServiceId.value) {
    error.value = '프롬프트와 서비스를 선택해주세요.'
    return
  }

  loading.value = true
  error.value = null
  response.value = null
  startElapsedTimer()

  try {
    const requestData = {
      ...request.value,
      serviceId: selectedServiceId.value
    }
    const apiResponse = await api.post<ImageGenerationResponseDto>('/image-generation/generate', requestData)
    response.value = apiResponse.data
  } catch (error: any) {
    console.error('이미지 생성 실패:', error)
    const data = error.response?.data
    let errorMessage = '이미지 생성에 실패했습니다.'
    if (data) {
      if (typeof data === 'string') {
        errorMessage = data
      } else if (data.message) {
        errorMessage = data.message
      } else if (data.error) {
        errorMessage = data.innerError ? `${data.error}: ${data.innerError}` : data.error
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    error.value = errorMessage
    console.error('상세 오류 정보:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: errorMessage
    })
  } finally {
    stopElapsedTimer()
    loading.value = false
    if (!error.value && response.value) {
      toastText.value = '이미지가 생성되었습니다.'
      showToast.value = true
      setTimeout(() => { showToast.value = false }, 2500)
    }
  }
}

const openImageModal = (imageUrl: string) => {
  selectedImageUrl.value = imageUrl
  showImageModal.value = true
}

const downloadImage = async (imageUrl: string, index: number) => {
  try {
    const downloadFilename = `generated-image-${Date.now()}-${index + 1}.png`

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
    const downloadUrl = `/api/image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(downloadFilename)}`
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
  } catch (error: any) {
    console.error('이미지 다운로드 실패:', error)
    alert('이미지 다운로드에 실패했습니다: ' + (error.response?.data?.message || error.message || '알 수 없는 오류'))
  }
}

const downloadAllImages = async () => {
  if (!response.value || response.value.imageUrls.length === 0) return

  for (let i = 0; i < response.value.imageUrls.length; i++) {
    await downloadImage(response.value.imageUrls[i], i)
    // 다운로드 간 약간의 지연 (브라우저 정책상)
    if (i < response.value.imageUrls.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 500))
    }
  }
}

/** 인증이 필요한 프록시를 통해 이미지 로드. blob URL 캐시. */
const proxyImageUrls = ref<Record<string, string>>({})
const lightboxImageSrc = ref<string>('')

const loadImageViaProxy = async (imageUrl: string): Promise<string> => {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('data:')) return imageUrl
  if (proxyImageUrls.value[imageUrl]) return proxyImageUrls.value[imageUrl]
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    try {
      const url = `/api/image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}`
      const res = await api.get(url, { responseType: 'blob' })
      const blobUrl = URL.createObjectURL(res.data)
      proxyImageUrls.value = { ...proxyImageUrls.value, [imageUrl]: blobUrl }
      return blobUrl
    } catch (e) {
      console.error('이미지 프록시 로드 실패:', e)
      return ''
    }
  }
  return imageUrl
}

const getProxyImageSrc = (imageUrl: string, _index: number): string => {
  if (!imageUrl) return ''
  if (imageUrl.startsWith('data:')) return imageUrl
  return proxyImageUrls.value[imageUrl] ?? ''
}

/** response 변경 시 이미지들을 프록시로 로드 */
watch(() => response.value?.imageUrls, async (urls) => {
  if (!urls?.length) {
    Object.values(proxyImageUrls.value).forEach(u => { if (u.startsWith('blob:')) URL.revokeObjectURL(u) })
    proxyImageUrls.value = {}
    return
  }
  for (let i = 0; i < urls.length; i++) {
    await loadImageViaProxy(urls[i])
  }
}, { immediate: true })

/** lightbox 열릴 때 해당 이미지 로드 */
watch(() => selectedImageUrl.value, async (url) => {
  lightboxImageSrc.value = ''
  if (url) {
    lightboxImageSrc.value = await loadImageViaProxy(url)
  }
}, { immediate: true })

onUnmounted(() => {
  Object.values(proxyImageUrls.value).forEach(u => { if (u?.startsWith('blob:')) URL.revokeObjectURL(u) })
  if (lightboxImageSrc.value?.startsWith('blob:')) URL.revokeObjectURL(lightboxImageSrc.value)
  // 트랙 #88 H5 (2026-05-13): 진행 중 페이지 이탈 시 타이머 누수 방지
  stopElapsedTimer()
})

const handleImageError = (event: Event) => {
  console.error('이미지 로드 실패:', event)
  const img = event.target as HTMLImageElement
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23f0f0f0" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3E이미지를 불러올 수 없습니다%3C/text%3E%3C/svg%3E'
}

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('ko-KR')
}

watch(
  [
    () => selectedServiceId.value,
    () => request.value.model,
    () => request.value.size,
    () => request.value.quality,
    () => request.value.numberOfImages
  ],
  () => {
    if (selectedServiceId.value) fetchEstimatedCost()
    else estimatedCost.value = null
  }
)

onMounted(() => {
  loadImageServices()
})
</script>

