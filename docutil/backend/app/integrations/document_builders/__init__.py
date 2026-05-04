"""문서 빌더 패키지.

Phase 4 S1 D3 — `DocumentBuilder` ABC + `BuilderRegistry` 공개 심볼만 노출한다.
구체 빌더 (HTML/PPTX/DOCX/HWPX/PDF) 는 S1 D4 이후 하위 서브패키지로 추가된다.

사용 예::

    from app.integrations.document_builders import BuilderRegistry, get_builder

    builder = get_builder("pptx")
    file_bytes = await builder.build(schema)

참조 문서:
- docs/phase1_architecture.md §3 (P7 Builder Adapter Interface), §4.1.2
- docs/phase1_decisions.md Q5 (HwpxBuilder `-> bytes` 유지 결정)
- docs/phase3_execution_roadmap.md §2.1 S1 D3
"""

# 구체 빌더 side-effect import — 각 서브패키지 __init__.py 가 모듈 레벨에서
# register_*_builder() 를 호출해 BuilderRegistry 에 자동 등록한다.
# Celery worker / FastAPI 프로세스 모두 이 __init__.py 만 건드려도 전 포맷 사용 가능.
# S3 D1 — docx 는 스텁 (빈 .docx 반환). 실제 렌더는 S5 완성 예정.
from app.integrations.document_builders import docx, html, pptx  # noqa: F401, E402
from app.integrations.document_builders.base import (
    BuilderRegistry,
    BuildTarget,
    DocumentBuilder,
    get_builder,
)

__all__ = [
    "BuilderRegistry",
    "BuildTarget",
    "DocumentBuilder",
    "get_builder",
]
