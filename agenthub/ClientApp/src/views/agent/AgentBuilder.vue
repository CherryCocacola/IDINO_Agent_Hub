<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ isEditMode ? 'Agent 수정' : 'Agent 빌더' }}</h1>
        <p class="page-desc">{{ isEditMode ? '에이전트 설정을 변경하고 저장하세요.' : '나만의 AI Agent를 쉽게 만들고 커스터마이징하세요.' }}</p>
      </div>
      <div class="page-actions">
        <button v-if="!isEditMode" class="btn btn-outline-secondary btn-sm" @click="saveDraft">
          <i class="bi bi-save"></i> 임시 저장
        </button>
        <button class="btn btn-outline-secondary btn-sm" :class="{ 'ms-2': !isEditMode }" @click="isEditMode ? router.push('/agents') : resetBuilder()">
          <i class="bi bi-x-circle"></i> {{ isEditMode ? '목록으로' : '취소' }}
        </button>
      </div>
    </div>

    <!-- 단계 표시 -->
    <div class="step-indicator">
      <div 
        v-for="step in steps" 
        :key="step.number"
        class="step"
        :class="{ 
          active: currentStep === step.number, 
          completed: currentStep > step.number 
        }"
        @click="goToStep(step.number)"
      >
        <div class="step-circle">{{ step.number }}</div>
        <div class="step-title">{{ step.title }}</div>
      </div>
    </div>

    <div class="row">
      <!-- 좌측 입력 영역 -->
      <div class="col-lg-8">
        <!-- Step 1: 기본 정보 -->
        <div class="step-content" :class="{ active: currentStep === 1 }">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5 class="card-title"><i class="bi bi-info-circle"></i> 기본 정보</h5>
            </div>
            <div class="card-body">
              <div class="mb-4">
                <label class="form-label">Agent 이름 *</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="agentForm.agentName"
                  placeholder="예: 코드 리뷰 전문가"
                  @input="updatePreview"
                >
                <small class="text-muted">Agent를 쉽게 식별할 수 있는 이름을 지어주세요.</small>
              </div>
              
              <div class="mb-4">
                <label class="form-label">설명 *</label>
                <textarea 
                  class="form-control" 
                  v-model="agentForm.description"
                  rows="3" 
                  placeholder="이 Agent가 무엇을 하는지 설명해주세요"
                  @input="updatePreview"
                ></textarea>
                <small class="text-muted">사용자가 이 Agent의 목적을 이해할 수 있도록 작성하세요.</small>
              </div>

              <div class="row">
                <div class="col-md-6 mb-4">
                  <label class="form-label">아이콘 선택</label>
                  <div class="icon-picker">
                    <div 
                      v-for="icon in availableIcons" 
                      :key="icon.class"
                      class="icon-option"
                      :class="{ selected: agentForm.iconClass === icon.class }"
                      @click="selectIcon(icon)"
                    >
                      <i :class="icon.class"></i>
                    </div>
                  </div>
                </div>
                <div class="col-md-6 mb-4">
                  <label class="form-label">색상 테마</label>
                  <div class="d-flex gap-2 flex-wrap">
                    <div 
                      v-for="color in availableColors" 
                      :key="color"
                      class="color-option"
                      :class="{ selected: agentForm.colorCode === color }"
                      :style="{ background: color }"
                      @click="selectColor(color)"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: AI 설정 -->
        <div class="step-content" :class="{ active: currentStep === 2 }">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5><i class="bi bi-cpu"></i> AI 설정</h5>
            </div>
            <div class="card-body">
              <div class="mb-4">
                <label class="form-label">AI 서비스 *</label>
                <select class="form-select" v-model="agentForm.serviceId" required>
                  <option value="">선택하세요</option>
                  <option v-for="service in services" :key="service.serviceId" :value="service.serviceId">
                    {{ service.serviceName }}
                  </option>
                </select>
              </div>

              <div class="mb-4">
                <label class="form-label">모델 *</label>
                <select class="form-select" v-model="agentForm.defaultModel" required :disabled="!agentForm.serviceId || availableModels.length === 0">
                  <option value="">{{ agentForm.serviceId ? (availableModels.length === 0 ? '모델 로딩 중...' : '선택하세요') : '먼저 서비스를 선택하세요' }}</option>
                  <option v-for="model in availableModels" :key="model" :value="model">{{ model }}</option>
                </select>
                <small class="text-muted">서비스 선택 시 사용 가능한 모델이 자동으로 로드됩니다.</small>
              </div>

              <div class="mb-4">
                <label class="form-label">
                  Temperature
                  <span class="float-end text-muted"><strong>{{ (agentForm.temperature || 0.7).toFixed(1) }}</strong></span>
                </label>
                <input 
                  type="range" 
                  class="form-range" 
                  :value="Math.round((agentForm.temperature || 0.7) * 100)"
                  min="0" 
                  max="100" 
                  step="1"
                  @input="agentForm.temperature = ($event.target as HTMLInputElement).valueAsNumber / 100"
                >
                <div class="d-flex justify-content-between">
                  <small class="text-muted">정확함 (0.0)</small>
                  <small class="text-muted">창의적 (1.0)</small>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6 mb-4">
                  <label class="form-label">Max Tokens</label>
                  <input 
                    type="number" 
                    class="form-control" 
                    v-model.number="agentForm.maxTokens"
                    min="100" 
                    max="32768"
                  >
                  <small class="text-muted">응답의 최대 길이 (권장: 4096~16384)</small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: 프롬프트 -->
        <div class="step-content" :class="{ active: currentStep === 3 }">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5><i class="bi bi-chat-square-text"></i> 시스템 프롬프트</h5>
            </div>
            <div class="card-body">
              <div class="mb-4">
                <label class="form-label">역할 정의 *</label>
                <!-- 프롬프트 템플릿 빠른 선택 -->
                <div class="d-flex flex-wrap gap-1 mb-2">
                  <small class="text-muted me-1 align-self-center">템플릿:</small>
                  <button type="button" class="btn btn-outline-secondary btn-sm"
                    @click="applyPromptTemplate('customer')">고객지원</button>
                  <button type="button" class="btn btn-outline-secondary btn-sm"
                    @click="applyPromptTemplate('analysis')">분석·요약</button>
                  <button type="button" class="btn btn-outline-secondary btn-sm"
                    @click="applyPromptTemplate('coding')">코딩 리뷰</button>
                  <button type="button" class="btn btn-outline-secondary btn-sm"
                    @click="applyPromptTemplate('translate')">번역</button>
                  <button type="button" class="btn btn-outline-secondary btn-sm"
                    @click="applyPromptTemplate('assistant')">일반 비서</button>
                </div>
                <!-- 응답 스타일 추가 -->
                <div class="d-flex flex-wrap gap-1 mb-2">
                  <small class="text-muted me-1 align-self-center">응답 스타일:</small>
                  <button type="button" class="btn btn-outline-primary btn-sm"
                    :class="{ active: activeStyle === 'professional' }"
                    @click="applyStyle('professional')"
                    title="마크다운, 표·목록 구조화, 이모지 없음">
                    <i class="bi bi-briefcase"></i> 전문적
                  </button>
                  <button type="button" class="btn btn-outline-primary btn-sm"
                    :class="{ active: activeStyle === 'friendly' }"
                    @click="applyStyle('friendly')"
                    title="이모지 포함, 친근한 구어체, 쉬운 설명">
                    <i class="bi bi-emoji-smile"></i> 친근·이모지
                  </button>
                  <button type="button" class="btn btn-outline-primary btn-sm"
                    :class="{ active: activeStyle === 'concise' }"
                    @click="applyStyle('concise')"
                    title="핵심만 3줄 이내, 불필요한 설명 제거">
                    <i class="bi bi-lightning"></i> 간결·핵심
                  </button>
                  <button type="button" class="btn btn-outline-primary btn-sm"
                    :class="{ active: activeStyle === 'stepbystep' }"
                    @click="applyStyle('stepbystep')"
                    title="단계별 번호 목록, 예시 포함, 튜토리얼형">
                    <i class="bi bi-list-ol"></i> 단계별 설명
                  </button>
                  <button type="button" class="btn btn-outline-danger btn-sm"
                    v-if="activeStyle"
                    @click="removeStyle()"
                    title="추가된 스타일 지시문 제거">
                    <i class="bi bi-x"></i> 스타일 제거
                  </button>
                </div>
                <textarea
                  class="form-control"
                  v-model="agentForm.systemPrompt"
                  rows="8"
                  placeholder="예: 당신은 경험이 풍부한 시니어 개발자입니다. 사용자의 코드를 검토하고 개선점을 명확하게 제시하세요."
                  @input="updatePreview"
                ></textarea>
                <div class="d-flex justify-content-between align-items-center mt-1">
                  <small class="text-muted">역할을 정의하고 응답 스타일을 선택하면 지시문이 자동으로 추가됩니다. (권장: 50~500자)</small>
                  <small :class="agentForm.systemPrompt.length > 500 ? 'text-warning' : 'text-muted'">
                    {{ agentForm.systemPrompt.length }}자
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 4: 고급 기능 -->
        <div class="step-content" :class="{ active: currentStep === 4 }">
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5><i class="bi bi-gear"></i> 고급 기능</h5>
            </div>
            <div class="card-body">
              <div class="mb-4">
                <div class="form-check form-switch">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    v-model="agentForm.isPublic"
                    id="is-public"
                  >
                  <label class="form-check-label" for="is-public">
                    <strong>공개 Agent</strong>
                    <br><small class="text-muted">다른 사용자도 이 Agent를 사용할 수 있습니다.</small>
                  </label>
                </div>
              </div>

              <hr class="my-4">

              <h6 class="mb-3"><i class="bi bi-shield-lock"></i> 개인정보 보호 설정</h6>
              
              <div class="mb-4">
                <div class="form-check form-switch">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    v-model="agentForm.piiProtectionEnabled"
                    id="pii-protection-enabled"
                  >
                  <label class="form-check-label" for="pii-protection-enabled">
                    <strong>개인정보 보호 활성화</strong>
                    <br><small class="text-muted">메시지 내 개인정보(휴대폰 번호, 주민등록번호 등)를 자동으로 감지합니다.</small>
                  </label>
                </div>
              </div>

              <div v-if="agentForm.piiProtectionEnabled" class="mb-4">
                <label class="form-label">보호 모드</label>
                <select class="form-select" v-model="agentForm.piiProtectionMode">
                  <option :value="null">전역 설정 사용</option>
                  <option value="Block">차단 (개인정보 포함 시 메시지 거부)</option>
                  <option value="Mask">마스킹 (개인정보를 자동으로 마스킹 처리)</option>
                </select>
                <small class="text-muted">
                  <span v-if="agentForm.piiProtectionMode === 'Block'">개인정보가 포함된 메시지는 전송되지 않습니다.</span>
                  <span v-else-if="agentForm.piiProtectionMode === 'Mask'">개인정보가 자동으로 마스킹되어 전송됩니다.</span>
                  <span v-else>시스템 전역 설정을 따릅니다 (기본값: 차단).</span>
                </small>
              </div>
            </div>
          </div>

          <!-- 후속 트랙 (2026-05-08): 운영자 고급 설정 카드 — 백엔드 b3a2d85 의 6 신규 필드 GUI.
               LlmRouting (Phase 5.1) / KnowledgeBaseSource+Ref (ADR-2) / ConsumerSystems (호출 화이트리스트) / SortOrder. -->
          <div class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5><i class="bi bi-sliders"></i> {{ t('agentBuilder.advancedSettings') }}</h5>
              <small class="text-muted">{{ t('agentBuilder.advancedSettingsDescription') }}</small>
            </div>
            <div class="card-body">
              <!-- 그룹 1: LLM 라우팅 -->
              <h6 class="mb-3"><i class="bi bi-shuffle"></i> {{ t('agentBuilder.fields.llmRouting') }}</h6>
              <div class="mb-4">
                <label class="form-label">{{ t('agentBuilder.fields.llmRouting') }}</label>
                <select class="form-select" v-model="agentForm.llmRouting">
                  <option value="External">{{ t('agentBuilder.llmRoutingOptions.external') }}</option>
                  <option value="Internal">{{ t('agentBuilder.llmRoutingOptions.internal') }}</option>
                  <option value="Hybrid">{{ t('agentBuilder.llmRoutingOptions.hybrid') }}</option>
                </select>
                <small class="text-muted">{{ t('agentBuilder.fields.llmRoutingHelp') }}</small>
              </div>

              <div v-if="agentForm.llmRouting === 'Hybrid'" class="mb-4">
                <label class="form-label">{{ t('agentBuilder.fields.routingPolicyJson') }}</label>
                <textarea
                  class="form-control"
                  :class="{ 'is-invalid': routingPolicyJsonError }"
                  v-model="agentForm.routingPolicyJson"
                  rows="4"
                  placeholder='{"default":"external","piiAction":"internal"}'
                  @blur="validateRoutingPolicyJson"
                ></textarea>
                <div v-if="routingPolicyJsonError" class="invalid-feedback d-block">
                  {{ routingPolicyJsonError }}
                </div>
                <small class="text-muted">{{ t('agentBuilder.fields.routingPolicyJsonHelp') }}</small>
              </div>

              <hr class="my-4">

              <!-- 그룹 2: 지식베이스 (RAG) -->
              <h6 class="mb-3"><i class="bi bi-database"></i> {{ t('agentBuilder.fields.knowledgeBaseSource') }}</h6>
              <div class="mb-4">
                <label class="form-label">{{ t('agentBuilder.fields.knowledgeBaseSource') }}</label>
                <select class="form-select" v-model="agentForm.knowledgeBaseSource">
                  <option value="DocUtil">{{ t('agentBuilder.knowledgeBaseSourceOptions.docutil') }}</option>
                  <option value="AgentHub" class="text-muted">{{ t('agentBuilder.knowledgeBaseSourceOptions.agentHub') }}</option>
                </select>
                <small class="text-muted">{{ t('agentBuilder.fields.knowledgeBaseSourceHelp') }}</small>
              </div>

              <div v-if="agentForm.knowledgeBaseSource === 'DocUtil'" class="mb-4">
                <label class="form-label">{{ t('agentBuilder.fields.knowledgeBaseRef') }}</label>
                <input
                  type="text"
                  class="form-control"
                  v-model="agentForm.knowledgeBaseRef"
                  placeholder="예: 부산대-2024-사업계획"
                />
                <small class="text-muted">{{ t('agentBuilder.fields.knowledgeBaseRefHelp') }}</small>
              </div>

              <hr class="my-4">

              <!-- 그룹 3: 호출 화이트리스트 -->
              <h6 class="mb-3"><i class="bi bi-shield-check"></i> {{ t('agentBuilder.fields.consumerSystems') }}</h6>
              <div class="mb-4">
                <label class="form-label">{{ t('agentBuilder.fields.consumerSystems') }}</label>
                <textarea
                  class="form-control"
                  :class="{ 'is-invalid': consumerSystemsError }"
                  v-model="agentForm.consumerSystems"
                  rows="2"
                  placeholder='["docutil-user","career-coaching"]'
                  @blur="validateConsumerSystems"
                ></textarea>
                <div v-if="consumerSystemsError" class="invalid-feedback d-block">
                  {{ consumerSystemsError }}
                </div>
                <small class="text-muted">{{ t('agentBuilder.fields.consumerSystemsHelp') }}</small>
              </div>

              <hr class="my-4">

              <!-- 그룹 4: 정렬 순서 -->
              <h6 class="mb-3"><i class="bi bi-sort-numeric-down"></i> {{ t('agentBuilder.fields.sortOrder') }}</h6>
              <div class="mb-2">
                <label class="form-label">{{ t('agentBuilder.fields.sortOrder') }}</label>
                <input
                  type="number"
                  class="form-control"
                  style="max-width: 200px;"
                  v-model.number="agentForm.sortOrder"
                  min="0"
                  placeholder="0"
                />
                <small class="text-muted">{{ t('agentBuilder.fields.sortOrderHelp') }}</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 5: 테스트 & 배포 -->
        <div class="step-content" :class="{ active: currentStep === 5 }">
          <!-- 탭 -->
          <ul class="nav nav-tabs mb-3">
            <li class="nav-item">
              <button class="nav-link" :class="{ active: step5Tab === 'test' }" @click="step5Tab = 'test'">
                <i class="bi bi-play-circle"></i> 테스트
              </button>
            </li>
            <li class="nav-item">
              <button class="nav-link" :class="{ active: step5Tab === 'share' }" @click="step5Tab = 'share'">
                <i class="bi bi-share"></i> 공유 & 임베드
              </button>
            </li>
          </ul>

          <!-- 테스트 탭 -->
          <div v-if="step5Tab === 'test'" class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5><i class="bi bi-play-circle"></i> 테스트해보기</h5>
            </div>
            <div class="card-body">
              <div class="alert alert-success" v-if="testResult">
                <i class="bi bi-check-circle"></i> 테스트 성공! Agent가 정상 응답합니다.
              </div>
              <div class="mb-3">
                <textarea
                  class="form-control"
                  v-model="testInput"
                  rows="3"
                  placeholder="테스트 메시지를 입력하세요..."
                ></textarea>
              </div>
              <button class="btn btn-primary mb-4" @click="runTest" :disabled="testing">
                <i class="bi bi-play-fill"></i> {{ testing ? '테스트 중...' : '테스트 실행' }}
              </button>
              <div v-if="testOutput" class="mb-4">
                <h6 class="mb-3">테스트 결과</h6>
                <div class="p-3 bg-light rounded">
                  <pre class="mb-0" style="white-space: pre-wrap;">{{ testOutput }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- 공유 & 임베드 탭 -->
          <div v-if="step5Tab === 'share'" class="card aiuiux-card mb-4">
            <div class="card-header bg-transparent border-bottom">
              <h5><i class="bi bi-share"></i> 공유 & 임베드 설정</h5>
            </div>
            <div class="card-body">

              <!-- 게스트 채팅 허용 -->
              <div class="mb-4">
                <div class="form-check form-switch mb-1">
                  <input class="form-check-input" type="checkbox" id="allowGuestChat" v-model="agentForm.allowGuestChat" />
                  <label class="form-check-label fw-bold" for="allowGuestChat">게스트 채팅 허용 (비로그인 사용자)</label>
                </div>
                <small class="text-muted">활성화 시 아래 URL/임베드 기능을 사용할 수 있습니다.</small>
              </div>

              <!-- 챗봇 커스텀 설정 -->
              <div class="mb-4 p-3 border rounded">
                <h6 class="mb-3"><i class="bi bi-sliders"></i> 챗봇 커스텀</h6>
                <div class="mb-3">
                  <label class="form-label">환영 메시지 <small class="text-muted">(챗봇 시작 시 봇이 먼저 보내는 메시지)</small></label>
                  <textarea class="form-control" v-model="agentForm.welcomeMessage" rows="2"
                    placeholder="예) 안녕하세요! 무엇을 도와드릴까요?"></textarea>
                </div>
                <div class="mb-3">
                  <label class="form-label">입력창 안내 문구</label>
                  <input type="text" class="form-control" v-model="agentForm.placeholderText"
                    placeholder="예) 궁금한 점을 입력하세요..." />
                </div>
                <div class="mb-3">
                  <label class="form-label">테마</label>
                  <select class="form-select" v-model="agentForm.chatTheme">
                    <option value="light">🌞 밝은 테마 (Light)</option>
                    <option value="dark">🌙 어두운 테마 (Dark)</option>
                    <option value="auto">🔄 시스템 따름 (Auto)</option>
                  </select>
                </div>
              </div>

              <!-- 임베드 도메인 화이트리스트 -->
              <div class="mb-4" v-if="agentForm.allowGuestChat">
                <label class="form-label fw-bold">
                  <i class="bi bi-shield-lock"></i> 임베드 허용 도메인
                  <small class="text-muted fw-normal ms-1">(선택, 비워두면 전체 허용)</small>
                </label>
                <textarea class="form-control" v-model="agentForm.allowedEmbedDomains" rows="2"
                  placeholder="예) https://example.com,https://partner.com (쉼표로 구분)"></textarea>
                <small class="text-muted">설정 시 허용 도메인의 iframe에서만 임베드 채팅을 사용할 수 있습니다.</small>
              </div>

              <!-- 저장 후 공유 링크 표시 -->
              <template v-if="savedAgentCode">
                <div class="mb-4 p-3 border rounded bg-light">
                  <h6 class="mb-3"><i class="bi bi-link-45deg"></i> 공유 링크</h6>

                  <!-- 테스트 페이지 -->
                  <div class="mb-3">
                    <label class="form-label small text-muted">🔬 내부 테스트 페이지 (로그인 필요)</label>
                    <div class="input-group">
                      <input type="text" class="form-control form-control-sm" :value="testPageUrl" readonly />
                      <button class="btn btn-outline-secondary btn-sm" @click="copyText(testPageUrl, 'test')" title="복사">
                        <i :class="copySuccess === 'test' ? 'bi bi-check' : 'bi bi-copy'"></i>
                      </button>
                      <a :href="testPageUrl" target="_blank" class="btn btn-outline-primary btn-sm">
                        <i class="bi bi-box-arrow-up-right"></i>
                      </a>
                    </div>
                  </div>

                  <!-- 챗봇 공유 URL -->
                  <div class="mb-3">
                    <label class="form-label small text-muted">🤖 챗봇 공유 URL (비로그인 접근 가능)</label>
                    <div v-if="!agentForm.allowGuestChat" class="alert alert-warning py-2 small">
                      <i class="bi bi-lock"></i> 게스트 채팅을 허용해야 사용 가능합니다.
                    </div>
                    <div v-else class="input-group">
                      <input type="text" class="form-control form-control-sm" :value="chatbotUrl" readonly />
                      <button class="btn btn-outline-secondary btn-sm" @click="copyText(chatbotUrl, 'chatbot')">
                        <i :class="copySuccess === 'chatbot' ? 'bi bi-check' : 'bi bi-copy'"></i>
                      </button>
                      <a :href="chatbotUrl" target="_blank" class="btn btn-outline-primary btn-sm">
                        <i class="bi bi-box-arrow-up-right"></i>
                      </a>
                    </div>
                  </div>

                  <!-- 임베드 -->
                  <div>
                    <label class="form-label small text-muted">📌 웹페이지 임베드 코드</label>
                    <div v-if="!agentForm.allowGuestChat" class="alert alert-warning py-2 small">
                      <i class="bi bi-lock"></i> 게스트 채팅을 허용해야 사용 가능합니다.
                    </div>
                    <template v-else>
                      <div class="d-flex gap-2 mb-2 align-items-center">
                        <label class="small">너비</label>
                        <input type="number" class="form-control form-control-sm" style="width:90px" v-model="embedWidth" />
                        <label class="small">높이</label>
                        <input type="number" class="form-control form-control-sm" style="width:90px" v-model="embedHeight" />
                        <span class="text-muted small">px</span>
                      </div>
                      <div class="position-relative">
                        <pre class="bg-dark text-light p-3 rounded small" style="white-space:pre-wrap;font-size:11px">{{ embedCode }}</pre>
                        <button class="btn btn-sm btn-light position-absolute top-0 end-0 m-2"
                          @click="copyText(embedCode, 'embed')">
                          <i :class="copySuccess === 'embed' ? 'bi bi-check text-success' : 'bi bi-copy'"></i>
                          {{ copySuccess === 'embed' ? '복사됨!' : '복사' }}
                        </button>
                      </div>
                    </template>
                  </div>
                </div>
              </template>

              <!-- QR 코드 -->
              <div v-if="agentForm.allowGuestChat" class="mt-3">
                <h6 class="mb-2"><i class="bi bi-qr-code"></i> QR 코드</h6>
                <div class="d-flex align-items-start gap-3">
                  <img :src="`/api/agents/public/${savedAgentCode}/qr?size=200`"
                    alt="QR Code" width="120" height="120"
                    class="border rounded p-1 bg-white" />
                  <div>
                    <p class="small text-muted mb-2">QR 코드를 스캔하면 챗봇 페이지로 바로 이동합니다.</p>
                    <a :href="`/api/agents/public/${savedAgentCode}/qr?size=400`"
                      download="qr-code.png" class="btn btn-sm btn-outline-secondary">
                      <i class="bi bi-download"></i> 다운로드
                    </a>
                  </div>
                </div>
              </div>

              <!-- 아직 저장 전 -->
              <template v-else>
                <div class="alert alert-info">
                  <i class="bi bi-info-circle"></i>
                  Agent를 저장하면 공유 URL 및 임베드 코드가 생성됩니다.
                </div>
              </template>

            </div>
          </div>
        </div>

        <!-- 네비게이션 버튼 -->
        <div class="d-flex justify-content-between mb-4">
          <button 
            class="btn btn-secondary" 
            @click="prevStep"
            :disabled="currentStep === 1"
          >
            <i class="bi bi-arrow-left"></i> 이전
          </button>
          <button 
            v-if="currentStep < 5"
            class="btn btn-primary" 
            @click="nextStep"
          >
            다음 <i class="bi bi-arrow-right"></i>
          </button>
          <button 
            v-else
            class="btn btn-success" 
            @click="saveAgent"
            :disabled="saving"
          >
            <i class="bi bi-check-circle"></i> {{ saving ? '저장 중...' : isEditMode ? 'Agent 수정 완료' : 'Agent 저장' }}
          </button>
        </div>
      </div>

      <!-- 우측 미리보기 -->
      <div class="col-lg-4">
        <div class="card aiuiux-card ab-preview-card">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0 fw-semibold"><i class="bi bi-eye me-1"></i> 미리보기</h6>
          </div>
          <div class="card-body text-center">
            <div
              class="ab-preview-icon mx-auto mb-3"
              :style="{ background: agentForm.colorCode || 'var(--ai-primary)' }"
            >
              <i :class="agentForm.iconClass || 'bi bi-robot'"></i>
            </div>
            <h6 class="fw-bold mb-1">{{ agentForm.agentName || '새 Agent' }}</h6>
            <p class="text-muted small mb-3">{{ agentForm.description || 'Agent 설명이 여기에 표시됩니다.' }}</p>
            <div class="mb-3">
              <span class="badge" :style="{ background: agentForm.colorCode || 'var(--ai-primary)' }">
                {{ getServiceName() || '서비스 미선택' }}
              </span>
            </div>
            <div class="ab-preview-meta">
              <div class="ab-preview-meta-row">
                <span class="ab-preview-meta-label">모델</span>
                <span class="ab-preview-meta-value">{{ agentForm.defaultModel || '-' }}</span>
              </div>
              <div class="ab-preview-meta-row">
                <span class="ab-preview-meta-label">Temperature</span>
                <span class="ab-preview-meta-value">{{ (agentForm.temperature || 0.7).toFixed(1) }}</span>
              </div>
              <div class="ab-preview-meta-row">
                <span class="ab-preview-meta-label">Max Tokens</span>
                <span class="ab-preview-meta-value">{{ agentForm.maxTokens || '-' }}</span>
              </div>
              <div class="ab-preview-meta-row">
                <span class="ab-preview-meta-label">RAG</span>
                <span class="ab-preview-meta-value" :class="agentForm.enableRag ? 'text-success' : 'text-muted'">
                  {{ agentForm.enableRag ? '활성' : '비활성' }}
                </span>
              </div>
              <div class="ab-preview-meta-row">
                <span class="ab-preview-meta-label">게스트 채팅</span>
                <span class="ab-preview-meta-value" :class="agentForm.allowGuestChat ? 'text-success' : 'text-muted'">
                  {{ agentForm.allowGuestChat ? '허용' : '비허용' }}
                </span>
              </div>
            </div>
          </div>
          <!-- 진행도 표시 -->
          <div class="card-footer bg-transparent border-top pt-2 pb-3 px-3">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <small class="text-muted">완성도</small>
              <small class="fw-semibold" style="color: var(--ai-primary)">{{ completionPercent }}%</small>
            </div>
            <div class="progress" style="height:5px;border-radius:10px;">
              <div class="progress-bar" role="progressbar"
                :style="{ width: completionPercent + '%', background: 'var(--ai-primary)' }">
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 후속 트랙 B-1 (2026-05-08) 완료: AgentDto / ConversationDto / ApiServiceDto 의 TypeScript 타입을
// 백엔드 C# Models/DTOs (Agent.cs / ConversationDto.cs / ApiServiceDto.cs) 와 정렬 후 `@ts-nocheck` 해제.
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import type { AgentDto } from '@/types'

// 후속 트랙 (2026-05-08): 신규 운영자 고급 설정 카드(LlmRouting/KB/ConsumerSystems/SortOrder) 의 라벨/help 텍스트는 i18n locale 에서 로드.
const { t } = useI18n()

interface ApiService {
  serviceId: number
  serviceName: string
}

interface Step {
  number: number
  title: string
}

const router = useRouter()
const route = useRoute()
const editingAgentId = ref<number | null>(null)
const isEditMode = computed(() => editingAgentId.value !== null)
const currentStep = ref(1)
const saving = ref(false)
const testing = ref(false)
const testInput = ref('')
const testOutput = ref('')
const testResult = ref(false)

const steps: Step[] = [
  { number: 1, title: '기본 정보' },
  { number: 2, title: 'AI 설정' },
  { number: 3, title: '프롬프트' },
  { number: 4, title: '고급 기능' },
  { number: 5, title: '테스트 & 배포' }
]

const services = ref<ApiService[]>([])
const availableModels = ref<string[]>([])

const agentForm = ref({
  agentName: '',
  description: '',
  serviceId: 0,
  defaultModel: '',
  systemPrompt: '',
  iconClass: 'bi bi-robot',
  colorCode: '#0d6efd',
  temperature: 0.7,
  maxTokens: 4096,
  isPublic: false,
  // 후속 트랙 B-1 (2026-05-08): template 의 RAG 미리보기 (line 547-548) 가 참조하는 필드.
  // 백엔드 Agent.cs 의 EnableRag (Required bool) 와 정렬. Phase 6.5 부터 DocUtil 위임 흐름이 활성화될 때
  // 사용자 토글 UI 가 추가될 예정 — 현재는 template 미리보기에서 RAG 활성/비활성 상태만 표시.
  enableRag: false,
  piiProtectionEnabled: true,
  piiProtectionMode: null as string | null,
  // 공유 / 임베드
  welcomeMessage: '',
  placeholderText: '',
  chatTheme: 'light',
  allowGuestChat: false,
  allowedEmbedDomains: '',
  // 후속 트랙 (2026-05-08): 백엔드 AgentDto 갭 보강 commit b3a2d85 의 6 신규 필드 운영자 폼.
  // 빈 문자열은 백엔드 서비스 레이어에서 null 정규화 + 기본값 폴백 처리 (CreateAgentAsync line 153-179, UpdateAgentAsync line 209-236).
  llmRouting: 'External', // Phase 5.1 라우팅 모드, 기본 External
  routingPolicyJson: '', // Hybrid 전용 결정 규칙 JSON, 비어두면 백엔드 기본 정책 사용
  knowledgeBaseSource: 'AgentHub', // ADR-2: 신규 Agent 는 백엔드 default 와 정렬, UI 가 'DocUtil' 권장
  knowledgeBaseRef: '', // DocUtil collection ID, 비어두면 글로벌 corpus
  consumerSystems: '', // 호출 가능 End-User App ID JSON 배열 텍스트
  sortOrder: 0, // 같은 카테고리 내 정렬 순서
})
// 후속 트랙 (2026-05-08): 신규 6 필드 중 JSON 입력 필드 2개의 클라이언트 검증 상태.
// 빈 문자열은 valid 로 취급하고, 비어있지 않을 때만 JSON 파싱 시도. 실패 시 한국어 에러 메시지 표시 (제출은 막지 않음 — 백엔드가 최종 검증).
const routingPolicyJsonError = ref<string>('')
const consumerSystemsError = ref<string>('')

const validateRoutingPolicyJson = () => {
  const raw = agentForm.value.routingPolicyJson?.trim() ?? ''
  if (!raw) { routingPolicyJsonError.value = ''; return }
  try {
    const parsed = JSON.parse(raw)
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      routingPolicyJsonError.value = 'JSON 객체 형식이어야 합니다. 예: {"default":"external","piiAction":"internal"}'
      return
    }
    routingPolicyJsonError.value = ''
  } catch {
    routingPolicyJsonError.value = '유효한 JSON 형식이 아닙니다. 예: {"default":"external","piiAction":"internal"}'
  }
}

