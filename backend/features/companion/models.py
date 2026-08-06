import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class CoverLetter(CrudModelMixin, Base):
    __tablename__ = "cover_letters"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("job_descriptions.id"), default=None
    )
    company_name: Mapped[str] = mapped_column(String(200))
    role_title: Mapped[str] = mapped_column(String(200))
    hiring_manager: Mapped[str | None] = mapped_column(String(150), default=None)
    body: Mapped[str] = mapped_column(Text)


class LinkedinGeneration(CrudModelMixin, Base):
    __tablename__ = "linkedin_generations"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    target_role: Mapped[str | None] = mapped_column(String(150), default=None)
    headline: Mapped[str] = mapped_column(String(250))
    about: Mapped[str] = mapped_column(Text)
