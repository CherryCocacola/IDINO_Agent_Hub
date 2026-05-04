<template>
  <div class="page-content-wrap pb-page container-fluid" :class="{ 'py-4': !currentPresentation }">
    <!-- Page Header (빈 상태/로딩 시에만 표시) -->
    <div class="page-header" v-if="!currentPresentation">
      <div>
        <h1 class="page-heading">{{ $t('presentationBuilder.title') }}</h1>
        <p class="page-desc">{{ $t('presentationBuilder.desc') }}</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary me-2" @click="showLoadModal = true">
          <i class="bi bi-folder2-open me-2"></i>{{ $t('presentationBuilder.loadExisting') }}
        </button>
        <button class="btn btn-primary" @click="showGenerateModal = true">
          <i class="bi bi-magic me-2"></i>{{ $t('presentationBuilder.generateWithAi') }}
        </button>
      </div>
    </div>

    <!-- 기존 프레젠테이션 불러오기 모달 (PRESENTATIONS 테이블 기반) -->
    <div
      class="pb-modal-overlay"
      :class="{ open: showLoadModal }"
      v-if="showLoadModal"
      @click.self="showLoadModal = false"
    >
      <div class="pb-modal pb-modal-lg">
        <div class="pb-modal-header">
          <div class="pb-modal-title-wrap">
            <div class="pb-modal-icon"><i class="bi bi-folder2-open"></i></div>
            <div>
              <h4>{{ $t('presentationBuilder.loadModalTitle') }}</h4>
              <p class="mb-0">이미 생성된 프레젠테이션을 선택하세요</p>
            </div>
          </div>
          <div class="d-flex align-items-center gap-2">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="loadSavedPresentations" :disabled="loadModalLoading" title="새로고침">
              <i class="bi bi-arrow-clockwise" :class="{ 'pb-spin': loadModalLoading }"></i> 새로고침
            </button>
            <button type="button" class="pb-modal-close" @click="showLoadModal = false"><i class="bi bi-x-lg"></i></button>
          </div>
        </div>
        <div class="pb-modal-body">
          <div v-if="loadModalError" class="alert alert-danger mb-3">
            <i class="bi bi-exclamation-triangle me-2"></i>{{ loadModalError }}
            <button type="button" class="btn btn-sm btn-outline-danger ms-2" @click="loadModalError = null">닫기</button>
          </div>
          <div v-if="loadModalLoading" class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 mb-0 text-muted">{{ $t('presentationBuilder.loadingList') }}</p>
          </div>
          <div v-else-if="!savedPresentations.length" class="text-center py-5 text-muted">
            <i class="bi bi-inbox" style="font-size: 2.5rem;"></i>
            <p class="mt-3 mb-0">{{ $t('presentationBuilder.noSaved') }}</p>
            <p class="small">{{ $t('presentationBuilder.createNewHint') }}</p>
          </div>
          <div v-else class="pb-load-list">
            <div
              v-for="p in savedPresentations"
              :key="p.presentationId"
              class="pb-load-item"
              @click="loadPresentation(p)"
            >
              <div class="pb-load-item-thumb" :class="'pbr-thumb-' + (p.themeId || 'default')">
                <div class="pbr-slide-thumb-bar"></div>
                <div class="pbr-slide-thumb-line"></div>
                <div class="pbr-slide-thumb-line pbr-tm-short"></div>
              </div>
              <div class="pb-load-item-info">
                <strong class="pb-load-item-title">{{ p.title || $t('presentationBuilder.noTitle') }}</strong>
                <span class="pb-load-item-meta">{{ $t('presentationBuilder.slidesCount', { count: p.slideCount }) }} · {{ formatDate(p.updatedAt) }}</span>
              </div>
              <i class="bi bi-chevron-right text-muted"></i>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 생성 모달 -->
    <div
      class="pb-modal-overlay"
      :class="{ open: showGenerateModal }"
      v-if="showGenerateModal"
      @click.self="showGenerateModal = false"
    >
      <div class="pb-modal pb-modal-lg">
        <div class="pb-modal-header">
          <div class="pb-modal-title-wrap">
            <div class="pb-modal-icon"><i class="bi bi-magic"></i></div>
            <div>
              <h4>{{ $t('presentationBuilder.generateModalTitle') }}</h4>
              <p>{{ $t('presentationBuilder.generateModalDesc') }}</p>
            </div>
          </div>
          <button type="button" class="pb-modal-close" @click="showGenerateModal = false"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="pb-modal-body">
          <form @submit.prevent="generatePresentation">
            <!-- 생성 방식 -->
            <div class="pb-form-field">
              <label class="pb-form-label">{{ $t('presentationBuilder.sourceType') }}</label>
              <div class="pb-method-grid">
                <button type="button" class="pb-method-btn" :class="{ active: generationRequest.sourceType === 'topic' }" @click="generationRequest.sourceType = 'topic'">
                  <i class="bi bi-lightbulb"></i>
                  <strong>{{ $t('presentationBuilder.topic') }}</strong>
                  <small>{{ $t('presentationBuilder.topicHint') }}</small>
                </button>
                <button type="button" class="pb-method-btn" :class="{ active: generationRequest.sourceType === 'paste' }" @click="generationRequest.sourceType = 'paste'">
                  <i class="bi bi-clipboard"></i>
                  <strong>{{ $t('presentationBuilder.paste') }}</strong>
                  <small>{{ $t('presentationBuilder.pasteHint') }}</small>
                </button>
                <button type="button" class="pb-method-btn" :class="{ active: generationRequest.sourceType === 'import' }" @click="generationRequest.sourceType = 'import'">
                  <i class="bi bi-link-45deg"></i>
                  <strong>{{ $t('presentationBuilder.import') }}</strong>
                  <small>{{ $t('presentationBuilder.importHint') }}</small>
                </button>
              </div>
            </div>

            <!-- 주제/내용 -->
            <div class="pb-form-field">
              <label class="pb-form-label">
                {{ generationRequest.sourceType === 'topic' ? $t('presentationBuilder.topicLabel') : generationRequest.sourceType === 'paste' ? $t('presentationBuilder.pasteLabel') : $t('presentationBuilder.importLabel') }} <span class="text-danger">*</span>
              </label>
              <textarea
                v-if="generationRequest.sourceType === 'topic'"
                class="pb-form-textarea"
                v-model="generationRequest.prompt"
                rows="4"
                :placeholder="$t('presentationBuilder.topicPlaceholder')"
              ></textarea>
              <textarea
                v-else-if="generationRequest.sourceType === 'paste'"
                class="pb-form-textarea"
                v-model="generationRequest.pasteContent"
                rows="6"
                :placeholder="$t('presentationBuilder.pastePlaceholder')"
              ></textarea>
              <input
                v-else
                type="url"
                class="pb-form-textarea d-block w-100"
                v-model="generationRequest.importUrl"
                placeholder="https://..."
              >
              <div class="pb-char-row" v-if="generationRequest.sourceType !== 'import'">
                <span>{{ contentLength }}</span> / 2000
              </div>
              <small class="pb-form-hint" v-if="generationRequest.sourceType === 'import'">웹 페이지에서 본문 텍스트를 추출해 슬라이드로 만듭니다.</small>
            </div>

            <div class="pb-form-row">
              <div class="pb-form-field">
                <label class="pb-form-label">템플릿 사용 <span class="pb-optional">선택사항</span></label>
                <select class="pb-form-select" v-model.number="generationRequest.templateId" @change="onTemplateChange">
                  <option :value="undefined">템플릿 없이 생성</option>
                  <option v-for="template in availableTemplates" :key="template.templateId" :value="template.templateId">
                    {{ template.templateName }} — {{ template.templateStructure?.slideCount || 0 }}슬라이드
                  </option>
                </select>
                <small class="pb-form-hint">
                  <i class="bi bi-info-circle me-1"></i>
                  <router-link to="/presentation-templates">시스템 관리 &gt; 프레젠테이션 템플릿 관리</router-link>에서 등록·관리할 수 있습니다.
                </small>
              </div>
              <div class="pb-form-field">
                <label class="pb-form-label">슬라이드 개수</label>
                <div class="pb-count-row">
                  <button type="button" class="pb-count-btn" @click="generationRequest.slideCount = Math.max(3, (generationRequest.slideCount || 5) - 1)" :disabled="!!generationRequest.templateId">
                    <i class="bi bi-dash"></i>
                  </button>
                  <input type="number" class="pb-count-input" v-model.number="generationRequest.slideCount" min="3" max="20" :disabled="!!generationRequest.templateId">
                  <button type="button" class="pb-count-btn" @click="generationRequest.slideCount = Math.min(20, (generationRequest.slideCount || 5) + 1)" :disabled="!!generationRequest.templateId">
                    <i class="bi bi-plus"></i>
                  </button>
                </div>
                <small class="pb-form-hint">{{ generationRequest.templateId ? $t('presentationBuilder.templateSlideHint') : $t('presentationBuilder.slideCountHint') }}</small>
              </div>
            </div>

            <div class="pb-form-row">
              <div class="pb-form-field">
                <label class="pb-form-label">AI 서비스 <span class="text-danger">*</span></label>
                <select class="pb-form-select" v-model.number="generationRequest.serviceId" required>
                  <option value="">서비스를 선택하세요</option>
                  <option v-for="service in aiServices" :key="service.serviceId" :value="service.serviceId">
                    {{ service.serviceName }}
                  </option>
                </select>
              </div>
              <div class="pb-form-field">
                <label class="pb-form-label">스타일</label>
                <select class="pb-form-select" v-model="generationRequest.style">
                  <option value="business">비즈니스</option>
                  <option value="education">교육</option>
                  <option value="marketing">마케팅</option>
                  <option value="creative">창의적</option>
                </select>
              </div>
            </div>

            <div class="pb-form-field" v-if="generationRequest.serviceId">
              <label class="pb-form-label">모델</label>
              <select class="pb-form-select" v-model="generationRequest.model">
                <option value="">기본 모델 사용</option>
                <option v-for="model in availableModels" :key="model" :value="model">{{ model }}</option>
              </select>
            </div>

            <div class="pb-form-row">
              <div class="pb-form-field">
                <label class="pb-form-label">{{ $t('presentationBuilder.slideSize') || '슬라이드 비율' }}</label>
                <select class="pb-form-select" v-model="generationRequest.slideSize">
                  <option value="16:9">16:9 (와이드스크린)</option>
                  <option value="4:3">4:3 (기본)</option>
                  <option value="16:10">16:10</option>
                </select>
              </div>
              <div class="pb-form-field">
                <label class="pb-form-label">테마</label>
                <select class="pb-form-select" v-model="generationRequest.themeId">
                  <option value="">기본</option>
                  <option v-for="t in availableThemes" :key="t.themeId" :value="t.themeId">{{ t.name }}</option>
                </select>
              </div>
            </div>
            <div class="pb-form-row">
              <div class="pb-form-field">
                <label class="pb-form-label">{{ $t('presentationBuilder.fontHeading') || '제목 글꼴' }} <span class="pb-optional">선택</span></label>
                <select class="pb-form-select" v-model="generationRequest.fontHeading">
                  <option value="">테마 기본</option>
                  <option value="맑은 고딕">맑은 고딕</option>
                  <option value="Noto Sans KR">Noto Sans KR</option>
                  <option value="Pretendard">Pretendard</option>
                  <option value="나눔고딕">나눔고딕</option>
                  <option value="배달의민족 한나">배달의민족 한나</option>
                  <option value="Arial">Arial</option>
                  <option value="Calibri">Calibri</option>
                </select>
              </div>
              <div class="pb-form-field">
                <label class="pb-form-label">{{ $t('presentationBuilder.fontBody') || '본문 글꼴' }} <span class="pb-optional">선택</span></label>
                <select class="pb-form-select" v-model="generationRequest.fontBody">
                  <option value="">테마 기본</option>
                  <option value="맑은 고딕">맑은 고딕</option>
                  <option value="Noto Sans KR">Noto Sans KR</option>
                  <option value="Pretendard">Pretendard</option>
                  <option value="나눔고딕">나눔고딕</option>
                  <option value="배달의민족 한나">배달의민족 한나</option>
                  <option value="Arial">Arial</option>
                  <option value="Calibri">Calibri</option>
                </select>
              </div>
            </div>

            <!-- AI 이미지 삽입 -->
            <div class="pb-form-field">
              <label class="pb-toggle-row" for="includeAiImages">
                <div class="pb-toggle-switch">
                  <input type="checkbox" id="includeAiImages" v-model="generationRequest.includeAiImages">
                  <span class="pb-toggle-knob"></span>
                </div>
                <div>
                  <strong>AI 이미지 자동 삽입</strong>
                  <small>각 슬라이드에 어울리는 AI 이미지를 자동으로 생성·삽입합니다 (추가 비용 발생)</small>
                </div>
              </label>
            </div>
            <template v-if="generationRequest.includeAiImages">
              <div class="pb-form-field">
                <label class="pb-form-label">이미지 생성 서비스</label>
                <select class="pb-form-select" v-model.number="generationRequest.imageServiceId">
                  <option :value="undefined">선택</option>
                  <option v-for="s in imageServices" :key="s.serviceId" :value="s.serviceId">{{ s.serviceName }}</option>
                </select>
              </div>
              <div class="pb-form-field" v-if="generationRequest.imageServiceId">
                <label class="pb-form-label">이미지 모델</label>
                <select class="pb-form-select" v-model="generationRequest.imageModel">
                  <option value="">기본</option>
                  <option v-for="m in imageModels" :key="m" :value="m">{{ m }}</option>
                </select>
              </div>
            </template>
          </form>
        </div>

        <div class="pb-modal-footer">
          <button type="button" class="pb-btn-cancel" @click="showGenerateModal = false">취소</button>
          <button type="button" class="btn btn-primary pb-btn-generate" @click="generatePresentation" :disabled="generating">
            <i class="bi bi-magic me-2"></i>{{ generating ? $t('presentationBuilder.generating') : $t('presentationBuilder.generate') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 슬라이드 쇼 오버레이 -->
    <Teleport to="body">
      <div
        v-if="showSlideshowMode && currentPresentation"
        class="pbr-slideshow-overlay"
        @click.self="handleSlideshowClick"
      >
        <button class="pbr-slideshow-close" @click="exitSlideshow" :title="$t('presentationBuilder.slideshowExit')">
          <i class="bi bi-x-lg"></i>
        </button>
        <div class="pbr-slideshow-nav pbr-slideshow-prev" @click="slideshowPrev" v-if="slides.length > 1">
          <i class="bi bi-chevron-left"></i>
        </div>
        <div class="pbr-slideshow-nav pbr-slideshow-next" @click="slideshowNext" v-if="slides.length > 1">
          <i class="bi bi-chevron-right"></i>
        </div>
        <div class="pbr-slideshow-content">
          <div
            class="pbr-preview-slide pbr-slideshow-slide"
            :data-theme="effectiveThemeId || 'default'"
            :data-layout="(slideshowSlide?.layout || 'title-content')"
          >
            <div class="pbr-prev-inner" :data-layout="slideshowSlide?.layout || 'title-content'">
              <!-- title-only -->
              <template v-if="slideshowSlide?.layout === 'title-only'">
                <div class="pbr-layout-center">
                  <div class="pbr-prev-title pbr-title-huge">{{ slideshowSlide.title || '' }}</div>
                  <div v-if="slideshowSlide.content?.trim()" class="pbr-prev-subtitle pbr-prev-markdown" v-html="renderMarkdown(firstLine(slideshowSlide.content))"></div>
                </div>
              </template>
              <!-- section-header -->
              <template v-else-if="slideshowSlide?.layout === 'section-header'">
                <div class="pbr-layout-section-header">
                  <div class="pbr-section-accent"></div>
                  <div class="pbr-prev-title pbr-title-section">{{ slideshowSlide.title || '' }}</div>
                  <div v-if="slideshowSlide.content?.trim()" class="pbr-prev-subtitle pbr-prev-markdown" v-html="renderMarkdown(slideshowSlide.content)"></div>
                </div>
              </template>
              <!-- quote -->
              <template v-else-if="slideshowSlide?.layout === 'quote'">
                <div class="pbr-layout-center pbr-layout-quote">
                  <div class="pbr-quote-mark">"</div>
                  <div class="pbr-quote-text pbr-prev-markdown" v-html="renderMarkdown(slideshowSlide.content || '')"></div>
                  <div v-if="slideshowSlide.title?.trim()" class="pbr-quote-author">— {{ slideshowSlide.title }}</div>
                </div>
              </template>
              <!-- thank-you -->
              <template v-else-if="slideshowSlide?.layout === 'thank-you'">
                <div class="pbr-layout-center pbr-layout-thank-you">
                  <div class="pbr-thankyou-icon">✨</div>
                  <div class="pbr-prev-title pbr-title-huge">{{ slideshowSlide.title || 'Thank You' }}</div>
                  <div v-if="slideshowSlide.content?.trim()" class="pbr-prev-subtitle pbr-prev-markdown" v-html="renderMarkdown(slideshowSlide.content)"></div>
                </div>
              </template>
              <!-- image-title -->
              <template v-else-if="slideshowSlide?.layout === 'image-title'">
                <div class="pbr-prev-title">{{ slideshowSlide.title || '' }}</div>
                <div class="pbr-layout-image-title">
                  <div class="pbr-img-side">
                    <img v-if="slideshowSlide.imageUrl" :src="slideshowSlide.imageUrl" class="pbr-slide-img" />
                    <div v-else class="pbr-img-placeholder">
                      <i class="bi bi-image"></i>
                      <span v-if="slideshowSlide.imageDescription" class="pbr-img-desc-hint">{{ slideshowSlide.imageDescription }}</span>
                    </div>
                  </div>
                  <div class="pbr-content-side">
                    <div class="pbr-prev-body pbr-prev-markdown" v-html="renderMarkdown(slideshowSlide.content || '')"></div>
                  </div>
                </div>
              </template>
              <!-- two-column / comparison -->
              <template v-else-if="(slideshowSlide?.layout || '').match(/two-column|comparison/)">
                <div class="pbr-prev-title">{{ slideshowSlide?.title || '' }}</div>
                <div class="pbr-prev-two-col">
                  <div class="pbr-prev-col pbr-prev-markdown" v-html="renderMarkdown(slideshowLeftContent)"></div>
                  <div class="pbr-prev-col pbr-prev-markdown" v-html="renderMarkdown(slideshowRightContent)"></div>
                </div>
              </template>
              <!-- default: title-content -->
              <template v-else>
                <div class="pbr-prev-title">{{ slideshowSlide?.title || '' }}</div>
                <div class="pbr-prev-body pbr-prev-markdown" v-html="renderMarkdown(slideshowSlide?.content || '')"></div>
                <div v-if="slideshowSlide?.tables?.length" class="pbr-prev-tables">
                  <table v-for="(tbl, ti) in slideshowSlide.tables" :key="ti" class="pbr-prev-table">
                    <thead v-if="tbl.headerRow && tbl.rows?.length"><tr><th v-for="(cell, ci) in tbl.rows[0]" :key="ci">{{ cell }}</th></tr></thead>
                    <tbody>
                      <tr v-for="(row, ri) in (tbl.headerRow ? tbl.rows?.slice(1) : tbl.rows) || []" :key="ri">
                        <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-if="slideshowSlide?.charts?.length" class="pbr-prev-charts">
                  <div v-for="(ch, chi) in slideshowSlide.charts" :key="chi" class="pbr-prev-chart">
                    <div class="pbr-prev-chart-title">{{ ch.title }}</div>
                    <table class="pbr-prev-table pbr-prev-chart-data" v-if="ch.data && Object.keys(ch.data).length">
                      <tbody><tr v-for="(val, key) in ch.data" :key="String(key)"><th>{{ key }}</th><td>{{ val }}</td></tr></tbody>
                    </table>
                  </div>
                </div>
              </template>
            </div>
            <div class="pbr-prev-num">{{ slideshowIndex + 1 }} / {{ slides.length }}</div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Empty State -->
    <div v-if="!currentPresentation && !generating" class="pb-empty-state">
      <div class="pb-empty-icon"><i class="bi bi-file-earmark-slides"></i></div>
      <h5 class="pb-empty-title">새 프레젠테이션을 생성하거나<br>기존 프레젠테이션을 불러오세요</h5>
      <p class="pb-empty-desc">AI가 주제를 분석하고 슬라이드 구성부터 내용까지 자동으로 만들어 드립니다.</p>
      <div class="pb-empty-actions">
        <button class="btn btn-primary btn-lg" @click="showGenerateModal = true">
          <i class="bi bi-magic me-2"></i>AI로 생성하기
        </button>
        <!--button class="btn btn-outline-secondary btn-lg" @click="triggerFileImport">
          <i class="bi bi-upload me-2"></i>파일 불러오기
        </button-->
      </div>
      <input ref="fileInputRef" type="file" class="d-none" accept=".pptx,.ppt,.pdf" @change="onFileSelected">

      <div class="pb-feature-chips">
        <span class="pb-chip"><i class="bi bi-lightning"></i> 빠른 생성</span>
        <span class="pb-chip"><i class="bi bi-palette"></i> 다양한 테마</span>
        <span class="pb-chip"><i class="bi bi-image"></i> AI 이미지 삽입</span>
        <span class="pb-chip"><i class="bi bi-download"></i> PPTX 내보내기</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else-if="generating" class="pb-loading-state">
      <div class="pb-loading-inner">
        <div class="pb-loading-icon">
          <div class="pb-ring"></div>
          <div class="pb-ring pb-ring2"></div>
          <div class="pb-ring pb-ring3"></div>
          <i class="bi bi-file-earmark-slides pb-ring-icon"></i>
        </div>
        <h5 class="pb-loading-title">프레젠테이션을 생성하는 중입니다...</h5>
        <p class="pb-loading-sub">AI가 주제를 분석하고 있어요</p>
        <div class="pb-loading-steps">
          <div class="pb-step" :class="loadingStep >= 1 ? 'pb-step-done' : 'pb-step-active'">
            <i :class="loadingStep >= 1 ? 'bi bi-check-circle' : 'bi bi-arrow-repeat pb-step-spin'"></i>
            주제 분석 중...
          </div>
          <div class="pb-step" :class="loadingStep >= 2 ? 'pb-step-done' : loadingStep === 1 ? 'pb-step-active' : ''">
            <i :class="loadingStep >= 2 ? 'bi bi-check-circle' : 'bi bi-circle'"></i>
            슬라이드 구성 설계
          </div>
          <div class="pb-step" :class="loadingStep >= 3 ? 'pb-step-done' : loadingStep === 2 ? 'pb-step-active' : ''">
            <i :class="loadingStep >= 3 ? 'bi bi-check-circle' : 'bi bi-circle'"></i>
            콘텐츠 작성
          </div>
          <div class="pb-step" :class="loadingStep >= 4 ? 'pb-step-done' : loadingStep === 3 ? 'pb-step-active' : ''">
            <i :class="loadingStep >= 4 ? 'bi bi-check-circle' : 'bi bi-circle'"></i>
            디자인 적용
          </div>
        </div>
        <div class="pb-progress-wrap">
          <div class="pb-progress-bar" :style="{ width: loadingProgress + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- Result Area (presentation-builder-result 기반) -->
    
    <div v-else class="pbr-page">
      <div class="pbr-layout">
        <!-- Col 1: Slide List -->
        <aside class="pbr-col-slides">
          <div class="pbr-panel">
            <div class="pbr-panel-header">
              <span class="pbr-panel-title">슬라이드</span>
              <button class="pbr-icon-btn" @click="addNewSlide" :title="$t('presentationBuilder.addSlide')">
                <i class="bi bi-plus"></i>
              </button>
            </div>
            <div class="pbr-slide-list">
              <div
                v-for="(slide, index) in (currentPresentation?.slides || [])"
                :key="slide.slideId"
                class="pbr-slide-item"
                :class="{
                  active: selectedSlideId === slide.slideId,
                  'slide-dragging': dragFromIndex === index,
                  'slide-drag-over': dragOverIndex === index && dragFromIndex !== null
                }"
                @click="selectSlide(slide.slideId)"
                @dragover.prevent="onSlideDragOver($event, index)"
                @dragenter="onSlideDragEnter(index)"
                @dragleave="onSlideDragLeave"
                @drop.prevent="onSlideDrop($event, index)"
              >
                <div class="pbr-slide-thumb" :class="'pbr-thumb-' + (effectiveThemeId || 'default')">
                  <div class="pbr-slide-thumb-bar"></div>
                  <div class="pbr-slide-thumb-line"></div>
                  <div class="pbr-slide-thumb-line pbr-tm-short"></div>
                </div>
                <div class="pbr-slide-item-top">
                  <span
                    class="pbr-drag-handle"
                    draggable="true"
                    @dragstart="onSlideDragStart($event, index)"
                    @dragend="onSlideDragEnd"
                    :title="$t('presentationBuilder.dragToReorder')"
                  >
                    <i class="bi bi-grip-vertical"></i>
                  </span>
                  <span class="pbr-slide-num">{{ index + 1 }}</span>
                  <button
                    class="pbr-slide-del"
                    @click.stop="deleteSlide(slide.slideId)"
                    v-if="(currentPresentation?.slides?.length || 0) > 1"
                    :title="$t('presentationBuilder.delete')"
                  >
                    <i class="bi bi-x"></i>
                  </button>
                </div>
                <span class="pbr-slide-preview-title">{{ slide.title || $t('presentationBuilder.noTitle') }}</span>
                <span class="pbr-slide-preview-body">{{ (slide.content || '').substring(0, 80) }}{{ (slide.content || '').length > 80 ? '...' : '' }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- Col 2: Slide Editor -->
        <main class="pbr-col-editor">
          <div class="pbr-panel pbr-panel-fill">
            <div class="pbr-panel-header">
              <span class="pbr-panel-title">슬라이드 편집</span>
              <div class="pbr-export-group">
                <button class="btn btn-sm btn-outline-secondary pbr-export-btn" @click="startSlideshow" :disabled="!currentPresentation" :title="$t('presentationBuilder.slideshow')">
                  <i class="bi bi-play-circle me-1"></i>{{ $t('presentationBuilder.slideshow') }}
                </button>
                <button class="btn btn-sm btn-outline-primary pbr-export-btn pbr-export-pptx" @click="exportPptx" :disabled="!currentPresentation || exportingPptx" title="PowerPoint 파일로 다운로드">
                  <span v-if="exportingPptx" class="pbr-export-spinner"></span>
                  <i v-else class="bi bi-file-earmark-ppt me-1"></i>
                  {{ exportingPptx ? '저장 중...' : 'PPTX' }}
                </button>
                <button class="btn btn-sm pbr-export-btn pbr-export-pdf" @click="exportPdf" :disabled="!currentPresentation || exportingPdf" title="PDF로 다운로드 (서버에 LibreOffice 필요)">
                  <span v-if="exportingPdf" class="pbr-export-spinner"></span>
                  <i v-else class="bi bi-file-pdf me-1"></i>
                  {{ exportingPdf ? '변환 중...' : 'PDF' }}
                </button>
              </div>
            </div>
            <div class="pbr-panel-body">
              <template v-if="selectedSlide">
                <div class="pbr-preview-wrap">
                  <div class="pbr-preview-slide" :data-theme="effectiveThemeId || 'default'" :data-layout="selectedSlide.layout || 'title-content'">
                    <div class="pbr-prev-inner" :data-layout="selectedSlide.layout || 'title-content'">
                      <!-- title-only: 대형 중앙 제목 -->
                      <template v-if="selectedSlide.layout === 'title-only'">
                        <div class="pbr-layout-center">
                          <div class="pbr-prev-title pbr-title-huge">{{ selectedSlide.title || '(제목)' }}</div>
                          <div v-if="selectedSlide.content?.trim()" class="pbr-prev-subtitle pbr-prev-markdown" v-html="renderMarkdown(firstLine(selectedSlide.content))"></div>
                        </div>
                      </template>
                      <!-- section-header: 섹션 구분자 -->
                      <template v-else-if="selectedSlide.layout === 'section-header'">
                        <div class="pbr-layout-section-header">
                          <div class="pbr-section-accent"></div>
                          <div class="pbr-prev-title pbr-title-section">{{ selectedSlide.title || '(섹션 제목)' }}</div>
                          <div v-if="selectedSlide.content?.trim()" class="pbr-prev-subtitle pbr-prev-markdown" v-html="renderMarkdown(selectedSlide.content)"></div>
                        </div>
                      </template>
                      <!-- quote: 인용구 -->
                      <template v-else-if="selectedSlide.layout === 'quote'">
                        <div class="pbr-layout-center pbr-layout-quote">
                          <div class="pbr-quote-mark">"</div>
                          <div class="pbr-quote-text pbr-prev-markdown" v-html="renderMarkdown(selectedSlide.content || '')"></div>
                          <div v-if="selectedSlide.title?.trim()" class="pbr-quote-author">— {{ selectedSlide.title }}</div>
                        </div>
                      </template>
                      <!-- thank-you: 마무리 슬라이드 -->
                      <template v-else-if="selectedSlide.layout === 'thank-you'">
                        <div class="pbr-layout-center pbr-layout-thank-you">
                          <div class="pbr-thankyou-icon">✨</div>
                          <div class="pbr-prev-title pbr-title-huge">{{ selectedSlide.title || 'Thank You' }}</div>
                          <div v-if="selectedSlide.content?.trim()" class="pbr-prev-subtitle pbr-prev-markdown" v-html="renderMarkdown(selectedSlide.content)"></div>
                        </div>
                      </template>
                      <!-- image-title: 이미지 + 콘텐츠 -->
                      <template v-else-if="selectedSlide.layout === 'image-title'">
                        <div class="pbr-prev-title">{{ selectedSlide.title || '(제목)' }}</div>
                        <div class="pbr-layout-image-title">
                          <div class="pbr-img-side">
                            <img v-if="selectedSlide.imageUrl" :src="selectedSlide.imageUrl" class="pbr-slide-img" />
                            <div v-else class="pbr-img-placeholder">
                              <i class="bi bi-image"></i>
                              <span v-if="selectedSlide.imageDescription" class="pbr-img-desc-hint">{{ selectedSlide.imageDescription }}</span>
                            </div>
                          </div>
                          <div class="pbr-content-side">
                            <div class="pbr-prev-body pbr-prev-markdown" v-html="renderMarkdown(selectedSlide.content || '')"></div>
                          </div>
                        </div>
                      </template>
                      <!-- two-column / comparison: 2단 -->
                      <template v-else-if="(selectedSlide.layout || '').match(/two-column|comparison/)">
                        <div class="pbr-prev-title">{{ selectedSlide.title || '(제목)' }}</div>
                        <div class="pbr-prev-two-col">
                          <div class="pbr-prev-col pbr-prev-markdown" v-html="renderMarkdown(previewLeftContent)"></div>
                          <div class="pbr-prev-col pbr-prev-markdown" v-html="renderMarkdown(previewRightContent)"></div>
                        </div>
                      </template>
                      <!-- default: title-content -->
                      <template v-else>
                        <div class="pbr-prev-title">{{ selectedSlide.title || '(제목)' }}</div>
                        <div class="pbr-prev-body pbr-prev-markdown" v-html="renderMarkdown(selectedSlide.content || '')"></div>
                        <div v-if="selectedSlide.tables?.length" class="pbr-prev-tables">
                          <table v-for="(tbl, ti) in selectedSlide.tables" :key="ti" class="pbr-prev-table">
                            <thead v-if="tbl.headerRow && tbl.rows?.length">
                              <tr><th v-for="(cell, ci) in tbl.rows[0]" :key="ci">{{ cell }}</th></tr>
                            </thead>
                            <tbody>
                              <tr v-for="(row, ri) in (tbl.headerRow ? tbl.rows?.slice(1) : tbl.rows) || []" :key="ri">
                                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                        <div v-if="selectedSlide.charts?.length" class="pbr-prev-charts">
                          <div v-for="(ch, chi) in selectedSlide.charts" :key="chi" class="pbr-prev-chart">
                            <div class="pbr-prev-chart-title">{{ ch.title }}</div>
                            <table class="pbr-prev-table pbr-prev-chart-data" v-if="ch.data && Object.keys(ch.data).length">
                              <tbody>
                                <tr v-for="(val, key) in ch.data" :key="String(key)"><th>{{ key }}</th><td>{{ val }}</td></tr>
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </template>
                    </div>
                    <div class="pbr-prev-num">{{ (currentPresentation?.slides?.findIndex(s => s.slideId === selectedSlideId) ?? -1) + 1 || 1 }} / {{ currentPresentation?.slides?.length || 0 }}</div>
                  </div>
                </div>
                <div class="pbr-fields">
                  <div class="pbr-field-group">
                    <label class="pbr-label">제목</label>
                    <input type="text" class="pbr-input" v-model="selectedSlide.title" @blur="saveSlide" :placeholder="$t('presentationBuilder.slideTitle')">
                  </div>
                  <div class="pbr-field-group">
                    <label class="pbr-label">본문 <span class="pbr-optional">(Markdown 지원)</span></label>
                    <textarea class="pbr-textarea" v-model="selectedSlide.content" @blur="saveSlide" rows="5" :placeholder="$t('presentationBuilder.slideContent')"></textarea>
                    <small class="pbr-form-hint">**굵게**, *기울임*, 목록(-), 표 등 Markdown 형식으로 입력 가능</small>
                  </div>
                  <div class="pbr-field-row">
                    <div class="pbr-field-group">
                      <label class="pbr-label">레이아웃</label>
                      <select class="pbr-select" v-model="selectedSlide.layout" @change="saveSlide">
                        <option value="title-content">제목 + 본문</option>
                        <option value="title-only">제목만</option>
                        <option value="two-column">2단 레이아웃</option>
                        <option value="image-title">이미지 + 제목</option>
                        <option value="section-header">섹션 헤더</option>
                        <option value="comparison">비교</option>
                        <option value="quote">인용</option>
                        <option value="thank-you">감사 / 끝맺음</option>
                      </select>
                    </div>
                    <div class="pbr-field-group">
                      <label class="pbr-label">슬라이드 이미지 <span class="pbr-optional">선택사항</span></label>
                      <input ref="slideImageInputRef" type="file" class="d-none" accept="image/*" @change="onSlideImageSelected">
                      <div v-if="!selectedSlide.imageUrl" class="pbr-img-upload" @click="triggerSlideImageUpload">
                        <i class="bi bi-image"></i>
                        <span>클릭하여 이미지 추가</span>
                      </div>
                      <div v-else class="pbr-img-preview">
                        <img :src="selectedSlide.imageUrl" alt="slide image">
                        <button class="pbr-img-remove" @click="removeSlideImage" :title="$t('presentationBuilder.removeImage')">
                          <i class="bi bi-x"></i>
                        </button>
                      </div>
                      <small v-if="selectedSlide.imageDescription" class="pbr-img-hint">{{ selectedSlide.imageDescription }}</small>
                    </div>
                  </div>
                  <!-- 표 편집 -->
                  <div class="pbr-field-group">
                    <div class="pbr-tables-header">
                      <label class="pbr-label">표</label>
                      <button class="pbr-btn-add-table" @click="addTable">
                        <i class="bi bi-table me-1"></i>표 추가
                      </button>
                    </div>
                    <div v-if="selectedSlide.tables?.length" class="pbr-table-editors">
                      <div
                        v-for="(tbl, tblIdx) in selectedSlide.tables"
                        :key="tblIdx"
                        class="pbr-table-editor"
                      >
                        <div class="pbr-table-editor-header">
                          <span class="pbr-table-editor-label">표 {{ tblIdx + 1 }}</span>
                          <div class="pbr-table-editor-actions">
                            <label class="pbr-check-inline">
                              <input type="checkbox" v-model="tbl.headerRow" @change="saveSlide"> 헤더행
                            </label>
                            <button class="pbr-icon-btn" @click="addTableRow(tblIdx)" title="행 추가"><i class="bi bi-plus-square"></i></button>
                            <button class="pbr-icon-btn" @click="addTableCol(tblIdx)" title="열 추가"><i class="bi bi-layout-three-columns"></i></button>
                            <button class="pbr-icon-btn pbr-icon-btn-danger" @click="removeTable(tblIdx)" title="표 삭제"><i class="bi bi-trash"></i></button>
                          </div>
                        </div>
                        <div class="pbr-table-grid-wrap">
                          <div
                            class="pbr-table-grid"
                            :style="{ gridTemplateColumns: `repeat(${(tbl.rows[0]?.length || 1) + 1}, 1fr)` }"
                          >
                            <template v-for="(row, rowIdx) in tbl.rows" :key="rowIdx">
                              <input
                                v-for="(cell, colIdx) in row"
                                :key="colIdx"
                                class="pbr-table-cell"
                                :class="{ 'pbr-table-head-cell': rowIdx === 0 && tbl.headerRow }"
                                :value="cell"
                                @input="updateTableCell(tblIdx, rowIdx, colIdx, ($event.target as HTMLInputElement).value)"
                                @blur="saveSlide"
                              />
                              <button class="pbr-table-del-row" @click="removeTableRow(tblIdx, rowIdx)" title="행 삭제">
                                <i class="bi bi-dash-circle"></i>
                              </button>
                            </template>
                            <!-- 열 삭제 버튼 행 -->
                            <template v-if="tbl.rows[0]?.length">
                              <button
                                v-for="(_, colIdx) in tbl.rows[0]"
                                :key="'del-col-' + colIdx"
                                class="pbr-table-del-col"
                                @click="removeTableCol(tblIdx, colIdx)"
                                title="열 삭제"
                              ><i class="bi bi-dash-circle"></i></button>
                              <div class="pbr-table-corner"></div>
                            </template>
                          </div>
                        </div>
                      </div>
                    </div>
                    <p v-else class="pbr-form-hint">표가 없습니다. 위 버튼으로 추가하세요.</p>
                  </div>

                  <div class="pbr-save-row">
                    <button class="btn btn-primary pbr-save-btn" @click="saveSlide">
                      <i class="bi bi-check me-2"></i>저장
                    </button>
                    <span class="pbr-saved-hint" :class="{ show: savedHint }">{{ savedHint }}</span>
                  </div>
                </div>
              </template>
              <div v-else class="pbr-empty-editor">
                <i class="bi bi-file-earmark-slides"></i>
                <p>슬라이드를 선택하세요</p>
              </div>
            </div>
          </div>
        </main>

        <!-- Col 3: Properties -->
        <aside class="pbr-col-props">
          <div class="pbr-panel">
            <div class="pbr-panel-header">
              <span class="pbr-panel-title">속성</span>
            </div>
            <div class="pbr-panel-body pbr-props-body">
              <div class="pbr-field-group" v-if="currentPresentation">
                <label class="pbr-label">프레젠테이션 제목</label>
                <input type="text" class="pbr-input" v-model="currentPresentation.title" @blur="savePresentation">
              </div>

              <div class="pbr-field-group" v-if="currentPresentation">
                <label class="pbr-label">테마</label>
                <select class="pbr-select" :value="currentPresentation.themeId || ''" @change="applyTheme(($event.target as HTMLSelectElement).value)">
                  <option value="">기본</option>
                  <option v-for="t in availableThemes" :key="t.themeId" :value="t.themeId">{{ t.name }}</option>
                </select>
              </div>

              <div class="pbr-theme-preview-wrap" v-if="currentPresentation">
                <div class="pbr-theme-mini" :data-theme="effectiveThemeId || 'default'">
                  <div class="pbr-tm-bar"></div>
                  <div class="pbr-tm-lines">
                    <span></span><span></span><span class="pbr-tm-short"></span>
                  </div>
                </div>
              </div>

              <div class="pbr-field-group" v-if="selectedSlide">
                <label class="pbr-label">현재 슬라이드</label>
                <input type="number" class="pbr-input pbr-slide-num-input" :value="selectedSlide.slideNumber" min="1" readonly>
              </div>

              <div class="pbr-divider"></div>

              <div class="pbr-stats" v-if="currentPresentation">
                <div class="pbr-stat">
                  <span class="pbr-stat-label">총 슬라이드</span>
                  <span class="pbr-stat-val">{{ currentPresentation?.slides?.length || 0 }}</span>
                </div>
              </div>

              <div class="pbr-divider"></div>

              <button class="btn btn-primary w-100 pbr-regen-btn" @click="showGenerateModal = true">
                <i class="bi bi-magic me-2"></i>{{ $t('presentationBuilder.createNew') }}
              </button>
              <button class="btn btn-outline-secondary w-100 pbr-back-btn" @click="createNewPresentation">
                <i class="bi bi-arrow-left me-2"></i>{{ $t('presentationBuilder.backToList') }}
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
    <!-- Toast -->
    <div class="pb-toast" :class="['pb-toast--' + toastType, { show: showToast }]">
      <i :class="toastType === 'error' ? 'bi bi-exclamation-circle' : toastType === 'info' ? 'bi bi-info-circle' : 'bi bi-check-circle'"></i>
      <span>{{ toastText }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 단일 줄바꿈(\n)을 <br>로 변환 (gfm breaks)
marked.use({ breaks: true })

const { t } = useI18n()

function renderMarkdown(text: string): string {
  if (!text?.trim()) return ''
  return DOMPurify.sanitize(marked.parse(text) as string)
}

function firstLine(text: string): string {
  if (!text?.trim()) return ''
  return text.split(/\r?\n/).find(l => l.trim()) || ''
}
import './PresentationBuilder.css'
import type { 
  ApiServiceDto, 
  PresentationDto, 
  PresentationListItemDto,
  SlideDto, 
  PresentationGenerationRequestDto,
  PresentationTemplateDto,
  PresentationThemeConfig
} from '@/types'

const showGenerateModal = ref(false)
const showLoadModal = ref(false)
const generating = ref(false)
const loadModalLoading = ref(false)
const loadModalError = ref<string | null>(null)
const savedPresentations = ref<PresentationListItemDto[]>([])
const currentPresentation = ref<PresentationDto | null>(null)
const selectedSlideId = ref<string | null>(null)
const aiServices = ref<ApiServiceDto[]>([])
const availableModels = ref<string[]>([])
const availableTemplates = ref<PresentationTemplateDto[]>([])
const selectedTemplate = ref<PresentationTemplateDto | null>(null)
const availableThemes = ref<PresentationThemeConfig[]>([])
const imageServices = ref<ApiServiceDto[]>([])
const imageModels = ref<string[]>([])
const dragFromIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
const showSlideshowMode = ref(false)
const slideshowIndex = ref(0)
const reordering = ref(false)
const exportingPptx = ref(false)
const exportingPdf = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const showToast = ref(false)
const toastText = ref(t('presentationBuilder.done'))
const toastType = ref<'success' | 'error' | 'info'>('success')
let loadingStepInterval: ReturnType<typeof setInterval> | null = null

const generationRequest = ref<PresentationGenerationRequestDto>({
  prompt: '',
  pasteContent: '',
  importUrl: '',
  sourceType: 'topic',
  slideCount: 5,
  templateId: undefined,
  serviceId: 0,
  style: 'business',
  slideSize: '16:9',
  themeId: '',
  includeAiImages: false,
  imageServiceId: undefined,
  imageModel: undefined
})

const selectedSlide = computed(() => {
  if (!currentPresentation.value || !selectedSlideId.value) return null
  const slides = currentPresentation.value.slides
  if (!slides?.length) return null
  return slides.find(s => s.slideId === selectedSlideId.value) || null
})

const contentLength = computed(() => {
  const st = generationRequest.value.sourceType || 'topic'
  if (st === 'topic') return (generationRequest.value.prompt || '').length
  if (st === 'paste') return (generationRequest.value.pasteContent || '').length
  return 0
})

const effectiveThemeId = computed(() => {
  const tid = currentPresentation.value?.themeId || ''
  return tid || 'default'
})

const slides = computed(() => currentPresentation.value?.slides || [])
const slideshowSlide = computed(() => slides.value[slideshowIndex.value] || null)
const slideshowLeftContent = computed(() => {
  const c = slideshowSlide.value?.content || ''
  const [left] = splitContentForTwoColumns(c)
  return left
})
const slideshowRightContent = computed(() => {
  const c = slideshowSlide.value?.content || ''
  const [, right] = splitContentForTwoColumns(c)
  return right
})

/** 2단 레이아웃 미리보기용 좌측 콘텐츠 (백엔드 SplitContentForTwoColumns와 동일 로직) */
const previewLeftContent = computed(() => {
  const c = selectedSlide.value?.content || ''
  const [left] = splitContentForTwoColumns(c)
  return left
})
/** 2단 레이아웃 미리보기용 우측 콘텐츠 */
const previewRightContent = computed(() => {
  const c = selectedSlide.value?.content || ''
  const [, right] = splitContentForTwoColumns(c)
  return right
})

function splitContentForTwoColumns(content: string): [string, string] {
  if (!content?.trim()) return ['', '']
  const lines = content.split(/\r?\n/)
  const sections: string[] = []
  let current: string[] = []
  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('**') && trimmed.endsWith('**') && trimmed.length > 4) {
      if (current.length > 0) {
        sections.push(current.join('\n'))
        current = []
      }
    }
    if (line || current.length > 0) current.push(line)
  }
  if (current.length > 0) sections.push(current.join('\n'))
  if (sections.length === 0) {
    const nonEmpty = lines.filter(l => l.trim())
    const mid = Math.ceil(nonEmpty.length / 2)
    return [nonEmpty.slice(0, mid).join('\n'), nonEmpty.slice(mid).join('\n')]
  }
  if (sections.length === 1) {
    const inner = sections[0].split(/\r?\n/).filter(l => l.trim())
    const mid = Math.ceil(inner.length / 2)
    return [inner.slice(0, mid).join('\n'), inner.slice(mid).join('\n')]
  }
  const mid = Math.ceil(sections.length / 2)
  return [sections.slice(0, mid).join('\n\n'), sections.slice(mid).join('\n\n')]
}

const savedHint = ref('')
const slideImageInputRef = ref<HTMLInputElement | null>(null)

const loadingStep = ref(1)
const loadingProgress = ref(0)

const loadAiServices = async () => {
  try {
    const response = await api.get<ApiServiceDto[]>('/apiservices')
    aiServices.value = (response.data || []).filter(
      s => s.serviceType === 'Chat' || s.serviceType === 'Both'
    )
  } catch (error: any) {
    console.error('AI 서비스 로드 실패:', error)
  }
}

const loadTemplates = async () => {
  try {
    const response = await api.get<PresentationTemplateDto[]>('/presentation-templates')
    availableTemplates.value = response.data || []
  } catch (error: any) {
    console.error('템플릿 로드 실패:', error)
    availableTemplates.value = []
  }
}

const loadThemes = async () => {
  try {
    const response = await api.get<PresentationThemeConfig[]>('/presentations/themes')
    availableThemes.value = response.data || []
  } catch (error: any) {
    console.error('테마 로드 실패:', error)
    availableThemes.value = []
  }
}

const loadImageServices = async () => {
  try {
    const response = await api.get<ApiServiceDto[]>('/apiservices')
    imageServices.value = (response.data || []).filter(
      (s: ApiServiceDto) => s.serviceType === 'ImageGeneration' || s.serviceType === 'Both'
    )
  } catch (error: any) {
    console.error('이미지 서비스 로드 실패:', error)
    imageServices.value = []
  }
}

function getDefaultThemeIdForStyle(style: string): string {
  const s = (style || '').trim().toLowerCase()
  switch (s) {
    case 'business': return 'business-blue'
    case 'education': return 'education'
    case 'marketing': return 'marketing'
    case 'creative': return 'minimal'
    default: return ''
  }
}

const onTemplateChange = () => {
  if (generationRequest.value.templateId) {
    selectedTemplate.value = availableTemplates.value.find(
      t => t.templateId === generationRequest.value.templateId
    ) || null
    if (selectedTemplate.value?.templateStructure) {
      generationRequest.value.slideCount = selectedTemplate.value.templateStructure.slideCount
    }
  } else {
    selectedTemplate.value = null
  }
}

// 스타일 변경 시 해당 스타일에 맞는 테마를 기본으로 제안
watch(() => generationRequest.value.style, (newStyle) => {
  generationRequest.value.themeId = getDefaultThemeIdForStyle(newStyle || '')
}, { immediate: true })

// 생성 모달을 열 때 템플릿 목록 갱신 (시스템 관리에서 등록한 템플릿 반영)
watch(showGenerateModal, (open) => {
  if (open) loadTemplates()
})

// 불러오기 모달을 열 때 PRESENTATIONS 테이블에서 목록 로드
watch(showLoadModal, (open) => {
  if (open) {
    loadModalError.value = null
    loadSavedPresentations()
  } else {
    loadModalLoading.value = false
    loadModalError.value = null
  }
})

/** PRESENTATIONS 테이블에서 저장된 프레젠테이션 목록 조회 */
const loadSavedPresentations = async () => {
  loadModalLoading.value = true
  loadModalError.value = null
  savedPresentations.value = []
  try {
    const res = await api.get<PresentationListItemDto[]>('/presentations/list', { timeout: 15000 })
    const data = res.data
    if (Array.isArray(data)) {
      savedPresentations.value = data
    } else {
      savedPresentations.value = []
    }
  } catch (err: any) {
    console.error('프레젠테이션 목록 로드 실패:', err)
    savedPresentations.value = []
    const status = err?.response?.status
    const msg = err?.response?.data?.message || err?.message || String(err)
    if (status === 401) {
      loadModalError.value = t('presentationBuilder.loginRequired')
    } else if (status === 404) {
      loadModalError.value = 'API 경로를 찾을 수 없습니다. 서버 설정을 확인해주세요.'
    } else {
      loadModalError.value = msg ? `목록 로드 실패: ${msg}` : t('presentationBuilder.loadFailed')
    }
  } finally {
    loadModalLoading.value = false
  }
}

/** 선택한 프레젠테이션 상세 로드 (GET /presentations/{id}) */
const loadPresentation = async (p: PresentationListItemDto) => {
  loadModalError.value = null
  try {
    const res = await api.get<PresentationDto>(`/presentations/${p.presentationId}`)
    const pres = res.data
    if (!pres) {
      loadModalError.value = '프레젠테이션 데이터를 받지 못했습니다.'
      return
    }
    currentPresentation.value = pres
    selectedSlideId.value = pres.slides?.length ? pres.slides[0].slideId : null
    showLoadModal.value = false
  } catch (err: any) {
    console.error('프레젠테이션 로드 실패:', err)
    const msg = err?.response?.data?.message || err?.message
    loadModalError.value = msg ? `불러오기 실패: ${msg}` : t('presentationBuilder.presentationLoadFailed')
  }
}

function formatDate(d: string | Date | undefined): string {
  if (!d) return ''
  const dt = typeof d === 'string' ? new Date(d) : d
  return dt.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' })
}

const loadModels = async (serviceId: number) => {
  if (!serviceId) {
    availableModels.value = []
    return
  }
  try {
    const response = await api.get<string[]>(`/apiservices/${serviceId}/models`)
    availableModels.value = response.data || []
  } catch (error: any) {
    console.error('모델 목록 로드 실패:', error)
    availableModels.value = []
  }
}

const generatePresentation = async () => {
  const req = generationRequest.value
  const st = req.sourceType || 'topic'
  if (st === 'topic' && !req.prompt?.trim()) {
    alert(t('presentationBuilder.enterTopic'))
    return
  }
  if (st === 'paste' && !req.pasteContent?.trim()) {
    alert(t('presentationBuilder.enterPasteText'))
    return
  }
  if (st === 'import' && !req.importUrl?.trim()) {
    alert(t('presentationBuilder.enterUrl'))
    return
  }
  if (!req.serviceId) {
    alert('AI 서비스를 선택해주세요.')
    return
  }
  if (req.includeAiImages && (!req.imageServiceId || req.imageServiceId <= 0)) {
    alert('AI 이미지를 사용하려면 이미지 생성 서비스를 선택해주세요.')
    return
  }

  generating.value = true
  loadingStep.value = 1
  loadingProgress.value = 10
  loadingStepInterval = setInterval(() => {
    if (loadingStep.value < 4) {
      loadingStep.value++
      loadingProgress.value = Math.min(90, loadingProgress.value + 25)
    } else {
      loadingProgress.value = Math.min(95, loadingProgress.value + 2)
    }
  }, 800)

  try {
    let response
    if (generationRequest.value.templateId) {
      // 템플릿 기반 생성
      response = await api.post<PresentationDto>(
        `/presentation-templates/${generationRequest.value.templateId}/generate`,
        generationRequest.value
      )
    } else {
      // 일반 생성
      response = await api.post<PresentationDto>('/presentations/generate', generationRequest.value)
    }
    
    currentPresentation.value = response.data
    if (response.data.slides.length > 0) {
      selectedSlideId.value = response.data.slides[0].slideId
    }
    showGenerateModal.value = false
    if (loadingStepInterval) {
      clearInterval(loadingStepInterval)
      loadingStepInterval = null
    }
    loadingStep.value = 4
    loadingProgress.value = 100
    showExportToast(t('presentationBuilder.generated'))
  } catch (error: any) {
    console.error('프레젠테이션 생성 실패:', error)
    const data = error.response?.data
    const msg = typeof data === 'string' ? data : (data?.message ?? data?.detail ?? data?.title)
    const text = (msg && String(msg).trim()) ? String(msg) : (error.response?.statusText || t('presentationBuilder.generateFailed'))
    alert(text)
  } finally {
    generating.value = false
    if (loadingStepInterval) {
      clearInterval(loadingStepInterval)
      loadingStepInterval = null
    }
  }
}

const createNewPresentation = () => {
  if (currentPresentation.value && !confirm(t('presentationBuilder.confirmNewWithoutSave'))) return
  currentPresentation.value = null
  selectedSlideId.value = null
  showGenerateModal.value = true
}

const triggerFileImport = () => {
  fileInputRef.value?.click()
}

const triggerSlideImageUpload = () => {
  slideImageInputRef.value?.click()
}

const onSlideImageSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || !selectedSlide.value || !currentPresentation.value) return
  if (!file.type.startsWith('image/')) {
    toastText.value = t('presentationBuilder.imageOnly')
    showToast.value = true
    setTimeout(() => { showToast.value = false }, 2500)
    input.value = ''
    return
  }
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await api.post<{ path: string }>('/files/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const path = res.data?.path
    if (path) {
      const url = path.startsWith('/') ? `/api/files/download${path}` : `/api/files/download/${path}`
      selectedSlide.value.imageUrl = url
      selectedSlide.value.imageDescription = undefined
      await saveSlide()
    }
  } catch (err: any) {
    console.error('이미지 업로드 실패:', err)
    toastText.value = err.response?.data?.message || t('presentationBuilder.imageUploadFailed')
    showToast.value = true
    setTimeout(() => { showToast.value = false }, 2500)
  }
  input.value = ''
}

