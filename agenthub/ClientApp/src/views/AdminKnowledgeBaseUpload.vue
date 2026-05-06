<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminKb.uploadTitle') }}</h1>
        <p class="page-desc">{{ t('adminKb.uploadSubtitle') }}</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-outline-secondary btn-sm" @click="goBack">
          <i class="bi bi-arrow-left" aria-hidden="true"></i>
          {{ t('common.back') }}
        </button>
      </div>
    </div>

    <div v-if="store.error" class="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
      <span>{{ store.error }}</span>
      <button type="button" class="btn-close" :aria-label="t('common.close')" @click="store.clearError"></button>
    </div>

    <div class="card aiuiux-card">
      <div class="card-body">
        <!-- 드래그 앤 드롭 영역 -->
        <div
          class="upload-dropzone"
          :class="{ active: isDragging, 'has-file': !!selectedFile }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
          @click="onZoneClick"
          role="button"
          tabindex="0"
          :aria-label="t('adminKb.dropzoneLabel')"
          @keydown.enter.prevent="onZoneClick"
          @keydown.space.prevent="onZoneClick"
        >
          <input
            ref="fileInputRef"
            type="file"
            class="d-none"
            @change="onFileSelected"
            accept=".pdf,.txt,.csv,.xls,.xlsx,.doc,.docx,.hwp,.pptx"
          />
          <div v-if="!selectedFile" class="text-center py-5">
            <i class="bi bi-cloud-arrow-up fs-1 text-muted" aria-hidden="true"></i>
            <p class="mt-2 mb-1 fw-medium">{{ t('adminKb.dropzoneTitle') }}</p>
            <small class="text-muted">{{ t('adminKb.dropzoneHint') }}</small>
          </div>
          <div v-else class="d-flex align-items-center py-3 px-2">
            <i class="bi bi-file-earmark-text fs-3 text-primary me-3" aria-hidden="true"></i>
            <div class="flex-grow-1">
              <div class="fw-medium">{{ selectedFile.name }}</div>
              <small class="text-muted">{{ formatBytes(selectedFile.size) }}</small>
            </div>
            <button
              class="btn btn-sm btn-outline-danger"
              @click.stop="clearFile"
              :aria-label="t('adminKb.removeFile')"
            >
              <i class="bi bi-x-lg" aria-hidden="true"></i>
            </button>
          </div>
        </div>

        <!-- 메타 입력 -->
        <div class="row g-3 mt-3">
          <div class="col-md-6">
            <label for="folderIdInput" class="form-label">
              {{ t('adminKb.folderId') }}
              <span class="text-muted small">({{ t('common.optional') }})</span>
            </label>
            <input
              id="folderIdInput"
              type="text"
              class="form-control"
              v-model="folderId"
              :placeholder="t('adminKb.folderIdHint')"
            />
            <small class="form-text text-muted">{{ t('adminKb.folderIdDesc') }}</small>
          </div>
          <div class="col-md-6">
            <label for="visibilityInput" class="form-label">
              {{ t('adminKb.visibility') }}
              <span class="text-muted small">({{ t('common.optional') }})</span>
            </label>
            <select id="visibilityInput" class="form-select" v-model="visibility">
              <option value="">{{ t('adminKb.visibilityDefault') }}</option>
              <option value="public">{{ t('adminKb.visibilityPublic') }}</option>
              <option value="internal">{{ t('adminKb.visibilityInternal') }}</option>
              <option value="confidential">{{ t('adminKb.visibilityConfidential') }}</option>
            </select>
          </div>
        </div>

        <!-- 진행 상태 -->
        <div v-if="store.isUploading" class="mt-4">
          <div class="d-flex align-items-center mb-2">
            <div class="spinner-border spinner-border-sm me-2" role="status">
              <span class="visually-hidden">{{ t('adminKb.uploading') }}</span>
            </div>
            <span class="small">{{ t('adminKb.uploading') }}</span>
          </div>
          <div class="progress" role="progressbar" :aria-label="t('adminKb.uploading')">
            <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%;"></div>
          </div>
        </div>

        <div v-if="completed" class="alert alert-success mt-4 d-flex align-items-center" role="alert">
          <i class="bi bi-check-circle-fill me-2" aria-hidden="true"></i>
          <span>{{ t('adminKb.uploadSuccess') }}</span>
        </div>
      </div>

      <div class="card-footer bg-transparent d-flex justify-content-end gap-2">
        <button class="btn btn-outline-secondary" @click="goBack" :disabled="store.isUploading">
          {{ t('common.cancel') }}
        </button>
        <button
          class="btn btn-primary"
          :disabled="!selectedFile || store.isUploading"
          @click="onUpload"
        >
          <i class="bi bi-cloud-arrow-up me-1" aria-hidden="true"></i>
          {{ store.isUploading ? t('adminKb.uploading') : t('adminKb.upload') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDocUtilStore } from '@/stores/docUtilStore'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const store = useDocUtilStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const folderId = ref<string>('')
const visibility = ref<string>('')
const isDragging = ref<boolean>(false)
const completed = ref<boolean>(false)

function onZoneClick(): void {
  fileInputRef.value?.click()
}

function onFileSelected(event: Event): void {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    completed.value = false
    store.clearError()
  }
}

function onDrop(event: DragEvent): void {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
    completed.value = false
    store.clearError()
  }
}

function clearFile(): void {
  selectedFile.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

async function onUpload(): Promise<void> {
  if (!selectedFile.value) return
  completed.value = false
  const success = await store.uploadDocument(
    selectedFile.value,
    folderId.value || undefined,
    visibility.value || undefined
  )
  if (success) {
    completed.value = true
    setTimeout(() => {
      router.push({ name: 'AdminKnowledgeBase' })
    }, 800)
  }
}

function goBack(): void {
  router.push({ name: 'AdminKnowledgeBase' })
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

onMounted(() => {
  // 메인 페이지에서 folderId 쿼리 전달 시 미리 채움
  const queryFolder = route.query.folderId
  if (typeof queryFolder === 'string') {
    folderId.value = queryFolder
  }
})
</script>

<style scoped>
.upload-dropzone {
  border: 2px dashed var(--ai-border, #dee2e6);
  border-radius: 12px;
  background: var(--ai-bg-light, #f8f9fa);
  transition: all 0.2s ease;
  cursor: pointer;
  outline: none;
}

.upload-dropzone:hover,
.upload-dropzone:focus-visible {
  border-color: var(--ai-primary, #4f46e5);
  background: rgba(79, 70, 229, 0.04);
}

.upload-dropzone.active {
  border-color: var(--ai-primary, #4f46e5);
  background: rgba(79, 70, 229, 0.08);
}

.upload-dropzone.has-file {
  border-style: solid;
  cursor: default;
}
</style>
