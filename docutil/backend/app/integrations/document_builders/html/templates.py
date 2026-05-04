"""HTML 빌더 공통 템플릿 문자열 (Phase 4 S1 D4).

renderer.py 가 조립하는 최상위 HTML 문서 골격과 CSS 변수 주입 블록, 페이지
래퍼, placeholder 마크업을 한 곳에 모았다. 문자열 포매팅은 `str.format()` 이
아닌 f-string / `.join()` 조합으로 처리한다 — CSS 변수 값은 반드시 사전 이스
케이프되어 들어오므로 템플릿 자체는 단순 조립만 책임진다.

설계 판단 포인트:
- **FE 와 동일한 `--doc-*` 네임스페이스**: `frontend/src/styles/document-tokens.css`
  가 기본값을 정의하므로, 서버 HTML 도 동일한 변수명을 사용해 iframe preview
  에서 React 렌더와 서버 렌더가 서로 교체 가능해진다.
- **design_tokens 는 인라인 <style>** 로 주입한다. FE 는 data-brand-preset/
  data-spacing 속성으로 variant 를 제어하는데, 서버 HTML 은 단발성 산출물
  이므로 런타임 스와핑이 필요 없고, 스키마에서 받은 값으로 한 번만 오버라이
  드한다.
- **CSS 안전 값 검증은 여기서 안 함**: renderer.py 에서 `_safe_css_value()`
  를 통해 이미 안전성이 확보된 문자열만 넘어온다 (SRP).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 문서 골격
# ---------------------------------------------------------------------------
#
# `<!doctype html>` 은 반드시 소문자 + 선두. 테스트에서 prefix 검사.
# `<html lang="ko">` 로 한글 기본 지정. viewport 는 iframe 환경 호환용.
# `<meta charset="utf-8">` 는 utf-8 bytes 반환 계약과 일치.
#
# 인라인 CSS 블록은 두 개로 분리:
#   1. BASE_STYLE — 모든 문서 공통 (컴포넌트 기본 스타일, 토큰 기본값).
#   2. 토큰 오버라이드 — renderer 에서 design_tokens 로부터 생성 후 주입.

DOCTYPE = "<!doctype html>"

# 기본 스타일. FE 의 document-tokens.css 와 키·기본값이 동일해야 한다.
# hex 하드코딩 금지 규칙은 *컴포넌트* 에 적용되는 것이고, 이 기본값 블록은
# 토큰 자체의 정의이므로 hex 리터럴 사용이 정상이다.
BASE_STYLE = """\
:root {
  --doc-primary: #0a4fc2;
  --doc-primary-foreground: #ffffff;
  --doc-accent: #ff6b35;
  --doc-accent-foreground: #ffffff;
  --doc-text: #1f2937;
  --doc-text-muted: #64748b;
  --doc-background: #ffffff;
  --doc-surface: #f8fafc;
  --doc-border: #e2e8f0;
  --doc-info: #2563eb;
  --doc-warning: #eab308;
  --doc-success: #22c55e;
  --doc-danger: #ef4444;
  --doc-accent-soft: rgba(255, 107, 53, 0.18);
  --doc-primary-soft: rgba(10, 79, 194, 0.08);
  --doc-font-family: "Pretendard", "Noto Sans KR", ui-sans-serif, system-ui, sans-serif;
  --doc-font-size-xs: 0.75rem;
  --doc-font-size-sm: 0.875rem;
  --doc-font-size-base: 1rem;
  --doc-font-size-lg: 1.125rem;
  --doc-font-size-xl: 1.5rem;
  --doc-font-size-2xl: 2rem;
  --doc-font-size-3xl: 2.5rem;
  --doc-line-height-tight: 1.2;
  --doc-line-height-normal: 1.5;
  --doc-line-height-relaxed: 1.75;
  --doc-spacing-xs: 0.25rem;
  --doc-spacing-sm: 0.5rem;
  --doc-spacing-md: 1rem;
  --doc-spacing-lg: 1.5rem;
  --doc-spacing-xl: 2rem;
  --doc-spacing-2xl: 3rem;
  --doc-page-padding: 3rem;
  --doc-radius-sm: 0.25rem;
  --doc-radius-md: 0.5rem;
  --doc-radius-lg: 1rem;
  --doc-radius-xl: 1.5rem;
  --doc-shadow-sm: 0 1px 2px 0 rgba(15, 23, 42, 0.05);
  --doc-shadow-md: 0 4px 6px -1px rgba(15, 23, 42, 0.1);
  --doc-shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.1);
  --doc-page-width-slide: 1280px;
  --doc-page-width-section-a4: 794px;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: var(--doc-font-family);
  color: var(--doc-text);
  background: var(--doc-background);
  line-height: var(--doc-line-height-normal);
}
.doc-root {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--doc-spacing-xl);
  padding: var(--doc-spacing-md);
}
.doc-page {
  background: var(--doc-background);
  padding: var(--doc-page-padding);
  border: 1px solid var(--doc-border);
  border-radius: var(--doc-radius-md);
  box-shadow: var(--doc-shadow-sm);
  display: flex;
  flex-direction: column;
  gap: var(--doc-spacing-md);
}
.doc-page[data-page-kind="slide"] {
  max-width: var(--doc-page-width-slide);
  aspect-ratio: 16 / 9;
}
.doc-page[data-page-kind="section"] {
  max-width: var(--doc-page-width-section-a4);
}
.doc-component { width: 100%; }
.doc-component-placeholder {
  background: var(--doc-surface);
  border: 1px dashed var(--doc-border);
  border-radius: var(--doc-radius-sm);
  padding: var(--doc-spacing-md);
  color: var(--doc-text-muted);
  font-size: var(--doc-font-size-sm);
}
"""


def render_document(
    token_overrides_css: str,
    spacing_attr: str,
    brand_preset_attr: str,
    document_id_attr: str,
    body_inner: str,
) -> str:
    """최상위 HTML 문서 문자열을 조립한다.

    Args:
        token_overrides_css: `:root` 에 덧씌울 토큰 오버라이드 CSS (이미
            이스케이프·검증 완료된 문자열). 빈 문자열일 수 있다.
        spacing_attr: ``data-spacing`` 속성 값 (compact/normal/relaxed).
        brand_preset_attr: ``data-brand-preset`` 속성 값 (idino_default 등).
        document_id_attr: ``data-document-id`` 속성 값 (이미 이스케이프됨).
        body_inner: `<div class="doc-root">` 내부에 삽입될 페이지 HTML.

    Returns:
        완성된 HTML 문자열 (아직 bytes encode 전).

    Notes:
        모든 인자는 호출자가 `html.escape()` 및 CSS 안전 검증을 선행한
        값을 넘긴다. 이 함수 자체는 이스케이프를 수행하지 않는다.
    """
    return (
        f"{DOCTYPE}\n"
        f'<html lang="ko">\n'
        f"<head>\n"
        f'  <meta charset="utf-8">\n'
        f'  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>DocuUtil 문서</title>\n"
        f"  <style>{BASE_STYLE}</style>\n"
        f"  <style>{token_overrides_css}</style>\n"
        f"</head>\n"
        f"<body>\n"
        f'  <div class="doc-root document-preview-root"'
        f' data-document-id="{document_id_attr}"'
        f' data-spacing="{spacing_attr}"'
        f' data-brand-preset="{brand_preset_attr}">\n'
        f"{body_inner}"
        f"  </div>\n"
        f"</body>\n"
        f"</html>\n"
    )


def render_page(
    page_id_attr: str,
    page_kind_attr: str,
    layout_attr: str,
    components_html: str,
) -> str:
    """단일 페이지(`<section class="doc-page">`) 래퍼를 조립한다.

    FE PageRenderer 와 동일한 data-* 속성 집합을 노출해 iframe postMessage
    element-select 시 동일한 탐색 로직을 재사용할 수 있게 한다.
    """
    return (
        f'    <section class="doc-page"'
        f' data-page-id="{page_id_attr}"'
        f' data-page-kind="{page_kind_attr}"'
        f' data-layout="{layout_attr}">\n'
        f"{components_html}"
        f"    </section>\n"
    )


def render_placeholder(component_type_attr: str, component_id_attr: str, page_id_attr: str) -> str:
    """미지원 컴포넌트용 placeholder `<div>`.

    `validate_components()` 가 탐지한 컴포넌트 타입은 정상 렌더 대신 이
    placeholder 로 대체된다. 빌드 실패를 유발하지 않고 degradation 배지를
    통해 사용자에게 제한을 알린다.
    """
    return (
        f'      <div class="doc-component doc-component-placeholder"'
        f' data-component-id="{component_id_attr}"'
        f' data-component-type="{component_type_attr}"'
        f' data-page-id="{page_id_attr}">\n'
        f'        <span>이 포맷에서는 "{component_type_attr}" 컴포넌트가 지원되지 않습니다.</span>\n'
        f"      </div>\n"
    )
