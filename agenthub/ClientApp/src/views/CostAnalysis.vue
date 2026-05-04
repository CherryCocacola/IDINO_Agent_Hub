<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">비용 분석</h1>
        <p class="page-desc mb-0">마지막 조회: {{ lastQueryTime || '—' }}</p>
      </div>
      <div class="page-actions">
        <select class="form-select form-select-sm" style="width:140px" v-model="period" @change="loadData()">
          <option value="today">오늘</option>
          <option value="week">이번 주</option>
          <option value="month">이번 달</option>
          <option value="year">올해</option>
        </select>
        <button class="btn btn-outline-secondary btn-sm ms-2" @click="loadData()">
          <i class="bi bi-arrow-clockwise me-1"></i> 새로고침
        </button>
        <button class="btn btn-primary btn-sm ms-2" @click="showBudgetModal = true">
          <i class="bi bi-gear me-1"></i> 예산 설정
        </button>
      </div>
    </div>

    <!-- 로딩 상태 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">로딩 중...</span>
      </div>
      <p class="mt-3 text-muted">데이터를 불러오는 중...</p>
    </div>

    <!-- KPI Row (모니터링 스타일) -->
    <div v-else class="row g-3 mb-4">
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">${{ stats.totalCost.toFixed(2) }}</div>
          <div class="kpi-label">총 비용</div>
          <div class="kpi-trend" :class="stats.costIncrease > 0 ? 'kpi-down' : stats.costIncrease < 0 ? 'kpi-up' : ''">
            <template v-if="stats.costIncrease > 0"><i class="bi bi-arrow-up"></i> +{{ stats.costIncrease.toFixed(1) }}%</template>
            <template v-else-if="stats.costIncrease < 0"><i class="bi bi-arrow-down"></i> {{ stats.costIncrease.toFixed(1) }}%</template>
            <template v-else><i class="bi bi-dash"></i> 변화 없음</template>
          </div>
        </div>
      </div>
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">${{ stats.projectedCost.toFixed(2) }}</div>
          <div class="kpi-label">예상 월말 비용</div>
          <div class="kpi-trend text-muted" style="font-size:11px">예측치</div>
        </div>
      </div>
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">{{ stats.budgetUsage.toFixed(0) }}%</div>
          <div class="kpi-label">예산 사용률</div>
          <div class="health-bar mt-2" style="height:6px; --pct: 0%;" :style="{ '--pct': Math.min(stats.budgetUsage, 100) + '%', '--c': stats.budgetUsage > 90 ? 'var(--ai-danger)' : stats.budgetUsage > 75 ? 'var(--ai-warning)' : 'var(--ai-success)' }"></div>
          <small class="text-muted fs-xs">예산 ${{ stats.budget.toFixed(2) }}</small>
        </div>
      </div>
      <div class="col-xl col-md-4 col-6">
        <div class="kpi-card">
          <div class="kpi-value">${{ stats.dailyAverage.toFixed(2) }}</div>
          <div class="kpi-label">평균 일일 비용</div>
          <div class="kpi-trend text-muted" style="font-size:11px">기간 평균</div>
        </div>
      </div>
    </div>

    <!-- 차트 영역 (모니터링/모델 카드 스타일) -->
    <div class="row g-4 mb-4">
      <div class="col-lg-6">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom">
            <div>
              <h5 class="card-title mb-0">서비스별 비용 분석</h5>
              <p class="card-subtitle mb-0">서비스별 비용 비율</p>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="serviceCosts.length === 0" class="text-center text-muted py-5 px-3">
              <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
              <p class="mt-3 mb-0">데이터가 없습니다</p>
            </div>
            <div v-else class="health-grid">
              <div class="health-row health-header">
                <div class="health-model">서비스</div>
                <div class="health-bar-cell">비용 비율</div>
              </div>
              <div 
                v-for="service in serviceCosts" 
                :key="service.serviceName"
                class="health-row"
              >
                <div class="health-model">
                  <span class="model-dot" :style="{ background: service.colorCode }"></span>
                  {{ service.serviceName }}
                </div>
                <div class="health-bar-cell">
                  <div class="health-bar" :style="{ '--pct': service.percentage + '%', '--c': service.colorCode }"></div>
                  <span class="health-val">${{ service.totalCost.toFixed(2) }} ({{ service.percentage.toFixed(1) }}%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom">
            <div>
              <h5 class="card-title mb-0">일별 비용 추이</h5>
              <p class="card-subtitle mb-0">일별 누적 비용</p>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="dailyCostData.length === 0" class="text-center text-muted py-5">
              <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
              <p class="mt-3">데이터가 없습니다</p>
            </div>
            <div v-else class="table-responsive max-height-300 scrollable">
              <table class="table table-sm table-hover aiuiux-table mb-0">
                <thead>
                  <tr>
                    <th>날짜</th>
                    <th class="text-end">비용</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in dailyCostData" :key="item.date">
                    <td>
                      <div class="table-name-cell">
                        <div class="table-cell-icon icon-date"><i class="bi bi-calendar3"></i></div>
                        <div class="table-cell-meta">
                          <p class="table-cell-title mb-0">{{ new Date(item.date).toLocaleDateString('ko-KR') }}</p>
                        </div>
                      </div>
                    </td>
                    <td class="text-end"><span class="table-num-cell">${{ item.cost.toFixed(2) }}</span></td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <th>합계</th>
                    <th class="text-end table-num-cell">${{ dailyCostData.reduce((sum, item) => sum + item.cost, 0).toFixed(2) }}</th>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 서비스별 상세 비용 (모델 테이블 스타일) -->
    <div v-if="!loading" class="row mb-4">
      <div class="col-12">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
            <div>
              <h5 class="card-title mb-0">서비스별 상세 비용</h5>
              <p class="card-subtitle mb-0">요청·토큰·비용 현황</p>
            </div>
            <div class="d-flex gap-2 align-items-center">
              <button class="btn btn-sm btn-outline-secondary" @click="exportCostReport" :disabled="serviceCosts.length === 0">
                <i class="bi bi-download me-1"></i> 내보내기
              </button>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="serviceCosts.length === 0" class="text-center text-muted py-5">
              <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
              <p class="mt-3">데이터가 없습니다</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover mb-0 aiuiux-table">
                <thead>
                  <tr>
                    <th>서비스</th>
                    <th class="text-end">요청 수</th>
                    <th class="text-end">토큰 사용</th>
                    <th class="text-end">총 비용</th>
                    <th>비율</th>
                    <th class="text-end">평균 비용/요청</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="service in serviceCosts" :key="service.serviceName">
                    <td>
                      <div class="table-name-cell">
                        <div class="table-cell-icon" :style="{ background: service.colorCode }">
                          <i :class="getServiceIcon(service.serviceName)" style="color: #fff;"></i>
                        </div>
                        <div class="table-cell-meta">
                          <p class="table-cell-title mb-0">{{ service.serviceName }}</p>
                        </div>
                      </div>
                    </td>
                    <td class="text-end table-num-cell text-muted fs-xs">{{ service.requestCount.toLocaleString() }}</td>
                    <td class="text-end table-num-cell text-muted fs-xs">{{ service.totalTokens.toLocaleString() }}</td>
                    <td class="text-end table-num-cell">${{ service.totalCost.toFixed(2) }}</td>
                    <td>
                      <div class="health-bar" style="max-width: 120px;" :style="{ '--pct': service.percentage + '%', '--c': service.colorCode }"></div>
                      <small class="text-muted">{{ service.percentage.toFixed(1) }}%</small>
                    </td>
                    <td class="text-end table-num-cell text-muted fs-xs">${{ (service.totalCost / service.requestCount || 0).toFixed(4) }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <th>합계</th>
                    <th class="text-end table-num-cell">{{ serviceCosts.reduce((sum, s) => sum + s.requestCount, 0).toLocaleString() }}</th>
                    <th class="text-end table-num-cell">{{ serviceCosts.reduce((sum, s) => sum + s.totalTokens, 0).toLocaleString() }}</th>
                    <th class="text-end table-num-cell">${{ serviceCosts.reduce((sum, s) => sum + s.totalCost, 0).toFixed(2) }}</th>
                    <th>100%</th>
                    <th class="text-end">-</th>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 최적화 제안 -->
    <div v-if="!loading" class="row">
      <div class="col-12">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <div>
              <h5 class="card-title mb-0"><i class="bi bi-lightbulb me-2"></i>비용 최적화 제안</h5>
              <p class="card-subtitle mb-0">절감 방안 및 예산 상태</p>
            </div>
          </div>
          <div class="card-body">
            <div v-if="serviceCosts.length === 0" class="text-center text-muted py-3">
              <p class="mb-0">분석할 데이터가 없습니다.</p>
            </div>
            <div v-else class="alert-list">
              <div class="alert-item alert-item-info">
                <div class="alert-icon"><i class="bi bi-info-circle"></i></div>
                <div class="alert-content">
                  <p class="alert-title">모델 최적화</p>
                  <p class="alert-desc mb-0" v-if="potentialSavings > 0">
                    비용 효율적인 모델로 전환 시 월 ${{ potentialSavings.toFixed(2) }} 절감 가능
                  </p>
                  <p class="alert-desc mb-0" v-else>추가 최적화 여지가 제한적입니다.</p>
                </div>
              </div>
              <div class="alert-item alert-item-warning" v-if="topCostService !== '-'">
                <div class="alert-icon"><i class="bi bi-exclamation-triangle"></i></div>
                <div class="alert-content">
                  <p class="alert-title">사용량 모니터링</p>
                  <p class="alert-desc mb-0">
                    {{ topCostService }} 사용량이 전체의 {{ topCostPercentage.toFixed(1) }}%를 차지합니다.
                    <span v-if="topCostPercentage > 50">이 서비스의 사용 패턴을 검토해보세요.</span>
                  </p>
                </div>
              </div>
              <div class="alert-item alert-item-success" v-if="stats.budgetUsage < 75">
                <div class="alert-icon"><i class="bi bi-check-circle"></i></div>
                <div class="alert-content">
                  <p class="alert-title">예산 상태</p>
                  <p class="alert-desc mb-0">현재 예산 사용률이 {{ stats.budgetUsage.toFixed(1) }}%로 양호한 수준입니다.</p>
                </div>
              </div>
              <div class="alert-item alert-item-error" v-else-if="stats.budgetUsage >= 100">
                <div class="alert-icon"><i class="bi bi-exclamation-circle"></i></div>
                <div class="alert-content">
                  <p class="alert-title">예산 초과</p>
                  <p class="alert-desc mb-0">예산을 초과했습니다. 사용량을 검토하세요.</p>
                </div>
              </div>
              <div class="alert-item alert-item-warning" v-else>
                <div class="alert-icon"><i class="bi bi-exclamation-triangle"></i></div>
                <div class="alert-content">
                  <p class="alert-title">예산 경고</p>
                  <p class="alert-desc mb-0">예산 사용률이 {{ stats.budgetUsage.toFixed(1) }}%입니다. 주의가 필요합니다.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 예산 설정 모달 -->
    <div class="modal fade" :class="{ show: showBudgetModal, 'd-block': showBudgetModal }" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title">예산 설정</h5>
            <button type="button" class="btn-close" @click="showBudgetModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleSetBudget">
              <div class="mb-3">
                <label class="form-label">월간 예산 ($)</label>
                <input type="number" class="form-control" v-model.number="budgetForm.monthlyBudget" step="0.01" required>
              </div>
              <div class="mb-3">
                <label class="form-label">연간 예산 ($)</label>
                <input type="number" class="form-control" v-model.number="budgetForm.yearlyBudget" step="0.01" required>
              </div>
              <div class="mb-3">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" v-model="budgetForm.alertEnabled" id="budget-alert">
                  <label class="form-check-label" for="budget-alert">
                    예산 80% 도달 시 알림
                  </label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showBudgetModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleSetBudget">저장</button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showBudgetModal }" v-if="showBudgetModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { CostAnalysisDto, ServiceCostDto, UsageStatsDto } from '@/types'

interface CostStats {
  totalCost: number
  projectedCost: number
  budgetUsage: number
  budget: number
  dailyAverage: number
  costIncrease: number
}

interface ServiceCostDetail extends ServiceCostDto {
  colorCode?: string
  totalTokens: number
}

interface DailyCostData {
  date: string
  cost: number
}

interface BudgetForm {
  monthlyBudget: number
  yearlyBudget: number
  alertEnabled: boolean
}

const period = ref('month')
const loading = ref(false)
const showBudgetModal = ref(false)
const lastQueryTime = ref('')
const usageStats = ref<UsageStatsDto[]>([])
const dailyCostData = ref<DailyCostData[]>([])

const stats = ref<CostStats>({
  totalCost: 0,
  projectedCost: 0,
  budgetUsage: 0,
  budget: 2000,
  dailyAverage: 0,
  costIncrease: 0
})

const serviceCosts = ref<ServiceCostDetail[]>([])
const costAnalysis = ref<CostAnalysisDto | null>(null)

const budgetForm = ref<BudgetForm>({
  monthlyBudget: 2000,
  yearlyBudget: 24000,
  alertEnabled: true
})

const topCostService = computed(() => {
  if (serviceCosts.value.length === 0) return '-'
  return serviceCosts.value[0].serviceName
})

const topCostPercentage = computed(() => {
  if (serviceCosts.value.length === 0 || stats.value.totalCost === 0) return 0
  return (serviceCosts.value[0].totalCost / stats.value.totalCost) * 100
})

const potentialSavings = computed(() => {
  return stats.value.totalCost * 0.2
})

const loadData = async () => {
  try {
    loading.value = true
    const endDate = new Date()
    const startDate = new Date()
    let previousStartDate = new Date()
    let previousEndDate = new Date()
    
    switch (period.value) {
      case 'today':
        startDate.setHours(0, 0, 0, 0)
        previousStartDate = new Date(startDate)
        previousStartDate.setDate(previousStartDate.getDate() - 1)
        previousEndDate = new Date(startDate)
        break
      case 'week':
        startDate.setDate(startDate.getDate() - 7)
        previousStartDate = new Date(startDate)
        previousStartDate.setDate(previousStartDate.getDate() - 7)
        previousEndDate = new Date(startDate)
        break
      case 'month':
        startDate.setMonth(startDate.getMonth() - 1)
        previousStartDate = new Date(startDate)
        previousStartDate.setMonth(previousStartDate.getMonth() - 1)
        previousEndDate = new Date(startDate)
        break
      case 'year':
        startDate.setFullYear(startDate.getFullYear() - 1)
        previousStartDate = new Date(startDate)
        previousStartDate.setFullYear(previousStartDate.getFullYear() - 1)
        previousEndDate = new Date(startDate)
        break
    }

    // 현재 기간 비용 분석 및 사용량 통계
    const [costRes, usageRes, prevCostRes] = await Promise.all([
      api.get<CostAnalysisDto>('/analytics/cost', {
        params: {
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString()
        }
      }).catch(() => ({ data: null })),
      api.get<UsageStatsDto[]>('/analytics/usage', {
        params: {
          startDate: startDate.toISOString(),
          endDate: endDate.toISOString()
        }
      }).catch(() => ({ data: [] })),
      // 이전 기간 비용 (증가율 계산용)
      api.get<CostAnalysisDto>('/analytics/cost', {
        params: {
          startDate: previousStartDate.toISOString(),
          endDate: previousEndDate.toISOString()
        }
      }).catch(() => ({ data: null }))
    ])

    costAnalysis.value = costRes.data
    usageStats.value = usageRes.data || []
    const previousCost = prevCostRes.data?.totalCost || 0

    if (costAnalysis.value) {
      // 기간 일수 계산
      const daysDiff = Math.max(1, Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)))
      
      // 일별 비용 데이터 생성
      const dailyCostMap = new Map<string, number>()
      usageStats.value.forEach(stat => {
        const dateKey = new Date(stat.date).toISOString().split('T')[0]
        const existing = dailyCostMap.get(dateKey) || 0
        dailyCostMap.set(dateKey, existing + stat.totalCost)
      })
      
      dailyCostData.value = Array.from(dailyCostMap.entries())
        .map(([date, cost]) => ({ date, cost }))
        .sort((a, b) => a.date.localeCompare(b.date))

      // 서비스별 토큰 데이터 매핑
      const serviceTokenMap = new Map<number, number>()
      usageStats.value.forEach(stat => {
        const existing = serviceTokenMap.get(stat.serviceId) || 0
        serviceTokenMap.set(stat.serviceId, existing + stat.totalTokens)
      })

      stats.value.totalCost = costAnalysis.value.totalCost
      
      // 예상 월말 비용 계산 (현재 일평균 * 남은 일수)
      const currentDayOfMonth = endDate.getDate()
      const daysInMonth = new Date(endDate.getFullYear(), endDate.getMonth() + 1, 0).getDate()
      const remainingDays = Math.max(0, daysInMonth - currentDayOfMonth)
      const dailyAvg = daysDiff > 0 ? costAnalysis.value.totalCost / daysDiff : 0
      stats.value.projectedCost = period.value === 'month' 
        ? costAnalysis.value.totalCost + (dailyAvg * remainingDays)
        : costAnalysis.value.totalCost * 1.2
      
      stats.value.budgetUsage = stats.value.budget > 0 
        ? (costAnalysis.value.totalCost / stats.value.budget) * 100 
        : 0
      stats.value.dailyAverage = dailyAvg
      
      // 전월 대비 증가율 계산
      stats.value.costIncrease = previousCost > 0
        ? ((costAnalysis.value.totalCost - previousCost) / previousCost) * 100
        : 0
      
      // 서비스별 비용 데이터에 토큰 정보 추가
      serviceCosts.value = costAnalysis.value.serviceCosts.map(sc => ({
        ...sc,
        colorCode: getServiceColor(sc.serviceName),
        totalTokens: serviceTokenMap.get(sc.serviceId) || 0
      }))
    }
  } catch (error) {
    console.error('Error loading cost data:', error)
  } finally {
    loading.value = false
    lastQueryTime.value = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }
}

