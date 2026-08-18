import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ImportSessionStatus
from app.database.base import Base, CrudModelMixin, pg_enum


class ImportSession(CrudModelMixin, Base):
    """A staged CV import: an uploaded PDF was extracted and classified into
    per-section proposals, but nothing is written to the real profile tables
    until the user reviews and confirms. proposed_data is read-only once
    written by the classifier; confirming re-validates and writes a
    (possibly user-edited) payload the caller sends separately, never the
    stored proposal blindly."""

    __tablename__ = "import_sessions"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    source_filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[ImportSessionStatus] = mapped_column(
        pg_enum(ImportSessionStatus, name="import_session_status"),
        default=ImportSessionStatus.PENDING,
    )
    proposed_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
