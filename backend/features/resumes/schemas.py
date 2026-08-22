import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.enums import SectionType


class ResumeTemplateResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class ContactVisibility(BaseModel):
    phone: bool = True
    location: bool = True
    website: bool = True
    github: bool = True
    linkedin: bool = True
    email: bool = True


class ResumeSection(BaseModel):
    section_type: SectionType
    custom_title: str | None = Field(default=None, max_length=100)
    visible: bool = True
    item_ids: list[uuid.UUID] = Field(default_factory=list)


class ResumeStyle(BaseModel):
    """Visual knobs every Jinja2 template must render from instead of
    hardcoding -- so a resume's PDF always reflects what the user actually
    picked in the builder. font_family names map to real, installed font
    stacks in the renderer (see renderer.py's FONT_STACKS)."""

    accent_color: str = Field(default="#1a1a1a", pattern=r"^#[0-9a-fA-F]{6}$")
    font_family: Literal["arial", "calibri", "times", "georgia"] = "arial"
    # "extreme" is a 4th, denser-than-"compact" tier -- like content_density,
    # it's computed-only (the autofit search tries it automatically when
    # "compact" still overflows) and deliberately not offered as a manual
    # choice in TemplateCustomizer, since it trades a noticeable amount of
    # aesthetic breathing room for page space.
    spacing: Literal["compact", "cozy", "relaxed", "extreme"] = "cozy"
    # Computed-only: set exclusively by the AI-generation one-page trim loop
    # (features/ai/page_fit.py) when spacing presets alone aren't enough to
    # fit a page -- never exposed as a manual choice in TemplateCustomizer.
    # Multiplies font-size and numeric spacing/margins continuously, the
    # LaTeX-style lever between "spacing preset" and "delete content."
    content_density: float = Field(default=1.0, ge=0.8, le=1.0)


class ResumeContent(BaseModel):
    summary: str | None = Field(default=None, max_length=2000)
    contact_visibility: ContactVisibility = Field(default_factory=ContactVisibility)
    sections: list[ResumeSection] = Field(default_factory=list)
    style: ResumeStyle = Field(default_factory=ResumeStyle)
    # Per-item description text, scoped to this resume only -- never
    # written back to the source table (Experience.description etc.), so
    # the profile's own canonical text is untouched no matter how a resume
    # tailors it. Every value here is produced by features.ai.
    # description_condenser, which only ever selects/reorders sentences
    # already present in the item's real description -- it cannot
    # introduce text that doesn't already exist somewhere in the source.
    # Keyed by item id (as a string -- JSON object keys can't be UUIDs).
    description_overrides: dict[str, str] = Field(default_factory=dict)
    # Same resume-scoped-only guarantee as description_overrides, for an
    # item's own title/role and its organization/institution line -- e.g.
    # rephrasing "Software Engineering Intern" without touching the real
    # Experience row. Only meaningful for section types with a sub-heading
    # (see section_registry.py's TITLE_FIELDS/SUBTITLE_FIELDS); silently
    # ignored at render time for section types without one.
    title_overrides: dict[str, str] = Field(default_factory=dict)
    subtitle_overrides: dict[str, str] = Field(default_factory=dict)


class PreviewWithRequest(BaseModel):
    """Renders arbitrary, not-yet-saved content against a candidate
    template -- nothing here is persisted. Powers the template picker's
    live comparison cards: real backend renders of "what would this resume
    look like in template X", rather than a second, approximate React
    re-implementation of each template."""

    content: ResumeContent
    template_id: uuid.UUID


class RewriteTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    job_description: str | None = Field(default=None, max_length=10000)
    target_role: str | None = Field(default=None, max_length=200)


class RewriteTextResponse(BaseModel):
    # None means the rewrite step didn't produce a usable result (provider
    # unavailable, malformed response, or the rewrite failed the
    # deterministic fact-check) -- not an error, since the caller already
    # has the original text as a fallback and should just keep it.
    rewritten_text: str | None


class ResumeCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    template_id: uuid.UUID


class ResumeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    template_id: uuid.UUID | None = None


class ResumeResponse(BaseModel):
    id: uuid.UUID
    title: str
    template_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    latest_version_number: int

    model_config = {"from_attributes": True}


class ResumeVersionResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    version_number: int
    content: ResumeContent
    rendered_file_id: uuid.UUID | None
    rendered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeVersionSummaryResponse(BaseModel):
    id: uuid.UUID
    version_number: int
    rendered_file_id: uuid.UUID | None
    rendered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeAutofitResponse(BaseModel):
    version: ResumeVersionResponse
    # True if the content still doesn't fit one page even at the tightest
    # lossless spacing/density -- the caller (builder UI) should surface
    # this as "you need to remove or shorten something," never silently
    # drop content itself.
    overflowing: bool
