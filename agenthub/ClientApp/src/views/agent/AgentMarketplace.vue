<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">Agent 마켓플레이스</h1>
        <p class="page-desc">커뮤니티가 만든 Agent를 탐색하고 다운로드하세요</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="$router.push('/agents/builder')">
          <i class="bi bi-plus-circle"></i> 내 Agent 업로드
        </button>
      </div>
    </div>

    <!-- 검색 & 필터 -->
    <div class="ag-filter-bar mb-4">
      <div class="ag-search-wrap">
        <i class="bi bi-search ag-search-icon"></i>
        <input 
          type="text" 
          class="ag-search-input" 
          v-model="searchText"
          placeholder="Agent 검색... (이름, 설명)"
          @input="filterAgents"
        >
        <button 
          type="button" 
          class="ag-search-clear" 
          v-show="searchText" 
          @click="searchText = ''; filterAgents()"
        >
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
      <div class="ag-filter-selects">
        <select class="ag-select" v-model="categoryFilter" @change="filterAgents">
          <option value="">전체 카테고리</option>
          <option value="coding">코딩</option>
          <option value="writing">문서 작성</option>
          <option value="analysis">데이터 분석</option>
          <option value="marketing">마케팅</option>
        </select>
        <select class="ag-select" v-model="sortBy" @change="filterAgents">
          <option value="popular">인기순</option>
          <option value="recent">최신순</option>
          <option value="rating">평점순</option>
          <option value="downloads">다운로드순</option>
        </select>
      </div>
      <div class="ag-filter-right">
        <span class="ag-count-label">전체 <strong>{{ filteredAgents.length }}</strong>개</span>
      </div>
    </div>

    <!-- Agent 카드 그리드 -->
    <div class="row">
      <div 
        v-for="agent in filteredAgents" 
        :key="agent.agentId"
        class="col-lg-3 col-md-4 col-sm-6 mb-4"
      >
        <div class="card aiuiux-card h-100 agent-card" @click="viewAgent(agent)">
          <div class="card-body text-center">
            <div 
              class="agent-icon mx-auto mb-3"
              :style="{ 
                background: getAgentDisplayColor(agent.colorCode, '#0d6efd'),
                width: '60px',
                height: '60px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2rem',
                color: getAgentContrastTextColor(getAgentDisplayColor(agent.colorCode, '#0d6efd'))
              }"
            >
              <i :class="agent.iconClass || 'bi bi-robot'"></i>
            </div>
            <h5 class="card-title">{{ agent.agentName }}</h5>
            <p class="card-text text-muted small" style="min-height: 60px;">
              {{ agent.description || '커뮤니티에서 만든 Agent입니다.' }}
            </p>
            <div class="mb-3">
              <span class="badge bg-secondary me-1">
                <i :class="getServiceIcon(agent.serviceName)"></i> {{ agent.serviceName }}
              </span>
              <span class="badge bg-info">
                <i class="bi bi-download"></i> {{ agent.downloadCount || 0 }}
              </span>
            </div>
            <div class="d-flex align-items-center justify-content-center mb-2">
              <i class="bi bi-star-fill text-warning me-1"></i>
              <strong>{{ agent.rating || '4.5' }}</strong>
              <span class="text-muted ms-1">({{ agent.reviewCount || 0 }})</span>
            </div>
          </div>
          <div class="card-footer bg-white text-center">
            <button class="btn btn-primary btn-sm w-100" @click.stop="installAgent(agent)">
              <i class="bi bi-download"></i> 설치하기
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 페이지네이션 -->
    <div class="row">
      <div class="col-12">
        <nav>
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="goToPage(currentPage - 1)">이전</a>
            </li>
            <li 
              v-for="page in totalPages" 
              :key="page"
              class="page-item"
              :class="{ active: page === currentPage }"
            >
              <a class="page-link" href="#" @click.prevent="goToPage(page)">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="goToPage(currentPage + 1)">다음</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- Agent 상세 모달 -->
    <div class="modal fade" :class="{ show: showDetailModal }" :style="{ display: showDetailModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content" v-if="selectedAgent">
          <div class="modal-header">
            <h5 class="modal-title">
              <i :class="selectedAgent.iconClass || 'bi bi-robot'" :style="{ color: getAgentDisplayColor(selectedAgent.colorCode, '#0d6efd') }"></i>
              {{ selectedAgent.agentName }}
            </h5>
            <button type="button" class="btn-close" @click="showDetailModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <strong>설명</strong>
              <p>{{ selectedAgent.description }}</p>
            </div>
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>서비스:</strong> {{ selectedAgent.serviceName }}
              </div>
              <div class="col-md-6">
                <strong>제작자:</strong> {{ selectedAgent.createdByName }}
              </div>
            </div>
            <div class="mb-3">
              <strong>다운로드:</strong> {{ selectedAgent.downloadCount || 0 }}회
              <strong class="ms-3">평점:</strong> {{ selectedAgent.rating || '4.5' }} ({{ selectedAgent.reviewCount || 0 }}개 리뷰)
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showDetailModal = false">닫기</button>
            <button type="button" class="btn btn-primary" @click="installAgent(selectedAgent)">
              <i class="bi bi-download"></i> 설치하기
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showDetailModal }" v-if="showDetailModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAgentDisplayColor, getAgentContrastTextColor } from '@/utils/agentUtils'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import type { AgentDto } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
// 트랙 #134 (2026-05-29): 마켓플레이스 = "다른 사용자가 만든 Public Agent 둘러보고
// 가져다 쓰는 곳" 정의 명확화. 본인 작성 Public Agent 는 /agents (선택) 에서
// 이미 관리되므로 중복 표시 + UX 혼란 회피 위해 본인 작성 제외.
const isOthersAgent = (a: AgentDto) => a.createdBy !== authStore.user?.userId
const agents = ref<AgentDto[]>([])
const loading = ref(false)
const searchText = ref('')
const categoryFilter = ref('')
const sortBy = ref('popular')
const currentPage = ref(1)
const itemsPerPage = 10
const showDetailModal = ref(false)
const selectedAgent = ref<AgentDto | null>(null)

