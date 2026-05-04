<template>
  <div class="page-content-wrap">
    <!-- Page Header (agents.html 참고) -->
    <div class="ag-page-header">
      <div class="ag-header-left">
        <h1 class="ag-page-title">AI Agent 선택</h1>
        <p class="ag-page-desc">실행할 Agent를 선택하거나 새로운 Agent를 생성하세요</p>
      </div>
      <div class="ag-header-right">
        <button type="button" class="btn btn-primary" @click="showCreateModal = true">
          <i class="bi bi-plus-lg"></i> 새 Agent 생성
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="ag-filter-bar">
      <div class="ag-search-wrap">
        <i class="bi bi-search ag-search-icon"></i>
        <input 
          type="text" 
          class="ag-search-input" 
          v-model="searchText" 
          placeholder="Agent 검색... (이름, 설명, 서비스)"
          @input="filterAgents"
        >
        <button 
          type="button" 
          class="ag-search-clear" 
          v-show="searchText" 
          @click="searchText = ''; filterAgents()"
        >
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
      <div class="ag-filter-selects">
        <select class="ag-select" v-model="serviceFilter" @change="filterAgents">
          <option value="">모든 서비스</option>
          <option v-for="service in services" :key="service.serviceId" :value="service.serviceCode">
            {{ service.serviceName }}
          </option>
        </select>
      </div>
      <div class="ag-filter-right">
        <div class="ag-view-btns">
          <button 
            type="button" 
            class="ag-view-btn" 
            :class="{ active: viewMode === 'grid' }" 
            @click="viewMode = 'grid'" 
            title="그리드 보기"
          >
            <i class="bi bi-grid-3x3-gap-fill"></i>
          </button>
          <button 
            type="button" 
            class="ag-view-btn" 
            :class="{ active: viewMode === 'list' }" 
            @click="viewMode = 'list'" 
            title="리스트 보기"
          >
            <i class="bi bi-list-ul"></i>
          </button>
        </div>
        <span class="ag-count-label">전체 <strong>{{ filteredAgents.length + 1 }}</strong>개 Agent</span>
      </div>
    </div>

    <!-- Agent Grid -->
    <div class="ag-grid" :class="{ 'list-view': viewMode === 'list' }" v-show="!showEmpty">
      <!-- 기본 모드 -->
      <div class="ag-card ag-card-default" @click="startDefaultMode">
        <div class="ag-card-body">
          <div class="ag-icon-wrap ag-icon-default">
            <i class="bi bi-chat-dots-fill"></i>
          </div>
          <h5 class="ag-card-title">기본 모드</h5>
          <p class="ag-card-desc">AI 서비스를 직접 선택하고 자유롭게 대화할 수 있는 기본 채팅 모드입니다.</p>
          <div class="ag-service-tags">
            <span 
              v-for="(service, idx) in services.slice(0, 4)" 
              :key="service.serviceId"
              :class="['ag-tag', ['ag-tag-blue','ag-tag-orange','ag-tag-teal','ag-tag-gray'][idx % 4]]"
            >
              {{ service.serviceName }}
            </span>
          </div>
        </div>
        <div class="ag-card-footer">
          <button type="button" class="ag-btn-start ag-btn-full" @click.stop="startDefaultMode">
            <i class="bi bi-play-fill"></i> 시작하기
          </button>
        </div>
      </div>

      <!-- 커스텀 Agent 카드들 -->
      <div 
        v-for="agent in filteredAgents" 
        :key="agent.agentId"
        class="ag-card"
        :style="{ '--ag-color': getAgentDisplayColor(agent.colorCode), '--ag-text': getAgentContrastTextColor(agent.colorCode) }"
      >
        <div class="ag-card-ribbon" v-if="isMyAgent(agent)">커스텀</div>
        <div class="ag-card-body" @click="startAgent(agent)">
          <div class="ag-icon-wrap ag-icon-dynamic">
            <i :class="agent.iconClass || 'bi bi-robot'"></i>
          </div>
          <h5 class="ag-card-title">{{ agent.agentName }}</h5>
          <p class="ag-card-short">{{ agent.description || '커스텀 AI Agent' }}</p>
          <div class="ag-model-badge">
            <i class="bi bi-cpu"></i> {{ agent.defaultModel || agent.serviceName }}
          </div>
          <div class="ag-system-preview" v-if="agent.systemPrompt">
            {{ truncateText(agent.systemPrompt, 120) }}
          </div>
          <div class="ag-system-preview" v-else style="font-style: italic; color: var(--ai-text-muted);">
            시스템 프롬프트가 설정되지 않았습니다.
          </div>
        </div>
        <div class="ag-card-footer ag-footer-flex">
          <button type="button" class="ag-btn-start ag-btn-dynamic" @click.stop="startAgent(agent)">
            <i class="bi bi-play-fill"></i> 실행하기
          </button>
          <button
            v-if="isMyAgent(agent)"
            type="button"
            class="ag-btn-edit"
            @click.stop="editAgent(agent)"
            title="Agent 수정"
          >
            <i class="bi bi-pencil"></i>
          </button>
          <a
            v-if="isMyAgent(agent) && agent.agentCode"
            :href="`/agent-test/${agent.agentCode}`"
            target="_blank"
            class="ag-btn-edit"
            title="테스트 & 공유 링크"
            @click.stop
          >
            <i class="bi bi-share"></i>
          </a>
        </div>
      </div>

      <!-- 새 Agent 추가 카드 -->
      <div class="ag-card ag-card-add" @click="showCreateModal = true">
        <div class="ag-card-body ag-add-body">
          <div class="ag-add-icon">
            <i class="bi bi-plus-lg"></i>
          </div>
          <h5 class="ag-add-title">새 Agent 생성</h5>
          <p class="ag-add-desc">커스텀 Agent를 생성하고 설정할 수 있습니다.</p>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div class="ag-empty" v-show="showEmpty">
      <div class="ag-empty-icon"><i class="bi bi-robot"></i></div>
      <h5>검색 결과가 없습니다</h5>
      <p>다른 키워드나 필터를 사용해 보세요.</p>
      <button type="button" class="btn btn-primary" @click="searchText = ''; serviceFilter = ''; filterAgents()">
        <i class="bi bi-arrow-counterclockwise"></i> 필터 초기화
      </button>
    </div>

    <!-- Agent 생성 모달 -->
    <div class="modal fade" :class="{ show: showCreateModal, 'd-block': showCreateModal }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header bg-transparent border-bottom">
            <div class="d-flex align-items-center gap-3">
              <div class="ag-modal-title-icon" style="width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,var(--ai-primary),#6366F1);color:#fff;display:flex;align-items:center;justify-content:center;">
                <i class="bi bi-plus-lg"></i>
              </div>
              <div>
                <h5 class="modal-title mb-0">새 Agent 생성</h5>
                <p class="text-muted small mb-0">커스텀 AI Agent를 만들어 팀과 공유하세요</p>
              </div>
            </div>
            <button type="button" class="btn-close" @click="closeCreateModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleCreateAgent" class="ag-modal-form">
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">Agent 이름 <span class="ag-required">*</span></label>
                  <input type="text" class="ag-form-input" v-model="newAgent.agentName" placeholder="예: 마케팅 분석 Agent" required>
                </div>
                <div class="ag-form-group">
                  <label class="ag-form-label">아이콘</label>
                  <div class="ag-icon-picker">
                    <button 
                      v-for="opt in ICON_OPTIONS" 
                      :key="opt.value"
                      type="button" 
                      class="ag-icon-opt" 
                      :class="{ active: newAgent.iconClass === opt.value }"
                      @click="newAgent.iconClass = opt.value"
                    >
                      <i :class="'bi ' + opt.icon"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div class="ag-form-group">
                <label class="ag-form-label">설명 <span class="ag-required">*</span></label>
                <textarea class="ag-form-input ag-form-textarea" rows="2" v-model="newAgent.description" placeholder="Agent의 역할과 기능을 간략히 설명하세요" required></textarea>
              </div>
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">AI 서비스 <span class="ag-required">*</span></label>
                  <select 
                    class="ag-form-input" 
                    v-model="newAgent.serviceId" 
                    @change="loadServiceModels"
                    :disabled="loadingModels"
                    required
                  >
                    <option value="">서비스 선택</option>
                    <option v-for="service in services" :key="service.serviceId" :value="service.serviceId">
                      {{ service.serviceName }}
                    </option>
                  </select>
                  <small class="text-muted" v-if="services.length === 0">서비스를 불러오는 중...</small>
                </div>
                <div class="ag-form-group">
                  <label class="ag-form-label">모델 <span class="ag-required">*</span></label>
                  <select 
                    class="ag-form-input" 
                    v-model="newAgent.defaultModel" 
                    :disabled="!newAgent.serviceId || loadingModels"
                    required
                  >
                    <option value="">{{ newAgent.serviceId ? (loadingModels ? '로딩 중...' : '선택하세요') : '서비스를 먼저 선택하세요' }}</option>
                    <option v-for="model in availableModels" :key="model" :value="model">
                      {{ model }}
                    </option>
                  </select>
                  <small class="text-muted" v-if="newAgent.serviceId && !loadingModels && availableModels.length === 0">
                    사용 가능한 모델이 없습니다.
                  </small>
                </div>
              </div>
              <div class="ag-form-group">
                <label class="ag-form-label">
                  시스템 프롬프트 <span class="ag-required">*</span>
                  <span class="ag-form-hint">Agent의 행동과 응답 방식을 정의합니다</span>
                </label>
                <textarea class="ag-form-input ag-form-textarea" rows="5" v-model="newAgent.systemPrompt" placeholder="예) 당신은 마케팅 전문가입니다. 고객이 제공한 제품 정보를 바탕으로..." required></textarea>
                <div class="ag-char-count">{{ (newAgent.systemPrompt || '').length }} / 4000자</div>
              </div>
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">
                    Temperature
                    <span class="ag-form-hint">높을수록 창의적 (0 ~ 2)</span>
                  </label>
                  <div class="ag-slider-wrap" :style="{ '--slider-percent': ((newAgent.temperature ?? 0.7) / 2 * 100) + '%' }">
                    <input type="range" class="ag-slider" v-model.number="newAgent.temperature" min="0" max="2" step="0.1">
                    <span class="ag-slider-val">{{ newAgent.temperature ?? 0.7 }}</span>
                  </div>
                </div>
                <div class="ag-form-group">
                  <label class="ag-form-label">
                    Max Tokens
                    <span class="ag-form-hint">최대 응답 토큰 수</span>
                  </label>
                  <input type="number" class="ag-form-input" v-model.number="newAgent.maxTokens" min="256" max="32000" step="256">
                </div>
              </div>
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">Agent 색상</label>
                  <div class="ag-color-picker">
                    <button 
                      v-for="color in COLOR_OPTIONS" 
                      :key="color"
                      type="button" 
                      class="ag-color-opt" 
                      :class="{ active: (newAgent.colorCode || '#4F46E5') === color }"
                      :style="{ background: color }"
                      @click="newAgent.colorCode = color"
                    ></button>
                  </div>
                </div>
                <div class="ag-form-group ag-form-switches">
                  <label class="ag-form-label">옵션</label>
                  <div class="ag-switches">
                    <label class="ag-switch-row">
                      <div class="ag-switch">
                        <input type="checkbox" v-model="newAgent.isPublic" id="isPublic">
                        <span class="ag-switch-knob"></span>
                      </div>
                      <span>공개 Agent <small>(다른 사용자 사용 가능)</small></span>
                    </label>
                    <label class="ag-switch-row">
                      <div class="ag-switch">
                        <input type="checkbox" v-model="newAgent.enableRag" id="enableRag" @change="onRagToggle">
                        <span class="ag-switch-knob"></span>
                      </div>
                      <span>RAG 기능 <small>(Knowledge Base 연동)</small></span>
                    </label>
                  </div>
                </div>
              </div>
              
              <!-- RAG 문서 선택 (enableRag 시 표시) -->
              <div v-if="newAgent.enableRag" class="ag-form-group mt-3">
                <div class="ms-0 mt-2">
                  <div class="alert alert-info mb-3">
                    <small>
                      <i class="bi bi-info-circle"></i> 
                      RAG 기능을 사용하면 Agent가 Knowledge Base의 문서를 참조하여 더 정확한 답변을 제공할 수 있습니다.
                    </small>
                  </div>
                  
                  <!-- 문서 제약 조건 -->
                  <div class="mb-3">
                    <label class="form-label">문서 제약 조건</label>
                    <div class="row">
                      <div class="col-md-6 mb-2">
                        <label class="form-label small">최대 문서 수</label>
                        <input 
                          type="number" 
                          class="form-control form-control-sm" 
                          v-model.number="ragConstraints.maxDocuments" 
                          min="1" 
                          max="50" 
                          :value="ragConstraints.maxDocuments"
                        >
                        <small class="text-muted">선택 가능한 최대 문서 수 (1-50)</small>
                      </div>
                      <div class="col-md-6 mb-2">
                        <div class="form-check mt-4">
                          <input 
                            class="form-check-input" 
                            type="checkbox" 
                            v-model="ragConstraints.requireIndexed" 
                            id="requireIndexed"
                          >
                          <label class="form-check-label small" for="requireIndexed">
                            인덱싱된 문서만 허용
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 문서 선택 -->
                  <div class="mb-3">
                    <label class="form-label">
                      연결할 문서 선택 
                      <span class="badge bg-secondary ms-2">
                        {{ newAgent.selectedDocumentIds?.length || 0 }} / {{ ragConstraints.maxDocuments }}
                      </span>
                    </label>
                    <div v-if="loadingDocuments" class="text-center py-3">
                      <div class="spinner-border spinner-border-sm" role="status"></div>
                      <small class="d-block mt-2 text-muted">문서 목록을 불러오는 중...</small>
                    </div>
                    <div v-else-if="availableDocuments.length === 0" class="alert alert-warning">
                      <small>
                        <i class="bi bi-exclamation-triangle"></i> 
                        사용 가능한 문서가 없습니다. Knowledge Base에서 문서를 먼저 생성하고 인덱싱하세요.
                      </small>
                    </div>
                    <div v-else class="border rounded p-2 max-height-300 scrollable">
                      <div 
                        v-for="doc in availableDocuments" 
                        :key="doc.documentId"
                        class="form-check mb-2"
                      >
                        <input 
                          class="form-check-input" 
                          type="checkbox" 
                          :value="doc.documentId"
                          :id="`doc-${doc.documentId}`"
                          :checked="newAgent.selectedDocumentIds?.includes(doc.documentId)"
                          @change="toggleDocument(doc.documentId)"
                          :disabled="!newAgent.selectedDocumentIds?.includes(doc.documentId) && 
                                     (newAgent.selectedDocumentIds?.length || 0) >= ragConstraints.maxDocuments"
                        >
                        <label class="form-check-label" :for="`doc-${doc.documentId}`">
                          <strong>{{ doc.title }}</strong>
                          <small class="text-muted d-block">
                            <span class="badge bg-success" v-if="doc.isIndexed">
                              <i class="bi bi-check-circle"></i> 인덱싱됨 ({{ doc.chunkCount }} chunks)
                            </span>
                            <span class="badge bg-warning" v-else>
                              <i class="bi bi-exclamation-circle"></i> 인덱싱 필요
                            </span>
                            <span class="ms-2">{{ doc.sourceType }}</span>
                          </small>
                        </label>
                      </div>
                    </div>
                    <small class="text-muted d-block mt-2">
                      <i class="bi bi-info-circle"></i> 
                      최대 {{ ragConstraints.maxDocuments }}개의 문서를 선택할 수 있습니다.
                      <span v-if="ragConstraints.requireIndexed">인덱싱된 문서만 선택 가능합니다.</span>
                    </small>
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer d-flex justify-content-end gap-2">
            <button type="button" class="ag-btn-cancel" @click="closeCreateModal">취소</button>
            <button type="button" class="btn btn-primary" @click="handleCreateAgent">
              <i class="bi bi-check-lg"></i> Agent 생성
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showCreateModal }" v-if="showCreateModal"></div>

    <!-- Agent 수정 모달 -->
    <div class="modal fade" :class="{ show: showEditModal, 'd-block': showEditModal }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header bg-transparent border-bottom">
            <div class="d-flex align-items-center gap-3">
              <div style="width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,#F59E0B,#D97706);color:#fff;display:flex;align-items:center;justify-content:center;">
                <i class="bi bi-pencil"></i>
              </div>
              <div>
                <h5 class="modal-title mb-0">Agent 수정</h5>
                <p class="text-muted small mb-0">Agent 설정을 변경합니다</p>
              </div>
            </div>
            <button type="button" class="btn-close" @click="closeEditModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateAgent" class="ag-modal-form">
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">Agent 이름 <span class="ag-required">*</span></label>
                  <input type="text" class="ag-form-input" v-model="editAgentData.agentName" placeholder="예: 마케팅 분석 Agent" required>
                </div>
                <div class="ag-form-group">
                  <label class="ag-form-label">아이콘</label>
                  <div class="ag-icon-picker">
                    <button 
                      v-for="opt in ICON_OPTIONS" 
                      :key="opt.value"
                      type="button" 
                      class="ag-icon-opt" 
                      :class="{ active: editAgentData.iconClass === opt.value }"
                      @click="editAgentData.iconClass = opt.value"
                    >
                      <i :class="'bi ' + opt.icon"></i>
                    </button>
                  </div>
                </div>
              </div>
              <div class="ag-form-group">
                <label class="ag-form-label">설명 <span class="ag-required">*</span></label>
                <textarea class="ag-form-input ag-form-textarea" rows="2" v-model="editAgentData.description" placeholder="Agent의 역할과 기능을 간략히 설명하세요" required></textarea>
              </div>
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">AI 서비스 <span class="ag-required">*</span></label>
                  <select 
                    class="ag-form-input" 
                    v-model="editAgentData.serviceId" 
                    @change="loadEditServiceModels"
                    :disabled="loadingModels"
                    required
                  >
                    <option value="">서비스 선택</option>
                    <option v-for="service in services" :key="service.serviceId" :value="service.serviceId">
                      {{ service.serviceName }}
                    </option>
                  </select>
                  <small class="text-muted" v-if="services.length === 0">서비스를 불러오는 중...</small>
                </div>
                <div class="ag-form-group">
                  <label class="ag-form-label">모델 <span class="ag-required">*</span></label>
                  <select 
                    class="ag-form-input" 
                    v-model="editAgentData.defaultModel" 
                    :disabled="!editAgentData.serviceId || loadingModels"
                    required
                  >
                    <option value="">{{ editAgentData.serviceId ? (loadingModels ? '로딩 중...' : '선택하세요') : '서비스를 먼저 선택하세요' }}</option>
                    <option v-for="model in editAvailableModels" :key="model" :value="model">
                      {{ model }}
                    </option>
                  </select>
                  <small class="text-muted" v-if="editAgentData.serviceId && !loadingModels && editAvailableModels.length === 0">
                    사용 가능한 모델이 없습니다.
                  </small>
                </div>
              </div>
              <div class="ag-form-group">
                <label class="ag-form-label">
                  시스템 프롬프트 <span class="ag-required">*</span>
                  <span class="ag-form-hint">Agent의 행동과 응답 방식을 정의합니다</span>
                </label>
                <textarea class="ag-form-input ag-form-textarea" rows="5" v-model="editAgentData.systemPrompt" placeholder="예) 당신은 마케팅 전문가입니다. 고객이 제공한 제품 정보를 바탕으로..." required></textarea>
                <div class="ag-char-count">{{ (editAgentData.systemPrompt || '').length }} / 4000자</div>
              </div>
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">
                    Temperature
                    <span class="ag-form-hint">높을수록 창의적 (0 ~ 2)</span>
                  </label>
                  <div class="ag-slider-wrap" :style="{ '--slider-percent': ((editAgentData.temperature ?? 0.7) / 2 * 100) + '%' }">
                    <input type="range" class="ag-slider" v-model.number="editAgentData.temperature" min="0" max="2" step="0.1">
                    <span class="ag-slider-val">{{ editAgentData.temperature ?? 0.7 }}</span>
                  </div>
                </div>
                <div class="ag-form-group">
                  <label class="ag-form-label">
                    Max Tokens
                    <span class="ag-form-hint">최대 응답 토큰 수</span>
                  </label>
                  <input type="number" class="ag-form-input" v-model.number="editAgentData.maxTokens" min="256" max="32000" step="256">
                </div>
              </div>
              <div class="ag-form-row">
                <div class="ag-form-group">
                  <label class="ag-form-label">Agent 색상</label>
                  <div class="ag-color-picker">
                    <button 
                      v-for="color in COLOR_OPTIONS" 
                      :key="color"
                      type="button" 
                      class="ag-color-opt" 
                      :class="{ active: (editAgentData.colorCode || '#4F46E5') === color }"
                      :style="{ background: color }"
                      @click="editAgentData.colorCode = color"
                    ></button>
                  </div>
                </div>
                <div class="ag-form-group ag-form-switches">
                  <label class="ag-form-label">옵션</label>
                  <div class="ag-switches">
                    <label class="ag-switch-row">
                      <div class="ag-switch">
                        <input type="checkbox" v-model="editAgentData.isPublic" id="editIsPublic">
                        <span class="ag-switch-knob"></span>
                      </div>
                      <span>공개 Agent <small>(다른 사용자 사용 가능)</small></span>
                    </label>
                    <label class="ag-switch-row">
                      <div class="ag-switch">
                        <input type="checkbox" v-model="editAgentData.enableRag" id="editEnableRag">
                        <span class="ag-switch-knob"></span>
                      </div>
                      <span>RAG 기능 <small>(Knowledge Base 연동)</small></span>
                    </label>
                  </div>
                </div>
              </div>

              <!-- 공유 & 임베드 설정 -->
              <hr class="my-3">
              <div class="mb-2">
                <h6 class="mb-3"><i class="bi bi-share"></i> 공유 & 임베드 설정</h6>
                <div class="form-check form-switch mb-2">
                  <input class="form-check-input" type="checkbox" id="editAllowGuestChat" v-model="editAgentData.allowGuestChat" />
                  <label class="form-check-label fw-bold" for="editAllowGuestChat">게스트 채팅 허용 (비로그인 사용자 접근)</label>
                </div>
                <div v-if="editAgentData.allowGuestChat">
                  <div class="ag-form-row mt-2">
                    <div class="ag-form-group">
                      <label class="ag-form-label">환영 메시지</label>
                      <textarea class="ag-form-input" v-model="editAgentData.welcomeMessage" rows="2"
                        placeholder="예) 안녕하세요! 무엇을 도와드릴까요?"></textarea>
                    </div>
                    <div class="ag-form-group">
                      <label class="ag-form-label">입력창 안내 문구</label>
                      <input type="text" class="ag-form-input" v-model="editAgentData.placeholderText"
                        placeholder="예) 궁금한 점을 입력하세요..." />
                    </div>
                  </div>
                  <div class="ag-form-group">
                    <label class="ag-form-label">테마</label>
                    <select class="ag-form-input" v-model="editAgentData.chatTheme">
                      <option value="light">라이트</option>
                      <option value="dark">다크</option>
                      <option value="auto">시스템 자동</option>
                    </select>
                  </div>
                </div>

                <!-- 공유 링크 (agentCode가 있을 때) -->
                <template v-if="editingAgentCode">
                  <div class="mt-3 p-3 border rounded" style="background:#f8fafc;">
                    <div class="mb-2 d-flex align-items-center gap-2">
                      <small class="text-muted fw-bold"><i class="bi bi-link-45deg"></i> 테스트 페이지</small>
                      <a :href="`/agent-test/${editingAgentCode}`" target="_blank" class="btn btn-sm btn-outline-secondary py-0">
                        <i class="bi bi-box-arrow-up-right"></i>
                      </a>
                    </div>
                    <div v-if="editAgentData.allowGuestChat">
                      <div class="mb-2">
                        <small class="text-muted fw-bold">🤖 챗봇 공유 URL</small>
                        <div class="input-group input-group-sm mt-1">
                          <input type="text" class="form-control form-control-sm" readonly
                            :value="`${origin}/chatbot/${editingAgentCode}`" />
                          <button class="btn btn-outline-secondary"
                            @click="copyEditShareUrl(`${origin}/chatbot/${editingAgentCode}`)">
                            {{ editShareCopySuccess ? '복사됨!' : '복사' }}
                          </button>
                        </div>
                      </div>
                      <div>
                        <small class="text-muted fw-bold">📌 임베드 URL</small>
                        <div class="input-group input-group-sm mt-1">
                          <input type="text" class="form-control form-control-sm" readonly
                            :value="`${origin}/embed/${editingAgentCode}`" />
                          <button class="btn btn-outline-secondary"
                            @click="copyEditShareUrl(`${origin}/embed/${editingAgentCode}`)">
                            복사
                          </button>
                        </div>
                      </div>
                    </div>
                    <div v-else class="alert alert-warning py-2 small mb-0">
                      <i class="bi bi-lock"></i> 게스트 채팅을 허용해야 챗봇 URL과 임베드 기능을 사용할 수 있습니다.
                    </div>
                  </div>
                </template>
              </div>
            </form>
          </div>
          <div class="modal-footer d-flex align-items-center justify-content-between">
            <button
              type="button"
              class="ag-btn-delete"
              @click="handleDeleteAgent"
              v-if="editingAgent"
            >
              <i class="bi bi-trash"></i> 삭제
            </button>
            <div class="d-flex gap-2 ms-auto">
              <button
                v-if="editingAgent"
                type="button"
                class="btn btn-outline-secondary btn-sm"
                @click="router.push(`/agents/builder/${editingAgent.agentId}`); closeEditModal()"
                title="5단계 빌더에서 전체 설정 수정"
              >
                <i class="bi bi-tools"></i> 빌더에서 수정
              </button>
              <button type="button" class="ag-btn-cancel" @click="closeEditModal">취소</button>
              <button type="button" class="btn btn-primary ag-btn-edit-save" @click="handleUpdateAgent">
                <i class="bi bi-check-lg"></i> 저장하기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showEditModal }" v-if="showEditModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { getAgentDisplayColor, getAgentContrastTextColor } from '@/utils/agentUtils'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { AgentDto, ApiServiceDto } from '@/types'

