import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_optional_url


class HackathonCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    project_name: str | None = Field(default=None, max_length=200)
    event_date: date | None = None
    result: str | None = Field(default=None, max_length=150)
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class HackathonUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    project_name: str | None = Field(default=None, max_length=200)
    event_date: date | None = None
    result: str | None = Field(default=None, max_length=150)
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class HackathonResponse(BaseModel):
    id: uuid.UUID
    name: str
    project_name: str | None
    event_date: date | None
    result: str | None
    url: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
