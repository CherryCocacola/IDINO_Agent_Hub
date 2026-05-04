/* =============================================
   채팅 상세 페이지 - chat-detail.js
   ============================================= */
'use strict';

/* ── Service metadata ─────────────────────────── */
const SERVICES = {
  chatgpt:    { name:'ChatGPT',          color:'#00C9FF', icon:'fas fa-comment-dots',   models:['gpt-4o','gpt-4o-mini','gpt-4-turbo','gpt-4','gpt-3.5-turbo','gpt-5','gpt-5-mini'] },
  claude:     { name:'Claude',           color:'#D97706', icon:'fas fa-robot',           models:['Claude Sonnet 4','Claude Opus 4','Claude Haiku 3.5'] },
  gemini:     { name:'Gemini',           color:'#3B82F6', icon:'fab fa-google',          models:['Gemini 1.5 Pro','Gemini 1.5 Flash','Gemini 2.0 Flash'] },
  cursor:     { name:'Cursor',           color:'#8B5CF6', icon:'fas fa-code',            models:['Cursor Default'] },
  copilot:    { name:'Copilot',          color:'#6B7280', icon:'fab fa-github',          models:['Copilot Default'] },
  mistral:    { name:'Mistral',          color:'#F59E0B', icon:'fas fa-star',            models:['Mistral Large','Mistral Medium','Mistral Small'] },
  dalle:      { name:'DALL-E 3',         color:'#10B981', icon:'fas fa-image',           models:['DALL-E 3','DALL-E 2'] },
  'gemini-img':{ name:'Gemini Img',      color:'#3B82F6', icon:'fas fa-image',           models:['Gemini Pro Image'] },
  imagen4:    { name:'Imagen 4',         color:'#059669', icon:'fas fa-image',           models:['Imagen 4'] },
  'gen4-img': { name:'Gen4 Image',       color:'#6D28D9', icon:'fas fa-image',           models:['Gen4 Image'] },
  flux2:      { name:'Flux 2',           color:'#B45309', icon:'fas fa-image',           models:['Flux 2'] },
  'gen4-video':{ name:'Gen4 Video',      color:'#DC2626', icon:'fas fa-video',           models:['Gen4 Video'] },
  veo:        { name:'Veo 3.1',          color:'#7C3AED', icon:'fas fa-film',            models:['Veo 3.1'] },
  'openai-video':{ name:'OpenAI Video',  color:'#0EA5E9', icon:'fas fa-camera-movie',    models:['OpenAI Sora'] },
};

/* ── App State ────────────────────────────────── */
const cdState = {
  svc:          'chatgpt',
  model:        'gpt-4-turbo',
  temperature:  0.7,
  maxTokens:    4096,
  lang:         'auto',
  webSearch:    false,
  rag:          false,
  deepResearch: false,
  deepThink:    false,
  streaming:    true,
  messages:     [],   // { role, content, time }
  totalTokens:  0,
  msgCount:     0,
  cost:         0,
  quotaToday:   0,
  quotaMonth:   0,
  isStreaming:  false,
  streamTimer:  null,
  attachments:  [],
};

