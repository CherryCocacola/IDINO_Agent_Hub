/* =============================================
   AI 채팅 - 핵심 로직
   ============================================= */

(function () {
  'use strict';

  // =============================================
  // STATE
  // =============================================
  const state = {
    currentModel: { id: 'claude', name: 'Claude Sonnet 4', provider: 'Anthropic' },
    messages: [],          // { role, content, model, time, tokens }
    totalTokens: 0,
    isStreaming: false,
    attachments: [],
    systemPrompt: '',
    params: { temperature: 0.7, maxTokens: 2048, topP: 0.9 },
    currentChatId: 1,
  };

  // Cost per 1K tokens (approximate, KRW)
  const MODEL_COST = { claude: 3, gpt4o: 5, gemini: 1, finance: 4, dalle: 10 };

  // Demo responses for each model
  const DEMO_RESPONSES = {
    claude: [
      `안녕하세요! 저는 **Claude Sonnet 4**입니다. 무엇을 도와드릴까요?\n\n질문하신 내용을 분석해 보겠습니다. 다음과 같은 접근 방식을 제안드립니다:\n\n1. **현황 파악** - 현재 상태를 정확히 이해합니다\n2. **요구사항 분석** - 달성하고자 하는 목표를 명확히 합니다\n3. **솔루션 제안** - 최적의 방법을 추천드립니다\n\n더 구체적인 내용을 알려주시면 더 정확한 도움을 드릴 수 있습니다.`,

      `좋은 질문이네요! 다음과 같이 Python 코드로 구현할 수 있습니다:\n\n\`\`\`python\nfrom fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\nfrom typing import Optional\nimport uvicorn\n\napp = FastAPI(title="AI REST API", version="1.0.0")\n\nclass MessageRequest(BaseModel):\n    content: str\n    model: str = "claude-sonnet-4"\n    max_tokens: Optional[int] = 2048\n\nclass MessageResponse(BaseModel):\n    response: str\n    tokens_used: int\n    model: str\n\n@app.post("/v1/chat", response_model=MessageResponse)\nasync def chat(request: MessageRequest):\n    # AI 모델 호출 로직\n    result = await call_ai_model(request)\n    return MessageResponse(\n        response=result["content"],\n        tokens_used=result["usage"]["total_tokens"],\n        model=request.model\n    )\n\n@app.get("/v1/models")\nasync def list_models():\n    return {"models": ["gpt-4o", "claude-sonnet-4", "gemini-pro"]}\n\nif __name__ == "__main__":\n    uvicorn.run(app, host="0.0.0.0", port=8000)\n\`\`\`\n\n이 코드는 **FastAPI** 프레임워크를 사용하여 구현되었습니다. 주요 특징:\n- `/v1/chat` 엔드포인트로 AI 모델 호출\n- Pydantic을 사용한 요청/응답 검증\n- 비동기 처리로 성능 최적화\n\n추가 기능이 필요하시면 알려주세요!`,

      `데이터를 분석한 결과 다음과 같은 **핵심 인사이트** 3가지를 도출했습니다:\n\n### 1. 사용량 증가 트렌드 📈\n- 지난 7일 대비 **12.5% 증가**\n- 피크 시간대: 오전 10시 ~ 오후 3시\n- 주말 사용량이 평일 대비 35% 낮음\n\n### 2. 모델별 성능 차이 🤖\n\n| 모델 | 평균 응답시간 | 정확도 | 비용효율 |\n|------|------------|--------|--------|\n| GPT-4o | 198ms | 94% | 중 |\n| Claude | 241ms | 96% | 상 |\n| Gemini | 312ms | 91% | 하 |\n\n### 3. 비용 최적화 기회 💰\n- Claude를 기본 모델로 사용 시 **월 약 ₩180K 절감** 가능\n- 간단한 작업에 경량 모델 활용 권장\n\n> 이 분석은 최근 30일 데이터를 기반으로 합니다.`,
    ],

    gpt4o: [
      `안녕하세요! **GPT-4o**입니다. 최신 OpenAI 모델로 텍스트, 이미지, 코드 등 다양한 작업을 처리할 수 있습니다.\n\n요청하신 내용을 정리해드리겠습니다. 먼저 다음 사항들을 고려해볼 필요가 있습니다:\n\n- **성능 요구사항**: 응답 속도와 정확도 균형\n- **비용 효율성**: 모델 선택에 따른 비용 최적화\n- **확장성**: 트래픽 증가에 대한 대응 방안\n\n구체적인 사용 사례를 공유해주시면 더 맞춤화된 답변을 드릴 수 있습니다.`,

      `마케팅 이메일 초안을 작성해드리겠습니다:\n\n---\n**제목**: [기업명]의 AI 솔루션으로 업무 효율을 3배 높이세요\n\n안녕하세요, [담당자명] 님\n\n바쁘신 업무 중에 연락드려 죄송합니다.\n\n저는 **[회사명]**의 AI 솔루션 담당 [이름]입니다. 최근 귀사의 디지털 트랜스포메이션 노력에 대해 알게 되어 연락드리게 되었습니다.\n\n**저희 AI 통합관리 플랫폼은:**\n- ✅ GPT-4o, Claude, Gemini 등 12개 AI 모델 통합 관리\n- ✅ 실시간 모니터링 및 비용 최적화\n- ✅ 기업 수준의 보안 및 권한 관리\n- ✅ 30분 내 도입 가능한 직관적 UI\n\n**도입 기업의 평균 성과:**\n- 업무 처리 속도 **300% 향상**\n- AI 운영 비용 **40% 절감**\n- 개발 리소스 **60% 절약**\n\n30분 무료 데모를 제안드립니다. 다음 주 가능한 시간이 있으신가요?\n\n감사합니다.\n---\n\n필요에 따라 내용을 수정하겠습니다!`,
    ],

    gemini: [
      `**Gemini Pro 1.5**입니다. 멀티모달 기능을 포함한 강력한 AI 어시스턴트입니다.\n\n요청하신 분석 작업을 진행하겠습니다. Gemini는 특히 **긴 컨텍스트 처리**와 **다양한 형식의 데이터 분석**에 강점이 있습니다.\n\n구체적인 데이터나 파일을 업로드해주시면 즉시 분석을 시작하겠습니다.`,
    ],

    finance: [
      `**Custom-FinanceBot v2.1**입니다. 금융 데이터 분석 및 투자 인사이트 전문 AI입니다.\n\n⚠️ **주의**: 본 AI의 분석 결과는 참고용이며, 실제 투자 결정 시에는 전문 금융 어드바이저와 상담하시기 바랍니다.\n\n질문하신 내용에 대한 금융 분석을 제공해드리겠습니다:\n\n### 시장 동향 분석\n- **KOSPI**: 2,580pt (▲ 12pt, +0.47%)\n- **KOSDAQ**: 845pt (▼ 3pt, -0.35%)\n- **원/달러**: 1,325원\n\n### 섹터별 AI 관련 종목\n| 종목 | 현재가 | 전일 대비 | PER |\n|------|--------|----------|-----|\n| 삼성전자 | 72,400 | ▲ 600 | 18.2 |\n| SK하이닉스 | 168,500 | ▲ 2,100 | 24.1 |\n| 카카오 | 38,200 | ▼ 400 | 32.5 |\n\n더 구체적인 종목 분석이나 포트폴리오 검토가 필요하신가요?`,
    ],
  };

  // =============================================
  // DOM REFS
  // =============================================
  const chatMessages  = document.getElementById('chatMessages');
  const chatInput     = document.getElementById('chatInput');
  const btnSend       = document.getElementById('btnSend');
  const btnNewChat    = document.getElementById('btnNewChat');
  const chatWelcome   = document.getElementById('chatWelcome');
  const tokenCount    = document.getElementById('tokenCount');
  const costEstimate  = document.getElementById('costEstimate');
  const modelSelectBtn= document.getElementById('modelSelectBtn');
  const modelDropdown = document.getElementById('modelDropdown');
  const btnSystemPrompt = document.getElementById('btnSystemPrompt');
  const systemPromptPanel = document.getElementById('systemPromptPanel');
  const btnParams     = document.getElementById('btnParams');
  const paramsPanel   = document.getElementById('paramsPanel');
  const btnClearChat  = document.getElementById('btnClearChat');
  const fileInput     = document.getElementById('fileInput');
  const btnAttach     = document.getElementById('btnAttach');
  const attachmentPreview = document.getElementById('attachmentPreview');
  const historyItems  = document.querySelectorAll('.history-item');
  const msgContextMenu = document.getElementById('msgContextMenu');

  // =============================================
  // TEXTAREA AUTO-RESIZE
  // =============================================
  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  }

  chatInput.addEventListener('input', function () {
    autoResize(this);
    btnSend.disabled = this.value.trim() === '' && state.attachments.length === 0;
  });

  // Enter = send, Shift+Enter = newline
  chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!btnSend.disabled && !state.isStreaming) sendMessage();
    }
  });

  // =============================================
  // MODEL SELECTOR
  // =============================================
  modelSelectBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    this.classList.toggle('open');
    modelDropdown.classList.toggle('open');
  });

  document.addEventListener('click', function () {
    modelSelectBtn.classList.remove('open');
    modelDropdown.classList.remove('open');
  });

  document.querySelectorAll('.model-dropdown-item:not(.model-dropdown-disabled)').forEach(function (item) {
    item.addEventListener('click', function (e) {
      e.stopPropagation();
      const modelId   = this.dataset.model;
      const modelName = this.dataset.name;
      const provider  = this.dataset.provider;

      state.currentModel = { id: modelId, name: modelName, provider };

      // Update button display
      const iconEl  = modelSelectBtn.querySelector('.model-select-icon');
      const nameEl  = modelSelectBtn.querySelector('.model-select-name');
      const provEl  = modelSelectBtn.querySelector('.model-select-provider');
      const srcIcon = this.querySelector('.model-select-icon');

      iconEl.className = srcIcon.className;
      iconEl.innerHTML = srcIcon.innerHTML;
      nameEl.textContent = modelName;
      provEl.textContent = provider;

      // Update selected state
      document.querySelectorAll('.model-dropdown-item').forEach(i => {
        i.classList.remove('model-dropdown-selected');
        const chk = i.querySelector('.model-dropdown-check');
        if (chk) chk.remove();
      });
      this.classList.add('model-dropdown-selected');
      const check = document.createElement('i');
      check.className = 'fas fa-check model-dropdown-check';
      this.appendChild(check);

      modelSelectBtn.classList.remove('open');
      modelDropdown.classList.remove('open');
    });
  });

  // =============================================
  // PANELS: System Prompt & Params
  // =============================================
  btnSystemPrompt.addEventListener('click', function () {
    const open = systemPromptPanel.style.display !== 'none';
    systemPromptPanel.style.display = open ? 'none' : 'block';
    paramsPanel.style.display = 'none';
    this.classList.toggle('active', !open);
    btnParams.classList.remove('active');
  });

  document.getElementById('btnCloseSystemPrompt').addEventListener('click', function () {
    systemPromptPanel.style.display = 'none';
    btnSystemPrompt.classList.remove('active');
  });

  btnParams.addEventListener('click', function () {
    const open = paramsPanel.style.display !== 'none';
    paramsPanel.style.display = open ? 'none' : 'block';
    systemPromptPanel.style.display = 'none';
    this.classList.toggle('active', !open);
    btnSystemPrompt.classList.remove('active');
  });

  // Sliders
  document.getElementById('tempSlider').addEventListener('input', function () {
    document.getElementById('tempDisplay').textContent = this.value;
    state.params.temperature = parseFloat(this.value);
  });
  document.getElementById('maxTokensSlider').addEventListener('input', function () {
    document.getElementById('maxTokensDisplay').textContent = parseInt(this.value).toLocaleString();
    state.params.maxTokens = parseInt(this.value);
  });
  document.getElementById('topPSlider').addEventListener('input', function () {
    document.getElementById('topPDisplay').textContent = this.value;
    state.params.topP = parseFloat(this.value);
  });

  // =============================================
  // FILE ATTACH
  // =============================================
  btnAttach.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', function () {
    Array.from(this.files).forEach(function (file) {
      state.attachments.push(file);
      addAttachmentChip(file.name);
    });
    this.value = '';
    btnSend.disabled = chatInput.value.trim() === '' && state.attachments.length === 0;
    if (state.attachments.length > 0) {
      attachmentPreview.style.display = 'flex';
      btnSend.disabled = false;
    }
  });

  function addAttachmentChip(name) {
    const chip = document.createElement('div');
    chip.className = 'attachment-chip';
    chip.innerHTML = `<i class="fas fa-file"></i><span>${name}</span><button onclick="removeAttachment('${name}', this)"><i class="fas fa-times"></i></button>`;
    attachmentPreview.appendChild(chip);
  }

  window.removeAttachment = function (name, btn) {
    state.attachments = state.attachments.filter(f => f.name !== name);
    btn.closest('.attachment-chip').remove();
    if (state.attachments.length === 0) {
      attachmentPreview.style.display = 'none';
      if (chatInput.value.trim() === '') btnSend.disabled = true;
    }
  };

  // =============================================
  // CLEAR CHAT
  // =============================================
  btnClearChat.addEventListener('click', function () {
    if (state.messages.length === 0) return;
    if (confirm('현재 대화를 초기화할까요?')) {
      state.messages = [];
      state.totalTokens = 0;
      updateTokenDisplay();
      renderMessages();
    }
  });

  // =============================================
  // SEND MESSAGE
  // =============================================
  btnSend.addEventListener('click', function () {
    if (state.isStreaming) {
      stopStreaming();
    } else if (!btnSend.disabled) {
      sendMessage();
    }
  });

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text && state.attachments.length === 0) return;

    // Hide welcome
    if (chatWelcome) chatWelcome.style.display = 'none';

    // Build user message content
    let content = text;
    if (state.attachments.length > 0) {
      content += state.attachments.map(f => `\n\n📎 [첨부파일: ${f.name}]`).join('');
    }

    const userMsg = {
      role: 'user',
      content: content,
      time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      tokens: Math.ceil(content.length / 3),
    };

    state.messages.push(userMsg);
    state.totalTokens += userMsg.tokens;

    // Clear input
    chatInput.value = '';
    autoResize(chatInput);
    btnSend.disabled = true;
    state.attachments = [];
    attachmentPreview.innerHTML = '';
    attachmentPreview.style.display = 'none';

    renderMessages();
    scrollToBottom();

    // Generate AI response
    setTimeout(() => generateResponse(), 400);
  }

  // =============================================
  // RESPONSE GENERATION (SIMULATED STREAMING)
  // =============================================
  let streamInterval = null;

  function generateResponse() {
    state.isStreaming = true;
    btnSend.disabled = false;
    btnSend.classList.add('sending');
    btnSend.querySelector('i').className = 'fas fa-stop';

    const modelId = state.currentModel.id;
    const responses = DEMO_RESPONSES[modelId] || DEMO_RESPONSES.claude;
    const fullText = responses[Math.floor(Math.random() * responses.length)];

    // Add thinking message
    const thinkingMsg = {
      role: 'assistant',
      content: '',
      model: modelId,
      modelName: state.currentModel.name,
      time: new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }),
      tokens: 0,
      streaming: true,
    };
    state.messages.push(thinkingMsg);
    renderMessages();
    scrollToBottom();

    // Stream characters
    let i = 0;
    const chunkSize = 3;
    streamInterval = setInterval(function () {
      if (i >= fullText.length) {
        clearInterval(streamInterval);
        thinkingMsg.streaming = false;
        thinkingMsg.tokens = Math.ceil(fullText.length / 3);
        state.totalTokens += thinkingMsg.tokens;
        state.isStreaming = false;
        btnSend.classList.remove('sending');
        btnSend.querySelector('i').className = 'fas fa-paper-plane';
        btnSend.disabled = chatInput.value.trim() === '';
        updateTokenDisplay();
        renderMessages();
        scrollToBottom();
        return;
      }
      thinkingMsg.content += fullText.slice(i, i + chunkSize);
      i += chunkSize;
      renderLastAssistantMessage(thinkingMsg);
      scrollToBottom();
    }, 18);
  }

  function stopStreaming() {
    if (streamInterval) clearInterval(streamInterval);
    state.isStreaming = false;
    const last = state.messages[state.messages.length - 1];
    if (last && last.streaming) {
      last.streaming = false;
      last.tokens = Math.ceil(last.content.length / 3);
      state.totalTokens += last.tokens;
    }
    btnSend.classList.remove('sending');
    btnSend.querySelector('i').className = 'fas fa-paper-plane';
    btnSend.disabled = chatInput.value.trim() === '';
    updateTokenDisplay();
    renderMessages();
  }

  // =============================================
  // RENDER
  // =============================================
  function renderMessages() {
    // Keep welcome in DOM; it's hidden via display:none
    // Clear only message groups
    document.querySelectorAll('.message-group').forEach(el => el.remove());

    state.messages.forEach(function (msg, idx) {
      const el = buildMessageEl(msg, idx);
      chatMessages.appendChild(el);
    });

    // Highlight code blocks
    document.querySelectorAll('.msg-bubble pre code').forEach(function (block) {
      hljs.highlightElement(block);
    });
  }

  function renderLastAssistantMessage(msg) {
    const existing = document.querySelector('.message-group.streaming-msg');
    if (existing) existing.remove();
    const el = buildMessageEl(msg, state.messages.length - 1);
    el.classList.add('streaming-msg');
    chatMessages.appendChild(el);
  }

  function buildMessageEl(msg, idx) {
    const div = document.createElement('div');
    div.className = `message-group msg-${msg.role}`;
    if (msg.model) div.setAttribute('data-model', msg.model);
    div.dataset.idx = idx;

    if (msg.role === 'user') {
      div.innerHTML = `
        <div class="msg-avatar"><i class="fas fa-user"></i></div>
        <div>
          <div class="msg-bubble">${escapeUserContent(msg.content)}</div>
          <div class="msg-actions">
            <button class="msg-action-btn" onclick="copyMessage(${idx})"><i class="fas fa-copy"></i> 복사</button>
            <button class="msg-action-btn" onclick="editMessage(${idx})"><i class="fas fa-edit"></i> 편집</button>
          </div>
        </div>`;
    } else {
      const iconMap = { claude:'brain', gpt4o:'robot', gemini:'gem', finance:'chart-pie', dalle:'image' };
      const icon = iconMap[msg.model] || 'brain';

      let bubbleContent;
      if (msg.streaming && msg.content === '') {
        bubbleContent = `<div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>`;
      } else {
        const rendered = renderMarkdown(msg.content);
        const cursor   = msg.streaming ? '<span class="streaming-cursor"></span>' : '';
        bubbleContent  = rendered + cursor;
      }

      div.innerHTML = `
        <div class="msg-avatar"><i class="fas fa-${icon}"></i></div>
        <div class="msg-content">
          <div class="msg-header">
            <span class="msg-model-name">${msg.modelName || 'AI'}</span>
            <span class="msg-time">${msg.time}</span>
            ${msg.tokens ? `<span class="msg-token-info"><i class="fas fa-coins"></i> ${msg.tokens.toLocaleString()} tokens</span>` : ''}
          </div>
          <div class="msg-bubble">${bubbleContent}</div>
          <div class="msg-actions">
            <button class="msg-action-btn" onclick="copyMessage(${idx})"><i class="fas fa-copy"></i> 복사</button>
            <button class="msg-action-btn" onclick="regenerateMessage(${idx})"><i class="fas fa-sync"></i> 재생성</button>
            <button class="msg-action-btn" onclick="toggleRaw(${idx}, this)"><i class="fas fa-code"></i> Raw</button>
          </div>
        </div>`;
    }

    // Right-click context menu
    div.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      showContextMenu(e.clientX, e.clientY, idx);
    });

    return div;
  }

  // =============================================
  // MARKDOWN RENDER
  // =============================================
  function renderMarkdown(text) {
    const useMarkdown = document.getElementById('chkMarkdown').checked;
    if (!useMarkdown) return escapeUserContent(text);

    // Pre-process code blocks to add header
    let processed = text.replace(/```(\w*)\n?([\s\S]*?)```/g, function (_, lang, code) {
      const langLabel = lang || 'code';
      return `<div class="code-block-header"><span class="code-lang">${langLabel}</span><button class="code-copy-btn" onclick="copyCode(this)"><i class="fas fa-copy"></i> 복사</button></div><pre><code class="language-${langLabel}">${escapeHtml(code.trim())}</code></pre>`;
    });

    // Wrap pre blocks
    processed = processed.replace(/<div class="code-block-header">[\s\S]*?<\/pre>/g, function (m) {
      return `<div class="code-wrapper">${m}</div>`;
    });

    if (window.marked) {
      // Parse non-code parts with marked
      try {
        const renderer = new marked.Renderer();
        const result = marked.parse(processed, { renderer, breaks: true, gfm: true });
        return result;
      } catch (e) {
        return processed.replace(/\n/g, '<br>');
      }
    }
    return processed.replace(/\n/g, '<br>');
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function escapeUserContent(str) {
    return escapeHtml(str).replace(/\n/g, '<br>');
  }

  // =============================================
  // MESSAGE ACTIONS
  // =============================================
  window.copyMessage = function (idx) {
    const msg = state.messages[idx];
    if (!msg) return;
    navigator.clipboard.writeText(msg.content).then(() => showToast('복사되었습니다'));
  };

  window.copyCode = function (btn) {
    const code = btn.closest('.code-wrapper')?.querySelector('code');
    if (code) {
      navigator.clipboard.writeText(code.innerText).then(() => {
        btn.innerHTML = '<i class="fas fa-check"></i> 완료';
        setTimeout(() => { btn.innerHTML = '<i class="fas fa-copy"></i> 복사'; }, 1500);
      });
    }
  };

  window.regenerateMessage = function (idx) {
    // Remove from idx onwards (keep user message at idx-1)
    state.messages = state.messages.slice(0, idx);
    renderMessages();
    setTimeout(() => generateResponse(), 200);
  };

  window.editMessage = function (idx) {
    const msg = state.messages[idx];
    if (!msg) return;
    chatInput.value = msg.content;
    autoResize(chatInput);
    btnSend.disabled = false;
    chatInput.focus();
    state.messages = state.messages.slice(0, idx);
    renderMessages();
  };

  window.toggleRaw = function (idx, btn) {
    const msg = state.messages[idx];
    if (!msg) return;
    const bubble = btn.closest('.msg-content').querySelector('.msg-bubble');
    if (bubble.dataset.raw === '1') {
      bubble.innerHTML = renderMarkdown(msg.content);
      bubble.dataset.raw = '0';
      btn.innerHTML = '<i class="fas fa-code"></i> Raw';
      document.querySelectorAll('.msg-bubble pre code').forEach(b => hljs.highlightElement(b));
    } else {
      bubble.textContent = msg.content;
      bubble.dataset.raw = '1';
      btn.innerHTML = '<i class="fas fa-eye"></i> 렌더';
    }
  };

  // =============================================
  // CONTEXT MENU
  // =============================================
  let ctxIdx = -1;

  function showContextMenu(x, y, idx) {
    ctxIdx = idx;
    msgContextMenu.style.display = 'block';
    msgContextMenu.style.left = Math.min(x, window.innerWidth - 180) + 'px';
    msgContextMenu.style.top  = Math.min(y, window.innerHeight - 150) + 'px';
  }

  document.addEventListener('click', function () {
    msgContextMenu.style.display = 'none';
  });

  document.getElementById('ctxCopy').addEventListener('click', () => { if (ctxIdx >= 0) copyMessage(ctxIdx); });
  document.getElementById('ctxRegenerate').addEventListener('click', () => { if (ctxIdx >= 0) regenerateMessage(ctxIdx); });
  document.getElementById('ctxEdit').addEventListener('click', () => { if (ctxIdx >= 0) editMessage(ctxIdx); });
  document.getElementById('ctxDelete').addEventListener('click', function () {
    if (ctxIdx >= 0) {
      state.messages.splice(ctxIdx, 1);
      renderMessages();
    }
  });

  // =============================================
  // TOKEN / COST DISPLAY
  // =============================================
  function updateTokenDisplay() {
    tokenCount.textContent = state.totalTokens.toLocaleString();
    const costPer1k = MODEL_COST[state.currentModel.id] || 3;
    const cost = Math.ceil((state.totalTokens / 1000) * costPer1k);
    costEstimate.textContent = '₩' + cost.toLocaleString();
  }

  // =============================================
  // HISTORY PANEL
  // =============================================
  historyItems.forEach(function (item) {
    item.addEventListener('click', function (e) {
      if (e.target.closest('.history-item-del')) return;
      document.querySelectorAll('.history-item').forEach(i => i.classList.remove('history-item-active'));
      this.classList.add('history-item-active');
      // In a real app, load the conversation
      const chatName = this.querySelector('.history-item-title').textContent;
      document.getElementById('currentChatName').textContent = chatName;
    });
  });

  document.querySelectorAll('.history-item-del').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      this.closest('.history-item').remove();
    });
  });

  // =============================================
  // NEW CHAT
  // =============================================
  btnNewChat.addEventListener('click', function () {
    state.messages = [];
    state.totalTokens = 0;
    updateTokenDisplay();
    renderMessages();
    if (chatWelcome) chatWelcome.style.display = 'flex';
    chatInput.value = '';
    autoResize(chatInput);
    btnSend.disabled = true;
    document.getElementById('currentChatName').textContent = '새 대화';
    document.querySelectorAll('.history-item').forEach(i => i.classList.remove('history-item-active'));
  });

  // =============================================
  // SUGGESTION CHIPS
  // =============================================
  document.querySelectorAll('.suggestion-chip').forEach(function (chip) {
    chip.addEventListener('click', function () {
      chatInput.value = this.dataset.text;
      autoResize(chatInput);
      btnSend.disabled = false;
      chatInput.focus();
    });
  });

  // =============================================
  // EXPORT
  // =============================================
  document.getElementById('btnExport').addEventListener('click', function () {
    if (state.messages.length === 0) { showToast('내보낼 대화가 없습니다'); return; }
    const text = state.messages.map(function (m) {
      const role = m.role === 'user' ? '사용자' : m.modelName || 'AI';
      return `[${role}] ${m.time}\n${m.content}\n`;
    }).join('\n---\n\n');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url;
    a.download = `대화_${new Date().toLocaleDateString('ko-KR')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('대화가 저장되었습니다');
  });

  // =============================================
  // TOAST NOTIFICATION
  // =============================================
  function showToast(msg) {
    const toast = document.createElement('div');
    toast.style.cssText = `
      position:fixed; bottom:80px; left:50%; transform:translateX(-50%);
      background:rgba(17,24,39,0.92); color:#fff; padding:8px 18px;
      border-radius:20px; font-size:13px; font-weight:500; z-index:9999;
      animation:fadeIn 0.2s ease; pointer-events:none;
      backdrop-filter:blur(8px); box-shadow:0 4px 12px rgba(0,0,0,0.2);
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
  }

  // =============================================
  // UTILS
  // =============================================
  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // =============================================
  // EXAMPLE CONVERSATIONS (예시 대화 데이터)
  // =============================================
  const EXAMPLE_CONVERSATIONS = {

    // 대화 1: Python 코드 최적화 (claude, 현재 활성)
    1: {
      model: { id: 'claude', name: 'Claude Sonnet 4', provider: 'Anthropic' },
      title: 'Python 코드 최적화',
      messages: [
        {
          role: 'user',
          content: '안녕하세요! 다음 Python 코드가 너무 느린데 최적화 방법을 알려주세요.\n\ndef find_duplicates(lst):\n    duplicates = []\n    for i in range(len(lst)):\n        for j in range(i+1, len(lst)):\n            if lst[i] == lst[j] and lst[i] not in duplicates:\n                duplicates.append(lst[i])\n    return duplicates\n\n리스트가 100만 개 요소일 때 너무 오래 걸립니다.',
          time: '09:21',
          tokens: 98,
        },
        {
          role: 'assistant',
          model: 'claude',
          modelName: 'Claude Sonnet 4',
          time: '09:21',
          tokens: 312,
          content: `현재 코드는 **O(n²)** 시간복잡도를 가지고 있어 100만 개 요소에서 매우 느립니다. 다음과 같이 최적화할 수 있습니다.

### 방법 1. Set 활용 — O(n) 시간복잡도

\`\`\`python
def find_duplicates_fast(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)
\`\`\`

### 방법 2. Counter 활용 (가장 Pythonic)

\`\`\`python
from collections import Counter

def find_duplicates_counter(lst):
    counts = Counter(lst)
    return [item for item, count in counts.items() if count > 1]
\`\`\`

### 방법 3. Pandas 활용 (대용량 데이터)

\`\`\`python
import pandas as pd

def find_duplicates_pandas(lst):
    s = pd.Series(lst)
    return s[s.duplicated()].unique().tolist()
\`\`\`

### 성능 비교

| 방법 | 100만 요소 | 시간복잡도 |
|------|-----------|-----------|
| 기존 코드 | ~180초 | O(n²) |
| Set 활용 | ~0.15초 | O(n) |
| Counter | ~0.18초 | O(n) |
| Pandas | ~0.08초 | O(n) |

> **추천**: 일반 목적이라면 **방법 2 (Counter)**, 대용량 데이터라면 **방법 3 (Pandas)**를 사용하세요. 약 **1,200배** 성능 향상을 기대할 수 있습니다! 🚀`,
        },
        {
          role: 'user',
          content: '와, 엄청난 차이네요! Counter 방법으로 적용해봤는데 정말 빠르네요. 그런데 이번엔 메모리 사용량도 줄이고 싶은데, 제너레이터를 활용하는 방법도 있을까요?',
          time: '09:24',
          tokens: 52,
        },
        {
          role: 'assistant',
          model: 'claude',
          modelName: 'Claude Sonnet 4',
          time: '09:24',
          tokens: 287,
          content: `좋은 질문입니다! 제너레이터를 활용하면 **메모리 효율**을 크게 높일 수 있습니다.

### 제너레이터 버전

\`\`\`python
def find_duplicates_generator(lst):
    """메모리 효율적인 제너레이터 버전"""
    seen = set()
    yielded = set()
    for item in lst:
        if item in seen and item not in yielded:
            yield item
            yielded.add(item)
        seen.add(item)

# 사용 예시
data = list(range(1_000_000)) + list(range(500_000))  # 중복 포함

# 전체 결과가 필요할 때
duplicates = list(find_duplicates_generator(data))

# 첫 번째 중복만 필요할 때 (매우 효율적!)
first_dup = next(find_duplicates_generator(data), None)
\`\`\`

### 파일에서 스트리밍 처리 (초대용량)

\`\`\`python
def find_duplicates_from_file(filepath):
    """파일을 한 줄씩 읽어 메모리 절약"""
    seen = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            item = line.strip()
            if item in seen:
                yield item
            seen.add(item)
\`\`\`

### 메모리 사용량 비교

| 방법 | 메모리 (100만 요소) | 특징 |
|------|-------------------|------|
| Counter | ~80 MB | 전체 카운트 저장 |
| Set 활용 | ~60 MB | seen + result 두 set |
| **제너레이터** | **~40 MB** | lazy evaluation |
| 파일 스트리밍 | **~8 MB** | 파일 기반 처리 |

> 💡 **핵심 포인트**: 제너레이터는 결과를 한 번에 메모리에 올리지 않고 **필요할 때마다 하나씩** 생성합니다. 전체 결과가 필요 없다면 특히 효율적입니다!`,
        },
        {
          role: 'user',
          content: '완벽해요! 정리하자면 성능이 중요하면 Counter, 메모리가 중요하면 제너레이터를 쓰면 되겠군요. 마지막으로 이 함수들에 대한 단위 테스트 코드도 작성해주실 수 있나요?',
          time: '09:28',
          tokens: 61,
        },
        {
          role: 'assistant',
          model: 'claude',
          modelName: 'Claude Sonnet 4',
          time: '09:28',
          tokens: 341,
          content: `정확히 이해하셨습니다! 단위 테스트 코드를 작성해드릴게요.

\`\`\`python
import unittest
from collections import Counter

# 테스트할 함수들 import (같은 파일이나 모듈에서)
# from your_module import find_duplicates_counter, find_duplicates_generator

class TestFindDuplicates(unittest.TestCase):

    def setUp(self):
        """각 테스트 전 공통 데이터 준비"""
        self.normal_list   = [1, 2, 3, 2, 4, 3, 5]
        self.no_dup_list   = [1, 2, 3, 4, 5]
        self.empty_list    = []
        self.all_dup_list  = [1, 1, 1, 1]
        self.string_list   = ['apple', 'banana', 'apple', 'cherry', 'banana']
        self.large_list    = list(range(100_000)) + list(range(50_000))

    # --- Counter 버전 테스트 ---
    def test_counter_finds_duplicates(self):
        result = find_duplicates_counter(self.normal_list)
        self.assertEqual(set(result), {2, 3})

    def test_counter_no_duplicates(self):
        result = find_duplicates_counter(self.no_dup_list)
        self.assertEqual(result, [])

    def test_counter_empty_list(self):
        result = find_duplicates_counter(self.empty_list)
        self.assertEqual(result, [])

    def test_counter_all_duplicates(self):
        result = find_duplicates_counter(self.all_dup_list)
        self.assertEqual(result, [1])

    def test_counter_string_list(self):
        result = find_duplicates_counter(self.string_list)
        self.assertEqual(set(result), {'apple', 'banana'})

    def test_counter_performance(self):
        """100만 요소에서 1초 이내 완료 검증"""
        import time
        start = time.time()
        find_duplicates_counter(self.large_list)
        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0, f"너무 느림: {elapsed:.2f}초")

    # --- 제너레이터 버전 테스트 ---
    def test_generator_finds_duplicates(self):
        result = list(find_duplicates_generator(self.normal_list))
        self.assertEqual(set(result), {2, 3})

    def test_generator_lazy_evaluation(self):
        """제너레이터가 실제로 lazy하게 동작하는지 검증"""
        gen = find_duplicates_generator(self.large_list)
        # 첫 번째 값만 가져와도 전체를 처리하지 않음
        first = next(gen, None)
        self.assertIsNotNone(first)

    def test_generator_empty_list(self):
        result = list(find_duplicates_generator(self.empty_list))
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main(verbosity=2)
\`\`\`

### 실행 결과 예시

\`\`\`
test_counter_all_duplicates ... ok
test_counter_empty_list ... ok
test_counter_finds_duplicates ... ok
test_counter_no_duplicates ... ok
test_counter_performance ... ok
test_counter_string_list ... ok
test_generator_empty_list ... ok
test_generator_finds_duplicates ... ok
test_generator_lazy_evaluation ... ok

Ran 9 tests in 0.312s  OK
\`\`\`

총 9개 테스트로 **엣지 케이스**(빈 리스트, 전체 중복, 문자열)와 **성능 검증**까지 커버합니다. pytest를 사용하신다면 \`pytest test_duplicates.py -v\`로 실행하면 더 예쁜 출력을 볼 수 있어요! ✅`,
        },
      ],
    },

    // 대화 2: 마케팅 이메일 (gpt4o)
    2: {
      model: { id: 'gpt4o', name: 'GPT-4o', provider: 'OpenAI' },
      title: '마케팅 이메일 초안',
      messages: [
        {
          role: 'user',
          content: 'AI 솔루션을 기업 고객에게 소개하는 마케팅 이메일을 작성해줘. 제목도 포함해서.',
          time: '11:05',
          tokens: 33,
        },
        {
          role: 'assistant',
          model: 'gpt4o',
          modelName: 'GPT-4o',
          time: '11:05',
          tokens: 298,
          content: `## 📧 마케팅 이메일 초안

---

**제목**: 귀사의 업무 효율을 3배 높여드립니다 — AI 통합관리 플랫폼 무료 체험

---

안녕하세요, [담당자명] 님

바쁘신 와중에 연락드려 죄송합니다.

저는 **AI Manager** 솔루션을 담당하고 있는 [이름]입니다. 최근 귀사에서 AI 도입을 검토 중이시라는 소식을 접하고 연락드리게 되었습니다.

### 🤔 이런 고민을 하고 계신가요?

- GPT, Claude, Gemini 등 **여러 AI 모델을 따로따로 관리**하느라 불편하신가요?
- AI 사용 비용이 어디서 얼마나 나가는지 **파악이 안 되시나요?**
- 팀원별로 AI 접근 권한을 **체계적으로 관리**하고 싶으신가요?

### ✅ AI Manager가 해결해드립니다

**하나의 플랫폼**에서 모든 AI 모델을 통합 관리하세요.

| 기능 | 효과 |
|------|------|
| 12개 AI 모델 통합 | 모델 전환 시간 **90% 절감** |
| 실시간 비용 모니터링 | AI 운영비용 **평균 40% 절감** |
| 역할 기반 권한 관리 | 보안 사고 **Zero** 달성 |
| 파이프라인 자동화 | 반복 업무 **80% 자동화** |

### 🎁 특별 제안 (이번 달 한정)

**30일 무료 체험** + 전담 온보딩 지원

👉 [무료 체험 시작하기] 버튼

또는 **15분 화상 데모**를 원하신다면 편한 시간을 알려주세요. 직접 시연해드리겠습니다.

감사합니다.

[이름] 드림
AI Manager 영업팀
📞 02-0000-0000 | 📧 sales@aimanager.kr

---
*수신 거부를 원하시면 [여기]를 클릭하세요.*`,
        },
        {
          role: 'user',
          content: '좋은데 좀 더 짧고 캐주얼하게 바꿔줘. 스타트업 느낌으로.',
          time: '11:08',
          tokens: 24,
        },
        {
          role: 'assistant',
          model: 'gpt4o',
          modelName: 'GPT-4o',
          time: '11:08',
          tokens: 185,
          content: `## ⚡ 캐주얼 버전

---

**제목**: AI 12개 모델, 하나로 관리해보셨나요? 👋

---

안녕하세요!

혹시 GPT, Claude, Gemini 쓰면서 **"이거 한 곳에서 관리할 수 없나?"** 생각해본 적 있으신가요?

저희가 딱 그걸 만들었어요 😄

**AI Manager** — 모든 AI를 한 화면에서

✅ 12개 모델 통합 관리
✅ 실시간 비용 추적
✅ 팀 권한 설정
✅ 자동화 파이프라인

복잡한 설정 없이 **30분이면 셋업 완료**입니다.

이번 달까지 **무료 체험** 가능해요. 관심 있으시면 댓글이나 DM 주세요!

👉 **[지금 시작하기]**

---

*P.S. 15분짜리 데모도 해드립니다. 부담 없이 연락주세요 🙌*`,
        },
      ],
    },

    // 대화 3: 데이터 분석 (gemini)
    3: {
      model: { id: 'gemini', name: 'Gemini Pro 1.5', provider: 'Google' },
      title: '재무 데이터 분석 요약',
      messages: [
        {
          role: 'user',
          content: '다음 분기별 매출 데이터를 분석해줘:\nQ1: 1.2억, Q2: 1.8억, Q3: 1.5억, Q4: 2.4억\n전년도: Q1: 0.9억, Q2: 1.1억, Q3: 1.3억, Q4: 1.9억',
          time: '14:32',
          tokens: 73,
        },
        {
          role: 'assistant',
          model: 'gemini',
          modelName: 'Gemini Pro 1.5',
          time: '14:32',
          tokens: 356,
          content: `## 📊 분기별 매출 분석 리포트

### 연간 성과 요약

| 구분 | 올해 | 전년도 | 성장률 |
|------|------|--------|--------|
| Q1 | 1.2억 | 0.9억 | **+33.3%** |
| Q2 | 1.8억 | 1.1억 | **+63.6%** |
| Q3 | 1.5억 | 1.3억 | **+15.4%** |
| Q4 | 2.4억 | 1.9억 | **+26.3%** |
| **연간** | **6.9억** | **5.2억** | **+32.7%** |

### 핵심 인사이트 3가지

#### 1. 📈 전반적 고성장 달성
연간 **32.7% 성장**으로 강한 상승세를 보이고 있습니다. 특히 Q2에서 전년비 **63.6%** 급성장을 기록했습니다.

#### 2. ⚠️ Q3 성장 둔화 주목
Q3에서 Q2 대비 매출이 **1.8억 → 1.5억으로 16.7% 감소**했습니다. 계절적 요인인지 구조적 문제인지 원인 파악이 필요합니다.

#### 3. 🚀 Q4 최고 실적
Q4가 연간 최고 매출(2.4억)을 기록하며 하반기 회복세가 뚜렷합니다. 이 모멘텀을 내년 Q1으로 이어가는 전략이 중요합니다.

### 트렌드 분석

\`\`\`
매출 추이 (단위: 억원)
2.4 |                    ████
1.8 |          ████      ████
1.5 |          ████ ████ ████
1.2 | ████     ████ ████ ████
0.9 |────────────────────────
    Q1   Q2   Q3   Q4
    ■ 올해  □ 전년도
\`\`\`

### 권고사항

1. **Q3 원인 분석** — 비수기 마케팅 강화 또는 신제품 출시 검토
2. **Q4 성장 동력 파악** — 성공 요인을 다른 분기에 적용
3. **내년 목표** — 현재 추세 유지 시 연간 **9억 이상** 달성 가능

> 더 상세한 분석이 필요하시면 제품별 / 지역별 데이터를 공유해주세요!`,
        },
      ],
    },

    // 대화 4: React 컴포넌트 설계 (gpt4o)
    4: {
      model: { id: 'gpt4o', name: 'GPT-4o', provider: 'OpenAI' },
      title: 'React 컴포넌트 설계',
      messages: [
        {
          role: 'user',
          content: '재사용 가능한 React 모달 컴포넌트를 TypeScript로 설계해줘. 사이즈 조절, 오버레이 클릭 닫기, 애니메이션 포함해서.',
          time: '15:44',
          tokens: 48,
        },
        {
          role: 'assistant',
          model: 'gpt4o',
          modelName: 'GPT-4o',
          time: '15:44',
          tokens: 428,
          content: `재사용 가능한 모달 컴포넌트를 설계해드리겠습니다.

### 📁 파일 구조

\`\`\`
components/
├── Modal/
│   ├── Modal.tsx
│   ├── Modal.module.css
│   └── index.ts
\`\`\`

### Modal.tsx

\`\`\`typescript
import React, { useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import styles from './Modal.module.css';

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: ModalSize;
  closeOnOverlay?: boolean;
  closeOnEsc?: boolean;
  className?: string;
}

const sizeMap: Record<ModalSize, string> = {
  sm:   '400px',
  md:   '560px',
  lg:   '720px',
  xl:   '960px',
  full: '95vw',
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeOnOverlay = true,
  closeOnEsc = true,
  className = '',
}) => {
  const overlayRef = useRef<HTMLDivElement>(null);

  // ESC 키 닫기
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (closeOnEsc && e.key === 'Escape') onClose();
  }, [closeOnEsc, onClose]);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden'; // 스크롤 방지
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleKeyDown]);

  // 오버레이 클릭 처리
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlay && e.target === overlayRef.current) onClose();
  };

  if (!isOpen) return null;

  return createPortal(
    <div
      ref={overlayRef}
      className={\`\${styles.overlay} \${isOpen ? styles.open : ''}\`}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      <div
        className={\`\${styles.modal} \${className}\`}
        style={{ maxWidth: sizeMap[size] }}
      >
        {/* Header */}
        {title && (
          <div className={styles.header}>
            <h2 id="modal-title" className={styles.title}>{title}</h2>
            <button className={styles.closeBtn} onClick={onClose} aria-label="닫기">
              ✕
            </button>
          </div>
        )}

        {/* Body */}
        <div className={styles.body}>{children}</div>

        {/* Footer */}
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>,
    document.body
  );
};
\`\`\`

### Modal.module.css (애니메이션 포함)

\`\`\`css
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  animation: fadeIn 0.2s ease forwards;
  padding: 16px;
}

.modal {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  animation: slideUp 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes fadeIn  { to { opacity: 1; } }
@keyframes slideUp {
  from { transform: translateY(30px) scale(0.95); opacity: 0; }
  to   { transform: translateY(0)    scale(1);    opacity: 1; }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.title { font-size: 18px; font-weight: 700; margin: 0; }

.closeBtn {
  width: 32px; height: 32px;
  border: none; background: none; border-radius: 8px;
  font-size: 16px; cursor: pointer; color: #888;
  transition: all 0.15s;
}
.closeBtn:hover { background: #f5f5f5; color: #333; }

.body   { padding: 24px; overflow-y: auto; flex: 1; }
.footer { padding: 16px 24px; border-top: 1px solid #f0f0f0;
          display: flex; justify-content: flex-end; gap: 8px; }
\`\`\`

### 사용 예시

\`\`\`tsx
const [isOpen, setIsOpen] = useState(false);

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="사용자 추가"
  size="lg"
  footer={
    <>
      <button onClick={() => setIsOpen(false)}>취소</button>
      <button onClick={handleSubmit}>저장</button>
    </>
  }
>
  <p>모달 내용이 여기에 들어갑니다.</p>
</Modal>
\`\`\`

**주요 특징**: Portal 렌더링, ESC/오버레이 닫기, 스크롤 잠금, 접근성(aria), 5가지 사이즈, 스프링 애니메이션까지 모두 포함되어 있습니다! 🎉`,
        },
      ],
    },

    // 대화 5: SQL 쿼리 작성 (claude)
    5: {
      model: { id: 'claude', name: 'Claude Sonnet 4', provider: 'Anthropic' },
      title: 'SQL 쿼리 작성 도움',
      messages: [
        {
          role: 'user',
          content: '월별 신규 가입자 수와 유지율(전달 대비 재방문 비율)을 같이 보여주는 SQL 쿼리 짜줘. 테이블은 users(id, created_at)랑 visits(user_id, visited_at) 두 개야.',
          time: '16:10',
          tokens: 67,
        },
        {
          role: 'assistant',
          model: 'claude',
          modelName: 'Claude Sonnet 4',
          time: '16:10',
          tokens: 312,
          content: `월별 신규 가입자와 유지율을 함께 조회하는 쿼리입니다.

\`\`\`sql
WITH
-- 1. 월별 신규 가입자
monthly_signups AS (
  SELECT
    DATE_TRUNC('month', created_at) AS month,
    COUNT(DISTINCT id)              AS new_users
  FROM users
  GROUP BY 1
),

-- 2. 월별 활성 사용자 (방문한 사람)
monthly_active AS (
  SELECT
    DATE_TRUNC('month', visited_at) AS month,
    COUNT(DISTINCT user_id)         AS active_users
  FROM visits
  GROUP BY 1
),

-- 3. 전달 활성 사용자
prev_month_active AS (
  SELECT
    month,
    active_users,
    LAG(active_users) OVER (ORDER BY month) AS prev_active_users
  FROM monthly_active
)

-- 최종 조합
SELECT
  s.month,
  s.new_users,
  p.active_users,
  p.prev_active_users,
  ROUND(
    p.active_users::numeric / NULLIF(p.prev_active_users, 0) * 100, 1
  ) AS retention_rate_pct
FROM monthly_signups    s
LEFT JOIN prev_month_active p ON s.month = p.month
ORDER BY s.month DESC;
\`\`\`

### 결과 예시

| month | new_users | active_users | prev_active | retention_rate |
|-------|-----------|-------------|-------------|----------------|
| 2025-02 | 1,240 | 8,920 | 8,150 | 109.5% |
| 2025-01 | 1,580 | 8,150 | 7,430 | 109.7% |
| 2024-12 | 2,100 | 7,430 | 6,210 | 119.6% |

> **retention_rate_pct > 100%** 인 경우는 신규 유입이 이탈보다 많다는 의미입니다.

### 진짜 유지율 (이탈 제외) 버전

이전 달 사용자 중 이번 달에도 방문한 비율을 보려면:

\`\`\`sql
WITH cohort AS (
  SELECT
    v1.user_id,
    DATE_TRUNC('month', v1.visited_at) AS month,
    DATE_TRUNC('month', v2.visited_at) AS next_month
  FROM visits v1
  LEFT JOIN visits v2
    ON  v1.user_id = v2.user_id
    AND DATE_TRUNC('month', v2.visited_at)
      = DATE_TRUNC('month', v1.visited_at) + INTERVAL '1 month'
)
SELECT
  month,
  COUNT(DISTINCT user_id)               AS users,
  COUNT(DISTINCT CASE WHEN next_month IS NOT NULL THEN user_id END) AS retained,
  ROUND(
    COUNT(DISTINCT CASE WHEN next_month IS NOT NULL THEN user_id END)::numeric
    / NULLIF(COUNT(DISTINCT user_id), 0) * 100, 1
  ) AS true_retention_pct
FROM cohort
GROUP BY month
ORDER BY month DESC;
\`\`\`

어떤 DB를 쓰시나요? MySQL이면 \`DATE_TRUNC\` 대신 \`DATE_FORMAT\`, BigQuery면 그대로 사용 가능합니다! 😊`,
        },
      ],
    },
  };

  // =============================================
  // LOAD EXAMPLE CONVERSATION
  // =============================================
  function loadConversation(id) {
    const conv = EXAMPLE_CONVERSATIONS[id];
    if (!conv) return;

    // Update model selector UI
    state.currentModel = conv.model;
    const modelIconMap = { claude:'brain', gpt4o:'robot', gemini:'gem', finance:'chart-pie' };
    const iconEl  = modelSelectBtn.querySelector('.model-select-icon');
    const nameEl  = modelSelectBtn.querySelector('.model-select-name');
    const provEl  = modelSelectBtn.querySelector('.model-select-provider');
    iconEl.className = `model-select-icon model-${conv.model.id}`;
    iconEl.innerHTML = `<i class="fas fa-${modelIconMap[conv.model.id] || 'brain'}"></i>`;
    nameEl.textContent = conv.model.name;
    provEl.textContent = conv.model.provider;

    // Load messages
    state.messages = conv.messages.map(m => Object.assign({}, m));
    state.totalTokens = state.messages.reduce((sum, m) => sum + (m.tokens || 0), 0);

    // Hide welcome
    if (chatWelcome) chatWelcome.style.display = 'none';

    // Update breadcrumb
    document.getElementById('currentChatName').textContent = conv.title;

    // Render
    renderMessages();
    updateTokenDisplay();
    setTimeout(scrollToBottom, 50);
  }

  // Bind history items to example conversations
  historyItems.forEach(function (item) {
    item.addEventListener('click', function (e) {
      if (e.target.closest('.history-item-del')) return;
      const id = parseInt(this.dataset.id);
      document.querySelectorAll('.history-item').forEach(i => i.classList.remove('history-item-active'));
      this.classList.add('history-item-active');
      loadConversation(id);
    });
  });

  // Auto-load the first (active) conversation on page load
  loadConversation(1);

  // Initialize token display
  updateTokenDisplay();

})();