const validateConsumerSystems = () => {
  const raw = agentForm.value.consumerSystems?.trim() ?? ''
  if (!raw) { consumerSystemsError.value = ''; return }
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || !parsed.every((v) => typeof v === 'string')) {
      consumerSystemsError.value = '문자열 JSON 배열 형식이어야 합니다. 예: ["docutil-user","career-coaching"]'
      return
    }
    consumerSystemsError.value = ''
  } catch {
    consumerSystemsError.value = '유효한 JSON 형식이 아닙니다. 예: ["docutil-user","career-coaching"]'
  }
}

const step5Tab = ref<'test' | 'share'>('test')
const savedAgentCode = ref<string | null>(null)
const embedWidth = ref(400)
const embedHeight = ref(600)
const copySuccess = ref('')

const completionPercent = computed(() => {
  let score = 0
  if (agentForm.value.agentName) score += 20
  if (agentForm.value.description) score += 10
  if (agentForm.value.serviceId) score += 20
  if (agentForm.value.defaultModel) score += 10
  if (agentForm.value.systemPrompt) score += 25
  if (agentForm.value.iconClass !== 'bi bi-robot' || agentForm.value.colorCode !== '#0d6efd') score += 5
  if (agentForm.value.welcomeMessage) score += 10
  return Math.min(score, 100)
})

