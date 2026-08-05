import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import LanguageProficiency
from app.database.base import Base, CrudModelMixin, pg_enum


class Language(CrudModelMixin, Base):
    __tablename__ = "languages"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    proficiency: Mapped[LanguageProficiency] = mapped_column(
        pg_enum(LanguageProficiency, "language_proficiency")
    )
