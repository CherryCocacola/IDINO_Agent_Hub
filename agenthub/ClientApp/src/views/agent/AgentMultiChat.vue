<template>
  <div class="mc-page-wrap">
    <!-- 좌측 사이드바 - 채팅 목록 -->
    <div class="mc-chat-sidebar">
      <div class="mc-sidebar-header">
        <button class="btn btn-primary w-100" @click="createNewChat">
          <i class="bi bi-plus-lg"></i> 새 채팅
        </button>
      </div>
      
      <div class="mc-chat-list">
        <div
          v-for="chat in chats"
          :key="chat.id"
          class="mc-chat-item"
          :class="{ active: currentChatId === chat.id }"
          @click="selectChat(chat.id)"
        >
          <span 
            v-if="chat.service?.colorCode" 
            class="mc-chat-item-svc" 
            :style="{ backgroundColor: chat.service.colorCode }"
          >
            <i :class="chat.service.iconClass || 'bi bi-cpu'"></i>
            {{ chat.service.serviceName }}
          </span>
          <div class="mc-chat-item-title">
            <i v-if="chat.isPinned" class="bi bi-pin-fill me-1 text-warning"></i>
            {{ chat.title || '새 채팅' }}
          </div>
          <div class="mc-chat-item-preview">{{ chat.preview || (chat.messageCount && chat.messageCount > 0 ? `${chat.messageCount}개 메시지` : '새로운 대화') }}</div>
          <div class="mc-chat-item-time">{{ formatChatTime(chat.updatedAt) }}</div>
          <button
            class="mc-chat-item-del"
            @click.stop="deleteChat(chat.id)"
            title="채팅 삭제"
          >
            <i class="bi bi-trash"></i>
          </button>
        </div>
        <div v-if="chats.length === 0" class="p-3 text-center text-muted">
          <small>채팅이 없습니다. 새 채팅을 시작하세요.</small>
        </div>
      </div>
    </div>

    <!-- 우측 채팅 영역 -->
    <div class="mc-chat-container-wrap">
      <div class="mc-chat-container">
          <!-- 채팅 헤더 -->
          <div class="mc-chat-header">
            <div class="mc-header-top">
              <div class="mc-header-title-area">
                <h6 class="mc-chat-title">{{ currentChat?.title || '새 채팅' }}</h6>
                <span 
                  v-if="currentChat?.service"
                  class="mc-service-badge"
                  :style="{ backgroundColor: currentChat.service.colorCode || 'var(--ai-primary)' }"
                >
                  <i :class="[currentChat.service.iconClass || 'bi bi-cpu', 'me-1']"></i>
                  {{ currentChat.service.serviceName }}
                </span>
              </div>
              <div class="mc-header-actions">
                <button class="btn btn-sm btn-outline-secondary" @click="showSettingsModal = true" title="설정">
                  <i class="bi bi-sliders"></i>
                </button>
                <button
                  v-if="currentChatId"
                  class="btn btn-sm btn-outline-danger"
                  @click="deleteChat(currentChatId)"
                  title="채팅 삭제"
                >
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
            
            <!-- 트랙 #97-post4 (2026-05-18): 외부/내부 LLM 탭 분기 -->
            <div class="mc-svc-tabs">
              <button
                type="button"
                class="mc-svc-tab"
                :class="{ 'mc-svc-tab-active': activeServiceTab === 'external' }"
                @click="activeServiceTab = 'external'"
                :title="$t('multiChat.externalLlmTitle') || '외부 인터넷 LLM (OpenAI / Claude / Gemini / Perplexity 등)'"
              >
                <i class="bi bi-globe me-1"></i>
                <span>{{ $t('multiChat.externalLlm') || '외부 LLM' }}</span>
                <span class="mc-svc-tab-badge">{{ externalActiveCount }}</span>
              </button>
              <button
                type="button"
                class="mc-svc-tab"
                :class="{ 'mc-svc-tab-active': activeServiceTab === 'internal' }"
                @click="activeServiceTab = 'internal'"
                :title="$t('multiChat.internalLlmTitle') || '내부 LAN-only LLM (Project Nexus)'"
              >
                <i class="bi bi-hdd-network me-1"></i>
                <span>{{ $t('multiChat.internalLlm') || '내부 LLM' }}</span>
                <span class="mc-svc-tab-badge">{{ internalActiveCount }}</span>
              </button>
            </div>
            <div class="mc-svc-grid">
              <button
                v-for="service in filteredServices"
                :key="service.serviceId"
                type="button"
                class="mc-svc-btn"
                :class="{ 'mc-svc-active': currentChat?.service?.serviceId === service.serviceId }"
                @click="switchService(service)"
                :title="service.serviceName"
                :style="currentChat?.service?.serviceId === service.serviceId ? {
                  borderColor: service.colorCode || 'var(--ai-primary)',
                  backgroundColor: service.colorCode || 'var(--ai-primary)',
                  color: '#fff'
                } : {}"
              >
                <i :class="service.iconClass || 'bi bi-cpu'"></i>
                <span class="ms-1">{{ service.serviceName }}</span>
              </button>
              <!-- 빈 탭 안내 -->
              <div v-if="filteredServices.length === 0" class="mc-svc-empty">
                <i class="bi bi-info-circle me-1"></i>
                <span v-if="activeServiceTab === 'external'">
                  {{ $t('multiChat.noExternalLlm') || '사용 가능한 외부 LLM 이 없습니다. 운영자 콘솔에서 API 키를 등록해 주세요.' }}
                </span>
                <span v-else>
                  {{ $t('multiChat.noInternalLlm') || '사용 가능한 내부 LLM 이 없습니다. (Nexus 미설정)' }}
                </span>
              </div>
            </div>
          </div>

          <!-- 채팅 메시지 영역 -->
          <div class="mc-messages" ref="chatBody">
            <!-- 빈 상태 -->
            <div v-if="!currentChatId || currentMessages.length === 0" class="mc-empty-chat">
              <i class="bi bi-chat-dots"></i>
              <h5>새로운 대화를 시작하세요</h5>
              <p class="text-muted">아래에 메시지를 입력하여 AI와 대화를 시작할 수 있습니다.</p>
              <div class="mc-empty-prompts">
                <button
                  v-for="(prompt, index) in suggestedPrompts"
                  :key="index"
                  class="btn btn-sm btn-outline-primary"
                  @click="useSuggestedPrompt(prompt.text)"
                >
                  {{ prompt.icon }} {{ prompt.label }}
                </button>
              </div>
            </div>
            
            <!-- 날짜 구분선 -->
            <div v-if="currentMessages.length > 0" class="mc-date-divider">
              <span>{{ new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' }) }}</span>
            </div>
            
            <!-- 메시지들 -->
            <template v-for="message in currentMessages" :key="message.messageId || message.tempId">
              <div
                :class="['mc-msg', message.role === 'user' ? 'mc-msg-user' : 'mc-msg-assistant']"
              >
                <!-- 트랙 #97-post5 — 발화 출처 영구 보존: 메시지의 originXxx 우선, 없으면 currentChat fallback -->
                <div
                  v-if="message.role === 'assistant'"
                  class="mc-msg-avatar"
                  :style="{ backgroundColor: message.originColorCode || currentChat?.service?.colorCode || 'var(--ai-primary)' }"
                >
                  <i :class="message.originIconClass || currentChat?.service?.iconClass || 'bi bi-robot'"></i>
                </div>
                <div class="mc-msg-content">
                  <div class="mc-msg-header">
                    <strong>{{ message.role === 'user' ? '나' : (message.originServiceName || currentChat?.service?.serviceName || 'AI') }}</strong>
                    <small v-if="message.originModel" class="ms-2 text-muted" style="font-size: 11px;">{{ message.originModel }}</small>
                    <small class="ms-2">{{ formatTime(message.createdAt) }}</small>
                  </div>
                  <!-- 메시지 첨부파일 -->
                  <div v-if="message.attachments && message.attachments.length > 0" class="message-attachments mb-2">
                    <div v-for="(attachment, idx) in message.attachments" :key="idx" class="mb-1">
                      <a v-if="attachment.type === 'file'" :href="getFileDownloadUrl(attachment.url)" target="_blank" class="badge bg-secondary text-decoration-none me-1" @click.prevent="downloadFile(attachment)">
                        <i class="bi bi-file-earmark me-1"></i>{{ attachment.name }}
                      </a>
                      <div v-else-if="attachment.type === 'image'" class="message-image-wrapper" style="position: relative; display: inline-block; max-width: 100%;">
                        <img 
                          :src="getImageSource(attachment)" 
                          :alt="attachment.name" 
                          style="max-width: 300px; max-height: 300px; border-radius: 8px; object-fit: contain; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" 
                          class="me-1 message-image"
                          @error="handleImageError($event, attachment)"
                          @click="openImageModal(getImageSource(attachment), attachment.name)"
                          loading="lazy"
                        >
                        <div class="d-flex align-items-center gap-2 mt-1">
                          <div class="small text-muted" style="word-break: break-all; flex: 1;">{{ attachment.name }}</div>
                          <button 
                            v-if="attachment.url"
                            class="btn btn-sm btn-outline-secondary" 
                            type="button"
                            @click.stop="downloadImage(attachment.url, attachment.name)"
                            title="이미지 다운로드"
                            style="padding: 0.25rem 0.5rem; font-size: 0.75rem;"
                          >
                            <i class="bi bi-download"></i>
                          </button>
                        </div>
                      </div>
                      <audio v-else-if="attachment.type === 'audio' && attachment.url" :src="getAttachmentUrl(attachment.url)" controls class="me-1" style="max-width: 300px;"></audio>
                    </div>
                  </div>
                  <div 
                    class="mc-msg-bubble" 
                    v-html="formatMessage(message.content, message.messageId || message.tempId || '', message.citations)"
                  ></div>
                  <!-- Perplexity AI 출처 링크 -->
                  <div v-if="message.citations && message.citations.length > 0" class="message-citations mt-3" :id="`citations-${message.messageId || message.tempId}`">
                    <div class="border-top pt-2">
                      <small class="text-muted d-block mb-2">
                        <i class="bi bi-link-45deg me-1"></i>
                        <strong>출처:</strong>
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
                </div>
                <div v-if="message.role === 'user'" class="mc-msg-avatar mc-msg-avatar-user">
                  <i class="bi bi-person"></i>
                </div>
              </div>
            </template>

            <!-- 로딩 인디케이터 -->
            <div v-if="loading" class="mc-msg mc-msg-assistant">
              <div 
                class="mc-msg-avatar"
                :style="{ backgroundColor: currentChat?.service?.colorCode || 'var(--ai-primary)' }"
              >
                <i :class="currentChat?.service?.iconClass || 'bi bi-robot'"></i>
              </div>
              <div class="mc-msg-content">
                <div class="mc-typing-spinner">
                  <span class="mc-typing-dot"></span>
                  <span class="mc-typing-dot"></span>
                  <span class="mc-typing-dot"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 입력 영역 -->
          <div class="mc-input-area">
            <!-- 숨김 파일 input -->
            <input
              type="file"
              ref="fileInputRef"
              class="d-none"
              accept="image/*,.pdf,.txt,.doc,.docx,.xls,.xlsx,.csv"
              @change="handleFileSelected"
            >
            <!-- 첨부 미리보기 -->
            <div v-if="pendingAttachments.length > 0" class="mc-attach-preview">
              <div v-for="(att, idx) in pendingAttachments" :key="idx" class="mc-attach-chip">
                <i :class="att.type === 'image' ? 'bi bi-image' : 'bi bi-file-earmark'" class="me-1"></i>
                <span>{{ att.name }}</span>
                <button type="button" class="btn-chip-remove" @click="removePendingAttachment(idx)">
                  <i class="bi bi-x"></i>
                </button>
              </div>
            </div>
            <div class="mc-input-wrapper">
              <button class="btn btn-sm btn-outline-secondary mc-attach-btn" @click="attachFile" type="button" title="파일 첨부" :disabled="uploadingFile">
                <i v-if="uploadingFile" class="bi bi-arrow-clockwise" style="animation:spin .8s linear infinite;display:inline-block"></i>
                <i v-else class="bi bi-paperclip"></i>
              </button>
              <textarea
                class="mc-textarea"
                v-model="inputMessage"
                placeholder="메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
                rows="1"
                @keydown.enter.exact.prevent="handleSubmit"
                @keydown.shift.enter.exact="() => {}"
                @input="(e) => { updateCharCount(); const target = e.target as HTMLTextAreaElement; target.style.height = 'auto'; target.style.height = Math.min(target.scrollHeight, 100) + 'px'; }"
              ></textarea>
              <button
                class="mc-send-btn"
                :class="{ 'mc-send-disabled': isButtonDisabled, 'mc-loading': loading }"
                @click="handleSubmit"
                :disabled="isButtonDisabled"
              >
                <i class="bi bi-send-fill"></i>
              </button>
            </div>
            <div class="mc-input-footer">
              <small>
                <span>{{ charCount }}</span> / 4000 자
              </small>
              <small>Enter로 전송 · Shift+Enter로 줄바꿈</small>
            </div>
          </div>
        </div>
      </div>

    <!-- 설정 모달 -->
    <div :class="['mc-modal-overlay', { open: showSettingsModal }]" v-show="showSettingsModal" @click.self="showSettingsModal = false">
      <div class="mc-modal">
        <div class="mc-modal-header">
          <h5 class="mc-modal-title"><i class="bi bi-sliders me-2"></i>채팅 설정</h5>
          <button type="button" class="btn-close" @click="showSettingsModal = false"></button>
        </div>
        <div class="mc-modal-body">
            <div class="mb-3">
              <label class="form-label">모델</label>
              <select class="form-select" v-model="modelSettings.model">
                <option v-for="model in availableModels" :key="model" :value="model">{{ model }}</option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label">답변 언어</label>
              <select class="form-select" v-model="responseLanguage">
                <option value="auto">자동 감지</option>
                <option value="ko">한국어</option>
                <option value="en">English</option>
              </select>
              <small class="text-muted d-block mt-1">
                AI가 응답할 언어를 선택하세요
              </small>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Temperature</label>
              <div class="mc-slider-wrap">
                <input
                  type="range"
                  class="mc-slider"
                  min="0"
                  max="100"
                  v-model.number="modelSettings.temperature"
                  :style="{ background: `linear-gradient(to right, #4F46E5 0%, #4F46E5 ${modelSettings.temperature}%, #e5e7eb ${modelSettings.temperature}%, #e5e7eb 100%)` }"
                >
                <span class="mc-slider-val">{{ (modelSettings.temperature / 100).toFixed(1) }}</span>
              </div>
              <div class="mc-slider-hints">
                <small class="text-muted">정확함 (0.0)</small>
                <small class="text-muted">창의적 (1.0)</small>
              </div>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Max Tokens</label>
              <input
                type="number"
                class="form-control"
                v-model.number="modelSettings.maxTokens"
                min="100"
                max="8000"
              >
            </div>
            
            <div class="mb-3">
              <label class="form-label">시스템 프롬프트</label>
              <textarea
                class="form-control"
                rows="3"
                v-model="systemPrompt"
                placeholder="AI의 역할이나 행동 방식을 지정하세요..."
              ></textarea>
            </div>
            
            <div class="mb-3">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" v-model="streamResponse" id="stream-response">
                <label class="form-check-label" for="stream-response">
                  스트리밍 응답 (실시간)
                </label>
              </div>
            </div>
            
            <div class="mb-3">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" v-model="saveHistory" id="save-history" checked>
                <label class="form-check-label" for="save-history">
                  대화 기록 자동 저장
                </label>
              </div>
            </div>
            
            <div class="mb-3" v-if="currentChat?.service?.serviceCode?.toLowerCase() === 'chatgpt' || currentChat?.service?.serviceCode?.toLowerCase() === 'openai'">
              <div class="form-check form-switch">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  id="enableWebSearchMulti"
                  v-model="enableWebSearch"
                >
                <label class="form-check-label" for="enableWebSearchMulti">
                  <i class="bi bi-search me-1"></i>
                  웹 검색 활성화 (Tavily)
                </label>
              </div>
              <small class="text-muted d-block mt-1">
                최신 정보를 웹에서 검색하여 답변에 포함합니다.
              </small>
            </div>
            <div class="mb-3">
              <div class="form-check form-switch">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  id="enableRagMulti"
                  v-model="enableRag"
                >
                <label class="form-check-label" for="enableRagMulti">
                  <i class="bi bi-database me-1"></i>
                  RAG 활성화 (Knowledge Base)
                </label>
              </div>
              <small class="text-muted d-block mt-1">
                지식베이스 문서를 검색하여 답변에 포함합니다.
              </small>
            </div>
        </div>
        <div class="mc-modal-footer">
          <button type="button" class="btn btn-secondary" @click="showSettingsModal = false">취소</button>
          <button type="button" class="btn btn-primary" @click="saveSettings">저장</button>
        </div>
      </div>
    </div>
    
    <!-- 이미지 확대 모달 (mc-modal 스타일) -->
    <div 
      v-if="showImageModal" 
      class="mc-modal-overlay mc-image-modal open"
      @click.self="closeImageModal"
    >
      <div class="mc-modal">
        <div class="mc-modal-header" style="border-bottom: none; padding-bottom: 0;">
          <h5 class="mc-modal-title text-white">{{ imageModalTitle }}</h5>
          <button type="button" class="btn-close btn-close-white" @click="closeImageModal" aria-label="Close"></button>
        </div>
        <div class="mc-modal-body">
          <img 
            :src="imageModalSrc" 
            :alt="imageModalTitle"
            @error="imageModalSrc = ''"
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 후속 트랙 B-1 (2026-05-08) 완료: 인라인 ConversationDto / ApiService 인터페이스를
// 백엔드 C# Models/DTOs (ConversationDto.cs / ApiServiceDto.cs) 와 정렬 후 `@ts-nocheck` 해제.
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import api from '@/services/api'
// 트랙 #97-post7 (2026-05-18) — 멀티채팅 SSE streaming 추가 (AgentChat 단일 패턴 이식)
import { streamChat, type SendDirectMessageStreamRequest } from '@/services/sseClient'
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
import './AgentMultiChat.css'
import {
  safeGetSessionStorage,
  safeSetSessionStorage,
  safeRemoveSessionStorage
} from '@/utils/storage'

// 트랙 #88 H2 (2026-05-13) — 멀티채팅 첨부 보존
// 사용자가 멀티채팅에서 이미지를 첨부한 뒤 이미지 생성 페이지 등 다른 라우트로 이동했다가
// 돌아오는 경우 컴포넌트가 unmount → 재mount 되면서 로컬 ref(pendingAttachments)는 소실된다.
// 이를 막기 위해 sessionStorage(탭 단위 휘발)에 첨부 메타데이터(백엔드에 이미 업로드된 영구 URL,
// 파일명, 타입)를 영속화한다. 탭을 닫으면 자동으로 비워지므로 다른 사용자 세션 간 누수 없음.
//
// 주의: preview(blob: URL)는 다음 mount 시 무효하므로 저장하지 않는다.
// 재mount 시 이미지 표시는 백엔드 url을 직접 사용한다(이미 업로드 완료된 상태).
const ATTACH_STORAGE_KEY = 'agenthub.multiChat.pendingAttachments'

// 후속 트랙 B-1: ApiServiceDto 의 defaultModel 필드를 인라인 인터페이스에도 미러링.
// 트랙 #97-post4 (2026-05-18): ServiceCategory("external"/"internal") + HasActiveKey 추가.
//   - 외부/내부 LLM 탭 분기용 + 키 미설정/만료 시 dropdown 에서 숨김.
interface ApiService {
  serviceId: number
  serviceCode: string
  serviceName: string
  description?: string
  iconClass?: string
  colorCode?: string
  defaultModel?: string
  serviceType?: 'Chat' | 'ImageGeneration' | 'VideoGeneration' | 'Both'
  serviceCategory?: 'external' | 'internal'
  hasActiveKey?: boolean
}

// 후속 트랙 B-1: ConversationDto 의 EnableRag / EnableWebSearch (백엔드 [Required] non-nullable bool) 미러링.
interface ConversationDto {
  conversationId: number
  userId: number
  agentId?: number
  agentName?: string
  serviceId: number
  serviceName: string
  title?: string
  model?: string
  temperature?: number
  maxTokens?: number
  messageCount: number
  totalTokens: number
  totalCost: number
  lastMessageAt?: string
  isArchived: boolean
  isPinned: boolean
  language?: string // 'ko', 'en', 'auto'
  enableRag: boolean
  enableWebSearch: boolean
  createdAt: string
  updatedAt: string
}

interface ChatMessageDto {
  messageId: number
  conversationId: number
  role: 'user' | 'assistant' | 'system'
  content: string
  attachments?: string // JSON 문자열 (이미지 URL 목록 등)
  tokensUsed?: number
  model?: string
  finishReason?: string
  createdAt: string
  citations?: string[]
}

interface ChatSession {
  id: string
  conversationId?: number // 실제 DB의 ConversationId
  title: string
  preview: string
  service: ApiService | null
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  model: string
  temperature: number
  maxTokens: number
  messageCount?: number
  isPinned?: boolean
  language?: string // 'ko', 'en', 'auto'
  enableRag?: boolean
  enableWebSearch?: boolean
  // H4(5-4) — 채팅 슬롯별 진행 상태. 같은 ChatGPT Agent 의 서로 다른 채팅을 동시에 호출할 수 있도록
  // 전역 `loading` ref 대신 슬롯 단위 플래그로 분리한다.
  loading?: boolean
}

interface Message {
  messageId?: number
  tempId?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  createdAt: string | Date
  citations?: string[]
  attachments?: Array<{
    type: 'image' | 'file' | 'audio'
    url: string
    name: string
    preview?: string
  }>
  // 트랙 #97-post7 — SSE streaming 중 표시 (cursor 효과 등)
  isStreaming?: boolean
  // 트랙 #97-post5 (2026-05-18): 메시지 발화 출처 영구 보존
  //   - 사용자가 service 를 변경해도 기존 응답의 provider(gpt/nexus/claude/...)
  //     아이콘/색상/이름은 그대로 유지되어야 함 (대화 기록 일관성)
  //   - assistant 메시지 생성 시 currentChat.service 의 스냅샷 + 백엔드 model 응답 저장
  originServiceCode?: string
  originServiceName?: string
  originIconClass?: string
  originColorCode?: string
  originModel?: string
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

// marked v11+ 부터 mangle/headerIds 옵션은 default false 로 변경되어 MarkedOptions 에서 제거됨.
// (Phase 3 vue-tsc 2.x 부채 정리 — TS2353 해소, 동작 변화 없음)
marked.setOptions({
  breaks: true,
  gfm: true,
  renderer: renderer
})

const services = ref<ApiService[]>([])
// 트랙 #97-post4 (2026-05-18): 외부/내부 LLM 탭 분기 + 키 없는 모델 숨김
const activeServiceTab = ref<'external' | 'internal'>('external')
const chats = ref<ChatSession[]>([])
const currentChatId = ref<string | null>(null)
const inputMessage = ref('')
const loading = ref(false)
const chatBody = ref<HTMLElement | null>(null)
const showSettingsModal = ref(false)
const charCount = ref(0)
const showImageModal = ref(false)
const imageModalSrc = ref('')
const imageModalTitle = ref('')
const systemPrompt = ref('당신은 도움이 되고 친절한 AI 어시스턴트입니다.')
// 트랙 #97-post8 (2026-05-18) — 결함 G fix: streaming 기본 활성화.
//   기존: false → 비스트리밍 = 응답 전체 대기 = 10~20초 (GPT web 3초 대비 큰 격차).
//   fix-A(SSE 401) + post7(신규 conv race) 로 원인 결함 해소 → streaming 기본 활성화 안전.
const streamResponse = ref(true)
const saveHistory = ref(true)

// 전송 버튼 비활성화 여부
const isButtonDisabled = ref(true)

const modelSettings = ref({
  // 트랙 #97-post6 (2026-05-18) — 결함 E (gpt-4 응답 미표시) 회피:
  //   기존 'gpt-4-turbo' 은 ApiServiceModels 카탈로그(gpt-5/o3/o3-mini/o1/o1-mini/gpt-4o/gpt-4o-mini)에 없는 obsolete 모델.
  //   사용자가 카탈로그 API 응답 도착 전에 선택하면 백엔드는 응답하지만 frontend 처리에서 누락 가능.
  //   카탈로그에 항상 존재하는 안전 모델로 변경.
  model: 'gpt-4o-mini',
  temperature: 70,
  maxTokens: 2048
})

const enableWebSearch = ref(false)
const enableRag = ref(false)
const responseLanguage = ref<string>('auto') // 'auto', 'ko', 'en'

// 트랙 #97-post6 — obsolete 하드코딩 모델 제거. 카탈로그 API(`/apiservices/{id}/models`) 응답이 우선.
//   초기 빈 배열로 시작 → loadModels() 가 운영 카탈로그로 채움. 카탈로그에 없는 모델 사용자 선택 차단.
const availableModels = ref<string[]>(['gpt-4o-mini'])

const suggestedPrompts = [
  { icon: '👋', label: '인사하기', text: '안녕하세요! 오늘 어떤 도움이 필요하신가요?' },
  { icon: '💻', label: '코딩 도움', text: '파이썬으로 간단한 웹 크롤러 만드는 방법을 알려주세요' },
  { icon: '✍️', label: '글쓰기 도움', text: '효과적인 이메일 작성 팁을 알려주세요' },
  { icon: '📊', label: '데이터 분석', text: '데이터 분석 프로젝트 시작하는 방법' }
]

// 현재 채팅 세션
const currentChat = computed(() => {
  return chats.value.find(c => c.id === currentChatId.value) || null
})

// 현재 채팅의 메시지
const currentMessages = computed(() => {
  return currentChat.value?.messages || []
})

// 트랙 #97-post4 (2026-05-18): 활성 키 보유 외부/내부 LLM 필터
//   - 백엔드(/api/apiservices) 가 ServiceCategory("external"/"internal") + HasActiveKey 채워서 응답
//   - 키 미설정/만료(HasActiveKey=false) 인 provider 는 dropdown 에서 숨김 (사용자 결정: 우선 무시)
//   - 향후 키 추가 시 ApiKeyPool 자동 갱신 → 백엔드 응답 변경 → 자동 노출
//   - Chat 전용 (이미지 생성은 별도 화면)
const filteredServices = computed(() => {
  return services.value.filter(s =>
    s.hasActiveKey === true &&
    (s.serviceCategory ?? 'external') === activeServiceTab.value &&
    (s.serviceType ?? 'Chat') === 'Chat'
  )
})

// 각 탭의 활성 카운트 — 배지 표시용
const externalActiveCount = computed(() =>
  services.value.filter(s => s.hasActiveKey === true && (s.serviceCategory ?? 'external') === 'external' && (s.serviceType ?? 'Chat') === 'Chat').length
)
const internalActiveCount = computed(() =>
  services.value.filter(s => s.hasActiveKey === true && s.serviceCategory === 'internal' && (s.serviceType ?? 'Chat') === 'Chat').length
)

// 서비스별 모델 목록 로드
const loadModels = async (serviceId: number) => {
  try {
    const response = await api.get<string[]>(`/apiservices/${serviceId}/models`)
    if (response.data && response.data.length > 0) {
      availableModels.value = response.data
      // 현재 모델이 새 목록에 없으면 첫 번째 모델로 변경
      if (!availableModels.value.includes(modelSettings.value.model)) {
        modelSettings.value.model = availableModels.value[0]
      }
    }
  } catch (error) {
    console.error('Error loading models:', error)
  }
}

const loadServices = async () => {
  try {
    const response = await api.get<ApiService[]>('/apiservices')
    services.value = response.data || []
    if (services.value.length > 0 && !currentChat.value) {
      await loadModels(services.value[0].serviceId)
    }
  } catch (error) {
    console.error('Error loading services:', error)
  }
}

// ChatConversations 불러오기
const loadConversations = async () => {
  try {
    // services가 로드되지 않았으면 먼저 로드
    if (services.value.length === 0) {
      await loadServices()
    }
    
    const response = await api.get<ConversationDto[]>('/chat/conversations?isArchived=false')
    const conversations = response.data || []
    
    // ChatSession 형태로 변환
    const convertedChats: ChatSession[] = conversations.map(conv => {
      // serviceId로 서비스 찾기
      const service = services.value.find(s => s.serviceId === conv.serviceId)
      if (!service) {
        console.warn(`Service not found for conversation ${conv.conversationId}, serviceId: ${conv.serviceId}, serviceName: ${conv.serviceName}`)
        // 서비스를 찾지 못한 경우, ServiceName으로 다시 시도하거나 기본 서비스 사용
        const fallbackService = services.value.find(s => s.serviceName === conv.serviceName) || services.value[0]
        if (fallbackService) {
          console.log(`Using fallback service for conversation ${conv.conversationId}: ${fallbackService.serviceName}`)
        }
        return {
          id: `conv-${conv.conversationId}`,
          conversationId: conv.conversationId,
          title: conv.title || '새 채팅',
          preview: '',
          service: fallbackService || null,
          messages: [],
          createdAt: new Date(conv.createdAt),
          updatedAt: new Date(conv.updatedAt || conv.createdAt),
          model: conv.model || fallbackService?.defaultModel || 'gpt-4-turbo',
          temperature: conv.temperature ? Math.round(conv.temperature * 100) : 70,
          maxTokens: conv.maxTokens || 2048,
          messageCount: conv.messageCount || 0,
          isPinned: conv.isPinned || false,
          language: conv.language || 'auto',
          enableRag: conv.enableRag || false,
          enableWebSearch: conv.enableWebSearch || false
        }
      }
      
      return {
        id: `conv-${conv.conversationId}`,
        conversationId: conv.conversationId,
        title: conv.title || '새 채팅',
        preview: '', // 첫 메시지로 채울 예정
        service: service,
        messages: [], // 메시지는 별도로 로드
        createdAt: new Date(conv.createdAt),
        updatedAt: new Date(conv.updatedAt || conv.createdAt),
        model: conv.model || service.defaultModel || 'gpt-4-turbo',
        temperature: conv.temperature ? Math.round(conv.temperature * 100) : 70,
        maxTokens: conv.maxTokens || 2048,
        messageCount: conv.messageCount || 0,
        isPinned: conv.isPinned || false,
        language: conv.language || 'auto',
        enableRag: conv.enableRag || false,
        enableWebSearch: conv.enableWebSearch || false
      }
    })
    
    // 고정된 채팅을 맨 위로
    convertedChats.sort((a, b) => {
      if (a.isPinned && !b.isPinned) return -1
      if (!a.isPinned && b.isPinned) return 1
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    })
    
    // 기존 채팅 목록과 병합 (새로 생성한 채팅은 유지)
    // conversationId가 없는 로컬 채팅만 유지
    const existingLocalChats = chats.value.filter(c => !c.conversationId)
    
    // 현재 선택된 채팅의 conversationId 확인
    const currentChat = chats.value.find(c => c.id === currentChatId.value)
    const currentConversationId = currentChat?.conversationId
    
    // DB에서 로드한 채팅 목록으로 교체
    chats.value = [...convertedChats, ...existingLocalChats]
    
    // 현재 선택된 채팅이 conversationId를 가지고 있었으면, 로드된 목록에서 찾아서 선택 상태 유지
    if (currentConversationId) {
      const reloadedChat = chats.value.find(c => c.conversationId === currentConversationId)
      if (reloadedChat && currentChatId.value !== reloadedChat.id) {
        currentChatId.value = reloadedChat.id
      }
    }
    
    // 메시지는 selectChat에서 선택 시에만 로드 (초기 로드 시 N개 API 호출 방지 → 속도 개선)
  } catch (error) {
    console.error('Error loading conversations:', error)
  }
}

// 새 채팅 생성
const createNewChat = () => {
  const defaultService = services.value[0] || null
  const newChat: ChatSession = {
    id: `chat-${Date.now()}`,
    title: '새 채팅',
    preview: '',
    service: defaultService,
    messages: [],
    createdAt: new Date(),
    updatedAt: new Date(),
    model: modelSettings.value.model,
    temperature: modelSettings.value.temperature,
    maxTokens: modelSettings.value.maxTokens,
    enableRag: false,
    enableWebSearch: false
  }
  chats.value.unshift(newChat)
  currentChatId.value = newChat.id
  if (defaultService) {
    loadModels(defaultService.serviceId)
  }
}

// 채팅 선택
const selectChat = async (chatId: string) => {
  currentChatId.value = chatId
  const chat = chats.value.find(c => c.id === chatId)
  if (!chat) return

  // H4(5-4) — 활성 채팅 전환 시 입력창 비활성/스피너 표시를 그 채팅의 진행 상태로 동기화.
  // (다른 채팅이 백그라운드에서 진행 중이어도 현재 채팅이 idle 이면 입력 가능)
  loading.value = chat.loading === true
  
  // 채팅의 서비스 정보가 없으면 services에서 다시 찾기 (conversationId가 있는 경우)
  if (!chat.service && chat.conversationId) {
    // services를 다시 로드
    if (services.value.length === 0) {
      await loadServices()
    }
    
    // conversationId로 ConversationDto 정보를 다시 가져와서 serviceId 확인
    try {
      const convResponse = await api.get<ConversationDto>(`/chat/conversations/${chat.conversationId}`)
      const conv = convResponse.data
      if (conv) {
        // serviceId로 서비스 찾기
        const service = services.value.find(s => s.serviceId === conv.serviceId)
        if (service) {
          chat.service = service
          console.log(`Service found for conversation ${chat.conversationId}: ${service.serviceName}`)
        } else {
          console.warn(`Service not found for conversation ${chat.conversationId}, serviceId: ${conv.serviceId}`)
          // 기본 서비스 사용
          if (services.value.length > 0) {
            chat.service = services.value[0]
          }
        }
        // 언어 설정 복원
        if (conv.language) {
          chat.language = conv.language
          responseLanguage.value = conv.language
        }
        // RAG 및 웹 검색 설정 복원
        if (conv.enableRag !== undefined) {
          chat.enableRag = conv.enableRag
          enableRag.value = conv.enableRag
        }
        if (conv.enableWebSearch !== undefined) {
          chat.enableWebSearch = conv.enableWebSearch
          enableWebSearch.value = conv.enableWebSearch
        }
      }
    } catch (error) {
      console.error(`Error loading conversation ${chat.conversationId}:`, error)
      // 기본 서비스 사용
      if (services.value.length > 0) {
        chat.service = services.value[0]
      }
    }
  }
  
  // 채팅의 서비스가 있으면 해당 서비스로 전환
  if (chat.service) {
    // 해당 서비스를 현재 채팅의 서비스로 설정 (화면 업데이트를 위해)
    await loadModels(chat.service.serviceId)
    modelSettings.value.model = chat.model || chat.service.defaultModel || 'gpt-4-turbo'
    modelSettings.value.temperature = chat.temperature || 70
    modelSettings.value.maxTokens = chat.maxTokens || 2048
    // 언어 설정 복원
    if (chat.language) {
      responseLanguage.value = chat.language
    }
    // RAG 및 웹 검색 설정 복원
    if (chat.enableRag !== undefined) {
      enableRag.value = chat.enableRag
    }
    if (chat.enableWebSearch !== undefined) {
      enableWebSearch.value = chat.enableWebSearch
    }
  } else {
    // 서비스가 없으면 첫 번째 서비스 사용
    if (services.value.length > 0) {
      chat.service = services.value[0]
      await loadModels(chat.service.serviceId)
      modelSettings.value.model = chat.model || chat.service.defaultModel || 'gpt-4-turbo'
      modelSettings.value.temperature = chat.temperature || 70
      modelSettings.value.maxTokens = chat.maxTokens || 2048
      // 언어 설정 복원
      if (chat.language) {
        responseLanguage.value = chat.language
      }
    }
  }
  
  // conversationId가 있으면 메시지 불러오기
  if (chat.conversationId && chat.messages.length === 0) {
    try {
      const response = await api.get<ChatMessageDto[]>(`/chat/conversations/${chat.conversationId}/messages`)
      const messages = response.data || []
      chat.messages = messages.map(m => {
        // attachments JSON 파싱 (이미지 URL 목록)
        let attachments: Array<{ type: 'image' | 'file' | 'audio'; url: string; name: string }> | undefined = undefined
        if (m.attachments) {
          try {
            const imageUrls = JSON.parse(m.attachments) as string[]
            if (Array.isArray(imageUrls) && imageUrls.length > 0) {
              attachments = imageUrls.map((url: string, index: number) => ({
                type: 'image' as const,
                url: url,
                name: `generated-image-${index + 1}.png`
              }))
            }
          } catch (e) {
            console.warn('Failed to parse attachments JSON:', e)
          }
        }
        return {
          messageId: m.messageId,
          role: m.role as 'user' | 'assistant' | 'system',
          content: m.content,
          createdAt: m.createdAt,
          citations: (m as any).citations,
          attachments: attachments
        }
      })
      
      // 미리보기 업데이트
      const firstUserMessage = messages.find(m => m.role === 'user')
      if (firstUserMessage) {
        chat.preview = firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '')
      }
    } catch (error) {
      console.error('Error loading messages:', error)
    }
  }
  
  await nextTick()
  scrollToBottom()
  setupCitationClickHandlers()
}

// 트랙 #88 H1 (2026-05-13) — 채팅 삭제 견고화
// 기존 결함: 삭제 버튼을 눌러도 UI가 갱신되지 않거나 silent fail 로 사용자가 인지하지 못함.
// 해결:
//   1) confirm 메시지에 채팅 제목을 노출하여 사용자가 어느 채팅을 지우는지 명확히 인지
//   2) 백엔드 DELETE 성공 후 loadConversations 로 서버 상태와 동기화 → reactive 미반영 결함 차단
//   3) 404 응답은 "이미 삭제됨"으로 간주하고 로컬에서도 제거(서버/UI 불일치 자가복구)
//   4) 401/403/5xx 응답 시 한국어 안내 alert 로 사용자 통지
//   5) 삭제 성공 시 한국어 confirm 안내 alert (정식 toast 도입 전까지 alert 사용)
const deleteChat = async (chatId: string) => {
  const chat = chats.value.find(c => c.id === chatId)
  if (!chat) {
    // 이미 화면에서 사라진 채팅(이중 클릭 등) — silent return
    return
  }

  const titleForPrompt = chat.title?.trim() || '새 채팅'
  if (!confirm(`"${titleForPrompt}" 채팅을 삭제하시겠습니까?\n삭제된 채팅과 대화 내용은 복구할 수 없습니다.`)) {
    return
  }

  // 1단계: 서버 측 삭제 (conversationId 가 있을 때만 — 아직 저장되지 않은 로컬 채팅은 서버 호출 불필요)
  let serverDeleteSucceeded = true
  if (chat.conversationId) {
    try {
      await api.delete(`/chat/conversations/${chat.conversationId}`)
    } catch (error: any) {
      const status = error?.response?.status
      if (status === 404) {
        // 서버에는 이미 없는 대화 — 로컬에서만 제거되면 일관성 회복
        console.warn(`[MultiChat] Conversation ${chat.conversationId} 가 서버에 이미 없음(404) — 로컬에서만 제거합니다.`)
      } else if (status === 401 || status === 403) {
        // 인증/권한 문제 — 인터셉터가 401 처리하므로 여기서는 403 만 별도 안내
        alert('이 채팅을 삭제할 권한이 없습니다.')
        return
      } else {
        console.error('[MultiChat] 채팅 삭제 실패:', error)
        alert('채팅 삭제 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.')
        return
      }
      serverDeleteSucceeded = false
    }
  }

  // 2단계: 로컬 상태에서 제거 + 다음 선택 채팅 결정
  const index = chats.value.findIndex(c => c.id === chatId)
  if (index !== -1) {
    chats.value.splice(index, 1)
  }

  // 현재 보고 있는 채팅이 삭제된 경우 — 다음 채팅 선택 또는 새 채팅 생성
  if (currentChatId.value === chatId) {
    if (chats.value.length > 0) {
      currentChatId.value = chats.value[0].id
      await selectChat(chats.value[0].id)
    } else {
      currentChatId.value = null
      createNewChat()
    }
  }

  // 3단계: 서버에 실제로 저장되어 있던 대화면, 서버 목록과 재동기화하여
  // Vue reactive 미반영 또는 다중 탭 사이 불일치를 해소한다.
  if (chat.conversationId && serverDeleteSucceeded) {
    try {
      await loadConversations()
    } catch (e) {
      // loadConversations 자체가 실패해도 위에서 로컬 splice 는 끝났으므로 UX 영향 없음
      console.warn('[MultiChat] 삭제 후 목록 재동기화 실패:', e)
    }
  }
}

// 서비스 전환
// 트랙 #97-post5 (2026-05-18) — 중대 결함 fix:
//   기존 동작: chat.service 만 변경 (frontend) → conversationId 보유 채팅이면
//   백엔드 `/api/chat/conversations/{id}/messages` 호출 시 body 에 serviceId 미전송 →
//   백엔드는 conversation 의 원래 ServiceId(예: chatgpt) 그대로 사용 →
//   사용자는 nexus 선택했는데 실제로는 chatgpt 응답 (ApiUsages 도 chatgpt 로 기록)
//
//   신규 동작: 기존 conversation 보유 채팅에서 service 변경 시 → 새 채팅 자동 생성.
//   사용자 의도(다른 모델로 시도)가 곧 새 대화의 시작이므로 UX 자연스러움.
const switchService = async (service: ApiService) => {
  const existing = chats.value.find(c => c.id === currentChatId.value)

  // 케이스 A — 기존 conversation 있고 다른 service 로 변경 → 새 채팅 자동 생성
  if (existing?.conversationId && existing.service?.serviceId !== service.serviceId) {
    createNewChat()
    const fresh = chats.value.find(c => c.id === currentChatId.value)
    if (fresh) {
      fresh.service = service
      await loadModels(service.serviceId)
      if (availableModels.value.length > 0) {
        modelSettings.value.model = availableModels.value[0]
        fresh.model = modelSettings.value.model
      }
    }
    return
  }

  // 케이스 B — 신규(conversationId 없음) 또는 같은 service 재선택
  if (!currentChatId.value) {
    createNewChat()
  }
  const chat = chats.value.find(c => c.id === currentChatId.value)
  if (chat) {
    chat.service = service
    await loadModels(service.serviceId)
    if (availableModels.value.length > 0) {
      modelSettings.value.model = availableModels.value[0]
      chat.model = modelSettings.value.model
    }
  }
}

// 전송 핸들러
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
  // H4(5-4) — 채팅별 진행 상태를 사용해 같은 ChatGPT Agent 의 다른 채팅을 병렬 호출 가능하게 한다.
  // 전역 loading.value 는 입력창 비활성/스피너 표시용으로만 유지하고, 동시 호출 차단은 chat.loading 로 한다.
  if (!inputMessage.value.trim()) return

  // 현재 채팅이 없으면 새로 생성
  if (!currentChatId.value) {
    createNewChat()
  }

  const chat = chats.value.find(c => c.id === currentChatId.value)
  if (!chat || !chat.service) {
    alert('AI 서비스를 선택해주세요.')
    return
  }

  // 동일 채팅에 동시 호출은 차단(이전 응답이 끝나야 다음 질문). 다른 채팅은 영향 없음.
  if (chat.loading) {
    return
  }

  const userMessage: Message = {
    tempId: `temp-${Date.now()}`,
    role: 'user',
    content: inputMessage.value,
    createdAt: new Date(),
    attachments: pendingAttachments.value.length > 0 ? [...pendingAttachments.value] : undefined
  }

  chat.messages.push(userMessage)
  const messageText = inputMessage.value
  const attachmentsCopy = [...pendingAttachments.value]
  inputMessage.value = ''
  charCount.value = 0
  pendingAttachments.value = []
  chat.loading = true
  loading.value = true // 현재 활성 채팅에 대한 입력창 비활성/스피너 표시

  // 채팅 제목 자동 생성 (첫 메시지인 경우)
  if (chat.messages.length === 1) {
    chat.title = messageText.length > 30 ? messageText.substring(0, 30) + '...' : messageText
  }
  chat.preview = messageText.length > 50 ? messageText.substring(0, 50) + '...' : messageText
  chat.updatedAt = new Date()

  try {
    await scrollToBottom()

    let assistantMessage: Message

    // conversationId가 있으면 기존 conversation에 메시지 전송
    if (chat.conversationId) {
      // H3(5-3) — 첨부 이미지를 vision payload(MessageContentDto 배열) 형식으로 보낸다.
      // 기존: JSON.stringify(이미지 URL[]) → backend SendMessageRequestDto 에 필드 없어 무시 → LLM 미전달.
      // 신규: attachments: [{type:'image_url', imageUrl:'data:...' | 'https://...'}] → ChatService 가
      // 마지막 user 메시지의 Contents 로 결합하여 AiProxyService(OpenAI/Claude/Gemini) 의 vision payload 로 변환.
      const imageAttachments = attachmentsCopy
        .filter(a => a.type === 'image' && !!a.url)
        .map(a => ({
          type: 'image_url' as const,
          imageUrl: a.url,
          fileName: a.name
        }))
      const response = await api.post(`/chat/conversations/${chat.conversationId}/messages`, {
        message: messageText,
        stream: streamResponse.value,
        enableWebSearch: enableWebSearch.value && (chat.service.serviceCode?.toLowerCase() === 'chatgpt' || chat.service.serviceCode?.toLowerCase() === 'openai'),
        enableRag: enableRag.value,
        ragTopK: 5,
        language: responseLanguage.value,
        attachments: imageAttachments.length > 0 ? imageAttachments : undefined
      })

      assistantMessage = {
        messageId: response.data.messageId,
        role: 'assistant',
        content: response.data.content || '응답이 없습니다.',
        createdAt: response.data.createdAt || new Date(),
        citations: (response.data as any).citations || undefined,
        // 트랙 #97-post5 — 발화 출처 영구 보존 (service 변경 후에도 유지)
        originServiceCode: chat.service?.serviceCode,
        originServiceName: chat.service?.serviceName,
        originIconClass: chat.service?.iconClass,
        originColorCode: chat.service?.colorCode,
        originModel: (response.data as any).model || chat.model
      }
    } else {
      // 새로운 conversation 생성
      // 이전 대화 이력 포함
      // H3(5-3) — 마지막 user 메시지에 첨부 이미지가 있으면 OpenAI Vision 호환의 multimodal contents
      // 배열 형식으로 전송한다. 이전 메시지(이미 답변 완료된 history)는 텍스트만 전송.
      const requestMessages = chat.messages
        .filter(m => m.role !== 'system')
        .map((m, idx, arr): { role: string; content?: string; contents?: Array<{ type: string; text?: string; imageUrl?: string; fileName?: string }> } => {
          const isLastUser = m.role === 'user' && idx === arr.length - 1
          // 이번 턴에 보낼 첨부는 attachmentsCopy 에 있다(이미 pendingAttachments 에서 분리됨).
          if (isLastUser && attachmentsCopy.length > 0) {
            const imageParts = attachmentsCopy
              .filter(a => a.type === 'image' && !!a.url)
              .map(a => ({
                type: 'image_url' as const,
                imageUrl: a.url,
                fileName: a.name
              }))
            if (imageParts.length > 0) {
              const contents: Array<{ type: string; text?: string; imageUrl?: string; fileName?: string }> = []
              if (m.content && m.content.length > 0) {
                contents.push({ type: 'text', text: m.content })
              }
              contents.push(...imageParts)
              return { role: m.role, content: m.content, contents }
            }
          }
          return { role: m.role, content: m.content }
        })

      // 시스템 프롬프트 추가
      if (systemPrompt.value) {
        requestMessages.unshift({
          role: 'system',
          content: systemPrompt.value
        })
      }

      // 이미지 생성 서비스/모델인지 확인
      const serviceType = (chat.service as any)?.serviceType
      const modelName = modelSettings.value.model?.toLowerCase() || ''
      const serviceCode = chat.service.serviceCode?.toLowerCase() || ''
      
      const isImageGenerationService = serviceType === 'ImageGeneration' || serviceType === 'Both' ||
        serviceCode.includes('dalle') || serviceCode.includes('gemini') && modelName.includes('image')
      
      const isImageGenerationModel = modelName.includes('dall-e') || 
        modelName.includes('dalle') ||
        modelName.includes('imagen') ||
        modelName.includes('flux') ||
        modelName.includes('gen4-image') ||
        modelName.includes('gemini') && (modelName.includes('image') || modelName.includes('pro-image'))
      
      // 이미지 생성 서비스/모델인 경우 이미지 생성 API로 라우팅
      if (isImageGenerationService || isImageGenerationModel) {
        const prompt = messageText.trim()
        
        if (!prompt) {
          throw new Error('이미지 생성을 위한 프롬프트를 입력해주세요.')
        }

        // 이미지 생성 요청
        const imageResponse = await api.post('/image-generation/generate', {
          serviceId: chat.service.serviceId,
          model: modelSettings.value.model || 'dall-e-3',
          prompt: prompt,
          size: '1024x1024',
          quality: 'standard',
          numberOfImages: 1,
          conversationId: chat.conversationId || null
        })

        // 로딩 상태 즉시 해제 (이미지 생성은 응답이 즉시 와도 후속 처리가 길 수 있음)
        chat.loading = false
        loading.value = chats.value.some(c => c.loading === true)
        await nextTick()

        // 이미지 생성 응답을 메시지로 표시
        const imageUrls = imageResponse.data?.imageUrls || []
        assistantMessage = {
          tempId: `img-${Date.now()}`,
          role: 'assistant',
          content: `이미지 생성 완료 (${imageUrls.length}개)`,
          attachments: imageUrls.map((url: string, index: number) => ({
            type: 'image',
            url: url,
            name: `generated-image-${index + 1}.png`
          })),
          createdAt: new Date()
        }
        
        // 이미지 생성 응답에서 conversationId가 오면 저장
        if (imageResponse.data?.conversationId) {
          const newConversationId = imageResponse.data.conversationId
          // 트랙 #97-post7 (2026-05-18) — race fix:
          //   기존 결함: currentMessages 백업이 assistantMessage push 전에 일어나 백업에 누락.
          //   loadConversations 가 chats.value 통째 교체 → 옛 chat reference 는 chats.value 에 없음 →
          //   updatedChat.messages = currentMessages (assistantMessage 없는 상태) → 화면 빈 응답 → F5 시 백엔드 로드로 표시.
          //   fix: 백업에 assistantMessage 까지 포함 → updatedChat 에 완전한 메시지 배열 복원.
          const currentMessages = [...chat.messages, assistantMessage]

          chat.conversationId = newConversationId
          chat.id = `conv-${newConversationId}`

          // DB에 저장된 conversation이므로 목록을 다시 로드하여 최신 상태 반영
          await loadConversations()

          // 로드 후 현재 채팅 찾기
          const updatedChat = chats.value.find(c => c.conversationId === newConversationId)
          if (updatedChat) {
            currentChatId.value = updatedChat.id
            // 작업 중 메시지 + assistantMessage 까지 영구 보존 (post7 fix)
            updatedChat.messages = currentMessages
            updatedChat.updatedAt = new Date()
          }
        }
      } else if (streamResponse.value) {
        // ════════════════════════════════════════════════════════════
        // 트랙 #97-post7 (2026-05-18) — SSE streaming 분기 (신규 conv)
        //   AgentChat 단일 streamChat for-await 패턴 이식.
        //   토큰 도착 즉시 화면에 점진 표시 (ChatGPT/Claude web 처럼).
        //
        //   payload 는 비스트리밍과 동일. stream:true 는 streamChat 내부에서 강제.
        //   첫 'meta' event 의 conversationId 로 chat.conversationId 갱신 (in-place).
        //   delta 마다 assistantMessage.content 누적 → Vue reactivity 가 자동 렌더.
        // ════════════════════════════════════════════════════════════
        const streamPayload: SendDirectMessageStreamRequest = {
          serviceId: chat.service.serviceId,
          model: modelSettings.value.model,
          temperature: modelSettings.value.temperature / 100,
          maxTokens: modelSettings.value.maxTokens,
          messages: requestMessages,
          enableWebSearch: enableWebSearch.value && (chat.service.serviceCode?.toLowerCase() === 'chatgpt' || chat.service.serviceCode?.toLowerCase() === 'openai'),
          enableRag: enableRag.value,
          ragTopK: 5,
          language: responseLanguage.value
        }

        // streaming 메시지 미리 push — Vue reactivity 가 delta 마다 렌더링
        const streamingMsg: Message = {
          tempId: `streaming-${Date.now()}`,
          role: 'assistant',
          content: '',
          createdAt: new Date(),
          isStreaming: true,
          originServiceCode: chat.service?.serviceCode,
          originServiceName: chat.service?.serviceName,
          originIconClass: chat.service?.iconClass,
          originColorCode: chat.service?.colorCode,
          originModel: chat.model
        }
        chat.messages.push(streamingMsg)
        chat.updatedAt = new Date()

        let firstDelta = false
        try {
          for await (const evt of streamChat(streamPayload)) {
            switch (evt.type) {
              case 'delta':
                if (!firstDelta) {
                  firstDelta = true
                  chat.loading = false  // 첫 토큰 도착 = 로딩 인디케이터 제거
                }
                streamingMsg.content += evt.content ?? ''
                await scrollToBottom()
                break
              case 'meta':
                if (evt.conversationId && !chat.conversationId) {
                  chat.conversationId = evt.conversationId
                  chat.id = `conv-${evt.conversationId}`
                }
                if (evt.messageId) streamingMsg.messageId = evt.messageId
                if (evt.model) streamingMsg.originModel = evt.model
                break
              case 'usage':
                // 토큰/비용은 conv list 갱신 시 자연 반영
                break
              case 'error':
                streamingMsg.content = evt.message || '오류가 발생했습니다.'
                break
            }
          }
        } catch (err: any) {
          if (err?.name === 'AbortError') {
            streamingMsg.content = (streamingMsg.content || '') + '\n\n_사용자가 중단했습니다_'
          } else {
            // 비스트리밍 catch 와 동일 정책으로 surface
            streamingMsg.content = '오류가 발생했습니다: ' + (err?.message || '알 수 없는 오류')
            streamingMsg.isStreaming = false
            throw err
          }
        } finally {
          streamingMsg.isStreaming = false
          if (chat.loading) chat.loading = false
        }

        if (!streamingMsg.content || streamingMsg.content.trim() === '') {
          streamingMsg.content = '응답이 없습니다.'
        }
        // streaming 분기는 이미 push 했으므로 후속 assistantMessage 처리 skip
        assistantMessage = streamingMsg
      } else {
        const response = await api.post('/chat/send', {
          serviceId: chat.service.serviceId,
          model: modelSettings.value.model,
          temperature: modelSettings.value.temperature / 100,
          maxTokens: modelSettings.value.maxTokens,
          messages: requestMessages,
          stream: false,
          enableWebSearch: enableWebSearch.value && (chat.service.serviceCode?.toLowerCase() === 'chatgpt' || chat.service.serviceCode?.toLowerCase() === 'openai'),
          enableRag: enableRag.value,
          ragTopK: 5,
          language: responseLanguage.value
        })

        assistantMessage = {
          messageId: response.data.messageId,
          role: 'assistant',
          content: response.data.content || '응답이 없습니다.',
          createdAt: new Date(),
          citations: response.data.citations || undefined,
          // 트랙 #97-post5 — 발화 출처 영구 보존 (신규 conversation 분기)
          originServiceCode: chat.service?.serviceCode,
          originServiceName: chat.service?.serviceName,
          originIconClass: chat.service?.iconClass,
          originColorCode: chat.service?.colorCode,
          originModel: (response.data as any).model || chat.model
        }

        // response에서 conversationId가 오면 저장
        // DirectSendMessageResponseDto에 conversationId가 포함되어 있음
        if ((response.data as any).conversationId) {
          const newConversationId = (response.data as any).conversationId
          // 트랙 #97-post7 (2026-05-18) — race fix (Nexus 첫 응답 미표시 결함):
          //   기존 결함: currentMessages 백업이 assistantMessage push 전에 일어나 백업에 누락.
          //   loadConversations 가 `chats.value = [...convertedChats, ...existingLocalChats]` 통째 교체 →
          //   옛 chat reference 는 chats.value 에 없음 (existingLocalChats 는 conversationId 없는 것만) →
          //   updatedChat.messages = currentMessages (assistantMessage 누락) → 화면 빈 응답.
          //   F5 시 selectChat → 백엔드 메시지 로드 → 표시 (사용자 보고와 일치).
          //   fix: 백업에 assistantMessage 까지 포함하여 updatedChat 에 완전한 메시지 배열 복원.
          const currentMessages = [...chat.messages, assistantMessage]

          chat.conversationId = newConversationId
          chat.id = `conv-${newConversationId}`

          // DB에 저장된 conversation이므로 목록을 다시 로드하여 최신 상태 반영
          await loadConversations()

          // 로드 후 현재 채팅 찾기
          const updatedChat = chats.value.find(c => c.conversationId === newConversationId)
          if (updatedChat) {
            currentChatId.value = updatedChat.id
            // 작업 중 메시지 + assistantMessage 까지 영구 보존 (post7 fix)
            updatedChat.messages = currentMessages
            updatedChat.updatedAt = new Date()
          }
        }
      }
    }

    // 트랙 #97-post7 — streaming 분기는 이미 push 했으므로 중복 push 방지
    if (assistantMessage && !chat.messages.includes(assistantMessage)) {
      chat.messages.push(assistantMessage)
      chat.updatedAt = new Date()
    }
  } catch (error: any) {
    console.error('Error sending message:', error)
    const errorMessage: Message = {
      tempId: `error-${Date.now()}`,
      role: 'assistant',
      content: '오류가 발생했습니다: ' + (error.response?.data?.message || error.message),
      createdAt: new Date()
    }
    chat.messages.push(errorMessage)
  } finally {
    chat.loading = false
    // 전역 loading 은 "다른 채팅이 동시 진행 중이면 true 유지, 아니면 false". 입력창/스피너 표시용.
    loading.value = chats.value.some(c => c.loading === true)
    await scrollToBottom()
    await nextTick()
    setupCitationClickHandlers()
  }
}

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

const formatChatTime = (date: Date): string => {
  const now = new Date()
  const chatDate = new Date(date)
  const diffMs = now.getTime() - chatDate.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return '방금'
  if (diffMins < 60) return `${diffMins}분 전`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}시간 전`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}일 전`
  return chatDate.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

// URL 안전하게 가져오기
const getFileUrl = (url: string | null | undefined): string => {
  if (!url || typeof url !== 'string') return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  if (typeof window !== 'undefined' && window.location && window.location.origin) {
    return `${window.location.origin}${url}`
  }
  return url
}

const getAttachmentUrl = (url: string | null | undefined): string => {
  return getFileUrl(url)
}

// 파일 다운로드 URL 생성 (API 엔드포인트 사용)
const getFileDownloadUrl = (url: string | null | undefined): string => {
  if (!url || typeof url !== 'string') return ''
  
  // 이미 전체 URL인 경우 API 엔드포인트로 변환
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const urlObj = new URL(url)
      const filePath = urlObj.pathname
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
  
  return url
}

// 파일 다운로드 핸들러
const downloadFile = async (attachment: { type: string; url?: string | null; name: string }) => {
  try {
    if (!attachment.url || typeof attachment.url !== 'string') {
      alert('파일 URL이 없습니다.')
      return
    }
    
    const downloadUrl = getFileDownloadUrl(attachment.url)
    if (!downloadUrl) {
      alert('파일 다운로드 URL을 생성할 수 없습니다.')
      return
    }
    
    const response = await api.get(downloadUrl, {
      responseType: 'blob'
    })
    
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
    alert('파일 다운로드에 실패했습니다: ' + (error.response?.data?.message || error.message))
  }
}

// 이미지 소스 가져오기 (preview 우선, 없으면 URL 사용)
const getImageSource = (attachment: { type: string; url?: string | null; name: string; preview?: string }): string => {
  // Base64 preview가 있으면 우선 사용
  if (attachment.preview) {
    return attachment.preview
  }
  // preview가 없으면 URL 사용
  if (attachment.url && typeof attachment.url === 'string') {
    // data URL인 경우 그대로 반환 (Base64 이미지)
    if (attachment.url.startsWith('data:')) {
      return attachment.url
    }
    // 일반 URL인 경우 getAttachmentUrl 사용
    return getAttachmentUrl(attachment.url)
  }
  return ''
}

// 이미지 다운로드 핸들러
const downloadImage = async (imageUrl: string, filename: string) => {
  try {
    if (!imageUrl || typeof imageUrl !== 'string') {
      alert('이미지 URL이 없습니다.')
      return
    }
    
    const downloadFilename = filename || `image-${Date.now()}.png`
    
    // data URL인 경우 (Base64 이미지) 직접 다운로드
    if (imageUrl.startsWith('data:')) {
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
    
    // 이미지 URL이 외부 URL인 경우 백엔드 프록시를 통해 다운로드
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      const downloadUrl = `/api/image-generation/download?imageUrl=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(downloadFilename)}`
      
      const response = await api.get(downloadUrl, {
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
    } else {
      // 내부 URL인 경우
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
    alert('이미지 다운로드에 실패했습니다: ' + (error.response?.data?.message || error.message || '알 수 없는 오류'))
  }
}

// 이미지 로드 에러 처리
const handleImageError = (event: Event, attachment: { type: string; url?: string | null; name: string; preview?: string }) => {
  const img = event.target as HTMLImageElement
  // 이미 URL을 사용하고 있었는데 에러가 난 경우, preview로 재시도
  if (attachment.preview && img.src !== attachment.preview) {
    console.warn('[handleImageError] Image URL failed, trying preview:', attachment.url || 'N/A')
    img.src = attachment.preview
    img.onerror = null // 무한 루프 방지
  } else {
    console.error('[handleImageError] Image failed to load:', {
      name: attachment.name,
      url: attachment.url || 'N/A',
      hasPreview: !!attachment.preview
    })
    img.alt = `이미지를 불러올 수 없습니다: ${attachment.name}`
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
    
    // marked의 커스텀 렌더러가 이미 코드 블록을 올바르게 처리
    // HTML 코드 블록은 렌더러에서 직접 처리되므로 추가 처리 불필요
    let html = marked.parse(processedContent) as string
    
    // Perplexity citation 번호 [1], [2] 등을 클릭 가능한 링크로 변환
    if (citations && citations.length > 0) {
      html = html.replace(/\[(\d+)\]/g, (match, num) => {
        const index = parseInt(num) - 1
        if (index >= 0 && index < citations.length) {
          return `<a href="#citation-${messageId}-${num}" class="citation-number" data-citation-id="citation-${messageId}-${num}" title="${citations[index]}">[${num}]</a>`
        }
        return match
      })
    }
    
    // 테이블에 Bootstrap 클래스 추가
    html = html.replace(/<table>/g, '<table class="table table-bordered table-striped table-hover">')
    html = html.replace(/<thead>/g, '<thead class="table-light">')
    
    if (typeof window !== 'undefined') {
      // 코드 블록을 임시로 마스킹하여 DOMPurify가 건드리지 않도록 함
      const codeBlockPlaceholders: string[] = []
      html = html.replace(/<pre[^>]*><code[^>]*>[\s\S]*?<\/code><\/pre>/gi, (match) => {
        const placeholder = `__CODE_BLOCK_${codeBlockPlaceholders.length}__`
        codeBlockPlaceholders.push(match)
        return placeholder
      })
      
      // 나머지 HTML을 DOMPurify로 처리
      html = DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
          'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
          'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'ul', 'ol', 'li', 'blockquote',
          'table', 'thead', 'tbody', 'tr', 'th', 'td',
          'a', 'img',
          'hr', 'div', 'span'
        ],
        ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel', 'id', 'data-citation-id'],
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
    
    return html
  } catch (error) {
    console.error('Error parsing markdown:', error)
    return content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

// Citation 번호 클릭 이벤트 핸들러 설정
const setupCitationClickHandlers = () => {
  if (typeof document === 'undefined') return
  
  const citationLinks = document.querySelectorAll('.message-text .citation-number')
  citationLinks.forEach(link => {
    link.removeEventListener('click', handleCitationClick as EventListener)
    link.addEventListener('click', handleCitationClick as EventListener)
  })
}

const handleCitationClick = (event: Event) => {
  event.preventDefault()
  const target = event.currentTarget as HTMLElement
  const citationId = target.getAttribute('data-citation-id') || target.getAttribute('href')?.replace('#', '')
  
  if (citationId) {
    scrollToCitation(citationId)
  }
}

const scrollToCitation = (citationId: string) => {
  const element = document.getElementById(citationId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.classList.add('citation-highlight')
    setTimeout(() => {
      element.classList.remove('citation-highlight')
    }, 2000)
  }
}

const useSuggestedPrompt = (text: string) => {
  inputMessage.value = text
  charCount.value = text.length
}

const updateCharCount = () => {
  charCount.value = inputMessage.value.length
}

// ── 파일 첨부 ──────────────────────────────────────────────────
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadingFile = ref(false)

// 트랙 #88 H2 — 첨부 영속화
// 컴포넌트 unmount 와 무관하게 탭 동안 유지되도록 sessionStorage 와 동기화한다.
// `preview` 필드는 blob:// URL 이라 다음 mount 시 무효하므로 직렬화에서 제외한다.
interface PendingAttachment {
  type: 'image' | 'file'
  url: string
  name: string
  preview?: string
}

/** sessionStorage 에서 초기 첨부 목록을 복원한다. 파싱 실패 시 빈 배열. */
const loadPendingAttachments = (): PendingAttachment[] => {
  const raw = safeGetSessionStorage(ATTACH_STORAGE_KEY)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    // 백엔드 영구 URL 만 신뢰. preview 같은 휘발성 필드는 무시한다.
    return parsed
      .filter((a: any) => a && typeof a.url === 'string' && a.url.length > 0)
      .map((a: any): PendingAttachment => ({
        type: a.type === 'file' ? 'file' : 'image',
        url: String(a.url),
        name: String(a.name || '첨부 파일')
      }))
  } catch (e) {
    console.warn('[MultiChat] pendingAttachments 복원 실패:', e)
    return []
  }
}

/** 현재 첨부 목록을 sessionStorage 에 저장. preview 는 직렬화 제외. */
const persistPendingAttachments = (list: PendingAttachment[]): void => {
  if (list.length === 0) {
    safeRemoveSessionStorage(ATTACH_STORAGE_KEY)
    return
  }
  const minimal = list.map(a => ({ type: a.type, url: a.url, name: a.name }))
  safeSetSessionStorage(ATTACH_STORAGE_KEY, JSON.stringify(minimal))
}

const pendingAttachments = ref<PendingAttachment[]>(loadPendingAttachments())

// 첨부 목록 변경 시 자동으로 sessionStorage 에 동기화 (deep watch)
watch(pendingAttachments, (list) => {
  persistPendingAttachments(list)
}, { deep: true })

const attachFile = () => {
  fileInputRef.value?.click()
}

const handleFileSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  input.value = '' // 같은 파일 재선택 허용

  uploadingFile.value = true
  try {
    const isImage = file.type.startsWith('image/')
    const endpoint = isImage ? '/files/upload/image' : '/files/upload'
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder', 'chat-attachments')

    const response = await api.post(endpoint, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    const url = response.data?.url || response.data?.filePath || ''
    const attachment = {
      type: isImage ? ('image' as const) : ('file' as const),
      url,
      name: file.name,
      preview: isImage ? URL.createObjectURL(file) : undefined
    }
    pendingAttachments.value.push(attachment)
  } catch (err) {
    console.error('파일 업로드 실패:', err)
    alert('파일 업로드에 실패했습니다.')
  } finally {
    uploadingFile.value = false
  }
}

const removePendingAttachment = (idx: number) => {
  const att = pendingAttachments.value[idx]
  if (att?.preview?.startsWith('blob:')) URL.revokeObjectURL(att.preview)
  pendingAttachments.value.splice(idx, 1)
}

const saveSettings = () => {
  if (currentChat.value) {
    currentChat.value.model = modelSettings.value.model
    currentChat.value.temperature = modelSettings.value.temperature
    currentChat.value.maxTokens = modelSettings.value.maxTokens
  }
  showSettingsModal.value = false
}

watch([loading, currentChat], ([newLoading, newChat]) => {
  isButtonDisabled.value = newLoading || !newChat || !newChat.service
}, { immediate: true })

watch(() => currentMessages.value.length, async () => {
  await scrollToBottom()
  await nextTick()
  setupCitationClickHandlers()
})

watch(() => currentChatId.value, async () => {
  await nextTick()
  setupCitationClickHandlers()
})

onMounted(async () => {
  await loadServices()
  await loadConversations()
  if (chats.value.length === 0) {
    createNewChat()
  } else {
    // 첫 번째 conversation 선택
    const firstChat = chats.value[0]
    currentChatId.value = firstChat.id
    // selectChat을 통해 서비스 및 모델 설정
    await selectChat(firstChat.id)
  }
})

// 트랙 #88 H2 — 컴포넌트 unmount 시 blob URL 메모리 누수 방지.
// pendingAttachments 자체는 sessionStorage 에 영속화되어 있어 재mount 시 복원되지만,
// 이전 mount 에서 만든 blob: preview 는 OS 측에 묶여 있어 명시적으로 revokeObjectURL 호출이 필요하다.
// (sessionStorage 에는 preview 가 저장되지 않으므로, blob 해제로 인해 다른 곳의 표시가 깨지지 않는다.)
onBeforeUnmount(() => {
  for (const att of pendingAttachments.value) {
    if (att.preview?.startsWith('blob:')) {
      try {
        URL.revokeObjectURL(att.preview)
      } catch (e) {
        // 이미 해제된 경우 등은 무시
      }
    }
  }
})
</script>

<style scoped>
.chat-sidebar {
  height: calc(100vh - 56px);
  overflow-y: auto;
  border-right: 1px solid #e5e7eb;
  background: #f9fafb;
}

.chat-list-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.2s;
  position: relative;
}

.chat-list-item:hover {
  background: #f3f4f6;
}

.chat-list-item.active {
  background: white;
  border-left: 3px solid #4F46E5;
}

.chat-list-item .chat-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
  padding-right: 60px;
}

.chat-list-item .chat-preview {
  font-size: 0.75rem;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 60px;
}

.chat-list-item .chat-time {
  font-size: 0.7rem;
  color: #9ca3af;
  position: absolute;
  top: 12px;
  right: 16px;
}

.chat-list-item .delete-chat {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-list-item:hover .delete-chat {
  opacity: 1;
}

.chat-list-item:hover .chat-time {
  opacity: 0;
}

.chat-container {
  height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
}

/* 채팅 헤더 스타일 */
.chat-header {
  position: relative;
  z-index: 10;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chat-container .p-3.bg-white {
  position: relative;
  z-index: 10;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chat-header-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.5;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: white;
}

.message {
  margin-bottom: 24px;
  animation: slideInMessage 0.3s ease-out;
}

.message-user {
  display: flex;
  justify-content: flex-end;
}

.message-assistant {
  display: flex;
  justify-content: flex-start;
}

.message-content {
  max-width: 75%;
  width: fit-content;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 0.875rem;
  line-height: 1.6;
  color: inherit;
}

/* 사용자 메시지 - 보라색 배경에 흰색 텍스트 */
.message-user .message-content {
  background: #4F46E5 !important;
  border-bottom-right-radius: 4px;
}

.message-user .message-content .message-text {
}

/* Assistant 메시지 - 회색 배경에 어두운 텍스트 */
.message-assistant .message-content {
  background: #f8f9fa !important;
  color: #1f2937 !important;
  border-bottom-left-radius: 4px;
  border-left: 3px solid #4F46E5;
  line-height: 1.7 !important;
}

.message-assistant .message-content .message-text {
  color: #1f2937 !important;
}

/* Assistant 메시지 내부 모든 요소 - 어두운 색상 강제 적용 (흰색 제외) */
.message-assistant .message-content,
.message-assistant .message-content *,
.message-assistant .message-content .message-text,
.message-assistant .message-content .message-text :deep(*),
.message-assistant .message-content .message-text :deep(p),
.message-assistant .message-content .message-text :deep(span),
.message-assistant .message-content .message-text :deep(div),
.message-assistant .message-content .message-text :deep(li),
.message-assistant .message-content .message-text :deep(ul),
.message-assistant .message-content .message-text :deep(ol),
.message-assistant .message-content .message-text :deep(h1),
.message-assistant .message-content .message-text :deep(h2),
.message-assistant .message-content .message-text :deep(h3),
.message-assistant .message-content .message-text :deep(h4),
.message-assistant .message-content .message-text :deep(h5),
.message-assistant .message-content .message-text :deep(h6) {
  color: #1f2937 !important;
}

.message-assistant .message-content .message-text :deep(p) {
  color: #1f2937 !important;
  margin: 0.625rem 0 !important;
  line-height: 1.75 !important;
}

/* user-message-text 클래스는 흰색 */
.user-message-text {
  color: white !important;
}

/* assistant-message-text 클래스는 어두운 색상 */
.assistant-message-text {
  color: #1f2937 !important;
}

.assistant-message-text :deep(*),
.assistant-message-text :deep(p) {
  color: #1f2937 !important;
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

/* 모바일에서 폰트 크기 90%로 조정 - assistant-message-text */
@media (max-width: 768px) {
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

.message-assistant .message-content .message-text :deep(strong) {
  color: #111827 !important;
  font-weight: 600 !important;
}

.message-assistant .message-content .message-text :deep(em) {
  color: #374151 !important;
  font-style: italic !important;
}

/* 리스트 스타일 개선 */
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

.message-assistant .message-content .message-text :deep(li) {
  margin-left: -0.5rem !important;
  margin-right: 0.5rem !important;
}

.message-user .message-content .message-text :deep(li) {
  margin-left: -0.5rem !important;
  margin-right: 0.5rem !important;
}

.message-text :deep(li::marker) {
  color: inherit !important;
  opacity: 0.75;
  font-weight: 500;
}

.message-text :deep(ul ul),
.message-text :deep(ol ol) {
  margin-top: 0.375rem !important;
  margin-bottom: 0.375rem !important;
  padding-left: 1.25rem !important;
}

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

/* h3 크기 조정 */
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
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.75rem;
}

.message-user .message-content .message-header {
  color: white !important;
}

.message-user .message-content .message-header strong {
  color: white !important;
}

.message-user .message-content .message-header small {
  color: rgba(255, 255, 255, 0.8) !important;
}

.message-assistant .message-content .message-header {
  color: #374151 !important;
}

.message-assistant .message-content .message-header small {
  color: #6b7280 !important;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  margin: 0 8px;
  flex-shrink: 0;
  background-color: #6c757d;
}

/* 서비스별 아바타 배경색 */
.service-avatar-chatgpt,
.service-avatar-openai {
  background-color: #00c9ff !important;
}

.service-avatar-claude,
.service-avatar-anthropic {
  background-color: #667eea !important;
}

.service-avatar-gemini,
.service-avatar-google {
  background-color: #e65100 !important;
}

.service-avatar-perplexity {
  background-color: #2e7d32 !important;
}

.service-avatar-default {
  background-color: #6c757d !important;
}

.message-user .message-avatar {
  background-color: #4F46E5 !important;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
}

.empty-chat i {
  font-size: 4rem;
  margin-bottom: 16px;
  color: #d1d5db;
}

.chat-input-area {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.chat-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  resize: none;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  max-height: 100px;
  min-height: 40px;
  line-height: 1.5;
  overflow-y: auto;
}

.chat-input:focus {
  outline: none;
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.send-button {
  height: 48px;
  width: 48px;
  border-radius: 12px;
  border: none;
  background: #4F46E5;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.send-button:hover:not(.btn-disabled) {
  background: #4338CA;
  transform: translateY(-1px);
}

.send-button.btn-disabled {
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
  transform: none;
  pointer-events: none;
}

.service-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}

/* 서비스 선택 탭 개선된 스타일 */
/* 서비스 선택 그리드 레이아웃 (여러 줄로 표시) */
.service-selector-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  width: 100%;
}

.service-selector-wrapper {
  position: relative;
}

.service-selector-scroll {
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db transparent;
}

.service-selector-scroll::-webkit-scrollbar {
  height: 4px;
}

.service-selector-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.service-selector-scroll::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.service-selector-scroll::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

.service-selector-btn {
  padding: 0.5rem 0.875rem;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  background: #ffffff;
  color: #6b7280;
  font-weight: 500;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  position: relative;
  overflow: hidden;
  flex: 0 1 auto;
  min-width: 0;
}

.service-selector-btn:hover:not(.service-selector-active) {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #374151;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.service-selector-btn:active:not(.service-selector-active) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.service-selector-btn.service-selector-active {
  color: white !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
  font-weight: 600;
}

.service-selector-btn.service-selector-active:hover {
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.service-chatgpt,
.service-openai {
  background: #e0f2f1;
  color: #00796b;
}

.service-claude,
.service-anthropic {
  background: #ede7f6;
  color: #5e35b1;
}

.service-gemini,
.service-google {
  background: #fff3e0;
  color: #e65100;
}

.service-perplexity {
  background: #e8f5e9;
  color: #2e7d32;
}

/* ═══ mc-modal 스타일 (multi-chat.html 참조) ═══ */
.mc-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9000;
  display: none;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(5px);
  padding: 20px;
}
.mc-modal-overlay.open {
  display: flex;
  animation: mcFade 0.2s ease;
}
@keyframes mcFade {
  from { opacity: 0; }
  to { opacity: 1; }
}

.mc-modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.2);
  animation: mcSlide 0.22s ease;
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}
@keyframes mcSlide {
  from { transform: translateY(16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.mc-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px 14px;
  border-bottom: 1px solid #e5e7eb;
}
.mc-modal-title {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: #111827;
}

.mc-modal-body {
  padding: 20px 22px;
  overflow-y: auto;
  flex: 1;
}
.mc-modal-body::-webkit-scrollbar { width: 4px; }
.mc-modal-body::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }

.mc-modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 22px 16px;
  border-top: 1px solid #e5e7eb;
  background: #f8fafc;
  border-radius: 0 0 16px 16px;
}

/* mc-slider (Temperature) */
.mc-slider-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.mc-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(to right, #4F46E5 35%, #e5e7eb 35%);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}
.mc-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #4F46E5;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(79, 70, 229, 0.4);
  cursor: pointer;
}
.mc-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #4F46E5;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(79, 70, 229, 0.4);
  cursor: pointer;
}
.mc-slider-val {
  min-width: 30px;
  text-align: right;
  font-size: 12px;
  font-weight: 700;
  color: #4F46E5;
  background: #eef2ff;
  padding: 2px 6px;
  border-radius: 4px;
}
.mc-slider-hints {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 10px;
}

/* 이미지 확대 모달 (mc-modal 스타일 적용) */
.mc-image-modal.mc-modal-overlay {
  background: rgba(0, 0, 0, 0.8);
}
.mc-image-modal .mc-modal {
  max-width: 90vw;
  max-height: 90vh;
  background: transparent;
  box-shadow: none;
}
.mc-image-modal .mc-modal-header {
  background: transparent;
}
.mc-image-modal .mc-modal-title {
  color: #fff;
}
.mc-image-modal .mc-modal-body {
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
}
.mc-image-modal .mc-modal-body img {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 8px;
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
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

.message-text :deep(.citation-number:hover) {
  color: #6366F1 !important;
  background-color: rgba(79, 70, 229, 0.2);
  transform: scale(1.1);
}

.message-user .message-content .message-text :deep(.citation-number) {
}

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

/* 테이블 스타일 */
.message-text :deep(.table) {
  width: 100%;
  margin: 1rem 0;
  font-size: 0.9rem;
}

.message-text :deep(.table th) {
  background-color: #f8f9fa;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
  padding: 0.75rem;
}

.message-text :deep(.table td) {
  padding: 0.75rem;
  vertical-align: top;
  border-bottom: 1px solid #dee2e6;
}

.message-text :deep(.table tbody tr:hover) {
  background-color: #f8f9fa;
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

/* 마크다운 코드 스타일 (기존 유지) */
.message-text :deep(.markdown-code) {
  background: none !important;
  padding: 0 !important;
  border: none !important;
  color: inherit !important;
  font-size: inherit !important;
}

.message-assistant .message-content .message-text :deep(.markdown-code) {
  background-color: #f1f3f5;
  color: #d63384;
  border-color: #dee2e6;
}

.message-user .message-content .message-text :deep(.markdown-code) {
}

/* 코드 블록 스타일 */
.message-text :deep(pre),
.message-text :deep(.markdown-code-block) {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px 16px;
  margin: 12px 0;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #212529;
}

.message-text :deep(pre code),
.message-text :deep(.markdown-code-block code) {
  background-color: transparent;
  color: #212529;
  padding: 0;
  border: none;
  font-size: inherit;
  font-weight: normal;
}

.message-assistant .message-content .message-text :deep(pre),
.message-assistant .message-content .message-text :deep(.markdown-code-block) {
  background-color: #f8f9fa;
  border-left: 3px solid #4F46E5;
}

.message-user .message-content .message-text :deep(pre),
.message-user .message-content .message-text :deep(.markdown-code-block) {
  border-left: 3px solid rgba(255, 255, 255, 0.5) !important;
}

.message-user .message-content .message-text :deep(pre code),
.message-user .message-content .message-text :deep(.markdown-code-block code) {
  background-color: transparent !important;
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

/* C# 코드 블록 내부 (code 태그) - Prism.js와 통합 */
.message-text :deep(pre code.language-csharp),
.message-text :deep(pre.language-csharp code) {
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

/* Prism.js 토큰 스타일 오버라이드 - C# */
.message-text :deep(pre code.language-csharp .token.keyword),
.message-text :deep(pre.language-csharp code .token.keyword) {
  color: #56b6c2 !important;
  font-weight: 600 !important;
}

.message-text :deep(pre code.language-csharp .token.class-name),
.message-text :deep(pre.language-csharp code .token.class-name) {
  color: #e5c07b !important;
  font-weight: 500 !important;
}

.message-text :deep(pre code.language-csharp .token.function),
.message-text :deep(pre.language-csharp code .token.function) {
  color: #61afef !important;
  font-weight: 500 !important;
}

.message-text :deep(pre code.language-csharp .token.string),
.message-text :deep(pre.language-csharp code .token.string) {
  color: #98c379 !important;
}

.message-text :deep(pre code.language-csharp .token.number),
.message-text :deep(pre.language-csharp code .token.number) {
  color: #d19a66 !important;
}

.message-text :deep(pre code.language-csharp .token.comment),
.message-text :deep(pre.language-csharp code .token.comment) {
  color: #7f848e !important;
  font-style: italic !important;
}

.message-text :deep(pre code.language-csharp .token.attr-name),
.message-text :deep(pre.language-csharp code .token.attr-name),
.message-text :deep(pre code.language-csharp .token.attribute),
.message-text :deep(pre.language-csharp code .token.attribute) {
  color: #c678dd !important;
}

.message-text :deep(pre code.language-csharp .token.preprocessor),
.message-text :deep(pre.language-csharp code .token.preprocessor) {
  color: #be5046 !important;
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

@keyframes slideInMessage {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── 마크다운 렌더링 스타일 ─────────────────────────────────────────────── */
.mc-msg-bubble {
  font-size: 13px;
  line-height: 1.7;
  word-break: break-word;
}

/* 헤딩 — 브라우저 기본값(h1=2em, h2=1.5em) 완전 재정의 */
.mc-msg-bubble :deep(.markdown-heading) {
  font-weight: 700 !important;
  line-height: 1.35 !important;
  margin: 1em 0 0.35em !important;
  color: #111827 !important;
}
.mc-msg-bubble :deep(.markdown-heading:first-child) { margin-top: 0 !important; }
.mc-msg-bubble :deep(h1.markdown-h1) {
  font-size: 15px !important;
  padding-bottom: 0.25em !important;
  border-bottom: 2px solid #e5e7eb !important;
}
.mc-msg-bubble :deep(h2.markdown-h2) {
  font-size: 14px !important;
  padding-bottom: 0.2em !important;
  border-bottom: 1px solid #e5e7eb !important;
}
.mc-msg-bubble :deep(h3.markdown-h3) {
  font-size: 13.5px !important;
  color: #374151 !important;
}
.mc-msg-bubble :deep(h4.markdown-h4),
.mc-msg-bubble :deep(h5.markdown-h5),
.mc-msg-bubble :deep(h6.markdown-h6) {
  font-size: 13px !important;
  color: #6b7280 !important;
}

/* 단락 */
.mc-msg-bubble :deep(.markdown-paragraph) {
  margin: 0 0 0.7em;
  line-height: 1.75;
}
.mc-msg-bubble :deep(.markdown-paragraph:last-child) { margin-bottom: 0; }

/* 목록 */
.mc-msg-bubble :deep(.markdown-ul),
.mc-msg-bubble :deep(.markdown-ol) {
  margin: 0.3em 0 0.75em;
  padding-left: 1.5em;
}
.mc-msg-bubble :deep(.markdown-ul) { list-style: disc; }
.mc-msg-bubble :deep(.markdown-ol) { list-style: decimal; }
.mc-msg-bubble :deep(.markdown-ul .markdown-ul) {
  list-style: circle;
  margin: 0.2em 0;
}
.mc-msg-bubble :deep(.markdown-list-item) {
  margin: 0.28em 0;
  line-height: 1.7;
}
.mc-msg-bubble :deep(.markdown-list-item::marker) { color: #6366f1; }

/* 인라인 코드 */
.mc-msg-bubble :deep(code:not(pre code)) {
  background: rgba(99,102,241,0.08);
  color: #6366f1;
  border: 1px solid rgba(99,102,241,0.18);
  border-radius: 5px;
  padding: 1px 6px;
  font-size: 0.85em;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

/* 코드 블록 */
.mc-msg-bubble :deep(pre) {
  background: #1e1e2e;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 13px 15px;
  margin: 0.5em 0 0.9em;
  overflow-x: auto;
}
.mc-msg-bubble :deep(pre code) {
  background: none;
  border: none;
  color: #cdd6f4;
  font-size: 0.8em;
  line-height: 1.65;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  padding: 0;
}

/* 인용문 */
.mc-msg-bubble :deep(blockquote) {
  border-left: 3px solid #6366f1;
  background: rgba(99,102,241,0.05);
  margin: 0.5em 0;
  padding: 7px 13px;
  border-radius: 0 8px 8px 0;
  color: #4b5563;
  font-style: italic;
}

/* 구분선 */
.mc-msg-bubble :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 0.9em 0;
}

/* 표 */
.mc-msg-bubble :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5em 0 0.9em;
  font-size: 0.87em;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.mc-msg-bubble :deep(th) {
  background: #6366f1;
  color: #fff;
  padding: 7px 11px;
  text-align: left;
  font-weight: 600;
  font-size: 0.85em;
}
.mc-msg-bubble :deep(td) {
  padding: 6px 11px;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: top;
}
.mc-msg-bubble :deep(tr:last-child td) { border-bottom: none; }
.mc-msg-bubble :deep(tr:nth-child(even) td) { background: rgba(99,102,241,0.03); }

/* 굵게 / 이탤릭 */
.mc-msg-bubble :deep(strong) { font-weight: 700; }
.mc-msg-bubble :deep(em) { font-style: italic; color: #4b5563; }

/* ── 파일 첨부 미리보기 ── */
.mc-attach-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 6px 12px 0;
}
.mc-attach-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(79,70,229,.1);
  border: 1px solid rgba(79,70,229,.25);
  border-radius: 20px;
  font-size: 0.78rem;
  color: var(--ai-primary, #4f46e5);
  max-width: 200px;
}
.mc-attach-chip span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.btn-chip-remove {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--ai-primary, #4f46e5);
  line-height: 1;
  font-size: 0.75rem;
  opacity: 0.7;
  flex-shrink: 0;
}
.btn-chip-remove:hover { opacity: 1; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
