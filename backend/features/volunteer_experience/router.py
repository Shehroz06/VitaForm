import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.profiles.dependencies import CurrentProfile
from features.volunteer_experience.dependencies import get_volunteer_experience_service
from features.volunteer_experience.models import VolunteerExperience
from features.volunteer_experience.schemas import (
    VolunteerExperienceCreateRequest,
    VolunteerExperienceResponse,
    VolunteerExperienceUpdateRequest,
)

router = APIRouter(prefix="/volunteer-experience", tags=["volunteer-experience"])

VolunteerExperienceServiceDep = Annotated[
    BaseOwnedCrudService[VolunteerExperience], Depends(get_volunteer_experience_service)
]


@router.get("", response_model=SuccessResponse[list[VolunteerExperienceResponse]])
async def list_volunteer_experience(
    profile: CurrentProfile,
    service: VolunteerExperienceServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[VolunteerExperienceResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=VolunteerExperience.start_date,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Volunteer experience retrieved successfully.",
        data=[VolunteerExperienceResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "",
    response_model=SuccessResponse[VolunteerExperienceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_volunteer_experience(
    data: VolunteerExperienceCreateRequest,
    profile: CurrentProfile,
    service: VolunteerExperienceServiceDep,
) -> SuccessResponse[VolunteerExperienceResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Volunteer experience created successfully.",
        data=VolunteerExperienceResponse.model_validate(entity),
    )


@router.get("/{entry_id}", response_model=SuccessResponse[VolunteerExperienceResponse])
async def get_volunteer_experience(
    entry_id: uuid.UUID,
    profile: CurrentProfile,
    service: VolunteerExperienceServiceDep,
) -> SuccessResponse[VolunteerExperienceResponse]:
    entity = await service.get_owned(entry_id, profile.id)
    return SuccessResponse(
        message="Volunteer experience retrieved successfully.",
        data=VolunteerExperienceResponse.model_validate(entity),
    )


@router.patch("/{entry_id}", response_model=SuccessResponse[VolunteerExperienceResponse])
async def update_volunteer_experience(
    entry_id: uuid.UUID,
    data: VolunteerExperienceUpdateRequest,
    profile: CurrentProfile,
    service: VolunteerExperienceServiceDep,
) -> SuccessResponse[VolunteerExperienceResponse]:
    entity = await service.update_owned(
        entry_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Volunteer experience updated successfully.",
        data=VolunteerExperienceResponse.model_validate(entity),
    )


@router.delete("/{entry_id}", response_model=SuccessResponse[MessageResponse])
async def delete_volunteer_experience(
    entry_id: uuid.UUID,
    profile: CurrentProfile,
    service: VolunteerExperienceServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(entry_id, profile.id)
    return SuccessResponse(
        message="Volunteer experience deleted successfully.",
        data=MessageResponse(message="Deleted."),
    )
