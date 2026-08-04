import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class Profile(CrudModelMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    headline: Mapped[str | None] = mapped_column(String(150), default=None)
    bio: Mapped[str | None] = mapped_column(Text, default=None)
    phone: Mapped[str | None] = mapped_column(String(30), default=None)
    location: Mapped[str | None] = mapped_column(String(150), default=None)
    website_url: Mapped[str | None] = mapped_column(String(500), default=None)
    github_url: Mapped[str | None] = mapped_column(String(500), default=None)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), default=None)
    avatar_url: Mapped[str | None] = mapped_column(String(500), default=None)
