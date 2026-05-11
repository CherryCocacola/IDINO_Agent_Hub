<template>
  <div class="d-flex vh-100" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 왼쪽 사이드바 -->
    <aside class="sidebar app-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <router-link to="/" class="sidebar-brand">
          <i class="bi bi-robot"></i>
          <span v-if="!sidebarCollapsed">{{ $t('common.appName') }}</span>
        </router-link>
        <button class="btn btn-link sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
          <i class="bi" :class="sidebarCollapsed ? 'bi-chevron-right' : 'bi-chevron-left'"></i>
        </button>
      </div>
      
      <nav class="sidebar-nav">
        <div 
          v-for="category in menuCategories" 
          :key="category.id"
          class="menu-category"
        >
          <div 
            class="menu-category-header"
            @click="toggleCategory(category.id)"
            v-if="!sidebarCollapsed"
          >
            <i :class="category.icon"></i>
            <span>{{ category.name }}</span>
            <i class="bi ms-auto" :class="expandedCategories[category.id] ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
          </div>
          <div 
            v-else
            class="menu-category-header-collapsed"
            :title="category.name"
            @click="toggleCategory(category.id)"
          >
            <i :class="category.icon"></i>
          </div>
          
          <ul
            v-if="expandedCategories[category.id] || sidebarCollapsed"
            class="menu-items"
          >
            <li
              v-for="item in category.items"
              :key="item.path"
              class="menu-item"
            >
              <!-- 준비중 메뉴 -->
              <span
                v-if="item.comingSoon"
                class="menu-link menu-link-disabled"
                :title="sidebarCollapsed ? item.name + ' (준비중)' : '준비중입니다'"
              >
                <i :class="item.icon"></i>
                <span v-if="!sidebarCollapsed">{{ item.name }}<span class="badge-coming-soon">준비중</span></span>
              </span>
              <!-- 일반 메뉴 -->
              <router-link
                v-else
                :to="item.path"
                class="menu-link"
                :class="{ active: isActiveRoute(item.path) }"
                :title="sidebarCollapsed ? item.name : ''"
              >
                <i :class="item.icon"></i>
                <span v-if="!sidebarCollapsed">{{ item.name }}</span>
              </router-link>
            </li>
          </ul>
        </div>
      </nav>
    </aside>

    <!-- 메인 컨텐츠 영역 -->
    <div class="main-content app-main-content flex-grow-1 d-flex flex-column">
      <!-- 상단 헤더 -->
      <header class="top-header app-top-header">
        <div class="d-flex justify-content-between align-items-center w-100">
          <div class="d-flex align-items-center">
            <button class="btn btn-link d-lg-none" @click="mobileSidebarOpen = !mobileSidebarOpen">
              <i class="bi bi-list"></i>
            </button>
            <h5 class="mb-0 ms-3">{{ currentPageTitle }}</h5>
          </div>
          <div class="topbar-right">
            <!--
            <button class="topbar-btn" title="알림">
              <i class="bi bi-bell"></i>
              <span class="badge-dot"></span>
            </button>
            -->
            <div class="dropdown">
              <button class="topbar-btn" type="button" data-bs-toggle="dropdown" title="언어">
                <i class="bi bi-globe"></i>
              </button>
              <ul class="dropdown-menu dropdown-menu-end">
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="changeLanguage('ko')">
                    <i class="bi bi-check me-2" v-if="currentLanguage === 'ko'"></i>
                    <span class="me-2" v-else></span>{{ $t('chat.korean') }}
                  </a>
                </li>
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="changeLanguage('en')">
                    <i class="bi bi-check me-2" v-if="currentLanguage === 'en'"></i>
                    <span class="me-2" v-else></span>{{ $t('chat.english') }}
                  </a>
                </li>
              </ul>
            </div>
            <div class="topbar-divider"></div>
            <div class="dropdown">
              <button type="button" class="topbar-user topbar-user-btn" data-bs-toggle="dropdown">
                <div class="user-avatar">
                  <i class="bi bi-person"></i>
                </div>
                <div class="user-info">
                  <span class="user-name">{{ authStore.user?.fullName || $t('nav.user') }}</span>
                  <span class="user-role">{{ formatRole(authStore.user?.roles?.[0]) }}</span>
                </div>
                <i class="bi bi-chevron-down topbar-user-chevron"></i>
              </button>
              <ul class="dropdown-menu dropdown-menu-end">
                <li>
                  <router-link to="/settings" class="dropdown-item">
                    <i class="bi bi-gear me-2"></i>{{ $t('nav.settings') }}
                  </router-link>
                </li>
                <li><hr class="dropdown-divider"></li>
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="handleLogout">
                    <i class="bi bi-box-arrow-right me-2"></i>{{ $t('nav.logout') }}
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </header>

      <!-- 메인 컨텐츠 -->
      <main class="flex-grow-1 overflow-auto p-4" :class="{ 'main-content-compact': isCompactPage, 'main-content-full': isFullPage }">
        <router-view />
      </main>
    </div>

    <!-- 모바일 사이드바 오버레이 -->
    <div 
      v-if="mobileSidebarOpen" 
      class="mobile-sidebar-overlay"
      @click="mobileSidebarOpen = false"
    ></div>
    
    <!-- 모바일 사이드바 -->
    <aside class="mobile-sidebar app-sidebar" :class="{ open: mobileSidebarOpen }">
      <div class="sidebar-header">
        <router-link to="/" class="sidebar-brand" @click="mobileSidebarOpen = false">
          <i class="bi bi-robot"></i>
          <span>{{ $t('common.appName') }}</span>
        </router-link>
        <button class="btn btn-link sidebar-toggle" @click="mobileSidebarOpen = false">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
      
      <nav class="sidebar-nav">
        <div 
          v-for="category in menuCategories" 
          :key="category.id"
          class="menu-category"
        >
          <div 
            class="menu-category-header"
            @click="toggleCategory(category.id)"
          >
            <i :class="category.icon"></i>
            <span>{{ category.name }}</span>
            <i class="bi ms-auto" :class="expandedCategories[category.id] ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
          </div>
          
          <ul
            v-if="expandedCategories[category.id]"
            class="menu-items"
          >
            <li
              v-for="item in category.items"
              :key="item.path"
              class="menu-item"
            >
              <!-- 준비중 메뉴 -->
              <span
                v-if="item.comingSoon"
                class="menu-link menu-link-disabled"
                title="준비중입니다"
              >
                <i :class="item.icon"></i>
                <span>{{ item.name }}<span class="badge-coming-soon">준비중</span></span>
              </span>
              <!-- 일반 메뉴 -->
              <router-link
                v-else
                :to="item.path"
                class="menu-link"
                :class="{ active: isActiveRoute(item.path) }"
                @click="mobileSidebarOpen = false"
              >
                <i :class="item.icon"></i>
                <span>{{ item.name }}</span>
              </router-link>
            </li>
          </ul>
        </div>
      </nav>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import { safeSetLocalStorage } from '@/utils/storage'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { locale, t } = useI18n()

