<template>
  <div class="test-page">
    <!-- 상단 바 -->
    <header class="test-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <i class="bi bi-arrow-left"></i> 빌더로 돌아가기
        </button>
        <div class="divider"></div>
        <div v-if="agent" class="agent-badge" :style="{ backgroundColor: agent.colorCode || '#0d6efd' }">
          <i :class="agent.iconClass || 'bi bi-robot'"></i>
          <span>{{ agent.agentName }}</span>
        </div>
      </div>
      <div class="header-right">
        <span class="model-badge" v-if="agent?.defaultModel">{{ agent.defaultModel }}</span>
        <button class="btn-outline" @click="showDebug = !showDebug">
          <i class="bi bi-bug"></i> 디버그 {{ showDebug ? '숨기기' : '보기' }}
        </button>
        <button class="btn-outline" @click="clearChat">
          <i class="bi bi-trash3"></i> 초기화
        </button>
      </div>
    </header>

    <div class="test-body">
      <!-- 좌측: 에이전트 정보 패널 -->
      <aside class="info-panel">
        <div v-if="loading" class="panel-loading">
          <div class="spinner"></div>
        </div>
        <template v-else-if="agent">
          <div class="panel-section">
            <h3>기본 정보</h3>
            <div class="info-row"><span>이름</span><b>{{ agent.agentName }}</b></div>
            <div class="info-row"><span>모델</span><b>{{ agent.defaultModel || '기본' }}</b></div>
            <div class="info-row"><span>서비스</span><b>{{ agent.serviceName || '-' }}</b></div>
            <div class="info-row"><span>RAG</span><b>{{ agent.enableRag ? '✅ 활성' : '❌ 비활성' }}</b></div>
            <div class="info-row"><span>공개 채팅</span><b>{{ agent.allowGuestChat ? '✅ 허용' : '❌ 비허용' }}</b></div>
          </div>
          <div class="panel-section" v-if="agent.systemPrompt">
            <h3>시스템 프롬프트</h3>
            <div class="prompt-preview">{{ agent.systemPrompt }}</div>
          </div>
          <div class="panel-section" v-if="agent.allowGuestChat">
            <h3>공유 링크</h3>
            <div class="share-link-box">
              <div class="share-link-row">
                <label>챗봇 URL</label>
                <div class="link-copy">
                  <input :value="chatbotUrl" readonly class="link-input" />
                  <button class="copy-btn" @click="copyUrl(chatbotUrl)"><i class="bi bi-copy"></i></button>
                </div>
              </div>
              <div class="share-link-row">
                <label>임베드 URL</label>
                <div class="link-copy">
                  <input :value="embedUrl" readonly class="link-input" />
                  <button class="copy-btn" @click="copyUrl(embedUrl)"><i class="bi bi-copy"></i></button>
                </div>
              </div>
              <div class="share-link-row" style="align-items:center;">
                <label>QR 코드</label>
                <div style="display:flex;flex-direction:column;gap:6px;align-items:flex-start">
                  <img :src="`/api/agents/public/${code}/qr?size=160`"
                    alt="QR" width="80" height="80"
                    style="border:1px solid #e2e8f0;border-radius:6px;padding:3px;background:white;" />
                  <a :href="`/api/agents/public/${code}/qr?size=400`"
                    download="qr-code.png"
                    style="font-size:11px;color:#3b82f6;">
                    <i class="bi bi-download"></i> 다운로드
                  </a>
                </div>
              </div>
            </div>
          </div>
          <div class="panel-section" v-else>
            <h3>공유 링크</h3>
            <div class="share-disabled">
              <i class="bi bi-lock"></i>
              <p>게스트 채팅이 비활성화되어 있습니다.<br>에이전트 설정에서 "게스트 채팅 허용"을 켜주세요.</p>
            </div>
          </div>
        </template>
      </aside>

      <!-- 중앙: 채팅 영역 -->
      <section class="chat-section">
        <div v-if="loading" class="chat-loading">
          <div class="spinner"></div><p>에이전트 로딩 중...</p>
        </div>
        <div v-else-if="notFound" class="chat-error">
          <i class="bi bi-exclamation-triangle" style="font-size:40px;color:#ef4444"></i>
          <p>에이전트를 찾을 수 없습니다.</p>
        </div>
        <template v-else>
          <div class="chat-body" ref="chatBody">
            <div v-if="messages.length === 0" class="empty-chat">
              <i class="bi bi-chat-dots" style="font-size:48px;color:#cbd5e1"></i>
              <p>테스트 메시지를 입력하세요</p>
            </div>
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="msg-row"
              :class="msg.role === 'user' ? 'user-row' : 'bot-row'"
            >
              <div v-if="msg.role === 'assistant'" class="bot-avatar" :style="{ backgroundColor: agent?.colorCode || '#0d6efd' }">
                <i :class="agent?.iconClass || 'bi bi-robot'"></i>
              </div>
              <div class="msg-bubble" :class="msg.role === 'user' ? 'user-bubble' : 'bot-bubble'">
                <div v-html="msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content"></div>
                <div v-if="msg.meta" class="msg-meta">
                  {{ msg.meta.model }} · {{ msg.meta.tokens }}토큰 · {{ msg.meta.ms }}ms
                </div>
              </div>
            </div>
            <div v-if="thinking" class="msg-row bot-row">
              <div class="bot-avatar" :style="{ backgroundColor: agent?.colorCode || '#0d6efd' }">
                <i :class="agent?.iconClass || 'bi bi-robot'"></i>
              </div>
              <div class="msg-bubble bot-bubble typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>

          <div class="chat-input-area">
            <textarea
              v-model="inputMessage"
              placeholder="테스트할 메시지를 입력하세요... (Shift+Enter: 줄바꿈)"
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResize"
              :disabled="thinking"
              ref="inputRef"
              rows="2"
            ></textarea>
            <button class="send-btn" @click="sendMessage" :disabled="!inputMessage.trim() || thinking"
              :style="{ backgroundColor: agent?.colorCode || '#0d6efd' }">
              <i class="bi bi-send-fill"></i>
            </button>
          </div>
        </template>
      </section>

      <!-- 우측: 디버그 패널 -->
      <aside class="debug-panel" v-if="showDebug">
        <h3><i class="bi bi-bug"></i> 디버그</h3>
        <div class="debug-section">
          <h4>마지막 요청</h4>
          <pre class="debug-pre">{{ debugRequest || '아직 요청 없음' }}</pre>
        </div>
        <div class="debug-section">
          <h4>마지막 응답</h4>
          <pre class="debug-pre">{{ debugResponse || '아직 응답 없음' }}</pre>
        </div>
        <div class="debug-section">
          <h4>통계</h4>
          <div class="stat-row"><span>총 메시지</span><b>{{ messages.length }}</b></div>
          <div class="stat-row"><span>총 토큰</span><b>{{ totalTokens }}</b></div>
          <div class="stat-row"><span>평균 응답시간</span><b>{{ avgMs }}ms</b></div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'

