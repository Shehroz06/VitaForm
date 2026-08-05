from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.patents.models import Patent
from features.patents.repository import PatentRepository


def get_patent_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> PatentRepository:
    return PatentRepository(db)


def get_patent_service(
    repository: Annotated[PatentRepository, Depends(get_patent_repository)],
) -> BaseOwnedCrudService[Patent]:
    return BaseOwnedCrudService(repository, Patent.profile_id, "Patent not found.")
