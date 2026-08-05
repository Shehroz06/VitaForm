import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.enums import PatentStatus
from app.core.validators import validate_optional_url


class PatentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    patent_number: str | None = Field(default=None, max_length=100)
    status: PatentStatus = PatentStatus.FILED
    filing_date: date | None = None
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class PatentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    patent_number: str | None = Field(default=None, max_length=100)
    status: PatentStatus | None = None
    filing_date: date | None = None
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class PatentResponse(BaseModel):
    id: uuid.UUID
    title: str
    patent_number: str | None
    status: PatentStatus
    filing_date: date | None
    url: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
