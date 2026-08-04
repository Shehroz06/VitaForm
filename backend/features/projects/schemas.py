import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import ProjectStatus, SkillCategory, SkillLevel
from app.core.validators import validate_optional_url


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    role: str | None = Field(default=None, max_length=150)
    status: ProjectStatus = ProjectStatus.IN_PROGRESS
    start_date: date | None = None
    end_date: date | None = None
    repository_url: str | None = Field(default=None, max_length=500)
    demo_url: str | None = Field(default=None, max_length=500)
    is_pinned: bool = False
    skill_ids: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("repository_url", "demo_url")
    @classmethod
    def validate_urls(cls, value: str | None) -> str | None:
        return validate_optional_url(value)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    role: str | None = Field(default=None, max_length=150)
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    repository_url: str | None = Field(default=None, max_length=500)
    demo_url: str | None = Field(default=None, max_length=500)
    is_pinned: bool | None = None
    skill_ids: list[uuid.UUID] | None = None

    @field_validator("repository_url", "demo_url")
    @classmethod
    def validate_urls(cls, value: str | None) -> str | None:
        return validate_optional_url(value)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class SkillSummary(BaseModel):
    id: uuid.UUID
    name: str
    category: SkillCategory
    level: SkillLevel | None

    model_config = {"from_attributes": True}


class ProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    role: str | None
    status: ProjectStatus
    start_date: date | None
    end_date: date | None
    repository_url: str | None
    demo_url: str | None
    is_pinned: bool
    skills: list[SkillSummary]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
