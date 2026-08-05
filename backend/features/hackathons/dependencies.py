from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.hackathons.models import Hackathon
from features.hackathons.repository import HackathonRepository


def get_hackathon_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> HackathonRepository:
    return HackathonRepository(db)


def get_hackathon_service(
    repository: Annotated[HackathonRepository, Depends(get_hackathon_repository)],
) -> BaseOwnedCrudService[Hackathon]:
    return BaseOwnedCrudService(repository, Hackathon.profile_id, "Hackathon not found.")
