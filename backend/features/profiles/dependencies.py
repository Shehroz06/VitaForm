from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import CurrentUser
from features.profiles.models import Profile
from features.profiles.repository import ProfileRepository
from features.profiles.service import ProfileService


def get_profile_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> ProfileRepository:
    return ProfileRepository(db)


def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    repository: Annotated[ProfileRepository, Depends(get_profile_repository)],
) -> ProfileService:
    return ProfileService(db, repository)


async def get_current_profile(
    user: CurrentUser,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> Profile:
    """Resolves (creating if necessary) the authenticated user's profile.
    Shared by education/experience/projects/skills routers, which are all
    sub-resources scoped to a profile_id."""
    return await service.get_or_create(user.id)


CurrentProfile = Annotated[Profile, Depends(get_current_profile)]
