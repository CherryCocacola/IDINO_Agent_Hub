# AI 프레젠테이션 생성 기능 고도화 계획

## 개요
AI로 프레젠테이션 생성 시 다음 6가지 기능을 추가/개선합니다.
1. **프레젠테이션 사이즈 선택** (4:3, 16:9 등)
2. **도표(Chart) 및 표(Table) 삽입**
3. **마크다운 기반 서식** (**굵게**, *기울임* 등 내용별 서식)
4. **글꼴 유연 설정** (사용자 선택 + 테마 프리셋 + AI 글꼴 힌트)
5. **디자인·레이아웃 자동화** (요소별 최적화)
6. **미리보기 슬라이드 쇼** (발표 모드)

---

## Phase 1: 프레젠테이션 사이즈 선택

### 1.1 현재 상태
- `PptxGenerationService.cs`에 슬라이드 크기가 하드코딩됨
- `SlideWidth = 9144000L` (10인치), `SlideHeight = 6858000L` (7.5인치) → **4:3 비율**

### 1.2 지원할 사이즈 옵션

| 옵션 ID | 비율 | 폭(EMU) | 높이(EMU) | 용도 |
|---------|------|---------|-----------|------|
| `4:3` | 4:3 | 9144000 | 6858000 | 기본, 레거시 |
| `16:9` | 16:9 | 9144000 | 5143500 | 와이드스크린(기본 권장) |
| `16:10` | 16:10 | 9144000 | 5715000 | 맥북 등 |
| `A4` | A4 | 9144000 | 6858000 | 인쇄용(4:3과 동일) |

*EMU: English Metric Unit, 914400 EMU = 1인치*

### 1.3 구현 작업

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | DTO 확장 | `PresentationGenerationRequestDto.cs` | `SlideSize` 속성 추가 (기본값: "16:9") |
| 2 | DTO 확장 | `PresentationDto.cs` | `SlideSize` 속성 추가 (저장용) |
| 3 | DB 마이그레이션 | (선택) | Presentations 테이블에 SlideSize 컬럼 추가 |
| 4 | 상수 정의 | `PptxGenerationService.cs` 또는 `PresentationThemes.cs` | 사이즈별 Width/Height 상수 |
| 5 | 서비스 수정 | `PptxGenerationService.cs` | `GeneratePptxAsync`에서 사이즈 파라미터 받아 슬라이드 크기 적용 |
| 6 | UI 추가 | `PresentationBuilder.vue` | AI 생성 모달에 "슬라이드 비율" 선택 UI (4:3, 16:9, 16:10) |

---

## Phase 2: 도표(Chart) 및 표(Table) 삽입

### 2.1 현재 상태
- `SlideDto`에 `Charts: List<ChartDto>` 존재
- `ChartDto`: ChartType(bar/line/pie), Title, Data(Dictionary)
- **PptxGenerationService에서 Chart 렌더링 미구현** (Charts 데이터가 있어도 PPTX에 반영 안 됨)
- **Table(표) DTO 없음**

### 2.2 Chart 구현

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | AI 프롬프트 수정 | `PresentationService.cs` | JSON 형식에 `charts` 배열 추가 요청. 데이터가 있는 슬라이드에 chart 생성 |
| 2 | Chart 렌더링 | `PptxGenerationService.cs` | OOXML ChartPart 생성. DocumentFormat.OpenXml.Drawing.Charts 사용 |
| 3 | Chart 레이아웃 | `PptxGenerationService.cs` | title-content + chart 레이아웃: 제목/본문 + 차트 영역 배치 |

**AI 응답 JSON 확장 예시:**
```json
{
  "slides": [
    {
      "title": "2024년 매출 추이",
      "content": "• Q1~Q4 성장률 분석",
      "layout": "title-content",
      "charts": [
        {
          "chartType": "bar",
          "title": "분기별 매출",
          "data": {
            "Q1": 100, "Q2": 150, "Q3": 180, "Q4": 220
          }
        }
      ]
    }
  ]
}
```

### 2.3 Table(표) 구현

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | DTO 추가 | `SlideDto.cs` | `Tables: List<TableDto>` 추가 |
| 2 | TableDto 정의 | `DTOs/` | `TableDto { Rows: List<List<string>>, HeaderRow?: bool }` |
| 3 | AI 프롬프트 수정 | `PresentationService.cs` | 표가 필요한 슬라이드에 `tables` 배열 추가 요청 |
| 4 | Table 렌더링 | `PptxGenerationService.cs` | OOXML A.Table, A.TableRow, A.TableCell 생성 |
| 5 | 레이아웃 | `PptxGenerationService.cs` | `table` 또는 `title-content` + table 혼합 레이아웃 |

**AI 응답 JSON 확장 예시:**
```json
{
  "slides": [
    {
      "title": "제품 비교",
      "layout": "title-content",
      "tables": [
        {
          "headerRow": true,
          "rows": [
            ["제품", "가격", "평점"],
            ["A", "10만원", "4.5"],
            ["B", "15만원", "4.8"]
          ]
        }
      ]
    }
  ]
}
```

---

## Phase 3: 마크다운 서식 확장

