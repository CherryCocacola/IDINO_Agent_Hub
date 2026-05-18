<template>
  <div class="cd-chat-wrapper">
    <div class="cd-layout">
      <!-- 좌측 패널 - 설정 -->
      <aside class="cd-left-panel">
        <!-- 통계 -->
        <div class="cd-stats-row">
          <div class="cd-stat-card">
            <div class="cd-stat-value">
              <i class="bi bi-chat-dots"></i>
              <strong>{{ messages.length }}</strong>
            </div>
            <span>{{ $t('chat.messageCount') }}</span>
          </div>
          <div class="cd-stat-card">
            <div class="cd-stat-value">
              <i class="bi bi-hash" style="color:var(--ai-success);"></i>
              <strong>{{ stats.tokensUsed }}</strong>
            </div>
            <span>{{ $t('agentChat.tokensUsed') }}</span>
          </div>
          <div class="cd-stat-card">
            <div class="cd-stat-value">
              <i class="bi bi-currency-dollar" style="color:var(--ai-warning);"></i>
              <strong>${{ stats.cost.toFixed(2) }}</strong>
            </div>
            <span>{{ $t('agentChat.cost') }}</span>
          </div>
        </div>

        <!-- 모델 설정 -->
        <div class="cd-panel-card">
          <div class="cd-panel-header">
            <i class="bi bi-sliders"></i> {{ $t('agentChat.modelSettings') }}
          </div>
          <div class="cd-panel-body">
            <div class="cd-field">
              <label class="cd-label cd-label-row">
                <span>{{ $t('agentChat.model') }}</span>
                <span class="cd-hint cd-hint-inline" v-if="selectedService">{{ selectedService.serviceName }} · {{ $t('agentChat.modelsCount', { count: availableModels.length }) }}</span>
              </label>
              <select 
                class="cd-select" 
                v-model="modelSettings.model"
                :key="`model-select-${selectedService?.serviceId || 'none'}-${availableModels.length}`"
              >
                <option v-for="model in availableModels" :key="model" :value="model">{{ model }}</option>
              </select>
            </div>

            <div class="cd-field">
              <label class="cd-label cd-label-row">
                <span>{{ $t('agentChat.temperature') }}</span>
                <span class="cd-val-badge">{{ (modelSettings.temperature / 100).toFixed(1) }}</span>
              </label>
              <input 
                type="range" 
                class="cd-range" 
                v-model.number="modelSettings.temperature"
                min="0" 
                max="100"
              >
              <div class="cd-range-labels">
                <span>{{ $t('agentChat.accurate') }}</span>
                <span>{{ $t('agentChat.creative') }}</span>
              </div>
            </div>

            <div class="cd-field">
              <label class="cd-label">{{ $t('agentChat.maxTokens') }}</label>
              <input 
                type="number" 
                class="cd-input" 
                v-model.number="modelSettings.maxTokens"
                min="1" 
                max="32768"
              >
            </div>

            <!-- 웹 검색 옵션 -->
            <div class="cd-toggle-item" v-if="
              selectedService?.serviceCode?.toLowerCase() === 'chatgpt' || 
              selectedService?.serviceCode?.toLowerCase() === 'openai' ||
              selectedService?.serviceType === 'ImageGeneration' ||
              selectedService?.serviceType === 'Both' ||
              (modelSettings.model?.toLowerCase().includes('gemini') && modelSettings.model?.toLowerCase().includes('image'))
            ">
              <div class="cd-toggle-info">
                <div class="cd-toggle-title"><i class="bi bi-search"></i> {{ $t('agentChat.enableWebSearch') }}</div>
                <div class="cd-toggle-desc">{{ selectedService?.serviceType === 'ImageGeneration' || selectedService?.serviceType === 'Both' ? $t('agentChat.imageGenWebSearchDesc') : $t('agentChat.enableWebSearchDesc') }}</div>
              </div>
              <label class="cd-switch">
                <input type="checkbox" id="enableWebSearch" v-model="enableWebSearch">
                <span class="cd-switch-knob"></span>
              </label>
            </div>

            <!--
              EnableRag 토글: per-conversation RAG override.
              Agent.KnowledgeBaseSource="DocUtil" + Agent.KnowledgeBaseRef(collection ID) 정의(ADR-2)에 따라
              실제 RAG 권위는 Agent 단위로 결정되며, 사용자가 채팅 화면에서 문서를 직접 선택하는 패러다임은
              Phase 2 자체 KB drop 으로 폐기됨. 본 토글은 대화 단위 RAG on/off 만 제어한다.
            -->
            <div class="cd-toggle-item">
              <div class="cd-toggle-info">
                <div class="cd-toggle-title"><i class="bi bi-database"></i> {{ $t('agentChat.enableRag') }}</div>
                <div class="cd-toggle-desc">{{ $t('agentChat.enableRagDesc') }}</div>
              </div>
              <label class="cd-switch">
                <input type="checkbox" id="enableRag" v-model="enableRag">
                <span class="cd-switch-knob"></span>
              </label>
            </div>

            <div class="cd-toggle-item">
              <div class="cd-toggle-info">
                <div class="cd-toggle-title"><i class="bi bi-search-heart"></i> {{ $t('agentChat.deepResearch') }}</div>
                <div class="cd-toggle-desc">{{ $t('agentChat.deepResearchDesc') }}</div>
              </div>
              <label class="cd-switch">
                <input type="checkbox" id="enableDeepResearch" v-model="enableDeepResearch" :disabled="!enableWebSearch && !enableRag">
                <span class="cd-switch-knob"></span>
              </label>
            </div>

            <div class="cd-toggle-item">
              <div class="cd-toggle-info">
                <div class="cd-toggle-title"><i class="bi bi-lightbulb"></i> {{ $t('agentChat.deepThinking') }}</div>
                <div class="cd-toggle-desc">{{ $t('agentChat.deepThinkingDesc') }}</div>
              </div>
              <label class="cd-switch">
                <input type="checkbox" id="enableDeepThinking" v-model="enableDeepThinking">
                <span class="cd-switch-knob"></span>
              </label>
            </div>

            <div class="cd-field">
              <label class="cd-label cd-label-row">
                <span>{{ $t('agentChat.responseLanguage') }}</span>
                <span class="cd-hint cd-hint-inline">{{ $t('agentChat.responseLanguageDesc') }}</span>
              </label>
              <select class="cd-select" v-model="responseLanguage">
                <option value="auto">{{ $t('chat.auto') }}</option>
                <option value="ko">{{ $t('chat.korean') }}</option>
                <option value="en">{{ $t('chat.english') }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 할당량 정보 -->
        <div class="cd-panel-card">
          <div class="cd-panel-header">
            <i class="bi bi-pie-chart"></i> {{ $t('agentChat.quotaStatus') }}
          </div>
          <div class="cd-panel-body cd-quota-body">
            <div class="row align-items-center g-2">
              <div class="col-8">
                <div class="cd-quota-item">
                  <div class="cd-quota-row">
                    <span class="cd-quota-label">{{ $t('agentChat.todayUsed') }}</span>
                    <span class="cd-quota-val">{{ quota.todayUsed }} / {{ quota.dailyLimit }}</span>
                  </div>
                  <div class="cd-quota-bar">
                    <div class="cd-quota-fill success" :style="{ width: Math.min((quota.todayUsed / quota.dailyLimit * 100), 100) + '%' }"></div>
                  </div>
                </div>
                <div class="cd-quota-item">
                  <div class="cd-quota-row">
                    <span class="cd-quota-label">{{ $t('agentChat.monthUsed') }}</span>
                    <span class="cd-quota-val">{{ quota.monthUsed }} / {{ quota.monthlyLimit }}</span>
                  </div>
                  <div class="cd-quota-bar">
                    <div class="cd-quota-fill warning" :style="{ width: Math.min((quota.monthUsed / quota.monthlyLimit * 100), 100) + '%' }"></div>
                  </div>
                </div>
              </div>
              <div class="col-4">
                <div class="cd-quota-remaining">
                  <div class="cd-quota-remaining-label">{{ $t('agentChat.remaining') }}</div>
                  <div class="cd-quota-remaining-val">{{ Math.max(quota.monthlyLimit - quota.monthUsed, 0) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 빠른 액션 -->
        <div class="cd-panel-card">
          <div class="cd-panel-header">
            <i class="bi bi-lightning"></i> {{ $t('agentChat.quickActions') }}
          </div>
          <div class="cd-panel-body">
            <div class="cd-quick-actions">
              <button class="cd-action-btn danger" @click="clearChat">
                <i class="bi bi-trash"></i> {{ $t('agentChat.clearChat') }}
              </button>
              <button class="cd-action-btn secondary" @click="saveChat">
                <i class="bi bi-download"></i> {{ $t('agentChat.saveChat') }}
              </button>
            </div>
          </div>
        </div>
      </aside>

      <!-- 메인 채팅 영역 -->
      <div class="cd-chat-area" role="main">
        <!-- 채팅 헤더 (chat-detail 참고) -->
        <div class="cd-chat-header">
          <div class="cd-svc-strip-wrap">
            <label class="cd-strip-label"><i class="bi bi-cpu"></i> {{ $t('agentChat.selectAiServiceLabel') }}</label>
            <div class="cd-svc-strip">
              <button
                v-for="service in services"
                :key="service.serviceId"
                type="button"
                class="cd-strip-btn"
                :class="{ active: selectedService?.serviceId === service.serviceId }"
                @click="selectService(service)"
                :style="{ '--cd-svc-color': service.colorCode || '#4F46E5' }"
              >
                <i :class="service.iconClass || 'bi bi-cpu'"></i>
                <span>{{ service.serviceName }}</span>
              </button>
            </div>
          </div>
          <div class="cd-current-bar">
            <div class="cd-current-svc">
              <div class="cd-current-icon" :style="{ color: selectedService?.colorCode || '#4F46E5' }">
                <i :class="selectedService?.iconClass || 'bi bi-robot'"></i>
              </div>
              <div class="cd-current-meta">
                <span class="cd-current-name" :style="{ color: selectedService?.colorCode || '#4F46E5' }">
                  {{ selectedService?.serviceName || $t('agentChat.selectAiService') }}
                </span>
                <span class="cd-current-model">{{ modelSettings.model }}</span>
              </div>
            </div>
            <div class="cd-current-right">
              <span class="cd-connected-badge">
                <span class="cd-status-dot" :class="connectionStatus === 'online' ? 'online' : connectionStatus === 'checking' ? 'checking' : 'offline'"></span>
                {{ connectionStatus === 'online' ? $t('agentChat.connected') : connectionStatus === 'offline' ? $t('agentChat.disconnected') : $t('agentChat.checking') }}
              </span>
              <button type="button" class="cd-icon-btn" @click="showSettingsModal = true" :title="$t('agentChat.advancedSettings')">
                <i class="bi bi-gear"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- 메시지 영역 -->
        <div class="cd-messages" ref="chatBody">
            <!-- 날짜 구분선 -->
            <div class="cd-date-divider">
              <span>{{ new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' }) }}</span>
            </div>

            <!-- 메시지들 -->
            <template v-for="message in messages" :key="message.messageId || message.tempId">
              <div 
                :class="['cd-msg', message.role === 'user' ? 'cd-msg-user' : 'cd-msg-assistant']"
                :data-message-id="message.messageId || message.tempId"
              >
                <div v-if="message.role === 'assistant'" class="cd-msg-avatar" :style="{ backgroundColor: selectedService?.colorCode || '#6c757d' }">
                  <i :class="selectedService?.iconClass || 'bi bi-robot'"></i>
                </div>
                <div class="cd-msg-content">
                  <div class="cd-msg-header">
                    <strong>{{ message.role === 'user' ? $t('agentChat.me') : (selectedService?.serviceName || 'AI') }}</strong>
                    <span class="cd-msg-time">{{ formatTime(message.createdAt) }}</span>
                    <button
                      v-if="message.role === 'user' && !editingMessageId"
                      type="button"
                      class="cd-msg-edit-btn"
                      @click="startEditing(message)"
                      :title="$t('agentChat.edit')"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                  </div>
                  <!-- {{ $t('agentChat.attachments') }} 표시 -->
                  <div v-if="message.attachments && message.attachments.length > 0" class="message-attachments mb-2">
                    <div v-for="(attachment, idx) in message.attachments" :key="idx" class="mb-1">
                      <a v-if="attachment.type === 'file'" :href="getFileDownloadUrl(attachment.url)" target="_blank" class="badge bg-secondary text-decoration-none me-1" @click.prevent="downloadFile(attachment)">
                        <i class="bi bi-file-earmark me-1"></i>{{ attachment.name }}
                      </a>
                      <div v-else-if="attachment.type === 'image'" class="message-image-wrapper image-wrapper">
                        <img 
                          :src="getImageSource(attachment)" 
                          :alt="attachment.name" 
                          class="me-1 message-image image-preview-lg"
                          @error="handleImageError($event, attachment)"
                          @click="openImageModal(getImageSource(attachment), attachment.name)"
                          loading="lazy"
                        >
                        <div class="d-flex align-items-center gap-2 mt-1">
                          <div class="small text-muted text-break-all">{{ attachment.name }}</div>
                          <button 
                            class="btn btn-sm btn-outline-secondary btn-sm-icon" 
                            type="button"
                            @click.stop="downloadImage(attachment.url, attachment.name)"
                            :title="$t('agentChat.imageDownload')"
                          >
                            <i class="bi bi-download"></i>
                          </button>
                        </div>
                      </div>
                      <audio v-else-if="attachment.type === 'audio'" :src="getAttachmentUrl(attachment.url)" controls class="me-1 audio-control"></audio>
                    </div>
                  </div>
                  <!-- 편집 모드 -->
                  <div v-if="editingMessageId === (message.messageId || message.tempId)" class="message-editor mb-2">
                    <textarea 
                      v-model="editingContent"
                      class="form-control min-height-80"
                      rows="5"
                    ></textarea>
                    <div class="d-flex gap-2 mt-2">
                      <button @click="saveAndResend(message)" class="btn btn-primary btn-sm">
                        <i class="bi bi-check-lg me-1"></i>{{ $t('agentChat.saveAndResend') }}
                      </button>
                      <button @click="cancelEditing" class="btn btn-secondary btn-sm">
                        <i class="bi bi-x-lg me-1"></i>{{ $t('agentChat.cancel') }}
                      </button>
                    </div>
                  </div>
                  <!-- 일반 메시지 표시 (편집 모드가 아닐 때만) -->
                  <div
                    v-else-if="message.content && message.content.trim()"
                    class="cd-msg-bubble"
                    :class="{ 'cd-msg-streaming': message.isStreaming }"
                    v-html="formatMessage(message.content, message.messageId || message.tempId || '', message.citations)"
                    :style="message.role === 'user' ? {
                      display: 'block',
                      visibility: 'visible',
                      opacity: 1,
                      transform: 'none',
                    } : {
                      display: 'block',
                      visibility: 'visible',
                      opacity: 1,
                      transform: 'none',
                      color: '#1f2937'
                    }"
                  ></div>
                  <!-- 스트리밍 중인 assistant 메시지에 깜빡이는 cursor 표시 -->
                  <span v-if="message.isStreaming" class="cd-streaming-cursor" aria-hidden="true">▋</span>
                  <!-- Perplexity AI 출처 링크 -->
                  <div v-if="message.citations && message.citations.length > 0" class="message-citations mt-3" :id="`citations-${message.messageId || message.tempId}`">
                    <div class="border-top pt-2">
                      <small class="text-muted d-block mb-2">
                        <i class="bi bi-link-45deg me-1"></i>
                        <strong>{{ $t('agentChat.sources') }}</strong>
                      </small>
                      <div class="d-flex flex-wrap gap-2">
                        <a
                          v-for="(citation, index) in message.citations"
                          :key="index"
                          :id="`citation-${message.messageId || message.tempId}-${index + 1}`"
                          :href="citation"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="badge bg-secondary text-decoration-none citation-link"
                          :title="citation"
                        >
                          <i class="bi bi-box-arrow-up-right me-1"></i>
                          [{{ index + 1 }}] {{ citation.length > 50 ? citation.substring(0, 50) + '...' : citation }}
                        </a>
                      </div>
                    </div>
                  </div>
                  <!-- 모델명 · 토큰 수 표시 (assistant 메시지에만) -->
                  <div v-if="message.role === 'assistant' && (message.model || message.tokensUsed)" class="cd-msg-meta">
                    <span v-if="message.model" class="cd-msg-model">{{ message.model }}</span>
                    <span v-if="message.model && message.tokensUsed" class="cd-msg-meta-sep">·</span>
                    <span v-if="message.tokensUsed" class="cd-msg-tokens">{{ message.tokensUsed.toLocaleString() }} tokens</span>
                  </div>
                </div>
                <div v-if="message.role === 'user'" class="cd-msg-avatar user">
                  <i class="bi bi-person"></i>
                </div>
              </div>
            </template>

            <!-- 로딩 인디케이터 -->
            <div v-if="loading" class="cd-msg cd-msg-assistant">
              <div class="cd-msg-avatar" :style="{ backgroundColor: selectedService?.colorCode || '#6c757d' }">
                <i :class="selectedService?.iconClass || 'bi bi-robot'"></i>
              </div>
              <div class="cd-msg-content">
                <div class="cd-typing">
                  <span class="cd-typing-dot"></span>
                  <span class="cd-typing-dot"></span>
                  <span class="cd-typing-dot"></span>
                </div>
              </div>
            </div>
        </div>

        <!-- 제안 프롬프트 (처음에만 표시) - chat-detail 순서: messages 다음 -->
        <div class="cd-suggestions" v-if="messages.length <= 1">
          <div class="cd-suggest-label"><i class="bi bi-lightbulb"></i> {{ $t('chat.suggestedPrompts') }}</div>
          <div class="cd-suggest-chips">
              <button type="button" class="cd-suggest-chip" @click="useSuggestedPrompt($t('agentChat.suggestedPrompts.codeReview'))">
                <i class="bi bi-code"></i> {{ $t('chat.codeReview') }}
              </button>
              <button type="button" class="cd-suggest-chip" @click="useSuggestedPrompt($t('agentChat.suggestedPrompts.documentWriting'))">
                <i class="bi bi-file-text"></i> {{ $t('chat.documentWriting') }}
              </button>
              <button type="button" class="cd-suggest-chip" @click="useSuggestedPrompt($t('agentChat.suggestedPrompts.brainstorming'))">
                <i class="bi bi-lightbulb"></i> {{ $t('chat.brainstorming') }}
              </button>
              <button type="button" class="cd-suggest-chip" @click="useSuggestedPrompt($t('agentChat.suggestedPrompts.dataAnalysis'))">
                <i class="bi bi-graph-up"></i> {{ $t('chat.dataAnalysis') }}
              </button>
          </div>
        </div>

        <!-- 입력 영역 -->
        <div class="cd-input-area">
            <!-- 첨부 파일 미리보기 (chat-detail: cd-attachments) -->
            <div v-if="uploadedFiles.length > 0 || uploadedImages.length > 0 || uploadedAudio" class="cd-attachments" id="attachmentPreview">
              <small class="text-muted d-block mb-2">
                <i class="bi bi-paperclip"></i> <strong>{{ $t('agentChat.attachments') }} ({{ uploadedFiles.length + uploadedImages.length + (uploadedAudio ? 1 : 0) }}개):</strong>
              </small>
              
              <!-- 파일 목록 -->
              <div v-if="uploadedFiles.length > 0" class="mb-2">
                <div v-for="(file, index) in uploadedFiles" :key="index" class="d-flex align-items-center justify-content-between mb-1 p-2 bg-white rounded border">
                  <div class="d-flex align-items-center flex-grow-1">
                    <i class="bi bi-file-earmark me-2 icon-lg"></i>
                    <div class="flex-grow-1">
                      <div class="fw-bold">{{ file.file.name }}</div>
                      <small class="text-muted">{{ formatFileSize(file.file.size) }}</small>
                      <span v-if="file.parsedContent" class="badge bg-success ms-2">{{ $t('agentChat.parsed') }}</span>
                    </div>
                  </div>
                  <button class="btn btn-sm btn-link text-danger p-0 ms-2" @click="removeFile(index)" :title="$t('agentChat.remove')">
                    <i class="bi bi-x-circle icon-lg"></i>
                  </button>
                </div>
              </div>
              
              <!-- 이미지 미리보기 -->
              <div v-if="uploadedImages.length > 0" class="mb-2">
                <div v-for="(img, index) in uploadedImages" :key="index" class="d-inline-block me-2 mb-1 position-relative image-thumbnail-container">
                  <img :src="img.preview" :alt="img.file.name" class="image-preview">
                  <div class="small text-muted mt-1 image-thumbnail-name">{{ img.file.name }}</div>
                  <button class="btn btn-sm btn-link text-danger p-0 position-absolute top-0 end-0 icon-remove-btn" @click="removeImage(index)" :title="$t('agentChat.remove')">
                    <i class="bi bi-x-circle-fill icon-lg"></i>
                  </button>
                </div>
              </div>
              
              <!-- 오디오 미리보기 -->
              <div v-if="uploadedAudio" class="mb-2">
                <div class="d-flex align-items-center justify-content-between p-2 bg-white rounded border">
                  <div class="d-flex align-items-center flex-grow-1">
                    <i class="bi bi-file-earmark-music me-2 icon-lg"></i>
                    <div>
                      <div class="fw-bold">{{ uploadedAudio.file.name }}</div>
                      <small class="text-muted">{{ formatFileSize(uploadedAudio.file.size) }}</small>
                    </div>
                  </div>
                  <button class="btn btn-sm btn-link text-danger p-0 ms-2" @click="removeAudio" :title="$t('agentChat.remove')">
                    <i class="bi bi-x-circle icon-lg"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- 메시지 입력 폼 -->
            <form @submit.prevent="handleSubmit($event)">
              <div class="cd-input-row">
                <div class="cd-attach-btns">
                  <button class="cd-attach-btn" type="button" @click="attachFile" :title="$t('agentChat.attachFile')">
                    <i class="bi bi-paperclip"></i>
                  </button>
                  <button class="cd-attach-btn" type="button" @click="attachImage" :title="$t('agentChat.attachImage')">
                    <i class="bi bi-image"></i>
                  </button>
                  <button 
                    class="cd-attach-btn" 
                    type="button" 
                    @click="toggleAudioRecording" 
                    :class="{ recording: isRecording }"
                    :title="isRecording ? $t('agentChat.stopRecording') : $t('agentChat.recordAudio')"
                    :disabled="isRecordingAudio"
                  >
                    <i :class="isRecording ? 'bi bi-stop-fill' : 'bi bi-mic'"></i>
                    <span v-if="isRecording">{{ recordingTime }}</span>
                  </button>
                  <button 
                    class="cd-attach-btn" 
                    type="button" 
                    @click="attachAudioFile" 
                    :title="$t('agentChat.selectAudioFile')"
                    :disabled="isRecording"
                  >
                    <i class="bi bi-file-earmark-music"></i>
                  </button>
                </div>
                <input type="file" ref="fileInput" class="input-hidden" accept=".pdf,.txt,.csv,.xls,.xlsx,.doc,.docx,.hwp,.hwpx,.ppt,.pptx" @change="handleFileSelect" multiple>
                <input type="file" ref="imageInput" class="input-hidden" accept="image/*" @change="handleImageSelect" multiple>
                <input type="file" ref="audioInput" class="input-hidden" accept="audio/*,video/*" @change="handleAudioSelect">
                <textarea 
                  class="cd-textarea" 
                  v-model="inputMessage"
                  :placeholder="$t('chat.inputPlaceholder') + ' (' + $t('agentChat.shiftEnterNewline') + ')'" 
                  rows="1"
                  @keydown.enter.exact.prevent="handleSubmit($event)"
                  @keydown.shift.enter.exact="() => {}"
                  @input="(e) => { const target = e.target as HTMLTextAreaElement; target.style.height = 'auto'; target.style.height = Math.min(target.scrollHeight, 100) + 'px'; }"
                ></textarea>
                <!-- 스트리밍 중에는 "응답 중단" 버튼으로 토글, 아니면 기존 전송 버튼 -->
                <button
                  v-if="streamAbortController"
                  class="cd-send-btn"
                  type="button"
                  @click="stopStreaming"
                  :title="$t('agentChat.streamingStop')"
                >
                  <i class="bi bi-stop-circle"></i> {{ $t('agentChat.streamingStop') }}
                </button>
                <button v-else class="cd-send-btn" type="submit" @click="handleSubmit($event)">
                  <i class="bi bi-send"></i> {{ $t('agentChat.send') }}
                </button>
              </div>
            </form>

            <!-- Footer info row (chat-detail) -->
            <div class="cd-input-footer">
              <span class="cd-footer-svc" v-if="selectedService">
                <i class="bi bi-check-circle" style="color:var(--ai-success);"></i>
                {{ $t('agentChat.connectionStatus') }} <strong>{{ selectedService.serviceName }}</strong> (<span>{{ modelSettings.model }}</span>)
              </span>
              <span class="cd-footer-hint">{{ $t('agentChat.shiftEnterHint') }}</span>
            </div>

            <!-- 예제 프롬프트 (이미지 생성 서비스일 때만 표시) -->
            <div class="mt-4 mb-custom" v-if="selectedService && (selectedService.serviceType === 'ImageGeneration' || selectedService.serviceType === 'Both')">
              <small class="text-muted d-block mb-2">
                <i class="bi bi-lightbulb-fill me-1"></i>{{ $t('agentChat.examplePrompts') }}
              </small>
              
              <!-- 카테고리 필터 -->
              <div v-if="!loadingExamplePrompts && examplePrompts.length > 0" class="mb-3">
                <div class="d-flex flex-wrap gap-2">
                  <button
                    :class="['btn', 'btn-sm', selectedCategory === null ? 'btn-primary' : 'btn-outline-secondary']"
                    @click="selectedCategory = null"
                  >
                    <i class="bi bi-grid me-1"></i>{{ $t('agentChat.all') }}
                  </button>
                  <button
                    v-for="category in availableCategories"
                    :key="category"
                    :class="['btn', 'btn-sm', selectedCategory === category ? 'btn-primary' : 'btn-outline-secondary']"
                    @click="selectedCategory = category"
                  >
                    {{ category }}
                  </button>
                </div>
              </div>
              
              <div v-if="loadingExamplePrompts" class="text-center py-2">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                  <span class="visually-hidden">Loading...</span>
                </div>
              </div>
              <div v-else-if="filteredExamplePrompts.length > 0" class="example-prompts-list">
                <div 
                  v-for="example in filteredExamplePrompts" 
                  :key="example.examplePromptId"
                  class="example-prompt-item"
                >
                  <div 
                    class="card h-100 example-prompt-card transition-all"
                    @click="useExamplePrompt(example.prompt)"
                    @mouseenter="(e) => { const target = e.currentTarget as HTMLElement; if (target) target.style.transform = 'translateY(-2px)' }"
                    @mouseleave="(e) => { const target = e.currentTarget as HTMLElement; if (target) target.style.transform = 'translateY(0)' }"
                  >
                    <div class="card-body p-2">
                      <div class="d-flex align-items-start mb-2">
                        <i 
                          :class="[example.iconClass || 'bi bi-image', 'me-2', 'icon-lg', 'text-primary']"
                        ></i>
                        <div class="flex-grow-1">
                          <h6 class="card-title mb-1 card-title-sm">{{ example.title }}</h6>
                          <p class="card-text small text-muted mb-2 card-text-sm">
                            {{ example.description || example.prompt.substring(0, 60) + '...' }}
                          </p>
                        </div>
                      </div>
                      <div class="d-flex align-items-center justify-content-between gap-2">
                        <span v-if="example.category" class="badge bg-secondary badge-xs">
                          {{ example.category }}
                        </span>
                        <button 
                          class="btn btn-sm btn-outline-primary flex-shrink-0"
                          @click.stop="useExamplePrompt(example.prompt)"
                        >
                          <i class="bi bi-arrow-right-circle me-1"></i>{{ $t('agentChat.useExamplePrompt') }}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else-if="!loadingExamplePrompts" class="example-prompts-empty">
                <p class="text-muted small mb-0">{{ $t('agentChat.noExamplePrompts') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  <!-- 모달들 (Teleport로 body에 렌더링) -->
  <Teleport to="body">
    <div :class="['modal', 'fade', { show: showSettingsModal, 'modal-show': showSettingsModal, 'modal-hide': !showSettingsModal }]" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-gear"></i> {{ $t('agentChat.advancedSettings') }}</h5>
            <button type="button" class="btn-close" @click="showSettingsModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">시스템 프롬프트</label>
              <textarea class="form-control" rows="4" v-model="advancedSettings.systemPrompt" :placeholder="$t('agentChat.systemPromptPlaceholder')"></textarea>
              <!-- 응답 스타일 빠른 적용 -->
              <div class="d-flex flex-wrap gap-1 mt-2">
                <small class="text-muted me-1 align-self-center">스타일:</small>
                <button type="button" class="btn btn-sm"
                  :class="chatActiveStyle === 'professional' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="applyChatStyle('professional')" title="마크다운, 이모지 없음, 전문적 문체">
                  <i class="bi bi-briefcase"></i> 전문적
                </button>
                <button type="button" class="btn btn-sm"
                  :class="chatActiveStyle === 'friendly' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="applyChatStyle('friendly')" title="이모지 포함, 친근한 설명">
                  <i class="bi bi-emoji-smile"></i> 친근·이모지
                </button>
                <button type="button" class="btn btn-sm"
                  :class="chatActiveStyle === 'concise' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="applyChatStyle('concise')" title="3~5문장 핵심만">
                  <i class="bi bi-lightning"></i> 간결
                </button>
                <button type="button" class="btn btn-sm"
                  :class="chatActiveStyle === 'stepbystep' ? 'btn-primary' : 'btn-outline-secondary'"
                  @click="applyChatStyle('stepbystep')" title="단계별 번호 목록">
                  <i class="bi bi-list-ol"></i> 단계별
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger"
                  v-if="chatActiveStyle"
                  @click="removeChatStyle()">
                  <i class="bi bi-x"></i>
                </button>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ $t('agentChat.responseFormat') }}</label>
              <select class="form-select" v-model="advancedSettings.responseFormat">
                <option value="text">{{ $t('agentChat.responseFormatText') }}</option>
                <option value="markdown">{{ $t('agentChat.responseFormatMarkdown') }}</option>
                <option value="json">{{ $t('agentChat.responseFormatJson') }}</option>
                <option value="code">{{ $t('agentChat.responseFormatCode') }}</option>
              </select>
            </div>
            <div class="mb-3">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" v-model="advancedSettings.saveHistory" id="save-history">
                <label class="form-check-label" for="save-history">
                  {{ $t('agentChat.saveHistory') }}
                </label>
              </div>
            </div>
            <div class="mb-3">
              <div class="form-check">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  v-model="enableWebSearch" 
                  id="enableWebSearchModal"
                  :disabled="
                    selectedService?.serviceCode?.toLowerCase() !== 'chatgpt' && 
                    selectedService?.serviceCode?.toLowerCase() !== 'openai' &&
                    selectedService?.serviceType !== 'ImageGeneration' &&
                    selectedService?.serviceType !== 'Both' &&
                    !(modelSettings.model?.toLowerCase().includes('gemini') && modelSettings.model?.toLowerCase().includes('image'))
                  "
                >
                <label class="form-check-label" for="enableWebSearchModal">
                  <i class="bi bi-search me-1"></i> {{ $t('agentChat.webSearchTavily') }}
                  <small class="text-muted d-block mt-1" v-if="
                    selectedService?.serviceCode?.toLowerCase() !== 'chatgpt' && 
                    selectedService?.serviceCode?.toLowerCase() !== 'openai' &&
                    selectedService?.serviceType !== 'ImageGeneration' &&
                    selectedService?.serviceType !== 'Both' &&
                    !(modelSettings.model?.toLowerCase().includes('gemini') && modelSettings.model?.toLowerCase().includes('image'))
                  ">
                    {{ $t('agentChat.webSearchServiceHint') }}
                  </small>
                  <small class="text-muted d-block mt-1" v-else>
                    <span v-if="selectedService?.serviceType === 'ImageGeneration' || selectedService?.serviceType === 'Both'">
                      {{ $t('agentChat.webSearchImageDesc') }}
                    </span>
                    <span v-else>
                      {{ $t('agentChat.webSearchTextDesc') }}
                    </span>
                  </small>
                </label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showSettingsModal = false">{{ $t('agentChat.close') }}</button>
            <button type="button" class="btn btn-primary" @click="showSettingsModal = false">{{ $t('agentChat.apply') }}</button>
          </div>
        </div>
      </div>
    </div>
    <div :class="['modal-backdrop', 'fade', { show: showSettingsModal }]" v-if="showSettingsModal"></div>
    
    <!-- 이미지 확대 모달 -->
    <div 
      v-if="showImageModal" 
      class="modal fade show modal-overlay"
      @click.self="closeImageModal"
    >
      <div class="modal-dialog modal-dialog-centered modal-lg modal-lg-custom">
        <div class="modal-content modal-content-transparent">
          <div class="modal-header modal-header-no-border">
            <h5 class="modal-title text-white">{{ imageModalTitle }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="closeImageModal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center modal-body-no-padding">
            <img 
              :src="imageModalSrc" 
              :alt="imageModalTitle"
              class="modal-image"
              @error="imageModalSrc = ''"
            >
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import { streamChat } from '@/services/sseClient'
import type { AgentDto, ExamplePromptDto } from '@/types'
import './AgentChat.css'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
// Prism 언어 지원
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-java'
import 'prismjs/components/prism-csharp'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-css'
import 'prismjs/components/prism-markup'

interface ApiService {
  serviceId: number
  serviceCode: string
  serviceName: string
  description?: string
  iconClass?: string
  colorCode?: string
  serviceType?: 'Chat' | 'ImageGeneration' | 'Both'
}

interface MessageContent {
  type: 'text' | 'image_url' | 'audio_url' | 'file'
  text?: string
  imageUrl?: string
  audioUrl?: string
  fileUrl?: string
  fileName?: string
}

interface Message {
  messageId?: number
  tempId?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  contents?: MessageContent[] // 멀티모달 콘텐츠
  createdAt: string | Date
  citations?: string[] // Perplexity AI citations
  attachments?: Array<{
    type: string
    url: string
    name: string
    preview?: string // Base64 preview for images
  }>
  isEditing?: boolean // 편집 모드 여부
  model?: string // 응답에 사용된 모델명
  tokensUsed?: number // 응답 토큰 수
  // 스트리밍 채팅 상태 (Phase 3.5b 신규)
  isStreaming?: boolean // SSE 스트리밍 진행 중이면 true → UI에 cursor blink 등 표시
  cost?: number // usage 청크 도착 시 갱신
  errorCode?: string // SSE error 청크의 code (예: BANNED_WORD_DETECTED)
}

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const agentId = computed(() => route.params.id ? parseInt(route.params.id as string) : null)

const services = ref<ApiService[]>([])
const selectedService = ref<ApiService | null>(null)
const agent = ref<AgentDto | null>(null)
const messages = ref<Message[]>([])
const inputMessage = ref('')
const loading = ref(false)
const currentConversationId = ref<number | null>(null) // 현재 대화 ID 추적
const connectionStatus = ref<'online' | 'offline' | 'checking'>('checking')
const chatBody = ref<HTMLElement | null>(null)
let statusCheckInterval: number | null = null
const fileInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const audioInput = ref<HTMLInputElement | null>(null)
const showSettingsModal = ref(false)
const uploadedFiles = ref<Array<{ file: File; type: string; url?: string; parsedContent?: string }>>([])
const uploadedImages = ref<Array<{ file: File; url?: string; preview?: string; base64?: string }>>([])
const uploadedAudio = ref<{ file: File; url?: string } | null>(null)

// 음성 녹음 관련
const isRecording = ref(false)
const isRecordingAudio = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const recordingTime = ref('00:00')
const recordingTimer = ref<number | null>(null)
const recordingStartTime = ref<number>(0)
const mediaStream = ref<MediaStream | null>(null)

// 전송 버튼 비활성화 여부 (명시적 boolean ref)
const isButtonDisabled = ref(false)

const modelSettings = ref({
  model: 'gpt-4-turbo',
  temperature: 70,
  maxTokens: 4096
})

const enableWebSearch = ref(false)
const enableRag = ref(false)
const enableDeepResearch = ref(false) // 심층 리서치: 다중 웹 검색 + RAG 통합 분석
const enableDeepThinking = ref(false) // 더 오래 생각하기: Chain-of-Thought 프롬프팅
const thinkingMode = ref<string>('chain-of-thought') // 'chain-of-thought', 'step-by-step'
const responseLanguage = ref<string>('auto') // 'auto', 'ko', 'en'

// SSE 스트리밍 (Phase 3.5b)
// 기본 활성화. 백엔드 /api/chat/send/stream 미배포 환경 대비를 위해 사용자가 토글로 끌 수 있다(Settings 모달에서 노출).
// false면 기존 비스트리밍 분기로 폴백.
const useStreaming = ref(true)
// 진행 중 스트리밍을 사용자가 중단할 수 있도록 AbortController 보관
const streamAbortController = ref<AbortController | null>(null)

// Knowledge Base 문서 선택 UI 는 Phase 2 자체 KB drop (ADR-2) 으로 제거됨.
// 운영자가 Agent.KnowledgeBaseSource="DocUtil" + Agent.KnowledgeBaseRef(collection ID) 로 화이트리스트를 결정하므로,
// 사용자 채팅 화면에서는 EnableRag 토글로 대화 단위 on/off 만 제어한다.

// 편집 공간 관련
const editingMessageId = ref<string | number | null>(null)
const editingContent = ref('')

const quota = ref({
  todayUsed: 0,
  dailyLimit: 100,
  monthUsed: 0,
  monthlyLimit: 1000
})

const examplePrompts = ref<ExamplePromptDto[]>([])
const loadingExamplePrompts = ref(false)
const selectedCategory = ref<string | null>(null) // null = 전체
const showImageModal = ref(false)
const imageModalSrc = ref('')
const imageModalTitle = ref('')

const stats = ref({
  tokensUsed: 0,
  cost: 0
})

// 서비스별 사용 가능한 모델 목록 (API에서 동적으로 가져옴)
const availableModels = ref<string[]>(['gpt-4-turbo'])

// 모델 목록 로드
const loadModels = async (serviceId: number) => {
  try {
    console.log('[loadModels] Loading models for service:', serviceId)
    const response = await api.get<string[]>(`/apiservices/${serviceId}/models`)
    if (response.data && response.data.length > 0) {
      availableModels.value = response.data
      console.log('[loadModels] Models loaded:', availableModels.value)
      
      // 현재 모델이 새 목록에 없으면 첫 번째 모델로 변경
      if (!availableModels.value.includes(modelSettings.value.model)) {
        modelSettings.value.model = availableModels.value[0]
        console.log('[loadModels] Model changed to:', modelSettings.value.model)
      }
      
      // 이미지가 첨부되어 있고 Vision을 지원하는 모델이 선택되지 않았으면 자동 변경
      if (uploadedImages.value.length > 0) {
        const visionModels = availableModels.value.filter(m => 
          m.toLowerCase().includes('vision') || 
          m.toLowerCase().includes('gpt-4-turbo') ||
          m.toLowerCase().includes('gpt-4o')
        )
        if (visionModels.length > 0 && !visionModels.includes(modelSettings.value.model)) {
          const recommendedModel = visionModels.find(m => m.toLowerCase().includes('turbo')) || visionModels[0]
          console.log('[loadModels] Image detected, changing to vision model:', recommendedModel)
          modelSettings.value.model = recommendedModel
        }
      }
    } else {
      console.warn('[loadModels] No models returned from API')
    }
  } catch (error: any) {
    console.error('[loadModels] Error loading models:', error)
    // 에러 발생 시 기본 모델 목록 유지
  }
}

// 전송 버튼 비활성화 여부 업데이트
watch([loading, selectedService], ([newLoading, newService]) => {
  isButtonDisabled.value = newLoading || !newService
}, { immediate: true })

// 할당량 정보 로드
const loadQuota = async () => {
  if (!selectedService.value) return
  
  try {
    const response = await api.get(`/quota/my/${selectedService.value.serviceId}`)
    if (response.data) {
      quota.value = {
        todayUsed: response.data.todayUsage || response.data.CurrentUsage || 0,
        dailyLimit: response.data.dailyLimit || response.data.DailyLimit || 100,
        monthUsed: response.data.currentUsage || response.data.CurrentUsage || 0,
        monthlyLimit: response.data.monthlyLimit || response.data.MonthlyLimit || 1000
      }
      console.log('[loadQuota] Quota loaded:', quota.value, 'Response:', response.data)
    }
  } catch (error: any) {
    console.error('[loadQuota] Error loading quota:', error)
    // API 엔드포인트가 없거나 할당량이 없는 경우 기본값 사용
    if (error.response?.status === 404) {
      quota.value = {
        todayUsed: 0,
        dailyLimit: 100,
        monthUsed: 0,
        monthlyLimit: 1000
      }
    }
  }
}

watch(() => selectedService.value?.serviceId, () => {
  if (selectedService.value) {
    loadQuota()
    loadExamplePrompts()
  }
})

// 모델이 변경되면 예제 프롬프트 다시 로드
watch(() => modelSettings.value.model, () => {
  if (selectedService.value) {
    loadExamplePrompts()
  }
})

// loadDocuments / onRagToggle / toggleDocument 함수는 Phase 2 자체 KB drop (ADR-2) 으로 제거됨.
// `/api/knowledgebase` 백엔드 컨트롤러가 `7f1a9ae` 에서 완전 제거되어 SPA fallback HTML 을 200 으로 반환하던 dead code 였음.

// ── AgentChat 응답 스타일 ──────────────────────────────────────────────────
const chatStyleSnippets: Record<string, string> = {
  professional: `\n\n## 응답 형식\n- 마크다운(##, **굵게**, 표, 코드블록)을 적극 활용하세요.\n- 핵심 정보는 표나 목록으로 구조화하세요.\n- 이모지는 사용하지 마세요.\n- 전문적이고 간결한 문체를 유지하세요.`,
  friendly: `\n\n## 응답 형식\n- 섹션 제목 앞에 관련 이모지를 1개 붙이세요. (예: ## 📌 핵심 개념)\n- ✅ 좋은 예, ❌ 나쁜 예, ⚠️ 주의, 💡 팁 이모지를 상황에 맞게 사용하세요.\n- 친근하고 대화체로 쉽게 설명하세요.`,
  concise: `\n\n## 응답 형식\n- 답변은 3~5문장 이내로 핵심만 전달하세요.\n- 서론 없이 바로 본론으로 시작하세요.\n- 불필요한 예의 표현은 생략하세요.`,
  stepbystep: `\n\n## 응답 형식\n- 반드시 번호 목록(1. 2. 3.)으로 단계별로 설명하세요.\n- 각 단계에 구체적인 예시를 포함하세요.\n- 마지막에 전체 흐름을 한 줄로 요약하세요.`
}
const chatActiveStyle = ref('friendly')

const applyChatStyle = (key: string) => {
  let base = advancedSettings.value.systemPrompt
    .replace(/\n*## 응답 형식[\s\S]*$/m, '')
    .replace(/\n*## Response Guidelines[\s\S]*$/m, '')
    .trimEnd()
  advancedSettings.value.systemPrompt = base + (chatStyleSnippets[key] ?? '')
  chatActiveStyle.value = key
}

const removeChatStyle = () => {
  advancedSettings.value.systemPrompt = advancedSettings.value.systemPrompt
    .replace(/\n*## 응답 형식[\s\S]*$/m, '')
    .replace(/\n*## Response Guidelines[\s\S]*$/m, '')
    .trimEnd()
  chatActiveStyle.value = ''
}

const advancedSettings = ref({
  systemPrompt: t('agentChat.defaultSystemPrompt') + chatStyleSnippets['friendly'],
  responseFormat: 'markdown',
  // 트랙 #97-post8 (2026-05-18) — 결함 G fix: streamResponse 기본값 true 전환.
  //   기존 결함: 초기값 false → 비스트리밍 = 응답 전체 대기 = 10~20초 (GPT web 3초 대비 큰 격차).
  //   "중복 응답 방지" 회피용으로 false 였으나, fix-A(sseClient 401 처리 부재) + post7(신규 conv race)
  //   로 원인 결함 2건이 모두 해소되었으므로 streaming 기본 활성화가 안전.
  //   사용자는 좌측 설정 토글로 비스트리밍 폴백을 여전히 선택 가능.
  streamResponse: true,
  saveHistory: true
})

const loadAgent = async () => {
  if (!agentId.value) return
  
  try {
    const response = await api.get<AgentDto>(`/agents/${agentId.value}`)
    agent.value = response.data
    
    // Agent 설정 적용
    if (agent.value.systemPrompt) {
      advancedSettings.value.systemPrompt = agent.value.systemPrompt
    }
    if (agent.value.temperature) {
      modelSettings.value.temperature = Math.round(agent.value.temperature * 100)
    }
    if (agent.value.maxTokens) {
      modelSettings.value.maxTokens = agent.value.maxTokens
    }
    if (agent.value.defaultModel) {
      modelSettings.value.model = agent.value.defaultModel
    }
    
    // Agent의 RAG 설정 적용 — Agent.EnableRag 만 토글에 반영.
    // 문서 목록 fetch 는 Phase 2 자체 KB drop (ADR-2) 으로 제거됨.
    if (agent.value.enableRag !== undefined) {
      enableRag.value = agent.value.enableRag
    }
    
    // Agent의 서비스 찾기
    if (services.value.length > 0 && agent.value) {
      const service = services.value.find(s => s.serviceId === agent.value!.serviceId)
      if (service) {
        await selectService(service)
        // 서비스 선택 후에도 Agent의 모델이 유효하면 유지
        if (agent.value!.defaultModel && availableModels.value.includes(agent.value!.defaultModel)) {
          modelSettings.value.model = agent.value!.defaultModel
        }
      }
    }
  } catch (error: any) {
    // 404: Agent가 없거나 비활성화됨 → Agent 선택 페이지로 이동
    if (error?.response?.status === 404) {
      console.warn(`Agent ${agentId.value} not found, redirecting to agent list`)
      router.push('/agents/chat')
    } else {
      console.error('Error loading agent:', error)
    }
  }
}

const loadServices = async () => {
  try {
    const response = await api.get<ApiService[]>('/apiservices', { params: { serviceType: 'Chat' } })
    services.value = response.data || []
    
    // Agent가 있으면 로드 (Agent가 서비스를 결정함)
    if (agentId.value) {
      await loadAgent()
    } else if (services.value.length > 0 && !selectedService.value) {
      // Agent가 없으면 첫 번째 서비스 선택
      await selectService(services.value[0])
    }
  } catch (error: any) {
    console.error('Error loading services:', error)
    alert(t('common.error') + ': ' + (error.response?.data?.message || error.message))
  }
}

// 연결 상태 확인
const checkConnectionStatus = async () => {
  if (!selectedService.value) {
    connectionStatus.value = 'offline'
    return
  }
  
  try {
    connectionStatus.value = 'checking'
    // 실제 API 연결 상태 확인 엔드포인트 호출
    const response = await api.get(`/apiservices/${selectedService.value.serviceId}/connection-status`, {
      timeout: 5000 // 5초 타임아웃
    })
    
    if (response.data && response.data.connected === true) {
      connectionStatus.value = 'online'
    } else {
      connectionStatus.value = 'offline'
    }
  } catch (error: any) {
    console.warn('Connection check failed:', error)
    connectionStatus.value = 'offline'
  }
}

const selectService = async (service: ApiService) => {
  console.log('[selectService] Service selected:', service)
  const previousService = selectedService.value
  
  // 서비스 변경 시 대화 ID 초기화 (새 대화 시작)
  if (previousService?.serviceId !== service.serviceId) {
    currentConversationId.value = null
  }
  
  selectedService.value = service
  
  // 연결 상태 확인
  await checkConnectionStatus()
  
  // 모델 목록 동적으로 로드
  await loadModels(service.serviceId)
  await loadQuota()
  
  // 예제 프롬프트 로드
  await loadExamplePrompts()
  
  // 서비스가 변경된 경우 모델 자동 업데이트
  if (previousService?.serviceId !== service.serviceId) {
    console.log('[selectService] Service changed, updating model')
    
    // Agent의 모델이 있고 새 서비스에도 유효한 경우 유지
    if (agent.value?.defaultModel && availableModels.value.includes(agent.value.defaultModel)) {
      console.log('[selectService] Keeping agent model:', agent.value.defaultModel)
      modelSettings.value.model = agent.value.defaultModel
      return
    }
    
    // 현재 모델이 새 서비스의 모델 목록에 없으면 첫 번째 모델로 변경
    const currentModel = modelSettings.value.model
    if (!availableModels.value.includes(currentModel) && availableModels.value.length > 0) {
      console.log('[selectService] Changing model from', currentModel, 'to', availableModels.value[0])
      modelSettings.value.model = availableModels.value[0]
    } else {
      console.log('[selectService] Current model is valid, keeping:', currentModel)
    }
  }
}

// 전송 핸들러 (disabled 체크 포함)
const handleSubmit = (e?: Event | KeyboardEvent) => {
  if (e) {
    e.preventDefault()
    e.stopPropagation()
  }
  if (isButtonDisabled.value) {
    return false
  }
  sendMessage()
}

const sendMessage = async () => {
  // 중복 전송 방지: 이미 로딩 중이면 무시
  if (loading.value) {
    console.warn('[sendMessage] Already sending message, ignoring duplicate request')
    return
  }
  
  // 입력 검증
  if (!selectedService.value) {
    alert(t('agentChat.selectServiceFirst'))
    return
  }

  // 첨부 파일이 있는지 확인
  const hasAttachments = uploadedFiles.value.length > 0 || uploadedImages.value.length > 0 || uploadedAudio.value !== null
  
  if (!inputMessage.value.trim() && !hasAttachments) {
    alert(t('agentChat.enterMessage'))
    return
  }
  
  if (!selectedService.value || loading.value) return

  const messageText = inputMessage.value
  const attachments: Array<{ type: string; url: string; name: string; preview?: string }> = []
  
  // 첨부 파일 정보 수집 (preview 포함)
  uploadedFiles.value.forEach(f => {
    if (f.url) attachments.push({ type: 'file', url: f.url, name: f.file.name })
  })
  uploadedImages.value.forEach(img => {
    // 이미지는 preview (Base64)를 우선 저장하여 서버 URL 문제 시에도 표시 가능하도록 함
    attachments.push({ 
      type: 'image', 
      url: img.url || '', 
      name: img.file.name,
      preview: img.preview // Base64 preview 저장
    })
  })
  if (uploadedAudio.value?.url) {
    attachments.push({ type: 'audio', url: uploadedAudio.value.url, name: uploadedAudio.value.file.name })
  }

  // 사용자 메시지 표시 (텍스트와 첨부파일을 함께 하나의 메시지로 표시)
  // 첨부파일만 있는 경우 빈 텍스트로 표시 (첨부파일만 보이도록)
  const userMessage: Message = {
    tempId: `temp-${Date.now()}`,
    role: 'user',
    content: messageText.trim(), // 첨부파일만 있으면 빈 문자열
    attachments: attachments.length > 0 ? attachments : undefined,
    createdAt: new Date()
  }

  messages.value.push(userMessage)
  
  // 환영 메시지 제거 (사용자가 메시지를 보내면 환영 메시지 제거)
  const welcomeMessageIndex = messages.value.findIndex(m => m.tempId === 'welcome')
  if (welcomeMessageIndex !== -1) {
    messages.value.splice(welcomeMessageIndex, 1)
  }
  inputMessage.value = ''
  loading.value = true
  
  // 첨부 파일 초기화는 전송 성공 후

  try {
    await scrollToBottom()

    // 시스템 메시지가 이미 있으면 제거하고 새로 추가
    const userMessages = messages.value.filter(m => m.role === 'user')
    const assistantMessages = messages.value.filter(m => m.role === 'assistant')
    
    // 이전 대화 이력을 포함한 메시지 배열 구성 (멀티모달 지원)
    const requestMessages: Array<{ role: string; content?: string; contents?: Array<{ type: string; text?: string; image_url?: { url: string }; audio_url?: string; file_url?: string; file_name?: string }> }> = []
    
    // 시스템 프롬프트 추가 (최상단) - Agent의 systemPrompt가 있으면 사용, 없으면 기본값
    const systemPrompt = agent.value?.systemPrompt || advancedSettings.value.systemPrompt
    if (systemPrompt) {
      requestMessages.push({
        role: 'system',
        content: systemPrompt
      })
    }
    
    // 이전 대화 이력 추가 (user-assistant 페어)
    // 마지막 메시지(userMessage)를 제외한 이전 메시지들만 추가
    // 직전 2턴은 멀티모달(.contents) 유지, 나머지는 텍스트만 전달 (토큰 절약)
    const recentTurns = 2
    for (let i = 0; i < userMessages.length - 1; i++) {
      const uMsg = userMessages[i]
      const keepMultimodal = i >= userMessages.length - 1 - recentTurns
      if (uMsg) {
        if (keepMultimodal && uMsg.contents && uMsg.contents.length > 0) {
          requestMessages.push({ role: 'user', contents: uMsg.contents })
        } else if (uMsg.content) {
          requestMessages.push({ role: 'user', content: uMsg.content })
        }
      }
      if (assistantMessages[i] && assistantMessages[i].content) {
        requestMessages.push({
          role: 'assistant',
          content: assistantMessages[i].content
        })
      }
    }
    
    // 현재 메시지 추가 (멀티모달 지원)
    const messageContents: Array<{ type: string; text?: string; image_url?: { url: string }; audio_url?: string; file_url?: string; file_name?: string }> = []
    
    // 텍스트 콘텐츠 추가
    if (messageText.trim()) {
      messageContents.push({
        type: 'text',
        text: messageText.trim()
      })
    }
    
    // 이미지 콘텐츠 추가 (OpenAI Vision API는 Base64를 지원)
    for (const img of uploadedImages.value) {
      if (img.base64) {
        // Base64 인코딩된 이미지를 data URL 형식으로 전송
        // MIME 타입 결정 (이미지 타입에 따라)
        const mimeType = img.file.type || 'image/jpeg'
        const dataUrl = `data:${mimeType};base64,${img.base64}`
        console.log('[sendMessage] Adding image with Base64:', {
          fileName: img.file.name,
          mimeType: mimeType,
          base64Length: img.base64.length,
          dataUrlLength: dataUrl.length,
          dataUrlPrefix: dataUrl.substring(0, 50) + '...',
          dataUrlEnd: '...' + dataUrl.substring(Math.max(0, dataUrl.length - 20))
        })
        
        // Base64 data URL 형식 검증
        if (!dataUrl.startsWith('data:')) {
          console.error('[sendMessage] Invalid data URL format:', dataUrl.substring(0, 100))
          throw new Error(t('agentChat.invalidImageDataUrl'))
        }
        
        messageContents.push({
          type: 'image_url',
          image_url: { url: dataUrl }
        })
      } else {
        console.warn('[sendMessage] Image has no base64, skipping (Base64 required for OpenAI Vision API):', img)
      }
    }
    
    // 오디오 콘텐츠 추가
    if (uploadedAudio.value?.url) {
      const audioUrl = getFileUrl(uploadedAudio.value.url)
      messageContents.push({
        type: 'audio_url',
        audio_url: audioUrl
      })
    }
    
    // 파일 콘텐츠 추가 (파싱된 텍스트 포함)
    // 파싱된 파일 내용을 수집하여 텍스트로 통합
    const parsedFileTexts: string[] = []
    for (const file of uploadedFiles.value) {
      if (file.url && file.parsedContent && file.parsedContent.trim()) {
        // 파싱된 내용이 있으면 텍스트로 추가 (실제 파일 내용 전달)
        parsedFileTexts.push(`[파일: ${file.file.name}]\n${file.parsedContent}`)
      }
    }
    
    // 사용자 입력 텍스트와 파싱된 파일 내용을 결합
    const allTextParts: string[] = []
    if (messageText.trim()) {
      allTextParts.push(messageText.trim())
    }
    if (parsedFileTexts.length > 0) {
      allTextParts.push(...parsedFileTexts)
    }
    
    // 통합된 텍스트가 있으면 메시지 콘텐츠에 추가
    if (allTextParts.length > 0) {
      messageContents.push({
        type: 'text',
        text: allTextParts.join('\n\n')
      })
    }
    
    if (messageContents.length > 0) {
      // 멀티모달 콘텐츠를 API 형식으로 변환
      const apiMessageContents = messageContents.map(c => {
        if (c.type === 'text' && c.text) {
          return { type: 'text', text: c.text }
        } else if (c.type === 'image_url' && c.image_url?.url) {
          // Base64 data URL이 이미 포함되어 있음
          return { type: 'image_url', imageUrl: c.image_url.url }
        } else if (c.type === 'audio_url' && c.audio_url) {
          return { type: 'audio_url', audioUrl: c.audio_url }
        } else if (c.type === 'file' && c.file_url) {
          return { type: 'file', fileUrl: c.file_url, fileName: c.file_name || '' }
        }
        return null
      }).filter(c => c !== null && (c.text !== undefined || c.imageUrl !== undefined || c.audioUrl !== undefined || c.fileUrl !== undefined)) as { type: string; text?: string; imageUrl?: string; audioUrl?: string; fileUrl?: string; fileName?: string }[]
      
      console.log('[sendMessage] Final apiMessageContents:', apiMessageContents.map(c => ({
        type: c.type,
        hasText: !!c.text,
        textPreview: c.text ? (c.text.substring(0, 200) + (c.text.length > 200 ? '...' : '')) : undefined,
        hasImageUrl: !!c.imageUrl,
        imageUrlPreview: c.imageUrl ? (c.imageUrl.substring(0, 50) + '...') : undefined
      })))
      
      // 필터링 후 유효한 콘텐츠가 없는 경우 처리 (이론적으로는 발생하지 않아야 함)
      if (apiMessageContents.length === 0) {
        requestMessages.push({
          role: 'user',
          content: t('agentChat.message')
        })
      } else if (apiMessageContents.length === 1 && apiMessageContents[0].type === 'text' && apiMessageContents[0].text) {
        // 단순 텍스트인 경우 content만 사용 (Contents는 전송하지 않음)
        requestMessages.push({
          role: 'user',
          content: apiMessageContents[0].text
        })
      } else {
        // 멀티모달 콘텐츠인 경우 contents 배열 사용, Content도 함께 전송 (필수)
        // 텍스트가 없으면 빈 문자열로라도 전송하여 첨부파일과 함께 하나의 메시지로 전송
        const textContent = apiMessageContents.find(c => c.type === 'text')?.text || ''
        requestMessages.push({
          role: 'user',
          content: textContent, // 파일 내용이 포함된 텍스트 또는 빈 문자열
          contents: apiMessageContents
        })
      }
    } else {
      // 아무것도 없는 경우 기본 메시지 추가 (이론적으로는 발생하지 않아야 함)
      requestMessages.push({
        role: 'user',
        content: t('agentChat.message')
      })
    }

    // 유효성 검사
    if (!selectedService.value || !selectedService.value.serviceId) {
      throw new Error(t('agentChat.selectServiceError'))
    }

    if (requestMessages.length === 0 || requestMessages.filter(m => m.role === 'user').length === 0) {
      throw new Error(t('agentChat.enterMessageError'))
    }

    // 이미지가 포함된 메시지가 있는지 확인
    const hasImageMessage = requestMessages.some(m => {
      if (typeof m === 'object' && m !== null) {
        const msg = m as any
        if (Array.isArray(msg.contents)) {
          return msg.contents.some((c: any) => c.type === 'image_url')
        }
      }
      return false
    })
    
    // 이미지 생성 서비스/모델인지 확인
    const service = selectedService.value as any
    const serviceType = service?.serviceType
    const modelName = modelSettings.value.model?.toLowerCase() || ''
    const serviceCode = selectedService.value.serviceCode?.toLowerCase() || ''
    
    const isImageGenerationService = serviceType === 'ImageGeneration' || serviceType === 'Both' ||
      serviceCode.includes('dalle')
    
    const isImageGenerationModel = modelName.includes('dall-e') || 
      modelName.includes('dalle') ||
      modelName.includes('imagen') ||
      modelName.includes('flux') ||
      modelName.includes('gen4-image')
    
    // 비디오 생성 서비스/모델인지 확인
    const isVideoGenerationService = serviceType === 'VideoGeneration' || serviceType === 'Both'
    
    const isVideoGenerationModel = modelName.includes('videogeneration') ||
      modelName.includes('video-generation') ||
      modelName.includes('veo') ||
      modelName.includes('sora') ||
      serviceCode.includes('gen4-video') ||
      serviceCode.includes('veo') ||
      serviceCode.includes('sora')

    console.log('Sending request:', {
      serviceId: selectedService.value.serviceId,
      agentId: agentId.value,
      model: modelSettings.value.model,
      temperature: modelSettings.value.temperature / 100,
      maxTokens: modelSettings.value.maxTokens,
      messageCount: requestMessages.length,
      stream: false,
      hasImage: hasImageMessage,
      isImageGenerationService,
      isImageGenerationModel,
      isVideoGenerationService,
      isVideoGenerationModel,
      serviceType,
      lastMessagePreview: requestMessages.length > 0 ? JSON.stringify(requestMessages[requestMessages.length - 1]).substring(0, 300) : 'empty'
    })

    // 비디오 생성 서비스/모델인 경우 비디오 생성 API로 라우팅 (먼저 확인)
    if (isVideoGenerationService || isVideoGenerationModel) {
      // 사용자 메시지에서 프롬프트 추출
      const userMessage = requestMessages.find(m => m.role === 'user')
      let prompt = ''
      
      if (userMessage) {
        if (typeof userMessage === 'object' && 'content' in userMessage && userMessage.content) {
          prompt = userMessage.content
        } else if (typeof userMessage === 'object' && 'contents' in userMessage && Array.isArray(userMessage.contents)) {
          const textContent = userMessage.contents.find((c: any) => c.type === 'text')
          prompt = textContent?.text || ''
        }
      }

      if (!prompt) {
        throw new Error(t('agentChat.videoPromptRequired'))
      }

      // 비디오 생성 API는 최소 2개 모델이 필요하므로 에러 메시지 표시
      const errorMessage: Message = {
        tempId: `error-${Date.now()}`,
        role: 'assistant',
        content: t('agentChat.videoModelsRequired'),
        createdAt: new Date()
      }
      messages.value.push(errorMessage)
      loading.value = false
      await scrollToBottom()
      return
    }
    
    // 이미지 생성 서비스/모델인 경우 이미지 생성 API로 라우팅
    if (isImageGenerationService || isImageGenerationModel) {
      // 사용자 메시지에서 프롬프트 추출
      const userMessage = requestMessages.find(m => m.role === 'user')
      let prompt = ''
      
      if (userMessage) {
        if (typeof userMessage === 'object' && 'content' in userMessage && userMessage.content) {
          prompt = userMessage.content
        } else if (typeof userMessage === 'object' && 'contents' in userMessage && Array.isArray(userMessage.contents)) {
          const textContent = userMessage.contents.find((c: any) => c.type === 'text')
          prompt = textContent?.text || ''
        }
      }

      // 프롬프트가 없어도 이미지가 첨부되어 있으면 이미지만으로 생성 가능
      if (!prompt && uploadedImages.value.length === 0) {
        throw new Error(t('agentChat.imageGenerationPrompt'))
      }
      
      // 프롬프트가 없고 이미지만 있는 경우 기본 프롬프트 추가
      if (!prompt && uploadedImages.value.length > 0) {
        prompt = t('agentChat.imageReferencePrompt')
      }

      // 첨부된 이미지 추출 (Gemini Image 등 멀티모달 지원 모델용)
      const imageAttachments: Array<{ mimeType: string; data: string }> = []
      if (uploadedImages.value.length > 0) {
        for (const img of uploadedImages.value) {
          if (img.base64) {
            // Base64 데이터에서 MIME 타입 추출
            let mimeType = 'image/jpeg' // 기본값
            if (img.file?.type) {
              mimeType = img.file.type
            } else if (img.base64.includes('data:image/')) {
              // data URL에서 MIME 타입 추출
              const match = img.base64.match(/data:image\/([^;]+)/)
              if (match) {
                mimeType = `image/${match[1]}`
              }
            }
            
            // Base64 데이터 추출 (data URL이면 data: 부분 제거)
            let base64Data = img.base64
            if (base64Data.includes(',')) {
              base64Data = base64Data.split(',')[1]
            } else if (base64Data.startsWith('data:')) {
              const parts = base64Data.split(';base64,')
              base64Data = parts.length > 1 ? parts[1] : base64Data.replace('data:', '')
            }
            
            if (base64Data) {
              imageAttachments.push({
                mimeType: mimeType,
                data: base64Data
              })
            }
          }
        }
      }

      // 이미지 생성 요청 (대화 히스토리, 첨부 이미지, 웹 검색 포함)
      const imageResponse = await api.post('/image-generation/generate', {
        serviceId: selectedService.value.serviceId,
        model: modelSettings.value.model || 'dall-e-3',
        prompt: prompt,
        size: '1024x1024',
        quality: 'standard',
        numberOfImages: 1,
        agentId: agentId.value || null,
        conversationId: currentConversationId.value, // 기존 대화 ID 전달 (있으면)
        messages: requestMessages.filter(m => m.role !== 'system').map(m => ({
          role: m.role,
          content: m.content || ''
        })), // 대화 히스토리 전달
        imageAttachments: imageAttachments.length > 0 ? imageAttachments : undefined, // 첨부 이미지 전달
        enableWebSearch: enableWebSearch.value // 웹 검색 활성화 여부
      })

      // 로딩 상태 즉시 해제
      loading.value = false
      await nextTick()

      // 환영 메시지 제거
      const welcomeMessageIndex = messages.value.findIndex(m => m.tempId === 'welcome')
      if (welcomeMessageIndex !== -1) {
        messages.value.splice(welcomeMessageIndex, 1)
      }

      // conversationId 저장 (응답에서 받거나 기존 값 유지)
      if (imageResponse.data?.conversationId) {
        currentConversationId.value = imageResponse.data.conversationId
      }

      // 이미지 생성 응답을 메시지로 표시
      const imageUrls = imageResponse.data?.imageUrls || []
      const assistantMessage: Message = {
        tempId: `img-${Date.now()}`,
        role: 'assistant',
        content: t('agentChat.imageGenerationComplete', { count: imageUrls.length }),
        attachments: imageUrls.map((url: string, index: number) => ({
          type: 'image',
          url: url,
          name: `generated-image-${index + 1}.png`
        })),
        createdAt: new Date()
      }

      messages.value.push(assistantMessage)
      
      // 할당량 정보 갱신
      await loadQuota()
      
      // 첨부 파일 초기화
      uploadedFiles.value = []
      uploadedImages.value = []
      uploadedAudio.value = null
      
      await scrollToBottom()
      return
    }

    // 로딩 상태를 먼저 false로 설정하여 로딩 인디케이터 제거 (응답 받기 전)
    // 하지만 실제 응답을 받은 후에만 최종적으로 false로 유지
    // responseFormat을 시스템 프롬프트 지시로 변환
    const formatInstruction = advancedSettings.value.responseFormat !== 'markdown'
      ? { 'text': '일반 텍스트로 답변해주세요. 마크다운 문법을 사용하지 마세요.',
          'json': '반드시 유효한 JSON 형식으로만 답변해주세요.',
          'code': '코드 블록을 중심으로 답변해주세요.' }[advancedSettings.value.responseFormat] ?? null
      : null

    // formatInstruction이 있으면 requestMessages의 system 메시지에 추가
    if (formatInstruction) {
      const sysMsg = requestMessages.find((m: { role: string }) => m.role === 'system')
      if (sysMsg) {
        (sysMsg as { role: string; content?: string }).content = ((sysMsg as { content?: string }).content ?? '') + `\n\n${formatInstruction}`
      } else {
        requestMessages.unshift({ role: 'system', content: formatInstruction })
      }
    }

    // ──────────────────────────────────────────────────────────────────────
    // /chat/send 호출 — 스트리밍 분기 (Phase 3.5b 신규) vs 비스트리밍 폴백
    // ──────────────────────────────────────────────────────────────────────
    // 공통 페이로드: useStreaming 토글에 따라 /chat/send 또는 /chat/send/stream으로 분기
    const chatPayload = {
      serviceId: selectedService.value.serviceId,
      agentId: agentId.value || null,
      conversationId: currentConversationId.value || undefined,
      model: modelSettings.value.model || 'gpt-4-turbo',
      temperature: modelSettings.value.temperature / 100,
      maxTokens: modelSettings.value.maxTokens || 4096,
      messages: requestMessages,
      enableWebSearch: enableWebSearch.value && (
        selectedService.value.serviceCode?.toLowerCase() === 'chatgpt' ||
        selectedService.value.serviceCode?.toLowerCase() === 'openai' ||
        selectedService.value.serviceType === 'ImageGeneration' ||
        selectedService.value.serviceType === 'Both' ||
        (modelSettings.value.model?.toLowerCase().includes('gemini') && modelSettings.value.model?.toLowerCase().includes('image'))
      ),
      enableRag: enableRag.value,
      ragTopK: 3,
      // documentIds 필드는 Phase 2 자체 KB drop (ADR-2) 으로 제거됨.
      // 백엔드 RagService.cs(line 88-93) 도 documentIds 를 디버그 로그만 남기고 무시하므로
      // 페이로드에서 아예 제외해 라인 노이즈를 줄인다. RAG 권위는 Agent.KnowledgeBaseSource/Ref 로 결정.
      language: responseLanguage.value,
      enableDeepResearch: enableDeepResearch.value,
      enableDeepThinking: enableDeepThinking.value,
      thinkingMode: thinkingMode.value
    }

    if (useStreaming.value) {
      // ────────────────────────────────────────────────────────────────────
      // SSE 스트리밍 분기 — 토큰 단위로 즉시 표시되어 5~10초 대기 UX 문제 해소
      // ────────────────────────────────────────────────────────────────────
      // 환영 메시지가 있으면 첫 chunk 도착 전에 제거(빈 화면 방지)
      const welcomeIdx = messages.value.findIndex(m => m.tempId === 'welcome')
      if (welcomeIdx !== -1) messages.value.splice(welcomeIdx, 1)

      // 빈 assistant 메시지를 먼저 push — content가 빈 동안에는 v-else-if 가드로 bubble 미표시,
      // typing dots 인디케이터가 그 자리를 차지하므로 사용자에게는 자연스러움.
      // 첫 delta 도착 시 loading=false로 인디케이터 제거, content가 채워지며 bubble이 등장.
      const tempId = `streaming-${Date.now()}`
      const assistantMsg: Message = reactive({
        tempId,
        role: 'assistant',
        content: '',
        createdAt: new Date(),
        isStreaming: true
      })
      messages.value.push(assistantMsg)

      // 사용자가 "응답 중단" 버튼을 누르면 abort
      const abortCtrl = new AbortController()
      streamAbortController.value = abortCtrl

      let firstDeltaReceived = false
      let aborted = false
      let streamErrored = false

      try {
        for await (const evt of streamChat(chatPayload, abortCtrl.signal)) {
          switch (evt.type) {
            case 'delta':
              if (!firstDeltaReceived) {
                // 첫 토큰 도착 — 로딩 인디케이터 제거 (사용자에게 즉각적인 응답성 제공)
                firstDeltaReceived = true
                loading.value = false
                await nextTick()
              }
              assistantMsg.content += evt.content ?? ''
              // 스트리밍 도중에도 새 메시지가 시야 밖으로 밀리면 따라 스크롤
              await scrollToBottom()
              break

            case 'meta':
              if (evt.conversationId) currentConversationId.value = evt.conversationId
              if (evt.messageId) assistantMsg.messageId = evt.messageId
              if (evt.model) assistantMsg.model = evt.model
              break

            case 'usage':
              if (typeof evt.totalTokens === 'number') {
                assistantMsg.tokensUsed = evt.totalTokens
                stats.value.tokensUsed += evt.totalTokens
              }
              if (typeof evt.cost === 'number') {
                assistantMsg.cost = evt.cost
                stats.value.cost += evt.cost
              }
              break

            case 'error':
              // 백엔드가 의미 있는 에러를 SSE 본문에 흘린 경우(BANNED_WORD/PII 등)
              streamErrored = true
              assistantMsg.errorCode = evt.code
              assistantMsg.content = evt.message || t('agentChat.streamingError')
              if (evt.code === 'BANNED_WORD_DETECTED' || evt.code === 'PII_DETECTED') {
                assistantMsg.content += '\n\n' + t('agentChat.bannedWordsRetry')
              }
              break
          }
        }
      } catch (err: any) {
        if (err?.name === 'AbortError' || abortCtrl.signal.aborted) {
          // 사용자 중단 — 지금까지 받은 content는 유지, 안내 메시지를 한 줄 덧붙임
          aborted = true
          assistantMsg.content =
            (assistantMsg.content?.length ? assistantMsg.content + '\n\n' : '') +
            `_${t('agentChat.streamingAborted')}_`
        } else {
          // 네트워크/HTTP/refresh 실패 등 — 비스트리밍 폴백 catch와 동일 정책으로 surface
          streamErrored = true
          throw err
        }
      } finally {
        assistantMsg.isStreaming = false
        streamAbortController.value = null
        if (loading.value) loading.value = false
        await nextTick()
      }

      // content가 끝까지 비어있으면 안내 문구로 채움 (사용자에게 빈 bubble 방지)
      if (!assistantMsg.content || assistantMsg.content.trim() === '') {
        assistantMsg.content = t('agentChat.noResponse')
      }

      // 사용량 갱신 + 첨부 파일 초기화 (정상 종료 / 중단 / 에러 모두 동일 처리)
      if (!streamErrored && !aborted) {
        await loadQuota()
      }
      uploadedFiles.value = []
      uploadedImages.value = []
      uploadedAudio.value = null
    } else {
      // ────────────────────────────────────────────────────────────────────
      // 비스트리밍 폴백 (기존 흐름 보존)
      // ────────────────────────────────────────────────────────────────────
      const response = await api.post('/chat/send', { ...chatPayload, stream: false })

      // 응답 디버깅
      console.log('[sendMessage] API Response received:', {
        messageId: response.data.messageId,
        contentLength: response.data.content?.length || 0,
        contentPreview: response.data.content ? response.data.content.substring(0, 100) : '(empty)',
        model: response.data.model,
        tokensUsed: response.data.tokensUsed,
        cost: response.data.cost
      })

      // conversationId 저장 (응답에서 받거나 기존 값 유지)
      if (response.data?.conversationId) {
        currentConversationId.value = response.data.conversationId
      }

      // 응답을 받았으므로 로딩 상태 즉시 해제 (로딩 인디케이터 즉시 제거)
      loading.value = false
      await nextTick() // DOM 업데이트 대기하여 로딩 인디케이터 즉시 제거 보장

      // 환영 메시지가 있으면 제거 (실제 응답이 오면 환영 메시지 제거)
      const welcomeMessageIndex = messages.value.findIndex(m => m.tempId === 'welcome')
      if (welcomeMessageIndex !== -1) {
        messages.value.splice(welcomeMessageIndex, 1)
      }

      // 중복 응답 방지: 이미 동일한 messageId를 가진 메시지가 있는지 확인
      const existingMessageIndex = response.data.messageId && response.data.messageId > 0
        ? messages.value.findIndex(m => m.messageId === response.data.messageId && m.role === 'assistant')
        : -1

      // Content가 비어있는 경우 경고 로그
      if (!response.data.content || response.data.content.trim() === '') {
        console.warn('[sendMessage] Empty content in API response:', response.data)
      }

      if (existingMessageIndex === -1) {
        // 새 메시지만 추가 (중복 체크 완료)
        const assistantMessage: Message = {
          messageId: response.data.messageId || 0,
          role: 'assistant',
          content: response.data.content || t('agentChat.noResponse'),
          createdAt: new Date(),
          citations: response.data.citations || undefined,
          model: response.data.model || undefined,
          tokensUsed: response.data.tokensUsed || undefined
        }

        messages.value.push(assistantMessage)
      } else {
        // 이미 존재하는 메시지면 내용만 업데이트 (중복 방지)
        console.warn('[sendMessage] Duplicate message detected, updating existing message:', response.data.messageId)
        messages.value[existingMessageIndex].content = response.data.content || t('agentChat.noResponse')
        messages.value[existingMessageIndex].citations = response.data.citations || undefined
        messages.value[existingMessageIndex].model = response.data.model || undefined
        messages.value[existingMessageIndex].tokensUsed = response.data.tokensUsed || undefined
      }
      stats.value.tokensUsed += response.data.tokensUsed || 0
      stats.value.cost += (response.data.cost || 0)

      // 메시지 전송 성공 후 할당량 정보 갱신 및 첨부 파일 초기화
      await loadQuota()

      // 첨부 파일 초기화
      uploadedFiles.value = []
      uploadedImages.value = []
      uploadedAudio.value = null
    }
  } catch (error: any) {
    // 에러 발생 시 로딩 상태 즉시 해제
    loading.value = false

    // 진행 중이던 스트리밍 정리
    if (streamAbortController.value) {
      streamAbortController.value = null
    }

    // 스트리밍 placeholder 메시지(content가 비어있고 isStreaming였던 메시지)는 제거 — 빈 bubble + error 메시지 중복 방지
    const streamingPlaceholderIdx = messages.value.findIndex(
      m => m.role === 'assistant' && m.tempId?.startsWith('streaming-') && (!m.content || m.content.trim() === '')
    )
    if (streamingPlaceholderIdx !== -1) {
      messages.value.splice(streamingPlaceholderIdx, 1)
    } else {
      // placeholder가 일부 내용을 채우고 있었던 경우 → isStreaming 플래그만 끄고 cursor 제거
      const partialIdx = messages.value.findIndex(
        m => m.role === 'assistant' && m.tempId?.startsWith('streaming-') && m.isStreaming
      )
      if (partialIdx !== -1) {
        messages.value[partialIdx].isStreaming = false
      }
    }

    console.error('Error sending message:', error)

    // 중복 에러 메시지 방지
    const existingErrorIndex = messages.value.findIndex(m =>
      m.tempId?.startsWith('error-') && m.role === 'assistant'
    )
    
    if (existingErrorIndex === -1) {
      // Vertex AI 관련 에러인 경우 더 명확한 메시지 제공
      let errorContent = error.response?.data?.message || error.message || t('common.error')

      // 금칙어/개인정보 오류 시 재시도 안내 추가 (다른 메시지 보내면 정상 진행된다는 피드백)
      if (errorContent.includes('금칙어') || errorContent.includes('개인정보')) {
        errorContent = errorContent + '\n\n' + t('agentChat.bannedWordsRetry')
      }
      // Vertex AI 인증 실패 또는 deprecated 모델 관련 에러 감지
      else if (errorContent.includes('Vertex AI') ||
          errorContent.includes('OAuth') ||
          errorContent.includes('imagegeneration@006') ||
          errorContent.includes('deprecated')) {
        errorContent = `${t('agentChat.imageGenFailed')}: ${errorContent}\n\n` + t('agentChat.imageGenDeprecated')
      }

      const errorMessage: Message = {
        tempId: `error-${Date.now()}`,
        role: 'assistant',
        content: t('agentChat.errorOccurred') + ': ' + errorContent,
        createdAt: new Date()
      }
      messages.value.push(errorMessage)
    }
    
    // 에러 메시지를 콘솔에 더 자세히 출력
    if (error.response) {
      console.error('Response error:', error.response.data)
      console.error('Status:', error.response.status)
    }
  } finally {
    // 로딩 상태는 위에서 이미 해제했으므로, 여기서는 스크롤만 처리
    await scrollToBottom()
  }
}

// 진행 중인 SSE 스트리밍을 사용자가 중단할 때 호출 (UI에서 "응답 중단" 버튼 등에 바인딩)
const stopStreaming = () => {
  if (streamAbortController.value) {
    streamAbortController.value.abort()
    streamAbortController.value = null
  }
}

const clearChat = () => {
  if (confirm(t('agentChat.clearConfirm'))) {
    messages.value = []
    stats.value = { tokensUsed: 0, cost: 0 }
  }
}

const saveChat = () => {
  const chatData = {
    messages: messages.value,
    stats: stats.value,
    createdAt: new Date().toISOString()
  }
  const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `chat_${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const attachFile = () => {
  fileInput.value?.click()
}

const attachImage = () => {
  imageInput.value?.click()
}

// 음성 파일 선택 (기존 기능)
const attachAudioFile = () => {
  audioInput.value?.click()
}

// 음성 녹음 토글
const toggleAudioRecording = async () => {
  if (isRecording.value) {
    // 녹음 중지
    stopRecording()
  } else {
    // 녹음 시작
    await startRecording()
  }
}

// 녹음 시작
const startRecording = async () => {
  try {
    // MediaDevices API 지원 확인
    if (!navigator || typeof navigator === 'undefined') {
      alert(t('agentChat.browserNotSupported'))
      return
    }
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      // 오래된 브라우저를 위한 폴백
      const getUserMedia = (navigator as any).getUserMedia || 
                          (navigator as any).webkitGetUserMedia || 
                          (navigator as any).mozGetUserMedia || 
                          (navigator as any).msGetUserMedia
      
      if (!getUserMedia) {
        alert(t('agentChat.recordingNotSupported'))
        return
      }
      
      // 오래된 API 사용 (Promise 기반으로 변환)
      const stream = await new Promise<MediaStream>((resolve, reject) => {
        getUserMedia.call(navigator, { audio: true }, resolve, reject)
      })
      mediaStream.value = stream
    } else {
      // 마이크 권한 요청
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStream.value = stream
    }
    
    // MediaRecorder 생성 (브라우저 호환성 고려)
    let mimeType = 'audio/webm'
    if (!MediaRecorder.isTypeSupported('audio/webm')) {
      if (MediaRecorder.isTypeSupported('audio/mp4')) {
        mimeType = 'audio/mp4'
      } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        mimeType = 'audio/ogg'
      }
    }
    
    // stream이 mediaStream.value에 저장되어 있는지 확인
    const currentStream = mediaStream.value!
    const recorder = new MediaRecorder(currentStream, {
      mimeType: mimeType
    })
    
    audioChunks.value = []
    
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }
    
    recorder.onstop = async () => {
      try {
        // 녹음된 오디오를 Blob으로 생성
        const audioBlob = new Blob(audioChunks.value, { type: recorder.mimeType })
        
        // 파일 확장자 결정
        let extension = 'webm'
        if (recorder.mimeType.includes('mp4')) extension = 'mp4'
        else if (recorder.mimeType.includes('ogg')) extension = 'ogg'
        
        // File 객체로 변환
        const audioFile = new File([audioBlob], `recording_${Date.now()}.${extension}`, {
          type: recorder.mimeType,
          lastModified: Date.now()
        })
        
        // 서버에 업로드
        const formData = new FormData()
        formData.append('file', audioFile)
        
        const response = await api.post('/files/upload/audio', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        uploadedAudio.value = {
          file: audioFile,
          url: response.data.path
        }
        
        console.log('[Recording] Audio uploaded successfully:', response.data.path)
      } catch (error: any) {
        console.error('[Recording] Audio upload error:', error)
        alert(`${t('agentChat.audioUploadFailed')}: ${error.response?.data?.message || error.message}`)
      } finally {
        // 스트림 종료
        if (mediaStream.value) {
          mediaStream.value.getTracks().forEach(track => track.stop())
          mediaStream.value = null
        }
        
        // 타이머 정리
        if (recordingTimer.value !== null) {
          clearInterval(recordingTimer.value)
          recordingTimer.value = null
        }
        
        recordingTime.value = '00:00'
        isRecordingAudio.value = false
      }
    }
    
    recorder.onerror = (event: any) => {
      console.error('[Recording] MediaRecorder error:', event.error)
      alert(t('agentChat.recordingError'))
      stopRecording()
    }
    
    mediaRecorder.value = recorder
    recorder.start(1000) // 1초마다 데이터 수집
    
    isRecording.value = true
    isRecordingAudio.value = true
    recordingStartTime.value = Date.now()
    
    // 녹음 시간 표시
    recordingTimer.value = window.setInterval(() => {
      const elapsed = Math.floor((Date.now() - recordingStartTime.value) / 1000)
      const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0')
      const seconds = (elapsed % 60).toString().padStart(2, '0')
      recordingTime.value = `${minutes}:${seconds}`
    }, 1000)
    
  } catch (error: any) {
    console.error('[Recording] Error starting recording:', error)
    
    if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
      alert(t('agentChat.micPermissionRequired'))
    } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
      alert(t('agentChat.micNotFound'))
    } else {
      alert(`${t('agentChat.recordingStartFailed')}: ${error.message}`)
    }
    
    isRecording.value = false
    isRecordingAudio.value = false
    
    // 스트림 정리
    if (mediaStream.value) {
      mediaStream.value.getTracks().forEach(track => track.stop())
      mediaStream.value = null
    }
  }
}

// 녹음 중지
const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop()
    isRecording.value = false
  }
}

// 편집 공간 (Canva) 기능
const startEditing = (message: Message) => {
  if (message.role !== 'user') return
  editingMessageId.value = message.messageId || message.tempId || null
  editingContent.value = message.content || ''
}

const cancelEditing = () => {
  editingMessageId.value = null
  editingContent.value = ''
}

const saveAndResend = async (message: Message) => {
  if (!editingContent.value.trim()) {
    alert(t('agentChat.enterEditContent'))
    return
  }
  
  // 편집된 내용으로 메시지 업데이트
  const messageIndex = messages.value.findIndex(m => 
    (m.messageId || m.tempId) === (message.messageId || message.tempId)
  )
  
  if (messageIndex !== -1) {
    // 해당 메시지와 이후의 assistant 응답 제거
    messages.value.splice(messageIndex + 1)
    // 사용자 메시지 내용 업데이트
    messages.value[messageIndex].content = editingContent.value
  }
  
  // 편집 모드 종료
  cancelEditing()
  
  // 편집된 메시지로 재전송
  const originalInput = inputMessage.value
  inputMessage.value = editingContent.value
  await sendMessage()
  inputMessage.value = originalInput
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  for (let i = 0; i < target.files.length; i++) {
    const file = target.files[i]
    const fileType = getFileType(file.name)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/files/upload?parse=true', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      uploadedFiles.value.push({
        file,
        type: fileType,
        url: response.data.filePath,
        parsedContent: response.data.parsedContent
      })
    } catch (error: any) {
      console.error('File upload error:', error)
      alert(`${t('agentChat.fileUploadFailed')}: ${error.response?.data?.message || error.message}`)
    }
  }
  
  // Reset input
  target.value = ''
}

const handleImageSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  for (let i = 0; i < target.files.length; i++) {
    const file = target.files[i]
    
    // 이미지 파일 크기 제한 (20MB)
    const maxSize = 20 * 1024 * 1024
    if (file.size > maxSize) {
      alert(`${t('agentChat.imageUploadFailed')}: ${t('agentChat.fileTooLarge')} (${t('agentChat.fileSizeLimit', { size: formatFileSize(file.size) })})`)
      continue
    }
    
    try {
      // 이미지 미리보기 및 Base64 생성 (OpenAI Vision API용)
      const preview = await createImagePreview(file)
      // Base64 데이터 URL에서 실제 Base64 부분만 추출 (data:image/jpeg;base64, 부분 제거)
      let base64 = ''
      if (preview.includes(',')) {
        base64 = preview.split(',')[1]
      } else if (preview.startsWith('data:')) {
        // data: 다음에 바로 base64가 오는 경우 (드문 경우)
        const parts = preview.split(';base64,')
        base64 = parts.length > 1 ? parts[1] : preview.replace('data:', '')
      } else {
        base64 = preview
      }
      
      if (!base64 || base64.length === 0) {
        throw new Error(t('agentChat.base64ExtractFailed'))
      }
      
      console.log('[handleImageSelect] Image processed:', {
        name: file.name,
        size: file.size,
        type: file.type,
        previewLength: preview.length,
        base64Length: base64.length,
        base64Prefix: base64.substring(0, 20) + '...',
        hasPreview: !!preview
      })
      
      // 서버에 업로드 (선택적, 나중에 참조용)
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await api.post('/files/upload/image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        uploadedImages.value.push({
          file,
          url: response.data.path,
          preview,
          base64
        })
      } catch (uploadError: any) {
        // 업로드 실패해도 Base64가 있으면 계속 진행
        console.warn('Image upload to server failed, using Base64 only:', uploadError)
        uploadedImages.value.push({
          file,
          preview,
          base64
        })
      }
      
      // 이미지가 추가되면 Vision API 모델 자동 선택
      if (selectedService.value) {
        const serviceCode = selectedService.value.serviceCode?.toLowerCase()
        
        // OpenAI/ChatGPT의 경우 Vision 모델 선택
        // 웹 검색은 ChatGPT/OpenAI 또는 이미지 생성 서비스에서 사용 가능
        const isWebSearchEnabled = serviceCode === 'openai' || 
          serviceCode === 'chatgpt' ||
          selectedService.value?.serviceType === 'ImageGeneration' ||
          selectedService.value?.serviceType === 'Both' ||
          (modelSettings.value.model?.toLowerCase().includes('gemini') && modelSettings.value.model?.toLowerCase().includes('image'));
        
        if (isWebSearchEnabled) {
          await loadModels(selectedService.value.serviceId)
          // Vision 모델이 있는지 확인하고 자동 선택
          const visionModels = availableModels.value.filter(m => 
            m.toLowerCase().includes('vision') || 
            m.toLowerCase().includes('gpt-4-turbo') ||
            m.toLowerCase().includes('gpt-4o')
          )
          if (visionModels.length > 0 && !visionModels.includes(modelSettings.value.model)) {
            const recommendedModel = visionModels.find(m => m.toLowerCase().includes('turbo')) || 
                                     visionModels.find(m => m.toLowerCase().includes('gpt-4o')) ||
                                     visionModels[0]
            console.log('[handleImageSelect] Auto-selecting vision model:', recommendedModel)
            modelSettings.value.model = recommendedModel
          }
        }
        // Gemini의 경우 Gemini 3 Pro Image 모델 선택
        else if (serviceCode === 'gemini' || serviceCode === 'google') {
          await loadModels(selectedService.value.serviceId)
          // Gemini 3 Pro Image 모델이 있는지 확인하고 자동 선택
          const geminiImageModels = availableModels.value.filter(m => 
            m.toLowerCase().includes('gemini-3-pro-image') ||
            m.toLowerCase().includes('gemini-3.0-pro-image')
          )
          if (geminiImageModels.length > 0 && !geminiImageModels.includes(modelSettings.value.model)) {
            const recommendedModel = geminiImageModels[0]
            console.log('[handleImageSelect] Auto-selecting Gemini 3 Pro Image model:', recommendedModel)
            modelSettings.value.model = recommendedModel
          }
        }
      }
    } catch (error: any) {
      console.error('Image processing error:', error)
      alert(`${t('agentChat.imageUploadFailed')}: ${error.message}`)
    }
  }
  
  target.value = ''
}

const handleAudioSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return

  const file = target.files[0]
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/files/upload/audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    uploadedAudio.value = {
      file,
      url: response.data.path
    }
  } catch (error: any) {
    console.error('Audio upload error:', error)
    alert(`${t('agentChat.audioUploadFailed')}: ${error.response?.data?.message || error.message}`)
  }
  
  target.value = ''
}

const getFileType = (fileName: string): string => {
  const ext = fileName.split('.').pop()?.toLowerCase() || ''
  if (['pdf'].includes(ext)) return 'pdf'
  if (['txt'].includes(ext)) return 'text'
  if (['csv'].includes(ext)) return 'csv'
  if (['xls', 'xlsx'].includes(ext)) return 'excel'
  if (['doc', 'docx'].includes(ext)) return 'word'
  if (['hwp'].includes(ext)) return 'hwp'
  return 'file'
}

const createImagePreview = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target?.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const removeImage = (index: number) => {
  uploadedImages.value.splice(index, 1)
}

const removeAudio = () => {
  uploadedAudio.value = null
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// URL 안전하게 가져오기 (window.location 접근 보호)
const getFileUrl = (url: string): string => {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  if (typeof window !== 'undefined' && window.location && window.location.origin) {
    return `${window.location.origin}${url}`
  }
  // window가 없는 경우 (SSR 등) 원본 URL 반환
  return url
}

const getAttachmentUrl = (url: string): string => {
  return getFileUrl(url)
}

// 파일 다운로드 URL 생성 (API 엔드포인트 사용)
const getFileDownloadUrl = (url: string): string => {
  if (!url) return ''
  
  // 이미 전체 URL인 경우 API 엔드포인트로 변환
  if (url.startsWith('http://') || url.startsWith('https://')) {
    // URL에서 경로 부분만 추출
    try {
      const urlObj = new URL(url)
      const filePath = urlObj.pathname
      // /uploads/로 시작하는 경우 /api/files/download로 변환
      if (filePath.startsWith('/uploads/')) {
        return `/api/files/download${filePath}`
      }
    } catch {
      // URL 파싱 실패 시 그대로 반환
    }
  }
  
  // 상대 경로인 경우 API 엔드포인트로 변환
  if (url.startsWith('/uploads/')) {
    return `/api/files/download${url}`
  }
  
  // 경로가 없는 경우 원본 URL 반환
  return url
}

// 파일 다운로드 핸들러
const downloadFile = async (attachment: { type: string; url: string; name: string }) => {
  try {
    const downloadUrl = getFileDownloadUrl(attachment.url)
    console.log('[downloadFile] Downloading file:', { name: attachment.name, url: attachment.url, downloadUrl })
    
    // API를 통해 다운로드 (인증 토큰 포함)
    const response = await api.get(downloadUrl, {
      responseType: 'blob'
    })
    
    // Blob을 다운로드 링크로 변환
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = attachment.name || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error: any) {
    console.error('Error downloading file:', error)
    alert(`${t('agentChat.fileDownloadFailed')}: ${error.response?.data?.message || error.message}`)
    
    // 실패 시 직접 링크로 시도 (fallback)
    const downloadUrl = getFileDownloadUrl(attachment.url)
    if (downloadUrl.startsWith('/api/files/download')) {
      window.open(downloadUrl, '_blank')
    }
  }
}

// 이미지 소스 가져오기 (preview 우선, 없으면 URL 사용)
const getImageSource = (attachment: { type: string; url: string; name: string; preview?: string }): string => {
  // Base64 preview가 있으면 우선 사용 (서버 URL 문제 방지)
  if (attachment.preview) {
    return attachment.preview
  }
  // preview가 없으면 URL 사용
  if (attachment.url) {
    // data URL인 경우 그대로 반환 (Base64 이미지)
    if (attachment.url.startsWith('data:')) {
      return attachment.url
    }
    // 일반 URL인 경우 getAttachmentUrl 사용
    return getAttachmentUrl(attachment.url)
  }
  // 둘 다 없으면 빈 문자열 (에러 처리됨)
  return ''
}

// 이미지 다운로드 핸들러
const downloadImage = async (imageUrl: string, filename: string) => {
  try {
    const downloadFilename = filename || `image-${Date.now()}.png`
    
    // data URL인 경우 (Base64 이미지) 직접 다운로드
    if (imageUrl.startsWith('data:')) {
      // data URL에서 Base64 데이터 추출
      const base64Match = imageUrl.match(/^data:([^;]+);base64,(.+)$/)
      if (base64Match) {
        const mimeType = base64Match[1] || 'image/png'
        const base64Data = base64Match[2]
        
        // Base64를 Blob으로 변환
        const byteCharacters = atob(base64Data)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], { type: mimeType })
        
        // Blob을 다운로드 링크로 변환
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = downloadFilename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        return
      }
    }
    
    // 이미지 URL이 외부 URL인 경우 백엔드 프록시를 통해 다운로드 (CORS 문제 해결, 인증 포함)
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      const downloadUrl = `/api/image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(downloadFilename)}`
      
      // api 객체를 사용하여 인증 토큰이 포함된 요청으로 이미지 다운로드
      const response = await api.get(downloadUrl, {
        responseType: 'blob'
      })
      
      // Blob을 다운로드 링크로 변환
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = downloadFilename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } else {
      // 내부 URL인 경우 api 객체를 사용하여 인증 토큰 포함
      const response = await api.get(getAttachmentUrl(imageUrl), {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = downloadFilename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }
  } catch (error: any) {
    console.error('이미지 다운로드 실패:', error)
    alert(t('agentChat.imageDownloadFailed') + ': ' + (error.response?.data?.message || error.message || t('common.error')))
  }
}

// 이미지 로드 에러 처리
const handleImageError = (event: Event, attachment: { type: string; url: string; name: string; preview?: string }) => {
  const img = event.target as HTMLImageElement
  // 이미 URL을 사용하고 있었는데 에러가 난 경우, preview로 재시도
  if (attachment.preview && img.src !== attachment.preview) {
    console.warn('[handleImageError] Image URL failed, trying preview:', attachment.url)
    img.src = attachment.preview
    img.onerror = null // 무한 루프 방지
  } else {
    // preview도 실패했거나 없는 경우
    console.error('[handleImageError] Image failed to load:', {
      name: attachment.name,
      url: attachment.url,
      hasPreview: !!attachment.preview
    })
    // 에러 메시지 표시
    img.alt = t('agentChat.imageLoadFailed', { name: attachment.name })
    img.style.backgroundColor = '#f0f0f0'
    img.style.padding = '20px'
    img.style.display = 'flex'
    img.style.alignItems = 'center'
    img.style.justifyContent = 'center'
  }
}

// 이미지 모달 열기
const openImageModal = (src: string, title: string) => {
  imageModalSrc.value = src
  imageModalTitle.value = title
  showImageModal.value = true
}

// 이미지 모달 닫기
const closeImageModal = () => {
  showImageModal.value = false
  imageModalSrc.value = ''
  imageModalTitle.value = ''
}

const useSuggestedPrompt = (prompt: string) => {
  inputMessage.value = prompt
  // 포커스 이동
  nextTick(() => {
    const textarea = document.querySelector('textarea.form-control') as HTMLTextAreaElement
    if (textarea) {
      textarea.focus()
    }
  })
}

const useExamplePrompt = (prompt: string) => {
  inputMessage.value = prompt
  // 포커스 이동
  nextTick(() => {
    const textarea = document.querySelector('textarea.form-control') as HTMLTextAreaElement
    if (textarea) {
      textarea.focus()
      // 스크롤을 입력창으로 이동
      textarea.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

const loadExamplePrompts = async () => {
  if (!selectedService.value) {
    examplePrompts.value = []
    selectedCategory.value = null // 카테고리 초기화
    return
  }

  try {
    loadingExamplePrompts.value = true
    const serviceCode = selectedService.value.serviceCode
    const model = modelSettings.value.model
    
    // 서비스 코드로 필터링 (모델은 백엔드에서 유연하게 처리)
    const params: any = {
      serviceCode: serviceCode,
      isActive: true
    }
    
    // 모델 파라미터는 전달하지만, 백엔드에서 null인 것도 포함하도록 처리
    if (model) {
      params.model = model
    }
    
    const response = await api.get<ExamplePromptDto[]>('/exampleprompts', { params })
    
    // 백엔드에서 이미 필터링되어 오므로 그대로 사용
    // ServiceCode가 일치하거나 null인 것, Model이 null이거나 일치하는 것
    examplePrompts.value = response.data || []
    // 카테고리 초기화 (서비스 변경 시)
    selectedCategory.value = null
  } catch (error: any) {
    console.error('Error loading example prompts:', error)
    examplePrompts.value = []
  } finally {
    loadingExamplePrompts.value = false
  }
}

// 사용 가능한 카테고리 목록 (computed)
const availableCategories = computed(() => {
  const categories = new Set<string>()
  examplePrompts.value.forEach(prompt => {
    if (prompt.category) {
      categories.add(prompt.category)
    }
  })
  return Array.from(categories).sort()
})

// 필터링된 예제 프롬프트 (computed)
const filteredExamplePrompts = computed(() => {
  if (selectedCategory.value === null) {
    return examplePrompts.value
  }
  return examplePrompts.value.filter(prompt => prompt.category === selectedCategory.value)
})

const scrollToBottom = async () => {
  await nextTick()
  if (chatBody.value) {
    chatBody.value.scrollTop = chatBody.value.scrollHeight
  }
}

const formatTime = (date: string | Date): string => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

// Marked 설정 및 커스텀 렌더러
const renderer = new marked.Renderer()

// HTML 엔티티 디코딩 헬퍼 함수
const decodeHtmlEntities = (text: string): string => {
  const textarea = document.createElement('textarea')
  textarea.innerHTML = text
  return textarea.value
}

// 코드 블록 내 연속 공백을 &nbsp;로 변환하는 함수
const preserveSpacesInCode = (code: string): string => {
  // 연속된 공백(2개 이상)을 &nbsp;로 변환
  // 첫 번째 공백은 일반 공백으로 유지하고, 나머지는 &nbsp;로 변환
  return code.replace(/([^\S\n])([^\S\n]+)/g, (match, firstSpace, spaces) => {
    return firstSpace + '&nbsp;'.repeat(spaces.length)
  })
}

// 코드 블록 렌더러 커스터마이징
renderer.code = (code: string, language?: string) => {
  // HTML 엔티티가 포함되어 있을 수 있으므로 디코딩
  let decodedCode = code
  if (code.includes('&lt;') || code.includes('&gt;') || code.includes('&quot;') || code.includes('&amp;')) {
    try {
      decodedCode = decodeHtmlEntities(code)
    } catch (e) {
      // 디코딩 실패 시 원본 사용
      decodedCode = code
    }
  }
  
  // HTML 코드 블록은 Prism.js를 사용하지 않고 직접 처리 (왜곡 방지)
  if (language && language.toLowerCase() === 'html') {
    // HTML 코드 블록: 이미 디코딩된 코드를 안전하게 이스케이프하여 표시
    // 만약 여전히 HTML 엔티티가 있다면 추가 디코딩
    let finalCode = decodedCode
    if (decodedCode.includes('&lt;') || decodedCode.includes('&gt;')) {
      // 아직 HTML 엔티티가 남아있다면 디코딩
      finalCode = decodeHtmlEntities(decodedCode)
    }
    
    // 최종적으로 안전하게 이스케이프
    let escapedCode = finalCode
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
    
    // 연속 공백을 &nbsp;로 변환
    escapedCode = preserveSpacesInCode(escapedCode)
    
    return `<pre class="language-html"><code class="language-html">${escapedCode}</code></pre>`
  }
  
  if (typeof window !== 'undefined' && Prism && language) {
    const prismLang = language.toLowerCase()
    
    // Prism이 지원하는 언어인지 확인 (HTML 제외)
    if (Prism.languages[prismLang]) {
      try {
        // Prism.highlight는 원본 문자열을 받아야 하므로 디코딩된 코드 사용
        let highlightedCode = Prism.highlight(decodedCode, Prism.languages[prismLang], prismLang)
        // Prism이 생성한 HTML에서 code 태그 내부의 공백 변환
        highlightedCode = highlightedCode.replace(/([^\S\n])([^\S\n]+)/g, (match, firstSpace, spaces) => {
          return firstSpace + '&nbsp;'.repeat(spaces.length)
        })
        return `<pre class="language-${prismLang}"><code class="language-${prismLang}">${highlightedCode}</code></pre>`
      } catch (e) {
        console.error('Prism highlighting error:', e)
        // 에러 발생 시 기본 렌더링
        let escapedCode = decodedCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        escapedCode = preserveSpacesInCode(escapedCode)
        return `<pre class="language-${prismLang}"><code class="language-${prismLang}">${escapedCode}</code></pre>`
      }
    } else {
      // 지원하지 않는 언어는 기본 렌더링
      let escapedCode = decodedCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      escapedCode = preserveSpacesInCode(escapedCode)
      return `<pre class="language-${prismLang}"><code class="language-${prismLang}">${escapedCode}</code></pre>`
    }
  }
  
  // Prism이 없거나 언어가 없으면 기본 렌더링
  let escapedCode = decodedCode.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  escapedCode = preserveSpacesInCode(escapedCode)
  const langClass = language ? ` class="language-${language}"` : ''
  return `<pre><code${langClass}>${escapedCode}</code></pre>`
}

// 인라인 코드 렌더러 커스터마이징
renderer.codespan = (code: string) => {
  // HTML 엔티티가 이미 인코딩되어 있을 수 있으므로 먼저 디코딩
  let decodedCode = code
  if (code.includes('&lt;') || code.includes('&gt;') || code.includes('&quot;') || code.includes('&amp;')) {
    try {
      decodedCode = decodeHtmlEntities(code)
    } catch (e) {
      decodedCode = code
    }
  }
  // 디코딩된 코드를 다시 안전하게 이스케이프
  const escapedCode = decodedCode
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
  return `<code>${escapedCode}</code>`
}

marked.setOptions({
  breaks: true, // 줄바꿈을 <br>로 변환
  gfm: true, // GitHub Flavored Markdown 지원
  renderer: renderer
})

const formatMessage = (content: string, messageId: string | number, citations?: string[]): string => {
  if (!content) return ''
  
  try {
    // AI 응답에서 코드 블록 내부의 HTML 엔티티를 먼저 디코딩
    // 마크다운 코드 블록 (```language\ncode\n```) 패턴 찾기
    // HTML 코드 블록은 별도 처리 (language가 html인 경우)
    let processedContent = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, codeBlock) => {
      const language = lang ? lang.toLowerCase().trim() : ''
      
      // HTML 코드 블록의 경우: HTML 엔티티 디코딩하지 않고 그대로 유지 (렌더러에서 처리)
      if (language === 'html') {
        return match // 원본 그대로 반환 (렌더러에서 처리)
      }
      
      // 다른 언어 코드 블록: HTML 엔티티 디코딩
      const decodedCode = codeBlock
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&#x27;/g, "'")
        .replace(/&#x2F;/g, '/')
        .replace(/&amp;/g, '&')
        .replace(/&nbsp;/g, ' ')
      
      // 코드 블록을 원래 형태로 복원
      return lang ? `\`\`\`${lang}\n${decodedCode}\n\`\`\`` : `\`\`\`\n${decodedCode}\n\`\`\``
    })
    
    // 인라인 코드 블록 (`code`) 패턴 찾기 - HTML 엔티티 디코딩 (렌더러에서 다시 이스케이프)
    processedContent = processedContent.replace(/`([^`]+)`/g, (match, code) => {
      // 인라인 코드 내부의 HTML 엔티티 디코딩 (렌더러에서 다시 안전하게 이스케이프됨)
      const decodedCode = code
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&#x27;/g, "'")
        .replace(/&#x2F;/g, '/')
        .replace(/&amp;/g, '&')
      return `\`${decodedCode}\``
    })

    // [BUTTONS: ...] 를 marked 처리 전에 플레이스홀더로 치환 (|가 테이블로 오해되는 것 방지)
    // 주의: __text__ 는 markdown bold 문법이므로 영문+숫자만 사용
    const quickReplyPlaceholders: string[] = []
    processedContent = processedContent.replace(/\[BUTTONS:\s*([^\]]+)\]/g, (_match: string, buttonsStr: string) => {
      const buttons = buttonsStr.split('|').map((b: string) => b.trim()).filter(Boolean)
      const btns = buttons.map((btn: string) => {
        const escaped = btn.replace(/"/g, '&quot;')
        return `<button class="quick-reply-btn" data-quick-reply="${escaped}">${escaped}</button>`
      }).join('')
      const btnHtml = `<div class="quick-reply-container">${btns}</div>`
      const placeholder = `QRPH${quickReplyPlaceholders.length}XEND`
      quickReplyPlaceholders.push(btnHtml)
      return placeholder
    })

    // marked의 커스텀 렌더러가 이미 Prism 구문 강조를 적용
    let html = marked.parse(processedContent) as string
    
    // HTML 코드 블록은 이미 커스텀 렌더러에서 올바르게 이스케이프되었으므로 추가 처리 불필요
    // 다른 언어 코드 블록에 대해서만 추가 처리 (필요시)
    
    // Perplexity citation 번호 [1], [2] 등을 클릭 가능한 링크로 변환
    if (citations && citations.length > 0) {
      // [1], [2], [10] 등의 패턴을 찾아서 클릭 가능한 링크로 변환
      html = html.replace(/\[(\d+)\]/g, (match, num) => {
        const index = parseInt(num) - 1
        if (index >= 0 && index < citations.length) {
          // citation 번호를 클릭하면 해당 출처로 스크롤
          const citationUrl = citations[index].replace(/"/g, '&quot;')
          return `<a href="#citation-${messageId}-${num}" class="citation-number" data-citation-id="citation-${messageId}-${num}" title="${citationUrl}">[${num}]</a>`
        }
        return match
      })
    }
    
    // 테이블에 Bootstrap 클래스 추가
    html = html.replace(/<table>/g, '<table class="markdown-table table table-bordered table-striped table-hover">')
    html = html.replace(/<thead>/g, '<thead class="table-light">')
    
    // 코드 블록에 클래스 추가 및 스타일 개선 (Prism이 처리하지 않은 경우)
    html = html.replace(/<pre><code(?!\s+class="language-)/g, '<pre class="markdown-code-block"><code class="markdown-code"')
    html = html.replace(/<code(?!\s+class="language-)(?!\s+class="markdown-)/g, '<code class="markdown-inline-code"')
    
    // 헤딩에 클래스 추가
    html = html.replace(/<h1>/g, '<h1 class="markdown-heading markdown-h1">')
    html = html.replace(/<h2>/g, '<h2 class="markdown-heading markdown-h2">')
    html = html.replace(/<h3>/g, '<h3 class="markdown-heading markdown-h3">')
    html = html.replace(/<h4>/g, '<h4 class="markdown-heading markdown-h4">')
    html = html.replace(/<h5>/g, '<h5 class="markdown-heading markdown-h5">')
    html = html.replace(/<h6>/g, '<h6 class="markdown-heading markdown-h6">')
    
    // 리스트에 클래스 추가
    html = html.replace(/<ul>/g, '<ul class="markdown-list markdown-ul">')
    html = html.replace(/<ol>/g, '<ol class="markdown-list markdown-ol">')
    html = html.replace(/<li>/g, '<li class="markdown-list-item">')
    
    // 단락에 클래스 추가 및 간격 개선
    html = html.replace(/<p>/g, '<p class="markdown-paragraph">')
    
    // blockquote 스타일 개선
    html = html.replace(/<blockquote>/g, '<blockquote class="markdown-blockquote">')
    
    // 링크에 클래스 추가
    html = html.replace(/<a href=/g, '<a class="markdown-link" href=')
    
    // 강조 텍스트 개선
    html = html.replace(/<strong>/g, '<strong class="markdown-strong">')
    html = html.replace(/<em>/g, '<em class="markdown-em">')
    
    // hr 스타일 개선
    html = html.replace(/<hr>/g, '<hr class="markdown-hr">')
    
    // DOMPurify로 XSS 방지 (안전한 HTML만 허용)
    if (typeof window !== 'undefined') {
      // 코드 블록을 임시로 마스킹하여 DOMPurify가 건드리지 않도록 함
      const codeBlockPlaceholders: string[] = []
      html = html.replace(/<pre[^>]*><code[^>]*>[\s\S]*?<\/code><\/pre>/gi, (match) => {
        const placeholder = `__CODE_BLOCK_${codeBlockPlaceholders.length}__`
        codeBlockPlaceholders.push(match)
        return placeholder
      })
      html = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
          'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
          'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'ul', 'ol', 'li', 'blockquote',
          'table', 'thead', 'tbody', 'tr', 'th', 'td',
          'a', 'img',
          'hr', 'div', 'span',
          'button'
        ],
        ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel', 'id', 'data-citation-id', 'data-quick-reply'],
        ALLOW_DATA_ATTR: true,
        KEEP_CONTENT: true,
        FORBID_TAGS: [],
        FORBID_ATTR: []
      })
      
      // 코드 블록을 원래대로 복원하고, code 태그 내부의 공백 변환
      codeBlockPlaceholders.forEach((codeBlock, index) => {
        // code 태그 내부의 연속 공백을 &nbsp;로 변환
        const processedCodeBlock = codeBlock.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (codeMatch: string, codeContent: string) => {
          // 연속된 공백(2개 이상)을 &nbsp;로 변환
          const processed = codeContent.replace(/([^\S\n])([^\S\n]+)/g, (_spaceMatch: string, firstSpace: string, spaces: string) => {
            return firstSpace + '&nbsp;'.repeat(spaces.length)
          })
          return codeMatch.replace(codeContent, processed)
        })
        html = html.replace(`__CODE_BLOCK_${index}__`, processedCodeBlock)
      })
      
      // 인라인 code 태그 내부의 공백도 변환 (pre로 감싸진 code는 이미 처리되었으므로 제외)
      html = html.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (codeMatch: string, codeContent: string) => {
        // pre 태그로 감싸진 code는 이미 처리되었으므로 제외
        if (codeMatch.includes('<pre') || codeMatch.includes('</pre>')) {
          return codeMatch
        }
        // 인라인 code 태그 내부의 연속 공백 변환
        const processed = codeContent.replace(/([^\S\n])([^\S\n]+)/g, (_spaceMatch: string, firstSpace: string, spaces: string) => {
          return firstSpace + '&nbsp;'.repeat(spaces.length)
        })
        return codeMatch.replace(codeContent, processed)
      })
    } else {
      // DOMPurify를 사용하지 않는 경우에도 code 태그 내부 공백 변환
      html = html.replace(/<code[^>]*>([\s\S]*?)<\/code>/gi, (codeMatch: string, codeContent: string) => {
        const processed = codeContent.replace(/([^\S\n])([^\S\n]+)/g, (_spaceMatch: string, firstSpace: string, spaces: string) => {
          return firstSpace + '&nbsp;'.repeat(spaces.length)
        })
        return codeMatch.replace(codeContent, processed)
      })
    }

    // Quick reply 플레이스홀더 복원 (DOMPurify 이후에 삽입하여 sanitize 우회)
    quickReplyPlaceholders.forEach((btnHtml, index) => {
      html = html.replace(`QRPH${index}XEND`, btnHtml)
    })

    return html
  } catch (error) {
    console.error('Error parsing markdown:', error)
    // 에러 발생 시 기본 텍스트 반환
    return escapeHtml(content)
  }
}

