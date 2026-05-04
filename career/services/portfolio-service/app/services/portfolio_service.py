"""Portfolio Service - Business Logic"""
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx

from ..config import settings
from ..database import get_db_pool
from ..schemas.portfolio import (
    ArtifactType,
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioSummaryResponse,
    PortfolioTypeInfo,
    PortfolioTypesResponse,
)

logger = logging.getLogger(__name__)


class PortfolioService:
    """Service for managing student portfolios"""

    # Type display info
    TYPE_INFO = {
        ArtifactType.GITHUB: {
            "display_name": "GitHub",
            "description": "GitHub repository or profile",
            "icon": "github"
        },
        ArtifactType.NOTION: {
            "display_name": "Notion",
            "description": "Notion page or workspace",
            "icon": "notion"
        },
        ArtifactType.BLOG: {
            "display_name": "Blog",
            "description": "Personal or technical blog",
            "icon": "blog"
        },
        ArtifactType.WEBSITE: {
            "display_name": "Website",
            "description": "Personal portfolio website",
            "icon": "globe"
        },
        ArtifactType.PROJECT: {
            "display_name": "Project",
            "description": "Project documentation or demo",
            "icon": "folder"
        },
        ArtifactType.PAPER: {
            "display_name": "Paper",
            "description": "Research paper or publication",
            "icon": "file-text"
        },
        ArtifactType.VIDEO: {
            "display_name": "Video",
            "description": "Video content or presentation",
            "icon": "video"
        },
        ArtifactType.DOCUMENT: {
            "display_name": "Document",
            "description": "Document or report",
            "icon": "file"
        },
        ArtifactType.CERTIFICATION: {
            "display_name": "자격증",
            "description": "Certification or license",
            "icon": "award"
        },
        ArtifactType.EXPERIENCE: {
            "display_name": "경험",
            "description": "Work or internship experience",
            "icon": "briefcase"
        },
        ArtifactType.AWARD: {
            "display_name": "수상",
            "description": "Award or recognition",
            "icon": "trophy"
        },
        ArtifactType.PRESENTATION: {
            "display_name": "발표",
            "description": "Presentation or talk",
            "icon": "presentation"
        },
        ArtifactType.DESIGN: {
            "display_name": "디자인",
            "description": "Design work or portfolio",
            "icon": "palette"
        },
        ArtifactType.CODE: {
            "display_name": "코드",
            "description": "Code sample or snippet",
            "icon": "code"
        },
        ArtifactType.OTHER: {
            "display_name": "Other",
            "description": "Other portfolio item",
            "icon": "link"
        },
    }

    async def get_student_portfolios(self, student_id: str) -> PortfolioListResponse:
        """Get all portfolio items for a student"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            rows = await conn.fetch(
                """
                SELECT portfolio_id, student_id, artifact_type, title, url,
                       description, is_primary, ins_dt as created_at, upd_dt as updated_at
                FROM tb_portfolio
                WHERE student_id = $1
                ORDER BY is_primary DESC, ins_dt DESC
                """,
                student_id
            )

            items = [self._row_to_response(row) for row in rows]
            primary_item = next((item for item in items if item.is_primary), None)

            return PortfolioListResponse(
                student_id=student_id,
                total_count=len(items),
                items=items,
                primary_item=primary_item
            )

    async def get_portfolio_by_id(self, portfolio_id: str) -> Optional[PortfolioResponse]:
        """Get a specific portfolio item by ID"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            row = await conn.fetchrow(
                """
                SELECT portfolio_id, student_id, artifact_type, title, url,
                       description, is_primary, ins_dt as created_at, upd_dt as updated_at
                FROM tb_portfolio
                WHERE portfolio_id = $1
                """,
                uuid.UUID(portfolio_id)
            )

            if row:
                return self._row_to_response(row)
            return None

    async def create_portfolio(self, data: PortfolioCreate) -> PortfolioResponse:
        """Create a new portfolio item"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # If this is primary, unset other primary items
            if data.is_primary:
                await conn.execute(
                    """
                    UPDATE tb_portfolio SET is_primary = FALSE, upd_dt = CURRENT_TIMESTAMP
                    WHERE student_id = $1 AND is_primary = TRUE
                    """,
                    data.student_id
                )

            row = await conn.fetchrow(
                """
                INSERT INTO tb_portfolio (
                    student_id, artifact_type, title, url, description, is_primary,
                    ins_user_id, ins_dt
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'SYSTEM', CURRENT_TIMESTAMP)
                RETURNING portfolio_id, student_id, artifact_type, title, url,
                          description, is_primary, ins_dt as created_at, upd_dt as updated_at
                """,
                data.student_id,
                data.artifact_type.value,
                data.title,
                data.url,
                data.description,
                data.is_primary
            )

            logger.info(f"Created portfolio item for student {data.student_id}: {data.title}")
            return self._row_to_response(row)

    async def update_portfolio(
        self,
        portfolio_id: str,
        data: PortfolioUpdate
    ) -> Optional[PortfolioResponse]:
        """Update a portfolio item"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Get existing item
            existing = await conn.fetchrow(
                "SELECT student_id, is_primary FROM tb_portfolio WHERE portfolio_id = $1",
                uuid.UUID(portfolio_id)
            )

            if not existing:
                return None

            # If setting as primary, unset other primary items
            if data.is_primary and not existing['is_primary']:
                await conn.execute(
                    """
                    UPDATE tb_portfolio SET is_primary = FALSE, upd_dt = CURRENT_TIMESTAMP
                    WHERE student_id = $1 AND is_primary = TRUE
                    """,
                    existing['student_id']
                )

            # Build update query dynamically
            updates = []
            values = []
            param_count = 0

            if data.artifact_type is not None:
                param_count += 1
                updates.append(f"artifact_type = ${param_count}")
                values.append(data.artifact_type.value)

            if data.title is not None:
                param_count += 1
                updates.append(f"title = ${param_count}")
                values.append(data.title)

            if data.url is not None:
                param_count += 1
                updates.append(f"url = ${param_count}")
                values.append(data.url)

            if data.description is not None:
                param_count += 1
                updates.append(f"description = ${param_count}")
                values.append(data.description)

            if data.is_primary is not None:
                param_count += 1
                updates.append(f"is_primary = ${param_count}")
                values.append(data.is_primary)

            if not updates:
                return await self.get_portfolio_by_id(portfolio_id)

            updates.append("upd_dt = CURRENT_TIMESTAMP")
            param_count += 1
            values.append(uuid.UUID(portfolio_id))

            query = f"""
                UPDATE tb_portfolio
                SET {', '.join(updates)}
                WHERE portfolio_id = ${param_count}
                RETURNING portfolio_id, student_id, artifact_type, title, url,
                          description, is_primary, ins_dt as created_at, upd_dt as updated_at
            """

            row = await conn.fetchrow(query, *values)

            logger.info(f"Updated portfolio item {portfolio_id}")
            return self._row_to_response(row) if row else None

    async def delete_portfolio(self, portfolio_id: str) -> bool:
        """Delete a portfolio item"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            result = await conn.execute(
                "DELETE FROM tb_portfolio WHERE portfolio_id = $1",
                uuid.UUID(portfolio_id)
            )

            deleted = result == "DELETE 1"
            if deleted:
                logger.info(f"Deleted portfolio item {portfolio_id}")
            return deleted

    async def set_primary(self, portfolio_id: str) -> Optional[PortfolioResponse]:
        """Set a portfolio item as primary"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Get the item's student_id
            row = await conn.fetchrow(
                "SELECT student_id FROM tb_portfolio WHERE portfolio_id = $1",
                uuid.UUID(portfolio_id)
            )

            if not row:
                return None

            student_id = row['student_id']

            # Unset all primary items for this student
            await conn.execute(
                """
                UPDATE tb_portfolio
                SET is_primary = FALSE, upd_dt = CURRENT_TIMESTAMP
                WHERE student_id = $1 AND is_primary = TRUE
                """,
                student_id
            )

            # Set this item as primary
            result = await conn.fetchrow(
                """
                UPDATE tb_portfolio
                SET is_primary = TRUE, upd_dt = CURRENT_TIMESTAMP
                WHERE portfolio_id = $1
                RETURNING portfolio_id, student_id, artifact_type, title, url,
                          description, is_primary, ins_dt as created_at, upd_dt as updated_at
                """,
                uuid.UUID(portfolio_id)
            )

            logger.info(f"Set portfolio item {portfolio_id} as primary")
            return self._row_to_response(result) if result else None

    async def get_portfolio_summary(self, student_id: str) -> PortfolioSummaryResponse:
        """Get portfolio summary statistics for a student"""
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")

            # Get all items
            rows = await conn.fetch(
                """
                SELECT artifact_type, is_primary, url, ins_dt, upd_dt
                FROM tb_portfolio
                WHERE student_id = $1
                ORDER BY COALESCE(upd_dt, ins_dt) DESC
                """,
                student_id
            )

            # Calculate statistics
            total_items = len(rows)
            by_type = {}
            has_primary = False
            primary_url = None
            last_updated = None

            for row in rows:
                artifact_type = row['artifact_type']
                by_type[artifact_type] = by_type.get(artifact_type, 0) + 1

                if row['is_primary']:
                    has_primary = True
                    primary_url = row['url']

                updated = row['upd_dt'] or row['ins_dt']
                if last_updated is None or updated > last_updated:
                    last_updated = updated

            # Get top skills from tb_student_skill
            skill_rows = await conn.fetch(
                """
                SELECT s.skill_nm
                FROM tb_student_skill ss
                JOIN tb_skill s ON ss.skill_cd = s.skill_cd
                WHERE ss.student_id = $1
                ORDER BY ss.current_level DESC
                LIMIT 5
                """,
                student_id
            )
            top_skills = [row['skill_nm'] for row in skill_rows] if skill_rows else []

            return PortfolioSummaryResponse(
                student_id=student_id,
                total_items=total_items,
                by_type=by_type,
                has_primary=has_primary,
                primary_url=primary_url,
                top_skills=top_skills,
                last_updated=last_updated
            )

    def get_portfolio_types(self) -> PortfolioTypesResponse:
        """Get list of available portfolio types"""
        types = [
            PortfolioTypeInfo(
                type=artifact_type,
                display_name=info["display_name"],
                description=info["description"],
                icon=info["icon"]
            )
            for artifact_type, info in self.TYPE_INFO.items()
        ]
        return PortfolioTypesResponse(types=types)

    async def verify_student_exists(self, student_id: str) -> bool:
        """Verify that a student exists"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.STUDENT_SERVICE_URL}/students/{student_id}"
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to verify student: {e}")
            # Fall back to database check
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute(f"SET search_path TO {settings.DB_SCHEMA}")
                row = await conn.fetchrow(
                    "SELECT 1 FROM tb_student WHERE student_id = $1",
                    student_id
                )
                return row is not None

    def _row_to_response(self, row) -> PortfolioResponse:
        """Convert database row to response schema"""
        return PortfolioResponse(
            portfolio_id=str(row['portfolio_id']),
            student_id=row['student_id'],
            artifact_type=ArtifactType(row['artifact_type']),
            title=row['title'],
            url=row['url'],
            description=row['description'],
            is_primary=row['is_primary'] or False,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            tags=None,  # Not stored in current schema
            skills=None  # Not stored in current schema
        )
