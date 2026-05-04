/* =============================================
   멀티 AI 채팅 - multi-chat.js
   ============================================= */

/* ── Service definitions ── */
const MC_SERVICES = {
  chatgpt:     { label: 'ChatGPT',          color: '#00C9FF', icon: 'fas fa-comment-dots',  models: ['gpt-5.2','gpt-5','gpt-5-mini','gpt-5-nano','gpt-5.2-instant','gpt-5.2-thinking','gpt-5.2-pro','gpt-4-turbo','gpt-4o','gpt-4','gpt-3.5-turbo','gpt-4o-mini'] },
  claude:      { label: 'Claude',           color: '#D97706', icon: 'fas fa-robot',          models: ['claude-opus-4','claude-sonnet-4','claude-haiku-3.5','claude-opus-3','claude-sonnet-3.5','claude-haiku-3'] },
  cursor:      { label: 'Cursor',           color: '#8B5CF6', icon: 'fas fa-code',           models: ['cursor-large','cursor-small','cursor-fast'] },
  copilot:     { label: 'Copilot',          color: '#6B7280', icon: 'fab fa-github',         models: ['copilot-gpt-4o','copilot-gpt-4','copilot-claude'] },
  gemini:      { label: 'Gemini',           color: '#3B82F6', icon: 'fab fa-google',         models: ['gemini-2.5-pro','gemini-2.5-flash','gemini-2.0-pro','gemini-2.0-flash','gemini-1.5-pro'] },
  mistral:     { label: 'Mistral',          color: '#F59E0B', icon: 'fas fa-star',           models: ['mistral-large','mistral-medium','mistral-small','mistral-nemo'] },
  dalle:       { label: 'DALL-E 3',         color: '#10B981', icon: 'fas fa-image',          models: ['dall-e-3','dall-e-2'] },
  'gemini-img':{ label: 'Gemini 3 Pro Image', color: '#3B82F6', icon: 'fas fa-image',        models: ['gemini-3-pro-image'] },
  imagen4:     { label: 'Imagen 4',         color: '#059669', icon: 'fas fa-image',          models: ['imagen-4','imagen-3'] },
  'gen4-img':  { label: 'Gen4 Image',       color: '#6D28D9', icon: 'fas fa-image',          models: ['gen4-image'] },
  flux2:       { label: 'Flux 2',           color: '#B45309', icon: 'fas fa-image',          models: ['flux-2-pro','flux-2'] },
  'gen4-video':{ label: 'Gen4 Video',       color: '#DC2626', icon: 'fas fa-video',          models: ['gen4-video'] },
  veo:         { label: 'Veo 3.1',          color: '#7C3AED', icon: 'fas fa-film',           models: ['veo-3.1','veo-3'] },
  'openai-video':{ label: 'OpenAI Video',   color: '#0EA5E9', icon: 'fas fa-clapperboard',   models: ['openai-video-1'] }
};

/* ── Sample AI replies ── */
const MC_REPLIES = [
  `안녕하세요! 무엇을 도와드릴까요? 코드 작성, 문서 요약, 번역, 데이터 분석 등 다양한 작업을 도와드릴 수 있습니다.`,
  `네, 알겠습니다! 요청하신 내용을 처리하겠습니다.\n\n**주요 포인트:**\n- 정확한 정보를 기반으로 답변드립니다\n- 추가 질문이 있으시면 언제든지 말씀해주세요\n- 복잡한 작업도 단계별로 안내해 드립니다`,
  `좋은 질문입니다! 다음과 같이 정리할 수 있습니다:\n\n1. **첫 번째 핵심 사항** - 핵심 내용 요약\n2. **두 번째 핵심 사항** - 추가 세부 정보\n3. **세 번째 핵심 사항** - 실질적 적용 방법\n\n더 자세한 설명이 필요하시면 알려주세요!`,
  `물론이죠! 예시 코드를 제공해 드리겠습니다:\n\n\`\`\`python\ndef hello_world():\n    print("Hello, AI World!")\n    return True\n\nhello_world()\n\`\`\`\n\n이 코드는 간단한 예시입니다. 실제 사용 사례에 맞게 수정해 드릴 수 있습니다.`,
  `분석 결과를 공유드립니다:\n\n| 항목 | 값 | 비고 |\n|------|-----|------|\n| 정확도 | 96.5% | 높음 |\n| 처리 속도 | 1.2초 | 빠름 |\n| 메모리 | 256MB | 적당 |\n\n> 전반적으로 성능이 우수합니다. 최적화를 통해 더 개선할 수 있습니다.`
];

