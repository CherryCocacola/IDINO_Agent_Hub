/* =============================================
   이미지 생성 페이지 - image-create.js
   ============================================= */

/* ── Service → Models map ── */
const IC_SERVICES = {
  dalle: {
    label: 'DALL-E 3',
    color: '#10B981',
    models: ['dall-e-3', 'dall-e-2'],
    costPer: 0.040,
    supportMultiple: false
  },
  'gemini-img': {
    label: 'Gemini 3 Pro Image',
    color: '#3B82F6',
    models: ['gemini-3-pro-image-preview', 'gemini-2.5-flash-image'],
    costPer: 0.030,
    supportMultiple: true
  },
  imagen4: {
    label: 'Imagen 4',
    color: '#059669',
    models: ['imagen-4', 'imagen-4-ultra', 'imagen-3'],
    costPer: 0.020,
    supportMultiple: true
  },
  'gen4-img': {
    label: 'Gen4 Image',
    color: '#6D28D9',
    models: ['gen4-image', 'gen4-image-fast'],
    costPer: 0.050,
    supportMultiple: false
  },
  flux2: {
    label: 'Flux 2',
    color: '#B45309',
    models: ['flux-2-pro', 'flux-2', 'flux-1-schnell'],
    costPer: 0.015,
    supportMultiple: true
  }
};

/* ── Quality multipliers ── */
const IC_QUALITY_MULT = { standard: 1, hd: 1.5 };

/* ── Size labels ── */
const IC_SIZE_LABELS = {
  '1024x1024': { cls: '',          label: '1024×1024 · 정사각형' },
  '1792x1024': { cls: 'landscape', label: '1792×1024 · 가로' },
  '1024x1792': { cls: 'portrait',  label: '1024×1792 · 세로' },
  '512x512':   { cls: 'small',     label: '512×512 · 소형' }
};

/* ── Sample gradient placeholders (simulate generated images) ── */
const IC_GRADIENTS = [
  'linear-gradient(135deg,#667eea,#764ba2)',
  'linear-gradient(135deg,#f093fb,#f5576c)',
  'linear-gradient(135deg,#4facfe,#00f2fe)',
  'linear-gradient(135deg,#43e97b,#38f9d7)',
  'linear-gradient(135deg,#fa709a,#fee140)',
  'linear-gradient(135deg,#a18cd1,#fbc2eb)',
  'linear-gradient(135deg,#fccb90,#d57eeb)',
  'linear-gradient(135deg,#a1c4fd,#c2e9fb)',
  'linear-gradient(135deg,#fd7043,#ff8a65)',
  'linear-gradient(135deg,#26a69a,#00897b)'
];

/* ── State ── */
let icState = {
  service: '',
  model: '',
  prompt: '',
  size: '1024x1024',
  quality: 'standard',
  count: 1,
  results: [],       // [{ gradient, label, prompt, model, time, ms, cost }]
  lbIndex: 0,
  generating: false
};

/* ─────────────────────────────────────────
   INIT
───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setupService();
  setupPrompt();
  setupSizeGrid();
  setupCount();
  setupQuality();
  setupForm();
  setupLightbox();
  updateCost();
});

/* ─────────────────────────────────────────
   SERVICE SELECT
───────────────────────────────────────── */
function setupService() {
  const sel = document.getElementById('icService');
  sel.addEventListener('change', () => {
    icState.service = sel.value;
    populateModels(sel.value);
    updateCost();
    // If service doesn't support multiple, cap count at 1
    if (sel.value && !IC_SERVICES[sel.value]?.supportMultiple) {
      setCount(1);
      document.getElementById('icCountUp').disabled = true;
      document.getElementById('icCountDown').disabled = true;
      document.getElementById('icCount').disabled = true;
    } else {
      document.getElementById('icCountUp').disabled = false;
      document.getElementById('icCountDown').disabled = false;
      document.getElementById('icCount').disabled = false;
    }
  });
}

function populateModels(svcKey) {
  const modelSel = document.getElementById('icModel');
  modelSel.innerHTML = '<option value="">기본 모델 사용</option>';
  if (!svcKey || !IC_SERVICES[svcKey]) return;
  IC_SERVICES[svcKey].models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    modelSel.appendChild(opt);
  });
  modelSel.addEventListener('change', () => {
    icState.model = modelSel.value;
  });
}