/* ── Sample AI replies ────────────────────────── */
const SAMPLE_REPLIES = [
  `물론입니다! 말씀하신 내용을 바탕으로 분석해 드리겠습니다.\n\n**주요 포인트:**\n1. 문제의 핵심을 파악하는 것이 우선입니다.\n2. 단계별 접근 방식이 효과적입니다.\n3. 결과를 검증하는 과정을 잊지 마세요.\n\n더 구체적인 내용을 알려주시면 더 자세한 분석을 제공해 드릴 수 있습니다.`,
  `좋은 질문이네요! 제가 확인한 바에 따르면:\n\n\`\`\`javascript\n// 예시 코드\nfunction solution(input) {\n  const result = input.map(item => item * 2);\n  return result.filter(x => x > 10);\n}\n\`\`\`\n\n이 방법으로 문제를 해결할 수 있습니다. 성능도 최적화되어 있습니다.`,
  `네, 이해했습니다. 다음과 같이 정리해 드릴게요:\n\n| 항목 | 내용 | 우선순위 |\n|------|------|----------|\n| 기능 A | 핵심 기능 | 높음 |\n| 기능 B | 보조 기능 | 중간 |\n| 기능 C | 선택 기능 | 낮음 |\n\n> 중요: 우선순위에 따라 순차적으로 진행하시는 것을 권장합니다.\n\n추가 질문이 있으시면 언제든지 말씀해 주세요!`,
  `감사합니다! 분석 결과를 공유해 드리겠습니다.\n\n**결론:** 현재 접근 방식은 전반적으로 올바른 방향이지만, 몇 가지 개선점이 있습니다.\n\n- ✅ 구조적 설계는 잘 되어 있습니다\n- ⚠️ 성능 최적화가 필요한 부분이 있습니다\n- ❌ 보안 취약점이 발견되었습니다\n\n각 항목에 대해 자세한 설명이 필요하시면 말씀해 주세요.`,
  `알겠습니다. 요청하신 내용을 처리했습니다.\n\n번역 결과:\n*"The quick brown fox jumps over the lazy dog"*\n→ **"빠른 갈색 여우가 게으른 개를 뛰어넘습니다"**\n\n추가로 자연스러운 한국어 표현으로 다듬으면:\n→ **"날쌘 갈색 여우가 느릿한 개를 폴짝 뛰어넘었습니다"**\n\n맥락에 따라 적합한 표현을 선택하시면 됩니다.`,
];

/* ── Boot ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initServiceSelectors();
  initLeftPanelSettings();
  initInputArea();
  initSuggestions();
  initAdvModal();
  initQuickActions();
  setTodayLabel();
  syncServiceUI('chatgpt');
});

/* ── Sidebar toggle ───────────────────────────── */
function initSidebar() {
  document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('sidebar-collapsed');
    document.getElementById('mainWrapper')?.classList.toggle('sidebar-collapsed');
  });
}

/* ── Service selector (both strip + chips) ─────── */
function initServiceSelectors() {
  // Top strip
  document.querySelectorAll('#svcStrip .cd-strip-btn').forEach(btn => {
    btn.addEventListener('click', () => selectService(btn.dataset.svc));
  });
  // Left panel chips
  document.querySelectorAll('#serviceChips .cd-svc-chip').forEach(btn => {
    btn.addEventListener('click', () => selectService(btn.dataset.svc));
  });
}

function selectService(svcId) {
  const svc = SERVICES[svcId];
  if (!svc) return;
  cdState.svc = svcId;
  cdState.model = svc.models[0];
  syncServiceUI(svcId);
}

function syncServiceUI(svcId) {
  const svc = SERVICES[svcId];
  if (!svc) return;

  /* — strip buttons — */
  document.querySelectorAll('#svcStrip .cd-strip-btn').forEach(btn => {
    const isActive = btn.dataset.svc === svcId;
    btn.classList.toggle('active', isActive);
    btn.style.setProperty('--cd-svc-color', isActive ? svc.color : '');
  });

  /* — left panel chips — */
  document.querySelectorAll('#serviceChips .cd-svc-chip').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.svc === svcId);
  });

  /* — current bar — */
  const nameEl   = document.getElementById('currentSvcName');
  const iconWrap = document.getElementById('currentSvcIcon');
  const modelLbl = document.getElementById('currentModelLabel');
  if (nameEl)   { nameEl.textContent = svc.name; nameEl.style.color = svc.color; }
  if (iconWrap) { iconWrap.innerHTML = `<i class="${svc.icon}"></i>`; iconWrap.style.color = svc.color; }
  if (modelLbl) modelLbl.textContent = cdState.model;

  /* — footer — */
  const footSvc   = document.getElementById('footerSvcName');
  const footModel = document.getElementById('footerModelName');
  if (footSvc)   footSvc.textContent   = svc.name;
  if (footModel) footModel.textContent = cdState.model;

  /* — subtitle in topbar — */
  const topTitle = document.getElementById('topbarChatTitle');
  if (topTitle) topTitle.textContent = svc.name;

  /* — welcome avatar color — */
  const welcomeAvatar = document.querySelector('#welcomeMsg .cd-msg-avatar');
  if (welcomeAvatar) {
    welcomeAvatar.style.background = svc.color;
    welcomeAvatar.style.borderColor = svc.color;
    welcomeAvatar.style.color = '#fff';
    welcomeAvatar.innerHTML = `<i class="${svc.icon}"></i>`;
  }

  /* — model dropdown in left panel — */
  const modelSel = document.getElementById('modelSelect');
  if (modelSel) {
    modelSel.innerHTML = svc.models.map(m =>
      `<option value="${m}"${m === cdState.model ? ' selected' : ''}>${m}</option>`
    ).join('');
    const hint = document.getElementById('modelHint');
    if (hint) hint.textContent = `${svc.name} · ${svc.models.length}개 모델`;
  }
}

