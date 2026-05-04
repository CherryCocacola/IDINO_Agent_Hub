<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">Workflow 실행 모니터링</h1>
        <p class="page-desc">워크플로우 실행 입력 및 실행 기록을 확인합니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="executeWorkflow" v-if="workflowId">
          <i class="bi bi-play-fill"></i> 실행
        </button>
      </div>
    </div>

    <div class="card aiuiux-card mb-3">
      <div class="card-body">
        <div class="mb-3">
          <label class="form-label">입력 데이터 (JSON)</label>
          <textarea 
            class="form-control font-monospace" 
            v-model="inputData"
            rows="5"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom">
        <h5 class="card-title">실행 기록</h5>
      </div>
      <div class="card-body">
        <div v-if="executions.length === 0" class="text-center text-muted py-5">
          실행 기록이 없습니다.
        </div>
        <div v-else>
          <div 
            v-for="execution in executions" 
            :key="execution.executionId"
            class="card mb-2"
          >
            <div class="card-body">
              <div class="d-flex justify-content-between">
                <div>
                  <h6>Execution #{{ execution.executionId }}</h6>
                  <small class="text-muted">
                    {{ new Date(execution.startedAt).toLocaleString() }}
                  </small>
                </div>
                <span class="badge" :class="getStatusBadgeClass(execution.status)">
                  {{ execution.status }}
                </span>
              </div>
              <div v-if="execution.nodeExecutions" class="mt-3">
                <h6>노드 실행 상태:</h6>
                <div class="row">
                  <div 
                    v-for="nodeExec in execution.nodeExecutions"
                    :key="nodeExec.nodeExecutionId"
                    class="col-md-3 mb-2"
                  >
                    <div class="card aiuiux-card">
                      <div class="card-body p-2">
                        <small>{{ nodeExec.nodeCode }}</small>
                        <span class="badge badge-sm ms-2" :class="getStatusBadgeClass(nodeExec.status)">
                          {{ nodeExec.status }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const workflowId = ref<number | null>(null)
const inputData = ref('{}')
const executions = ref<any[]>([])

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'Completed':
      return 'bg-success'
    case 'Failed':
      return 'bg-danger'
    case 'Running':
      return 'bg-primary'
    case 'Cancelled':
      return 'bg-secondary'
    default:
      return 'bg-secondary'
  }
}

const executeWorkflow = async () => {
  if (!workflowId.value) return

  try {
    const response = await axios.post(`/api/workflows/${workflowId.value}/execute`, {
      inputData: inputData.value,
      waitForCompletion: true
    })
    executions.value.unshift(response.data)
  } catch (error: any) {
    alert('실행 실패: ' + error.response?.data?.message || error.message)
  }
}

const loadExecutions = async () => {
  if (!workflowId.value) return

  try {
    const response = await axios.get('/api/workflows/executions', {
      params: { workflowId: workflowId.value }
    })
    executions.value = response.data
  } catch (error) {
    console.error('Error loading executions:', error)
  }
}

onMounted(() => {
  if (route.params.id) {
    workflowId.value = parseInt(route.params.id as string)
    loadExecutions()
  }
})
</script>
