import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.profiles.dependencies import CurrentProfile
from features.research.dependencies import get_research_service
from features.research.models import Research
from features.research.schemas import (
    ResearchCreateRequest,
    ResearchResponse,
    ResearchUpdateRequest,
)

router = APIRouter(prefix="/research", tags=["research"])

ResearchServiceDep = Annotated[BaseOwnedCrudService[Research], Depends(get_research_service)]


@router.get("", response_model=SuccessResponse[list[ResearchResponse]])
async def list_research(
    profile: CurrentProfile,
    service: ResearchServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ResearchResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "publication_date": Research.publication_date,
            "created_at": Research.created_at,
            "updated_at": Research.updated_at,
        },
        default=Research.publication_date,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="Research retrieved successfully.",
        data=[ResearchResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[ResearchResponse], status_code=status.HTTP_201_CREATED
)
async def create_research(
    data: ResearchCreateRequest,
    profile: CurrentProfile,
    service: ResearchServiceDep,
) -> SuccessResponse[ResearchResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Research created successfully.", data=ResearchResponse.model_validate(entity)
    )


@router.get("/{research_id}", response_model=SuccessResponse[ResearchResponse])
async def get_research(
    research_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResearchServiceDep,
) -> SuccessResponse[ResearchResponse]:
    entity = await service.get_owned(research_id, profile.id)
    return SuccessResponse(
        message="Research retrieved successfully.", data=ResearchResponse.model_validate(entity)
    )


@router.patch("/{research_id}", response_model=SuccessResponse[ResearchResponse])
async def update_research(
    research_id: uuid.UUID,
    data: ResearchUpdateRequest,
    profile: CurrentProfile,
    service: ResearchServiceDep,
) -> SuccessResponse[ResearchResponse]:
    entity = await service.update_owned(
        research_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Research updated successfully.", data=ResearchResponse.model_validate(entity)
    )


@router.delete("/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research(
    research_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResearchServiceDep,
) -> None:
    await service.delete_owned(research_id, profile.id)