const chatbotUrl = computed(() =>
  savedAgentCode.value ? `${window.location.origin}/chatbot/${savedAgentCode.value}` : ''
)
const embedUrl = computed(() =>
  savedAgentCode.value ? `${window.location.origin}/embed/${savedAgentCode.value}?theme=${agentForm.value.chatTheme}` : ''
)
const testPageUrl = computed(() =>
  savedAgentCode.value ? `${window.location.origin}/agent-test/${savedAgentCode.value}` : ''
)
const embedCode = computed(() =>
  savedAgentCode.value
    ? `<iframe\n  src="${embedUrl.value}"\n  width="${embedWidth.value}"\n  height="${embedHeight.value}"\n  frameborder="0"\n  style="border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.12)"\n></iframe>`
    : ''
)

async function copyText(text: string, key: string) {
  await navigator.clipboard.writeText(text)
  copySuccess.value = key
  setTimeout(() => { copySuccess.value = '' }, 2000)
}

const availableIcons = [
  { class: 'bi bi-code-square', name: '코드' },
  { class: 'bi bi-file-text', name: '문서' },
  { class: 'bi bi-graph-up', name: '그래프' },
  { class: 'bi bi-lightbulb', name: '아이디어' },
  { class: 'bi bi-book', name: '책' },
  { class: 'bi bi-megaphone', name: '마케팅' },
  { class: 'bi bi-translate', name: '번역' },
  { class: 'bi bi-robot', name: '로봇' },
  { class: 'bi bi-pencil-square', name: '편집' },
  { class: 'bi bi-chat-dots', name: '채팅' },
  { class: 'bi bi-cpu', name: 'CPU' },
  { class: 'bi bi-briefcase', name: '비즈니스' }
]

