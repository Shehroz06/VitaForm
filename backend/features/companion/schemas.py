import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CoverLetterAIResponse(BaseModel):
    cover_letter: str = Field(min_length=100, max_length=4000)


class LinkedinAIResponse(BaseModel):
    headline: str = Field(min_length=1, max_length=220)
    about: str = Field(min_length=50, max_length=2600)


class GenerateCoverLetterRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    hiring_manager: str | None = Field(default=None, max_length=150)
    job_description_id: uuid.UUID | None = None
    job_description_text: str | None = Field(default=None, max_length=10000)


class GenerateLinkedinRequest(BaseModel):
    target_role: str | None = Field(default=None, max_length=150)


class CoverLetterResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    role_title: str
    hiring_manager: str | None
    job_description_id: uuid.UUID | None
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkedinGenerationResponse(BaseModel):
    id: uuid.UUID
    target_role: str | None
    headline: str
    about: str
    created_at: datetime

    model_config = {"from_attributes": True}
