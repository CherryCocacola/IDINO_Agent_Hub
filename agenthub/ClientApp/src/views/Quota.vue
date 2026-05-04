<template>
  <div class="page-content-wrap">
    <div class="page-header mb-4">
      <div>
        <h1 class="page-heading">할당량 관리 및 모니터링</h1>
        <p class="page-desc">사용자별 AI 서비스 할당량을 관리하고 사용량을 모니터링합니다.</p>
      </div>
    </div>

    <!-- 권한/오류 메시지 -->
    <div v-if="loadError" class="alert alert-danger alert-dismissible fade show" role="alert">
      {{ loadError }}
      <button type="button" class="btn-close" @click="loadError = null" aria-label="닫기"></button>
    </div>
    <div v-else-if="isViewingOwnQuotasOnly" class="alert alert-info mb-4">
      <i class="bi bi-info-circle me-2"></i>본인 할당량만 조회 중입니다. 전체 사용자 할당량 관리는 관리자 권한이 필요합니다.
    </div>

    <!-- 필터 -->
    <div class="ag-filter-bar mb-4">
      <div class="ag-search-wrap quota-user-wrap">
        <i class="bi bi-person ag-search-icon"></i>
        <input 
          type="text" 
          class="ag-search-input" 
          :value="getSelectedUserDisplay()"
          @focus="handleUserInputFocus"
          @blur="handleUserInputBlur"
          placeholder="사용자 선택..."
          autocomplete="off"
          readonly
          :disabled="isViewingOwnQuotasOnly"
          :class="{ 'cursor-pointer': !isViewingOwnQuotasOnly }"
        >
        <button 
          v-if="selectedUserId && !isViewingOwnQuotasOnly" 
          type="button" 
          class="ag-search-clear" 
          @mousedown.prevent="selectUser(null)"
          title="선택 해제"
        >
          <i class="bi bi-x-lg"></i>
        </button>
        <div 
          v-if="showUserDropdown && !isViewingOwnQuotasOnly" 
          class="quota-user-dropdown" 
          @mousedown.prevent
        >
          <input 
            type="text" 
            class="quota-dropdown-search" 
            v-model="userSearchText" 
            placeholder="사용자 검색 (이름, 이메일)"
            @mousedown.stop
            @focus.stop
          >
          <div class="quota-dropdown-list">
            <button 
              type="button" 
              class="quota-dropdown-item" 
              :class="{ active: !selectedUserId }"
              @mousedown.prevent="selectUser(null)"
            >
              전체 사용자
            </button>
            <div v-if="filteredUsers.length === 0 && userSearchText" class="quota-dropdown-empty">
              검색 결과가 없습니다.
            </div>
            <button
              v-for="user in filteredUsers" 
              :key="user.userId"
              type="button"
              class="quota-dropdown-item"
              :class="{ active: selectedUserId === user.userId }"
              @mousedown.prevent="selectUser(user.userId)"
            >
              {{ user.fullName }} ({{ user.email }})
            </button>
          </div>
        </div>
      </div>
      <div class="ag-filter-selects">
        <select class="ag-select" v-model="selectedServiceId" @change="loadQuotas">
          <option value="">모든 서비스</option>
          <option v-for="service in services" :key="service.serviceId" :value="service.serviceId">
            {{ service.serviceName }}
          </option>
        </select>
      </div>
      <div class="ag-filter-right">
        <button class="btn btn-outline-secondary btn-sm" @click="resetFilters">
          <i class="bi bi-arrow-clockwise me-1"></i>초기화
        </button>
        <span v-if="uniqueQuotas.length > 0" class="ag-count-label">
          <strong>{{ uniqueQuotas.length }}</strong>개 할당량
        </span>
      </div>
    </div>

    <!-- 통계 요약 (Dashboard 스타일) -->
    <div class="row g-4 mb-4">
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-graph-up"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">총 API 호출</p>
            <h2 class="stat-value">{{ stats.totalCalls }}</h2>
            <p class="stat-change">이번 달</p>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-success">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-currency-dollar"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">총 비용</p>
            <h2 class="stat-value">${{ stats.totalCost.toFixed(2) }}</h2>
            <p class="stat-change">이번 달</p>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-info">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-speedometer2"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">평균 사용률</p>
            <h2 class="stat-value">{{ stats.avgUsage }}%</h2>
            <p class="stat-change">전체 할당량 대비</p>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-danger">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-exclamation-triangle"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">한도 초과 경고</p>
            <h2 class="stat-value">{{ stats.warnings }}</h2>
            <p class="stat-change">사용자</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 서비스별 할당량 카드 -->
    <div class="row mb-4">
      <div v-if="loading" class="col-12 text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="mt-2 text-muted">할당량을 불러오는 중...</p>
      </div>
      <div v-else-if="uniqueQuotas.length === 0" class="col-12">
        <div class="card aiuiux-card">
          <div class="card-body text-center py-5">
            <i class="bi bi-pie-chart" style="font-size: 3rem; opacity: 0.3; color: var(--ai-text-muted);"></i>
            <p class="mt-3 mb-1 fw-600" style="color: var(--ai-text-primary);">
              {{ isViewingOwnQuotasOnly ? '아직 할당량이 설정되지 않았습니다.' : '등록된 할당량이 없습니다.' }}
            </p>
            <p class="small text-muted mb-0" v-if="isViewingOwnQuotasOnly">
              관리자에게 AI 서비스 할당량 설정을 요청하세요.
            </p>
            <p class="small text-muted mb-0" v-else>
              사용자·서비스를 선택한 후 <strong>수정</strong> 버튼으로 할당량을 설정할 수 있습니다.
            </p>
          </div>
        </div>
      </div>
      <div 
        v-else
        v-for="quota in uniqueQuotas" 
        :key="`${quota.userId}-${quota.serviceId}`"
        class="col-lg-6 mb-4"
      >
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <div>
              <h5 class="card-title mb-0">
                <i :class="getServiceIcon(quota.serviceName)" :style="{ color: getServiceColor(quota.serviceName) }" class="me-2"></i>
                {{ quota.serviceName }} 할당량
              </h5>
              <p class="card-subtitle mb-0 text-muted small" v-if="!selectedUserId && !isViewingOwnQuotasOnly">
                <i class="bi bi-person"></i> {{ quota.userEmail }}
              </p>
            </div>
            <button 
              v-if="!isViewingOwnQuotasOnly" 
              class="btn btn-sm btn-outline-primary" 
              @click="editQuota(quota)"
            >
              <i class="bi bi-pencil"></i> 수정
            </button>
          </div>
          <div class="card-body">
            <div class="mb-4">
              <div class="d-flex justify-content-between mb-2">
                <span class="text-muted">월간 사용량</span>
                <span class="fw-600">{{ quota.currentUsage }} / {{ quota.monthlyLimit }} 요청</span>
              </div>
              <div class="progress mb-2" style="height: 28px; border-radius: var(--ai-radius);">
                <div 
                  class="progress-bar" 
                  :class="getUsageBarClass(quota)"
                  :style="{ width: Math.min(getUsagePercentage(quota), 100) + '%' }"
                >
                  {{ getUsagePercentage(quota) }}%
                </div>
              </div>
              <small :class="getUsageTextClass(quota)">
                <i v-if="getUsagePercentage(quota) > 80" class="bi bi-exclamation-triangle me-1"></i>
                {{ getUsageText(quota) }}
              </small>
            </div>
            <div class="row g-2 text-center">
              <div class="col-4">
                <div class="p-3 rounded" style="background: var(--ai-bg-light);">
                  <h4 class="stat-value mb-0" style="font-size: 1.25rem;" :style="{ color: getServiceColor(quota.serviceName) }">
                    ${{ (quota.currentCost ?? 0).toFixed(2) }}
                  </h4>
                  <small class="text-muted">이번 달 비용</small>
                </div>
              </div>
              <div class="col-4">
                <div class="p-3 rounded" style="background: var(--ai-bg-light);">
                  <h4 class="stat-value mb-0" style="font-size: 1.25rem;" :style="{ color: getServiceColor(quota.serviceName) }">
                    {{ quota.dailyLimit }}
                  </h4>
                  <small class="text-muted">일일 한도</small>
                </div>
              </div>
              <div class="col-4">
                <div class="p-3 rounded" style="background: var(--ai-bg-light);">
                  <h4 class="stat-value mb-0" style="font-size: 1.25rem;" :style="{ color: getServiceColor(quota.serviceName) }">
                    {{ Math.max(quota.monthlyLimit - quota.currentUsage, 0) }}
                  </h4>
                  <small class="text-muted">남은 요청</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 할당량 수정 모달 -->
    <div class="modal fade" :class="{ show: showEditModal }" :style="{ display: showEditModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil"></i> 할당량 설정</h5>
            <button type="button" class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body" v-if="editingQuota">
            <form @submit.prevent="handleUpdateQuota">
              <div class="mb-3">
                <label class="form-label">서비스</label>
                <input type="text" class="form-control" :value="editingQuota.serviceName" readonly>
              </div>
              <div class="mb-3">
                <label class="form-label">월간 할당량</label>
                <input type="number" class="form-control" v-model.number="quotaForm.monthlyLimit" required>
                <small class="text-muted">최대 API 호출 횟수</small>
              </div>
              <div class="mb-3">
                <label class="form-label">일일 한도</label>
                <input type="number" class="form-control" v-model.number="quotaForm.dailyLimit" required>
                <small class="text-muted">하루 최대 API 호출 횟수</small>
              </div>
              <div class="mb-3">
                <label class="form-label">비용 제한 (월간)</label>
                <div class="input-group">
                  <span class="input-group-text">$</span>
                  <input type="number" class="form-control" v-model.number="quotaForm.costLimit" step="0.01" required>
                </div>
              </div>
              <div class="mb-3">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" v-model="quotaForm.isAlertEnabled" id="enable-alert">
                  <label class="form-check-label" for="enable-alert">
                    한도 80% 도달 시 알림
                  </label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showEditModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleUpdateQuota">
              <i class="bi bi-check-lg"></i> 저장
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showEditModal }" v-if="showEditModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { QuotaDto } from '@/types'
import type { UserDto } from '@/types'

