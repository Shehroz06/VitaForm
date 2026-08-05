from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.competitions.models import Competition


class CompetitionRepository(BaseRepository[Competition]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Competition)
