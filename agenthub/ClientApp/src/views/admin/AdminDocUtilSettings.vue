<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilSettings.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilSettings.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="refresh"
          :disabled="loading"
          :aria-label="t('adminDocutilSettings.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.refresh') }}
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

    <!-- 성공 알림 -->
    <div
      v-if="successMessage"
      class="alert alert-success d-flex justify-content-between align-items-center"
      role="status"
    >
      <span>{{ successMessage }}</span>
      <button
        type="button"
        class="btn-close"
        :aria-label="t('common.close')"
        @click="successMessage = ''"
      ></button>
    </div>

    <!-- 탭 네비게이션 -->
    <ul
      class="nav nav-tabs mb-3"
      role="tablist"
      :aria-label="t('adminDocutilSettings.tabsLabel')"
    >
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'general' }"
          role="tab"
          :aria-selected="activeTab === 'general'"
          @click="activeTab = 'general'"
        >
          <i class="bi bi-gear me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.tabGeneral') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'security' }"
          role="tab"
          :aria-selected="activeTab === 'security'"
          @click="activeTab = 'security'"
        >
          <i class="bi bi-shield-lock me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.tabSecurity') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'storage' }"
          role="tab"
          :aria-selected="activeTab === 'storage'"
          @click="activeTab = 'storage'"
        >
          <i class="bi bi-hdd-stack me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.tabStorage') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'maintenance' }"
          role="tab"
          :aria-selected="activeTab === 'maintenance'"
          @click="activeTab = 'maintenance'"
        >
          <i class="bi bi-wrench-adjustable me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.tabMaintenance') }}
        </button>
      </li>
    </ul>

    <!-- 로딩 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">{{ t('common.loading') }}</span>
      </div>
    </div>

    <!-- 일반(General) -->
    <section v-else-if="activeTab === 'general'" class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom">
        <h6 class="mb-0">
          <i class="bi bi-gear me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.generalTitle') }}
        </h6>
      </div>
      <div class="card-body">
        <form @submit.prevent="saveGeneral">
          <div class="mb-3">
            <label for="settings-default-language" class="form-label small">
              {{ t('adminDocutilSettings.defaultLanguage') }}
            </label>
            <select
              id="settings-default-language"
              v-model="general.defaultLanguage"
              class="form-select form-select-sm"
              style="max-width: 280px;"
            >
              <option value="ko">{{ t('adminDocutilSettings.langKo') }}</option>
              <option value="en">{{ t('adminDocutilSettings.langEn') }}</option>
              <option value="vi">{{ t('adminDocutilSettings.langVi') }}</option>
              <option value="ja">{{ t('adminDocutilSettings.langJa') }}</option>
              <option value="zh">{{ t('adminDocutilSettings.langZh') }}</option>
            </select>
          </div>

          <hr />

          <div class="form-check form-switch mb-3">
            <input
              id="settings-maintenance-mode"
              v-model="general.maintenanceMode"
              type="checkbox"
              class="form-check-input"
              role="switch"
            />
            <label class="form-check-label" for="settings-maintenance-mode">
              <span class="fw-medium">{{ t('adminDocutilSettings.maintenanceMode') }}</span>
              <small class="d-block text-muted">
                {{ t('adminDocutilSettings.maintenanceModeDesc') }}
              </small>
            </label>
          </div>

          <div class="text-end">
            <button
              type="submit"
              class="btn btn-primary btn-sm"
              :disabled="generalSaving"
            >
              <span
                v-if="generalSaving"
                class="spinner-border spinner-border-sm me-1"
                aria-hidden="true"
              ></span>
              <i v-else class="bi bi-save me-1" aria-hidden="true"></i>
              {{ t('adminDocutilSettings.saveGeneral') }}
            </button>
          </div>
        </form>
      </div>
    </section>

    <!-- 보안(Security) -->
    <section v-else-if="activeTab === 'security'" class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom">
        <h6 class="mb-0">
          <i class="bi bi-shield-lock me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.securityTitle') }}
        </h6>
      </div>
      <div class="card-body">
        <form @submit.prevent="saveSecurity">
          <h6 class="text-muted small fw-semibold mb-3">
            {{ t('adminDocutilSettings.passwordPolicy') }}
          </h6>

          <div class="mb-3 row align-items-center">
            <label
              for="settings-password-min-length"
              class="col-sm-5 col-form-label col-form-label-sm"
            >
              {{ t('adminDocutilSettings.passwordMinLength') }}
            </label>
            <div class="col-sm-3">
              <input
                id="settings-password-min-length"
                v-model.number="security.passwordMinLength"
                type="number"
                class="form-control form-control-sm"
                min="6"
                max="32"
              />
            </div>
          </div>

          <div class="form-check form-switch mb-2">
            <input
              id="settings-password-uppercase"
              v-model="security.passwordRequireUppercase"
              type="checkbox"
              class="form-check-input"
              role="switch"
            />
            <label class="form-check-label small" for="settings-password-uppercase">
              {{ t('adminDocutilSettings.passwordRequireUppercase') }}
            </label>
          </div>

          <div class="form-check form-switch mb-2">
            <input
              id="settings-password-number"
              v-model="security.passwordRequireNumber"
              type="checkbox"
              class="form-check-input"
              role="switch"
            />
            <label class="form-check-label small" for="settings-password-number">
              {{ t('adminDocutilSettings.passwordRequireNumber') }}
            </label>
          </div>

          <div class="form-check form-switch mb-3">
            <input
              id="settings-password-special"
              v-model="security.passwordRequireSpecial"
              type="checkbox"
              class="form-check-input"
              role="switch"
            />
            <label class="form-check-label small" for="settings-password-special">
              {{ t('adminDocutilSettings.passwordRequireSpecial') }}
            </label>
          </div>

          <hr />

          <div class="mb-3 row align-items-center">
            <label
              for="settings-session-timeout"
              class="col-sm-5 col-form-label col-form-label-sm"
            >
              {{ t('adminDocutilSettings.sessionTimeoutMinutes') }}
            </label>
            <div class="col-sm-3">
              <input
                id="settings-session-timeout"
                v-model.number="security.sessionTimeoutMinutes"
                type="number"
                class="form-control form-control-sm"
                min="5"
                max="480"
              />
            </div>
            <div class="col-sm-12">
              <small class="text-muted">
                {{ t('adminDocutilSettings.sessionTimeoutDesc') }}
              </small>
            </div>
          </div>

          <div class="text-end">
            <button
              type="submit"
              class="btn btn-primary btn-sm"
              :disabled="securitySaving"
            >
              <span
                v-if="securitySaving"
                class="spinner-border spinner-border-sm me-1"
                aria-hidden="true"
              ></span>
              <i v-else class="bi bi-save me-1" aria-hidden="true"></i>
              {{ t('adminDocutilSettings.saveSecurity') }}
            </button>
          </div>
        </form>
      </div>
    </section>

    <!-- 스토리지(Storage) -->
    <section v-else-if="activeTab === 'storage'" class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom">
        <h6 class="mb-0">
          <i class="bi bi-hdd-stack me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.storageTitle') }}
        </h6>
      </div>
      <div class="card-body">
        <!-- MinIO 연결 상태 -->
        <div class="d-flex justify-content-between align-items-start mb-3 p-3 border rounded">
          <div>
            <div class="fw-medium">{{ t('adminDocutilSettings.minioConnection') }}</div>
            <small class="text-muted">
              {{ storage.minioEndpoint || t('adminDocutilSettings.minioEndpointNone') }}
            </small>
          </div>
          <span
            v-if="storage.minioConnected"
            class="badge bg-success-subtle text-success-emphasis"
          >
            <i class="bi bi-check-circle me-1" aria-hidden="true"></i>
            {{ t('adminDocutilSettings.minioConnected') }}
          </span>
          <span v-else class="badge bg-danger-subtle text-danger-emphasis">
            <i class="bi bi-x-circle me-1" aria-hidden="true"></i>
            {{ t('adminDocutilSettings.minioDisconnected') }}
          </span>
        </div>

        <!-- 스토리지 사용량 -->
        <div class="mb-3">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="small text-muted">{{ t('adminDocutilSettings.storageUsed') }}</span>
            <span class="small fw-medium">
              {{ formatBytes(storage.usedStorageBytes) }} /
              {{ formatBytes(storage.totalStorageBytes) }}
            </span>
          </div>
          <div
            class="progress"
            role="progressbar"
            :aria-valuenow="storageUsagePercent"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-label="t('adminDocutilSettings.storageUsageLabel')"
            style="height: 10px;"
          >
            <div
              class="progress-bar"
              :class="storageBarClass"
              :style="{ width: storageUsagePercent + '%' }"
            ></div>
          </div>
          <small class="text-muted">
            {{ t('adminDocutilSettings.storageUsagePercent', { percent: storageUsagePercent }) }}
          </small>
        </div>

        <!-- 용량 요약 -->
        <div class="row g-2">
          <div class="col-md-6">
            <div class="border rounded p-3">
              <div class="small text-muted">
                {{ t('adminDocutilSettings.storageTotal') }}
              </div>
              <div class="fs-5 fw-bold">{{ formatBytes(storage.totalStorageBytes) }}</div>
            </div>
          </div>
          <div class="col-md-6">
            <div class="border rounded p-3">
              <div class="small text-muted">
                {{ t('adminDocutilSettings.storageAvailable') }}
              </div>
              <div class="fs-5 fw-bold">
                {{ formatBytes(storageAvailableBytes) }}
              </div>
            </div>
          </div>
        </div>

        <p class="text-muted small mt-3 mb-0">
          <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.storageReadonlyHint') }}
        </p>
      </div>
    </section>

    <!-- 유지보수(Maintenance) -->
    <section v-else-if="activeTab === 'maintenance'" class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom">
        <h6 class="mb-0">
          <i class="bi bi-wrench-adjustable me-1" aria-hidden="true"></i>
          {{ t('adminDocutilSettings.maintenanceTitle') }}
        </h6>
      </div>
      <div class="card-body">
        <p class="text-muted small">
          {{ t('adminDocutilSettings.maintenanceHint') }}
        </p>

        <div class="border rounded p-3">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <div class="fw-medium">
                <i class="bi bi-trash me-1" aria-hidden="true"></i>
                {{ t('adminDocutilSettings.orphanCleanupTitle') }}
              </div>
              <small class="text-muted">
                {{ t('adminDocutilSettings.orphanCleanupDesc') }}
              </small>
            </div>
            <span class="badge bg-secondary-subtle text-secondary-emphasis">
              {{ t('adminDocutilSettings.comingSoon') }}
            </span>
          </div>
          <small class="d-block text-muted mt-2">
            <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
            {{ t('adminDocutilSettings.orphanCleanupBackendNote') }}
          </small>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilSettings — DocUtil 시스템 설정 운영자 화면 (트랙 A1 Phase B, 2026-05-25).
 *
 * 진입 경로: /admin/docutil-settings (Admin / SuperAdmin 전용)
 *
 * 책임:
 *   1. 일반 / 보안 / 스토리지 / 유지보수 4 탭 운영
 *   2. AgentHub BFF `/api/admin/docutil/settings/*` 호출 (DocUtil `/api/v1/settings/*` 위임)
 *
 * 유지보수 탭:
 *   고아 벡터 cleanup endpoint 는 backend-specialist 가 정책에 따라 정의. 본 트랙에서는
 *   UI placeholder 만 제공하며 활성화 시 endpoint hookup 추가.
 */
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  getDocUtilSettings,
  updateDocUtilGeneralSettings,
  updateDocUtilSecuritySettings,
  type DocUtilGeneralSettings,
  type DocUtilSecuritySettings,
  type DocUtilStorageSettings
} from '@/services/docutilService'

