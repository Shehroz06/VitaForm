import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_optional_url


class PortfolioItemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    url: str | None = Field(default=None, max_length=500)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class PortfolioItemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    url: str | None = Field(default=None, max_length=500)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class PortfolioItemResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