interface KnowledgeBaseDocument {
  documentId: number
  userId: number
  userName: string
  title: string
  sourceType: string
  sourceId?: string
  isIndexed: boolean
  indexedAt?: string
  chunkCount: number
  createdAt: string
  updatedAt: string
}

interface RagConstraints {
  maxDocuments: number
  requireIndexed: boolean
}

const ICON_OPTIONS = [
  { value: 'bi bi-robot', icon: 'bi-robot' },
  { value: 'bi bi-brain', icon: 'bi-brain' },
  { value: 'bi bi-lightbulb', icon: 'bi-lightbulb' },
  { value: 'bi bi-rocket', icon: 'bi-rocket' },
  { value: 'bi bi-star', icon: 'bi-star' },
  { value: 'bi bi-magic', icon: 'bi-magic' },
  { value: 'bi bi-cpu', icon: 'bi-cpu' },
  { value: 'bi bi-code-slash', icon: 'bi-code-slash' }
] as const

const COLOR_OPTIONS = ['#4F46E5', '#0EA5E9', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#6C757D'] as const

interface CreateAgentData {
  agentName: string
  description: string
  serviceId: number
  defaultModel: string
  systemPrompt: string
  temperature?: number
  maxTokens?: number
  iconClass?: string
  colorCode?: string
  isPublic: boolean
  enableRag?: boolean
  selectedDocumentIds?: number[]
  allowGuestChat?: boolean
  welcomeMessage?: string
  placeholderText?: string
  chatTheme?: string
}

const router = useRouter()
const authStore = useAuthStore()
const agents = ref<AgentDto[]>([])
const services = ref<ApiServiceDto[]>([])
const loading = ref(false)
const loadingModels = ref(false)
const loadingDocuments = ref(false)
const searchText = ref('')
const serviceFilter = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingAgent = ref<AgentDto | null>(null)
const availableModels = ref<string[]>([])
const editAvailableModels = ref<string[]>([])
const availableDocuments = ref<KnowledgeBaseDocument[]>([])

const ragConstraints = ref<RagConstraints>({
  maxDocuments: 10,
  requireIndexed: true
})

const newAgent = ref<CreateAgentData>({
  agentName: '',
  description: '',
  serviceId: 0,
  defaultModel: '',
  systemPrompt: '',
  temperature: 0.7,
  maxTokens: 2048,
  iconClass: 'bi bi-robot',
  colorCode: '#4F46E5',
  isPublic: false,
  enableRag: false,
  selectedDocumentIds: []
})

const editAgentData = ref<CreateAgentData>({
  agentName: '',
  description: '',
  serviceId: 0,
  defaultModel: '',
  systemPrompt: '',
  temperature: 0.7,
  maxTokens: 2048,
  iconClass: 'bi bi-robot',
  colorCode: '#4F46E5',
  isPublic: false,
  enableRag: false,
  selectedDocumentIds: [],
  allowGuestChat: false,
  welcomeMessage: '',
  placeholderText: '',
  chatTheme: 'light'
})
const editingAgentCode = ref<string | null>(null)
const editShareCopySuccess = ref(false)
const origin = window.location.origin

const filteredAgents = computed(() => {
  let result = agents.value

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(agent => 
      agent.agentName.toLowerCase().includes(search) ||
      (agent.description || '').toLowerCase().includes(search) ||
      agent.serviceName.toLowerCase().includes(search)
    )
  }

  if (serviceFilter.value) {
    result = result.filter(agent => 
      agent.serviceName.toLowerCase() === serviceFilter.value.toLowerCase()
    )
  }

  return result
})

