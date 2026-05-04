<template>
  <div class="page-content-wrap">
    <div class="page-header mb-4">
      <div>
        <h1 class="page-heading">개인정보 보호 설정</h1>
        <p class="page-desc">시스템 전체 개인정보 보호 설정을 관리합니다. (관리자 전용)</p>
      </div>
    </div>

    <!-- 전역 설정 -->
    <div class="card aiuiux-card mb-4">
      <div class="card-header bg-transparent border-bottom">
        <div>
          <h5 class="card-title mb-0"><i class="bi bi-gear me-2"></i>전역 개인정보 보호 설정</h5>
          <p class="card-subtitle mb-0">활성화·보호 모드·감지 유형</p>
        </div>
      </div>
      <div class="card-body">
        <form @submit.prevent="saveSettings">
          <div class="mb-4">
            <div class="form-check form-switch">
              <input 
                class="form-check-input" 
                type="checkbox" 
                v-model="settings.enabled"
                id="pii-enabled"
              >
              <label class="form-check-label" for="pii-enabled">
                <strong>개인정보 보호 활성화</strong>
                <br><small class="text-muted">시스템 전체에서 개인정보 자동 감지 및 보호 기능을 활성화합니다.</small>
              </label>
            </div>
          </div>

          <div v-if="settings.enabled" class="mb-4">
            <label class="form-label">보호 모드</label>
            <select class="form-select" v-model="settings.mode">
              <option value="Block">차단 (개인정보 포함 시 메시지 거부)</option>
              <option value="Mask">마스킹 (개인정보를 자동으로 마스킹 처리)</option>
            </select>
            <small class="text-muted d-block mt-1">
              <span v-if="settings.mode === 'Block'">개인정보가 포함된 메시지는 전송되지 않습니다.</span>
              <span v-else>개인정보가 자동으로 마스킹되어 전송됩니다.</span>
            </small>
          </div>

          <div v-if="settings.enabled" class="mb-4">
            <label class="form-label">감지할 개인정보 유형</label>
            <div class="row">
              <div class="col-md-6" v-for="type in availableTypes" :key="type.value">
                <div class="form-check">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    :value="type.value"
                    v-model="settings.detectionTypes"
                    :id="`type-${type.value}`"
                  >
                  <label class="form-check-label" :for="`type-${type.value}`">
                    {{ type.label }}
                  </label>
                </div>
              </div>
            </div>
            <small class="text-muted d-block mt-2">선택한 유형의 개인정보만 감지합니다.</small>
          </div>

          <div class="text-end">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <i class="bi bi-check-lg"></i> {{ saving ? '저장 중...' : '설정 저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 통계 -->
    <div class="card aiuiux-card mb-4">
      <div class="card-header bg-transparent border-bottom">
        <div>
          <h5 class="card-title mb-0"><i class="bi bi-graph-up me-2"></i>개인정보 감지 통계</h5>
          <p class="card-subtitle mb-0">개인정보 감지 통계를 조회합니다.</p>
        </div>
      </div>
      <div class="card-body">
        <div v-if="loadingStats" class="text-center py-4">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">로딩 중...</span>
          </div>
        </div>
        <div v-else-if="statsError" class="text-center py-4">
          <i class="bi bi-exclamation-triangle text-warning" style="font-size:2rem;"></i>
          <p class="text-muted mt-2">{{ statsError }}</p>
          <button class="btn btn-sm btn-outline-secondary mt-1" @click="loadStatistics">
            <i class="bi bi-arrow-clockwise me-1"></i>다시 시도
          </button>
        </div>
        <div v-else-if="statistics && statistics.totalDetections === 0" class="text-center py-4 text-muted">
          <i class="bi bi-inbox" style="font-size:2rem; opacity:0.5;"></i>
          <p class="mt-2">선택한 기간에 감지된 개인정보가 없습니다.</p>
        </div>
        <div v-else-if="statistics">
          <div class="row mb-4">
            <div class="col-md-3">
              <div class="card bg-primary text-white">
                <div class="card-body">
                  <h6>전체 감지</h6>
                  <h3>{{ statistics.totalDetections.toLocaleString() }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="card bg-danger text-white">
                <div class="card-body">
                  <h6>차단</h6>
                  <h3>{{ statistics.blockedCount.toLocaleString() }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="card bg-warning text-white">
                <div class="card-body">
                  <h6>마스킹</h6>
                  <h3>{{ statistics.maskedCount.toLocaleString() }}</h3>
                </div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="card bg-info text-white">
                <div class="card-body">
                  <h6>감지 유형 수</h6>
                  <h3>{{ Object.keys(statistics.detectionTypeCounts).length }}</h3>
                </div>
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-md-6 mb-4">
              <h6>유형별 감지 횟수</h6>
              <div class="table-responsive">
                <table class="table table-sm">
                  <thead>
                    <tr>
                      <th>유형</th>
                      <th class="text-end">횟수</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="[type, count] in Object.entries(statistics.detectionTypeCounts)" :key="type">
                      <td>{{ getTypeName(type) }}</td>
                      <td class="text-end">{{ count.toLocaleString() }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="col-md-6 mb-4">
              <h6>Agent별 감지 횟수 (TOP 10)</h6>
              <div class="table-responsive">
                <table class="table table-sm">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th class="text-end">횟수</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="[agent, count] in Object.entries(statistics.agentCounts).slice(0, 10)" :key="agent">
                      <td>{{ agent }}</td>
                      <td class="text-end">{{ count.toLocaleString() }}</td>
                    </tr>
                    <tr v-if="Object.keys(statistics.agentCounts).length === 0">
                      <td colspan="2" class="text-center text-muted">데이터가 없습니다.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 감지 로그 -->
    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom d-flex flex-wrap justify-content-between align-items-center gap-3">
        <div>
          <h5 class="card-title mb-0"><i class="bi bi-list-ul me-2"></i>감지 로그</h5>
          <p class="card-subtitle mb-0">개인정보 감지 로그를 조회합니다.</p>
        </div>
        <div class="d-flex align-items-center gap-2">
          <input type="date" class="ag-filter-date" v-model="filterStartDate" @change="loadLogs" title="시작일">
          <span class="text-muted">~</span>
          <input type="date" class="ag-filter-date" v-model="filterEndDate" @change="loadLogs" title="종료일">
        </div>
      </div>
      <div class="card-body">
        <div v-if="loadingLogs" class="text-center py-4">
          <div class="spinner-border" role="status">
            <span class="visually-hidden">로딩 중...</span>
          </div>
        </div>
        <div v-else-if="logs.length === 0" class="text-center py-5 text-muted">
          <i class="bi bi-inbox icon-3xl"></i>
          <p class="mt-3">감지 로그가 없습니다.</p>
        </div>
        <div v-else>
          <div class="table-responsive">
            <table class="table table-hover">
              <thead>
                <tr>
                  <th>일시</th>
                  <th>사용자</th>
                  <th>Agent</th>
                  <th>감지 유형</th>
                  <th>조치</th>
                  <th>IP 주소</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in logs" :key="log.logId">
                  <td>{{ formatDate(log.detectedAt) }}</td>
                  <td>{{ log.userName || '-' }}</td>
                  <td>{{ log.agentName || '-' }}</td>
                  <td>
                    <span class="badge bg-warning">{{ log.detectionTypeName }}</span>
                  </td>
                  <td>
                    <span :class="log.actionTaken === 'Block' ? 'badge bg-danger' : 'badge bg-warning'">
                      {{ log.actionTaken === 'Block' ? '차단' : '마스킹' }}
                    </span>
                  </td>
                  <td>{{ log.ipAddress || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 페이징 -->
          <nav v-if="totalPages > 1">
            <ul class="pagination justify-content-center">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">이전</a>
              </li>
              <li 
                v-for="page in visiblePages" 
                :key="page"
                class="page-item" 
                :class="{ active: page === currentPage }"
              >
                <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">다음</a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { PiiProtectionSettings, PiiDetectionStatisticsDto, PiiDetectionLogDto } from '@/types'

const settings = ref<PiiProtectionSettings>({
  enabled: true,
  mode: 'Block',
  detectionTypes: []
})

const availableTypes = [
  { value: 'PhoneNumber', label: '휴대폰 번호' },
  { value: 'ResidentNumber', label: '주민등록번호' },
  { value: 'CreditCard', label: '신용카드 번호' },
  { value: 'Email', label: '이메일 주소' },
  { value: 'AccountNumber', label: '계좌번호' },
  { value: 'DriverLicense', label: '운전면허번호' },
  { value: 'PassportNumber', label: '여권번호' },
  { value: 'AlienRegistrationNumber', label: '외국인등록번호' }
]

const saving = ref(false)
const loadingStats = ref(false)
const loadingLogs = ref(false)
const statistics = ref<PiiDetectionStatisticsDto | null>(null)
const statsError = ref<string | null>(null)
const logs = ref<PiiDetectionLogDto[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = ref(1)
const filterStartDate = ref('')
const filterEndDate = ref('')

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const getTypeName = (type: string): string => {
  const found = availableTypes.find(t => t.value === type)
  return found ? found.label : type
}

const formatDate = (date: string | Date): string => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('ko-KR')
}

const loadSettings = async () => {
  try {
    const response = await api.get<PiiProtectionSettings>('/systemsettings/pii-protection')
    settings.value = response.data
  } catch (error: any) {
    console.error('설정 로드 실패:', error)
    alert('설정을 불러오는 중 오류가 발생했습니다.')
  }
}

const saveSettings = async () => {
  try {
    saving.value = true
    await api.put('/systemsettings/pii-protection', settings.value)
    alert('설정이 저장되었습니다.')
    await loadStatistics()
  } catch (error: any) {
    console.error('설정 저장 실패:', error)
    alert(error.response?.data?.message || '설정 저장 중 오류가 발생했습니다.')
  } finally {
    saving.value = false
  }
}

const loadStatistics = async () => {
  try {
    loadingStats.value = true
    statsError.value = null
    const params: any = {}
    if (filterStartDate.value) params.startDate = filterStartDate.value
    if (filterEndDate.value) params.endDate = filterEndDate.value

    const response = await api.get<PiiDetectionStatisticsDto>('/piidetectionlogs/statistics', { params })
    statistics.value = response.data
  } catch (error: any) {
    console.error('통계 로드 실패:', error)
    statsError.value = error.response?.data?.message || '통계 조회 중 오류가 발생했습니다.'
    statistics.value = null
  } finally {
    loadingStats.value = false
  }
}

const loadLogs = async () => {
  try {
    loadingLogs.value = true
    const params: any = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    if (filterStartDate.value) params.startDate = filterStartDate.value
    if (filterEndDate.value) params.endDate = filterEndDate.value
    
    const response = await api.get<{ items: PiiDetectionLogDto[], totalCount: number, page: number, pageSize: number, totalPages: number }>('/piidetectionlogs', { params })
    logs.value = response.data.items || []
    totalPages.value = response.data.totalPages || 1
  } catch (error: any) {
    console.error('로그 로드 실패:', error)
    logs.value = []
  } finally {
    loadingLogs.value = false
  }
}

const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadLogs()
  }
}

onMounted(() => {
  // 날짜 기본값 설정 (최근 30일) — 로드 함수 호출 전에 먼저 설정해야 날짜 필터가 적용됨
  const endDate = new Date()
  const startDate = new Date()
  startDate.setDate(startDate.getDate() - 30)
  filterStartDate.value = startDate.toISOString().split('T')[0]
  filterEndDate.value = endDate.toISOString().split('T')[0]

  loadSettings()
  loadStatistics()
  loadLogs()
})
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}
</style>
