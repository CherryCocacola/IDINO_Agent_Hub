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
        <!-- 트랙 #127 (2026-05-29): 소유권 필터. Admin 은 다른 사용자가 만든 Agent 까지 보이는
             설계(AgentsController.cs:52)라 운영 화면이 혼잡할 수 있음. 본 select 로 관점 전환
             가능 — "내 Agent" / "Public Agent" / "타인 Agent" / "모든 Agent". -->
        <select class="ag-select" v-model="ownerFilter" @change="filterAgents">
          <option value="all">모든 Agent</option>
          <option value="mine">내 Agent</option>
          <option value="public">Public Agent</option>
          <option value="others">타인 Agent</option>
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
        <!-- 트랙 #127 (2026-05-29): 소유권/공개 라벨 동적 표시. 본인 작성 vs Public vs 타인
             구분을 카드 좌상단 ribbon 으로 노출. Admin 운영 화면 혼란 방지. -->
        <div class="ag-card-ribbon" :class="getRibbonClass(agent)">{{ getRibbonLabel(agent) }}</div>
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
          <!-- 트랙 #133 (2026-05-29): 공유 버튼이 새 탭으로 /agent-test/:code 이동했으나
               sessionStorage per-tab 격리로 토큰 부재 → 로그인 redirect 결함.
               Modal 로 공유 URL/QR/복사 즉시 노출하여 현재 화면 유지 + 인증 우회.
               전체 테스트 페이지는 modal 안 보조 링크로 제공 (같은 탭 이동). -->
          <button
            v-if="isMyAgent(agent) && agent.agentCode"
            type="button"
            class="ag-btn-edit"
            title="공유 링크"
            @click.stop="openShareModal(agent)"
          >
            <i class="bi bi-share"></i>
          </button>
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

    <!-- 트랙 #133: 공유 modal — Agent 의 외부 공유 URL + QR + 복사. -->
    <div v-if="shareAgent" class="ag-share-modal-backdrop" @click="shareAgent = null">
      <div class="ag-share-modal" @click.stop>
        <div class="ag-share-modal-header">
          <h5 class="mb-0">
            <i class="bi bi-share me-2"></i>{{ shareAgent.agentName }} 공유
          </h5>
          <button type="button" class="btn-close" @click="shareAgent = null"></button>
        </div>
        <div class="ag-share-modal-body">
          <div class="ag-share-section">
            <label class="form-label small fw-semibold">공유 URL</label>
            <div class="ag-share-url-row">
              <input type="text" class="form-control form-control-sm" :value="shareUrl" readonly>
              <button type="button" class="btn btn-primary btn-sm" @click="copyShareUrl">
                <i class="bi bi-copy"></i> 복사
              </button>
            </div>
            <small class="text-muted">외부 사용자가 인증 없이 이 Agent 와 대화할 수 있는 공개 링크입니다.</small>
          </div>
          <div class="ag-share-section">
            <label class="form-label small fw-semibold">QR 코드</label>
            <div class="ag-share-qr">
              <img :src="`/api/agents/public/${shareAgent.agentCode}/qr?size=160`" alt="QR" width="160" height="160" />
              <div class="d-flex flex-column gap-2">
                <a :href="`/api/agents/public/${shareAgent.agentCode}/qr?size=400`"
                   download="qr-code.png" class="btn btn-outline-secondary btn-sm">
                  <i class="bi bi-download"></i> QR 이미지 다운로드
                </a>
                <small class="text-muted">QR 스캔 시 공유 URL 로 이동합니다.</small>
              </div>
            </div>
          </div>
          <div class="ag-share-section">
            <label class="form-label small fw-semibold">iframe 임베드</label>
            <div class="ag-share-url-row">
              <input type="text" class="form-control form-control-sm" :value="embedUrl" readonly>
              <button type="button" class="btn btn-secondary btn-sm" @click="copyEmbedUrl">
                <i class="bi bi-copy"></i> 복사
              </button>
            </div>
            <small class="text-muted">외부 사이트에 iframe 으로 삽입할 때 사용합니다.</small>
          </div>
        </div>
        <div class="ag-share-modal-footer">
          <router-link
            :to="`/agent-test/${shareAgent.agentCode}`"
            class="btn btn-outline-primary btn-sm"
          >
            <i class="bi bi-box-arrow-up-right me-1"></i>전체 테스트 페이지 열기
          </router-link>
          <button type="button" class="btn btn-secondary btn-sm" @click="shareAgent = null">닫기</button>
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
// 트랙 #127 (2026-05-29): 소유권 필터 — 'all'/'mine'/'public'/'others'.
// Admin 은 backend AgentsController.cs:52 분기로 다른 사용자 Agent 까지 받으므로
// 화면 혼잡 방지용 관점 전환 select.
const ownerFilter = ref<'all' | 'mine' | 'public' | 'others'>('all')
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

  // 트랙 #127: 소유권 필터 적용.
  if (ownerFilter.value !== 'all') {
    result = result.filter(agent => {
      const mine = isMyAgent(agent)
      if (ownerFilter.value === 'mine') return mine
      if (ownerFilter.value === 'public') return !!agent.isPublic
      if (ownerFilter.value === 'others') return !mine
      return true
    })
  }

  return result
})

const showEmpty = computed(() =>
  filteredAgents.value.length === 0 &&
  (searchText.value || serviceFilter.value || ownerFilter.value !== 'all')
)

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

