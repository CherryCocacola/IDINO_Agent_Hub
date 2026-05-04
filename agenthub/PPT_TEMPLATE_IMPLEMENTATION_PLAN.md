# PPT 템플릿 + 에이전트 자동 채우기 구현 계획

## 개요
미리 만들어둔 PPT 템플릿을 업로드하고, AI 에이전트가 템플릿의 구조를 유지하면서 내용을 자동으로 채우는 기능을 구현합니다.

## 구현 단계

### 1. 데이터베이스 모델 추가
- **PresentationTemplate 모델 생성**
  - TemplateId (PK)
  - TemplateName (템플릿 이름)
  - TemplateFilePath (템플릿 파일 경로)
  - TemplateStructure (슬라이드 구조 JSON)
  - Category (비즈니스, 교육, 마케팅 등)
  - IsPublic (공개 여부)
  - CreatedBy (생성자)
  - CreatedAt, UpdatedAt

### 2. 템플릿 업로드 및 파싱
- **템플릿 업로드 API**
  - PPTX 파일 업로드
  - OpenXML을 사용하여 템플릿 구조 분석
  - 슬라이드 레이아웃, 플레이스홀더 위치 추출
  - 템플릿 메타데이터 저장

- **템플릿 구조 파싱 서비스**
  - `PptxTemplateParser` 서비스 생성
  - 슬라이드별 레이아웃 정보 추출
  - 플레이스홀더(제목, 본문, 이미지) 위치 파악
  - 템플릿 구조를 JSON으로 저장

### 3. 템플릿 기반 프레젠테이션 생성
- **템플릿 로드 및 구조 복제**
  - 템플릿 파일 로드
  - 슬라이드 구조 복제
  - 레이아웃 및 스타일 유지

- **AI 에이전트로 내용 채우기**
  - 템플릿의 각 슬라이드에 대해 AI 프롬프트 생성
  - 플레이스홀더 위치에 맞춰 내용 생성
  - 템플릿의 디자인과 스타일 유지

### 4. 프론트엔드 UI
- **템플릿 선택 UI**
  - 템플릿 목록 표시
  - 템플릿 미리보기
  - 템플릿 업로드 기능

- **템플릿 기반 생성 모달**
  - 템플릿 선택 드롭다운
  - 주제/내용 입력
  - AI 서비스 및 모델 선택

## 기술적 세부사항

### 템플릿 구조 파싱
```csharp
// 템플릿에서 슬라이드 구조 추출
- 슬라이드 개수
- 각 슬라이드의 레이아웃 타입
- 플레이스홀더 위치 및 타입
- 색상 스키마, 폰트 정보
```

### AI 프롬프트 생성
```csharp
// 템플릿 기반 프롬프트
"템플릿의 {슬라이드번호}번 슬라이드는 {레이아웃타입} 레이아웃입니다.
이 슬라이드의 제목 영역에 '{주제}'와 관련된 제목을 생성하고,
본문 영역에 주요 내용을 불릿 포인트로 작성하세요."
```

### 템플릿 적용 로직
```csharp
1. 템플릿 PPTX 파일 로드
2. 각 슬라이드의 구조 복제
3. AI가 생성한 내용을 플레이스홀더에 삽입
4. 템플릿의 스타일(색상, 폰트) 유지
```

## 파일 구조

### 백엔드
- `Models/PresentationTemplate.cs` - 템플릿 모델
- `DTOs/PresentationTemplateDto.cs` - 템플릿 DTO
- `DTOs/TemplateUploadRequestDto.cs` - 템플릿 업로드 요청
- `Services/IPptxTemplateParser.cs` - 템플릿 파싱 인터페이스
- `Services/PptxTemplateParser.cs` - 템플릿 파싱 구현
- `Services/IPresentationTemplateService.cs` - 템플릿 관리 서비스
- `Services/PresentationTemplateService.cs` - 템플릿 관리 구현
- `Controllers/PresentationTemplateController.cs` - 템플릿 API

### 프론트엔드
- `views/PresentationTemplateManager.vue` - 템플릿 관리 페이지
- `views/PresentationBuilder.vue` - 템플릿 선택 UI 추가
- `types/index.ts` - 템플릿 관련 타입 추가

## 데이터베이스 마이그레이션
- `PresentationTemplates` 테이블 생성
- 템플릿 파일 저장 경로: `wwwroot/templates/`

## 구현 우선순위
1. **1단계**: 템플릿 모델 및 업로드 기능
2. **2단계**: 템플릿 구조 파싱
3. **3단계**: 템플릿 기반 프레젠테이션 생성
4. **4단계**: 프론트엔드 UI 통합
