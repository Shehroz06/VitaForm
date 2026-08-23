from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.exceptions.base import ServiceUnavailableException
from app.schemas.response import SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[dict])
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]) -> SuccessResponse[dict]:
    """Touches the database, not just the process -- a container
    orchestrator using this to gate traffic needs to know the app can
    actually serve requests, not just that the event loop is running."""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServiceUnavailableException("Database is unreachable.") from exc
    return SuccessResponse(message="Service is healthy.", data={"status": "ok"})