/* ── Left Panel Settings ──────────────────────── */
function initLeftPanelSettings() {
  /* model change */
  document.getElementById('modelSelect')?.addEventListener('change', e => {
    cdState.model = e.target.value;
    document.getElementById('currentModelLabel').textContent = cdState.model;
    document.getElementById('footerModelName').textContent   = cdState.model;
  });

  /* temperature */
  const slider = document.getElementById('tempSlider');
  const valEl  = document.getElementById('tempVal');
  slider?.addEventListener('input', () => {
    cdState.temperature = slider.value / 100;
    if (valEl) valEl.textContent = cdState.temperature.toFixed(1);
    const pct = slider.value;
    slider.style.background = `linear-gradient(to right, var(--primary) ${pct}%, var(--border) ${pct}%)`;
  });

  /* max tokens */
  document.getElementById('maxTokens')?.addEventListener('change', e => {
    cdState.maxTokens = parseInt(e.target.value) || 4096;
  });

  /* lang */
  document.getElementById('langSelect')?.addEventListener('change', e => {
    cdState.lang = e.target.value;
  });

  /* toggles */
  document.getElementById('toggleWebSearch')?.addEventListener('change', e => {
    cdState.webSearch = e.target.checked;
    syncDeepResearch();
  });
  document.getElementById('toggleRag')?.addEventListener('change', e => {
    cdState.rag = e.target.checked;
    syncDeepResearch();
  });
  document.getElementById('toggleDeepResearch')?.addEventListener('change', e => {
    cdState.deepResearch = e.target.checked;
  });
  document.getElementById('toggleDeepThink')?.addEventListener('change', e => {
    cdState.deepThink = e.target.checked;
  });
}

function syncDeepResearch() {
  const deep = document.getElementById('toggleDeepResearch');
  if (deep) deep.disabled = !(cdState.webSearch || cdState.rag);
}

/* ── Suggestions ──────────────────────────────── */
function initSuggestions() {
  document.querySelectorAll('.cd-suggest-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const textarea = document.getElementById('chatInput');
      if (textarea) {
        textarea.value = chip.dataset.text;
        autoResizeTA(textarea);
        textarea.focus();
      }
      // Hide suggestions after first use
      const area = document.getElementById('suggestionsArea');
      if (area) { area.style.opacity = '0'; setTimeout(() => area.style.display = 'none', 200); }
    });
  });
}

