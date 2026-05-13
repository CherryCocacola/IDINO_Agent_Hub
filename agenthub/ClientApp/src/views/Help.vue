<template>
  <div class="page-content-wrap">
    <div class="page-header text-center mb-5">
      <div>
        <h1 class="page-heading">{{ t('help.title') }}</h1>
        <p class="page-desc">{{ t('help.subtitle') }}</p>
      </div>
      <div class="row justify-content-center mt-4">
        <div class="col-md-6">
          <div class="input-group input-group-lg">
            <span class="input-group-text"><i class="bi bi-search"></i></span>
            <input
              type="text"
              class="form-control"
              v-model="searchQuery"
              :placeholder="t('help.searchPlaceholder')"
              @keyup.enter="searchHelp"
            >
            <button class="btn btn-primary" @click="searchHelp">
              {{ t('help.searchButton') }}
            </button>
          </div>
          <!-- 결함 트랙 #89 M5: 검색 결과 카운트 표시 (검색어가 있을 때만) -->
          <div v-if="searchQuery.trim()" class="text-muted small mt-2">
            {{ t('help.searchResultsCount', { count: filteredFAQs.length }) }}
          </div>
        </div>
      </div>
    </div>

    <!-- 주요 카테고리 -->
    <div class="row mb-5">
      <div class="col-12">
        <h4 class="mb-3">{{ t('help.mainCategories') }}</h4>
      </div>
      <div class="col-md-3 mb-3" v-for="category in categories" :key="category.id">
        <div class="card aiuiux-card help-card h-100" :style="{ '--category-color': category.color }" @click="showCategory(category.id)">
          <div class="card-body text-center">
            <i :class="category.icon" class="help-category-icon"></i>
            <h5 class="mt-3">{{ category.title }}</h5>
            <p class="text-muted small">{{ category.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <!-- FAQ -->
      <div class="col-lg-8">
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-question-circle"></i> {{ t('help.faqTitle') }}</h5>
          </div>
          <div class="card-body p-0">
            <div class="accordion" id="faqAccordion">
              <div
                v-for="(faq, index) in filteredFAQs"
                :key="index"
                class="accordion-item"
              >
                <h2 class="accordion-header">
                  <button
                    class="accordion-button"
                    :class="{ collapsed: openAccordionIndex !== index }"
                    type="button"
                    :data-bs-target="`#faq-${index}`"
                    :aria-expanded="openAccordionIndex === index"
                    @click="toggleAccordion(index)"
                  >
                    {{ faq.question }}
                  </button>
                </h2>
                <div
                  :id="`faq-${index}`"
                  class="accordion-collapse collapse"
                  :class="{ show: openAccordionIndex === index }"
                >
                  <div class="accordion-body">
                    <div v-html="sanitize(faq.answer)"></div>
                  </div>
                </div>
              </div>
              <div v-if="filteredFAQs.length === 0" class="text-center py-5 text-muted">
                <i class="bi bi-inbox icon-3xl"></i>
                <p class="mt-3">{{ t('help.noResults') }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 우측: 빠른 링크 & 지원 -->
      <div class="col-lg-4">
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="mb-0"><i class="bi bi-link-45deg"></i> {{ t('help.quickLinksTitle') }}</h5>
          </div>
          <div class="list-group list-group-flush">
            <a href="#" class="list-group-item list-group-item-action" @click.prevent="scrollToSection('getting-started')">
              <i class="bi bi-rocket"></i> {{ t('help.quickLinks.gettingStarted') }}
            </a>
            <a href="#" class="list-group-item list-group-item-action" @click.prevent="scrollToSection('api')">
              <i class="bi bi-code-square"></i> {{ t('help.quickLinks.api') }}
            </a>
            <a href="#" class="list-group-item list-group-item-action" @click.prevent="scrollToSection('troubleshooting')">
              <i class="bi bi-tools"></i> {{ t('help.quickLinks.troubleshooting') }}
            </a>
          </div>
        </div>

        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="mb-0"><i class="bi bi-headset"></i> {{ t('help.supportTitle') }}</h5>
          </div>
          <div class="card-body">
            <p class="mb-3">{{ t('help.supportDesc') }}</p>
            <button class="btn btn-primary w-100" @click="contactSupport()">
              <i class="bi bi-envelope"></i> {{ t('help.emailSupport') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import DOMPurify from 'dompurify'
import api from '@/services/api'
import type { FaqDto, TutorialDto } from '@/types'

// 결함 트랙 #89 M2/M5 (2026-05-13): 본문 i18n 적용 + 검색 결함 해소.
const { t } = useI18n()

interface Category {
  id: string
  title: string
  description: string
  icon: string
  color: string
}

interface FAQ {
  question: string
  answer: string
  category?: string
}

const sanitize = (html: string) => DOMPurify.sanitize(html)

const searchQuery = ref('')
const openAccordionIndex = ref<number | null>(0)
const faqs = ref<FAQ[]>([])
const tutorials = ref<TutorialDto[]>([])
const loading = ref(false)
const tutorialsLoading = ref(false)

// 결함 트랙 #89 M2: 카테고리 라벨도 i18n 적용 — locale 토글 시 함께 변경.
// computed 로 정의하여 locale.value 변동에 자동 반응.
const categories = computed<Category[]>(() => [
  {
    id: 'getting-started',
    title: t('help.categories.gettingStarted.title'),
    description: t('help.categories.gettingStarted.description'),
    icon: 'bi bi-rocket text-primary',
    color: '#0d6efd'
  },
  {
    id: 'agents',
    title: t('help.categories.agents.title'),
    description: t('help.categories.agents.description'),
    icon: 'bi bi-robot text-success',
    color: '#198754'
  },
  {
    id: 'api',
    title: t('help.categories.api.title'),
    description: t('help.categories.api.description'),
    icon: 'bi bi-code-square text-warning',
    color: '#ffc107'
  },
  {
    id: 'troubleshooting',
    title: t('help.categories.troubleshooting.title'),
    description: t('help.categories.troubleshooting.description'),
    icon: 'bi bi-tools text-danger',
    color: '#dc3545'
  }
])

const loadFaqs = async () => {
  try {
    loading.value = true
    const response = await api.get<FaqDto[]>('/faqs', {
      params: { isActive: true }
    })

    faqs.value = (response.data || []).map(f => ({
      question: f.question,
      answer: f.answer,
      category: f.category
    }))
  } catch (error) {
    console.error('Error loading FAQs:', error)
    // 에러 발생 시 빈 배열로 설정
    faqs.value = []
  } finally {
    loading.value = false
  }
}

const loadTutorials = async () => {
  try {
    tutorialsLoading.value = true
    const response = await api.get<TutorialDto[]>('/tutorials', {
      params: { isActive: true }
    })

    tutorials.value = response.data || []
  } catch (error) {
    console.error('Error loading tutorials:', error)
    tutorials.value = []
  } finally {
    tutorialsLoading.value = false
  }
}

// 결함 트랙 #89 M5 (2026-05-13): 검색 매칭 범위 확장.
// 종전: question/answer text 만 검색 → 카테고리 한국어 라벨로 검색하면 결과 0건.
// 수정: question + answer + category(id 영문) 3 필드에 대해 부분 일치 검색.
const filteredFAQs = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return faqs.value

  return faqs.value.filter(faq =>
    faq.question.toLowerCase().includes(q) ||
    faq.answer.toLowerCase().includes(q) ||
    (faq.category || '').toLowerCase().includes(q)
  )
})

// 결함 트랙 #89 M5: 검색 버튼/Enter 클릭 시 실제 동작 부여.
// 종전: 빈 함수(주석만) → 사용자가 검색해도 시각적 피드백 없음.
// 수정: 첫 매칭 항목을 자동으로 펼치고, 결과 영역으로 스크롤. 결과 없으면 안내 영역 표시.
const searchHelp = () => {
  // computed 가 이미 필터링하므로 추가 호출 불필요. UX 차원의 후처리만 수행.
  if (filteredFAQs.value.length > 0) {
    openAccordionIndex.value = 0
    // 다음 tick 후 DOM 갱신을 기다려 스크롤
    setTimeout(() => {
      const element = document.getElementById('faqAccordion')
      element?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  } else {
    // 결과 없음: accordion 열림 상태만 해제
    openAccordionIndex.value = null
  }
}

const showCategory = (categoryId: string) => {
  // 결함 트랙 #89 M5: 카테고리 카드 클릭 시 검색창에 한글 라벨 대신 영문 id 를 넣는다.
  // 그래야 FAQ.category (영문 id) 와 매칭되어 결과가 정확히 표시된다.
  searchQuery.value = categoryId
  // 해당 카테고리의 첫 번째 FAQ 열기
  const firstIndex = faqs.value.findIndex(f => f.category === categoryId)
  if (firstIndex >= 0) {
    openAccordionIndex.value = firstIndex
    setTimeout(() => {
      const element = document.getElementById(`faq-${firstIndex}`)
      element?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  } else {
    // 매칭되는 FAQ 가 없으면 검색 결과 영역으로만 스크롤 — 결과 카운트 0 안내가 자연스럽게 노출.
    openAccordionIndex.value = null
    setTimeout(() => {
      const element = document.getElementById('faqAccordion')
      element?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }
}

const toggleAccordion = (index: number) => {
  if (openAccordionIndex.value === index) {
    openAccordionIndex.value = null
  } else {
    openAccordionIndex.value = index
  }
}

const scrollToSection = (sectionId: string) => {
  showCategory(sectionId)
}

const contactSupport = () => {
  window.location.href = 'mailto:jyj7970@idino.co.kr?subject=도움말 문의'
}

onMounted(() => {
  loadFaqs()
  loadTutorials()
})
</script>

<style scoped>
.help-card {
  cursor: pointer;
  transition: all 0.2s;
}

.help-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.video-card {
  cursor: pointer;
  transition: all 0.2s;
}

.video-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.video-thumb {
  width: 100%;
  height: 180px;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  transition: background 0.3s;
}

.video-thumb:hover .video-overlay {
  background: rgba(0, 0, 0, 0.5);
}
</style>
