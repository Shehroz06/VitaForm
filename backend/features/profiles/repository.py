import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.profiles.models import Profile


class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Profile)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Profile | None:
        stmt = select(Profile).where(Profile.user_id == user_id, Profile.deleted_at.is_(None))
        return (await self._db.execute(stmt)).scalar_one_or_none()
