import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
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
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Research.publication_date,
        sort_desc=True,
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


@router.delete("/{research_id}", response_model=SuccessResponse[MessageResponse])
async def delete_research(
    research_id: uuid.UUID,
    profile: CurrentProfile,
    service: ResearchServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(research_id, profile.id)
    return SuccessResponse(
        message="Research deleted successfully.", data=MessageResponse(message="Deleted.")
    )
