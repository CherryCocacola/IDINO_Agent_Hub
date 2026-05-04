/* =============================================
   프레젠테이션 편집 - presentation-builder-result.js
   ============================================= */
'use strict';

/* ─── Default slide data ─────────────────────── */
const PBR_DEFAULT_SLIDES = [
  {
    title: '재벌집 막내아들: 드라마 성공 요인 분석',
    body:  '시청률 추이, 경제적 파급 효과 및 IP 확장 전략',
    layout: 'title-content',
    image: '',
  },
  {
    title: '작품 개요 및 핵심 줄거리',
    body:  '• 장르: 판타지, 기업 드라마, 복수극\n• 원작: 산경 작가의 동명 웹소설 (카카오페이지)\n• 방영: JTBC, 2022년 12월 ~ 2023년 1월\n• 주연: 송중기, 이성민, 신현빈',
    layout: 'title-content',
    image: '',
  },
  {
    title: '주요 흥행 요인 분석',
    body:  '• 스토리텔링의 힘\n  - \'회귀\'라는 판타지 요소와 현실 재벌 드라마의 결합\n  - 탄탄한 원작 IP 기반\n• 캐스팅 파워\n  - 송중기의 복귀작으로 높은 화제성\n• 연출 & 제작 품질\n  - 고퀄리티 영상미와 1970-80년대 시대 고증',
    layout: 'title-content',
    image: '',
  },
  {
    title: '시장 성과 및 경제적 파급력',
    body:  '• 시청률 기록: 최고 시청률 26.9% 달성 (JTBC 역대 최고)\n• OTT 성과: Disney+ 글로벌 인기 TOP 순위 진입\n• 관련 도서 판매량 급증: 원작 웹소설 유료 전환 폭증\n• 주연 배우 광고 모델료 상승: 송중기 광고 계약 다수 체결',
    layout: 'title-content',
    image: '',
  },
  {
    title: '결론 및 시사점',
    body:  '• 슈퍼 IP의 성공적인 미디어 믹스 사례 (웹소설 → 드라마)\n• K-콘텐츠의 글로벌 확장 가능성 재확인\n• 탄탄한 서사 + 스타 파워 + OTT 플랫폼 시너지 전략의 중요성\n• 향후 시즌2 및 IP 확장(게임·웹툰) 가능성 긍정적',
    layout: 'title-content',
    image: '',
  },
];

/* ─── State ────────────────────────────────────── */
const pbrState = {
  slides:        JSON.parse(JSON.stringify(PBR_DEFAULT_SLIDES)),
  activeIdx:     0,
  theme:         'business-blue',
  presTitle:     '재벌집 막내아들: 드라마 성공 요인 분석',
};

/* ─── DOM refs ──────────────────────────────────── */
const $ = id => document.getElementById(id);

/* ─── Init ──────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  renderSlideList();
  selectSlide(0);
  setupTheme();
  setupFields();
  setupImageUpload();
  setupSave();
  setupExport();
  setupActions();
  applyThemeToPreview();
});

/* ─── Slide List ─────────────────────────────────── */
function renderSlideList() {
  const list = $('pbrSlideList');
  list.innerHTML = '';

  pbrState.slides.forEach((slide, idx) => {
    const item = document.createElement('div');
    item.className = 'pbr-slide-item' + (idx === pbrState.activeIdx ? ' active' : '');
    item.dataset.idx = idx;

    item.innerHTML = `
      <div class="pbr-slide-item-top">
        <span class="pbr-drag-handle" draggable="true" title="드래그하여 순서 변경">
          <i class="fas fa-grip-vertical"></i>
        </span>
        <span class="pbr-slide-num">${idx + 1}</span>
        <button class="pbr-slide-del" data-idx="${idx}" title="삭제">
          <i class="fas fa-xmark"></i>
        </button>
      </div>
      <div class="pbr-slide-thumb pbr-thumb-${pbrState.theme}">
        <div class="pbr-slide-thumb-bar"></div>
        <div class="pbr-slide-thumb-line"></div>
        <div class="pbr-slide-thumb-line"></div>
      </div>
      <span class="pbr-slide-preview-title">${slide.title || '제목 없음'}</span>
      <span class="pbr-slide-preview-body">${slide.body || ''}</span>
    `;

    // Select
    item.addEventListener('click', e => {
      if (e.target.closest('.pbr-slide-del')) return;
      selectSlide(idx);
    });

    // Delete
    item.querySelector('.pbr-slide-del').addEventListener('click', e => {
      e.stopPropagation();
      deleteSlide(idx);
    });

    // Drag & drop (reorder)
    setupDrag(item, idx);

    list.appendChild(item);
  });

  // Update stats
  const statTotal = $('pbrStatTotal');
  if (statTotal) statTotal.textContent = pbrState.slides.length;
}