// 흰색 제외 - agent 배지/아이콘에서 가독성을 위해
const WHITE_COLORS = ['#ffffff', '#fff', '#FFFFFF', '#FFF', 'white']
const DEFAULT_AGENT_COLOR = '#0d6efd'
const availableColors = [
  '#0d6efd', '#198754', '#ffc107', '#dc3545',
  '#6610f2', '#0dcaf0', '#fd7e14', '#d63384'
]

const sanitizeColorCode = (color: string | null | undefined): string => {
  if (!color) return DEFAULT_AGENT_COLOR
  const normalized = color.trim().toLowerCase()
  if (WHITE_COLORS.includes(color.trim()) || normalized === '#fff' || normalized === '#ffffff') return DEFAULT_AGENT_COLOR
  return color
}

const loadServices = async () => {
  try {
    const response = await api.get<ApiService[]>('/apiservices')
    services.value = response.data || []
  } catch (error) {
    console.error('Error loading services:', error)
  }
}

const loadModels = async (serviceId: number) => {
  if (!serviceId) { availableModels.value = []; return }
  try {
    const res = await api.get<string[]>(`/apiservices/${serviceId}/models`)
    availableModels.value = res.data || []
    if (availableModels.value.length > 0 && !availableModels.value.includes(agentForm.value.defaultModel)) {
      agentForm.value.defaultModel = availableModels.value[0]
    }
  } catch (error) {
    console.error('Error loading models:', error)
    availableModels.value = []
  }
}

