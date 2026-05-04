<template>
  <div class="public-chat-page" :class="[`theme-${theme}`]">
    <!-- 로딩 -->
    <div v-if="loading" class="loading-screen">
      <div class="spinner"></div>
      <p>불러오는 중...</p>
    </div>

    <!-- 404 -->
    <div v-else-if="notFound" class="not-found-screen">
      <div class="not-found-icon">🤖</div>
      <h2>챗봇을 찾을 수 없습니다</h2>
      <p>존재하지 않거나 비공개 챗봇입니다.</p>
    </div>

    <!-- 챗봇 UI -->
    <template v-else-if="agent">
      <!-- 헤더 -->
      <header class="chat-header">
        <div class="agent-info">
          <div class="agent-icon" :style="{ backgroundColor: agent.colorCode || '#0d6efd' }">
            <i :class="agent.iconClass || 'bi bi-robot'"></i>
          </div>
          <div class="agent-meta">
            <h1>{{ agent.agentName }}</h1>
            <p v-if="agent.description">{{ agent.description }}</p>
          </div>
        </div>
        <div class="header-actions">
          <button class="btn-icon" @click="clearChat" title="대화 초기화">
            <i class="bi bi-arrow-counterclockwise"></i>
          </button>
        </div>
      </header>

      <!-- 메시지 영역 -->
      <main class="chat-body" ref="chatBody">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message-row"
          :class="msg.role === 'user' ? 'user-row' : 'bot-row'"
        >
          <div v-if="msg.role === 'assistant'" class="bot-avatar" :style="{ backgroundColor: agent.colorCode || '#0d6efd' }">
            <i :class="agent.iconClass || 'bi bi-robot'"></i>
          </div>
          <div class="message-bubble" :class="msg.role === 'user' ? 'user-bubble' : 'bot-bubble'">
            <div v-if="msg.role === 'assistant'" class="bubble-content" v-html="renderMarkdown(msg.content)"></div>
            <div v-else class="bubble-content">{{ msg.content }}</div>
          </div>
        </div>

        <!-- 응답 대기 중 -->
        <div v-if="thinking" class="message-row bot-row">
          <div class="bot-avatar" :style="{ backgroundColor: agent.colorCode || '#0d6efd' }">
            <i :class="agent.iconClass || 'bi bi-robot'"></i>
          </div>
          <div class="message-bubble bot-bubble thinking">
            <span></span><span></span><span></span>
          </div>
        </div>
      </main>

      <!-- 입력 영역 -->
      <footer class="chat-footer">
        <div class="input-area">
          <textarea
            v-model="inputMessage"
            :placeholder="agent.placeholderText || '메시지를 입력하세요...'"
            rows="1"
            @keydown.enter.exact.prevent="sendMessage"
            @input="autoResize"
            ref="inputRef"
            :disabled="thinking"
          ></textarea>
          <button class="send-btn" @click="sendMessage" :disabled="!inputMessage.trim() || thinking" :style="{ backgroundColor: agent.colorCode || '#0d6efd' }">
            <i class="bi bi-send-fill"></i>
          </button>
        </div>
        <p class="footer-note">Powered by AI Agent Platform</p>
      </footer>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

