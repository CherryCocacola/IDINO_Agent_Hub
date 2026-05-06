<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminKb.detailTitle') }}</h1>
        <p class="page-desc">{{ t('adminKb.detailSubtitle') }}</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-outline-secondary btn-sm me-2" @click="goBack">
          <i class="bi bi-arrow-left" aria-hidden="true"></i>
          {{ t('common.back') }}
        </button>
        <button
          v-if="store.currentDocument"
          class="btn btn-outline-danger btn-sm"
          @click="onDelete"
          :disabled="store.isLoading"
        >
          <i class="bi bi-trash" aria-hidden="true"></i>
          {{ t('adminKb.delete') }}
        </button>
      </div>
    </div>

    <div v-if="store.error" class="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
      <span>{{ store.error }}</span>
      <button type="button" class="btn-close" :aria-label="t('common.close')" @click="store.clearError"></button>
    </div>

    <!-- 로딩 -->
    <div v-if="store.isLoading && !store.currentDocument" class="card aiuiux-card">
      <div class="card-body text-center py-5">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">{{ t('common.loading') }}</span>
        </div>
      </div>
    </div>

    <!-- 미존재 -->
    <div v-else-if="!store.currentDocument" class="card aiuiux-card">
      <div class="card-body text-center text-muted py-5">
        <i class="bi bi-question-circle fs-2 d-block mb-2" aria-hidden="true"></i>
        <p class="mb-0">{{ t('adminKb.notFound') }}</p>
      </div>
    </div>

    <!-- 상세 -->
    <template v-else>
      <div class="row g-3">
        <div class="col-md-7">
          <div class="card aiuiux-card">
            <div class="card-header bg-transparent border-bottom">
              <h6 class="mb-0">
                <i class="bi bi-file-earmark-text me-1" aria-hidden="true"></i>
                {{ t('adminKb.metadata') }}
              </h6>
            </div>
            <div class="card-body">
              <dl class="row mb-0 small">
                <dt class="col-sm-4 text-muted">{{ t('adminKb.docName') }}</dt>
                <dd class="col-sm-8 fw-medium">{{ store.currentDocument.name }}</dd>

                <dt class="col-sm-4 text-muted">{{ t('adminKb.docId') }}</dt>
                <dd class="col-sm-8"><code>{{ store.currentDocument.id }}</code></dd>

                <dt class="col-sm-4 text-muted">{{ t('adminKb.docStatus') }}</dt>
                <dd class="col-sm-8">
                  <span class="badge bg-secondary-subtle text-secondary-emphasis">
                    {{ store.currentDocument.status }}
                  </span>
                </dd>

                <dt class="col-sm-4 text-muted">{{ t('adminKb.docCreatedAt') }}</dt>
                <dd class="col-sm-8">{{ formatDate(store.currentDocument.createdAt) }}</dd>

                <dt class="col-sm-4 text-muted">{{ t('adminKb.uploaderName') }}</dt>
                <dd class="col-sm-8">{{ store.currentDocument.uploaderName || '-' }}</dd>

                <dt class="col-sm-4 text-muted">{{ t('adminKb.visibility') }}</dt>
                <dd class="col-sm-8">
                  <code v-if="store.currentDocument.visibilityTargets" class="small">
                    {{ JSON.stringify(store.currentDocument.visibilityTargets) }}
                  </code>
                  <span v-else class="text-muted">-</span>
                </dd>
              </dl>
            </div>
          </div>
        </div>
        <div class="col-md-5">
          <div class="card aiuiux-card">
            <div class="card-header bg-transparent border-bottom">
              <h6 class="mb-0">
                <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
                {{ t('adminKb.summary') }}
              </h6>
            </div>
            <div class="card-body">
              <ul class="list-unstyled mb-0 small">
                <li class="d-flex justify-content-between mb-2">
                  <span class="text-muted">{{ t('adminKb.chunkCount') }}</span>
                  <span class="fw-medium">{{ store.currentChunks.length }}</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- 청크 목록 -->
      <div class="card aiuiux-card mt-3">
        <div class="card-header bg-transparent border-bottom d-flex align-items-center">
          <h6 class="mb-0 me-2">
            <i class="bi bi-list-columns-reverse me-1" aria-hidden="true"></i>
            {{ t('adminKb.chunks') }}
          </h6>
          <span class="badge bg-secondary-subtle text-secondary-emphasis">
            {{ store.currentChunks.length }}
          </span>
        </div>
        <div class="card-body p-0">
          <div v-if="store.currentChunks.length === 0" class="text-center text-muted py-4">
            <small>{{ t('adminKb.chunksEmpty') }}</small>
          </div>
          <ul v-else class="list-group list-group-flush">
            <li
              v-for="chunk in store.currentChunks"
              :key="chunk.chunkId"
              class="list-group-item"
            >
              <div class="d-flex justify-content-between align-items-start mb-1">
                <span class="badge bg-primary-subtle text-primary-emphasis">
                  #{{ chunk.chunkIndex }}
                </span>
                <code class="text-muted small">{{ chunk.chunkId }}</code>
              </div>
              <p class="mb-0 small chunk-text">{{ chunk.content }}</p>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDocUtilStore } from '@/stores/docUtilStore'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const store = useDocUtilStore()

function load(): void {
  const id = route.params.id
  if (typeof id === 'string' && id.length > 0) {
    store.loadDocumentDetail(id)
  }
}

async function onDelete(): Promise<void> {
  if (!store.currentDocument) return
  const message = t('adminKb.deleteConfirm', { name: store.currentDocument.name })
  if (!window.confirm(message)) return
  const success = await store.removeDocument(store.currentDocument.id)
  if (success) {
    router.push({ name: 'AdminKnowledgeBase' })
  }
}

function goBack(): void {
  router.push({ name: 'AdminKnowledgeBase' })
}

function formatDate(value: string | null): string {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return value
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<style scoped>
.chunk-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
  color: var(--ai-text, #212529);
}
</style>