interface AgentInfo {
  agentId: number
  agentName: string
  agentCode: string
  description?: string
  iconClass?: string
  colorCode?: string
  systemPrompt?: string
  defaultModel?: string
  serviceName?: string
  enableRag: boolean
  allowGuestChat: boolean
  welcomeMessage?: string
  placeholderText?: string
}
interface Message {
  role: 'user' | 'assistant'
  content: string
  meta?: { model: string; tokens: number; ms: number }
}

const route = useRoute()
const router = useRouter()
const code = computed(() => route.params.code as string)

const agent = ref<AgentInfo | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(true)
const notFound = ref(false)
const thinking = ref(false)
const showDebug = ref(false)
const chatBody = ref<HTMLElement | null>(null)
const debugRequest = ref('')
const debugResponse = ref('')
const responseTimes = ref<number[]>([])
const totalTokens = ref(0)
const avgMs = computed(() =>
  responseTimes.value.length ? Math.round(responseTimes.value.reduce((a, b) => a + b, 0) / responseTimes.value.length) : 0
)

const origin = window.location.origin
const chatbotUrl = computed(() => `${origin}/chatbot/${code.value}`)
const embedUrl   = computed(() => `${origin}/embed/${code.value}`)

onMounted(async () => {
  await loadAgent()
})

