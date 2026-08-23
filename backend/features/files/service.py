import uuid

from fastapi import UploadFile

from app.config.settings import Settings
from app.core.enums import FilePurpose
from app.core.storage import StorageProvider
from app.core.uploads import read_upload_capped
from app.exceptions.base import ResourceNotFoundException
from features.files.models import File
from features.files.repository import FileRepository
from features.files.validation import max_size_bytes_for, validate_upload
from features.profiles.models import Profile
from features.profiles.repository import ProfileRepository


class FileUploadService:
    """Validates, stores, and records an uploaded file for a profile.
    Shared by every upload call site (avatar, certification/achievement
    attachments) so validation and storage-cleanup logic lives in one place."""

    def __init__(
        self,
        repository: FileRepository,
        storage: StorageProvider,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._settings = settings

    async def upload(
        self, profile_id: uuid.UUID, purpose: FilePurpose, upload_file: UploadFile
    ) -> File:
        max_bytes = max_size_bytes_for(purpose, self._settings)
        content = await read_upload_capped(
            upload_file,
            max_bytes,
            f"File exceeds the maximum size of {max_bytes // (1024 * 1024)}MB.",
        )
        extension = validate_upload(
            purpose, upload_file.filename, upload_file.content_type, len(content), self._settings
        )
        content_type = upload_file.content_type or "application/octet-stream"
        filename = upload_file.filename or f"upload.{extension}"
        return await self._persist(profile_id, purpose, filename, content_type, content)

    async def store_generated(
        self,
        profile_id: uuid.UUID,
        purpose: FilePurpose,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> File:
        """Stores server-generated content (e.g. a rendered resume PDF) that
        was never user-uploaded, so it skips upload validation entirely."""
        return await self._persist(profile_id, purpose, filename, content_type, content)

    async def _persist(
        self,
        profile_id: uuid.UUID,
        purpose: FilePurpose,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> File:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        stored_filename = f"{uuid.uuid4()}.{extension}"
        storage_path = f"{profile_id}/{stored_filename}"
        await self._storage.save(storage_path, content, content_type)

        entity = await self._repository.create(
            profile_id=profile_id,
            purpose=purpose,
            original_filename=filename,
            stored_filename=stored_filename,
            content_type=content_type,
            size_bytes=len(content),
            storage_path=storage_path,
            url="",
        )
        return await self._repository.update(
            entity, url=f"{self._settings.api_base_url}/files/{entity.id}"
        )

    async def delete(self, file_id: uuid.UUID, profile_id: uuid.UUID) -> None:
        entity = await self._repository.get_by_id(file_id)
        if entity is None or entity.profile_id != profile_id:
            raise ResourceNotFoundException("File not found.")
        await self._storage.delete(entity.storage_path)
        await self._repository.soft_delete(entity)


class AvatarService:
    """A profile has at most one active avatar. Uploading replaces it
    (old file soft-deleted + removed from storage); profiles.avatar_url
    stays in sync as the denormalized field the rest of the app reads."""

    def __init__(
        self,
        file_service: FileUploadService,
        file_repository: FileRepository,
        profile_repository: ProfileRepository,
    ) -> None:
        self._file_service = file_service
        self._file_repository = file_repository
        self._profile_repository = profile_repository

    async def upload_avatar(self, profile: Profile, upload_file: UploadFile) -> File:
        previous = await self._file_repository.find_active_by_purpose(
            profile.id, FilePurpose.AVATAR
        )
        uploaded = await self._file_service.upload(profile.id, FilePurpose.AVATAR, upload_file)
        for old in previous:
            await self._file_service.delete(old.id, profile.id)
        await self._profile_repository.update(profile, avatar_url=uploaded.url)
        return uploaded

    async def remove_avatar(self, profile: Profile) -> None:
        previous = await self._file_repository.find_active_by_purpose(
            profile.id, FilePurpose.AVATAR
        )
        for old in previous:
            await self._file_service.delete(old.id, profile.id)
        await self._profile_repository.update(profile, avatar_url=None)