// Citation 번호 클릭 시 해당 출처로 스크롤하는 함수
const scrollToCitation = (citationId: string) => {
  const element = document.getElementById(citationId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    // 잠시 하이라이트 효과
    element.classList.add('citation-highlight')
    setTimeout(() => {
      element.classList.remove('citation-highlight')
    }, 2000)
  }
}

// 추가: DOM이 업데이트된 후 citation 핸들러 설정
onMounted(() => {
  setupCitationClickHandlers()

  // Quick reply 버튼 클릭 이벤트 위임
  if (chatBody.value) {
    chatBody.value.addEventListener('click', (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest('[data-quick-reply]') as HTMLElement | null
      if (!target) return
      const text = target.getAttribute('data-quick-reply')
      if (text && !loading.value) {
        inputMessage.value = text
        sendMessage()
      }
    })
  }
})

// HTML 이스케이프 헬퍼 함수
const escapeHtml = (text: string): string => {
  if (typeof document === 'undefined') {
    // SSR 환경에서도 작동하도록
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
  }
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}


// Citation 번호 클릭 이벤트 핸들러 설정
const setupCitationClickHandlers = () => {
  if (typeof document === 'undefined') return
  
  // 모든 citation-number 링크에 클릭 이벤트 추가
  const citationLinks = document.querySelectorAll('.message-text .citation-number')
  citationLinks.forEach(link => {
    // 기존 리스너 제거 (중복 방지)
    link.removeEventListener('click', handleCitationClick as EventListener)
    // 새 리스너 추가
    link.addEventListener('click', handleCitationClick as EventListener)
  })
}

