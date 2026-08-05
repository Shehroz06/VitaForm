from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.leadership_roles.models import LeadershipRole


class LeadershipRoleRepository(BaseRepository[LeadershipRole]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, LeadershipRole)
