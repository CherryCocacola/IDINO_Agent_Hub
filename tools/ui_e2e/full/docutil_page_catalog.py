"""트랙 #105 Phase C.1 — DocUtil 전 페이지 버튼/인터랙션 카탈로그.

대상:
- Admin 14 page: dashboard / departments / projects / documents / admin-accounts /
                 search-scopes / api-keys / templates / agents / evaluation /
                 quotas / settings / search-test / help / quick-guide
- User 4 page: chat / my-documents / search / reports
- Designer 3 page: designer/create, designer/[documentId], designer/fill/[templateId]
- Auth 1 page: login
- Misc 2 page: / (landing redirect), /preview-host (iframe inner)
- Common Layout: header, admin-sidebar, user-sidebar

ID 규칙:
- ADM-{PAGE}-{nnn} : 운영자 페이지
- USR-{PAGE}-{nnn} : 사용자 페이지
- DSG-{PAGE}-{nnn} : 디자이너
- AUT-{PAGE}-{nnn} : 인증
- LAY-{PAGE}-{nnn} : 공통 layout (header / sidebar)
- MSC-{PAGE}-{nnn} : landing / preview-host

risk_level:
- safe     : 조회 / navigation / UI 토글 — 운영 영향 0
- mutation : create / update / delete — 운영 데이터 변경
- cost     : LLM 호출 — 외부 비용 발생

automation_mode:
- auto   : Playwright 헤드리스 자동화 가능 (URL 접근 + DOM assertion 으로 검증)
- manual : 파일 업로드/iframe postMessage 등 자동화 비용 高 — 수동 점검
- skip   : 시연/UI 만의 영역 (예: 단순 정적 텍스트) — e2e 매트릭스에 정의만, 실행은 패스
"""
from __future__ import annotations