// Citation 번호 클릭 핸들러
const handleCitationClick = (event: Event) => {
  event.preventDefault()
  const target = event.currentTarget as HTMLElement
  const citationId = target.getAttribute('data-citation-id') || target.getAttribute('href')?.replace('#', '')
  
  if (citationId) {
    scrollToCitation(citationId)
  }
}

// 메시지 표시 강제 - 전역 스타일 오버라이드
const forceMessageVisibility = () => {
  if (typeof document === 'undefined') return
  
  const styleId = 'agent-chat-force-visible'
  let style = document.getElementById(styleId) as HTMLStyleElement
  
  if (!style) {
    style = document.createElement('style')
    style.id = styleId
    document.head.appendChild(style)
  }
  
  style.textContent = `
    .chat-body .message,
    .chat-body .message-user,
    .chat-body .message-assistant {
      animation: none !important;
      animation-name: none !important;
      animation-duration: 0s !important;
      animation-delay: 0s !important;
      animation-fill-mode: none !important;
      animation-play-state: paused !important;
      opacity: 1 !important;
      visibility: visible !important;
      display: flex !important;
      transform: none !important;
    }
    .chat-body .message-content,
    .chat-body .message-text {
      opacity: 1 !important;
      visibility: visible !important;
      display: block !important;
      transform: none !important;
    }
    .chat-body .message-text > * {
      opacity: 1 !important;
      visibility: visible !important;
      display: block !important;
      transform: none !important;
    }
    .chat-body .message-avatar {
      opacity: 1 !important;
      visibility: visible !important;
      display: flex !important;
      transform: none !important;
    }
    /* 사용자 메시지 텍스트 색상 강제 */
    .chat-body .message-user .message-content,
    .chat-body .message-user .message-text,
    .chat-body .message-user .message-text *,
    .chat-body .message-user .message-content * {
    }
    /* 어시스턴트 메시지 텍스트 색상 강제 */
    .chat-body .message-assistant .message-content,
    .chat-body .message-assistant .message-text,
    .chat-body .message-assistant .message-text *,
    .chat-body .message-assistant .message-content * {
      color: #111827 !important;
    }
  `
}

