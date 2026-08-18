import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi import File as FileParam

from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import MessageResponse, SuccessResponse
from features.cv_import.dependencies import get_import_service
from features.cv_import.schemas import (
    ImportConfirmRequest,
    ImportConfirmResultResponse,
    ImportSessionResponse,
)
from features.cv_import.service import ImportService
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/cv-import", tags=["cv-import"])

ImportServiceDep = Annotated[ImportService, Depends(get_import_service)]


@router.post(
    "/sessions",
    response_model=SuccessResponse[ImportSessionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_import_session(
    profile: CurrentProfile,
    service: ImportServiceDep,
    file: Annotated[UploadFile, FileParam()],
) -> SuccessResponse[ImportSessionResponse]:
    content = await file.read()
    session = await service.create_session(profile, file.filename, content)
    return SuccessResponse(
        message="CV parsed. Review the proposed data before confirming.",
        data=ImportSessionResponse.model_validate(session),
    )


@router.get("/sessions", response_model=SuccessResponse[list[ImportSessionResponse]])
async def list_import_sessions(
    profile: CurrentProfile,
    service: ImportServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[ImportSessionResponse]]:
    items, total = await service.list_sessions(
        profile.id, page=pagination.page, limit=pagination.limit
    )
    return SuccessResponse(
        message="Import sessions retrieved successfully.",
        data=[ImportSessionResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.get("/sessions/{session_id}", response_model=SuccessResponse[ImportSessionResponse])
async def get_import_session(
    session_id: uuid.UUID, profile: CurrentProfile, service: ImportServiceDep
) -> SuccessResponse[ImportSessionResponse]:
    session = await service.get_owned_session(session_id, profile.id)
    return SuccessResponse(
        message="Import session retrieved successfully.",
        data=ImportSessionResponse.model_validate(session),
    )


@router.post(
    "/sessions/{session_id}/confirm",
    response_model=SuccessResponse[ImportConfirmResultResponse],
)
async def confirm_import_session(
    session_id: uuid.UUID,
    data: ImportConfirmRequest,
    profile: CurrentProfile,
    service: ImportServiceDep,
) -> SuccessResponse[ImportConfirmResultResponse]:
    session = await service.get_owned_session(session_id, profile.id)
    created_counts, profile_bio_updated = await service.confirm(session, profile, data)
    return SuccessResponse(
        message="Import confirmed and written to your profile.",
        data=ImportConfirmResultResponse(
            created_counts=created_counts, profile_headline_updated=profile_bio_updated
        ),
    )


@router.post(
    "/sessions/{session_id}/reject", response_model=SuccessResponse[ImportSessionResponse]
)
async def reject_import_session(
    session_id: uuid.UUID, profile: CurrentProfile, service: ImportServiceDep
) -> SuccessResponse[ImportSessionResponse]:
    session = await service.get_owned_session(session_id, profile.id)
    await service.reject(session)
    return SuccessResponse(
        message="Import rejected.", data=ImportSessionResponse.model_validate(session)
    )


@router.delete("/sessions/{session_id}", response_model=SuccessResponse[MessageResponse])
async def delete_import_session(
    session_id: uuid.UUID, profile: CurrentProfile, service: ImportServiceDep
) -> SuccessResponse[MessageResponse]:
    session = await service.get_owned_session(session_id, profile.id)
    await service.delete(session)
    return SuccessResponse(
        message="Import session deleted successfully.", data=MessageResponse(message="Deleted.")
    )