const showEmpty = computed(() => filteredAgents.value.length === 0 && (searchText.value || serviceFilter.value))

const loadAgents = async () => {
  try {
    loading.value = true
    // isPublic 파라미터 없이 모든 Agent 가져오기
    const [agentsRes, servicesRes] = await Promise.all([
      api.get<AgentDto[]>('/agents'),
      api.get<ApiServiceDto[]>('/apiservices')
    ])
    agents.value = agentsRes.data || []
    services.value = servicesRes.data || []
    console.log('Loaded agents:', agents.value.length, agents.value)
    console.log('Loaded services:', services.value.length)
  } catch (error: any) {
    console.error('Error loading agents:', error)
    console.error('Error response:', error.response?.data)
    console.error('Error status:', error.response?.status)
    // 사용자에게 알림 (개발 중이므로)
    if (error.response?.status === 500) {
      console.error('Server error. Check backend logs for details.')
    }
  } finally {
    loading.value = false
  }
}

const loadServiceModels = async () => {
  if (!newAgent.value.serviceId) {
    availableModels.value = []
    newAgent.value.defaultModel = ''
    return
  }

  try {
    loadingModels.value = true
    newAgent.value.defaultModel = ''
    const response = await api.get<string[]>(`/apiservices/${newAgent.value.serviceId}/models`)
    availableModels.value = response.data || []
    
    // 기본 모델이 있으면 자동 선택
    const selectedService = services.value.find(s => s.serviceId === newAgent.value.serviceId)
    if (selectedService?.defaultModel && availableModels.value.includes(selectedService.defaultModel)) {
      newAgent.value.defaultModel = selectedService.defaultModel
    }
  } catch (error) {
    console.error('Error loading models:', error)
    availableModels.value = []
  } finally {
    loadingModels.value = false
  }
}