interface ApiService {
  serviceId: number
  serviceName: string
}

interface QuotaStats {
  totalCalls: number
  totalCost: number
  avgUsage: number
  warnings: number
}

interface QuotaForm {
  monthlyLimit: number
  dailyLimit: number
  costLimit: number
  isAlertEnabled: boolean
}

const quotas = ref<QuotaDto[]>([])
const users = ref<UserDto[]>([])
const services = ref<ApiService[]>([])
const loading = ref(false)
const selectedUserId = ref<number | null>(null)
// "" (빈 문자열)로 초기화해야 select의 "모든 서비스" option과 v-model이 정확히 매칭됨
const selectedServiceId = ref<string | number>('')
const userSearchText = ref('')
const showUserDropdown = ref(false)
const showEditModal = ref(false)
const editingQuota = ref<QuotaDto | null>(null)
const isViewingOwnQuotasOnly = ref(false)
const loadError = ref<string | null>(null)

const quotaForm = ref<QuotaForm>({
  monthlyLimit: 0,
  dailyLimit: 0,
  costLimit: 0,
  isAlertEnabled: false
})

const filteredUsers = computed(() => {
  if (!userSearchText.value) {
    return users.value
  }
  const search = userSearchText.value.toLowerCase()
  return users.value.filter(user => 
    (user.fullName || '').toLowerCase().includes(search) ||
    (user.email || '').toLowerCase().includes(search) ||
    (user.department || '').toLowerCase().includes(search)
  )
})

