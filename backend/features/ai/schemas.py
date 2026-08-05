import uuid

from pydantic import BaseModel, Field

from app.core.enums import SectionType


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
    template_id: uuid.UUID
    job_description: str = Field(min_length=50, max_length=10000)
    target_role: str | None = Field(default=None, max_length=150)
    target_company: str | None = Field(default=None, max_length=150)