/* ─────────────────────────────────────────
   PROMPT
───────────────────────────────────────── */
function setupPrompt() {
  const ta = document.getElementById('icPrompt');
  const cnt = document.getElementById('icCharCount');
  ta.addEventListener('input', () => {
    icState.prompt = ta.value;
    cnt.textContent = ta.value.length;
  });
}

/* ─────────────────────────────────────────
   SIZE GRID
───────────────────────────────────────── */
function setupSizeGrid() {
  document.querySelectorAll('.ic-size-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ic-size-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      icState.size = btn.dataset.val;
      updateCost();
    });
  });
}

/* ─────────────────────────────────────────
   COUNT
───────────────────────────────────────── */
function setupCount() {
  const input = document.getElementById('icCount');
  document.getElementById('icCountDown').addEventListener('click', () => setCount(icState.count - 1));
  document.getElementById('icCountUp').addEventListener('click', () => setCount(icState.count + 1));
  input.addEventListener('change', () => setCount(parseInt(input.value) || 1));
}

function setCount(n) {
  n = Math.max(1, Math.min(10, n));
  icState.count = n;
  document.getElementById('icCount').value = n;
  updateCost();
}

/* ─────────────────────────────────────────
   QUALITY
───────────────────────────────────────── */
function setupQuality() {
  document.getElementById('icQuality').addEventListener('change', function() {
    icState.quality = this.value;
    updateCost();
  });
}

/* ─────────────────────────────────────────
   COST ESTIMATE
───────────────────────────────────────── */
function updateCost() {
  const svc = IC_SERVICES[icState.service];
  const base = svc ? svc.costPer : 0;
  const qMult = IC_QUALITY_MULT[icState.quality] || 1;
  const total = base * qMult * icState.count;
  document.getElementById('icCostVal').textContent = total > 0
    ? '$' + total.toFixed(4)
    : '$0.0000';
}

/* ─────────────────────────────────────────
   FORM SUBMIT
───────────────────────────────────────── */
function setupForm() {
  document.getElementById('icForm').addEventListener('submit', e => {
    e.preventDefault();
    if (icState.generating) return;

    const svc = document.getElementById('icService').value;
    const prompt = document.getElementById('icPrompt').value.trim();

    if (!svc) { shakeEl(document.getElementById('icService')); showToast('서비스를 선택해주세요.', 'warn'); return; }
    if (!prompt) { shakeEl(document.getElementById('icPrompt')); showToast('프롬프트를 입력해주세요.', 'warn'); return; }

    startGenerate(svc, prompt);
  });
}

function startGenerate(svc, prompt) {
  icState.generating = true;
  icState.service = svc;
  icState.prompt = prompt;

  // UI: loading
  const btn = document.getElementById('icSubmitBtn');
  btn.disabled = true;
  btn.classList.add('ic-generating');
  document.getElementById('icSubmitText').textContent = '생성 중...';

  document.getElementById('icEmptyState').style.display = 'none';
  document.getElementById('icResultGrid').style.display = 'none';
  document.getElementById('icDownloadAll').style.display = 'none';
  document.getElementById('icLoadingState').style.display = 'flex';

  // Update loading text
  const msgs = [
    '이미지를 생성하는 중입니다...',
    'AI가 프롬프트를 분석하고 있어요...',
    '픽셀 하나하나를 그리는 중입니다...',
    '거의 다 됐어요! 마무리 중...'
  ];
  let mIdx = 0;
  const msgTimer = setInterval(() => {
    mIdx = (mIdx + 1) % msgs.length;
    document.getElementById('icLoadingText').textContent = msgs[mIdx];
  }, 1800);

  const startMs = Date.now();
  const delay = 3000 + Math.random() * 3000;

  setTimeout(() => {
    clearInterval(msgTimer);
    const elapsed = Date.now() - startMs;
    finishGenerate(svc, prompt, elapsed);
  }, delay);
}

