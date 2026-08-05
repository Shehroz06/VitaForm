import uuid
from datetime import date

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import PatentStatus
from app.database.base import Base, CrudModelMixin, pg_enum


class Patent(CrudModelMixin, Base):
    __tablename__ = "patents"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    patent_number: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[PatentStatus] = mapped_column(
        pg_enum(PatentStatus, "patent_status"), default=PatentStatus.FILED
    )
    filing_date: Mapped[date | None] = mapped_column(default=None)
    url: Mapped[str | None] = mapped_column(String(500), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
