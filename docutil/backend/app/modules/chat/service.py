"""
Chat business logic.

Manages chat sessions, persists messages, and orchestrates the
search-augmented LLM streaming pipeline used by the WebSocket handler.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.search.service import SearchService

from .schemas import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    WebSocketResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ChatService:
    """Stateless service for chat session and message operations.

    All public methods receive their dependencies explicitly so that
    callers control the transaction boundary.
    """

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        data: ChatSessionCreate,
    ) -> ChatSessionResponse:
        """Create a new chat session.

        Parameters
        ----------
        db:
            Active database session.
        user_id:
            Authenticated user creating the session.
        org_id:
            Organisation scope for multi-tenancy.
        data:
            Session creation payload (title, scope, scoped doc IDs).
        """

        from app.modules.chat.models import ChatSession

        session = ChatSession(
            user_id=user_id,
            organization_id=org_id,
            title=data.title,
            search_scope_id=data.search_scope_id,
            scoped_document_ids=([str(d) for d in data.scoped_document_ids] if data.scoped_document_ids else None),
            is_active=True,
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)

        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            organization_id=session.organization_id,
            search_scope_id=session.search_scope_id,
            title=session.title,
            scoped_document_ids=(
                [UUID(str(d)) for d in session.scoped_document_ids] if session.scoped_document_ids else None
            ),
            is_active=session.is_active,
            created_at=session.ins_dt,
            updated_at=session.upd_dt,
        )

    @staticmethod
    async def get_sessions(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[ChatSessionResponse], int]:
        """Return a paginated list of the user's chat sessions.

        Returns
        -------
        tuple
            ``(items, total_count)``
        """

        from app.modules.chat.models import ChatSession

        offset = (page - 1) * size

        # 트랙 #102b fix(2026-05-19): delete_session 이 is_active=False 로 soft-delete 하므로
        # list 응답에서도 active session 만 노출해야 한다. 이전에는 필터가 없어 삭제된 세션이
        # 새로고침 시 다시 나타나는 결함이 있었다.
        # Total count
        count_stmt = (
            select(func.count())
            .select_from(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.organization_id == org_id,
                ChatSession.is_active.is_(True),
            )
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        # Paginated items
        stmt = (
            select(ChatSession)
            .where(
                ChatSession.user_id == user_id,
                ChatSession.organization_id == org_id,
                ChatSession.is_active.is_(True),
            )
            .order_by(ChatSession.upd_dt.desc())
            .offset(offset)
            .limit(size)
        )

        result = await db.execute(stmt)
        rows = result.scalars().all()

        items = [
            ChatSessionResponse(
                id=s.id,
                user_id=s.user_id,
                organization_id=s.organization_id,
                search_scope_id=s.search_scope_id,
                title=s.title,
                scoped_document_ids=([UUID(str(d)) for d in s.scoped_document_ids] if s.scoped_document_ids else None),
                is_active=s.is_active,
                created_at=s.ins_dt,
                updated_at=s.upd_dt,
            )
            for s in rows
        ]

        return items, total

    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
    ) -> ChatSessionResponse:
        """Retrieve a single chat session by ID.

        Raises
        ------
        ValueError
            If the session does not exist or does not belong to *user_id*.
        """

        from app.modules.chat.models import ChatSession

        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            raise ValueError("Chat session not found.")

        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            organization_id=session.organization_id,
            search_scope_id=session.search_scope_id,
            title=session.title,
            scoped_document_ids=(
                [UUID(str(d)) for d in session.scoped_document_ids] if session.scoped_document_ids else None
            ),
            is_active=session.is_active,
            created_at=session.ins_dt,
            updated_at=session.upd_dt,
        )

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
    ) -> None:
        """Soft-delete a chat session by marking it inactive.

        Associated messages are retained for audit purposes.

        Raises
        ------
        ValueError
            If the session does not exist or does not belong to *user_id*.
        """

        from app.modules.chat.models import ChatSession

        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            raise ValueError("Chat session not found.")

        session.is_active = False
        await db.flush()

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @staticmethod
    async def get_messages(
        db: AsyncSession,
        session_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[ChatMessageResponse], int]:
        """Return a paginated list of messages within a session.

        Messages are ordered chronologically (oldest first) so the
        client can render them in conversation order.

        Returns
        -------
        tuple
            ``(items, total_count)``
        """

        from app.modules.chat.models import ChatMessage

        offset = (page - 1) * size

        count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session_id)
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.ins_dt.asc())
            .offset(offset)
            .limit(size)
        )

        result = await db.execute(stmt)
        rows = result.scalars().all()

        items = [
            ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                citations=m.citations,
                model_used=m.model_used,
                token_count_input=m.token_count_input,
                token_count_output=m.token_count_output,
                latency_ms=m.latency_ms,
                hallucination_score=m.hallucination_score,
                created_at=m.ins_dt,
            )
            for m in rows
        ]

        return items, total

    # ------------------------------------------------------------------
    # Streaming message processing
    # ------------------------------------------------------------------

    @staticmethod
    async def process_message(
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        content: str,
        options: dict[str, Any] | None = None,
        user_role: str | None = None,
        user_dept_id: UUID | None = None,
    ) -> AsyncGenerator[WebSocketResponse, None]:
        """Process an incoming user message and stream back the response.

        This is the core pipeline used by the WebSocket handler:

        1. Load session context and conversation history.
        2. Persist the user message.
        3. Search within scoped documents for relevant context.
        4. Build the LLM prompt with conversation history + context.
        5. Stream the LLM response, yielding WebSocket-format chunks.
        6. Persist the assistant message with citations and metadata.
        7. Yield a final ``done`` frame.

        Yields
        ------
        WebSocketResponse
            Frames of types ``status``, ``chunk``, ``citations``,
            ``metadata``, and ``done``.
        """

        from app.modules.chat.models import ChatMessage, ChatSession

        settings = get_settings()
        start = time.perf_counter()

        # -- 1. Load session ---------------------------------------------------
        yield WebSocketResponse(
            type="status",
            data={"message": "Loading session context..."},
        )

        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session is None:
            yield WebSocketResponse(
                type="status",
                data={"message": "Error: session not found.", "error": True},
            )
            return

        # Load recent conversation history (last 20 messages)
        history_stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.ins_dt.desc())
            .limit(20)
        )
        history_result = await db.execute(history_stmt)
        history_rows = list(reversed(history_result.scalars().all()))

        # -- 2. Save user message ----------------------------------------------
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=content,
        )
        db.add(user_message)
        await db.flush()

        # Auto-generate title from first message if not set
        if session.title is None:
            session.title = content[:100] + ("..." if len(content) > 100 else "")
            await db.flush()

        # -- 3. Search for relevant context ------------------------------------
        deep_search = bool(options.get("deep_search", False)) if options else False

        if deep_search:
            yield WebSocketResponse(
                type="status",
                data={"message": "심층 검색을 수행합니다..."},
            )
        else:
            yield WebSocketResponse(
                type="status",
                data={"message": "Searching documents..."},
            )

        scope_id = session.search_scope_id
        doc_ids = [UUID(str(d)) for d in session.scoped_document_ids] if session.scoped_document_ids else None

        # 검색 단계는 OpenAI 임베딩 API 를 호출하므로 429/네트워크 오류로 실패할 수
        # 있다. 실패해도 챗봇 자체는 답변을 시도해야 사용자 경험이 좋으므로,
        # 빈 컨텍스트로 LLM 단계에 진입하고 에러 사유를 status 프레임으로 알린다.
        try:
            if deep_search:
                from app.modules.search.agentic_search import AgenticSearchService

                search_response = await AgenticSearchService.agentic_search(
                    db=db,
                    query=content,
                    scope_id=scope_id,
                    doc_ids=doc_ids,
                    org_id=session.organization_id,
                    max_results=8,
                    user_id=user_id,
                    user_role=user_role,
                    user_dept_id=user_dept_id,
                    as_user_view=True,
                )
            else:
                search_response = await SearchService.hybrid_search(
                    db=db,
                    query=content,
                    scope_id=scope_id,
                    doc_ids=doc_ids,
                    org_id=session.organization_id,
                    max_results=8,
                    user_id=user_id,
                    user_role=user_role,
                    user_dept_id=user_dept_id,
                    as_user_view=True,
                )
            context_chunks = [r.content for r in search_response.results]
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 429:
                search_warning = (
                    "OpenAI 임베딩 사용량 한도(429)를 초과해 문서 검색을 건너뜁니다. "
                    "관리자에게 결제/한도 갱신을 요청해주세요."
                )
            elif status_code == 401:
                search_warning = "임베딩 API 키 인증 실패(401). 관리자에게 API 키 확인을 요청해주세요."
            else:
                search_warning = f"문서 검색이 실패했습니다(HTTP {status_code})."
            logger.warning("Embedding search failed: status=%s", status_code)
            yield WebSocketResponse(
                type="status",
                data={"message": search_warning, "warning": True},
            )
            # 검색 실패 시에도 LLM 응답을 시도하기 위해 빈 응답으로 fallback.
            search_response = SimpleNamespace(results=[])
            context_chunks = []
        except Exception:
            logger.exception("Document search failed")
            yield WebSocketResponse(
                type="status",
                data={
                    "message": "문서 검색 중 오류가 발생했습니다. 컨텍스트 없이 답변을 시도합니다.",
                    "warning": True,
                },
            )
            search_response = SimpleNamespace(results=[])
            context_chunks = []

        # -- 4. Build LLM prompt -----------------------------------------------
        yield WebSocketResponse(
            type="status",
            data={"message": "Generating response..."},
        )

        messages = ChatService._build_llm_messages(
            history=history_rows,
            context_chunks=context_chunks,
            user_query=content,
        )

        # -- 5. Stream LLM response --------------------------------------------
        full_answer = ""
        token_count_input = 0
        token_count_output = 0

        # Phase 7 — R2 완전 보강: OpenAI httpx 직접 스트리밍을 AgentHubClient.chat_stream
        # 위임으로 교체 (anti-patterns.md §1 위반 해소).
        # - 엔드포인트: AgentHub `POST /v1/chat/completions` (stream=True)
        # - 인증: `X-API-Key` (환경변수 AGENTHUB_API_KEY) — AgentHub 가 라우팅/사용량/PII 처리.
        # - AgentCode: chat 흐름은 `docutil-rag-chat` 사용 (factory.create_llm_client 매핑과 일치).
        # - chunk 형식: OpenAI ChatCompletionChunk 와 동일 (`choices[0].delta.content` + `usage`)
        #   → 기존 token_count_input/output usage 추출 로직 그대로 보존.
        from app.integrations.agenthub_client import (
            AgentHubError,
            get_agenthub_client,
        )

        temperature = options.get("temperature", settings.llm_temperature) if options else settings.llm_temperature
        max_tokens = options.get("max_tokens", settings.llm_max_tokens) if options else settings.llm_max_tokens

        try:
            agenthub = get_agenthub_client()
            async for chunk_data in agenthub.chat_stream(
                agent_code="docutil-rag-chat",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                try:
                    delta = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        full_answer += delta
                        token_count_output += 1
                        yield WebSocketResponse(
                            type="chunk",
                            data={"text": delta},
                        )

                    # AgentHub 가 OpenAI 호환 usage 를 전달하면 정확한 토큰 수로 덮어쓴다.
                    usage = chunk_data.get("usage")
                    if usage:
                        token_count_input = usage.get("prompt_tokens", token_count_input)
                        token_count_output = usage.get("completion_tokens", token_count_output)
                except Exception:
                    logger.debug("Skipping unparseable AgentHub SSE chunk")

        except AgentHubError as exc:
            # AgentHub 가 HTTP 4xx/5xx 또는 네트워크 오류를 한국어 메시지의 AgentHubError 로
            # 변환해서 던진다. status_code 별로 사용자 안내문을 분기.
            status_code = exc.status_code
            if status_code == 429:
                full_answer = "AI 사용량 한도(429)를 초과했습니다. 관리자에게 결제/한도 갱신을 요청해주세요."
            elif status_code in (401, 403):
                full_answer = "AI 게이트웨이 인증에 실패했습니다. 관리자에게 AgentHub API 키 설정 확인을 요청해주세요."
            elif status_code and 500 <= status_code < 600:
                full_answer = (
                    f"AI 서비스가 일시적으로 응답하지 않습니다(HTTP {status_code}). 잠시 후 다시 시도해주세요."
                )
            else:
                # AgentHubError 메시지를 사용자에게 그대로 노출 (이미 한국어).
                full_answer = str(exc) or ("AI 호출이 실패했습니다. 관리자에게 문의해주세요.")
            logger.warning("AgentHub chat_stream 실패: status=%s err=%s", status_code, exc)
            yield WebSocketResponse(type="chunk", data={"text": full_answer})
        except Exception:
            # AgentHubClient 가 변환하지 못한 예외(예: 환경변수 미설정 ValueError 등).
            logger.exception("LLM streaming failed (AgentHub 위임)")
            full_answer = "응답 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            yield WebSocketResponse(type="chunk", data={"text": full_answer})

        # -- 6. Build citations and metadata -----------------------------------
        citations = [
            {
                "document_id": str(r.document_id),
                "document_name": r.document_name,
                "page_number": r.page_number,
                "snippet": r.content[:300],
                "relevance_score": min(r.score, 1.0),
            }
            for r in search_response.results
        ]

        yield WebSocketResponse(
            type="citations",
            data={"citations": citations},
        )

        latency_ms = int((time.perf_counter() - start) * 1000)

        # Hallucination check (lightweight)
        hallucination_score = await SearchService._check_hallucination(
            answer=full_answer,
            context_chunks=context_chunks,
        )

        metadata = {
            "model_used": settings.llm_model,
            "token_count_input": token_count_input,
            "token_count_output": token_count_output,
            "latency_ms": latency_ms,
            "hallucination_score": hallucination_score,
        }

        yield WebSocketResponse(
            type="metadata",
            data=metadata,
        )

        # -- 7. Persist assistant message --------------------------------------
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=full_answer,
            citations=citations if citations else None,
            model_used=settings.llm_model,
            token_count_input=token_count_input,
            token_count_output=token_count_output,
            latency_ms=latency_ms,
            hallucination_score=hallucination_score,
        )
        db.add(assistant_message)

        # Update session timestamp (DB 컬럼명은 upd_dt)
        session.upd_dt = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        await db.flush()

        yield WebSocketResponse(
            type="done",
            data={"message_id": str(assistant_message.id)},
        )

    # ==================================================================
    # Private helpers
    # ==================================================================

    @staticmethod
    def _build_llm_messages(
        history: list[Any],
        context_chunks: list[str],
        user_query: str,
    ) -> list[dict[str, str]]:
        """Assemble the message list for the LLM API call.

        Includes a system prompt, numbered context passages, conversation
        history, and the current user query.
        """

        numbered_context = "\n\n".join(f"[{i + 1}] {chunk}" for i, chunk in enumerate(context_chunks))

        system_prompt = (
            "You are a knowledgeable document assistant. Answer the user's "
            "questions using ONLY the provided context. Include inline "
            "citation markers [1], [2], etc. when referencing specific "
            "passages. If the context does not contain enough information "
            "to answer, say so honestly.\n\n"
            f"Context:\n{numbered_context}"
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add conversation history
        for msg in history:
            messages.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                }
            )

        # Add current query
        messages.append(
            {
                "role": "user",
                "content": user_query,
            }
        )

        return messages
