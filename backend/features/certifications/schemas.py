import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.validators import validate_optional_url


class CertificationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    issuing_organization: str = Field(min_length=1, max_length=200)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_id: str | None = Field(default=None, max_length=150)
    credential_url: str | None = Field(default=None, max_length=500)

    @field_validator("credential_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.issue_date and self.expiration_date and self.expiration_date < self.issue_date:
            raise ValueError("expiration_date must be on or after issue_date.")
        return self


class CertificationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    issuing_organization: str | None = Field(default=None, min_length=1, max_length=200)
    issue_date: date | None = None
    expiration_date: date | None = None
    credential_id: str | None = Field(default=None, max_length=150)
    credential_url: str | None = Field(default=None, max_length=500)

    @field_validator("credential_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_optional_url(value)

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if self.issue_date and self.expiration_date and self.expiration_date < self.issue_date:
            raise ValueError("expiration_date must be on or after issue_date.")
        return self


class CertificationResponse(BaseModel):
    id: uuid.UUID
    name: str
    issuing_organization: str
    issue_date: date | None
    expiration_date: date | None
    credential_id: str | None
    credential_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
