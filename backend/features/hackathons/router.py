import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.hackathons.dependencies import get_hackathon_service
from features.hackathons.models import Hackathon
from features.hackathons.schemas import (
    HackathonCreateRequest,
    HackathonResponse,
    HackathonUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/hackathons", tags=["hackathons"])

HackathonServiceDep = Annotated[BaseOwnedCrudService[Hackathon], Depends(get_hackathon_service)]


@router.get("", response_model=SuccessResponse[list[HackathonResponse]])
async def list_hackathons(
    profile: CurrentProfile,
    service: HackathonServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[HackathonResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Hackathon.event_date,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Hackathons retrieved successfully.",
        data=[HackathonResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[HackathonResponse], status_code=status.HTTP_201_CREATED
)
async def create_hackathon(
    data: HackathonCreateRequest,
    profile: CurrentProfile,
    service: HackathonServiceDep,
) -> SuccessResponse[HackathonResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Hackathon created successfully.", data=HackathonResponse.model_validate(entity)
    )


@router.get("/{hackathon_id}", response_model=SuccessResponse[HackathonResponse])
async def get_hackathon(
    hackathon_id: uuid.UUID,
    profile: CurrentProfile,
    service: HackathonServiceDep,
) -> SuccessResponse[HackathonResponse]:
    entity = await service.get_owned(hackathon_id, profile.id)
    return SuccessResponse(
        message="Hackathon retrieved successfully.", data=HackathonResponse.model_validate(entity)
    )


@router.patch("/{hackathon_id}", response_model=SuccessResponse[HackathonResponse])
async def update_hackathon(
    hackathon_id: uuid.UUID,
    data: HackathonUpdateRequest,
    profile: CurrentProfile,
    service: HackathonServiceDep,
) -> SuccessResponse[HackathonResponse]:
    entity = await service.update_owned(
        hackathon_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Hackathon updated successfully.", data=HackathonResponse.model_validate(entity)
    )


@router.delete("/{hackathon_id}", response_model=SuccessResponse[MessageResponse])
async def delete_hackathon(
    hackathon_id: uuid.UUID,
    profile: CurrentProfile,
    service: HackathonServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(hackathon_id, profile.id)
    return SuccessResponse(
        message="Hackathon deleted successfully.", data=MessageResponse(message="Deleted.")
    )
