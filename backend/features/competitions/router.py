import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.competitions.dependencies import get_competition_service
from features.competitions.models import Competition
from features.competitions.schemas import (
    CompetitionCreateRequest,
    CompetitionResponse,
    CompetitionUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/competitions", tags=["competitions"])

CompetitionServiceDep = Annotated[
    BaseOwnedCrudService[Competition], Depends(get_competition_service)
]


@router.get("", response_model=SuccessResponse[list[CompetitionResponse]])
async def list_competitions(
    profile: CurrentProfile,
    service: CompetitionServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[CompetitionResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "event_date": Competition.event_date,
            "created_at": Competition.created_at,
            "updated_at": Competition.updated_at,
        },
        default=Competition.event_date,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="Competitions retrieved successfully.",
        data=[CompetitionResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[CompetitionResponse], status_code=status.HTTP_201_CREATED
)
async def create_competition(
    data: CompetitionCreateRequest,
    profile: CurrentProfile,
    service: CompetitionServiceDep,
) -> SuccessResponse[CompetitionResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Competition created successfully.",
        data=CompetitionResponse.model_validate(entity),
    )


@router.get("/{competition_id}", response_model=SuccessResponse[CompetitionResponse])
async def get_competition(
    competition_id: uuid.UUID,
    profile: CurrentProfile,
    service: CompetitionServiceDep,
) -> SuccessResponse[CompetitionResponse]:
    entity = await service.get_owned(competition_id, profile.id)
    return SuccessResponse(
        message="Competition retrieved successfully.",
        data=CompetitionResponse.model_validate(entity),
    )


@router.patch("/{competition_id}", response_model=SuccessResponse[CompetitionResponse])
async def update_competition(
    competition_id: uuid.UUID,
    data: CompetitionUpdateRequest,
    profile: CurrentProfile,
    service: CompetitionServiceDep,
) -> SuccessResponse[CompetitionResponse]:
    entity = await service.update_owned(
        competition_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Competition updated successfully.",
        data=CompetitionResponse.model_validate(entity),
    )


@router.delete("/{competition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competition(
    competition_id: uuid.UUID,
    profile: CurrentProfile,
    service: CompetitionServiceDep,
) -> None:
    await service.delete_owned(competition_id, profile.id)