interface AgentInfo {
  agentId: number
  agentName: string
  agentCode: string
  description?: string
  iconClass?: string
  colorCode?: string
  welcomeMessage?: string
  placeholderText?: string
  chatTheme?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const route = useRoute()
const code = computed(() => route.params.code as string)

const agent = ref<AgentInfo | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(true)
const notFound = ref(false)
const thinking = ref(false)
const chatBody = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

const theme = computed(() => agent.value?.chatTheme || 'light')

// 기본 API base URL
const apiBase = window.location.origin + '/api'

onMounted(async () => {
  await loadAgent()

  // Quick reply 버튼 클릭 이벤트 위임
  if (chatBody.value) {
    chatBody.value.addEventListener('click', (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('[data-quick-reply]') as HTMLElement | null
      if (!target) return
      const text = target.getAttribute('data-quick-reply')
      if (text && !thinking.value) {
        inputMessage.value = text
        sendMessage()
      }
    })
  }
})

async function loadAgent() {
  try {
    const res = await axios.get(`${apiBase}/agents/public/${code.value}/info`)
    agent.value = res.data
    // 환영 메시지 표시
    if (agent.value?.welcomeMessage) {
      messages.value.push({ role: 'assistant', content: agent.value.welcomeMessage })
    }
  } catch (e: any) {
    if (e.response?.status === 404) notFound.value = true
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
  await nextTick()
  scrollToBottom()

  // 대화 이력 (최근 10턴)
  const history = messages.value.slice(-20).map(m => ({ role: m.role, content: m.content }))

  try {
    const res = await axios.post(`${apiBase}/agents/public/${code.value}/chat`, {
      message: text,
      messages: history
    })
    messages.value.push({ role: 'assistant', content: res.data.content })
  } catch {
    messages.value.push({ role: 'assistant', content: '⚠️ 응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.' })
  } finally {
    thinking.value = false
    await nextTick()
    scrollToBottom()
  }
}

function clearChat() {
  messages.value = []
  if (agent.value?.welcomeMessage) {
    messages.value.push({ role: 'assistant', content: agent.value.welcomeMessage })
  }
}

function scrollToBottom() {
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function renderMarkdown(text: string): string {
  // [BUTTONS: ...] 를 marked 처리 전에 플레이스홀더로 치환
  const placeholders: string[] = []
  let processed = text.replace(/\[BUTTONS:\s*([^\]]+)\]/g, (_match, buttonsStr: string) => {
    const btns = buttonsStr.split('|').map((b: string) => b.trim()).filter(Boolean)
      .map((btn: string) => {
        const escaped = btn.replace(/"/g, '&quot;')
        return `<button class="quick-reply-btn" data-quick-reply="${escaped}">${escaped}</button>`
      }).join('')
    const placeholder = `QRPH${placeholders.length}XEND`
    placeholders.push(`<div class="quick-reply-container">${btns}</div>`)
    return placeholder
  })

  let html = processed
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')

  // 플레이스홀더 복원
  placeholders.forEach((btnHtml, index) => {
    html = html.replace(`QRPH${index}XEND`, btnHtml)
  })
  return html
}
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.public-chat-page {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  background: #f1f5f9;
  color: #1e293b;
}

/* ── 테마 ── */
.theme-dark {
  background: #0f172a;
  color: #e2e8f0;
}
.theme-dark .chat-header  { background: #1e293b; border-color: #334155; }
.theme-dark .chat-footer  { background: #1e293b; border-color: #334155; }
.theme-dark .bot-bubble   { background: #1e293b; color: #e2e8f0; border-color: #334155; }
.theme-dark .input-area textarea { background: #0f172a; color: #e2e8f0; border-color: #334155; }

/* ── 헤더 ── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.agent-info { display: flex; align-items: center; gap: 12px; }
.agent-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 20px; flex-shrink: 0;
}
.agent-meta h1 { font-size: 16px; font-weight: 700; }
.agent-meta p  { font-size: 12px; color: #64748b; margin-top: 2px; }
.header-actions { display: flex; gap: 8px; }
.btn-icon {
  background: none; border: none; cursor: pointer;
  padding: 6px; border-radius: 8px; font-size: 18px; color: #64748b;
  transition: background .15s;
}
.btn-icon:hover { background: #f1f5f9; }

/* ── 메시지 영역 ── */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message-row { display: flex; align-items: flex-end; gap: 8px; }
.user-row    { flex-direction: row-reverse; }

.bot-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 14px; flex-shrink: 0;
}

.message-bubble {
  max-width: 72%;
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.user-bubble {
  background: #3b82f6;
  color: white;
  border-bottom-right-radius: 4px;
}
.bot-bubble {
  background: white;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
}
.bubble-content :deep(code) {
  background: rgba(0,0,0,.08);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}
.bubble-content :deep(.quick-reply-container) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.bubble-content :deep(.quick-reply-btn) {
  padding: 6px 14px;
  border: 1.5px solid #6366f1;
  border-radius: 20px;
  background: #fff;
  color: #6366f1;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.bubble-content :deep(.quick-reply-btn:hover) {
  background: #6366f1;
  color: #fff;
}

/* ── 타이핑 점 애니메이션 ── */
.thinking {
  padding: 14px 18px;
  display: flex; gap: 5px; align-items: center;
}
.thinking span {
  width: 7px; height: 7px;
  background: #94a3b8;
  border-radius: 50%;
  animation: bounce 1.2s infinite;
}
.thinking span:nth-child(2) { animation-delay: .2s; }
.thinking span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}

/* ── 푸터 ── */
.chat-footer {
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 12px 16px 8px;
}
.input-area {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.input-area textarea {
  flex: 1;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
  min-height: 42px;
  max-height: 120px;
  transition: border-color .2s;
}
.input-area textarea:focus { border-color: #3b82f6; }
.send-btn {
  width: 42px; height: 42px;
  border-radius: 12px;
  border: none;
  color: white;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  transition: opacity .2s;
}
.send-btn:disabled { opacity: 0.4; cursor: default; }
.footer-note {
  text-align: center;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 6px;
}

/* ── 로딩 / 404 ── */
.loading-screen, .not-found-screen {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
}
.spinner {
  width: 40px; height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.not-found-icon { font-size: 56px; }
.not-found-screen h2 { font-size: 22px; color: #1e293b; }
.not-found-screen p  { color: #64748b; }

@media (max-width: 480px) {
  .message-bubble { max-width: 88%; }
  .agent-meta p   { display: none; }
}
</style>
