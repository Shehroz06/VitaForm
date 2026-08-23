from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.interests.models import Interest


class InterestRepository(BaseRepository[Interest]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Interest)
