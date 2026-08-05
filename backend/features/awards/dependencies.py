from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.awards.models import Award
from features.awards.repository import AwardRepository


def get_award_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> AwardRepository:
    return AwardRepository(db)


def get_award_service(
    repository: Annotated[AwardRepository, Depends(get_award_repository)],
) -> BaseOwnedCrudService[Award]:
    return BaseOwnedCrudService(repository, Award.profile_id, "Award not found.")