async function loadAgent() {
  try {
    const res = await api.get(`/agents/bycode/${code.value}`)
    agent.value = res.data
    if (agent.value?.welcomeMessage) {
      messages.value.push({ role: 'assistant', content: agent.value.welcomeMessage })
    }
  } catch (e: any) {
    notFound.value = e.response?.status === 404
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  const text = inputMessage.value.trim()
  if (!text || thinking.value) return

  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  thinking.value = true
  await nextTick(); scrollToBottom()

  const history = messages.value.slice(-20).map(m => ({ role: m.role, content: m.content }))
  const reqPayload = { message: text, messages: history }
  debugRequest.value = JSON.stringify(reqPayload, null, 2)

  const startMs = Date.now()
  try {
    const res = await api.post(`/agents/public/${code.value}/chat`, reqPayload)
    const elapsed = Date.now() - startMs
    responseTimes.value.push(elapsed)
    totalTokens.value += res.data.tokensUsed || 0

    messages.value.push({
      role: 'assistant',
      content: res.data.content,
      meta: { model: res.data.model || '-', tokens: res.data.tokensUsed || 0, ms: elapsed }
    })
    debugResponse.value = JSON.stringify(res.data, null, 2)
  } catch (e: any) {
    messages.value.push({ role: 'assistant', content: '⚠️ 오류: ' + (e.response?.data?.message || e.message) })
    debugResponse.value = JSON.stringify(e.response?.data || e.message, null, 2)
  } finally {
    thinking.value = false
    await nextTick(); scrollToBottom()
  }
}

function clearChat() {
  messages.value = []
  debugRequest.value = ''
  debugResponse.value = ''
  responseTimes.value = []
  totalTokens.value = 0
  if (agent.value?.welcomeMessage)
    messages.value.push({ role: 'assistant', content: agent.value.welcomeMessage })
}

function goBack() {
  router.push('/agents/builder')
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

async function copyUrl(url: string) {
  await navigator.clipboard.writeText(url)
  alert('복사되었습니다!')
}

function renderMarkdown(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.test-page {
  display: flex; flex-direction: column; height: 100vh;
  font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  background: #f1f5f9; font-size: 13px;
}

/* 헤더 */
.test-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; background: white; border-bottom: 1px solid #e2e8f0;
  gap: 12px; flex-shrink: 0;
}
.header-left, .header-right { display: flex; align-items: center; gap: 10px; }
.back-btn {
  background: none; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 6px 12px; cursor: pointer; font-size: 13px; color: #475569;
  display: flex; align-items: center; gap: 6px;
}
.back-btn:hover { background: #f8fafc; }
.divider { width: 1px; height: 24px; background: #e2e8f0; }
.agent-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 20px; color: white;
  font-weight: 700; font-size: 13px;
}
.model-badge {
  background: #f1f5f9; border: 1px solid #e2e8f0;
  border-radius: 20px; padding: 3px 10px; font-size: 12px; color: #475569;
}
.btn-outline {
  background: none; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 6px 12px; cursor: pointer; font-size: 12px; color: #475569;
  display: flex; align-items: center; gap: 5px; transition: background .15s;
}
.btn-outline:hover { background: #f8fafc; }

/* 레이아웃 */
.test-body {
  display: flex; flex: 1; overflow: hidden; gap: 0;
}

/* 좌측 패널 */
.info-panel {
  width: 280px; min-width: 220px; flex-shrink: 0;
  background: white; border-right: 1px solid #e2e8f0;
  overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 16px;
}
.panel-section h3 {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: .05em;
  margin-bottom: 10px;
}
.info-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 0; border-bottom: 1px solid #f1f5f9; font-size: 12px;
}
.info-row span { color: #64748b; }
.prompt-preview {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 8px 10px; font-size: 11.5px; color: #475569;
  max-height: 140px; overflow-y: auto; line-height: 1.6;
  white-space: pre-wrap; word-break: break-word;
}
.share-link-box { display: flex; flex-direction: column; gap: 10px; }
.share-link-row { display: flex; flex-direction: column; gap: 4px; }
.share-link-row label { font-size: 11px; color: #64748b; }
.link-copy { display: flex; gap: 4px; }
.link-input {
  flex: 1; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 5px 8px; font-size: 11px; color: #475569; background: #f8fafc;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.copy-btn {
  background: #3b82f6; color: white; border: none; border-radius: 6px;
  width: 28px; height: 28px; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
}
.share-disabled {
  background: #fef9ec; border: 1px solid #fde68a; border-radius: 8px;
  padding: 12px; text-align: center; color: #92400e; font-size: 12px;
}
.share-disabled i { font-size: 20px; margin-bottom: 6px; display: block; }
.share-disabled p { line-height: 1.5; }

/* 채팅 영역 */
.chat-section {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
  background: #f8fafc;
}
.chat-body {
  flex: 1; overflow-y: auto; padding: 16px;
  display: flex; flex-direction: column; gap: 12px;
}
.empty-chat {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 10px;
  color: #94a3b8; margin-top: 60px;
}
.msg-row { display: flex; align-items: flex-end; gap: 8px; }
.user-row { flex-direction: row-reverse; }
.bot-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 13px; flex-shrink: 0;
}
.msg-bubble {
  max-width: 70%; padding: 9px 13px; border-radius: 16px;
  line-height: 1.55; word-break: break-word; font-size: 13px;
}
.user-bubble { background: #3b82f6; color: white; border-bottom-right-radius: 3px; }
.bot-bubble  { background: white; border: 1px solid #e2e8f0; border-bottom-left-radius: 3px; }
.msg-meta { font-size: 10px; color: #94a3b8; margin-top: 5px; }
.bot-bubble :deep(code) {
  background: rgba(0,0,0,.06); padding: 1px 4px; border-radius: 3px;
}
.typing { display: flex; gap: 4px; align-items: center; }
.typing span {
  width: 6px; height: 6px; background: #94a3b8; border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce {
  0%,80%,100% { transform: translateY(0); }
  40%          { transform: translateY(-5px); }
}

/* 입력창 */
.chat-input-area {
  display: flex; gap: 8px; align-items: flex-end;
  padding: 10px 16px; background: white; border-top: 1px solid #e2e8f0;
}
.chat-input-area textarea {
  flex: 1; border: 1.5px solid #e2e8f0; border-radius: 10px;
  padding: 9px 12px; font-size: 13px; resize: none; outline: none;
  font-family: inherit; line-height: 1.5; min-height: 44px; max-height: 160px;
  transition: border-color .2s;
}
.chat-input-area textarea:focus { border-color: #3b82f6; }
.send-btn {
  width: 40px; height: 40px; border-radius: 10px; border: none;
  color: white; cursor: pointer; display: flex; align-items: center; justify-content: center;
  font-size: 15px; flex-shrink: 0; transition: opacity .2s;
}
.send-btn:disabled { opacity: .4; cursor: default; }

/* 디버그 패널 */
.debug-panel {
  width: 280px; min-width: 220px; flex-shrink: 0;
  background: #0f172a; border-left: 1px solid #1e293b;
  overflow-y: auto; padding: 14px; color: #e2e8f0;
  display: flex; flex-direction: column; gap: 14px;
}
.debug-panel h3 {
  font-size: 13px; font-weight: 700; color: #94a3b8;
  display: flex; align-items: center; gap: 6px;
}
.debug-section h4 { font-size: 11px; color: #64748b; margin-bottom: 6px; }
.debug-pre {
  background: #1e293b; border-radius: 6px; padding: 8px;
  font-size: 10.5px; white-space: pre-wrap; word-break: break-all;
  color: #7dd3fc; max-height: 200px; overflow-y: auto;
}
.stat-row {
  display: flex; justify-content: space-between;
  padding: 4px 0; border-bottom: 1px solid #1e293b; font-size: 12px;
}
.stat-row span { color: #64748b; }

/* 로딩 */
.panel-loading, .chat-loading, .chat-error {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; height: 100%; color: #94a3b8;
}
.spinner {
  width: 30px; height: 30px;
  border: 3px solid #e2e8f0; border-top-color: #3b82f6;
  border-radius: 50%; animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
