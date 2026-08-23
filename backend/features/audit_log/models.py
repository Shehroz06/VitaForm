import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin, pg_enum


class AuditAction(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Append-only record of who changed what and when, across every
    profile-owned resource. Written automatically by a SQLAlchemy
    before_flush listener (app/core/audit.py) that inspects every flush's
    pending changes -- no individual feature service has to remember to
    log anything itself, and none currently does.

    Deliberately not a CrudModelMixin: this is never updated or
    soft-deleted after being written. An audit trail that could be edited
    isn't one."""

    __tablename__ = "audit_logs"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    action: Mapped[AuditAction] = mapped_column(pg_enum(AuditAction, name="audit_action"))
    resource_type: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
