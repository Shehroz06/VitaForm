import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class ResumeTemplate(CrudModelMixin, Base):
    __tablename__ = "resume_templates"

    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)


class Resume(CrudModelMixin, Base):
    __tablename__ = "resumes"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resume_templates.id"))
    title: Mapped[str] = mapped_column(String(200))


class ResumeVersion(CrudModelMixin, Base):
    __tablename__ = "resume_versions"
    __table_args__ = (UniqueConstraint("resume_id", "version_number"),)

    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    rendered_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("files.id"), default=None
    )
    rendered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
