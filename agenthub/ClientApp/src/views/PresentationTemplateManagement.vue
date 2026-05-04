<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">프레젠테이션 템플릿 관리</h1>
        <p class="page-desc">PPTX 템플릿을 등록·관리합니다. 프레젠테이션 생성 시 여기서 등록한 템플릿을 선택할 수 있습니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="showUploadModal = true">
          <i class="bi bi-upload me-1"></i>템플릿 업로드
        </button>
      </div>
    </div>

    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
        <h6 class="mb-0">등록된 템플릿</h6>
        <div class="d-flex align-items-center gap-2">
          <select class="form-select form-select-sm w-auto" v-model="filterCategory">
            <option value="">전체 카테고리</option>
            <option value="business">비즈니스</option>
            <option value="education">교육</option>
            <option value="marketing">마케팅</option>
            <option value="creative">창의적</option>
          </select>
        </div>
      </div>
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status"></div>
          <p class="mt-2 text-muted">템플릿 목록을 불러오는 중...</p>
        </div>
        <div v-else-if="filteredTemplates.length === 0" class="text-center py-5 text-muted">
          <i class="bi bi-file-earmark-slides display-4"></i>
          <p class="mt-2">등록된 템플릿이 없습니다.</p>
          <p class="small">위 '템플릿 업로드' 버튼으로 PPTX 파일을 등록하세요.</p>
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle aiuiux-table">
            <thead>
              <tr>
                <th>이름</th>
                <th>카테고리</th>
                <th>슬라이드 수</th>
                <th>공개</th>
                <th>등록일</th>
                <th class="text-end">작업</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in filteredTemplates" :key="t.templateId">
                <td>
                  <strong>{{ t.templateName }}</strong>
                  <small v-if="t.description" class="d-block text-muted text-truncate" style="max-width: 200px">{{ t.description }}</small>
                </td>
                <td><span class="badge bg-secondary">{{ categoryLabel(t.category) }}</span></td>
                <td>{{ t.templateStructure?.slideCount ?? '-' }}</td>
                <td>
                  <span v-if="t.isPublic" class="badge bg-success">공개</span>
                  <span v-else class="badge bg-light text-dark">비공개</span>
                </td>
                <td><small>{{ formatDate(t.createdAt) }}</small></td>
                <td class="text-end">
                  <button class="btn btn-sm btn-outline-primary me-1" @click="previewTemplate(t)" title="미리보기">
                    <i class="bi bi-eye"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-secondary me-1" @click="downloadTemplate(t)" title="다운로드">
                    <i class="bi bi-download"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="confirmDelete(t)" title="삭제">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 업로드 모달 -->
    <div
      class="modal fade"
      :class="{ show: showUploadModal, 'd-block': showUploadModal }"
      tabindex="-1"
      v-if="showUploadModal"
      @click.self="showUploadModal = false"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">템플릿 업로드</h5>
            <button type="button" class="btn-close" @click="showUploadModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="uploadTemplate">
              <div class="mb-3">
                <label class="form-label">템플릿 이름 <span class="text-danger">*</span></label>
                <input v-model="uploadForm.templateName" type="text" class="form-control" required placeholder="예: 마케팅 기본 템플릿" />
              </div>
              <div class="mb-3">
                <label class="form-label">설명</label>
                <textarea v-model="uploadForm.description" class="form-control" rows="2" placeholder="선택 사항"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">카테고리</label>
                <select v-model="uploadForm.category" class="form-select">
                  <option value="business">비즈니스</option>
                  <option value="education">교육</option>
                  <option value="marketing">마케팅</option>
                  <option value="creative">창의적</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">PPTX 파일 <span class="text-danger">*</span></label>
                <input ref="fileInput" type="file" class="form-control" accept=".pptx" required @change="onFileSelect" />
                <small class="text-muted">PowerPoint 템플릿(.pptx)만 지원합니다.</small>
              </div>
              <div class="mb-3 form-check">
                <input v-model="uploadForm.isPublic" type="checkbox" class="form-check-input" id="uploadIsPublic" />
                <label class="form-check-label" for="uploadIsPublic">공개 (다른 사용자도 선택 가능)</label>
              </div>
              <div class="d-flex justify-content-end gap-2">
                <button type="button" class="btn btn-secondary" @click="showUploadModal = false">취소</button>
                <button type="submit" class="btn btn-primary" :disabled="uploading || !selectedFile">
                  <span v-if="uploading" class="spinner-border spinner-border-sm me-1"></span>
                  {{ uploading ? '업로드 중...' : '업로드' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showUploadModal }" v-if="showUploadModal" @click="showUploadModal = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { PresentationTemplateDto } from '@/types'

const loading = ref(true)
const templates = ref<PresentationTemplateDto[]>([])
const filterCategory = ref('')
const showUploadModal = ref(false)
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)

