<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">지식베이스</h1>
        <p class="page-desc">팀의 지식을 체계적으로 관리하고 공유하세요</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-outline-secondary btn-sm me-2" @click="showUploadModal = true">
          <i class="bi bi-upload"></i> 파일 업로드
        </button>
        <button class="btn btn-primary btn-sm" @click="createNewDocument">
          <i class="bi bi-file-earmark-plus"></i> 새 문서 작성
        </button>
      </div>
    </div>

    <div class="row">
      <div class="col-md-3">
        <div class="card aiuiux-card mb-2">
          <div class="card-body py-2 px-3">
            <div class="input-group input-group-sm">
              <input 
                type="text" 
                class="form-control" 
                v-model="searchText"
                placeholder="문서 검색..."
                @keyup.enter="loadDocuments"
              >
              <button class="btn btn-primary" type="button" @click="loadDocuments">
                <i class="bi bi-search"></i>
              </button>
            </div>
          </div>
        </div>
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">문서 목록</h6>
            <div class="filter-segmented" role="group" aria-label="문서 필터">
              <button
                type="button"
                class="filter-segmented-btn"
                :class="{ active: filterIndexed === null }"
                @click="filterIndexed = null"
                title="전체"
              >
                <i class="bi bi-list-ul" aria-hidden="true"></i>
                <span class="filter-segmented-label">전체</span>
              </button>
              <button
                type="button"
                class="filter-segmented-btn filter-segmented-success"
                :class="{ active: filterIndexed === true }"
                @click="filterIndexed = true"
                title="인덱싱된 문서만"
              >
                <i class="bi bi-check-circle" aria-hidden="true"></i>
                <span class="filter-segmented-label">인덱싱</span>
              </button>
              <button
                type="button"
                class="filter-segmented-btn filter-segmented-warning"
                :class="{ active: filterIndexed === false }"
                @click="filterIndexed = false"
                title="미인덱싱 문서만"
              >
                <i class="bi bi-x-circle" aria-hidden="true"></i>
                <span class="filter-segmented-label">미인덱싱</span>
              </button>
            </div>
          </div>
          <div class="card-body" style="max-height: 600px; overflow-y: auto;">
            <div v-if="loading" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
            <div v-else-if="documents.length === 0" class="text-center text-muted py-4 px-3">
              <small>문서가 없습니다.</small>
            </div>
            <ul v-else class="doc-list">
              <li 
                v-for="doc in documents" 
                :key="doc.documentId"
                class="doc-item"
                :class="{ active: selectedDoc?.documentId === doc.documentId }"
                @click="selectDocument(doc)"
              >
                <div class="doc-item-icon">
                  <i class="bi bi-file-earmark-text"></i>
                </div>
                <div class="doc-item-body">
                  <p class="doc-item-title">{{ doc.title }}</p>
                  <p class="doc-item-meta">{{ formatTime(doc.updatedAt) }}</p>
                  <div class="d-flex gap-1 flex-wrap doc-item-badges">
                    <span v-if="doc.isIndexed" class="perm-badge perm-badge-success">인덱싱됨</span>
                    <span v-else class="perm-badge perm-badge-warning">미인덱싱</span>
                    <span v-if="doc.chunkCount > 0" class="perm-badge perm-badge-info">{{ doc.chunkCount }}개 청크</span>
                  </div>
                </div>
                <button 
                  class="btn btn-sm btn-link text-danger p-0 ms-1"
                  @click.stop="deleteDocument(doc.documentId)"
                  title="삭제"
                >
                  <i class="bi bi-trash"></i>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 중앙: 에디터 -->
      <div class="col-md-6">
        <div class="card aiuiux-card">
          <div class="editor-toolbar aiuiux-editor-toolbar">
            <div class="btn-group me-2" role="group">
              <button class="btn btn-sm btn-outline-secondary" @click="formatText('bold')">
                <i class="bi bi-type-bold"></i>
              </button>
              <button class="btn btn-sm btn-outline-secondary" @click="formatText('italic')">
                <i class="bi bi-type-italic"></i>
              </button>
              <button class="btn btn-sm btn-outline-secondary" @click="formatText('h1')">
                <i class="bi bi-type-h1"></i>
              </button>
              <button class="btn btn-sm btn-outline-secondary" @click="formatText('list')">
                <i class="bi bi-list-ul"></i>
              </button>
              <button class="btn btn-sm btn-outline-secondary" @click="formatText('code')">
                <i class="bi bi-code-slash"></i>
              </button>
            </div>
            <div class="ms-auto">
              <button 
                v-if="selectedDoc && !selectedDoc.isIndexed" 
                class="btn btn-sm btn-warning me-2" 
                @click="indexDocument"
                :disabled="indexing"
              >
                <i class="bi bi-database-add"></i> 인덱싱
              </button>
              <button 
                v-if="selectedDoc && selectedDoc.isIndexed" 
                class="btn btn-sm btn-info me-2" 
                @click="reindexDocument"
                :disabled="indexing"
              >
                <i class="bi bi-arrow-clockwise"></i> 재인덱싱
              </button>
              <button class="btn btn-sm btn-success" @click="saveDocument" :disabled="saving">
                <i class="bi bi-save"></i> {{ saving ? '저장 중...' : '저장' }}
              </button>
            </div>
          </div>
          <div class="editor-content">
            <input 
              type="text" 
              class="form-control border-0 fs-3 mb-3" 
              v-model="documentForm.title"
              placeholder="문서 제목"
            >
            <textarea 
              class="form-control border-0" 
              v-model="documentForm.content"
              rows="15" 
              placeholder="내용을 입력하세요..."
            ></textarea>
          </div>
        </div>

        <!-- AI Q&A 도우미 -->
        <div class="card aiuiux-card mt-3" v-if="selectedDoc && selectedDoc.isIndexed">
          <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
            <h6 class="card-title mb-0"><i class="bi bi-robot me-1"></i> AI Q&A</h6>
            <button class="btn btn-xs btn-link text-muted p-0" @click="aiMessages = []" title="대화 초기화">
              <i class="bi bi-arrow-counterclockwise"></i>
            </button>
          </div>
          <div class="card-body p-0">
            <!-- 대화 메시지 -->
            <div class="kb-chat-messages" ref="aiChatEl">
              <div v-if="aiMessages.length === 0" class="kb-chat-empty">
                <i class="bi bi-chat-dots text-muted"></i>
                <p class="text-muted small mb-0">이 문서에 대해 무엇이든 질문하세요.</p>
              </div>
              <div
                v-for="(msg, idx) in aiMessages"
                :key="idx"
                class="kb-chat-msg"
                :class="msg.role === 'user' ? 'kb-msg-user' : 'kb-msg-ai'"
              >
                <div class="kb-msg-bubble">{{ msg.content }}</div>
              </div>
              <div v-if="aiLoading" class="kb-chat-msg kb-msg-ai">
                <div class="kb-msg-bubble kb-typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
            <!-- 입력 -->
            <div class="kb-chat-input">
              <input
                type="text"
                class="form-control form-control-sm"
                v-model="aiQuery"
                placeholder="문서에 대해 질문하세요..."
                @keyup.enter="askAI"
                :disabled="aiLoading"
              >
              <button class="btn btn-sm btn-primary ms-2" @click="askAI" :disabled="aiLoading || !aiQuery.trim()">
                <i class="bi bi-send-fill"></i>
              </button>
            </div>
          </div>
        </div>
        <div class="card aiuiux-card mt-3 text-center py-3" v-else-if="selectedDoc && !selectedDoc.isIndexed">
          <small class="text-muted"><i class="bi bi-info-circle me-1"></i>AI Q&A는 인덱싱된 문서에서만 사용 가능합니다.</small>
        </div>
      </div>

      <!-- 우측: 문서 정보 -->
      <div class="col-md-3">
        <div class="card aiuiux-card mb-3">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="card-title mb-0">문서 정보</h6>
          </div>
          <div class="card-body" v-if="selectedDoc">
            <ul class="activity-stat-list">
              <li class="activity-stat-item">
                <span class="label">생성일</span>
                <span class="value">{{ formatDateTime(selectedDoc.createdAt) }}</span>
              </li>
              <li class="activity-stat-item">
                <span class="label">수정일</span>
                <span class="value">{{ formatDateTime(selectedDoc.updatedAt) }}</span>
              </li>
              <li class="activity-stat-item" v-if="selectedDoc.indexedAt">
                <span class="label">인덱싱일</span>
                <span class="value">{{ formatDateTime(selectedDoc.indexedAt) }}</span>
              </li>
              <li class="activity-stat-item">
                <span class="label">청크 수</span>
                <span class="value">{{ selectedDoc.chunkCount }}</span>
              </li>
              <li class="activity-stat-item" v-if="selectedDoc.sourceType">
                <span class="label">소스 타입</span>
                <span class="value">{{ selectedDoc.sourceType }}</span>
              </li>
            </ul>
          </div>
          <div class="card-body text-muted" v-else>
            <small>문서를 선택하세요.</small>
          </div>
        </div>
      </div>
    </div>

    <!-- 파일 업로드 모달 -->
    <div 
      v-if="showUploadModal" 
      class="modal fade show" 
      style="display: block; background-color: rgba(0,0,0,0.5);"
      @click.self="showUploadModal = false"
    >
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title">파일 업로드</h5>
            <button type="button" class="btn-close" @click="showUploadModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">파일 선택</label>
              <input 
                type="file" 
                class="form-control" 
                ref="fileInput"
                @change="handleFileSelect"
                accept=".pdf,.txt,.csv,.xls,.xlsx,.doc,.docx"
              >
              <small class="text-muted">PDF, TXT, CSV, XLSX, DOCX 파일을 지원합니다.</small>
            </div>
            <div class="mb-3">
              <label class="form-label">제목 (선택)</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="uploadTitle"
                placeholder="파일명이 기본 제목으로 사용됩니다"
              >
            </div>
            <div class="form-check mb-3">
              <input 
                class="form-check-input" 
                type="checkbox" 
                id="indexImmediately"
                v-model="indexImmediately"
              >
              <label class="form-check-label" for="indexImmediately">
                업로드 후 즉시 인덱싱
              </label>
            </div>
            <div v-if="uploading" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">업로드 중...</span>
              </div>
              <small class="d-block mt-2">파일을 업로드하고 인덱싱하는 중입니다...</small>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showUploadModal = false">취소</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="uploadFile"
              :disabled="!selectedFile || uploading"
            >
              {{ uploading ? '업로드 중...' : '업로드' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
// Phase 3 후속 트랙 (C-1): 본 파일은 Phase 2 (자체 KB drop, ADR-2) 에서 제거된
// /api/knowledgebase 백엔드 라우트를 호출하므로 deprecate 대상.
// 운영자 진입점은 /admin/knowledge-base (AdminKnowledgeBase.vue) 로 일원화됨.
// 라우트/뷰 완전 제거는 별도 트랙으로 분리 (vue-tsc 검사 일시 우회).
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '@/services/api'

interface KnowledgeBaseDocumentList {
  documentId: number
  userId: number
  userName: string
  title: string
  sourceType: string
  sourceId?: string
  isIndexed: boolean
  indexedAt?: string
  chunkCount: number
  createdAt: string
  updatedAt: string
}

interface KnowledgeBaseDocument {
  documentId: number
  userId: number
  userName: string
  title: string
  content: string
  sourceType: string
  sourceId?: string
  isIndexed: boolean
  indexedAt?: string
  chunkCount: number
  createdAt: string
  updatedAt: string
}

const selectedDoc = ref<KnowledgeBaseDocument | null>(null)
const documents = ref<KnowledgeBaseDocumentList[]>([])
const searchText = ref('')
const filterIndexed = ref<boolean | null>(null)
const loading = ref(false)
const saving = ref(false)
const indexing = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)
const selectedFile = ref<File | null>(null)
const uploadTitle = ref('')
const indexImmediately = ref(true)
const fileInput = ref<HTMLInputElement | null>(null)
const aiQuery = ref('')
const aiResponse = ref('')
const aiMessages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
const aiLoading = ref(false)
const aiChatEl = ref<HTMLElement | null>(null)

const documentForm = ref({
  title: '',
  content: ''
})

// 필터링된 문서 목록
const filteredDocuments = computed(() => {
  return documents.value
})

// 문서 목록 로드
const loadDocuments = async () => {
  try {
    loading.value = true
    const params: any = {}
    if (searchText.value) {
      params.search = searchText.value
    }
    if (filterIndexed.value !== null) {
      params.isIndexed = filterIndexed.value
    }
    
    const response = await api.get<KnowledgeBaseDocumentList[]>('/knowledgebase', { params })
    documents.value = response.data
  } catch (error: any) {
    console.error('문서 목록 로드 실패:', error)
    alert('문서 목록을 불러오는데 실패했습니다.')
  } finally {
    loading.value = false
  }
}

// 문서 선택
const selectDocument = async (doc: KnowledgeBaseDocumentList) => {
  try {
    loading.value = true
    const response = await api.get<KnowledgeBaseDocument>(`/knowledgebase/${doc.documentId}`)
    selectedDoc.value = response.data
    documentForm.value.title = response.data.title
    documentForm.value.content = response.data.content
  } catch (error: any) {
    console.error('문서 로드 실패:', error)
    alert('문서를 불러오는데 실패했습니다.')
  } finally {
    loading.value = false
  }
}

// 새 문서 생성
const createNewDocument = () => {
  selectedDoc.value = null
  documentForm.value = { title: '', content: '' }
}

// 문서 저장
const saveDocument = async () => {
  if (!documentForm.value.title.trim()) {
    alert('문서 제목을 입력하세요.')
    return
  }

  try {
    saving.value = true
    
    if (selectedDoc.value) {
      // 업데이트
      const response = await api.put<KnowledgeBaseDocument>(
        `/knowledgebase/${selectedDoc.value.documentId}`,
        {
          title: documentForm.value.title,
          content: documentForm.value.content,
          reindex: false // 사용자가 명시적으로 재인덱싱 버튼을 누를 때만 재인덱싱
        }
      )
      selectedDoc.value = response.data
      await loadDocuments() // 목록 새로고침
      alert('문서가 저장되었습니다.')
    } else {
      // 생성
      const response = await api.post<KnowledgeBaseDocument>('/knowledgebase', {
        title: documentForm.value.title,
        content: documentForm.value.content,
        sourceType: 'KnowledgeBase',
        indexImmediately: true
      })
      selectedDoc.value = response.data
      await loadDocuments() // 목록 새로고침
      alert('문서가 생성되었습니다.')
    }
  } catch (error: any) {
    console.error('문서 저장 실패:', error)
    alert(error.response?.data?.message || '문서 저장에 실패했습니다.')
  } finally {
    saving.value = false
  }
}

// 문서 삭제
const deleteDocument = async (documentId: number) => {
  if (!confirm('정말 이 문서를 삭제하시겠습니까?')) {
    return
  }

  try {
    await api.delete(`/knowledgebase/${documentId}`)
    if (selectedDoc.value?.documentId === documentId) {
      selectedDoc.value = null
      documentForm.value = { title: '', content: '' }
    }
    await loadDocuments() // 목록 새로고침
    alert('문서가 삭제되었습니다.')
  } catch (error: any) {
    console.error('문서 삭제 실패:', error)
    alert(error.response?.data?.message || '문서 삭제에 실패했습니다.')
  }
}

// 문서 인덱싱
const indexDocument = async () => {
  if (!selectedDoc.value) return

  try {
    indexing.value = true
    await api.post(`/knowledgebase/${selectedDoc.value.documentId}/index`)
    await selectDocument(selectedDoc.value) // 문서 정보 새로고침
    await loadDocuments() // 목록 새로고침
    alert('문서가 인덱싱되었습니다.')
  } catch (error: any) {
    console.error('인덱싱 실패:', error)
    alert(error.response?.data?.message || '인덱싱에 실패했습니다.')
  } finally {
    indexing.value = false
  }
}

// 문서 재인덱싱
const reindexDocument = async () => {
  if (!selectedDoc.value) return

  if (!confirm('문서를 재인덱싱하시겠습니까? 기존 인덱스가 삭제되고 새로 생성됩니다.')) {
    return
  }

  try {
    indexing.value = true
    await api.post(`/knowledgebase/${selectedDoc.value.documentId}/reindex`)
    await selectDocument(selectedDoc.value) // 문서 정보 새로고침
    await loadDocuments() // 목록 새로고침
    alert('문서가 재인덱싱되었습니다.')
  } catch (error: any) {
    console.error('재인덱싱 실패:', error)
    alert(error.response?.data?.message || '재인덱싱에 실패했습니다.')
  } finally {
    indexing.value = false
  }
}

// 파일 선택
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    if (!uploadTitle.value) {
      uploadTitle.value = selectedFile.value.name.replace(/\.[^/.]+$/, '') // 확장자 제거
    }
  }
}