/* ── State ── */
let mcState = {
  activeChatId: null,
  chats: [],          // [{ id, title, preview, svc, time, messages }]
  currentSvc: 'chatgpt',
  settings: {
    model:       'gpt-5.2',
    lang:        'auto',
    temperature: 0.7,
    maxTokens:   4096,
    sysPrompt:   '',
    streaming:   false,
    saveHistory: true,
    webSearch:   false,
    rag:         false
  },
  isStreaming: false,
  streamTimer: null
};

/* ─────────────────────────────────────────
   INIT
───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initDate();
  setupServiceGrid();
  setupInput();
  setupButtons();
  setupModal();

  // Create initial chat
  createNewChat();
});

function initDate() {
  const d = new Date();
  const label = `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일`;
  document.querySelectorAll('.mc-date-label').forEach(el => el.textContent = label);
}

/* ─────────────────────────────────────────
   CHAT MANAGEMENT
───────────────────────────────────────── */
function createNewChat() {
  const id = 'chat_' + Date.now();
  const svc = mcState.currentSvc;
  const svcInfo = MC_SERVICES[svc];
  const chat = {
    id,
    title: '새 채팅',
    preview: '새로운 대화',
    svc,
    time: '방금',
    messages: []
  };
  mcState.chats.unshift(chat);
  renderChatList();
  selectChat(id);
}

function selectChat(chatId) {
  mcState.activeChatId = chatId;
  const chat = getChatById(chatId);
  if (!chat) return;

  // Update chat list active state
  renderChatList();

  // Set service to chat's service
  setService(chat.svc, false);

  // Render messages
  renderMessages(chat);

  // Update title
  document.getElementById('mcChatTitle').textContent = chat.title;
}

function getChatById(id) {
  return mcState.chats.find(c => c.id === id);
}

function deleteChat(chatId, e) {
  e.stopPropagation();
  mcState.chats = mcState.chats.filter(c => c.id !== chatId);
  if (mcState.activeChatId === chatId) {
    if (mcState.chats.length > 0) {
      selectChat(mcState.chats[0].id);
    } else {
      createNewChat();
      return;
    }
  }
  renderChatList();
  showToast('채팅이 삭제되었습니다.');
}

function renderChatList() {
  const list = document.getElementById('chatList');
  if (!list) return;

  if (mcState.chats.length === 0) {
    list.innerHTML = `<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:12px;">채팅 목록이 없습니다</div>`;
    return;
  }

  list.innerHTML = mcState.chats.map(chat => {
    const svcInfo = MC_SERVICES[chat.svc] || MC_SERVICES.chatgpt;
    const isActive = chat.id === mcState.activeChatId;
    return `
      <div class="mc-chat-item ${isActive ? 'active' : ''}" data-id="${chat.id}" onclick="selectChat('${chat.id}')">
        <div class="mc-chat-item-svc" style="background:${svcInfo.color};">
          <i class="${svcInfo.icon}" style="font-size:9px;"></i> ${svcInfo.label}
        </div>
        <div class="mc-chat-item-title">${escHtml(chat.title)}</div>
        <div class="mc-chat-item-preview">${escHtml(chat.preview)}</div>
        <div class="mc-chat-item-time">${chat.time}</div>
        <button class="mc-chat-item-del" onclick="deleteChat('${chat.id}', event)" title="채팅 삭제">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    `;
  }).join('');
}

/* ─────────────────────────────────────────
   SERVICE SELECTOR
───────────────────────────────────────── */
function setupServiceGrid() {
  document.querySelectorAll('.mc-svc-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const svc = btn.dataset.svc;
      setService(svc, true);
    });
  });
}

function setService(svcId, updateChat) {
  const svcInfo = MC_SERVICES[svcId];
  if (!svcInfo) return;
  mcState.currentSvc = svcId;

  // Update buttons
  document.querySelectorAll('.mc-svc-btn').forEach(btn => {
    const isActive = btn.dataset.svc === svcId;
    if (isActive) {
      btn.style.borderColor = svcInfo.color;
      btn.style.backgroundColor = svcInfo.color;
      btn.style.color = '#fff';
      btn.classList.add('mc-svc-active');
    } else {
      btn.style.borderColor = '';
      btn.style.backgroundColor = '';
      btn.style.color = '';
      btn.classList.remove('mc-svc-active');
    }
  });

  // Update service badge in title
  const badge = document.getElementById('mcServiceBadge');
  if (badge) {
    badge.style.background = svcInfo.color;
    badge.innerHTML = `<i class="${svcInfo.icon} me-1"></i> ${svcInfo.label}`;
    badge.dataset.svc = svcId;
  }

  // Update current chat's svc if requested
  if (updateChat && mcState.activeChatId) {
    const chat = getChatById(mcState.activeChatId);
    if (chat) {
      chat.svc = svcId;
      renderChatList();
    }
  }
}

