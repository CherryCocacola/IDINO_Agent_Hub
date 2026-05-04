# prompt-box

Designer Shell 좌측 상단의 **자연어 프롬프트 입력 박스**. Phase 4 S1 D6 범위에서는 **Mode A(자유 생성)** 만 담당한다. Mode B 슬롯 지시와 regenerate-component 분기는 D7/D8 이후에 연결된다.

## 구성 파일

| 파일                     | 역할                                                     |
| ------------------------ | -------------------------------------------------------- |
| `index.tsx`              | `<PromptBox>` 외부 컴포넌트. state 소유 + 자식 위젯 조립 |
| `PromptInput.tsx`        | Textarea + DocumentType Select + "생성" 버튼             |
| `PromptOptions.tsx`      | 기준 문서 다중선택(Dialog) + 에이전트 Select             |
| `ValidationFeedback.tsx` | 입력/요청 에러 alert + 재시도 버튼                       |
| `useDocumentMutation.ts` | `POST /v2/documents` 전용 mutation 훅 (`useState` 기반)  |
| `constants.ts`           | DocumentType 7종·에이전트 필터 매핑·정량 상수            |

## 주요 UX

- **Ctrl/Cmd + Enter** 로 생성 트리거. Shift+Enter 는 줄바꿈.
- 프롬프트 빈칸 → 생성 버튼 disabled.
- 로딩 중 textarea/Select disabled, 버튼에 스피너 + "생성 중".
- 실패 시 `role=alert` 경고 + 다시 시도 버튼.
- 기준 문서는 Dialog + Checkbox 리스트로 최대 10개 선택 가능, 제목 검색 지원.
- 에이전트 목록은 선택된 DocumentType 에 맞춰 `/agents?agent_type=...` 으로 자동 필터.

## DocumentType 7종 매핑

| value           | label           | 매핑되는 agent_type                    |
| --------------- | --------------- | -------------------------------------- |
| `slide_report`  | 슬라이드 보고서 | `report`                               |
| `docx_report`   | 서술형 보고서   | `report`                               |
| `minutes`       | 회의록          | `minutes`                              |
| `proposal`      | 제안서          | `proposal`                             |
| `one_pager`     | 원페이저        | `report`                               |
| `weekly_status` | 주간 현황       | `report`                               |
| `freeform_doc`  | 자유 문서       | `freeform_doc,report,proposal,minutes` |

## 상태 관리 선택 사유

`docs/phase1_decisions.md` v1.2 Q10 결정에 따라 SWR / React Query 를 사용하지 않는다. `<PromptBox>` 의 mutation 은 1회성 사용자 액션이라 cache invalidation 이 필요 없고, 상위 컴포넌트가 응답을 state 에 주입하면 `useDocument` 없이도 프리뷰/편집 흐름을 완성할 수 있다. 다른 designer 훅(예: D8 `updatePage`) 도 동일한 `useState` 패턴으로 맞춘다.

## 사용 예

```tsx
"use client";
import { useRef, useState } from "react";
import { PromptBox } from "@/components/document-designer/prompt-box";
import { PreviewPane, type PreviewPaneHandle } from "@/components/document-designer/preview-pane";
import type { DocumentSchema } from "@/types/document-schema";

export function DesignerShell() {
  const [document, setDocument] = useState<DocumentSchema | null>(null);
  const previewPaneRef = useRef<PreviewPaneHandle | null>(null);

  return (
    <div className="grid grid-cols-[320px_1fr]">
      <PromptBox onDocumentGenerated={setDocument} previewPaneRef={previewPaneRef} />
      <PreviewPane ref={previewPaneRef} schema={document} />
    </div>
  );
}
```

## 제약

- `apiClient` 외 HTTP 수단 금지. 절대 `fetch(...)` 직접 호출하지 않는다.
- hex 하드코딩 금지. shadcn/ui 토큰 또는 `var(--doc-*)` 만 사용.
- 다른 designer 서브디렉터리 (`preview-pane/`, `edit-sidebar/forms/`, `design-token-picker/`) 를 수정하지 않는다. 상호작용은 ref 핸들 또는 props 콜백만 경유.

## 후속 Story 선행 조건

- **D7 (backend `router.py`)** : 본 모듈이 `POST /v2/documents` 를 `mode=free_generation` 로 호출하므로 백엔드 스키마와 1:1 일치 필요.
- **D8 (PATCH 훅 확장)** : `useDocumentMutation` 과 동일한 `useState` 기반 패턴으로 `updatePage` / `regenerateComponent` 추가 예정.
