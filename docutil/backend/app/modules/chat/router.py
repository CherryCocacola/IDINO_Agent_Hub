"""
FastAPI router for chat session and message endpoints.

All routes in this module are mounted under the ``/chat`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentOrganizationId, CurrentUser

from .schemas import (
    ChatMessageCreate,
    ChatMessageListResponse,
    ChatMessageSendResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
)
from .service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["chat"])


# ---------------------------------------------------------------------------
# GET /chat/sessions -- List sessions
# ---------------------------------------------------------------------------


@router.get(
    "/chat/sessions",
    response_model=ChatSessionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List chat sessions",
    description="Retrieve a paginated list of the current user's chat sessions.",
)
async def list_sessions(
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    size: int = Query(default=20, ge=1, le=100, description="Items per page."),
) -> ChatSessionListResponse:
    """Return the authenticated user's chat sessions."""

    items, total = await ChatService.get_sessions(
        db=db,
        user_id=current_user.user_id,
        org_id=org_id,
        page=page,
        size=size,
    )

    return ChatSessionListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /chat/sessions -- Create session
# ---------------------------------------------------------------------------


@router.post(
    "/chat/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
    description=(
        "Create a new chat session. Optionally scope it to a search scope "
        "or a specific set of documents."
    ),
)
async def create_session(
    payload: ChatSessionCreate,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Create a new chat session for the authenticated user."""

    return await ChatService.create_session(
        db=db,
        user_id=current_user.user_id,
        org_id=org_id,
        data=payload,
    )


# ---------------------------------------------------------------------------
# GET /chat/sessions/{session_id} -- Get session
# ---------------------------------------------------------------------------


@router.get(
    "/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a chat session",
    description="Retrieve details of a specific chat session.",
    responses={
        404: {"description": "Session not found."},
    },
)
async def get_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    """Return a single chat session by ID."""

    try:
        return await ChatService.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# DELETE /chat/sessions/{session_id} -- Delete session
# ---------------------------------------------------------------------------


@router.delete(
    "/chat/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete a chat session",
    description=(
        "Soft-delete a chat session by marking it inactive. "
        "Messages are retained for audit purposes."
    ),
    responses={
        404: {"description": "Session not found."},
    },
)
async def delete_session(
    session_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a chat session."""

    try:
        await ChatService.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# GET /chat/sessions/{session_id}/messages -- Get messages
# ---------------------------------------------------------------------------


@router.get(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatMessageListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get session messages",
    description=(
        "Retrieve a paginated list of messages within a chat session, "
        "ordered chronologically (oldest first)."
    ),
    responses={
        404: {"description": "Session not found."},
    },
)
async def get_messages(
    session_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    size: int = Query(default=50, ge=1, le=200, description="Items per page."),
) -> ChatMessageListResponse:
    """Return messages for a chat session."""

    # Verify session ownership first
    try:
        await ChatService.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    items, total = await ChatService.get_messages(
        db=db,
        session_id=session_id,
        page=page,
        size=size,
    )

    return ChatMessageListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /chat/sessions/{session_id}/messages -- Send message (REST fallback)
# ---------------------------------------------------------------------------


@router.post(
    "/chat/sessions/{session_id}/messages",
    response_model=ChatMessageSendResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a chat message (REST)",
    description=(
        "Send a message via REST as a fallback when WebSocket is unavailable. "
        "Processes the message synchronously and returns the assistant response."
    ),
    responses={
        404: {"description": "Session not found."},
    },
)
async def send_message(
    session_id: UUID,
    payload: ChatMessageCreate,
    current_user: CurrentUser,
    org_id: CurrentOrganizationId,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageSendResponse:
    """Process a user message and return the assistant response."""

    # Verify session ownership
    try:
        await ChatService.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    # Collect streaming response into a single result
    from .schemas import ChatMessageResponse

    final_content = ""
    final_citations = None
    final_metadata: dict = {}
    message_id = None

    async for ws_response in ChatService.process_message(
        db=db,
        session_id=session_id,
        user_id=current_user.user_id,
        content=payload.content,
        user_role=current_user.role,
        user_dept_id=current_user.department_id,
    ):
        if ws_response.type == "chunk":
            final_content += ws_response.data.get("text", "")
        elif ws_response.type == "citations":
            final_citations = ws_response.data.get("citations")
        elif ws_response.type == "metadata":
            final_metadata = ws_response.data
        elif ws_response.type == "done":
            message_id = ws_response.data.get("message_id")

    await db.commit()

    from datetime import datetime, timezone

    return ChatMessageSendResponse(
        message=ChatMessageResponse(
            id=message_id or session_id,
            session_id=session_id,
            role="assistant",
            content=final_content,
            citations=final_citations,
            model_used=final_metadata.get("model_used"),
            token_count_input=final_metadata.get("token_count_input"),
            token_count_output=final_metadata.get("token_count_output"),
            latency_ms=final_metadata.get("latency_ms"),
            hallucination_score=final_metadata.get("hallucination_score"),
            created_at=datetime.now(timezone.utc),
        )
    )
