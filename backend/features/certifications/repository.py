from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.certifications.models import Certification


class CertificationRepository(BaseRepository[Certification]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Certification)
