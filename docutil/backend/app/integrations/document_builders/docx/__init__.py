"""DOCX 빌더 서브패키지 (Phase 4 S3 D1 스텁).

`DocxBuilder` 구체 빌더 *골격* 을 임포트 시점에 `BuilderRegistry` 에 자동 등록한다.
S3 D1 범위에서는 빈 .docx 반환 + Chart 컴포넌트만 선언적으로 supported 로 명시하는
**placeholder 구현** 이며, 실제 컴포넌트 렌더 로직은 S5 에서 완성된다.

테스트에서 Registry 상태를 리셋(clear) 한 경우 다시 등록하려면 아래를 사용::

    from app.integrations.document_builders.docx import register_docx_builder
    register_docx_builder()

참조:
- docs/phase3_execution_roadmap.md §2.3 S3 D1 (Chart DOCX matplotlib PNG 준비)
- docs/phase3_execution_roadmap.md §2.5 S5 (DOCX/HWPX 완성)
- backend/app/integrations/document_builders/pptx/__init__.py (동일 패턴)
"""

from __future__ import annotations

from app.integrations.document_builders.base import BuilderRegistry
from app.integrations.document_builders.docx.builder import DocxBuilder

__all__ = ["DocxBuilder", "register_docx_builder"]


def register_docx_builder() -> DocxBuilder:
    """`DocxBuilder` 인스턴스를 생성·등록하고 반환한다.

    등록은 base.py 의 `BuilderRegistry.register` 호출로 수행되며, 기존
    등록이 있으면 경고 로그와 함께 덮어쓴다.
    """
    builder = DocxBuilder()
    BuilderRegistry.register(builder)
    return builder


# 임포트 시점 자동 등록 — 앱 부팅 시 이 모듈 임포트만으로 Registry 에 들어간다.
# 현재는 S5 에서 실제 렌더 로직이 구현될 때까지 **빈 .docx 반환** 스텁.
register_docx_builder()
