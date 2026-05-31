<template>
  <div class="page-content-wrap">
    <div class="page-header mb-4">
      <div>
        <h1 class="page-heading">도움말 FAQ 관리</h1>
        <p class="page-desc">사용자에게 노출되는 자주 묻는 질문을 등록·수정·삭제합니다.</p>
      </div>
      <button type="button" class="btn btn-primary" @click="openCreateModal">
        <i class="bi bi-plus-lg"></i> 신규 FAQ
      </button>
    </div>

    <!-- 알림 -->
    <div v-if="successMessage" class="alert alert-success alert-dismissible">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''"></button>
    </div>

    <!-- 필터 -->
    <div class="card aiuiux-card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-3">
            <label class="form-label small">카테고리</label>
            <select v-model="categoryFilter" class="form-select form-select-sm">
              <option value="">전체</option>
              <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label small">활성 여부</label>
            <select v-model="activeFilter" class="form-select form-select-sm">
              <option value="">전체</option>
              <option value="true">활성</option>
              <option value="false">비활성</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label small">검색</label>
            <input v-model="searchText" type="text" class="form-control form-control-sm" placeholder="질문/답변 검색...">
          </div>
          <div class="col-md-2">
            <button type="button" class="btn btn-outline-secondary btn-sm w-100" @click="resetFilters">초기화</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 테이블 -->
    <div class="card aiuiux-card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>불러오는 중...
        </div>
        <table v-else-if="filtered.length > 0" class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th style="width: 60px">ID</th>
              <th style="width: 140px">카테고리</th>
              <th>질문</th>
              <th style="width: 90px" class="text-center">활성</th>
              <th style="width: 80px" class="text-center">정렬순</th>
              <th style="width: 140px">수정일</th>
              <th style="width: 110px" class="text-end">작업</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="faq in filtered" :key="faq.faqId">
              <td>{{ faq.faqId }}</td>
              <td>
                <span class="badge bg-light text-dark">{{ categoryLabel(faq.category) }}</span>
              </td>
              <td class="text-truncate" style="max-width: 500px">{{ faq.question }}</td>
              <td class="text-center">
                <span class="badge" :class="faq.isActive ? 'bg-success' : 'bg-secondary'">
                  {{ faq.isActive ? '활성' : '비활성' }}
                </span>
              </td>
              <td class="text-center">{{ faq.sortOrder }}</td>
              <td class="small text-muted">{{ formatDate(faq.updatedAt) }}</td>
              <td class="text-end">
                <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="openEditModal(faq)" title="수정">
                  <i class="bi bi-pencil"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="onDelete(faq)" title="삭제">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">
          <i class="bi bi-info-circle me-1"></i>등록된 FAQ 가 없습니다.
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-end mt-2">
      <small class="text-muted">총 {{ filtered.length }} / {{ items.length }} 건</small>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="modal.open" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title">{{ modal.mode === 'create' ? '신규 FAQ 등록' : 'FAQ 수정' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label fw-semibold">카테고리 <span class="text-danger">*</span></label>
              <select v-model="modal.form.category" class="form-select">
                <option value="">선택하세요</option>
                <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }} ({{ c.value }})</option>
              </select>
              <small class="text-muted">Help.vue 의 카테고리 카드 / 빠른 링크와 매칭되는 영문 id 입니다.</small>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">질문 <span class="text-danger">*</span></label>
              <input v-model="modal.form.question" type="text" class="form-control" maxlength="500" placeholder="질문 (최대 500자)">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">답변 <span class="text-danger">*</span></label>
              <textarea v-model="modal.form.answer" class="form-control" rows="6" placeholder="답변 본문"></textarea>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">정렬순</label>
                <input v-model.number="modal.form.sortOrder" type="number" class="form-control" min="0" max="9999">
                <small class="text-muted">낮을수록 먼저 표시.</small>
              </div>
              <div class="col-md-6 mb-3 d-flex align-items-end">
                <div class="form-check form-switch">
                  <input v-model="modal.form.isActive" type="checkbox" class="form-check-input" id="faqActive">
                  <label class="form-check-label" for="faqActive">활성 (사용자 화면 노출)</label>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal" :disabled="saving">취소</button>
            <button type="button" class="btn btn-primary" @click="saveModal" :disabled="saving || !canSave">
              <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
              {{ saving ? '저장 중...' : '저장' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="modal.open" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import api from '@/services/api'

// Help.vue 의 4 카테고리와 매칭 — 변경 시 양쪽 동기화 필요
const CATEGORIES = [
  { value: 'getting-started', label: '시작하기' },
  { value: 'agents', label: 'AI 에이전트' },
  { value: 'api', label: 'API' },
  { value: 'troubleshooting', label: '문제 해결' }
]

interface Faq {
  faqId: number
  question: string
  answer: string
  category: string | null
  sortOrder: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

const items = ref<Faq[]>([])
const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const categoryFilter = ref('')
const activeFilter = ref('')
const searchText = ref('')

const modal = reactive({
  open: false,
  mode: 'create' as 'create' | 'edit',
  editId: 0,
  form: {
    question: '',
    answer: '',
    category: '',
    sortOrder: 0,
    isActive: true
  }
})
const saving = ref(false)

const filtered = computed(() => {
  let result = items.value
  if (categoryFilter.value) result = result.filter(f => f.category === categoryFilter.value)
  if (activeFilter.value === 'true') result = result.filter(f => f.isActive)
  if (activeFilter.value === 'false') result = result.filter(f => !f.isActive)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    result = result.filter(f =>
      f.question.toLowerCase().includes(q) || (f.answer || '').toLowerCase().includes(q)
    )
  }
  return [...result].sort((a, b) => a.sortOrder - b.sortOrder || a.faqId - b.faqId)
})

const canSave = computed(() =>
  !!modal.form.category && !!modal.form.question.trim() && !!modal.form.answer.trim()
)

const categoryLabel = (v: string | null): string => {
  if (!v) return '미분류'
  return CATEGORIES.find(c => c.value === v)?.label || v
}

const formatDate = (iso: string): string => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('ko-KR') + ' ' + d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

const resetFilters = () => {
  categoryFilter.value = ''
  activeFilter.value = ''
  searchText.value = ''
}

const load = async () => {
  loading.value = true
  try {
    const { data } = await api.get<Faq[]>('/faqs')
    items.value = data || []
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    errorMessage.value = err.response?.data?.message || 'FAQ 목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  modal.mode = 'create'
  modal.editId = 0
  modal.form = { question: '', answer: '', category: '', sortOrder: 0, isActive: true }
  modal.open = true
}

const openEditModal = (faq: Faq) => {
  modal.mode = 'edit'
  modal.editId = faq.faqId
  modal.form = {
    question: faq.question,
    answer: faq.answer,
    category: faq.category || '',
    sortOrder: faq.sortOrder,
    isActive: faq.isActive
  }
  modal.open = true
}

const closeModal = () => {
  modal.open = false
}

const saveModal = async () => {
  saving.value = true
  try {
    if (modal.mode === 'create') {
      await api.post('/faqs', modal.form)
      successMessage.value = 'FAQ 가 등록되었습니다.'
    } else {
      await api.put(`/faqs/${modal.editId}`, modal.form)
      successMessage.value = 'FAQ 가 수정되었습니다.'
    }
    modal.open = false
    await load()
    setTimeout(() => (successMessage.value = ''), 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    errorMessage.value = err.response?.data?.message || '저장에 실패했습니다.'
  } finally {
    saving.value = false
  }
}

const onDelete = async (faq: Faq) => {
  if (!confirm(`"${faq.question.substring(0, 60)}..." FAQ 를 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/faqs/${faq.faqId}`)
    successMessage.value = 'FAQ 가 삭제되었습니다.'
    await load()
    setTimeout(() => (successMessage.value = ''), 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    errorMessage.value = err.response?.data?.message || '삭제에 실패했습니다.'
  }
}

onMounted(() => load())
</script>
