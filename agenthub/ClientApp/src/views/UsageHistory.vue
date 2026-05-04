<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">사용 내역</h1>
        <p class="page-desc mb-0">마지막 조회: {{ lastQueryTime || '—' }}</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-success btn-sm" @click="exportToExcel">
          <i class="bi bi-file-excel me-1"></i> Excel 내보내기
        </button>
        <button class="btn btn-outline-secondary btn-sm ms-2" @click="exportToCSV">
          <i class="bi bi-filetype-csv me-1"></i> CSV 내보내기
        </button>
      </div>
    </div>

    <form @submit.prevent="applyFilters" class="mb-4">
      <div class="ag-filter-bar">
        <div class="ag-search-wrap">
          <i class="bi bi-search ag-search-icon"></i>
          <input 
            type="text" 
            class="ag-search-input" 
            v-model="filters.search"
            placeholder="프롬프트 내용 검색..."
          >
          <button 
            type="button" 
            class="ag-search-clear" 
            v-show="filters.search" 
            @click="filters.search = ''"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="ag-filter-selects">
          <input type="date" class="ag-filter-date" v-model="filters.startDate" title="시작일">
          <input type="date" class="ag-filter-date" v-model="filters.endDate" title="종료일">
          <select class="ag-select" v-model="filters.userId">
            <option value="">전체 사용자</option>
            <option v-for="user in users" :key="user.userId" :value="user.userId">
              {{ user?.fullName || '-' }}
            </option>
          </select>
          <select class="ag-select" v-model="filters.serviceId">
            <option value="">전체 서비스</option>
            <option v-for="service in services" :key="service.serviceId" :value="service.serviceId">
              {{ service.serviceName }}
            </option>
          </select>
          <select class="ag-select" v-model="filters.status">
            <option value="">상태</option>
            <option value="success">성공</option>
            <option value="error">실패</option>
          </select>
        </div>
        <div class="ag-filter-right">
          <button type="submit" class="btn btn-primary btn-sm">
            <i class="bi bi-search me-1"></i>검색
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" @click="resetFilters">
            <i class="bi bi-arrow-clockwise me-1"></i>초기화
          </button>
        </div>
      </div>
    </form>

    <!-- KPI Row (모니터링 스타일) -->
    <div class="row g-3 mb-4">
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.totalCalls.toLocaleString() }}</div>
          <div class="kpi-label">총 호출 수</div>
        </div>
      </div>
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">{{ formatTokens(stats.totalTokens) }}</div>
          <div class="kpi-label">총 토큰</div>
        </div>
      </div>
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">${{ stats.totalCost.toFixed(2) }}</div>
          <div class="kpi-label">총 비용</div>
        </div>
      </div>
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.avgResponseTime }}초</div>
          <div class="kpi-label">평균 응답시간</div>
        </div>
      </div>
    </div>

    <!-- 사용 내역 테이블 (모니터링 스타일) -->
    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
        <div>
          <h5 class="card-title mb-0">사용 내역</h5>
          <p class="card-subtitle mb-0">API 호출 이력</p>
        </div>
        <div class="d-flex gap-2 align-items-center">
          <select class="form-select form-select-sm" style="width:120px" v-model.number="pageSize">
            <option :value="10">10개씩</option>
            <option :value="20">20개씩</option>
            <option :value="50">50개씩</option>
            <option :value="100">100개씩</option>
          </select>
        </div>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover mb-0 aiuiux-table">
            <thead>
              <tr>
                <th>일시</th>
                <th>사용자</th>
                <th>서비스/모델</th>
                <th>프롬프트</th>
                <th>토큰</th>
                <th>응답시간</th>
                <th>비용</th>
                <th>상태</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="9" class="text-center py-5">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">로딩 중...</span>
                  </div>
                  <p class="mt-2 text-muted">데이터를 불러오는 중...</p>
                </td>
              </tr>
              <tr v-else-if="paginatedUsages.length === 0">
                <td colspan="9" class="text-center py-5 text-muted">
                  <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
                  <p class="mt-3">데이터가 없습니다</p>
                </td>
              </tr>
              <tr v-else v-for="usage in paginatedUsages" :key="usage.usageId">
                <td class="text-muted fs-xs">{{ formatDateTime(usage.requestTime) }}</td>
                <td>{{ usage.userName || '-' }}</td>
                <td>
                  <div>
                    <strong>{{ usage.serviceName }}</strong><br>
                    <small class="text-muted">{{ usage.model || '-' }}</small>
                  </div>
                </td>
                <td>
                  <div class="text-truncate-ellipsis" :title="usage.prompt || '-'">
                    {{ truncateText(usage.prompt || '-', 50) }}
                  </div>
                </td>
                <td>{{ (usage.tokensUsed || 0).toLocaleString() }}</td>
                <td>{{ formatResponseTime(usage.responseTime || 0) }}</td>
                <td>${{ (usage.requestCost ?? 0).toFixed(4) }}</td>
                <td>
                  <span
                    class="status-badge"
                    :class="(usage.statusCode ?? 0) === 200 ? 'status-online' : 'status-error'"
                  >
                    {{ (usage.statusCode ?? 0) === 200 ? '성공' : '실패' }}
                  </span>
                </td>
                <td>
                  <button class="uh-detail-btn" @click="viewDetail(usage)">
                    <i class="bi bi-eye-fill"></i>
                    <span>상세</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="card-footer bg-transparent border-top">
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 px-1">
          <small class="uh-page-info">
            <strong>{{ (currentPage - 1) * pageSize + 1 }}–{{ Math.min(currentPage * pageSize, totalUsageCount) }}</strong>
            / 전체 <strong>{{ totalUsageCount.toLocaleString() }}</strong>건
          </small>
          <nav>
            <ul class="pagination pagination-sm justify-content-center mb-0">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link uh-page-nav" href="#" @click.prevent="goToPage(1)" title="처음">
                  <i class="bi bi-chevron-double-left"></i>
                </a>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" href="#" @click.prevent="goToPage(currentPage - 1)">이전</a>
              </li>
              <li
                v-for="(page, idx) in displayedPages"
                :key="idx"
                class="page-item"
                :class="{ active: page === currentPage, 'uh-page-ellipsis': page === '...' }"
              >
                <a class="page-link" href="#" @click.prevent="typeof page === 'number' && goToPage(page)">{{ page }}</a>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <a class="page-link" href="#" @click.prevent="goToPage(currentPage + 1)">다음</a>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <a class="page-link uh-page-nav" href="#" @click.prevent="goToPage(totalPages)" title="마지막">
                  <i class="bi bi-chevron-double-right"></i>
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>

    <!-- 상세 보기 모달 -->
    <div class="modal fade" :class="{ show: showDetailModal }" :style="{ display: showDetailModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content uh-modal" v-if="selectedUsage">

          <!-- 모달 헤더 -->
          <div class="uh-modal-hdr">
            <div class="uh-modal-hdr-left">
              <div class="uh-modal-icon">
                <i class="bi bi-activity"></i>
              </div>
              <div>
                <h5 class="uh-modal-title">사용 내역 상세</h5>
                <p class="uh-modal-subtitle">{{ formatDateTime(selectedUsage.requestTime) }}</p>
              </div>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="status-badge" :class="(selectedUsage.statusCode ?? 0) === 200 ? 'status-online' : 'status-error'">
                <i :class="(selectedUsage.statusCode ?? 0) === 200 ? 'bi bi-check-circle-fill' : 'bi bi-x-circle-fill'" class="me-1"></i>
                {{ (selectedUsage.statusCode ?? 0) === 200 ? '성공' : '실패' }}
              </span>
              <button type="button" class="uh-modal-close-btn" @click="showDetailModal = false">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          <!-- 모달 바디 -->
          <div class="uh-modal-body">
            <!-- 기본 정보 그리드 -->
            <div class="uh-info-grid">
              <div class="uh-info-item">
                <span class="uh-info-label"><i class="bi bi-person-fill"></i> 사용자</span>
                <span class="uh-info-value">{{ selectedUsage.userName || '-' }}</span>
              </div>
              <div class="uh-info-item">
                <span class="uh-info-label"><i class="bi bi-cloud-fill"></i> 서비스</span>
                <span class="uh-info-value">{{ selectedUsage.serviceName }}</span>
              </div>
              <div class="uh-info-item">
                <span class="uh-info-label"><i class="bi bi-cpu-fill"></i> 모델</span>
                <span class="uh-info-value">{{ selectedUsage.model || '-' }}</span>
              </div>
              <div class="uh-info-item">
                <span class="uh-info-label"><i class="bi bi-hash"></i> HTTP 상태</span>
                <span class="uh-info-value">{{ selectedUsage.statusCode ?? '-' }}</span>
              </div>
            </div>

            <!-- 사용량 통계 카드 -->
            <div class="uh-usage-stats">
              <div class="uh-usage-stat">
                <div class="uh-usage-stat-icon" style="background:rgba(79,70,229,.1);color:var(--ai-primary);">
                  <i class="bi bi-chat-dots-fill"></i>
                </div>
                <div>
                  <div class="uh-usage-stat-val">{{ (selectedUsage.tokensUsed || 0).toLocaleString() }}</div>
                  <div class="uh-usage-stat-lbl">토큰 사용</div>
                </div>
              </div>
              <div class="uh-usage-stat">
                <div class="uh-usage-stat-icon" style="background:rgba(16,185,129,.1);color:#059669;">
                  <i class="bi bi-currency-dollar"></i>
                </div>
                <div>
                  <div class="uh-usage-stat-val">${{ (selectedUsage.requestCost ?? 0).toFixed(4) }}</div>
                  <div class="uh-usage-stat-lbl">비용</div>
                </div>
              </div>
              <div class="uh-usage-stat">
                <div class="uh-usage-stat-icon" style="background:rgba(14,165,233,.1);color:#0284C7;">
                  <i class="bi bi-stopwatch-fill"></i>
                </div>
                <div>
                  <div class="uh-usage-stat-val">{{ formatResponseTime(selectedUsage.responseTime || 0) }}</div>
                  <div class="uh-usage-stat-lbl">응답 시간</div>
                </div>
              </div>
            </div>

            <!-- 프롬프트 -->
            <div class="uh-modal-section" v-if="selectedUsage.prompt">
              <div class="uh-modal-section-title">
                <i class="bi bi-chat-text-fill"></i> 프롬프트
              </div>
              <pre class="uh-modal-code">{{ selectedUsage.prompt }}</pre>
            </div>

            <!-- 오류 메시지 -->
            <div class="uh-modal-section" v-if="selectedUsage.errorMessage">
              <div class="uh-modal-section-title" style="color:var(--ai-danger)">
                <i class="bi bi-exclamation-triangle-fill"></i> 오류 메시지
              </div>
              <pre class="uh-modal-code uh-modal-code-error">{{ selectedUsage.errorMessage }}</pre>
            </div>
          </div>

          <!-- 모달 푸터 -->
          <div class="uh-modal-ftr">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="showDetailModal = false">
              <i class="bi bi-x me-1"></i>닫기
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showDetailModal }" v-if="showDetailModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/services/api'
import type { UserDto, ApiServiceDto, ApiUsageDto } from '@/types'