const { t } = useI18n()

type Tab = 'general' | 'security' | 'storage' | 'maintenance'
const activeTab = ref<Tab>('general')

const loading = ref<boolean>(false)
const errorMessage = ref<string>('')
const successMessage = ref<string>('')

const general = ref<DocUtilGeneralSettings>({
  defaultLanguage: 'ko',
  maintenanceMode: false
})
const generalSaving = ref<boolean>(false)

const security = ref<DocUtilSecuritySettings>({
  passwordMinLength: 8,
  passwordRequireUppercase: true,
  passwordRequireNumber: true,
  passwordRequireSpecial: true,
  sessionTimeoutMinutes: 30
})
const securitySaving = ref<boolean>(false)

const storage = ref<DocUtilStorageSettings>({
  minioConnected: false,
  minioEndpoint: '',
  totalStorageBytes: 0,
  usedStorageBytes: 0
})

const storageUsagePercent = computed<number>(() => {
  if (storage.value.totalStorageBytes <= 0) return 0
  const pct = Math.round(
    (storage.value.usedStorageBytes / storage.value.totalStorageBytes) * 100
  )
  return Math.max(0, Math.min(100, pct))
})

const storageAvailableBytes = computed<number>(() => {
  const available = storage.value.totalStorageBytes - storage.value.usedStorageBytes
  return Math.max(0, available)
})

