"""HTML 빌더 서브패키지 (Phase 4 S1 D4).

`HtmlRenderer` 구체 빌더를 임포트 시점에 `BuilderRegistry` 에 자동 등록한다.
등록 중복은 base.py 가 경고 로그 + 덮어쓰기로 허용하므로 테스트에서
`BuilderRegistry.clear()` 후 이 모듈을 reload 해도 안전하다.

테스트에서 Registry 상태를 리셋(clear) 한 경우 다시 등록하려면 아래를 사용::

    from app.integrations.document_builders.html import register_html_renderer
    register_html_renderer()
"""

from __future__ import annotations

from app.integrations.document_builders.base import BuilderRegistry
from app.integrations.document_builders.html.renderer import HtmlRenderer

__all__ = ["HtmlRenderer", "register_html_renderer"]


def register_html_renderer() -> HtmlRenderer:
    """`HtmlRenderer` 인스턴스를 생성·등록하고 반환한다.

    등록은 base.py 의 `BuilderRegistry.register` 호출로 수행되며, 기존
    등록이 있으면 경고 로그와 함께 덮어쓴다.
    """
    renderer = HtmlRenderer()
    BuilderRegistry.register(renderer)
    return renderer


# 임포트 시점 자동 등록 — 앱 부팅 시 이 모듈 임포트만으로 Registry 에 들어간다.
# (Registry 는 프로세스 전역 싱글톤이므로 경로에 관계없이 공유.)
register_html_renderer()
