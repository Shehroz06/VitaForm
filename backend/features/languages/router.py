import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
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
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Language.name,
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


@router.delete("/{language_id}", response_model=SuccessResponse[MessageResponse])
async def delete_language(
    language_id: uuid.UUID,
    profile: CurrentProfile,
    service: LanguageServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(language_id, profile.id)
    return SuccessResponse(
        message="Language deleted successfully.", data=MessageResponse(message="Deleted.")
    )
