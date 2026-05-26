<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilQuickGuide.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilQuickGuide.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="refresh"
          :disabled="loading"
          :aria-label="t('adminDocutilQuickGuide.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilQuickGuide.refresh') }}
        </button>
      </div>
    </div>

    <!-- 에러 알림 -->
    <div
      v-if="errorMessage"
      class="alert alert-warning d-flex justify-content-between align-items-center"
      role="alert"
    >
      <span>{{ errorMessage }}</span>
      <button
        type="button"
        class="btn-close"
        :aria-label="t('common.close')"
        @click="errorMessage = ''"
      ></button>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">{{ t('common.loading') }}</span>
      </div>
    </div>

    <!-- 가이드 카드 그리드 -->
    <div v-else class="row g-3">
      <div
        v-for="guide in guides"
        :key="guide.key"
        class="col-md-6"
      >
        <article class="card aiuiux-card h-100">
          <div class="card-body">
            <h6 class="d-flex align-items-center mb-2">
              <i
                :class="['me-2', 'text-primary', 'fs-5', guide.icon]"
                aria-hidden="true"
              ></i>
              <span class="fw-semibold">{{ guide.title }}</span>
            </h6>
            <p class="text-muted small mb-3">{{ guide.description }}</p>
            <ol class="ps-3 mb-0 small">
              <li
                v-for="(step, idx) in guide.steps"
                :key="idx"
                class="mb-1"
              >
                {{ step }}
              </li>
            </ol>
          </div>
        </article>
      </div>
    </div>

    <!-- 추가 도움말 -->
    <article class="card aiuiux-card mt-3">
      <div class="card-body">
        <h6 class="d-flex align-items-center mb-2">
          <i class="bi bi-book-half me-2 text-primary fs-5" aria-hidden="true"></i>
          <span class="fw-semibold">{{ t('adminDocutilQuickGuide.moreHelpTitle') }}</span>
        </h6>
        <p class="text-muted small mb-0">
          {{ t('adminDocutilQuickGuide.moreHelpDesc') }}
          <router-link to="/help" class="link-primary">
            {{ t('adminDocutilQuickGuide.helpLink') }}
          </router-link>
        </p>
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilQuickGuide — DocUtil 사용자 가이드 운영자 화면 (트랙 A1 Phase B, 2026-05-25).
 *
 * 진입 경로: /admin/docutil-quick-guide (Admin / SuperAdmin 전용)
 *
 * 책임:
 *   1. 4 개 가이드 카드(문서 업로드 / 검색 범위 설정 / AI 채팅 / API 키 관리) 표시
 *   2. BFF `GET /api/admin/docutil/quick-guide` 호출 시도 → 실패 시 i18n 정적 가이드로 fallback
 *
 * 정적 fallback 정책:
 *   본 페이지는 운영자가 시스템 사용법을 빠르게 익히는 용도. 백엔드는 정적 콘텐츠를 그대로
 *   반환하므로 endpoint 가 미구현이거나 5xx 인 경우에도 i18n 콘텐츠로 즉시 표시 가능해야 한다.
 */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  getDocUtilQuickGuide,
  type DocUtilQuickGuideEntry
} from '@/services/docutilService'

const { t, tm } = useI18n()

interface GuideCard {
  key: string
  icon: string
  title: string
  description: string
  steps: string[]
}

const loading = ref<boolean>(false)
const errorMessage = ref<string>('')
const remoteGuides = ref<DocUtilQuickGuideEntry[] | null>(null)

// i18n tm() 으로 정적 4개 가이드 항목을 한 번에 읽어와 fallback 으로 사용한다.
const staticGuides = computed<GuideCard[]>(() => {
  const keys = ['documentUpload', 'searchScope', 'aiChat', 'apiKeys'] as const
  const icons: Record<(typeof keys)[number], string> = {
    documentUpload: 'bi bi-file-earmark-arrow-up',
    searchScope: 'bi bi-search',
    aiChat: 'bi bi-chat-dots',
    apiKeys: 'bi bi-key'
  }
  return keys.map<GuideCard>((k) => {
    const raw = tm(`adminDocutilQuickGuide.guides.${k}`) as
      | { title?: string; description?: string; steps?: string[] }
      | undefined
    return {
      key: k,
      icon: icons[k],
      title: raw?.title ?? k,
      description: raw?.description ?? '',
      steps: Array.isArray(raw?.steps) ? raw!.steps : []
    }
  })
})

// 원격 응답이 있으면 그것을 우선, 없으면 정적 fallback 사용.
const guides = computed<GuideCard[]>(() => {
  if (remoteGuides.value && remoteGuides.value.length > 0) {
    return remoteGuides.value.map<GuideCard>((g, idx) => ({
      key: g.key ?? `remote-${idx}`,
      icon: g.icon ?? 'bi bi-info-circle',
      title: g.title ?? '',
      description: g.description ?? '',
      steps: Array.isArray(g.steps) ? g.steps : []
    }))
  }
  return staticGuides.value
})

async function fetchGuide(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await getDocUtilQuickGuide()
    remoteGuides.value =
      data && Array.isArray(data.guides) && data.guides.length > 0 ? data.guides : null
  } catch (err: unknown) {
    // 백엔드 endpoint 미구현 / 5xx 도 정적 fallback 으로 조용히 전환 — 운영자에게 가이드는
    // 항상 표시되어야 하므로 오류 alert 대신 콘솔 경고만.
    remoteGuides.value = null
    // eslint-disable-next-line no-console
    console.warn('[AdminDocUtilQuickGuide] BFF 호출 실패 — 정적 가이드로 fallback:', err)
  } finally {
    loading.value = false
  }
}

function refresh(): void {
  fetchGuide()
}

onMounted(() => {
  fetchGuide()
})
</script>

<style scoped>
.aiuiux-card {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.aiuiux-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

ol.ps-3 li::marker {
  color: var(--bs-primary);
  font-weight: 600;
}
</style>
