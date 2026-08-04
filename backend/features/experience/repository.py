from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.experience.models import Experience


class ExperienceRepository(BaseRepository[Experience]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Experience)
