import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import EmploymentType


class JobAnalysis(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)


class AnalyzeJobRequest(BaseModel):
    raw_text: str = Field(min_length=50, max_length=10000)


class JobDescriptionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    raw_text: str = Field(min_length=50, max_length=10000)
    company_name: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=150)
    employment_type: EmploymentType | None = None


class JobDescriptionUpdateRequest(BaseModel):
    """Corrects metadata on an already-saved posting -- title, company,
    location, employment type. Deliberately excludes raw_text: that's what
    keywords/required_skills/preferred_skills were analyzed from, and
    create_job already treats identical raw_text as the same posting, so a
    genuinely different JD body is a new posting, not an edit to this one."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=150)
    employment_type: EmploymentType | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    website_url: str | None
    industry: str | None
    notes: str | None

    model_config = {"from_attributes": True}


class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    title: str
    raw_text: str
    location: str | None
    employment_type: EmploymentType | None
    company_id: uuid.UUID | None
    company_name: str | None
    keywords: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AtsScoreResponse(BaseModel):
    id: uuid.UUID
    job_description_id: uuid.UUID
    overall_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
