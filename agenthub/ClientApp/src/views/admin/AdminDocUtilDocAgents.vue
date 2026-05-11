<template>
  <div class="admin-docutil-doc-agents container-fluid py-4">
    <header class="mb-3 d-flex align-items-start justify-content-between flex-wrap gap-2">
      <div>
        <h1 class="h3 mb-1">{{ t('adminDocutilDocAgents.title') }}</h1>
        <p class="text-muted mb-0">{{ t('adminDocutilDocAgents.subtitle') }}</p>
      </div>
      <div class="d-flex gap-2">
        <button type="button" class="btn btn-outline-secondary" @click="loadAgents" :disabled="loading">
          <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilDocAgents.refresh') }}
        </button>
        <button type="button" class="btn btn-primary" @click="openCreateDialog">
          <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilDocAgents.newAgent') }}
        </button>
      </div>
    </header>

    <div class="alert alert-info mb-3" role="alert">
      <i class="bi bi-info-circle me-2"></i>{{ t('adminDocutilDocAgents.warningSeparateDomain') }}
    </div>

    <div v-if="successMessage" class="alert alert-success alert-dismissible" role="alert">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''" aria-label="close"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible" role="alert">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''" aria-label="close"></button>
    </div>

    <!-- 필터 -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-4">
            <label class="form-label small">{{ t('adminDocutilDocAgents.filterAgentType') }}</label>
            <input
              v-model="agentTypeInput"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilDocAgents.filterAgentTypePlaceholder')"
              @keyup.enter="onApplyFilters"
            />
          </div>
          <div class="col-md-3">
            <label class="form-label small">{{ t('adminDocutilDocAgents.pageSize') }}</label>
            <select v-model.number="size" class="form-select" @change="onPageSizeChange">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <div class="col-md-3 d-flex gap-2">
            <button type="button" class="btn btn-secondary flex-fill" @click="onClearFilters">
              {{ t('adminDocutilDocAgents.clearFilters') }}
            </button>
            <button type="button" class="btn btn-primary flex-fill" @click="onApplyFilters">
              {{ t('adminDocutilDocAgents.applyFilters') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 표 -->
    <div class="card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilDocAgents.loading') }}
        </div>
        <table v-else-if="agents.length > 0" class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>{{ t('adminDocutilDocAgents.colName') }}</th>
              <th>{{ t('adminDocutilDocAgents.colAgentType') }}</th>
              <th>{{ t('adminDocutilDocAgents.colLlmProvider') }}</th>
              <th>{{ t('adminDocutilDocAgents.colLlmModel') }}</th>
              <th>{{ t('adminDocutilDocAgents.colTemperature') }}</th>
              <th>{{ t('adminDocutilDocAgents.colIsActive') }}</th>
              <th>{{ t('adminDocutilDocAgents.colUpdatedAt') }}</th>
              <th class="text-end">{{ t('adminDocutilDocAgents.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in agents" :key="agent.id">
              <td>
                <strong>{{ agent.name }}</strong>
                <div v-if="agent.description" class="small text-muted text-truncate" style="max-width: 320px;">
                  {{ agent.description }}
                </div>
              </td>
              <td><code class="small">{{ agent.agentType }}</code></td>
              <td class="small">{{ agent.llmProvider ?? '—' }}</td>
              <td class="small"><code>{{ agent.llmModel }}</code></td>
              <td class="small">{{ agent.temperature }}</td>
              <td>
                <span v-if="agent.isActive" class="badge bg-success">
                  {{ t('adminDocutilDocAgents.active') }}
                </span>
                <span v-else class="badge bg-secondary">
                  {{ t('adminDocutilDocAgents.inactive') }}
                </span>
              </td>
              <td class="small">{{ formatDate(agent.updatedAt) }}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-info me-1"
                  @click="openDetail(agent)"
                >
                  {{ t('adminDocutilDocAgents.viewDetail') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-primary me-1"
                  @click="openEditDialog(agent)"
                >
                  {{ t('adminDocutilDocAgents.edit') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger"
                  @click="onDelete(agent)"
                >
                  {{ t('adminDocutilDocAgents.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">{{ t('adminDocutilDocAgents.emptyList') }}</div>
      </div>
      <div v-if="agents.length > 0" class="card-footer d-flex justify-content-between align-items-center">
        <div class="small text-muted">
          {{ t('adminDocutilDocAgents.totalCount', { total }) }}
        </div>
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: page <= 1 }">
              <button type="button" class="page-link" @click="onChangePage(page - 1)">
                {{ t('adminDocutilDocAgents.prevPage') }}
              </button>
            </li>
            <li class="page-item disabled">
              <span class="page-link">
                {{ t('adminDocutilDocAgents.page') }} {{ page }} / {{ totalPages }}
              </span>
            </li>
            <li class="page-item" :class="{ disabled: page >= totalPages }">
              <button type="button" class="page-link" @click="onChangePage(page + 1)">
                {{ t('adminDocutilDocAgents.nextPage') }}
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 상세 모달 -->
    <div
      v-if="detailModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilDocAgents.detailTitle') }}</h5>
            <button type="button" class="btn-close" @click="detailModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="!detailModal.agent" class="text-center py-3 text-muted">
              <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilDocAgents.loading') }}
            </div>
            <div v-else>
              <dl class="row mb-0">
                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldName') }}</dt>
                <dd class="col-sm-8">{{ detailModal.agent.name }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldDescription') }}</dt>
                <dd class="col-sm-8">{{ detailModal.agent.description ?? '—' }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldAgentType') }}</dt>
                <dd class="col-sm-8"><code>{{ detailModal.agent.agentType }}</code></dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldSystemPrompt') }}</dt>
                <dd class="col-sm-8">
                  <pre class="bg-light p-2 small mb-0 rounded">{{ detailModal.agent.systemPrompt }}</pre>
                </dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldLlmProvider') }}</dt>
                <dd class="col-sm-8">{{ detailModal.agent.llmProvider ?? '—' }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldLlmModel') }}</dt>
                <dd class="col-sm-8"><code>{{ detailModal.agent.llmModel }}</code></dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldTemperature') }}</dt>
                <dd class="col-sm-8">{{ detailModal.agent.temperature }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldMaxTokens') }}</dt>
                <dd class="col-sm-8">{{ detailModal.agent.maxTokens }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.fieldIsActive') }}</dt>
                <dd class="col-sm-8">
                  <span v-if="detailModal.agent.isActive" class="badge bg-success">
                    {{ t('adminDocutilDocAgents.active') }}
                  </span>
                  <span v-else class="badge bg-secondary">
                    {{ t('adminDocutilDocAgents.inactive') }}
                  </span>
                </dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.metaId') }}</dt>
                <dd class="col-sm-8 small"><code>{{ detailModal.agent.id }}</code></dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.metaOrganizationId') }}</dt>
                <dd class="col-sm-8 small"><code>{{ detailModal.agent.organizationId }}</code></dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.metaCreatedBy') }}</dt>
                <dd class="col-sm-8 small">{{ detailModal.agent.createdBy }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.metaCreatedAt') }}</dt>
                <dd class="col-sm-8 small">{{ formatDate(detailModal.agent.createdAt) }}</dd>

                <dt class="col-sm-4">{{ t('adminDocutilDocAgents.metaUpdatedAt') }}</dt>
                <dd class="col-sm-8 small">{{ formatDate(detailModal.agent.updatedAt) }}</dd>
              </dl>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="detailModal.open = false">
              {{ t('adminDocutilDocAgents.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="detailModal.open" class="modal-backdrop fade show"></div>

    <!-- 생성/수정 모달 -->
    <div
      v-if="editModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editModal.mode === 'create'
                ? t('adminDocutilDocAgents.createTitle')
                : t('adminDocutilDocAgents.editTitle') }}
            </h5>
            <button type="button" class="btn-close" @click="editModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocAgents.fieldName') }} *</label>
              <input v-model="editForm.name" type="text" class="form-control" maxlength="255" />
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocAgents.fieldDescription') }}</label>
              <textarea v-model="editForm.description" class="form-control" rows="2" maxlength="2000"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocAgents.fieldAgentType') }} *</label>
              <input v-model="editForm.agentType" type="text" class="form-control" maxlength="20" />
              <div class="form-text small">{{ t('adminDocutilDocAgents.fieldAgentTypeHelp') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocAgents.fieldSystemPrompt') }} *</label>
              <textarea
                v-model="editForm.systemPrompt"
                class="form-control"
                rows="5"
              ></textarea>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">{{ t('adminDocutilDocAgents.fieldLlmProvider') }}</label>
                <input v-model="editForm.llmProvider" type="text" class="form-control" maxlength="50" />
                <div class="form-text small">{{ t('adminDocutilDocAgents.fieldLlmProviderHelp') }}</div>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">{{ t('adminDocutilDocAgents.fieldLlmModel') }}</label>
                <input v-model="editForm.llmModel" type="text" class="form-control" maxlength="255" />
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">{{ t('adminDocutilDocAgents.fieldTemperature') }}</label>
                <input
                  v-model.number="editForm.temperature"
                  type="number"
                  class="form-control"
                  min="0"
                  max="2"
                  step="0.1"
                />
                <div class="form-text small">{{ t('adminDocutilDocAgents.fieldTemperatureHelp') }}</div>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">{{ t('adminDocutilDocAgents.fieldMaxTokens') }}</label>
                <input
                  v-model.number="editForm.maxTokens"
                  type="number"
                  class="form-control"
                  min="1"
                  max="128000"
                  step="1"
                />
                <div class="form-text small">{{ t('adminDocutilDocAgents.fieldMaxTokensHelp') }}</div>
              </div>
            </div>
            <div v-if="editModal.mode === 'edit'" class="mb-2 form-check">
              <input
                v-model="editForm.isActive"
                type="checkbox"
                class="form-check-input"
                id="docAgentIsActive"
              />
              <label class="form-check-label" for="docAgentIsActive">
                {{ t('adminDocutilDocAgents.fieldIsActive') }}
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="editModal.open = false">
              {{ t('adminDocutilDocAgents.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="saving"
              @click="onSave"
            >
              <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
              {{ saving
                ? (editModal.mode === 'create'
                    ? t('adminDocutilDocAgents.creating')
                    : t('adminDocutilDocAgents.saving'))
                : (editModal.mode === 'create'
                    ? t('adminDocutilDocAgents.create')
                    : t('adminDocutilDocAgents.save')) }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="editModal.open" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import * as docutilService from '@/services/docutilService'
import type { DocUtilDocAgent, DocUtilDocAgentDetail } from '@/services/docutilService'

const { t } = useI18n()

// 목록 상태
const loading = ref(false)
const agents = ref<DocUtilDocAgent[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)

// 필터(입력 vs 적용 분리)
const agentTypeInput = ref('')
const appliedAgentType = ref('')

const successMessage = ref('')
const errorMessage = ref('')

// 상세 모달
const detailModal = reactive<{ open: boolean; agent: DocUtilDocAgentDetail | null }>({
  open: false,
  agent: null
})

// 생성/수정 모달
const editModal = reactive<{ open: boolean; mode: 'create' | 'edit'; targetId: string | null }>({
  open: false,
  mode: 'create',
  targetId: null
})
const editForm = reactive<{
  name: string
  description: string
  agentType: string
  systemPrompt: string
  llmProvider: string
  llmModel: string
  temperature: number
  maxTokens: number
  isActive: boolean
}>({
  name: '',
  description: '',
  agentType: '',
  systemPrompt: '',
  llmProvider: '',
  llmModel: 'gpt-4o',
  temperature: 0.1,
  maxTokens: 4096,
  isActive: true
})
const saving = ref(false)

const totalPages = computed(() => {
  if (total.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / size.value))
})

async function loadAgents() {
  loading.value = true
  errorMessage.value = ''
  try {
    const list = await docutilService.listDocAgents(page.value, size.value, {
      agentType: appliedAgentType.value || undefined
    })
    agents.value = list.items
    total.value = list.total
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocAgents.errorBoundary'))
    agents.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAgents()
})

function onApplyFilters() {
  appliedAgentType.value = agentTypeInput.value.trim()
  page.value = 1
  loadAgents()
}

function onClearFilters() {
  agentTypeInput.value = ''
  appliedAgentType.value = ''
  page.value = 1
  loadAgents()
}

function onPageSizeChange() {
  page.value = 1
  loadAgents()
}

function onChangePage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  loadAgents()
}

async function openDetail(agent: DocUtilDocAgent) {
  detailModal.agent = null
  detailModal.open = true
  try {
    detailModal.agent = await docutilService.getDocAgent(agent.id)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocAgents.errorBoundary'))
    detailModal.open = false
  }
}

function openCreateDialog() {
  editModal.mode = 'create'
  editModal.targetId = null
  editForm.name = ''
  editForm.description = ''
  editForm.agentType = 'chatbot'
  editForm.systemPrompt = ''
  editForm.llmProvider = ''
  editForm.llmModel = 'gpt-4o'
  editForm.temperature = 0.1
  editForm.maxTokens = 4096
  editForm.isActive = true
  editModal.open = true
}

function openEditDialog(agent: DocUtilDocAgent) {
  editModal.mode = 'edit'
  editModal.targetId = agent.id
  editForm.name = agent.name
  editForm.description = agent.description ?? ''
  editForm.agentType = agent.agentType
  editForm.systemPrompt = agent.systemPrompt
  editForm.llmProvider = agent.llmProvider ?? ''
  editForm.llmModel = agent.llmModel
  editForm.temperature = agent.temperature
  editForm.maxTokens = agent.maxTokens
  editForm.isActive = agent.isActive
  editModal.open = true
}

function validateForm(): string | null {
  if (!editForm.name.trim()) return t('adminDocutilDocAgents.validationNameRequired')
  if (editForm.name.length > 255) return t('adminDocutilDocAgents.validationNameLength')
  if (editForm.description && editForm.description.length > 2000)
    return t('adminDocutilDocAgents.validationDescriptionLength')
  if (!editForm.agentType.trim()) return t('adminDocutilDocAgents.validationAgentTypeRequired')
  if (editForm.agentType.length > 20) return t('adminDocutilDocAgents.validationAgentTypeLength')
  if (!editForm.systemPrompt.trim()) return t('adminDocutilDocAgents.validationSystemPromptRequired')
  if (editForm.llmProvider && editForm.llmProvider.length > 50)
    return t('adminDocutilDocAgents.validationLlmProviderLength')
  if (editForm.llmModel && editForm.llmModel.length > 255)
    return t('adminDocutilDocAgents.validationLlmModelLength')
  if (editForm.temperature < 0 || editForm.temperature > 2)
    return t('adminDocutilDocAgents.validationTemperatureRange')
  if (editForm.maxTokens < 1 || editForm.maxTokens > 128000)
    return t('adminDocutilDocAgents.validationMaxTokensRange')
  return null
}

async function onSave() {
  const err = validateForm()
  if (err) {
    errorMessage.value = err
    return
  }

  saving.value = true
  errorMessage.value = ''
  try {
    if (editModal.mode === 'create') {
      await docutilService.createDocAgent({
        name: editForm.name.trim(),
        description: editForm.description.trim() || null,
        agentType: editForm.agentType.trim(),
        systemPrompt: editForm.systemPrompt.trim(),
        llmProvider: editForm.llmProvider.trim() || null,
        llmModel: editForm.llmModel.trim() || 'gpt-4o',
        temperature: editForm.temperature,
        maxTokens: editForm.maxTokens
      })
      successMessage.value = t('adminDocutilDocAgents.createSuccess')
    } else if (editModal.targetId) {
      await docutilService.updateDocAgent(editModal.targetId, {
        name: editForm.name.trim(),
        description: editForm.description.trim() || null,
        agentType: editForm.agentType.trim(),
        systemPrompt: editForm.systemPrompt.trim(),
        llmProvider: editForm.llmProvider.trim() || null,
        llmModel: editForm.llmModel.trim() || null,
        temperature: editForm.temperature,
        maxTokens: editForm.maxTokens,
        isActive: editForm.isActive
      })
      successMessage.value = t('adminDocutilDocAgents.updateSuccess')
    }
    editModal.open = false
    await loadAgents()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocAgents.errorUnknown'))
  } finally {
    saving.value = false
  }
}

async function onDelete(agent: DocUtilDocAgent) {
  if (!window.confirm(t('adminDocutilDocAgents.confirmDelete', { name: agent.name }))) return
  errorMessage.value = ''
  try {
    await docutilService.deleteDocAgent(agent.id)
    successMessage.value = t('adminDocutilDocAgents.deleteSuccess')
    await loadAgents()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocAgents.errorUnknown'))
  }
}

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
.admin-docutil-doc-agents .modal {
  background-color: rgba(0, 0, 0, 0.4);
}
.admin-docutil-doc-agents pre {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
}
</style>
