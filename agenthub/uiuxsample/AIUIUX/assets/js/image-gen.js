/* =============================================
   간편 이미지 생성기 - JS
   ============================================= */
'use strict';

// ── State ──────────────────────────────────────
const state = {
  model:   'dalle3',
  count:   1,
  size:    '1024x1024',
  quality: 'hd',
  style:   '',
  results: [],
  lbIndex: 0,
  busy:    false,
};

const MODEL_META = {
  dalle3:     { label: 'DALL·E 3',           grad: 'grad-dalle' },
  sdxl:       { label: 'Stable Diffusion XL', grad: 'grad-sdxl'  },
  midjourney: { label: 'Midjourney',          grad: 'grad-mj'    },
  ideogram:   { label: 'Ideogram',            grad: 'grad-id'    },
};

const ICONS = [
  'fa-mountain-sun','fa-city','fa-tree','fa-dragon',
  'fa-cat','fa-house','fa-user-astronaut','fa-coffee',
  'fa-leaf','fa-water','fa-snowflake','fa-sun',
  'fa-fish','fa-dove','fa-gem','fa-rocket',
];

// ── Boot ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  bindModelTabs();
  bindPills();
  bindStyleChips();
  bindGenerateBtn();
  bindResultActions();
  bindLightbox();
  bindSidebar();
});

// ── Model Tabs ─────────────────────────────────
function bindModelTabs() {
  document.querySelectorAll('.ig-model-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.ig-model-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.model = tab.dataset.model;
      syncMeta();
    });
  });
}

// ── Pills ──────────────────────────────────────
function bindPills() {
  // Count
  document.querySelectorAll('.ig-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ig-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.count = parseInt(btn.dataset.count);
      syncMeta();
    });
  });

  // Size
  document.querySelectorAll('.ig-pill-size').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ig-pill-size').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.size = btn.dataset.size;
    });
  });

  // Quality
  document.querySelectorAll('.ig-pill-q').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ig-pill-q').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.quality = btn.dataset.quality;
    });
  });
}

// ── Style Chips ────────────────────────────────
function bindStyleChips() {
  document.querySelectorAll('.ig-style-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.ig-style-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.style = chip.dataset.add || '';
    });
  });
}

// ── Sync subtitle & button meta ────────────────
function syncMeta() {
  const { model, count } = state;
  const label = MODEL_META[model].label;
  const text = `${label} · ${count}장`;

  const subtitle = document.getElementById('modelSubtitle');
  const btnMeta  = document.getElementById('btnMeta');
  if (subtitle) subtitle.textContent = text;
  if (btnMeta)  btnMeta.textContent  = text;
}

// ── Generate ───────────────────────────────────
function bindGenerateBtn() {
  const btn = document.getElementById('btnGenerate');
  if (!btn) return;

  btn.addEventListener('click', startGenerate);

  // Ctrl+Enter shortcut
  document.getElementById('promptInput')?.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      startGenerate();
    }
  });
}

let genTimer = null;

function startGenerate() {
  if (state.busy) return;

  const promptEl = document.getElementById('promptInput');
  const prompt = promptEl?.value.trim() || '';
  if (!prompt) {
    promptEl?.focus();
    shakeInput(promptEl);
    return;
  }

  state.busy = true;

  // UI: loading
  const btn = document.getElementById('btnGenerate');
  const icon = document.getElementById('btnIcon');
  const btnText = document.getElementById('btnText');
  if (btn)     btn.classList.add('loading');
  if (btn)     btn.disabled = true;
  if (icon)    icon.className = 'fas fa-spinner';
  if (btnText) btnText.textContent = '생성 중...';

  // Show progress, hide result
  const progressWrap = document.getElementById('progressWrap');
  const emptyState   = document.getElementById('emptyState');
  const resultGrid   = document.getElementById('resultGrid');
  const resultActions= document.getElementById('resultActions');
  if (progressWrap)   progressWrap.style.display = 'block';
  if (emptyState)     emptyState.style.display = 'none';
  if (resultGrid)     resultGrid.style.display = 'none';
  if (resultActions)  resultActions.style.display = 'none';

  // Animate progress bar
  const fill  = document.getElementById('progressFill');
  const label = document.getElementById('progressLabel');
  const steps = [
    { at: 8,  ms: 0,    text: '프롬프트 분석 중...' },
    { at: 35, ms: 800,  text: '이미지 생성 중...' },
    { at: 72, ms: 1800, text: '디테일 처리 중...' },
    { at: 95, ms: 2600, text: '마무리 중...' },
  ];

  steps.forEach(s => {
    setTimeout(() => {
      if (fill)  fill.style.width = s.at + '%';
      if (label) label.textContent = s.text;
    }, s.ms);
  });

  const totalMs = 3200 + state.count * 200 + Math.random() * 600;

  genTimer = setTimeout(() => {
    finishGenerate(prompt);
  }, totalMs);
}