const loadDocuments = async () => {
  try {
    loadingDocuments.value = true
    const response = await api.get<KnowledgeBaseDocument[]>('/knowledgebase', {
      params: { 
        isIndexed: ragConstraints.value.requireIndexed ? true : undefined 
      }
    })
    
    let docs = response.data || []
    
    // 인덱싱 필수인 경우 필터링 (백엔드에서 이미 필터링되지만 이중 체크)
    if (ragConstraints.value.requireIndexed) {
      docs = docs.filter(doc => doc.isIndexed)
    }
    
    availableDocuments.value = docs
  } catch (error) {
    console.error('Error loading documents:', error)
    availableDocuments.value = []
  } finally {
    loadingDocuments.value = false
  }
}

const onRagToggle = () => {
  if (newAgent.value.enableRag) {
    loadDocuments()
  } else {
    newAgent.value.selectedDocumentIds = []
  }
}

const toggleDocument = (documentId: number) => {
  if (!newAgent.value.selectedDocumentIds) {
    newAgent.value.selectedDocumentIds = []
  }
  
  const index = newAgent.value.selectedDocumentIds.indexOf(documentId)
  if (index > -1) {
    newAgent.value.selectedDocumentIds.splice(index, 1)
  } else {
    if (newAgent.value.selectedDocumentIds.length < ragConstraints.value.maxDocuments) {
      newAgent.value.selectedDocumentIds.push(documentId)
    }
  }
}

