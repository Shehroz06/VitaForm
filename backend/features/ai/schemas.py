import uuid

from pydantic import BaseModel, Field

from app.core.enums import SectionType
from features.files.schemas import FileResponse


class AIResumeSection(BaseModel):
    section_type: SectionType
    item_ids: list[uuid.UUID] = Field(default_factory=list)


class AIResumeResponse(BaseModel):
    """The exact JSON shape the AI provider must return. The AI only ever
    selects ids from the candidates it was given and writes a summary --
    it never supplies the actual factual content, which always comes from
    the database via the existing Phase 5 renderer."""

    summary: str = Field(min_length=1, max_length=2000)
    keywords: list[str] = Field(default_factory=list)
    sections: list[AIResumeSection] = Field(default_factory=list)


class ResumeGenerateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    # Optional, same as title -- template/color are presentation choices,
    # not part of "describe the role." Omitted means "use the default
    # template with its own default look."
    template_id: uuid.UUID | None = Field(default=None)
    accent_color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    job_description: str = Field(min_length=50, max_length=10000)
    target_role: str | None = Field(default=None, max_length=150)
    target_company: str | None = Field(default=None, max_length=150)


class GenerateResumeResponse(BaseModel):
    """Carries the resume id alongside the exported file, so callers can
    navigate straight to the resume that was just generated instead of only
    getting a downloadable PDF with no link back to it."""

    resume_id: uuid.UUID
    file: FileResponse