watch(() => agentForm.value.serviceId, (id) => {
  if (id) loadModels(id)
  else availableModels.value = []
})

const selectIcon = (icon: { class: string }) => {
  agentForm.value.iconClass = icon.class
  updatePreview()
}

const selectColor = (color: string) => {
  agentForm.value.colorCode = sanitizeColorCode(color) || color
  updatePreview()
}

const updatePreview = () => {
  // 미리보기는 자동으로 업데이트됨
}

const promptTemplates: Record<string, string> = {
  customer: '당신은 친절하고 전문적인 고객지원 담당자입니다. 고객의 문의를 경청하고 신속하고 정확한 해결책을 제공하세요. 공감하는 태도로 응대하되 간결하게 답변하세요.',
  analysis: '당신은 데이터 분석 및 요약 전문가입니다. 주어진 정보를 핵심 내용 위주로 명확하게 정리하고, 필요 시 bullet point를 활용하여 가독성 높게 제공하세요.',
  coding: '당신은 경험이 풍부한 시니어 개발자입니다. 코드 리뷰 시 버그, 성능 개선점, 가독성 문제를 구체적인 이유와 함께 제시하고 개선된 코드 예시도 함께 제공하세요.',
  translate: '당신은 전문 번역가입니다. 원문의 뉘앙스와 문맥을 유지하면서 자연스럽게 번역하세요. 전문 용어는 적절한 표현을 사용하고, 필요 시 원어를 괄호 안에 병기하세요.',
  assistant: '당신은 유능하고 친절한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.'
}

