import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.core.base_crud import BaseRepository
from app.core.sorting import SortSpec
from features.jobs.models import AtsScore, Company, JobDescription


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Company)

    async def get_or_create_by_name(self, profile_id: uuid.UUID, name: str) -> Company:
        stmt = select(Company).where(
            Company.profile_id == profile_id, Company.name == name, Company.deleted_at.is_(None)
        )
        existing = (await self._db.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        return await self.create(profile_id=profile_id, name=name)


class JobDescriptionRepository(BaseRepository[JobDescription]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, JobDescription)

    async def get_by_id(self, entity_id: uuid.UUID) -> JobDescription | None:
        stmt = (
            select(JobDescription)
            .where(JobDescription.id == entity_id, JobDescription.deleted_at.is_(None))
            .options(selectinload(JobDescription.company))
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def get_by_hash(
        self, profile_id: uuid.UUID, raw_text_hash: str
    ) -> JobDescription | None:
        stmt = (
            select(JobDescription)
            .where(
                JobDescription.profile_id == profile_id,
                JobDescription.raw_text_hash == raw_text_hash,
                JobDescription.deleted_at.is_(None),
            )
            .options(selectinload(JobDescription.company))
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_column: InstrumentedAttribute[uuid.UUID],
        owner_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        sort_columns: SortSpec | None = None,
    ) -> tuple[list[JobDescription], int]:
        base_stmt = select(JobDescription).where(
            owner_column == owner_id, JobDescription.deleted_at.is_(None)
        )

        total = (
            await self._db.execute(select(func.count()).select_from(base_stmt.subquery()))
        ).scalar_one()

        if sort_columns:
            base_stmt = base_stmt.order_by(
                *(column.desc() if desc else column.asc() for column, desc in sort_columns)
            )

        items_stmt = (
            base_stmt.options(selectinload(JobDescription.company))
            .offset((page - 1) * limit)
            .limit(limit)
        )
        items = list((await self._db.execute(items_stmt)).scalars().all())
        return items, total


class AtsScoreRepository(BaseRepository[AtsScore]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AtsScore)

    async def get_latest_for_job(
        self, job_description_id: uuid.UUID, profile_id: uuid.UUID
    ) -> AtsScore | None:
        stmt = (
            select(AtsScore)
            .where(
                AtsScore.job_description_id == job_description_id,
                AtsScore.profile_id == profile_id,
                AtsScore.deleted_at.is_(None),
            )
            .order_by(AtsScore.created_at.desc())
            .limit(1)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()
