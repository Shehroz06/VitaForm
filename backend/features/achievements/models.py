import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Achievement(CrudModelMixin, Base):
    __tablename__ = "achievements"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    issuer: Mapped[str | None] = mapped_column(String(200), default=None)
    date_achieved: Mapped[date | None] = mapped_column(default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