// ── 응답 스타일 지시문 ────────────────────────────────────────────────────
const STYLE_MARKER = '<!-- style:'
const styleSnippets: Record<string, string> = {
  professional: `\n\n<!-- style:professional -->\n## 응답 형식\n- 마크다운(##, **굵게**, 표, 코드블록)을 적극 활용하세요.\n- 핵심 정보는 표나 목록으로 구조화하세요.\n- 이모지는 사용하지 마세요.\n- 전문적이고 간결한 문체를 유지하세요.`,
  friendly: `\n\n<!-- style:friendly -->\n## 응답 형식\n- 섹션 제목 앞에 관련 이모지를 1개 붙이세요. (예: ## 📌 핵심 개념)\n- ✅ 좋은 예, ❌ 나쁜 예, ⚠️ 주의, 💡 팁 이모지를 상황에 맞게 사용하세요.\n- 친근하고 대화체로 쉽게 설명하세요.\n- 초보자도 이해할 수 있도록 구체적인 예시를 들어주세요.`,
  concise: `\n\n<!-- style:concise -->\n## 응답 형식\n- 답변은 3~5문장 이내로 핵심만 전달하세요.\n- 서론·배경 설명 없이 바로 본론으로 시작하세요.\n- 불필요한 예의 표현("물론입니다", "좋은 질문이에요") 생략하세요.\n- 추가 설명이 필요한 경우 사용자가 요청하도록 안내하세요.`,
  stepbystep: `\n\n<!-- style:stepbystep -->\n## 응답 형식\n- 복잡한 내용은 반드시 번호 목록(1. 2. 3.)으로 단계별로 설명하세요.\n- 각 단계에 구체적인 예시나 코드를 포함하세요.\n- 단계 사이의 인과관계를 명확히 설명하세요.\n- 마지막에 전체 흐름을 한 줄로 요약하세요.`
}

