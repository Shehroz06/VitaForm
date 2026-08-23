import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.languages.dependencies import get_language_service
from features.languages.models import Language
from features.languages.schemas import (
    LanguageCreateRequest,
    LanguageResponse,
    LanguageUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/languages", tags=["languages"])

LanguageServiceDep = Annotated[BaseOwnedCrudService[Language], Depends(get_language_service)]


@router.get("", response_model=SuccessResponse[list[LanguageResponse]])
async def list_languages(
    profile: CurrentProfile,
    service: LanguageServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[LanguageResponse]]:
    sort_column, sort_desc = resolve_sort(
        pagination.sort,
        {
            "name": Language.name,
            "created_at": Language.created_at,
            "updated_at": Language.updated_at,
        },
        default=Language.name,
        default_desc=False,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=sort_column,
        sort_desc=sort_desc,
    )
    return SuccessResponse(
        message="Languages retrieved successfully.",
        data=[LanguageResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[LanguageResponse], status_code=status.HTTP_201_CREATED
)
async def create_language(
    data: LanguageCreateRequest,
    profile: CurrentProfile,
    service: LanguageServiceDep,
) -> SuccessResponse[LanguageResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Language created successfully.", data=LanguageResponse.model_validate(entity)
    )


@router.get("/{language_id}", response_model=SuccessResponse[LanguageResponse])
async def get_language(
    language_id: uuid.UUID,
    profile: CurrentProfile,
    service: LanguageServiceDep,
) -> SuccessResponse[LanguageResponse]:
    entity = await service.get_owned(language_id, profile.id)
    return SuccessResponse(
        message="Language retrieved successfully.", data=LanguageResponse.model_validate(entity)
    )


@router.patch("/{language_id}", response_model=SuccessResponse[LanguageResponse])
async def update_language(
    language_id: uuid.UUID,
    data: LanguageUpdateRequest,
    profile: CurrentProfile,
    service: LanguageServiceDep,
) -> SuccessResponse[LanguageResponse]:
    entity = await service.update_owned(
        language_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Language updated successfully.", data=LanguageResponse.model_validate(entity)
    )


@router.delete("/{language_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(
    language_id: uuid.UUID,
    profile: CurrentProfile,
    service: LanguageServiceDep,
) -> None:
    await service.delete_owned(language_id, profile.id)
