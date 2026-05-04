/* =============================================
   AI 통합관리시스템 - AI Agents 페이지 JS
   ============================================= */
'use strict';

// ── Model options by service ───────────────────
const SERVICE_MODELS = {
  chatgpt:     ['GPT-4o', 'GPT-4o Mini', 'GPT-4 Turbo', 'GPT-3.5 Turbo'],
  claude:      ['Claude Sonnet 4', 'Claude Opus 4', 'Claude Haiku 3.5'],
  gemini:      ['Gemini 1.5 Pro', 'Gemini 1.5 Flash', 'Gemini 2.0 Flash'],
  cursor:      ['Cursor Default'],
  copilot:     ['Copilot Default'],
  mistral:     ['Mistral Large', 'Mistral Medium', 'Mistral Small'],
  dalle:       ['DALL-E 3', 'DALL-E 2'],
  'gemini-image': ['Gemini 3 Pro Image'],
  imagen4:     ['Imagen 4'],
  flux2:       ['Flux 2'],
  'gen4-video':['Gen4 Video'],
  veo:         ['Veo 3.1'],
  'openai-video':['OpenAI Sora'],
};

// Currently edited agent (for edit modal)
let currentEditId = null;
let selectedNewIcon  = 'fa-robot';
let selectedEditIcon = 'fa-robot';
let selectedNewColor  = '#4F46E5';

// ── Boot ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSidebarToggle();
  initSearch();
  initFilters();
  initViewToggle();
  initNewAgentModal();
  initEditModal();
  bindNewAgentBtn();
  updateCount();
});

// ── Sidebar ───────────────────────────────────
function initSidebarToggle() {
  document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('sidebar-collapsed');
    document.getElementById('mainWrapper')?.classList.toggle('sidebar-collapsed');
  });
}

// ── Search ────────────────────────────────────
function initSearch() {
  const input     = document.getElementById('agentSearch');
  const clearBtn  = document.getElementById('searchClear');
  if (!input) return;

  input.addEventListener('input', () => {
    const hasVal = input.value.length > 0;
    if (clearBtn) clearBtn.style.display = hasVal ? 'block' : 'none';
    applyFilters();
  });
  clearBtn?.addEventListener('click', () => {
    input.value = '';
    clearBtn.style.display = 'none';
    applyFilters();
  });
}

// ── Filters ───────────────────────────────────
function initFilters() {
  document.getElementById('serviceFilter')?.addEventListener('change', applyFilters);
  document.getElementById('categoryFilter')?.addEventListener('change', applyFilters);
}

function applyFilters() {
  const query    = (document.getElementById('agentSearch')?.value || '').toLowerCase().trim();
  const service  = document.getElementById('serviceFilter')?.value || '';
  const category = document.getElementById('categoryFilter')?.value || '';

  const cards   = document.querySelectorAll('.ag-grid .ag-card:not(.ag-card-add)');
  let visible = 0;

  cards.forEach(card => {
    const name     = (card.dataset.name     || '').toLowerCase();
    const svc      = (card.dataset.service  || '').toLowerCase();
    const cat      = (card.dataset.category || '').toLowerCase();
    const preview  = (card.querySelector('.ag-system-preview')?.textContent || '').toLowerCase();
    const desc     = (card.querySelector('.ag-card-short, .ag-card-desc')?.textContent || '').toLowerCase();

    const matchQ   = !query   || name.includes(query) || desc.includes(query) || preview.includes(query);
    const matchSvc = !service  || svc === service;
    const matchCat = !category || cat === category;

    const show = matchQ && matchSvc && matchCat;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  });

  // Always show add card
  document.querySelector('.ag-card-add').style.display = '';

  // Empty state
  const empty = document.getElementById('agEmpty');
  const grid  = document.getElementById('agentGrid');
  if (empty && grid) {
    empty.style.display = visible === 0 ? 'flex' : 'none';
    grid.style.display  = visible === 0 ? 'none' : 'grid';
  }

  updateCount(visible);
}

function updateCount(n) {
  const label = document.getElementById('agentCountLabel');
  if (!label) return;
  const cards = document.querySelectorAll('.ag-grid .ag-card:not(.ag-card-add)');
  const total = n !== undefined ? n : cards.length;
  label.innerHTML = `전체 <strong>${total}</strong>개 Agent`;
}

