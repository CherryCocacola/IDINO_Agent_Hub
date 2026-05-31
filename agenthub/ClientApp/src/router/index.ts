import { createRouter, createWebHistory } from 'vue-router'
import { safeGetAuthStorage } from '@/utils/storage'
import { useAuthStore } from '@/stores/auth'

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
        component: () => import('@/views/Users.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
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
        component: () => import('@/views/AuditLog.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'cost-analysis',
        name: 'CostAnalysis',
        component: () => import('@/views/CostAnalysis.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
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
      // Phase 10.1c (2026-05-10): DocUtil 프로젝트/보드 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-projects',
        name: 'AdminDocUtilProjects',
        component: () => import('@/views/admin/AdminDocUtilProjects.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2a (2026-05-10): DocUtil 대시보드 운영자 모니터링 (BFF 패턴)
      {
        path: 'admin/docutil-dashboard',
        name: 'AdminDocUtilDashboard',
        component: () => import('@/views/admin/AdminDocUtilDashboard.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2a (2026-05-10): DocUtil 감사 로그 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-audit',
        name: 'AdminDocUtilAudit',
        component: () => import('@/views/admin/AdminDocUtilAudit.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2b (2026-05-10): DocUtil 검색범위 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-search-scopes',
        name: 'AdminDocUtilSearchScopes',
        component: () => import('@/views/admin/AdminDocUtilSearchScopes.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2b (2026-05-10): DocUtil 평가(RAG 품질) 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-evaluation',
        name: 'AdminDocUtilEvaluation',
        component: () => import('@/views/admin/AdminDocUtilEvaluation.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2c (2026-05-11): DocUtil FAQ 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-faq',
        name: 'AdminDocUtilFaq',
        component: () => import('@/views/admin/AdminDocUtilFaq.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // 트랙 #136 (2026-05-31): AgentHub 도움말 FAQ + 튜토리얼 운영자 관리 콘솔.
      // backend FaqsController / TutorialsController 의 POST/PUT/DELETE Admin 가드 활용.
      {
        path: 'admin/faqs',
        name: 'AdminFaqs',
        component: () => import('@/views/admin/AdminFaqs.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'admin/tutorials',
        name: 'AdminTutorials',
        component: () => import('@/views/admin/AdminTutorials.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2c (2026-05-11): DocUtil 보고서/템플릿 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-reports',
        name: 'AdminDocUtilReports',
        component: () => import('@/views/admin/AdminDocUtilReports.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2d (2026-05-11): DocUtil 문서 템플릿(Jinja2) 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-templates',
        name: 'AdminDocUtilTemplates',
        component: () => import('@/views/admin/AdminDocUtilTemplates.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2e (2026-05-11): DocUtil LLM API Key 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-api-keys',
        name: 'AdminDocUtilApiKeys',
        component: () => import('@/views/admin/AdminDocUtilApiKeys.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2e (2026-05-11): DocUtil 에이전트(챗봇용 페르소나) 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-doc-agents',
        name: 'AdminDocUtilDocAgents',
        component: () => import('@/views/admin/AdminDocUtilDocAgents.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // Phase 10.2e (2026-05-11): DocUtil 문서 V2(디자이너 워크플로) 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-documents-v2',
        name: 'AdminDocUtilDocumentsV2',
        component: () => import('@/views/admin/AdminDocUtilDocumentsV2.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // 트랙 A1 Phase B (2026-05-25): DocUtil 시스템 설정 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-settings',
        name: 'AdminDocUtilSettings',
        component: () => import('@/views/admin/AdminDocUtilSettings.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // 트랙 A1 Phase B (2026-05-25): DocUtil 퀵 가이드 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-quick-guide',
        name: 'AdminDocUtilQuickGuide',
        component: () => import('@/views/admin/AdminDocUtilQuickGuide.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      // 트랙 A1 Phase B (2026-05-25): DocUtil 검색 테스트 운영자 콘솔 (BFF 패턴)
      {
        path: 'admin/docutil-search-test',
        name: 'AdminDocUtilSearchTest',
        component: () => import('@/views/admin/AdminDocUtilSearchTest.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/Reports.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
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
        component: () => import('@/views/BannedWords.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'pii-protection',
        name: 'PiiProtection',
        component: () => import('@/views/PiiProtection.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'team',
        name: 'Team',
        component: () => import('@/views/Team.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'system-health',
        name: 'SystemHealth',
        component: () => import('@/views/SystemHealth.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'database-backup',
        name: 'DatabaseBackup',
        component: () => import('@/views/DatabaseBackup.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
      },
      {
        path: 'presentation-templates',
        name: 'PresentationTemplateManagement',
        component: () => import('@/views/PresentationTemplateManagement.vue'),
        meta: { requiresAuth: true, role: 'Admin' }
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

// ════════════════════════════════════════════════════════════════════════════
// 권한 가드 (Phase 10.x — 2026-05-11, code-analysis-specialist Critical 결함 보강)
//
// 배경:
//   /admin/* (특히 DocUtil 관리 13 라우트) 들은 meta.role / meta.roles 가
//   부착되어 있으나 종전 router.beforeEach 는 token 존재만 검증하였다.
//   → 일반 사용자가 URL 직접 입력 시 BFF 401 차단에 의존했지만, UI 레벨에서
//      이미 차단해야 사용자 경험·보안이 일관된다(컨트롤러 [Authorize] 는 백엔드
//      최종 방어선이고, 라우터 가드는 1차 진입 차단).
//
// 동작 정책:
//   1. token 미존재 + requiresAuth = login 으로 리다이렉트(기존 동작 유지)
//   2. token 존재 + meta.role / meta.roles 부착 = user.roles 와 교차 검증
//      - SuperAdmin 은 항상 통과(상위 권한 — Admin 포함 모든 페이지)
//      - 부족 시 '/' (Dashboard) 로 리다이렉트
//   3. user 미로드 상태(예: 새로고침 직후) 면 loadUser() 시도, 실패 시 logout 후 login
//
// 참고: ChatGPT/Claude 등 SPA 보호 패턴 — 백엔드 [Authorize] 가 단일 진실,
//       라우터 가드는 사용자 UX 차원의 사전 차단이다. 이중 방어로 본다.
// ════════════════════════════════════════════════════════════════════════════

/**
 * 라우트 meta 의 role / roles 정의를 단일 배열로 정규화한다.
 * - meta.role: 'Admin'         → ['Admin']
 * - meta.roles: ['Admin', ...] → 그대로
 * - 둘 다 없음                  → []  (권한 검사 skip)
 */
function getRequiredRoles(meta: Record<string, unknown>): string[] {
  const required: string[] = []
  if (typeof meta.role === 'string' && meta.role.length > 0) {
    required.push(meta.role)
  }
  if (Array.isArray(meta.roles)) {
    for (const r of meta.roles) {
      if (typeof r === 'string' && r.length > 0) required.push(r)
    }
  }
  return required
}

/**
 * 사용자가 요구 role 중 하나라도 보유한지 검사.
 * SuperAdmin 은 상위 권한이므로 항상 true.
 */
function hasRequiredRole(userRoles: string[], required: string[]): boolean {
  if (required.length === 0) return true
  if (userRoles.includes('SuperAdmin')) return true
  return required.some((r) => userRoles.includes(r))
}

router.beforeEach(async (to, _from, next) => {
  // 트랙 #97-pre2-2 (2026-05-14): safeGetLocalStorage → safeGetAuthStorage 로 교정.
  // 트랙 #88 C2 의 "자동 로그인 유지" 분기에서 rememberMe=false 사용자는 sessionStorage 에
  // 토큰이 저장된다. 그러나 본 가드가 localStorage 만 보면 sessionStorage 에 저장된 토큰을
  // 못 찾아 token=null 로 인식하고 /login 으로 무한 redirect — 로그인 자체가 성공해도
  // 화면이 그대로 머무는 결함이 발생한다. authStore 와 동일한 local→session 탐색 정책을 적용.
  const token = safeGetAuthStorage('token')

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

  // ── user 로드 + 권한(role/roles) 검증 ───────────────────────────────
  // 트랙 #100 F2 fix — 모든 인증 라우트 진입 시 user 가 null 이면 loadUser() 호출.
  //   기존 결함: loadUser 가 `required.length > 0` (meta.role 있는 라우트) 일 때만 호출 →
  //   Settings 같은 일반 라우트는 user 갱신 안 됨 → authStore.user.departmentPath 가 null →
  //   화면이 "미배정" 으로 fallback (BFF 응답에 departmentPath 가 있어도 무용).
  //   해소: user 로드를 권한 검사와 분리하여 모든 인증 라우트에 적용.
  if (to.meta.requiresAuth && token) {
    const auth = useAuthStore()

    // 1) user 가 메모리에 없다면(새로고침 직후 또는 일반 라우트 첫 진입) 토큰으로 로드 시도.
    if (!auth.user) {
      try {
        await auth.loadUser()
      } catch {
        // loadUser 실패는 내부적으로 logout 처리 — login 으로 보냄.
        next({ path: '/login', query: { redirect: to.fullPath } })
        return
      }
    }

    // 2) meta.role|roles 가 부착된 라우트만 권한 검사 수행 (일반 라우트는 통과).
    const required = getRequiredRoles(to.meta as Record<string, unknown>)
    if (required.length > 0) {
      const userRoles = auth.user?.roles ?? []
      if (!hasRequiredRole(userRoles, required)) {
        // 권한 부족 — 무한 루프 방지를 위해 root('/' = Dashboard) 로 리다이렉트.
        // 사용자에게는 alert/toast 대신 console 경고만(UX는 진입 차단으로 충분).
        // eslint-disable-next-line no-console
        console.warn(
          `[router] 권한 부족 — 라우트 진입 차단: path=${to.fullPath}, ` +
            `required=[${required.join(', ')}], userRoles=[${userRoles.join(', ')}]`
        )
        next('/')
        return
      }
    }
  }

  next()
})

export default router