const removeSlideImage = async () => {
  if (!selectedSlide.value) return
  selectedSlide.value.imageUrl = undefined
  selectedSlide.value.imageDescription = undefined
  await saveSlide()
}

const onFileSelected = (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const name = file.name.toLowerCase()
  if (!name.endsWith('.pptx') && !name.endsWith('.ppt') && !name.endsWith('.pdf')) {
    toastText.value = 'PPTX, PPT, PDF 파일만 지원됩니다.'
    showToast.value = true
    setTimeout(() => { showToast.value = false }, 2500)
    input.value = ''
    return
  }
  toastText.value = t('presentationBuilder.importPreparing')
  showToast.value = true
  setTimeout(() => { showToast.value = false }, 2500)
  input.value = ''
}

const selectSlide = (slideId: string) => {
  selectedSlideId.value = slideId
}

/** 저장용 슬라이드 복사 (data URL 제거로 요청 크기 축소, 저장 오류 방지) */
function slideForSave(slide: SlideDto): SlideDto {
  const imgUrl = slide.imageUrl?.startsWith('data:') ? undefined : slide.imageUrl
  const images = slide.images?.filter((u): u is string => typeof u === 'string' && !u.startsWith('data:')) ?? []
  return { ...slide, imageUrl: imgUrl, images }
}

