from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.education.models import Education


class EducationRepository(BaseRepository[Education]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Education)
