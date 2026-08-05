import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from app.core.enums import FilePurpose
from features.files.models import File


class FileRepository(BaseRepository[File]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, File)

    async def find_active_by_purpose(
        self, profile_id: uuid.UUID, purpose: FilePurpose
    ) -> list[File]:
        stmt = select(File).where(
            File.profile_id == profile_id,
            File.purpose == purpose,
            File.deleted_at.is_(None),
        )
        return list((await self._db.execute(stmt)).scalars().all())
