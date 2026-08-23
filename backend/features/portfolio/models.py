import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, CrudModelMixin


class PortfolioItem(CrudModelMixin, Base):
    """A single showcased work (case study, design piece, publication --
    whatever the profile owner wants to point at) with a title and a link.
    Deliberately separate from Projects: Projects captures what was built
    and with what tech, for a resume/CV context; a portfolio item captures
    the presentable result, for a portfolio-site context."""

    __tablename__ = "portfolio_items"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    url: Mapped[str | None] = mapped_column(String(500), default=None)
