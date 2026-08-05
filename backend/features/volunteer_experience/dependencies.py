from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.volunteer_experience.models import VolunteerExperience
from features.volunteer_experience.repository import VolunteerExperienceRepository


def get_volunteer_experience_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VolunteerExperienceRepository:
    return VolunteerExperienceRepository(db)


def get_volunteer_experience_service(
    repository: Annotated[
        VolunteerExperienceRepository, Depends(get_volunteer_experience_repository)
    ],
) -> BaseOwnedCrudService[VolunteerExperience]:
    return BaseOwnedCrudService(
        repository, VolunteerExperience.profile_id, "Volunteer experience not found."
    )