/* ─────────────────────────────────────────
   MESSAGES
───────────────────────────────────────── */
function renderMessages(chat) {
  const area = document.getElementById('mcMessages');
  const d = new Date();
  const dateLabel = `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일`;

  // Date divider
  let html = `<div class="mc-date-divider"><span>${dateLabel}</span></div>`;

  if (chat.messages.length === 0) {
    // Welcome message
    const svcInfo = MC_SERVICES[chat.svc] || MC_SERVICES.chatgpt;
    html += buildWelcomeMsg(svcInfo);
  } else {
    chat.messages.forEach(msg => {
      html += buildMsgHtml(msg);
    });
  }

  area.innerHTML = html;
  scrollToBottom();
}

function buildWelcomeMsg(svcInfo) {
  return `
    <div class="mc-msg mc-msg-assistant">
      <div class="mc-msg-avatar svc-${escHtml(mcState.currentSvc)}">
        <i class="${svcInfo.icon}"></i>
      </div>
      <div class="mc-msg-content">
        <div class="mc-msg-bubble">
          <p>안녕하세요! <strong>${escHtml(svcInfo.label)}</strong>에 연결되었습니다.</p>
          <p>무엇을 도와드릴까요?</p>
        </div>
      </div>
    </div>
  `;
}

function buildMsgHtml(msg) {
  const isUser = msg.role === 'user';
  const svcInfo = MC_SERVICES[msg.svc] || MC_SERVICES.chatgpt;
  const timeStr = msg.time || '방금';

  if (isUser) {
    return `
      <div class="mc-msg mc-msg-user">
        <div class="mc-msg-content">
          <div class="mc-msg-header">
            <strong>나</strong>
            <small class="ms-2">${timeStr}</small>
          </div>
          <div class="mc-msg-bubble">${escHtml(msg.text)}</div>
        </div>
        <div class="mc-msg-avatar user-avatar-msg">
          <i class="fas fa-person"></i>
        </div>
      </div>
    `;
  } else {
    return `
      <div class="mc-msg mc-msg-assistant">
        <div class="mc-msg-avatar svc-${escHtml(msg.svc || 'chatgpt')}">
          <i class="${svcInfo.icon}"></i>
        </div>
        <div class="mc-msg-content">
          <div class="mc-msg-bubble">${renderMarkdown(msg.text)}</div>
        </div>
      </div>
    `;
  }
}

function appendUserMsg(text) {
  const now = formatTime();
  const area = document.getElementById('mcMessages');
  const div = document.createElement('div');
  div.className = 'mc-msg mc-msg-user';
  div.innerHTML = `
    <div class="mc-msg-content">
      <div class="mc-msg-header">
        <strong>나</strong>
        <small class="ms-2">${now}</small>
      </div>
      <div class="mc-msg-bubble">${escHtml(text)}</div>
    </div>
    <div class="mc-msg-avatar user-avatar-msg">
      <i class="fas fa-person"></i>
    </div>
  `;
  area.appendChild(div);
  scrollToBottom();
  return div;
}

function appendTypingIndicator() {
  const svcInfo = MC_SERVICES[mcState.currentSvc] || MC_SERVICES.chatgpt;
  const area = document.getElementById('mcMessages');
  const div = document.createElement('div');
  div.className = 'mc-msg mc-msg-assistant';
  div.id = 'mcTypingRow';
  div.innerHTML = `
    <div class="mc-msg-avatar svc-${mcState.currentSvc}">
      <i class="${svcInfo.icon}"></i>
    </div>
    <div class="mc-msg-content">
      <div class="mc-typing-spinner">
        <div class="mc-typing-dot"></div>
        <div class="mc-typing-dot"></div>
        <div class="mc-typing-dot"></div>
      </div>
    </div>
  `;
  area.appendChild(div);
  scrollToBottom();
  return div;
}

function removeTypingIndicator() {
  const el = document.getElementById('mcTypingRow');
  if (el) el.remove();
}

