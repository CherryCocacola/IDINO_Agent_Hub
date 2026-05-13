<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('dashboard.title') }}</h1>
        <p class="page-desc">{{ t('dashboard.subtitle') }}</p>
      </div>
      <!--
        결함 트랙 #89 M3 (2026-05-13): "사용 기록" 진입점은 admin 만 노출.
        백엔드 GET /api/analytics/usage-history 는 [Authorize(Roles="Admin")] 이므로
        일반 user 클릭 시 router 가드가 / 로 리다이렉트하여 혼란 → 진입점 자체 숨김으로 일관성 확보.
        (옵션 A: user-self 엔드포인트 신설은 후속 트랙으로 분리.)
      -->
      <div class="page-actions" v-if="isAdmin">
        <router-link to="/usage-history" class="btn btn-outline-secondary btn-sm">
          <i class="bi bi-clock-history me-1"></i>{{ t('dashboard.viewUsageHistory') }}
        </router-link>
      </div>
    </div>

    <div v-if="statsError" class="alert alert-danger alert-dismissible fade show mb-4" role="alert">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ statsError }}
      <button type="button" class="btn-close" @click="statsError = null" :aria-label="t('dashboard.closeAlert')"></button>
    </div>

    <div class="row g-4 mb-4">
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-people"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">{{ t('dashboard.totalUsers') }}</p>
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
            <p class="stat-label">{{ t('dashboard.activeSubscriptions') }}</p>
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
            <p class="stat-label">{{ t('dashboard.todayApiCalls') }}</p>
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
            <p class="stat-label">{{ t('dashboard.thisMonthCost') }}</p>
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
          <h5 class="card-title mb-0">{{ t('dashboard.recentActivity') }}</h5>
          <p class="card-subtitle mb-0">{{ t('dashboard.recentActivitySubtitle') }}</p>
        </div>
        <!-- 결함 트랙 #89 M3: 전체 보기도 admin 전용 -->
        <router-link v-if="isAdmin && recentActivities.length > 0" to="/usage-history" class="btn btn-sm btn-outline-secondary">{{ t('dashboard.viewAll') }}</router-link>
      </div>
      <div class="card-body p-0">
        <div v-if="loadingActivities" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ t('dashboard.loading') }}</span>
          </div>
          <p class="mt-2 text-muted">{{ t('dashboard.loadingData') }}</p>
        </div>
        <div v-else-if="activitiesForbidden" class="text-center text-muted py-5">
          <i class="bi bi-shield-lock" style="font-size: 2.5rem; opacity: 0.5;"></i>
          <p class="mt-3">{{ t('dashboard.adminOnlyActivities') }}</p>
        </div>
        <div v-else-if="activitiesError" class="text-center py-5">
          <div class="alert alert-warning mb-0 mx-3">
            <i class="bi bi-exclamation-triangle me-2"></i>{{ activitiesError }}
          </div>
        </div>
        <div v-else-if="recentActivities.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
          <p class="mt-3">{{ t('dashboard.noData') }}</p>
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover mb-0 aiuiux-table">
            <thead>
              <tr>
                <th>{{ t('dashboard.table.datetime') }}</th>
                <th>{{ t('dashboard.table.user') }}</th>
                <th>{{ t('dashboard.table.serviceModel') }}</th>
                <th>{{ t('dashboard.table.prompt') }}</th>
                <th>{{ t('dashboard.table.tokens') }}</th>
                <th>{{ t('dashboard.table.responseTime') }}</th>
                <th>{{ t('dashboard.table.cost') }}</th>
                <th>{{ t('dashboard.table.status') }}</th>
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
                    {{ (activity.statusCode ?? 0) === 200 ? t('dashboard.table.success') : t('dashboard.table.failure') }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <!-- 결함 트랙 #89 M3: 푸터의 "사용 기록 전체 보기" 도 admin 전용 -->
      <div v-if="isAdmin && recentActivities.length > 0 && !loadingActivities && !activitiesForbidden && !activitiesError" class="card-footer bg-transparent border-top">
        <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 px-1">
          <small class="uh-page-info">
            {{ t('dashboard.footer.recentCount', { count: recentActivities.length }) }}
            <template v-if="recentActivitiesTotalCount > 0">
              {{ t('dashboard.footer.totalCount', { total: recentActivitiesTotalCount.toLocaleString() }) }}
            </template>
          </small>
          <router-link to="/usage-history" class="btn btn-sm btn-outline-primary">
            <i class="bi bi-clock-history me-1"></i>{{ t('dashboard.footer.viewAllUsage') }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'

// 결함 트랙 #89 M2 (2026-05-13): 대시보드 본문 i18n 적용 — locale 토글 시 즉시 반응.
// useScope 기본값으로 'local' 이지만 messages 를 별도 주입하지 않으므로 fallback chain 으로 global 메시지 사용.
const { t } = useI18n()

// 결함 트랙 #89 M3 (2026-05-13): 일반 user 에게 사용기록 진입점 숨김 (백엔드 admin only).
const authStore = useAuthStore()
const isAdmin = computed<boolean>(() => {
  const roles = authStore.user?.roles ?? []
  return roles.includes('Admin') || roles.includes('SuperAdmin')
})

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
      activitiesError.value = t('dashboard.loadActivitiesFailed')
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
    statsError.value = error.response?.data?.message ?? t('dashboard.loadStatsFailed')
  } finally {
    loadingStats.value = false
  }

  // 결함 트랙 #89 M3: 최근 활동은 admin 전용 — 일반 user 는 호출 자체를 skip 하여 403 노이즈 방지.
  // (백엔드는 여전히 [Authorize(Roles="Admin")] — UI 1차 차단, 백엔드 최종 방어.)
  if (isAdmin.value) {
    await loadRecentActivities()
  } else {
    // user role: 최근 활동 카드 자체를 빈 상태로 두되, 안내 문구는 admin-only 메시지로 통일.
    activitiesForbidden.value = true
  }
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