watch(() => messages.value.length, async () => {
  await nextTick()
  forceMessageVisibility()
  await scrollToBottom()
  setupCitationClickHandlers()
})

onMounted(async () => {
  await loadServices()
  // 초기 citation 핸들러 설정
  await nextTick()
  setupCitationClickHandlers()
  
  // 메시지 표시 강제
  forceMessageVisibility()
  
  // 서비스가 로드된 후 연결 상태 확인 및 할당량 정보 로드
  if (selectedService.value) {
    await checkConnectionStatus()
    await loadQuota()
  }
  
  // 주기적으로 연결 상태 확인 (30초마다)
  statusCheckInterval = window.setInterval(() => {
    if (selectedService.value) {
      checkConnectionStatus()
    }
  }, 30000)
  
  // 환영 메시지 (초기 로딩 시에만 표시, 대화 기록이 없을 때만)
  if (messages.value.length === 0) {
    const welcomeMessage = agent.value?.systemPrompt 
      ? t('agentChat.welcomeWithAgent', { name: agent.value.agentName || 'AI', description: agent.value.description || t('agentChat.howCanIHelp') })
      : t('agentChat.welcomeDefault')
    
    messages.value.push({
      tempId: 'welcome',
      role: 'assistant',
      content: welcomeMessage,
      createdAt: new Date()
    })
  }
  
  await nextTick()
  forceMessageVisibility()
})

