import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ReferenceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    relationship: str | None = Field(default=None, max_length=150)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, max_length=2000)


class ReferenceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    relationship: str | None = Field(default=None, max_length=150)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, max_length=2000)


class ReferenceResponse(BaseModel):
    id: uuid.UUID
    name: str
    relationship: str | None
    contact_email: str | None
    contact_phone: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
