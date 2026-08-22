from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from features.skills.repository import SkillRepository
from features.skills.service import SkillService


def get_skill_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> SkillRepository:
    return SkillRepository(db)


def get_skill_service(
    repository: Annotated[SkillRepository, Depends(get_skill_repository)],
) -> SkillService:
    return SkillService(repository)