// ── View Toggle ───────────────────────────────
function initViewToggle() {
  document.getElementById('viewGrid')?.addEventListener('click', () => {
    document.getElementById('agentGrid')?.classList.remove('list-view');
    document.getElementById('viewGrid')?.classList.add('active');
    document.getElementById('viewList')?.classList.remove('active');
  });
  document.getElementById('viewList')?.addEventListener('click', () => {
    document.getElementById('agentGrid')?.classList.add('list-view');
    document.getElementById('viewList')?.classList.add('active');
    document.getElementById('viewGrid')?.classList.remove('active');
  });
}

// ── New Agent Modal ───────────────────────────
function bindNewAgentBtn() {
  document.getElementById('btnNewAgent')?.addEventListener('click', openNewAgentModal);
}

function openNewAgentModal() {
  openModal('modalNewAgent');
}

function initNewAgentModal() {
  // Service → Model cascade
  const svcSel = document.getElementById('newAgentService');
  const mdlSel = document.getElementById('newAgentModel');
  svcSel?.addEventListener('change', () => {
    populateModels(svcSel.value, mdlSel);
  });

  // Temperature slider
  const tempSlider = document.getElementById('newTempSlider');
  const tempVal    = document.getElementById('newTempVal');
  tempSlider?.addEventListener('input', () => {
    if (tempVal) tempVal.textContent = parseFloat(tempSlider.value).toFixed(1);
    updateSliderGradient(tempSlider);
  });

  // Prompt char count
  const promptTA = document.getElementById('newAgentPrompt');
  const charCount = document.getElementById('promptCharCount');
  promptTA?.addEventListener('input', () => {
    if (charCount) charCount.textContent = promptTA.value.length;
  });

  // Icon picker
  initIconPicker('iconPicker', (icon) => { selectedNewIcon = icon; });

  // Color picker
  initColorPicker('colorPicker', (color) => { selectedNewColor = color; });
}

// ── Edit Agent Modal ──────────────────────────
function initEditModal() {
  const svcSel = document.getElementById('editAgentService');
  const mdlSel = document.getElementById('editAgentModel');
  svcSel?.addEventListener('change', () => populateModels(svcSel.value, mdlSel));

  const slider = document.getElementById('editTempSlider');
  const val    = document.getElementById('editTempVal');
  slider?.addEventListener('input', () => {
    if (val) val.textContent = parseFloat(slider.value).toFixed(1);
    updateSliderGradient(slider);
  });

  initIconPicker('editIconPicker', (icon) => { selectedEditIcon = icon; });
}

// ── Icon Picker Helper ────────────────────────
function initIconPicker(pickerId, onChange) {
  const picker = document.getElementById(pickerId);
  if (!picker) return;
  picker.querySelectorAll('.ag-icon-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      picker.querySelectorAll('.ag-icon-opt').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      onChange(btn.dataset.icon);
    });
  });
}

// ── Color Picker Helper ───────────────────────
function initColorPicker(pickerId, onChange) {
  const picker = document.getElementById(pickerId);
  if (!picker) return;
  picker.querySelectorAll('.ag-color-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      picker.querySelectorAll('.ag-color-opt').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      onChange(btn.dataset.color);
    });
  });
}

// ── Model cascade ─────────────────────────────
function populateModels(service, selectEl) {
  if (!selectEl) return;
  const models = SERVICE_MODELS[service] || [];
  selectEl.innerHTML = '';
  if (models.length === 0) {
    selectEl.innerHTML = '<option value="">모델 없음</option>';
    selectEl.disabled = true;
    return;
  }
  selectEl.disabled = false;
  models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.toLowerCase().replace(/\s/g, '-');
    opt.textContent = m;
    selectEl.appendChild(opt);
  });
}

// ── Slider gradient sync ──────────────────────
function updateSliderGradient(slider) {
  const min = parseFloat(slider.min), max = parseFloat(slider.max), val = parseFloat(slider.value);
  const pct = ((val - min) / (max - min)) * 100;
  slider.style.background = `linear-gradient(to right, var(--primary) ${pct}%, var(--border) ${pct}%)`;
}

