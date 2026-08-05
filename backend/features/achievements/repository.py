from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.achievements.models import Achievement


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Achievement)
