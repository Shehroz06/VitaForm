from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.research.models import Research
from features.research.repository import ResearchRepository


def get_research_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> ResearchRepository:
    return ResearchRepository(db)


def get_research_service(
    repository: Annotated[ResearchRepository, Depends(get_research_repository)],
) -> BaseOwnedCrudService[Research]:
    return BaseOwnedCrudService(repository, Research.profile_id, "Research entry not found.")
