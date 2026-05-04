# 레이아웃 아키텍처 문서

## 📋 목차
1. [개요](#개요)
2. [레이아웃 컨셉](#레이아웃-컨셉)
3. [구조 상세](#구조-상세)
4. [주요 컴포넌트](#주요-컴포넌트)
5. [장점 및 특징](#장점-및-특징)
6. [반응형 디자인](#반응형-디자인)
7. [네비게이션 구조](#네비게이션-구조)

---

## 개요

본 프로젝트는 **Vue.js 3** 기반의 **SPA(Single Page Application)** 구조를 채택하고 있으며, **중첩 라우팅(Nested Routing)** 패턴을 사용하여 일관된 레이아웃을 제공합니다.

### 기술 스택
- **프레임워크**: Vue.js 3 (Composition API)
- **라우팅**: Vue Router 4
- **상태 관리**: Pinia
- **UI 프레임워크**: Bootstrap 5
- **아이콘**: Bootstrap Icons
- **다국어**: Vue I18n

---

## 레이아웃 컨셉

### 1. **고정 사이드바 + 동적 컨텐츠 영역**

```
┌─────────────┬─────────────────────────────┐
│             │         Top Header           │
│  Sidebar    ├─────────────────────────────┤
│  (고정)     │                             │
│             │      Main Content           │
│             │      (동적)                 │
│             │                             │
│             │                             │
└─────────────┴─────────────────────────────┘
```

### 2. **카테고리 기반 네비게이션**

메뉴 항목을 기능별로 카테고리화하여 사용자가 쉽게 원하는 기능을 찾을 수 있도록 구성했습니다.

### 3. **접을 수 있는 사이드바**

데스크톱 환경에서 작업 공간을 최대화하기 위해 사이드바를 접을 수 있는 기능을 제공합니다.

---

## 구조 상세

### 전체 레이아웃 구조

```vue
<template>
  <div class="d-flex vh-100">
    <!-- 1. 왼쪽 사이드바 (고정) -->
    <aside class="sidebar">
      - 사이드바 헤더 (브랜드 로고 + 접기 버튼)
      - 네비게이션 메뉴 (카테고리별 그룹화)
    </aside>

    <!-- 2. 메인 컨텐츠 영역 (동적) -->
    <div class="main-content">
      - 상단 헤더 (페이지 제목 + 사용자 메뉴 + 언어 선택)
      - 메인 컨텐츠 (<router-view />)
    </div>

    <!-- 3. 모바일 사이드바 (반응형) -->
    <aside class="mobile-sidebar">
      - 모바일 환경에서만 표시
      - 오버레이 방식으로 동작
    </aside>
  </div>
</template>
```

### 컴포넌트 계층 구조

```
App.vue
└── MainLayout.vue (레이아웃 래퍼)
    ├── Sidebar (왼쪽 네비게이션)
    │   ├── SidebarHeader
    │   └── SidebarNav
    │       └── MenuCategory (여러 개)
    │           └── MenuItem (여러 개)
    │
    └── MainContent
        ├── TopHeader
        │   ├── PageTitle
        │   ├── LanguageSelector
        │   └── UserMenu
        │
        └── RouterView (동적 컨텐츠)
            ├── Dashboard.vue
            ├── AgentSelect.vue
            ├── AgentChat.vue
            ├── Analytics.vue
            └── ... (기타 페이지들)
```

---

## 주요 컴포넌트

### 1. MainLayout.vue

**역할**: 전체 애플리케이션의 레이아웃을 담당하는 최상위 컴포넌트

**주요 기능**:
- 사이드바 표시/숨김 제어
- 모바일 사이드바 오버레이 관리
- 현재 페이지 제목 동적 표시
- 언어 변경 기능
- 사용자 인증 상태 관리
- 라우트 변경 감지 및 카테고리 자동 확장

**상태 관리**:
```typescript
- sidebarCollapsed: 사이드바 접힘 상태
- mobileSidebarOpen: 모바일 사이드바 열림 상태
- expandedCategories: 각 카테고리의 확장 상태
```

### 2. Sidebar (사이드바)

**디자인 컨셉**: 밝은 회색 톤 (#f8f9fa)의 깔끔한 디자인

**주요 특징**:
- **고정 너비**: 280px (확장 시), 70px (접힘 시)
- **카테고리 기반 메뉴**: 기능별로 그룹화된 메뉴 구조
- **접기/펼치기**: 각 카테고리별 독립적인 확장/축소
- **활성 상태 표시**: 현재 라우트에 맞는 메뉴 항목 하이라이트
- **부드러운 애니메이션**: CSS transition을 통한 자연스러운 전환

**카테고리 구조**:
1. **대시보드** (Dashboard)
   - 대시보드

2. **AI 서비스** (AI Services)
   - Agents
   - Multi Chat
   - Image Generation
   - Video Generation
   - Presentation Builder

3. **관리** (Management)
   - Users
   - Team
   - Quota
   - API Keys

4. **분석** (Analytics)
   - Analytics
   - Audit Log
   - Cost Analysis
   - Usage History

5. **시스템** (System)
   - Knowledge Base
   - System Health
   - Database Backup

6. **설정** (Settings)
   - Settings
   - Help

### 3. TopHeader (상단 헤더)

**주요 기능**:
- 현재 페이지 제목 표시
- 언어 선택 드롭다운 (한국어/English)
- 사용자 프로필 메뉴 (설정, 로그아웃)
- 모바일 환경에서 사이드바 토글 버튼

**디자인**:
- 흰색 배경 (#ffffff)
- 하단 테두리로 구분
- 그림자 효과로 깊이감 제공

### 4. MainContent (메인 컨텐츠 영역)

**특징**:
- `flex-grow-1`로 남은 공간 모두 차지
- `overflow-auto`로 스크롤 가능
- 패딩 1.5rem (p-4)로 여백 제공
- `<router-view />`를 통해 동적 컨텐츠 렌더링

---

## 장점 및 특징

### 1. **일관된 사용자 경험**

- 모든 페이지에서 동일한 네비게이션 구조 제공
- 사용자가 어느 페이지에 있든 쉽게 다른 기능으로 이동 가능
- 브랜드 일관성 유지 (사이드바 브랜드 로고)

### 2. **효율적인 공간 활용**

- **접을 수 있는 사이드바**: 작업 공간을 최대화하면서도 네비게이션 접근성 유지
- **고정 헤더**: 항상 보이는 헤더로 현재 위치 파악 용이
- **반응형 디자인**: 모바일 환경에서 오버레이 사이드바로 화면 공간 최적화

### 3. **직관적인 네비게이션**

- **카테고리 기반 구조**: 관련 기능들을 그룹화하여 찾기 쉬움
- **아이콘 + 텍스트**: 시각적 인식과 텍스트 설명의 조화
- **활성 상태 표시**: 현재 페이지를 명확하게 표시
- **자동 카테고리 확장**: 현재 페이지가 속한 카테고리 자동 확장

### 4. **확장성**

- **중첩 라우팅**: 새로운 페이지 추가 시 라우터 설정만으로 자동 레이아웃 적용
- **카테고리 추가 용이**: `menuCategories` 배열에 항목 추가만으로 메뉴 확장 가능
- **컴포넌트 재사용**: 각 페이지는 독립적인 컴포넌트로 개발 가능

### 5. **성능 최적화**

- **Lazy Loading**: 라우트별 컴포넌트 지연 로딩으로 초기 로딩 시간 단축
- **CSS Transition**: 하드웨어 가속을 활용한 부드러운 애니메이션
- **조건부 렌더링**: 모바일 사이드바는 필요할 때만 렌더링

### 6. **접근성**

- **키보드 네비게이션**: 라우터 링크로 키보드 접근 가능
- **시맨틱 HTML**: `<nav>`, `<aside>`, `<header>`, `<main>` 태그 사용
- **ARIA 속성**: 필요 시 추가 가능한 구조

### 7. **다국어 지원**

- **Vue I18n 통합**: 모든 메뉴 항목과 텍스트가 다국어 지원
- **언어 전환**: 헤더에서 쉽게 언어 변경 가능
- **로컬 스토리지 저장**: 선택한 언어 설정 유지

### 8. **인증 통합**

- **라우터 가드**: 인증이 필요한 페이지 자동 보호
- **인증 상태 관리**: Pinia store를 통한 전역 인증 상태 관리
- **자동 리다이렉트**: 미인증 사용자 자동 로그인 페이지 이동

---

## 반응형 디자인

### 데스크톱 (≥992px)

```
┌─────────────┬─────────────────────────────┐
│             │         Header              │
│  Sidebar    ├─────────────────────────────┤
│  (280px)    │                             │
│             │      Content                │
│             │                             │
└─────────────┴─────────────────────────────┘
```

**특징**:
- 고정 사이드바 (접기 가능)
- 넓은 작업 공간
- 헤더에 모든 기능 표시

### 모바일 (<992px)

```
┌─────────────────────────────┐
│  [☰]  Header               │
├─────────────────────────────┤
│                             │
│      Content                │
│                             │
└─────────────────────────────┘

[사이드바 열기 시]
┌─────────────┬───────────────┐
│             │  Header       │
│  Sidebar    ├───────────────┤
│  (오버레이) │               │
│             │   Content     │
└─────────────┴───────────────┘
```

**특징**:
- 사이드바 숨김 (햄버거 메뉴로 열기)
- 오버레이 방식 사이드바
- 터치 친화적 인터페이스
- 헤더 간소화 (아이콘 중심)

### 사이드바 접힘 모드 (데스크톱)

```
┌─────┬─────────────────────────────┐
│  🏠 │         Header              │
│  🤖 ├─────────────────────────────┤
│  ⚙️ │                             │
│  📊 │      Content                │
│  🖥️ │                             │
│  ⚙️ │                             │
└─────┴─────────────────────────────┘
```

**특징**:
- 아이콘만 표시 (70px 너비)
- 호버 시 툴팁으로 메뉴 이름 표시
- 최대 작업 공간 확보

---

## 네비게이션 구조

### 메뉴 카테고리 구조

```typescript
interface MenuCategory {
  id: string              // 카테고리 고유 ID
  name: string           // 카테고리 이름 (다국어)
  icon: string           // Bootstrap Icons 클래스
  items: MenuItem[]      // 하위 메뉴 항목들
}

interface MenuItem {
  name: string           // 메뉴 이름 (다국어)
  path: string          // 라우트 경로
  icon: string          // Bootstrap Icons 클래스
}
```

### 라우팅 구조

```typescript
routes: [
  {
    path: '/login',
    component: Login.vue,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: MainLayout.vue,      // 레이아웃 래퍼
    meta: { requiresAuth: true },
    children: [                      // 중첩 라우트
      { path: '', component: Dashboard.vue },
      { path: 'agents', component: AgentSelect.vue },
      { path: 'agents/chat/:id?', component: AgentChat.vue },
      // ... 기타 페이지들
    ]
  }
]
```

### 라우터 가드

- **인증 체크**: `requiresAuth: true`인 라우트는 토큰 확인
- **자동 리다이렉트**: 미인증 시 `/login`으로 이동
- **로그인 상태 유지**: 이미 로그인한 사용자는 로그인 페이지 접근 불가

---

## 디자인 시스템

### 색상 팔레트

- **Primary**: #4F46E5 (인디고)
- **Background**: #ffffff (흰색)
- **Sidebar Background**: #f8f9fa (밝은 회색)
- **Border**: #e9ecef (연한 회색)
- **Text Primary**: #212529 (진한 회색)
- **Text Secondary**: #6c757d (중간 회색)
- **Hover Background**: #e9ecef (연한 회색)
- **Active Background**: #e7f3ff (연한 파란색)

### 타이포그래피

- **브랜드**: 1.15rem, font-weight: 700
- **카테고리 헤더**: 0.875rem, font-weight: 600
- **메뉴 항목**: 0.875rem, font-weight: 500
- **활성 메뉴**: font-weight: 600

### 간격 시스템

- **사이드바 패딩**: 1rem (수평), 0.75rem (수직)
- **메뉴 항목 패딩**: 0.625rem (수직), 1rem (수평)
- **메인 컨텐츠 패딩**: 1.5rem (p-4)
- **헤더 패딩**: 1rem (수직), 1.5rem (수평)

### 애니메이션

- **사이드바 접기**: `transition: width 0.3s ease`
- **메뉴 호버**: `transition: all 0.2s ease`
- **모바일 사이드바**: `transition: left 0.3s ease`

---

## 상태 관리

### Pinia Store 활용

- **AuthStore**: 사용자 인증 상태, 사용자 정보 관리
- **전역 상태**: 레이아웃 컴포넌트에서 직접 사용

### 로컬 상태

- **사이드바 상태**: `sidebarCollapsed` (ref)
- **카테고리 확장**: `expandedCategories` (ref)
- **모바일 사이드바**: `mobileSidebarOpen` (ref)

### 반응형 데이터

- **현재 페이지 제목**: `currentPageTitle` (computed)
- **활성 라우트**: `isActiveRoute()` (함수)
- **메뉴 카테고리**: `menuCategories` (computed, i18n 반영)

---

## 확장성 고려사항

### 새로운 페이지 추가 시

1. **라우터 설정** (`router/index.ts`)
   ```typescript
   {
     path: 'new-page',
     name: 'NewPage',
     component: () => import('@/views/NewPage.vue')
   }
   ```

2. **메뉴 추가** (`MainLayout.vue`)
   ```typescript
   {
     name: t('nav.newPage'),
     path: '/new-page',
     icon: 'bi bi-new-icon'
   }
   ```

3. **다국어 추가** (`i18n/locales/ko.json`, `en.json`)
   ```json
   {
     "nav": {
       "newPage": "새 페이지"
     }
   }
   ```

### 새로운 카테고리 추가 시

```typescript
{
  id: 'newCategory',
  name: t('nav.categories.newCategory'),
  icon: 'bi bi-icon',
  items: [
    // 메뉴 항목들
  ]
}
```

---

## 성능 최적화

### 1. 코드 스플리팅

- 각 라우트별 컴포넌트를 동적 import로 로딩
- 초기 번들 크기 최소화
- 필요한 페이지만 로드

### 2. 조건부 렌더링

- 모바일 사이드바는 필요할 때만 렌더링
- 접힌 사이드바에서는 텍스트 숨김

### 3. CSS 최적화

- Scoped 스타일로 스타일 충돌 방지
- CSS 변수 활용 가능 (향후 확장)
- 하드웨어 가속 애니메이션

---

## 접근성 (Accessibility)

### 현재 구현

- 시맨틱 HTML 태그 사용
- 키보드 네비게이션 지원 (라우터 링크)
- 명확한 포커스 상태

### 향후 개선 가능 사항

- ARIA 레이블 추가
- 키보드 단축키 지원
- 스크린 리더 최적화

---

## 보안 고려사항

### 라우터 가드

- 인증이 필요한 페이지는 자동으로 보호
- 토큰 만료 시 자동 로그아웃 및 리다이렉트

### 사용자 권한

- 현재는 모든 인증된 사용자가 모든 메뉴 접근 가능
- 향후 역할 기반 접근 제어(RBAC) 확장 가능

---

## 결론

현재 레이아웃 구조는 다음과 같은 장점을 제공합니다:

1. ✅ **일관성**: 모든 페이지에서 동일한 네비게이션 경험
2. ✅ **확장성**: 새로운 기능 추가가 용이한 구조
3. ✅ **반응형**: 다양한 디바이스에서 최적화된 경험
4. ✅ **사용자 친화적**: 직관적인 카테고리 기반 네비게이션
5. ✅ **성능**: 코드 스플리팅과 조건부 렌더링으로 최적화
6. ✅ **유지보수성**: 명확한 컴포넌트 구조와 상태 관리

이러한 구조는 대규모 엔터프라이즈 애플리케이션에 적합하며, 지속적인 기능 확장과 유지보수를 용이하게 합니다.
