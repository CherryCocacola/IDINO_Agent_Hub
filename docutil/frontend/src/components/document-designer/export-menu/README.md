# export-menu

우측 패널 상단의 **Export 드롭다운**. `POST /v2/documents/{id}/export?format=...`를 호출하고 Celery 비동기 빌더의 완료를 폴링한 뒤 MinIO presigned URL을 브라우저 다운로드로 연결한다.

- 지원 포맷: `pptx`, `docx`, `hwpx`, `pdf`, `html`
- `metadata.degraded_components`가 비어있지 않으면 HWPX 선택 시 "일부 컴포넌트는 간소화되어 표현됩니다" 경고 토스트.
- HWP는 **노출하지 않는다**(techspec §7.3.1). 대신 HWPX 항목 하단에 "한컴 2020+에서 열림" 안내 문구.

shadcn `dropdown-menu` + `button`을 재사용. 완성은 Phase 4 S1(기본 메뉴), S5(HWPX 활성화), S7(PDF).
