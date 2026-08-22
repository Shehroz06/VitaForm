import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import SkillCategory, SkillLevel
from app.database.base import Base, CrudModelMixin, pg_enum


class Skill(CrudModelMixin, Base):
    __tablename__ = "skills"
    __table_args__ = (
        Index(
            "ix_skills_profile_lower_name",
            "profile_id",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[SkillCategory] = mapped_column(pg_enum(SkillCategory, "skill_category"))
    level: Mapped[SkillLevel | None] = mapped_column(
        pg_enum(SkillLevel, "skill_level"), default=None
    )
