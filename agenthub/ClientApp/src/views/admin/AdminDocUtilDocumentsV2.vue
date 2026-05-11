<template>
  <div class="admin-docutil-documents-v2 container-fluid py-4">
    <header class="mb-3 d-flex align-items-start justify-content-between flex-wrap gap-2">
      <div>
        <h1 class="h3 mb-1">{{ t('adminDocutilDocumentsV2.title') }}</h1>
        <p class="text-muted mb-0">{{ t('adminDocutilDocumentsV2.subtitle') }}</p>
      </div>
      <div class="d-flex gap-2 flex-wrap">
        <button type="button" class="btn btn-outline-secondary" @click="loadDocuments" :disabled="loading">
          <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilDocumentsV2.refresh') }}
        </button>
        <button type="button" class="btn btn-primary" @click="openGenerateDialog">
          <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilDocumentsV2.newDocument') }}
        </button>
        <button type="button" class="btn btn-outline-info" @click="openExportStatusDialog">
          <i class="bi bi-cloud-download me-1"></i>{{ t('adminDocutilDocumentsV2.exportStatus') }}
        </button>
      </div>
    </header>

    <div class="alert alert-info mb-3" role="alert">
      <i class="bi bi-info-circle me-2"></i>{{ t('adminDocutilDocumentsV2.warningSeparateDomain') }}
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
          <div class="col-md-3">
            <label class="form-label small">{{ t('adminDocutilDocumentsV2.filterDocumentType') }}</label>
            <input
              v-model="docTypeInput"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilDocumentsV2.filterDocumentTypePlaceholder')"
              @keyup.enter="onApplyFilters"
            />
          </div>
          <div class="col-md-3">
            <label class="form-label small">{{ t('adminDocutilDocumentsV2.filterMode') }}</label>
            <input
              v-model="modeInput"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilDocumentsV2.filterModePlaceholder')"
              @keyup.enter="onApplyFilters"
            />
          </div>
          <div class="col-md-2">
            <label class="form-label small">{{ t('adminDocutilDocumentsV2.pageSize') }}</label>
            <select v-model.number="limit" class="form-select" @change="onLimitChange">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <div class="col-md-2">
            <label class="form-label small">{{ t('adminDocutilDocumentsV2.offset') }}</label>
            <input v-model.number="offset" type="number" class="form-control" min="0" step="1" />
          </div>
          <div class="col-md-2 d-flex gap-2">
            <button type="button" class="btn btn-secondary flex-fill" @click="onClearFilters">
              {{ t('adminDocutilDocumentsV2.clearFilters') }}
            </button>
            <button type="button" class="btn btn-primary flex-fill" @click="onApplyFilters">
              {{ t('adminDocutilDocumentsV2.applyFilters') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 표 -->
    <div class="card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilDocumentsV2.loading') }}
        </div>
        <table v-else-if="documents.length > 0" class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>{{ t('adminDocutilDocumentsV2.colTitle') }}</th>
              <th>{{ t('adminDocutilDocumentsV2.colDocumentType') }}</th>
              <th>{{ t('adminDocutilDocumentsV2.colMode') }}</th>
              <th>{{ t('adminDocutilDocumentsV2.colStatus') }}</th>
              <th>{{ t('adminDocutilDocumentsV2.colLlmModel') }}</th>
              <th>{{ t('adminDocutilDocumentsV2.colCreatedAt') }}</th>
              <th class="text-end">{{ t('adminDocutilDocumentsV2.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in documents" :key="doc.id">
              <td>
                <strong>{{ doc.title || '—' }}</strong>
                <div class="small text-muted text-truncate" style="max-width: 320px;">
                  <code>{{ doc.id }}</code>
                </div>
              </td>
              <td><code class="small">{{ doc.documentType }}</code></td>
              <td><code class="small">{{ doc.mode }}</code></td>
              <td>
                <span :class="statusBadgeClass(doc.status)">{{ doc.status }}</span>
              </td>
              <td class="small"><code>{{ doc.llmModel ?? '—' }}</code></td>
              <td class="small">{{ formatDate(doc.createdAt) }}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-info me-1"
                  @click="openDetail(doc)"
                >
                  {{ t('adminDocutilDocumentsV2.viewDetail') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-primary me-1"
                  @click="openPatchDialog(doc)"
                >
                  {{ t('adminDocutilDocumentsV2.patch') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-success"
                  @click="openExportDialog(doc)"
                >
                  {{ t('adminDocutilDocumentsV2.export') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">{{ t('adminDocutilDocumentsV2.emptyList') }}</div>
      </div>
      <div v-if="documents.length > 0" class="card-footer d-flex justify-content-between align-items-center">
        <div class="small text-muted">
          {{ t('adminDocutilDocumentsV2.totalCount', { total }) }}
        </div>
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: offset <= 0 }">
              <button type="button" class="page-link" @click="onPrevPage">
                {{ t('adminDocutilDocumentsV2.prevPage') }}
              </button>
            </li>
            <li class="page-item disabled">
              <span class="page-link">
                {{ t('adminDocutilDocumentsV2.page') }} {{ currentPage }} / {{ totalPages }}
              </span>
            </li>
            <li class="page-item" :class="{ disabled: offset + limit >= total }">
              <button type="button" class="page-link" @click="onNextPage">
                {{ t('adminDocutilDocumentsV2.nextPage') }}
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
      <div class="modal-dialog modal-xl" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilDocumentsV2.detailTitle') }}</h5>
            <button type="button" class="btn-close" @click="detailModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="!detailModal.document" class="text-center py-3 text-muted">
              <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilDocumentsV2.loading') }}
            </div>
            <div v-else>
              <ul class="nav nav-tabs mb-3">
                <li class="nav-item">
                  <a
                    href="#"
                    class="nav-link"
                    :class="{ active: detailTab === 'info' }"
                    @click.prevent="detailTab = 'info'"
                  >{{ t('adminDocutilDocumentsV2.tabInfo') }}</a>
                </li>
                <li class="nav-item">
                  <a
                    href="#"
                    class="nav-link"
                    :class="{ active: detailTab === 'schema' }"
                    @click.prevent="detailTab = 'schema'"
                  >{{ t('adminDocutilDocumentsV2.tabSchema') }}</a>
                </li>
              </ul>

              <div v-if="detailTab === 'info'">
                <dl class="row mb-0">
                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.colTitle') }}</dt>
                  <dd class="col-sm-8">{{ detailModal.document.title || '—' }}</dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.colDocumentType') }}</dt>
                  <dd class="col-sm-8"><code>{{ detailModal.document.documentType }}</code></dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.colMode') }}</dt>
                  <dd class="col-sm-8"><code>{{ detailModal.document.mode }}</code></dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.colStatus') }}</dt>
                  <dd class="col-sm-8">
                    <span :class="statusBadgeClass(detailModal.document.status)">
                      {{ detailModal.document.status }}
                    </span>
                  </dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaError') }}</dt>
                  <dd class="col-sm-8 text-danger small">{{ detailModal.document.errorMessage ?? '—' }}</dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.colLlmModel') }}</dt>
                  <dd class="col-sm-8">
                    <code v-if="detailModal.document.llmProvider">{{ detailModal.document.llmProvider }}/</code>
                    <code>{{ detailModal.document.llmModel ?? '—' }}</code>
                  </dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaTokens') }}</dt>
                  <dd class="col-sm-8 small">
                    {{ detailModal.document.promptTokens ?? '—' }} / {{ detailModal.document.completionTokens ?? '—' }}
                  </dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaId') }}</dt>
                  <dd class="col-sm-8 small"><code>{{ detailModal.document.id }}</code></dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaOrganizationId') }}</dt>
                  <dd class="col-sm-8 small"><code>{{ detailModal.document.organizationId }}</code></dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaAgentId') }}</dt>
                  <dd class="col-sm-8 small">
                    <code v-if="detailModal.document.agentId">{{ detailModal.document.agentId }}</code>
                    <span v-else>—</span>
                  </dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaTemplateId') }}</dt>
                  <dd class="col-sm-8 small">
                    <code v-if="detailModal.document.templateId">{{ detailModal.document.templateId }}</code>
                    <span v-else>—</span>
                  </dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaGeneratedBy') }}</dt>
                  <dd class="col-sm-8 small">{{ detailModal.document.generatedByUserId ?? '—' }}</dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaCreatedAt') }}</dt>
                  <dd class="col-sm-8 small">{{ formatDate(detailModal.document.createdAt) }}</dd>

                  <dt class="col-sm-4">{{ t('adminDocutilDocumentsV2.metaCompletedAt') }}</dt>
                  <dd class="col-sm-8 small">
                    {{ detailModal.document.completedAt ? formatDate(detailModal.document.completedAt) : '—' }}
                  </dd>
                </dl>
              </div>

              <div v-else-if="detailTab === 'schema'">
                <pre class="bg-light p-2 small mb-0 rounded">{{ formatJson(detailModal.document.documentSchema) }}</pre>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="detailModal.open = false">
              {{ t('adminDocutilDocumentsV2.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="detailModal.open" class="modal-backdrop fade show"></div>

    <!-- 신규 생성 모달 -->
    <div
      v-if="generateModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilDocumentsV2.createTitle') }}</h5>
            <button type="button" class="btn-close" @click="generateModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-secondary small">{{ t('adminDocutilDocumentsV2.createHint') }}</div>

            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldPrompt') }}</label>
              <textarea
                v-model="generateForm.prompt"
                class="form-control"
                rows="4"
                maxlength="8000"
              ></textarea>
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldPromptHelp') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldDocumentType') }}</label>
              <select v-model="generateForm.documentType" class="form-select">
                <option value="slide_report">slide_report</option>
                <option value="docx_report">docx_report</option>
                <option value="proposal">proposal</option>
                <option value="minutes">minutes</option>
                <option value="one_pager">one_pager</option>
                <option value="weekly_status">weekly_status</option>
                <option value="freeform_doc">freeform_doc</option>
              </select>
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldDocumentTypeHelp') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldMode') }}</label>
              <select v-model="generateForm.mode" class="form-select" disabled>
                <option value="free_generation">free_generation</option>
              </select>
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldModeHelp') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldSourceDocumentIds') }}</label>
              <textarea
                v-model="generateForm.sourceDocumentIdsRaw"
                class="form-control"
                rows="2"
                :placeholder="t('adminDocutilDocumentsV2.fieldSourceDocumentIdsPlaceholder')"
              ></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldAgentId') }}</label>
              <input v-model="generateForm.agentId" type="text" class="form-control" />
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldAgentIdHelp') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldDesignTokens') }}</label>
              <textarea
                v-model="generateForm.designTokensRaw"
                class="form-control font-monospace small"
                rows="3"
              ></textarea>
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldDesignTokensHelp') }}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="generateModal.open = false">
              {{ t('adminDocutilDocumentsV2.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="generating"
              @click="onGenerate"
            >
              <span v-if="generating" class="spinner-border spinner-border-sm me-2"></span>
              {{ generating
                ? t('adminDocutilDocumentsV2.creating')
                : t('adminDocutilDocumentsV2.create') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="generateModal.open" class="modal-backdrop fade show"></div>

    <!-- 부분 패치 모달 -->
    <div
      v-if="patchModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ t('adminDocutilDocumentsV2.patchTitle') }}
              <small v-if="patchModal.targetId" class="text-muted ms-2">
                <code>{{ patchModal.targetId }}</code>
              </small>
            </h5>
            <button type="button" class="btn-close" @click="patchModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-secondary small">{{ t('adminDocutilDocumentsV2.patchHint') }}</div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldPatchType') }}</label>
              <select v-model="patchForm.patchType" class="form-select">
                <option value="page">page</option>
                <option value="component">component</option>
                <option value="tokens">tokens</option>
              </select>
            </div>
            <div v-if="patchForm.patchType !== 'tokens'" class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldPageId') }}</label>
              <input
                v-model="patchForm.pageId"
                type="text"
                class="form-control"
                pattern="^p\d+$"
                placeholder="p1"
              />
            </div>
            <div v-if="patchForm.patchType === 'component'" class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldComponentId') }}</label>
              <input
                v-model="patchForm.componentId"
                type="text"
                class="form-control"
                pattern="^c\d+$"
                placeholder="c1"
              />
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldPatchData') }}</label>
              <textarea
                v-model="patchForm.dataRaw"
                class="form-control font-monospace small"
                rows="6"
              ></textarea>
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldPatchDataHelp') }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldExpectedVersion') }}</label>
              <input
                v-model.number="patchForm.expectedVersion"
                type="number"
                class="form-control"
                min="1"
              />
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldExpectedVersionHelp') }}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="patchModal.open = false">
              {{ t('adminDocutilDocumentsV2.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="patching"
              @click="onPatch"
            >
              <span v-if="patching" class="spinner-border spinner-border-sm me-2"></span>
              {{ patching
                ? t('adminDocutilDocumentsV2.submitting')
                : t('adminDocutilDocumentsV2.submit') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="patchModal.open" class="modal-backdrop fade show"></div>

    <!-- Export 요청 모달 -->
    <div
      v-if="exportModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ t('adminDocutilDocumentsV2.exportTitle') }}
              <small v-if="exportModal.targetId" class="text-muted ms-2">
                <code>{{ exportModal.targetId }}</code>
              </small>
            </h5>
            <button type="button" class="btn-close" @click="exportModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-secondary small">{{ t('adminDocutilDocumentsV2.exportHint') }}</div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldExportFormat') }}</label>
              <select v-model="exportForm.format" class="form-select">
                <option value="pptx">pptx</option>
                <option value="docx">docx</option>
                <option value="hwpx">hwpx</option>
                <option value="pdf">pdf</option>
                <option value="html">html</option>
              </select>
              <div class="form-text small">{{ t('adminDocutilDocumentsV2.fieldExportFormatHelp') }}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="exportModal.open = false">
              {{ t('adminDocutilDocumentsV2.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="exporting"
              @click="onExport"
            >
              <span v-if="exporting" class="spinner-border spinner-border-sm me-2"></span>
              {{ exporting
                ? t('adminDocutilDocumentsV2.requesting')
                : t('adminDocutilDocumentsV2.request') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="exportModal.open" class="modal-backdrop fade show"></div>

    <!-- Export 상태/다운로드 모달 -->
    <div
      v-if="statusModal.open"
      class="modal fade show d-block"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
    >
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilDocumentsV2.exportStatusTitle') }}</h5>
            <button type="button" class="btn-close" @click="statusModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-secondary small">{{ t('adminDocutilDocumentsV2.exportStatusHint') }}</div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilDocumentsV2.fieldJobId') }}</label>
              <input
                v-model="statusForm.jobId"
                type="text"
                class="form-control"
                :placeholder="t('adminDocutilDocumentsV2.fieldJobIdPlaceholder')"
              />
            </div>

            <div v-if="statusForm.lastStatus" class="card mt-2">
              <div class="card-body">
                <div class="mb-2">
                  <span :class="statusBadgeClass(statusForm.lastStatus.status)">
                    {{ statusLabel(statusForm.lastStatus.status) }}
                  </span>
                  <span class="ms-2 small text-muted">
                    {{ t('adminDocutilDocumentsV2.statusProgress', { progress: statusForm.lastStatus.progress }) }}
                  </span>
                </div>
                <div v-if="statusForm.lastStatus.error" class="text-danger small">
                  {{ statusForm.lastStatus.error }}
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="statusModal.open = false">
              {{ t('adminDocutilDocumentsV2.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-outline-primary"
              :disabled="polling"
              @click="onPollStatus"
            >
              <span v-if="polling" class="spinner-border spinner-border-sm me-2"></span>
              {{ polling
                ? t('adminDocutilDocumentsV2.polling')
                : t('adminDocutilDocumentsV2.pollStatus') }}
            </button>
            <button
              type="button"
              class="btn btn-success"
              :disabled="downloading || !canDownload"
              @click="onDownload"
            >
              <span v-if="downloading" class="spinner-border spinner-border-sm me-2"></span>
              {{ downloading
                ? t('adminDocutilDocumentsV2.downloading')
                : t('adminDocutilDocumentsV2.downloadFile') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="statusModal.open" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import * as docutilService from '@/services/docutilService'
import type {
  DocUtilDocumentV2,
  DocUtilDocumentV2Detail,
  DocumentV2Type,
  DocumentV2ExportFormat,
  DocumentV2ExportStatus,
  DocumentV2ExportStatusValue,
  DocumentV2PatchType
} from '@/services/docutilService'

const { t } = useI18n()

// ── 목록 ─────────────────────────────────────────────────────────────────
const loading = ref(false)
const documents = ref<DocUtilDocumentV2[]>([])
const total = ref(0)
const limit = ref(20)
const offset = ref(0)

const docTypeInput = ref('')
const modeInput = ref('')
const appliedDocType = ref('')
const appliedMode = ref('')

const successMessage = ref('')
const errorMessage = ref('')

const totalPages = computed(() => {
  if (total.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / limit.value))
})

const currentPage = computed(() => {
  return Math.floor(offset.value / limit.value) + 1
})

// ── 상세 ─────────────────────────────────────────────────────────────────
const detailModal = reactive<{ open: boolean; document: DocUtilDocumentV2Detail | null }>({
  open: false,
  document: null
})
const detailTab = ref<'info' | 'schema'>('info')

// ── 생성 ─────────────────────────────────────────────────────────────────
const generateModal = reactive<{ open: boolean }>({ open: false })
const generateForm = reactive<{
  prompt: string
  documentType: DocumentV2Type
  mode: 'free_generation' | 'template_fill'
  sourceDocumentIdsRaw: string
  agentId: string
  designTokensRaw: string
}>({
  prompt: '',
  documentType: 'slide_report',
  mode: 'free_generation',
  sourceDocumentIdsRaw: '',
  agentId: '',
  designTokensRaw: ''
})
const generating = ref(false)

// ── 패치 ─────────────────────────────────────────────────────────────────
const patchModal = reactive<{ open: boolean; targetId: string | null }>({
  open: false,
  targetId: null
})
const patchForm = reactive<{
  patchType: DocumentV2PatchType
  pageId: string
  componentId: string
  dataRaw: string
  expectedVersion: number | null
}>({
  patchType: 'component',
  pageId: '',
  componentId: '',
  dataRaw: '{}',
  expectedVersion: null
})
const patching = ref(false)

// ── Export 요청 ──────────────────────────────────────────────────────────
const exportModal = reactive<{ open: boolean; targetId: string | null }>({
  open: false,
  targetId: null
})
const exportForm = reactive<{ format: DocumentV2ExportFormat }>({ format: 'pptx' })
const exporting = ref(false)

// ── Export 상태/다운로드 ─────────────────────────────────────────────────
const statusModal = reactive<{ open: boolean }>({ open: false })
const statusForm = reactive<{ jobId: string; lastStatus: DocumentV2ExportStatus | null }>({
  jobId: '',
  lastStatus: null
})
const polling = ref(false)
const downloading = ref(false)
const canDownload = computed(() => statusForm.lastStatus?.status === 'completed')

// ── 로드 ─────────────────────────────────────────────────────────────────
async function loadDocuments() {
  loading.value = true
  errorMessage.value = ''
  try {
    const list = await docutilService.listDocumentsV2(limit.value, offset.value, {
      documentType: appliedDocType.value || undefined,
      mode: appliedMode.value || undefined
    })
    documents.value = list.items
    total.value = list.total
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorBoundary'))
    documents.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDocuments()
})

function onApplyFilters() {
  appliedDocType.value = docTypeInput.value.trim()
  appliedMode.value = modeInput.value.trim()
  offset.value = 0
  loadDocuments()
}

function onClearFilters() {
  docTypeInput.value = ''
  modeInput.value = ''
  appliedDocType.value = ''
  appliedMode.value = ''
  offset.value = 0
  loadDocuments()
}

function onLimitChange() {
  offset.value = 0
  loadDocuments()
}

function onPrevPage() {
  const next = Math.max(0, offset.value - limit.value)
  if (next === offset.value) return
  offset.value = next
  loadDocuments()
}

function onNextPage() {
  if (offset.value + limit.value >= total.value) return
  offset.value = offset.value + limit.value
  loadDocuments()
}

// ── 상세 ─────────────────────────────────────────────────────────────────
async function openDetail(doc: DocUtilDocumentV2) {
  detailModal.document = null
  detailTab.value = 'info'
  detailModal.open = true
  try {
    detailModal.document = await docutilService.getDocumentV2(doc.id)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorBoundary'))
    detailModal.open = false
  }
}

// ── 생성 ─────────────────────────────────────────────────────────────────
function openGenerateDialog() {
  generateForm.prompt = ''
  generateForm.documentType = 'slide_report'
  generateForm.mode = 'free_generation'
  generateForm.sourceDocumentIdsRaw = ''
  generateForm.agentId = ''
  generateForm.designTokensRaw = ''
  generateModal.open = true
}

function parseSourceIds(raw: string): string[] | null {
  const tokens = raw
    .split(/[\s,;\n]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
  return tokens.length > 0 ? tokens : null
}

function parseJsonObject(raw: string, fieldErrorKey: string): { ok: true; value: Record<string, unknown> | null } | { ok: false; error: string } {
  const trimmed = raw.trim()
  if (!trimmed) return { ok: true, value: null }
  try {
    const parsed = JSON.parse(trimmed)
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      return { ok: false, error: t(fieldErrorKey) }
    }
    return { ok: true, value: parsed as Record<string, unknown> }
  } catch {
    return { ok: false, error: t(fieldErrorKey) }
  }
}

async function onGenerate() {
  // 검증
  if (!generateForm.prompt.trim()) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationPromptRequired')
    return
  }
  if (generateForm.prompt.length > 8000) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationPromptLength')
    return
  }
  if (generateForm.mode === 'template_fill') {
    errorMessage.value = t('adminDocutilDocumentsV2.validationTemplateFill')
    return
  }
  const ids = parseSourceIds(generateForm.sourceDocumentIdsRaw)
  if (ids && ids.length > 10) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationSourceIdsMax')
    return
  }
  const designTokensParsed = parseJsonObject(
    generateForm.designTokensRaw,
    'adminDocutilDocumentsV2.validationDesignTokensJson'
  )
  if (!designTokensParsed.ok) {
    errorMessage.value = designTokensParsed.error
    return
  }

  generating.value = true
  errorMessage.value = ''
  try {
    const created = await docutilService.generateDocumentV2({
      prompt: generateForm.prompt.trim(),
      documentType: generateForm.documentType,
      mode: 'free_generation',
      sourceDocumentIds: ids,
      agentId: generateForm.agentId.trim() || null,
      designTokens: designTokensParsed.value
    })
    successMessage.value = t('adminDocutilDocumentsV2.createSuccess', { status: created.status })
    generateModal.open = false
    await loadDocuments()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorUnknown'))
  } finally {
    generating.value = false
  }
}

// ── 패치 ─────────────────────────────────────────────────────────────────
function openPatchDialog(doc: DocUtilDocumentV2) {
  patchModal.targetId = doc.id
  patchForm.patchType = 'component'
  patchForm.pageId = ''
  patchForm.componentId = ''
  patchForm.dataRaw = '{}'
  patchForm.expectedVersion = null
  patchModal.open = true
}

async function onPatch() {
  if (!patchModal.targetId) return
  // 검증
  if (!patchForm.patchType) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationPatchTypeRequired')
    return
  }
  if (patchForm.patchType === 'page' && !patchForm.pageId.trim()) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationPageIdRequired')
    return
  }
  if (patchForm.patchType === 'component'
      && (!patchForm.pageId.trim() || !patchForm.componentId.trim())) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationComponentIdRequired')
    return
  }
  if (patchForm.patchType === 'tokens'
      && (patchForm.pageId.trim() || patchForm.componentId.trim())) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationTokensNoIdentifier')
    return
  }
  if (patchForm.pageId && !/^p\d+$/.test(patchForm.pageId.trim())) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationPageIdFormat')
    return
  }
  if (patchForm.componentId && !/^c\d+$/.test(patchForm.componentId.trim())) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationComponentIdFormat')
    return
  }
  if (patchForm.expectedVersion != null && patchForm.expectedVersion < 1) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationExpectedVersion')
    return
  }
  const dataParsed = parseJsonObject(
    patchForm.dataRaw,
    'adminDocutilDocumentsV2.validationPatchDataJson'
  )
  if (!dataParsed.ok) {
    errorMessage.value = dataParsed.error
    return
  }
  if (!dataParsed.value) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationPatchDataJson')
    return
  }

  patching.value = true
  errorMessage.value = ''
  try {
    await docutilService.patchDocumentV2(patchModal.targetId, {
      patchType: patchForm.patchType,
      pageId: patchForm.pageId.trim() || null,
      componentId: patchForm.componentId.trim() || null,
      data: dataParsed.value,
      expectedVersion: patchForm.expectedVersion ?? null
    })
    successMessage.value = t('adminDocutilDocumentsV2.patchSuccess')
    patchModal.open = false
    await loadDocuments()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorUnknown'))
  } finally {
    patching.value = false
  }
}

// ── Export ──────────────────────────────────────────────────────────────
function openExportDialog(doc: DocUtilDocumentV2) {
  exportModal.targetId = doc.id
  exportForm.format = 'pptx'
  exportModal.open = true
}

async function onExport() {
  if (!exportModal.targetId) return
  exporting.value = true
  errorMessage.value = ''
  try {
    const ack = await docutilService.requestDocumentV2Export(exportModal.targetId, {
      format: exportForm.format
    })
    successMessage.value = t('adminDocutilDocumentsV2.exportRequested', { jobId: ack.jobId })
    exportModal.open = false
    // 즉시 상태 모달로 이어서 폴링 가능하도록 jobId 채워줌.
    statusForm.jobId = ack.jobId
    statusForm.lastStatus = null
    statusModal.open = true
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorUnknown'))
  } finally {
    exporting.value = false
  }
}

function openExportStatusDialog() {
  statusForm.jobId = ''
  statusForm.lastStatus = null
  statusModal.open = true
}

async function onPollStatus() {
  if (!statusForm.jobId.trim()) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationJobIdRequired')
    return
  }
  polling.value = true
  errorMessage.value = ''
  try {
    statusForm.lastStatus = await docutilService.getDocumentV2ExportStatus(
      statusForm.jobId.trim()
    )
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorUnknown'))
    statusForm.lastStatus = null
  } finally {
    polling.value = false
  }
}

async function onDownload() {
  if (!statusForm.jobId.trim()) {
    errorMessage.value = t('adminDocutilDocumentsV2.validationJobIdRequired')
    return
  }
  if (!canDownload.value) return

  downloading.value = true
  errorMessage.value = ''
  try {
    const download = await docutilService.downloadDocumentV2Export(statusForm.jobId.trim())
    // 브라우저에 파일 저장 유도.
    const url = URL.createObjectURL(download.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = download.fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    successMessage.value = t('adminDocutilDocumentsV2.downloadSuccess')
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilDocumentsV2.errorUnknown'))
  } finally {
    downloading.value = false
  }
}

// ── 유틸 ─────────────────────────────────────────────────────────────────
function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function formatJson(obj: unknown): string {
  if (obj == null) return '—'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function statusBadgeClass(status: string): string {
  if (status === 'completed') return 'badge bg-success'
  if (status === 'failed') return 'badge bg-danger'
  if (status === 'running') return 'badge bg-info'
  if (status === 'pending') return 'badge bg-secondary'
  return 'badge bg-light text-dark'
}

function statusLabel(status: DocumentV2ExportStatusValue): string {
  switch (status) {
    case 'pending':
      return t('adminDocutilDocumentsV2.statusPending')
    case 'running':
      return t('adminDocutilDocumentsV2.statusRunning')
    case 'completed':
      return t('adminDocutilDocumentsV2.statusCompleted')
    case 'failed':
      return t('adminDocutilDocumentsV2.statusFailed')
    default:
      return status
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
.admin-docutil-documents-v2 .modal {
  background-color: rgba(0, 0, 0, 0.4);
}
.admin-docutil-documents-v2 pre {
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 480px;
  overflow-y: auto;
}
</style>