function finishGenerate(prompt) {
  state.busy = false;

  // Reset button
  const btn     = document.getElementById('btnGenerate');
  const icon    = document.getElementById('btnIcon');
  const btnText = document.getElementById('btnText');
  if (btn)     { btn.classList.remove('loading'); btn.disabled = false; }
  if (icon)    icon.className = 'fas fa-sparkles';
  if (btnText) btnText.textContent = '이미지 생성';

  // Fill to 100% then hide progress
  const fill = document.getElementById('progressFill');
  const progressWrap = document.getElementById('progressWrap');
  if (fill) fill.style.width = '100%';
  setTimeout(() => {
    if (progressWrap) progressWrap.style.display = 'none';
    if (fill) fill.style.width = '0%';
  }, 300);

  // Build results
  state.results = [];
  const styleAdd = state.style ? `, ${state.style}` : '';
  const fullPrompt = prompt + styleAdd;

  for (let i = 0; i < state.count; i++) {
    state.results.push({
      id:      Date.now() + i,
      model:   state.model,
      prompt:  fullPrompt,
      size:    state.size,
      quality: state.quality,
      icon:    ICONS[Math.floor(Math.random() * ICONS.length)],
    });
  }

  renderGrid();
  showToast(`${state.count}장의 이미지가 생성되었습니다!`);
}

// ── Render Grid ────────────────────────────────
function renderGrid() {
  const grid    = document.getElementById('resultGrid');
  const empty   = document.getElementById('emptyState');
  const actions = document.getElementById('resultActions');
  if (!grid) return;

  if (state.results.length === 0) {
    grid.style.display = 'none';
    if (empty)   empty.style.display = 'flex';
    if (actions) actions.style.display = 'none';
    return;
  }

  // Single result → centered
  grid.className = 'ig-result-grid' + (state.results.length === 1 ? ' single' : '');
  grid.style.display = 'grid';
  if (empty)   empty.style.display = 'none';
  if (actions) actions.style.display = 'flex';

  grid.innerHTML = '';
  state.results.forEach((r, idx) => {
    const grad = MODEL_META[r.model]?.grad || 'grad-dalle';
    const card = document.createElement('div');
    card.className = 'ig-result-card';
    card.innerHTML = `
      <div class="ig-card-inner ${grad}">
        <i class="fas ${r.icon}"></i>
      </div>
      <div class="ig-card-hover">
        <button class="ig-card-btn" title="확대" data-action="view"     data-idx="${idx}"><i class="fas fa-expand"></i></button>
        <button class="ig-card-btn" title="다운로드" data-action="dl"   data-idx="${idx}"><i class="fas fa-download"></i></button>
        <button class="ig-card-btn" title="변형" data-action="variant"  data-idx="${idx}"><i class="fas fa-shuffle"></i></button>
        <button class="ig-card-btn" title="삭제" data-action="del"      data-idx="${idx}"><i class="fas fa-trash"></i></button>
      </div>
      <div class="ig-card-num">#${idx + 1}</div>
    `;

    // Card click → lightbox
    card.addEventListener('click', e => {
      const btn = e.target.closest('.ig-card-btn');
      if (!btn) { openLightbox(idx); return; }
      const action = btn.dataset.action;
      const i = parseInt(btn.dataset.idx);
      if (action === 'view')    openLightbox(i);
      else if (action === 'dl') showToast('이미지를 다운로드합니다.');
      else if (action === 'variant') { showToast('변형 이미지를 생성합니다...'); startGenerate(); }
      else if (action === 'del') {
        state.results.splice(i, 1);
        renderGrid();
        showToast('이미지를 삭제했습니다.', 'info');
      }
    });

    grid.appendChild(card);
  });
}

