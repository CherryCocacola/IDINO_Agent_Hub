# 프레젠테이션 빌더 고도화 계획

> Gamma, Beautiful.ai, Canva 등 AI PPT 서비스를 참고한 개선 로드맵  
> 작성일: 2026-01-26

---

## 1. 현황 요약

### 1.1 현재 구현 기능
- **AI 기반 슬라이드 생성**: 주제 입력 → AI가 JSON 구조로 슬라이드 제목/본문 생성
- **템플릿 기반 생성**: 업로드된 PPTX 템플릿 구조 파싱 후, AI가 플레이스홀더에 맞춰 내용 채우기
- **스타일 선택**: 비즈니스/교육/마케팅/창의적 중 선택
- **슬라이드 개수**: 3~20장 지정 (템플릿 사용 시 템플릿 개수 고정)
- **편집·저장**: 슬라이드별 제목/본문 편집, 프레젠테이션 제목 수정
- **내보내기**: PPTX, PDF 다운로드

### 1.2 한계점
- **생성 방식**: “주제 + 슬라이드 수” 위주, 문서/URL 기반 생성 없음
- **레이아웃**: 단순 title-content 구조, 피라미드·퍼널·스테어케이스 등 스마트 레이아웃 미지원
- **이미지**: AI 생성 이미지/일러스트 자동 삽입 없음, 텍스트 위주
- **테마·브랜딩**: 테마/색상/폰트 사전 선택 후 생성하는 플로우 없음
- **재생성·리디자인**: 한 번에 테마/레이아웃만 바꿔서 전체 갱신하는 기능 없음
- **협업·버전**: 실시간 협업, 버전 이력 미지원

---

## 2. 벤치마크 (Gamma, Beautiful.ai, Canva 참고)

### 2.1 Gamma
| 기능 | 설명 | 적용 우선순위 |
|------|------|----------------|
| 원클릭 생성 | 주제만 입력해 전체 덱 자동 생성 | ✅ 이미 유사 구현 |
| 3가지 생성 모드 | Generate(초안) / Paste(기존 텍스트 정리) / Import(파일·URL 변환) | 🔴 높음 |
| 파일·URL 임포트 | PDF, PPTX, 링크 업로드 → 슬라이드로 변환 | 🔴 높음 |
| 테마 원클릭 전환 | 덱 전체를 다른 테마로 한 번에 리디자인 | 🟡 중간 |
| 스마트 레이아웃 | 피라미드, 퍼널, 스테어케이스 등 | 🟡 중간 |
| AI 이미지 생성 | 테마/내용에 맞는 AI 이미지 자동 삽입 | 🔴 높음 |
| 카드/풀블리드 옵션 | 카드 너비, 풀블리드 등 레이아웃 옵션 | 🟢 낮음 |
| 내보내기 | PPTX, PDF, 웹 공유 | ✅ 이미 구현 |

### 2.2 Beautiful.ai
| 기능 | 설명 | 적용 우선순위 |
|------|------|----------------|
| 테마 우선 생성 | 브랜드 테마 선택 후 AI 생성 → 일관된 디자인 | 🟡 중간 |
| 자동 레이아웃 | 간격·정렬·구조 자동 조정 | 🟡 중간 |
| AI 이미지 생성 | 주제에 맞는 커스텀 이미지 생성 | 🔴 높음 |
| Smart Slides | 내용에 맞게 레이아웃이 변하는 템플릿 | 🟡 중간 |
| PPTX 임포트 | 기존 PPT 불러와서 AI로 개선 | 🔴 높음 |
| Find & Replace | 전체 덱 텍스트 일괄 치환 | 🟢 낮음 |

### 2.3 Canva (참고)
| 기능 | 설명 | 적용 우선순위 |
|------|------|----------------|
| 매직 스튜디오 | AI 기반 디자인·요약·이미지 생성 | 참고 |
| 다형식 내보내기 | 비디오, 인쇄물 등 | 🟢 선택 |

---

## 3. 고도화 목표 및 원칙

- **사용자 경험**: “주제만 넣어도 쓸 만한 덱이 나온다” + “문서/URL을 넣으면 자동으로 슬라이드화”
- **디자인 품질**: 테마·레이아웃·AI 이미지를 조합해 Gamma/Beautiful.ai에 근접한 퀄리티
- **기술 스택 유지**: 기존 ASP.NET Core, Vue, Open XML 기반 유지하며 단계적 확장
- **AI 서비스 연동**: 기존 Chat/Image 서비스 연동 재사용 (이미지 생성은 image-generation API 활용)