/* ── Input Area ───────────────────────────────── */
function initInputArea() {
  const textarea = document.getElementById('chatInput');
  const sendBtn  = document.getElementById('btnSend');

  /* auto resize */
  textarea?.addEventListener('input', () => autoResizeTA(textarea));

  /* Enter = send, Shift+Enter = newline */
  textarea?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendBtn?.addEventListener('click', sendMessage);

  /* file inputs */
  document.getElementById('btnAttachFile')?.addEventListener('click', () =>
    document.getElementById('fileInputDoc')?.click());
  document.getElementById('btnAttachImage')?.addEventListener('click', () =>
    document.getElementById('fileInputImage')?.click());
  document.getElementById('btnAudioFile')?.addEventListener('click', () =>
    document.getElementById('fileInputAudio')?.click());

  document.getElementById('fileInputDoc')?.addEventListener('change', handleFiles);
  document.getElementById('fileInputImage')?.addEventListener('change', handleFiles);
  document.getElementById('fileInputAudio')?.addEventListener('change', handleFiles);

  /* voice recording toggle */
  document.getElementById('btnVoice')?.addEventListener('click', toggleVoice);
}

function autoResizeTA(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 180) + 'px';
}

/* ── Send Message ─────────────────────────────── */
function sendMessage() {
  if (cdState.isStreaming) return;

  const textarea = document.getElementById('chatInput');
  const text = textarea?.value.trim() || '';
  if (!text && cdState.attachments.length === 0) return;

  // Hide suggestions
  const suggestions = document.getElementById('suggestionsArea');
  if (suggestions) suggestions.style.display = 'none';

  // Hide welcome message on first send
  const welcome = document.getElementById('welcomeMsg');
  if (welcome) welcome.style.display = 'none';

  // Append user message
  const userMsg = { role: 'user', content: text, time: nowTime() };
  cdState.messages.push(userMsg);
  appendMessage('user', text, cdState.attachments.slice());

  // Clear input
  if (textarea) { textarea.value = ''; textarea.style.height = 'auto'; }
  cdState.attachments = [];
  renderAttachments();

  // Update stats
  cdState.msgCount++;
  cdState.totalTokens += estimateTokens(text);
  updateStats();

  // Simulate AI response
  setTimeout(() => generateAIReply(text), 300);
}

function generateAIReply(userText) {
  cdState.isStreaming = true;

  const sendBtn  = document.getElementById('btnSend');
  const sendIcon = document.getElementById('sendIcon');
  if (sendBtn)  sendBtn.classList.add('loading');
  if (sendIcon) sendIcon.className = 'fas fa-spinner';

  // Show typing indicator
  const typingId = 'typing-' + Date.now();
  appendTyping(typingId);

  const delay = 600 + Math.random() * 400;

  setTimeout(() => {
    removeTyping(typingId);

    // Pick reply
    const reply = SAMPLE_REPLIES[Math.floor(Math.random() * SAMPLE_REPLIES.length)];

    // Append message with streaming
    const msgEl = appendMessage('assistant', '', []);
    streamText(msgEl, reply, () => {
      cdState.isStreaming = false;
      if (sendBtn)  sendBtn.classList.remove('loading');
      if (sendIcon) sendIcon.className = 'fas fa-paper-plane';

      // Update state
      cdState.messages.push({ role: 'assistant', content: reply, time: nowTime() });
      cdState.msgCount++;
      cdState.totalTokens += estimateTokens(reply);
      cdState.cost += estimateCost(reply);
      cdState.quotaToday  = Math.min(100, cdState.quotaToday + 1);
      cdState.quotaMonth  = Math.min(1000, cdState.quotaMonth + 1);
      updateStats();
      updateQuota();
    });
  }, delay);
}

