import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.interests.dependencies import get_interest_service
from features.interests.models import Interest
from features.interests.schemas import (
    InterestCreateRequest,
    InterestResponse,
    InterestUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/interests", tags=["interests"])

InterestServiceDep = Annotated[BaseOwnedCrudService[Interest], Depends(get_interest_service)]


@router.get("", response_model=SuccessResponse[list[InterestResponse]])
async def list_interests(
    profile: CurrentProfile,
    service: InterestServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[InterestResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "name": Interest.name,
            "created_at": Interest.created_at,
            "updated_at": Interest.updated_at,
        },
        default=Interest.name,
        default_desc=False,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="Interests retrieved successfully.",
        data=[InterestResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[InterestResponse], status_code=status.HTTP_201_CREATED
)
async def create_interest(
    data: InterestCreateRequest,
    profile: CurrentProfile,
    service: InterestServiceDep,
) -> SuccessResponse[InterestResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Interest created successfully.", data=InterestResponse.model_validate(entity)
    )


@router.get("/{interest_id}", response_model=SuccessResponse[InterestResponse])
async def get_interest(
    interest_id: uuid.UUID,
    profile: CurrentProfile,
    service: InterestServiceDep,
) -> SuccessResponse[InterestResponse]:
    entity = await service.get_owned(interest_id, profile.id)
    return SuccessResponse(
        message="Interest retrieved successfully.", data=InterestResponse.model_validate(entity)
    )


@router.patch("/{interest_id}", response_model=SuccessResponse[InterestResponse])
async def update_interest(
    interest_id: uuid.UUID,
    data: InterestUpdateRequest,
    profile: CurrentProfile,
    service: InterestServiceDep,
) -> SuccessResponse[InterestResponse]:
    entity = await service.update_owned(
        interest_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Interest updated successfully.", data=InterestResponse.model_validate(entity)
    )


@router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interest(
    interest_id: uuid.UUID,
    profile: CurrentProfile,
    service: InterestServiceDep,
) -> None:
    await service.delete_owned(interest_id, profile.id)
