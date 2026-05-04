"""DocumentServiceV2 — DocumentSchema 기반 문서 생성 서비스.

Phase 4 S1 D6 산출물. Mode A (자유 생성) 의 end-to-end 파이프라인을
구현하며, Phase 2 전환계획 §2.1 B1-a 에 따라
``report_generator._rag_extract_content`` 의 RAG 조립 로직을
``build_rag_context`` 로 이관한다 (원본 삭제는 S2 에서 수행).

파이프라인 (generate)
---------------------
1. 문서 ID 선생성 (LLM 응답에 주입)
2. RAG 컨텍스트 구성 (build_rag_context)
3. Agent 프롬프트 로드 (선택)
4. LLM.generate_with_schema → DocumentSchema
5. 스키마에 메타 (document_id/mode/metadata) 주입 후 재검증
6. ``tb_documents_v2`` 에 ORM 저장 (비정규화 컬럼 포함)
7. ``DocumentV2`` 인스턴스 반환

P4 (Router→Service→Integration) 엄수. 본 서비스는 ``AgenticSearchService``
와 ``SearchService`` 를 직접 호출하는데, 이는 integration 경로 (Qdrant 조회)
의 진입점이라 P4 의 "Service → Service 금지" 예외에 해당한다 (Search 도
DB/Qdrant 를 감싸는 integration wrapper 이므로). 호출 체인에 다른 도메인
서비스가 끼어들지 않도록 유지한다.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select

from app.integrations.image_generation.auto_select import (
    DalleQuotaExceededError,
    auto_select_image,
)
from app.integrations.llm.factory import create_llm_client, get_provider_for_task
from app.modules.agents.models import Agent
from app.modules.documents.models import Document, DocumentChunk
from app.modules.documents_v2.constants import (
    MAX_CITATIONS_STORED,
)
from app.modules.documents_v2.exceptions import (
    ConcurrentModificationError,
    DocumentGenerationError,
    DocumentSchemaValidationError,
    RAGContextError,
)
from app.modules.documents_v2.models import DocumentV2
from app.modules.documents_v2.schemas import (
    DesignTokens,
    DocumentSchema,
    ImageComponent,
    ImageGridItem,
    Page,
)
from app.modules.documents_v2.utils import (
    build_system_prompt,
    build_user_prompt,
    citation_dict_from_result,
    join_rag_chunks,
    serialize_rag_chunk,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.integrations.llm.client import LLMClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DocumentServiceV2
# ---------------------------------------------------------------------------


class DocumentServiceV2:
    """DocumentSchema 기반 문서 생성 서비스 (Phase 4 S1)."""

    # ------------------------------------------------------------------
    # RAG 컨텍스트 (B1-a 이관 대상)
    # ------------------------------------------------------------------

    @staticmethod
    async def build_rag_context(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        prompt: str,
        source_document_ids: list[UUID] | None = None,
        max_chunks: int = 40,
    ) -> tuple[str, list[dict[str, Any]]]:
        """LLM 프롬프트용 근거 텍스트와 citation dict 목록을 반환한다.

        Parameters
        ----------
        db:
            SQLAlchemy async 세션.
        user_id:
            요청자 ID (검색 히스토리 기록용, AgenticSearchService 에 전달).
        org_id:
            조직 ID (검색 범위 한정).
        prompt:
            자연어 검색 쿼리 (사용자 프롬프트를 그대로 사용).
        source_document_ids:
            ``None`` 이면 조직 전역 하이브리드 검색, 비어 있지 않으면
            해당 문서 내 chunks 를 직접 로드한다 (H5 분할 로딩 패턴).
        max_chunks:
            반환에 포함할 최대 chunk 수. 기본 40 개 (LLM 토큰 예산 고려).

        Returns
        -------
        tuple[str, list[dict]]
            ``(context_text, citations)``. context_text 는 LLM 프롬프트에
            삽입할 근거 블록, citations 는
            :data:`schemas.Citation` 호환 dict 의 목록.

        Notes
        -----
        Phase 2 §2.1 B1-a : ``report_generator._rag_extract_content`` 의
        Qdrant hybrid_search 경로와 동등한 결과를 제공한다. 차이점:

        - 쿼리 임베딩 생성·검색 수행을 ``AgenticSearchService`` 로 위임
          (P1 단일 구현).
        - chunk 본문 포맷은 ``[rN] 문서명 (섹션 · p.N)`` 로 통일되며,
          citations 에 바로 삽입할 수 있는 dict 목록도 함께 반환한다.
        """

        citations: list[dict[str, Any]] = []
        serialized_chunks: list[str] = []

        # ---- case A: source_document_ids 지정 → DB chunks 직접 로드 --------
        if source_document_ids:
            try:
                rows = await DocumentServiceV2._load_chunks_for_documents(
                    db=db,
                    org_id=org_id,
                    document_ids=source_document_ids,
                    limit=max_chunks,
                )
            except Exception as exc:  # noqa: BLE001 - 외부(DB) 실패는 상위로 래핑
                raise RAGContextError("근거 문서 chunks 조회 중 오류가 발생했습니다.") from exc

            for i, (chunk, document) in enumerate(rows, start=1):
                citation_id = f"r{i}"
                serialized_chunks.append(
                    serialize_rag_chunk(
                        i,
                        document_title=document.name if document else None,
                        section_title=chunk.section_title,
                        page_number=chunk.page_number,
                        content=chunk.content,
                        citation_id=citation_id,
                    )
                )
                citations.append(
                    citation_dict_from_result(
                        citation_id,
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        excerpt=chunk.content,
                    )
                )

            return join_rag_chunks(serialized_chunks), citations

        # ---- case B: 조직 전역 에이전틱 검색 ---------------------------------
        try:
            # 지연 import 로 Search 모듈의 자체 import 그래프를 서비스
            # 생성 시점에 평가하지 않는다 (P3 의 import order 유지).
            from app.modules.search.agentic_search import AgenticSearchService

            search_response = await AgenticSearchService.agentic_search(
                db=db,
                query=prompt,
                scope_id=None,
                doc_ids=None,
                org_id=org_id,
                max_results=max_chunks,
                user_id=user_id,
            )
        except Exception as exc:  # noqa: BLE001
            raise RAGContextError("RAG 검색 중 오류가 발생했습니다.") from exc

        results = list(search_response.results or [])[:max_chunks]
        for i, result in enumerate(results, start=1):
            citation_id = f"r{i}"
            serialized_chunks.append(
                serialize_rag_chunk(
                    i,
                    document_title=result.document_name,
                    section_title=result.section_title,
                    page_number=result.page_number,
                    content=result.content,
                    citation_id=citation_id,
                )
            )
            citations.append(
                citation_dict_from_result(
                    citation_id,
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    excerpt=result.content,
                )
            )

        return join_rag_chunks(serialized_chunks), citations

    @staticmethod
    async def _load_chunks_for_documents(
        db: AsyncSession,
        org_id: UUID,
        document_ids: list[UUID],
        limit: int,
    ) -> list[tuple[DocumentChunk, Document | None]]:
        """조직에 속한 문서들의 chunk 를 ``limit`` 개 만큼 로드한다.

        organization_id 필터는 SQL 레벨에서 적용해 권한 우회를 차단한다.
        """

        stmt = (
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.id.in_(document_ids))
            .where(Document.organization_id == org_id)
            .order_by(DocumentChunk.document_id, DocumentChunk.chunk_index)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.all())

    # ------------------------------------------------------------------
    # Mode A: 자유 생성
    # ------------------------------------------------------------------

    @staticmethod
    async def generate(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        *,
        prompt: str,
        document_type: str,
        source_document_ids: list[UUID] | None = None,
        agent_id: UUID | None = None,
        design_tokens: dict | None = None,
        source_chat_session_id: UUID | None = None,
    ) -> DocumentV2:
        """Mode A (자유 생성) — 프롬프트 기반 DocumentSchema 생성 및 저장.

        실패 시나리오별 동작
        ------------------
        - RAG 조립 실패 (Qdrant/DB 오류): ``RAGContextError`` 를 발생시키고
          DB 에는 아무 row 도 남기지 않는다.
        - LLM 호출·검증 실패: ``DocumentV2`` row 를 ``status='error'`` 와
          ``error_message`` 로 저장한 뒤 ``DocumentGenerationError`` /
          ``DocumentSchemaValidationError`` 를 raise 한다.
        """

        if document_type not in {
            "slide_report",
            "docx_report",
            "proposal",
            "minutes",
            "one_pager",
            "weekly_status",
            "freeform_doc",
        }:
            raise DocumentGenerationError(f"지원하지 않는 문서 타입입니다: '{document_type}'")

        # 1) 문서 ID 선생성 ----------------------------------------------------
        document_id = uuid.uuid4()

        # 2) RAG 컨텍스트 -----------------------------------------------------
        context_text, citations = await DocumentServiceV2.build_rag_context(
            db=db,
            user_id=user_id,
            org_id=org_id,
            prompt=prompt,
            source_document_ids=source_document_ids,
        )

        # 3) Agent system_prompt 로드 ----------------------------------------
        agent: Agent | None = None
        agent_prompt: str | None = None
        if agent_id is not None:
            agent = await db.get(Agent, agent_id)
            if agent is None:
                raise DocumentGenerationError(f"에이전트를 찾을 수 없습니다: {agent_id}")
            if agent.organization_id != org_id:
                raise DocumentGenerationError("다른 조직의 에이전트는 사용할 수 없습니다.")
            agent_prompt = agent.system_prompt

        # 4) 프롬프트 구성 ----------------------------------------------------
        system_prompt = build_system_prompt(document_type, agent_prompt=agent_prompt)
        user_prompt = build_user_prompt(prompt, context_text)

        # 5) LLM 클라이언트 (factory 경유 - P1) ------------------------------
        provider = (agent.llm_provider if agent and agent.llm_provider else None) or get_provider_for_task("report")
        try:
            llm_client: LLMClient = create_llm_client(
                provider,
                model=(agent.llm_model if agent else None),
            )
        except ValueError as exc:
            raise DocumentGenerationError(f"LLM 클라이언트 생성 실패: {exc}") from exc

        temperature = agent.temperature if agent else 0.3
        max_tokens = agent.max_tokens if agent else 16_384

        # 6) LLM 호출 + 스키마 검증 ------------------------------------------
        try:
            schema = await llm_client.generate_with_schema(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=DocumentSchema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ValidationError as exc:
            await DocumentServiceV2._persist_failure(
                db=db,
                document_id=document_id,
                user_id=user_id,
                org_id=org_id,
                document_type=document_type,
                agent_id=agent_id,
                source_document_ids=source_document_ids,
                source_chat_session_id=source_chat_session_id,
                provider=provider,
                model=(agent.llm_model if agent else None),
                error_message=f"LLM 응답 스키마 검증 실패: {exc}",
            )
            raise DocumentSchemaValidationError("LLM 응답이 DocumentSchema 를 만족하지 못했습니다.") from exc
        except Exception as exc:  # noqa: BLE001 - 외부 호출은 포괄적으로 래핑
            await DocumentServiceV2._persist_failure(
                db=db,
                document_id=document_id,
                user_id=user_id,
                org_id=org_id,
                document_type=document_type,
                agent_id=agent_id,
                source_document_ids=source_document_ids,
                source_chat_session_id=source_chat_session_id,
                provider=provider,
                model=(agent.llm_model if agent else None),
                error_message=f"LLM 호출 실패: {exc}",
            )
            raise DocumentGenerationError("LLM 호출에 실패했습니다. 잠시 후 다시 시도해 주세요.") from exc

        # 7) 이미지 자동 선택 (Unsplash → DALL-E fallback, Phase 4 S3 D3) -----
        # LLM 이 prompt-only ImageComponent / ImageGridItem 를 생성한 경우,
        # Unsplash 우선 → 실패 시 DALL-E 3 fallback 으로 src 를 자동 주입한다.
        # 실패한 컴포넌트는 src=None 유지 → PPTX 빌더가 placeholder 로 degrade.
        try:
            schema, degraded_image_component_ids = await DocumentServiceV2._auto_fill_image_sources(
                schema,
                organization_id=org_id,
                db=db,
            )
        except Exception as exc:  # noqa: BLE001 - 자동 선택 실패는 생성 중단 사유 아님
            # 자동 선택 단계 자체가 예기치 못한 예외로 완전히 실패한 경우에도
            # 문서 생성은 계속 진행한다 (degrade-friendly). 개별 이미지 실패는
            # 이미 _auto_fill_image_sources 내부에서 흡수된다.
            logger.warning("이미지 자동 선택 중 예외 발생 — 원본 schema 유지: %s", exc)
            degraded_image_component_ids = []

        # 8) 메타 주입 후 재검증 ---------------------------------------------
        now = datetime.now(UTC)
        try:
            schema = DocumentServiceV2._apply_metadata_overrides(
                schema,
                document_id=document_id,
                document_type=document_type,
                user_id=user_id,
                citations=citations,
                created_at=now,
                provider=provider,
                model=(agent.llm_model if agent else None),
                source_document_ids=source_document_ids,
                source_chat_session_id=source_chat_session_id,
                degraded_components=degraded_image_component_ids,
            )
        except ValidationError as exc:
            await DocumentServiceV2._persist_failure(
                db=db,
                document_id=document_id,
                user_id=user_id,
                org_id=org_id,
                document_type=document_type,
                agent_id=agent_id,
                source_document_ids=source_document_ids,
                source_chat_session_id=source_chat_session_id,
                provider=provider,
                model=(agent.llm_model if agent else None),
                error_message=f"메타 주입 후 스키마 검증 실패: {exc}",
            )
            raise DocumentSchemaValidationError("문서 메타 데이터 주입 중 스키마 검증에 실패했습니다.") from exc

        # 8) ORM 저장 --------------------------------------------------------
        title = DocumentServiceV2._derive_title(schema, fallback=prompt)

        doc = DocumentV2(
            id=document_id,
            organization_id=org_id,
            generated_by_user_id=user_id,
            agent_id=agent_id,
            template_id=None,
            source_chat_session_id=source_chat_session_id,
            document_type=document_type,
            mode="free_generation",
            schema_version=1,
            source_document_ids=list(source_document_ids) if source_document_ids else None,
            title=title,
            status="completed",
            completed_at=now,
            llm_provider=provider,
            llm_model=(agent.llm_model if agent else None),
            prompt_tokens=None,
            completion_tokens=None,
            document_schema=schema.model_dump(mode="json"),
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)

        return doc

    # ------------------------------------------------------------------
    # 이미지 자동 선택 (Phase 4 S3 D3)
    # ------------------------------------------------------------------

    @staticmethod
    async def _auto_fill_image_sources(
        schema: DocumentSchema,
        *,
        organization_id: UUID,
        db: AsyncSession | None = None,
    ) -> tuple[DocumentSchema, list[str]]:
        """schema 내 prompt-only 이미지 컴포넌트의 src 를 자동 선택으로 채운다.

        적용 대상:
            - ``ImageComponent`` (22 컴포넌트 중 #11)
            - ``ImageGridItem`` (``ImageGridComponent`` 의 하위 2~4 개)

        Hero.image (HeroImage) 는 배경 이미지로만 쓰여 자동 생성 호출이
        과도한 비용을 유발할 수 있어 S3 D3 범위에서는 제외한다 (prompt 만
        남아 있는 경우는 placeholder 렌더 유지). S4 에서 정책 재검토.

        동작 순서 (P4 준수 — service 는 integration 만 호출):
            1. 스키마 전체를 순회하며 (page, component, index) 식별자로
               자동 주입 대상 리스트를 수집.
            2. ``asyncio.gather`` 로 병렬 `auto_select_image` 호출. ``db`` /
               ``organization_id`` 를 전달해 DALL-E fallback 시 쿼터 체크.
            3. 성공한 결과를 in-place 주입, alt 비어있으면 prompt 앞 60자로 보강.
            4. 실패(None) 는 원본 유지 → 상위에서 스키마 재검증 불요.
            5. **쿼터 초과** (DalleQuotaExceededError) — 해당 이미지만 src=None
               유지하고 ``degraded_components`` 에 컴포넌트 id 를 기록.
               전체 생성은 중단하지 않는다 (soft degrade).

        Args:
            schema: LLM 이 반환한 DocumentSchema 원본.
            organization_id: 쿼터 체크 대상 조직 ID.
            db: AsyncSession. None 이면 쿼터 체크가 skip 된다 (테스트/내부 경로).

        Returns:
            (schema, degraded_component_ids). 첫 번째는 src 가 in-place 수정된
            schema (참조 동일). 두 번째는 쿼터 초과로 src 주입이 실패한 컴포넌트
            ID 리스트 — 상위에서 ``metadata.degraded_components`` 에 병합.

        **Idempotency**: ``src`` 가 이미 설정된 컴포넌트는 건드리지 않는다.
        """

        # 1) 대상 수집 --------------------------------------------------------
        tasks: list[asyncio.Task[str | None]] = []
        # 각 task 에 대응하는 "적용 콜백" — 결과가 오면 해당 컴포넌트에 src 를 주입.
        # 튜플 구조: (kind, target_component, item_idx, component_id)
        #   - component_id 는 degrade 기록용. ImageGridItem 자체는 id 가 없어
        #     상위 ImageGridComponent id 를 재사용한다.
        appliers: list[tuple[str, object, int | None, str]] = []

        for page in schema.pages:
            for comp_idx, comp in enumerate(page.components):
                if isinstance(comp, ImageComponent):
                    if not comp.src and comp.prompt:
                        tasks.append(
                            asyncio.create_task(
                                auto_select_image(
                                    comp.prompt,
                                    comp.alt or "",
                                    organization_id=organization_id,
                                    db=db,
                                )
                            )
                        )
                        appliers.append(("image", comp, None, comp.id))
                # ImageGridComponent 내부 아이템들도 동일하게 처리.
                elif comp.__class__.__name__ == "ImageGridComponent":
                    for item_idx, item in enumerate(comp.images):  # type: ignore[attr-defined]
                        if isinstance(item, ImageGridItem) and not item.src and item.prompt:
                            tasks.append(
                                asyncio.create_task(
                                    auto_select_image(
                                        item.prompt,
                                        item.alt or "",
                                        organization_id=organization_id,
                                        db=db,
                                    )
                                )
                            )
                            appliers.append(("grid_item", comp, item_idx, comp.id))
                # 나머지 컴포넌트 (Hero, Paragraph 등) 는 대상 아님 — 건너뜀.
                _ = comp_idx  # 향후 degrade log 용 예약.

        if not tasks:
            return schema, []

        # 2) 병렬 실행 (예외는 개별 태스크에서 None 으로 변환되거나 아래에서 흡수) ---
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3) 결과 적용 --------------------------------------------------------
        # 쿼터 초과로 실패한 컴포넌트 id 를 수집해 상위에 반환한다.
        # 같은 id 가 여러 번 등장(같은 ImageGrid 의 여러 item)할 수 있으나,
        # 중복 제거는 호출부(_apply_metadata_overrides)의 dedup 로직에서 수행.
        degraded_ids: list[str] = []

        for (kind, target, item_idx, comp_id), result in zip(appliers, results, strict=True):
            if isinstance(result, DalleQuotaExceededError):
                # 쿼터 초과 — 이 이미지만 placeholder 유지 + degrade 기록.
                # 전체 생성은 중단하지 않는다 (soft degrade 정책).
                logger.info(
                    "쿼터 초과로 이미지 자동 생성 skip — component_id=%s kind=%s",
                    comp_id,
                    kind,
                )
                degraded_ids.append(comp_id)
                continue
            if isinstance(result, BaseException):
                # 개별 컴포넌트의 예기치 못한 예외 — placeholder degrade + 로그.
                logger.warning("이미지 자동 선택 태스크 예외: %s (kind=%s)", result, kind)
                continue
            if not result:
                # None 반환 — 해당 컴포넌트는 prompt-only 유지 (빌더가 placeholder).
                continue

            if kind == "image":
                image_comp = target  # type: ignore[assignment]
                image_comp.src = result  # type: ignore[attr-defined]
                # alt 자동 보정 — 빈 문자열/whitespace 만일 때 prompt 앞 60자로 대체.
                current_alt = getattr(image_comp, "alt", "") or ""
                if not current_alt.strip():
                    prompt_text = getattr(image_comp, "prompt", "") or ""
                    image_comp.alt = prompt_text.strip()[:60] or "(자동 생성 이미지)"  # type: ignore[attr-defined]
            elif kind == "grid_item":
                grid_comp = target  # type: ignore[assignment]
                assert item_idx is not None
                item = grid_comp.images[item_idx]  # type: ignore[attr-defined]
                item.src = result
                current_alt = getattr(item, "alt", "") or ""
                if not current_alt.strip():
                    prompt_text = getattr(item, "prompt", "") or ""
                    item.alt = prompt_text.strip()[:60] or "(자동 생성 이미지)"

        return schema, degraded_ids

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_metadata_overrides(
        schema: DocumentSchema,
        *,
        document_id: UUID,
        document_type: str,
        user_id: UUID,
        citations: list[dict[str, Any]],
        created_at: datetime,
        provider: str,
        model: str | None,
        source_document_ids: list[UUID] | None,
        source_chat_session_id: UUID | None,
        degraded_components: list[str] | None = None,
    ) -> DocumentSchema:
        """LLM 이 생성한 schema 에 서버 관리 필드를 주입한 새 모델을 반환한다.

        - document_id / mode / type 은 서버 값으로 덮어쓴다.
        - metadata.created_at / updated_at / generated_by_user_id /
          llm_* / source_* / citations 를 설정한다.
        - citations 는 최대 :data:`MAX_CITATIONS_STORED` 개로 제한.
        - degraded_components 는 자동 이미지 생성 쿼터 초과 등으로 degrade 된
          컴포넌트 id 목록. LLM 이 돌려준 값과 서버 수집값을 합친 후 중복 제거.
        """

        payload = schema.model_dump(mode="python")
        payload["document_id"] = document_id
        payload["type"] = document_type
        payload["mode"] = "free_generation"
        payload["template_id"] = None

        metadata = dict(payload.get("metadata") or {})
        metadata["created_at"] = created_at
        metadata["updated_at"] = created_at
        metadata["generated_by_user_id"] = user_id
        metadata["llm_provider"] = provider
        metadata["llm_model"] = model
        metadata["source_document_ids"] = list(source_document_ids or [])
        metadata["source_chat_session_id"] = source_chat_session_id
        # LLM 이 생성한 citations 는 사용하지 않고, 서버가 RAG 에서 수집한
        # citations 로 교체한다 (할루시네이션 방지).
        metadata["citations"] = list(citations[:MAX_CITATIONS_STORED])
        # degraded_components 병합 — 기존값 + 쿼터 초과 이미지 id. dedup.
        existing_degraded = list(metadata.get("degraded_components") or [])
        extra_degraded = list(degraded_components or [])
        merged_degraded: list[str] = []
        seen: set[str] = set()
        for cid in existing_degraded + extra_degraded:
            if cid not in seen:
                merged_degraded.append(cid)
                seen.add(cid)
        metadata["degraded_components"] = merged_degraded
        metadata.setdefault("prompt_tokens", None)
        metadata.setdefault("completion_tokens", None)
        payload["metadata"] = metadata

        return DocumentSchema.model_validate(payload)

    @staticmethod
    def _derive_title(schema: DocumentSchema, fallback: str) -> str:
        """저장용 ``title`` 컬럼 값을 schema 로부터 파생한다.

        우선순위:
            1. pages[0].title
            2. pages[0].components[0].text (SlideTitle / Heading / Paragraph 등)
            3. user prompt 의 앞 80자
        """

        if schema.pages:
            first = schema.pages[0]
            if first.title:
                return first.title[:512]
            for comp in first.components:
                text = getattr(comp, "text", None)
                if isinstance(text, str) and text.strip():
                    return text.strip()[:512]
        return (fallback or "(제목 없음)")[:512]

    @staticmethod
    async def _persist_failure(
        *,
        db: AsyncSession,
        document_id: UUID,
        user_id: UUID,
        org_id: UUID,
        document_type: str,
        agent_id: UUID | None,
        source_document_ids: list[UUID] | None,
        source_chat_session_id: UUID | None,
        provider: str,
        model: str | None,
        error_message: str,
    ) -> None:
        """실패한 생성 요청의 흔적을 ``status='error'`` 로 남긴다.

        document_schema 컬럼은 NOT NULL 이므로 **최소 유효 skeleton** 을
        저장한다 (오류 조사용). 검증 에러 자체의 저장이 다시 실패하면
        조용히 삼키지 않고 로깅만 하고 반환한다 (메인 에러를 가리지 않도록).
        """

        try:
            now = datetime.now(UTC)
            skeleton = {
                "document_id": str(document_id),
                "schema_version": "1.0",
                "type": document_type,
                "mode": "free_generation",
                "template_id": None,
                "design_tokens": {
                    "primary_color": "#0A4FC2",
                    "accent_color": "#FF6B35",
                    "text_color": "#1F2937",
                    "background_color": "#FFFFFF",
                    "font_family": "Pretendard",
                    "spacing": "normal",
                    "brand_preset": "idino_default",
                },
                "pages": [
                    {
                        "id": "p1",
                        "page_kind": "section",
                        "layout": "content_body",
                        "title": "(생성 실패)",
                        "locked": False,
                        "page_number_visible": True,
                        "speaker_notes": None,
                        "components": [
                            {
                                "id": "c1",
                                "type": "Paragraph",
                                "text": "문서 생성에 실패했습니다.",
                                "emphasis": "normal",
                                "locked": False,
                                "anchor": None,
                            }
                        ],
                    }
                ],
                "metadata": {
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "generated_by_user_id": str(user_id),
                    "llm_provider": provider,
                    "llm_model": model,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "source_document_ids": [str(d) for d in (source_document_ids or [])],
                    "source_chat_session_id": (str(source_chat_session_id) if source_chat_session_id else None),
                    "citations": [],
                    "degraded_components": [],
                },
            }

            doc = DocumentV2(
                id=document_id,
                organization_id=org_id,
                generated_by_user_id=user_id,
                agent_id=agent_id,
                template_id=None,
                source_chat_session_id=source_chat_session_id,
                document_type=document_type,
                mode="free_generation",
                schema_version=1,
                source_document_ids=list(source_document_ids) if source_document_ids else None,
                title="(생성 실패)",
                status="error",
                completed_at=None,
                llm_provider=provider,
                llm_model=model,
                prompt_tokens=None,
                completion_tokens=None,
                document_schema=skeleton,
                error_message=error_message[:2000],
            )
            db.add(doc)
            await db.flush()
        except Exception:  # noqa: BLE001 - 실패 경로 자체의 실패는 로그만
            logger.exception(
                "DocumentV2 실패 레코드 저장 중 오류 발생 (document_id=%s)",
                document_id,
            )

    # ------------------------------------------------------------------
    # Phase 4 S1 D8: Partial DocumentSchema PATCH
    # ------------------------------------------------------------------

    @staticmethod
    async def apply_patch(
        db: AsyncSession,
        user_id: UUID,  # noqa: ARG004 - 감사/추적 용도 예약 (S1 D10 에서 audit 연동)
        org_id: UUID,
        document_id: UUID,
        *,
        patch_type: str,
        page_id: str | None,
        component_id: str | None,
        data: dict,
        expected_version: int | None = None,
    ) -> DocumentV2:
        """DocumentSchema 의 부분 업데이트를 적용한다 (Phase 4 S1 D8).

        흐름
        ----
        1. 조직 스코프로 문서 로드 (``SELECT ... FOR UPDATE``).
        2. 존재·권한 검증 — 없으면 ``DocumentGenerationError``, 타 조직이면
           ``DocumentGenerationError('다른 조직의 문서')`` (라우터에서 403 매핑).
        3. 낙관적 락 (optional) — ``expected_version`` 이 주어졌을 때 현재
           ``schema_version`` 과 다르면 ``ConcurrentModificationError``.
        4. 현재 JSONB 를 :class:`DocumentSchema` 로 파싱.
        5. ``patch_type`` 별 분기:
           - ``page``      : pages[page_id] 를 ``data`` 로 교체.
           - ``component`` : page 내 컴포넌트를 shallow 병합 (``type`` 보호).
           - ``tokens``    : design_tokens 를 교체.
        6. 수정된 schema 를 다시 ``model_validate`` 로 재검증 — 무결성 보장.
        7. ``document_schema`` 컬럼에 dict 로 저장 (단순성 우선, jsonb_set 미사용).
           ``schema_version`` 을 1 증가시키고 ``upd_dt`` 를 현재 시각으로 갱신.
        8. 새 ``DocumentV2`` 를 반환 (router 가 commit + DTO 변환).

        Notes
        -----
        - P1: 모든 스키마 검증은 ``DocumentSchema`` 를 단일 경로로 사용한다.
        - P5: 외부 입력이 스키마 제약을 위반하면 ``DocumentSchemaValidationError``
          로 래핑해 422 를 유도한다.
        - jsonb_set 보다 전체 재저장을 선택한 근거: (i) 평균 문서가 ~100KB 로
          네트워크 부담이 없음 (Q10 결정), (ii) Pydantic 재검증 결과를 그대로
          저장할 수 있어 부분 경로 불일치 위험을 제거.
        """

        # 1) 문서 로드 (조직 스코프 + FOR UPDATE) -------------------------
        stmt = select(DocumentV2).where(DocumentV2.id == document_id).with_for_update()
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()

        if doc is None:
            raise DocumentGenerationError("요청한 문서를 찾을 수 없습니다.")
        if doc.organization_id != org_id:
            raise DocumentGenerationError("다른 조직의 문서에는 접근할 수 없습니다.")

        # 2) 낙관적 락 -------------------------------------------------------
        if expected_version is not None and doc.schema_version != expected_version:
            raise ConcurrentModificationError(
                f"문서가 다른 사용자에 의해 이미 수정되었습니다. "
                f"(current={doc.schema_version}, expected={expected_version})"
            )

        # 3) 현재 schema 파싱 -----------------------------------------------
        try:
            current_schema = DocumentSchema.model_validate(doc.document_schema)
        except ValidationError as exc:
            # DB 에 저장된 schema 가 망가져 있는 이례 케이스 — 422 로 노출.
            raise DocumentSchemaValidationError(
                "저장된 문서 스키마가 유효하지 않아 패치를 적용할 수 없습니다."
            ) from exc

        # 4) patch 적용 (분기) ----------------------------------------------
        #
        # 각 분기는 스키마 일부 검증을 동반한다 (Page, Component, DesignTokens).
        # 검증 실패는 ``DocumentSchemaValidationError`` 로 래핑해 422 를 유도한다.
        try:
            if patch_type == "page":
                if page_id is None:
                    # schemas 레벨에서 거르지만 안전망.
                    raise DocumentGenerationError("patch_type='page' 에는 page_id 가 필요합니다.")
                DocumentServiceV2._apply_page_patch(current_schema, page_id, data)
            elif patch_type == "component":
                if page_id is None or component_id is None:
                    raise DocumentGenerationError("patch_type='component' 에는 page_id 와 component_id 가 필요합니다.")
                DocumentServiceV2._apply_component_patch(current_schema, page_id, component_id, data)
            elif patch_type == "tokens":
                DocumentServiceV2._apply_tokens_patch(current_schema, data)
            else:
                raise DocumentGenerationError(f"지원하지 않는 patch_type 입니다: {patch_type!r}")
        except ValidationError as exc:
            raise DocumentSchemaValidationError(
                f"패치 데이터의 스키마 검증에 실패했습니다: {exc.errors()[0].get('msg', '')}"
            ) from exc

        # 5) 재검증 + updated_at 갱신 ----------------------------------------
        now = datetime.now(UTC)
        try:
            payload = current_schema.model_dump(mode="python")
            metadata = dict(payload.get("metadata") or {})
            metadata["updated_at"] = now
            payload["metadata"] = metadata
            validated = DocumentSchema.model_validate(payload)
        except ValidationError as exc:
            raise DocumentSchemaValidationError(
                f"패치 적용 후 문서 스키마 검증에 실패했습니다: {exc.errors()[0].get('msg', '')}"
            ) from exc

        # 6) DB 저장 ---------------------------------------------------------
        doc.document_schema = validated.model_dump(mode="json")
        doc.schema_version = (doc.schema_version or 1) + 1
        doc.upd_dt = now

        await db.flush()
        await db.refresh(doc)
        return doc

    # ----- patch 적용 헬퍼 (in-place 수정) --------------------------------

    @staticmethod
    def _apply_page_patch(schema: DocumentSchema, page_id: str, patch_data: dict) -> None:
        """pages[page_id] 를 ``patch_data`` 로 전체 교체한다.

        ``patch_data`` 는 :class:`Page` 와 호환되어야 하며, 서버가 ``id`` 를
        대상 page_id 로 강제한다 (클라이언트가 id 를 잘못 지정해도 안전).
        검증은 ``model_validate`` 단계에서 수행되며, 실패 시 상위에서
        ``ValidationError`` → ``DocumentSchemaValidationError`` 로 래핑된다.

        Mode B locked 보호 (D8):
            ``page.locked == True`` 인 페이지는 수정이 금지된다.
            ``DocumentGenerationError`` 를 raise 하여 라우터에서 400 을 반환한다.
            (403 이 더 적절하지만 D7 라우터 매핑 컨벤션을 따라 400 으로 통일.)
        """

        for idx, page in enumerate(schema.pages):
            if page.id != page_id:
                continue
            # locked 페이지는 Mode B 슬롯 고정 목적 — 수정 금지.
            if page.locked:
                raise DocumentGenerationError(f"잠긴 페이지는 수정할 수 없습니다: page_id={page_id!r}")
            merged = dict(patch_data)
            merged["id"] = page_id  # 대상 id 는 서버가 강제
            try:
                schema.pages[idx] = Page.model_validate(merged)
            except ValidationError:
                raise
            return

        raise DocumentGenerationError(f"해당 페이지를 찾을 수 없습니다: page_id={page_id!r}")

    @staticmethod
    def _apply_component_patch(
        schema: DocumentSchema,
        page_id: str,
        component_id: str,
        patch_data: dict,
    ) -> None:
        """page 내 컴포넌트의 필드를 shallow 병합한다.

        - ``type`` 필드는 **기존 값을 강제로 유지** (discriminator 보호).
          클라이언트가 다른 타입을 시도하면 ``DocumentGenerationError`` 로
          거부한다 (라우터에서 400 매핑).
        - ``id`` 는 대상 component_id 로 강제한다.
        - 병합 후 해당 컴포넌트 클래스의 ``model_validate`` 로 재검증한다.

        Mode B locked 보호 (D8):
            - ``page.locked == True`` 인 페이지의 컴포넌트는 수정 금지.
            - 컴포넌트 자체가 ``locked == True`` 이면 수정 금지 (Mode B 슬롯 앵커).
            - 단, 수정 주체가 **새로 locked 로 전환만 하는 경우** (현재 False →
              patch 에 ``locked=True`` 만 포함) 는 허용 — 편집 완료 후 잠금.
              이 세분화는 테스트 ``test_patch_component_locked_field_allowed``
              의 기대 동작과 일치한다.
        """

        for page in schema.pages:
            if page.id != page_id:
                continue

            # 소속 페이지가 잠긴 경우 컴포넌트도 수정 금지.
            if page.locked:
                raise DocumentGenerationError(f"잠긴 페이지의 컴포넌트는 수정할 수 없습니다: page_id={page_id!r}")

            for idx, comp in enumerate(page.components):
                if comp.id != component_id:
                    continue

                # 이미 locked 된 컴포넌트는 원칙적으로 수정 거부.
                # 예외: locked 필드를 잠금 해제 (True → False) 하는 요청은 허용.
                if comp.locked and not (
                    "locked" in patch_data
                    and patch_data["locked"] is False
                    and set(patch_data.keys()) <= {"locked", "anchor"}
                ):
                    raise DocumentGenerationError(
                        f"잠긴 컴포넌트는 수정할 수 없습니다: page_id={page_id!r}, component_id={component_id!r}"
                    )

                # type 변경 시도 차단 -------------------------------------
                if "type" in patch_data and patch_data["type"] != comp.type:
                    raise DocumentGenerationError(
                        f"컴포넌트 타입 변경은 허용되지 않습니다: {comp.type} → {patch_data['type']}"
                    )

                merged = {**comp.model_dump(mode="json"), **patch_data}
                # type/id 는 서버가 보호.
                merged["type"] = comp.type
                merged["id"] = component_id

                try:
                    page.components[idx] = comp.__class__.model_validate(merged)
                except ValidationError:
                    raise
                return

            # 페이지는 찾았으나 컴포넌트 미존재 --------------------------
            raise DocumentGenerationError(
                f"해당 컴포넌트를 찾을 수 없습니다: page_id={page_id!r}, component_id={component_id!r}"
            )

        raise DocumentGenerationError(f"해당 페이지를 찾을 수 없습니다: page_id={page_id!r}")

    @staticmethod
    def _apply_tokens_patch(schema: DocumentSchema, patch_data: dict) -> None:
        """design_tokens 를 ``patch_data`` 로 전체 교체한다.

        부분 병합이 아니라 전체 교체를 채택한 이유: :class:`DesignTokens` 는
        7개 필드 모두 기본값을 가지는 작은 객체라 부분 병합 시 의도하지 않은
        이전 값이 남을 수 있다. 클라이언트는 항상 전체 토큰을 보낸다.
        """

        try:
            schema.design_tokens = DesignTokens.model_validate(patch_data)
        except ValidationError:
            raise

    # ------------------------------------------------------------------
    # Phase 4 S2 D4: Export 비동기 작업 (Celery dispatch + Redis 상태)
    # ------------------------------------------------------------------

    @staticmethod
    async def request_export(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        document_id: UUID,
        *,
        format: str,  # noqa: A002 - FE API 스펙(ExportFormat)과 1:1 매칭 유지
    ) -> UUID:
        """Export 작업을 생성·Celery 로 dispatch 하고 job_id 를 반환한다.

        동작 흐름
        ----------
        1. 문서를 조직 스코프로 조회 → 없음(404) / 타 조직(403) 분기.
        2. format 유효성 검증 (BuildTarget 5 종). 잘못된 값은 400.
        3. ``uuid4()`` job_id 생성 → Redis 에 ``pending`` 초기 상태 저장 (TTL 3600s).
           - user_id / org_id 도 기록: `get_export_status` 에서 권한 재검증.
        4. Celery ``generate_document_export.delay(...)`` 호출.
        5. job_id 반환.

        P4 (Router→Service→Integration) 준수: Router 는 이 메서드만 호출하고,
        Celery dispatch 자체는 service 가 담당. Worker 내부는 DB/빌더/Redis 를
        각각 integration wrapper 로 취급한다.

        Raises:
            DocumentGenerationError: 문서 없음 / 타 조직 / 미지원 포맷.
        """

        # 지연 import 로 순환 의존 회피 (worker → service → worker 순환 방지).
        from app.integrations.document_builders.base import _VALID_TARGETS
        from app.workers.export_worker import (
            EXPORT_JOB_TTL_SECONDS,
            export_job_key,
        )

        # ---- 1) 문서 조회 + 권한 ------------------------------------------
        doc = await db.get(DocumentV2, document_id)
        if doc is None:
            raise DocumentGenerationError("요청한 문서를 찾을 수 없습니다.")
        if doc.organization_id != org_id:
            raise DocumentGenerationError("다른 조직의 문서에는 접근할 수 없습니다.")

        # ---- 2) 포맷 유효성 -----------------------------------------------
        if format not in _VALID_TARGETS:
            raise DocumentGenerationError(
                f"지원하지 않는 문서 포맷입니다: '{format}'. 사용 가능한 포맷: {', '.join(_VALID_TARGETS)}."
            )

        # ---- 3) job_id + Redis 초기 상태 -----------------------------------
        job_id = uuid.uuid4()
        now_iso = datetime.now(UTC).isoformat()
        initial_state = {
            "status": "pending",
            "progress": 0,
            "document_id": str(document_id),
            "user_id": str(user_id),
            "org_id": str(org_id),
            "format": format,
            "result_key": None,
            "download_url": None,
            "error": None,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        # Redis 접근은 app.core.cache 의 async 클라이언트 사용 (FastAPI 경로).
        from app.core.cache import get_redis

        redis = await get_redis()
        if redis is not None:
            try:
                await redis.set(
                    export_job_key(job_id),
                    json.dumps(initial_state, ensure_ascii=False),
                    ex=EXPORT_JOB_TTL_SECONDS,
                )
            except Exception:  # noqa: BLE001 - Redis 실패는 치명적이지만 로그 후 계속
                logger.exception("Redis export 상태 초기화 실패: job_id=%s", job_id)
        else:
            logger.warning("Redis 사용 불가 — export job 상태 초기화를 건너뜁니다.")

        # ---- 4) Celery dispatch -------------------------------------------
        from app.workers.export_worker import generate_document_export

        try:
            generate_document_export.delay(
                job_id=str(job_id),
                document_id=str(document_id),
                format=format,
                organization_overrides=None,
            )
        except Exception as exc:  # noqa: BLE001 - RabbitMQ 연결 실패 등
            # dispatch 실패 시 Redis 상태를 failed 로 반전시켜 폴링 훅이 즉시 종료하도록 한다.
            if redis is not None:
                failure_state = dict(initial_state)
                failure_state["status"] = "failed"
                failure_state["error"] = f"Export 작업 dispatch 에 실패했습니다: {exc}"
                failure_state["updated_at"] = datetime.now(UTC).isoformat()
                try:
                    await redis.set(
                        export_job_key(job_id),
                        json.dumps(failure_state, ensure_ascii=False),
                        ex=EXPORT_JOB_TTL_SECONDS,
                    )
                except Exception:  # noqa: BLE001
                    logger.exception("Redis failed 상태 기록 실패: job_id=%s", job_id)
            raise DocumentGenerationError("Export 작업 등록에 실패했습니다. 잠시 후 다시 시도해 주세요.") from exc

        return job_id

    # ------------------------------------------------------------------
    # Phase 4 S2 D10: Export 결과 프록시 다운로드
    # ------------------------------------------------------------------
    #
    # W4 블로커 대응 (S2 D9 완료 리포트 옵션 C):
    # - 기존 presigned URL 방식은 Docker 내부 hostname (``minio:9000``) 이
    #   응답에 포함되어 FE 브라우저가 resolve 하지 못한다.
    # - URL rewrite 는 AWS SigV4 서명 불일치로 403 을 유발해 불가.
    # - 결론: 백엔드가 MinIO object bytes 를 직접 읽어 StreamingResponse 로
    #   전달하는 API 프록시 엔드포인트를 둔다 (``reports/{id}/download`` 패턴
    #   재사용). presigned URL 은 노출하지 않는다.
    #
    # 본 메서드는 job 상태 검증 + 권한 재확인 + MinIO bytes 로드 + filename
    # 파생을 담당하며, 라우터에서 StreamingResponse 로 감싸기만 한다.

    @staticmethod
    async def get_export_file(
        job_id: UUID,
        user_id: UUID,
        org_id: UUID,
    ) -> tuple[bytes, str, str]:
        """Export 결과물 bytes · content-type · 파일명을 반환한다 (Phase 4 S2 D10).

        Returns:
            ``(payload_bytes, content_type, filename)`` 튜플.

            - payload_bytes: MinIO 에서 가져온 원본 바이트. StreamingResponse
              에서 ``iter([payload_bytes])`` 로 단일 청크로 감싸 전달한다.
              (운영 평균 PPTX ~500KB–5MB 기준 단일 청크가 단순하고 충분.)
            - content_type: ``FORMAT_CONTENT_TYPE`` 맵에서 파생된 MIME.
            - filename: 사용자 저장시 표시되는 파일명. 기본 ``{document_id}.{ext}``
              형식. 한글 안전을 위해 라우터에서 RFC 5987 인코딩한다.

        Raises:
            DocumentGenerationError: 다음 상황별로 구분된 한국어 메시지를 담아
            발생시키며, 라우터가 아래 HTTP 상태로 매핑한다.

            - job 없음/TTL 만료 → 404 "Export 작업을 찾을 수 없습니다"
            - status != "completed" → 409 "아직 완료되지 않은 작업"
            - MinIO object 부재 (NoSuchKey) → 410 "파일이 만료되었습니다"
            - 요청자 user_id/org_id 불일치 → 403
            - Redis 접근 불가 / 상태 JSON 손상 → 404 / 500
        """

        from app.core.cache import get_redis
        from app.workers.export_worker import (
            FORMAT_CONTENT_TYPE,
            export_job_key,
        )

        redis = await get_redis()
        if redis is None:
            raise DocumentGenerationError("Export 작업 상태 저장소에 접근할 수 없습니다.")

        raw = await redis.get(export_job_key(job_id))
        if raw is None:
            # TTL 만료이거나 존재하지 않는 job_id.
            raise DocumentGenerationError(
                "요청한 Export 작업을 찾을 수 없습니다. 만료되었거나 존재하지 않는 job_id 입니다."
            )

        try:
            state = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.exception("Export 상태 JSON 파싱 실패: job_id=%s", job_id)
            raise DocumentGenerationError("Export 작업 상태를 해석할 수 없습니다.") from exc

        # ---- 권한 재검증 (get_export_status 와 동일 패턴) ------------------
        owner_org = state.get("org_id")
        owner_user = state.get("user_id")
        if owner_org is not None and owner_org != str(org_id):
            raise DocumentGenerationError("다른 조직의 Export 작업에는 접근할 수 없습니다.")
        if owner_user is not None and owner_user != str(user_id):
            raise DocumentGenerationError("다른 사용자의 Export 작업에는 접근할 수 없습니다.")

        # ---- 완료 상태 확인 ----------------------------------------------
        status_value = state.get("status")
        if status_value != "completed":
            # pending/running/failed 모두 다운로드 불가. 409 로 매핑된다.
            raise DocumentGenerationError(f"아직 완료되지 않은 Export 작업입니다. 현재 상태: {status_value!r}.")

        result_key = state.get("result_key")
        if not result_key:
            # completed 인데 result_key 가 비어있다면 worker 버그.
            raise DocumentGenerationError("완료된 작업에 결과 파일 키가 기록되어 있지 않습니다.")

        fmt = state.get("format") or "bin"
        document_id = state.get("document_id")

        content_type = FORMAT_CONTENT_TYPE.get(fmt, "application/octet-stream")
        # 기본 파일명: 문서 ID 기반 — DB 조회 없이 빠르게 구성.
        # (title 기반 파일명은 향후 확장 포인트로 남김; 한글 title 은 라우터의
        #  RFC 5987 인코딩으로 안전하게 내려간다.)
        ext = fmt if fmt in FORMAT_CONTENT_TYPE else "bin"
        filename = f"{document_id or job_id}.{ext}"

        # ---- MinIO bytes 획득 (P1: MinIOService 경유) ---------------------
        from minio.error import S3Error

        from app.core.config import get_settings
        from app.integrations.object_storage import MinIOService

        settings = get_settings()
        minio_svc = MinIOService()

        try:
            payload = minio_svc.get_object_bytes(
                bucket=settings.minio_bucket,
                object_name=result_key,
            )
        except S3Error as exc:
            # NoSuchKey (object 이미 제거됨) 는 "파일 만료" 로 표현해 410 매핑.
            if getattr(exc, "code", "") == "NoSuchKey":
                raise DocumentGenerationError("Export 파일이 만료되었거나 삭제되었습니다.") from exc
            # 그 외 S3 오류는 502 로 매핑되도록 일반 메시지.
            logger.exception("MinIO 에서 Export 파일을 읽지 못했습니다: key=%s", result_key)
            raise DocumentGenerationError("Export 파일을 스토리지에서 가져오지 못했습니다.") from exc

        return payload, content_type, filename

    @staticmethod
    async def get_export_status(
        job_id: UUID,
        user_id: UUID,
        org_id: UUID,
    ) -> dict[str, Any]:
        """Export 작업의 현재 상태를 조회한다.

        Returns:
            dict 형태의 상태 뷰. 다음 필드를 보장::

                { "status": str,
                  "progress": int,
                  "download_url": str | None,
                  "error": str | None }

        Raises:
            DocumentGenerationError:
                - Redis 에 상태가 없음 (만료 또는 잘못된 job_id) → 라우터 404.
                - 다른 사용자/조직의 작업 → 라우터 403.
        """

        from app.core.cache import get_redis
        from app.workers.export_worker import export_job_key

        redis = await get_redis()
        if redis is None:
            # Redis 불가 = 상태 불명. 안전하게 404 로 매핑.
            raise DocumentGenerationError("Export 작업 상태 저장소에 접근할 수 없습니다.")

        raw = await redis.get(export_job_key(job_id))
        if raw is None:
            raise DocumentGenerationError(
                "요청한 Export 작업을 찾을 수 없습니다. 만료되었거나 존재하지 않는 job_id 입니다."
            )

        try:
            state = json.loads(raw)
        except json.JSONDecodeError as exc:
            # Redis 값이 깨짐 — 운영 이슈.
            logger.exception("Export 상태 JSON 파싱 실패: job_id=%s", job_id)
            raise DocumentGenerationError("Export 작업 상태를 해석할 수 없습니다.") from exc

        # ---- 권한 재검증 ---------------------------------------------------
        # 조직 검증을 우선 (사용자 탈퇴/이동 가능성). user_id 도 함께 체크.
        owner_org = state.get("org_id")
        owner_user = state.get("user_id")
        if owner_org is not None and owner_org != str(org_id):
            raise DocumentGenerationError("다른 조직의 Export 작업에는 접근할 수 없습니다.")
        if owner_user is not None and owner_user != str(user_id):
            # 같은 조직 내 타 사용자 작업도 조회 불가 — 403.
            raise DocumentGenerationError("다른 사용자의 Export 작업에는 접근할 수 없습니다.")

        # ---- 응답 뷰 조립 -------------------------------------------------
        return {
            "status": state.get("status", "pending"),
            "progress": int(state.get("progress") or 0),
            "download_url": state.get("download_url"),
            "error": state.get("error"),
        }
