<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">Tool Builder</h1>
        <p class="page-desc">새 도구를 정의하고 코드를 작성합니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-outline-secondary btn-sm me-2" @click="validateCode">
          <i class="bi bi-check-circle"></i> 검증
        </button>
        <button class="btn btn-success btn-sm me-2" @click="testCode">
          <i class="bi bi-play-fill"></i> 테스트
        </button>
        <button class="btn btn-primary btn-sm" @click="saveTool">
          <i class="bi bi-save"></i> 저장
        </button>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6">
        <div class="card aiuiux-card mb-3">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title">Tool 정보</h5>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Tool 이름 *</label>
              <input type="text" class="form-control" v-model="toolForm.toolName">
            </div>
            <div class="mb-3">
              <label class="form-label">설명</label>
              <textarea class="form-control" v-model="toolForm.description" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">타입 *</label>
              <select class="form-select" v-model="toolForm.toolType">
                <option value="CSharp">C#</option>
                <option value="Python">Python</option>
                <option value="JavaScript">JavaScript</option>
                <option value="Api">API</option>
              </select>
            </div>
          </div>
        </div>

        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title">코드</h5>
          </div>
          <div class="card-body">
            <textarea 
              class="form-control font-monospace" 
              v-model="toolForm.code"
              rows="20"
              style="font-size: 14px;"
            ></textarea>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="card aiuiux-card mb-3">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title">테스트</h5>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">입력 데이터 (JSON)</label>
              <textarea 
                class="form-control font-monospace" 
                v-model="testInput"
                rows="5"
              ></textarea>
            </div>
            <div v-if="testResult" class="alert" :class="testResult.success ? 'alert-success' : 'alert-danger'">
              <pre>{{ testResult.output }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const toolForm = ref({
  toolName: '',
  description: '',
  toolType: 'CSharp',
  code: ''
})

const testInput = ref('{}')
const testResult = ref<any>(null)

const validateCode = async () => {
  try {
    const response = await axios.post('/api/tool-builder/validate', {
      language: toolForm.value.toolType,
      code: toolForm.value.code
    })
    alert(response.data.valid ? '코드가 유효합니다.' : `오류: ${response.data.errors.join(', ')}`)
  } catch (error: any) {
    alert('검증 실패: ' + error.response?.data?.message || error.message)
  }
}

const testCode = async () => {
  try {
    const response = await axios.post('/api/tool-builder/test', {
      language: toolForm.value.toolType,
      code: toolForm.value.code,
      inputData: testInput.value
    })
    testResult.value = response.data
  } catch (error: any) {
    testResult.value = {
      success: false,
      output: error.response?.data?.message || error.message
    }
  }
}

const saveTool = async () => {
  try {
    const request = {
      toolName: toolForm.value.toolName,
      description: toolForm.value.description,
      toolType: toolForm.value.toolType,
      code: toolForm.value.code
    }
    
    if (route.query.id) {
      await axios.put(`/api/tools/${route.query.id}`, request)
    } else {
      await axios.post('/api/tools', request)
    }
    
    alert('저장되었습니다.')
    router.push('/tools')
  } catch (error: any) {
    alert('저장 실패: ' + error.response?.data?.message || error.message)
  }
}

onMounted(async () => {
  if (route.query.id) {
    try {
      const response = await axios.get(`/api/tools/${route.query.id}`)
      const tool = response.data
      toolForm.value.toolName = tool.toolName
      toolForm.value.description = tool.description || ''
      toolForm.value.toolType = tool.toolType
      if (tool.activeVersion?.code) {
        toolForm.value.code = tool.activeVersion.code
      }
    } catch (error) {
      console.error('Error loading tool:', error)
    }
  }
})
</script>
