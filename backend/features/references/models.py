import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Reference(CrudModelMixin, Base):
    __tablename__ = "references"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    relationship: Mapped[str | None] = mapped_column(String(150), default=None)
    contact_email: Mapped[str | None] = mapped_column(String(255), default=None)
    contact_phone: Mapped[str | None] = mapped_column(String(30), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
