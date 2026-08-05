import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.awards.dependencies import get_award_service
from features.awards.models import Award
from features.awards.schemas import AwardCreateRequest, AwardResponse, AwardUpdateRequest
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/awards", tags=["awards"])

AwardServiceDep = Annotated[BaseOwnedCrudService[Award], Depends(get_award_service)]


@router.get("", response_model=SuccessResponse[list[AwardResponse]])
async def list_awards(
    profile: CurrentProfile,
    service: AwardServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[AwardResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Award.date_received,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Awards retrieved successfully.",
        data=[AwardResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[AwardResponse], status_code=status.HTTP_201_CREATED
)
async def create_award(
    data: AwardCreateRequest,
    profile: CurrentProfile,
    service: AwardServiceDep,
) -> SuccessResponse[AwardResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Award created successfully.", data=AwardResponse.model_validate(entity)
    )


@router.get("/{award_id}", response_model=SuccessResponse[AwardResponse])
async def get_award(
    award_id: uuid.UUID,
    profile: CurrentProfile,
    service: AwardServiceDep,
) -> SuccessResponse[AwardResponse]:
    entity = await service.get_owned(award_id, profile.id)
    return SuccessResponse(
        message="Award retrieved successfully.", data=AwardResponse.model_validate(entity)
    )


@router.patch("/{award_id}", response_model=SuccessResponse[AwardResponse])
async def update_award(
    award_id: uuid.UUID,
    data: AwardUpdateRequest,
    profile: CurrentProfile,
    service: AwardServiceDep,
) -> SuccessResponse[AwardResponse]:
    entity = await service.update_owned(award_id, profile.id, **data.model_dump(exclude_unset=True))
    return SuccessResponse(
        message="Award updated successfully.", data=AwardResponse.model_validate(entity)
    )


@router.delete("/{award_id}", response_model=SuccessResponse[MessageResponse])
async def delete_award(
    award_id: uuid.UUID,
    profile: CurrentProfile,
    service: AwardServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(award_id, profile.id)
    return SuccessResponse(
        message="Award deleted successfully.", data=MessageResponse(message="Deleted.")
    )
