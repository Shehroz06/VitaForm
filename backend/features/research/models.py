import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Research(CrudModelMixin, Base):
    __tablename__ = "research"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    publication_venue: Mapped[str | None] = mapped_column(String(200), default=None)
    publication_date: Mapped[date | None] = mapped_column(default=None)
    url: Mapped[str | None] = mapped_column(String(500), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