function finishGenerate(svcKey, prompt, elapsedMs) {
  const svc = IC_SERVICES[svcKey];
  const count = icState.count;
  const quality = icState.quality;
  const size = icState.size;
  const model = document.getElementById('icModel').value || (svc?.models[0] || '기본 모델');

  const qMult = IC_QUALITY_MULT[quality] || 1;
  const costEach = (svc?.costPer || 0.030) * qMult;
  const totalCost = costEach * count;

  // Build results
  icState.results = [];
  for (let i = 0; i < count; i++) {
    icState.results.push({
      gradient: IC_GRADIENTS[(Math.floor(Math.random() * IC_GRADIENTS.length))],
      label: `이미지 ${i + 1}`,
      prompt,
      model,
      size,
      quality,
      time: formatDateTime(),
      ms: elapsedMs,
      cost: costEach
    });
  }

  // Hide loading
  document.getElementById('icLoadingState').style.display = 'none';

  // Render grid
  renderResultGrid(count, size);

  // Gen info
  document.getElementById('icGenInfo').innerHTML = `
    <div class="ic-gen-info-grid">
      <div class="ic-gen-info-item">
        <div class="ic-gen-info-label">프롬프트</div>
        <div class="ic-gen-info-val">${escHtml(prompt)}</div>
      </div>
      <div class="ic-gen-info-item">
        <div class="ic-gen-info-label">모델</div>
        <div class="ic-gen-info-val">${escHtml(model)}</div>
      </div>
      <div class="ic-gen-info-item">
        <div class="ic-gen-info-label">생성 시간</div>
        <div class="ic-gen-info-val">${formatDateTime()}</div>
      </div>
      <div class="ic-gen-info-item">
        <div class="ic-gen-info-label">응답 시간</div>
        <div class="ic-gen-info-val">${elapsedMs.toLocaleString()}ms</div>
      </div>
      <div class="ic-gen-info-item">
        <div class="ic-gen-info-label">크기 · 품질</div>
        <div class="ic-gen-info-val">${size} · ${quality === 'hd' ? 'HD (고화질)' : 'Standard'}</div>
      </div>
      <div class="ic-gen-info-item">
        <div class="ic-gen-info-label">총 비용</div>
        <div class="ic-gen-info-val" style="color:var(--primary);font-weight:700;">$${totalCost.toFixed(4)}</div>
      </div>
    </div>
  `;

  document.getElementById('icResultGrid').style.display = 'block';
  if (count > 1) document.getElementById('icDownloadAll').style.display = 'inline-flex';

  // Reset button
  const btn = document.getElementById('icSubmitBtn');
  btn.disabled = false;
  btn.classList.remove('ic-generating');
  document.getElementById('icSubmitText').textContent = '다시 생성';
  icState.generating = false;

  showToast(`이미지 ${count}장 생성 완료!`);
}

