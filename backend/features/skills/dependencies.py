from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.skills.models import Skill
from features.skills.repository import SkillRepository


def get_skill_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> SkillRepository:
    return SkillRepository(db)


def get_skill_service(
    repository: Annotated[SkillRepository, Depends(get_skill_repository)],
) -> BaseOwnedCrudService[Skill]:
    return BaseOwnedCrudService(repository, Skill.profile_id, "Skill not found.")
