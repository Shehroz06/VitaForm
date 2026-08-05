from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.competitions.models import Competition
from features.competitions.repository import CompetitionRepository


def get_competition_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CompetitionRepository:
    return CompetitionRepository(db)


def get_competition_service(
    repository: Annotated[CompetitionRepository, Depends(get_competition_repository)],
) -> BaseOwnedCrudService[Competition]:
    return BaseOwnedCrudService(repository, Competition.profile_id, "Competition not found.")