type ApiUsage = ApiUsageDto

interface UsageFilters {
  startDate: string
  endDate: string
  userId: string
  serviceId: string
  status: string
  search: string
}

interface UsageStats {
  totalCalls: number
  totalTokens: number
  totalCost: number
  avgResponseTime: number
}

const usages = ref<ApiUsage[]>([])
const totalUsageCount = ref(0)
const users = ref<UserDto[]>([])
const services = ref<ApiServiceDto[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const showDetailModal = ref(false)
const selectedUsage = ref<ApiUsage | null>(null)
const lastQueryTime = ref('')

const filters = ref<UsageFilters>({
  startDate: '',
  endDate: '',
  userId: '',
  serviceId: '',
  status: '',
  search: ''
})

const stats = ref<UsageStats>({
  totalCalls: 0,
  totalTokens: 0,
  totalCost: 0,
  avgResponseTime: 0
})

/**
 * KPI 집계 — 새 /analytics/usage-summary 엔드포인트 사용
 * SQL aggregate(COUNT/SUM/AVG) 단일 쿼리로 처리 → 수만 건도 빠름
 * 기존 take:10000 방식 대비 수십 배 속도 개선
 */
const loadStats = async () => {
  try {
    const params: Record<string, string | number> = {}
    if (filters.value.startDate) {
      params.startDate = new Date(filters.value.startDate).toISOString()
    }
    if (filters.value.endDate) {
      params.endDate = new Date(filters.value.endDate + 'T23:59:59').toISOString()
    }
    if (filters.value.userId) {
      params.userId = parseInt(filters.value.userId)
    }
    if (filters.value.serviceId) {
      params.serviceId = parseInt(filters.value.serviceId)
    }
    if (filters.value.status) {
      params.statusCode = filters.value.status === 'success' ? 200 : 500
    }

    const response = await api.get<{
      totalCalls: number
      totalTokens: number
      totalCost: number
      avgResponseTime: number
    }>('/analytics/usage-summary', { params })

    const data = response.data
    stats.value = {
      totalCalls:      data?.totalCalls      ?? 0,
      totalTokens:     data?.totalTokens     ?? 0,
      totalCost:       data?.totalCost       ?? 0,
      avgResponseTime: data?.avgResponseTime ?? 0
    }
  } catch (error) {
    console.error('Error loading stats:', error)
    // 통계 로드 실패 시 totalUsageCount로 totalCalls만 채움
    stats.value = { ...stats.value, totalCalls: totalUsageCount.value }
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(totalUsageCount.value / pageSize.value)))

/** 윈도우 페이지네이션: 최대 9개 버튼만 표시 */
const displayedPages = computed((): (number | '...')[] => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | '...')[] = [1]
  const left = Math.max(2, current - 2)
  const right = Math.min(total - 1, current + 2)
  if (left > 2) pages.push('...')
  for (let i = left; i <= right; i++) pages.push(i)
  if (right < total - 1) pages.push('...')
  pages.push(total)
  return pages
})

