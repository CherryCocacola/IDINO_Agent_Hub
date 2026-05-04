<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">감사 로그</h1>
        <p class="page-desc">모든 시스템 활동을 추적하고 감사합니다</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-success btn-sm" @click="exportLogs">
          <i class="bi bi-download"></i> 로그 내보내기
        </button>
        <button class="btn btn-primary btn-sm ms-2" @click="loadLogs">
          <i class="bi bi-arrow-clockwise"></i> 새로고침
        </button>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-9">
        <form @submit.prevent="applyFilters" class="mb-4">
          <div class="ag-filter-bar">
            <div class="ag-search-wrap">
              <i class="bi bi-search ag-search-icon"></i>
              <input
                type="text"
                class="ag-search-input"
                v-model="filters.search"
                placeholder="IP 주소 또는 상세 내용 검색..."
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
              <select class="ag-select" v-model="filters.action">
                <option value="">활동 유형</option>
                <option value="POST /api/auth/login">로그인</option>
                <option value="POST">생성</option>
                <option value="PUT">수정</option>
                <option value="DELETE">삭제</option>
              </select>
              <select class="ag-select" v-model="filters.result">
                <option value="">결과</option>
                <option value="success">성공</option>
                <option value="failure">실패</option>
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

        <!-- 로그 테이블 -->
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">활동 로그</h5>
            <!-- ── 총 개수 칩 ── -->
            <div class="al-count-chip">
              <span class="al-count-icon"><i class="bi bi-list-ul"></i></span>
              <span class="al-count-text">총</span>
              <strong class="al-count-num">{{ totalLogCount.toLocaleString() }}</strong>
              <span class="al-count-unit">건</span>
            </div>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0 aiuiux-table">
                <thead>
                  <tr>
                    <th>일시 · 사용자</th>
                    <th>활동</th>
                    <th>대상</th>
                    <th>IP 주소</th>
                    <th>결과</th>
                    <th class="text-end">작업</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="log in paginatedLogs"
                    :key="log.logId"
                    class="log-row"
                    @click="viewLogDetail(log)"
                  >
                    <td>
                      <div class="table-name-cell">
                        <div class="table-cell-icon icon-date">
                          <i class="bi bi-calendar3"></i>
                        </div>
                        <div class="table-cell-meta">
                          <p class="table-cell-title mb-0">{{ formatDateTime(log.createdAt) }}</p>
                          <p class="table-cell-subtitle mb-0">{{ log.userName || '-' }}</p>
                        </div>
                      </div>
                    </td>

                    <!-- ── 활동 컬럼 ── -->
                    <td>
                      <div class="al-action-badge" :class="getActionBadgeType(log.activityType)">
                        <i :class="getActionIcon(log.activityType)"></i>
                        <span>{{ getActionLabel(log.activityType) }}</span>
                      </div>
                    </td>

                    <td><span class="table-num-cell muted">{{ log.entityType || '-' }}</span></td>
                    <td><small class="text-muted font-mono">{{ log.ipAddress || '-' }}</small></td>

                    <!-- ── 결과 컬럼 ── -->
                    <td>
                      <div class="al-result-badge" :class="log.isSuccess === false ? 'al-result-fail' : 'al-result-success'">
                        <i :class="log.isSuccess === false ? 'bi bi-x-circle-fill' : 'bi bi-check-circle-fill'"></i>
                        <span>{{ log.isSuccess === false ? '실패' : '성공' }}</span>
                      </div>
                    </td>

                    <!-- ── 작업 컬럼 ── -->
                    <td class="text-end">
                      <button class="al-detail-btn" @click.stop="viewLogDetail(log)" title="상세보기">
                        <i class="bi bi-eye-fill"></i>
                        <span>상세</span>
                      </button>
                    </td>
                  </tr>
                  <!-- 로딩/빈 상태 -->
                  <tr v-if="loading">
                    <td colspan="6" class="text-center py-5">
                      <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                      <span class="text-muted">로딩 중...</span>
                    </td>
                  </tr>
                  <tr v-else-if="paginatedLogs.length === 0">
                    <td colspan="6" class="text-center py-5 text-muted">
                      <i class="bi bi-inbox" style="font-size: 1.8rem; opacity:.4; display:block; margin-bottom:8px;"></i>
                      로그가 없습니다
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="card-footer bg-transparent border-top">
            <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 px-1">
              <small class="al-page-info">
                <strong>{{ (currentPage - 1) * itemsPerPage + 1 }}–{{ Math.min(currentPage * itemsPerPage, totalLogCount) }}</strong>
                / 전체 <strong>{{ totalLogCount.toLocaleString() }}</strong>건
              </small>
              <nav>
                <ul class="pagination pagination-sm justify-content-center mb-0">
                  <li class="page-item" :class="{ disabled: currentPage === 1 }">
                    <a class="page-link al-page-nav" href="#" @click.prevent="goToPage(1)" title="처음">
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
                    :class="{ active: page === currentPage, 'al-page-ellipsis': page === '...' }"
                  >
                    <a class="page-link" href="#" @click.prevent="typeof page === 'number' && goToPage(page)">{{ page }}</a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                    <a class="page-link" href="#" @click.prevent="goToPage(currentPage + 1)">다음</a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                    <a class="page-link al-page-nav" href="#" @click.prevent="goToPage(totalPages)" title="마지막">
                      <i class="bi bi-chevron-double-right"></i>
                    </a>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
      </div>

      <!-- 우측: 통계 & 이상 징후 -->
      <div class="col-lg-3">
        <!-- 통계 -->
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="card-title mb-0"><i class="bi bi-bar-chart me-2"></i>오늘의 활동</h6>
          </div>
          <div class="card-body">
            <ul class="activity-stat-list">
              <li class="activity-stat-item">
                <span class="label">로그인</span>
                <span class="value text-success">{{ todayStats.login }}</span>
              </li>
              <li class="activity-stat-item">
                <span class="label">생성</span>
                <span class="value text-primary">{{ todayStats.create }}</span>
              </li>
              <li class="activity-stat-item">
                <span class="label">수정</span>
                <span class="value text-info">{{ todayStats.update }}</span>
              </li>
              <li class="activity-stat-item">
                <span class="label">삭제</span>
                <span class="value text-warning">{{ todayStats.delete }}</span>
              </li>
              <li class="activity-stat-item">
                <span class="label">실패</span>
                <span class="value text-danger">{{ todayStats.failure }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- 이상 징후 -->
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="card-title mb-0"><i class="bi bi-exclamation-triangle me-2"></i>이상 징후</h6>
          </div>
          <div class="card-body p-0">
            <div v-if="anomalies.length === 0" class="text-center text-muted py-4 px-3">
              <i class="bi bi-check-circle" style="font-size: 2rem;"></i>
              <p class="mt-2 mb-0">이상 징후 없음</p>
            </div>
            <div v-else class="alert-list">
              <div
                v-for="anomaly in anomalies"
                :key="anomaly.id"
                class="alert-item alert-item-warning"
              >
                <div class="alert-icon"><i class="bi bi-exclamation-triangle"></i></div>
                <div class="alert-content">
                  <p class="alert-title">{{ anomaly.type }}</p>
                  <p class="alert-desc mb-0">{{ anomaly.message }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 로그 상세 모달 -->
    <div class="modal fade" :class="{ show: showDetailModal }" :style="{ display: showDetailModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content al-modal" v-if="selectedLog">

          <!-- 모달 헤더 -->
          <div class="al-modal-hdr">
            <div class="al-modal-hdr-left">
              <div class="al-modal-icon">
                <i :class="getActionIcon(selectedLog.activityType)"></i>
              </div>
              <div>
                <h5 class="al-modal-title">활동 로그 상세</h5>
                <p class="al-modal-subtitle">{{ formatDateTime(selectedLog.createdAt) }}</p>
              </div>
            </div>
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <div class="al-action-badge" :class="getActionBadgeType(selectedLog.activityType)">
                <i :class="getActionIcon(selectedLog.activityType)"></i>
                <span>{{ getActionLabel(selectedLog.activityType) }}</span>
              </div>
              <div class="al-result-badge" :class="selectedLog.isSuccess === false ? 'al-result-fail' : 'al-result-success'">
                <i :class="selectedLog.isSuccess === false ? 'bi bi-x-circle-fill' : 'bi bi-check-circle-fill'"></i>
                <span>{{ selectedLog.isSuccess === false ? '실패' : '성공' }}</span>
              </div>
              <button type="button" class="al-modal-close-btn" @click="showDetailModal = false">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          <!-- 모달 바디 -->
          <div class="al-modal-body">
            <!-- 기본 정보 그리드 -->
            <div class="al-info-grid">
              <div class="al-info-item">
                <span class="al-info-label"><i class="bi bi-person-fill"></i> 사용자</span>
                <span class="al-info-value">{{ selectedLog.userName || '-' }}</span>
              </div>
              <div class="al-info-item">
                <span class="al-info-label"><i class="bi bi-hdd-stack-fill"></i> 대상 리소스</span>
                <span class="al-info-value">{{ selectedLog.entityType || '-' }}</span>
              </div>
              <div class="al-info-item">
                <span class="al-info-label"><i class="bi bi-wifi"></i> IP 주소</span>
                <span class="al-info-value font-mono">{{ selectedLog.ipAddress || '-' }}</span>
              </div>
              <div class="al-info-item">
                <span class="al-info-label"><i class="bi bi-hash"></i> 상태 코드</span>
                <span class="al-info-value">{{ selectedLog.statusCode ?? '-' }}</span>
              </div>
            </div>

            <!-- 설명 -->
            <div class="al-modal-section" v-if="selectedLog.description">
              <div class="al-modal-section-title">
                <i class="bi bi-card-text"></i> 설명
              </div>
              <div class="al-modal-section-body">{{ selectedLog.description }}</div>
            </div>

            <!-- 상세 내용 (JSON/raw) -->
            <div class="al-modal-section" v-if="selectedLog.details">
              <div class="al-modal-section-title">
                <i class="bi bi-code-square"></i> 상세 내용
              </div>
              <pre class="al-modal-code">{{ selectedLog.details }}</pre>
            </div>
          </div>

          <!-- 모달 푸터 -->
          <div class="al-modal-ftr">
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
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { UserDto } from '@/types'

interface ActivityLog {
  logId: number
  userId?: number
  userName?: string
  activityType: string
  entityType?: string
  entityId?: number
  description?: string
  details?: string
  ipAddress?: string
  userAgent?: string
  isSuccess?: boolean
  statusCode?: number
  createdAt: string
}

interface LogFilters {
  startDate: string
  endDate: string
  userId: string
  action: string
  result: string
  search: string
}

interface TodayStats {
  login: number
  create: number
  update: number
  delete: number
  failure: number
}

interface Anomaly {
  id: string
  type: string
  message: string
}

const logs = ref<ActivityLog[]>([])
const totalLogCount = ref(0)
const users = ref<UserDto[]>([])
const loading = ref(false)
const currentPage = ref(1)
const itemsPerPage = 20
const showDetailModal = ref(false)
const selectedLog = ref<ActivityLog | null>(null)

const filters = ref<LogFilters>({
  startDate: '',
  endDate: '',
  userId: '',
  action: '',
  result: '',
  search: ''
})

const todayStats = computed<TodayStats>(() => {
  const today = new Date().toISOString().split('T')[0]
  const todayLogs = logs.value.filter(log => log.createdAt.startsWith(today))

  return {
    login: todayLogs.filter(l => l.activityType.includes('login')).length,
    create: todayLogs.filter(l => l.activityType.startsWith('POST')).length,
    update: todayLogs.filter(l => l.activityType.startsWith('PUT')).length,
    delete: todayLogs.filter(l => l.activityType.startsWith('DELETE')).length,
    failure: todayLogs.filter(l => l.isSuccess === false).length
  }
})

const anomalies = computed<Anomaly[]>(() => {
  return []
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalLogCount.value / itemsPerPage)))

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

const paginatedLogs = computed(() => logs.value)

const loadLogs = async () => {
  try {
    loading.value = true
    const params: Record<string, string | number> = {
      skip: (currentPage.value - 1) * itemsPerPage,
      take: itemsPerPage
    }
    if (filters.value.startDate) params.startDate = new Date(filters.value.startDate).toISOString()
    if (filters.value.endDate) params.endDate = new Date(filters.value.endDate + 'T23:59:59').toISOString()
    if (filters.value.userId) params.userId = parseInt(filters.value.userId)
    if (filters.value.action) params.action = filters.value.action
    if (filters.value.search) params.search = filters.value.search

    const response = await api.get<{ items: ActivityLog[]; totalCount: number }>('/activitylog', { params })
    const data = response.data
    logs.value = data?.items || []
    totalLogCount.value = data?.totalCount ?? 0
  } catch (error: any) {
    console.error('Error loading logs:', error)
    logs.value = []
    if (error?.response?.status === 403) {
      alert('감사 로그 조회 권한이 없습니다. (Admin 역할 필요)')
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

const applyFilters = () => {
  currentPage.value = 1
  loadLogs()
}

const resetFilters = () => {
  filters.value = {
    startDate: '',
    endDate: '',
    userId: '',
    action: '',
    result: '',
    search: ''
  }
  currentPage.value = 1
  loadLogs()
}

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadLogs()
  }
}

const viewLogDetail = (log: ActivityLog) => {
  selectedLog.value = log
  showDetailModal.value = true
}

const exportLogs = () => {
  const csv = [
    ['일시', '사용자', '활동', '대상', 'IP 주소', '결과'].join(','),
    ...paginatedLogs.value.map(log => [
      formatDateTime(log.createdAt),
      log.userName || '',
      log.activityType,
      log.entityType || '',
      log.ipAddress || '',
      log.isSuccess === false ? '실패' : '성공'
    ].join(','))
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit_log_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('ko-KR')
}

const getActionLabel = (activityType: string): string => {
  if (activityType.includes('login')) return '로그인'
  if (activityType.startsWith('POST')) return '생성'
  if (activityType.startsWith('PUT') || activityType.startsWith('PATCH')) return '수정'
  if (activityType.startsWith('DELETE')) return '삭제'
  if (activityType.startsWith('GET')) return '조회'
  return activityType
}

const getActionIcon = (activityType: string): string => {
  if (activityType.includes('login')) return 'bi bi-box-arrow-in-right'
  if (activityType.startsWith('POST')) return 'bi bi-plus-circle-fill'
  if (activityType.startsWith('PUT') || activityType.startsWith('PATCH')) return 'bi bi-pencil-fill'
  if (activityType.startsWith('DELETE')) return 'bi bi-trash3-fill'
  if (activityType.startsWith('GET')) return 'bi bi-eye-fill'
  return 'bi bi-activity'
}

/** 활동 배지 색상 타입 */
const getActionBadgeType = (activityType: string): string => {
  if (activityType.includes('login')) return 'al-action-login'
  if (activityType.startsWith('POST')) return 'al-action-create'
  if (activityType.startsWith('PUT') || activityType.startsWith('PATCH')) return 'al-action-update'
  if (activityType.startsWith('DELETE')) return 'al-action-delete'
  if (activityType.startsWith('GET')) return 'al-action-read'
  return 'al-action-other'
}

const getActionBadgeClass = (activityType: string): string => {
  if (activityType.includes('login')) return 'bg-info'
  if (activityType.startsWith('POST')) return 'bg-success'
  if (activityType.startsWith('PUT') || activityType.startsWith('PATCH')) return 'bg-warning'
  if (activityType.startsWith('DELETE')) return 'bg-danger'
  if (activityType.startsWith('GET')) return 'bg-primary'
  return 'bg-secondary'
}

onMounted(() => {
  loadLogs()
  loadUsers()
})
</script>

<style scoped>
.log-row {
  cursor: pointer;
  transition: background 0.15s ease;
}
.log-row:hover {
  background: var(--ai-bg-light);
}
.modal.show { display: block; }
.modal-backdrop.show { opacity: 0.5; }
.font-mono { font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; }

/* ── 총 개수 칩 ── */
.al-count-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  background: var(--ai-bg-light);
  border: 1px solid var(--ai-border);
  border-radius: 20px;
  font-size: 13px;
  color: var(--ai-text-secondary);
  line-height: 1;
}
.al-count-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: var(--ai-primary-light);
  border-radius: 50%;
  color: var(--ai-primary);
  font-size: 10px;
}
.al-count-text { color: var(--ai-text-muted); font-size: 12px; }
.al-count-num {
  font-size: 15px;
  font-weight: 700;
  color: var(--ai-primary);
  letter-spacing: -0.5px;
}
.al-count-unit { color: var(--ai-text-muted); font-size: 12px; }

/* ── 활동 배지 ── */
.al-action-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  line-height: 1;
  border: 1px solid transparent;
}
.al-action-badge i { font-size: 11px; }

