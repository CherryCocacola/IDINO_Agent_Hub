# document-schema/components

22개 React 컴포넌트. `phase1_architecture.md` §3.2 카탈로그의 컴포넌트 1:1 대응.

| #     | 이름                                                        | 상태 (Phase 1)        | 도입 스프린트 |
| ----- | ----------------------------------------------------------- | --------------------- | ------------- |
| 1     | SlideTitle                                                  | Phase 1 스켈레톤 완료 | S1 MVP        |
| 2     | Heading                                                     | Phase 1 타입만        | S1 MVP        |
| 3     | Paragraph                                                   | Phase 1 스켈레톤 완료 | S1 MVP        |
| 4     | BulletList                                                  | Phase 1 스켈레톤 완료 | S1 MVP        |
| 5     | KPI                                                         | Phase 1 스켈레톤 완료 | S1 MVP        |
| 6     | DataTable                                                   | Phase 1 스켈레톤 완료 | S2            |
| 7~8   | Chart, Image                                                | 타입만                | S2            |
| 9~14  | SlideSubtitle, Quote, Callout, Timeline, ImageGrid, IconRow | 타입만                | S3            |
| 15~18 | TwoColumn, ThreeColumn, Hero, Comparison                    | 타입만                | S4            |
| 19~22 | ExecutiveSummary, RiskMatrix, ActionItemList, AttendeeList  | 타입만                | S6            |

**규약**

- 파일명은 PascalCase (`SlideTitle.tsx`, `DataTable.tsx`).
- 한 파일 한 컴포넌트. props 타입은 `types/document-schema.ts`에서 import만 하고 여기서 재정의 금지.
- 렌더 내부는 `var(--doc-*)` CSS 변수만. Tailwind 유틸은 레이아웃(`flex`, `gap-*` 등) 중심으로만 사용.

Phase 4 S1에서 MVP 5종의 실제 렌더 로직을 채우고, S2~S6에 걸쳐 나머지 17종을 추가한다.
