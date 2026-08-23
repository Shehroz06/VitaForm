from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from features.audit_log.repository import AuditLogRepository


def get_audit_log_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditLogRepository:
    return AuditLogRepository(db)
