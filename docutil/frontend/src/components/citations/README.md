# citations

`DocumentSchema.metadata.citations`에 저장된 근거 청크를 표시하는 **공통 Citations UI**. 기존 챗봇 전용 구현(`components/chat/` 내부)에서 **승격**되어, designer 프리뷰와 챗봇 양쪽이 동일 컴포넌트를 사용한다(`phase1_architecture.md` §재활용 #18).

- `<CitationList citations>` — 풋터·주석 영역에 번호 매긴 출처 목록.
- `<CitationMarker id>` — 본문 내 `[cite: r1]` 인라인 마커 → 툴팁으로 원문 발췌.
- 클릭 시 원본 문서로 이동(`/my-documents/{documentId}#chunk-{chunkId}`).

구체 구현은 Phase 4 S6(citations Mode A 자동 삽입)에서 확정. 지금은 기존 챗봇 구현을 이관할 수 있도록 빈 디렉토리만 준비.