// 모달이 열릴 때 문서 목록 로드
watch(showCreateModal, (isOpen) => {
  if (isOpen && newAgent.value.enableRag) {
    loadDocuments()
  }
})

const filterAgents = () => {
  // computed property가 자동으로 업데이트됨
}

const startDefaultMode = () => {
  router.push('/agents/chat')
}

const startAgent = (agent: AgentDto) => {
  router.push(`/agents/chat/${agent.agentId}`)
}

// 본인이 만든 Agent인지 확인
const isMyAgent = (agent: AgentDto): boolean => {
  return authStore.user?.userId === agent.createdBy
}

// Agent 수정 모달 열기
const editAgent = async (agent: AgentDto) => {
  editingAgent.value = agent
  editingAgentCode.value = agent.agentCode || null
  editAgentData.value = {
    agentName: agent.agentName,
    description: agent.description || '',
    serviceId: agent.serviceId,
    defaultModel: agent.defaultModel || '',
    systemPrompt: agent.systemPrompt || '',
    temperature: agent.temperature ?? 0.7,
    maxTokens: agent.maxTokens || 2048,
    iconClass: agent.iconClass || 'bi bi-robot',
    colorCode: agent.colorCode || '#4F46E5',
    isPublic: agent.isPublic,
    enableRag: agent.enableRag || false,
    selectedDocumentIds: [],
    allowGuestChat: agent.allowGuestChat || false,
    welcomeMessage: agent.welcomeMessage || '',
    placeholderText: agent.placeholderText || '',
    chatTheme: agent.chatTheme || 'light'
  }
  
  // 서비스 모델 로드
  if (agent.serviceId) {
    await loadEditServiceModels()
  }
  
  showEditModal.value = true
}