const saveSlide = async () => {
  if (!currentPresentation.value || !selectedSlideId.value) return
  const pres = currentPresentation.value
  if (!pres.presentationId) {
    alert(t('presentationBuilder.noPresentationToSave'))
    return
  }

  const slide = pres.slides.find(s => s.slideId === selectedSlideId.value)
  if (!slide) return

  try {
    // PUT slides 한 번만 호출 (내부에서 전체 프레젠테이션 저장). data URL 제거 후 전송.
    const res = await api.put<PresentationDto>(
      `/presentations/${pres.presentationId}/slides/${selectedSlideId.value}`,
      slideForSave(slide)
    )
    if (res.data) currentPresentation.value = res.data
    savedHint.value = t('presentationBuilder.saved')
    setTimeout(() => { savedHint.value = '' }, 2500)
  } catch (error: any) {
    console.error('슬라이드 저장 실패:', error)
    const msg = error.response?.data?.message ?? error.message ?? t('presentationBuilder.saveFailed')
    alert(msg)
  }
}

const savePresentation = async () => {
  if (!currentPresentation.value) return
  const pres = currentPresentation.value
  if (!pres.presentationId) {
    alert(t('presentationBuilder.noPresentationToSave'))
    return
  }

  try {
    const res = await api.put<PresentationDto>(`/presentations/${pres.presentationId}`, pres)
    if (res.data) currentPresentation.value = res.data
  } catch (error: any) {
    console.error('프레젠테이션 저장 실패:', error)
    const msg = error.response?.data?.message ?? error.message ?? t('presentationBuilder.saveFailed')
    alert(msg)
  }
}

