import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sorting import SortSpec
from features.audit_log.models import AuditLog


class AuditLogRepository:
    """Read-only: rows are written exclusively by app/core/audit.py's
    before_flush listener, never through application code, so there's no
    create/update/delete here to mirror BaseRepository's shape."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_profile(
        self,
        profile_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        sort_columns: SortSpec | None = None,
    ) -> tuple[list[AuditLog], int]:
        base_stmt = select(AuditLog).where(AuditLog.profile_id == profile_id)

        total = (
            await self._db.execute(select(func.count()).select_from(base_stmt.subquery()))
        ).scalar_one()

        if sort_columns:
            base_stmt = base_stmt.order_by(
                *(column.desc() if desc else column.asc() for column, desc in sort_columns)
            )

        items_stmt = base_stmt.offset((page - 1) * limit).limit(limit)
        items = list((await self._db.execute(items_stmt)).scalars().all())
        return items, total
