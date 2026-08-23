import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.core.base_crud import BaseRepository
from app.core.sorting import SortSpec
from features.projects.models import Project
from features.skills.models import Skill


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Project)

    async def get_by_id(self, entity_id: uuid.UUID) -> Project | None:
        stmt = (
            select(Project)
            .where(Project.id == entity_id, Project.deleted_at.is_(None))
            .options(selectinload(Project.skills))
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_column: InstrumentedAttribute[uuid.UUID],
        owner_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        sort_columns: SortSpec | None = None,
    ) -> tuple[list[Project], int]:
        base_stmt = select(Project).where(
            owner_column == owner_id, Project.deleted_at.is_(None)
        )

        total = (
            await self._db.execute(select(func.count()).select_from(base_stmt.subquery()))
        ).scalar_one()

        if sort_columns:
            base_stmt = base_stmt.order_by(
                *(column.desc() if desc else column.asc() for column, desc in sort_columns)
            )

        items_stmt = (
            base_stmt.options(selectinload(Project.skills)).offset((page - 1) * limit).limit(limit)
        )
        items = list((await self._db.execute(items_stmt)).scalars().all())
        return items, total

    async def get_skills_by_ids(
        self, skill_ids: list[uuid.UUID], profile_id: uuid.UUID
    ) -> list[Skill]:
        if not skill_ids:
            return []
        stmt = select(Skill).where(
            Skill.id.in_(skill_ids),
            Skill.profile_id == profile_id,
            Skill.deleted_at.is_(None),
        )
        return list((await self._db.execute(stmt)).scalars().all())
