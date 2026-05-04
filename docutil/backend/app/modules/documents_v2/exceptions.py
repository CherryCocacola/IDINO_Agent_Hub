"""documents_v2 모듈 전용 예외 타입.

Phase 4 S1 D6 에서 도입. ``DocumentServiceV2.generate`` 의 실패 경로
(LLM 호출 실패, 스키마 검증 실패, 저장 실패 등) 를 계층적으로 구분해
router 층에서 HTTP 상태 코드 매핑 (D7 작업) 을 용이하게 한다.

상위 계층 ``DocumentV2Error`` → 중립 400. 하위 클래스별로 422/502/500.
"""

from __future__ import annotations


class DocumentV2Error(Exception):
    """documents_v2 모듈의 공통 예외 베이스.

    메시지는 한국어로 작성하며 사용자 노출 가능한 문장을 원칙으로 한다.
    """


class DocumentGenerationError(DocumentV2Error):
    """LLM 호출 자체가 실패한 경우 (네트워크/타임아웃/5xx)."""


class DocumentSchemaValidationError(DocumentV2Error):
    """LLM 응답이 ``DocumentSchema`` 로 검증되지 않은 경우."""


class RAGContextError(DocumentV2Error):
    """RAG 컨텍스트 조립 중 외부 의존 (Qdrant/DB) 이 실패한 경우.

    컨텍스트 비어있음 자체는 에러가 아니므로 구분한다.
    """


class ConcurrentModificationError(DocumentV2Error):
    """낙관적 락 실패: 다른 사용자가 먼저 문서를 수정한 경우.

    Phase 4 S1 D8 에서 도입. ``PATCH /v2/documents/{id}`` 요청에
    ``expected_version`` 이 포함되었으나 현재 ``schema_version`` 과
    일치하지 않을 때 발생한다. 라우터는 이를 409 Conflict 로 매핑한다.
    """
