<template>
  <div class="admin-docutil-faq container-fluid py-4">
    <header class="mb-3 d-flex align-items-start justify-content-between flex-wrap gap-2">
      <div>
        <h1 class="h3 mb-1">{{ t('adminDocutilFaq.title') }}</h1>
        <p class="text-muted mb-0">{{ t('adminDocutilFaq.subtitle') }}</p>
      </div>
      <div class="d-flex gap-2">
        <button type="button" class="btn btn-outline-secondary" @click="loadFaqs(true)" :disabled="loading">
          <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilFaq.refresh') }}
        </button>
        <button type="button" class="btn btn-primary" @click="openCreateDialog">
          <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilFaq.newFaq') }}
        </button>
      </div>
    </header>

    <!-- 알림 -->
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
          <div class="col-md-5">
            <label class="form-label small">{{ t('adminDocutilFaq.search') }}</label>
            <input
              v-model="searchInput"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilFaq.searchPlaceholder')"
              @keyup.enter="onApplyFilters"
            />
          </div>
          <div class="col-md-3">
            <label class="form-label small">{{ t('adminDocutilFaq.filterCategory') }}</label>
            <input
              v-model="categoryInput"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilFaq.filterCategoryAll')"
              @keyup.enter="onApplyFilters"
            />
          </div>
          <div class="col-md-2">
            <label class="form-label small">{{ t('adminDocutilFaq.pageSize') }}</label>
            <select v-model.number="size" class="form-select" @change="onPageSizeChange">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <div class="col-md-2 d-flex gap-2">
            <button type="button" class="btn btn-secondary flex-fill" @click="onClearFilters">
              {{ t('adminDocutilFaq.clearFilters') }}
            </button>
            <button type="button" class="btn btn-primary flex-fill" @click="onApplyFilters">
              {{ t('adminDocutilFaq.applyFilters') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 표 -->
    <div class="card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilFaq.loading') }}
        </div>
        <table v-else-if="faqs.length > 0" class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>{{ t('adminDocutilFaq.colQuestion') }}</th>
              <th class="d-none d-md-table-cell">{{ t('adminDocutilFaq.colCategory') }}</th>
              <th class="d-none d-md-table-cell text-center">{{ t('adminDocutilFaq.colDisplayOrder') }}</th>
              <th class="d-none d-md-table-cell text-center">{{ t('adminDocutilFaq.colIsActive') }}</th>
              <th class="d-none d-lg-table-cell">{{ t('adminDocutilFaq.colUpdatedAt') }}</th>
              <th class="text-end">{{ t('adminDocutilFaq.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="faq in faqs" :key="faq.id">
              <td class="text-truncate" style="max-width: 480px">{{ faq.question }}</td>
              <td class="d-none d-md-table-cell">
                <span v-if="faq.category" class="badge bg-light text-dark">{{ faq.category }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="d-none d-md-table-cell text-center">{{ faq.displayOrder }}</td>
              <td class="d-none d-md-table-cell text-center">
                <span
                  class="badge"
                  :class="faq.isActive ? 'bg-success' : 'bg-secondary'"
                >
                  {{ faq.isActive ? t('adminDocutilFaq.active') : t('adminDocutilFaq.inactive') }}
                </span>
              </td>
              <td class="d-none d-lg-table-cell text-muted small">{{ formatDate(faq.updatedAt) }}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary me-1"
                  @click="openDetail(faq)"
                  :title="t('adminDocutilFaq.viewDetail')"
                >
                  <i class="bi bi-eye"></i>
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-primary me-1"
                  @click="openEditDialog(faq)"
                  :title="t('adminDocutilFaq.edit')"
                >
                  <i class="bi bi-pencil"></i>
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger"
                  @click="onDelete(faq)"
                  :title="t('adminDocutilFaq.delete')"
                >
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">
          {{ t('adminDocutilFaq.emptyList') }}
        </div>
      </div>
    </div>

    <!-- 페이지네이션 -->
    <div class="d-flex justify-content-between align-items-center mt-3">
      <small class="text-muted">{{ t('adminDocutilFaq.totalCount', { total }) }}</small>
      <div class="d-flex align-items-center gap-2">
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary"
          :disabled="page <= 1 || loading"
          @click="onChangePage(page - 1)"
        >
          <i class="bi bi-chevron-left"></i>{{ t('adminDocutilFaq.prevPage') }}
        </button>
        <span class="small text-muted">{{ t('adminDocutilFaq.page') }} {{ page }} / {{ totalPages }}</span>
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary"
          :disabled="page >= totalPages || loading"
          @click="onChangePage(page + 1)"
        >
          {{ t('adminDocutilFaq.nextPage') }}<i class="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- 상세 모달 -->
    <div v-if="detailModal.open" class="modal fade show d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilFaq.detailTitle') }}</h5>
            <button type="button" class="btn-close" @click="detailModal.open = false"></button>
          </div>
          <div class="modal-body" v-if="detailModal.faq">
            <dl class="row">
              <dt class="col-sm-3">{{ t('adminDocutilFaq.fieldQuestion') }}</dt>
              <dd class="col-sm-9">{{ detailModal.faq.question }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.fieldAnswer') }}</dt>
              <dd class="col-sm-9" style="white-space: pre-wrap">{{ detailModal.faq.answer }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.fieldCategory') }}</dt>
              <dd class="col-sm-9">{{ detailModal.faq.category || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.fieldDisplayOrder') }}</dt>
              <dd class="col-sm-9">{{ detailModal.faq.displayOrder }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.fieldIsActive') }}</dt>
              <dd class="col-sm-9">
                {{ detailModal.faq.isActive ? t('adminDocutilFaq.active') : t('adminDocutilFaq.inactive') }}
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.metaSearchScopeId') }}</dt>
              <dd class="col-sm-9 text-muted small">{{ detailModal.faq.searchScopeId || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.metaOrganizationId') }}</dt>
              <dd class="col-sm-9 text-muted small">{{ detailModal.faq.organizationId }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.metaCreatedAt') }}</dt>
              <dd class="col-sm-9 text-muted small">{{ formatDate(detailModal.faq.createdAt) }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilFaq.metaUpdatedAt') }}</dt>
              <dd class="col-sm-9 text-muted small">{{ formatDate(detailModal.faq.updatedAt) }}</dd>
            </dl>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="detailModal.open = false">
              {{ t('adminDocutilFaq.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="detailModal.open" class="modal-backdrop fade show"></div>

    <!-- 생성/수정 모달 -->
    <div v-if="editModal.open" class="modal fade show d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ editModal.mode === 'create' ? t('adminDocutilFaq.createTitle') : t('adminDocutilFaq.editTitle') }}
            </h5>
            <button type="button" class="btn-close" @click="editModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">
                {{ t('adminDocutilFaq.fieldQuestion') }} <span class="text-danger">*</span>
              </label>
              <textarea
                v-model="editForm.question"
                class="form-control"
                rows="2"
                :placeholder="t('adminDocutilFaq.questionPlaceholder')"
              ></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">
                {{ t('adminDocutilFaq.fieldAnswer') }} <span class="text-danger">*</span>
              </label>
              <textarea
                v-model="editForm.answer"
                class="form-control"
                rows="8"
                :placeholder="t('adminDocutilFaq.answerPlaceholder')"
              ></textarea>
            </div>
            <div class="row g-2">
              <div class="col-md-4">
                <label class="form-label">{{ t('adminDocutilFaq.fieldCategory') }}</label>
                <input
                  v-model="editForm.category"
                  type="text"
                  class="form-control"
                  :placeholder="t('adminDocutilFaq.categoryPlaceholder')"
                />
              </div>
              <div class="col-md-4">
                <label class="form-label">{{ t('adminDocutilFaq.fieldDisplayOrder') }}</label>
                <input
                  v-model.number="editForm.displayOrder"
                  type="number"
                  class="form-control"
                  min="0"
                />
              </div>
              <div class="col-md-4">
                <label class="form-label">{{ t('adminDocutilFaq.fieldSearchScopeId') }}</label>
                <input
                  v-model="editForm.searchScopeId"
                  type="text"
                  class="form-control"
                  :placeholder="t('adminDocutilFaq.scopeIdPlaceholder')"
                />
              </div>
              <div v-if="editModal.mode === 'edit'" class="col-12">
                <div class="form-check">
                  <input
                    v-model="editForm.isActive"
                    class="form-check-input"
                    type="checkbox"
                    id="faqIsActive"
                  />
                  <label class="form-check-label" for="faqIsActive">
                    {{ t('adminDocutilFaq.fieldIsActive') }}
                  </label>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="editModal.open = false">
              {{ t('adminDocutilFaq.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="saving"
              @click="onSave"
            >
              <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
              {{ saving ? t('adminDocutilFaq.saving') : t('adminDocutilFaq.save') }}
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
import type { DocUtilFaq, DocUtilFaqDetail } from '@/services/docutilService'

const { t } = useI18n()

// ── 목록 상태 ────────────────────────────────────────────────────────────
const loading = ref(false)
const faqs = ref<DocUtilFaq[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)

// ── 필터 상태(입력 vs 적용된 값 분리) ─────────────────────────────────────
const searchInput = ref('')
const categoryInput = ref('')
const appliedSearch = ref('')
const appliedCategory = ref('')

// ── 알림 ─────────────────────────────────────────────────────────────────
const successMessage = ref('')
const errorMessage = ref('')

// ── 모달 상태 ────────────────────────────────────────────────────────────
const detailModal = reactive<{ open: boolean; faq: DocUtilFaqDetail | null }>({
  open: false,
  faq: null
})
const editModal = reactive<{ open: boolean; mode: 'create' | 'edit'; targetId: string | null }>({
  open: false,
  mode: 'create',
  targetId: null
})
const editForm = reactive({
  question: '',
  answer: '',
  category: '',
  displayOrder: 0,
  searchScopeId: '',
  isActive: true
})
const saving = ref(false)

// ── 파생 값 ──────────────────────────────────────────────────────────────
const totalPages = computed(() => {
  if (total.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / size.value))
})

// ── 로드 ─────────────────────────────────────────────────────────────────
async function loadFaqs(showSuccess: boolean = false) {
  loading.value = true
  errorMessage.value = ''
  try {
    const list = await docutilService.listFaqs(page.value, size.value, {
      category: appliedCategory.value || undefined,
      q: appliedSearch.value || undefined
    })
    faqs.value = list.items
    total.value = list.total
    if (showSuccess) {
      // 새로고침 성공은 별도 메시지 없음 — 무음 갱신.
    }
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilFaq.errorBoundary'))
    faqs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFaqs()
})

// ── 이벤트 ───────────────────────────────────────────────────────────────
function onApplyFilters() {
  appliedSearch.value = searchInput.value.trim()
  appliedCategory.value = categoryInput.value.trim()
  page.value = 1
  loadFaqs()
}

function onClearFilters() {
  searchInput.value = ''
  categoryInput.value = ''
  appliedSearch.value = ''
  appliedCategory.value = ''
  page.value = 1
  loadFaqs()
}

function onPageSizeChange() {
  page.value = 1
  loadFaqs()
}

function onChangePage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  loadFaqs()
}

// ── 상세 ─────────────────────────────────────────────────────────────────
async function openDetail(faq: DocUtilFaq) {
  detailModal.faq = null
  detailModal.open = true
  try {
    detailModal.faq = await docutilService.getFaq(faq.id)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilFaq.errorBoundary'))
    detailModal.open = false
  }
}

// ── 생성/수정 ────────────────────────────────────────────────────────────
function openCreateDialog() {
  editModal.mode = 'create'
  editModal.targetId = null
  editForm.question = ''
  editForm.answer = ''
  editForm.category = ''
  editForm.displayOrder = 0
  editForm.searchScopeId = ''
  editForm.isActive = true
  editModal.open = true
}

function openEditDialog(faq: DocUtilFaq) {
  editModal.mode = 'edit'
  editModal.targetId = faq.id
  editForm.question = faq.question
  editForm.answer = faq.answer
  editForm.category = faq.category ?? ''
  editForm.displayOrder = faq.displayOrder
  editForm.searchScopeId = faq.searchScopeId ?? ''
  editForm.isActive = faq.isActive
  editModal.open = true
}

async function onSave() {
  // 검증
  if (!editForm.question.trim()) {
    errorMessage.value = t('adminDocutilFaq.validationQuestionRequired')
    return
  }
  if (editForm.question.length > 2000) {
    errorMessage.value = t('adminDocutilFaq.validationQuestionLength')
    return
  }
  if (!editForm.answer.trim()) {
    errorMessage.value = t('adminDocutilFaq.validationAnswerRequired')
    return
  }
  if (editForm.category && editForm.category.length > 128) {
    errorMessage.value = t('adminDocutilFaq.validationCategoryLength')
    return
  }

  saving.value = true
  errorMessage.value = ''
  try {
    if (editModal.mode === 'create') {
      await docutilService.createFaq({
        question: editForm.question.trim(),
        answer: editForm.answer.trim(),
        category: editForm.category.trim() || null,
        displayOrder: editForm.displayOrder,
        searchScopeId: editForm.searchScopeId.trim() || null
      })
      successMessage.value = t('adminDocutilFaq.createSuccess')
    } else if (editModal.targetId) {
      await docutilService.updateFaq(editModal.targetId, {
        question: editForm.question.trim(),
        answer: editForm.answer.trim(),
        category: editForm.category.trim() || null,
        displayOrder: editForm.displayOrder,
        isActive: editForm.isActive
      })
      successMessage.value = t('adminDocutilFaq.updateSuccess')
    }
    editModal.open = false
    await loadFaqs()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilFaq.errorUnknown'))
  } finally {
    saving.value = false
  }
}

// ── 삭제 ─────────────────────────────────────────────────────────────────
async function onDelete(faq: DocUtilFaq) {
  if (!window.confirm(t('adminDocutilFaq.confirmDelete'))) return
  errorMessage.value = ''
  try {
    await docutilService.deleteFaq(faq.id)
    successMessage.value = t('adminDocutilFaq.deleteSuccess')
    await loadFaqs()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilFaq.errorUnknown'))
  }
}

// ── 유틸 ─────────────────────────────────────────────────────────────────
function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

function extractError(e: unknown, fallback: string): string {
  if (typeof e === 'object' && e !== null) {
    // axios error
    const anyE = e as { response?: { data?: { message?: string } }; message?: string }
    if (anyE.response?.data?.message) return anyE.response.data.message
    if (anyE.message) return anyE.message
  }
  return fallback
}
</script>

<style scoped>
.admin-docutil-faq .modal {
  background-color: rgba(0, 0, 0, 0.4);
}
</style>
