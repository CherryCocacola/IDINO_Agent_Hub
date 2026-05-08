<template>
  <div class="page-content-wrap wfb-wrap">
    <!-- 헤더 -->
    <div class="page-header">
      <div>
        <h1 class="page-heading">Workflow Builder</h1>
        <p class="page-desc">노드를 연결해 AI 워크플로우를 구성하세요.</p>
      </div>
      <div class="page-actions d-flex gap-2 align-items-center">
        <button class="btn btn-outline-secondary btn-sm" @click="toggleView">
          <i :class="viewMode === 'visual' ? 'bi bi-code-slash' : 'bi bi-diagram-3'"></i>
          {{ viewMode === 'visual' ? '코드 보기' : '시각적 보기' }}
        </button>
        <button class="btn btn-outline-success btn-sm" @click="testWorkflow" :disabled="testing">
          <i class="bi bi-play-fill"></i> {{ testing ? '실행 중...' : '테스트' }}
        </button>
        <button class="btn btn-primary btn-sm" @click="saveWorkflow" :disabled="saving">
          <i class="bi bi-save"></i> {{ saving ? '저장 중...' : '저장' }}
        </button>
        <button class="btn btn-outline-secondary btn-sm" @click="router.push('/workflows')">
          <i class="bi bi-arrow-left"></i> 목록
        </button>
      </div>
    </div>

    <!-- 이름/설명 입력 -->
    <div class="card aiuiux-card mb-3">
      <div class="card-body py-3">
        <div class="row g-3">
          <div class="col-md-4">
            <label class="form-label fw-semibold">Workflow 이름 *</label>
            <input type="text" class="form-control" v-model="workflowForm.workflowName" placeholder="예: 고객 문의 처리 플로우">
          </div>
          <div class="col-md-8">
            <label class="form-label fw-semibold">설명</label>
            <input type="text" class="form-control" v-model="workflowForm.description" placeholder="워크플로우의 목적을 간략히 설명하세요">
          </div>
        </div>
      </div>
    </div>

    <!-- 시각적 편집기 -->
    <div v-if="viewMode === 'visual'" class="wfb-editor-wrap card aiuiux-card">
      <div class="wfb-editor-body">

        <!-- 노드 팔레트 (왼쪽) -->
        <div class="wfb-palette">
          <div class="wfb-palette-title">노드 추가</div>
          <div
            v-for="nt in nodeTypes"
            :key="nt.type"
            class="wfb-palette-item"
            draggable="true"
            @dragstart="onDragStart($event, nt.type)"
            :style="{ borderLeftColor: nt.color }"
          >
            <i :class="nt.icon" :style="{ color: nt.color }"></i>
            <span>{{ nt.label }}</span>
          </div>
          <div class="wfb-palette-hint">드래그하여 캔버스에 추가</div>
        </div>

        <!-- Vue Flow 캔버스 (중앙) -->
        <div
          class="wfb-canvas"
          @dragover.prevent
          @drop="onDrop"
          ref="canvasRef"
        >
          <VueFlow
            v-model:nodes="flowNodes"
            v-model:edges="flowEdges"
            :default-viewport="{ zoom: 1 }"
            :min-zoom="0.3"
            :max-zoom="2"
            :snap-to-grid="true"
            :snap-grid="[20, 20]"
            :connect-on-click="false"
            fit-view-on-init
            @connect="onConnect"
            @node-click="onNodeClick"
            @pane-click="selectedNode = null"
          >
            <Background pattern-color="#dee2e6" :gap="20" />
            <Controls />

            <!-- 커스텀 노드 렌더링 -->
            <template #node-wf="{ data, id }">
              <div
                class="wf-node"
                :class="{ 'wf-node--selected': selectedNode?.id === id }"
                :style="{ borderTopColor: getNodeColor(data.nodeType) }"
              >
                <div class="wf-node-header" :style="{ background: getNodeColor(data.nodeType) }">
                  <i :class="getNodeIcon(data.nodeType)"></i>
                  <span>{{ getNodeLabel(data.nodeType) }}</span>
                </div>
                <div class="wf-node-body">
                  <div class="wf-node-name">{{ data.label || '이름 없음' }}</div>
                  <div class="wf-node-type-badge">{{ data.nodeType }}</div>
                </div>
                <!-- 연결 핸들 — Position 은 enum 이므로 :position 바인딩으로 Position.Left/Right 전달 -->
                <Handle type="target" :position="Position.Left" />
                <Handle type="source" :position="Position.Right" />
                <template v-if="data.nodeType === 'Condition'">
                  <Handle id="true" type="source" :position="Position.Right" style="top: 35%" />
                  <Handle id="false" type="source" :position="Position.Right" style="top: 65%" />
                </template>
              </div>
            </template>
          </VueFlow>
        </div>

        <!-- 노드 속성 편집기 (오른쪽) -->
        <div class="wfb-props" v-if="selectedNode">
          <div class="wfb-props-title">
            <i :class="getNodeIcon(selectedNode.data.nodeType)" :style="{ color: getNodeColor(selectedNode.data.nodeType) }"></i>
            노드 설정
          </div>

          <div class="mb-3">
            <label class="form-label fw-semibold">노드 이름</label>
            <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.label" @input="markDirty" placeholder="노드 식별 이름">
          </div>

          <div class="mb-3">
            <label class="form-label fw-semibold">노드 타입</label>
            <input type="text" class="form-control form-control-sm" :value="selectedNode.data.nodeType" readonly>
          </div>

          <!-- Agent 노드 설정 -->
          <template v-if="selectedNode.data.nodeType === 'Agent'">
            <div class="mb-3">
              <label class="form-label fw-semibold">에이전트 선택</label>
              <select class="form-select form-select-sm" v-model="selectedNode.data.config.agentId" @change="markDirty">
                <option value="">-- 선택하세요 --</option>
                <option v-for="a in agents" :key="a.agentId" :value="a.agentId">{{ a.agentName }}</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">입력 변수</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.inputVar" @input="markDirty" placeholder="예: {{input}}">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">출력 변수</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.outputVar" @input="markDirty" placeholder="예: agentResult">
            </div>
          </template>

          <!-- LLM 노드 설정 -->
          <template v-if="selectedNode.data.nodeType === 'LLM'">
            <div class="mb-3">
              <label class="form-label fw-semibold">프롬프트</label>
              <textarea class="form-control form-control-sm" rows="4" v-model="selectedNode.data.config.prompt" @input="markDirty" placeholder="LLM에 전달할 프롬프트"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">모델</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.model" @input="markDirty" placeholder="예: gpt-4o-mini">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">출력 변수</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.outputVar" @input="markDirty" placeholder="예: llmResult">
            </div>
          </template>

          <!-- Condition 노드 설정 -->
          <template v-if="selectedNode.data.nodeType === 'Condition'">
            <div class="mb-3">
              <label class="form-label fw-semibold">조건식</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.condition" @input="markDirty" placeholder="예: {{score}} > 80">
            </div>
            <div class="text-muted small">
              <span class="badge bg-success me-1">True</span> 오른쪽 위 핸들<br>
              <span class="badge bg-danger me-1">False</span> 오른쪽 아래 핸들
            </div>
          </template>

          <!-- Loop 노드 설정 -->
          <template v-if="selectedNode.data.nodeType === 'Loop'">
            <div class="mb-3">
              <label class="form-label fw-semibold">반복 횟수</label>
              <input type="number" class="form-control form-control-sm" v-model.number="selectedNode.data.config.maxIterations" @input="markDirty" min="1" max="100" placeholder="3">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">반복 변수</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.iterVar" @input="markDirty" placeholder="예: items">
            </div>
          </template>

          <!-- Tool 노드 설정 -->
          <template v-if="selectedNode.data.nodeType === 'Tool'">
            <div class="mb-3">
              <label class="form-label fw-semibold">도구 ID</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.toolId" @input="markDirty" placeholder="도구 ID">
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">입력 데이터 (JSON)</label>
              <textarea class="form-control form-control-sm font-monospace" rows="3" v-model="selectedNode.data.config.inputJson" @input="markDirty" placeholder='{"key": "{{var}}"}'></textarea>
            </div>
          </template>

          <!-- DataTransform 노드 설정 -->
          <template v-if="selectedNode.data.nodeType === 'DataTransform'">
            <div class="mb-3">
              <label class="form-label fw-semibold">변환 식 (JSON Path 또는 템플릿)</label>
              <textarea class="form-control form-control-sm font-monospace" rows="4" v-model="selectedNode.data.config.transform" @input="markDirty"></textarea>
            </div>
          </template>

          <!-- 공통: Start/Output -->
          <template v-if="selectedNode.data.nodeType === 'Start'">
            <div class="mb-3">
              <label class="form-label fw-semibold">입력 변수 이름</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.inputVar" @input="markDirty" placeholder="예: userInput">
            </div>
          </template>

          <template v-if="selectedNode.data.nodeType === 'Output'">
            <div class="mb-3">
              <label class="form-label fw-semibold">출력 변수 이름</label>
              <input type="text" class="form-control form-control-sm" v-model="selectedNode.data.config.outputVar" @input="markDirty" placeholder="예: finalResult">
            </div>
          </template>

          <!-- 고급: 원시 JSON 설정 -->
          <details class="mt-3">
            <summary class="text-muted small" style="cursor:pointer">고급 설정 (JSON)</summary>
            <textarea class="form-control form-control-sm font-monospace mt-2" rows="5"
              :value="JSON.stringify(selectedNode.data.config, null, 2)"
              @input="onRawConfigEdit"
            ></textarea>
          </details>

          <div class="mt-3 d-flex gap-2">
            <button class="btn btn-danger btn-sm w-100" @click="deleteSelectedNode">
              <i class="bi bi-trash"></i> 노드 삭제
            </button>
          </div>
        </div>

        <!-- 노드 미선택 안내 -->
        <div class="wfb-props wfb-props--empty" v-else>
          <div class="text-center text-muted">
            <i class="bi bi-arrow-left-circle" style="font-size:2rem"></i>
            <p class="mt-2 small">노드를 클릭하면<br>설정이 표시됩니다</p>
          </div>
        </div>

      </div>
    </div>

    <!-- 코드 편집기 -->
    <div v-else class="card aiuiux-card">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-center mb-2">
          <label class="form-label mb-0 fw-semibold">Workflow 정의 (JSON)</label>
          <button class="btn btn-outline-secondary btn-sm" @click="formatJson">
            <i class="bi bi-braces"></i> 포맷
          </button>
        </div>
        <textarea
          class="form-control font-monospace"
          v-model="workflowForm.workflowDefinition"
          rows="24"
          style="font-size: 13px;"
          spellcheck="false"
        ></textarea>
      </div>
    </div>

    <!-- 테스트 결과 모달 -->
    <div v-if="testResult" class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-play-circle me-2"></i>테스트 실행 결과</h5>
            <button type="button" class="btn-close" @click="testResult = null"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <span class="badge" :class="testResult.status === 'Completed' ? 'bg-success' : 'bg-danger'">
                {{ testResult.status }}
              </span>
              <span class="ms-2 text-muted small">실행 시간: {{ testResult.executionTime }}ms</span>
            </div>
            <div v-if="testResult.outputData">
              <label class="fw-semibold">출력 데이터</label>
              <pre class="bg-light p-3 rounded small">{{ JSON.stringify(JSON.parse(testResult.outputData || '{}'), null, 2) }}</pre>
            </div>
            <div v-if="testResult.errorMessage" class="alert alert-danger small">
              {{ testResult.errorMessage }}
            </div>
            <div v-if="testResult.nodeExecutions?.length">
              <label class="fw-semibold mb-2">노드별 실행 결과</label>
              <div class="table-responsive">
                <table class="table table-sm table-bordered">
                  <thead class="table-light">
                    <tr>
                      <th>노드</th><th>타입</th><th>상태</th><th>시간</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="ne in testResult.nodeExecutions" :key="ne.nodeExecutionId">
                      <td>{{ ne.nodeCode }}</td>
                      <td>{{ ne.nodeType }}</td>
                      <td><span class="badge" :class="ne.status === 'Completed' ? 'bg-success' : 'bg-danger'">{{ ne.status }}</span></td>
                      <td>{{ ne.executionTime }}ms</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="testResult = null">닫기</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Phase 3 후속 트랙 (D-1) 완료 — @vue-flow/core 의 NodeMouseEvent 시그니처 + Position enum