const uniqueQuotas = computed(() => {
  // (userId, serviceId) 조합으로 중복 제거
  const seen = new Set<string>()
  return quotas.value.filter(quota => {
    const key = `${quota.userId}-${quota.serviceId}`
    if (seen.has(key)) {
      return false
    }
    seen.add(key)
    return true
  })
})

const stats = computed<QuotaStats>(() => {
  const totalCalls = uniqueQuotas.value.reduce((sum, q) => sum + q.currentUsage, 0)
  const totalCost = uniqueQuotas.value.reduce((sum, q) => sum + q.currentCost, 0)
  const totalLimit = uniqueQuotas.value.reduce((sum, q) => sum + q.monthlyLimit, 0)
  const avgUsage = totalLimit > 0 ? Math.round((totalCalls / totalLimit) * 100) : 0
  const warnings = uniqueQuotas.value.filter(q => getUsagePercentage(q) > 80).length

  return {
    totalCalls,
    totalCost,
    avgUsage,
    warnings
  }
})

const loadQuotas = async () => {
  try {
    loading.value = true
    loadError.value = null
    isViewingOwnQuotasOnly.value = false
    const params: Record<string, string | number> = {}
    if (selectedUserId.value != null) params.userId = selectedUserId.value
    const sid = selectedServiceId.value
    if (sid !== '' && sid != null && !isNaN(Number(sid)) && Number(sid) > 0) {
      params.serviceId = Number(sid)
    }

    try {
      const response = await api.get<QuotaDto[]>('/quota', { params })
      quotas.value = response.data || []
    } catch (err: any) {
      if (err.response?.status === 403) {
        const myRes = await api.get<QuotaDto[]>('/quota/my-quotas')
        quotas.value = myRes.data || []
        isViewingOwnQuotasOnly.value = true
      } else {
        throw err
      }
    }
  } catch (error: any) {
    console.error('Error loading quotas:', error)
    quotas.value = []
    loadError.value = error.response?.data?.message ?? '할당량 목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    const response = await api.get<UserDto[]>('/users')
    users.value = response.data || []
  } catch (error) {
    console.error('Error loading users:', error)
  }
}

