<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">금칙어 관리</h1>
        <p class="page-desc">등록된 금칙어가 포함된 메시지는 자동으로 차단됩니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="openAddModal">
          <i class="bi bi-plus-circle me-1"></i>금칙어 추가
        </button>
      </div>
    </div>

    <!-- 탭 -->
    <div class="banned-tabs" role="tablist">
      <button
        type="button"
        role="tab"
        class="banned-tab"
        :class="{ active: activeTab === 'global' }"
        :aria-selected="activeTab === 'global'"
        @click="handleTabChange('global')"
      >
        <i class="bi bi-globe" aria-hidden="true"></i>
        <span>전역 금칙어</span>
      </button>
      <button
        type="button"
        role="tab"
        class="banned-tab"
        :class="{ active: activeTab === 'agent' }"
        :aria-selected="activeTab === 'agent'"
        @click="handleTabChange('agent')"
      >
        <i class="bi bi-robot" aria-hidden="true"></i>
        <span>Agent별 금칙어</span>
      </button>
    </div>

    <!-- Agent 선택 (Agent별 탭일 때만 표시) -->
    <div v-if="activeTab === 'agent'" class="row mb-3">
      <div class="col-12">
        <div class="d-flex align-items-center gap-2">
          <label class="mb-0"><i class="bi bi-robot"></i> Agent 선택:</label>
          <select class="form-select form-select-sm select-auto-max-300" v-model="selectedAgentId" @change="handleAgentChange">
            <option :value="null">전체 Agent</option>
            <option v-for="a in myAgents" :key="a.agentId" :value="a.agentId">{{ a.agentName }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 금칙어 목록 -->
    <div class="row">
      <div class="col-12">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <div>
              <h5 class="card-title mb-0">
                {{ activeTab === 'global' ? '전역 금칙어' : 'Agent별 금칙어' }}
                <span class="ag-count-label ms-2">총 <strong>{{ totalCount }}</strong>개</span>
              </h5>
              <p class="card-subtitle mb-0">목록 추가·삭제</p>
            </div>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="mt-2 mb-0 text-muted">로딩 중...</p>
            </div>
            <div v-else-if="bannedWords.length === 0" class="text-center py-5 text-muted">
              <i class="bi bi-shield-check icon-3xl"></i>
              <p class="mt-3">등록된 금칙어가 없습니다.</p>
            </div>
            <div v-else>
              <div v-for="bw in bannedWords" :key="bw.bannedWordId" class="bw-item">
                <div class="bw-item-main">
                  <div class="bw-item-body">
                    <div class="bw-item-header">
                      <span class="bw-word">{{ bw.word }}</span>
                      <span class="status-badge ms-2" :class="bw.isActive ? 'status-online' : 'status-offline'">
                        {{ bw.isActive ? '활성' : '비활성' }}
                      </span>
                    </div>
                    <div class="bw-item-meta">
                      <span v-if="bw.agentName" class="perm-badge perm-badge-info me-2">{{ bw.agentName }}</span>
                      <span v-else class="perm-badge perm-badge-default me-2">전역</span>
                      <span v-if="bw.description" class="bw-desc">{{ bw.description }}</span>
                      <span class="bw-date">등록일 {{ formattedDates.get(bw.bannedWordId) || formatDate(bw.createdAt) }}</span>
                    </div>
                  </div>
                  <div class="bw-item-actions">
                    <button class="btn btn-sm btn-outline-primary" @click="openEditModal(bw)" title="수정">
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-secondary" 
                      @click="toggleActive(bw)"
                      :title="bw.isActive ? '비활성화' : '활성화'"
                    >
                      <i class="bi" :class="bw.isActive ? 'bi-pause' : 'bi-play'"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteBannedWord(bw)" title="삭제">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 페이지네이션 -->
            <div class="d-flex justify-content-between align-items-center mt-4" v-if="bannedWords.length > 0">
              <div class="text-muted">
                총 <strong>{{ totalCount }}</strong>개의 금칙어 중 
                <strong>{{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalCount) }}</strong> 표시
              </div>
              <nav>
                <ul class="pagination mb-0">
                  <li class="page-item" :class="{ disabled: currentPage === 1 }">
                    <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">
                      <i class="bi bi-chevron-left"></i>
                    </a>
                  </li>
                  <li 
                    v-for="page in visiblePages" 
                    :key="page"
                    class="page-item" 
                    :class="{ active: page === currentPage }"
                  >
                    <a class="page-link" href="#" @click.prevent="changePage(page)">
                      {{ page }}
                    </a>
                  </li>
                  <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                    <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">
                      <i class="bi bi-chevron-right"></i>
                    </a>
                  </li>
                </ul>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 금칙어 추가 모달 -->
    <div class="modal fade" :class="{ show: showAddModal, 'd-block': showAddModal }" tabindex="-1" v-if="showAddModal">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-shield-exclamation"></i> 금칙어 추가</h5>
            <button type="button" class="btn-close" @click="closeAddModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">금칙어 *</label>
              <input type="text" class="form-control" v-model="newBannedWord.word" placeholder="예: 비속어, 금지어구" required>
              <small class="text-muted">차단할 단어 또는 문구를 입력하세요.</small>
            </div>
            <div class="mb-3" v-if="activeTab === 'agent'">
              <label class="form-label">적용 대상</label>
              <select class="form-select" v-model="newBannedWord.agentId">
                <option :value="null">전역 (모든 Agent)</option>
                <option v-for="a in myAgents" :key="a.agentId" :value="a.agentId">{{ a.agentName }}</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">설명 (선택)</label>
              <textarea class="form-control" rows="2" v-model="newBannedWord.description" placeholder="금칙어 등록 사유 또는 설명"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="closeAddModal">취소</button>
            <button type="button" class="btn btn-primary" :disabled="!newBannedWord.word.trim()" @click="createBannedWord">
              <i class="bi bi-check-lg"></i> 추가
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showAddModal }" v-if="showAddModal" @click="closeAddModal"></div>

    <!-- 금칙어 수정 모달 -->
    <div class="modal fade" :class="{ show: showEditModal, 'd-block': showEditModal }" tabindex="-1" v-if="showEditModal">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil"></i> 금칙어 수정</h5>
            <button type="button" class="btn-close" @click="closeEditModal"></button>
          </div>
          <div class="modal-body" v-if="editingBannedWord">
            <div class="mb-3">
              <label class="form-label">금칙어 *</label>
              <input type="text" class="form-control" v-model="editingBannedWord.word" required>
            </div>
            <div class="mb-3" v-if="activeTab === 'agent'">
              <label class="form-label">적용 대상</label>
              <select class="form-select" v-model="editingBannedWord.agentId">
                <option :value="null">전역 (모든 Agent)</option>
                <option v-for="a in myAgents" :key="a.agentId" :value="a.agentId">{{ a.agentName }}</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">설명</label>
              <textarea class="form-control" rows="2" v-model="editingBannedWord.description"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="closeEditModal">취소</button>
            <button type="button" class="btn btn-primary" :disabled="!editingBannedWord?.word?.trim()" @click="updateBannedWord">
              <i class="bi bi-check-lg"></i> 저장
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showEditModal }" v-if="showEditModal" @click="closeEditModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import type { BannedWordDto, CreateBannedWordRequestDto, UpdateBannedWordRequestDto, AgentDto } from '@/types'