// 을 정확한 타입으로 import 하여 strict 게이트 통과. (@ts-nocheck 해제, 트랙 #9)
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import type { NodeMouseEvent } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import api from '@/services/api'

const route = useRoute()
const router = useRouter()

const viewMode = ref<'visual' | 'code'>('visual')
const saving = ref(false)
const testing = ref(false)
const testResult = ref<any>(null)
const isDirty = ref(false)
const canvasRef = ref<HTMLElement | null>(null)
const selectedNode = ref<any>(null)
const agents = ref<any[]>([])

const workflowForm = ref({
  workflowName: '',
  description: '',
  workflowDefinition: '{}'
})

// ── Vue Flow 상태 ────────────────────────────────────────────────────────────
const flowNodes = ref<any[]>([])
const flowEdges = ref<any[]>([])

const { addNodes, addEdges, project } = useVueFlow()

// ── 노드 타입 정의 ────────────────────────────────────────────────────────────
const nodeTypes = [
  { type: 'Start',         label: '시작',       icon: 'bi bi-play-circle-fill', color: '#22c55e' },
  { type: 'Agent',         label: 'AI 에이전트', icon: 'bi bi-robot',            color: '#6366f1' },
  { type: 'LLM',           label: 'LLM 호출',   icon: 'bi bi-cpu',              color: '#8b5cf6' },
  { type: 'Tool',          label: '도구 실행',   icon: 'bi bi-wrench',           color: '#f97316' },
  { type: 'Condition',     label: '조건 분기',   icon: 'bi bi-signpost-split',   color: '#eab308' },
  { type: 'Loop',          label: '반복',        icon: 'bi bi-arrow-repeat',     color: '#06b6d4' },
  { type: 'DataTransform', label: '데이터 변환', icon: 'bi bi-shuffle',          color: '#ec4899' },
  { type: 'Output',        label: '종료/출력',   icon: 'bi bi-stop-circle-fill', color: '#ef4444' },
]