const filteredAgents = computed(() => {
  // 트랙 #134: isPublic && 본인 작성 아닌 것만 (마켓플레이스 = 타인 공유 Public Agent)
  let result = agents.value.filter(a => a.isPublic && isOthersAgent(a))

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(agent => 
      agent.agentName.toLowerCase().includes(search) ||
      (agent.description || '').toLowerCase().includes(search)
    )
  }

  if (categoryFilter.value) {
    // 카테고리 필터링은 나중에 구현
  }

  // 정렬
  result = [...result].sort((a, b) => {
    switch (sortBy.value) {
      case 'recent':
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      case 'rating':
        return (b.rating || 0) - (a.rating || 0)
      case 'downloads':
        return (b.downloadCount || 0) - (a.downloadCount || 0)
      default:
        return (b.downloadCount || 0) - (a.downloadCount || 0)
    }
  })

  const start = (currentPage.value - 1) * itemsPerPage
  const end = start + itemsPerPage
  return result.slice(start, end)
})

const totalPages = computed(() => {
  // 트랙 #134: filteredAgents 와 정합 — 본인 작성 제외
  return Math.ceil(agents.value.filter(a => a.isPublic && isOthersAgent(a)).length / itemsPerPage)
})

const loadAgents = async () => {
  try {
    loading.value = true
    const response = await api.get<AgentDto[]>('/agents', { params: { isPublic: true } })
    agents.value = response.data || []
  } catch (error) {
    console.error('Error loading agents:', error)
  } finally {
    loading.value = false
  }
}

const filterAgents = () => {
  currentPage.value = 1
  // computed가 자동으로 업데이트됨
}

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

const viewAgent = (agent: AgentDto) => {
  selectedAgent.value = agent
  showDetailModal.value = true
}

const installAgent = async (agent: AgentDto) => {
  try {
    // Agent를 내 Agent 목록에 추가 (간단히 복사하는 개념)
    await api.post('/agents', {
      agentName: agent.agentName,
      description: agent.description,
      serviceId: agent.serviceId,
      defaultModel: agent.defaultModel || 'gpt-4-turbo',
      systemPrompt: agent.systemPrompt,
      iconClass: agent.iconClass,
      colorCode: getAgentDisplayColor(agent.colorCode, '#0d6efd'),
      temperature: agent.temperature,
      maxTokens: agent.maxTokens,
      isPublic: false
    })
    alert('Agent가 설치되었습니다!')
    router.push('/agents')
  } catch (error: any) {
    console.error('Error installing agent:', error)
    alert(error.response?.data?.message || 'Agent 설치 중 오류가 발생했습니다.')
  }
}

const getServiceIcon = (serviceName: string): string => {
  const name = serviceName.toLowerCase()
  if (name.includes('chatgpt') || name.includes('gpt')) return 'bi bi-chat-square-text'
  if (name.includes('claude')) return 'bi bi-robot'
  if (name.includes('cursor')) return 'bi bi-code-slash'
  if (name.includes('copilot')) return 'bi bi-github'
  return 'bi bi-cpu'
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.agent-card {
  cursor: pointer;
  transition: all 0.3s;
}

.agent-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>
