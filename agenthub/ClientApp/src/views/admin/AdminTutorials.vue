<template>
  <div class="page-content-wrap">
    <div class="page-header mb-4">
      <div>
        <h1 class="page-heading">튜토리얼 관리</h1>
        <p class="page-desc">사용자 도움말에 노출되는 튜토리얼 영상/안내 콘텐츠를 등록·수정·삭제합니다.</p>
      </div>
      <button type="button" class="btn btn-primary" @click="openCreateModal">
        <i class="bi bi-plus-lg"></i> 신규 튜토리얼
      </button>
    </div>

    <div v-if="successMessage" class="alert alert-success alert-dismissible">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''"></button>
    </div>

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
            <input v-model="searchText" type="text" class="form-control form-control-sm" placeholder="제목/설명 검색...">
          </div>
          <div class="col-md-2">
            <button type="button" class="btn btn-outline-secondary btn-sm w-100" @click="resetFilters">초기화</button>
          </div>
        </div>
      </div>
    </div>

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
              <th>제목</th>
              <th style="width: 90px" class="text-center">활성</th>
              <th style="width: 80px" class="text-center">조회수</th>
              <th style="width: 80px" class="text-center">정렬순</th>
              <th style="width: 140px">수정일</th>
              <th style="width: 110px" class="text-end">작업</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in filtered" :key="t.tutorialId">
              <td>{{ t.tutorialId }}</td>
              <td><span class="badge bg-light text-dark">{{ categoryLabel(t.category) }}</span></td>
              <td class="text-truncate" style="max-width: 400px">
                <strong>{{ t.title }}</strong>
                <small v-if="t.description" class="d-block text-muted text-truncate">{{ t.description }}</small>
              </td>
              <td class="text-center">
                <span class="badge" :class="t.isActive ? 'bg-success' : 'bg-secondary'">
                  {{ t.isActive ? '활성' : '비활성' }}
                </span>
              </td>
              <td class="text-center">{{ t.viewCount }}</td>
              <td class="text-center">{{ t.sortOrder }}</td>
              <td class="small text-muted">{{ formatDate(t.updatedAt) }}</td>
              <td class="text-end">
                <a v-if="t.videoUrl" :href="t.videoUrl" target="_blank" class="btn btn-sm btn-outline-secondary me-1" title="영상 열기">
                  <i class="bi bi-play-circle"></i>
                </a>
                <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="openEditModal(t)" title="수정">
                  <i class="bi bi-pencil"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger" @click="onDelete(t)" title="삭제">
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">
          <i class="bi bi-info-circle me-1"></i>등록된 튜토리얼이 없습니다.
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-end mt-2">
      <small class="text-muted">총 {{ filtered.length }} / {{ items.length }} 건</small>
    </div>

    <div v-if="modal.open" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title">{{ modal.mode === 'create' ? '신규 튜토리얼 등록' : '튜토리얼 수정' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label fw-semibold">제목 <span class="text-danger">*</span></label>
              <input v-model="modal.form.title" type="text" class="form-control" maxlength="200" placeholder="튜토리얼 제목">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">설명</label>
              <textarea v-model="modal.form.description" class="form-control" rows="3" placeholder="튜토리얼 요약 설명"></textarea>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">카테고리 <span class="text-danger">*</span></label>
                <select v-model="modal.form.category" class="form-select">
                  <option value="">선택하세요</option>
                  <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
                </select>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">재생 시간</label>
                <input v-model="modal.form.duration" type="text" class="form-control" placeholder="예: 5:30">
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">영상 URL</label>
              <input v-model="modal.form.videoUrl" type="url" class="form-control" placeholder="https://...">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">썸네일 URL</label>
              <input v-model="modal.form.thumbnailUrl" type="url" class="form-control" placeholder="https://...">
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">정렬순</label>
                <input v-model.number="modal.form.sortOrder" type="number" class="form-control" min="0" max="9999">
              </div>
              <div class="col-md-6 mb-3 d-flex align-items-end">
                <div class="form-check form-switch">
                  <input v-model="modal.form.isActive" type="checkbox" class="form-check-input" id="tutActive">
                  <label class="form-check-label" for="tutActive">활성 (사용자 화면 노출)</label>
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

const CATEGORIES = [
  { value: 'getting-started', label: '시작하기' },
  { value: 'agents', label: 'AI 에이전트' },
  { value: 'api', label: 'API' },
  { value: 'troubleshooting', label: '문제 해결' }
]

interface Tutorial {
  tutorialId: number
  title: string
  description: string | null
  videoUrl: string | null
  thumbnailUrl: string | null
  duration: string | null
  category: string | null
  sortOrder: number
  isActive: boolean
  viewCount: number
  createdAt: string
  updatedAt: string
}

const items = ref<Tutorial[]>([])
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
    title: '',
    description: '',
    videoUrl: '',
    thumbnailUrl: '',
    duration: '',
    category: '',
    sortOrder: 0,
    isActive: true
  }
})
const saving = ref(false)

const filtered = computed(() => {
  let result = items.value
  if (categoryFilter.value) result = result.filter(t => t.category === categoryFilter.value)
  if (activeFilter.value === 'true') result = result.filter(t => t.isActive)
  if (activeFilter.value === 'false') result = result.filter(t => !t.isActive)
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    result = result.filter(t =>
      t.title.toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q)
    )
  }
  return [...result].sort((a, b) => a.sortOrder - b.sortOrder || a.tutorialId - b.tutorialId)
})

const canSave = computed(() => !!modal.form.title.trim() && !!modal.form.category)

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
    const { data } = await api.get<Tutorial[]>('/tutorials')
    items.value = data || []
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    errorMessage.value = err.response?.data?.message || '튜토리얼 목록을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  modal.mode = 'create'
  modal.editId = 0
  modal.form = { title: '', description: '', videoUrl: '', thumbnailUrl: '', duration: '', category: '', sortOrder: 0, isActive: true }
  modal.open = true
}

const openEditModal = (t: Tutorial) => {
  modal.mode = 'edit'
  modal.editId = t.tutorialId
  modal.form = {
    title: t.title,
    description: t.description || '',
    videoUrl: t.videoUrl || '',
    thumbnailUrl: t.thumbnailUrl || '',
    duration: t.duration || '',
    category: t.category || '',
    sortOrder: t.sortOrder,
    isActive: t.isActive
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
      await api.post('/tutorials', modal.form)
      successMessage.value = '튜토리얼이 등록되었습니다.'
    } else {
      await api.put(`/tutorials/${modal.editId}`, modal.form)
      successMessage.value = '튜토리얼이 수정되었습니다.'
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

const onDelete = async (t: Tutorial) => {
  if (!confirm(`"${t.title}" 튜토리얼을 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/tutorials/${t.tutorialId}`)
    successMessage.value = '튜토리얼이 삭제되었습니다.'
    await load()
    setTimeout(() => (successMessage.value = ''), 3000)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    errorMessage.value = err.response?.data?.message || '삭제에 실패했습니다.'
  }
}

onMounted(() => load())
</script>