// 파일 업로드
const uploadFile = async () => {
  if (!selectedFile.value) return

  try {
    uploading.value = true
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    if (uploadTitle.value) {
      formData.append('title', uploadTitle.value)
    }
    formData.append('indexImmediately', indexImmediately.value.toString())

    const response = await api.post('/files/upload/knowledgebase', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    showUploadModal.value = false
    selectedFile.value = null
    uploadTitle.value = ''
    if (fileInput.value) {
      fileInput.value.value = ''
    }

    await loadDocuments() // 목록 새로고침
    alert('파일이 업로드되었습니다.')
  } catch (error: any) {
    console.error('파일 업로드 실패:', error)
    alert(error.response?.data?.message || '파일 업로드에 실패했습니다.')
  } finally {
    uploading.value = false
  }
}

// AI Q&A — 선택 문서 범위 RAG 채팅
const askAI = async () => {
  const q = aiQuery.value.trim()
  if (!q || aiLoading.value || !selectedDoc.value) return

  aiMessages.value.push({ role: 'user', content: q })
  aiQuery.value = ''
  aiLoading.value = true

  await nextTick()
  if (aiChatEl.value) aiChatEl.value.scrollTop = aiChatEl.value.scrollHeight

  try {
    // AiProxy 직접 호출: RAG 모드로 지식 베이스 검색 포함
    const response = await api.post('/ai-proxy/chat', {
      messages: [
        {
          role: 'system',
          content: `당신은 지식 베이스 문서를 기반으로 답변하는 AI 어시스턴트입니다. 문서 제목: "${selectedDoc.value.title}". 아래 컨텍스트를 참고하여 정확하게 답변하세요.`
        },
        ...aiMessages.value.map(m => ({ role: m.role, content: m.content }))
      ],
      enableRag: true,
      ragDocumentId: selectedDoc.value.id,
      language: 'ko'
    })

    const answer = response.data?.content || response.data?.message || '응답을 받지 못했습니다.'
    aiMessages.value.push({ role: 'assistant', content: answer })
  } catch (err: any) {
    const errMsg = err?.response?.data?.message || '응답 생성 중 오류가 발생했습니다.'
    aiMessages.value.push({ role: 'assistant', content: `⚠️ ${errMsg}` })
  } finally {
    aiLoading.value = false
    await nextTick()
    if (aiChatEl.value) aiChatEl.value.scrollTop = aiChatEl.value.scrollHeight
  }
}

const formatText = (type: string) => {
  // 텍스트 포맷팅 로직 (향후 구현 가능)
  console.log('Format:', type)
}

const formatTime = (date: string): string => {
  const now = new Date()
  const docDate = new Date(date)
  const diff = now.getTime() - docDate.getTime()
  const minutes = Math.floor(diff / 60000)
  
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}일 전`
  return docDate.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 필터 변경 시 문서 목록 다시 로드
watch(filterIndexed, () => {
  loadDocuments()
})

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
/* 문서 목록 필터: 세그먼트 컨트롤 */
.filter-segmented {
  display: inline-flex;
  background: var(--ai-bg-light, #f8f9fa);
  border: 1px solid var(--ai-border, #dee2e6);
  border-radius: 8px;
  padding: 2px;
  gap: 0;
}

.filter-segmented-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--ai-text-muted, #6c757d);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.filter-segmented-btn:hover {
  color: var(--ai-text, #212529);
  background: rgba(0, 0, 0, 0.04);
}

.filter-segmented-btn.active {
  background: #fff;
  color: #495057;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.filter-segmented-btn.filter-segmented-success.active {
  background: rgba(25, 135, 84, 0.12);
  color: #0f5132;
}

.filter-segmented-btn.filter-segmented-warning.active {
  background: rgba(255, 193, 7, 0.18);
  color: #664d03;
}

.filter-segmented-label {
  white-space: nowrap;
}

@media (max-width: 576px) {
  .filter-segmented-label {
    display: none;
  }
  .filter-segmented-btn {
    padding: 6px 10px;
  }
}

.editor-toolbar.aiuiux-editor-toolbar {
  padding: 12px 16px;
  background: var(--ai-bg-light);
  border-bottom: 1px solid var(--ai-border);
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.editor-content {
  min-height: 500px;
  padding: 20px;
}

.editor-content input:focus,
.editor-content textarea:focus {
  outline: none;
  box-shadow: none;
  border-color: var(--ai-primary);
}

.modal {
  z-index: 1055;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1050;
}

/* ── KB AI Q&A ── */
.kb-chat-messages {
  max-height: 260px;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.kb-chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px 0;
  font-size: 1.6rem;
}
.kb-chat-msg { display: flex; }
.kb-msg-user { justify-content: flex-end; }
.kb-msg-ai   { justify-content: flex-start; }
.kb-msg-bubble {
  max-width: 88%;
  padding: 7px 12px;
  border-radius: 10px;
  font-size: 0.8125rem;
  line-height: 1.5;
  white-space: pre-wrap;
}
.kb-msg-user .kb-msg-bubble {
  background: var(--ai-primary, #4f46e5);
  color: #fff;
  border-bottom-right-radius: 3px;
}
.kb-msg-ai .kb-msg-bubble {
  background: var(--ai-bg, #f3f4f6);
  color: var(--ai-text, #111827);
  border-bottom-left-radius: 3px;
}
.kb-typing { display: flex; gap: 4px; align-items: center; padding: 10px 14px; }
.kb-typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--ai-text-muted, #9ca3af);
  animation: kb-bounce .9s infinite;
}
.kb-typing span:nth-child(2) { animation-delay: .2s; }
.kb-typing span:nth-child(3) { animation-delay: .4s; }
@keyframes kb-bounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-5px); } }

.kb-chat-input {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-top: 1px solid var(--ai-border, #e5e7eb);
  gap: 6px;
}
</style>