// ──────────────────────────────────────────────
// 마크다운 표 파싱 & 표 편집 헬퍼
// ──────────────────────────────────────────────

/**
 * content 문자열에서 마크다운 표를 찾아 TableDto[] 로 변환하고,
 * 표가 제거된 content 텍스트를 반환한다.
 */
/**
 * content 문자열에서 마크다운 표를 찾아 TableDto[] 로 변환하고,
 * 표가 제거된 content 텍스트를 반환한다.
 * - 각 행의 끝 | 는 선택사항 (일부 AI 생성 마크다운은 생략함)
 */
function parseMarkdownTablesFromContent(content: string): { tables: { headerRow: boolean; rows: string[][] }[]; contentWithoutTables: string } {
  const tables: { headerRow: boolean; rows: string[][] }[] = []

  // 마크다운 표 패턴: 헤더행 + 구분선 + 1개 이상의 데이터행
  // 끝 |는 선택적 (\|?), Windows/Unix 줄바꿈 모두 지원
  const tablePattern = /^([ \t]*\|[^\n]+?\|?[ \t]*\r?\n)([ \t]*\|[ \t]*[-: |]+?[ \t]*\|?[ \t]*\r?\n)((?:[ \t]*\|[^\n]+?\|?[ \t]*\r?\n?)+)/gm
  let contentWithoutTables = content

  /** 파이프(|)로 구분된 마크다운 행을 셀 배열로 변환 */
  const parseRow = (line: string): string[] => {
    const trimmed = line.trim().replace(/\r$/, '')
    const parts = trimmed.split('|')
    if (parts.length > 0 && parts[0].trim() === '') parts.shift()
    if (parts.length > 0 && parts[parts.length - 1].trim() === '') parts.pop()
    return parts.map((c: string) => c.trim()).filter((c: string) => c !== '')
  }

  let match: RegExpExecArray | null
  while ((match = tablePattern.exec(content)) !== null) {
    const headerLine = match[1]
    const dataBlock  = match[3]

    const headerCells = parseRow(headerLine)
    const dataRows = dataBlock
      .split('\n')
      .map((l: string) => l.replace(/\r$/, ''))
      .filter((l: string) => l.trim().includes('|'))
      .map(parseRow)
      .filter((r: string[]) => r.length > 0)

    if (headerCells.length > 0 && dataRows.length > 0) {
      tables.push({ headerRow: true, rows: [headerCells, ...dataRows] })
    }
    contentWithoutTables = contentWithoutTables.replace(match[0], '\n')
  }

  return { tables, contentWithoutTables: contentWithoutTables.replace(/\n{3,}/g, '\n\n').trim() }
}

