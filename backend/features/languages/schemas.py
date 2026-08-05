import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import LanguageProficiency


class LanguageCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    proficiency: LanguageProficiency


class LanguageUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    proficiency: LanguageProficiency | None = None


class LanguageResponse(BaseModel):
    id: uuid.UUID
    name: str
    proficiency: LanguageProficiency
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
