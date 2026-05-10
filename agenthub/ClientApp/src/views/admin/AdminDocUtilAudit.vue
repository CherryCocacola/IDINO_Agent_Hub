<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilAudit.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilAudit.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-primary btn-sm"
          @click="exportCsv"
          :disabled="exporting"
        >
          <i class="bi bi-download me-1" aria-hidden="true"></i>
          {{ exporting ? t('adminDocutilAudit.exporting') : t('adminDocutilAudit.exportCsv') }}
        </button>
      </div>
    </div>

    <!-- 알림 -->
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
    <div
      v-if="successMessage"
      class="alert alert-success d-flex justify-content-between align-items-center"
      role="alert"
    >
      <span>{{ successMessage }}</span>
      <button
        type="button"
        class="btn-close"
        :aria-label="t('common.close')"
        @click="successMessage = ''"
      ></button>
    </div>

    <!-- 필터 카드 -->
    <div class="card shadow-sm mb-3">
      <div class="card-body">
        <h2 class="h6 m-0 mb-3">{{ t('adminDocutilAudit.filters') }}</h2>
        <div class="row g-2">
          <div class="col-12 col-md-3">
            <label class="form-label small text-muted m-0" :for="actionId">
              {{ t('adminDocutilAudit.filterAction') }}
            </label>
            <input
              :id="actionId"
              v-model="filterAction"
              type="text"
              class="form-control form-control-sm"
              :placeholder="t('adminDocutilAudit.filterActionPlaceholder')"
              @keydown.enter.prevent="applyFilters"
            />
          </div>
          <div class="col-12 col-md-3">
            <label class="form-label small text-muted m-0" :for="resTypeId">
              {{ t('adminDocutilAudit.filterResourceType') }}
            </label>
            <input
              :id="resTypeId"
              v-model="filterResourceType"
              type="text"
              class="form-control form-control-sm"
              :placeholder="t('adminDocutilAudit.filterResourceTypePlaceholder')"
              @keydown.enter.prevent="applyFilters"
            />
          </div>
          <div class="col-12 col-md-3">
            <label class="form-label small text-muted m-0" :for="userIdId">
              {{ t('adminDocutilAudit.filterUserId') }}
            </label>
            <input
              :id="userIdId"
              v-model="filterUserId"
              type="text"
              class="form-control form-control-sm"
              :placeholder="t('adminDocutilAudit.filterUserIdPlaceholder')"
              @keydown.enter.prevent="applyFilters"
            />
          </div>
          <div class="col-6 col-md-3">
            <label class="form-label small text-muted m-0" :for="startId">
              {{ t('adminDocutilAudit.filterStartDate') }}
            </label>
            <input
              :id="startId"
              v-model="filterStartDate"
              type="datetime-local"
              class="form-control form-control-sm"
            />
          </div>
          <div class="col-6 col-md-3">
            <label class="form-label small text-muted m-0" :for="endId">
              {{ t('adminDocutilAudit.filterEndDate') }}
            </label>
            <input
              :id="endId"
              v-model="filterEndDate"
              type="datetime-local"
              class="form-control form-control-sm"
            />
          </div>
          <div class="col-12 col-md-9 d-flex align-items-end gap-2">
            <button class="btn btn-primary btn-sm" @click="applyFilters">
              <i class="bi bi-funnel me-1" aria-hidden="true"></i>
              {{ t('adminDocutilAudit.applyFilters') }}
            </button>
            <button class="btn btn-outline-secondary btn-sm" @click="clearFilters">
              <i class="bi bi-x-lg me-1" aria-hidden="true"></i>
              {{ t('adminDocutilAudit.clearFilters') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 페이지 크기 + 합계 -->
    <div class="d-flex flex-wrap align-items-center gap-2 mb-2 small">
      <span class="text-muted">
        {{ t('adminDocutilAudit.totalCount', { total: formatNumber(totalCount) }) }}
      </span>
      <div class="ms-auto d-flex align-items-center gap-2">
        <label class="text-muted m-0" :for="sizeId">
          {{ t('adminDocutilAudit.pageSize') }}:
        </label>
        <select
          :id="sizeId"
          v-model.number="pageSize"
          class="form-select form-select-sm"
          style="width: 90px"
          @change="onPageSizeChange"
        >
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
      </div>
    </div>

    <!-- 표 -->
    <div class="card shadow-sm">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-sm table-hover m-0 align-middle">
            <thead class="table-light">
              <tr>
                <th scope="col" style="min-width: 160px">
                  {{ t('adminDocutilAudit.colCreatedAt') }}
                </th>
                <th scope="col" style="min-width: 120px">
                  {{ t('adminDocutilAudit.colAction') }}
                </th>
                <th scope="col" style="min-width: 110px">
                  {{ t('adminDocutilAudit.colResourceType') }}
                </th>
                <th scope="col" style="min-width: 240px">
                  {{ t('adminDocutilAudit.colResourceId') }}
                </th>
                <th scope="col" style="min-width: 240px">
                  {{ t('adminDocutilAudit.colUserId') }}
                </th>
                <th scope="col" style="min-width: 120px">
                  {{ t('adminDocutilAudit.colIpAddress') }}
                </th>
                <th scope="col" style="width: 80px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="7" class="text-center text-muted py-4">
                  {{ t('adminDocutilAudit.loading') }}
                </td>
              </tr>
              <tr v-else-if="entries.length === 0">
                <td colspan="7" class="text-center text-muted py-4">
                  {{ t('adminDocutilAudit.empty') }}
                </td>
              </tr>
              <tr v-for="entry in entries" :key="entry.id" v-else>
                <td>
                  <code class="small">{{ formatDateTime(entry.createdAt) }}</code>
                </td>
                <td>
                  <span class="badge bg-secondary-subtle text-body">{{ entry.action }}</span>
                </td>
                <td>{{ entry.resourceType }}</td>
                <td>
                  <code class="small">
                    {{ entry.resourceId ?? t('adminDocutilAudit.noResourceId') }}
                  </code>
                </td>
                <td>
                  <code class="small">
                    {{ entry.userId ?? t('adminDocutilAudit.noUserId') }}
                  </code>
                </td>
                <td>
                  <code class="small">
                    {{ entry.ipAddress ?? t('adminDocutilAudit.noIpAddress') }}
                  </code>
                </td>
                <td class="text-end">
                  <button
                    type="button"
                    class="btn btn-link btn-sm p-0"
                    @click="openDetailsModal(entry)"
                  >
                    {{ t('adminDocutilAudit.openDetails') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 페이지네이션 -->
    <div class="d-flex justify-content-end align-items-center gap-2 mt-3 small">
      <button
        class="btn btn-outline-secondary btn-sm"
        :disabled="page <= 1 || loading"
        @click="setPage(page - 1)"
      >
        <i class="bi bi-chevron-left" aria-hidden="true"></i>
        {{ t('adminDocutilAudit.prevPage') }}
      </button>
      <span class="text-muted">
        {{ t('adminDocutilAudit.page') }} {{ page }} / {{ totalPages }}
      </span>
      <button
        class="btn btn-outline-secondary btn-sm"
        :disabled="page >= totalPages || loading"
        @click="setPage(page + 1)"
      >
        {{ t('adminDocutilAudit.nextPage') }}
        <i class="bi bi-chevron-right" aria-hidden="true"></i>
      </button>
    </div>

    <!-- 상세 모달 -->
    <div
      v-if="detailsTarget"
      class="modal fade show"
      style="display: block; background: rgba(0, 0, 0, 0.4)"
      tabindex="-1"
      role="dialog"
      :aria-label="t('adminDocutilAudit.modalDetailsTitle')"
    >
      <div class="modal-dialog modal-lg modal-dialog-scrollable" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilAudit.modalDetailsTitle') }}</h5>
            <button
              type="button"
              class="btn-close"
              :aria-label="t('common.close')"
              @click="closeDetailsModal"
            ></button>
          </div>
          <div class="modal-body">
            <dl class="row">
              <dt class="col-sm-4 text-muted">{{ t('adminDocutilAudit.modalIdLabel') }}</dt>
              <dd class="col-sm-8">
                <code class="small">{{ detailsTarget.id }}</code>
              </dd>

              <dt class="col-sm-4 text-muted">
                {{ t('adminDocutilAudit.modalCreatedAtLabel') }}
              </dt>
              <dd class="col-sm-8">{{ formatDateTime(detailsTarget.createdAt) }}</dd>

              <dt class="col-sm-4 text-muted">{{ t('adminDocutilAudit.modalActionLabel') }}</dt>
              <dd class="col-sm-8">
                <span class="badge bg-secondary-subtle text-body">{{ detailsTarget.action }}</span>
              </dd>

              <dt class="col-sm-4 text-muted">
                {{ t('adminDocutilAudit.modalResourceTypeLabel') }}
              </dt>
              <dd class="col-sm-8">{{ detailsTarget.resourceType }}</dd>

              <dt class="col-sm-4 text-muted">
                {{ t('adminDocutilAudit.modalResourceIdLabel') }}
              </dt>
              <dd class="col-sm-8">
                <code class="small">
                  {{ detailsTarget.resourceId ?? t('adminDocutilAudit.noResourceId') }}
                </code>
              </dd>

              <dt class="col-sm-4 text-muted">{{ t('adminDocutilAudit.modalOrgIdLabel') }}</dt>
              <dd class="col-sm-8">
                <code class="small">{{ detailsTarget.organizationId }}</code>
              </dd>

              <dt class="col-sm-4 text-muted">{{ t('adminDocutilAudit.modalUserIdLabel') }}</dt>
              <dd class="col-sm-8">
                <code class="small">
                  {{ detailsTarget.userId ?? t('adminDocutilAudit.noUserId') }}
                </code>
              </dd>

              <dt class="col-sm-4 text-muted">{{ t('adminDocutilAudit.modalIpLabel') }}</dt>
              <dd class="col-sm-8">
                <code class="small">
                  {{ detailsTarget.ipAddress ?? t('adminDocutilAudit.noIpAddress') }}
                </code>
              </dd>
            </dl>
            <hr />
            <h6 class="mb-2">{{ t('adminDocutilAudit.modalDetailsLabel') }}</h6>
            <pre
              v-if="detailsTarget.details"
              class="bg-light p-2 small"
              style="max-height: 300px; overflow: auto;"
            >{{ formatDetailsJson(detailsTarget.details) }}</pre>
            <p v-else class="text-muted small m-0">
              {{ t('adminDocutilAudit.modalNoDetails') }}
            </p>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary btn-sm"
              @click="closeDetailsModal"
            >
              {{ t('adminDocutilAudit.modalClose') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilAudit.vue — Phase 10.2a (2026-05-10).
 *
 * DocUtil 의 감사 로그 조회 + CSV 내보내기.
 *
 * 호출 흐름:
 *   본 컴포넌트
 *     -> services/docutilService (listAuditLogs / exportAuditLogs)
 *     -> AgentHub `/api/admin/docutil/audit-logs[/export]` (AdminDocUtilOperationsController)
 *     -> IDocUtilClient
 *     -> DocUtil FastAPI `/api/v1/audit-logs[/export]`
 *
 * 표시 정책:
 *   - 컬럼: 일시 / Action / 리소스 종류 / 리소스 ID / 사용자 / IP / [상세 보기]
 *   - 메타데이터(details) 는 모달에서 raw JSON 으로 노출(추정 금지 — DocUtil 측 free-form dict)
 *   - CSV export 는 한글 RFC 5987 파일명 보존 + Blob URL.revokeObjectURL 정리
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  listAuditLogs,
  exportAuditLogs,
  type DocUtilAuditLogEntry,
  type AuditLogFilters
} from '@/services/docutilService'

const { t } = useI18n()

// ─── 상태 ──────────────────────────────────────────────────────────────────
const entries = ref<DocUtilAuditLogEntry[]>([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = ref(50)

const loading = ref(false)
const exporting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// 필터 (input 바인딩 — 적용 시 commit)
const filterAction = ref('')
const filterResourceType = ref('')
const filterUserId = ref('')
const filterStartDate = ref('') // datetime-local 형식 (YYYY-MM-DDTHH:mm)
const filterEndDate = ref('')

const detailsTarget = ref<DocUtilAuditLogEntry | null>(null)

// 입력 ID 안정 식별자 (for/aria 연결).
const actionId = 'audit-filter-action'
const resTypeId = 'audit-filter-resource-type'
const userIdId = 'audit-filter-user-id'
const startId = 'audit-filter-start'
const endId = 'audit-filter-end'
const sizeId = 'audit-page-size'

// ─── computed ─────────────────────────────────────────────────────────────
const totalPages = computed(() => {
  if (totalCount.value <= 0 || pageSize.value <= 0) return 1
  return Math.max(1, Math.ceil(totalCount.value / pageSize.value))
})

// ─── 포매터 ────────────────────────────────────────────────────────────
function formatNumber(n: number): string {
  if (Number.isNaN(n)) return '0'
  return n.toLocaleString()
}

function formatDateTime(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

function formatDetailsJson(details: Record<string, unknown> | null): string {
  if (!details) return ''
  try {
    return JSON.stringify(details, null, 2)
  } catch {
    return String(details)
  }
}

/** datetime-local (YYYY-MM-DDTHH:mm) → ISO-8601 UTC. */
function toIsoUtc(local: string): string | undefined {
  if (!local || !local.trim()) return undefined
  const d = new Date(local)
  if (Number.isNaN(d.getTime())) return undefined
  return d.toISOString()
}

// ─── 데이터 로드 ────────────────────────────────────────────────────────
function buildFilters(): AuditLogFilters {
  return {
    page: page.value,
    size: pageSize.value,
    action: filterAction.value,
    resourceType: filterResourceType.value,
    userId: filterUserId.value,
    startDate: toIsoUtc(filterStartDate.value),
    endDate: toIsoUtc(filterEndDate.value)
  }
}

async function loadAuditLogs(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const list = await listAuditLogs(buildFilters())
    entries.value = list.items
    totalCount.value = list.total
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err, 'errorBoundary')
  } finally {
    loading.value = false
  }
}

function extractErrorMessage(err: unknown, fallbackKey: string): string {
  if (typeof err === 'object' && err !== null) {
    const r = (err as { response?: { data?: { message?: string } } }).response
    const msg = r?.data?.message
    if (typeof msg === 'string' && msg.trim()) return msg
    const m = (err as { message?: string }).message
    if (typeof m === 'string' && m.trim()) return m
  }
  return t(`adminDocutilAudit.${fallbackKey}`)
}

function applyFilters(): void {
  page.value = 1
  void loadAuditLogs()
}

function clearFilters(): void {
  filterAction.value = ''
  filterResourceType.value = ''
  filterUserId.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  page.value = 1
  void loadAuditLogs()
}

function setPage(newPage: number): void {
  if (newPage < 1 || newPage > totalPages.value) return
  page.value = newPage
  void loadAuditLogs()
}

function onPageSizeChange(): void {
  page.value = 1
  void loadAuditLogs()
}

// ─── CSV export ─────────────────────────────────────────────────────────
async function exportCsv(): Promise<void> {
  exporting.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const result = await exportAuditLogs({
      action: filterAction.value,
      resourceType: filterResourceType.value,
      userId: filterUserId.value,
      startDate: toIsoUtc(filterStartDate.value),
      endDate: toIsoUtc(filterEndDate.value)
    })
    triggerDownload(result.blob, result.fileName)
    successMessage.value = t('adminDocutilAudit.exportSuccess')
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err, 'errorExportBoundary')
  } finally {
    exporting.value = false
  }
}

function triggerDownload(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // Blob URL 정리(메모리 누수 방지).
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

// ─── 모달 ──────────────────────────────────────────────────────────────
function openDetailsModal(entry: DocUtilAuditLogEntry): void {
  detailsTarget.value = entry
}

function closeDetailsModal(): void {
  detailsTarget.value = null
}

onMounted(() => {
  void loadAuditLogs()
})
</script>

<style scoped>
.modal {
  z-index: 1050;
}
</style>
