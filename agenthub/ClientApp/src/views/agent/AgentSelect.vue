<template>
  <div class="page-content-wrap">
    <!-- Page Header (agents.html 참고) -->
    <div class="ag-page-header">
      <div class="ag-header-left">
        <h1 class="ag-page-title">AI Agent 선택</h1>
        <p class="ag-page-desc">실행할 Agent를 선택하거나 새로운 Agent를 생성하세요</p>
      </div>
      <div class="ag-header-right">
        <button type="button" class="btn btn-primary" @click="goToCreateBuilder">
          <i class="bi bi-plus-lg"></i> 새 Agent 생성
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="ag-filter-bar">
      <div class="ag-search-wrap">
        <i class="bi bi-search ag-search-icon"></i>
        <input 
          type="text" 
          class="ag-search-input" 
          v-model="searchText" 
          placeholder="Agent 검색... (이름, 설명, 서비스)"
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
        <select class="ag-select" v-model="serviceFilter" @change="filterAgents">
          <option value="">모든 서비스</option>
          <option v-for="service in services" :key="service.serviceId" :value="service.serviceCode">
            {{ service.serviceName }}
          </option>
        </select>
      </div>
      <div class="ag-filter-right">
        <div class="ag-view-btns">
          <button 
            type="button" 
            class="ag-view-btn" 
            :class="{ active: viewMode === 'grid' }" 
            @click="viewMode = 'grid'" 
            title="그리드 보기"
          >
            <i class="bi bi-grid-3x3-gap-fill"></i>
          </button>
          <button 
            type="button" 
            class="ag-view-btn" 
            :class="{ active: viewMode === 'list' }" 
            @click="viewMode = 'list'" 
            title="리스트 보기"
          >
            <i class="bi bi-list-ul"></i>
          </button>
        </div>
        <span class="ag-count-label">전체 <strong>{{ filteredAgents.length + 1 }}</strong>개 Agent</span>
      </div>
    </div>

    <!-- Agent Grid -->
    <div class="ag-grid" :class="{ 'list-view': viewMode === 'list' }" v-show="!showEmpty">
      <!-- 기본 모드 -->
      <div class="ag-card ag-card-default" @click="startDefaultMode">
        <div class="ag-card-body">
          <div class="ag-icon-wrap ag-icon-default">
            <i class="bi bi-chat-dots-fill"></i>
          </div>
          <h5 class="ag-card-title">기본 모드</h5>
          <p class="ag-card-desc">AI 서비스를 직접 선택하고 자유롭게 대화할 수 있는 기본 채팅 모드입니다.</p>
          <div class="ag-service-tags">
            <span 
              v-for="(service, idx) in services.slice(0, 4)" 
              :key="service.serviceId"
              :class="['ag-tag', ['ag-tag-blue','ag-tag-orange','ag-tag-teal','ag-tag-gray'][idx % 4]]"
            >
              {{ service.serviceName }}
            </span>
          </div>
        </div>
        <div class="ag-card-footer">
          <button type="button" class="ag-btn-start ag-btn-full" @click.stop="startDefaultMode">
            <i class="bi bi-play-fill"></i> 시작하기
          </button>
        </div>
      </div>

      <!-- 커스텀 Agent 카드들 -->
      <div 
        v-for="agent in filteredAgents" 
        :key="agent.agentId"
        class="ag-card"
        :style="{ '--ag-color': getAgentDisplayColor(agent.colorCode), '--ag-text': getAgentContrastTextColor(agent.colorCode) }"
      >
        <div class="ag-card-ribbon" v-if="isMyAgent(agent)">커스텀</div>
        <div class="ag-card-body" @click="startAgent(agent)">
          <div class="ag-icon-wrap ag-icon-dynamic">
            <i :class="agent.iconClass || 'bi bi-robot'"></i>
          </div>
          <h5 class="ag-card-title">{{ agent.agentName }}</h5>
          <p class="ag-card-short">{{ agent.description || '커스텀 AI Agent' }}</p>
          <div class="ag-model-badge">
            <i class="bi bi-cpu"></i> {{ agent.defaultModel || agent.serviceName }}
          </div>
          <div class="ag-system-preview" v-if="agent.systemPrompt">
            {{ truncateText(agent.systemPrompt, 120) }}
          </div>
          <div class="ag-system-preview" v-else style="font-style: italic; color: var(--ai-text-muted);">
            시스템 프롬프트가 설정되지 않았습니다.
          </div>
        </div>
        <div class="ag-card-footer ag-footer-flex">
          <button type="button" class="ag-btn-start ag-btn-dynamic" @click.stop="startAgent(agent)">
            <i class="bi bi-play-fill"></i> 실행하기
          </button>
          <button
            v-if="isMyAgent(agent)"
            type="button"
            class="ag-btn-edit"
            @click.stop="goToEditBuilder(agent)"
            title="빌더에서 수정"
          >
            <i class="bi bi-pencil"></i>
          </button>
          <button
            v-if="isMyAgent(agent)"
            type="button"
            class="ag-btn-edit ag-btn-delete-card"
            @click.stop="confirmDeleteAgent(agent)"
            title="Agent 삭제"
          >
            <i class="bi bi-trash"></i>
          </button>
          <a
            v-if="isMyAgent(agent) && agent.agentCode"
            :href="`/agent-test/${agent.agentCode}`"
            target="_blank"
            class="ag-btn-edit"
            title="테스트 & 공유 링크"
            @click.stop
          >
            <i class="bi bi-share"></i>
          </a>
        </div>
      </div>

      <!-- 새 Agent 추가 카드 -->
      <div class="ag-card ag-card-add" @click="goToCreateBuilder">
        <div class="ag-card-body ag-add-body">
          <div class="ag-add-icon">
            <i class="bi bi-plus-lg"></i>
          </div>
          <h5 class="ag-add-title">새 Agent 생성</h5>
          <p class="ag-add-desc">정식 빌더에서 LLM 라우팅·RAG 권위·공유 설정을 함께 구성합니다.</p>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div class="ag-empty" v-show="showEmpty">
      <div class="ag-empty-icon"><i class="bi bi-robot"></i></div>
      <h5>검색 결과가 없습니다</h5>
      <p>다른 키워드나 필터를 사용해 보세요.</p>
      <button type="button" class="btn btn-primary" @click="searchText = ''; serviceFilter = ''; filterAgents()">
        <i class="bi bi-arrow-counterclockwise"></i> 필터 초기화
      </button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAgentDisplayColor, getAgentContrastTextColor } from '@/utils/agentUtils'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { AgentDto, ApiServiceDto } from '@/types'

