<template>
  <div class="embed-chat" :class="[`theme-${theme}`, { minimized: isMinimized }]">
    <!-- 헤더 -->
    <header class="embed-header" :style="{ backgroundColor: agent?.colorCode || '#0d6efd' }">
      <div class="header-left">
        <i :class="agent?.iconClass || 'bi bi-robot'" class="header-icon"></i>
        <span class="header-title">{{ agent?.agentName || '...' }}</span>
      </div>
      <div class="header-actions">
        <button class="icon-btn" @click="clearChat" title="초기화">
          <i class="bi bi-arrow-counterclockwise"></i>
        </button>
        <button class="icon-btn" @click="toggleMinimize" :title="isMinimized ? '펼치기' : '최소화'">
          <i :class="isMinimized ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        </button>
      </div>
    </header>

    <!-- 채팅 본문 (최소화 시 숨김) -->
    <template v-if="!isMinimized">
      <div v-if="loading" class="embed-loading">
        <div class="mini-spinner"></div>
      </div>
      <div v-else-if="notFound" class="embed-error">
        <i class="bi bi-exclamation-circle"></i>
        <span>챗봇을 찾을 수 없습니다</span>
      </div>
      <template v-else>
        <!-- 메시지 목록 -->
        <main class="embed-body" ref="chatBody">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="msg-row"
            :class="msg.role === 'user' ? 'user-row' : 'bot-row'"
          >
            <div class="msg-bubble" :class="msg.role === 'user' ? 'user-bubble' : 'bot-bubble'"
              :style="msg.role === 'user' ? { backgroundColor: agent?.colorCode || '#3b82f6' } : {}">
              <div v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)"></div>
              <div v-else>{{ msg.content }}</div>
            </div>
          </div>

          <!-- 타이핑 표시 -->
          <div v-if="thinking" class="msg-row bot-row">
            <div class="msg-bubble bot-bubble typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        </main>

        <!-- 입력창 -->
        <footer class="embed-footer">
          <input
            v-model="inputMessage"
            :placeholder="agent?.placeholderText || '메시지 입력...'"
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="thinking"
            class="embed-input"
          />
          <button
            class="embed-send"
            @click="sendMessage"
            :disabled="!inputMessage.trim() || thinking"
            :style="{ backgroundColor: agent?.colorCode || '#0d6efd' }"
          >
            <i class="bi bi-send-fill"></i>
          </button>
        </footer>
      </template>
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
  iconClass?: string
  colorCode?: string
  welcomeMessage?: string
  placeholderText?: string
  chatTheme?: string
}
interface Message { role: 'user' | 'assistant'; content: string }

const route = useRoute()
const code = computed(() => route.params.code as string)

const agent = ref<AgentInfo | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(true)
const notFound = ref(false)
const thinking = ref(false)
const isMinimized = ref(false)
const chatBody = ref<HTMLElement | null>(null)
const theme = computed(() => agent.value?.chatTheme || 'light')
const apiBase = window.location.origin + '/api'

