import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Education(CrudModelMixin, Base):
    __tablename__ = "educations"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    institution_name: Mapped[str] = mapped_column(String(200))
    degree: Mapped[str] = mapped_column(String(150))
    field_of_study: Mapped[str | None] = mapped_column(String(150), default=None)
    grade: Mapped[str | None] = mapped_column(String(50), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date | None] = mapped_column(default=None)
    is_current: Mapped[bool] = mapped_column(default=False)