// 수정용 서비스 모델 로드
const loadEditServiceModels = async () => {
  if (!editAgentData.value.serviceId) {
    editAvailableModels.value = []
    editAgentData.value.defaultModel = ''
    return
  }

  try {
    loadingModels.value = true
    const response = await api.get<string[]>(`/apiservices/${editAgentData.value.serviceId}/models`)
    editAvailableModels.value = response.data || []
    
    // 현재 모델이 새 서비스에도 유효하면 유지, 아니면 첫 번째 모델 선택
    if (!editAvailableModels.value.includes(editAgentData.value.defaultModel)) {
      const selectedService = services.value.find(s => s.serviceId === editAgentData.value.serviceId)
      if (selectedService?.defaultModel && editAvailableModels.value.includes(selectedService.defaultModel)) {
        editAgentData.value.defaultModel = selectedService.defaultModel
      } else if (editAvailableModels.value.length > 0) {
        editAgentData.value.defaultModel = editAvailableModels.value[0]
      }
    }
  } catch (error) {
    console.error('Error loading edit models:', error)
    editAvailableModels.value = []
  } finally {
    loadingModels.value = false
  }
}

// Agent 수정
const handleUpdateAgent = async () => {
  if (!editingAgent.value) return
  
  // 유효성 검사
  if (!editAgentData.value.agentName || !editAgentData.value.description || !editAgentData.value.serviceId || !editAgentData.value.defaultModel) {
    alert('필수 항목을 모두 입력해주세요.')
    return
  }

  try {
    const requestData: any = {
      agentName: editAgentData.value.agentName,
      description: editAgentData.value.description,
      serviceId: editAgentData.value.serviceId,
      defaultModel: editAgentData.value.defaultModel,
      systemPrompt: editAgentData.value.systemPrompt,
      temperature: editAgentData.value.temperature,
      maxTokens: editAgentData.value.maxTokens,
      iconClass: editAgentData.value.iconClass,
      colorCode: editAgentData.value.colorCode,
      isPublic: editAgentData.value.isPublic,
      enableRag: editAgentData.value.enableRag,
      allowGuestChat: editAgentData.value.allowGuestChat,
      welcomeMessage: editAgentData.value.welcomeMessage,
      placeholderText: editAgentData.value.placeholderText,
      chatTheme: editAgentData.value.chatTheme
    }

    await api.put(`/agents/${editingAgent.value.agentId}`, requestData)
    
    // 성공 메시지
    alert('Agent가 성공적으로 수정되었습니다.')
    
    // 모달 닫기 및 데이터 초기화
    closeEditModal()
    
    await loadAgents()
  } catch (error: any) {
    console.error('Error updating agent:', error)
    const errorMessage = error.response?.data?.message || error.response?.data?.error || 'Agent 수정 중 오류가 발생했습니다.'
    alert(errorMessage)
  }
}