// 빠른 생성/수정 모달은 deprecate (정식 빌더 `/agents/builder/:id?` 단일 진입점화).
// LlmRouting / KnowledgeBaseSource / KnowledgeBaseRef / RoutingPolicyJson / ConsumerSystems
// 등 Phase 5+ 신규 메타는 모두 정식 빌더에서만 관리한다. 본 페이지는 카탈로그(카드 그리드)
// + 채팅 진입 + 빌더 redirect + 삭제 confirm 만 담당.

const router = useRouter()
const authStore = useAuthStore()
const agents = ref<AgentDto[]>([])
const services = ref<ApiServiceDto[]>([])
const loading = ref(false)
const searchText = ref('')
const serviceFilter = ref('')
const viewMode = ref<'grid' | 'list'>('grid')

const filteredAgents = computed(() => {
  let result = agents.value

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(agent =>
      agent.agentName.toLowerCase().includes(search) ||
      (agent.description || '').toLowerCase().includes(search) ||
      agent.serviceName.toLowerCase().includes(search)
    )
  }

  if (serviceFilter.value) {
    result = result.filter(agent =>
      agent.serviceName.toLowerCase() === serviceFilter.value.toLowerCase()
    )
  }

  return result
})

const showEmpty = computed(() => filteredAgents.value.length === 0 && (searchText.value || serviceFilter.value))

const loadAgents = async () => {
  try {
    loading.value = true
    // isPublic 파라미터 없이 모든 Agent + 서비스 카탈로그(필터 옵션) 동시 fetch
    const [agentsRes, servicesRes] = await Promise.all([
      api.get<AgentDto[]>('/agents'),
      api.get<ApiServiceDto[]>('/apiservices')
    ])
    agents.value = agentsRes.data || []
    services.value = servicesRes.data || []
  } catch (error: any) {
    console.error('Error loading agents:', error)
    if (error.response?.status === 500) {
      console.error('Server error. Check backend logs for details.')
    }
  } finally {
    loading.value = false
  }
}

const filterAgents = () => {
  // computed property 가 자동으로 업데이트됨
}

const startDefaultMode = () => {
  router.push('/agents/chat')
}

const startAgent = (agent: AgentDto) => {
  router.push(`/agents/chat/${agent.agentId}`)
}

// 본인이 만든 Agent 인지 확인
const isMyAgent = (agent: AgentDto): boolean => {
  return authStore.user?.userId === agent.createdBy
}

// 정식 빌더로 redirect — 신규 Agent 생성
const goToCreateBuilder = () => {
  router.push('/agents/builder')
}

// 정식 빌더로 redirect — 기존 Agent 수정 (deep link)
const goToEditBuilder = (agent: AgentDto) => {
  router.push(`/agents/builder/${agent.agentId}`)
}

// Agent 삭제 — confirm dialog + DELETE 호출 + 카탈로그 재조회
const confirmDeleteAgent = async (agent: AgentDto) => {
  if (!confirm(`정말로 "${agent.agentName}" Agent를 삭제하시겠습니까?`)) {
    return
  }

  try {
    await api.delete(`/agents/${agent.agentId}`)
    alert('Agent가 성공적으로 삭제되었습니다.')
    await loadAgents()
  } catch (error: any) {
    console.error('Error deleting agent:', error)
    const errorMessage = error.response?.data?.message || error.response?.data?.error || 'Agent 삭제 중 오류가 발생했습니다.'
    alert(errorMessage)
  }
}

// 텍스트 자르기 헬퍼
const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.ag-header-left { flex: 1; }
.ag-header-right { flex-shrink: 0; }
/* 카드 풋터의 삭제 버튼 — 호버 시 빨간색 강조 */
.ag-btn-delete-card:hover { color: var(--bs-danger, #dc3545); }
</style>
