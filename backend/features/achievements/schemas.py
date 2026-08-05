import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class AchievementCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    issuer: str | None = Field(default=None, max_length=200)
    date_achieved: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class AchievementUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    issuer: str | None = Field(default=None, max_length=200)
    date_achieved: date | None = None
    description: str | None = Field(default=None, max_length=2000)


class AchievementResponse(BaseModel):
    id: uuid.UUID
    title: str
    issuer: str | None
    date_achieved: date | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
