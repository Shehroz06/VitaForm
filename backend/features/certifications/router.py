import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.base_crud import BaseOwnedCrudService
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.certifications.dependencies import get_certification_service
from features.certifications.models import Certification
from features.certifications.schemas import (
    CertificationCreateRequest,
    CertificationResponse,
    CertificationUpdateRequest,
)
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/certifications", tags=["certifications"])

CertificationServiceDep = Annotated[
    BaseOwnedCrudService[Certification], Depends(get_certification_service)
]


@router.get("", response_model=SuccessResponse[list[CertificationResponse]])
async def list_certifications(
    profile: CurrentProfile,
    service: CertificationServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[CertificationResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Certification.issue_date,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Certifications retrieved successfully.",
        data=[CertificationResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[CertificationResponse], status_code=status.HTTP_201_CREATED
)
async def create_certification(
    data: CertificationCreateRequest,
    profile: CurrentProfile,
    service: CertificationServiceDep,
) -> SuccessResponse[CertificationResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Certification created successfully.",
        data=CertificationResponse.model_validate(entity),
    )


@router.get("/{certification_id}", response_model=SuccessResponse[CertificationResponse])
async def get_certification(
    certification_id: uuid.UUID,
    profile: CurrentProfile,
    service: CertificationServiceDep,
) -> SuccessResponse[CertificationResponse]:
    entity = await service.get_owned(certification_id, profile.id)
    return SuccessResponse(
        message="Certification retrieved successfully.",
        data=CertificationResponse.model_validate(entity),
    )


@router.patch("/{certification_id}", response_model=SuccessResponse[CertificationResponse])
async def update_certification(
    certification_id: uuid.UUID,
    data: CertificationUpdateRequest,
    profile: CurrentProfile,
    service: CertificationServiceDep,
) -> SuccessResponse[CertificationResponse]:
    entity = await service.update_owned(
        certification_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Certification updated successfully.",
        data=CertificationResponse.model_validate(entity),
    )


@router.delete("/{certification_id}", response_model=SuccessResponse[MessageResponse])
async def delete_certification(
    certification_id: uuid.UUID,
    profile: CurrentProfile,
    service: CertificationServiceDep,
) -> SuccessResponse[MessageResponse]:
    await service.delete_owned(certification_id, profile.id)
    return SuccessResponse(
        message="Certification deleted successfully.", data=MessageResponse(message="Deleted.")
    )
