"""
WebSocket endpoint for real-time streaming chat.

Handles authentication via an initial ``auth`` message sent after connection,
manages the connection lifecycle, and bridges incoming messages to
``ChatService.process_message`` which yields streamed response chunks.

Security: Tokens are never passed as URL query parameters. Instead, the client
connects without credentials and sends ``{"type": "auth", "token": "..."}``
as its first message.
"""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.security import TokenData, decode_token

from .schemas import WebSocketMessage, WebSocketResponse
from .service import ChatService

logger = logging.getLogger(__name__)

ws_router = APIRouter(tags=["chat-websocket"])

# Maximum time (seconds) the server waits for the auth message after accept.
_AUTH_TIMEOUT_SECONDS = 10


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@ws_router.websocket("/chat/ws/{session_id}")
async def ws_chat(
    websocket: WebSocket,
    session_id: UUID,
) -> None:
    """Handle a WebSocket connection for streaming chat.

    Authentication
    --------------
    The client opens the connection **without credentials** and immediately
    sends an ``auth`` message containing the JWT::

        ws://host/chat/ws/{session_id}

        → {"type": "auth", "token": "<jwt>"}
        ← {"type": "status", "data": {"message": "Authenticated. Ready to chat."}}

    The server closes the connection with code **4001** if:
    * No ``auth`` message arrives within 10 seconds.
    * The token is invalid or expired.

    Protocol
    --------
    After authentication the client sends JSON-encoded ``WebSocketMessage``
    objects and receives ``WebSocketResponse`` objects.

    Supported inbound message types:

    * ``message`` -- sends a chat message; the server streams back
      ``status``, ``chunk``, ``citations``, ``metadata``, and ``done``
      frames.
    * ``ping`` -- keep-alive; the server responds with a ``status`` frame.

    Error Handling
    --------------
    * Authentication failures close the connection with code **4001**.
    * Malformed payloads return an error ``status`` frame but keep the
      connection open so the client can retry.
    * Internal errors are logged and surfaced as error ``status`` frames.
    """

    # -- 1. Accept connection (no credentials in URL) ---------------------------
    await websocket.accept()

    # -- 2. Wait for auth message -----------------------------------------------
    user = await _wait_for_auth(websocket)

    if user is None:
        return  # connection already closed by _wait_for_auth

    logger.info(
        "WebSocket authenticated: user=%s session=%s",
        user.user_id,
        session_id,
    )

    await _send(
        websocket,
        WebSocketResponse(
            type="status",
            data={"message": "Authenticated. Ready to chat."},
        ),
    )

    # -- 3. Message loop --------------------------------------------------------
    try:
        while True:
            raw = await websocket.receive_text()

            # Parse inbound message
            try:
                msg = WebSocketMessage.model_validate_json(raw)
            except Exception as parse_err:
                await _send(
                    websocket,
                    WebSocketResponse(
                        type="status",
                        data={
                            "message": f"Invalid message format: {parse_err}",
                            "error": True,
                        },
                    ),
                )
                continue

            # Handle ping / keep-alive
            if msg.type == "ping":
                await _send(
                    websocket,
                    WebSocketResponse(
                        type="status",
                        data={"message": "pong"},
                    ),
                )
                continue

            # Handle chat message
            if msg.type == "message":
                if not msg.content or not msg.content.strip():
                    await _send(
                        websocket,
                        WebSocketResponse(
                            type="status",
                            data={
                                "message": "Message content cannot be empty.",
                                "error": True,
                            },
                        ),
                    )
                    continue

                await _handle_chat_message(
                    websocket=websocket,
                    session_id=session_id,
                    user=user,
                    content=msg.content.strip(),
                    options=msg.options,
                )
                continue

            # Unknown type
            await _send(
                websocket,
                WebSocketResponse(
                    type="status",
                    data={
                        "message": f"Unknown message type: '{msg.type}'.",
                        "error": True,
                    },
                ),
            )

    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected: user=%s session=%s",
            user.user_id,
            session_id,
        )
    except Exception:
        logger.exception(
            "WebSocket error: user=%s session=%s",
            user.user_id,
            session_id,
        )
        try:
            await _send(
                websocket,
                WebSocketResponse(
                    type="status",
                    data={
                        "message": "Internal server error. Connection closing.",
                        "error": True,
                    },
                ),
            )
            await websocket.close(code=1011, reason="Internal server error.")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _wait_for_auth(websocket: WebSocket) -> TokenData | None:
    """Wait for an ``auth`` message and validate the token.

    Returns ``TokenData`` on success, or ``None`` if authentication failed
    (the connection is closed before returning ``None``).
    """

    try:
        raw = await asyncio.wait_for(
            websocket.receive_text(),
            timeout=_AUTH_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("WebSocket authentication timed out")
        await websocket.close(
            code=4001,
            reason="Authentication timed out. Send auth message within %d seconds."
            % _AUTH_TIMEOUT_SECONDS,
        )
        return None
    except WebSocketDisconnect:
        return None

    # Parse auth payload
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        await websocket.close(
            code=4001,
            reason="Invalid auth message format. Expected JSON with type and token.",
        )
        return None

    msg_type = payload.get("type")
    token = payload.get("token")

    if msg_type != "auth" or not token:
        await websocket.close(
            code=4001,
            reason='First message must be {"type": "auth", "token": "<jwt>"}.',
        )
        return None

    # Validate token
    user = _authenticate_token(token)
    if user is None:
        await websocket.close(
            code=4001,
            reason="Authentication failed. Invalid or expired token.",
        )
        return None

    return user


def _authenticate_token(token: str) -> TokenData | None:
    """Validate a JWT token and return ``TokenData`` or ``None``."""

    try:
        token_data = decode_token(token)
    except Exception:
        logger.warning("WebSocket authentication failed: invalid token")
        return None

    # Ensure the token is an access token
    from app.core.security import TokenType

    if token_data.token_type != TokenType.ACCESS:
        logger.warning("WebSocket authentication failed: wrong token type")
        return None

    return token_data


async def _send(websocket: WebSocket, response: WebSocketResponse) -> None:
    """Serialise and send a ``WebSocketResponse`` as JSON text."""
    await websocket.send_text(response.model_dump_json())


async def _handle_chat_message(
    websocket: WebSocket,
    session_id: UUID,
    user: TokenData,
    content: str,
    options: dict | None,
) -> None:
    """Process a chat message within a database session and stream chunks.

    Opens a new database session for each message so that long-lived
    WebSocket connections do not hold a single session open indefinitely.
    """

    async with async_session_factory() as db:
        try:
            async for ws_response in ChatService.process_message(
                db=db,
                session_id=session_id,
                user_id=user.user_id,
                content=content,
                options=options,
                user_role=user.role,
                user_dept_id=user.department_id,
            ):
                await _send(websocket, ws_response)

            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception(
                "Error processing chat message: session=%s", session_id
            )
            await _send(
                websocket,
                WebSocketResponse(
                    type="status",
                    data={
                        "message": "Failed to process message. Please try again.",
                        "error": True,
                    },
                ),
            )
