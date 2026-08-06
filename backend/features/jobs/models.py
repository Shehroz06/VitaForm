import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EmploymentType
from app.database.base import Base, CrudModelMixin, pg_enum


class Company(CrudModelMixin, Base):
    __tablename__ = "companies"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    website_url: Mapped[str | None] = mapped_column(String(500), default=None)
    industry: Mapped[str | None] = mapped_column(String(150), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)


class JobDescription(CrudModelMixin, Base):
    __tablename__ = "job_descriptions"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"), default=None)
    title: Mapped[str] = mapped_column(String(200))
    raw_text: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(150), default=None)
    employment_type: Mapped[EmploymentType | None] = mapped_column(
        pg_enum(EmploymentType, name="employment_type"), default=None
    )
    keywords: Mapped[list[str]] = mapped_column(JSONB, default=list)
    required_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    preferred_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)

    company: Mapped[Company | None] = relationship()


class AtsScore(CrudModelMixin, Base):
    __tablename__ = "ats_scores"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_descriptions.id"), index=True
    )
    overall_score: Mapped[int] = mapped_column(Integer)
    matched_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, default=list)
