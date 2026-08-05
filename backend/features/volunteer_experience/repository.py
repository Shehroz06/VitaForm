from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.volunteer_experience.models import VolunteerExperience


class VolunteerExperienceRepository(BaseRepository[VolunteerExperience]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, VolunteerExperience)
