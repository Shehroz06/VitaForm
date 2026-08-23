from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseOwnedCrudService
from app.database.session import get_db
from features.portfolio.models import PortfolioItem
from features.portfolio.repository import PortfolioItemRepository


def get_portfolio_item_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PortfolioItemRepository:
    return PortfolioItemRepository(db)


def get_portfolio_item_service(
    repository: Annotated[PortfolioItemRepository, Depends(get_portfolio_item_repository)],
) -> BaseOwnedCrudService[PortfolioItem]:
    return BaseOwnedCrudService(repository, PortfolioItem.profile_id, "Portfolio item not found.")
