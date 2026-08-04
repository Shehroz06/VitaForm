from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.skills.models import Skill


class SkillRepository(BaseRepository[Skill]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Skill)
