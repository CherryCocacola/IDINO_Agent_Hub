# 트랙 #105 Phase A.1 — 챗봇 문서 선택 0건 결함 진단 보고서

**작성일**: 2026-05-20
**진단 대상**: DocUtil 사용자 챗봇(/chat) 의 `DocumentScopeModal` 에서 선택 가능한 문서가 0건으로 노출되는 결함
**관련 사용자 보고**: 트랙 #105 사용자 요청 0-2-1 / 1-3
**전제 트랙**: 트랙 #104 (2026-05-19, 'user' role 누락 fix — documents/documents_v2/agents 3 router 만 처리)

---

## 1. 사용자 보고

> "사용자화면 - 문서 업로드 에서 전체공개 문서들이 보이는데, 챗봇에서는 선택할 수 있는 문서가 없어 (권한에 문제가 있는건 아닌지)"

- 영향 계정: hslee (DB 정보 — id=`b54f6c80-...`, **role='user'**, dept=NULL, org=000001)
- 정상 동작 기대: `/documents` 페이지에서 보이는 public 30 건이 챗봇의 `DocumentScopeModal` 에서도 동일하게 선택 가능해야 함
- 실제: `DocumentScopeModal` 내부 트리 0건 (미분류 노드조차 안 보임)

---

## 2. 가설 후보 (Plan 단계)