// ── Result Actions ─────────────────────────────
function bindResultActions() {
  document.getElementById('btnDownload')?.addEventListener('click', () => {
    showToast('전체 이미지 다운로드를 시작합니다.');
  });
  document.getElementById('btnRegenerate')?.addEventListener('click', () => {
    startGenerate();
  });
  document.getElementById('btnClear')?.addEventListener('click', () => {
    state.results = [];
    renderGrid();
  });
}

// ── Lightbox ───────────────────────────────────
function bindLightbox() {
  document.getElementById('lbBg')?.addEventListener('click', closeLightbox);
  document.getElementById('lbClose')?.addEventListener('click', closeLightbox);
  document.getElementById('lbPrev')?.addEventListener('click', () => navLightbox(-1));
  document.getElementById('lbNext')?.addEventListener('click', () => navLightbox(1));

  document.getElementById('lbDownload')?.addEventListener('click', () => showToast('이미지를 다운로드합니다.'));
  document.getElementById('lbCopyPrompt')?.addEventListener('click', () => {
    const r = state.results[state.lbIndex];
    if (r) navigator.clipboard?.writeText(r.prompt).then(() => showToast('프롬프트가 복사되었습니다.'));
  });
  document.getElementById('lbVariant')?.addEventListener('click', () => {
    closeLightbox();
    showToast('변형 이미지를 생성합니다...');
    startGenerate();
  });

  document.addEventListener('keydown', e => {
    const lb = document.getElementById('igLightbox');
    if (!lb?.classList.contains('open')) return;
    if (e.key === 'Escape')     closeLightbox();
    if (e.key === 'ArrowLeft')  navLightbox(-1);
    if (e.key === 'ArrowRight') navLightbox(1);
  });
}

function openLightbox(idx) {
  state.lbIndex = idx;
  renderLightbox();
  document.getElementById('igLightbox')?.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  document.getElementById('igLightbox')?.classList.remove('open');
  document.body.style.overflow = '';
}

function navLightbox(dir) {
  state.lbIndex = (state.lbIndex + dir + state.results.length) % state.results.length;
  renderLightbox();
}

function renderLightbox() {
  const r = state.results[state.lbIndex];
  if (!r) return;
  const meta = MODEL_META[r.model];
  const grad = meta?.grad || 'grad-dalle';

  const img = document.getElementById('lbImg');
  if (img) {
    img.className = `ig-lb-img ${grad}`;
    img.innerHTML = `<i class="fas ${r.icon}"></i>`;
  }
  const modelBadge = document.getElementById('lbModel');
  if (modelBadge) modelBadge.textContent = meta?.label || r.model;

  const promptEl = document.getElementById('lbPromptText');
  if (promptEl) promptEl.textContent = r.prompt;
}

// ── Sidebar toggle ─────────────────────────────
function bindSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const wrapper = document.getElementById('mainWrapper');
  toggle?.addEventListener('click', () => {
    sidebar?.classList.toggle('sidebar-collapsed');
    wrapper?.classList.toggle('sidebar-collapsed');
  });
}

// ── Toast ──────────────────────────────────────
let toastTimer = null;
function showToast(msg, type = 'success') {
  const el   = document.getElementById('igToast');
  const text = document.getElementById('toastText');
  const icon = el?.querySelector('i');
  if (!el || !text) return;
  if (toastTimer) clearTimeout(toastTimer);
  text.textContent = msg;
  if (icon) {
    icon.className = type === 'info' ? 'fas fa-circle-info' : 'fas fa-check-circle';
    icon.style.color = type === 'info' ? '#3B82F6' : '#10B981';
  }
  el.classList.add('show');
  toastTimer = setTimeout(() => el.classList.remove('show'), 2600);
}

// ── Shake animation (empty prompt) ─────────────
function shakeInput(el) {
  if (!el) return;
  el.style.borderColor = 'var(--danger)';
  el.style.animation = 'none';
  requestAnimationFrame(() => {
    el.style.animation = 'shakeField 0.35s ease';
  });
  setTimeout(() => {
    el.style.borderColor = '';
    el.style.animation = '';
  }, 800);
}

// Inject shake keyframes
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes shakeField {
    0%,100% { transform: translateX(0); }
    20%     { transform: translateX(-6px); }
    40%     { transform: translateX(6px); }
    60%     { transform: translateX(-4px); }
    80%     { transform: translateX(4px); }
  }
`;
document.head.appendChild(shakeStyle);