function appendAssistantMsg(text) {
  const svcInfo = MC_SERVICES[mcState.currentSvc] || MC_SERVICES.chatgpt;
  const area = document.getElementById('mcMessages');
  const div = document.createElement('div');
  div.className = 'mc-msg mc-msg-assistant';
  div.innerHTML = `
    <div class="mc-msg-avatar svc-${mcState.currentSvc}">
      <i class="${svcInfo.icon}"></i>
    </div>
    <div class="mc-msg-content">
      <div class="mc-msg-bubble" id="streamBubble"></div>
    </div>
  `;
  area.appendChild(div);
  scrollToBottom();
  return div.querySelector('#streamBubble');
}

/* ─────────────────────────────────────────
   SEND MESSAGE
───────────────────────────────────────── */
function setupInput() {
  const input = document.getElementById('mcInput');
  const sendBtn = document.getElementById('mcSendBtn');
  const charCount = document.getElementById('mcCharCount');

  input.addEventListener('input', () => {
    // Auto-resize
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 100) + 'px';

    // Char count
    const len = input.value.length;
    charCount.textContent = len;

    // Send button state
    if (len > 0 && !mcState.isStreaming) {
      sendBtn.classList.remove('mc-send-disabled');
      sendBtn.disabled = false;
    } else {
      sendBtn.classList.add('mc-send-disabled');
      sendBtn.disabled = true;
    }
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    }
  });

  sendBtn.addEventListener('click', () => {
    if (!sendBtn.disabled) sendMessage();
  });

  // Attach file
  document.getElementById('btnAttach').addEventListener('click', () => {
    document.getElementById('mcFileInput').click();
  });
}

function sendMessage() {
  const input = document.getElementById('mcInput');
  const text = input.value.trim();
  if (!text || mcState.isStreaming) return;

  const chat = getChatById(mcState.activeChatId);
  if (!chat) return;

  // Save to chat
  const now = formatTime();
  chat.messages.push({ role: 'user', text, svc: mcState.currentSvc, time: now });

  // Update chat title if first message
  if (chat.messages.length === 1) {
    chat.title = text.slice(0, 28) + (text.length > 28 ? '…' : '');
    chat.preview = text.slice(0, 32) + (text.length > 32 ? '…' : '');
    document.getElementById('mcChatTitle').textContent = chat.title;
    renderChatList();
  }

  // Clear welcome message
  const welcome = document.getElementById('mcWelcomeMsg');
  if (welcome) welcome.remove();

  // Append user message
  appendUserMsg(text);

  // Clear input
  input.value = '';
  input.style.height = 'auto';
  document.getElementById('mcCharCount').textContent = '0';
  const sendBtn = document.getElementById('mcSendBtn');
  sendBtn.classList.add('mc-send-disabled');
  sendBtn.disabled = true;

  // Start AI reply
  mcState.isStreaming = true;
  sendBtn.classList.add('mc-loading');
  document.getElementById('mcSendIcon').className = 'fas fa-spinner';

  setTimeout(() => {
    appendTypingIndicator();
    scrollToBottom();

    const delay = 700 + Math.random() * 600;
    setTimeout(() => {
      removeTypingIndicator();

      const reply = MC_REPLIES[Math.floor(Math.random() * MC_REPLIES.length)];
      const bubble = appendAssistantMsg('');

      // Save to chat
      chat.messages.push({ role: 'assistant', text: reply, svc: mcState.currentSvc, time: formatTime() });
      chat.preview = reply.slice(0, 32) + (reply.length > 32 ? '…' : '');
      chat.time = '방금';
      renderChatList();

      // Stream text
      streamText(bubble, reply, () => {
        mcState.isStreaming = false;
        sendBtn.classList.remove('mc-loading');
        document.getElementById('mcSendIcon').className = 'fas fa-paper-plane';

        const curVal = document.getElementById('mcInput').value;
        if (curVal.length > 0) {
          sendBtn.classList.remove('mc-send-disabled');
          sendBtn.disabled = false;
        }
      });
    }, delay);
  }, 100);
}

function streamText(bubble, fullText, onDone) {
  bubble.innerHTML = '<span class="mc-cursor"></span>';
  let idx = 0;
  let rendered = '';

  const timer = setInterval(() => {
    if (idx >= fullText.length) {
      clearInterval(timer);
      bubble.innerHTML = renderMarkdown(fullText);
      if (onDone) onDone();
      return;
    }
    const chunk = Math.min(3, fullText.length - idx);
    rendered += fullText.slice(idx, idx + chunk);
    idx += chunk;
    bubble.innerHTML = renderMarkdown(rendered) + '<span class="mc-cursor"></span>';
    scrollToBottom();
  }, 14);

  mcState.streamTimer = timer;
}