const sidebarCollapsed = ref(false)
const mobileSidebarOpen = ref(false)
const expandedCategories = ref<Record<string, boolean>>({
  dashboard: true,
  aiServices: true,
  management: false,
  analytics: false,
  system: false,
  docutil: false,
  admin: false,
  settings: false
})

interface MenuItem {
  name: string
  path: string
  icon: string
  roles?: string[]  // undefined = 모든 역할 허용
  comingSoon?: boolean
}

interface MenuCategory {
  id: string
  name: string
  icon: string
  items: MenuItem[]
  roles?: string[]  // undefined = 모든 역할 허용
}

const hasRole = (roles?: string[]): boolean => {
  if (!roles || roles.length === 0) return true
  const userRoles = authStore.user?.roles?.map(r => r.toLowerCase()) ?? []
  return roles.some(r => userRoles.includes(r.toLowerCase()))
}

const allMenuCategories = computed<MenuCategory[]>(() => [
  {
    id: 'dashboard',
    name: t('nav.categories.dashboard'),
    icon: 'bi bi-speedometer2',
    items: [
      {
        name: t('nav.dashboard'),
        path: '/',
        icon: 'bi bi-house'
      }
    ]
  },
  {
    id: 'aiServices',
    name: t('nav.categories.aiServices'),
    icon: 'bi bi-robot',
    items: [
      {
        name: t('nav.agents'),
        path: '/agents',
        icon: 'bi bi-robot'
      },
      {
        name: t('nav.multiChat'),
        path: '/agents/multi-chat',
        icon: 'bi bi-chat-dots'
      },
      {
        name: t('nav.imageGeneration'),
        path: '/image-generation',
        icon: 'bi bi-image'
      },
      {
        name: t('nav.quickImageGeneration'),
        path: '/quick-image',
        icon: 'bi bi-image-fill'
      },
      {
        name: t('nav.presentationBuilder'),
        path: '/presentation-builder',
        icon: 'bi bi-file-earmark-slides'
      }
    ]
  },
  // Phase 5: management 카테고리는 모든 항목이 Admin 전용이므로 admin 으로 통합 이동 → 카테고리 자체 제거
  // Phase 5: analytics 카테고리는 모든 항목이 Admin 전용이므로 admin 으로 통합 이동 → 카테고리 자체 제거
  // Phase 5: system 카테고리는 모든 항목이 admin 으로 이동 + Phase 2 자체 KB drop 잔재(/knowledge-base) 메뉴 제거 → 카테고리 자체 제거
  //         (라우트는 후속 트랙 C-1 에서 일괄 제거. SPA fallback 유지로 북마크 호환)
  // Phase 10.1a (2026-05-10): DocUtil 운영 카테고리 신설 — Admin/SuperAdmin 전용.
  //   본 트랙(10.1a)에서 사용자 1개 항목 + Phase 10.1b 부서/할당량 항목 추가. 후속 10.1c(프로젝트)
  //   트랙에서 같은 카테고리에 항목이 추가됨.
  {
    id: 'docutil',
    name: t('nav.categories.docutil'),
    icon: 'bi bi-database',
    roles: ['Admin', 'SuperAdmin'],
    items: [
      {
        name: t('nav.docutilUsers'),
        path: '/admin/docutil-users',
        icon: 'bi bi-people',
        roles: ['Admin', 'SuperAdmin']
      },
      {
        name: t('nav.docutilDepartments'),
        path: '/admin/docutil-departments',
        icon: 'bi bi-diagram-3',
        roles: ['Admin', 'SuperAdmin']
      },
      {
        name: t('nav.docutilProjects'),
        path: '/admin/docutil-projects',
        icon: 'bi bi-folder2-open',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2a (2026-05-10): DocUtil 대시보드 + 감사 로그 — 운영 모니터링.
      {
        name: t('nav.docutilDashboard'),
        path: '/admin/docutil-dashboard',
        icon: 'bi bi-speedometer2',
        roles: ['Admin', 'SuperAdmin']
      },
      {
        name: t('nav.docutilAudit'),
        path: '/admin/docutil-audit',
        icon: 'bi bi-journal-text',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2b (2026-05-10): DocUtil 검색범위 + 평가 — RAG 품질 운영.
      {
        name: t('nav.docutilSearchScopes'),
        path: '/admin/docutil-search-scopes',
        icon: 'bi bi-bullseye',
        roles: ['Admin', 'SuperAdmin']
      },
      {
        name: t('nav.docutilEvaluation'),
        path: '/admin/docutil-evaluation',
        icon: 'bi bi-clipboard-check',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2c (2026-05-11): DocUtil FAQ + 보고서 — 콘텐츠/산출물 운영.
      {
        name: t('nav.docutilFaq'),
        path: '/admin/docutil-faq',
        icon: 'bi bi-question-circle',
        roles: ['Admin', 'SuperAdmin']
      },
      {
        name: t('nav.docutilReports'),
        path: '/admin/docutil-reports',
        icon: 'bi bi-file-earmark-text',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2d (2026-05-11): DocUtil 문서 템플릿(Jinja2) — 문서 생성용 템플릿 운영.
      {
        name: t('nav.docutilTemplates'),
        path: '/admin/docutil-templates',
        icon: 'bi bi-file-earmark-code',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2e (2026-05-11): DocUtil LLM API Key — 외부 프로바이더 키 등록/회수/검증.
      {
        name: t('nav.docutilApiKeys'),
        path: '/admin/docutil-api-keys',
        icon: 'bi bi-key',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2e (2026-05-11): DocUtil 자체 에이전트(챗봇용 페르소나) — AgentHub Agent 와 별개.
      {
        name: t('nav.docutilDocAgents'),
        path: '/admin/docutil-doc-agents',
        icon: 'bi bi-robot',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 10.2e (2026-05-11): DocUtil 문서 V2(디자이너 워크플로) — 보고서 템플릿의 후속.
      {
        name: t('nav.docutilDocumentsV2'),
        path: '/admin/docutil-documents-v2',
        icon: 'bi bi-easel2',
        roles: ['Admin', 'SuperAdmin']
      }
    ]
  },
  {
    id: 'admin',
    name: t('nav.categories.admin'),
    icon: 'bi bi-shield-lock',
    roles: ['Admin', 'SuperAdmin'],
    items: [
      // Phase 6.3 운영자 KB 콘솔 (DocUtil BFF) - Admin/SuperAdmin 전용
      {
        name: t('nav.adminKnowledgeBase'),
        path: '/admin/knowledge-base',
        icon: 'bi bi-book-half',
        roles: ['Admin', 'SuperAdmin']
      },
      // Phase 4 RAG 메트릭 대시보드 (`/api/admin/metrics/rag`) - Admin/SuperAdmin 전용
      {
        name: t('nav.adminRagMetrics'),
        path: '/admin/rag-metrics',
        icon: 'bi bi-graph-up-arrow',
        roles: ['Admin', 'SuperAdmin']
      },
      // 기존 management 에서 이동
      {
        name: t('nav.users'),
        path: '/users',
        icon: 'bi bi-people',
        roles: ['Admin']
      },
      {
        name: t('nav.team'),
        path: '/team',
        icon: 'bi bi-people-fill',
        roles: ['Admin']
      },
      {
        name: t('nav.quota'),
        path: '/quota',
        icon: 'bi bi-bar-chart',
        roles: ['Admin']
      },
      {
        name: t('nav.apiKeys'),
        path: '/api-keys',
        icon: 'bi bi-key',
        roles: ['Admin']
      },
      {
        name: t('nav.bannedWords'),
        path: '/banned-words',
        icon: 'bi bi-shield-exclamation',
        roles: ['Admin']
      },
      {
        name: t('nav.piiProtection'),
        path: '/pii-protection',
        icon: 'bi bi-shield-lock',
        roles: ['Admin']
      },
      // 기존 analytics 에서 이동
      {
        name: t('nav.analytics'),
        path: '/analytics',
        icon: 'bi bi-graph-up-arrow',
        roles: ['Admin']
      },
      {
        name: t('nav.auditLog'),
        path: '/audit-log',
        icon: 'bi bi-journal-text',
        roles: ['Admin']
      },
      {
        name: t('nav.costAnalysis'),
        path: '/cost-analysis',
        icon: 'bi bi-currency-dollar',
        roles: ['Admin']
      },
      {
        name: t('nav.usageHistory'),
        path: '/usage-history',
        icon: 'bi bi-clock-history',
        roles: ['Admin']
      },
      // 기존 system 에서 이동
      {
        name: t('nav.systemHealth'),
        path: '/system-health',
        icon: 'bi bi-heart-pulse',
        roles: ['Admin']
      },
      {
        name: t('nav.presentationTemplateManagement'),
        path: '/presentation-templates',
        icon: 'bi bi-file-earmark-slides',
        roles: ['Admin']
      }
    ]
  },
  {
    id: 'settings',
    name: t('nav.categories.settings'),
    icon: 'bi bi-sliders',
    items: [
      {
        name: t('nav.settings'),
        path: '/settings',
        icon: 'bi bi-gear'
      },
      {
        name: t('nav.help'),
        path: '/help',
        icon: 'bi bi-question-circle'
      }
    ]
  }
])

// 역할 기반 필터링된 메뉴
const menuCategories = computed<MenuCategory[]>(() =>
  allMenuCategories.value
    .filter(cat => hasRole(cat.roles))
    .map(cat => ({
      ...cat,
      items: cat.items.filter(item => hasRole(item.roles))
    }))
    .filter(cat => cat.items.length > 0)
)

const isCompactPage = computed(() => {
  const compactPaths = ['/presentation-templates', '/project-todos']
  return compactPaths.some(p => route.path === p || route.path.startsWith(p + '/'))
})

const isFullPage = computed(() => {
  return route.path === '/agents/multi-chat' || route.path.startsWith('/agents/multi-chat/')
})

const currentPageTitle = computed(() => {
  const currentPath = route.path
  for (const category of menuCategories.value) {
    for (const item of category.items) {
      if (item.path === currentPath || currentPath.startsWith(item.path + '/')) {
        return item.name
      }
    }
  }
  return t('common.appName')
})

const isActiveRoute = (path: string): boolean => {
  if (path === '/') {
    return route.path === '/'
  }
  // /agents는 Agent 선택 페이지만 active, 멀티 채팅(/agents/multi-chat) 등 하위 경로와 분리
  if (path === '/agents') {
    return route.path === '/agents'
  }
  return route.path.startsWith(path)
}

const toggleCategory = (categoryId: string) => {
  expandedCategories.value[categoryId] = !expandedCategories.value[categoryId]
}

const currentLanguage = computed(() => locale.value)
const currentLanguageName = computed(() => {
  return locale.value === 'ko' ? '한국어' : 'English'
})

const changeLanguage = (lang: 'ko' | 'en') => {
  locale.value = lang
  safeSetLocalStorage('i18n_locale', lang)
}

// 현재 경로에 따라 카테고리 자동 확장
watch(() => route.path, (newPath) => {
  for (const category of menuCategories.value) {
    for (const item of category.items) {
      if (newPath.startsWith(item.path) || (item.path === '/' && newPath === '/')) {
        expandedCategories.value[category.id] = true
        break
      }
    }
  }
}, { immediate: true })

onMounted(async () => {
  try {
    if (authStore.isAuthenticated && !authStore.user) {
      await authStore.loadUser()
    }
  } catch (error) {
    console.error('Error loading user:', error)
    if (error && typeof error === 'object' && 'response' in error) {
      const httpError = error as { response?: { status?: number } }
      if (httpError.response?.status === 401) {
        await authStore.logout()
        router.push('/login')
      }
    }
  }
})

function formatRole(role: string | undefined): string {
  if (!role) return 'User'
  const map: Record<string, string> = {
    admin: 'Admin',
    superadmin: 'Super Admin',
    developer: 'Developer',
    user: 'User'
  }
  return map[role.toLowerCase()] || role.charAt(0).toUpperCase() + role.slice(1).toLowerCase()
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
/* 시스템 사이드바 - AI Manager 테마 (딥 퍼플 + 액센트 블루) */
.sidebar {
  width: 280px;
  height: 100vh;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-header-border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  transition: width 0.3s ease;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 70px;
}

/* 사이드바가 접혔을 때 메인 컨텐츠 영역 조정 */
.sidebar-collapsed .main-content {
  margin-left: 70px;
  width: calc(100% - 70px);
}

.sidebar-header {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--sidebar-header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--sidebar-bg);
  min-height: 70px;
}

.sidebar-brand {
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 1.15rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: color 0.2s ease, opacity 0.2s ease;
}

.sidebar-brand i {
  font-size: 1.5rem;
  color: var(--accent-blue);
}

.sidebar-brand:hover {
  color: var(--sidebar-text);
  opacity: 0.9;
}

.sidebar-toggle {
  color: var(--sidebar-text-inactive);
  padding: 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.sidebar-toggle:hover {
  color: var(--sidebar-text);
  background: rgba(255, 255, 255, 0.08);
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.75rem 0;
  background: var(--sidebar-bg);
}

.menu-category {
  margin-bottom: 0.25rem;
}

.menu-category-header {
  padding: 0.625rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--sidebar-text-inactive);
  font-weight: 600;
  font-size: 0.875rem;
  border-radius: 0;
}

.menu-category-header:hover {
  background-color: rgba(255, 255, 255, 0.06);
  color: var(--sidebar-text);
}

.menu-category-header i {
  font-size: 1.1rem;
  color: var(--sidebar-text-inactive);
  width: 20px;
  text-align: center;
}

.menu-category-header-collapsed {
  padding: 0.75rem;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--sidebar-text-inactive);
  border-radius: var(--radius-lg);
  margin: 0.25rem 0.5rem;
}

.menu-category-header-collapsed:hover {
  background-color: rgba(255, 255, 255, 0.06);
  color: var(--sidebar-text);
}

.menu-category-header-collapsed i {
  font-size: 1.25rem;
  color: var(--sidebar-text-inactive);
}

.menu-items {
  list-style: none;
  padding: 0;
  margin: 0;
  background-color: transparent;
}

.menu-item {
  margin: 0;
}

.menu-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem 0.625rem 2.75rem;
  color: var(--sidebar-text-inactive);
  text-decoration: none;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 500;
}

.menu-link:hover {
  background-color: rgba(255, 255, 255, 0.06);
  color: var(--sidebar-text);
  border-left-color: var(--accent-blue);
}

.menu-link.active {
  background-color: var(--accent-blue);
  color: var(--sidebar-text);
  border-left-color: var(--accent-blue);
  font-weight: 600;
}

.menu-link i {
  font-size: 1rem;
  width: 18px;
  text-align: center;
}

.menu-link-disabled {
  opacity: 0.45;
  cursor: not-allowed;
  pointer-events: none;
}

.badge-coming-soon {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  font-size: 0.65rem;
  font-weight: 600;
  border-radius: 10px;
  background: rgba(255, 193, 7, 0.25);
  color: #ffc107;
  vertical-align: middle;
  letter-spacing: 0.02em;
}

.sidebar.collapsed .menu-link {
  padding: 0.75rem;
  justify-content: center;
  border-left: none;
  border-radius: 8px;
  margin: 0.25rem 0.5rem;
  width: calc(100% - 1rem);
}

.sidebar.collapsed .menu-link span {
  display: none;
}

.sidebar.collapsed .menu-link.active {
  background-color: var(--accent-blue);
}

.main-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--main-bg);
  margin-left: 280px;
  width: calc(100% - 280px);
  transition: margin-left 0.3s ease, width 0.3s ease;
}

.top-header {
  background: var(--main-bg);
  border-bottom: 1px solid var(--border-light);
  padding: 1rem 1.5rem;
  box-shadow: var(--shadow-sm);
}

.mobile-sidebar-overlay {
  display: none;
}

.mobile-sidebar {
  display: none;
}

/* 모바일 반응형 */
@media (max-width: 991.98px) {
  .sidebar {
    display: none !important;
  }

  .main-content {
    margin-left: 0 !important;
    width: 100% !important;
  }

  .sidebar-collapsed .main-content {
    margin-left: 0 !important;
    width: 100% !important;
  }

  .mobile-sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1040;
    backdrop-filter: blur(2px);
  }

  .mobile-sidebar {
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0;
    left: -280px;
    width: 280px;
    height: 100vh;
    max-height: 100vh;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--sidebar-header-border);
    z-index: 1050;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.15);
    transition: left 0.3s ease;
    overflow: hidden;
  }

  .mobile-sidebar.open {
    left: 0;
  }
}

/* 스크롤바 스타일링 */
.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.25);
  border-radius: 3px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.4);
}

/* 여백이 넓은 페이지(presentation-templates, project-todos) 패딩 축소 */
.main-content-compact {
  padding: 0.75rem !important;
}

/* 멀티 채팅 등 전체 화면 페이지 - 패딩 제거, 자식이 채우도록 */
.main-content-full {
  padding: 0 !important;
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}
.main-content-full .mc-page-wrap {
  flex: 1;
  min-height: 0;
}
</style>
