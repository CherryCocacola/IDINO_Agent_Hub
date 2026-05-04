# design-token-picker

Designer Shell 우측 15% 영역 하단의 **디자인 토큰 조정 UI**. `DocumentSchema.design_tokens` 7개 필드(primary/accent/text/background 색상, font_family, spacing, brand_preset)를 실시간으로 편집한다.

Phase 4 S1 D5 구현본. 편집 동작은 두 개의 독립 debounce 파이프로 흘러간다.

## 구성

```
design-token-picker/
├── index.tsx                   # <DesignTokenPicker> 외부 노출 컴포넌트
├── BrandPresetButtons.tsx      # 상단 프리셋 row
├── ColorTokenSlider.tsx        # HTML5 color picker + HEX input
├── FontTokenSelect.tsx         # font_family Select
├── SpacingTokenRadio.tsx       # spacing 라디오
├── tokens.ts                   # 내부 상수 (DEFAULT_DESIGN_TOKENS, BRAND_PRESETS 등)
├── useDebouncedTokenSync.ts    # 50ms preview + 500ms commit debounce 훅
└── __tests__/
    └── design-token-picker.test.tsx
```

## Debounce 파이프

| 파이프    | 딜레이    | 역할                                                     | 연결 경로                                                                        |
| --------- | --------- | -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `preview` | **50ms**  | iframe `<html>` 의 CSS 변수 (`--doc-*`) 를 즉시 override | `PreviewPaneHandle.sendTokenUpdate(patch)`                                       |
| `commit`  | **500ms** | 서버 PATCH. 최종 값만 1회 전송                           | `apiClient.patch('/v2/documents/{id}', { patchType: 'tokens', data: ... })` (D8) |

두 파이프 모두 누적 병합된다. 드래그 도중 primary·accent 를 연속으로 만지고 손을 떼면 commit 은 `{ primary_color, accent_color, brand_preset: "custom" }` 단일 페이로드로 flush.

```tsx
// 호출자 예시 (Designer shell 에서 wiring)
<DesignTokenPicker
  tokens={document.design_tokens}
  onPreview={(patch) => previewRef.current?.sendTokenUpdate(patch)}
  onCommit={(patch) => commitTokensPatch(patch)} // D8 에서 apiClient.patch 연결
/>
```

## UX 규약

1. **상단**: 브랜드 프리셋 버튼 row — 클릭 시 `onApply(전체 DesignTokens)` → preview 와 commit 파이프에 **전체** 토큰을 흘린다 (schema-patch-local/tokens 매핑).
2. **중간**: 색상 4종 슬라이더, 폰트 Select, spacing 라디오.
3. **하단**: **기본값 복원** 버튼 — `DEFAULT_DESIGN_TOKENS` 로 전체 롤백.

### 브랜드 프리셋 잠금

- `brand_preset = idino_default / idino_mono` 일 때 색상 input 은 `readOnly + disabled` + "IDINO 브랜드 프리셋 사용 중 — 커스텀 모드에서 편집" 힌트 노출.
- `brand_preset = custom` 일 때만 색상 자유 편집.
- 사용자가 프리셋 잠김 상태에서 색상을 바꾸려면, 현재는 다른 프리셋을 거치지 않고 직접 편집할 수 없다. (D6 prompt-box 에서 "커스텀으로 전환" 토글을 추가할 예정.)
- 색상 편집 경로에서 brand_preset 을 자동으로 `custom` 으로 승격 처리할 수 있도록 `ColorTokenSlider` 가 패치 payload 에 `brand_preset: "custom"` 을 함께 실어 보낸다.

## CSS 변수 시스템

`frontend/src/styles/document-tokens.css` 에서 세 가지 브랜드 프리셋을 정의한다.

| preset                       | primary   | accent    | 의도                                                    |
| ---------------------------- | --------- | --------- | ------------------------------------------------------- |
| `idino_default` (:root 기본) | `#0A4FC2` | `#FF6B35` | IDINO 코퍼레이트                                        |
| `idino_mono`                 | `#2B2B2B` | `#666666` | 흑백 단색 변형                                          |
| `navy`                       | `#0F2F5A` | `#D4A017` | 공공·금융 (`brand_preset = custom` 슬롯으로 매핑)       |
| `forest`                     | `#1F5F3F` | `#A3D65C` | ESG·지속가능경영 (CSS 만 정의, picker 버튼은 navy 노출) |

각 프리셋은 `.document-preview-root[data-brand-preset="..."]` (iframe 내부) 와 `:root[data-brand-preset="..."]` (picker UI 자체) 두 셀렉터를 동시에 커버해, picker 의 `activePreset` 바뀜만으로도 UI 프리뷰 스와치가 즉시 반영된다.

spacing 프리셋(`compact` / `relaxed`) 도 동일하게 두 셀렉터를 지원한다.

## 파일별 책임

- **`index.tsx`** — 공용 컴포넌트. `tokens` / `onPreview` / `onCommit` 3개 props 만 받음.
- **`BrandPresetButtons.tsx`** — 프리셋 버튼 row. `aria-pressed`, 색상 스와치 2분할.
- **`ColorTokenSlider.tsx`** — HTML5 `<input type="color">` + HEX Input. 잘못된 hex 는 blur 시 롤백.
- **`FontTokenSelect.tsx`** — shadcn `Select`. 옵션 라벨에 실제 fontStack 적용.
- **`SpacingTokenRadio.tsx`** — `fieldset` + 네이티브 radio (sr-only + label 스타일).
- **`tokens.ts`** — `DEFAULT_DESIGN_TOKENS`, `BRAND_PRESETS`, `FONT_FAMILY_OPTIONS`, `SPACING_OPTIONS`, `isValidHexColor`, `normalizeHexColor`, `isColorEditingLocked`.
- **`useDebouncedTokenSync.ts`** — 이중 debounce 훅. `preview / commit / flushPreview / flushCommit / flush / cancel` 노출.

## 테스트

`__tests__/design-token-picker.test.tsx` 에서 10건 시나리오 (최소 요건 8건).

```bash
cd frontend
npx vitest run src/components/document-designer/design-token-picker/
```

## D5 범위 밖

- `apiClient.patch(...)` 실제 호출 — D8 에서 wiring.
- 문서 상태 스토어(Zustand) 연결 — Designer shell 컨테이너에서 수행.
- D6 prompt-box 와의 연동 (token picker 와 프롬프트가 같은 사이드바 영역을 공유할 때의 탭/스크롤 정책).
- 신규 프리셋을 사용자 정의로 저장하는 UI (Phase 4 S2).
