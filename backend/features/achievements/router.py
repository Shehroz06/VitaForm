import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi import File as FileParam

from app.core.base_crud import BaseOwnedCrudService
from app.core.enums import FilePurpose
from app.schemas.pagination import PaginationParams, build_pagination_meta, get_pagination
from app.schemas.response import SuccessResponse
from features.achievements.dependencies import get_achievement_service
from features.achievements.models import Achievement
from features.achievements.schemas import (
    AchievementCreateRequest,
    AchievementResponse,
    AchievementUpdateRequest,
)
from features.files.dependencies import get_file_upload_service
from features.files.service import FileUploadService
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/achievements", tags=["achievements"])

AchievementServiceDep = Annotated[
    BaseOwnedCrudService[Achievement], Depends(get_achievement_service)
]
FileUploadServiceDep = Annotated[FileUploadService, Depends(get_file_upload_service)]


@router.get("", response_model=SuccessResponse[list[AchievementResponse]])
async def list_achievements(
    profile: CurrentProfile,
    service: AchievementServiceDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> SuccessResponse[list[AchievementResponse]]:
    items, total = await service.list_owned(
        profile.id,
        page=pagination.page,
        limit=pagination.limit,
        sort_column=Achievement.date_achieved,
        sort_desc=True,
    )
    return SuccessResponse(
        message="Achievements retrieved successfully.",
        data=[AchievementResponse.model_validate(item) for item in items],
        meta=build_pagination_meta(pagination.page, pagination.limit, total),
    )


@router.post(
    "", response_model=SuccessResponse[AchievementResponse], status_code=status.HTTP_201_CREATED
)
async def create_achievement(
    data: AchievementCreateRequest,
    profile: CurrentProfile,
    service: AchievementServiceDep,
) -> SuccessResponse[AchievementResponse]:
    entity = await service.create_owned(profile.id, **data.model_dump())
    return SuccessResponse(
        message="Achievement created successfully.",
        data=AchievementResponse.model_validate(entity),
    )


@router.get("/{achievement_id}", response_model=SuccessResponse[AchievementResponse])
async def get_achievement(
    achievement_id: uuid.UUID,
    profile: CurrentProfile,
    service: AchievementServiceDep,
) -> SuccessResponse[AchievementResponse]:
    entity = await service.get_owned(achievement_id, profile.id)
    return SuccessResponse(
        message="Achievement retrieved successfully.",
        data=AchievementResponse.model_validate(entity),
    )


@router.patch("/{achievement_id}", response_model=SuccessResponse[AchievementResponse])
async def update_achievement(
    achievement_id: uuid.UUID,
    data: AchievementUpdateRequest,
    profile: CurrentProfile,
    service: AchievementServiceDep,
) -> SuccessResponse[AchievementResponse]:
    entity = await service.update_owned(
        achievement_id, profile.id, **data.model_dump(exclude_unset=True)
    )
    return SuccessResponse(
        message="Achievement updated successfully.",
        data=AchievementResponse.model_validate(entity),
    )


@router.delete("/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement(
    achievement_id: uuid.UUID,
    profile: CurrentProfile,
    service: AchievementServiceDep,
) -> None:
    await service.delete_owned(achievement_id, profile.id)


@router.post("/{achievement_id}/attachment", response_model=SuccessResponse[AchievementResponse])
async def upload_achievement_attachment(
    achievement_id: uuid.UUID,
    profile: CurrentProfile,
    service: AchievementServiceDep,
    file_service: FileUploadServiceDep,
    file: Annotated[UploadFile, FileParam()],
) -> SuccessResponse[AchievementResponse]:
    achievement = await service.get_owned(achievement_id, profile.id)
    if achievement.file_id is not None:
        await file_service.delete(achievement.file_id, profile.id)

    uploaded = await file_service.upload(profile.id, FilePurpose.ACHIEVEMENT, file)
    entity = await service.update_owned(achievement_id, profile.id, file_id=uploaded.id)
    return SuccessResponse(
        message="Attachment uploaded successfully.",
        data=AchievementResponse.model_validate(entity),
    )


@router.delete("/{achievement_id}/attachment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement_attachment(
    achievement_id: uuid.UUID,
    profile: CurrentProfile,
    service: AchievementServiceDep,
    file_service: FileUploadServiceDep,
) -> None:
    achievement = await service.get_owned(achievement_id, profile.id)
    if achievement.file_id is not None:
        await file_service.delete(achievement.file_id, profile.id)
        await service.update_owned(achievement_id, profile.id, file_id=None)
