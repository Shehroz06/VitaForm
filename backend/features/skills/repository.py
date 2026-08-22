import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from app.core.enums import SkillCategory, SkillLevel
from features.skills.models import Skill


class SkillRepository(BaseRepository[Skill]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Skill)

    async def get_or_create(
        self,
        profile_id: uuid.UUID,
        *,
        name: str,
        category: SkillCategory,
        level: SkillLevel | None = None,
    ) -> Skill:
        stmt = select(Skill).where(
            Skill.profile_id == profile_id,
            func.lower(Skill.name) == name.lower(),
            Skill.deleted_at.is_(None),
        )
        existing = (await self._db.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        return await self.create(profile_id=profile_id, name=name, category=category, level=level)
