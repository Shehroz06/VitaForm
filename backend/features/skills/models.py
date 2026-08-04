import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import SkillCategory, SkillLevel
from app.database.base import Base, CrudModelMixin, pg_enum


class Skill(CrudModelMixin, Base):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[SkillCategory] = mapped_column(pg_enum(SkillCategory, "skill_category"))
    level: Mapped[SkillLevel | None] = mapped_column(
        pg_enum(SkillLevel, "skill_level"), default=None
    )