const uploadForm = ref({
  templateName: '',
  description: '',
  category: 'business',
  isPublic: false
})

const filteredTemplates = computed(() => {
  if (!filterCategory.value) return templates.value
  return templates.value.filter(t => (t.category || 'business') === filterCategory.value)
})

function categoryLabel(cat: string) {
  const m: Record<string, string> = { business: '비즈니스', education: '교육', marketing: '마케팅', creative: '창의적' }
  return m[cat] || cat
}

function formatDate(s: string) {
  if (!s) return '-'
  const d = new Date(s)
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

async function loadTemplates() {
  loading.value = true
  try {
    const res = await api.get<PresentationTemplateDto[]>('/presentation-templates')
    templates.value = res.data ?? []
  } catch (err: any) {
    console.error('템플릿 목록 로드 실패:', err)
    templates.value = []
  } finally {
    loading.value = false
  }
}

async function uploadTemplate() {
  if (!uploadForm.value.templateName.trim() || !selectedFile.value) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('templateFile', selectedFile.value)
    formData.append('templateName', uploadForm.value.templateName.trim())
    if (uploadForm.value.description) formData.append('description', uploadForm.value.description)
    formData.append('category', uploadForm.value.category)
    formData.append('isPublic', String(uploadForm.value.isPublic))

    await api.post('/presentation-templates/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    showUploadModal.value = false
    uploadForm.value = { templateName: '', description: '', category: 'business', isPublic: false }
    selectedFile.value = null
    if (fileInput.value) fileInput.value.value = ''
    await loadTemplates()
  } catch (err: any) {
    const msg = err.response?.data?.message ?? err.message ?? '업로드에 실패했습니다.'
    alert(msg)
  } finally {
    uploading.value = false
  }
}

const fileDownloading = ref(false)

async function getTemplateFileBlob(templateId: number, inline: boolean): Promise<Blob> {
  const res = await api.get(`/presentation-templates/${templateId}/file`, {
    params: { inline: inline ? 1 : 0 },
    responseType: 'blob'
  })
  return res.data as Blob
}

function previewTemplate(t: PresentationTemplateDto) {
  getTemplateFileBlob(t.templateId, true)
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    })
    .catch((err: any) => {
      const msg = err.response?.data?.message ?? err.message ?? '미리보기를 불러올 수 없습니다.'
      alert(msg)
    })
}

function downloadTemplate(t: PresentationTemplateDto) {
  if (fileDownloading.value) return
  fileDownloading.value = true
  getTemplateFileBlob(t.templateId, false)
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = (t.templateName || 'template').replace(/\.pptx$/i, '') + '.pptx'
      a.click()
      URL.revokeObjectURL(url)
    })
    .catch((err: any) => {
      const msg = err.response?.data?.message ?? err.message ?? '다운로드에 실패했습니다.'
      alert(msg)
    })
    .finally(() => {
      fileDownloading.value = false
    })
}

function confirmDelete(t: PresentationTemplateDto) {
  if (!confirm(`"${t.templateName}" 템플릿을 삭제하시겠습니까?`)) return
  deleteTemplate(t.templateId)
}

async function deleteTemplate(id: number) {
  try {
    await api.delete(`/presentation-templates/${id}`)
    await loadTemplates()
  } catch (err: any) {
    const msg = err.response?.data?.message ?? err.message ?? '삭제에 실패했습니다.'
    alert(msg)
  }
}

onMounted(() => {
  loadTemplates()
})
</script>
