# document-schema/layouts

6개 layout 래퍼. `Page.layout` enum을 보고 페이지 전체의 **배치 컨테이너**를 담당한다 (PPTX 슬라이드 마스터의 React 대응 개념).

| layout | 역할 |
|---|---|
| `title_slide` | 표지 — SlideTitle/SlideSubtitle/Image 중앙 정렬 |
| `section_divider` | 섹션 분할 — Heading level=1 대형 표시 |
| `content_body` | 본문 — 컴포넌트 세로 흐름 |
| `kpi_dashboard` | KPI 2~4개 그리드 |
| `two_column` | TwoColumn 1개 고정 |
| `closing` | 맺음 — Heading + Paragraph 중앙 |

각 layout은 허용 컴포넌트를 검증하는 것이 아니라 **권장 배치**만 제공한다 (스키마 validator는 백엔드 Pydantic이 담당). Phase 4 S1에서 완성.