const loadServices = async () => {
  try {
    const response = await api.get<ApiService[]>('/apiservices')
    services.value = response.data || []
  } catch (error) {
    console.error('Error loading services:', error)
    services.value = []
  }
}

const getSelectedUserDisplay = (): string => {
  if (!selectedUserId.value) return '전체 사용자'
  const user = users.value.find(u => u.userId === selectedUserId.value)
  if (user) return `${user.fullName} (${user.email})`
  return '전체 사용자'
}

const selectUser = (userId: number | null) => {
  selectedUserId.value = userId
  showUserDropdown.value = false
  userSearchText.value = ''
  loadQuotas()
}

const handleUserInputFocus = () => {
  showUserDropdown.value = true
  userSearchText.value = ''
}

const handleUserInputBlur = () => {
  setTimeout(() => {
    showUserDropdown.value = false
    userSearchText.value = ''
  }, 200)
}

const resetFilters = () => {
  selectedUserId.value = null
  selectedServiceId.value = ''
  userSearchText.value = ''
  showUserDropdown.value = false
  loadQuotas()
}

const editQuota = (quota: QuotaDto) => {
  editingQuota.value = quota
  quotaForm.value = {
    monthlyLimit: quota.monthlyLimit,
    dailyLimit: quota.dailyLimit,
    costLimit: quota.costLimit,
    isAlertEnabled: quota.isAlertEnabled
  }
  showEditModal.value = true
}

