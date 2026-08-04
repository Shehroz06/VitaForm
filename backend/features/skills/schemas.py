import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import SkillCategory, SkillLevel


class SkillCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: SkillCategory
    level: SkillLevel | None = None


class SkillUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: SkillCategory | None = None
    level: SkillLevel | None = None


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: SkillCategory
    level: SkillLevel | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
