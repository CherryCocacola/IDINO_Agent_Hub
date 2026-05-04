# designer (user 라우트)

DocumentSchema 기반 신규 문서 생성·편집 UX의 Next.js 라우트. Mode A/B 통합 진입점.

- `create/` — Mode A 자유 생성 시작 화면 (`template_id=null`).
- `fill/[templateId]/` — Mode B 양식 채우기 진입 (`mode=template_fill`).
- `[documentId]/` — 생성 완료된 문서의 편집·프리뷰 (Phase 4 S1에서 추가 예정).

기존 `(user)/reports/`는 Phase 4 S7에서 이 경로로 리다이렉트 처리한 뒤 폐기한다.
