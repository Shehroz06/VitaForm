from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.patents.models import Patent


class PatentRepository(BaseRepository[Patent]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Patent)
