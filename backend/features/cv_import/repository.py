from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.cv_import.models import ImportSession


class ImportSessionRepository(BaseRepository[ImportSession]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ImportSession)