/* ── Append message to DOM ────────────────────── */
function appendMessage(role, content, attachments) {
  const area = document.getElementById('messagesArea');
  if (!area) return null;

  const svc = SERVICES[cdState.svc];
  const isUser = role === 'user';

  const row = document.createElement('div');
  row.className = `cd-msg cd-msg-${role}`;

  const avatarClass = isUser ? 'user' : `assistant ${cdState.svc}`;
  const avatarHtml = isUser
    ? `<div class="cd-msg-avatar user"><i class="fas fa-user"></i></div>`
    : `<div class="cd-msg-avatar assistant" style="background:${svc.color};border-color:${svc.color};color:#fff;"><i class="${svc.icon}"></i></div>`;

  const attachHtml = attachments.length > 0
    ? `<div class="cd-msg-attachments">${attachments.map(a =>
        `<span class="cd-attach-chip"><i class="fas fa-paperclip"></i>${escHtml(a.name)}</span>`
      ).join('')}</div>`
    : '';

  row.innerHTML = `
    ${avatarHtml}
    <div class="cd-msg-content">
      ${attachHtml}
      <div class="cd-msg-bubble" id="bubble-${row.id || ''}">
        ${content ? renderMarkdown(content) : ''}
      </div>
      <div style="display:flex;align-items:center;gap:6px;">
        <div class="cd-msg-time">${nowTime()}</div>
        <div class="cd-msg-actions">
          <button class="cd-msg-act-btn" title="복사" onclick="copyMsgContent(this)"><i class="fas fa-copy"></i></button>
          ${!isUser ? `<button class="cd-msg-act-btn" title="재생성" onclick="regenMsg(this)"><i class="fas fa-rotate"></i></button>` : ''}
        </div>
      </div>
    </div>
  `;

  area.appendChild(row);
  scrollToBottom();
  return row.querySelector('.cd-msg-bubble');
}

/* ── Streaming text ───────────────────────────── */
function streamText(bubbleEl, fullText, onDone) {
  if (!bubbleEl) { onDone && onDone(); return; }

  bubbleEl.innerHTML = '<span class="cd-cursor"></span>';
  const cursor = bubbleEl.querySelector('.cd-cursor');

  let i = 0;
  const speed = 14; // ms per char
  const chunkSize = 3;

  cdState.streamTimer = setInterval(() => {
    if (i >= fullText.length) {
      clearInterval(cdState.streamTimer);
      cursor?.remove();
      bubbleEl.innerHTML = renderMarkdown(fullText);
      // Re-highlight code
      bubbleEl.querySelectorAll('pre code').forEach(el => {
        if (typeof hljs !== 'undefined') hljs.highlightElement(el);
      });
      scrollToBottom();
      onDone && onDone();
      return;
    }
    const slice = fullText.slice(0, Math.min(i + chunkSize, fullText.length));
    if (cursor) cursor.remove();
    bubbleEl.innerHTML = escHtml(slice) + '<span class="cd-cursor"></span>';
    i += chunkSize;
    scrollToBottom();
  }, speed);
}

/* ── Typing indicator ─────────────────────────── */
function appendTyping(id) {
  const area = document.getElementById('messagesArea');
  if (!area) return;
  const svc = SERVICES[cdState.svc];
  const el = document.createElement('div');
  el.className = 'cd-msg cd-msg-assistant';
  el.id = id;
  el.innerHTML = `
    <div class="cd-msg-avatar assistant" style="background:${svc.color};border-color:${svc.color};color:#fff;">
      <i class="${svc.icon}"></i>
    </div>
    <div class="cd-msg-content">
      <div class="cd-typing">
        <span class="cd-typing-dot"></span>
        <span class="cd-typing-dot"></span>
        <span class="cd-typing-dot"></span>
      </div>
    </div>`;
  area.appendChild(el);
  scrollToBottom();
}
function removeTyping(id) {
  document.getElementById(id)?.remove();
}

/* ── Attachments ──────────────────────────────── */
function handleFiles(e) {
  Array.from(e.target.files).forEach(f => {
    cdState.attachments.push({ name: f.name, size: f.size, type: f.type });
  });
  renderAttachments();
  e.target.value = '';
}

function renderAttachments() {
  const preview = document.getElementById('attachmentPreview');
  if (!preview) return;
  if (cdState.attachments.length === 0) { preview.style.display = 'none'; return; }
  preview.style.display = 'flex';
  preview.innerHTML = cdState.attachments.map((a, i) => `
    <div class="cd-attach-chip">
      <i class="fas fa-paperclip"></i>
      ${escHtml(a.name)}
      <button onclick="removeAttachment(${i})"><i class="fas fa-xmark"></i></button>
    </div>`).join('');
}

