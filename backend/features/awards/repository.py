from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.awards.models import Award


class AwardRepository(BaseRepository[Award]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Award)