const activeTab = ref<'global' | 'agent'>('global')
const bannedWords = ref<BannedWordDto[]>([])
const loading = ref(false)
const showAddModal = ref(false)
const showEditModal = ref(false)
const editingBannedWord = ref<BannedWordDto | null>(null)
const myAgents = ref<AgentDto[]>([])
const selectedAgentId = ref<number | null>(null)

// 페이징 관련
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)
const totalPages = computed(() => Math.ceil(totalCount.value / pageSize.value))

// 날짜 포맷팅 캐시 (성능 최적화)
const formattedDates = ref(new Map<number, string>())

// Phase 3 vue-tsc 2.x 부채 정리 — null 사용을 undefined 로 좁힘
// (DTO 의 agentId?: number 와 정렬, intersection 결과 null 이 거부되는 문제 해소)
const newBannedWord = ref<CreateBannedWordRequestDto>({
  word: '',
  agentId: undefined,
  description: ''
})

onMounted(() => {
  loadBannedWords()
  if (activeTab.value === 'agent') {
    loadAgents()
  }
})

const loadAgents = async () => {
  try {
    const res = await api.get<AgentDto[]>('/agents')
    myAgents.value = (res.data || []).filter((a: AgentDto) => a.isActive)
  } catch (e: any) {
    console.error('Agent 목록 로드 실패:', e)
    myAgents.value = []
  }
}

