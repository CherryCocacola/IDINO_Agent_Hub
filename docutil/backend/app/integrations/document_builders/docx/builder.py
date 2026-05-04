"""DocxBuilder — DocumentSchema → DOCX 바이트 빌더 (Phase 4 S3 D1 스텁).

`DocumentBuilder` ABC 를 상속한 세 번째 구체 빌더 **골격**. S3 D1 범위에서는
빈 python-docx `Document()` 를 BytesIO 로 직렬화해 반환한다.

**구현 범위 매핑**:

- **S3 D1 (현재)**: 빌더 등록 + 빈 .docx 반환 스텁. `supported_components` 에
  Chart 를 선언해두어 후속 S5 에서 matplotlib PNG 기반 차트 삽입을 구현할 때
  HtmlRenderer/PptxBuilder 와 동일한 registry 경로를 재사용할 수 있게 한다.

- **S5 (예정)**: Paragraph / Heading / BulletList / DataTable / Chart(PNG) /
  Image / KPI 등 컴포넌트 실제 렌더 로직 이식. 이 때 components.py / constants.py
  가 본 패키지에 추가된다 (PptxBuilder 와 동일한 파일 구조).

설계 판단 포인트:

1. **async 시그니처 유지**: base.py ABC 계약. 현재는 I/O 가 없지만 S5 에서
   matplotlib 렌더 / MinIO 이미지 fetch 가 들어오면 자연스럽게 수용 가능.
2. **supported_components 에 Chart 만 선언**: 스텁 단계에서는 실제 렌더 없이
   빈 문서만 반환하므로, validate_components() 결과에 따라 호출부가 "DOCX 는
   아직 Chart 만 지원함" 을 인식할 수 있다. S5 에서 8~9 종으로 확장된다.
3. **로깅**: build() 호출 시 "스텁 단계" 경고를 한 번 남겨 운영 모니터링에서
   실수로 프로덕션 경로를 타는 경우 즉시 드러나게 한다.

참조:
- docs/phase1_architecture.md §3 (P7 Builder Adapter Interface)
- docs/phase3_execution_roadmap.md §2.3 S3 D1, §2.5 S5
- backend/app/integrations/document_builders/pptx/builder.py (동일 ABC 구현체)
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, ClassVar

# integration layer 예외 — 외부 SDK 직접 import 허용 범위.
# python-docx 는 본 서브패키지 외에서는 절대 사용 금지 (P1 단일 구현).
from docx import Document

from app.integrations.document_builders.base import BuildTarget, DocumentBuilder

if TYPE_CHECKING:
    from app.modules.documents_v2.schemas import DocumentSchema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DocxBuilder (S3 D1 스텁)
# ---------------------------------------------------------------------------


class DocxBuilder(DocumentBuilder):
    """DocumentSchema → DOCX (OOXML) 바이트 (S3 D1 스텁).

    현재 단계에서는 **빈 .docx** 만 반환한다. 실제 컴포넌트 렌더 로직은 S5 에서
    완성되며, 그 때 `supported_components` 도 PptxBuilder 에 준하는 8~9 종으로
    확장된다.

    `supported_components` 에 `"Chart"` 를 선언해 두는 이유는 S3 D1 의 "DOCX
    matplotlib PNG 준비" 문맥 때문. 실제 렌더는 아직이지만, 인터페이스 레벨에서
    DOCX 빌더가 Chart 를 지원하기로 **약속** 한 상태임을 표시한다. S5 에서
    `components.py` 가 추가되면서 이 약속이 구현된다.
    """

    target: ClassVar[BuildTarget] = "docx"
    # S3 D1 범위: 선언만 — 실제 렌더는 S5. 다른 컴포넌트는 빌드 시 skip + WARN.
    supported_components: ClassVar[frozenset[str]] = frozenset({"Chart"})

    # -- 메인 진입점 ---------------------------------------------------------

    async def build(self, schema: DocumentSchema) -> bytes:
        """DocumentSchema 를 DOCX 파일 바이트로 변환한다 (S3 D1 스텁).

        현재 구현은 **빈 python-docx Document** 를 BytesIO 로 직렬화한다.
        schema 의 pages/components 는 **아직 무시** 되며 S5 에서 구현 예정.

        Args:
            schema: 변환 대상 문서 스키마. 향후 완성 시 사용.

        Returns:
            OOXML(ZIP) 포맷 DOCX 바이트. `b"PK"` ZIP 시그니처로 시작.

        Notes:
            - BuilderRegistry 검증용 스텁. 실제 렌더 로직은 S5 의 `components.py`
              (신규 예정) 에서 구현된다.
            - 빈 Document 도 python-docx 는 기본 스타일 + settings.xml 을 포함한
              완전한 OOXML 구조로 생성하므로 바이트가 손상되지 않는다.
        """
        logger.info(
            "DocxBuilder.build: S3 D1 스텁 호출 — 빈 .docx 반환 (document_id=%s, 렌더는 S5 이관 예정).",
            getattr(schema, "document_id", "<unknown>"),
        )

        # validate_components 는 호출해 두되 결과는 logging 만 (스텁 상태 표시).
        unsupported = self.validate_components(schema)
        if unsupported:
            logger.info(
                "DocxBuilder: S3 D1 스텁에서 미지원 컴포넌트 %d 종 skip — %s (S5 에서 이관 예정)",
                len(unsupported),
                ", ".join(unsupported),
            )

        # 빈 Document → BytesIO → bytes.
        doc = Document()
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