// 컴포넌트 언마운트 시 정리
onBeforeUnmount(() => {
  // 상태 확인 인터벌 정리
  if (statusCheckInterval !== null) {
    clearInterval(statusCheckInterval)
    statusCheckInterval = null
  }
  
  // 녹음 중이면 중지
  if (isRecording.value && mediaRecorder.value) {
    stopRecording()
  }
  
  // 스트림 정리
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
  
  // 타이머 정리
  if (recordingTimer.value !== null) {
    clearInterval(recordingTimer.value)
    recordingTimer.value = null
  }

  // 진행 중인 SSE 스트리밍 정리 (Phase 3.5b)
  if (streamAbortController.value) {
    streamAbortController.value.abort()
    streamAbortController.value = null
  }
})
</script>

<style scoped>
/* 전역 스타일과의 충돌을 완전히 막기 위해 scoped를 유지하되 더 강력하게 */
</style>

<style>
/* 전역 스타일 오버라이드 - scoped 밖에서 전역 적용 */
.chat-body {
  min-height: 400px !important;
  height: 100% !important;
  max-height: none !important;
  padding: 20px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  position: relative !important;
  z-index: 10 !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  flex: 1 1 auto !important;
  -webkit-overflow-scrolling: touch !important;
  transform: none !important;
}

