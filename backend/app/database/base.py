import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def pg_enum[T: StrEnum](enum_cls: type[T], name: str) -> SAEnum:
    """Postgres ENUM column storing the enum's lowercase .value (e.g. "full_time")
    instead of SQLAlchemy's default of the member .name (e.g. "FULL_TIME")."""
    return SAEnum(enum_cls, name=name, values_callable=lambda cls: [e.value for e in cls])


class Base(DeclarativeBase):
    pass


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class CrudModelMixin(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Combined mixin for owned, soft-deletable entities (profile sub-resources).
    Gives app/core/base_crud.py a single stable type to bind its generics to."""
