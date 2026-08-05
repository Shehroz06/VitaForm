import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, UploadFile, status
from fastapi import File as FileParam
from fastapi.responses import RedirectResponse

from app.core.storage import StorageProvider
from app.exceptions.base import ResourceNotFoundException
from app.schemas.response import MessageResponse, SuccessResponse
from features.files.dependencies import (
    get_avatar_service,
    get_file_repository,
    get_file_upload_service,
    get_storage_provider,
)
from features.files.repository import FileRepository
from features.files.schemas import FileResponse
from features.files.service import AvatarService, FileUploadService
from features.profiles.dependencies import CurrentProfile

router = APIRouter(prefix="/files", tags=["files"])

FileUploadServiceDep = Annotated[FileUploadService, Depends(get_file_upload_service)]
AvatarServiceDep = Annotated[AvatarService, Depends(get_avatar_service)]
FileRepositoryDep = Annotated[FileRepository, Depends(get_file_repository)]
StorageProviderDep = Annotated[StorageProvider, Depends(get_storage_provider)]


@router.post(
    "/avatar", response_model=SuccessResponse[FileResponse], status_code=status.HTTP_201_CREATED
)
async def upload_avatar(
    profile: CurrentProfile,
    avatar_service: AvatarServiceDep,
    file: Annotated[UploadFile, FileParam()],
) -> SuccessResponse[FileResponse]:
    uploaded = await avatar_service.upload_avatar(profile, file)
    return SuccessResponse(
        message="Avatar uploaded successfully.", data=FileResponse.model_validate(uploaded)
    )


@router.delete("/avatar", response_model=SuccessResponse[MessageResponse])
async def delete_avatar(
    profile: CurrentProfile,
    avatar_service: AvatarServiceDep,
) -> SuccessResponse[MessageResponse]:
    await avatar_service.remove_avatar(profile)
    return SuccessResponse(
        message="Avatar removed successfully.", data=MessageResponse(message="Deleted.")
    )


@router.get("/{file_id}")
async def get_file(
    file_id: uuid.UUID,
    repository: FileRepositoryDep,
    storage: StorageProviderDep,
) -> Response:
    """Publicly retrieves a file by its unguessable UUID (no auth required —
    same trust model as a share-link). Redirects to a signed URL for S3-backed
    storage; streams bytes directly for local disk storage."""
    entity = await repository.get_by_id(file_id)
    if entity is None:
        raise ResourceNotFoundException("File not found.")

    signed_url = storage.get_signed_url(entity.storage_path)
    if signed_url is not None:
        return RedirectResponse(signed_url)

    content = await storage.read(entity.storage_path)
    return Response(content=content, media_type=entity.content_type)


@router.delete("/{file_id}", response_model=SuccessResponse[MessageResponse])
async def delete_file(
    file_id: uuid.UUID,
    profile: CurrentProfile,
    file_service: FileUploadServiceDep,
) -> SuccessResponse[MessageResponse]:
    await file_service.delete(file_id, profile.id)
    return SuccessResponse(
        message="File deleted successfully.", data=MessageResponse(message="Deleted.")
    )
