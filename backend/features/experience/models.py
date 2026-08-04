import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import EmploymentType
from app.database.base import Base, CrudModelMixin, pg_enum


class Experience(CrudModelMixin, Base):
    __tablename__ = "experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    job_title: Mapped[str] = mapped_column(String(150))
    employment_type: Mapped[EmploymentType] = mapped_column(
        pg_enum(EmploymentType, "employment_type")
    )
    location: Mapped[str | None] = mapped_column(String(150), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    start_date: Mapped[date] = mapped_column()
    end_date: Mapped[date | None] = mapped_column(default=None)
    is_current: Mapped[bool] = mapped_column(default=False)