const getNodeColor = (type: string) => nodeTypes.find(n => n.type === type)?.color ?? '#6c757d'
const getNodeIcon  = (type: string) => nodeTypes.find(n => n.type === type)?.icon  ?? 'bi bi-circle'
const getNodeLabel = (type: string) => nodeTypes.find(n => n.type === type)?.label ?? type

// ── 드래그 앤 드롭 ─────────────────────────────────────────────────────────────
let dragNodeType = ''

const onDragStart = (e: DragEvent, type: string) => {
  dragNodeType = type
  e.dataTransfer!.effectAllowed = 'move'
}

const onDrop = (e: DragEvent) => {
  if (!dragNodeType || !canvasRef.value) return
  const bounds = canvasRef.value.getBoundingClientRect()
  const pos = project({
    x: e.clientX - bounds.left,
    y: e.clientY - bounds.top
  })
  const id = `node_${Date.now()}`
  addNodes([{
    id,
    type: 'wf',
    position: pos,
    data: {
      label: getNodeLabel(dragNodeType),
      nodeType: dragNodeType,
      config: {}
    }
  }])
  dragNodeType = ''
  markDirty()
}

// ── 연결 핸들러 ────────────────────────────────────────────────────────────────
const onConnect = (params: any) => {
  addEdges([{
    id: `e_${params.source}_${params.target}`,
    source: params.source,
    sourceHandle: params.sourceHandle,
    target: params.target,
    targetHandle: params.targetHandle,
    animated: true,
    style: { stroke: '#6366f1', strokeWidth: 2 }
  }])
  markDirty()
}

