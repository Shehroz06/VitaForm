import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.portfolio.dependencies import get_portfolio_item_service
from features.portfolio.models import PortfolioItem
from features.portfolio.schemas import (
    PortfolioItemCreateRequest,
    PortfolioItemResponse,
    PortfolioItemUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

PortfolioItemServiceDep = Annotated[
    BaseOwnedCrudService[PortfolioItem], Depends(get_portfolio_item_service)
]


@router.get("", response_model=SuccessResponse[list[PortfolioItemResponse]])
async def list_portfolio_items(
    profile: CurrentProfile,
    service: PortfolioItemServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[PortfolioItemResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "title": PortfolioItem.title,
            "created_at": PortfolioItem.created_at,
            "updated_at": PortfolioItem.updated_at,
        },
        default=PortfolioItem.created_at,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="Portfolio items retrieved successfully.",
        data=[PortfolioItemResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "",
    response_model=SuccessResponse[PortfolioItemResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_portfolio_item(
    data: PortfolioItemCreateRequest,
    profile: CurrentProfile,
    service: PortfolioItemServiceDep,
) -> SuccessResponse[PortfolioItemResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Portfolio item created successfully.",
        data=PortfolioItemResponse.model_validate(entity),
    )


@router.get("/{portfolio_item_id}", response_model=SuccessResponse[PortfolioItemResponse])
async def get_portfolio_item(
    portfolio_item_id: uuid.UUID,
    profile: CurrentProfile,
    service: PortfolioItemServiceDep,
) -> SuccessResponse[PortfolioItemResponse]:
    entity = await service.get_owned(portfolio_item_id, profile.id)
    return SuccessResponse(
        message="Portfolio item retrieved successfully.",
        data=PortfolioItemResponse.model_validate(entity),
    )


@router.patch("/{portfolio_item_id}", response_model=SuccessResponse[PortfolioItemResponse])
async def update_portfolio_item(
    portfolio_item_id: uuid.UUID,
    data: PortfolioItemUpdateRequest,
    profile: CurrentProfile,
    service: PortfolioItemServiceDep,
) -> SuccessResponse[PortfolioItemResponse]:
    entity = await service.update_owned(
        portfolio_item_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Portfolio item updated successfully.",
        data=PortfolioItemResponse.model_validate(entity),
    )


@router.delete("/{portfolio_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_item(
    portfolio_item_id: uuid.UUID,
    profile: CurrentProfile,
    service: PortfolioItemServiceDep,
) -> None:
    await service.delete_owned(portfolio_item_id, profile.id)