// ── Create Agent ──────────────────────────────
function createAgent() {
  const name    = document.getElementById('newAgentName')?.value.trim();
  const desc    = document.getElementById('newAgentDesc')?.value.trim();
  const service = document.getElementById('newAgentService')?.value;
  const model   = document.getElementById('newAgentModel')?.value;
  const prompt  = document.getElementById('newAgentPrompt')?.value.trim();

  // Validation
  if (!name)    { shakeEl('newAgentName'); return; }
  if (!service) { shakeEl('newAgentService'); return; }
  if (!prompt)  { shakeEl('newAgentPrompt'); return; }

  const temp      = parseFloat(document.getElementById('newTempSlider')?.value || '0.7').toFixed(1);
  const maxTokens = document.getElementById('newMaxTokens')?.value || '2048';
  const isPublic  = document.getElementById('newIsPublic')?.checked;
  const ragEnabled= document.getElementById('newEnableRag')?.checked;
  const modelLabel= document.getElementById('newAgentModel')?.options[document.getElementById('newAgentModel').selectedIndex]?.text || '';

  // Build new card and inject into grid
  addAgentCard({
    name, desc: desc || '커스텀 Agent', service, modelLabel,
    prompt, temp, maxTokens, isPublic, ragEnabled,
    icon: selectedNewIcon, color: selectedNewColor,
  });

  closeModal('modalNewAgent');
  resetNewForm();
  showToast(`"${name}" Agent가 생성되었습니다!`);
}

function addAgentCard({ name, desc, service, modelLabel, prompt, icon, color }) {
  const grid = document.getElementById('agentGrid');
  const addCard = document.getElementById('cardAddAgent');
  if (!grid || !addCard) return;

  // Determine text color based on luminance
  const textColor = isLightColor(color) ? '#212529' : '#ffffff';
  const id = 'agent-' + Date.now();

  const card = document.createElement('div');
  card.className = 'ag-card';
  card.dataset.name = name;
  card.dataset.service = service;
  card.dataset.category = 'custom';
  card.style.cssText = `--ag-color:${color}; --ag-text:${textColor};`;
  card.id = id;

  card.innerHTML = `
    <div class="ag-card-ribbon">커스텀</div>
    <div class="ag-card-body">
      <div class="ag-icon-wrap ag-icon-dynamic">
        <i class="fas ${icon}"></i>
      </div>
      <h5 class="ag-card-title">${escHtml(name)}</h5>
      <p class="ag-card-short">${escHtml(desc)}</p>
      <div class="ag-model-badge">
        <i class="fas fa-microchip"></i> ${escHtml(modelLabel || '모델 미지정')}
      </div>
      <div class="ag-system-preview">${escHtml(prompt)}</div>
    </div>
    <div class="ag-card-footer ag-footer-flex">
      <button class="ag-btn-start ag-btn-dynamic" onclick="startAgent('${id}')">
        <i class="fas fa-play"></i> 실행하기
      </button>
      <button class="ag-btn-edit" onclick="editAgent('${id}')" title="Agent 수정">
        <i class="fas fa-pencil"></i>
      </button>
    </div>
  `;

  // Hover effect
  card.addEventListener('mouseenter', () => { card.style.borderColor = color; });
  card.addEventListener('mouseleave', () => { card.style.borderColor = ''; });

  grid.insertBefore(card, addCard);
  updateCount();
}

function resetNewForm() {
  ['newAgentName','newAgentDesc','newAgentPrompt','newMaxTokens'].forEach(id => {
    const el = document.getElementById(id);
    if (el) { if (el.tagName === 'INPUT' && el.type === 'number') el.value = '2048'; else el.value = ''; }
  });
  const svc = document.getElementById('newAgentService');
  const mdl = document.getElementById('newAgentModel');
  if (svc) svc.value = '';
  if (mdl) { mdl.innerHTML = '<option value="">서비스를 먼저 선택하세요</option>'; mdl.disabled = true; }
  const slider = document.getElementById('newTempSlider');
  const val    = document.getElementById('newTempVal');
  if (slider) { slider.value = '0.7'; updateSliderGradient(slider); }
  if (val)    val.textContent = '0.7';
  const cnt = document.getElementById('promptCharCount');
  if (cnt) cnt.textContent = '0';
  selectedNewIcon  = 'fa-robot';
  selectedNewColor = '#4F46E5';
  document.querySelectorAll('#iconPicker .ag-icon-opt').forEach((b,i) => b.classList.toggle('active', i===0));
  document.querySelectorAll('#colorPicker .ag-color-opt').forEach((b,i) => b.classList.toggle('active', i===0));
}

