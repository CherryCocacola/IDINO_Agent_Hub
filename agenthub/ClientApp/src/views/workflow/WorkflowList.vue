<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">Workflows</h1>
        <p class="page-desc">워크플로우 목록을 검색하고 관리합니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="$router.push('/workflows/builder')">
          <i class="bi bi-plus-circle"></i> 새 Workflow 생성
        </button>
      </div>
    </div>

    <div class="card aiuiux-card">
      <div class="card-body">
        <div class="ag-filter-bar">
          <div class="ag-search-wrap">
            <i class="bi bi-search ag-search-icon"></i>
            <input 
              type="text" 
              class="ag-search-input" 
              v-model="searchQuery"
              placeholder="Workflow 검색... (이름, 설명)"
            >
            <button 
              type="button" 
              class="ag-search-clear" 
              v-show="searchQuery" 
              @click="searchQuery = ''"
            >
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="ag-filter-right">
            <span class="ag-count-label">전체 <strong>{{ filteredWorkflows.length }}</strong>개</span>
          </div>
        </div>

        <div class="row">
          <div 
            v-for="workflow in filteredWorkflows" 
            :key="workflow.workflowId"
            class="col-md-4 mb-3"
          >
            <div class="card aiuiux-card h-100">
              <div class="card-body">
                <h5 class="card-title">
                  <i :class="workflow.iconClass || 'bi bi-diagram-3'"></i>
                  {{ workflow.workflowName }}
                </h5>
                <p class="card-text text-muted">{{ workflow.description }}</p>
                <div v-if="workflow.nodes" class="mb-2">
                  <small class="text-muted">{{ workflow.nodes.length }} nodes</small>
                </div>
              </div>
              <div class="card-footer">
                <button class="btn btn-sm btn-primary" @click="editWorkflow(workflow.workflowId)">
                  편집
                </button>
                <button class="btn btn-sm btn-success" @click="executeWorkflow(workflow.workflowId)">
                  실행
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
// ↓ anti-patterns.md §11 — JWT 자동 부착 + 401 토큰 갱신을 위해 공통 api 인스턴스 사용
import api from '@/services/api'

const router = useRouter()
const workflows = ref<any[]>([])
const searchQuery = ref('')

const filteredWorkflows = computed(() => {
  if (!searchQuery.value) return workflows.value
  
  return workflows.value.filter(w => 
    w.workflowName.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    (w.description && w.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
  )
})

const loadWorkflows = async () => {
  try {
    // baseURL=/api 가 인터셉터에 의해 자동 적용되므로 경로는 `/workflows` 만 전달
    const response = await api.get('/workflows')
    workflows.value = response.data
  } catch (error) {
    console.error('Error loading workflows:', error)
  }
}

const editWorkflow = (workflowId: number) => {
  router.push(`/workflows/builder?id=${workflowId}`)
}

const executeWorkflow = (workflowId: number) => {
  router.push(`/workflows/executions/${workflowId}`)
}

onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.card {
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-5px);
}
</style>