// ── 노드 클릭 ──────────────────────────────────────────────────────────────────
// @vue-flow/core 의 nodeClick emit 시그니처: (event: NodeMouseEvent) => void
// NodeMouseEvent shape = { event: MouseTouchEvent, node: GraphNode }
const onNodeClick = ({ node }: NodeMouseEvent) => {
  selectedNode.value = node
}

const deleteSelectedNode = () => {
  if (!selectedNode.value) return
  flowNodes.value = flowNodes.value.filter(n => n.id !== selectedNode.value.id)
  flowEdges.value = flowEdges.value.filter(
    e => e.source !== selectedNode.value.id && e.target !== selectedNode.value.id
  )
  selectedNode.value = null
  markDirty()
}

const markDirty = () => { isDirty.value = true }

// ── 속성 편집기 Raw JSON ───────────────────────────────────────────────────────
const onRawConfigEdit = (e: Event) => {
  try {
    selectedNode.value.data.config = JSON.parse((e.target as HTMLTextAreaElement).value)
    markDirty()
  } catch {}
}

// ── 뷰 모드 전환 ────────────────────────────────────────────────────────────────
const toggleView = () => {
  if (viewMode.value === 'visual') {
    // 시각적 → 코드: flow 상태를 JSON으로 직렬화
    workflowForm.value.workflowDefinition = flowToJson()
    viewMode.value = 'code'
  } else {
    // 코드 → 시각적: JSON을 파싱하여 flow 상태로 복원
    jsonToFlow(workflowForm.value.workflowDefinition)
    viewMode.value = 'visual'
  }
}

