from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.projects.models import Project
from features.projects.repository import ProjectRepository


def get_project_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> ProjectRepository:
    return ProjectRepository(db)


def get_project_service(
    repository: Annotated[ProjectRepository, Depends(get_project_repository)],
) -> BaseOwnedCrudService[Project]:
    return BaseOwnedCrudService(repository, Project.profile_id, "Project not found.")
