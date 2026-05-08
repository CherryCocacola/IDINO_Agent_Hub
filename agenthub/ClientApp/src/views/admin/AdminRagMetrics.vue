<template>
  <div class="page-content-wrap">
    <!-- 페이지 헤더 -->
    <div class="page-header d-flex justify-content-between align-items-start flex-wrap gap-2">
      <div>
        <h1 class="page-heading">{{ t('adminRagMetrics.title') }}</h1>
        <p class="page-desc">{{ t('adminRagMetrics.subtitle') }}</p>
      </div>
      <div class="page-actions d-flex align-items-center gap-2">
        <!-- 자동 갱신 토글 (5초 간격, 기본 off) -->
        <div class="form-check form-switch m-0">
          <input
            id="autoRefreshSwitch"
            class="form-check-input"
            type="checkbox"
            role="switch"
            v-model="autoRefresh"
            :aria-label="t('adminRagMetrics.autoRefresh')"
          />
          <label class="form-check-label small" for="autoRefreshSwitch">
            {{ t('adminRagMetrics.autoRefresh') }}
          </label>
        </div>
        <button
          type="button"
          class="btn btn-primary btn-sm"
          @click="refresh"
          :disabled="isLoading"
          :aria-label="t('adminRagMetrics.refresh')"
        >
          <i class="bi bi-arrow-clockwise me-1" aria-hidden="true"></i>
          {{ isLoading ? t('adminRagMetrics.loading') : t('adminRagMetrics.refresh') }}
        </button>
      </div>
    </div>

    <!-- 인증 실패 안내 -->
    <div v-if="authError" class="alert alert-warning d-flex align-items-start gap-2" role="alert">
      <i class="bi bi-shield-exclamation fs-5" aria-hidden="true"></i>
      <div>
        <div class="fw-semibold">{{ t('adminRagMetrics.authErrorTitle') }}</div>
        <div class="small">{{ t('adminRagMetrics.authErrorBody') }}</div>
      </div>
    </div>

    <!-- 일반 에러 알림 -->
    <div
      v-else-if="errorMessage"
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

    <!-- 첫 로딩 (스냅샷 부재 시) -->
    <div
      v-if="isLoading && !snapshot"
      class="text-center text-muted py-5"
      role="status"
      aria-live="polite"
    >
      <div class="spinner-border spinner-border-sm" aria-hidden="true"></div>
      <span class="ms-2">{{ t('adminRagMetrics.loading') }}</span>
    </div>

    <!-- 메트릭 본체 -->
    <template v-if="snapshot">
      <!-- 마지막 갱신 시각 -->
      <div class="d-flex justify-content-end mb-2">
        <small class="text-muted">
          {{ t('adminRagMetrics.lastUpdated') }}: {{ lastUpdatedLabel }}
        </small>
      </div>

      <!-- 요약 카드 4개 -->
      <div class="row g-3 mb-4">
        <div class="col-12 col-sm-6 col-lg-3">
          <div class="card aiuiux-card summary-card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start">
                <div class="summary-card-label">{{ t('adminRagMetrics.summary.ragInvocations') }}</div>
                <i class="bi bi-search summary-card-icon" aria-hidden="true"></i>
              </div>
              <div class="summary-card-value">{{ formatNumber(snapshot.ragInvocations) }}</div>
              <div class="summary-card-sub text-muted">
                {{ t('adminRagMetrics.summary.ragZeroResults') }}: {{ formatNumber(snapshot.ragZeroResults) }}
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-sm-6 col-lg-3">
          <div class="card aiuiux-card summary-card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start">
                <div class="summary-card-label">{{ t('adminRagMetrics.summary.docUtilSearchCalls') }}</div>
                <i class="bi bi-cloud-arrow-up summary-card-icon" aria-hidden="true"></i>
              </div>
              <div class="summary-card-value">{{ formatNumber(snapshot.docUtilSearchCalls) }}</div>
              <div class="summary-card-sub text-muted">
                {{ t('adminRagMetrics.summary.failures') }}: {{ formatNumber(snapshot.docUtilSearchFailures) }}
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-sm-6 col-lg-3">
          <div class="card aiuiux-card summary-card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start">
                <div class="summary-card-label">{{ t('adminRagMetrics.summary.queryRewriteHitRatio') }}</div>
                <i class="bi bi-lightning-charge summary-card-icon" aria-hidden="true"></i>
              </div>
              <div class="summary-card-value">
                {{ formatRatio(snapshot.queryRewriteCacheHitRatio) }}
              </div>
              <div class="summary-card-sub text-muted">
                {{ t('adminRagMetrics.summary.calls') }}: {{ formatNumber(snapshot.queryRewriteCalls) }}
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-sm-6 col-lg-3">
          <div class="card aiuiux-card summary-card h-100">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-start">
                <div class="summary-card-label">{{ t('adminRagMetrics.summary.avgLatency') }}</div>
                <i class="bi bi-stopwatch summary-card-icon" aria-hidden="true"></i>
              </div>
              <div class="summary-card-value">
                {{ formatLatency(snapshot.avgDocUtilSearchLatencyMs) }}
              </div>
              <div class="summary-card-sub text-muted">
                {{ t('adminRagMetrics.summary.totalLatency') }}: {{ formatNumber(snapshot.docUtilSearchLatencyMsTotal) }} ms
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 상세 표 (모든 카운터 + 파생 통계 16개) -->
      <div class="card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex align-items-center">
          <i class="bi bi-table me-1" aria-hidden="true"></i>
          <h6 class="mb-0">{{ t('adminRagMetrics.details.title') }}</h6>
          <small class="text-muted ms-2">
            {{ t('adminRagMetrics.details.subtitle') }}
          </small>
        </div>
        <div class="table-responsive">
          <table class="table table-sm mb-0 align-middle">
            <thead>
              <tr>
                <th scope="col" class="ps-3" style="width: 35%;">{{ t('adminRagMetrics.details.metric') }}</th>
                <th scope="col" class="text-end pe-3" style="width: 25%;">{{ t('adminRagMetrics.details.value') }}</th>
                <th scope="col" class="text-muted small">{{ t('adminRagMetrics.details.note') }}</th>
              </tr>
            </thead>
            <tbody>
              <!-- Query Rewrite 그룹 -->
              <tr class="table-secondary">
                <th colspan="3" class="ps-3 small fw-semibold">
                  {{ t('adminRagMetrics.groups.queryRewrite') }}
                </th>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.queryRewriteCacheHit') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.queryRewriteCacheHit) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.cacheHit') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.queryRewriteCacheMiss') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.queryRewriteCacheMiss) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.cacheMiss') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.queryRewriteCalls') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.queryRewriteCalls) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.llmCalls') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.queryRewriteFailures') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.queryRewriteFailures) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.failures') }}</td>
              </tr>
              <tr>
                <td class="ps-3 fst-italic">{{ t('adminRagMetrics.fields.queryRewriteCacheHitRatio') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatRatio(snapshot.queryRewriteCacheHitRatio) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.derived') }}</td>
              </tr>

              <!-- DocUtil Search 그룹 -->
              <tr class="table-secondary">
                <th colspan="3" class="ps-3 small fw-semibold">
                  {{ t('adminRagMetrics.groups.docUtilSearch') }}
                </th>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.docUtilSearchCacheHit') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.docUtilSearchCacheHit) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.cacheHit') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.docUtilSearchCacheMiss') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.docUtilSearchCacheMiss) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.cacheMiss') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.docUtilSearchCalls') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.docUtilSearchCalls) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.httpCalls') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.docUtilSearchFailures') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.docUtilSearchFailures) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.failures') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.docUtilSearchLatencyMsTotal') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.docUtilSearchLatencyMsTotal) }} ms</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.latencyTotal') }}</td>
              </tr>
              <tr>
                <td class="ps-3 fst-italic">{{ t('adminRagMetrics.fields.avgDocUtilSearchLatencyMs') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatLatency(snapshot.avgDocUtilSearchLatencyMs) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.derived') }}</td>
              </tr>
              <tr>
                <td class="ps-3 fst-italic">{{ t('adminRagMetrics.fields.docUtilSearchCacheHitRatio') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatRatio(snapshot.docUtilSearchCacheHitRatio) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.derived') }}</td>
              </tr>

              <!-- RAG Pipeline 그룹 -->
              <tr class="table-secondary">
                <th colspan="3" class="ps-3 small fw-semibold">
                  {{ t('adminRagMetrics.groups.ragPipeline') }}
                </th>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.ragInvocations') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.ragInvocations) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.ragInvocations') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.ragZeroResults') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.ragZeroResults) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.ragZeroResults') }}</td>
              </tr>
              <tr>
                <td class="ps-3">{{ t('adminRagMetrics.fields.ragDistinctChunksTotal') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatNumber(snapshot.ragDistinctChunksTotal) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.distinctChunks') }}</td>
              </tr>
              <tr>
                <td class="ps-3 fst-italic">{{ t('adminRagMetrics.fields.avgRagDistinctChunks') }}</td>
                <td class="text-end pe-3 fw-semibold">{{ formatDecimal(snapshot.avgRagDistinctChunks) }}</td>
                <td class="text-muted small">{{ t('adminRagMetrics.notes.derived') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/**
 * Phase 5 RAG 메트릭 대시보드.
 *
 * - Phase 4 신규 endpoint `GET /api/admin/metrics/rag` 의 시각화 view.
 * - Admin/SuperAdmin 권한이 필요(라우트 가드 + 백엔드 [Authorize] 동시 게이트).
 * - 백엔드 응답이 in-memory 휘발성 카운터이므로 서버 재시작 시 0 으로 reset 되는 점은 의도된 단순성.
 *   외부 prometheus/시계열 영속화는 별도 트랙.
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'

const { t } = useI18n()

// ── 응답 DTO 형상 (백엔드 RagMetricsSnapshotDto 와 1:1 정렬, camelCase) ──
interface RagMetricsSnapshot {
  queryRewriteCacheHit: number
  queryRewriteCacheMiss: number
  queryRewriteCalls: number
  queryRewriteFailures: number
  docUtilSearchCacheHit: number
  docUtilSearchCacheMiss: number
  docUtilSearchCalls: number
  docUtilSearchFailures: number
  docUtilSearchLatencyMsTotal: number
  ragInvocations: number
  ragZeroResults: number
  ragDistinctChunksTotal: number
  // 파생 통계 (서버 계산값 — 0 보호 후)
  avgDocUtilSearchLatencyMs: number
  queryRewriteCacheHitRatio: number
  docUtilSearchCacheHitRatio: number
  avgRagDistinctChunks: number
}

const AUTO_REFRESH_INTERVAL_MS = 5_000

const snapshot = ref<RagMetricsSnapshot | null>(null)
const isLoading = ref(false)
const errorMessage = ref('')
const authError = ref(false)
const autoRefresh = ref(false)
const lastUpdatedAt = ref<Date | null>(null)
let autoRefreshTimer: ReturnType<typeof setInterval> | null = null

const lastUpdatedLabel = computed(() => {
  if (!lastUpdatedAt.value) return '-'
  // 한국어 환경 우선, 시스템 로케일 따름
  return lastUpdatedAt.value.toLocaleString()
})

// 안전한 숫자 포맷 (null/NaN/Infinity 보호)
function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '0'
  return Math.trunc(value).toLocaleString()
}

function formatDecimal(value: number | null | undefined, fractionDigits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '0'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits
  })
}

function formatRatio(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '0%'
  // ratio 는 0..1 range — 백분율로 환산
  const pct = Math.max(0, Math.min(1, value)) * 100
  return `${pct.toFixed(1)}%`
}

function formatLatency(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '0 ms'
  return `${value.toFixed(1)} ms`
}

async function fetchSnapshot(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  authError.value = false
  try {
    // services/api 의 axios 인스턴스 사용 — JWT 자동 부착 + baseURL=/api
    const { data } = await api.get<RagMetricsSnapshot>('/admin/metrics/rag')
    snapshot.value = data
    lastUpdatedAt.value = new Date()
  } catch (err: unknown) {
    // 인증 실패 (401/403) 는 별도 안내, 그 외는 일반 에러로
    let status: number | undefined
    if (err && typeof err === 'object' && 'response' in err) {
      const httpError = err as { response?: { status?: number; data?: { message?: string } } }
      status = httpError.response?.status
      if (status === 401 || status === 403) {
        authError.value = true
      } else {
        const serverMessage = httpError.response?.data?.message
        errorMessage.value =
          serverMessage || t('adminRagMetrics.errorGeneric')
      }
    } else {
      errorMessage.value = t('adminRagMetrics.errorGeneric')
    }
  } finally {
    isLoading.value = false
  }
}

function refresh(): void {
  void fetchSnapshot()
}

function startAutoRefresh(): void {
  stopAutoRefresh()
  autoRefreshTimer = setInterval(() => {
    if (!authError.value) {
      void fetchSnapshot()
    }
  }, AUTO_REFRESH_INTERVAL_MS)
}

function stopAutoRefresh(): void {
  if (autoRefreshTimer !== null) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

watch(autoRefresh, (enabled) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

onMounted(() => {
  void fetchSnapshot()
})

onBeforeUnmount(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.summary-card {
  border-left: 3px solid var(--accent-blue, #4a90e2);
}

.summary-card-label {
  font-size: 0.8125rem;
  color: var(--text-secondary, #6c757d);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.summary-card-icon {
  font-size: 1.1rem;
  color: var(--accent-blue, #4a90e2);
  opacity: 0.7;
}

.summary-card-value {
  font-size: 1.625rem;
  font-weight: 700;
  margin-top: 0.5rem;
  color: var(--text-primary, #212529);
  line-height: 1.2;
  word-break: break-all;
}

.summary-card-sub {
  font-size: 0.75rem;
  margin-top: 0.25rem;
}

.table-secondary th {
  background-color: rgba(0, 0, 0, 0.04);
}
</style>