---

## 4. 단계별 개선 계획

### Phase 1: 생성 입력 다양화 (Generate / Paste / Import)

**목표**: Gamma 스타일 3가지 생성 모드 제공

| 항목 | 내용 | 담당 영역 |
|------|------|-----------|
| **Generate** | 현재와 동일. “주제 + 슬라이드 수 + 스타일”로 생성 | 유지 |
| **Paste** | 사용자가 붙여넣은 긴 텍스트(또는 개요)를 입력받아, AI가 구간별로 슬라이드 제목/본문 분리 생성 | 백엔드: 새 API 또는 기존 generate 파라미터 확장 (예: `sourceType: 'paste'`, `pasteContent`) |
| **Import** | 파일(PPTX, PDF, DOCX) 또는 URL 업로드 → 텍스트 추출 → AI가 요약/구조화해 슬라이드 생성 | 백엔드: 파일 업로드·파싱, URL 크롤링·파싱, 텍스트 추출 서비스 |

**API 확장 예시**
- `POST /presentations/generate`  
  - body: `prompt`, `slideCount`, `serviceId`, `style`, `templateId` (기존)  
  - 추가: `sourceType?: 'topic' | 'paste' | 'import'`, `pasteContent?: string`, `importFileUrl?: string`, `importUrl?: string`
- Import 전용: `POST /presentations/import` (파일 multipart 또는 URL) → 텍스트 추출 후 generate와 동일 파이프라인

**프론트엔드**
- 생성 모달 상단에 “생성 방식” 탭 또는 라디오: **주제로 생성** / **텍스트 붙여넣기** / **파일·URL 가져오기**
- Paste: textarea (긴 글)
- Import: 파일 업로드 + URL 입력 필드

---

### Phase 2: 스마트 레이아웃 및 테마

**목표**: 슬라이드 타입 다양화 + 테마/색상/폰트 선택

| 항목 | 내용 | 담당 영역 |
|------|------|-----------|
| **레이아웃 타입** | title-only, title-content, title-image-content, section-header, pyramid, funnel, comparison, quote, thank-you 등 정의 | DTO/DB: `SlideDto.Layout` 확장, AI 프롬프트에 레이아웃 지시 |
| **테마 사전 선택** | 생성 전 “테마” 선택 (미리 정의한 5~10종: 비즈니스 블루, 다크, 미니멀, 마케팅 등) | 백엔드: 테마별 색상/폰트 매핑, PptxGenerationService에 테마 적용 |
| **테마 원클릭 변경** | 이미 만든 프레젠테이션에 대해 “다른 테마 적용” 버튼 → 색상/폰트만 일괄 변경 | 백엔드: `PUT /presentations/{id}/theme`, 프론트: 테마 선택 UI |

**데이터**
- 테마: `ThemeId`, `Name`, `PrimaryColor`, `SecondaryColor`, `FontHeading`, `FontBody` 등 (코드 또는 DB)
- 슬라이드: `Layout` 값 확장 (기존 title-content 유지 호환)

---

### Phase 3: AI 이미지 자동 삽입

**목표**: 슬라이드별로 AI 생성 이미지 1장씩 자동 추천·삽입 (선택적)

| 항목 | 내용 | 담당 영역 |
|------|------|-----------|
| **이미지 생성 연동** | 기존 image-generation API 호출 (DALL·E 등). 슬라이드 제목/본문 요약을 프롬프트로 사용 | 백엔드: PresentationService에서 슬라이드당 1회 이미지 생성 호출 (옵션), SlideDto에 `ImageUrl` 또는 `ImagePrompt` 추가 |
| **비용·시간 제어** | “AI 이미지 포함” 체크박스, 또는 슬라이드별 “이미지 생성” 버튼으로 선택 생성 | 프론트: 생성 옵션, 슬라이드 편집 시 “이미지 생성” 버튼 |
| **캐시** | 동일 프롬프트는 이미지 URL 캐시해 재사용 검토 | 선택 |

**SlideDto 확장**
- `ImageUrl?: string`, `ImagePrompt?: string` (생성에 사용한 프롬프트)

