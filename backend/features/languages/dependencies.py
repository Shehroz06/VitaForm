from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.languages.models import Language
from features.languages.repository import LanguageRepository


def get_language_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> LanguageRepository:
    return LanguageRepository(db)


def get_language_service(
    repository: Annotated[LanguageRepository, Depends(get_language_repository)],
) -> BaseOwnedCrudService[Language]:
    return BaseOwnedCrudService(repository, Language.profile_id, "Language not found.")
