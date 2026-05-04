# document-designer

Mode A(자유 생성) · Mode B(양식 채우기)에서 공통으로 사용하는 **편집기 셸(shell)** UI 묶음. DocumentSchema를 조작하는 3분할 작업 공간(좌측 편집 사이드바 + 프롬프트, 중앙 iframe 라이브 프리뷰, 우측 디자인 토큰 피커 + Export 메뉴)을 구성한다.

각 서브 디렉토리는 한 개의 "패널" 단위이며, 패널 간 상태 공유는 `@/lib/document-schema`의 훅(`useDocument`, `useDocumentMutation`)을 통해서만 이루어진다. 패널 간 직접 import는 금지한다. 실제 렌더링 구현은 Phase 4 S1~S7에서 채워 넣는다 — 현재는 시그니처 스켈레톤만 존재한다.
