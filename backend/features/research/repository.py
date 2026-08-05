from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.research.models import Research


class ResearchRepository(BaseRepository[Research]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Research)
