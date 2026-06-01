<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilDepartments.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilDepartments.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-primary btn-sm"
          @click="refreshAll"
          :disabled="loadingDepts || loadingOrg || loadingQuota"
          :aria-label="t('adminDocutilDepartments.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilDepartments.refresh') }}
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

    <!-- 조직 정보 + 할당량 (상단 카드 2개) -->
    <div class="row g-3 mb-3">
      <div class="col-lg-6">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
              <i class="bi bi-building me-1" aria-hidden="true"></i>
              {{ t('adminDocutilDepartments.organizationInfo') }}
            </h6>
            <button
              v-if="organization && !loadingOrg"
              class="btn btn-sm btn-outline-secondary"
              @click="openEditOrgModal"
              :aria-label="t('adminDocutilDepartments.editOrg')"
            >
              <i class="bi bi-pencil" aria-hidden="true"></i>
              {{ t('adminDocutilDepartments.editOrg') }}
            </button>
          </div>
          <div class="card-body">
            <div v-if="loadingOrg" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <dl v-else-if="organization" class="row mb-0 small">
              <dt class="col-sm-4">{{ t('adminDocutilDepartments.colOrgId') }}</dt>
              <dd class="col-sm-8"><code>{{ organization.id }}</code></dd>
              <dt class="col-sm-4">{{ t('adminDocutilDepartments.colOrgName') }}</dt>
              <dd class="col-sm-8">{{ organization.name }}</dd>
              <dt class="col-sm-4">{{ t('adminDocutilDepartments.colOrgSlug') }}</dt>
              <dd class="col-sm-8"><code>{{ organization.slug }}</code></dd>
              <dt class="col-sm-4">{{ t('adminDocutilDepartments.colOrgDescription') }}</dt>
              <dd class="col-sm-8">
                <span v-if="organization.description">{{ organization.description }}</span>
                <span v-else class="text-muted">-</span>
              </dd>
              <dt class="col-sm-4">{{ t('adminDocutilDepartments.colOrgCreatedAt') }}</dt>
              <dd class="col-sm-8">{{ formatDate(organization.createdAt) }}</dd>
            </dl>
            <p v-else class="text-muted mb-0">{{ t('adminDocutilDepartments.organizationEmpty') }}</p>
          </div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
              <i class="bi bi-speedometer2 me-1" aria-hidden="true"></i>
              {{ t('adminDocutilDepartments.quotaInfo') }}
              <span v-if="quota" class="text-muted small ms-1">{{ quota.yearMonth }}</span>
            </h6>
            <button
              class="btn btn-sm btn-outline-secondary"
              @click="loadQuota"
              :disabled="loadingQuota"
              :aria-label="t('adminDocutilDepartments.refresh')"
            >
              <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
            </button>
          </div>
          <div class="card-body">
            <div v-if="loadingQuota" class="text-center py-3">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="quota && quota.quotas.length > 0">
              <div
                v-for="q in quota.quotas"
                :key="q.quotaType"
                class="mb-3 d-flex align-items-center"
              >
                <div class="flex-grow-1">
                  <div class="d-flex justify-content-between align-items-center small mb-1">
                    <strong>{{ q.quotaType }}</strong>
                    <span class="text-muted">
                      {{ q.usedCount }} / {{ q.monthlyLimit }}
                      <small>({{ t('adminDocutilDepartments.remaining') }} {{ q.remaining }})</small>
                    </span>
                  </div>
                  <div class="progress" style="height: 6px;" :title="`${quotaPercent(q)}%`">
                    <div
                      class="progress-bar"
                      :class="quotaProgressClass(q)"
                      :style="{ width: quotaPercent(q) + '%' }"
                      role="progressbar"
                      :aria-valuenow="q.usedCount"
                      aria-valuemin="0"
                      :aria-valuemax="q.monthlyLimit"
                    ></div>
                  </div>
                </div>
                <button
                  class="btn btn-sm btn-link ms-2"
                  @click="openEditQuotaModal(q)"
                  :aria-label="t('adminDocutilDepartments.editQuota')"
                >
                  <i class="bi bi-pencil-square" aria-hidden="true"></i>
                </button>
              </div>
            </div>
            <p v-else class="text-muted mb-0">{{ t('adminDocutilDepartments.quotaEmpty') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 부서 트리 + 상세 패널 (좌우 분할) -->
    <div class="row g-3">
      <!-- 좌측: 부서 트리 -->
      <div class="col-lg-5">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
              <i class="bi bi-diagram-3 me-1" aria-hidden="true"></i>
              {{ t('adminDocutilDepartments.departmentsTree') }}
              <span class="text-muted small ms-1" v-if="departments.length > 0">({{ departments.length }})</span>
            </h6>
            <button
              class="btn btn-sm btn-primary"
              @click="openCreateRootDeptModal"
              :disabled="loadingDepts"
              :aria-label="t('adminDocutilDepartments.createRoot')"
            >
              <i class="bi bi-plus-lg" aria-hidden="true"></i>
              {{ t('adminDocutilDepartments.createRoot') }}
            </button>
          </div>
          <div class="card-body p-0">
            <div v-if="loadingDepts" class="text-center py-5">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="departments.length === 0" class="text-center text-muted py-5">
              <i class="bi bi-inbox fs-2 d-block mb-2" aria-hidden="true"></i>
              <p class="mb-0">{{ t('adminDocutilDepartments.empty') }}</p>
            </div>
            <ul v-else class="list-group list-group-flush">
              <li
                v-for="dept in sortedDepartments"
                :key="dept.id"
                class="list-group-item d-flex justify-content-between align-items-center"
                :class="{ 'list-group-item-active': selectedDeptId === dept.id }"
                @click="selectDept(dept.id)"
                role="button"
                :aria-label="dept.name"
              >
                <div class="d-flex align-items-center" :style="{ marginLeft: (dept.depth * 16) + 'px' }">
                  <i
                    class="me-2"
                    :class="dept.depth === 0 ? 'bi bi-folder' : 'bi bi-folder2-open'"
                    aria-hidden="true"
                  ></i>
                  <div>
                    <div class="fw-medium">{{ dept.name }}</div>
                    <small class="text-muted">depth={{ dept.depth }}</small>
                  </div>
                </div>
                <div class="btn-group btn-group-sm" @click.stop>
                  <button
                    class="btn btn-link p-1"
                    @click="openCreateChildDeptModal(dept)"
                    :title="t('adminDocutilDepartments.createChild')"
                    :aria-label="t('adminDocutilDepartments.createChild')"
                  >
                    <i class="bi bi-plus" aria-hidden="true"></i>
                  </button>
                  <button
                    class="btn btn-link p-1"
                    @click="openEditDeptModal(dept)"
                    :title="t('adminDocutilDepartments.edit')"
                    :aria-label="t('adminDocutilDepartments.edit')"
                  >
                    <i class="bi bi-pencil" aria-hidden="true"></i>
                  </button>
                  <button
                    class="btn btn-link p-1 text-danger"
                    @click="confirmDeleteDept(dept)"
                    :title="t('adminDocutilDepartments.delete')"
                    :aria-label="t('adminDocutilDepartments.delete')"
                  >
                    <i class="bi bi-trash" aria-hidden="true"></i>
                  </button>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 우측: 선택 부서 상세 + 멤버 -->
      <div class="col-lg-7">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0">
              <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
              {{ t('adminDocutilDepartments.deptDetail') }}
            </h6>
          </div>
          <div class="card-body">
            <p v-if="!selectedDept" class="text-muted text-center py-4 mb-0">
              {{ t('adminDocutilDepartments.selectPrompt') }}
            </p>
            <div v-else>
              <dl class="row mb-3 small">
                <dt class="col-sm-4">{{ t('adminDocutilDepartments.colDeptId') }}</dt>
                <dd class="col-sm-8"><code>{{ selectedDept.id }}</code></dd>
                <dt class="col-sm-4">{{ t('adminDocutilDepartments.colDeptName') }}</dt>
                <dd class="col-sm-8">{{ selectedDept.name }}</dd>
                <dt class="col-sm-4">{{ t('adminDocutilDepartments.colDeptParent') }}</dt>
                <dd class="col-sm-8">
                  <span v-if="selectedDept.parentId">
                    <code>{{ selectedDept.parentId }}</code>
                    <small v-if="parentName(selectedDept.parentId)" class="text-muted ms-2">
                      ({{ parentName(selectedDept.parentId) }})
                    </small>
                  </span>
                  <span v-else class="text-muted">{{ t('adminDocutilDepartments.rootMark') }}</span>
                </dd>
                <dt class="col-sm-4">{{ t('adminDocutilDepartments.colDeptDepth') }}</dt>
                <dd class="col-sm-8">{{ selectedDept.depth }}</dd>
                <dt class="col-sm-4">{{ t('adminDocutilDepartments.colDeptPath') }}</dt>
                <dd class="col-sm-8"><code>{{ selectedDept.path }}</code></dd>
                <dt class="col-sm-4">{{ t('adminDocutilDepartments.colDeptCreatedAt') }}</dt>
                <dd class="col-sm-8">{{ formatDate(selectedDept.createdAt) }}</dd>
              </dl>

              <div class="d-flex justify-content-between align-items-center border-top pt-3 mb-2">
                <h6 class="mb-0">
                  <i class="bi bi-people me-1" aria-hidden="true"></i>
                  {{ t('adminDocutilDepartments.members') }}
                  <span class="text-muted small ms-1" v-if="members.length > 0">({{ members.length }})</span>
                </h6>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-primary"
                  @click="openAddMemberModal"
                  :aria-label="t('adminDocutilDepartments.addMember')"
                >
                  <i class="bi bi-plus-lg" aria-hidden="true"></i>
                  {{ t('adminDocutilDepartments.addMember') }}
                </button>
              </div>
              <div v-if="loadingMembers" class="text-center py-3">
                <div class="spinner-border spinner-border-sm" role="status">
                  <span class="visually-hidden">{{ t('common.loading') }}</span>
                </div>
              </div>
              <p v-else-if="members.length === 0" class="text-muted small mb-0">
                {{ t('adminDocutilDepartments.membersEmpty') }}
              </p>
              <div v-else class="table-responsive">
                <table class="table table-sm table-hover mb-0">
                  <thead class="table-light">
                    <tr>
                      <th scope="col">{{ t('adminDocutilDepartments.colMemberUsername') }}</th>
                      <th scope="col">{{ t('adminDocutilDepartments.colMemberEmail') }}</th>
                      <th scope="col" style="width: 100px;">{{ t('adminDocutilDepartments.colMemberRole') }}</th>
                      <th scope="col" style="width: 100px;" class="text-end">{{ t('common.actions') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="m in members" :key="m.id">
                      <td>{{ m.username }}</td>
                      <td>{{ m.email }}</td>
                      <td>
                        <span class="badge bg-secondary-subtle text-secondary-emphasis">{{ m.role }}</span>
                      </td>
                      <td class="text-end">
                        <button
                          type="button"
                          class="btn btn-sm btn-link text-danger p-1"
                          @click="confirmRemoveMember(m)"
                          :title="t('adminDocutilDepartments.removeMember')"
                          :aria-label="t('adminDocutilDepartments.removeMember')"
                        >
                          <i class="bi bi-person-dash" aria-hidden="true"></i>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 부서 생성/수정 모달 -->
    <div
      v-if="deptModal.open"
      class="modal-overlay d-flex align-items-center justify-content-center"
      role="dialog"
      :aria-label="deptModal.mode === 'create'
        ? t('adminDocutilDepartments.modalCreateTitle')
        : t('adminDocutilDepartments.modalEditTitle')"
      @click.self="closeDeptModal"
    >
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            {{ deptModal.mode === 'create'
              ? t('adminDocutilDepartments.modalCreateTitle')
              : t('adminDocutilDepartments.modalEditTitle') }}
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeDeptModal"
          ></button>
        </div>
        <form @submit.prevent="submitDeptModal">
          <div class="card-body">
            <div class="mb-3">
              <label for="dept-name" class="form-label small">
                {{ t('adminDocutilDepartments.colDeptName') }}
                <span class="text-danger">*</span>
              </label>
              <input
                id="dept-name"
                type="text"
                class="form-control form-control-sm"
                v-model="deptModal.name"
                maxlength="128"
                required
                :placeholder="t('adminDocutilDepartments.namePlaceholder')"
              />
            </div>
            <div class="mb-3">
              <label for="dept-parent" class="form-label small">
                {{ t('adminDocutilDepartments.colDeptParent') }}
              </label>
              <select
                id="dept-parent"
                class="form-select form-select-sm"
                v-model="deptModal.parentId"
              >
                <option :value="null">{{ t('adminDocutilDepartments.rootOption') }}</option>
                <option
                  v-for="d in selectableParents"
                  :key="d.id"
                  :value="d.id"
                >
                  {{ '— '.repeat(d.depth) }}{{ d.name }}
                </option>
              </select>
              <small v-if="deptModal.mode === 'edit'" class="form-text text-muted">
                {{ t('adminDocutilDepartments.parentEditHint') }}
              </small>
            </div>
            <div v-if="deptModal.error" class="alert alert-danger small mb-0">
              {{ deptModal.error }}
            </div>
          </div>
          <div class="card-footer bg-transparent text-end">
            <button type="button" class="btn btn-sm btn-outline-secondary me-2" @click="closeDeptModal">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="deptModal.submitting">
              <span v-if="deptModal.submitting" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
              {{ deptModal.mode === 'create' ? t('adminDocutilDepartments.create') : t('adminDocutilDepartments.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 조직 정보 수정 모달 -->
    <div
      v-if="orgModal.open"
      class="modal-overlay d-flex align-items-center justify-content-center"
      role="dialog"
      :aria-label="t('adminDocutilDepartments.modalEditOrgTitle')"
      @click.self="closeOrgModal"
    >
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">{{ t('adminDocutilDepartments.modalEditOrgTitle') }}</h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeOrgModal"
          ></button>
        </div>
        <form @submit.prevent="submitOrgModal">
          <div class="card-body">
            <div class="mb-3">
              <label for="org-name" class="form-label small">{{ t('adminDocutilDepartments.colOrgName') }}</label>
              <input
                id="org-name"
                type="text"
                class="form-control form-control-sm"
                v-model="orgModal.name"
                maxlength="128"
              />
            </div>
            <div class="mb-3">
              <label for="org-desc" class="form-label small">{{ t('adminDocutilDepartments.colOrgDescription') }}</label>
              <textarea
                id="org-desc"
                class="form-control form-control-sm"
                v-model="orgModal.description"
                rows="3"
              ></textarea>
            </div>
            <div v-if="orgModal.error" class="alert alert-danger small mb-0">
              {{ orgModal.error }}
            </div>
          </div>
          <div class="card-footer bg-transparent text-end">
            <button type="button" class="btn btn-sm btn-outline-secondary me-2" @click="closeOrgModal">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="orgModal.submitting">
              <span v-if="orgModal.submitting" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
              {{ t('adminDocutilDepartments.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 할당량 한도 수정 모달 -->
    <div
      v-if="quotaModal.open"
      class="modal-overlay d-flex align-items-center justify-content-center"
      role="dialog"
      :aria-label="t('adminDocutilDepartments.modalEditQuotaTitle')"
      @click.self="closeQuotaModal"
    >
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            {{ t('adminDocutilDepartments.modalEditQuotaTitle') }}
            <code class="ms-2 small">{{ quotaModal.quotaType }}</code>
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeQuotaModal"
          ></button>
        </div>
        <form @submit.prevent="submitQuotaModal">
          <div class="card-body">
            <p class="small text-muted mb-3">
              {{ t('adminDocutilDepartments.quotaModalHint') }}
            </p>
            <div class="mb-3">
              <label for="quota-limit" class="form-label small">
                {{ t('adminDocutilDepartments.monthlyLimit') }}
                <span class="text-danger">*</span>
              </label>
              <input
                id="quota-limit"
                type="number"
                class="form-control form-control-sm"
                v-model.number="quotaModal.monthlyLimit"
                min="0"
                step="1"
                required
              />
              <small class="form-text text-muted">
                {{ t('adminDocutilDepartments.quotaUsedCount', {
                  used: quotaModal.usedCount,
                }) }}
              </small>
            </div>
            <div v-if="quotaModal.error" class="alert alert-danger small mb-0">
              {{ quotaModal.error }}
            </div>
          </div>
          <div class="card-footer bg-transparent text-end">
            <button type="button" class="btn btn-sm btn-outline-secondary me-2" @click="closeQuotaModal">
              {{ t('common.cancel') }}
            </button>
            <button type="submit" class="btn btn-sm btn-primary" :disabled="quotaModal.submitting">
              <span v-if="quotaModal.submitting" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
              {{ t('adminDocutilDepartments.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 부서 멤버 추가 모달 (트랙 #101 F8) -->
    <div
      v-if="addMemberModal.open"
      class="modal-overlay d-flex align-items-center justify-content-center"
      role="dialog"
      :aria-label="t('adminDocutilDepartments.modalAddMemberTitle')"
      @click.self="closeAddMemberModal"
    >
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            <i class="bi bi-person-plus me-1" aria-hidden="true"></i>
            {{ t('adminDocutilDepartments.modalAddMemberTitle') }}
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeAddMemberModal"
          ></button>
        </div>
        <form @submit.prevent="submitAddMember">
          <div class="card-body">
            <p class="small text-muted mb-3">
              {{ t('adminDocutilDepartments.addMemberHint') }}
            </p>
            <div class="mb-3">
              <label for="add-member-search" class="form-label small">
                {{ t('adminDocutilDepartments.userSearch') }}
              </label>
              <div class="input-group input-group-sm">
                <input
                  id="add-member-search"
                  type="text"
                  class="form-control"
                  v-model="addMemberModal.searchInput"
                  :placeholder="t('adminDocutilDepartments.userSearchPlaceholder')"
                  @keydown.enter.prevent="searchUsers"
                />
                <button
                  type="button"
                  class="btn btn-outline-primary"
                  @click="searchUsers"
                  :disabled="addMemberModal.searching"
                >
                  <span v-if="addMemberModal.searching" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
                  {{ t('adminDocutilDepartments.userSearchButton') }}
                </button>
              </div>
            </div>
            <div v-if="addMemberModal.results.length > 0" class="mb-3">
              <label class="form-label small">
                {{ t('adminDocutilDepartments.userSearchResults') }}
                <span class="text-muted">({{ addMemberModal.results.length }})</span>
              </label>
              <div class="list-group list-group-flush user-search-results">
                <button
                  v-for="u in addMemberModal.results"
                  :key="u.id"
                  type="button"
                  class="list-group-item list-group-item-action small"
                  :class="{ active: addMemberModal.selectedUserId === u.id }"
                  @click="addMemberModal.selectedUserId = u.id"
                >
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <strong>{{ u.username }}</strong>
                      <span class="text-muted ms-2">{{ u.email }}</span>
                    </div>
                    <span
                      v-if="u.departmentId"
                      class="badge bg-warning-subtle text-warning-emphasis"
                      :title="t('adminDocutilDepartments.userAlreadyInDepartment')"
                    >
                      {{ t('adminDocutilDepartments.userAlreadyInDepartmentBadge') }}
                    </span>
                  </div>
                </button>
              </div>
            </div>
            <p v-else-if="addMemberModal.searched && !addMemberModal.searching" class="small text-muted mb-3">
              {{ t('adminDocutilDepartments.userSearchEmpty') }}
            </p>
            <div v-if="addMemberModal.error" class="alert alert-danger small mb-0">
              {{ addMemberModal.error }}
            </div>
          </div>
          <div class="card-footer bg-transparent text-end">
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary me-2"
              @click="closeAddMemberModal"
              :disabled="addMemberModal.submitting"
            >
              {{ t('common.cancel') }}
            </button>
            <button
              type="submit"
              class="btn btn-sm btn-primary"
              :disabled="addMemberModal.submitting || !addMemberModal.selectedUserId"
            >
              <span v-if="addMemberModal.submitting" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
              {{ t('adminDocutilDepartments.addMemberConfirm') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilDepartments — DocUtil 조직/부서/할당량 운영자 관리 화면 (Phase 10.1b, 2026-05-10).
 *
 * 진입 경로: /admin/docutil-departments (Admin / SuperAdmin 전용)
 *
 * 책임:
 *   1. 조직 정보 카드 — 조회 + 수정 모달
 *   2. 월 할당량 카드 — 진행률 표시 + 한도 수정 모달(quota_type 별)
 *   3. 부서 트리(좌측) + 부서 상세/멤버(우측)
 *      - 평탄 List 응답을 path 정렬 + depth 들여쓰기로 트리화
 *      - 노드 액션: 신규 하위 / 수정 / 삭제, 루트는 별도 버튼
 *      - 모달: 부서 생성 / 부서 수정 (이름 + parent dropdown)
 *
 * 백엔드 BFF: /api/admin/docutil/{organization,departments,...}
 *   - 권한 게이트: [Authorize(Roles="Admin,SuperAdmin")]
 *   - 인증: services/api.ts axios 인터셉터 — JWT 자동 부착, 401 갱신
 *   - 캐시: 백엔드가 10분 TTL + version-key invalidate (mutation 후 자동 갱신).
 *           할당량은 캐시 미적용(매 GET fresh).
 */
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  getOrganization,
  updateOrganization,
  listDepartments,
  createDepartment,
  updateDepartment,
  deleteDepartment,
  getDepartmentMembers,
  getOrganizationQuota,
  updateOrganizationQuota,
  listUsers,
  updateUser,
  type DocUtilOrganization,
  type DocUtilDepartment,
  type DocUtilDepartmentMember,
  type DocUtilOrganizationQuotaCurrent,
  type DocUtilOrganizationQuotaStatus,
  type DocUtilUserSummary,
} from '@/services/docutilService'

const { t } = useI18n()

// ── 상태: 조직 / 부서 / 할당량 ─────────────────────────────────────────────
const organization = ref<DocUtilOrganization | null>(null)
const departments = ref<DocUtilDepartment[]>([])
const members = ref<DocUtilDepartmentMember[]>([])
const quota = ref<DocUtilOrganizationQuotaCurrent | null>(null)

const loadingOrg = ref<boolean>(false)
const loadingDepts = ref<boolean>(false)
const loadingMembers = ref<boolean>(false)
const loadingQuota = ref<boolean>(false)

const errorMessage = ref<string>('')

const selectedDeptId = ref<string | null>(null)

// ── 트리 정렬: path 사전순 → 트리 들여쓰기 효과 ────────────────────────────
const sortedDepartments = computed<DocUtilDepartment[]>(() =>
  [...departments.value].sort((a, b) => a.path.localeCompare(b.path))
)

// 모달 dropdown — 자기 자신과 자기 자손은 제외(순환 부모 방지).
const selectableParents = computed<DocUtilDepartment[]>(() => {
  const editingId = deptModal.value.editingId
  if (!editingId) {
    return sortedDepartments.value
  }
  // 편집 모드: editingId 의 path 로 시작하는 노드(자손)는 제외.
  const editing = departments.value.find(d => d.id === editingId)
  if (!editing) return sortedDepartments.value
  return sortedDepartments.value.filter(d => !d.path.startsWith(editing.path))
})

const selectedDept = computed<DocUtilDepartment | null>(() =>
  selectedDeptId.value
    ? departments.value.find(d => d.id === selectedDeptId.value) ?? null
    : null
)

function parentName(parentId: string): string | null {
  const p = departments.value.find(d => d.id === parentId)
  return p?.name ?? null
}

// ── 데이터 로드 ───────────────────────────────────────────────────────────
async function loadOrganization(): Promise<void> {
  loadingOrg.value = true
  errorMessage.value = ''
  try {
    organization.value = await getOrganization()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingOrg.value = false
  }
}

async function loadDepartments(): Promise<void> {
  loadingDepts.value = true
  errorMessage.value = ''
  try {
    departments.value = await listDepartments()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingDepts.value = false
  }
}

async function loadMembers(deptId: string): Promise<void> {
  loadingMembers.value = true
  errorMessage.value = ''
  try {
    members.value = await getDepartmentMembers(deptId)
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingMembers.value = false
  }
}

async function loadQuota(): Promise<void> {
  loadingQuota.value = true
  errorMessage.value = ''
  try {
    quota.value = await getOrganizationQuota()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingQuota.value = false
  }
}

async function refreshAll(): Promise<void> {
  await Promise.all([loadOrganization(), loadDepartments(), loadQuota()])
  if (selectedDeptId.value) {
    await loadMembers(selectedDeptId.value)
  }
}

function selectDept(deptId: string): void {
  selectedDeptId.value = deptId
  members.value = []
  void loadMembers(deptId)
}

// ── 부서 모달 ─────────────────────────────────────────────────────────────
interface DeptModalState {
  open: boolean
  mode: 'create' | 'edit'
  editingId: string | null
  name: string
  parentId: string | null
  error: string
  submitting: boolean
}

const deptModal = ref<DeptModalState>({
  open: false,
  mode: 'create',
  editingId: null,
  name: '',
  parentId: null,
  error: '',
  submitting: false,
})

function openCreateRootDeptModal(): void {
  deptModal.value = {
    open: true,
    mode: 'create',
    editingId: null,
    name: '',
    parentId: null,
    error: '',
    submitting: false,
  }
}

function openCreateChildDeptModal(parent: DocUtilDepartment): void {
  deptModal.value = {
    open: true,
    mode: 'create',
    editingId: null,
    name: '',
    parentId: parent.id,
    error: '',
    submitting: false,
  }
}

function openEditDeptModal(dept: DocUtilDepartment): void {
  deptModal.value = {
    open: true,
    mode: 'edit',
    editingId: dept.id,
    name: dept.name,
    parentId: dept.parentId,
    error: '',
    submitting: false,
  }
}

function closeDeptModal(): void {
  deptModal.value.open = false
}

async function submitDeptModal(): Promise<void> {
  if (!deptModal.value.name.trim()) {
    deptModal.value.error = t('adminDocutilDepartments.nameRequired')
    return
  }
  deptModal.value.submitting = true
  deptModal.value.error = ''
  try {
    if (deptModal.value.mode === 'create') {
      await createDepartment({
        name: deptModal.value.name.trim(),
        parentId: deptModal.value.parentId,
      })
    } else if (deptModal.value.editingId) {
      await updateDepartment(deptModal.value.editingId, {
        name: deptModal.value.name.trim(),
        parentId: deptModal.value.parentId,
      })
    }
    deptModal.value.open = false
    await loadDepartments()
  } catch (err: unknown) {
    deptModal.value.error = extractErrorMessage(err)
  } finally {
    deptModal.value.submitting = false
  }
}

async function confirmDeleteDept(dept: DocUtilDepartment): Promise<void> {
  // 1차 확인
  const message = t('adminDocutilDepartments.deleteConfirm', { name: dept.name })
  if (!window.confirm(message)) return
  // 2차 확인(영구 삭제 경고)
  if (!window.confirm(t('adminDocutilDepartments.deleteConfirmFinal'))) return

  loadingDepts.value = true
  errorMessage.value = ''
  try {
    await deleteDepartment(dept.id)
    if (selectedDeptId.value === dept.id) {
      selectedDeptId.value = null
      members.value = []
    }
    await loadDepartments()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingDepts.value = false
  }
}

// ── 조직 정보 모달 ────────────────────────────────────────────────────────
interface OrgModalState {
  open: boolean
  name: string
  description: string
  error: string
  submitting: boolean
}

const orgModal = ref<OrgModalState>({
  open: false,
  name: '',
  description: '',
  error: '',
  submitting: false,
})

function openEditOrgModal(): void {
  if (!organization.value) return
  orgModal.value = {
    open: true,
    name: organization.value.name,
    description: organization.value.description ?? '',
    error: '',
    submitting: false,
  }
}

function closeOrgModal(): void {
  orgModal.value.open = false
}

async function submitOrgModal(): Promise<void> {
  if (!organization.value) return

  // 변경사항 차이 — 빈 문자열을 null 로 변환하여 partial update.
  const payload: { name?: string; description?: string | null } = {}
  if (orgModal.value.name && orgModal.value.name !== organization.value.name) {
    payload.name = orgModal.value.name
  }
  const newDesc = orgModal.value.description.trim()
  const oldDesc = organization.value.description ?? ''
  if (newDesc !== oldDesc) {
    payload.description = newDesc.length > 0 ? newDesc : null
  }

  if (Object.keys(payload).length === 0) {
    orgModal.value.error = t('adminDocutilDepartments.orgNoChanges')
    return
  }

  orgModal.value.submitting = true
  orgModal.value.error = ''
  try {
    organization.value = await updateOrganization(payload)
    orgModal.value.open = false
  } catch (err: unknown) {
    orgModal.value.error = extractErrorMessage(err)
  } finally {
    orgModal.value.submitting = false
  }
}

// ── 할당량 모달 ───────────────────────────────────────────────────────────
interface QuotaModalState {
  open: boolean
  quotaType: string
  monthlyLimit: number
  usedCount: number
  error: string
  submitting: boolean
}

const quotaModal = ref<QuotaModalState>({
  open: false,
  quotaType: '',
  monthlyLimit: 0,
  usedCount: 0,
  error: '',
  submitting: false,
})

function openEditQuotaModal(q: DocUtilOrganizationQuotaStatus): void {
  quotaModal.value = {
    open: true,
    quotaType: q.quotaType,
    monthlyLimit: q.monthlyLimit,
    usedCount: q.usedCount,
    error: '',
    submitting: false,
  }
}

function closeQuotaModal(): void {
  quotaModal.value.open = false
}

async function submitQuotaModal(): Promise<void> {
  if (quotaModal.value.monthlyLimit < 0 || !Number.isInteger(quotaModal.value.monthlyLimit)) {
    quotaModal.value.error = t('adminDocutilDepartments.quotaInvalid')
    return
  }

  quotaModal.value.submitting = true
  quotaModal.value.error = ''
  try {
    await updateOrganizationQuota(quotaModal.value.quotaType, {
      monthlyLimit: quotaModal.value.monthlyLimit,
    })
    quotaModal.value.open = false
    await loadQuota()
  } catch (err: unknown) {
    quotaModal.value.error = extractErrorMessage(err)
  } finally {
    quotaModal.value.submitting = false
  }
}

// ── 트랙 #101 F8: 부서 멤버 추가/제거 ───────────────────────────────────
// 모델: DocUtil 측 부서 멤버십은 user.department_id 단일 FK 매핑이므로
//       "추가" = updateUser({ departmentId: <현재 부서 id> })
//       "제거" = updateUser({ departmentId: "" })  (빈 문자열 → 백엔드 → DocUtil null 매핑)
interface AddMemberModalState {
  open: boolean
  searchInput: string
  results: DocUtilUserSummary[]
  selectedUserId: string | null
  searched: boolean
  searching: boolean
  submitting: boolean
  error: string
}

const addMemberModal = ref<AddMemberModalState>({
  open: false,
  searchInput: '',
  results: [],
  selectedUserId: null,
  searched: false,
  searching: false,
  submitting: false,
  error: '',
})

function openAddMemberModal(): void {
  if (!selectedDeptId.value) return
  addMemberModal.value = {
    open: true,
    searchInput: '',
    results: [],
    selectedUserId: null,
    searched: false,
    searching: false,
    submitting: false,
    error: '',
  }
}

function closeAddMemberModal(): void {
  addMemberModal.value.open = false
}

async function searchUsers(): Promise<void> {
  const q = addMemberModal.value.searchInput.trim()
  // 빈 검색은 전체 사용자 첫 50명을 로드 (DocUtil 기본 페이지 사이즈 한도 내).
  addMemberModal.value.searching = true
  addMemberModal.value.error = ''
  try {
    const data = await listUsers(1, 50, q || undefined)
    addMemberModal.value.results = data.items
    addMemberModal.value.searched = true
    // 검색 결과 중 첫 항목 자동 선택 (UX — 단건 결과 시 즉시 확정 가능).
    if (data.items.length > 0) {
      addMemberModal.value.selectedUserId = data.items[0].id
    } else {
      addMemberModal.value.selectedUserId = null
    }
  } catch (err: unknown) {
    addMemberModal.value.error = extractErrorMessage(err)
  } finally {
    addMemberModal.value.searching = false
  }
}

async function submitAddMember(): Promise<void> {
  if (!selectedDeptId.value || !addMemberModal.value.selectedUserId) return

  addMemberModal.value.submitting = true
  addMemberModal.value.error = ''
  try {
    await updateUser(addMemberModal.value.selectedUserId, {
      departmentId: selectedDeptId.value,
    })
    addMemberModal.value.open = false
    // 멤버 list 새로고침.
    await loadMembers(selectedDeptId.value)
  } catch (err: unknown) {
    addMemberModal.value.error = extractErrorMessage(err)
  } finally {
    addMemberModal.value.submitting = false
  }
}

async function confirmRemoveMember(member: DocUtilDepartmentMember): Promise<void> {
  if (!selectedDeptId.value) return
  const message = t('adminDocutilDepartments.removeMemberConfirm', { username: member.username })
  if (!window.confirm(message)) return

  loadingMembers.value = true
  errorMessage.value = ''
  try {
    // 빈 문자열 = 부서 해제 의도 (백엔드가 DocUtil null 로 매핑).
    await updateUser(member.id, { departmentId: '' })
    await loadMembers(selectedDeptId.value)
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingMembers.value = false
  }
}

// ── 표시 헬퍼 ─────────────────────────────────────────────────────────────
function quotaPercent(q: DocUtilOrganizationQuotaStatus): number {
  if (!q.monthlyLimit || q.monthlyLimit <= 0) return 0
  return Math.min(100, Math.round((q.usedCount / q.monthlyLimit) * 100))
}

function quotaProgressClass(q: DocUtilOrganizationQuotaStatus): string {
  const pct = quotaPercent(q)
  if (pct >= 90) return 'bg-danger'
  if (pct >= 70) return 'bg-warning'
  return 'bg-success'
}

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
  return t('adminDocutilDepartments.errorUnknown')
}

onMounted(() => {
  void refreshAll()
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

/* 트랙 #151 (2026-06-01): active 일 때는 hover 회색이 우선되지 않도록 :not(.active) 한정.
   원인: Vue scoped style 이 Bootstrap CSS 보다 늦게 cascade 되어 동일 specificity 의
   `.list-group-item:hover` 가 `.list-group-item.active` 의 파란 배경을 가렸음.
   결과: 사용자가 행 클릭 후 호버 해제 시 active 배경이 안 보이는 결함. */
.list-group-item:not(.active):hover {
  background-color: var(--bs-tertiary-bg, rgba(0, 0, 0, 0.04));
}

.list-group-item-active {
  background-color: var(--bs-primary-bg-subtle, #cfe2ff);
}

dl.row dt {
  font-weight: 600;
  color: var(--bs-secondary-color);
}

.user-search-results {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid var(--bs-border-color, #dee2e6);
  border-radius: 0.25rem;
}
</style>
