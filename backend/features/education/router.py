import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.education.dependencies import get_education_service
from features.education.models import Education
from features.education.schemas import (
    EducationCreateRequest,
    EducationResponse,
    EducationUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/education", tags=["education"])

EducationServiceDep = Annotated[BaseOwnedCrudService[Education], Depends(get_education_service)]


@router.get("", response_model=SuccessResponse[list[EducationResponse]])
async def list_education(
    profile: CurrentProfile,
    service: EducationServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[EducationResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "start_date": Education.start_date,
            "created_at": Education.created_at,
            "updated_at": Education.updated_at,
        },
        default=Education.start_date,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
    )
    return SuccessResponse(
        message="Education retrieved successfully.",
        data=[EducationResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[EducationResponse], status_code=status.HTTP_201_CREATED
)
async def create_education(
    data: EducationCreateRequest,
    profile: CurrentProfile,
    service: EducationServiceDep,
) -> SuccessResponse[EducationResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Education created successfully.", data=EducationResponse.model_validate(entity)
    )


@router.get("/{education_id}", response_model=SuccessResponse[EducationResponse])
async def get_education(
    education_id: uuid.UUID,
    profile: CurrentProfile,
    service: EducationServiceDep,
) -> SuccessResponse[EducationResponse]:
    entity = await service.get_owned(education_id, profile.id)
    return SuccessResponse(
        message="Education retrieved successfully.", data=EducationResponse.model_validate(entity)
    )


@router.patch("/{education_id}", response_model=SuccessResponse[EducationResponse])
async def update_education(
    education_id: uuid.UUID,
    data: EducationUpdateRequest,
    profile: CurrentProfile,
    service: EducationServiceDep,
) -> SuccessResponse[EducationResponse]:
    entity = await service.update_owned(
        education_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Education updated successfully.", data=EducationResponse.model_validate(entity)
    )


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    education_id: uuid.UUID,
    profile: CurrentProfile,
    service: EducationServiceDep,
) -> None:
    await service.delete_owned(education_id, profile.id)