/* 메시지 컨테이너 - 글로벌 스타일 완전 오버라이드 */
.chat-body .message,
.chat-body .message-user,
.chat-body .message-assistant,
div.chat-body > div.message,
div.chat-body > div.message-user,
div.chat-body > div.message-assistant {
  margin-bottom: 24px !important;
  animation: none !important;
  animation-name: none !important;
  animation-duration: 0s !important;
  animation-delay: 0s !important;
  animation-fill-mode: none !important;
  animation-play-state: paused !important;
  width: 100% !important;
  display: flex !important;
  opacity: 1 !important;
  position: relative !important;
  z-index: 11 !important;
  visibility: visible !important;
  transform: none !important;
  will-change: auto !important;
}

.chat-body .message-avatar,
div.chat-body .message-avatar {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  z-index: 12 !important;
  animation: none !important;
}

.chat-body .message-content,
div.chat-body .message-content {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  animation: none !important;
}

.chat-body .message-text,
div.chat-body .message-text {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  animation: none !important;
}

.chat-body .message-text > *,
div.chat-body .message-text > * {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
  animation: none !important;
}

/* 사용자 메시지 텍스트 색상 강제 */
.chat-body .message-user .message-content,
div.chat-body .message-user .message-content {
}

.chat-body .message-user .message-text,
div.chat-body .message-user .message-text {
}

.chat-body .message-user .message-text *,
div.chat-body .message-user .message-text *,
.chat-body .message-user .message-text p,
div.chat-body .message-user .message-text p,
.chat-body .message-user .message-text span,
div.chat-body .message-user .message-text span,
.chat-body .message-user .message-text div,
div.chat-body .message-user .message-text div,
.chat-body .message-user .message-text li,
div.chat-body .message-user .message-text li,
.chat-body .message-user .message-text li *,
div.chat-body .message-user .message-text li *,
.chat-body .message-user .message-text li p,
div.chat-body .message-user .message-text li p,
.chat-body .message-user .message-content *,
div.chat-body .message-user .message-content *,
.chat-body .message-user .message-content p,
div.chat-body .message-user .message-content p,
.chat-body .message-user .message-content span,
div.chat-body .message-user .message-content span {
}

/* 어시스턴트 메시지 텍스트 색상 강제 */
.chat-body .message-assistant .message-content,
div.chat-body .message-assistant .message-content {
  color: #111827 !important;
}

.chat-body .message-assistant .message-text,
div.chat-body .message-assistant .message-text {
  color: #111827 !important;
}

.chat-body .message-assistant .message-text *,
div.chat-body .message-assistant .message-text *,
.chat-body .message-assistant .message-content *,
div.chat-body .message-assistant .message-content * {
  color: #111827 !important;
}
</style>

<style scoped>
/* 전역 스타일과의 충돌을 완전히 막기 위해 scoped를 유지하되 더 강력하게 */
.message-user {
  display: flex !important;
  justify-content: flex-end !important;
  align-items: flex-start !important;
  width: 100% !important;
  flex-direction: row !important;
}

.message-user .message-avatar {
  order: 2 !important;
}

.message-user .message-content {
  order: 1 !important;
}

.message-assistant {
  display: flex !important;
  justify-content: flex-start !important;
  align-items: flex-start !important;
  width: 100% !important;
  flex-direction: row !important;
}

.chat-body .message-content {
  max-width: 75% !important;
  min-width: 120px !important;
  width: fit-content !important;
  padding: 10px 14px !important;
  border-radius: 12px !important;
  font-size: 0.875rem !important;
  line-height: 1.6 !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  word-break: break-word !important;
  white-space: normal !important;
  display: block !important;
  position: relative !important;
  z-index: 12 !important;
  flex: none !important;
  visibility: visible !important;
  opacity: 1 !important;
  transform: none !important;
}

.message-user .message-content {
  background: #4F46E5 !important;
  color: white !important;
  border-bottom-right-radius: 4px;
  margin-right: 0 !important;
  margin-left: auto !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
  text-align: left !important;
}

.message-user .message-content {
  color: white !important;
}

.message-user .message-content .message-header {
  color: rgba(255, 255, 255, 0.9) !important;
}

.message-user .message-content .message-header small {
  color: rgba(255, 255, 255, 0.7) !important;
}

.message-user .message-content {
}

.message-user .message-content .message-text {
}

.message-user .message-content .message-text,
.message-user .message-content .message-text *,
.message-user .message-content .message-text :deep(*),
.message-user .message-content .message-text :deep(p),
.message-user .message-content .message-text :deep(span),
.message-user .message-content .message-text :deep(div),
.message-user .message-content .message-text :deep(li),
.message-user .message-content .message-text :deep(ul),
.message-user .message-content .message-text :deep(ol),
.message-user .message-content .message-text :deep(h1),
.message-user .message-content .message-text :deep(h2),
.message-user .message-content .message-text :deep(h3),
.message-user .message-content .message-text :deep(h4),
.message-user .message-content .message-text :deep(h5),
.message-user .message-content .message-text :deep(h6),
.message-user .message-content .message-text :deep(strong),
.message-user .message-content .message-text :deep(em),
.message-user .message-content .message-text :deep(code),
.message-user .message-content .message-text :deep(pre),
.message-user .message-content .message-text :deep(a) {
}

/* 사용자 메시지 내부 모든 텍스트 요소 강제 흰색 - 최우선 적용 */
.message-user .message-content,
.message-user .message-content *,
.message-user .message-content :deep(*),
.message-user .message-content :deep(p),
.message-user .message-content :deep(span),
.message-user .message-content :deep(div),
.message-user .message-content :deep(h1),
.message-user .message-content :deep(h2),
.message-user .message-content :deep(h3),
.message-user .message-content :deep(h4),
.message-user .message-content :deep(h5),
.message-user .message-content :deep(h6),
.message-user .message-content :deep(strong),
.message-user .message-content :deep(em),
.message-user .message-content :deep(li),
.message-user .message-content :deep(ul),
.message-user .message-content :deep(ol),
.message-user .message-content :deep(li > p),
.message-user .message-content :deep(li > span),
.message-user .message-content :deep(a),
.user-message-text,
.user-message-text *,
.user-message-text :deep(*),
.user-message-text :deep(p),
.user-message-text :deep(span),
.user-message-text :deep(div),
.user-message-text :deep(li),
.user-message-text :deep(li > p) {
}

/* assistant-message-text 내부 h2, h3, h4 스타일 */
.assistant-message-text :deep(.markdown-h2),
.assistant-message-text :deep(h2),
.assistant-message-text h2 {
  font-size: 1.8rem !important;
  font-weight: bold !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
  line-height: 1.4 !important;
}

.assistant-message-text :deep(.markdown-h3),
.assistant-message-text :deep(h3),
.assistant-message-text h3 {
  font-size: 1.4rem !important;
  font-weight: 600 !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.4 !important;
}

.assistant-message-text :deep(.markdown-h4),
.assistant-message-text :deep(h4),
.assistant-message-text h4 {
  font-size: 1.2rem !important;
  font-weight: normal !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.5 !important;
}

/* user-message-text 내부 h2, h3, h4 스타일 */
.user-message-text :deep(.markdown-h2),
.user-message-text :deep(h2),
.user-message-text h2 {
  font-size: 1.8rem !important;
  font-weight: bold !important;
  color: #ffffff !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3) !important;
  line-height: 1.4 !important;
}

.user-message-text :deep(.markdown-h3),
.user-message-text :deep(h3),
.user-message-text h3 {
  font-size: 1.4rem !important;
  font-weight: 600 !important;
  color: #ffffff !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.4 !important;
}

.user-message-text :deep(.markdown-h4),
.user-message-text :deep(h4),
.user-message-text h4 {
  font-size: 1.2rem !important;
  font-weight: normal !important;
  color: #ffffff !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.5 !important;
}

.message-user .message-content :deep(p),
.user-message-text :deep(p) {
  margin: 0.5rem 0 !important;
  background: transparent !important;
}

.message-assistant .message-content {
  background: #f8f9fa !important;
  color: #1f2937 !important;
  border-bottom-left-radius: 4px;
  border-left: 3px solid #4F46E5 !important;
  margin-left: 8px !important;
  margin-right: 0 !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
  line-height: 1.7 !important;
}

/* 어시스턴트 메시지 가독성 향상 */
.message-assistant .message-content .message-text {
  color: #1f2937 !important;
}

.message-assistant .message-content .message-text :deep(p) {
  color: #1f2937 !important;
  margin: 0.625rem 0 !important;
  line-height: 1.75 !important;
}

.message-assistant .message-content .message-text :deep(strong) {
  color: #111827 !important;
  font-weight: 600 !important;
}

.message-assistant .message-content .message-text :deep(em) {
  color: #374151 !important;
  font-style: italic !important;
}

.message-assistant .message-content .message-header {
  color: #374151 !important;
}

.message-assistant .message-content .message-header small {
  color: #6b7280 !important;
}

.message-assistant .message-content .message-text {
  color: #111827 !important;
}

.message-assistant .message-content .message-text :deep(*),
.message-assistant .message-content .message-text :deep(p),
.message-assistant .message-content .message-text :deep(span),
.message-assistant .message-content .message-text :deep(div),
.message-assistant .message-content .message-text :deep(li),
.message-assistant .message-content .message-text :deep(ul),
.message-assistant .message-content .message-text :deep(ol) {
  color: #111827 !important;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.75rem;
  font-weight: 500;
}

.message-header strong {
  font-weight: 600;
}

.chat-body .message-text {
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  word-break: break-word !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  line-height: 1.6 !important;
  color: inherit !important;
  position: relative !important;
  z-index: 13 !important;
  transform: none !important;
}

/* v-html로 렌더링된 내용도 보이도록 */
.chat-body .message-text > * {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  color: inherit !important;
  transform: none !important;
}

.chat-body .message-text > p {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  margin: 0.5rem 0 !important;
  transform: none !important;
}

.chat-body .message-text > p:first-child {
  margin-top: 0 !important;
}

.chat-body .message-text > p:last-child {
  margin-bottom: 0 !important;
}

.message-text > * {
  margin-top: 0 !important;
  margin-bottom: 0.75rem !important;
}

.message-text > *:first-child {
  margin-top: 0 !important;
}

.message-text > *:last-child {
  margin-bottom: 0 !important;
}

/* 마크다운 단락 스타일 */
.message-text :deep(.markdown-paragraph) {
  margin-bottom: 0.875rem !important;
  line-height: 1.7 !important;
  color: inherit !important;
}

.message-text :deep(.markdown-paragraph:last-child) {
  margin-bottom: 0 !important;
}

.message-avatar {
  width: 36px;
  height: 36px;
  min-width: 36px;
  min-height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  margin: 0 8px;
  flex-shrink: 0;
}

.status-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
  animation: pulse 2s infinite;
}

.status-indicator.online {
  background-color: #10b981;
}

.status-indicator.offline {
  background-color: #ef4444;
  animation: none;
}

.status-indicator.checking {
  background-color: #f59e0b;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}

.chat-card {
  display: flex;
  flex-direction: column;
}

.chat-card .card-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

/* 비활성화 버튼 스타일 */
.btn-disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
  pointer-events: none !important;
}

