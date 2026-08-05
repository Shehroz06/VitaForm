from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.certifications.models import Certification
from features.certifications.repository import CertificationRepository


def get_certification_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CertificationRepository:
    return CertificationRepository(db)


def get_certification_service(
    repository: Annotated[CertificationRepository, Depends(get_certification_repository)],
) -> BaseOwnedCrudService[Certification]:
    return BaseOwnedCrudService(repository, Certification.profile_id, "Certification not found.")