/**
 * 슬라이드가 바뀔 때, tables 가 비어있고 content 에 마크다운 표가 있으면
 * 자동으로 tables 로 이동시키고 content 에서 제거한다.
 * ※ 즉시 저장하지 않음 — 다음 사용자 동작(blur/저장 버튼)이 발생할 때 함께 저장됨.
 */
let _mdTableExtractTimer: ReturnType<typeof setTimeout> | null = null

function tryExtractMarkdownTables() {
  const slide = selectedSlide.value
  if (!slide) return
  if (slide.tables && slide.tables.length > 0) return
  const { tables, contentWithoutTables } = parseMarkdownTablesFromContent(slide.content || '')
  if (tables.length === 0) return
  slide.tables = tables
  slide.content = contentWithoutTables
}

watch(selectedSlideId, () => {
  if (_mdTableExtractTimer) { clearTimeout(_mdTableExtractTimer); _mdTableExtractTimer = null }
  // 즉시 시도 + 200ms 후 재시도 (데이터 로딩 타이밍 보정)
  tryExtractMarkdownTables()
  _mdTableExtractTimer = setTimeout(() => {
    _mdTableExtractTimer = null
    tryExtractMarkdownTables()
  }, 200)
})

const addTable = () => {
  if (!selectedSlide.value) return
  if (!selectedSlide.value.tables) selectedSlide.value.tables = []
  selectedSlide.value.tables.push({ headerRow: true, rows: [['헤더1', '헤더2'], ['내용1', '내용2']] })
}