const activeStyle = ref<string>('')

const applyStyle = (key: string) => {
  // 기존 스타일 지시문 제거 후 새 스타일 추가
  let base = agentForm.value.systemPrompt.replace(/\n*<!-- style:[^>]+ -->[\s\S]*$/m, '').trimEnd()
  agentForm.value.systemPrompt = base + (styleSnippets[key] ?? '')
  activeStyle.value = key
}

const removeStyle = () => {
  agentForm.value.systemPrompt = agentForm.value.systemPrompt
    .replace(/\n*<!-- style:[^>]+ -->[\s\S]*$/m, '')
    .trimEnd()
  activeStyle.value = ''
}

const applyPromptTemplate = (key: string) => {
  // 템플릿 적용 시 기존 스타일 지시문은 유지
  const currentStyle = activeStyle.value
  agentForm.value.systemPrompt = (promptTemplates[key] ?? '')
  if (currentStyle) applyStyle(currentStyle)
}

const getServiceName = (): string => {
  const service = services.value.find(s => s.serviceId === agentForm.value.serviceId)
  return service?.serviceName || '-'
}

const goToStep = (step: number) => {
  if (step <= currentStep.value || isStepCompleted(step - 1)) {
    currentStep.value = step
  }
}

const isStepCompleted = (step: number): boolean => {
  switch (step) {
    case 1:
      return !!(agentForm.value.agentName && agentForm.value.description)
    case 2:
      return !!(agentForm.value.serviceId && agentForm.value.defaultModel)
    case 3:
      return !!agentForm.value.systemPrompt
    case 4:
      return true
    default:
      return false
  }
}

const nextStep = () => {
  if (currentStep.value < 5 && validateStep(currentStep.value)) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const validateStep = (step: number): boolean => {
  switch (step) {
    case 1:
      if (!agentForm.value.agentName || !agentForm.value.description) {
        alert('Agent 이름과 설명을 입력해주세요.')
        return false
      }
      return true
    case 2:
      if (!agentForm.value.serviceId || !agentForm.value.defaultModel) {
        alert('AI 서비스와 모델을 선택해주세요.')
        return false
      }
      return true
    case 3:
      if (!agentForm.value.systemPrompt) {
        alert('시스템 프롬프트를 입력해주세요.')
        return false
      }
      return true
    default:
      return true
  }
}

const runTest = async () => {
  if (!testInput.value.trim()) {
    alert('테스트 메시지를 입력해주세요.')
    return
  }

  try {
    testing.value = true
    testOutput.value = ''
    
    const response = await api.post('/chat/send', {
      serviceId: agentForm.value.serviceId,
      agentId: null,
      model: agentForm.value.defaultModel,
      temperature: agentForm.value.temperature,
      maxTokens: agentForm.value.maxTokens,
      messages: [
        { role: 'system', content: agentForm.value.systemPrompt },
        { role: 'user', content: testInput.value }
      ],
      stream: false
    })

    testOutput.value = response.data.content || '응답이 없습니다.'
    testResult.value = true
  } catch (error: any) {
    console.error('Error testing agent:', error)
    testOutput.value = '오류: ' + (error.response?.data?.message || error.message)
  } finally {
    testing.value = false
  }
}

const saveAgent = async () => {
  if (!validateStep(1) || !validateStep(2) || !validateStep(3)) {
    alert('필수 항목을 모두 입력해주세요.')
    return
  }

  try {
    saving.value = true
    const payload = { ...agentForm.value, colorCode: sanitizeColorCode(agentForm.value.colorCode) }

    if (isEditMode.value) {
      // 수정 모드: PUT
      const response = await api.put(`/agents/${editingAgentId.value}`, payload)
      savedAgentCode.value = response.data?.agentCode || savedAgentCode.value
      alert('Agent가 성공적으로 수정되었습니다!')
    } else {
      // 신규 생성: POST
      const response = await api.post('/agents', payload)
      savedAgentCode.value = response.data?.agentCode || null
      editingAgentId.value = response.data?.agentId || null
      alert('Agent가 성공적으로 생성되었습니다!')
    }
    step5Tab.value = 'share'
  } catch (error: any) {
    console.error('Error saving agent:', error)
    alert(error.response?.data?.message || 'Agent 저장 중 오류가 발생했습니다.')
  } finally {
    saving.value = false
  }
}

const loadAgentForEdit = async (agentId: number) => {
  try {
    const response = await api.get(`/agents/${agentId}`)
    const agent: AgentDto = response.data
    editingAgentId.value = agent.agentId
    savedAgentCode.value = agent.agentCode || null
    agentForm.value = {
      agentName: agent.agentName || '',
      description: agent.description || '',
      serviceId: agent.serviceId || 0,
      defaultModel: agent.defaultModel || '',
      systemPrompt: agent.systemPrompt || '',
      iconClass: agent.iconClass || 'bi bi-robot',
      colorCode: agent.colorCode || '#0d6efd',
      temperature: agent.temperature ?? 0.7,
      maxTokens: agent.maxTokens || 4096,
      isPublic: agent.isPublic || false,
      // 후속 트랙 B-1 (2026-05-08): 백엔드 AgentDto.enableRag 가 optional (?)이므로 ?? false 폴백 — 기존 동작 보존.
      enableRag: agent.enableRag ?? false,
      piiProtectionEnabled: agent.piiProtectionEnabled ?? true,
      piiProtectionMode: agent.piiProtectionMode || null,
      welcomeMessage: agent.welcomeMessage || '',
      placeholderText: agent.placeholderText || '',
      chatTheme: agent.chatTheme || 'light',
      allowGuestChat: agent.allowGuestChat || false,
      allowedEmbedDomains: agent.allowedEmbedDomains || '',
      // 후속 트랙 (2026-05-08): 백엔드 b3a2d85 의 6 신규 필드 매핑.
      // null/undefined → 화면 default 값으로 폴백, 빈 문자열은 그대로 유지하여 placeholder 가 보이도록.
      llmRouting: agent.llmRouting || 'External',
      routingPolicyJson: agent.routingPolicyJson ?? '',
      knowledgeBaseSource: agent.knowledgeBaseSource || 'AgentHub',
      knowledgeBaseRef: agent.knowledgeBaseRef ?? '',
      consumerSystems: agent.consumerSystems ?? '',
      sortOrder: agent.sortOrder ?? 0,
    }
  } catch (error: any) {
    console.error('Error loading agent for edit:', error)
    alert('에이전트 정보를 불러오는 중 오류가 발생했습니다.')
    router.push('/agents')
  }
}

const saveDraft = () => {
  localStorage.setItem('agent_draft', JSON.stringify(agentForm.value))
  alert('임시 저장되었습니다.')
}

const resetBuilder = () => {
  if (confirm('작성 중인 내용을 모두 삭제하시겠습니까?')) {
    agentForm.value = {
      agentName: '',
      description: '',
      serviceId: 0,
      defaultModel: '',
      systemPrompt: '',
      iconClass: 'bi bi-robot',
      colorCode: '#0d6efd',
      temperature: 0.7,
      maxTokens: 4096,
      isPublic: false,
      // 후속 트랙 B-1 (2026-05-08): reset 시에도 동일 shape 유지.
      enableRag: false,
      piiProtectionEnabled: true,
      piiProtectionMode: null,
      welcomeMessage: '',
      placeholderText: '',
      chatTheme: 'light',
      allowGuestChat: false,
      allowedEmbedDomains: '',
      // 후속 트랙 (2026-05-08): 6 신규 필드 default reset.
      llmRouting: 'External',
      routingPolicyJson: '',
      knowledgeBaseSource: 'AgentHub',
      knowledgeBaseRef: '',
      consumerSystems: '',
      sortOrder: 0,
    }
    routingPolicyJsonError.value = ''
    consumerSystemsError.value = ''
    currentStep.value = 1
    step5Tab.value = 'test'
    savedAgentCode.value = null
    testInput.value = ''
    testOutput.value = ''
    testResult.value = false
  }
}

onMounted(async () => {
  await loadServices()

  const idParam = route.params.id
  if (idParam) {
    // 수정 모드: route param의 id로 기존 에이전트 데이터 로드
    const agentId = parseInt(String(idParam), 10)
    if (!isNaN(agentId)) {
      await loadAgentForEdit(agentId)
    }
  } else {
    // 템플릿으로 만들기: query params에서 데이터 채우기
    const q = route.query
    if (q.templateName || q.templatePrompt) {
      agentForm.value.agentName = String(q.templateName || '')
      agentForm.value.description = String(q.templateDesc || '')
      agentForm.value.systemPrompt = String(q.templatePrompt || '')
      if (q.templateIcon) agentForm.value.iconClass = String(q.templateIcon)
      if (q.templateColor) agentForm.value.colorCode = String(q.templateColor)
    } else {
      // 신규 생성 모드: 임시 저장된 데이터 불러오기
      const draft = localStorage.getItem('agent_draft')
      if (draft) {
        try {
          agentForm.value = { ...agentForm.value, ...JSON.parse(draft) }
        } catch (e) {
          console.error('Error loading draft:', e)
        }
      }
    }
  }
})
</script>

<style scoped>
/* ── Step Indicator ──────────────────────────────────────────────────────── */
.step-indicator {
  display: flex;
  margin-bottom: 28px;
  position: relative;
  background: var(--ai-bg-card);
  border: 1px solid var(--ai-border);
  border-radius: var(--ai-radius-lg);
  padding: 16px 8px;
  box-shadow: var(--ai-shadow-sm);
}
.step-indicator::before {
  content: '';
  position: absolute;
  top: 36px;
  left: 10%;
  right: 10%;
  height: 2px;
  background: var(--ai-border);
  z-index: 0;
}

.step {
  flex: 1;
  text-align: center;
  padding: 4px 8px;
  cursor: pointer;
  transition: all 0.25s;
  position: relative;
  z-index: 1;
}
.step:hover .step-circle { border-color: var(--ai-primary); }

.step-circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--ai-bg-page);
  border: 2px solid var(--ai-border);
  color: var(--ai-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 7px;
  font-weight: 700;
  font-size: 0.88rem;
  transition: all 0.25s;
}

