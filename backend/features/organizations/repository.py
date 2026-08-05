from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.organizations.models import Organization


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Organization)