---

### Phase 4: 편집·재생성 UX 개선

**목표**: 개별 슬라이드 재생성, 슬라이드 순서 변경, Find & Replace

| 항목 | 내용 | 담당 영역 |
|------|------|-----------|
| **슬라이드 재생성** | “이 슬라이드만 다시 생성” 버튼 → 해당 슬라이드 제목/본문만 AI로 재작성 | 백엔드: `POST /presentations/{id}/slides/{slideId}/regenerate`, 프론트: 슬라이드 카드 메뉴 |
| **드래그 앤 드롭** | 좌측 썸네일 목록에서 순서 변경 | 프론트: Vue DnD, 백엔드: `PUT /presentations/{id}/slides/reorder` |
| **Find & Replace** | 전체 덱에서 특정 단어/문구 일괄 치환 | 프론트: 모달 입력 → 백엔드 `POST /presentations/{id}/replace` 또는 프론트만 치환 후 저장 |

---

### Phase 5: 협업·버전·공유 (장기)

**목표**: 링크 공유, (선택) 실시간 협업, 버전 이력

| 항목 | 내용 | 담당 영역 |
|------|------|-----------|
| **공개 링크** | “보기 전용 링크 생성” → 비로그인 사용자도 웹에서 슬라이드 뷰 | 백엔드: 토큰 기반 읽기 전용 URL, 프론트: 공개 뷰어 페이지 |
| **버전 이력** | 저장 시 스냅샷 저장, 이전 버전 목록·복원 | DB: PresentationVersions 테이블, API: list/restore |
| **실시간 협업** | 다중 사용자 동시 편집 (SignalR 등) | 대규모 작업, 별도 계획 |

---

## 5. 기술적 세부사항

### 5.1 백엔드
- **텍스트 추출**: PDF → iTextSharp 또는 PdfPig, DOCX → Open XML, URL → HttpClient + Html Agility Pack 또는 전문 라이브러리. 추출 텍스트를 AI system prompt에 “다음 문서를 기반으로 슬라이드 구조를 만들어라” 형태로 전달.
- **이미지 생성 호출**: `IAiProxyService` 또는 ImageGeneration 전용 서비스 호출, 슬라이드당 1회 (타임아웃·재시도 정책 적용).
- **테마 적용**: PptxGenerationService에서 테마 ID에 따라 색상·폰트 매핑 후 Open XML 스타일 설정.

### 5.2 프론트엔드
- **생성 모드 UI**: 생성 모달을 “주제 / 붙여넣기 / 가져오기” 탭으로 분리하거나, 한 폼에 `sourceType` + 조건부 필드.
- **파일 업로드**: multipart/form-data, 진행률 표시. 대용량 시 Chunk 업로드 검토.
- **슬라이드 목록 DnD**: VueDraggable 또는 native HTML5 DnD로 `slides` 배열 순서 변경 후 reorder API 호출.

### 5.3 DB/저장
- **Presentations**: 기존 유지. `ThemeId` nullable 컬럼 추가 가능.
- **Slides**: JSON 내 `layout`, `imageUrl`, `imagePrompt` 등 확장.
- **Import 이력**: 필요 시 `PresentationImport` 테이블 (원본 URL/파일명, 추출 텍스트 요약 등).

---

## 6. 우선순위 요약

| 순위 | 단계 | 기대 효과 | 난이도 |
|------|------|-----------|--------|
| 1 | Phase 1 (Paste / Import) | 생성 입력 다양화, Gamma/Beautiful와 유사 경험 | 중 |
| 2 | Phase 3 (AI 이미지) | 시각적 품질 크게 향상 | 중 |
| 3 | Phase 2 (테마·레이아웃) | 디자인 일관성, 전문성 | 중 |
| 4 | Phase 4 (재생성·DnD·Replace) | 편집 효율 향상 | 하 |
| 5 | Phase 5 (공유·버전) | 팀 사용·운영 편의 | 상 |

---

## 7. 참고 문서

- 기존 템플릿 구현: `PPT_TEMPLATE_IMPLEMENTATION_PLAN.md`
- Gamma: https://gamma.app/
- Beautiful.ai: https://www.beautiful.ai/

---

**문서 버전**: 1.0  
**다음 단계**: Phase 1 상세 API·화면 스펙 확정 후 개발 착수 권장
