<template>
  <div class="page-content-wrap">
    <div class="page-header text-center mb-5">
      <div>
        <h1 class="page-heading">도움말 센터</h1>
        <p class="page-desc">무엇을 도와드릴까요?</p>
      </div>
      <div class="row justify-content-center mt-4">
        <div class="col-md-6">
          <div class="input-group input-group-lg">
            <span class="input-group-text"><i class="bi bi-search"></i></span>
            <input 
              type="text" 
              class="form-control" 
              v-model="searchQuery"
              placeholder="질문을 검색하세요..."
              @keyup.enter="searchHelp"
            >
            <button class="btn btn-primary" @click="searchHelp">
              검색
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 주요 카테고리 -->
    <div class="row mb-5">
      <div class="col-12">
        <h4 class="mb-3">주요 카테고리</h4>
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
            <h5 class="card-title mb-0"><i class="bi bi-question-circle"></i> 자주 묻는 질문 (FAQ)</h5>
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
                <p class="mt-3">검색 결과가 없습니다</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 우측: 빠른 링크 & 지원 -->
      <div class="col-lg-4">
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="mb-0"><i class="bi bi-link-45deg"></i> 빠른 링크</h5>
          </div>
          <div class="list-group list-group-flush">
            <a href="#" class="list-group-item list-group-item-action" @click.prevent="scrollToSection('getting-started')">
              <i class="bi bi-rocket"></i> 시작하기 가이드
            </a>
            <a href="#" class="list-group-item list-group-item-action" @click.prevent="scrollToSection('api')">
              <i class="bi bi-code-square"></i> API 문서
            </a>
            <a href="#" class="list-group-item list-group-item-action" @click.prevent="scrollToSection('troubleshooting')">
              <i class="bi bi-tools"></i> 문제 해결
            </a>
          </div>
        </div>

        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="mb-0"><i class="bi bi-headset"></i> 지원 문의</h5>
          </div>
          <div class="card-body">
            <p class="mb-3">더 도움이 필요하신가요?</p>
            <button class="btn btn-primary w-100" @click="contactSupport()">
              <i class="bi bi-envelope"></i> 이메일 지원
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import DOMPurify from 'dompurify'
import api from '@/services/api'
import type { FaqDto, TutorialDto } from '@/types'

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

const categories = ref<Category[]>([
  {
    id: 'getting-started',
    title: '시작하기',
    description: '기본 사용법 및 설정',
    icon: 'bi bi-rocket text-primary',
    color: '#0d6efd'
  },
  {
    id: 'agents',
    title: 'Agent 사용',
    description: 'Agent 생성 및 관리',
    icon: 'bi bi-robot text-success',
    color: '#198754'
  },
  {
    id: 'api',
    title: 'API 연동',
    description: 'API 키 및 개발',
    icon: 'bi bi-code-square text-warning',
    color: '#ffc107'
  },
  {
    id: 'troubleshooting',
    title: '문제 해결',
    description: '오류 및 트러블슈팅',
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

const filteredFAQs = computed(() => {
  if (!searchQuery.value) return faqs.value
  
  const query = searchQuery.value.toLowerCase()
  return faqs.value.filter(faq => 
    faq.question.toLowerCase().includes(query) ||
    faq.answer.toLowerCase().includes(query)
  )
})

const searchHelp = () => {
  // 검색 기능은 computed가 처리
}

const showCategory = (categoryId: string) => {
  const category = categories.value.find(c => c.id === categoryId)
  if (category) {
    searchQuery.value = category.title
    // 해당 카테고리의 첫 번째 FAQ 열기
    const firstIndex = faqs.value.findIndex(f => f.category === categoryId)
    if (firstIndex >= 0) {
      openAccordionIndex.value = firstIndex
      setTimeout(() => {
        const element = document.getElementById(`faq-${firstIndex}`)
        element?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    }
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
