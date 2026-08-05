from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.core.storage import LocalStorageProvider, S3StorageProvider, StorageProvider
from app.database.session import get_db
from features.files.repository import FileRepository
from features.files.service import AvatarService, FileUploadService
from features.profiles.repository import ProfileRepository


def get_storage_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageProvider:
    if settings.storage_provider == "s3":
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET must be set when STORAGE_PROVIDER=s3.")
        return S3StorageProvider(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
        )
    return LocalStorageProvider(Path(settings.storage_local_path))


def get_file_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> FileRepository:
    return FileRepository(db)


def get_file_upload_service(
    repository: Annotated[FileRepository, Depends(get_file_repository)],
    storage: Annotated[StorageProvider, Depends(get_storage_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> FileUploadService:
    return FileUploadService(repository, storage, settings)


def get_avatar_service(
    file_service: Annotated[FileUploadService, Depends(get_file_upload_service)],
    file_repository: Annotated[FileRepository, Depends(get_file_repository)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvatarService:
    return AvatarService(file_service, file_repository, ProfileRepository(db))