/* ─────────────────────────────────────────
   BUTTONS
───────────────────────────────────────── */
function setupButtons() {
  // New chat
  document.getElementById('btnNewChat').addEventListener('click', () => {
    createNewChat();
  });

  // Delete current chat
  document.getElementById('btnDeleteChat').addEventListener('click', () => {
    if (!mcState.activeChatId) return;
    if (!confirm('현재 채팅을 삭제하시겠습니까?')) return;
    deleteChat(mcState.activeChatId, { stopPropagation: () => {} });
  });

  // Open settings modal
  document.getElementById('btnOpenSettings').addEventListener('click', openSettings);
}

/* ─────────────────────────────────────────
   SETTINGS MODAL
───────────────────────────────────────── */
/* Temperature 슬라이더 업데이트 (모듈 레벨 — openSettings에서도 호출 가능) */
function updateTempSlider() {
  const tempSlider = document.getElementById('settingsTemp');
  const tempLabel  = document.getElementById('settingsTempLabel');
  if (!tempSlider) return;
  const val = parseFloat(tempSlider.value);
  tempLabel.textContent = val.toFixed(1);
  const pct = (val / 2) * 100;
  tempSlider.style.background =
    `linear-gradient(to right, var(--primary) ${pct}%, var(--border) ${pct}%)`;
}

function setupModal() {
  const overlay = document.getElementById('modalSettings');

  // Close buttons
  document.getElementById('btnCloseSettings').addEventListener('click', closeSettings);
  document.getElementById('btnCancelSettings').addEventListener('click', closeSettings);
  overlay.addEventListener('click', e => { if (e.target === overlay) closeSettings(); });

  // Save
  document.getElementById('btnSaveSettings').addEventListener('click', saveSettings);

  // Temperature slider
  document.getElementById('settingsTemp').addEventListener('input', updateTempSlider);
  updateTempSlider(); // Init

  // Keyboard close
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeSettings();
  });
}

function openSettings() {
  const s = mcState.settings;
  document.getElementById('settingsModel').value        = s.model;
  document.getElementById('settingsLang').value         = s.lang;
  document.getElementById('settingsTemp').value         = s.temperature;
  document.getElementById('settingsTempLabel').textContent = s.temperature.toFixed(1);
  updateTempSlider();
  document.getElementById('settingsMaxTokens').value    = s.maxTokens;
  document.getElementById('settingsSysPrompt').value    = s.sysPrompt;
  document.getElementById('settingsStreaming').checked  = s.streaming;
  document.getElementById('settingsSaveHistory').checked= s.saveHistory;
  document.getElementById('settingsWebSearch').checked  = s.webSearch;
  document.getElementById('settingsRag').checked        = s.rag;

  document.getElementById('modalSettings').classList.add('open');
}

function closeSettings() {
  document.getElementById('modalSettings').classList.remove('open');
}

function saveSettings() {
  mcState.settings = {
    model:       document.getElementById('settingsModel').value,
    lang:        document.getElementById('settingsLang').value,
    temperature: parseFloat(parseFloat(document.getElementById('settingsTemp').value).toFixed(1)),
    maxTokens:   parseInt(document.getElementById('settingsMaxTokens').value) || 4096,
    sysPrompt:   document.getElementById('settingsSysPrompt').value,
    streaming:   document.getElementById('settingsStreaming').checked,
    saveHistory: document.getElementById('settingsSaveHistory').checked,
    webSearch:   document.getElementById('settingsWebSearch').checked,
    rag:         document.getElementById('settingsRag').checked
  };
  closeSettings();
  showToast('설정이 저장되었습니다.');
}

/* ─────────────────────────────────────────
   HELPERS
───────────────────────────────────────── */
function scrollToBottom() {
  const area = document.getElementById('mcMessages');
  if (area) area.scrollTop = area.scrollHeight;
}

function formatTime() {
  const d = new Date();
  const h = d.getHours();
  const m = String(d.getMinutes()).padStart(2, '0');
  const ampm = h >= 12 ? '오후' : '오전';
  const h12 = h % 12 || 12;
  return `${ampm} ${h12}:${m}`;
}

function escHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderMarkdown(text) {
  if (!text) return '';
  try {
    marked.setOptions({
      highlight: (code, lang) => {
        if (lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
      },
      breaks: true,
      gfm: true
    });
    return marked.parse(text);
  } catch (e) {
    return escHtml(text);
  }
}

function showToast(msg, duration = 2500) {
  const toast = document.getElementById('mcToast');
  const text  = document.getElementById('mcToastText');
  text.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

/* ── Sidebar toggle (common.js fallback) ── */
const sidebarToggle = document.getElementById('sidebarToggle');
if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}