// ── JSON 직렬화 / 역직렬화 ──────────────────────────────────────────────────────
const flowToJson = () => {
  const nodes = flowNodes.value.map((n, i) => ({
    nodeCode: n.id,
    nodeType: n.data.nodeType,
    nodeConfig: JSON.stringify(n.data.config ?? {}),
    positionX: n.position.x,
    positionY: n.position.y,
    sortOrder: i,
    connections: JSON.stringify({
      targets: flowEdges.value
        .filter(e => e.source === n.id)
        .map(e => ({ nodeCode: e.target, handle: e.sourceHandle ?? 'default' }))
    }),
    label: n.data.label
  }))
  return JSON.stringify({ nodes }, null, 2)
}

const jsonToFlow = (jsonStr: string) => {
  try {
    const def = JSON.parse(jsonStr)
    const nodes = def.nodes ?? []
    const newNodes: any[] = nodes.map((n: any) => ({
      id: n.nodeCode,
      type: 'wf',
      position: { x: n.positionX ?? 100, y: n.positionY ?? 100 },
      data: {
        label: n.label ?? getNodeLabel(n.nodeType),
        nodeType: n.nodeType,
        config: (() => { try { return JSON.parse(n.nodeConfig ?? '{}') } catch { return {} } })()
      }
    }))
    const newEdges: any[] = []
    nodes.forEach((n: any) => {
      try {
        const conns = JSON.parse(n.connections ?? '{}')
        ;(conns.targets ?? []).forEach((t: any) => {
          newEdges.push({
            id: `e_${n.nodeCode}_${t.nodeCode}`,
            source: n.nodeCode,
            sourceHandle: t.handle !== 'default' ? t.handle : undefined,
            target: t.nodeCode,
            animated: true,
            style: { stroke: '#6366f1', strokeWidth: 2 }
          })
        })
      } catch {}
    })
    flowNodes.value = newNodes
    flowEdges.value = newEdges
  } catch (e) {
    console.error('JSON 파싱 오류:', e)
  }
}

// ── JSON 포맷터 ─────────────────────────────────────────────────────────────────
const formatJson = () => {
  try {
    workflowForm.value.workflowDefinition = JSON.stringify(
      JSON.parse(workflowForm.value.workflowDefinition), null, 2
    )
  } catch { alert('유효하지 않은 JSON입니다.') }
}

// ── 저장 ───────────────────────────────────────────────────────────────────────
const saveWorkflow = async () => {
  if (!workflowForm.value.workflowName.trim()) {
    alert('Workflow 이름을 입력해주세요.')
    return
  }

  // 시각적 모드라면 먼저 직렬화
  if (viewMode.value === 'visual') {
    workflowForm.value.workflowDefinition = flowToJson()
  }

  try {
    saving.value = true
    const def = JSON.parse(workflowForm.value.workflowDefinition)
    const request = {
      workflowName: workflowForm.value.workflowName,
      description: workflowForm.value.description,
      workflowDefinition: workflowForm.value.workflowDefinition,
      nodes: (def.nodes ?? []).map((n: any) => ({
        nodeCode: n.nodeCode,
        nodeType: n.nodeType,
        nodeConfig: n.nodeConfig ?? '{}',
        positionX: n.positionX ?? 0,
        positionY: n.positionY ?? 0,
        connections: n.connections ?? '{}',
        sortOrder: n.sortOrder ?? 0
      }))
    }

    if (route.query.id) {
      await api.put(`/workflows/${route.query.id}`, request)
    } else {
      await api.post('/workflows', request)
    }
    isDirty.value = false
    alert('저장되었습니다.')
    router.push('/workflows')
  } catch (error: any) {
    alert('저장 실패: ' + (error.response?.data?.message ?? error.message))
  } finally {
    saving.value = false
  }
}

// ── 테스트 실행 ────────────────────────────────────────────────────────────────
const testWorkflow = async () => {
  if (!route.query.id) {
    alert('테스트를 실행하려면 먼저 워크플로우를 저장해주세요.')
    return
  }
  try {
    testing.value = true
    const response = await api.post(`/workflows/${route.query.id}/execute`, {
      inputData: '{}',
      waitForCompletion: true
    })
    testResult.value = response.data
  } catch (error: any) {
    alert('테스트 실패: ' + (error.response?.data?.message ?? error.message))
  } finally {
    testing.value = false
  }
}

