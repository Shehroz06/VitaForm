import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import GenerationStatus
from app.database.base import Base, CrudModelMixin, pg_enum


class PromptHistory(CrudModelMixin, Base):
    """One row per (purpose, version) -- the static prompt template, not a
    per-request log. New rows are only inserted when the template text for
    a purpose actually changes (get-or-create by hash at generation time)."""

    __tablename__ = "prompt_history"
    __table_args__ = (UniqueConstraint("purpose", "version"),)

    purpose: Mapped[str] = mapped_column(String(50))
    version: Mapped[int] = mapped_column(Integer)
    prompt_hash: Mapped[str] = mapped_column(String(64), index=True)
    template: Mapped[str] = mapped_column(Text)


class GenerationHistory(CrudModelMixin, Base):
    """One row per AI-generation attempt (a call to POST /resumes/generate),
    regardless of whether it ultimately succeeded or exhausted retries."""

    __tablename__ = "generation_history"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id"), index=True)
    # Nullable: a generation attempt that exhausted every provider never
    # produces a resume at all, so there is nothing to point at.
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resumes.id"), default=None, index=True
    )
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resume_versions.id"), default=None
    )
    # Same nullable-target convention as resume_id/resume_version_id above,
    # extended for Phase 8's two additional document types. A polymorphic
    # single "target" column would be more elegant past 3-4 document types,
    # but isn't worth the complexity yet.
    cover_letter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cover_letters.id"), default=None
    )
    linkedin_generation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("linkedin_generations.id"), default=None
    )
    prompt_history_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prompt_history.id"))
    status: Mapped[GenerationStatus] = mapped_column(
        pg_enum(GenerationStatus, name="generation_status")
    )
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text, default=None)


class AIProviderLog(CrudModelMixin, Base):
    """One row per underlying provider API call -- a single generation event
    may have several (initial attempt, retries, fallback provider)."""

    __tablename__ = "ai_provider_logs"

    generation_history_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("generation_history.id"), default=None, index=True
    )
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    latency_ms: Mapped[int] = mapped_column(Integer)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    retry_attempt: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    # Deliberately unpopulated for now -- provider pricing changes too often
    # to hardcode responsibly. Column exists so cost tracking can be added
    # later without a schema change.
    estimated_cost_usd: Mapped[float | None] = mapped_column(default=None)