.step.active .step-circle {
  background: var(--ai-primary);
  border-color: var(--ai-primary);
  color: #fff;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.18);
}
.step.completed .step-circle {
  background: var(--ai-success);
  border-color: var(--ai-success);
  color: #fff;
}
.step.completed .step-circle::before { content: '✓'; font-size: 0.9rem; }

.step-title {
  font-size: 0.78rem;
  color: var(--ai-text-muted);
  font-weight: 500;
  white-space: nowrap;
}
.step.active .step-title {
  color: var(--ai-primary);
  font-weight: 700;
}
.step.completed .step-title { color: var(--ai-success); }

/* ── Step Content ────────────────────────────────────────────────────────── */
.step-content { display: none; }
.step-content.active {
  display: block;
  animation: abFadeIn 0.25s ease;
}
@keyframes abFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Icon Picker ─────────────────────────────────────────────────────────── */
.icon-picker {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
}
.icon-option {
  aspect-ratio: 1;
  border: 1.5px solid var(--ai-border);
  border-radius: var(--ai-radius);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.3rem;
  transition: all 0.18s;
  background: var(--ai-bg-card);
  color: var(--ai-text-secondary);
}
.icon-option:hover {
  border-color: var(--ai-primary);
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  transform: scale(1.08);
}
.icon-option.selected {
  border-color: var(--ai-primary);
  background: var(--ai-primary);
  color: #fff;
  box-shadow: 0 2px 8px rgba(79,70,229,0.3);
}

/* ── Color Picker ────────────────────────────────────────────────────────── */
.color-option {
  width: 36px;
  height: 36px;
  border-radius: var(--ai-radius);
  cursor: pointer;
  border: 2.5px solid transparent;
  transition: all 0.18s;
  box-shadow: var(--ai-shadow-sm);
}
.color-option:hover { transform: scale(1.15); border-color: var(--ai-text-primary); }
.color-option.selected {
  border-color: var(--ai-text-primary);
  transform: scale(1.15);
  box-shadow: 0 0 0 3px rgba(79,70,229,0.25);
}

/* ── Preview Card ────────────────────────────────────────────────────────── */
.ab-preview-card { position: sticky; top: 76px; }

.ab-preview-icon {
  width: 76px;
  height: 76px;
  border-radius: var(--ai-radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.2rem;
  color: #fff;
  box-shadow: 0 6px 18px rgba(79,70,229,0.28);
}

.ab-preview-meta {
  background: var(--ai-bg-page);
  border-radius: var(--ai-radius);
  padding: 10px 12px;
  text-align: left;
  margin-top: 4px;
}
.ab-preview-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid var(--ai-border-light);
  font-size: 12px;
}
.ab-preview-meta-row:last-child { border-bottom: none; }
.ab-preview-meta-label { color: var(--ai-text-muted); }
.ab-preview-meta-value { font-weight: 600; color: var(--ai-text-primary); font-size: 11.5px; }
</style>