const removeTable = (tblIdx: number) => {
  if (!selectedSlide.value?.tables) return
  selectedSlide.value.tables.splice(tblIdx, 1)
  saveSlide()
}

const addTableRow = (tblIdx: number) => {
  const tbl = selectedSlide.value?.tables?.[tblIdx]
  if (!tbl) return
  const cols = tbl.rows[0]?.length || 2
  tbl.rows.push(Array(cols).fill('').map(() => ''))
}

const addTableCol = (tblIdx: number) => {
  const tbl = selectedSlide.value?.tables?.[tblIdx]
  if (!tbl) return
  for (const row of tbl.rows) row.push('')
}

const removeTableRow = (tblIdx: number, rowIdx: number) => {
  const tbl = selectedSlide.value?.tables?.[tblIdx]
  if (!tbl || tbl.rows.length <= 1) return
  tbl.rows.splice(rowIdx, 1)
  saveSlide()
}

const removeTableCol = (tblIdx: number, colIdx: number) => {
  const tbl = selectedSlide.value?.tables?.[tblIdx]
  if (!tbl) return
  if ((tbl.rows[0]?.length || 0) <= 1) return
  for (const row of tbl.rows) row.splice(colIdx, 1)
  saveSlide()
}

const updateTableCell = (tblIdx: number, rowIdx: number, colIdx: number, value: string) => {
  const tbl = selectedSlide.value?.tables?.[tblIdx]
  if (!tbl?.rows?.[rowIdx]) return
  tbl.rows[rowIdx][colIdx] = value
}