const handleSetBudget = () => {
  stats.value.budget = budgetForm.value.monthlyBudget
  localStorage.setItem('budget_settings', JSON.stringify(budgetForm.value))
  showBudgetModal.value = false
}

const exportCostReport = () => {
  // CSV 내보내기
  const csv = [
    ['서비스', '요청 수', '토큰 사용', '총 비용', '비율'].join(','),
    ...serviceCosts.value.map(sc => [
      sc.serviceName,
      sc.requestCount,
      sc.totalTokens,
      sc.totalCost.toFixed(2),
      sc.percentage.toFixed(1) + '%'
    ].join(','))
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cost_analysis_${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const getServiceIcon = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return 'bi bi-chat-square-text'
  if (name.includes('claude')) return 'bi bi-robot'
  if (name.includes('cursor')) return 'bi bi-code-slash'
  if (name.includes('copilot')) return 'bi bi-github'
  return 'bi bi-cpu'
}

const getServiceColor = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return '#0dcaf0'
  if (name.includes('claude')) return '#198754'
  if (name.includes('cursor')) return '#ffc107'
  if (name.includes('copilot')) return '#6c757d'
  return '#6c757d'
}

onMounted(() => {
  loadData()
  const saved = localStorage.getItem('budget_settings')
  if (saved) {
    budgetForm.value = JSON.parse(saved)
    stats.value.budget = budgetForm.value.monthlyBudget
  }
})
</script>
