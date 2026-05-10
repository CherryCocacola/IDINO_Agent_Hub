<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilProjects.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilProjects.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-primary btn-sm me-2"
          @click="openCreateProjectModal"
          :aria-label="t('adminDocutilProjects.createProject')"
        >
          <i class="bi bi-plus-lg" aria-hidden="true"></i>
          {{ t('adminDocutilProjects.createProject') }}
        </button>
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="refreshAll"
          :disabled="loadingProjects || loadingTree || loadingDetail"
          :aria-label="t('adminDocutilProjects.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilProjects.refresh') }}
        </button>
      </div>
    </div>

    <!-- 에러 알림 -->
    <div
      v-if="errorMessage"
      class="alert alert-danger d-flex justify-content-between align-items-center"
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

    <!-- 탭 토글 + 검색 -->
    <div class="d-flex flex-wrap align-items-end gap-2 mb-3">
      <ul class="nav nav-pills" role="tablist">
        <li class="nav-item">
          <button
            type="button"
            class="nav-link"
            :class="{ active: activeTab === 'list' }"
            @click="activeTab = 'list'"
          >
            <i class="bi bi-list-ul me-1" aria-hidden="true"></i>
            {{ t('adminDocutilProjects.tabList') }}
          </button>
        </li>
        <li class="nav-item">
          <button
            type="button"
            class="nav-link"
            :class="{ active: activeTab === 'tree' }"
            @click="activeTab = 'tree'; void loadTree()"
          >
            <i class="bi bi-diagram-3 me-1" aria-hidden="true"></i>
            {{ t('adminDocutilProjects.tabTree') }}
          </button>
        </li>
      </ul>

      <div v-if="activeTab === 'list'" class="d-flex flex-grow-1 align-items-center gap-2">
        <input
          v-model="searchInput"
          type="text"
          class="form-control form-control-sm"
          :placeholder="t('adminDocutilProjects.searchPlaceholder')"
          :aria-label="t('adminDocutilProjects.search')"
          @keydown.enter.prevent="applySearch"
        />
        <button class="btn btn-sm btn-outline-primary" @click="applySearch">
          {{ t('adminDocutilProjects.applySearch') }}
        </button>
        <button
          v-if="searchQuery"
          class="btn btn-sm btn-outline-secondary"
          @click="clearSearch"
        >
          {{ t('adminDocutilProjects.clearSearch') }}
        </button>
      </div>
    </div>

    <div class="row g-3">
      <!-- 좌측 : 프로젝트 목록 또는 트리 -->
      <div class="col-lg-5">
        <!-- 목록 탭 -->
        <div v-if="activeTab === 'list'" class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0">
              <i class="bi bi-folder me-1" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.tabList') }}
              <span v-if="projectList && !loadingProjects" class="text-muted small ms-1">
                ({{ projectList.total }})
              </span>
            </h6>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingProjects" class="text-center py-4">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div
              v-else-if="!projectList || projectList.items.length === 0"
              class="text-center py-4 text-muted"
            >
              {{ t('adminDocutilProjects.empty') }}
            </div>
            <ul v-else class="list-group list-group-flush">
              <li
                v-for="p in projectList.items"
                :key="p.id"
                class="list-group-item"
                :class="{ 'list-group-item-active': selectedProjectId === p.id }"
                @click="selectProject(p.id)"
              >
                <div class="d-flex justify-content-between align-items-start">
                  <div class="flex-grow-1 me-2">
                    <div class="fw-semibold">{{ p.name }}</div>
                    <div v-if="p.description" class="small text-muted text-truncate">
                      {{ p.description }}
                    </div>
                    <div class="small text-muted">
                      <i class="bi bi-clock me-1" aria-hidden="true"></i>
                      {{ formatDate(p.createdAt) }}
                    </div>
                  </div>
                  <div class="btn-group btn-group-sm" role="group">
                    <button
                      class="btn btn-outline-secondary"
                      :title="t('adminDocutilProjects.edit')"
                      @click.stop="openEditProjectModal(p)"
                    >
                      <i class="bi bi-pencil" aria-hidden="true"></i>
                    </button>
                    <button
                      class="btn btn-outline-danger"
                      :title="t('adminDocutilProjects.delete')"
                      @click.stop="confirmDeleteProject(p)"
                    >
                      <i class="bi bi-trash" aria-hidden="true"></i>
                    </button>
                  </div>
                </div>
              </li>
            </ul>

            <!-- 페이지네이션 -->
            <div
              v-if="projectList && projectList.total > size"
              class="card-footer bg-transparent d-flex justify-content-between align-items-center"
            >
              <div class="small text-muted">
                {{ page }} / {{ Math.max(1, Math.ceil(projectList.total / size)) }}
              </div>
              <div class="btn-group btn-group-sm">
                <button
                  class="btn btn-outline-secondary"
                  :disabled="page <= 1 || loadingProjects"
                  @click="changePage(page - 1)"
                >
                  <i class="bi bi-chevron-left" aria-hidden="true"></i>
                </button>
                <button
                  class="btn btn-outline-secondary"
                  :disabled="page * size >= projectList.total || loadingProjects"
                  @click="changePage(page + 1)"
                >
                  <i class="bi bi-chevron-right" aria-hidden="true"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 트리 탭 -->
        <div v-else class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0">
              <i class="bi bi-diagram-3 me-1" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.tabTree') }}
            </h6>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingTree" class="text-center py-4">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="tree.length === 0" class="text-center py-4 text-muted">
              {{ t('adminDocutilProjects.empty') }}
            </div>
            <ul v-else class="list-group list-group-flush">
              <li
                v-for="node in tree"
                :key="node.id"
                class="list-group-item"
                :class="{ 'list-group-item-active': selectedProjectId === node.id }"
                @click="selectProject(node.id)"
              >
                <div class="d-flex justify-content-between align-items-center">
                  <div class="flex-grow-1 me-2">
                    <i class="bi bi-folder me-1" aria-hidden="true"></i>
                    <span class="fw-semibold">{{ node.name }}</span>
                    <span class="ms-2 small text-muted">
                      {{ t('adminDocutilProjects.treeBoardCount', { count: node.boards.length }) }}
                    </span>
                  </div>
                </div>
                <div v-if="node.boards.length > 0" class="ms-3 mt-1">
                  <div
                    v-for="board in node.boards"
                    :key="board.id"
                    class="small text-muted d-flex align-items-center"
                  >
                    <i class="bi bi-bookmark me-1" aria-hidden="true"></i>
                    {{ board.name }}
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 우측 : 선택된 프로젝트 상세 -->
      <div class="col-lg-7">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
              <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.projectInfo') }}
            </h6>
            <button
              v-if="selectedProject"
              class="btn btn-sm btn-outline-secondary"
              @click="openEditProjectModal(selectedProject)"
            >
              <i class="bi bi-pencil" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.edit') }}
            </button>
          </div>
          <div class="card-body">
            <div v-if="loadingDetail" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="!selectedProject" class="text-muted">
              {{ t('adminDocutilProjects.selectPrompt') }}
            </div>
            <dl v-else class="row mb-0 small">
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colId') }}</dt>
              <dd class="col-sm-9"><code>{{ selectedProject.id }}</code></dd>
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colName') }}</dt>
              <dd class="col-sm-9">{{ selectedProject.name }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colDescription') }}</dt>
              <dd class="col-sm-9">
                <span v-if="selectedProject.description">{{ selectedProject.description }}</span>
                <span v-else class="text-muted">-</span>
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colAllowDownload') }}</dt>
              <dd class="col-sm-9">
                <span v-if="selectedProject.allowOriginalDownload" class="badge bg-success">
                  {{ t('adminDocutilProjects.yes') }}
                </span>
                <span v-else class="badge bg-secondary">
                  {{ t('adminDocutilProjects.no') }}
                </span>
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colCreatedBy') }}</dt>
              <dd class="col-sm-9"><code>{{ selectedProject.createdBy }}</code></dd>
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colCreatedAt') }}</dt>
              <dd class="col-sm-9">{{ formatDate(selectedProject.createdAt) }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilProjects.colUpdatedAt') }}</dt>
              <dd class="col-sm-9">{{ formatDate(selectedProject.updatedAt) }}</dd>
            </dl>
          </div>
        </div>

        <!-- 멤버 -->
        <div v-if="selectedProject" class="card aiuiux-card mt-3">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0">
              <i class="bi bi-people me-1" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.projectMembers') }}
              <span class="text-muted small ms-1">({{ members.length }})</span>
            </h6>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingMembers" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="members.length === 0" class="text-muted text-center py-3">
              {{ t('adminDocutilProjects.membersEmpty') }}
            </div>
            <table v-else class="table table-sm mb-0 small">
              <thead class="table-light">
                <tr>
                  <th>{{ t('adminDocutilProjects.colMemberUsername') }}</th>
                  <th>{{ t('adminDocutilProjects.colMemberEmail') }}</th>
                  <th>{{ t('adminDocutilProjects.colMemberRole') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in members" :key="m.id">
                  <td>{{ m.username }}</td>
                  <td>{{ m.email }}</td>
                  <td>
                    <span class="badge" :class="m.role === 'admin' ? 'bg-primary' : 'bg-secondary'">
                      {{ m.role }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 부서 -->
        <div v-if="selectedProject" class="card aiuiux-card mt-3">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0">
              <i class="bi bi-diagram-2 me-1" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.projectDepartments') }}
              <span class="text-muted small ms-1">({{ projectDepartments.length }})</span>
            </h6>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingDepartments" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="projectDepartments.length === 0" class="text-muted text-center py-3">
              {{ t('adminDocutilProjects.departmentsEmpty') }}
            </div>
            <table v-else class="table table-sm mb-0 small">
              <thead class="table-light">
                <tr>
                  <th>{{ t('adminDocutilProjects.colDeptName') }}</th>
                  <th>{{ t('adminDocutilProjects.colDeptDepth') }}</th>
                  <th>{{ t('adminDocutilProjects.colDeptPath') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in projectDepartments" :key="d.id">
                  <td>{{ d.name }}</td>
                  <td>{{ d.depth }}</td>
                  <td><code class="small">{{ d.path }}</code></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 보드 -->
        <div v-if="selectedProject" class="card aiuiux-card mt-3">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
              <i class="bi bi-bookmark me-1" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.projectBoards') }}
              <span v-if="boardList" class="text-muted small ms-1">
                ({{ boardList.total }})
              </span>
            </h6>
            <button class="btn btn-sm btn-outline-primary" @click="openCreateBoardModal">
              <i class="bi bi-plus-lg" aria-hidden="true"></i>
              {{ t('adminDocutilProjects.createBoard') }}
            </button>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingBoards" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div
              v-else-if="!boardList || boardList.items.length === 0"
              class="text-muted text-center py-3"
            >
              {{ t('adminDocutilProjects.boardsEmpty') }}
            </div>
            <table v-else class="table table-sm mb-0 small">
              <thead class="table-light">
                <tr>
                  <th>{{ t('adminDocutilProjects.colBoardName') }}</th>
                  <th>{{ t('adminDocutilProjects.colBoardDescription') }}</th>
                  <th>{{ t('adminDocutilProjects.colCreatedAt') }}</th>
                  <th class="text-end" style="width: 100px;">&nbsp;</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in boardList.items" :key="b.id">
                  <td>{{ b.name }}</td>
                  <td>
                    <span v-if="b.description">{{ b.description }}</span>
                    <span v-else class="text-muted">-</span>
                  </td>
                  <td>{{ formatDate(b.createdAt) }}</td>
                  <td class="text-end">
                    <div class="btn-group btn-group-sm">
                      <button
                        class="btn btn-outline-secondary"
                        :title="t('adminDocutilProjects.edit')"
                        @click="openEditBoardModal(b)"
                      >
                        <i class="bi bi-pencil" aria-hidden="true"></i>
                      </button>
                      <button
                        class="btn btn-outline-danger"
                        :title="t('adminDocutilProjects.delete')"
                        @click="confirmDeleteBoard(b)"
                      >
                        <i class="bi bi-trash" aria-hidden="true"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 프로젝트 생성/수정 모달 -->
    <div v-if="projectModal.open" class="modal-overlay d-flex justify-content-center align-items-center">
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            {{ projectModal.mode === 'create'
              ? t('adminDocutilProjects.modalCreateProjectTitle')
              : t('adminDocutilProjects.modalEditProjectTitle') }}
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeProjectModal"
          ></button>
        </div>
        <div class="card-body">
          <div class="mb-3">
            <label class="form-label small">{{ t('adminDocutilProjects.colName') }}</label>
            <input
              v-model="projectModal.name"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilProjects.namePlaceholder')"
              :maxlength="255"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label small">{{ t('adminDocutilProjects.colDescription') }}</label>
            <textarea
              v-model="projectModal.description"
              class="form-control"
              :placeholder="t('adminDocutilProjects.descriptionPlaceholder')"
              :maxlength="2000"
              rows="3"
            ></textarea>
          </div>
          <!-- allow_original_download 은 ProjectCreate(POST) 에만 존재. ProjectUpdate 에는 미존재 → 신규 생성 모드에서만 노출 -->
          <div v-if="projectModal.mode === 'create'" class="mb-3 form-check">
            <input
              id="allowOriginalDownload"
              v-model="projectModal.allowOriginalDownload"
              type="checkbox"
              class="form-check-input"
            />
            <label for="allowOriginalDownload" class="form-check-label small">
              {{ t('adminDocutilProjects.allowOriginalDownload') }}
            </label>
            <div class="form-text small">
              {{ t('adminDocutilProjects.allowOriginalDownloadHint') }}
            </div>
          </div>
          <div v-if="projectModal.error" class="alert alert-danger small mb-0" role="alert">
            {{ projectModal.error }}
          </div>
        </div>
        <div class="card-footer bg-transparent border-top text-end">
          <button
            type="button"
            class="btn btn-outline-secondary me-2"
            @click="closeProjectModal"
            :disabled="projectModal.submitting"
          >
            {{ t('adminDocutilProjects.cancel') }}
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="submitProjectModal"
            :disabled="projectModal.submitting"
          >
            <span v-if="projectModal.submitting" class="spinner-border spinner-border-sm me-1"></span>
            {{ projectModal.mode === 'create'
              ? t('adminDocutilProjects.create')
              : t('adminDocutilProjects.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 보드 생성/수정 모달 -->
    <div v-if="boardModal.open" class="modal-overlay d-flex justify-content-center align-items-center">
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            {{ boardModal.mode === 'create'
              ? t('adminDocutilProjects.modalCreateBoardTitle')
              : t('adminDocutilProjects.modalEditBoardTitle') }}
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeBoardModal"
          ></button>
        </div>
        <div class="card-body">
          <div class="mb-3">
            <label class="form-label small">{{ t('adminDocutilProjects.colBoardName') }}</label>
            <input
              v-model="boardModal.name"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilProjects.boardNamePlaceholder')"
              :maxlength="255"
              required
            />
          </div>
          <div class="mb-3">
            <label class="form-label small">{{ t('adminDocutilProjects.colBoardDescription') }}</label>
            <textarea
              v-model="boardModal.description"
              class="form-control"
              :placeholder="t('adminDocutilProjects.descriptionPlaceholder')"
              :maxlength="2000"
              rows="3"
            ></textarea>
          </div>
          <div v-if="boardModal.error" class="alert alert-danger small mb-0" role="alert">
            {{ boardModal.error }}
          </div>
        </div>
        <div class="card-footer bg-transparent border-top text-end">
          <button
            type="button"
            class="btn btn-outline-secondary me-2"
            @click="closeBoardModal"
            :disabled="boardModal.submitting"
          >
            {{ t('adminDocutilProjects.cancel') }}
          </button>
          <button
            type="button"
            class="btn btn-primary"
            @click="submitBoardModal"
            :disabled="boardModal.submitting"
          >
            <span v-if="boardModal.submitting" class="spinner-border spinner-border-sm me-1"></span>
            {{ boardModal.mode === 'create'
              ? t('adminDocutilProjects.create')
              : t('adminDocutilProjects.save') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// ════════════════════════════════════════════════════════════════════════════
// AdminDocUtilProjects.vue — DocUtil 프로젝트/보드 운영자 콘솔 (Phase 10.1c)
//
// 진입점: 사이드바 docutil 카테고리 → 'DocUtil 프로젝트' (`/admin/docutil-projects`)
//
// 백엔드: AgentHub `/api/admin/docutil/projects[/...]` (BFF 13 endpoint)
// 통합 namespace: `docutil-collections` — 본 화면 mutation 시 AgentBuilder dropdown 도 즉시 갱신.
//
// 레이아웃:
//   - 상단: 탭(목록/트리) + 검색 + 신규 버튼
//   - 좌측: 프로젝트 목록(페이지네이션 + 검색) 또는 트리(boards 펼침)
//   - 우측: 선택된 프로젝트의 정보 + 멤버 + 부서 + 보드(CRUD)
//   - 모달: 프로젝트 생성/수정, 보드 생성/수정
// ════════════════════════════════════════════════════════════════════════════
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  type DocUtilProject,
  type DocUtilProjectList,
  type DocUtilProjectTreeNode,
  type DocUtilProjectMember,
  type DocUtilProjectDepartment,
  type DocUtilBoard,
  type DocUtilBoardList,
  listProjects,
  getProjectTree,
  getProject,
  createProject,
  updateProject,
  deleteProject,
  getProjectMembers,
  getProjectDepartments,
  listProjectBoards,
  createProjectBoard,
  updateProjectBoard,
  deleteProjectBoard,
} from '@/services/docutilService'

const { t } = useI18n()

// ── 상태 ──────────────────────────────────────────────────────────────────
const activeTab = ref<'list' | 'tree'>('list')
const errorMessage = ref<string>('')

const projectList = ref<DocUtilProjectList | null>(null)
const tree = ref<DocUtilProjectTreeNode[]>([])
const selectedProjectId = ref<string | null>(null)
const selectedProject = ref<DocUtilProject | null>(null)
const members = ref<DocUtilProjectMember[]>([])
const projectDepartments = ref<DocUtilProjectDepartment[]>([])
const boardList = ref<DocUtilBoardList | null>(null)

const loadingProjects = ref<boolean>(false)
const loadingTree = ref<boolean>(false)
const loadingDetail = ref<boolean>(false)
const loadingMembers = ref<boolean>(false)
const loadingDepartments = ref<boolean>(false)
const loadingBoards = ref<boolean>(false)

const page = ref<number>(1)
const size = ref<number>(20)
const searchInput = ref<string>('')
const searchQuery = ref<string>('')

// ── 데이터 로드 ───────────────────────────────────────────────────────────
async function loadProjects(): Promise<void> {
  loadingProjects.value = true
  errorMessage.value = ''
  try {
    projectList.value = await listProjects(
      page.value,
      size.value,
      searchQuery.value || undefined
    )
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingProjects.value = false
  }
}

async function loadTree(): Promise<void> {
  if (tree.value.length > 0 && !errorMessage.value) {
    // 이미 로드된 경우 재호출 생략(refreshAll 만 강제 reload).
    return
  }
  loadingTree.value = true
  errorMessage.value = ''
  try {
    tree.value = await getProjectTree()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingTree.value = false
  }
}

async function loadProjectDetail(id: string): Promise<void> {
  loadingDetail.value = true
  errorMessage.value = ''
  try {
    selectedProject.value = await getProject(id)
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingDetail.value = false
  }
}

async function loadMembers(id: string): Promise<void> {
  loadingMembers.value = true
  try {
    members.value = await getProjectMembers(id)
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingMembers.value = false
  }
}

async function loadProjectDepartments(id: string): Promise<void> {
  loadingDepartments.value = true
  try {
    projectDepartments.value = await getProjectDepartments(id)
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingDepartments.value = false
  }
}

async function loadBoards(id: string): Promise<void> {
  loadingBoards.value = true
  try {
    boardList.value = await listProjectBoards(id, 1, 50)
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingBoards.value = false
  }
}

async function refreshAll(): Promise<void> {
  // 트리는 강제 reload — guard 우회.
  tree.value = []
  await Promise.all([
    loadProjects(),
    activeTab.value === 'tree' ? loadTree() : Promise.resolve(),
  ])
  if (selectedProjectId.value) {
    await selectProject(selectedProjectId.value)
  }
}

async function selectProject(id: string): Promise<void> {
  selectedProjectId.value = id
  members.value = []
  projectDepartments.value = []
  boardList.value = null
  await Promise.all([
    loadProjectDetail(id),
    loadMembers(id),
    loadProjectDepartments(id),
    loadBoards(id),
  ])
}

// ── 검색 / 페이지네이션 ──────────────────────────────────────────────────
function applySearch(): void {
  searchQuery.value = searchInput.value.trim()
  page.value = 1
  void loadProjects()
}

function clearSearch(): void {
  searchInput.value = ''
  searchQuery.value = ''
  page.value = 1
  void loadProjects()
}

function changePage(newPage: number): void {
  if (newPage < 1) return
  page.value = newPage
  void loadProjects()
}

// ── 프로젝트 모달 ────────────────────────────────────────────────────────
interface ProjectModalState {
  open: boolean
  mode: 'create' | 'edit'
  editingId: string | null
  name: string
  description: string
  allowOriginalDownload: boolean
  error: string
  submitting: boolean
}

const projectModal = ref<ProjectModalState>({
  open: false,
  mode: 'create',
  editingId: null,
  name: '',
  description: '',
  allowOriginalDownload: true,
  error: '',
  submitting: false,
})

function openCreateProjectModal(): void {
  projectModal.value = {
    open: true,
    mode: 'create',
    editingId: null,
    name: '',
    description: '',
    allowOriginalDownload: true,
    error: '',
    submitting: false,
  }
}

function openEditProjectModal(p: DocUtilProject): void {
  projectModal.value = {
    open: true,
    mode: 'edit',
    editingId: p.id,
    name: p.name,
    description: p.description ?? '',
    allowOriginalDownload: p.allowOriginalDownload,
    error: '',
    submitting: false,
  }
}

function closeProjectModal(): void {
  projectModal.value.open = false
}

async function submitProjectModal(): Promise<void> {
  const trimmedName = projectModal.value.name.trim()
  if (!trimmedName) {
    projectModal.value.error = t('adminDocutilProjects.nameRequired')
    return
  }
  if (trimmedName.length > 255) {
    projectModal.value.error = t('adminDocutilProjects.nameTooLong')
    return
  }
  if (projectModal.value.description.length > 2000) {
    projectModal.value.error = t('adminDocutilProjects.descriptionTooLong')
    return
  }

  projectModal.value.submitting = true
  projectModal.value.error = ''
  try {
    if (projectModal.value.mode === 'create') {
      const created = await createProject({
        name: trimmedName,
        description: projectModal.value.description.trim() || null,
        allowOriginalDownload: projectModal.value.allowOriginalDownload,
      })
      projectModal.value.open = false
      await loadProjects()
      // 새로 만든 프로젝트 자동 선택.
      await selectProject(created.id)
    } else if (projectModal.value.editingId) {
      // partial update — 변경된 필드만 전송.
      const original = selectedProject.value
        ?? projectList.value?.items.find(p => p.id === projectModal.value.editingId)
        ?? null
      const payload: { name?: string; description?: string | null } = {}
      const newDesc = projectModal.value.description.trim()
      if (!original || trimmedName !== original.name) payload.name = trimmedName
      if (!original || newDesc !== (original.description ?? '')) {
        payload.description = newDesc.length > 0 ? newDesc : null
      }
      if (Object.keys(payload).length === 0) {
        projectModal.value.error = t('adminDocutilProjects.noChanges')
        projectModal.value.submitting = false
        return
      }
      await updateProject(projectModal.value.editingId, payload)
      projectModal.value.open = false
      await loadProjects()
      // 동일 항목 선택 상태 유지하며 detail 재로드.
      if (selectedProjectId.value === projectModal.value.editingId) {
        await loadProjectDetail(selectedProjectId.value)
      }
    }
  } catch (err: unknown) {
    projectModal.value.error = extractErrorMessage(err)
  } finally {
    projectModal.value.submitting = false
  }
}

async function confirmDeleteProject(p: DocUtilProject): Promise<void> {
  if (!window.confirm(t('adminDocutilProjects.deleteProjectConfirm', { name: p.name }))) return
  if (!window.confirm(t('adminDocutilProjects.deleteProjectConfirmFinal'))) return

  loadingProjects.value = true
  errorMessage.value = ''
  try {
    await deleteProject(p.id)
    if (selectedProjectId.value === p.id) {
      selectedProjectId.value = null
      selectedProject.value = null
      members.value = []
      projectDepartments.value = []
      boardList.value = null
    }
    await loadProjects()
    if (activeTab.value === 'tree') {
      tree.value = []
      await loadTree()
    }
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingProjects.value = false
  }
}

// ── 보드 모달 ────────────────────────────────────────────────────────────
interface BoardModalState {
  open: boolean
  mode: 'create' | 'edit'
  editingId: string | null
  name: string
  description: string
  error: string
  submitting: boolean
}

const boardModal = ref<BoardModalState>({
  open: false,
  mode: 'create',
  editingId: null,
  name: '',
  description: '',
  error: '',
  submitting: false,
})

function openCreateBoardModal(): void {
  if (!selectedProjectId.value) return
  boardModal.value = {
    open: true,
    mode: 'create',
    editingId: null,
    name: '',
    description: '',
    error: '',
    submitting: false,
  }
}

function openEditBoardModal(b: DocUtilBoard): void {
  boardModal.value = {
    open: true,
    mode: 'edit',
    editingId: b.id,
    name: b.name,
    description: b.description ?? '',
    error: '',
    submitting: false,
  }
}

function closeBoardModal(): void {
  boardModal.value.open = false
}

async function submitBoardModal(): Promise<void> {
  if (!selectedProjectId.value) return

  const trimmedName = boardModal.value.name.trim()
  if (!trimmedName) {
    boardModal.value.error = t('adminDocutilProjects.nameRequired')
    return
  }
  if (trimmedName.length > 255) {
    boardModal.value.error = t('adminDocutilProjects.nameTooLong')
    return
  }
  if (boardModal.value.description.length > 2000) {
    boardModal.value.error = t('adminDocutilProjects.descriptionTooLong')
    return
  }

  boardModal.value.submitting = true
  boardModal.value.error = ''
  try {
    if (boardModal.value.mode === 'create') {
      await createProjectBoard(selectedProjectId.value, {
        name: trimmedName,
        description: boardModal.value.description.trim() || null,
      })
    } else if (boardModal.value.editingId) {
      const original = boardList.value?.items.find(b => b.id === boardModal.value.editingId)
      const payload: { name?: string; description?: string | null } = {}
      const newDesc = boardModal.value.description.trim()
      if (!original || trimmedName !== original.name) payload.name = trimmedName
      if (!original || newDesc !== (original.description ?? '')) {
        payload.description = newDesc.length > 0 ? newDesc : null
      }
      if (Object.keys(payload).length === 0) {
        boardModal.value.error = t('adminDocutilProjects.noChanges')
        boardModal.value.submitting = false
        return
      }
      await updateProjectBoard(selectedProjectId.value, boardModal.value.editingId, payload)
    }
    boardModal.value.open = false
    await loadBoards(selectedProjectId.value)
    if (activeTab.value === 'tree') {
      tree.value = []
      await loadTree()
    }
  } catch (err: unknown) {
    boardModal.value.error = extractErrorMessage(err)
  } finally {
    boardModal.value.submitting = false
  }
}

async function confirmDeleteBoard(b: DocUtilBoard): Promise<void> {
  if (!selectedProjectId.value) return
  if (!window.confirm(t('adminDocutilProjects.deleteBoardConfirm', { name: b.name }))) return
  if (!window.confirm(t('adminDocutilProjects.deleteBoardConfirmFinal'))) return

  loadingBoards.value = true
  errorMessage.value = ''
  try {
    await deleteProjectBoard(selectedProjectId.value, b.id)
    await loadBoards(selectedProjectId.value)
    if (activeTab.value === 'tree') {
      tree.value = []
      await loadTree()
    }
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingBoards.value = false
  }
}

// ── 유틸 ──────────────────────────────────────────────────────────────────
function formatDate(value: string | null): string {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return value
  }
}

function extractErrorMessage(err: unknown): string {
  // axios 에러: response.data.message — services/api.ts 인터셉터 패턴.
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const resp = (err as { response?: { data?: { message?: string } } }).response
    if (resp?.data?.message) return resp.data.message
  }
  if (err instanceof Error) return err.message
  return t('adminDocutilProjects.errorUnknown')
}

onMounted(() => {
  void loadProjects()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1050;
}

.modal-card {
  width: 90%;
  max-width: 560px;
  max-height: 86vh;
  overflow-y: auto;
}

.list-group-item {
  cursor: pointer;
  transition: background-color 0.15s ease-in-out;
}

.list-group-item:hover {
  background-color: var(--bs-tertiary-bg, rgba(0, 0, 0, 0.04));
}

.list-group-item-active {
  background-color: var(--bs-primary-bg-subtle, #cfe2ff);
}

dl.row dt {
  font-weight: 600;
  color: var(--bs-secondary-color);
}

.nav-pills .nav-link {
  cursor: pointer;
}
</style>
