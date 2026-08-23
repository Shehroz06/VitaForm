from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.interests.models import Interest
from features.interests.repository import InterestRepository


def get_interest_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> InterestRepository:
    return InterestRepository(db)


def get_interest_service(
    repository: Annotated[InterestRepository, Depends(get_interest_repository)],
) -> BaseOwnedCrudService[Interest]:
    return BaseOwnedCrudService(repository, Interest.profile_id, "Interest not found.")
