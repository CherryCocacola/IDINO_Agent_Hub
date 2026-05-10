<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilDashboard.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilDashboard.subtitle') }}</p>
      </div>
      <div class="page-actions d-flex align-items-center gap-2">
        <label class="form-check form-switch m-0 d-flex align-items-center gap-2">
          <input
            type="checkbox"
            class="form-check-input"
            :checked="autoRefresh"
            @change="toggleAutoRefresh"
            :aria-label="t('adminDocutilDashboard.autoRefresh')"
          />
          <span class="form-check-label small">
            {{ autoRefresh
              ? t('adminDocutilDashboard.autoRefreshOn')
              : t('adminDocutilDashboard.autoRefreshOff') }}
          </span>
        </label>
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="loadAll(true)"
          :disabled="loading"
          :aria-label="t('adminDocutilDashboard.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilDashboard.refresh') }}
        </button>
      </div>
    </div>

    <!-- 에러 알림 -->
    <div
      v-if="errorMessage"
      class="alert alert-danger d-flex justify-content-between align-items-center"
      role="alert"
    >
      <span>{{ errorMessage }}</span>
      <button
        type="button"
        class="btn-close"
        :aria-label="t('common.close')"
        @click="errorMessage = ''"
      ></button>
    </div>

    <!-- 기간 선택 + 마지막 갱신 -->
    <div class="d-flex flex-wrap align-items-center gap-3 mb-3">
      <label class="form-label m-0 small text-muted">
        {{ t('adminDocutilDashboard.period') }}:
      </label>
      <div class="btn-group btn-group-sm" role="group">
        <button
          v-for="opt in periodOptions"
          :key="opt.value || 'all'"
          type="button"
          class="btn btn-outline-secondary"
          :class="{ active: period === opt.value }"
          @click="setPeriod(opt.value)"
        >
          {{ t(opt.labelKey) }}
        </button>
      </div>
      <span v-if="lastUpdatedDisplay" class="ms-auto small text-muted">
        {{ t('adminDocutilDashboard.lastUpdated') }}: {{ lastUpdatedDisplay }}
      </span>
    </div>

    <!-- 1) 핵심 KPI -->
    <section class="mb-4" :aria-label="t('adminDocutilDashboard.metricsTitle')">
      <h2 class="h6 text-muted mb-2">{{ t('adminDocutilDashboard.metricsTitle') }}</h2>
      <div class="row g-3">
        <div class="col-6 col-md-3">
          <div class="card h-100 shadow-sm">
            <div class="card-body">
              <div class="text-muted small">{{ t('adminDocutilDashboard.metricTotalUsers') }}</div>
              <div class="h3 m-0">{{ metrics ? formatNumber(metrics.totalUsers) : '—' }}</div>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card h-100 shadow-sm">
            <div class="card-body">
              <div class="text-muted small">{{ t('adminDocutilDashboard.metricActiveUsers') }}</div>
              <div class="h3 m-0">{{ metrics ? formatNumber(metrics.activeUsers) : '—' }}</div>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card h-100 shadow-sm">
            <div class="card-body">
              <div class="text-muted small">{{ t('adminDocutilDashboard.metricTotalDocuments') }}</div>
              <div class="h3 m-0">{{ metrics ? formatNumber(metrics.totalDocuments) : '—' }}</div>
            </div>
          </div>
        </div>
        <div class="col-6 col-md-3">
          <div class="card h-100 shadow-sm">
            <div class="card-body">
              <div class="text-muted small">{{ t('adminDocutilDashboard.metricTotalSearches') }}</div>
              <div class="h3 m-0">{{ metrics ? formatNumber(metrics.totalSearches) : '—' }}</div>
            </div>
          </div>
        </div>
      </div>
      <!-- 기능별 사용량 -->
      <div class="card mt-3 shadow-sm">
        <div class="card-body">
          <h3 class="h6">{{ t('adminDocutilDashboard.metricFeatureUsage') }}</h3>
          <div v-if="!metrics" class="text-muted small">
            {{ t('adminDocutilDashboard.loading') }}
          </div>
          <div v-else-if="featureUsageEntries.length === 0" class="text-muted small">
            {{ t('adminDocutilDashboard.metricFeatureEmpty') }}
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm m-0">
              <thead>
                <tr>
                  <th scope="col">Feature</th>
                  <th scope="col" class="text-end">Count</th>
                  <th scope="col" style="width: 40%">Share</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in featureUsageEntries" :key="entry.key">
                  <th scope="row">{{ entry.key }}</th>
                  <td class="text-end">{{ formatNumber(entry.value) }}</td>
                  <td>
                    <div
                      class="progress"
                      role="progressbar"
                      :aria-valuenow="entry.value"
                      :aria-valuemin="0"
                      :aria-valuemax="featureUsageMax"
                    >
                      <div
                        class="progress-bar bg-info"
                        :style="{ width: featureUsagePercent(entry.value) + '%' }"
                      ></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <div class="row g-3 mb-4">
      <!-- 2) 응답시간 시계열 -->
      <div class="col-12 col-lg-7">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h3 class="h6">{{ t('adminDocutilDashboard.responseTimesTitle') }}</h3>
            <div v-if="loadingResponseTimes" class="text-muted small">
              {{ t('adminDocutilDashboard.loading') }}
            </div>
            <div
              v-else-if="!responseTimes || responseTimes.timestamps.length === 0"
              class="text-muted small"
            >
              {{ t('adminDocutilDashboard.responseTimesEmpty') }}
            </div>
            <template v-else>
              <div class="d-flex flex-wrap gap-3 mb-2 small text-muted">
                <span>
                  {{ t('adminDocutilDashboard.responseTimesPoints', {
                    count: responseTimes.timestamps.length
                  }) }}
                </span>
                <span>
                  {{ t('adminDocutilDashboard.responseTimesAvg') }}:
                  <strong>{{ formatNumber(rtAvg) }} {{ t('adminDocutilDashboard.responseTimesUnit') }}</strong>
                </span>
                <span>
                  {{ t('adminDocutilDashboard.responseTimesMax') }}:
                  <strong>{{ formatNumber(rtMax) }} {{ t('adminDocutilDashboard.responseTimesUnit') }}</strong>
                </span>
                <span>
                  {{ t('adminDocutilDashboard.responseTimesMin') }}:
                  <strong>{{ formatNumber(rtMin) }} {{ t('adminDocutilDashboard.responseTimesUnit') }}</strong>
                </span>
              </div>
              <div class="bar-chart">
                <div
                  v-for="(value, idx) in responseTimes.values"
                  :key="responseTimes.timestamps[idx]"
                  class="bar-chart-item"
                  :title="`${formatTimestamp(responseTimes.timestamps[idx])} — ${formatNumber(value)} ms`"
                >
                  <div class="bar-fill bg-primary" :style="{ height: rtBarHeight(value) + '%' }"></div>
                  <div class="bar-label">{{ formatTimestampShort(responseTimes.timestamps[idx]) }}</div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 3) 검색 사용량 -->
      <div class="col-12 col-lg-5">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h3 class="h6">{{ t('adminDocutilDashboard.searchUsageTitle') }}</h3>
            <div v-if="loadingSearchUsage" class="text-muted small">
              {{ t('adminDocutilDashboard.loading') }}
            </div>
            <div v-else-if="!searchUsage" class="text-muted small">
              {{ t('adminDocutilDashboard.responseTimesEmpty') }}
            </div>
            <dl v-else class="row m-0">
              <dt class="col-6 text-muted small">
                {{ t('adminDocutilDashboard.searchUsagePeriodLabel') }}
              </dt>
              <dd class="col-6">{{ searchUsage.period || '—' }}</dd>

              <dt class="col-6 text-muted small">
                {{ t('adminDocutilDashboard.searchUsageRequests') }}
              </dt>
              <dd class="col-6">{{ formatNumber(searchUsage.totalRequests) }}</dd>

              <dt class="col-6 text-muted small">
                {{ t('adminDocutilDashboard.searchUsageResponses') }}
              </dt>
              <dd class="col-6">{{ formatNumber(searchUsage.totalResponses) }}</dd>

              <dt class="col-6 text-muted small">
                {{ t('adminDocutilDashboard.searchUsageFailures') }}
              </dt>
              <dd class="col-6">{{ formatNumber(searchUsage.totalFailures) }}</dd>

              <dt class="col-6 text-muted small">
                {{ t('adminDocutilDashboard.searchUsageSuccessRate') }}
              </dt>
              <dd class="col-6">
                <strong>{{ searchSuccessRate }}</strong>
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>

    <div class="row g-3">
      <!-- 4) 검색 오류 일별 -->
      <div class="col-12 col-lg-7">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h3 class="h6">{{ t('adminDocutilDashboard.searchErrorsTitle') }}</h3>
            <div v-if="loadingSearchErrors" class="text-muted small">
              {{ t('adminDocutilDashboard.loading') }}
            </div>
            <div
              v-else-if="!searchErrors || searchErrors.dates.length === 0"
              class="text-muted small"
            >
              {{ t('adminDocutilDashboard.searchErrorsEmpty') }}
            </div>
            <template v-else>
              <div class="small text-muted mb-2">
                {{ t('adminDocutilDashboard.searchErrorsTotal') }}:
                <strong>{{ formatNumber(searchErrorsTotal) }}</strong>
              </div>
              <div class="table-responsive" style="max-height: 280px; overflow-y: auto;">
                <table class="table table-sm m-0">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col" class="text-end">Errors</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(date, idx) in searchErrors.dates"
                      :key="date"
                      :class="{ 'table-warning': searchErrors.errorCounts[idx] > 0 }"
                    >
                      <td>{{ date }}</td>
                      <td class="text-end">{{ formatNumber(searchErrors.errorCounts[idx] ?? 0) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 5) 업로드 상태 분포 -->
      <div class="col-12 col-lg-5">
        <div class="card shadow-sm h-100">
          <div class="card-body">
            <h3 class="h6">{{ t('adminDocutilDashboard.uploadStatusTitle') }}</h3>
            <div v-if="loadingUploadStatus" class="text-muted small">
              {{ t('adminDocutilDashboard.loading') }}
            </div>
            <template v-else-if="uploadStatus">
              <div class="d-flex justify-content-between mb-2">
                <span class="small text-muted">
                  {{ t('adminDocutilDashboard.uploadStatusTotal') }}:
                </span>
                <strong>{{ formatNumber(uploadStatusTotal) }}</strong>
              </div>
              <div class="progress" style="height: 24px;" role="progressbar">
                <div
                  v-if="uploadStatus.completed > 0"
                  class="progress-bar bg-success"
                  :style="{ width: uploadStatusPct(uploadStatus.completed) + '%' }"
                  :title="`${t('adminDocutilDashboard.uploadStatusCompleted')}: ${uploadStatus.completed}`"
                >
                  {{ uploadStatus.completed }}
                </div>
                <div
                  v-if="uploadStatus.processing > 0"
                  class="progress-bar bg-info"
                  :style="{ width: uploadStatusPct(uploadStatus.processing) + '%' }"
                  :title="`${t('adminDocutilDashboard.uploadStatusProcessing')}: ${uploadStatus.processing}`"
                >
                  {{ uploadStatus.processing }}
                </div>
                <div
                  v-if="uploadStatus.waiting > 0"
                  class="progress-bar bg-warning text-dark"
                  :style="{ width: uploadStatusPct(uploadStatus.waiting) + '%' }"
                  :title="`${t('adminDocutilDashboard.uploadStatusWaiting')}: ${uploadStatus.waiting}`"
                >
                  {{ uploadStatus.waiting }}
                </div>
                <div
                  v-if="uploadStatus.error > 0"
                  class="progress-bar bg-danger"
                  :style="{ width: uploadStatusPct(uploadStatus.error) + '%' }"
                  :title="`${t('adminDocutilDashboard.uploadStatusError')}: ${uploadStatus.error}`"
                >
                  {{ uploadStatus.error }}
                </div>
              </div>
              <dl class="row mt-3 m-0 small">
                <dt class="col-6 text-muted">
                  <span class="badge bg-success">{{ t('adminDocutilDashboard.uploadStatusCompleted') }}</span>
                </dt>
                <dd class="col-6 text-end">{{ formatNumber(uploadStatus.completed) }}</dd>

                <dt class="col-6 text-muted">
                  <span class="badge bg-info">{{ t('adminDocutilDashboard.uploadStatusProcessing') }}</span>
                </dt>
                <dd class="col-6 text-end">{{ formatNumber(uploadStatus.processing) }}</dd>

                <dt class="col-6 text-muted">
                  <span class="badge bg-warning text-dark">{{ t('adminDocutilDashboard.uploadStatusWaiting') }}</span>
                </dt>
                <dd class="col-6 text-end">{{ formatNumber(uploadStatus.waiting) }}</dd>

                <dt class="col-6 text-muted">
                  <span class="badge bg-danger">{{ t('adminDocutilDashboard.uploadStatusError') }}</span>
                </dt>
                <dd class="col-6 text-end">{{ formatNumber(uploadStatus.error) }}</dd>
              </dl>
            </template>
            <div v-else class="text-muted small">
              {{ t('adminDocutilDashboard.responseTimesEmpty') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilDashboard.vue — Phase 10.2a (2026-05-10).
 *
 * DocUtil 의 운영 메트릭(KPI / 응답시간 / 검색 통계 / 업로드 상태)을 한 화면에서 모니터링.
 * 5 개 endpoint 를 병렬 fetch 후 카드/표/막대로 시각화.
 *
 * 호출 흐름:
 *   본 컴포넌트
 *     -> services/docutilService (getDashboardMetrics / getDashboardResponseTimes
 *        / getDashboardSearchErrors / getDashboardSearchUsage / getDashboardUploadStatus)
 *     -> AgentHub `/api/admin/docutil/dashboard/*` (AdminDocUtilOperationsController)
 *     -> IDocUtilClient
 *     -> DocUtil FastAPI `/api/v1/dashboard/*`
 *
 * chart.js 미사용 — 기간/범위가 작으므로 간결한 div/table 시각화 우선 (vendor 청크 영향 최소).
 */
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  getDashboardMetrics,
  getDashboardResponseTimes,
  getDashboardSearchErrors,
  getDashboardSearchUsage,
  getDashboardUploadStatus,
  type DocUtilDashboardMetrics,
  type DocUtilResponseTimes,
  type DocUtilSearchErrors,
  type DocUtilSearchUsage,
  type DocUtilUploadStatus
} from '@/services/docutilService'

const { t } = useI18n()

// ─── 상태 ──────────────────────────────────────────────────────────────────
const metrics = ref<DocUtilDashboardMetrics | null>(null)
const responseTimes = ref<DocUtilResponseTimes | null>(null)
const searchErrors = ref<DocUtilSearchErrors | null>(null)
const searchUsage = ref<DocUtilSearchUsage | null>(null)
const uploadStatus = ref<DocUtilUploadStatus | null>(null)

const loadingMetrics = ref(false)
const loadingResponseTimes = ref(false)
const loadingSearchErrors = ref(false)
const loadingSearchUsage = ref(false)
const loadingUploadStatus = ref(false)

const errorMessage = ref('')

const period = ref<string>('7d')
const periodOptions = [
  { value: '', labelKey: 'adminDocutilDashboard.periodAll' },
  { value: '24h', labelKey: 'adminDocutilDashboard.period24h' },
  { value: '7d', labelKey: 'adminDocutilDashboard.period7d' },
  { value: '30d', labelKey: 'adminDocutilDashboard.period30d' }
] as const

const lastUpdated = ref<Date | null>(null)
const autoRefresh = ref(false)
let autoRefreshTimer: number | null = null

// ─── computed ────────────────────────────────────────────────────────────
const loading = computed(
  () =>
    loadingMetrics.value ||
    loadingResponseTimes.value ||
    loadingSearchErrors.value ||
    loadingSearchUsage.value ||
    loadingUploadStatus.value
)

const lastUpdatedDisplay = computed(() => {
  if (!lastUpdated.value) return ''
  return lastUpdated.value.toLocaleTimeString()
})

const featureUsageEntries = computed(() => {
  if (!metrics.value) return []
  return Object.entries(metrics.value.featureUsage)
    .map(([key, value]) => ({ key, value }))
    .sort((a, b) => b.value - a.value)
})

const featureUsageMax = computed(() => {
  const vals = featureUsageEntries.value.map((e) => e.value)
  return vals.length === 0 ? 1 : Math.max(...vals, 1)
})

function featureUsagePercent(value: number): number {
  if (featureUsageMax.value <= 0) return 0
  return Math.min(100, Math.round((value / featureUsageMax.value) * 100))
}

const rtAvg = computed(() => {
  const v = responseTimes.value?.values ?? []
  if (v.length === 0) return 0
  return v.reduce((a, b) => a + b, 0) / v.length
})
const rtMax = computed(() => {
  const v = responseTimes.value?.values ?? []
  return v.length === 0 ? 0 : Math.max(...v)
})
const rtMin = computed(() => {
  const v = responseTimes.value?.values ?? []
  return v.length === 0 ? 0 : Math.min(...v)
})

function rtBarHeight(value: number): number {
  if (rtMax.value <= 0) return 0
  return Math.max(2, Math.round((value / rtMax.value) * 100))
}

const searchSuccessRate = computed(() => {
  const u = searchUsage.value
  if (!u || u.totalRequests <= 0) return '—'
  const rate = (u.totalResponses / u.totalRequests) * 100
  return `${rate.toFixed(1)}%`
})

const searchErrorsTotal = computed(() =>
  (searchErrors.value?.errorCounts ?? []).reduce((a, b) => a + (b ?? 0), 0)
)

const uploadStatusTotal = computed(() => {
  const u = uploadStatus.value
  if (!u) return 0
  return u.completed + u.processing + u.waiting + u.error
})

function uploadStatusPct(value: number): number {
  if (uploadStatusTotal.value <= 0) return 0
  return Math.max(0, Math.min(100, (value / uploadStatusTotal.value) * 100))
}

// ─── 포매터 ────────────────────────────────────────────────────────────
function formatNumber(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '—'
  if (Math.abs(n) < 1000) return Number.isInteger(n) ? String(n) : n.toFixed(1)
  return n.toLocaleString()
}

function formatTimestamp(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

function formatTimestampShort(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// ─── 데이터 로드 ────────────────────────────────────────────────────────
async function loadMetrics(): Promise<void> {
  loadingMetrics.value = true
  try {
    metrics.value = await getDashboardMetrics()
  } finally {
    loadingMetrics.value = false
  }
}

async function loadResponseTimes(): Promise<void> {
  loadingResponseTimes.value = true
  try {
    responseTimes.value = await getDashboardResponseTimes(period.value || undefined)
  } finally {
    loadingResponseTimes.value = false
  }
}

async function loadSearchErrors(): Promise<void> {
  loadingSearchErrors.value = true
  try {
    searchErrors.value = await getDashboardSearchErrors(period.value || undefined)
  } finally {
    loadingSearchErrors.value = false
  }
}

async function loadSearchUsage(): Promise<void> {
  loadingSearchUsage.value = true
  try {
    searchUsage.value = await getDashboardSearchUsage(period.value || undefined)
  } finally {
    loadingSearchUsage.value = false
  }
}

async function loadUploadStatus(): Promise<void> {
  loadingUploadStatus.value = true
  try {
    uploadStatus.value = await getDashboardUploadStatus()
  } finally {
    loadingUploadStatus.value = false
  }
}

async function loadAll(triggeredByUser = false): Promise<void> {
  if (triggeredByUser) errorMessage.value = ''
  try {
    await Promise.all([
      loadMetrics(),
      loadResponseTimes(),
      loadSearchErrors(),
      loadSearchUsage(),
      loadUploadStatus()
    ])
    lastUpdated.value = new Date()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  }
}

function extractErrorMessage(err: unknown): string {
  if (typeof err === 'object' && err !== null) {
    const r = (err as { response?: { data?: { message?: string } } }).response
    const msg = r?.data?.message
    if (typeof msg === 'string' && msg.trim()) return msg
    const m = (err as { message?: string }).message
    if (typeof m === 'string' && m.trim()) return m
  }
  return t('adminDocutilDashboard.errorUnknown')
}

function setPeriod(value: string): void {
  if (period.value === value) return
  period.value = value
  // 기간 의존 endpoint 만 재로드(metrics/upload-status 는 미의존).
  void loadResponseTimes()
  void loadSearchErrors()
  void loadSearchUsage()
}

function toggleAutoRefresh(): void {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    autoRefreshTimer = window.setInterval(() => {
      void loadAll(false)
    }, 5000)
  } else if (autoRefreshTimer !== null) {
    window.clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

onMounted(() => {
  void loadAll(true)
})

onBeforeUnmount(() => {
  if (autoRefreshTimer !== null) {
    window.clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
})
</script>

<style scoped>
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 180px;
  padding: 8px 0;
  border-bottom: 1px solid var(--bs-border-color);
  overflow-x: auto;
}
.bar-chart-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 32px;
  height: 100%;
  justify-content: flex-end;
}
.bar-fill {
  width: 100%;
  border-radius: 2px 2px 0 0;
  min-height: 2px;
}
.bar-label {
  font-size: 0.65rem;
  color: var(--bs-secondary-color, #6c757d);
  margin-top: 4px;
  text-align: center;
  white-space: nowrap;
  transform: rotate(-30deg);
  transform-origin: top center;
}
.page-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}
</style>