const addNewSlide = async () => {
  if (!currentPresentation.value) return

  const newSlide: SlideDto = {
    slideId: crypto.randomUUID(),
    slideNumber: currentPresentation.value.slides.length + 1,
    title: t('presentationBuilder.newSlide'),
    content: '',
    layout: 'title-content',
    images: [],
    charts: []
  }

  try {
    await api.post(`/presentations/${currentPresentation.value.presentationId}/slides`, newSlide)
    currentPresentation.value.slides.push(newSlide)
    selectedSlideId.value = newSlide.slideId
  } catch (error: any) {
    console.error('슬라이드 추가 실패:', error)
    alert(t('presentationBuilder.addSlideFailed'))
  }
}

const deleteSlide = async (slideId: string) => {
  if (!currentPresentation.value) return

  if (currentPresentation.value.slides.length <= 1) {
    alert(t('presentationBuilder.minSlidesRequired'))
    return
  }

  if (!confirm(t('presentationBuilder.confirmDeleteSlide'))) return

  try {
    await api.delete(`/presentations/${currentPresentation.value.presentationId}/slides/${slideId}`)
    currentPresentation.value.slides = currentPresentation.value.slides.filter(s => s.slideId !== slideId)
    
    if (selectedSlideId.value === slideId) {
      if (currentPresentation.value.slides.length > 0) {
        selectedSlideId.value = currentPresentation.value.slides[0].slideId
      } else {
        selectedSlideId.value = null
      }
    }
  } catch (error: any) {
    console.error('슬라이드 삭제 실패:', error)
    alert(t('presentationBuilder.deleteSlideFailed'))
  }
}

// 슬라이드 순서 변경 (드래그 앤 드롭)
function onSlideDragStart(e: DragEvent, index: number) {
  dragFromIndex.value = index
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(index))
  }
  if (e.target instanceof HTMLElement) {
    e.target.style.cursor = 'grabbing'
  }
}

function onSlideDragEnd() {
  dragFromIndex.value = null
  dragOverIndex.value = null
  document.querySelectorAll('.slide-drag-handle').forEach(el => {
    if (el instanceof HTMLElement) el.style.cursor = ''
  })
}