// Agent 삭제
const handleDeleteAgent = async () => {
  if (!editingAgent.value) return
  
  if (!confirm(`정말로 "${editingAgent.value.agentName}" Agent를 삭제하시겠습니까?`)) {
    return
  }

  try {
    await api.delete(`/agents/${editingAgent.value.agentId}`)
    
    // 성공 메시지
    alert('Agent가 성공적으로 삭제되었습니다.')
    
    // 모달 닫기 및 데이터 초기화
    closeEditModal()
    
    await loadAgents()
  } catch (error: any) {
    console.error('Error deleting agent:', error)
    const errorMessage = error.response?.data?.message || error.response?.data?.error || 'Agent 삭제 중 오류가 발생했습니다.'
    alert(errorMessage)
  }
}

// 생성 모달 닫기
const closeCreateModal = () => {
  showCreateModal.value = false
  newAgent.value = {
    agentName: '',
    description: '',
    serviceId: 0,
    defaultModel: '',
    systemPrompt: '',
    temperature: 0.7,
    maxTokens: 2048,
    iconClass: 'bi bi-robot',
    colorCode: '#4F46E5',
    isPublic: false,
    enableRag: false,
    selectedDocumentIds: []
  }
  availableModels.value = []
  availableDocuments.value = []
}

// 수정 모달 닫기
const closeEditModal = () => {
  showEditModal.value = false
  editingAgent.value = null
  editingAgentCode.value = null
  editShareCopySuccess.value = false
  editAgentData.value = {
    agentName: '',
    description: '',
    serviceId: 0,
    defaultModel: '',
    systemPrompt: '',
    temperature: 0.7,
    maxTokens: 2048,
    iconClass: 'bi bi-robot',
    colorCode: '#4F46E5',
    isPublic: false,
    enableRag: false,
    selectedDocumentIds: [],
    allowGuestChat: false,
    welcomeMessage: '',
    placeholderText: '',
    chatTheme: 'light'
  }
  editAvailableModels.value = []
}

