"""트랙 #83 — 전수 라우트 카탈로그 + 케이스 정의.

AgentHub Vue 49 routes + DocUtil Next.js 25 routes = 74 routes.
라우트당 평균 6~10 케이스 (진입/렌더링/주요 인터랙션/권한/에러) → 약 600 케이스.

원칙:
- 운영 영향 0 (read-only + 안전 mutation 1 cycle 만)
- mutation 케이스는 별도 risk='mutation' 표시 + safe_cycle=True
- LLM 비용 케이스는 risk='cost' 표시 + once_only=True
- DocUtil 인증 의존은 default SKIP (자격증명 제공 시 진행 분기)
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TestCase:
    case_id: str  # 예: AH-001
    sheet: str  # 시트명 (라우트별)
    screen: str  # 화면명
    path: str  # 라우트 경로
    interaction: str  # 인터랙션 / 검증 항목
    precond: str  # 사전조건
    action: str  # 입력 / 액션
    expected: str  # 기대 결과
    risk: str  # safe / mutation / cost
    auto: str  # auto / manual / skip
    role: str  # anon / user / admin / superadmin
    note: str = ""


# ════════════════════════════════════════════════════════════════════════════
# AgentHub Vue 49 라우트
# ════════════════════════════════════════════════════════════════════════════

# Public (인증 불필요) 9개
PUBLIC_ROUTES = [
    ("Login", "/login", "Login.vue"),
    ("Landing", "/landing", "LandingPage.vue"),
    ("ForgotPassword", "/forgot-password", "ForgotPassword.vue"),
    ("ResetPassword", "/reset-password", "ResetPassword.vue"),
    ("TermsOfService", "/terms", "TermsOfService.vue"),
    ("PrivacyPolicy", "/privacy", "PrivacyPolicy.vue"),
    ("AgentPublicChat", "/chatbot/test", "AgentPublicChat.vue"),
    ("AgentEmbed", "/embed/test", "AgentEmbed.vue"),
    ("AgentTestPage", "/agent-test/test", "AgentTestPage.vue"),  # requiresAuth=true
]

# Protected (admin) 40개
PROTECTED_ROUTES = [
    ("Dashboard", "/", "Dashboard.vue"),
    ("Users", "/users", "Users.vue"),
    ("Agents", "/agents", "AgentSelect.vue"),
    ("AgentChat", "/agents/chat", "AgentChat.vue"),
    ("AgentMultiChat", "/agents/multi-chat", "AgentMultiChat.vue"),
    ("AgentBuilder", "/agents/builder", "AgentBuilder.vue"),
    ("Quota", "/quota", "Quota.vue"),
    ("Analytics", "/analytics", "Analytics.vue"),
    ("Settings", "/settings", "Settings.vue"),
    ("Playground", "/playground", "Playground.vue"),
    ("AgentMarketplace", "/agents/marketplace", "AgentMarketplace.vue"),
    ("AgentTemplates", "/agents/templates", "AgentTemplates.vue"),
    ("AuditLog", "/audit-log", "AuditLog.vue"),
    ("CostAnalysis", "/cost-analysis", "CostAnalysis.vue"),
    ("Help", "/help", "Help.vue"),
    ("AdminKnowledgeBase", "/admin/knowledge-base", "AdminKnowledgeBase.vue"),
    ("AdminKnowledgeBaseUpload", "/admin/knowledge-base/upload", "AdminKnowledgeBaseUpload.vue"),
    ("AdminRagMetrics", "/admin/rag-metrics", "AdminRagMetrics.vue"),
    ("AdminDocUtilUsers", "/admin/docutil-users", "AdminDocUtilUsers.vue"),
    ("AdminDocUtilDepartments", "/admin/docutil-departments", "AdminDocUtilDepartments.vue"),
    ("AdminDocUtilProjects", "/admin/docutil-projects", "AdminDocUtilProjects.vue"),
    ("AdminDocUtilDashboard", "/admin/docutil-dashboard", "AdminDocUtilDashboard.vue"),
    ("AdminDocUtilAudit", "/admin/docutil-audit", "AdminDocUtilAudit.vue"),
    ("AdminDocUtilSearchScopes", "/admin/docutil-search-scopes", "AdminDocUtilSearchScopes.vue"),
    ("AdminDocUtilEvaluation", "/admin/docutil-evaluation", "AdminDocUtilEvaluation.vue"),
    ("AdminDocUtilFaq", "/admin/docutil-faq", "AdminDocUtilFaq.vue"),
    ("AdminDocUtilReports", "/admin/docutil-reports", "AdminDocUtilReports.vue"),
    ("AdminDocUtilTemplates", "/admin/docutil-templates", "AdminDocUtilTemplates.vue"),
    ("AdminDocUtilApiKeys", "/admin/docutil-api-keys", "AdminDocUtilApiKeys.vue"),
    ("AdminDocUtilDocAgents", "/admin/docutil-doc-agents", "AdminDocUtilDocAgents.vue"),
    ("AdminDocUtilDocumentsV2", "/admin/docutil-documents-v2", "AdminDocUtilDocumentsV2.vue"),
    ("Reports", "/reports", "Reports.vue"),
    ("UsageHistory", "/usage-history", "UsageHistory.vue"),
    ("ApiKeys", "/api-keys", "ApiKeys.vue"),
    ("BannedWords", "/banned-words", "BannedWords.vue"),
    ("PiiProtection", "/pii-protection", "PiiProtection.vue"),
    ("Team", "/team", "Team.vue"),
    ("SystemHealth", "/system-health", "SystemHealth.vue"),
    ("DatabaseBackup", "/database-backup", "DatabaseBackup.vue"),
    ("PresentationTemplateManagement", "/presentation-templates", "PresentationTemplateManagement.vue"),
    ("ImageGeneration", "/image-generation", "ImageGeneration.vue"),
    ("QuickImageGeneration", "/quick-image", "QuickImageGeneration.vue"),
    ("PresentationBuilder", "/presentation-builder", "PresentationBuilder.vue"),
    ("Tools", "/tools", "ToolList.vue"),
    ("ToolBuilder", "/tools/builder", "ToolBuilder.vue"),
    ("Workflows", "/workflows", "WorkflowList.vue"),
    ("WorkflowBuilder", "/workflows/builder", "WorkflowBuilder.vue"),
    ("WorkflowExecutionMonitor", "/workflows/executions", "WorkflowExecutionMonitor.vue"),
]

# ════════════════════════════════════════════════════════════════════════════
# DocUtil Next.js 25 라우트
# ════════════════════════════════════════════════════════════════════════════

DOCUTIL_ROUTES = [
    # 공개 (3)
    ("DU_Home", "/", "page.tsx", "anon"),
    ("DU_PreviewHost", "/preview-host", "page.tsx", "anon"),
    ("DU_Login", "/login", "(auth)/login/page.tsx", "anon"),
    # 관리자 (15) — DocUtil 자격증명 미확보 → SKIP 기본값
    ("DU_AdminDashboard", "/dashboard", "(admin)/dashboard/page.tsx", "admin"),
    ("DU_AdminAccounts", "/admin-accounts", "(admin)/admin-accounts/page.tsx", "admin"),
    ("DU_Agents", "/agents", "(admin)/agents/page.tsx", "admin"),
    ("DU_ApiKeys", "/api-keys", "(admin)/api-keys/page.tsx", "admin"),
    ("DU_Departments", "/departments", "(admin)/departments/page.tsx", "admin"),
    ("DU_Documents", "/documents", "(admin)/documents/page.tsx", "admin"),
    ("DU_Evaluation", "/evaluation", "(admin)/evaluation/page.tsx", "admin"),
    ("DU_Help", "/help", "(admin)/help/page.tsx", "admin"),
    ("DU_Projects", "/projects", "(admin)/projects/page.tsx", "admin"),
    ("DU_QuickGuide", "/quick-guide", "(admin)/quick-guide/page.tsx", "admin"),
    ("DU_Quotas", "/quotas", "(admin)/quotas/page.tsx", "admin"),
    ("DU_SearchScopes", "/search-scopes", "(admin)/search-scopes/page.tsx", "admin"),
    ("DU_SearchTest", "/search-test", "(admin)/search-test/page.tsx", "admin"),
    ("DU_Settings", "/settings", "(admin)/settings/page.tsx", "admin"),
    ("DU_Templates", "/templates", "(admin)/templates/page.tsx", "admin"),
    # 사용자 (6) — DocUtil 자격증명 미확보 → SKIP 기본값
    ("DU_Chat", "/chat", "(user)/chat/page.tsx", "user"),
    ("DU_DesignerCreate", "/designer/create", "(user)/designer/create/page.tsx", "user"),
    ("DU_DesignerFill", "/designer/fill/dummy", "(user)/designer/fill/[templateId]/page.tsx", "user"),
    ("DU_DesignerDocument", "/designer/dummy", "(user)/designer/[documentId]/page.tsx", "user"),
    ("DU_MyDocuments", "/my-documents", "(user)/my-documents/page.tsx", "user"),
    ("DU_Reports", "/reports", "(user)/reports/page.tsx", "user"),
    ("DU_Search", "/search", "(user)/search/page.tsx", "user"),
]


def _make_cases_for_route(
    route_id: int,
    sheet: str,
    screen: str,
    path: str,
    is_public: bool,
    is_admin_only: bool = False,
    docutil: bool = False,
    docutil_anon: bool = False,
) -> list[TestCase]:
    """라우트당 표준 케이스 셋 생성."""
    prefix = f"AH-{route_id:03d}" if not docutil else f"DU-{route_id:03d}"
    cases: list[TestCase] = []
    # 1. 화면 진입 (admin 로그인 상태)
    if not docutil or docutil_anon:
        precond_enter = "(admin 로그인) — public 라우트도 admin 세션 보유 상태에서 진입" if not is_public else "(미로그인) anonymous"
        cases.append(TestCase(
            f"{prefix}-01", sheet, screen, path,
            "화면 진입 (admin 세션)" if not is_public else "화면 진입 (anonymous)",
            precond_enter,
            f"GET {path}",
            "HTTP 200 또는 클라이언트 라우팅 성공 + 페이지 마운트 (Vue/Next 컴포넌트 렌더)",
            "safe", "auto",
            "admin" if not is_public else "anon",
        ))
    else:
        cases.append(TestCase(
            f"{prefix}-01", sheet, screen, path,
            "화면 진입 (인증 의존 — DocUtil 자격증명 미확보)",
            "DocUtil 운영자 자격증명 미확보",
            f"GET {path}",
            "로그인 페이지로 리다이렉트 또는 DocUtil 자격증명 확보 후 재진행",
            "safe", "skip",
            "admin",
            "DocUtil 자격증명 제공 시 진행 분기",
        ))

    # 2. 권한 분기 (anonymous 진입 시 리다이렉트)
    if not is_public:
        cases.append(TestCase(
            f"{prefix}-02", sheet, screen, path,
            "권한 분기 (anonymous → /login 리다이렉트)",
            "(미로그인 + 새 컨텍스트)",
            f"GET {path} (token 없음)",
            "/login?redirect=... 또는 /landing 으로 리다이렉트",
            "safe", "auto",
            "anon",
        ))
    else:
        cases.append(TestCase(
            f"{prefix}-02", sheet, screen, path,
            "권한 분기 (admin 진입도 허용)",
            "(admin 로그인 상태)",
            f"GET {path}",
            "redirect=true 가 아닌 경우 그대로 표시 또는 routerGuard 에 따라 /로 이동",
            "safe", "auto",
            "admin",
        ))

    # 3. 페이지 마운트 검증 (DOM 안정화)
    cases.append(TestCase(
        f"{prefix}-03", sheet, screen, path,
        "DOM 마운트 + 주요 컨테이너 렌더",
        "(라우트 진입 완료)",
        "DOM 로드 + 1초 대기 → console error 0건 + 핵심 selector 가시",
        "console error 0건 (잘 알려진 외부 라이브러리 경고 제외), 핵심 컨테이너(main/main-layout/page-root) 렌더",
        "safe", "auto",
        "admin" if not is_public else "anon",
    ))

    # 4. 데이터 자동 호출 / API 응답 (admin 화면 위주)
    if not is_public and not docutil:
        cases.append(TestCase(
            f"{prefix}-04", sheet, screen, path,
            "페이지 진입 시 API 자동 호출 응답 확인",
            "(라우트 진입 완료)",
            "network 모니터 — 첫 5초 내 발생한 /api 또는 /v1 호출 + 상태코드 수집",
            "관련 API 200 OK 또는 비-401 응답. 401 발생 시 권한 분기 케이스로 분류",
            "safe", "auto",
            "admin",
        ))

    # 5. 메뉴 가시성 / 사이드바 활성
    if not is_public and not docutil:
        cases.append(TestCase(
            f"{prefix}-05", sheet, screen, path,
            "사이드바 / 헤더 / 활성 메뉴 표시",
            "(라우트 진입 완료)",
            "선택된 메뉴 highlight + 현재 사용자(admin) 정보 표시 확인",
            "사이드바 노드 활성 클래스 + 사용자 아바타/이름 가시",
            "safe", "auto",
            "admin",
        ))

    # 6. 스크린샷 저장
    cases.append(TestCase(
        f"{prefix}-06", sheet, screen, path,
        "스크린샷 캡처 (감사용)",
        "(라우트 진입 + DOM 안정화)",
        "viewport 스크린샷 (full=false)",
        "screenshots/full/ 하위 .png 저장됨 (평문 시크릿 없음)",
        "safe", "auto",
        "admin" if not is_public else "anon",
    ))

    return cases


def _make_special_cases() -> list[TestCase]:
    """라우트별 특수 인터랙션 (모달/폼/버튼 등) — 안전 범위만."""
    sp: list[TestCase] = []

    # ─── Login.vue ───
    sp.extend([
        TestCase(
            "AH-SP-001", "Login", "로그인", "/login",
            "잘못된 자격증명 → 에러 표시",
            "(미로그인)",
            "email=wrong@test.com / password=wrongpw → 로그인",
            "400/401 응답 + 한국어 에러 메시지 (예: '이메일 또는 비밀번호가 올바르지 않습니다')",
            "safe", "auto", "anon",
        ),
        TestCase(
            "AH-SP-002", "Login", "로그인", "/login",
            "올바른 자격증명 → 대시보드 진입",
            "(미로그인)",
            f"admin@example.com / Admin123! → 로그인",
            "200 OK + token 저장 + / 리다이렉트",
            "safe", "auto", "anon",
        ),
        TestCase(
            "AH-SP-003", "Login", "로그인", "/login",
            "비밀번호 찾기 링크 → /forgot-password 라우팅",
            "(미로그인 + 로그인 페이지)",
            "비밀번호 찾기 링크 클릭",
            "/forgot-password 페이지 진입",
            "safe", "auto", "anon",
        ),
    ])

    # ─── Dashboard.vue ───
    sp.extend([
        TestCase(
            "AH-SP-010", "Dashboard", "대시보드", "/",
            "주요 카드/차트 렌더링",
            "(admin 로그인)",
            "/ 진입",
            "사용량/에이전트수/비용 등 카드 4+ 렌더, 차트 1+ 렌더",
            "safe", "auto", "admin",
        ),
    ])

    # ─── ApiKeys.vue (이미 시나리오 1 진행분 인용) ───
    sp.extend([
        TestCase(
            "AH-SP-020", "ApiKeys", "API 키", "/api-keys",
            "탭 전환 (관리자 / Agent API 키)",
            "(admin 로그인)",
            "두 탭 클릭하여 전환",
            "각 탭 콘텐츠 렌더",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-021", "ApiKeys", "API 키", "/api-keys",
            "[시나리오 1 인용] Agent API 키 발급+회수 1 cycle",
            "트랙 #75 commit b7de919 참조",
            "(자동화 완료 — 재실행 안 함)",
            "PASS (시나리오 1 결과 인용)",
            "mutation", "manual", "admin",
            "tools/ui_e2e/scenario_1_apikey.py 결과 참조",
        ),
    ])

    # ─── Agents.vue / AgentChat ───
    sp.extend([
        TestCase(
            "AH-SP-030", "Agents", "에이전트 목록", "/agents",
            "에이전트 카드 클릭 → 채팅 진입",
            "(admin 로그인 + 에이전트 1+ 존재)",
            "첫 에이전트 카드 클릭",
            "/agents/chat/{id} 라우팅 + 채팅 컴포넌트 마운트",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-031", "AgentChat", "에이전트 채팅", "/agents/chat",
            "[시나리오 2 인용] LLM 1회 호출",
            "트랙 #75 commit b7de919 참조",
            "(자동화 완료 — 재실행 안 함)",
            "PASS (시나리오 2 결과 인용 — LLM 비용 1회만)",
            "cost", "manual", "admin",
            "tools/ui_e2e/scenario_2_chat.py 결과 참조",
        ),
        TestCase(
            "AH-SP-032", "AgentBuilder", "에이전트 빌더", "/agents/builder",
            "신규 에이전트 생성 폼 표시",
            "(admin 로그인)",
            "/agents/builder 진입",
            "이름/모델/시스템 프롬프트 입력 필드 가시",
            "safe", "auto", "admin",
        ),
    ])

    # ─── AdminKnowledgeBase / AdminRagMetrics ───
    sp.extend([
        TestCase(
            "AH-SP-040", "AdminKnowledgeBase", "운영자 KB", "/admin/knowledge-base",
            "KB 컬렉션 목록 로드 (DocUtil BFF)",
            "(admin 로그인)",
            "/admin/knowledge-base 진입",
            "DocUtil collections 목록 표시 또는 빈 상태 UI",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-041", "AdminRagMetrics", "RAG 메트릭", "/admin/rag-metrics",
            "RAG 메트릭 차트 표시",
            "(admin 로그인)",
            "/admin/rag-metrics 진입",
            "메트릭 차트/표 렌더",
            "safe", "auto", "admin",
        ),
    ])

    # ─── AdminDocUtil* (13개) ───
    # 각 화면 진입은 표준 케이스에 포함되므로 별도 인터랙션은 안전 범위 내 1개씩만
    for slug, sheet, screen in [
        ("docutil-users", "AdminDocUtilUsers", "DocUtil 사용자"),
        ("docutil-departments", "AdminDocUtilDepartments", "DocUtil 부서"),
        ("docutil-projects", "AdminDocUtilProjects", "DocUtil 프로젝트"),
        ("docutil-dashboard", "AdminDocUtilDashboard", "DocUtil 대시보드"),
        ("docutil-audit", "AdminDocUtilAudit", "DocUtil 감사"),
        ("docutil-search-scopes", "AdminDocUtilSearchScopes", "DocUtil 검색범위"),
        ("docutil-evaluation", "AdminDocUtilEvaluation", "DocUtil 평가"),
        ("docutil-faq", "AdminDocUtilFaq", "DocUtil FAQ"),
        ("docutil-reports", "AdminDocUtilReports", "DocUtil 보고서"),
        ("docutil-templates", "AdminDocUtilTemplates", "DocUtil 템플릿"),
        ("docutil-api-keys", "AdminDocUtilApiKeys", "DocUtil API 키"),
        ("docutil-doc-agents", "AdminDocUtilDocAgents", "DocUtil 에이전트"),
        ("docutil-documents-v2", "AdminDocUtilDocumentsV2", "DocUtil 문서 V2"),
    ]:
        sp.append(TestCase(
            f"AH-SP-050-{slug}", sheet, screen, f"/admin/{slug}",
            "BFF 데이터 로드 (DocUtil → AgentHub BFF)",
            "(admin 로그인)",
            f"/admin/{slug} 진입",
            "DocUtil API 응답 또는 5xx 시 한국어 에러 토스트",
            "safe", "auto", "admin",
        ))

    # ─── 일반 관리자 페이지 ───
    sp.extend([
        TestCase(
            "AH-SP-060", "Users", "사용자 관리", "/users",
            "사용자 목록 페이지네이션",
            "(admin 로그인)",
            "/users 진입",
            "사용자 표 렌더 + 페이지네이션 컨트롤",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-061", "Settings", "설정", "/settings",
            "설정 폼 표시 (저장 안 함)",
            "(admin 로그인)",
            "/settings 진입 → 값 확인 (변경 없이)",
            "설정 폼 가시 — 운영 무변경",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-062", "SystemHealth", "시스템 헬스", "/system-health",
            "헬스 체크 결과 표시",
            "(admin 로그인)",
            "/system-health 진입",
            "PostgreSQL/Redis/외부 LLM 헬스 표시",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-063", "DatabaseBackup", "DB 백업", "/database-backup",
            "백업 목록 표시 (실행 안 함)",
            "(admin 로그인)",
            "/database-backup 진입",
            "백업 이력 + 백업 트리거 버튼 가시 (클릭하지 않음)",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-064", "Analytics", "분석", "/analytics",
            "차트 렌더 + 기간 필터",
            "(admin 로그인)",
            "/analytics 진입",
            "차트 1+ 렌더, 기간 선택기 가시",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-065", "AuditLog", "감사 로그", "/audit-log",
            "감사 로그 표 + 필터",
            "(admin 로그인)",
            "/audit-log 진입",
            "감사 로그 행 렌더 또는 빈 상태",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-066", "BannedWords", "금칙어", "/banned-words",
            "금칙어 목록 표시",
            "(admin 로그인)",
            "/banned-words 진입",
            "금칙어 목록 + 카테고리 필터",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-067", "PiiProtection", "PII 보호", "/pii-protection",
            "PII 설정 표시",
            "(admin 로그인)",
            "/pii-protection 진입",
            "PII 정책 폼 가시 (변경 없음)",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-068", "Quota", "할당량", "/quota",
            "할당량 표 표시",
            "(admin 로그인)",
            "/quota 진입",
            "사용자/프로바이더별 할당량 표 렌더",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-069", "Team", "팀", "/team",
            "팀 목록 표시",
            "(admin 로그인)",
            "/team 진입",
            "팀 목록 또는 빈 상태",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-070", "Reports", "리포트", "/reports",
            "리포트 목록 표시",
            "(admin 로그인)",
            "/reports 진입",
            "리포트 이력 렌더",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-071", "UsageHistory", "사용 이력", "/usage-history",
            "사용 이력 표 + 페이지네이션",
            "(admin 로그인)",
            "/usage-history 진입",
            "사용 이력 행 렌더 + 페이지네이션",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-072", "CostAnalysis", "비용 분석", "/cost-analysis",
            "비용 차트 표시",
            "(admin 로그인)",
            "/cost-analysis 진입",
            "프로바이더/모델별 비용 차트 렌더",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-073", "Help", "도움말", "/help",
            "도움말 페이지 콘텐츠 표시",
            "(admin 로그인)",
            "/help 진입",
            "도움말 섹션 렌더",
            "safe", "auto", "admin",
        ),
    ])

    # ─── Playground (LLM 비용) ───
    sp.append(TestCase(
        "AH-SP-080", "Playground", "Playground", "/playground",
        "모델 선택 드롭다운 + 프롬프트 입력 폼 표시 (전송 안 함)",
        "(admin 로그인)",
        "/playground 진입 — 모델 선택만, 전송 클릭 안 함",
        "모델 드롭다운 + 텍스트영역 가시, LLM 호출 발생 안 함",
        "safe", "auto", "admin",
        "전송은 LLM 비용 발생 — 자동화 차단",
    ))

    # ─── Tools / Workflows ───
    sp.extend([
        TestCase(
            "AH-SP-090", "Tools", "도구 목록", "/tools",
            "도구 목록 + 새로 만들기 버튼",
            "(admin 로그인)",
            "/tools 진입",
            "도구 목록 또는 빈 상태 + 새로 만들기 버튼 가시",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-091", "ToolBuilder", "도구 빌더", "/tools/builder",
            "도구 빌더 폼 표시 (저장 안 함)",
            "(admin 로그인)",
            "/tools/builder 진입",
            "도구 타입 선택 (C#/Script/API) + 코드 에디터 가시",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-092", "Workflows", "워크플로우 목록", "/workflows",
            "워크플로우 목록 표시",
            "(admin 로그인)",
            "/workflows 진입",
            "워크플로우 카드/표 렌더",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-093", "WorkflowBuilder", "워크플로우 빌더", "/workflows/builder",
            "Vue Flow 에디터 마운트",
            "(admin 로그인)",
            "/workflows/builder 진입",
            "Vue Flow 캔버스 + 노드 팔레트 가시",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-094", "WorkflowExecutionMonitor", "실행 모니터", "/workflows/executions",
            "실행 이력 표시",
            "(admin 로그인)",
            "/workflows/executions 진입",
            "실행 이력 행 또는 빈 상태",
            "safe", "auto", "admin",
        ),
    ])

    # ─── Marketplace / Templates ───
    sp.extend([
        TestCase(
            "AH-SP-100", "AgentMarketplace", "에이전트 마켓플레이스", "/agents/marketplace",
            "마켓플레이스 카드 표시",
            "(admin 로그인)",
            "/agents/marketplace 진입",
            "에이전트 카드 그리드 렌더",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-101", "AgentTemplates", "에이전트 템플릿", "/agents/templates",
            "템플릿 목록 표시",
            "(admin 로그인)",
            "/agents/templates 진입",
            "템플릿 카드 렌더",
            "safe", "auto", "admin",
        ),
    ])

    # ─── 이미지/프리젠테이션 (LLM/이미지 비용) ───
    sp.extend([
        TestCase(
            "AH-SP-110", "ImageGeneration", "이미지 생성", "/image-generation",
            "이미지 생성 폼 표시 (전송 안 함)",
            "(admin 로그인)",
            "/image-generation 진입 — 폼 확인만",
            "프롬프트 입력 + 모델 선택 가시, 생성 클릭 안 함",
            "safe", "auto", "admin",
            "이미지 생성은 비용 — 자동화 차단",
        ),
        TestCase(
            "AH-SP-111", "QuickImageGeneration", "빠른 이미지", "/quick-image",
            "빠른 이미지 폼 표시 (전송 안 함)",
            "(admin 로그인)",
            "/quick-image 진입",
            "폼 가시",
            "safe", "auto", "admin",
            "이미지 생성은 비용 — 자동화 차단",
        ),
        TestCase(
            "AH-SP-112", "PresentationBuilder", "프레젠테이션 빌더", "/presentation-builder",
            "프레젠테이션 빌더 마운트",
            "(admin 로그인)",
            "/presentation-builder 진입",
            "빌더 UI 가시",
            "safe", "auto", "admin",
            "PPTX 생성은 비용 — 자동화 차단",
        ),
        TestCase(
            "AH-SP-113", "PresentationTemplateManagement", "프레젠테이션 템플릿", "/presentation-templates",
            "템플릿 목록 표시",
            "(admin 로그인)",
            "/presentation-templates 진입",
            "PPTX 템플릿 목록 또는 빈 상태",
            "safe", "auto", "admin",
        ),
    ])

    # ─── 다중 채팅 / 공개 챗봇 ───
    sp.extend([
        TestCase(
            "AH-SP-120", "AgentMultiChat", "다중 에이전트 채팅", "/agents/multi-chat",
            "다중 채팅 UI 마운트",
            "(admin 로그인)",
            "/agents/multi-chat 진입",
            "다중 패널 UI 가시",
            "safe", "auto", "admin",
        ),
        TestCase(
            "AH-SP-121", "AgentPublicChat", "공개 챗봇", "/chatbot/test",
            "잘못된 code → 404 또는 한국어 에러",
            "(미로그인)",
            "/chatbot/nonexistent 진입",
            "404 페이지 또는 '에이전트를 찾을 수 없습니다' 메시지",
            "safe", "auto", "anon",
        ),
        TestCase(
            "AH-SP-122", "AgentEmbed", "임베드", "/embed/test",
            "잘못된 code → 에러 표시",
            "(미로그인)",
            "/embed/nonexistent 진입",
            "404 또는 에러 메시지",
            "safe", "auto", "anon",
        ),
    ])

    # ─── 후속 (시나리오 3, 4 인용) ───
    sp.extend([
        TestCase(
            "AH-SP-130", "ALL", "전역 — DocUtil 502 fallback", "",
            "[시나리오 3 인용] AdminDocUtil* 13개 화면에서 DocUtil 502 시 한국어 에러 fallback",
            "트랙 #75 commit b7de919 참조",
            "(자동화 완료 — 재실행 안 함)",
            "PASS (시나리오 3 결과 인용)",
            "safe", "manual", "admin",
            "tools/ui_e2e/scenario_3_fail_fix.py 결과 참조",
        ),
        TestCase(
            "AH-SP-131", "ALL", "전역 — DocUtil 로그인 확인", "",
            "[시나리오 4 인용] DocUtil 자격증명 미확보 확인",
            "트랙 #75 commit 3542e33 참조",
            "(자동화 완료 — 재실행 안 함)",
            "SKIP (시나리오 4 결과 인용 — DocUtil 자격증명 제공 시 진행)",
            "safe", "manual", "admin",
            "tools/ui_e2e/scenario_4_docutil.py 결과 참조",
        ),
    ])

    return sp


def build_all_cases() -> list[TestCase]:
    """전체 케이스 카탈로그 빌드."""
    all_cases: list[TestCase] = []
    rid = 1
    # Public (admin 세션 보유 상태에서 진입 + anonymous 진입 양쪽)
    for screen, path, _vue in PUBLIC_ROUTES:
        cases = _make_cases_for_route(rid, screen, screen, path, is_public=True)
        all_cases.extend(cases)
        rid += 1
    # Protected
    for screen, path, _vue in PROTECTED_ROUTES:
        cases = _make_cases_for_route(rid, screen, screen, path, is_public=False)
        all_cases.extend(cases)
        rid += 1

    # DocUtil
    drid = 1
    for entry in DOCUTIL_ROUTES:
        screen, path, _file, role = entry
        is_anon = (role == "anon")
        cases = _make_cases_for_route(drid, screen, screen, path, is_public=is_anon, docutil=True, docutil_anon=is_anon)
        all_cases.extend(cases)
        drid += 1

    # 특수 케이스
    all_cases.extend(_make_special_cases())

    return all_cases


if __name__ == "__main__":
    cases = build_all_cases()
    by_sheet: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    by_auto: dict[str, int] = {}
    for c in cases:
        by_sheet[c.sheet] = by_sheet.get(c.sheet, 0) + 1
        by_risk[c.risk] = by_risk.get(c.risk, 0) + 1
        by_auto[c.auto] = by_auto.get(c.auto, 0) + 1
    print(f"Total cases: {len(cases)}")
    print(f"Sheets: {len(by_sheet)}")
    print(f"By risk: {by_risk}")
    print(f"By auto: {by_auto}")
