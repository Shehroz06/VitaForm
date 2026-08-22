import uuid
from typing import Any

from app.core.base_crud import BaseOwnedCrudService
from features.skills.models import Skill
from features.skills.repository import SkillRepository


class SkillService(BaseOwnedCrudService[Skill]):
    """Same interface as the generic owned-CRUD service, except creation is
    idempotent: resubmitting a skill the profile already has (case-
    insensitive name match) returns the existing row instead of inserting a
    duplicate -- same pattern as CompanyRepository.get_or_create_by_name."""

    def __init__(self, repository: SkillRepository) -> None:
        super().__init__(repository, Skill.profile_id, "Skill not found.")
        self._skills = repository

    async def create_owned(self, owner_id: uuid.UUID, **values: Any) -> Skill:
        return await self._skills.get_or_create(owner_id, **values)
