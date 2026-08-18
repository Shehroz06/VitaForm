import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseRepository
from features.resumes.models import Resume, ResumeTemplate, ResumeVersion


class ResumeTemplateRepository(BaseRepository[ResumeTemplate]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ResumeTemplate)

    async def list_active(self) -> list[ResumeTemplate]:
        stmt = select(ResumeTemplate).where(
            ResumeTemplate.is_active.is_(True), ResumeTemplate.deleted_at.is_(None)
        )
        return list((await self._db.execute(stmt)).scalars().all())

    async def get_by_slug(self, slug: str) -> ResumeTemplate | None:
        stmt = select(ResumeTemplate).where(
            ResumeTemplate.slug == slug, ResumeTemplate.deleted_at.is_(None)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()


class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Resume)


class ResumeVersionRepository(BaseRepository[ResumeVersion]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ResumeVersion)

    async def get_latest(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        stmt = (
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id, ResumeVersion.deleted_at.is_(None))
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def get_by_number(
        self, resume_id: uuid.UUID, version_id: uuid.UUID
    ) -> ResumeVersion | None:
        stmt = select(ResumeVersion).where(
            ResumeVersion.id == version_id,
            ResumeVersion.resume_id == resume_id,
            ResumeVersion.deleted_at.is_(None),
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def list_by_resume(
        self, resume_id: uuid.UUID, *, page: int = 1, limit: int = 20
    ) -> tuple[list[ResumeVersion], int]:
        base_stmt = select(ResumeVersion).where(
            ResumeVersion.resume_id == resume_id, ResumeVersion.deleted_at.is_(None)
        )
        total = (
            await self._db.execute(select(func.count()).select_from(base_stmt.subquery()))
        ).scalar_one()
        items_stmt = (
            base_stmt.order_by(ResumeVersion.version_number.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = list((await self._db.execute(items_stmt)).scalars().all())
        return items, total

    async def create_version(
        self, resume_id: uuid.UUID, version_number: int, content: dict[str, Any]
    ) -> ResumeVersion:
        return await self.create(
            resume_id=resume_id, version_number=version_number, content=content
        )