const paginatedUsages = computed(() => usages.value)

const loadUsages = async () => {
  try {
    loading.value = true
    
    const params: any = {
      skip: (currentPage.value - 1) * pageSize.value,
      take: pageSize.value
    }
    
    if (filters.value.startDate) {
      params.startDate = new Date(filters.value.startDate).toISOString()
    }
    if (filters.value.endDate) {
      params.endDate = new Date(filters.value.endDate + 'T23:59:59').toISOString()
    }
    if (filters.value.userId) {
      params.userId = parseInt(filters.value.userId)
    }
    if (filters.value.serviceId) {
      params.serviceId = parseInt(filters.value.serviceId)
    }
    if (filters.value.status) {
      params.statusCode = filters.value.status === 'success' ? 200 : 500
    }
    if (filters.value.search) {
      params.search = filters.value.search
    }
    
    // 테이블 데이터 먼저 로드 (통계는 별도 비동기)
    const usageResponse = await api.get<{ items: ApiUsage[]; totalCount: number }>('/analytics/usage-history', { 
      params,
      timeout: 30000
    })
    const data = usageResponse.data
    usages.value = data?.items || []
    totalUsageCount.value = data?.totalCount ?? 0
    lastQueryTime.value = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    
    // 통계는 백그라운드에서 로드 (테이블 표시를 막지 않음)
    loadStats()
  } catch (error: any) {
    console.error('Error loading usages:', error)
    usages.value = []
    const msg = error?.response?.data?.message || error?.message || '데이터를 불러오는데 실패했습니다.'
    if (error?.response?.status === 403) {
      alert('사용 내역 조회 권한이 없습니다. (Admin 역할 필요)')
    } else {
      alert(msg)
    }
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
    const response = await api.get<ApiServiceDto[]>('/apiservices')
    services.value = response.data || []
  } catch (error) {
    console.error('Error loading services:', error)
  }
}

