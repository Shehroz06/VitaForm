import uuid
from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Certification(CrudModelMixin, Base):
    __tablename__ = "certifications"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    issuing_organization: Mapped[str] = mapped_column(String(200))
    issue_date: Mapped[date | None] = mapped_column(default=None)
    expiration_date: Mapped[date | None] = mapped_column(default=None)
    credential_id: Mapped[str | None] = mapped_column(String(150), default=None)
    credential_url: Mapped[str | None] = mapped_column(String(500), default=None)
