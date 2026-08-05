import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import FilePurpose
from app.database.base import Base, CrudModelMixin, pg_enum


class File(CrudModelMixin, Base):
    __tablename__ = "files"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    purpose: Mapped[FilePurpose] = mapped_column(pg_enum(FilePurpose, name="file_purpose"))
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(500))