/* 로그인 - 파랑 */
.al-action-login {
  background: rgba(14, 165, 233, 0.1);
  color: #0284C7;
  border-color: rgba(14, 165, 233, 0.2);
}
/* 생성 - 초록 */
.al-action-create {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border-color: rgba(16, 185, 129, 0.2);
}
/* 수정 - 주황/노랑 */
.al-action-update {
  background: rgba(245, 158, 11, 0.1);
  color: #D97706;
  border-color: rgba(245, 158, 11, 0.2);
}
/* 삭제 - 빨강 */
.al-action-delete {
  background: rgba(239, 68, 68, 0.1);
  color: #DC2626;
  border-color: rgba(239, 68, 68, 0.2);
}
/* 조회 - 보라 */
.al-action-read {
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  border-color: rgba(79, 70, 229, 0.2);
}
/* 기타 */
.al-action-other {
  background: var(--ai-bg-light);
  color: var(--ai-text-muted);
  border-color: var(--ai-border);
}

/* ── 결과 배지 ── */
.al-result-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  border: 1px solid transparent;
}
.al-result-badge i { font-size: 11px; }

.al-result-success {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
  border-color: rgba(16, 185, 129, 0.2);
}
.al-result-fail {
  background: rgba(239, 68, 68, 0.08);
  color: #DC2626;
  border-color: rgba(239, 68, 68, 0.18);
}

