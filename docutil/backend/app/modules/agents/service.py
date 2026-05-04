"""Business logic for AI agent management."""

from __future__ import annotations

import uuid
from uuid import UUID

import logging

from fastapi import HTTPException, status
from sqlalchemy import func, select

from .models import Agent

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from .schemas import AgentCreate, AgentUpdate

logger = logging.getLogger(__name__)


class AgentService:
    """Stateless service methods for AI agent CRUD."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_agent(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        data: AgentCreate,
    ) -> Agent:
        """Create a new AI agent."""
        agent = Agent(
            organization_id=org_id,
            name=data.name,
            description=data.description,
            agent_type=data.agent_type,
            system_prompt=data.system_prompt,
            llm_model=data.llm_model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            is_active=True,
            created_by=user_id,
        )
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        return agent

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @staticmethod
    async def get_agents(
        db: AsyncSession,
        org_id: UUID,
        agent_type: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Agent], int]:
        """Return a paginated list of agents for an organisation.

        Optionally filter by ``agent_type`` ('chatbot', 'report', 'proposal').
        """
        base_query = select(Agent).where(
            Agent.organization_id == org_id,
        )

        if agent_type is not None:
            base_query = base_query.where(Agent.agent_type == agent_type)

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Paginated items
        offset = (page - 1) * size
        items_query = base_query.order_by(Agent.ins_dt.desc()).offset(offset).limit(size)
        result = await db.execute(items_query)
        items = list(result.scalars().all())

        return items, total

    # ------------------------------------------------------------------
    # Get single
    # ------------------------------------------------------------------

    @staticmethod
    async def get_agent(
        db: AsyncSession,
        agent_id: UUID,
        org_id: UUID | None = None,
    ) -> Agent:
        """Fetch a single agent by ID, or 404.

        When ``org_id`` is provided the query is scoped to that organisation.
        When ``org_id`` is ``None`` (internal use) the lookup is global.
        """
        conditions = [Agent.id == agent_id]
        if org_id is not None:
            conditions.append(Agent.organization_id == org_id)

        stmt = select(Agent).where(*conditions)
        result = await db.execute(stmt)
        agent = result.scalar_one_or_none()

        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_id}' not found.",
            )
        return agent

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update_agent(
        db: AsyncSession,
        agent_id: UUID,
        org_id: UUID,
        data: AgentUpdate,
    ) -> Agent:
        """Update an agent's fields."""
        agent = await AgentService.get_agent(db, agent_id, org_id)

        update_fields = data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(agent, field, value)

        await db.flush()
        await db.refresh(agent)
        return agent

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_agent(
        db: AsyncSession,
        agent_id: UUID,
        org_id: UUID,
    ) -> None:
        """Delete an agent by ID. Raises 404 if not found."""
        agent = await AgentService.get_agent(db, agent_id, org_id)
        await db.delete(agent)
        await db.flush()