onMounted(async () => {
  // URL 쿼리로 테마 오버라이드 가능: ?theme=dark
  const queryTheme = new URLSearchParams(window.location.search).get('theme')
  await loadAgent(queryTheme)

  // 부모 페이지에 준비 완료 알림
  window.parent.postMessage({ type: 'agent-embed-ready', code: code.value }, '*')

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

async function loadAgent(themeOverride?: string | null) {
  try {
    const res = await axios.get(`${apiBase}/agents/public/${code.value}/info`)
    agent.value = res.data
    if (themeOverride) agent.value!.chatTheme = themeOverride
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

  const history = messages.value.slice(-16).map(m => ({ role: m.role, content: m.content }))
  try {
    const res = await axios.post(`${apiBase}/agents/public/${code.value}/chat`, {
      message: text, messages: history
    })
    messages.value.push({ role: 'assistant', content: res.data.content })
    // 부모 페이지에 새 메시지 이벤트 전달
    window.parent.postMessage({ type: 'agent-message', role: 'assistant', content: res.data.content }, '*')
  } catch {
    messages.value.push({ role: 'assistant', content: '⚠️ 오류가 발생했습니다. 다시 시도해 주세요.' })
  } finally {
    thinking.value = false
    await nextTick(); scrollToBottom()
  }
}

function clearChat() {
  messages.value = []
  if (agent.value?.welcomeMessage)
    messages.value.push({ role: 'assistant', content: agent.value.welcomeMessage })
}

function toggleMinimize() {
  isMinimized.value = !isMinimized.value
  window.parent.postMessage({ type: 'agent-embed-toggle', minimized: isMinimized.value }, '*')
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

function renderMarkdown(text: string): string {
  // [BUTTONS: ...] 를 처리 전에 플레이스홀더로 치환
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
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.embed-chat {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100dvh;
  font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  font-size: 13px;
  background: #f8fafc;
  color: #1e293b;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0,0,0,.12);
}
.embed-chat.minimized { height: auto; }

/* 테마 다크 */
.theme-dark { background: #1e293b; color: #e2e8f0; }
.theme-dark .embed-footer { background: #0f172a; border-color: #334155; }
.theme-dark .embed-input  { background: #1e293b; color: #e2e8f0; border-color: #334155; }
.theme-dark .bot-bubble   { background: #334155; color: #e2e8f0; }

/* 헤더 */
.embed-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px;
  color: white;
  flex-shrink: 0;
}
.header-left  { display: flex; align-items: center; gap: 8px; }
.header-icon  { font-size: 18px; }
.header-title { font-weight: 700; font-size: 14px; }
.header-actions { display: flex; gap: 4px; }
.icon-btn {
  background: rgba(255,255,255,.2); border: none; color: white;
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; transition: background .15s;
}
.icon-btn:hover { background: rgba(255,255,255,.35); }

/* 본문 */
.embed-body {
  flex: 1; overflow-y: auto; padding: 12px 10px;
  display: flex; flex-direction: column; gap: 10px;
}

.msg-row { display: flex; }
.user-row { justify-content: flex-end; }
.bot-row  { justify-content: flex-start; }

.msg-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 14px;
  line-height: 1.55;
  word-break: break-word;
}
.user-bubble {
  color: white;
  border-bottom-right-radius: 3px;
}
.bot-bubble {
  background: white;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 3px;
}
.bot-bubble :deep(code) {
  background: rgba(0,0,0,.08); padding: 1px 4px; border-radius: 3px; font-size: 11px;
}
.bot-bubble :deep(.quick-reply-container) {
  display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
}
.bot-bubble :deep(.quick-reply-btn) {
  padding: 4px 12px;
  border: 1.5px solid #6366f1;
  border-radius: 16px;
  background: #fff;
  color: #6366f1;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.bot-bubble :deep(.quick-reply-btn:hover) {
  background: #6366f1;
  color: #fff;
}

/* 타이핑 애니메이션 */
.typing { display: flex; gap: 4px; align-items: center; padding: 10px 14px; }
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

/* 푸터 */
.embed-footer {
  display: flex; gap: 6px; align-items: center;
  padding: 8px 10px;
  background: white;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.embed-input {
  flex: 1; border: 1.5px solid #e2e8f0; border-radius: 8px;
  padding: 7px 10px; font-size: 13px; outline: none; font-family: inherit;
  transition: border-color .2s;
}
.embed-input:focus { border-color: #3b82f6; }
.embed-send {
  width: 34px; height: 34px; border-radius: 8px; border: none;
  color: white; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; transition: opacity .2s;
}
.embed-send:disabled { opacity: .4; cursor: default; }

/* 로딩 / 에러 */
.embed-loading, .embed-error {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  color: #94a3b8; font-size: 13px;
}
.mini-spinner {
  width: 22px; height: 22px;
  border: 3px solid #e2e8f0; border-top-color: #3b82f6;
  border-radius: 50%; animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
