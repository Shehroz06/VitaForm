import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.patents.dependencies import get_patent_service
from features.patents.models import Patent
from features.patents.schemas import PatentCreateRequest, PatentResponse, PatentUpdateRequest
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/patents", tags=["patents"])

PatentServiceDep = Annotated[BaseOwnedCrudService[Patent], Depends(get_patent_service)]


@router.get("", response_model=SuccessResponse[list[PatentResponse]])
async def list_patents(
    profile: CurrentProfile,
    service: PatentServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[PatentResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "filing_date": Patent.filing_date,
            "created_at": Patent.created_at,
            "updated_at": Patent.updated_at,
        },
        default=Patent.filing_date,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="Patents retrieved successfully.",
        data=[PatentResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[PatentResponse], status_code=status.HTTP_201_CREATED
)
async def create_patent(
    data: PatentCreateRequest,
    profile: CurrentProfile,
    service: PatentServiceDep,
) -> SuccessResponse[PatentResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Patent created successfully.", data=PatentResponse.model_validate(entity)
    )


@router.get("/{patent_id}", response_model=SuccessResponse[PatentResponse])
async def get_patent(
    patent_id: uuid.UUID,
    profile: CurrentProfile,
    service: PatentServiceDep,
) -> SuccessResponse[PatentResponse]:
    entity = await service.get_owned(patent_id, profile.id)
    return SuccessResponse(
        message="Patent retrieved successfully.", data=PatentResponse.model_validate(entity)
    )


@router.patch("/{patent_id}", response_model=SuccessResponse[PatentResponse])
async def update_patent(
    patent_id: uuid.UUID,
    data: PatentUpdateRequest,
    profile: CurrentProfile,
    service: PatentServiceDep,
) -> SuccessResponse[PatentResponse]:
    entity = await service.update_owned(
        patent_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Patent updated successfully.", data=PatentResponse.model_validate(entity)
    )


@router.delete("/{patent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patent(
    patent_id: uuid.UUID,
    profile: CurrentProfile,
    service: PatentServiceDep,
) -> None:
    await service.delete_owned(patent_id, profile.id)