| 가설 | 내용 | 검증 결과 |
|---|---|---|
| H1 | `document-selector.tsx:108-130` 의 `/documents?size=100` 호출이 `as_user_view` 미전달 → backend visibility scope 진입 → 0건 매칭 | ❌ 기각 — `/documents` 페이지에서는 size=10/페이지네이션으로 동일하게 호출되는데 정상 노출. 또한 service.py:374-395 의 scope clauses 가 public 문서를 누락하지 않음 (트랙 #104 검증) |
| H2 | `/projects/tree` 응답은 200 인데 frontend 트리 매핑에서 unassigned 추가 로직 누락 | △ 부분 — unassigned 로직(라인 214-228)은 있으나 H5 가 원인이라 미발동 |
| H3 | `/documents?size=100` 응답 자체가 0건 (size 파라미터 분기 결함) | ❌ 기각 — backend service.py:list_documents 코드상 size 는 단순 limit 만 적용, 권한 분기에 영향 없음 |
| H4 | chat 세션 생성 endpoint 의 require_role 'user' 누락 | ❌ 기각 — `chat/router.py:32` `prefix=""`, POST `/chat/sessions` 핸들러(line 87-100)는 `CurrentUser` 만 Depends(require_role 미사용 = 모든 인증 사용자 허용). `DocumentScopeModal` 은 세션 생성 전에 열림 |
| **H5** | **`projects/router.py:52` 의 `_require_member` 화이트리스트에 'user' 누락** → `/projects/tree` 가 hslee 에 대해 **403** → frontend `Promise.all` reject → catch 진입 → 빈 배열 반환 → `DocumentSelector` 트리 0건 | **✅ 확정** |

---

## 3. 코드 정독으로 확정한 호출 흐름

### 3.1 Frontend 호출 흐름

`docutil/frontend/src/app/(user)/chat/page.tsx:845-856`
```tsx
<DocumentScopeModal
  open={showScopeModal}
  ...
/>
```
사용자가 "새 채팅" 버튼을 누르면 `showScopeModal=true` → `DocumentScopeModal` 마운트 → 내부에서 `DocumentSelector` 렌더 → `fetchDocumentTree()` 호출.

`docutil/frontend/src/components/documents/document-selector.tsx:105-235`
```ts
export async function fetchDocumentTree(): Promise<DocumentNode[]> {
  try {
    const [treeData, docsData] = await Promise.all([
      apiClient.get("/projects/tree"),                  // ★ 403 → reject
      apiClient.get("/documents", { size: "100" }),     // 200 (30 items)
    ]);
    ...
  } catch (err) {
    console.error("Failed to fetch document tree:", err);
    return [];                                          // ★ 빈 배열
  }
}
```

`Promise.all` 의 fail-fast 특성:
- 한쪽이 reject 되면 즉시 catch 진입
- `/documents` 가 200 으로 응답한 30 건은 **사용조차 안 됨**

### 3.2 Backend 권한 게이트

`docutil/backend/app/modules/projects/router.py:52`
```python
_require_member = require_role([
    "super_admin", "admin", "org_admin", "manager", "member", "editor", "viewer"
])
```
**'user' 가 빠져 있음.**

`docutil/backend/app/modules/projects/router.py:79-93`
```python
@router.get("/projects/tree")
async def get_projects_tree(
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),   # ★ 'user' role 차단
):
    ...
```
hslee (role='user') 가 호출하면 `require_role` 이 403 반환.

### 3.3 트랙 #104 fix 와의 정합성 깨짐

트랙 #104 (2026-05-19) 에서는 `documents/documents_v2/agents` 3 router 의 `_require_member` / `_require_reader` 에 'user' 추가만 진행. 같은 패턴이 다른 router 에도 있는지 전수 확인은 누락. 그 결과 `projects/reports/search_scopes/templates` 4 router 에 'user' 누락 잔존.

| Router | 헬퍼 | 라인 | 'user' 포함? | 사용자 화면 호출 여부 |
|---|---|---|---|---|
| documents | `_require_member` | 60 | ✅ (트랙 #104) | YES — /documents, /my-documents |
| documents_v2 | `_require_reader` | 73 | ✅ (트랙 #104) | YES — /documents |
| agents | `_require_member` | 40 | ✅ (트랙 #104) | YES — /agents, /chat |
| **projects** | `_require_member` | **52** | **❌** | **YES — DocumentScopeModal `/projects/tree`** |
| **reports** | `_require_member` | **64** | **❌** | Phase B 에서 frontend grep 으로 검증 예정 |
| **search_scopes** | `_require_member` | **48** | **❌** | Phase B 에서 frontend grep 으로 검증 예정 |
| **templates** | `_require_member` | **52** | **❌ + 'manager' 도 누락** | Phase B 에서 frontend grep 으로 검증 예정 |

---

## 4. Root Cause 확정

**`docutil/backend/app/modules/projects/router.py:52` 의 `_require_member` 화이트리스트에 'user' 누락.**

직접 영향: `/projects/tree` 가 hslee 에 대해 **403 Forbidden** → frontend `fetchDocumentTree()` 의 `Promise.all` reject → catch 진입 → 빈 배열 → `DocumentScopeModal` 의 트리 0건.

부수 영향: 같은 router 의 다른 `/projects` 관련 GET endpoint 도 hslee 에게 403. 즉 챗봇뿐 아니라 프로젝트 트리를 사용하는 모든 사용자 화면에서 동일 결함.

---

## 5. Phase A.2 fix 범위 (확정)

본 진단으로 Phase A.2 fix 는 Phase B.3 의 'user' 누락 일괄 fix 와 자연스럽게 묶임:

- **즉시 fix (이번 트랙 #105 Phase A.2)**: `projects/router.py:52` 의 `_require_member` 에 'user' 추가. 이것만으로 챗봇 결함은 해소.
- **묶음 fix (Phase B.3 으로 분리)**: `reports/router.py:64`, `search_scopes/router.py:48`, `templates/router.py:52` 의 동일 패턴. 사용자 화면 호출 여부 grep 후 결함 판정 → 결함이면 'user' 추가.

사용자 사전 결정(EnterPlanMode AskUserQuestion 1번): "추가 'user' 누락 발견 시 즉시 fix + 운영 배포".

---

## 6. 검증 계획 (Phase A.3)

운영 배포 후 5계정 검증:

| 계정 | role | 기대 |
|---|---|---|
| super_admin | super_admin | `/projects/tree` 200, 챗봇 트리 노출 |
| admin | admin | `/projects/tree` 200, 챗봇 트리 노출 |
| developer | (트랙 #99 정의 확인 필요) | `/projects/tree` 200, 챗봇 트리 노출 |
| hslee | **user** | `/projects/tree` **200 (fix 후)**, 챗봇 트리에 public 30 건 표시 |
| shbaek | (role 확인 필요) | 동일 |

추가 회귀 회피 점검:
- `/documents` 페이지에서 hslee 가 보던 30 건이 그대로 유지되는지 (Phase A fix 가 documents 측에 부수 영향 없는지)
- `/agents` 등 트랙 #104 에서 fix 한 endpoint 가 여전히 정상 (회귀 없음)

---

## 7. 후속 작업 (Phase B / Phase C 와의 연관)

- **Phase B.1 endpoint 카탈로그**: 이번 진단으로 'user' 누락 잠재 4 router 가 이미 식별됨. 카탈로그 추출 시 같은 패턴이 더 있는지(예: audit/faq/users/organizations/settings) 전수 검증.
- **Phase B.2 결함 식별**: 4 router 의 사용자 화면 호출 여부 grep 으로 결함 판정.
- **Phase B.3 일괄 fix**: 본 진단의 1 router fix 와 함께 5 router 모두 운영 배포.

---

## 8. 핵심 파일 (수정/참조)

- `docutil/backend/app/modules/projects/router.py:52` — fix 대상 (1 라인)
- `docutil/frontend/src/components/documents/document-selector.tsx:105-235` — Promise.all + catch 동작 확인 (수정 없음)
- `docutil/frontend/src/app/(user)/chat/page.tsx:845-856` — `DocumentScopeModal` 호출 (수정 없음)
- `docutil/backend/app/modules/chat/router.py` — chat 세션 생성 핸들러 (수정 없음, H4 기각 확인용)
- `docutil/backend/app/core/dependencies.py` — `require_role` 헬퍼 (수정 없음, 동작 확인용)