// 중복 요청 방지를 위한 플래그
let isLoadingBannedWords = false

const loadBannedWords = async () => {
  // 이미 로딩 중이면 무시
  if (isLoadingBannedWords) return
  
  isLoadingBannedWords = true
  loading.value = true
  
  try {
    const agentId = activeTab.value === 'agent' ? selectedAgentId.value : null
    const res = await api.get<{ items: BannedWordDto[], totalCount: number, page: number, pageSize: number, totalPages: number }>('/bannedwords', { 
      params: { 
        agentId,
        page: currentPage.value,
        pageSize: pageSize.value
      } 
    })
    
    if (res.data && typeof res.data === 'object' && 'items' in res.data) {
      bannedWords.value = res.data.items || []
      totalCount.value = res.data.totalCount || 0
      
      // 날짜 포맷팅 캐시 업데이트
      formattedDates.value.clear()
      bannedWords.value.forEach(bw => {
        formattedDates.value.set(bw.bannedWordId, formatDate(bw.createdAt))
      })
    } else {
      // 레거시 응답 형식 지원
      bannedWords.value = Array.isArray(res.data) ? res.data : []
      totalCount.value = bannedWords.value.length
      
      // 날짜 포맷팅 캐시 업데이트
      formattedDates.value.clear()
      bannedWords.value.forEach(bw => {
        formattedDates.value.set(bw.bannedWordId, formatDate(bw.createdAt))
      })
    }
  } catch (e: any) {
    console.error('금칙어 목록 로드 실패:', e)
    bannedWords.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
    isLoadingBannedWords = false
  }
}

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadBannedWords()
}

const openAddModal = () => {
  newBannedWord.value = {
    word: '',
    agentId: activeTab.value === 'agent' ? (selectedAgentId.value ?? undefined) : undefined,
    description: ''
  }
  showAddModal.value = true
}

const closeAddModal = () => {
  showAddModal.value = false
  newBannedWord.value = { word: '', agentId: undefined, description: '' }
}

const createBannedWord = async () => {
  try {
    const request: CreateBannedWordRequestDto = {
      word: newBannedWord.value.word.trim(),
      agentId: newBannedWord.value.agentId ?? undefined,
      description: newBannedWord.value.description?.trim() || undefined
    }
    await api.post('/bannedwords', request)
    closeAddModal()
    await loadBannedWords()
    alert('금칙어가 추가되었습니다.')
  } catch (e: any) {
    console.error('금칙어 추가 실패:', e)
    alert(e.response?.data?.message || '금칙어 추가에 실패했습니다.')
  }
}

const openEditModal = (bw: BannedWordDto) => {
  editingBannedWord.value = { ...bw }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingBannedWord.value = null
}