// ── 에이전트 목록 로드 ─────────────────────────────────────────────────────────
const loadAgents = async () => {
  try {
    const response = await api.get('/agents')
    agents.value = response.data ?? []
  } catch {}
}

// ── 초기화 ────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadAgents()

  if (route.query.id) {
    try {
      const response = await api.get(`/workflows/${route.query.id}`)
      const workflow = response.data
      workflowForm.value.workflowName = workflow.workflowName
      workflowForm.value.description = workflow.description ?? ''
      workflowForm.value.workflowDefinition = workflow.workflowDefinition ?? '{}'
      // 기존 nodes 데이터를 workflowDefinition에 병합
      if (workflow.nodes?.length) {
        const existingDef = (() => { try { return JSON.parse(workflowForm.value.workflowDefinition) } catch { return {} } })()
        if (!existingDef.nodes?.length) {
          existingDef.nodes = workflow.nodes
          workflowForm.value.workflowDefinition = JSON.stringify(existingDef, null, 2)
        }
      }
      jsonToFlow(workflowForm.value.workflowDefinition)
    } catch (error) {
      console.error('워크플로우 로드 오류:', error)
    }
  } else {
    // 새 워크플로우: 기본 시작/종료 노드 추가
    flowNodes.value = [
      {
        id: 'start',
        type: 'wf',
        position: { x: 80, y: 200 },
        data: { label: '시작', nodeType: 'Start', config: { inputVar: 'userInput' } }
      },
      {
        id: 'output',
        type: 'wf',
        position: { x: 600, y: 200 },
        data: { label: '종료', nodeType: 'Output', config: { outputVar: 'finalResult' } }
      }
    ]
  }
})
</script>

<style scoped>
/* ── 레이아웃 ────────────────────────────────────────────────────────────────── */
.wfb-wrap { display: flex; flex-direction: column; height: calc(100vh - 60px); }

.wfb-editor-wrap { flex: 1; min-height: 0; }
.wfb-editor-body {
  display: flex;
  height: 640px;
  overflow: hidden;
}

/* ── 팔레트 ────────────────────────────────────────────────────────────────── */
.wfb-palette {
  width: 140px;
  flex-shrink: 0;
  border-right: 1px solid var(--ai-border);
  padding: 12px 8px;
  background: var(--ai-bg-card);
  overflow-y: auto;
}
.wfb-palette-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ai-text-muted);
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--ai-border);
}
.wfb-palette-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 8px;
  margin-bottom: 4px;
  border-radius: 6px;
  border-left: 3px solid transparent;
  background: var(--ai-bg);
  font-size: 12px;
  cursor: grab;
  user-select: none;
  transition: background 0.15s;
}
.wfb-palette-item:hover { background: var(--ai-bg-hover); }
.wfb-palette-item:active { cursor: grabbing; }
.wfb-palette-hint {
  font-size: 10px;
  color: var(--ai-text-muted);
  text-align: center;
  margin-top: 12px;
}

/* ── 캔버스 ──────────────────────────────────────────────────────────────────── */
.wfb-canvas {
  flex: 1;
  min-width: 0;
  height: 100%;
  background: var(--ai-bg);
}
.vue-flow { height: 100%; }

/* ── 커스텀 노드 ──────────────────────────────────────────────────────────────── */
.wf-node {
  min-width: 140px;
  border-radius: 8px;
  border: 2px solid var(--ai-border);
  overflow: hidden;
  background: var(--ai-bg-card);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: box-shadow 0.15s, border-color 0.15s;
}
.wf-node--selected { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.2); }
.wf-node-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}
.wf-node-body { padding: 8px 10px; }
.wf-node-name { font-size: 12px; font-weight: 600; color: var(--ai-text); }
.wf-node-type-badge {
  font-size: 10px;
  color: var(--ai-text-muted);
  margin-top: 2px;
}

/* ── 속성 패널 ───────────────────────────────────────────────────────────────── */
.wfb-props {
  width: 240px;
  flex-shrink: 0;
  border-left: 1px solid var(--ai-border);
  padding: 14px;
  background: var(--ai-bg-card);
  overflow-y: auto;
}
.wfb-props--empty {
  display: flex;
  align-items: center;
  justify-content: center;
}
.wfb-props-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--ai-border);
  display: flex;
  align-items: center;
  gap: 6px;
}
</style>