window.removeAttachment = function(i) {
  cdState.attachments.splice(i, 1);
  renderAttachments();
};

/* ── Voice ────────────────────────────────────── */
let voiceActive = false;
function toggleVoice() {
  voiceActive = !voiceActive;
  const btn = document.getElementById('btnVoice');
  if (btn) btn.classList.toggle('recording', voiceActive);
  if (voiceActive) showToast('음성 녹음 중...', 'info');
  else { showToast('녹음 완료'); setTimeout(() => { const ta = document.getElementById('chatInput'); if (ta) { ta.value = '(음성 입력된 내용입니다)'; autoResizeTA(ta); } }, 400); }
}

/* ── Message actions ──────────────────────────── */
window.copyMsgContent = function(btn) {
  const bubble = btn.closest('.cd-msg-content')?.querySelector('.cd-msg-bubble');
  if (bubble) navigator.clipboard?.writeText(bubble.innerText).then(() => showToast('복사되었습니다.'));
};
window.regenMsg = function(btn) {
  const msgRow = btn.closest('.cd-msg');
  msgRow?.remove();
  generateAIReply('');
};

/* ── Quick Actions ────────────────────────────── */
function initQuickActions() {
  document.getElementById('btnClearChat')?.addEventListener('click', () => {
    const area = document.getElementById('messagesArea');
    if (!area) return;
    // Keep date divider only
    const divider = area.querySelector('.cd-date-divider');
    area.innerHTML = '';
    if (divider) area.appendChild(divider);
    // Re-show welcome
    cdState.messages = [];
    cdState.msgCount = cdState.totalTokens = cdState.cost = 0;
    const svc = SERVICES[cdState.svc];
    const welcome = document.createElement('div');
    welcome.className = 'cd-msg cd-msg-assistant';
    welcome.id = 'welcomeMsg';
    welcome.innerHTML = `
      <div class="cd-msg-avatar assistant" style="background:${svc.color};border-color:${svc.color};color:#fff;">
        <i class="${svc.icon}"></i>
      </div>
      <div class="cd-msg-content">
        <div class="cd-msg-bubble">
          <p>대화가 초기화되었습니다. 무엇을 도와드릴까요?</p>
        </div>
        <div class="cd-msg-time">방금 전</div>
      </div>`;
    area.appendChild(welcome);
    // Show suggestions again
    const sugg = document.getElementById('suggestionsArea');
    if (sugg) { sugg.style.display = ''; sugg.style.opacity = '1'; }
    updateStats();
    showToast('대화가 초기화되었습니다.', 'info');
  });

  document.getElementById('btnSaveChat')?.addEventListener('click', () => {
    if (cdState.messages.length === 0) { showToast('저장할 대화가 없습니다.', 'info'); return; }
    const content = cdState.messages.map(m => `[${m.role.toUpperCase()}] ${m.content}`).join('\n\n');
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `chat-${Date.now()}.txt`; a.click();
    URL.revokeObjectURL(url);
    showToast('대화 내용이 저장되었습니다.');
  });
}

/* ── Advanced Settings Modal ──────────────────── */
function initAdvModal() {
  document.getElementById('btnAdvSettings')?.addEventListener('click', openAdvModal);
  document.getElementById('btnAdvSettings2')?.addEventListener('click', openAdvModal);
  document.getElementById('btnApplySettings')?.addEventListener('click', applyAdvSettings);

  // Sync streaming toggle knob with cd-switch styling
  const ms = document.getElementById('modalStreaming');
  if (ms) {
    ms.parentElement.className = 'cd-modal-switch';
    const knob = document.createElement('span');
    knob.className = 'cd-switch-knob';
    ms.parentElement.appendChild(knob);
  }
}

