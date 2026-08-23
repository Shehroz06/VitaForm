from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.portfolio.models import PortfolioItem


class PortfolioItemRepository(BaseRepository[PortfolioItem]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, PortfolioItem)
