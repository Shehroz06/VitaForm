import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
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
        try:
            return await self._repository.create(user_id=user_id)
        except IntegrityError:
            # Lost a race against a concurrent request creating the same
            # user's profile (e.g. several dashboard requests resolving
            # `CurrentProfile` in parallel right after login) -- the flush
            # above leaves the session's transaction unusable until rolled
            # back, after which the row the other request committed is
            # visible to re-fetch.
            await self._db.rollback()
            profile = await self._repository.get_by_user_id(user_id)
            if profile is not None:
                return profile
            raise

    async def update(self, user_id: uuid.UUID, **values: Any) -> Profile:
        profile = await self.get_or_create(user_id)
        return await self._repository.update(profile, **values)

    async def compute_completion_percentage(
        self, profile: Profile, first_name: str | None, last_name: str | None
    ) -> int:
        has_basics = bool(first_name and last_name)
        counts = await self._count_all(profile.id)

        checks_passed = sum(
            [
                has_basics,
                counts[Education] > 0,
                counts[Experience] > 0,
                counts[Project] > 0,
                counts[Skill] > 0,
            ]
        )
        return round((checks_passed / _COMPLETION_CHECKS) * 100)

    async def _count_all(
        self, profile_id: uuid.UUID
    ) -> dict[type[Education | Experience | Project | Skill], int]:
        """One round trip for all four counts: each is a scalar subquery
        selected as its own labeled column of a single one-row query,
        rather than a separate SELECT per model. (A UNION ALL of single-row
        counts would also be one round trip, but its row order isn't
        actually guaranteed by the SQL standard -- this avoids relying on
        that.)"""
        models: list[type[Education | Experience | Project | Skill]] = [
            Education,
            Experience,
            Project,
            Skill,
        ]

        def _count_subquery(model: type[Education | Experience | Project | Skill]) -> Any:
            return (
                select(func.count())
                .select_from(model)
                .where(model.profile_id == profile_id, model.deleted_at.is_(None))
                .scalar_subquery()
            )

        stmt = select(*(_count_subquery(model).label(model.__name__) for model in models))
        row = (await self._db.execute(stmt)).one()
        return dict(zip(models, row, strict=True))
