import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_optional_url


class ResearchCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    publication_venue: str | None = Field(default=None, max_length=200)
    publication_date: date | None = None
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class ResearchUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    publication_venue: str | None = Field(default=None, max_length=200)
    publication_date: date | None = None
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class ResearchResponse(BaseModel):
    id: uuid.UUID
    title: str
    publication_venue: str | None
    publication_date: date | None
    url: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
