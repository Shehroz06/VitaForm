import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.database.base import CrudModelMixin
from app.exceptions.base import ResourceNotFoundException


class BaseRepository[ModelT: CrudModelMixin]:
    """Generic CRUD against a single table, scoped to an owning foreign key
    (e.g. profile_id) and excluding soft-deleted rows. Feature repositories
    subclass this and bind `model`, adding only their own query methods."""

    def __init__(self, db: AsyncSession, model: type[ModelT]) -> None:
        self._db = db
        self._model = model

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = select(self._model).where(
            self._model.id == entity_id, self._model.deleted_at.is_(None)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def list_by_owner(
        self,
        owner_column: InstrumentedAttribute[uuid.UUID],
        owner_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        sort_column: InstrumentedAttribute[Any] | None = None,
        sort_desc: bool = False,
    ) -> tuple[list[ModelT], int]:
        base_stmt = select(self._model).where(
            owner_column == owner_id, self._model.deleted_at.is_(None)
        )

        total = (
            await self._db.execute(select(func.count()).select_from(base_stmt.subquery()))
        ).scalar_one()

        if sort_column is not None:
            base_stmt = base_stmt.order_by(sort_column.desc() if sort_desc else sort_column.asc())

        items_stmt = base_stmt.offset((page - 1) * limit).limit(limit)
        items = list((await self._db.execute(items_stmt)).scalars().all())
        return items, total

    async def create(self, **values: Any) -> ModelT:
        entity = self._model(**values)
        self._db.add(entity)
        await self._db.flush()
        return entity

    async def update(self, entity: ModelT, **values: Any) -> ModelT:
        for key, value in values.items():
            setattr(entity, key, value)
        await self._db.flush()
        return entity

    async def soft_delete(self, entity: ModelT) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._db.flush()


class BaseOwnedCrudService[ModelT: CrudModelMixin]:
    """Adds ownership authorization on top of BaseRepository: every read/write
    verifies the entity's owner column matches the requesting user's scope,
    raising 404 (never 403) for entities that exist but aren't owned by the
    caller, so existence of other users' data is never leaked."""

    def __init__(
        self,
        repository: BaseRepository[ModelT],
        owner_column: InstrumentedAttribute[uuid.UUID],
        not_found_message: str,
    ) -> None:
        self._repository = repository
        self._owner_column = owner_column
        self._not_found_message = not_found_message

    async def get_owned(self, entity_id: uuid.UUID, owner_id: uuid.UUID) -> ModelT:
        entity = await self._repository.get_by_id(entity_id)
        if entity is None or getattr(entity, self._owner_column.key) != owner_id:
            raise ResourceNotFoundException(self._not_found_message)
        return entity

    async def list_owned(
        self,
        owner_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 20,
        sort_column: InstrumentedAttribute[Any] | None = None,
        sort_desc: bool = False,
    ) -> tuple[list[ModelT], int]:
        return await self._repository.list_by_owner(
            self._owner_column,
            owner_id,
            page=page,
            limit=limit,
            sort_column=sort_column,
            sort_desc=sort_desc,
        )

    async def create_owned(self, owner_id: uuid.UUID, **values: Any) -> ModelT:
        return await self._repository.create(**{self._owner_column.key: owner_id}, **values)

    async def update_owned(
        self, entity_id: uuid.UUID, owner_id: uuid.UUID, **values: Any
    ) -> ModelT:
        entity = await self.get_owned(entity_id, owner_id)
        return await self._repository.update(entity, **values)

    async def delete_owned(self, entity_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        entity = await self.get_owned(entity_id, owner_id)
        await self._repository.soft_delete(entity)