function openAdvModal() {
  document.getElementById('modalAdvSettings')?.classList.add('open');
  document.body.style.overflow = 'hidden';
  // Sync state to modal
  const ws = document.getElementById('modalWebSearch');
  if (ws) ws.checked = cdState.webSearch;
}

window.closeAdvModal = function() {
  document.getElementById('modalAdvSettings')?.classList.remove('open');
  document.body.style.overflow = '';
};

function applyAdvSettings() {
  const sysPrompt = document.getElementById('systemPrompt')?.value;
  const format    = document.getElementById('responseFormat')?.value;
  const ctx       = document.getElementById('contextWindow')?.value;
  const streaming = document.getElementById('modalStreaming')?.checked;
  const webSearch = document.getElementById('modalWebSearch')?.checked;

  cdState.streaming = streaming ?? true;
  if (webSearch !== undefined) {
    cdState.webSearch = webSearch;
    const leftToggle = document.getElementById('toggleWebSearch');
    if (leftToggle) leftToggle.checked = webSearch;
    syncDeepResearch();
  }

  closeAdvModal();
  showToast('설정이 적용되었습니다.');
}

/* ── Stats & Quota ────────────────────────────── */
function updateStats() {
  setText('statMessages', cdState.msgCount);
  setText('statTokens',   cdState.totalTokens.toLocaleString());
  setText('statCost',    `$${cdState.cost.toFixed(4)}`);
}

function updateQuota() {
  const todayPct  = (cdState.quotaToday / 100) * 100;
  const monthPct  = (cdState.quotaMonth / 1000) * 100;
  setText('quotaToday',  `${cdState.quotaToday} / 100`);
  setText('quotaMonth',  `${cdState.quotaMonth} / 1000`);
  setText('quotaRemaining', (1000 - cdState.quotaMonth).toLocaleString());

  const todayBar  = document.getElementById('quotaTodayBar');
  const monthBar  = document.getElementById('quotaMonthBar');
  if (todayBar)  todayBar.style.width  = todayPct + '%';
  if (monthBar)  monthBar.style.width  = monthPct + '%';
  if (monthBar)  monthBar.className = `cd-quota-fill ${monthPct > 80 ? 'danger' : monthPct > 50 ? 'warning' : 'success'}`;
}

/* ── Scroll to bottom ─────────────────────────── */
function scrollToBottom() {
  const area = document.getElementById('messagesArea');
  if (area) area.scrollTop = area.scrollHeight;
}

/* ── Today label ──────────────────────────────── */
function setTodayLabel() {
  const today = new Date();
  const opts = { year:'numeric', month:'long', day:'numeric' };
  setText('todayLabel', today.toLocaleDateString('ko-KR', opts));
}

/* ── Toast ────────────────────────────────────── */
let toastTimer = null;
function showToast(msg, type = 'success') {
  const el   = document.getElementById('cdToast');
  const text = document.getElementById('cdToastText');
  const icon = el?.querySelector('i');
  if (!el || !text) return;
  if (toastTimer) clearTimeout(toastTimer);
  text.textContent = msg;
  if (icon) {
    icon.className = type === 'info' ? 'fas fa-circle-info' : type === 'warn' ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle';
    icon.style.color = type === 'info' ? '#3B82F6' : type === 'warn' ? '#F59E0B' : '#10B981';
  }
  el.classList.add('show');
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

/* ── Markdown renderer ────────────────────────── */
function renderMarkdown(text) {
  if (typeof marked !== 'undefined') {
    marked.setOptions({ breaks: true, gfm: true });
    return marked.parse(text);
  }
  return escHtml(text).replace(/\n/g, '<br>');
}

/* ── Helpers ──────────────────────────────────── */
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function nowTime() {
  return new Date().toLocaleTimeString('ko-KR', { hour:'2-digit', minute:'2-digit' });
}
function estimateTokens(text) { return Math.ceil(text.length / 4); }
function estimateCost(text)   { return estimateTokens(text) * 0.00001; }
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
