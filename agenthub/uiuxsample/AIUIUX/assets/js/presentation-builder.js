/* =============================================
   프레젠테이션 생성 - presentation-builder.js
   ============================================= */
'use strict';

/* ─── State ────────────────────────────────────── */
const pbState = {
  method:      'topic',
  theme:       'default',
  slideCount:  5,
  service:     '',
  style:       'business',
  includeImgs: false,
  slides:      [],
  title:       '',
  genTime:     0,
};

/* ─── Slide content templates ────────────────── */
const PB_SLIDE_TEMPLATES = [
  { type: 'cover',   titleSuffix: '',               bullets: [] },
  { type: 'intro',   titleSuffix: ' 개요',          bullets: ['주요 배경 및 목적', '핵심 문제 정의', '접근 방식 소개'] },
  { type: 'body1',   titleSuffix: ' 현황 분석',     bullets: ['현재 상황 분석', '주요 지표 검토', '기회 요인 식별'] },
  { type: 'body2',   titleSuffix: ' 핵심 전략',     bullets: ['전략적 방향성', '우선순위 과제', '실행 로드맵'] },
  { type: 'body3',   titleSuffix: ' 기대 효과',     bullets: ['정량적 기대 효과', '정성적 기대 효과', '리스크 및 대응 방안'] },
  { type: 'body4',   titleSuffix: ' 실행 계획',     bullets: ['단계별 추진 계획', '담당 조직 및 역할', '마일스톤'] },
  { type: 'body5',   titleSuffix: ' 성과 측정',     bullets: ['KPI 정의', '측정 방법 및 주기', '목표 달성 기준'] },
  { type: 'body6',   titleSuffix: ' 사례 연구',     bullets: ['국내외 벤치마킹 사례', '성공 요인 분석', '시사점 도출'] },
  { type: 'body7',   titleSuffix: ' 기술 검토',     bullets: ['기술 스택 현황', '도입 방안', '기술 로드맵'] },
  { type: 'body8',   titleSuffix: ' 투자 계획',     bullets: ['예산 규모 및 구성', '투자 회수 계획', '재무적 영향'] },
  { type: 'body9',   titleSuffix: ' 조직 구성',     bullets: ['팀 구성 방안', '역할과 책임', '역량 개발 계획'] },
  { type: 'body10',  titleSuffix: ' 파트너십',      bullets: ['전략적 파트너 현황', '협력 모델', '시너지 창출 방안'] },
  { type: 'body11',  titleSuffix: ' 리스크 관리',   bullets: ['주요 리스크 식별', '리스크별 대응 전략', '비상 계획'] },
  { type: 'body12',  titleSuffix: ' 미래 전망',     bullets: ['중장기 비전', '성장 시나리오', '발전 방향'] },
  { type: 'body13',  titleSuffix: ' 혁신 전략',     bullets: ['혁신 방향 설정', '디지털 전환 계획', '경쟁 우위 확보'] },
  { type: 'body14',  titleSuffix: ' 고객 가치',     bullets: ['고객 세그먼트 분석', '가치 제안', '고객 경험 설계'] },
  { type: 'body15',  titleSuffix: ' 운영 효율화',   bullets: ['프로세스 최적화', '자동화 도입', '비용 절감 방안'] },
  { type: 'body16',  titleSuffix: ' 데이터 활용',   bullets: ['데이터 수집 현황', '분석 및 인사이트', '활용 방안'] },
  { type: 'closing', titleSuffix: ' 결론 및 제언',  bullets: ['핵심 요약', '최우선 실행 과제', '기대 성과'] },
];

/* ─── DOM refs ────────────────────────────────── */
const $ = id => document.getElementById(id);

/* ─── Init ────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  setupMethodGrid();
  setupThemeGrid();
  setupSlideCount();
  setupModal();
  setupFormListeners();
  setupResultActions();
});

/* ─── Method grid ─────────────────────────────── */
function setupMethodGrid() {
  const grid = $('pbMethodGrid');
  if (!grid) return;
  grid.querySelectorAll('.pb-method-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      grid.querySelectorAll('.pb-method-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      pbState.method = btn.dataset.method;

      const label  = $('pbContentLabel');
      const ta     = $('pbContent');
      if (pbState.method === 'topic') {
        label.innerHTML = '주제/내용 <span class="text-danger">*</span>';
        ta.placeholder = '예: 인공지능의 미래와 영향력';
        ta.rows = 4;
      } else if (pbState.method === 'paste') {
        label.innerHTML = '텍스트 내용 <span class="text-danger">*</span>';
        ta.placeholder = '슬라이드로 만들 텍스트를 붙여넣으세요...';
        ta.rows = 6;
      } else {
        label.innerHTML = 'URL <span class="text-danger">*</span>';
        ta.placeholder = 'https://example.com/article';
        ta.rows = 2;
      }
    });
  });
}