CASES: list[dict] = [
    # ════════════════════════════════════════════════════════════════════
    # LAY — 공통 Layout (header + admin sidebar + user sidebar)
    # ════════════════════════════════════════════════════════════════════
    # Header (components/layouts/header.tsx) — admin/user 양쪽 모두 노출
    {"id": "LAY-HDR-001", "page": "(공통)", "section": "header", "button_label": "IDINO 로고 영역",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "로고 클릭은 navigation 없음 (단순 표시) — 클릭 시 화면 변동 0 확인",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-HDR-002", "page": "(공통)", "section": "header", "button_label": "관리자 화면 / 사용자 화면 전환",
     "action_type": "navigate", "api_endpoint": None,
     "expected_behavior": "admin role 일 때만 노출. /search ↔ /dashboard 토글 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-HDR-003", "page": "(공통)", "section": "header", "button_label": "세션 남은 시간 카운트다운",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "tokenExpiresAt 기반 MM:SS 표시. 5분/1분 미만 색상 전환 (green→yellow→red). 0 도달 시 자동 로그아웃",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-HDR-004", "page": "(공통)", "section": "header", "button_label": "사용자 아바타 (프로필 드롭다운 트리거)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "드롭다운 오픈/클로즈. 외부 클릭 시 자동 닫힘. (사용자 명시 결함 — 우측 상단 프로필 클릭 시 화면 리프레시만 됨)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-HDR-005", "page": "(공통)", "section": "header", "button_label": "프로필 (드롭다운 항목)",
     "action_type": "navigate", "api_endpoint": None,
     "expected_behavior": "/settings 로 navigation + 드롭다운 close",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-HDR-006", "page": "(공통)", "section": "header", "button_label": "로그아웃 (드롭다운 항목)",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/auth/logout",
     "expected_behavior": "logout 호출 + token 제거 + /login 이동",
     "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "LAY-HDR-007", "page": "(공통)", "section": "header", "button_label": "로그아웃 (헤더 우측 아이콘, desktop)",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/auth/logout",
     "expected_behavior": "동일 logout 동작 — 별도 버튼이지만 같은 핸들러",
     "risk_level": "mutation", "automation_mode": "auto"},

    # Admin Sidebar
    {"id": "LAY-ASB-001", "page": "(admin)", "section": "sidebar", "button_label": "대시보드",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/dashboard 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-002", "page": "(admin)", "section": "sidebar", "button_label": "부서/조직 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/departments 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-003", "page": "(admin)", "section": "sidebar", "button_label": "프로젝트 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/projects 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-004", "page": "(admin)", "section": "sidebar", "button_label": "문서 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/documents 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-005", "page": "(admin)", "section": "sidebar", "button_label": "사용자 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/admin-accounts 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-006", "page": "(admin)", "section": "sidebar", "button_label": "검색 범위 설정",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/search-scopes 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-007", "page": "(admin)", "section": "sidebar", "button_label": "API 키 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/api-keys 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-008", "page": "(admin)", "section": "sidebar", "button_label": "템플릿 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/templates 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-009", "page": "(admin)", "section": "sidebar", "button_label": "에이전트 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/agents 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-010", "page": "(admin)", "section": "sidebar", "button_label": "AI 품질 평가",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/evaluation 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-011", "page": "(admin)", "section": "sidebar", "button_label": "쿼터 관리",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/quotas 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-012", "page": "(admin)", "section": "sidebar", "button_label": "설정",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/settings 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-013", "page": "(admin)", "section": "sidebar", "button_label": "사이드바 접기/펼치기 (desktop)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "collapsed state 토글 (w-64 ↔ w-72)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-ASB-014", "page": "(admin)", "section": "sidebar", "button_label": "햄버거 (mobile)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "mobile overlay 사이드바 오픈 — viewport 375x812 시 햄버거 visible",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — viewport 변경 후 햄버거 button visible 확인 (e2e_helpers.viewport_override)

    # User Sidebar
    {"id": "LAY-USB-001", "page": "(user)", "section": "sidebar", "button_label": "문서 검색",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/search 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-USB-002", "page": "(user)", "section": "sidebar", "button_label": "문서 업로드",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/my-documents 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-USB-003", "page": "(user)", "section": "sidebar", "button_label": "챗봇",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/chat 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-USB-004", "page": "(user)", "section": "sidebar", "button_label": "보고서",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/reports 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-USB-005", "page": "(user)", "section": "sidebar", "button_label": "문서 디자이너 (Beta)",
     "action_type": "navigate", "api_endpoint": None, "expected_behavior": "/designer/create 이동",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "LAY-USB-006", "page": "(user)", "section": "sidebar", "button_label": "사이드바 로그아웃",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/auth/logout",
     "expected_behavior": "logout + /login 이동", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # AUT — Login
    # ════════════════════════════════════════════════════════════════════
    {"id": "AUT-LGN-001", "page": "/login", "section": "main", "button_label": "Username Input",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "input 포커스 + 입력 가능 상태", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "AUT-LGN-002", "page": "/login", "section": "main", "button_label": "Password Input",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "password type input — 마스킹 확인", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "AUT-LGN-003", "page": "/login", "section": "main", "button_label": "로그인 (form submit)",
     "action_type": "submit", "api_endpoint": "POST /api/v1/auth/login",
     "expected_behavior": "유효 credential → role 별 redirect (admin → /dashboard, user → /search)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "AUT-LGN-004", "page": "/login", "section": "main", "button_label": "로그인 (오류 credential)",
     "action_type": "submit", "api_endpoint": "POST /api/v1/auth/login",
     "expected_behavior": "401 에러 → 한국어 토스트 표시", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # MSC — landing / preview-host
    # ════════════════════════════════════════════════════════════════════
    {"id": "MSC-LDG-001", "page": "/", "section": "main", "button_label": "(자동 redirect)",
     "action_type": "navigate", "api_endpoint": None,
     "expected_behavior": "인증 안 됨 → /login. admin → /dashboard. user → /search",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "MSC-PVH-001", "page": "/preview-host", "section": "iframe", "button_label": "preview-host 컴포넌트 클릭",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "iframe 내부 — postMessage docutil/element-select 부모에 전송 (iframe mount 만 검증)",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — iframe DOM mount 까지만 검증 (postMessage 자체는 별도 e2e)

    # ════════════════════════════════════════════════════════════════════
    # ADM — Dashboard (/dashboard)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-DASH-001", "page": "/dashboard", "section": "main", "button_label": "(페이지 진입 — 4개 메트릭 API 동시 호출)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/dashboard/{metrics,upload-status,response-times,search-errors}",
     "expected_behavior": "4개 fetch 병렬 + skeleton → 메트릭 카드/차트 렌더링",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-002", "page": "/dashboard", "section": "main", "button_label": "검색 사용자 수 카드",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "MetricCard pink — active_users 표시", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-003", "page": "/dashboard", "section": "main", "button_label": "검색 기능 사용 수 카드",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "MetricCard green — feature_usage 합산값", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-004", "page": "/dashboard", "section": "main", "button_label": "등록 완료 문서 수 카드",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "MetricCard yellow — total_documents 표시", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-005", "page": "/dashboard", "section": "main", "button_label": "기능 사용 BarChart (recharts)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "검색/Q&A/챗봇/에이전트 4개 카테고리 막대 — 요청/응답/실패 stacked",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-006", "page": "/dashboard", "section": "main", "button_label": "문서 업로드 상태 도넛",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "completed/processing/waiting/error PieChart — tooltip 한국어 매핑",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-007", "page": "/dashboard", "section": "main", "button_label": "시간대별 응답 시간 LineChart",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "X=시간, Y=ms — 데이터 0 시 \"데이터가 없습니다\"", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-008", "page": "/dashboard", "section": "main", "button_label": "날짜별 검색 오류 수 BarChart",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "errors 빨강 막대", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DASH-009", "page": "/dashboard", "section": "main", "button_label": "30 초 자동 새로고침",
     "action_type": "click", "api_endpoint": "GET /api/v1/dashboard/*",
     "expected_behavior": "setInterval 30000ms — 4개 API 재호출 — ApiCallCounter 로 32s 대기 후 호출 ≥1 확인",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — ApiCallCounter 로 dashboard API 호출 횟수 검증 (32s 대기)

    # ════════════════════════════════════════════════════════════════════
    # ADM — Departments (/departments)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-DEP-001", "page": "/departments", "section": "main", "button_label": "(페이지 진입 — 트리 로드)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/organizations/{orgId}/departments?tree=true",
     "expected_behavior": "부서 트리 + 조직 이름 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-002", "page": "/departments", "section": "main", "button_label": "부서 검색 input",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "client-side filter — 트리 노드 표시/숨김", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-003", "page": "/departments", "section": "main", "button_label": "회사명 인라인 수정 펜",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Input + 저장/취소 버튼 노출", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-004", "page": "/departments", "section": "main", "button_label": "회사명 저장 (체크)",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/organizations/{orgId}",
     "expected_behavior": "회사명 update — 성공 토스트", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DEP-005", "page": "/departments", "section": "main", "button_label": "부서 생성 (헤더 버튼)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 — 부서명/상위 부서 입력", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-006", "page": "/departments", "section": "modal", "button_label": "부서 생성 다이얼로그 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/organizations/{orgId}/departments",
     "expected_behavior": "부서 생성 + 트리 refetch + 성공 토스트", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DEP-007", "page": "/departments", "section": "main", "button_label": "트리 노드 펼침/접기 (chevron)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "expandedNodes Set 토글", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-008", "page": "/departments", "section": "main", "button_label": "트리 노드 선택",
     "action_type": "click", "api_endpoint": "GET /api/v1/organizations/{orgId}/departments/{deptId}/members",
     "expected_behavior": "우측 패널 — 멤버 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-009", "page": "/departments", "section": "main", "button_label": "트리 노드 호버 — 하위 부서 추가",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (parent_id 자동 채움)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-010", "page": "/departments", "section": "main", "button_label": "트리 노드 호버 — 부서 수정",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (수정 모드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-011", "page": "/departments", "section": "modal", "button_label": "부서 수정 다이얼로그 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/organizations/{orgId}/departments/{id}",
     "expected_behavior": "부서 update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DEP-012", "page": "/departments", "section": "main", "button_label": "트리 노드 호버 — 부서장 지정",
     "action_type": "click", "api_endpoint": "GET /api/v1/users/?org_id=...",
     "expected_behavior": "사용자 목록 fetch + Dialog 오픈", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-013", "page": "/departments", "section": "modal", "button_label": "부서장 지정 다이얼로그 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/organizations/{orgId}/departments/{id}/head",
     "expected_behavior": "head_user_id update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DEP-014", "page": "/departments", "section": "main", "button_label": "트리 노드 호버 — 부서 삭제",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "AlertDialog 오픈 (하위 부서 경고)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-015", "page": "/departments", "section": "modal", "button_label": "부서 삭제 확정",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/organizations/{orgId}/departments/{id}",
     "expected_behavior": "부서 삭제 + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DEP-016", "page": "/departments", "section": "main", "button_label": "멤버 추가 (우측 패널)",
     "action_type": "click", "api_endpoint": "GET /api/v1/users/?org_id=...",
     "expected_behavior": "Dialog 오픈 + 사용자 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DEP-017", "page": "/departments", "section": "modal", "button_label": "멤버 추가 확정",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/organizations/{orgId}/departments/{id}/members",
     "expected_behavior": "멤버 추가 + 목록 refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DEP-018", "page": "/departments", "section": "main", "button_label": "멤버 제거 (UserMinus 아이콘)",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/organizations/{orgId}/departments/{id}/members/{uid}",
     "expected_behavior": "멤버 제거 + refetch", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Projects (/projects)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-PRJ-001", "page": "/projects", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/projects",
     "expected_behavior": "프로젝트 목록 + 부서 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-002", "page": "/projects", "section": "main", "button_label": "프로젝트 검색 input",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "client-side filter (이름/설명)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-003", "page": "/projects", "section": "main", "button_label": "프로젝트 생성 (헤더)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (이름/설명/부서/원본 다운로드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-004", "page": "/projects", "section": "modal", "button_label": "프로젝트 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/projects (생성) / PUT /api/v1/projects/{id} (수정)",
     "expected_behavior": "프로젝트 create/update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-PRJ-005", "page": "/projects", "section": "main", "button_label": "프로젝트 행 펼침/접기",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "expandedProjects 토글 + breadcrumb 업데이트", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-006", "page": "/projects", "section": "main", "button_label": "프로젝트 행 ⋯ 메뉴 — 수정",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (수정 모드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-007", "page": "/projects", "section": "main", "button_label": "프로젝트 행 ⋯ 메뉴 — 멤버 관리",
     "action_type": "click", "api_endpoint": "GET /api/v1/projects/{id}/members",
     "expected_behavior": "멤버 다이얼로그 + 멤버 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-008", "page": "/projects", "section": "modal", "button_label": "프로젝트 멤버 추가",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/projects/{id}/members",
     "expected_behavior": "멤버 추가 + role(manager/member) 지정", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-PRJ-009", "page": "/projects", "section": "modal", "button_label": "프로젝트 멤버 제거",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/projects/{id}/members/{uid}",
     "expected_behavior": "멤버 제거 + 목록 갱신", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-PRJ-010", "page": "/projects", "section": "main", "button_label": "프로젝트 행 ⋯ 메뉴 — 보드 추가",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "보드 Dialog 오픈", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-011", "page": "/projects", "section": "modal", "button_label": "보드 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/projects/{id}/boards (생성) / PUT /.../boards/{id} (수정)",
     "expected_behavior": "보드 create/update + 프로젝트 refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-PRJ-012", "page": "/projects", "section": "main", "button_label": "프로젝트 행 ⋯ 메뉴 — 삭제",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "AlertDialog 오픈", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-013", "page": "/projects", "section": "modal", "button_label": "프로젝트/보드/폴더 삭제 확정",
     "action_type": "mutation",
     "api_endpoint": "DELETE /api/v1/projects/{id} | /api/v1/projects/{pid}/boards/{bid} | /api/v1/boards/{bid}/folders/{fid}",
     "expected_behavior": "type 별 endpoint 분기 + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-PRJ-014", "page": "/projects", "section": "main", "button_label": "보드 행 ⋯ 메뉴 — 수정/폴더 추가/삭제",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "각각 Dialog/AlertDialog 오픈", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-015", "page": "/projects", "section": "modal", "button_label": "폴더 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/boards/{bid}/folders (생성) / PUT (수정)",
     "expected_behavior": "폴더 create/update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-PRJ-016", "page": "/projects", "section": "modal", "button_label": "부서 multi-select 체크박스",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "자신 + 하위 부서 모두 선택/해제 (계층적 토글)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-PRJ-017", "page": "/projects", "section": "modal", "button_label": "원본 문서 다운로드 허용 Switch",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "allow_original_download 토글", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Documents (/documents)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-DOC-001", "page": "/documents", "section": "main", "button_label": "(페이지 진입 — 트리 + 목록)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/projects (트리) + /api/v1/documents (목록)",
     "expected_behavior": "프로젝트 트리 + 문서 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-002", "page": "/documents", "section": "main", "button_label": "트리 — 프로젝트/보드 펼침",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "toggleTreeNode Set 토글", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-003", "page": "/documents", "section": "main", "button_label": "트리 — 폴더 선택",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents?folder_id=...",
     "expected_behavior": "선택된 폴더의 문서만 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-004", "page": "/documents", "section": "main", "button_label": "파일 업로드 버튼",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "<input type=\"file\"> 클릭 트리거 + 업로드 모달 — input[type=file] selector 존재만 검증",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — input[type=file] selector 존재만 검증 (실제 업로드는 ADM-DOC-005)
    {"id": "ADM-DOC-005", "page": "/documents", "section": "modal", "button_label": "업로드 확정",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/documents/upload (multipart)",
     "expected_behavior": "파일 업로드 + 청크 분할 + 임베딩 큐 (Celery) — 운영 영향 큼 — manual 유지",
     "risk_level": "mutation", "automation_mode": "manual"},
    # ↑ Phase C 보강 — 실제 업로드는 임베딩 큐 (Celery) + Qdrant 영향 — 운영 보호 위해 manual 유지.
    # 자동화 시 별도 mutation runner 에서 E2E_ALLOW_MUTATION=1 + cleanup 보장 필요.
    {"id": "ADM-DOC-006", "page": "/documents", "section": "main", "button_label": "문서 행 클릭 — 상세",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents/{id}",
     "expected_behavior": "상세 패널 표시 (메타/벡터 상태)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-007", "page": "/documents", "section": "main", "button_label": "문서 행 — 접근 권한",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents/{id}/access + /api/v1/users/?org_id=...",
     "expected_behavior": "접근 권한 다이얼로그 오픈", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-008", "page": "/documents", "section": "modal", "button_label": "접근 권한 추가",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/documents/{id}/access",
     "expected_behavior": "사용자 접근 권한 부여", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DOC-009", "page": "/documents", "section": "modal", "button_label": "접근 권한 제거",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/documents/{id}/access/{uid}",
     "expected_behavior": "사용자 접근 권한 제거", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DOC-010", "page": "/documents", "section": "main", "button_label": "문서 행 — 다운로드",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents/{id}/download",
     "expected_behavior": "원본 파일 다운로드 (RFC 5987 한글 파일명) — download_file() 헬퍼 — binary size ≥ 100B 검증",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — download_file() 헬퍼 — 첫 행의 다운로드 버튼 클릭 → binary size 검증
    {"id": "ADM-DOC-011", "page": "/documents", "section": "main", "button_label": "문서 행 — 삭제",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "AlertDialog 오픈", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-012", "page": "/documents", "section": "modal", "button_label": "문서 삭제 확정",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/documents/{id}",
     "expected_behavior": "문서 + Qdrant 벡터 + MinIO 파일 삭제", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-DOC-013", "page": "/documents", "section": "main", "button_label": "페이지네이션 이전",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents?page=N-1",
     "expected_behavior": "currentPage 감소", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-DOC-014", "page": "/documents", "section": "main", "button_label": "페이지네이션 다음",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents?page=N+1",
     "expected_behavior": "currentPage 증가", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Admin Accounts (/admin-accounts)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-ACC-001", "page": "/admin-accounts", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/users/ + /api/v1/departments",
     "expected_behavior": "사용자 목록 + 부서 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-ACC-002", "page": "/admin-accounts", "section": "main", "button_label": "사용자 생성 (헤더)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (username/email/password/role/department)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-ACC-003", "page": "/admin-accounts", "section": "modal", "button_label": "사용자 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/users/ (생성) / PUT /api/v1/users/{id} (수정)",
     "expected_behavior": "사용자 create/update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-ACC-004", "page": "/admin-accounts", "section": "main", "button_label": "사용자 행 수정",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (수정 모드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-ACC-005", "page": "/admin-accounts", "section": "main", "button_label": "사용자 활성화",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/users/{id}/activate",
     "expected_behavior": "is_active=true 변경", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-ACC-006", "page": "/admin-accounts", "section": "main", "button_label": "사용자 비활성화",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/users/{id}/deactivate",
     "expected_behavior": "is_active=false 변경", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-ACC-007", "page": "/admin-accounts", "section": "main", "button_label": "사용자 잠금 해제",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/users/{id}/unlock",
     "expected_behavior": "failed_login_count=0 + lock 해제", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Search Scopes (/search-scopes)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-SCP-001", "page": "/search-scopes", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/search-scopes",
     "expected_behavior": "검색 범위 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-SCP-002", "page": "/search-scopes", "section": "main", "button_label": "검색 범위 생성",
     "action_type": "click", "api_endpoint": "GET /api/v1/search-scopes/locations",
     "expected_behavior": "Dialog 오픈 + 위치(프로젝트/보드/폴더) 트리 fetch",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-SCP-003", "page": "/search-scopes", "section": "modal", "button_label": "검색 범위 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/search-scopes (생성) / PUT /api/v1/search-scopes/{id} (수정)",
     "expected_behavior": "scope create/update + 위치 매핑", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-SCP-004", "page": "/search-scopes", "section": "main", "button_label": "검색 범위 수정",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (수정 모드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-SCP-005", "page": "/search-scopes", "section": "main", "button_label": "검색 범위 삭제",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/search-scopes/{id}",
     "expected_behavior": "scope 삭제 + refetch", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — API Keys (/api-keys)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-KEY-001", "page": "/api-keys", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/admin/api-keys",
     "expected_behavior": "API Key 목록 fetch (provider/모델/마스킹된 key 표시)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-KEY-002", "page": "/api-keys", "section": "main", "button_label": "API Key 등록",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (provider/name/api_key/model 입력)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-KEY-003", "page": "/api-keys", "section": "modal", "button_label": "API Key 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/admin/api-keys",
     "expected_behavior": "key 암호화 저장 + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-KEY-004", "page": "/api-keys", "section": "main", "button_label": "API Key 검증",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/admin/api-keys/{id}/verify",
     "expected_behavior": "외부 LLM 호출 검증 (cost 발생 — 짧은 ping 메시지)",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "ADM-KEY-005", "page": "/api-keys", "section": "main", "button_label": "API Key 삭제",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/admin/api-keys/{id}",
     "expected_behavior": "key 삭제 + refetch", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Templates (/templates)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-TPL-001", "page": "/templates", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/templates",
     "expected_behavior": "템플릿 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-TPL-002", "page": "/templates", "section": "main", "button_label": "템플릿 생성 (5-step wizard)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 — step 1 (기본 정보)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-TPL-003", "page": "/templates", "section": "modal", "button_label": "Smart Upload (LLM 변수 추출)",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/templates/smart-analyze (multipart)",
     "expected_behavior": "PPTX/DOCX 업로드 → LLM 변수 자동 추출 (cost)",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "ADM-TPL-004", "page": "/templates", "section": "modal", "button_label": "Step 별 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/templates (step 1) / PUT (step 2~5)",
     "expected_behavior": "step 별 partial save", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-TPL-005", "page": "/templates", "section": "modal", "button_label": "템플릿 파일 교체",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/templates/{id}/file (multipart)",
     "expected_behavior": "MinIO 파일 교체 — 운영 template 영향 위험 (HIGH). 자동화 비권장.",
     "risk_level": "mutation", "automation_mode": "manual"},
    # ↑ Phase C 보강 — manual 유지. 운영 template 파일이 영향받음 (rollback 어려움 — MinIO 원본 덮어쓰기).
    {"id": "ADM-TPL-006", "page": "/templates", "section": "main", "button_label": "템플릿 수정",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (수정 모드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-TPL-007", "page": "/templates", "section": "main", "button_label": "템플릿 삭제",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/templates/{id}",
     "expected_behavior": "템플릿 삭제 + MinIO 파일 삭제", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Agents (/agents)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-AGT-001", "page": "/agents", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/agents",
     "expected_behavior": "Agent 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-AGT-002", "page": "/agents", "section": "main", "button_label": "Agent 생성",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (name/agent_type/system_prompt/temperature/max_tokens)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-AGT-003", "page": "/agents", "section": "modal", "button_label": "Agent 저장",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/agents (생성) / PUT /api/v1/agents/{id} (수정)",
     "expected_behavior": "Agent create/update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-AGT-004", "page": "/agents", "section": "main", "button_label": "Agent 수정",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Dialog 오픈 (수정 모드)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-AGT-005", "page": "/agents", "section": "main", "button_label": "Agent 삭제",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/agents/{id}",
     "expected_behavior": "Agent 삭제 + refetch", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Evaluation (/evaluation)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-EVL-001", "page": "/evaluation", "section": "main", "button_label": "(페이지 진입 — runs/trend/config)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/evaluation/{runs,trend,config}",
     "expected_behavior": "평가 실행 목록 + 트렌드 + 설정 fetch (3개 병렬)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-EVL-002", "page": "/evaluation", "section": "main", "button_label": "평가 실행",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/evaluation/run",
     "expected_behavior": "평가 작업 큐잉 (LLM judge 호출 — cost 발생)",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "ADM-EVL-003", "page": "/evaluation", "section": "main", "button_label": "설정 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/evaluation/config",
     "expected_behavior": "평가 config update (judge model/threshold)", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-EVL-004", "page": "/evaluation", "section": "main", "button_label": "실행 상세 보기",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/evaluation/runs/{id}/logs",
     "expected_behavior": "실행 로그 + 케이스별 결과 표시", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Quotas (/quotas)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-QTA-001", "page": "/quotas", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/admin/quotas",
     "expected_behavior": "쿼터 종류별 현황 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-QTA-002", "page": "/quotas", "section": "main", "button_label": "쿼터 수정 시작 (펜)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "인라인 input 모드 전환", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-QTA-003", "page": "/quotas", "section": "main", "button_label": "쿼터 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/admin/quotas/{type}",
     "expected_behavior": "쿼터 limit update + refetch", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-QTA-004", "page": "/quotas", "section": "main", "button_label": "조직 일괄 적용",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/admin/quotas/apply-org",
     "expected_behavior": "조직 전체 쿼터 일괄 적용", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-QTA-005", "page": "/quotas", "section": "main", "button_label": "수정 취소",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "인라인 input 닫기 (변경사항 폐기)", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Settings (/settings)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-SET-001", "page": "/settings", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/settings",
     "expected_behavior": "general/security/storage 3개 섹션 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-SET-002", "page": "/settings", "section": "main", "button_label": "General 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/settings/general",
     "expected_behavior": "일반 설정 update", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-SET-003", "page": "/settings", "section": "main", "button_label": "Security 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/settings/security",
     "expected_behavior": "보안 설정 update", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-SET-004", "page": "/settings", "section": "main", "button_label": "Storage 저장",
     "action_type": "mutation", "api_endpoint": "PUT /api/v1/settings/storage",
     "expected_behavior": "스토리지 설정 update", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "ADM-SET-005", "page": "/settings", "section": "main", "button_label": "고아 벡터 정리 실행",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/maintenance/cleanup-orphaned-vectors",
     "expected_behavior": "Qdrant 중 DB 에 없는 벡터 삭제 — 자동화 비권장 — manual 유지",
     "risk_level": "mutation", "automation_mode": "manual"},
    # ↑ Phase C 보강 — manual 유지. 운영 Qdrant 영향 큼 (rollback 어려움 — 벡터 영구 삭제).

    # ════════════════════════════════════════════════════════════════════
    # ADM — Search Test (/search-test)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-SCH-001", "page": "/search-test", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/search-scopes + /api/v1/search/history",
     "expected_behavior": "검색 범위 + 이력 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-SCH-002", "page": "/search-test", "section": "main", "button_label": "검색어 input",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "Enter 키 → handleSearch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-SCH-003", "page": "/search-test", "section": "main", "button_label": "검색 실행",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/search",
     "expected_behavior": "hybrid 검색 (dense + BM25) — 임베딩 호출 cost", "risk_level": "cost", "automation_mode": "manual"},
    {"id": "ADM-SCH-004", "page": "/search-test", "section": "main", "button_label": "검색 범위 selector",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "scope_id 변경 → 다음 검색에 적용", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # ADM — Help / Quick Guide (정적)
    # ════════════════════════════════════════════════════════════════════
    {"id": "ADM-HLP-001", "page": "/help", "section": "main", "button_label": "FAQ 검색 input",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "client-side FAQ filter", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-HLP-002", "page": "/help", "section": "main", "button_label": "Accordion 항목 펼침",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "AccordionItem expand/collapse", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "ADM-HLP-003", "page": "/help", "section": "main", "button_label": "이메일 mailto 링크",
     "action_type": "navigate", "api_endpoint": None,
     "expected_behavior": "mailto: 핸들러 호출", "risk_level": "safe", "automation_mode": "skip"},
    {"id": "ADM-QGD-001", "page": "/quick-guide", "section": "main", "button_label": "가이드 카드 표시",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "5개 가이드 (업로드/범위/채팅/검색/설정) 정적 표시",
     "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # USR — Chat (/chat)
    # ════════════════════════════════════════════════════════════════════
    {"id": "USR-CHT-001", "page": "/chat", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/chat/sessions + /api/v1/agents?type=chatbot",
     "expected_behavior": "세션 목록 + chatbot agent 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-002", "page": "/chat", "section": "sidebar", "button_label": "새 채팅 (사이드바)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "DocumentScopeModal 오픈 (channel: 새 채팅)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-003", "page": "/chat", "section": "sidebar", "button_label": "기본 에이전트 selector",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "selectedChatAgentId 변경 — 다음 메시지에 적용", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-004", "page": "/chat", "section": "sidebar", "button_label": "세션 항목 클릭",
     "action_type": "click", "api_endpoint": "GET /api/v1/chat/sessions/{id}/messages",
     "expected_behavior": "activeSessionId 설정 + 메시지 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-005", "page": "/chat", "section": "sidebar", "button_label": "세션 삭제 (호버 휴지통)",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/chat/sessions/{id}",
     "expected_behavior": "세션 삭제 + 목록 업데이트", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "USR-CHT-006", "page": "/chat", "section": "main", "button_label": "세션 설정 (Settings2 아이콘)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "DocumentScopeModal 오픈 (channel: 범위 수정)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-007", "page": "/chat", "section": "modal", "button_label": "DocumentScopeModal — 확정",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/chat/sessions (새 세션) or PATCH (범위 수정)",
     "expected_behavior": "scopedDocumentIds 저장 + 세션 생성/업데이트", "risk_level": "mutation", "automation_mode": "auto"},
    {"id": "USR-CHT-008", "page": "/chat", "section": "main", "button_label": "심층 검색 토글",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "deepSearch state 토글 (다음 메시지에 적용)", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-009", "page": "/chat", "section": "main", "button_label": "메시지 textarea — 자동 높이",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "줄바꿈 시 자동 높이 (max 200px) — Shift+Enter 줄바꿈, Enter 전송",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-CHT-010", "page": "/chat", "section": "main", "button_label": "메시지 전송 (Send 아이콘)",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/chat/sessions/{id}/messages (SSE stream)",
     "expected_behavior": "WebSocket/SSE 스트리밍 — LLM 호출 cost. citations 포함 응답",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "USR-CHT-011", "page": "/chat", "section": "main", "button_label": "스트리밍 중지 (Square 아이콘)",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/chat/sessions/{id}/stop",
     "expected_behavior": "AbortController + 부분 응답 유지", "risk_level": "mutation", "automation_mode": "manual"},
    {"id": "USR-CHT-012", "page": "/chat", "section": "main", "button_label": "응답 메시지 — 출처(citation) 클릭",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "출처 문서 detail 오픈/highlight", "risk_level": "safe", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # USR — My Documents (/my-documents)
    # ════════════════════════════════════════════════════════════════════
    {"id": "USR-MDC-001", "page": "/my-documents", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/documents?mine=true + /api/v1/user/scope",
     "expected_behavior": "내 문서 목록 + 사용자 scope fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-MDC-002", "page": "/my-documents", "section": "main", "button_label": "파일 업로드",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/documents/upload (multipart)",
     "expected_behavior": "내 영역에 문서 업로드 + 임베딩 큐 — manual 유지 (cleanup 의무)",
     "risk_level": "mutation", "automation_mode": "manual"},
    # ↑ Phase C 보강 — 사용자 영역 업로드도 임베딩 큐 (Celery) 트리거 — manual 유지 (별도 mutation runner)
    {"id": "USR-MDC-003", "page": "/my-documents", "section": "main", "button_label": "문서 행 — 상세",
     "action_type": "click", "api_endpoint": "GET /api/v1/documents/{id}",
     "expected_behavior": "상세 패널", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-MDC-004", "page": "/my-documents", "section": "main", "button_label": "문서 삭제",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/documents/{id}",
     "expected_behavior": "문서 + 벡터 삭제", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # USR — Search (/search)
    # ════════════════════════════════════════════════════════════════════
    {"id": "USR-SRC-001", "page": "/search", "section": "main", "button_label": "검색 form submit",
     "action_type": "submit", "api_endpoint": "POST /api/v1/search",
     "expected_behavior": "hybrid 검색 (임베딩 호출 — cost)", "risk_level": "cost", "automation_mode": "manual"},
    {"id": "USR-SRC-002", "page": "/search", "section": "main", "button_label": "검색 결과 — 보고서 생성 다이얼로그",
     "action_type": "click", "api_endpoint": "GET /api/v1/templates?type=report",
     "expected_behavior": "보고서 다이얼로그 + 템플릿 목록 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-SRC-003", "page": "/search", "section": "modal", "button_label": "보고서 템플릿 변경",
     "action_type": "click", "api_endpoint": "GET /api/v1/templates/{id}",
     "expected_behavior": "변수 메타 + Jinja2 슬롯 fetch", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-SRC-004", "page": "/search", "section": "modal", "button_label": "보고서 생성 실행",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/reports/generate",
     "expected_behavior": "Celery 비동기 — Structured Outputs LLM 호출 (cost)",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "USR-SRC-005", "page": "/search", "section": "modal", "button_label": "디자이너 모드로 생성 → designer 이동",
     "action_type": "navigate", "api_endpoint": "POST /api/v1/v2/documents",
     "expected_behavior": "/designer/{document_id} 이동 — LLM 호출 cost",
     "risk_level": "cost", "automation_mode": "manual"},
    # ↑ Phase C 보강 — cost — manual 유지. /search 진입까지만 검증 (E2E_ALLOW_COST=1 시 cost runner)

    # ════════════════════════════════════════════════════════════════════
    # USR — Reports (/reports)
    # ════════════════════════════════════════════════════════════════════
    {"id": "USR-RPT-001", "page": "/reports", "section": "main", "button_label": "(페이지 진입 — 410 fallback 대응)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/reports + /api/v1/templates?type=report",
     "expected_behavior": "보고서 목록 + 템플릿 fetch. 410 → 디자이너 신 시스템 유도",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-RPT-002", "page": "/reports", "section": "main", "button_label": "템플릿 선택",
     "action_type": "click", "api_endpoint": "GET /api/v1/templates/{id}",
     "expected_behavior": "변수 form 표시 (user_input + ai_generated 분류)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-RPT-003", "page": "/reports", "section": "main", "button_label": "Jinja2 변수 입력 (텍스트/이미지)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "fieldName/value 매핑 state update", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-RPT-004", "page": "/reports", "section": "main", "button_label": "이미지 변수 소스 선택 (AI/Unsplash)",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "imageVarSource 토글", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "USR-RPT-005", "page": "/reports", "section": "main", "button_label": "미리보기",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/reports/{templateId}/preview",
     "expected_behavior": "샘플 데이터로 렌더링", "risk_level": "safe", "automation_mode": "manual"},
    {"id": "USR-RPT-006", "page": "/reports", "section": "main", "button_label": "보고서 생성",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/reports/generate",
     "expected_behavior": "Celery + Structured Outputs LLM (cost). DOCX/PPTX 생성",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "USR-RPT-007", "page": "/reports", "section": "main", "button_label": "디자이너로 이동",
     "action_type": "navigate", "api_endpoint": "POST /api/v1/v2/documents",
     "expected_behavior": "/designer/{document_id} 이동 — LLM 호출 cost 발생",
     "risk_level": "cost", "automation_mode": "manual"},
    # ↑ Phase C 보강 — cost — manual 유지. E2E_ALLOW_COST=1 시에만 cost runner 별도 실행.
    {"id": "USR-RPT-008", "page": "/reports", "section": "main", "button_label": "보고서 다운로드",
     "action_type": "click", "api_endpoint": "GET /api/v1/reports/{id}/download",
     "expected_behavior": "DOCX/PPTX 다운로드 (RFC 5987) — download_file() 헬퍼",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — download_file() 헬퍼 — 첫 보고서 다운로드 (없으면 SKIP)
    {"id": "USR-RPT-009", "page": "/reports", "section": "main", "button_label": "보고서 삭제",
     "action_type": "mutation", "api_endpoint": "DELETE /api/v1/reports/{id}",
     "expected_behavior": "보고서 record + MinIO 파일 삭제", "risk_level": "mutation", "automation_mode": "auto"},

    # ════════════════════════════════════════════════════════════════════
    # DSG — Designer (Mode A 자유 생성)
    # ════════════════════════════════════════════════════════════════════
    {"id": "DSG-CRT-001", "page": "/designer/create", "section": "main", "button_label": "(페이지 진입 — DesignerShell)",
     "action_type": "navigate", "api_endpoint": None,
     "expected_behavior": "3분할 레이아웃 — PromptBox / PreviewPane (iframe) / DesignTokenPicker",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "DSG-CRT-002", "page": "/designer/create", "section": "main", "button_label": "PromptBox 입력 + 생성",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/v2/documents",
     "expected_behavior": "LLM 호출 (cost) + DocumentSchema 생성 + 자동 replace /designer/{id}",
     "risk_level": "cost", "automation_mode": "manual"},
    {"id": "DSG-CRT-003", "page": "/designer/create", "section": "main", "button_label": "DocumentType 선택",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "type select (slide_report 등) — 다음 생성에 적용",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "DSG-CRT-004", "page": "/designer/create", "section": "main", "button_label": "DesignTokenPicker 변경",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "color/font token 변경 → iframe postMessage", "risk_level": "safe", "automation_mode": "auto"},
    {"id": "DSG-DID-001", "page": "/designer/[documentId]", "section": "main", "button_label": "(페이지 진입)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/v2/documents/{id}",
     "expected_behavior": "DocumentSchema fetch + store 주입 + DesignerShell 렌더",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "DSG-DID-002", "page": "/designer/[documentId]", "section": "iframe", "button_label": "PreviewPane 요소 클릭",
     "action_type": "click", "api_endpoint": None,
     "expected_behavior": "iframe postMessage docutil/element-select → EditSidebar 열림 (iframe mount 만 검증)",
     "risk_level": "safe", "automation_mode": "auto"},
    # ↑ Phase C 보강 — iframe_mounted() 만 검증. postMessage 자체는 designer document 가 있어야 작동
    {"id": "DSG-DID-003", "page": "/designer/[documentId]", "section": "main", "button_label": "EditSidebar 속성 변경",
     "action_type": "mutation", "api_endpoint": "PATCH /api/v1/v2/documents/{id}",
     "expected_behavior": "schema patch 전송 + iframe 재렌더 — vue-flow 동적 selector 안정성 낮음",
     "risk_level": "mutation", "automation_mode": "manual"},
    # ↑ Phase C 보강 — manual 유지. vue-flow 의 동적 노드 조작은 selector 안정성 낮음 (자동화 비용 > 이익)
    {"id": "DSG-DID-004", "page": "/designer/[documentId]", "section": "main", "button_label": "내보내기 (PPTX/PDF)",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/v2/documents/{id}/export",
     "expected_behavior": "Celery 변환 → MinIO 저장 — 실제 document 필요 (선행 mutation 의존)",
     "risk_level": "mutation", "automation_mode": "manual"},
    # ↑ Phase C 보강 — manual 유지. designer document 가 선행되어야 함 (시나리오 의존도 高)
    {"id": "DSG-FIL-001", "page": "/designer/fill/[templateId]", "section": "main", "button_label": "(페이지 진입 — Mode B)",
     "action_type": "navigate", "api_endpoint": "GET /api/v1/templates/{id}",
     "expected_behavior": "템플릿 기반 빈 폼 표시 (variables 자동 분류)",
     "risk_level": "safe", "automation_mode": "auto"},
    {"id": "DSG-FIL-002", "page": "/designer/fill/[templateId]", "section": "main", "button_label": "변수 채우기 → 생성",
     "action_type": "mutation", "api_endpoint": "POST /api/v1/v2/documents/from-template/{id}",
     "expected_behavior": "LLM 호출 (cost) + DocumentSchema 생성", "risk_level": "cost", "automation_mode": "manual"},
]


# ════════════════════════════════════════════════════════════════════════
# 통계
# ════════════════════════════════════════════════════════════════════════

def stats() -> dict:
    """카탈로그 통계 산출."""
    from collections import Counter
    by_page = Counter(c["page"] for c in CASES)
    by_risk = Counter(c["risk_level"] for c in CASES)
    by_auto = Counter(c["automation_mode"] for c in CASES)
    by_action = Counter(c["action_type"] for c in CASES)
    return {
        "total": len(CASES),
        "by_page": dict(by_page),
        "by_risk_level": dict(by_risk),
        "by_automation_mode": dict(by_auto),
        "by_action_type": dict(by_action),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
