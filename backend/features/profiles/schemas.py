import uuid

from pydantic import BaseModel, Field, field_validator

from app.core.validators import validate_optional_url


class ProfileUpdateRequest(BaseModel):
    headline: str | None = Field(default=None, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=150)
    website_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)

    @field_validator("website_url", "github_url", "linkedin_url")
    @classmethod
    def validate_urls(cls, value: str | None) -> str | None:
        return validate_optional_url(value)


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    headline: str | None
    bio: str | None
    phone: str | None
    location: str | None
    website_url: str | None
    github_url: str | None
    linkedin_url: str | None
    avatar_url: str | None
    completion_percentage: int

    model_config = {"from_attributes": True}
