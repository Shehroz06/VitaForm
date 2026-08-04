import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from features.education.models import Education
from features.experience.models import Experience
from features.profiles.models import Profile
from features.profiles.repository import ProfileRepository
from features.projects.models import Project
from features.skills.models import Skill

# Each check is worth an equal share of 100%.
_COMPLETION_CHECKS = 5


class ProfileService:
    def __init__(self, db: AsyncSession, repository: ProfileRepository) -> None:
        self._db = db
        self._repository = repository

    async def get_or_create(self, user_id: uuid.UUID) -> Profile:
        profile = await self._repository.get_by_user_id(user_id)
        if profile is not None:
            return profile
        return await self._repository.create(user_id=user_id)

    async def update(self, user_id: uuid.UUID, **values: Any) -> Profile:
        profile = await self.get_or_create(user_id)
        return await self._repository.update(profile, **values)

    async def compute_completion_percentage(self, profile: Profile) -> int:
        has_basics = bool(profile.headline and profile.bio)
        education_count = await self._count(Education, profile.id)
        experience_count = await self._count(Experience, profile.id)
        project_count = await self._count(Project, profile.id)
        skill_count = await self._count(Skill, profile.id)

        checks_passed = sum(
            [
                has_basics,
                education_count > 0,
                experience_count > 0,
                project_count > 0,
                skill_count > 0,
            ]
        )
        return round((checks_passed / _COMPLETION_CHECKS) * 100)

    async def _count(
        self, model: type[Education | Experience | Project | Skill], profile_id: uuid.UUID
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(model)
            .where(model.profile_id == profile_id, model.deleted_at.is_(None))
        )
        return (await self._db.execute(stmt)).scalar_one()
