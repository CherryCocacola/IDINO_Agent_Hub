import { createRouter, createWebHistory } from 'vue-router'
import { safeGetLocalStorage } from '@/utils/storage'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  // ── 인증 불필요 퍼블릭 페이지 ──────────────────────────────────
  {
    path: '/landing',
    name: 'Landing',
    component: () => import('@/views/LandingPage.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/terms',
    name: 'TermsOfService',
    component: () => import('@/views/TermsOfService.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/privacy',
    name: 'PrivacyPolicy',
    component: () => import('@/views/PrivacyPolicy.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/chatbot/:code',
    name: 'AgentPublicChat',
    component: () => import('@/views/agent/AgentPublicChat.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/embed/:code',
    name: 'AgentEmbed',
    component: () => import('@/views/agent/AgentEmbed.vue'),
    meta: { requiresAuth: false }
  },
  // ── 로그인 필요 내부 테스트 페이지 ─────────────────────────────
  {
    path: '/agent-test/:code',
    name: 'AgentTestPage',
    component: () => import('@/views/agent/AgentTestPage.vue'),
    meta: { requiresAuth: true }
  },
  // ──────────────────────────────────────────────────────────────
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue')
      },
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('@/views/agent/AgentSelect.vue')
      },
      {
        path: 'agents/chat/:id?',
        name: 'AgentChat',
        component: () => import('@/views/agent/AgentChat.vue')
      },
      {
        path: 'agents/multi-chat',
        name: 'AgentMultiChat',
        component: () => import('@/views/agent/AgentMultiChat.vue')
      },
      {
        path: 'agents/builder/:id?',
        name: 'AgentBuilder',
        component: () => import('@/views/agent/AgentBuilder.vue')
      },
      {
        path: 'quota',
        name: 'Quota',
        component: () => import('@/views/Quota.vue')
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue')
      },
      {
        path: 'playground',
        name: 'Playground',
        component: () => import('@/views/Playground.vue')
      },
      {
        path: 'agents/marketplace',
        name: 'AgentMarketplace',
        component: () => import('@/views/agent/AgentMarketplace.vue')
      },
      {
        path: 'agents/templates',
        name: 'AgentTemplates',
        component: () => import('@/views/agent/AgentTemplates.vue')
      },
      {
        path: 'audit-log',
        name: 'AuditLog',
        component: () => import('@/views/AuditLog.vue')
      },
      {
        path: 'cost-analysis',
        name: 'CostAnalysis',
        component: () => import('@/views/CostAnalysis.vue')
      },
      {
        path: 'help',
        name: 'Help',
        component: () => import('@/views/Help.vue')
      },
      // ── 후속 트랙 C-1 (2026-05-08) 완료: Phase 2 자체 KB drop 잔재 라우트 `/knowledge-base` 완전 제거.
      // 운영자 KB 진입점은 아래 `/admin/knowledge-base` (DocUtil BFF, Phase 6.3) 단일화 — R2 통합 원칙.
      // ── 운영자 KB(DocUtil BFF) — Phase 6.3 신설. R2 단일 진입점: 운영자 KB 관리는 AgentHub 에서만 ──
      {
        path: 'admin/knowledge-base',
        name: 'AdminKnowledgeBase',
        component: () => import('@/views/AdminKnowledgeBase.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'admin/knowledge-base/upload',
        name: 'AdminKnowledgeBaseUpload',
        component: () => import('@/views/AdminKnowledgeBaseUpload.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'admin/knowledge-base/:id',
        name: 'AdminKnowledgeBaseDetail',
        component: () => import('@/views/AdminKnowledgeBaseDetail.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 5 RAG 메트릭 대시보드 (Phase 4 endpoint /api/admin/metrics/rag 의 시각화 view)
      {
        path: 'admin/rag-metrics',
        name: 'AdminRagMetrics',
        component: () => import('@/views/admin/AdminRagMetrics.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.1a (2026-05-10): DocUtil 사용자 운영자 콘솔 (BFF 패턴)
      // 향후 10.1b(부서) / 10.1c(프로젝트) 트랙에서 추가 라우트 연결 예정.
      {
        path: 'admin/docutil-users',
        name: 'AdminDocUtilUsers',
        component: () => import('@/views/admin/AdminDocUtilUsers.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.1b (2026-05-10): DocUtil 조직/부서/할당량 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-departments',
        name: 'AdminDocUtilDepartments',
        component: () => import('@/views/admin/AdminDocUtilDepartments.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/Reports.vue')
      },
      {
        path: 'usage-history',
        name: 'UsageHistory',
        component: () => import('@/views/UsageHistory.vue')
      },
      {
        path: 'api-keys',
        name: 'ApiKeys',
        component: () => import('@/views/ApiKeys.vue')
      },
      {
        path: 'banned-words',
        name: 'BannedWords',
        component: () => import('@/views/BannedWords.vue')
      },
      {
        path: 'pii-protection',
        name: 'PiiProtection',
        component: () => import('@/views/PiiProtection.vue')
      },
      {
        path: 'team',
        name: 'Team',
        component: () => import('@/views/Team.vue')
      },
      {
        path: 'system-health',
        name: 'SystemHealth',
        component: () => import('@/views/SystemHealth.vue')
      },
      {
        path: 'database-backup',
        name: 'DatabaseBackup',
        component: () => import('@/views/DatabaseBackup.vue')
      },
      {
        path: 'presentation-templates',
        name: 'PresentationTemplateManagement',
        component: () => import('@/views/PresentationTemplateManagement.vue')
      },
      {
        path: 'image-generation',
        name: 'ImageGeneration',
        component: () => import('@/views/ImageGeneration.vue')
      },
      {
        path: 'quick-image',
        name: 'QuickImageGeneration',
        component: () => import('@/views/QuickImageGeneration.vue')
      },
      {
        path: 'presentation-builder',
        name: 'PresentationBuilder',
        component: () => import('@/views/PresentationBuilder.vue')
      },
      {
        path: 'tools',
        name: 'Tools',
        component: () => import('@/views/tool/ToolList.vue')
      },
      {
        path: 'tools/builder',
        name: 'ToolBuilder',
        component: () => import('@/views/tool/ToolBuilder.vue')
      },
      {
        path: 'workflows',
        name: 'Workflows',
        component: () => import('@/views/workflow/WorkflowList.vue')
      },
      {
        path: 'workflows/builder',
        name: 'WorkflowBuilder',
        component: () => import('@/views/workflow/WorkflowBuilder.vue')
      },
      {
        path: 'workflows/executions/:id?',
        name: 'WorkflowExecutionMonitor',
        component: () => import('@/views/workflow/WorkflowExecutionMonitor.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = safeGetLocalStorage('token')

  // 루트(/) 미로그인 → 랜딩 페이지 (requiresAuth 체크보다 먼저)
  if (to.path === '/' && !token) {
    next('/landing')
    return
  }

  // 인증이 필요한 페이지 → 미로그인 시 로그인 페이지로 (원래 경로 redirect 파라미터 유지)
  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 이미 로그인한 경우: 로그인·랜딩 페이지 진입 방지 → 대시보드로
  if ((to.path === '/login' || to.path === '/landing') && token) {
    next('/')
    return
  }

  next()
})

export default router