// 트랙 #127 (2026-05-29): 카드 좌상단 ribbon 라벨/스타일.
// - 본인 작성 + Public: "내 Agent · Public" (mine primary + public success 혼합)
// - 본인 작성 비공개: "내 Agent" (primary)
// - 타인 작성 Public: "Public" (success)
// - 타인 작성 비공개: "타인" (secondary, Admin 한정 노출 케이스)
const getRibbonLabel = (agent: AgentDto): string => {
  const mine = isMyAgent(agent)
  if (mine && agent.isPublic) return '내 Agent · Public'
  if (mine) return '내 Agent'
  if (agent.isPublic) return 'Public'
  return '타인'
}

// 트랙 #133 (2026-05-29): 공유 modal — 새 탭 진입 시 sessionStorage per-tab
// 격리로 토큰 부재 결함 회피. 현재 화면에서 공유 URL/QR/iframe 임베드 즉시 노출.
const shareAgent = ref<AgentDto | null>(null)
const shareUrl = computed(() =>
  shareAgent.value ? `${window.location.origin}/chatbot/${shareAgent.value.agentCode}` : ''
)
const embedUrl = computed(() =>
  shareAgent.value
    ? `<iframe src="${window.location.origin}/embed/${shareAgent.value.agentCode}" width="400" height="600" frameborder="0"></iframe>`
    : ''
)
const openShareModal = (agent: AgentDto) => {
  shareAgent.value = agent
}
// 트랙 #133b (2026-05-29): 운영 URL 이 HTTP (192.168.10.39:64005) 라 navigator.clipboard
// 가 secure context 제약으로 동작 안 함. document.execCommand('copy') fallback +
// 최종 실패 시 input 자동 선택 안내.
const copyToClipboard = async (text: string, successMessage: string): Promise<void> => {
  // 1차: 현대 API — secure context (HTTPS/localhost) 에서만 동작
  if (typeof navigator !== 'undefined' && navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text)
      alert(successMessage)
      return
    } catch {
      // fallback 으로 진행
    }
  }
  // 2차: 레거시 execCommand — HTTP 환경에서도 동작 (deprecated 지만 광범위 지원)
  try {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    textarea.setAttribute('readonly', '')
    document.body.appendChild(textarea)
    textarea.select()
    textarea.setSelectionRange(0, text.length)
    const ok = document.execCommand('copy')
    document.body.removeChild(textarea)
    if (ok) {
      alert(successMessage)
      return
    }
  } catch {
    // 최종 fallback
  }
  // 3차: 사용자에게 수동 복사 안내
  alert(`자동 복사에 실패했습니다. 아래 텍스트를 직접 선택해 복사해 주세요:\n\n${text}`)
}

const copyShareUrl = () => copyToClipboard(shareUrl.value, '공유 URL 이 복사되었습니다.')
const copyEmbedUrl = () => copyToClipboard(embedUrl.value, 'iframe 임베드 코드가 복사되었습니다.')

const getRibbonClass = (agent: AgentDto): string => {
  const mine = isMyAgent(agent)
  if (mine && agent.isPublic) return 'ag-ribbon-mine-public'
  if (mine) return 'ag-ribbon-mine'
  if (agent.isPublic) return 'ag-ribbon-public'
  return 'ag-ribbon-others'
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

/* 트랙 #127 (2026-05-29): 카드 좌상단 ribbon 소유권/공개 라벨 색상. */
.ag-card-ribbon { color: #ffffff; padding: 2px 8px; font-size: 0.75rem; font-weight: 600; border-radius: 0 0 6px 0; }
.ag-card-ribbon.ag-ribbon-mine         { background-color: #4F46E5; }  /* primary indigo — 본인 */
.ag-card-ribbon.ag-ribbon-public       { background-color: #198754; }  /* success green — 공개 */
.ag-card-ribbon.ag-ribbon-mine-public  { background: linear-gradient(90deg, #4F46E5 0%, #198754 100%); }  /* 혼합 */
.ag-card-ribbon.ag-ribbon-others       { background-color: #6c757d; }  /* secondary gray — 타인(Admin only) */

/* 트랙 #133 (2026-05-29): 공유 modal */
.ag-share-modal-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5);
  z-index: 1050; display: flex; align-items: center; justify-content: center;
  animation: fadeIn 0.15s ease;
}
.ag-share-modal {
  background: #ffffff; border-radius: 12px; width: 540px; max-width: 92vw;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
.ag-share-modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem 1.25rem; border-bottom: 1px solid #e5e7eb;
}
.ag-share-modal-body { padding: 1.25rem; display: flex; flex-direction: column; gap: 1.25rem; }
.ag-share-modal-footer {
  display: flex; justify-content: space-between; gap: 0.5rem;
  padding: 0.75rem 1.25rem; border-top: 1px solid #e5e7eb; background: #f9fafb;
}
.ag-share-section { display: flex; flex-direction: column; gap: 0.35rem; }
.ag-share-url-row { display: flex; gap: 0.5rem; align-items: stretch; }
.ag-share-url-row input { flex: 1; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; }
.ag-share-qr { display: flex; gap: 1rem; align-items: center; }
.ag-share-qr img { border: 1px solid #e5e7eb; border-radius: 8px; padding: 4px; background: #fff; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
