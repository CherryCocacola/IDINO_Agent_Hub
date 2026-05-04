"""문서 빌더 공통 인터페이스 (Phase 4 S1 D3).

P1 단일 구현 원칙 + P7 Builder Adapter Interface 원칙에 따라 모든 문서 파일
출력(HTML/PPTX/DOCX/HWPX/PDF) 은 `DocumentBuilder` 추상 클래스를 상속한
구현체만 허용한다. `BuilderRegistry` 는 출력 대상(target) -> 빌더 인스턴스를
매핑해 런타임 조회한다.

설계 판단 포인트:
- Registry 는 **모듈 레벨 클래스 속성**(사실상 싱글톤) 으로 구현한다. 프로세스
  전역에서 공유되며, 앱 부팅 시 각 구체 빌더 모듈이 `BuilderRegistry.register(...)`
  를 호출해 자기 자신을 등록한다.
- `build()` 는 **async** 시그니처다. Celery 동기 경로에서도 `asyncio.run()`
  또는 `run_until_complete()` 로 래핑해 호출하도록 통일한다. (I/O 바운드
  MinIO 업로드, 이미지 fetch 등이 함께 묶일 가능성에 대비.)
- HwpxBuilder 도 `phase1_decisions.md Q5` 결정에 따라 `-> bytes` 를 유지한다.
  임시파일 경유는 빌더 내부 구현 세부로 은닉된다.
- Registry 중복 등록은 **명시적으로 덮어쓰기 허용**(경고 로그 기록) — 테스트
  용이성을 우선. 운영 코드에서 중복 등록이 발생하면 경고로 바로 드러난다.

참조:
- docs/phase1_architecture.md §3 (P7), §4.1.2, §7.4
- docs/phase1_decisions.md Q5
- docs/phase3_execution_roadmap.md §2.1 S1 D3
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import ClassVar, Literal

from fastapi import HTTPException, status

from app.modules.documents_v2.schemas import (
    Component,
    DocumentSchema,
    Page,
    ThreeColumnComponent,
    TwoColumnComponent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 타입
# ---------------------------------------------------------------------------

# Phase 1 아키텍처 §4.1.2 에서 확정한 5 개 출력 포맷.
BuildTarget = Literal["html", "pptx", "docx", "hwpx", "pdf"]


# 문자열 enum 런타임 검증용 튜플. `Literal` 은 런타임에 값을 열거할 수 없어
# 별도로 보관한다. BuildTarget 변경 시 이 튜플도 함께 수정해야 한다.
_VALID_TARGETS: tuple[str, ...] = ("html", "pptx", "docx", "hwpx", "pdf")


# ---------------------------------------------------------------------------
# DocumentBuilder ABC
# ---------------------------------------------------------------------------


class DocumentBuilder(ABC):
    """모든 문서 빌더의 공통 추상 기반.

    구체 빌더 (HtmlRenderer, PptxBuilder, DocxBuilder, HwpxBuilder, PdfBuilder)
    는 다음 두 클래스 속성과 한 추상 메서드를 반드시 제공해야 한다:

    1. ``target`` — 이 빌더가 처리하는 출력 포맷 (`BuildTarget` 중 하나).
    2. ``supported_components`` — 이 빌더가 네이티브로 지원하는 컴포넌트
       ``type`` 문자열 집합 (예: ``frozenset({"SlideTitle", "Paragraph"})``).
       목록에 포함되지 않은 컴포넌트는 `validate_components()` 에서 탐지되며
       구체 빌더가 degradation 정책을 적용할지 거부할지 결정한다.
    3. ``build(schema)`` — 실제 바이트 변환 로직.

    공통 헬퍼 ``validate_components()`` 는 기본 구현을 제공한다.
    """

    # 구체 빌더가 클래스 속성으로 재정의.
    # mypy/ruff 가 미초기화로 오해하지 않도록 기본값을 None 으로 두되,
    # 등록 시 `BuilderRegistry.register()` 가 유효성을 검증한다.
    target: ClassVar[BuildTarget]
    supported_components: ClassVar[frozenset[str]]

    # -- 추상 인터페이스 -----------------------------------------------------

    @abstractmethod
    async def build(self, schema: DocumentSchema) -> bytes:
        """`DocumentSchema` 를 파일 바이트로 변환한다.

        HwpxBuilder 도 `phase1_decisions.md Q5` 결정에 따라 반환 타입은
        `bytes` 를 유지한다 (임시파일은 내부 은닉).
        """

    # -- 공통 헬퍼 -----------------------------------------------------------

    def validate_components(self, schema: DocumentSchema) -> list[str]:
        """지원하지 않는 컴포넌트 ``type`` 문자열 목록을 반환한다.

        빈 리스트면 모든 컴포넌트가 지원됨을 뜻한다. 반환 리스트는
        `metadata.degraded_components` 기록 / 사용자 배지 표시 / 오류 메시지
        등에서 재사용된다.

        컨테이너 컴포넌트(`TwoColumn`/`ThreeColumn`) 는 재귀적으로 내부 자식
        컴포넌트까지 검사한다.

        Args:
            schema: 검사 대상 문서 스키마.

        Returns:
            지원되지 않는 컴포넌트 타입 문자열의 중복 제거·정렬된 리스트.
        """
        unsupported: set[str] = set()
        for page in schema.pages:
            self._collect_unsupported_in_page(page, unsupported)
        return sorted(unsupported)

    # -- 내부 재귀 헬퍼 ------------------------------------------------------

    def _collect_unsupported_in_page(self, page: Page, acc: set[str]) -> None:
        """한 페이지의 모든 컴포넌트를 순회하며 미지원 타입을 누적."""
        for comp in page.components:
            self._collect_unsupported_in_component(comp, acc)

    def _collect_unsupported_in_component(self, component: Component, acc: set[str]) -> None:
        """단일 컴포넌트 + (있다면) 자식 컴포넌트까지 재귀 검사."""
        # `type` 필드는 Discriminated Union 의 리터럴이므로 항상 존재한다.
        type_name = component.type
        if type_name not in self.supported_components:
            acc.add(type_name)

        # TwoColumn / ThreeColumn 은 내부에 재귀 컴포넌트를 가진다.
        if isinstance(component, TwoColumnComponent):
            for child in component.left:
                self._collect_unsupported_in_component(child, acc)
            for child in component.right:
                self._collect_unsupported_in_component(child, acc)
        elif isinstance(component, ThreeColumnComponent):
            for col in component.columns:
                for child in col:
                    self._collect_unsupported_in_component(child, acc)


# ---------------------------------------------------------------------------
# BuilderRegistry
# ---------------------------------------------------------------------------


class BuilderRegistry:
    """target -> DocumentBuilder 인스턴스 매핑 (프로세스 전역 싱글톤).

    모듈 레벨 클래스 속성 `_registry` 에 등록 상태가 저장된다. 이는 파이썬
    import 시스템이 기본 제공하는 싱글톤 동작(모듈 캐시)에 편승한 것이라
    별도의 락/메타클래스가 필요없다. 테스트 격리를 위한 `clear()` 를 함께
    제공한다.

    구체 빌더는 자기 모듈 최하단에서 다음 패턴으로 등록한다::

        class PptxBuilder(DocumentBuilder):
            target = "pptx"
            supported_components = frozenset({"SlideTitle", ...})

            async def build(self, schema): ...

        BuilderRegistry.register(PptxBuilder())
    """

    # 클래스 속성 = 프로세스 전역 단일 상태.
    _registry: ClassVar[dict[BuildTarget, DocumentBuilder]] = {}

    # -- 등록/조회 API -------------------------------------------------------

    @classmethod
    def register(cls, builder: DocumentBuilder) -> None:
        """빌더 인스턴스를 등록한다.

        - `builder.target` 이 `BuildTarget` Literal 과 일치하는지 검증.
        - `supported_components` 가 `frozenset` 인지 검증.
        - 이미 동일 target 이 등록되어 있다면 **덮어쓰되 경고 로그**를 남긴다.
          (테스트에서 빌더 교체, 개발 중 핫리로드 등을 자연스럽게 지원.)

        Raises:
            ValueError: `target` 이 알려지지 않은 포맷이거나
                `supported_components` 가 `frozenset` 이 아닐 때.
        """
        target = getattr(builder, "target", None)
        if target not in _VALID_TARGETS:
            raise ValueError(f"DocumentBuilder.target 이 올바르지 않습니다: {target!r}. 허용값: {_VALID_TARGETS}")
        supported = getattr(builder, "supported_components", None)
        if not isinstance(supported, frozenset):
            raise ValueError(
                "DocumentBuilder.supported_components 는 frozenset[str] 이어야 "
                f"합니다 (실제: {type(supported).__name__})."
            )

        if target in cls._registry:
            logger.warning(
                "BuilderRegistry: target=%r 빌더가 이미 등록되어 있어 덮어씁니다 (%s -> %s).",
                target,
                type(cls._registry[target]).__name__,
                type(builder).__name__,
            )

        # Literal 타입 좁히기: 위 `in _VALID_TARGETS` 검증으로 안전.
        cls._registry[target] = builder  # type: ignore[index]

    @classmethod
    def get(cls, target: BuildTarget) -> DocumentBuilder:
        """등록된 빌더 인스턴스를 반환한다.

        미등록 target 조회 시 **한국어 메시지**의 `HTTPException(501)` 을 발생
        시킨다. 501 Not Implemented 는 "엔드포인트는 알지만 아직 미구현"을 뜻해
        빌더 미등록 상황에 의미상 부합한다.

        Raises:
            HTTPException: target 이 미등록이거나 알 수 없는 포맷일 때.
        """
        if target not in _VALID_TARGETS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"지원하지 않는 문서 포맷입니다: {target!r}. 사용 가능한 포맷: {', '.join(_VALID_TARGETS)}."),
            )
        builder = cls._registry.get(target)
        if builder is None:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=(
                    f"'{target}' 포맷 빌더가 아직 등록되지 않았습니다. "
                    f"현재 사용 가능한 포맷: "
                    f"{', '.join(cls.list_targets()) or '(없음)'}."
                ),
            )
        return builder

    @classmethod
    def list_targets(cls) -> list[BuildTarget]:
        """현재 등록된 target 목록을 정렬해 반환."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """등록 상태를 초기화한다 (테스트 전용).

        운영 코드에서는 호출하지 말 것. 빌더는 프로세스 부팅 시 1회 등록되고
        그 뒤 수명 종료까지 유지되는 것이 정상이다.
        """
        cls._registry.clear()


# ---------------------------------------------------------------------------
# 편의 팩토리
# ---------------------------------------------------------------------------


def get_builder(target: BuildTarget) -> DocumentBuilder:
    """`BuilderRegistry.get()` 의 얕은 래퍼.

    Service 레이어에서 import 를 짧게 쓰기 위한 공개 팩토리.
    """
    return BuilderRegistry.get(target)
