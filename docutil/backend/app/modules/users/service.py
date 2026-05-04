"""Business logic for user management."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password

from .models import User
from .schemas import UserCreate, UserUpdate


class UserService:
    """Static service methods for user CRUD operations."""

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user with a hashed password.

        Raises 409 if the username or email already exists.
        """
        # Check uniqueness of username
        existing = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_data.username}' is already taken.",
            )

        # Check uniqueness of email
        existing = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{user_data.email}' is already registered.",
            )

        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            organization_id=user_data.organization_id,
            department_id=user_data.department_id,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user(db: AsyncSession, user_id: UUID) -> User:
        """Return a single user by ID or raise 404."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found.",
            )
        return user

    @staticmethod
    async def get_users(
        db: AsyncSession,
        org_id: UUID,
        page: int = 1,
        size: int = 20,
        role_filter: str | None = None,
        status_filter: str | None = None,
        search_filter: str | None = None,
    ) -> tuple[list[User], int]:
        """Return a paginated list of users within an organisation.

        ``search_filter`` 는 username/email 에 대한 ILIKE 부분 일치 검색용.
        공백만 들어오는 경우는 무시한다.

        Returns a tuple of ``(users, total_count)``.
        """
        base_query = select(User).where(User.organization_id == org_id)

        if role_filter is not None:
            base_query = base_query.where(User.role == role_filter)
        if status_filter is not None:
            base_query = base_query.where(User.status == status_filter)
        if search_filter is not None and search_filter.strip():
            # username 또는 email 에 부분 일치 (대소문자 무시)
            like = f"%{search_filter.strip()}%"
            base_query = base_query.where(
                or_(User.username.ilike(like), User.email.ilike(like))
            )

        # Total count (with same filters)
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Paginated results
        offset = (page - 1) * size
        items_query = (
            base_query
            .order_by(User.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_query)
        users = list(result.scalars().all())

        return users, total

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: UUID,
        user_data: UserUpdate,
    ) -> User:
        """Update a user with the supplied fields."""
        user = await UserService.get_user(db, user_id)

        update_fields = user_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(user, field, value)

        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> None:
        """Hard-delete a user by ID. Raises 404 if not found."""
        user = await UserService.get_user(db, user_id)
        await db.delete(user)
        await db.flush()

    @staticmethod
    async def update_status(
        db: AsyncSession,
        user_id: UUID,
        new_status: str,
    ) -> User:
        """Toggle a user's status (active / inactive / locked).

        Raises 400 if the supplied status is not valid.
        """
        allowed = {"active", "inactive", "locked"}
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{new_status}'. Allowed: {sorted(allowed)}.",
            )

        user = await UserService.get_user(db, user_id)
        user.status = new_status
        await db.flush()
        await db.refresh(user)
        return user
