import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.profiles.dependencies import CurrentProfile
from features.references.dependencies import get_reference_service
from features.references.models import Reference
from features.references.schemas import (
    ReferenceCreateRequest,
    ReferenceResponse,
    ReferenceUpdateRequest,
)

router = APIRouter(prefix="/references", tags=["references"])

ReferenceServiceDep = Annotated[BaseOwnedCrudService[Reference], Depends(get_reference_service)]


@router.get("", response_model=SuccessResponse[list[ReferenceResponse]])
async def list_references(
    profile: CurrentProfile,
    service: ReferenceServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ReferenceResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "name": Reference.name,
            "created_at": Reference.created_at,
            "updated_at": Reference.updated_at,
        },
        default=Reference.name,
        default_desc=False,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="References retrieved successfully.",
        data=[ReferenceResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[ReferenceResponse], status_code=status.HTTP_201_CREATED
)
async def create_reference(
    data: ReferenceCreateRequest,
    profile: CurrentProfile,
    service: ReferenceServiceDep,
) -> SuccessResponse[ReferenceResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Reference created successfully.", data=ReferenceResponse.model_validate(entity)
    )


@router.get("/{reference_id}", response_model=SuccessResponse[ReferenceResponse])
async def get_reference(
    reference_id: uuid.UUID,
    profile: CurrentProfile,
    service: ReferenceServiceDep,
) -> SuccessResponse[ReferenceResponse]:
    entity = await service.get_owned(reference_id, profile.id)
    return SuccessResponse(
        message="Reference retrieved successfully.", data=ReferenceResponse.model_validate(entity)
    )


@router.patch("/{reference_id}", response_model=SuccessResponse[ReferenceResponse])
async def update_reference(
    reference_id: uuid.UUID,
    data: ReferenceUpdateRequest,
    profile: CurrentProfile,
    service: ReferenceServiceDep,
) -> SuccessResponse[ReferenceResponse]:
    entity = await service.update_owned(
        reference_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Reference updated successfully.", data=ReferenceResponse.model_validate(entity)
    )


@router.delete("/{reference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reference(
    reference_id: uuid.UUID,
    profile: CurrentProfile,
    service: ReferenceServiceDep,
) -> None:
    await service.delete_owned(reference_id, profile.id)
