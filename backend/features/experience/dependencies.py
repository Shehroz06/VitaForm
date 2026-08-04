from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.experience.models import Experience
from features.experience.repository import ExperienceRepository


def get_experience_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExperienceRepository:
    return ExperienceRepository(db)


def get_experience_service(
    repository: Annotated[ExperienceRepository, Depends(get_experience_repository)],
) -> BaseOwnedCrudService[Experience]:
    return BaseOwnedCrudService(repository, Experience.profile_id, "Experience entry not found.")