const storageBarClass = computed<string>(() => {
  if (storageUsagePercent.value >= 90) return 'bg-danger'
  if (storageUsagePercent.value >= 75) return 'bg-warning'
  return 'bg-primary'
})

function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const k = 1024
  const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(k)))
  const value = bytes / Math.pow(k, i)
  return `${value.toFixed(value >= 100 ? 0 : 2)} ${units[i]}`
}

async function fetchSettings(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await getDocUtilSettings()
    if (data.general) general.value = data.general
    if (data.security) security.value = data.security
    if (data.storage) storage.value = data.storage
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function refresh(): void {
  fetchSettings()
}

async function saveGeneral(): Promise<void> {
  generalSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const updated = await updateDocUtilGeneralSettings(general.value)
    general.value = updated
    successMessage.value = t('adminDocutilSettings.saveGeneralSuccess')
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    generalSaving.value = false
  }
}

async function saveSecurity(): Promise<void> {
  securitySaving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const updated = await updateDocUtilSecuritySettings(security.value)
    security.value = updated
    successMessage.value = t('adminDocutilSettings.saveSecuritySuccess')
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    securitySaving.value = false
  }
}

// 스토리지 PUT(`updateDocUtilStorageSettings`)은 운영자가 MinIO endpoint 등을 변경할 수 있게
// 백엔드가 정책을 결정한 뒤에 saveStorage 핸들러를 붙인다. 본 트랙은 read-only 표시만 제공.

function extractErrorMessage(err: unknown): string {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const resp = (err as { response?: { data?: { message?: string } } }).response
    if (resp?.data?.message) return resp.data.message
  }
  if (err instanceof Error) return err.message
  return t('adminDocutilSettings.errorUnknown')
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.nav-tabs .nav-link {
  color: var(--bs-secondary-color);
  border: none;
  border-bottom: 2px solid transparent;
}

.nav-tabs .nav-link.active {
  color: var(--bs-primary);
  background: transparent;
  border-bottom-color: var(--bs-primary);
  font-weight: 600;
}

.nav-tabs .nav-link:hover:not(.active) {
  border-bottom-color: var(--bs-border-color);
}
</style>
