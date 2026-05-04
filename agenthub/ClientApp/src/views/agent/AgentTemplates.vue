<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">프롬프트 템플릿</h1>
        <p class="page-desc">자주 사용하는 프롬프트를 템플릿으로 저장하고 재사용하세요</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="showCreateModal = true">
          <i class="bi bi-plus-circle"></i> 새 템플릿
        </button>
      </div>
    </div>

    <!-- 탭 -->
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <a 
          class="nav-link" 
          :class="{ active: activeTab === 'my' }"
          @click.prevent="activeTab = 'my'"
        >
          내 템플릿
        </a>
      </li>
      <li class="nav-item">
        <a 
          class="nav-link" 
          :class="{ active: activeTab === 'team' }"
          @click.prevent="activeTab = 'team'"
        >
          팀 템플릿
        </a>
      </li>
      <li class="nav-item">
        <a 
          class="nav-link" 
          :class="{ active: activeTab === 'official' }"
          @click.prevent="activeTab = 'official'"
        >
          공식 템플릿
        </a>
      </li>
    </ul>

    <!-- 템플릿 그리드 -->
    <div class="row">
      <div 
        v-for="template in filteredTemplates" 
        :key="template.id"
        class="col-lg-4 col-md-6 mb-4"
      >
        <div class="card aiuiux-card h-100 template-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h5 class="card-title">{{ template.name }}</h5>
                <span class="badge bg-secondary">{{ template.category }}</span>
              </div>
              <div class="dropdown">
                <button class="btn btn-sm btn-link" type="button" data-bs-toggle="dropdown">
                  <i class="bi bi-three-dots"></i>
                </button>
                <ul class="dropdown-menu dropdown-menu-end">
                  <li><a class="dropdown-item" href="#" @click.prevent="editTemplate(template)">수정</a></li>
                  <li><a class="dropdown-item" href="#" @click.prevent="duplicateTemplate(template)">복제</a></li>
                  <li><hr class="dropdown-divider"></li>
                  <li><a class="dropdown-item text-danger" href="#" @click.prevent="deleteTemplate(template)">삭제</a></li>
                </ul>
              </div>
            </div>
            <p class="card-text text-muted small" style="min-height: 60px;">
              {{ template.description || '프롬프트 템플릿' }}
            </p>
            <div class="mb-3">
              <small class="text-muted">
                <i class="bi bi-clock"></i> {{ formatDate(template.createdAt) }}
              </small>
            </div>
          </div>
          <div class="card-footer bg-white d-flex gap-2">
            <button class="btn btn-primary btn-sm flex-grow-1" @click="useAsAgent(template)">
              <i class="bi bi-robot"></i> Agent로 만들기
            </button>
            <button class="btn btn-outline-secondary btn-sm" @click="useTemplate(template)" title="Playground에서 사용">
              <i class="bi bi-play-circle"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 템플릿 생성 모달 -->
    <div class="modal fade" :class="{ show: showCreateModal }" :style="{ display: showCreateModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">새 템플릿 만들기</h5>
            <button type="button" class="btn-close" @click="showCreateModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleSaveTemplate">
              <div class="mb-3">
                <label class="form-label">템플릿 이름 *</label>
                <input type="text" class="form-control" v-model="templateForm.name" required>
              </div>
              <div class="mb-3">
                <label class="form-label">카테고리</label>
                <select class="form-select" v-model="templateForm.category">
                  <option value="code-review">코드 리뷰</option>
                  <option value="documentation">문서 작성</option>
                  <option value="translation">번역</option>
                  <option value="analysis">데이터 분석</option>
                  <option value="marketing">마케팅</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">설명</label>
                <textarea class="form-control" v-model="templateForm.description" rows="2"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">프롬프트 *</label>
                <textarea class="form-control" v-model="templateForm.content" rows="8" required></textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleSaveTemplate">
              <i class="bi bi-check-lg"></i> 저장
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showCreateModal }" v-if="showCreateModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'

interface Template {
  id: string
  name: string
  category: string
  description?: string
  content: string
  createdAt: string
  isTeam?: boolean
  isOfficial?: boolean
}

const router = useRouter()
const activeTab = ref<'my' | 'team' | 'official'>('my')
const templates = ref<Template[]>([])
const loading = ref(false)
const showCreateModal = ref(false)

const templateForm = ref({
  name: '',
  category: 'code-review',
  description: '',
  content: ''
})

const filteredTemplates = computed(() => {
  return templates.value.filter(t => {
    if (activeTab.value === 'my') return !t.isTeam && !t.isOfficial
    if (activeTab.value === 'team') return t.isTeam
    return t.isOfficial
  })
})

const loadTemplates = async () => {
  try {
    loading.value = true
    // 실제 API 엔드포인트가 없으면 localStorage 사용
    const saved = localStorage.getItem('prompt_templates')
    if (saved) {
      templates.value = JSON.parse(saved)
    } else {
      // 기본 템플릿
      templates.value = [
        {
          id: '1',
          name: '코드 리뷰 템플릿',
          category: 'code-review',
          description: '코드 품질 검토용',
          content: '다음 코드를 리뷰해주세요. 성능, 보안, 가독성 측면에서 평가해주세요.',
          createdAt: new Date().toISOString(),
          isOfficial: true
        }
      ]
    }
    // loading 변수 사용
    if (templates.value.length > 0) {
      console.log('Templates loaded:', templates.value.length)
    }
  } catch (error) {
    console.error('Error loading templates:', error)
  } finally {
    loading.value = false
  }
}

const handleSaveTemplate = () => {
  const newTemplate: Template = {
    id: Date.now().toString(),
    name: templateForm.value.name,
    category: templateForm.value.category,
    description: templateForm.value.description,
    content: templateForm.value.content,
    createdAt: new Date().toISOString()
  }
  templates.value.push(newTemplate)
  localStorage.setItem('prompt_templates', JSON.stringify(templates.value))
  showCreateModal.value = false
  templateForm.value = { name: '', category: 'code-review', description: '', content: '' }
}

const useTemplate = (template: Template) => {
  router.push({
    path: '/playground',
    query: { template: template.content }
  })
}

const useAsAgent = (template: Template) => {
  router.push({
    path: '/agents/builder',
    query: {
      templateName: template.name,
      templateDesc: template.description || '',
      templatePrompt: template.content
    }
  })
}

const editTemplate = (template: Template) => {
  templateForm.value = {
    name: template.name,
    category: template.category,
    description: template.description || '',
    content: template.content
  }
  // TODO: 템플릿 ID 추적하여 업데이트
  showCreateModal.value = true
}

const duplicateTemplate = (template: Template) => {
  templateForm.value = {
    name: template.name + ' (복사)',
    category: template.category,
    description: template.description || '',
    content: template.content
  }
  showCreateModal.value = true
}

const deleteTemplate = (template: Template) => {
  if (confirm('템플릿을 삭제하시겠습니까?')) {
    templates.value = templates.value.filter(t => t.id !== template.id)
    localStorage.setItem('prompt_templates', JSON.stringify(templates.value))
  }
}

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('ko-KR')
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-card {
  transition: all 0.2s;
}

.template-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>
