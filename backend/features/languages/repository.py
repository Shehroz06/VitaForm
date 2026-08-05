from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.languages.models import Language


class LanguageRepository(BaseRepository[Language]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Language)