function selectSlide(idx) {
  if (idx < 0 || idx >= pbrState.slides.length) return;
  pbrState.activeIdx = idx;

  // Highlight list
  document.querySelectorAll('.pbr-slide-item').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
  });

  // Fill editor fields
  const slide = pbrState.slides[idx];
  $('pbrSlideTitle').value = slide.title || '';
  $('pbrSlideBody').value  = slide.body  || '';
  $('pbrLayout').value     = slide.layout || 'title-content';

  // Image
  if (slide.image) {
    $('pbrImgPreviewEl').src       = slide.image;
    $('pbrImgPreview').style.display = 'block';
    $('pbrImgUpload').style.display  = 'none';
  } else {
    $('pbrImgPreview').style.display = 'none';
    $('pbrImgUpload').style.display  = 'flex';
  }

  // Slide number in props
  $('pbrSlideNumInput').value = idx + 1;

  // Update preview
  updatePreview();

  // Hide saved hint
  const hint = $('pbrSavedHint');
  if (hint) { hint.classList.remove('show'); }
}

function deleteSlide(idx) {
  if (pbrState.slides.length <= 1) {
    showToast('슬라이드는 최소 1개 이상이어야 합니다.');
    return;
  }
  pbrState.slides.splice(idx, 1);
  const newIdx = Math.min(pbrState.activeIdx, pbrState.slides.length - 1);
  renderSlideList();
  selectSlide(newIdx);
  showToast('슬라이드가 삭제되었습니다.');
}

function addSlide() {
  const newSlide = {
    title:  '새 슬라이드',
    body:   '',
    layout: 'title-content',
    image:  '',
  };
  pbrState.slides.splice(pbrState.activeIdx + 1, 0, newSlide);
  renderSlideList();
  selectSlide(pbrState.activeIdx + 1);
  showToast('슬라이드가 추가되었습니다.');
}

/* ─── Drag & Drop reorder ─────────────────────── */
let dragSrcIdx = null;

function setupDrag(item, idx) {
  const handle = item.querySelector('.pbr-drag-handle');
  handle.addEventListener('mousedown', () => { item.draggable = true; });
  item.addEventListener('dragstart', e => {
    dragSrcIdx = idx;
    e.dataTransfer.effectAllowed = 'move';
    item.style.opacity = '0.5';
  });
  item.addEventListener('dragend', () => { item.style.opacity = ''; item.draggable = false; });
  item.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
  item.addEventListener('drop', e => {
    e.preventDefault();
    if (dragSrcIdx === null || dragSrcIdx === idx) return;
    const moved = pbrState.slides.splice(dragSrcIdx, 1)[0];
    pbrState.slides.splice(idx, 0, moved);
    dragSrcIdx = null;
    renderSlideList();
    selectSlide(idx);
  });
}

/* ─── Preview ────────────────────────────────── */
function updatePreview() {
  const slide = pbrState.slides[pbrState.activeIdx];
  const previewSlide = $('pbrPreviewSlide');

  $('pbrPrevTitle').textContent = slide.title || '';
  $('pbrPrevBody').textContent  = slide.body  || '';
  $('pbrPrevNum').textContent   = `${pbrState.activeIdx + 1} / ${pbrState.slides.length}`;
  previewSlide.dataset.theme    = pbrState.theme;
}

