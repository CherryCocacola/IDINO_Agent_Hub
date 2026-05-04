<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">Custom Tools</h1>
        <p class="page-desc">등록된 도구를 검색하고 관리합니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="$router.push('/tools/builder')">
          <i class="bi bi-plus-circle"></i> 새 Tool 생성
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
              placeholder="Tool 검색... (이름, 설명)"
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
          <div class="ag-filter-selects">
            <select class="ag-select" v-model="selectedType">
              <option value="">모든 타입</option>
              <option value="CSharp">C#</option>
              <option value="Python">Python</option>
              <option value="JavaScript">JavaScript</option>
              <option value="Api">API</option>
            </select>
          </div>
          <div class="ag-filter-right">
            <span class="ag-count-label">전체 <strong>{{ filteredTools.length }}</strong>개</span>
          </div>
        </div>

        <div class="row">
          <div 
            v-for="tool in filteredTools" 
            :key="tool.toolId"
            class="col-md-4 mb-3"
          >
            <div class="card aiuiux-card h-100">
              <div class="card-body">
                <h5 class="card-title">
                  <i :class="tool.iconClass || 'bi bi-tools'"></i>
                  {{ tool.toolName }}
                </h5>
                <p class="card-text text-muted">{{ tool.description }}</p>
                <span class="badge bg-secondary">{{ tool.toolType }}</span>
              </div>
              <div class="card-footer">
                <button class="btn btn-sm btn-primary" @click="editTool(tool.toolId)">
                  편집
                </button>
                <button class="btn btn-sm btn-success" @click="testTool(tool.toolId)">
                  테스트
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
import axios from 'axios'

const router = useRouter()
const tools = ref<any[]>([])
const searchQuery = ref('')
const selectedType = ref('')

const filteredTools = computed(() => {
  let filtered = tools.value

  if (searchQuery.value) {
    filtered = filtered.filter(t => 
      t.toolName.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (t.description && t.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
    )
  }

  if (selectedType.value) {
    filtered = filtered.filter(t => t.toolType === selectedType.value)
  }

  return filtered
})

const loadTools = async () => {
  try {
    const response = await axios.get('/api/tools')
    tools.value = response.data
  } catch (error) {
    console.error('Error loading tools:', error)
  }
}

const editTool = (toolId: number) => {
  router.push(`/tools/builder?id=${toolId}`)
}

const testTool = (toolId: number) => {
  // Tool 테스트 로직
  console.log('Test tool:', toolId)
}

onMounted(() => {
  loadTools()
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