function onSlideDragOver(_e: DragEvent, index: number) {
  if (dragFromIndex.value === null) return
  dragOverIndex.value = index
}

function onSlideDragEnter(index: number) {
  if (dragFromIndex.value === null) return
  dragOverIndex.value = index
}

function onSlideDragLeave() {
  // dragleave가 자식으로 버블되므로 약간의 디바운스 없이 바로 null 하면 깜빡임 가능
  dragOverIndex.value = null
}

async function onSlideDrop(_e: DragEvent, toIndex: number) {
  const fromIndex = dragFromIndex.value
  dragFromIndex.value = null
  dragOverIndex.value = null

  if (fromIndex === null || !currentPresentation.value || fromIndex === toIndex) return

  const slides = [...currentPresentation.value.slides]
  const [moved] = slides.splice(fromIndex, 1)
  slides.splice(toIndex, 0, moved)

  // 슬라이드 번호 갱신
  slides.forEach((s, i) => { s.slideNumber = i + 1 })

  const slideIds = slides.map(s => s.slideId)
  reordering.value = true
  try {
    const res = await api.post<PresentationDto>(
      `/presentations/${currentPresentation.value.presentationId}/reorder`,
      { slideIds }
    )
    if (res.data) {
      currentPresentation.value.slides = res.data.slides
    } else {
      currentPresentation.value.slides = slides
    }
  } catch (error: any) {
    console.error('슬라이드 순서 변경 실패:', error)
    alert(error.response?.data?.message || t('presentationBuilder.reorderFailed'))
    currentPresentation.value.slides = [...currentPresentation.value.slides]
  } finally {
    reordering.value = false
  }
}

function startSlideshow() {
  if (!currentPresentation.value?.slides?.length) return
  const idx = currentPresentation.value.slides.findIndex(s => s.slideId === selectedSlideId.value)
  slideshowIndex.value = idx >= 0 ? idx : 0
  showSlideshowMode.value = true
}

function exitSlideshow() {
  showSlideshowMode.value = false
}

function slideshowPrev() {
  if (slideshowIndex.value > 0) slideshowIndex.value--
}

function slideshowNext() {
  if (slideshowIndex.value < slides.value.length - 1) slideshowIndex.value++
}

function handleSlideshowClick(e: MouseEvent) {
  if (!showSlideshowMode.value || slides.value.length <= 1) return
  const target = e.target as HTMLElement
  if (target.closest('.pbr-slideshow-prev')) slideshowPrev()
  else if (target.closest('.pbr-slideshow-next')) slideshowNext()
}

function handleSlideshowKeydown(e: KeyboardEvent) {
  if (!showSlideshowMode.value) return
  if (e.key === 'Escape') exitSlideshow()
  else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    slideshowPrev()
  } else if (e.key === 'ArrowRight' || e.key === ' ') {
    e.preventDefault()
    slideshowNext()
  }
}

const applyTheme = async (themeId: string) => {
  if (!currentPresentation.value) return
  try {
    const res = await api.put<PresentationDto>(
      `/presentations/${currentPresentation.value.presentationId}/theme`,
      { themeId: themeId || '' }
    )
    if (res.data) currentPresentation.value.themeId = res.data.themeId
  } catch (error: any) {
    console.error('테마 적용 실패:', error)
    alert(error.response?.data?.message || t('presentationBuilder.themeApplyFailed'))
  }
}

function showExportToast(text: string, type: 'success' | 'error' | 'info' = 'success', duration = 3000) {
  toastText.value = text
  toastType.value = type
  showToast.value = true
  setTimeout(() => { showToast.value = false }, duration)
}

/**
 * PPTX 내보내기 — axios api 서비스 사용 (인터셉터로 토큰 자동 주입 및 에러 처리)
 */
const exportPptx = async () => {
  if (!currentPresentation.value) return

  exportingPptx.value = true
  try {
    const themeId = currentPresentation.value.themeId || effectiveThemeId.value || 'default'
    const payload: PresentationDto = {
      ...currentPresentation.value,
      themeId
    }

    const response = await api.post<Blob>('/presentations/export/pptx', payload, {
      responseType: 'blob',
      timeout: 60000,
      headers: {
        'Accept': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      }
    })

    // 서버가 빈 응답을 반환한 경우
    if (!response.data || (response.data as Blob).size === 0) {
      showExportToast('PPTX 파일이 비어있습니다. 다시 시도해 주세요.', 'error', 4000)
      return
    }

    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    })
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    const safeTitle = (currentPresentation.value.title || 'presentation').replace(/[^a-zA-Z0-9가-힣\s]/g, '_').trim()
    link.setAttribute('download', `${safeTitle}.pptx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    showExportToast('PPTX 다운로드가 완료되었습니다.')
  } catch (error: any) {
    console.error('PPTX 내보내기 실패:', error)
    // api.ts 인터셉터가 blob 에러를 JSON으로 변환해줌 (responseType: blob 시)
    const status = error?.response?.status
    const data = error?.response?.data
    let message = 'PPTX 내보내기에 실패했습니다.'
    if (status === 503) {
      message = '서버가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.'
    } else if (status === 401) {
      message = '인증이 만료되었습니다. 다시 로그인해 주세요.'
    } else if (data && typeof data === 'object' && data.message) {
      message = data.message
    } else if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      message = 'PPTX 생성 시간이 초과되었습니다. 슬라이드 수를 줄이고 다시 시도해 주세요.'
    } else if (!error?.response) {
      message = '서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.'
    }
    showExportToast(message, 'error', 5000)
  } finally {
    exportingPptx.value = false
  }
}

/**
 * PDF 내보내기 — axios api 서비스 사용 (LibreOffice 없을 시 PPTX로 폴백)
 */
const exportPdf = async () => {
  if (!currentPresentation.value) return

  exportingPdf.value = true
  try {
    const themeId = currentPresentation.value.themeId || effectiveThemeId.value || 'default'
    const payload: PresentationDto = {
      ...currentPresentation.value,
      themeId
    }

    const response = await api.post<Blob>('/presentations/export/pdf', payload, {
      responseType: 'blob',
      timeout: 120000, // LibreOffice PDF 변환 최대 2분
      headers: {
        'Accept': 'application/pdf'
      }
    })

    const blob = response.data as Blob
    if (!blob || blob.size === 0) {
      showExportToast('PDF 파일이 비어있습니다. 다시 시도해 주세요.', 'error', 4000)
      return
    }

    // X-Pdf-Fallback-Pptx: true → LibreOffice 없음, PPTX 폴백
    const isPptxFallback = response.headers['x-pdf-fallback-pptx'] === 'true'
    const ext = isPptxFallback ? 'pptx' : 'pdf'
    const mimeType = isPptxFallback
      ? 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      : 'application/pdf'

    const downloadUrl = window.URL.createObjectURL(new Blob([blob], { type: mimeType }))
    const link = document.createElement('a')
    link.href = downloadUrl
    const safeTitle = (currentPresentation.value.title || 'presentation').replace(/[^a-zA-Z0-9가-힣\s]/g, '_').trim()
    link.setAttribute('download', `${safeTitle}.${ext}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)

    if (isPptxFallback) {
      showExportToast('서버에 LibreOffice가 없어 PPTX로 대신 다운로드되었습니다. PPTX를 열어 PDF로 저장하세요.', 'info', 7000)
    } else {
      showExportToast('PDF 다운로드가 완료되었습니다.')
    }
  } catch (error: any) {
    console.error('PDF 내보내기 실패:', error)
    // api.ts 인터셉터가 blob 에러를 JSON으로 변환 (responseType: blob 시)
    const status = error?.response?.status
    const data = error?.response?.data
    let message = 'PDF 내보내기에 실패했습니다.'
    let suggestion = ''

    if (status === 503) {
      message = '서버가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.'
    } else if (status === 401) {
      message = '인증이 만료되었습니다. 다시 로그인해 주세요.'
    } else if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      message = 'PDF 변환 시간이 초과되었습니다. PPTX로 먼저 다운로드한 뒤 수동으로 PDF 변환해 주세요.'
      showExportToast(message, 'error', 7000)
      return
    } else if (!error?.response) {
      message = '서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.'
    } else if (data && typeof data === 'object') {
      message = data.message || message
      suggestion = data.suggestion || ''
    }

    showExportToast(suggestion ? `${message} ${suggestion}` : message, 'error', 6000)
  } finally {
    exportingPdf.value = false
  }
}

// AI 서비스 변경 감지
watch(() => generationRequest.value.serviceId, (newServiceId) => {
  if (newServiceId) {
    loadModels(newServiceId)
  }
})

watch(() => generationRequest.value.imageServiceId, (id) => {
  if (id) loadImageModels(id)
}, { immediate: true })

const loadImageModels = async (serviceId: number) => {
  if (!serviceId) { imageModels.value = []; return }
  try {
    const response = await api.get<string[]>(`/apiservices/${serviceId}/models`)
    imageModels.value = response.data || []
  } catch {
    imageModels.value = []
  }
}

onMounted(() => {
  loadAiServices()
  loadTemplates()
  loadThemes()
  loadImageServices()
  window.addEventListener('keydown', handleSlideshowKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleSlideshowKeydown)
})
</script>

<style scoped>
.pbr-drag-handle {
  cursor: grab;
  user-select: none;
  touch-action: none;
}
.pbr-drag-handle:active {
  cursor: grabbing;
}
</style>