/* ── 상세 보기 버튼 ── */
.al-detail-btn {
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
  letter-spacing: 0.1px;
}
.al-detail-btn i { font-size: 11px; }
.al-detail-btn:hover {
  border-color: var(--ai-primary);
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.15);
}
.al-detail-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

/* 통계 아이템 색상 */
.activity-stat-item .value.text-success { color: var(--ai-success) !important; }
.activity-stat-item .value.text-primary { color: var(--ai-primary) !important; }
.activity-stat-item .value.text-info { color: var(--ai-info) !important; }
.activity-stat-item .value.text-warning { color: var(--ai-warning) !important; }
.activity-stat-item .value.text-danger { color: var(--ai-danger) !important; }

/* ── 페이지네이션 개선 ── */
.al-page-info {
  font-size: 12px;
  color: var(--ai-text-muted);
}
.al-page-info strong { color: var(--ai-text-primary); font-weight: 600; }
.al-page-nav i { font-size: 10px; }
.al-page-ellipsis .page-link {
  pointer-events: none;
  color: var(--ai-text-muted);
  background: transparent;
  border-color: transparent;
  cursor: default;
}

/* ── 로그 상세 모달 ── */
.al-modal {
  border: none;
  border-radius: var(--ai-radius-lg);
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,.18);
}