/* 강조 텍스트 스타일 */
.message-text :deep(.markdown-strong) {
  font-weight: 700 !important;
  color: inherit !important;
}

.message-text :deep(.markdown-em) {
  font-style: italic !important;
  color: inherit !important;
}

/* 출처 링크 스타일 */
.message-citations {
  margin-top: 0.75rem;
  padding-top: 0.5rem;
}

.citation-link {
  transition: all 0.2s ease;
}

.citation-link:hover {
  background-color: #6c757d !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Citation 번호 스타일 */
.message-text :deep(.citation-number) {
  color: #4F46E5 !important;
  text-decoration: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 3px;
  background-color: rgba(79, 70, 229, 0.1);
}

.message-user .message-content .message-text :deep(.citation-number) {
  color: rgba(255, 255, 255, 0.9) !important;
  background-color: rgba(255, 255, 255, 0.2);
}

.message-text :deep(.citation-number:hover) {
  color: #6366F1;
  background-color: rgba(79, 70, 229, 0.2);
  transform: scale(1.1);
}

/* Citation 하이라이트 효과 */
.citation-highlight {
  animation: citationPulse 2s ease-in-out;
  background-color: rgba(79, 70, 229, 0.3) !important;
}

@keyframes citationPulse {
  0%, 100% {
    background-color: rgba(79, 70, 229, 0.3);
  }
  50% {
    background-color: rgba(79, 70, 229, 0.6);
  }
}

/* 애니메이션 완전 비활성화 */
@keyframes slideInMessageChat {
  from {
    opacity: 1 !important;
    transform: none !important;
  }
  to {
    opacity: 1 !important;
    transform: none !important;
  }
}

/* 마크다운 인라인 코드 스타일 */
.message-text :deep(.markdown-inline-code) {
  background: rgba(0, 0, 0, 0.08) !important;
  padding: 0.125rem 0.375rem !important;
  border-radius: 4px !important;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 0.875em !important;
  color: inherit !important;
  font-weight: 500 !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
}

.message-user .message-content .message-text :deep(.markdown-inline-code) {
  background: rgba(255, 255, 255, 0.25) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

/* 마크다운 코드 블록 스타일 */
.message-text :deep(.markdown-code-block) {
  background: rgba(0, 0, 0, 0.04) !important;
  padding: 1rem 1.25rem !important;
  border-radius: 8px !important;
  overflow-x: auto !important;
  margin: 1rem 0 !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Courier New', monospace !important;
  font-size: 0.875rem !important;
  line-height: 1.6 !important;
}

.message-user .message-content .message-text :deep(.markdown-code-block) {
  background: rgba(255, 255, 255, 0.18) !important;
  border-color: rgba(255, 255, 255, 0.25) !important;
}

.message-text :deep(.markdown-code) {
  background: none !important;
  padding: 0 !important;
  border: none !important;
  color: inherit !important;
  font-size: inherit !important;
}

/* 일반 code 태그 (class 없는 경우) - 인라인 코드 */
.message-text :deep(code:not([class])) {
  background-color: #f5f5f5 !important;
  color: #333 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.9em !important;
  font-weight: 400 !important;
  border: 1px solid #e0e0e0 !important;
}

/* 일반 code 태그가 pre 내부에 있는 경우 (코드 블록) */
.message-text :deep(pre code:not([class])) {
  display: block !important;
  width: 100% !important;
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-x: auto !important;
  background-color: #f5f5f5 !important;
  color: #333 !important;
  padding: 10px !important;
  border-radius: 4px !important;
  margin: 0 !important;
  border: 1px solid #e0e0e0 !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.875rem !important;
  line-height: 1.6 !important;
}

/* 일반 pre > code 블록 컨테이너 */
.message-text :deep(pre:has(code:not([class]))) {
  background-color: #f5f5f5 !important;
  padding: 0 !important;
  border-radius: 4px !important;
  margin: 12px 0 !important;
  border: 1px solid #e0e0e0 !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
}

/* 작은 화면에서 줄바꿈 처리 */
@media (max-width: 768px) {
  .message-text :deep(pre code:not([class])) {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
  }
}

/* 사용자 메시지의 일반 code 태그 */
.message-user .message-content .message-text :deep(code:not([class])) {
  background-color: rgba(245, 245, 245, 0.2) !important;
  color: #ffffff !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.message-user .message-content .message-text :deep(pre code:not([class])) {
  background-color: rgba(245, 245, 245, 0.15) !important;
  color: #ffffff !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}

/* Assistant 메시지의 일반 code 태그 */
.message-assistant .message-content .message-text :deep(code:not([class])) {
  background-color: #f5f5f5 !important;
  color: #333 !important;
  border-color: #e0e0e0 !important;
}

.message-assistant .message-content .message-text :deep(pre code:not([class])) {
  background-color: #f5f5f5 !important;
  color: #333 !important;
  border-color: #e0e0e0 !important;
}

/* 코드 블록 스크롤바 스타일 */
.message-text :deep(.markdown-code-block::-webkit-scrollbar) {
  height: 8px;
}

.message-text :deep(.markdown-code-block::-webkit-scrollbar-track) {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.message-text :deep(.markdown-code-block::-webkit-scrollbar-thumb) {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.message-text :deep(.markdown-code-block::-webkit-scrollbar-thumb:hover) {
  background: rgba(0, 0, 0, 0.3);
}

/* 마크다운 테이블 스타일 개선 */
.message-text :deep(.markdown-table) {
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  margin: 1.25rem 0 !important;
  font-size: 0.875rem !important;
  border-radius: 8px !important;
  overflow: hidden !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
}

.message-text :deep(.markdown-table th) {
  background-color: rgba(0, 0, 0, 0.06) !important;
  font-weight: 600 !important;
  padding: 0.875rem 1rem !important;
  text-align: left !important;
  border-bottom: 2px solid rgba(0, 0, 0, 0.1) !important;
  color: inherit !important;
}

.message-user .message-content .message-text :deep(.markdown-table th) {
  background-color: rgba(255, 255, 255, 0.15) !important;
  border-bottom-color: rgba(255, 255, 255, 0.3) !important;
}

.message-text :deep(.markdown-table td) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.08) !important;
  padding: 0.875rem 1rem !important;
  text-align: left !important;
  color: inherit !important;
  vertical-align: top !important;
}

.message-user .message-content .message-text :deep(.markdown-table td) {
  border-bottom-color: rgba(255, 255, 255, 0.15) !important;
}

.message-text :deep(.markdown-table tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.03) !important;
}

.message-user .message-content .message-text :deep(.markdown-table tbody tr:hover) {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.message-text :deep(.markdown-table tbody tr:last-child td) {
  border-bottom: none !important;
}

/* 마크다운 리스트 스타일 개선 */
.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 0.875rem 0 !important;
  padding-left: 1.5rem !important;
  color: inherit !important;
  list-style-position: outside !important;
}

.message-text :deep(ul) {
  list-style-type: disc !important;
}

.message-text :deep(ol) {
  list-style-type: decimal !important;
}

.message-text :deep(li) {
  margin: 0.375rem 0 !important;
  padding: 0.25rem 0.5rem !important;
  line-height: 1.65 !important;
  color: inherit !important;
  border-radius: 4px !important;
}

/* 어시스턴트 메시지의 리스트 항목 배경 */
.message-assistant .message-content .message-text :deep(li) {
  background-color: rgba(255, 255, 255, 0.5) !important;
  margin-left: -0.5rem !important;
  margin-right: 0.5rem !important;
}

/* 사용자 메시지의 리스트 항목 배경 */
.message-user .message-content .message-text :deep(li) {
  background-color: rgba(255, 255, 255, 0.12) !important;
  margin-left: -0.5rem !important;
  margin-right: 0.5rem !important;
}

.message-text :deep(li::marker) {
  color: inherit !important;
  opacity: 0.75;
  font-weight: 500;
}

/* 중첩 리스트 */
.message-text :deep(ul ul),
.message-text :deep(ol ol),
.message-text :deep(ul ol),
.message-text :deep(ol ul) {
  margin-top: 0.375rem !important;
  margin-bottom: 0.375rem !important;
  padding-left: 1.25rem !important;
}

/* 중첩 리스트 항목 */
.message-text :deep(li li) {
  margin: 0.25rem 0 !important;
  padding: 0.125rem 0.375rem !important;
}

/* 리스트 내부 단락 - 자연스러운 여백 */
.message-text :deep(li > p) {
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
}

.message-text :deep(ol li > p),
.message-text :deep(ul li > p) {
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
  display: inline !important;
}

.message-text :deep(li > p:not(:last-child)) {
  margin-bottom: 0.25rem !important;
}

.message-text :deep(ol li > p:not(:last-child)),
.message-text :deep(ul li > p:not(:last-child)) {
  margin-bottom: 0.25rem !important;
}

/* 마크다운 헤딩 스타일 (기존 h1-h6 스타일도 유지하되 markdown-heading 클래스 우선) */
.message-text :deep(.markdown-heading),
.message-text h1,
.message-text h2,
.message-text h3,
.message-text h4,
.message-text h5,
.message-text h6 {
  margin-top: 1.5rem !important;
  margin-bottom: 0.875rem !important;
  font-weight: 700 !important;
  line-height: 1.3 !important;
  color: inherit !important;
}

.message-text :deep(.markdown-h1),
.message-text h1 {
  font-size: 1.75rem !important;
  margin-top: 1.75rem !important;
  border-bottom: 2px solid rgba(0, 0, 0, 0.1) !important;
  padding-bottom: 0.5rem !important;
}

.message-user .message-content .message-text :deep(.markdown-h1),
.message-user .message-content .message-text h1 {
  border-bottom-color: rgba(255, 255, 255, 0.3) !important;
}

/* h2, h3, h4 헤딩 스타일 */
.message-text :deep(.markdown-h2),
.message-text h2 {
  font-size: 1.8rem !important;
  font-weight: bold !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
  line-height: 1.4 !important;
}

.message-user .message-content .message-text :deep(.markdown-h2),
.message-user .message-content .message-text h2 {
  color: #ffffff !important;
  border-bottom-color: rgba(255, 255, 255, 0.3) !important;
}

.message-text :deep(.markdown-h3),
.message-text h3 {
  font-size: 1.4rem !important;
  font-weight: 600 !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.4 !important;
}

.message-user .message-content .message-text :deep(.markdown-h3),
.message-user .message-content .message-text h3 {
  color: #ffffff !important;
}

.message-text :deep(.markdown-h4),
.message-text h4 {
  font-size: 1.2rem !important;
  font-weight: normal !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.5 !important;
}

.message-user .message-content .message-text :deep(.markdown-h4),
.message-user .message-content .message-text h4 {
  color: #ffffff !important;
}

/* assistant-message-text 내부 h2, h3, h4 스타일 */
.assistant-message-text :deep(.markdown-h2),
.assistant-message-text :deep(h2),
.assistant-message-text h2 {
  font-size: 1.8rem !important;
  font-weight: bold !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
  line-height: 1.4 !important;
}

.assistant-message-text :deep(.markdown-h3),
.assistant-message-text :deep(h3),
.assistant-message-text h3 {
  font-size: 1.4rem !important;
  font-weight: 600 !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.4 !important;
}

.assistant-message-text :deep(.markdown-h4),
.assistant-message-text :deep(h4),
.assistant-message-text h4 {
  font-size: 1.2rem !important;
  font-weight: normal !important;
  color: #333 !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.5 !important;
}

/* user-message-text 내부 h2, h3, h4 스타일 */
.user-message-text :deep(.markdown-h2),
.user-message-text :deep(h2),
.user-message-text h2 {
  font-size: 1.8rem !important;
  font-weight: bold !important;
  color: #ffffff !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  padding-bottom: 8px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3) !important;
  line-height: 1.4 !important;
}

.user-message-text :deep(.markdown-h3),
.user-message-text :deep(h3),
.user-message-text h3 {
  font-size: 1.4rem !important;
  font-weight: 600 !important;
  color: #ffffff !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.4 !important;
}

.user-message-text :deep(.markdown-h4),
.user-message-text :deep(h4),
.user-message-text h4 {
  font-size: 1.2rem !important;
  font-weight: normal !important;
  color: #ffffff !important;
  margin-top: 16px !important;
  margin-bottom: 8px !important;
  line-height: 1.5 !important;
}

/* 모바일에서 폰트 크기 90%로 조정 */
@media (max-width: 768px) {
  .message-text :deep(.markdown-h2),
  .message-text h2 {
    font-size: 1.62rem !important; /* 1.8rem * 0.9 */
  }
  
  .message-text :deep(.markdown-h3),
  .message-text h3 {
    font-size: 1.26rem !important; /* 1.4rem * 0.9 */
  }
  
  .message-text :deep(.markdown-h4),
  .message-text h4 {
    font-size: 1.08rem !important; /* 1.2rem * 0.9 */
  }
  
  /* assistant-message-text 모바일 */
  .assistant-message-text :deep(.markdown-h2),
  .assistant-message-text :deep(h2),
  .assistant-message-text h2 {
    font-size: 1.62rem !important; /* 1.8rem * 0.9 */
  }
  
  .assistant-message-text :deep(.markdown-h3),
  .assistant-message-text :deep(h3),
  .assistant-message-text h3 {
    font-size: 1.26rem !important; /* 1.4rem * 0.9 */
  }
  
  .assistant-message-text :deep(.markdown-h4),
  .assistant-message-text :deep(h4),
  .assistant-message-text h4 {
    font-size: 1.08rem !important; /* 1.2rem * 0.9 */
  }
  
  /* user-message-text 모바일 */
  .user-message-text :deep(.markdown-h2),
  .user-message-text :deep(h2),
  .user-message-text h2 {
    font-size: 1.62rem !important; /* 1.8rem * 0.9 */
  }
  
  .user-message-text :deep(.markdown-h3),
  .user-message-text :deep(h3),
  .user-message-text h3 {
    font-size: 1.26rem !important; /* 1.4rem * 0.9 */
  }
  
  .user-message-text :deep(.markdown-h4),
  .user-message-text :deep(h4),
  .user-message-text h4 {
    font-size: 1.08rem !important; /* 1.2rem * 0.9 */
  }
}

.message-text :deep(.markdown-h5),
.message-text h5 {
  font-size: 1rem !important;
  margin-top: 0.875rem !important;
}

.message-text :deep(.markdown-h6),
.message-text h6 {
  font-size: 0.875rem !important;
  margin-top: 0.75rem !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.8;
}

.message-text :deep(.markdown-heading:first-child),
.message-text h1:first-child,
.message-text h2:first-child,
.message-text h3:first-child {
  margin-top: 0 !important;
}

/* 마크다운 링크 스타일 */
.message-text :deep(.markdown-link),
.message-text a {
  color: #4F46E5 !important;
  text-decoration: none !important;
  border-bottom: 1px solid rgba(79, 70, 229, 0.3) !important;
  transition: all 0.2s ease !important;
  font-weight: 500 !important;
  word-break: break-all !important;
}

.message-user .message-content .message-text :deep(.markdown-link),
.message-user .message-content .message-text a {
  color: rgba(255, 255, 255, 0.95) !important;
  border-bottom-color: rgba(255, 255, 255, 0.4) !important;
}

.message-text :deep(.markdown-link:hover),
.message-text a:hover {
  color: #6366F1 !important;
  border-bottom-color: #6366F1 !important;
  text-decoration: none !important;
}

.message-user .message-content .message-text :deep(.markdown-link:hover),
.message-user .message-content .message-text a:hover {
  border-bottom-color: rgba(255, 255, 255, 0.6) !important;
}

/* 마크다운 인용구 스타일 */
.message-text :deep(.markdown-blockquote),
.message-text blockquote {
  border-left: 4px solid #4F46E5 !important;
  padding: 0.875rem 1.125rem !important;
  margin: 1rem 0 !important;
  background: rgba(79, 70, 229, 0.08) !important;
  border-radius: 6px !important;
  font-style: italic !important;
  color: inherit !important;
  line-height: 1.6 !important;
}

.message-user .message-content .message-text :deep(.markdown-blockquote),
.message-user .message-content .message-text blockquote {
  background: rgba(255, 255, 255, 0.15) !important;
  border-left-color: rgba(255, 255, 255, 0.6) !important;
}

.message-text :deep(.markdown-blockquote p:last-child),
.message-text blockquote p:last-child {
  margin-bottom: 0 !important;
}

/* 마크다운 구분선 스타일 */
.message-text :deep(.markdown-hr),
.message-text hr {
  border: none !important;
  border-top: 2px solid rgba(0, 0, 0, 0.12) !important;
  margin: 1.5rem 0 !important;
  opacity: 0.6 !important;
}

.message-user .message-content .message-text :deep(.markdown-hr),
.message-user .message-content .message-text hr {
  border-top-color: rgba(255, 255, 255, 0.35) !important;
}

/* Python 코드 가독성 개선 - 다크 테마 */
/* Python 코드 블록 컨테이너 (pre 태그) */
.message-text :deep(pre:has(code.language-python)) {
  background-color: #2d2d2d !important;
  padding: 12px !important;
  border-radius: 6px !important;
  margin: 16px 0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  position: relative !important;
}

/* Python 코드 블록 내부 (code 태그) - Prism.js와 통합 */
.message-text :deep(pre code.language-python),
.message-text :deep(pre.language-python code) {
  display: block !important;
  width: 100% !important;
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-x: auto !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  margin: 0 !important;
  color: #f8f8f2 !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
  letter-spacing: 0.01em !important;
  tab-size: 4 !important;
  -moz-tab-size: 4 !important;
  font-weight: 400 !important;
}

/* Prism.js 토큰 스타일 오버라이드 - Python */
.message-text :deep(pre code.language-python .token.keyword),
.message-text :deep(pre.language-python code .token.keyword) {
  color: #66d9ef !important;
  font-weight: 600 !important;
}

.message-text :deep(pre code.language-python .token.string),
.message-text :deep(pre.language-python code .token.string) {
  color: #e6db74 !important;
}

.message-text :deep(pre code.language-python .token.number),
.message-text :deep(pre.language-python code .token.number) {
  color: #ae81ff !important;
}

.message-text :deep(pre code.language-python .token.comment),
.message-text :deep(pre.language-python code .token.comment) {
  color: #75715e !important;
  font-style: italic !important;
}

.message-text :deep(pre code.language-python .token.function),
.message-text :deep(pre.language-python code .token.function) {
  color: #a6e22e !important;
}

/* Python 인라인 코드 (블록이 아닌 경우) */
.message-text :deep(code.language-python:not(pre code)) {
  background-color: #2d2d2d !important;
  color: #f8f8f2 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-size: 0.9em !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
}

/* Python 키워드 색상 (CSS 선택자로 가능한 범위) */
.message-text :deep(code.language-python .keyword),
.message-text :deep(code.language-python .kwd) {
  color: #66d9ef !important;
  font-weight: 600 !important;
}

/* Python 문자열 색상 */
.message-text :deep(code.language-python .string),
.message-text :deep(code.language-python .str) {
  color: #e6db74 !important;
}

/* Python 숫자 색상 */
.message-text :deep(code.language-python .number),
.message-text :deep(code.language-python .num) {
  color: #ae81ff !important;
}

/* Python 주석 색상 */
.message-text :deep(code.language-python .comment),
.message-text :deep(code.language-python .cmt) {
  color: #75715e !important;
  font-style: italic !important;
}

/* Python 함수/클래스 이름 */
.message-text :deep(code.language-python .function),
.message-text :deep(code.language-python .fn) {
  color: #a6e22e !important;
}

/* Python 변수 */
.message-text :deep(code.language-python .variable),
.message-text :deep(code.language-python .var) {
  color: #f8f8f2 !important;
}

/* 사용자 메시지의 Python 코드 블록 */
.message-user .message-content .message-text :deep(pre:has(code.language-python)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.message-user .message-content .message-text :deep(pre code.language-python) {
  color: #f8f8f2 !important;
}

.message-user .message-content .message-text :deep(code.language-python:not(pre code)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  color: #f8f8f2 !important;
}

/* Assistant 메시지의 Python 코드 블록 */
.message-assistant .message-content .message-text :deep(pre:has(code.language-python)) {
  background-color: #2d2d2d !important;
  border-left: 4px solid #3776ab !important;
}

.message-assistant .message-content .message-text :deep(pre code.language-python) {
  color: #f8f8f2 !important;
}

/* 작은 화면에서 줄바꿈 처리 */
@media (max-width: 768px) {
  .message-text :deep(pre code.language-python) {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
  }
}

/* 코드 블록 스크롤바 스타일링 */
.message-text :deep(pre code.language-python)::-webkit-scrollbar {
  height: 8px;
}

.message-text :deep(pre code.language-python)::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 4px;
}

.message-text :deep(pre code.language-python)::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.message-text :deep(pre code.language-python)::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* Java 코드 가독성 개선 - 다크 테마 */
/* Java 코드 블록 컨테이너 (pre 태그) */
.message-text :deep(pre:has(code.language-java)) {
  background-color: #2d2d2d !important;
  padding: 12px !important;
  border-radius: 6px !important;
  margin: 16px 0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  position: relative !important;
}

/* Java 코드 블록 내부 (code 태그) */
.message-text :deep(pre code.language-java) {
  display: block !important;
  width: 100% !important;
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-x: auto !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  margin: 0 !important;
  color: #f8f8f2 !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
  letter-spacing: 0.01em !important;
  tab-size: 4 !important;
  -moz-tab-size: 4 !important;
  font-weight: 400 !important;
}

/* Java 인라인 코드 (블록이 아닌 경우) */
.message-text :deep(code.language-java:not(pre code)) {
  background-color: #2d2d2d !important;
  color: #f8f8f2 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-size: 0.9em !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
}

/* Java Prism.js 토큰 스타일 - 모든 토큰 명시적 색상 지정 */
/* Java 키워드 (public, class, static, void, int 등) */
.message-text :deep(pre code.language-java .token.keyword),
.message-text :deep(pre.language-java code .token.keyword),
.message-text :deep(code.language-java .token.keyword) {
  color: #66d9ef !important;
  font-weight: 600 !important;
}

/* Java 자료형 (int, String, boolean, double 등) */
.message-text :deep(pre code.language-java .token.type),
.message-text :deep(pre.language-java code .token.type),
.message-text :deep(code.language-java .token.type),
.message-text :deep(pre code.language-java .token.builtin),
.message-text :deep(pre.language-java code .token.builtin) {
  color: #66d9ef !important;
  font-weight: 500 !important;
  font-style: italic !important;
}

/* Java 연산자 (+, -, *, /, =, ==, !=, <, >, <=, >= 등) */
.message-text :deep(pre code.language-java .token.operator),
.message-text :deep(pre.language-java code .token.operator),
.message-text :deep(code.language-java .token.operator) {
  color: #f8f8f2 !important;
  font-weight: 500 !important;
}

/* Java 구두점 (;, ., ,, {, }, [, ], (, ) 등) */
.message-text :deep(pre code.language-java .token.punctuation),
.message-text :deep(pre.language-java code .token.punctuation),
.message-text :deep(code.language-java .token.punctuation) {
  color: #f8f8f2 !important;
  font-weight: 400 !important;
}

/* Java 문자열 */
.message-text :deep(pre code.language-java .token.string),
.message-text :deep(pre.language-java code .token.string),
.message-text :deep(code.language-java .token.string) {
  color: #a6e22e !important;
}

/* Java 숫자 */
.message-text :deep(pre code.language-java .token.number),
.message-text :deep(pre.language-java code .token.number),
.message-text :deep(code.language-java .token.number) {
  color: #ae81ff !important;
}

/* Java 주석 */
.message-text :deep(pre code.language-java .token.comment),
.message-text :deep(pre.language-java code .token.comment),
.message-text :deep(code.language-java .token.comment) {
  color: #75715e !important;
  font-style: italic !important;
}

/* Java 클래스/인터페이스 이름 */
.message-text :deep(pre code.language-java .token.class-name),
.message-text :deep(pre.language-java code .token.class-name),
.message-text :deep(code.language-java .token.class-name) {
  color: #e5c07b !important;
  font-weight: 500 !important;
}

/* Java 메서드/함수 이름 */
.message-text :deep(pre code.language-java .token.function),
.message-text :deep(pre.language-java code .token.function),
.message-text :deep(code.language-java .token.function) {
  color: #61afef !important;
  font-weight: 500 !important;
}

/* Java 변수 */
.message-text :deep(pre code.language-java .token.variable),
.message-text :deep(pre.language-java code .token.variable),
.message-text :deep(code.language-java .token.variable) {
  color: #f8f8f2 !important;
}

/* Java 불린값 (true, false) */
.message-text :deep(pre code.language-java .token.boolean),
.message-text :deep(pre.language-java code .token.boolean),
.message-text :deep(code.language-java .token.boolean) {
  color: #ae81ff !important;
  font-weight: 600 !important;
}

/* Java 상수 (null, this, super 등) */
.message-text :deep(pre code.language-java .token.constant),
.message-text :deep(pre.language-java code .token.constant),
.message-text :deep(code.language-java .token.constant) {
  color: #66d9ef !important;
  font-weight: 600 !important;
}

/* Java 속성/필드 */
.message-text :deep(pre code.language-java .token.property),
.message-text :deep(pre.language-java code .token.property),
.message-text :deep(code.language-java .token.property) {
  color: #f8f8f2 !important;
}

/* Java 네임스페이스/패키지 */
.message-text :deep(pre code.language-java .token.namespace),
.message-text :deep(pre.language-java code .token.namespace),
.message-text :deep(code.language-java .token.namespace) {
  color: #e5c07b !important;
}

/* 기본 텍스트 색상 (토큰이 지정되지 않은 경우) */
.message-text :deep(pre code.language-java),
.message-text :deep(pre.language-java code),
.message-text :deep(code.language-java) {
  color: #f8f8f2 !important;
}

/* 사용자 메시지의 Java 토큰들 */
.message-user .message-content .message-text :deep(pre code.language-java .token.operator),
.message-user .message-content .message-text :deep(pre code.language-java .token.punctuation) {
  color: #ffffff !important;
}

/* 사용자 메시지의 Java 코드 블록 */
.message-user .message-content .message-text :deep(pre:has(code.language-java)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.message-user .message-content .message-text :deep(pre code.language-java) {
  color: #f8f8f2 !important;
}

.message-user .message-content .message-text :deep(code.language-java:not(pre code)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  color: #f8f8f2 !important;
}

/* Assistant 메시지의 Java 코드 블록 */
.message-assistant .message-content .message-text :deep(pre:has(code.language-java)) {
  background-color: #2d2d2d !important;
  border-left: 4px solid #f89820 !important; /* Java 오렌지 색상 */
}

.message-assistant .message-content .message-text :deep(pre code.language-java) {
  color: #f8f8f2 !important;
}

/* 작은 화면에서 줄바꿈 처리 */
@media (max-width: 768px) {
  .message-text :deep(pre code.language-java) {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
  }
}

/* 코드 블록 스크롤바 스타일링 */
.message-text :deep(pre code.language-java)::-webkit-scrollbar {
  height: 8px;
}

.message-text :deep(pre code.language-java)::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 4px;
}

.message-text :deep(pre code.language-java)::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.message-text :deep(pre code.language-java)::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* C# 코드 가독성 개선 - 다크 테마 */
/* C# 코드 블록 컨테이너 (pre 태그) */
.message-text :deep(pre:has(code.language-csharp)) {
  background-color: #2d2d2d !important;
  padding: 12px !important;
  border-radius: 8px !important;
  margin: 16px 0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  position: relative !important;
}

/* C# 코드 블록 포커스/선택 강조 */
.message-text :deep(pre:has(code.language-csharp):focus) {
  outline: 2px solid rgba(97, 175, 239, 0.5) !important;
  outline-offset: 2px !important;
}

.message-text :deep(pre:has(code.language-csharp):focus-within) {
  outline: 2px solid rgba(97, 175, 239, 0.3) !important;
  outline-offset: 2px !important;
}

/* C# 코드 블록 내부 (code 태그) */
.message-text :deep(pre code.language-csharp) {
  display: block !important;
  width: 100% !important;
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-x: auto !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  margin: 0 !important;
  color: #f8f8f2 !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
  letter-spacing: 0.01em !important;
  tab-size: 4 !important;
  -moz-tab-size: 4 !important;
  font-weight: 400 !important;
}

/* C# 인라인 코드 (블록이 아닌 경우) */
.message-text :deep(code.language-csharp:not(pre code)) {
  background-color: #2d2d2d !important;
  color: #f8f8f2 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-size: 0.9em !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  tab-size: 4 !important;
  -moz-tab-size: 4 !important;
}

/* C# 키워드 색상 (public, class, async, await, var 등) */
.message-text :deep(code.language-csharp .keyword),
.message-text :deep(code.language-csharp .kwd) {
  color: #56b6c2 !important;
  font-weight: 600 !important;
}

/* C# 형식/클래스/네임스페이스 (class-name, namespace) */
.message-text :deep(code.language-csharp .class-name),
.message-text :deep(code.language-csharp .clazz),
.message-text :deep(code.language-csharp .namespace),
.message-text :deep(code.language-csharp .type) {
  color: #e5c07b !important;
  font-weight: 500 !important;
}

/* C# 메서드/함수 (function) */
.message-text :deep(code.language-csharp .function),
.message-text :deep(code.language-csharp .method) {
  color: #61afef !important;
  font-weight: 500 !important;
}

/* C# 문자열 (string) */
.message-text :deep(code.language-csharp .string),
.message-text :deep(code.language-csharp .str) {
  color: #98c379 !important;
}

/* C# 숫자 (number) */
.message-text :deep(code.language-csharp .number),
.message-text :deep(code.language-csharp .num) {
  color: #d19a66 !important;
}

/* C# 주석 (comment, xml-doc 포함) */
.message-text :deep(code.language-csharp .comment),
.message-text :deep(code.language-csharp .cmt),
.message-text :deep(code.language-csharp .xml-doc) {
  color: #7f848e !important;
  font-style: italic !important;
}

/* C# 속성/어노테이션 (annotation, attribute) */
.message-text :deep(code.language-csharp .annotation),
.message-text :deep(code.language-csharp .attribute),
.message-text :deep(code.language-csharp .attr) {
  color: #c678dd !important;
}

/* C# 전처리 지시문 (preprocessor) */
.message-text :deep(code.language-csharp .preprocessor),
.message-text :deep(code.language-csharp .pp),
.message-text :deep(code.language-csharp .directive) {
  color: #be5046 !important;
}

/* C# 연산자/구두점 (operator/punctuation) - 기본색 유지 */
.message-text :deep(code.language-csharp .operator),
.message-text :deep(code.language-csharp .punctuation) {
  color: #f8f8f2 !important;
}

/* C# 변수 */
.message-text :deep(code.language-csharp .variable),
.message-text :deep(code.language-csharp .var) {
  color: #f8f8f2 !important;
}

/* 사용자 메시지의 C# 코드 블록 */
.message-user .message-content .message-text :deep(pre:has(code.language-csharp)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.message-user .message-content .message-text :deep(pre code.language-csharp) {
  color: #f8f8f2 !important;
}

.message-user .message-content .message-text :deep(code.language-csharp:not(pre code)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  color: #f8f8f2 !important;
}

/* Assistant 메시지의 C# 코드 블록 */
.message-assistant .message-content .message-text :deep(pre:has(code.language-csharp)) {
  background-color: #2d2d2d !important;
  border-left: 4px solid #68217a !important; /* C# 보라색 */
}

.message-assistant .message-content .message-text :deep(pre code.language-csharp) {
  color: #f8f8f2 !important;
}

/* 작은 화면에서 줄바꿈 처리 및 폰트 크기 조정 */
@media (max-width: 768px) {
  .message-text :deep(pre code.language-csharp) {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    font-size: 0.81rem !important; /* 0.9rem * 0.9 = 90% */
  }
  
  .message-text :deep(code.language-csharp:not(pre code)) {
    font-size: 0.81em !important; /* 0.9em * 0.9 = 90% */
  }
}

/* C# 코드 블록 스크롤바 스타일링 */
.message-text :deep(pre code.language-csharp)::-webkit-scrollbar {
  height: 8px;
}

.message-text :deep(pre code.language-csharp)::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 4px;
}

.message-text :deep(pre code.language-csharp)::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.message-text :deep(pre code.language-csharp)::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* HTML 코드 블록 스타일 */
/* HTML 코드 블록 컨테이너 (pre 태그) */
.message-text :deep(pre:has(code.language-html)) {
  background-color: #2d2d2d !important;
  padding: 12px !important;
  border-radius: 8px !important;
  margin: 16px 0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  position: relative !important;
}

/* HTML 코드 블록 포커스/선택 강조 */
.message-text :deep(pre:has(code.language-html):focus) {
  outline: 2px solid rgba(224, 108, 117, 0.5) !important;
  outline-offset: 2px !important;
}

.message-text :deep(pre:has(code.language-html):focus-within) {
  outline: 2px solid rgba(224, 108, 117, 0.3) !important;
  outline-offset: 2px !important;
}

.message-text :deep(pre code.language-html) {
  display: block !important;
  width: 100% !important;
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-x: auto !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  margin: 0 !important;
  color: #f8f8f2 !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
  letter-spacing: 0.01em !important;
  tab-size: 4 !important;
  -moz-tab-size: 4 !important;
  font-weight: 400 !important;
}

/* HTML 인라인 코드 (블록이 아닌 경우) */
.message-text :deep(code.language-html:not(pre code)) {
  background-color: #2d2d2d !important;
  color: #f8f8f2 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-size: 0.9em !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
}

/* HTML 코드 블록 - Prism.js를 사용하지 않으므로 간단한 스타일만 적용 */
/* 모든 HTML 코드는 기본 텍스트 색상으로 표시되며, < > 기호도 명확히 보임 */
.message-text :deep(pre code.language-html),
.message-text :deep(pre.language-html code),
.message-text :deep(code.language-html) {
  color: #f8f8f2 !important;
}

/* HTML 코드 블록 내부의 모든 텍스트 노드가 명확히 보이도록 - < > 기호 포함 */
.message-text :deep(pre code.language-html *),
.message-text :deep(pre.language-html code *),
.message-text :deep(code.language-html *) {
  color: #f8f8f2 !important;
  opacity: 1 !important;
}

/* HTML 선택 색상 (접근성) */
.message-text :deep(pre code.language-html::selection) {
  background-color: rgba(224, 108, 117, 0.3) !important;
  color: #ffffff !important;
}

.message-text :deep(pre code.language-html::-moz-selection) {
  background-color: rgba(224, 108, 117, 0.3) !important;
  color: #ffffff !important;
}

/* 사용자 메시지의 HTML 코드 블록 */
.message-user .message-content .message-text :deep(pre:has(code.language-html)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.message-user .message-content .message-text :deep(pre code.language-html) {
  color: #f8f8f2 !important;
}

.message-user .message-content .message-text :deep(code.language-html:not(pre code)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  color: #f8f8f2 !important;
}

/* Assistant 메시지의 HTML 코드 블록 */
.message-assistant .message-content .message-text :deep(pre:has(code.language-html)) {
  background-color: #2d2d2d !important;
  border-left: 4px solid #e06c75 !important; /* HTML 태그 색상 */
}

.message-assistant .message-content .message-text :deep(pre code.language-html) {
  color: #f8f8f2 !important;
}

/* 모바일 반응형 (768px 이하) */
@media (max-width: 768px) {
  .message-text :deep(pre code.language-html) {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    font-size: 0.81rem !important;
  }
  .message-text :deep(code.language-html:not(pre code)) {
    font-size: 0.81em !important;
  }
}

/* HTML 코드 블록 스크롤바 스타일 */
.message-text :deep(pre code.language-html)::-webkit-scrollbar {
  height: 8px;
}

.message-text :deep(pre code.language-html)::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 4px;
}

.message-text :deep(pre code.language-html)::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.message-text :deep(pre code.language-html)::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* 라인 넘버 스타일 (Prism line-numbers 플러그인 사용 시) */
.message-text :deep(pre.line-numbers:has(code.language-html)) {
  position: relative !important;
  padding-left: 3.8em !important;
  counter-reset: linenumber !important;
}

.message-text :deep(pre.line-numbers:has(code.language-html) > code) {
  position: relative !important;
  white-space: inherit !important;
}

.message-text :deep(pre.line-numbers:has(code.language-html) .line-numbers-rows) {
  position: absolute !important;
  pointer-events: none !important;
  top: 0 !important;
  font-size: 100% !important;
  left: -3.8em !important;
  width: 3em !important;
  letter-spacing: -1px !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
  user-select: none !important;
  padding-top: 12px !important;
  padding-bottom: 12px !important;
}

.message-text :deep(pre.line-numbers:has(code.language-html) .line-numbers-rows > span) {
  display: block !important;
  counter-increment: linenumber !important;
  padding-right: 0.8em !important;
  text-align: right !important;
  color: #7f848e !important;
}

/* SQL 코드 블록 스타일 */
/* SQL 코드 블록 컨테이너 (pre 태그) */
.message-text :deep(pre:has(code.language-sql)) {
  background-color: #2d2d2d !important;
  padding: 12px !important;
  border-radius: 8px !important;
  margin: 16px 0 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  overflow-x: auto !important;
  overflow-y: visible !important;
  position: relative !important;
}

/* SQL 코드 블록 포커스/선택 강조 */
.message-text :deep(pre:has(code.language-sql):focus) {
  outline: 2px solid rgba(86, 182, 194, 0.5) !important;
  outline-offset: 2px !important;
}

.message-text :deep(pre:has(code.language-sql):focus-within) {
  outline: 2px solid rgba(86, 182, 194, 0.3) !important;
  outline-offset: 2px !important;
}

.message-text :deep(pre code.language-sql) {
  display: block !important;
  width: 100% !important;
  white-space: pre !important;
  word-wrap: normal !important;
  overflow-x: auto !important;
  background-color: transparent !important;
  padding: 0 !important;
  border: none !important;
  margin: 0 !important;
  color: #f8f8f2 !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
  font-size: 0.9rem !important;
  line-height: 1.7 !important;
  letter-spacing: 0.01em !important;
  tab-size: 4 !important;
  -moz-tab-size: 4 !important;
  font-weight: 400 !important;
}

/* SQL 인라인 코드 (블록이 아닌 경우) */
.message-text :deep(code.language-sql:not(pre code)) {
  background-color: #2d2d2d !important;
  color: #f8f8f2 !important;
  padding: 2px 6px !important;
  border-radius: 4px !important;
  font-size: 0.9em !important;
  font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', 'SF Mono', 'Menlo', monospace !important;
}

/* SQL Prism.js 토큰 스타일 */
/* SQL 키워드 (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, WITH 등) */
.message-text :deep(pre code.language-sql .token.keyword),
.message-text :deep(pre.language-sql code .token.keyword),
.message-text :deep(code.language-sql .token.keyword) {
  color: #56b6c2 !important;
  font-weight: 600 !important;
}

/* SQL 함수/집계 (COUNT, SUM, AVG, MIN, MAX 등) */
.message-text :deep(pre code.language-sql .token.function),
.message-text :deep(pre.language-sql code .token.function),
.message-text :deep(code.language-sql .token.function),
.message-text :deep(pre code.language-sql .token.builtin),
.message-text :deep(pre.language-sql code .token.builtin),
.message-text :deep(code.language-sql .token.builtin) {
  color: #61afef !important;
  font-weight: 500 !important;
}

/* SQL 테이블/컬럼 식별자 (identifier, class-name) */
.message-text :deep(pre code.language-sql .token.class-name),
.message-text :deep(pre.language-sql code .token.class-name),
.message-text :deep(code.language-sql .token.class-name),
.message-text :deep(pre code.language-sql .token.identifier),
.message-text :deep(pre.language-sql code .token.identifier),
.message-text :deep(code.language-sql .token.identifier) {
  color: #e5c07b !important;
  font-weight: 500 !important;
}

/* SQL 문자열 (string) */
.message-text :deep(pre code.language-sql .token.string),
.message-text :deep(pre.language-sql code .token.string),
.message-text :deep(code.language-sql .token.string) {
  color: #98c379 !important;
}

/* SQL 숫자 (number) */
.message-text :deep(pre code.language-sql .token.number),
.message-text :deep(pre.language-sql code .token.number),
.message-text :deep(code.language-sql .token.number) {
  color: #d19a66 !important;
}

/* SQL 연산자 및 구두점 (operator, punctuation) - 기본색 유지 */
.message-text :deep(pre code.language-sql .token.operator),
.message-text :deep(pre.language-sql code .token.operator),
.message-text :deep(code.language-sql .token.operator),
.message-text :deep(pre code.language-sql .token.punctuation),
.message-text :deep(pre.language-sql code .token.punctuation),
.message-text :deep(code.language-sql .token.punctuation) {
  color: #f8f8f2 !important;
  font-weight: 400 !important;
}

/* SQL 주석 (comment: -- 또는 주석 블록) */
.message-text :deep(pre code.language-sql .token.comment),
.message-text :deep(pre.language-sql code .token.comment),
.message-text :deep(code.language-sql .token.comment) {
  color: #7f848e !important;
  font-style: italic !important;
}

/* SQL 선택 색상 (접근성) */
.message-text :deep(pre code.language-sql::selection) {
  background-color: rgba(86, 182, 194, 0.3) !important;
  color: #ffffff !important;
}

.message-text :deep(pre code.language-sql::-moz-selection) {
  background-color: rgba(86, 182, 194, 0.3) !important;
  color: #ffffff !important;
}

/* 사용자 메시지의 SQL 코드 블록 */
.message-user .message-content .message-text :deep(pre:has(code.language-sql)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

.message-user .message-content .message-text :deep(pre code.language-sql) {
  color: #f8f8f2 !important;
}

.message-user .message-content .message-text :deep(code.language-sql:not(pre code)) {
  background-color: rgba(45, 45, 45, 0.9) !important;
  color: #f8f8f2 !important;
}

/* Assistant 메시지의 SQL 코드 블록 */
.message-assistant .message-content .message-text :deep(pre:has(code.language-sql)) {
  background-color: #2d2d2d !important;
  border-left: 4px solid #56b6c2 !important; /* SQL 키워드 색상 */
}

.message-assistant .message-content .message-text :deep(pre code.language-sql) {
  color: #f8f8f2 !important;
}

/* 모바일 반응형 (768px 이하) */
@media (max-width: 768px) {
  .message-text :deep(pre code.language-sql) {
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    font-size: 0.81rem !important;
  }
  .message-text :deep(code.language-sql:not(pre code)) {
    font-size: 0.81em !important;
  }
}

/* SQL 코드 블록 스크롤바 스타일 */
.message-text :deep(pre code.language-sql)::-webkit-scrollbar {
  height: 8px;
}

.message-text :deep(pre code.language-sql)::-webkit-scrollbar-track {
  background: #1e1e1e;
  border-radius: 4px;
}

.message-text :deep(pre code.language-sql)::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.message-text :deep(pre code.language-sql)::-webkit-scrollbar-thumb:hover {
  background: #777;
}

/* 라인 넘버 스타일 (Prism line-numbers 플러그인 사용 시) */
.message-text :deep(pre.line-numbers:has(code.language-sql)) {
  position: relative !important;
  padding-left: 3.8em !important;
  counter-reset: linenumber !important;
}

.message-text :deep(pre.line-numbers:has(code.language-sql) > code) {
  position: relative !important;
  white-space: inherit !important;
}

.message-text :deep(pre.line-numbers:has(code.language-sql) .line-numbers-rows) {
  position: absolute !important;
  pointer-events: none !important;
  top: 0 !important;
  font-size: 100% !important;
  left: -3.8em !important;
  width: 3em !important;
  letter-spacing: -1px !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
  user-select: none !important;
  padding-top: 12px !important;
  padding-bottom: 12px !important;
}

.message-text :deep(pre.line-numbers:has(code.language-sql) .line-numbers-rows > span) {
  display: block !important;
  counter-increment: linenumber !important;
  padding-right: 0.8em !important;
  text-align: right !important;
  color: #7f848e !important;
}
</style>