### 3.1 현재 상태
- `ParseMarkdownRuns`에서 `**텍스트**` → 굵게 처리 **이미 지원됨**
- AI 프롬프트에 마크다운 사용 안내 **없음**
- `*기울임*`, `-` 리스트 등 **미지원**

### 3.2 지원할 마크다운

| 마크다운 | 결과 | 우선순위 |
|----------|------|----------|
| `**텍스트**` | 굵게 | ✅ 이미 구현 |
| `*텍스트*` | 기울임 | P1 |
| `` `코드` `` | 고정폭(선택) | P2 |
| `- 항목` | 불릿 리스트 | ✅ 줄바꿈으로 이미 처리 |
| `1. 항목` | 번호 리스트 | P2 |

### 3.3 구현 작업

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | AI 프롬프트 수정 | `PresentationService.cs` | content에 **굵게**, *기울임* 사용 권장 문구 추가 |
| 2 | ParseMarkdownRuns 확장 | `PptxGenerationService.cs` | `*텍스트*` → Italic 처리 추가 (Bold와 중첩 가능) |
| 3 | (선택) 제목/본문별 서식 | `PptxGenerationService.cs` | 제목: 기본 굵게, 본문: **강조**만 굵게 등 차등 적용 |

**AI 프롬프트 추가 문구 예시:**
```
**TEXT FORMATTING (use in content):**
- Use **bold** for key terms or emphasis: **핵심 포인트**
- Use *italic* for subtle emphasis or terms
- Keep bullet points with • or -
```

---

## Phase 4: 글꼴 유연 설정 (복합 방식)

### 4.1 현재 상태
- `PresentationThemes.cs`: 테마별 `FontHeading`, `FontBody` (현재 모두 "맑은 고딕")
- `PptxGenerationService.cs`: `CreateRunProperties`에서 fontSize, bold, color만 설정. **글꼴은 테마 FontScheme에서만 사용, Run 단위 지정 없음**

### 4.2 사용자 선택 (기본)

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | DTO 확장 | `PresentationGenerationRequestDto.cs` | `FontHeading`, `FontBody` (string, optional) 추가 |
| 2 | DTO 확장 | `PresentationDto.cs` | `FontHeading`, `FontBody` 저장용 |
| 3 | RunProperties 수정 | `PptxGenerationService.cs` | `CreateRunProperties`에 `fontFamily` 파라미터 추가, `A.LatinFont`/`A.EastAsianFont` Typeface 설정 |
| 4 | UI 추가 | `PresentationBuilder.vue` | AI 생성 모달에 "제목 글꼴", "본문 글꼴" 드롭다운 추가 |

**지원 글꼴 목록 (시스템 기본):** 맑은 고딕, Noto Sans KR, Pretendard, 나눔고딕, 배달의민족 한나, Arial, Calibri

### 4.3 테마별 프리셋 확장

| 작업 | 파일 | 내용 |
|------|------|------|
| 테마별 글꼴 차등 | `PresentationThemes.cs` | 각 테마에 FontHeading/FontBody를 서로 다르게 지정 (예: Education=나눔고딕, Minimal=Pretendard) |
| UI 연동 | `PresentationBuilder.vue` | 테마 선택 시 해당 테마의 글꼴을 기본값으로 표시, 사용자가 덮어쓸 수 있음 |

### 4.4 AI 글꼴 힌트 (구간별)

| 작업 | 파일 | 내용 |
|------|------|------|
| AI 프롬프트 | `PresentationService.cs` | content 내 `[font:글꼴명]텍스트[/font]` 사용 안내 추가 |
| 파싱 확장 | `PptxGenerationService.cs` | `ParseMarkdownRuns`에 `[font:xxx]...[/font]` 정규식 처리, 해당 구간에만 fontFamily 적용 |

**AI 프롬프트 예시:**
```
**FONT HINTS (optional, use sparingly):**
- For special emphasis or quotes: [font:나눔명조]인용문[/font]
- Use only when content truly benefits from a different font
```

**글꼴 결정 우선순위:** 1) `[font:xxx]` 구간 → 해당 글꼴 / 2) 사용자 선택 FontHeading/FontBody / 3) 테마 FontHeading/FontBody

---

## Phase 5: 디자인·레이아웃 자동화 (요소별 최적화)

### 5.1 현재 상태
- `PptxGenerationService.CreateSlideAsync`: layout별로 switch-case로 고정된 좌표/크기 사용
- AI가 layout을 결정하지만, **content 길이·유형에 따른 동적 조정 없음**

### 5.2 요소별 최적화 전략

| 요소 유형 | 최적화 기준 | 자동화 내용 |
|-----------|-------------|-------------|
| 제목 | 길이·줄 수 | 짧으면 큰 폰트·중앙 정렬, 길면 폰트 축소·여백 조정 |
| 본문 | 불릿 수·줄 수 | 3개 이하면 여백 확대, 7개 이상이면 폰트 축소 |
| 이미지 | 유무·비율 | image-title vs title-content 자동 선택, 이미지 비율에 맞춰 영역 조정 |
| 숫자/데이터 | 패턴 감지 | "Q1: 100, Q2: 150" 등 → chart/table 레이아웃 권장 |
| 비교/대조 | 키워드·구조 | "vs", "A vs B", "장점/단점" → comparison 자동 |

