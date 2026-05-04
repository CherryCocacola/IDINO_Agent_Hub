<template>
  <div>
    <div class="row mb-3">
      <div class="col-md-6">
        <h2><i class="bi bi-controller"></i> AI 플레이그라운드</h2>
        <p class="text-muted">프롬프트를 실험하고 결과를 비교하세요</p>
      </div>
      <div class="col-md-6 text-end">
        <div class="btn-group me-2">
          <button 
            class="btn btn-outline-primary"
            :class="{ active: mode === 'single' }"
            @click="mode = 'single'"
          >
            단일
          </button>
          <button 
            class="btn btn-outline-primary"
            :class="{ active: mode === 'compare' }"
            @click="mode = 'compare'"
          >
            A/B 비교
          </button>
        </div>
        <button class="btn btn-success" @click="saveExperiment">
          <i class="bi bi-save"></i> 저장
        </button>
      </div>
    </div>

    <div class="playground-grid" :class="{ 'comparison-mode': mode === 'compare' }">
      <!-- 입력 패널 -->
      <div class="panel">
        <div class="panel-header">
          <i class="bi bi-pencil-square"></i> 프롬프트 입력
        </div>
        <div class="panel-body">
          <div class="mb-3">
            <label class="form-label">시스템 프롬프트</label>
            <textarea 
              class="form-control" 
              v-model="prompt.systemPrompt" 
              rows="3" 
              placeholder="AI의 역할을 정의하세요..."
            ></textarea>
          </div>

          <div class="mb-3">
            <label class="form-label">사용자 프롬프트</label>
            <textarea 
              class="form-control" 
              v-model="prompt.userPrompt" 
              rows="6" 
              placeholder="질문이나 요청을 입력하세요..."
            ></textarea>
          </div>

          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label">모델</label>
              <select class="form-select form-select-sm" v-model="prompt.model">
                <option>GPT-4 Turbo</option>
                <option>GPT-4</option>
                <option>GPT-3.5 Turbo</option>
                <option>Claude 3 Opus</option>
                <option>Claude 3 Sonnet</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">Temperature <span>{{ (prompt.temperature / 100).toFixed(1) }}</span></label>
              <input 
                type="range" 
                class="form-range" 
                v-model.number="prompt.temperature" 
                min="0" 
                max="100"
              >
            </div>
          </div>

          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label">Max Tokens</label>
              <input type="number" class="form-control form-control-sm" v-model.number="prompt.maxTokens">
            </div>
            <div class="col-md-6">
              <label class="form-label">Top P</label>
              <input 
                type="number" 
                class="form-control form-control-sm" 
                v-model.number="prompt.topP" 
                step="0.1" 
                min="0" 
                max="1"
              >
            </div>
          </div>

          <button class="btn btn-primary w-100" @click="runExperiment" :disabled="loading">
            <i class="bi bi-play-fill"></i> 실행
          </button>
        </div>
      </div>

      <!-- 출력 패널 -->
      <div class="panel">
        <div class="panel-header">
          <i class="bi bi-chat-right-text"></i> AI 응답
          <span class="badge bg-secondary float-end">{{ prompt.model }}</span>
        </div>
        <div class="panel-body">
          <div class="output-text" v-if="!output">{{ loading ? '처리 중...' : 'AI의 응답이 여기에 표시됩니다...\n\n실행 버튼을 클릭하면 결과를 볼 수 있습니다.' }}</div>
          <div class="output-text" v-else>{{ output }}</div>

          <div class="mt-3 p-3 bg-light rounded" v-if="stats.tokensUsed > 0">
            <strong>통계</strong>
            <ul class="list-unstyled mt-2 mb-0">
              <li>토큰 사용: <strong>{{ stats.tokensUsed }}</strong></li>
              <li>응답 시간: <strong>{{ stats.responseTime }}s</strong></li>
              <li>비용: <strong>${{ stats.cost.toFixed(4) }}</strong></li>
            </ul>
          </div>

          <div class="mt-3">
            <button class="btn btn-sm btn-outline-secondary" @click="copyOutput">
              <i class="bi bi-clipboard"></i> 복사
            </button>
            <button class="btn btn-sm btn-outline-primary" @click="runExperiment" :disabled="loading">
              <i class="bi bi-arrow-clockwise"></i> 다시 생성
            </button>
            <button class="btn btn-sm btn-outline-success" @click="saveExperiment">
              <i class="bi bi-save"></i> 저장
            </button>
          </div>
        </div>
      </div>

      <!-- 비교 모드 추가 패널 -->
      <div v-if="mode === 'compare'" class="panel">
        <div class="panel-header">
          <i class="bi bi-chat-right-text"></i> AI 응답 (비교)
          <span class="badge bg-secondary float-end">{{ prompt.model }}</span>
        </div>
        <div class="panel-body">
          <div class="output-text" v-if="!output2">{{ loading2 ? '처리 중...' : '비교 결과가 여기에 표시됩니다...' }}</div>
          <div class="output-text" v-else>{{ output2 }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'

const mode = ref<'single' | 'compare'>('single')
const loading = ref(false)
const loading2 = ref(false)

const prompt = ref({
  systemPrompt: '당신은 도움이 되는 AI 어시스턴트입니다.',
  userPrompt: '',
  model: 'GPT-3.5 Turbo',
  temperature: 70,
  maxTokens: 2048,
  topP: 1
})

const output = ref('')
const output2 = ref('')

const stats = ref({
  tokensUsed: 0,
  responseTime: 0,
  cost: 0
})

const runExperiment = async () => {
  if (!prompt.value.userPrompt.trim()) {
    alert('사용자 프롬프트를 입력하세요.')
    return
  }

  try {
    loading.value = true
    output.value = ''
    
    const startTime = Date.now()
    // 실제 API 호출은 ChatController를 통해 처리
    const response = await api.post('/chat/send', {
      serviceId: 1, // 기본 서비스 ID
      model: prompt.value.model,
      temperature: prompt.value.temperature / 100,
      maxTokens: prompt.value.maxTokens,
      messages: [
        { role: 'system', content: prompt.value.systemPrompt },
        { role: 'user', content: prompt.value.userPrompt }
      ],
      stream: false
    })

    const responseTime = (Date.now() - startTime) / 1000
    output.value = response.data.content || '응답이 없습니다.'
    stats.value = {
      tokensUsed: response.data.tokensUsed || 0,
      responseTime: parseFloat(responseTime.toFixed(2)),
      cost: response.data.cost || 0
    }

    if (mode.value === 'compare') {
      loading2.value = true
      // 두 번째 응답도 같은 방식으로 처리
      setTimeout(() => {
        output2.value = '비교 응답 (실제로는 다른 모델/파라미터로 실행)'
        loading2.value = false
      }, 1000)
    }
  } catch (error: any) {
    console.error('Error running experiment:', error)
    alert(error.response?.data?.message || '실험 실행 중 오류가 발생했습니다.')
    output.value = '오류가 발생했습니다: ' + (error.response?.data?.message || error.message)
  } finally {
    loading.value = false
  }
}

const copyOutput = () => {
  navigator.clipboard.writeText(output.value)
  alert('클립보드에 복사되었습니다.')
}

const saveExperiment = () => {
  const experiment = {
    prompt: prompt.value,
    output: output.value,
    stats: stats.value,
    createdAt: new Date().toISOString()
  }
  localStorage.setItem(`experiment_${Date.now()}`, JSON.stringify(experiment))
  alert('실험이 저장되었습니다.')
}
</script>

<style scoped>
.playground-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: calc(100vh - 200px);
}

.playground-grid.comparison-mode {
  grid-template-columns: 1fr 1fr 1fr;
}

.panel {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  background: #f8f9fa;
  padding: 15px;
  border-bottom: 1px solid #dee2e6;
  font-weight: 600;
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.output-text {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  min-height: 200px;
}
</style>