function applyThemeToPreview() {
  $('pbrPreviewSlide').dataset.theme = pbrState.theme;
  $('pbrThemeMini').dataset.theme    = pbrState.theme;
}

/* ─── Theme ────────────────────────────────────── */
function setupTheme() {
  const sel = $('pbrTheme');
  if (!sel) return;
  sel.value = pbrState.theme;
  sel.addEventListener('change', () => {
    pbrState.theme = sel.value;
    applyThemeToPreview();
    renderSlideList(); // update thumb colors
  });
}

/* ─── Fields (live preview update) ────────────── */
function setupFields() {
  $('pbrSlideTitle').addEventListener('input', () => {
    $('pbrPrevTitle').textContent = $('pbrSlideTitle').value;
  });
  $('pbrSlideBody').addEventListener('input', () => {
    $('pbrPrevBody').textContent = $('pbrSlideBody').value;
  });
  $('pbrPresTitle').addEventListener('input', () => {
    pbrState.presTitle = $('pbrPresTitle').value;
  });
}

/* ─── Image upload ─────────────────────────────── */
function setupImageUpload() {
  const upload  = $('pbrImgUpload');
  const input   = $('pbrImgInput');
  const preview = $('pbrImgPreview');
  const previewEl = $('pbrImgPreviewEl');
  const removeBtn = $('pbrImgRemove');

  upload.addEventListener('click', () => input.click());
  input.addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const dataUrl = ev.target.result;
      pbrState.slides[pbrState.activeIdx].image = dataUrl;
      previewEl.src = dataUrl;
      preview.style.display = 'block';
      upload.style.display  = 'none';
    };
    reader.readAsDataURL(file);
    input.value = '';
  });
  removeBtn.addEventListener('click', () => {
    pbrState.slides[pbrState.activeIdx].image = '';
    preview.style.display = 'none';
    upload.style.display  = 'flex';
    previewEl.src = '';
  });
}

/* ─── Save ─────────────────────────────────────── */
function setupSave() {
  $('btnSaveSlide').addEventListener('click', saveCurrentSlide);
}

function saveCurrentSlide() {
  const slide = pbrState.slides[pbrState.activeIdx];
  slide.title  = $('pbrSlideTitle').value;
  slide.body   = $('pbrSlideBody').value;
  slide.layout = $('pbrLayout').value;

  // Refresh list preview text
  const items = document.querySelectorAll('.pbr-slide-item');
  const item  = items[pbrState.activeIdx];
  if (item) {
    const titleEl = item.querySelector('.pbr-slide-preview-title');
    const bodyEl  = item.querySelector('.pbr-slide-preview-body');
    if (titleEl) titleEl.textContent = slide.title || '제목 없음';
    if (bodyEl)  bodyEl.textContent  = slide.body  || '';
  }

  // Show saved hint
  const hint = $('pbrSavedHint');
  hint.textContent = '✓ 저장됨';
  hint.classList.add('show');
  setTimeout(() => hint.classList.remove('show'), 2500);

  showToast('슬라이드가 저장되었습니다.');
}

/* ─── Export ────────────────────────────────────── */
function setupExport() {
  $('btnExportPptx').addEventListener('click', () => {
    saveCurrentSlide();
    showToast('PPTX 내보내기 중...');
    setTimeout(() => showToast('PPTX 내보내기 완료!'), 1200);
  });
  $('btnExportPdf').addEventListener('click', () => {
    showToast('PDF 내보내기 중... (LibreOffice 필요)');
    setTimeout(() => showToast('PDF 내보내기 완료!'), 1400);
  });
}

/* ─── Actions ───────────────────────────────────── */
function setupActions() {
  // Add slide
  $('btnAddSlide').addEventListener('click', addSlide);

  // Regenerate
  $('btnRegenerate').addEventListener('click', () => {
    window.location.href = 'presentation-builder.html';
  });

  // Back to list
  $('btnBackToList').addEventListener('click', () => {
    window.location.href = 'presentation-builder.html';
  });
}

/* ─── Toast ─────────────────────────────────────── */
let toastTimer = null;
function showToast(msg) {
  const toast = $('pbrToast');
  $('pbrToastText').textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}
