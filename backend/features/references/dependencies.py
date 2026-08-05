from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.references.models import Reference
from features.references.repository import ReferenceRepository


def get_reference_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> ReferenceRepository:
    return ReferenceRepository(db)


def get_reference_service(
    repository: Annotated[ReferenceRepository, Depends(get_reference_repository)],
) -> BaseOwnedCrudService[Reference]:
    return BaseOwnedCrudService(repository, Reference.profile_id, "Reference not found.")
