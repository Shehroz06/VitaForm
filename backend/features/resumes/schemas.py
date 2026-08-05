import uuid
from datetime import datetime

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


class ResumeContent(BaseModel):
    summary: str | None = Field(default=None, max_length=2000)
    contact_visibility: ContactVisibility = Field(default_factory=ContactVisibility)
    sections: list[ResumeSection] = Field(default_factory=list)


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
