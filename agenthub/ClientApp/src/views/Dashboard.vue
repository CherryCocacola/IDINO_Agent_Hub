<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">시스템 대시보드</h1>
        <p class="page-desc">AI 통합관리시스템 현황을 한눈에 확인하세요</p>
      </div>
      <div class="page-actions">
        <router-link to="/usage-history" class="btn btn-outline-secondary btn-sm">
          <i class="bi bi-clock-history me-1"></i>사용 기록
        </router-link>
      </div>
    </div>

    <div v-if="statsError" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ statsError }}
      <button type="button" class="btn-close" @click="statsError = null" aria-label="닫기"></button>
    </div>

    <div class="row g-4 mb-4">
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-people"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">총 사용자</p>
            <h2 class="stat-value">
              <span v-if="loadingStats" class="spinner-border spinner-border-sm me-1" role="status"></span>
              {{ loadingStats ? '' : stats.totalUsers }}
            </h2>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-success">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-check-circle"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">활성 구독</p>
            <h2 class="stat-value">
              <span v-if="loadingStats" class="spinner-border spinner-border-sm me-1" role="status"></span>
              {{ loadingStats ? '' : stats.activeUsers }}
            </h2>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-info">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-graph-up"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">오늘 API 호출</p>
            <h2 class="stat-value">
              <span v-if="loadingStats" class="spinner-border spinner-border-sm me-1" role="status"></span>
              {{ loadingStats ? '' : stats.todayApiCalls }}
            </h2>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-danger">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-currency-dollar"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">이번 달 비용</p>
            <h2 class="stat-value">
              <span v-if="loadingStats" class="spinner-border spinner-border-sm me-1" role="status"></span>
              {{ loadingStats ? '' : '$' + formatCost(stats.thisMonthCost) }}
            </h2>
          </div>
        </div>
      </div>
    </div>

    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
        <div>
          <h5 class="card-title mb-0">최근 활동</h5>
          <p class="card-subtitle mb-0">API 사용 내역 (최근 7일)</p>
        </div>
        <router-link v-if="recentActivities.length > 0" to="/usage-history" class="btn btn-sm btn-outline-secondary">전체 보기</router-link>
      </div>
      <div class="card-body p-0">
        <div v-if="loadingActivities" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">로딩 중...</span>
          </div>
          <p class="mt-2 text-muted">데이터를 불러오는 중...</p>
        </div>
        <div v-else-if="activitiesForbidden" class="text-center text-muted py-5">
          <i class="bi bi-shield-lock" style="font-size: 2.5rem; opacity: 0.5;"></i>
          <p class="mt-3">최근 활동을 보려면 관리자 권한이 필요합니다.</p>
        </div>
        <div v-else-if="activitiesError" class="text-center py-5">
          <div class="alert alert-warning mb-0 mx-3">
            <i class="bi bi-exclamation-triangle me-2"></i>{{ activitiesError }}
          </div>
        </div>
        <div v-else-if="recentActivities.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
          <p class="mt-3">데이터가 없습니다</p>
        </div>
        <div v-else class="table-responsive">
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
              </tr>
            </thead>
            <tbody>
              <tr v-for="activity in recentActivities" :key="activity.usageId">
                <td class="text-muted fs-xs">{{ formatDateTime(activity.requestTime) }}</td>
                <td>{{ activity.userName || '-' }}</td>
                <td>
                  <div>
                    <strong>{{ activity.serviceName }}</strong><br>
                    <small class="text-muted">{{ activity.model || '-' }}</small>
                  </div>
                </td>
                <td>
                  <div class="text-truncate-ellipsis" :title="activity.prompt || '-'">
                    {{ truncateText(activity.prompt || '-', 50) }}
                  </div>
                </td>
                <td>{{ (activity.tokensUsed || 0).toLocaleString() }}</td>
                <td>{{ formatResponseTime(activity.responseTime || 0) }}</td>
                <td>${{ (activity.requestCost ?? 0).toFixed(4) }}</td>
                <td>
                  <span
                    class="status-badge"
                    :class="(activity.statusCode ?? 0) === 200 ? 'status-online' : 'status-error'"
                  >
                    {{ (activity.statusCode ?? 0) === 200 ? '성공' : '실패' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="recentActivities.length > 0 && !loadingActivities && !activitiesForbidden && !activitiesError" class="card-footer bg-transparent border-top">
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 px-1">
          <small class="uh-page-info">
            최근 <strong>{{ recentActivities.length }}</strong>건
            <template v-if="recentActivitiesTotalCount > 0">
              (전체 <strong>{{ recentActivitiesTotalCount.toLocaleString() }}</strong>건)
            </template>
          </small>
          <router-link to="/usage-history" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-clock-history me-1"></i>사용 기록 전체 보기
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

// 비용 포맷팅 함수
const formatCost = (cost: number | undefined | null): string => {
  if (cost == null || isNaN(cost)) {
    return '0.00'
  }
  return cost.toFixed(2)
}

interface DashboardStats {
  totalUsers?: number
  activeUsers?: number
  todayApiCalls?: number
  thisMonthCost?: number
  // PascalCase도 지원 (API 응답 형식에 따라)
  TotalUsers?: number
  ActiveUsers?: number
  TodayApiCalls?: number
  ThisMonthCost?: number
}

interface ApiUsage {
  usageId: number
  userId: number
  userName?: string
  serviceId: number
  serviceName: string
  model?: string
  tokensUsed?: number
  requestCost: number
  requestTime: string
  responseTime?: number
  statusCode?: number
  errorMessage?: string
  prompt?: string
}

const recentActivitiesTotalCount = ref(0)

const stats = ref<DashboardStats>({
  totalUsers: 0,
  activeUsers: 0,
  todayApiCalls: 0,
  thisMonthCost: 0
})

const loadingStats = ref(true)
const loadingActivities = ref(false)
const recentActivities = ref<ApiUsage[]>([])
const activitiesForbidden = ref(false)
const activitiesError = ref<string | null>(null)
const statsError = ref<string | null>(null)

// 시간 포맷팅 (UsageHistory와 동일)
const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString('ko-KR')
}

// 응답시간 포맷팅 (UsageHistory와 동일)
const formatResponseTime = (ms: number | undefined): string => {
  if (!ms) return '0.00초'
  return (ms / 1000).toFixed(2) + '초'
}

// 텍스트 잘림 (UsageHistory와 동일)
const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 최근 활동 로드 (최근 7일만 조회하여 속도 개선)
const loadRecentActivities = async () => {
  try {
    loadingActivities.value = true
    activitiesForbidden.value = false
    activitiesError.value = null
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - 7)
    const response = await api.get<{ items: ApiUsage[]; totalCount: number }>('/analytics/usage-history', {
      params: {
        startDate: start.toISOString(),
        endDate: end.toISOString(),
        skip: 0,
        take: 10
      }
    })
    recentActivities.value = response.data?.items || []
    recentActivitiesTotalCount.value = response.data?.totalCount ?? 0
  } catch (error: any) {
    console.error('Error loading recent activities:', error)
    if (error.response?.status === 403) {
      recentActivities.value = []
      activitiesForbidden.value = true
    } else {
      activitiesError.value = '최근 활동을 불러오지 못했습니다.'
    }
  } finally {
    loadingActivities.value = false
  }
}

onMounted(async () => {
  try {
    loadingStats.value = true
    statsError.value = null
    const response = await api.get<DashboardStats>('/analytics/dashboard')
    const data = response.data
    // PascalCase 또는 camelCase 모두 지원
    stats.value = {
      totalUsers: data.totalUsers ?? data.TotalUsers ?? 0,
      activeUsers: data.activeUsers ?? data.ActiveUsers ?? 0,
      todayApiCalls: data.todayApiCalls ?? data.TodayApiCalls ?? 0,
      thisMonthCost: data.thisMonthCost ?? data.ThisMonthCost ?? 0
    }
  } catch (error: any) {
    console.error('Error loading dashboard stats:', error)
    statsError.value = error.response?.data?.message ?? '대시보드 통계를 불러오지 못했습니다.'
  } finally {
    loadingStats.value = false
  }
  
  // 최근 활동 로드
  await loadRecentActivities()
})
</script>

<style scoped>
.uh-page-info {
  font-size: 12px;
  color: var(--ai-text-muted);
}
.uh-page-info strong {
  color: var(--ai-text-primary);
  font-weight: 600;
}
</style>