/* ─── Theme grid ────────────────────────────── */
function setupThemeGrid() {
  const grid = $('pbThemeGrid');
  if (!grid) return;
  grid.querySelectorAll('.pb-theme-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      grid.querySelectorAll('.pb-theme-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      pbState.theme = btn.dataset.theme;
    });
  });
}

/* ─── Slide count +/- ──────────────────────── */
function setupSlideCount() {
  const input = $('pbSlideCount');
  $('pbSlideDown').addEventListener('click', () => {
    const v = Math.max(3, parseInt(input.value) - 1);
    input.value = v;
    pbState.slideCount = v;
  });
  $('pbSlideUp').addEventListener('click', () => {
    const v = Math.min(20, parseInt(input.value) + 1);
    input.value = v;
    pbState.slideCount = v;
  });
  input.addEventListener('change', () => {
    const v = Math.min(20, Math.max(3, parseInt(input.value) || 5));
    input.value = v;
    pbState.slideCount = v;
  });
}

/* ─── Modal open/close ─────────────────────── */
function setupModal() {
  // Open
  ['btnOpenCreate', 'btnOpenCreate2'].forEach(id => {
    const el = $(id);
    if (el) el.addEventListener('click', openCreateModal);
  });
  // Close
  ['btnCloseCreate', 'btnCancelCreate'].forEach(id => {
    const el = $(id);
    if (el) el.addEventListener('click', closeCreateModal);
  });
  // Backdrop
  const overlay = $('modalCreate');
  if (overlay) {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeCreateModal();
    });
  }
  // Slide detail close
  ['btnCloseDetail', 'btnCloseDetail2'].forEach(id => {
    const el = $(id);
    if (el) el.addEventListener('click', closeDetailModal);
  });
  const detailOverlay = $('modalSlideDetail');
  if (detailOverlay) {
    detailOverlay.addEventListener('click', e => {
      if (e.target === detailOverlay) closeDetailModal();
    });
  }

  // File import
  const btnImport = $('btnImportFile');
  const fileInput = $('pbFileInput');
  if (btnImport && fileInput) {
    btnImport.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', e => {
      if (e.target.files.length) {
        showToast(`파일 불러오기: ${e.target.files[0].name}`);
      }
    });
  }

  // ESC key
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeCreateModal();
      closeDetailModal();
    }
  });
}