const updateBannedWord = async () => {
  if (!editingBannedWord.value) return

  try {
    const request: UpdateBannedWordRequestDto = {
      word: editingBannedWord.value.word.trim(),
      agentId: editingBannedWord.value.agentId ?? undefined,
      description: editingBannedWord.value.description?.trim() || undefined
    }
    await api.put(`/bannedwords/${editingBannedWord.value.bannedWordId}`, request)
    closeEditModal()
    await loadBannedWords()
    alert('금칙어가 수정되었습니다.')
  } catch (e: any) {
    console.error('금칙어 수정 실패:', e)
    alert(e.response?.data?.message || '금칙어 수정에 실패했습니다.')
  }
}

const toggleActive = async (bw: BannedWordDto) => {
  try {
    const request: UpdateBannedWordRequestDto = {
      isActive: !bw.isActive
    }
    await api.put(`/bannedwords/${bw.bannedWordId}`, request)
    await loadBannedWords()
  } catch (e: any) {
    console.error('금칙어 상태 변경 실패:', e)
    alert(e.response?.data?.message || '금칙어 상태 변경에 실패했습니다.')
  }
}

const deleteBannedWord = async (bw: BannedWordDto) => {
  if (!confirm(`"${bw.word}" 금칙어를 삭제하시겠습니까?`)) {
    return
  }

  try {
    await api.delete(`/bannedwords/${bw.bannedWordId}`)
    await loadBannedWords()
    alert('금칙어가 삭제되었습니다.')
  } catch (e: any) {
    console.error('금칙어 삭제 실패:', e)
    alert(e.response?.data?.message || '금칙어 삭제에 실패했습니다.')
  }
}

const formatDate = (date: string | Date) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 탭 변경 핸들러 (중복 호출 방지)
const handleTabChange = async (tab: 'global' | 'agent') => {
  if (activeTab.value === tab) return // 이미 같은 탭이면 무시
  activeTab.value = tab
  currentPage.value = 1
  if (tab === 'agent' && myAgents.value.length === 0) {
    await loadAgents()
  }
  await loadBannedWords()
}

// Agent 변경 핸들러 (중복 호출 방지)
const handleAgentChange = () => {
  currentPage.value = 1
  loadBannedWords()
}
</script>

<style scoped>
.bw-item {
  padding: 14px 18px;
  border: 1px solid var(--ai-border-light);
  border-radius: var(--ai-radius);
  background: var(--ai-bg-card);
  margin-bottom: 12px;
  transition: background 0.15s, border-color 0.15s;
}

.bw-item:hover {
  background: var(--ai-bg-light);
  border-color: var(--ai-border);
}

.bw-item-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.bw-item-body {
  flex: 1;
  min-width: 0;
}

.bw-item-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.bw-word {
  font-size: 14px;
  font-weight: 600;
  color: var(--ai-text-primary);
}

.bw-item-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--ai-text-muted);
}

.bw-desc {
  color: var(--ai-text-secondary);
}

.bw-date {
  font-size: 11px;
}

.bw-item-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.bw-item-actions .btn {
  padding: 4px 6px;
}

/* status-offline: 비활성 상태 (muted) */
.status-badge.status-offline {
  background: var(--ai-bg-light);
  color: var(--ai-text-muted);
}

/* perm-badge-default: 전역 등 중립 배지 */
.perm-badge.perm-badge-default {
  background: var(--ai-bg-light);
  color: var(--ai-text-secondary);
  border: 1px solid var(--ai-border);
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}

/* 탭: 세그먼트 스타일 */
.banned-tabs {
  display: inline-flex;
  background: var(--ai-bg-light, #f1f3f5);
  border: 1px solid var(--ai-border, #dee2e6);
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
  margin-bottom: 1rem;
}

.banned-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--ai-text-muted, #6c757d);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}

.banned-tab:hover {
  color: var(--ai-text, #212529);
  background: rgba(255, 255, 255, 0.7);
}

.banned-tab.active {
  background: #fff;
  color: var(--ai-primary, #0d6efd);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.banned-tab i {
  font-size: 1.05em;
  opacity: 0.9;
}
</style>