### 5.3 구현 작업

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | AI 프롬프트 확장 | `PresentationService.cs` | 요소별 레이아웃 선택 규칙 추가 (데이터→chart, 비교→comparison 등) |
| 2 | (선택) 휴리스틱 | `PptxGenerationService.cs` | content 길이 기반 폰트/여백 보정 |
| 3 | 미리보기 CSS | `PresentationBuilder.vue`, `PresentationBuilder.css` | content 길이에 따른 동적 스타일 |

---

## Phase 6: 미리보기 슬라이드 쇼

### 6.1 요구사항
- 편집 화면에서 **슬라이드 쇼 모드** 진입
- 전체 화면 또는 모달 형태로 슬라이드 순차 표시
- 키보드(화살표, Space, ESC) 및 화면 클릭으로 이동

### 6.2 구현 방식
- **권장**: 모달 오버레이 + `position: fixed` + `width/height: 100vw/100vh`로 전체 화면 느낌 구현
- Fullscreen API는 선택 사항 (브라우저 호환성 고려)

### 6.3 구현 작업

| 순서 | 작업 | 파일 | 내용 |
|------|------|------|------|
| 1 | 상태 추가 | `PresentationBuilder.vue` | `showSlideshowMode`, `slideshowIndex` |
| 2 | 버튼 추가 | `PresentationBuilder.vue` | 편집 헤더에 "슬라이드 쇼" 버튼 |
| 3 | 슬라이드 쇼 오버레이 | `PresentationBuilder.vue` | `v-if="showSlideshowMode"` 전체화면 div, 현재 슬라이드만 표시 |
| 4 | 키보드 이벤트 | `PresentationBuilder.vue` | ArrowLeft/Right, Space, Escape 처리 |
| 5 | 클릭 네비게이션 | `PresentationBuilder.vue` | 좌우 영역 클릭 시 이전/다음 |
| 6 | 스타일 | `PresentationBuilder.css` | `.pbr-slideshow-overlay` 전체화면 스타일 |

---

## 구현 우선순위 및 일정 제안

| Phase | 기능 | 난이도 | 예상 공수 | 권장 순서 |
|-------|------|--------|-----------|-----------|
| **Phase 6** | 슬라이드 쇼 | 낮음 | 0.5~1일 | 1순위 |
| **Phase 3** | 마크다운 서식 (AI 프롬프트 + *기울임*) | 낮음 | 0.5일 | 2순위 |
| **Phase 1** | 슬라이드 사이즈 선택 | 낮음 | 1일 | 3순위 |
| **Phase 5** | 레이아웃 자동화 (AI 프롬프트) | 낮음 | 0.5일 | 4순위 |
| **Phase 4** | 글꼴 유연 설정 | 중간 | 1.5일 | 5순위 |
| **Phase 2** | Chart 렌더링 | 중간 | 2~3일 | 6순위 |
| **Phase 2** | Table 렌더링 | 중간 | 1.5일 | 7순위 |

---

## 기술 참고

### OOXML 슬라이드 크기
- `PresentationDocument` 생성 시 또는 `Presentation.PresentationProperties`에서 `SldSz` (Slide Size) 설정
- `cx`, `cy` 속성: EMU 단위 (914400 = 1인치)

### Chart in Open XML
- `ChartPart` 추가, `ChartSpace` > `Chart` > `PlotArea` > `BarChart`/`LineChart`/`PieChart`
- `DocumentFormat.OpenXml.Drawing.Charts` 네임스페이스

### Table in Open XML
- `A.Graphic` > `A.GraphicData` > `A.Table`
- `A.TableRow`, `A.TableCell`, `A.TextBody` 구조

---

## 체크리스트 (구현 시)

- [x] Phase 3: AI 프롬프트에 마크다운 안내 추가
- [x] Phase 3: ParseMarkdownRuns에 *italic* 지원
- [x] Phase 1: SlideSize DTO 및 UI
- [x] Phase 1: PptxGenerationService 사이즈 적용
- [x] Phase 4: CreateRunProperties에 fontFamily 및 LatinFont/EastAsianFont 추가
- [x] Phase 4: FontHeading/FontBody DTO 및 UI
- [x] Phase 4: 테마별 글꼴 차등 설정 (Education=나눔고딕, Minimal=Pretendard)
- [ ] Phase 4: ParseMarkdownRuns에 [font:xxx] 파싱 (선택)
- [x] Phase 5: AI 프롬프트에 요소별 레이아웃 선택 규칙 추가
- [x] Phase 6: 슬라이드 쇼 버튼 및 오버레이
- [x] Phase 6: 키보드/클릭 네비게이션
- [x] Phase 2: AI 프롬프트 charts/tables 형식 안내
- [ ] Phase 2: ChartDto → OOXML Chart 렌더링
- [x] Phase 2: TableDto 추가 및 Table 렌더링
- [x] 다국어 키 추가 (슬라이드 비율, 글꼴, 슬라이드 쇼 등)
