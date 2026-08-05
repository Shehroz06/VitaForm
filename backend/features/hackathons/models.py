import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Hackathon(CrudModelMixin, Base):
    __tablename__ = "hackathons"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    project_name: Mapped[str | None] = mapped_column(String(200), default=None)
    event_date: Mapped[date | None] = mapped_column(default=None)
    result: Mapped[str | None] = mapped_column(String(150), default=None)
    url: Mapped[str | None] = mapped_column(String(500), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
