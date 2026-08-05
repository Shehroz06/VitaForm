import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class VolunteerExperience(CrudModelMixin, Base):
    __tablename__ = "volunteer_experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    organization_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(150))
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date | None] = mapped_column(default=None)
    is_current: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