/* 헤더 */
.al-modal-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--ai-bg-card) 0%, var(--ai-bg-light) 100%);
  border-bottom: 1px solid var(--ai-border);
}
.al-modal-hdr-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.al-modal-icon {
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
.al-modal-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--ai-text-primary);
  margin: 0;
}
.al-modal-subtitle {
  font-size: 11px;
  color: var(--ai-text-muted);
  margin: 3px 0 0;
}
.al-modal-close-btn {
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
.al-modal-close-btn:hover {
  border-color: var(--ai-primary);
  color: var(--ai-primary);
  background: var(--ai-primary-light);
}

/* 바디 */
.al-modal-body { padding: 24px; }

/* 정보 그리드 */
.al-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
}
.al-info-item {
  background: var(--ai-bg-light);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  padding: 12px 14px;
}
.al-info-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: var(--ai-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 5px;
}
.al-info-label i { margin-right: 4px; opacity: .7; }
.al-info-value {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--ai-text-primary);
  word-break: break-all;
}

/* 섹션 */
.al-modal-section { margin-bottom: 16px; }
.al-modal-section-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--ai-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding-bottom: 8px;
  margin-bottom: 10px;
  border-bottom: 1px solid var(--ai-border);
}
.al-modal-section-title i { margin-right: 6px; }
.al-modal-section-body {
  font-size: 13px;
  color: var(--ai-text-primary);
  line-height: 1.6;
  background: var(--ai-bg-light);
  padding: 12px 14px;
  border-radius: var(--ai-radius);
  border: 1px solid var(--ai-border);
}
.al-modal-code {
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 12px;
  background: var(--ai-bg-light);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius);
  padding: 14px 16px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 280px;
  overflow-y: auto;
  color: var(--ai-text-primary);
  margin: 0;
}

/* 푸터 */
.al-modal-ftr {
  padding: 14px 24px;
  background: var(--ai-bg-light);
  border-top: 1px solid var(--ai-border);
  display: flex;
  justify-content: flex-end;
}
</style>
