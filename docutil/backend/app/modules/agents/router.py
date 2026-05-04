"""FastAPI router for AI agent management endpoints.

All routes in this module are mounted under the ``/agents`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

import uuid
from uuid import UUID


from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.database import get_db
from app.core.dependencies import require_role

from .schemas import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
)
from .service import AgentService

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.security import TokenData

router = APIRouter(prefix="", tags=["agents"])

# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------
_require_admin = require_role(["super_admin", "admin", "org_admin"])
_require_member = require_role(["super_admin", "admin", "org_admin", "editor", "member", "viewer"])


# ---------------------------------------------------------------------------
# GET /agents
# ---------------------------------------------------------------------------


@router.get(
    "/agents",
    response_model=AgentListResponse,
    summary="List AI agents",
    description="Return a paginated list of AI agents for the organisation.",
)
async def list_agents(
    agent_type: str | None = Query(
        default=None,
        description="Filter by agent type ('chatbot', 'report', or 'proposal').",
    ),
    page: int = Query(1, ge=1, description="Page number."),
    size: int = Query(20, ge=1, le=100, description="Items per page."),
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> AgentListResponse:
    """List all AI agents visible to the user's organisation."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    items, total = await AgentService.get_agents(
        db,
        org_id=current_user.organization_id,
        agent_type=agent_type,
        page=page,
        size=size,
    )
    return AgentListResponse(
        items=[AgentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# POST /agents
# ---------------------------------------------------------------------------


@router.post(
    "/agents",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an AI agent",
    description="Create a new AI agent configuration.",
)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> AgentResponse:
    """Create a new AI agent."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    agent = await AgentService.create_agent(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.user_id,
        data=data,
    )
    return AgentResponse.model_validate(agent)


# ---------------------------------------------------------------------------
# GET /agents/{agent_id}
# ---------------------------------------------------------------------------


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Get AI agent details",
)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_member),
) -> AgentResponse:
    """Retrieve a single AI agent by ID."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    agent = await AgentService.get_agent(
        db,
        agent_id=agent_id,
        org_id=current_user.organization_id,
    )
    return AgentResponse.model_validate(agent)


# ---------------------------------------------------------------------------
# PUT /agents/{agent_id}
# ---------------------------------------------------------------------------


@router.put(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    summary="Update an AI agent",
)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> AgentResponse:
    """Update the configuration of an existing AI agent."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    agent = await AgentService.update_agent(
        db,
        agent_id=agent_id,
        org_id=current_user.organization_id,
        data=payload,
    )
    return AgentResponse.model_validate(agent)


# ---------------------------------------------------------------------------
# DELETE /agents/{agent_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Delete an AI agent",
)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(_require_admin),
) -> Response:
    """Remove an AI agent permanently."""
    if current_user.organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with an organisation.",
        )

    await AgentService.delete_agent(
        db,
        agent_id=agent_id,
        org_id=current_user.organization_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
