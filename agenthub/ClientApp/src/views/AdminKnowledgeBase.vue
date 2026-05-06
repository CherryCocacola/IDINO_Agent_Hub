<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminKb.title') }}</h1>
        <p class="page-desc">{{ t('adminKb.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-outline-secondary btn-sm me-2"
          @click="goUpload"
          :aria-label="t('adminKb.upload')"
        >
          <i class="bi bi-upload" aria-hidden="true"></i>
          {{ t('adminKb.upload') }}
        </button>
        <button
          class="btn btn-primary btn-sm"
          @click="refresh"
          :disabled="store.isLoading"
          :aria-label="t('adminKb.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminKb.refresh') }}
        </button>
      </div>
    </div>

    <!-- 검색 바 -->
    <div class="card aiuiux-card mb-3">
      <div class="card-body py-2 px-3">
        <form class="d-flex gap-2 align-items-center" @submit.prevent="onSearch">
          <div class="input-group input-group-sm flex-grow-1">
            <span class="input-group-text">
              <i class="bi bi-search" aria-hidden="true"></i>
            </span>
            <input
              type="text"
              class="form-control"
              v-model="searchQuery"
              :placeholder="t('adminKb.searchPlaceholder')"
              :aria-label="t('adminKb.search')"
            />
          </div>
          <input
            type="text"
            class="form-control form-control-sm"
            style="max-width: 220px;"
            v-model="folderInput"
            :placeholder="t('adminKb.folderIdPlaceholder')"
            :aria-label="t('adminKb.folderId')"
          />
          <button type="submit" class="btn btn-sm btn-primary" :disabled="store.isSearching">
            {{ store.isSearching ? t('adminKb.searching') : t('adminKb.search') }}
          </button>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            @click="onClearSearch"
            v-if="store.lastSearchQuery"
          >
            {{ t('adminKb.clearSearch') }}
          </button>
        </form>
      </div>
    </div>

    <!-- 에러 알림 -->
    <div v-if="store.error" class="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
      <span>{{ store.error }}</span>
      <button type="button" class="btn-close" :aria-label="t('common.close')" @click="store.clearError"></button>
    </div>

    <!-- 검색 결과 -->
    <div v-if="store.lastSearchQuery" class="card aiuiux-card mb-3">
      <div class="card-header bg-transparent border-bottom">
        <h6 class="mb-0">
          <i class="bi bi-search me-1" aria-hidden="true"></i>
          {{ t('adminKb.searchResultsFor', { query: store.lastSearchQuery }) }}
          <span class="text-muted small ms-2">({{ store.searchResults.length }})</span>
        </h6>
      </div>
      <div class="card-body p-0">
        <div v-if="store.searchResults.length === 0" class="text-center text-muted py-4">
          <small>{{ t('adminKb.searchEmpty') }}</small>
        </div>
        <ul v-else class="list-group list-group-flush">
          <li v-for="hit in store.searchResults" :key="hit.id" class="list-group-item">
            <div class="d-flex justify-content-between align-items-start mb-1">
              <code class="text-muted small">{{ hit.id }}</code>
              <span class="badge bg-info-subtle text-info-emphasis">
                {{ t('adminKb.score') }}: {{ hit.score.toFixed(3) }}
              </span>
            </div>
            <p class="mb-0 small text-body-secondary preview-text">{{ truncate(hit.content, 280) }}</p>
          </li>
        </ul>
      </div>
    </div>

    <!-- 문서 목록 -->
    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
          <i class="bi bi-folder2-open me-1" aria-hidden="true"></i>
          {{ t('adminKb.documents') }}
          <span class="text-muted small ms-2" v-if="store.pagination.total > 0">
            ({{ store.pagination.total }})
          </span>
        </h6>
        <small class="text-muted" v-if="store.currentFolderId">
          {{ t('adminKb.currentFolder') }}: <code>{{ store.currentFolderId }}</code>
        </small>
      </div>
      <div class="card-body p-0">
        <div v-if="store.isLoading" class="text-center py-5">
          <div class="spinner-border spinner-border-sm" role="status">
            <span class="visually-hidden">{{ t('common.loading') }}</span>
          </div>
        </div>
        <div v-else-if="store.documents.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-inbox fs-2 d-block mb-2" aria-hidden="true"></i>
          <p class="mb-0">{{ t('adminKb.empty') }}</p>
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th scope="col">{{ t('adminKb.docName') }}</th>
                <th scope="col" style="width: 120px;">{{ t('adminKb.docStatus') }}</th>
                <th scope="col" style="width: 180px;">{{ t('adminKb.docCreatedAt') }}</th>
                <th scope="col" style="width: 200px;" class="text-end">{{ t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in store.documents" :key="doc.id">
                <td>
                  <div class="d-flex align-items-center">
                    <i class="bi bi-file-earmark-text me-2 text-primary" aria-hidden="true"></i>
                    <div>
                      <div class="fw-medium">{{ doc.name }}</div>
                      <code class="text-muted small">{{ doc.id }}</code>
                    </div>
                  </div>
                </td>
                <td>
                  <span :class="['badge', statusBadgeClass(doc.status)]">{{ doc.status }}</span>
                </td>
                <td>
                  <small class="text-muted">{{ formatDate(doc.createdAt) }}</small>
                </td>
                <td class="text-end">
                  <button
                    class="btn btn-sm btn-link"
                    @click="goDetail(doc.id)"
                    :aria-label="t('adminKb.viewDetail')"
                  >
                    <i class="bi bi-eye" aria-hidden="true"></i>
                    {{ t('adminKb.viewDetail') }}
                  </button>
                  <button
                    class="btn btn-sm btn-link text-danger"
                    @click="confirmDelete(doc.id, doc.name)"
                    :aria-label="t('adminKb.delete')"
                  >
                    <i class="bi bi-trash" aria-hidden="true"></i>
                    {{ t('adminKb.delete') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 페이지네이션 -->
      <div
        v-if="store.documents.length > 0 && totalPages > 1"
        class="card-footer bg-transparent d-flex justify-content-between align-items-center"
      >
        <small class="text-muted">
          {{ t('adminKb.pageInfo', { page: store.pagination.page, total: totalPages }) }}
        </small>
        <nav :aria-label="t('adminKb.pagination')">
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: store.pagination.page <= 1 }">
              <button class="page-link" @click="goPage(store.pagination.page - 1)" :disabled="store.pagination.page <= 1">
                <i class="bi bi-chevron-left" aria-hidden="true"></i>
              </button>
            </li>
            <li class="page-item active">
              <span class="page-link">{{ store.pagination.page }}</span>
            </li>
            <li class="page-item" :class="{ disabled: store.pagination.page >= totalPages }">
              <button class="page-link" @click="goPage(store.pagination.page + 1)" :disabled="store.pagination.page >= totalPages">
                <i class="bi bi-chevron-right" aria-hidden="true"></i>
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDocUtilStore } from '@/stores/docUtilStore'

const { t } = useI18n()
const router = useRouter()
const store = useDocUtilStore()

const searchQuery = ref<string>('')
const folderInput = ref<string>('')

const totalPages = computed(() => {
  if (store.pagination.size <= 0) return 1
  return Math.max(1, Math.ceil(store.pagination.total / store.pagination.size))
})

function refresh(): void {
  store.fetchDocuments(folderInput.value || undefined, store.pagination.page, store.pagination.size)
}

function goPage(page: number): void {
  if (page < 1 || page > totalPages.value) return
  store.fetchDocuments(folderInput.value || undefined, page, store.pagination.size)
}

function onSearch(): void {
  if (!searchQuery.value.trim()) {
    store.clearSearch()
    return
  }
  store.searchKnowledgeBase(searchQuery.value, folderInput.value || undefined)
}

function onClearSearch(): void {
  searchQuery.value = ''
  store.clearSearch()
}

function goUpload(): void {
  router.push({
    name: 'AdminKnowledgeBaseUpload',
    query: folderInput.value ? { folderId: folderInput.value } : undefined
  })
}

function goDetail(id: string): void {
  router.push({ name: 'AdminKnowledgeBaseDetail', params: { id } })
}

async function confirmDelete(id: string, name: string): Promise<void> {
  const message = t('adminKb.deleteConfirm', { name })
  // window.confirm 은 키보드 접근성 OK — Bootstrap 모달은 다이얼로그가 이미 다른 곳에서 사용 중일 때 충돌 위험.
  if (!window.confirm(message)) return
  await store.removeDocument(id)
}

function statusBadgeClass(status: string): string {
  const lower = (status || '').toLowerCase()
  if (lower.includes('index') || lower.includes('ready') || lower === 'completed' || lower === 'done') {
    return 'bg-success-subtle text-success-emphasis'
  }
  if (lower.includes('pending') || lower.includes('queue') || lower.includes('progress')) {
    return 'bg-warning-subtle text-warning-emphasis'
  }
  if (lower.includes('fail') || lower.includes('error')) {
    return 'bg-danger-subtle text-danger-emphasis'
  }
  return 'bg-secondary-subtle text-secondary-emphasis'
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

function truncate(text: string, max: number): string {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '…' : text
}

onMounted(() => {
  store.fetchDocuments(undefined, 1, store.pagination.size)
})
</script>

<style scoped>
.preview-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
}
</style>
