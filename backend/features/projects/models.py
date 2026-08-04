import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ProjectStatus
from app.database.base import Base, CrudModelMixin, pg_enum

if TYPE_CHECKING:
    from features.skills.models import Skill

project_skills = Table(
    "project_skills",
    Base.metadata,
    Column("project_id", UUID(as_uuid=True), ForeignKey("projects.id"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True),
)


class Project(CrudModelMixin, Base):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    role: Mapped[str | None] = mapped_column(String(150), default=None)
    status: Mapped[ProjectStatus] = mapped_column(
        pg_enum(ProjectStatus, "project_status"),
        default=ProjectStatus.IN_PROGRESS,
    )
    start_date: Mapped[date | None] = mapped_column(default=None)
    end_date: Mapped[date | None] = mapped_column(default=None)
    repository_url: Mapped[str | None] = mapped_column(String(500), default=None)
    demo_url: Mapped[str | None] = mapped_column(String(500), default=None)
    is_pinned: Mapped[bool] = mapped_column(default=False)

    skills: Mapped[list["Skill"]] = relationship(secondary=project_skills)
