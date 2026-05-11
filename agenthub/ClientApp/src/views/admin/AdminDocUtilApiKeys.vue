<template>
  <div class="admin-docutil-api-keys container-fluid py-4">
    <header class="mb-3 d-flex align-items-start justify-content-between flex-wrap gap-2">
      <div>
        <h1 class="h3 mb-1">{{ t('adminDocutilApiKeys.title') }}</h1>
        <p class="text-muted mb-0">{{ t('adminDocutilApiKeys.subtitle') }}</p>
      </div>
      <div class="d-flex gap-2">
        <button type="button" class="btn btn-outline-secondary" @click="loadApiKeys" :disabled="loading">
          <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilApiKeys.refresh') }}
        </button>
        <button type="button" class="btn btn-primary" @click="openCreateDialog">
          <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilApiKeys.newApiKey') }}
        </button>
      </div>
    </header>

    <div class="alert alert-warning mb-3" role="alert">
      <i class="bi bi-exclamation-triangle me-2"></i>{{ t('adminDocutilApiKeys.warningPlainKey') }}
      <div class="small mt-1">{{ t('adminDocutilApiKeys.warningAdminOnly') }}</div>
    </div>

    <div v-if="successMessage" class="alert alert-success alert-dismissible" role="alert">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''" aria-label="close"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible" role="alert">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''" aria-label="close"></button>
    </div>

    <!-- 페이지 크기 -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-3">
            <label class="form-label small">{{ t('adminDocutilApiKeys.pageSize') }}</label>
            <select v-model.number="size" class="form-select" @change="onPageSizeChange">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- 표 -->
    <div class="card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilApiKeys.loading') }}
        </div>
        <table v-else-if="apiKeys.length > 0" class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>{{ t('adminDocutilApiKeys.colLlmName') }}</th>
              <th><code>{{ t('adminDocutilApiKeys.colApiKeyPrefix') }}</code></th>
              <th>{{ t('adminDocutilApiKeys.colIsVerified') }}</th>
              <th>{{ t('adminDocutilApiKeys.colRegisteredBy') }}</th>
              <th>{{ t('adminDocutilApiKeys.colCreatedAt') }}</th>
              <th class="text-end">{{ t('adminDocutilApiKeys.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in apiKeys" :key="key.id">
              <td><strong>{{ key.llmName }}</strong></td>
              <td><code class="small">{{ key.apiKeyPrefix }}</code></td>
              <td>
                <span v-if="key.isVerified" class="badge bg-success">
                  {{ t('adminDocutilApiKeys.verified') }}
                </span>
                <span v-else class="badge bg-secondary">
                  {{ t('adminDocutilApiKeys.unverified') }}
                </span>
              </td>
              <td class="small text-muted">{{ key.registeredBy ?? '—' }}</td>
              <td class="small">{{ formatDate(key.createdAt) }}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-primary me-1"
                  :disabled="verifyingId === key.id"
                  @click="onVerify(key)"
                >
                  <span v-if="verifyingId === key.id" class="spinner-border spinner-border-sm me-1"></span>
                  {{ verifyingId === key.id
                    ? t('adminDocutilApiKeys.verifying')
                    : t('adminDocutilApiKeys.verify') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger"
                  @click="onDelete(key)"
                >
                  {{ t('adminDocutilApiKeys.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">{{ t('adminDocutilApiKeys.emptyList') }}</div>
      </div>
      <div v-if="apiKeys.length > 0" class="card-footer d-flex justify-content-between align-items-center">
        <div class="small text-muted">
          {{ t('adminDocutilApiKeys.totalCount', { total }) }}
        </div>
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: page <= 1 }">
              <button type="button" class="page-link" @click="onChangePage(page - 1)">
                {{ t('adminDocutilApiKeys.prevPage') }}
              </button>
            </li>
            <li class="page-item disabled">
              <span class="page-link">
                {{ t('adminDocutilApiKeys.page') }} {{ page }} / {{ totalPages }}
              </span>
            </li>
            <li class="page-item" :class="{ disabled: page >= totalPages }">
              <button type="button" class="page-link" @click="onChangePage(page + 1)">
                {{ t('adminDocutilApiKeys.nextPage') }}
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 등록 모달 -->
    <div
      v-if="createModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilApiKeys.createTitle') }}</h5>
            <button type="button" class="btn-close" @click="createModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-warning small">
              {{ t('adminDocutilApiKeys.createHint') }}
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilApiKeys.fieldLlmName') }} *</label>
              <input
                v-model="createForm.llmName"
                type="text"
                class="form-control"
                :placeholder="t('adminDocutilApiKeys.fieldLlmNamePlaceholder')"
                maxlength="64"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilApiKeys.fieldApiKey') }} *</label>
              <input
                v-model="createForm.apiKey"
                type="password"
                class="form-control"
                :placeholder="t('adminDocutilApiKeys.fieldApiKeyPlaceholder')"
                autocomplete="off"
                maxlength="4096"
              />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="createModal.open = false">
              {{ t('adminDocutilApiKeys.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="creating"
              @click="onCreate"
            >
              <span v-if="creating" class="spinner-border spinner-border-sm me-2"></span>
              {{ creating ? t('adminDocutilApiKeys.creating') : t('adminDocutilApiKeys.create') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="createModal.open" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import * as docutilService from '@/services/docutilService'
import type { DocUtilApiKey } from '@/services/docutilService'

const { t } = useI18n()

// 목록 상태
const loading = ref(false)
const apiKeys = ref<DocUtilApiKey[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)

const successMessage = ref('')
const errorMessage = ref('')

// 모달 / 폼
const createModal = reactive<{ open: boolean }>({ open: false })
const createForm = reactive<{ llmName: string; apiKey: string }>({ llmName: '', apiKey: '' })
const creating = ref(false)

const verifyingId = ref<string | null>(null)

const totalPages = computed(() => {
  if (total.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / size.value))
})

async function loadApiKeys() {
  loading.value = true
  errorMessage.value = ''
  try {
    const list = await docutilService.listApiKeys(page.value, size.value)
    apiKeys.value = list.items
    total.value = list.total
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilApiKeys.errorBoundary'))
    apiKeys.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadApiKeys()
})

function onPageSizeChange() {
  page.value = 1
  loadApiKeys()
}

function onChangePage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  loadApiKeys()
}

function openCreateDialog() {
  createForm.llmName = ''
  createForm.apiKey = ''
  createModal.open = true
}

async function onCreate() {
  // 검증
  if (!createForm.llmName.trim()) {
    errorMessage.value = t('adminDocutilApiKeys.validationLlmNameRequired')
    return
  }
  if (createForm.llmName.length > 64) {
    errorMessage.value = t('adminDocutilApiKeys.validationLlmNameLength')
    return
  }
  if (!createForm.apiKey.trim()) {
    errorMessage.value = t('adminDocutilApiKeys.validationApiKeyRequired')
    return
  }
  if (createForm.apiKey.length > 4096) {
    errorMessage.value = t('adminDocutilApiKeys.validationApiKeyLength')
    return
  }

  creating.value = true
  errorMessage.value = ''
  try {
    const created = await docutilService.createApiKey({
      llmName: createForm.llmName.trim(),
      apiKey: createForm.apiKey
    })
    successMessage.value = t('adminDocutilApiKeys.createSuccess', { prefix: created.apiKeyPrefix })
    createModal.open = false
    // 평문 키는 즉시 메모리에서 지운다 — 폼 reset.
    createForm.apiKey = ''
    await loadApiKeys()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilApiKeys.errorUnknown'))
  } finally {
    creating.value = false
  }
}

async function onDelete(key: DocUtilApiKey) {
  const confirmMsg = t('adminDocutilApiKeys.confirmDelete', {
    llm: key.llmName,
    prefix: key.apiKeyPrefix
  })
  if (!window.confirm(confirmMsg)) return

  errorMessage.value = ''
  try {
    await docutilService.deleteApiKey(key.id)
    successMessage.value = t('adminDocutilApiKeys.deleteSuccess')
    await loadApiKeys()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilApiKeys.errorUnknown'))
  }
}

async function onVerify(key: DocUtilApiKey) {
  verifyingId.value = key.id
  errorMessage.value = ''
  try {
    const result = await docutilService.verifyApiKey(key.id)
    if (result.isValid) {
      successMessage.value = t('adminDocutilApiKeys.verifySuccess', { message: result.message })
    } else {
      errorMessage.value = t('adminDocutilApiKeys.verifyFailed', { message: result.message })
    }
    await loadApiKeys()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilApiKeys.errorUnknown'))
  } finally {
    verifyingId.value = null
  }
}

// 유틸
function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function extractError(e: unknown, fallback: string): string {
  if (typeof e === 'object' && e !== null) {
    const anyE = e as { response?: { data?: { message?: string } }; message?: string }
    if (anyE.response?.data?.message) return anyE.response.data.message
    if (anyE.message) return anyE.message
  }
  return fallback
}
</script>

<style scoped>
.admin-docutil-api-keys .modal {
  background-color: rgba(0, 0, 0, 0.4);
}
</style>