const handleUpdateQuota = async () => {
  if (!editingQuota.value) return

  try {
    await api.post(`/quota/user/${editingQuota.value.userId}/service/${editingQuota.value.serviceId}`, quotaForm.value)
    showEditModal.value = false
    editingQuota.value = null
    await loadQuotas()
  } catch (error: any) {
    console.error('Error updating quota:', error)
    const msg = error.response?.status === 403
      ? '할당량 수정 권한이 없습니다. 관리자만 수정할 수 있습니다.'
      : (error.response?.data?.message || '할당량 수정 중 오류가 발생했습니다.')
    alert(msg)
  }
}

const getUsagePercentage = (quota: QuotaDto): number => {
  if (quota.monthlyLimit === 0) return 0
  return Math.round((quota.currentUsage / quota.monthlyLimit) * 100)
}

const getUsageBarClass = (quota: QuotaDto): string => {
  const percentage = getUsagePercentage(quota)
  if (percentage >= 90) return 'bg-danger'
  if (percentage >= 80) return 'bg-warning'
  return `bg-${getServiceColorClass(quota.serviceName)}`
}

const getUsageTextClass = (quota: QuotaDto): string => {
  const percentage = getUsagePercentage(quota)
  if (percentage >= 90) return 'text-danger'
  if (percentage >= 80) return 'text-warning'
  return 'text-muted'
}

const getUsageText = (quota: QuotaDto): string => {
  const percentage = getUsagePercentage(quota)
  if (percentage >= 90) return '⚠️ 한도 초과 임박'
  if (percentage >= 80) return '⚠️ 한도 근접 경고'
  return `일일 한도: ${quota.dailyLimit} 요청 | 남은 요청: ${quota.monthlyLimit - quota.currentUsage}`
}

const getServiceIcon = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return 'bi bi-chat-square-text'
  if (name.includes('claude')) return 'bi bi-robot'
  if (name.includes('cursor')) return 'bi bi-code-slash'
  if (name.includes('copilot')) return 'bi bi-github'
  return 'bi bi-diagram-3'
}

const getServiceColor = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return '#0dcaf0'
  if (name.includes('claude')) return '#0d6efd'
  if (name.includes('cursor')) return '#ffc107'
  if (name.includes('copilot')) return '#6c757d'
  return '#6c757d'
}

const getServiceColorClass = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return 'info'
  if (name.includes('claude')) return 'primary'
  if (name.includes('cursor')) return 'warning'
  if (name.includes('copilot')) return 'secondary'
  return 'secondary'
}

onMounted(() => {
  loadQuotas()
  loadUsers()
  loadServices()
})
</script>

<style scoped>
.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}

.quota-user-wrap {
  min-width: 220px;
  max-width: 320px;
}

.cursor-pointer {
  cursor: pointer;
}

.quota-user-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--ai-bg-card);
  border: 1.5px solid var(--ai-border);
  border-radius: var(--ai-radius-lg);
  padding: 10px;
  z-index: 1000;
  box-shadow: var(--ai-shadow-lg);
  margin-top: 6px;
}

.quota-dropdown-search {
  width: 100%;
  height: 36px;
  padding: 0 12px;
  border: 1.5px solid var(--ai-border);
  border-radius: var(--ai-radius);
  background: var(--ai-bg-card);
  font-size: 13px;
  color: var(--ai-text-primary);
  outline: none;
  margin-bottom: 8px;
}

.quota-dropdown-search:focus {
  border-color: var(--ai-primary);
}

.quota-dropdown-search::placeholder {
  color: var(--ai-text-muted);
}

.quota-dropdown-list {
  max-height: 220px;
  overflow-y: auto;
}

.quota-dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  text-align: left;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--ai-radius);
  transition: background 0.15s;
  font-size: 13px;
  color: var(--ai-text-primary);
}

.quota-dropdown-item:hover {
  background: var(--ai-bg-light);
}

.quota-dropdown-item.active {
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  font-weight: 600;
}

.quota-dropdown-empty {
  padding: 12px;
  font-size: 12px;
  color: var(--ai-text-muted);
}
</style>