function renderResultGrid(count, size) {
  const sizeInfo = IC_SIZE_LABELS[size] || IC_SIZE_LABELS['1024x1024'];
  const colClass = count === 1 ? 'col-12' : 'col-md-6';

  const grid = document.getElementById('icImageGrid');
  grid.innerHTML = icState.results.map((r, idx) => `
    <div class="${colClass}">
      <div class="ic-img-card">
        <div class="ic-img-thumb-wrap ${sizeInfo.cls}" data-idx="${idx}" onclick="openLightbox(${idx})">
          <div class="ic-img-thumb" style="background:${r.gradient};position:absolute;inset:0;"></div>
          <button class="ic-img-zoom-btn" onclick="openLightbox(${idx}); event.stopPropagation();">
            <i class="fas fa-expand"></i>
          </button>
        </div>
        <div class="ic-img-card-body">
          <span class="ic-img-label">${r.label}</span>
          <button class="btn btn-sm btn-outline-primary ic-img-download-btn" onclick="downloadImage(${idx})">
            <i class="fas fa-download me-1"></i>다운로드
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

/* ─────────────────────────────────────────
   LIGHTBOX
───────────────────────────────────────── */
function setupLightbox() {
  document.getElementById('icLbClose').addEventListener('click', closeLightbox);
  document.getElementById('icLbBackdrop').addEventListener('click', closeLightbox);
  document.getElementById('icLbPrev').addEventListener('click', () => navLightbox(-1));
  document.getElementById('icLbNext').addEventListener('click', () => navLightbox(1));
  document.getElementById('icLbDownload').addEventListener('click', () => downloadImage(icState.lbIndex));
  document.getElementById('icDownloadAll').addEventListener('click', downloadAll);

  document.addEventListener('keydown', e => {
    const lb = document.getElementById('icLightbox');
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') navLightbox(-1);
    if (e.key === 'ArrowRight') navLightbox(1);
  });
}

function openLightbox(idx) {
  if (!icState.results.length) return;
  icState.lbIndex = idx;
  renderLightbox();
  document.getElementById('icLightbox').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeLightbox() {
  document.getElementById('icLightbox').classList.remove('open');
  document.body.style.overflow = '';
}

function navLightbox(dir) {
  const len = icState.results.length;
  icState.lbIndex = (icState.lbIndex + dir + len) % len;
  renderLightbox();
}

function renderLightbox() {
  const r = icState.results[icState.lbIndex];
  if (!r) return;

  // Use a canvas-drawn gradient as a data URL to simulate an image
  const canvas = document.createElement('canvas');
  canvas.width = 800; canvas.height = 800;
  const ctx = canvas.getContext('2d');

  // Parse simple gradient colors from the gradient string
  const match = r.gradient.match(/#[0-9a-fA-F]{3,6}/g) || ['#667eea','#764ba2'];
  const grad = ctx.createLinearGradient(0, 0, 800, 800);
  grad.addColorStop(0, match[0]);
  grad.addColorStop(1, match[1] || match[0]);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 800, 800);

  // Overlay prompt text
  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  ctx.font = 'bold 22px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(r.prompt.slice(0, 40) + (r.prompt.length > 40 ? '...' : ''), 400, 400);

  document.getElementById('icLbImg').src = canvas.toDataURL('image/png');
  document.getElementById('icLbLabel').textContent =
    `${r.label} · ${IC_SIZE_LABELS[r.size]?.label || r.size}`;

  // Show/hide nav
  document.getElementById('icLbPrev').style.display = icState.results.length > 1 ? 'flex' : 'none';
  document.getElementById('icLbNext').style.display = icState.results.length > 1 ? 'flex' : 'none';
}

/* ─────────────────────────────────────────
   DOWNLOAD
───────────────────────────────────────── */
function downloadImage(idx) {
  const r = icState.results[idx];
  if (!r) return;

  const canvas = document.createElement('canvas');
  const [w, h] = (r.size || '1024x1024').split('x').map(Number);
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext('2d');
  const match = r.gradient.match(/#[0-9a-fA-F]{3,6}/g) || ['#667eea','#764ba2'];
  const grad = ctx.createLinearGradient(0, 0, w, h);
  grad.addColorStop(0, match[0]);
  grad.addColorStop(1, match[1] || match[0]);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  canvas.toBlob(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `generated-image-${idx + 1}.png`;
    a.click();
    URL.revokeObjectURL(url);
  });

  showToast(`이미지 ${idx + 1} 다운로드 완료`);
}

function downloadAll() {
  icState.results.forEach((_, idx) => {
    setTimeout(() => downloadImage(idx), idx * 300);
  });
  showToast('전체 다운로드 시작');
}

/* ─────────────────────────────────────────
   HELPERS
───────────────────────────────────────── */
function escHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}

function formatDateTime() {
  return new Date().toLocaleString('ko-KR');
}

function shakeEl(el) {
  el.classList.add('ic-shake');
  setTimeout(() => el.classList.remove('ic-shake'), 500);
}

function showToast(msg, type = 'success') {
  const toast = document.getElementById('icToast');
  const icon  = toast.querySelector('i');
  document.getElementById('icToastText').textContent = msg;
  icon.className = type === 'warn'
    ? 'fas fa-exclamation-circle'
    : 'fas fa-check-circle';
  icon.style.color = type === 'warn' ? '#F59E0B' : '#10B981';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

/* Shake animation (injected dynamically to avoid extra CSS) */
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes icShake {
    0%,100%{transform:translateX(0)}
    20%{transform:translateX(-6px)}
    40%{transform:translateX(6px)}
    60%{transform:translateX(-4px)}
    80%{transform:translateX(4px)}
  }
  .ic-shake { animation: icShake 0.45s ease; border-color: var(--danger) !important; }
`;
document.head.appendChild(shakeStyle);

/* Sidebar toggle */
const sidebarToggle = document.getElementById('sidebarToggle');
if (sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
}
