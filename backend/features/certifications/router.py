import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi import File as FileParam

from app.core.base_crud import BaseOwnedCrudService
from app.core.enums import FilePurpose
from app.core.sorting import resolve_sort
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.certifications.dependencies import get_certification_service
from features.certifications.models import Certification
from features.certifications.schemas import (
    CertificationCreateRequest,
    CertificationResponse,
    CertificationUpdateRequest,
)
from features.files.dependencies import get_file_upload_service
from features.files.service import FileUploadService
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/certifications", tags=["certifications"])

CertificationServiceDep = Annotated[
    BaseOwnedCrudService[Certification], Depends(get_certification_service)
]
FileUploadServiceDep = Annotated[FileUploadService, Depends(get_file_upload_service)]


@router.get("", response_model=SuccessResponse[list[CertificationResponse]])
async def list_certifications(
    profile: CurrentProfile,
    service: CertificationServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[CertificationResponse]]:
    sort_columns = resolve_sort(
        pagination.sort,
        {
            "issue_date": Certification.issue_date,
            "created_at": Certification.created_at,
            "updated_at": Certification.updated_at,
        },
        default=Certification.issue_date,
        default_desc=True,
    )
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_columns=sort_columns,
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


@router.delete("/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certification(
    certification_id: uuid.UUID,
    profile: CurrentProfile,
    service: CertificationServiceDep,
) -> None:
    await service.delete_owned(certification_id, profile.id)


@router.post(
    "/{certification_id}/attachment", response_model=SuccessResponse[CertificationResponse]
)
async def upload_certification_attachment(
    certification_id: uuid.UUID,
    profile: CurrentProfile,
    service: CertificationServiceDep,
    file_service: FileUploadServiceDep,
    file: Annotated[UploadFile, FileParam()],
) -> SuccessResponse[CertificationResponse]:
    certification = await service.get_owned(certification_id, profile.id)
    if certification.file_id is not None:
        await file_service.delete(certification.file_id, profile.id)

    uploaded = await file_service.upload(profile.id, FilePurpose.CERTIFICATE, file)
    entity = await service.update_owned(certification_id, profile.id, file_id=uploaded.id)
    return SuccessResponse(
        message="Attachment uploaded successfully.",
        data=CertificationResponse.model_validate(entity),
    )


@router.delete("/{certification_id}/attachment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certification_attachment(
    certification_id: uuid.UUID,
    profile: CurrentProfile,
    service: CertificationServiceDep,
    file_service: FileUploadServiceDep,
) -> None:
    certification = await service.get_owned(certification_id, profile.id)
    if certification.file_id is not None:
        await file_service.delete(certification.file_id, profile.id)
        await service.update_owned(certification_id, profile.id, file_id=None)