function openCreateModal() {
  $('modalCreate').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeCreateModal() {
  $('modalCreate').classList.remove('open');
  document.body.style.overflow = '';
}
function openDetailModal() {
  $('modalSlideDetail').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeDetailModal() {
  $('modalSlideDetail').classList.remove('open');
  document.body.style.overflow = '';
}

/* ─── Form listeners ───────────────────────── */
function setupFormListeners() {
  // Char count
  const ta = $('pbContent');
  const counter = $('pbCharCount');
  if (ta && counter) {
    ta.addEventListener('input', () => {
      counter.textContent = ta.value.length;
    });
  }

  // Service / style
  const svcSel = $('pbService');
  if (svcSel) svcSel.addEventListener('change', () => { pbState.service = svcSel.value; });
  const styleSel = $('pbStyle');
  if (styleSel) styleSel.addEventListener('change', () => { pbState.style = styleSel.value; });

  // Toggle
  const imgToggle = $('pbIncludeImages');
  if (imgToggle) imgToggle.addEventListener('change', () => { pbState.includeImgs = imgToggle.checked; });

  // Generate button
  const btnGen = $('btnGenerate');
  if (btnGen) btnGen.addEventListener('click', handleGenerate);
}

/* ─── Generate ─────────────────────────────── */
function handleGenerate() {
  const content = $('pbContent').value.trim();
  const service = $('pbService').value;

  if (!content) {
    $('pbContent').focus();
    $('pbContent').style.borderColor = '#EF4444';
    setTimeout(() => { $('pbContent').style.borderColor = ''; }, 2000);
    return;
  }
  if (!service) {
    $('pbService').style.borderColor = '#EF4444';
    setTimeout(() => { $('pbService').style.borderColor = ''; }, 2000);
    return;
  }

  pbState.slideCount = parseInt($('pbSlideCount').value) || 5;
  pbState.service    = service;
  pbState.style      = $('pbStyle').value;
  pbState.title      = content.length > 40 ? content.substring(0, 40) + '...' : content;

  closeCreateModal();
  startGeneration();
}

/* ─── Loading simulation ───────────────────── */
const PB_STEPS_INFO = [
  { id: 'pbStep1', label: '주제 분석 중...', sub: 'AI가 주제를 분석하고 있어요', pct: 15 },
  { id: 'pbStep2', label: '슬라이드 구성 설계 중...', sub: '슬라이드 구조를 설계하고 있어요', pct: 40 },
  { id: 'pbStep3', label: '콘텐츠 작성 중...', sub: '각 슬라이드 내용을 작성하고 있어요', pct: 70 },
  { id: 'pbStep4', label: '디자인 적용 중...', sub: '테마와 디자인을 적용하고 있어요', pct: 90 },
];

function startGeneration() {
  // Show loading
  $('pbEmptyState').style.display  = 'none';
  $('pbResultArea').style.display  = 'none';
  $('pbLoadingState').style.display = 'flex';

  // Reset steps
  $('pbLoadingTitle').textContent = '프레젠테이션을 생성하는 중입니다...';
  $('pbProgressBar').style.width  = '5%';
  PB_STEPS_INFO.forEach((s, i) => {
    const el = $(s.id);
    if (el) {
      el.className = 'pb-step' + (i === 0 ? ' pb-step-active' : '');
      el.querySelector('i').className = i === 0 ? 'fas fa-spinner fa-spin' : 'fas fa-circle';
      // Update text
      const labelMap = ['주제 분석 중...', '슬라이드 구성 설계', '콘텐츠 작성', '디자인 적용'];
      el.childNodes[1] ? (el.childNodes[1].textContent = ' ' + labelMap[i]) : null;
    }
  });

  const startTime = Date.now();
  let stepIdx = 0;

  const stepDurations = [900, 1200, 1500, 800];

  function runStep(idx) {
    if (idx >= PB_STEPS_INFO.length) {
      // Done
      $('pbProgressBar').style.width = '100%';
      $('pbLoadingTitle').textContent = '완료!';
      setTimeout(() => {
        pbState.genTime = ((Date.now() - startTime) / 1000).toFixed(1);
        buildSlides();
        showResult();
      }, 500);
      return;
    }

    const info = PB_STEPS_INFO[idx];
    const stepEl = $(info.id);

    // Mark current as active
    if (stepEl) {
      stepEl.className = 'pb-step pb-step-active';
      const icon = stepEl.querySelector('i');
      if (icon) icon.className = 'fas fa-spinner fa-spin';
    }

    $('pbLoadingSub').textContent = info.sub;
    $('pbProgressBar').style.width = info.pct + '%';

    setTimeout(() => {
      // Mark done
      if (stepEl) {
        stepEl.className = 'pb-step pb-step-done';
        const icon = stepEl.querySelector('i');
        if (icon) icon.className = 'fas fa-check-circle';
      }
      runStep(idx + 1);
    }, stepDurations[idx]);
  }

  // Small initial delay
  setTimeout(() => runStep(0), 300);
}

/* ─── Build slides data ─────────────────────── */
function buildSlides() {
  pbState.slides = [];
  const count = pbState.slideCount;

  for (let i = 0; i < count; i++) {
    const tplIdx = i === 0 ? 0
      : i === count - 1 ? PB_SLIDE_TEMPLATES.length - 1
      : Math.min(1 + i, PB_SLIDE_TEMPLATES.length - 2);

    const tpl = PB_SLIDE_TEMPLATES[tplIdx];
    const baseTitle = pbState.title.replace(/\.\.\.$/, '');

    pbState.slides.push({
      num:    i + 1,
      title:  i === 0 ? baseTitle : baseTitle + tpl.titleSuffix,
      bullets: tpl.bullets.slice(),
      theme:  pbState.theme,
      type:   tpl.type,
    });
  }
}

/* ─── Show result ───────────────────────────── */
function showResult() {
  $('pbLoadingState').style.display = 'none';
  $('pbResultArea').style.display   = 'block';

  // Toolbar info
  $('pbResultTitle').textContent = pbState.title;
  const svcLabel = {
    chatgpt: 'ChatGPT', claude: 'Claude', gemini: 'Gemini',
    cursor: 'Cursor', copilot: 'Copilot', mistral: 'Mistral'
  }[pbState.service] || pbState.service;
  $('pbResultInfo').textContent = `슬라이드 ${pbState.slides.length}개 · ${svcLabel}`;

  renderSlideGrid();
  renderGenInfo();
}

/* ─── Render slide grid ─────────────────────── */
function renderSlideGrid() {
  const grid = $('pbSlideGrid');
  grid.innerHTML = '';

  pbState.slides.forEach((slide, idx) => {
    const card = document.createElement('div');
    card.className = 'pb-slide-card';
    card.dataset.theme = slide.theme;
    card.title = `슬라이드 ${slide.num}: ${slide.title}`;

    card.innerHTML = `
      <div class="pb-slide-thumb">
        <div class="pb-slide-thumb-inner">
          <div class="pb-slide-th-title">${slide.title}</div>
          ${slide.type !== 'cover' ? slide.bullets.slice(0, 2).map(() => '<div class="pb-slide-th-line"></div>').join('') : ''}
        </div>
      </div>
      <div class="pb-slide-card-footer">
        <span class="pb-slide-num">${slide.num}</span>
        <span class="pb-slide-label">${slide.title}</span>
      </div>
    `;

    card.addEventListener('click', () => openSlideDetail(idx));
    grid.appendChild(card);
  });
}

/* ─── Gen info ──────────────────────────────── */
function renderGenInfo() {
  const svcLabel = {
    chatgpt: 'ChatGPT', claude: 'Claude', gemini: 'Gemini',
    cursor: 'Cursor', copilot: 'Copilot', mistral: 'Mistral'
  }[pbState.service] || pbState.service;
  const themeLabel = {
    default: '기본', 'business-blue': '비즈니스 블루', dark: '다크',
    minimal: '미니멀', marketing: '마케팅', education: '교육'
  }[pbState.theme] || pbState.theme;

  $('pbGenInfo').innerHTML = `
    <i class="fas fa-info-circle"></i>
    <span>
      <strong>${svcLabel}</strong> 로 생성됨 · 테마: <strong>${themeLabel}</strong> ·
      슬라이드 ${pbState.slides.length}개 · 생성 시간: ${pbState.genTime}초
    </span>
  `;
}

/* ─── Slide detail modal ────────────────────── */
function openSlideDetail(idx) {
  const slide = pbState.slides[idx];
  $('pbDetailSlideTitle').textContent = slide.title;
  $('pbDetailSlideNum').textContent   = `슬라이드 ${slide.num} / ${pbState.slides.length}`;

  // Preview area — apply theme bg
  const preview = $('pbDetailPreview');
  const themeGradients = {
    default:         'linear-gradient(135deg, #f5f7ff 0%, #e8eafe 100%)',
    'business-blue': 'linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%)',
    dark:            'linear-gradient(135deg, #111827 0%, #1F2937 100%)',
    minimal:         '#ffffff',
    marketing:       'linear-gradient(135deg, #F97316 0%, #EF4444 100%)',
    education:       'linear-gradient(135deg, #059669 0%, #0D9488 100%)',
  };
  const isDark = ['business-blue', 'dark', 'marketing', 'education'].includes(slide.theme);
  preview.style.background = themeGradients[slide.theme] || themeGradients.default;
  preview.style.border = slide.theme === 'minimal' ? '1px solid var(--border)' : 'none';

  const titleColor = isDark ? '#ffffff' : '#3730A3';
  const lineColor  = isDark ? 'rgba(255,255,255,0.3)' : 'rgba(79,70,229,0.15)';

  preview.innerHTML = `
    <div class="pb-detail-title" style="color:${titleColor}">${slide.title}</div>
    ${slide.bullets.map(() => `<div class="pb-detail-body-line" style="background:${lineColor}"></div>`).join('')}
  `;

  // Content
  if (slide.bullets.length) {
    $('pbDetailContent').innerHTML = `
      <strong style="font-size:13px;color:var(--text-primary)">주요 내용</strong>
      <ul>${slide.bullets.map(b => `<li>${b}</li>`).join('')}</ul>
    `;
  } else {
    $('pbDetailContent').innerHTML = '<p class="text-muted" style="font-size:13px">커버 슬라이드입니다.</p>';
  }

  openDetailModal();
}

/* ─── Result actions ────────────────────────── */
function setupResultActions() {
  const btnEdit = $('btnEditResult');
  if (btnEdit) btnEdit.addEventListener('click', () => {
    showToast('편집 기능은 준비 중입니다.');
  });

  const btnPptx = $('btnExportPptx');
  if (btnPptx) btnPptx.addEventListener('click', () => {
    simulateExport('PPTX');
  });

  const btnPdf = $('btnExportPdf');
  if (btnPdf) btnPdf.addEventListener('click', () => {
    simulateExport('PDF');
  });

  const btnNew = $('btnNewPres');
  if (btnNew) btnNew.addEventListener('click', () => {
    $('pbResultArea').style.display  = 'none';
    $('pbEmptyState').style.display  = 'flex';
    pbState.slides = [];
    openCreateModal();
  });

  const btnEditSlide = $('btnEditSlide');
  if (btnEditSlide) btnEditSlide.addEventListener('click', () => {
    showToast('슬라이드 편집 기능은 준비 중입니다.');
  });
}

function simulateExport(format) {
  showToast(`${format} 내보내기 중...`);
  setTimeout(() => {
    showToast(`${format} 내보내기 완료!`);
  }, 1200);
}

/* ─── Toast ────────────────────────────────── */
let toastTimer = null;
function showToast(msg) {
  const toast = $('pbToast');
  $('pbToastText').textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}
