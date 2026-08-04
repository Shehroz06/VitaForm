from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.education.models import Education
from features.education.repository import EducationRepository


def get_education_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> EducationRepository:
    return EducationRepository(db)


def get_education_service(
    repository: Annotated[EducationRepository, Depends(get_education_repository)],
) -> BaseOwnedCrudService[Education]:
    return BaseOwnedCrudService(repository, Education.profile_id, "Education entry not found.")
