/* =============================================
   간편 이미지 - quick-image.js
   ============================================= */
'use strict';

/* ─── Gradient palette ─────────────────────── */
const QI_GRADIENTS = [
  ['#667eea', '#764ba2'],
  ['#f093fb', '#f5576c'],
  ['#4facfe', '#00f2fe'],
  ['#43e97b', '#38f9d7'],
  ['#fa709a', '#fee140'],
  ['#a18cd1', '#fbc2eb'],
  ['#fccb90', '#d57eeb'],
  ['#a1c4fd', '#c2e9fb'],
  ['#fd7043', '#ff8a65'],
  ['#26c6da', '#00acc1'],
];

/* ─── State ────────────────────────────────── */
let qiState = {
  generating: false,
  prompt:     '',
  gradIdx:    0,
};

/* ─── DOM refs ──────────────────────────────── */
const $ = id => document.getElementById(id);

/* ─── Init ──────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setupCharCount();
  setupSubmit();
  setupDownload();
});

/* ─── Char count ─────────────────────────────── */
function setupCharCount() {
  const ta = $('qiPrompt');
  const counter = $('qiCharCount');
  if (!ta || !counter) return;
  ta.addEventListener('input', () => {
    const len = ta.value.length;
    counter.textContent = len;
    if (len > 1000) ta.value = ta.value.substring(0, 1000);
  });
  ta.addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleGenerate();
    }
  });
}

/* ─── Submit ────────────────────────────────── */
function setupSubmit() {
  const btn = $('qiSubmitBtn');
  if (btn) btn.addEventListener('click', handleGenerate);
}

function handleGenerate() {
  if (qiState.generating) return;

  const prompt = $('qiPrompt').value.trim();
  if (!prompt) {
    $('qiPrompt').focus();
    $('qiPrompt').style.borderColor = '#EF4444';
    setTimeout(() => { $('qiPrompt').style.borderColor = ''; }, 1800);
    return;
  }

  qiState.prompt  = prompt;
  qiState.gradIdx = Math.floor(Math.random() * QI_GRADIENTS.length);
  startGenerate();
}

/* ─── Loading ───────────────────────────────── */
function startGenerate() {
  qiState.generating = true;

  // UI: disable button
  const btn  = $('qiSubmitBtn');
  const text = $('qiSubmitText');
  btn.disabled = true;
  text.textContent = '생성 중...';

  // Show loading
  $('qiEmptyState').style.display   = 'none';
  $('qiImageWrap').style.display    = 'none';
  $('qiLoadingState').style.display = 'flex';
  $('qiDownloadBtn').style.display  = 'none';

  // Animate progress bar
  const bar = $('qiLoadingBar');
  bar.style.width = '0%';

  const targets = [20, 45, 70, 88, 95];
  let tIdx = 0;
  const barTimer = setInterval(() => {
    if (tIdx < targets.length) {
      bar.style.width = targets[tIdx] + '%';
      tIdx++;
    } else {
      clearInterval(barTimer);
    }
  }, 400);

  // Simulate generation time (1.5 ~ 2.5s)
  const delay = 1500 + Math.random() * 1000;
  setTimeout(() => {
    clearInterval(barTimer);
    bar.style.width = '100%';
    setTimeout(() => finishGenerate(), 300);
  }, delay);
}

/* ─── Finish ────────────────────────────────── */
function finishGenerate() {
  qiState.generating = false;

  // Re-enable button
  $('qiSubmitBtn').disabled = false;
  $('qiSubmitText').textContent = '이미지 생성';

  // Hide loading, show image
  $('qiLoadingState').style.display = 'none';
  $('qiImageWrap').style.display    = 'block';
  $('qiDownloadBtn').style.display  = 'flex';

  // Render canvas
  renderCanvas();

  // Caption
  $('qiCaption').textContent = qiState.prompt.length > 60
    ? qiState.prompt.substring(0, 60) + '...'
    : qiState.prompt;

  // Toast
  showToast('이미지 생성 완료!');
}

/* ─── Canvas render ─────────────────────────── */
function renderCanvas() {
  const canvas = $('qiCanvas');
  const ctx    = canvas.getContext('2d');
  const W = 800;
  const H = 600;
  canvas.width  = W;
  canvas.height = H;

  const [c1, c2] = QI_GRADIENTS[qiState.gradIdx];
  const grad = ctx.createLinearGradient(0, 0, W, H);
  grad.addColorStop(0, c1);
  grad.addColorStop(1, c2);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // Decorative circles
  ctx.globalAlpha = 0.15;
  const circles = [
    { x: W * 0.15, y: H * 0.2,  r: 140 },
    { x: W * 0.82, y: H * 0.75, r: 180 },
    { x: W * 0.5,  y: H * 0.5,  r: 90  },
    { x: W * 0.7,  y: H * 0.15, r: 60  },
    { x: W * 0.2,  y: H * 0.85, r: 100 },
  ];
  circles.forEach(c => {
    ctx.beginPath();
    ctx.arc(c.x, c.y, c.r, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.fill();
  });
  ctx.globalAlpha = 1;

  // "AI" watermark icon area
  ctx.globalAlpha = 0.2;
  ctx.font = 'bold 120px Arial';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('AI', W / 2, H / 2 - 40);
  ctx.globalAlpha = 1;

  // Prompt text
  const maxW  = W - 80;
  const words = qiState.prompt.split(' ');
  let lines   = [];
  let current = '';
  ctx.font = 'bold 20px "Noto Sans KR", "Malgun Gothic", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  for (const word of words) {
    const test = current ? current + ' ' + word : word;
    if (ctx.measureText(test).width > maxW) {
      if (current) lines.push(current);
      current = word;
    } else {
      current = test;
    }
    if (lines.length >= 2) break;
  }
  if (current && lines.length < 3) lines.push(current);
  lines = lines.slice(0, 2);

  const lineH  = 28;
  const totalH = lines.length * lineH;
  let   startY = H / 2 + 60;

  // Background box
  if (lines.length) {
    const boxW = Math.min(maxW, 600);
    const boxH = totalH + 24;
    ctx.globalAlpha = 0.35;
    ctx.fillStyle = '#000000';
    roundRect(ctx, (W - boxW) / 2, startY - 12, boxW, boxH, 12);
    ctx.globalAlpha = 1;
  }

  ctx.shadowColor   = 'rgba(0,0,0,0.5)';
  ctx.shadowBlur    = 8;
  ctx.shadowOffsetX = 1;
  ctx.shadowOffsetY = 1;

  lines.forEach((line, i) => {
    ctx.fillStyle = '#ffffff';
    ctx.fillText(line, W / 2, startY + i * lineH);
  });

  ctx.shadowColor = 'transparent';
  ctx.shadowBlur  = 0;
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
}

/* ─── Download ──────────────────────────────── */
function setupDownload() {
  const btn = $('qiDownloadBtn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const canvas = $('qiCanvas');
    const link   = document.createElement('a');
    const name   = 'quick-image-' + Date.now() + '.png';
    link.download = name;
    link.href     = canvas.toDataURL('image/png');
    link.click();
    showToast('이미지가 다운로드되었습니다.');
  });
}

/* ─── Toast ─────────────────────────────────── */
let toastTimer = null;
function showToast(msg) {
  const toast = $('qiToast');
  $('qiToastText').textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}
