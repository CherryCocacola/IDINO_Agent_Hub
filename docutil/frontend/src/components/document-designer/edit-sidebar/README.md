# edit-sidebar

좌측 30% 영역의 **컴포넌트 편집 사이드바**. 현재 선택된 `Page` 또는 `Component`의 속성을 form 형태로 노출하고, `useDocumentMutation`으로 patch를 적용한다.

- 선택 대상이 없으면 document 레벨(제목·타입·페이지 목록)을 편집한다.
- Mode B에서는 `locked=true` 필드를 disabled로 표시하고 자물쇠 아이콘(`lucide-react` Lock)을 붙인다.
- 각 컴포넌트 타입별 Form은 `components/{Type}Form.tsx`에 분리(Phase 4 S1~S6 단계적 도입).

렌더링·저장 로직은 Phase 4에서 구현.
