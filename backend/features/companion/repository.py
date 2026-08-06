from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.companion.models import CoverLetter, LinkedinGeneration


class CoverLetterRepository(BaseRepository[CoverLetter]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, CoverLetter)


class LinkedinGenerationRepository(BaseRepository[LinkedinGeneration]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, LinkedinGeneration)
