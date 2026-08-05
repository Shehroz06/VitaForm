import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CompetitionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_date: date | None = None
    result: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=2000)


class CompetitionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    event_date: date | None = None
    result: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=2000)


class CompetitionResponse(BaseModel):
    id: uuid.UUID
    name: str
    event_date: date | None
    result: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
