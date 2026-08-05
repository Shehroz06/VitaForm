from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.achievements.models import Achievement
from features.achievements.repository import AchievementRepository


def get_achievement_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AchievementRepository:
    return AchievementRepository(db)


def get_achievement_service(
    repository: Annotated[AchievementRepository, Depends(get_achievement_repository)],
) -> BaseOwnedCrudService[Achievement]:
    return BaseOwnedCrudService(repository, Achievement.profile_id, "Achievement not found.")
