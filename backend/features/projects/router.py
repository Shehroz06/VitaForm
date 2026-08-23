import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.exceptions.base import ValidationException
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.profiles.dependencies import CurrentProfile
from features.projects.dependencies import get_project_repository, get_project_service
from features.projects.models import Project
from features.projects.repository import ProjectRepository
from features.projects.schemas import ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest
from features.skills.models import Skill

router = APIRouter(prefix="/projects", tags=["projects"])

ProjectServiceDep = Annotated[BaseOwnedCrudService[Project], Depends(get_project_service)]
ProjectRepositoryDep = Annotated[ProjectRepository, Depends(get_project_repository)]


async def _resolve_skills(
    repository: ProjectRepository, skill_ids: list[uuid.UUID], profile_id: uuid.UUID
) -> list[Skill]:
    skills = await repository.get_skills_by_ids(skill_ids, profile_id)
    if len(skills) != len(set(skill_ids)):
        raise ValidationException("One or more skill_ids do not belong to your profile.")
    return skills


@router.get("", response_model=SuccessResponse[list[ProjectResponse]])
async def list_projects(
    profile: CurrentProfile,
    service: ProjectServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ProjectResponse]]:
    sort_column, sort_desc = resolve_sort(
        pagination.sort,
        {
            "created_at": Project.created_at,
            "updated_at": Project.updated_at,
        },
        default=Project.created_at,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=sort_column,
        sort_desc=sort_desc,
    )
    return SuccessResponse(
        message="Projects retrieved successfully.",
        data=[ProjectResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[ProjectResponse], status_code=status.HTTP_201_CREATED
)
async def create_project(
    data: ProjectCreateRequest,
    profile: CurrentProfile,
    service: ProjectServiceDep,
    repository: ProjectRepositoryDep,
) -> SuccessResponse[ProjectResponse]:
    skills = await _resolve_skills(repository, data.skill_ids, profile.id)
    values = data.model_dump(exclude={"skill_ids"})
    entity = await service.create_owned(profile.id, skills=skills, **values)
    return SuccessResponse(
        message="Project created successfully.", data=ProjectResponse.model_validate(entity)
    )


@router.get("/{project_id}", response_model=SuccessResponse[ProjectResponse])
async def get_project(
    project_id: uuid.UUID,
    profile: CurrentProfile,
    service: ProjectServiceDep,
) -> SuccessResponse[ProjectResponse]:
    entity = await service.get_owned(project_id, profile.id)
    return SuccessResponse(
        message="Project retrieved successfully.", data=ProjectResponse.model_validate(entity)
    )


@router.patch("/{project_id}", response_model=SuccessResponse[ProjectResponse])
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdateRequest,
    profile: CurrentProfile,
    service: ProjectServiceDep,
    repository: ProjectRepositoryDep,
) -> SuccessResponse[ProjectResponse]:
    values = data.model_dump(exclude_unset=True, exclude={"skill_ids"})
    if data.skill_ids is not None:
        values["skills"] = await _resolve_skills(repository, data.skill_ids, profile.id)

    entity = await service.update_owned(project_id, profile.id, **values)
    return SuccessResponse(
        message="Project updated successfully.", data=ProjectResponse.model_validate(entity)
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    profile: CurrentProfile,
    service: ProjectServiceDep,
) -> None:
    await service.delete_owned(project_id, profile.id)
