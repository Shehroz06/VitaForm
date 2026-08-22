import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.experience.dependencies import get_experience_service
from features.experience.models import Experience
from features.experience.schemas import (
    ExperienceCreateRequest,
    ExperienceResponse,
    ExperienceUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/experience", tags=["experience"])

ExperienceServiceDep = Annotated[
    BaseOwnedCrudService[Experience], Depends(get_experience_service)
]


@router.get("", response_model=SuccessResponse[list[ExperienceResponse]])
async def list_experience(
    profile: CurrentProfile,
    service: ExperienceServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ExperienceResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Experience.start_date,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Experience retrieved successfully.",
        data=[ExperienceResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[ExperienceResponse], status_code=status.HTTP_201_CREATED
)
async def create_experience(
    data: ExperienceCreateRequest,
    profile: CurrentProfile,
    service: ExperienceServiceDep,
) -> SuccessResponse[ExperienceResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Experience created successfully.",
        data=ExperienceResponse.model_validate(entity),
    )


@router.get("/{experience_id}", response_model=SuccessResponse[ExperienceResponse])
async def get_experience(
    experience_id: uuid.UUID,
    profile: CurrentProfile,
    service: ExperienceServiceDep,
) -> SuccessResponse[ExperienceResponse]:
    entity = await service.get_owned(experience_id, profile.id)
    return SuccessResponse(
        message="Experience retrieved successfully.",
        data=ExperienceResponse.model_validate(entity),
    )


@router.patch("/{experience_id}", response_model=SuccessResponse[ExperienceResponse])
async def update_experience(
    experience_id: uuid.UUID,
    data: ExperienceUpdateRequest,
    profile: CurrentProfile,
    service: ExperienceServiceDep,
) -> SuccessResponse[ExperienceResponse]:
    entity = await service.update_owned(
        experience_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Experience updated successfully.",
        data=ExperienceResponse.model_validate(entity),
    )


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    experience_id: uuid.UUID,
    profile: CurrentProfile,
    service: ExperienceServiceDep,
) -> None:
    await service.delete_owned(experience_id, profile.id)
