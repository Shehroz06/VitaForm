from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.hackathons.models import Hackathon


class HackathonRepository(BaseRepository[Hackathon]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Hackathon)