const applyFilters = () => {
  currentPage.value = 1
  loadUsages()
}

const resetFilters = () => {
  const today = new Date()
  const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
  
  filters.value = {
    startDate: lastMonth.toISOString().split('T')[0],
    endDate: today.toISOString().split('T')[0],
    userId: '',
    serviceId: '',
    status: '',
    search: ''
  }
  currentPage.value = 1
  loadUsages()
}

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadUsages()
  }
}

const viewDetail = (usage: ApiUsage) => {
  selectedUsage.value = usage
  showDetailModal.value = true
}

const exportToExcel = () => {
  alert('Excel 내보내기 기능 (구현 필요)')
}

const exportToCSV = () => {
  const csv = [
    ['일시', '사용자', '서비스', '모델', '토큰', '응답시간', '비용', '상태'].join(','),
    ...paginatedUsages.value.map(u => [
      formatDateTime(u.requestTime),
      u.userName || '',
      u.serviceName,
      u.model || '',
      (u.tokensUsed || 0).toString(),
      formatResponseTime(u.responseTime),
      (u.requestCost ?? 0).toFixed(4),
      u.statusCode === 200 ? '성공' : '실패'
    ].join(','))
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `usage_history_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('ko-KR')
}

const formatResponseTime = (ms: number | undefined): string => {
  if (!ms) return '0.00초'
  return (ms / 1000).toFixed(2) + '초'
}

const formatTokens = (tokens: number): string => {
  if (tokens >= 1000000) return (tokens / 1000000).toFixed(1) + 'M'
  if (tokens >= 1000) return (tokens / 1000).toFixed(1) + 'K'
  return tokens.toString()
}

const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

watch(pageSize, () => {
  currentPage.value = 1
  loadUsages()
})

onMounted(() => {
  const today = new Date()
  const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
  
  filters.value.endDate = today.toISOString().split('T')[0]
  filters.value.startDate = lastMonth.toISOString().split('T')[0]
  
  loadUsages()
  loadUsers()
  loadServices()
})
</script>

<style scoped>
/* ── 상세 버튼 ── */
.uh-detail-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 11px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid var(--ai-border);
  border-radius: 20px;
  background: var(--ai-bg-light);
  color: var(--ai-text-secondary);
  cursor: pointer;
  transition: all 0.18s ease;
  white-space: nowrap;
}
.uh-detail-btn i { font-size: 11px; }
.uh-detail-btn:hover {
  border-color: var(--ai-primary);
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(79,70,229,.15);
}
.uh-detail-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

/* ── 페이지네이션 ── */
.uh-page-info {
  font-size: 12px;
  color: var(--ai-text-muted);
}
.uh-page-info strong { color: var(--ai-text-primary); font-weight: 600; }
.uh-page-nav i { font-size: 10px; }
.uh-page-ellipsis .page-link {
  pointer-events: none;
  color: var(--ai-text-muted);
  background: transparent;
  border-color: transparent;
  cursor: default;
}

/* ── 모달 ── */
.uh-modal {
  border: none;
  border-radius: var(--ai-radius-lg);
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.18);
}

/* 헤더 */
.uh-modal-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--ai-bg-card) 0%, var(--ai-bg-light) 100%);
  border-bottom: 1px solid var(--ai-border);
}
.uh-modal-hdr-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.uh-modal-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.uh-modal-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--ai-text-primary);
  margin: 0;
}
.uh-modal-subtitle {
  font-size: 11px;
  color: var(--ai-text-muted);
  margin: 3px 0 0;
}
.uh-modal-close-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--ai-border);
  border-radius: 8px;
  background: var(--ai-bg-card);
  color: var(--ai-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
  font-size: 12px;
}
.uh-modal-close-btn:hover {
  border-color: var(--ai-primary);
  color: var(--ai-primary);
  background: var(--ai-primary-light);
}

/* 바디 */
.uh-modal-body { padding: 24px; }

/* 기본 정보 그리드 */
.uh-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
}
.uh-info-item {
  background: var(--ai-bg-light);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  padding: 12px 14px;
}
.uh-info-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: var(--ai-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 5px;
}
.uh-info-label i { margin-right: 4px; opacity: .7; }
.uh-info-value {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--ai-text-primary);
  word-break: break-all;
}

/* 사용량 통계 카드 */
.uh-usage-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.uh-usage-stat {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--ai-bg-light);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  padding: 14px 16px;
}
.uh-usage-stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}
.uh-usage-stat-val {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: var(--ai-text-primary);
  line-height: 1;
  margin-bottom: 3px;
}
.uh-usage-stat-lbl {
  display: block;
  font-size: 11px;
  color: var(--ai-text-muted);
}

/* 섹션 */
.uh-modal-section { margin-bottom: 16px; }
.uh-modal-section-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--ai-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-bottom: 8px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--ai-border);
}
.uh-modal-section-title i { margin-right: 6px; }
.uh-modal-code {
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  background: var(--ai-bg-light);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  padding: 14px 16px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 240px;
  overflow-y: auto;
  color: var(--ai-text-primary);
  margin: 0;
}
.uh-modal-code-error {
  background: rgba(239,68,68,.05);
  border-color: rgba(239,68,68,.2);
  color: #DC2626;
}

/* 푸터 */
.uh-modal-ftr {
  padding: 14px 24px;
  background: var(--ai-bg-light);
  border-top: 1px solid var(--ai-border);
  display: flex;
  justify-content: flex-end;
}
</style>
