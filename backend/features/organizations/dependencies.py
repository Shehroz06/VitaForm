from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.organizations.models import Organization
from features.organizations.repository import OrganizationRepository


def get_organization_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrganizationRepository:
    return OrganizationRepository(db)


def get_organization_service(
    repository: Annotated[OrganizationRepository, Depends(get_organization_repository)],
) -> BaseOwnedCrudService[Organization]:
    return BaseOwnedCrudService(repository, Organization.profile_id, "Organization not found.")