// ── Edit Agent ────────────────────────────────
window.editAgent = function(agentId) {
  currentEditId = agentId;

  // Try to find card and pre-fill
  const card = document.getElementById(agentId) || document.querySelector(`[data-name]`);
  const nameEl   = document.getElementById('editAgentName');
  const descEl   = document.getElementById('editAgentDesc');
  const promptEl = document.getElementById('editAgentPrompt');

  if (card) {
    const title   = card.querySelector('.ag-card-title')?.textContent || '';
    const short   = card.querySelector('.ag-card-short')?.textContent || '';
    const preview = card.querySelector('.ag-system-preview')?.textContent || '';
    if (nameEl)   nameEl.value   = title;
    if (descEl)   descEl.value   = short;
    if (promptEl) promptEl.value = preview;
  }

  const slider = document.getElementById('editTempSlider');
  if (slider) updateSliderGradient(slider);

  openModal('modalEditAgent');
};

function saveAgent() {
  const name = document.getElementById('editAgentName')?.value.trim();
  if (!name) { shakeEl('editAgentName'); return; }

  // Update card if it exists
  if (currentEditId) {
    const card = document.getElementById(currentEditId);
    if (card) {
      const titleEl = card.querySelector('.ag-card-title');
      const shortEl = card.querySelector('.ag-card-short');
      const prevEl  = card.querySelector('.ag-system-preview');
      const desc  = document.getElementById('editAgentDesc')?.value.trim();
      const prompt= document.getElementById('editAgentPrompt')?.value.trim();
      if (titleEl) titleEl.textContent = name;
      if (shortEl && desc) shortEl.textContent = desc;
      if (prevEl  && prompt) prevEl.textContent = prompt;
      card.dataset.name = name;
    }
  }

  closeModal('modalEditAgent');
  showToast(`Agent가 수정되었습니다.`);
}

// ── Start Agent ───────────────────────────────
window.startAgent = function(agentId) {
  const nameMap = {
    default:      '기본 모드',
    idino:        '아이디노 도우미',
    dictionary:   '전공단어사전',
    english:      '영어선생님',
    codereview:   '코드 리뷰 Agent',
    docs:         '문서 작성 Agent',
    dataanalysis: '데이터 분석 Agent',
    support:      '고객 지원 Agent',
    translate:    '번역 Agent',
  };
  const name = nameMap[agentId] || agentId;
  showToast(`"${name}" Agent를 시작합니다...`);
  setTimeout(() => { window.location.href = 'chat.html'; }, 800);
};

// ── Reset Filters ─────────────────────────────
window.resetFilters = function() {
  const search = document.getElementById('agentSearch');
  const svc    = document.getElementById('serviceFilter');
  const cat    = document.getElementById('categoryFilter');
  const clrBtn = document.getElementById('searchClear');
  if (search) search.value = '';
  if (svc)    svc.value    = '';
  if (cat)    cat.value    = '';
  if (clrBtn) clrBtn.style.display = 'none';
  applyFilters();
};

// ── Modal open/close ──────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
  document.body.style.overflow = 'hidden';
}

window.closeModal = function(id) {
  document.getElementById(id)?.classList.remove('open');
  document.body.style.overflow = '';
};

// Close on backdrop click
document.addEventListener('click', e => {
  if (e.target.classList.contains('ag-modal-overlay')) {
    e.target.classList.remove('open');
    document.body.style.overflow = '';
  }
});

// ESC close
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.ag-modal-overlay.open').forEach(m => {
      m.classList.remove('open');
      document.body.style.overflow = '';
    });
  }
});

// ── Toast ──────────────────────────────────────
let toastTimer = null;
function showToast(msg, type = 'success') {
  const el   = document.getElementById('agToast');
  const text = document.getElementById('agToastText');
  const icon = el?.querySelector('i');
  if (!el || !text) return;
  if (toastTimer) clearTimeout(toastTimer);
  text.textContent = msg;
  if (icon) {
    icon.className = type === 'warn' ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle';
    icon.style.color = type === 'warn' ? '#F59E0B' : '#10B981';
  }
  el.classList.add('show');
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}

// ── Shake animation ───────────────────────────
function shakeEl(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.style.borderColor = 'var(--danger)';
  el.animate([
    { transform: 'translateX(0)' },
    { transform: 'translateX(-6px)' },
    { transform: 'translateX(6px)' },
    { transform: 'translateX(-4px)' },
    { transform: 'translateX(0)' },
  ], { duration: 320, easing: 'ease' });
  setTimeout(() => { el.style.borderColor = ''; }, 600);
  el.focus();
}

// ── Utils ──────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function isLightColor(hex) {
  const c = hex.replace('#','');
  const r = parseInt(c.substring(0,2),16);
  const g = parseInt(c.substring(2,4),16);
  const b = parseInt(c.substring(4,6),16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 155;
}
