<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">통합 분석 대시보드</h1>
        <p class="page-desc">시스템 전체의 사용 현황을 시각적으로 분석합니다.</p>
      </div>
      <div class="page-actions">
        <div class="btn-group btn-group-sm" role="group">
          <button 
            type="button" 
            class="btn btn-outline-primary"
            :class="{ active: period === 'today' }"
            @click="period = 'today'; loadData()"
          >
            오늘
          </button>
          <button 
            type="button" 
            class="btn btn-outline-primary"
            :class="{ active: period === 'week' }"
            @click="period = 'week'; loadData()"
          >
            이번주
          </button>
          <button 
            type="button" 
            class="btn btn-outline-primary"
            :class="{ active: period === 'month' }"
            @click="period = 'month'; loadData()"
          >
            이번달
          </button>
        </div>
      </div>
    </div>

    <!-- 핵심 지표 -->
    <div class="row g-4 mb-4">
      <div class="col-lg-3 col-md-6">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-people"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">활성 사용자</p>
            <h2 class="stat-value">{{ dashboardStats.activeUsers }}</h2>
            <p class="stat-change">전체 {{ dashboardStats.totalUsers }}명</p>
          </div>
        </div>
      </div>
      <div class="col-lg-3 col-md-6">
        <div class="stat-card stat-card-success">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-lightning"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">오늘 API 호출</p>
            <h2 class="stat-value">{{ formatNumber(dashboardStats.todayApiCalls) }}</h2>
            <p class="stat-change">선택 기간: {{ formatNumber(stats.totalCalls) }}</p>
          </div>
        </div>
      </div>
      <div class="col-lg-3 col-md-6 d-none d-md-block">
        <div class="stat-card stat-card-info">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-currency-dollar"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">총 비용</p>
            <h2 class="stat-value">${{ dashboardStats.thisMonthCost?.toFixed(2) ?? '0.00' }}</h2>
          </div>
        </div>
      </div>
      <div class="col-lg-3 col-md-6 d-none d-md-block">
        <div class="stat-card stat-card-warning">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-graph-up-arrow"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">토큰 사용</p>
            <h2 class="stat-value">{{ formatNumber(stats.totalTokens || 0) }}</h2>
          </div>
        </div>
      </div>
    </div>

    <!-- 차트 영역 -->
    <div class="row mb-4">
      <!-- 일별 사용량 추이 -->
      <div class="col-lg-8 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0">일별 API 호출 추이</h5>
          </div>
          <div class="card-body p-0">
            <div v-if="dailyUsageData.length === 0" class="text-center text-muted py-5">
              데이터가 없습니다.
            </div>
            <div v-else class="table-responsive">
              <table class="table table-sm aiuiux-table">
                <thead>
                  <tr>
                    <th>날짜</th>
                    <th class="text-end">호출 수</th>
                    <th class="text-end">비용</th>
                    <th class="text-end">평균 응답시간</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in dailyUsageData" :key="index">
                    <td>
                      <div class="table-name-cell">
                        <div class="table-cell-icon icon-date"><i class="bi bi-calendar3"></i></div>
                        <div class="table-cell-meta">
                          <div class="table-cell-title">{{ formatDate(item.date) }}</div>
                          <div class="table-cell-subtitle">{{ formatDayOfWeek(item.date) }} · 일별 집계</div>
                        </div>
                      </div>
                    </td>
                    <td class="text-end">
                      <span class="table-num-cell">{{ formatNumber(item.requestCount) }}</span>
                    </td>
                    <td class="text-end">
                      <span class="table-num-cell">${{ item.totalCost.toFixed(2) }}</span>
                    </td>
                    <td class="text-end">
                      <span class="table-num-cell muted">{{ item.avgResponseTime }}ms</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- 서비스별 사용 비율 -->
      <div class="col-lg-4 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0">서비스별 사용 비율</h5>
          </div>
          <div class="card-body p-0">
            <div v-if="serviceStats.length === 0" class="text-center text-muted py-5">
              데이터가 없습니다.
            </div>
            <div v-else class="health-grid">
              <div class="health-row health-header">
                <span>서비스</span>
                <span>비율</span>
              </div>
              <div
                v-for="service in serviceStats"
                :key="service.serviceName"
                class="health-row"
              >
                <div class="health-model">
                  <div
                    class="model-dot"
                    :style="{ background: getServiceColor(service.serviceName) }"
                  ></div>
                  {{ service.serviceName }}
                </div>
                <div class="health-bar-cell">
                  <div
                    class="health-bar"
                    :style="{ '--pct': service.percentage + '%', '--c': getServiceColor(service.serviceName) }"
                  ></div>
                  <span>{{ service.percentage }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 사용자 TOP 10 & 일별 비용 -->
    <div class="row mb-4">
      <div class="col-lg-6 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0">사용자별 API 호출 TOP 10</h5>
          </div>
          <div class="card-body p-0">
            <div v-if="topUsers.length === 0" class="text-center text-muted py-5">
              데이터가 없습니다.
            </div>
            <div v-else class="consumer-list">
              <div
                v-for="(user, index) in topUsers"
                :key="user.userId"
                class="consumer-item"
              >
                <div class="consumer-rank">{{ index + 1 }}</div>
                <div class="consumer-avatar" :class="getConsumerAvatarClass(index)">
                  <i class="bi bi-person"></i>
                </div>
                <div class="consumer-info">
                  <p class="consumer-name">{{ user.fullName || user.email }}</p>
                  <div class="consumer-bar">
                    <div
                      class="consumer-bar-fill"
                      :style="{ width: topUsersMaxCalls ? (user.requestCount / topUsersMaxCalls * 100) + '%' : '0%' }"
                    ></div>
                  </div>
                  <div class="consumer-meta">${{ user.totalCost.toFixed(2) }}</div>
                </div>
                <span class="consumer-count">{{ formatNumber(user.requestCount) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0">서비스별 비용 분포</h5>
          </div>
          <div class="card-body">
            <div v-if="!costAnalysis || costAnalysis.serviceCosts.length === 0" class="text-center text-muted py-5">
              데이터가 없습니다.
            </div>
            <div v-else>
              <div class="analytics-cost-hero">
                <p class="analytics-cost-hero-value">${{ costAnalysis.totalCost.toFixed(2) }}</p>
                <p class="analytics-cost-hero-period">총 비용 ({{ formatDate(costAnalysis.startDate) }} ~ {{ formatDate(costAnalysis.endDate) }})</p>
              </div>
              <div class="table-responsive">
                <table class="table table-sm aiuiux-table">
                  <thead>
                    <tr>
                      <th>서비스</th>
                      <th class="text-end">비용</th>
                      <th class="text-end">비율</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="service in costAnalysis.serviceCosts" :key="service.serviceId">
                      <td>
                        <i :class="getServiceIcon(service.serviceName)" :style="{ color: getServiceColor(service.serviceName) }"></i>
                        {{ service.serviceName }}
                      </td>
                      <td class="text-end">${{ service.totalCost.toFixed(2) }}</td>
                      <td class="text-end">{{ service.percentage.toFixed(1) }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 주요 인사이트 -->
    <div class="row mb-4">
      <div class="col-lg-12 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent">
            <h5 class="card-title mb-0"><i class="bi bi-lightbulb"></i> 주요 인사이트</h5>
          </div>
          <div class="card-body p-0">
            <div class="alert-list">
              <div class="alert-item alert-item-info">
                <div class="alert-icon"><i class="bi bi-graph-up-arrow"></i></div>
                <div class="alert-content">
                  <p class="alert-title">인기 서비스</p>
                  <p class="alert-desc">
                    <span v-if="topService">{{ topService }}</span>
                    <span v-else>-</span>가 가장 많이 사용됩니다.
                  </p>
                  <span class="alert-time">선택 기간 기준</span>
                </div>
              </div>
              <div class="alert-item alert-item-success">
                <div class="alert-icon"><i class="bi bi-people"></i></div>
                <div class="alert-content">
                  <p class="alert-title">최고 사용자</p>
                  <p class="alert-desc">
                    <span v-if="topUsers.length > 0">{{ topUsers[0].fullName || topUsers[0].email }}</span>
                    <span v-else>-</span>
                    · {{ topUsers.length > 0 ? formatNumber(topUsers[0].requestCount) : 0 }} 호출
                  </p>
                  <span class="alert-time">API 호출 TOP 1</span>
                </div>
              </div>
              <div class="alert-item alert-item-warning">
                <div class="alert-icon"><i class="bi bi-currency-dollar"></i></div>
                <div class="alert-content">
                  <p class="alert-title">총 비용</p>
                  <p class="alert-desc">
                    선택 기간 ${{ stats.totalCost.toFixed(2) }} · 이번 달 ${{ dashboardStats.thisMonthCost.toFixed(2) }}
                  </p>
                  <span class="alert-time">실시간 집계</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 에이전트별 통계 -->
    <div class="card aiuiux-card mb-4" v-if="myAgents.length > 0">
      <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
        <h5 class="mb-0"><i class="bi bi-robot"></i> 내 에이전트별 통계</h5>
        <div class="d-flex gap-2 align-items-center">
          <select class="form-select form-select-sm" style="width:auto" v-model="agentStatPeriod" @change="loadAgentStats">
            <option value="day">오늘</option>
            <option value="week">이번 주</option>
            <option value="month">이번 달</option>
            <option value="year">올해</option>
          </select>
          <select class="form-select form-select-sm" style="width:auto" v-model="selectedAgentId" @change="loadAgentStats">
            <option v-for="a in myAgents" :key="a.agentId" :value="a.agentId">{{ a.agentName }}</option>
          </select>
        </div>
      </div>
      <div class="card-body">
        <div v-if="agentStatsLoading" class="text-center py-3"><div class="spinner-border spinner-border-sm"></div></div>
        <div v-else-if="agentStats">
          <div class="row g-3 mb-3">
            <div class="col-sm-6 col-md-3">
              <div class="border rounded p-3 text-center">
                <div class="fs-4 fw-bold text-primary">{{ agentStats.conversations }}</div>
                <div class="small text-muted">대화 수</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="border rounded p-3 text-center">
                <div class="fs-4 fw-bold text-success">{{ formatNumber(agentStats.totalRequests) }}</div>
                <div class="small text-muted">총 요청</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="border rounded p-3 text-center">
                <div class="fs-4 fw-bold text-info">{{ formatNumber(agentStats.totalTokens) }}</div>
                <div class="small text-muted">총 토큰</div>
              </div>
            </div>
            <div class="col-sm-6 col-md-3">
              <div class="border rounded p-3 text-center">
                <div class="fs-4 fw-bold text-warning">${{ (agentStats.totalCost || 0).toFixed(4) }}</div>
                <div class="small text-muted">총 비용</div>
              </div>
            </div>
          </div>
          <div class="row g-3">
            <div class="col-sm-4">
              <div class="border rounded p-3 text-center">
                <div class="fs-5 fw-bold">{{ agentStats.avgResponseTime }}ms</div>
                <div class="small text-muted">평균 응답시간</div>
              </div>
            </div>
            <div class="col-sm-4">
              <div class="border rounded p-3 text-center">
                <div class="fs-5 fw-bold text-success">{{ agentStats.successRate }}%</div>
                <div class="small text-muted">성공률</div>
              </div>
            </div>
            <div class="col-sm-4">
              <div class="border rounded p-3 text-center">
                <div class="fs-5 fw-bold text-danger">{{ agentStats.errorCount }}</div>
                <div class="small text-muted">오류 수</div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-muted text-center py-3">통계 데이터가 없습니다.</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { UsageStatsDto, CostAnalysisDto, UserUsageDto, DashboardStatsDto } from '@/types'

interface AnalyticsStats {
  totalCalls: number
  totalCost: number
  avgResponseTime: number
  totalTokens?: number
}

interface ServiceStat {
  serviceName: string
  percentage: number
}

interface DailyUsage {
  date: string
  requestCount: number
  totalCost: number
  avgResponseTime: number
}

const period = ref('month')
const loading = ref(false)

const dashboardStats = ref<DashboardStatsDto>({
  totalUsers: 0,
  activeUsers: 0,
  todayApiCalls: 0,
  thisMonthCost: 0
})

const stats = ref<AnalyticsStats>({
  totalCalls: 0,
  totalCost: 0,
  avgResponseTime: 0
})

const serviceStats = ref<ServiceStat[]>([])
const usageStats = ref<UsageStatsDto[]>([])
const costAnalysis = ref<CostAnalysisDto | null>(null)
const topUsers = ref<UserUsageDto[]>([])

const topService = computed(() => {
  if (serviceStats.value.length === 0) return null
  return serviceStats.value[0].serviceName
})

const topUsersMaxCalls = computed(() => {
  if (topUsers.value.length === 0) return 0
  return Math.max(...topUsers.value.map(u => u.requestCount))
})

const dailyUsageData = computed<DailyUsage[]>(() => {
  const dailyMap = new Map<string, { requestCount: number; totalCost: number; totalResponseTime: number; count: number }>()
  
  usageStats.value.forEach(stat => {
    const dateKey = stat.date.split('T')[0]
    const existing = dailyMap.get(dateKey) || { requestCount: 0, totalCost: 0, totalResponseTime: 0, count: 0 }
    
    dailyMap.set(dateKey, {
      requestCount: existing.requestCount + stat.requestCount,
      totalCost: existing.totalCost + stat.totalCost,
      totalResponseTime: existing.totalResponseTime + stat.averageResponseTime,
      count: existing.count + 1
    })
  })
  
  return Array.from(dailyMap.entries())
    .map(([date, data]) => ({
      date,
      requestCount: data.requestCount,
      totalCost: data.totalCost,
      avgResponseTime: data.count > 0 ? Math.round(data.totalResponseTime / data.count) : 0
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(-30) // 최근 30일
})

const loadData = async () => {
  try {
    loading.value = true
    const endDate = new Date()
    const startDate = new Date()
    
    switch (period.value) {
      case 'today':
        startDate.setHours(0, 0, 0, 0)
        break
      case 'week':
        startDate.setDate(startDate.getDate() - 7)
        break
      case 'month':
        startDate.setMonth(startDate.getMonth() - 1)
        break
    }

    // Dashboard 통계 (전체 시스템 통계)
    const dashboardRes = await api.get<DashboardStatsDto>('/analytics/dashboard')
    dashboardStats.value = dashboardRes.data || {
      totalUsers: 0,
      activeUsers: 0,
      todayApiCalls: 0,
      thisMonthCost: 0
    }

    // 사용량 통계 및 비용 분석
    const [usageRes, costRes, topUsersRes] = await Promise.all([
      api.get<UsageStatsDto[]>('/analytics/usage', {
        params: { startDate: startDate.toISOString(), endDate: endDate.toISOString() }
      }).catch(() => ({ data: [] })),
      api.get<CostAnalysisDto>('/analytics/cost', {
        params: { startDate: startDate.toISOString(), endDate: endDate.toISOString() }
      }).catch(() => ({ data: null })),
      api.get<UserUsageDto[]>('/analytics/top-users', {
        params: { top: 10 }
      }).catch(() => ({ data: [] }))
    ])

    usageStats.value = usageRes.data || []
    costAnalysis.value = costRes.data || null
    topUsers.value = topUsersRes.data || []

    // 선택 기간 통계 계산
    const totalCalls = usageStats.value.reduce((sum, s) => sum + s.requestCount, 0)
    const totalCost = usageStats.value.reduce((sum, s) => sum + s.totalCost, 0)
    const totalResponseTime = usageStats.value.reduce((sum, s) => sum + s.averageResponseTime, 0)
    const count = usageStats.value.length

    stats.value = {
      totalCalls,
      totalCost,
      avgResponseTime: count > 0 ? Math.round(totalResponseTime / count) : 0,
      totalTokens: usageStats.value.reduce((sum, s) => sum + ((s as any).totalTokens || 0), 0)
    }

    // 서비스별 통계 (비용 분석 데이터 사용)
    if (costAnalysis.value && costAnalysis.value.serviceCosts.length > 0) {
      serviceStats.value = costAnalysis.value.serviceCosts.map(service => ({
        serviceName: service.serviceName,
        percentage: Number(service.percentage.toFixed(1))
      })).sort((a, b) => b.percentage - a.percentage)
    } else {
      // 비용 분석 데이터가 없으면 사용량 통계로 계산
      const serviceMap = new Map<string, number>()
      usageStats.value.forEach(s => {
        const current = serviceMap.get(s.serviceName) || 0
        serviceMap.set(s.serviceName, current + s.requestCount)
      })

      const total = Array.from(serviceMap.values()).reduce((sum, v) => sum + v, 0)
      serviceStats.value = Array.from(serviceMap.entries()).map(([name, count]) => ({
        serviceName: name,
        percentage: total > 0 ? Math.round((count / total) * 100) : 0
      })).sort((a, b) => b.percentage - a.percentage)
    }
  } catch (error) {
    console.error('Error loading analytics data:', error)
  } finally {
    loading.value = false
  }
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit' 
  })
}

const formatDayOfWeek = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('ko-KR', { weekday: 'short' })
}

const getServiceIcon = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return 'bi bi-chat-square-text'
  if (name.includes('claude')) return 'bi bi-robot'
  if (name.includes('cursor')) return 'bi bi-code-slash'
  if (name.includes('copilot')) return 'bi bi-github'
  if (name.includes('gemini')) return 'bi bi-google'
  if (name.includes('dall') || name.includes('imagen') || name.includes('flux')) return 'bi bi-image'
  return 'bi bi-circle-fill'
}

const getServiceColor = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return '#0dcaf0'
  if (name.includes('claude')) return '#198754'
  if (name.includes('cursor')) return '#ffc107'
  if (name.includes('copilot')) return '#6c757d'
  if (name.includes('gemini')) return '#4285f4'
  if (name.includes('dall') || name.includes('imagen') || name.includes('flux')) return '#9c27b0'
  return '#6c757d'
}

const avatarClasses = ['consumer-app', 'consumer-mobile', 'consumer-analytics', 'consumer-auto', 'consumer-dev']
const getConsumerAvatarClass = (index: number): string => avatarClasses[index % avatarClasses.length] || 'consumer-user'

// ── 에이전트별 통계 ─────────────────────────────────────────────────────────
interface AgentSimple { agentId: number; agentName: string }
interface AgentStat {
  conversations: number; totalRequests: number; totalTokens: number
  totalCost: number; avgResponseTime: number; successRate: number; errorCount: number
}

const myAgents = ref<AgentSimple[]>([])
const selectedAgentId = ref<number | null>(null)
const agentStatPeriod = ref('month')
const agentStats = ref<AgentStat | null>(null)
const agentStatsLoading = ref(false)

const loadMyAgents = async () => {
  try {
    const res = await api.get<any[]>('/agents')
    myAgents.value = (res.data || []).map((a: any) => ({ agentId: a.agentId, agentName: a.agentName }))
    if (myAgents.value.length > 0) {
      selectedAgentId.value = myAgents.value[0].agentId
      await loadAgentStats()
    }
  } catch { /* 무시 */ }
}

const loadAgentStats = async () => {
  if (!selectedAgentId.value) return
  try {
    agentStatsLoading.value = true
    const res = await api.get(`/analytics/agents/${selectedAgentId.value}/stats`, {
      params: { period: agentStatPeriod.value }
    })
    agentStats.value = res.data
  } catch { agentStats.value = null }
  finally { agentStatsLoading.value = false }
}

onMounted(() => {
  loadData()
  loadMyAgents()
})
</script>

<style scoped>
.progress {
  border-radius: 4px;
}
</style>
