from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.leadership_roles.models import LeadershipRole
from features.leadership_roles.repository import LeadershipRoleRepository


def get_leadership_role_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeadershipRoleRepository:
    return LeadershipRoleRepository(db)


def get_leadership_role_service(
    repository: Annotated[LeadershipRoleRepository, Depends(get_leadership_role_repository)],
) -> BaseOwnedCrudService[LeadershipRole]:
    return BaseOwnedCrudService(
        repository, LeadershipRole.profile_id, "Leadership role not found."
    )