const copyEditShareUrl = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    editShareCopySuccess.value = true
    setTimeout(() => { editShareCopySuccess.value = false }, 2000)
  } catch {
    prompt('URL을 복사하세요:', text)
  }
}

const handleCreateAgent = async () => {
  // 유효성 검사
  if (!newAgent.value.agentName || !newAgent.value.description || !newAgent.value.serviceId || !newAgent.value.defaultModel) {
    alert('필수 항목을 모두 입력해주세요.')
    return
  }

  if (newAgent.value.enableRag && (!newAgent.value.selectedDocumentIds || newAgent.value.selectedDocumentIds.length === 0)) {
    const confirm = window.confirm('RAG 기능을 사용하지만 문서를 선택하지 않았습니다. 계속하시겠습니까?')
    if (!confirm) return
  }

  // RAG 제약 조건 검사
  if (newAgent.value.enableRag && newAgent.value.selectedDocumentIds) {
    if (newAgent.value.selectedDocumentIds.length > ragConstraints.value.maxDocuments) {
      alert(`최대 ${ragConstraints.value.maxDocuments}개의 문서만 선택할 수 있습니다.`)
      return
    }

    if (ragConstraints.value.requireIndexed) {
      const unindexedDocs = availableDocuments.value.filter(
        doc => newAgent.value.selectedDocumentIds?.includes(doc.documentId) && !doc.isIndexed
      )
      if (unindexedDocs.length > 0) {
        alert('인덱싱되지 않은 문서가 포함되어 있습니다. 인덱싱된 문서만 선택할 수 있습니다.')
        return
      }
    }
  }

  try {
    // API 요청 데이터 준비
    const requestData: any = {
      agentName: newAgent.value.agentName,
      description: newAgent.value.description,
      serviceId: newAgent.value.serviceId,
      defaultModel: newAgent.value.defaultModel,
      systemPrompt: newAgent.value.systemPrompt,
      temperature: newAgent.value.temperature,
      maxTokens: newAgent.value.maxTokens,
      iconClass: newAgent.value.iconClass,
      colorCode: newAgent.value.colorCode,
      isPublic: newAgent.value.isPublic,
      enableRag: newAgent.value.enableRag
    }

    // RAG 문서 ID 추가
    if (newAgent.value.enableRag && newAgent.value.selectedDocumentIds && newAgent.value.selectedDocumentIds.length > 0) {
      requestData.selectedDocumentIds = newAgent.value.selectedDocumentIds
    }

    await api.post('/agents', requestData)
    
    // 성공 메시지
    alert('Agent가 성공적으로 생성되었습니다.')
    
    // 모달 닫기 및 폼 초기화
    closeCreateModal()
    
    await loadAgents()
  } catch (error: any) {
    console.error('Error creating agent:', error)
    const errorMessage = error.response?.data?.message || error.response?.data?.error || 'Agent 생성 중 오류가 발생했습니다.'
    alert(errorMessage)
  }
}

// 텍스트 자르기 헬퍼 함수
const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

onMounted(() => {
  loadAgents()
})
</script>

<style scoped>
.ag-header-left { flex: 1; }
.ag-header-right { flex-shrink: 0; }
.modal.show { display: block; }
.modal-backdrop.show { opacity: 0.5; }
</style>
